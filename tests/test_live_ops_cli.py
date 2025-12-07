# tests/test_live_ops_cli.py
"""
Tests für Live-Ops CLI (Phase 51)
=================================

Tests für:
- CLI-Parsing & Basic-Flow
- Subcommands (orders, portfolio, health)
- JSON-Output
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import live_ops


# =============================================================================
# HELP TEXT TESTS
# =============================================================================


def test_live_ops_help(capsys):
    """Testet dass --help funktioniert und alle Subcommands zeigt."""
    try:
        live_ops.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    captured = capsys.readouterr()
    assert "Live-/Testnet Operations CLI" in captured.out
    assert "orders" in captured.out
    assert "portfolio" in captured.out
    assert "health" in captured.out


def test_live_ops_orders_help(capsys):
    """Testet dass 'orders --help' funktioniert."""
    try:
        live_ops.main(["orders", "--help"])
    except SystemExit as exc:
        assert exc.code == 0

    captured = capsys.readouterr()
    # Help-Text enthält Pflichtargument --signals
    assert "--signals" in captured.out
    assert "--config" in captured.out


def test_live_ops_portfolio_help(capsys):
    """Testet dass 'portfolio --help' funktioniert."""
    try:
        live_ops.main(["portfolio", "--help"])
    except SystemExit as exc:
        assert exc.code == 0

    captured = capsys.readouterr()
    # Help-Text enthält wesentliche Argumente
    assert "--config" in captured.out
    assert "--json" in captured.out
    assert "--no-risk" in captured.out


def test_live_ops_health_help(capsys):
    """Testet dass 'health --help' funktioniert."""
    try:
        live_ops.main(["health", "--help"])
    except SystemExit as exc:
        assert exc.code == 0

    captured = capsys.readouterr()
    # Help-Text enthält wesentliche Argumente
    assert "--config" in captured.out
    assert "--json" in captured.out


# =============================================================================
# HEALTH COMMAND TESTS
# =============================================================================


def test_live_ops_health_json_output(capsys, tmp_path):
    """Testet dass 'health --json' JSON-Output erzeugt."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[environment]
mode = "testnet"

[live_risk]
enabled = true
max_total_exposure_notional = 5000.0
max_symbol_exposure_notional = 2000.0

[live_alerts]
enabled = true
min_level = "warning"
sinks = ["log"]
"""
    )

    exit_code = live_ops.main(["health", "--config", str(config_file), "--json"])

    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert "config_ok" in data
    assert "exchange_ok" in data
    assert "alerts_enabled" in data
    assert "live_risk_ok" in data
    assert "overall_status" in data
    assert data["overall_status"] in ["OK", "DEGRADED", "FAIL"]


def test_live_ops_health_text_output(capsys, tmp_path):
    """Testet dass 'health' Text-Output erzeugt."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[environment]
mode = "testnet"

[live_risk]
enabled = true

[live_alerts]
enabled = true
"""
    )

    exit_code = live_ops.main(["health", "--config", str(config_file)])

    assert exit_code == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "Health Check" in output
    assert "Config:" in output
    assert "Exchange:" in output
    assert "Alerts:" in output
    assert "Live Risk:" in output
    assert "Overall Status:" in output


def test_live_ops_health_missing_config(capsys):
    """Testet dass 'health' bei fehlender Config korrekt reagiert."""
    exit_code = live_ops.main(["health", "--config", "nonexistent_config.toml"])

    # Sollte nicht crashen, aber FAIL-Status haben
    assert exit_code == 1
    captured = capsys.readouterr()
    output = captured.out

    assert "Config:" in output or "FAIL" in output


# =============================================================================
# PORTFOLIO COMMAND TESTS
# =============================================================================


@patch("scripts.live_ops.create_exchange_client")
@patch("scripts.live_ops.LivePortfolioMonitor")
def test_live_ops_portfolio_json_mode(mock_monitor_class, mock_create_client, capsys, tmp_path):
    """Testet dass 'portfolio --json' JSON-Output erzeugt."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[environment]
mode = "testnet"

[general]
starting_capital = 10000.0
base_currency = "EUR"
"""
    )

    # Mock Portfolio-Monitor
    mock_snapshot = MagicMock()
    mock_snapshot.as_of.isoformat.return_value = "2025-01-15T10:30:00+00:00"
    mock_snapshot.positions = []
    mock_snapshot.num_open_positions = 0
    mock_snapshot.total_notional = 0.0
    mock_snapshot.total_unrealized_pnl = 0.0
    mock_snapshot.total_realized_pnl = 0.0
    mock_snapshot.symbol_notional = {}

    mock_monitor = MagicMock()
    mock_monitor.snapshot.return_value = mock_snapshot
    mock_monitor_class.return_value = mock_monitor

    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    exit_code = live_ops.main(["portfolio", "--config", str(config_file), "--json"])

    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert "as_of" in data
    assert "positions" in data
    assert "totals" in data


@patch("scripts.live_ops.create_exchange_client")
@patch("scripts.live_ops.LivePortfolioMonitor")
def test_live_ops_portfolio_no_risk(mock_monitor_class, mock_create_client, capsys, tmp_path):
    """Testet dass 'portfolio --no-risk' ohne Risk-Check läuft."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[environment]
mode = "testnet"

[general]
starting_capital = 10000.0
"""
    )

    mock_snapshot = MagicMock()
    mock_snapshot.as_of.strftime.return_value = "2025-01-15 10:30:00"
    mock_snapshot.positions = []
    mock_snapshot.num_open_positions = 0
    mock_snapshot.total_notional = 0.0
    mock_snapshot.total_unrealized_pnl = 0.0
    mock_snapshot.total_realized_pnl = 0.0
    mock_snapshot.symbol_notional = {}

    mock_monitor = MagicMock()
    mock_monitor.snapshot.return_value = mock_snapshot
    mock_monitor_class.return_value = mock_monitor

    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    exit_code = live_ops.main(["portfolio", "--config", str(config_file), "--no-risk"])

    assert exit_code == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "Portfolio Snapshot" in output or "positions" in output.lower()


# =============================================================================
# ORDERS COMMAND TESTS
# =============================================================================


@patch("scripts.live_ops.run_live_risk_check")
@patch("scripts.live_ops.load_signals_csv")
def test_live_ops_orders_json_mode(mock_load_signals, mock_risk_check, capsys, tmp_path):
    """Testet dass 'orders --json' JSON-Output erzeugt."""
    import pandas as pd

    # Mock Signals
    df_signals = pd.DataFrame({
        "symbol": ["BTC/EUR"],
        "direction": [1.0],
        "as_of": ["2025-01-15T10:00:00"],
        "strategy_key": ["test_strategy"],
        "run_name": ["test_run"],
    })
    mock_load_signals.return_value = df_signals

    # Mock Risk-Check
    mock_result = MagicMock()
    mock_result.allowed = True
    mock_result.reasons = []
    mock_result.metrics = {}
    mock_risk_check.return_value = mock_result

    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[environment]
mode = "testnet"
"""
    )

    signals_file = tmp_path / "signals.csv"
    signals_file.write_text("symbol,direction,as_of,strategy_key,run_name\nBTC/EUR,1.0,2025-01-15T10:00:00,test,test")

    exit_code = live_ops.main([
        "orders",
        "--signals", str(signals_file),
        "--config", str(config_file),
        "--json",
    ])

    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert "preview_name" in data
    assert "num_signals" in data
    assert "num_orders" in data
    assert "orders" in data


@patch("scripts.live_ops.run_live_risk_check")
@patch("scripts.live_ops.load_signals_csv")
def test_live_ops_orders_text_mode(mock_load_signals, mock_risk_check, capsys, tmp_path):
    """Testet dass 'orders' Text-Output erzeugt."""
    import pandas as pd

    df_signals = pd.DataFrame({
        "symbol": ["BTC/EUR"],
        "direction": [1.0],
        "as_of": ["2025-01-15T10:00:00"],
        "strategy_key": ["test_strategy"],
        "run_name": ["test_run"],
    })
    mock_load_signals.return_value = df_signals

    mock_result = MagicMock()
    mock_result.allowed = True
    mock_result.reasons = []
    mock_result.metrics = {}
    mock_risk_check.return_value = mock_result

    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[environment]
mode = "testnet"
"""
    )

    signals_file = tmp_path / "signals.csv"
    signals_file.write_text("symbol,direction,as_of,strategy_key,run_name\nBTC/EUR,1.0,2025-01-15T10:00:00,test,test")

    exit_code = live_ops.main([
        "orders",
        "--signals", str(signals_file),
        "--config", str(config_file),
    ])

    assert exit_code == 0
    captured = capsys.readouterr()
    output = captured.out

    assert "Order Preview" in output
    assert "Orders generiert" in output or "orders" in output.lower()


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


def test_live_ops_unknown_command():
    """Testet dass unbekannte Commands einen Fehler erzeugen."""
    try:
        live_ops.main(["unknown_command"])
        assert False, "Should have raised SystemExit"
    except SystemExit as exc:
        assert exc.code == 2


def test_live_ops_orders_missing_signals():
    """Testet dass 'orders' ohne --signals einen Fehler erzeugt."""
    try:
        live_ops.main(["orders", "--config", "config/config.toml"])
        assert False, "Should have raised SystemExit"
    except SystemExit as exc:
        # argparse exits with code 2 for missing required arguments
        assert exc.code == 2


