"""Tests für try_git_sha (_forward_run_manifest) mit gemocktem subprocess."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import _forward_run_manifest as _frm  # noqa: E402
from _forward_run_manifest import try_git_sha  # noqa: E402


def test_try_git_sha_returns_stripped_stdout_when_git_succeeds() -> None:
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = "  deadbeef\n"

    with patch.object(_frm.subprocess, "run", return_value=proc) as mock_run:
        assert try_git_sha() == "deadbeef"

    mock_run.assert_called_once_with(
        ["git", "rev-parse", "HEAD"],
        cwd=_frm._REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


def test_try_git_sha_returns_none_when_git_fails() -> None:
    proc = MagicMock()
    proc.returncode = 128

    with patch.object(_frm.subprocess, "run", return_value=proc):
        assert try_git_sha() is None


def test_try_git_sha_returns_none_on_subprocess_oserror() -> None:
    with patch.object(
        _frm.subprocess,
        "run",
        side_effect=OSError("git not found"),
    ):
        assert try_git_sha() is None


def test_try_git_sha_returns_none_on_subprocess_timeout() -> None:
    exc = subprocess.TimeoutExpired(cmd=["git", "rev-parse", "HEAD"], timeout=5)
    with patch.object(_frm.subprocess, "run", side_effect=exc):
        assert try_git_sha() is None


def test_try_git_sha_returns_none_on_file_not_found_error() -> None:
    with patch.object(
        _frm.subprocess,
        "run",
        side_effect=FileNotFoundError("git"),
    ):
        assert try_git_sha() is None
