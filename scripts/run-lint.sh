#!/usr/bin/env bash
# run-lint.sh — canonical wiki-quality lint aggregator.
#
# Runs every deterministic check the plugin ships, emits a JSON summary with
# per-check severity, and writes a Markdown report to
# <vault>/wiki/meta/lint-report-YYYY-MM-DD.md. Read-only; never mutates wiki
# content.
#
# Resolution order for the vault root (via lib/vault_root.sh):
#     KM_VAULT_PATH (env)  ->  positional argument  ->  current working directory
#
# Usage:
#   scripts/run-lint.sh                       # write report + print summary
#   scripts/run-lint.sh /path/to/vault        # explicit vault root
#   scripts/run-lint.sh --json                # JSON only, no report file, no stdout noise
#   scripts/run-lint.sh --quiet               # write report, no stdout
#   scripts/run-lint.sh --no-report           # JSON to stdout, no report file (alias for --json)
#
# Exit codes:
#   0  always (read-only — exit code does NOT reflect findings; downstream
#      tooling (CI, pre-commit) inspects the JSON severity totals instead).
#   2  on usage / resolver error.
#
# Severity defaults (hardcoded for PR1; PR1.5+ may make this configurable):
#   error  spaced_filenames, spaced_wikilinks_body, terminology(ERROR)
#   warn   orphans, dead_link_targets, frontmatter_gaps, terminology(WARN)
#   info   title_overlap

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=../lib/vault_root.sh
. "$REPO_ROOT/lib/vault_root.sh"

# --- arg parsing -----------------------------------------------------------

JSON_ONLY=0
QUIET=0
POSITIONAL=""
for arg in "$@"; do
  case "$arg" in
    --json|--no-report) JSON_ONLY=1 ;;
    --quiet)            QUIET=1 ;;
    --help|-h)
      sed -n '1,30p' "$0" | sed 's|^# \?||' >&2
      exit 0
      ;;
    -*)
      printf 'run-lint: unknown flag %s\n' "$arg" >&2
      exit 2
      ;;
    *)
      if [ -z "$POSITIONAL" ]; then
        POSITIONAL="$arg"
      else
        printf 'run-lint: extra positional argument %s\n' "$arg" >&2
        exit 2
      fi
      ;;
  esac
done

VAULT_ROOT="$(km_resolve_vault_root "$POSITIONAL")"
WIKI_ROOT="$VAULT_ROOT/wiki"

if [ ! -d "$WIKI_ROOT" ]; then
  printf 'run-lint: wiki root %s is not a directory\n' "$WIKI_ROOT" >&2
  exit 2
fi

DATE=$(date +%Y-%m-%d)
TMPROOT="${TMPDIR:-/tmp}"
TMP=$(mktemp -d "$TMPROOT/run-lint.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

# --- inventory -------------------------------------------------------------

find "$WIKI_ROOT" -type f -name '*.md' > "$TMP/all-paths.txt"
TOTAL_PAGES=$(wc -l < "$TMP/all-paths.txt" | tr -d ' ')

# --- check: spaced_filenames (error) --------------------------------------

find "$WIKI_ROOT" -type f -name '* *.md' ! -path "$WIKI_ROOT/_templates/*" > "$TMP/spaced-files.txt"
SPACED=$(wc -l < "$TMP/spaced-files.txt" | tr -d ' ')

# --- check: spaced_wikilinks_body (error) ----------------------------------

WIKI_ROOT="$WIKI_ROOT" python3 - > "$TMP/spaced-links.txt" << 'PY'
import os, re, sys
wiki = os.environ["WIKI_ROOT"]
LINK = re.compile(r'\[\[([^\]]+)\]\]')
for root, _, files in os.walk(wiki):
    parts = root.split(os.sep)
    if "_templates" in parts or "meta" in parts:
        continue
    for fn in sorted(files):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(root, fn)
        with open(p, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                for m in LINK.finditer(line):
                    target = re.split(r'[|#]', m.group(1), maxsplit=1)[0].strip()
                    if " " in target:
                        print(f"{p}:{i}: {m.group(0)}")
PY
SPACED_LINKS=$(wc -l < "$TMP/spaced-links.txt" | tr -d ' ')

# --- check: orphans (warn) ------------------------------------------------

# scripts/lint-orphans.py uses the resolver via env, so set KM_VAULT_PATH for it.
KM_VAULT_PATH="$VAULT_ROOT" python3 "$SCRIPT_DIR/lint-orphans.py" > "$TMP/orphans.txt" || true
ORPHANS=$(wc -l < "$TMP/orphans.txt" | tr -d ' ')

# --- check: dead_link_targets (warn) --------------------------------------

# Collect all wikilink targets (lowercased, alias/anchor stripped).
# grep exit 1 on "no matches" + pipefail would kill the run — wrap in || true.
{ grep -rEho '\[\[[^]]+\]\]' "$WIKI_ROOT" 2>/dev/null || true; } \
  | sed -E 's/\[\[([^|#]+)([|#][^]]*)?\]\]/\1/' \
  | sed -E 's/\.md$//' | tr 'A-Z' 'a-z' | sort -u > "$TMP/links.txt"
awk -F/ '{ f=$NF; sub(/\.md$/, "", f); print tolower(f) }' "$TMP/all-paths.txt" | sort -u > "$TMP/basenames.txt"
find "$WIKI_ROOT" -type f -name '*.md' | sed "s|^$WIKI_ROOT/||; s|\.md\$||" | tr 'A-Z' 'a-z' | sort -u > "$TMP/paths.txt"
# .raw/ is a vault convention (immutable source folder); harmless if missing.
if [ -d "$VAULT_ROOT/.raw" ]; then
  find "$VAULT_ROOT/.raw" -type f \( -name '*.md' -o -name '*.json' -o -name '*.txt' -o -name '*.pdf' \) 2>/dev/null \
    | sed 's|\.md$||' | tr 'A-Z' 'a-z' | sort -u > "$TMP/raw.txt"
else
  : > "$TMP/raw.txt"
fi
sort -u "$TMP/basenames.txt" "$TMP/paths.txt" "$TMP/raw.txt" > "$TMP/valid.txt"
comm -23 "$TMP/links.txt" "$TMP/valid.txt" > "$TMP/dead.txt"
DEAD=$(wc -l < "$TMP/dead.txt" | tr -d ' ')

# --- check: frontmatter_gaps (warn) ---------------------------------------

WIKI_ROOT="$WIKI_ROOT" python3 - > "$TMP/fm-gaps.txt" << 'PY'
import os
wiki = os.environ["WIKI_ROOT"]
required = ["type","title","created","updated","status"]
for root, _, files in os.walk(wiki):
    for fn in files:
        if not fn.endswith(".md"):
            continue
        p = os.path.join(root, fn)
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                head = "".join(f.readline() for _ in range(30))
        except OSError:
            continue
        if not head.startswith("---"):
            print(p)
            continue
        lines = head.splitlines()
        missing = [k for k in required if not any(L.startswith(k+":") for L in lines)]
        if missing:
            print(f"{p}\t{','.join(missing)}")
PY
GAPS=$(wc -l < "$TMP/fm-gaps.txt" | tr -d ' ')

# --- check: terminology (pass-through severities) -------------------------

TERM_ERR=0
TERM_WARN=0
if [ -x "$SCRIPT_DIR/lint-terminology.py" ]; then
  KM_VAULT_PATH="$VAULT_ROOT" python3 "$SCRIPT_DIR/lint-terminology.py" --json > "$TMP/term.json" 2>/dev/null || true
  if [ -s "$TMP/term.json" ]; then
    # Single python call -> emits "err warn" on one line. Robust against
    # subshell exit-code quirks that bit the earlier two-call form.
    read -r TERM_ERR TERM_WARN < <(python3 - <<PY
import json
try:
    d = json.load(open("$TMP/term.json"))
except Exception:
    print("0 0"); raise SystemExit(0)
e = sum(1 for f in d if isinstance(f, dict) and f.get("severity") == "ERROR")
w = sum(1 for f in d if isinstance(f, dict) and f.get("severity") == "WARN")
print(f"{e} {w}")
PY
) || { TERM_ERR=0; TERM_WARN=0; }
  fi
fi

# --- check: title_overlap (info) ------------------------------------------

TITLE_OVERLAP=0
if [ -x "$SCRIPT_DIR/lint-title-overlap.py" ]; then
  KM_VAULT_PATH="$VAULT_ROOT" python3 "$SCRIPT_DIR/lint-title-overlap.py" > "$TMP/title.txt" 2>/dev/null || true
  # Each finding line is "score\tpath-a\tpath-b". Header lines start with "#".
  # grep -c returns exit 1 when count is 0 -> use awk to avoid the || fallthrough
  # that produced "0\n0" when grep matched nothing.
  TITLE_OVERLAP=$(awk '/^[0-9]/{n++} END{print n+0}' "$TMP/title.txt")
fi

# --- aggregate JSON --------------------------------------------------------

# items previews capped to 30 entries per check to keep the JSON bounded.
WIKI_ROOT="$WIKI_ROOT" \
VAULT_ROOT="$VAULT_ROOT" \
DATE="$DATE" \
TOTAL_PAGES="$TOTAL_PAGES" \
SPACED="$SPACED" \
SPACED_LINKS="$SPACED_LINKS" \
ORPHANS="$ORPHANS" \
DEAD="$DEAD" \
GAPS="$GAPS" \
TERM_ERR="$TERM_ERR" \
TERM_WARN="$TERM_WARN" \
TITLE_OVERLAP="$TITLE_OVERLAP" \
TMP="$TMP" \
python3 - > "$TMP/summary.json" << 'PY'
import json, os
def head_lines(path, n=30):
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            out.append(line.rstrip("\n"))
    return out
checks = [
    {"name": "spaced_filenames", "severity": "error",
     "count": int(os.environ["SPACED"]),
     "items": head_lines(f"{os.environ['TMP']}/spaced-files.txt")},
    {"name": "spaced_wikilinks_body", "severity": "error",
     "count": int(os.environ["SPACED_LINKS"]),
     "items": head_lines(f"{os.environ['TMP']}/spaced-links.txt")},
    {"name": "orphans", "severity": "warn",
     "count": int(os.environ["ORPHANS"]),
     "items": head_lines(f"{os.environ['TMP']}/orphans.txt")},
    {"name": "dead_link_targets", "severity": "warn",
     "count": int(os.environ["DEAD"]),
     "items": head_lines(f"{os.environ['TMP']}/dead.txt")},
    {"name": "frontmatter_gaps", "severity": "warn",
     "count": int(os.environ["GAPS"]),
     "items": head_lines(f"{os.environ['TMP']}/fm-gaps.txt")},
    {"name": "terminology", "severity": "error" if int(os.environ["TERM_ERR"]) > 0 else "warn",
     "count": int(os.environ["TERM_ERR"]) + int(os.environ["TERM_WARN"]),
     "errors": int(os.environ["TERM_ERR"]),
     "warns": int(os.environ["TERM_WARN"]),
     "items": []},
    {"name": "title_overlap", "severity": "info",
     "count": int(os.environ["TITLE_OVERLAP"]),
     "items": head_lines(f"{os.environ['TMP']}/title.txt")},
]
totals = {"error": 0, "warn": 0, "info": 0}
for c in checks:
    if c.get("count", 0) <= 0:
        continue
    if c["name"] == "terminology":
        totals["error"] += c.get("errors", 0)
        totals["warn"]  += c.get("warns", 0)
    else:
        totals[c["severity"]] += c["count"]
summary = {
    "date": os.environ["DATE"],
    "vault_root": os.environ["VAULT_ROOT"],
    "wiki_root": os.environ["WIKI_ROOT"],
    "pages_scanned": int(os.environ["TOTAL_PAGES"]),
    "checks": checks,
    "totals": totals,
}
print(json.dumps(summary, indent=2, ensure_ascii=False))
PY

# --- output ---------------------------------------------------------------

if [ "$JSON_ONLY" -eq 1 ]; then
  cat "$TMP/summary.json"
  exit 0
fi

REPORT_DIR="$WIKI_ROOT/meta"
REPORT="$REPORT_DIR/lint-report-$DATE.md"
mkdir -p "$REPORT_DIR"

{
  printf -- '---\ntype: meta\ntitle: "Lint Report %s"\ncreated: %s\nupdated: %s\ntags:\n  - meta\n  - lint\nstatus: developing\n---\n\n' "$DATE" "$DATE" "$DATE"
  printf -- '# Lint Report: %s\n\n' "$DATE"
  printf -- '## Summary\n\n| Check | Severity | Count |\n|---|---|---|\n'
  python3 -c "
import json
d = json.load(open('$TMP/summary.json'))
for c in d['checks']:
    print(f\"| {c['name']} | {c['severity']} | {c['count']} |\")
print()
t = d['totals']
print(f\"**Totals:** error={t['error']}  warn={t['warn']}  info={t['info']}  (pages scanned: {d['pages_scanned']})\")
"
  printf '\n## Findings\n\n'
  python3 -c "
import json
d = json.load(open('$TMP/summary.json'))
for c in d['checks']:
    if c['count'] <= 0:
        continue
    print(f\"### {c['name']} (severity={c['severity']}, count={c['count']})\")
    print()
    for it in c.get('items', [])[:30]:
        print(f\"- {it}\")
    if c['count'] > len(c.get('items', [])):
        print(f\"- … {c['count'] - len(c.get('items', []))} more\")
    print()
"
  printf '## Machine-readable summary\n\n```json\n'
  cat "$TMP/summary.json"
  printf '\n```\n'
} > "$REPORT"

if [ "$QUIET" -eq 0 ]; then
  printf 'Lint report: %s\n' "$REPORT"
  python3 -c "
import json
d = json.load(open('$TMP/summary.json'))
t = d['totals']
print(f\"Totals: error={t['error']}  warn={t['warn']}  info={t['info']}  pages={d['pages_scanned']}\")
"
fi
