# Changelog

All notable changes to agentic-knowledge-management. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [2.0.0] - 2026-07-02

### Added

- **`wiki-issues` skill — one owner for the `wiki/meta/OPEN-ISSUES.md` issue stack (ADR-0005).** Absorbs the former `/wiki:handoff` (push: synthesize session todos/insights into stack entries with fresh year-resetting `I-YYYY-NNN` ids) and `/wiki:fix-issues` (pop: verify and work exactly one ready top-of-stack issue, with resolved/stale/inconclusive/aggregation dispositions) as two sub-flows, plus stack init and a format-version guard. Ships a colocated validator (`skills/wiki-issues/scripts/lint-open-issues.py`: schema / stack↔body parity / `blocked_by` cycles / 4-key sort) wired into `run-lint.py` so `totals.error` gates it in CI. Section whitelist reconciled to 12 values (audit V-6).
- **`visualize` skill — self-contained HTML export layer (15th skill).** Ships `careerhackeralex`'s upstream visualization skill (MIT, v0.3.0), re-scoped as an external shareable-artifact layer (decks, infographics, dashboards, one-pagers) that complements the internal `canvas` board. `SKILL.md` trimmed to a lean ~10 KB dispatcher (49,959 → 10,212 B) with the heavy code blocks relocated into `references/`; frontmatter gains `allowed-tools: Read Write Edit Glob Grep`. Default output `wiki/visualizations/<slug>.html` plus a companion `type: visualization` stub — both git-ignored (regenerable) and `wiki-lint`-excluded. README gains a Credits section.
- **Skill-count SSOT guard (`tests/test_skill_count_ssot.py`, FUP-5).** The git-tracked `skills/*/SKILL.md` set is the single source of truth for the plugin's skill count; the guard (wired into `make test` / CI) fails if any count literal or enumeration table drifts. Reconciled every surface to **15 skills** — README (×2) + `.github/copilot-instructions.md` numeric literals, and the `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` skill tables (the latter two were additionally missing the `wiki-issues` row).

### Changed

- **Shell→Python migration (in progress).** The `run-lint` aggregator and the DragonScale address allocator are now pure Python (`scripts/run-lint.py`, `scripts/allocate-address.py`), invoked directly with no shell wrapper. `run-lint.py` additionally folds its six `lint-*.py` checks in-process (imported `collect*` entrypoints instead of `sys.executable` subprocesses), so the aggregate `--json` and Markdown report are produced with zero subprocess startup and stay byte-identical to the prior output. Each `lint-*.py` remains runnable standalone via its `__main__`. Vault root resolves via `lib/vault_root.py`. Tracked under `docs/plans/PLAN-sh-to-py-full-migration.md`.
- **Release lint gate scoped to the plugin distribution (`bin/release.py`).** `scripts/run-lint.py` lints the working vault (`wiki/`), which is not part of the shipped plugin, so its severity findings (the pre-existing 182-error demo content) no longer block `make release`. The gate now blocks only when run-lint cannot run (crash / unparseable JSON); distribution correctness stays gated by `make test`. Regression guard: `tests/test_release_gate.py` (`make test-release-gate`, wired into `make test`). Fixes the "release lint-gate trap" that made 2.0.0 uncuttable.

### Fixed

- **`dead_link_targets` no longer false-flags wikilinks to `.raw/` sources as dead.** The legacy shell aggregator built the `.raw` half of the valid-target set from `find`'s full path with only a trailing `.md` stripped, so a bare `[[foo]]` could never match a source `.raw/foo.pdf` and was always reported DEAD (the raw-union had never worked). `run-lint.py` now adds each in-glob raw file's basename with the final extension stripped, case-insensitively, ASCII-lowercased, so source citations resolve. This intentionally changes dead-link results versus the previous shell implementation: some links that were falsely dead become valid.

### Removed

- **`scripts/run-lint.sh` and `scripts/allocate-address.sh` removed.** The Python ports are now the direct entrypoints; `Makefile`, CI (`.github/workflows/test.yml`), `bin/release.sh`, `bin/setup-dragonscale.sh`, the `wiki-lint` / `wiki-ingest` skills + agents, and `docs/dragonscale-guide.md` were repointed to `.py`. Feature-detection guards switched from `[ -x …sh ]` to `[ -f …py ]` so a missing port disables the optional path rather than silently passing.
- **`tests/test_run_lint.sh` retired** in favor of `tests/test_run_lint.py`. The shell test's top-level-key and seeded-finding assertions are a subset of the Python characterization suite (183 checks). `make test-run-lint` and CI now run `python3 tests/test_run_lint.py`.
- **All 7 `commands/` files removed — the plugin is skills-only (ADR-0001, executed via FUP-4).** Breaking change vs `v1.10.1`: the `/wiki:fix-issues`, `/wiki:handoff`, `/wiki`, `/save`, `/canvas`, `/autoresearch`, and `/doc-pipeline` slash-commands no longer exist. **Migration (audit V-3):** trigger the same behavior via natural language or the skills. The 2 substantive commands are now the `wiki-issues` skill (say "handoff" / "synthesize issues" to push, "fix issues" / "work the top issue" to pop); the 5 thin wrappers were already backed by their same-named skills (`wiki`, `save`, `canvas`, `autoresearch`, `doc-pipeline`). No `plugin.json` / `marketplace.json` change (commands were never enumerated there).
- **Multi-agent surfaces removed — the plugin is Claude-only.** Breaking change vs `v1.10.1`: `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`, and `bin/setup-multi-agent.py` no longer ship, and the plugin no longer advertises Codex / Gemini / Cursor / Windsurf / OpenCode support. Every convention those files carried already had a single source of truth in `skills/*`, `references/operational-rules/*`, `hooks/hooks.json`, `README.md`, or `CLAUDE.md` (provenance map: `docs/audit/2026-07-02/multi-agent-salvage.md`); `CLAUDE.md` gains a "Conventions & Editing" pointer section that preserves the single-entry-point value. The skill-count SSOT guard (`tests/test_skill_count_ssot.py`) was repointed to the Claude-only surface set (`TABLE_SURFACES = [CLAUDE.md]`; copilot dropped from the numeric + name-list checks). README drops the "Multi-agent support" tagline and the "Multi-model support" comparison row.

## [1.10.1] - 2026-06-21

### Changed

- **`scripts/allocate-address.sh` is now a thin shell shim over a new `scripts/allocate-address.py`.** DragonScale Mechanism 2's address allocator was reimplemented in Python so it locks via `fcntl.flock` (the POSIX `flock(2)` syscall) instead of the util-linux `flock(1)` CLI. macOS does not ship `flock(1)`, so the shell allocator failed on every macOS invocation (exit 1 with a misleading "could not acquire lock" message) and its test suite could not run there. The Python version works on macOS and Linux with no external binary and keeps the same kernel-managed auto-release on process exit. Vault root now resolves through `lib/vault_root.py` (`KM_VAULT_PATH` -> cwd), completing the PR0 resolver routing and fixing the marketplace-install case where script-relative resolution pointed at the plugin dir. The shim preserves the executable API and the `[ -x ]` feature detection, so `wiki-ingest`, `wiki-lint`, and `setup-dragonscale` are unchanged.

### Fixed

- **Allocator test suite could not run under restricted temp environments.** `tests/test_allocate_address.sh` used `mktemp -d -t`, which ignores `$TMPDIR`. Replaced by `tests/test_allocate_address.py` (plain-python, `$TMPDIR`-aware), which also adds a 20-way concurrency stress exercising the `fcntl.flock` guard.

## [1.10.0] - 2026-06-03

### Added

- **`hooks/wiki-path-safety.sh` opt-in mixed mode for vaults that double as work trees.** A repo that holds both wiki content and active non-wiki work (the plugin's own dev tree, code projects with a `wiki/` knowledge layer) can now opt out of the strict whitelist for non-wiki paths. In `mixed` mode the hook emits a PreToolUse `permissionDecision: allow` with a model-visible `additionalContext` reminder instead of `exit 2`. Strict mode (default) is unchanged. `.raw/` immutability and wiki filename hyphenation stay hard exits in both modes (wiki integrity rules per SPEC F2 resolution).
- **`.vault-meta/config.json` config schema** with `version: 1` and `path_safety_mode` (`strict` | `mixed`). Single source of truth; no env override. Bootstrap is idempotent and silent: vaults predating v1.10.0 get a strict config written on the next hook fire so the read path has no missing-file branch. Malformed JSON, unknown `version`, and unknown `path_safety_mode` warn on stderr and fall back to strict.

  Example:

  ```json
  { "version": 1, "path_safety_mode": "mixed" }
  ```

- **`bin/setup-vault.sh`** asks "Does this repo also hold non-wiki work (code, docs) next to the wiki? [y/N]" on TTY-interactive fresh installs and writes the chosen mode to `.vault-meta/config.json`. Non-interactive runs default to strict, no prompt. Idempotent: existing config files are preserved.
- **`tests/test_wiki_path_safety.sh`** extended from 14 to 43 cases. Adds the `strict` x `mixed` mode dimension, NotebookEdit tool-input shape, and config bootstrap / malformed / unknown-version / unknown-mode cases.

### Fixed

- **`hooks/wiki-path-safety.sh` NotebookEdit silent-pass.** The hook matcher is `Write|Edit|NotebookEdit`, but the tool-input extractor only read `file_path`. `NotebookEdit` passes `notebook_path`, so every notebook write silent-passed the hook. The extractor now falls back to `notebook_path` and notebook writes are subject to the same whitelist and mode logic as Write/Edit.

### Notes

- The DRAFT spec discussed a `KM_PATH_SAFETY` runtime env override. It was not shipped: hooks inherit the environment captured at session start, so an env override cannot toggle live mid-session, and documenting it would have been misleading. Mode is config-only: edit `.vault-meta/config.json` to switch.
- `PostToolUse` runs `git add wiki/ .raw/ .vault-meta/` after Write/Edit. In `mixed` mode, non-wiki writes (for example `src/foo.ts`) are allowed but NOT auto-staged by this hook (the matcher stages only wiki paths). Intentional: the hook should not auto-commit code-shaped writes.

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
