#!/usr/bin/env bash
# Tests for lib/vault_root.sh — KM_VAULT_PATH -> argv -> cwd.
# Run: bash tests/test_vault_root.sh
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=../lib/vault_root.sh
. "$REPO_ROOT/lib/vault_root.sh"

PASS=0
FAIL=0

ok() { printf 'PASS %s\n' "$1"; PASS=$((PASS+1)); }
no() { printf 'FAIL %s: expected %q, got %q\n' "$1" "$2" "$3" >&2; FAIL=$((FAIL+1)); }

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then ok "$label"; else no "$label" "$expected" "$actual"; fi
}

# 1. default = cwd
unset KM_VAULT_PATH
TMP1="$(mktemp -d "${TMPDIR:-/tmp}/vault_root_test.XXXXXX")"
got="$(cd "$TMP1" && km_resolve_vault_root)"
# macOS /var → /private/var realpath dance; just compare resolved
expected="$(cd "$TMP1" && pwd -P)"
assert_eq "vault_root default = cwd" "$expected" "$got"

got="$(cd "$TMP1" && km_resolve_wiki_root)"
assert_eq "wiki_root default = cwd/wiki" "$expected/wiki" "$got"

# 2. argv wins over cwd
unset KM_VAULT_PATH
TMP2="$(mktemp -d "${TMPDIR:-/tmp}/vault_root_test.XXXXXX")"
expected2="$(cd "$TMP2" && pwd -P)"
got="$(km_resolve_vault_root "$TMP2")"
assert_eq "vault_root argv wins over cwd" "$expected2" "$got"

got="$(km_resolve_wiki_root "$TMP2")"
assert_eq "wiki_root argv = path directly" "$expected2" "$got"

# 3. env wins over argv
TMP_ENV="$(mktemp -d "${TMPDIR:-/tmp}/vault_root_test.XXXXXX")"
TMP_ARGV="$(mktemp -d "${TMPDIR:-/tmp}/vault_root_test.XXXXXX")"
expected_env="$(cd "$TMP_ENV" && pwd -P)"
KM_VAULT_PATH="$TMP_ENV" got="$(km_resolve_vault_root "$TMP_ARGV")"
assert_eq "vault_root env wins over argv" "$expected_env" "$got"

KM_VAULT_PATH="$TMP_ENV" got="$(km_resolve_wiki_root "$TMP_ARGV")"
assert_eq "wiki_root env wins over argv" "$expected_env/wiki" "$got"

# 4. env wins over cwd
TMP_CWD="$(mktemp -d "${TMPDIR:-/tmp}/vault_root_test.XXXXXX")"
KM_VAULT_PATH="$TMP_ENV" got="$(cd "$TMP_CWD" && km_resolve_vault_root)"
assert_eq "vault_root env wins over cwd" "$expected_env" "$got"

# 5. tilde expansion
KM_VAULT_PATH="~" got="$(km_resolve_vault_root)"
expected_home="$(cd "$HOME" && pwd -P)"
assert_eq "env ~ expands to \$HOME" "$expected_home" "$got"

# Cleanup
rm -rf "$TMP1" "$TMP2" "$TMP_ENV" "$TMP_ARGV" "$TMP_CWD"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
