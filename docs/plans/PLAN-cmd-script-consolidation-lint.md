---
artifact: plan
slug: cmd-script-consolidation-lint
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [spec, adr-0002, test-design]
---

# Plan — lint-Cluster nach `skills/wiki-lint/scripts/` verschieben (Zero-Behavior-Change)

> Beantwortet: WELCHE Schritte, in welcher Folge, WIE verifiziert?
> Wegwerf-Artefakt: nach Done erledigt.
> **Anker (7 W):** Wie (primär: Schritte) · Wann (Reihenfolge) · Womit (Deps/Tools) · Wann-erledigt (Done-Definition)
> **Verträge:** [SPEC-lint](../specs/SPEC-cmd-script-consolidation-lint.md) · [Test-Design](../test-designs/cmd-script-consolidation.md) · [ADR-0002](../adr/0002-colocate-scripts-under-skill.md)

## Ziel & Done-Definition  ‹Wann-erledigt›

Alle 7 lint-Skripte liegen unter `skills/wiki-lint/scripts/`, `scripts/` enthält keine
`lint-*.py`/`run-lint.py` mehr, und der lint-Output ist **byte-identisch** zu vor dem Move.

**Done, wenn alle gleichzeitig gelten (= AC1–AC8 des Spec):**
- `run-lint.py --json` gegen den Fixture-Vault liefert `diff`-leer VOR vs. NACH Move (AC2).
- Markdown-Report identisch bis auf das Datum (AC3).
- `python3 tests/test_run_lint.py` + `test_lint_orphans/terminology/title_overlap.py` grün mit neuen Pfaden (AC4).
- Kein `ModuleNotFoundError` beim Modul-Import (`from vault_root import …` auflösbar) → beweist korrekte `REPO_ROOT`/lib-Tiefe (AC5).
- `make test` und `make lint` grün (AC7); `hooks/wiki-path-safety.py` unberührt; Read-only-Parität (AC8).
- Kein `grep` findet mehr `scripts/(run-lint|lint-)` als **ausführbaren** Pfad außerhalb `skills/wiki-lint/scripts/` (AC6) — inkl. Korrektur der kaputten `scripts/lint/`-Subdir-Refs (siehe Schritt 8 + §Geklärte Fakten).
- `evals/run.py` grün (Test-Design-Quality-Gate: Eval-Suites 100 % pass).

## Geklärte Fakten (in diesen Plan injiziert)  ‹Womit: Kontext›

1. **`REPO_ROOT`-Tiefe (verifiziert live):** `scripts/run-lint.py:51` = `REPO_ROOT = SCRIPT_DIR.parent`.
   Nach Move zeigt `SCRIPT_DIR.parent` auf `skills/wiki-lint/` → falsch. **Muss `SCRIPT_DIR.parent.parent.parent`** (3 Ebenen), damit `REPO_ROOT / "lib"` weiterhin `<repo>/lib` trifft.
2. **lib-Import-Tiefe der 3 Sub-Linter (verifiziert live):** `lint-orphans.py:29`, `lint-terminology.py:37`, `lint-title-overlap.py:30` = `parent.parent / "lib"`. **Muss `parent.parent.parent.parent / "lib"`** (Präzedenz live bestätigt: `skills/doc-pipeline/scripts/convert-doc.py:37`).
3. **`lint-deps` / `lint-programs` / `lint-rename` haben LOKALE `resolve_vault(cli_arg)`** (kein lib-Import, kein `sys.path`) → **KEIN Pfad-Edit** an diesen dreien nötig. `lint-rename.py` wird zudem nie via importlib aggregiert (nur CLI), zieht aber für Cluster-Kohäsion mit um.
4. **`_load_lint_module(stem)` ist `SCRIPT_DIR`-relativ** (`run-lint.py:56-77`) → übersteht den Move automatisch, **vorausgesetzt Aggregator + alle 5 aggregierten Sub-Linter landen im selben Ordner**. Bleibt einer zurück, bricht der Import zur Modul-Ladezeit.
5. **Broken-Subdir-Ref-Klasse (verifiziert live):** manche Caller referenzieren `scripts/lint/…` — einen **nicht existierenden Unterordner**. Zwei Unterklassen sauber trennen:
   - **In-Scope (jetzt korrigieren):** `skills/autoresearch/SKILL.md:46,60,61,262` referenziert `scripts/lint/lint-deps.py`. Reales File ist `scripts/lint-deps.py` → nach Move `skills/wiki-lint/scripts/lint-deps.py`. Diese 4 Refs auf die NEUE korrekte Location setzen (Teil des lint-Ref-Updates).
   - **OUT OF SCOPE (nur notieren, NICHT anfassen):** `commands/wiki/fix-issues.md:47,208` und `commands/wiki/handoff.md:98` referenzieren `scripts/lint/lint-open-issues.py`. `lint-open-issues.py` ist ein **vorbestehendes, externes Vault-Repo-Tool**, das in DIESEM Repo nicht existiert und **nicht** Teil dieses Clusters ist → nicht verschieben, nicht anlegen, nicht auf eine lint-Location zeigen lassen. Separat als Bug führen. Ebenso rein historisch: `docs/upstream-roadmap.md:321,364,365` (beschreibt alten `.sh`-Zustand) — Historie, unberührt lassen.
6. **Makefile-Realität (verifiziert live):** einziger **ausführbarer** lint-Aufruf ist `Makefile:30` (`@python3 scripts/run-lint.py`). Zeilen `:16-19` sind Help-`@echo`-Strings (nicht ausführbar, aber Doku → mitziehen für AC6-Konsistenz). Test-Targets `:50,54,58,62` rufen `tests/…` auf (unverändert; die Pfad-Konstante steckt IM Test).
7. **Repo-Zustand bei Planungsstart:** Branch `main`, Worktree hat vorbestehende Änderungen (2 gelöschte Rules-Dateien, untracked `skills/visualize/`). **Vor Ausführung:** sauberer Zustand auf dediziertem Branch herstellen (Human-Gate 0) — Move + Edits gehören in EINEN PR (atomarer importlib-Cluster).

## Schritte  ‹Wie›

> Reihenfolge ist load-bearing: **Baseline VOR Move** (sonst kein Golden-Vergleich), **Move atomar**, **Pfad-Fixes unmittelbar nach Move** (sonst rot), **Diff-Gate + Tests VOR Commit**.

### Phase A — Vorbereitung & Baseline (nichts verschieben)

1. **Branch + sauberer Baum.** Feature-Branch von `main` (z. B. `refactor/lint-colocate`); Worktree für diesen Cluster clean (vorbestehende, fremde Änderungen aus §Geklärte-Fakten-7 nicht mitnehmen).
   → verify: `git rev-parse --abbrev-ref HEAD` = Feature-Branch; `git status --short` zeigt keine lint-relevanten Änderungen.

2. **Fixture-Vault materialisieren (deterministisch, wiederverwendbar).** Baseline-Strategie: den vom Test bereits definierten Seed nutzen — `tests/test_run_lint.py::_seed_base_vault` (Spec §Checkliste-„Offen" nennt ihn als Kandidaten) — in ein **festes tmp-Verzeichnis** materialisieren, das für PRE und POST identisch ist. So ist der Golden-Diff nicht von Live-`wiki/`-Drift abhängig.
   → verify: `<fixture>/wiki/` existiert und enthält den vollständigen Seed (gleiche Datei-Liste wie `_seed_base_vault` erzeugt); zweiter Aufruf des Seeders auf leeres tmp erzeugt bit-gleiche Struktur (Determinismus-Check).

3. **PRE-Move-Baseline erfassen (JSON + Report).** `KM_VAULT_PATH=<fixture> python3 scripts/run-lint.py --json > $TMPDIR/lint-pre.json` und den Markdown-Report nach `$TMPDIR/lint-pre.md` sichern (Report liegt lt. Spec unter `<vault>/wiki/meta/lint-report-YYYY-MM-DD.md` → herauskopieren). Datum-Zeile im Report notieren (einzige erlaubte Differenz).
   → verify: `lint-pre.json` ist valides JSON mit Top-Level-Keys `date · vault_root · wiki_root · pages_scanned · checks[] · totals` und den 9 Check-Namen in fixer Reihenfolge (`spaced_filenames … research_program_codes`); `jq -e '.checks|length==9'` (oder Python-Äquivalent, siehe R6-Caveat) → true. Exit-Code `0`.

   **★ HUMAN-GATE 1: Baseline erfasst & plausibel, BEVOR irgendeine Datei bewegt wird.**

### Phase B — Atomarer Move + Pfad-Korrekturen (ein kohärenter Commit)

4. **Zielverzeichnis anlegen.** `mkdir -p skills/wiki-lint/scripts/` (existiert lt. Live-Check noch nicht).
   → verify: `test -d skills/wiki-lint/scripts` (Verzeichnis vorhanden).

5. **7 Dateien atomar verschieben (`git mv`, History erhalten).** `run-lint.py`, `lint-orphans.py`, `lint-terminology.py`, `lint-title-overlap.py`, `lint-deps.py`, `lint-programs.py`, `lint-rename.py` → `skills/wiki-lint/scripts/`. **Alle 7 in einem Rutsch** (importlib-Cluster darf nie zerrissen sein, §Geklärte-Fakten-4).
   → verify: `ls skills/wiki-lint/scripts/*.py | wc -l` = 7; `ls scripts/lint-*.py scripts/run-lint.py 2>/dev/null` → leer; `git status` zeigt 7× `renamed:` (nicht delete+add) → History erhalten.

6. **`run-lint.py` `REPO_ROOT`-Tiefe korrigieren** (`:51`): `REPO_ROOT = SCRIPT_DIR.parent` → `SCRIPT_DIR.parent.parent.parent`. `_load_lint_module` (SCRIPT_DIR-relativ) **NICHT** anfassen; die 5 `_load_lint_module("…")`-Aufrufe bleiben unverändert.
   → verify: `python3 -c "import importlib.util,sys; s=importlib.util.spec_from_file_location('run_lint','skills/wiki-lint/scripts/run-lint.py'); m=importlib.util.module_from_spec(s); sys.modules['run_lint']=m; s.loader.exec_module(m)"` → kein `ModuleNotFoundError` (beweist `REPO_ROOT/lib` trifft `<repo>/lib` UND alle 5 Sub-Linter luden). (= AC5 / Test-Design Unit-„Import-Smoke".)

7. **lib-Pfad-Tiefe in 3 Sub-Lintern anpassen:** `lint-orphans.py:29`, `lint-terminology.py:37`, `lint-title-overlap.py:30` je `parent.parent` → `parent.parent.parent.parent`. **`lint-deps.py` / `lint-programs.py` / `lint-rename.py` NICHT anfassen** (lokale `resolve_vault`, §Geklärte-Fakten-3).
   → verify: `grep -n 'parent.parent.parent.parent / "lib"' skills/wiki-lint/scripts/lint-orphans.py skills/wiki-lint/scripts/lint-terminology.py skills/wiki-lint/scripts/lint-title-overlap.py` → 3 Treffer; `grep -rn 'parent.parent / "lib"' skills/wiki-lint/scripts/` → leer (keine alte Tiefe übrig); `grep -n 'sys.path' skills/wiki-lint/scripts/lint-deps.py skills/wiki-lint/scripts/lint-programs.py skills/wiki-lint/scripts/lint-rename.py` → leer (unangetastet).

8. **Referenzen aktualisieren (operative Caller + Broken-Subdir-Fix).** Alle `scripts/(run-lint|lint-)`-Pfade auf `skills/wiki-lint/scripts/…` umziehen, PLUS die In-Scope-Broken-Subdir-Refs korrigieren:
   - **Ausführbar / Caller:**
     - `bin/release.py:49` → `"skills/wiki-lint/scripts/run-lint.py"`
     - `evals/run.py:68` → `"skills/wiki-lint/scripts/lint-terminology.py"`
     - `Makefile:30` → `@python3 skills/wiki-lint/scripts/run-lint.py`
   - **Test-Pfad-Konstanten (Whitebox/Blackbox laufen automatisch nach):**
     - `tests/test_run_lint.py:31` `HELPER = ROOT / "scripts" / "run-lint.py"` → `ROOT / "skills" / "wiki-lint" / "scripts" / "run-lint.py"`; Exec-Bit-Gates `:381,405,435` `ROOT/"scripts"/"lint-terminology.py"` → Skill-Pfad. `ROOT` (Repo-Root-Berechnung) **bleibt**.
     - `tests/test_lint_orphans.py:20` `SCRIPT = REPO / "scripts" / "lint-orphans.py"` → Skill-Pfad. `REPO` bleibt.
     - `tests/test_lint_terminology.py:18` und `tests/test_lint_title_overlap.py:17` analog.
   - **Broken-Subdir-Fix (In-Scope, §Geklärte-Fakten-5):** `skills/autoresearch/SKILL.md:46,60,61,262` `scripts/lint/lint-deps.py` → `skills/wiki-lint/scripts/lint-deps.py` (4 Vorkommen).
   - **Doku/Help (nicht ausführbar, für AC6-Konsistenz mitziehen):** `Makefile:16-19` Help-`@echo`-Strings; `skills/wiki-lint/SKILL.md` (Spec nennt `:26,29,55,380,390,417,422`); `_templates/research-queue.md:75` (`scripts/run-lint.py` → Skill-Pfad); Test-Docstrings (`tests/test_*.py:2` u. a.) kosmetisch.
   - **NICHT anfassen:** `commands/wiki/fix-issues.md:47,208`, `commands/wiki/handoff.md:98` (`lint-open-issues.py`, external/out-of-scope); `docs/upstream-roadmap.md:*` (Historie); Vorhaben-Docs `docs/{specs,prds,test-designs,adr,plans,manifests}/`; `CHANGELOG`/`releases/`; `.handoff/`; `docs/influence-log.md` (Log-Historie).
   → verify (Schritt 9 ist der harte Gate).

### Phase C — Verifikation (VOR Commit)

9. **Stale-Ref-Sweep = 0.** Kein ausführbarer/Caller-Pfad zeigt mehr auf die alte Ablage, und die In-Scope-Broken-Subdir-Ref ist weg:
   - `grep -rn -E 'scripts/(run-lint|lint-)' --include='*.py' --include='*.md' --include=Makefile . | grep -v -E 'docs/(specs|prds|test-designs|adr|plans|manifests)/|CHANGELOG|releases/|\.handoff/|docs/influence-log|docs/upstream-roadmap'` → nur noch Treffer, die `skills/wiki-lint/scripts/…` enthalten (alte Form 0).
   - `grep -rn 'scripts/lint/lint-deps' skills/autoresearch/SKILL.md` → leer (Broken-Subdir korrigiert).
   → verify: beide Bedingungen erfüllt (= AC6 + Test-Design Smoke „Refs aktualisiert").

10. **POST-Move-Baseline erfassen — identischer Fixture-Vault, identisches Kommando.** `KM_VAULT_PATH=<fixture> python3 skills/wiki-lint/scripts/run-lint.py --json > $TMPDIR/lint-post.json`; Report → `$TMPDIR/lint-post.md`.
    → verify: Exit-Code `0`; JSON valide, 9 Checks in fixer Reihenfolge.

11. **★ Diff-Gate: PRE vs. POST byte-identisch.** `diff $TMPDIR/lint-pre.json $TMPDIR/lint-post.json` → **leer** (AC2). `diff` der beiden `.md`-Reports → nur die Datumszeile differiert (AC3).
    → verify: JSON-`diff` liefert 0 Zeilen; Report-`diff` liefert ausschließlich die `date`-Zeile.

    **★ HUMAN-GATE 2: Diff-leer bestätigt, BEVOR der alte Zustand endgültig weg ist (= vor `git commit`/Merge). Ist der Diff nicht leer → Rollback (siehe Risiken), nicht „nachbessern am Output".**

12. **Test-Suite grün (neue Pfade).** `python3 tests/test_run_lint.py` (druckt „All tests passed.", B1–B67), `python3 tests/test_lint_orphans.py`, `python3 tests/test_lint_terminology.py`, `python3 tests/test_lint_title_overlap.py`.
    → verify: alle vier drucken ihre Pass-Zeile; kein `ModuleNotFoundError`, kein `FileNotFoundError` auf `scripts/…` (= AC4).

13. **Make-Targets + Evals grün.** `make lint` (läuft jetzt `skills/wiki-lint/scripts/run-lint.py`), `make test-run-lint`, `make test` (Gesamt), sowie `python3 evals/run.py` (bzw. das Eval-Kommando).
    → verify: `make test` endet mit „All tests passed."; `make lint` Exit `0`; Eval-Suites 100 % pass (= AC7 + Test-Design-Quality-Gate).

14. **Read-only-Parität / path-safety unberührt.** Sicherstellen, dass der Lint während Schritt 10 **nicht** in `<fixture>/wiki/`-Content geschrieben hat (nur `wiki/meta/lint-report-*.md` ist erlaubt) und `hooks/wiki-path-safety.py` nicht verändert wurde.
    → verify: `git status` zeigt keine Änderung an `hooks/wiki-path-safety.py`; im Fixture nur der erwartete Report neu (= AC8 / Test-Design Security).

### Phase D — Commit

15. **Ein kohärenter Commit (conventional).** `git mv` + alle Edits zusammen: `refactor(lint): co-locate lint cluster under skills/wiki-lint/scripts (ADR-0002)`. Push/PR nur nach ausdrücklicher Freigabe (Human-Gate 3).
    → verify: `git show --stat` listet 7 Renames + die Edit-Dateien in EINEM Commit; `git log -1 --format=%s` entspricht Conventional-Format.

## Abhängigkeiten / Reihenfolge  ‹Wann / Womit›

- **Werkzeuge:** `git` (`git mv`), `python3` (3.12+, wg. `sys.modules`-Registrierung vor `exec_module`), `make`, `grep`/`rg`, `diff`, `jq` **oder** Python-`json` (siehe R6 im Machine-Profil: kein `!` in Quotes/Heredocs — Diff/JSON-Checks als Datei-Skript oder mit `[ -e ]`/`==`-Vergleichen schreiben, nicht mit `!=`).
- **Harte Ordnung:** 1→2→3 (Baseline) **muss** vor 4→8 (Move+Fix) liegen; 6/7 (Pfad-Fixes) **unmittelbar** nach 5 (Move), sonst ist der Zwischenzustand rot; 9 (Stale-Sweep) + 11 (Diff-Gate) + 12–14 (Tests) **vor** 15 (Commit).
- **Kopplung (nicht splitten):** Move (5) + `REPO_ROOT`-Fix (6) + lib-Tiefe-Fix (7) + Test-Konstanten (8) gehören in **einen** Commit — der importlib-Cluster ist zwischen diesen Schritten nicht lauffähig (ADR-0002 „Rollout atomar").
- **Externe Deps:** keine (interne Skripte; einzige Caller sind die in §5 des Spec + der autoresearch-Broken-Ref gelisteten).

## Risiken & Rollback

- **R1 — Ein Sub-Linter bleibt in `scripts/` zurück** → `_load_lint_module` bricht beim Modul-Import (`FileNotFoundError`/`ModuleNotFoundError`). → Rollback: Schritt 5 vollständig nachziehen (alle 7 zusammen); Verify-Zähler `wc -l = 7` fängt das vor dem Diff-Gate ab.
- **R2 — `REPO_ROOT`/lib-Tiefe falsch berechnet** (zu wenige/zu viele `.parent`) → `from vault_root import …` schlägt schon beim Import fehl. → Rollback: Tiefe gegen Präzedenz `doc-pipeline/scripts/convert-doc.py:37` (`parent×4`) und `REPO_ROOT = parent×3` abgleichen; Import-Smoke (Schritt 6-verify) ist der Fangnetz-Check.
- **R3 — Diff NICHT leer** (Schritt 11) → Verhaltensänderung eingeschleppt (z. B. versehentlich Logik statt nur Pfad editiert, oder Fixture zwischen PRE/POST verändert). → Rollback: **kein** Nachbessern am Output; `git restore`/`git checkout` auf die editierten Files, Ursache isolieren (nur die 4 zulässigen Pfad-Edits + Ref-Updates dürfen abweichen), Baseline mit identischem Fixture neu ziehen. Notfalls `git revert` des Move-Commits (stellt flache `scripts/`-Ablage + alte Pfade in einem Schritt her, Spec §8 Backout).
- **R4 — `git mv` als delete+add statt rename** (History-Verlust) → Rollback: `git reset` und erneut mit `git mv` (nicht `mv`+`git add`); `git status`-„renamed:"-Check (Schritt 5-verify) verifiziert.
- **R5 — Baseline gegen Live-`wiki/` statt fixem Fixture** → nicht-reproduzierbarer Diff (Live-Drift). → Rollback: ausschließlich das materialisierte tmp-Fixture aus Schritt 2 für PRE und POST verwenden; nie den echten Vault.
- **R6 — Falsche Broken-Ref korrigiert** (z. B. `lint-open-issues.py` fälschlich auf lint-Location gezeigt) → out-of-scope-Bruch. → Rollback: nur die 4 autoresearch-`lint-deps`-Refs anfassen; `lint-open-issues.py`-Refs (fix-issues.md/handoff.md) explizit unberührt lassen; Schritt 9-Sweep schließt `commands/` nicht ein, daher kein False-Positive-Druck dorthin.
- **R7 — Test-Docstring-Kosmetik triggert Diff/Erwartungen** → unwahrscheinlich (nur Kommentare), aber: Docstring-Edits sind rein kosmetisch und dürfen keine Assertion berühren. → Rollback: Docstrings zurücksetzen, wenn ein Test darauf prüft (tut keiner — verifiziert: Treffer nur in Zeile 2/Kommentaren).

## Human-Gates  ‹Wann: Freigabe›

- [ ] **Gate 0 — Clean-Repo/Branch:** dedizierter Feature-Branch, lint-relevanter Worktree clean, bevor Schritt 4 (Move) startet. (CLAUDE.md: „Work only in a clean git repo on the intended branch".)
- [ ] **Gate 1 — Baseline erfasst:** `lint-pre.json` + `lint-pre.md` liegen vor und sind plausibel (9 Checks, Exit 0), **bevor** irgendeine Datei bewegt wird (Schritt 3 → 4).
- [ ] **Gate 2 — Diff-leer vor Commit:** JSON-`diff` leer + Report-`diff` nur Datum, **bevor** committet/gemerged wird (Schritt 11 → 15). Rot ⇒ Rollback, kein Nachbessern.
- [ ] **Gate 3 — Push/PR:** Commit steht; Push/PR-Erstellung erst nach ausdrücklicher Nutzerfreigabe (CLAUDE.md: „ask before any push").

---
### Checkliste
- [x] Done-Definition konkret  ‹Wann-erledigt›  (an AC1–AC8 + Quality-Gate gebunden, je mit Kommando/Diff)
- [x] Jeder Schritt hat einen Verify-Check  ‹Wie›  (15/15 Schritte mit konkretem Check)
- [x] Riskante Schritte haben Rollback  (R1–R7, inkl. `git revert`-Backout)
- [x] Human-Gates markiert  ‹Wann›  (Gate 0–3: Branch · Baseline-vor-Move · Diff-vor-Commit · Push)
- [x] Schritte atomar genug → werden zu Tasks  (je 1 Aktion + 1 Verify; Move+Fixes bewusst als 1 Commit gekoppelt)
- [x] 7-W-Abdeckung geprüft  (Wie/Wann/Womit/Wann-erledigt im Kopf + je Sektion)
- [x] Broken-Subdir-Refs adressiert  (In-Scope: autoresearch `lint-deps`; Out-of-Scope: `lint-open-issues` nur notiert)
- [x] Baseline-Strategie fixiert  (deterministischer `_seed_base_vault`-Fixture in festem tmp, identisch für PRE/POST)
- [ ] **Offen (aus Spec übernommen):** exakte Fixierung des Fixture-Seeders (`_seed_base_vault`) beim Ausführen bestätigen; `[should]`-`resolve_vault`-Dedup bleibt default weggelassen (reiner Move).
