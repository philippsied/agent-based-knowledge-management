---
name: research-brief
description: >
  Construct or audit a structured research brief for the
  agentic-knowledge-management:autoresearch skill, enforcing twelve conventions
  (W1-W12) that prevent the most common failure modes of LLM-generated briefs:
  source anchoring on stale training data, unverified numbers,
  confirmation-biased objectives, binary stopping conditions,
  research-loop-as-decision-maker, bilingual evidence asymmetry, quantity-over-quality
  source quotas, missing scout phase, uniform cost ceilings, no output exemplar,
  direct wiki write without review gate, and unchallenged framing.
  Triggers on: "schreib Brief", "write a research brief", "Brief erstellen",
  "/brief <task-id>", "audit this brief", "validate brief",
  or when the autoresearch skill encounters a queue task whose brief is missing,
  is "_to brief_", or carries brief_version < 1.
allowed-tools: Read Write Edit Glob Grep Bash
---

# research-brief: Brief Construction & Audit

You produce structured research briefs that the `autoresearch` skill consumes. Briefs that pass this skill carry `brief_version: 1` in frontmatter. The `autoresearch` skill hard-gates on this field — a brief without it cannot start a research loop.

The skill has **two modes**: `construct` (write a new brief) and `audit` (validate an existing brief against the conventions and produce a diff with required edits).

---

## Mode selection

1. **Construct mode** — user says: "schreib Brief für R-YYYY-NNN", "/brief R-YYYY-NNN", "write a research brief for <topic>", "Brief erstellen für …".
2. **Audit mode** — user says: "audit brief R-YYYY-NNN", "validate this brief", "check brief", "audit the existing briefs", or you encounter a brief whose `brief_version` is absent / < 1.

If ambiguous: default to `construct` when the task has no brief, `audit` when the task has a brief but no `brief_version`.

---

## Inputs

- **Task ID** (preferred): `R-YYYY-NNN` matching a row in `wiki/meta/research-queue.md`. The skill reads program, priority, deps, title from the queue.
- **Free-form topic** (fallback): a short imperative phrase. The skill will offer to register a new queue row before writing the brief.
- **Existing brief path** (audit mode only): `wiki/meta/brief-R-YYYY-NNN-<slug>.md`.

If a task ID is given but the queue row's `brief` field is already a non-`_to brief_` wikilink, refuse to overwrite. Surface the existing brief path and offer to switch to audit mode.

---

## Convention enforcement — the W1-W12 set

The conventions are detailed in `references/conventions.md`. They map to twelve named failure modes. Six are **hard gates** (the skill refuses to finalize a brief that fails them). Six are **warnings** (the skill produces a brief but flags the failure and requires a one-line rationale).

| ID | Failure mode | Gate level |
|---|---|---|
| W1 | Source-instance anchoring (named firms / vendors from training data) | warn |
| W2 | Unverified numbers in brief frontmatter or topic statement | warn |
| W3 | Confirmation-biased objectives (no falsification question) | **hard** |
| W4 | Binary stopping condition (no must-have / best-effort split) | **hard** |
| W5 | Decision-page deliverable without "Pending Human" marker | **hard** |
| W6 | DACH topic without explicit DE-source quota | warn (hard if `program: DACH \| VERT \| GTM \| LEGAL \| VAL`) |
| W7 | Quantity-only source target ("≥N sources" with no tier breakdown) | warn |
| W8 | Missing Phase-0 scout step | **hard** |
| W9 | Cost ceiling without three-factor justification | warn |
| W10 | No exemplar reference for output structure | warn |
| W11 | Output path direct to `wiki/research/` (not `wiki/meta/draft-…/`) | **hard** |
| W12 | No meta-question check on the framing | **hard** |

The pre-flight checklist in `references/preflight-checklist.md` is the canonical evaluator.

---

## Construct workflow

### Phase 0 — Load context

1. Read `wiki/meta/research-queue.md`. Locate the task row. Extract `program`, `priority`, `title`, `depends_on`.
2. Read `references/conventions.md` and `references/brief-skeleton.md` into working memory.
3. If `program` is in {DACH, VERT, GTM, LEGAL, VAL}, set `requires_de_source_quota = true`.

### Phase 1 — Frame check (W12)

Ask one clarifying question to the user, even in Auto Mode:

> The current title is "<title>". Before I draft the brief, are these two assumptions right?
> 1. The framing question itself is well-posed (no broader question we should be answering instead).
> 2. The program assignment "<program>" is the right primary lane.
>
> If you spot a better framing or program, say so. Otherwise reply "go".

This is the one place where Auto Mode does **not** apply — the framing decision must be human-confirmed because it's the one decision the loop cannot recover from later.

### Phase 2 — Compose

Fill the brief skeleton in `references/brief-skeleton.md`. Every section is mandatory. Sections explicitly designed to enforce conventions:

- **Topic** (W2): no numerical claims unless cited inline.
- **Why now**: concrete unblock or hebel, not vague rationale.
- **Meta-question** (W12): one-paragraph self-challenge on the framing. Records what alternative framings were considered.
- **Objectives** (W3): each numbered objective ends with a *Falsification* sub-bullet — what would prove this thesis wrong, what would the contrary evidence look like.
- **Source classes, not instances** (W1): list source *categories* (e.g. "≥3 major DACH commercial law firms with published 2025–2026 AI-Act commentary"). Concrete names allowed only with `# example, verify currency` inline marker.
- **Source-tier quotas** (W7): use the tier vocabulary — Primary / Expert-secondary / Practitioner — with per-tier minimums.
- **DE-source quota** (W6): if `requires_de_source_quota = true`, include the phrase "≥30% German-language primary sources" (or higher).
- **Stopping condition — two tiers** (W4): explicit `Must-have:` block (gates completion) and `Best-effort:` block ("if not found, write an Evidence-Gap section, do not fabricate").
- **Phase-0 scout requirement** (W8): explicit instruction to spend the first hour verifying that the named sources still exist before deep research.
- **Cost ceiling — three-factor justification** (W9): for `MAX_DEPTH`, `MAX_SOURCES`, `MAX_TOKENS_SYNTHESIS`, name the three inputs: sub-topic count, citation intensity, time-sensitivity.
- **Output path** (W11): all outputs first land in `wiki/meta/draft-<task-id>/`. After human review, a separate skill (`agentic-knowledge-management:promote-draft`, future) moves them to their final paths.
- **Exemplar reference** (W10): link at least one existing high-quality wiki page as output-structure exemplar. For first-of-program briefs where no exemplar exists, mark explicitly: `Exemplar: TBD (this brief's output will become the program-{X} exemplar).`
- **Deliverables** (W5): any deliverable inside `wiki/decisions/` must be named `Decision-Brief-…` (not `Decision-…`) and the brief must instruct the loop to add a `Decision Pending Human Review` marker to the frontmatter.

### Phase 3 — Pre-flight

Run `references/preflight-checklist.md` over the draft. Each W1-W12 has a check. Any hard-gate failure stops the workflow and returns the brief to phase 2 with the specific gate violation. Warn-level failures surface in the final report.

### Phase 4 — Persist

1. Write the brief to `wiki/meta/brief-<task-id>-<slug>.md` with frontmatter:
   ```yaml
   ---
   type: meta
   title: "Brief — <task-id>: <Title>"
   created: <today>
   updated: <today>
   tags: [meta, autoresearch, brief, …]
   status: ready
   program: <program>
   brief_version: 1
   conventions_applied: W1,W2,W3,W4,W5,W6,W7,W8,W9,W10,W11,W12
   warnings: [<list of warn-level findings>]
   related:
     - "[[research-queue]]"
   ---
   ```
2. Update `wiki/meta/research-queue.md`:
   - Replace `_to brief_` (or stale brief link) with `[[brief-<task-id>-<slug>]]`.
   - Bump the row's `Updated` column to today.

### Phase 5 — Report

Return to the user:
- Brief path.
- Conventions passed and any warnings.
- Sections that needed the most human input during framing (signal for skill improvement).

---

## Audit workflow

1. Read the existing brief file.
2. Run `references/preflight-checklist.md`.
3. Produce a section-by-section report:
   - Section | Convention | Status (pass / warn / **fail**) | Suggested edit.
4. If any hard gate fails, mark the brief as `brief_version: 0` (or leave absent) — explicitly **not** version 1 — and offer to apply the suggested edits in-place.
5. If only warnings exist, offer to either fix the warnings or accept them with a one-line rationale appended to the brief's `warnings:` frontmatter list.
6. After successful audit + edits, set `brief_version: 1`, write `conventions_applied:` and `warnings:` frontmatter, update `research-queue.md` `Updated:` column.

---

## Hard-gate integration with `autoresearch`

The `autoresearch` skill's no-argument flow (see `skills/autoresearch/SKILL.md`) is updated to refuse any task whose brief lacks `brief_version: 1`. The error surface is:

> `Refusing to start R-YYYY-NNN: brief does not carry brief_version: 1.
> Run the agentic-knowledge-management:research-brief skill in audit mode first.`

The `autoresearch` skill change is a one-line frontmatter check, not a rewrite. See `references/conventions.md` § *Autoresearch integration* for the exact patch.

---

## Limits & non-goals

- This skill does **not** run web research. It only produces and validates the *brief* that another skill consumes.
- This skill does **not** make program-classification decisions. It reads the program from the queue and asks the user to confirm in Phase 1.
- This skill does **not** rewrite existing wiki content. It only writes to `wiki/meta/brief-…` and updates the queue row.
- Brief versioning is intentionally linear: `brief_version: 1` is the current schema. When conventions evolve, a new schema bumps to `2` and audit mode is responsible for migration.
