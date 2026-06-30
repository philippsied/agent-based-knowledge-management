---
type: meta
title: "Research Queue"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - meta
  - research
  - queue
  - autoresearch
status: evergreen
related:
  - "[[decisions/Research-Program-Codes]]"
  - "[[research/programs/_index]]"
---

# Research Queue

Central, prioritized backlog of research tasks for the `agentic-knowledge-management:autoresearch` skill. Single source of truth for **what to research next**.

> [!key-insight] Contract
> Invoking `/agentic-knowledge-management:autoresearch` **without arguments** reads this file, selects the top task by priority (then by `created` FIFO), flips its status to `in-progress`, runs the loop, and on completion flips it to `done` plus appends the deliverable links. Invoking *with* arguments bypasses this queue and runs an ad-hoc topic.

## Status legend

| Status | Meaning |
|---|---|
| `queued` | Ready to pick up. The default for new entries. |
| `in-progress` | Autoresearch loop currently running or paused mid-run. Only one task in this state at a time. |
| `done` | Loop completed and deliverables filed. Row stays here for ~30 days, then archived to `wiki/meta/research-queue-archive.md`. |
| `blocked` | Cannot start until a dependency resolves. `blocked_by:` field names the gating issue or task. |
| `dropped` | De-prioritized intentionally. Keep with a one-line `reason:`. |

## Priority legend

| Prio | Meaning |
|---|---|
| `P0` | Unblocks active work or a current gate. Must start this week. |
| `P1` | High leverage, no current blocker but compounds other work. Should start this month. |
| `P2` | Useful background research. Run when P0/P1 empty. |
| `P3` | Nice-to-have. Drop after one quarter if not picked up. |

## Program codes

Every task carries a `program:` field (see [[decisions/Research-Program-Codes]] for the seed list and rules). Adapt this table for your own program codes — the `lint-programs.py` check whitelists against the decision doc's `## Seed list` table.

| Code | Program | Anchor page |
|---|---|---|
| `EVAL` | Example: Evals, Judges, Skill Quality | [[research/programs/EVAL]] |
| `OPS` | Example: Internal tooling, vault structure, pipelines | [[research/programs/OPS]] |
| `GTM` | Example: Go-to-market, sales, marketing | [[research/programs/GTM]] |

---

## Active queue

| ID | Status | Prio | Program | Title | Brief | Deps | Created | Updated |
|---|---|---|---|---|---|---|---|---|
| R-YYYY-001 | `queued` | P1 | EVAL | Example task title | [[brief-R-YYYY-001-slug]] | — | YYYY-MM-DD | YYYY-MM-DD |

> [!note] Dep semantics
> `Deps` column lists **hard** prerequisites (`depends_on:`). The autoresearch skill refuses to start a task whose deps are not all `done`. Soft "informs" relationships go in the per-task brief's `related:` frontmatter and don't block.

## Done (rolling 30 days)

| ID | Status | Prio | Program | Title | Deliverables | Created | Finished |
|---|---|---|---|---|---|---|---|

## Conventions

- **IDs**: `R-YYYY-NNN` (year-padded, zero-padded). The `lint-deps.py` script parses this exact shape.
- **One row = one logical research task**. Decompose multi-question batches into separate rows so each can be `done` independently.
- **Brief column**: link to a `wiki/meta/brief-R-YYYY-NNN-slug.md` page using the [[research-brief]] template. Placeholder `_to brief_` is fine for early-stage rows.
- **Deps**: comma-separated `R-YYYY-NNN` IDs. Em-dash `—`, ASCII hyphen `-`, or empty cell all mean "no deps".
- **Lint integration**: `scripts/run-lint.py` runs `lint-deps.py` (DAG check) and `lint-programs.py` (program-code whitelist) automatically when this file exists. Severity = `error` if duplicates / missing deps / cycles / unknown codes are detected.
