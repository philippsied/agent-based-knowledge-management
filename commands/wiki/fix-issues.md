---
description: Pop the top issue from wiki/meta/OPEN-ISSUES.md (LIFO), verify it, then either remove it (already done) or fix it and remove. Exactly one issue per invocation.
allowed-tools: Read, Edit, Bash, Grep, Glob
---

# /wiki:fix-issues — Top-of-Stack-Issue verifizieren und abarbeiten

Ziel: **Genau ein** Issue aus `wiki/meta/OPEN-ISSUES.md` pro Aufruf bearbeiten. Stack-Disziplin: LIFO. Verifizieren statt blind fixen.

Sprache: Deutsch für Chat und Issue-Bodies; Englisch nur für Code-Identifier/Commit-Conventions, wo das im Repo etabliert ist.

## Hard rules (nicht verhandelbar)

- **GENAU EIN Issue pro Aufruf.** Mehr nicht. Wenn der User mehr will, ruft er das Command erneut auf.
- **Niemals OPEN-ISSUES.md editieren ohne saubere Git-Baseline.** Vorher Status prüfen, nachher committen.
- **Niemals stillschweigend aggregieren.** Der Aggregations-Pfad (siehe Schritt 3) erfordert explizite User-Zustimmung.
- **Niemals ein Issue löschen, das nicht verifiziert werden konnte.** Bei Inkonklusivität bleibt der Bullet stehen, mit inline-Note `(verified inconclusive YYYY-MM-DD)`.

## Pre-conditions (Guardrails — hart)

1. `git status --porcelain wiki/meta/OPEN-ISSUES.md` ausführen.
   - **Wenn dirty**: ABBRECHEN. User muss erst committen oder stashen. Keine weiteren Edits.
   - **Wenn clean**: weiter.
2. `git log -1 --oneline -- wiki/meta/OPEN-ISSUES.md` ausführen — Commit-Hash des aktuellen Stands merken (kommt in den Final-Report).

## Schritt 1 — Datei vollständig lesen

`Read wiki/meta/OPEN-ISSUES.md` komplett. Inventory aller Issues über alle Kategorien aufbauen.

## Schritt 2 — Top-of-Stack identifizieren

Das Top-Issue ist **der erste Bullet im ersten nicht-leeren Sektions-Block** unter `# Open Issues`. Genau dieser eine Bullet ist das Arbeitsziel.

Den Bullet-Text (inkl. WO-Anker) wörtlich notieren — er wird in Schritt 4–6 und im Final-Report referenziert.

## Schritt 3 — Aggregations-Scan (MANDATORY, einmalig)

Bevor irgendetwas geändert wird: Alle Issues nochmal mental durchgehen. Frage: Würde **ein** größerer Fix (Plugin-Update, Skript-Rewrite, fundamentale Überarbeitung) das Top-Issue **plus mindestens zwei weitere** Issues deterministisch erledigen?

- **NEIN** → weiter zu Schritt 4.
- **JA** → STOP. Dem User folgende Wahl präsentieren und auf Antwort warten:

  ```
  Aggregations-Vorschlag: Issues [<liste>] könnten gebündelt durch einen größeren Fix
  ([Plugin-Update X / Skript-Rewrite Y / Refactor Z]) gemeinsam erledigt werden.

  Optionen:
    (1) Nur Top-Issue fixen ("<top-titel>").
    (2) Aggregieren: Die N Issues werden zu einem neuen Top-Issue
        "<Aggregations-Titel>" zusammengefasst. Die anderen Bullets werden
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

Drei mögliche Ergebnisse:

### 4a — Already resolved (Symptom ist weg)

→ Bullet aus OPEN-ISSUES.md entfernen.
→ Eintrag in `wiki/log.md` **oben** anfügen (neue Einträge top):
  ```
  ## [YYYY-MM-DD] verify | resolved: <issue-titel>
  - Operation: `/wiki:fix-issues` Top-of-Stack-Verifikation.
  - Status: resolved — <kurze Begründung mit Evidenz (Output, Commit-Ref)>.
  - Why: <ein Satz zur Wurzel — was hat es eigentlich gefixt>.
  ```
→ Weiter zu Schritt 5.

### 4b — Stale aber teilweise wahr (z.B. Zeilennummer driftet, Count drifted)

→ Bullet **nicht** entfernen.
→ Den ungenauen Teil im Bullet in-place patchen (Zeilennummer korrigieren, Count aktualisieren, Datum verschieben).
→ Frontmatter `updated:` auf heute.
→ Kein log.md-Eintrag nötig (Issue bleibt offen).
→ Weiter zu Schritt 5.

### 4c — Still real (Issue ist gültig und nicht erledigt)

→ Den Fix durchführen. Konventionelle Tools (Edit, Write) für Code-Änderungen.
→ Nach erfolgreichem Fix:
  - Bullet aus OPEN-ISSUES.md entfernen.
  - Eintrag in `wiki/log.md` oben anfügen:
    ```
    ## [YYYY-MM-DD] fix | <issue-titel>
    - Operation: `/wiki:fix-issues` Top-of-Stack-Fix.
    - Change: <kurz, was geändert wurde — Datei + Kern-Edit>.
    - Why: <ein Satz, der die Ursprungs-Begründung des Issues spiegelt>.
    ```
→ Frontmatter `updated:` auf heute (beide Files).
→ Weiter zu Schritt 5.

## Schritt 5 — Commit-Disziplin

- **Pfad 4a (resolved, kein Code-Fix nötig)**: ein Commit, Format:
  ```
  chore(meta): resolve "<issue-titel>"

  Verified <kurze Evidenz>. Removed from OPEN-ISSUES.md, logged in wiki/log.md.
  ```
- **Pfad 4b (stale patch)**: ein Commit, Format:
  ```
  chore(meta): patch stale ref in "<issue-titel>"

  <was korrigiert wurde — Zeile/Count/Datum>.
  ```
- **Pfad 4c (real fix)**: bis zu **zwei** Commits:
  1. Der Code-Fix: `fix(<scope>): <was>` oder `feat(<scope>): <was>`.
  2. Die Meta-Aktualisierung: `chore(meta): resolve "<issue-titel>"`.

Niemals --no-verify. Niemals --amend (wir bauen frische Commits, damit die History sauber ist).

## Schritt 6 — Final-Report (3 Zeilen)

```
Top-Issue: <titel>.
Outcome: <resolved | patched-stale | fixed | aggregated>.
New top of stack: <titel des nächsten Bullets>.
```

Bei Bedarf eine vierte Zeile mit dem Commit-Hash der finalen Änderung.

## Schritt 7 — Aggregations-Pfad (nur wenn User Antwort (2) gewählt hat)

1. Alle N betroffenen Bullets aus OPEN-ISSUES.md entfernen (über die jeweiligen Kategorien hinweg).
2. **Einen neuen Bullet** ganz oben in der ersten Kategorie einfügen, der den Bündel-Fix als Top-Issue beschreibt. Schema:

   ```
   - **<Aggregations-Titel> [aggregated <YYYY-MM-DD>]** — <Beschreibung des einen größeren Fixes, der alle N Issues löst>. Ersetzt N=<n> Vorgänger-Issues: <kommagetrennte Liste der entfernten Titel>. WO: `<haupt-pfad>` + verwandte.
   ```

3. Frontmatter `updated:` auf heute.
4. **Kein Fix durchführen** — der Sinn des Aggregations-Pfads ist, mehrere Issues zu einem zu konsolidieren, ohne sie sofort zu lösen.
5. Ein Commit, Format:
   ```
   chore(meta): aggregate <N> issues into "<aggregations-titel>"

   Ersetzt: <kommagetrennte Liste>. Begründung: <ein Satz, warum der gebündelte Fix sinnvoller ist als N einzelne>.
   ```
6. Final-Report wie in Schritt 6, Outcome = `aggregated`.

## Edge Cases

- **OPEN-ISSUES.md ist leer (keine Bullets unter irgendeiner Sektion)**: Mit "Keine offenen Issues. Nichts zu tun." abbrechen, kein Commit.
- **Top-Issue ist mehrdeutig** (z.B. zwei Bullets im ersten Block — sollte nicht passieren, aber falls): den lexikalisch ersten nehmen.
- **Verifikation schlägt aus technischen Gründen fehl** (Sandbox, fehlendes Tool): inline-Note `(verified inconclusive YYYY-MM-DD: <grund>)` ergänzen, Bullet stehen lassen, kein Removal. Ein Commit mit `chore(meta): mark "<titel>" inconclusive`.
- **Fix verändert mehr Files als gedacht**: dem User vor dem Commit den Diff zeigen und Bestätigung einholen.
