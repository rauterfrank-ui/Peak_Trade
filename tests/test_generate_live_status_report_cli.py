# tests/test_generate_live_status_report_cli.py
"""
Tests für scripts/generate_live_status_report.py (Phase 57)
============================================================

Testet das CLI-Verhalten des Live-Status-Report-Generators.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

# Pfad-Setup
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# =============================================================================
# Test Fixtures
# =============================================================================


class DummyCompletedProcess:
    """Dummy-CompletedProcess für Mocking."""

    def __init__(self, stdout: str, returncode: int = 0):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = ""


def fake_subprocess_run(
    args: List[str],
    check: bool = False,
    capture_output: bool = False,
    text: bool = False,
):
    """Fake subprocess.run für Tests."""
    if "health" in args:
        return DummyCompletedProcess(
            stdout=json.dumps(
                {
                    "overall_status": "OK",
                    "config_ok": True,
                    "config_errors": [],
                    "exchange_ok": True,
                    "exchange_errors": [],
                    "alerts_enabled": True,
                    "alert_sinks_configured": ["log", "slack_webhook"],
                    "alert_config_warnings": [],
                    "live_risk_ok": True,
                    "live_risk_warnings": [],
                }
            )
        )
    if "portfolio" in args:
        return DummyCompletedProcess(
            stdout=json.dumps(
                {
                    "as_of": "2025-12-07T09:00:00Z",
                    "mode": "testnet",
                    "free_cash": 4845.67,
                    "positions": [
                        {
                            "symbol": "BTCUSD",
                            "size": 0.1,
                            "side": "long",
                            "notional": 4000.0,
                            "unrealized_pnl": 120.5,
                        }
                    ],
                    "totals": {
                        "num_open_positions": 1,
                        "total_notional": 4000.0,
                        "total_unrealized_pnl": 120.5,
                        "total_realized_pnl": 0.0,
                    },
                    "symbol_notional": {"BTCUSD": 4000.0},
                    "risk": {
                        "allowed": True,
                        "reasons": [],
                        "metrics": {},
                    },
                }
            )
        )
    raise AssertionError(f"Unexpected args: {args}")


# =============================================================================
# Tests
# =============================================================================


def test_generate_live_status_report_markdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Testet, dass ein Markdown-Report generiert wird."""
    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    output_dir = tmp_path / "reports" / "live_status"
    config_path = tmp_path / "config.toml"
    config_path.write_text("[environment]\nmode = 'testnet'")

    # Import nach Mock-Setup
    from scripts.generate_live_status_report import main

    # CLI-Args simulieren
    import sys

    original_argv = sys.argv
    try:
        sys.argv = [
            "generate_live_status_report.py",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--format",
            "markdown",
            "--tag",
            "daily",
        ]

        result = main()
        assert result == 0

        # Prüfe, dass Markdown-File erstellt wurde
        md_files = list(output_dir.glob("live_status_*.md"))
        assert len(md_files) == 1

        md_content = md_files[0].read_text(encoding="utf-8")
        assert "# Peak_Trade Live Status Report" in md_content
        assert "## 1. Health Overview" in md_content
        assert "## 2. Portfolio Snapshot" in md_content
        assert "Tag: `daily`" in md_content

    finally:
        sys.argv = original_argv


def test_generate_live_status_report_html(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Testet, dass ein HTML-Report generiert wird."""
    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    output_dir = tmp_path / "reports" / "live_status"
    config_path = tmp_path / "config.toml"
    config_path.write_text("[environment]\nmode = 'testnet'")

    from scripts.generate_live_status_report import main

    import sys

    original_argv = sys.argv
    try:
        sys.argv = [
            "generate_live_status_report.py",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--format",
            "html",
            "--tag",
            "weekly",
        ]

        result = main()
        assert result == 0

        # Prüfe, dass HTML-File erstellt wurde
        html_files = list(output_dir.glob("live_status_*.html"))
        assert len(html_files) == 1

        html_content = html_files[0].read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html_content
        assert "<h1>Peak_Trade Live Status Report</h1>" in html_content

    finally:
        sys.argv = original_argv


def test_generate_live_status_report_both(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Testet, dass beide Formate (Markdown + HTML) generiert werden."""
    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    output_dir = tmp_path / "reports" / "live_status"
    config_path = tmp_path / "config.toml"
    config_path.write_text("[environment]\nmode = 'testnet'")

    from scripts.generate_live_status_report import main

    import sys

    original_argv = sys.argv
    try:
        sys.argv = [
            "generate_live_status_report.py",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--format",
            "both",
        ]

        result = main()
        assert result == 0

        # Prüfe, dass beide Files erstellt wurden
        md_files = list(output_dir.glob("live_status_*.md"))
        html_files = list(output_dir.glob("live_status_*.html"))
        assert len(md_files) == 1
        assert len(html_files) == 1

    finally:
        sys.argv = original_argv


def test_generate_live_status_report_with_notes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Testet, dass Operator-Notizen aus Datei geladen werden."""
    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    output_dir = tmp_path / "reports" / "live_status"
    config_path = tmp_path / "config.toml"
    config_path.write_text("[environment]\nmode = 'testnet'")

    notes_file = tmp_path / "notes.md"
    notes_file.write_text("- [ ] TODO: Test-Notiz\n- [ ] TODO: Weitere Notiz")

    from scripts.generate_live_status_report import main

    import sys

    original_argv = sys.argv
    try:
        sys.argv = [
            "generate_live_status_report.py",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--format",
            "markdown",
            "--notes-file",
            str(notes_file),
        ]

        result = main()
        assert result == 0

        md_files = list(output_dir.glob("live_status_*.md"))
        assert len(md_files) == 1

        md_content = md_files[0].read_text(encoding="utf-8")
        assert "## 4. Notes (Operator)" in md_content
        assert "Test-Notiz" in md_content
        assert "Weitere Notiz" in md_content

    finally:
        sys.argv = original_argv


def test_generate_live_status_report_missing_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Testet, dass fehlende Config-Datei korrekt behandelt wird."""
    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    output_dir = tmp_path / "reports" / "live_status"
    config_path = tmp_path / "nonexistent.toml"

    from scripts.generate_live_status_report import main

    import sys

    original_argv = sys.argv
    try:
        sys.argv = [
            "generate_live_status_report.py",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--format",
            "markdown",
        ]

        result = main()
        assert result == 1  # Fehler erwartet

    finally:
        sys.argv = original_argv








