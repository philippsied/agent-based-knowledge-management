# Packaging, Skill Integration & Path Decoupling

**For:** the `agentic-knowledge-steward` clean-start. **As-of:** 2026-07-06.
**Companions:** [`LAYOUT-and-test-architecture.md`](LAYOUT-and-test-architecture.md) · [`SPEC`](../specs/SPEC-1.0.0-clean-start-migration.md)
**Revises:** ADR-0002 (D7, colocate-under-skill) + ADR-0003 (D8, setup-stays-in-bin) — see §7.

Answers four questions: (1) which `bin`/`scripts`/`_templates` files move into skills vs a shared
lib for clean plugin deployment; (2) how to make setup a skill so updates flow through it; (3) whether
a template-guard makes sense; (4) how to decouple fixed paths so skills become reusable.

---

## 0. Deployment model (the constraints everything follows from)

| Fact (verified) | Consequence |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}` = install dir, **read-only at runtime, wiped on every version bump** | Plugin must never write into itself; nothing persistent lives there |
| `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/{id}/`) **survives updates** | Cross-update plugin state (rare here) goes here |
| The **user vault** (cwd / `KM_VAULT_PATH`) is the per-user state | Provisioned files + template-lock live in the vault, not the plugin |
| `skills/hooks/agents/commands` auto-discovered under plugin root; **`scripts/lib/bin` are not** | Non-standard dirs are referenced explicitly via `${CLAUDE_PLUGIN_ROOT}/…` |

**Design North Star:** the plugin ships read-only capability; the vault holds mutable state; the bridge
between them is resolved at runtime (`${CLAUDE_PLUGIN_ROOT}` for plugin code, `vault_root` for user data)
— never a hardcoded repo path.

---

## 1. Script ownership — where each file lands (Q1)

**Rule (cardinality + cohesion):**
- Referenced by **exactly one** skill → `skills/<skill>/scripts/` (colocate; the skill becomes self-contained).
- A **cohesive subsystem** (modules that import each other) → stays together under its owning skill, even if other skills *call* it.
- A **shared primitive** (used by ≥2 skills **and** by install tooling, or imported as a library) → `lib/`.

Caller graph (who *references* each script) → placement:

| Script | Referenced by (skills) | → Home under `plugin/` | Why |
|---|---|---|---|
| `run-lint.py` + `lint-deps/orphans/programs/rename/terminology/title-overlap.py` | wiki, wiki-lint, wiki-issues, autoresearch | **`skills/wiki-lint/scripts/`** | One lint subsystem — `run-lint` imports the `lint-*` as siblings (importlib). Splitting by caller would break sibling loads. Other skills *call* the aggregator; they don't own it. |
| `tiling-check.py` | wiki-lint | `skills/wiki-lint/scripts/` | Sole owner (DragonScale M3 semantic-tiling lint) |
| `boundary-score.py` | autoresearch | `skills/autoresearch/scripts/` | Sole owner (boundary-first topic selection) |
| `wiki-prepass.py`, `rewrite-wikilinks.py` | (ingest/refactor utilities) | `skills/wiki-ingest/scripts/` | Ingest-time helpers |
| `lint-open-issues.py` | wiki-issues | `skills/wiki-issues/scripts/` *(already there)* | Cross-loaded by `run-lint` via path (ADR-0002) |
| `convert-doc.py`, `finalize-md.py` | doc-pipeline | `skills/doc-pipeline/scripts/` *(already there)* | Sole owner |
| `allocate-address.py` | **writer:** wiki-ingest · **readers (`--peek`):** wiki-lint, setup-dragonscale, agents | **`skills/wiki-ingest/scripts/`** | Sole **writer** is ingest (§1a). Never imported — CLI only → belongs to its writer, not `lib/`. Readers cross-invoke `${CLAUDE_PLUGIN_ROOT}/skills/wiki-ingest/scripts/allocate-address.py --peek`. |
| `vault_root.py` | hook + all lint/doc scripts (IMPORT) | `lib/` *(already there)* | Pure imported resolver — genuine shared lib |
| **NEW** `plugin_root.py` | new (IMPORT) | `lib/` | Runtime plugin-root resolver (§4) — kills repo-root hardcoding |

> **`lib/` is only these two.** Both are **import-only** helpers (verified: `from vault_root import …`). Every other "shared-looking" script is a CLI with a real single owner (found by write-semantics + fold-membership, §1a). A CLI is never `lib/`; it lives with its owner and is cross-invoked via `${CLAUDE_PLUGIN_ROOT}`.

## 1a. Undocumented owners + a latent path bug (Q2: "gibt es einen undokumentierten Owner?")

Reference counts lie; **write-semantics + importlib-fold membership** give the true owner:

| Script | Looks like | **True owner** | Evidence |
|---|---|---|---|
| `allocate-address.py` | shared (4 domains) | **wiki-ingest** (sole writer) | Only ingest calls it bare (`ADDR=$(…allocate-address.py)`, "before writing a new page"); wiki-lint/setup/agents call only `--peek` (read). |
| `lint-deps.py` | autoresearch tool (name+caller) | **wiki-lint subsystem** (binding) + autoresearch consumer | `run-lint.py:76` folds it (`_load_lint_module("lint-deps")`, `collect()` at :385) → must stay a `run-lint` sibling. Autoresearch also invokes it standalone (`--ready`) → cross-invoke, not co-move. |

**Latent bug found** — `skills/autoresearch/SKILL.md` invokes `scripts/lint/lint-deps.py` (a `lint/` **subdir**), but **no `scripts/lint/` dir exists** (actual path is flat `scripts/lint-deps.py`). The upstream `ai-secondbrain` convention (`scripts/lint/…`, still named in `lint-open-issues.py:5`'s docstring) was flattened here but autoresearch's guard was never updated → `[ -x scripts/lint/lint-deps.py ]` silently fails → **DAG validation is skipped today**. The migration must repoint it to `${CLAUDE_PLUGIN_ROOT}/skills/wiki-lint/scripts/lint-deps.py` (AC12.7). *(Aside: scrub the internal `ai-secondbrain` provenance line — your own prior repo, not upstream, but a de-personalization target.)*

**Use-case frequency (drives what needs to be hot/cheap):**

| Module | Caller × trigger | Frequency |
|---|---|---|
| `vault_root` | PreToolUse hook (**every Write/Edit**) + every lint/doc script | **hottest** — per operation; keep import-light (stdlib only, D1 lesson) |
| `plugin_root` (NEW) | script startup | per-invocation, trivial |
| `allocate-address` | wiki-ingest **per new page** (write); `--peek` reads occasional | ingest-time, medium |
| lint subsystem (`run-lint`+checks) | "lint the wiki" ~every 10–15 ingests | low |
| `lint-deps` (extra) | autoresearch per DAG step (`--ready`) | low |
| `boundary-score` | autoresearch per topic-selection | low |

**`bin/` is not homogeneous — split it:**

| `bin/` file | Nature | → |
|---|---|---|
| `setup-vault.py`, `setup-dragonscale.py` | Provisioning (user-facing) | **Logic → `lib/provision.py`**, fronted by a **setup skill** (§2); keep a thin `bin/` CLI shim for CI/non-Claude |
| `release.py`, `sync-versions.py` | Dev-only release tooling | **`engineering/`** — NOT shipped to plugin consumers (`sync-versions` is near-obsolete after `marketplace.json` drop) |

> This resolves last turn's over-broad "all of `bin/` → `plugin/`": only provisioning is plugin-runtime; release tooling is engineering.

## 2. Setup as a skill, with update flow (Q2)

**Today:** `bin/setup-vault.py` *prints `cp -i` instructions* (verified: lines 187–190) — semi-manual, one-shot, no update path.

**Target:** provisioning becomes an idempotent library fronted by a skill, so first-run **and** updates go through the same entrypoint.

```
plugin/lib/provision.py         # idempotent engine: provision + reconcile (importable, hash-aware)
plugin/bin/setup-vault.py       # thin CLI: `python3 …/bin/setup-vault.py [vault]` → provision.main()  (CI / non-Claude)
plugin/skills/wiki/SKILL.md     # extend the existing /wiki skill: "set up | check | update the vault"
```

- **First run** (`/wiki` → "set up"): `provision.apply(vault)` copies `_templates/` + `references/operational-rules/` from `${CLAUDE_PLUGIN_ROOT}` into the vault, seeds `.vault-meta/`, writes the initial `template-lock.json` (§3).
- **Update run** (after a plugin version bump refreshes `${CLAUDE_PLUGIN_ROOT}`): the SAME skill calls `provision.reconcile(vault)` → diffs shipped vs vault vs lock → offers updates. No re-install, no manual `cp`.
- `/wiki` already advertises "scaffold a new vault or check setup status" — this extends it with the reconcile verb rather than adding a surface.

**Why a skill (not a bare CLI):** updates then ride the plugin's normal channel — user says "update my vault", Claude runs the bundled reconcile against the freshly-installed template versions. The CLI shim stays for CI.

## 3. Template-guard — yes, it fills a real gap (Q3)

There is **no** manifest / version / hash today, so stale vault templates are invisible. A guard is worth it — built as **skill-invoked reconcile**, not an always-on watcher.

**Mechanism:**
1. **Ship a manifest** — `plugin/_templates/manifest.json`: `{ "<template>": {"version": N, "sha256": "…"} }` (or per-file `template_version:` frontmatter). Generated in CI so it can't drift.
2. **Per-vault lock** — `.vault-meta/template-lock.json` in the **vault** (survives plugin updates, travels with the vault — unlike `${CLAUDE_PLUGIN_ROOT}`). Records the version/hash the user last accepted per template.
3. **3-state reconcile** (in `provision.reconcile`):

   | Shipped vs lock vs vault-file | State | Action |
   |---|---|---|
   | shipped == lock | **up-to-date** | nothing |
   | shipped > lock, vault-file == lock hash | **update available** | offer to overwrite; on accept, bump lock |
   | shipped > lock, vault-file ≠ lock hash | **conflict** (user edited locally) | show diff, **never clobber**; let user merge, then re-lock |

4. **Delivery — skill-primary + session hint (decided 2026-07-06):** the `/wiki` skill (or a small `template-check` verb) runs the reconcile on demand **and** a cheap SessionStart hook reads only the two JSONs and, if a mismatch exists, emits one line ("N template updates available — run /wiki update"). The hook does **only** the JSON compare — no per-Write scanning, no hashing on the hot path — consistent with the repo's "not always-on" discipline (LEARNINGS/foundational-principles are pull, not push). `${CLAUDE_PLUGIN_ROOT}` is not populated in SessionStart hooks (verified), so the hint reads the **vault** lock + a vault-cached manifest copy, not the plugin dir.

**Reject:** a filesystem watcher / per-tool-use hook that re-hashes templates on every edit — perf cost + noise for a rare event.

## 4. Decoupling fixed paths → reusable skills (Q4)

**Two distinct senses of "reusable" — name them, they need different things:**

| Sense | Definition | Requirement | Achievable here? |
|---|---|---|---|
| **Plugin-relocatable** | The whole plugin works whether at repo root, `repo/plugin/`, or `~/.claude/plugins/…` | No repo-root hardcoding; resolve via `${CLAUDE_PLUGIN_ROOT}` + `__file__` | **Yes — the real goal.** This is what the `plugin/` move needs anyway. |
| **Skill-liftable** | Copy one skill folder into another plugin and it runs standalone | Zero external deps, or vendored deps | **Only for self-contained skills** (see tiers) |

**Mechanisms (apply all):**
1. **`${CLAUDE_PLUGIN_ROOT}/…`** in every SKILL.md / hooks.json script reference — never `../../scripts/…`.
2. **`__file__`-relative** for a script's own siblings (already the norm).
3. **NEW `lib/plugin_root.py`** — runtime mirror of the tests' `_paths.py`: `CLAUDE_PLUGIN_ROOT` env → else walk up to `.claude-plugin/plugin.json`. Any shared-lib import resolves through it, so no script hardcodes `parent.parent`-as-repo-root.
4. **Skill self-containment tiers:**

   | Tier | Skills | Note |
   |---|---|---|
   | **Liftable** (colocated scripts or none, no shared lib) | `defuddle`, `obsidian-bases`, `obsidian-markdown`, `save`, `visualize`, `canvas`, `wiki-fold`, `doc-pipeline` | Can be reused in another plugin as-is |
   | **Relocatable** (need `lib/` primitives: `vault_root`, `allocate-address`, `plugin_root`) | `wiki`, `wiki-ingest`, `wiki-lint`, `wiki-query`, `wiki-issues`, `autoresearch`, `research-brief` | Portable *within* a plugin that ships `lib/`; document the `lib/` dependency in each SKILL.md |

   Making the DragonScale/wiki family fully liftable would require vendoring `lib/` into each — rejected (duplication/drift, the exact D6/D4 mistake). Relocatable + a documented `lib/` dependency is the right ceiling.

## 5. Resulting `plugin/` tree (script placement)

```
plugin/
├── lib/                       vault_root.py · plugin_root.py(NEW) · provision.py(NEW)   ← import-only helpers
├── bin/                       setup-vault.py · setup-dragonscale.py   (thin CLI shims → lib/provision)
├── skills/
│   ├── wiki-lint/scripts/     run-lint.py + lint-{orphans,terminology,title-overlap,deps,programs,rename}.py + tiling-check.py
│   ├── autoresearch/scripts/  boundary-score.py                       (cross-invokes wiki-lint/lint-deps)
│   ├── wiki-ingest/scripts/   allocate-address.py · wiki-prepass.py · rewrite-wikilinks.py
│   ├── wiki-issues/scripts/   lint-open-issues.py                     (cross-loaded by run-lint)
│   └── doc-pipeline/scripts/  convert-doc.py · finalize-md.py
└── _templates/                + manifest.json(NEW, CI-generated)
```
`engineering/` gains `release.py`, `sync-versions.py` (dev tooling, moved out of the plugin).

## 6. Test impact
Tests repoint script paths through `_paths.py` (LAYOUT §5.4): `PLUGIN_ROOT/skills/wiki-lint/scripts/run-lint.py`,
`PLUGIN_ROOT/skills/wiki-ingest/scripts/allocate-address.py`, `LIB/vault_root.py`, etc. — none via `PLUGIN_ROOT/scripts/…`.
`test_setup_provisioning.py` now targets `lib/provision.py` (+ the thin CLI). New: `test_template_guard.py` for the 3-state reconcile.
A regression test should assert the fixed `lint-deps` path resolves (guards the §1a latent-path bug from recurring).

## 7. Decisions this revises / raises

- **Revises D8 (ADR-0003, "setup stays in bin, install-time ≠ skill-runtime").** The update requirement makes setup a **skill capability**; logic moves to `lib/provision.py` fronted by `/wiki`, with a thin `bin/` CLI kept for CI. State this explicitly in the new ADR so the future repo doesn't "helpfully" re-fold it (the D8 lesson, applied to its own reversal).
- **Extends D7 (ADR-0002).** Finish the colocation D7 intended, with the **cohesion caveat**: the lint subsystem stays whole under `wiki-lint` (sibling importlib), and shared primitives go to `lib/` — not scattered by caller.
- **Confirm:** (a) lint subsystem whole under `wiki-lint` (recommended) vs strict per-caller split; (b) `allocate-address` in `lib/` as importable+CLI (recommended) vs under `wiki-ingest`; (c) template-guard = skill-primary + optional session hint (recommended) vs skill-only.

## 8. Acceptance criteria (fold into SPEC as S12)
- **AC12.1** No script under `plugin/**` resolves a shared dep via repo-root `parent.parent`; shared access goes through `lib/plugin_root.py` or `${CLAUDE_PLUGIN_ROOT}`.
- **AC12.2** Sole-owner scripts sit under their owning skill; the lint subsystem is whole under `skills/wiki-lint/scripts/` (incl. `lint-deps`, which `run-lint` folds); `allocate-address` under `skills/wiki-ingest/scripts/` (its sole writer). `lib/` contains **only** the import-only helpers `vault_root.py` + `plugin_root.py` (+ `provision.py`).
- **AC12.7** The `scripts/lint/lint-deps.py` broken path in `autoresearch/SKILL.md` is repointed to `${CLAUDE_PLUGIN_ROOT}/skills/wiki-lint/scripts/lint-deps.py` and resolves; the `ai-secondbrain` provenance line in `lint-open-issues.py` is scrubbed. A test asserts the path resolves.
- **AC12.3** `release.py` + `sync-versions.py` live under `engineering/`, not `plugin/`.
- **AC12.4** `/wiki` skill exposes provision **and** reconcile; `bin/setup-*.py` delegate to `lib/provision.py` (no logic duplication — diff the two entrypoints: shared function, not copy).
- **AC12.5** `_templates/manifest.json` ships (CI-generated); `provision.reconcile` implements the 3 states incl. **no-clobber on local edits**; lock lives at `.vault-meta/template-lock.json` in the vault.
- **AC12.6** Every SKILL.md / hooks.json script reference uses `${CLAUDE_PLUGIN_ROOT}/…`; `rg` for `\.\./(scripts|lib|bin)/` in `plugin/skills` + `plugin/hooks` → 0.
