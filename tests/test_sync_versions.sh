#!/usr/bin/env bash
set -euo pipefail
# Test: bin/sync-versions.sh mirrors version correctly

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/sync-vers-test.XXXXXX")"
trap "rm -rf $TMP" EXIT

# Copy minimal repo skeleton
mkdir -p "$TMP/.claude-plugin" "$TMP/bin"
cp "$REPO_ROOT/.claude-plugin/plugin.json" "$TMP/.claude-plugin/"
cp "$REPO_ROOT/.claude-plugin/marketplace.json" "$TMP/.claude-plugin/"
cp "$REPO_ROOT/bin/sync-versions.sh" "$TMP/bin/"
chmod +x "$TMP/bin/sync-versions.sh"

# Bump plugin.json to a unique version
jq '.version="99.99.99"' "$TMP/.claude-plugin/plugin.json" > "$TMP/.claude-plugin/plugin.json.tmp"
mv "$TMP/.claude-plugin/plugin.json.tmp" "$TMP/.claude-plugin/plugin.json"

# Run sync (from inside the tmp repo)
(cd "$TMP" && bash bin/sync-versions.sh)

# Assert
META=$(jq -r '.metadata.version' "$TMP/.claude-plugin/marketplace.json")
PLG=$(jq -r '.plugins[0].version' "$TMP/.claude-plugin/marketplace.json")
[ "$META" = "99.99.99" ] || { echo "FAIL: metadata.version = $META"; exit 1; }
[ "$PLG"  = "99.99.99" ] || { echo "FAIL: plugins[0].version = $PLG"; exit 1; }

echo "test_sync_versions.sh: PASS"
