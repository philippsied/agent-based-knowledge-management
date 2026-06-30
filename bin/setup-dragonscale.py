#!/usr/bin/env python3
"""setup-dragonscale.py — opt-in installer for DragonScale Memory.

Provisions the runtime files that the wiki-ingest and wiki-lint skills
feature-detect. Safe to re-run (idempotent).

Does NOT install ollama or pull any embedding model. Those are
prerequisites for Mechanism 3 (semantic tiling) and are the user's
responsibility. Mechanism 1 (fold) and Mechanism 2 (addresses) have no
external prerequisites.

Usage:
  python3 bin/setup-dragonscale.py [optional: /path/to/vault]
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def main() -> None:
    vault = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR.parent

    print(f"Setting up DragonScale Memory at: {vault}")
    os.chdir(vault)

    # ── 1. Verify required artifacts that ship with the plugin ───────────────
    for required in (
        "scripts/allocate-address.py",
        "scripts/tiling-check.py",
        "skills/wiki-fold/SKILL.md",
    ):
        if not Path(required).exists():
            sys.stderr.write(
                f"ERR: missing {required}. Reinstall the agentic-knowledge-management plugin.\n"
            )
            sys.exit(1)
    os.chmod("scripts/allocate-address.py", 0o755)
    os.chmod("scripts/tiling-check.py", 0o755)

    # ── 2. Provision .vault-meta/ ────────────────────────────────────────────
    Path(".vault-meta").mkdir(parents=True, exist_ok=True)
    counter = Path(".vault-meta/address-counter.txt")
    if not counter.is_file():
        counter.write_text("1\n")
        print("OK  .vault-meta/address-counter.txt initialized at 1")
    else:
        print("--  .vault-meta/address-counter.txt already present (not overwritten)")

    thresholds = Path(".vault-meta/tiling-thresholds.json")
    if not thresholds.is_file():
        thresholds.write_text(
            """{
  "version": 1,
  "model": "nomic-embed-text",
  "bands": {
    "error": 0.90,
    "review": 0.80
  },
  "calibrated": false,
  "calibration_pairs_labeled": 0,
  "notes": "Conservative seed thresholds, NOT calibrated against this vault. See skills/wiki-lint/SKILL.md Semantic Tiling section for the calibration procedure."
}
"""
        )
        print("OK  .vault-meta/tiling-thresholds.json initialized with conservative seed bands")
    else:
        print("--  .vault-meta/tiling-thresholds.json already present (not overwritten)")

    # ── 3. Provision .raw/.manifest.json (if absent) ─────────────────────────
    Path(".raw").mkdir(parents=True, exist_ok=True)
    manifest = Path(".raw/.manifest.json")
    if not manifest.is_file():
        today = date.today().strftime("%Y-%m-%d")
        manifest.write_text(
            "{\n"
            '  "version": 1,\n'
            f'  "created": "{today}",\n'
            '  "description": "Ingest delta tracker and address map for the agentic-knowledge-management vault. Do not hand-edit; wiki-ingest maintains this.",\n'
            '  "sources": {},\n'
            '  "address_map": {}\n'
            "}\n"
        )
        print("OK  .raw/.manifest.json initialized (empty sources + address_map)")
    else:
        print("--  .raw/.manifest.json already present (not overwritten)")

    # ── 4. Rollout-baseline marker in legacy-pages.txt ───────────────────────
    legacy = Path(".vault-meta/legacy-pages.txt")
    if not legacy.is_file():
        today = date.today().strftime("%Y-%m-%d")
        legacy.write_text(
            "# DragonScale legacy-pages manifest\n"
            f"# rollout: {today}\n"
            "#\n"
            "# List, one path per line, any pages whose frontmatter `created:` date is\n"
            "# post-rollout but which should still be treated as legacy (i.e. not required\n"
            "# to have an address). Also lines beginning with \"# rollout:\" set the\n"
            "# per-vault rollout baseline used by wiki-lint for severity classification.\n"
            "# Example:\n"
            "# wiki/sources/old-page-with-wrong-metadata.md\n"
        )
        print("OK  .vault-meta/legacy-pages.txt initialized (rollout baseline set to today)")
    else:
        print("--  .vault-meta/legacy-pages.txt already present (not overwritten)")

    # ── 5. Sanity checks ─────────────────────────────────────────────────────
    print("")
    print("Sanity checks:")
    proc = subprocess.run(
        ["python3", "scripts/allocate-address.py", "--peek"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    last_line = proc.stdout.splitlines()[-1] if proc.stdout.splitlines() else ""
    if proc.returncode != 0 or not last_line.isdigit():
        sys.stderr.write(f"ERR: address counter sanity check failed: {last_line}\n")
        sys.exit(3)
    print(f"  next address: c-{int(last_line):06d}")

    python = shutil.which("python3") or "not installed"
    print(f"  python3:      {python}")

    if shutil.which("curl"):
        version = subprocess.run(
            ["curl", "-sS", "--max-time", "2", "http://localhost:11434/api/version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if version.returncode == 0:
            print("  ollama:       reachable at http://localhost:11434")
            tags = subprocess.run(
                ["curl", "-sS", "--max-time", "2", "http://localhost:11434/api/tags"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if "nomic-embed-text" in tags.stdout:
                print("  nomic-embed:  installed")
            else:
                print("  nomic-embed:  NOT installed (run 'ollama pull nomic-embed-text' to enable Mechanism 3)")
        else:
            print("  ollama:       not reachable (Mechanism 3 will no-op; install from https://ollama.com)")
    else:
        print("  curl:         not installed (cannot check ollama)")

    print("")
    print("DragonScale setup complete.")
    print("See wiki/concepts/DragonScale Memory.md for the full spec.")
    print("See skills/wiki-fold/ for Mechanism 1 (log folds).")
    print("wiki-ingest and wiki-lint will now feature-detect DragonScale automatically.")


if __name__ == "__main__":
    main()
