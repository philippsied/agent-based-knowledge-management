#!/usr/bin/env python3
"""Rewrite [[link]] occurrences across <vault>/wiki/*.md using a TSV mapping.

Mapping format (tab-separated, one rule per line; lines starting with # are
comments):

    old-link-text    NewBasenameWithoutMd

Matching is case-insensitive on the link text. Section anchors (#foo) and
display aliases (|alias) are preserved. By default, wiki/_templates/ and
files named lint-report-*.md are skipped.

Vault root resolution (matches lib/vault_root.sh):
    --vault flag  ->  KM_VAULT_PATH env  ->  current working directory

Usage:
    scripts/rewrite-wikilinks.py <mapping.tsv> [--vault PATH] [--dry-run] [--include-templates]

Exit codes:
    0  success
    1  mapping file missing or empty
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


def resolve_vault(cli_arg: str | None) -> Path:
    for candidate in (cli_arg, os.environ.get("KM_VAULT_PATH"), os.getcwd()):
        if not candidate:
            continue
        p = Path(candidate).expanduser().resolve()
        if p.exists():
            return p
    raise SystemExit("ERROR: vault root could not be resolved")


def load_mapping(path: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if "\t" not in line:
                print(f"WARN: line {n} has no tab; skipping: {line!r}", file=sys.stderr)
                continue
            src, dst = line.split("\t", 1)
            mapping[src.strip().lower()] = dst.strip()
    return mapping


def build_regex(keys) -> re.Pattern:
    keys = sorted(keys, key=len, reverse=True)
    pat = "|".join(re.escape(k) for k in keys)
    return re.compile(r"\[\[(" + pat + r")(\|[^\]]+|#[^\]]+)?\]\]", re.IGNORECASE)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mapping")
    ap.add_argument("--vault", help="Vault root override (else KM_VAULT_PATH or CWD)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--include-templates", action="store_true")
    args = ap.parse_args()

    vault = resolve_vault(args.vault)
    wiki = vault / "wiki"
    if not wiki.is_dir():
        print(f"ERROR: {wiki} is not a directory", file=sys.stderr)
        return 1

    if not os.path.isfile(args.mapping):
        print(f"ERROR: mapping not found: {args.mapping}", file=sys.stderr)
        return 1
    mapping = load_mapping(args.mapping)
    if not mapping:
        print("ERROR: mapping file empty", file=sys.stderr)
        return 1

    rx = build_regex(mapping.keys())
    changed, total = 0, 0
    for root, _, files in os.walk(wiki):
        parts = root.split(os.sep)
        if not args.include_templates and "_templates" in parts:
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            if fn.startswith("lint-report-"):
                continue
            p = os.path.join(root, fn)
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            def repl(m: re.Match) -> str:
                tail = m.group(2) or ""
                return f"[[{mapping[m.group(1).lower()]}{tail}]]"

            new, n = rx.subn(repl, content)
            if n > 0:
                total += n
                changed += 1
                print(f"{p}: {n}")
                if not args.dry_run:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(new)
    suffix = " (dry-run)" if args.dry_run else ""
    print(f"\nTotal: {total} substitutions across {changed} files{suffix}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
