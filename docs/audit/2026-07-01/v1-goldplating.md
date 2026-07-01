---
agent: V1
lens: gold-plating
generated: 2026-07-01
audit_base: 0a9916d
scope: VALUE-MAXIMIZATION (Phase 2) — scope/effort vs feature value; internal consistency assumed green
class: value
---

# V1 — Gold-Plating Audit (value-maximization)

**Feature under audit:** two refactor/maintenance workstreams on a solo-maintained Claude+Obsidian plugin.
**Central measured fact:** the `cmd-script-consolidation` workstream is a **declared zero-behavior-change refactor** (PRD §4 "reiner Refactor: gleiche Inputs → gleiche Outputs", "Keine neuen Features") of **3612 production LOC**, and it is documented with **21 planning artifacts / 2233 doc-lines / ~23,739 words / 66 atomic tasks**. That is a **6.6 : 1 words-of-planning to LOC-touched** ratio for work whose atomic action set is *`git mv` + fix importlib paths + delete 7 files*. This is the dominant gold-plating signal; specifics below.

Baseline footprint (verified):
| cluster | prod-LOC | files | actual code action |
|---|--:|--:|---|
| lint | 1828 | 7 | move dir + preserve `importlib`/test load-paths |
| dragonscale | 972 | 3 | extract 1 shared `lib/` module + split across 3 skills |
| ingest | 330 | 2 | **`git mv` two stdlib standalones** |
| setup | 482 | 3 | **swap ~2 inline lines onto existing `resolve_vault_root()`; no move** |
| commands | 0 | 7 (.md) | verify coverage, delete 7 command files |

---

## Q1 — Is artifact volume/depth proportionate to feature size?

**Verdict: NO for `cmd-script-consolidation` (materially over-documented); YES for `dragonscale-agentic-wiki-followups` (proportionate).**

The follow-ups workstream is right-sized: a single 67-line tracker (`docs/tasks/dragonscale-agentic-wiki-followups.md`) holds 9 FUPs, and only the two that gate real code (counter fix, skill-home) got promoted to ADRs. That is correct decide-next discipline — decisions split from the fixes they gate, no premature spec on the P2 items. Keep as-is.

The consolidation workstream is not. Evidence of disproportion:

1. **Uniform maximal depth regardless of cluster size.** All 5 module specs carry the identical heavyweight 8-section skeleton — §1 Ziel · §2 Verträge · §3 Verhalten · §4 Ansatz · §5 Acceptance · §6 Test-Design · §7 **Security/Privacy** · §8 Rollout/Migration/Backout — *including a Security/Privacy section on a `git mv`* (`docs/specs/SPEC-cmd-script-consolidation-ingest.md:88` §7, `...-setup.md` §7). A file relocation has no security surface; the section is template tax, not analysis.
   - *Cheaper:* drop §7 Security and §8 Rollout/Backout from the pure-move specs (ingest, lint, setup) — "backout = `git revert` the one commit" is already true and needs no dedicated section. Effort delta: −~40 lines/spec, −3 sections × 3 specs.

2. **66 atomic tasks for a no-behavior-change refactor.** `tasks-commands:16, tasks-lint:12, tasks-dragonscale:14, tasks-ingest:12, tasks-setup:12`. For solo execution of a mechanical move, a per-cluster 12–16-row task grid with dependency-graph mermaid + ordering + risk section each is planning that will not be read at the density it was written.

3. **Doc-to-code ratio inverts on the small clusters** (see per-cluster table in Q3): ingest spends **321 doc-lines to move 330 LOC** and setup **317 doc-lines to touch ~2 lines**.

**Over-documenting artifacts, named:**
- `docs/specs/SPEC-cmd-script-consolidation-ingest.md` (111 ln) + `docs/plans/PLAN-cmd-script-consolidation-ingest.md` (141 ln) + `docs/tasks/cmd-script-consolidation-ingest.md` (68 ln) — **320 lines to `git mv` two files**; the plan's own Ground-Truth §5 states "einzige zwingende Code-Aktion = die zwei `git mv`. Zwingende Live-Pfad-Doc-Edits ≈ null" and S5/S6 expect **0 edits**. Recommendation: **trim** — fold spec+plan+task into one ~40-line move-checklist.
- `docs/plans/PLAN-cmd-script-consolidation-setup.md` (125 ln) — 12 steps (S0–S12), 3 human-gates, 6 rollback rows to change `vault = Path(...) if ... else SCRIPT_DIR.parent` → `resolve_vault_root(...)` in 2 files. The one abstraction it evaluates (`bin/_setup_common.py`) it correctly **SKIPs** (<5 LOC shared) — good judgment, but reaching that skip took a 125-line plan. Recommendation: **trim** to a ~30-line plan.

**Recommendation (Q1):** collapse the ingest and setup triplets; strip §7/§8 from the pure-move specs. This is the highest-leverage reduction — it removes ~500–600 doc-lines of the 2233 with zero loss of execution safety (the deterministic verify-gates that matter can live in the task checklist).

---

## Q2 — ADR-0005 new `wiki-issues` skill vs folding into `wiki-lint`

**Verdict: value JUSTIFIES cost — keep the new skill, but the surrounding spec is over-built for a not-yet-existent file. Net: keep-as-is on the decision, trim on the SPEC.**

Read: `docs/adr/0005-skill-home-open-issues-commands.md`, `docs/adr/0001-delete-commands-skills-only.md`, `docs/specs/SPEC-wiki-issues.md`.

**Why the new skill is NOT gold-plating (the value is real and evidenced):**
- ADR-0005 §Context gives a concrete structural argument, not a preference: `fix-issues` and `handoff` are **producer/consumer over one stateful artifact** (`wiki/meta/OPEN-ISSUES.md` — a stack with ID scheme, priority, ready-flag, LIFO). Folding push into `save` and pop into `wiki-lint` (ADR-0001's original split) would **duplicate the stack's ID/format invariants across two skills** and keep them in sync — a real drift cost.
- The rejected "fold into `wiki-lint`" alternative is correctly rejected on a stated ground (ADR-0005 §Alternatives): `wiki-lint` is **deterministic read-mostly analysis**; embedding a stateful mutating workflow bloats its responsibility and its `allowed-tools` surface. That is a legitimate cohesion boundary, not empire-building.
- The two commands are **~337 lines of substantive logic** (`fix-issues` 211 + `handoff` 126), not thin wrappers — they need *a* home, and ADR-0001 (accepted) forbids leaving them as commands.

So the choice is "one new skill" vs "split a stateful artifact across two ill-fitting skills." One skill is the cheaper *maintenance* outcome even though it is +1 skill surface. **Cost is acknowledged in the ADR itself** (§Consequences: "14 → 15 … compounds skill-count SSOT drift FUP-5") — the trade was made with eyes open.

**Where ADR-0005 / SPEC-wiki-issues DOES over-reach (trim targets):**
- `SPEC-wiki-issues.md` ports the full `ai-secondbrain` reference shape — **dual machine/human representation + parity validator, `blocked_by` DAG cycle-detection, format-version guard, year-resetting never-recycled ID allocator under `fcntl` lock, an 8-fixture test suite** (§6) — for a stack file that **does not exist on disk** (verified: `wiki/meta/OPEN-ISSUES.md` absent) and has, on day one, zero entries. This is building the battle-hardened v3 of a feature before v1 exists.
  - *Cheaper alternative:* ship a **minimal `wiki-issues` v1** = single-representation flat list + the pop/push flows + one schema+sort check wired into `run-lint`. Defer the DAG cycle-check, dual-representation parity guard, format-version guard, and the year-rollover ID lock to a follow-up **once the stack has real churn** that justifies them. Effort delta: roughly halves the port (AC5/AC6 + the dual-model in §2.1 + 4 of 8 fixtures become "later"), and drops the borrowed `c-NNNNNN`-style locked allocator (§4) which is heavy machinery for IDs on a solo file with no concurrent writers.
- The `blocked_by` DAG / cycle detection specifically: on a personal issue queue that a single agent pops one-at-a-time, cycles are a theoretical failure the validator guards against before any issue has ever been filed. Low value until proven needed.

**Verdict Q2:** keep the `wiki-issues` skill decision (**keep-as-is**); **trim** `SPEC-wiki-issues.md` to a v1 slice and defer the reference vault's hardening (parity guard, DAG, format-guard, locked allocator, half the fixtures) behind real usage. Rough delta: −1 heavy allocator, −2 guards, −~4 fixtures of pre-emptive robustness.

---

## Q3 — Specs/plans whose granularity exceeds the decision they support

**Verdict: YES — the ingest and setup module tracks, plus the "one full spec+plan+task triplet per cluster" fan-out, exceed their decisions.**

Per-cluster granularity vs the code decision each supports:

| cluster | spec+plan+task doc-lines | prod-LOC | decision the docs support | proportion |
|---|--:|--:|---|---|
| lint | 365 | 1828 | move dir, preserve importlib load-paths, keep JSON byte-identical | **proportionate** (real breakage risk in importlib paths + test loaders) |
| dragonscale | 468 | 972 | extract shared `lib/` module, split 3 scripts across 3 skills | **proportionate-ish** (genuine `lib/` extraction + sys.path-depth change = real risk) |
| ingest | 321 | 330 | **`git mv` 2 files** | **exceeds** — 141-line plan, plan admits 0 expected edits |
| setup | 317 | 482 | **swap ~2 lines onto existing resolver; no move** | **exceeds** — 125-line plan to reach a "SKIP the helper" conclusion |
| commands | 394 | 0 | verify coverage, delete 7 files (+ triggers `wiki-issues`) | mostly proportionate (coverage-matrix-before-delete is the load-bearing safety step) |

- **`git mv`-class work (ingest) does not need spec §Verhalten + §Edge-Cases + §Fehlerbehandlung + §Security + §Rollout.** The plan already proves via `rg` that no consumer references the paths as live. A 40-line "move + hash-parity + `make test` green" checklist carries the same safety.
- **The fan-out pattern itself is the granularity error:** 5 clusters each got the *same* full spec+plan+task triple. lint and dragonscale earn it (importlib/`lib`-extraction risk). ingest, setup, and arguably commands did not need a *separate module spec* — they could be sections in one consolidation spec. That is the "9-plan spread where 3 would do" pattern the question names: here it is **5 module-plans where ~2 (lint, dragonscale) carry the real risk** and the other three are checklist-grade.

**Recommendation (Q3):**
- **Trim** ingest + setup to single checklists (covered in Q1).
- **Keep** lint and dragonscale plans at current depth — their importlib load-path and `lib/`-extraction risks are exactly what a plan is for.
- Optionally merge `commands`/`ingest`/`setup` module-specs into one "mechanical moves + deletion" spec, leaving lint and dragonscale as standalone. Effort delta: 5 specs → 3.

---

## Q4 — Is the single test-design right-sized to risk?

**Verdict: RIGHT-SIZED, leaning slightly lean in one spot — keep-as-is.**

`docs/test-designs/cmd-script-consolidation.md` (82 ln, 30 mapping rows, status `approved`) maps acceptance → tests across the 5 modules with a numeric Quality-Gate. Its risk-weighting is correct:
- It concentrates on the **one thing that can actually break invisibly**: `run-lint.py --json` byte-identical pre/post against a fixture vault (the CI-gating contract, PRD G4) and the importlib load-paths. That *is* where the refactor risk lives — good targeting.
- It correctly does **not** invent new behavioral tests (the refactor changes no behavior; the existing 10-file `tests/` suite is the regression net, reused as-is). Not writing new unit tests for moved-but-unchanged code is the *right* call, not under-testing.
- One appropriately-flagged reality: `pytest` is not installed; the operational gate is `make test` (stdlib unittest). The plans surface this honestly rather than asserting a green pytest run.

**Where it is slightly lean (not a defect, a note):** the `wiki-issues` skill (the one place *new behavior* is introduced) is scoped to a **different** manifest and is not in this test-design — its tests live in `SPEC-wiki-issues.md §6`. That is structurally correct (different workstream), but it means no single test-design covers the only net-new-code component. If anything in this audit needs *more* test rigor it is `wiki-issues`, and Q2 already argues the opposite direction (its 8-fixture suite is pre-emptive). Net: the test-design for the refactor is correctly sized; do not inflate it.

**Recommendation (Q4):** **keep-as-is.** Do not add tests for behavior-preserving moves. Right-sized against risk.

---

## Roll-up

`dragonscale-followups` workstream + `wiki-issues` *decision* + refactor *test-design* are right-sized and should stay. The gold-plating is concentrated in the `cmd-script-consolidation` refactor: 6.6:1 planning-to-code for a zero-behavior-change `git mv`, with the **ingest** and **setup** module triplets and the uniform §7-Security/§8-Rollout skeleton on pure-move specs as the concrete trim targets (~500–600 doc-lines removable with no loss of execution safety); secondary trim is `SPEC-wiki-issues.md`, which ports a battle-hardened stack (parity guard, DAG, format-guard, locked ID allocator, 8 fixtures) for a file that doesn't exist yet — ship a v1 slice and defer the hardening behind real usage.

counts: high=2 med=3 low=2 | keep-as-is=4 trim=5
