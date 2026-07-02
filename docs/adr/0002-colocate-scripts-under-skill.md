---
artifact: adr
number: 0002
status: accepted
manifest: docs/manifests/cmd-script-consolidation.json
---

# ADR-0002 — Skripte unter besitzenden Skill co-located; shared → lib/

> **Anker (7 W):** Warum (Kontext + Konsequenzen) · Was (die Entscheidung) · Womit (Alternativen)

## Status
accepted (2026-07-01)

## Kontext  ‹Warum›
17 Skripte (~3745 LOC) liegen flach in `scripts/` + `bin/`, gekoppelt je Cluster, aber nicht
beim Skill der sie besitzt. `skills/doc-pipeline/scripts/` zeigt bereits Co-location als etabliertes
Muster. Flache Ablage erschwert Ownership + Discoverability.

## Entscheidung  ‹Was›
Jedes Skript zieht unter `skills/<besitzender-skill>/scripts/`; Code der von >1 Skill genutzt wird
zieht nach `lib/`.

**Ziel-Mapping (Prinzip — Detail + Verifikation in Modul-Specs):**

| Skript(e) | Ziel | Modul-Spec |
|---|---|---|
| `run-lint` + `lint-orphans/terminology/title-overlap/deps/programs` + `lint-rename` | `skills/wiki-lint/scripts/` | spec-lint |
| `tiling-check` (semantic tiling lint) | `skills/wiki-lint/scripts/` | spec-lint / spec-dragonscale |
| `boundary-score` (boundary-first autoresearch) | `skills/autoresearch/scripts/` | spec-dragonscale |
| `allocate-address` (DragonScale page addresses) | `skills/wiki-ingest/scripts/` *(Nutzung verifizieren)* | spec-dragonscale |
| `rewrite-wikilinks`, `wiki-prepass` | `skills/wiki-ingest/scripts/` | spec-ingest |
| `setup-vault/dragonscale/multi-agent` | `skills/wiki/scripts/` *oder* `bin/` behalten | spec-setup |
| `lib/vault_root.py` + geteilte DragonScale-Util | `lib/` | spec-lint / spec-dragonscale |
| `release.py`, `sync-versions.py` | bleibt `bin/` (out-of-scope) | — |

## Alternativen  ‹Womit›
- **Zentral konsolidieren** (bleibt `scripts/`, nur zu packages bündeln) — verworfen: bindet Skripte nicht an Skill, Discoverability bleibt flach.
- **Hybrid** (skill-eigene unter Skill, shared zentral) — deckungsgleich mit "shared → lib/" und daher in diese Entscheidung integriert, nicht separat.

## Konsequenzen  ‹Warum: Folgen›
**Gut:** Skripte beim Skill auffindbar; klare Ownership; folgt `doc-pipeline`-Präzedenz.
**Schlecht / Kosten:** `dragonscale`-Cluster splittet über 3 Skills; geteilte DragonScale-Util muss nach `lib/`; `importlib`-Ladepfade in `run-lint.py` + `tests/` + alle Pfad-Referenzen müssen mitziehen; `bin/setup`-Ownership uneindeutig (→ `wiki`-Skill oder `bin/` — spec-setup entscheidet).
**Folge-Arbeiten:** Mapping-Detail je Modul-Spec; `lib/`-Modul für shared; `run-lint` importlib + Tests aktualisieren; Ref-Update (README/AGENTS/GEMINI/Makefile/docs/SKILL.md).

---
### Checkliste
- [x] Kontext nennt die echten Kräfte  ‹Warum›
- [x] Entscheidung in 1 Satz klar  ‹Was›
- [x] ≥1 ernsthafte Alternative + Grund der Ablehnung  ‹Womit›
- [x] Konsequenzen gut UND schlecht
- [x] Status gesetzt (immutable — Änderung = neue ADR)
