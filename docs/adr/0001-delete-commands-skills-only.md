---
artifact: adr
number: 0001
status: accepted
manifest: docs/manifests/cmd-script-consolidation.json
---

# ADR-0001 — Commands löschen, Skills-only

> **Anker (7 W):** Warum (Kontext + Konsequenzen) · Was (die Entscheidung) · Womit (Alternativen)

## Status
accepted (2026-07-01)

## Kontext  ‹Warum›
Das Plugin hat zwei Invocation-Oberflächen: `commands/` (`/slash`, user-invoked) und `skills/`
(model-invoked). 5 der 7 commands sind dünne Router die einen gleichnamigen Skill duplizieren;
2 sind fett (`fix-issues` 211z, `handoff` 126z). Zwei Oberflächen → Logik-Drift + doppelte
Wartung. `plugin.json`/`marketplace.json` enumerieren commands **nicht** → Löschen erfordert
keine Manifest-Änderung.

## Entscheidung  ‹Was›
`commands/` wird vollständig entfernt; sämtliche command-Funktionalität wird ZUERST in Skills
migriert, danach die command-Dateien gelöscht — künftig Skills-only.

## Alternativen  ‹Womit›
- **Thin-wrapper** (behalte `/slash`, Logik im Skill) — verworfen: User will eine Oberfläche; `/slash`-UX nicht erforderlich.
- **Hybrid** (user-facing behalten, redundante löschen) — verworfen: inkonsistent, uneinheitliche Regel pro command.

## Konsequenzen  ‹Warum: Folgen›
**Gut:** eine Quelle des Verhaltens; kein Drift; weniger Wartungsoberfläche.
**Schlecht / Kosten:** `/slash`-UX entfällt (Nutzer triggern per natürlicher Sprache / Skill-Auto-Trigger); `handoff` braucht Skill-Heimat; jedes command-Verhalten muss VOR Löschung als in-Skill-vorhanden nachgewiesen werden.
**Folge-Arbeiten:** Coverage-Matrix in spec-commands; Skill-Heimat für `handoff` (Fold vs. neu); `fix-issues`→`wiki-lint` fix-forward; docs die `/commands` erwähnen aktualisieren.
**Breaking-Change (released Plugin):** Das Löschen der Commands ist ein Breaking-Change für das bereits veröffentlichte Plugin (`v1.10.1`); der user-facing Migrationsweg (CHANGELOG-Deprecation + `wiki-issues`-Äquivalent) gehört zu FUP-4 (Audit V-3).

---
### Checkliste
- [x] Kontext nennt die echten Kräfte  ‹Warum›
- [x] Entscheidung in 1 Satz klar  ‹Was›
- [x] ≥1 ernsthafte Alternative + Grund der Ablehnung  ‹Womit›
- [x] Konsequenzen gut UND schlecht
- [x] Status gesetzt (immutable — Änderung = neue ADR)
