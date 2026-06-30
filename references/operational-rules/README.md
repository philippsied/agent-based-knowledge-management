# Operational Rules — opt-in reference pack

Modular rule files that govern how an agent operates against this vault. They are intentionally **not** auto-installed by `bin/setup-vault.py` because they impose strong conventions (atomic commits, sandbox awareness, verification-before-change). Adopt them on a per-vault basis.

## How to install

```bash
mkdir -p "$VAULT/.claude/rules"
cp -i "${CLAUDE_PLUGIN_ROOT}/references/operational-rules/"*.md "$VAULT/.claude/rules/"
```

Then point `CLAUDE.md` at the rules directory, e.g.:

```markdown
## Operational rules

Read every file under `.claude/rules/` once at session start. Rules apply
in addition to anything in CLAUDE.md, never instead of.
```

Pick the rules you want — they are designed to be independent files, not a monolith.

## What each rule does

| File | Scope |
|---|---|
| `agent-principles.md` | Verification-before-change, honesty, discipline. The "always-on" baseline. |
| `architecture-defaults.md` | Agent-native over subprocess-to-CLI. Skill frontmatter version path. |
| `atomic-tasks-and-commits.md` | One TodoWrite item = one logical commit. 200 LOC ceiling per uncommitted diff. Decomposition trigger for N-item batches. |
| `code-quality.md` | Smallest meaningful change. No drive-by refactors. No placeholder content. |
| `communication.md` | 1–2 sentence post-task statements. No flattery. Cite real file:line references. |
| `git.md` | Conventional commit conventions. `fix:` vs `feat:` discipline. Empty-dir tracking via `.gitkeep`. |
| `identifiers.md` | ASCII identifiers, kebab-case, marketplace-name reservations. |
| `project-locality.md` | No global config writes. Plans + memory stay in-project. |
| `resumption.md` | Continue cues ("weiter", "continue") resume the in-progress todo without re-asking. |
| `sandbox.md` | Sandbox-denial handoff protocol. Never work around denials silently. |
| `security.md` | Pause-and-confirm list for irreversible actions. |
| `testing.md` | Test discipline conventions (project-specific — review before adopting). |
| `workflow.md` | Read first / propose second / execute third. `git mv` for renames. Bash CWD discipline. Vault-coordinator cross-sync. |

## Why "opt-in" rather than installed

These rules grew out of one specific vault's experience (`ai-secondbrain`). They impose real friction:

- The atomic-commits rule forces decomposition for multi-item batches and a strict 200 LOC ceiling. Useful for ML/research vaults where each finding wants a separable commit; overkill for personal notes vaults.
- The agent-native-over-CLI rule rules out a class of useful subprocess workflows.
- The verification-before-change rule slows down trivial edits.

Adopt the subset that matches your vault's stakes. The README and audit trail under `wiki/log.md` (auto-maintained) become your governance surface — these rules sharpen what gets recorded there.

## Rationale references

Most rules cite a specific incident or retro that produced them. Read the source vault's `wiki/log.md` and `wiki/meta/OPEN-ISSUES.md` for the original context before adopting heavyweight rules.
