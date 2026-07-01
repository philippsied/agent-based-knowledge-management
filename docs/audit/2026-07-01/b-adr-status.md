---
agent: B
checks: "#2,#3"
generated: 2026-07-01
base_commit: 0a9916d
branch: docs/cmd-script-consolidation-plan
---

# Agent B — ADR coherence (#2) & status parity (#3)

Scope: cross-checks #2 (ADR-0005 vs ADR-0001 silent-contradiction) and #3 (status parity
tracker ⇄ manifest ⇄ ADR). Read-only. Every finding cites file:line + actual quote (R2).

---

## #2 — ADR-0005 vs ADR-0001 (silent-contradiction check)

**Verdict: OK — NOT a silent contradiction.** ADR-0005 explicitly names ADR-0001's earlier
`fix-issues → wiki-lint` lean, quotes the original German follow-up text, states that it
resolves the open question, and rejects the ADR-0001 approach as a *named* alternative with a
concrete reason. This is an explicit supersession of the lean, not a silent divergence.

**Evidence:**

1. Context section names + quotes the earlier lean verbatim, and frames this ADR as its
   resolution —
   `docs/adr/0005-skill-home-open-issues-commands.md:22`:
   > `ADR-0001's follow-up work left this open: *"Skill-Heimat für `handoff` (Fold vs. neu); `fix-issues`→`wiki-lint` fix-forward."* — the `fix-issues` home was leaned toward `wiki-lint`, and `handoff` was undecided. This ADR resolves both, because FUP-4 (executing the deletion) cannot proceed until every substantive command has a proven in-skill home.`

2. The ADR-0001 approach is carried as an explicit REJECTED alternative with rationale (drift
   risk + overloading stateless lint) —
   `docs/adr/0005-skill-home-open-issues-commands.md:35`:
   > `**ADR-0001's split: `fix-issues` → `wiki-lint`, `handoff` → `save`** — rejected: it splits the push and pop of a single stateful artifact across two skills, so the stack's ID/format invariants must be duplicated and kept in sync in two places (drift risk). It also overloads stateless `wiki-lint` with stateful workflow.`

3. A second, adjacent alternative closes the "fold into lint" door directly —
   `docs/adr/0005-skill-home-open-issues-commands.md:36`:
   > `**Fold both into `wiki-lint`** — rejected: `wiki-lint` is deterministic, read-mostly analysis; embedding a stateful, mutating issue-stack workflow bloats its responsibility and its `allowed-tools` surface.`

4. ADR-0005 also affirms (not contradicts) ADR-0001's governing decision — it treats
   skills-only as binding and rejects "keep the commands" for contradicting it —
   `docs/adr/0005-skill-home-open-issues-commands.md:17` and `:37`:
   > `:17  ADR-0001 (accepted) decides "commands are deleted, skills-only." …`
   > `:37  **Keep the two commands as-is** — rejected: contradicts the accepted ADR-0001 (skills-only).`

Cross-reference to the source lean in ADR-0001's own consequences confirms ADR-0005 quoted it
faithfully — `docs/adr/0001-delete-commands-skills-only.md:30` (`## Konsequenzen`) is the
section that carried the `fix-issues`→`wiki-lint` / `handoff` follow-up now resolved here.

**Class: `ok`** · **Severity: low** (informational — no defect; the acknowledgment is present
and explicit).

---

## #3 — Status parity across tracker ⇄ manifest ⇄ ADR

**Verdict: PASS with one documented representational nuance.** Both decisions are consistent
across all three surfaces. IMPORTANT NUANCE: the manifest (JSON `status` + its generated MD
mirror) does NOT store the ADR status token (`accepted`/`proposed`); it stores decide-next
**lifecycle states** (`verified`/`todo`). The manifest's own `verify` field defines the
mapping, so parity is *semantic*, not token-literal. No mismatch — but flagged so a naive
token-grep of the manifest is not misread as a contradiction.

### FUP-1 / ADR-0004 = accepted

- **ADR file — accepted (token-literal, two places):**
  - `docs/adr/0004-canonical-address-counter-start.md:4`:
    > `status: accepted     # proposed | accepted | superseded-by:NNNN`
  - `docs/adr/0004-canonical-address-counter-start.md:13`:
    > `accepted (2026-07-01)   <!-- superseded by ADR-NNNN if revisited -->`
- **Tracker — accepted (three places):**
  - `docs/tasks/dragonscale-agentic-wiki-followups.md:11`:
    > `… FUP-1 → [ADR-0004](…) (**accepted**), …`
  - `docs/tasks/dragonscale-agentic-wiki-followups.md:33`:
    > `| **FUP-1** | … → **[ADR-0004](…)** (accepted: canonical = `1`) | … | ADR-0004 ratified by owner (status → accepted). |`
- **Manifest JSON — lifecycle `verified`, maps to accepted:**
  - `docs/manifests/dragonscale-agentic-wiki-followups.json:11`: `"status": "verified"` (entry `adr-0004`)
  - `docs/manifests/dragonscale-agentic-wiki-followups.json:19`: `"verify": "Owner ratifies status: accepted"` → `verified` == owner-ratified == ADR `accepted`.
- **Manifest MD — mirrors `verified`:**
  - `docs/manifests/dragonscale-agentic-wiki-followups.md:7`: `| adr-0004 | adr | verified | — | yes | — |`

  Parity result: **consistent** — ADR token `accepted` ⇔ tracker `accepted` ⇔ manifest lifecycle `verified` (= ratified).

### FUP-3 / ADR-0005 = proposed

- **ADR file — proposed (token-literal, two places):**
  - `docs/adr/0005-skill-home-open-issues-commands.md:4`:
    > `status: proposed     # proposed | accepted | superseded-by:NNNN`
  - `docs/adr/0005-skill-home-open-issues-commands.md:13`:
    > `proposed   <!-- accepted (YYYY-MM-DD) | superseded by ADR-NNNN -->`
- **Tracker — proposed (two places):**
  - `docs/tasks/dragonscale-agentic-wiki-followups.md:11`:
    > `… FUP-3 → [ADR-0005](…) (proposed), …`
  - `docs/tasks/dragonscale-agentic-wiki-followups.md:35`:
    > `| **FUP-3** | … → **[ADR-0005](…)** (proposed: new `wiki-issues` skill) | … | ADR-0005 ratified by owner (status → accepted). |`
- **Manifest JSON — lifecycle `todo`, maps to proposed:**
  - `docs/manifests/dragonscale-agentic-wiki-followups.json:43`: `"status": "todo"` (entry `adr-0005`)
  - `docs/manifests/dragonscale-agentic-wiki-followups.json:51`: `"verify": "Owner ratifies status: accepted"` → not yet verified == ADR still `proposed`.
- **Manifest MD — mirrors `todo`:**
  - `docs/manifests/dragonscale-agentic-wiki-followups.md:9`: `| adr-0005 | adr | todo | — | yes | — |`

  Parity result: **consistent** — ADR token `proposed` ⇔ tracker `proposed` ⇔ manifest lifecycle `todo` (= not-yet-ratified).

**Class: `flag-only`** (representational nuance worth noting for future auto-checks — the
manifest deliberately uses lifecycle vocab, not ADR-status vocab; a literal cross-surface
token-grep would false-positive) · **Severity: low**. No status-value mismatch found; do NOT
raise as high-sev.

---

## S-b (carry-forward seed) — EN/DE heading split

**Verdict: confirmed consistency observation (not a blocker).** The pre-existing bundle ADR
(0001) uses German section headings; the this-session ADRs (0004, 0005) use English. Structure
and anchor glyphs (‹…›) are identical; only the language differs.

- `docs/adr/0001-delete-commands-skills-only.md:15,22,26,30`:
  > `## Kontext  ‹Warum›` · `## Entscheidung  ‹Was›` · `## Alternativen  ‹Womit›` · `## Konsequenzen  ‹Warum: Folgen›`
- `docs/adr/0004-canonical-address-counter-start.md:15,31,35,40`:
  > `## Context  ‹Why›` · `## Decision  ‹What›` · `## Alternatives  ‹With-what›` · `## Consequences  ‹Why: outcomes›`
- `docs/adr/0005-skill-home-open-issues-commands.md:15,29,33,39`:
  > `## Context  ‹Why›` · `## Decision  ‹What›` · `## Alternatives  ‹With-what›` · `## Consequences  ‹Why: outcomes›`

(Note: per CLAUDE.md, English is the standard for Claude config/technical artifacts, so 0004/0005
are the on-convention pair and 0001 is the outlier — but this is not this session's scope to fix.)

**Class: `value`** · **Severity: low**.

---

## Roll-up

#2 clean (ADR-0005 explicitly supersedes ADR-0001's `fix-issues→wiki-lint` lean at :22 and :35 — no silent contradiction); #3 status values consistent across all three surfaces for both FUP-1/ADR-0004 (accepted) and FUP-3/ADR-0005 (proposed), with one low-sev representational nuance (manifest uses lifecycle `verified`/`todo`, not ADR tokens); S-b EN/DE heading split confirmed (value/low).
