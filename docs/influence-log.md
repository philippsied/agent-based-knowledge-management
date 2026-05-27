# Influence Log

Where ideas in this plugin came from outside the upstream repo. Each entry attributes a concept, pattern, or piece of code to its origin, so we can revisit, re-evaluate, or credit the source later. Append-only, newest entries at the top.

## How to add an entry

When adopting a pattern from another project, plugin, or article:

```markdown
## YYYY-MM-DD — <short title>
- Origin: <project / repo / paper> @ <ref or version>
- Adopted: <what specifically came over — file paths, ideas, conventions>
- Adapted: <what we changed and why — never copy verbatim if context differs>
- Skills / scripts touched: ...
- Why we found it useful: 1-2 sentences.
- Risks / caveats: anything to revisit.
```

---

## 2026-05-28 — Thino plugin redistribution — license unverified (TODO)

- Origin: Track A repo-cleanup pass (concurrent-grove plan); attempt to slim the bundled Obsidian plugin payload.
- Adopted: nothing yet — the planned step was to vendor only `data.json` and have `bin/setup-vault.sh` re-download `main.js` / `manifest.json` / `styles.css` from the Thino GitHub releases (analogous to the existing Excalidraw pattern).
- Adapted: deferred. The plugin self-identifies as "Closed source" in its `manifest.json`, and the sandbox in which this cleanup ran blocks both `gh api` (denied access to `~/.config/gh`) and `curl https://raw.githubusercontent.com/Quorafind/Obsidian-Thino/.../LICENSE`. License terms could therefore not be verified from this session. Until a human reviewer confirms the upstream LICENSE permits redistribution of the release binaries via setup-vault.sh, the Thino bundle remains vendored as-is (no deletion, no setup-vault.sh extension, no `.gitignore` block, no `ATTRIBUTION.md` disclaimer change).
- Skills / scripts touched: none (intentionally — the cleanup was aborted at the license-check gate).
- Why we found it useful: documenting the abort prevents the next contributor from repeating the same fetch attempts and rediscovering the sandbox limitation. The next step is a human-driven license check on `https://github.com/Quorafind/Obsidian-Thino` (LICENSE file or README) and, if compatible, executing the planned vendor-to-fetch swap.
- Risks / caveats: continuing to ship the Thino binaries without a verified license is a legal-distribution risk; do not deepen the dependency until cleared. Also: `data.json` is currently whitelisted in `.gitignore`, so user-state can drift into commits — review when the license question is settled.

## 2026-05-19 — Bilingual terminology policy (schema-level)

- Origin: user-supplied concept document (Philipp Sieder, 2026-05-19); cross-checked against general translation-memory and term-base literature.
- Adopted: four-artifact model (termbase, DNT classification, first-use gloss, dual-form retrieval); decision-authority split (autonomous / escalate / never); ingest/lint/audit touchpoint structure.
- Adapted: physical representation chosen as Markdown index page + `aliases:` frontmatter (no separate JSON termbase). Lint surfaces findings, never auto-fixes judgment calls. Out-of-scope items from the concept (multilingual mirroring, > 2 languages) explicitly excluded.
- Skills / scripts touched: `skills/wiki-ingest/SKILL.md`, `skills/wiki-lint/SKILL.md`, `skills/obsidian-markdown/references/frontmatter.md`, `scripts/lint-terminology.py`, `agents/wiki-ingest.md`.
- Why we found it useful: English-primary content drifts on DACH-native terms (AGB, IHK, Vorstand) when no policy enforces native preservation. Without dual-form retrieval, German queries silently miss pages they should hit.
- Risks / caveats: classification is a judgment call by definition — escalation paths must stay open; lint must not auto-rewrite. Termbase population is initial-seed only, will need a second pass once 50+ pages carry `dnt_class`.

## 2026-05-19 — Title-overlap lint (lightweight duplicate detection)

- Origin: PKM convention (MOC pattern, Nick Milo / LYT); standard Jaccard-on-filename-tokens used across many static site generators.
- Adopted: token-Jaccard on filenames as a cheap pre-filter for duplicate-page candidates.
- Adapted: extended to handle umlauts (`äöüß`) for German filenames; configurable threshold; integrates into the existing lint pipeline.
- Skills / scripts touched: `scripts/lint-title-overlap.py`, `tests/test_lint_title_overlap.py`.
- Why we found it useful: at < 500 pages, an embedding-based duplicate check (DragonScale Mechanism 3) is overkill. Filename-token overlap catches 80%+ of accidental duplicates at zero infrastructure cost.
- Risks / caveats: misses semantic duplicates with no shared tokens. Pair with manual MOC review or revisit Mechanism 3 once the vault grows beyond 500 pages.

## 2026-05-19 — Eval suite scaffold

- Origin: skill-creator skill (anthropic-skills marketplace); general LLM-as-judge eval pattern (Anthropic eval cookbook, OpenAI evals).
- Adopted: case-based directory layout, expected-output files, LLM-as-judge grading prompts, baseline-snapshot JSON.
- Adapted: scoped to wiki-ingest / wiki-lint / wiki-query (this plugin's three primary skills). Runner is bash-first, not pytest, to keep dependencies minimal.
- Skills / scripts touched: `evals/`.
- Why we found it useful: skill changes are easy to introduce silently — without baseline cases, regressions hide. Eval suite gives a deterministic check after every cherry-pick or refactor.
- Risks / caveats: cases capture today's expectations; they need periodic refresh as the skill evolves. Don't treat passing evals as proof of progress, only as a guardrail against regression.
