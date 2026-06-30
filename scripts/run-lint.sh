#!/usr/bin/env bash
# scripts/run-lint.sh — shell shim around scripts/run-lint.py.
#
# The canonical wiki-quality lint aggregator now lives in run-lint.py (single
# source of truth). This wrapper preserves the original executable API for
# existing callers (Makefile `lint`, CI, bin/release.sh, skills/wiki-lint) and
# the `[ -x ... ]` feature detection, with the documented flags unchanged:
#   scripts/run-lint.sh                  # write report + print summary
#   scripts/run-lint.sh /path/to/vault   # explicit vault root
#   scripts/run-lint.sh --json           # JSON only, no report file, no stdout noise
#   scripts/run-lint.sh --quiet          # write report, no stdout
#   scripts/run-lint.sh --no-report      # JSON to stdout, no report file (alias for --json)
#
# Exit codes are owned by run-lint.py (0 read-only/help, 2 usage / missing wiki);
# the exit code never reflects findings. The Python implementation resolves the
# vault root via lib/vault_root.py and fixes the .raw-union dead-link bug the
# legacy shell version carried. Mirrors the allocate-address.sh -> .py wrapper.
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/run-lint.py" "$@"
