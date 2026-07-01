---
type: audit-evidence
phase: 0
gate: G0
audit_base_commit: 0a9916d
pinned_from: 3c4717a
generated: 2026-07-01
verdict: GREEN
---

# Phase 0 — Struktur-Gate (G0) · Evidence

Read-only deterministic sweep über alle Planungsartefakte beider Bundles
(`cmd-script-consolidation` + `dragonscale-agentic-wiki-followups`).
Methode: ein Python-Sweep im Sandbox, jeder Befund mit konkretem Check-Ergebnis (R2).
**Keine Edits.** Basis-Commit re-gepinnt auf `0a9916d` (siehe S0-Note).

## Verdict: 🟢 G0 = GREEN — Fanout (Phase 1) freigegeben

Alle 8 Struktur-Kriterien bestanden. Kein struktureller Blocker.

| # | Kriterium | Ergebnis | Gate |
|---|-----------|----------|:----:|
| 1 | Manifest `validate`/`coverage`/`status` (beide) | beide `valid`; coverage+status vorhanden | ✅ |
| 2 | Manifest-Path-Integrität | cmd: 20 paths, 0 missing · followups: 4 paths, 0 missing | ✅ |
| 3 | MD-Link-Integrität (docs/) | 90 rel-links geprüft, **0 echte broken** (1 `%20`-Kandidat verifiziert existent) | ✅ |
| 4 | `file:line`-Zitate (docs/) | 45 distinct; 11 „invalid" = **ausschließlich `.sh` historisch** (bekannt, per `3710c15`); 0 unerwartet | ✅ |
| 5 | Seed-Claims (Handoff #1) | 3/3 exakt verifiziert | ✅ |
| 6 | SDD-Ketten-Sektionen | **0 echte Gaps** (6 Flags = EN/DE-Needle-Fehltreffer, Sektionen verifiziert vorhanden) | ✅ |
| 7 | Orphan-Check (5 cmd-task-files) | alle referenziert (2–4 refs) — Handoff-Sorge **widerlegt** | ✅ |
| 8 | Modeling fup-2/fup-4 | beide → shared tracker (wie dokumentiert) | ✅* |

`*` strukturell konsistent; die *Rechtfertigung* shared-tracker vs. file-per-module ist ein Phase-1-Semantik-Punkt, kein G0-Defekt.

## S0 — Freeze-Note (relevant für C6)

HEAD bewegte sich während der Session `3c4717a → 0a9916d`.
`0a9916d` = `chore: drop stale .cursor/.windsurf claude-obsidian rule mirrors` (135 Zeilen, nur IDE-Rule-Mirrors).
**Kein `docs/`, kein `scripts/`, kein Manifest berührt** → alle zitierten Artefakt-`file:line` intakt, Citation-Drift = 0.
Vermutlich decide-next Auto-Commit. Audit-Basis re-gepinnt auf `0a9916d`. Branch weiterhin unpushed/unmerged.

## Detail-Evidence

### 1 Manifest-Health
```
cmd-script-consolidation.json      validate=valid  coverage=7-W ok  status ok
dragonscale-agentic-wiki-followups validate=valid  coverage=7-W ok  status ok
```

### 3 Link — der eine Kandidat
`docs/dragonscale-guide.md → ../wiki/concepts/DragonScale%20Memory.md`
- raw (mit `%20`): exists=False · **decoded**: `wiki/concepts/DragonScale Memory.md` exists=**True**
- → gültiger URL-encodeter Obsidian-Link, kein Defekt.

### 4 `.sh`-Zitate (11, alle historisch-korrekt, NICHT anfassen)
`bin/setup-dragonscale.sh` · `scripts/run-lint.sh` · `bin/release.sh` · `hooks/wiki-path-safety.sh` ·
`scripts/allocate-address.sh` · `bin/setup-multi-agent.sh` — Pre-Konsolidierungs-Stand, per Audit `3710c15` bewusst als History behalten. `.py`-Äquivalente existieren (siehe #5).

### 5 Seed-Claims (exakt)
```
bin/setup-dragonscale.py:52  →  counter.write_text("1\n")          [seeds 1 ✓]
bin/setup-vault.py:48        →  counter.write_text("0\n")          [seeds 0 ✓]
scripts/allocate-address.py:140 → current = read_or_recover_counter()  [read-then-increment ✓]
```

### 6 „Gap"-Flags widerlegt
- **PRDs (3/3):** haben `## 3. Goals & Success metrics ‹When-done›` + `### Checklist (before status: approved)` → Acceptance-Mechanismus vorhanden. Needle „acceptance/success criteria" verfehlte „Success metrics".
- **ADR 0001/0002/0003:** haben `## Konsequenzen ‹Warum: Folgen›` + `### Checkliste`. Englischer Needle „consequences" verfehlte deutsches „Konsequenzen".

### 7 Orphan-Check (Handoff-Sorge widerlegt)
```
commands.md    refs=3  (manifests, plans, test-designs)
dragonscale.md refs=2  (plans, test-designs)
ingest.md      refs=3  (manifests, plans, test-designs)
lint.md        refs=3  (manifests, plans, test-designs)
setup.md       refs=4  (adr, manifests, plans, test-designs)
```

### 8 Modeling
`fup-2` und `fup-4` → beide `docs/tasks/dragonscale-agentic-wiki-followups.md` (shared tracker, dokumentiert).

## Carry-forward Seeds für Phase 1 (kein G0-Defekt — an Agents übergeben)

- **S-a → Agent A (#1):** `setup-vault.py:48` seedet `0` vs. ADR-0004 kanonisch `1` — **live Code↔Doc-Divergenz bestätigt**. Klasse `flag-only` (Konflikt C5), NICHT `fix-doc`.
- **S-b → Agent B (Konsistenz-Lens):** EN/DE-Heading-Split — pre-existing Bundle deutsch, this-session englisch (PRDs + ADRs). Konsistenz-Beobachtung, low-sev.
- **S-c → Phase 1 (#Modeling):** shared-tracker (followups) vs. file-per-module (cmd) — Rechtfertigung/Reconcile nötig, dokumentiert vorhanden.
- **S-d → Agent D (#8):** die 11 `.sh`-Zitate bleiben Disposition „historisch" (per `3710c15`) — Phase 1 darf sie NICHT als broken „fixen".
- **S-e (S0):** HEAD-Move audit-neutral, re-gepinnt `0a9916d`.
