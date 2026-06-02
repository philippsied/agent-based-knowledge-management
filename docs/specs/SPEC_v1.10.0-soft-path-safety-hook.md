# Spec: Soft-Mode for wiki-path-safety (v1.10.0)

Status: LOCKED. Supersedes prior DRAFT 2026-06-01 after review-session synthesis.
Source of truth for v1.10.0 implementation. Author: review session 2026-06-01.

## 1. Motivation

The v1.9.1 guards solved the cross-repo case: a non-vault repo (no `.vault-meta/`,
no `KM_VAULT_PATH`) now passes through untouched. One case remains unsolved: a
repo that is BOTH a vault and an active work tree at the same time, for example:

- the plugin's own development repo (`hooks/`, `tests/`, `lib/`, `bin/`, `Makefile`),
- a code project that keeps a `wiki/` folder as its knowledge vault.

In such a "mixed" repo the hook is still strict: any write outside the whitelist
returns exit 2 and hard-blocks legitimate non-wiki work. This release adds an
opt-in soft mode that injects a model-visible reminder instead of blocking for
non-wiki paths.

## 2. Goals / Non-goals

Goals:
- Opt-in soft mode; no hard block for non-wiki paths in mixed repos.
- Surface a reminder to the agent so it reconsiders, rather than silently allowing.
- Single source of configuration via `.vault-meta/config.json` with schema
  version from day one.
- Fix the NotebookEdit silent-pass bug (extractor reads `notebook_path` as
  fallback).

Non-goals:
- Loosening wiki-internal rules (filename hyphenation, `.raw/` immutability).
- Auto-detecting which skill is active (not reliably available to a hook).
- Backward compatibility framing (user controls all installs; auto-migration
  handles existing vaults).
- Runtime env override (`KM_PATH_SAFETY` was never shipped, see Section 8).

## 3. Modes

- `strict` (default, current behavior): whitelist enforced; non-wiki write inside
  a vault returns exit 2.
- `mixed`: non-wiki writes are NOT blocked; the hook emits a model-visible
  reminder via `permissionDecision: allow` + `additionalContext` and exits 0.
  Wiki-internal rules (`.raw/` immutability, hyphenation) stay hard.

No `off` mode. Deleting `.vault-meta/` already neutralizes the hook via Guard A
(non-vault sessions pass through). Adding a third mode duplicates that path
without new capability.

## 4. Resolution priority

`.vault-meta/config.json` is the only source. No env override. Live toggle is a
plain edit of the config file (read cost ~1ms per Write/Edit, negligible).

Resolution composes with the v1.9.1 guards, which run first: a non-vault
session still exits 0 before any mode logic.

## 5. Config schema

`.vault-meta/config.json`:

```json
{
  "version": 1,
  "path_safety_mode": "strict"
}
```

- `version` (int, required): schema version. Hook rejects unknown versions with
  a one-line stderr warning and falls back to `strict`.
- `path_safety_mode` (string, required): `"strict"` | `"mixed"`. Anything else
  falls back to `strict` with a stderr warning.

Schema-versioned from day one. The single line `"version": 1` removes the
migration phase the next time the file grows a field.

## 6. Setup flow (bin/setup-vault.sh)

On fresh install, ask interactively (TTY only):

> Does this repo also hold non-wiki work (code, docs) next to the wiki? [y/N]

- `y` writes `path_safety_mode: "mixed"` to `.vault-meta/config.json`.
- default `N` writes `path_safety_mode: "strict"`.

Idempotent: never overwrite an existing config (same `[ -f F ] || ...` pattern
as `address-counter.txt` and `legacy-pages.txt`). Non-interactive (CI, piped)
defaults to `strict`, no prompt.

For vaults that exist before v1.10.0, the hook bootstraps the file on the next
fire (see Section 11).

## 7. Wiki-context detection

A PreToolUse hook cannot reliably know which skill is active; `tool_input` only
carries the target path and content. So detection is path-based:

- wiki paths (`wiki/`, `.vault-meta/`, `scripts/`, `.claude/`, root files
  `CLAUDE.md` / `README.md` / `.gitignore` / `.gitattributes`,
  `.raw/.manifest.json`) are treated as wiki context, normal rules apply.
- any other in-vault path in a mixed repo is non-wiki context: reminder, not
  block.

A future skill-aware hint (e.g. `KM_WIKI_CONTEXT=1`) is documented as a future
refinement only (see Section 16).

## 8. Reminder mechanism (resolved)

PreToolUse exit 0 with stdout:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "additionalContext": "Mixed-mode vault: writing `<rel>` outside the wiki whitelist (wiki/, scripts/, .vault-meta/, .claude/, root CLAUDE.md|README.md|.gitignore|.gitattributes, .raw/.manifest.json). Write ALLOWED. If this is non-wiki work (code, tests, build), proceed. If you meant a wiki page, move it under wiki/."
  }
}
```

Verified against the official Claude Code hooks docs
(https://docs.claude.com/en/docs/claude-code/hooks): `additionalContext` is
model-visible for `PreToolUse`, inserted as a system reminder next to the tool
result. No empirical sandbox needed; the prior DRAFT's Phase 0 is dropped.

Option C (stderr + exit 0) was rejected: stderr is forwarded to the model only
on exit 2.

`KM_PATH_SAFETY` env override is NOT part of this release. Hooks are
subprocesses that inherit the environment captured at session start, so an env
override cannot toggle live mid-session; documenting it would mislead. Listed
in the CHANGELOG as internal-only / never shipped.

## 9. Mode semantics (full table)

| Path class                                                       | strict            | mixed                 |
| ---------------------------------------------------------------- | ----------------- | --------------------- |
| `wiki/*` (excl. `_templates/`, `lint-...`)                       | allow + name rule | allow + name rule     |
| `wiki/_templates/*`                                              | allow             | allow                 |
| `wiki/meta/lint-report-*`                                        | allow             | allow                 |
| `scripts/*`, `.vault-meta/*`, `.claude/*`                        | allow             | allow                 |
| `CLAUDE.md`, `README.md`, `.gitignore`, `.gitattributes`         | allow             | allow                 |
| `.raw/.manifest.json`                                            | allow             | allow                 |
| `.raw/*` (other)                                                 | **block**         | **block** (integrity) |
| Spaced `wiki/*.md` name                                          | **block**         | **block** (integrity) |
| Anything else inside vault root                                  | **block**         | **allow + reminder**  |
| Outside vault root                                               | allow (Guard B)   | allow (Guard B)       |
| Non-vault session                                                | allow (Guard A)   | allow (Guard A)       |

`.raw/` immutability and wiki filename hyphenation stay hard in both modes (F2
resolved: wiki integrity rules are not reminder-able; they catch the exact
failure modes a soft reminder would let slip).

## 10. NotebookEdit fix (shipped in this release)

`hooks/hooks.json` matches `Write|Edit|NotebookEdit`, but
`hooks/wiki-path-safety.sh` reads only `tool_input.file_path`. NotebookEdit
passes `notebook_path`, so today every notebook write silent-passes. Fix:
extractor falls back to `notebook_path`. One-line change in the inline Python
at the top of the hook.

## 11. Migration (no manual step required)

Vaults without `.vault-meta/config.json` get the file written on the next hook
fire with `{"version":1,"path_safety_mode":"strict"}`, then continue under
strict rules. The hook has no "missing config" long-tail branch.

Fresh installs via `bin/setup-vault.sh` get the interactive prompt (Section 6).

## 12. PostToolUse interaction (documented, no code change)

`PostToolUse` runs `git add wiki/ .raw/ .vault-meta/` after Write/Edit. In
mixed mode, `src/foo.ts` is allowed but NOT auto-committed by this hook,
because the matcher stages only wiki paths. Intentional: the hook should not
auto-commit code-shaped writes. Documented in the README so users do not file
it as a bug.

## 13. Tests (deterministic, extend tests/test_wiki_path_safety.sh)

Mode-dimension truth table:
`(strict | mixed) x (wiki | non-wiki | .raw source | spaced wiki name | docs/)`
with the expected exit code and (for mixed) the expected stdout JSON shape.

Plus:
- Bootstrap: missing config + Write inside vault writes
  `{"version":1,"path_safety_mode":"strict"}` and continues as strict.
- Malformed JSON: stderr warning, fall back to strict, exit code unchanged.
- Unknown `version`: stderr warning, fall back to strict.
- Unknown `path_safety_mode` value: stderr warning, fall back to strict.
- NotebookEdit JSON shape (`notebook_path` only, no `file_path`) exercised
  against both strict block and mixed reminder.

## 14. Implementation phases

1. Hook: extend file-path extractor with `notebook_path` fallback (NotebookEdit
   fix).
2. Hook: add config-read + idempotent bootstrap.
3. Hook: mixed-mode branch (reminder instead of exit 2 for non-wiki paths;
   `.raw/` and hyphenation stay hard).
4. Hook: remove the temporary `docs/*` whitelist entry that was added during
   the review session.
5. `setup-vault.sh`: interactive prompt + `.vault-meta/config.json` write
   (idempotent, TTY-gated).
6. Extend test suite (mode x path truth table + bootstrap + config parsing +
   NotebookEdit).
7. Docs: CHANGELOG + README section on path-safety mode and PostToolUse
   auto-commit clarification.
8. Release: `bin/sync-versions.sh`, `bin/release.sh v1.10.0`, pin
   `marketplace.json.plugins[0].source.ref` to `v1.10.0`.

## 15. Resolved questions (from prior DRAFT)

- F1 (Reminder mechanism A vs B vs C): RESOLVED. Option B, verified per
  official docs.
- F2 (Mixed mode hardness for `.raw/` and hyphenation): RESOLVED. Both stay
  hard in both modes; wiki integrity rules catch failure modes a soft reminder
  would let slip.
- F3 (Config location/format): RESOLVED. `.vault-meta/config.json`, key
  `path_safety_mode`, with `version: 1` schema field.
- F4 (Need for `off` mode): RESOLVED. Dropped. Delete `.vault-meta/` to
  neutralize the hook via Guard A.

## 16. Out of scope (future)

- `KM_WIKI_CONTEXT` env hint from skills to disambiguate "wiki work" from
  "code work" inside a mixed repo. Unreliable today; revisit when the skill
  framework exposes a stable propagation channel.
- `updatedInput.file_path` auto-rename of spaced wiki names instead of
  blocking; changes tool semantics subtly, defer.
- `wiki_whitelist_extra: [...]` in config; the `version: 1` schema makes this
  extension safe, but no use case yet.
- Telemetry log of reminder fires (`.vault-meta/path-safety.log`).
- Runtime env override (`KM_PATH_SAFETY`); see Section 8.
