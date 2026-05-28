#!/usr/bin/env python3
"""Pre-ingest entity-registry pre-pass.

Reads each new source file under <vault>/.raw/, extracts capitalized
noun-phrase candidates (multi-word entities) from the first ~5KB, ranks
by frequency across the batch, and writes a stub for the top-N most-
mentioned candidates into <vault>/wiki/<folder>/<Hyphenated-Name>.md so
that parallel wiki-ingest agents will Edit existing pages instead of
racing to Write duplicates.

Heuristic — not perfect; intended to seed the registry, not be definitive.

Usage:
    scripts/wiki-prepass.py [file1.md file2.md ...]
        — scans the given files (paths are vault-relative or absolute)
    scripts/wiki-prepass.py --all
        — scans every .md file under <vault>/.raw/ (non-recursive top level)
    scripts/wiki-prepass.py --vault /path/to/vault --all
        — explicit vault root

Vault root resolution (matches lib/vault_root.sh):
    --vault flag  ->  KM_VAULT_PATH env  ->  current working directory

Stubs are written with status=seed and a TODO marker. Agents Read -> Edit
them during ingest, adding sources and context.

Exit codes:
    0  success
    1  no input files / vault not found
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

# Common proper-noun patterns: "Claude Code", "EU AI Act", "Lovable Labs"
ENTITY_RE = re.compile(r"\b([A-Z][A-Za-zÄÖÜäöüß0-9]+(?:[-/. ][A-Z][A-Za-zÄÖÜäöüß0-9]+){0,3})\b")

# Words to discard as standalone "entities"
STOPLIST = {
    "The", "This", "That", "These", "Those", "From", "When", "Where",
    "How", "Why", "What", "Who", "Use", "Used", "First", "Second",
    "Section", "Chapter", "Page", "Note", "See", "Source", "Sources",
    "Read", "Write", "Edit", "Make", "Get", "Set", "TL", "DR", "MVP",
    "OK", "API", "URL", "PR", "MR",
}


def resolve_vault(cli_arg: str | None) -> Path:
    """Mirror lib/vault_root.py order: --vault > KM_VAULT_PATH > CWD."""
    for candidate in (cli_arg, os.environ.get("KM_VAULT_PATH"), os.getcwd()):
        if not candidate:
            continue
        p = Path(candidate).expanduser().resolve()
        if p.exists():
            return p
    raise SystemExit("ERROR: vault root could not be resolved")


def slugify(name: str) -> str:
    """Convert 'EU AI Act' -> 'EU-AI-Act'; preserve case of original."""
    return re.sub(r"\s+", "-", name.strip())


def extract_candidates(text: str, top_n: int = 80) -> list[tuple[str, int]]:
    counts: collections.Counter[str] = collections.Counter()
    for m in ENTITY_RE.finditer(text[:20000]):
        cand = m.group(1).strip()
        if cand in STOPLIST:
            continue
        if len(cand) < 4:
            continue
        # Only multi-word OR known-acronym-style
        if " " not in cand and "-" not in cand and "." not in cand:
            if not (cand.isupper() and 2 <= len(cand) <= 6):
                continue
        counts[cand] += 1
    return counts.most_common(top_n)


def suggest_folder(name: str, body: str) -> str:
    n = name.lower()
    if any(t in n for t in ("gmbh", "ag", "inc", "ltd", "labs", "ai")):
        return "entities"
    if any(t in n for t in ("framework", "model", "method", "principle", "pattern", "law", "test")):
        return "concepts"
    return "entities"


def stub_body(name: str) -> str:
    today = _dt.date.today().isoformat()
    return f"""---
type: entity
title: "{name}"
created: {today}
updated: {today}
tags:
  - stub
  - prepass-seed
status: seed
aliases: []
related: []
sources: []
---

# {name}

<!-- prepass stub: wiki-ingest agents will fill this in. Delete this marker once content exists. -->

## Snapshot
- Why it matters for us: TODO.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*", help="Source files (vault-relative or absolute)")
    ap.add_argument("--all", action="store_true",
                    help="Scan every *.md in <vault>/.raw/ (non-recursive)")
    ap.add_argument("--vault", help="Vault root override (else KM_VAULT_PATH or CWD)")
    ap.add_argument("--threshold", type=int, default=3,
                    help="Minimum occurrences across batch to seed a stub")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would be seeded without writing files")
    args = ap.parse_args()

    vault = resolve_vault(args.vault)
    raw_dir = vault / ".raw"
    wiki_dir = vault / "wiki"

    if args.all:
        if not raw_dir.exists():
            print(f"ERROR: {raw_dir} does not exist", file=sys.stderr)
            return 1
        files = sorted(
            str(p) for p in raw_dir.iterdir()
            if p.suffix == ".md" and not p.name.startswith(".")
        )
    else:
        # Resolve each given path: absolute as-is, else vault-relative.
        files = []
        for f in args.files:
            p = Path(f)
            if not p.is_absolute():
                p = vault / f
            files.append(str(p))

    if not files:
        print("ERROR: no input files. Use --all or pass file paths.", file=sys.stderr)
        return 1

    aggregate: collections.Counter[str] = collections.Counter()
    text_by_file: dict[str, str] = {}
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                t = fh.read()
        except FileNotFoundError:
            print(f"WARN: missing input: {f}", file=sys.stderr)
            continue
        text_by_file[f] = t
        for name, count in extract_candidates(t):
            aggregate[name] += count

    seeded: list[tuple[str, str, int]] = []
    skipped: list[tuple[str, str, int]] = []
    for name, total in aggregate.most_common():
        if total < args.threshold:
            break
        slug = slugify(name)
        # Locate an existing wiki page (any folder) by basename match.
        existing: str | None = None
        for root, _, ws in os.walk(wiki_dir):
            for w in ws:
                if w.lower() == slug.lower() + ".md":
                    existing = os.path.join(root, w)
                    break
            if existing:
                break
        if existing:
            skipped.append((name, existing, total))
            continue
        folder = suggest_folder(name, "\n".join(text_by_file.values()))
        target = wiki_dir / folder / (slug + ".md")
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(stub_body(name), encoding="utf-8")
        seeded.append((name, str(target), total))

    print(json.dumps({
        "vault": str(vault),
        "files_scanned": len(text_by_file),
        "stubs_seeded": len(seeded),
        "already_existed": len(skipped),
        "threshold": args.threshold,
        "dry_run": args.dry_run,
        "top_seeded": [{"name": n, "path": p, "count": c} for n, p, c in seeded[:30]],
        "top_skipped": [{"name": n, "path": p, "count": c} for n, p, c in skipped[:10]],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
