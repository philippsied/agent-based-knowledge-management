# PLAN — Full `.sh` → `.py` Migration (decision-locked)

> **Status:** DECISION-LOCKED planning artifact. A later execution session/Workflow follows this verbatim.
> **Scope:** Delete *every* tracked `.sh` in the repo, port all real-logic shells to Python, fold the
> six `lint-*.py` subprocess checks into imported modules (MEDIUM consolidation), and port the three
> `.sh` test suites to Python. **End state:** `git ls-files '*.sh'` returns **nothing**.
> **This file is the ONLY artifact this planning pass writes.** No `.sh`/`.py`/doc/git mutation occurs here.

## Locked goals (do not re-litigate)

1. **Delete all `.sh`**, including the three thin shims (`scripts/allocate-address.sh`,
   `scripts/run-lint.sh`, `lib/vault_root.sh`). Their callers repoint to the `.py` directly.
2. **Port** all real-logic `.sh` to `.py`; drop the external `jq` dependency in favour of python `json`.
3. **Consolidation = MEDIUM:** fold the six `lint-*.py` that `run-lint.py` runs as `sys.executable`
   subprocesses into **imported modules** (single process). JSON + Markdown report stay **byte-identical**;
   `tests/test_run_lint.py` (183 checks) stays green. **No** Heavy/unified-CLI.
4. **Port** `.sh` test suites to `.py`; delete the `.sh` tests.

---

## 1. Inventory — every tracked `.sh`

`git ls-files '*.sh'` → **15 files**. "Twin exists?" = does a `.py` with the logic already exist.

| # | `.sh` file | Role (1 line) | Target `.py` | Logic source | Test file |
|---|-----------|---------------|--------------|--------------|-----------|
| 1 | `scripts/allocate-address.sh` | Thin shim → `allocate-address.py` (DragonScale Mech 2 allocator) | `scripts/allocate-address.py` (**exists**) | TWIN exists — delete shim only | `tests/test_allocate_address.py` (repoint) |
| 2 | `scripts/run-lint.sh` | Thin shim → `run-lint.py` (lint aggregator) | `scripts/run-lint.py` (**exists**) | TWIN exists — delete shim only | `tests/test_run_lint.py` (stays) |
| 3 | `lib/vault_root.sh` | Thin shim → `vault_root.py` (vault-root resolver, sourced by shells) | `lib/vault_root.py` (**exists**) | TWIN exists — delete shim after shell callers migrate | `tests/test_vault_root.py` (**exists, 13 fns**) |
| 4 | `bin/setup-vault.sh` | Interactive vault scaffolder (TTY prompt, curl downloads, snippet enable) | `bin/setup-vault.py` (**new**) | PORT | none today → add `tests/test_setup_vault.py` (smoke) |
| 5 | `bin/setup-dragonscale.sh` | Idempotent DragonScale installer (`.vault-meta/`, chmod, ollama probe) | `bin/setup-dragonscale.py` (**new**) | PORT | none → smoke only |
| 6 | `bin/setup-multi-agent.sh` | Symlinks `skills/` into Codex/OpenCode/Gemini/Cursor/Windsurf | `bin/setup-multi-agent.py` (**new**) | PORT | none → smoke only |
| 7 | `bin/sync-versions.sh` | Mirror `plugin.json` version → `marketplace.json` (drop `jq`) | `bin/sync-versions.py` (**new**) | PORT | `tests/test_sync_versions.sh` → port to `.py` |
| 8 | `bin/release.sh` | Release pipeline: test+lint gate, version bump, CHANGELOG check, tag, optional PDF | `bin/release.py` (**new**) | PORT | none → smoke (arg-validation) |
| 9 | `hooks/wiki-path-safety.sh` | PreToolUse hook — vault path-safety + hyphen-naming (exit 0 allow / 2 block) | `hooks/wiki-path-safety.py` (**new**) | PORT — **security-critical** | `tests/test_wiki_path_safety.sh` (43) → port to `.py` |
| 10 | `skills/doc-pipeline/scripts/convert-doc.sh` | Stage-1 doc→MD (markit/textutil/pandoc dispatch, mktemp, image-strip) | `skills/doc-pipeline/scripts/convert-doc.py` (**new**) | PORT | none → smoke (arg/exit) |
| 11 | `skills/doc-pipeline/scripts/finalize-md.sh` | Stage-4 approval-gated finalize (`status: approved` grep gate) | `skills/doc-pipeline/scripts/finalize-md.py` (**new**) | PORT | none → smoke (arg/exit) |
| 12 | `evals/run.sh` | Eval-suite runner; already embeds `python3 - <<PY` + calls `score-summary.py` | `evals/run.py` (**new**) | PORT (mostly orchestration) | none → smoke |
| 13 | `tests/test_sync_versions.sh` | Test for #7 (1 PASS line, exit-on-fail) | `tests/test_sync_versions.py` (**new**) | PORT then delete | — |
| 14 | `tests/test_vault_root.sh` | Test for #3 (8 shell cases) | **none — RETIRE** (`test_vault_root.py` already covers it) | DELETE only | — |
| 15 | `tests/test_wiki_path_safety.sh` | Test for #9 (43 cases, security-critical parity) | `tests/test_wiki_path_safety.py` (**new**) | PORT then delete | — |

**Twins that already exist** (`git ls-files '*.py'`): `lib/vault_root.py`, `scripts/allocate-address.py`,
`scripts/run-lint.py`, all six `scripts/lint-*.py`, `tests/test_vault_root.py`, `evals/score-summary.py`.
Items 1–3 are therefore **delete-shim** operations (no porting); items 4–12 require porting; 14 is **pure retire**.

---

## 2. EXHAUSTIVE caller + doc reference map

Evidence: `git grep -n -F '<basename>'` across the whole repo (run live during planning).
Buckets: **(a) executable callers**, **(b) living docs that instruct invocation**, **(c) HISTORICAL — leave as-is, do not edit**.
Each repoint lists the **new `.py` invocation form**. Total `.sh` reference surface = **289 hits / 58 files**
(`git grep -nE '\.sh([^a-zA-Z]|$)'`).

> **Global historical-doc allowlist (NEVER edit — bucket (c) everywhere):**
> `CHANGELOG.md`, `docs/releases/*`, `docs/upstream-roadmap.md`, `docs/upstream-merge-log.md`,
> `docs/eval-results-trend.md`, `docs/influence-log.md`, `ATTRIBUTION.md`,
> `docs/plans/PHASE2-run-lint-pytest-spec.md`, `docs/plans/PLAN_v1.10.0-soft-path-safety-hook.md`,
> `docs/specs/SPEC_v1.10.0-soft-path-safety-hook.md`, `docs/plans/PLAN-visualize-integration.md`,
> `docs/specs/SPEC-visualize-wiki-integration.md`. These narrate past releases/decisions and must read
> exactly as written. The `.py` docstrings that name the `.sh` they ported (e.g. `run-lint.py:2`,
> `lint-rename.py:12`, `test_run_lint.py` comments) are also historical-by-design — leave them.

### 2.1 `allocate-address.sh` → `python3 scripts/allocate-address.py`
**(a) executable callers**
- `bin/setup-dragonscale.sh:24` — `for required in "scripts/allocate-address.sh" …` → change to `.py`
- `bin/setup-dragonscale.sh:30` — `chmod +x scripts/allocate-address.sh …` → `chmod +x scripts/allocate-address.py …` (or drop chmod; see §3.5)
- `bin/setup-dragonscale.sh:102` — `NEXT=$(./scripts/allocate-address.sh --peek …)` → `python3 scripts/allocate-address.py --peek`
- `scripts/run-lint.sh:17` — comment in the shim (file deleted)

**(b) living docs**
- `agents/wiki-ingest.md:42,44,56` — feature-detection `[ -x ./scripts/allocate-address.sh ]` + single-writer rule → repoint to `.py`; **feature-detect must switch to checking `scripts/allocate-address.py`** (see §3.1)
- `agents/wiki-lint.md:37,45` — `[ -x ./scripts/allocate-address.sh ] && [ -f ./.vault-meta/address-counter.txt ]` → check `.py`
- `docs/dragonscale-guide.md:22,55,117,125,176,282,286,290,298,303,305,309,315,547` — many invocation + detection mentions → repoint to `.py`. **Note:** lines that are *historical changelog-style* blocks inside this guide (e.g. release notes) stay; the operational "how to run" lines (176/282/286/290/298) repoint. Reviewer must read each in context.
- `skills/wiki-ingest/SKILL.md:311,316,339,344,352,353,354,358` — required-tool section + detection + `ADDR=$(./scripts/allocate-address.sh)` → `.py`; **detection guard `[ -x ./scripts/allocate-address.sh ]` → `.py`**
- `skills/wiki-lint/SKILL.md:193,227,252,261` — detection + `--peek`/`--rebuild` references → `.py`

**(c) HISTORICAL — do not edit**
- `CHANGELOG.md:9,23,147`; `docs/plans/PHASE2-run-lint-pytest-spec.md:15`; `docs/releases/v1.6.0.md:64`;
  `docs/upstream-roadmap.md:349`.

### 2.2 `run-lint.sh` → `python3 scripts/run-lint.py`
**(a) executable callers**
- `.github/workflows/test.yml:39` — `bash scripts/run-lint.sh --json > /tmp/lint.json` → `python3 scripts/run-lint.py --json …`; **the surrounding `jq` parse lines (40-46) drop** (see §3.2 / §6 CI)
- `Makefile:30` — `@bash scripts/run-lint.sh` → `@python3 scripts/run-lint.py`
- `bin/release.sh:32` — `bash scripts/run-lint.sh --json | jq -e '.error_count == 0'` → in `release.py`, call `run-lint.py --json` and parse with python `json` (no `jq`)
- `scripts/run-lint.py:*` (×11) — these are **docstring/comment self-references** naming the ported `.sh` → historical-by-design, **leave**
- `tests/test_run_lint.py:900,909,941` — divergence comments → **leave** (historical)

**(b) living docs**
- `_templates/research-queue.md:75` — "`scripts/run-lint.sh` runs `lint-deps.py`…" → repoint to `.py`
- `skills/wiki-lint/SKILL.md:26,29` — `scripts/run-lint.sh` / `… --json` invocation block → `.py`

**(c) HISTORICAL — do not edit**
- `CHANGELOG.md:9,81,85,90,92`; entire `docs/plans/PHASE2-run-lint-pytest-spec.md` (×17);
  `docs/upstream-roadmap.md` (×14, all roadmap/forecast prose).

### 2.3 `vault_root.sh` → `lib/vault_root.py` (import directly; deleted LAST)
**(a) executable callers**
- `Makefile:35` — `@echo "=== test_vault_root.sh ==="` → drop line (test retired)
- `Makefile:36` — `@bash tests/test_vault_root.sh` → drop (retired; `test_vault_root.py` runs at line 33-34 already)
- `hooks/wiki-path-safety.sh:16` — comment "matches lib/vault_root.sh" (hook itself is ported; comment goes with it)
- `scripts/allocate-address.sh:14` — comment (shim deleted)
- `skills/doc-pipeline/scripts/convert-doc.sh:29-30` — `. ".../lib/vault_root.sh"` **source** → in `convert-doc.py`, `import` `lib/vault_root.py` / call its resolver
- `skills/doc-pipeline/scripts/finalize-md.sh:19-20` — same source → import in `finalize-md.py`
- `tests/test_vault_root.sh:2,3,7,8` — file retired
- `lib/vault_root.py:79` — docstring self-reference → **leave** (historical)
- `scripts/lint-deps.py:13`, `lint-programs.py:21`, `lint-rename.py:6`, `rewrite-wikilinks.py:13`, `wiki-prepass.py:21` — **docstring** "Vault root resolution (matches lib/vault_root.sh)" comments. Optional: update text to "(matches lib/vault_root.py)" for accuracy, but **not load-bearing**; safe to leave. Reviewer choice — does **not** block the gate (comment, not invocation).

**(b) living docs**
- `skills/doc-pipeline/SKILL.md:41` — "resolved via the plugin-wide `lib/vault_root.sh`" → `lib/vault_root.py`

**(c) HISTORICAL — do not edit**
- `CHANGELOG.md:74,76`; `docs/plans/PHASE2-…:50,51`; `docs/plans/PLAN_v1.10.0-…:178`;
  `docs/upstream-roadmap.md:187,218`.

### 2.4 `setup-vault.sh` → `python3 bin/setup-vault.py`
**(b) living docs**
- `.gitignore:8,11` — comments "downloaded by setup-vault.sh" → update to `.py` (comment only; non-blocking but in scope)
- `.gitignore:122` — "Each install scaffolds its own vault via bin/setup-vault.sh." → `.py`
- `README.md:68` — `bash bin/setup-vault.sh` → `python3 bin/setup-vault.py`
- `README.md:75,213,283,297` — narrative mentions of `setup-vault.sh` → `.py`
- `docs/dragonscale-guide.md:37` — `bash bin/setup-vault.sh` → `.py`
- `docs/install-guide.md:37,150,217` — `bash bin/setup-vault.sh` (×2 commands + 1 narrative) → `.py`
- `references/operational-rules/README.md:3` — narrative → `.py`

**(c) HISTORICAL — do not edit**
- `ATTRIBUTION.md:39`; `CHANGELOG.md:42,65,66`; `docs/influence-log.md:24,26,28`;
  `docs/plans/PLAN_v1.10.0-…:146,186`; `docs/specs/SPEC_v1.10.0-…:76,167,201`.

### 2.5 `setup-dragonscale.sh` → `python3 bin/setup-dragonscale.py`
**(a) executable callers**
- `Makefile:21` — help-text echo → `.py`
- `Makefile:82` — `@bash bin/setup-dragonscale.sh` → `@python3 bin/setup-dragonscale.py`

**(b) living docs**
- `docs/dragonscale-guide.md:13,44,48,105,110,507,564` — `bash bin/setup-dragonscale.sh [path]` (incl. positional-arg form) → `python3 bin/setup-dragonscale.py [path]`
- `docs/install-guide.md:6` — narrative → `.py`

**(c) HISTORICAL — do not edit**
- `CHANGELOG.md:150,157`; `docs/releases/v1.6.0.md:8,170,324`; `docs/upstream-roadmap.md:339`.

### 2.6 `setup-multi-agent.sh` → `python3 bin/setup-multi-agent.py`
**(b) living docs**
- `.cursor/rules/claude-obsidian.mdc:61` — `bash bin/setup-multi-agent.sh` → `.py`
- `.windsurf/rules/claude-obsidian.md:30` — narrative + command → `.py`
- `AGENTS.md:22` — `bash bin/setup-multi-agent.sh` → `.py`
- `GEMINI.md:16` — `bash bin/setup-multi-agent.sh` → `.py`

**(c) HISTORICAL — do not edit**
- `docs/plans/PLAN-visualize-integration.md:52,154`; `docs/specs/SPEC-visualize-wiki-integration.md:135,281,318`;
  `docs/upstream-roadmap.md:85`. (Q9 in PLAN-visualize confirmed this installer has **no** hard-coded skill count — nothing to update there.)

### 2.7 `release.sh` → `python3 bin/release.py`
**(a) executable callers**
- `Makefile:79` — `@bash bin/release.sh $(VERSION)` → `@python3 bin/release.py $(VERSION)`
- `scripts/run-lint.sh:6` — comment in shim (deleted)

**(c) HISTORICAL — do not edit**
- `CHANGELOG.md:9`; `docs/plans/PLAN_v1.10.0-…:211`; `docs/specs/SPEC_v1.10.0-…:207`.

### 2.8 `sync-versions.sh` → `python3 bin/sync-versions.py`
**(a) executable callers**
- `.github/workflows/version-drift.yml:7` — `paths: - 'bin/sync-versions.sh'` → `'bin/sync-versions.py'` (**trigger path**)
- `.github/workflows/version-drift.yml:20` — `if [ ! -x bin/sync-versions.sh ]` → feature-detect `bin/sync-versions.py` (or drop the guard; Track D is merged)
- `.github/workflows/version-drift.yml:21,28` — echo messages naming the script → `.py`
- `.github/workflows/version-drift.yml:25` — `bash bin/sync-versions.sh` → `python3 bin/sync-versions.py`
- `Makefile:20` — help echo → `.py`
- `Makefile:75` — `@bash bin/sync-versions.sh` → `@python3 bin/sync-versions.py`
- `bin/release.sh:11` — comment (file deleted)
- `bin/release.sh:40` — `bash bin/sync-versions.sh` → call from `release.py` as `python3 bin/sync-versions.py` (or import)
- `tests/test_sync_versions.sh:3,13,14,21` — file ported then deleted

**(c) HISTORICAL — do not edit**
- `docs/plans/PLAN_v1.10.0-…:211`; `docs/specs/SPEC_v1.10.0-…:207`.

### 2.9 `wiki-path-safety.sh` → `python3 hooks/wiki-path-safety.py`
**(a) executable callers**
- `hooks/hooks.json:35` — `"command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/wiki-path-safety.sh"` →
  `"command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/wiki-path-safety.py"` (**the one distribution-critical hook edit; see §3.9, §6**)
- `scripts/lint-rename.py:12` — docstring naming the hook → **leave** (historical)
- `tests/test_wiki_path_safety.sh:2,17` — file ported then deleted

**(b) living docs**
- `README.md:194` — "`hooks/wiki-path-safety.sh` is a PreToolUse hook…" → `.py`
- `hooks/README.md:11,40` — table row + "The script at `hooks/wiki-path-safety.sh`…" → `.py`

**(c) HISTORICAL — do not edit**
- `CHANGELOG.md:33,47,58`; `docs/plans/PLAN_v1.10.0-…:118,133,181`; `docs/specs/SPEC_v1.10.0-…:156`;
  `docs/upstream-roadmap.md:79,209,253,360`.

### 2.10 `convert-doc.sh` → `python3 …/convert-doc.py`
**(b) living docs**
- `commands/doc-pipeline.md:10` — `"$CLAUDE_PLUGIN_ROOT/skills/doc-pipeline/scripts/convert-doc.sh" "<source>"` → `.py`
- `skills/doc-pipeline/SKILL.md:13,34,63,65,201` — pipeline diagram + Stage-1 invocation (incl. `--out-dir`) → `.py`

**(a) executable callers**
- `skills/doc-pipeline/scripts/convert-doc.sh:135` — internal echo mentioning `finalize-md.sh` (file ported)

**(c) HISTORICAL — do not edit**
- `CHANGELOG.md:115`.

### 2.11 `finalize-md.sh` → `python3 …/finalize-md.py`
**(a) executable callers**
- `skills/doc-pipeline/scripts/convert-doc.sh:135` — echo "run finalize-md.sh" → becomes `finalize-md.py` inside `convert-doc.py`

**(b) living docs**
- `commands/doc-pipeline.md:18` — `"$CLAUDE_PLUGIN_ROOT/…/finalize-md.sh" <staging-file>` → `.py`
- `skills/doc-pipeline/SKILL.md:21,35,168` — diagram + Stage-4 invocation → `.py`

**(c) HISTORICAL — do not edit**
- `CHANGELOG.md:115`.

### 2.12 `run.sh` (evals) → `python3 evals/run.py` (or `./evals/run.py`)
**(b) living docs**
- `evals/README.md:17,60,70,71,72` — entry-point description + `./evals/run.sh [skill] [case]` invocation forms (incl. positional args) → `./evals/run.py`

**(c) HISTORICAL — do not edit**
- `docs/eval-results-trend.md:3,7,10`; `docs/upstream-merge-log.md:14`.

### 2.13–2.15 Test-suite `.sh`
- `test_sync_versions.sh` — `Makefile:67,68` (`@echo`, `@bash tests/test_sync_versions.sh`) → `@python3 tests/test_sync_versions.py`.
- `test_vault_root.sh` — `Makefile:35,36` → **delete both lines** (covered by `test_vault_root.py` at Makefile:33-34). `CHANGELOG.md:76` historical (leave).
- `test_wiki_path_safety.sh` — `Makefile:71,72` → `@python3 tests/test_wiki_path_safety.py`. `CHANGELOG.md:43` + `docs/plans/PLAN_v1.10.0-…:153,183,191` + `docs/specs/SPEC_v1.10.0-…:177` historical (leave).

---

## 3. Per-file migration recipe

> **Universal port conventions** (apply to every ported `.py`):
> - `set -euo pipefail` → idiomatic Python: exceptions propagate (= `-e`); explicit `os.environ`/`.get`
>   with checks (= `-u`); for `pipefail`, capture subprocess return codes explicitly.
> - **Preserve exact exit codes** (they are part of the contract — hooks and `make`/CI branch on them).
> - **Preserve stdout byte-for-byte** where it is consumed (allocator output, lint JSON, hook JSON).
> - TTY-interactive `read` → `input()` guarded by `sys.stdin.isatty()`.
> - Keep each file directly runnable: `#!/usr/bin/env python3` + `if __name__ == "__main__": sys.exit(main())`.
> - Match existing twin style (see `scripts/allocate-address.py`, `lib/vault_root.py`).

### 3.1 `scripts/allocate-address.sh` (DELETE shim)
- **No port** — `allocate-address.py` already carries the logic (the shim mirrors the wrapper pattern).
- **Delete** the shim. Repoint callers/docs per §2.1.
- **Feature-detect callers** (`[ -x ./scripts/allocate-address.sh ]` in `wiki-ingest`/`wiki-lint` SKILL + agent files):
  switch the test to `[ -f ./scripts/allocate-address.py ]` (the `.py` need not carry the executable bit if
  invoked as `python3 …`; prefer existence over exec-bit to avoid chmod coupling). Invocation `$(./scripts/allocate-address.sh)`
  → `$(python3 scripts/allocate-address.py)`; `--peek`/`--rebuild` flags unchanged.

### 3.2 `scripts/run-lint.sh` (DELETE shim)
- **No port** — `run-lint.py` is canonical.
- **Delete** the shim. Repoint `Makefile:30`, `test.yml:39`, `bin/release.sh:32` (→ `release.py`), SKILL/template docs.
- **CI JSON-parse change:** in `test.yml`, the lint job currently does `bash run-lint.sh --json > /tmp/lint.json`
  then `jq -r '.totals.error'`. Replace with `python3 scripts/run-lint.py --json …` and read the error count
  with python (or keep `jq` only on the JSON *output* — but the migration goal drops `jq`, so prefer
  python). Either keep the gate logic in the YAML or move it behind `make lint` + a `--check`/exit-code path.

### 3.3 `lib/vault_root.sh` (DELETE shim — LAST)
- **No port** — `vault_root.py` is canonical.
- Delete **only after** its three shell *sourcers* are gone: `hooks/wiki-path-safety.sh`,
  `convert-doc.sh`, `finalize-md.sh` (all become `.py` that `import` the resolver). Also after `Makefile:35-36`
  and `tests/test_vault_root.sh` are removed.
- **Import contract for the new `.py` callers:** `lib/vault_root.py` already exposes a resolver
  (`KM_VAULT_PATH` env → argv → cwd, with `~` expansion). New ported scripts import it
  (e.g. `sys.path.insert` to repo root, then `from lib.vault_root import resolve_vault_root`) rather than
  shelling out. Execution session must confirm the exact public function name in `lib/vault_root.py` and
  reuse it (single source of truth).

### 3.4 `bin/setup-vault.sh` → `bin/setup-vault.py`
- **TTY prompt (lines 47-49):** `if [ -t 0 ]; then printf '…[y/N] '; read -r ANSWER` →
  `if sys.stdin.isatty(): answer = input('Does this repo also hold non-wiki work … [y/N] ')`. Preserve the
  default-No semantics and the resulting `.vault-meta/config.json` write (strict vs mixed mode).
- **Downloads:** `curl -sS -L … -o …` for Excalidraw `main.js` (8 MB) + Thino `main.js`/`styles.css`
  → `urllib.request` (stdlib) or `subprocess` to `curl` (keep curl to avoid behaviour drift on redirects;
  `curl` is already assumed present). Preserve the `[ -f manifest.json ] && [ ! -f main.js ]` guards.
- **`mkdir -p` scaffolding (16-20)** → `pathlib.Path(...).mkdir(parents=True, exist_ok=True)`.
- **Trailing `echo` guidance block** → `print(...)`; keep the literal text (users follow it).
- **Exit codes:** `set -euo pipefail` → let exceptions raise; preserve any explicit non-zero exits.
- Delete `.sh`. Repoint README/install-guide/dragonscale-guide/.gitignore comments per §2.4.

### 3.5 `bin/setup-dragonscale.sh` → `bin/setup-dragonscale.py`
- **Required-file loop (24)** and **`chmod +x` (30):** the loop checks `scripts/allocate-address.sh` +
  `scripts/tiling-check.py` → check `scripts/allocate-address.py` + `scripts/tiling-check.py`. `chmod +x`
  can target the `.py` files (`os.chmod`) **or** be dropped if everything is invoked via `python3` — decide
  in execution; if any doc still says "make executable", keep a `chmod`.
- **`--peek` call (102):** `NEXT=$(./scripts/allocate-address.sh --peek …)` →
  `subprocess.run(["python3","scripts/allocate-address.py","--peek"], …)`.
- **Ollama probe (108-111):** `command -v curl` + `curl --max-time 2 localhost:11434/...` → `shutil.which("curl")`
  + `subprocess`/`urllib` with timeout; preserve the "not installed"/"reachable" report lines.
- **Positional vault arg** (`setup-dragonscale.sh /path/to/vault`) — preserve as `argv[1]`.
- Delete `.sh`. Repoint `Makefile:21,82` + dragonscale-guide/install-guide.

### 3.6 `bin/setup-multi-agent.sh` → `bin/setup-multi-agent.py`
- **Symlink helper (34-56):** `ln -s "$target" "$dest"` with the three guards (exists-correct / exists-wrong /
  not-a-symlink) → `os.symlink` wrapped in the same three checks (`Path.is_symlink()`, `os.readlink`,
  `Path.exists()`). Preserve the colored `[$agent_name] …` messages (or drop ANSI — cosmetic; keep text).
- Targets: `~/.codex`, `~/.opencode`, `~/.gemini`, `.cursor`, `.windsurf` skill dirs — preserve all five.
- **No hard-coded skill count** (verified). Delete `.sh`. Repoint AGENTS/GEMINI/.cursor/.windsurf docs.

### 3.7 `bin/sync-versions.sh` → `bin/sync-versions.py` (**drop `jq`**)
- `VERSION=$(jq -r '.version' plugin.json)` → `json.load(open(PLUGIN_JSON))["version"]`; preserve the
  null/empty guard → `exit 2`.
- `jq --arg v "$VERSION" '…' marketplace.json` (the mirror write) → load `marketplace.json` with `json`,
  set the nested version fields (`metadata.version` + `plugins[0].version` — confirmed by the test), write
  back. **Critical:** match `jq`'s output formatting so `version-drift.yml`'s `diff -q` stays stable —
  `json.dump(..., indent=2)` + trailing newline; the execution session must byte-compare the first run's
  output against the committed `marketplace.json` and adjust separators/newline to avoid a spurious drift fail.
- Delete `.sh`. Port `tests/test_sync_versions.sh` → `.py`. Repoint `version-drift.yml` (trigger path + body),
  `Makefile`, `release.py`.

### 3.8 `bin/release.sh` → `bin/release.py`
- **Arg validation (19-20):** require `X.Y.Z` regex → `re.fullmatch(r'\d+\.\d+\.\d+', version)`; preserve
  `exit 2`.
- **Clean-tree gate (26):** `git diff --quiet` → `subprocess.run(["git","diff","--quiet"]).returncode` →
  `exit 3` on dirty.
- **Lint gate (32):** `run-lint.sh --json | jq -e '.error_count == 0'` → call `run-lint.py --json`, parse with
  `json`, `exit 4` if errors. (Drops `jq`.)
- **CHANGELOG gate (35):** `grep -q "^## \[$VERSION\]" CHANGELOG.md` → python read + check; `exit 5`.
- **Version bump (38):** `jq '.version=$v' plugin.json` → `json` round-trip.
- **sync-versions (40):** call `python3 bin/sync-versions.py` (or import its `main`).
- **Optional pandoc PDF (43-44):** `command -v pandoc` → `shutil.which`; keep non-fatal-on-failure.
- Preserve the numbered exit-code contract (2/3/4/5). Delete `.sh`. Repoint `Makefile:79`.

### 3.9 `hooks/wiki-path-safety.sh` → `hooks/wiki-path-safety.py` (**SECURITY-CRITICAL**)
- **Contract:** reads `tool_input.file_path` from the hook JSON on stdin; **exit 0 = allow, exit 2 = block**;
  mixed-mode allow-with-reminder = exit 0 **plus** a stdout JSON reminder. Preserve all three outcomes exactly.
- **Vault-root + config bootstrap (16, 54-55):** resolve root via the **imported** `lib/vault_root.py`;
  idempotent silent bootstrap of `.vault-meta/config.json` to strict on first fire.
- **The `case "$ABS" in … esac` path-whitelist ladders (79-190):** port each glob branch to Python with
  identical matching semantics. **Hazard:** shell `case` globs (`"$VAULT_ROOT"/wiki/_templates/*`) are not
  Python `fnmatch` 1:1 for `/` — use prefix/`Path` checks that reproduce the shell behaviour; characterization
  test (§3.15) is the oracle.
- **Hyphen-naming rule (181-190):** `printf '%s' "$BASENAME" | grep -q ' '` (block on space in basename) →
  `' ' in basename`. Preserve exit 2.
- **`hooks.json:35` command swap** is the cutover point — do it **only after** 43/43 parity is green (§6/§7).
- **Latency:** this runs on **every** Write/Edit/NotebookEdit. Python startup (~30-60 ms cold) is added to the
  hot path vs bash. Mandate a quick latency sanity check (single invocation under, say, 150 ms) and keep the
  script import-light (no heavy imports at module top; stdlib only).

### 3.10 `skills/doc-pipeline/scripts/convert-doc.sh` → `convert-doc.py`
- **Required positional `SRC` (34)** with `${1:?usage:…}` → argparse positional + usage string; `exit 2` on bad arg.
- **Flag parse (40-44):** `--out-dir`, `--no-ref`, `--keep-images` → argparse; preserve `exit 2` on unknown.
- **Dependency checks:** `command -v markit` (49), `textutil`/`libreoffice` (75-82) → `shutil.which`; preserve
  the exact error strings + exit codes (`exit 1`).
- **Temp dir + trap (65-66):** `mktemp -d` + `trap 'rm -rf' EXIT` → `tempfile.mkdtemp()` + `try/finally`
  (or `tempfile.TemporaryDirectory()`).
- **Format dispatch (71-99):** `.doc`→textutil→docx→markit; pandoc reference (110-125) gated on
  `command -v pandoc`. Preserve.
- **Image-strip perl (106):** `perl -i -pe 's{!\[..\](..)}{<!-- REVIEW… -->}'` → equivalent `re.sub` over the
  output file. **Non-ASCII strings** in output (`→`, `ℹ`, German "Bild im Original entfernt") — keep UTF-8 exact.
- **vault_root source (29-30)** → `import` resolver from `lib/vault_root.py`.
- Delete `.sh`. Repoint SKILL.md + `commands/doc-pipeline.md`.

### 3.11 `skills/doc-pipeline/scripts/finalize-md.sh` → `finalize-md.py`
- **Positional `SRC` (23)** `${1:?usage:…}` → argparse; flags `--out-dir`, `--force` (28-31); `exit 2` unknown.
- **Approval gate (39-42):** `grep -Eq '^\s*status:\s*approved' "$SRC"` else `exit 3` → python regex; preserve
  `exit 3` (this is the safety gate).
- **Remaining-review count (64):** `grep -c -E '<!--\s*(PIPELINE-)?REVIEW'` → python count.
- **vault_root source (19-20)** → import resolver.
- Delete `.sh`. Repoint SKILL.md + `commands/doc-pipeline.md`. Note the cross-reference in `convert-doc.py`'s
  guidance echo (formerly `convert-doc.sh:135`) now says `finalize-md.py`.

### 3.12 `evals/run.sh` → `evals/run.py`
- Already Python-heavy: line 49 `python3 scripts/lint-terminology.py … --json`, line 51 inline
  `python3 - "$expected" "$actual" "$case_dir" <<'PY' … PY` (a full comparison block), line 124
  `python3 evals/score-summary.py`. The inline heredoc **lifts directly** into a function in `run.py`.
- **Orchestration (110-116):** `while IFS= read -r case_dir; do case "$skill" in …` iterating case folders →
  `pathlib` glob + dispatch dict. Preserve the per-skill routing (`lint`/`ingest`/`query`).
- **Args:** `./evals/run.sh [skill] [case-glob]` → argparse positional(s). Preserve all three doc'd forms.
- `score-summary.py` stays as-is (already a twin); `run.py` calls it (or imports it).
- Delete `.sh`. Repoint `evals/README.md`.

### 3.13 `tests/test_sync_versions.sh` → `tests/test_sync_versions.py`
- Shell test copies `bin/sync-versions.sh` into a temp repo, runs it, asserts `metadata.version` and
  `plugins[0].version` both equal the injected version (`99.99.99`). Port to Python: build temp fixture,
  invoke `bin/sync-versions.py`, assert both fields with `json`. Preserve the exact assertion targets.
- Delete `.sh`. Repoint `Makefile:67,68` → `@python3 tests/test_sync_versions.py`.

### 3.14 `tests/test_vault_root.sh` → **RETIRE (delete only)**
- `tests/test_vault_root.py` already exists with **13 test functions** covering env→argv→cwd precedence,
  `~` expansion, empty-arg, and the python-helper-missing path — superset of the 8 shell cases.
- **Action:** delete `tests/test_vault_root.sh`; **delete** `Makefile:35-36` (the `.sh` echo + invocation).
  No port. Confirm `test_vault_root.py` runs in `make test-vault-root` (Makefile:33-34) — it does.

### 3.15 `tests/test_wiki_path_safety.sh` → `tests/test_wiki_path_safety.py` (**43 cases, security parity**)
- The shell suite is a truth-table runner: `run <cwd> <file_path> [KM_VAULT_PATH]` → echoes the hook's exit
  code; `ck <label> <want-exit> <got>` asserts; plus `contains`-style checks for the mixed-mode reminder JSON.
  Sections cover strict×mixed mode, NotebookEdit input extraction, missing/malformed/unknown-version config
  (C1-C4 → exit 0/2/2/2), wiki/concepts/docs allow paths (M1-M6 → exit 0), and block paths (exit 2).
- **Port:** drive `hooks/wiki-path-safety.py` as a subprocess (feed hook JSON on stdin, set `cwd`/env),
  assert `returncode` and (for mixed-mode) the stdout reminder. **Reproduce all 43 cases 1:1** — this is the
  parity oracle for §3.9. Counting must show **43/43** before the `hooks.json` cutover.
- Delete `.sh`. Repoint `Makefile:71,72` → `@python3 tests/test_wiki_path_safety.py`.

---

## 4. Dependency-ordered phases

> **Progress (resume marker):** P0–P6 ✅ **DONE** — full `.sh`→`.py` migration complete; `git ls-files '*.sh'` empty. Landed on `main` via merge `0b92a96` (feature commit `11d5d12`; earlier P0 `2c8ed48`, P1 `666b196`). Gates green: `make test`, 183 run-lint checks, hook 47/47 parity, marketplace byte-stable, no `jq` in shipped code/CI, stale-ref scan clean. P3 carry-over resolved: `release.py` reads `.totals.error` and dropped `jq`. Security fix in P6: hook symlink fail-open (resolved-root vs unresolved candidate) closed by canonicalizing the candidate path; regression-tested S1–S4.

Topologically ordered so nothing breaks mid-flight. Each phase = one coherent commit (conventional format).
**`lib/vault_root.sh` is deleted LAST** (Phase 6), only after its three shell sourcers are Python.
**The `run-lint.sh` shim** is deleted in Phase 3 once CI/Makefile/release/wiki-lint are repointed.

| Phase | Title | Files touched | Depends on | Parallel-safe with |
|-------|-------|---------------|-----------|--------------------|
| **P0** | **Lint consolidation** (MEDIUM) — fold 6 `lint-*.py` into imports inside `run-lint.py`; keep each `__main__`-runnable | `scripts/run-lint.py`, `scripts/lint-*.py` (add importable entrypoints), `tests/test_run_lint.py` (only if helper imports shift) | — | **P1** (disjoint files) |
| **P1** | **Leaf shims: allocate-address + run-lint** delete; repoint callers/docs | del `scripts/allocate-address.sh`, `scripts/run-lint.sh`; edit `Makefile`, `.github/workflows/test.yml`, `bin/release.sh`†, SKILL/agent/template docs (§2.1, §2.2) | P0 (so `run-lint.py` is final form before CI repoints) | P2 partially |
| **P2** | **Installers** port: `setup-vault`, `setup-dragonscale`, `setup-multi-agent` | new `bin/setup-*.py`; del 3 `.sh`; edit README, install-guide, dragonscale-guide, AGENTS/GEMINI/.cursor/.windsurf/.gitignore (§2.4-2.6) | P1 (dragonscale references allocate-address.py) | P4 (doc-pipeline) once P1 done |
| **P3** | **Versioning chain:** `sync-versions` then `release` (release calls sync-versions + run-lint) | new `bin/sync-versions.py`, `bin/release.py`; del 2 `.sh`; port `tests/test_sync_versions.sh`→`.py`; edit `version-drift.yml`, `Makefile` (§2.7, 2.8, 3.13) | P1 (release's lint gate → run-lint.py) | — (sequential within: sync-versions BEFORE release) |
| **P4** | **doc-pipeline** port: `convert-doc`, `finalize-md` (both source `vault_root`) | new 2 `.py`; del 2 `.sh`; edit SKILL.md, `commands/doc-pipeline.md` (§2.10, 2.11) | needs `vault_root.py` import contract (already exists) | P2, P5 |
| **P5** | **evals** port: `run.sh`→`run.py` | new `evals/run.py`; del `.sh`; edit `evals/README.md` (§2.12) | — | P2, P3, P4 |
| **P6** | **Hook + vault_root finale** (SECURITY GATE): port `wiki-path-safety.sh`, port `test_wiki_path_safety.sh` (43), retire `test_vault_root.sh`, then **delete `lib/vault_root.sh`** | new `hooks/wiki-path-safety.py`, `tests/test_wiki_path_safety.py`; del `hooks/wiki-path-safety.sh`, `tests/test_wiki_path_safety.sh`, `tests/test_vault_root.sh`, **`lib/vault_root.sh`**; edit `hooks/hooks.json`, `hooks/README.md`, README, `Makefile` (§2.3, 2.9, 3.14, 3.15) | **P4 must be done** (convert-doc/finalize-md no longer source `vault_root.sh`); P2 (no installer sources it — confirmed none do) | LAST — run alone |

**`lib/vault_root.sh` deletion preconditions (all in P6 or earlier):** its only sourcers are
`hooks/wiki-path-safety.sh` (P6), `convert-doc.sh` (P4), `finalize-md.sh` (P4); plus `tests/test_vault_root.sh`
(P6) and `Makefile:35-36` (P6). Once those are Python/removed, the shim has zero callers → delete.

**Parallelization recommendation**
- **Concurrent batch A:** P0 ∥ P1 are disjoint (lint internals vs leaf-shim deletes) — but P1's CI repoint
  should land *after* P0 finalizes `run-lint.py`; if run by one agent, do P0 then P1.
- **Concurrent batch B:** after P1, **P2 ∥ P3 ∥ P4 ∥ P5** touch disjoint file sets (installers / versioning /
  doc-pipeline / evals) and can run in parallel worktrees.
- **Sequential tail:** **P6 alone, last** (security gate + the vault_root finale depend on P4).
- Sequential-only constraint **inside** P3: `sync-versions.py` before `release.py`.

---

## 5. Lint-consolidation sub-plan (MEDIUM)

**Current state (evidence).** `scripts/run-lint.py` lines **267-395** define six wrapper functions that each
shell out via `sys.executable` through a shared `_run_capture(args, vault_root)` helper:

| Wrapper (run-lint.py) | Subprocess today | Gate | Returns |
|---|---|---|---|
| `run_orphans` (285) | `python3 lint-orphans.py` | none | raw stdout (paths) |
| `run_terminology` (294) | `python3 lint-terminology.py --json` | `[ -x ]` exec-bit | `(err, warn)` from JSON severities |
| `run_title_overlap` (321) | `python3 lint-title-overlap.py` | `[ -x ]` exec-bit | `(count, raw_stdout)`; count = lines starting with digit |
| `run_dag` (336) | `python3 lint-deps.py --vault … --json` | `[ -f research-queue.md ]` + script exists | dict of 5 counts |
| `run_programs` (369) | `python3 lint-programs.py --vault … --json` | `[ -f research-queue.md ]` + `[ -f Research-Program-Codes.md ]` + script exists | dict of 3 counts |
| *(lint-rename.py)* | **not called by run-lint.py** | — | standalone only (hook-rename tool) |

**Each `lint-*.py` already separates data from presentation** (evidence — pure functions):
- `lint-orphans.py`: `find_orphans(wiki_root) -> list[str]` (37); `main(argv)` (98) + `__main__` (122).
- `lint-deps.py`: `parse_queue` (61), `find_cycles` (97); `main()` (138) + `__main__` (243).
- `lint-programs.py`: `parse_queue_programs` (58), `parse_seed_codes` (76), `split_program_cell` (93);
  `main()` (108) + `__main__` (212).
- `lint-terminology.py`: `iter_pages`, `check_page`, `check_termbase_orphans`, `format_markdown`;
  `main(argv)` (224) + `__main__` (256). `--json` emits `[asdict(f) …]`.
- `lint-title-overlap.py`: `collect_pages` (54), `find_overlaps(pages, threshold)` (65);
  `main(argv)` (76) + `__main__` (102).
- `lint-rename.py`: `main()` (34) + `__main__` (118) — leave as-is (not aggregated).

**Target module API.** Add to each aggregated `lint-*.py` a thin **importable entrypoint** that returns the
*same structured data the subprocess JSON/stdout currently yields*, computed by the existing pure functions —
**without** going through argparse/`print`. Suggested signatures (execution session finalizes exact names):

```python
# lint-orphans.py
def collect(vault_root: Path) -> list[str]: ...          # == find_orphans(wiki_root)
# lint-terminology.py
def collect_findings(vault_root: Path) -> list[dict]: ... # == the --json list (asdict findings)
# lint-title-overlap.py
def collect_lines(vault_root: Path) -> list[str]: ...     # == the plain stdout lines run_title_overlap parses
# lint-deps.py
def collect(vault_root: Path) -> dict: ...                # == the --json dict run_dag reads
# lint-programs.py
def collect(vault_root: Path) -> dict: ...                # == the --json dict run_programs reads
```

`run-lint.py` then replaces each `_run_capture([sys.executable, …])` body with a direct call to the imported
`collect*` and applies the **same post-processing it already does** (severity counting, digit-line counting,
`len(...)` of list keys). Net effect: identical inputs → identical derived numbers, **zero** subprocess
startup.

**Preserve byte-identical output.**
- The wrappers currently *derive* counts from subprocess output, then the summary-assembly (run-lint.py 398+)
  and report renderer (496+) build the JSON + Markdown. **Do not touch** assembly/rendering — only swap the
  *data source* feeding the wrappers. The 183-check `tests/test_run_lint.py` asserts the assembled output,
  so it is the byte-identity oracle.
- **Gating must be reproduced in-process:** the `[ -x ]` exec-bit gates (`run_terminology`,
  `run_title_overlap`) and the `[ -f ]` existence gates (`run_dag`, `run_programs`) currently short-circuit
  to zero. Keep equivalent guards before calling `collect*` so a vault missing `research-queue.md` (etc.)
  still yields the all-zero defaults. **Subtlety:** once these are imports not subprocesses, the exec-bit
  check is semantically odd (you don't need `+x` to import). **Decision:** keep the existing gate *predicate*
  (file presence / configured-feature) to preserve behaviour, but the `[ -x ]`-specific gates may be replaced
  by an existence check **only if** `test_run_lint.py` stays green — if any test encodes the exec-bit gate,
  preserve it via `os.access(..., X_OK)`. The test suite decides.
- **Error isolation:** subprocesses swallowed failures (`return (0,0)` / zero dict on parse error). Imports
  raise in-process — wrap each `collect*` call in the same defensive try/except that defaults to zero, so a
  malformed vault cannot crash the aggregate (parity with `|| true`).

**Standalone runnability (MANDATORY).** Each `lint-*.py` stays invokable as `__main__` — Makefile test targets
run them directly (`make test-terminology` → `test_lint_terminology.py`; `make test-title-overlap`;
`make test-lint-orphans`), and `evals/run.sh:49` calls `python3 scripts/lint-terminology.py … --json`.
So: **keep `main()` + `if __name__ == "__main__"` intact**; add `collect*` alongside, do not replace.
`main()` should call `collect*` internally then format — single code path, no duplicated logic.

**Test strategy.**
1. Before P0: capture golden `run-lint.py --json` + report on a representative vault.
2. Refactor wrappers to imports.
3. `python3 tests/test_run_lint.py` must report **183** passing.
4. Byte-diff new `--json`/report vs the golden (normalizing only `date`/abs-path fields, per the PHASE2 spec
   convention) → must be empty.
5. Confirm each aggregated `lint-*.py` still runs standalone (`--json` and human modes) and its own
   `test_lint_*.py` passes.

---

## 6. Risk register

| # | Risk | Severity | Mitigation (mandated) |
|---|------|----------|-----------------------|
| R1 | **Hook enforcement regression** — `wiki-path-safety.py` mis-ports a `case` glob → a blocked path becomes allowed (or vice-versa). Security-critical. | **HIGH** | Port `test_wiki_path_safety.sh` first; require **43/43** parity before swapping `hooks.json:35`. Use the shell suite's exact truth table as oracle. |
| R2 | **Hook hot-path latency** — runs on every Write/Edit/NotebookEdit; Python cold-start adds ~30-60 ms vs bash. | MED | Keep the script stdlib-only, no heavy top-level imports; sanity-check a single invocation stays well under ~150 ms; document the trade-off. |
| R3 | **Installer doc churn** — under the delete-`.sh` policy every `bash bin/setup-*.sh` in user-facing docs changes to `python3 bin/setup-*.py`. ~20 living-doc edits across README/install-guide/dragonscale-guide/AGENTS/GEMINI/.cursor/.windsurf. | **HIGH (churn)** | Treat doc repointing as first-class deliverable per phase; the §2 map enumerates every file:line. Verify with the §7 stale-ref scan. |
| R4 | **Installer TTY/UX drift** — `[ -t 0 ]`+`read` → `input()`; mis-handling non-TTY (CI/pipe) could hang or change default-No behaviour. | MED | Guard with `sys.stdin.isatty()`; preserve default-No; smoke-test piped + interactive. |
| R5 | **CI breakage** — `test.yml` & `version-drift.yml` install `jq` and parse with it; `version-drift.yml` triggers on `bin/sync-versions.sh` path and `[ -x ]`-gates it. | **HIGH** | Repoint trigger `paths`, swap `bash`→`python3`, replace `jq` parsing with python; the `jq` apt-install steps become removable. Re-run both workflows on the PR. |
| R6 | **`sync-versions` output formatting drift** — python `json.dump` not byte-matching `jq` output → `version-drift.yml`'s `diff -q` spuriously fails forever. | MED | First run must byte-compare against committed `marketplace.json`; tune `indent`/separators/trailing newline until `diff` is clean; the ported `.py` test asserts the two version fields. |
| R7 | **Lint consolidation output drift** — folding subprocesses into imports changes a byte of JSON/report. | MED | §5 golden-diff + 183-check gate; only the data source changes, not assembly/rendering; preserve gating + error-swallowing semantics. |
| R8 | **Plugin distribution** — does renaming break installs? | LOW | `.claude-plugin/plugin.json` has **no `files`/include allowlist**; `.gitignore` excludes only vault *content* (`wiki/`, `.raw/`), **not** `bin/`/`hooks/`/`scripts/`/`lib/`. So those ship as tracked and renaming is internal. The **only** distribution-critical edit is `hooks/hooks.json:35` (hook command) — must point to `.py` and Python must be present at install. |
| R9 | **Marketplace / version-drift workflow** — see R5/R6; also `bin/release.py` must keep the bump→sync→tag order. | MED | P3 keeps `sync-versions` before `release`; release's CHANGELOG + clean-tree + lint gates (exit 3/4/5) preserved. |
| R10 | **Feature-detection callers** flip silently — `[ -x ./scripts/allocate-address.sh ]` in SKILL/agent files. If left pointing at the deleted `.sh`, DragonScale silently *disables* (detection returns false). | MED | §3.1: switch guards to `[ -f scripts/allocate-address.py ]` (existence, not exec-bit). Verify wiki-ingest/wiki-lint enable correctly post-rename. |

---

## 7. Per-phase verification gate

Run at the end of **each** phase (and the final gate after P6):

1. **`make test` is green** (all `.py` suites + the not-yet-migrated `.sh` suites until their phase retires them).
2. **`python3 tests/test_run_lint.py` reports `183`** passing (after P0; every phase thereafter).
3. **Hook parity = 43/43** — `python3 tests/test_wiki_path_safety.py` (P6) reports 43 passed, 0 failed,
   **before** `hooks.json` is cut over.
4. **STALE-REFERENCE SCAN:** `git grep -nE '\.sh([^a-zA-Z]|$)'` returns **only** allowlisted matches.
   - **Allowlist (intentional/historical — see §2 global allowlist):** `CHANGELOG.md`, `docs/releases/*`,
     `docs/upstream-roadmap.md`, `docs/upstream-merge-log.md`, `docs/eval-results-trend.md`,
     `docs/influence-log.md`, `ATTRIBUTION.md`, `docs/plans/PHASE2-run-lint-pytest-spec.md`,
     `docs/plans/PLAN_v1.10.0-soft-path-safety-hook.md`, `docs/specs/SPEC_v1.10.0-soft-path-safety-hook.md`,
     `docs/plans/PLAN-visualize-integration.md`, `docs/specs/SPEC-visualize-wiki-integration.md`,
     **this file** (`docs/plans/PLAN-sh-to-py-full-migration.md`), and `.py` docstring/comment self-references
     that name a ported `.sh` (`scripts/run-lint.py`, `scripts/lint-rename.py`, `lib/vault_root.py`,
     `tests/test_run_lint.py`, and the five `lint-*.py`/`rewrite-wikilinks.py`/`wiki-prepass.py` "matches
     lib/vault_root.sh" docstrings — optionally updated, but allowlisted either way).
   - **Baseline today:** 289 hits / 58 files. After migration, every hit outside the allowlist must be gone.
     A convenient check: `git grep -nE '\.sh([^a-zA-Z]|$)' | grep -vE '<allowlist-regex>'` → empty.
5. **No `jq` invocation remains in shipped code/CI** — `git grep -n 'jq ' -- bin .github Makefile scripts` →
   empty (docstrings/historical excluded).
6. **FINAL GATE (after P6):** `git ls-files '*.sh'` → **empty**. `make test` green. Both GitHub workflows pass.

---

## 8. Execution-model recommendation

**Scope:** 15 `.sh` files (9 ported, 3 shim-deletes, 1 pure-retire, 2 test ports) + 1 in-place lint
consolidation + **~120-150 caller/doc reference edits** across ~40 files (the rest of the 289 hits are
historical/allowlisted and untouched).

**Recommendation: run as a multi-phase Workflow, ~6 phases (P0–P6)**, not a single session:
- The work has clean topological seams (§4) and a **disjoint parallel batch** (P2 ∥ P3 ∥ P4 ∥ P5) that a
  Workflow can fan out across worktrees, collapsing wall-clock time.
- Two phases are **gated and must be serial**: **P0** (consolidation, byte-identity gate) and **P6** (hook
  security parity 43/43 + the vault_root finale). These belong in their own phases with explicit human review
  before the `hooks.json` cutover.
- Each phase is one conventional commit with its own §7 gate, so a failure is isolated and revertible.
- **Suggested Workflow shape:** P0 → P1 → [P2,P3,P4,P5 parallel] → P6, with a human gate before P6's
  `hooks.json` swap and before the final `git ls-files '*.sh'` empty-check.
- If run as sequential sessions instead: same 6 phases in the same order, ~1 session per phase (P2/P5 are
  small; P6 is the heaviest due to the 43-case parity port).

**Per R4 (context budget):** keep each phase's evidence in its own session; this plan file + the §2 reference
map are the authoritative artifacts the execution agents read — they should not re-grep the whole repo,
only the file:line targets enumerated here.
