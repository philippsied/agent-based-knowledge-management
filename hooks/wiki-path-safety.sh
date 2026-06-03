#!/usr/bin/env bash
# Vault write-safety hook. Deterministic enforcement of two rules:
#
#   1. Path whitelist: writes only into wiki/, scripts/, .vault-meta/,
#      .claude/, $TMPDIR, plus CLAUDE.md / README.md / .gitignore /
#      .gitattributes / .raw/.manifest.json (relative to the resolved
#      vault root).
#   2. Naming convention: wiki/*.md filenames must NOT contain spaces
#      (use hyphenated Title-Case). _templates/ and lint reports are
#      exempt.
#
# Wire as a PreToolUse hook for Write|Edit|NotebookEdit. The hook reads
# the tool-input JSON from stdin and exits 2 with a message on stderr to
# block, or exits 0 to allow.
#
# Vault root resolution (matches lib/vault_root.sh):
#   KM_VAULT_PATH (env)  ->  current working directory
#
# Rationale: A 2026-05-19 batch ingest produced 588 wikilink rewrites and
# 11 misplaced files because the same conventions were enforced only by
# prompt. This hook makes them deterministic.

set -euo pipefail

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    ti = d.get("tool_input", {})
    print(ti.get("file_path") or ti.get("notebook_path", ""))
except Exception:
    print("")
')

if [ -z "$FILE" ]; then
    exit 0   # No file_path — let the tool decide.
fi

# Resolve vault root: env override -> CWD. Mirrors lib/vault_root.py order.
VAULT_ROOT="${KM_VAULT_PATH:-$PWD}"
VAULT_ROOT="$(cd "$VAULT_ROOT" 2>/dev/null && pwd || echo "$VAULT_ROOT")"

# ---------- Guard A: only enforce inside an actual vault ----------
# The plugin may be installed at user scope, so this hook fires in EVERY
# session, including unrelated repos. A non-vault repo has no .vault-meta/
# marker and no KM_VAULT_PATH; pass it through untouched, like the other hooks.
if [ ! -d "$VAULT_ROOT/.vault-meta" ] && [ -z "${KM_VAULT_PATH:-}" ]; then
    exit 0
fi

# ---------- Config: resolve path-safety mode ----------
# Single source: .vault-meta/config.json. No env override.
# Bootstrap is idempotent and silent: vaults predating v1.10.0 get a strict
# config on the next hook fire so the read path has no missing-file branch.
CONFIG_FILE="$VAULT_ROOT/.vault-meta/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    printf '%s\n' '{' '  "version": 1,' '  "path_safety_mode": "strict"' '}' > "$CONFIG_FILE"
fi

MODE=$(python3 -c '
import json, sys
try:
    with open(sys.argv[1]) as fh:
        data = json.load(fh)
except Exception:
    sys.stderr.write("wiki-path-safety: config.json unreadable; falling back to strict\n")
    print("strict"); sys.exit(0)
if data.get("version") != 1:
    sys.stderr.write("wiki-path-safety: config.json unknown version; falling back to strict\n")
    print("strict"); sys.exit(0)
mode = data.get("path_safety_mode")
if mode not in ("strict", "mixed"):
    sys.stderr.write("wiki-path-safety: config.json unknown path_safety_mode; falling back to strict\n")
    print("strict"); sys.exit(0)
print(mode)
' "$CONFIG_FILE")

case "$FILE" in
    /*) ABS="$FILE" ;;
    *)  ABS="$VAULT_ROOT/$FILE" ;;
esac

# ---------- Guard B: only regulate writes inside the resolved vault root ----------
# Out-of-vault writes are not this hook's concern (e.g. KM_VAULT_PATH points at
# the vault while you work in another repo). Let them pass.
case "$ABS" in
    "$VAULT_ROOT"/*) ;;
    *) exit 0 ;;
esac

# ---------- Rule 1: path whitelist ----------
# Two-pass check so the $TMPDIR / /tmp carve-out only applies to paths that
# are NOT under the resolved vault (otherwise a vault placed under /tmp —
# common in test setups — would silently pass every block).
under_vault=0
case "$ABS" in
    "$VAULT_ROOT"/*) under_vault=1 ;;
esac

allowed=0
case "$ABS" in
    "$VAULT_ROOT"/wiki/*)              allowed=1 ;;
    "$VAULT_ROOT"/.raw/.manifest.json) allowed=1 ;;
    "$VAULT_ROOT"/scripts/*)           allowed=1 ;;
    "$VAULT_ROOT"/.vault-meta/*)       allowed=1 ;;
    "$VAULT_ROOT"/.claude/*)           allowed=1 ;;
    "$VAULT_ROOT"/CLAUDE.md)           allowed=1 ;;
    "$VAULT_ROOT"/README.md)           allowed=1 ;;
    "$VAULT_ROOT"/.gitignore)          allowed=1 ;;
    "$VAULT_ROOT"/.gitattributes)      allowed=1 ;;
esac

if [ "$under_vault" -eq 0 ] && [ "$allowed" -ne 1 ]; then
    case "$ABS" in
        /tmp/*|/private/tmp/*) allowed=1 ;;
    esac
    # Match TMPDIR prefix (TMPDIR may be empty in some contexts)
    if [ -n "${TMPDIR:-}" ] && [ "${ABS#${TMPDIR}}" != "$ABS" ]; then
        allowed=1
    fi
fi

if [ "$allowed" -ne 1 ]; then
    # ---------- Rule 1a: .raw/ immutability (hard in both modes) ----------
    case "$ABS" in
        "$VAULT_ROOT"/.raw/*)
            echo "BLOCKED: .raw/ source files are immutable. Only .raw/.manifest.json is writable." >&2
            echo "Attempted path: $ABS" >&2
            echo "Vault root:     $VAULT_ROOT" >&2
            exit 2
            ;;
    esac

    # ---------- Mixed mode: model-visible reminder, allow the write ----------
    if [ "$MODE" = "mixed" ]; then
        REL="${ABS#$VAULT_ROOT/}"
        python3 -c '
import json, sys
rel = sys.argv[1]
msg = (
    "Mixed-mode vault: writing `" + rel + "` outside the wiki whitelist "
    "(wiki/, scripts/, .vault-meta/, .claude/, root CLAUDE.md|README.md|"
    ".gitignore|.gitattributes, .raw/.manifest.json). Write ALLOWED. "
    "If this is non-wiki work (code, tests, build), proceed. "
    "If you meant a wiki page, move it under wiki/."
)
out = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "additionalContext": msg,
    }
}
print(json.dumps(out))
' "$REL"
        exit 0
    fi

    # ---------- Strict mode: block ----------
    case "$ABS" in
        "$VAULT_ROOT"/concepts/*|"$VAULT_ROOT"/entities/*|"$VAULT_ROOT"/sources/*|"$VAULT_ROOT"/people/*|"$VAULT_ROOT"/research/*|"$VAULT_ROOT"/learning/*|"$VAULT_ROOT"/domains/*)
            echo "BLOCKED: wiki content must live under wiki/. Did you mean wiki${ABS#$VAULT_ROOT}?" >&2
            ;;
        *)
            echo "BLOCKED: vault path-safety: writes only allowed under wiki/, scripts/, .vault-meta/, .claude/, \$TMPDIR, or CLAUDE.md / README.md / .gitignore / .gitattributes / .raw/.manifest.json." >&2
            ;;
    esac
    echo "Attempted path: $ABS" >&2
    echo "Vault root:     $VAULT_ROOT" >&2
    exit 2
fi

# ---------- Rule 2: naming convention for wiki/*.md ----------
# Only enforce on wiki/ markdown files; templates and lint reports are exempt.
case "$ABS" in
    "$VAULT_ROOT"/wiki/_templates/*) exit 0 ;;
    "$VAULT_ROOT"/wiki/meta/lint-report-*) exit 0 ;;
esac
BASENAME=$(basename "$ABS")
case "$BASENAME" in
    *.md)
        # Reject space in basename
        if printf '%s' "$BASENAME" | grep -q ' '; then
            HYPHENATED=$(printf '%s' "$BASENAME" | tr ' ' '-')
            echo "BLOCKED: wiki filenames must be hyphenated (no spaces)." >&2
            echo "  Got:      $BASENAME" >&2
            echo "  Expected: $HYPHENATED" >&2
            echo "  Convention enforced because mixed slug styles produced 254 broken wikilinks in a single batch." >&2
            exit 2
        fi
        ;;
esac

exit 0
