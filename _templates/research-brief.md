---
type: meta
title: "Brief — R-YYYY-NNN: <one-line topic>"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - meta
  - autoresearch
  - brief
status: ready
program: <CODE>
related:
  - "[[research-queue]]"
  - "[[research/programs/<CODE>]]"
---

# Brief — R-YYYY-NNN: <one-line topic>

## Topic

**One bold sentence stating the deliverable.** Follow with 2–3 sentences of scope: what the research must cover and what is explicitly out of scope.

## Why this is worth researching

Explain the current blocker, opportunity, or decision this brief unlocks. Cite the upstream pain point. Reference current vault state if relevant (link to `wiki/meta/OPEN-ISSUES.md`, the hot cache, or a competing brief).

If this is `P0`, explain the dated event that forces the deadline.

## Research objectives (in priority order)

1. **Objective 1 (one bold lead-in).** One paragraph elaborating: what to look for, what counts as a complete answer, what to compare.
2. **Objective 2.** …
3. **Objective 3.** …

Keep the list to 5–10 numbered items. Each item must be answerable from sources, not from speculation.

## Sources to hit

- **Our own**: paths to relevant files in this vault or sibling repos.
- **Primary literature**: papers, official docs, RFCs.
- **Community / practitioners**: blogs, forum threads, repo conventions.
- **Adversarial sources**: counter-evidence, failed implementations, criticism.

List specific URLs or canonical names. Avoid generic "search the web" pointers.

## Stopping condition

Stop when you have:

- A **decision or comparison matrix** with named alternatives × evaluated dimensions.
- **N concrete artefacts** (paths, configs, examples) — list them.
- **Open questions surfaced** that should become follow-up briefs (link slot for new queue rows).

Specify the artefacts precisely: file paths, schema shapes, function signatures, table dimensions. The autoresearch loop terminates when these are all produced.

## Deliverable layout

The autoresearch skill files its findings as:

- `wiki/research/<topic-slug>/Findings.md` — main synthesis (entry point).
- `wiki/research/<topic-slug>/<sub-topic>.md` — one page per major sub-finding.
- `wiki/sources/<slug>.md` — one page per cited source.
- `wiki/decisions/<Decision-Slug>.md` — only if this brief produces a binding decision.

If this brief should land elsewhere (e.g. directly under `wiki/<program>/`), specify the override path here.

## Pre-registered scope

Items the loop **must not** drift into without filing a new brief:

- <Anti-scope item 1>
- <Anti-scope item 2>

This guards against scope creep mid-run.
