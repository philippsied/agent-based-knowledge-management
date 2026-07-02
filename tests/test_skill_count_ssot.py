#!/usr/bin/env python3
"""test_skill_count_ssot.py — skill-count single-source-of-truth guard (FUP-5).

Drift guard for the plugin's advertised skill inventory. The **single source of
truth** is the set of git-tracked `skills/*/SKILL.md` directories: a shipped plugin
ships what is committed, so "tracked" (not "on-disk") is the canonical denominator.
Every human-facing count literal and every skill enumeration table/list must equal
that set. Before this guard, the count drifted silently across the plugin's surfaces
(e.g. 13 vs 14 vs 15, and enumeration tables missing whole skills).

This plugin is Claude-only — the AGENTS.md / GEMINI.md / copilot surfaces were removed
in the 2.0.0 consolidation; the guarded surfaces are the Claude + distribution set.

Three assertions, all against the *tracked* set C (|C| = N):

- **SSOT:** N = number of tracked `skills/*/SKILL.md` (via `git ls-files`).
- **G2 numeric literals:** every `<digits> skill(s)` phrase in README.md and
  docs/prds/agentic-wiki.md equals N.
- **G3 enumeration table:** the skill-name row set of the "Skill" table in
  CLAUDE.md equals C.

Prose "friendly-name" lists (README narrative, PRD `(N skills): ingest, query, …`)
are intentionally NOT membership-checked — they use display names, not dir slugs —
only their numeric literal is guarded by G2.

Usage:
  python3 tests/test_skill_count_ssot.py     # exits 0 on pass, 1 on drift
  make test-skill-count-ssot
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files carrying a numeric "<n> skills" literal (G2). Only these are scanned, so
# historical planning docs (docs/plans, docs/specs, CHANGELOG) that reference past
# counts do not trip the guard.
NUMERIC_SURFACES = [
    "README.md",
    "docs/prds/agentic-wiki.md",
]

# Files whose "Skill" enumeration table must list exactly the canonical set (G3).
TABLE_SURFACES = ["CLAUDE.md"]

PASS = 0


class Fail(SystemExit):
    """Raised on any drift; exits non-zero so make/CI catches it."""


def _ok(msg):
    global PASS
    PASS += 1
    print(f"  ok  {msg}")


def _fail(msg):
    raise Fail(f"FAIL: {msg}")


def tracked_skill_set():
    """Canonical set C = basenames of git-tracked skills/*/SKILL.md (the SSOT)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "skills/*/SKILL.md"],
            capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        _fail(f"could not enumerate tracked skills via git ls-files: {exc}")
    names = {
        line.split("/")[1]
        for line in out.splitlines()
        if line.startswith("skills/") and line.endswith("/SKILL.md")
    }
    if not names:
        _fail("git ls-files returned no tracked skills/*/SKILL.md — wrong cwd or nothing staged")
    return names


def read(rel):
    p = ROOT / rel
    if not p.exists():
        _fail(f"expected surface missing on disk: {rel}")
    return p.read_text(encoding="utf-8")


def first_backtick_slug(cell):
    """First `backtick-slug` token's leading slug in a table cell, or None.

    Tolerates adornments *inside* the backticks (e.g. `/autoresearch [topic]`,
    `/wiki-query`) by capturing the leading `[a-z][a-z0-9-]+` slug after an
    optional `/`, without requiring a closing backtick right after the slug.
    Header ("Skill") and separator ("---") cells have no backtick → None.
    """
    m = re.search(r"`/?([a-z][a-z0-9-]+)", cell)
    return m.group(1) if m else None


def table_skill_names(rel):
    """Skill-name set from the `| Skill | … |` table in `rel` (first-cell backtick slugs)."""
    lines = read(rel).splitlines()
    names, in_table, seen_sep = set(), False, False
    for ln in lines:
        cells = ln.split("|")
        if not in_table:
            # header row whose first data-cell is exactly "Skill"
            if len(cells) >= 3 and cells[1].strip() == "Skill":
                in_table = True
                seen_sep = False
            continue
        # inside the table
        if "|" not in ln or ln.strip() == "":
            break  # table ended
        if not seen_sep:
            seen_sep = True  # the |---|---| separator row
            continue
        slug = first_backtick_slug(cells[1] if len(cells) >= 2 else "")
        if slug:
            names.add(slug)
    if not names:
        _fail(f"no skill rows found in the 'Skill' table of {rel}")
    return names


def main():
    canonical = tracked_skill_set()
    n = len(canonical)
    print(f"SSOT: {n} tracked skills — {sorted(canonical)}")

    # G2 — every numeric "<n> skills" literal == N
    for rel in NUMERIC_SURFACES:
        # `(?!-)` skips hyphenated compounds ("3 skill-related") — never a count literal.
        found = re.findall(r"\b(\d+)\s+skills?\b(?!-)", read(rel), re.IGNORECASE)
        if not found:
            _fail(f"{rel}: expected a '<n> skills' count literal, found none")
        bad = [v for v in found if int(v) != n]
        if bad:
            _fail(f"{rel}: count literal(s) {bad} != canonical {n} (all '<n> skills' must read {n})")
        _ok(f"{rel}: {len(found)} numeric literal(s) all == {n}")

    # G3 — each enumeration table's skill set == canonical set
    for rel in TABLE_SURFACES:
        names = table_skill_names(rel)
        if names != canonical:
            missing = sorted(canonical - names)
            extra = sorted(names - canonical)
            _fail(f"{rel} skills table drift — missing={missing} extra={extra}")
        _ok(f"{rel}: skills table lists exactly the {n} canonical skills")

    print(f"\nAll {PASS} skill-count SSOT checks passed (N={n}).")


if __name__ == "__main__":
    main()
