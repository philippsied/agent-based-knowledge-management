---
title: PLAN — visualize skill integration (decision-locked execution plan)
status: DECISION-LOCKED (planning only — NOT executed). Phases B→E ready to run in a later session.
repo: /Users/philipp/AI-powered_workbench/agent-based-knowledge-management
input: docs/specs/SPEC-visualize-wiki-integration.md (§0 decision, §6 wiring checklist, §7 open questions, §8 phases)
author: planning pass (read-only; evidence-backed)
date: 2026-06-30
supersedes_questions: SPEC §7 Q1–Q9 (all resolved below)
---

# PLAN — Integrating the `visualize` skill

This plan locks the 9 open questions from SPEC §7 and turns SPEC §8 phases B→E into ordered,
file-exact steps. It is a **planning artifact** — nothing here has been executed.

---

## ⚠️ Review gate — confirm BEFORE execute

Three decisions below are **maintainer-policy calls**, not mechanical facts. They are locked to a
recommendation for planning purposes but MUST be confirmed by the maintainer before the execution
session runs the affected step:

1. **Gitignore commit-policy (Q3)** — "are generated visualizations committed or ignored?"
   Locked recommendation: **ignore generated HTML** (treat as ephemeral, consistent with the
   existing `wiki/*` + `_attachments/` ignore posture). This is a vault-philosophy call.
   → Affects Phase C step C4.
2. **Version bump (Q4)** — "does adding this skill warrant a plugin minor bump (1.10.1 → 1.11.0)?"
   Locked recommendation: **yes, bump to 1.11.0 on the next release cut** (new user-facing skill =
   minor under semver), keep upstream `version: 0.3.0` inside the skill metadata. Release-timing is
   the maintainer's call. → Affects Phase E step E5.
3. **Attribution mechanism (Q6)** — where `careerhackeralex` credit lives.
   Locked recommendation: **add a README "Credits" section + keep author in skill frontmatter**
   (no separate NOTICE file). Attribution form is a maintainer/legal-style preference.
   → Affects Phase D step D2.

If the maintainer disagrees with any of the three, only the named step changes; the rest of the
plan stands.

---

## Decisions table (SPEC §7 Q1–Q9)

All "Evidence" cites were verified by inspection on 2026-06-30 (read/grep, not asserted).

| Q | Decision | Rationale (1 line) | Evidence (file:line) |
|---|----------|--------------------|----------------------|
| **Q1 — Output location** | `wiki/visualizations/` (new dir), with per-call override allowed | Graph-adjacent + Obsidian renders HTML there; matches SPEC recommendation and the vault's "knowledge lives under `wiki/`" convention. `_attachments/` is for source media, not generated artifacts. | `docs/specs/SPEC-visualize-wiki-integration.md:§7 Q1` (recommends `wiki/visualizations/`); dir absent today → `ctx_execute`: "wiki/visualizations does NOT exist yet"; existing `wiki/` subdirs (concepts, entities, comparisons, …) confirm the `wiki/<kind>/` pattern. |
| **Q2 — Companion wiki stub** | **Yes — write a tiny companion `.md` stub** per generated HTML (frontmatter `type: visualization` + link + `![[...]]` embed) | Makes the artifact graph-visible and lint-classifiable; without it the HTML is an orphan invisible to `wiki-query`/graph. Cheap (a few lines). | SPEC R2 mitigation (`§5 R2`: "optionally write a tiny companion wiki stub … so the artifact is graph-visible and lint-safe"); graph/orphan concern is the wiki's core value prop (`skills/wiki/SKILL.md:` "Cross-references are already there"). |
| **Q3 — Gitignore policy** ⚠️ | **Ignore generated HTML + stubs** (ephemeral output) — add `wiki/visualizations/*` rule; this is consistent because `wiki/*` is *already* fully ignored | The vault already ignores all generated content (`/wiki/*` except `.gitkeep`) and `_attachments/`; committing generated viz would break that posture. No extra `.gitignore` rule is strictly needed since `/wiki/*` (line 124) already catches it — add an explicit anchored note for clarity. **Maintainer-policy → confirm.** | `.gitignore:124` `/wiki/*`; `.gitignore:125` `!/wiki/.gitkeep`; `.gitignore:110` `_attachments/`; `.gitignore:123` "Only the directory anchors (.gitkeep) and shared default config remain tracked." |
| **Q4 — Version reconciliation** ⚠️ | Keep skill `metadata.version: 0.3.0`; **bump plugin 1.10.1 → 1.11.0** at the release that includes this skill | Two independent version namespaces: upstream skill provenance (0.3.0, preserve for attribution) vs plugin semver. New user-facing skill = minor bump. **Release timing is maintainer-policy → confirm.** | plugin.json:3 `"version": "1.10.1"`; `skills/visualize/SKILL.md:14` `version: 0.3.0`; SPEC §2.2 confirms working tree at 1.10.1 and "no `skills` array" (auto-discovery). |
| **Q5 — `allowed-tools`** | **Add `allowed-tools: Read Write Edit Glob Grep`** to the skill frontmatter | The skill must `Write` HTML (+ stub) and `Read` vault content; 9 of 14 skills already declare it, incl. the 2 newest *house* skills (`autoresearch`, `research-brief`). `visualize` is upstream-pure today but house convention favors declaring. No Bash/Web needed (pure local generation). | `ctx_execute` allowed-tools audit: 9/14 YES; newest house skills WITH it = `autoresearch` (mtime 2026-05-28, `allowed-tools: Read Write Edit Glob Grep WebFetch WebSearch Bash`) and `research-brief` (2026-05-27, `allowed-tools: Read Write Edit Glob Grep Bash`); `visualize` currently `name+description` only (`skills/visualize/SKILL.md:1-16`). |
| **Q6 — Attribution** ⚠️ | **README "Credits" section** (new) + keep `metadata.author: careerhackeralex` in frontmatter. **No** separate NOTICE file. | No NOTICE exists and README has no Credits section today; a single README section is the lightest correct way to preserve MIT attribution without adding a new root file. **Form is maintainer preference → confirm.** | `ctx_execute` Q6 check: only `./LICENSE` exists (no NOTICE); README MIT hits are badge (README.md:9) + comparison table (README.md:55) only — **no Credits/kepano/careerhackeralex section**; `skills/visualize/` has no LICENSE/NOTICE. |
| **Q7 — Trim depth** | **Lean dispatcher, ~8–10 KB** (≈170–220 lines): keep frontmatter, core principles, output rules, the "load `references/<x>.md` when…" routing table, non-negotiables; relocate all 18 large code blocks into the already-existing `references/`. | SPEC gate is "≤ ~10 KB"; 8–10 KB balances trigger reliability (enough description/routing) vs context cost. Pure-6 KB risks dropping the routing table; keep-15 KB fails the gate. | SPEC §8 Phase B gate ("SKILL.md ≤ ~10 KB"); current size `skills/visualize/SKILL.md` = **883 lines / 49,959 B**; targets already exist: `references/skeleton.md` (15 KB), `css-techniques.md` (30 KB), `design-system.md` (26 KB), `libraries.md` (6.4 KB), `menu.md` (9.6 KB), `animations.md` (6.1 KB), `types.md` (9.1 KB). |
| **Q8 — Lint awareness** | **Teach `wiki-lint` to recognize `wiki/visualizations/`**: classify the *companion stubs* as a meta/excluded class (no `address:` required, not orphan-flagged), and the raw `.html` is not a `.md` page so it's already out of scope. Add `wiki/visualizations/` to the path-exclude list. | `wiki-lint` only scans `wiki/**/*.md`; raw HTML is never scanned. Stubs are generated metadata, not authored concepts → exclude by path like `folds`/`meta`. Prevents false orphan/address errors. (Note: spec's phrasing "skips `_attachments`/`_templates`" is loose — those live outside `wiki/` so lint never reaches them; the *actual* exclude list is path `wiki/folds`+`wiki/meta`, filenames, frontmatter `type:`, and symlinks.) | `skills/wiki-lint/SKILL.md:316` "Excludes (path): anything under `wiki/folds/` or `wiki/meta/`."; `:317` filename excludes; `:318` frontmatter `type: meta`/`type: fold`; `:319` symlink exclude; `:212` "Meta / fold / excluded" classification row. |
| **Q9 — `bin/setup-multi-agent.sh` hard-codes "13"?** | **NO. Confirmed clean — no count, no skill list.** No edit needed in this script. | `grep '13' bin/setup-multi-agent.sh` → **0 matches**. Script (87 lines) symlinks the whole `$SKILLS_DIR` (`bin/setup-multi-agent.sh:21` `SKILLS_DIR="$REPO_ROOT/skills"`; lines 65/68/71/74/77 `link_if_missing "$SKILLS_DIR" …`) → auto-discovers `visualize/`. The only "13" literals live in 7 docs (SPEC §2.4 / Appendix A). | `ctx_execute` Q9: "grep for digits 13/14/count… (no output)"; `bin/setup-multi-agent.sh:21,65-77`. |

### Count-drift surface (consequence of Q9) — the 7 docs that DO hard-code "13"
Verified via SPEC §2.4 + Appendix A (line anchors). `visualize` appears in **0** of them today.

| Doc | Anchor(s) | Edit |
|-----|-----------|------|
| `README.md` | L15 `**13 skills.**`; L329 tree comment `# 13 skills` | 13→14 ×2 + add `visualize/` tree node |
| `CLAUDE.md` | L49-65 Plugin Skills table (no count literal) | add `/visualize` row |
| `AGENTS.md` | L25-41 table (no count literal) | add `visualize` row |
| `GEMINI.md` | L19-35 table (no count literal) | add `visualize` row |
| `.github/copilot-instructions.md` | L13 `13 skills (… name list)` | 13→14 + add `visualize` to name list |
| `.windsurf/rules/claude-obsidian.md` | L15 `13 SKILL.md files`; L30 `all 13 skills`; L32-44 bullets | 13→14 ×2 + add `visualize` bullet |
| `.cursor/rules/claude-obsidian.mdc` | L19 `13 skills`; L23-37 table | 13→14 + add `visualize` row |

---

## Locked execution plan — Phases B → E

> Manifests need **NO skills-array edit** (SPEC §2.2: skills auto-discover; no `skills` array in
> either manifest). `skills/visualize/` is already loadable today; only git-tracking + the wiring
> below remain. The `Archiv.zip` cleanup (SPEC R8) is assumed already done — confirm before Phase B.

### Phase B — Trim SKILL.md (Q7)
**Goal:** lean orchestrator, no behavioral regression.

- **B1.** Edit `skills/visualize/SKILL.md`: move the 18 large fenced code blocks (HTML skeletons,
  CSS, Chart.js, menu, animations) **out** into the matching existing references —
  `references/skeleton.md`, `css-techniques.md`, `design-system.md`, `libraries.md`, `menu.md`,
  `animations.md`, `types.md`. Append (don't duplicate) only blocks not already present.
- **B2.** In `skills/visualize/SKILL.md`, keep: frontmatter, core principles, output rules,
  non-negotiables, and a **"load `references/<x>.md` when …" routing table**. Target **8–10 KB
  (~170–220 lines)**, down from 883 lines / 49,959 B.
- **Gate B:** `wc -c skills/visualize/SKILL.md` ≤ ~10,240 B; quick smoke test (one deck + one
  infographic + one dashboard prompt) produces equivalent HTML to pre-trim. No reference file
  loses content (each code block has a home).

### Phase C — Wire (Q1, Q2, Q3, Q4-frontmatter, Q5)
**Goal:** skill triggers cleanly, no `canvas` collision, output location defined.

- **C1.** Edit `skills/visualize/SKILL.md` frontmatter (Q5): add
  `allowed-tools: Read Write Edit Glob Grep`. Preserve `license: MIT` and `metadata.author:
  careerhackeralex` / `metadata.version: 0.3.0` (Q4 — do NOT relabel).
- **C2.** Edit `skills/visualize/SKILL.md` **and** `skills/canvas/SKILL.md` descriptions (R4):
  sharpen the boundary — `visualize` = external shareable HTML artifact; `canvas` = internal
  Obsidian reference board. Add a one-line cross-reference in each.
- **C3.** Encode output location (Q1) + companion stub (Q2) in the skill body: default
  `wiki/visualizations/<slug>.html`; write a companion `wiki/visualizations/<slug>.md` stub
  (`type: visualization` frontmatter + link + `![[<slug>.html]]` embed); allow per-call override.
- **C4.** ⚠️ **(confirm Q3 first)** Edit `.gitignore`: add an explicit anchored comment +
  rule block for `wiki/visualizations/` under the existing `/wiki/*` policy (functionally already
  ignored by `.gitignore:124`; the explicit note documents intent). If maintainer chooses
  *commit*, instead add `!wiki/visualizations/` un-ignore — but default is **ignore**.
- **C5.** Create `commands/visualize.md` — copy the `commands/canvas.md` template: frontmatter
  `description:` **only** (no `name`, no `allowed-tools`), body `Read the \`visualize\` skill.`
  + a short operation table. (SPEC §2.2 + Appendix B confirm this is the alias template.)
- **C6.** Optional: `.claude-plugin/plugin.json` `keywords` — add `"html"`, `"presentation"`,
  `"infographic"` (`"visual"`/`"canvas"` already present). **No** skills-array edit.
- **Gate C:** representative prompts ("make a one-pager from wiki page X", "add this image to my
  canvas") route to the correct skill (no visualize/canvas collision); `/visualize` resolves to
  the skill via the new command.

### Phase D — Docs (Q6 + the 7-doc count/list bump)
**Goal:** docs stop lying ("13 skills"); attribution present.

- **D1.** Apply the 7-doc count/list bump per the table above:
  `README.md` (L15, L329 + tree node), `CLAUDE.md` (L49-65 row), `AGENTS.md` (L25-41 row),
  `GEMINI.md` (L19-35 row), `.github/copilot-instructions.md` (L13), `.windsurf/rules/claude-obsidian.md`
  (L15, L30, L32-44), `.cursor/rules/claude-obsidian.mdc` (L19, L23-37).
- **D2.** ⚠️ **(confirm Q6 first)** Edit `README.md`: add a **"Credits"** section attributing the
  `visualize` skill to `careerhackeralex` (MIT, upstream v0.3.0). No NOTICE file.
- **Gate D:** `grep -rn '\b13\b' README.md CLAUDE.md AGENTS.md GEMINI.md .github/ .windsurf/ .cursor/`
  shows **0** stale skill-count "13" in skill contexts; `grep -rn 'visuali[sz]e'` shows hits in all
  7 docs + `commands/visualize.md`; README has a Credits entry.

### Phase E — Test + release (Q8 + verification)
**Goal:** lint-aware, end-to-end verified, optionally cut a release.

- **E1.** Edit `skills/wiki-lint/SKILL.md` (Q8): add `wiki/visualizations/` to the path-exclude
  list (alongside `wiki/folds/`, `wiki/meta/` at SKILL.md:316) so companion stubs aren't
  orphan/address-flagged.
- **E2.** Verify count: `ls skills/ | wc -l` == 14 == every count literal in README/copilot/windsurf/cursor.
- **E3.** Smoke test end-to-end: trigger "make a one-pager from wiki page X" → HTML lands in
  `wiki/visualizations/`, companion stub created, `wiki-lint` runs clean (no new orphan/address errors).
- **E4.** Confirm `skills/visualize/Archiv.zip` is absent before any tracking/commit (SPEC R8).
- **E5.** ⚠️ **(confirm Q4 release timing first)** If cutting a release: bump
  `.claude-plugin/plugin.json` `version` 1.10.1 → 1.11.0 **and** mirror in
  `.claude-plugin/marketplace.json` (`metadata.version`, `plugins[0].version`, and
  `plugins[0].source.ref` tag `v1.11.0`). Update CHANGELOG.
- **Gate E:** lint clean; smoke test green; count==14 everywhere; (if released) all three
  marketplace version fields + plugin version + tag agree.

---

## File-touch summary (planning reference — do NOT execute here)

**Required:** `skills/visualize/SKILL.md` (trim + frontmatter + output/stub), `skills/canvas/SKILL.md`
(description), `commands/visualize.md` (new), `skills/wiki-lint/SKILL.md` (exclude), `CLAUDE.md`,
`README.md` (+ Credits), `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`,
`.windsurf/rules/claude-obsidian.md`, `.cursor/rules/claude-obsidian.mdc`.
**Conditional (maintainer-gated):** `.gitignore` (Q3), `.claude-plugin/plugin.json` +
`.claude-plugin/marketplace.json` (Q4 version), CHANGELOG.
**Explicitly NOT touched:** `bin/setup-multi-agent.sh` (Q9 — verified clean), manifest `skills`
arrays (none exist).
