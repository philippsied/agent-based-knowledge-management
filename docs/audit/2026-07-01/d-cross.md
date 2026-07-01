---
agent: D
check: "#7"
generated: 2026-07-01
scope: "DragonScale PRD (product) vs SPEC-cmd-script-consolidation-dragonscale (refactor)"
verdict: complementary — no contradiction
---

# Cross-check #7 — DragonScale PRD vs cmd-script-consolidation SPEC (dragonscale module)

**Relationship under test:** PRD = product-level (WHAT the DragonScale memory feature IS + WHY);
SPEC = refactor-level (WHERE the three dragonscale scripts live after co-location). They are meant
to be complementary. Task: verify no conflicting claims on script locations, counter behavior, skill
ownership, file paths, or naming; where both name the same artifact, confirm they agree.

Files (only these read):
- `docs/prds/dragonscale.md`
- `docs/specs/SPEC-cmd-script-consolidation-dragonscale.md`

Note: reference-integrity (#8) + manifest-health (#9) were verified green in Phase 0
(`docs/audit/2026-07-01/structural-evidence.md`) — not re-run here.

---

## Overlap analysis (every shared artifact)

### O1 — `boundary-score.py` (Mechanism 4 scorer)
- **Verdict:** AGREE.
- **Evidence:**
  - PRD `docs/prds/dragonscale.md:65` — "**R5 …** `scripts/boundary-score.py` ranks pages by `boundary_score(p) = (out_degree(p) − in_degree(p)) × exp(−days_since_updated / 30)` … Feeds no-topic `/autoresearch`; supports `--json` and `--top N`."
  - SPEC `docs/specs/SPEC-cmd-script-consolidation-dragonscale.md:33` — "`boundary-score.py` | 316 | `skills/autoresearch/scripts/` | … `:121` ruft `./scripts/boundary-score.py --json --top 5` für No-Topic-Frontier-Auswahl (Mechanism 4) … **Einziger funktionaler Aufrufer = autoresearch.**"
  - SPEC `:143` AC-1 — "`boundary-score.py` liegt unter `skills/autoresearch/scripts/`; `scripts/boundary-score.py` existiert nicht mehr."
- **Agreement:** same script, same consumer (autoresearch), same flags (`--json`/`--top N` vs `--top 5`, N specialized). PRD names the current flat path `scripts/boundary-score.py`; SPEC relocates it to `skills/autoresearch/scripts/`. The path change is the SPEC's whole purpose — not a contradiction of the PRD's product description.
- **Class:** `ok`. **Severity:** —

### O2 — `tiling-check.py` (Mechanism 3 semantic tiling lint)
- **Verdict:** AGREE.
- **Evidence:**
  - PRD `:64` — "**R4 …** `scripts/tiling-check.py` embeds pages via local `nomic-embed-text` (ollama) … **error ≥ 0.90**, **review 0.80–0.90**, **pass < 0.80**. Modes `--peek` / `--report`. Lock on `.vault-meta/.tiling.lock`. Exit codes 10/11."
  - SPEC `:34` — "`tiling-check.py` | 500 | `skills/wiki-lint/scripts/` … Mechanism 3, semantic tiling … **Besitzer = wiki-lint.**"
  - SPEC `:102-108` — "ollama + `nomic-embed-text` … Feature-Gate-Exit-Codes **10** … und **11** … `.vault-meta/.tiling.lock` flock … `--report`-Pfad gegen `VAULT_ROOT` validiert."
- **Agreement:** identical on model dependency (ollama + nomic-embed-text), exit codes (10/11), lock file (`.vault-meta/.tiling.lock`), and modes (`--peek`/`--report`). SPEC only relocates path (`scripts/` → `skills/wiki-lint/scripts/`) and preserves all behavior bit-for-bit (`:108` "Move ändert **nur** den Skript-Pfad, keine Logik").
- **Class:** `ok`. **Severity:** —

### O3 — `allocate-address.py` + counter behavior (Mechanism 2)
- **Verdict:** AGREE.
- **Evidence:**
  - PRD `:60` — "**R2 …** `scripts/allocate-address.py` allocates `c-NNNNNN` (6-digit, creation-order counter — **not** a content hash). Atomic under `fcntl.flock` on `.vault-meta/.address.lock` (5 s lock timeout). Modes: `allocate` (default), `--peek`, `--rebuild` … Exit codes 0/1/2/3."
  - SPEC `:35` — "`allocate-address.py` | 153 | `skills/wiki-ingest/scripts/` | **ingest-Zeit, nicht fold-Zeit** … der **Schreib-Aufruf** (reserviert Adresse) sitzt in wiki-ingest … `wiki-lint` … nutzt nur `--peek` **read-only** … → Konsument, nicht Besitzer. **Besitzer = wiki-ingest.**"
  - SPEC `:70-71` — "`allocate-address.py` trägt **nichts** zu `lib/` bei … seine Adress-Mathematik (`scan_max_c_address`, `read_or_recover_counter`, `acquire_lock`) bleibt im Skript unter `wiki-ingest`."
- **Agreement:** same script, same address format (`c-NNNNNN`), same `--peek` mode, same lock semantics. The counter/address *math* stays inside the script (SPEC does not alter it). SPEC additionally pins the owning skill (wiki-ingest) and the consumer relationship (wiki-lint `--peek` read-only) — a sharpening, fully consistent with PRD R2.
- **Class:** `ok`. **Severity:** —

### O4 — Counter start value (the known 1-vs-0 open question)
- **Verdict:** AGREE (no conflict; SPEC deliberately out of scope on this).
- **Evidence:**
  - PRD `:61` — "counter starting at 1 (first page `c-000001`)"; PRD `:81` — "**Counter-start inconsistency.** `setup-dragonscale.py` seeds the counter at `1` while `setup-vault.py` seeds `0` … The canonical start value should be pinned. *(Owner decision; not resolved in this PRD — no script change here.)*"
  - SPEC `:19` — "Reiner Refactor — gleiche Inputs → gleiche Outputs (PRD §4 Out, ADR-0002)."; SPEC `:159-160` — "es wird kein Sicherheitsverhalten geändert, nur der Skript-Pfad."
- **Agreement:** the counter-start question is a *behavioral/product* concern the PRD owns and explicitly leaves open. The SPEC is a pure path/structure refactor that changes **no** behavior, so it neither restates nor contradicts the counter value. No overlap-conflict. (Note: this is the same 1-vs-0 item tracked separately in ADR-0004; the SPEC correctly stays silent on it.)
- **Class:** `ok`. **Severity:** —

### O5 — Setup / installer script name (`bin/setup-dragonscale.py`)
- **Verdict:** AGREE.
- **Evidence:**
  - PRD `:45` — "`bin/setup-dragonscale.py`: idempotent provisioning of `.vault-meta/` …"; PRD `:61` — "**R3 …** `bin/setup-dragonscale.py` is idempotent … provisions `.vault-meta/`."
  - SPEC `:78-79` — installer is a reference to update: "`bin/setup-dragonscale.py` (Zeilen 37, 46 — Installer-Copy + chmod)" and "(Zeilen 36, 45, 118 — Copy + chmod + `--peek`-Smoke-Test)"; SPEC `:147` AC-5 lists "`bin/setup-dragonscale.py` (Copy-Liste + chmod + `--peek`)".
- **Agreement:** both use the identical installer path/name `bin/setup-dragonscale.py`. PRD describes what it *does* (provision `.vault-meta/`); SPEC describes it as a caller whose script-copy list must be updated after the move. Complementary roles, same artifact, no naming conflict.
- **Class:** `ok`. **Severity:** —

### O6 — Skill ownership / integration points (the one point I flagged for scrutiny)
- **Verdict:** AGREE — no contradiction after close reading.
- **Evidence:**
  - PRD `:47` — "Opt-in integration points in the `wiki-fold`, `wiki-ingest`, `wiki-lint`, and `autoresearch` skills."; PRD `:69` — "**R7 …** `wiki-fold`, `wiki-ingest`, `wiki-lint`, and `autoresearch` detect `.vault-meta/` and enable DragonScale paths only when present."
  - SPEC `:35` — "**ingest-Zeit, nicht fold-Zeit** (offene Frage aufgelöst) … `skills/wiki-fold/SKILL.md` ruft es **nicht** auf."
- **Why no conflict:** The PRD's four-skill list is the *feature-detection surface across all four mechanisms* — one mechanism per skill: Fold→`wiki-fold` (PRD R1 `:59`), Addresses→(ingest), Tiling→`wiki-lint` (R4), Boundary→`autoresearch` (R5). The PRD nowhere claims `wiki-fold` calls `allocate-address.py`: PRD R1 `:59` scopes `wiki-fold` strictly to rolling up `wiki/log.md`, and PRD R2 `:60` names **no** calling skill for the allocator. So the SPEC's statement that `wiki-fold` does not call `allocate-address` (and that allocation is ingest-time) *resolves an ambiguity the PRD left open* — the SPEC even labels it "offene Frage aufgelöst" (open question resolved). It sharpens, it does not overturn a PRD assertion.
- **Class:** `ok`. **Severity:** — (would be `value` only if one wanted to backport the ingest-time clarity into PRD R2; not required — no defect.)

### O7 — `lib/dragonscale_pages.py` (new shared module)
- **Verdict:** COMPLEMENTARY — no conflict.
- **Evidence:**
  - SPEC `:53` — "**Neues Modul:** `lib/dragonscale_pages.py` — DragonScale-Seiten-Policy … genutzt von `boundary-score` (in `autoresearch`) und `tiling-check` (in `wiki-lint`)."; SPEC `:146` AC-4.
  - PRD — no mention (product-level document; the extraction of shared exclude-policy/`log` into a `lib/` module is a refactor-internal implementation detail).
- **Agreement:** the new `lib/` module is below the PRD's altitude by design; the PRD is silent, not contradictory. No shared claim to conflict on.
- **Class:** `ok`. **Severity:** —

### O8 — `lib/vault_root.py` placement authority
- **Verdict:** COMPLEMENTARY — SPEC defers to PRD.
- **Evidence:**
  - SPEC `:23` — "gemeinsam ist heute nur `from vault_root import resolve_vault_root` (`lib/vault_root.py`, bleibt `lib/` laut PRD §6)."
  - PRD §6 `:71-77` — constraints/assumptions (stdlib `fcntl.flock`, local-only embeddings, immutable sources, optionality). PRD does not name `vault_root.py`, but the SPEC cites §6 as the authority keeping shared util in `lib/`.
- **Agreement:** SPEC explicitly cites the PRD as the governing authority for the `lib/` placement — the definition of complementary, not contradictory.
- **Class:** `ok`. **Severity:** —

### O9 — Determinism + optionality invariant
- **Verdict:** AGREE.
- **Evidence:**
  - PRD `:73` — "Same input → same output for addresses, folds, and scores."; PRD `:77` — "**Optionality is a hard invariant** … the base vault must build and run identically with DragonScale absent."
  - SPEC `:19` — "Reiner Refactor — gleiche Inputs → gleiche Outputs"; SPEC `:113-116` — a forgotten reference makes the "optionaler DragonScale-Pfad **verstummt** (no-op), statt hart zu brechen — deckt sich mit dem bestehenden Opt-in-Muster."
- **Agreement:** the SPEC's refactor invariant (same in→same out) and its silent-no-op fallback are exactly the PRD's determinism + hard-optionality guarantees. Mutually reinforcing.
- **Class:** `ok`. **Severity:** —

---

## `.sh` historical-reference check (carry-forward seed S-d)
Neither file in scope cites `bin/setup-dragonscale.sh` or `scripts/allocate-address.sh` as a current
instruction. PRD uses `.py` paths throughout (`:45,:60,:61,:64,:65`); SPEC uses `.py` paths
throughout (`:33-35,:77-79`) and even lists `docs/plans/PLAN-sh-to-py-full-migration.md` (`:78-79`)
as a *reference to update*, i.e. it treats the `.sh`→`.py` migration as historical. No misleading
current `.sh` instruction present. Consistent with commit 3710c15 policy — nothing to flag.

---

## Roll-up
Complementary as intended: all nine shared artifacts (three scripts, counter/address semantics,
installer name, skill ownership, two `lib/` modules, determinism/optionality) AGREE. The PRD supplies
the product-level flat-path `scripts/`/`bin/` description of the current feature; the SPEC relocates
those same scripts to `skills/<skill>/scripts/` and cites the PRD as authority where they touch. The
one flagged point (wiki-fold vs allocate-address ownership) is the SPEC *resolving* an ambiguity the
PRD deliberately left open — a sharpening, not a contradiction. **No conflict found; verdict `ok`.**
