---
title: SPEC — Repo consolidation to 2.0.0 (Claude-only, no history migration)
status: G3 GREEN — S1–S8 done (+ docs/DECISION-LOG.md refute-judge PASS; 5 handoffs pruned; project memory consolidated + index consistent); awaiting go for G4 (final verify + push checkpoint)
repo: /Users/philipp/AI-powered_workbench/agent-based-knowledge-management
base_commit: 2d8daca
branch: main
author: simple-sdd session 2026-07-02
inputs:
  - .handoff/2026-07-02-repo-upgrade-auf-2-0-0-abschliessen-voll.md  (driving handoff; consumed → pruned in S6, durable content captured in docs/DECISION-LOG.md)
  - docs/manifests/dragonscale-agentic-wiki-followups.json
  - tests/test_skill_count_ssot.py (guard — surfaces coupled to multi-agent files)
scope_contract_fixed_2026-07-02:
  - Q-scope  = "Consolidate, do NOT migrate" → current repo to a clean push-able 2.0.0 state;
               history-wipe + move to a new repo is a SEPARATE later session.
  - Q-origin = "Push as checkpoint" → after all-green, push main to existing origin (push APPROVED).
  - Q-tag    = "Prepare, do NOT tag" → fix release gate + finalize CHANGELOG [2.0.0]; NO git tag cut.
defaults_applied_no_question_needed:
  - Multi-agent reduction = FULL Claude-only (goal: "komplett auf Claude reduzieren"); salvage valuable bits first.
  - Cleanup = keep dead-end SOURCE docs (plans/specs/audit) as decision-log source until the migration session; only prune the 4 handoffs.
  - Artifact set = Spec + binary ACs + gates + durable Decision-Log (maintenance consolidation, not greenfield → no PRD/Threat-Model/DPIA).
---

# SPEC — Repo consolidation to 2.0.0

## 0. Goal (the goal behind the goal)

Bring the repo from "48 commits ahead, unreleased, still multi-agent" to **one coherent,
push-able 2.0.0 state that presents as a Claude-only plugin**, with the accumulated
reversals/dead-ends captured once in a durable Decision-Log so the (later) history-wipe
migration can start from a clean, non-repeating record. This session does NOT execute the
migration and does NOT cut the release tag — it makes both trivially doable next.

## 1. Baseline (verified this session, 2026-07-02)

- `main`, **48 ahead of origin/main**, tree clean, HEAD `2d8daca`. [verified]
- Multi-agent surfaces all PRESENT: `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `bin/setup-multi-agent.py`. [verified]
- Guard `tests/test_skill_count_ssot.py` hardcodes: `TABLE_SURFACES = [CLAUDE.md, AGENTS.md, GEMINI.md]` (G3); `NUMERIC_SURFACES = [README.md, .github/copilot-instructions.md, docs/prds/agentic-wiki.md]` (G2); `COPILOT = .github/copilot-instructions.md` (G4). Deleting AGENTS/GEMINI/copilot **breaks the guard** unless surfaces are repointed to the Claude-only set. [verified]
- README multi-agent claims at L15 ("Multi-agent support"), L44/L51 (comparison table "Multi-model support | Claude, Gemini, Codex, Cursor, Windsurf"). [verified]
- `bin/release.py` lint gate (~:47-60) aborts when `run-lint --json totals.error != 0`; current 182 errors = working-vault `wiki/` (out-of-distribution). [verified]
- Manifest: only `spec-wiki-issues` = todo; all else verified. Branches `fup-4-wiki-issues`, `fup-5-skill-count-ssot` still exist (merged). [verified]

## 2. Specs (each with a BINARY, checkable acceptance criterion)

### S1 — Salvage valuable multi-agent content  (dep: none)
Extract every content block UNIQUE to `AGENTS.md` / `GEMINI.md` / `.github/copilot-instructions.md`
(not already in CLAUDE.md/skills); fold the operationally-valuable ones in, discard the rest with reason.
- **AC1:** `docs/audit/2026-07-02/multi-agent-salvage.md` exists and lists each unique block with a disposition `folded→<path>` or `discard:<reason>`.
- **AC2:** every block marked `folded→X` is grep-verifiable at X.

### S2 — Delete multi-agent surfaces + repoint guard  (dep: S1)
- **AC1:** `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `bin/setup-multi-agent.py` all absent (`test ! -e`).
- **AC2:** guard updated — `TABLE_SURFACES == ["CLAUDE.md"]`; `NUMERIC_SURFACES` no longer lists copilot; G4/`COPILOT` assertion removed; docstring reflects Claude-only.
- **AC3:** `make test-skill-count-ssot` exits 0.
- **AC4:** `make test` exits 0.

### S3 — Purge multi-agent claims from README + docs  (dep: S2)
- **AC1:** README.md carries no "Multi-agent support" / "Multi-model support" feature claim and no Gemini/Codex/Cursor/Windsurf/Copilot as-supported-tool row.
- **AC2:** `rg -i 'multi-agent|multi-model|GEMINI|copilot|codex|windsurf|setup-multi-agent'` over tracked files, excluding {CHANGELOG.md, docs/adr/**, docs/DECISION-LOG.md, docs/audit/2026-07-02/multi-agent-salvage.md, this spec}, returns **0 unintended** refs (each remaining hit manually confirmed historical/durable).
- **AC3:** `python scripts/run-lint.py` exits 0 (or documented working-vault-only residual, unchanged from baseline).

### S4 — Scope the release lint gate to distributed paths  (dep: none)
> **Evidence correction (2026-07-02):** `scripts/run-lint.py` is a WORKING-VAULT linter
> (scans `wiki/`, exits 0 even on findings), NOT a distribution linter — it scans zero
> shipped files. So "scope to distribution" = exclude its findings from the gate; the
> gate blocks only when run-lint itself cannot run. The original AC3 ("inject error in a
> distributed file") was based on a wrong assumption about run-lint's scope; reframed below.
- **AC1:** `bin/release.py` gate excludes working-vault findings (distribution scope = 0 run-lint files); mechanism documented in the `lint_gate()` docstring. ✓
- **AC2 (positive):** current tree (182 vault findings) → gate PASSES. ✓ (`tests/test_release_gate.py`)
- **AC3 (negative, reframed):** the gate still BLOCKS when run-lint cannot run (rc≠0 / unparseable JSON / missing totals). ✓ (3 block-cases in `tests/test_release_gate.py`)
- **AC4:** `git tag -l v2.0.0` empty (no tag cut). ✓

### S5 — Finalize CHANGELOG for 2.0.0  (dep: none)
- **AC1:** `## [2.0.0] - 2026-07-02` is the top RELEASED section.
- **AC2:** it documents (a) BREAKING `commands/` removal [FUP-4], (b) `visualize` as 15th skill [FUP-5], (c) skill-count SSOT guard [FUP-5], (d) multi-agent → Claude-only reduction [this session].
- **AC3:** `.claude-plugin/plugin.json` version NOT bumped (stays pre-2.0.0 until the tag session) — consistent with "prepare, not tag".

### S6 — Prune disposable work-states  (dep: S7 — content captured first)
- **AC1:** all `.handoff/*.md` removed (evidence: 5 files present, not 4 as the handoff stated).
- **AC2:** `.handoff/` is gitignored (untracked local process artifacts — `.gitignore:139`), so pruning leaves no git-level dangling reference. No tracked file carries a broken markdown/wikilink to a pruned handoff; the residual mentions are `inputs:` provenance (frontmatter strings) and grep-exclusion patterns, not file dependencies.
- **AC3:** `docs/plans/**`, executed `docs/specs/**`, `docs/audit/**` PRESERVED (decision-log source until migration) — presence-checked, NOT deleted this session.

### S7 — Durable Change + Decision log  (dep: none; feeds S6)
- **AC1:** `docs/DECISION-LOG.md` exists (confirm none pre-existing first).
- **AC2:** one structured entry per reversal/dead-end, ≥6: sh→py migration, commands→skills (ADR-0001/FUP-4), counter off-by-one (ADR-0004/FUP-2), visualize integrate-vs-exclude, release lint-gate trap, multi-agent → Claude-only — each `{what-changed, what-was-tried-&-reversed, why, current-state, refs-by-path}`.
- **AC3:** a linear "2.0.0 change summary" section that references CHANGELOG (no duplication).
- **AC4 (judge):** a second model, prompted to REFUTE completeness, confirms all 6 dead-ends represented and no already-fixed error is presented as still-open.

### S8 — Memory synthesis + consolidation  (dep: S7)
- **AC1:** `consolidate-memory` run; MEMORY.md index has no dangling pointer (every listed file exists) and every memory file is listed.
- **AC2:** `release-lint-gate-blocks-on-working-vault.md` updated to reflect the S4 fix (resolved), not left stale.
- **AC3:** a memory pointing to `docs/DECISION-LOG.md` + the 2.0.0 consolidated state exists.

### S9 — Consolidate + push checkpoint  (dep: S1–S8)
- **AC1:** work committed as coherent conventional commits (branch-per-plan per decide-next auto-branch is expected).
- **AC2:** `make test` exits 0 AND `run-lint` distributed-scope exits 0 — evidence shown.
- **AC3:** final G-verify refute-judge PASS against S1–S8 ACs.
- **AC4:** `git push` succeeds; `origin/main` == local HEAD (Q-origin APPROVED).
- **AC5:** merged branches `fup-4-wiki-issues` / `fup-5-skill-count-ssot` deleted ONLY after explicit approval at G4.

## 3. Gates (STOP boundaries — execution never crosses a red gate)

| Gate | Covers | Binary pass criterion |
|------|--------|-----------------------|
| **G0 / G-spec** | this document | user approves the spec |
| **G1** | S1–S3 | 4 files gone · guard repointed · `make test-skill-count-ssot`=0 · `make test`=0 · README multi-agent-claim-free |
| **G2** | S4–S5 | gate scoped + positive/negative proven · `## [2.0.0]` top released section · no v2.0.0 tag |
| **G3** | S6–S8 | Decision-Log judge-PASS · handoffs pruned · MEMORY.md index consistent · lint-gate memory updated |
| **G4 / G-verify** | S9 | all-green + refute-judge PASS → push checkpoint → (explicit approval) branch cleanup |

## 4. Execution model

Gate-by-gate, autonomous between gates (R5). At each gate: STOP, surface evidence, wait for go.
Red gate halts the pipeline. Committing under this spec may auto-branch to `docs/<slug>-plan`
(decide-next auto-branch workflow) — intended. Push (G4) and branch-delete (AC5) are the only
outward/irreversible actions and are already scoped to explicit approval.

## 5. Out of scope (this session)

History-wipe / new-repo migration · release tag cut · plugin.json version bump · pruning
plans/specs/audit source docs · `spec-wiki-issues` (manifest todo — untouched, tracked for later).
