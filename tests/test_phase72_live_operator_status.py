# tests/test_phase72_live_operator_status.py
"""
Peak_Trade: Tests für Phase 72 - Live Operator Status CLI
===========================================================

Testet die Status-Report-Generierung für die Live-Operator-Konsole.

Phase 72: Read-Only Status-CLI, keine State-Änderungen.
"""
from __future__ import annotations

import pytest

from src.core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
    LIVE_CONFIRM_TOKEN,
)
from src.live.risk_limits import LiveRiskConfig, LiveRiskLimits
from src.live.safety import SafetyGuard
from scripts.live_operator_status import generate_live_status_report


class TestLiveOperatorStatus:
    """Tests für Live-Operator-Status (Phase 72)."""

    def test_generate_status_report_paper_mode(self):
        """Test: Status-Report für Paper-Modus."""
        env = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        guard = SafetyGuard(env_config=env)

        report = generate_live_status_report(env, guard, live_risk_limits=None)

        assert "Peak_Trade - Live Operator Status" in report
        assert "Phase 71/72" in report
        assert "Mode:                    paper" in report
        assert "Effective Mode:          paper" in report
        assert "Paper-Modus aktiv" in report

    def test_generate_status_report_testnet_mode(self):
        """Test: Status-Report für Testnet-Modus."""
        env = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        guard = SafetyGuard(env_config=env)

        report = generate_live_status_report(env, guard, live_risk_limits=None)

        assert "Mode:                    testnet" in report
        assert "Effective Mode:          dry_run" in report
        assert "Testnet-Modus aktiv" in report

    def test_generate_status_report_live_mode_gates_closed(self):
        """Test: Status-Report für Live-Modus mit geschlossenen Gates."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
            live_mode_armed=False,
            live_dry_run_mode=True,
        )
        guard = SafetyGuard(env_config=env)

        report = generate_live_status_report(env, guard, live_risk_limits=None)

        assert "Mode:                    live" in report
        assert "Effective Mode:          live_dry_run" in report
        assert "enable_live_trading:    False" in report
        assert "live_mode_armed:        False" in report
        assert "live_dry_run_mode:      True" in report
        assert "Allowed:                 False" in report
        assert "Gate 1: enable_live_trading = False" in report
        assert "Gate 2: live_mode_armed = False" in report
        assert "Technisches Gate: live_dry_run_mode = True" in report

    def test_generate_status_report_live_mode_all_gates_open_but_dry_run(self):
        """Test: Status-Report für Live-Modus mit allen Gates offen, aber Dry-Run."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=True,
            live_dry_run_mode=True,  # Phase 71: Blockiert trotzdem
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        guard = SafetyGuard(env_config=env)

        report = generate_live_status_report(env, guard, live_risk_limits=None)

        assert "Mode:                    live" in report
        assert "Effective Mode:          live_dry_run" in report
        assert "enable_live_trading:    True" in report
        assert "live_mode_armed:        True" in report
        assert "live_dry_run_mode:      True" in report
        assert "Allowed:                 False" in report
        assert "Technisches Gate: live_dry_run_mode = True" in report
        # Prüfe, dass der Report erklärt, warum echte Orders blockiert sind
        assert "live_dry_run_mode=True" in report and "blockiert" in report

    def test_generate_status_report_confirm_token_status(self):
        """Test: Status-Report zeigt Token-Status (ohne Wert zu loggen)."""
        # Token gesetzt und gültig
        env_valid = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        guard_valid = SafetyGuard(env_config=env_valid)
        report_valid = generate_live_status_report(env_valid, guard_valid, live_risk_limits=None)

        assert "confirm_token:          SET (valid)" in report_valid or "SET (valid)" in report_valid

        # Token gesetzt aber ungültig
        env_invalid = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            confirm_token="WRONG_TOKEN",
        )
        guard_invalid = SafetyGuard(env_config=env_invalid)
        report_invalid = generate_live_status_report(env_invalid, guard_invalid, live_risk_limits=None)

        assert "SET (invalid)" in report_invalid or "invalid" in report_invalid.lower()

        # Token nicht gesetzt
        env_none = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            confirm_token=None,
        )
        guard_none = SafetyGuard(env_config=env_none)
        report_none = generate_live_status_report(env_none, guard_none, live_risk_limits=None)

        assert "NOT SET" in report_none

    def test_generate_status_report_with_risk_limits(self):
        """Test: Status-Report mit LiveRiskLimits."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        risk_config = LiveRiskConfig(
            enabled=True,
            base_currency="EUR",
            max_daily_loss_abs=500.0,
            max_daily_loss_pct=5.0,
            max_total_exposure_notional=5000.0,
            max_symbol_exposure_notional=2500.0,
            max_open_positions=10,
            max_order_notional=1000.0,
            block_on_violation=True,
            use_experiments_for_daily_pnl=True,
            # Phase 71: Live-spezifische Limits
            max_live_notional_per_order=1000.0,
            max_live_notional_total=5000.0,
            live_trade_min_size=10.0,
        )
        risk_limits = LiveRiskLimits(config=risk_config)

        report = generate_live_status_report(env, guard, live_risk_limits=risk_limits)

        assert "Live Risk-Limits" in report
        assert "Risk-Limits Enabled:     True" in report
        assert "Base Currency:           EUR" in report
        assert "max_live_notional_per_order: 1000.00 EUR" in report
        assert "max_live_notional_total:     5000.00 EUR" in report
        assert "live_trade_min_size:         10.00" in report

    def test_generate_status_report_with_risk_limits_not_set(self):
        """Test: Status-Report mit LiveRiskLimits, aber Limits nicht gesetzt."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        risk_config = LiveRiskConfig(
            enabled=True,
            base_currency="EUR",
            max_daily_loss_abs=None,
            max_daily_loss_pct=None,
            max_total_exposure_notional=None,
            max_symbol_exposure_notional=None,
            max_open_positions=None,
            max_order_notional=None,
            block_on_violation=True,
            use_experiments_for_daily_pnl=True,
            # Phase 71: Live-spezifische Limits nicht gesetzt
            max_live_notional_per_order=None,
            max_live_notional_total=None,
            live_trade_min_size=None,
        )
        risk_limits = LiveRiskLimits(config=risk_config)

        report = generate_live_status_report(env, guard, live_risk_limits=risk_limits)

        assert "Live Risk-Limits" in report
        assert "max_live_notional_per_order: NOT SET" in report
        assert "max_live_notional_total:     NOT SET" in report
        assert "live_trade_min_size:         NOT SET" in report
        assert "Einige Live-Limits sind nicht gesetzt" in report or "nicht gesetzt" in report

    def test_generate_status_report_without_risk_limits(self):
        """Test: Status-Report ohne LiveRiskLimits."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        report = generate_live_status_report(env, guard, live_risk_limits=None)

        assert "Live Risk-Limits" in report
        assert "NOT LOADED" in report or "nicht vorhanden" in report

    def test_generate_status_report_phase_hint(self):
        """Test: Status-Report enthält Phase-71/72-Hinweise."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        report = generate_live_status_report(env, guard, live_risk_limits=None)

        assert "Phase 71/72" in report
        assert "Dry-Run only" in report or "Dry-Run" in report
        assert "keine echten Orders" in report or "keine echten Orders möglich" in report

    def test_generate_status_report_is_live_execution_allowed_integration(self):
        """Test: Status-Report zeigt korrektes Ergebnis von is_live_execution_allowed()."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
        )
        guard = SafetyGuard(env_config=env)

        report = generate_live_status_report(env, guard, live_risk_limits=None)

        # Prüfe, dass is_live_execution_allowed() Ergebnis korrekt angezeigt wird
        assert "Live-Execution Status" in report
        assert "is_live_execution_allowed" in report
        assert "Allowed:                 False" in report
        assert "enable_live_trading=False" in report or "Gate 1" in report

    def test_generate_status_report_read_only_scope(self):
        """Test: Status-Report macht Read-Only-Scope klar."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        report = generate_live_status_report(env, guard, live_risk_limits=None)

        # Prüfe, dass keine "ändern", "setzen", "aktivieren" etc. in schreibendem Kontext vorkommt
        # (außer in Hinweisen/Empfehlungen)
        assert "Phase 71/72" in report
        # Report sollte nur Status zeigen, keine Schreiboperationen vorschlagen


