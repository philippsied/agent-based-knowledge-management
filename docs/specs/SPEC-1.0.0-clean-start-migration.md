# SPEC — 1.0.0 Clean-Start Migration

**Goal.** Recreate `agentic-knowledge-management` (v2.0.0, forked from `AgriciDaniel/claude-obsidian`)
as a fresh **`agentic-knowledge-steward` 1.0.0** in the empty GitLab repo `curated-agent-os/agentic-knowledge-steward`,
carrying only what matters, scrubbed of heritage, MIT/license notices consolidated into a single root `ORIGIN.md`.

**Inventory (per-file dispositions):** [`INVENTORY-clean-start.md`](../migration/INVENTORY-clean-start.md) — authoritative for *which* files.
This spec is authoritative for *acceptance* and *gates*.

**Scope of THIS run (locked 2026-07-06):** produce this spec + the inventory. **No target-repo mutation.**
Execution specs (S5–S8) define ACs for the *later* gated run; they are not executed now.

## Locked decisions

Identity: keep **"Philipp Sieder"** (strip `philippsied` handle/URLs only) ·
License: root **`LICENSE`** (MIT © Philipp Sieder) **+ `ORIGIN.md`** (license-bearing upstreams only) ·
Assets: **drop + de-embed** heritage gifs · Rebrand: `…-management` → **`agentic-knowledge-steward`**, version → **`1.0.0`**.

**Gate answers (2026-07-06):**
1. `dragonscale.md` feature rationale → **folded into the Gesamt-PRD** `agentic-wiki.md`; standalone dropped.
2. Learnings doc → renamed **`docs/LEARNINGS.md`**.
3. **No own marketplace** → `.claude-plugin/marketplace.json` **dropped** (plugin reachable only via external marketplaces).
4. External named patterns (Karpathy LLM-Wiki + autoresearch) → **integrated as owned principles** in `references/operational-rules/foundational-principles.md`; names scrubbed. `ORIGIN.md` keeps **license-bearing sources only** (see S9). Same rule for any workflow/skill that follows a named external pattern.

---

## Specs & binary acceptance criteria

Each AC is a command or a yes/no check. "PASS" requires the cited evidence.

### S1 — Inventory completeness
Every tracked source file has exactly one disposition with a rationale.
- **AC1.1** Every tracked path (`git ls-files | wc -l` == **206**) is classified in `INVENTORY-clean-start.md` — via a per-file row or an explicit directory-group rule; zero unclassified.
- **AC1.2** Every disposition ∈ {KEEP, SCRUB, TRANSFORM, DROP, NEW}.

### S2 — Heritage-scrub map is exhaustive & correct
Every heritage-token occurrence is routed: rebrand, strip, → `ORIGIN.md`, or legit-external-keep.
- **AC2.1** For each of the 47 trace files, the inventory names the token(s) and the action.
- **AC2.2** The legit-external allowlist (setup-vault plugin URLs; `yourname/your-vault`; kepano; `.gitignore` MIT/copyright comments) is enumerated and excluded from stripping.
- **AC2.3** *(exec-time)* After scrub, in the **target** tree:
  `rg -i 'AgriciDaniel|agricidaniel\.com|AI Marketing Hub|claude-obsidian|careerhackeralex|karpathy|SlRvb|philippsied|akm-marketplace|agent-based-knowledge-management|agentic-knowledge-management|1\.10\.1|youtube\.com/watch' --glob '!ORIGIN.md'` → **0 hits** (allowlisted external URLs excepted).

### S3 — `ORIGIN.md` consolidation (license-bearing sources only, mapped to components)
- **AC3.1** Root `ORIGIN.md` exists and names each **license-bearing** source with its license **and** the component it covers: claude-obsidian (MIT) → codebase lineage; visualize/careerhackeralex (MIT) → `skills/visualize/`; the 4 Obsidian plugins (MIT) → `setup-vault.py` downloads; SlRvb (GPL-2.0) → `css-snippets.md` *(documentary — no GPL file tracked; verify at exec whether `css-snippets.md` reproduces SlRvb CSS text vs. documents an owned callout style)*.
- **AC3.2** `ATTRIBUTION.md` is **absent** from the target tree.
- **AC3.3** `ORIGIN.md` contains **no** pattern-only / non-license credit (no "Karpathy", no "prior art" courtesy section) — those live in `foundational-principles.md` (S9). Matt Pocock handoff is not a tracked source → not in scope.
- **AC3.4** No tracked file other than `LICENSE` and `ORIGIN.md` contains a full license block (MIT/GPL text). Check: `rg -l 'Permission is hereby granted|GNU GENERAL PUBLIC' -g '!LICENSE' -g '!ORIGIN.md'` → **0**.

### S4 — License correctness (MIT compliance preserved)
- **AC4.1** `LICENSE` contains "Philipp Sieder", **not** "AgriciDaniel".
- **AC4.2** The upstream AgriciDaniel/claude-obsidian MIT copyright line is retained **in `ORIGIN.md`** (MIT §"retain the notice" satisfied — not silently dropped).

### S5 — Rebrand identity *(exec-time)*
- **AC5.1** `plugin/.claude-plugin/plugin.json`: `name == "agentic-knowledge-steward"`, `version == "1.0.0"`, no `philippsied` handle/URL, `homepage`/`repository` → GitLab, no `karpathy` keyword, and the description's "Based on Andrej Karpathy's LLM Wiki pattern" clause removed (→ principle, S9).
- **AC5.2** `.claude-plugin/marketplace.json` is **absent** (no own marketplace). `bin/sync-versions.py` + `tests/test_sync_versions.py` are updated to not require it (version SSOT = `plugin.json` alone); `.github/workflows/version-drift.yml` was already dropped.
- **AC5.3** `CHANGELOG.md` top entry is `[1.0.0]`; no `[2.0.0]`/`[1.x]` history retained.
- **AC5.4** `python bin/sync-versions.py --check` (or equivalent) reports version consistency at `1.0.0` against the reduced surface.

### S6 — Legacy-baggage drop *(exec-time)*
- **AC6.1** Every path in the inventory DROP set (**57** — the 56 baggage/planning files + `.claude-plugin/marketplace.json`) is **absent** from the target.
- **AC6.2** Every KEEP/SCRUB/TRANSFORM path is **present** (relocated per S10 — `plugin/…` or `engineering/…`); NEW files present: root `ORIGIN.md`, `plugin/references/operational-rules/foundational-principles.md`, `engineering/tests/_paths.py`, `engineering/test-architecture.md`; absent: `ATTRIBUTION.md`, `DECISION-LOG.md`, `dragonscale.md`, `marketplace.json`.
- **AC6.3** Cross-check: target `git ls-files | wc -l` ≈ **157** (206 − 57 DROP − 1 ATTRIBUTION-fold + 9 NEW; relocation into `plugin/`/`engineering/` does not change counts). Path-based ACs above are the gate; the number is a sanity check.

### S7 — Forensic Learnings doc *(exec-time)*
- **AC7.1** `docs/LEARNINGS.md` present in target (renamed from `DECISION-LOG.md`), scrubbed of heritage tokens (S2.3 applies). No stale `DECISION-LOG.md` remains; inbound refs (chiefly `CLAUDE.md`) repointed.
- **AC7.2** It contains the existing D1–D9 **plus** sections covering **security, performance, maintenance, and design-mistake** lessons distilled from the old history.
- **AC7.3** A refactoring-only trigger is enforced by **both**: a header banner in the doc **and** a rule in `CLAUDE.md` ("consult `docs/LEARNINGS.md` only during refactoring work"). It is **not** an always-on context load (no SessionStart hook references it).

### S8 — Clean-start integrity *(exec-time)*
- **AC8.1** Target working tree populated per inventory; `make test` exits **0** in the target.
- **AC8.2** Exactly **one** commit, tagged/message `1.0.0`, author **Philipp Sieder**.
- **AC8.3** **Not pushed.** `git -C <target> log origin/main..HEAD` errors / shows the commit is local (no remote ref). Pushes are G-push only.

### S9 — Pattern absorption (named external patterns → owned foundations) *(exec-time)*
Per gate answer #4: patterns the repo follows are integrated as **owned principles**, not name-credited heritage.
- **AC9.1** `references/operational-rules/foundational-principles.md` exists and states, de-personalized, at least: the **LLM-Wiki compounding-knowledge** principle (whole-vault concept) and the **autoresearch loop** principle (behind `skills/autoresearch/`).
- **AC9.2** `rg -i 'karpathy'` over the entire target tree (**including `ORIGIN.md`**) → **0 hits**. The name is gone; the principle remains as owned architecture.
- **AC9.3** Feature rationale is consolidated: `docs/prds/agentic-wiki.md` (the Gesamt-PRD) carries the DragonScale feature rationale; `docs/prds/dragonscale.md` is absent (folded).
- **AC9.4** `foundational-principles.md` is referenced from the `CLAUDE.md` "Conventions & Editing" map (single entry point), not always-on-loaded.

### S10 — Repo layout: `plugin/` + `engineering/` *(exec-time)*
Design + full mapping: [`LAYOUT-and-test-architecture.md`](../migration/LAYOUT-and-test-architecture.md).
- **AC10.1** `plugin/.claude-plugin/plugin.json` exists; `skills/`, `hooks/`, `agents/`, `scripts/`, `lib/`, `bin/`, `references/`, `_templates/` all live under `plugin/`.
- **AC10.2** `tests/` and `evals/` live under `engineering/`. No `tests/` or `evals/` at repo root.
- **AC10.3** **No `.claude/` directory inside `plugin/`** (would suppress skill discovery). Check: `test ! -e plugin/.claude`.
- **AC10.4** `README.md` documents the install path: external marketplaces must reference this plugin with `source.type = "git-subdir"`, `subdirectory = "plugin/"`.
- **AC10.5** Every hook/skill reference to a bundled script uses `${CLAUDE_PLUGIN_ROOT}/…` (no repo-root-relative script path). Check: `rg -n 'python3? +(\./)?(scripts|bin|lib)/' plugin/hooks plugin/skills` → 0 (all such refs go through `${CLAUDE_PLUGIN_ROOT}`).

### S11 — Test-design architecture *(exec-time)*
Review + target design: [`LAYOUT-and-test-architecture.md`](../migration/LAYOUT-and-test-architecture.md) §5.
- **AC11.1** `engineering/tests/_paths.py` exists and resolves `PLUGIN_ROOT` by walking up to `plugin/.claude-plugin/plugin.json` (or `KM_PLUGIN_ROOT` env).
- **AC11.2** **No** `engineering/tests/test_*.py` resolves paths via `Path(__file__)…parent.parent`; all use `_paths.py`. Check: `rg -l 'parent\.parent' engineering/tests` → 0.
- **AC11.3** `make test` exits **0** from the new layout (`python3 engineering/tests/test_*.py`; `lint` → `plugin/scripts/run-lint.py`).
- **AC11.4** `test_skill_count_ssot.py` reads `plugin/skills/*/SKILL.md`; still yields **15**.
- **AC11.5** The two characterization suites (`test_run_lint.py`, `test_wiki_path_safety.py`) pass **byte-identically pre- and post-move** — the move preserved behavior (run `make test` before reorg, capture, compare after).
- **AC11.6** `engineering/test-architecture.md` states the two tiers: Tier-1 deterministic (`make test`, gates release) vs Tier-2 model-graded evals (`engineering/evals/`, not in `make test`).

### S12 — Packaging, skill-integration & path decoupling *(exec-time)*
Design + caller graph: [`PACKAGING-and-skill-integration.md`](../migration/PACKAGING-and-skill-integration.md). Revises D7/D8 → new ADR.
- **AC12.1** No script under `plugin/**` resolves a shared dependency via repo-root `parent.parent`; shared access goes through `plugin/lib/plugin_root.py` (NEW) or `${CLAUDE_PLUGIN_ROOT}`.
- **AC12.2** Sole-owner scripts sit under their owning skill; the **lint subsystem is whole** under `plugin/skills/wiki-lint/scripts/` (`run-lint` + `lint-{orphans,terminology,title-overlap,deps,programs,rename}` + `tiling-check` — `lint-deps` included because `run-lint` folds it). `allocate-address`→`plugin/skills/wiki-ingest/scripts/` (sole writer), `boundary-score`→autoresearch, `wiki-prepass`/`rewrite-wikilinks`→wiki-ingest. `plugin/lib/` holds **only** import-only helpers: `vault_root.py`, `plugin_root.py`, `provision.py`.
- **AC12.3** `release.py` + `sync-versions.py` live under `engineering/`, **not** `plugin/`.
- **AC12.4** The `/wiki` skill exposes provision **and** reconcile; `plugin/bin/setup-*.py` delegate to `plugin/lib/provision.py` (NEW) — shared function, no copied logic.
- **AC12.5** `plugin/_templates/manifest.json` ships (CI-generated); `provision.reconcile` implements the 3 states incl. **no-clobber on locally-edited templates**; the lock is `.vault-meta/template-lock.json` in the vault (not in `${CLAUDE_PLUGIN_ROOT}`).
- **AC12.6** Every SKILL.md / hooks.json script reference uses `${CLAUDE_PLUGIN_ROOT}/…`. Check: `rg -n '\.\./(scripts|lib|bin)/' plugin/skills plugin/hooks` → 0.
- **AC12.7** *(latent bug, fix)* `autoresearch/SKILL.md`'s broken `scripts/lint/lint-deps.py` path (no such dir today → DAG validation silently skipped) is repointed to `${CLAUDE_PLUGIN_ROOT}/skills/wiki-lint/scripts/lint-deps.py` and resolves; a test asserts it. The `ai-secondbrain` provenance line in `lint-open-issues.py` is scrubbed (de-personalization). Check: `rg -n 'scripts/lint/' plugin` → 0.

---

## Gates

| Gate | Enters when | Exit criterion | Reversible? |
|------|-------------|----------------|-------------|
| **G-spec** *(this run's endpoint)* | Inventory + specs written | You approve the per-file dispositions + open items | Yes — nothing mutated |
| **G-exec** | G-spec green | S1–S7 executed into the **target working tree** (scrub, rebrand, ORIGIN.md, drops, learnings doc) | Yes — local only |
| **G-verify** | G-exec green | S8 ACs green (`make test` 0); **refute-judge** (2nd model) on S2–S7; **security-review** for secret/PII leakage + MIT compliance | Yes — pre-commit / local |
| **G-push** | G-verify green | *(separately, explicitly approved — each step)* ① old GitHub repo: push 52 commits → set **Private** archive; ② target: `git push` 1.0.0 to GitLab | **No — irreversible/outward** |

**Rules:** execution never crosses a red gate. Between green gates, run autonomously. Each **G-push** action is individually confirmed (irreversible, outward-facing) — not batched.

## Verification plan (S6 discipline — "detection is not a verdict")
- Scrub ACs (S2.3, S3.3) are **`rg` commands** run against the target tree — evidence, not assertion.
- `make test` exit code is the S8 oracle.
- A second model is prompted to **refute** each of S2–S7 against these ACs before G-verify closes.
- Preconditions checked at reliance: target repo empty (verified 2026-07-06), source tree clean, no secrets in the 52 archive commits (security-review before G-push ①).

## Out of scope (this migration)
Regenerating brand assets (Q4 = drop); porting CI to `.gitlab-ci.yml` (follow-up NEW); relocating `scripts/` under skills (D7 — record-only).
