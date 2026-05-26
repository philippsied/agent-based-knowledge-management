#!/usr/bin/env bash
# Tests for scripts/run-lint.sh.
#
# Builds a synthetic vault, runs the aggregator in --json mode, asserts that
# the expected metric keys are present and that seeded findings show up under
# the correct severity. Also verifies that --quiet writes the report file.
#
# Run: bash tests/test_run_lint.sh
set -u

REPO="$(cd "$(dirname "$0")/.." && pwd)"
RUN_LINT="$REPO/scripts/run-lint.sh"

PASS=0
FAIL=0
ok() { printf 'PASS %s\n' "$1"; PASS=$((PASS+1)); }
no() { printf 'FAIL %s: %s\n' "$1" "$2" >&2; FAIL=$((FAIL+1)); }

mk_vault() {
  local root="$1"
  mkdir -p "$root/wiki/concepts" "$root/wiki/entities" "$root/wiki/meta" "$root/wiki/_templates"
  # canonical roots — well-formed frontmatter, excluded from orphan detection
  cat > "$root/wiki/index.md" <<'EOF'
---
type: meta
title: "Index"
created: 2026-05-26
updated: 2026-05-26
status: developing
---
[[Linked-Concept]] [[Dead-Target]]
EOF
  cat > "$root/wiki/log.md" <<'EOF'
---
type: meta
title: "Log"
created: 2026-05-26
updated: 2026-05-26
status: developing
---
EOF
  cat > "$root/wiki/hot.md" <<'EOF'
---
type: meta
title: "Hot"
created: 2026-05-26
updated: 2026-05-26
status: developing
---
EOF
  cat > "$root/wiki/overview.md" <<'EOF'
---
type: meta
title: "Overview"
created: 2026-05-26
updated: 2026-05-26
status: developing
---
EOF
  # linked page (well-formed, NOT an orphan)
  cat > "$root/wiki/concepts/Linked-Concept.md" <<'EOF'
---
type: concept
title: "Linked Concept"
created: 2026-05-26
updated: 2026-05-26
status: developing
---
Body.
EOF
  # orphan page (well-formed, no inbound links)
  cat > "$root/wiki/concepts/Orphan-Page.md" <<'EOF'
---
type: concept
title: "Orphan"
created: 2026-05-26
updated: 2026-05-26
status: developing
---
[[Spaced Target]] — this should trip spaced_wikilinks_body
EOF
  # spaced filename — naming-convention violation
  touch "$root/wiki/concepts/Spaced Filename.md"
  cat > "$root/wiki/concepts/Spaced Filename.md" <<'EOF'
---
type: concept
title: "Spaced Filename"
created: 2026-05-26
updated: 2026-05-26
status: developing
---
Body.
EOF
  # page with missing frontmatter
  cat > "$root/wiki/entities/No-Frontmatter.md" <<'EOF'
Just a body, no YAML.
EOF
  # _templates excluded from spaced-filename check
  cat > "$root/wiki/_templates/has spaces.md" <<'EOF'
---
type: meta
title: "Template with spaces"
created: 2026-05-26
updated: 2026-05-26
status: developing
---
Templates may contain placeholder spaces.
EOF
}

# --- 1. JSON mode, seeded vault -------------------------------------------

VAULT="$(mktemp -d "${TMPDIR:-/tmp}/run-lint-test.XXXXXX")"
mk_vault "$VAULT"

JSON_OUT="$(KM_VAULT_PATH="$VAULT" bash "$RUN_LINT" --json 2>/dev/null)"

if [ -z "$JSON_OUT" ]; then
  no "JSON output not empty" "(no stdout)"
else
  ok "JSON output not empty"
fi

# Required top-level keys
for key in date vault_root wiki_root pages_scanned checks totals; do
  if printf '%s' "$JSON_OUT" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if '$key' in d else 1)"; then
    ok "JSON has key: $key"
  else
    no "JSON has key: $key" "(missing)"
  fi
done

# All expected check names present
expected_checks="spaced_filenames spaced_wikilinks_body orphans dead_link_targets frontmatter_gaps terminology title_overlap"
for chk in $expected_checks; do
  if printf '%s' "$JSON_OUT" \
      | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if any(c['name']=='$chk' for c in d['checks']) else 1)"; then
    ok "check present: $chk"
  else
    no "check present: $chk" "(missing)"
  fi
done

# Seeded findings: spaced filename count >= 1, spaced wikilink body count >= 1, orphan count >= 1
for chk in spaced_filenames spaced_wikilinks_body orphans; do
  COUNT=$(printf '%s' "$JSON_OUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d['checks']:
    if c['name'] == '$chk':
        print(c['count'])
        break
")
  if [ "${COUNT:-0}" -ge 1 ]; then
    ok "seeded finding present: $chk (count=$COUNT)"
  else
    no "seeded finding present: $chk" "count=$COUNT, expected ≥ 1"
  fi
done

# Severity totals: errors >= 2 (one spaced filename + one body link), warns >= 1 (orphan)
ERRORS=$(printf '%s' "$JSON_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['totals']['error'])")
WARNS=$(printf '%s'  "$JSON_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['totals']['warn'])")
[ "$ERRORS" -ge 2 ] && ok "totals.error >= 2 (got $ERRORS)" || no "totals.error >= 2" "got $ERRORS"
[ "$WARNS"  -ge 1 ] && ok "totals.warn >= 1 (got $WARNS)"   || no "totals.warn >= 1"  "got $WARNS"

# --- 2. Report-file mode --------------------------------------------------

KM_VAULT_PATH="$VAULT" bash "$RUN_LINT" --quiet 2>/dev/null
DATE=$(date +%Y-%m-%d)
REPORT="$VAULT/wiki/meta/lint-report-$DATE.md"
if [ -f "$REPORT" ]; then
  ok "report file written: $REPORT"
else
  no "report file written" "$REPORT missing"
fi
if grep -q "Lint Report: $DATE" "$REPORT" 2>/dev/null; then
  ok "report has title header"
else
  no "report has title header" "(no match)"
fi
if grep -q "spaced_filenames" "$REPORT" 2>/dev/null; then
  ok "report mentions spaced_filenames"
else
  no "report mentions spaced_filenames" "(no match)"
fi

# --- 3. KM_VAULT_PATH override behaviour ----------------------------------

# Without KM_VAULT_PATH the script should default to cwd. Run from a clean tmpdir
# with no wiki/ — expect exit 2 (resolver-error / wiki not found).
EMPTY="$(mktemp -d "${TMPDIR:-/tmp}/run-lint-empty.XXXXXX")"
set +e
( cd "$EMPTY" && bash "$RUN_LINT" --json >/dev/null 2>&1 )
RC=$?
set -e
if [ "$RC" -eq 2 ]; then
  ok "exit 2 when wiki/ missing"
else
  no "exit 2 when wiki/ missing" "got $RC"
fi

# Cleanup
trash "$VAULT" "$EMPTY" 2>/dev/null || rm -r "$VAULT" "$EMPTY"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
