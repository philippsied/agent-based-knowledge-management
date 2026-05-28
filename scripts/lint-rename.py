#!/usr/bin/env python3
"""Rename <vault>/wiki/*.md files with spaces in their basename to
hyphenated form. Then rewrite all inbound `[[Old Name]]` wikilinks to
`[[Old-Name]]` across the vault.

Vault root resolution (matches lib/vault_root.sh):
    --vault flag  ->  KM_VAULT_PATH env  ->  current working directory

Use `--dry-run` to preview without renaming or rewriting.

This is the one-shot remediation for the convention enforced by
`hooks/wiki-path-safety.sh` (Rule 2). Run it once on a vault that
predates the hook to bring legacy filenames into compliance.
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--vault", help="Vault root override (else KM_VAULT_PATH or CWD)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without renaming or rewriting")
    args = ap.parse_args()

    vault = resolve_vault(args.vault)
    wiki = vault / "wiki"
    if not wiki.is_dir():
        print(f"ERROR: {wiki} is not a directory", file=sys.stderr)
        return 1

    renames: list[tuple[str, str, str, str]] = []
    for root, _dirs, files in os.walk(wiki):
        parts = root.split(os.sep)
        if "_templates" in parts:
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            if " " not in fn:
                continue
            old_path = os.path.join(root, fn)
            old_base = fn[:-3]
            new_base = old_base.replace(" ", "-")
            new_fn = new_base + ".md"
            new_path = os.path.join(root, new_fn)
            if os.path.exists(new_path):
                print(f"SKIP collision: {new_path} already exists", file=sys.stderr)
                continue
            renames.append((old_path, new_path, old_base, new_base))

    # Execute renames.
    for old_path, new_path, _, _ in renames:
        if args.dry_run:
            print(f"WOULD RENAME: {old_path} -> {new_path}")
        else:
            os.rename(old_path, new_path)
            print(f"RENAMED: {old_path} -> {new_path}")

    print(f"\nTotal renames: {len(renames)}{' (dry-run)' if args.dry_run else ''}")

    if not renames:
        print("No renames; skipping wikilink rewrite.")
        return 0

    # Rewrite [[Old Name]] (case-insensitive on the key) to [[New-Name]].
    mapping = {old_base.lower(): new_base for _, _, old_base, new_base in renames}
    keys = sorted(mapping.keys(), key=len, reverse=True)
    key_pat = "|".join(re.escape(k) for k in keys)
    link_re = re.compile(r"\[\[(" + key_pat + r")(\|[^\]]+|#[^\]]+)?\]\]", re.IGNORECASE)

    changed_files = 0
    total_subs = 0
    for root, _, files in os.walk(wiki):
        parts = root.split(os.sep)
        if "_templates" in parts:
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(root, fn)
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            def repl(m: re.Match) -> str:
                key = m.group(1).lower()
                tail = m.group(2) or ""
                return f"[[{mapping[key]}{tail}]]"

            new, n = link_re.subn(repl, content)
            if n > 0:
                if not args.dry_run:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(new)
                changed_files += 1
                total_subs += n

    suffix = " (dry-run)" if args.dry_run else ""
    print(f"Wikilink rewrites: {total_subs} substitutions across {changed_files} files{suffix}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
