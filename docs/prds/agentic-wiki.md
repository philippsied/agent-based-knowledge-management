---
artifact: prd
slug: agentic-wiki
status: draft        # draft | review | approved
related: CLAUDE.md, AGENTS.md, GEMINI.md, docs/prds/dragonscale.md, docs/upstream-roadmap.md
---

# PRD — Agentic Wiki (Platform)

> Answers: WHAT is the platform & WHY? For whom? How do we measure success?
> **No HOW** — implementation lives in the skills, scripts, and hooks themselves; module-level refactors live in `docs/specs/`.
> **Anchors (5 W):** Why · What · What-not · When-done · With-what — no How.
> **Relationship:** This is the foundation. [DragonScale](./dragonscale.md) is one optional extension layered on top; this PRD owns the base skills, setup, hooks, and scripts that both the repo and DragonScale build on.

## 1. Problem & Evidence  ‹Why›

LLM sessions are stateless: context evaporates between sessions, insights are lost, and research never compounds. Re-explaining the same background every session is pure waste, and human-first note tools (including plain Obsidian) give an agent no reliable, deterministic way to read, write, and *maintain* a knowledge base at quality.

The Agentic Wiki turns Claude + Obsidian into a **persistent, compounding knowledge base**: drop any source, ask any question, and the vault grows richer every session. It is Markdown-first with Python as the only executable code and **no build step**, so the same repository is simultaneously a Claude Code plugin, a cross-agent Skills package (via `AGENTS.md` / `GEMINI.md` / Copilot instructions), and an Obsidian vault openable directly.

## 2. Target users / Beneficiaries  ‹What: for whom›

- **Knowledge workers & researchers** who want a cumulative "second brain" an agent keeps current, not a pile of dead notes.
- **Claude and other agents** (GitHub Copilot, Gemini CLI) as read/write clients — the platform is deliberately cross-agent.
- **Cross-project consumers** that reference the vault from other repositories for context they don't hold locally.
- **Plugin / vault maintainers** who need deterministic quality and consistency enforcement rather than prose conventions.

## 3. Goals & Success metrics  ‹When-done›

| # | Goal | Success metric (binary / measurable) |
|---|------|--------------------------------------|
| G1 | Persist & compound knowledge across sessions | Hot cache + index + log restore context on `SessionStart`; each ingest adds cross-referenced pages; nothing lost between sessions. |
| G2 | Ingest any source | Files, URLs, batches, and binary docs (`.docx/.pdf/.pptx/.xlsx/…`) convert into structured, cross-linked wiki pages. |
| G3 | Answer from the vault, grounded | Questions answered via hot → index → pages with citations; good answers filed back. |
| G4 | Enforce quality deterministically | CI `wiki-quality` gate passes only when `run-lint.py --json` reports `totals.error == 0`; the path-safety hook blocks misplaced/misnamed writes. |
| G5 | Stay portable & extensible | Repo remains valid as Claude plugin **and** cross-agent skill package **and** Obsidian vault at once; extensions (DragonScale) attach without hard-coupling. |

## 4. Scope  ‹What / What-not›

**In scope**
- The **skill suite** (14 skills): ingest, query, lint, save, autoresearch, research-brief, doc-pipeline, defuddle, canvas, obsidian-bases, obsidian-markdown, visualize, and the `wiki` router.
- **Setup / bootstrap**: `bin/setup-vault.py`, `bin/setup-multi-agent.py`, the plugin manifest (`.claude-plugin/plugin.json`), marketplace (`marketplace.json`), and the `Makefile` targets.
- **Lifecycle hooks** (5) including the write-safety gate and wiki auto-commit.
- **Quality tooling**: the `lint-*` scripts, the `run-lint.py` aggregator, the pytest suite, the evals harness, and the GitHub Actions workflows.
- **Vault structure & config**: `.raw/` (immutable), `wiki/`, `_templates/`, `.vault-meta/`, and the cross-agent config files.
- **Extension points** that DragonScale (and future extensions) rely on: `.vault-meta/` feature-detection and a single vault-root resolver.

**Out of scope**
- The **DragonScale mechanisms** themselves (separate PRD): this platform only provides the extension points and feature-detection, not the fold/address/tiling/boundary logic.
- A shipped **MCP server**: MCP is opt-in and user-configured; the repo ships documentation only, no `.mcp.json`.
- Any **non-Markdown / non-Python build system**; no compiled artifacts, no bundler.
- **Hosted / cloud services**: the platform runs locally against a local vault.

## 5. Requirements (prioritized)  ‹What›

**P0 — core platform**
- **R1 Ingest pipeline.** `wiki-ingest` skill (+ `agents/wiki-ingest` parallel subagent) turns sources into cross-referenced entity/concept pages, updates the index, and logs. `scripts/wiki-prepass.py` runs the entity-registry pre-pass; `doc-pipeline` (+ colocated `convert-doc.py` / `finalize-md.py`) converts binary docs with a QC gate; `defuddle` strips web clutter before ingest. Optional `review` flag = pre-ingest human gate.
- **R2 Retrieval.** `wiki-query` answers from hot cache → index → pages with citations (quick / standard / deep modes); `save` files conversations/insights back as structured notes and updates index + log + hot cache.
- **R3 Structure & setup.** `bin/setup-vault.py` scaffolds the vault; the `wiki` skill routes setup and sub-skills; the vault layout is fixed (`.raw/` immutable, `wiki/`, `_templates/`, `.vault-meta/`); `lib/vault_root.py` is the single vault-root resolver (order: `KM_VAULT_PATH` → CLI arg → cwd) so a marketplace-installed plugin operates on the user's vault, not its install dir.
- **R4 Write-safety hook.** `hooks/wiki-path-safety.py` (PreToolUse on `Write|Edit|NotebookEdit`) deterministically enforces (a) a path whitelist (`wiki/`, `scripts/`, `.vault-meta/`, `.gitattributes`, `.raw/.manifest.json`) and (b) no spaces in `wiki/*.md` filenames.
- **R5 Quality lint + CI gate.** `scripts/run-lint.py` aggregates the `lint-*` checks (orphans, deps, programs, rename, terminology, title-overlap); `wiki-lint` skill (+ `agents/wiki-lint` subagent) drives it; `test.yml` fails the build when `run-lint.py --json` reports any `error`.

**P1 — high value**
- **R6 Session lifecycle hooks (5).** `SessionStart` (load `wiki/hot.md`), `PostCompact` (re-orient after compaction), `PreToolUse` (path-safety, R4), `PostToolUse` (auto-`git add`/commit of `wiki/ .raw/ .vault-meta/`), `Stop` (emit a signal when `wiki/` changed so the hot cache is refreshed).
- **R7 Autonomous research.** `autoresearch` skill (search → fetch → synthesize → file loop, configured by `program.md`) with `research-brief` enforcing the W1–W12 brief conventions; both carry `evals/`.
- **R8 Authoring & visual skills.** `canvas` (Obsidian `.canvas`), `obsidian-bases` (`.base` DB views), `obsidian-markdown` (Obsidian-flavored syntax), `visualize` (self-contained HTML visuals).
- **R9 Cross-agent portability.** `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, and `.github/copilot-instructions.md` expose the skill suite to Claude, generic agents, Gemini, and Copilot; `plugin.json` + `marketplace.json` handle distribution; skills/commands/hooks are auto-discovered by directory convention (no explicit manifest keys).
- **R10 Release & version integrity.** `bin/release.py` prepares releases; `bin/sync-versions.py` mirrors `plugin.json` → `marketplace.json`; `version-drift.yml` fails PRs on drift; `release.yml` attaches a rendered PDF.

**P2 — supporting**
- **R11 Extension hosting.** The platform must host optional extensions without hard-coupling: `.vault-meta/` feature-detection across skills and an opt-in installer (`bin/setup-dragonscale.py`) let [DragonScale](./dragonscale.md) attach and detach cleanly.
- **R12 Regression evals.** `evals/run.py` (+ `score-summary.py`) is a guardrail over `ingest` / `lint` / `query` case folders — a regression tripwire, not a benchmark.
- **R13 Optional MCP.** Direct vault read/write via MCP is documented (`skills/wiki/references/mcp-setup.md`, four options) but not shipped; the platform must not depend on it.
- **R14 Multi-agent install.** `bin/setup-multi-agent.py` installs the skill set for multi-agent use.
- **R15 Command-deletion migration path.** When ADR-0001's command deletion is executed, ship a user-facing migration path: a CHANGELOG/release-note deprecation of the removed commands plus equivalent invocation via the `wiki-issues` skill (the plugin is released, `v1.10.1`, so the breaking change must be signposted). Tracked as an FUP-4 deliverable (audit V-3).

## 6. Constraints & Assumptions  ‹With-what›

- **Markdown-first, Python-only, no build step.** The only executable code is Python; everything else is Markdown/JSON. This keeps the repo simultaneously a plugin, a skill package, and an Obsidian vault.
- **Determinism where it gates quality.** Path-safety, lint, address allocation, and version-drift are deterministic and CI-enforced — not prose conventions (the write-safety hook exists precisely because prose conventions once misplaced 11 files).
- **Immutable sources.** `.raw/` is read-only to the agent.
- **Auto-discovery.** `plugin.json` declares no explicit `skills`/`commands`/`hooks`/`mcpServers` keys; Claude Code discovers them by directory convention — directory layout is therefore load-bearing.
- **Single vault-root resolver.** All scripts resolve the vault through `lib/vault_root.py`; no per-script path assumptions.

## 7. Risks & open questions

- **Commands ⇄ skills duplication.** ADR-0001 ("delete commands, skills-only") is *accepted* but **not executed**: 7 command files still coexist with the skills — 5 are thin wrappers, but `commands/wiki/fix-issues.md` and `commands/wiki/handoff.md` are substantive and need a skill home first.
- **Inventory drift.** `.github/copilot-instructions.md` still says "13 skills" while 14 exist on disk (`visualize` is undocumented). There is no single source of truth for the skill count.
- **`_attachments/` absent.** The directory is referenced in `CLAUDE.md` and `.gitignore` but does not exist on disk.
- **No local pre-commit gate.** `.pre-commit-config.yaml` is absent; quality is enforced in CI and via the hook, but not at commit time locally (roadmap PR3a/PR3b territory).
- **Cross-agent write path depends on user MCP config.** Without a shipped server, non-Claude agents' direct write access is user-configured and unverified in CI.

### Checklist (before status: approved)
- [x] Full component inventory verified on disk (2026-07-01)
- [ ] Commands-vs-skills coexistence resolved (execute ADR-0001 or defer explicitly)
- [ ] Skill-count single source of truth (fix copilot-instructions 13 → 14)
- [ ] `_attachments/` created or de-referenced across docs
- [ ] Success metrics G1–G5 wired to the evals harness + lint totals

---

## Appendix A — Skill catalog (14, verified on disk)

| Skill | Purpose (one line) |
|---|---|
| `wiki` | Router/bootstrap: scaffold or check the vault, manage hot cache, route to sub-skills. |
| `wiki-ingest` | Ingest files/URLs/batches into cross-referenced entity + concept pages; optional review gate. |
| `wiki-query` | Answer questions from the vault (hot → index → pages) with citations; quick/standard/deep. |
| `wiki-lint` | Health-check: orphans, dead links, stale claims, missing xrefs, frontmatter gaps. |
| `wiki-fold` | DragonScale M1 rollup of `wiki/log.md` into idempotent fold pages. |
| `save` | File the current conversation/insight into the vault as a structured note. |
| `autoresearch` | Autonomous research loop (search → fetch → synthesize → file), configured by `program.md`. |
| `research-brief` | Build/audit an autoresearch brief against the W1–W12 conventions. |
| `doc-pipeline` | Convert binary docs (`.docx/.pdf/.pptx/.xlsx/…`) into ingest-ready Markdown with a QC gate. |
| `defuddle` | Strip ads/nav/boilerplate from web pages before ingest (~40–60% token savings). |
| `canvas` | Add images/text/PDFs/pages to Obsidian `.canvas` files with auto-positioning. |
| `obsidian-bases` | Create/edit Obsidian Bases (`.base`) database-style views. |
| `obsidian-markdown` | Author correct Obsidian-flavored Markdown (wikilinks, callouts, embeds, properties). |
| `visualize` | Build self-contained HTML visualizations from any content. |

## Appendix B — Scripts, shared lib & bin (verified on disk)

- **Lint / quality (`scripts/`):** `run-lint.py` (aggregator; `--json` gates CI), `lint-orphans.py`, `lint-deps.py`, `lint-programs.py`, `lint-rename.py`, `lint-terminology.py`, `lint-title-overlap.py`.
- **DragonScale-core (`scripts/`):** `allocate-address.py`, `tiling-check.py`, `boundary-score.py` (owned by the DragonScale PRD; listed here as the extension's scripts hosted by the platform).
- **Utility (`scripts/`):** `rewrite-wikilinks.py`, `wiki-prepass.py`.
- **Colocated (per ADR-0002):** `skills/doc-pipeline/scripts/convert-doc.py`, `.../finalize-md.py`.
- **Shared lib:** `lib/vault_root.py` (vault-root resolver — single source of truth).
- **bin/:** `setup-vault.py`, `setup-dragonscale.py`, `setup-multi-agent.py`, `release.py`, `sync-versions.py`.

## Appendix C — Hooks (`hooks/hooks.json`, 5 lifecycle hooks)

| Event | Matcher | Action |
|---|---|---|
| `SessionStart` | `startup\|resume` | Load `wiki/hot.md` into context + orientation prompt. |
| `PostCompact` | — | Re-read hot cache after context compaction. |
| `PreToolUse` | `Write\|Edit\|NotebookEdit` | `wiki-path-safety.py` — path whitelist + naming enforcement. |
| `PostToolUse` | `Write\|Edit` | Auto-`git add` + commit of `wiki/ .raw/ .vault-meta/`. |
| `Stop` | — | Emit a signal when `wiki/` changed so the hot cache is refreshed. |

## Appendix D — CI, tests & evals

- **GitHub Actions:** `test.yml` (`make test` + wiki-quality lint gate on `run-lint.py --json`), `release.yml` (attach rendered PDF), `version-drift.yml` (`plugin.json` → `marketplace.json` sync).
- **Tests (`tests/`, pytest, 10):** allocate_address, boundary_score, lint_orphans, lint_terminology, lint_title_overlap, run_lint, sync_versions, tiling_check, vault_root, wiki_path_safety.
- **Evals (`evals/`):** `run.py` + `score-summary.py` over `ingest` / `lint` / `query` case folders — regression guardrail.
- **Absent by design:** `.mcp.json`, `.pre-commit-config.yaml`, `_attachments/`.
