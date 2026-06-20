#!/usr/bin/env python3
"""allocate-address.py — atomic creation-order address allocation for the vault.

DragonScale Mechanism 2. Reserves the next address of the form c-NNNNNN and
increments the counter under an exclusive fcntl.flock. On a missing counter
file, recovers by scanning the vault for the highest existing c-NNNNNN in page
frontmatter and resuming from max+1. Never silently resets to 1 in a non-empty
vault.

Locking uses fcntl.flock (POSIX advisory lock, the flock(2) syscall) rather than
the util-linux flock(1) CLI, so it works on macOS and Linux with no external
binary. The lock auto-releases when the file descriptor closes, including on
process death. Mirrors the locking approach already used by
scripts/tiling-check.py (Mechanism 3).

Vault root via lib/vault_root.py resolver (KM_VAULT_PATH env -> cwd), matching
the sibling DragonScale scripts (tiling-check.py, boundary-score.py). This
completes the PR0 resolver routing for the address allocator.

Usage:
  allocate-address.py            # prints the reserved address (e.g. c-000042)
  allocate-address.py --peek     # prints the next value without incrementing
  allocate-address.py --rebuild  # recomputes counter from max observed and exits

Exit codes:
  0 success
  1 lock acquisition failed (another writer held the lock past the 5s timeout)
  2 .vault-meta directory missing and cannot be created
  3 counter value corrupt/non-numeric, or unknown mode
"""

from __future__ import annotations

import fcntl
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from vault_root import resolve_vault_root  # noqa: E402

VAULT_ROOT = resolve_vault_root()
COUNTER_FILE = VAULT_ROOT / ".vault-meta" / "address-counter.txt"
LOCK_FILE = VAULT_ROOT / ".vault-meta" / ".address.lock"
WIKI_DIR = VAULT_ROOT / "wiki"

LOCK_TIMEOUT_SEC = 5
EXIT_LOCK = 1
EXIT_META = 2
EXIT_CORRUPT = 3

# address: c-NNNNNN  (exactly six digits) on its own frontmatter line.
ADDR_RE = re.compile(r"^address:\s+c-([0-9]{6})\s*$")


def scan_max_c_address() -> int:
    """Largest NNNNNN from 'address: c-NNNNNN' lines inside the FIRST YAML
    frontmatter block of each wiki .md file. Code-block examples and body prose
    are excluded. Returns 0 if none found or the wiki dir is absent."""
    if not WIKI_DIR.is_dir():
        return 0
    max_n = 0
    for path in WIKI_DIR.rglob("*.md"):
        if not path.is_file():
            continue
        try:
            with path.open(encoding="utf-8") as fh:
                first = fh.readline()
                if first.rstrip("\n") != "---":
                    continue  # no leading frontmatter block; skip file
                for line in fh:
                    s = line.rstrip("\n")
                    if s == "---":
                        break  # end of frontmatter; stop before body
                    m = ADDR_RE.match(s)
                    if m:
                        n = int(m.group(1))
                        if n > max_n:
                            max_n = n
        except OSError:
            continue
    return max_n


def read_or_recover_counter() -> int:
    if not COUNTER_FILE.is_file():
        val = scan_max_c_address() + 1
        COUNTER_FILE.write_text(f"{val}\n")
        sys.stderr.write(
            f"INFO: counter file missing; recovered from vault scan, set to {val}\n"
        )
    raw = COUNTER_FILE.read_text().strip()
    if not re.fullmatch(r"[0-9]+", raw):
        sys.stderr.write(
            f"ERR: counter file content is not a positive integer: {raw}\n"
        )
        sys.exit(EXIT_CORRUPT)
    return int(raw)


def acquire_lock() -> int:
    """Exclusive advisory lock with a 5s timeout, polling LOCK_NB. Returns the
    held fd (released by the caller via fcntl.LOCK_UN + close)."""
    fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_RDWR, 0o644)
    deadline = time.monotonic() + LOCK_TIMEOUT_SEC
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except OSError:
            if time.monotonic() > deadline:
                sys.stderr.write(
                    "ERR: could not acquire address allocator lock within 5s\n"
                )
                os.close(fd)
                sys.exit(EXIT_LOCK)
            time.sleep(0.05)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "allocate"

    try:
        COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        sys.stderr.write("ERR: cannot create .vault-meta/\n")
        sys.exit(EXIT_META)

    fd = acquire_lock()
    try:
        if mode == "--peek":
            print(read_or_recover_counter())
        elif mode == "--rebuild":
            val = scan_max_c_address() + 1
            COUNTER_FILE.write_text(f"{val}\n")
            print(f"Counter rebuilt: next = {val}")
        elif mode in ("allocate", ""):
            current = read_or_recover_counter()
            COUNTER_FILE.write_text(f"{current + 1}\n")
            print("c-%06d" % current)
        else:
            sys.stderr.write(f"ERR: unknown mode: {mode}\n")
            sys.stderr.write(f"Usage: {sys.argv[0]} [allocate|--peek|--rebuild]\n")
            sys.exit(EXIT_CORRUPT)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


if __name__ == "__main__":
    main()
