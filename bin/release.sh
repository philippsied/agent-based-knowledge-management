#!/usr/bin/env bash
# bin/release.sh <version> — prepare a new release.
#
# Usage: bin/release.sh 1.9.0
#
# Steps:
#   1. Validate version format
#   2. Verify clean working tree
#   3. Run tests + lint
#   4. Bump plugin.json version
#   5. Sync marketplace.json via bin/sync-versions.sh
#   6. Verify CHANGELOG entry exists
#   7. Optional pandoc PDF generation
#   8. Commit + tag (no push — user controls)

set -euo pipefail

VERSION="${1:-}"
[ -n "$VERSION" ] || { echo "Usage: $0 <version>"; exit 2; }
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Invalid version: $VERSION (expected X.Y.Z)"; exit 2; }

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Clean working tree
git diff --quiet || { echo "Uncommitted changes — stash or commit first"; exit 3; }

# Pre-flight
echo "Running tests..."
make test
echo "Running lint..."
python3 scripts/run-lint.py --json | jq -e '.error_count == 0' >/dev/null || { echo "Lint errors present"; exit 4; }

# CHANGELOG check
grep -q "^## \[$VERSION\]" CHANGELOG.md || { echo "Missing CHANGELOG entry for $VERSION"; exit 5; }

# Bump
jq --arg v "$VERSION" '.version=$v' .claude-plugin/plugin.json > .claude-plugin/plugin.json.tmp
mv .claude-plugin/plugin.json.tmp .claude-plugin/plugin.json
bash bin/sync-versions.sh

# Optional PDF generation
if command -v pandoc >/dev/null 2>&1; then
  pandoc docs/install-guide.md -o /tmp/install-guide-$VERSION.pdf || echo "PDF generation failed, continuing"
fi

# Commit + tag
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(release): cut v$VERSION"
git tag -a "v$VERSION" -m "v$VERSION"

echo ""
echo "Release v$VERSION prepared locally."
echo "Review with: git show v$VERSION"
echo "Push with:   git push origin main --tags"
echo "Then update marketplace.json.plugins[0].source.ref to v$VERSION and re-commit."
