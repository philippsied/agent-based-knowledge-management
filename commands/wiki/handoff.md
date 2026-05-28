---
description: Synthesize session todos and insights into wiki/meta/OPEN-ISSUES.md as new stack-top issues (LIFO).
argument-hint: [optional: session topic / one-liner context]
allowed-tools: Read, Edit, Bash
---

# /wiki:handoff — Session-Erkenntnisse in OPEN-ISSUES.md überführen

Ziel: Am Ende einer Session (oder wann immer neue Erkenntnisse anfallen) offene Todos, Bugs und nicht-triviale Beobachtungen als **synthetisierte** Issues in `wiki/meta/OPEN-ISSUES.md` ablegen, sodass künftige Sessions sie via `/wiki:fix-issues` stack-basiert abarbeiten können.

Sprache der Issues: **Deutsch** (Schema `**WAS** — WARUM. WO.`). Sprache der Commit-Messages: Deutsch oder Englisch je nach Konvention im Repo.

## Pre-conditions (Guardrails — hart)

1. `git status --porcelain wiki/meta/OPEN-ISSUES.md` ausführen.
   - **Wenn Output nicht leer** (= uncommitted changes): ABBRECHEN. Dem User mitteilen: "OPEN-ISSUES.md hat uncommitted changes. Bitte erst committen oder stashen, damit die Handoff-Synthese gegen eine saubere Baseline läuft." Keine weiteren Edits.
   - **Wenn Output leer**: weiter.
2. `git log -1 --oneline -- wiki/meta/OPEN-ISSUES.md` ausführen — bestätigt, dass der aktuelle Stand in der History sichtbar ist. Den Commit-Hash dem User im Final-Report zeigen, damit der Diff später nachvollziehbar bleibt.

## Schritt 1 — Existierende Struktur lesen

`Read wiki/meta/OPEN-ISSUES.md` einmal komplett. Mentale Liste der existierenden Kategorien aufbauen. Standardkategorien:

- `## Hook / enforcement layer`
- `## Lint`
- `## Vault-State`
- `## Tooling-Gaps`
- `## Plugin / Skill (upstream-Issues für ...)`
- `## Memory / cross-session`

Nur dann eine **neue** Kategorie anlegen, wenn das Issue ehrlich in keine existierende passt.

## Schritt 2 — Synthese (nicht copy-paste)

Aus dem Session-Kontext (User-Nachrichten, Tool-Outputs, eigene Beobachtungen) Issues extrahieren, die folgende Kriterien erfüllen:

- **Konkret, nicht vag.** "X-Funktion verliert Y in `<file>:L42`" akzeptiert. "Refactor sollte irgendwo passieren" abgelehnt.
- **Hat einen `WO:`-Anker.** Datei, Pfad, Zeile oder klarer Bereich. Ohne Anker gehört es in `wiki/questions/` oder `wiki/decisions/`, nicht hierher.
- **Ist nicht reine Session-State.** "Wir waren beim Debuggen von X als der Context ausging" gehört in working notes, nicht hier.
- **Konvergente Bullets aggregieren.** Wenn 3+ neue Bullets dieselbe Wurzel haben → ein gebündeltes Issue statt drei near-Duplikate.

Schema pro Bullet:

```
- **<Kurzer Titel — WAS>** — <Ein Satz Symptom oder Risiko, WARUM>. WO: `<path[:line]>` (oder klarer Bereich).
```

## Schritt 3 — Einfügen (LIFO/Stack-Top)

Neue Bullets **oben** in ihrer Kategorie einfügen. `/wiki:fix-issues` arbeitet die Datei top-down ab — was zuletzt rein kommt, wird zuerst geprüft.

Die Reihenfolge der Kategorien selbst bleibt unverändert. Wenn eine neue Kategorie nötig ist, vor `## Memory / cross-session` einsortieren (Memory bleibt das strukturell letzte Thema).

## Schritt 4 — Verifikation des Edits

Vor dem Commit: `git diff wiki/meta/OPEN-ISSUES.md` anzeigen. Sicherstellen, dass:

- Frontmatter `updated:` auf das heutige Datum aktualisiert ist (YYYY-MM-DD).
- Keine bestehenden Bullets versehentlich verändert wurden.
- Alle neuen Bullets dem `**WAS** — WARUM. WO.`-Schema folgen.

## Schritt 5 — Commit

Genau ein Commit, Format:

```
docs(meta): handoff <N> open issues from <session topic>

<optional: 1–2 Zeilen Kontext, welche Sektion(en) gewachsen sind>
```

Wenn der User beim Aufruf ein Topic-Argument übergeben hat, dieses in den Subject einsetzen. Sonst aus dem Session-Kontext eine knappe Beschreibung ableiten (z.B. "OPEN-ISSUES verification pass" oder "lint refactor session").

## Schritt 6 — Final-Report (3 Zeilen)

```
Filed: <N> neue Issues in Kategorien: <X, Y, Z>.
Top of stack: <Titel des nun obersten Bullets>.
Commit: <kurzer-hash> <subject>.
```

## Was dieses Command NICHT macht

- **Bestehende Issues nicht editieren oder verschieben.** Stale Line-Numbers korrigieren ist Job von `/wiki:fix-issues`, nicht `/wiki:handoff`.
- **Keine Issues ohne `WO:`-Anker.** Non-actionable Beobachtungen werden zurückgewiesen.
- **Keine Massen-Reorganisation.** Wenn der User die Kategorien-Struktur ändern will, erfolgt das in einem separaten manuellen Commit.
