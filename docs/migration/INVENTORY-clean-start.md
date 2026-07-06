# Clean-Start Migration — File-by-File Inventory

**Source repo:** `agentic-knowledge-management` (this repo, `main` @ `0415194`, 206 tracked files)
**Target repo:** `agentic-knowledge-steward` (GitLab `curated-agent-os/…`, empty, 0 commits)
**As-of:** 2026-07-06. **Companions:** [`SPEC`](../specs/SPEC-1.0.0-clean-start-migration.md) · [`LAYOUT-and-test-architecture.md`](LAYOUT-and-test-architecture.md) · [`PACKAGING-and-skill-integration.md`](PACKAGING-and-skill-integration.md)

Every one of the 206 tracked files is listed below with an explicit **disposition** and a
**rationale** (why it matters for the new repo / why it is baggage). Nothing is copied blind.

> **Target layout (see LAYOUT doc for the full map).** The dispositions below are **orthogonal to relocation**: a KEEP/SCRUB file also moves to its new home — plugin runtime → `plugin/**` (`.claude-plugin, skills, hooks, agents, scripts, lib, bin, references, _templates`); dev tooling → `engineering/**` (`tests, evals`); docs + Obsidian-vault skeleton + repo-meta stay at root. Disposition = *does it survive & what changes*; location = *where it lands*.

## Scope decisions locked (2026-07-06)

| # | Decision | Value |
|---|----------|-------|
| Q1 | This run's deliverable | **Inventory + specs only** — no target-repo mutation |
| Q2 | New identity | **Keep "Philipp Sieder"** as author; strip only old-repo URLs / handles / vanity links |
| Q3 | License layout | Real root **`LICENSE`** (MIT © Philipp Sieder, own code) **+ `ORIGIN.md`** for all upstream notices |
| Q4 | Heritage assets | **Drop + de-embed** the `claude-obsidian-*` / `welcome-canvas` gifs |

## Disposition legend

| Code | Meaning |
|------|---------|
| **KEEP** | Carry forward unchanged — no heritage trace, no edit needed |
| **SCRUB** | Carry forward, but edit to remove/replace heritage tokens (tokens listed) |
| **TRANSFORM** | Carry forward, substantially reworked (reset / rewrite / fold) |
| **DROP** | Do **not** carry to the clean-start repo (process history / legacy baggage) |
| **NEW** | Create fresh in the target (does not exist in source) |

**Rebrand token map** (applied wherever SCRUB says "rebrand"):
`agentic-knowledge-management` → `agentic-knowledge-steward` ·
`agent-based-knowledge-management` (old GitHub repo) → `agentic-knowledge-steward` ·
`akm-marketplace` → `aks-marketplace` · `github.com/philippsied/…` → `gitlab.com/curated-agent-os/agentic-knowledge-steward` ·
`v1.10.1` / `1.10.1` / `2.0.0` → `1.0.0`.

**Heritage-strip tokens** (removed everywhere except `ORIGIN.md`):
`AgriciDaniel`, `agricidaniel.com`, `AI Marketing Hub`, `claude-obsidian`, `careerhackeralex`,
`Karpathy`/`karpathy`, `SlRvb`, `philippsied` (handle/URL only — the display name "Philipp Sieder" **stays**),
the YouTube link, and the two gif filenames.

**Legit-external allowlist** (github/URLs that are NOT heritage — never scrub):
`github.com/zsviczian/…`, `github.com/Quorafind/…` (Obsidian plugin downloads in `setup-vault.py`);
`github.com/yourname/your-vault` (generic placeholder in `git-setup.md`);
`kepano/obsidian-skills` cross-ref (`obsidian-markdown/SKILL.md`); the MIT/copyright comment lines in `.gitignore`.

---

## Root (8)

| File | Disp. | Why / what to change |
|------|-------|----------------------|
| `README.md` | **TRANSFORM** | Highest trace density (57 hits). De-embed both gifs; strip AgriciDaniel/claude-obsidian/agricidaniel.com/YouTube/`philippsied` vanity + the upstream "multi-model" comparison; rebrand name; License section → point to `LICENSE` + `ORIGIN.md`. Core product front page — must survive, fully rewritten. |
| `CLAUDE.md` | **SCRUB** | Core harness the user wants carried clean. Rebrand 2× name; update wiki-path + "Cross-Project Access" example path; add "consult `DECISION-LOG.md` only during refactoring" rule (see S7). |
| `LICENSE` | **TRANSFORM** | Currently MIT © 2026 **AgriciDaniel** — that is upstream's copyright. Regenerate as MIT © 2026 **Philipp Sieder** (own code). The AgriciDaniel/claude-obsidian MIT notice moves to `ORIGIN.md`. |
| `ATTRIBUTION.md` | **TRANSFORM → DROP** | Its licensing content (Karpathy, SlRvb GPL-2.0, 4 Obsidian plugins MIT, claude-obsidian MIT) is the **seed for `ORIGIN.md`**. Once folded, the standalone file is removed (single licensing home per Q3). |
| `CHANGELOG.md` | **TRANSFORM** | Reset to a single `[1.0.0] – 2026-07-…` clean-start entry. Drop all v1.x/2.0.0 history and the `1.10.1`/`careerhackeralex` refs (version lineage = heritage). |
| `WIKI.md` | **SCRUB** | Vault landing page — keep. Strip Karpathy/AgriciDaniel/claude-obsidian/AI-Marketing-Hub; rebrand name. |
| `Makefile` | **SCRUB** | Core build entrypoint — keep. Rebrand 2× name. |
| `.gitignore` | **SCRUB** | Keep. Drop line 107 `claude-obsidian-archive/` (heritage path). Keep the MIT/copyright comment lines (legit notes about downloaded plugin binaries). |

## `.claude-plugin/` (2) — identity core

| File | Disp. | Why / what to change |
|------|-------|----------------------|
| `plugin.json` | **SCRUB** | Manifest identity. `name`→`agentic-knowledge-steward`; `version`→`1.0.0`; author **name** stays "Philipp Sieder" but strip the `philippsied` handle + `github.com/philippsied` profile URL (→ GitLab or remove `url`); `homepage`/`repository`→GitLab; drop `karpathy` keyword; description keep ("Claude + Obsidian" is generic). |
| `marketplace.json` | **DROP** | *(Gate #3)* No own marketplace — plugin reachable only via **external** marketplaces. Remove the file. **Coupling:** `bin/sync-versions.py` + `tests/test_sync_versions.py` must drop the marketplace parity check (version SSOT = `plugin.json` alone). `version-drift.yml` is already dropped. |

## `.github/workflows/` (3)

| File | Disp. | Why |
|------|-------|-----|
| `release.yml`, `test.yml`, `version-drift.yml` | **DROP** | GitHub Actions do **not** run on GitLab — dead config on the target. Their intent (test + version-drift + release gates) is preserved by `make test` and `bin/release.py`. **Follow-up NEW:** port to `.gitlab-ci.yml` (flagged, not blocking this migration). |

## `.raw/` · `.vault-meta/` · `wiki/` (3)

| File | Disp. | Why |
|------|-------|-----|
| `.raw/.gitkeep` | **KEEP** | Empty immutable-source dir skeleton. Vault content is gitignored → clean-start ships **no demo baggage**. |
| `.vault-meta/tiling-thresholds.json` | **KEEP** | DragonScale tiling config — live feature data. |
| `wiki/.gitkeep` | **KEEP** | Empty vault skeleton (all `wiki/` content gitignored, incl. the heritage gifs — hence "de-embed refs", not "drop files"). |

## `_templates/` (13)

**KEEP all** (Obsidian Templater + eval/config templates — vault infrastructure).
Exception: `research-queue.md` → **SCRUB** (2× rebrand name). The other 12
(`comparison`, `concept`, `entity`, `eval-config-poll.json`, `judge-prompt-output-only`,
`judge-prompt-structured-trace`, `labeling-rubric`, `open-issues`, `pending-commits`,
`question`, `research-brief`, `source`) carry no heritage → **KEEP**.

## `agents/` (2)

| File | Disp. | Why |
|------|-------|-----|
| `wiki-ingest.md`, `wiki-lint.md` | **KEEP** | Subagent definitions — no heritage traces found. |

## `bin/` (4) — split by nature (see [PACKAGING](PACKAGING-and-skill-integration.md) §1–2)

| File | Disp. → home | Why / what to change |
|------|-------|----------------------|
| `setup-vault.py` | **SCRUB → `plugin/bin/`** (thin CLI) | Rebrand name. **Keep** zsviczian/Quorafind download URLs (legit). Provisioning **logic → NEW `plugin/lib/provision.py`**; this becomes a thin CLI shim; the `/wiki` skill fronts provision+reconcile (S12, revises D8). |
| `setup-dragonscale.py` | **SCRUB → `plugin/bin/`** (thin CLI) | Rebrand; delegate to `lib/provision.py` DragonScale path. |
| `release.py` | **KEEP → `engineering/`** | Dev-only release tooling (fixed lint-gate D5). Not shipped to plugin consumers. |
| `sync-versions.py` | **KEEP → `engineering/`** *(near-obsolete)* | Mirrored `plugin.json`→`marketplace.json`; marketplace dropped (Gate #3) → reduce to a `plugin.json`-only version check or retire. Dev tooling, not plugin. |

## `docs/` — loose (8)

| File | Disp. | Why |
|------|-------|-----|
| `DECISION-LOG.md` → **`LEARNINGS.md`** | **TRANSFORM** | *(Gate #2)* **The one artifact meant to survive.** Renamed `docs/LEARNINGS.md`; becomes the forensic learnings doc (S7): scrub `1.10.1`/name; add **security / performance / maintenance / design-mistake** dimensions; refactoring-only trigger banner; repoint inbound refs (chiefly `CLAUDE.md`). |
| `install-guide.md` | **TRANSFORM** | 2nd-highest trace (39 hits). Rewrite install flow for the GitLab repo; repoint every `github.com`/`philippsied`/old-name to the new coordinates. |
| `dragonscale-guide.md` | **SCRUB** | Keep (user-facing feature guide). Rebrand + strip `1.10.1` version anchor. |
| `bilingual-terminology-policy.md` | **SCRUB** | Keep (durable policy). Strip claude-obsidian/Karpathy example mentions. |
| `influence-log.md` | **DROP** | Pure heritage — tracks upstream influence. |
| `upstream-merge-log.md` | **DROP** | Pure heritage — fork/upstream merge log. |
| `upstream-roadmap.md` | **DROP** | Pure heritage — upstream's roadmap. |
| `eval-results-trend.md` | **DROP** | Historical eval-trend data from the old repo (regenerates from fresh runs). |

## `docs/adr/` (5) — **KEEP all**

Durable architecture rationale ("why it is the way it is") — directly serves the
"don't repeat mistakes" mandate. `0001-delete-commands-skills-only.md` → **SCRUB** (`1.10.1`×1);
`0002`…`0005` → **KEEP** (verify the lone `mit` mention in 0002 is prose, not a license claim).

## `docs/audit/` (11) — **DROP all**

`2026-07-01/{AUDIT-REPORT,a-counter,b-adr-status,c-wiki-issues,d-cross,structural-evidence,v1-goldplating,v2-gaps,v3-sequencing}.md`,
`2026-07-02/{fup-5-refute-judge,multi-agent-salvage}.md`.
Process audit history of the old repo. Every durable lesson is already distilled into
`DECISION-LOG.md` (D1–D9) + the ADRs. The `multi-agent-salvage` provenance map is captured by DECISION-LOG **D6**.

## `docs/manifests/` (4) — **DROP all**

`cmd-script-consolidation.{json,md}`, `dragonscale-agentic-wiki-followups.{json,md}`.
Cross-session work-tracking manifests for **completed** work.

## `docs/plans/` (9) — **DROP all**

`PHASE2-run-lint-pytest-spec`, `PLAN-cmd-script-consolidation-{commands,dragonscale,ingest,lint,setup}`,
`PLAN-sh-to-py-full-migration`, `PLAN-visualize-integration`, `PLAN_v1.10.0-soft-path-safety-hook`.
Implementation plans for work already shipped; durable outcomes live in ADRs + DECISION-LOG.

## `docs/prds/` (3)

| File | Disp. | Why |
|------|-------|-----|
| `agentic-wiki.md` | **TRANSFORM** | *(Gate #1)* The **Gesamt-PRD**. Keep + SCRUB `1.10.1`, **and absorb the DragonScale feature rationale** so all feature rationale lives in one product doc. |
| `dragonscale.md` | **TRANSFORM → DROP** | *(Gate #1)* Fold its durable feature rationale into `agentic-wiki.md`; drop the standalone. |
| `cmd-script-consolidation.md` | **DROP** | PRD for a completed **refactor** (process, not a feature) — lessons live in ADRs + `LEARNINGS.md`. |

## `docs/specs/` (10) — **DROP all**

`SPEC-2.0.0-consolidation`, `SPEC-cmd-script-consolidation-{commands,dragonscale,ingest,lint,setup}`,
`SPEC-fup-5-skill-count-ssot`, `SPEC-visualize-wiki-integration`, `SPEC-wiki-issues`, `SPEC_v1.10.0-soft-path-safety-hook`.
Specs of **completed** work. (This migration's own spec is a **source-repo-only** artifact — see below — and is itself not shipped to the target.)

## `docs/tasks/` (6) · `docs/templates/` (1) · `docs/test-designs/` (1) · `docs/releases/` (1) — **DROP**

`tasks/*` (6, completed-work breakdowns); `templates/open-issues.md` (duplicate of `_templates/open-issues.md` — dedupe);
`test-designs/cmd-script-consolidation.md`; `releases/v1.6.0.md` (old release notes).

## `evals/` (20) — **KEEP all**

`run.py`, `score-summary.py`, `README.md` + three fixture cases
(`ingest/case-001-*` ×5, `lint/case-001-*` ×6, `query/case-001-*` ×6).
Eval harness + fixtures that validate the shipped skills — no heritage traces. **KEEP**.

## `hooks/` (3)

| File | Disp. | Why |
|------|-------|-----|
| `hooks.json` | **KEEP** | Hook-config SSOT. |
| `wiki-path-safety.py` | **KEEP** | Security hook (43/43 parity oracle, D1). |
| `README.md` | **SCRUB** | Rebrand 2× name. |

## `lib/` (1) · `scripts/` (12) — **KEEP all content; relocate by owner** (see [PACKAGING](PACKAGING-and-skill-integration.md) §1)

No heritage traces → all **KEEP**, but each moves to its owner (finishing D7 with the cohesion caveat):

| Script(s) | → home |
|---|---|
| `run-lint` + `lint-deps/orphans/programs/rename/terminology/title-overlap` + `tiling-check` | `plugin/skills/wiki-lint/scripts/` (lint subsystem — kept whole for sibling importlib) |
| `boundary-score` | `plugin/skills/autoresearch/scripts/` (sole owner) |
| `allocate-address`, `wiki-prepass`, `rewrite-wikilinks` | `plugin/skills/wiki-ingest/scripts/` — `allocate-address`'s **sole writer is wiki-ingest** (readers use `--peek` cross-invoke); never imported → not `lib/` |
| `vault_root.py`, NEW `plugin_root.py`, NEW `provision.py` | `plugin/lib/` — **import-only** helpers; the entire shared lib is just these |

> **Fix during move (latent bug, [PACKAGING §1a](PACKAGING-and-skill-integration.md#1a-undocumented-owners--a-latent-path-bug-q2-gibt-es-einen-undokumentierten-owner)):** `autoresearch/SKILL.md` calls `scripts/lint/lint-deps.py` — that `lint/` subdir does **not** exist → the guard silently skips DAG validation today. Repoint to `${CLAUDE_PLUGIN_ROOT}/skills/wiki-lint/scripts/lint-deps.py` (S12/AC12.7). Also scrub the `ai-secondbrain` provenance line in `lint-open-issues.py`.

## `references/operational-rules/` (14) — **KEEP all**

`README`, `agent-principles`, `architecture-defaults`, `atomic-tasks-and-commits`, `code-quality`,
`communication`, `git`, `identifiers`, `project-locality`, `resumption`, `sandbox`, `security`, `testing`, `workflow`.
The rules harness the user explicitly wants carried clean — no heritage traces. **KEEP**.

## `skills/` (44 across 15 skills) — **KEEP all skills; SCRUB the heritage-bearing files**

| File | Disp. | Token(s) / action |
|------|-------|-------------------|
| `autoresearch/SKILL.md` | **SCRUB** | rebrand name; "Karpathy's autoresearch pattern" → reword as the owned **autoresearch loop** principle (name scrubbed; principle in `foundational-principles.md`, S9) |
| `canvas/SKILL.md` | **SCRUB** | strip AgriciDaniel; github example |
| `canvas/references/canvas-spec.md` | **SCRUB** | example node `github.com/karpathy` → neutral; "AI Marketing Hub" example → neutral brand |
| `research-brief/SKILL.md` | **SCRUB** | rebrand name ×3 |
| `research-brief/references/conventions.md` | **SCRUB** | rebrand name ×3 |
| `research-brief/references/brief-skeleton.md` | **SCRUB** | rebrand name |
| `visualize/SKILL.md` | **SCRUB** | `author: careerhackeralex` → remove (non-standard field) ; MIT credit → `ORIGIN.md` |
| `visualize/references/anthropic-skill-guide-notes.md` | **SCRUB** | license/MIT mention → `ORIGIN.md` if attribution, else keep prose |
| `wiki/SKILL.md` | **SCRUB** | strip AgriciDaniel / AI Marketing Hub |
| `wiki/references/css-snippets.md` | **SCRUB** | SlRvb GPL-2.0 credit → `ORIGIN.md`; keep the snippet documentation |
| `doc-pipeline/scripts/convert-doc.py` | **SCRUB** | rebrand name |
| `doc-pipeline/scripts/finalize-md.py` | **SCRUB** | rebrand name |
| `wiki/references/git-setup.md` | **KEEP** | `yourname/your-vault` placeholder is legit |
| `obsidian-markdown/SKILL.md` | **KEEP** | `kepano/obsidian-skills` cross-ref is legit |
| *all other `skills/**` (≈30 files)* | **KEEP** | `defuddle`, `obsidian-bases`, `save`, `wiki-fold/*`, `wiki-ingest`, `wiki-issues/*`, `wiki-lint`, `wiki-query`, remaining `wiki/references/*`, `visualize/references/*`, `autoresearch/{evals,references}`, `research-brief/{evals,preflight}` — no heritage traces |

## `tests/` (14) — **KEEP all**

`test_{allocate_address,boundary_score,lint_orphans,lint_terminology,lint_title_overlap,open_issues,release_gate,run_lint,setup_provisioning,skill_count_ssot,sync_versions,tiling_check,vault_root,wiki_path_safety}.py`.
The suite validates the clean-start tree. `test_skill_count_ssot.py` guards skill **names/count** (15), **not** the brand — so the rebrand does not touch it. Verify at exec that no assertion is brand-coupled.

---

## NEW files (create in target)

| File | Contents |
|------|----------|
| `ORIGIN.md` (root) | Home for **license-bearing** upstreams only, each mapped to its component: claude-obsidian **MIT** (AgriciDaniel) → codebase lineage; visualize skill **MIT** (careerhackeralex) → `skills/visualize/`; 4 Obsidian plugins **MIT** (liamcain, Quorafind, zsviczian, noatpad) → `setup-vault.py` downloads; SlRvb CSS **GPL-2.0** → `css-snippets.md` (documentary — no GPL file tracked/shipped). **No** Karpathy / prior-art / Matt-Pocock section (Karpathy → principles per Gate #4; Matt Pocock is not a tracked source). |
| `plugin/references/operational-rules/foundational-principles.md` | *(Gate #4)* Owned theoretical foundations, de-personalized: the **LLM-Wiki compounding-knowledge** principle and the **autoresearch loop** principle (patterns formerly credited to Karpathy), plus a pointer to DragonScale as an owned mechanism. Referenced from `CLAUDE.md` "Conventions & Editing"; not always-on. |
| `engineering/tests/_paths.py` | *(reorg)* Depth-independent path SSOT — resolves `PLUGIN_ROOT` by walking up to `plugin/.claude-plugin/plugin.json`. Replaces the `parent.parent` root-coupling in all 14 suites (LAYOUT §5.4). |
| `engineering/test-architecture.md` | *(reorg)* Two-tier test doc: Tier-1 deterministic `make test` vs Tier-2 model-graded evals. |
| `plugin/lib/plugin_root.py` | *(packaging)* Runtime plugin-root resolver (`${CLAUDE_PLUGIN_ROOT}` → walk to `.claude-plugin/`) so shared-lib access never hardcodes repo-root (S12). |
| `plugin/lib/provision.py` | *(packaging)* Idempotent, hash-aware provision+reconcile engine; fronted by `/wiki`, called by the thin `bin/setup-*` CLIs (S12, revises D8). |
| `plugin/_templates/manifest.json` | *(packaging)* CI-generated per-template version+sha256 — the template-guard's shipped side (S12). |
| `engineering/tests/test_template_guard.py` | *(packaging)* Guards the 3-state reconcile incl. no-clobber-on-local-edit. |
| `docs/adr/0006-packaging-and-skill-setup.md` | *(packaging)* Records the D7-finish + D8-reversal (setup→skill) so the future repo doesn't re-fold it. |
| `.gitlab-ci.yml` (root) | *(follow-up, non-blocking)* CI port of the dropped GitHub Actions; Tier-1 `make test` as required job. Root-level (GitLab requirement). |

## Source-repo-only artifacts (this planning bundle — NOT shipped to target)

- `docs/specs/SPEC-1.0.0-clean-start-migration.md` — the spec/AC/gate bundle.
- `docs/migration/INVENTORY-clean-start.md` — this file.

These live with the **archive** (old repo → Private) as the migration recipe; they are consumed once and are in the target's implicit DROP set.

---

## Arithmetic (for the S6 acceptance criterion)

| | Count |
|---|------:|
| Source tracked files | 206 |
| DROP (baggage + `marketplace.json`) | −57 |
| ATTRIBUTION.md folded → ORIGIN.md | −1 |
| NEW `ORIGIN.md` + `foundational-principles.md` | +2 |
| NEW `engineering/tests/_paths.py` + `engineering/test-architecture.md` | +2 |
| NEW packaging: `plugin_root.py` + `provision.py` + `_templates/manifest.json` + `test_template_guard.py` + `adr/0006` | +5 |
| `DECISION-LOG.md`→`LEARNINGS.md` rename · relocation into `plugin/`+`engineering/`+skill-owners | ±0 |
| **Expected target tracked files** | **≈ 157** |

DROP (57) = `.github/workflows`(3) + docs loose(4) + audit(11) + manifests(4) + plans(9) + prds(2: `cmd-script-consolidation` + folded `dragonscale`) + specs(11) + tasks(6) + templates(1) + test-designs(1) + releases(1) + migration(3) + `.claude-plugin/marketplace.json`(1) = **57**.
The extra 4 vs. the `ff6ee8f` snapshot are this SDD bundle itself (`docs/specs/SPEC-1.0.0` + `docs/migration/`×3), added in `0415194` — planning artifacts, not shipped.
The S6 AC is **path-based** (every DROP path absent, every KEEP/SCRUB/TRANSFORM path present, both NEW files present, `ATTRIBUTION.md`/`DECISION-LOG.md`/`dragonscale.md`/`marketplace.json` absent) — the ≈157 figure is a cross-check, not the gate.

## Resolved at G-spec (2026-07-06)

1. `dragonscale.md` → **fold feature rationale into the Gesamt-PRD** `agentic-wiki.md`; drop standalone.
2. Learnings doc → **`docs/LEARNINGS.md`**.
3. **No own marketplace** → drop `marketplace.json`; reachable via external marketplaces only.
4. Named external patterns → **integrate as owned principles** (`foundational-principles.md`), names scrubbed; `ORIGIN.md` = license-bearing sources only. Rule generalizes to every workflow/skill that follows a named external pattern.
