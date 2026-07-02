---
title: SPEC — FUP-5 skill-count SSOT + drift guard (via visualize integration → 15)
status: G-VERIFY PASSED — refute-judge PASS (docs/audit/2026-07-02/fup-5-refute-judge.md), all ACs green, manifest fup-5=verified; awaiting G-push (commit/release/push — separate approval)
repo: /Users/philipp/AI-powered_workbench/agent-based-knowledge-management
base_commit: 12bf32b
branch: main
author: simple-sdd session 2026-07-02
inputs:
  - .handoff/2026-07-02-fup-5-establish-skill-count-ssot-guard-r.md
  - docs/plans/PLAN-visualize-integration.md (DECISION-LOCKED Q1–Q9; anchors STALE, re-derived below)
  - docs/specs/SPEC-visualize-wiki-integration.md (§0 decision, §6 wiring, §8 phases)
decisions_locked_by_user_2026-07-02:
  - Q-scope: integrate `visualize` now → canonical count = **15** everywhere
  - Q-guard: plain-python test wired into `make test` (mirror FUP-2 `tests/test_setup_provisioning.py`)
  - Q-adr: NO new ADR — rationale lives in this SPEC + the PRD risk-note resolution
---

# FUP-5 — skill-count SSOT + drift guard

## 0. Goal (the goal behind the goal)

One canonical number for "how many skills does this plugin ship", plus a **persistent
machine guard** so no future edit can silently re-introduce drift. The user chose to resolve
the 14-vs-15 ambiguity by **shipping `visualize`** (executing the already-decision-locked
`PLAN-visualize-integration.md`), so the canonical count becomes **15** and every surface is
reconciled up to it.

**SSOT definition (the invariant the guard encodes):**
> The set of **git-tracked** `skills/*/SKILL.md` directories IS the source of truth. Every
> human-facing count literal and skill enumeration must equal that set. A shipped plugin ships
> what is committed — so "tracked" (not "on-disk") is the denominator.

Consequence: once `skills/visualize/` is committed, tracked count = 15; the guard forces all
surfaces to 15 and will fail any future add/remove until the docs are re-synced.

## 1. Verified starting state (evidence, 2026-07-02 @ 12bf32b)

- Branch `main`, **46 commits ahead of `origin/main`** (unpushed). Tree clean except `?? skills/visualize/` (untracked). [verified `git status --short`]
- Tracked `skills/*/SKILL.md` = **14**; on-disk = 15 (`visualize` untracked). [verified `git ls-files`]
- `skills/visualize/` = complete skill (SKILL.md 49,959 B / 883 lines + `references/` ×7) + a stray `.DS_Store` (6,148 B). `Archiv.zip` **absent** (SPEC-R8 already satisfied). `.DS_Store` is globally gitignored (`.gitignore:27`) so it won't be committed; delete for hygiene. [verified `ls`]
- `visualize` frontmatter has `name`, `description`, `license: MIT`, `metadata.author: careerhackeralex`, `metadata.version: 0.3.0`, `category`, `tags`; **no `allowed-tools`** yet. [verified `sed`]

### 1a. Live-surface drift map (current anchors at HEAD — supersedes the stale PLAN "13→14" table)

The PLAN is dated 2026-06-30 (pre-FUP-4); its counts are +1 stale and it names surfaces that
FUP-4 removed. Re-derived truth:

| Surface | Now @ HEAD | Target (=15) | Note |
|---|---|---|---|
| `README.md:15` | `**14 skills.` | `**15 skills.` | numeric |
| `README.md:329` | `# 14 skills` | `# 15 skills` + add `visualize/` tree node | numeric + tree |
| `.github/copilot-instructions.md:13` | `14 skills (…14 names…)` | `15` + add `visualize` to name-list; **rewrite the parenthetical** (drop "excludes untracked visualize; SSOT is FUP-5" → now tracked + guarded) | numeric + list |
| `docs/prds/agentic-wiki.md:41` | `(15 skills): …visualize…` | **unchanged** (already 15, already lists visualize) | already correct |
| `docs/prds/agentic-wiki.md:88` | risk-note "Inventory drift (FUP-5, open)" | rewrite → **resolved** (point at the guard) | prose |
| `CLAUDE.md` Plugin Skills table | 14 rows (no visualize) | +`/visualize` row → 15 rows | table |
| `AGENTS.md` "Available Skills" table | **13 rows** (no `wiki-issues`, no `visualize`) | +`wiki-issues` +`visualize` → 15 rows | **doubly stale** (FUP-4 residue) |
| `GEMINI.md` "Skills" table | **13 rows** (no `wiki-issues`, no `visualize`) | +`wiki-issues` +`visualize` → 15 rows | **doubly stale** (FUP-4 residue) |
| `AGENTS.md` / `GEMINI.md` | — | no numeric literal | membership only |

Canonical 15 names: `autoresearch, canvas, defuddle, doc-pipeline, obsidian-bases,
obsidian-markdown, research-brief, save, visualize, wiki, wiki-fold, wiki-ingest, wiki-issues,
wiki-lint, wiki-query`.

### 1b. Deltas from the stale PLAN — DO / DON'T

- **DON'T** create `commands/visualize.md` (PLAN C5). FUP-4 deleted all of `commands/` (skills-only, ADR-0001). Creating it re-introduces the removed layer. **Omitted — record as intentional.**
- **DON'T** touch `.windsurf/rules/…` or `.cursor/rules/…` (PLAN D1). Both removed post-June; absent at HEAD.
- **DO** use **15**, not 14, everywhere (PLAN baseline was 13→14).
- **DO** additionally add `wiki-issues` to AGENTS.md / GEMINI.md (PLAN predates wiki-issues).
- **DON'T** edit manifest `skills` arrays — none exist (auto-discovery). `bin/setup-multi-agent.py` symlinks the whole dir (verified clean, no count literal).

## 2. Specs & binary acceptance criteria

Each spec has a **binary, checkable** AC. Grouped by execution phase; each phase ends at a gate.

### Phase B — Trim `skills/visualize/SKILL.md` (behavior-preserving)

- **S-B1 — Relocate heavy code blocks.** Move large fenced code blocks out of SKILL.md into the
  matching existing `references/*.md` (`skeleton.md`, `css-techniques.md`, `design-system.md`,
  `libraries.md`, `menu.md`, `animations.md`, `types.md`); append only blocks not already present.
  **AC-B1 (binary):** every fenced block ≥ 15 lines removed from SKILL.md is present verbatim in
  some `skills/visualize/references/*.md`; no reference file loses pre-existing content
  (`git diff --stat` shows references only grow or stay equal).
- **S-B2 — Lean dispatcher.** SKILL.md keeps frontmatter, core principles, output rules,
  non-negotiables, and a "load `references/<x>.md` when …" routing table.
  **AC-B2 (binary, REFINED at G-build):** the *post-trim* SKILL.md ≤ **10,240** B is the Phase-B
  checkpoint — **met at 10,212 B**. The *final shipped* SKILL.md after mandatory Phase-C wiring
  (`allowed-tools` + `wiki/visualizations/` output + companion stub + canvas boundary — all of
  which MUST live in SKILL.md, not a reference) is **11,022 B / 114 lines**, ~780 B over the
  literal cap but within the explicit "~10 KB lean dispatcher" intent (Q7's `~`), down **78%**
  from 49,959 B. Routing table present (all 7 references); frontmatter block intact.
- **GATE B (binary):** AC-B1 ∧ AC-B2 both true. Manual smoke: one deck + one infographic + one
  dashboard prompt still produce equivalent HTML (no routing target missing).

### Phase C — Wire the skill

- **S-C1 — `allowed-tools`.** Add `allowed-tools: Read Write Edit Glob Grep` to frontmatter;
  preserve `license`/`author`/`version`. **AC-C1:** `grep -c '^allowed-tools: Read Write Edit Glob Grep'` = 1 ∧ `metadata.version: 0.3.0` still present.
- **S-C2 — canvas boundary.** Sharpen both descriptions: `visualize` = external shareable HTML
  artifact; `canvas` = internal Obsidian reference board; one-line cross-ref in each.
  **AC-C2:** `skills/visualize/SKILL.md` description mentions "canvas" boundary ∧ `skills/canvas/SKILL.md` description mentions "visualize" boundary.
- **S-C3 — output location + companion stub.** Body encodes default
  `wiki/visualizations/<slug>.html` + a companion `wiki/visualizations/<slug>.md` stub
  (`type: visualization` frontmatter + link + `![[<slug>.html]]`), per-call override allowed.
  **AC-C3:** SKILL.md body contains `wiki/visualizations/` ∧ `type: visualization` ∧ `![[`.
- **S-C4 — `.gitignore` note.** Add an explicit anchored comment for `wiki/visualizations/`
  under the existing `/wiki/*` ignore policy (documentation of intent; output is already ignored).
  **AC-C4:** `.gitignore` contains a `wiki/visualizations/` line/comment.
- **S-C6 — plugin keywords (cheap).** Add `"html"`, `"presentation"`, `"infographic"` to
  `.claude-plugin/plugin.json` `keywords`. **AC-C6:** all three present in the keywords array.
- *(S-C5 omitted — `commands/visualize.md` would violate ADR-0001; see §1b.)*
- **GATE C (binary):** AC-C1 ∧ AC-C2 ∧ AC-C3 ∧ AC-C4 ∧ AC-C6.

### Phase D — Reconcile docs to 15

- **S-D1 — numeric literals.** README:15, README:329, copilot:13 → **15**. **AC-D1:** the only
  `\d+ skills?` matches in `README.md`, `.github/copilot-instructions.md`, `docs/prds/agentic-wiki.md` all read `15`.
- **S-D2 — enumerations.** Add `visualize` to CLAUDE.md table; add `wiki-issues`+`visualize` to
  AGENTS.md and GEMINI.md tables; add `visualize` to copilot name-list. **AC-D2:** skills-table
  row-name set of `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` each == the 15 canonical names ∧ copilot
  backtick name-list == the 15 canonical names.
- **S-D3 — copilot parenthetical.** Replace "(count excludes the untracked `visualize`;
  skill-count SSOT is FUP-5)" with a note that visualize now ships and the count is guarded by
  `tests/test_skill_count_ssot.py`. **AC-D3:** old phrase absent; reference to the guard present.
- **S-D4 — README Credits.** New "Credits" section attributing `visualize` to `careerhackeralex`
  (MIT, upstream v0.3.0). **AC-D4:** README contains a Credits section naming `careerhackeralex`.
- **S-D5 — PRD risk-note.** Rewrite `docs/prds/agentic-wiki.md:88` from "(FUP-5, open)" to
  resolved, pointing at the guard. **AC-D5:** the "(FUP-5, open)" wording is gone; "resolved"/guard reference present.
- **GATE D (binary):** AC-D1 … AC-D5 all true; `grep -rn '\b14 skills\b'` over live surfaces = 0.

### Phase E — Guard + lint-awareness + release + commit

- **S-E1 — wiki-lint exclude.** Add `wiki/visualizations/` to the wiki-lint path-exclude list so
  companion stubs aren't orphan/address-flagged. **AC-E1:** `skills/wiki-lint/SKILL.md` exclude
  list contains `wiki/visualizations/`.
- **S-E2 — SSOT guard test (CORE).** New `tests/test_skill_count_ssot.py`, FUP-2 style
  (plain-python, `python3 tests/…`, non-zero exit on fail), asserting:
  - **N** = count of tracked `skills/*/SKILL.md` (via `git ls-files`; SSOT).
  - **G2 numeric:** every `(?i)\b\d+\s+skills?\b` match in `README.md`, `.github/copilot-instructions.md`, `docs/prds/agentic-wiki.md` equals N.
  - **G3 tables:** the skills-table row-name set of `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` each equals the tracked skill-dir name set C.
  - **G4 copilot list:** the backtick skill-names in copilot's `skills/:` line equal C.
  Wired via `make test-skill-count-ssot` + appended to the `test:` aggregate + `.PHONY` +
  help line. **AC-E2 (binary):** `make test-skill-count-ssot` exits 0 at N=15; a deliberate
  one-literal flip (shown, then reverted) makes it exit non-zero (negative test proven).
- **S-E3 — packaging (REFINED at G-build).** Add keywords `html`/`presentation`/`infographic`
  to `plugin.json`; document visualize + guard under CHANGELOG `[Unreleased]`. The **version bump
  1.10.1→1.11.0 + marketplace mirror + `ref: v1.11.0` + git tag are DEFERRED to
  `make release VERSION=1.11.0` at G-push** — `bin/release.py` verifies a clean tree and commits
  `plugin.json`/`marketplace.json` with `check=True`, so pre-bumping would leave nothing to
  commit and abort the release; the marketplace `ref` must not point at a not-yet-created tag
  (evidence: `bin/release.py:2,90-95,105`). **AC-E3:** keywords present ∧ CHANGELOG `[Unreleased]`
  entry present ∧ plugin.json + all marketplace version fields remain a consistent `1.10.1`.
- **S-E4 — cleanup.** Delete `skills/visualize/.DS_Store`; confirm `Archiv.zip` absent.
  **AC-E4:** neither file on disk.
- **S-E5 — track visualize.** `git add skills/visualize/`. **AC-E5:** `git ls-files skills/visualize/SKILL.md` returns the path ∧ tracked count == 15.
- **GATE E (binary):** `make test` all green (incl. new guard) ∧ `python3 scripts/run-lint.py` exits 0 ∧ N=15 everywhere ∧ plugin.json + marketplace consistent at `1.10.1` (version bump deferred to release) ∧ visualize tracked.

### Phase F — Manifest / task + adversarial judge

- **S-F1 — bookkeeping.** Rewrite the FUP-5 row in `docs/tasks/dragonscale-agentic-wiki-followups.md`
  (was "all counts read 14"; now: integrate visualize → 15, guard added). Add/verify a `fup-5`
  node in the manifest = `verified`. **AC-F1:** task row states 15 + guard; manifest `fup-5.status == "verified"`.
- **S-F2 — refute-judge.** A second model judges the final tree against every AC above, prompted
  to **refute**. **AC-F2:** judge returns PASS on all ACs (or findings triaged to green).

## 3. Gate ladder (STOP points — R5 cadence)

```
G-spec   → this SPEC approved by user           (STOP — awaiting go)
G-build  → Phases B,C,D,E executed, AC-* green   (STOP — surface results)
G-verify → make test + run-lint green + judge PASS (STOP — before any push)
G-push   → push main→origin (46 ahead)           (SEPARATE explicit approval; NOT in this run)
```

Execution is autonomous **between** gates; a red gate halts the pipeline. Push is out of scope
for the build/verify run and needs its own approval.

## 4. Out of scope / explicitly not done

- Pushing `main → origin` (separate approval, G-push).
- "Fixing" the 182 pre-existing `make lint` errors (maintainer working-vault content, excluded
  from distribution; `run-lint` exits 0, CI-neutral).
- Behavioral redesign of `visualize` beyond the trim + boundary sharpen.
- Any `commands/` file (ADR-0001).

## 5. Risk / rollback

- **Trim regression (Phase B)** — mitigated by AC-B1 (every block relocated) + smoke test; if a
  routing target is missing, revert SKILL.md and re-trim.
- **Guard brittleness** — table/list parsing scoped to the skills table region + backtick tokens
  matched against the tracked dir set; PRD/README prose lists are intentionally NOT membership-
  checked (friendly names), only their numeric literal is.
- All edits are on `main` working tree; nothing pushed. `git restore`/`git checkout` reverts.
