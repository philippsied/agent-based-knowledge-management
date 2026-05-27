# Brief Skeleton (brief_version: 1)

Drop-in template for a research brief. Replace `<placeholders>`. Every section is mandatory; deletion of a section causes a hard-gate failure in pre-flight.

```markdown
---
type: meta
title: "Brief — <task-id>: <Short Title>"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags:
  - meta
  - autoresearch
  - brief
  - <program-tag>
status: ready
program: <PROGRAM-CODE>
brief_version: 1
conventions_applied: W1,W2,W3,W4,W5,W6,W7,W8,W9,W10,W11,W12
warnings: []                # populated by pre-flight; empty list means clean run
related:
  - "[[research-queue]]"
  - "[[research/programs/<PROGRAM-CODE>]]"
---

# Brief — <task-id>: <Short Title>

Self-contained brief for the `autoresearch` loop. Conforms to W1-W12 (see `agent-based-knowledge-management/skills/research-brief/references/conventions.md`).

## Topic

<One paragraph. State the research question with date precision (e.g. "in May 2026"). No specific numerical claims unless cited. No proper-noun source lists.>

## Why now

<One paragraph. What gets unblocked by this research? Cite the downstream task or business question concretely. If priority is P0/P1, name the gate explicitly.>

## Meta-question (W12)

**Assumed framing**: <one sentence stating the question this brief answers>.

**Alternative framings considered**:
- <Alternative A — one line>
- <Alternative B — one line>

**Why the chosen framing won**: <one paragraph>.

**Tripwire**: <one sentence describing what evidence during the run would force a re-brief — e.g. "if scout phase finds the named alternative is materially larger, halt and re-brief">.

## Research objectives

Each objective ends with a *Falsification* sub-bullet (W3).

1. **<Objective 1 title>.** <One paragraph or bullet list of what to find.>
   - *Falsification:* <what evidence would prove this objective's premise wrong>.

2. **<Objective 2 title>.** <…>
   - *Falsification:* <…>.

<…3 to 10 objectives total, each with falsification.>

## Source classes (W1)

List source *categories*, not specific outlets. Concrete examples allowed only with `# example, verify currency` marker. Tier each class.

**Primary**:
- <Class 1 — e.g. "EU regulatory primary text and official AI-Office guidance, 2024-2026 dated">.
- <Class 2 — …>.

**Expert-secondary**:
- <Class 3 — e.g. "≥3 major DACH commercial law firms with published Art-4 commentary 2025-2026">. *Examples (verify currency): Noerr, Hengeler Mueller, CMS.*
- <Class 4 — …>.

**Practitioner**:
- <Class 5 — e.g. "engineering retrospectives from teams that shipped AI-literacy programs in 2025-2026">.

## Stopping condition (W4, W6, W7)

**Must-have** — completion gates; missing any of these is a real run failure:

- ≥<N> Primary sources, ≥<N> Expert-secondary, ≥<N> Practitioner.
- <DACH topics only: ≥30% German-language primary sources>.
- <Required artifact 1>.
- <Required artifact 2>.

**Best-effort** — attempt; if not findable, write an `Evidence Gap` section in the master synthesis page rather than fabricate:

- <Optional artifact 1>.
- <Optional artifact 2>.

## Phase 0 — Scout (W8)

**Strictly bounded**: ≤1 hour, ≤5k tokens, ≤8 source touches.

Goal: verify the source classes above still produce viable hits in May 2026.

Exit conditions:
- ≥50% of source classes return viable hits → proceed to deep synthesis.
- <50% → halt the loop, write `wiki/meta/draft-<task-id>/scout-report.md`, return control to the brief author for a re-brief.

## Deliverables (W11, W5)

All outputs land first in `wiki/meta/draft-<task-id>/`. A separate skill or manual step promotes to final path after human review.

- `wiki/meta/draft-<task-id>/research/Research-<Title>-2026.md` — master synthesis.
- `wiki/meta/draft-<task-id>/concepts/<Concept-1>.md` — <description>.
- `wiki/meta/draft-<task-id>/comparisons/<Comparison>.md` — <description>.
- `wiki/meta/draft-<task-id>/decisions/Decision-Brief-<Topic>.md` — tradeoff analysis with recommendation; the loop must add `decision_status: pending_human_review` to its frontmatter. **Not** a committed decision.
- `wiki/meta/draft-<task-id>/_templates/<Template>.md` — <description>.

## Exemplar (W10)

Use the following existing page as the output-structure exemplar for the master synthesis:

[[<existing-high-quality-page>]]

<OR, if no exemplar exists for this program yet:>

Exemplar: TBD (this brief's output will become the program-<PROGRAM-CODE> exemplar).

## Guardrails

- Cite every numerical claim or remove it.
- Distinguish first-party from third-party evidence inline.
- Bilingual policy per [[wiki/meta/termbase]]: German Eigennamen and Rechtsbegriffe preserved native, English gloss on first use.
- No scope drift into <list of adjacent topics that are out-of-scope here>.
- <Topic-specific guardrails>.

## Iteration / cost ceiling (W9)

- `MAX_DEPTH`: <N>
- `MAX_SOURCES`: <N>
- `MAX_TOKENS_SYNTHESIS`: ~<N>k

**Justification** (three factors):
- *Sub-topic count*: <1 sentence — how many independent threads>.
- *Citation intensity*: <1 sentence — claims-per-citation ratio expected>.
- *Time-sensitivity*: <1 sentence — fast-moving topic or stable>.

Pre-run hygiene: commit `wiki/hot.md` + `wiki/index.md`; freeze evals during run.
```
