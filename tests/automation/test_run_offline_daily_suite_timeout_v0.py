"""Tests for offline daily suite `job_pytest_fast` timeout wiring (no full pytest run)."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from scripts.automation.run_offline_daily_suite import (
    PYTEST_FAST_TIMEOUT_SEC,
    job_pytest_fast,
)


def test_pytest_fast_timeout_constant_default() -> None:
    assert PYTEST_FAST_TIMEOUT_SEC == 600


def test_job_pytest_fast_dry_run_skips_subprocess() -> None:
    with patch.object(subprocess, "run") as m:
        result = job_pytest_fast(dry_run=True)
    m.assert_not_called()
    assert result.status == "skipped"


def test_job_pytest_fast_passes_expected_cmd_and_timeout() -> None:
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
    assert m.call_args.kwargs["timeout"] == PYTEST_FAST_TIMEOUT_SEC


def test_job_pytest_fast_timeout_expired_marks_failed_with_config_seconds() -> None:
    with patch.object(subprocess, "run") as m:
        m.side_effect = subprocess.TimeoutExpired(
            cmd=["pytest", "-q", "-x", "--tb=short"],
            timeout=PYTEST_FAST_TIMEOUT_SEC,
        )
        result = job_pytest_fast(dry_run=False)
    assert result.status == "failed"
    assert result.error_msg == f"Pytest timeout after {PYTEST_FAST_TIMEOUT_SEC}s"
