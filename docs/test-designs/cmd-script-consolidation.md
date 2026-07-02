---
artifact: test-design
slug: cmd-script-consolidation
status: approved
manifest: docs/manifests/cmd-script-consolidation.json
depends_on: [prd]
---

# Test-Design — Commands→Skills-Integration + Skript-Konsolidierung

> Reiner Refactor → Leitidee: **Verhalten bit-identisch, nur Struktur ändert sich.**
> **Anker (7 W):** Wann-erledigt (Acceptance→Test) · Wie (Test-Ebenen) · Womit (Quality-Gate)
> Aggregiert die Acceptance-Criteria der 5 Modul-Specs (commands · lint · dragonscale · ingest · setup).

## Ebenen  ‹Wie›
- **Unit:** verschobene `lint-*`/dragonscale-Module ladbar (importlib von neuem Pfad) + `collect*`/Adress-Fns identisch; `lib/`-Pfadtiefe korrekt (`from vault_root import …` lädt); `lib/dragonscale_pages.py` byte-identische Konstanten; `resolve_vault`-Präzedenz erhalten.
- **Integration:** `run-lint.py --json` identischer Report gegen Fixture-Vault pre/post; bestehende Tests grün via `make test` (10 unittest-Targets, KEIN pytest) + Evals (`autoresearch`, `research-brief`); `tiling-check` ollama-Skip (Exit 10/11) erhalten; `allocate-address --peek` read-only aus `wiki-lint` funktioniert.
- **Smoke:** jeder Skill lädt; `SKILL.md`-Referenzen resolven; verschobene Skripte per Basis-Aufruf lauffähig; `fd commands/` = 0; neuer Skill `wiki-issues` (push+pop) vorhanden; `bin/setup-*` idempotent gegen tmp-Vault.
- **Security:** `hooks/wiki-path-safety.py` unverändert; zugehöriger Test grün; kein setup-Skript modifiziert path-safety.

## Akzeptanz → Test Mapping  ‹Wann-erledigt›

### commands ([spec](../specs/SPEC-cmd-script-consolidation-commands.md))
| Acceptance-Criterion | Test | Ebene |
|---|---|---|
| `commands/` restlos entfernt | `fd . commands/` == 0 | Smoke |
| 5 Router: Verhalten via Skill-Trigger erreichbar (Coverage-Matrix ✓) | Skill-Trigger-Smoke je Skill | Smoke |
| neuer Skill `wiki-issues` mit PUSH+POP auf `wiki/meta/OPEN-ISSUES.md` | Skill lädt; Ops vorhanden; Datenmodell/Guardrails erhalten | Integration |
| `fix-issues`/`handoff`-Logik wortgetreu migriert | Vergleich Command-Body ↔ Skill-Body (Schritte/Formate) | Integration |
| `/commands`-Referenzen in docs/README aktualisiert | `rg 'commands/'` (ohne Historie/Vorhaben-Docs) == 0 | Smoke |

### lint ([spec](../specs/SPEC-cmd-script-consolidation-lint.md))
| Acceptance-Criterion | Test | Ebene |
|---|---|---|
| 7 lint-Skripte unter `skills/wiki-lint/scripts/` | `fd lint-*.py skills/wiki-lint/scripts/` == 6 + run-lint | Smoke |
| `run-lint --json` diff leer pre/post | Fixture-Vault diff | Integration |
| `REPO_ROOT`/Sub-Linter `lib`-Pfadtiefe korrigiert | Modul-Import lädt ohne `ModuleNotFoundError` | Unit |
| `tests/test_run_lint.py` + 3 lint-Tests grün mit neuen Pfaden | `make test` | Integration |
| Refs aktualisiert (Makefile, SKILL.md, release.py, evals/run.py) | `rg 'scripts/(run-lint\|lint-)'` alt == 0 | Smoke |

### dragonscale ([spec](../specs/SPEC-cmd-script-consolidation-dragonscale.md))
| Acceptance-Criterion | Test | Ebene |
|---|---|---|
| boundary→autoresearch, tiling→wiki-lint, allocate→wiki-ingest verortet | `fd` je Zielordner | Smoke |
| `lib/dragonscale_pages.py`: Konstanten+`log()` byte-identisch | Unit-Vergleich | Unit |
| divergente Fns per-Skript ODER Superset mit beiden Suiten grün | `make test-boundary test-tiling` | Unit |
| `sys.path`-Tiefe korrigiert | Import lädt | Unit |
| Konsumenten aktualisiert (SKILL.md, agents/, setup-dragonscale, Makefile, tests, docs) | `rg` alt-Pfade == 0 | Smoke |
| `tiling-check` ollama Exit 10/11 = Skip erhalten | Integration (ohne ollama) | Integration |
| `allocate-address --peek` read-only aus wiki-lint | Integration | Integration |

### ingest ([spec](../specs/SPEC-cmd-script-consolidation-ingest.md))
| Acceptance-Criterion | Test | Ebene |
|---|---|---|
| beide Skripte unter `skills/wiki-ingest/scripts/` | `fd` | Smoke |
| Referenzen aktualisiert (doc-layer; keine Skill-Pfad-Refs) | `rg` alt-Pfade == 0 | Smoke |
| `resolve_vault`-Dedup erhält Präzedenz ODER per-Skript belassen | Unit (Präzedenz-Reihenfolge) | Unit |
| volle Suite grün (Regressions-Check) | `make test` | Integration |

### setup ([spec](../specs/SPEC-cmd-script-consolidation-setup.md))
| Acceptance-Criterion | Test | Ebene |
|---|---|---|
| setup-* bleiben in `bin/` ([ADR-0003](../adr/0003-setup-cluster-stays-in-bin.md)) | Doc-Check | — |
| geteilte Resolver-Logik via `lib/vault_root`; `_setup_common` nur wenn non-trivial | Unit | Unit |
| setup end-to-end idempotent gegen tmp-Vault | Smoke | Smoke |
| `hooks/wiki-path-safety.py` unberührt | Security-Test | Security |

## Quality-Gate (numerisch)  ‹Womit›
- Bestehende Tests: **100 %** pass via `make test` (10 unittest-Targets; pytest NICHT installiert).
- Eval-Suites: **100 %** pass (2: autoresearch, research-brief).
- Tote interne Pfad-Referenzen: **0** (nach Ausschluss Historie: CHANGELOG/releases + Vorhaben-Docs docs/prds|specs|test-designs|adr).
- Verbleibende command-Dateien: **0**.
- `run-lint --json` pre/post: **diff leer** (byte-identisch) auf Fixture-Vault.
- Bekanntes Vorbestehendes (NICHT durch Refactor verursacht, separat führen): dangling `scripts/lint/lint-open-issues.py` + `scripts/lint/`-Subdir-Referenz.

---
### Checkliste
- [x] Jedes Acceptance-Criterion hat ≥1 Test  ‹Wann-erledigt›  (je Modul-Spec gemappt)
- [x] Alle relevanten Ebenen abgedeckt  ‹Wie›
- [x] Numerische Quality-Gate-Schwellen gesetzt  ‹Womit›
- [x] Security-Test (path-safety) referenziert
