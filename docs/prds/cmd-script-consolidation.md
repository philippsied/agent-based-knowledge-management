---
artifact: prd
slug: cmd-script-consolidation
status: approved        # draft | review | approved
manifest: docs/manifests/cmd-script-consolidation.json
---

# PRD — Commands→Skills-Integration + Skript-Konsolidierung

> Beantwortet: WAS bauen wir & WARUM? Für wen? Woran messen wir Erfolg?
> **Kein WIE** — Implementierung in den Modul-Specs (`docs/specs/SPEC-cmd-script-consolidation-*.md`).
> **Anker (7 W):** Warum · Was · Was-nicht · Wann-erledigt · Womit — kein Wie.

## 1. Problem & Evidenz  ‹Warum›

Zwei Duplikations-/Kopplungsherde, verifiziert am Repo-Stand:

**Commands doppeln Skills.** 7 command-Dateien, 5 davon dünne Router die einen gleichnamigen
Skill duplizieren; 2 fett mit echter Logik:

| command | Zeilen | delegiert an Skill? | Befund |
|---|--:|---|---|
| `commands/autoresearch.md` | 19 | ✓ `skills/autoresearch` | dünner Router |
| `commands/wiki.md` | 23 | ✓ `skills/wiki` | dünner Router |
| `commands/doc-pipeline.md` | 25 | ✓ `skills/doc-pipeline` (+scripts) | dünner Router |
| `commands/canvas.md` | 21 | erwähnt Skill 1× | prüfen: deckt Skill alles? |
| `commands/save.md` | 16 | erwähnt Skill 1× | prüfen: deckt Skill alles? |
| `commands/wiki/fix-issues.md` | 211 | — | **fette Logik**, überlappt `wiki-lint` (fix-forward) |
| `commands/wiki/handoff.md` | 126 | — | **fette Logik, KEIN backing Skill** |

Folge: Logik driftet zwischen command und Skill; zwei Wartungsorte. `plugin.json` +
`marketplace.json` enumerieren commands/skills **nicht** (Auto-Discovery per Konvention) →
Löschen von `commands/` erfordert keine Manifest-Änderung.

**Skripte gekoppelt aber flach + skill-fern.** 12 Top-Level-Skripte + 5 in `bin/` (~3745 LOC),
starke Intra-Cluster-Kopplung, aber flach in `scripts/` statt beim besitzenden Skill.
`skills/doc-pipeline/scripts/` zeigt bereits das Co-locate-Muster.

| Cluster | Skripte | LOC | Kopplung (verifiziert) |
|---|---|--:|---|
| **lint** | `run-lint`(684) + `lint-orphans`(129) `lint-terminology`(269) `lint-title-overlap`(118) `lint-deps`(265) `lint-programs`(237) + `lint-rename`(119) | ~1421 | `run-lint.py` importiert 5 linters **in-process** via `collect*`; `lint-rename` standalone |
| **dragonscale** | `boundary-score`(316) `tiling-check`(500) `allocate-address`(153) | ~969 | DragonScale-Feature-Familie, geteilte Utilities |
| **ingest** | `rewrite-wikilinks`(118) `wiki-prepass`(210) | ~328 | Ingest-Zeit-Transforms |
| **setup (bin/)** | `setup-vault`(214) `setup-dragonscale`(163) `setup-multi-agent`(102) | ~479 | Installer-Familie |
| shared | `lib/vault_root.py` | — | von mehreren genutzt → bleibt `lib/` |
| out-of-scope | `bin/release.py`(110) `bin/sync-versions.py`(38) | — | Release-Tooling, geringe Kopplung |

## 2. Zielnutzer / Begünstigte  ‹Was: für wen›

Primär: Plugin-Maintainer (philippsied) — weniger Wartungsoberfläche, klare Ownership.
Sekundär: Downstream-Nutzer die Skills invoken (Verhalten muss identisch bleiben).

## 3. Ziele & Erfolgsmetriken  ‹Wann-erledigt›

| Ziel | Metrik (messbar) | Zielwert |
|---|---|---|
| Commands funktional in Skills aufgegangen | `fd . commands/` = 0 Dateien **und** Coverage-Matrix jedes command-Verhaltens = ✓ | 0 Dateien / 100 % gedeckt |
| Gekoppelte Skripte konsolidiert + co-located | jeder Cluster unter besitzendem Skill (bzw. `lib/` wenn shared) | 4/4 Cluster verortet |
| Verhalten erhalten (reiner Refactor) | `pytest tests/` + 2 eval-Suites grün | 100 % pass |
| lint-Ergebnis unverändert | `run-lint --json` pre/post gegen Fixture-Vault | diff leer |
| Keine toten internen Referenzen | `rg` auf `commands/` + alte Skript-Pfade in README/AGENTS/GEMINI/Makefile/docs/SKILL.md | 0 Treffer |

## 4. Scope  ‹Was / Was-nicht›

**In:**
- Command-Funktionalität in Skills migrieren, dann `commands/` löschen (Migration VOR Löschung).
- `handoff` (kein Skill) → Skill-Heimat schaffen (neuer Skill oder Fold in `wiki`/`wiki-lint`) — verifizieren dass kein bestehender externer `handoff`-Skill dupliziert wird.
- `fix-issues` → `wiki-lint` fix-forward.
- lint / dragonscale / ingest / setup Cluster: inhaltlich konsolidieren + unter besitzenden Skill co-located; shared → `lib/`.
- Alle internen Pfad-Referenzen aktualisieren.
- Test-Coverage für geänderte Import-Pfade.

**Out (Non-Goals):**
- Keine Verhaltensänderung an Skills/Skripten (reiner Refactor: gleiche Inputs → gleiche Outputs).
- Keine neuen Features.
- `release.py` / `sync-versions.py` nicht konsolidiert (separate Concern, geringe Kopplung).
- Kein Redesign von `hooks/wiki-path-safety.py` (Constraint: intakt lassen).
- Keine Änderung an Vault-Inhalten / Wiki-Daten.

## 5. Anforderungen (priorisiert)  ‹Was›

- [must] Jedes command-Verhalten VOR Löschung nachweislich in einem Skill vorhanden (Coverage-Matrix).
- [must] `handoff` bekommt Skill-Heimat; `fix-issues`-Logik → `wiki-lint`.
- [must] Gekoppelte Skripte co-located unter besitzendem Skill; shared → `lib/`.
- [must] Alle internen Pfad-Referenzen aktualisiert (README, AGENTS, GEMINI, Makefile, docs, SKILL.md).
- [must] `pytest tests/` + evals grün; Import-Pfad-Änderungen (importlib in `run-lint.py`, `tests/test_run_lint.py`) mitgezogen.
- [should] Innerhalb Cluster Duplikat-Logik konsolidieren (nicht nur Dateien verschieben).
- [could] setup-Cluster (`bin/`) vereinheitlichen.

## 6. Constraints & Annahmen  ‹Womit›

- Claude Code entdeckt `skills/` + `commands/` per Konvention; Löschen von `commands/` = Verlust der `/slash`-UX (akzeptiert, [ADR-0001](../adr/0001-delete-commands-skills-only.md)).
- `lint-*.py` sind bindestrich-benannt, geladen via `importlib.util.spec_from_file_location` (nicht normal importierbar) → Verschieben muss Ladepfade in `run-lint.py` + `tests/test_run_lint.py` erhalten.
- `lib/vault_root.py` = shared Root-Resolver → bleibt `lib/`.
- Bestehende Tests (10 in `tests/`) + Evals (`autoresearch`, `research-brief`) = Regressions-Netz.

## 7. Risiken & offene Fragen

- **Risk:** Verschieben von `lint-*.py` bricht `importlib`-Pfade in `run-lint.py` + Tests. → Pfade + Tests gemeinsam ziehen (spec-lint).
- **Risk:** `dragonscale`-Cluster spannt 3 Skills (boundary→autoresearch, tiling→wiki-lint, allocate→wiki-ingest) → "co-locate" splittet Cluster; geteilte DragonScale-Util braucht `lib/`-Modul (spec-dragonscale, ADR-0002).
- **Risk:** `handoff` ohne Skill → Scope-Creep durch neuen Skill. → Fold-vs-neu in spec-commands entscheiden.
- **Offen:** dupliziert `commands/wiki/handoff.md` den externen `handoff`-Plugin-Skill (`cs-handoff`)? In spec-commands verifizieren — nicht neu bauen.

---
### Checkliste (vor status: approved)
- [x] Problem mit Evidenz, nicht Vermutung  ‹Warum›
- [x] Zielnutzer benannt  ‹Was›
- [x] Mind. 1 messbare Erfolgsmetrik mit Zielwert  ‹Wann-erledigt›
- [x] Non-Goals explizit  ‹Was-nicht›
- [x] Anforderungen priorisiert (must/should/could)
- [x] Kein Implementierungs-WIE enthalten (Mapping = Prinzip, Detail in Specs)
- [x] Offene Fragen gelistet
- [x] 7-W-Abdeckung geprüft (Wie → Specs, Wann/Reihenfolge → Plans)
