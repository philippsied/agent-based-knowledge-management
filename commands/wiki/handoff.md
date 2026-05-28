---
description: Synthesize session todos and insights into wiki/meta/OPEN-ISSUES.md as new stack entries with fresh IDs (priority-ordered, ready-first, LIFO tiebreaker).
argument-hint: [optional: session topic / one-liner context]
allowed-tools: Read, Edit, Bash
---

# /wiki:handoff — Session-Erkenntnisse in OPEN-ISSUES.md überführen

Ziel: Am Ende einer Session (oder wann immer neue Erkenntnisse anfallen) offene Todos, Bugs und nicht-triviale Beobachtungen als **synthetisierte** Issues in `wiki/meta/OPEN-ISSUES.md` ablegen, sodass künftige Sessions sie via `/wiki:fix-issues` priorisiert abarbeiten können.

Sprache der Issues: **Deutsch**. Sprache der Commit-Messages: Deutsch oder Englisch je nach Konvention im Repo.

## Datenmodell (Hybrid: YAML-Stack + Body-Sektionen)

`wiki/meta/OPEN-ISSUES.md` trägt im Frontmatter ein `stack:`-Array (die geordnete Arbeitsliste) und im Body pro Item eine `### I-2026-NNN — Titel` Sektion unter ihrem `## <section>`-Block. Felder pro Stack-Item:

```yaml
- id: I-2026-NNN
  priority: P0|P1|P2|P3
  section: <whitelist>
  title: "…"
  pushed: YYYY-MM-DD
  blocked_by: [I-…]    # leer = ready
```

Section-Whitelist (genau diese 7):
`enforcement` · `lint` · `vault-content` · `tooling` · `templates` · `skill-plugin` · `eval-observability`

Bedeutung:
- `enforcement` — Hooks, Self-Mod-Guard, path-safety, pre-commit/CI.
- `lint` — Lint-Scripts, run-lint-Integration, Schema-Checks.
- `vault-content` — stale pages, dead links, Duplikate, misplaced files, Bilingual-DNT.
- `tooling` — Helper-Scripts, Tests, Convention-vs-Practice, manifest-sync.
- `templates` — Platzhalter-Wikilinks, Template-Konventionen.
- `skill-plugin` — Skill-Definitions, Plugin-Branch, Trigger-Phrasen, Sub-Agent-Reports, Memory-Persistenz.
- `eval-observability` — Trace-Logging, Pinned-Regression, Eval-Gated-CI, CoT-Judging, Spec-Kit-Constitution.

Nur dann ein Issue außerhalb dieser Whitelist einsortieren, wenn es ehrlich in keine passt — dann zuerst dem User eine neue Section vorschlagen.

## Pre-conditions (Guardrails — hart)

1. `git status --porcelain wiki/meta/OPEN-ISSUES.md` ausführen.
   - **Wenn Output nicht leer** (= uncommitted changes): ABBRECHEN. Dem User mitteilen: "OPEN-ISSUES.md hat uncommitted changes. Bitte erst committen oder stashen, damit die Handoff-Synthese gegen eine saubere Baseline läuft." Keine weiteren Edits.
   - **Wenn Output leer**: weiter.
2. `git log -1 --oneline -- wiki/meta/OPEN-ISSUES.md` ausführen — den Commit-Hash dem User im Final-Report zeigen.

## Schritt 1 — Existierende Struktur lesen + ID-Counter ermitteln

`Read wiki/meta/OPEN-ISSUES.md` einmal komplett. Frontmatter `stack:` + Body-Sektionen erfassen.

ID-Counter für das laufende Jahr (Format `I-YYYY-NNN`, zero-padded 3-stellig):

1. Alle `stack[].id` sammeln + alle `aggregated_from`-IDs (auch bereits entfernte zählen mit).
2. `wiki/log.md` nach Resolve-Einträgen des laufenden Jahres scannen (regex `I-2026-(\d{3})`).
3. `next_id = max(beobachtete NNN) + 1`. Wenn das Jahr noch keine IDs hat → `I-2026-001`.

**Keine ID-Recycling** — gelöschte oder aggregierte Nummern werden nicht neu vergeben.

## Schritt 2 — Synthese (nicht copy-paste)

Aus dem Session-Kontext (User-Nachrichten, Tool-Outputs, eigene Beobachtungen) Issues extrahieren, die folgende Kriterien erfüllen:

- **Konkret, nicht vag.** "X-Funktion verliert Y in `<file>:L42`" akzeptiert. "Refactor sollte irgendwo passieren" abgelehnt.
- **Hat einen `WO:`-Anker.** Datei, Pfad, Zeile oder klarer Bereich. Ohne Anker gehört es in `wiki/questions/` oder `wiki/decisions/`, nicht hierher.
- **Ist nicht reine Session-State.** "Wir waren beim Debuggen von X als der Context ausging" gehört in working notes, nicht hier.
- **Konvergente Issues aggregieren.** Wenn 3+ neue Issues dieselbe Wurzel haben → ein gebündeltes Issue statt drei near-Duplikate.

Pro Issue:

- Ein **Stack-Item** im Frontmatter (Felder oben). `priority` default P2 (User kann beim Aufruf override geben — z.B. "handoff P1"). `blocked_by` default `[]`; wenn das Issue klar auf ein bestehendes wartet (Prosa "kann erst nach X"), die betreffende ID eintragen. `pushed` = heute.
- Eine **Body-Sektion** unter der passenden `## <section>`:
  ```
  ### I-2026-NNN — <Kurzer Titel — WAS>
  **Priority:** Pn · **Pushed:** YYYY-MM-DD · **WO:** `<path[:line]>`

  <Ein Satz Symptom oder Risiko, WARUM>.
  ```
  Optionale Zeile `**Blocked by:** [[#I-2026-MMM]]`, falls `blocked_by` gesetzt.

## Schritt 3 — Einfügen (priority-sortiert)

Neue Stack-Items so in das `stack:`-Array einsortieren, dass das Array invariant sortiert bleibt: **Priority ASC** (P0 zuerst), bei Gleichstand **ready vor blocked**, dann **`pushed` DESC** (jüngster zuerst). Nicht naiv prepend — an die korrekte Position einfügen.

Body-Sektionen ans **Ende** der jeweiligen `## <section>`-Block-Sektion anhängen (Body-Reihenfolge ist nur kosmetisch; die Arbeitsreihenfolge lebt im Stack).

## Schritt 4 — Verifikation des Edits

Vor dem Commit: `git diff wiki/meta/OPEN-ISSUES.md` anzeigen. Sicherstellen, dass:

- Frontmatter `updated:` auf das heutige Datum aktualisiert ist (YYYY-MM-DD).
- Keine bestehenden Items verändert wurden.
- `stack[].id`-Set == `### I-…`-Body-Header-Set (kein Drift).
- Jede neue `id` unique + Format `I-YYYY-NNN`.
- Jede `section` ∈ Whitelist.
- Jede `blocked_by`-ID existiert im Stack.
- Stack-Sortierung stimmt (Priority ASC, ready-first, pushed DESC).

Optional: `python3 scripts/lint/lint-open-issues.py` laufen lassen, falls vorhanden.

## Schritt 5 — Commit

Genau ein Commit, Format:

```
docs(meta): handoff <N> open issues from <session topic>

<optional: 1–2 Zeilen Kontext, welche Section(s) gewachsen sind>
```

Wenn der User beim Aufruf ein Topic-Argument übergeben hat, dieses in den Subject einsetzen. Sonst aus dem Session-Kontext eine knappe Beschreibung ableiten.

## Schritt 6 — Final-Report (3 Zeilen)

```
Filed: <N> neue Issues (IDs <I-…, I-…>) in Sections: <X, Y, Z>.
Top of stack: <id + Titel des nun obersten ready-Items>.
Commit: <kurzer-hash> <subject>.
```

## Was dieses Command NICHT macht

- **Bestehende Issues nicht editieren oder verschieben.** Stale Line-Numbers korrigieren ist Job von `/wiki:fix-issues`, nicht `/wiki:handoff`.
- **Keine Issues ohne `WO:`-Anker.** Non-actionable Beobachtungen werden zurückgewiesen.
- **Keine `aggregated_from`-Felder setzen** — das ist `/wiki:fix-issues` Schritt 7 (Aggregations-Pfad).
- **Keine ID-Recycling.** Der Counter zählt vorwärts.
- **Keine Massen-Reorganisation.** Wenn der User die Section-Struktur ändern will, erfolgt das in einem separaten manuellen Commit.
