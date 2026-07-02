# Multi-agent salvage — provenance map before deletion (S1 of SPEC-2.0.0-consolidation)

Before deleting `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`, and
`bin/setup-multi-agent.py` (S2), every content block is enumerated here with a disposition:

- `covered-by→<path>` — the content already has a single-source-of-truth elsewhere; deletion loses nothing.
- `moot` — only meaningful for the multi-agent setup being removed (Claude auto-discovers via `.claude-plugin/`).
- `folded→<path>` — genuinely worth keeping for Claude; relocated (grep-verifiable at the target).
- `discard` — redundant AND partly stale/incorrect; not worth relocating.

**Outcome:** nothing in the three files is unique operational knowledge. Every convention
already has an SSOT in `skills/*`, `references/operational-rules/*`, `hooks/hooks.json`,
`README.md`, or `CLAUDE.md`. One block is folded: a **Conventions & Editing** pointer section
added to `CLAUDE.md`, which preserves copilot's one-entry-point navigational value for Claude
without duplicating any convention text.

## AGENTS.md

| Block | Disposition |
|---|---|
| A1 Cross-platform intro (Codex/OpenCode/Agent Skills spec) | `moot` — Claude-only |
| A2 `allowed-tools` cross-agent compat note | `moot` — Claude reads the field natively |
| A3 Skills discovery via symlink + `setup-multi-agent.py` | `moot` — Claude auto-discovers via `.claude-plugin/` |
| A4 Available-skills trigger table (15 rows) | `covered-by→CLAUDE.md` (Plugin Skills table) + each `skills/*/SKILL.md` description (SSOT) |
| A5 Key Conventions (vault root / hot cache / `.raw` immutable / manifest) | `covered-by→references/operational-rules/workflow.md` + `CLAUDE.md` (Vault Structure) |
| A6 Bootstrap steps (read hot.md silently, …) | `covered-by→hooks/hooks.json` (SessionStart) + `skills/wiki/SKILL.md` |
| A7 Reference links (homepage / karpathy / kepano) | `covered-by→README.md` |

## GEMINI.md

| Block | Disposition |
|---|---|
| G1 Gemini/Antigravity intro | `moot` — Claude-only |
| G2 Skills discovery via `~/.gemini` symlink + installer | `moot` |
| G3 Skills "what it does" table (15 rows) | `covered-by→CLAUDE.md` + `skills/*/SKILL.md` |
| G4 Trigger-phrase examples | `covered-by→skills/*/SKILL.md` descriptions (SSOT) |
| G5 Vault Conventions | `covered-by→references/operational-rules/workflow.md` + `CLAUDE.md` |
| G6 Bootstrap | `covered-by→hooks/hooks.json` + `skills/wiki/SKILL.md` |
| G7 Project Links | `covered-by→README.md` |

## .github/copilot-instructions.md

| Block | Disposition |
|---|---|
| C1 Project intro / type | `covered-by→README.md` + `CLAUDE.md` |
| C2 Repository Layout (15 skills enumerated) | `covered-by→README.md` + `tests/test_skill_count_ssot.py` (SSOT) |
| C3 Conventions (frontmatter plural keys / wikilinks / dates / `.raw` / `log.md` append-only / `hot.md` overwrite / callouts) | `covered-by→references/operational-rules/workflow.md` + `skills/obsidian-markdown/SKILL.md:83` (callouts) + `skills/wiki/SKILL.md:153` (log.md). NOTE: the "skills use no `allowed-tools`" claim is **stale** — `skills/wiki` + `skills/obsidian-markdown` still carry it → `discard` that line |
| C4 When Editing Skills (frontmatter/body style) | `covered-by→skills/obsidian-markdown/SKILL.md` + skill-creator conventions |
| C5 When Editing Hooks (valid event names / types / matcher) | `covered-by→hooks/hooks.json` (SSOT) + `docs/prds/agentic-wiki.md` |
| C6 Cross-Reference | `discard` — points at wrong upstream fork `AgriciDaniel/claude-obsidian`; `README.md` has the correct homepage |

## Fold (the one kept block)

| Fold | Target | What it preserves |
|---|---|---|
| F1 — a **Conventions & Editing** pointer section indexing the convention SSOTs | `folded→CLAUDE.md` | copilot's single-entry-point value: one place in Claude's primary context file that points at where each editing convention authoritatively lives (no convention text duplicated) |
