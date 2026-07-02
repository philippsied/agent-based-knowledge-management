---
agent: C
checks: "#4,#5,#6"
generated: 2026-07-01
audit_base: 0a9916d
branch: docs/cmd-script-consolidation-plan
---

# Audit fragment C — skill count · constraint triad · SPEC references

Read-only documentation-consistency audit. Every finding cites `file:line` + actual quote.
Class ∈ {fix-doc | flag-only | value | ok}. Severity ∈ {high | med | low}.

---

## #4 — Skill-count story (one known gap vs. three contradicting truths)

**Verdict: OK — the drift is a single, consistently-governed known gap tracked as FUP-5. One low-sev flag on the drifted surface itself.**

**Ground truth (verified on disk):** 14 skill dirs contain `SKILL.md` — `autoresearch, canvas, defuddle, doc-pipeline, obsidian-bases, obsidian-markdown, research-brief, save, visualize, wiki, wiki-fold, wiki-ingest, wiki-lint, wiki-query`.

**FUP-5 is the canonical governance item** (the single "SSOT" that ties the three counts together):
- `docs/tasks/dragonscale-agentic-wiki-followups.md:37` — "**FUP-5** | Establish skill-count SSOT; fix drift (`copilot-instructions.md` says 13, disk has 14) | … | Single source for the skill inventory; all counts read 14; a lint/test guards future drift."

**Each count, in context:**
- `docs/prds/agentic-wiki.md:41` — "The **skill suite** (14 skills): ingest, query, lint, save, autoresearch, research-brief, doc-pipeline, defuddle, canvas, obsidian-bases, obsidian-markdown, visualize, and the `wiki` router." → states **14**.
- `docs/prds/agentic-wiki.md:87` — "**Inventory drift.** `.github/copilot-instructions.md` still says \"13 skills\" while 14 exist on disk (`visualize` is undocumented). There is no single source of truth for the skill count." → **explicitly names the 13-vs-14 drift as a known gap.**
- `docs/prds/agentic-wiki.md:95` — "- [ ] Skill-count single source of truth (fix copilot-instructions 13 → 14)" → follow-up item (the PRD backing for FUP-5).
- `docs/specs/SPEC-wiki-issues.md:72` — "… Skill count moves 14 → 15 (update SSOT, FUP-5)." → states **14→15** and ties it to FUP-5.
- `docs/adr/0005-skill-home-open-issues-commands.md:47` — "One more skill to maintain (14 → 15) … compounds the skill-count SSOT drift already tracked as FUP-5." and `:53` — "Update the skill count 14 → 15 wherever counted (ties to FUP-5)." → states **14→15**, ties to FUP-5.
- `.github/copilot-instructions.md:13` — "`skills/`: 13 skills (`autoresearch`, `canvas`, `defuddle`, `doc-pipeline`, `obsidian-bases`, `obsidian-markdown`, `research-brief`, `save`, `wiki`, `wiki-fold`, `wiki-ingest`, `wiki-lint`, `wiki-query`) …" → states **13** (omits `visualize`).

**Analysis:** This is NOT three independent contradicting claims. Disk=14 is truth; PRD asserts 14 AND flags the copilot 13 as drift; SPEC and ADR-0005 both carry 14→15 and explicitly point at FUP-5; FUP-5 (tasks doc) is the one SSOT item that will fix the copilot surface. The `copilot-instructions.md:13` "13" is precisely the stale value FUP-5 exists to correct — its existence is expected, not a contradiction.

- **Finding C4-a (low, flag-only):** `.github/copilot-instructions.md:13` states "13 skills" as a flat fact with **no inline marker** (no "known-stale / see FUP-5" pointer). A reader landing there directly has no signal it is the drifted surface. Evidence: line 13 quote above contains no FUP/drift reference (verified: grep for `FUP|drift|14|15|SSOT` in the file returns only line 13's skill list, no acknowledgment). Low severity because the drift is fully governed elsewhere; FUP-5 will resolve it.
- **Finding C4-b (low, value):** Minor list-vs-count nuance inside the PRD. `docs/prds/agentic-wiki.md:41` says "14 skills" but its inline enumeration names **13** items and **omits `wiki-fold`** (present on disk and in the copilot list); `copilot-instructions.md:13` conversely enumerates 13 but omits `visualize`. Neither enumerated list equals the on-disk 14. Not a count contradiction (both the 14 headline and FUP-5 are correct), but the PRD's own name-list is internally short by one. Worth folding into FUP-5's "all counts read 14" SSOT work.

Class: **ok** (story is coherent) · residual low-sev flags C4-a (flag-only), C4-b (value).

---

## #5 — Template ⇄ SPEC-wiki-issues ⇄ ADR-0005 constraint agreement

**Verdict: OK — all five constraints agree across the three required sources. One cross-scope divergence flagged (section whitelist vs. the `commands/` migration source).**

Sources: T = `docs/templates/open-issues.md` · S = `docs/specs/SPEC-wiki-issues.md` · A = `docs/adr/0005-skill-home-open-issues-commands.md`.

### Agreement matrix (constraint × source)

| Constraint | Template (T) | SPEC (S) | ADR-0005 (A) | Verdict |
|---|---|---|---|---|
| **Field names** (id, priority, section, title, pushed, blocked_by; opt. inconclusive_reason, aggregated_from) | T:29-36 ✓ (all 6 + 2 optional) | S:21 ✓ (identical set incl. both optionals) | A:59 ✓ (id, priority, section, title, pushed, blocked_by) | **match** |
| **`I-YYYY-NNN` id scheme** (year-resetting, never recycled) | T:29,62,105 ✓ ("`id` matches `I-YYYY-NNN`, unique, never recycled") | S:21,27 ✓ ("`I-YYYY-NNN` … year-resetting, never recycled") | A:61 ✓ ("ID `I-YYYY-NNN`, year-resetting, never recycled") | **match** |
| **4-key sort invariant** (priority ASC · ready-first · inconclusive-last · pushed DESC) | T:26-27 ✓ (all 4 keys, same order) | S:31 ✓ ("**sort** (4-key invariant)"), :42 (inconclusive sorts last) | A:60 ✓ ("priority ASC · ready-first … · inconclusive-last · `pushed` DESC") | **match** |
| **Section whitelist** | T:58 ✓ enumerates 8: `enforcement · lint · tooling · docs · skills · hooks · ci · dragonscale` | S:21 defers ("`section` (whitelist)"), no list | A:66 defers ("controlled vocabulary, tuned to plugin domains"), no list | **match** (T enumerates; S & A defer without conflict) |
| **4 dispositions** (resolved / patched / inconclusive + hard-delete→log) | T:42-43,95 ✓ ("resolved (removed …) \| patched (stale) \| inconclusive"; resolved→[[log]]) | S:40-42,60 ✓ (resolved/fixed→hard-delete+`log.md`; patched; inconclusive) | A:63-64 ✓ ("resolved (hard-delete), patched (stale), inconclusive"; history→`log.md`) | **match** |

All five rows **match** within {T, S, A}. On the whitelist row, only the template enumerates concrete values; SPEC and ADR-0005 intentionally point at the template/reference for the list, so there is no contradiction among the three.

**Supporting quotes (whitelist + dispositions, the two rows most prone to drift):**
- T:58 — "`enforcement` · `lint` · `tooling` · `docs` · `skills` · `hooks` · `ci` · `dragonscale`"
- A:66 — "**Section whitelist** — controlled vocabulary, tuned to plugin domains." (no enumeration)
- S:40 — "**resolved/fixed** → hard-delete stack item + body section; append a `log.md` entry (`Resolved (removed from OPEN-ISSUES.md): I-YYYY-NNN … + \"now N items, lint green\"`)."
- A:64 — "**Hard-delete on resolve** — history goes to `log.md` … The file stays a live queue, not a graveyard."

- **Finding C5-a (med, value):** Section-whitelist divergence against the **migration source** (out of the T/S/A triad but directly relevant, since SPEC ports these commands). The template's 8-value list `enforcement · lint · tooling · docs · skills · hooks · ci · dragonscale` (T:58) does **not** match the 7-value whitelist defined in the command that SPEC absorbs — `commands/wiki/handoff.md` (indexed): "Section-Whitelist (genau diese 7): `enforcement` · `lint` · `vault-content` · `tooling` · `templates` · `skill-plugin` · `eval-observability`". Only `enforcement`, `lint`, `tooling` overlap; the other 5 differ on each side. SPEC:63/AC and A:66 both say the whitelist is a binding constraint but neither reconciles the two lists. When `wiki-issues` is built (SPEC gates fixtures on parity with the ported commands), the implementer must decide which whitelist is canonical. Class: value (design decision to surface), med severity — a controlled vocabulary that silently changes during migration can strand existing issues' `section` values. Note: the `commands/` file is outside the "never touch docs artifacts / your scope files" set; flagged, not to be edited by this audit.

Class: **ok** for the T/S/A triad · residual C5-a (value, med) for the template-vs-command whitelist gap.

---

## #6 — SPEC-wiki-issues references resolve & are accurate

**Verdict: OK on all three references. The path-safety concern does NOT materialize — the hook whitelists `wiki/` by prefix, so `wiki/meta/OPEN-ISSUES.md` is writable. No high-sev flag.**

### 6a — ADR-0002 (colocation) reference
- `docs/specs/SPEC-wiki-issues.md:54` — "Skill layout per [ADR-0002](../adr/0002-colocate-scripts-under-skill.md): `skills/wiki-issues/SKILL.md` + `skills/wiki-issues/scripts/lint-open-issues.py` + `skills/wiki-issues/references/open-issues-template.md`."
- ADR-0002 decision, `docs/adr/0002-colocate-scripts-under-skill.md:21` — "Jedes Skript zieht unter `skills/<besitzender-skill>/scripts/`; Code der von >1 Skill genutzt wird zieht nach `lib/`." (link path resolves — file exists, `status: accepted`, :4).
- **Accurate.** SPEC's layout (skill's own validator under `skills/wiki-issues/scripts/`) is exactly ADR-0002's "each script colocated under `skills/<owning-skill>/scripts/`; shared → `lib/`". `lint-open-issues.py` is single-skill-owned, so it correctly stays under the skill, not `lib/`. **Class: ok.**

### 6b — ADR-0004 (allocator semantics) reference
- `docs/specs/SPEC-wiki-issues.md:54` — "Reuse the DragonScale pattern: a counter-under-lock allocator for ids (see [ADR-0004](../adr/0004-canonical-address-counter-start.md) semantics) …". Also S:27 "allocate fresh `I-YYYY-NNN` (year-resetting, never recycled)".
- ADR-0004, `docs/adr/0004-canonical-address-counter-start.md:22` — "The allocator `scripts/allocate-address.py` is **read-then-increment**: `allocate` reads the counter as `current`, prints `c-%06d % current`, then writes `current + 1` … The allocator also validates that the counter is a **positive integer**." (link resolves — file exists, `status: accepted`, :4/:13).
- **Accurate, with one nuance.** SPEC borrows the *mechanism* (monotonic counter-under-lock, read-then-increment, never-recycled ids) — a faithful match to ADR-0004's semantics. ADR-0004 governs a **vault-global, never-resetting** `c-NNNNNN` counter; the issue scheme is **`I-YYYY-NNN`, year-resetting** (S:27, A:61). SPEC/ADR-0005 are explicit that ids reset per year, so this is an intentional adaptation, not a misread — SPEC cites ADR-0004 for "semantics" (allocator behavior), not for the reset policy. **Class: ok** (adaptation is stated, not silent).

### 6c — Path-safety whitelist vs. `wiki/meta/` (the high-sev candidate)
- SPEC assumption, `docs/specs/SPEC-wiki-issues.md:69` — "Writes only into `wiki/meta/` (+ `log.md`) — inside the path-safety hook whitelist." (and S:16 the file is `wiki/meta/OPEN-ISSUES.md`).
- **Hook actually allows it — verified by reading the whitelist logic:**
  - `hooks/wiki-path-safety.py:139-140` — "`if _is_under(abs_path, vault_root + \"/wiki\"): allowed = 1`".
  - `hooks/wiki-path-safety.py:78` — `_is_under` is a **prefix** test: "`return abs_path.startswith(root + \"/\")`".
  - Therefore any path under `wiki/` — including `wiki/meta/OPEN-ISSUES.md` and `wiki/meta/log.md` — satisfies the whitelist. There is no exact-match restriction on `wiki/` (the exact-match branches at :141,:149-156 are only for the standalone root files like `CLAUDE.md`, `.raw/.manifest.json`).
  - Corroborating: `hooks/wiki-path-safety.py:224` already treats `wiki/meta/` as an established writable location — "`if abs_path.startswith(vault_root + \"/wiki/meta/lint-report-\")`" (lint reports are written there today).
- **Verdict: SPEC's assumption is CORRECT. The high-sev risk does NOT exist.** `wiki/meta/` is writable because it is a subdirectory of the whitelisted `wiki/` prefix. **Class: ok**, no flag.

Class for #6: **ok** on all three sub-checks (references resolve, descriptions accurate, path-safety assumption holds).

---

## Roll-up

#4 skill-count drift is one coherent FUP-5-governed gap (not 3 contradictions) with 2 low residual flags; #5 all five constraints agree across template/SPEC/ADR-0005, with one med cross-scope whitelist divergence vs. the ported `commands/` source; #6 all three SPEC references resolve and are accurate — the `wiki/meta/` path-safety concern is disproven (hook prefix-whitelists `wiki/`).

**Counts:** high=0 med=1 low=2 ok=6 (checks/subchecks passing) | fix-doc=0 flag-only=1 value=2 (+3 ok-verdict checks)
