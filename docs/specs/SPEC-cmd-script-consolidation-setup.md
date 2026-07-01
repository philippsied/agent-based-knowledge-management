---
artifact: spec
slug: cmd-script-consolidation
module: setup
status: draft
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [prd, adr-0002]
---

# Spec — setup-Cluster (bin/) konsolidieren [setup]

> WIE konsolidieren wir die Installer-Familie in `bin/` — und gehört sie unter einen Skill?
> **Anker (7 W):** Wie · Womit · [PRD](../prds/cmd-script-consolidation.md) · [ADR-0002](../adr/0002-colocate-scripts-under-skill.md)

## 1. Ziel & Kontext  ‹Was/Warum → PRD›
Installer-Familie (~479 LOC über drei Skripte) inhaltlich konsolidieren und Ownership **entscheiden** (offene Frage aus ADR-0002: `skills/wiki/scripts/` vs. `bin/` behalten). Reiner Refactor: identisches Verhalten (gleiche Inputs → gleiche Outputs, gleiche Exit-Codes, gleiche geschriebene Dateien), keine neuen Features (PRD §4 Out).

**Befund aus Code (Evidenz):** Die drei Skripte teilen KEINEN gemeinsamen Vault-Root-Resolver. `setup-vault.py` und `setup-dragonscale.py` duplizieren beide wortgleich das Inline-Idiom `vault = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR.parent` — und dieses weicht vom kanonischen `lib/vault_root.py::resolve_vault_root()` (Kette `KM_VAULT_PATH` env → argv → cwd) ab, das jedes Lint-/DragonScale-Skript importiert. Das ist die einzige echte, sinnvoll deduplizierbare Logik. `setup-multi-agent.py` operiert auf `REPO_ROOT` (kein Vault-Argument, andere Concern: Skill-Symlinks) und teilt nichts mit den anderen beiden.

## 2. Schnittstellen / Verträge  ‹Womit›

### 2.1 Die drei Skripte (Ist-Zustand, verifiziert am Code)

| Skript | LOC | Entrypoint | Vault-/Root-Auflösung | Was es einrichtet |
|---|--:|---|---|---|
| `bin/setup-vault.py` | 214 | `main()` unter `if __name__ == "__main__"`; `download(url, dest)` Helper | `vault = argv[1] else SCRIPT_DIR.parent` (inline) | Vault-Skelett (`wiki/{concepts,entities,sources,meta}`, `_templates/`, `.vault-meta/`); idempotente DragonScale-State-Dateien (`address-counter.txt`, `legacy-pages.txt`); path-safety `config.json` (TTY-gated `strict`/`mixed`); Obsidian-Config (`graph.json`, `app.json`, `appearance.json`); Download zweier Plugin-Binaries (Excalidraw `main.js`, Thino v1.9.7); Post-Setup-Guidance |
| `bin/setup-dragonscale.py` | 163 | `main()` unter `if __name__ == "__main__"` | `vault = argv[1] else SCRIPT_DIR.parent` (inline, **identisch zu vault**) | Opt-in DragonScale-Runtime: verifiziert mitgelieferte Artefakte (`scripts/allocate-address.py`, `scripts/tiling-check.py`, `skills/wiki-fold/SKILL.md`), `chmod 0o755`; provisioniert `.vault-meta/` (`address-counter.txt`, `legacy-pages.txt`, `tiling-thresholds.json`); `.raw/.manifest.json`; Rollout-Baseline-Marker; Sanity-Checks |
| `bin/setup-multi-agent.py` | 102 | `main()` unter `if __name__ == "__main__"`; `link_if_missing(target, dest, agent_name)` Helper | `REPO_ROOT = SCRIPT_DIR.parent`, `SKILLS_DIR = REPO_ROOT/"skills"` (**kein Vault-Argument**) | Symlinkt `skills/` in Agent-Homes (Codex `~/.codex/skills/…`, OpenCode, Gemini, Cursor `.cursor/skills`, Windsurf `.windsurf/skills`); idempotent (prüft bestehende Symlinks) |

### 2.2 Geteilte Logik → gemeinsames Modul

| Kandidat | In welchen Skripten | Deduplizierung |
|---|---|---|
| **Vault-Root-Auflösung** `argv[1] else SCRIPT_DIR.parent` | `setup-vault.py`, `setup-dragonscale.py` (wortgleich) | **Auf `lib/vault_root.py::resolve_vault_root()` umstellen** (bereits vorhanden, env→argv→cwd). Import-Muster identisch zu den Lint-Skripten: `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib")); from vault_root import resolve_vault_root`. **Achtung Verhaltens-Delta:** `resolve_vault_root()` fällt auf `cwd` (statt `SCRIPT_DIR.parent`) zurück, wenn `KM_VAULT_PATH`/argv fehlen. Für den dokumentierten Aufruf `python3 bin/setup-*.py` aus dem Repo-Root sind `cwd` und `SCRIPT_DIR.parent` identisch → verhaltensneutral. Falls das Nutzungsprofil "aus beliebigem cwd ohne Argument" existiert (nicht in Docs belegt), wäre es ein Delta → **vor Umstellung im Test verifizieren** (§6), sonst statt `resolve_vault_root()` das Idiom in einen shared Helper mit `SCRIPT_DIR.parent`-Fallback extrahieren. |
| **Idempotentes `.vault-meta/`-State-Scaffolding** (`address-counter.txt`, `legacy-pages.txt` mit `if not …is_file()`-Guard) | `setup-vault.py` (1a), `setup-dragonscale.py` (2/4) | Kandidat für einen Helper (`scaffold_dragonscale_state(vault)`), ABER die beiden Vorkommen unterscheiden sich (vault schreibt nur Counter+Legacy; dragonscale schreibt zusätzlich `tiling-thresholds.json`, `.raw/.manifest.json`, Rollout-Baseline). **Nur den exakt deckungsgleichen Teil** deduplizieren; abweichende Teile bleiben skript-lokal. Wenn die gemeinsame Schnittmenge < ~10 LOC ist, Deduplizierung NICHT erzwingen (CLAUDE.md §2: keine Abstraktion für Einmal-Nutzung). |

**Ziel des shared Moduls:** `bin/` (nicht `lib/`) — siehe Ownership-Entscheidung §4. `lib/vault_root.py` bleibt der Ort des Resolvers (existiert bereits, wird nur importiert). Ein etwaiges neues Setup-Helper-Modul lebt als `bin/_setup_common.py` neben den Skripten, weil es ausschließlich von Install-Tooling in `bin/` genutzt wird.

### 2.3 Aufrufer (verifiziert per Grep über `docs/`, `Makefile`, Root-Markdown)

| Aufrufer | Zeile(n) | Skript | Art |
|---|---|---|---|
| `Makefile` | L21 (help), L79–80 (target `setup-dragonscale`) | `setup-dragonscale.py` | Make-Target (`@python3 bin/setup-dragonscale.py`) |
| `README.md` | L68, L213 | `setup-vault.py` | User-Doc (Bootstrap-Befehl) |
| `docs/install-guide.md` | L37, L217 | `setup-vault.py` | User-Doc |
| `docs/dragonscale-guide.md` | L13, L37, L44, L48, L105, L110, L507, L564 | `setup-vault.py` (L37), `setup-dragonscale.py` (übrige) | User-Doc |
| `AGENTS.md` | L22 | `setup-multi-agent.py` | Bootstrap-Doc |
| `GEMINI.md` | L16 | `setup-multi-agent.py` | Bootstrap-Doc |

**Kein Test und kein Skill (`SKILL.md`) ruft `bin/setup-*` auf.** Alle Aufrufe sind entweder User-Bootstrap-Befehle vor der ersten Skill-/Obsidian-Nutzung oder das eine Make-Target. Belegt die Einordnung als Install-Tooling.

Out-of-scope (PRD §4, ADR-0002): `release.py`, `sync-versions.py` — nicht anfassen.

## 3. Verhalten  ‹Wie›
Vertrag: **byte-identisches Verhalten** vor/nach Refactor. Der Refactor tauscht nur die Root-Auflösung gegen den kanonischen Resolver und extrahiert ggf. exakt deckungsgleichen State-Scaffolding-Code; er ändert keine geschriebenen Datei-Inhalte, keine Exit-Codes, keine Prompt-Texte.

### Happy path
- `python3 bin/setup-vault.py` (aus Repo-Root, ohne Arg): legt Vault-Skelett + State + `config.json` + Obsidian-Config an, lädt Binaries, druckt Guidance, Exit 0. Identisch zu vorher.
- `python3 bin/setup-dragonscale.py [/pfad/zum/vault]`: verifiziert Artefakte, provisioniert `.vault-meta/`, Exit 0.
- `python3 bin/setup-multi-agent.py`: symlinkt `skills/` in alle Agent-Homes, Exit 0.
- Argument-Override `python3 bin/setup-*.py /path/to/vault` funktioniert wie zuvor (argv[1] hat Vorrang — bleibt bei `resolve_vault_root()` erhalten).

### Edge-Cases (Idempotenz)
- Erneuter Lauf jedes Skripts ist ein No-Op auf bereits existierenden Dateien: `if not …is_file()`-Guards (State), Symlink-Existenzprüfung (`link_if_missing`), vorhandene `config.json` wird **nicht** überschrieben. Muss nach Refactor unverändert gelten.
- `config.json`-Scaffolding: TTY-interaktiv → Prompt (`strict`/`mixed`); non-interaktiv (`not sys.stdin.isatty()`) → Default `strict`, kein Prompt. **Intakt lassen** (§7).
- Root-Auflösung ohne Arg aus Repo-Root: `cwd == SCRIPT_DIR.parent` → Resolver liefert dieselbe Wurzel. (Delta nur, falls aus fremdem cwd ohne Arg aufgerufen — §2.2.)

### Fehlerbehandlung
- `setup-dragonscale.py`: fehlendes Pflicht-Artefakt → `stderr` + `sys.exit(1)`. Unverändert.
- `setup-multi-agent.py`: fehlendes `skills/`-Verzeichnis → Fehlermeldung. Unverändert.
- `setup-vault.py` Download-Fehler (`download()` via `subprocess`/curl): bestehendes Verhalten unverändert übernehmen — keine neue Fehlerbehandlung hinzufügen (CLAUDE.md §2).

## 4. Gewählter Ansatz  ‹Wie›

### 4.1 Ownership-Entscheidung: **`bin/` behalten** (nicht unter Skill verschieben)
**Entscheidung:** Alle drei Skripte bleiben in `bin/`.

**Begründung (nach "wer ruft, und wann"):**
1. **Bootstrap vor Skill-Existenz.** `setup-multi-agent.py` symlinkt `skills/` überhaupt erst in die Agent-Homes — es kann nicht in dem Verzeichnis wohnen, das es installiert (Henne-Ei). `setup-vault.py` läuft laut README/Install-Guide "einmal vor dem ersten Obsidian-Öffnen", also bevor irgendein Skill genutzt wird.
2. **Aufgerufen außerhalb von Skills.** Alle Aufrufer (§2.3) sind User-Bootstrap-Befehle + ein `Makefile`-Target; kein `SKILL.md`, kein Test ruft sie auf. Damit sind sie Install-/Release-Tooling, genau die Kategorie, die ADR-0002 selbst in `bin/` belässt (`release.py`, `sync-versions.py`).
3. **ADR-0002 lässt genau dies offen.** Das Ziel-Mapping der ADR listet `setup-vault/dragonscale/multi-agent` explizit als „`skills/wiki/scripts/` *oder* `bin/` behalten — spec-setup entscheidet". Diese Spec entscheidet: `bin/`.

**Abweichung vom ADR-0002-Default → ADR-Ergänzung nötig.** Der ADR-Default ist „Skript unter besitzenden Skill". Diese Entscheidung weicht bewusst ab. Deshalb: **Addendum an ADR-0002** (kurzer Abschnitt „Ausnahme: Install-Bootstrap-Tooling bleibt in `bin/`", mit den drei Gründen oben und der Analogie zu `release.py`). Kein neuer ADR — nur Ergänzung, da deckungsgleich mit der bereits dokumentierten `release.py`-Ausnahme.

### 4.2 Deduplizierung
- **P1 (sicher):** In `setup-vault.py` + `setup-dragonscale.py` die duplizierte Inline-Root-Auflösung durch Import von `lib/vault_root.py::resolve_vault_root()` ersetzen — nach vorheriger Verifikation des cwd-Fallback-Deltas (§2.2, §6). Vereinheitlicht die drei Skripte + alle Lint-Skripte auf **eine** Resolver-Quelle.
- **P2 (optional, nur bei echter Schnittmenge):** Deckungsgleiches `.vault-meta/`-State-Scaffolding in `bin/_setup_common.py` extrahieren. Nur ausführen, wenn die gemeinsame Schnittmenge groß genug ist, dass Deduplizierung Netto-Vereinfachung bringt; sonst weglassen (CLAUDE.md §2/§3). `setup-multi-agent.py` bleibt unberührt (teilt nichts).

### 4.3 Referenz-Updates
Da Ownership = `bin/`, **ändern sich keine Pfade** → die Aufrufer in §2.3 müssen NICHT umgeschrieben werden (Pfade bleiben `bin/setup-*.py`). Zu aktualisieren ist nur, was sich durch den Refactor tatsächlich ändert:
- **ADR-0002:** Addendum (§4.1).
- **`docs/manifests/cmd-script-consolidation.json`** + **`docs/test-designs/cmd-script-consolidation.md`**: Status/Smoke-Eintrag für Modul `setup` (existieren beide).
- Falls P1 den kanonischen Resolver einführt: kein Doc-Update nötig (interne Implementierung).

**Explizit NICHT in Scope dieser Spec:** die veralteten `bin/setup-*.sh`-Erwähnungen in historischen Docs (`docs/influence-log.md`, `docs/releases/v1.6.0.md`, diverse `docs/plans/*`, `docs/upstream-roadmap.md`) — das sind abgeschlossene Migrations-/Release-Artefakte, kein aktueller Aufruf-Pfad; anfassen wäre Scope-Creep (CLAUDE.md §3).

## 5. Acceptance-Criteria (binär, testbar)  ‹Wann-erledigt›
- [ ] **Ownership entschieden + dokumentiert:** Entscheidung = `bin/` (§4.1) steht in dieser Spec; ADR-0002 hat ein Addendum, das die Abweichung vom Colocate-Default begründet. (Verifikation: `rg -n "bin/" docs/adr/0002-colocate-scripts-under-skill.md` findet den Addendum-Abschnitt.)
- [ ] **Geteilte Logik dedupliziert:** `setup-vault.py` und `setup-dragonscale.py` enthalten die Inline-Zeile `vault = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR.parent` nicht mehr, sondern importieren `resolve_vault_root`. (Verifikation: `rg -c "resolve_vault_root" bin/setup-vault.py bin/setup-dragonscale.py` == 1 je Datei; das alte Idiom per `rg` nicht mehr auffindbar.) P2 nur akzeptanzrelevant, falls durchgeführt.
- [ ] **Aufrufer korrekt:** Alle Aufrufer aus §2.3 zeigen weiterhin auf `bin/setup-*.py` und funktionieren (keine Pfadänderung, da `bin/` behalten). (Verifikation: `make setup-dragonscale` läuft ohne Fehler; `rg "bin/setup-(vault|dragonscale|multi-agent)\.py" README.md docs/install-guide.md AGENTS.md GEMINI.md Makefile` liefert die erwarteten Treffer.)
- [ ] **Setup end-to-end idempotent gegen tmp-Vault:** In einem frischen `$TMPDIR`-Vault laufen alle drei Skripte fehlerfrei (Exit 0); ein **zweiter** Lauf ist ein No-Op (keine Datei-Änderung, `git`/Diff bzw. mtime-Vergleich leer). Die vor dem Refactor erzeugten Dateien/Inhalte sind byte-identisch zu den danach erzeugten (Golden-Vergleich). (Verifikation: Smoke-Skript aus test-design, siehe §6.)
- [ ] **Path-safety-Constraint gehalten:** `config.json`-Scaffolding-Logik (strict/mixed, TTY-gated) in `setup-vault.py` unverändert; `hooks/wiki-path-safety.py` unangetastet. (Verifikation: `git diff -- hooks/wiki-path-safety.py` leer; `config.json`-Block per Diff nur formal, nicht inhaltlich verändert.)

## 6. Test-Design  ‹Wann-erledigt›
→ [test-design](../test-designs/cmd-script-consolidation.md) (Smoke: setup gegen tmp-Vault)

Modul-spezifische Smoke-Schritte:
1. **Golden-Vergleich (Verhaltens-Identität):** vor Refactor jeden Setup-Lauf gegen frischen `$TMPDIR`-Vault ausführen und Ausgabe-Baum + Datei-Inhalte snapshotten; nach Refactor wiederholen; Bäume müssen byte-identisch sein.
2. **Idempotenz:** jedes Skript zweimal laufen lassen; zweiter Lauf darf keine Datei-mtimes/-Inhalte ändern.
3. **cwd-Fallback-Delta (Gate für P1):** `resolve_vault_root()` vs. `SCRIPT_DIR.parent` im dokumentierten Aufruf (Repo-Root, ohne Arg) vergleichen → müssen dieselbe Wurzel liefern, bevor P1 gemergt wird.
4. **Argument-Override:** `setup-*.py /tmp/x` schreibt nach `/tmp/x`, nicht nach Repo-Root.

## 7. Security / Privacy  ‹Womit›
**Constraint (PRD §4, hart):** Kein Redesign von `hooks/wiki-path-safety.py`. Verifiziert: **keines** der drei Setup-Skripte installiert oder modifiziert die Hook-Datei selbst. `setup-vault.py` scaffoldt lediglich `.vault-meta/config.json` (`version:1`, `path_safety_mode` `strict`|`mixed`), die der Hook zur Laufzeit liest. Diese Scaffolding-Logik (inkl. TTY-gated Prompt, Default `strict`) bleibt **inhaltlich unverändert** — der Refactor berührt nur Root-Auflösung/State-Dedup, nicht den `config.json`-Block. Downloads (`setup-vault.py`) und Symlink-Ziele (`setup-multi-agent.py`) bleiben unverändert; keine neuen Netzwerk-/FS-Angriffsflächen.

## 8. Rollout / Migration / Backout  ‹Wann›
- **Rollout:** ein Commit (P1 Resolver-Dedup + ADR-Addendum), optional zweiter Commit für P2 State-Helper. Kein Pfadwechsel → keine Nutzer-Migration nötig.
- **Backout:** `git revert` des/der Commits. Setup ist idempotent, daher folgenlos re-runnbar; kein Zustands-Rollback im Vault erforderlich (erzeugte `.vault-meta/`-Dateien bleiben gültig).

---
### Checkliste (vor status: approved)
- [x] Ownership entschieden (`bin/`, §4.1) · [x] Aufrufer-Referenzen erfasst + Pfad-Konstanz begründet (§2.3, §4.3) · [x] Acceptance binär/testbar (§5) · [x] 7-W geprüft (Wie/Womit/Wann-erledigt/Was-nicht abgedeckt)
- [ ] ADR-0002-Addendum geschrieben (Umsetzungs-Schritt, nicht Spec-intern) · [ ] cwd-Fallback-Delta im Test verifiziert (Gate für P1)
