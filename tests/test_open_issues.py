#!/usr/bin/env python3
"""test_open_issues.py — unit + CLI tests for the OPEN-ISSUES.md validator.

System under test: skills/wiki-issues/scripts/lint-open-issues.py — the hybrid
`stack:` (YAML frontmatter) ↔ `### I-YYYY-NNN` (body) validator for
wiki/meta/OPEN-ISSUES.md.

Mirrors tests/test_run_lint.py / tests/test_tiling_check.py style: plain-python
Fail(SystemExit) + assert_eq/assert_true helpers, importlib white-box loading of
the hyphenated script, subprocess black-box CLI tests, KM_VAULT_PATH temp vaults
via tempfile.mkdtemp ($TMPDIR-aware). NOT pytest. A __main__ runner prints
"All tests passed." on success and sys.exit(1) on any failure.

White-box cases build small in-memory Markdown strings and call lint(text)
directly; black-box cases write throwaway temp files / temp vaults. The real
repo vault (wiki/meta/OPEN-ISSUES.md) is never read or written.

Usage:
  python3 tests/test_open_issues.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SUT = ROOT / "skills" / "wiki-issues" / "scripts" / "lint-open-issues.py"
RUN_LINT = ROOT / "scripts" / "run-lint.py"

# White-box import of the hyphenated validator (hyphen -> importlib).
spec = importlib.util.spec_from_file_location("lint_open_issues", SUT)
loi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loi)


class Fail(SystemExit):
    pass


def assert_eq(label, expected, actual):
    if expected != actual:
        raise Fail(f"FAIL {label}: expected {expected!r}, got {actual!r}")
    print(f"OK   {label}")


def assert_true(label, cond):
    if not cond:
        raise Fail(f"FAIL {label}")
    print(f"OK   {label}")


# --- fixture builders ------------------------------------------------------


def item(iid, priority, section, pushed, **extra):
    """One stack entry with the required fields; `extra` adds optional keys
    (blocked_by, inconclusive_since/reason, aggregated_from, ...)."""
    d = {
        "id": iid,
        "priority": priority,
        "section": section,
        "title": f"Title for {iid}",
        "pushed": pushed,
    }
    d.update(extra)
    return d


def body_section(iid):
    """A well-formed body section with the `**Priority:** … **WO:**` meta line
    (so it does not trip the meta-line warning)."""
    return f"\n### {iid}\n\n**Priority:** P1 · **WO:** WO-x\n\nBody text.\n"


def doc(items, body_ids=None):
    """Build an OPEN-ISSUES.md string: YAML `stack:` frontmatter mirrored by
    body `### I-…` sections. `body_ids=None` -> one section per stack id (parity
    holds); pass an explicit list to break parity on purpose."""
    frontmatter = yaml.safe_dump({"stack": items}, sort_keys=False,
                                 allow_unicode=True)
    if body_ids is None:
        body_ids = [it["id"] for it in items]
    body = "".join(body_section(b) for b in body_ids)
    return f"---\n{frontmatter}---\n{body}"


def flat_doc():
    """Frontmatter present but NO `stack:` key (the pre-migration flat file)."""
    return "---\ntype: meta\ntitle: \"Open Issues\"\n---\n\nSome prose body.\n"


# --- temp helpers (mktemp-style; cleaned with shutil.rmtree in python) ------


def new_tmp(prefix="open-issues-test."):
    base = os.environ.get("TMPDIR") or "/tmp"
    return Path(tempfile.mkdtemp(prefix=prefix, dir=base))


def write_temp_file(text, suffix=".md"):
    base = os.environ.get("TMPDIR") or "/tmp"
    fd, name = tempfile.mkstemp(prefix="open-issues.", suffix=suffix, dir=base)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return Path(name)


def cli(path, *args):
    """Run the validator CLI as a subprocess. Default args: --json <path>."""
    if not args:
        args = ("--json", str(path))
    return subprocess.run(
        [sys.executable, str(SUT), *args],
        capture_output=True, text=True, timeout=60,
    )


def run_lint_json(vault: Path):
    """Run scripts/run-lint.py --json against a KM_VAULT_PATH temp vault."""
    env = dict(os.environ)
    env["KM_VAULT_PATH"] = str(vault)
    r = subprocess.run(
        [sys.executable, str(RUN_LINT), "--json"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    return r, json.loads(r.stdout)


def check_by_name(summary, name):
    for c in summary["checks"]:
        if c["name"] == name:
            return c
    raise Fail(f"check {name!r} not present in run-lint summary")


# ===========================================================================
# 0 — public API surface (SECTIONS)
# ===========================================================================


def test_sections_frozenset_of_12():
    expected = {
        "enforcement", "lint", "tooling", "ci", "hooks", "docs", "templates",
        "skills", "skill-plugin", "vault-content", "eval-observability",
        "dragonscale",
    }
    assert_eq("00 SECTIONS has 12", 12, len(loi.SECTIONS))
    assert_eq("00 SECTIONS exact set", expected, set(loi.SECTIONS))


# ===========================================================================
# 1 — good_valid: 2 items, correct sort, matching body sections
# ===========================================================================


def test_good_valid():
    text = doc([
        item("I-2026-001", "P0", "lint", "2026-06-01"),
        item("I-2026-002", "P1", "docs", "2026-05-01"),
    ])
    r = loi.lint(text)
    assert_eq("01 good has_errors False", False, loi.has_errors(r))
    assert_eq("01 good error_count 0", 0, loi.error_count(r))
    assert_eq("01 good sort_ok True", True, r["sort_ok"])
    assert_eq("01 good item_count 2", 2, r["item_count"])
    # No error-category lists populated (warnings are allowed and do not count).
    assert_eq("01 good no field_errors", [], r["field_errors"])
    assert_eq("01 good no section_errors", [], r["section_errors"])
    assert_eq("01 good parity clean",
              ([], []),
              (r["parity"]["in_stack_not_body"],
               r["parity"]["in_body_not_stack"]))


# ===========================================================================
# 2 — empty_stack: stack: [] and no body sections -> 0 errors
# ===========================================================================


def test_empty_stack():
    text = doc([], body_ids=[])
    r = loi.lint(text)
    assert_eq("02 empty has_stack True", True, r["has_stack"])
    assert_eq("02 empty error_count 0", 0, loi.error_count(r))
    assert_eq("02 empty has_errors False", False, loi.has_errors(r))
    assert_eq("02 empty item_count 0", 0, r["item_count"])


# ===========================================================================
# 3 — bad_section: section not in the 12 -> section error
# ===========================================================================


def test_bad_section():
    text = doc([item("I-2026-001", "P0", "not-a-section", "2026-06-01")])
    r = loi.lint(text)
    assert_eq("03 section_errors count 1", 1, len(r["section_errors"]))
    assert_true("03 section_errors names the id + value",
                "I-2026-001" in r["section_errors"][0]
                and "not-a-section" in r["section_errors"][0])
    assert_eq("03 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 4 — parity: stack id with no body section -> in_stack_not_body
# ===========================================================================


def test_parity_stack_not_body():
    # stack has I-2026-001 but body has NO sections at all.
    text = doc([item("I-2026-001", "P0", "lint", "2026-06-01")], body_ids=[])
    r = loi.lint(text)
    assert_eq("04 in_stack_not_body == [id]",
              ["I-2026-001"], r["parity"]["in_stack_not_body"])
    assert_eq("04 in_body_not_stack empty", [], r["parity"]["in_body_not_stack"])
    assert_eq("04 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 5 — parity: body `### I-` with no stack id -> in_body_not_stack
# ===========================================================================


def test_parity_body_not_stack():
    # stack is [] (so no other error), body carries an orphan `### I-` section.
    text = doc([], body_ids=["I-2026-050"])
    r = loi.lint(text)
    assert_eq("05 in_body_not_stack == [id]",
              ["I-2026-050"], r["parity"]["in_body_not_stack"])
    assert_eq("05 in_stack_not_body empty", [], r["parity"]["in_stack_not_body"])
    assert_eq("05 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 6 — blocked_by cycle: A blocks B, B blocks A -> cycle detected
# ===========================================================================


def test_blocked_by_cycle():
    text = doc([
        item("I-2026-001", "P0", "lint", "2026-06-01",
             blocked_by=["I-2026-002"]),
        item("I-2026-002", "P0", "lint", "2026-05-01",
             blocked_by=["I-2026-001"]),
    ])
    r = loi.lint(text)
    assert_true("06 at least one cycle", len(r["cycles"]) >= 1)
    cyc_nodes = {n for c in r["cycles"] for n in c}
    assert_true("06 cycle covers both ids",
                {"I-2026-001", "I-2026-002"} <= cyc_nodes)
    assert_eq("06 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 7 — blocked_by an id not in the stack -> missing_blocked_by_targets
# ===========================================================================


def test_missing_blocked_by_target():
    text = doc(
        [item("I-2026-001", "P0", "lint", "2026-06-01",
              blocked_by=["I-2026-999"])],
        body_ids=["I-2026-001"],
    )
    r = loi.lint(text)
    assert_eq("07 one missing target", 1, len(r["missing_blocked_by_targets"]))
    mbt = r["missing_blocked_by_targets"][0]
    assert_eq("07 missing target id", "I-2026-001", mbt["id"])
    assert_eq("07 missing target ref", "I-2026-999", mbt["missing"])
    assert_eq("07 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 8 — bad_id_format: I-26-1 -> id_format error
# ===========================================================================


def test_bad_id_format():
    text = doc([item("I-26-1", "P0", "lint", "2026-06-01")],
               body_ids=["I-26-1"])
    r = loi.lint(text)
    assert_eq("08 id_format_errors == [bad id]", ["I-26-1"],
              r["id_format_errors"])
    assert_eq("08 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 9 — duplicate_ids -> duplicate error
# ===========================================================================


def test_duplicate_ids():
    text = doc([
        item("I-2026-001", "P0", "lint", "2026-06-02"),
        item("I-2026-001", "P1", "docs", "2026-05-01"),
    ], body_ids=["I-2026-001"])
    r = loi.lint(text)
    assert_eq("09 duplicate_ids == [id]", ["I-2026-001"], r["duplicate_ids"])
    assert_eq("09 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 10 — mis_sort_priority: a P1 placed before a P0 -> sort_ok False
# ===========================================================================


def test_mis_sort_priority():
    text = doc([
        item("I-2026-002", "P1", "docs", "2026-05-01"),   # P1 first — wrong
        item("I-2026-001", "P0", "lint", "2026-06-01"),   # P0 second
    ])
    r = loi.lint(text)
    assert_eq("10 sort_ok False", False, r["sort_ok"])
    assert_eq("10 expected_order is P0-first",
              ["I-2026-001", "I-2026-002"], r["expected_order"])
    assert_eq("10 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 11 — ready-first (empty blocked_by first within a priority group)
# ===========================================================================


def test_ready_first_correct():
    # same priority: ready (no blocked_by) BEFORE blocked -> correct.
    text = doc([
        item("I-2026-002", "P1", "docs", "2026-05-01"),                 # ready
        item("I-2026-001", "P1", "lint", "2026-06-01",
             blocked_by=["I-2026-002"]),                                # blocked
    ])
    r = loi.lint(text)
    assert_eq("11a ready-first correct sort_ok True", True, r["sort_ok"])


def test_ready_first_wrong():
    # same priority: blocked BEFORE ready -> wrong.
    text = doc([
        item("I-2026-001", "P1", "lint", "2026-06-01",
             blocked_by=["I-2026-002"]),                                # blocked
        item("I-2026-002", "P1", "docs", "2026-05-01"),                 # ready
    ])
    r = loi.lint(text)
    assert_eq("11b ready-first violated sort_ok False", False, r["sort_ok"])


# ===========================================================================
# 12 — inconclusive-last within a priority group
# ===========================================================================


def test_inconclusive_last_correct():
    # same priority: normal BEFORE inconclusive -> correct.
    text = doc([
        item("I-2026-001", "P1", "lint", "2026-06-01"),                 # normal
        item("I-2026-002", "P1", "docs", "2026-05-01",
             inconclusive_since="2026-04-01",
             inconclusive_reason="waiting on upstream"),                # inconc.
    ])
    r = loi.lint(text)
    assert_eq("12a inconclusive-last correct sort_ok True", True, r["sort_ok"])


def test_inconclusive_last_wrong():
    # same priority: inconclusive BEFORE normal -> wrong.
    text = doc([
        item("I-2026-001", "P1", "lint", "2026-06-01",
             inconclusive_since="2026-04-01",
             inconclusive_reason="waiting on upstream"),                # inconc.
        item("I-2026-002", "P1", "docs", "2026-05-01"),                 # normal
    ])
    r = loi.lint(text)
    assert_eq("12b inconclusive-last violated sort_ok False",
              False, r["sort_ok"])


# ===========================================================================
# 13 — inconclusive_since set but inconclusive_reason missing -> pairing error
# ===========================================================================


def test_inconclusive_pairing():
    text = doc(
        [item("I-2026-001", "P0", "lint", "2026-06-01",
              inconclusive_since="2026-04-01")],  # no inconclusive_reason
        body_ids=["I-2026-001"],
    )
    r = loi.lint(text)
    assert_eq("13 pairing error == [id]",
              ["I-2026-001"], r["inconclusive_pairing_errors"])
    assert_eq("13 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 14 — aggregated_from lists an id still in the stack -> aggregated error
# ===========================================================================


def test_aggregated_still_present():
    text = doc([
        item("I-2026-001", "P0", "lint", "2026-06-01",
             aggregated_from=["I-2026-002"]),
        item("I-2026-002", "P1", "docs", "2026-05-01"),  # still present
    ])
    r = loi.lint(text)
    assert_eq("14 one aggregated-still-present",
              1, len(r["aggregated_still_present"]))
    agg = r["aggregated_still_present"][0]
    assert_eq("14 aggregated owner id", "I-2026-001", agg["id"])
    assert_eq("14 aggregated ref", "I-2026-002", agg["aggregated"])
    assert_eq("14 has_errors True", True, loi.has_errors(r))


# ===========================================================================
# 15 — year_rollover: I-2025-009 and I-2026-001 coexist -> NO id_format error
# ===========================================================================


def test_year_rollover():
    text = doc([
        item("I-2025-009", "P0", "lint", "2026-06-01"),
        item("I-2026-001", "P1", "docs", "2026-05-01"),
    ])
    r = loi.lint(text)
    assert_eq("15 no id_format errors across years", [], r["id_format_errors"])
    assert_eq("15 sort_ok True (P0 before P1)", True, r["sort_ok"])
    assert_eq("15 has_errors False", False, loi.has_errors(r))


# ===========================================================================
# 16 — flat_file: frontmatter present, NO stack: key -> format guard fires
# ===========================================================================


def test_flat_file():
    r = loi.lint(flat_doc())
    assert_eq("16 flat has_stack False", False, r["has_stack"])
    assert_eq("16 flat has_errors True", True, loi.has_errors(r))
    assert_true("16 flat error_count >= 1", loi.error_count(r) >= 1)


# ===========================================================================
# 17 — CLI black-box: good -> 0, broken -> 1, flat -> 1
# ===========================================================================


def test_cli_exit_codes():
    good = write_temp_file(doc([
        item("I-2026-001", "P0", "lint", "2026-06-01"),
        item("I-2026-002", "P1", "docs", "2026-05-01"),
    ]))
    broken = write_temp_file(doc([
        item("I-2026-001", "P0", "not-a-section", "2026-06-01"),
    ]))
    flat = write_temp_file(flat_doc())
    try:
        assert_eq("17 CLI good exit 0", 0, cli(good).returncode)
        assert_eq("17 CLI broken exit 1", 1, cli(broken).returncode)
        assert_eq("17 CLI flat exit 1", 1, cli(flat).returncode)
        # good --json actually parses and reports ok:true
        out = json.loads(cli(good).stdout)
        assert_eq("17 CLI good json ok True", True, out["ok"])
    finally:
        for p in (good, broken, flat):
            p.unlink(missing_ok=True)


# ===========================================================================
# 18 — collect(): existence-gated + clean + broken
# ===========================================================================


def test_collect_absent_file():
    # temp dir WITHOUT wiki/meta/OPEN-ISSUES.md -> error_count 0 (optional file).
    v = new_tmp("open-issues-collect-absent.")
    try:
        d = loi.collect(v)
        assert_eq("18a collect absent error_count 0", 0, d["error_count"])
        assert_eq("18a collect absent has_errors False", False,
                  loi.has_errors(d))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_collect_clean_file():
    v = new_tmp("open-issues-collect-clean.")
    try:
        (v / "wiki" / "meta").mkdir(parents=True)
        (v / "wiki" / "meta" / "OPEN-ISSUES.md").write_text(doc([
            item("I-2026-001", "P0", "lint", "2026-06-01"),
            item("I-2026-002", "P1", "docs", "2026-05-01"),
        ]), encoding="utf-8")
        d = loi.collect(v)
        assert_eq("18b collect clean error_count 0", 0, d["error_count"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_collect_broken_file():
    v = new_tmp("open-issues-collect-broken.")
    try:
        (v / "wiki" / "meta").mkdir(parents=True)
        (v / "wiki" / "meta" / "OPEN-ISSUES.md").write_text(doc([
            item("I-2026-001", "P0", "not-a-section", "2026-06-01"),
        ]), encoding="utf-8")
        d = loi.collect(v)
        assert_true("18c collect broken error_count > 0", d["error_count"] > 0)
        assert_eq("18c collect broken has_errors True", True, loi.has_errors(d))
    finally:
        shutil.rmtree(v, ignore_errors=True)


# ===========================================================================
# 19 — run-lint.py integration: broken OPEN-ISSUES.md surfaces as an
#      `open_issues` check (severity error, count>0) counted into totals.error.
#      Regression-guards the run-lint.py <-> lint-open-issues.py wiring.
# ===========================================================================


def test_run_lint_integration_open_issues_broken():
    v = new_tmp("open-issues-runlint.")
    try:
        (v / "wiki" / "meta").mkdir(parents=True)
        # minimal valid index so run-lint's wiki scan is happy
        (v / "wiki" / "index.md").write_text(
            "---\ntype: meta\ntitle: \"Index\"\ncreated: 2026-05-26\n"
            "updated: 2026-05-26\nstatus: developing\n---\nBody.\n",
            encoding="utf-8",
        )
        # BROKEN OPEN-ISSUES.md (bad section -> >=1 validator error)
        (v / "wiki" / "meta" / "OPEN-ISSUES.md").write_text(doc([
            item("I-2026-001", "P0", "not-a-section", "2026-06-01"),
        ]), encoding="utf-8")

        r, summary = run_lint_json(v)
        assert_eq("19 run-lint rc 0 (findings != failure)", 0, r.returncode)
        oi = check_by_name(summary, "open_issues")
        assert_eq("19 open_issues severity error", "error", oi["severity"])
        assert_true("19 open_issues count > 0", oi["count"] > 0)
        assert_true("19 totals.error includes open_issues",
                    summary["totals"]["error"] >= oi["count"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_run_lint_integration_open_issues_clean():
    # Complementary guard: a CLEAN OPEN-ISSUES.md -> open_issues info, count 0.
    v = new_tmp("open-issues-runlint-clean.")
    try:
        (v / "wiki" / "meta").mkdir(parents=True)
        (v / "wiki" / "index.md").write_text(
            "---\ntype: meta\ntitle: \"Index\"\ncreated: 2026-05-26\n"
            "updated: 2026-05-26\nstatus: developing\n---\nBody.\n",
            encoding="utf-8",
        )
        (v / "wiki" / "meta" / "OPEN-ISSUES.md").write_text(doc([
            item("I-2026-001", "P0", "lint", "2026-06-01"),
            item("I-2026-002", "P1", "docs", "2026-05-01"),
        ]), encoding="utf-8")
        _r, summary = run_lint_json(v)
        oi = check_by_name(summary, "open_issues")
        assert_eq("19b clean open_issues severity info", "info", oi["severity"])
        assert_eq("19b clean open_issues count 0", 0, oi["count"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


if __name__ == "__main__":
    try:
        test_sections_frozenset_of_12()
        test_good_valid()
        test_empty_stack()
        test_bad_section()
        test_parity_stack_not_body()
        test_parity_body_not_stack()
        test_blocked_by_cycle()
        test_missing_blocked_by_target()
        test_bad_id_format()
        test_duplicate_ids()
        test_mis_sort_priority()
        test_ready_first_correct()
        test_ready_first_wrong()
        test_inconclusive_last_correct()
        test_inconclusive_last_wrong()
        test_inconclusive_pairing()
        test_aggregated_still_present()
        test_year_rollover()
        test_flat_file()
        test_cli_exit_codes()
        test_collect_absent_file()
        test_collect_clean_file()
        test_collect_broken_file()
        test_run_lint_integration_open_issues_broken()
        test_run_lint_integration_open_issues_clean()
    except Fail as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print("\nAll tests passed.")
