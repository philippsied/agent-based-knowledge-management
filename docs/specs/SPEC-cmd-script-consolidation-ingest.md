---
artifact: spec
slug: cmd-script-consolidation
module: ingest
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [prd, adr-0002]
---

# Spec — ingest-Cluster konsolidieren + co-locate [ingest]

> WIE verschieben wir die Ingest-Transform-Skripte unter `skills/wiki-ingest/scripts/` **ohne Verhaltensänderung**?
> **Anker (7 W):** Wie · Womit · [PRD](../prds/cmd-script-consolidation.md) · [ADR-0002](../adr/0002-colocate-scripts-under-skill.md)

## 1. Ziel & Kontext  ‹Was/Warum → PRD›
Ingest-Cluster (2 Skripte, ~328 LOC) zieht von `scripts/` nach `skills/wiki-ingest/scripts/` (ADR-0002: Skript beim besitzenden Skill). Reiner Refactor: **identisches Verhalten**, nur Ablageort + textuelle Referenzen ändern sich. Kein neuer Code, keine geänderte CLI, keine geänderte Ausgabe.

## 2. Schnittstellen / Verträge  ‹Womit›

### Skripte im Cluster
| Skript | LOC | Aktuell | Ziel |
|---|--:|---|---|
| `rewrite-wikilinks.py` | 118 | `scripts/` | `skills/wiki-ingest/scripts/` |
| `wiki-prepass.py` | 210 | `scripts/` | `skills/wiki-ingest/scripts/` |

### CLI-/Entrypoint-Verträge (unverändert zu erhalten)

**`rewrite-wikilinks.py`** — Bulk-Rewrite von `[[wikilink]]`-Vorkommen in `<vault>/wiki/**/*.md` anhand einer TSV-Mapping-Datei.
- Aufruf: `rewrite-wikilinks.py <mapping.tsv> [--vault PATH] [--dry-run] [--include-templates]`
- Positional: `mapping` (Pflicht) — TSV, eine Regel/Zeile `alt-link-text<TAB>NeuerBasenameOhneMd`; `#`-Zeilen = Kommentar; Zeilen ohne Tab → `WARN` nach stderr, übersprungen.
- Flags: `--vault` (Root-Override), `--dry-run` (nur zählen/melden, nicht schreiben), `--include-templates` (auch `wiki/_templates/` einbeziehen).
- Vault-Root-Auflösung (inline `resolve_vault`): **`--vault` → `KM_VAULT_PATH` → CWD**.
- Input: `mapping.tsv` (Datei) + `<vault>/wiki/**/*.md`. Output: In-place-Rewrites derselben `.md` (bzw. keine bei `--dry-run`); pro geänderte Datei `"{pfad}: {n}"` nach stdout, Abschlusszeile `"Total: {total} substitutions across {changed} files[ (dry-run)]"`.
- Matching case-insensitiv auf Link-Text; Anchor `#foo` und Alias `|alias` bleiben erhalten (Regex-Gruppe 2). Standardmäßig übersprungen: `wiki/_templates/` und Dateien `lint-report-*.md`.
- Exit: `0` Erfolg · `1` Mapping fehlt/leer bzw. `wiki/` kein Verzeichnis. Vault nicht auflösbar → `SystemExit("ERROR: …")`.

**`wiki-prepass.py`** — Pre-Ingest-Entity-Registry-Vorlauf: extrahiert häufige Groß­schreib-Nominalphrasen aus neuen `.raw/`-Quellen und seedet Stub-Seiten, damit parallele Ingest-Agenten Seiten *editieren* statt Duplikate zu *schreiben*.
- Aufruf: `wiki-prepass.py [file1.md file2.md …]` · `wiki-prepass.py --all` · `wiki-prepass.py --vault PATH --all`
- Positional: `files` (0..n; absolut oder vault-relativ). Flags: `--all` (alle `*.md` in `<vault>/.raw/`, nicht-rekursiv, ohne Dotfiles), `--vault`, `--threshold N` (Default `3`, Mindest­häufigkeit über den Batch), `--dry-run` (melden ohne Schreiben).
- Vault-Root-Auflösung (inline `resolve_vault`): **`--vault` → `KM_VAULT_PATH` → CWD**.
- Input: `files` bzw. `.raw/*.md`; liest je Datei den Text (`errors="replace"`). Output: Stub-`.md` unter `<vault>/wiki/<folder>/<Hyphenated-Name>.md` (`folder` ∈ `{entities, concepts}` via `suggest_folder`) mit Frontmatter `type: entity`, `status: seed`, tags `stub`/`prepass-seed`; abschließend ein **JSON-Report** nach stdout (`vault, files_scanned, stubs_seeded, already_existed, threshold, dry_run, top_seeded[], top_skipped[]`, `ensure_ascii=False`).
- Bereits existierende Seite (Basename-Match, beliebiger Ordner) → nicht überschrieben, als `skipped` gezählt. Fehlende Input-Datei → `WARN` nach stderr, übersprungen.
- Exit: `0` Erfolg · `1` keine Input-Dateien / `.raw/` fehlt (bei `--all`). Vault nicht auflösbar → `SystemExit`.

### Konsumenten / Referenzen (verifiziert per `rg`)
- **Kein produktiver In-Process-Import:** Beide Skripte sind reine Stdlib-Standalones (`argparse, os, re, sys, pathlib`; prepass zusätzlich `collections, datetime, json`). **Keiner importiert `lib/vault_root.py`** — jeder trägt eine eigene, inline-kopierte `resolve_vault()`. → Move erfordert **null Import-Fixes**.
- **Kein `skills/`-Pfadref auf diese zwei Skripte:** `skills/wiki-ingest/SKILL.md` nennt nur `scripts/allocate-address.py` (gehört zu spec-dragonscale, **out of scope**) — **nicht** `rewrite-wikilinks.py`/`wiki-prepass.py`. Kein anderer `skills/`-File nennt sie per Pfad. → Anders als die Skelett-Annahme gibt es **innerhalb `skills/` keinen load-bearing Pfad-Ref** für diesen Cluster.
- **`skills/wiki/references/frontmatter.md`:** nennt keinen Skriptpfad; dokumentiert aber das `status`-Enum inkl. `seed`. `wiki-prepass.py` **produziert** Seiten mit `status: seed` + tag `prepass-seed` → **Vertrags-Kopplung** (Stub-Frontmatter muss schema-konform bleiben), **kein Pfad zum Ändern**.
- **Kein Test referenziert** eines der Skripte oder seine Funktionen (`tests/` gesweept: `rewrite/prepass/extract_candidates/build_regex/load_mapping/slugify/suggest_folder/stub_body` → 0 Treffer). Keine gezielten Unit-Tests existieren.
- **Doc-Layer-Referenzen (Bookkeeping, kein Code):** `docs/prds/cmd-script-consolidation.md:43`, `docs/adr/0002-colocate-scripts-under-skill.md:32`, `docs/upstream-roadmap.md` (Zeilen 97/213/293/294/333/363), `docs/plans/PLAN-sh-to-py-full-migration.md` (109/541), `docs/test-designs/cmd-script-consolidation.md:30` (Smoke-Gate-Regex), Geschwister-Specs. Diese beschreiben die Migration bzw. verweisen historisch auf `scripts/…`.

### Shared-Util-Befund (ADR-0002 „shared → lib/")
- `resolve_vault()` ist **innerhalb des Clusters dupliziert** (identisch in beiden Skripten) und spiegelt konzeptuell `lib/vault_root.py`.
- **Achtung — Präzedenz-Divergenz:** Inline-`resolve_vault()` nutzt **`cli_arg → KM_VAULT_PATH → CWD`**; `lib/vault_root.py::resolve_vault_root()` nutzt **`KM_VAULT_PATH → cli_arg → CWD`** (Doku + Code). Der prepass-Docstring behauptet fälschlich „Mirror lib/vault_root.py". Ein naives „auf `lib/vault_root` umstellen" würde also **Verhalten ändern** (verletzt den Refactor-Vertrag). → Dedup ist **`should`**, nicht `must`; falls durchgeführt, muss die bestehende Präzedenz `cli_arg → env → cwd` **bit-genau erhalten** bleiben (nicht `resolve_vault_root` übernehmen). Koordination mit spec-lint/spec-dragonscale, kein separates Duplikat in `lib/`.

## 3. Verhalten  ‹Wie›

### Happy path
- **rewrite-wikilinks:** Nach dem Move liefert `skills/wiki-ingest/scripts/rewrite-wikilinks.py <mapping> [--vault …]` für denselben Vault + dasselbe Mapping **identische** In-place-Rewrites und identisches stdout (`{pfad}: {n}` + `Total: …`) wie zuvor aus `scripts/`.
- **wiki-prepass:** `--all` bzw. explizite Dateien seeden dieselben Stubs in dieselben `wiki/<folder>/`-Ziele mit identischem Frontmatter und identischem JSON-Report (bei gleicher Eingabe/Threshold).
- Vault-Auflösung greift weiterhin über `--vault`/`KM_VAULT_PATH`/CWD; die Skripte sind CWD-unabhängig, daher ist der neue Speicherort für die Laufzeit irrelevant (kein `__file__`- oder relativer-Import-Bezug).

### Edge-Cases
- `rewrite-wikilinks`: `--dry-run` schreibt nichts, zählt korrekt; `--include-templates` bezieht `_templates/` ein; `lint-report-*.md` bleiben stets ausgenommen; Anchor/Alias bleiben erhalten; längere Keys matchen zuerst (Regex nach Länge sortiert).
- `wiki-prepass`: existierende Basename-Seite → `skipped`, nicht überschrieben; `--threshold` filtert; Umlaut-Entities (`ENTITY_RE` mit `ÄÖÜäöüß`) werden erkannt; nur Multi-Word oder Acronym-Style (2–6 Großbuchstaben) zählen; `STOPLIST` verworfen.
- Hyphenierte Dateinamen (`rewrite-wikilinks.py`, `wiki-prepass.py`) sind **nicht als Modul importierbar** — hier unkritisch, da niemand sie importiert (nur Ausführung als Skript).

### Fehlerbehandlung
- Mapping fehlt/leer bzw. `wiki/` fehlt → Exit `1` + `ERROR` nach stderr (rewrite-wikilinks).
- Keine Input-Dateien / `.raw/` fehlt bei `--all` → Exit `1` + `ERROR` (wiki-prepass); fehlende Einzeldatei → `WARN`, weiter.
- Vault-Root nicht auflösbar → `SystemExit("ERROR: vault root could not be resolved")` (beide).
- All dieses Verhalten bleibt **byte-genau** erhalten; der Move darf keine Fehlerpfade berühren.

## 4. Gewählter Ansatz  ‹Wie›
1. **Verschieben** (Inhalt unverändert): `git mv scripts/rewrite-wikilinks.py skills/wiki-ingest/scripts/rewrite-wikilinks.py` und `git mv scripts/wiki-prepass.py skills/wiki-ingest/scripts/wiki-prepass.py`. Ausführ-Bit (`0755`) via `git mv` erhalten.
2. **Import-/Pfad-Fixes:** **keine** — beide Skripte sind Stdlib-Standalones ohne relative Imports und ohne `__file__`-Bezug; kein produktiver Konsument importiert sie.
3. **Doc-Referenz-Update (Bookkeeping):** `scripts/rewrite-wikilinks.py`/`scripts/wiki-prepass.py` → `skills/wiki-ingest/scripts/…` anpassen in: `docs/prds/…:43`, `docs/adr/0002-…:32`, `docs/upstream-roadmap.md` (97/213/293/294/333/363), `docs/plans/PLAN-sh-to-py-full-migration.md` (109/541). Smoke-Gate-Regex in `docs/test-designs/cmd-script-consolidation.md:30` „um neue Pfade bereinigen" (siehe §5).
4. **SKILL.md / frontmatter.md:** **keine Pfad-Edits** für diesen Cluster — `wiki-ingest/SKILL.md` nennt diese Skripte nicht (nur `allocate-address.py`, out of scope); `frontmatter.md` nennt keinen Skriptpfad. Beide nur **verifizieren** (Contract-Check, §5), nicht editieren.
5. **Docstring-Kosmetik (optional, nicht blockierend):** „Vault root resolution (matches lib/vault_root.sh)" in beiden Docstrings ist veraltet (`.sh` existiert nicht mehr). Angleichen an `.py` erlaubt, aber kein Gate (Kommentar, nicht load-bearing) — vgl. PLAN-sh-to-py:109.
6. **Within-Cluster-Dedup von `resolve_vault()` (`should`, optional):** nur wenn ohne Verhaltensänderung möglich. Präzedenz `cli_arg → KM_VAULT_PATH → CWD` **muss** erhalten bleiben; `lib/vault_root.resolve_vault_root()` (env-first) ist **nicht** eins-zu-eins verwendbar → nicht ungeprüft übernehmen. Bevorzugt: Beibehaltung der Inline-Kopien oder geteilter Helper mit exakt dieser Präzedenz; kein neues Duplikat in `lib/`.

## 5. Acceptance-Criteria (binär, testbar)  ‹Wann-erledigt›
- [ ] `skills/wiki-ingest/scripts/rewrite-wikilinks.py` **und** `skills/wiki-ingest/scripts/wiki-prepass.py` existieren; `scripts/rewrite-wikilinks.py` **und** `scripts/wiki-prepass.py` existieren **nicht** mehr (`test -f` / `! test -e`).
- [ ] Beide verschobenen Dateien sind **inhaltlich identisch** zum Vorzustand (`git show HEAD:scripts/<name>` == neue Datei; nur Doc-Referenz-Bookkeeping in `docs/` weicht ab).
- [ ] Beide bleiben ausführbar (`test -x`) und `--help` liefert unveränderten Usage-Text; Exit `0`.
- [ ] **Verhaltens-Parität rewrite-wikilinks:** gegen Fixture-Vault + festes Mapping ist stdout/Rewrite-Resultat neu == alt (Diff leer); `--dry-run` schreibt nichts.
- [ ] **Verhaltens-Parität wiki-prepass:** gegen Fixture-Vault (`--all --dry-run`) ist der JSON-Report neu == alt (Diff leer, `ensure_ascii=False` beachtet).
- [ ] Doc-Referenzen aktualisiert: `rg -n 'scripts/(rewrite-wikilinks|wiki-prepass)' docs/` liefert nur bewusst-historische Kontexte; keine Referenz behauptet die Skripte lägen noch unter `scripts/` als aktueller Pfad.
- [ ] Smoke-Gate grün: `rg 'commands/|scripts/(run-lint|lint-|boundary|tiling|allocate|rewrite-wikilinks|wiki-prepass)'` über README/AGENTS/GEMINI/Makefile/docs/SKILL.md == 0 nach Bereinigung um neue Pfade (test-designs:30).
- [ ] **Verifiziert (kein Edit nötig):** `skills/wiki-ingest/SKILL.md` und `skills/wiki/references/frontmatter.md` referenzieren keinen der beiden Skriptpfade → keine Änderung; `wiki-prepass`-Stub-Frontmatter (`status: seed`, tag `prepass-seed`) bleibt schema-konform zu `frontmatter.md`.
- [ ] **Betroffene Tests grün:** volle `tests/`-Suite läuft unverändert durch (kein Test referenziert diese Skripte → Regressionsnachweis, keine neuen Pflicht-Tests).

## 6. Test-Design  ‹Wann-erledigt›
→ [test-design](../test-designs/cmd-script-consolidation.md) (Unit: rewrite/prepass Output-Parität gegen Fixture-Vault, pre/post-Move-Diff · Smoke: keine toten Pfad-Referenzen)

## 7. Security / Privacy  ‹Womit›
n/a. Reiner Verschiebe-Refactor; keine neue Datenverarbeitung, keine neuen Schreibziele, kein geänderter Vertrauensrahmen.

## 8. Rollout / Migration / Backout  ‹Wann›
- **Rollout:** ein atomarer Commit (2× `git mv` + Doc-Referenz-Updates).
- **Backout:** `git revert <commit>` stellt Ablageort + Referenzen wieder her; da keine Importe/Konsumenten betroffen sind, ist der Backout risikofrei. Alternativ `git mv` zurück nach `scripts/`.

---
### Checkliste (vor status: approved)
- [x] Referenzen aktualisiert (Doc-Layer gelistet; `skills/` verifiziert **ohne** Pfad-Ref → kein Edit)
- [x] Acceptance binär (`test -f`/`! test -e`, Diff-leer-Gates, Smoke-Regex == 0)
- [x] Test-Design verlinkt
- [x] 7-W geprüft (Wie/Womit/Wann-erledigt abgedeckt)
- [x] Shared-Util-Befund dokumentiert (`resolve_vault` dupliziert; Präzedenz-Divergenz zu `lib/vault_root.py` → Dedup nur `should`, Verhalten erhalten)
- [x] Import-Graph verifiziert (Stdlib-Standalones, kein `lib/`-Import, kein `skills/`/`tests/`-Ref → null Import-Fixes)
