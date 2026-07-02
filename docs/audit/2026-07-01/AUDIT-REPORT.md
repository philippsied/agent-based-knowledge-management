---
type: audit-report
title: "Full consistency & value audit — DragonScale / Agentic-Wiki + cmd-script-consolidation"
audit_base_commit: 0a9916d
scope: "3 PRDs · 5 ADRs · 8 specs · 9 plans · 6 tasks · 1 test-design · 4 manifests (both bundles)"
method: "Phase 0 structural gate → Phase 1 semantic fanout (4 agents, #1–#9) → Phase 2 value fanout (3 lenses)"
disposition: report-only
generated: 2026-07-01
verdict:
  contradiction_free: true
  gates: "G0 green · G1 green · G2 assembled"
---

# Audit Report — Consistency, Correctness & Value

**Bottom line.** The artifact set is **structurally sound and contradiction-free** — every semantic cross-check (#1–#9) passed, and all four handoff worries were *refuted*, not confirmed. Only **one doc-only defect** exists (ADR-0004's rationale). The audit's real payload is a **convergent value signal**: three independent value lenses + the correctness pass all point at the same action — **ship the FUP-2 one-line runtime fix first**, out from behind the docs-only hold it has no dependency on.

Full evidence per finding lives in the fragment files (indexed at bottom); this report deduplicates and ranks them.

---

## 1 · Correctness findings (deduplicated, severity-ranked)

| ID | Sev | Finding | Class | Evidence | Fixable under docs-only? |
|----|-----|---------|-------|----------|--------------------------|
| **F1** | 🔴 high | `setup-vault.py:48` seeds counter `0` → a vault's **first allocated address is `c-000000`**, off-by-one against every doc & against `setup-dragonscale.py:52` (seeds `1`). Real runtime defect. | `flag-only` | `bin/setup-vault.py:48`, `bin/setup-dragonscale.py:52`, `scripts/allocate-address.py:140` | ❌ needs 1-line **script** edit = **FUP-2** (behind docs-only hold) |
| **F2** | 🟠 med | **ADR-0004's stated rationale is factually wrong.** It claims seed 0 triggers "positive-integer validation / exit-3". Real: the guard `re.fullmatch(r"[0-9]+", …)` **accepts `0`** → yields `c-000000` at **exit 0, silently**. The *decision* (seed = 1) stays correct; only the *why* is false — and it misleads FUP-2. | `fix-doc` | `scripts/allocate-address.py:95`; ADR-0004 Context L22/L27, Alternatives L37, Follow-up L52 | ✅ **yes** — correct wording to "non-negative integer / `[0-9]+`", drop the exit-3 claim |

**Everything else on correctness verified consistent (ok):**
- **#2** ADR-0005 does **not** silently contradict ADR-0001 — it explicitly quotes the earlier `fix-issues→wiki-lint` lean (`docs/adr/0005-*.md:22`) and rejects it as a named alternative (`:35`).
- **#3** Status parity holds across tracker ⇄ manifest ⇄ ADR (FUP-1/ADR-0004 = accepted; FUP-3/ADR-0005 = proposed). *Nuance (low, flag-only):* the manifest uses decide-next lifecycle tokens (`verified`/`todo`) mapped to ADR tokens via its `verify:` field — worth noting for future auto-checks, not a mismatch.
- **#4** Skill-count drift (PRD 14 · SPEC 14→15 · copilot 13) is **one coherent, FUP-5-governed known gap**, not three contradicting truths.
- **#5** wiki-issues **template ⇄ SPEC ⇄ ADR-0005** agree on all five constraints (field names, `I-YYYY-NNN`, 4-key sort, section whitelist, 4 dispositions).
- **#6** SPEC-wiki-issues references resolve & are accurate; the **high-sev path-safety candidate is disproven** — `wiki/meta/OPEN-ISSUES.md` **is** writable (hook prefix-whitelists `wiki/` at `hooks/wiki-path-safety.py:139`).
- **#7** DragonScale PRD (product) vs cmd-script-consolidation SPEC (refactor) are **complementary** — all 9 shared artifacts agree, no contradiction.
- **#8/#9** (Phase 0) links/paths/manifests all clean; 11 `.sh` citations are intentional history (per `3710c15`), not defects.

---

## 2 · Value findings (Phase 2 — `value` class)

| ID | Sev | Finding | Lens | Evidence |
|----|-----|---------|------|----------|
| **V-1** | 🔴 high | **Sequencing is mis-ordered.** FUP-2 (1-line, gate ADR-0004 already *accepted*, manifest-`ready`) is falsely trapped behind the 5-cluster cmd-script refactor by a **docs-only hold it has no dependency on**. | seq (V3) | `docs/manifests/dragonscale-agentic-wiki-followups.json`, tracker FUP-2 |
| **V-2** | 🔴 high | **Counter-seeding is entirely untested** — both setup scripts have zero tests; the seed-0/`c-000000` edge that hides F1 is exactly what's uncovered. | gaps (V2) | `docs/test-designs/*` (no provisioning test) |
| **V-3** | 🔴 high | **No user-facing migration/rollback** for ADR-0001's command deletion (skills-only). Users on old slash-commands get no deprecation path. | gaps (V2) | `docs/adr/0001-*.md` + plans |
| **V-4** | 🟠 med | **Planning over-build:** cmd-script-consolidation is a zero-behavior `git mv`/import refactor (~3612 LOC) carrying **21 docs / ~2233 lines / 66 tasks ≈ 6.6:1 planning-to-code**. 5 trim candidates. | gold (V1) | fragment v1 |
| **V-5** | 🟠 med | DS "G0 strictly-optional" promise is **unasserted** (no check enforces optionality). | gaps (V2) | PRD dragonscale G0 |
| **V-6** | 🟠 med | Section-whitelist **divergence** between wiki-issues template/SPEC and the `commands/` migration source. | gold/refs (C, V1) | fragment c #5 (C5-a) |
| **V-7** | 🟡 low | EN/DE heading split (pre-existing bundle German · this-session English) across PRDs + ADRs. | consistency (B) | ADR-0001 `## Konsequenzen` vs ADR-0004 `## Consequences` |

**Right-sized (explicitly NOT gold-plating):** the `wiki-issues` new-skill decision, the follow-ups tracker, and the refactor test-design (V1).

---

## 3 · The convergence (why F1/V-1/V-2 are the headline)

Four independent passes point at **one** action:

- **Correctness (A):** F1 is a real off-by-one runtime bug.
- **Gaps (V2):** the same surface is untested *and* under-prioritized — "highest-leverage action: land the FUP-2 1-line fix + a `test_setup_provisioning.py` guard as one PR."
- **Sequencing (V3):** FUP-2 is mis-trapped behind an unrelated refactor; ship it first.
- **ADR-0004 (F2):** the decision record that governs this exact value got its *reasoning* wrong.

→ **Highest-value move: FUP-2 fix + provisioning test as a single PR, ahead of the refactor.** Its gate (ADR-0004) is already accepted; the only thing blocking it is the self-imposed docs-only hold.

---

## 4 · Recommended dispositions (for G3 — user decides; report-only default)

**A. Fixable now, docs-only-compliant (1 clean edit):**
- **F2** — correct ADR-0004's rationale text (decision unchanged). Zero code risk.

**B. Requires lifting the docs-only hold (converged top action):**
- **F1 + V-1 + V-2** — one PR: `setup-vault.py:48` `0→1` **and** add `test_setup_provisioning.py` asserting first address = `c-000001` for both setup scripts.

**C. Unblock the pending decision:**
- **Ratify ADR-0005** → unblocks FUP-4 (`wiki-issues`), the highest-fan-out pending item (unblocks 2 downstream).

**D. Value backlog (triage, not urgent):**
- V-3 command-migration/rollback note for ADR-0001 · V-4 trim the 5 over-built planning artifacts · V-5 assert G0-optionality · V-6 reconcile section-whitelist · promote FUP-7 (V3) · V-7 EN/DE + manifest-token consistency.

---

## 5 · Fragment index (full evidence)

| Fragment | Covers |
|----------|--------|
| [structural-evidence.md](structural-evidence.md) | Phase 0 G0 — manifests, paths, links, citations, seeds, orphans, modeling |
| [a-counter.md](a-counter.md) | #1 counter/allocator (F1, F2) |
| [b-adr-status.md](b-adr-status.md) | #2 ADR coherence, #3 status parity, EN/DE |
| [c-wiki-issues.md](c-wiki-issues.md) | #4 skill-count, #5 constraint triad, #6 SPEC refs / path-safety |
| [d-cross.md](d-cross.md) | #7 PRD-vs-refactor cross-bundle (9 overlaps) |
| [v1-goldplating.md](v1-goldplating.md) | Phase 2 gold-plating (V-4, V-6) |
| [v2-gaps.md](v2-gaps.md) | Phase 2 high-value gaps (V-2, V-3, V-5) |
| [v3-sequencing.md](v3-sequencing.md) | Phase 2 sequencing leverage (V-1) |

_No files were edited during this audit. All findings are read-only until you approve a disposition._
