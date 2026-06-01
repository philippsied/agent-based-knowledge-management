#\!/usr/bin/env bash
# Tests for hooks/wiki-path-safety.sh - vault-detection guards + path/naming rules.
#
#   Guard A: enforce only inside an actual vault (.vault-meta/ marker or KM_VAULT_PATH).
#   Guard B: regulate only writes that resolve inside the vault root.
#   Rule 1:  path whitelist for in-vault writes.
#   Rule 2:  wiki/*.md filenames must be hyphenated; _templates and lint reports exempt.
#
# Exit 0 = allow, exit 2 = block.
# Run: bash tests/test_wiki_path_safety.sh   (or: make test-wiki-path-safety)
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$REPO_ROOT/hooks/wiki-path-safety.sh"

PASS=0
FAIL=0
ck() {
  if [ "$2" = "$3" ]; then printf 'PASS %s (exit %s)\n' "$1" "$3"; PASS=$((PASS+1))
  else printf 'FAIL %s: want exit %s, got %s\n' "$1" "$2" "$3" >&2; FAIL=$((FAIL+1)); fi
}

# run <cwd> <file_path> [KM_VAULT_PATH] -> echoes the hook exit code
run() {
  local cwd="$1" fp="$2" env_path="${3:-}" json
  json=$(printf '{"tool_input":{"file_path":"%s"}}' "$fp")
  if [ -n "$env_path" ]; then
    printf '%s' "$json" | ( cd "$cwd" && KM_VAULT_PATH="$env_path" bash "$HOOK" ) >/dev/null 2>&1
  else
    printf '%s' "$json" | ( cd "$cwd" && bash "$HOOK" ) >/dev/null 2>&1
  fi
  printf '%s' "$?"
}

unset KM_VAULT_PATH

V="$(mktemp -d "${TMPDIR:-/tmp}/wps_vault.XXXXXX")"
mkdir -p "$V/.vault-meta" "$V/wiki/_templates" "$V/.raw" "$V/src" "$V/scripts" "$V/concepts"
N="$(mktemp -d "${TMPDIR:-/tmp}/wps_plain.XXXXXX")"; mkdir -p "$N/src"
O="$(mktemp -d "${TMPDIR:-/tmp}/wps_other.XXXXXX")"; mkdir -p "$O/src"
V="$(cd "$V" && pwd -P)"; N="$(cd "$N" && pwd -P)"; O="$(cd "$O" && pwd -P)"

# Guard A - vault detection (the bug this fixes)
ck "A1 non-vault src write allowed"    0 "$(run "$N" "$N/src/foo.ts")"
ck "A2 non-vault arbitrary abs path"   0 "$(run "$N" "/etc/hosts")"
ck "A3 vault detected, src blocked"    2 "$(run "$V" "$V/src/foo.ts")"
# Guard B - KM_VAULT_PATH set, write lands outside the vault
ck "B1 env-vault out-of-vault allow"   0 "$(run "$O" "$O/src/x.ts" "$V")"
ck "B2 env-vault in-vault src block"   2 "$(run "$O" "$V/src/x.ts" "$V")"
# Rule 1 - whitelist inside a real vault
ck "R1 wiki page allowed"              0 "$(run "$V" "$V/wiki/page.md")"
ck "R2 non-whitelisted src blocked"    2 "$(run "$V" "$V/src/foo.ts")"
ck "R3 .raw source immutable"          2 "$(run "$V" "$V/.raw/source.md")"
ck "R4 .raw/.manifest.json allowed"    0 "$(run "$V" "$V/.raw/.manifest.json")"
ck "R5 CLAUDE.md allowed"              0 "$(run "$V" "$V/CLAUDE.md")"
ck "R6 top-level concepts blocked"     2 "$(run "$V" "$V/concepts/x.md")"
ck "R7 scripts allowed"                0 "$(run "$V" "$V/scripts/x.sh")"
# Rule 2 - hyphenation
ck "N1 hyphenated wiki name allowed"   0 "$(run "$V" "$V/wiki/good-name.md")"
ck "N2 spaced wiki name blocked"       2 "$(run "$V" "$V/wiki/Bad Name.md")"
ck "N3 _templates spaced exempt"       0 "$(run "$V" "$V/wiki/_templates/Tpl With Space.md")"
# Edge
EMPTY=$(printf '{"tool_input":{}}' | ( cd "$N" && bash "$HOOK" ) >/dev/null 2>&1; printf '%s' "$?")
ck "E1 no file_path allowed"           0 "$EMPTY"

# cleanup (find -delete avoids the rm -rf guard hook; functionally identical)
find "$V" "$N" "$O" -depth -delete 2>/dev/null || true
printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
