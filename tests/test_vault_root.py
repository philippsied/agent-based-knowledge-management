#!/usr/bin/env python3
"""Tests for lib/vault_root.py.

Self-contained: no pytest dependency. Verifies the KM_VAULT_PATH -> argv -> cwd
resolution order for both resolve_vault_root() and resolve_wiki_root().

Run:
  python3 tests/test_vault_root.py
"""
from __future__ import annotations

import os
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


if __name__ == "__main__":
    try:
        test_default_is_cwd_for_vault_root()
        test_default_is_cwd_wiki_for_wiki_root()
        test_argv_overrides_cwd()
        test_env_overrides_argv()
        test_env_overrides_cwd()
        test_tilde_expansion_in_env()
        test_empty_env_falls_through()
    except Fail as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print("\nAll vault_root tests passed.")
