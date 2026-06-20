#!/usr/bin/env bash
# scripts/allocate-address.sh — shell shim around scripts/allocate-address.py.
#
# Allocation logic lives in allocate-address.py (single source of truth). This
# wrapper preserves the original executable API for existing callers
# (wiki-ingest, wiki-lint, setup-dragonscale) and the `[ -x ... ]` feature
# detection checks:
#   ./scripts/allocate-address.sh            # reserve + print the next address
#   ./scripts/allocate-address.sh --peek     # print next without incrementing
#   ./scripts/allocate-address.sh --rebuild  # recompute counter from max observed
#
# The Python implementation guards the counter with fcntl.flock (POSIX flock(2)
# syscall), so it needs no util-linux flock(1) CLI and works on macOS and Linux
# alike. Mirrors the lib/vault_root.sh -> lib/vault_root.py wrapper pattern.
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/allocate-address.py" "$@"
