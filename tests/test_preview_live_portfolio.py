# tests/test_preview_live_portfolio.py
"""
Tests für scripts/preview_live_portfolio.py (Phase 48)
=======================================================

Tests für:
- CLI-Argument-Parsing
- Hauptfunktion mit Mock-Exchange-Client
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Projekt-Root zum Python-Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import scripts.preview_live_portfolio as preview_script
from src.live.broker_base import BaseBrokerClient
from src.live.portfolio_monitor import LivePortfolioSnapshot

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_config_path(tmp_path: Path) -> Path:
    """Erstellt eine temporäre Config-Datei."""
    config_content = """
[general]
base_currency = "EUR"
starting_capital = 10000.0

[live_risk]
enabled = true
max_total_exposure_notional = 50000.0
max_symbol_exposure_notional = 20000.0
max_open_positions = 10
max_daily_loss_abs = 500.0
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(config_content)
    return config_file


# =============================================================================
# PARSER TESTS
# =============================================================================


def test_parse_args_defaults():
    """Testet Default-Argumente."""
    args = preview_script.parse_args([])

    assert args.config_path == "config/config.toml"
    assert args.no_risk is False
    assert args.json is False
    assert args.starting_cash is None
    assert args.verbose is False


def test_parse_args_custom():
    """Testet Custom-Argumente."""
    args = preview_script.parse_args([
        "--config", "custom.toml",
        "--no-risk",
        "--json",
        "--starting-cash", "20000.0",
        "--verbose",
    ])

    assert args.config_path == "custom.toml"
    assert args.no_risk is True
    assert args.json is True
    assert args.starting_cash == 20000.0
    assert args.verbose is True


# =============================================================================
# MAIN FUNCTION TESTS
# =============================================================================


@patch("scripts.preview_live_portfolio.load_config")
@patch("scripts.preview_live_portfolio.create_exchange_client")
@patch("scripts.preview_live_portfolio.LiveRiskLimits")
@patch("scripts.preview_live_portfolio.LivePortfolioMonitor")
def test_main_success(
    mock_monitor_class,
    mock_risk_limits_class,
    mock_create_client,
    mock_load_config,
    sample_config_path: Path,
    capsys,
):
    """Testet erfolgreichen Hauptlauf."""
    # Mock Setup
    mock_cfg = MagicMock()
    mock_cfg.get.return_value = 10000.0
    mock_load_config.return_value = mock_cfg

    mock_client = Mock(spec=BaseBrokerClient)
    mock_create_client.return_value = mock_client

    mock_risk_limits = MagicMock()
    mock_risk_limits_class.from_config.return_value = mock_risk_limits

    mock_monitor = MagicMock()
    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=[],
    )
    mock_monitor.snapshot.return_value = snapshot
    mock_monitor_class.return_value = mock_monitor

    mock_risk_result = MagicMock()
    mock_risk_result.allowed = True
    mock_risk_result.reasons = []
    mock_risk_result.metrics = {}
    mock_risk_limits.evaluate_portfolio.return_value = mock_risk_result

    # Führe aus
    exit_code = preview_script.main(["--config", str(sample_config_path)])

    # Prüfe
    assert exit_code == 0
    assert mock_load_config.called
    assert mock_create_client.called
    assert mock_monitor.snapshot.called
    assert mock_risk_limits.evaluate_portfolio.called

    # Prüfe Ausgabe
    captured = capsys.readouterr()
    assert "Live Portfolio Snapshot" in captured.out or "portfolio" in captured.out.lower()


@patch("scripts.preview_live_portfolio.load_config")
@patch("scripts.preview_live_portfolio.create_exchange_client")
@patch("scripts.preview_live_portfolio.LivePortfolioMonitor")
def test_main_no_risk(
    mock_monitor_class,
    mock_create_client,
    mock_load_config,
    sample_config_path: Path,
    capsys,
):
    """Testet --no-risk Flag."""
    # Mock Setup
    mock_cfg = MagicMock()
    mock_load_config.return_value = mock_cfg

    mock_client = Mock(spec=BaseBrokerClient)
    mock_create_client.return_value = mock_client

    mock_monitor = MagicMock()
    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=[],
    )
    mock_monitor.snapshot.return_value = snapshot
    mock_monitor_class.return_value = mock_monitor

    # Führe aus
    exit_code = preview_script.main(["--config", str(sample_config_path), "--no-risk"])

    # Prüfe
    assert exit_code == 0
    # Risk-Limits sollten nicht geladen werden
    # (können wir nicht direkt prüfen, aber sollte keine Exception werfen)


@patch("scripts.preview_live_portfolio.load_config")
@patch("scripts.preview_live_portfolio.create_exchange_client")
@patch("scripts.preview_live_portfolio.LivePortfolioMonitor")
def test_main_json_output(
    mock_monitor_class,
    mock_create_client,
    mock_load_config,
    sample_config_path: Path,
    capsys,
):
    """Testet --json Flag."""
    import json

    # Mock Setup
    mock_cfg = MagicMock()
    mock_load_config.return_value = mock_cfg

    mock_client = Mock(spec=BaseBrokerClient)
    mock_create_client.return_value = mock_client

    mock_monitor = MagicMock()
    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=[],
    )
    mock_monitor.snapshot.return_value = snapshot
    mock_monitor_class.return_value = mock_monitor

    # Führe aus
    exit_code = preview_script.main(["--config", str(sample_config_path), "--json", "--no-risk"])

    # Prüfe
    assert exit_code == 0

    # Prüfe JSON-Ausgabe
    captured = capsys.readouterr()
    try:
        data = json.loads(captured.out)
        assert "as_of" in data
        assert "positions" in data
        assert "totals" in data
    except json.JSONDecodeError:
        pytest.fail("Ausgabe ist kein gültiges JSON")


def test_main_config_not_found(capsys):
    """Testet Fehlerbehandlung: Config-Datei nicht gefunden."""
    exit_code = preview_script.main(["--config", "nonexistent.toml"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "nicht gefunden" in captured.err.lower() or "not found" in captured.err.lower()


@patch("scripts.preview_live_portfolio.load_config")
@patch("scripts.preview_live_portfolio.create_exchange_client")
def test_main_exception_handling(
    mock_create_client,
    mock_load_config,
    sample_config_path: Path,
    capsys,
):
    """Testet Exception-Handling."""
    # Mock Setup: Exception werfen
    mock_load_config.side_effect = Exception("Test exception")

    exit_code = preview_script.main(["--config", str(sample_config_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Fehler" in captured.err or "error" in captured.err.lower()


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================


def test_create_exchange_client():
    """Testet create_exchange_client()."""
    mock_cfg = MagicMock()
    mock_cfg.get.side_effect = lambda key, default=None: {
        "general.starting_capital": 10000.0,
        "general.base_currency": "EUR",
    }.get(key, default)

    client = preview_script.create_exchange_client(mock_cfg)

    assert isinstance(client, BaseBrokerClient)


def test_format_portfolio_snapshot():
    """Testet format_portfolio_snapshot()."""
    from src.live.portfolio_monitor import LivePositionSnapshot

    positions = [
        LivePositionSnapshot(
            symbol="BTC/EUR",
            side="long",
            size=0.5,
            entry_price=28000.0,
            mark_price=29500.0,
            notional=14750.0,
        ),
    ]

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=positions,
    )

    output = preview_script.format_portfolio_snapshot(snapshot)

    assert "Live Portfolio Snapshot" in output
    assert "BTC/EUR" in output
    assert "14750" in output or "14750.0" in output








