#!/usr/bin/env python3
"""test_release_gate.py — release lint-gate scoping guard (SPEC-2.0.0-consolidation S4).

The release lint gate MUST be scoped to the plugin distribution. `scripts/run-lint.py`
lints the working Obsidian vault (`wiki/`), which is not distributed; its severity
findings (the pre-existing 182-error working-vault content) must NEVER block a release.
The gate blocks only when run-lint itself cannot run (crash / unparseable JSON).

This is a regression guard against the "release lint-gate trap": before the 2.0.0
consolidation, `bin/release.py` blocked on `run-lint totals.error != 0`, so a release
could never be cut while the demo vault carried any lint finding.

Usage:
  python3 tests/test_release_gate.py     # exits 0 on pass, 1 on drift
  make test-release-gate
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("release", ROOT / "bin" / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)  # defines lint_gate(); main() is under __main__ guard

FAILS = 0


def check(name, cond):
    global FAILS
    if cond:
        print(f"  ok  {name}")
    else:
        FAILS += 1
        print(f"FAIL: {name}")


# PASS — working-vault findings never block (the real-world 182-error case)
check(
    "vault findings do not block (rc=0, error=182 -> pass)",
    release.lint_gate(0, '{"totals": {"error": 182, "warn": 56, "info": 1}}') is None,
)
check("zero findings pass (rc=0, error=0)", release.lint_gate(0, '{"totals": {"error": 0}}') is None)

# BLOCK — a broken linter must still bite (gate is not a no-op)
check("run-lint crash blocks (rc!=0 -> 4)", release.lint_gate(1, "") == 4)
check("unparseable JSON blocks (rc=0, bad stdout -> 4)", release.lint_gate(0, "not json") == 4)
check("missing totals blocks (rc=0, no totals key -> 4)", release.lint_gate(0, '{"date": "x"}') == 4)

if FAILS:
    print(f"\n{FAILS} release-gate check(s) FAILED.")
    sys.exit(1)
print("\nAll release-gate checks passed.")
