---
agent: A
check: "#1"
generated: 2026-07-01
scope: ADR-0004 (canonical address-counter start = 1) coherence across ADR / PRD-R3 / guide vs real scripts
files_read:
  - docs/adr/0004-canonical-address-counter-start.md
  - docs/prds/dragonscale.md
  - docs/dragonscale-guide.md
  - bin/setup-dragonscale.py
  - bin/setup-vault.py
  - scripts/allocate-address.py
---

# Cross-check #1 — ADR-0004 canonical address-counter start = 1

## Q1 — Does ADR-0004's "seed 0 → c-000000 / exit-3 (positive-integer validation)" claim match what allocate-address.py actually does?

**Verdict:** NO — partially wrong. Seed 0 deterministically yields `c-000000` **with exit 0 (success), no error**. The ADR's repeated claim that the allocator validates a *positive* integer and that seed 0 "risks an outright exit-3 error" / "collides with the allocator's positive-integer validation" is factually incorrect: the validation regex accepts `0`.

**Evidence — what the ADR claims:**
- `docs/adr/0004-canonical-address-counter-start.md:22` — "The allocator also validates that the counter is a **positive integer** (`allocate-address.py:96-100`, exit 3 on failure)."
- `docs/adr/0004-canonical-address-counter-start.md:27` — "Seed **0** → first allocation reads `0` → first page would be **`c-000000`** (off-by-one …), and, because the allocator requires a **positive** integer, a `0` seed risks an outright **exit-3 error** on first allocate depending on the validation branch."
- `docs/adr/0004-canonical-address-counter-start.md:37` — "Seed `0` as canonical — rejected: produces `c-000000` … and **collides with the allocator's positive-integer validation (risk of exit 3 on first allocate)**."
- `docs/adr/0004-canonical-address-counter-start.md:52` (Follow-up) — "Confirm the allocator's positive-integer validation branch (whether `0` errors or passes) when writing the FUP-2 test." *(The ADR itself flags this as unresolved.)*

**Evidence — what the code actually does (this audit resolves the branch):**
- `scripts/allocate-address.py:95` — `if not re.fullmatch(r"[0-9]+", raw):` — regex `[0-9]+` matches `"0"` (it is a **non-negative** integer check, NOT positive). Therefore for `raw == "0"` the branch is NOT taken → **no exit 3**.
- `scripts/allocate-address.py:100` — `return int(raw)` → returns `0`.
- `scripts/allocate-address.py:140-142` (allocate mode) — `current = read_or_recover_counter()` → `current == 0`; `COUNTER_FILE.write_text(f"{current + 1}\n")` writes `1`; `print("c-%06d" % current)` prints **`c-000000`**; function returns normally → **exit 0**.
- Corroboration that exit-3 fires only on non-numeric input: `scripts/allocate-address.py:29` docstring — "3 counter value corrupt/non-numeric, or unknown mode"; the error message at `:97` reads "content is not a positive integer" but the guard at `:96` (`re.fullmatch(r"[0-9]+", raw)`) does not enforce positivity — `0`, `00`, `000` all pass.

**Net:** The ADR is right that seed 0 gives the wrong address (`c-000000`, off-by-one), and its *decision* (canonical = 1) is sound. But its stated *rationale* — "positive-integer validation" and "risk of exit-3 on a 0 seed" — does not hold: the code accepts `0` and succeeds. The real defect of seed 0 is the silent off-by-one (`c-000000`), not an error.

- **Class:** fix-doc  *(ADR Context L22/L27, Alternatives L37, Follow-up L52: correct "positive integer"→"non-negative integer / `[0-9]+`" and drop/replace the "exit-3 risk" claim; resolve L52's open branch to "0 passes, prints c-000000, exit 0". The decision itself needs no change.)*
- **Severity:** med  *(ADR is an accepted, immutable-by-convention decision record whose stated technical rationale is verifiably false and misleads the FUP-2 test author, who is explicitly told at L52 to expect a possible error. Decision outcome unaffected, so not high.)*

---

## Q2 — Is counter=1 described consistently in PRD R3 and the guide? Any contradiction with the ADR?

**Verdict:** YES — consistent. Both the PRD (R3) and the guide state counter starts at `1` → first page `c-000001`, exactly matching ADR-0004's decision. No contradiction on the canonical value.

**Evidence:**
- `docs/prds/dragonscale.md:61` — "**R3 Setup & provisioning.** `bin/setup-dragonscale.py` … provisions `.vault-meta/`: **counter starting at 1 (first page `c-000001`)** …"
- `docs/dragonscale-guide.md:155` — "`address-counter.txt` **starts at `1`**, so the next reserved page address in a brand-new vault will be **`c-000001`**."
- `docs/dragonscale-guide.md:275` — "`c-` means creation-order counter. The numeric part is zero-padded to six digits." (address format matches `allocate-address.py:142` `"c-%06d"` and `ADDR_RE` at `:55` `c-([0-9]{6})`.)
- ADR agreement: `docs/adr/0004-canonical-address-counter-start.md:26` cites both surfaces — 'matching the documented behavior (guide "counter starts at 1 → `c-000001`"; DragonScale PRD R3)' — and `:33`/`:43` restate seed `1` → `c-000001`.
- Note: the guide (`:155`, `:275`) and PRD R3 (`:61`) describe only the **correct** `setup-dragonscale` path; neither surface repeats the ADR's erroneous "positive-integer / exit-3" reasoning, so the Q1 defect is localized to the ADR and does not propagate to PRD/guide.

- **Class:** ok
- **Severity:** low

---

## Q3 — Is setup-vault.py's seed 0 acknowledged as intentional/legacy, or is it an unflagged divergence?

**Verdict:** Acknowledged as an inconsistency to fix (flagged), NOT defended as intentional/legacy. It is a LIVE code↔doc divergence (carry-forward seed S-a confirmed): the docs/ADR canonicalize `1`, the `setup-vault.py` code still seeds `0`. Correctly classified flag-only — the doc/ADR is right; the code is the outlier.

**Evidence — the divergence (code seeds 0):**
- `bin/setup-vault.py:48` — `counter.write_text("0\n")` (inside `if not counter.is_file():`, L47). **Seeds 0.** ✅ S-a pinned.
- vs `bin/setup-dragonscale.py:52` — `counter.write_text("1\n")` then `:53` `print("OK  .vault-meta/address-counter.txt initialized at 1")`. **Seeds 1.** ✅ S-a pinned.
- The `setup-vault.py` comment block (L44-45) explains only that state is per-vault ("each vault initializes its own counter …"); it does **not** justify the `0` value as intentional or legacy — so the `0` is an unjustified literal, not a documented design choice.

**Evidence — it IS flagged (not unflagged) in the docs:**
- ADR: `docs/adr/0004-canonical-address-counter-start.md:20` names `bin/setup-vault.py:48 → seeds 0` as the divergent seed; `:33` — "`bin/setup-vault.py` (currently `0`) is the **outlier to be corrected (FUP-2)**"; `:51` — "**FUP-2** (bugfix): change `bin/setup-vault.py:48` seed `0` → `1` … *(Deferred — script edit, out of scope for this ADR round.)*"
- PRD: `docs/prds/dragonscale.md:81` — "**Counter-start inconsistency.** `setup-dragonscale.py` seeds the counter at `1` while `setup-vault.py` seeds `0` (code-level, surfaced in the 2026-07-01 docs audit). The canonical start value should be pinned. *(Owner decision; not resolved in this PRD — no script change here.)*"
- PRD open item: `docs/prds/dragonscale.md:90` — "[ ] Counter-start inconsistency (setup-dragonscale vs setup-vault) resolved" (unchecked).
- Guide: makes **no** mention of `setup-vault.py` or a `0` seed (guide `:155` documents only the `1` start). The guide is silent on the divergence — acceptable since it documents the intended contract, but it is the one surface that does not cross-reference the known outlier.

**Net:** The `0`-seed is a genuine code↔doc divergence, but it is *acknowledged and tracked* in both the ADR (FUP-2) and the PRD (open item), explicitly deferred as a code fix out of scope for the docs round. This is exactly the flag-only case: docs/ADR correct, code diverges, do not edit the script.

- **Class:** flag-only  *(code `setup-vault.py:48` diverges from the canonical ADR decision; fix belongs to FUP-2 script edit, not this docs audit. Do NOT edit the script.)*
- **Severity:** high  *(a real runtime defect — a vault provisioned via `setup-vault.py` allocates `c-000000` as its first address, off-by-one against every doc surface and the `setup-dragonscale` path; already correctly scoped to FUP-2.)*

---

**Roll-up:** 3 findings — high=1 (S-a code↔doc seed divergence, flag-only) · med=1 (ADR "positive-integer/exit-3" rationale factually wrong, fix-doc) · ok/low=1 (PRD R3 + guide consistent with ADR decision). Counts: high=1 med=1 low=1 ok=1 | fix-doc=1 flag-only=1 value=0 ok=1.
