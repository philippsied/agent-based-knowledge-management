# Changelog

All notable changes to agentic-knowledge-management. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [1.9.1] - 2026-05-31

### Fixed

- **Vault-detection guard for `hooks/wiki-path-safety.sh`.** The PreToolUse hook is registered by a user-scope plugin, so it fired in every session and blocked ordinary writes (`src/`, `lib/`, and similar) in unrelated repositories, and even in the plugin's own development tree. Two guards now bound it. Guard A enforces nothing unless the session is an actual vault (a `.vault-meta/` marker is present or `KM_VAULT_PATH` is set). Guard B only governs writes that resolve inside the vault root. Non-vault sessions and out-of-vault writes now pass through untouched, matching the defensive behavior of the other three hooks.

## [1.9.0] - 2026-05-30

### Changed

- **`/wiki:fix-issues` + `/wiki:handoff` + `_templates/open-issues.md` — hybrid stack schema (breaking behavior change).** `OPEN-ISSUES.md` now carries a YAML frontmatter `stack:` array (the ordered work queue) plus per-issue `### I-YYYY-NNN` body sections. Issues gain stable ids, `priority` (P0–P3), `section` (7-value whitelist: `enforcement`/`lint`/`vault-content`/`tooling`/`templates`/`skill-plugin`/`eval-observability`), `blocked_by`, plus `inconclusive_since`/`inconclusive_reason` and `aggregated_from` metadata. `/wiki:fix-issues` now pops the first *ready* (unblocked) highest-priority issue and gains an inconclusive (4d) path; `/wiki:handoff` inserts in priority-sorted position with year-resetting ids. Ordering changed from pure LIFO to priority-ASC → ready-first → LIFO-tiebreaker. The reference vault's data migration and `lint-open-issues.py` validator land separately in the vault repo.
- **Vault content excluded from plugin distribution.** `wiki/`, `.raw/` source documents, and per-vault DragonScale state files (`.vault-meta/address-counter.txt`, `.vault-meta/legacy-pages.txt`) are no longer tracked. The plugin ships only the directory anchors (`wiki/.gitkeep`, `.raw/.gitkeep`) and shared default config (`.vault-meta/tiling-thresholds.json`). Each install scaffolds its own vault state via `bin/setup-vault.sh`. Eliminates the prior CI-lint noise (182 errors / 37 warnings sourced exclusively from the maintainer's working vault) and removes ~5.3 MB of personal knowledge content from every install.
- **`bin/setup-vault.sh`** now scaffolds `.vault-meta/` with a fresh `address-counter.txt` (seeded `0`) and a `legacy-pages.txt` template. Idempotent: existing files are preserved.

## [1.8.0] - 2026-05-26

First two PRs of the [upstream roadmap](docs/upstream-roadmap.md) for deterministic wiki-quality tooling. PR0 lays the portability foundation; PR1 ships the canonical lint aggregator on top of it.

### Added (PR0 — vault-root resolver, per `docs/upstream-roadmap.md` §5)

- **`lib/vault_root.py` + `lib/vault_root.sh`** — single source of truth for "where is the vault". Resolution order: `KM_VAULT_PATH` (env) → positional CLI arg → cwd. Cwd default makes a marketplace-installed plugin operate on the user's vault rather than on its own install directory under `~/.claude/plugins/`. Env override is for hooks, CI jobs, and other contexts where cwd is not the vault.
- **Resolver-routing**: `scripts/tiling-check.py`, `scripts/boundary-score.py`, `scripts/lint-terminology.py`, `scripts/lint-title-overlap.py` no longer reference `__file__` for `VAULT_ROOT`. Fixes the plugin-is-vault path conflation (§2.3 of the roadmap) that would have silently mis-resolved every script's vault root once the plugin was installed via the marketplace.
- **`tests/test_vault_root.py` (10 cases) + `tests/test_vault_root.sh` (8 cases)** — env > argv > cwd precedence, tilde expansion, empty-env fall-through.
- **`make test-vault-root` / `make test-terminology` / `make test-title-overlap`** targets, wired into default `test`.

### Added (PR1 — canonical lint aggregator, per `docs/upstream-roadmap.md` §5)

- **`scripts/run-lint.sh`** — single-runner wiki-quality lint aggregator. Calls every deterministic check (`spaced_filenames`, `spaced_wikilinks_body`, `orphans`, `dead_link_targets`, `frontmatter_gaps`, `terminology`, `title_overlap`) and emits a structured JSON summary with **per-check severity** (`error` / `warn` / `info`) plus a totals block. Required for the Tier-1 (pre-commit) and Tier-2 (CI) gates that ship in subsequent PRs (PR3a / PR3b).
- **`scripts/lint-orphans.py`** — ported from the reference vault, now uses the resolver from PR0 and a case-insensitive path index (the source script's `os.path.isfile` slash-form was case-sensitive on tmpfs).
- **`tests/test_lint_orphans.py`** — 4 cases: orphan detection, argv form, missing-wiki guard, plain output.
- **`tests/test_run_lint.sh`** — 23 cases covering the JSON schema, every check name, seeded findings, report-file writing, and the resolver fallback.
- **`make lint`** target — runs `scripts/run-lint.sh` against the current vault.
- **`make test-lint-orphans` / `make test-run-lint`** targets, wired into the default `test` target.

### Changed

- **`skills/wiki-lint/SKILL.md`** — adds a "Deterministic engine first, judgment second" preamble pointing at `scripts/run-lint.sh` as the canonical entry point; LLM-judgment checks now layer on top of the aggregator's output instead of duplicating its work.

### Severity defaults (`scripts/run-lint.sh`)

| Check | Severity |
|---|---|
| `spaced_filenames` | error |
| `spaced_wikilinks_body` | error |
| `terminology` | pass-through (error / warn from `lint-terminology.py`) |
| `frontmatter_gaps` | warn |
| `orphans` | warn |
| `dead_link_targets` | warn |
| `title_overlap` | info |

Configurable severity overrides ship in PR1.5+ (JSON-Schema for frontmatter) or PR3b (CI gate config); for now the defaults are hardcoded.

### Known follow-up

Running `make lint` against this repo's own `wiki/` after the v1.8.0 cut reports **183 errors + 37 warns + 1 info**. This is the pre-flight cleanup blocker for PR3b's CI gate (see `docs/upstream-roadmap.md` §0.1 *Pre-flight blocker for PR3b*); it does not block PR1.5 or PR2.

## [1.7.0] - 2026-05-21

### Added

- **doc-pipeline skill + `/doc-pipeline` command**: 4-stage document→ingest pipeline. Stage 1 deterministic raw conversion (`markit` + a `pandoc` fidelity reference, with `.doc`→docx and `.pptm`→pptx pre-handling). Stage 2 QC pass annotating conversion fidelity, language, clarity, redundancy, verbosity, currency, links, sources, footnotes, tables and Mermaid-diagram opportunities as inline `<!-- REVIEW -->` comments without altering content. Stage 3 human approval gate. Stage 4 annotation stripper producing a clean file for `wiki-ingest`. Checkworthy facts are flagged; web fact-checking runs on request.
- `skills/doc-pipeline/scripts/convert-doc.sh` and `finalize-md.sh` — deterministic conversion and approval-gated finalize (preserve Markdown hard breaks).

## [1.6.0] - 2026-04-24

### Added (DragonScale Mechanism 4, opt-in)

- **Boundary-first autoresearch**: `scripts/boundary-score.py` computes `(out_degree - in_degree) * recency_weight` across the wikilink graph and emits top-K frontier pages. `/autoresearch` invoked without a topic now offers the top-5 frontier pages as research candidates when the vault has adopted DragonScale.
- `tests/test_boundary_score.py` — 35 unit tests covering frontmatter parsing, recency weight, wikilink extraction (with code-block guard), graph construction, scoring, CLI interface.
- `make test-boundary` target + integration into `make test`.

### Changed

- `skills/autoresearch/SKILL.md` — new Topic Selection section with three paths: explicit (A), boundary-first (B, opt-in), user-ask (C, default without DragonScale).
- `commands/autoresearch.md` — no-topic usage documented for both modes.
- `wiki/concepts/DragonScale Memory.md` — Mechanism 4 flipped from NOT IMPLEMENTED to shipped; exact scoring formula and "what is NOT included" callout added. Version bumped to v0.4.
- Version synced to 1.6.0 across plugin.json and marketplace.json.

## [1.5.1] - 2026-04-24 (Phase 3.6 hardening)

### Fixed

- `scripts/tiling-check.py`: `--report PATH` now resolved against VAULT_ROOT and rejected if it escapes (security: prevents hostile or accidental writes outside the vault).
- `.vault-meta/legacy-pages.txt`: rollout baseline corrected from 2026-04-24 to 2026-04-23 (matches earliest addressed page in the seed vault).
- `AGENTS.md`: wiki-fold listed in the skills table; stale claim that "all skills use only name/description" narrowed to newer skills (older skills still carry allowed-tools for Claude Code compatibility).
- `skills/wiki-ingest/SKILL.md`: resolves the internal contradiction between "immutable .raw/" and "maintain .raw/.manifest.json" — user-dropped source documents remain immutable; only the manifest is wiki-ingest-maintained.
- `docs/install-guide.md`: version 1.2.0 -> 1.5.0 with a DragonScale optional-install callout.

## [1.5.0] - 2026-04-24

### Added (DragonScale Memory extension, opt-in)

- **Mechanism 1 — Fold operator** (`skills/wiki-fold/`): extractive, structurally-idempotent rollups of `wiki/log.md` entries into per-batch meta-pages under `wiki/folds/`. Dry-run via stdout by default (does not trigger PostToolUse auto-commit hook); commit mode explicit.
- **Mechanism 2 — Deterministic page addresses** (opt-in): `scripts/allocate-address.sh` flock-guarded atomic allocator; new `address: c-NNNNNN` frontmatter convention; re-ingest idempotency via `.raw/.manifest.json address_map`. `wiki-ingest` and `wiki-lint` skills feature-detect DragonScale setup.
- **Mechanism 3 — Semantic tiling lint** (opt-in): `scripts/tiling-check.py` uses local `nomic-embed-text` via ollama to flag candidate duplicate pages by cosine similarity. Banded thresholds (error/review/pass) documented as conservative seeds with manual calibration procedure.
- `wiki/concepts/DragonScale Memory.md` — full design spec (v0.3) with four mechanisms, scope boundary, and primary-source citations.
- `bin/setup-dragonscale.sh` — idempotent installer that provisions `.vault-meta/` counter, thresholds, and legacy-pages manifest.
- `tests/` — shell + python test suite for the allocator and tiling-check. Run via `make test`.
- `Makefile` — developer targets (`test`, `setup-dragonscale`, `clean-test-state`).

### Changed

- `hooks/hooks.json` PostToolUse now stages `.vault-meta/` in addition to `wiki/` and `.raw/` so DragonScale runtime state is captured by the auto-commit hook.
- `skills/wiki-ingest/SKILL.md` and `skills/wiki-lint/SKILL.md` gained opt-in DragonScale sections behind feature-detection guards; original behavior unchanged for vaults that have not run `setup-dragonscale.sh`.
- `agents/wiki-ingest.md` explicitly forbids parallel sub-agents from calling the allocator (single-writer rule for address assignment).
- `agents/wiki-lint.md` extended to describe Address Validation and Semantic Tiling checks.
- Stale `allowed-tools` frontmatter removed from `wiki-ingest` and `wiki-lint` SKILL.md (kepano convention: only `name` and `description`).
- Version strings synced across `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and documentation.

### Security

- `scripts/tiling-check.py` locks `OLLAMA_URL` to localhost by default. Remote endpoints require `--allow-remote-ollama`. Symlinks and vault-root escapes are rejected before any read.

### Not in this release

- **Mechanism 4 — Boundary-first autoresearch**: documented in the spec as a future proposal; no code shipped. `skills/autoresearch/SKILL.md` unchanged.

## [1.4.3] - prior

Previous state. See git log for details.
