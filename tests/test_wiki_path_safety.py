#!/usr/bin/env python3
"""Tests for hooks/wiki-path-safety.py - vault-detection guards, path/naming
rules, v1.10.0 mode dimension (strict/mixed), config bootstrap, NotebookEdit shape.

  Guard A: enforce only inside an actual vault (.vault-meta/ marker or KM_VAULT_PATH).
  Guard B: regulate only writes that resolve inside the vault root.
  Rule 1:  path whitelist for in-vault writes.
  Rule 2:  wiki/*.md filenames must be hyphenated; _templates and lint reports exempt.
  Modes:   strict (default) / mixed (PreToolUse JSON reminder for non-whitelist
           in-vault paths). .raw/ immutability and hyphenation stay hard in both.

Exit 0 = allow, exit 2 = block. Mixed-mode allow with reminder = exit 0 + stdout JSON.

Self-contained: no pytest dependency. Drives hooks/wiki-path-safety.py as a
subprocess, feeding the hook JSON on stdin.

Run: python3 tests/test_wiki_path_safety.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "wiki-path-safety.py"

PASS = 0
FAIL = 0

# Populated by run_capture / run_notebook.
EXIT = 0
STDOUT = ""
STDERR = ""


def ck(name: str, want: int, got: int) -> None:
    global PASS, FAIL
    if want == got:
        print(f"PASS {name} (exit {got})")
        PASS += 1
    else:
        print(f"FAIL {name}: want exit {want}, got {got}", file=sys.stderr)
        FAIL += 1


def ck_str(name: str, want: str, got: str) -> None:
    global PASS, FAIL
    if want == got:
        print(f"PASS {name} ({got})")
        PASS += 1
    else:
        print(f"FAIL {name}: want {want}, got {got}", file=sys.stderr)
        FAIL += 1


def ck_contains(name: str, substring: str, haystack: str) -> None:
    global PASS, FAIL
    if substring in haystack:
        print(f"PASS {name} (contains {substring})")
        PASS += 1
    else:
        print(
            f"FAIL {name}: {substring} not found (got: {haystack})",
            file=sys.stderr,
        )
        FAIL += 1


def _invoke(cwd: str, payload: dict, env_path: str | None = None):
    """Run the hook with payload on stdin; return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    env.pop("KM_VAULT_PATH", None)
    if env_path is not None:
        env["KM_VAULT_PATH"] = env_path
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run(cwd: str, fp: str, env_path: str | None = None) -> int:
    """run <cwd> <file_path> [KM_VAULT_PATH] -> returns exit code only."""
    rc, _, _ = _invoke(cwd, {"tool_input": {"file_path": fp}}, env_path)
    return rc


def run_capture(cwd: str, fp: str) -> None:
    """Populate globals EXIT, STDOUT, STDERR from a file_path write."""
    global EXIT, STDOUT, STDERR
    EXIT, STDOUT, STDERR = _invoke(cwd, {"tool_input": {"file_path": fp}})


def run_notebook(cwd: str, np: str) -> None:
    """Populate globals EXIT, STDOUT, STDERR from a notebook_path write.

    Mirrors the NotebookEdit tool input shape (no file_path).
    """
    global EXIT, STDOUT, STDERR
    EXIT, STDOUT, STDERR = _invoke(cwd, {"tool_input": {"notebook_path": np}})


def with_config(vault: str, mode: str) -> None:
    path = Path(vault, ".vault-meta", "config.json")
    path.write_text(json.dumps({"version": 1, "path_safety_mode": mode}))


def with_raw_config(vault: str, raw: str) -> None:
    Path(vault, ".vault-meta", "config.json").write_text(raw)


def rm_config(vault: str) -> None:
    cfg = Path(vault, ".vault-meta", "config.json")
    if cfg.exists():
        cfg.unlink()


def main() -> int:
    os.environ.pop("KM_VAULT_PATH", None)

    tmp_base = os.environ.get("TMPDIR", "/tmp")
    V = tempfile.mkdtemp(prefix="wps_vault.", dir=tmp_base)
    for sub in (
        ".vault-meta", "wiki/_templates", ".raw", "src", "scripts",
        "concepts", "docs",
    ):
        Path(V, sub).mkdir(parents=True, exist_ok=True)
    N = tempfile.mkdtemp(prefix="wps_plain.", dir=tmp_base)
    Path(N, "src").mkdir(parents=True, exist_ok=True)
    O = tempfile.mkdtemp(prefix="wps_other.", dir=tmp_base)
    Path(O, "src").mkdir(parents=True, exist_ok=True)
    # Canonicalize (pwd -P equivalent) so paths match the hook's resolve().
    V = str(Path(V).resolve())
    N = str(Path(N).resolve())
    O = str(Path(O).resolve())

    # Symlinked-vault fixture: SL is a logical symlink, SR its resolved target.
    # Exercises the resolve()-consistency fix — an absolute logical file_path
    # under a symlinked root must be canonicalized before the whitelist test, or
    # the strict block fails open (2026 security review regression).
    SR = str(Path(tempfile.mkdtemp(prefix="wps_symreal.", dir=tmp_base)).resolve())
    for sub in (".vault-meta", "wiki", ".raw"):
        Path(SR, sub).mkdir(parents=True, exist_ok=True)
    SL = os.path.join(tmp_base, "wps_symlink." + os.path.basename(SR))
    os.symlink(SR, SL)

    try:
        # Each section explicitly sets the mode it expects.
        with_config(V, "strict")

        # --- Guard A: vault detection ---
        ck("A1 non-vault src write allowed", 0, run(N, f"{N}/src/foo.ts"))
        ck("A2 non-vault arbitrary abs path", 0, run(N, "/etc/hosts"))
        ck("A3 vault detected, src blocked", 2, run(V, f"{V}/src/foo.ts"))

        # --- Guard B: KM_VAULT_PATH set, write lands outside the vault ---
        ck("B1 env-vault out-of-vault allow", 0, run(O, f"{O}/src/x.ts", V))
        ck("B2 env-vault in-vault src block", 2, run(O, f"{V}/src/x.ts", V))

        # --- Symlinked vault root (resolve() consistency / fail-open regression) ---
        with_config(SR, "strict")
        ck("S1 symlinked-root non-whitelist blocked", 2, run(SL, f"{SL}/secrets.txt", SL))
        ck("S2 symlinked-root .raw immutable", 2, run(SL, f"{SL}/.raw/source.md", SL))
        ck("S3 symlinked-root wiki page allowed", 0, run(SL, f"{SL}/wiki/page.md", SL))
        ck("S4 wiki/.. traversal collapses and blocks", 2, run(V, f"{V}/wiki/../secrets.txt"))

        # --- Rule 1: whitelist inside a real vault (strict) ---
        ck("R1 wiki page allowed", 0, run(V, f"{V}/wiki/page.md"))
        ck("R2 non-whitelisted src blocked", 2, run(V, f"{V}/src/foo.ts"))
        ck("R3 .raw source immutable", 2, run(V, f"{V}/.raw/source.md"))
        ck("R4 .raw/.manifest.json allowed", 0, run(V, f"{V}/.raw/.manifest.json"))
        ck("R5 CLAUDE.md allowed", 0, run(V, f"{V}/CLAUDE.md"))
        ck("R6 top-level concepts blocked", 2, run(V, f"{V}/concepts/x.md"))
        ck("R7 scripts allowed", 0, run(V, f"{V}/scripts/x.sh"))
        ck("R8 docs/ blocked in strict", 2, run(V, f"{V}/docs/foo.md"))

        # --- Rule 2: hyphenation ---
        ck("N1 hyphenated wiki name allowed", 0, run(V, f"{V}/wiki/good-name.md"))
        ck("N2 spaced wiki name blocked", 2, run(V, f"{V}/wiki/Bad Name.md"))
        ck(
            "N3 _templates spaced exempt", 0,
            run(V, f"{V}/wiki/_templates/Tpl With Space.md"),
        )

        # --- Edge ---
        rc, _, _ = _invoke(N, {"tool_input": {}})
        ck("E1 no file_path allowed", 0, rc)

        # --- Mode dimension: mixed ---
        with_config(V, "mixed")
        run_capture(V, f"{V}/wiki/page.md")
        ck("M1 mixed + wiki page exit", 0, EXIT)
        run_capture(V, f"{V}/src/foo.ts")
        ck("M2 mixed + non-wiki exit", 0, EXIT)
        ck_contains(
            "M2 reminder JSON has permissionDecision",
            '"permissionDecision": "allow"', STDOUT,
        )
        ck_contains("M2 reminder JSON has relative path", "src/foo.ts", STDOUT)
        ck_contains(
            "M2 reminder JSON has hookEventName",
            '"hookEventName": "PreToolUse"', STDOUT,
        )
        run_capture(V, f"{V}/.raw/source.md")
        ck("M3 mixed + .raw still blocks", 2, EXIT)
        ck_contains("M3 .raw stderr message", "immutable", STDERR)
        run_capture(V, f"{V}/wiki/Bad Name.md")
        ck("M4 mixed + spaced wiki name blocks", 2, EXIT)
        ck_contains("M4 hyphenation stderr", "hyphenated", STDERR)
        run_capture(V, f"{V}/concepts/x.md")
        ck("M5 mixed + concepts exit", 0, EXIT)
        ck_contains("M5 concepts reminder names path", "concepts/x.md", STDOUT)
        run_capture(V, f"{V}/docs/foo.md")
        ck("M6 mixed + docs exit", 0, EXIT)
        ck_contains("M6 docs reminder names path", "docs/foo.md", STDOUT)

        # --- NotebookEdit shape (notebook_path only, no file_path) ---
        with_config(V, "strict")
        run_notebook(V, f"{V}/src/nb.ipynb")
        ck("NB1 strict + notebook outside wiki blocks", 2, EXIT)
        with_config(V, "mixed")
        run_notebook(V, f"{V}/src/nb.ipynb")
        ck("NB2 mixed + notebook outside wiki allows", 0, EXIT)
        ck_contains("NB2 notebook reminder names path", "src/nb.ipynb", STDOUT)
        run_notebook(V, f"{V}/wiki/notebook.ipynb")
        ck("NB3 wiki notebook allowed", 0, EXIT)

        # --- Config bootstrap + malformed + unknown ---
        rm_config(V)
        run_capture(V, f"{V}/wiki/page.md")
        ck("C1 missing config bootstrap exit", 0, EXIT)
        boot = "present" if Path(V, ".vault-meta", "config.json").is_file() else "missing"
        ck_str("C1 missing config wrote file", "present", boot)
        ck_contains(
            "C1 bootstrap config has strict",
            '"path_safety_mode": "strict"',
            Path(V, ".vault-meta", "config.json").read_text(),
        )

        with_raw_config(V, "not json")
        run_capture(V, f"{V}/src/foo.ts")
        ck("C2 malformed JSON exits as strict", 2, EXIT)
        ck_contains("C2 stderr warns about unreadable", "config.json unreadable", STDERR)

        with_raw_config(V, '{"version": 99, "path_safety_mode": "mixed"}')
        run_capture(V, f"{V}/src/foo.ts")
        ck("C3 unknown version exits as strict", 2, EXIT)
        ck_contains("C3 stderr warns about unknown version", "unknown version", STDERR)

        with_raw_config(V, '{"version": 1, "path_safety_mode": "unknown"}')
        run_capture(V, f"{V}/src/foo.ts")
        ck("C4 unknown mode exits as strict", 2, EXIT)
        ck_contains("C4 stderr warns about unknown mode", "unknown path_safety_mode", STDERR)
    finally:
        for d in (V, N, O, SR):
            shutil.rmtree(d, ignore_errors=True)
        if os.path.islink(SL):
            os.unlink(SL)

    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
