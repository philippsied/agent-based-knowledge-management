---
type: meta
title: "Pending Commits"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags:
  - meta
  - commits
status: developing
---

# Pending Commits

Append-at-top queue of Conventional Commit-shaped proposals produced by the autoresearch / ingest / save skills. Each block is one logical commit. Delete blocks as they are committed; never edit prior blocks.

Format:

```
## YYYY-MM-DD HH:MM — <task-id-or-topic>

### <type>(<scope>): <subject>
- path/to/file-1
- path/to/file-2

### chore(wiki): refresh coordinator files for <task-id>
- wiki/hot.md
- wiki/index.md
- wiki/log.md
```

Conventions:

- **One block per skill run.** Multi-run sessions stack at the top; oldest at the bottom.
- **Cluster boundaries match commit boundaries.** Each `### <type>(<scope>):` sub-section becomes exactly one `git commit`.
- **Coordinator files live in their own `chore(wiki):` cluster** — never bundled with `feat(research):` content.
- **Unrelated `git status` entries** (lint scripts, raw clippings, etc.) go under `### chore(repo): unrelated changes — confirm before committing` so the user can split or bundle.
- **After committing a block**: delete it from this file. Empty file = clean tree.

---

<!-- New blocks added by skills appear above this line -->
