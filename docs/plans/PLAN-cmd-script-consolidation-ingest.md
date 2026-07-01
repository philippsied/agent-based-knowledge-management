---
artifact: plan
slug: cmd-script-consolidation-ingest
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [spec, adr-0002, test-design]
---

# Plan — ingest-Cluster co-locate unter `skills/wiki-ingest/scripts/` (ZERO behavior change)

> Beantwortet: WELCHE Schritte, in welcher Folge, WIE verifiziert?
> Wegwerf-Artefakt: nach Done erledigt.
> **Anker (7 W):** Wie (primär: Schritte) · Wann (Reihenfolge) · Womit (Deps/Tools) · Wann-erledigt (Done-Definition)
> **Vertrag:** reiner Verschiebe-Refactor. Identisches Verhalten, nur Ablageort (+ ggf. reine Bookkeeping-Textrefs) ändern sich.
> **Quellen:** [SPEC-ingest](../specs/SPEC-cmd-script-consolidation-ingest.md) · [ADR-0002](../adr/0002-colocate-scripts-under-skill.md) · [Test-Design](../test-designs/cmd-script-consolidation.md)

## Ziel & Done-Definition  ‹Wann-erledigt›

Erledigt, wenn **alle** binären Gates grün sind:

- `skills/wiki-ingest/scripts/rewrite-wikilinks.py` **und** `skills/wiki-ingest/scripts/wiki-prepass.py` existieren; `scripts/rewrite-wikilinks.py` **und** `scripts/wiki-prepass.py` existieren **nicht** mehr.
- Beide verschobenen Dateien sind **byte-identisch** zum Vorzustand (`git show HEAD:scripts/<name>` == neuer Inhalt) — sofern KEIN optionaler Dedup/Docstring-Edit gewählt wird; bei gewähltem Edit gilt stattdessen die Verhaltens-Parität (unten).
- Beide sind weiterhin ausführbar (Mode `0755` erhalten) und liefern unveränderten `--help`/Usage-Text, Exit `0`.
- **Verhaltens-Parität** (Fixture-Vault): rewrite-wikilinks stdout+Rewrite-Diff pre==post leer; wiki-prepass `--all --dry-run` JSON-Report pre==post leer (`ensure_ascii=False`).
- **Keine toten Live-Pfad-Refs:** `rg 'scripts/(rewrite-wikilinks|wiki-prepass)'` liefert außerhalb bewusster Historie (siehe §Reihenfolge → Ref-Klärung) **0** Treffer, die behaupten, die Skripte lägen aktuell unter `scripts/`.
- **Volle Testsuite grün** als Regressionsnachweis: `make test` (10 Testdateien) läuft unverändert durch.

## Ground-Truth-Befund (verifiziert, weicht teils von den Spec-Zeilennummern ab)  ‹Womit›

Vor der Ausführung per `rg`/`stat`/`sed` bestätigt — **wichtig, weil die im Spec §3/§4 gelisteten Zeilennummern veraltet sind**:

1. **Quelle vorhanden, Ziel fehlt:** `scripts/rewrite-wikilinks.py` (Mode `0755`), `scripts/wiki-prepass.py` (Mode `0755`) existieren. `skills/wiki-ingest/scripts/` **existiert noch nicht** → `git mv` legt es an.
2. **`resolve_vault()` byte-identisch in beiden Skripten**, Präzedenz **`cli_arg → KM_VAULT_PATH → CWD`** (Schleife über `(cli_arg, os.environ.get("KM_VAULT_PATH"), os.getcwd())`, erster existierender Pfad gewinnt, sonst `SystemExit`). `lib/vault_root.py::resolve_vault_root()` nutzt **env-first** (`KM_VAULT_PATH → cli_arg → cwd`) → **divergiert**. Naives „auf lib umstellen" = Verhaltensänderung.
3. **pytest ist NICHT installiert** (`ModuleNotFoundError: No module named 'pytest'`). Die Suite läuft über **`make test`** bzw. `python3 tests/test_*.py` (stdlib `unittest`). „pytest grün" ist hier operational = **`make test` grün**. (Falls jemand pytest nachinstalliert: `python3 -m pytest tests/` ist gleichwertig, aber nicht Voraussetzung.)
4. **Doc-Layer-Refs — reale Fundstellen (nicht die Spec-Zeilen):**
   - `docs/prds/cmd-script-consolidation.md:43` — nennt `rewrite-wikilinks`/`wiki-prepass` **ohne** `scripts/`-Präfix (LOC-Tabelle) → **kein Pfad-Edit**.
   - `docs/adr/0002-colocate-scripts-under-skill.md:32` — bare Namen, zeigt bereits `skills/wiki-ingest/scripts/` als Ziel → **kein Pfad-Edit**.
   - `docs/upstream-roadmap.md:216, 296, 366` — die **einzigen** Fundstellen mit Literal `scripts/rewrite-wikilinks.py`/`scripts/wiki-prepass.py`. Kontext: PR5-Record (`:216`), „New:"-Changelog (`:296`), Current-State-Inventory-Appendix vom 2026-05-21 (`:366`). Das sind **historische Aufzeichnungen**, keine „aktueller-Pfad"-Aussagen.
   - `docs/plans/PLAN-sh-to-py-full-migration.md` (~`:109`, ~`:541`) — nur die **„matches lib/vault_root.sh"-Docstring-Allowlist**, dort explizit als „leave / allowlisted / not load-bearing" markiert → **kein Pfad-Edit**.
   - `docs/test-designs/cmd-script-consolidation.md` — **keine** Fundstelle für Skriptnamen/„smoke" bzgl. dieses Clusters; Zeile 30 betrifft `commands/`, nicht diese Skripte.
   - **Kein** `skills/`-Pfadref (nur `allocate-address.py`, out of scope), **kein** Test-Ref, **kein** Manifest-Ref, **keine** Sibling-Spec außer der eigenen Spec.
   - Root-Smoke `rg 'scripts/(rewrite-wikilinks|wiki-prepass)' README.md AGENTS.md GEMINI.md Makefile` → **bereits 0**.
5. **Netto:** einzige zwingende Code-Aktion = die zwei `git mv`. Zwingende *Live-Pfad*-Doc-Edits ≈ **null**; die verbleibenden Refs sind Historie/Allowlist und werden **verifiziert + gegated**, nicht blind editiert (siehe Human-Gate 1).

## Schritte  ‹Wie›

> Reihenfolge strikt. Jeder Schritt hat einen deterministischen Verify. Abbruch bei rotem Verify → §Risiken & Rollback.

**S0 — Vorbedingungen (read-only)**
Aktion: bestätige sauberen Baum auf `main` und dass die aktuell in `git status` gelisteten Deletions/Untracked (`.cursor/…`, `.windsurf/…`, `skills/visualize/`) **nicht** zu diesem Cluster gehören und den Move nicht blockieren.
→ verify: `git rev-parse --abbrev-ref HEAD` == `main`; `git status --short` enthält keine Änderung an `scripts/rewrite-wikilinks.py`/`scripts/wiki-prepass.py`/`skills/wiki-ingest/`. (Human-Gate 0.)

**S1 — Pre-Move-Baseline sichern (für Byte-/Verhaltens-Diff)**
Aktion: capture in Scratch: (a) `git hash-object scripts/rewrite-wikilinks.py scripts/wiki-prepass.py` → Blob-Hashes; (b) `--help`-Ausgabe beider Skripte; (c) gegen einen **Fixture-Vault** (siehe §Deps) `python3 scripts/rewrite-wikilinks.py <fixture-map.tsv> --vault <fix> --dry-run` (stdout) und `python3 scripts/wiki-prepass.py --vault <fix> --all --dry-run` (JSON stdout). Alles nach `$SCRATCH/pre/`.
→ verify: 4 Baseline-Artefakte existieren und sind nicht leer; beide Skripte Exit `0` im Dry-Run.

**S2 — Zielverzeichnis + Move (git mv, Inhalt unverändert)**
Aktion: `mkdir -p skills/wiki-ingest/scripts` (falls nötig; `git mv` legt Pfad i.d.R. selbst an), dann
`git mv scripts/rewrite-wikilinks.py skills/wiki-ingest/scripts/rewrite-wikilinks.py`
`git mv scripts/wiki-prepass.py skills/wiki-ingest/scripts/wiki-prepass.py`.
→ verify: `test -f skills/wiki-ingest/scripts/rewrite-wikilinks.py && test -f skills/wiki-ingest/scripts/wiki-prepass.py`; `test ! -e scripts/rewrite-wikilinks.py && test ! -e scripts/wiki-prepass.py`; `git diff --cached --stat` zeigt genau 2 Renames (R100).

**S3 — Byte-Identität + Mode nach Move**
Aktion: vergleiche neue Blob-Hashes und Mode gegen Baseline.
→ verify: `git hash-object skills/wiki-ingest/scripts/<name>` == S1-Hash (beide); `git diff --cached --summary` zeigt keine Mode-Änderung (bleibt `100755`); `test -x skills/wiki-ingest/scripts/rewrite-wikilinks.py && test -x skills/wiki-ingest/scripts/wiki-prepass.py`.

**S4 — Verhaltens-Parität nach Move (kein CWD-/`__file__`-Effekt)**
Aktion: dieselben Kommandos wie S1 vom **neuen** Pfad gegen denselben Fixture-Vault → `$SCRATCH/post/`; dann `diff -u` pre↔post je Artefakt.
→ verify: `--help` neu==alt; rewrite-wikilinks Dry-Run-stdout neu==alt; wiki-prepass JSON-Report neu==alt (Diffs leer); beide Exit `0`.

**S5 — Ref-Klärung (Doc-Layer) — live neu bestimmen, NICHT Spec-Zeilen vertrauen**
Aktion: `rg -n 'scripts/(rewrite-wikilinks|wiki-prepass)'` über das Repo (ohne `.git`). Jede Fundstelle klassifizieren als **(A) Live-Pfad-Aussage** (behauptet aktuellen Ablageort) → editieren zu `skills/wiki-ingest/scripts/…`, oder **(B) Historie/Allowlist** (PR-Record, Changelog/„New:", Current-State-Inventory in `docs/upstream-roadmap.md`; „matches lib/vault_root.sh"-Docstrings in `PLAN-sh-to-py`; die eigenen Vorhaben-Docs `docs/{prds,specs,test-designs,adr,plans,manifests}`) → **unangetastet lassen** (Editieren würde Historie verfälschen). Nach Befund: aktuell sind **alle** verbleibenden Fundstellen Klasse (B) → voraussichtlich **0 Edits**. Human-Gate 1 bestätigt diese Einstufung.
→ verify: Liste aller Fundstellen mit Klassifizierung (A/B) liegt vor; Anzahl (A) == Anzahl vorgenommener Edits.

**S6 — (bedingt) Live-Pfad-Refs editieren**
Aktion: nur falls S5 Klasse-(A)-Treffer ergab: `scripts/<name>.py` → `skills/wiki-ingest/scripts/<name>.py` an genau diesen Stellen. Sonst überspringen.
→ verify: pro Edit zeigt `git diff` ausschließlich den Pfad-Tausch (keine Sinnänderung); falls übersprungen: dokumentiert „keine Klasse-(A)-Treffer".

**S7 — Smoke-Gate: keine toten Live-Pfade**
Aktion: (a) `rg -n 'scripts/(rewrite-wikilinks|wiki-prepass)' README.md AGENTS.md GEMINI.md Makefile` ; (b) `rg -n 'scripts/(rewrite-wikilinks|wiki-prepass)' docs/` und Ergebnis gegen die Klasse-(B)-Allowlist (Historie/Vorhaben-Docs) prüfen.
→ verify: (a) == 0 Treffer; (b) enthält ausschließlich Klasse-(B)-Fundstellen (upstream-roadmap-Historie + Vorhaben-Docs), keine Live-Pfad-Behauptung „liegt unter `scripts/`".

**S8 — Contract-Checks (nur verifizieren, KEIN Edit)**
Aktion: bestätige, dass `skills/wiki-ingest/SKILL.md` und `skills/wiki/references/frontmatter.md` keinen der beiden Skriptpfade nennen; bestätige, dass wiki-prepass weiterhin `status: seed` + tag `prepass-seed` produziert (aus S4-JSON ableitbar bzw. per `rg 'status.*seed|prepass-seed' skills/wiki-ingest/scripts/wiki-prepass.py`).
→ verify: `rg 'rewrite-wikilinks|wiki-prepass' skills/wiki-ingest/SKILL.md skills/wiki/references/frontmatter.md` == 0; Stub-Frontmatter-Felder unverändert vorhanden.

**S9 — (optional, `should`) Within-Cluster-Dedup von `resolve_vault()` — NUR bei bewiesener Präzedenz-Erhaltung**
Aktion: Standard = **DEFER** (siehe §Dedup-Entscheidung). Falls dennoch ausgeführt: gemeinsamen Helper mit **exakt** `cli_arg → KM_VAULT_PATH → CWD` + „erster existierender Pfad, sonst `SystemExit`" bereitstellen; `lib/vault_root.resolve_vault_root()` (env-first) **nicht** übernehmen; kein neues Duplikat in `lib/`. Danach zwingend S4 erneut.
→ verify: Nur wenn ausgeführt — ein Präzedenz-Unit-Test (env gesetzt **und** cli_arg gesetzt → cli_arg gewinnt) grün; S4-Verhaltens-Parität weiterhin leer-Diff. Wenn übersprungen: dokumentiert „per-Skript belassen (pure refactor > DRY)".

**S10 — (optional, kosmetisch) Docstring `lib/vault_root.sh` → `.py`**
Aktion: nur falls gewünscht; nicht blockierend. Ändert die „(matches lib/vault_root.sh)"-Kommentarzeile.
→ verify: `git diff` zeigt nur Kommentartext; S3-Byte-Identität ist dann bewusst nicht mehr erfüllt → statt dessen S4 maßgeblich.

**S11 — Volle Regressions-Suite**
Aktion: `make test` im Repo-Root ausführen (10 Testdateien; kein Test referenziert diese Skripte → reiner Regressionsnachweis).
→ verify: Abschlusszeile „All tests passed."; Exit `0`. (Fallback falls jemand pytest hat: `python3 -m pytest tests/` grün — nicht erforderlich.)

**S12 — Commit (Human-Gate 2 davor)**
Aktion: nach Freigabe ein atomarer Commit (conventional): `refactor(ingest): co-locate rewrite-wikilinks + wiki-prepass under skills/wiki-ingest/scripts (ADR-0002)`. Kein Push ohne separate Freigabe.
→ verify: `git show --stat` zeigt genau die 2 Renames (+ evtl. Klasse-(A)-Doc-Edits / optionale S9/S10-Änderungen); Arbeitsbaum danach clean.

## Abhängigkeiten / Reihenfolge  ‹Wann / Womit›

**Tools/Deps:** `git` (mv/hash-object/diff), `rg`, `python3` (stdlib; **kein** pytest), `make`. **Fixture-Vault** für S1/S4: minimaler tmp-Vault unter `$SCRATCH` mit `wiki/`-Seite(n) inkl. `[[wikilink]]` + kleiner `mapping.tsv`, und `.raw/*.md` mit ≥1 wiederholter Großschreib-Nominalphrase (≥ threshold 3) für prepass; identisch für pre/post. (Nur Leseeingabe + Dry-Run → keine Vault-Mutation.)

**Interne Reihenfolge:** S0→S1→S2→S3→S4 strikt sequenziell (Baseline muss vor Move stehen). S5→S7 nach dem Move. S8 unabhängig nach Move. S9/S10 optional, wenn gewählt **vor** S11. S11 als letztes Gate vor S12.

**Cluster-übergreifend (INJECT):**
- **Parallel-sicher** mit den Clustern *lint* / *commands* / *setup*: dieser Cluster teilt **kein** Zielverzeichnis mit ihnen (Ziel = `skills/wiki-ingest/scripts/`). Kann unabhängig laufen/committen.
- **Downstream-Kopplung:** *tasks-dragonscale* hängt von *tasks-ingest* ab — `allocate-address.py` landet **ebenfalls** in `skills/wiki-ingest/scripts/`. Daher **erst diesen ingest-Move abschließen**, dann dragonscale. Kein Konflikt auf denselben *Dateien* (andere Skripte), aber gemeinsames *Zielverzeichnis* → ingest legt es an, dragonscale baut darauf auf. Reihenfolge: **ingest vor dragonscale**.

## Risiken & Rollback

- **R1 — `git mv` verliert Ausführ-Bit / Inhalt driftet.** → verhindert durch S3 (hash-object + Mode-Check). Rollback: `git mv` zurück nach `scripts/` bzw. `git checkout -- <pfad>`; vor Commit reversibel ohne Historie.
- **R2 — Verhaltensänderung durch Ablageort (CWD/`__file__`).** Nach Befund ausgeschlossen (CWD-unabhängig, kein `__file__`). Absicherung: S4-Parität. Rollback: revert Move.
- **R3 — Fälschliches Editieren historischer Refs** (`upstream-roadmap`-Historie / Vorhaben-Docs) → verfälscht Aufzeichnungen. Verhindert durch S5-Klassifizierung + Human-Gate 1. Rollback: `git checkout -- docs/…` für irrtümliche Edits.
- **R4 — Optionaler Dedup ändert Präzedenz** (env-first statt cli-first) = stiller Verhaltensbruch. Verhindert durch DEFER-Default + S9-Präzedenztest + erneutes S4. Rollback: Inline-Kopien wiederherstellen (`git checkout`).
- **R5 — „pytest grün" nicht erfüllbar** (pytest fehlt). Aufgelöst: Gate = `make test` (stdlib unittest). Kein Rollback nötig; Doku in Done-Definition.
- **R6 — Vorbestehende, NICHT durch diesen Refactor verursachte Dangling-Refs** (`scripts/lint/lint-open-issues.py` etc., siehe Test-Design §Quality-Gate) → **separat führen**, nicht in diesem Move „mitfixen" (Surgical-Changes-Regel).
- **Gesamt-Backout:** ein Commit → `git revert <commit>` stellt Ablageort + evtl. Refs risikofrei wieder her (keine Importe/Konsumenten betroffen).

## Human-Gates  ‹Wann: Freigabe›

- [ ] **HG0 (vor S1):** Sauberer Baum auf `main` bestätigt; die bereits offenen `git status`-Einträge (`.cursor`/`.windsurf`/`skills/visualize`) sind cluster-fremd und werden nicht mitverändert.
- [ ] **HG1 (nach S5, vor S6):** Freigabe der Ref-Klassifizierung — Bestätigung, dass die verbleibenden `scripts/…`-Fundstellen Historie/Allowlist (Klasse B) sind und **nicht** editiert werden (erwartet: 0 Live-Pfad-Edits).
- [ ] **HG2 (vor S12):** Freigabe des Dedup-Entscheids (DEFER vs. ausführen) **und** des Commits. Kein `git push` ohne separate, ausdrückliche Freigabe.

## Dedup-Entscheidung  ‹Womit›

**DEFER (per-Skript belassen).** Begründung: `resolve_vault()` ist byte-identisch dupliziert, aber die Cluster-Präzedenz **`cli_arg → KM_VAULT_PATH → CWD`** divergiert bewusst von `lib/vault_root.py` (**env-first**). Der Vertrag dieses Vorhabens ist **ZERO behavior change**; ein Dedup ist nur `should`, nicht `must`. „Pure refactor (nur Move) > DRY": den verhaltensneutralen Move nicht mit einer verhaltens-sensiblen Konsolidierung koppeln. Dedup bleibt möglich (S9) — nur mit Präzedenz-Beweis (Unit-Test) + erneuter S4-Parität, koordiniert mit spec-lint/spec-dragonscale, und **nicht** durch Übernahme von `resolve_vault_root()`.

---
### Checkliste
- [x] Done-Definition konkret  ‹Wann-erledigt›  (byte-/Verhaltens-Diff, Existenz-Gates, `make test` grün, 0 tote Live-Refs)
- [x] Jeder Schritt hat einen Verify-Check  ‹Wie›  (S0–S12, deterministisch)
- [x] Riskante Schritte haben Rollback  (R1–R6 + Gesamt-Backout)
- [x] Human-Gates markiert  ‹Wann›  (HG0/HG1/HG2)
- [x] Schritte atomar genug → werden zu Tasks
- [x] 7-W-Abdeckung geprüft
- [x] Ehrlichkeits-Punkte offengelegt: pytest fehlt → `make test`; Spec-Zeilennummern veraltet → Live-`rg` maßgeblich; verbleibende Doc-Refs sind Historie → 0 erwartete Live-Edits; Dedup = DEFER
