#!/usr/bin/env python3
"""Tests for scripts/lint-orphans.py.

Self-contained: builds a synthetic wiki tree in a tempdir, runs the script as
a subprocess against it, asserts on the output. No pytest dependency.

Run:
  python3 tests/test_lint_orphans.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "lint-orphans.py"


class Fail(AssertionError):
    pass


def write(p: Path, text: str = "") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def make_vault(root: Path) -> None:
    wiki = root / "wiki"
    # canonical roots — excluded by lint-orphans
    write(wiki / "index.md", "[[Linked-Page]] [[Concepts/Nested]]")
    write(wiki / "log.md", "")
    write(wiki / "hot.md", "")
    write(wiki / "overview.md", "")
    # a linked page — should NOT be flagged
    write(wiki / "concepts" / "Linked-Page.md", "Body")
    # a nested page linked via path — should NOT be flagged
    write(wiki / "concepts" / "Nested.md", "Body")
    # two orphans
    write(wiki / "concepts" / "Orphan-A.md", "Body, no inbound links.")
    write(wiki / "entities" / "Orphan-B.md", "Body, no inbound links.")
    # template — currently NOT excluded, but documented behavior we may revisit
    write(wiki / "_templates" / "tpl.md", "[[ignored]]")


def run_json(vault_root: Path) -> dict:
    env = os.environ.copy()
    env["KM_VAULT_PATH"] = str(vault_root)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        env=env, capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        raise Fail(f"FAIL script exit {result.returncode}: {result.stderr}")
    return json.loads(result.stdout)


def test_orphans_detected():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR", "/tmp")) as td:
        vault = Path(td)
        make_vault(vault)
        out = run_json(vault)
        names = sorted(Path(p).name for p in out["items"])
        # Linked-Page and Nested should NOT appear; the two Orphan-* should.
        expected = ["Orphan-A.md", "Orphan-B.md"]
        # _templates/tpl.md may or may not appear — current implementation
        # walks all directories; the script does not filter templates. We
        # accept either, and assert only that the two real orphans show up.
        for needed in expected:
            if needed not in names:
                raise Fail(f"FAIL expected {needed} in orphans, got {names}")
        for forbidden in ("Linked-Page.md", "Nested.md", "index.md", "log.md", "hot.md", "overview.md"):
            if forbidden in names:
                raise Fail(f"FAIL {forbidden} should NOT be flagged as orphan")
        print(f"PASS orphans detected ({len(names)} total, expected ≥ 2)")


def test_argv_form():
    """Without env, argv should still resolve to the given wiki root."""
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR", "/tmp")) as td:
        vault = Path(td)
        make_vault(vault)
        env = {k: v for k, v in os.environ.items() if k != "KM_VAULT_PATH"}
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(vault / "wiki"), "--json"],
            env=env, capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise Fail(f"FAIL argv form exit {result.returncode}: {result.stderr}")
        out = json.loads(result.stdout)
        if out["count"] < 2:
            raise Fail(f"FAIL argv form found {out['count']} orphans, expected ≥ 2")
        print("PASS argv form resolves correctly")


def test_missing_wiki_dir():
    """A vault with no wiki/ directory should return empty, not crash."""
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR", "/tmp")) as td:
        vault = Path(td)
        out = run_json(vault)
        if out["count"] != 0:
            raise Fail(f"FAIL missing wiki/ should give count=0, got {out['count']}")
        print("PASS missing wiki/ handled gracefully")


def test_plain_output():
    """Default (non-JSON) output: one path per line."""
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR", "/tmp")) as td:
        vault = Path(td)
        make_vault(vault)
        env = os.environ.copy()
        env["KM_VAULT_PATH"] = str(vault)
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            env=env, capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise Fail(f"FAIL plain exit {result.returncode}")
        lines = [L for L in result.stdout.splitlines() if L.strip()]
        if len(lines) < 2:
            raise Fail(f"FAIL plain output had {len(lines)} lines, expected ≥ 2")
        print(f"PASS plain output: {len(lines)} lines")


if __name__ == "__main__":
    try:
        test_orphans_detected()
        test_argv_form()
        test_missing_wiki_dir()
        test_plain_output()
    except Fail as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print("\nAll lint-orphans tests passed.")
