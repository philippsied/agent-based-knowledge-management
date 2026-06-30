#!/usr/bin/env python3
"""setup-vault.py — agentic-knowledge-management vault setup script.

Run this ONCE before opening Obsidian for the first time.
Usage: python3 bin/setup-vault.py [optional: /path/to/vault]
Default: uses the parent of the directory where this script lives (the vault root).

Faithful port of bin/setup-vault.sh: creates the vault directory skeleton,
scaffolds idempotent DragonScale state + path-safety config (TTY-gated prompt),
writes the Obsidian config files, downloads the two plugin binaries that are too
large to track in git, and prints the post-setup guidance block.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def download(url: str, dest: Path) -> None:
    """Mirror `curl -sS -L <url> -o <dest>`. curl is assumed present (the bash
    original used it directly); keep it to avoid redirect-handling drift."""
    subprocess.run(["curl", "-sS", "-L", url, "-o", str(dest)], check=True)


def main() -> None:
    vault = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR.parent
    obsidian = vault / ".obsidian"

    print(f"Setting up agentic-knowledge-management vault at: {vault}")

    # ── 1. Create directories ────────────────────────────────────────────────
    (obsidian / "snippets").mkdir(parents=True, exist_ok=True)
    (vault / ".raw").mkdir(parents=True, exist_ok=True)
    for sub in ("concepts", "entities", "sources", "meta"):
        (vault / "wiki" / sub).mkdir(parents=True, exist_ok=True)
    (vault / "_templates").mkdir(parents=True, exist_ok=True)
    (vault / ".vault-meta").mkdir(parents=True, exist_ok=True)

    # ── 1a. Scaffold DragonScale state files (idempotent) ────────────────────
    # These are per-vault state. The plugin distribution does NOT ship them; each
    # vault initializes its own counter and legacy-pages manifest on first run.
    counter = vault / ".vault-meta" / "address-counter.txt"
    if not counter.is_file():
        counter.write_text("0\n")

    legacy = vault / ".vault-meta" / "legacy-pages.txt"
    if not legacy.is_file():
        legacy.write_text(
            "# DragonScale legacy-pages manifest\n"
            "# rollout: vault-local\n"
            "#\n"
            "# List, one path per line, any pages whose frontmatter `created:` date is\n"
            "# post-rollout but which should still be treated as legacy (i.e. not required\n"
            "# to carry a deterministic c-NNNNNN address). One path per line, relative to\n"
            "# the vault root. Lines starting with '#' are comments.\n"
        )

    # ── 1b. Scaffold path-safety config (idempotent, TTY-gated prompt) ───────
    # Asks whether this repo also holds non-wiki work next to the wiki. Default is
    # strict, which keeps the hook's exit-2 block. Mixed converts the block into a
    # model-visible reminder. See docs/specs/SPEC_v1.10.0-soft-path-safety-hook.md.
    config = vault / ".vault-meta" / "config.json"
    if not config.is_file():
        path_safety_mode = "strict"
        if sys.stdin.isatty():
            answer = input(
                "Does this repo also hold non-wiki work (code, docs) next to the wiki? [y/N] "
            )
            if answer in ("y", "Y", "yes", "YES"):
                path_safety_mode = "mixed"
        config.write_text(
            "{\n"
            '  "version": 1,\n'
            f'  "path_safety_mode": "{path_safety_mode}"\n'
            "}\n"
        )
        print(f"✓ Wrote .vault-meta/config.json (path_safety_mode: {path_safety_mode})")

    # ── 2. Write graph.json ──────────────────────────────────────────────────
    (obsidian / "graph.json").write_text(
        """{
  "collapse-filter": false,
  "search": "path:wiki",
  "showTags": false,
  "showAttachments": false,
  "hideUnresolved": true,
  "showOrphans": false,
  "collapse-color-groups": false,
  "colorGroups": [
    { "query": "path:wiki/entities",    "color": { "a": 1, "rgb": 12945088 } },
    { "query": "path:wiki/concepts",    "color": { "a": 1, "rgb": 5227007  } },
    { "query": "path:wiki/sources",     "color": { "a": 1, "rgb": 6986069  } },
    { "query": "path:wiki/meta",        "color": { "a": 1, "rgb": 5676246  } },
    { "query": "path:wiki",             "color": { "a": 1, "rgb": 5676246  } }
  ],
  "showArrow": true,
  "textFadeMultiplier": -1,
  "nodeSizeMultiplier": 1.8,
  "lineSizeMultiplier": 1.2,
  "centerStrength": 0.5,
  "repelStrength": 30,
  "linkStrength": 1.5,
  "linkDistance": 120,
  "scale": 1.0
}
"""
    )

    # ── 3. Write app.json (excluded files) ───────────────────────────────────
    (obsidian / "app.json").write_text(
        """{
  "userIgnoreFilters": [
    "agents/",
    "commands/",
    "hooks/",
    "skills/",
    "_templates/",
    "README.md",
    "CLAUDE.md",
    "WIKI.md",
    "Welcome.md"
  ]
}
"""
    )

    # ── 4. Write appearance.json (enable CSS snippets) ───────────────────────
    (obsidian / "appearance.json").write_text(
        """{
  "enabledCssSnippets": [
    "vault-colors",
    "ITS-Dataview-Cards",
    "ITS-Image-Adjustments"
  ]
}
"""
    )

    # ── 5. Download Excalidraw main.js (8MB, not in git) ─────────────────────
    excalidraw = obsidian / "plugins" / "obsidian-excalidraw-plugin"
    if (excalidraw / "manifest.json").is_file() and not (excalidraw / "main.js").is_file():
        print("Downloading Excalidraw main.js (~8MB)...")
        download(
            "https://github.com/zsviczian/obsidian-excalidraw-plugin/releases/latest/download/main.js",
            excalidraw / "main.js",
        )
        print("✓ Excalidraw main.js downloaded")
    elif (excalidraw / "main.js").is_file():
        print("✓ Excalidraw main.js already present")

    # ── 6. Download Obsidian Memos / Thino v1.9.7 (MIT, ~1MB combined) ───────
    # We ship Thino v1 (MIT licensed). Thino v3 is closed-source via Pkmer Insider.
    # Plugin id is `obsidian-memos` on both versions; user can upgrade in-place later.
    thino = obsidian / "plugins" / "thino"
    thino_release_url = "https://github.com/Quorafind/Obsidian-Thino/releases/download/1.9.7"
    if (thino / "manifest.json").is_file() and not (thino / "main.js").is_file():
        print("Downloading Obsidian Memos (Thino v1.9.7) main.js + styles.css (~1MB)...")
        download(f"{thino_release_url}/main.js", thino / "main.js")
        download(f"{thino_release_url}/styles.css", thino / "styles.css")
        print("✓ Obsidian Memos v1.9.7 downloaded (MIT licensed)")
        print("  Upgrade to Thino v3 (closed source, more features) available via Pkmer Insider:")
        print("    https://github.com/Quorafind/Obsidian-Thino")
    elif (thino / "main.js").is_file():
        print("✓ Obsidian Memos / Thino plugin files already present")

    print("")
    print("✓ Setup complete.")
    print("")
    print("Next steps:")
    print("  1. Open Obsidian")
    print(f"  2. Manage Vaults → Open folder as vault → select: {vault}")
    print("  3. Enable community plugins when prompted (Calendar, Obsidian Memos (Thino v1), Excalidraw, Banners are pre-installed)")
    print("  4. Install: Dataview, Templater, Obsidian Git  (Settings → Community Plugins)")
    print("  5. Type /wiki in Claude Code to scaffold your knowledge base")
    print("")
    print("Optional opt-in packs:")
    print("  - Operational rules (atomic commits, sandbox awareness, verification-before-change):")
    print(f'      mkdir -p "{vault}/.claude/rules"')
    print(f'      cp -i "${{CLAUDE_PLUGIN_ROOT}}/references/operational-rules/"*.md "{vault}/.claude/rules/"')
    print("    See references/operational-rules/README.md for the per-rule rationale.")
    print("  - Issue-stack workflow templates (research-queue, briefs, OPEN-ISSUES, pending-commits):")
    print(f'      cp -i "${{CLAUDE_PLUGIN_ROOT}}/_templates/"{{research-queue,research-brief,open-issues,pending-commits}}.md "{vault}/wiki/meta/"')
    print("")
    print("Pre-installed plugins:")
    print("  - Calendar (sidebar calendar with word count + task dots)")
    print("  - Obsidian Memos / Thino v1 (quick memo capture; MIT. v3 available via Pkmer Insider)")
    print("  - Excalidraw (freehand drawing + image annotation)")
    print("  - Banners (add banner: to any note frontmatter for header images)")
    print("")
    print("CSS snippets enabled:")
    print("  - vault-colors: color-codes wiki/ folders in file explorer")
    print("  - ITS-Dataview-Cards: use ```dataviewjs with .cards for card grids")
    print("  - ITS-Image-Adjustments: append |100 to image embeds for sizing")
    print("")
    print("Views available:")
    print("  - Wiki Map canvas (wiki/Wiki Map.canvas) — knowledge graph")
    print("  - Design Ideas canvas (projects/visual-vault/design-ideas.canvas) — visual reference board")
    print("  - Graph view filtered to wiki/ only, color-coded by type")
    print("")
    print("To switch to the visual layout (Canvas + Calendar + Thino sidebar):")
    print("  Quit Obsidian, then run:")
    print(f"    cp {obsidian}/workspace-visual.json {obsidian}/workspace.json")
    print("  Then reopen Obsidian.")
    print("")
    print("Graph colors: if they reset after closing Obsidian, open Graph settings")
    print("→ Color groups and re-add them once. They persist permanently after that.")


if __name__ == "__main__":
    main()
