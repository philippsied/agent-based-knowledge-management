# Sandbox Awareness

The Bash sandbox in this environment denies certain operations by default.
When a sandbox denial blocks progress, STOP and hand the exact command off
to the user — do not retry with workarounds that obscure the boundary.

## Commonly blocked operations

| Operation | Reason | Handoff form |
|-----------|--------|--------------|
| `gh` CLI auth-bound calls | `~/.config/gh/` denied | Print the command, ask user to run it locally |
| `rm -rf` outside the project | Write paths restricted | Confirm scope, ask user to run the cleanup |
| Writes to `~/.claude/settings.json` | Global config forbidden by `project-locality.md` | Refuse and document why |
| Cache writes outside `$TMPDIR` (e.g. `~/.cache/uv`) | Sandbox blocks `~/.cache` | Run interactively from the user's shell |
| Reads from `~/.ssh`, `~/.gnupg`, credential stores | Always denied | Never attempt — these are policy, not bug |

## Never work around

If a sandbox denial appears, do not:

- Pipe through alternative shells (`zsh -c`, `sh -c`) hoping for different rules.
- Move artifacts into allowed paths just to bypass a write-deny on the canonical path.
- Disable the user's hooks/wrappers (e.g. the project-level `python3 → uv run python3` rewriter).
- Use `--no-verify` / `--no-gpg-sign` to skip safety nets unless the user explicitly asked.

Document the blocked command in the response so the user can re-run it
locally with an explanation of what it would have done. That handoff is the
correct outcome, not a failure.

## Pre-flight before risky chains

Before a chain that depends on a tool that may be denied (commits, pushes,
GitHub API calls, worktree cleanup), do a single test invocation first
(e.g. `git status`, `gh auth status`) and react to denial early instead of
mid-chain.
