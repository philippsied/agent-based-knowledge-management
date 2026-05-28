# Project Locality

Everything stays inside the project directory. Do NOT modify global config.

| Artifact | Location | NOT here |
|----------|----------|----------|
| Plans | `./plans/` in the project | `~/.claude/plans/` |
| Memory | `./memory/` in the project | `~/.claude/projects/.../memory/` |
| Generated files | Current working directory | Anywhere outside |
| Project permissions | `.claude/settings.local.json` | `~/.claude/settings.json` |
| Slash commands | `.claude/commands/` in the project | `~/.claude/commands/` (only if global) |

**Only exception:** Skills under `~/.claude/skills/` — technically enforced by Claude Code.

**FORBIDDEN:**
- Modifying `~/.claude/settings.json` (global config)
- Writing files outside the workspace (except `~/.claude/skills/`)
- Storing plans or memory in `~/.claude/`
