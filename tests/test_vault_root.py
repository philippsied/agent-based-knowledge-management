#!/usr/bin/env python3
"""Tests for lib/vault_root.py.

Self-contained: no pytest dependency. Verifies the KM_VAULT_PATH -> argv -> cwd
resolution order for both resolve_vault_root() and resolve_wiki_root().

Run:
  python3 tests/test_vault_root.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

from vault_root import (  # noqa: E402
    ENV_VAR,
    resolve_vault_root,
    resolve_wiki_root,
)

VAULT_ROOT_PY = ROOT / "lib" / "vault_root.py"


def _run_cli(args: list[str], env: dict[str, str] | None = None) -> str:
    """Run the CLI and return stdout stripped of its trailing newline."""
    full_env = os.environ.copy()
    if env is not None:
        for k, v in env.items():
            if v is None:
                full_env.pop(k, None)
            else:
                full_env[k] = v
    result = subprocess.run(
        [sys.executable, str(VAULT_ROOT_PY), *args],
        capture_output=True, text=True, check=True, env=full_env,
    )
    return result.stdout.rstrip("\n")


class Fail(AssertionError):
    pass


def assert_eq(label: str, expected, actual) -> None:
    if expected != actual:
        raise Fail(f"FAIL {label}: expected {expected!r}, got {actual!r}")
    print(f"PASS {label}")


def assert_true(label: str, cond: bool) -> None:
    if not cond:
        raise Fail(f"FAIL {label}")
    print(f"PASS {label}")


def _clear_env() -> None:
    os.environ.pop(ENV_VAR, None)


def test_default_is_cwd_for_vault_root():
    _clear_env()
    with tempfile.TemporaryDirectory() as td:
        td_resolved = Path(td).resolve()
        old = Path.cwd()
        os.chdir(td)
        try:
            got = resolve_vault_root()
            assert_eq("vault_root default = cwd", td_resolved, got)
        finally:
            os.chdir(old)


def test_default_is_cwd_wiki_for_wiki_root():
    _clear_env()
    with tempfile.TemporaryDirectory() as td:
        td_resolved = Path(td).resolve()
        old = Path.cwd()
        os.chdir(td)
        try:
            got = resolve_wiki_root()
            assert_eq("wiki_root default = cwd/wiki", td_resolved / "wiki", got)
        finally:
            os.chdir(old)


def test_argv_overrides_cwd():
    _clear_env()
    with tempfile.TemporaryDirectory() as td:
        td_resolved = Path(td).resolve()
        got_vault = resolve_vault_root(td)
        assert_eq("vault_root argv wins over cwd", td_resolved, got_vault)
        # For wiki root, argv is treated as a wiki path directly (backward compat).
        got_wiki = resolve_wiki_root(td)
        assert_eq("wiki_root argv = path directly", td_resolved, got_wiki)


def test_env_overrides_argv():
    with tempfile.TemporaryDirectory() as env_td, tempfile.TemporaryDirectory() as argv_td:
        env_resolved = Path(env_td).resolve()
        os.environ[ENV_VAR] = env_td
        try:
            got_vault = resolve_vault_root(argv_td)
            assert_eq("vault_root env wins over argv", env_resolved, got_vault)
            got_wiki = resolve_wiki_root(argv_td)
            assert_eq("wiki_root env wins over argv",
                      (env_resolved / "wiki").resolve(), got_wiki)
        finally:
            _clear_env()


def test_env_overrides_cwd():
    with tempfile.TemporaryDirectory() as env_td, tempfile.TemporaryDirectory() as cwd_td:
        env_resolved = Path(env_td).resolve()
        os.environ[ENV_VAR] = env_td
        old = Path.cwd()
        os.chdir(cwd_td)
        try:
            got_vault = resolve_vault_root()
            assert_eq("vault_root env wins over cwd", env_resolved, got_vault)
            got_wiki = resolve_wiki_root()
            assert_eq("wiki_root env wins over cwd",
                      (env_resolved / "wiki").resolve(), got_wiki)
        finally:
            os.chdir(old)
            _clear_env()


def test_tilde_expansion_in_env():
    home = Path.home()
    os.environ[ENV_VAR] = "~"
    try:
        got = resolve_vault_root()
        assert_eq("env ~ expands to $HOME", home.resolve(), got)
    finally:
        _clear_env()


def test_empty_env_falls_through():
    """An empty KM_VAULT_PATH should be treated as unset."""
    _clear_env()
    os.environ[ENV_VAR] = ""
    with tempfile.TemporaryDirectory() as argv_td:
        argv_resolved = Path(argv_td).resolve()
        try:
            got = resolve_vault_root(argv_td)
            assert_eq("empty env falls through to argv", argv_resolved, got)
        finally:
            _clear_env()


def test_cli_vault_with_env():
    """CLI: --vault with KM_VAULT_PATH set returns the env value."""
    with tempfile.TemporaryDirectory() as td:
        td_resolved = Path(td).resolve()
        out = _run_cli(["--vault"], env={ENV_VAR: td})
        assert_eq("cli --vault honours env", str(td_resolved), out)


def test_cli_wiki_with_env():
    """CLI: --wiki with KM_VAULT_PATH set returns <env>/wiki."""
    with tempfile.TemporaryDirectory() as td:
        td_resolved = Path(td).resolve()
        out = _run_cli(["--wiki"], env={ENV_VAR: td})
        assert_eq("cli --wiki honours env", str((td_resolved / "wiki").resolve()), out)


def test_cli_vault_with_positional_arg():
    """CLI: --vault with positional arg and no env returns the argv value."""
    with tempfile.TemporaryDirectory() as td:
        td_resolved = Path(td).resolve()
        out = _run_cli(["--vault", td], env={ENV_VAR: None})
        assert_eq("cli --vault positional arg", str(td_resolved), out)


def test_cli_wiki_with_positional_arg():
    """CLI: --wiki with positional arg and no env returns the argv as wiki path."""
    with tempfile.TemporaryDirectory() as td:
        td_resolved = Path(td).resolve()
        out = _run_cli(["--wiki", td], env={ENV_VAR: None})
        assert_eq("cli --wiki positional arg", str(td_resolved), out)


def test_cli_env_wins_over_argv():
    """CLI: env beats positional arg, matching helper precedence."""
    with tempfile.TemporaryDirectory() as env_td, tempfile.TemporaryDirectory() as argv_td:
        env_resolved = Path(env_td).resolve()
        out = _run_cli(["--vault", argv_td], env={ENV_VAR: env_td})
        assert_eq("cli --vault env > argv", str(env_resolved), out)


def test_cli_parity_with_python_helper():
    """Parity: the CLI prints exactly what resolve_*() returns for the same input.

    Covers a handful of env/argv combinations so that any future drift between
    the python helper and the CLI surfaces here.
    """
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        cases = [
            # (env, argv, helper, label)
            (None, None, "vault", "parity vault (no env, no argv)"),
            (None, a, "vault", "parity vault (argv only)"),
            (a, None, "vault", "parity vault (env only)"),
            (a, b, "vault", "parity vault (env beats argv)"),
            (None, None, "wiki", "parity wiki (no env, no argv)"),
            (None, a, "wiki", "parity wiki (argv only)"),
            (a, None, "wiki", "parity wiki (env only)"),
            (a, b, "wiki", "parity wiki (env beats argv)"),
        ]
        for env_val, argv_val, which, label in cases:
            # Helper invocation (in-process)
            saved_env = os.environ.pop(ENV_VAR, None)
            try:
                if env_val is not None:
                    os.environ[ENV_VAR] = env_val
                if which == "vault":
                    helper_out = str(resolve_vault_root(argv_val))
                else:
                    helper_out = str(resolve_wiki_root(argv_val))
            finally:
                os.environ.pop(ENV_VAR, None)
                if saved_env is not None:
                    os.environ[ENV_VAR] = saved_env

            # CLI invocation
            cli_args = [f"--{which}"]
            if argv_val is not None:
                cli_args.append(argv_val)
            cli_out = _run_cli(cli_args, env={ENV_VAR: env_val})
            assert_eq(label, helper_out, cli_out)


if __name__ == "__main__":
    try:
        test_default_is_cwd_for_vault_root()
        test_default_is_cwd_wiki_for_wiki_root()
        test_argv_overrides_cwd()
        test_env_overrides_argv()
        test_env_overrides_cwd()
        test_tilde_expansion_in_env()
        test_empty_env_falls_through()
        test_cli_vault_with_env()
        test_cli_wiki_with_env()
        test_cli_vault_with_positional_arg()
        test_cli_wiki_with_positional_arg()
        test_cli_env_wins_over_argv()
        test_cli_parity_with_python_helper()
    except Fail as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print("\nAll vault_root tests passed.")
