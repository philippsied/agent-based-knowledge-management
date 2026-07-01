---
artifact: plan
slug: cmd-script-consolidation-dragonscale
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [spec-dragonscale, test-design]
---

# Plan — dragonscale-Cluster splitten + geteilte Util nach `lib/` [dragonscale]

> Beantwortet: WELCHE Schritte, in welcher Folge, WIE verifiziert?
> Wegwerf-Artefakt: nach Done erledigt.
> **Anker (7 W):** Wie (primär: Schritte) · Wann (Reihenfolge) · Womit (Deps/Tools) · Wann-erledigt (Done-Definition)
> **Verträge:** [Spec](../specs/SPEC-cmd-script-consolidation-dragonscale.md) · [Test-Design](../test-designs/cmd-script-consolidation.md) · [ADR-0002](../adr/0002-colocate-scripts-under-skill.md)

## Ziel & Done-Definition  ‹Wann-erledigt›

Der DragonScale-Cluster (`boundary-score.py`, `tiling-check.py`, `allocate-address.py`) ist auf seine
drei besitzenden Skills verteilt, geteilter byte-identischer Code liegt in `lib/dragonscale_pages.py`,
**alle** Aufrufer-Referenzen zeigen auf die neuen Pfade — bei **null Verhaltensänderung** (reiner Refactor).

Done, wenn **alle** Spec-AC-1…10 erfüllt sind, konkret:
- `boundary-score.py` → `skills/autoresearch/scripts/`, `tiling-check.py` → `skills/wiki-lint/scripts/`,
  `allocate-address.py` → `skills/wiki-ingest/scripts/`; alte `scripts/`-Pfade existieren nicht mehr (AC-1/2/3).
- `lib/dragonscale_pages.py` enthält die byte-identisch geteilten Symbole; `boundary-score` + `tiling-check`
  importieren daraus, kein Duplikat der extrahierten Symbole inline (AC-4).
- `sys.path`-Tiefe je verschobenem Skript korrigiert (`parent.parent` → `parent.parent.parent`); Start ohne
  `ImportError` (AC-6).
- Alle §2.3-Referenzen aktualisiert (AC-5); `rg 'scripts/(boundary-score|tiling-check|allocate-address)\.py'`
  = **0** Treffer außer `wiki/meta/**`, `CHANGELOG.md`, `__pycache__` (AC-7).
- `make test` grün (`test_boundary_score`, `test_tiling_check`, `test_allocate_address` + Rest); autoresearch-Eval
  grün; `run-lint --json` pre/post gegen Fixture-Vault diff-leer (AC-8/9).
- `tiling-check` Exit-Codes 10/11 weiterhin als Skip behandelt (AC-10).

## Schritte  ‹Wie›

> Reihenfolge = Spec §4 (Extraktion → Move → Ref → Regression). **Jeder Schritt einzeln grün + eigener Commit.**
> Baseline zuerst festhalten, damit „diff-leer" später beweisbar ist.

### Phase 0 — Baseline & Vorbedingungen

1. **Sauberer Start + Cross-Plan-Vorbedingung prüfen.** `git status` clean auf `main` (bzw. Arbeitsbranch);
   Manifest-Status von `tasks-lint` und `tasks-ingest` = `done` verifizieren (dieser Plan läuft NACH beiden,
   s. Abhängigkeiten).
   → verify: `git status --porcelain` leer; `python3 -c "import json;d=json.load(open('docs/manifests/cmd-script-consolidation.json'));print({a['id']:a['status'] for a in d['artifacts'] if a['id'] in ('tasks-lint','tasks-ingest')})"` zeigt beide `done`.

2. **Grün-Baseline + Verhaltens-Baseline aufnehmen.** `make test` einmal grün laufen lassen; `run-lint --json`
   gegen den Fixture-Vault erzeugen und als Referenz speichern (`baseline-runlint.json`).
   → verify: `make test` exit 0; `python3 scripts/run-lint.py --json > /tmp/baseline-runlint.json` erzeugt Datei ohne Fehler.

### Phase 1 — `lib/dragonscale_pages.py` extrahieren (VOR dem Move — Extraktion isoliert testen)

3. **[MUST] Byte-identische Symbole nach `lib/dragonscale_pages.py` extrahieren.** Neues Modul mit den in
   Spec §2.2 als byte-identisch belegten Symbolen anlegen: Konstanten `EXCLUDE_TYPES`, `EXCLUDE_FILENAMES`,
   `EXCLUDE_PATH_PREFIXES`, `FRONTMATTER_RE`, `TYPE_RE` und `log(msg: str) -> None`. Vor dem Verschieben der
   Bytes einen Byte-Vergleich zwischen `boundary-score.py` und `tiling-check.py` fahren, um die Identität zu
   bestätigen (nicht annehmen).
   → verify: `python3 - <<'PY'`-Skript vergleicht die zu extrahierenden Blöcke beider Quelldateien und meldet
     `IDENTICAL`; Import-Smoke `python3 -c "import sys; sys.path.insert(0,'lib'); import dragonscale_pages as d; d.log('x'); print(d.EXCLUDE_TYPES, d.TYPE_RE.pattern)"` läuft.

4. **[MUST] `boundary-score` + `tiling-check` auf Import umstellen (Symbole inline entfernen).** In beiden
   Skripten die extrahierten Konstanten + `log` durch `from dragonscale_pages import (...)` ersetzen; die
   inline-Definitionen der extrahierten Symbole löschen (nur diese — keine anderen). `sys.path`-Insert bleibt
   in diesem Schritt UNVERÄNDERT (Skripte liegen noch in `scripts/`, `parent.parent/lib` ist hier noch korrekt).
   → verify: `rg -n 'EXCLUDE_TYPES\s*=|def log\(' scripts/boundary-score.py scripts/tiling-check.py` findet
     **0** Inline-Definitionen der extrahierten Symbole; `python3 tests/test_boundary_score.py` **und**
     `python3 tests/test_tiling_check.py` grün — **beide Suiten VOR dem Move** (Extraktion vom Move getrennt verifiziert).

5. **[SHOULD, guarded] Superset-API `parse_frontmatter`/`included` extrahieren — nur wenn beide Suiten grün bleiben.**
   `parse_frontmatter(text, keys=...)` (parst alle Felder; jeder Aufrufer liest weiter nur seine Keys) und
   `included(path, vault_root)` (bedient **beide** Rückgabeformen bool/tuple UND erhält strict-vs-non-strict
   `resolve`-Semantik je Aufrufer) nach `lib/dragonscale_pages.py` heben; beide Skripte darauf umstellen.
   **Guard/Abbruch:** bringt der Merge in `test_boundary_score` ODER `test_tiling_check` auch nur **eine**
   Abweichung, wird dieser Schritt **komplett revertiert** und `parse_frontmatter`/`included` bleiben per-Skript
   (Duplikat akzeptiert — reiner Refactor > DRY, Spec §2.2 SHOULD, §3 Fehlerbehandlung). Der Ausgang wird in
   AC-4 dokumentiert („Superset extrahiert" ODER „per-Skript belassen, weil Suite X regredierte").
   → verify: `python3 tests/test_boundary_score.py` **und** `python3 tests/test_tiling_check.py` grün NACH der
     Umstellung. Bei rot: `git checkout -- scripts/boundary-score.py scripts/tiling-check.py lib/dragonscale_pages.py`
     auf den Stand nach Schritt 4, dann beide Suiten erneut grün (Fallback bestätigt).

### Phase 2 — Move + `sys.path`-Tiefe korrigieren

6. **`boundary-score.py` → `skills/autoresearch/scripts/` (git mv) + `sys.path`-Tiefe fixen.** `mkdir -p`
   Zielordner falls nötig; `git mv scripts/boundary-score.py skills/autoresearch/scripts/boundary-score.py`;
   die `sys.path.insert`-Zeile von `parent.parent / "lib"` auf `parent.parent.parent / "lib"` ändern
   (neuer Pfad ist eine Ebene tiefer → `lib/` liegt drei statt zwei Ebenen höher).
   → verify: `python3 skills/autoresearch/scripts/boundary-score.py --json --top 1` startet **ohne**
     `ImportError` (findet `dragonscale_pages` + `vault_root`); alter Pfad weg: `test ! -e scripts/boundary-score.py`.

7. **`tiling-check.py` → `skills/wiki-lint/scripts/` (git mv) + `sys.path`-Tiefe fixen.** Zielordner ist
   **geteilt mit dem lint-Cluster** (plan-lint legt dort `run-lint`/`lint-*` ab) — vor `git mv` prüfen, dass
   der Ordner existiert (von tasks-lint erzeugt) und **keine** Namenskollision besteht (`tiling-check.py` ≠
   `lint-*.py`, ≠ `run-lint.py`). `sys.path`-Zeile analog auf `parent.parent.parent / "lib"`.
   → verify: `test -d skills/wiki-lint/scripts && test ! -e skills/wiki-lint/scripts/tiling-check.py` (Ordner da,
     Datei noch nicht) **vor** dem mv; danach `python3 skills/wiki-lint/scripts/tiling-check.py --peek` startet
     ohne `ImportError` und liefert einen der definierten Exit-Codes (0/2/3/4/10/11, nicht ImportError-Traceback);
     `test ! -e scripts/tiling-check.py`.

8. **`allocate-address.py` → `skills/wiki-ingest/scripts/` (git mv) + `sys.path`-Tiefe fixen.**
   `git mv scripts/allocate-address.py skills/wiki-ingest/scripts/allocate-address.py`; `sys.path`-Zeile analog
   auf `parent.parent.parent / "lib"`.
   → verify: `python3 skills/wiki-ingest/scripts/allocate-address.py --peek` startet ohne `ImportError` und gibt
     den Zählerwert aus (read-only, mutiert nichts); `test ! -e scripts/allocate-address.py`.

### Phase 3 — Referenzen aktualisieren (Spec §2.3, vollständig)

> Nach jedem Update-Block eine gezielte `rg`-Kontrolle. Alte Pfade dürfen NUR in den bewusst
> ausgeschlossenen Dateien (`wiki/meta/**`, `CHANGELOG.md`, `__pycache__`) überleben.

9. **`boundary-score`-Konsumenten → `skills/autoresearch/scripts/boundary-score.py`.** Aktualisieren:
   `skills/autoresearch/SKILL.md` (Feature-Gate `[ -x ./scripts/boundary-score.py ]` Zeile 112 + Aufruf
   `./scripts/boundary-score.py --json --top 5` Zeile 121); `Makefile` (`test-boundary`-Header-Kommentar Zeile 15,
   ggf. Zielbody); `tests/test_boundary_score.py` (`HELPER = ROOT / "scripts" / "boundary-score.py"` Zeile 20 +
   Docstring Zeile 2); `docs/dragonscale-guide.md`; `docs/releases/v1.6.0.md`.
   **Nicht anfassen:** die `scripts/lint/lint-deps.py`-Zeilen (46/60/61/262) in derselben SKILL.md — die gehören
   zum **lint**-Cluster (plan-lint), nicht zu boundary-score (s. Abhängigkeiten, Broken-Subdir-Klasse).
   → verify: `rg -n 'scripts/boundary-score\.py' --glob '!wiki/meta/**' --glob '!CHANGELOG.md' .` = **0** Treffer;
     `python3 tests/test_boundary_score.py` grün.

10. **`tiling-check`-Konsumenten → `skills/wiki-lint/scripts/tiling-check.py`.** Aktualisieren:
    `skills/wiki-lint/SKILL.md` (Zeilen 277/278/287/291/300/309/371 — `--peek`/`--report`-Aufrufe + Fehlermeldungstexte);
    `agents/wiki-lint.md` (Zeilen 38/46 — Feature-Gate + Delegation, Exit-Codes 0/2/3/4/10/11 **wortgleich** erhalten);
    `bin/setup-dragonscale.py` (Copy-Liste Zeile 37, `os.chmod` Zeile 46); `Makefile` (`test-tiling`-Kommentar Zeile 14);
    `tests/test_tiling_check.py` (`HELPER` Zeile 21 + Docstring Zeile 2); `docs/dragonscale-guide.md`;
    `docs/plans/PLAN-sh-to-py-full-migration.md`; `docs/upstream-roadmap.md`; `docs/releases/v1.6.0.md`.
    → verify: `rg -n 'scripts/tiling-check\.py' --glob '!wiki/meta/**' --glob '!CHANGELOG.md' .` = **0** Treffer;
      `python3 tests/test_tiling_check.py` grün; `rg -n '10/11' agents/wiki-lint.md` bestätigt Exit-Code-Handling unverändert.

11. **`allocate-address`-Konsumenten → `skills/wiki-ingest/scripts/allocate-address.py`.** Aktualisieren:
    `skills/wiki-ingest/SKILL.md` (Feature-Gate + `ADDR=$(python3 scripts/allocate-address.py)` + „Before writing…");
    `skills/wiki-lint/SKILL.md` (`--peek`-Konsument read-only: Zeilen 193/227/252/260/261);
    `agents/wiki-ingest.md` (Zeilen 42/44/56); `agents/wiki-lint.md` (Zeile 37/45 — `--peek`-Konsument);
    `bin/setup-dragonscale.py` (Copy-Liste Zeile 36, `os.chmod` Zeile 45, `--peek`-Smoke-Test Zeile 118);
    `Makefile` (`test-address`-Kommentar Zeile 13); `tests/test_allocate_address.py` (`ALLOCATOR` Zeile 25 +
    Docstring Zeile 4); `docs/dragonscale-guide.md`; `docs/plans/PLAN-sh-to-py-full-migration.md`;
    `docs/releases/v1.6.0.md`.
    **Read-only-Invariante:** der `--peek`-Aufruf aus `wiki-lint` bleibt read-only (kein `--rebuild`/Schreiben
    aus dem lint-Pfad) — nur Pfad ändert sich (Spec §2.1).
    → verify: `rg -n 'scripts/allocate-address\.py' --glob '!wiki/meta/**' --glob '!CHANGELOG.md' .` = **0** Treffer;
      `python3 tests/test_allocate_address.py` grün; `python3 bin/setup-dragonscale.py`-Smoke gegen tmp-Vault findet
      den Allocator am neuen Pfad (kein „No such file").

### Phase 4 — Gesamt-Regression (Quality-Gate)

12. **Vollständiger `rg`-Sweep (AC-7).** Alle drei Skriptnamen zugleich prüfen.
    → verify: `rg 'scripts/(boundary-score|tiling-check|allocate-address)\.py' --glob '!wiki/meta/**' --glob '!CHANGELOG.md' --glob '!**/__pycache__/**' .` = **0** Treffer.

13. **`make test` gesamt (AC-8).** Alle 10 Test-Dateien grün, insbesondere `test_boundary_score`,
    `test_tiling_check`, `test_allocate_address` (mit mitgezogenen `HELPER`/`ALLOCATOR`/`importlib`-Pfaden).
    → verify: `make test` exit 0; Quality-Gate: 100 % pass.

14. **Verhaltens-Gleichheit + Eval (AC-9/10).** `run-lint --json` erneut gegen Fixture-Vault und mit Baseline
    (Schritt 2) diffen; autoresearch-Eval laufen; `tiling-check`-Skip-Verhalten ohne ollama prüfen (Exit 10/11 →
    wird als Skip behandelt, kein harter Bruch).
    → verify: `diff <(python3 scripts/run-lint.py --json) /tmp/baseline-runlint.json` **leer**; autoresearch-Eval
      exit 0; ohne laufendes ollama liefert `python3 skills/wiki-lint/scripts/tiling-check.py --peek` Exit 10 oder 11
      und `wiki-lint` behandelt es als Skip (nicht als Fehler).

## Abhängigkeiten / Reihenfolge  ‹Wann / Womit›

- **Interne Reihenfolge:** strikt Phase 0 → 1 → 2 → 3 → 4 (Spec §4: Extraktion **vor** Move, Move **vor**
  Ref-Update, Ref-Update **vor** Gesamt-Regression). Innerhalb Phase 1 gilt: Schritt 5 (Superset-SHOULD) nur
  nach grünem Schritt 4 (MUST); bei Regression Revert auf Stand nach Schritt 4.
- **Cross-Plan (harte Vorbedingung — vom Manifest kodiert):** Diese Arbeit läuft **NACH plan-lint UND
  plan-ingest**. Das Manifest kodiert exakt `tasks-dragonscale → depends_on: ["plan-dragonscale",
  "tasks-lint", "tasks-ingest"]`. Gründe:
  1. **Geteiltes Zielverzeichnis** `skills/wiki-lint/scripts/`: `tiling-check.py` (dieser Plan) und die
     `run-lint`/`lint-*`-Skripte (plan-lint) landen im **selben** Ordner. tasks-lint erzeugt/besitzt diesen
     Ordner; dieser Plan legt `tiling-check.py` **dazu** (keine Kollision: `tiling-check.py` ≠ `lint-*.py`).
  2. **Broken-Subdir-Ref-Klasse:** `skills/autoresearch/SKILL.md` referenziert `scripts/lint/lint-deps.py`
     (nicht-existentes Subdir, Zeilen 46/60/61/262). Diese Referenzen gehören **plan-lint** (lint-Cluster),
     nicht diesem Plan — dieser Plan fasst sie NICHT an (Schritt 9 „Nicht anfassen"). Nach plan-lint zeigen
     sie auf den korrekten neuen lint-Ort; dieser Plan stellt nur sicher, dass die **boundary-score**-Refs
     in derselben Datei (Zeilen 112/121, sauber root-relativ) auf `skills/autoresearch/scripts/` gezogen werden.
- **Tooling/Womit:** `git mv` (Historie erhalten) · `rg` (Ref-Sweeps) · `make test` (10 Test-Dateien) ·
  autoresearch-Eval · Fixture-Vault für `run-lint --json` · Python-Byte-Vergleich für Extraktions-Identität.
- **`lib/`-Auflösung (Womit, load-bearing):** alle drei Skripte müssen nach dem Move `lib/dragonscale_pages.py`
  UND `lib/vault_root.py` auflösen → `sys.path`-Insert von `parent.parent` auf `parent.parent.parent`
  (Repo-Wurzel-relativ). Falsch = `ImportError` beim Start (von Tests gefangen, AC-6).

## Risiken & Rollback

- **Superset-Merge (`parse_frontmatter`/`included`) verschiebt Verhalten** (divergente Bodies/Signaturen,
  strict-vs-non-strict `resolve`, Symlink-/Escape-Behandlung) → **Rollback:** Schritt 5 komplett revertieren
  (`git checkout -- scripts/boundary-score.py scripts/tiling-check.py lib/dragonscale_pages.py` auf Stand nach
  Schritt 4), `parse_frontmatter`/`included` **per-Skript belassen** (Spec §2.2 SHOULD-Guard). Duplikat wird
  bewusst akzeptiert; in AC-4 dokumentieren.
- **`sys.path`-Tiefe nach Move nicht angepasst** → `ImportError` beim Start. **Rollback:** Zeile auf
  `parent.parent.parent / "lib"` korrigieren; von Import-Smoke (Schritte 6/7/8) + Tests (AC-6) sofort gefangen.
- **Vergessene Referenz** (Aufrufer zeigt weiter auf `scripts/<name>.py`) → Feature-Gate `[ -x/-f … ]` schlägt
  fehl, der optionale DragonScale-Pfad **verstummt still** (no-op). Gefährlich: stiller No-op = *bestandener*
  Test, aber *kaputtes* Feature. **Mitigation/Rollback:** `rg`-Sweep (Schritt 12, AC-7) muss **0** ergeben;
  bei Resttreffer Referenz nachziehen, bevor Done erklärt wird.
- **Namenskollision im geteilten Ordner** `skills/wiki-lint/scripts/` (falls plan-lint noch nicht fertig oder
  gleichnamige Datei) → **Rollback:** `git mv` zurück; Cross-Plan-Vorbedingung (tasks-lint done) in Schritt 1
  erneut prüfen, erst dann Schritt 7.
- **`tiling-check` Exit-Code-Semantik (10/11) versehentlich geändert** beim Ref-Update in agents/SKILL.md →
  **Rollback:** Diff der geänderten Zeilen prüfen, Exit-Code-Handling wortgleich wiederherstellen; AC-10-Verify
  (Skip ohne ollama) muss halten.
- **Gesamter Vorgang** (struktur-/pfad-bezogen, keine Datenmigration) → **Backout:** `git revert` der
  Move-/Extraktions-/Ref-Commits stellt flache `scripts/`-Pfade + inline-Util vollständig wieder her, ohne
  Restzustand (keine Vault-/`.vault-meta/`-Änderung — Spec §8).

## Human-Gates  ‹Wann: Freigabe›

- [ ] **Gate A — Vor Start:** Bestätigen, dass `tasks-lint` UND `tasks-ingest` `done` sind (Cross-Plan-Reihenfolge)
      und der Arbeitsbranch clean ist. Ohne diese Freigabe nicht mit Phase 1 beginnen.
- [ ] **Gate B — Superset-Entscheidung (nach Schritt 4, vor/ nach Schritt 5):** Freigabe, ob der SHOULD-Superset
      (`parse_frontmatter`/`included`) versucht wird; bei Regression Freigabe des Fallbacks „per-Skript belassen".
- [ ] **Gate C — Vor Merge/Done:** Review, dass AC-7 (`rg` = 0), AC-8 (`make test` grün), AC-9 (`run-lint --json`
      diff-leer) und AC-10 (Exit 10/11 = Skip) alle erfüllt sind — insbesondere kein stiller No-op durch
      vergessene Referenz.

---
### Checkliste
- [x] Done-Definition konkret  ‹Wann-erledigt›  (an AC-1…10 gebunden, mit Verify-Kommandos)
- [x] Jeder Schritt hat einen Verify-Check  ‹Wie›  (jeder der 14 Schritte)
- [x] Riskante Schritte haben Rollback  (Superset-Guard, sys.path, vergessene Ref, Kollision, Exit-Codes, Gesamt-Backout)
- [x] Human-Gates markiert  ‹Wann›  (Gate A Vorbedingung · Gate B Superset · Gate C Done)
- [x] Schritte atomar genug → werden zu Tasks  (14 atomare Schritte, je 1 Commit)
- [x] 7-W-Abdeckung geprüft  (Wie=Schritte · Wann=Reihenfolge/Phasen · Womit=Deps/Tools · Wann-erledigt=Done)
- [x] Cross-Plan-Ordering explizit  (Manifest `tasks-dragonscale → tasks-lint + tasks-ingest`; Broken-Subdir-Klasse koordiniert mit plan-lint)
