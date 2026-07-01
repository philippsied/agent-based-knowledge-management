---
artifact: adr
number: 0003
status: accepted
manifest: docs/manifests/cmd-script-consolidation.json
---

# ADR-0003 — setup-Cluster bleibt in `bin/` (Ausnahme zu ADR-0002)

> **Anker (7 W):** Warum (Kontext + Konsequenzen) · Was (die Entscheidung) · Womit (Alternativen)
> Präzedenz-Verweis: [ADR-0002](0002-colocate-scripts-under-skill.md), [spec-setup](../specs/SPEC-cmd-script-consolidation-setup.md)

## Status
accepted (2026-07-01)

## Kontext  ‹Warum›
[ADR-0002](0002-colocate-scripts-under-skill.md) legt als Default fest: Skripte ziehen unter den
besitzenden Skill. spec-setup hat per Evidenz gezeigt, dass die Installer-Familie
(`bin/setup-vault.py` · `setup-dragonscale.py` · `setup-multi-agent.py`) **Bootstrap-/Install-Tooling**
ist, das VOR jeder Skill-Nutzung läuft (Aufrufer: `Makefile`-Targets, `docs/install-guide.md`, `README.md`)
— nicht zur Skill-Laufzeit. Sie unter `skills/wiki/scripts/` zu ziehen würde Install-Aufrufer
verkomplizieren und suggerieren, sie seien Skill-Runtime.

## Entscheidung  ‹Was›
Der setup-Cluster bleibt in `bin/`; gemeinsame Resolver-Logik nutzt das bestehende `lib/vault_root.py`,
optionales `bin/_setup_common.py` nur wenn die gemeinsame Schnittmenge nicht-trivial ist.

## Alternativen  ‹Womit›
- **Co-locate unter `skills/wiki/scripts/`** (ADR-0002-Default) — verworfen: install-time, nicht runtime; würde `Makefile`/`install-guide`-Aufrufe verkomplizieren ohne Ownership-Gewinn.

## Konsequenzen  ‹Warum: Folgen›
**Gut:** Install-Tooling bleibt am konventionellen Ort; keine Aufrufer-Pfad-Änderung nötig; klare Trennung install-time vs. skill-runtime.
**Schlecht / Kosten:** ADR-0002 gilt nicht uniform — dies ist die dokumentierte Ausnahme.
**Folge-Arbeiten:** spec-setup referenziert diese ADR; `release.py`/`sync-versions.py` bleiben konsistent ebenfalls in `bin/` (bereits out-of-scope laut PRD).

---
### Checkliste
- [x] Kontext nennt die echten Kräfte  ‹Warum›
- [x] Entscheidung in 1 Satz klar  ‹Was›
- [x] ≥1 ernsthafte Alternative + Grund der Ablehnung  ‹Womit›
- [x] Konsequenzen gut UND schlecht
- [x] Status gesetzt (immutable — Änderung = neue ADR)
