# Decision Log — agentic-knowledge-management

**What this is.** The durable, human-authored record of every significant *decision* and every
*reversal / dead-end* taken while building this plugin. It is the ONE record intended to survive the
pending **history-wipe migration** (this repo will be re-created as a fresh git repo with a single
squashed root commit — all commit history is discarded). Nothing else carries the *why* across that
boundary.

**Mandate.** *"Behobene Fehler und Irrwege nicht reproduzieren"* — the future repo must not
re-introduce a fixed error or re-walk an abandoned path. Every entry therefore makes the **lesson**
explicit: what was tried, why it was chosen or reversed, and what NOT to do again.

**Relationship to other docs.** This is the companion to [`CHANGELOG.md`](../CHANGELOG.md):
the CHANGELOG records *what changed* (user-facing, per release); this log records *why* and captures
*reversals / rejected alternatives* the CHANGELOG omits. Rationale detail lives in the ADRs / plans /
specs — this log references them **by path** and never duplicates their bodies. When an entry and a
referenced doc disagree, the doc is authoritative for detail; this log is authoritative for the
one-line lesson.

**As-of date:** 2026-07-03. All dates are absolute (YYYY-MM-DD).

---

## Decisions & reversals

### D1 — Full `.sh` → `.py` migration (shell wrappers removed)

- **Decision:** Port every tracked shell script (15 `.sh` files) to pure Python and make the `.py`
  the direct entrypoint; delete the shell wrappers/shims entirely.
- **What was tried / prior state:** The toolchain was shell + Python side by side — thin `.sh` shims
  (`scripts/run-lint.sh`, `scripts/allocate-address.sh`, `lib/vault_root.sh`) fronting Python twins,
  plus standalone shell installers/hooks (`bin/setup-*.sh`, `bin/release.sh`, `bin/sync-versions.sh`
  with a `jq` dependency, `hooks/wiki-path-safety.sh`, doc-pipeline stages, `evals/run.sh`).
  Dual surfaces meant behavior drift and a `jq` external dependency.
- **Why chosen:** One language for maintainability; drop the `jq` dependency (stdlib `json`);
  `run-lint.py` folds its six `lint-*.py` checks in-process (imported `collect*` entrypoints, no
  subprocess) with byte-identical output. `hooks/wiki-path-safety.sh` was security-critical — its
  port required 1:1 parity (**43/43** characterization cases) before the `hooks.json` cutover.
- **Current state (2026-07-02):** `run-lint`, `allocate-address` and the aggregator ported and made
  direct entrypoints; `Makefile`, CI, `bin/release.py`, `bin/setup-dragonscale.py`, the wiki-lint /
  wiki-ingest skills+agents, and `docs/dragonscale-guide.md` repointed to `.py`. `run-lint.sh`,
  `allocate-address.sh` and `tests/test_run_lint.sh` removed. Feature-detection guards switched from
  `[ -x …sh ]` to `[ -f …py ]` (a missing port disables the optional path instead of silently
  passing). Migration is tracked as "in progress" in the CHANGELOG.
- **Lesson — do not repeat:** Do not re-introduce shell shims that duplicate a Python twin — one
  language, one entrypoint. A missing optional tool must *disable* a path, never silently pass
  (`-f py`, not `-x sh`). For the security hook, the shell truth-table test IS the parity oracle:
  never cut over `hooks.json` before the port reproduces every case; keep the hook import-light
  (stdlib only) because it runs on every Write/Edit and pays Python cold-start on the hot path.
- **Refs:** `docs/plans/PLAN-sh-to-py-full-migration.md`; CHANGELOG `[2.0.0]` (Changed + Removed).

### D2 — Commands deleted → the plugin is skills-only

- **Decision:** Delete all 7 `commands/` slash-command files; the plugin exposes behavior only
  through `skills/` (model-invoked).
- **What was tried / prior state:** Two invocation surfaces coexisted — `commands/` (`/slash`,
  user-invoked) and `skills/` (model-invoked). 5 of the 7 commands were thin routers duplicating a
  same-named skill; 2 were substantive (`fix-issues` ~211 lines, `handoff` ~126 lines). Two surfaces
  → logic drift + double maintenance. `plugin.json` / `marketplace.json` never enumerated commands,
  so deletion needed no manifest change.
- **Why chosen:** One source of behavior, no drift, smaller maintenance surface. Cost accepted:
  `/slash` UX is gone (trigger via natural language / skill auto-trigger), and every command's
  behavior had to be proven present in a skill *before* deletion (coverage-before-delete is
  mandatory).
- **Current state (2026-07-02):** All 7 command files removed (executed as FUP-4). The 2 substantive
  commands became the `wiki-issues` skill; the 5 thin wrappers were already backed by their
  same-named skills (`wiki`, `save`, `canvas`, `autoresearch`, `doc-pipeline`). Breaking change vs
  `v1.10.1`; CHANGELOG carries the user migration note (audit V-3).
- **Lesson — do not repeat:** Do not maintain a thin `/command` that only routes to a same-named
  skill — it is pure drift surface. Never delete a command until a skill demonstrably covers its
  behavior (coverage matrix first). When a released plugin loses a surface, ship the migration note.
- **Refs:** `docs/adr/0001-delete-commands-skills-only.md`; CHANGELOG `[2.0.0]` (Removed, FUP-4);
  coverage matrix `skills/wiki-issues/references/coverage-matrix.md`.

### D3 — Canonical address-counter start value (off-by-one bugfix)

- **Decision:** The DragonScale Mechanism-2 address counter holds "next address," is **seeded at
  `1`**, and yields `c-000001` as the first allocation.
- **What was tried / prior state:** `bin/setup-vault.py` seeded the counter at `0`, so the first
  allocation was `c-000000` — an off-by-one against the documented "starts at 1" contract. The bug
  was **silent**: the allocator's `[0-9]+` check accepts `0` and exits 0, so nothing errored (it is a
  silent off-by-one, not an exit-3 guard).
- **Why chosen (over alternatives):** Fixing the seed literal (`0` → `1`) is the smallest possible
  change surface — one line, no allocator changes. *Rejected:* seeding `0` as canonical (keeps the
  `c-000000` off-by-one and forces rewriting the guide/PRD contract); changing the allocator to
  pre-increment (larger blast radius on shipped Mechanism-2 semantics, touches the allocator + tests
  + `--peek`/`--rebuild` invariants, and shifts every existing vault's counter by one).
- **Current state (2026-07-02):** Fixed 2026-07-01 (FUP-2): `bin/setup-vault.py` seed `0` → `1`;
  `tests/test_setup_provisioning.py` asserts the first allocation is `c-000001` (9 checks green). A
  vault that already allocated `c-000000` needs a one-time `--rebuild` / migration note (believed
  rare).
- **Lesson — do not repeat:** Never re-seed the counter at `0` — it silently reproduces `c-000000`
  (no guard catches it). Keep the "counter = next address, seeded 1" contract as the single source
  of truth; prefer the one-line seed fix over re-architecting allocator semantics.
- **Refs:** `docs/adr/0004-canonical-address-counter-start.md` (FUP-2);
  `tests/test_setup_provisioning.py`.

### D4 — `visualize`: integrate as the 15th skill (NOT exclude) + skill-count SSOT guard

- **Decision:** Resolve the 14-vs-15 skill-count ambiguity by **integrating** `skills/visualize/` as
  the 15th tracked skill (not excluding it), making **15** the canonical count everywhere, and adding
  a test guard that fails on future drift.
- **What was tried / prior state:** `skills/visualize/` sat untracked on `main`; prior sessions had
  said "leave it," so the true count was ambiguous (some surfaces said 14, some 15, some — stale
  FUP-4 residue in the then-present `AGENTS.md`/`GEMINI.md` — said 13). No mechanism prevented the
  numbers from diverging across README / CLAUDE.md / PRD / copilot docs.
- **Why chosen:** Integrating captures the skill's value and collapses the ambiguity to a single
  number; a plain-Python guard wired into `make test` (mirroring the FUP-2 test pattern) makes drift
  a test failure instead of a silent doc rot. No new ADR was cut — rationale lives in the SPEC + the
  PRD risk-note resolution (decision locked by user 2026-07-02).
- **Current state (2026-07-02):** `visualize` shipped as the 15th skill; all count/name surfaces
  reconciled to 15; `tests/test_skill_count_ssot.py` guards the numeric + name-list surfaces.
  Refute-judge PASS; manifest `fup-5 = verified` (commit `e73ce31`).
- **Lesson — do not repeat:** Do not leave a real skill untracked "for later" — the count then drifts
  across every doc that hard-codes it. A count duplicated across N docs needs a single-source guard,
  or it silently diverges (this is exactly what happened while the count lived only in prose).
- **Refs:** `docs/plans/PLAN-visualize-integration.md`; `docs/specs/SPEC-fup-5-skill-count-ssot.md`;
  `tests/test_skill_count_ssot.py`; commit `e73ce31`.

### D5 — Release lint-gate trap (release was structurally un-cuttable) — FIXED this session

- **Decision:** Scope the `bin/release.py` lint gate to the plugin **distribution**; do not gate the
  release on working-vault / demo-content lint quality.
- **What was tried / prior state:** `bin/release.py` blocked the release when `run-lint --json`
  reported `totals.error != 0`. But `scripts/run-lint.py` lints the **working vault** (`wiki/`),
  which carries 182 pre-existing demo-content findings and is **not part of the shipped plugin** —
  `run-lint` scans zero distributed files and exits 0 by design. So the gate coupled the release to
  content that isn't distributed, making **v2.0.0 structurally un-cuttable** (`make release` aborted
  at the gate every time). An earlier framing ("inject an error into a distributed file to test the
  gate") was itself based on a wrong assumption about run-lint's scope and was discarded.
- **Why fixed this way:** `lint_gate()` now excludes working-vault findings (distribution scan = 0
  run-lint files) and blocks **only** when run-lint itself cannot run (non-zero rc / unparseable JSON
  / missing totals). Distribution correctness stays gated by `make test`, which is the right gate for
  shipped code. Mechanism documented in the `lint_gate()` docstring.
- **Current state (2026-07-02, commit `b44056e`):** FIXED. Current tree (182 vault findings) → gate
  PASSES; gate still BLOCKS on the three run-lint failure modes. Regression test
  `tests/test_release_gate.py` (`make test-release-gate`, wired into `make test`). No `v2.0.0` tag cut
  (that is a later session).
- **Lesson — do not repeat:** Never gate a *distribution* release on *working-vault / demo-content*
  quality — verify first whether a linter even scans shipped files before wiring it into the release
  gate. A gate should block on "the check couldn't run," not on out-of-distribution content noise.
- **Refs:** `docs/specs/SPEC-2.0.0-consolidation.md` (S4); `bin/release.py` (`lint_gate()`);
  `tests/test_release_gate.py`; commit `b44056e`. (Supersedes the earlier
  `release-lint-gate-blocks-on-working-vault.md` memory, now resolved.)

### D6 — Multi-agent surfaces removed → the plugin is Claude-only — DONE this session

- **Decision:** Reduce the plugin to Claude-only; remove all cross-agent bootstrap surfaces.
- **What was tried / prior state:** The plugin shipped `AGENTS.md`, `GEMINI.md`,
  `.github/copilot-instructions.md`, and `bin/setup-multi-agent.py`, advertising Codex / Gemini /
  Cursor / Windsurf / OpenCode support. These cross-agent files **duplicated** conventions and
  drifted independently — their skill tables were doubly stale (13 rows: missing both `wiki-issues`
  and `visualize`), i.e. the skill count read 13/14/15 depending on which file you opened.
- **Why chosen:** Every convention those files carried already had a single source of truth in
  `skills/*`, `references/operational-rules/*`, `hooks/hooks.json`, `README.md`, or `CLAUDE.md`.
  Nothing unique was lost — a provenance map was written *before* deletion to prove salvage
  (goal: "komplett auf Claude reduzieren"). `CLAUDE.md` gained a "Conventions & Editing" pointer
  section to preserve the single-entry-point value.
- **Current state (2026-07-02, commit `a4a7bd6`):** DONE. The four surfaces are absent; README drops
  the "Multi-agent support" tagline and the "Multi-model support" comparison row. The skill-count
  guard was repointed to the Claude-only surface set (`TABLE_SURFACES = ["CLAUDE.md"]`; copilot
  dropped from the numeric + name-list checks; `make test` green).
- **Lesson — do not repeat:** Do not maintain per-agent bootstrap files that restate conventions —
  they are duplication that drifts (here: three different skill counts). Keep one source of truth per
  convention. Before deleting any file believed redundant, write the provenance map that proves every
  line has a home elsewhere; when you drop a surface, repoint whatever guard was coupled to it.
- **Refs:** `docs/audit/2026-07-02/multi-agent-salvage.md` (provenance map);
  `docs/specs/SPEC-2.0.0-consolidation.md` (S1–S3); `tests/test_skill_count_ssot.py`; commit
  `a4a7bd6`.

### D7 — Scripts colocate under their owning skill; shared → `lib/`

- **Decision:** Each script moves under `skills/<owning-skill>/scripts/`; code used by more than one
  skill moves to `lib/`.
- **What was tried / prior state:** All scripts lived in a flat central `scripts/` directory, not
  bound to any skill (flat discoverability, unclear ownership).
- **Why chosen (over alternatives):** Scripts become discoverable next to the skill that owns them,
  with clear ownership (follows the `doc-pipeline` precedent). *Rejected:* central consolidation into
  packages (keeps scripts unbound from skills, discoverability stays flat); a separate "hybrid" option
  (identical to "shared → `lib/`", so folded in rather than kept distinct).
- **Current state (2026-07-02):** Accepted. `run-lint` + its `lint-*` checks → `skills/wiki-lint/`;
  shared DragonScale util → `lib/`; `run-lint.py` importlib load-paths + tests + all path references
  updated. Note the cost: the DragonScale cluster splits across 3 skills.
- **Lesson — do not repeat:** Do not re-flatten scripts into a central `scripts/` bucket unbound from
  skills. Shared code has exactly one home (`lib/`), not a copy per skill. When you relocate a script,
  its importlib/path references and tests must move with it in the same change.
- **Refs:** `docs/adr/0002-colocate-scripts-under-skill.md`.

### D8 — The `setup-*` cluster stays in `bin/` (explicit exception to D7)

- **Decision:** The installer family (`bin/setup-vault.py`, `setup-dragonscale.py`, and the
  since-removed `setup-multi-agent.py`) stays in `bin/`, not under a skill; shared resolver logic
  reuses `lib/vault_root.py`.
- **What was tried / prior state:** ADR-0002 (D7) had just made "colocate under the owning skill" the
  default, which would pull the installers under `skills/wiki/scripts/`.
- **Why chosen:** Evidence (spec-setup) showed the installers are **bootstrap / install-time tooling**
  that runs *before* any skill is used — callers are `Makefile` targets, `docs/install-guide.md`,
  `README.md`, not skill runtime. Colocating them under a skill would complicate install callers and
  falsely imply they are skill-runtime. So D7's default is deliberately *not* applied here.
- **Current state (2026-07-02):** Accepted as an explicit exception to D7. (`setup-multi-agent.py` was
  later removed entirely — see D6 — but the install-time-tooling rationale for the remaining installers
  stands.)
- **Lesson — do not repeat:** Do not colocate install-time / bootstrap tooling under a skill just
  because a "colocate under skill" default exists — install-time ≠ skill-runtime. State the exception
  explicitly next to the rule it breaks, so the future repo doesn't "helpfully" re-fold it.
- **Refs:** `docs/adr/0003-setup-cluster-stays-in-bin.md` (exception to
  `docs/adr/0002-colocate-scripts-under-skill.md`).

### D9 — Skill-home for the OPEN-ISSUES stack: one new `wiki-issues` skill (not a split)

- **Decision:** Create one dedicated `wiki-issues` skill that owns the entire
  `wiki/meta/OPEN-ISSUES.md` stack lifecycle — both the `handoff`-style push and the `fix-issues`-style
  pop-and-work — plus the stack's format (ID scheme, priority, ready-flag, LIFO ordering).
- **What was tried / prior state:** ADR-0001 (D2) had originally proposed *splitting* the two
  substantive commands across existing skills — `fix-issues` → `wiki-lint`, `handoff` → `save`.
- **Why chosen (over alternatives):** *Rejected — the ADR-0001 split:* it would scatter the push and
  pop of a **single stateful artifact** across two skills, forcing the stack's ID/format invariants to
  be duplicated and kept in sync in two places (drift risk), and it would overload stateless
  `wiki-lint` with a stateful workflow. *Rejected — fold both into `wiki-lint`:* `wiki-lint` is
  deterministic, read-mostly analysis; a mutating issue-stack workflow bloats its responsibility and
  its `allowed-tools` surface. *Rejected — keep the commands as-is:* contradicts D2 (skills-only).
- **Current state (2026-07-01 accepted; executed as FUP-4):** One `wiki-issues` skill owns the stack;
  it unblocked the command deletion in D2. Cost noted at decision time: one more skill (14 → 15),
  which compounded the count-drift later resolved by D4.
- **Lesson — do not repeat:** Do not split the read and write halves of one stateful artifact across
  two skills — its invariants then live in two places and drift. Give a stateful workflow its own
  owner; keep stateless/read-mostly skills free of mutating stack logic.
- **Refs:** `docs/adr/0005-skill-home-open-issues-commands.md` (supersedes the split proposed in
  `docs/adr/0001-delete-commands-skills-only.md`).

---

## 2.0.0 change summary

Release **`[2.0.0]` (2026-07-02)** bundles the following. Each line points to its
[`CHANGELOG.md`](../CHANGELOG.md) `[2.0.0]` entry; prose is not duplicated here.

- **Shell → Python migration (in progress)** — `run-lint` + address allocator now pure Python,
  invoked with no shell wrapper; `run-lint.py` folds its six checks in-process; `jq` dropped.
  → CHANGELOG `[2.0.0]` › *Changed*. (See D1.)
- **Release lint gate scoped to the distribution** — gate no longer blocks on the 182 working-vault
  findings; blocks only when run-lint cannot run. Regression: `tests/test_release_gate.py`.
  → CHANGELOG `[2.0.0]` › *Changed* / *Fixed*. (See D5.)
- **All 7 `commands/` files removed — skills-only** (breaking vs `v1.10.1`; migration note included).
  → CHANGELOG `[2.0.0]` › *Removed* (FUP-4). (See D2, D9.)
- **Multi-agent surfaces removed — Claude-only** (`AGENTS.md`, `GEMINI.md`, copilot instructions,
  `setup-multi-agent.py` gone; guard repointed; README tagline/row dropped; breaking vs `v1.10.1`).
  → CHANGELOG `[2.0.0]` › *Removed*. (See D6.)
- **`visualize` shipped as the 15th skill + skill-count SSOT guard** (`tests/test_skill_count_ssot.py`).
  → CHANGELOG `[2.0.0]` › *Added* / *Changed* (FUP-5). (See D4.)
- **`tests/test_run_lint.sh` retired** in favor of `tests/test_run_lint.py` (Python characterization
  suite, 183 checks). → CHANGELOG `[2.0.0]` › *Removed*. (See D1.)
- **Address-counter off-by-one fixed** (seed `0` → `1`; first allocation `c-000001`).
  → CHANGELOG `[2.0.0]` › *Fixed* (FUP-2). (See D3.)

> Not done in this release, by design: no `v2.0.0` git tag cut, and the `.claude-plugin/plugin.json`
> version is intentionally **not** bumped ("prepare, not tag"); the history-wipe migration to a fresh
> repo is a separate later session. See `docs/specs/SPEC-2.0.0-consolidation.md` (§5, scope contract).
