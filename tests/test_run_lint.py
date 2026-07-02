#!/usr/bin/env python3
"""test_run_lint.py — characterization / parity tests for scripts/run-lint.py.

Implements the test cases from docs/plans/PHASE2-run-lint-pytest-spec.md
(Part B, cases B1-B67). Mirrors tests/test_tiling_check.py style: plain-python
Fail(SystemExit) + assert_eq/assert_true helpers, importlib for white-box unit
tests, subprocess for black-box CLI tests, a __main__ runner that prints
"All tests passed." on success and sys.exit(1) on failure. NOT pytest.

Black-box cases invoke scripts/run-lint.py via subprocess against a throwaway
temp vault selected with KM_VAULT_PATH (tempfile.mkdtemp, $TMPDIR-aware). The
real repo vault is never touched.

Usage:
  python3 tests/test_run_lint.py
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "scripts" / "run-lint.py"

# White-box import of run-lint.py (hyphenated filename -> importlib).
spec = importlib.util.spec_from_file_location("run_lint", HELPER)
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)


class Fail(SystemExit):
    pass


PASS = 0


def ok(label):
    global PASS
    print(f"OK   {label}")
    PASS += 1


def skip(label, why):
    print(f"SKIP {label}: {why}")


def assert_eq(label, expected, actual):
    if expected != actual:
        raise Fail(f"FAIL {label}: expected {expected!r}, got {actual!r}")
    ok(label)


def assert_true(label, cond):
    if not cond:
        raise Fail(f"FAIL {label}")
    ok(label)


# --- shared fixtures -------------------------------------------------------


def _fm(title, type_="meta"):
    return (
        "---\n"
        f"type: {type_}\n"
        f'title: "{title}"\n'
        "created: 2026-05-26\n"
        "updated: 2026-05-26\n"
        "status: developing\n"
        "---\n"
    )


def mk_vault(root: Path):
    """Port of the bash mk_vault (tests/test_run_lint.sh). Seeds the canonical
    fixture: 9 *.md files under wiki/, one spaced filename, one spaced body
    link, one orphan, one missing-frontmatter page, one _templates file."""
    (root / "wiki" / "concepts").mkdir(parents=True)
    (root / "wiki" / "entities").mkdir(parents=True)
    (root / "wiki" / "meta").mkdir(parents=True)
    (root / "wiki" / "_templates").mkdir(parents=True)

    (root / "wiki" / "index.md").write_text(
        _fm("Index") + "[[Linked-Concept]] [[Dead-Target]]\n"
    )
    (root / "wiki" / "log.md").write_text(_fm("Log"))
    (root / "wiki" / "hot.md").write_text(_fm("Hot"))
    (root / "wiki" / "overview.md").write_text(_fm("Overview"))
    (root / "wiki" / "concepts" / "Linked-Concept.md").write_text(
        _fm("Linked Concept", "concept") + "Body.\n"
    )
    (root / "wiki" / "concepts" / "Orphan-Page.md").write_text(
        _fm("Orphan", "concept")
        + "[[Spaced Target]] — this should trip spaced_wikilinks_body\n"
    )
    (root / "wiki" / "concepts" / "Spaced Filename.md").write_text(
        _fm("Spaced Filename", "concept") + "Body.\n"
    )
    (root / "wiki" / "entities" / "No-Frontmatter.md").write_text(
        "Just a body, no YAML.\n"
    )
    (root / "wiki" / "_templates" / "has spaces.md").write_text(
        _fm("Template with spaces") + "Templates may contain placeholder spaces.\n"
    )


# Known seeded *.md count under wiki/ (index, log, hot, overview,
# Linked-Concept, Orphan-Page, Spaced Filename, No-Frontmatter,
# _templates/has spaces = 9). find counts ALL *.md (incl _templates/meta).
SEEDED_PAGES = 9


def new_tmp(prefix="run-lint-test."):
    base = os.environ.get("TMPDIR") or "/tmp"
    return Path(tempfile.mkdtemp(prefix=prefix, dir=base))


def run_lint(vault: Path | None, *args, cwd=None, env_extra=None):
    """Invoke scripts/run-lint.py as a subprocess. When `vault` is given it is
    passed via KM_VAULT_PATH; pass vault=None to leave the env var unset."""
    env = dict(os.environ)
    env.pop("KM_VAULT_PATH", None)
    if vault is not None:
        env["KM_VAULT_PATH"] = str(vault)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True, text=True, env=env, timeout=60,
        cwd=str(cwd) if cwd else None,
    )


def json_for(vault: Path, *extra_args):
    """Run --json on a seeded vault and return the parsed object."""
    r = run_lint(vault, "--json", *extra_args)
    return json.loads(r.stdout)


def check_by_name(summary, name):
    for c in summary["checks"]:
        if c["name"] == name:
            return c
    raise Fail(f"check {name!r} not present")


# A module-level seeded vault + its --json, reused across Section 1/4-10 cases
# that only read the seeded summary (mirrors the bash suite running once).
_SEEDED = None
_SUMMARY = None


def seeded():
    global _SEEDED, _SUMMARY
    if _SEEDED is None:
        _SEEDED = new_tmp()
        mk_vault(_SEEDED)
        _SUMMARY = json_for(_SEEDED)
    return _SEEDED, _SUMMARY


# ===========================================================================
# Section 1 — JSON mode on seeded vault (B1-B19)
# ===========================================================================


def test_section1_json_seeded():
    v, summary = seeded()
    r = run_lint(v, "--json")

    # B1 json_output_nonempty
    assert_true("B1 json_output_nonempty", r.stdout.strip() != "")
    json.loads(r.stdout)  # parses
    ok("B1 json parses")

    # B2-B7 top-level keys present
    for key in ("date", "vault_root", "wiki_root", "pages_scanned",
                "checks", "totals"):
        assert_true(f"B json_key_{key}", key in summary)

    # B8-B14 check names present
    names = [c["name"] for c in summary["checks"]]
    for nm in ("spaced_filenames", "spaced_wikilinks_body", "orphans",
               "dead_link_targets", "frontmatter_gaps", "terminology",
               "title_overlap"):
        assert_true(f"B check_present_{nm}", nm in names)

    # B15 seeded_spaced_filenames_ge_1
    assert_true("B15 spaced_filenames>=1",
                check_by_name(summary, "spaced_filenames")["count"] >= 1)
    # B16 seeded_spaced_wikilinks_body_ge_1
    assert_true("B16 spaced_wikilinks_body>=1",
                check_by_name(summary, "spaced_wikilinks_body")["count"] >= 1)
    # B17 seeded_orphans_ge_1
    assert_true("B17 orphans>=1",
                check_by_name(summary, "orphans")["count"] >= 1)
    # B18 totals_error_ge_2
    assert_true("B18 totals.error>=2", summary["totals"]["error"] >= 2)
    # B19 totals_warn_ge_1
    assert_true("B19 totals.warn>=1", summary["totals"]["warn"] >= 1)


# ===========================================================================
# Section 2 — Report-file mode (B20-B22)
# ===========================================================================


def test_section2_report_file():
    v = new_tmp()
    try:
        mk_vault(v)
        r = run_lint(v, "--quiet")
        assert_eq("B20 quiet rc 0", 0, r.returncode)
        date = datetime.date.today().isoformat()
        report = v / "wiki" / "meta" / f"lint-report-{date}.md"
        assert_true("B20 report_file_written", report.is_file())
        text = report.read_text()
        assert_true("B21 report_has_title_header",
                    f"Lint Report: {date}" in text)
        assert_true("B22 report_mentions_spaced_filenames",
                    "spaced_filenames" in text)
    finally:
        shutil.rmtree(v, ignore_errors=True)


# ===========================================================================
# Section 3 — Resolver / missing-wiki (B23)
# ===========================================================================


def test_section3_missing_wiki():
    empty = new_tmp("run-lint-empty.")
    try:
        # KM_VAULT_PATH unset, cwd = empty dir with no wiki/
        r = run_lint(None, "--json", cwd=empty)
        assert_eq("B23 exit_2_when_wiki_missing", 2, r.returncode)
    finally:
        shutil.rmtree(empty, ignore_errors=True)


# ===========================================================================
# Section 4 — exact-schema & value-type parity (B24-B34)
# ===========================================================================

CHECK_ORDER = [
    "spaced_filenames", "spaced_wikilinks_body", "orphans",
    "dead_link_targets", "frontmatter_gaps", "terminology",
    "title_overlap", "research_queue_dag", "research_program_codes",
    "open_issues",
]


def test_section4_schema():
    _v, summary = seeded()
    checks = summary["checks"]

    # B24 check_order_exact
    assert_eq("B24 check_order_exact", CHECK_ORDER, [c["name"] for c in checks])
    # B25 all_checks_present (9 core + open_issues added by FUP-4)
    assert_eq("B25 len(checks)==10", 10, len(checks))
    names = [c["name"] for c in checks]
    assert_true("B25 dag+programs+open_issues present",
                "research_queue_dag" in names
                and "research_program_codes" in names
                and "open_issues" in names)

    # B26 top_level_value_types
    assert_true("B26 date is str", isinstance(summary["date"], str))
    assert_true("B26 vault_root is str", isinstance(summary["vault_root"], str))
    assert_true("B26 wiki_root is str", isinstance(summary["wiki_root"], str))
    assert_true("B26 pages_scanned is int",
                isinstance(summary["pages_scanned"], int))
    assert_true("B26 checks is list", isinstance(summary["checks"], list))
    assert_true("B26 totals is dict", isinstance(summary["totals"], dict))

    # B27 counts_are_integers (top-level count + every numeric sub-key)
    numeric_subkeys = (
        "errors", "warns", "duplicates", "missing_targets", "cycles",
        "ready_set", "task_count", "unknown_codes", "missing_home_pages",
        "triage_tasks",
    )
    all_int = True
    for c in checks:
        if type(c["count"]) is not int:
            all_int = False
        for k in numeric_subkeys:
            if k in c and type(c[k]) is not int:
                all_int = False
    assert_true("B27 counts_are_integers", all_int)

    # B28 items_are_strings
    all_str = all(
        isinstance(it, str) for c in checks for it in c.get("items", [])
    )
    assert_true("B28 items_are_strings", all_str)

    # B29 totals_keys_exact
    assert_eq("B29 totals_keys_exact",
              {"error", "warn", "info"}, set(summary["totals"].keys()))

    # B30 terminology_subkeys_present
    term = check_by_name(summary, "terminology")
    assert_true("B30 terminology_subkeys_present",
                isinstance(term.get("errors"), int)
                and isinstance(term.get("warns"), int))

    # B31 dag_subkeys_present
    dag = check_by_name(summary, "research_queue_dag")
    assert_true("B31 dag_subkeys_present", all(
        isinstance(dag.get(k), int) for k in
        ("duplicates", "missing_targets", "cycles", "ready_set", "task_count")
    ))

    # B32 program_subkeys_present
    prog = check_by_name(summary, "research_program_codes")
    assert_true("B32 program_subkeys_present", all(
        isinstance(prog.get(k), int) for k in
        ("unknown_codes", "missing_home_pages", "triage_tasks")
    ))

    # B33 vault_root_resolved_absolute
    v, _ = seeded()
    assert_eq("B33 vault_root resolved absolute",
              str(Path(v).resolve()), summary["vault_root"])
    assert_eq("B33 wiki_root == vault_root/wiki",
              summary["vault_root"] + "/wiki", summary["wiki_root"])

    # B34 pages_scanned_exact
    assert_eq("B34 pages_scanned_exact", SEEDED_PAGES, summary["pages_scanned"])


# ===========================================================================
# Section 5 — severity-source parity (B35-B43)
# ===========================================================================


def test_section5_severity_hardcoded():
    _v, summary = seeded()
    # B35 spaced_filenames severity is hardcoded error even when count>0
    sf = check_by_name(summary, "spaced_filenames")
    assert_true("B35 spaced_filenames count>0", sf["count"] > 0)
    assert_eq("B35 spaced_filenames_severity_is_error", "error", sf["severity"])
    # B36 orphans severity warn
    assert_eq("B36 orphans_severity_is_warn", "warn",
              check_by_name(summary, "orphans")["severity"])
    # B37 title_overlap severity info
    assert_eq("B37 title_overlap_severity_is_info", "info",
              check_by_name(summary, "title_overlap")["severity"])


def _seed_base_vault(v: Path):
    """Minimal valid vault: wiki/ with one well-formed index.md."""
    (v / "wiki" / "meta").mkdir(parents=True)
    (v / "wiki" / "index.md").write_text(_fm("Index"))


def test_section5_terminology_passthrough_warn():
    # B38 dnt_class valid but page absent from termbase -> WARN
    v = new_tmp()
    try:
        _seed_base_vault(v)
        (v / "wiki" / "concepts").mkdir(parents=True)
        (v / "wiki" / "concepts" / "Warn-Term.md").write_text(
            _fm("Warn Term", "concept")
            + "dnt_class: coined\naliases:\n  - Alpha\n  - Beta\n"
        )
        # NOTE: dnt_class/aliases must be inside frontmatter; rebuild properly.
        (v / "wiki" / "concepts" / "Warn-Term.md").write_text(
            "---\ntype: concept\ntitle: \"Warn Term\"\ncreated: 2026-05-26\n"
            "updated: 2026-05-26\nstatus: developing\ndnt_class: coined\n"
            "aliases:\n  - Alpha\n  - Beta\n---\nBody.\n"
        )
        term = check_by_name(json_for(v), "terminology")
        if not (os.access(ROOT / "scripts" / "lint-terminology.py", os.X_OK)):
            skip("B38 terminology_passthrough_warn",
                 "lint-terminology.py not executable")
            return
        assert_eq("B38 terminology severity warn", "warn", term["severity"])
        assert_eq("B38 terminology errors==0", 0, term["errors"])
        assert_true("B38 terminology warns>=1", term["warns"] >= 1)
        assert_eq("B38 terminology count==errors+warns",
                  term["errors"] + term["warns"], term["count"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section5_terminology_passthrough_error():
    # B39 dnt_class invalid value -> ERROR
    v = new_tmp()
    try:
        _seed_base_vault(v)
        (v / "wiki" / "concepts").mkdir(parents=True)
        (v / "wiki" / "concepts" / "Bad-Term.md").write_text(
            "---\ntype: concept\ntitle: \"Bad Term\"\ncreated: 2026-05-26\n"
            "updated: 2026-05-26\nstatus: developing\n"
            "dnt_class: not-a-valid-class\naliases:\n  - One\n  - Two\n---\nBody.\n"
        )
        if not os.access(ROOT / "scripts" / "lint-terminology.py", os.X_OK):
            skip("B39 terminology_passthrough_error",
                 "lint-terminology.py not executable")
            return
        summary = json_for(v)
        term = check_by_name(summary, "terminology")
        assert_eq("B39 terminology severity error", "error", term["severity"])
        assert_true("B39 terminology errors>=1", term["errors"] >= 1)
        assert_true("B39 term errors in totals.error",
                    summary["totals"]["error"] >= term["errors"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section5_terminology_totals_split():
    # B40 BOTH a terminology ERROR and WARN -> totals split by errors/warns
    v = new_tmp()
    try:
        _seed_base_vault(v)
        (v / "wiki" / "concepts").mkdir(parents=True)
        (v / "wiki" / "concepts" / "Bad-Term.md").write_text(
            "---\ntype: concept\ntitle: \"Bad Term\"\ncreated: 2026-05-26\n"
            "updated: 2026-05-26\nstatus: developing\n"
            "dnt_class: not-a-valid-class\naliases:\n  - One\n  - Two\n---\nBody.\n"
        )
        (v / "wiki" / "concepts" / "Warn-Term.md").write_text(
            "---\ntype: concept\ntitle: \"Warn Term\"\ncreated: 2026-05-26\n"
            "updated: 2026-05-26\nstatus: developing\ndnt_class: coined\n"
            "aliases:\n  - Alpha\n  - Beta\n---\nBody.\n"
        )
        if not os.access(ROOT / "scripts" / "lint-terminology.py", os.X_OK):
            skip("B40 terminology_totals_split",
                 "lint-terminology.py not executable")
            return
        summary = json_for(v)
        term = check_by_name(summary, "terminology")
        assert_true("B40 term has both error+warn",
                    term["errors"] >= 1 and term["warns"] >= 1)
        assert_true("B40 totals.error includes term error",
                    summary["totals"]["error"] >= term["errors"])
        assert_true("B40 totals.warn includes term warn",
                    summary["totals"]["warn"] >= term["warns"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def _queue_table(rows: list[str]) -> str:
    head = (
        "---\ntype: meta\ntitle: \"Research Queue\"\ncreated: 2026-05-26\n"
        "updated: 2026-05-26\nstatus: developing\n---\n\n## Active Queue\n\n"
        "| ID | Status | Prio | Program | Title | Brief | Deps | Created | Updated |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    return head + "".join(r + "\n" for r in rows)


def test_section5_dag_flip_to_error():
    # B41 queue with duplicate task ID -> dag severity flips to error
    v = new_tmp()
    try:
        _seed_base_vault(v)
        (v / "wiki" / "meta" / "research-queue.md").write_text(_queue_table([
            "| R-2026-001 | queued | P1 | EVAL | A | brief | — | 2026-05-26 | 2026-05-26 |",
            "| R-2026-001 | queued | P1 | EVAL | B | brief | — | 2026-05-26 | 2026-05-26 |",
        ]))
        summary = json_for(v)
        dag = check_by_name(summary, "research_queue_dag")
        assert_eq("B41 dag severity error", "error", dag["severity"])
        assert_true("B41 dag count>=1", dag["count"] >= 1)
        assert_eq("B41 dag count==duplicates+missing+cycles",
                  dag["duplicates"] + dag["missing_targets"] + dag["cycles"],
                  dag["count"])
        assert_true("B41 dag counted into totals.error",
                    summary["totals"]["error"] >= dag["count"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section5_dag_info_when_clean():
    # B42 valid DAG -> info, count 0, contributes nothing
    v = new_tmp()
    try:
        _seed_base_vault(v)
        (v / "wiki" / "meta" / "research-queue.md").write_text(_queue_table([
            "| R-2026-001 | queued | P1 | EVAL | A | brief | — | 2026-05-26 | 2026-05-26 |",
        ]))
        summary = json_for(v)
        dag = check_by_name(summary, "research_queue_dag")
        assert_eq("B42 dag severity info", "info", dag["severity"])
        assert_eq("B42 dag count 0", 0, dag["count"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section5_program_flip_to_error():
    # B43 queue row referencing an unknown program code -> error
    v = new_tmp()
    try:
        _seed_base_vault(v)
        (v / "wiki" / "decisions").mkdir(parents=True)
        (v / "wiki" / "meta" / "research-queue.md").write_text(_queue_table([
            "| R-2026-001 | queued | P1 | NOPE | A | brief | — | 2026-05-26 | 2026-05-26 |",
        ]))
        (v / "wiki" / "decisions" / "Research-Program-Codes.md").write_text(
            "---\ntype: decision\ntitle: \"Research Program Codes\"\n"
            "created: 2026-05-26\nupdated: 2026-05-26\nstatus: developing\n---\n\n"
            "## Seed list\n\n| Code | Name | Notes |\n|---|---|---|\n"
            "| `EVAL` | Evals | x |\n"
        )
        summary = json_for(v)
        prog = check_by_name(summary, "research_program_codes")
        assert_eq("B43 program severity error", "error", prog["severity"])
        assert_true("B43 program count>=1", prog["count"] >= 1)
        assert_true("B43 program counted into totals.error",
                    summary["totals"]["error"] >= prog["count"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


# ===========================================================================
# Section 6 — optional-check gating (B44-B46)
# ===========================================================================


def test_section6_dag_absent_zeroed():
    # B44 no research-queue.md -> dag present, count 0, info, sub-keys 0
    _v, summary = seeded()
    dag = check_by_name(summary, "research_queue_dag")
    assert_eq("B44 dag count 0 (no queue)", 0, dag["count"])
    assert_eq("B44 dag severity info", "info", dag["severity"])
    assert_true("B44 dag subkeys 0", all(
        dag[k] == 0 for k in
        ("duplicates", "missing_targets", "cycles", "ready_set", "task_count")
    ))


def test_section6_program_absent_zeroed():
    # B45 no queue / no decision doc -> programs present, count 0, info
    _v, summary = seeded()
    prog = check_by_name(summary, "research_program_codes")
    assert_eq("B45 program count 0", 0, prog["count"])
    assert_eq("B45 program severity info", "info", prog["severity"])
    assert_true("B45 program subkeys 0", all(
        prog[k] == 0 for k in
        ("unknown_codes", "missing_home_pages", "triage_tasks")
    ))


def test_section6_dag_skipped_when_script_missing():
    # B46 — scripts are co-located in this port; marked skip per spec C.6.
    skip("B46 dag_skipped_when_script_missing",
         "scripts co-located with run-lint.py; guard not triggerable without "
         "relocating scripts (spec C.6 permits skip)")


# ===========================================================================
# Section 7 — CLI-surface parity (B47-B56)
# ===========================================================================


def test_section7_unknown_flag():
    v, _ = seeded()
    r = run_lint(v, "--bogus")
    assert_eq("B47 unknown_flag_exit_2", 2, r.returncode)
    assert_true("B47 unknown flag stderr", "unknown flag" in r.stderr)


def test_section7_extra_positional():
    r = run_lint(None, "/a", "/b")
    assert_eq("B48 extra_positional_exit_2", 2, r.returncode)
    assert_true("B48 extra positional stderr",
                "extra positional" in r.stderr)


def test_section7_help():
    v = new_tmp()
    try:
        mk_vault(v)
        r = run_lint(v, "--help")
        assert_eq("B49 help_exit_0", 0, r.returncode)
        # usage text emitted to stderr, not stdout
        assert_true("B49 help usage on stderr", "Usage" in r.stderr)
        assert_eq("B49 help stdout empty", "", r.stdout)
        date = datetime.date.today().isoformat()
        report = v / "wiki" / "meta" / f"lint-report-{date}.md"
        assert_true("B49 help writes no report", not report.exists())
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section7_no_report_alias():
    v = new_tmp()
    try:
        mk_vault(v)
        date = datetime.date.today().isoformat()
        report = v / "wiki" / "meta" / f"lint-report-{date}.md"

        r1 = run_lint(v, "--no-report")
        a = json.loads(r1.stdout)
        no_report_created = not report.exists()

        r2 = run_lint(v, "--json")
        b = json.loads(r2.stdout)

        # normalize the report file possibly created in between (it should not)
        assert_true("B50 --no-report writes no report", no_report_created)
        # structurally identical (date/paths are identical for same vault)
        assert_eq("B50 no_report_is_alias_for_json", a, b)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section7_json_suppresses_report_and_summary():
    v = new_tmp()
    try:
        mk_vault(v)
        r = run_lint(v, "--json")
        date = datetime.date.today().isoformat()
        report = v / "wiki" / "meta" / f"lint-report-{date}.md"
        assert_true("B51 --json no report file", not report.exists())
        assert_true("B51 --json no summary line",
                    "Totals:" not in r.stdout and "Lint report:" not in r.stdout)
        json.loads(r.stdout)  # stdout is pure JSON
        ok("B51 stdout is pure JSON")
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section7_quiet_writes_report_no_stdout():
    v = new_tmp()
    try:
        mk_vault(v)
        r = run_lint(v, "--quiet")
        date = datetime.date.today().isoformat()
        report = v / "wiki" / "meta" / f"lint-report-{date}.md"
        assert_true("B52 quiet report exists", report.is_file())
        assert_eq("B52 quiet stdout empty", "", r.stdout)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section7_default_mode():
    v = new_tmp()
    try:
        mk_vault(v)
        r = run_lint(v)
        date = datetime.date.today().isoformat()
        report = v / "wiki" / "meta" / f"lint-report-{date}.md"
        assert_true("B53 default report exists", report.is_file())
        # The script prints the RESOLVED vault path (resolve_vault_root() calls
        # .resolve(); on macOS /var -> /private/var), so match the resolved form.
        resolved_report = v.resolve() / "wiki" / "meta" / f"lint-report-{date}.md"
        assert_true("B53 default stdout has 'Lint report:'",
                    f"Lint report: {resolved_report}" in r.stdout)
        assert_true("B53 default stdout has Totals line",
                    "Totals: error=" in r.stdout and "pages=" in r.stdout)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section7_json_and_quiet_json_wins():
    v = new_tmp()
    try:
        mk_vault(v)
        r = run_lint(v, "--json", "--quiet")
        date = datetime.date.today().isoformat()
        report = v / "wiki" / "meta" / f"lint-report-{date}.md"
        assert_true("B54 json+quiet: JSON on stdout",
                    r.stdout.strip().startswith("{"))
        json.loads(r.stdout)
        assert_true("B54 json+quiet: no report file", not report.exists())
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section7_positional_vault_arg():
    v = new_tmp()
    try:
        mk_vault(v)
        # KM_VAULT_PATH unset; pass vault as positional arg
        r = run_lint(None, str(v), "--json")
        assert_eq("B55 positional rc 0", 0, r.returncode)
        summary = json.loads(r.stdout)
        assert_eq("B55 positional_vault_root_arg",
                  str(Path(v).resolve()), summary["vault_root"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section7_env_overrides_positional():
    a = new_tmp("run-lint-A.")
    b = new_tmp("run-lint-B.")
    try:
        mk_vault(a)
        mk_vault(b)
        # KM_VAULT_PATH=A, positional=B -> env A wins
        r = run_lint(a, str(b), "--json")
        summary = json.loads(r.stdout)
        assert_eq("B56 env_overrides_positional",
                  str(Path(a).resolve()), summary["vault_root"])
    finally:
        shutil.rmtree(a, ignore_errors=True)
        shutil.rmtree(b, ignore_errors=True)


# ===========================================================================
# Section 8 — report-content parity (B57-B60)
# ===========================================================================


def test_section8_report_frontmatter():
    v = new_tmp()
    try:
        mk_vault(v)
        run_lint(v, "--quiet")
        date = datetime.date.today().isoformat()
        text = (v / "wiki" / "meta" / f"lint-report-{date}.md").read_text()
        assert_true("B57 report starts with ---", text.startswith("---"))
        assert_true("B57 type: meta", "type: meta" in text)
        assert_true("B57 title", f'title: "Lint Report {date}"' in text)
        assert_true("B57 status developing", "status: developing" in text)
        assert_true("B57 tags meta+lint",
                    "- meta" in text and "- lint" in text)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section8_summary_table_all_checks():
    v = new_tmp()
    try:
        mk_vault(v)
        run_lint(v, "--quiet")
        date = datetime.date.today().isoformat()
        text = (v / "wiki" / "meta" / f"lint-report-{date}.md").read_text()
        # one table row per check, shape | name | severity | count |
        rows = 0
        for c in CHECK_ORDER:
            for line in text.splitlines():
                if line.startswith(f"| {c} |"):
                    rows += 1
                    break
        assert_eq("B58 report_summary_table_all_checks", len(CHECK_ORDER), rows)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section8_machine_readable_json_block():
    v = new_tmp()
    try:
        mk_vault(v)
        # Capture --json FIRST, before any report exists, so the inventory
        # observes the same file set the --quiet run will. (Writing the report
        # adds a *.md to wiki/meta and would bump pages_scanned on a later run —
        # faithful shared behavior of both .sh and .py.)
        stdout_json = json_for(v)
        run_lint(v, "--quiet")
        date = datetime.date.today().isoformat()
        text = (v / "wiki" / "meta" / f"lint-report-{date}.md").read_text()
        start = text.index("```json\n") + len("```json\n")
        end = text.index("\n```", start)
        embedded = json.loads(text[start:end])
        assert_eq("B59 report_has_machine_readable_json_block",
                  stdout_json, embedded)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section8_findings_truncation():
    # B60 a check with >30 findings -> 30 items then "- … N more"
    v = new_tmp()
    try:
        _seed_base_vault(v)
        (v / "wiki" / "concepts").mkdir(parents=True)
        for i in range(1, 36):  # 35 orphan pages
            (v / "wiki" / "concepts" / f"Orphan-{i}.md").write_text(
                _fm(f"Orphan {i}", "concept") + "Body.\n"
            )
        summary = json_for(v)
        orphans = check_by_name(summary, "orphans")
        assert_true("B60 orphans count>30", orphans["count"] > 30)
        assert_eq("B60 items capped at 30 in JSON", 30, len(orphans["items"]))

        run_lint(v, "--quiet")
        date = datetime.date.today().isoformat()
        text = (v / "wiki" / "meta" / f"lint-report-{date}.md").read_text()
        more = orphans["count"] - len(orphans["items"])
        assert_true("B60 report truncation marker",
                    f"- … {more} more" in text)
    finally:
        shutil.rmtree(v, ignore_errors=True)


# ===========================================================================
# Section 9 — exit-code & read-only parity (B61-B63)
# ===========================================================================


def test_section9_exit_0_with_findings():
    v = new_tmp()
    try:
        mk_vault(v)
        r = run_lint(v)  # default mode, vault has errors
        assert_eq("B61 exit_0_with_findings", 0, r.returncode)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section9_read_only_no_mutation():
    v = new_tmp()
    try:
        mk_vault(v)
        # snapshot mtime+size of every wiki *.md EXCEPT the report dir output
        before = {}
        for p in (v / "wiki").rglob("*.md"):
            before[p] = (p.stat().st_mtime_ns, p.stat().st_size)
        run_lint(v)  # default mode writes only the report
        date = datetime.date.today().isoformat()
        report = v / "wiki" / "meta" / f"lint-report-{date}.md"
        mutated = []
        for p, sig in before.items():
            if p == report:
                continue
            if (p.stat().st_mtime_ns, p.stat().st_size) != sig:
                mutated.append(p)
        assert_eq("B62 read_only_no_wiki_mutation", [], mutated)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section9_exit_2_message_on_missing_wiki():
    empty = new_tmp("run-lint-empty.")
    try:
        r = run_lint(None, "--json", cwd=empty)
        assert_eq("B63 exit_2 on missing wiki", 2, r.returncode)
        assert_true("B63 stderr mentions wiki not a directory",
                    "wiki root" in r.stderr and "is not a directory" in r.stderr)
    finally:
        shutil.rmtree(empty, ignore_errors=True)


# ===========================================================================
# Section 10 — empty / edge vault (B64-B67)
# ===========================================================================


def test_section10_empty_wiki_zero_findings():
    v = new_tmp()
    try:
        _seed_base_vault(v)  # only a well-formed index.md
        summary = json_for(v)
        for c in summary["checks"]:
            assert_eq(f"B64 {c['name']} count 0", 0, c["count"])
        assert_eq("B64 totals all zero",
                  {"error": 0, "warn": 0, "info": 0}, summary["totals"])
        r = run_lint(v)  # default mode still writes a report, exit 0
        assert_eq("B64 empty vault exit 0", 0, r.returncode)
        date = datetime.date.today().isoformat()
        assert_true("B64 report still written",
                    (v / "wiki" / "meta" / f"lint-report-{date}.md").is_file())
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section10_templates_excluded_from_spaced_filenames():
    # B65 _templates/has spaces.md must NOT count (fixture seeds it)
    _v, summary = seeded()
    sf = check_by_name(summary, "spaced_filenames")
    template_counted = any("_templates" in it for it in sf["items"])
    assert_true("B65 templates_excluded_from_spaced_filenames",
                not template_counted)


def test_section10_meta_and_templates_excluded_from_spaced_links():
    # B66 [[Spaced Target]] in meta/ and _templates/ must NOT count
    v = new_tmp()
    try:
        _seed_base_vault(v)
        (v / "wiki" / "_templates").mkdir(parents=True)
        (v / "wiki" / "meta" / "with-link.md").write_text(
            _fm("Meta Link") + "[[Spaced Target]]\n"
        )
        (v / "wiki" / "_templates" / "tmpl.md").write_text(
            _fm("Tmpl Link") + "[[Spaced Target]]\n"
        )
        sw = check_by_name(json_for(v), "spaced_wikilinks_body")
        assert_eq("B66 meta_and_templates_excluded_from_spaced_links",
                  0, sw["count"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section10_dead_link_respects_raw_and_paths():
    # B67 — validates the wiki-relative slash-path union AND the CORRECTED
    # .raw-union behavior of run-lint.py.
    #
    # FIX-FORWARD NOTE (run-lint.py diverges from run-lint.sh here): the legacy
    # .sh raw pipeline
    #   find "$VAULT/.raw" ... | sed 's|\.md$||' | tr A-Z a-z
    # operated on find's FULL paths and stripped only a trailing `.md`, so a
    # `.raw/<x>.pdf` entered the valid set as a full lowercased path WITH its
    # `.pdf` suffix and a bare `[[<x>]]` could never match it (always DEAD).
    # run-lint.py is fixed forward: each in-glob `.raw` file contributes its
    # BASENAME with the final extension stripped, lowercased. So
    # `.raw/Some-Source.pdf` -> valid target `some-source`, and
    # `[[Some-Source]]` is NOT dead. (run-lint.sh keeps the legacy bug until the
    # shim swap; any future parity golden-diff must exclude this raw scenario.)
    v = new_tmp()
    try:
        _seed_base_vault(v)
        (v / ".raw").mkdir(parents=True)
        (v / ".raw" / "Some-Source.pdf").write_text("")
        (v / "wiki" / "concepts").mkdir(parents=True)
        (v / "wiki" / "concepts" / "Nested.md").write_text(_fm("Nested", "concept"))
        (v / "wiki" / "index.md").write_text(
            _fm("Index") + "[[Some-Source]] [[concepts/Nested]]\n"
        )
        dead = check_by_name(json_for(v), "dead_link_targets")
        # Path union DOES catch the nested wiki-relative slash path.
        assert_true("B67 nested path not dead (path union)",
                    "concepts/nested" not in dead["items"])
        # CORRECTED: .raw/.pdf contributes its basename stem -> bare target NOT dead.
        assert_true("B67 raw .pdf basename makes bare target not dead",
                    "some-source" not in dead["items"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


# ===========================================================================
# Section 11 — corrected .raw-union behavior (fix-forward in run-lint.py)
# ===========================================================================
#
# LOCKED SEMANTICS: each in-glob (*.md/*.json/*.txt/*.pdf) file under <vault>/.raw
# contributes exactly ONE valid dead-link target = its BASENAME with the FINAL
# extension stripped, ASCII-lowercased. Basename only (subdir disambiguation is
# out of scope; same-stem files in different dirs collapse to one target). Files
# whose extension is NOT in the glob contribute nothing (documented limitation).
# run-lint.py DIVERGES from run-lint.sh for this one case (see B67).


def _raw_vault(raw_files, link_target, *, extra_pages=None):
    """Build a throwaway vault with a base index.md whose body links to
    `[[link_target]]`, plus the given .raw files. Returns the vault path; caller
    cleans up. `raw_files`: list of paths relative to <vault>/.raw.
    `extra_pages`: optional {wiki-relative path: body-after-frontmatter}."""
    v = new_tmp("raw-union.")
    _seed_base_vault(v)
    (v / "wiki" / "index.md").write_text(
        _fm("Index") + f"[[{link_target}]]\n"
    )
    for rel in raw_files:
        p = v / ".raw" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("")
    if extra_pages:
        for rel, body in extra_pages.items():
            p = v / "wiki" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(_fm(Path(rel).stem, "concept") + body)
    return v


def _is_dead(vault: Path, target_lower: str) -> bool:
    dead = rl.dead_link_targets(vault / "wiki", vault)
    return target_lower in dead


def test_section11_raw_core_pdf():
    # (a) .raw/foo.pdf + [[foo]] -> NOT dead (core)
    v = _raw_vault(["foo.pdf"], "foo")
    try:
        assert_true("S11a raw pdf core not dead", not _is_dead(v, "foo"))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_raw_all_globbed_exts():
    # (b) each of .raw/x.md, .raw/x.txt, .raw/x.json -> [[x]] NOT dead
    for ext in ("md", "txt", "json"):
        v = _raw_vault([f"x.{ext}"], "x")
        try:
            assert_true(f"S11b raw .{ext} not dead", not _is_dead(v, "x"))
        finally:
            shutil.rmtree(v, ignore_errors=True)


def test_section11_raw_case_insensitive():
    # (c) .raw/Foo.PDF -> [[foo]] NOT dead (ASCII-lowercased basename + ext)
    v = _raw_vault(["Foo.PDF"], "foo")
    try:
        assert_true("S11c raw Foo.PDF case-insensitive not dead",
                    not _is_dead(v, "foo"))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_raw_subdirectory_basename():
    # (d) .raw/sub/deep/foo.pdf -> [[foo]] NOT dead (basename match)
    v = _raw_vault(["sub/deep/foo.pdf"], "foo")
    try:
        assert_true("S11d raw nested basename not dead", not _is_dead(v, "foo"))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_raw_final_extension_only():
    # (e) .raw/foo.bar.pdf -> [[foo.bar]] NOT dead AND [[foo]] STILL dead.
    # Link BOTH targets so the dead set can actually contain "foo".
    v = new_tmp("raw-union-e.")
    try:
        _seed_base_vault(v)
        (v / ".raw").mkdir(parents=True)
        (v / ".raw" / "foo.bar.pdf").write_text("")
        (v / "wiki" / "index.md").write_text(
            _fm("Index") + "[[foo.bar]] [[foo]]\n"
        )
        dead = rl.dead_link_targets(v / "wiki", v)
        # only the final ext is stripped: raw target is "foo.bar", not "foo".
        assert_true("S11e raw foo.bar.pdf -> [[foo.bar]] not dead",
                    "foo.bar" not in dead)
        assert_true("S11e raw foo.bar.pdf -> [[foo]] still dead",
                    "foo" in dead)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_raw_spaces_in_stem():
    # (f) .raw/my source.pdf -> [[my source]] NOT dead (independent of the
    # spaced-wikilink check, which is a different check entirely).
    v = _raw_vault(["my source.pdf"], "my source")
    try:
        assert_true("S11f raw spaced stem not dead",
                    not _is_dead(v, "my source"))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_raw_glob_scope_unchanged():
    # (g) .raw/foo.png -> [[foo]] STILL dead (extension not in the glob)
    v = _raw_vault(["foo.png"], "foo")
    try:
        assert_true("S11g raw .png out-of-glob stays dead", _is_dead(v, "foo"))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_no_raw_dir_no_crash():
    # (h) no .raw dir -> no crash, link to nonexistent target still dead
    v = new_tmp("raw-union-none.")
    try:
        _seed_base_vault(v)
        (v / "wiki" / "index.md").write_text(_fm("Index") + "[[nope]]\n")
        assert_true("S11h no .raw dir: nonexistent target dead",
                    _is_dead(v, "nope"))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_genuinely_dead_regression():
    # (i) genuinely dead [[nonexistent]] (no page, no raw) -> STILL dead,
    # even with an unrelated raw file present.
    v = _raw_vault(["unrelated.pdf"], "nonexistent")
    try:
        assert_true("S11i genuinely dead stays dead", _is_dead(v, "nonexistent"))
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_valid_wiki_page_link_stays_valid():
    # (j) a normal valid wiki-page link stays valid; other checks unaffected.
    v = new_tmp("raw-union-page.")
    try:
        _seed_base_vault(v)
        (v / ".raw").mkdir(parents=True)
        (v / ".raw" / "src.pdf").write_text("")
        (v / "wiki" / "concepts").mkdir(parents=True)
        (v / "wiki" / "concepts" / "Real-Page.md").write_text(
            _fm("Real Page", "concept") + "Body.\n"
        )
        (v / "wiki" / "index.md").write_text(
            _fm("Index") + "[[Real-Page]] [[src]]\n"
        )
        summary = json_for(v)
        dead = check_by_name(summary, "dead_link_targets")
        assert_true("S11j real page link valid",
                    "real-page" not in dead["items"])
        assert_true("S11j raw src link valid", "src" not in dead["items"])
        assert_eq("S11j no dead links at all", 0, dead["count"])
        # other checks' counts unchanged from a clean base vault
        assert_eq("S11j spaced_filenames still 0", 0,
                  check_by_name(summary, "spaced_filenames")["count"])
        assert_eq("S11j frontmatter_gaps still 0", 0,
                  check_by_name(summary, "frontmatter_gaps")["count"])
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_dedup_collision():
    # (k) .raw/a.pdf + .raw/a.md collapse to a single target; [[a]] valid.
    # Accepted trade-off: two different sources sharing a stem mask each other
    # (and could mask a genuine typo), which the locked basename-only semantics
    # deliberately permit (subdir disambiguation is out of scope).
    v = _raw_vault(["a.pdf", "a.md"], "a")
    try:
        dead = rl.dead_link_targets(v / "wiki", v)
        assert_true("S11k collision: [[a]] valid", "a" not in dead)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_section11_integration_mixed_vault():
    # (l) integration: --json DEAD count and the Markdown report reflect the
    # corrected set on a vault mixing valid-page / raw / genuinely-dead links.
    v = new_tmp("raw-union-int.")
    try:
        _seed_base_vault(v)
        (v / ".raw").mkdir(parents=True)
        (v / ".raw" / "Report-2025.pdf").write_text("")  # -> report-2025
        (v / "wiki" / "concepts").mkdir(parents=True)
        (v / "wiki" / "concepts" / "Good.md").write_text(
            _fm("Good", "concept") + "Body.\n"
        )
        (v / "wiki" / "index.md").write_text(
            _fm("Index")
            + "[[Good]] [[Report-2025]] [[ghost]]\n"  # valid, raw, dead
        )
        # JSON view: exactly one dead target ('ghost')
        summary = json_for(v)
        dead = check_by_name(summary, "dead_link_targets")
        assert_eq("S11l json dead count == 1", 1, dead["count"])
        assert_eq("S11l json dead set == {ghost}", ["ghost"], dead["items"])
        # Markdown report reflects the same corrected set
        run_lint(v, "--quiet")
        date = datetime.date.today().isoformat()
        text = (v / "wiki" / "meta" / f"lint-report-{date}.md").read_text()
        assert_true("S11l report lists ghost as dead", "- ghost\n" in text)
        assert_true("S11l report omits report-2025 from dead",
                    "- report-2025\n" not in text)
        assert_true("S11l report omits good from dead", "- good\n" not in text)
    finally:
        shutil.rmtree(v, ignore_errors=True)


# ===========================================================================
# White-box unit tests (spec C.10): pure functions exposed by the port.
# ===========================================================================


def test_whitebox_ascii_lower():
    # tr 'A-Z' 'a-z' is ASCII-only; non-ASCII passes through (umlauts).
    assert_eq("WB ascii_lower ASCII", "abc-def", rl.ascii_lower("ABC-DEF"))
    assert_eq("WB ascii_lower umlaut passthrough", "kÜchen",
              rl.ascii_lower("KÜchen"))
    assert_true("WB ascii_lower != str.lower for umlaut",
                rl.ascii_lower("Ü") != "Ü".lower())


def test_whitebox_build_summary_severity():
    # build_summary severity sources: hardcoded, passthrough, flipped.
    base_raw = dict(
        spaced_filenames_items=[], spaced_links_items=[], orphans_items=[],
        dead_items=[], fm_gaps_items=[], title_items=[], title_count=0,
        term_err=0, term_warn=0,
        dag=dict(duplicates=0, missing_targets=0, cycles=0, ready_set=0,
                 task_count=0),
        prog=dict(unknown_codes=0, missing_home_pages=0, triage_tasks=0),
    )
    vp = Path("/v")
    wp = Path("/v/wiki")

    # spaced_filenames hardcoded error even with count>0
    raw = dict(base_raw, spaced_filenames_items=["x"])
    s = rl.build_summary("2026-01-01", vp, wp, 1, raw)
    sf = next(c for c in s["checks"] if c["name"] == "spaced_filenames")
    assert_eq("WB spaced_filenames hardcoded error", "error", sf["severity"])
    assert_eq("WB totals.error from spaced_filenames", 1, s["totals"]["error"])

    # terminology passthrough: error when term_err>0
    raw = dict(base_raw, term_err=1, term_warn=2)
    s = rl.build_summary("2026-01-01", vp, wp, 0, raw)
    term = next(c for c in s["checks"] if c["name"] == "terminology")
    assert_eq("WB terminology severity error (err>0)", "error", term["severity"])
    assert_eq("WB terminology count==err+warn", 3, term["count"])
    # totals split by subcounts, NOT by top-level severity
    assert_eq("WB totals.error from term errors", 1, s["totals"]["error"])
    assert_eq("WB totals.warn from term warns", 2, s["totals"]["warn"])

    # terminology warn when only warns
    raw = dict(base_raw, term_err=0, term_warn=2)
    s = rl.build_summary("2026-01-01", vp, wp, 0, raw)
    term = next(c for c in s["checks"] if c["name"] == "terminology")
    assert_eq("WB terminology severity warn (err==0)", "warn", term["severity"])

    # dag flips info->error on derived errors; counted into totals.error
    raw = dict(base_raw, dag=dict(duplicates=2, missing_targets=1, cycles=0,
                                  ready_set=0, task_count=5))
    s = rl.build_summary("2026-01-01", vp, wp, 0, raw)
    dag = next(c for c in s["checks"] if c["name"] == "research_queue_dag")
    assert_eq("WB dag severity flips to error", "error", dag["severity"])
    assert_eq("WB dag count == dup+missing+cycles", 3, dag["count"])
    assert_eq("WB dag counted into totals.error", 3, s["totals"]["error"])

    # dag info when clean (count 0 contributes nothing)
    raw = dict(base_raw, dag=dict(duplicates=0, missing_targets=0, cycles=0,
                                  ready_set=3, task_count=5))
    s = rl.build_summary("2026-01-01", vp, wp, 0, raw)
    dag = next(c for c in s["checks"] if c["name"] == "research_queue_dag")
    assert_eq("WB dag info when clean", "info", dag["severity"])
    assert_eq("WB dag count 0 when clean", 0, dag["count"])
    assert_eq("WB clean dag contributes nothing",
              {"error": 0, "warn": 0, "info": 0}, s["totals"])

    # program flips info->error on unknown+missing_pages
    raw = dict(base_raw, prog=dict(unknown_codes=1, missing_home_pages=2,
                                   triage_tasks=4))
    s = rl.build_summary("2026-01-01", vp, wp, 0, raw)
    prog = next(c for c in s["checks"] if c["name"] == "research_program_codes")
    assert_eq("WB program severity flips to error", "error", prog["severity"])
    assert_eq("WB program count == unknown+missing", 3, prog["count"])
    assert_eq("WB program counted into totals.error", 3, s["totals"]["error"])


def test_whitebox_value_types():
    raw = dict(
        spaced_filenames_items=[], spaced_links_items=[], orphans_items=[],
        dead_items=[], fm_gaps_items=[], title_items=[], title_count=0,
        term_err=0, term_warn=0,
        dag=dict(duplicates=0, missing_targets=0, cycles=0, ready_set=0,
                 task_count=0),
        prog=dict(unknown_codes=0, missing_home_pages=0, triage_tasks=0),
    )
    s = rl.build_summary("2026-01-01", Path("/v"), Path("/v/wiki"), 7, raw)
    assert_true("WB pages_scanned int", type(s["pages_scanned"]) is int)
    for c in s["checks"]:
        assert_true(f"WB {c['name']} count int", type(c["count"]) is int)


def test_whitebox_dead_link_pipeline():
    # dead_link_targets set algebra on a synthetic wiki.
    v = new_tmp("wb-dead.")
    try:
        wiki = v / "wiki"
        (wiki / "concepts").mkdir(parents=True)
        (wiki / "index.md").write_text(
            _fm("Index") + "[[Linked]] [[Missing]] [[concepts/Nested]]\n"
        )
        (wiki / "Linked.md").write_text(_fm("Linked"))
        (wiki / "concepts" / "Nested.md").write_text(_fm("Nested", "concept"))
        dead = rl.dead_link_targets(wiki, v)
        assert_true("WB dead: missing IS dead", "missing" in dead)
        assert_true("WB dead: linked NOT dead", "linked" not in dead)
        assert_true("WB dead: nested path NOT dead",
                    "concepts/nested" not in dead)
        assert_eq("WB dead: result sorted+unique", sorted(set(dead)), dead)
    finally:
        shutil.rmtree(v, ignore_errors=True)


def test_whitebox_spaced_filename_excludes_templates():
    v = new_tmp("wb-sf.")
    try:
        wiki = v / "wiki"
        (wiki / "_templates").mkdir(parents=True)
        (wiki / "concepts").mkdir(parents=True)
        (wiki / "concepts" / "Spaced One.md").write_text("x")
        (wiki / "_templates" / "has spaces.md").write_text("x")
        items = rl.find_spaced_filenames(wiki)
        assert_eq("WB spaced_filenames count 1 (template excluded)", 1, len(items))
        assert_true("WB spaced_filenames excludes _templates",
                    not any("_templates" in it for it in items))
    finally:
        shutil.rmtree(v, ignore_errors=True)


if __name__ == "__main__":
    try:
        # Black-box, seeded
        test_section1_json_seeded()
        test_section2_report_file()
        test_section3_missing_wiki()
        test_section4_schema()
        test_section5_severity_hardcoded()
        test_section5_terminology_passthrough_warn()
        test_section5_terminology_passthrough_error()
        test_section5_terminology_totals_split()
        test_section5_dag_flip_to_error()
        test_section5_dag_info_when_clean()
        test_section5_program_flip_to_error()
        test_section6_dag_absent_zeroed()
        test_section6_program_absent_zeroed()
        test_section6_dag_skipped_when_script_missing()
        test_section7_unknown_flag()
        test_section7_extra_positional()
        test_section7_help()
        test_section7_no_report_alias()
        test_section7_json_suppresses_report_and_summary()
        test_section7_quiet_writes_report_no_stdout()
        test_section7_default_mode()
        test_section7_json_and_quiet_json_wins()
        test_section7_positional_vault_arg()
        test_section7_env_overrides_positional()
        test_section8_report_frontmatter()
        test_section8_summary_table_all_checks()
        test_section8_machine_readable_json_block()
        test_section8_findings_truncation()
        test_section9_exit_0_with_findings()
        test_section9_read_only_no_mutation()
        test_section9_exit_2_message_on_missing_wiki()
        test_section10_empty_wiki_zero_findings()
        test_section10_templates_excluded_from_spaced_filenames()
        test_section10_meta_and_templates_excluded_from_spaced_links()
        test_section10_dead_link_respects_raw_and_paths()
        # Section 11 — corrected .raw-union (fix-forward)
        test_section11_raw_core_pdf()
        test_section11_raw_all_globbed_exts()
        test_section11_raw_case_insensitive()
        test_section11_raw_subdirectory_basename()
        test_section11_raw_final_extension_only()
        test_section11_raw_spaces_in_stem()
        test_section11_raw_glob_scope_unchanged()
        test_section11_no_raw_dir_no_crash()
        test_section11_genuinely_dead_regression()
        test_section11_valid_wiki_page_link_stays_valid()
        test_section11_dedup_collision()
        test_section11_integration_mixed_vault()
        # White-box
        test_whitebox_ascii_lower()
        test_whitebox_build_summary_severity()
        test_whitebox_value_types()
        test_whitebox_dead_link_pipeline()
        test_whitebox_spaced_filename_excludes_templates()
    except Fail as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    finally:
        if _SEEDED is not None:
            shutil.rmtree(_SEEDED, ignore_errors=True)
    print(f"\n{PASS} checks passed.\nAll tests passed.")
