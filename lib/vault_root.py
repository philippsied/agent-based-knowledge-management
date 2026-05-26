"""Vault-root resolver — single source of truth for "where is the vault".

Resolution order (PR0 convention, see docs/upstream-roadmap.md):

    KM_VAULT_PATH (env)  ->  positional CLI argument  ->  current working directory

The cwd default makes a marketplace-installed plugin operate on the user's vault
rather than on its own install directory under ~/.claude/plugins/. The env
override is for hooks, CI jobs, and other contexts where cwd isn't the vault.

Two public helpers:

  resolve_vault_root(cli_arg=None) -> Path
      Returns the vault root itself. Used by scripts whose argv (if any) is the
      vault root — e.g., tiling-check.py.

  resolve_wiki_root(cli_arg=None) -> Path
      Returns <vault_root>/wiki. Used by scripts whose argv historically pointed
      at the wiki subdirectory directly (lint-terminology.py,
      lint-title-overlap.py). If cli_arg is given, it is treated as the wiki
      root directly (backward-compatible with existing callers and tests).

Both helpers expand ~ and resolve the path. They do NOT verify existence; the
calling script decides how to handle a missing directory (most exit with a
specific error message + non-zero code).
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_VAR = "KM_VAULT_PATH"


def _from_env() -> Path | None:
    raw = os.environ.get(ENV_VAR)
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def resolve_vault_root(cli_arg: str | os.PathLike | None = None) -> Path:
    """Return the resolved vault root.

    Order: KM_VAULT_PATH env -> cli_arg -> cwd.
    """
    env_root = _from_env()
    if env_root is not None:
        return env_root
    if cli_arg is not None:
        return Path(cli_arg).expanduser().resolve()
    return Path.cwd().resolve()


def resolve_wiki_root(cli_arg: str | os.PathLike | None = None) -> Path:
    """Return the resolved wiki directory (<vault_root>/wiki).

    If cli_arg is given, it is interpreted as a wiki root directly — this
    preserves backward compatibility with lint-terminology.py /
    lint-title-overlap.py callers that pass a wiki path explicitly.

    If KM_VAULT_PATH is set, it wins over cli_arg (env > argv > cwd), and the
    wiki root is computed as <KM_VAULT_PATH>/wiki.
    """
    env_root = _from_env()
    if env_root is not None:
        return (env_root / "wiki").resolve()
    if cli_arg is not None:
        return Path(cli_arg).expanduser().resolve()
    return (Path.cwd() / "wiki").resolve()
