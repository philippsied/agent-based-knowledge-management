---
artifact: plan
slug: cmd-script-consolidation
module: commands
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [spec, adr-0001, test-design]
branch: docs/cmd-script-consolidation-plan
---

# Plan — Command→Skill-Migration + Löschung `commands/`

> Beantwortet: WELCHE Schritte, in welcher Folge, WIE verifiziert?
> Wegwerf-Artefakt: nach Done erledigt.
> **Anker (7 W):** Wie (primär: Schritte) · Wann (Reihenfolge) · Womit (Deps/Tools) · Wann-erledigt (Done-Definition)
> **Verträge:** [Spec](../specs/SPEC-cmd-script-consolidation-commands.md) · [ADR-0001](../adr/0001-delete-commands-skills-only.md) · [Test-Design](../test-designs/cmd-script-consolidation.md)

## Ziel & Done-Definition  ‹Wann-erledigt›

**Ziel:** Reiner Refactor — alle 7 command-Dateien gehen verlustfrei in Skills auf, danach wird `commands/` vollständig gelöscht. Gleiche Trigger → gleiches Verhalten → gleiche Outputs. **Migration + Deckungsnachweis strikt VOR jeder Löschung.**

**Done, wenn alle Acceptance-Criteria (Spec §5) binär erfüllt sind:**
- [ ] Coverage-Matrix (Spec §2): alle 7 Zeilen aufgelöst (5× ✓ Router deckungsgleich, 2× migriert) — **vor** jeder Löschung nachgewiesen.
- [ ] `skills/wiki-issues/SKILL.md` existiert, enthält **beide** Operations (PUSH ex-`handoff`, POP ex-`fix-issues`) mit unverändertem Datenmodell, Guardrails, Schritten 1–7 (POP) / 1–6 (PUSH) und allen Commit-Formaten.
- [ ] Diff Command-Body ↔ `wiki-issues`-Operation inhaltlich leer (nur Framing „command"→„skill operation").
- [ ] `scripts/lint/lint-open-issues.py`-Referenzen im migrierten Skill **guarded / 1:1 übernommen** — kein Hard-Wire, keine Neuerstellung (siehe Schritt 3 + Klarstellung unten).
- [ ] `skills/wiki/SKILL.md` *Operations*-Tabelle enthält eine `wiki-issues`-Routing-Zeile.
- [ ] Doku-/Konfig-Referenzen auf `commands/` bzw. `/wiki:*`/`/slash` aktualisiert (Spec §4.3).
- [ ] `fd . commands/` == 0 (Verzeichnis restlos entfernt).
- [ ] Referenz-Grep sauber (Historie/Vorhaben-Docs ausgenommen); `pytest tests/` grün.

**KLARSTELLUNG (injizierte Fakten, gelten für den ganzen Plan):**
1. **`scripts/lint/lint-open-issues.py` ist eine vorbestehende Dangling-Referenz** — die Datei existiert in **diesem** Repo nicht (verifiziert: `fd lint-open-issues` = 0 Treffer, keine Skill-/Script-Referenz; lebt laut CHANGELOG im Vault-Repo). **OUT OF SCOPE** dieser Migration. Im migrierten `wiki-issues` die Referenzen **exakt so guarded übernehmen, wie die Commands sie tragen** („falls vorhanden" / if-present) — **nicht** anlegen, **nicht** hart verdrahten. Schritt 3 enthält einen dedizierten Verify-Check, dass der Guard die Migration überlebt.
2. **Das Plugin entdeckt `skills/` + `commands/` per Konvention** (Auto-Discovery). `.claude-plugin/marketplace.json` enumeriert weder commands noch skills → Löschen von `commands/` erfordert **keine** Manifest-Änderung (verifiziert, Spec §2/§4.4).

## Schritte  ‹Wie›

> Legende Verify: `⌘` = Shell-Kommando (aus Repo-Root ausführbar) · `👁` = beobachtbare Inspektion/Judge.
> Phasen: **A** Vorbedingungen → **B** Migration (neuer Skill) → **C** Coverage-Verifikation → **D** GATE → **E** Referenz-Update → **F** Löschung → **G** Regressionsnetz. Deletion (Phase F) ist erst nach GATE (Phase D) erlaubt.

### Phase A — Vorbedingungen

1. **Sauberen Ausgangszustand herstellen.** Auf Branch `docs/cmd-script-consolidation-plan`; Working-Tree für die zu ändernden Pfade sauber (bestehende, unabhängige Änderungen ggf. separat committen/stashen).
   → verify: `⌘` `git branch --show-current` == `docs/cmd-script-consolidation-plan` **und** `git status --porcelain skills/ commands/ README.md AGENTS.md CLAUDE.md references/ docs/upstream-roadmap.md` == leer.

2. **Baseline-Snapshot der 7 command-Bodies + Zielskills ziehen** (für den späteren Diff-Judge in Schritt 12). Zeilen-/Inhalts-Referenz festhalten: `commands/wiki/fix-issues.md` (211 z, POP), `commands/wiki/handoff.md` (126 z, PUSH), 5 Router.
   → verify: `⌘` `fd -e md . commands/ | wc -l` == 7 **und** `git rev-parse HEAD` notiert (Snapshot-Ankerpunkt).

### Phase B — Migration: neuer Skill `wiki-issues` (löst die 2 „gap"-Zeilen)

3. **`skills/wiki-issues/SKILL.md` neu anlegen.** YAML-Frontmatter nach Spec §2.3: `name: wiki-issues`, `allowed-tools: Read, Edit, Bash, Grep, Glob` (Union POP+PUSH), Description + Trigger-Phrasen inkl. „fix issues", „/wiki:fix-issues", „nächstes offenes Issue abarbeiten", „handoff", „/wiki:handoff", „Session-Erkenntnisse ablegen". Datenmodell-Sektion (Hybrid YAML-`stack:` + `### I-YYYY-NNN`-Body-Sektionen, 7er-Section-Whitelist `enforcement|lint|vault-content|tooling|templates|skill-plugin|eval-observability`, „Wahrheit im Frontmatter") **einmal** dokumentieren, von beiden Operations genutzt. **`scripts/lint/lint-open-issues.py`-Referenzen wortgetreu und guarded übernehmen** (POP: Lint-Hint bei Drift/Abbruch wie in `fix-issues` Z.47/208; PUSH: optionaler `python3 scripts/lint/lint-open-issues.py`-Aufruf „falls vorhanden" wie in `handoff` Z.98) — **nicht** anlegen, **nicht** hart verdrahten.
   → verify: `⌘` `test -f skills/wiki-issues/SKILL.md && echo OK` **und** `rg -c 'I-YYYY-NNN|blocked_by|inconclusive_since|aggregated_from' skills/wiki-issues/SKILL.md` ≥ 1 **und** `rg -n 'lint-open-issues' skills/wiki-issues/SKILL.md` trifft **und** im Kontext jeder Fundstelle steht „falls vorhanden"/if-present bzw. reiner Lint-Hint (kein `test -f`/Hard-Require, keine Datei-Erzeugung) — `👁` bestätigt Guard überlebt Migration.

4. **Operation PUSH (ex-`handoff`) wortgetreu einsetzen.** Aus `commands/wiki/handoff.md` (Z.1–126) übernehmen: Ziel, Guardrails (Pre-conditions 1–2: `git status --porcelain` clean sonst Abbruch; `git log -1 --oneline`), Schritte 1–6 (ID-Counter-Ermittlung inkl. „keine ID-Recycling"; Synthese-Kriterien; priority-sortiertes Einfügen; Edit-Verifikation; Commit; Final-Report), „Was dieses Command NICHT macht", Commit-Format `docs(meta): handoff <N> open issues from <session topic>`, Default-Priority P2 + Override („handoff P1"). Nur Framing „command → skill operation" ändern.
   → verify: `👁` Diff `handoff.md` ↔ PUSH-Sektion inhaltlich leer (nur Framing) **und** `⌘` `rg -c 'docs\(meta\): handoff' skills/wiki-issues/SKILL.md` == 1 **und** `rg -c 'keine ID-Recycling|ID-Recycling' skills/wiki-issues/SKILL.md` ≥ 1.

5. **Operation POP (ex-`fix-issues`) wortgetreu einsetzen.** Aus `commands/wiki/fix-issues.md` (Z.1–211) übernehmen: Hard rules (genau 1 Issue/Aufruf; nie ohne saubere Git-Baseline; nie stillschweigend aggregieren; nie unverifiziert löschen; nie Stack/Body-Drift), Pre-conditions, Schritte 1–7 inkl. der **vier Verifikations-Pfade 4a resolved / 4b stale-patch / 4c real-fix (≤2 Commits) / 4d inconclusive**, Aggregations-Pfad (Schritt 7, `aggregated_from`), Sortier-Invariante (priority ASC → ready-before-blocked → inconclusive-last → `pushed` DESC), **alle 4 Commit-Formate** je Pfad, „Niemals --no-verify / --amend", Edge Cases. Nur Framing ändern.
   → verify: `👁` Diff `fix-issues.md` ↔ POP-Sektion inhaltlich leer **und** `⌘` alle vier Pfad-Marker vorhanden: `rg -c '4a|4b|4c|4d' skills/wiki-issues/SKILL.md` ≥ 1 **und** `rg -c 'no-verify|--amend' skills/wiki-issues/SKILL.md` ≥ 1 **und** `rg -c 'chore\(meta\): (resolve|patch stale|mark|aggregate)' skills/wiki-issues/SKILL.md` == 4 (alle vier Commit-Formate present).

6. **`wiki`-Routing-Zeile ergänzen.** In `skills/wiki/SKILL.md` *Operations*-Tabelle (Z.102–110) **eine** Zeile analog zum Bestand hinzufügen: `| "fix issues", "handoff", "/wiki:fix-issues", "/wiki:handoff" | ISSUES | \`wiki-issues\` |`. Keine weitere Änderung an `wiki/SKILL.md`.
   → verify: `⌘` `rg -n 'wiki-issues' skills/wiki/SKILL.md` trifft in der Operations-Tabelle **und** `git diff --stat skills/wiki/SKILL.md` zeigt genau +1 inhaltliche Zeile (surgical).

### Phase C — Coverage-Verifikation der 5 Router (Deckung VOR Löschung, kein Edit nötig außer ggf. Trigger)

7. **Router-Deckung gegen die 5 Zielskills prüfen** (Spec §2.1, je Router 1:1). Für `autoresearch|wiki|doc-pipeline|canvas|save`: bestätigen, dass der gleichnamige Skill das command-Verhalten vollständig trägt (Topic-Selection A–D; SCAFFOLD; 4-Stage/Batch/Fact-check/`--out-dir`; alle Canvas-Ops inkl. `from banana`; Save-Workflow/Note-Types/Dedup).
   → verify: `👁` Coverage-Matrix (Spec §2) je Router-Zeile als ✓ bestätigt (Judge/manuell) — **kein** Router trägt Logik, die der Skill nicht hat.

8. **Slash-Trigger-Deckung bestätigen** (Spec §3 Edge-Cases): die in den Router-Bodies genannten `/…`-Strings müssen als Trigger-Phrasen in der jeweiligen `SKILL.md` stehen.
   → verify: `⌘` je Skill grep, dass der Slash-String / natürlichsprachliche Äquivalent-Trigger vorhanden ist: `rg -l '/save' skills/save/SKILL.md`, `rg -l '/canvas' skills/canvas/SKILL.md`, `rg -l '/autoresearch' skills/autoresearch/SKILL.md`, `rg -l '/wiki' skills/wiki/SKILL.md`, `rg -l 'doc pipeline|convert to markdown' skills/doc-pipeline/SKILL.md` — jeweils Treffer. **Falls ein Trigger fehlt: hier ergänzen, VOR Löschung** (Spec §3 Fehlerbehandlung).

### Phase D — HUMAN-GATE (Deletion-Vorbedingung)

9. **GATE 1 — Freigabe „Coverage-Matrix vollständig, Skill angelegt".** Vor **jeder** Löschung: alle Ergebnisse aus Schritt 3–8 dem Menschen vorlegen. Erst nach expliziter Freigabe weiter zu Phase E/F.
   → verify: `👁` Human-Gate 1 (siehe Abschnitt Human-Gates) abgehakt; Deletion-Preconditions-Liste alle ✓.

### Phase E — Referenz-Update (Doku/Konfig; nach GATE, vor/mit Löschung)

10. **Echte Ist-Zustands-Referenzen aktualisieren** (Spec §4.3, verifiziert per `rg`):
    - `README.md`: Struktur-Baum-Zeile `├── commands/` (Z.350) + Unterzeilen `save.md`/`autoresearch.md`/`canvas.md` (Z.352–354) entfernen; Skill-Kommentare mit `/…` (Z.335–343, 379) und die `/slash`-Tabelle (Z.123–132) auf Skill-Namen/natürliche Trigger umstellen (kein command-Verzeichnis mehr).
    - `CLAUDE.md` (Vault): Plugin-Skills-Tabelle (Z.57–62) `/slash`-Spalte auf natürlichsprachliche Trigger/Skill-Namen umstellen; `wiki-issues` (fix-issues/handoff) aufnehmen.
    - `AGENTS.md`: Z.34/36 (`save`/`canvas` mit `/save`/`/canvas`) Trigger-Notation an Skill-Auto-Trigger angleichen.
    - `docs/upstream-roadmap.md`: Ist-Behauptungen `commands/wiki-handoff.md`/`commands/wiki-fix-issues.md` (Z.215) + `.claude/commands/wiki/…` (Z.367) auf Zielzustand `wiki-issues`/skills-only angleichen; Z.172/291–292 nur angleichen, falls sie den Ist-Zustand behaupten (Z.291–292 beschreiben Accept-Verhalten → Wortlaut prüfen, nicht Historie umschreiben).
    → verify: `⌘` `rg -n 'commands/' README.md AGENTS.md CLAUDE.md docs/upstream-roadmap.md` == 0.

11. **Sonderfall `references/operational-rules/project-locality.md:11` entscheiden** (Spec §4.3: „prüfen; falls generische CC-Doku (nicht plugin-spezifisch) → belassen, sonst angleichen"). Die Zeile beschreibt generisch, wo Slash-Commands in Claude-Code-Projekten liegen (`.claude/commands/`), **nicht** dieses Plugin. Konflikt mit Spec §5, die `references/` im Acceptance-Grep auf 0 fordert → **Entscheidung am GATE 2 einholen** (Abschnitt Human-Gates): (a) generisch belassen und Acceptance-Grep um diese eine generische Zeile ausnehmen (dokumentierte Ausnahme), **oder** (b) Zeile so umformulieren, dass sie nicht auf `commands/` matched.
    → verify: `👁` Entscheidung (a)/(b) am GATE 2 getroffen und angewandt; `⌘` bei (b): `rg -n 'commands/' references/` == 0; bei (a): Ausnahme in Acceptance-Notiz dokumentiert.

### Phase F — Löschung (letzter mutierender Schritt, erst nach GATE 1)

12. **Diff-Judge: migrierte Bodies inhaltlich deckungsgleich** — letzte Kontrolle vor Löschen der Quell-Bodies. `handoff.md` ↔ PUSH und `fix-issues.md` ↔ POP: nur Framing unterscheidet sich.
    → verify: `👁` Judge/manuell bestätigt „inhaltlich leerer Diff" für beide Paare (Spec §5 + Test-Design „Vergleich Command-Body ↔ Skill-Body").

13. **Die 2 fetten command-Dateien löschen** (jetzt migriert): `commands/wiki/fix-issues.md`, `commands/wiki/handoff.md`.
    → verify: `⌘` `test -e commands/wiki/fix-issues.md || test -e commands/wiki/handoff.md; echo $?` == 1 (beide weg).

14. **Die 5 Router-Dateien löschen** (Deckung ✓): `commands/autoresearch.md`, `commands/wiki.md`, `commands/doc-pipeline.md`, `commands/canvas.md`, `commands/save.md`.
    → verify: `⌘` `fd -e md . commands/ | wc -l` == 0.

15. **`commands/`-Verzeichnis restlos entfernen** (jetzt leer; Auto-Discovery braucht kein Manifest-Update).
    → verify: `⌘` `fd . commands/ 2>/dev/null | wc -l` == 0 **und** `test -d commands/; echo $?` == 1.

### Phase G — Regressionsnetz + Abschluss

16. **Referenz-Grep + Skill-Load-Smoke gesamt** (Test-Design Smoke-Ebene): keine toten `commands/`-Refs (Historie/Vorhaben-Docs ausgenommen); neuer Skill vorhanden; Routing-Zeile da.
    → verify: `⌘` `rg -n 'commands/' README.md AGENTS.md CLAUDE.md docs/upstream-roadmap.md` == 0 (references/ gemäß Schritt 11-Entscheidung) **und** `fd . skills/wiki-issues -t f | wc -l` ≥ 1 **und** `rg -l 'wiki-issues' skills/wiki/SKILL.md` trifft.

17. **`pytest tests/` grün** (Regressionsnetz; Tests referenzieren `commands/` nicht — verifiziert).
    → verify: `⌘` `uv run pytest tests/ -q` (oder `python3 -m pytest tests/ -q`) exit 0; Quality-Gate: 100 % pass (10 Test-Dateien) + Eval-Suites unberührt.

18. **Manifest-Status `commands`-Plan auf done/verified setzen** und Commit(s) in kohärenten Einheiten (conventional): (i) `feat(skills): add wiki-issues skill (migrate fix-issues POP + handoff PUSH)`, (ii) `docs: repoint command refs to skills`, (iii) `refactor: delete commands/ (skills-only, ADR-0001)`. Kein `--no-verify`, kein force-push.
    → verify: `⌘` `git log --oneline -3` zeigt die Commits; `git status --porcelain` sauber; Manifest-Eintrag `plan`(commands) status aktualisiert.

## Abhängigkeiten / Reihenfolge  ‹Wann / Womit›

**Harte Reihenfolge (nicht umsortierbar):**
`A (1–2)` → `B (3–6, neuer Skill + Routing)` → `C (7–8, Router-Deckung)` → **`D (9, GATE 1)`** → `E (10–11, Refs)` → `F (12–15, Löschung)` → `G (16–18, Regression + Commit)`.

- **Migration + Coverage-Verifikation (B, C) MÜSSEN vor jeder Löschung (F) abgeschlossen sein** — Kern-Constraint aus ADR-0001 + PRD-Must + Spec §3 Fehlerbehandlung („Löschung vor Migration → verboten").
- **GATE 1 (D) ist die Löschungs-Vorbedingung**: keine Datei aus `commands/` wird angefasst, bevor die Coverage-Matrix alle ✓ zeigt und `wiki-issues` steht.
- Schritt 6 (Routing-Zeile) hängt an Schritt 3 (Skill existiert). Schritt 12 (Diff-Judge) hängt an Schritt 4+5. Schritt 13 hängt an 12; 14 an 7+8+GATE; 15 an 13+14.
- **Parallelisierbar:** Schritt 4 (PUSH) und 5 (POP) unabhängig (verschiedene Sektionen derselben Datei — nur seriell schreiben). Schritt 7 (Router-Deckung) und 8 (Trigger) unabhängig voneinander. Referenz-Edits in Schritt 10 (README/CLAUDE/AGENTS/roadmap) sind datei-lokal parallelisierbar.

**Womit (Tools):** `git`, `fd`, `rg`, `uv`/`python3 -m pytest`. Keine neuen Dependencies. Kein Manifest-/Plugin-Edit nötig (Auto-Discovery).

## Risiken & Rollback

- **R1 — Löschung vor vollständiger Migration** (Verhaltensverlust). → Mitigation: GATE 1 (Schritt 9) blockt Phase F; Schritte 3–8 sind harte Vorbedingung. → Rollback: `git revert <delete-commit>` stellt `commands/` versioniert wieder her; `skills/wiki-issues/` ist additiv und separat entfernbar.
- **R2 — `wiki-issues` weicht inhaltlich vom command-Body ab** (fehlender Guardrail/Schritt/Commit-Format → reiner Refactor verletzt). → Mitigation: Diff-Judge Schritte 4/5/12 mit konkreten `rg`-Zählern (4 Commit-Formate, 4 Pfade, no-verify/amend, ID-Recycling). → Rollback: Skill-Datei ist additiv; korrigieren oder `git checkout -- skills/wiki-issues/SKILL.md` vor Delete.
- **R3 — `lint-open-issues.py`-Guard versehentlich hart verdrahtet / Datei angelegt** (Scope-Creep, injizierter Fakt 1). → Mitigation: Verify in Schritt 3 prüft „falls vorhanden"/Lint-Hint-Semantik explizit; `fd lint-open-issues` muss **weiterhin** 0 Treffer haben. → Rollback: Guard zurück auf if-present; keine Datei committen.
- **R4 — Referenz-Grep trifft Historie/Vorhaben-Docs** (falsch-positive Failures). → Mitigation: Grep-Scope bewusst nur `README.md AGENTS.md CLAUDE.md docs/upstream-roadmap.md` (+references/ konditional); `CHANGELOG.md`, `docs/releases/*`, `docs/prds|specs|test-designs|adr|manifests` **ausgenommen** (Spec §4.3). → Rollback: Grep-Scope korrigieren, keine Historie umschreiben.
- **R5 — `project-locality.md:11` generische-vs-plugin-Doku-Konflikt** (Spec §4.3 vs §5). → Mitigation: GATE 2 (Schritt 11) entscheidet (a) belassen+Ausnahme oder (b) umformulieren. → Rollback: `git checkout -- references/operational-rules/project-locality.md`.
- **R6 — Trigger-Lücke** (Slash-String nicht als Skill-Trigger). → Mitigation: Schritt 8 grep-verifiziert je Skill; fehlt einer → ergänzen VOR Löschung. → Rollback: Trigger-Phrase nachtragen.
- **R7 — pytest rot durch unerwartete command-Kopplung.** → Mitigation: vorab verifiziert `rg commands/ tests/` == 0. → Rollback: `git revert` des Delete-Commits, Ursache prüfen.

**Globaler Rollback:** Branch `docs/cmd-script-consolidation-plan`; jeder Schritt ist ein eigener kohärenter Commit → `git revert <sha>` einzeln möglich; kein force-push, kein `reset --hard`.

## Human-Gates  ‹Wann: Freigabe›

- [ ] **GATE 1 (VOR Phase F / jeder Löschung):** Coverage-Matrix (Spec §2) alle 7 Zeilen ✓ (5 Router deckungsgleich + `wiki-issues` mit PUSH+POP angelegt, Diff-Judge inhaltlich leer, `lint-open-issues`-Guard überlebt, Routing-Zeile da). Deletion erst nach expliziter Freigabe.
- [ ] **GATE 2 (in Phase E, Schritt 11):** Entscheidung zu `references/operational-rules/project-locality.md:11` — generisch belassen (+ dokumentierte Grep-Ausnahme) **oder** umformulieren. Nicht still selbst wählen.
- [ ] **GATE 3 (vor Merge nach `main`):** Alle Acceptance-Criteria ✓, `pytest` grün, Referenz-Grep sauber, `commands/` weg. Freigabe für Merge/Push (Push generell nur mit expliziter Zustimmung).

**Deletion-Preconditions (müssen ALLE ✓ sein, bevor Schritt 13 startet):**
1. `skills/wiki-issues/SKILL.md` existiert mit PUSH+POP (Schritt 3–5).
2. Diff Command-Body ↔ Skill-Operation inhaltlich leer, beide Paare (Schritt 4/5/12).
3. `lint-open-issues`-Referenzen guarded/if-present übernommen, Datei weiterhin nicht existent (Schritt 3).
4. Routing-Zeile in `skills/wiki/SKILL.md` (Schritt 6).
5. Coverage-Matrix alle 5 Router ✓ + Slash-Trigger vorhanden (Schritt 7–8).
6. GATE 1 freigegeben (Schritt 9).

---
### Checkliste
- [x] Done-Definition konkret  ‹Wann-erledigt›  (Acceptance-Criteria Spec §5 gespiegelt, binär)
- [x] Jeder Schritt hat einen Verify-Check  ‹Wie›  (⌘ Kommando oder 👁 Judge je Schritt 1–18)
- [x] Riskante Schritte haben Rollback  (R1–R7 + globaler `git revert`, Branch benannt)
- [x] Human-Gates markiert  ‹Wann›  (GATE 1 vor Löschung, GATE 2 references-Entscheidung, GATE 3 vor Merge)
- [x] Schritte atomar genug → werden zu Tasks  (18 atomare Schritte, je 1 Aktion + 1 Verify)
- [x] 7-W-Abdeckung geprüft  (Wie/Wann/Womit/Wann-erledigt; Reihenfolge erzwingt Migration+Coverage VOR Deletion)
- [x] Injizierte Fakten honoriert  (lint-open-issues out-of-scope + guarded + Verify-Step 3; Auto-Discovery → kein Manifest-Edit)
