---
artifact: prd
slug: dragonscale
status: draft        # draft | review | approved
related: docs/dragonscale-guide.md, docs/releases/v1.6.0.md, CHANGELOG.md
---

# PRD — DragonScale Memory

> Answers: WHAT are we building & WHY? For whom? How do we measure success?
> **No HOW** — operational mechanics live in [docs/dragonscale-guide.md](../dragonscale-guide.md); the shipped baseline is [docs/releases/v1.6.0.md](../releases/v1.6.0.md).
> **Anchors (5 W):** Why · What · What-not · When-done · With-what — no How.

## 1. Problem & Evidence  ‹Why›

An always-on wiki vault decays as it grows, in four specific ways:

- **Unbounded log.** `wiki/log.md` is append-only. Without rollup it grows without bound and the signal in older entries becomes unreachable.
- **Unstable identity.** Pages have no durable ID. Renames and re-ingestion break inbound links and make it impossible to reliably refer to "the same page" across sessions.
- **Silent duplication.** Near-duplicate pages accumulate because nothing detects semantic overlap at ingest/lint time.
- **Frontier-blind research.** `/autoresearch` with no explicit topic has no notion of *where* knowledge is thin, so it cannot self-direct toward the growth edge.

These are structural, not cosmetic: each compounds with vault size. DragonScale adds four conservative, deterministic, opt-in helpers — one per decay mode. The name is taken from the Heighway *dragon curve*, a fractal built by recursive paper-folding: recursive folding motivates hierarchical log rollup, and the curve's self-similar boundary motivates a frontier-first research agenda. The name signals structure and self-similarity — not an optimality claim.

## 2. Target users / Beneficiaries  ‹What: for whom›

- **Vault owners** who ingest continuously and need the knowledge base to stay navigable and trustworthy at scale.
- **Claude (the agent)** as the primary reader: stable addresses, deduplicated pages, and rolled-up logs directly improve retrieval precision and reduce wasted context.
- **Cross-project consumers** that reference this vault from other repositories and depend on stable page identity for durable links.

## 3. Goals & Success metrics  ‹When-done›

| # | Goal | Success metric (binary / measurable) |
|---|------|--------------------------------------|
| G0 | Stay strictly optional | If setup is never run, base vault + original skill behavior are **unchanged** (feature-detected). |
| G1 | Bound the log via rollup | Fold produces extractive, structurally-idempotent meta-pages; re-running fold on unchanged input yields **no diff**; the source log is never mutated. |
| G2 | Give every page a stable identity | Every new page receives a unique `c-NNNNNN`; re-ingesting the same source **reuses** its address (0 duplicate addresses; address map stable across re-ingest). |
| G3 | Stop duplicates before they spread | Any page pair with cosine similarity ≥ 0.90 is surfaced as an **error** in lint; 0.80–0.90 as **review**. |
| G4 | Make no-topic research frontier-aware | No-topic `/autoresearch` ranks candidates by boundary score and proposes the top-N frontier pages; the user keeps the final topic choice. |

## 4. Scope  ‹What / What-not›

**In scope**
- The four mechanisms: Fold, Deterministic Addresses, Semantic Tiling Lint, Boundary-First Autoresearch.
- `bin/setup-dragonscale.py`: idempotent provisioning of `.vault-meta/` (counter, threshold seed, legacy-pages manifest).
- Feature detection so each mechanism activates only when `.vault-meta/` is present.
- Opt-in integration points in the `wiki-fold`, `wiki-ingest`, `wiki-lint`, and `autoresearch` skills.

**Out of scope**
- The base platform (vault ingest/query/lint/setup) — that is the Agentic-Wiki platform, not DragonScale.
- Any hard dependency: DragonScale must never be required for base operation.
- Mutating `.raw/` sources (immutable) or rewriting page bodies.
- Cloud/hosted embeddings — Mechanism 3 uses a **local** model only (`ollama` + `nomic-embed-text`); if absent, only M3 is blocked.
- Abstractive/LLM summarization in Fold (extractive by design, to stay deterministic and hallucination-free).

## 5. Requirements (prioritized)  ‹What›

**P0 — core, must ship**
- **R1 Fold operator (Mechanism 1).** Extractive rollup of `wiki/log.md` into `wiki/folds/fold-k{K}-from-{start}-to-{end}-n{N}.md`. Dry-run is the default; committing a fold requires an explicit action. Structurally idempotent and non-destructive (log preserved).
- **R2 Deterministic addresses (Mechanism 2).** `scripts/allocate-address.py` allocates `c-NNNNNN` (6-digit, creation-order counter — **not** a content hash). Atomic under `fcntl.flock` on `.vault-meta/.address.lock` (5 s lock timeout). Modes: `allocate` (default), `--peek`, `--rebuild`. Re-ingest idempotency via the `.raw/` manifest `address_map`. Exit codes 0/1/2/3.
- **R3 Setup & provisioning.** `bin/setup-dragonscale.py` is idempotent, accepts an optional vault path, and provisions `.vault-meta/`: counter starting at 1 (first page `c-000001`), threshold seed, and a legacy-pages manifest with rollout baseline `2026-04-23`.

**P1 — high value**
- **R4 Semantic tiling lint (Mechanism 3).** `scripts/tiling-check.py` embeds pages via local `nomic-embed-text` (ollama) and bands cosine similarity: **error ≥ 0.90**, **review 0.80–0.90**, **pass < 0.80**. Modes `--peek` / `--report`. Lock on `.vault-meta/.tiling.lock`. Exit codes 10/11. Thresholds live in `.vault-meta/` and are user-calibrable.
- **R5 Boundary-first autoresearch (Mechanism 4).** `scripts/boundary-score.py` ranks pages by `boundary_score(p) = (out_degree(p) − in_degree(p)) × exp(−days_since_updated / 30)` (recency half-life 30 days, no floor), excluding index/meta files. Feeds no-topic `/autoresearch`; supports `--json` and `--top N`. The user retains topic choice.

**P2 — supporting**
- **R6 Reversible off-switch.** Stopping the DragonScale skills/scripts returns the vault to base behavior with no cleanup required; the disable path is documented.
- **R7 Skill feature-detection.** `wiki-fold`, `wiki-ingest`, `wiki-lint`, and `autoresearch` detect `.vault-meta/` and enable DragonScale paths only when present.

## 6. Constraints & Assumptions  ‹With-what›

- **Determinism.** Same input → same output for addresses, folds, and scores. No randomness; no wall-clock in outputs beyond documented date ranges.
- **Locking.** Uses Python's standard-library `fcntl.flock` (POSIX `flock(2)`); **no** util-linux `flock(1)` CLI. Works on macOS and Linux with a stock `python3`.
- **Local-only embeddings.** M3 assumes local `ollama` + `nomic-embed-text`; graceful degradation when absent (only M3 blocked).
- **Immutable sources.** `.raw/` is never modified by any mechanism.
- **Optionality is a hard invariant**, not a preference: the base vault must build and run identically with DragonScale absent.

## 7. Risks & open questions

- **Counter-start inconsistency.** `setup-dragonscale.py` seeds the counter at `1` while `setup-vault.py` seeds `0` (code-level, surfaced in the 2026-07-01 docs audit). The canonical start value should be pinned. *(Owner decision; not resolved in this PRD — no script change here.)*
- **Tiling thresholds are seed values.** The 0.90 / 0.80 bands are conservative defaults; false-positive/negative rates are unquantified and need per-vault calibration data.
- **Fold granularity (`k`).** The rollup fan-in `k` trades summary density against traceability; there is no adaptive policy yet.
- **Version anchor.** The guide is pinned to `v1.6.0`; behavior is verified unchanged through `v1.10.1`, but the anchor must track future behavior changes.

### Checklist (before status: approved)
- [x] All four mechanisms verified against shipped scripts (docs audit, 2026-07-01)
- [ ] G0 "strictly optional" asserted by a test/lint proving each mechanism (fold, addresses, tiling) is skippable and the vault returns to base behavior when disabled (audit V-5, via FUP-8)
- [ ] Success metrics G1–G4 expressed as CI/lint assertions
- [ ] Reversible disable path documented end-to-end
- [ ] Counter-start inconsistency (setup-dragonscale vs setup-vault) resolved
