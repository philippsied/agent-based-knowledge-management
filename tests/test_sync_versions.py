#!/usr/bin/env python3
"""Test: bin/sync-versions.py mirrors version correctly.

Self-contained: no pytest dependency. Builds a temp repo skeleton, bumps
plugin.json to a unique version, runs bin/sync-versions.py inside it, and
asserts both metadata.version and plugins[0].version got mirrored.

Run:
  python3 tests/test_sync_versions.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sync-vers-test.") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / ".claude-plugin").mkdir(parents=True)
        (tmp_path / "bin").mkdir(parents=True)
        shutil.copy(ROOT / ".claude-plugin" / "plugin.json", tmp_path / ".claude-plugin")
        shutil.copy(
            ROOT / ".claude-plugin" / "marketplace.json", tmp_path / ".claude-plugin"
        )
        shutil.copy(ROOT / "bin" / "sync-versions.py", tmp_path / "bin")

        # Bump plugin.json to a unique version
        plugin_path = tmp_path / ".claude-plugin" / "plugin.json"
        with open(plugin_path) as f:
            plugin = json.load(f)
        plugin["version"] = "99.99.99"
        with open(plugin_path, "w") as f:
            f.write(json.dumps(plugin, indent=2, ensure_ascii=False) + "\n")

        # Run sync (from inside the tmp repo)
        subprocess.run(
            [sys.executable, "bin/sync-versions.py"], cwd=tmp_path, check=True
        )

        # Assert
        with open(tmp_path / ".claude-plugin" / "marketplace.json") as f:
            market = json.load(f)
        meta = market["metadata"]["version"]
        plg = market["plugins"][0]["version"]
        if meta != "99.99.99":
            print(f"FAIL: metadata.version = {meta}")
            return 1
        if plg != "99.99.99":
            print(f"FAIL: plugins[0].version = {plg}")
            return 1

    print("test_sync_versions.py: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
