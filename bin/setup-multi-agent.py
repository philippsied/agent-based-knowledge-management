#!/usr/bin/env python3
"""setup-multi-agent.py — multi-agent skill installer.

Symlinks the skills/ directory into each AI agent's expected location.
Idempotent: safe to run multiple times.

Supported agents:
  - Claude Code    : auto-discovered via .claude-plugin/ (no symlink needed)
  - Codex CLI      : symlink to ~/.codex/skills/agentic-knowledge-management
  - OpenCode       : symlink to ~/.opencode/skills/agentic-knowledge-management
  - Gemini CLI     : symlink to ~/.gemini/skills/agentic-knowledge-management
  - Cursor         : symlink to .cursor/skills (in repo)
  - Windsurf       : symlink to .windsurf/skills (in repo)

Bootstrap files (AGENTS.md, GEMINI.md, .cursor/rules/, .windsurf/rules/,
.github/copilot-instructions.md) are already committed in the repo.
This script just wires up the skills directory.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
GRAY = "\033[0;37m"
NC = "\033[0m"


def link_if_missing(target: Path, dest: Path, agent_name: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.is_symlink():
        existing = os.readlink(dest)
        if existing == str(target):
            print(f"{GRAY}[{agent_name}] already linked: {dest}{NC}")
            return
        else:
            print(
                f"{YELLOW}[{agent_name}] symlink exists but points elsewhere: "
                f"{dest} -> {existing} (skipping, remove manually if you want to relink){NC}"
            )
            return

    if dest.exists():
        print(f"{YELLOW}[{agent_name}] path exists and is not a symlink: {dest} (skipping){NC}")
        return

    os.symlink(target, dest)
    print(f"{GREEN}[{agent_name}] linked: {dest} -> {target}{NC}")


def main() -> None:
    if not SKILLS_DIR.is_dir():
        print(
            f"ERROR: {SKILLS_DIR} does not exist. "
            "Are you running this from the agentic-knowledge-management repo?"
        )
        sys.exit(1)

    print("agentic-knowledge-management: multi-agent skill installer")
    print(f"Repo: {REPO_ROOT}")
    print()

    home = Path.home()

    # Codex CLI
    link_if_missing(SKILLS_DIR, home / ".codex/skills/agentic-knowledge-management", "Codex CLI")

    # OpenCode
    link_if_missing(SKILLS_DIR, home / ".opencode/skills/agentic-knowledge-management", "OpenCode")

    # Gemini CLI
    link_if_missing(SKILLS_DIR, home / ".gemini/skills/agentic-knowledge-management", "Gemini CLI")

    # Cursor (workspace-local)
    link_if_missing(SKILLS_DIR, REPO_ROOT / ".cursor/skills", "Cursor")

    # Windsurf (workspace-local)
    link_if_missing(SKILLS_DIR, REPO_ROOT / ".windsurf/skills", "Windsurf")

    print()
    print(
        f"{GREEN}Done.{NC} Bootstrap files (AGENTS.md, GEMINI.md, .cursor/rules/, "
        ".windsurf/rules/, .github/copilot-instructions.md) are already in this repo."
    )
    print()
    print("To verify each agent picks up the skills:")
    print("  - Claude Code: open the project, type /wiki")
    print("  - Codex CLI:   codex --list-skills | grep agentic-knowledge-management")
    print("  - Cursor:      open the project, ask 'what skills do you have?'")
    print("  - Windsurf:    open in Cascade, ask the same")
    print("  - Gemini CLI:  gemini --list-skills (if supported)")


if __name__ == "__main__":
    main()
