# Pre-flight Checklist (brief_version: 1)

Convention compliance checklist. Run after Phase 2 (Compose), before Phase 4 (Persist). One entry per W1-W12. Fail-on-hard, warn-on-warn.

For each check: locate the relevant section in the brief, apply the test, record `pass` / `warn` / **`fail`** in the audit table. Any **`fail`** stops the workflow and returns the brief to Phase 2 with the specific gate violation identified.

---

## W1 — Source-instance anchoring (warn)

**Test**: Scan `## Source classes` section. For every named proper-noun (e.g. a company, person, product), verify either:

- The named entity appears in a `*Examples (verify currency): …*` sub-line, OR
- The named entity carries an inline `# example, verify currency` marker.

**Fail condition**: comma-separated proper-noun list of length ≥3 appears without the marker.

**Action on warn**: append to `warnings:` frontmatter: `W1: <count> unmarked proper-noun list(s)`.

---

## W2 — Unverified numbers (warn)

**Test**: Scan `## Topic` and `## Why now` sections for digit-bearing tokens (e.g. `1M`, `400k`, `~30%`, `5 years`). Each must satisfy one of:

- Followed by inline citation `[source: …]`.
- Tagged with `(TBD by research)`.
- Time/date reference (e.g. "May 2026", "Q3 2026") — allowed.

**Fail condition**: any unmarked numeric claim about magnitude, market size, or count.

**Action on warn**: append to `warnings:` frontmatter: `W2: <count> uncited number(s)`.

---

## W3 — Confirmation-biased objectives (**hard**)

**Test**: For each numbered objective under `## Research objectives`, verify a sub-bullet exists starting with `*Falsification:*` or `Counter-evidence:`.

**Fail condition**: any numbered objective without a falsification sub-bullet.

**Action on fail**: halt workflow. Return to Phase 2 with the missing-falsification list. Example message:

> Objective 3 (`<title>`) has no falsification sub-bullet. Add one that names the contrary evidence the loop must search for.

---

## W4 — Binary stopping condition (**hard**)

**Test**: `## Stopping condition` section contains both:

- A `Must-have` header (or unambiguous equivalent) with concrete artifacts.
- A `Best-effort` header (or unambiguous equivalent) with an explicit "if not found, write Evidence Gap section, do not fabricate" instruction.

**Fail condition**: only one tier present, or no fabrication-prevention instruction in Best-effort.

**Action on fail**: halt workflow. Provide the W4 rule and skeleton diff.

---

## W5 — Decision-page deliverable (**hard**)

**Test**: Scan `## Deliverables` for any path under `wiki/decisions/` or `wiki/meta/draft-*/decisions/`. Each must satisfy:

- Filename starts with `Decision-Brief-` (not `Decision-`), AND
- Brief body contains an instruction such as: "Add `decision_status: pending_human_review` to its frontmatter."

**Fail condition**: a decision-path deliverable that fails either condition.

**Action on fail**: halt workflow. Suggest rename + marker.

---

## W6 — Bilingual evidence asymmetry (conditional **hard**)

**Test**: If `program` frontmatter is in {DACH, VERT, GTM, LEGAL, VAL}, scan `## Stopping condition` for an explicit German-language source percentage of ≥30%.

**Fail condition**: program in the listed set, no quota line.

**Action on fail (program in set)**: halt workflow.

**Action on warn (program not in set)**: append `W6: no DE-source quota (program does not require)`. Optional but record.

---

## W7 — Quantity-only source target (warn)

**Test**: `## Stopping condition` `Must-have` block lists explicit per-tier minimums for at least the three canonical tiers: Primary, Expert-secondary, Practitioner.

**Fail condition**: stopping condition uses only `≥N sources` aggregate counts.

**Action on warn**: append `W7: stopping condition uses aggregate source counts only` and suggest the tier rewrite.

---

## W8 — Missing Phase-0 scout (**hard**)

**Test**: Brief contains a section explicitly named `## Phase 0 — Scout` (or `## Scout phase`) with:

- Time/token bound stated (e.g. ≤1 hour, ≤5k tokens, ≤8 source touches).
- Exit conditions stated (proceed / halt-and-re-brief threshold).

**Fail condition**: section missing or bounds/exit not stated.

**Action on fail**: halt workflow.

---

## W9 — Uniform cost ceilings (warn)

**Test**: `## Iteration / cost ceiling` section contains a "Justification (three factors)" sub-paragraph naming:

- Sub-topic count.
- Citation intensity.
- Time-sensitivity.

**Fail condition**: any of the three named factors missing.

**Action on warn**: append `W9: cost ceiling missing factor(s): <list>`.

---

## W10 — No exemplar reference (warn)

**Test**: Brief contains a line matching `^Exemplar:` followed by either:

- A `[[wikilink]]` to an existing wiki page, OR
- The explicit `TBD (this brief's output will become the program-<X> exemplar)` declaration.

**Fail condition**: no `Exemplar:` line.

**Action on warn**: append `W10: no exemplar reference`.

---

## W11 — Direct wiki write (**hard**)

**Test**: For every entry under `## Deliverables`, the path begins with `wiki/meta/draft-<task-id>/`.

**Fail condition**: any deliverable path written outside `wiki/meta/draft-<task-id>/`.

**Action on fail**: halt workflow. Suggest path rewrite.

---

## W12 — No meta-question check (**hard**)

**Test**: Brief contains a `## Meta-question` (or `### Meta-question`) section with all four sub-elements:

1. `**Assumed framing**:` line.
2. `**Alternative framings considered**:` block with ≥1 alternative listed.
3. `**Why the chosen framing won**:` paragraph.
4. `**Tripwire**:` line.

**Fail condition**: section missing OR any of the four sub-elements absent.

**Action on fail**: halt workflow. Note that the Phase-1 frame-check in `SKILL.md` is the human-in-the-loop step that populates these — if the brief is being audited rather than constructed, surface the gap and ask the user to confirm framing.

---

## Audit table template

After running all twelve checks, produce this table for the user:

| Convention | Section | Status | Note |
|---|---|---|---|
| W1 | Source classes | pass / warn / **fail** | <one-line evidence> |
| W2 | Topic, Why now | pass / warn / **fail** | <…> |
| W3 | Research objectives | pass / **fail** | <…> |
| W4 | Stopping condition | pass / **fail** | <…> |
| W5 | Deliverables | pass / **fail** | <…> |
| W6 | Stopping condition | pass / warn / **fail** | <conditional on program> |
| W7 | Stopping condition | pass / warn | <…> |
| W8 | Phase 0 — Scout | pass / **fail** | <…> |
| W9 | Iteration / cost ceiling | pass / warn | <…> |
| W10 | Exemplar line | pass / warn | <…> |
| W11 | Deliverables paths | pass / **fail** | <…> |
| W12 | Meta-question | pass / **fail** | <…> |

If any row is **fail**, the brief does not receive `brief_version: 1` and cannot run via `autoresearch`. Construct-mode returns to Phase 2; audit-mode offers in-place edits.

If all hard gates are `pass` and any `warn` rows exist, the brief receives `brief_version: 1` with the warnings listed in the `warnings:` frontmatter array. The user is offered the choice to either resolve warnings or accept them with a one-line rationale appended.
