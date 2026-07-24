"""Durable isolated HOME for Workflow Dashboard archive-root contract tests.

On Linux GitHub Actions, pytest ``tmp_path`` lives under ``/tmp``. The production
canonical-default safety gate correctly rejects defaults under ``/tmp`` and
``/var/tmp``. Tests that assert no-env production default-path semantics must
therefore isolate HOME outside those ephemeral roots and outside the git
worktree — not under pytest's ephemeral basetemp.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from src.webui.workflow_dashboard_archive_root_v1 import (
    ENV_ARCHIVE_ROOT,
    _is_under,
    _path_is_under_tmp,
    _repo_root,
)

_CACHE_LEAF = "peak_trade_pytest_durable_homes"


def durable_isolated_home(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    *,
    label: str = "case",
) -> Path:
    """Return an absolute isolated HOME suitable for canonical-default assertions.

    Captures the real operator/runner home *before* monkeypatching ``HOME``.
    Creates the home under ``~/.cache/...`` (durable) via TemporaryDirectory so
    cleanup is automatic and the resolved path is not under ``/tmp``.
    """
    real_home = Path(os.path.expanduser("~")).resolve()
    repo = _repo_root()
    parent = real_home / ".cache" / _CACHE_LEAF / label
    if _path_is_under_tmp(parent):
        raise RuntimeError(f"durable home parent resolved under ephemeral tmp: {parent}")
    if _is_under(parent, repo) or parent == repo.resolve():
        raise RuntimeError(f"durable home parent resolved inside git repo: {parent}")
    parent.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.TemporaryDirectory(dir=str(parent), prefix="home_")
    request.addfinalizer(tmp.cleanup)
    home = Path(tmp.name) / "home"
    home.mkdir()

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    return home


__all__ = ["durable_isolated_home"]
