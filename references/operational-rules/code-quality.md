# Code Quality

- Only make changes directly requested. No unrequested refactoring,
  no feature additions, no "while we're at it" improvements.
- One change at a time. Test after each. Never bundle untested changes.
- When a function exceeds 40 lines, consider extracting — but only
  if explicitly asked or if it directly serves the current task.
- Prefer explicit over clever. Readability beats brevity.
- No placeholder content ("TODO: implement later", "lorem ipsum").
  If real content is unavailable, ask.
- When you encounter a bug unrelated to the current task, mention it
  but do not fix it unless asked.
- NEVER write tests that validate mocked behavior instead of real logic.
