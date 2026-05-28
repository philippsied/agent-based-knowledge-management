# Git Conventions

## Commit Messages

- Write in imperative mood: "Add feature" not "Added feature"
- Prefix: feat:, fix:, refactor:, docs:, test:, chore:
- Keep the first line under 72 characters

## Type selection (fix vs feat)

- Default to `fix:` when in doubt. A change that remedies broken or missing
  behavior is `fix:` even when implemented by adding code; net additions do
  not turn a fix into a `feat:`.
- Reserve `feat:` for capabilities the user could not previously accomplish.
- Use the most precise type otherwise (`refactor:`, `docs:`, `test:`, `chore:`,
  `perf:`, `ci:`, `build:`, `style:`).
- Heuristic: if a regression test you could write today would have failed
  *before* the change, it is `fix:`.
- Never apply `!` or a `BREAKING CHANGE:` footer without explicit confirmation
  — those markers trigger automatic major-version bumps in release tooling.

## Component scope

- Include a narrow scope: skill name, agent name, plugin name, or area
  (`marketplace`, `lifecycle`, `rules`).
- Avoid scope `agent-skill-hub` — it tells the reader nothing.

## Rules

- Do not commit generated files, build artifacts, or secrets.
- Do not amend or force-push without explicit confirmation.
- When asked to commit, stage only files related to the current task.
- Track empty directories with `.gitkeep` — Git ignores empty folders.
- Remove `.gitkeep` once real files exist in the directory.
- For new project structures: place `.gitkeep` in every empty directory BEFORE committing.
- Create a meaningful `.gitignore` BEFORE the first commit — OS files (.DS_Store),
  editor files, secrets (.env), build artifacts.
