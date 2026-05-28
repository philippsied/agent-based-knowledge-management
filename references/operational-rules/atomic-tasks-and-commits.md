# Atomic Tasks & Commit Cadence

## Decomposition trigger

Any work originating from a numbered multi-item spec block (PRD §X "Step Yb"
with N sub-items, plan checklist with N rows, issue with N acceptance
criteria) MUST be decomposed into N TodoWrite items BEFORE the first
Edit/Write/NotebookEdit call.

The decomposition is non-optional regardless of estimated total size.
"It's only 5 small items" does not justify a single bundled diff.

## Commit cadence

One TodoWrite item = one logical commit. After marking an item `completed`,
run the project's commit workflow (`commit-commands:commit`) or stage +
commit manually with `git mv`-aware staging per `.claude/rules/git.md`.

Exceptions:

- Pure formatter passes (`ruff format` after a logical commit) may piggyback.
- Test-only follow-ups that pin behavior introduced by the previous commit
  may piggyback into the same commit message scope.

Never:

- Bundle 2+ orthogonal sub-items into one commit.
- Defer all commits to "end of session" -- verification-after-each-item is
  the value the cadence buys.

## LOC ceiling

Single uncommitted diff > 200 LOC across tracked files (incl. submodule
changes) is a bug, not a feature. The `enforce-atomic-tasks` hook
(`.claude/hooks/enforce-atomic-tasks.sh`) reflects this. Do not bypass via
env override unless the diff is genuinely one logical unit (e.g. mass rename
produced by a single `git mv`).

## Session-start protocol for "Resume Step Xb"

When the prompt phrase contains "Step Xb", "Pre-Step-N block", "5 items", or
any plan-pointer indicating a multi-item batch:

1. Read the spec block.
2. Build the TodoWrite list (one item per spec sub-item).
3. The PostToolUse:TodoWrite hook auto-touches
   `.claude/.session-todo-active` so the atomic-tasks hook unblocks.
4. Execute item 1 -> tests green -> commit -> mark item completed.
5. Repeat for each item.

This is the default. The user does not need to repeat it in the prompt.

## Override discipline

`ATOMIC_TASK_LOC_THRESHOLD=99999` exists for genuine one-logical-unit diffs
(big rename, single regenerated lockfile, vendored snapshot). Do NOT export
it just to silence the hook on a real multi-item batch. If the hook fires
and the user has not explicitly authorized an override, decompose first.
