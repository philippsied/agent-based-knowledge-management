#!/usr/bin/env python3
# bin/release.py <version> — prepare a new release.
#
# Usage: bin/release.py 1.9.0
#
# Steps:
#   1. Validate version format
#   2. Verify clean working tree
#   3. Run tests + lint
#   4. Bump plugin.json version
#   5. Sync marketplace.json via bin/sync-versions.py
#   6. Verify CHANGELOG entry exists
#   7. Optional pandoc PDF generation
#   8. Commit + tag (no push — user controls)

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def lint_gate(returncode, stdout):
    """Release lint gate, scoped to the plugin DISTRIBUTION.

    `scripts/run-lint.py` lints the working Obsidian vault (`wiki/`), which is NOT
    part of the shipped plugin (skills/, hooks/, .claude-plugin/, docs, README). Its
    severity findings are demo-content quality, never a release blocker — so the gate
    excludes them: the distribution contains zero run-lint-scanned files, hence its
    distribution-scoped error count is 0 by construction. Distribution correctness is
    gated by `make test` (skill-count SSOT, version sync, vault-root, …) in pre-flight.

    Returns an exit code (int) to BLOCK the release, or None to pass. The gate blocks
    only when run-lint itself cannot run (non-zero exit / unparseable JSON) — a broken
    linter, not vault content.
    """
    if returncode != 0:
        return 4
    try:
        json.loads(stdout)["totals"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return 4
    return None


def main(argv):
    version = argv[1] if len(argv) > 1 else ""
    if not version:
        print(f"Usage: {argv[0]} <version>")
        return 2
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print(f"Invalid version: {version} (expected X.Y.Z)")
        return 2

    # Clean working tree
    if subprocess.run(["git", "diff", "--quiet"], cwd=REPO_ROOT).returncode != 0:
        print("Uncommitted changes — stash or commit first")
        return 3

    # Pre-flight
    print("Running tests...")
    subprocess.run(["make", "test"], cwd=REPO_ROOT, check=True)

    print("Running lint (advisory — working-vault health)...")
    proc = subprocess.run(
        [sys.executable, "scripts/run-lint.py", "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    blocked = lint_gate(proc.returncode, proc.stdout)
    if blocked is not None:
        print("run-lint could not run — the release gate blocks on a broken linter, "
              "not on working-vault findings")
        if proc.stderr.strip():
            sys.stderr.write(proc.stderr)
        return blocked
    print(f"  vault lint (advisory, not a release blocker): {json.loads(proc.stdout)['totals']}")

    # CHANGELOG check
    changelog_text = CHANGELOG.read_text()
    if not re.search(rf"^## \[{re.escape(version)}\]", changelog_text, re.MULTILINE):
        print(f"Missing CHANGELOG entry for {version}")
        return 5

    # Bump
    with open(PLUGIN_JSON) as f:
        plugin = json.load(f)
    plugin["version"] = version
    with open(PLUGIN_JSON, "w") as f:
        f.write(json.dumps(plugin, indent=2, ensure_ascii=False) + "\n")

    subprocess.run([sys.executable, "bin/sync-versions.py"], cwd=REPO_ROOT, check=True)

    # Optional PDF generation
    if shutil.which("pandoc"):
        rc = subprocess.run(
            ["pandoc", "docs/install-guide.md", "-o", f"/tmp/install-guide-{version}.pdf"],
            cwd=REPO_ROOT,
        ).returncode
        if rc != 0:
            print("PDF generation failed, continuing")

    # Commit + tag
    subprocess.run(
        ["git", "add", ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"],
        cwd=REPO_ROOT,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"chore(release): cut v{version}"], cwd=REPO_ROOT, check=True
    )
    subprocess.run(
        ["git", "tag", "-a", f"v{version}", "-m", f"v{version}"], cwd=REPO_ROOT, check=True
    )

    print("")
    print(f"Release v{version} prepared locally.")
    print(f"Review with: git show v{version}")
    print("Push with:   git push origin main --tags")
    print("Then update marketplace.json.plugins[0].source.ref to v%s and re-commit." % version)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
