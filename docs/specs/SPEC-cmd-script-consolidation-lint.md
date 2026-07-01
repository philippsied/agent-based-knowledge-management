---
artifact: spec
slug: cmd-script-consolidation
module: lint
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [prd, adr-0002]
---

# Spec — lint-Cluster konsolidieren + co-locate [lint]

> WIE konsolidieren + verschieben wir den lint-Cluster unter `skills/wiki-lint/scripts/` ohne Verhaltensänderung?
> **Anker (7 W):** Wie · Womit · [PRD](../prds/cmd-script-consolidation.md) · [ADR-0002](../adr/0002-colocate-scripts-under-skill.md)

## 1. Ziel & Kontext  ‹Was/Warum → PRD›

lint-Cluster (7 Dateien, ~1421 LOC) flach in `scripts/` → co-located unter `skills/wiki-lint/scripts/` gemäß [ADR-0002](../adr/0002-colocate-scripts-under-skill.md) (Skripte unter besitzendem Skill; shared → `lib/`). `run-lint.py` bleibt In-Process-Aggregator; `lib/vault_root.py` bleibt shared und wird NICHT verschoben.

**Cluster (verifiziert, LOC):** `run-lint.py`(684) · `lint-orphans.py`(129) · `lint-terminology.py`(269) · `lint-title-overlap.py`(118) · `lint-deps.py`(265) · `lint-programs.py`(237) · `lint-rename.py`(119). Ziel-Skill besitzt die Checks fachlich bereits (`skills/wiki-lint/SKILL.md`).

**Reiner Refactor:** Byte-identischer lint-Output (`run-lint.py --json` und Markdown-Report). KEINE Logik-, Schema- oder Severity-Änderung. Erfüllt PRD-`[must]` „Gekoppelte Skripte co-located" + „Alle internen Pfad-Referenzen aktualisiert" + „Import-Pfad-Änderungen (importlib) mitgezogen".

## 2. Schnittstellen / Verträge  ‹Womit›

### 2.1 Aggregator-Vertrag (`run-lint.py`)

- **Pfadauflösung (verifiziert, `run-lint.py:50-54`):**
  ```python
  SCRIPT_DIR = Path(__file__).resolve().parent
  REPO_ROOT  = SCRIPT_DIR.parent            # ← ändert sich semantisch nach Move
  sys.path.insert(0, str(REPO_ROOT / "lib"))
  from vault_root import resolve_vault_root
  ```
  Nach Move liegt `run-lint.py` unter `skills/wiki-lint/scripts/`; `SCRIPT_DIR.parent` zeigt dann auf `skills/wiki-lint/`, NICHT mehr auf Repo-Root. **`REPO_ROOT`-Berechnung muss 3 Ebenen hoch:** `SCRIPT_DIR.parent.parent.parent`, damit `REPO_ROOT / "lib"` weiterhin `<repo>/lib` trifft.
- **In-Process-Import der Sub-Linter (verifiziert, `run-lint.py:56-77`):** `_load_lint_module(stem)` baut `path = SCRIPT_DIR / f"{stem}.py"` und lädt via `importlib.util.spec_from_file_location(stem.replace("-", "_"), path)`, registriert `sys.modules[spec.name]` VOR `exec_module` (nötig, damit `@dataclass` in `lint-terminology` `sys.modules[cls.__module__]` bei Klassen-Erzeugung auflösen kann, Python 3.12+). Beim Modul-Import geladen:
  ```python
  _lint_orphans       = _load_lint_module("lint-orphans")
  _lint_terminology   = _load_lint_module("lint-terminology")
  _lint_title_overlap = _load_lint_module("lint-title-overlap")
  _lint_deps          = _load_lint_module("lint-deps")
  _lint_programs      = _load_lint_module("lint-programs")
  ```
  **`SCRIPT_DIR`-relativ ⇒ übersteht den Move automatisch** (alle 5 Sub-Linter wandern in denselben Ordner mit). `lint-rename.py` wird NICHT aggregiert (standalone Remediation, nur CLI).

### 2.2 `collect*`-Entrypoints (verifiziert — Signaturen bleiben unverändert)

| Sub-Linter | Entrypoint | Signatur | Aggregator-Wrapper | Rückgabe |
|---|---|---|---|---|
| `lint-orphans.py:98` | `collect` | `collect(wiki_root: Path) -> list[str]` | `run_orphans` (`run-lint.py:302`) | Liste Orphan-Pfade |
| `lint-terminology.py:237` | `collect_findings` | `collect_findings(wiki_root: Path) -> list[dict]` | `run_terminology` (`run-lint.py:315`) | Findings (ERROR/WARN) |
| `lint-title-overlap.py:92` | `collect_lines` | `collect_lines(wiki_root: Path, threshold: float = 0.55) -> str` | `run_title_overlap` (`run-lint.py:337`) | stdout-Text (byte-identisch zur CLI) |
| `lint-deps.py:181` | `collect` | `collect(vault_root: Path) -> dict` | `run_dag` (`run-lint.py:355`) | `analyze(...)`-dict (u.a. `ready_set`) |
| `lint-programs.py:150` | `collect` | `collect(vault_root: Path) -> dict` | `run_programs` (`run-lint.py:382`) | `analyze(...)`-dict |

> **Argument-Typ beachten:** `run_orphans/terminology/title_overlap` übergeben `wiki_root`; `run_dag/programs` übergeben `vault_root`. Rein Python-interne Funktionsaufrufe (keine Dateipfade) → vom Move UNBERÜHRT.

### 2.3 Shared-lib-Import in den Sub-Lintern (verifiziert — der eigentliche Bruchpunkt)

- **`lint-orphans/terminology/title-overlap`** (`:29-30` / `:37-38` / `:30-31`), identisches Muster:
  ```python
  sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
  from vault_root import resolve_wiki_root
  ```
  `parent.parent` = 2 Ebenen hoch = aktuell `<repo>/lib`. **Nach Move (`skills/wiki-lint/scripts/`) auf 4 Ebenen hoch:** `parent.parent.parent.parent / "lib"` (Präzedenz verifiziert: `skills/doc-pipeline/scripts/convert-doc.py:37`).
- **`lint-deps/programs/rename`** — importieren `lib/vault_root.py` NICHT; sie haben lokale `resolve_vault(cli_arg)` (`lint-deps.py:38`, `lint-programs.py:47`, `lint-rename.py:24`) mit Order `--vault → KM_VAULT_PATH → CWD`. **Kein `sys.path`/lib-Bezug ⇒ vom Move unberührt** (kein Pfad-Edit nötig).

### 2.4 Test-Ladepfade (verifiziert — müssen mit-verschoben werden)

- `tests/test_run_lint.py:30-31`: `ROOT = …parent.parent` (bleibt Repo-Root), `HELPER = ROOT / "scripts" / "run-lint.py"` → **`ROOT / "skills" / "wiki-lint" / "scripts" / "run-lint.py"`**. Whitebox-Import `spec_from_file_location("run_lint", HELPER)` (`:34`) folgt automatisch. Exec-Bit-Gates auf `ROOT/"scripts"/"lint-terminology.py"` (`:381,405,435`) analog anpassen.
- `tests/test_lint_orphans.py:20` `SCRIPT = REPO / "scripts" / "lint-orphans.py"`; `tests/test_lint_terminology.py:18`; `tests/test_lint_title_overlap.py:17` — je `…/ "scripts" / "lint-*.py"` → Skill-Pfad.

### 2.5 JSON-Schema (Contract, MUSS byte-identisch bleiben; verifiziert `run-lint.py:493-498`)

Top-Level-Keys: `date · vault_root · wiki_root · pages_scanned · checks[] · totals`. Jeder `checks[]`-Eintrag: `{name, severity, count, items}` (items auf 30 gekappt). Check-Namen (Reihenfolge fix): `spaced_filenames · spaced_wikilinks_body · orphans · dead_link_targets · frontmatter_gaps · terminology · title_overlap · research_queue_dag · research_program_codes`.

## 3. Verhalten  ‹Wie›

### Happy path — `run-lint --json` identisch pre/post

Gegeben ein Fixture-Vault; `run-lint.py --json` wird VOR und NACH dem Move gegen denselben Vault ausgeführt (via `KM_VAULT_PATH`). Die serialisierte JSON-Ausgabe ist byte-identisch (gleiche Keys, Reihenfolge, `count`, `severity`, `items`, `totals`). Ebenso der Markdown-Report `<vault>/wiki/meta/lint-report-YYYY-MM-DD.md`. Read-only-Garantie (kein Schreiben in `wiki/`-Content) bleibt. Exit-Code `0` (Findings via JSON, nicht via Exit-Code).

### Edge-Cases — hyphenierte Dateinamen bleiben nicht-importierbar → importlib-Pfad muss neuen Ordner treffen

`lint-orphans.py` etc. sind keine gültigen Python-Import-Identifier (Bindestrich). Sie werden ausschließlich via `spec_from_file_location(...SCRIPT_DIR / f"{stem}.py")` geladen. Da `SCRIPT_DIR` self-relativ ist, trifft der Loader nach dem Move automatisch `skills/wiki-lint/scripts/lint-*.py` — **vorausgesetzt Aggregator + alle 5 aggregierten Sub-Linter wandern gemeinsam in genau diesen Ordner**. Bleibt ein Sub-Linter zurück, bricht der Import. `lint-rename.py` wird nie via importlib geladen (nur CLI), muss aber für Cluster-Kohäsion + Referenz-Konsistenz mit-umziehen.

### Fehlerbehandlung — fehlender Vault-Root

Verhalten unverändert: `resolve_vault_root`/`resolve_wiki_root` (`lib/vault_root.py`) bzw. lokale `resolve_vault` lösen `KM_VAULT_PATH → argv/--vault → CWD` auf; existiert das Ziel nicht als Verzeichnis, Exit `2` (usage/resolver-Fehler) mit stderr-Meldung. Der Move darf diese Auflösung nicht verändern — deshalb ist die `REPO_ROOT`/`parent`-Tiefenkorrektur (§2.1, §2.3) verpflichtend: ein falsch berechneter `lib`-Pfad ließe `from vault_root import …` bereits beim Modul-Import mit `ModuleNotFoundError` fehlschlagen (nicht erst zur Laufzeit).

## 4. Gewählter Ansatz  ‹Wie›

Move + Pfad-Update, minimal-invasiv (Surgical-Changes). Reihenfolge:

1. **Verzeichnis anlegen:** `skills/wiki-lint/scripts/` (existiert noch nicht; unter `skills/wiki-lint/` liegt bisher nur `SKILL.md`).
2. **7 Dateien verschieben** (`git mv`, History erhalten): `run-lint.py`, `lint-orphans.py`, `lint-terminology.py`, `lint-title-overlap.py`, `lint-deps.py`, `lint-programs.py`, `lint-rename.py` → `skills/wiki-lint/scripts/`.
3. **`run-lint.py` `REPO_ROOT` korrigieren** (`:51`): `REPO_ROOT = SCRIPT_DIR.parent.parent.parent`, sodass `REPO_ROOT / "lib"` = `<repo>/lib`. `_load_lint_module` (SCRIPT_DIR-relativ) bleibt unverändert.
4. **lib-Pfad-Tiefe in 3 Sub-Lintern anpassen** (`lint-orphans.py:29`, `lint-terminology.py:37`, `lint-title-overlap.py:30`): `parent.parent` → `parent.parent.parent.parent` (Präzedenz `doc-pipeline`). `lint-deps/programs/rename` unverändert (kein lib-Import).
5. **Test-Pfadkonstanten aktualisieren:** `tests/test_run_lint.py:31` (+ `:381,405,435`), `tests/test_lint_orphans.py:20`, `tests/test_lint_terminology.py:18`, `tests/test_lint_title_overlap.py:17` → `skills/wiki-lint/scripts/…`. `ROOT`/`REPO` (Repo-Root-Berechnung) bleiben.
6. **Operative Referenzen aktualisieren** (§5 Liste): `Makefile` (5 Zeilen), `skills/wiki-lint/SKILL.md` (7 Zeilen), `bin/release.py:49`, `evals/run.py:68`, Test-Docstrings (kosmetisch).
7. **Verifizieren:** `run-lint.py --json`-Diff leer (pre/post, Fixture-Vault) · `python3 tests/test_run_lint.py` + `test_lint_*` grün · evals grün.

**[should] (optional, im selben PR erlaubt):** Innerhalb des Clusters die dreifach duplizierte `resolve_vault(cli_arg)` in `lint-deps/programs/rename` gegen `lib/vault_root.py` konsolidieren (DRY, PRD-`[should]` „Duplikat-Logik konsolidieren"). NUR falls byte-identischer Output beweisbar bleibt — sonst separat. **Default für diesen Spec: weglassen** (reiner Move minimiert Risiko).

**Bewusst NICHT im Scope (nicht anfassen):** `commands/wiki/handoff.md:98` und `skills/autoresearch/SKILL.md:46,60,61,262` referenzieren `scripts/lint/lint-deps.py` bzw. `scripts/lint/lint-open-issues.py` — ein **`scripts/lint/`-Unterordner, der nicht existiert** (verifiziert: kein `scripts/lint/`, kein `lint-open-issues.py`). Vorbestehende, kaputte Pfade UNABHÄNGIG von diesem Move (Surgical-Changes: hier nicht reparieren; separat als Bug melden).

## 5. Acceptance-Criteria (binär, testbar)  ‹Wann-erledigt›

- [ ] **AC1** Alle 7 lint-Skripte liegen unter `skills/wiki-lint/scripts/`; `scripts/` enthält keine `lint-*.py`/`run-lint.py` mehr (`ls skills/wiki-lint/scripts/*.py | wc -l` = 7; `ls scripts/lint-*.py scripts/run-lint.py` → leer).
- [ ] **AC2** `run-lint.py --json` gegen einen Fixture-Vault liefert byte-identische Ausgabe VOR vs. NACH Move (`diff` leer; gleiche `checks`-Reihenfolge, `count`, `severity`, `items`, `totals`).
- [ ] **AC3** Markdown-Report-Inhalt identisch (nur Datum variabel) für denselben Fixture-Vault pre/post.
- [ ] **AC4** `python3 tests/test_run_lint.py` druckt „All tests passed." (B1–B67) mit neuen Pfaden; `test_lint_orphans.py`, `test_lint_terminology.py`, `test_lint_title_overlap.py` grün.
- [ ] **AC5** `run-lint.py --json` läuft ohne `ModuleNotFoundError` (`from vault_root import …` auflösbar) → beweist korrekte `REPO_ROOT`/lib-Tiefe.
- [ ] **AC6** Alle operativen Referenzen aktualisiert (kein `grep` findet mehr `scripts/run-lint.py`|`scripts/lint-*.py` als *ausführbaren* Pfad außerhalb `skills/wiki-lint/scripts/`):
  - `Makefile:16,17,18,19,30`
  - `skills/wiki-lint/SKILL.md:26,29,55,380,390,417,422`
  - `bin/release.py:49`
  - `evals/run.py:68`
  - `tests/test_run_lint.py:31,381,405,435` · `tests/test_lint_orphans.py:20` · `tests/test_lint_terminology.py:18` · `tests/test_lint_title_overlap.py:17`
- [ ] **AC7** `make test-run-lint` (und `make lint` / direkter `python3 …/run-lint.py`) laufen mit aktualisiertem Makefile grün.
- [ ] **AC8** Kein Schreibzugriff auf `wiki/`-Content während Lint (Read-only-Parität, B61–B63).

## 6. Test-Design  ‹Wann-erledigt›

→ [test-design](../test-designs/cmd-script-consolidation.md) (Unit: `collect*` identisch · Integration: `run-lint --json` diff pre/post auf Fixture-Vault · Import-Smoke: kein `ModuleNotFoundError`).

## 7. Security / Privacy  ‹Womit›

n/a — reiner Datei-Move + Pfad-Update, keine neue Daten-/Netzwerk-/Ausführungsoberfläche. Read-only-Charakter des Linters bleibt.

## 8. Rollout / Migration / Backout  ‹Wann›

- **Rollout:** Atomar in einem PR (`git mv` + Pfad-Edits gekoppelt), damit der importlib-Cluster nie zerrissen ist. Kein Feature-Flag, kein Shim nötig (interne Skripte; keine externen Aufrufer außer den in §5 gelisteten).
- **Backout:** `git revert <merge-commit>` — stellt flache `scripts/`-Ablage + alte Pfade in einem Schritt wieder her (keine Daten-Migration, keine State-Änderung).

---
### Checkliste (vor status: approved)
- [x] importlib-Pfade + Tests mitgezogen (§2.1 `REPO_ROOT`, §2.3 lib-Tiefe, §2.4 Test-Konstanten, §4 Schritt 3–5)
- [x] Acceptance binär (AC1–AC8, je mit prüfbarem Kommando/Diff)
- [x] Test-Design verlinkt (§6)
- [x] 7-W geprüft (Wie/Womit-Anker + PRD/ADR-Links)
- [ ] **Offen:** Fixture-Vault für AC2/AC3-Golden-Diff fixieren (Kandidat: `tests/test_run_lint.py`-`_seed_base_vault`; im Test-Design festzulegen)
- [ ] **Offen:** Entscheidung `[should]`-Dedup (§4) — für diesen Move default *weggelassen*; falls gewünscht, eigener Spec/Task
- [ ] **Beobachtung (out-of-scope):** kaputte `scripts/lint/…`-Pfade in `commands/wiki/handoff.md`, `skills/autoresearch/SKILL.md` separat melden
