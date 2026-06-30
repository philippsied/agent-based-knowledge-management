#!/usr/bin/env python3
"""
lint-programs.py — Validate research-queue program codes.

Parses <vault>/wiki/meta/research-queue.md plus the program seed list in
<vault>/wiki/decisions/Research-Program-Codes.md, and runs:

  1. Program-code whitelist check: every row's `program` is in the seed
     list, or is the explicit "?" triage placeholder.
  2. Program-home-page existence: each whitelisted code has a page at
     <vault>/wiki/research/programs/<CODE>.md.
  3. Triage report: list rows with program = "?".

Multi-program rows (e.g. "EVAL, OPS" or "EVAL / OPS") are split and
every listed code is validated; the first is treated as primary.

Drift detection (compare declared program vs deliverable folder
destinations) is NOT implemented — it requires per-task deliverable
metadata that does not yet live in the queue table.

Vault root resolution (matches lib/vault_root.sh):
    --vault flag  ->  KM_VAULT_PATH env  ->  current working directory

Exit codes:
  0  no problems
  1  validation errors (unknown code, missing home page)
  2  queue or decision file not found

Optional --json: machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROW_RE = re.compile(r"^\|\s*(R-\d{4}-\d{3})\s*\|")
# A program seed-list row in the decision doc looks like:
#   | `EVAL` | Evals, Judges, Skill Quality | ... |
SEED_RE = re.compile(r"^\|\s*`([A-Z]{2,5})`\s*\|")


def resolve_vault(cli_arg: str | None) -> Path:
    """Mirror lib/vault_root.py order: --vault > KM_VAULT_PATH > CWD."""
    for candidate in (cli_arg, os.environ.get("KM_VAULT_PATH"), os.getcwd()):
        if not candidate:
            continue
        p = Path(candidate).expanduser().resolve()
        if p.exists():
            return p
    raise SystemExit("ERROR: vault root could not be resolved")


def parse_queue_programs(text: str) -> list[dict]:
    """Extract id + program cell from the Active queue table."""
    in_active = False
    rows: list[dict] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            in_active = s.lower().startswith("## active queue")
            continue
        if not in_active or not ROW_RE.match(line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 9:
            continue
        rows.append({"id": cells[0], "program_cell": cells[3]})
    return rows


def parse_seed_codes(text: str) -> list[str]:
    """Extract program codes from the Seed list table in the decision doc."""
    codes: list[str] = []
    in_seed = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            in_seed = s.lower().startswith("## seed list")
            continue
        if not in_seed:
            continue
        m = SEED_RE.match(line)
        if m:
            codes.append(m.group(1))
    return codes


def split_program_cell(cell: str) -> list[str]:
    """Split 'EVAL', 'EVAL, OPS', 'EVAL / OPS', '?' into a list of tokens.

    Keeps the explicit '?' triage marker as its own single-element list.
    """
    cell = cell.strip()
    if not cell:
        return []
    if cell == "?":
        return ["?"]
    for sep in [",", "/", "·", "|"]:
        cell = cell.replace(sep, " ")
    return [tok for tok in cell.split() if tok]


def analyze(queue_path: Path, decision_path: Path, programs_dir: Path,
            queue_rows: list[dict], seed_set: set[str]) -> dict:
    """Run the program-code checks. Returns the exact dict the CLI emits under
    --json (the canonical structured result)."""
    # 1. Whitelist check.
    unknown: list[tuple[str, str]] = []  # (task_id, code)
    triage: list[str] = []  # task IDs with program = '?'
    used_codes: set[str] = set()
    for row in queue_rows:
        tokens = split_program_cell(row["program_cell"])
        if not tokens:
            unknown.append((row["id"], "<empty>"))
            continue
        if tokens == ["?"]:
            triage.append(row["id"])
            continue
        for tok in tokens:
            if tok not in seed_set:
                unknown.append((row["id"], tok))
            else:
                used_codes.add(tok)

    # 2. Home-page existence.
    missing_pages: list[str] = []
    for code in sorted(seed_set):
        page = programs_dir / f"{code}.md"
        if not page.exists():
            missing_pages.append(code)

    return {
        "queue_file": str(queue_path),
        "decision_file": str(decision_path),
        "seed_codes": sorted(seed_set),
        "tasks_parsed": len(queue_rows),
        "unknown_codes": [{"task": t, "code": c} for (t, c) in unknown],
        "triage_tasks": triage,
        "missing_home_pages": missing_pages,
        "codes_in_use": sorted(used_codes),
        "codes_unused": sorted(seed_set - used_codes),
    }


def collect(vault_root: Path) -> dict:
    """Importable entrypoint for run-lint.py. Returns the same dict the CLI
    emits under --json, without print(). Assumes the queue + decision files
    exist (run-lint.py gates on their presence before calling)."""
    queue_path = vault_root / "wiki" / "meta" / "research-queue.md"
    decision_path = vault_root / "wiki" / "decisions" / "Research-Program-Codes.md"
    programs_dir = vault_root / "wiki" / "research" / "programs"
    queue_rows = parse_queue_programs(queue_path.read_text(encoding="utf-8"))
    seed_set = set(parse_seed_codes(decision_path.read_text(encoding="utf-8")))
    return analyze(queue_path, decision_path, programs_dir, queue_rows, seed_set)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", help="Vault root override (else KM_VAULT_PATH or CWD)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    queue_path = vault / "wiki" / "meta" / "research-queue.md"
    decision_path = vault / "wiki" / "decisions" / "Research-Program-Codes.md"
    programs_dir = vault / "wiki" / "research" / "programs"

    for required in (queue_path, decision_path):
        if not required.exists():
            print(f"ERROR: {required} not found.", file=sys.stderr)
            return 2

    queue_rows = parse_queue_programs(queue_path.read_text(encoding="utf-8"))
    seed_codes = parse_seed_codes(decision_path.read_text(encoding="utf-8"))
    seed_set = set(seed_codes)

    if not seed_set:
        print(
            f"ERROR: no seed codes parsed from {decision_path} "
            f"— check the '## Seed list' table format.",
            file=sys.stderr,
        )
        return 1

    result = analyze(queue_path, decision_path, programs_dir, queue_rows, seed_set)
    unknown = [(u["task"], u["code"]) for u in result["unknown_codes"]]
    triage = result["triage_tasks"]
    missing_pages = result["missing_home_pages"]
    used_codes = set(result["codes_in_use"])

    errors = bool(unknown or missing_pages)

    if args.json:
        print(json.dumps(result, indent=2))
        return 1 if errors else 0

    # Human text output.
    print("# Program-code lint")
    print(f"Queue:    {queue_path}")
    print(f"Decision: {decision_path}")
    print(f"Seed codes: {', '.join(sorted(seed_set))}")
    print(f"Tasks parsed: {len(queue_rows)}")
    print()

    if unknown:
        print("FAIL Unknown program codes:")
        for task, code in unknown:
            print(f"   {task} -> {code!r} (not in seed list)")
    else:
        print("OK   All program codes are whitelisted.")

    if triage:
        print(f"WARN Triage queue (program = '?'): {', '.join(triage)}")
    else:
        print("OK   No tasks awaiting program triage.")

    if missing_pages:
        print("FAIL Missing program home pages:")
        for code in missing_pages:
            print(f"   wiki/research/programs/{code}.md")
    else:
        print("OK   All program home pages exist.")

    unused = sorted(seed_set - used_codes)
    if unused:
        print(f"INFO Seed codes not yet used by any queued task: {', '.join(unused)}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
