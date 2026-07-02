#!/usr/bin/env python3
"""test_setup_provisioning.py — counter-seeding provisioning guard (FUP-2).

Regression guard for ADR-0004 (canonical address-counter start = 1). Both setup
scripts must seed .vault-meta/address-counter.txt at 1 so the first allocated
address is c-000001 — NOT the silent off-by-one c-000000 that a 0 seed produced
(the allocator's [0-9]+ guard accepts 0 and prints c-000000 at exit 0, so nothing
catches it).

Two layers:
- Behavioral: run bin/setup-vault.py against a throwaway temp vault, then the real
  allocator, asserting seed == 1 and first address == c-000001. Offline & safe —
  plugin downloads self-skip without plugin dirs, and the TTY path-safety prompt
  self-skips under a non-tty subprocess (stdin=DEVNULL). The real repo .vault-meta/
  is never touched; every run targets a fresh tempdir under $TMPDIR.
- Static drift-guard: assert BOTH setup scripts seed 1 and neither seeds 0. This
  covers bin/setup-dragonscale.py without provisioning the full plugin tree it
  requires on disk (scripts/, skills/wiki-fold/).

Usage:
  python3 tests/test_setup_provisioning.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETUP_VAULT = ROOT / "bin" / "setup-vault.py"
SETUP_DRAGONSCALE = ROOT / "bin" / "setup-dragonscale.py"
ALLOCATOR = ROOT / "scripts" / "allocate-address.py"

PASS = 0


class Fail(SystemExit):
    pass


def ok(label):
    global PASS
    print(f"OK   {label}")
    PASS += 1


def assert_eq(label, expected, actual):
    if expected != actual:
        raise Fail(f"FAIL {label}: expected {expected!r}, got {actual!r}")
    ok(label)


def assert_true(label, cond):
    if not cond:
        raise Fail(f"FAIL {label}")
    ok(label)


def make_tmp():
    base = os.environ.get("TMPDIR") or "/tmp"
    return Path(tempfile.mkdtemp(prefix="ds-setup-test.", dir=base))


def counter_of(vault):
    return (vault / ".vault-meta" / "address-counter.txt").read_text().strip()


def run_setup_vault(vault):
    # stdin=DEVNULL => non-tty => path-safety prompt self-skips (defaults strict).
    return subprocess.run(
        [sys.executable, str(SETUP_VAULT), str(vault)],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60,
    )


def run_allocator(vault, *args):
    env = dict(os.environ)
    env["KM_VAULT_PATH"] = str(vault)
    return subprocess.run(
        [sys.executable, str(ALLOCATOR), *args],
        capture_output=True, text=True, env=env, timeout=30,
    )


def test_setup_vault_seeds_one():
    v = make_tmp()
    try:
        r = run_setup_vault(v)
        assert_eq("setup-vault rc", 0, r.returncode)
        assert_eq("setup-vault seeds counter = 1", "1", counter_of(v))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_first_address_is_c000001():
    v = make_tmp()
    try:
        run_setup_vault(v)
        r = run_allocator(v)  # allocate mode
        assert_eq("first allocation after provisioning", "c-000001", r.stdout.strip())
        assert_eq("counter advanced to 2", "2", counter_of(v))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_setup_vault_idempotent():
    v = make_tmp()
    try:
        run_setup_vault(v)
        run_allocator(v)              # advances counter to 2
        run_setup_vault(v)            # re-run must NOT reset an active vault
        assert_eq("re-run does not reset counter", "2", counter_of(v))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_both_scripts_seed_one_statically():
    for label, path in (
        ("setup-vault.py", SETUP_VAULT),
        ("setup-dragonscale.py", SETUP_DRAGONSCALE),
    ):
        src = path.read_text()
        assert_true(f"{label} seeds counter at 1", 'counter.write_text("1\\n")' in src)
        assert_true(f"{label} does not seed counter at 0", 'counter.write_text("0\\n")' not in src)


if __name__ == "__main__":
    try:
        test_setup_vault_seeds_one()
        test_first_address_is_c000001()
        test_setup_vault_idempotent()
        test_both_scripts_seed_one_statically()
    except Fail as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print(f"\n{PASS} checks passed.")
