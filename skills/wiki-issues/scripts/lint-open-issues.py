#!/usr/bin/env python3
"""
lint-open-issues.py — Validate wiki/meta/OPEN-ISSUES.md hybrid stack schema.

Ported from ai-secondbrain scripts/lint/lint-open-issues.py. Colocated under
skills/wiki-issues/ per ADR-0002; owned by the wiki-issues skill (ADR-0005).
Validates wiki/meta/OPEN-ISSUES.md hybrid schema (schema/parity/cycles/sort).

Parses the YAML frontmatter `stack:` array and the body `### I-YYYY-NNN`
sections, then runs:

  1. Per-item required fields (id, priority, section, title, pushed).
  2. ID format (I-YYYY-NNN) + uniqueness.
  3. priority ∈ {P0,P1,P2,P3}; section ∈ whitelist.
  4. Stack ↔ body parity: stack[].id set == body `### I-…` header set.
  5. blocked_by referential integrity (every target exists in the stack).
  6. blocked_by cycle detection (DFS, same approach as lint-deps.py).
  7. inconclusive_since ↔ inconclusive_reason must appear as a pair.
  8. aggregated_from ids must NOT still be present in the stack.
  9. Sort order: priority ASC, ready-first, inconclusive-last, pushed DESC.

Warnings (do not affect exit code):
  - Body section missing its `**Priority:** … · **WO:** …` meta line.

Exit codes:
  0  no errors (warnings allowed)
  1  validation errors
  2  usage/parse error (bad CLI args)

Usage:
  lint-open-issues.py [path]      # default: wiki/meta/OPEN-ISSUES.md
  lint-open-issues.py --json [path]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import cmp_to_key
from pathlib import Path

import yaml

DEFAULT_PATH = Path("wiki/meta/OPEN-ISSUES.md")

ID_RE = re.compile(r"^I-\d{4}-\d{3}$")
HEADER_RE = re.compile(r"^###\s+(I-\d{4}-\d{3})\b")
META_RE = re.compile(r"\*\*Priority:\*\*.*\*\*WO:\*\*")

PRIORITIES = {"P0", "P1", "P2", "P3"}
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
# Reconciled section whitelist for this plugin (audit finding V-6).
SECTIONS = {
    "enforcement",
    "lint",
    "tooling",
    "ci",
    "hooks",
    "docs",
    "templates",
    "skills",
    "skill-plugin",
    "vault-content",
    "eval-observability",
    "dragonscale",
}
REQUIRED_FIELDS = ("id", "priority", "section", "title", "pushed")


def parse_frontmatter(text: str) -> dict:
    """Extract + parse the leading YAML frontmatter block delimited by '---'."""
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    try:
        return yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError:
        return {}


def parse_body(text: str) -> tuple[list[str], dict[str, bool]]:
    """Return (body ids in order, {id: has_meta_line}).

    A section's meta line is the first non-blank line after its `### I-…` header;
    it must contain both **Priority:** and **WO:**.
    """
    ids: list[str] = []
    has_meta: dict[str, bool] = {}
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        m = HEADER_RE.match(line)
        if not m:
            continue
        issue_id = m.group(1)
        ids.append(issue_id)
        has_meta[issue_id] = False
        for j in range(idx + 1, min(idx + 4, len(lines))):
            if lines[j].strip() == "":
                continue
            has_meta[issue_id] = bool(META_RE.search(lines[j]))
            break
    return ids, has_meta


def find_cycles(stack: list[dict]) -> list[list[str]]:
    """All simple cycles in the blocked_by graph (iterative DFS)."""
    graph = {
        item["id"]: list(item.get("blocked_by") or [])
        for item in stack
        if isinstance(item, dict) and "id" in item
    }
    color: dict[str, int] = {nid: 0 for nid in graph}  # 0=white 1=gray 2=black
    cycles: list[list[str]] = []

    def visit(start: str) -> None:
        dfs: list[tuple[str, object]] = [(start, iter(graph.get(start, [])))]
        path: list[str] = [start]
        color[start] = 1
        while dfs:
            node, it = dfs[-1]
            try:
                nxt = next(it)  # type: ignore[arg-type]
            except StopIteration:
                color[node] = 2
                path.pop()
                dfs.pop()
                continue
            if nxt not in graph:
                continue  # missing target handled separately
            if color.get(nxt, 0) == 1:
                idx = path.index(nxt)
                cycles.append(path[idx:] + [nxt])
                continue
            if color.get(nxt, 0) == 0:
                color[nxt] = 1
                path.append(nxt)
                dfs.append((nxt, iter(graph.get(nxt, []))))

    for nid in graph:
        if color[nid] == 0:
            visit(nid)
    return cycles


def _cmp(a: dict, b: dict) -> int:
    """Canonical order: priority ASC, ready-first, inconclusive-last, pushed DESC."""
    ka = (
        PRIORITY_RANK.get(a.get("priority"), 99),
        1 if (a.get("blocked_by") or []) else 0,
        1 if a.get("inconclusive_since") else 0,
    )
    kb = (
        PRIORITY_RANK.get(b.get("priority"), 99),
        1 if (b.get("blocked_by") or []) else 0,
        1 if b.get("inconclusive_since") else 0,
    )
    if ka != kb:
        return -1 if ka < kb else 1
    pa, pb = str(a.get("pushed", "")), str(b.get("pushed", ""))
    if pa == pb:
        return 0
    return -1 if pa > pb else 1  # newer (greater date) first


def lint(text: str) -> dict:
    """Run all checks; return a structured report dict."""
    fm = parse_frontmatter(text)
    stack = fm.get("stack")
    report: dict = {
        "has_stack": isinstance(stack, list),
        "item_count": 0,
        "field_errors": [],
        "id_format_errors": [],
        "duplicate_ids": [],
        "priority_errors": [],
        "section_errors": [],
        "parity": {"in_stack_not_body": [], "in_body_not_stack": []},
        "missing_blocked_by_targets": [],
        "cycles": [],
        "inconclusive_pairing_errors": [],
        "aggregated_still_present": [],
        "sort_ok": True,
        "expected_order": [],
        "warnings": [],
    }

    if not isinstance(stack, list):
        report["field_errors"].append("frontmatter has no `stack:` array (not migrated to hybrid?)")
        return report

    stack = [it for it in stack if isinstance(it, dict)]
    report["item_count"] = len(stack)

    # 1. Required fields.
    for it in stack:
        for f in REQUIRED_FIELDS:
            if f not in it or it.get(f) in (None, ""):
                report["field_errors"].append(f"{it.get('id', '<no-id>')}: missing `{f}`")
        if "blocked_by" not in it:
            report["warnings"].append(f"{it.get('id', '<no-id>')}: no `blocked_by` (treated as [])")

    ids = [it["id"] for it in stack if "id" in it]

    # 2. ID format + uniqueness.
    for iid in ids:
        if not ID_RE.match(str(iid)):
            report["id_format_errors"].append(str(iid))
    seen: set[str] = set()
    for iid in ids:
        if iid in seen:
            report["duplicate_ids"].append(iid)
        seen.add(iid)

    # 3. priority + section membership.
    for it in stack:
        if it.get("priority") not in PRIORITIES:
            report["priority_errors"].append(f"{it.get('id')}: {it.get('priority')!r}")
        if it.get("section") not in SECTIONS:
            report["section_errors"].append(f"{it.get('id')}: {it.get('section')!r}")

    # 4. Stack <-> body parity.
    body_ids, has_meta = parse_body(text)
    stack_set, body_set = set(ids), set(body_ids)
    report["parity"]["in_stack_not_body"] = sorted(stack_set - body_set)
    report["parity"]["in_body_not_stack"] = sorted(body_set - stack_set)

    # 5. blocked_by referential integrity.
    for it in stack:
        for dep in it.get("blocked_by") or []:
            if dep not in stack_set:
                report["missing_blocked_by_targets"].append({"id": it.get("id"), "missing": dep})

    # 6. Cycles.
    report["cycles"] = find_cycles(stack)

    # 7. inconclusive pairing.
    for it in stack:
        has_since = bool(it.get("inconclusive_since"))
        has_reason = bool(it.get("inconclusive_reason"))
        if has_since != has_reason:
            report["inconclusive_pairing_errors"].append(it.get("id"))

    # 8. aggregated_from ids must not still be in the stack.
    for it in stack:
        for src in it.get("aggregated_from") or []:
            if src in stack_set:
                report["aggregated_still_present"].append({"id": it.get("id"), "aggregated": src})

    # 9. Sort order.
    expected = sorted(stack, key=cmp_to_key(_cmp))
    expected_ids = [it.get("id") for it in expected]
    if ids != expected_ids:
        report["sort_ok"] = False
        report["expected_order"] = expected_ids

    # Warnings: missing meta line in body.
    for iid in body_ids:
        if not has_meta.get(iid, False):
            report["warnings"].append(f"{iid}: body section missing **Priority:** … **WO:** meta line")

    return report


def has_errors(r: dict) -> bool:
    return bool(
        r["field_errors"]
        or r["id_format_errors"]
        or r["duplicate_ids"]
        or r["priority_errors"]
        or r["section_errors"]
        or r["parity"]["in_stack_not_body"]
        or r["parity"]["in_body_not_stack"]
        or r["missing_blocked_by_targets"]
        or r["cycles"]
        or r["inconclusive_pairing_errors"]
        or r["aggregated_still_present"]
        or not r["sort_ok"]
        or not r["has_stack"]
    )


def error_count(r: dict) -> int:
    """Total count of error-category items in the report.

    Sum of every error list's length, +1 if sort is wrong, +1 if the
    format-guard (no `stack:` array) fired. Warnings are NOT counted.
    Invariant: == 0 exactly when has_errors(r) is False; >= 1 otherwise.
    """
    return (
        len(r["field_errors"])
        + len(r["id_format_errors"])
        + len(r["duplicate_ids"])
        + len(r["priority_errors"])
        + len(r["section_errors"])
        + len(r["parity"]["in_stack_not_body"])
        + len(r["parity"]["in_body_not_stack"])
        + len(r["missing_blocked_by_targets"])
        + len(r["cycles"])
        + len(r["inconclusive_pairing_errors"])
        + len(r["aggregated_still_present"])
        + (0 if r["sort_ok"] else 1)
        + (0 if r["has_stack"] else 1)
    )


def _empty_report(with_error_count: bool = True) -> dict:
    """A well-formed report with no errors — used when the file is absent."""
    report: dict = {
        "has_stack": True,
        "item_count": 0,
        "field_errors": [],
        "id_format_errors": [],
        "duplicate_ids": [],
        "priority_errors": [],
        "section_errors": [],
        "parity": {"in_stack_not_body": [], "in_body_not_stack": []},
        "missing_blocked_by_targets": [],
        "cycles": [],
        "inconclusive_pairing_errors": [],
        "aggregated_still_present": [],
        "sort_ok": True,
        "expected_order": [],
        "warnings": [],
    }
    if with_error_count:
        report["error_count"] = 0
    return report


def collect(vault_root) -> dict:
    """Importable entrypoint for run-lint.py. Returns lint()'s report dict
    augmented with an `error_count` key, without going through print().

    The file wiki/meta/OPEN-ISSUES.md is OPTIONAL until the wiki-issues skill
    initializes it: an absent file is NOT an error (error_count == 0). A file
    that exists but lacks a `stack:` array IS a format-guard error (>= 1).
    Existence-gated and exception-safe, mirroring the repo's other collect()
    entrypoints (lint-deps.py, lint-orphans.py).
    """
    issues_path = Path(vault_root) / "wiki" / "meta" / "OPEN-ISSUES.md"
    if not issues_path.exists():
        return _empty_report()
    try:
        text = issues_path.read_text(encoding="utf-8")
    except OSError:
        return _empty_report()
    report = lint(text)
    report["issues_file"] = str(issues_path)
    report["error_count"] = error_count(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=str(DEFAULT_PATH), help="OPEN-ISSUES.md path")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: {path} not found (run from repo root).", file=sys.stderr)
        return 1

    report = lint(path.read_text(encoding="utf-8"))
    report["issues_file"] = str(path)
    report["error_count"] = error_count(report)
    errors = has_errors(report)
    report["ok"] = not errors

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1 if errors else 0

    print(f"# Open-issues lint — {path}")
    if not report["has_stack"]:
        print("❌ No `stack:` array in frontmatter (file not migrated to hybrid schema?).")
        return 1
    print(f"Stack items: {report['item_count']}")
    print()

    def block(label: str, items, fmt=lambda x: str(x)):
        if items:
            print(f"❌ {label} ({len(items)}):")
            for x in items:
                print(f"   {fmt(x)}")
        else:
            print(f"✓ {label}: none")

    block("Missing required fields", report["field_errors"])
    block("ID format errors", report["id_format_errors"])
    block("Duplicate IDs", report["duplicate_ids"])
    block("Invalid priority", report["priority_errors"])
    block("Invalid section", report["section_errors"])
    block("In stack but no body section", report["parity"]["in_stack_not_body"])
    block("In body but not in stack", report["parity"]["in_body_not_stack"])
    block(
        "Missing blocked_by targets",
        report["missing_blocked_by_targets"],
        lambda x: f"{x['id']} blocked_by {x['missing']} (not in stack)",
    )
    block("Cycles", report["cycles"], lambda c: " → ".join(c))
    block("inconclusive_since/reason not paired", report["inconclusive_pairing_errors"])
    block(
        "aggregated_from still in stack",
        report["aggregated_still_present"],
        lambda x: f"{x['id']} aggregated {x['aggregated']} (still present)",
    )

    if report["sort_ok"]:
        print("✓ Sort order: correct (priority ASC, ready-first, inconclusive-last, pushed DESC)")
    else:
        print("❌ Sort order: incorrect. Expected:")
        for iid in report["expected_order"]:
            print(f"   {iid}")

    if report["warnings"]:
        print()
        print(f"⚠ Warnings ({len(report['warnings'])}):")
        for w in report["warnings"]:
            print(f"   {w}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
