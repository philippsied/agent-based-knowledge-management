#!/usr/bin/env bash
# Tests for hooks/wiki-path-safety.sh - vault-detection guards, path/naming rules,
# v1.10.0 mode dimension (strict/mixed), config bootstrap, NotebookEdit shape.
#
#   Guard A: enforce only inside an actual vault (.vault-meta/ marker or KM_VAULT_PATH).
#   Guard B: regulate only writes that resolve inside the vault root.
#   Rule 1:  path whitelist for in-vault writes.
#   Rule 2:  wiki/*.md filenames must be hyphenated; _templates and lint reports exempt.
#   Modes:   strict (default) / mixed (PreToolUse JSON reminder for non-whitelist
#            in-vault paths). .raw/ immutability and hyphenation stay hard in both.
#
# Exit 0 = allow, exit 2 = block. Mixed-mode allow with reminder = exit 0 + stdout JSON.
# Run: bash tests/test_wiki_path_safety.sh
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$REPO_ROOT/hooks/wiki-path-safety.sh"

PASS=0
FAIL=0

ck() {
  if [ "$2" = "$3" ]; then printf 'PASS %s (exit %s)\n' "$1" "$3"; PASS=$((PASS+1))
  else printf 'FAIL %s: want exit %s, got %s\n' "$1" "$2" "$3" >&2; FAIL=$((FAIL+1)); fi
}

ck_contains() {
  # ck_contains <name> <substring> <haystack>
  if printf '%s' "$3" | grep -qF -- "$2"; then
    printf 'PASS %s (contains %s)\n' "$1" "$2"; PASS=$((PASS+1))
  else
    printf 'FAIL %s: %s not found (got: %s)\n' "$1" "$2" "$3" >&2; FAIL=$((FAIL+1))
  fi
}

# run <cwd> <file_path> [KM_VAULT_PATH] -> echoes exit code only (legacy semantics).
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

# run_capture <cwd> <file_path> -> populates globals EXIT, STDOUT, STDERR.
run_capture() {
  local cwd="$1" fp="$2" json tmp
  json=$(printf '{"tool_input":{"file_path":"%s"}}' "$fp")
  tmp=$(mktemp "${TMPDIR:-/tmp}/wps_out.XXXXXX")
  STDERR=$(printf '%s' "$json" | ( cd "$cwd" && bash "$HOOK" ) 2>&1 1>"$tmp")
  EXIT=$?
  STDOUT=$(cat "$tmp"); rm -f "$tmp"
}

# run_notebook <cwd> <notebook_path> -> populates globals EXIT, STDOUT, STDERR.
# Mirrors the NotebookEdit tool input shape (no file_path).
run_notebook() {
  local cwd="$1" np="$2" json tmp
  json=$(printf '{"tool_input":{"notebook_path":"%s"}}' "$np")
  tmp=$(mktemp "${TMPDIR:-/tmp}/wps_out.XXXXXX")
  STDERR=$(printf '%s' "$json" | ( cd "$cwd" && bash "$HOOK" ) 2>&1 1>"$tmp")
  EXIT=$?
  STDOUT=$(cat "$tmp"); rm -f "$tmp"
}

with_config() {
  # with_config <vault> <mode>
  printf '{"version":1,"path_safety_mode":"%s"}' "$2" > "$1/.vault-meta/config.json"
}

with_raw_config() {
  # with_raw_config <vault> <raw-content>
  printf '%s' "$2" > "$1/.vault-meta/config.json"
}

rm_config() {
  rm -f "$1/.vault-meta/config.json"
}

unset KM_VAULT_PATH

V="$(mktemp -d "${TMPDIR:-/tmp}/wps_vault.XXXXXX")"
mkdir -p "$V/.vault-meta" "$V/wiki/_templates" "$V/.raw" "$V/src" "$V/scripts" "$V/concepts" "$V/docs"
N="$(mktemp -d "${TMPDIR:-/tmp}/wps_plain.XXXXXX")"; mkdir -p "$N/src"
O="$(mktemp -d "${TMPDIR:-/tmp}/wps_other.XXXXXX")"; mkdir -p "$O/src"
V="$(cd "$V" && pwd -P)"; N="$(cd "$N" && pwd -P)"; O="$(cd "$O" && pwd -P)"

# Each section explicitly sets the mode it expects, so test ordering does not matter.
with_config "$V" "strict"

# --- Guard A: vault detection ---
ck "A1 non-vault src write allowed"    0 "$(run "$N" "$N/src/foo.ts")"
ck "A2 non-vault arbitrary abs path"   0 "$(run "$N" "/etc/hosts")"
ck "A3 vault detected, src blocked"    2 "$(run "$V" "$V/src/foo.ts")"

# --- Guard B: KM_VAULT_PATH set, write lands outside the vault ---
ck "B1 env-vault out-of-vault allow"   0 "$(run "$O" "$O/src/x.ts" "$V")"
ck "B2 env-vault in-vault src block"   2 "$(run "$O" "$V/src/x.ts" "$V")"

# --- Rule 1: whitelist inside a real vault (strict) ---
ck "R1 wiki page allowed"              0 "$(run "$V" "$V/wiki/page.md")"
ck "R2 non-whitelisted src blocked"    2 "$(run "$V" "$V/src/foo.ts")"
ck "R3 .raw source immutable"          2 "$(run "$V" "$V/.raw/source.md")"
ck "R4 .raw/.manifest.json allowed"    0 "$(run "$V" "$V/.raw/.manifest.json")"
ck "R5 CLAUDE.md allowed"              0 "$(run "$V" "$V/CLAUDE.md")"
ck "R6 top-level concepts blocked"     2 "$(run "$V" "$V/concepts/x.md")"
ck "R7 scripts allowed"                0 "$(run "$V" "$V/scripts/x.sh")"
ck "R8 docs/ blocked in strict"        2 "$(run "$V" "$V/docs/foo.md")"

# --- Rule 2: hyphenation ---
ck "N1 hyphenated wiki name allowed"   0 "$(run "$V" "$V/wiki/good-name.md")"
ck "N2 spaced wiki name blocked"       2 "$(run "$V" "$V/wiki/Bad Name.md")"
ck "N3 _templates spaced exempt"       0 "$(run "$V" "$V/wiki/_templates/Tpl With Space.md")"

# --- Edge ---
EMPTY=$(printf '{"tool_input":{}}' | ( cd "$N" && bash "$HOOK" ) >/dev/null 2>&1; printf '%s' "$?")
ck "E1 no file_path allowed"           0 "$EMPTY"

# --- Mode dimension: mixed ---
with_config "$V" "mixed"
run_capture "$V" "$V/wiki/page.md"
ck "M1 mixed + wiki page exit"         0 "$EXIT"
run_capture "$V" "$V/src/foo.ts"
ck "M2 mixed + non-wiki exit"          0 "$EXIT"
ck_contains "M2 reminder JSON has permissionDecision" '"permissionDecision": "allow"' "$STDOUT"
ck_contains "M2 reminder JSON has relative path"      'src/foo.ts'                    "$STDOUT"
ck_contains "M2 reminder JSON has hookEventName"      '"hookEventName": "PreToolUse"' "$STDOUT"
run_capture "$V" "$V/.raw/source.md"
ck "M3 mixed + .raw still blocks"      2 "$EXIT"
ck_contains "M3 .raw stderr message"   "immutable" "$STDERR"
run_capture "$V" "$V/wiki/Bad Name.md"
ck "M4 mixed + spaced wiki name blocks" 2 "$EXIT"
ck_contains "M4 hyphenation stderr"    "hyphenated" "$STDERR"
run_capture "$V" "$V/concepts/x.md"
ck "M5 mixed + concepts exit"          0 "$EXIT"
ck_contains "M5 concepts reminder names path" "concepts/x.md" "$STDOUT"
run_capture "$V" "$V/docs/foo.md"
ck "M6 mixed + docs exit"              0 "$EXIT"
ck_contains "M6 docs reminder names path" "docs/foo.md" "$STDOUT"

# --- NotebookEdit shape (notebook_path only, no file_path) ---
with_config "$V" "strict"
run_notebook "$V" "$V/src/nb.ipynb"
ck "NB1 strict + notebook outside wiki blocks" 2 "$EXIT"
with_config "$V" "mixed"
run_notebook "$V" "$V/src/nb.ipynb"
ck "NB2 mixed + notebook outside wiki allows"  0 "$EXIT"
ck_contains "NB2 notebook reminder names path" "src/nb.ipynb" "$STDOUT"
run_notebook "$V" "$V/wiki/notebook.ipynb"
ck "NB3 wiki notebook allowed"         0 "$EXIT"

# --- Config bootstrap + malformed + unknown ---
rm_config "$V"
run_capture "$V" "$V/wiki/page.md"
ck "C1 missing config bootstrap exit"  0 "$EXIT"
BOOT="missing"; [ -f "$V/.vault-meta/config.json" ] && BOOT="present"
ck "C1 missing config wrote file"      "present" "$BOOT"
ck_contains "C1 bootstrap config has strict" '"path_safety_mode": "strict"' "$(cat "$V/.vault-meta/config.json")"

with_raw_config "$V" 'not json'
run_capture "$V" "$V/src/foo.ts"
ck "C2 malformed JSON exits as strict" 2 "$EXIT"
ck_contains "C2 stderr warns about unreadable" "config.json unreadable" "$STDERR"

with_raw_config "$V" '{"version": 99, "path_safety_mode": "mixed"}'
run_capture "$V" "$V/src/foo.ts"
ck "C3 unknown version exits as strict" 2 "$EXIT"
ck_contains "C3 stderr warns about unknown version" "unknown version" "$STDERR"

with_raw_config "$V" '{"version": 1, "path_safety_mode": "unknown"}'
run_capture "$V" "$V/src/foo.ts"
ck "C4 unknown mode exits as strict"   2 "$EXIT"
ck_contains "C4 stderr warns about unknown mode" "unknown path_safety_mode" "$STDERR"

# cleanup
find "$V" "$N" "$O" -depth -delete 2>/dev/null || true
printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
