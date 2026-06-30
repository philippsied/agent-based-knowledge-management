#!/usr/bin/env python3
"""Vault write-safety hook. Deterministic enforcement of two rules:

  1. Path whitelist: writes only into wiki/, scripts/, .vault-meta/,
     .claude/, $TMPDIR, plus CLAUDE.md / README.md / .gitignore /
     .gitattributes / .raw/.manifest.json (relative to the resolved
     vault root).
  2. Naming convention: wiki/*.md filenames must NOT contain spaces
     (use hyphenated Title-Case). _templates/ and lint reports are
     exempt.

Wire as a PreToolUse hook for Write|Edit|NotebookEdit. The hook reads
the tool-input JSON from stdin and exits 2 with a message on stderr to
block, or exits 0 to allow.

Vault root resolution (matches lib/vault_root.py):
  KM_VAULT_PATH (env)  ->  current working directory

Rationale: A 2026-05-19 batch ingest produced 588 wikilink rewrites and
11 misplaced files because the same conventions were enforced only by
prompt. This hook makes them deterministic.

Stdlib-only and import-light: this runs on every Write/Edit/NotebookEdit,
so the module top stays free of heavy imports to keep cold start low.
"""

import json
import os
import sys
from pathlib import Path

# Import the shared vault-root resolver (single source of truth).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from vault_root import resolve_vault_root  # noqa: E402


def _read_file_path(raw: str) -> str:
    """Extract file_path (or notebook_path) from the hook JSON; '' on any error."""
    try:
        d = json.loads(raw)
        ti = d.get("tool_input", {})
        return ti.get("file_path") or ti.get("notebook_path", "") or ""
    except Exception:
        return ""


def _resolve_mode(config_file: Path) -> str:
    """Read path_safety_mode from config.json, falling back to strict.

    Mirrors the shell validation ladder: unreadable / unknown version /
    unknown mode each emit a stderr warning and return 'strict'.
    """
    try:
        with open(config_file) as fh:
            data = json.load(fh)
    except Exception:
        sys.stderr.write(
            "wiki-path-safety: config.json unreadable; falling back to strict\n"
        )
        return "strict"
    if data.get("version") != 1:
        sys.stderr.write(
            "wiki-path-safety: config.json unknown version; falling back to strict\n"
        )
        return "strict"
    mode = data.get("path_safety_mode")
    if mode not in ("strict", "mixed"):
        sys.stderr.write(
            "wiki-path-safety: config.json unknown path_safety_mode; "
            "falling back to strict\n"
        )
        return "strict"
    return mode


def _is_under(abs_path: str, root: str) -> bool:
    """True iff abs_path is strictly under root/ (shell `case "$root"/*`)."""
    return abs_path.startswith(root + "/")


def main() -> int:
    raw = sys.stdin.read()
    file_path = _read_file_path(raw)

    if not file_path:
        return 0  # No file_path — let the tool decide.

    # Resolve vault root: env override -> CWD. Mirrors lib/vault_root.py order.
    vault_root = str(resolve_vault_root())

    # ---------- Guard A: only enforce inside an actual vault ----------
    # The plugin may be installed at user scope, so this hook fires in EVERY
    # session, including unrelated repos. A non-vault repo has no .vault-meta/
    # marker and no KM_VAULT_PATH; pass it through untouched.
    if not Path(vault_root, ".vault-meta").is_dir() and not os.environ.get(
        "KM_VAULT_PATH"
    ):
        return 0

    # ---------- Config: resolve path-safety mode ----------
    # Single source: .vault-meta/config.json. No env override.
    # Bootstrap is idempotent and silent: vaults predating v1.10.0 get a strict
    # config on the next hook fire so the read path has no missing-file branch.
    config_file = Path(vault_root, ".vault-meta", "config.json")
    if not config_file.is_file():
        config_file.write_text(
            '{\n  "version": 1,\n  "path_safety_mode": "strict"\n}\n'
        )

    mode = _resolve_mode(config_file)

    if file_path.startswith("/"):
        abs_path = file_path
    else:
        abs_path = vault_root + "/" + file_path

    # Canonicalize the candidate the SAME way resolve_vault_root() canonicalizes
    # the root (Path.resolve follows symlinks). Without this, an absolute logical
    # file_path under a symlinked root — e.g. /tmp/vault/secrets.txt where the
    # real root is /private/tmp/vault — fails every `_is_under` prefix check, so
    # Guard B passes it through (exit 0): a fail-open bypass of the strict block.
    # Resolving both sides keeps the comparison consistent and also collapses
    # `..` traversal before the whitelist test.
    abs_path = str(Path(abs_path).resolve())

    # ---------- Guard B: only regulate writes inside the resolved vault root ----
    # Out-of-vault writes are not this hook's concern (e.g. KM_VAULT_PATH points
    # at the vault while you work in another repo). Let them pass.
    if not _is_under(abs_path, vault_root):
        return 0

    # ---------- Rule 1: path whitelist ----------
    # Two-pass check so the $TMPDIR / /tmp carve-out only applies to paths that
    # are NOT under the resolved vault (otherwise a vault placed under /tmp —
    # common in test setups — would silently pass every block).
    under_vault = 1 if _is_under(abs_path, vault_root) else 0

    allowed = 0
    if _is_under(abs_path, vault_root + "/wiki"):
        allowed = 1
    elif abs_path == vault_root + "/.raw/.manifest.json":
        allowed = 1
    elif _is_under(abs_path, vault_root + "/scripts"):
        allowed = 1
    elif _is_under(abs_path, vault_root + "/.vault-meta"):
        allowed = 1
    elif _is_under(abs_path, vault_root + "/.claude"):
        allowed = 1
    elif abs_path == vault_root + "/CLAUDE.md":
        allowed = 1
    elif abs_path == vault_root + "/README.md":
        allowed = 1
    elif abs_path == vault_root + "/.gitignore":
        allowed = 1
    elif abs_path == vault_root + "/.gitattributes":
        allowed = 1

    if under_vault == 0 and allowed != 1:
        if abs_path.startswith("/tmp/") or abs_path.startswith("/private/tmp/"):
            allowed = 1
        # Match TMPDIR prefix (TMPDIR may be empty in some contexts)
        tmpdir = os.environ.get("TMPDIR", "")
        if tmpdir and abs_path.startswith(tmpdir):
            allowed = 1

    if allowed != 1:
        # ---------- Rule 1a: .raw/ immutability (hard in both modes) ----------
        if _is_under(abs_path, vault_root + "/.raw"):
            sys.stderr.write(
                "BLOCKED: .raw/ source files are immutable. "
                "Only .raw/.manifest.json is writable.\n"
            )
            sys.stderr.write("Attempted path: " + abs_path + "\n")
            sys.stderr.write("Vault root:     " + vault_root + "\n")
            return 2

        # ---------- Mixed mode: model-visible reminder, allow the write -------
        if mode == "mixed":
            rel = abs_path[len(vault_root + "/"):]
            msg = (
                "Mixed-mode vault: writing `" + rel + "` outside the wiki "
                "whitelist (wiki/, scripts/, .vault-meta/, .claude/, root "
                "CLAUDE.md|README.md|.gitignore|.gitattributes, "
                ".raw/.manifest.json). Write ALLOWED. "
                "If this is non-wiki work (code, tests, build), proceed. "
                "If you meant a wiki page, move it under wiki/."
            )
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "additionalContext": msg,
                }
            }
            print(json.dumps(out))
            return 0

        # ---------- Strict mode: block ----------
        wiki_dirs = (
            "/concepts/", "/entities/", "/sources/", "/people/",
            "/research/", "/learning/", "/domains/",
        )
        rel_from_root = abs_path[len(vault_root):]
        if any(rel_from_root.startswith(d) for d in wiki_dirs):
            sys.stderr.write(
                "BLOCKED: wiki content must live under wiki/. Did you mean "
                "wiki" + rel_from_root + "?\n"
            )
        else:
            sys.stderr.write(
                "BLOCKED: vault path-safety: writes only allowed under wiki/, "
                "scripts/, .vault-meta/, .claude/, $TMPDIR, or CLAUDE.md / "
                "README.md / .gitignore / .gitattributes / "
                ".raw/.manifest.json.\n"
            )
        sys.stderr.write("Attempted path: " + abs_path + "\n")
        sys.stderr.write("Vault root:     " + vault_root + "\n")
        return 2

    # ---------- Rule 2: naming convention for wiki/*.md ----------
    # Only enforce on wiki/ markdown files; templates and lint reports are exempt.
    if _is_under(abs_path, vault_root + "/wiki/_templates"):
        return 0
    if abs_path.startswith(vault_root + "/wiki/meta/lint-report-"):
        return 0

    basename = os.path.basename(abs_path)
    if basename.endswith(".md"):
        # Reject space in basename
        if " " in basename:
            hyphenated = basename.replace(" ", "-")
            sys.stderr.write(
                "BLOCKED: wiki filenames must be hyphenated (no spaces).\n"
            )
            sys.stderr.write("  Got:      " + basename + "\n")
            sys.stderr.write("  Expected: " + hyphenated + "\n")
            sys.stderr.write(
                "  Convention enforced because mixed slug styles produced 254 "
                "broken wikilinks in a single batch.\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
