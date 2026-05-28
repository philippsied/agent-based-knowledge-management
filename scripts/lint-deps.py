#!/usr/bin/env python3
"""
lint-deps.py — Validate the research queue's DAG.

Parses <vault>/wiki/meta/research-queue.md, extracts the Active queue
table, and runs:

  1. ID uniqueness check.
  2. Missing-dep-target check (depends_on points at a known task).
  3. Cycle detection.
  4. "Ready set" computation: queued tasks with all deps in `done`.

Vault root resolution (matches lib/vault_root.sh):
    --vault flag  ->  KM_VAULT_PATH env  ->  current working directory

Exit codes:
  0  no problems (or only diagnostics)
  1  validation errors (duplicate IDs, missing targets, cycles)
  2  queue file not found

Optional --json: machine-readable output.
Optional --ready: print only the ready-set IDs, one per line.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Match a queue row: starts with "| R-YYYY-NNN" followed by pipe-separated cells.
ROW_RE = re.compile(r"^\|\s*(R-\d{4}-\d{3})\s*\|")


def resolve_vault(cli_arg: str | None) -> Path:
    """Mirror lib/vault_root.py order: --vault > KM_VAULT_PATH > CWD."""
    for candidate in (cli_arg, os.environ.get("KM_VAULT_PATH"), os.getcwd()):
        if not candidate:
            continue
        p = Path(candidate).expanduser().resolve()
        if p.exists():
            return p
    raise SystemExit("ERROR: vault root could not be resolved")


def _strip_backticks(s: str) -> str:
    return s.strip().strip("`").strip()


def _parse_deps(cell: str) -> list[str]:
    """Parse the Deps column. '—', '-', empty -> no deps. Otherwise comma-split."""
    cell = cell.strip()
    if not cell or cell in {"—", "-", "–"}:
        return []
    return [tok.strip() for tok in cell.split(",") if tok.strip()]


def parse_queue(text: str) -> list[dict]:
    """Extract rows from the Active queue table.

    Expected column order (per research-queue.md):
        ID | Status | Prio | Program | Title | Brief | Deps | Created | Updated
    """
    in_active = False
    rows: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_active = stripped.lower().startswith("## active queue")
            continue
        if not in_active:
            continue
        if not ROW_RE.match(line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 9:
            continue
        rows.append(
            {
                "id": cells[0],
                "status": _strip_backticks(cells[1]),
                "priority": cells[2],
                "program": cells[3],
                "title": cells[4],
                "brief": cells[5],
                "deps": _parse_deps(cells[6]),
                "created": cells[7],
                "updated": cells[8],
            }
        )
    return rows


def find_cycles(rows: list[dict]) -> list[list[str]]:
    """Return all simple cycles in the depends_on graph.

    Iterative DFS with a recursion stack. Cycles are reported as the
    list of node IDs in cycle order (first node repeats implicitly).
    """
    graph = {r["id"]: r["deps"] for r in rows}
    color: dict[str, int] = {nid: 0 for nid in graph}  # 0=white, 1=gray, 2=black
    cycles: list[list[str]] = []

    def visit(start: str) -> None:
        stack: list[tuple[str, iter]] = [(start, iter(graph.get(start, [])))]
        path: list[str] = [start]
        color[start] = 1
        while stack:
            node, it = stack[-1]
            try:
                nxt = next(it)
            except StopIteration:
                color[node] = 2
                path.pop()
                stack.pop()
                continue
            if nxt not in graph:
                # Missing target — handled by lint_missing_targets, not here.
                continue
            if color.get(nxt, 0) == 1:
                idx = path.index(nxt)
                cycles.append(path[idx:] + [nxt])
                continue
            if color.get(nxt, 0) == 0:
                color[nxt] = 1
                path.append(nxt)
                stack.append((nxt, iter(graph.get(nxt, []))))

    for nid in graph:
        if color[nid] == 0:
            visit(nid)
    return cycles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", help="Vault root override (else KM_VAULT_PATH or CWD)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--ready",
        action="store_true",
        help="print only the ready set (queued + all deps done), one ID per line",
    )
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    queue_path = vault / "wiki" / "meta" / "research-queue.md"

    if not queue_path.exists():
        print(f"ERROR: {queue_path} not found.", file=sys.stderr)
        return 2

    text = queue_path.read_text(encoding="utf-8")
    rows = parse_queue(text)
    by_id = {r["id"]: r for r in rows}

    # 1. Duplicate IDs.
    duplicates: list[str] = []
    seen: set[str] = set()
    for r in rows:
        if r["id"] in seen:
            duplicates.append(r["id"])
        seen.add(r["id"])

    # 2. Missing dep targets.
    missing_targets: list[tuple[str, str]] = []
    for r in rows:
        for dep in r["deps"]:
            if dep not in by_id:
                missing_targets.append((r["id"], dep))

    # 3. Cycles.
    cycles = find_cycles(rows)

    # 4. Ready set.
    ready: list[str] = []
    for r in rows:
        if r["status"] != "queued":
            continue
        if all(by_id.get(d, {}).get("status") == "done" for d in r["deps"]):
            ready.append(r["id"])

    errors = bool(duplicates or missing_targets or cycles)

    if args.ready:
        for rid in ready:
            print(rid)
        return 1 if errors else 0

    if args.json:
        out = {
            "queue_file": str(queue_path),
            "task_count": len(rows),
            "duplicates": duplicates,
            "missing_targets": [
                {"task": t, "missing_dep": d} for (t, d) in missing_targets
            ],
            "cycles": cycles,
            "ready_set": ready,
        }
        print(json.dumps(out, indent=2))
        return 1 if errors else 0

    # Human text output.
    print(f"# Dependency lint — {queue_path}")
    print(f"Tasks parsed: {len(rows)}")
    print()

    if duplicates:
        print(f"FAIL Duplicate IDs: {', '.join(duplicates)}")
    else:
        print("OK   No duplicate IDs.")

    if missing_targets:
        print("FAIL Missing dependency targets:")
        for task, dep in missing_targets:
            print(f"   {task} depends_on {dep}, but {dep} is not in the queue.")
    else:
        print("OK   All dependency targets resolve.")

    if cycles:
        print(f"FAIL Cycles detected ({len(cycles)}):")
        for c in cycles:
            print(f"   {' -> '.join(c)}")
    else:
        print("OK   No cycles.")

    print()
    print(f"Ready set ({len(ready)} task{'s' if len(ready) != 1 else ''} startable now):")
    if ready:
        for rid in ready:
            r = by_id[rid]
            print(f"   {rid} [{r['priority']}/{r['program']}] {r['title']}")
    else:
        print("   (none)")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
