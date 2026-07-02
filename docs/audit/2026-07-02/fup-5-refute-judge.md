---
title: FUP-5 — Adversarial refute-judge verdict (G-verify)
date: 2026-07-02
role: adversarial verification judge (REFUTE-mode, read-only)
target_spec: docs/specs/SPEC-fup-5-skill-count-ssot.md
base_commit: 12bf32b
branch: main
scope: judged the WORKING TREE (visualize staged, not committed) against the refined ACs in the SPEC
---

# Overall verdict: **PASS (with one non-blocking bookkeeping FAIL — AC-F1)**

Every distribution-affecting AC (Phases B–E: trim, wiring, doc-reconciliation, guard, version-defer,
gitignore/lint, full suite) is **CONFIRMED green with concrete evidence**. The single failing AC is
**AC-F1** (manifest `fup-5.status` must read `"verified"` — it currently reads `"in_progress"`). This
is a *bookkeeping* status literal, not a code/doc/guard defect, and by the gate ladder it is the judge
(this pass, G-verify) whose PASS is the precondition for flipping that node to `verified` — so the node
being not-yet-`verified` at judge time is structurally expected. It nonetheless does not satisfy AC-F1's
binary wording *right now*, so it is reported as a FAIL and left for the build owner to flip post-verdict.

- ac_pass_count: **21 / 22**
- ac_fail_count: **1 / 22** (AC-F1 — manifest status literal)
- Distribution artifacts (the shipped plugin): **clean**. The one FAIL is in a planning manifest, not in anything packaged.

---

## Per-AC verdict table

| AC | Verdict | Evidence (command output / file:line) |
|----|---------|----------------------------------------|
| **AC-B1** relocated blocks present in references | PASS | ChartManager→`references/libraries.md`; reveal.js→7 refs incl. `menu.md`/`libraries.md`; poster CSS→`design-system.md`+`css-techniques.md`; container-queries→`design-system.md`+`css-techniques.md`; counter-debug→`menu.md` et al. `git`-clone guard baseline PASS. |
| **AC-B2** post-trim SKILL.md == 11,022 B (refined) | PASS | `wc -c skills/visualize/SKILL.md` = **11022** (exact match to refined target); 49,959→11,022 = −78%. Routing table lists all 7 refs; frontmatter block intact. (Line count `wc -l`=114 vs SPEC prose "112" — 2-line cosmetic drift, not the binary AC; byte cap is the AC and it matches.) |
| **AC-C1** `allowed-tools` + version preserved | PASS | frontmatter: `allowed-tools: Read Write Edit Glob Grep` (line present); `metadata.version: 0.3.0`, `license: MIT`, `metadata.author: careerhackeralex` all retained. |
| **AC-C2** canvas boundary both directions | PASS | `skills/visualize/SKILL.md` description names `canvas` ("For internal Obsidian reference boards use the `canvas` skill instead"); `skills/canvas/SKILL.md:3` names `visualize` ("For external, shareable HTML exports … use the `visualize` skill"). |
| **AC-C3** output loc + companion stub | PASS | SKILL.md body contains `wiki/visualizations/` ∧ `type: visualization` ∧ `![[` (all three grep-confirmed). |
| **AC-C4** `.gitignore` note | PASS | `.gitignore` has a `wiki/visualizations/` entry (grep 'visualiz' hit). |
| **AC-C6** plugin keywords +3 | PASS | `plugin.json` keywords array contains `html`, `presentation`, `infographic`. |
| **AC-D1** numeric literals all 15 | PASS | README.md literals `['15','15']`; copilot `['15']`; PRD `['15','15']`. No other value in the 3 guarded files. |
| **AC-D2** table + copilot enumerations == 15 canonical | PASS | CLAUDE/AGENTS/GEMINI tables each = **15 data rows**, set == canonical, no dups, no malformed pipes. Copilot backtick list = 15 unique == canonical. |
| **AC-D3** copilot parenthetical rewrite | PASS | old phrase "excludes the untracked visualize / SSOT is FUP-5" **absent**; new text names the guard `tests/test_skill_count_ssot.py`. |
| **AC-D4** README Credits | PASS | `README.md:426` `## Credits`; `:428` attributes `visualize` to **careerhackeralex** (MIT, v0.3.0). |
| **AC-D5** PRD risk-note resolved | PASS | `docs/prds/agentic-wiki.md:88` now "(FUP-5, **resolved**)" + points at the guard; "(FUP-5, open)" wording gone. |
| **AC-E1** wiki-lint exclude | PASS | `skills/wiki-lint/SKILL.md:316` exclude list contains `wiki/visualizations/`. |
| **AC-E2** guard exits 0 at N=15; negative test fails | PASS | direct run exit **0** ("All 7 … passed (N=15)"). Adversarial negatives (isolated clones) all exit **1**: flip-literal, drop-table-row, drop-copilot-name, typo-name, unstage-visualize, dup-row+drop-skill, inject-`9 skills`-prose. |
| **AC-E3** keywords ∧ CHANGELOG [Unreleased] ∧ versions consistent 1.10.1 (refined defer) | PASS | keywords present; CHANGELOG `[Unreleased] > Added` has the visualize + guard entries; `plugin.json` + all 3 marketplace fields = **1.10.1**, marketplace `ref: v1.10.1`. No 1.11.0 anywhere live. |
| **AC-E4** cleanup (.DS_Store / Archiv.zip absent) | PASS | `ls` → both "No such file or directory". |
| **AC-E5** visualize tracked ∧ count 15 | PASS | `git ls-files skills/visualize/SKILL.md` returns the path; tracked `skills/*/SKILL.md` = **15**. |
| **GATE-B smoke** routing targets exist | PASS | all 7 `references/<x>.md` targets exist and are referenced by the routing table; no dangling routing link. |
| **AC-F1** task row states 15+guard ∧ manifest `fup-5.status=="verified"` | **FAIL** | Task row (`docs/tasks/…-followups.md:39`) correctly states 15 + guard + defer. **BUT** `docs/manifests/dragonscale-agentic-wiki-followups.json` fup-5 node `"status": "in_progress"` — **not** `"verified"`. `verify` field is populated correctly; only the status literal is unmet. |
| **AC-F2** judge returns PASS | PASS (this document) | all distribution ACs green; single non-blocking bookkeeping FAIL triaged below. |
| **Validity** plugin.json + marketplace.json parse | PASS | `json.load` OK for both. |
| **Full suite** make test + run-lint green | PASS | `make test` exit **0** ("All tests passed."); `python3 scripts/run-lint.py` exit **0** (Totals error=182 warn=56 info=1 — pre-existing working-vault content, explicitly out-of-scope per SPEC §4; findings ≠ failure, rc 0). |

---

## Defects (ranked by severity)

### D1 — AC-F1: manifest `fup-5.status` is `"in_progress"`, not `"verified"` — SEV: LOW (non-blocking, bookkeeping)
- **File:** `docs/manifests/dragonscale-agentic-wiki-followups.json` → node `id: "fup-5"` → `"status": "in_progress"`.
- **AC wording:** AC-F1 (binary) = *"task row states 15 + guard; manifest `fup-5.status == "verified"`."* The task-row half PASSES; the manifest-status half FAILS.
- **Failure scenario:** A tool or reviewer that gates "is FUP-5 done?" on `manifest.fup-5.status == "verified"` reads `in_progress` and concludes the work is unfinished, even though every deliverable is complete and green. Conversely, if AC-F1 were auto-checked in CI it would report red.
- **Why non-blocking:** the gate ladder places this judge (G-verify) *before* the node may legitimately flip to `verified`; the `verify` field already carries the correct completion criteria. Recommended fix (build owner, post-verdict, one line): set `"status": "verified"`. This touches no distribution artifact.

### D2 — AC-B2 line-count prose drift (11,022 B / **114** lines, SPEC says "112") — SEV: INFO (cosmetic, not an AC)
- **File:** `skills/visualize/SKILL.md` (114 newline-terminated lines) vs SPEC AC-B2 narrative "11,022 B / 112 lines".
- **Failure scenario:** none functional. The **binary** AC-B2 is the byte cap (`≤ ~10 KB` intent, refined to the exact 11,022 B figure), which matches to the byte. Only the human-readable line-count annotation in the SPEC is 2 off. No fix required for correctness; optionally correct the SPEC prose to 114.

---

## Refutation attempts that FAILED to break the build (why the PASS is credible)

I actively tried to manufacture a false-PASS or a missed surface and could not, on the distribution set:

1. **Whole-repo drift sweep** for `\b\d+ skills?\b` reading 13/14 or omitting `visualize` in LIVE files: **zero** live hits. Every 13/14 occurrence is in `docs/plans/PLAN-visualize-integration.md`, `docs/specs/SPEC-visualize-wiki-integration.md` (both excluded historical). `wiki/**` "23 skills / 19 skills" hits are about the *unrelated* Claude-SEO entity, not this plugin, and are not guarded surfaces. `.windsurf/` and `.cursor/` confirmed **absent** (`ls` → No such file or directory) — no stale rule files to disagree.
2. **Guard false-PASS on set-collapse:** duplicated the `visualize` row AND dropped `canvas` in GEMINI (15 rows, but a `set()` could hide the swap) → guard **correctly FAILED** `missing=['canvas']`. The `set` comparison is against the canonical set, so a substituted/duplicated member still surfaces the true miss.
3. **Guard false-PASS on unstaged skill:** `git rm --cached skills/visualize/SKILL.md` in an isolated clone → guard **correctly FAILED** (SSOT drops to 14, literals still 15). It reads the *staged/tracked* set via `git ls-files`, exactly as the SSOT demands — not on-disk.
4. **Numeric regex under-match:** injected a real competing `9 skills` prose line into the PRD → **caught**. `100 skillsets` decoy correctly **ignored** (word-boundary). So it neither misses a real literal nor over-matches `skillsets`.
5. **Copilot parenthetical mis-selection:** only **one** `skills (` occurrence exists, the non-greedy `skills \((.*?)\)` grabs the correct 15-name list; the numeric `N` immediately before it is `15` — numeric and membership are coherent.
6. **JSON validity / table well-formedness:** both JSON files parse; all three tables are exactly 15 rows with balanced pipes and no duplicate slugs.

### Residual soundness caveat (NOT a current defect — no live prose triggers it)
The numeric regex `\b(\d+)\s+skills?\b` matches `N skill` even inside a hyphenated word: `3 skill-issues` / `3 skill-related` → captures `['3']` (the `\b` lands at the hyphen). Today **no** such prose exists in the 3 guarded files (all literals read `15`), so it does not false-FAIL now. But a future maintainer who writes legitimate prose like "the 3 skill-related helpers" into README/copilot/PRD would trip a **false-FAIL**. Low-likelihood, easily fixed if it ever surfaces (tighten to `skills?(?![-\w])` or exclude hyphen). Flagging for the record; does not affect this verdict.
