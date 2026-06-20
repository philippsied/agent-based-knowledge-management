#!/usr/bin/env python3
"""test_allocate_address.py — behavioral parity tests for the address allocator.

Black-box: invokes scripts/allocate-address.sh (the shell shim, exactly as real
callers do) as a subprocess against a throwaway temp vault selected via
KM_VAULT_PATH. Mirrors the original tests/test_allocate_address.sh suite plus a
20-way concurrency stress that exercises the fcntl.flock guard.

The real repo .vault-meta/ is never touched: every invocation points
KM_VAULT_PATH at a fresh tempdir under $TMPDIR.

Usage:
  python3 tests/test_allocate_address.py
"""

import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHIM = ROOT / "scripts" / "allocate-address.sh"

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


def make_vault():
    base = os.environ.get("TMPDIR") or "/tmp"
    v = Path(tempfile.mkdtemp(prefix="ds-test.", dir=base))
    (v / ".vault-meta").mkdir()
    (v / "wiki").mkdir()
    return v


def run(vault, *args):
    env = dict(os.environ)
    env["KM_VAULT_PATH"] = str(vault)
    return subprocess.run(
        ["bash", str(SHIM), *args],
        capture_output=True, text=True, env=env, timeout=30,
    )


def counter(vault):
    return (vault / ".vault-meta" / "address-counter.txt").read_text().strip()


def test_rebuild_empty():
    v = make_vault()
    try:
        r = run(v, "--rebuild")
        assert_eq("rebuild empty rc", 0, r.returncode)
        assert_eq("rebuild empty stdout", "Counter rebuilt: next = 1", r.stdout.strip())
        assert_eq("counter file value", "1", counter(v))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_peek_idempotent():
    v = make_vault()
    try:
        run(v, "--rebuild")
        p1 = run(v, "--peek").stdout.strip()
        p2 = run(v, "--peek").stdout.strip()
        assert_eq("peek idempotent", p1, p2)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_first_alloc():
    v = make_vault()
    try:
        run(v, "--rebuild")
        r = run(v)
        assert_eq("first alloc", "c-000001", r.stdout.strip())
        assert_eq("counter after 1 alloc", "2", counter(v))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_monotonic():
    v = make_vault()
    try:
        run(v, "--rebuild")
        run(v)
        assert_eq("second alloc", "c-000002", run(v).stdout.strip())
        assert_eq("third alloc", "c-000003", run(v).stdout.strip())
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_concurrent_unique():
    v = make_vault()
    try:
        run(v, "--rebuild")

        def one(_):
            return run(v).stdout.strip()

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            out = list(ex.map(one, range(20)))
        assert_eq("20 concurrent: total count", 20, len(out))
        assert_eq("20 concurrent: unique count", 20, len(set(out)))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_corrupt_counter():
    v = make_vault()
    try:
        (v / ".vault-meta" / "address-counter.txt").write_text("not-a-number\n")
        r = run(v)
        assert_eq("corrupt counter exit", 3, r.returncode)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_recovery_from_max():
    v = make_vault()
    try:
        (v / "wiki" / "fake.md").write_text(
            "---\ntype: concept\naddress: c-000500\n---\n"
        )
        r = run(v, "--peek")
        assert_eq("recovery from max observed", "501", r.stdout.strip())
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_codeblock_ignored():
    v = make_vault()
    try:
        (v / ".vault-meta" / "address-counter.txt").write_text("1\n")
        (v / "wiki" / "doc.md").write_text(
            "---\ntype: concept\n---\n"
            "# Doc with a code-block example\n"
            "```yaml\naddress: c-999999\n```\n"
        )
        r = run(v, "--rebuild")
        assert_eq("code-block ignored, rebuild to 1",
                  "Counter rebuilt: next = 1", r.stdout.strip())
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_unknown_mode():
    v = make_vault()
    try:
        run(v, "--rebuild")
        r = run(v, "--bogus")
        assert_eq("unknown mode exit", 3, r.returncode)
    finally:
        shutil.rmtree(v, ignore_errors=True)


if __name__ == "__main__":
    try:
        test_rebuild_empty()
        test_peek_idempotent()
        test_first_alloc()
        test_monotonic()
        test_concurrent_unique()
        test_corrupt_counter()
        test_recovery_from_max()
        test_codeblock_ignored()
        test_unknown_mode()
    except Fail as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print(f"\n{PASS} checks passed.")
