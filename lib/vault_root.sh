# lib/vault_root.sh — shell counterpart to lib/vault_root.py.
#
# Source this from any shell script that needs to know the vault root:
#
#     # shellcheck source=lib/vault_root.sh
#     . "$(dirname "$0")/../lib/vault_root.sh"
#     KM_VAULT_ROOT="$(km_resolve_vault_root "$1")"
#
# Resolution order matches the Python helper:
#
#     KM_VAULT_PATH (env)  ->  positional arg ($1)  ->  current working directory
#
# Functions:
#   km_resolve_vault_root [cli_arg]   prints the resolved vault root
#   km_resolve_wiki_root  [cli_arg]   prints <vault_root>/wiki

# Print the resolved vault root. Does not verify existence.
km_resolve_vault_root() {
  local arg="${1:-}"
  if [ -n "${KM_VAULT_PATH:-}" ]; then
    # Resolve to absolute path, expand ~. Use cd to normalize.
    (cd "${KM_VAULT_PATH/#\~/$HOME}" 2>/dev/null && pwd) || printf '%s\n' "${KM_VAULT_PATH/#\~/$HOME}"
    return 0
  fi
  if [ -n "$arg" ]; then
    (cd "${arg/#\~/$HOME}" 2>/dev/null && pwd) || printf '%s\n' "${arg/#\~/$HOME}"
    return 0
  fi
  pwd
}

# Print the resolved wiki root (<vault_root>/wiki). With KM_VAULT_PATH set,
# argv is ignored. Without env, argv is treated as a wiki root directly to stay
# backward-compatible with existing callers.
km_resolve_wiki_root() {
  local arg="${1:-}"
  if [ -n "${KM_VAULT_PATH:-}" ]; then
    local root
    root="$(km_resolve_vault_root)"
    printf '%s\n' "$root/wiki"
    return 0
  fi
  if [ -n "$arg" ]; then
    (cd "${arg/#\~/$HOME}" 2>/dev/null && pwd) || printf '%s\n' "${arg/#\~/$HOME}"
    return 0
  fi
  printf '%s\n' "$(pwd)/wiki"
}
