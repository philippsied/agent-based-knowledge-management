---
type: meta
title: "Open Issues"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - meta
  - issues
  - tracking
status: developing

# --- Stack ---
# Ordered work queue. Sort invariant (and lint-enforced order):
#   1. priority ASC (P0 first)
#   2. ready first (blocked_by == [] before blocked_by != [])
#   3. inconclusive last within a priority group
#   4. LIFO (pushed DESC) as final tiebreaker
# /wiki:fix-issues pops the first item with empty blocked_by.
# /wiki:handoff inserts new items in sorted position with fresh I-YYYY-NNN ids.
stack:
  - id: I-2026-001
    priority: P0
    section: enforcement
    title: "<ready P0 example — replace>"
    pushed: YYYY-MM-DD
    blocked_by: []

  - id: I-2026-002
    priority: P1
    section: eval-observability
    title: "<ready P1 example — replace>"
    pushed: YYYY-MM-DD
    blocked_by: []

  - id: I-2026-003
    priority: P2
    section: lint
    title: "<aggregated example — replace>"
    pushed: YYYY-MM-DD
    blocked_by: []
    aggregated_from: [I-2026-008, I-2026-009]

  - id: I-2026-004
    priority: P2
    section: vault-content
    title: "<inconclusive example — replace>"
    pushed: YYYY-MM-DD
    blocked_by: []
    inconclusive_since: YYYY-MM-DD
    inconclusive_reason: "<why verification was not conclusive>"

  - id: I-2026-005
    priority: P2
    section: tooling
    title: "<blocked example — replace>"
    pushed: YYYY-MM-DD
    blocked_by: [I-2026-001]
---

# Open Issues

Known issues across the vault, tooling, and plugin layer. The frontmatter `stack:` is the
ordered work queue (priority ASC, ready-first, inconclusive-last, LIFO tiebreaker). Resolved
issues are removed entirely (stack item + body section); history lives in [[log]].

- `/wiki:handoff` synthesizes new issues into the stack with fresh `I-YYYY-NNN` ids.
- `/wiki:fix-issues` pops the first ready item (empty `blocked_by`), verifies it, then removes it (resolved/fixed), patches it (stale), or marks it inconclusive. Exactly one issue per invocation.

## Priority legend
- **P0** — Blocks active work or a published deadline. Drop everything.
- **P1** — High leverage; should be picked within the week.
- **P2** — Background; pick when P0/P1 empty.
- **P3** — Nice-to-have; archive if untouched after one quarter.

## Section whitelist (12 — reconciled, audit V-6)
`enforcement` · `lint` · `tooling` · `ci` · `hooks` · `docs` · `templates` · `skills` ·
`skill-plugin` · `vault-content` · `eval-observability` · `dragonscale`
<!-- Canonical copy: skills/wiki-issues/references/open-issues-template.md. Body `## <section>` blocks below are illustrative — use any whitelist section. -->


Each issue is a `### I-YYYY-NNN — Title` subsection under its `## <section>` block, whose id
matches a `stack[].id` exactly. The first body line is the meta line
`**Priority:** … · **Pushed:** … · **WO:** …`. The truth lives in the frontmatter; body
`**Blocked by:**` / `**Note:**` lines are reflections. Body order is cosmetic — work order
lives in the stack.

## enforcement

<!-- Hooks, Self-Modification-Guard, path-safety, pre-commit/CI gaps. -->

### I-2026-001 — <ready P0 example — replace>
**Priority:** P0 · **Pushed:** YYYY-MM-DD · **WO:** `<path[:line]>`

<One sentence symptom or risk.>

## lint

<!-- Lint scripts, run-lint integration, missing checks, false positives, schema checks. -->

### I-2026-003 — <aggregated example — replace>
**Priority:** P2 · **Pushed:** YYYY-MM-DD · **WO:** `<path>`

<One sentence. Aggregated from I-2026-008 + I-2026-009 via /wiki:fix-issues step 7.>

## vault-content

<!-- Stale pages, broken wikilinks, duplicate concepts, misplaced files, bilingual DNT. -->

### I-2026-004 — <inconclusive example — replace>
**Priority:** P2 · **Pushed:** YYYY-MM-DD · **WO:** `<path>`
**Note:** inconclusive since YYYY-MM-DD — <why verification was not conclusive>

<One sentence symptom or risk.>

## tooling

<!-- Helper scripts, tests, convention-vs-practice, manifest sync, missing automation. -->

### I-2026-005 — <blocked example — replace>
**Priority:** P2 · **Pushed:** YYYY-MM-DD · **WO:** `<path>`
**Blocked by:** [[#I-2026-001]]

<One sentence. Cannot start until I-2026-001 resolves.>

## templates

<!-- Placeholder wikilinks leaking, template conventions, missing templates. -->

## skill-plugin

<!-- Skill definitions, plugin branch, trigger phrases, sub-agent reports, memory persistence. -->

## eval-observability

<!-- Trace logging, pinned regression baseline, eval-gated CI, CoT judging, spec-kit constitution. -->

### I-2026-002 — <ready P1 example — replace>
**Priority:** P1 · **Pushed:** YYYY-MM-DD · **WO:** `<path>`

<One sentence symptom or risk.>
