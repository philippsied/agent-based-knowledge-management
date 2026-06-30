# Phase 2 — Characterization Test Spec: `run-lint.sh` → `run-lint.py`

**Status:** SPEC ONLY. No migration, no implementation. This document defines the
characterization tests that a *future* `scripts/run-lint.py` must pass to prove
behavioral parity with the current `scripts/run-lint.sh`.

**Target test file (future):** `tests/test_run_lint.py`
**Run convention (from Makefile):** `python3 tests/test_run_lint.py` (NOT pytest —
the `Makefile` `test-*` targets invoke `python3 tests/test_X.py` / `bash tests/test_X.sh`
directly; the test must self-run via a `__main__` block and `sys.exit(1)` on failure).
**Test style to mirror:** `tests/test_tiling_check.py` — plain-python, `Fail(SystemExit)`
+ `assert_eq` / `assert_true` helpers, `importlib.util` for white-box unit tests,
`subprocess.run` for black-box CLI tests, `__main__` runner, "All tests passed." on success.

**Sibling migration convention to mirror:** `allocate-address.sh → allocate-address.py`
(in progress, `.py` not yet landed as of this spec). Conventions to carry over:
- Resolve vault root via `lib/vault_root.py` (`resolve_vault_root`), not a reimplemented resolver.
- Numeric, documented exit codes preserved exactly from the `.sh`.
- Tests run in a throwaway temp vault, never touching the real vault.
- Mirror `$TMPDIR`-aware `mktemp` usage (see commit `3ad2162`: "use $TMPDIR-aware mktemp").
  For Python, the equivalent is `tempfile.mkdtemp()` (honors `TMPDIR`).

---

## Part A — Behavioral characterization of `scripts/run-lint.sh`

This is the ground truth the port must reproduce. Source: `scripts/run-lint.sh` (415 lines),
its invoked sub-scripts, and `lib/vault_root.{sh,py}`.

### A.1 CLI surface (flags + positional)

Parsed in a `for arg in "$@"` loop (order-independent, all args scanned):

| Token | Effect | Notes |
|---|---|---|
| `--json` | `JSON_ONLY=1` | JSON to stdout, **no** report file, **no** summary line |
| `--no-report` | `JSON_ONLY=1` | exact alias for `--json` |
| `--quiet` | `QUIET=1` | write report file, suppress stdout summary |
| `--help` / `-h` | print header, `exit 0` | prints `sed -n '1,30p' "$0"` with leading `# ` stripped, to **stderr** |
| `<path>` (first non-flag) | sets `POSITIONAL` (vault root candidate) | passed to resolver |
| `<path>` (second non-flag) | `exit 2` "extra positional argument" | only one positional allowed |
| any other `-*` | `exit 2` "unknown flag" | leading-dash tokens not matched above |

Flag combination semantics:
- `--json` + `--quiet`: `JSON_ONLY` wins (JSON branch returns/`exit 0` before the report/quiet block).
- `--json` is checked first in the output section; `--quiet` only affects the non-JSON path.

### A.2 Vault-root resolution

- Sources `lib/vault_root.sh`, calls `km_resolve_vault_root "$POSITIONAL"`.
- `lib/vault_root.sh` is a thin wrapper that delegates to `lib/vault_root.py` (single source
  of truth) and re-exports `KM_VAULT_PATH`.
- Resolution order: **`KM_VAULT_PATH` env → positional arg → cwd**.
- `WIKI_ROOT="$VAULT_ROOT/wiki"`. If `! -d "$WIKI_ROOT"` → stderr message + `exit 2`.
- **Port note:** `run-lint.py` MUST call `resolve_vault_root()` from `lib/vault_root.py`
  (same import shim the other `.py` linters use:
  `sys.path.insert(0, .../lib); from vault_root import resolve_vault_root`). It must NOT
  reimplement env/argv/cwd precedence. `KM_VAULT_PATH` env must still win over the positional.

### A.3 The nine checks (names, order, severity, severity source)

Emitted in this exact order in the `checks` array:

| # | `name` | `severity` | Severity source | Count source |
|---|---|---|---|---|
| 1 | `spaced_filenames` | `error` (hardcoded) | hardcoded in run-lint.sh | `find … -name '* *.md'` excluding `_templates`, line count |
| 2 | `spaced_wikilinks_body` | `error` (hardcoded) | hardcoded | inline `python3` walk; `[[target]]` with space in target (alias/anchor stripped), excluding dirs `_templates` and `meta` |
| 3 | `orphans` | `warn` (hardcoded) | hardcoded | `lint-orphans.py` stdout line count (`|| true`) |
| 4 | `dead_link_targets` | `warn` (hardcoded) | hardcoded | `grep`+`sed`+`comm` pipeline (see A.5) |
| 5 | `frontmatter_gaps` | `warn` (hardcoded) | hardcoded | inline `python3`; head 30 lines, must start `---` and contain `type/title/created/updated/status:` |
| 6 | `terminology` | `error` if `TERM_ERR>0` else `warn` (DYNAMIC) | **pass-through** from `lint-terminology.py --json` | `TERM_ERR + TERM_WARN`; also emits `errors`, `warns` sub-keys |
| 7 | `title_overlap` | `info` (hardcoded) | hardcoded | `lint-title-overlap.py` stdout, `awk '/^[0-9]/{n++}'` |
| 8 | `research_queue_dag` | `error` if `DAG_ERRORS>0` else `info` (DYNAMIC) | hardcoded flip on derived count | `lint-deps.py --json`; only when `wiki/meta/research-queue.md` AND `lint-deps.py` exist |
| 9 | `research_program_codes` | `error` if `PROG_ERRORS>0` else `info` (DYNAMIC) | hardcoded flip on derived count | `lint-programs.py --json`; only when queue + `decisions/Research-Program-Codes.md` + script exist |

Severity-source distinction the port MUST preserve:
- Checks 1–5, 7: severity is a **constant literal** regardless of count.
- Check 6 (`terminology`): severity is **derived from the sub-script's own per-finding
  `severity` field** (`ERROR`/`WARN` uppercased in `lint-terminology.py`, counted into
  `TERM_ERR`/`TERM_WARN`). This is the only true pass-through.
- Checks 8, 9: severity **flips** `info→error` purely on whether the locally-derived error
  count (`DAG_ERRORS = duplicates+missing+cycles`; `PROG_ERRORS = unknown+missing_pages`) is
  `> 0`. The sub-script exit code is ignored (`|| true` / both branches `:`); JSON is still parsed.

### A.4 Exact JSON schema (`summary.json`, printed by `--json`, embedded in report)

Top-level object (printed via `json.dumps(summary, indent=2, ensure_ascii=False)`):

```
{
  "date":          <str>   # YYYY-MM-DD from `date +%Y-%m-%d`
  "vault_root":    <str>   # resolved absolute path
  "wiki_root":     <str>   # <vault_root>/wiki
  "pages_scanned": <int>   # count of *.md under wiki (find … -name '*.md' | wc -l)
  "checks":        <list>  # 9 objects, order per A.3
  "totals":        {"error": <int>, "warn": <int>, "info": <int>}
}
```

Per-check object shapes (note: **heterogeneous** — keys differ per check):

- **Common keys (all 9):** `name` (str), `severity` (str: one of `error`/`warn`/`info`),
  `count` (int), `items` (list[str]).
- `spaced_filenames`, `spaced_wikilinks_body`, `orphans`, `dead_link_targets`,
  `frontmatter_gaps`, `title_overlap`: `items` populated from `head_lines(...)` (≤30 lines,
  trailing `\n` stripped). Others have `items: []`.
- `terminology` additionally: `errors` (int), `warns` (int). `items: []`.
- `research_queue_dag` additionally: `duplicates`, `missing_targets`, `cycles`, `ready_set`,
  `task_count` (all int). `items: []`.
- `research_program_codes` additionally: `unknown_codes`, `missing_home_pages`,
  `triage_tasks` (all int). `items: []`.

`totals` accumulation rules (the port MUST replicate exactly):
- Skip any check with `count <= 0` (contributes nothing).
- `terminology`: adds `errors` → `totals.error` and `warns` → `totals.warn`
  (NOT by its own top-level `severity`).
- `research_queue_dag` / `research_program_codes`: add `count` to `totals[severity]`
  where `severity` was already flipped (so when count>0 it lands in `error`).
- All other checks: add `count` to `totals[severity]`.

Value-type contract for the port: every `count`/sub-count is a JSON **integer** (the `.sh`
forces this via `int(os.environ[...])`); never a string. `items` entries are strings.

### A.5 `dead_link_targets` pipeline (the most port-fragile check)

Built from set algebra over four temp files:
1. `links.txt`: `grep -rEho '\[\[[^]]+\]\]'` over wiki (wrapped `|| true`) → `sed` strip
   alias/anchor → `sed` strip trailing `.md` → `tr A-Z a-z` → `sort -u`.
2. `basenames.txt`: `awk -F/ '{f=$NF; sub(/\.md$/,"",f); print tolower(f)}'` over all paths → `sort -u`.
3. `paths.txt`: wiki-relative slash paths, `.md` stripped, lowercased, `sort -u`.
4. `raw.txt` (**CORRECTED ground truth for `run-lint.py`** — see the divergence box below):
   if `$VAULT_ROOT/.raw` exists, each `*.md/*.json/*.txt/*.pdf` file contributes exactly **one**
   valid target = its **basename with the FINAL extension stripped**, ASCII-lowercased; else empty.
   Examples: `.raw/foo.pdf` → `foo`; `.raw/sub/deep/Bar.PDF` → `bar` (extension match is
   case-insensitive); `.raw/a.b.pdf` → `a.b` (only the final ext is stripped); `.raw/my source.txt`
   → `my source`. A `.raw` file whose extension is **not** in the glob (e.g. `.raw/foo.png`)
   contributes nothing → `[[foo]]` stays dead (documented known limitation, not a bug).
5. `valid.txt = sort -u basenames paths raw`.
6. `dead.txt = comm -23 links.txt valid.txt` → `wc -l`.

This means: a wikilink target is "dead" iff its lowercased, alias/anchor-stripped, `.md`-stripped
form is NOT in {any page basename} ∪ {any wiki-relative path} ∪ {any `.raw` **basename stem**}.
Case-insensitive. The port must reproduce the link extraction, the basename/path unions, and the
corrected `.raw` basename-stem union (final-extension-only strip, case-insensitive glob match).

> **DIVERGENCE — `run-lint.py` fixes the `.raw` union forward; `run-lint.sh` keeps the legacy bug.**
> The legacy shell raw pipeline is
> `find "$VAULT_ROOT/.raw" … \( -name '*.md' … -o -name '*.pdf' \) | sed 's|\.md$||' | tr A-Z a-z`.
> `find` emits **full paths** and `sed` strips only a trailing `.md`, so a `.raw/foo.pdf` source
> enters the valid set as the **full lowercased path with its `.pdf` suffix** — which a bare
> `[[foo]]` can never match. Under the legacy `.sh`, every bare wikilink to a non-`.md` raw source is
> therefore **falsely flagged DEAD**. `run-lint.py` is fixed forward to the basename-stem semantics
> above; `run-lint.sh` retains the bug until the shim swap (do not touch `.sh`). Consequently
> `run-lint.py` **intentionally diverges** from `run-lint.sh` for this one case, and any future
> parity golden-diff (E3) **must exclude the `.raw`-union scenario** (or normalize it away).
> Basename-only is deliberate: two raw files sharing a stem in different dirs collapse to one target
> (and could mask a genuine typo) — accepted trade-off; subdir disambiguation is out of scope.

### A.6 Report-file behavior

- Only when NOT `--json`. Path: `$WIKI_ROOT/meta/lint-report-$DATE.md` (`DATE` = `%Y-%m-%d`).
- `mkdir -p` the `meta` dir first.
- Content blocks, in order:
  1. YAML frontmatter: `type: meta`, `title: "Lint Report <DATE>"`, `created`/`updated` = DATE,
     `tags: [meta, lint]`, `status: developing`.
  2. `# Lint Report: <DATE>`
  3. `## Summary` + Markdown table `| Check | Severity | Count |` (one row per check, in order)
     + a `**Totals:** error=… warn=… info=… (pages scanned: …)` line.
  4. `## Findings` — for each check with `count>0`: an `### <name> (severity=…, count=…)` heading,
     up to 30 `- <item>` lines, then `- … N more` when `count > len(items)`.
  5. `## Machine-readable summary` + a fenced ```json block containing the verbatim `summary.json`.
- After writing, if NOT `--quiet`: print `Lint report: <path>` then a `Totals: error=… warn=… info=… pages=…` line to stdout.

### A.7 Exit codes

| Code | Condition |
|---|---|
| `0` | normal completion (any findings) — **read-only; exit code never reflects findings** |
| `0` | `--help`/`-h` |
| `2` | unknown flag |
| `2` | extra (2nd) positional argument |
| `2` | resolver/usage error OR `wiki/` not a directory |

`set -euo pipefail` is active; `grep`/sub-script non-zero exits are individually neutralized
with `|| true` or `: ` so a "no matches" never aborts the run.

---

## Part B — Test cases for `tests/test_run_lint.py`

Format per case: **{name, setup, action, expected}**. Cases B1–B23 reproduce the 23 existing
assertions in `tests/test_run_lint.sh` (grouped by the bash file's three sections). Cases
B24+ are **NEW** coverage closing the gaps flagged in Part C. All black-box cases invoke the
*future* `scripts/run-lint.py` (the harness under test) via `subprocess.run`; white-box cases
use `importlib` against `run-lint.py`'s functions (assuming the port exposes them — see C.10).

**Shared fixture `mk_vault(root)`** — port of the bash `mk_vault`. Creates:
`wiki/{concepts,entities,meta,_templates}`; canonical roots `index.md` (body
`[[Linked-Concept]] [[Dead-Target]]`), `log.md`, `hot.md`, `overview.md` (all well-formed
frontmatter); `concepts/Linked-Concept.md` (linked, not orphan);
`concepts/Orphan-Page.md` (well-formed, body `[[Spaced Target]]`); `concepts/Spaced Filename.md`
(well-formed); `entities/No-Frontmatter.md` (body only); `_templates/has spaces.md` (well-formed).
Use `tempfile.mkdtemp()` so `TMPDIR` is honored (sibling convention).

### Section 1 — JSON mode on seeded vault (maps bash lines 111–165)

These run once against a `mk_vault` temp dir with `KM_VAULT_PATH` set and `--json`.

1. **`json_output_nonempty`** — *setup:* seeded vault. *action:* run `run-lint.py --json` with
   `KM_VAULT_PATH=<vault>`, capture stdout. *expected:* stdout is non-empty and parses as JSON.
2. **`json_key_date`** — *setup:* parsed JSON from #1. *action:* check top-level. *expected:* key `date` present.
3. **`json_key_vault_root`** — *expected:* key `vault_root` present.
4. **`json_key_wiki_root`** — *expected:* key `wiki_root` present.
5. **`json_key_pages_scanned`** — *expected:* key `pages_scanned` present.
6. **`json_key_checks`** — *expected:* key `checks` present.
7. **`json_key_totals`** — *expected:* key `totals` present.
8. **`check_present_spaced_filenames`** — *action:* scan `checks[].name`. *expected:* `spaced_filenames` present.
9. **`check_present_spaced_wikilinks_body`** — *expected:* `spaced_wikilinks_body` present.
10. **`check_present_orphans`** — *expected:* `orphans` present.
11. **`check_present_dead_link_targets`** — *expected:* `dead_link_targets` present.
12. **`check_present_frontmatter_gaps`** — *expected:* `frontmatter_gaps` present.
13. **`check_present_terminology`** — *expected:* `terminology` present.
14. **`check_present_title_overlap`** — *expected:* `title_overlap` present.
15. **`seeded_spaced_filenames_ge_1`** — *setup:* seeded (`concepts/Spaced Filename.md`).
    *action:* read that check's `count`. *expected:* `count >= 1`.
16. **`seeded_spaced_wikilinks_body_ge_1`** — *setup:* `Orphan-Page.md` has `[[Spaced Target]]`.
    *expected:* `spaced_wikilinks_body.count >= 1`.
17. **`seeded_orphans_ge_1`** — *setup:* `Orphan-Page.md` has no inbound links.
    *expected:* `orphans.count >= 1`.
18. **`totals_error_ge_2`** — *setup:* one spaced filename + one spaced body link (both `error`).
    *expected:* `totals.error >= 2`.
19. **`totals_warn_ge_1`** — *setup:* orphan present (`warn`). *expected:* `totals.warn >= 1`.

### Section 2 — Report-file mode (maps bash lines 167–186)

Run `run-lint.py --quiet` with `KM_VAULT_PATH=<vault>` (same seeded vault).

20. **`report_file_written`** — *action:* run `--quiet`; compute `DATE` via
    `datetime.date.today().isoformat()`. *expected:* `<vault>/wiki/meta/lint-report-<DATE>.md` exists.
21. **`report_has_title_header`** — *action:* read the report. *expected:* contains `Lint Report: <DATE>`.
22. **`report_mentions_spaced_filenames`** — *expected:* report text contains `spaced_filenames`.

### Section 3 — Resolver / missing-wiki (maps bash lines 188–201)

23. **`exit_2_when_wiki_missing`** — *setup:* fresh empty tempdir, **no** `wiki/`, `KM_VAULT_PATH`
    unset. *action:* run `run-lint.py --json` with `cwd=<empty>`. *expected:* return code `2`.

> Cases 1–23 above are the **parity baseline**. A faithful port passes all 23 unchanged
> (modulo `bash run-lint.sh` → `python3 run-lint.py`). They are necessary but NOT sufficient —
> the existing bash suite is shallow (only `>=` assertions, no exact schema, no severity-source
> coverage). Cases 24+ close those gaps.

### Section 4 — NEW: exact-schema & value-type parity (gap C.1)

24. **`check_order_exact`** — *setup:* seeded vault. *action:* list `[c["name"] for c in checks]`.
    *expected:* exactly `["spaced_filenames","spaced_wikilinks_body","orphans","dead_link_targets","frontmatter_gaps","terminology","title_overlap","research_queue_dag","research_program_codes"]`
    (note: **9** checks — bash suite never asserts the last two or the order).
25. **`all_nine_checks_present`** — *expected:* `len(checks) == 9` and includes `research_queue_dag`,
    `research_program_codes` (bash suite omits both).
26. **`top_level_value_types`** — *expected:* `date`/`vault_root`/`wiki_root` are `str`,
    `pages_scanned` is `int`, `checks` is `list`, `totals` is `dict`.
27. **`counts_are_integers`** — *action:* for every check, `type(count) is int`; same for every
    numeric sub-key (`errors`,`warns`,`duplicates`,`missing_targets`,`cycles`,`ready_set`,
    `task_count`,`unknown_codes`,`missing_home_pages`,`triage_tasks`). *expected:* all `int`,
    never `str` (guards against a port that forgets the `int(...)` coercion).
28. **`items_are_strings`** — *expected:* every entry of every `items` list is `str`.
29. **`totals_keys_exact`** — *expected:* `set(totals.keys()) == {"error","warn","info"}`.
30. **`terminology_subkeys_present`** — *expected:* `terminology` check has `errors` and `warns` int keys.
31. **`dag_subkeys_present`** — *expected:* `research_queue_dag` has
    `duplicates,missing_targets,cycles,ready_set,task_count` int keys.
32. **`program_subkeys_present`** — *expected:* `research_program_codes` has
    `unknown_codes,missing_home_pages,triage_tasks` int keys.
33. **`vault_root_resolved_absolute`** — *expected:* `vault_root` equals the resolved absolute
    path of the seeded vault (`Path(vault).resolve()`); `wiki_root == vault_root + "/wiki"`.
34. **`pages_scanned_exact`** — *setup:* seeded vault has a known `*.md` count under `wiki/`
    (count them in the fixture). *expected:* `pages_scanned` equals that exact number
    (includes `_templates/` and `meta/` — `find` counts all `*.md`).

### Section 5 — NEW: severity-source parity (gap C.2 — the core of the migration risk)

35. **`spaced_filenames_severity_is_error`** — *expected:* `severity == "error"` even when `count>0`
    (hardcoded literal, not derived).
36. **`orphans_severity_is_warn`** — *expected:* `severity == "warn"`.
37. **`title_overlap_severity_is_info`** — *expected:* `severity == "info"`.
38. **`terminology_severity_passthrough_warn`** — *setup:* seed a page with `dnt_class` whose value
    is valid but with `<2` aliases? (that is ERROR) — instead seed a WARN: a `dnt_class` page absent
    from `meta/termbase.md`. *action:* read `terminology`. *expected:* `severity == "warn"`,
    `errors == 0`, `warns >= 1`, and `count == errors + warns`.
39. **`terminology_severity_passthrough_error`** — *setup:* seed a page with `dnt_class` set to an
    invalid value (not in `{term-of-art,eigenname,coined,hybrid}`) → `lint-terminology.py` emits an
    `ERROR`. *expected:* `terminology.severity == "error"`, `errors >= 1`, and those errors counted
    into `totals.error`.
40. **`terminology_totals_use_subcounts_not_severity`** — *setup:* a vault with BOTH a terminology
    ERROR and a terminology WARN. *expected:* `totals.error` includes the term error AND
    `totals.warn` includes the term warn (i.e. the split is by `errors`/`warns`, not by the single
    top-level `severity`). This is the subtle bash rule at lines 343–345.
41. **`dag_severity_flips_to_error_on_findings`** — *setup:* vault WITH `wiki/meta/research-queue.md`
    containing a duplicate task ID (so `lint-deps.py` reports `duplicates>=1`). *expected:*
    `research_queue_dag.severity == "error"`, `count == DAG_ERRORS >= 1`, counted into `totals.error`.
42. **`dag_severity_info_when_clean`** — *setup:* queue file present, valid DAG (no dup/missing/cycle).
    *expected:* `research_queue_dag.severity == "info"`, `count == 0`, contributes nothing to totals.
43. **`program_severity_flips_to_error`** — *setup:* queue + `decisions/Research-Program-Codes.md`,
    with a queue row referencing an unknown program code. *expected:*
    `research_program_codes.severity == "error"`, `count >= 1`, into `totals.error`.

### Section 6 — NEW: optional-check gating (gap C.3)

44. **`dag_check_absent_queue_zeroed`** — *setup:* seeded vault with **no** `meta/research-queue.md`.
    *expected:* `research_queue_dag` still present with `count==0`, `severity=="info"`, all sub-keys `0`.
45. **`program_check_absent_files_zeroed`** — *setup:* no queue / no decision doc. *expected:*
    `research_program_codes` present, `count==0`, `severity=="info"`, sub-keys `0`.
46. **`dag_skipped_when_script_missing`** — *setup (white-box / env):* simulate `lint-deps.py`
    absent (e.g. point at a vault but the harness should guard on `SCRIPT_DIR/lint-deps.py`
    existence). *expected:* no crash; `research_queue_dag.count==0`. *(Documents the
    `[ -f "$SCRIPT_DIR/lint-deps.py" ]` guard — hard to trigger without relocating scripts;
    mark `skip` if the port keeps scripts co-located. See C.6.)*

### Section 7 — NEW: CLI-surface parity (gap C.4)

47. **`unknown_flag_exit_2`** — *action:* run `run-lint.py --bogus` on seeded vault.
    *expected:* return code `2`, stderr mentions the unknown flag.
48. **`extra_positional_exit_2`** — *action:* run `run-lint.py /a /b`. *expected:* return code `2`,
    stderr mentions "extra positional".
49. **`help_exit_0_to_stderr`** — *action:* run `run-lint.py --help`. *expected:* return code `0`;
    usage text emitted (to **stderr**, per the `.sh`); no report file created.
50. **`no_report_is_alias_for_json`** — *action:* run `run-lint.py --no-report` and `--json` on the
    same vault. *expected:* both print JSON to stdout, neither writes a report file; the two JSON
    payloads are structurally identical (ignoring nondeterministic ordering, if any).
51. **`json_suppresses_report_and_summary`** — *action:* run `--json`. *expected:* no
    `wiki/meta/lint-report-*.md` created during this run AND no `Totals:`/`Lint report:` summary
    line on stdout (stdout is pure JSON).
52. **`quiet_writes_report_no_stdout`** — *action:* run `--quiet`. *expected:* report file exists,
    stdout is empty (no `Lint report:` / `Totals:` lines).
53. **`default_mode_writes_report_and_summary`** — *action:* run with no flags. *expected:* report
    file exists AND stdout contains `Lint report: <path>` and a `Totals: error=… warn=… info=… pages=…` line.
54. **`json_and_quiet_json_wins`** — *action:* run `--json --quiet`. *expected:* JSON on stdout,
    no report file (JSON branch short-circuits before the quiet/report block).
55. **`positional_vault_root_arg`** — *setup:* seeded vault, `KM_VAULT_PATH` unset. *action:* run
    `run-lint.py <vault> --json`. *expected:* exits 0, `vault_root` == resolved `<vault>`.
56. **`env_overrides_positional`** — *setup:* two seeded vaults A (env) and B (arg). *action:* run
    `KM_VAULT_PATH=A run-lint.py B --json`. *expected:* `vault_root` resolves to **A**
    (env wins over positional — the `lib/vault_root.py` contract).

### Section 8 — NEW: report-content parity (gap C.5)

57. **`report_frontmatter_wellformed`** — *expected:* report starts with `---`, has
    `type: meta`, `title: "Lint Report <DATE>"`, `status: developing`, `tags:` incl. `meta` and `lint`.
58. **`report_summary_table_all_checks`** — *expected:* the `## Summary` table has one row per check
    (9 rows) with `| <name> | <severity> | <count> |`.
59. **`report_has_machine_readable_json_block`** — *expected:* report contains a ```json fence whose
    contents parse to the SAME object as the `--json` stdout for the same vault.
60. **`report_findings_truncation_marker`** — *setup:* a vault where one check has `>30` findings
    (e.g. 35 orphan pages). *expected:* that check's Findings section lists 30 `- ` items then a
    `- … 5 more` line (the `count - len(items)` rule). *(Also validates `items` is capped at 30 in JSON.)*

### Section 9 — NEW: exit-code & read-only parity (gap C.7)

61. **`exit_0_with_findings`** — *setup:* seeded vault (has errors). *action:* run default mode.
    *expected:* return code `0` (read-only contract — findings never change exit code).
62. **`read_only_no_wiki_mutation`** — *setup:* snapshot mtimes/hashes of all seeded `wiki/*.md`
    EXCEPT the generated `meta/lint-report-*.md`. *action:* run default mode. *expected:* no
    pre-existing wiki content file is modified (only the report is created).
63. **`exit_2_message_on_missing_wiki`** — *setup:* empty dir. *expected:* return code `2` AND
    stderr contains a "wiki root … is not a directory"-equivalent message (bash suite only checks
    the code, not the message).

### Section 10 — NEW: empty / edge vault (gap C.8)

64. **`empty_wiki_zero_findings`** — *setup:* vault with `wiki/` present but containing only a
    well-formed `index.md` (no violations). *expected:* all checks `count==0`,
    `totals=={"error":0,"warn":0,"info":0}`, exit 0, report still written.
65. **`templates_excluded_from_spaced_filenames`** — *setup:* `_templates/has spaces.md` present
    (the fixture already seeds this). *expected:* `spaced_filenames.count` does NOT include the
    template file (the `! -path "$WIKI_ROOT/_templates/*"` exclusion).
66. **`meta_and_templates_excluded_from_spaced_links`** — *setup:* put a `[[Spaced Target]]` link
    inside `meta/<x>.md` and `_templates/<y>.md`. *expected:* `spaced_wikilinks_body` does NOT count
    those (inline-python skips dirs named `_templates` or `meta`).
67. **`dead_link_targets_respects_raw_and_paths`** — *setup:* vault with `.raw/Some-Source.pdf` and a
    body wikilink `[[Some-Source]]`, plus a nested page `concepts/Nested.md` referenced as
    `[[concepts/Nested]]`. *expected (CORRECTED, `run-lint.py`):* **neither** counts as dead — the
    `.raw/Some-Source.pdf` source contributes the basename stem `some-source` to the valid set, and
    the wiki-relative slash path `concepts/nested` is caught by the path union. This is the
    fix-forward behavior; under the legacy `run-lint.sh` the bare `[[Some-Source]]` would still be
    DEAD (full-path-with-`.pdf` valid entry), so `run-lint.py` diverges here (see the A.5 divergence
    box). The earlier characterization that asserted `some-source` IS dead has been **flipped** to
    assert it is NOT dead.

### Section 11 — NEW: corrected `.raw`-union edge cases (fix-forward, `run-lint.py` only)

White-box cases over `dead_link_targets(wiki_root, vault_root)` (plus one black-box integration via
`--json` + report), each in a throwaway temp vault. These lock the corrected basename-stem semantics
of §A.5 step 4. They assert behavior that **diverges from `run-lint.sh`** and must be excluded from
any parity golden-diff (E3).

- **(a) core** — `.raw/foo.pdf` + `[[foo]]` → NOT dead.
- **(b) all globbed exts** — each of `.raw/x.md`, `.raw/x.txt`, `.raw/x.json` → `[[x]]` NOT dead.
- **(c) case-insensitive** — `.raw/Foo.PDF` → `[[foo]]` NOT dead (basename + extension folded).
- **(d) subdirectory** — `.raw/sub/deep/foo.pdf` → `[[foo]]` NOT dead (basename match; subdir ignored).
- **(e) final-extension-only** — `.raw/foo.bar.pdf` → `[[foo.bar]]` NOT dead **and** `[[foo]]` STILL dead.
- **(f) spaces** — `.raw/my source.pdf` → `[[my source]]` NOT dead (independent of the spaced-link check).
- **(g) glob scope unchanged** — `.raw/foo.png` → `[[foo]]` STILL dead (extension not in the glob).
- **(h) no `.raw` dir** — no crash; a link to a nonexistent target is still dead.
- **(i) genuinely-dead regression** — `[[nonexistent]]` with no page and no matching raw → STILL dead.
- **(j) valid-page regression** — a normal valid wiki-page link stays valid; `spaced_filenames` /
  `frontmatter_gaps` counts unchanged from a clean base vault.
- **(k) dedup/collision** — `.raw/a.pdf` + `.raw/a.md` collapse to a single target; `[[a]]` valid
  (accepted typo-masking trade-off, basename-only).
- **(l) integration** — on a vault mixing a valid page link, a raw-backed link, and a genuinely dead
  link, the `--json` `dead_link_targets` count and the Markdown report both reflect the corrected
  set (only the genuinely dead target is listed).

---

## Part C — Coverage gaps in the existing bash suite (what B24+ add)

The 23 bash cases assert presence and `>=` thresholds only. Concrete gaps:

- **C.1 No exact schema / value-type checks.** Bash never asserts the full key set, that counts are
  integers, that `items` are strings, exact `pages_scanned`, or `vault_root` value. → B24–B34.
- **C.2 No severity-source coverage.** Bash never distinguishes hardcoded vs pass-through vs flipped
  severity. The terminology pass-through and the dag/program `info→error` flips are entirely
  untested — yet they are the highest-risk behaviors to reproduce in Python. → B35–B43.
- **C.3 Last two checks untested.** `research_queue_dag` and `research_program_codes` are never
  asserted present, nor their gating-when-files-absent behavior. → B25, B44–B46.
- **C.4 CLI surface barely tested.** Only `--json` and `--quiet` exercised. Untested:
  `--no-report` alias, `--help`/`-h`, unknown-flag exit 2, extra-positional exit 2, positional vault
  arg, env-vs-arg precedence, `--json`+`--quiet` interaction, default-mode summary line. → B47–B56.
- **C.5 Report content shallow.** Bash checks only that the file exists, has the title, and mentions
  `spaced_filenames`. Untested: frontmatter, the full summary table, the embedded JSON block,
  the `… N more` truncation. → B57–B60.
- **C.6 `totals` split rule untested.** The terminology errors/warns split into totals
  (lines 343–345) and the dag/program count-into-flipped-severity rule (346–348) are untested. → B40, B41.
- **C.7 Read-only / exit-code-decoupled-from-findings never asserted.** → B61–B63.
- **C.8 No empty-vault, no `_templates`/`meta` exclusion, no `.raw` union tests.** → B64–B67,
  plus Section 11 (a)–(l) for the **corrected** `.raw` basename-stem union (fix-forward in
  `run-lint.py`; diverges from `run-lint.sh`).
- **C.9 No item-cap (30) test.** → B60.
- **C.10 White-box hooks absent.** Because the source is bash, there are no unit tests of individual
  helpers. The port should expose pure functions (e.g. `build_summary(...)`, `dead_link_targets(...)`,
  `resolve_severity(...)`) so `importlib`-style unit tests (mirroring `test_tiling_check.py`) can
  cover the totals math and severity logic directly, not just end-to-end. Spec recommends the port
  factor these out; B-cases that need them are marked.

---

## Part D — Portability landmines in `run-lint.sh` (faithful-port hazards)

Each is a place where a naive Python rewrite silently diverges. The port must consciously
reproduce or deliberately neutralize each.

1. **Inline `python3 -c` / heredoc string-interpolation of paths.** Lines 377–385, 387–400,
   408–413 build Python via `python3 -c "...$TMP..."` with **shell** interpolation of `$TMP`
   into a double-quoted Python string. A vault/temp path containing a quote, `$`, or backtick would
   break the bash version; the Python port removes this class entirely but MUST NOT reintroduce it
   (no `subprocess` round-trips to build the report). Characterize current behavior as: assumes
   temp paths are shell-safe.
2. **`read -r A B < <(python3 ...)` process substitution.** Lines 172–182 (terminology), 216–230
   (dag), 249–257 (programs) parse sub-script JSON via a one-line `print` and `read`. The comments
   explicitly note this is a workaround for "subshell exit-code quirks that bit the earlier
   two-call form" and "the `|| true` fallthrough that produced `0\n0`". The port must replicate the
   *result* (robust 0/0 on any parse failure) — i.e. JSON-parse defensively and default every count
   to 0 on exception. Process substitution `< <(...)` is bash-only (not POSIX `sh`).
3. **`grep -c` / `grep` "no match → exit 1" + `pipefail`.** Lines 121 (`grep … || true`), 192–194
   (switched to `awk '/^[0-9]/{n++}'` specifically because `grep -c` returns exit 1 on zero and,
   under `pipefail`, produced a spurious `0\n0`). The port must ensure "zero findings" yields a clean
   integer `0`, never a doubled or error value.
4. **`grep -rEho` (GNU-ish flags) — BSD/macOS divergence.** `-h` (no filename), `-o` (only match),
   `-E` (ERE), `-r` (recursive) combined. macOS BSD grep supports these, but `grep -P` (PCRE) is
   absent on BSD — the script wisely avoids `-P`. A Python port using `re` sidesteps the
   GNU/BSD grep split entirely; characterize the regex as ERE `\[\[[^]]+\]\]`.
5. **`sed -E` (ERE) — GNU vs BSD `-E` vs `-r`.** Lines 47, 122–123, 125, 128–129 use `sed -E`.
   macOS BSD sed uses `-E` (ok) but GNU historically `-r`; in-place and `\n` handling also differ.
   The `--help` path `sed -n '1,30p' "$0" | sed 's|^# \?||'` strips a literal `# ` (note the `\?`
   optional-space is a GNU ERE-ism inside a BRE `s///` — on BSD `\?` may be literal). The port should
   reproduce the *help text content*, not the sed mechanics.
6. **`tr 'A-Z' 'a-z'` locale/range casing.** Lines 123, 125, 129. ASCII-range lowercasing;
   differs from Python `.lower()` for non-ASCII (e.g. umlauts, which the wiki explicitly uses —
   see `lint-title-overlap.py` "German umlauts preserved"). The dead-link pipeline lowercases with
   `tr` (ASCII only) while page basenames may contain umlauts → a subtle case-folding mismatch the
   port must replicate exactly (use ASCII-only fold for parity, NOT `str.lower()`), or it will change
   which links count as dead.
7. **`comm -23` requires sorted input + locale collation.** Line 134. `comm` depends on `sort` order;
   `sort -u` collation is locale-sensitive (`LC_ALL` unset → may differ between CI and dev). The port
   must reproduce set-difference semantics; using Python sets removes the collation dependency but the
   port must confirm the *membership* result matches (esp. with the ASCII-fold from landmine 6).
8. **`awk -F/ '{f=$NF…}'` path splitting.** Line 124. Splits on `/` to get the basename; assumes no
   embedded newlines in filenames. Equivalent to `Path(p).name`. Embedded-newline filenames would
   desync `wc -l` counts (each `find` line == one path) — an adversarial edge the bash version does
   not handle; the port should match (assume no newlines in names).
9. **`wc -l` counts trailing newline; `tr -d ' '` strips padding.** Lines 81, 86, 109, 115, 135, 161.
   A file with content but no trailing newline undercounts by one in `wc -l`. The inline Python writers
   all `print()` (newline-terminated), so counts are consistent — but the port must count *records*
   (non-empty lines), matching how each producer emits exactly one finding per line. Off-by-one risk
   if the port counts `splitlines()` vs `split("\n")` on a trailing newline.
10. **`mktemp -d "$TMPROOT/run-lint.XXXXXX"` + `trap 'rm -rf' EXIT`.** Lines 74–76. Honors
    `${TMPDIR:-/tmp}`. The port should use `tempfile.mkdtemp()` (honors `TMPDIR`) with a
    `try/finally` or `atexit` cleanup. The `trap … EXIT` fires on every exit path including the early
    `exit 2`/`exit 0` — the Python port must clean up on the error/`--json`/`--help` paths too.
11. **`set -euo pipefail` interaction with `|| true`.** Line 29. Every tolerated failure is explicitly
    suffixed `|| true` or wrapped `{ … || true; }` or guarded by `[ -x … ]` / `[ -f … ]` / `[ -s … ]`.
    A Python port loses the implicit "abort on any unguarded failure" — it must instead make sub-script
    invocation failures non-fatal *only where the bash does* (every sub-script call is tolerant) while
    still surfacing genuine usage errors (`exit 2`). Do NOT make the whole port `try/except: pass`.
12. **`[ -x "$SCRIPT_DIR/lint-terminology.py" ]` executable-bit gate.** Lines 167, 189. The terminology
    and title-overlap checks run only if the script file has the **executable bit**; dag/programs gate
    on `[ -f ]` (existence) instead. This asymmetry is real behavior: on a checkout where
    `lint-terminology.py` lost its `+x` (e.g. a zip export, a Windows checkout), terminology is silently
    skipped (count 0) while dag still runs. The port must reproduce the *exact* gate per check
    (`-x` for terminology & title-overlap; `-f`/existence for dag & programs) or it changes results on
    permission-stripped trees. **This is the most surprising landmine.**
13. **`date +%Y-%m-%d` timezone.** Line 73. Local-time date; the report filename and `date` field use
    the runner's TZ. The port must use local date (`datetime.date.today()`), not UTC, for filename parity.
14. **`find … -name '* *.md'` glob for spaced filenames.** Line 85. Relies on `find`'s pattern; the
    `_templates` exclusion is `! -path "$WIKI_ROOT/_templates/*"`. The port's `rglob`/walk must apply
    the SAME exclusion (only `_templates`, NOT `meta`) — note this differs from the spaced-*links* check
    which excludes BOTH `_templates` and `meta`. Easy to over- or under-exclude.
15. **Severity-flip vs sub-script exit code.** Sub-scripts (`lint-deps.py`, `lint-programs.py`) exit `1`
    on validation errors but the aggregator ignores that (`|| true` / both branches `:`) and derives
    severity purely from JSON counts. A port that keys severity off the child return code instead of the
    parsed counts would diverge.

---

## Part E — Acceptance criteria for the future port

The port `scripts/run-lint.py` is accepted iff:
- **E1.** All 23 baseline cases (B1–B23) pass via `python3 tests/test_run_lint.py`.
- **E2.** All new cases B24–B67 pass (or are explicitly `skip`-marked with rationale, e.g. B46).
- **E3.** For a corpus of ≥3 real/synthetic vaults, `run-lint.py --json` output is **byte-identical**
  to `run-lint.sh --json` after normalizing only `date`/absolute-path fields **and excluding the
  `.raw`-union scenario** (a golden-file diff test is recommended as an additional B-case once both
  implementations coexist during migration). NOTE: `run-lint.py` intentionally diverges from
  `run-lint.sh` on the `dead_link_targets` `.raw` union (fix-forward — see the §A.5 divergence box),
  so corpus vaults that contain a `.raw/` dir with non-`.md` sources referenced by bare wikilinks
  will legitimately differ; the golden diff must omit those `dead_link_targets` entries (or use
  vaults without such links) until `run-lint.sh` is retired at the shim swap.
- **E4.** Exit codes match the table in A.7 for every flag/error path.
- **E5.** Read-only: no wiki content file mutated; only `meta/lint-report-<DATE>.md` written
  (and only in non-`--json` modes).
- **E6.** Vault resolution uses `lib/vault_root.py` (`resolve_vault_root`) — verified by B56
  (env-over-arg precedence).

**Migration test strategy:** during Phase 2, keep `run-lint.sh` in place and add a golden-diff
case that runs BOTH and asserts equality (E3), **excluding the `.raw`-union scenario** where
`run-lint.py` deliberately fixes forward (§A.5 divergence box; Section 11). Remove the `.sh` only
after the golden diff is green across the vault corpus and B1–B67 + Section 11 pass.
