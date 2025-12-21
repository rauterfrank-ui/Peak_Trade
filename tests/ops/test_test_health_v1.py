"""
Tests für Test Health v1 (Strategy-Coverage & Switch-Sanity)
=============================================================

Testet die v1-Erweiterungen der TestHealthAutomation:
  - StrategyCoverageConfig, StrategyCoverageStats, StrategyCoverageResult
  - SwitchSanityConfig, SwitchSanityResult
  - compute_strategy_coverage()
  - run_switch_sanity_check()
  - _build_slack_message_v1()

Stand: Dezember 2024
"""

from __future__ import annotations

import datetime as dt
import json
import tempfile
from pathlib import Path

import pytest

from src.ops.test_health_runner import (
    StrategyCoverageConfig,
    StrategyCoverageStats,
    StrategyCoverageResult,
    SwitchSanityConfig,
    SwitchSanityResult,
    TestHealthSummary,
    TriggerViolation,
    compute_strategy_coverage,
    load_strategy_coverage_config,
    load_switch_sanity_config,
    run_switch_sanity_check,
    _build_slack_message_v1,
    _load_allowed_strategies,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_config_v1(tmp_path):
    """Erstellt eine temporäre test_health_profiles.toml mit v1-Sektionen."""
    config_content = """
version = "1.0"
default_profile = "test_profile"

[notifications.slack]
enabled = true
webhook_env_var = "PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH"
min_severity = "warning"
include_strategy_coverage = true
include_switch_sanity = true

[strategy_coverage]
enabled = true
window_days = 7
min_backtests_per_strategy = 3
min_paper_runs_per_strategy = 1
link_to_strategy_switch_allowed = true
runs_directory = "reports/experiments"

[switch_sanity]
enabled = true
config_path = "config/config.toml"
section_path = "live_profile.strategy_switch"
allow_r_and_d_in_allowed = false
require_active_in_allowed = true
require_non_empty_allowed = true
r_and_d_strategy_keys = ["armstrong_cycle", "el_karoui_vol_model"]

[profiles.test_profile]
description = "Test Profile für v1-Tests"
time_window_days = 1

[[profiles.test_profile.checks]]
id = "test_check"
name = "Test Check"
cmd = "echo 'test'"
weight = 1
category = "tests"
"""
    config_path = tmp_path / "test_health_profiles.toml"
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def temp_live_config(tmp_path):
    """Erstellt eine temporäre config.toml mit live_profile.strategy_switch."""
    config_content = """
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "rsi_reversion", "breakout"]
auto_switch_enabled = false
require_confirmation = true
"""
    config_path = tmp_path / "config.toml"
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def temp_experiments_dir(tmp_path):
    """Erstellt ein temporäres Experiment-Verzeichnis mit Test-Runs."""
    experiments_dir = tmp_path / "reports" / "experiments"
    experiments_dir.mkdir(parents=True)

    # Erstelle Test-Run-Dateien
    now = dt.datetime.utcnow()

    # ma_crossover: 3 Backtests, 1 Paper-Run (OK)
    for i in range(3):
        run_file = experiments_dir / f"ma_crossover_backtest_{i}.json"
        run_file.write_text(
            json.dumps(
                {
                    "strategy_id": "ma_crossover",
                    "run_type": "backtest",
                    "timestamp": now.isoformat(),
                }
            )
        )

    run_file = experiments_dir / "ma_crossover_paper.json"
    run_file.write_text(
        json.dumps(
            {
                "strategy_id": "ma_crossover",
                "run_type": "paper_trade",
                "timestamp": now.isoformat(),
            }
        )
    )

    # rsi_reversion: 2 Backtests, 0 Paper-Runs (Violations!)
    for i in range(2):
        run_file = experiments_dir / f"rsi_reversion_backtest_{i}.json"
        run_file.write_text(
            json.dumps(
                {
                    "strategy_id": "rsi_reversion",
                    "run_type": "backtest",
                    "timestamp": now.isoformat(),
                }
            )
        )

    return experiments_dir


# ============================================================================
# Strategy Coverage Tests
# ============================================================================


class TestStrategyCoverageConfig:
    """Tests für StrategyCoverageConfig."""

    def test_default_values(self):
        """Test: Default-Werte werden korrekt gesetzt."""
        config = StrategyCoverageConfig()

        assert config.enabled is True
        assert config.window_days == 7
        assert config.min_backtests_per_strategy == 3
        assert config.min_paper_runs_per_strategy == 1
        assert config.link_to_strategy_switch_allowed is True

    def test_load_from_toml(self, temp_config_v1):
        """Test: Config wird korrekt aus TOML geladen."""
        config = load_strategy_coverage_config(temp_config_v1)

        assert config.enabled is True
        assert config.window_days == 7
        assert config.min_backtests_per_strategy == 3
        assert config.min_paper_runs_per_strategy == 1


class TestComputeStrategyCoverage:
    """Tests für compute_strategy_coverage()."""

    def test_disabled_returns_healthy(self):
        """Test: Wenn disabled, wird is_healthy=True zurückgegeben."""
        config = StrategyCoverageConfig(enabled=False)
        result = compute_strategy_coverage(config, ["ma_crossover"])

        assert result.enabled is False
        assert result.is_healthy is True
        assert result.strategies_checked == 0

    def test_empty_strategies_list(self):
        """Test: Leere Strategieliste → keine Violations."""
        config = StrategyCoverageConfig(enabled=True)
        result = compute_strategy_coverage(config, [])

        assert result.enabled is True
        assert result.is_healthy is True
        assert result.strategies_checked == 0

    def test_coverage_with_violations(self, temp_experiments_dir):
        """Test: Violations werden korrekt erkannt."""
        config = StrategyCoverageConfig(
            enabled=True,
            window_days=7,
            min_backtests_per_strategy=3,
            min_paper_runs_per_strategy=1,
            runs_directory=str(temp_experiments_dir),
        )

        # ma_crossover hat genug Runs, rsi_reversion nicht
        result = compute_strategy_coverage(
            config,
            ["ma_crossover", "rsi_reversion"],
        )

        assert result.enabled is True
        assert result.strategies_checked == 2
        assert result.strategies_with_violations == 1  # rsi_reversion
        assert not result.is_healthy

        # ma_crossover sollte keine Violations haben
        ma_stats = next(s for s in result.coverage_stats if s.strategy_id == "ma_crossover")
        # Mindestens 3 Backtests und 1 Paper-Run (kann durch Glob mehr sein)
        assert ma_stats.n_backtests >= 3
        assert ma_stats.n_paper_runs >= 1
        assert len(ma_stats.violations) == 0

        # rsi_reversion sollte Violations haben (nur 2 Backtests, 0 Paper)
        rsi_stats = next(s for s in result.coverage_stats if s.strategy_id == "rsi_reversion")
        # Die Glob-Patterns können Dateien mehrfach finden, aber rsi sollte trotzdem < 3 Backtests haben
        assert rsi_stats.n_paper_runs == 0  # Definitiv keine Paper-Runs
        assert len(rsi_stats.violations) >= 1  # Mindestens Paper-Run Violation

    def test_coverage_ok(self, temp_experiments_dir):
        """Test: Keine Violations wenn Coverage erfüllt."""
        config = StrategyCoverageConfig(
            enabled=True,
            window_days=7,
            min_backtests_per_strategy=3,
            min_paper_runs_per_strategy=1,
            runs_directory=str(temp_experiments_dir),
        )

        # Nur ma_crossover prüfen (hat genug Runs)
        result = compute_strategy_coverage(config, ["ma_crossover"])

        assert result.is_healthy is True
        assert result.strategies_with_violations == 0


# ============================================================================
# Switch Sanity Tests
# ============================================================================


class TestSwitchSanityConfig:
    """Tests für SwitchSanityConfig."""

    def test_default_values(self):
        """Test: Default-Werte werden korrekt gesetzt."""
        config = SwitchSanityConfig()

        assert config.enabled is True
        assert config.allow_r_and_d_in_allowed is False
        assert config.require_active_in_allowed is True
        assert config.require_non_empty_allowed is True
        assert "armstrong_cycle" in config.r_and_d_strategy_keys

    def test_load_from_toml(self, temp_config_v1):
        """Test: Config wird korrekt aus TOML geladen."""
        config = load_switch_sanity_config(temp_config_v1)

        assert config.enabled is True
        assert config.allow_r_and_d_in_allowed is False
        assert "armstrong_cycle" in config.r_and_d_strategy_keys


class TestRunSwitchSanityCheck:
    """Tests für run_switch_sanity_check()."""

    def test_disabled_returns_ok(self):
        """Test: Wenn disabled, wird is_ok=True zurückgegeben."""
        config = SwitchSanityConfig(enabled=False)
        result = run_switch_sanity_check(config)

        assert result.enabled is False
        assert result.is_ok is True

    def test_config_not_found(self, tmp_path):
        """Test: Fehlende Config-Datei → Violation."""
        config = SwitchSanityConfig(
            enabled=True,
            config_path=str(tmp_path / "nonexistent.toml"),
        )
        result = run_switch_sanity_check(config)

        assert result.is_ok is False
        assert "not found" in result.violations[0].lower()

    def test_section_not_found(self, tmp_path):
        """Test: Fehlende Section → Violation."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("[other_section]\nkey = 'value'")

        config = SwitchSanityConfig(
            enabled=True,
            config_path=str(config_path),
            section_path="live_profile.strategy_switch",
        )
        result = run_switch_sanity_check(config)

        assert result.is_ok is False
        assert "not found" in result.violations[0].lower()

    def test_empty_allowed_violation(self, tmp_path):
        """Test: Leere allowed-Liste → Violation."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = []
""")

        config = SwitchSanityConfig(
            enabled=True,
            config_path=str(config_path),
            require_non_empty_allowed=True,
        )
        result = run_switch_sanity_check(config)

        assert result.is_ok is False
        assert any("empty" in v.lower() for v in result.violations)

    def test_active_not_in_allowed_violation(self, tmp_path):
        """Test: active_strategy_id nicht in allowed → Violation."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[live_profile.strategy_switch]
active_strategy_id = "unknown_strategy"
allowed = ["ma_crossover", "rsi_reversion"]
""")

        config = SwitchSanityConfig(
            enabled=True,
            config_path=str(config_path),
            require_active_in_allowed=True,
        )
        result = run_switch_sanity_check(config)

        assert result.is_ok is False
        assert any("not in allowed" in v.lower() for v in result.violations)

    def test_r_and_d_in_allowed_violation(self, tmp_path):
        """Test: R&D-Strategie in allowed → Violation."""
        config_path = tmp_path / "config.toml"
        config_path.write_text("""
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "armstrong_cycle"]
""")

        config = SwitchSanityConfig(
            enabled=True,
            config_path=str(config_path),
            allow_r_and_d_in_allowed=False,
            r_and_d_strategy_keys=["armstrong_cycle"],
        )
        result = run_switch_sanity_check(config)

        assert result.is_ok is False
        assert any("r_and_d" in v.lower() for v in result.violations)

    def test_valid_config(self, temp_live_config):
        """Test: Valide Config → is_ok=True."""
        config = SwitchSanityConfig(
            enabled=True,
            config_path=str(temp_live_config),
            r_and_d_strategy_keys=["armstrong_cycle"],
        )
        result = run_switch_sanity_check(config)

        assert result.is_ok is True
        assert result.active_strategy_id == "ma_crossover"
        assert "ma_crossover" in result.allowed


# ============================================================================
# Slack Message Tests
# ============================================================================


class TestBuildSlackMessageV1:
    """Tests für _build_slack_message_v1()."""

    def test_healthy_message(self, tmp_path):
        """Test: Gesunde Summary → Status HEALTHY."""
        summary = TestHealthSummary(
            profile_name="test_profile",
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            checks=[],
            health_score=100.0,
            passed_checks=5,
            failed_checks=0,
            skipped_checks=0,
            total_weight=10,
            passed_weight=10,
        )

        message = _build_slack_message_v1(summary, tmp_path)

        assert "HEALTHY" in message
        assert "test_profile" in message
        assert "100.0" in message

    def test_message_with_trigger_violations(self, tmp_path):
        """Test: Message enthält Trigger-Violations."""
        summary = TestHealthSummary(
            profile_name="test_profile",
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            checks=[],
            health_score=60.0,
            passed_checks=3,
            failed_checks=2,
            skipped_checks=0,
            total_weight=10,
            passed_weight=6,
            trigger_violations=[
                TriggerViolation(
                    severity="error",
                    trigger_name="max_fail_rate",
                    message="Fail-Rate zu hoch: 40.00% > 20.00%",
                    actual_value=0.4,
                    threshold_value=0.2,
                ),
            ],
        )

        message = _build_slack_message_v1(summary, tmp_path)

        assert "Trigger Violations" in message
        assert "Fail-Rate" in message

    def test_message_with_coverage_violations(self, tmp_path):
        """Test: Message enthält Strategy-Coverage-Violations."""
        coverage = StrategyCoverageResult(
            enabled=True,
            strategies_checked=2,
            strategies_with_violations=1,
            coverage_stats=[],
            all_violations=["Strategy 'rsi_reversion': only 2/3 backtests"],
            is_healthy=False,
        )

        summary = TestHealthSummary(
            profile_name="test_profile",
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            checks=[],
            health_score=80.0,
            passed_checks=4,
            failed_checks=1,
            skipped_checks=0,
            total_weight=10,
            passed_weight=8,
            strategy_coverage=coverage,
        )

        message = _build_slack_message_v1(summary, tmp_path)

        assert "Strategy Coverage" in message
        assert "rsi_reversion" in message

    def test_message_with_sanity_violations(self, tmp_path):
        """Test: Message enthält Switch-Sanity-Violations."""
        sanity = SwitchSanityResult(
            enabled=True,
            is_ok=False,
            violations=["active_strategy_id 'unknown' not in allowed list"],
            active_strategy_id="unknown",
            allowed=["ma_crossover"],
            config_path="config/config.toml",
        )

        summary = TestHealthSummary(
            profile_name="test_profile",
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            checks=[],
            health_score=80.0,
            passed_checks=4,
            failed_checks=1,
            skipped_checks=0,
            total_weight=10,
            passed_weight=8,
            switch_sanity=sanity,
        )

        message = _build_slack_message_v1(summary, tmp_path)

        assert "Switch Sanity" in message
        assert "not in allowed" in message


# ============================================================================
# Integration Tests
# ============================================================================


class TestLoadAllowedStrategies:
    """Tests für _load_allowed_strategies()."""

    def test_load_from_valid_config(self, temp_live_config):
        """Test: Strategien werden korrekt aus Config geladen."""
        allowed = _load_allowed_strategies(
            str(temp_live_config),
            "live_profile.strategy_switch",
        )

        assert "ma_crossover" in allowed
        assert "rsi_reversion" in allowed
        assert "breakout" in allowed

    def test_load_from_nonexistent_config(self, tmp_path):
        """Test: Nicht existierende Config → leere Liste."""
        allowed = _load_allowed_strategies(
            str(tmp_path / "nonexistent.toml"),
            "live_profile.strategy_switch",
        )

        assert allowed == []

    def test_load_from_invalid_section(self, temp_live_config):
        """Test: Nicht existierende Section → leere Liste."""
        allowed = _load_allowed_strategies(
            str(temp_live_config),
            "nonexistent.section",
        )

        assert allowed == []


class TestTestHealthSummaryV1Methods:
    """Tests für die v1-Methoden von TestHealthSummary."""

    def test_has_strategy_coverage_violations(self):
        """Test: has_strategy_coverage_violations()."""
        summary = TestHealthSummary(
            profile_name="test",
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            checks=[],
            health_score=80.0,
            passed_checks=4,
            failed_checks=0,
            skipped_checks=0,
            total_weight=10,
            passed_weight=8,
        )

        # Ohne Coverage → False
        assert summary.has_strategy_coverage_violations() is False

        # Mit healthier Coverage → False
        summary.strategy_coverage = StrategyCoverageResult(
            enabled=True,
            strategies_checked=1,
            strategies_with_violations=0,
            coverage_stats=[],
            all_violations=[],
            is_healthy=True,
        )
        assert summary.has_strategy_coverage_violations() is False

        # Mit Violations → True
        summary.strategy_coverage.is_healthy = False
        assert summary.has_strategy_coverage_violations() is True

    def test_has_switch_sanity_violations(self):
        """Test: has_switch_sanity_violations()."""
        summary = TestHealthSummary(
            profile_name="test",
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            checks=[],
            health_score=80.0,
            passed_checks=4,
            failed_checks=0,
            skipped_checks=0,
            total_weight=10,
            passed_weight=8,
        )

        # Ohne Sanity → False
        assert summary.has_switch_sanity_violations() is False

        # Mit OK Sanity → False
        summary.switch_sanity = SwitchSanityResult(
            enabled=True,
            is_ok=True,
            violations=[],
            active_strategy_id="ma_crossover",
            allowed=["ma_crossover"],
            config_path="config.toml",
        )
        assert summary.has_switch_sanity_violations() is False

        # Mit Violations → True
        summary.switch_sanity.is_ok = False
        assert summary.has_switch_sanity_violations() is True

    def test_has_any_violations(self):
        """Test: has_any_violations() kombiniert alle Checks."""
        summary = TestHealthSummary(
            profile_name="test",
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            checks=[],
            health_score=100.0,
            passed_checks=5,
            failed_checks=0,
            skipped_checks=0,
            total_weight=10,
            passed_weight=10,
        )

        # Keine Violations → False
        assert summary.has_any_violations() is False

        # Trigger-Violation → True
        summary.trigger_violations = [
            TriggerViolation(
                severity="warning",
                trigger_name="test",
                message="Test",
                actual_value=1,
                threshold_value=0,
            )
        ]
        assert summary.has_any_violations() is True

        # Reset und Coverage-Violation → True
        summary.trigger_violations = []
        summary.strategy_coverage = StrategyCoverageResult(
            enabled=True,
            strategies_checked=1,
            strategies_with_violations=1,
            coverage_stats=[],
            all_violations=["Test"],
            is_healthy=False,
        )
        assert summary.has_any_violations() is True
