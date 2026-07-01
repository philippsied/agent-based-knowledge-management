---
artifact: spec
slug: wiki-issues
status: draft
manifest: docs/manifests/dragonscale-agentic-wiki-followups.json
depends_on: [adr-0005, adr-0001]
---

# Spec — wiki-issues skill (OPEN-ISSUES stack owner)

> WIE does a single `wiki-issues` skill own the `wiki/meta/OPEN-ISSUES.md` lifecycle (push + pop) deterministically? Realizes [ADR-0005](../adr/0005-skill-home-open-issues-commands.md); executes FUP-4 under [ADR-0001](../adr/0001-delete-commands-skills-only.md).
> Reference shape: the battle-tested `ai-secondbrain` vault (`wiki/meta/OPEN-ISSUES.md` + `log.md`). Template: [docs/templates/open-issues.md](../templates/open-issues.md).

## 1. Goal & Context  ‹What/Why → ADR-0005›

Give the `wiki/meta/OPEN-ISSUES.md` issue stack one owning skill. It absorbs the two substantive commands ADR-0001 leaves homeless — `fix-issues` (pop) and `handoff` (push) — as sub-flows, and owns the stack format, its validator, and its creation. In the plugin the file does **not yet exist**; the skill initializes it from the template. The design is not invented here — it ports a shape already proven in `ai-secondbrain`.

## 2. Interfaces / Contracts  ‹With-what›

### 2.1 Data model — dual representation
- **Machine queue** — frontmatter `stack:` list; each entry: `id` (`I-YYYY-NNN`), `priority` (`P0..P3`), `section` (whitelist), `title`, `pushed` (`YYYY-MM-DD`), `blocked_by` (`[ids]`); optional `inconclusive_reason`, `aggregated_from`.
- **Human detail** — body `## <section>` → `### I-YYYY-NNN — <title>` with a `**Priority:** · **Pushed:** · **WO:**` line, prose, optional `**Blocked by:**`.
- **Parity invariant** — every stack `id` ⇔ exactly one body section.

### 2.2 Operations & triggers
- **init** — if `OPEN-ISSUES.md` absent, scaffold from the template.
- **push** (triggers: "handoff", "synthesize issues") — turn session todos/insights into issues: allocate fresh `I-YYYY-NNN` (year-resetting, never recycled), insert in sorted position, add the body section.
- **pop** (triggers: "fix issues", "work the top issue") — select the first **ready** (empty `blocked_by`) top-of-stack item, verify it against current repo state, then dispose. **Exactly one issue per invocation.**

### 2.3 Validator contract — `lint-open-issues`
Port the reference `lint-open-issues.py`: checks **schema** (fields/types/id format), **parity** (stack ⇔ body), **cycles** (`blocked_by` DAG), and **sort** (4-key invariant). Exposes `--json`; wired into `scripts/run-lint.py` so `totals.error` gates CI. Ships with self-test cases.

## 3. Behavior  ‹How›

### Happy path — push
Collect candidate items → dedupe against existing stack (optionally `aggregated_from`) → allocate ids → insert each into stack at its sorted position and append its body section → run validator → report new count.

### Happy path — pop
Read stack → pick first item with empty `blocked_by` (top of the sorted stack) → verify against repo state → one disposition:
- **resolved/fixed** → hard-delete stack item + body section; append a `log.md` entry (`Resolved (removed from OPEN-ISSUES.md): I-YYYY-NNN … + "now N items, lint green"`).
- **patched** (stale) → correct the issue in place (e.g. line numbers, counts), keep it.
- **inconclusive** → set `inconclusive_reason`; it now sorts last within its priority.

### Edge cases
- **Format drift / legacy file** → a **format-version guard** detects hybrid-vs-flat before any write; refuses (does not blindly overwrite) on mismatch. *(Reference failure I-2026-041: a stale flat command nearly corrupted the hybrid file.)*
- **Empty stack** / **all items blocked** → pop reports "nothing ready"; no mutation.
- **id year-rollover** → first push of a new year starts `I-<year>-001`; ids never recycled across deletions.

### Error handling
- Schema-invalid file → refuse and surface the `lint-open-issues` diagnostics; do not write.
- Missing `OPEN-ISSUES.md` on pop → init from template, then report empty.

## 4. Chosen approach  ‹How›
Deterministic core in colocated scripts (sort, validate, id-allocate) — the LLM only synthesizes issue prose and judges verification. Reuse the DragonScale pattern: a counter-under-lock allocator for ids (see [ADR-0004](../adr/0004-canonical-address-counter-start.md) semantics), matching the plugin's "deterministic enforcement over prose" stance. Skill layout per [ADR-0002](../adr/0002-colocate-scripts-under-skill.md): `skills/wiki-issues/SKILL.md` + `skills/wiki-issues/scripts/lint-open-issues.py` + `skills/wiki-issues/references/open-issues-template.md`.

## 5. Acceptance criteria (binary, testable)  ‹When-done›
- **AC1** `init` produces a schema-valid `OPEN-ISSUES.md` from the template.
- **AC2** `push` allocates a unique, year-correct `I-YYYY-NNN`, inserts at the correct sorted position, stack ⇔ body in parity.
- **AC3** `pop` selects the correct first-ready item; each disposition leaves the file lint-green.
- **AC4** a resolved issue is hard-deleted from stack **and** body and logged in `log.md` with the `now N items, lint green` line.
- **AC5** `lint-open-issues` catches each of: schema break, stack↔body drift, `blocked_by` cycle, mis-sort; wired into `run-lint`; CI goes red on `error`.
- **AC6** the format-version guard refuses to write a non-hybrid/legacy file.
- **AC7** the 7 command files are removed and docs referencing `/commands` updated, with a coverage matrix proving in-skill parity (ADR-0001 gate).

## 6. Test design  ‹When-done›
Fixtures (close reference gap I-2026-043): ready-first pop · priority-sorted insert · drift guard (stack ≠ body) · inconclusive path · id year-rollover · empty / all-blocked stack · format-guard on a flat file · resolved→log-entry. Plus the validator self-test (schema/parity/cycles/sort), mirrored from the reference's 9-case suite.

## 7. Security / Privacy  ‹With-what›
Writes only into `wiki/meta/` (+ `log.md`) — inside the path-safety hook whitelist. Deterministic, no network, no secrets in issue bodies. `.raw/` untouched.

## 8. Rollout / Migration / Backout  ‹When›
Gated on **ADR-0005 accepted**. Order: build `skills/wiki-issues/` → port `fix-issues` + `handoff` with the coverage matrix → init `OPEN-ISSUES.md` → port + wire `lint-open-issues` → add fixtures → **only then** delete the 7 command files. Backout: keep the commands until parity is proven (ADR-0001 requires proof-before-delete). Skill count moves 14 → 15 (update SSOT, FUP-5).

### Checklist (before status: approved)
- [ ] Data model matches the reference + template
- [ ] `lint-open-issues` ported, wired into `run-lint`, self-tested
- [ ] Every AC has a fixture
- [ ] Format-version guard implemented
- [ ] Coverage matrix vs the old commands (ADR-0001)
- [ ] Gate: ADR-0005 accepted
