---
title: SPEC — Integrating the `visualize` skill into agentic-knowledge-management
status: draft (planning artifact for a LATER session — DO NOT EXECUTE from this doc)
repo: /Users/philipp/AI-powered_workbench/agent-based-knowledge-management
author: assessment pass (read-only)
date: 2026-06-21
recommendation: INTEGRATE — conditional on trimming SKILL.md first and scoping it as
  a deliberately complementary "external-format export" skill (not a vault-writing skill).
---

# 0. TL;DR / Decision

**Integrate — yes, conditionally.** `visualize` is a high-quality, self-contained HTML
visualization skill (MIT, third-party author `careerhackeralex`, v0.3.0). It fills a real
gap: the vault currently has **no way to turn wiki knowledge into a shareable/presentable
artifact** (deck, infographic, dashboard, one-pager). The existing `canvas` skill is *not*
a substitute — it builds an Obsidian-internal JSON board, not exportable HTML.

But it does **not** integrate cleanly as-is. Three conditions must be met before wiring:

1. **Trim `SKILL.md` (49,959 bytes / 883 lines) to a lean orchestrator** (~6-10 KB). The
   heavy HTML/CSS/Chart.js bodies duplicate content that *already exists* in its own
   `references/` (skeleton.md, css-techniques.md, design-system.md, …). This is a
   progressive-disclosure violation and the single biggest risk. (See §5.)
2. **Scope it as an *export* layer, not a vault layer.** Define where its HTML output lands
   (recommended: `wiki/visualizations/` or `_attachments/`, gitignore-aware) so it is a
   first-class citizen of the vault model rather than a foreign body that "ships nothing in."
   (See §3 FIT, §6 wiring step 6.)
3. **Reconcile metadata** (license attribution kept, version/author fields, trigger-phrase
   normalization to match house style). (See §6.)

If those three are out of scope for the integrating session, the fallback is **"vendor as-is,
document the divergence, do not normalize"** — still integrate, but accept the bloat and the
attribution mismatch as known debt.

---

# 1. Scope of this SPEC

This document **assesses and plans**. It does **not** modify any repo file and does **not**
wire anything in. It is the input to a later implementation session.

Inputs read (read-only):
- `skills/visualize/SKILL.md` (frontmatter, 22 H2 sections, 18 fenced code blocks) +
  all 9 `skills/visualize/references/*.md`.
- Integration surface: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  `CLAUDE.md`, `README.md`, `commands/canvas.md`, `commands/wiki.md`, `skills/canvas/SKILL.md`.
- Skill-count-drift surface: `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`,
  `.windsurf/rules/claude-obsidian.md`, `.cursor/rules/claude-obsidian.mdc`.

Out of scope: the redundant `skills/visualize/Archiv.zip` (being removed separately — ignore).

---

# 2. Current state (evidence)

## 2.1 The skill itself
- `skills/visualize/SKILL.md` — **49,959 bytes, 883 lines, 22 `##` sections, 18 code blocks.**
- Frontmatter (kepano-style `name`/`description` plus extra `license` + `metadata`):
  ```yaml
  name: visualize
  description: >
    Create beautiful, self-contained HTML visualizations from any content or idea.
    Use for: slide decks, presentations, infographics, dashboards, flowcharts, diagrams,
    timelines, comparison tables, data visualizations, landing pages, one-pagers, org charts,
    mind maps, process flows, kanban boards, report summaries, ...
    Trigger on requests like "visualize this," "make a deck," "create a slide,"
    "build an infographic," "show me a dashboard," "make this visual," ...
  license: MIT
  metadata:
    author: careerhackeralex
    version: 0.3.0
    category: document-creation
    tags: [visualization, html, slides, dashboard, infographic]
  ```
- `references/` (9 files, ~106 KB total — already well-structured):
  | file | bytes |
  |---|---|
  | css-techniques.md | 30,144 |
  | design-system.md | 26,342 |
  | skeleton.md | 15,151 |
  | menu.md | 9,632 |
  | types.md | 9,142 |
  | libraries.md | 6,395 |
  | animations.md | 6,101 |
  | eval.md | 2,361 |
  | anthropic-skill-guide-notes.md | 1,693 |
- Total skill dir ≈ **156.9 KB** (excluding the to-be-removed Archiv.zip).
- **License:** MIT (stated in frontmatter + referenced in `references/types.md` and
  `references/anthropic-skill-guide-notes.md`). No standalone `LICENSE` file in the skill dir.
- **Output:** a single self-contained `.html` file. **Nothing is written into the markdown
  vault** — no wiki page, no frontmatter, no wikilink, no address.

## 2.2 How skills are declared in this repo (IMPORTANT — changes the wiring story)
- **Neither `plugin.json` nor `marketplace.json` contains a `skills` array.** Skills are
  **auto-discovered** from `skills/<name>/SKILL.md`. Confirmed: `skills/` already contains
  **14 directories** including `visualize/`, so the skill is *already loadable* by Claude Code
  today — the only thing "untracked" is git status, not the plugin manifest.
- Manifest fields that exist: `name`, `version`, `description`, `author`, `license`, `homepage`,
  `repository`, `keywords` (plugin.json) and the mirror in marketplace.json's `plugins[0]`.
- **Version state:** `plugin.json` = **1.10.1**, `marketplace.json` (`metadata.version` and
  `plugins[0].version` + `ref: v1.10.1`) = **1.10.1**. (Git log shows 1.10.0 was the last
  *committed* cut; working tree is already at 1.10.1.) `keywords` already include
  `"canvas"` and `"visual"`.
- **Command-alias pattern** (`commands/canvas.md`, `commands/wiki.md`): frontmatter is
  **`description:` only** (no `name`, no `allowed-tools`); body is a one-liner
  `Read the \`<skill>\` skill.` followed by an operation table. This is the template to copy.

## 2.3 The existing `canvas` skill (overlap reference)
- `skills/canvas/SKILL.md` frontmatter: `name`, `description` (long trigger list),
  `allowed-tools: Read Write Edit Glob Grep`.
- Declares the vault's **three capture layers** explicitly:
  ```
  /save        → text synthesis (wiki/questions/, wiki/concepts/)
  /autoresearch → structured knowledge (wiki/sources/, wiki/concepts/)
  /canvas      → visual references (wiki/canvases/)
  ```
- Output: **Obsidian `.canvas` JSON** (JSON Canvas open standard) under `wiki/canvases/`.
  An *infinite board of references* (images/PDFs/notes), rendered only inside Obsidian.

## 2.4 Skill-count-drift surface (the "13 → 14" problem)
The repo hard-codes the count and/or an explicit skill enumeration in **7 docs**. `visualize`
appears in **none** of them today (grep for `visuali[sz]e` outside the skill dir = **0 hits**).

| # | File | Location(s) | What's there | Edit needed |
|---|---|---|---|---|
| 1 | `README.md` | L15 (headline `**13 skills.**`); L329 (tree comment `# 13 skills`) | count literal ×2 + ASCII tree of skill dirs (no `visualize/` node); also a command table L119-134 | bump 13→14, add `visualize/` tree node, optional command-table rows |
| 2 | `CLAUDE.md` | L49-65 "Plugin Skills" table | 13-row skill table, **no `visualize` row** (no count literal) | add `/visualize` row |
| 3 | `AGENTS.md` | L25-41 "Available Skills" table | 13-row table, no `visualize` (no count literal) | add `visualize` row |
| 4 | `GEMINI.md` | L19-35 "Skills" table | 13-row table, no `visualize` (no count literal) | add `visualize` row |
| 5 | `.github/copilot-instructions.md` | L13 | `13 skills (\`autoresearch\`, …, \`wiki-query\`)` — explicit name list | bump 13→14 + add `visualize` to list |
| 6 | `.windsurf/rules/claude-obsidian.md` | L15 (`13 SKILL.md files`), L30 (`all 13 skills`), L32-44 bullet list | 2 count literals + 13-item bullet list | bump 13→14 ×2 + add `visualize` bullet |
| 7 | `.cursor/rules/claude-obsidian.mdc` | L19 (`13 skills`), L23-37 table | count literal + 13-row table | bump 13→14 + add `visualize` row |

`bin/setup-multi-agent.sh` symlinks the whole `skills/` dir, so no per-skill registration is
needed there (it picks up `visualize/` automatically). Worth a grep in the wiring session to
confirm no count literal lives inside that script.

---

# 3. FIT — does an HTML-visualization skill belong in a markdown wiki vault?

## Argument AGAINST
- **Format mismatch.** The vault's entire value proposition (per `CLAUDE.md`) is *"output is
  Obsidian markdown"* — flat-YAML frontmatter, wikilinks, addresses, lint, folds. `visualize`
  produces a standalone `.html` blob that participates in **none** of those systems: no
  wikilink graph, no `index.md` entry, no orphan/lint coverage, no fold rollup.
- **Ships nothing into the vault today.** As written it writes an HTML file wherever the user
  is; it does not enrich the compounding knowledge base. That breaks the repo's "every session
  makes the wiki richer" thesis.
- **Heaviest skill in the repo by far** (157 KB vs the next-largest skill's references).
  Carrying it raises the maintenance and review surface materially.
- **Third-party provenance** (different author, independent versioning) — a divergent
  maintenance stream inside an otherwise single-author plugin.

## Argument FOR
- **It closes the "last-mile output" gap.** The vault is excellent at *accumulating* knowledge
  and *answering* (`wiki-query`) but has **no presentation/export path**. "Turn what you know
  about X into a one-page brief / deck / dashboard" is a natural, high-value follow-on to
  `wiki-query` and `autoresearch`. Today that request has no home.
- **It is genuinely complementary to `canvas`, not redundant** (see §4). Canvas = internal
  reference board; visualize = external shareable artifact. Different consumer, different
  format, different moment in the workflow.
- **The plugin already advertises the territory.** `plugin.json` keywords already include
  `"canvas"` and `"visual"`; a visual-export skill is on-brand.
- **Obsidian renders HTML attachments.** An HTML file dropped in `_attachments/` or
  `wiki/visualizations/` *can* be embedded/opened from Obsidian, and *can* be pinned onto a
  `canvas` board — so it need not be a foreign body if we define an output location.
- **Quality is high and references are already disciplined** — the bloat is confined to
  SKILL.md; the `references/` layer is exactly the structure the repo wants.

## Recommendation
**Integrate, but reframe it as the vault's "export / presentation layer," parallel to the
three capture layers.** Concretely: give it a defined output home inside the vault
(`wiki/visualizations/` recommended) so it stops "shipping nothing in," and position it in docs
as *"turn wiki knowledge into a shareable HTML artifact"* rather than a generic HTML toy. With
that reframing the FIT objection (format mismatch) becomes a *feature boundary* (markdown for
the knowledge graph, HTML for the export) rather than a contradiction.

---

# 4. OVERLAP with `canvas` — complementary, with one fuzzy edge

| dimension | `canvas` | `visualize` |
|---|---|---|
| Output format | Obsidian `.canvas` JSON (JSON Canvas std) | self-contained `.html` |
| Rendered by | Obsidian only | any browser; embeddable in Obsidian |
| Purpose | *internal* spatial board of **references** (images, PDFs, wiki notes) | *external/shareable* **presentation** (deck, infographic, dashboard) |
| Participates in vault graph | yes (links wiki pages as nodes) | no (standalone artifact) |
| Editable later in Obsidian | yes (drag nodes) | no (regenerate) |
| Trigger verbs | "add to canvas", "put this on the canvas", "open canvas" | "visualize this", "make a deck", "build an infographic", "show me a dashboard" |
| Layer | capture/organize | export/present |

**Verdict: complementary.** They are not substitutes — you cannot produce a portable infographic
with `canvas`, and you cannot build a living reference board with `visualize`.

**The one fuzzy edge — trigger collision risk on the word "visual":**
- canvas description contains *"visual layer," "put this on the canvas."*
- visualize description contains *"make this visual," "show me a dashboard."*
- Bare *"visualize X"* / *"make this visual"* could plausibly match either. **Mitigation
  (wiring step 5):** in both descriptions, sharpen the boundary —
  - canvas → emphasize *"on the Obsidian canvas board / add a reference / pin to canvas."*
  - visualize → emphasize *"as a standalone HTML deck/infographic/dashboard to share or
    present."*
  Add a one-line cross-reference in each SKILL.md ("for an Obsidian reference board use
  `canvas`; for a shareable HTML artifact use `visualize`").

**Boundary rule (for docs):**
> `canvas` = arrange existing references on an Obsidian board. `visualize` = generate a new,
> self-contained HTML artifact (deck/infographic/dashboard) from content or wiki knowledge.

---

# 5. RISKS

| # | Risk | Severity | Detail / mitigation |
|---|---|---|---|
| R1 | **SKILL.md bloat (49,959 B / 883 lines) violates progressive disclosure** | **HIGH** | The whole body loads into context whenever the skill triggers. 18 fenced code blocks (full HTML skeletons, CSS, Chart.js) duplicate `references/skeleton.md`, `css-techniques.md`, `design-system.md`, `libraries.md`, `menu.md`, `animations.md`. **Mitigation:** trim SKILL.md to a lean dispatcher (~6-10 KB): keep frontmatter, core principles, output rules, the "which reference to load when" routing table, and the non-negotiables; **move every large code block into the matching existing reference** (most already exist). Target parity with house skills whose SKILL.md is lean and heavy detail lives in `references/`. |
| R2 | **Ships nothing into the markdown vault** | MED | As-is it produces a loose `.html` with no vault linkage. **Mitigation:** define output dir (`wiki/visualizations/` recommended; or `_attachments/`); optionally write a tiny companion wiki stub (frontmatter + link + embed) so the artifact is graph-visible and lint-safe. Decide gitignore policy for generated HTML. |
| R3 | **License / provenance divergence** | MED | Skill is MIT by `careerhackeralex` v0.3.0; repo is MIT by `philippsied`. Compatible licenses, but attribution must be preserved. **Mitigation:** keep the upstream `license`/`metadata.author` in the skill frontmatter; add a one-line provenance/attribution note (e.g. in README "Credits" or a `NOTICE`); do **not** silently relabel authorship. Decide whether to keep upstream `version: 0.3.0` or align to plugin versioning (recommend: keep upstream version in skill metadata, bump only the plugin version). |
| R4 | **Trigger collision with `canvas` on "visual"** | MED | See §4. Mitigation = sharpen both descriptions + cross-reference. |
| R5 | **Skill-count drift across 7 docs** | MED | Known repo pattern. `visualize` currently in **0** docs; integrating without touching all 7 leaves the docs lying ("13 skills"). **Mitigation:** the §6 checklist enumerates every file/line. Consider a tiny check (grep that `skills/` dir count == the literal in README/copilot/windsurf/cursor) to prevent recurrence. |
| R6 | **Frontmatter shape differs from kepano-pure skills** | LOW | Repo's newest skills use only `name`+`description`; `visualize` adds `license`+`metadata`, and older skills add `allowed-tools`. AGENTS.md already says non-recognizing agents "should ignore" extra fields, so extra keys are tolerated. **Mitigation:** optional — leave as-is (tolerated) or add `allowed-tools` for Claude Code parity (it needs Write to emit the HTML; Read for vault content). |
| R7 | **Heaviest review/maintenance surface in repo** | LOW | 157 KB. Mostly mitigated by R1 trim; remainder is acceptable given the value. |
| R8 | **`Archiv.zip` redundancy** | INFO | Out of scope (removed separately). Confirm it's gone before committing so it isn't accidentally tracked. |

---

# 6. WIRING CHECKLIST (exact files to touch — for the LATER session)

> Manifests need **NO skill-array edit** (skills auto-discover). The work is: metadata
> reconciliation, one command alias, output-location decision, trigger normalization, and the
> 7-doc count/list bump.

**Pre-flight (gates):**
- [ ] 0a. Confirm clean git tree on the intended branch; `skills/visualize/Archiv.zip` already
  removed. Stage `skills/visualize/` for tracking.
- [ ] 0b. Confirm SKILL.md trim (R1) is in-scope for this session; if not, record as accepted debt.

**Core wiring (numbered):**
1. **Trim `skills/visualize/SKILL.md`** (R1): reduce to a lean orchestrator; relocate large
   HTML/CSS/JS code blocks into the already-existing matching `references/*.md`; keep a
   "load `references/<x>.md` when …" routing table. (Largest single task.)
2. **Reconcile `skills/visualize/SKILL.md` frontmatter** (R3, R6): preserve `license: MIT` and
   `metadata.author: careerhackeralex`; decide version policy (recommend keep `0.3.0` in skill
   metadata); optionally add `allowed-tools: Read Write Edit Glob Grep` for Claude Code parity.
3. **Normalize the `description` / triggers** (R4): sharpen the visualize/canvas boundary in
   **both** `skills/visualize/SKILL.md` and `skills/canvas/SKILL.md` descriptions; add a
   one-line cross-reference in each. Match house trigger-phrase style (lead with `/visualize`,
   then natural-language triggers, comma-separated — mirror `canvas`).
4. **Create `commands/visualize.md`** (command alias) — copy the `commands/canvas.md` pattern
   exactly:
   - frontmatter: `description:` only (no `name`, no `allowed-tools`);
   - body: `Read the \`visualize\` skill.` + a short operation/intent table
     (e.g. deck / infographic / dashboard / one-pager / from a wiki page);
   - state the default output location chosen in step 6.
5. **Decide + document the output location** (R2): recommend `wiki/visualizations/`
   (graph-adjacent) or `_attachments/`. Update `.gitignore` if generated HTML should be
   ignored. Optionally specify a tiny companion wiki stub for graph/lint visibility. Reflect
   the choice in `commands/visualize.md` and the skill body.
6. **`.claude-plugin/plugin.json`** — no skills array to edit. Optional: confirm `keywords`
   (`"visual"` already present; could add `"html"`, `"presentation"`, `"infographic"`).
   Bump `version` only if cutting a release that includes this skill.
7. **`.claude-plugin/marketplace.json`** — mirror any plugin.json `version` bump in
   `metadata.version`, `plugins[0].version`, and `plugins[0].source.ref` (the `vX.Y.Z` tag).
   No skill-array edit.

**Skill-count / skill-list bump (7 docs — do ALL or docs lie):**
8. `CLAUDE.md` — add a `/visualize` row to the "Plugin Skills" table (L49-65). (No count literal.)
9. `README.md` — (a) bump `**13 skills.**` → `**14 skills.**` (L15); (b) bump tree comment
   `# 13 skills` → `# 14 skills` and add a `│   ├── visualize/` node with `references/` (L329);
   (c) optional: add `/visualize` rows to the command table (L119-134).
10. `AGENTS.md` — add a `visualize` row to the "Available Skills" table (L25-41). (No count literal.)
11. `GEMINI.md` — add a `visualize` row to the "Skills" table (L19-35). (No count literal.)
12. `.github/copilot-instructions.md` — L13: bump `13 skills` → `14 skills` **and** insert
    `\`visualize\`` into the explicit name list.
13. `.windsurf/rules/claude-obsidian.md` — bump `13 SKILL.md files` (L15) and `all 13 skills`
    (L30) → 14; add a `- \`visualize\`: …` bullet to the list (L32-44).
14. `.cursor/rules/claude-obsidian.mdc` — bump `13 skills` (L19) → 14; add a `visualize` row to
    the table (L23-37).
15. (Verify) grep `bin/setup-multi-agent.sh` for any hard-coded skill count; update if present.

**Post-wiring verification:**
16. Re-grep repo for the literal `13` in skill contexts → expect **0** stale hits.
17. Re-grep `visuali[sz]e` repo-wide → expect hits now in all 7 docs + new command alias.
18. Confirm `ls skills/ | wc -l` == the count literal everywhere (== 14).
19. Smoke test: trigger the skill ("make a one-pager from wiki page X"), confirm HTML lands in
    the chosen output dir and (if stub chosen) the companion wiki note is created and lint-clean.

**File-touch tally (excluding pure verification/grep steps 15-19):**
`skills/visualize/SKILL.md`, `skills/canvas/SKILL.md`, `commands/visualize.md` (new),
optional `.gitignore`, `.claude-plugin/plugin.json` (optional/version), `.claude-plugin/marketplace.json`
(optional/version), `CLAUDE.md`, `README.md`, `AGENTS.md`, `GEMINI.md`,
`.github/copilot-instructions.md`, `.windsurf/rules/claude-obsidian.md`,
`.cursor/rules/claude-obsidian.mdc` → **13 files** (11 required + 2 optional manifest/gitignore).

---

# 7. OPEN QUESTIONS

1. **Output location:** `wiki/visualizations/`, `_attachments/`, or user-chosen per call?
   (Recommendation: `wiki/visualizations/`.) Affects R2, steps 4-5.
2. **Companion wiki stub:** should each generated HTML get a tiny markdown note (frontmatter +
   embed/link) so it joins the graph and lint? Or keep HTML purely as an attachment?
3. **Gitignore policy:** are generated visualizations committed (reproducible artifacts in the
   vault) or ignored (treated as ephemeral output)?
4. **Version reconciliation:** keep upstream `version: 0.3.0` in the skill's `metadata`, or
   align it to the plugin's semver? And does adding this skill warrant a plugin minor bump
   (→ 1.11.0) on the next release cut?
5. **`allowed-tools`:** add it for Claude Code parity (the skill must `Write` HTML), or stay
   kepano-pure (`name`+`description` only) like the newest skills?
6. **Attribution mechanism:** where does `careerhackeralex` credit live — README "Credits", a
   `NOTICE` file, or only the skill frontmatter?
7. **Trim depth:** how aggressive is the SKILL.md trim — pure dispatcher (~6 KB) or
   keep-most-prose (~15 KB)? Trade-off: triggering reliability vs context cost.
8. **Lint awareness:** should `wiki-lint` learn about `wiki/visualizations/` (skip or validate
   it), the way it already skips `_attachments`, `_templates`, `meta`, `folds`?
9. **Does `bin/setup-multi-agent.sh` hard-code "13" anywhere** (count or list)? (Verify in §6 step 15.)

---

# 8. Phased plan

**Phase A — Assess (DONE; this document).** Decision: integrate, conditional on §0.

**Phase B — Trim SKILL.md.** Execute wiring step 1 (+2). Reduce SKILL.md to lean orchestrator;
relocate code blocks to existing `references/`. *Gate:* SKILL.md ≤ ~10 KB and no behavioral
regression in a quick deck/infographic/dashboard smoke test.

**Phase C — Wire.** Steps 3-7: trigger normalization + cross-reference, `commands/visualize.md`,
output-location decision + optional `.gitignore`, optional manifest version bump.
*Gate:* skill triggers correctly; no collision with `canvas` on representative prompts.

**Phase D — Docs.** Steps 8-14 (all 7 count/list docs) + step 15. *Gate:* grep shows 0 stale
"13" in skill contexts; `visualize` present in all 7 docs.

**Phase E — Test + release.** Steps 16-19 verification; end-to-end "from wiki knowledge → HTML
export (+ optional stub)"; lint clean. Cut release (plugin + marketplace version) if desired.

---

# Appendix A — exact anchors for the count/list edits

- `README.md:15` — `… **13 skills. Zero manual filing. …**`
- `README.md:329` — `├── skills/                      # 13 skills (Agent Skills format)`
- `CLAUDE.md:49-65` — `## Plugin Skills` table (13 rows; add `/visualize`)
- `AGENTS.md:25-41` — `## Available Skills` table (13 rows; add `visualize`)
- `GEMINI.md:19-35` — `## Skills` table (13 rows; add `visualize`)
- `.github/copilot-instructions.md:13` — `- \`skills/\`: 13 skills (\`autoresearch\`, …, \`wiki-query\`), …`
- `.windsurf/rules/claude-obsidian.md:15` — `├── skills/              ← 13 SKILL.md files …`
- `.windsurf/rules/claude-obsidian.md:30` — `… Cascade auto-discovers all 13 skills:` (+ bullet list L32-44)
- `.cursor/rules/claude-obsidian.mdc:19` — `- **Skills**: 13 skills under \`skills/<name>/SKILL.md\` …` (+ table L23-37)

# Appendix B — command-alias template (from commands/canvas.md, to mirror for commands/visualize.md)

```
---
description: <one line — generate a self-contained HTML visualization (deck/infographic/dashboard) from content or a wiki page>
---

Read the `visualize` skill. Then run the operation matching the user's command.

| Command | What it does |
|---------|-------------|
| `/visualize` | ... |
| `/visualize deck [topic|page]` | ... |
| `/visualize infographic [...]` | ... |
| `/visualize dashboard [...]` | ... |

Default output: `wiki/visualizations/<name>.html`   # (pending Open Question #1)
```
