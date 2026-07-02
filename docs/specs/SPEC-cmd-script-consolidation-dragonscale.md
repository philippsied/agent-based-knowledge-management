---
artifact: spec
slug: cmd-script-consolidation
module: dragonscale
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [prd, adr-0002]
---

# Spec — dragonscale-Cluster konsolidieren + co-locate [dragonscale]

> WIE verteilen wir den DragonScale-Cluster auf die besitzenden Skills + geteilte Util nach `lib/`?
> **Anker (7 W):** Wie · Womit · [PRD](../prds/cmd-script-consolidation.md) · [ADR-0002](../adr/0002-colocate-scripts-under-skill.md)

## 1. Ziel & Kontext  ‹Was/Warum → PRD›
DragonScale-Cluster (~969 LOC) spannt **drei** Skills. Anders als `lint`/`ingest` (ein Cluster → ein
Skill) **splittet** Co-location diesen Cluster: jedes Skript zieht unter seinen durch echte Nutzung
belegten Besitzer-Skill; nur zwischen zwei der drei Skripten dupliziert echter Code, der nach `lib/`
extrahiert wird. Reiner Refactor — gleiche Inputs → gleiche Outputs (PRD §4 Out, ADR-0002).

**Kopplung verifiziert (nicht angenommen):** die drei Skripte importieren untereinander **nichts**;
gemeinsam ist heute nur `from vault_root import resolve_vault_root` (`lib/vault_root.py`, bleibt `lib/`
laut PRD §6). Die „geteilten Utilities“ aus PRD/ADR sind konkret: identische Exclude-Policy-Konstanten
+ `log()` zwischen `boundary-score` und `tiling-check` (Beleg §2). `allocate-address` teilt **keinen**
Body-Code mit den beiden (nur der triviale Name `main`).

## 2. Schnittstellen / Verträge  ‹Womit›

### 2.1 Ziel-Skill je Skript (durch reale Nutzung belegt)

| Skript | LOC | Ziel-Skill | Nutzungs-Beleg (Aufrufer, real) |
|---|--:|---|---|
| `boundary-score.py` | 316 | `skills/autoresearch/scripts/` | `skills/autoresearch/SKILL.md:112` Feature-Gate `[ -x ./scripts/boundary-score.py ]`, `:121` ruft `./scripts/boundary-score.py --json --top 5` für No-Topic-Frontier-Auswahl (Mechanism 4). Docstring: „boundary-first autoresearch scorer … autoresearch only invokes this“. **Einziger funktionaler Aufrufer = autoresearch.** |
| `tiling-check.py` | 500 | `skills/wiki-lint/scripts/` | `skills/wiki-lint/SKILL.md:277-309` (`--peek`, `--report`) + `agents/wiki-lint.md:38,46` delegieren an das Skript (Mechanism 3, semantic tiling). Docstring: „semantic tiling lint“. **Besitzer = wiki-lint.** Koordination mit spec-lint: `run-lint`/`lint-*` ziehen ebenfalls nach `skills/wiki-lint/scripts/` → gleiches Zielverzeichnis, keine Namenskollision (`tiling-check.py` ≠ `lint-*.py`). |
| `allocate-address.py` | 153 | `skills/wiki-ingest/scripts/` | **ingest-Zeit, nicht fold-Zeit** (offene Frage aufgelöst): `skills/wiki-ingest/SKILL.md:316` Feature-Gate, `:344` `ADDR=$(python3 scripts/allocate-address.py)`, `:358` „Before writing a new non-meta page, call …“ — der **Schreib-Aufruf** (reserviert Adresse) sitzt in wiki-ingest. `skills/wiki-fold/SKILL.md` ruft es **nicht** auf. `wiki-lint` (SKILL.md:193,227) nutzt nur `--peek` **read-only** zur Zähler-Konsistenz → Konsument, nicht Besitzer. **Besitzer = wiki-ingest.** |

Invokations-Konvention heute: alle Aufrufer nutzen den repo-root-relativen Pfad `./scripts/<name>.py`
bzw. `scripts/<name>.py`. Nach dem Move ändert sich dieser Pfad je Skript auf `skills/<skill>/scripts/<name>.py`
und muss in **jedem** Aufrufer (SKILL.md, agents/, docs, Makefile, Tests, Installer) mitgezogen werden (§2.3).

### 2.2 Geteilte Util → `lib/`-Modul (Beleg + ehrlicher Umfang)

Def-/Konstanten-Vergleich `boundary-score.py` ↔ `tiling-check.py` (byte-genau geprüft):

| Symbol | boundary-score | tiling-check | byte-identisch? | nach `lib/`? |
|---|:--:|:--:|:--:|---|
| `EXCLUDE_TYPES`, `EXCLUDE_FILENAMES`, `EXCLUDE_PATH_PREFIXES` | ✓ | ✓ | **ja** | **ja** |
| `FRONTMATTER_RE`, `TYPE_RE` | ✓ | ✓ | **ja** | **ja** |
| `log(msg)` | ✓ | ✓ | **ja** | **ja** |
| `parse_frontmatter(text)` | ✓ (4 Felder: type/updated/created/title) | ✓ (nur type) | **nein — divergente Bodies** | nur via Superset-API (s.u.) |
| `included(path, fm)` | ✓ → `bool`, `resolve(strict=True)` | ✓ → `tuple[bool,str]`, `resolve()` (non-strict) | **nein — divergente Signatur + Semantik** | nur via Superset-API (s.u.) |

**Neues Modul:** `lib/dragonscale_pages.py` — DragonScale-Seiten-Policy (Vault-Seiten-Auswahl +
Frontmatter), genutzt von `boundary-score` (in `autoresearch`) und `tiling-check` (in `wiki-lint`).

**Sicher (behavior-identisch) zu extrahieren — MUST:**
- Konstanten `EXCLUDE_TYPES`, `EXCLUDE_FILENAMES`, `EXCLUDE_PATH_PREFIXES`, `FRONTMATTER_RE`, `TYPE_RE`
- `log(msg: str) -> None`

**Nur mit verhaltenswahrender Superset-API zu extrahieren — SHOULD (sonst per-Skript belassen):**
- `parse_frontmatter(text, keys=...)` — die extrahierte Version parst **alle** Felder; jeder Aufrufer
  liest weiterhin nur die Keys, die er heute liest (tiling ignoriert updated/created/title → identisches
  Ergebnis). Muss durch beide Test-Suiten unverändert bestätigt werden.
- `included(path, vault_root)` — muss **beide** Rückgabeformen bedienen (Bool für boundary, Grund-String
  für tiling) UND die **strict-vs-non-strict** `resolve`-Semantik pro Aufrufer erhalten. Da dies das
  Regressions-Risiko ist (unterschiedliche Symlink-/Escape-Behandlung), ist es SHOULD, nicht MUST:
  bringt der Merge auch nur eine Test-Abweichung, bleibt `included` per-Skript (Duplikat akzeptiert,
  reiner Refactor > DRY).

`allocate-address.py` trägt **nichts** zu `lib/` bei (kein geteilter Body); seine Adress-Mathematik
(`scan_max_c_address`, `read_or_recover_counter`, `acquire_lock`) bleibt im Skript unter `wiki-ingest`.

### 2.3 Zu aktualisierende Referenzen (vollständig, verifiziert)

| Pfad-Referenz auf … | Dateien (Aufrufer/Doku/Test/Installer) |
|---|---|
| `scripts/boundary-score.py` | `skills/autoresearch/SKILL.md`; `Makefile` (test-boundary, Zeile ~15/46); `tests/test_boundary_score.py` (`HELPER`, `importlib` white-box); `docs/dragonscale-guide.md`; `docs/releases/v1.6.0.md` |
| `scripts/tiling-check.py` | `skills/wiki-lint/SKILL.md`; `agents/wiki-lint.md`; `bin/setup-dragonscale.py` (Zeilen 37, 46 — Installer-Copy + chmod); `Makefile` (test-tiling); `tests/test_tiling_check.py` (`HELPER`, `importlib`); `docs/dragonscale-guide.md`; `docs/plans/PLAN-sh-to-py-full-migration.md`; `docs/upstream-roadmap.md`; `docs/releases/v1.6.0.md` |
| `scripts/allocate-address.py` | `skills/wiki-ingest/SKILL.md`; `skills/wiki-lint/SKILL.md` (`--peek`-Konsument); `agents/wiki-ingest.md`; `agents/wiki-lint.md`; `bin/setup-dragonscale.py` (Zeilen 36, 45, 118 — Copy + chmod + `--peek`-Smoke-Test); `Makefile` (test-address); `tests/test_allocate_address.py` (`ALLOCATOR`); `docs/dragonscale-guide.md`; `docs/plans/PLAN-sh-to-py-full-migration.md`; `docs/releases/v1.6.0.md` |

`lib/`-Import bleibt gültig: alle drei Skripte setzen `sys.path.insert(0, <parent>/../lib)`. Nach dem Move
nach `skills/<skill>/scripts/` ist `lib/` zwei Ebenen höher **statt** einer → der `parent.parent`-Pfad
muss auf `parent.parent.parent` (bzw. äquivalent auf die Repo-Wurzel) angepasst werden, damit
`vault_root` und `dragonscale_pages` weiter auflösen. **(Load-bearing — siehe AC-6.)**

**Nicht zu ändern (bewusst ausgeschlossen):** `wiki/meta/**` Session-Logs, `CHANGELOG.md`,
`bin/__pycache__/*.pyc` (historisch/generiert). `README.md`/`AGENTS.md`/`GEMINI.md` nennen `scripts/`
nur generisch (kein DragonScale-Skriptpfad) → prüfen, i. d. R. keine Änderung.

## 3. Verhalten  ‹Wie›

### Happy path
Nach Move + Ref-Update verhält sich jedes Skript **identisch** zu vorher, nur unter neuem Pfad:
- `autoresearch` (No-Topic + DragonScale) ruft `skills/autoresearch/scripts/boundary-score.py --json --top 5`
  → gleiche Frontier-Top-K wie vorher.
- `wiki-lint` ruft `skills/wiki-lint/scripts/tiling-check.py --peek|--report` → gleiche Exit-Codes/Report.
- `wiki-ingest` ruft `skills/wiki-ingest/scripts/allocate-address.py` → gleiche `c-NNNNNN`-Reservierung;
  `wiki-lint --peek` liest denselben Zähler.
- `lib/dragonscale_pages.py` liefert für `boundary-score`/`tiling-check` dieselbe Seiten-Auswahl wie die
  bisher inline definierten Konstanten/Funktionen (Byte-Gleichheit der extrahierten Symbole vorausgesetzt).

### Edge-Cases — embeddings/Modell-Abhängigkeit von `tiling-check`
`tiling-check.py` ist das einzige Skript mit externer Laufzeit-Abhängigkeit: **ollama + `nomic-embed-text`**
(Default `http://127.0.0.1:11434`). Feature-Gate-Exit-Codes **10** (ollama unerreichbar) und **11** (Modell
nicht gepullt) müssen nach dem Move **unverändert** von `wiki-lint` als Skip-Bedingungen behandelt werden
(SKILL.md:287, agents/wiki-lint.md:38 „Surface exit codes 0/2/3/4/10/11 distinctly“). Sicherheits-Semantik
(`--allow-remote-ollama`, Symlink-/Vault-Escape-Reject, `.vault-meta/.tiling.lock` flock, `--report`-Pfad
gegen `VAULT_ROOT` validiert) bleibt bit-genau erhalten — Move ändert **nur** den Skript-Pfad, keine Logik.
Die anderen zwei Skripte brauchen ollama **nicht** (`boundary-score`: nur `python3`; `allocate-address`:
nur stdlib) — der Split darf diese Asymmetrie nicht einebnen.

### Fehlerbehandlung
- **Vergessene Referenz** (Aufrufer zeigt auf alten `scripts/`-Pfad): Feature-Gate `[ -x/-f … ]` schlägt
  fehl → optionaler DragonScale-Pfad **verstummt** (no-op), statt hart zu brechen — deckt sich mit dem
  bestehenden Opt-in-Muster. Genau deshalb ist die Ref-Vollständigkeit (§2.3) Acceptance-kritisch:
  ein stiller No-op ist ein *bestandener* Test, aber ein *kaputtes* Feature (PRD §3, „0 Treffer“ alte Pfade).
- **`lib/`-Pfad falsch nach Move** (`parent.parent` nicht angepasst): `ImportError` beim Start → Skript
  bricht sofort, von Tests gefangen (AC-6).
- **Superset-`included`/`parse_frontmatter` verschiebt Verhalten**: von den bestehenden 35 (boundary) bzw.
  tiling-Unit-Tests gefangen → Fallback „per-Skript belassen“ (§2.2 SHOULD).

## 4. Gewählter Ansatz  ‹Wie›
**Split-Move + gezielte `lib/`-Extraktion + Ref-Update**, in dieser Reihenfolge (jeder Schritt einzeln grün):

1. **`lib/dragonscale_pages.py` anlegen** mit den byte-identischen Symbolen (Exclude-Konstanten,
   `FRONTMATTER_RE`, `TYPE_RE`, `log`); optional (SHOULD) `parse_frontmatter`/`included` als Superset-API.
   `boundary-score` + `tiling-check` importieren daraus statt inline; verify: beide Unit-Suiten grün **vor**
   dem Move (Extraktion isoliert von Move testen).
2. **Move** `boundary-score.py` → `skills/autoresearch/scripts/`, `tiling-check.py` → `skills/wiki-lint/scripts/`,
   `allocate-address.py` → `skills/wiki-ingest/scripts/` (git mv). `sys.path`-Ebene (`parent.parent` →
   Repo-Wurzel) je Skript korrigieren; verify: `python3 <neuer Pfad> --help`/`--peek` startet ohne ImportError.
3. **Ref-Update** aller §2.3-Pfade (SKILL.md, agents/, `bin/setup-dragonscale.py` inkl. Copy-Liste/chmod/`--peek`,
   `Makefile`, Test-`HELPER`/`ALLOCATOR`/`importlib`, docs); verify: `rg 'scripts/(boundary-score|tiling-check|allocate-address)\.py'`
   findet **0** Treffer außerhalb der bewusst ausgeschlossenen Dateien (§2.3).
4. **Regression**: `make test` (inkl. `test_boundary_score`, `test_tiling_check`, `test_allocate_address`,
   `test_run_lint` mit spec-lint koordiniert) + autoresearch-Eval grün; `run-lint --json` pre/post gegen
   Fixture-Vault diff-leer (PRD §3).

Koordination: `tiling-check` und die `lint-*`-Skripte teilen sich das Zielverzeichnis `skills/wiki-lint/scripts/`
(spec-lint) — Reihenfolge/Zielordner mit spec-lint abstimmen, damit beide Specs denselben Ordner erzeugen.

## 5. Acceptance-Criteria (binär, testbar)  ‹Wann-erledigt›
- [ ] **AC-1** `boundary-score.py` liegt unter `skills/autoresearch/scripts/`; `scripts/boundary-score.py` existiert nicht mehr.
- [ ] **AC-2** `tiling-check.py` liegt unter `skills/wiki-lint/scripts/`; `scripts/tiling-check.py` existiert nicht mehr.
- [ ] **AC-3** `allocate-address.py` liegt unter `skills/wiki-ingest/scripts/`; `scripts/allocate-address.py` existiert nicht mehr.
- [ ] **AC-4** `lib/dragonscale_pages.py` existiert und enthält die byte-identisch geteilten Symbole (Exclude-Konstanten, `FRONTMATTER_RE`, `TYPE_RE`, `log`); `boundary-score` + `tiling-check` importieren daraus, kein Duplikat der extrahierten Symbole mehr inline. (`parse_frontmatter`/`included` nur extrahiert, wenn beide Test-Suiten unverändert grün bleiben; sonst dokumentiert per-Skript belassen.)
- [ ] **AC-5** Alle Konsumenten-Referenzen aus §2.3 aktualisiert: `skills/autoresearch/SKILL.md`, `skills/wiki-lint/SKILL.md`, `skills/wiki-ingest/SKILL.md`, `agents/wiki-lint.md`, `agents/wiki-ingest.md`, `bin/setup-dragonscale.py` (Copy-Liste + chmod + `--peek`), `Makefile`, `docs/dragonscale-guide.md` (+ `docs/plans/PLAN-sh-to-py-full-migration.md`, `docs/upstream-roadmap.md`, `docs/releases/v1.6.0.md`).
- [ ] **AC-6** `sys.path`-Auflösung nach `lib/` je verschobenem Skript korrigiert; `python3 <neuer Pfad> --peek`/`--help` startet ohne `ImportError`.
- [ ] **AC-7** `rg 'scripts/(boundary-score|tiling-check|allocate-address)\.py'` = **0** Treffer außer in `wiki/meta/**`, `CHANGELOG.md`, `__pycache__` (PRD §3 „0 Treffer“).
- [ ] **AC-8** Betroffene Tests grün: `tests/test_boundary_score.py`, `tests/test_tiling_check.py`, `tests/test_allocate_address.py` (Pfade `HELPER`/`ALLOCATOR`/`importlib` mitgezogen) — via `make test`.
- [ ] **AC-9** autoresearch-Eval grün; `run-lint --json` pre/post gegen Fixture-Vault diff-leer (Verhalten erhalten, reiner Refactor).
- [ ] **AC-10** `tiling-check` Exit-Codes 10/11 (ollama/Modell) werden von `wiki-lint` weiterhin als Skip behandelt (Feature-Gate + Exit-Code-Handling unverändert).

## 6. Test-Design  ‹Wann-erledigt›
→ [test-design](../test-designs/cmd-script-consolidation.md)

## 7. Security / Privacy  ‹Womit›
n/a (reiner Refactor). Sicherheits-Semantik von `tiling-check` (localhost-Default, `--allow-remote-ollama`-Gate,
Symlink-/Escape-Reject, `--report`-Pfad-Validierung gegen `VAULT_ROOT`) und `allocate-address` (`fcntl.flock`)
bleibt bit-genau erhalten — es wird kein Sicherheitsverhalten geändert, nur der Skript-Pfad.

## 8. Rollout / Migration / Backout  ‹Wann›
Rollout in der §4-Reihenfolge (Extraktion → Move → Ref → Regression), jeder Schritt ein eigener Commit.
**Backout:** `git revert` der Move-/Extraktions-Commits stellt die flachen `scripts/`-Pfade + inline-Util
wieder her; da rein pfad-/struktur-bezogen und ohne Datenmigration, ist der Revert vollständig und ohne
Restzustand (keine Vault-/`.vault-meta/`-Änderung).

---
### Checkliste (vor status: approved)
- [x] Ziel je Skript durch Nutzung belegt (boundary→autoresearch SKILL.md:112/121 · tiling→wiki-lint SKILL.md:277-309 + agent · allocate→wiki-ingest SKILL.md:316/344/358, **ingest-Zeit**)
- [x] shared→lib entschieden (`lib/dragonscale_pages.py`: Exclude-Policy + `log` MUST; `parse_frontmatter`/`included` SHOULD via Superset — Bodies divergent, ehrlich markiert)
- [x] Acceptance binär (AC-1…10, alle grep-/test-prüfbar)
- [x] 7-W geprüft (Wie=§3/§4 · Womit=§2 · Wann-erledigt=§5/§6)
