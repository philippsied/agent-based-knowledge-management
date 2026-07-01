---
artifact: adr
number: 0005
status: proposed     # proposed | accepted | superseded-by:NNNN
manifest: docs/manifests/dragonscale-agentic-wiki-followups.json
---

# ADR-0005 — Skill-home for the OPEN-ISSUES stack commands (fix-issues, handoff)

> **Anchors (7 W):** Why (context + consequences) · What (the decision) · With-what (alternatives)

## Status
proposed   <!-- accepted (YYYY-MM-DD) | superseded by ADR-NNNN -->

## Context  ‹Why›

ADR-0001 (accepted) decides "commands are deleted, skills-only." Of the 7 command files, 5 are thin skill wrappers (trivially deletable), but 2 are substantive and have **no skill home yet**:

- `commands/wiki/fix-issues.md` (~211 lines): pops the next ready, highest-priority entry from the `wiki/meta/OPEN-ISSUES.md` stack (priority ASC, ready-first, LIFO) and works it.
- `commands/wiki/handoff.md` (~126 lines): synthesizes session todos + insights into `wiki/meta/OPEN-ISSUES.md` as new stack entries with fresh IDs.

ADR-0001's follow-up work left this open: *"Skill-Heimat für `handoff` (Fold vs. neu); `fix-issues`→`wiki-lint` fix-forward."* — the `fix-issues` home was leaned toward `wiki-lint`, and `handoff` was undecided. This ADR resolves both, because FUP-4 (executing the deletion) cannot proceed until every substantive command has a proven in-skill home.

Key facts:
- Both commands are **producer/consumer over one stateful artifact**: `wiki/meta/OPEN-ISSUES.md` (a stack with an ID scheme, priority, ready-flag, LIFO ordering). `handoff` pushes; `fix-issues` pops-and-works.
- That artifact **does not yet exist on disk** (verified 2026-07-01) — it currently has no owner.
- `wiki-lint` is stateless analysis (it *surfaces* issues); `save` is session-capture (it files notes). Neither owns a stateful stack.

## Decision  ‹What›

Introduce a new dedicated skill **`wiki-issues`** that owns the full `wiki/meta/OPEN-ISSUES.md` stack lifecycle — both the `handoff`-style push (synthesize session items into stack entries) and the `fix-issues`-style pop-and-work — plus the stack's format (ID scheme, priority, ready-flag, ordering) and its creation. `fix-issues` and `handoff` fold into this one skill as its two sub-flows; the command files are then deleted under ADR-0001.

## Alternatives  ‹With-what›

- **ADR-0001's split: `fix-issues` → `wiki-lint`, `handoff` → `save`** — rejected: it splits the push and pop of a single stateful artifact across two skills, so the stack's ID/format invariants must be duplicated and kept in sync in two places (drift risk). It also overloads stateless `wiki-lint` with stateful workflow.
- **Fold both into `wiki-lint`** — rejected: `wiki-lint` is deterministic, read-mostly analysis; embedding a stateful, mutating issue-stack workflow bloats its responsibility and its `allowed-tools` surface.
- **Keep the two commands as-is** — rejected: contradicts the accepted ADR-0001 (skills-only).

## Consequences  ‹Why: outcomes›

**Good:**
- One owner for the `OPEN-ISSUES.md` stack → its ID scheme, priority, and LIFO invariants live in a single place.
- Gives the currently-absent stack a clear home.
- Unblocks FUP-4: with a named home, the substantive commands can be migrated and the wrappers deleted.

**Bad / cost:**
- One more skill to maintain (14 → 15) and to document — compounds the skill-count SSOT drift already tracked as FUP-5.
- Migration effort: port ~337 lines of German command logic into the new skill with parity (ADR-0001 requires proven in-skill coverage before deletion).

**Follow-up work:**
- **FUP-4** (execute ADR-0001): create `skills/wiki-issues/`, migrate `fix-issues` + `handoff` with a coverage matrix, delete the 7 command files, update docs referencing `/commands`. *(Deferred — code/doc edits out of scope for this ADR round.)*
- Initialize `wiki/meta/OPEN-ISSUES.md` (the stack the skill operates on) — currently absent.
- Update the skill count 14 → 15 wherever counted (ties to FUP-5).

## Design constraints (from ai-secondbrain reference)

The battle-tested `wiki/meta/OPEN-ISSUES.md` in the reference vault `ai-secondbrain` (a 532-line living file plus its `log.md` resolution history) fixes the shape `wiki-issues` must implement. Binding constraints — detail in [SPEC-wiki-issues](../specs/SPEC-wiki-issues.md), starting template in [docs/templates/open-issues.md](../templates/open-issues.md):

- **Dual representation + drift guard** — machine `stack:` YAML (id, priority, section, title, pushed, blocked_by) in frontmatter, mirrored by human `### I-YYYY-NNN` body sections; a validator keeps them in parity.
- **Deterministic sort, lint-enforced (not LLM)** — priority ASC · ready-first (empty `blocked_by`) · inconclusive-last · `pushed` DESC. Port the reference's `lint-open-issues.py` (schema/parity/cycles/sort) into `run-lint`.
- **ID `I-YYYY-NNN`, year-resetting, never recycled** — fresh monotonic id on push (counter-under-lock, like DragonScale `c-NNNNNN`).
- **`blocked_by` DAG → ready = empty** — pop takes the first ready item only.
- **One issue per pop** — verify → exactly one of: resolved (hard-delete), patched (stale), inconclusive (sorts last).
- **Hard-delete on resolve** — history goes to `log.md` (`Resolved (removed from OPEN-ISSUES.md): I-YYYY-NNN … "now N items, lint green"`). The file stays a live queue, not a graveyard.
- **`WO:` (where) on every issue** — grounds it in a concrete file/location (evidence-first).
- **Section whitelist** — controlled vocabulary, tuned to plugin domains.
- **Format-version guard before any write** — reference failure I-2026-041: a stale flat command nearly corrupted the hybrid file.
- **Test fixtures** for ready-first pop, priority-sorted insert, drift guard, inconclusive path — reference gap I-2026-043.

---
### Checklist
- [x] Context names the real forces  ‹Why›
- [x] Decision clear in 1 sentence  ‹What›
- [x] ≥1 serious alternative + reason for rejection  ‹With-what›
- [x] Consequences both good AND bad
- [x] Status set (proposed — owner ratifies → accepted; immutable, change = new ADR)
