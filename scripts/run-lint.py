#!/usr/bin/env python3
"""run-lint.py — canonical wiki-quality lint aggregator (Python port of run-lint.sh).

Runs every deterministic check the plugin ships, emits a JSON summary with
per-check severity, and writes a Markdown report to
<vault>/wiki/meta/lint-report-YYYY-MM-DD.md. Read-only; never mutates wiki
content.

Resolution order for the vault root (via lib/vault_root.py):
    KM_VAULT_PATH (env)  ->  positional argument  ->  current working directory

Usage:
  scripts/run-lint.py                       # write report + print summary
  scripts/run-lint.py /path/to/vault        # explicit vault root
  scripts/run-lint.py --json                # JSON only, no report file, no stdout noise
  scripts/run-lint.py --quiet               # write report, no stdout
  scripts/run-lint.py --no-report           # JSON to stdout, no report file (alias for --json)

Exit codes:
  0  always (read-only — exit code does NOT reflect findings; downstream
     tooling (CI, pre-commit) inspects the JSON severity totals instead).
  2  on usage / resolver error.

Severity defaults (hardcoded for PR1; PR1.5+ may make this configurable):
  error  spaced_filenames, spaced_wikilinks_body, terminology(ERROR)
  warn   orphans, dead_link_targets, frontmatter_gaps, terminology(WARN)
  info   title_overlap

This is a behavioral port of scripts/run-lint.sh. The sub-script checks
(orphans, terminology, title-overlap, dag, programs) are invoked as the same
subprocesses the shell script calls, so their results stay byte-identical. The
inline shell/awk/grep/sed checks (spaced filenames, spaced wikilinks, dead-link
targets, frontmatter gaps) are reproduced natively in Python.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

sys.path.insert(0, str(REPO_ROOT / "lib"))
from vault_root import resolve_vault_root  # noqa: E402

EXIT_USAGE = 2

# Wikilink ERE used by the shell (grep -rEho '\[\[[^]]+\]\]').
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
# Required frontmatter keys for the frontmatter_gaps check.
REQUIRED_FM = ["type", "title", "created", "updated", "status"]


# --- helpers ---------------------------------------------------------------


def ascii_lower(s: str) -> str:
    """ASCII-only lowercasing, matching `tr 'A-Z' 'a-z'`.

    The shell dead-link pipeline lowercases with `tr` (ASCII range only),
    NOT a Unicode-aware fold. Non-ASCII characters (e.g. umlauts) pass
    through unchanged. Reproducing this exactly preserves which links count
    as dead. Do NOT use str.lower() here.
    """
    out = []
    for ch in s:
        o = ord(ch)
        if 65 <= o <= 90:  # 'A'..'Z'
            out.append(chr(o + 32))
        else:
            out.append(ch)
    return "".join(out)


def head_lines(path: Path, n: int = 30) -> list[str]:
    """First n lines of a file with trailing newline stripped (mirrors the
    shell's head_lines: reads up to n records, rstrip('\\n'))."""
    if not path.is_file():
        return []
    out: list[str] = []
    with path.open(encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            out.append(line.rstrip("\n"))
    return out


# --- inline checks (native Python ports of the shell inline blocks) --------


def find_spaced_filenames(wiki_root: Path) -> list[str]:
    """find "$WIKI_ROOT" -type f -name '* *.md' ! -path "$WIKI_ROOT/_templates/*"

    Files whose basename contains a space and ends in .md, excluding anything
    under the _templates/ directory (ONLY _templates — NOT meta).
    """
    templates_dir = wiki_root / "_templates"
    results: list[str] = []
    for p in wiki_root.rglob("*.md"):
        if not p.is_file():
            continue
        if " " not in p.name:
            continue
        # ! -path "$WIKI_ROOT/_templates/*"
        try:
            p.relative_to(templates_dir)
            continue  # inside _templates -> excluded
        except ValueError:
            pass
        results.append(str(p))
    results.sort()
    return results


def find_spaced_wikilinks_body(wiki_root: Path) -> list[str]:
    """Reproduce the inline python walk (run-lint.sh lines 90-108):

    Walk the wiki, skipping any directory path component named _templates or
    meta. For each .md file, scan lines for [[target]] wikilinks; strip the
    alias/anchor (split on first '|' or '#'), strip surrounding whitespace,
    and emit "<path>:<lineno>: <full-match>" when the target contains a space.
    """
    results: list[str] = []
    for root, _dirs, files in os.walk(wiki_root):
        parts = root.split(os.sep)
        if "_templates" in parts or "meta" in parts:
            continue
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(root, fn)
            with open(p, encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    for m in LINK_RE.finditer(line):
                        target = re.split(r"[|#]", m.group(1), maxsplit=1)[0].strip()
                        if " " in target:
                            results.append(f"{p}:{i}: {m.group(0)}")
    return results


def find_frontmatter_gaps(wiki_root: Path) -> list[str]:
    """Reproduce the inline python walk (run-lint.sh lines 139-160):

    For each .md file, read the first 30 lines. If the head does not start
    with '---', emit the path. Otherwise emit "<path>\\t<missing,keys>" for
    any required key not present as a "<key>:" line prefix. Note: os.walk
    order (NOT sorted) — matches the shell which does not sort this list.
    """
    results: list[str] = []
    for root, _dirs, files in os.walk(wiki_root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(root, fn)
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    head = "".join(f.readline() for _ in range(30))
            except OSError:
                continue
            if not head.startswith("---"):
                results.append(p)
                continue
            lines = head.splitlines()
            missing = [
                k for k in REQUIRED_FM
                if not any(L.startswith(k + ":") for L in lines)
            ]
            if missing:
                results.append(f"{p}\t{','.join(missing)}")
    return results


def dead_link_targets(wiki_root: Path, vault_root: Path) -> list[str]:
    """Reproduce the dead-link set algebra (run-lint.sh lines 119-135).

    1. links: every [[...]] target across the wiki, alias/anchor stripped,
       trailing .md stripped, ASCII-lowercased, unique-sorted.
    2. valid set = union of:
         - basenames: every *.md path's basename, .md stripped, ASCII-lower
         - paths:     every wiki-relative slash path, .md stripped, ASCII-lower
         - raw:       if <vault>/.raw exists, basenames of *.md/*.json/*.txt/
                      *.pdf, .md stripped (others keep their extension),
                      ASCII-lower
    3. dead = links - valid  (comm -23), returned sorted.

    The grep/sed pipeline lowercases with `tr` (ASCII only) — see ascii_lower.
    """
    # --- links.txt ---
    link_alias_re = re.compile(r"\[\[([^|#]+)(?:[|#][^\]]*)?\]\]")
    md_suffix_re = re.compile(r"\.md$")
    links: set[str] = set()
    # grep -rEho '\[\[[^]]+\]\]' descends ALL files under wiki (grep -r),
    # not just .md, then sed strips alias/anchor and a trailing .md.
    for root, _dirs, files in os.walk(wiki_root):
        for fn in files:
            fp = os.path.join(root, fn)
            try:
                with open(fp, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            for m in LINK_RE.finditer(text):
                whole = m.group(0)  # '[[...]]'
                sm = link_alias_re.match(whole)
                if not sm:
                    continue
                target = sm.group(1)
                target = md_suffix_re.sub("", target)
                links.add(ascii_lower(target))

    # --- basenames.txt: awk -F/ '{f=$NF; sub(/.md$/,"",f); print tolower(f)}' ---
    basenames: set[str] = set()
    paths: set[str] = set()
    for p in wiki_root.rglob("*.md"):
        if not p.is_file():
            continue
        basenames.add(ascii_lower(md_suffix_re.sub("", p.name)))
        rel = p.relative_to(wiki_root).as_posix()
        rel = md_suffix_re.sub("", rel)
        paths.add(ascii_lower(rel))

    # --- raw.txt ---
    # The shell pipeline is:
    #   find "$VAULT_ROOT/.raw" -type f \( -name '*.md' -o -name '*.json'
    #     -o -name '*.txt' -o -name '*.pdf' \) | sed 's|\.md$||' | tr A-Z a-z
    # find prints the FULL path; `sed` strips only a trailing `.md` from that
    # full path (NOT a basename, and NOT other extensions). So a .pdf/.json/.txt
    # raw file keeps its extension, and a .md raw file keeps its directory
    # prefix. The valid-set entry is therefore the full lowercased path — which
    # bare link targets effectively never match. Reproduce that EXACTLY (using
    # the absolute path, the same string `find "$VAULT_ROOT/.raw"` would emit).
    raw: set[str] = set()
    raw_dir = vault_root / ".raw"
    if raw_dir.is_dir():
        for p in raw_dir.rglob("*"):
            if not p.is_file():
                continue
            # `find -name` matches on the basename's glob; restrict to the four
            # extensions. p.suffix is case-sensitive like find's glob on a
            # case-sensitive FS; the shell uses lowercase patterns only.
            if p.suffix not in (".md", ".json", ".txt", ".pdf"):
                continue
            full = md_suffix_re.sub("", str(p))
            raw.add(ascii_lower(full))

    valid = basenames | paths | raw
    dead = sorted(links - valid)
    return dead


# --- sub-script invocation (faithful subprocess calls) ---------------------


def _run_capture(args: list[str], vault_root: Path) -> tuple[int, str]:
    """Run a sub-script with KM_VAULT_PATH set, capturing stdout. stderr is
    discarded (the shell redirects 2>/dev/null on these). Never raises on a
    non-zero exit (the shell tolerates them with || true / : )."""
    env = dict(os.environ)
    env["KM_VAULT_PATH"] = str(vault_root)
    try:
        proc = subprocess.run(
            args, capture_output=True, text=True, env=env,
        )
    except OSError:
        return (127, "")
    return (proc.returncode, proc.stdout)


def run_orphans(vault_root: Path) -> str:
    """KM_VAULT_PATH=<vault> python3 lint-orphans.py  (|| true). Plain stdout,
    one path per line."""
    _rc, out = _run_capture(
        [sys.executable, str(SCRIPT_DIR / "lint-orphans.py")], vault_root
    )
    return out


def run_terminology(vault_root: Path) -> tuple[int, int]:
    """Gated on the executable bit of lint-terminology.py ([ -x ]). Returns
    (TERM_ERR, TERM_WARN), counting ERROR/WARN findings in the --json list.
    Any failure defaults to (0, 0)."""
    script = SCRIPT_DIR / "lint-terminology.py"
    if not (script.is_file() and os.access(script, os.X_OK)):
        return (0, 0)
    _rc, out = _run_capture(
        [sys.executable, str(script), "--json"], vault_root
    )
    if not out.strip():
        return (0, 0)
    try:
        data = json.loads(out)
    except Exception:
        return (0, 0)
    if not isinstance(data, list):
        return (0, 0)
    err = sum(
        1 for f in data if isinstance(f, dict) and f.get("severity") == "ERROR"
    )
    warn = sum(
        1 for f in data if isinstance(f, dict) and f.get("severity") == "WARN"
    )
    return (err, warn)


def run_title_overlap(vault_root: Path) -> tuple[int, str]:
    """Gated on the executable bit of lint-title-overlap.py ([ -x ]). Returns
    (count, raw_stdout). count = number of lines beginning with a digit
    (awk '/^[0-9]/{n++}'). raw_stdout feeds head_lines for the items list."""
    script = SCRIPT_DIR / "lint-title-overlap.py"
    if not (script.is_file() and os.access(script, os.X_OK)):
        return (0, "")
    _rc, out = _run_capture([sys.executable, str(script)], vault_root)
    count = 0
    for line in out.splitlines():
        if line[:1].isdigit():
            count += 1
    return (count, out)


def run_dag(wiki_root: Path, vault_root: Path) -> dict[str, int]:
    """Gated on existence ([ -f ]) of wiki/meta/research-queue.md AND
    lint-deps.py. Returns dict of derived counts; all 0 when gated out or on
    any parse failure (the shell defaults every count to 0)."""
    zero = {
        "duplicates": 0, "missing_targets": 0, "cycles": 0,
        "ready_set": 0, "task_count": 0,
    }
    queue = wiki_root / "meta" / "research-queue.md"
    script = SCRIPT_DIR / "lint-deps.py"
    if not (queue.is_file() and script.is_file()):
        return dict(zero)
    _rc, out = _run_capture(
        [sys.executable, str(script), "--vault", str(vault_root), "--json"],
        vault_root,
    )
    if not out.strip():
        return dict(zero)
    try:
        d = json.loads(out)
    except Exception:
        return dict(zero)
    if not isinstance(d, dict):
        return dict(zero)
    return {
        "task_count": int(d.get("task_count", 0)),
        "duplicates": len(d.get("duplicates", [])),
        "missing_targets": len(d.get("missing_targets", [])),
        "cycles": len(d.get("cycles", [])),
        "ready_set": len(d.get("ready_set", [])),
    }


def run_programs(wiki_root: Path, vault_root: Path) -> dict[str, int]:
    """Gated on existence ([ -f ]) of wiki/meta/research-queue.md AND
    wiki/decisions/Research-Program-Codes.md AND lint-programs.py. Returns
    dict of derived counts; all 0 when gated out or on any parse failure."""
    zero = {"unknown_codes": 0, "missing_home_pages": 0, "triage_tasks": 0}
    queue = wiki_root / "meta" / "research-queue.md"
    decision = wiki_root / "decisions" / "Research-Program-Codes.md"
    script = SCRIPT_DIR / "lint-programs.py"
    if not (queue.is_file() and decision.is_file() and script.is_file()):
        return dict(zero)
    _rc, out = _run_capture(
        [sys.executable, str(script), "--vault", str(vault_root), "--json"],
        vault_root,
    )
    if not out.strip():
        return dict(zero)
    try:
        d = json.loads(out)
    except Exception:
        return dict(zero)
    if not isinstance(d, dict):
        return dict(zero)
    return {
        "unknown_codes": len(d.get("unknown_codes", [])),
        "missing_home_pages": len(d.get("missing_home_pages", [])),
        "triage_tasks": len(d.get("triage_tasks", [])),
    }


# --- summary assembly ------------------------------------------------------


def build_summary(date: str, vault_root: Path, wiki_root: Path,
                  pages_scanned: int, raw: dict) -> dict:
    """Assemble the summary object (mirrors run-lint.sh lines 288-358).

    `raw` carries the per-check primitives:
      spaced_filenames_items, spaced_links_items, orphans_items,
      dead_items, fm_gaps_items, title_items (lists of str),
      term_err, term_warn (int),
      title_count (int),
      dag (dict), prog (dict).

    Severity sources preserved exactly:
      - checks 1-5, 7: hardcoded literal.
      - terminology: error if term_err>0 else warn (top-level), totals split
        by errors/warns sub-counts.
      - dag/programs: info, flipped to error when derived error-count > 0.
    """
    term_err = int(raw["term_err"])
    term_warn = int(raw["term_warn"])
    dag = raw["dag"]
    prog = raw["prog"]
    dag_errors = (
        int(dag["duplicates"]) + int(dag["missing_targets"]) + int(dag["cycles"])
    )
    prog_errors = (
        int(prog["unknown_codes"]) + int(prog["missing_home_pages"])
    )

    checks = [
        {"name": "spaced_filenames", "severity": "error",
         "count": len(raw["spaced_filenames_items"]),
         "items": raw["spaced_filenames_items"][:30]},
        {"name": "spaced_wikilinks_body", "severity": "error",
         "count": len(raw["spaced_links_items"]),
         "items": raw["spaced_links_items"][:30]},
        {"name": "orphans", "severity": "warn",
         "count": len(raw["orphans_items"]),
         "items": raw["orphans_items"][:30]},
        {"name": "dead_link_targets", "severity": "warn",
         "count": len(raw["dead_items"]),
         "items": raw["dead_items"][:30]},
        {"name": "frontmatter_gaps", "severity": "warn",
         "count": len(raw["fm_gaps_items"]),
         "items": raw["fm_gaps_items"][:30]},
        {"name": "terminology",
         "severity": "error" if term_err > 0 else "warn",
         "count": term_err + term_warn,
         "errors": term_err,
         "warns": term_warn,
         "items": []},
        {"name": "title_overlap", "severity": "info",
         "count": int(raw["title_count"]),
         "items": raw["title_items"][:30]},
        {"name": "research_queue_dag",
         "severity": "error" if dag_errors > 0 else "info",
         "count": dag_errors,
         "duplicates": int(dag["duplicates"]),
         "missing_targets": int(dag["missing_targets"]),
         "cycles": int(dag["cycles"]),
         "ready_set": int(dag["ready_set"]),
         "task_count": int(dag["task_count"]),
         "items": []},
        {"name": "research_program_codes",
         "severity": "error" if prog_errors > 0 else "info",
         "count": prog_errors,
         "unknown_codes": int(prog["unknown_codes"]),
         "missing_home_pages": int(prog["missing_home_pages"]),
         "triage_tasks": int(prog["triage_tasks"]),
         "items": []},
    ]

    totals = {"error": 0, "warn": 0, "info": 0}
    for c in checks:
        if c.get("count", 0) <= 0:
            continue
        if c["name"] == "terminology":
            totals["error"] += c.get("errors", 0)
            totals["warn"] += c.get("warns", 0)
        elif c["name"] in ("research_queue_dag", "research_program_codes"):
            # severity already flipped to "error" when count > 0
            totals[c["severity"]] += c["count"]
        else:
            totals[c["severity"]] += c["count"]

    return {
        "date": date,
        "vault_root": str(vault_root),
        "wiki_root": str(wiki_root),
        "pages_scanned": int(pages_scanned),
        "checks": checks,
        "totals": totals,
    }


def render_report(summary: dict, date: str) -> str:
    """Render the Markdown report body (mirrors run-lint.sh lines 373-404)."""
    parts: list[str] = []
    parts.append(
        "---\n"
        "type: meta\n"
        f'title: "Lint Report {date}"\n'
        f"created: {date}\n"
        f"updated: {date}\n"
        "tags:\n"
        "  - meta\n"
        "  - lint\n"
        "status: developing\n"
        "---\n\n"
    )
    parts.append(f"# Lint Report: {date}\n\n")

    parts.append("## Summary\n\n| Check | Severity | Count |\n|---|---|---|\n")
    for c in summary["checks"]:
        parts.append(f"| {c['name']} | {c['severity']} | {c['count']} |\n")
    parts.append("\n")
    t = summary["totals"]
    parts.append(
        f"**Totals:** error={t['error']}  warn={t['warn']}  info={t['info']}  "
        f"(pages scanned: {summary['pages_scanned']})\n"
    )

    parts.append("\n## Findings\n\n")
    for c in summary["checks"]:
        if c["count"] <= 0:
            continue
        parts.append(
            f"### {c['name']} (severity={c['severity']}, count={c['count']})\n"
        )
        parts.append("\n")
        items = c.get("items", [])
        for it in items[:30]:
            parts.append(f"- {it}\n")
        if c["count"] > len(items):
            parts.append(f"- … {c['count'] - len(items)} more\n")
        parts.append("\n")

    parts.append("## Machine-readable summary\n\n```json\n")
    # The shell writes summary.json via `print(json.dumps(...))` (adds a
    # trailing newline), then `cat`s it and appends `printf '\n```\n'` —
    # yielding `}\n\n```\n` (a blank line before the closing fence). Match it.
    parts.append(json.dumps(summary, indent=2, ensure_ascii=False))
    parts.append("\n\n```\n")
    return "".join(parts)


# --- CLI -------------------------------------------------------------------


def print_help() -> None:
    """Print the header doc block (lines 1-30 of this file) to stderr.

    The shell does `sed -n '1,30p' "$0" | sed 's|^# \\?||'`. Part D landmine #5:
    that second sed is a GNU-vs-BSD divergence. On macOS (BSD sed, this repo's
    target machine) `\\?` is a LITERAL '?', so the pattern `^# ?` matches
    nothing and the substitution is a NO-OP — `run-lint.sh --help` prints lines
    1-30 VERBATIM with the leading '#' comment markers intact (verified against
    the live .sh on macOS). We reproduce the observed BSD content: print the
    first 30 source lines unmodified. (Spec Part D #5: reproduce the help
    *content*, not the sed mechanics.)
    """
    src = Path(__file__).read_text(encoding="utf-8", errors="ignore")
    for line in src.splitlines()[:30]:
        print(line, file=sys.stderr)


def parse_args(argv: list[str]) -> tuple[int, int, str]:
    """Parse argv the way the shell `for arg in "$@"` loop does (order-
    independent). Returns (json_only, quiet, positional). May raise SystemExit
    (code 0 for --help, code 2 for unknown flag / extra positional)."""
    json_only = 0
    quiet = 0
    positional = ""
    for arg in argv:
        if arg in ("--json", "--no-report"):
            json_only = 1
        elif arg == "--quiet":
            quiet = 1
        elif arg in ("--help", "-h"):
            print_help()
            raise SystemExit(0)
        elif arg.startswith("-"):
            print(f"run-lint: unknown flag {arg}", file=sys.stderr)
            raise SystemExit(EXIT_USAGE)
        else:
            if not positional:
                positional = arg
            else:
                print(
                    f"run-lint: extra positional argument {arg}",
                    file=sys.stderr,
                )
                raise SystemExit(EXIT_USAGE)
    return (json_only, quiet, positional)


def main(argv: list[str]) -> int:
    json_only, quiet, positional = parse_args(argv)

    vault_root = resolve_vault_root(positional or None)
    wiki_root = vault_root / "wiki"

    if not wiki_root.is_dir():
        print(
            f"run-lint: wiki root {wiki_root} is not a directory",
            file=sys.stderr,
        )
        return EXIT_USAGE

    date = datetime.date.today().isoformat()
    tmp = Path(tempfile.mkdtemp(prefix="run-lint."))
    try:
        # --- inventory ---
        all_md = [p for p in wiki_root.rglob("*.md") if p.is_file()]
        total_pages = len(all_md)

        # --- inline checks ---
        spaced_filenames_items = find_spaced_filenames(wiki_root)
        spaced_links_items = find_spaced_wikilinks_body(wiki_root)
        dead_items = dead_link_targets(wiki_root, vault_root)
        fm_gaps_items = find_frontmatter_gaps(wiki_root)

        # --- sub-script checks ---
        orphans_out = run_orphans(vault_root)
        orphans_items = orphans_out.splitlines() if orphans_out else []
        # The shell counts orphans via `wc -l`; reproduce record semantics.
        # splitlines() drops a trailing newline so len() == record count.

        term_err, term_warn = run_terminology(vault_root)
        title_count, title_out = run_title_overlap(vault_root)
        title_items = title_out.splitlines() if title_out else []

        dag = run_dag(wiki_root, vault_root)
        prog = run_programs(wiki_root, vault_root)

        raw = {
            "spaced_filenames_items": spaced_filenames_items,
            "spaced_links_items": spaced_links_items,
            "orphans_items": orphans_items,
            "dead_items": dead_items,
            "fm_gaps_items": fm_gaps_items,
            "title_items": title_items,
            "title_count": title_count,
            "term_err": term_err,
            "term_warn": term_warn,
            "dag": dag,
            "prog": prog,
        }

        summary = build_summary(
            date, vault_root, wiki_root, total_pages, raw
        )
        summary_json = json.dumps(summary, indent=2, ensure_ascii=False)

        # --- output ---
        if json_only:
            print(summary_json)
            return 0

        report_dir = wiki_root / "meta"
        report = report_dir / f"lint-report-{date}.md"
        report_dir.mkdir(parents=True, exist_ok=True)
        report.write_text(render_report(summary, date), encoding="utf-8")

        if quiet == 0:
            print(f"Lint report: {report}")
            t = summary["totals"]
            print(
                f"Totals: error={t['error']}  warn={t['warn']}  "
                f"info={t['info']}  pages={summary['pages_scanned']}"
            )
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
