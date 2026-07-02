---
artifact: spec
slug: cmd-script-consolidation
module: commands
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [prd, adr-0001]
---

# Spec — Command→Skill-Migration + Löschung [commands]

> WIE migrieren wir jedes command-Verhalten verlustfrei in einen Skill und löschen dann `commands/`?
> **Anker (7 W):** Wie · Womit · Was · Wann-erledigt · [PRD](../prds/cmd-script-consolidation.md) · [ADR-0001](../adr/0001-delete-commands-skills-only.md)

## 1. Ziel & Kontext  ‹Was/Warum → PRD›
Alle command-Funktionalität geht in Skills auf, `commands/` wird gelöscht (Migration VOR Löschung).
Reiner Refactor: gleiche Trigger → gleiches Verhalten → gleiche Outputs. Kein neues Feature, keine
Verhaltensänderung an den Ziel-Skills außer dem *Hinzufügen* der bisher command-only Logik.

**Verifizierter Ist-Stand (Evidenz):**
- 7 command-Dateien: `autoresearch.md`, `wiki.md`, `doc-pipeline.md`, `canvas.md`, `save.md` (top-level, dünne Router) + `wiki/fix-issues.md` (211 z) + `wiki/handoff.md` (126 z) (fette Logik).
- `plugin.json` existiert nicht; `.claude-plugin/marketplace.json` enumeriert **weder** commands **noch** skills → Löschen von `commands/` erfordert **keine** Manifest-Änderung.
- Die 5 Router bestehen aus „Read the `<skill>` skill. Then run …" + einer Usage-/Op-Tabelle, die inhaltlich die Skill-Operations spiegelt.
- `fix-issues`/`handoff` verwalten einen **kuratierten Issue-Stack** in `wiki/meta/OPEN-ISSUES.md` (Template: `_templates/open-issues.md`). Dieses Verhalten hat **keinen** backing Skill.

## 2. Schnittstellen / Verträge  ‹Womit›  — Coverage-Matrix (verifiziert gegen Code)

Legende: ✓ = Ziel-Skill deckt das command-Verhalten bereits vollständig (reines Löschen sicher) · **gap** = Logik fehlt im Skill, muss migriert werden.

| command | Zeilen | Ziel-Skill | Aktion | verifiziert deckungsgleich? |
|---|--:|---|---|:--:|
| `autoresearch.md` | 19 | `autoresearch` | löschen (Router) | ✓ |
| `wiki.md` | 23 | `wiki` | löschen (Router) | ✓ |
| `doc-pipeline.md` | 25 | `doc-pipeline` | löschen (Router) | ✓ |
| `canvas.md` | 21 | `canvas` | löschen (Router) | ✓ |
| `save.md` | 16 | `save` | löschen (Router) | ✓ |
| `wiki/fix-issues.md` | 211 | **`wiki-issues` (neu)** | **Logik migrieren** → löschen | **gap** |
| `wiki/handoff.md` | 126 | **`wiki-issues` (neu)** | **Logik migrieren** → löschen | **gap** |

### 2.1 Deckungsnachweis je Router (warum reines Löschen sicher ist)

Jede Router-Zeile wurde gegen die `SKILL.md` des Ziel-Skills geprüft. Kein Router trägt Logik, die der Skill nicht schon hat:

| command | command-Inhalt (verifiziert) | im Skill vorhanden? |
|---|---|---|
| `autoresearch.md` | „Read the `autoresearch` skill", Usage `[topic]`/no-topic, Free-Text-Arg | Skill *Topic Selection* A (expliziter Text/Task-ID), B (queue), C (boundary), D (user-ask) + *Research Loop* + *Filing Results* → **deckt alles**, inkl. Free-Text via Pfad A |
| `wiki.md` | „Read the `wiki` skill" + Setup-Schritte (Obsidian-Check, `.obsidian/`-Check, `claude mcp list`, „What is this vault for?", scaffolden) | Skill *SCAFFOLD Operation* + *Operations*-Routing-Tabelle → **deckt alles** |
| `doc-pipeline.md` | „Read the `doc-pipeline` skill" + 4-Stage-Workflow, Batch-Subagent, `--out-dir`, Fact-check-Verweis | Skill *Stage 1–4* + *Batch mode (parallel)* + *Fact-check protocol* + `--out-dir`-Beispiel → **deckt alles** |
| `canvas.md` | „Read the `canvas` skill" + Op-Tabelle (`new`/`add image|text|pdf|note`/`zone`/`list`/`from banana`), Default-Canvas, Auto-Create | Skill *Operations* (jede Op 1:1) + *Default Canvas* + *Banana Integration* → **deckt alles** |
| `save.md` | „Read the `save` skill" + Usage (`/save`, `[name]`, `session`, `concept`, `decision`), „kein Vault → run /wiki first", Dedup-Check | Skill *Save Workflow* + *Note Type Decision* + *What to Save vs. Skip* (Dedup: „update existing page instead of creating a duplicate") → **deckt alles** |

**Residuale, bewusst akzeptierte Verhaltensdifferenz (ADR-0001):** Der `/slash`-Aufruf entfällt. Skill-Trigger-Phrasen (in jeder `SKILL.md` gelistet, inkl. der `/slash`-Strings wie „/save", „/canvas", „/autoresearch") plus Auto-Trigger übernehmen die Invocation. Kein *inhaltliches* Verhalten geht verloren.

### 2.2 Offene Verträge — aufgelöst

- **Dupliziert `handoff` den externen `handoff`/`cs-handoff`-Plugin-Skill?** → **NEIN.** Verifiziert: Der externe `handoff`-Plugin-Skill (`handoff:cs-handoff`, `handoff:handoff`) *„compact[et] the current conversation into a handoff document for another agent to pick up"* (Conversation→Handoff-Doc, Redaction, Auto-Load bei SessionStart). `commands/wiki/handoff.md` dagegen *synthetisiert Session-Erkenntnisse in `wiki/meta/OPEN-ISSUES.md` als priorisierten Issue-Stack*. **Gleiches Wort, andere Capability** (Conversation-Transfer vs. persistenter Issue-Backlog). Kein Recreate des externen Skills; kein Fold in `cs-handoff`. Die command-Logik bekommt eine **eigene** Skill-Heimat (siehe unten).
- **Wohin `fix-issues`/`handoff` folden?** → **Ein neuer Skill `wiki-issues`.** Beide Commands operieren auf **derselben Datei** (`wiki/meta/OPEN-ISSUES.md`) mit **demselben Datenmodell** (YAML-`stack:` + `### I-YYYY-NNN`-Body-Sektionen, 7er-Section-Whitelist). `handoff` = *push* (synthetisieren/einsortieren), `fix-issues` = *pop* (verifizieren/abarbeiten). Sie sind zwei Enden **einer** Capability → gehören in **einen** Skill mit zwei Operations, nicht in zwei.
- **Warum nicht in `wiki-lint` folden?** Verifiziert unterschiedliche Concerns: `wiki-lint` **detektiert** automatisiert Health-Probleme (Orphans, dead links, stale claims) über einen deterministischen Aggregator (`scripts/run-lint.py`) und schlägt Auto-Fixes vor (*Before Auto-Fixing*). `fix-issues`/`handoff` **kuratieren** einen manuell gepflegten Prioritäts-Backlog (menschliche Synthese, LIFO/Priority-Ordering, Aggregations-Zustimmung). Fold würde zwei orthogonale Modelle in einen Skill zwingen → verworfen.
- **Namens-Präzedenz:** `docs/upstream-roadmap.md` PR4 nennt genau diesen Zielnamen: *„`_templates/open-issues.md` + a `wiki-issues` skill"*. Die Spec übernimmt `wiki-issues` konsistent.

### 2.3 Contract des neuen Skills `wiki-issues` (Verhalten = Union der zwei Commands, unverändert)

| Aspekt | Wert (verifiziert aus den command-Bodies) |
|---|---|
| Skill-Verzeichnis | `skills/wiki-issues/SKILL.md` |
| Operation PUSH (ex-`handoff`) | Trigger u.a. „handoff", „/wiki:handoff", „Session-Erkenntnisse ablegen"; optionales Arg = Session-Topic/Priority-Override (z.B. „handoff P1") |
| Operation POP (ex-`fix-issues`) | Trigger u.a. „fix issues", „/wiki:fix-issues", „nächstes offenes Issue abarbeiten" |
| Datei | `wiki/meta/OPEN-ISSUES.md` (Template `_templates/open-issues.md`) |
| Datenmodell | Frontmatter `stack:`-Array (id `I-YYYY-NNN`, `priority` P0–P3, `section` aus 7er-Whitelist `enforcement|lint|vault-content|tooling|templates|skill-plugin|eval-observability`, `title`, `pushed`, `blocked_by`, opt. `inconclusive_since`/`inconclusive_reason`/`aggregated_from`) + pro Item `### I-YYYY-NNN — Titel` Body-Sektion. **Wahrheit im Frontmatter.** |
| Sortier-Invariante | priority ASC → ready-before-blocked → inconclusive-last → `pushed` DESC (LIFO-Tiebreaker) |
| Guardrails (POP) | genau 1 Issue/Aufruf; nur gegen saubere Git-Baseline (`git status --porcelain` clean, sonst Abbruch); nie stillschweigend aggregieren (Schritt-3-Zustimmung); nie unverifiziert löschen (4d bleibt im Stack); Stack↔Body-Sync sonst Abbruch |
| Verifikations-Pfade (POP) | 4a resolved · 4b stale-patch · 4c real-fix (≤2 Commits) · 4d inconclusive |
| Commit-Disziplin | conventional; nie `--no-verify`, nie `--amend`; Formate je Pfad wie im command |
| `allowed-tools` | Union: `Read, Edit, Bash, Grep, Glob` (POP) + `Read, Edit, Bash` (PUSH) → `Read, Edit, Bash, Grep, Glob` |
| Sprache | Issues Deutsch; Commit-Messages Deutsch/Englisch je Repo-Konvention |

**Bekannte Dangling-Referenz (aus den Command-Bodies, unverändert übernehmen):** beide Commands verweisen bei Drift/Guardrail-Bruch auf `scripts/lint/lint-open-issues.py`. Dieser Validator **existiert in diesem Repo nicht** (`fd lint-open-issues` = 0 Treffer; laut `CHANGELOG.md` „lands separately in the vault repo"). Reiner Refactor ⇒ Referenz **1:1 mitnehmen**, nicht neu erfinden und nicht reparieren (kein Scope-Creep; der fehlende Validator ist ein bestehendes, nicht durch diese Migration verursachtes Faktum → separat als Issue führen, nicht hier).

## 3. Verhalten  ‹Wie›  (Verhalten der *Migration*, nicht der Skills)

### Happy path
1. **Router-Skills (5):** Ziel-Skill deckt laut §2.1 alles → command-Datei ersatzlos löschen. Keine Skill-Edits nötig außer optionaler Trigger-Ergänzung (siehe Edge-Cases).
2. **`wiki-issues` (neu):** `skills/wiki-issues/SKILL.md` anlegen; die zwei command-Bodies **wortgetreu** als zwei Operations (PUSH/POP) übernehmen (Datenmodell, Guardrails, Schritte 1–7, Commit-Formate, Edge Cases identisch). Danach `commands/wiki/fix-issues.md` + `commands/wiki/handoff.md` löschen.
3. **`commands/` leeren:** nach Migration ist das Verzeichnis leer → gesamtes `commands/` entfernen.
4. **Referenzen ziehen:** alle Doku-/Konfig-Verweise auf `commands/` bzw. `/wiki:*` aktualisieren (Liste §4.3).
5. **Verifizieren:** `fd . commands/` == 0; Coverage-Matrix alle ✓; `pytest tests/` grün; Referenz-Grep 0 (bereinigt um erlaubte historische Erwähnungen, s. Edge-Cases).

### Edge-Cases
- **`/slash`-UX entfällt:** akzeptiert (ADR-0001). Sicherstellen, dass die in den Router-Bodies genannten Slash-Strings als Trigger-Phrasen in der jeweiligen `SKILL.md` stehen. Verifiziert vorhanden: `save`, `canvas`, `autoresearch` führen ihre `/…`-Strings bereits als Trigger; `wiki` triggert auf „/wiki"; `doc-pipeline` triggert auf „doc pipeline"/„convert to markdown". Für `wiki-issues` neue Trigger inkl. „/wiki:fix-issues"/„/wiki:handoff" aufnehmen, damit die alte Slash-Erwartung sprachlich weiter greift.
- **`CHANGELOG.md` + `docs/releases/*` + `docs/upstream-roadmap.md`** erwähnen `commands/…` **historisch/absichtlich**. Changelog- und Release-Einträge sind append-only Historie → **nicht** umschreiben. `upstream-roadmap.md` beschreibt den Zielzustand (`wiki-issues`) → nur angleichen, falls es den Ist-Zustand behauptet.
- **`docs/prds|specs|test-designs|manifests` dieses Vorhabens** referenzieren `commands/` als *Arbeitsgegenstand* → bleiben (sie beschreiben die Migration selbst). Der Referenz-Grep in den Acceptance-Kriterien schließt `docs/**` und `CHANGELOG.md` bewusst aus.

### Fehlerbehandlung
- **Skill-Trigger deckt Slash-String nicht** → Migration unvollständig: Trigger-Phrase ergänzen, bevor gelöscht wird.
- **`wiki-issues` weicht vom command-Body ab** (fehlender Guardrail/Schritt/Commit-Format) → reiner Refactor verletzt: fehlt etwas, ist die Migration nicht fertig; Diff Command↔Skill muss inhaltlich leer sein (nur Framing „command"→„skill operation").
- **Löschung vor Migration** → verboten (ADR-0001 + PRD must): erst Deckung nachgewiesen (Matrix ✓ / Skill angelegt), dann löschen.

## 4. Gewählter Ansatz  ‹Wie›

### 4.1 Migrate-then-delete je command
1. `autoresearch.md` → **delete** (Deckung §2.1 verifiziert). Vorher: Trigger „/autoresearch" in `skills/autoresearch/SKILL.md` vorhanden — bestätigt.
2. `wiki.md` → **delete**. Setup-Workflow vollständig in *SCAFFOLD Operation*; Trigger „/wiki" vorhanden.
3. `doc-pipeline.md` → **delete**. 4-Stage/Batch/Fact-check/`--out-dir` alle im Skill.
4. `canvas.md` → **delete**. Alle Ops inkl. `from banana` im Skill.
5. `save.md` → **delete**. Workflow/Note-Types/Dedup im Skill; „No wiki vault → run /wiki first" ist eine reine UX-Zeile, deren Kern (Vault-Fehlend-Behandlung) der Skill-Kontext trägt.
6. `wiki/fix-issues.md` → **migrate** nach `skills/wiki-issues/SKILL.md` (Operation POP), dann delete.
7. `wiki/handoff.md` → **migrate** nach `skills/wiki-issues/SKILL.md` (Operation PUSH), dann delete.
8. `commands/` (jetzt leer) → **delete** (Verzeichnis).

### 4.2 Skill-Heimat für `fix-issues`/`handoff`
Neuer Skill **`wiki-issues`** (Contract §2.3). Begründung: gemeinsame Datei + gemeinsames Datenmodell, komplementäre Operations (push/pop), abgegrenzt von `wiki-lint` (Detection vs. Kuration); Name durch `upstream-roadmap.md` PR4 präzediert. `wiki`-Routing-Tabelle in `skills/wiki/SKILL.md` um eine Zeile ergänzen („fix issues"/„handoff" → `wiki-issues`), analog zu den bestehenden Routing-Zeilen — damit bleibt das command-Verhalten „über das wiki-Ökosystem erreichbar" erhalten.

### 4.3 Referenz-Update-Liste (verifiziert per `rg`/`fd`)
Zu aktualisieren (echte Ist-Zustands-Referenzen):

| Datei | Referenz (verifiziert) | Aktion |
|---|---|---|
| `README.md` | `├── commands/` im Struktur-Baum (Zeile ~350) | Zeile entfernen (Verzeichnis existiert nicht mehr) |
| `CLAUDE.md` (Vault) | Plugin-Skills-Tabelle listet `/wiki`, `/save`, `/autoresearch`, `/canvas`, `/doc-pipeline`, `/wiki-fold` als „Trigger" | `/slash`-Spalte auf natürlichsprachliche Trigger/Skill-Namen umstellen; `wiki-issues` (fix-issues/handoff) aufnehmen |
| `AGENTS.md` | Zeilen 34/36: `save`/`canvas` mit „/save"/„/canvas" | Trigger-Notation an Skill-Auto-Trigger angleichen |
| `references/operational-rules/project-locality.md` | „Slash commands | `.claude/commands` …" | prüfen; falls generische CC-Doku (nicht plugin-spezifisch) → belassen, sonst angleichen |
| `docs/upstream-roadmap.md` | `commands/wiki-handoff.md` etc. + `.claude/commands/wiki/…` als Ist-Behauptung | auf Zielzustand `wiki-issues`/skills-only angleichen |

Nicht anfassen (Historie / Selbstbeschreibung des Vorhabens):
`CHANGELOG.md`, `docs/releases/*`, `docs/prds/*`, `docs/specs/*` (inkl. Sibling-Specs), `docs/test-designs/*`, `docs/manifests/*` — sie zitieren `commands/` als historischen oder als Migrations-Gegenstand.

### 4.4 Manifest/Plugin
Keine Änderung an `.claude-plugin/marketplace.json` nötig (enumeriert commands/skills nicht — verifiziert). Kein `plugin.json` vorhanden → nichts zu tun. Reihenfolge/Sequencing → Plan/Manifest (`docs/manifests/cmd-script-consolidation.json`), nicht diese Spec.

## 5. Acceptance-Criteria (binär, testbar)  ‹Wann-erledigt›
- [ ] Coverage-Matrix §2: alle 7 Zeilen aufgelöst (5× ✓ Router, 2× migriert) — vor jeder Löschung.
- [ ] `skills/wiki-issues/SKILL.md` existiert und enthält beide Operations (PUSH ex-`handoff`, POP ex-`fix-issues`) mit unverändertem Datenmodell, Guardrails, Schritten 1–7 und Commit-Formaten. Prüfbar: `rg -l 'I-YYYY-NNN|blocked_by|inconclusive_since|aggregated_from' skills/wiki-issues/SKILL.md` trifft.
- [ ] `fd . skills/wiki-issues -t f` ≥ 1 (Skill-Heimat für `handoff` **und** `fix-issues` vorhanden).
- [ ] Diff Command-Body ↔ `wiki-issues`-Operation inhaltlich leer (nur Framing geändert) — manuell/Judge-verifiziert.
- [ ] `fd . commands/` == 0 (Verzeichnis restlos entfernt).
- [ ] `skills/wiki/SKILL.md` *Operations*-Tabelle enthält eine `wiki-issues`-Routing-Zeile.
- [ ] `handoff`- **und** `fix-issues`-Verhalten via Skill-Trigger erreichbar (Trigger-Phrasen inkl. „/wiki:handoff"/„/wiki:fix-issues" in `wiki-issues`).
- [ ] Referenz-Grep sauber: `rg -n 'commands/' README.md AGENTS.md CLAUDE.md references/ docs/upstream-roadmap.md` == 0 (Historie/Vorhabens-Docs ausgenommen).
- [ ] `pytest tests/` grün (Regressionsnetz; keine command-Pfad-Abhängigkeit in Tests — verifiziert: Tests referenzieren `commands/` nicht).

## 6. Test-Design  ‹Wann-erledigt›
→ [test-design](../test-designs/cmd-script-consolidation.md) (Smoke: `fd commands/`; Coverage-Matrix; Skill-Load `wiki-issues`).

## 7. Security / Privacy  ‹Womit›
n/a — keine Datenpfad-Änderung. `wiki-issues` operiert (wie die Commands) nur auf `wiki/meta/OPEN-ISSUES.md`; keine neuen externen Sinks, keine Secret-Pfade. `hooks/wiki-path-safety.py` bleibt unangetastet (PRD-Constraint).

## 8. Rollout / Migration / Backout  ‹Wann›
- **Rollout:** in Reihenfolge §4.1 (migrieren → verifizieren → löschen). `commands/`-Löschung ist der letzte Schritt, erst nach grüner Matrix + angelegtem `wiki-issues`.
- **Backout:** `git revert` des Migrations-Commits stellt `commands/` wieder her (versioniert); `skills/wiki-issues/` ist additiv und kann separat entfernt werden. Da reiner Refactor: kein Datenmigrations-Rückbau nötig (OPEN-ISSUES-Format unverändert).

---
### Checkliste (vor status: approved)
- [x] Coverage-Matrix vollständig verifiziert · [x] Acceptance binär · [x] Test-Design verlinkt · [x] handoff-Heimat entschieden · [x] 7-W geprüft
