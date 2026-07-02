---
artifact: adr
number: 0004
status: accepted     # proposed | accepted | superseded-by:NNNN
manifest: docs/manifests/dragonscale-agentic-wiki-followups.json
---

# ADR-0004 — Canonical address-counter start value

> **Anchors (7 W):** Why (context + consequences) · What (the decision) · With-what (alternatives)

## Status
accepted (2026-07-01)   <!-- superseded by ADR-NNNN if revisited -->

> **Rationale correction (2026-07-01, audit `docs/audit/2026-07-01/`):** the original Context/Alternatives claimed a `0` seed risks an allocator *exit-3 / positive-integer* error. That is **false** — `read_or_recover_counter()` validates with `re.fullmatch(r"[0-9]+", …)` (`scripts/allocate-address.py:95`), so `0` **passes** and `allocate` prints `c-000000` at **exit 0** — a *silent* off-by-one, not an error. The decision (seed = `1`) is unchanged; only the rationale below is corrected.

## Context  ‹Why›

DragonScale Mechanism 2 (deterministic addresses) reserves page IDs of the form `c-NNNNNN` from a monotonic counter in `.vault-meta/address-counter.txt`. Two setup scripts seed that counter with **different** values:

- `bin/setup-dragonscale.py:52` → seeds `1`.
- `bin/setup-vault.py:48` → seeds `0`.

The allocator `scripts/allocate-address.py` is **read-then-increment**: `allocate` reads the counter as `current`, prints `c-%06d % current`, then writes `current + 1` (`allocate-address.py:140-142`); `--peek` prints the current value; `--rebuild` sets the counter to `scan_max_c_address() + 1`. The counter file therefore holds *"the next address to allocate."* The allocator validates the counter with `re.fullmatch(r"[0-9]+", …)` (`allocate-address.py:95-100`) — a **non-negative** integer, so `0` **passes**; only non-numeric content exits 3.

Under these semantics the divergent seeds diverge in behavior:

- Seed **1** → first allocation reads `1` → first page is **`c-000001`**, matching the documented behavior (guide "counter starts at 1 → `c-000001`"; DragonScale PRD R3).
- Seed **0** → first allocation reads `0` → first page is **`c-000000`** (off-by-one vs the documented `c-000001`). The failure is **silent**: `0` satisfies the allocator's `[0-9]+` check (`allocate-address.py:95`) and `allocate` prints `c-000000` at **exit 0** (`allocate-address.py:140-142`) — no exit-3 guard catches it. Seed `0` contradicts the documented contract with no error signal.

This is the **FUP-1** decision from [docs/tasks/dragonscale-agentic-wiki-followups.md](../tasks/dragonscale-agentic-wiki-followups.md); it gates **FUP-2** (aligning the two scripts).

## Decision  ‹What›

The canonical counter start value is **`1`**: `.vault-meta/address-counter.txt` is seeded at `1` so the first allocated address is `c-000001`, consistent with the read-then-increment allocator and the documented behavior. `bin/setup-vault.py` (currently `0`) is the outlier to be corrected (FUP-2); `bin/setup-dragonscale.py` (`1`) is already correct.

## Alternatives  ‹With-what›

- **Seed `0` as canonical** — rejected: produces `c-000000` as the first address (off-by-one vs docs), and does so **silently** — the allocator's `[0-9]+` check accepts `0`, so nothing errors. Would also require rewriting the guide/PRD and the "starts at 1" contract.
- **Change the allocator to pre-increment** (read `current+1`, store, print) so a `0` seed yields `c-000001` — rejected: larger blast radius on shipped Mechanism-2 semantics, touches `allocate-address.py` plus its tests and the `--peek`/`--rebuild` invariants, and shifts the meaning of every existing vault's counter file by one. Disproportionate to a one-line seed fix.

## Consequences  ‹Why: outcomes›

**Good:**
- Single, documented contract: the counter holds "next address," seeded at `1`, first page `c-000001`.
- Smallest possible change surface — one seed literal in `setup-vault.py`, no allocator changes.
- Removes the silent `c-000000` off-by-one from a `0`-seeded vault (no exit-3 guard exists — the bug is otherwise undetected).

**Bad / cost:**
- A vault already initialized by `setup-vault.py` with a `0` counter that has *not yet* allocated an address shifts from `c-000000` to `c-000001` semantics; a vault that already allocated `c-000000` needs a one-time `--rebuild` / migration note. (Believed rare; flagged for FUP-2.)

**Follow-up work:**
- **FUP-2** (bugfix): change `bin/setup-vault.py:48` seed `0` → `1`; add a test asserting the first allocation is `c-000001`; note migration for any `c-000000` vault. *(Executed 2026-07-01: seed fixed + `tests/test_setup_provisioning.py` added, 9 checks green.)*
- **Confirmed** (FUP-2): `0` passes the `[0-9]+` check and yields `c-000000` at exit 0 (no error) — so the guard is a silent off-by-one, not an exit-3. `tests/test_setup_provisioning.py` asserts the first allocation is `c-000001`.

---
### Checklist
- [x] Context names the real forces  ‹Why›
- [x] Decision clear in 1 sentence  ‹What›
- [x] ≥1 serious alternative + reason for rejection  ‹With-what›
- [x] Consequences both good AND bad
- [x] Status set (proposed — owner ratifies → accepted; immutable, change = new ADR)
