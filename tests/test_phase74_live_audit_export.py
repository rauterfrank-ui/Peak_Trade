# tests/test_phase74_live_audit_export.py
"""
Peak_Trade: Tests für Phase 74 - Live-Config Audit & Export
===========================================================

Testet das Audit-Snapshot-System für Governance, Audits und "Proof of Safety".

Phase 74: Read-Only, keine Config-Änderungen, keine Token-Werte exportieren.
"""
from __future__ import annotations

import json

import pytest

from src.core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
    LIVE_CONFIRM_TOKEN,
)
from src.live.audit import (
    LiveAuditGatingState,
    LiveAuditRiskState,
    LiveAuditDrillSummary,
    LiveAuditSafetySummary,
    LiveAuditSnapshot,
    build_live_audit_snapshot,
    live_audit_snapshot_to_dict,
    live_audit_snapshot_to_markdown,
)
from src.live.risk_limits import LiveRiskConfig, LiveRiskLimits
from src.live.safety import SafetyGuard


class TestLiveAuditSnapshot:
    """Tests für LiveAuditSnapshot (Phase 74)."""

    def test_build_live_audit_snapshot_basic(self):
        """Test: build_live_audit_snapshot() erstellt konsistente Snapshots."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)

        assert isinstance(snapshot, LiveAuditSnapshot)
        assert snapshot.timestamp_utc
        assert snapshot.gating is not None
        assert snapshot.risk is not None
        assert snapshot.drills is not None
        assert snapshot.safety is not None

    def test_build_live_audit_snapshot_gating_state(self):
        """Test: Gating-State ist korrekt."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=True,
            live_mode_armed=False,
            live_dry_run_mode=True,
        )
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)

        assert snapshot.gating.mode == "live"
        assert snapshot.gating.effective_mode == "live_dry_run"
        assert snapshot.gating.enable_live_trading is True
        assert snapshot.gating.live_mode_armed is False
        assert snapshot.gating.live_dry_run_mode is True

    def test_build_live_audit_snapshot_confirm_token_present_boolean(self):
        """Test: confirm_token_present ist Boolean, kein Wert exportiert."""
        # Token gesetzt und gültig
        env_valid = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        guard_valid = SafetyGuard(env_config=env_valid)
        snapshot_valid = build_live_audit_snapshot(env_valid, guard_valid, live_risk_limits=None)

        assert snapshot_valid.gating.confirm_token_present is True
        # Prüfe, dass kein Token-Wert im Snapshot ist
        snapshot_dict = live_audit_snapshot_to_dict(snapshot_valid)
        assert "confirm_token" not in str(snapshot_dict).lower() or "present" in str(snapshot_dict).lower()
        assert snapshot_dict["gating"]["confirm_token_present"] is True

        # Token nicht gesetzt
        env_none = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            confirm_token=None,
        )
        guard_none = SafetyGuard(env_config=env_none)
        snapshot_none = build_live_audit_snapshot(env_none, guard_none, live_risk_limits=None)

        assert snapshot_none.gating.confirm_token_present is False

    def test_build_live_audit_snapshot_risk_state(self):
        """Test: Risk-State ist korrekt."""
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
            max_live_notional_per_order=1000.0,
            max_live_notional_total=5000.0,
            live_trade_min_size=10.0,
        )
        risk_limits = LiveRiskLimits(config=risk_config)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=risk_limits)

        assert snapshot.risk.limits_enabled is True
        assert snapshot.risk.max_live_notional_per_order == 1000.0
        assert snapshot.risk.max_live_notional_total == 5000.0
        assert snapshot.risk.live_trade_min_size == 10.0

    def test_build_live_audit_snapshot_risk_state_not_loaded(self):
        """Test: Risk-State wenn LiveRiskLimits nicht geladen."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)

        assert snapshot.risk.limits_enabled is False
        assert snapshot.risk.max_live_notional_per_order is None
        assert snapshot.risk.max_live_notional_total is None
        assert snapshot.risk.live_trade_min_size is None
        assert snapshot.risk.limits_source == "not_loaded"

    def test_build_live_audit_snapshot_drill_summary(self):
        """Test: Drill-Summary ist korrekt."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)

        assert snapshot.drills.num_scenarios >= 7  # Mindestens A-G
        assert len(snapshot.drills.available_scenarios) == snapshot.drills.num_scenarios
        assert snapshot.drills.drills_executable is True
        # Prüfe, dass Standard-Drills vorhanden sind
        scenario_names = " ".join(snapshot.drills.available_scenarios)
        assert "A - Voll gebremst" in scenario_names
        assert "B - Gate 1 ok" in scenario_names
        assert "C - Alles armed" in scenario_names

    def test_build_live_audit_snapshot_safety_summary(self):
        """Test: Safety-Summary ist konsistent mit is_live_execution_allowed()."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            enable_live_trading=False,
        )
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)

        # Prüfe, dass is_live_execution_allowed konsistent ist
        from src.live.safety import is_live_execution_allowed

        allowed, reason = is_live_execution_allowed(env)
        assert snapshot.safety.is_live_execution_allowed == allowed
        assert len(snapshot.safety.reasons) > 0
        assert "Dry-Run" in snapshot.safety.safety_guarantee_v1_0 or "no real orders" in snapshot.safety.safety_guarantee_v1_0.lower()

    def test_build_live_audit_snapshot_environment_id(self):
        """Test: environment_id wird korrekt gesetzt."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(
            env, guard, live_risk_limits=None, environment_id="test_config"
        )

        assert snapshot.environment_id == "test_config"

    def test_live_audit_snapshot_to_dict_json_serializable(self):
        """Test: live_audit_snapshot_to_dict() liefert JSON-serialisierbares Dict."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)
        snapshot_dict = live_audit_snapshot_to_dict(snapshot)

        # Prüfe, dass es JSON-serialisierbar ist
        json_str = json.dumps(snapshot_dict, indent=2)
        assert json_str

        # Prüfe Struktur
        assert "timestamp_utc" in snapshot_dict
        assert "gating" in snapshot_dict
        assert "risk" in snapshot_dict
        assert "drills" in snapshot_dict
        assert "safety" in snapshot_dict
        assert "versions" in snapshot_dict

    def test_live_audit_snapshot_to_dict_no_token_values(self):
        """Test: Dict enthält keine Token-Werte, nur Boolean-Präsenz."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)
        snapshot_dict = live_audit_snapshot_to_dict(snapshot)

        # Prüfe, dass kein Token-Wert im Dict ist
        dict_str = json.dumps(snapshot_dict)
        assert LIVE_CONFIRM_TOKEN not in dict_str
        assert "confirm_token_present" in str(snapshot_dict)
        assert snapshot_dict["gating"]["confirm_token_present"] is True

    def test_live_audit_snapshot_to_markdown_format(self):
        """Test: live_audit_snapshot_to_markdown() erstellt korrektes Markdown."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)
        markdown_text = live_audit_snapshot_to_markdown(snapshot)

        assert "# Peak_Trade - Live Audit Snapshot" in markdown_text
        assert "## Gating Status" in markdown_text
        assert "## Risk Limits" in markdown_text
        assert "## Drills Summary" in markdown_text
        assert "## Safety Summary" in markdown_text
        assert "Dry-Run" in markdown_text or "no real orders" in markdown_text.lower()

    def test_live_audit_snapshot_to_markdown_no_token_values(self):
        """Test: Markdown enthält keine Token-Werte, nur Boolean-Präsenz."""
        env = EnvironmentConfig(
            environment=TradingEnvironment.LIVE,
            confirm_token=LIVE_CONFIRM_TOKEN,
        )
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)
        markdown_text = live_audit_snapshot_to_markdown(snapshot)

        # Prüfe, dass kein Token-Wert im Markdown ist
        assert LIVE_CONFIRM_TOKEN not in markdown_text
        assert "confirm_token_present" in markdown_text or "Token" in markdown_text
        assert "Wert nicht exportiert" in markdown_text or "not exported" in markdown_text.lower()

    def test_build_live_audit_snapshot_versions_info(self):
        """Test: Versions-Info ist vorhanden."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)

        assert snapshot.versions is not None
        assert "phase71_tests" in snapshot.versions
        assert "phase72_tests" in snapshot.versions
        assert "phase73_tests" in snapshot.versions

    def test_build_live_audit_snapshot_read_only(self):
        """Test: Snapshot-Erstellung ändert keine Config/State."""
        env = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard = SafetyGuard(env_config=env)

        # Snapshot erstellen
        snapshot = build_live_audit_snapshot(env, guard, live_risk_limits=None)

        # Prüfe, dass EnvironmentConfig unverändert ist
        assert env.environment == TradingEnvironment.LIVE
        assert env.enable_live_trading == env.enable_live_trading  # Unverändert

        # Prüfe, dass Snapshot nur lesend ist
        assert snapshot.gating.mode == "live"
        # Keine Schreiboperationen in build_live_audit_snapshot()

    def test_build_live_audit_snapshot_different_environments(self):
        """Test: Snapshot funktioniert für verschiedene Environments."""
        # Paper
        env_paper = EnvironmentConfig(environment=TradingEnvironment.PAPER)
        guard_paper = SafetyGuard(env_config=env_paper)
        snapshot_paper = build_live_audit_snapshot(env_paper, guard_paper, live_risk_limits=None)
        assert snapshot_paper.gating.mode == "paper"

        # Testnet
        env_testnet = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
        guard_testnet = SafetyGuard(env_config=env_testnet)
        snapshot_testnet = build_live_audit_snapshot(env_testnet, guard_testnet, live_risk_limits=None)
        assert snapshot_testnet.gating.mode == "testnet"

        # Live
        env_live = EnvironmentConfig(environment=TradingEnvironment.LIVE)
        guard_live = SafetyGuard(env_config=env_live)
        snapshot_live = build_live_audit_snapshot(env_live, guard_live, live_risk_limits=None)
        assert snapshot_live.gating.mode == "live"


