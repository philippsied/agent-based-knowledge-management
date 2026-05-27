# Brief Conventions — W1 through W12

The twelve named failure modes a research brief must avoid. Derived from a session retrospective on 2026-05-27 covering four briefs produced without these conventions. Each entry: failure mode, why it breaks research, the rule that prevents it, the gate level, and the pre-flight check.

> All references to "the loop" mean the `agentic-knowledge-management:autoresearch` skill that consumes the brief.

---

## W1 — Source-instance anchoring

**Failure**: Brief lists specific firms, vendors, products, or person-names from the author's training data ("Noerr, Hengeler, CMS", "Doctolib, CGM, Craftnote", "Andreas Lutz, Britta Behrens"). The loop chases these names. Many will be acquired, renamed, pivoted, or no longer relevant.

**Why it breaks research**: The loop burns tokens on dead links or stale pages and treats the recovered evidence as authoritative because the brief named it.

**Rule**: List source *classes*, not instances. Concrete names allowed only with the inline marker `# example, verify currency`, signalling the loop must check viability before relying.

**Gate**: warn.

**Pre-flight check**: regex-scan source section for comma-separated proper-noun lists ≥3 entries; if found and no marker, fail.

---

## W2 — Unverified numbers in brief

**Failure**: Brief frontmatter or topic paragraph contains numerical claims pulled from the author's memory ("~1M Handwerk businesses", "~400-500k Heilberufe"). The loop reads these as context and anchors its synthesis to them.

**Why it breaks research**: Anchoring bias — the loop's "verified" numbers cluster around the brief's seed numbers even when better sources disagree.

**Rule**: No specific numerical claims in topic statement or frontmatter. Use ranges with explicit "TBD by research" tagging or move the claim to a citable footnote.

**Gate**: warn.

**Pre-flight check**: regex-scan topic + why-now sections for digit-bearing tokens; if found without citation or `TBD` tag, fail.

---

## W3 — Confirmation-biased objectives

**Failure**: Objectives like "Where are the AI white spaces?" or "What hook patterns work best?" presuppose a positive answer. The loop searches for evidence of the presupposition.

**Why it breaks research**: The loop's evidence collection is biased toward confirmation. Contrary evidence gets filtered out.

**Rule**: Every numbered objective must include a *Falsification* sub-bullet: "What would prove this objective's premise wrong? What contrary evidence should be specifically searched for?"

**Gate**: **hard**.

**Pre-flight check**: every numbered objective in the brief has a sub-bullet starting with `*Falsification:*` or `Counter-evidence:`.

---

## W4 — Binary stopping condition

**Failure**: Stopping condition reads "Stop when you have X, Y, Z". When the loop cannot find X, it either fabricates or terminates prematurely.

**Why it breaks research**: No fallback path for irreducible evidence gaps. The brief assumes all stated artifacts can be produced from public sources.

**Rule**: Stopping condition splits into two tiers.

- **Must-have**: artifacts the loop is contractually required to produce. Missing one of these is a real failure.
- **Best-effort**: artifacts the loop should attempt but, if not findable, document as an Evidence Gap section in the synthesis page rather than fabricate.

**Gate**: **hard**.

**Pre-flight check**: stopping-condition section contains both `Must-have:` and `Best-effort:` headers (or unambiguous equivalents).

---

## W5 — Decision-page deliverable

**Failure**: Brief lists `wiki/decisions/<Topic>-Pick.md` as a deliverable. A research loop produces evidence syntheses, not committed decisions. Naming the output a "Decision" gives it false authority.

**Why it breaks research**: Conflates research output (tradeoff analysis with recommendation) with decision record (committed choice with rationale). The latter requires human deliberation that the loop cannot substitute.

**Rule**: Any deliverable in `wiki/decisions/` must be named `Decision-Brief-…` (not `Decision-…`). The brief must instruct the loop to add the frontmatter line `decision_status: pending_human_review` to any such page.

**Gate**: **hard**.

**Pre-flight check**: every deliverable path matching `wiki/decisions/…` either starts with `Decision-Brief-` or has explicit `decision_status: pending_human_review` instruction in the brief body.

---

## W6 — Bilingual evidence asymmetry

**Failure**: Brief mentions a bilingual policy but does not quantify the DE-source requirement. The loop's search defaults to English-dominant indices, under-representing the DE primary evidence the topic actually requires.

**Why it breaks research**: For DACH-flavoured topics, the resulting synthesis is a DACH topic discussed through English-language secondary sources. The wiki ends up with a distorted picture.

**Rule**: If `program` is in {DACH, VERT, GTM, LEGAL, VAL}, the brief must include an explicit DE-source quota: "≥30% of primary sources must be German-language". The quota can be raised per topic but cannot be lower than 30% without an explicit override line.

**Gate**: warn by default; **hard** if `program` is in the listed set.

**Pre-flight check**: if `program` in {DACH, VERT, GTM, LEGAL, VAL}, stopping condition contains explicit DE-source percentage; otherwise pass.

---

## W7 — Quantity-only source target

**Failure**: Stopping condition says "≥10 sources" or "≥15 sources". Ten low-quality blog posts pass this gate; three datable primary sources fail it.

**Why it breaks research**: Optimises for source count instead of source weight. The synthesis becomes a meta-analysis of secondary discussion rather than primary evidence.

**Rule**: Source targets must be tiered. Use the canonical tier vocabulary:

- **Primary** — statutory text, official agency guidance, first-party engineering posts by the system's maintainers, peer-reviewed papers.
- **Expert-secondary** — named law firms, named consultancies, named industry analysts, ranked academic surveys.
- **Practitioner** — production engineering blogs, conference talks, named operator post-mortems.

Stopping condition specifies minimums per tier. Example: "≥3 Primary, ≥3 Expert-secondary, ≥2 Practitioner".

**Gate**: warn.

**Pre-flight check**: stopping condition contains all three tier names with numeric minimums.

---

## W8 — Missing Phase-0 scout

**Failure**: Brief launches directly into full synthesis depth (3 iterations × 20+ sources). When the brief's named sources are partially dead (W1), the budget is burned before the dead-source rate is even known.

**Why it breaks research**: No early-exit mechanism. The loop discovers source rot only after committing the synthesis budget.

**Rule**: Brief must include a **Phase-0 scout** step: a strictly time-bounded (≤1 hour, ≤5k tokens) verification pass that checks the source-classes listed in the brief still produce viable hits. If the scout reports <50% viable, the loop returns control to the brief-author for a re-brief, not deep synthesis.

**Gate**: **hard**.

**Pre-flight check**: brief contains a section explicitly named `Phase 0 — Scout` or `Scout phase` with token/time bound.

---

## W9 — Uniform cost ceilings

**Failure**: All briefs share the same `MAX_DEPTH: 3 / MAX_SOURCES: 20 / MAX_TOKENS: 40k` ceiling regardless of topic. LinkedIn algorithm refresh and EU AI Act literacy have wildly different evidence shapes; the same ceiling either over-spends one and under-funds the other.

**Why it breaks research**: Mis-allocated budget. The output is either bloated (for narrow topics) or under-supported (for citation-heavy topics).

**Rule**: Cost ceilings must be justified by three factors:

- **Sub-topic count** — how many independent threads must be covered.
- **Citation intensity** — does each claim need 1 source, 3 sources, or a statutory quote.
- **Time-sensitivity** — is the topic in flux (LinkedIn) or stable (foundational concept).

The justification is two sentences below the ceiling block. Without it, the ceiling is arbitrary.

**Gate**: warn.

**Pre-flight check**: Iteration / cost ceiling section contains a sub-paragraph naming all three factors.

---

## W10 — No exemplar reference

**Failure**: Brief lists "1 master synthesis page" as a deliverable but doesn't reference any existing high-quality page as a structural exemplar. The loop reinvents the page structure from scratch each time.

**Why it breaks research**: Output structure varies across briefs. Vault-level navigation suffers; readers cannot rely on consistent page shape.

**Rule**: Brief must link at least one existing wiki page as the output-structure exemplar. For the first brief in a program where no exemplar exists, the brief must declare `Exemplar: TBD (this brief's output will become the program-<X> exemplar)`.

**Gate**: warn.

**Pre-flight check**: brief contains a line matching `Exemplar:` followed by a wikilink or the explicit TBD declaration.

---

## W11 — Direct wiki write

**Failure**: Brief instructs the loop to write outputs directly into `wiki/research/…`, `wiki/concepts/…`, `wiki/decisions/…`. If the loop hallucinates, the hallucination lands in the permanent corpus and contaminates future `wiki-query` answers.

**Why it breaks research**: No human-review gate. The wiki becomes a write-once, never-curated artifact store.

**Rule**: All loop outputs first land in `wiki/meta/draft-<task-id>/<original-path>`. A separate skill (`agentic-knowledge-management:promote-draft`, planned) handles human review and move to final path. Until that skill exists, the user must manually verify drafts before moving them.

**Gate**: **hard**.

**Pre-flight check**: every Deliverable path in the brief begins with `wiki/meta/draft-<task-id>/`.

---

## W12 — No meta-question check

**Failure**: Brief accepts the queue title's framing without challenge. "Handwerk vs Heilberufe vertical scoring" assumes those are the right two candidates; "LinkedIn DACH algorithm refresh" assumes LinkedIn is the right channel; "Sub-agent coordination patterns" assumes a coordination problem is the bottleneck.

**Why it breaks research**: The loop produces a high-quality answer to the wrong question. Cost is the same as a useful run; output value is near zero.

**Rule**: Brief includes a `Meta-question` section that:

1. States the framing assumption explicitly ("This brief assumes X is the right question").
2. Names 1-2 alternative framings that were considered.
3. States the reason the chosen framing won (one paragraph).
4. Names a tripwire that would invalidate the framing during the run.

**Gate**: **hard**. The Phase-1 frame-check in `SKILL.md` is the human-in-the-loop step that produces this section.

**Pre-flight check**: brief contains a `## Meta-question` (or `### Meta-question`) section with all four sub-elements.

---

## Autoresearch integration

The `autoresearch` skill must refuse to start a task whose brief lacks `brief_version: 1`. The minimum change to `skills/autoresearch/SKILL.md` is a single check inside the no-argument flow, before the loop begins:

```
Before flipping status to in-progress:
1. Read the brief file referenced by the queue row.
2. Parse frontmatter. If `brief_version` is absent or != 1:
   Print:
     Refusing to start R-YYYY-NNN: brief does not carry brief_version: 1.
     Run the agentic-knowledge-management:research-brief skill in audit mode first.
   Exit.
3. Otherwise proceed.
```

This is a defensive check, not a rewrite of the skill. Tracked separately (see this branch's commits when ready).

---

## Versioning

`brief_version: 1` is the schema described above. When conventions evolve and existing briefs need migration:

- Bump to `brief_version: 2`.
- Audit mode is responsible for migrating `1 → 2`.
- Old briefs remain runnable until the schema migration deadline expires (set per bump).
- The `autoresearch` skill accepts the highest supported version of the day.

Convention additions that are purely additive (e.g. adding W13) and don't break existing briefs may stay at the current version; only breaking changes trigger a bump.
