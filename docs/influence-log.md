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

## 2026-05-28 — Thino plugin redistribution — resolved via v1 (MIT) downgrade

- Origin: Track A repo-cleanup pass (concurrent-grove plan); slim the bundled Obsidian plugin payload by removing vendored binaries. Initial run aborted in sandbox (network restrictions prevented gh/curl license-check on upstream LICENSE); resolution requested by user pointed at the `v1` branch.
- Adopted: `bin/setup-vault.sh` downloads `main.js` + `styles.css` from the upstream `1.9.7` release; only the (267 B) `manifest.json` ships in-repo (rewritten to advertise v1.9.7 / "Obsidian Memos"). `.obsidian/plugins/thino/{main.js,styles.css,data.json}` removed from git; `.gitignore` extended to cover the downloaded artifacts.
- Adapted: shipped Thino **v1.9.7 ("Obsidian Memos")** instead of current upstream `main` (v3.0.12). Justification: the `v1` branch carries an explicit `MIT License` (Copyright 2022 Boninall) and 42 tagged releases with binary assets; `main` declares "Closed source" in `manifest.json` and has no LICENSE file. Both versions share plugin id `obsidian-memos`, so a Thino Insider (Pkmer) license-holder can upgrade in-place without state migration.
- Skills / scripts touched: `bin/setup-vault.sh` (new Thino fetch block, ~10 lines), `.gitignore` (Thino binary block, dropped `data.json` whitelist), `ATTRIBUTION.md` (entry renamed "Thino" → "Obsidian Memos (Thino v1)", license column added), `.obsidian/plugins/thino/manifest.json` (v3.0.4 → v1.9.7 metadata).
- Why we found it useful: removes a 2.6 MB redistribution that we could not legally justify (manifest declared "Closed source"). Users keep a quick-capture experience out of the box without us shipping a closed-source binary. The upgrade path to v3 stays intact via existing plugin id.
- Risks / caveats: v1.9.7 lacks UI features added in v2/v3; users expecting modern Thino UX must upgrade themselves. The fetch URL (`https://github.com/Quorafind/Obsidian-Thino/releases/download/1.9.7/...`) is stable for the published 1.9.7 release tag, but the v1 line stopped active development (last `v1` branch commit 2024-03-12) — expect no future security or compatibility patches on this code path. If the upstream owner ever rewrites or deletes the release, `setup-vault.sh` needs a fallback strategy.

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
