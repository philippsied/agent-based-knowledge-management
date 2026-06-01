# Revised Plan: Soft-Mode for wiki-path-safety (v1.10.0)

Status: REVIEW of `docs/plans/v1.10.0-soft-path-safety-hook.md` (DRAFT 2026-06-01).
Author: review session 2026-06-01. Supersedes the DRAFT.
Persisted here under `.vault-meta/` because the hook (correctly!) blocked
writes to `docs/plans/` during the review session — see Context.

## Context

The v1.9.1 guards solved the cross-repo case: a non-vault repo passes the hook
untouched. The remaining gap is the "mixed" repo — both a vault and an active
non-wiki work tree (the plugin's own dev repo is the canonical example, and
this very review session hit the bug live: writing this plan file to
`docs/plans/` was blocked because `docs/` is not in the whitelist). In strict
mode the hook hard-blocks any non-wiki write, which makes Bash, Edit, and
Write impractical on legitimate plugin code, tests, docs, lib, hooks.

The DRAFT plan addresses this but ships with three unnecessary modes, an env
override that does not behave as documented, an empirical "Phase 0" that has
since been resolved by upstream docs, and a backward-compatibility framing
that the user explicitly waived. This revision narrows scope so the change is
small, testable, and forward-only — no migration debt accrued.

Outcome: a mixed-mode vault treats wiki-whitelist paths as today (silent
allow, hard rules for `.raw/` immutability and wiki filename hyphenation) but
converts non-whitelist in-vault paths from `exit 2` blocks into model-visible
reminders via `permissionDecision: allow` + `additionalContext`. Non-vault and
out-of-vault paths are unchanged.

## Decisions locked from review

1. **Two modes only.** `strict` (default) and `mixed`. `off` dropped —
   deleting `.vault-meta/` already neutralizes the hook via Guard A. YAGNI
   eliminated.
2. **Single config source.** `.vault-meta/config.json`. No env override.
   `KM_PATH_SAFETY` removed entirely — env in subprocess hooks freezes at
   session start, so a runtime override is misleading. Live toggle = edit
   `config.json` (cost: ~1ms re-read per Write/Edit, negligible).
3. **Reminder mechanism = Option B, verified.** Official docs
   (https://docs.claude.com/en/docs/claude-code/hooks) confirm
   `hookSpecificOutput.additionalContext` is model-visible for `PreToolUse`,
   inserted as a system reminder next to the tool result. No Phase 0 / no
   empirical sandbox needed. Option C (stderr + exit 0) explicitly rejected —
   stderr is only forwarded to the model on exit 2.
4. **Config is mandatory, with auto-migration.** Setup writes `config.json`
   on fresh installs. Existing vaults get it on the next hook fire (hook
   bootstraps `{"version":1,"path_safety_mode":"strict"}` idempotently the
   first time it can't find the file). Hook never has a "missing config"
   long-tail branch.
5. **Schema versioned from day one.** `{"version": 1, ...}`. One line now
   eliminates a migration phase the next time the file grows a field.
6. **Wiki-context detection stays path-based.** Skill-aware detection ruled
   out for v1.10.0 (`KM_WIKI_CONTEXT` hint is unreliable across tool calls).
7. **Backward compatibility waived.** User has full control over all
   installs. Plan no longer carries BC framing.

## Config schema

`.vault-meta/config.json`:

```json
{
  "version": 1,
  "path_safety_mode": "strict"
}
```

- `version` (int, required): schema version. Hook rejects unknown versions
  with a clear warning and falls back to strict.
- `path_safety_mode` (string, required): `"strict"` | `"mixed"`. Anything
  else → fall back to `strict` and emit a warning to stderr.

Malformed JSON → fall back to `strict`, emit one-line warning. Same for
missing `version` (treat as `1`) and missing `path_safety_mode` (treat as
`strict`).

## Mode semantics

| Path class                                              | strict | mixed |
| ------------------------------------------------------- | ------ | ----- |
| `wiki/*` (excl. `_templates/`, `lint-…`)                | allow + name rule | allow + name rule |
| `wiki/_templates/*`                                     | allow  | allow |
| `wiki/meta/lint-report-*`                               | allow  | allow |
| `scripts/*`, `.vault-meta/*`, `.claude/*`               | allow  | allow |
| `CLAUDE.md`, `README.md`, `.gitignore`, `.gitattributes`| allow  | allow |
| `.raw/.manifest.json`                                   | allow  | allow |
| `.raw/*` (other)                                        | **block** | **block** (integrity) |
| Spaced `wiki/*.md` name                                 | **block** | **block** (integrity) |
| Anything else inside vault root                         | **block** | **allow + reminder** |
| Outside vault root                                      | allow (Guard B) | allow (Guard B) |
| Non-vault session                                       | allow (Guard A) | allow (Guard A) |

`.raw/` immutability and wiki filename hyphenation stay hard in both modes
(F2 resolved: wiki integrity rules are not "reminder-able" — they catch the
exact failure modes a soft reminder would let slip).

## Reminder shape (mixed mode, non-whitelist in-vault path)

stdout (single line, valid JSON, exit 0):

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","additionalContext":"Mixed-mode vault: writing `<rel>` outside the wiki whitelist (wiki/, scripts/, .vault-meta/, .claude/, root CLAUDE.md|README.md|.gitignore|.gitattributes, .raw/.manifest.json). Write ALLOWED. If this is non-wiki work (code, tests, build), proceed. If you meant a wiki page, move it under wiki/."}}
```

Rationale: names the mode, the offending path, what is whitelisted, the
explicit allow signal (so the agent does not retry), and the two paths
forward (proceed vs. relocate). Generic "outside vault" would be ignored.

## NotebookEdit bug (fix in this release)

`hooks/hooks.json` matches `Write|Edit|NotebookEdit`, but
`hooks/wiki-path-safety.sh` only reads `tool_input.file_path`. NotebookEdit
passes `notebook_path`, so it currently silent-passes every notebook write.
Fix: extractor reads `file_path` with fallback to `notebook_path`. One-line
change in the inline Python at the top of the hook.

## PostToolUse interaction (document only)

`PostToolUse` runs `git add wiki/ .raw/ .vault-meta/` after Write/Edit. In
mixed mode, `src/foo.ts` is allowed but **not** auto-committed by this hook,
because the matcher stages only wiki paths. Intentional — the hook should
not auto-commit code-shaped writes. Document in the README section so users
do not file it as a bug.

## Files to modify

- `hooks/wiki-path-safety.sh` — single hook source of truth.
  - Add config-read (jq-free, Python inline, same style as the existing
    `tool_input` parser at the top of the file). Resolve mode after Guard A
    so non-vault sessions skip config entirely.
  - Add idempotent bootstrap: if vault detected (Guard A pass) and no
    `.vault-meta/config.json`, write
    `{"version":1,"path_safety_mode":"strict"}` and continue as strict.
  - Wrap the existing exit-2 path: in mixed mode, replace the
    non-wiki-path block case with a stdout JSON emit + exit 0. Keep `.raw/`
    and hyphenation as exit 2 in both modes.
  - Extend file-path extraction to fall back to `notebook_path`.
  - Remove the temporary `docs/*` whitelist entry that was added during the
    review session to unblock plan-file writes; that entry should not ship.
- `bin/setup-vault.sh` — interactive prompt on fresh install asking
  "Does this repo also hold non-wiki work (code, docs) next to the wiki?
  [y/N]" (default N). Write the chosen mode to `.vault-meta/config.json`.
  Reuse the existing tty-detection idiom; non-interactive → strict, no
  prompt. Piggyback on the existing
  `address-counter.txt` / `legacy-pages.txt` write block; copy the
  `[ -f F ] || printf … > F` idempotency pattern.
- `tests/test_wiki_path_safety.sh` — extend the truth table:
  - Dimension: `strict` × `mixed`.
  - mixed + non-wiki-path → exit 0, stdout contains
    `"permissionDecision":"allow"` and the offending relative path.
  - mixed + `.raw/` source → still exit 2.
  - mixed + spaced wiki name → still exit 2.
  - missing config → strict + bootstrap file appears at
    `.vault-meta/config.json`.
  - malformed config → strict + stderr warning, exit code unchanged.
  - unknown `version` → strict + stderr warning.
  - NotebookEdit JSON shape (`notebook_path` only, no `file_path`) →
    exercised against both strict block and mixed reminder.
- `.claude-plugin/marketplace.json` — pin `plugins[0].source.ref` to
  `v1.10.0` as part of the release commit (per the existing release
  pattern; not part of the hook diff itself).
- `CHANGELOG.md` — new entry under v1.10.0:
  - mixed mode + `.vault-meta/config.json` (with one-line example)
  - NotebookEdit fix
  - explicit note that `KM_PATH_SAFETY` was never shipped (internal-only)
- `README.md` — short section "Path-safety mode" under the existing hook
  docs: how to switch, what the reminder looks like, why mixed exists,
  PostToolUse auto-commit clarification.

## Reusable existing code (no new abstractions)

- `lib/vault_root.py` / `lib/vault_root.sh` already resolve
  `KM_VAULT_PATH` → cwd. Use as-is. Do not introduce a parallel resolver.
- The hook's inline Python `tool_input` parser at the top of
  `hooks/wiki-path-safety.sh` is the template for config-read — same
  style, no jq dependency added.
- The truth-table runner in `tests/test_wiki_path_safety.sh` (the `run()`
  helper + `ck` assert) extends naturally to two more dimensions; no
  test-framework change.
- `bin/setup-vault.sh` already writes `.vault-meta/address-counter.txt`
  and `legacy-pages.txt`. The new `config.json` write joins that block.

## Verification

1. **Unit:** `bash tests/test_wiki_path_safety.sh` — all existing 14 cases
   plus ~10 new mode-aware cases pass.
2. **Smoke (strict):** In a clean repo with `.vault-meta/`, attempt to
   write `src/foo.ts` via the Write tool; confirm exit 2 and the stderr
   message reaches the agent's transcript.
3. **Smoke (mixed):** Flip mode via `vi .vault-meta/config.json`. Repeat
   the same write; confirm tool completes and that the next agent turn
   shows the system-reminder text from `additionalContext`. Verify by
   looking for the reminder string in the agent's next response, or by
   using `claude --print` with a trivial follow-up to confirm context
   carryover.
4. **NotebookEdit:** Construct a NotebookEdit call targeting
   `wiki/notebook.ipynb` and `src/foo.ipynb` from a vault; confirm strict
   blocks the second, mixed reminders it.
5. **Config bootstrap:** Delete `.vault-meta/config.json`; run any Write
   inside the vault; confirm the file is recreated with
   `{"version":1,"path_safety_mode":"strict"}` and the write proceeds
   under strict rules.
6. **Malformed config:** Write `not json` to `config.json`; confirm hook
   falls back to strict and emits one-line stderr warning.
7. **Release:** `bin/sync-versions.sh` + `bin/release.sh v1.10.0` flow,
   tag, `marketplace.json` ref pin, push tags.

## Out of scope (Future)

- `KM_WIKI_CONTEXT` env hint from skills to disambiguate "wiki work" from
  "code work" inside a mixed repo (unreliable today; revisit when the
  skill framework exposes a stable propagation channel).
- `updatedInput.file_path` auto-rename of spaced wiki names instead of
  blocking — changes tool semantics subtly, defer.
- `wiki_whitelist_extra: [...]` in config — extension path is now safe
  thanks to `version: 1` schema, but no use case yet.
- Telemetry log of reminder fires (`.vault-meta/path-safety.log`).
