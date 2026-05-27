---
type: meta
title: "Hot Cache"
updated: 2026-05-28T00:00:00
tags:
  - meta
  - hot-cache
status: evergreen
related:
  - "[[index]]"
  - "[[log]]"
  - "[[Wiki Map]]"
  - "[[getting-started]]"
  - "[[DragonScale Memory]]"
---

# Recent Context

Navigation: [[index]] | [[log]] | [[overview]]

## Last Updated

2026-05-28: Plugin-Quality-Sweep landed across 5 parallel tracks + 1 sequential doc-fix track. Brand-rename Phase 1 (9 replacements on plugin surface; vault content untouched per decision). `lib/vault_root.sh` consolidated to a Python subprocess wrapper (23 lines; Python is single source of truth, ~90ms overhead within tolerance). Release tooling shipped: `bin/sync-versions.sh`, `bin/release.sh`, `tests/test_sync_versions.sh`. Tags v1.5.0 / v1.5.1 / v1.7.0 / v1.8.0 backfilled annotated (v1.6.0 already existed). `marketplace.json.plugins[0].source.ref` pinned to `v1.8.0`. GitHub Actions added: `test.yml`, `version-drift.yml`, `release.yml`. Repo-cleanup: `docs/install-guide.pdf` removed (162 KB binary; md source remains), `make clean` target added. Thino plugin removal blocked — license unverifiable in sandbox; manifest declares "Closed source"; documented in `docs/influence-log.md` for follow-up. Doc-drift fixed: all skill counts updated to 13 across CLAUDE.md, README.md, AGENTS.md, GEMINI.md, .github/copilot-instructions.md, .windsurf/, .cursor/.

2026-05-26: v1.8.0 cut (PR0 + PR1 — vault-root resolver + canonical lint aggregator). Severity defaults hardcoded for PR1.

2026-05-21: v1.7.0 — doc-pipeline skill changelog entry.

2026-04-24 (multi-phase): v1.5.0 (Phase 3.5 hardening), v1.5.1 (Phase 3.6 hardening), v1.6.0 (DragonScale Mechanism 4 — boundary-first autoresearch). All four DragonScale mechanisms shipped and feature-gated this day. See CHANGELOG.md for granular detail.

2026-04-23: Phases 0–3 of DragonScale shipped — fold operator, deterministic addresses, semantic tiling lint.

## Plugin State

- **Version**: 1.8.0
- **Install ID**: `agentic-knowledge-management@akm-marketplace`
- **Skills**: 13 (autoresearch, canvas, defuddle, doc-pipeline, obsidian-bases, obsidian-markdown, research-brief, save, wiki, wiki-fold, wiki-ingest, wiki-lint, wiki-query)
- **Scripts** (`scripts/`): `allocate-address.sh`, `boundary-score.py`, `lint-orphans.py`, `lint-terminology.py`, `lint-title-overlap.py`, `run-lint.sh`, `tiling-check.py`
- **Lib** (`lib/`): `vault_root.py` (single source of truth for vault-root resolution), `vault_root.sh` (subprocess wrapper)
- **Setup + Release** (`bin/`): `setup-vault.sh`, `setup-dragonscale.sh`, `setup-multi-agent.sh`, `sync-versions.sh`, `release.sh`
- **Tests** (`tests/`): test_allocate_address.sh, test_boundary_score.py, test_lint_orphans.py, test_lint_terminology.py, test_lint_title_overlap.py, test_run_lint.sh, test_sync_versions.sh, test_tiling_check.py, test_vault_root.py, test_vault_root.sh. Zero ollama dependency for core tests.
- **CI** (`.github/workflows/`): `test.yml` (push + PR: make test + run-lint), `version-drift.yml` (PR drift gate on plugin.json/marketplace.json sync), `release.yml` (on release published: attach PDF via pandoc).
- **Hooks** (`hooks/hooks.json`): 4 hooks — SessionStart, PostCompact, PostToolUse [stages `wiki/`, `.raw/`, `.vault-meta/`], Stop.

## DragonScale Mechanisms

1. **Fold operator** (Mechanism 1): `skills/wiki-fold/`, dry-run verified AND first real fold committed at `wiki/folds/fold-k3-from-2026-04-23-to-2026-04-24-n8.md`.
2. **Deterministic addresses** (Mechanism 2): shipped and exercised; vault counter at 3. `c-000001` on `DragonScale Memory.md`. `c-000002` reserved-unassigned from validation pass (gap acceptable per spec).
3. **Semantic tiling lint** (Mechanism 3): shipped and activated. `nomic-embed-text` pulled; first tiling report at `wiki/meta/tiling-report-2026-04-24.md` (0 errors, 15 review-band pairs).
4. **Boundary-first autoresearch** (Mechanism 4): shipped (Phase 4, opt-in). `scripts/boundary-score.py` + `tests/test_boundary_score.py`. `/autoresearch` without a topic surfaces top-5 frontier pages as candidates; user picks, overrides, or declines. Explicitly labeled "agenda control" in both spec and skill.

## Key Lessons from This Release Cycle

1. Worktree isolation has subtle branchpoint timing — parallel agents may capture pre-merge HEAD. Verify branch base before merging cross-track work.
2. License-block-on-sandbox is a valid STOP signal: when a dependency's license cannot be programmatically verified, halting beats guessing.
3. Single source of truth for version (`plugin.json.version`) plus a tiny `jq` mirror script eliminates manifest drift without needing semantic-release tooling.
4. Cross-phase audits remain essential. Individual phase reviews miss drift between phases.
5. PostToolUse hook matcher is `Write|Edit`, so Bash writes don't fire it. Scripts that mutate tracked state must be Bash-only to avoid side-effect commits.

## Style Preferences

- No em dashes (U+2014) or `--` as punctuation. Periods, commas, colons, or parentheses. Hyphens in compound words are fine.
- Short and direct responses. No trailing summaries.
- Parallel tool calls when independent.

## Active Threads

- v1.5.0 through v1.8.0 tags exist locally (annotated, backfilled on historical release commits). User decides when to `git push origin --tags`.
- CI gate on first run will surface ~183 wiki-lint findings (vault content quality, not plugin-distribution). Track that cleanup separately if desired, or invert the lint job to "regression-only" mode.
- Thino bundle removed in favor of v1.9.7 ("Obsidian Memos", MIT). `.obsidian/plugins/thino/{main.js,styles.css}` (~2.6 MB) deleted from the repo; `setup-vault.sh` now downloads them from the upstream `1.9.7` release at first run, analogous to the Excalidraw pattern. Users with a Thino Insider (Pkmer) license can upgrade in-place (plugin id `obsidian-memos` is shared between v1/v3).
- `commands/` aliases registered for Claude Code: `/wiki`, `/save`, `/autoresearch`, `/canvas`, `/doc-pipeline`. Other skills (`wiki-ingest`, `wiki-query`, `wiki-lint`, etc.) trigger via natural-language phrases per their SKILL.md descriptions.

## Repo Locations

- Working: `~/AI-powered_workbench/agent-based-knowledge-management/`
- Public: `https://github.com/philippsied/agent-based-knowledge-management`
