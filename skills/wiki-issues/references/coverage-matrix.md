# Coverage matrix — commands → `wiki-issues` skill (ADR-0001 delete gate)

ADR-0001 requires **proven in-skill coverage** of every substantive command behavior *before* the
command files are deleted. This matrix maps each behavior of the two substantive commands
(`commands/wiki/handoff.md`, `commands/wiki/fix-issues.md`) to the covering anchor in
[SKILL.md](../SKILL.md). Gate is green iff there are **zero UNCOVERED rows**.

The 5 thin wrappers (`autoresearch`, `canvas`, `save`, `doc-pipeline`, `wiki`) are covered trivially:
each is a `/slash` router whose same-named skill already exists on disk (`skills/<name>/SKILL.md`,
verified present). They carry no unique logic. → **covered by the pre-existing skills**.

## handoff.md (126 ln) → push flow

| # | Command behavior | Source | SKILL.md anchor | Covered |
|---|---|---|---|---|
| H1 | Dual hybrid data model (YAML stack + body sections) | L13–24 | `## Data model` | ✅ |
| H2 | Section whitelist | L26–38 | `Section whitelist (12)` + template | ✅ reconciled 7→12 (V-6) |
| H3 | Pre-conditions: git dirty → ABORT; log commit hash | L40–45 | `## Pre-conditions` 1–2 | ✅ |
| H4 | Read structure + ID counter (stack + aggregated_from + `wiki/log.md` scan → max+1; no recycle) | L47–57 | push `### P1` | ✅ |
| H5 | Synthesis criteria (concrete · WO-anchor · not session-state · aggregate convergent) | L59–78 | push `### P2` | ✅ |
| H6 | Priority-sorted insert (not naive prepend; body appended to section) | L80–84 | push `### P3` | ✅ |
| H7 | Edit verification (diff · updated=today · no existing item changed · parity · unique id · section∈WL · blocked_by exists · sort) | L86–98 | push `### P4` | ✅ |
| H8 | Optional validator run | L98 | push `### P4` + `## Deterministic core` (now mandatory) | ✅ |
| H9 | Commit `docs(meta): handoff <N> …` | L100–110 | push `### P5` | ✅ |
| H10 | Final report (3 lines: Filed / Top of stack / Commit) | L112–118 | push `### P6` | ✅ |
| H11 | "does NOT" constraints (no edit-existing · no anchorless · no aggregated_from · no recycle · no mass-reorg) | L120–126 | push `### push does NOT` | ✅ |

## fix-issues.md (211 ln) → pop flow

| # | Command behavior | Source | SKILL.md anchor | Covered |
|---|---|---|---|---|
| F1 | Exactly one issue per invocation | L8, L32 | pop `### Hard rules` | ✅ |
| F2 | Language DE chat/bodies, EN identifiers | L10 | header `**Language:**` | ✅ |
| F3 | Dual hybrid data model; truth in frontmatter | L12–28 | `## Data model` | ✅ |
| F4 | Hard rules (one issue · clean baseline · no silent aggregate · no delete-unverified · no drift) | L30–36 | pop `### Hard rules` | ✅ |
| F5 | Pre-conditions (git dirty → ABORT; log hash) | L38–43 | `## Pre-conditions` | ✅ |
| F6 | Read fully + stack↔body drift check → abort on drift | L45–47 | pop `### F1` | ✅ |
| F7 | Top-of-stack = first ready item; empty / all-blocked edges | L49–57 | pop `### F2` | ✅ |
| F8 | Aggregation scan (MANDATORY, once, user consent, options (1)/(2)) | L59–85 | pop `### F3` | ✅ |
| F9 | Verify against repo (WO-anchor: file/line/tooling/script checks) | L87–95 | pop `### F4` | ✅ |
| F10 | 4a resolved → remove stack+body, `wiki/log.md` entry, updated | L98–109 | pop `### F4 → F4a` | ✅ |
| F11 | 4b stale → in-place patch, keep item, no log | L111–117 | pop `### F4 → F4b` | ✅ |
| F12 | 4c still real → fix, remove both, log | L119–132 | pop `### F4 → F4c` | ✅ |
| F13 | 4d inconclusive → set inconclusive_since/reason, sort last | L134–141 | pop `### F4 → F4d` | ✅ |
| F14 | Commit discipline (per-disposition formats; never --no-verify/--amend) | L143–167 | pop `### F5` | ✅ |
| F15 | Final report (3 lines: Top-Issue / Outcome / New top) | L169–177 | pop `### F6` | ✅ |
| F16 | Aggregation path (remove N, one new item + aggregated_from, no fix, commit) | L179–202 | pop `### F7` | ✅ |
| F17 | Edge cases (empty · all-blocked · bad blocked_by · drift · inconclusive-not-abort · fix-touches-more-files) | L204–211 | pop `### pop edge cases` | ✅ |

## Behaviors added by SPEC/ADR-0005 beyond the commands (not a coverage gap — additive)

| # | Behavior | Origin | SKILL.md anchor | Present |
|---|---|---|---|---|
| A1 | init flow (scaffold when absent) | SPEC AC1 | `## init flow` | ✅ |
| A2 | Format-version guard before any write (reference I-2026-041) | SPEC AC6 / ADR-0005 | `## Format-version guard` | ✅ |
| A3 | Ported validator wired into `run-lint` (schema/parity/cycles/sort) | SPEC AC5 | `## Deterministic core` + `scripts/lint-open-issues.py` | ✅ |
| A4 | Hard-delete on resolve → history to `wiki/log.md` | SPEC / ADR-0005 | `## Resolution log` | ✅ |

## Verdict
**0 UNCOVERED** across H1–H11, F1–F17. The 5 thin wrappers are covered by their pre-existing
same-named skills. ADR-0001 delete gate (G-coverage) is therefore **green** — the 7 command files may
be deleted.
