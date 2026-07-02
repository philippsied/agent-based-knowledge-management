# Template — wiki/meta/OPEN-ISSUES.md

Starting point for the `wiki-issues` skill (ADR-0005), derived from the battle-tested
living file in the reference vault `ai-secondbrain` (`wiki/meta/OPEN-ISSUES.md`, 532 lines)
and its `log.md` resolution history. On FUP-4 build this relocates to
`skills/wiki-issues/references/open-issues-template.md`.

**Format = dual representation**: a machine-readable `stack:` array in the frontmatter (the
ordered queue) mirrored by human `### I-YYYY-NNN` body sections. A validator
(`lint-open-issues`) keeps the two in parity and enforces the sort.

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
stack:
  - id: I-YYYY-NNN
    priority: P1              # P0 | P1 | P2 | P3
    section: <whitelisted>    # see whitelist below
    title: "<short imperative>"
    pushed: YYYY-MM-DD
    blocked_by: []            # [I-YYYY-MMM, ...]  non-empty ⇒ not ready
    # inconclusive_reason: "<why last verify was inconclusive>"   # optional
    # aggregated_from: [I-YYYY-AAA, I-YYYY-BBB]                    # optional
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

## Section whitelist
`enforcement` · `lint` · `tooling` · `docs` · `skills` · `hooks` · `ci` · `dragonscale`

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

## Resolution log snippet (pop → resolved; appended to top of `log.md`)

```markdown
## [YYYY-MM-DD] fix-issues | I-YYYY-NNN <short title>

- Disposition: resolved (removed from OPEN-ISSUES.md) | patched (stale) | inconclusive
- What: <what was done / found>
- OPEN-ISSUES now <N> items, lint green.
- Commit: `<sha>`
```

## Invariants (validator-enforced)
1. Every `stack:` id has exactly one `### I-YYYY-NNN` body section, and vice-versa (parity / drift guard).
2. Stack order obeys the 4-key sort invariant.
3. `blocked_by` forms a DAG (no cycles); an id is *ready* iff `blocked_by` is empty.
4. `section` ∈ whitelist. `priority` ∈ {P0,P1,P2,P3}. `id` matches `I-YYYY-NNN`, unique, never recycled.
5. Dates are `YYYY-MM-DD` strings; YAML lists use the `- item` form.
