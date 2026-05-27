---
name: autoresearch
description: >
  Autonomous iterative research loop. Takes a topic, runs web searches, fetches sources,
  synthesizes findings, and files everything into the wiki as structured pages.
  Based on Karpathy's autoresearch pattern: program.md configures objectives and constraints,
  the loop runs until depth is reached, output goes directly into the knowledge base.
  Triggers on: "/autoresearch", "autoresearch", "research [topic]", "deep dive into [topic]",
  "investigate [topic]", "find everything about [topic]", "research and file",
  "go research", "build a wiki on".
allowed-tools: Read Write Edit Glob Grep WebFetch WebSearch Bash
---

# autoresearch: Autonomous Research Loop

You are a research agent. You take a topic, run iterative web searches, synthesize findings, and file everything into the wiki. The user gets wiki pages, not a chat response.

This is based on Karpathy's autoresearch pattern: a configurable program defines your objectives. You run the loop until depth is reached. Output goes into the knowledge base.

---

## Before Starting

Read `references/program.md` to load the research objectives and constraints. This file is user-configurable. It defines what sources to prefer, how to score confidence, and any domain-specific constraints.

---

## Topic Selection

Four paths to a topic, evaluated in order:

### A. Explicit topic or task ID (always respected)

When the user passes an argument to the skill (`/autoresearch <argument>`, `autoresearch <argument>`, or `research <argument>`):

- **Argument matches `R-YYYY-NNN`** (a research-queue task ID): route through section B's task handling for that specific task. Skip the no-args concurrency / ready-set / boundary computation, but apply the **brief-presence**, **brief-version**, and **dependency** gates from section B before starting the loop. On gate failure, refuse with the canonical message — do not fall through to free-text mode.
- **Otherwise** (free-text topic): treat the argument as an ad-hoc topic. Set `QUEUE_MODE=0`, skip sections B-D, use the text verbatim as the loop input. Output goes to the ad-hoc draft path (see *Filing Results — Output path by mode*).

### B. Research-queue driven (default when no topic given, opt-in via queue file)

When `/autoresearch` is invoked WITHOUT a topic AND the vault has a research queue, default to picking the highest-priority ready task from `wiki/meta/research-queue.md`. This is the **deliberate-agenda** mode: tasks are pre-prioritized, briefed, and dependency-ordered by the user.

Feature detection (shell):

```bash
if [ -f wiki/meta/research-queue.md ] && [ -x scripts/lint/lint-deps.py ]; then
  QUEUE_MODE=1
else
  QUEUE_MODE=0
fi
```

When `QUEUE_MODE=1`:

1. **Concurrency check**: refuse to start if any row already has `status: in-progress`. Surface:
   ```
   Refusing to start: R-YYYY-NNN is still in-progress (started YYYY-MM-DD).
   Mark it done/queued first, or pass an explicit topic argument.
   ```
2. **Validate the DAG**: run `python3 scripts/lint/lint-deps.py`. If exit code != 0 (cycles, missing deps, or duplicate IDs), refuse to start and surface the lint output. The queue must be clean.
3. **Compute ready set**: run `python3 scripts/lint/lint-deps.py --ready`. This returns IDs of tasks where `status: queued` AND all `depends_on:` are `done`, in priority order (P0 first, then FIFO by `created`).
4. **Helper failure handling**: if the helper exits non-zero, emits no output, or returns an empty list, set `QUEUE_MODE=0` and fall through to section C below. Do NOT improvise a topic.
5. **Brief presence enforcement**: read the queue table to resolve the top ID. If its `Brief` cell is `_to brief_` or empty:
   - **No-args invocation** (queue-driven selection): skip to the next ready ID. If no ready task has a brief, fall through to C.
   - **Explicit task-ID invocation** (section A routing here): refuse and surface:
     ```
     Refusing to start R-YYYY-NNN: brief is missing or _to brief_.
     Run the agentic-knowledge-management:research-brief skill in construct mode to produce a brief first.
     ```
6. **Brief-version enforcement** (W11 gate, see `references/program.md` and the research-brief skill): read the brief file referenced by the queue row. Parse its frontmatter. If `brief_version` is absent or `!= 1`, surface:
   ```
   Refusing to start R-YYYY-NNN: brief does not carry brief_version: 1.
   Run the agentic-knowledge-management:research-brief skill in audit mode to validate and bring it to current schema.
   ```
   - **No-args invocation**: skip to the next ready ID after surfacing the message (do not silently skip — the user must see which task was unrunnable).
   - **Explicit task-ID invocation**: refuse and stop. Do not fall through to free-text mode.
7. **Present to user**:
   ```
   Selected R-YYYY-NNN [P0/EVAL]: <title>
   Brief: <brief link>
   Program home: [[research/programs/<CODE>]]
   Depends on: <list or —>
   Proceed? (y / type a topic to override / 'next' for the next ready task / 'cancel')
   ```
8. **On confirm**:
   - Edit the queue row: flip `status: queued` → `status: in-progress`, set `started: <today>`, bump `updated:`.
   - Use the brief content as the topic input for the research loop. The brief already encodes objectives, sources, stopping condition, and deliverables — respect them verbatim.
9. **On 'next'**: move to the next ready ID, repeat from step 5.
10. **On topic override**: set `QUEUE_MODE=0` for this run, do not touch the queue, use the typed text as topic.
11. **On 'cancel'**: ask via section D (user-chosen).

**During the loop**: never edit `wiki/meta/research-queue.md`'s row schema or other rows. Only the active row's `status`, `started`, `finished`, `updated`, and `deliverables` may be touched. **Never edit eval files** (mirrors the [[Self-Improvement-Loop]] principle: the agenda is the review loop).

**On loop completion (success)**:
- Flip the row's `status: in-progress` → `status: done`.
- Set `finished: <today>`, bump `updated:`.
- Append `deliverables:` links pointing at every page created in this run (synthesis, sources, concepts, entities).
- Update `wiki/log.md` per the normal *After Filing* section, plus a `Queue-task: R-YYYY-NNN` line.

**On loop failure or abort**:
- Flip the row back to `status: queued`. Leave `started:` populated so retry latency is visible.
- Log the failure mode to `wiki/log.md` under `Queue-task: R-YYYY-NNN — failed (<reason>)`.

### C. Boundary-first selection (agenda control, opt-in)
**This is agenda control, not pure memory.** DragonScale Memory.md Mechanism 4 labels this mechanism as such because it shapes which direction the research agent moves next. Users who want a strict memory-layer subset should omit this path entirely.

When `/autoresearch` is invoked WITHOUT a topic AND the vault has adopted DragonScale, default to surfacing the frontier of the vault as a set of candidate topics the user can accept, override, or decline.

Feature detection (shell):

```bash
if [ -x ./scripts/boundary-score.py ] && [ -d ./.vault-meta ] && command -v python3 >/dev/null 2>&1; then
  BOUNDARY_MODE=1
else
  BOUNDARY_MODE=0
fi
```

When `BOUNDARY_MODE=1` AND `QUEUE_MODE=0`:

1. Run `./scripts/boundary-score.py --json --top 5`. Returns the top 5 frontier pages by `boundary_score = (out_degree - in_degree) * recency_weight`.
2. **Helper failure handling**: if the helper exits non-zero, emits invalid JSON, or returns an empty `results` array, set `BOUNDARY_MODE=0` and fall through to section D below. Do NOT prompt the user with an empty candidate list, and do NOT improvise a topic.
3. Present the candidate list to the user: "Your top frontier pages are: [list]. Research which one? (1-5, or type a topic to override, or say 'cancel' to be asked normally.)"
4. If the user picks 1-5, use the selected page's title as the topic.
5. If the user types free text, use that.
6. If the user cancels or does not choose, fall through to D.

The boundary score is a heuristic, not an objective measure of what SHOULD be researched. The user always has the option to type a free-text topic to override the surfaced candidates.

**Link-resolution semantics**: the boundary helper uses **filename-stem wikilink resolution only**. `[[Foo]]` is counted as an edge to `Foo.md` anywhere in the vault. Aliases declared via frontmatter `aliases:` are **not** parsed. Folder-qualified links (e.g. `[[notes/Foo]]`) are resolved by stem only. This matches default Obsidian behavior for unique filenames but does not implement full Obsidian alias resolution.

### D. User-chosen (final fallback)
When `QUEUE_MODE=0` AND `BOUNDARY_MODE=0`, or the user declined every queue/frontier pick, ask: "What topic should I research?"

---

## Research Loop

```
Input: topic (from Topic Selection, above)

Round 1. Broad search
1. Decompose topic into 3-5 distinct search angles
2. For each angle: run 2-3 WebSearch queries
3. For top 2-3 results per angle: WebFetch the page
4. Extract from each: key claims, entities, concepts, open questions

Round 2. Gap fill
5. Identify what's missing or contradicted from Round 1
6. Run targeted searches for each gap (max 5 queries)
7. Fetch top results for each gap

Round 3. Synthesis check (optional, if gaps remain)
8. If major contradictions or missing pieces still exist: one more targeted pass
9. Otherwise: proceed to filing

Max rounds: 3 (as set in program.md). Stop when depth is reached or max rounds hit.
```

---

## Filing Results

### Output path by mode

The base output path differs by invocation mode:

- **`QUEUE_MODE=1`** (task picked from research-queue via no-args or explicit task ID): outputs first land under `wiki/meta/draft-<task-id>/` per the brief's W11 instruction. Sub-paths mirror the final structure: `wiki/meta/draft-<task-id>/sources/`, `wiki/meta/draft-<task-id>/concepts/`, `wiki/meta/draft-<task-id>/entities/`, `wiki/meta/draft-<task-id>/questions/`. A separate skill (`agentic-knowledge-management:promote-draft`, planned) or manual review promotes drafts to final paths after a human pass.
- **`QUEUE_MODE=0` ad-hoc topic** (free-text argument, boundary-mode pick, or user-chosen): outputs first land under `wiki/meta/draft-adhoc-<slug>-<YYYY-MM-DD-HHMM>/`. No brief = short default cap: `MAX_DEPTH: 1`, `MAX_SOURCES: 5`, overriding `references/program.md` defaults. Before starting the loop, surface one line: *"Ad-hoc mode uses a short default cap. For deeper runs, draft a brief via the research-brief skill and add it to wiki/meta/research-queue.md."*

**Path substitution rule**: wherever the section below says "create `wiki/sources/Foo.md`", "create `wiki/concepts/Bar.md`", etc., prepend the active mode's base prefix to the path. The page templates (frontmatter, body structure) are identical across modes — only the path differs.

### Pages to create

After research is complete, create these pages (under the active base prefix):

**wiki/sources/**. One page per major reference found
- Use source frontmatter (type, source_type, author, date_published, url, confidence, key_claims)
- Body: summary of the source, what it contributes to the topic

**wiki/concepts/**. One page per significant concept extracted
- Only create a page if the concept is substantive enough to stand alone
- Check the index first: update existing concept pages rather than creating duplicates

**wiki/entities/**. One page per significant person, org, or product identified
- Check the index first: update existing entity pages

**wiki/questions/**. One synthesis page titled "Research: [Topic]"
- This is the master synthesis. Everything comes together here.
- Sections: Overview, Key Findings, Entities, Concepts, Contradictions, Open Questions, Sources
- Full frontmatter with related links to all pages created in this session

---

## Synthesis Page Structure

```markdown
---
type: synthesis
title: "Research: [Topic]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - research
  - [topic-tag]
status: developing
related:
  - "[[Every page created in this session]]"
sources:
  - "[[wiki/sources/Source 1]]"
  - "[[wiki/sources/Source 2]]"
---

# Research: [Topic]

## Overview
[2-3 sentence summary of what was found]

## Key Findings
- Finding 1 (Source: [[Source Page]])
- Finding 2 (Source: [[Source Page]])
- ...

## Key Entities
- [[Entity Name]]: role/significance

## Key Concepts
- [[Concept Name]]: one-line definition

## Contradictions
- [[Source A]] says X. [[Source B]] says Y. [Brief note on which is more credible and why]

## Open Questions
- [Question that research didn't fully answer]
- [Gap that needs more sources]

## Sources
- [[Source 1]]: author, date
- [[Source 2]]: author, date
```

---

## After Filing

1. Update `wiki/index.md` **only when outputs landed in their final paths** (not under any `wiki/meta/draft-*/` prefix). Draft outputs are indexed at promotion time, not before — keeping the master catalog free of unreviewed pages
2. Append to `wiki/log.md` (at the TOP):
   ```
   ## [YYYY-MM-DD] autoresearch | [Topic]
   - Rounds: N
   - Sources found: N
   - Pages created: [[Page 1]], [[Page 2]], ...
   - Synthesis: [[Research: Topic]]
   - Key finding: [one sentence]
   - Queue-task: R-YYYY-NNN     # only if QUEUE_MODE=1
   ```
3. Update `wiki/hot.md` with the research summary
4. **If `QUEUE_MODE=1`**: update the row in `wiki/meta/research-queue.md`:
   - Flip `status: in-progress` → `status: done`.
   - Set `finished: <today>`, bump `updated:`.
   - Append `deliverables:` links pointing at every page created in this run.
   - Re-run `python3 scripts/lint/lint-deps.py` to confirm the DAG is still clean and to print the new ready set.

---

## Report to User

After filing everything:

```
Research complete: [Topic]

Rounds: N | Searches: N | Pages created: N

Created:
  wiki/questions/Research: [Topic].md (synthesis)
  wiki/sources/[Source 1].md
  wiki/concepts/[Concept 1].md
  wiki/entities/[Entity 1].md

Key findings:
- [Finding 1]
- [Finding 2]
- [Finding 3]

Open questions filed: N
```

---

## Constraints

Follow the limits in `references/program.md`:
- Max rounds (default: 3)
- Max pages per session (default: 15)
- Confidence scoring rules
- Source preference rules

If a constraint conflicts with completeness, respect the constraint and note what was left out in the Open Questions section.
