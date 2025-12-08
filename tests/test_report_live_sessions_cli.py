"""
Tests fuer scripts/report_live_sessions.py CLI (Phase 81)
=========================================================

Testet die CLI zum Generieren von Live-Session-Reports.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

import pytest

# Projekt-Root zum Path hinzufuegen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.experiments.live_session_registry import LiveSessionRecord


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_records() -> List[LiveSessionRecord]:
    """Erzeugt eine Liste von Sample-Records fuer Tests."""
    now = datetime.utcnow()
    return [
        LiveSessionRecord(
            session_id="session_001",
            run_id="run_001",
            run_type="live_session_shadow",
            mode="shadow",
            env_name="shadow_local",
            symbol="BTC/EUR",
            status="completed",
            started_at=now - timedelta(hours=2),
            finished_at=now - timedelta(hours=1),
            config={"strategy_name": "ma_crossover"},
            metrics={"realized_pnl": 150.0, "max_drawdown": 0.05},
            cli_args=["python", "scripts/run_execution_session.py", "--shadow"],
        ),
        LiveSessionRecord(
            session_id="session_002",
            run_id="run_002",
            run_type="live_session_testnet",
            mode="testnet",
            env_name="kraken_futures_testnet",
            symbol="ETH/EUR",
            status="completed",
            started_at=now - timedelta(hours=1),
            finished_at=now,
            config={"strategy_name": "rsi_reversion"},
            metrics={"realized_pnl": -50.0, "max_drawdown": 0.08},
            cli_args=["python", "scripts/run_execution_session.py", "--testnet"],
        ),
        LiveSessionRecord(
            session_id="session_003",
            run_id=None,
            run_type="live_session_shadow",
            mode="shadow",
            env_name="shadow_local",
            symbol="BTC/EUR",
            status="failed",
            started_at=now - timedelta(minutes=30),
            finished_at=now - timedelta(minutes=25),
            config={"strategy_name": "bollinger"},
            metrics={},
            error="ConnectionError: API timeout",
            cli_args=["python", "scripts/run_execution_session.py", "--shadow"],
        ),
    ]


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Erzeugt ein temporaeres Output-Verzeichnis."""
    output_dir = tmp_path / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# =============================================================================
# Test: CLI Argument Parsing
# =============================================================================


def test_cli_help_flag():
    """Test: --help Flag zeigt Hilfetext."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_cli_default_args():
    """Test: Default-Argumente werden korrekt gesetzt."""
    import argparse
    from scripts.report_live_sessions import main

    # Wir testen indirekt durch Mocking
    with patch("sys.argv", ["report_live_sessions.py", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            mock_list.return_value = []
            result = main()
            # Sollte erfolgreich durchlaufen (keine Sessions gefunden ist OK)
            assert result == 0
            mock_list.assert_called_once_with(
                run_type=None,
                status=None,
                limit=None,
            )


# =============================================================================
# Test: Filter-Optionen
# =============================================================================


def test_cli_run_type_filter(sample_records: List[LiveSessionRecord]):
    """Test: --run-type Filter wird korrekt angewendet."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--run-type", "live_session_shadow", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            mock_list.return_value = [r for r in sample_records if r.run_type == "live_session_shadow"]
            result = main()
            assert result == 0
            mock_list.assert_called_once_with(
                run_type="live_session_shadow",
                status=None,
                limit=None,
            )


def test_cli_status_filter(sample_records: List[LiveSessionRecord]):
    """Test: --status Filter wird korrekt angewendet."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--status", "completed", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            mock_list.return_value = [r for r in sample_records if r.status == "completed"]
            result = main()
            assert result == 0
            mock_list.assert_called_once_with(
                run_type=None,
                status="completed",
                limit=None,
            )


def test_cli_limit_filter(sample_records: List[LiveSessionRecord]):
    """Test: --limit Filter wird korrekt angewendet."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--limit", "2", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            mock_list.return_value = sample_records[:2]
            result = main()
            assert result == 0
            mock_list.assert_called_once_with(
                run_type=None,
                status=None,
                limit=2,
            )


def test_cli_combined_filters(sample_records: List[LiveSessionRecord]):
    """Test: Kombinierte Filter werden korrekt angewendet."""
    from scripts.report_live_sessions import main

    with patch(
        "sys.argv",
        ["report_live_sessions.py", "--run-type", "live_session_shadow", "--status", "completed", "--limit", "5", "--stdout"],
    ):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            mock_list.return_value = [sample_records[0]]
            result = main()
            assert result == 0
            mock_list.assert_called_once_with(
                run_type="live_session_shadow",
                status="completed",
                limit=5,
            )


# =============================================================================
# Test: Output-Format
# =============================================================================


def test_cli_output_format_markdown(sample_records: List[LiveSessionRecord], tmp_path: Path, capsys):
    """Test: --output-format markdown generiert Markdown."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--output-format", "markdown", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            with patch(
                "src.experiments.live_session_registry.render_sessions_markdown"
            ) as mock_render:
                mock_list.return_value = sample_records
                mock_render.return_value = "# Test Markdown Report"
                result = main()
                assert result == 0
                mock_render.assert_called_once()

    captured = capsys.readouterr()
    assert "# Test Markdown Report" in captured.out


def test_cli_output_format_html(sample_records: List[LiveSessionRecord], capsys):
    """Test: --output-format html generiert HTML."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--output-format", "html", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            with patch(
                "src.experiments.live_session_registry.render_sessions_html"
            ) as mock_render:
                mock_list.return_value = sample_records
                mock_render.return_value = "<html><body>Test HTML</body></html>"
                result = main()
                assert result == 0
                mock_render.assert_called_once()

    captured = capsys.readouterr()
    assert "<html>" in captured.out


def test_cli_output_format_both(sample_records: List[LiveSessionRecord], temp_output_dir: Path):
    """Test: --output-format both generiert Markdown und HTML Dateien."""
    from scripts.report_live_sessions import main

    with patch(
        "sys.argv",
        ["report_live_sessions.py", "--output-format", "both", "--output-dir", str(temp_output_dir)],
    ):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            with patch(
                "src.experiments.live_session_registry.render_sessions_markdown"
            ) as mock_md:
                with patch(
                    "src.experiments.live_session_registry.render_sessions_html"
                ) as mock_html:
                    mock_list.return_value = sample_records
                    mock_md.return_value = "# Markdown"
                    mock_html.return_value = "<html></html>"
                    result = main()
                    assert result == 0
                    mock_md.assert_called_once()
                    mock_html.assert_called_once()

    # Dateien sollten erzeugt worden sein
    md_files = list(temp_output_dir.glob("*_sessions_report.md"))
    html_files = list(temp_output_dir.glob("*_sessions_report.html"))
    assert len(md_files) == 1
    assert len(html_files) == 1


# =============================================================================
# Test: Summary-Only Mode
# =============================================================================


def test_cli_summary_only_markdown(sample_records: List[LiveSessionRecord], capsys):
    """Test: --summary-only generiert nur Summary (Markdown)."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--summary-only", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            with patch(
                "src.experiments.live_session_registry.get_session_summary"
            ) as mock_summary:
                mock_list.return_value = sample_records
                mock_summary.return_value = {
                    "num_sessions": 3,
                    "by_status": {"completed": 2, "failed": 1},
                    "total_realized_pnl": 100.0,
                    "avg_max_drawdown": 0.065,
                }
                result = main()
                assert result == 0
                mock_summary.assert_called_once()

    captured = capsys.readouterr()
    assert "Live-Session Registry Summary" in captured.out
    assert "Anzahl Sessions" in captured.out


def test_cli_summary_only_html(sample_records: List[LiveSessionRecord], capsys):
    """Test: --summary-only mit HTML-Format."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--summary-only", "--output-format", "html", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            with patch(
                "src.experiments.live_session_registry.get_session_summary"
            ) as mock_summary:
                mock_list.return_value = sample_records
                mock_summary.return_value = {
                    "num_sessions": 3,
                    "by_status": {"completed": 2, "failed": 1},
                }
                result = main()
                assert result == 0

    captured = capsys.readouterr()
    assert "<html>" in captured.out
    assert "Live-Session Registry Summary" in captured.out


# =============================================================================
# Test: Output-Dir
# =============================================================================


def test_cli_output_dir(sample_records: List[LiveSessionRecord], temp_output_dir: Path):
    """Test: --output-dir schreibt Dateien ins angegebene Verzeichnis."""
    from scripts.report_live_sessions import main

    with patch(
        "sys.argv",
        ["report_live_sessions.py", "--output-dir", str(temp_output_dir)],
    ):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            with patch(
                "src.experiments.live_session_registry.render_sessions_markdown"
            ) as mock_render:
                mock_list.return_value = sample_records
                mock_render.return_value = "# Report Content"
                result = main()
                assert result == 0

    # Datei sollte im temp_output_dir sein
    md_files = list(temp_output_dir.glob("*_sessions_report.md"))
    assert len(md_files) == 1
    assert md_files[0].read_text() == "# Report Content"


def test_cli_output_dir_creates_if_missing(sample_records: List[LiveSessionRecord], tmp_path: Path):
    """Test: --output-dir erzeugt Verzeichnis falls nicht vorhanden."""
    from scripts.report_live_sessions import main

    new_dir = tmp_path / "new_reports" / "nested"
    assert not new_dir.exists()

    with patch(
        "sys.argv",
        ["report_live_sessions.py", "--output-dir", str(new_dir), "--stdout"],
    ):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            with patch(
                "src.experiments.live_session_registry.render_sessions_markdown"
            ) as mock_render:
                mock_list.return_value = sample_records
                mock_render.return_value = "# Report"
                result = main()
                assert result == 0

    # Verzeichnis sollte jetzt existieren
    assert new_dir.exists()


# =============================================================================
# Test: Edge Cases
# =============================================================================


def test_cli_no_sessions_found(capsys):
    """Test: Keine Sessions gefunden gibt freundliche Meldung."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            mock_list.return_value = []
            result = main()
            assert result == 0

    captured = capsys.readouterr()
    assert "Keine Sessions gefunden" in captured.out


def test_cli_no_sessions_writes_empty_report(temp_output_dir: Path):
    """Test: Keine Sessions gefunden schreibt leeren Report."""
    from scripts.report_live_sessions import main

    with patch(
        "sys.argv",
        ["report_live_sessions.py", "--output-dir", str(temp_output_dir)],
    ):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            mock_list.return_value = []
            result = main()
            assert result == 0

    # Leerer Report sollte geschrieben worden sein
    md_files = list(temp_output_dir.glob("*_sessions_report.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text()
    assert "Keine Sessions gefunden" in content


# =============================================================================
# Test: Summary Formatters
# =============================================================================


def test_format_summary_markdown():
    """Test: format_summary_markdown erzeugt korrektes Markdown."""
    from scripts.report_live_sessions import format_summary_markdown

    summary = {
        "num_sessions": 5,
        "by_status": {"completed": 3, "failed": 2},
        "total_realized_pnl": 250.50,
        "avg_max_drawdown": 0.075,
        "first_started_at": "2025-12-01T10:00:00",
        "last_started_at": "2025-12-08T15:30:00",
    }

    md = format_summary_markdown(summary)

    assert "# Live-Session Registry Summary" in md
    assert "**Anzahl Sessions:** 5" in md
    assert "**completed:** 3" in md
    assert "**failed:** 2" in md
    assert "**Total Realized PnL:** 250.50" in md
    assert "**Avg Max Drawdown:** 0.0750" in md
    assert "**Erste Session:** 2025-12-01T10:00:00" in md
    assert "**Letzte Session:** 2025-12-08T15:30:00" in md


def test_format_summary_html():
    """Test: format_summary_html erzeugt korrektes HTML."""
    from scripts.report_live_sessions import format_summary_html

    summary = {
        "num_sessions": 3,
        "by_status": {"completed": 2, "aborted": 1},
        "total_realized_pnl": 100.0,
        "avg_max_drawdown": 0.05,
    }

    html = format_summary_html(summary)

    assert "<!DOCTYPE html>" in html
    assert "<title>Live-Session Registry Summary</title>" in html
    assert "Anzahl Sessions:</strong> 3" in html
    assert "<td>completed</td><td>2</td>" in html
    assert "Total Realized PnL:</strong> 100.00" in html


def test_format_summary_markdown_empty():
    """Test: format_summary_markdown mit leeren/fehlenden Werten."""
    from scripts.report_live_sessions import format_summary_markdown

    summary = {
        "num_sessions": 0,
        "by_status": {},
    }

    md = format_summary_markdown(summary)

    assert "# Live-Session Registry Summary" in md
    assert "**Anzahl Sessions:** 0" in md


def test_format_summary_html_empty():
    """Test: format_summary_html mit leeren/fehlenden Werten."""
    from scripts.report_live_sessions import format_summary_html

    summary = {
        "num_sessions": 0,
        "by_status": {},
    }

    html = format_summary_html(summary)

    assert "<!DOCTYPE html>" in html
    assert "Anzahl Sessions:</strong> 0" in html


# =============================================================================
# Test: Integration (ohne Mocks)
# =============================================================================


def test_cli_integration_with_temp_registry(tmp_path: Path):
    """Test: Integration mit echter Registry (in temp-Verzeichnis)."""
    from src.experiments.live_session_registry import (
        LiveSessionRecord,
        register_live_session_run,
    )
    from scripts.report_live_sessions import main

    # Registry-Verzeichnis
    registry_dir = tmp_path / "sessions"
    registry_dir.mkdir(parents=True, exist_ok=True)

    # Echte Session registrieren
    record = LiveSessionRecord(
        session_id="integration_test_001",
        run_id=None,
        run_type="live_session_shadow",
        mode="shadow",
        env_name="test_env",
        symbol="BTC/EUR",
        status="completed",
        started_at=datetime.utcnow(),
        config={"test": True},
        metrics={"realized_pnl": 100.0},
    )
    register_live_session_run(record, base_dir=registry_dir)

    # Output-Verzeichnis
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # CLI ausfuehren (mit gepatchtem DEFAULT_LIVE_SESSION_DIR)
    with patch(
        "sys.argv",
        ["report_live_sessions.py", "--output-dir", str(output_dir)],
    ):
        with patch(
            "src.experiments.live_session_registry.DEFAULT_LIVE_SESSION_DIR",
            registry_dir,
        ):
            result = main()
            assert result == 0

    # Report sollte erzeugt worden sein
    md_files = list(output_dir.glob("*_sessions_report.md"))
    assert len(md_files) == 1
    content = md_files[0].read_text()
    assert "integration_test_001" in content


# =============================================================================
# Test: Log-Level
# =============================================================================


def test_cli_log_level_debug():
    """Test: --log-level DEBUG wird akzeptiert."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--log-level", "DEBUG", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            mock_list.return_value = []
            result = main()
            assert result == 0


def test_cli_log_level_warning():
    """Test: --log-level WARNING wird akzeptiert."""
    from scripts.report_live_sessions import main

    with patch("sys.argv", ["report_live_sessions.py", "--log-level", "WARNING", "--stdout"]):
        with patch(
            "src.experiments.live_session_registry.list_session_records"
        ) as mock_list:
            mock_list.return_value = []
            result = main()
            assert result == 0
