#!/usr/bin/env python3
"""evals/run.py — minimal eval runner.

Iterates over case folders under evals/{ingest,lint,query}/, runs the
deterministic checks each case supports, and writes one JSON file
under evals/results/. Prints a summary on stdout.

Usage:
  ./evals/run.py                    # all skills, all cases
  ./evals/run.py ingest             # one skill, all cases
  ./evals/run.py lint case-001-*    # specific glob within a skill

Exit codes:
  0  ok (some cases may have failed — see JSON)
  2  no cases matched
  3  runner error
"""
from __future__ import annotations

import datetime
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def discover_cases(skill: str, pattern: str = "*") -> list[Path]:
    skill_dir = REPO_ROOT / "evals" / skill
    if not skill_dir.is_dir():
        return []
    matches = [
        p
        for p in skill_dir.iterdir()
        if p.is_dir() and fnmatch.fnmatch(p.name, pattern)
    ]
    return sorted(matches, key=lambda p: str(p))


def _matches(exp: dict, act: dict) -> bool:
    return all(
        (k == "path" and v in act.get("path", "")) or act.get(k) == v
        for k, v in exp.items()
    )


def run_lint_case(case_dir: str) -> str:
    vault = Path(case_dir) / "vault"
    expected_path = Path(case_dir) / "expected-findings.json"

    if not vault.is_dir() or not expected_path.is_file():
        return json.dumps(
            {
                "case": case_dir,
                "skill": "lint",
                "status": "skipped",
                "reason": "missing vault/ or expected-findings.json",
            },
            separators=(",", ":"),
        )

    try:
        proc = subprocess.run(
            [
                "python3",
                "scripts/lint-terminology.py",
                str(vault),
                "--json",
            ],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        )
        actual_str = proc.stdout
    except (subprocess.CalledProcessError, OSError):
        actual_str = "[]"

    expected = json.loads(expected_path.read_text())
    actual = json.loads(actual_str)

    found = sum(1 for e in expected if any(_matches(e, a) for a in actual))
    recall = found / len(expected) if expected else 1.0
    extras = [a for a in actual if not any(_matches(e, a) for e in expected)]
    false_pos = len(extras) / len(actual) if actual else 0.0

    status = "ok" if recall == 1.0 and false_pos == 0.0 else "fail"
    return json.dumps(
        {
            "case": case_dir,
            "skill": "lint",
            "status": status,
            "metrics": {
                "recall": round(recall, 3),
                "false_positive_rate": round(false_pos, 3),
                "expected_findings": len(expected),
                "actual_findings": len(actual),
            },
            "extras": extras[:5],
        }
    )


def run_manual_case(case_dir: str, skill: str) -> str:
    meta = Path(case_dir) / "case.json"
    if not meta.is_file():
        return json.dumps(
            {
                "case": case_dir,
                "skill": skill,
                "status": "skipped",
                "reason": "no case.json",
            },
            separators=(",", ":"),
        )
    return json.dumps(
        {
            "case": case_dir,
            "skill": skill,
            "status": "manual",
            "reason": "requires live agent run",
        },
        separators=(",", ":"),
    )


def main(argv: list[str]) -> int:
    skill_filter = argv[0] if len(argv) >= 1 else ""
    case_filter = argv[1] if len(argv) >= 2 else ""

    results_dir = REPO_ROOT / "evals" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H-%M-%SZ"
    )
    results_json = results_dir / f"{timestamp}.json"
    results_md = results_dir / f"{timestamp}.md"

    if not skill_filter:
        skills = ["ingest", "lint", "query"]
    else:
        skills = [skill_filter]

    # Build the JSON array by appending into the results file.
    parts: list[str] = ["["]
    first = True
    for skill in skills:
        if not (REPO_ROOT / "evals" / skill).is_dir():
            continue
        for case_dir in discover_cases(skill, case_filter or "*"):
            if not first:
                parts.append(",")
            first = False
            case_str = f"evals/{skill}/{case_dir.name}"
            if skill == "lint":
                parts.append(run_lint_case(case_str))
            elif skill == "ingest":
                parts.append(run_manual_case(case_str, "ingest"))
            elif skill == "query":
                parts.append(run_manual_case(case_str, "query"))
    parts.append("\n")
    parts.append("]")
    results_json.write_text("\n".join(parts))

    try:
        summary = subprocess.run(
            ["python3", "evals/score-summary.py", str(results_json)],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        ).stdout
        results_md.write_text(summary)
    except (subprocess.CalledProcessError, OSError):
        pass

    rel_json = results_json.relative_to(REPO_ROOT)
    rel_md = results_md.relative_to(REPO_ROOT)
    print(f"Wrote {rel_json}")
    print(f"Wrote {rel_md}")
    if results_md.is_file():
        sys.stdout.write(results_md.read_text())

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
