---
agent: V2
lens: high-value-gaps
generated: 2026-07-01
audit_base: 0a9916d
scope: value-maximization (Phase 2)
mode: read-only
---

# V2 — High-Value Gaps

Value-maximization pass. Lens: **missing work that would materially move the feature.**
Class = `value` throughout. Severity by impact: `high` (materially moves feature / prevents a
real defect) · `med` · `low`. Builds on the correctness audit (seed-0/`c-000000` off-by-one,
ADR-0004 rationale defect) — those are **not** re-derived here.

Evidence base (all at `0a9916d`):
- `bin/setup-vault.py:48` → `counter.write_text("0\n")`
- `bin/setup-dragonscale.py:52` → `counter.write_text("1\n")` + `:125` sanity check
- `tests/test_allocate_address.py:152` seeds `"1\n"`; `:64` reads counter — **never** seeds `0`, never invokes a setup script
- `grep setup-vault|setup-dragonscale tests/` → **NONE** (both setup scripts entirely untested)
- DragonScale PRD G2 metric = "Every new page receives a unique `c-NNNNNN`"; R3 = "counter starting at 1 (first page `c-000001`)"

---

## Q1 — PRD goals / success-metrics with NO covering spec/plan/task

Cross-mapped all three PRDs' §3 goal tables against `docs/specs/`, `docs/plans/`, `docs/tasks/`,
`docs/test-designs/`, and `tests/`.

**cmd-script-consolidation PRD** (§3, 5 goals) — **fully covered.** Every metric maps to
SPEC/PLAN/TASK-cmd-script-consolidation-* and the test-design's Acceptance→Test mapping. No gap.

**Agentic-Wiki PRD** (§3, G1–G5) and **DragonScale PRD** (§3, G0–G4): these two PRDs have **no
downstream spec/plan/task of their own** — the only artifact that references their goal set is
**FUP-8** ("wire PRD success metrics to tests/evals/lint"), and FUP-8 is P2, gated soft on
"PRDs approved", and explicitly **recorded-not-executed**
(`docs/tasks/dragonscale-agentic-wiki-followups.md`). So each goal below is *tracked* only via
a deferred umbrella task, with **no concrete covering assertion**:

| Goal | Metric | Covering assertion today? | Gap |
|---|---|---|---|
| DS **G0** — strictly optional | base vault unchanged if setup never run (feature-detected) | **NONE** — no feature-detection / "setup-not-run" test in `tests/` | **high** |
| DS **G1** — bound log via rollup | fold idempotent, re-run yields no diff, log never mutated | **NONE** — no `test_fold*`; `wiki-fold` skill unverified | med |
| DS **G2** — stable identity | unique `c-NNNNNN`; re-ingest reuses address (0 duplicates) | allocator tested, but **the seed that feeds it (`setup-vault.py`) is not** → the *provisioning* half of G2 is unverified | **high** (ties to Q3/Q4) |
| DS **G3** — stop duplicates | cosine ≥0.90 → error, 0.80–0.90 → review | `tests/test_tiling_check.py` exists → **covered** | — |
| DS **G4** — frontier-aware research | boundary-ranked top-N | `tests/test_boundary_score.py` exists → **covered** | low |
| Wiki **G1** — persist/compound across sessions | hot+index+log restore on SessionStart | **NONE** — SessionStart hook has no test | med |
| Wiki **G2** — ingest any source | files/URLs/binary docs → pages | **NONE** — no ingest/doc-pipeline test | med |
| Wiki **G3** — grounded answers | hot→index→pages w/ citations | **NONE** (inherently eval-shaped, not unit) | low |
| Wiki **G4** — deterministic quality | `run-lint --json` `totals.error==0`; path-safety blocks bad writes | `test_run_lint.py` + `test_wiki_path_safety.py` → **covered** | — |
| Wiki **G5** — portable (plugin+skill+vault) | repo valid in 3 modes at once | **NONE** — no tri-mode validity check | low |

**Most material uncovered goal: DS G0 (strictly-optional).** G0 is the *foundational safety
promise* of the entire DragonScale extension ("DragonScale must never be required for base
operation", DS PRD §4). It is asserted nowhere. A regression that makes a base skill hard-depend
on `.vault-meta/` would ship green.
- **Gap:** DS G0 has zero test coverage.
- **Why it matters:** G0 is the contract that lets DragonScale be optional; breaking it silently
  breaks every base-only vault. Highest-leverage single missing test.
- **Proposed artifact:** `tests/test_dragonscale_optional.py` — run a base skill/lint path against
  a tmp vault **without** `.vault-meta/`, assert unchanged behavior + no crash. Add a FUP row
  (or fold into FUP-8) that is **not** soft-gated behind "PRD approved".
- **Effort:** ~0.5 day (one black-box test mirroring existing tmp-vault harness).

**Secondary:** the two platform PRDs (DS, Wiki) have **no Spec** at all — they jump PRD→FUP-tracker.
For a "status: approved / draft" platform PRD that is acceptable *if* FUP-8 is scheduled; but
FUP-8 being P2-soft-gated means the approved PRDs currently have **no binding downstream contract**.
- **Proposed:** either (a) de-gate FUP-8 from "PRDs approved" and split it into per-goal test rows,
  or (b) accept the PRDs stay descriptive and mark G1/G2/G3/G5 explicitly "eval-only, no unit gate"
  so the absence is a *decision*, not a hole. **Effort:** ~1h (tracker edit).

---

## Q2 — Migration / rollback gap for ADR-0001 (delete slash-commands)

**Finding: HIGH-value gap — no user-facing migration/deprecation/rollback path exists at the
decision level.**

Evidence:
- `docs/adr/0001-delete-commands-skills-only.md:32` (Konsequenzen) states only:
  *"`/slash`-UX entfällt (Nutzer triggern per natürlicher Sprache / Skill-Auto-Trigger)"* — this
  acknowledges the loss but is an internal consequence note, **not** a user-facing migration path.
- ADR-0001 has **no** "Rollout / Migration / Backout" section. Neither does the
  cmd-script-consolidation PRD (checked §3–§7 + checklist).
- Contrast — the *derived* `docs/specs/SPEC-wiki-issues.md` **does** carry a §8 "Rollout /
  Migration / Backout". So the pattern exists in-repo; it is simply **absent for the 5 thin-wrapper
  deletions** (`/push`, `/pop`, and the 3 wiki routers) that users may invoke today by muscle memory.
- The task graph (`docs/tasks/cmd-script-consolidation-commands.md` CMD-9) updates *internal* refs
  (README/AGENTS/CLAUDE/roadmap) to `commands/`, but nothing tells an **end user** who types
  `/wiki-ingest` that the slash form is gone and what to type instead. No deprecation shim, no
  CHANGELOG-facing "removed commands" note is specified.

- **Gap:** No migration note / deprecation notice / rollback plan for users of the 7 deleted
  slash-commands. Removal is silent from the user's side.
- **Why it matters:** ADR-0001 itself lists loss of `/slash`-UX as a *cost*. A user who has
  `/fix-issues` or `/handoff` in their workflow gets a silent "command not found" with no pointer to
  the replacement skill/NL-trigger. For a shipped plugin this is a real adoption/DX regression, and
  there is no documented backout if the skills-only surface proves insufficient.
- **Proposed artifact:**
  1. A **"Migration / Backout" subsection** added to the cmd-script PRD **or** an ADR-0001 addendum
     ADR (ADR-0001 status is immutable → new ADR) mapping each removed command → its skill / NL
     trigger, plus a one-paragraph backout (git-revert the deletion commit; commands are
     manifest-independent per ADR-0001:19, so restore is clean).
  2. A user-facing **CHANGELOG/release "Removed commands → use instead" table** (the repo already
     keeps `docs/releases/`).
  3. Optionally a CMD-task acceptance line requiring that table before CMD-15 (commit gate).
- **Effort:** ~0.5 day (mapping table already derivable from the CMD-6 coverage matrix + one
  release-note stub).

---

## Q3 — Test gaps on risky surfaces (allocator · path-safety hook · counter seeding)

| Surface | Coverage today | Verdict |
|---|---|---|
| Allocator `scripts/allocate-address.py` | `tests/test_allocate_address.py` — rebuild, peek-idempotent, first-alloc=`c-000001`, monotonic, 20-way flock concurrency, corrupt counter, recovery-from-max, code-block-ignored, unknown-mode | **Well covered** for the allocator *in isolation* |
| Path-safety hook `hooks/wiki-path-safety.py` | `tests/test_wiki_path_safety.py` — Guard A/B, path whitelist, hyphenation, strict/mixed modes, config bootstrap, NotebookEdit shape (~15 assertions) | **Well covered** |
| **Counter *seeding*** (`setup-vault.py` / `setup-dragonscale.py`) | **NONE.** `grep setup-vault\|setup-dragonscale tests/` → no match. Both setup scripts are entirely untested. | **HIGH-value gap** |

**The seed-0 / `c-000000` edge is untested, and that is exactly the edge that hides the live bug.**

- `test_allocate_address.py` only ever puts a **`1`** into the counter — via `--rebuild`
  (`:? → "Counter rebuilt: next = 1"`) or a literal `write_text("1\n")` at `:152`. It **never**
  runs `setup-vault.py`, so the `"0\n"` seed at `setup-vault.py:48` never reaches the allocator in
  any test.
- Consequently: the allocator suite *proves* the intended first address is `c-000001`
  (`test_first_alloc`), while `setup-vault.py` seeds `0` → the real first `allocate` call on a
  `setup-vault`-provisioned vault returns **`c-000000`** — a value the test suite implicitly asserts
  should never occur. The suite gives false confidence: green tests, wrong runtime output.
- FUP-2's own acceptance says *"a test asserts it"* — **that test does not exist yet.** The
  test-design's dragonscale mapping asserts allocator *relocation* and `--peek` read-only, but has
  **no row** for setup-script seed value.

- **Gap:** No test that (a) runs each setup script against a tmp vault and asserts the seeded
  counter, and (b) asserts the first `allocate` on a freshly-`setup-vault`-provisioned vault yields
  `c-000001` (not `c-000000`).
- **Why it matters:** this is the *only* test that would have caught (and would prevent regression
  of) the live off-by-one. It also closes DS G2's provisioning half (Q1). Highest test ROI in the repo.
- **Proposed artifact:** `tests/test_setup_provisioning.py` — for each of `setup-vault.py`,
  `setup-dragonscale.py`: run against tmp vault, assert `address-counter.txt == "1"`, then invoke
  the allocator once and assert `c-000001`. Add a parity assertion that both scripts seed the
  **same** value (guards future drift). Wire into `make test`.
- **Effort:** ~0.5 day. **Should land in the same change as the FUP-2 one-line fix** — otherwise the
  fix is unguarded.

**Secondary (med):** DS **G0** feature-detection has no test (see Q1) — arguably the second-riskiest
untested surface, since it protects every base-only vault.

---

## Q4 — Is FUP-2 (the live runtime bug) prioritized appropriately?

**Finding: FUP-2 is *labelled* correctly but *operationally under-prioritized* — a real,
user-visible off-by-one is parked behind a docs-only hold with the same urgency as cosmetic P2 config
chores.**

Evidence:
- `docs/tasks/dragonscale-agentic-wiki-followups.md`: FUP-2 is **P1**, labelled `bugfix` `config`,
  depends on FUP-1 (ADR-0004, now **accepted**). Correct classification.
- **But** the whole tracker is *"recorded, not executed … the audit round was docs-only"*, and
  FUP-2's dependency FUP-1 is already `accepted` — so **nothing technical blocks FUP-2 anymore.**
  The only thing holding it is the self-imposed "docs-only" posture of that audit round.
- FUP-2 is a **one-line script edit** (`setup-vault.py:48` `"0\n"` → `"1\n"`), the decision it
  waited on is resolved, and it is a **real runtime defect** (first page on a `setup-vault` vault =
  `c-000000`, violating DS PRD G2 metric + R3's explicit "first page `c-000001`").
- Meanwhile it sits in the same undifferentiated P1/P2 pool as FUP-6 (`_attachments` dir) and FUP-7
  (pre-commit gate) — pure hygiene with no user-visible defect.

- **Gap:** FUP-2 is not flagged as *"unblocked + shippable now"*; it reads as "deferred like the
  rest." A live off-by-one deserves to jump the docs-only hold now that FUP-1 is accepted.
- **Why it matters:** every vault provisioned by `setup-vault.py` (the *base* setup path, not the
  DragonScale one) gets a wrong first address until this ships. It's the cheapest high-impact fix in
  the backlog (1 line + the Q3 test).
- **Proposed work:** promote FUP-2 to *do-now*: land the 1-line seed fix **plus** the
  `test_setup_provisioning.py` guard (Q3) **plus** the FUP-2 acceptance's "guide + PRD updated" in a
  single small PR. Drop the docs-only hold for this one item; FUP-1 (its gate) is already accepted.
- **Effort:** ~1h fix + test (the test is the Q3 artifact; do them together).

---

## Q5 — Other materially-missing artifacts

1. **DS G0 optionality test (high)** — covered in Q1/Q3; the single most valuable missing artifact
   after the FUP-2 guard. The strictly-optional promise (DS PRD §4: "must never be required for base
   operation") is contract-critical and asserted nowhere.

2. **`_attachments/` missing but referenced (med)** — confirmed: `CLAUDE.md:19` and multiple
   `.gitignore` lines (16, 92–110) reference `_attachments/`, but the directory **does not exist**
   on disk. This is FUP-6 (P2). Any wiki page or canvas op that writes an attachment path hits a
   missing dir. **Gap:** dangling config reference. **Proposed:** `_attachments/.gitkeep` (or
   de-reference). **Effort:** 5 min. Low complexity but it's a live inconsistency, not just a doc.

3. **Threat-model / privacy artifact for the platform PRDs (med).** Both DS and Wiki PRDs ship
   *without* a threat-model or privacy note, even though the standing preference (agent-discipline R1)
   makes security/privacy ALWAYS-IN for platform work. The wiki ingests **arbitrary user sources**
   (`.raw/`, URLs, binary docs) and DragonScale M3 shells out to a **local ollama** embedder. Only
   `SPEC-wiki-issues §7` carries a (one-line) security note; there is no vault-level threat model
   covering: untrusted-source ingestion (prompt-injection via ingested docs into an agent that then
   writes files), the PostToolUse **auto-commit** hook (auto-committing attacker-influenced content),
   or path-safety as the *sole* write guard. **Gap:** no platform threat-model/DPIA. **Why it
   matters:** an agent that auto-ingests URLs and auto-commits is a real injection surface; the
   path-safety hook is the only barrier and its threat coverage is unstated. **Proposed:**
   `docs/threat-models/agentic-wiki.md` (STRIDE-lite over ingest → write → auto-commit; note
   local-only embeddings as a privacy plus). **Effort:** ~0.5 day.

4. **Acceptance criterion that would change a decision — FUP-8's soft gate (med).** FUP-8 ("wire
   metrics to tests") is soft-gated on "PRDs approved", but the DS/Wiki PRDs already carry
   `status:` headers and are treated as authoritative by the FUP tracker. This circular gate
   (metrics wait on approval; approval has no checklist requiring metrics) means **no PRD goal is
   test-bound**. **Proposed:** add to each PRD's "before approved" checklist a line "each G-metric
   maps to a test/eval/lint assertion (FUP-8)", making the goal→test binding a *release gate* rather
   than a deferred nice-to-have. **Effort:** ~1h.

5. **Counter-parity assertion drift guard (low, subsumed by Q3).** Even after FUP-2 fixes
   `setup-vault.py`, nothing prevents the two scripts from diverging again. The Q3 test should
   include a direct "both scripts seed the identical value" assertion so ADR-0004's canonical `1`
   is machine-enforced, not just documented.

---

## Roll-up

| # | Gap | Sev | Rough effort |
|---|-----|-----|--------------|
| Q3 | Counter *seeding* (`setup-*.py`) untested — the seed-0/`c-000000` edge that hides the live bug; setup scripts entirely untested | **high** | 0.5d (land with FUP-2 fix) |
| Q1/Q3/Q5 | DS **G0** "strictly optional" has zero test — foundational safety promise unasserted | **high** | 0.5d |
| Q2 | No user-facing migration / deprecation / rollback for the 7 deleted slash-commands (ADR-0001 notes the cost but no path) | **high** | 0.5d |
| Q4 | FUP-2 operationally under-prioritized — live 1-line off-by-one parked behind docs-only hold though its gate (FUP-1) is accepted | **high** | 1h (do-now) |
| Q1 | DS/Wiki PRD goals (G1/G2-provisioning/G5, Wiki G1/G2) tracked only via P2-soft-gated FUP-8 → no binding downstream contract | med | 1h (regate) or 0.5d/goal |
| Q5 | Platform threat-model/privacy artifact absent (untrusted ingest → agent write → auto-commit injection surface) | med | 0.5d |
| Q5 | `_attachments/` referenced (CLAUDE.md, .gitignore) but dir missing (FUP-6) | med | 5min |
| Q5 | FUP-8 circular soft-gate → no PRD goal is test-bound; add goal→test line to PRD approval checklists | med | 1h |
| Q1 | DS G1 (fold idempotency), Wiki G2 (ingest), Wiki G1 (SessionStart) untested | med | 0.5d each |
| Q5 | Counter-parity drift guard (subsumed into Q3 test) | low | included |

**Counts:** high=4 · med=5 · low=1 · gaps-found=10

**Single highest-leverage action:** ship FUP-2's 1-line seed fix **together with**
`tests/test_setup_provisioning.py` (Q3) — one small PR that kills the live off-by-one, guards it
against regression, and closes DS G2's provisioning half. Its blocking decision (FUP-1/ADR-0004) is
already accepted; only the self-imposed docs-only hold stands in the way.
