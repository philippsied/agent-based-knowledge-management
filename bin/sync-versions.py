#!/usr/bin/env python3
# bin/sync-versions.py — mirror plugin.json version into marketplace.json.
#
# Single source of truth: .claude-plugin/plugin.json.version
# Mirrors into:
#   - .claude-plugin/marketplace.json.metadata.version
#   - .claude-plugin/marketplace.json.plugins[0].version

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"


def main():
    with open(PLUGIN_JSON) as f:
        version = json.load(f).get("version")
    if not version or version == "null":
        print("Failed to read version from plugin.json")
        return 2

    with open(MARKETPLACE_JSON) as f:
        data = json.load(f)
    data["metadata"]["version"] = version
    data["plugins"][0]["version"] = version

    with open(MARKETPLACE_JSON, "w") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    print(f"Synced marketplace.json to version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
