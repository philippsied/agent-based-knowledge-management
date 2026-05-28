# Resumption Protocol

When a previous turn was interrupted (stream idle timeout, usage limit, manual
stop) and the user types a continuation cue — "weiter", "Weiter", "continue",
"go on", "mach weiter" — resume immediately without re-asking for context.

Resumption sequence:

1. Read the in-progress TodoWrite item (top of the list with status
   `in_progress`).
2. If no TodoWrite exists, run `git status` and `git log --oneline -3` to
   reconstruct where work stopped.
3. State in one sentence what is being resumed, then continue executing.

Do NOT:

- Restate the original task at length.
- Ask "where would you like to continue?" — the cue itself is the answer.
- Mark the in-progress todo complete unless the underlying work is truly done.

If the resumption point is genuinely unclear (no todo, ambiguous git state),
ask one focused question identifying the gap, not a generic "what's next".
