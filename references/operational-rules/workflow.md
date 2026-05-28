# Workflow Conventions

## Read first, propose second, execute third

Before any non-trivial task:

1. Read CLAUDE.md, AGENTS.md, and any README in the working directory.
2. Surface the relevant conventions in a brief summary.
3. Present 2-3 approaches with trade-offs and ask, unless the request is
   bounded and obvious (typo, single-line rename, etc.).

Skipping this step has caused recurring friction: `rm` instead of `git mv`,
wrong-runtime assumptions during script migrations, over-aggressive bulk
edits. The cost of one read pass is far smaller than a corrective second pass.

## Renames use `git mv`

When relocating a tracked file or directory, use `git mv` so rename detection
works downstream. Never use `rm <old>` followed by a fresh `git add <new>` —
the diff loses the rename hint and code review gets noisier.

If a path moved without `git mv`, recover via `git mv -k` (or restage the
delete+add as a single rename in `git status`). Do not amend published
commits to fix it.

## Bash defensive guards

Scripts using `set -euo pipefail` MUST guard:

- **Optional probes**: wrap `command -v <tool>` in `|| true` when the
  presence of the tool is itself the question, not an error.
- **`find` on possibly-missing paths**: pre-check existence
  (`[[ -d "$dir" ]] && find "$dir" ...`) or use `find ... 2>/dev/null`
  when missing-paths are expected.
- **Empty-iteration**: `for f in $glob; do ...` with no matches expands
  to the literal pattern under nullglob-off shells. Set `shopt -s nullglob`
  or guard with `[[ -e "$f" ]]`.

Pipefail catches real bugs, but only when probes are explicitly classified
as "expected to fail sometimes" via `|| true` or guards.

## Bash CWD Discipline

Bash tool state persists between calls — `cd <subdir>` in turn 1 leaks into
turn 5. This caused real failures during Step 6b ("plans/...: No such file"
after a stale `cd PROJECTS/...`).

Rule: prefer absolute paths or `git -C <abs-path>` / `find <abs-path>` over
`cd`. If `cd` is unavoidable, every subsequent Bash call MUST either

- (a) `cd` back, or
- (b) use absolute paths.

Fast-check before each multi-line Bash call: does the command rely on the
session CWD being the repo root? If yes, prefix with `cd` to absolute repo
root or rewrite using absolute paths.

## Vault-coordinator cross-sync

`wiki/hot.md`, `wiki/index.md`, `wiki/log.md`, `wiki/meta/research-queue.md`,
`wiki/meta/OPEN-ISSUES.md` share state: page counts, queue state, recent
activity, open issues. After editing any one of them, surface impact on the
others in the same pass — log entries imply hot.md update, queue flips imply
index.md activity-section update.

On conflict, `wiki/log.md` (append-only history) is authoritative; `hot.md`
is derived. Coordinator files should never diverge longer than one session.
