# agentic-knowledge-management — Claude + Obsidian Wiki Vault

This folder is both a Claude Code plugin and an Obsidian vault.

**Plugin name:** `agentic-knowledge-management`
**Skills:** `/wiki`, `/wiki-ingest`, `/wiki-query`, `/wiki-lint`
**Vault path:** This directory (open in Obsidian directly)

## What This Vault Is For

This vault demonstrates the LLM Wiki pattern — a persistent, compounding knowledge base for Claude + Obsidian. Drop any source, ask any question, and the wiki grows richer with every session.

## Vault Structure

```
.raw/           source documents — immutable, Claude reads but never modifies
wiki/           Claude-generated knowledge base
_templates/     Obsidian Templater templates
_attachments/   images and PDFs referenced by wiki pages
```

## How to Use

Drop a source file into `.raw/`, then tell Claude: "ingest [filename]".

Ask any question. Claude reads the index first, then drills into relevant pages.

Run `/wiki` to scaffold a new vault or check setup status.

Run "lint the wiki" every 10-15 ingests to catch orphans and gaps.

## Cross-Project Access

To reference this wiki from another Claude Code project, add to that project's CLAUDE.md:

```markdown
## Wiki Knowledge Base
Path: /path/to/this/vault

When you need context not already in this project:
1. Read wiki/hot.md first (recent context, ~500 words)
2. If not enough, read wiki/index.md
3. If you need domain specifics, read wiki/<domain>/_index.md
4. Only then read individual wiki pages

Do NOT read the wiki for general coding questions or things already in this project.
```

## Plugin Skills

| Skill | Trigger |
|-------|---------|
| `/wiki` | Setup, scaffold, route to sub-skills |
| `/wiki-ingest` (or `ingest [source]`) | Single or batch source ingestion (files, URLs, images) |
| `/wiki-query` (or `query: [question]`) | Answer questions from wiki content (Quick / Standard / Deep modes) |
| `/wiki-lint` (or `lint the wiki`) | Health check: orphans, dead links, gaps, stale claims |
| `/wiki-fold` | DragonScale Mechanism 1 — rollup of log entries into meta-pages |
| `/wiki-issues` (or "handoff" / "fix issues") | Own the `wiki/meta/OPEN-ISSUES.md` stack — push session insights as issues, or pop-and-work the top ready issue |
| `/save` | File the current conversation or insight as a structured wiki note |
| `/autoresearch [topic]` | Autonomous research loop (search, fetch, synthesize, file) with optional topic selection |
| `/canvas` | Visual layer: add images, text, PDFs, wiki pages to Obsidian canvas |
| `/visualize` | Turn wiki pages/knowledge into self-contained HTML decks, infographics, dashboards |
| `/defuddle` | Strip clutter from URLs before ingest (40-60% token savings) |
| `/doc-pipeline` | Convert `.doc/.docx/.pdf/.pptx/.xlsx/...` into ingest-ready Markdown with QC gate |
| `/obsidian-bases` | Create and edit Obsidian Bases (`.base`) database-style views |
| `/obsidian-markdown` | Obsidian-flavored Markdown / wikilink / callout helpers |
| `/research-brief` | Construct or audit autoresearch briefs against W1-W12 conventions |

## Conventions & Editing

Single entry point to where each editing convention authoritatively lives (SSOT — do not duplicate here):

| When you edit… | Follow the convention in… |
|---|---|
| Vault pages (frontmatter, wikilinks, `YYYY-MM-DD` dates, `.raw/` immutability, `wiki/log.md` append-only, `wiki/hot.md` overwrite-at-session-end) | `references/operational-rules/workflow.md` |
| Agent behavior / operating principles | `references/operational-rules/agent-principles.md` |
| Custom callouts (`[!contradiction]`, `[!gap]`, `[!key-insight]`, `[!stale]`) | `skills/obsidian-markdown/SKILL.md` + `skills/wiki/references/css-snippets.md` |
| A skill (`skills/<name>/SKILL.md`; frontmatter = `name` + `description`) | `skills/obsidian-markdown/SKILL.md` |
| Hooks (`hooks/hooks.json`; valid events: SessionStart, Stop, PreToolUse, PostToolUse, PreCompact, PostCompact, UserPromptSubmit) | `hooks/hooks.json` (SSOT) |
| Anything advertising the skill count | `tests/test_skill_count_ssot.py` guards the tracked `skills/*/SKILL.md` set |

## MCP (Optional)

If you configured the MCP server, Claude can read and write vault notes directly.
See `skills/wiki/references/mcp-setup.md` for setup instructions.
