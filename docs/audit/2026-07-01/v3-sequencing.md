---
agent: V3
lens: sequencing
generated: 2026-07-01
audit_base: 0a9916d
class: value
---

# V3 — Sequencing Leverage Audit

Does the dependency order & priority maximize value-per-unit-effort? Evidence is cited as
`file:line` and `manifest-node`. Severity = leverage (high = reorder is materially cheaper/faster
to value).

**DAG facts (derived from manifests, base 0a9916d):**

- `cmd-script-consolidation` (20 nodes): **15 verified** (whole planning tree — PRD, 3 ADRs,
  test-design, 5 specs, 5 plans), **5 `todo`** execution task-trackers
  (`tasks-commands`, `tasks-lint`, `tasks-ingest`, `tasks-setup`, `tasks-dragonscale`).
  Ready leaves: `tasks-commands, tasks-lint, tasks-ingest, tasks-setup`. Sink = `tasks-dragonscale`
  (deps `plan-dragonscale, tasks-lint, tasks-ingest`).
- `dragonscale-agentic-wiki-followups` (5 nodes): `adr-0004` **verified**, `adr-0005` **todo**
  (`status: proposed`, `docs/adr/0005-…:4`), `fup-2` **todo/ready** (dep `adr-0004` verified),
  `fup-4` + `spec-wiki-issues` **todo/blocked** on `adr-0005`.

---

## Q1 — Is "cmd-script refactor BEFORE the DragonScale/wiki-issues follow-ups" value-maximizing? Should FUP-2 jump the queue?

**No — the blanket "refactor first" ordering mis-sequences the single highest-value item.**
FUP-2 should jump the entire queue. It is not coupled to the big refactor at all.

Evidence:

1. **FUP-2 is a live, shipped runtime defect, not a cleanup.** `bin/setup-vault.py:48` writes
   `"0\n"`; `bin/setup-dragonscale.py:52` writes `"1\n"` (both confirmed in source). ADR-0004
   (`docs/adr/0004-…:27`) states seed `0` → first page `c-000000` (off-by-one vs the documented
   `c-000001`) **and** "risks an outright **exit-3 error** on first allocate" because the allocator
   requires a positive integer. `setup-vault.py` is the *default/primary* vault-init path (it seeds
   the counter for an ordinary vault; `setup-dragonscale.py` is the opt-in mechanism). So **every
   fresh non-DragonScale vault ships broken** on first address allocation. Severity: high.

2. **Its decision gate is already cleared.** ADR-0004 is `status: accepted`
   (`docs/adr/0004-…:4`; manifest `adr-0004` = verified). The FUP-1→FUP-2 chain's decision half is
   *done*. FUP-2 is manifest-`ready` (`fup-2` deps = `adr-0004`, satisfied). Nothing real blocks it
   — only the self-imposed "docs-only round" hold (tracker preamble:
   `docs/tasks/dragonscale-agentic-wiki-followups.md` — "recorded, not executed … the audit round
   was docs-only").

3. **The fix is ~1 line + 1 test.** ADR-0004:51 + FUP-2 acceptance
   (`docs/tasks/dragonscale-agentic-wiki-followups.md`, FUP-2 row): change one seed literal, add a
   test asserting first allocation is `c-000001`, note migration. ADR-0004:44 — "smallest possible
   change surface — one seed literal."

4. **FUP-2 does NOT overlap the cmd-script refactor** — the two are disjoint on this file. The
   setup-cluster task tracker (`tasks-setup`) scopes its `setup-vault.py` edits to **vault-root
   resolver dedup only** — `SPEC-cmd-script-consolidation-setup.md` names the single dedupe target
   as `resolve_vault_root()`, and `docs/tasks/cmd-script-consolidation-setup.md` (SET-1, SET-4,
   SET-7) touches only `bin/n.py` / `setup-dragonscale.py` resolver lines, **never the counter-seed
   line 48**. So "wait for the refactor" buys FUP-2 nothing; the refactor never touches the bug.

**Verdict:** the cross-project "cmd-script → DragonScale followups" order is right *for FUP-4/
wiki-issues* (they genuinely share ADR-0001 command-deletion work — see Q3), but it is **wrong as a
blanket rule**: FUP-2 is falsely trapped behind a 5-node, 5-cluster refactor by a docs-only hold it
has no dependency on. **Ship FUP-2 first, standalone, today.** (Severity: **high** — a 1-line fix to
a live exit-3 bug is being held behind ~weeks of refactor for no dependency reason.)

---

## Q2 — Are the FUP P1/P2 assignments right?

Priorities are set in `docs/tasks/dragonscale-agentic-wiki-followups.md` (Tasks table, "Prio"
column) and mirrored in the Mermaid `class …,… p1` line. Assessment:

**Correct P1s:**

- **FUP-2** (P1) — correct, arguably *under*-ranked: it's the only one guarding a live runtime
  crash. Should be **P1-now / first-in-queue** (see Q1), not just "P1 among the decision-chains."
- **FUP-1** (P1) — correct but **already satisfied** (ADR-0004 accepted); it is spent, not pending.
- **FUP-3** (P1) — correct: it's the decision (`adr-0005`) that unblocks the most downstream
  follow-up work (`fup-4`, `spec-wiki-issues`). See Q3.

**Questionable:**

- **FUP-4** (P1) is *correctly* P1 by leverage (it's the actual command-deletion execution), **but
  it is currently blocked** — `adr-0005` is `status: proposed`, not accepted
  (`docs/adr/0005-…:4`; manifest `adr-0005` = todo). So its P1 is aspirational: it cannot start
  until FUP-3/ADR-0005 is ratified. The P1 label is fine; the ordering must place FUP-3 *strictly
  before* it (it does).

**P2s that are actually higher-leverage than their label:**

- **FUP-7** (P2 — local pre-commit gate → `run-lint.py`,
  `docs/tasks/dragonscale-agentic-wiki-followups.md` FUP-7 row). This is a **force-multiplier /
  quality-gate** item: once wired, every subsequent change (FUP-2's test, FUP-4's CI-green
  acceptance, FUP-5's drift-lint) is auto-verified locally instead of by hand. Standing prefs (R2
  evidence-first, quality-gate thresholds) treat gates as always-in, not nice-to-have. It is also
  dependency-free (`depends_on: []`) and cheap. **Recommend promote toward P1 / do-early** (right
  after FUP-2), because it lowers the cost of everything after it. Severity: med.

**P2s correctly ranked low:**

- **FUP-5** (skill-count SSOT 13-vs-14 drift), **FUP-6** (`_attachments/` presence), **FUP-9**
  (disable-path doc) — genuine but cosmetic/doc-consistency; correctly P2, parallelizable, no
  runtime impact.
- **FUP-8** (wire PRD metrics) — correctly **last**: its own note (`Ordering` section) makes it
  soft-dependent on "PRDs → approved" so the metric set is frozen first. Ranking is right.

**No P1 is genuinely low-value.** The main mis-ranking is directional: **FUP-2 under-ranked
(should be first)** and **FUP-7 under-ranked (P2 but is a leverage/gate item)**.

---

## Q3 — Critical path: which single item unblocks the most downstream work? Front-loaded or leaf-work?

**Two separate DAGs, two separate unblockers:**

- **Within `cmd-script-consolidation`:** the planning tree is fully verified, so the *remaining*
  critical path is short. `tasks-lint` and `tasks-ingest` each unblock **`tasks-dragonscale`**
  (the sink) — computed reverse-deps: `tasks-lint → tasks-dragonscale`,
  `tasks-ingest → tasks-dragonscale`. `tasks-dragonscale` also needs both because
  the dragonscale cluster collides with `wiki-lint/scripts/` and re-homes `allocate-address` into
  `wiki-ingest/scripts/` (task-tracker risk notes). So **`tasks-lint` + `tasks-ingest` are the
  joint unblockers of the sink**; `tasks-commands` and `tasks-setup` are independent leaves
  (`UNBLOCKS = -`). Front-loading `tasks-lint`/`tasks-ingest` (and running `tasks-commands`,
  `tasks-setup` in parallel) is the value-maximizing order — the manifest DAG already encodes this,
  so the plan *is* front-loading the unblocker here.

- **Across the follow-ups:** the single highest-fan-out *pending* decision is **FUP-3 / `adr-0005`**
  — it gates **both** `fup-4` and `spec-wiki-issues` (manifest reverse-dep: `adr-0005` unblocks 2).
  It is dependency-free and ratifiable now (`status: proposed`). **This is the one item to
  front-load on the DragonScale side.** Everything else there is either done (`adr-0004`), a ready
  leaf (`fup-2`), or blocked behind `adr-0005`.

**Is the plan front-loading unblockers or leaf-work?** *Mixed.* The **within-refactor** DAG
correctly front-loads unblockers (`tasks-lint`/`tasks-ingest` before the `tasks-dragonscale` sink).
But the **cross-project sequence is not**: it front-loads a large refactor while leaving the two
truly enabling actions — the **FUP-2 one-liner** (ready, unblocks a shipped bug) and the **ADR-0005
ratification** (unblocks 2 downstream nodes, costs one decision) — sitting behind a docs-only hold.
Those two are the cheapest, highest-leverage moves in the whole board and are *not* front-loaded.
Severity: high.

---

## Q4 — Is there a cheaper / higher-leverage re-sequencing overall? (concrete)

**Yes.** The current implied order is "finish the 5-cluster cmd-script refactor, then do FUP-1..9."
That defers a live bug and a zero-cost unblocking decision behind weeks of refactor. Re-sequence to
pull the cheap high-leverage items to the front and let the refactor's own DAG run in parallel:

**Reordering rationale (value = leverage ÷ cost):**

- Two moves have near-zero cost and outsized value: **FUP-2** (1 line, kills a shipped exit-3 bug,
  gate already cleared) and **ADR-0005 ratification** (one decision, unblocks 2 nodes). Do them
  first — they are not on the refactor's critical path and gate real work.
- **FUP-7** (pre-commit gate) is cheap and makes every later step self-verifying — do it early so
  FUP-2's test and FUP-4's "CI green" are enforced locally, not by hand.
- The cmd-script refactor's *internal* order is already optimal — keep it, run its ready leaves in
  parallel, respect `tasks-lint`+`tasks-ingest` → `tasks-dragonscale`.
- **FUP-4/wiki-issues correctly stays after cmd-script**, but for the *right* reason: it and
  `tasks-commands` both execute ADR-0001 command deletion — coordinate so the wrappers are deleted
  once, in the refactor, and `wiki-issues` re-homes the 2 substantive commands. Do it *after*
  `tasks-commands` to avoid double-deleting.
- **FUP-8 stays last** (needs PRDs frozen). **FUP-5/6/9** slot in as parallel P2 filler.

---

## Recommended sequence

1. **FUP-2** — fix `bin/setup-vault.py:48` seed `0`→`1` + test (`c-000001`) + migration note.
   *(1 line; ADR-0004 accepted; manifest-ready; kills a live exit-3 bug. Do standalone, now.)*
2. **FUP-3 → ratify ADR-0005** (`docs/adr/0005-…:4` `proposed`→`accepted`).
   *(One decision; unblocks `fup-4` **and** `spec-wiki-issues`; dependency-free.)*
3. **FUP-7** — local pre-commit gate → `run-lint.py`.
   *(Cheap force-multiplier; makes every step below self-verifying. Promote out of P2.)*
4. **cmd-script execution, its own DAG** — parallel ready leaves `tasks-commands`, `tasks-lint`,
   `tasks-ingest`, `tasks-setup`; then the sink `tasks-dragonscale` (needs `tasks-lint` +
   `tasks-ingest`). *(Front-load `tasks-lint`/`tasks-ingest`; internal order already optimal.)*
5. **spec-wiki-issues** then **FUP-4** — build the `wiki-issues` skill and delete/rehome the 7
   command files, **after** `tasks-commands` so ADR-0001's wrapper deletion isn't done twice.
6. **FUP-5, FUP-6, FUP-9** — parallel P2 doc/config-consistency fillers, any time after step 1.
7. **FUP-8** — wire PRD metrics to tests/evals/lint, **last** (needs PRDs frozen `draft→approved`).

---

## Roll-up

- **high (3):** (Q1/Q3) FUP-2 — live exit-3 seed bug held behind a docs-only hold with no real
  dependency; ship first. (Q3/Q4) ADR-0005 ratification is the highest-fan-out *pending* item
  (unblocks 2) and is not front-loaded. (Q1) The blanket "refactor-before-followups" rule
  mis-sequences the cheapest highest-value work.
- **med (2):** (Q2) FUP-7 is a P2-labelled leverage/quality-gate item — promote to do-early.
  (Q2) FUP-4's P1 is currently aspirational (blocked on `adr-0005`); label OK, ordering must keep
  FUP-3 strictly first.
- **low (1):** (Q2) FUP-1 is P1 but already satisfied (ADR-0004 accepted) — spent, not pending;
  drop from the active queue.
- **reorder-proposed:** **yes** — 7-step sequence above; pulls FUP-2 + ADR-0005 + FUP-7 ahead of the
  refactor, keeps the refactor's internal DAG and FUP-4/FUP-8 tail intact.

Counts: high=3 med=2 low=1 | reorder-proposed=yes
