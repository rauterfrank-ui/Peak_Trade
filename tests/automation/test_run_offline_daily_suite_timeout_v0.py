"""Tests for offline daily suite `job_pytest_fast` subprocess wiring (no full pytest run)."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from scripts.automation.run_offline_daily_suite import job_pytest_fast


def test_job_pytest_fast_dry_run_skips_subprocess() -> None:
    with patch.object(subprocess, "run") as m:
        result = job_pytest_fast(dry_run=True)
    m.assert_not_called()
    assert result.status == "skipped"


def test_job_pytest_fast_passes_expected_cmd_without_subprocess_timeout() -> None:
    with patch.object(subprocess, "run") as m:
        m.return_value = subprocess.CompletedProcess(
            args=["pytest"],
            returncode=0,
            stdout="",
            stderr="",
        )
        job_pytest_fast(dry_run=False)
    m.assert_called_once()
    assert m.call_args[0][0] == ["pytest", "-q", "-x", "--tb=short"]
    assert "timeout" not in m.call_args.kwargs


def test_job_pytest_fast_nonzero_return_marks_failed() -> None:
    with patch.object(subprocess, "run") as m:
        m.return_value = subprocess.CompletedProcess(
            args=["pytest"],
            returncode=1,
            stdout="",
            stderr="boom",
        )
        result = job_pytest_fast(dry_run=False)
    assert result.status == "failed"
    assert result.extra.get("returncode") == 1
    assert result.error_msg == "boom"
