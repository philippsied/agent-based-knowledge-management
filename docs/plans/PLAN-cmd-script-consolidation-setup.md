---
artifact: plan
slug: cmd-script-consolidation-setup
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [spec, adr-0003, test-design]
---

# Plan — setup-Cluster (bin/) konsolidieren OHNE Verschieben [setup]

> Beantwortet: WELCHE Schritte, in welcher Folge, WIE verifiziert?
> Wegwerf-Artefakt: nach Done erledigt.
> **Anker (7 W):** Wie (primär: Schritte) · Wann (Reihenfolge) · Womit (Deps/Tools) · Wann-erledigt (Done-Definition)
> Verträge: [SPEC-setup](../specs/SPEC-cmd-script-consolidation-setup.md) · [ADR-0003](../adr/0003-setup-cluster-stays-in-bin.md) · [test-design](../test-designs/cmd-script-consolidation.md)
> **Parallel-sicher:** Dieser Plan berührt ausschließlich `bin/` (+ `docs/`); disjunkt zu allen anderen Modul-Plänen (lint/dragonscale/ingest/commands leben unter `skills/…` bzw. `scripts/…`).

## Ziel & Done-Definition  ‹Wann-erledigt›

**Ziel:** Die Installer-Familie in `bin/` inhaltlich konsolidieren, **ohne** ein Skript zu verschieben (ADR-0003: bleibt in `bin/`). Der einzige echte Dedup-Gewinn: die wortgleich duplizierte Inline-Vault-Root-Auflösung in `setup-vault.py` + `setup-dragonscale.py` auf den kanonischen `lib/vault_root.py::resolve_vault_root()` umstellen — **nachdem** das vom Spec markierte cwd-Fallback-Delta per Test als verhaltensneutral bewiesen ist.

**Done, wenn ALLE zutreffen (= Acceptance §5 der Spec, binär):**
1. `setup-vault.py` **und** `setup-dragonscale.py` enthalten die Inline-Zeile `vault = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR.parent` nicht mehr, sondern importieren `resolve_vault_root` (je Datei genau 1 Treffer).
2. Das cwd-Fallback-Delta-Gate ist **grün** (Resolver == altes Idiom im dokumentierten Aufruf) — dokumentiert, bevor der Dedup-Commit steht.
3. Alle drei Skripte laufen fehlerfrei (Exit 0) gegen einen frischen `$TMPDIR`-Vault; ein **zweiter** Lauf ist ein No-Op (keine mtime-/Inhaltsänderung).
4. **Golden-Vergleich:** die von `setup-vault.py`/`setup-dragonscale.py` erzeugten Dateien sind byte-identisch pre/post-Refactor.
5. `hooks/wiki-path-safety.py` ist unangetastet (`git diff` leer); der `config.json`-Block in `setup-vault.py` ist inhaltlich unverändert (strict/mixed, TTY-gated).
6. `setup-multi-agent.py` ist unberührt (teilt keine Logik).
7. `make setup-dragonscale` läuft ohne Fehler; alle bestehenden `tests/` (10) grün.

**Entscheidung `bin/_setup_common.py` (evidenzbasiert, §4.2 P2):** **SKIP.** Analyse der gemeinsamen Schnittmenge zeigt: die einzigen zwei von beiden Skripten berührten State-Dateien (`address-counter.txt`, `legacy-pages.txt`) divergieren in BEIDEN Achsen — Seed-Inhalt (`0` vs. `1`; statisch `rollout: vault-local` vs. dynamisches Datum) UND Ausgabe (`setup-vault` schreibt still, `setup-dragonscale` druckt `OK/--`-Statuszeilen). Die echte Schnittmenge nach Parametrisierung < 5 LOC — ein Helper wäre eine Abstraktion für divergente Einmal-Nutzung (CLAUDE.md §2). **Kriterium für Nicht-Skip:** nur falls Schritt 3 eine ≥ ~10 LOC große, byte-deckungsgleiche Schnittmenge belegt (tut es nicht).

## Schritte  ‹Wie›

> Reihenfolge ist bindend: **Gate (S3) vor Dedup-Merge (S4).** S0–S3 sind read-only/Vorbereitung; ab S4 wird Code geändert.

### Phase A — Baseline sichern (read-only, kein Code-Change)

1. **Sauberen Ausgangszustand + Branch verifizieren.**
   → verify: `git status --porcelain` zeigt keine ungetrackten/geänderten Dateien in `bin/` **oder** `hooks/`; aktueller Branch ist der intendierte Arbeitsbranch. (Vorbestehende, unrelatierte Dirty-Einträge außerhalb `bin/`/`hooks/` → **Human-Gate G0**, siehe unten: erst klären/stashen, dann starten.)

2. **Ist-Zustand des Dedup-Ziels bestätigen (Evidenz-First).**
   → verify: `rg -c "vault = Path\(sys\.argv\[1\]\) if len\(sys\.argv\) > 1 else SCRIPT_DIR\.parent" bin/setup-vault.py bin/setup-dragonscale.py` liefert `1` je Datei; `rg -c "vault = Path\(sys\.argv\[1\]\)" bin/setup-multi-agent.py` liefert `0` (multi-agent teilt nichts).

3. **Golden-Baseline erzeugen (Verhaltens-Snapshot VOR Refactor).**
   In `$TMPDIR` zwei frische Vaults anlegen. Weil `setup-vault.py`/`setup-dragonscale.py` ohne Arg auf `SCRIPT_DIR.parent` (= Repo-Root) zeigen und `setup-dragonscale.py` intern `os.chdir(vault)` macht, **immer mit explizitem Pfad-Argument** gegen den tmp-Vault aufrufen (kein Schreiben ins Repo). Dann Ausgabe-Baum + Datei-Inhalte snapshotten (Hash je Datei). `setup-vault.py` non-interaktiv (stdin nicht-TTY) ausführen → Default `strict`, kein Prompt.
   → verify: Snapshot-Manifest (Pfad→sha256) für beide Skripte liegt unter `$TMPDIR/golden-pre.txt`; `setup-vault.py`/`setup-dragonscale.py` Exit 0. (`setup-multi-agent.py` symlinkt in HOME → NICHT im Golden-FS-Vergleich; separat in S7.)

### Phase B — cwd-Fallback-Delta-GATE (Pflicht vor jedem Merge)

4. **Präzedenz-Delta beweisen (Gate für P1 — Human-Gate G1).**
   Verifiziere, dass `resolve_vault_root()` im **dokumentierten** Aufrufprofil dieselbe Wurzel liefert wie das alte Idiom `SCRIPT_DIR.parent`. Drei Fälle testen, je gegen beide Auflösungen: (a) **kein Arg, cwd == Repo-Root** (der dokumentierte `python3 bin/setup-*.py`-Fall) → müssen identisch sein; (b) **Arg gesetzt** (`/tmp/x`) → beide liefern `/tmp/x` (argv-Vorrang bleibt); (c) **`KM_VAULT_PATH` gesetzt** → Resolver bevorzugt env (neue, additive Präzedenz — nur relevant, falls env je gesetzt wird; für Bootstrap-Nutzung ohne env verhaltensneutral). Zusätzlich das **`os.chdir`-Zusammenspiel** in `setup-dragonscale.py` prüfen: `vault` wird VOR `os.chdir(vault)` aufgelöst; Resolver muss VOR dem chdir aufgerufen werden, sonst kippt der cwd-Fallback.
   → verify: Fall (a) und (b) liefern für Resolver == altes Idiom **denselben** `Path`; Ergebnis dokumentiert in `$TMPDIR/gate-precedence.txt` mit „PASS". **Bei Delta in (a)/(b): STOP** — nicht auf `resolve_vault_root()` umstellen, stattdessen Idiom in Helper mit `SCRIPT_DIR.parent`-Fallback (Spec §2.2 Fallback-Variante); Plan-Reautorisierung nötig.

### Phase C — Dedup umsetzen (Code-Change, nur nach grünem Gate)

5. **`setup-vault.py`: Inline-Auflösung → kanonischer Resolver.**
   Vor `main()` (nach den Imports) das verifizierte Import-Idiom einfügen — **byte-identisch** zu den 8 bestehenden Nutzern (`hooks/wiki-path-safety.py`, `scripts/allocate-address.py` etc.):
   `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))` + `from vault_root import resolve_vault_root  # noqa: E402`.
   In `main()` Zeile `vault = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR.parent` ersetzen durch `vault = resolve_vault_root(sys.argv[1] if len(sys.argv) > 1 else None)`. `SCRIPT_DIR` bleibt erhalten, falls sonst genutzt — sonst nur entfernen, wenn durch DIESE Änderung verwaist (CLAUDE.md §3).
   → verify: `rg -c "resolve_vault_root" bin/setup-vault.py` == 1 (Import) bzw. Aufruf vorhanden; altes Idiom per `rg` nicht mehr auffindbar; `python3 -c "import ast; ast.parse(open('bin/setup-vault.py').read())"` OK (Syntax).

6. **`setup-dragonscale.py`: Inline-Auflösung → kanonischer Resolver (Reihenfolge zu `os.chdir` wahren).**
   Gleiches Import-Idiom einfügen. `vault = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR.parent` ersetzen durch `vault = resolve_vault_root(sys.argv[1] if len(sys.argv) > 1 else None)` — **muss VOR `os.chdir(vault)` (aktuell Zeile 32) stehen**, damit der cwd-Fallback des Resolvers noch das Repo-Root sieht (nach `os.chdir` wäre cwd = vault). Reihenfolge Resolve→chdir unverändert lassen.
   → verify: `rg -c "resolve_vault_root" bin/setup-dragonscale.py` == 1; altes Idiom weg; im Quelltext erscheint `resolve_vault_root(` **vor** `os.chdir(` (Zeilennummern-Check); Syntax-Parse OK.

### Phase D — Verifikation (Verhalten + Constraints)

7. **Idempotenz + Golden-Vergleich POST-Refactor (gegen tmp-Vault).**
   In frischen `$TMPDIR`-Vaults die Schritte aus S3 wiederholen (`golden-post.txt`); dann jedes Skript ein **zweites** Mal laufen lassen und mtimes/Hashes vergleichen. `setup-multi-agent.py` gegen einen wegwerfbaren `HOME`-Surrogat (`$TMPDIR/fakehome`) zweimal laufen lassen (Symlink-Existenzprüfung → 2. Lauf No-Op).
   → verify: `golden-pre.txt` == `golden-post.txt` (byte-identisch, `diff` leer) für `setup-vault`/`setup-dragonscale`; 2. Lauf jedes der drei Skripte ändert keine Datei-mtime/kein Hash (Exit 0, No-Op-Zeilen `--  … already present`); `setup-multi-agent` 2. Lauf meldet `already linked`.

8. **Argument-Override-Regression.**
   → verify: `python3 bin/setup-vault.py "$TMPDIR/ov"` schreibt Skelett nach `$TMPDIR/ov`, **nicht** ins Repo-Root; `git status --porcelain bin/ hooks/` unverändert; im Repo-Root entsteht kein `wiki/`/`.vault-meta/`.

9. **Path-safety-Constraint + config.json unverändert (Security-Gate — Human-Gate G2).**
   → verify: `git diff --exit-code -- hooks/wiki-path-safety.py` liefert Exit 0 (leer); `git diff -- bin/setup-vault.py` zeigt im `config.json`-Block (`path_safety_mode`, `isatty`, `strict`/`mixed`, Prompt-Text) **keine** inhaltliche Zeile geändert (nur die Resolver-Zeile + Import oben); kein Setup-Skript referenziert/schreibt `hooks/wiki-path-safety.py` (`rg -l "wiki-path-safety" bin/` == leer).

10. **Volle Test-Suite + Make-Target (Regression).**
    → verify: `make test` bzw. `pytest` → alle 10 `tests/`-Dateien grün (insb. `tests/test_vault_root.py`, `tests/test_run_lint.py`, `tests/test_lint_orphans.py` — Resolver-Präzedenz unverändert); `make setup-dragonscale` Exit 0.

### Phase E — Abschluss

11. **Manifest-Status für Modul `setup` fortschreiben** (nur `docs/manifests/cmd-script-consolidation.json`, Feld `session`/`status` des setup-bezogenen Eintrags — falls Konvention es vorsieht; sonst überspringen). ADR-0003 ist bereits `accepted` und deckt die Ownership-Entscheidung → **kein** neues ADR/Addendum nötig (die Spec-§4.1-Addendum-Forderung ist durch ADR-0003 erfüllt).
    → verify: `git diff` betrifft nur `bin/setup-vault.py`, `bin/setup-dragonscale.py` und optional das Manifest; nichts unter `skills/`/`scripts/`/`hooks/`.

12. **Commit (Human-Gate G3 vor Push).** Ein Commit `refactor(setup): dedup vault-root resolution onto lib/vault_root (keep bin/)`. Optional getrennter Commit nur bei P2 (entfällt: SKIP).
    → verify: `git show --stat` listet ausschließlich die zwei `bin/`-Skripte (+ ggf. Manifest); Commit-Message conventional. **Push erst nach expliziter Freigabe.**

## Abhängigkeiten / Reihenfolge  ‹Wann / Womit›

- **Tools:** `python3` (vorhanden), `rg`, `git`, `make`, `curl` (nur `setup-vault.py`-Downloads — im tmp-Golden ggf. netz-abhängig; Download-Zweig ist an vorhandene `manifest.json` der Plugins gekoppelt und im leeren tmp-Vault inaktiv → kein Netz nötig).
- **Harte Reihenfolge:** S1→S2→S3 (Baseline) → **S4 Gate** → S5/S6 (Dedup, in beliebiger Reihenfolge, unabhängig) → S7–S10 (Verify) → S11–S12 (Abschluss).
- **Gate-Kopplung:** S5/S6 dürfen NICHT vor grünem S4 beginnen (Spec §6.3, test-design „Gate für P1").
- **Dep auf andere Pläne:** keine. `bin/` ist disjunkt zu lint/dragonscale/ingest/commands-Modulen → dieser Plan ist vollständig parallel-fähig.
- **Upstream-Verträge:** ADR-0003 (accepted) fixiert „bleibt in `bin/`" → **keine** Pfad-/Aufrufer-Updates (README/Makefile/AGENTS.md/GEMINI.md/install-guide zeigen weiter auf `bin/setup-*.py`).

## Risiken & Rollback

- **R1 — cwd-Fallback-Delta real (Resolver ≠ altes Idiom in Fall a/b).** Würde Verhalten ändern (falscher Vault-Root ohne Arg aus fremdem cwd). → **Mitigation:** S4-Gate VOR Merge; bei Delta STOP + Fallback-Helper-Variante (Spec §2.2). → **Rollback:** kein Code committed (Gate ist pre-merge).
- **R2 — `os.chdir`-Ordering in `setup-dragonscale.py` verletzt.** Resolver nach `os.chdir` aufgerufen → cwd-Fallback liefert `vault` statt Repo-Root, bei fehlendem Arg falsch. → **Mitigation:** S6 erzwingt Resolve-vor-chdir + Zeilennummern-Check. → **Rollback:** `git checkout -- bin/setup-dragonscale.py`.
- **R3 — Import-Idiom weicht ab (sys.path-Tiefe falsch → `ModuleNotFoundError`).** → **Mitigation:** byte-identisches Kopieren aus `scripts/allocate-address.py`; `parent.parent/"lib"` ist für `bin/`-Skripte korrekt (bin/ → repo-root → lib/). → **Rollback:** `git checkout -- bin/`.
- **R4 — Golden-Vergleich schlägt fehl (unbeabsichtigte Inhaltsänderung, z.B. verwaistes `SCRIPT_DIR` entfernt und dabei anderes berührt).** → **Mitigation:** Surgical-Change (nur Resolver-Zeile + Import); S7 Golden-Diff fängt es. → **Rollback:** `git checkout -- bin/`.
- **R5 — Path-safety versehentlich berührt.** → **Mitigation:** S9 `git diff --exit-code hooks/wiki-path-safety.py`. → **Rollback:** `git checkout -- hooks/wiki-path-safety.py`.
- **R6 — P2-Übererfüllung (`_setup_common.py` doch angelegt).** → **Mitigation:** Entscheidung SKIP steht fest (Done §P2); Helper nur bei ≥~10 LOC deckungsgleicher Schnittmenge (nicht gegeben). → **Rollback:** Datei löschen, Inline-Code belassen.
- **Global Rollback:** `git revert` des einen Commits; Setup ist idempotent → folgenlos re-runnbar, kein Vault-Zustands-Rollback nötig (Spec §8).

## Human-Gates  ‹Wann: Freigabe›

- [ ] **G0 (vor S1):** Arbeitsstart nur bei sauberem Repo auf intendiertem Branch. Vorbestehende, unrelatierte Dirty-Einträge außerhalb `bin/`/`hooks/` (z.B. `docs/manifests/*`, `skills/visualize/`) → bestätigen/stashen, BEVOR Code geändert wird (CLAUDE.md: nur in clean repo arbeiten).
- [ ] **G1 (nach S4, vor S5/S6):** cwd-Fallback-Delta-Gate muss **PASS** sein — Beleg (`gate-precedence.txt`) gesichtet, bevor irgendein Dedup-Merge erfolgt. Bei Delta: Plan-Reautorisierung (Fallback-Helper-Variante).
- [ ] **G2 (nach S9):** Security-Gate — `hooks/wiki-path-safety.py` `git diff` leer UND `config.json`-Block inhaltlich unverändert bestätigt, bevor committet wird.
- [ ] **G3 (nach S12, vor Push):** Push/PR erst nach expliziter Nutzerfreigabe (CLAUDE.md: ask before any push).

---
### Checkliste
- [x] Done-Definition konkret (7 binäre Kriterien = Spec §5)  ‹Wann-erledigt›
- [x] Jeder Schritt hat einen Verify-Check (deterministisch: `rg`/`diff`/Exit-Code)  ‹Wie›
- [x] Riskante Schritte haben Rollback (R1–R6 + global `git revert`)
- [x] Human-Gates markiert (G0 clean-repo · G1 precedence-gate · G2 security · G3 push)  ‹Wann›
- [x] Schritte atomar genug → werden zu Tasks (12 nummerierte Schritte)
- [x] 7-W-Abdeckung geprüft (Wie/Wann/Womit/Wann-erledigt)
- [x] `_setup_common`-Entscheidung evidenzbasiert (SKIP, Kriterium dokumentiert)
- [x] Gate-vor-Merge-Reihenfolge erzwungen (S4 vor S5/S6)
- [x] Parallel-Sicherheit begründet (bin/ disjunkt zu skill-/scripts-Dirs)
