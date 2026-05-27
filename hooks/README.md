# agentic-knowledge-management Hooks

Plugin hooks for the agentic-knowledge-management wiki vault. All hooks are defined in `hooks.json`.

## Events

| Event | Type | Purpose |
|---|---|---|
| `SessionStart` | command + prompt | Loads `wiki/hot.md` into context. Command type runs `[ -f wiki/hot.md ] && cat wiki/hot.md` as the canonical safety check (works for non-vault sessions without erroring). Prompt type complements with semantic context restoration. Matcher: `startup\|resume`. |
| `PostCompact` | prompt | Re-loads `wiki/hot.md` after context compaction. Hook-injected context does NOT survive compaction (only `CLAUDE.md` does), so this hook restores the hot cache mid-session. |
| `PostToolUse` | command | Auto-commits any wiki/ or .raw/ changes after Write or Edit tool calls. Guarded by `[ -d .git ]` so it never errors in non-git directories, and by `git diff --cached --quiet` so it never creates empty commits. |
| `Stop` | prompt | Updates `wiki/hot.md` at the end of every Claude response with a brief summary of what changed. |

## Hook Output Contract (resolved)

Earlier versions of this README documented `anthropics/claude-code#10875` ("Plugin hooks JSON output not captured") as an active blocker. That issue is **closed (completed)** as of 2025-11-06. Per @dicksontsai's clarification in the thread, the root cause was never a missing STDOUT capture but a mixed-signaling pattern in hook authors' code.

**The rule**: a hook must commit to one output contract and not mix them.

- **Exit-2 + stderr**: write the block reason to stderr, exit with code 2. Claude Code treats whatever is on stderr as the block message. Simple, no JSON parsing.
- **Advanced JSON API + stdout + exit 0**: write a structured JSON payload (e.g. `{"continue": false, "stopReason": "..."}`) to stdout, exit 0. Claude Code parses and acts on the JSON.

Mixing the two (JSON to stderr with exit 2, or JSON to stdout with exit 2) used to behave inconsistently between inline hooks and plugin hooks; the inconsistency is what 10875 tracked. After the upstream fix, the behavior is uniform: pick one approach.

**Hooks in this plugin are on the safe path**: every command hook ends in `|| true` so it always exits 0, and any meaningful output goes to stdout. No JSON-to-stderr or exit-2 patterns. Compatible with both inline and plugin installs.

For Ruby-based hook stacks, see the parallel fix landed in `gabriel-dehan/claude_hooks#15` (merged 2026-01-04), which rewrites Stop hooks in the `claude_hooks` gem from `stderr + exit 2` to `stdout + exit 0`.

**Self-test** (still useful as a smoke check): open a fresh Claude Code session in a directory containing a populated `wiki/hot.md`. Ask "what's in the hot cache?". Claude should be able to answer from the SessionStart-injected context.

## Non-Vault Sessions

The SessionStart command hook uses `[ -f wiki/hot.md ] && cat wiki/hot.md || true` so it always exits 0, even when no vault is present. This makes the plugin safe to install globally without breaking non-vault Claude Code sessions.
