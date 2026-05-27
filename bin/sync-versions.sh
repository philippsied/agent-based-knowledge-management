#!/usr/bin/env bash
# bin/sync-versions.sh — mirror plugin.json version into marketplace.json.
#
# Single source of truth: .claude-plugin/plugin.json.version
# Mirrors into:
#   - .claude-plugin/marketplace.json.metadata.version
#   - .claude-plugin/marketplace.json.plugins[0].version

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_JSON="$REPO_ROOT/.claude-plugin/plugin.json"
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"

VERSION=$(jq -r '.version' "$PLUGIN_JSON")
[ -n "$VERSION" ] && [ "$VERSION" != "null" ] || { echo "Failed to read version from plugin.json"; exit 2; }

jq --arg v "$VERSION" \
   '.metadata.version=$v | .plugins[0].version=$v' \
   "$MARKETPLACE_JSON" > "$MARKETPLACE_JSON.tmp"
mv "$MARKETPLACE_JSON.tmp" "$MARKETPLACE_JSON"
echo "Synced marketplace.json to version $VERSION"
