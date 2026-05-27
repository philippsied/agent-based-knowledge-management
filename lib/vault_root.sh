#!/usr/bin/env bash
# lib/vault_root.sh — shell wrapper around lib/vault_root.py.
#
# Resolution logic lives in vault_root.py (single source of truth).
# This wrapper preserves the original API for existing shell callers:
#   km_resolve_vault_root [cli_arg]   # prints resolved vault root
#   km_resolve_wiki_root  [cli_arg]   # prints <vault_root>/wiki
#
# Resolution order (matches the Python helper):
#   KM_VAULT_PATH (env)  ->  positional arg  ->  current working directory

_VAULT_ROOT_PY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/vault_root.py"

# Re-export KM_VAULT_PATH so the python subprocess sees it even when callers
# set it via the `VAR=value func` prefix form (which produces a non-exported
# shell variable, invisible to child processes).
km_resolve_vault_root() {
  KM_VAULT_PATH="${KM_VAULT_PATH:-}" python3 "$_VAULT_ROOT_PY" --vault "${1:-}"
}

km_resolve_wiki_root() {
  KM_VAULT_PATH="${KM_VAULT_PATH:-}" python3 "$_VAULT_ROOT_PY" --wiki "${1:-}"
}
