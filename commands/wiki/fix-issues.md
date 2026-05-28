---
description: Pop the next ready, highest-priority issue from wiki/meta/OPEN-ISSUES.md stack (priority ASC, ready-first, LIFO tiebreaker), verify it, then either remove it (already done) or fix it and remove. Exactly one issue per invocation.
allowed-tools: Read, Edit, Bash, Grep, Glob
---

# /wiki:fix-issues — Top-of-Stack-Issue verifizieren und abarbeiten

Ziel: **Genau ein** Issue aus `wiki/meta/OPEN-ISSUES.md` pro Aufruf bearbeiten. Reihenfolge: Priority ASC (P0 zuerst), bei Gleichstand "ready vor blocked", dann LIFO (jüngster `pushed` zuerst). Verifizieren statt blind fixen.

Sprache: Deutsch für Chat und Issue-Bodies; Englisch nur für Code-Identifier/Commit-Conventions, wo das im Repo etabliert ist.

## Datenmodell (Hybrid: YAML-Stack + Body-Sektionen)

`wiki/meta/OPEN-ISSUES.md` trägt im Frontmatter ein `stack:`-Array — die geordnete Arbeitsliste. Jedes Item:

```yaml
- id: I-2026-NNN               # year-resetting counter
  priority: P0|P1|P2|P3
  section: <whitelist>          # enforcement|lint|vault-content|tooling|templates|skill-plugin|eval-observability
  title: "…"                    # identisch zum H3-Body-Header
  pushed: YYYY-MM-DD
  blocked_by: [I-2026-MMM, …]   # leer = ready
  inconclusive_since: YYYY-MM-DD # optional, paarweise mit reason
  inconclusive_reason: "…"       # optional
  aggregated_from: [I-…, …]      # optional, read-only (von Schritt 7 gesetzt)
```

Im Body steht pro Item eine `### I-2026-NNN — Titel` Sektion unter ihrem `## <section>`-Block, mit einer Meta-Zeile `**Priority:** … · **Pushed:** … · **WO:** …`. **Die Wahrheit liegt im Frontmatter**; Body-Zeilen (`**Blocked by:**`, `**Note:**`) sind Spiegelungen.

## Hard rules (nicht verhandelbar)

- **GENAU EIN Issue pro Aufruf.** Mehr nicht. Wenn der User mehr will, ruft er das Command erneut auf.
- **Niemals OPEN-ISSUES.md editieren ohne saubere Git-Baseline.** Vorher Status prüfen, nachher committen.
- **Niemals stillschweigend aggregieren.** Der Aggregations-Pfad (siehe Schritt 3) erfordert explizite User-Zustimmung.
- **Niemals ein Issue löschen, das nicht verifiziert werden konnte.** Bei Inkonklusivität bleibt das Item im Stack (Schritt 4d setzt `inconclusive_since`/`inconclusive_reason` und schiebt es ans Ende seiner Priority-Gruppe).
- **Niemals Stack und Body auseinanderlaufen lassen.** Nach jedem Edit muss die Menge der `stack[].id` exakt der Menge der `### I-…`-Body-Header entsprechen. Drift = Abbruch.

## Pre-conditions (Guardrails — hart)

1. `git status --porcelain wiki/meta/OPEN-ISSUES.md` ausführen.
   - **Wenn dirty**: ABBRECHEN. User muss erst committen oder stashen. Keine weiteren Edits.
   - **Wenn clean**: weiter.
2. `git log -1 --oneline -- wiki/meta/OPEN-ISSUES.md` ausführen — Commit-Hash des aktuellen Stands merken (kommt in den Final-Report).

## Schritt 1 — Datei vollständig lesen

`Read wiki/meta/OPEN-ISSUES.md` komplett. Frontmatter `stack:` parsen + Body-Sektionen inventarisieren. `stack[].id`-Set gegen `### I-…`-Header-Set abgleichen — bei Drift sofort ABBRECHEN (Lint-Hint: `scripts/lint/lint-open-issues.py`).

## Schritt 2 — Top-of-Stack identifizieren

Das Top-Issue ist **das erste Stack-Item, dessen `blocked_by` leer ist**. Das Array ist bereits Priority-ASC / ready-first / pushed-DESC sortiert; der erste ready-Eintrag ist damit das höchstpriore bearbeitbare Issue. Body-Detail = die `### I-2026-NNN`-Sektion mit passender ID.

Edge:
- **`stack` ist leer** → "Keine offenen Issues. Nichts zu tun." Abbrechen, kein Commit.
- **Alle Items haben nicht-leeres `blocked_by`** → "Stack hat nur blockierte Items: [<id-liste>]. Bitte Blocker zuerst auflösen." Abbrechen, kein Commit.

Die ID, den Titel und den WO-Anker wörtlich notieren — werden in Schritt 4–6 und im Final-Report referenziert.

## Schritt 3 — Aggregations-Scan (MANDATORY, einmalig)

Bevor irgendetwas geändert wird: Alle Issues nochmal mental durchgehen. Frage: Würde **ein** größerer Fix (Plugin-Update, Skript-Rewrite, fundamentale Überarbeitung) das Top-Issue **plus mindestens zwei weitere** Issues deterministisch erledigen?

- **NEIN** → weiter zu Schritt 4.
- **JA** → STOP. Dem User folgende Wahl präsentieren und auf Antwort warten:

  ```
  Aggregations-Vorschlag: Issues [<id-liste>] könnten gebündelt durch einen größeren Fix
  ([Plugin-Update X / Skript-Rewrite Y / Refactor Z]) gemeinsam erledigt werden.

  Optionen:
    (1) Nur Top-Issue fixen ("<top-titel>").
    (2) Aggregieren: Die N Issues werden zu einem neuen Top-Issue
        "<Aggregations-Titel>" zusammengefasst. Die anderen Items werden
        entfernt. Der eigentliche Fix wird NICHT in diesem Aufruf gemacht —
        das aggregierte Issue wird committet und in einem späteren
        /wiki:fix-issues-Aufruf bearbeitet.

  Antwort (1) oder (2) bitte.
  ```

  - Antwort **(1)** → weiter zu Schritt 4 mit dem ursprünglichen Top-Issue.
  - Antwort **(2)** → springe zu Schritt 7 (Aggregations-Pfad).
  - Keine Antwort / Abbruch → das Command beendet sich ohne Änderung.

  Niemals selbst eine Default-Wahl treffen. Niemals (2) ohne explizite User-Zustimmung.

## Schritt 4 — Top-Issue verifizieren

Das Top-Issue gegen den aktuellen Repo-Stand prüfen:

- **Wenn `WO:`-Anker eine Datei nennt**: `ls`/`Read` → existiert die Datei? Ist das Symptom noch reproduzierbar?
- **Wenn `WO:`-Anker eine Zeile nennt**: `Read <file> +/- 5 Zeilen` → ist der Inhalt noch dort?
- **Wenn das Issue fehlendes Tooling beschreibt**: `ls`/`Glob` → ist es wirklich noch nicht da?
- **Wenn das Issue ein Skript/Hook-Verhalten beschreibt**: das Skript laufen lassen (read-only) und Output gegen die Behauptung prüfen.

Vier mögliche Ergebnisse:

### 4a — Already resolved (Symptom ist weg)

→ Stack-Item (Frontmatter) **und** `### I-…`-Body-Sektion entfernen — beide.
→ Eintrag in `wiki/log.md` **oben** anfügen (neue Einträge top):
  ```
  ## [YYYY-MM-DD] verify | resolved: <id> <issue-titel>
  - Operation: `/wiki:fix-issues` Top-of-Stack-Verifikation.
  - Status: resolved — <kurze Begründung mit Evidenz (Output, Commit-Ref)>.
  - Why: <ein Satz zur Wurzel — was hat es eigentlich gefixt>.
  ```
→ Frontmatter `updated:` auf heute. Stack/Body-Sync prüfen.
→ Weiter zu Schritt 5.

### 4b — Stale aber teilweise wahr (z.B. Zeilennummer driftet, Count drifted)

→ Item **nicht** entfernen.
→ Den ungenauen Teil in der Body-Sektion in-place patchen (Zeilennummer korrigieren, Count aktualisieren). `pushed` nicht ändern.
→ Frontmatter `updated:` auf heute.
→ Kein log.md-Eintrag nötig (Issue bleibt offen).
→ Weiter zu Schritt 5.

### 4c — Still real (Issue ist gültig und nicht erledigt)

→ Den Fix durchführen. Konventionelle Tools (Edit, Write) für Code-Änderungen.
→ Nach erfolgreichem Fix:
  - Stack-Item + `### I-…`-Body-Sektion entfernen — beide.
  - Eintrag in `wiki/log.md` oben anfügen:
    ```
    ## [YYYY-MM-DD] fix | <id> <issue-titel>
    - Operation: `/wiki:fix-issues` Top-of-Stack-Fix.
    - Change: <kurz, was geändert wurde — Datei + Kern-Edit>.
    - Why: <ein Satz, der die Ursprungs-Begründung des Issues spiegelt>.
    ```
→ Frontmatter `updated:` auf heute (beide Files). Stack/Body-Sync prüfen.
→ Weiter zu Schritt 5.

### 4d — Inconclusive (Verifikation ohne klares Ergebnis, z.B. Sandbox/fehlendes Tool)

→ Item **nicht** entfernen.
→ Im Stack-Item `inconclusive_since: <heute>` + `inconclusive_reason: "<grund>"` setzen.
→ In der Body-Sektion eine Zeile `**Note:** inconclusive since <heute> — <grund>` ergänzen (Spiegelung).
→ Das Item innerhalb seiner Priority-Gruppe ans **Ende** sortieren, damit der nächste Aufruf nicht erneut daran hängenbleibt.
→ Frontmatter `updated:` auf heute. Stack/Body-Sync prüfen.
→ Weiter zu Schritt 5.

## Schritt 5 — Commit-Disziplin

- **Pfad 4a (resolved, kein Code-Fix nötig)**: ein Commit, Format:
  ```
  chore(meta): resolve "<id> <issue-titel>"

  Verified <kurze Evidenz>. Removed from OPEN-ISSUES.md stack + body, logged in wiki/log.md.
  ```
- **Pfad 4b (stale patch)**: ein Commit, Format:
  ```
  chore(meta): patch stale ref in "<id> <issue-titel>"

  <was korrigiert wurde — Zeile/Count>.
  ```
- **Pfad 4c (real fix)**: bis zu **zwei** Commits:
  1. Der Code-Fix: `fix(<scope>): <was>` oder `feat(<scope>): <was>`.
  2. Die Meta-Aktualisierung: `chore(meta): resolve "<id> <issue-titel>"`.
- **Pfad 4d (inconclusive)**: ein Commit, Format:
  ```
  chore(meta): mark "<id> <issue-titel>" inconclusive (since <YYYY-MM-DD>)

  <grund — warum Verifikation nicht abschließbar war>.
  ```

Niemals --no-verify. Niemals --amend (wir bauen frische Commits, damit die History sauber ist).

## Schritt 6 — Final-Report (3 Zeilen)

```
Top-Issue: <id> <titel>.
Outcome: <resolved | patched-stale | fixed | inconclusive | aggregated>.
New top of stack: <id + titel des nächsten ready-Items>.
```

Bei Bedarf eine vierte Zeile mit dem Commit-Hash der finalen Änderung.

## Schritt 7 — Aggregations-Pfad (nur wenn User Antwort (2) gewählt hat)

1. Alle N betroffenen Stack-Items + ihre N `### I-…`-Body-Sektionen entfernen (über die jeweiligen Sektionen hinweg).
2. **Ein neues Stack-Item** mit nächster freier ID anlegen, das den Bündel-Fix beschreibt, plus eine neue `### I-…`-Body-Sektion in der passenden `## <section>`. Frontmatter-Feld `aggregated_from: [<id-1>, …, <id-N>]` enthält die N entfernten IDs. Schema:

   ```yaml
   - id: I-2026-NNN
     priority: <höchste der N>
     section: <haupt-section>
     title: "<Aggregations-Titel>"
     pushed: <heute>
     blocked_by: []
     aggregated_from: [<id-1>, …, <id-N>]
   ```

3. Frontmatter `updated:` auf heute. Stack/Body-Sync prüfen.
4. **Kein Fix durchführen** — der Sinn des Aggregations-Pfads ist Konsolidierung, nicht sofortige Lösung.
5. Ein Commit, Format:
   ```
   chore(meta): aggregate <N> issues into "<id> <aggregations-titel>"

   Ersetzt: <kommagetrennte id-Liste>. Begründung: <ein Satz, warum der gebündelte Fix sinnvoller ist als N einzelne>.
   ```
6. Final-Report wie in Schritt 6, Outcome = `aggregated`.

## Edge Cases

- **OPEN-ISSUES.md `stack` ist leer**: "Keine offenen Issues. Nichts zu tun." Abbrechen, kein Commit.
- **Alle Items blockiert**: "Stack hat nur blockierte Items: [<id-liste>]. Bitte Blocker zuerst auflösen." Abbrechen, kein Commit.
- **`blocked_by` zeigt auf nicht-existente ID**: harter Abbruch, Hinweis auf `scripts/lint/lint-open-issues.py`. Kein Edit.
- **Stack/Body out of sync** (id-Set ≠ Header-Set): harter Abbruch, kein Edit, Lint-Hint.
- **Verifikation schlägt aus technischen Gründen fehl** (Sandbox, fehlendes Tool): das ist Pfad 4d (inconclusive), nicht Abbruch.
- **Fix verändert mehr Files als gedacht**: dem User vor dem Commit den Diff zeigen und Bestätigung einholen.
