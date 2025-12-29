"""
Smoke Tests für VaR Backtest Suite Snapshot Runner
===================================================

Tests für Phase 10: Operator convenience command.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "risk" / "run_var_backtest_suite_snapshot.py"


class TestCLIOutput:
    """Test CLI output and exit codes."""

    def test_help_message(self):
        """Test that --help works."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "VaR Backtest Suite Snapshot Runner" in result.stdout
        assert "--use-synthetic" in result.stdout
        assert "--enable-duration-diagnostic" in result.stdout
        assert "--enable-rolling" in result.stdout

    def test_synthetic_basic(self):
        """Test basic synthetic data run."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--use-synthetic",
                "--n-observations",
                "500",  # >= min_observations (250)
                "--confidence",
                "0.99",
                "--no-report",  # Skip report for speed
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        # Should exit 0 (tests passed) - or check that it ran without crash
        # Note: Exit code depends on test results, so just check output exists
        assert result.returncode in [0, 1]  # 0=pass, 1=some tests failed

        # Check console output
        output = result.stdout
        assert "VAR BACKTEST SUITE SUMMARY" in output
        assert "Observations:" in output
        assert "Violations:" in output
        assert "Kupiec POF:" in output
        assert "Independence:" in output
        assert "Cond. Coverage:" in output
        assert "Basel Traffic Light:" in output
        assert "Overall Verdict:" in output

    def test_synthetic_with_duration_diagnostic(self):
        """Test with Phase 9A duration diagnostic enabled."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--use-synthetic",
                "--n-observations",
                "300",
                "--confidence",
                "0.99",
                "--enable-duration-diagnostic",
                "--no-report",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        assert result.returncode == 0

        output = result.stdout
        assert "Phase 9A: Duration Diagnostic" in output
        assert "Duration Ratio:" in output
        assert "Clustering:" in output

    def test_synthetic_with_rolling_evaluation(self):
        """Test with Phase 9B rolling evaluation enabled."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--use-synthetic",
                "--n-observations",
                "500",
                "--confidence",
                "0.99",
                "--enable-rolling",
                "--rolling-window-size",
                "100",
                "--rolling-step-size",
                "100",
                "--no-report",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        assert result.returncode == 0

        output = result.stdout
        assert "Phase 9B: Rolling Evaluation" in output
        assert "Windows Evaluated:" in output
        assert "All-Pass Rate:" in output  # Corrected
        assert "Verdict Stability:" in output

    def test_synthetic_full_diagnostics(self):
        """Test with both Phase 9A and 9B enabled."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--use-synthetic",
                "--n-observations",
                "400",
                "--confidence",
                "0.99",
                "--enable-duration-diagnostic",
                "--enable-rolling",
                "--rolling-window-size",
                "100",
                "--no-report",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        assert result.returncode == 0

        output = result.stdout
        # Check both Phase 9A and 9B appear
        assert "Phase 9A: Duration Diagnostic" in output
        assert "Phase 9B: Rolling Evaluation" in output


class TestReportGeneration:
    """Test markdown report generation."""

    def test_report_creation(self, tmp_path):
        """Test that markdown report is created."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--use-synthetic",
                "--n-observations",
                "500",
                "--confidence",
                "0.99",
                "--output-dir",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        # Check that command ran (exit code may vary based on test results)
        assert result.returncode in [0, 1]

        # Check that report file was created
        report_files = list(tmp_path.glob("var_backtest_suite_snapshot_*.md"))
        assert len(report_files) == 1

        # Read report content
        report_content = report_files[0].read_text()

        # Check report structure
        assert "# VaR Backtest Suite Snapshot" in report_content
        assert "## Summary" in report_content
        assert "## Core Tests" in report_content
        assert "### Kupiec Proportion of Failures" in report_content
        assert "### Christoffersen Independence Test" in report_content
        assert "### Christoffersen Conditional Coverage Test" in report_content
        assert "### Basel Traffic Light" in report_content
        assert "## Overall Verdict" in report_content

    def test_report_with_phase9a(self, tmp_path):
        """Test report includes Phase 9A when enabled."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--use-synthetic",
                "--n-observations",
                "300",
                "--enable-duration-diagnostic",
                "--output-dir",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        assert result.returncode == 0

        report_files = list(tmp_path.glob("var_backtest_suite_snapshot_*.md"))
        report_content = report_files[0].read_text()

        assert "## Phase 9A: Duration Diagnostic" in report_content
        assert "Duration Ratio:" in report_content

    def test_report_with_phase9b(self, tmp_path):
        """Test report includes Phase 9B when enabled."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--use-synthetic",
                "--n-observations",
                "500",
                "--enable-rolling",
                "--rolling-window-size",
                "100",
                "--output-dir",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        assert result.returncode == 0

        report_files = list(tmp_path.glob("var_backtest_suite_snapshot_*.md"))
        report_content = report_files[0].read_text()

        assert "## Phase 9B: Rolling Evaluation" in report_content
        assert "### Pass Rates" in report_content
        assert "### Window Details" in report_content


class TestErrorHandling:
    """Test error handling and validation."""

    def test_missing_var_file(self):
        """Test that missing --var-file with --returns-file raises error."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--returns-file",
                "data/returns.csv",
                # Missing --var-file
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "--var-file is required" in result.stderr

    def test_no_data_source(self):
        """Test that missing data source raises error."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--confidence",
                "0.99",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        # Should show help about required arguments


class TestExitCodes:
    """Test exit codes for different scenarios."""

    def test_exit_code_all_pass(self):
        """Test exit code 0 when all core tests pass."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--use-synthetic",
                "--n-observations",
                "250",
                "--confidence",
                "0.99",
                "--no-report",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        # Should exit 0 (all tests passed)
        assert result.returncode == 0
        assert "✅ ALL PASSED" in result.stdout


class TestVerboseOutput:
    """Test verbose logging."""

    def test_verbose_flag(self):
        """Test that -v flag enables verbose logging."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--use-synthetic",
                "--n-observations",
                "500",
                "-v",
                "--no-report",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        # Just check that it doesn't crash
        assert result.returncode in [0, 1, 2]  # Any valid exit code


class TestDeterministicBehavior:
    """Test deterministic behavior for same inputs."""

    def test_deterministic_output(self, tmp_path):
        """Test that same input produces same-structure output."""
        # Run twice with same parameters
        args = [
            sys.executable,
            str(SCRIPT_PATH),
            "--use-synthetic",
            "--n-observations",
            "300",
            "--confidence",
            "0.99",
            "--output-dir",
            str(tmp_path / "run1"),
        ]

        result1 = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        args[-1] = str(tmp_path / "run2")
        result2 = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )

        assert result1.returncode == result2.returncode

        # Reports should have same structure (but different timestamps)
        report1 = list((tmp_path / "run1").glob("*.md"))[0].read_text()
        report2 = list((tmp_path / "run2").glob("*.md"))[0].read_text()

        # Check that both have same sections
        for section in [
            "# VaR Backtest Suite Snapshot",
            "## Summary",
            "## Core Tests",
            "## Overall Verdict",
        ]:
            assert section in report1
            assert section in report2
