# Identifiers and Naming

## ASCII identifiers only

File names, plugin names, skill names, agent names, command names, and
marketplace entry names: ASCII only, kebab-case (lowercase, hyphen-separated,
no underscores, no Unicode). Converters and regex patterns rely on it.

## Kebab-case rules

- Lowercase letters, digits, hyphens. Start with a letter.
- Good: `audit-skill`, `marketplace-tools`, `create-agent-skills`.
- Bad: `auditSkill`, `audit_skill`, `Audit-Skill`, `02-audit-skill`.

## Reserved marketplace names

The Claude Code marketplace blocks names like `claude-code-marketplace`,
`anthropic-plugins`, `agent-skills`, plus impersonating prefixes (`official-…`,
`anthropic-…`). Pick a distinctive name; check before publishing.

## Markdown tables and prose

- **Tables:** pipe-delimited (`| col | col |`), never box-drawing characters.
- **Prose:** Unicode is fine (emoji, em-dashes, etc.).
- **Code blocks and terminal examples:** prefer ASCII arrows (`->`, `<-`).
