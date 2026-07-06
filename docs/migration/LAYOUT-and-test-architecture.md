# Target Layout + Test-Design Architecture Review

**For:** the `agentic-knowledge-steward` clean-start. **As-of:** 2026-07-06.
**Companions:** [`INVENTORY-clean-start.md`](INVENTORY-clean-start.md) · [`SPEC-1.0.0-clean-start-migration.md`](../specs/SPEC-1.0.0-clean-start-migration.md)

Answers two asks: (a) consolidate everything plugin-related under `plugin/` and everything
engineering-related (tests, evals) under one folder; (b) review the test-design architecture.

---

## 1. Target top-level layout

```
agentic-knowledge-steward/
├── plugin/                         # THE Claude Code plugin — the only thing shipped to plugin consumers
│   ├── .claude-plugin/plugin.json  # (marketplace.json dropped — Gate #3)
│   ├── skills/                     # 15 skills            (auto-discovered relative to .claude-plugin/)
│   ├── hooks/                      # hooks.json + wiki-path-safety.py + README
│   ├── agents/                     # wiki-ingest, wiki-lint
│   ├── scripts/                    # lint-*, run-lint, allocate-address, tiling-check, …
│   ├── lib/                        # vault_root.py            (shared)
│   ├── bin/                        # setup-vault, setup-dragonscale, release, sync-versions
│   ├── references/                 # operational-rules/       (copied into user vaults on setup)
│   └── _templates/                 # source templates copied into user vaults      [see §4 flag]
├── engineering/                    # dev tooling — NOT shipped to plugin consumers
│   ├── tests/                      # 14 suites + _paths.py (NEW resolver)
│   ├── evals/                      # run.py, score-summary.py, 3 fixture cases
│   └── test-architecture.md        # NEW — the two-tier test doc (§5)
├── docs/                           # durable docs: adr/, LEARNINGS.md, guides, agentic-wiki PRD, install-guide, migration/
├── wiki/  .raw/  .vault-meta/  WIKI.md   # Obsidian vault skeleton (vault-runtime; content gitignored)
├── README.md  CLAUDE.md  LICENSE  ORIGIN.md  CHANGELOG.md
├── Makefile                        # dispatcher — targets point into plugin/ + engineering/
├── .gitlab-ci.yml                  # (follow-up) MUST sit at repo root for GitLab CI
└── .gitignore
```

**Boundary principle (why this is clean):** a plugin consumer installs **`plugin/` only** (via git-subdir).
`engineering/`, `docs/`, and the vault skeleton are repo-development artifacts that never reach plugin
consumers. `plugin/bin/setup-vault.py` provisions a *fresh* vault in the user's location — the repo-root
vault skeleton is only for local dev/demo.

## 2. Group → destination map (covers all 202 files without re-listing each)

| Source group | → Destination | Note |
|---|---|---|
| `.claude-plugin/plugin.json` | `plugin/.claude-plugin/` | `marketplace.json` dropped |
| `skills/**` (44) | `plugin/skills/**` | auto-discovered |
| `hooks/**` (3) | `plugin/hooks/**` | `${CLAUDE_PLUGIN_ROOT}` already used |
| `agents/**` (2) | `plugin/agents/**` | |
| `scripts/**` (12) | `plugin/scripts/**` | move **with** lib/ + skills/ (sibling `../lib` resolution) |
| `lib/vault_root.py` | `plugin/lib/` | |
| `bin/**` (4) | `plugin/bin/**` | |
| `references/operational-rules/**` (14) | `plugin/references/**` | CLAUDE.md pointers repoint here |
| `_templates/**` (13) | `plugin/_templates/**` | [§4 flag] |
| `tests/**` (14) | `engineering/tests/**` | + NEW `_paths.py` |
| `evals/**` (20) | `engineering/evals/**` | |
| `docs/**` (kept subset) | `docs/**` | unchanged location |
| `wiki/`, `.raw/`, `.vault-meta/`, `WIKI.md` | root (vault) | vault-runtime |
| `README/CLAUDE/LICENSE/CHANGELOG/.gitignore/Makefile` + NEW `ORIGIN.md` | root | Makefile = dispatcher |

## 3. Consumer requirements the `plugin/` subdir imposes (verified against Claude Code docs)

1. **External marketplaces must use `git-subdir`.** A marketplace listing this plugin needs
   `"source": {"type": "git-subdir", "url": "…/agentic-knowledge-steward", "subdirectory": "plugin/"}`.
   The official `claude-plugins-official` marketplace uses exactly this type. **→ document prominently in `README.md` + `ORIGIN.md` "How to install".**
2. **No `.claude/` directory inside `plugin/`.** A `.claude/` dir at the plugin root suppresses `skills/` discovery (Claude Code issue #44120). None is shipped today — keep it that way.
3. **Script references via `${CLAUDE_PLUGIN_ROOT}`.** Hooks + skills reference bundled scripts as `${CLAUDE_PLUGIN_ROOT}/scripts/…`. Our `hooks.json` PreToolUse already does. The variable is **not** populated in SessionStart hooks or command markdown — our SessionStart hook is vault-relative (`cat wiki/hot.md`), so unaffected.

> **Trade-off flag.** Official docs call a subdir plugin "valid but adds a consumer requirement" (the git-subdir source). The zero-consumer-burden alternative is to keep the plugin at **repo root** (standard discovery) and move only `engineering/` out. Recommended path honors your directive (`plugin/`); the fallback is a one-line spec change if you'd rather not impose git-subdir on listers.

## 4. Placement flags (judgment calls — defaults recommended)

- **`_templates/` → `plugin/_templates/`** (recommended): it is plugin-bundled — `setup-vault.py` copies it into user vaults via `${CLAUDE_PLUGIN_ROOT}/_templates/`. Consequence: this repo-as-vault's Obsidian *Templater* folder setting (in untracked `.obsidian/`) would point at the new path; only matters for local dev use, no tracked-file impact.
- **`.vault-meta/` → root** (recommended): vault-runtime state (hooks auto-commit it; `setup-dragonscale` writes it into the operated-on vault), not plugin-shipped.
- **`Makefile` → root dispatcher** (recommended): `make` is ergonomically run from repo root; targets just point into `plugin/` + `engineering/`. Alternative: `engineering/Makefile` + `make -C engineering`.
- **`.gitlab-ci.yml` → root** (required by GitLab): CI config must be at repo root, not under `engineering/`.

---

## 5. Test-design architecture — review

### 5.1 Current architecture (what's there today)

| Trait | Detail |
|---|---|
| **Runner** | Zero-dependency plain-Python — each `tests/test_*.py` defines `Fail(SystemExit)` + `assert_eq/assert_true`, run as `python3 tests/test_x.py`, exit 0/1. No pytest. |
| **Styles** | **Black-box** (subprocess-invoke `scripts/x.py` as real callers do) **+ white-box** (`importlib.util.spec_from_file_location` for hyphenated filenames). |
| **Aggregation** | `Makefile` fans 14 `test-*` targets into `make test` — one deterministic gate. |
| **Characterization suites** | `test_run_lint.py` (≈183 parity cases), `test_wiki_path_safety.py` (43 cases) — refactor oracles (D1 relied on the 43/43 truth-table before the hook cutover). |
| **SSOT guards** | `test_skill_count_ssot.py` (git-tracked `skills/*/SKILL.md`), `test_release_gate.py` (distribution-scoping, D5), `test_sync_versions.py`. |
| **Evals** | `evals/run.py` + fixture cases — behavioral, **model-graded**, **not** wired into `make test`. |
| **Path resolution** | Every suite: `ROOT = Path(__file__).resolve().parent.parent`, then `ROOT/scripts`, `ROOT/bin`, `ROOT/lib`, `ROOT/skills/wiki-issues/scripts/…`. |

### 5.2 Assessment — strengths
- **No test dependency** → runs on any `python3`; minimal supply-chain surface; CI-trivial.
- **Contract + internals** both covered (black-box real-caller path *and* white-box unit).
- **Deterministic, exit-code gated, single `make test`** → clean release gate.
- **Characterization oracles** make risky ports safe (proven by D1).
- **Drift guards** turn silent doc/version rot into test failures.

### 5.3 Assessment — the fragility the reorg exposes
1. **Root-path coupling (the load-bearing finding).** `Path(__file__).parent.parent` hardcodes "tests sit one directory under the root that also holds `scripts/bin/lib/skills`." Moving tests → `engineering/tests/` and code → `plugin/` **breaks every** `ROOT/…` reference (they'd resolve to `engineering/…`). Python scripts' own `../lib` resolution survives **only** because `scripts/ + lib/ + skills/` move together under `plugin/`.
2. **Evals are an ungated second tier.** `make test` green does **not** mean evals pass (they need a model). Silent today; must be stated so the gate isn't over-trusted.
3. **`marketplace.json` coupling** in `test_sync_versions.py` + `bin/release.py` (step 5 "sync marketplace") — the surface is dropped (Gate #3); both must lose the parity step.
4. **Cross-skill path load** — `run-lint.py` loads `skills/wiki-issues/scripts/lint-open-issues.py` by path (ADR-0002). Survives **iff** skills + scripts stay co-located under `plugin/` (they do).

### 5.4 Target test architecture (required changes)

1. **NEW `engineering/tests/_paths.py` — single source of truth for paths.** Resolves the repo/plugin root by walking up from `__file__` to the directory containing `plugin/.claude-plugin/plugin.json` (or `KM_PLUGIN_ROOT` env override):
   ```python
   # engineering/tests/_paths.py
   from pathlib import Path
   import os
   def _root(start):
       env = os.environ.get("KM_PLUGIN_ROOT")
       if env: return Path(env).expanduser().resolve()
       for p in [Path(start).resolve(), *Path(start).resolve().parents]:
           if (p / "plugin" / ".claude-plugin" / "plugin.json").exists():
               return p
       raise RuntimeError("repo root not found from " + str(start))
   REPO_ROOT   = _root(__file__)
   PLUGIN_ROOT = REPO_ROOT / "plugin"
   SCRIPTS, BIN, LIB, SKILLS = (PLUGIN_ROOT/"scripts", PLUGIN_ROOT/"bin",
                                PLUGIN_ROOT/"lib", PLUGIN_ROOT/"skills")
   ```
   Every suite replaces its `ROOT = …parent.parent` + `ROOT/scripts` with `from _paths import PLUGIN_ROOT, SCRIPTS, …`. Depth-independent → future moves don't break tests.
2. **Makefile dispatcher (root):** `python3 engineering/tests/test_x.py`; `lint` → `python3 plugin/scripts/run-lint.py`; `setup-dragonscale` → `python3 plugin/bin/setup-dragonscale.py`.
3. **`test_skill_count_ssot.py`:** glob → `git -C REPO_ROOT ls-files "plugin/skills/*/SKILL.md"`; name-list surface stays `CLAUDE.md` (root, unchanged).
4. **`test_sync_versions.py` + `bin/release.py`:** drop the marketplace parity step (version SSOT = `plugin.json` alone).
5. **`test_wiki_path_safety.py`:** drives `plugin/hooks/wiki-path-safety.py`; re-check the vault write-whitelist (`wiki/, scripts/, .vault-meta/, .claude/`) — the `scripts/` entry is vault-relative write policy, **not** the plugin's `scripts/`; confirm intent at exec.
6. **Two-tier statement in `engineering/test-architecture.md`:** Tier-1 deterministic (`make test`, gates release) vs Tier-2 behavioral evals (`engineering/evals/`, model-graded, optional CI job) — so "make test green" is never mistaken for "evals pass."

### 5.5 What does NOT need to change
- Plain-Python zero-dep style — keep (a strength, not debt).
- Black-box/white-box split — keep.
- `run-lint.py` internal importlib loads — unaffected (all inside `plugin/`).
- Characterization suites — keep as the refactor oracle for the move itself: run `make test` **before** and **after** the reorg; byte-identical pass = the move preserved behavior.

---

## 6. New files this reorg adds

| File | Purpose |
|---|---|
| `engineering/tests/_paths.py` | Depth-independent path SSOT resolver (§5.4.1) |
| `engineering/test-architecture.md` | Two-tier test doc + resolver contract (§5.4.6) |
| `.gitlab-ci.yml` (root, follow-up) | CI port; Tier-1 `make test` as the required job |

## 7. Acceptance hooks (fold into SPEC S10 + S11)
- Layout ACs: `plugin/.claude-plugin/plugin.json` exists; `skills/hooks/agents/scripts/lib/bin/references/_templates` are under `plugin/`; `tests/evals` under `engineering/`; **no `.claude/` dir inside `plugin/`**; README documents the git-subdir install.
- Test ACs: `make test` exits 0 from the **new** layout; no test contains `parent.parent` root-resolution (all via `_paths.py`); `test_skill_count_ssot` reads `plugin/skills/*/SKILL.md`; characterization suites pass byte-identically pre/post move.
