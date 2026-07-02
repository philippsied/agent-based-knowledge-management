# Template — wiki/meta/OPEN-ISSUES.md

Owned by the `wiki-issues` skill (ADR-0005). Derived from the battle-tested living file in the
reference vault `ai-secondbrain` (`wiki/meta/OPEN-ISSUES.md`, 532 lines) and its `log.md`
resolution history. The skill scaffolds this when `wiki/meta/OPEN-ISSUES.md` is absent (init flow).

**Format = dual representation**: a machine-readable `stack:` array in the frontmatter (the ordered
work queue) mirrored by human `### I-YYYY-NNN` body sections. The validator
(`scripts/lint-open-issues.py`) keeps the two in parity and enforces the sort.

---

## Skeleton (what the skill scaffolds when OPEN-ISSUES.md is absent)

```markdown
---
type: meta
title: "Open Issues"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [meta, issues, tracking]
status: developing
related: ["[[log]]"]
# --- Stack --- ordered work queue; sort lint-enforced by lint-open-issues:
#   1. priority ASC (P0 first)   2. ready first (empty blocked_by)
#   3. inconclusive last within a priority group   4. pushed DESC tiebreaker
stack: []
#  - id: I-YYYY-NNN
#    priority: P1              # P0 | P1 | P2 | P3
#    section: <whitelisted>    # see the 12-section whitelist below
#    title: "<short imperative>"
#    pushed: YYYY-MM-DD
#    blocked_by: []            # [I-YYYY-MMM, ...]  non-empty => not ready
#    inconclusive_since: YYYY-MM-DD   # optional, paired with inconclusive_reason
#    inconclusive_reason: "<why last verify was inconclusive>"   # optional, paired
#    aggregated_from: [I-YYYY-AAA, I-YYYY-BBB]                    # optional, read-only
---

# Open Issues

The frontmatter `stack:` is the ordered work queue (priority ASC, ready-first,
inconclusive-last, LIFO tiebreaker). Resolved issues are removed entirely (stack item +
body section); history lives in [[log]].

- **push** — synthesize session todos/insights into the stack with fresh `I-YYYY-NNN` ids
  (year-resetting, never recycled), inserted in sorted position.
- **pop** — take the first ready item (empty `blocked_by`), verify against current repo
  state, then remove (resolved/fixed), patch (stale), or mark inconclusive. Exactly one
  issue per invocation.

## Priority legend
- **P0** — blocks active work or a published deadline. Drop everything.
- **P1** — high leverage; pick within the week.
- **P2** — background; pick when P0/P1 empty.
- **P3** — nice-to-have; archive if untouched after one quarter.

## Section whitelist (12 — reconciled, audit V-6)
`enforcement` · `lint` · `tooling` · `ci` · `hooks` · `docs` · `templates` · `skills` ·
`skill-plugin` · `vault-content` · `eval-observability` · `dragonscale`

Meaning:
- `enforcement` — hooks logic, Self-Mod-Guard, path-safety, pre-commit/CI enforcement.
- `lint` — lint scripts, run-lint integration, schema checks.
- `tooling` — helper scripts, tests, convention-vs-practice, manifest-sync.
- `ci` — CI workflows, gates, release automation.
- `hooks` — hook wiring/registration (`hooks/hooks.json`, SessionStart/PreToolUse).
- `docs` — PRDs, ADRs, specs, README, docs consistency.
- `templates` — placeholder wikilinks, template conventions.
- `skills` — skill definitions, counts, SSOT, trigger phrases.
- `skill-plugin` — plugin/marketplace manifests, plugin-branch, sub-agent reports, memory.
- `vault-content` — stale pages, dead links, duplicates, misplaced files, bilingual-DNT.
- `eval-observability` — trace logging, pinned regression, eval-gated CI, CoT judging.
- `dragonscale` — DragonScale mechanisms (fold, tiling, boundary, addresses).

Only file an issue outside this whitelist if it honestly fits none — then first propose a new
section to the user.

## <section>

### I-YYYY-NNN — <title>
**Priority:** P1 · **Pushed:** YYYY-MM-DD · **WO:** `<concrete file / location>`
**Blocked by:** [[#I-YYYY-MMM]]   <!-- omit when ready -->

<1–3 sentences: what, why it matters, concrete evidence/location. No vague issues.>
```

---

## New-issue snippet (push adds both halves)

Stack entry (sorted insert):
```yaml
  - id: I-YYYY-NNN
    priority: P2
    section: skills
    title: "<short>"
    pushed: YYYY-MM-DD
    blocked_by: []
```
Body section (under the matching `## <section>`):
```markdown
### I-YYYY-NNN — <title>
**Priority:** P2 · **Pushed:** YYYY-MM-DD · **WO:** `<file>`

<description>
```

## Resolution log snippet (pop → resolved; appended to top of `wiki/log.md`)

```markdown
## [YYYY-MM-DD] fix-issues | I-YYYY-NNN <short title>

- Disposition: resolved (removed from OPEN-ISSUES.md) | patched (stale) | inconclusive
- What: <what was done / found>
- OPEN-ISSUES now <N> items, lint green.
- Commit: `<sha>`
```

## Invariants (validator-enforced)
1. Every `stack:` id has exactly one `### I-YYYY-NNN` body section, and vice-versa (parity / drift guard).
2. Stack order obeys the 4-key sort invariant (priority ASC · ready-first · inconclusive-last · pushed DESC).
3. `blocked_by` forms a DAG (no cycles); an id is *ready* iff `blocked_by` is empty. Every `blocked_by` target exists in the stack.
4. `section` ∈ 12-whitelist. `priority` ∈ {P0,P1,P2,P3}. `id` matches `I-YYYY-NNN`, unique, never recycled.
5. `inconclusive_since` and `inconclusive_reason` appear as a pair (both or neither). `aggregated_from` ids are not still present in the stack.
6. Dates are `YYYY-MM-DD` strings; YAML lists use the `- item` form.
```
