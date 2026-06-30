#!/usr/bin/env python3
"""finalize-md.py — Stage 4 of the doc→ingest pipeline (agentic-knowledge-management).

Takes an APPROVED staging file (raw MD + inline review annotations) and emits
a clean, ingest-ready Markdown: the <!-- PIPELINE-REVIEW ... --> header and all
<!-- REVIEW[...] --> comments are stripped. The staging file is left untouched
as the audit trail.

Guard: refuses to run unless the PIPELINE-REVIEW header says `status: approved`
(override with --force). This is the approval gate.

Usage:
  "$CLAUDE_PLUGIN_ROOT/skills/doc-pipeline/finalize-md.py" <staging-file.md> [--out-dir DIR] [--force]

Default out-dir = <vault>/.raw  (ingest-ready; picked up by the wiki-ingest skill)
"""

import os
import re
import sys
from pathlib import Path

# vault root via plugin-wide resolver (PR0): KM_VAULT_PATH env → cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "lib"))
from vault_root import resolve_vault_root  # noqa: E402


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def main(argv: list[str]) -> int:
    root = resolve_vault_root()

    if not argv:
        err("usage: finalize-md.py <staging-file.md> [--out-dir DIR] [--force]")
        return 2
    src = argv[0]
    rest = argv[1:]

    out_dir = str(root / ".raw")
    force = False
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--out-dir":
            out_dir = rest[i + 1]
            i += 2
        elif arg == "--force":
            force = True
            i += 1
        else:
            err(f"unknown arg: {arg}")
            return 2

    src_path = Path(src)
    if not src_path.is_file():
        err(f"ERROR: not found: {src}")
        return 1

    src_text = src_path.read_text(encoding="utf-8")

    # ---- approval gate ----
    if not force:
        if not re.search(r"^[ \t]*status:[ \t]*approved", src_text, re.MULTILINE):
            err(f"✗ BLOCKED: '{os.path.basename(src)}' is not approved.")
            err("  Set 'status: approved' in its <!-- PIPELINE-REVIEW --> header (or use --force).")
            return 3

    base = os.path.basename(src)
    out_path_dir = Path(out_dir)
    out_path_dir.mkdir(parents=True, exist_ok=True)
    out = out_path_dir / base

    # ---- strip pipeline metadata + annotations, tidy whitespace ----
    #  1) remove the multi-line <!-- PIPELINE-REVIEW ... --> header
    #  2) remove every single-/multi-line <!-- REVIEW[...] ... --> annotation
    #  3) collapse 3+ consecutive blank lines to a single blank line
    #  4) drop leading blank lines
    # NOTE: do NOT trim trailing whitespace — two trailing spaces are meaningful
    #       Markdown hard line breaks and must survive into the ingest-ready file.
    text = src_text
    text = re.sub(r"<!--\s*PIPELINE-REVIEW\b.*?-->\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"[ \t]*<!--\s*REVIEW\[.*?\].*?-->[ \t]*\n?", "", text, flags=re.DOTALL)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\A\n+", "", text)
    out.write_text(text, encoding="utf-8")

    # grep -c counts matching LINES, not total matches — replicate that.
    marker_re = re.compile(r"<!--\s*(?:PIPELINE-)?REVIEW")
    remaining = sum(1 for line in text.splitlines() if marker_re.search(line))
    words = len(text.split())
    print(f"✓ ingest-ready: {_relto(out, root)}  ({words} words)")
    if remaining > 0:
        err(f"  ⚠ {remaining} review marker(s) still present — inspect manually.")
    print(f"  audit trail kept at: {_relto(src_path, root)}")
    return 0


def _relto(path: Path, root: Path) -> str:
    """Mimic shell `${VAR#$ROOT/}` — strip a leading "<root>/" prefix if present."""
    prefix = f"{root}/"
    s = str(path)
    return s[len(prefix):] if s.startswith(prefix) else s


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
