# Architecture Defaults

## Agent-native over subprocess-to-CLI

When a skill, plugin, or script needs Claude-level reasoning (summarizing,
classifying, fan-out audits), use the Agent tool / subagent delegation.
NEVER shell out to the `claude` CLI as a subprocess.

Why: a subprocess call requires an API key, runs outside the session's
permission model, and forces manual user work the agent-native path avoids.
This was caught and rearchitected once (INDEX generator build); the rule
exists so it is not reintroduced.

How to apply: if you are about to write `claude -p`, `subprocess.run(["claude"...`,
or any shell invocation of the CLI, stop and convert it to an Agent call,
with parallel fan-out where the units are independent.

## Skill frontmatter version path

Skill and plugin version lives at `metadata.version` in frontmatter, never as
a top-level `version:` key. Release tooling reads `metadata.version`; a
top-level key is silently ignored and ships an unversioned artifact. Validate
this before any release commit.
