#!/usr/bin/env python3
"""lint-orphans.py — list wiki pages with no inbound wikilinks.

Read-only. Walks the resolved wiki root, builds an inbound-link counter, and
prints every page whose count is zero. Excludes the canonical entry points
(`index`, `log`, `hot`, `overview` — these are roots, not orphans).

Usage:
  scripts/lint-orphans.py                    # default: $KM_VAULT_PATH/wiki, or ./wiki
  scripts/lint-orphans.py /path/to/wiki      # explicit wiki root
  scripts/lint-orphans.py --json             # JSON array instead of plain list

Output (plain): one path per line, sorted.
Output (JSON):  {"wiki_root": "...", "count": N, "items": ["wiki/...", ...]}.

Backed by the resolver in lib/vault_root.py — env > argv > cwd.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path

# Resolver: KM_VAULT_PATH env -> argv -> cwd. See lib/vault_root.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from vault_root import resolve_wiki_root  # noqa: E402

LINK_RE = re.compile(r"\[\[([^|\]#]+)")

EXCLUDE_BASENAMES = {"index", "log", "hot", "overview"}


def find_orphans(wiki_root: Path) -> list[str]:
    """Return sorted list of orphan paths (relative to the parent of wiki_root)."""
    if not wiki_root.is_dir():
        return []

    pages: dict[str, list[str]] = {}
    # Map lowercased wiki-relative path (without .md) -> actual path, so the
    # slash-form `[[concepts/Nested]]` resolves case-insensitively regardless
    # of the underlying filesystem.
    path_index: dict[str, str] = {}
    for root, _, files in os.walk(wiki_root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(root, fn)
            base = fn[:-3]
            pages.setdefault(base.lower(), []).append(p)
            rel = os.path.relpath(p, wiki_root)[:-3]
            path_index[rel.lower().replace(os.sep, "/")] = p

    inbound: collections.Counter = collections.Counter()
    for root, _, files in os.walk(wiki_root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(root, fn)
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            for m in LINK_RE.finditer(text):
                tgt = m.group(1).strip()
                tlow = tgt.lower()
                if tlow in pages:
                    for px in pages[tlow]:
                        if px != p:
                            inbound[px] += 1
                if "/" in tlow and tlow in path_index:
                    cand = path_index[tlow]
                    if cand != p:
                        inbound[cand] += 1

    # Build vault-relative exclude set for the canonical roots.
    exclude_paths = {
        str(wiki_root / f"{name}.md") for name in EXCLUDE_BASENAMES
    }

    orphans: list[str] = []
    for base_low, paths in pages.items():
        if base_low in EXCLUDE_BASENAMES:
            continue
        for px in paths:
            if px in exclude_paths:
                continue
            if inbound[px] == 0:
                orphans.append(px)
    orphans.sort()
    return orphans


def collect(wiki_root: Path) -> list[str]:
    """Importable entrypoint for run-lint.py. Returns the same orphan list the
    plain CLI prints (one path per line), without going through print()."""
    return find_orphans(wiki_root)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=None,
                        help="Wiki root directory (default: $KM_VAULT_PATH/wiki, or ./wiki)")
    parser.add_argument("--json", action="store_true",
                        help="Emit a JSON object instead of plain lines")
    args = parser.parse_args(argv)

    wiki_root = resolve_wiki_root(args.root)
    orphans = find_orphans(wiki_root)

    if args.json:
        payload = {
            "wiki_root": str(wiki_root),
            "count": len(orphans),
            "items": orphans,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for o in orphans:
            print(o)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
