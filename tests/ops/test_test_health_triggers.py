"""
Tests für Test Health Triggers
===============================

Testet die erweiterte Trigger-Logik der TestHealthAutomation:
  - TestHealthTriggers dataclass
  - TestHealthStats dataclass
  - evaluate_triggers() Funktion
  - Trigger-Config-Loading aus TOML

Stand: Dezember 2024
"""

from __future__ import annotations

from src.ops.test_health_runner import (
    TestHealthStats,
    TestHealthTriggers,
    TriggerViolation,
    evaluate_triggers,
    load_test_health_profile,
)


class TestEvaluateTriggers:
    """Tests für evaluate_triggers()"""

    def test_no_violations_when_all_ok(self):
        """Test: Keine Violations wenn alle Bedingungen erfüllt."""
        triggers = TestHealthTriggers(
            min_total_runs=5,
            max_fail_rate=0.2,
            max_consecutive_failures=3,
            max_hours_since_last_run=24,
            require_critical_green=True,
        )

        stats = TestHealthStats(
            total_runs=10,
            failed_runs=1,  # 10% Fail-Rate < 20%
            max_consecutive_failures=2,  # < 3
            hours_since_last_run=12.0,  # < 24
            all_critical_groups_green=True,
        )

        violations = evaluate_triggers(triggers, stats)
        assert len(violations) == 0

    def test_min_total_runs_violation(self):
        """Test: Violation bei zu wenigen Runs."""
        triggers = TestHealthTriggers(min_total_runs=5)

        stats = TestHealthStats(
            total_runs=3,  # < 5
            failed_runs=0,
            max_consecutive_failures=0,
            hours_since_last_run=None,
            all_critical_groups_green=True,
        )

        violations = evaluate_triggers(triggers, stats)
        assert len(violations) == 1
        assert violations[0].trigger_name == "min_total_runs"
        assert violations[0].severity == "warning"
        assert violations[0].actual_value == 3
        assert violations[0].threshold_value == 5

    def test_max_fail_rate_violation(self):
        """Test: Violation bei zu hoher Fail-Rate."""
        triggers = TestHealthTriggers(max_fail_rate=0.2)  # max. 20%

        stats = TestHealthStats(
            total_runs=10,
            failed_runs=3,  # 30% > 20%
            max_consecutive_failures=0,
            hours_since_last_run=None,
            all_critical_groups_green=True,
        )

        violations = evaluate_triggers(triggers, stats)
        assert len(violations) == 1
        assert violations[0].trigger_name == "max_fail_rate"
        assert violations[0].severity == "error"
        assert violations[0].actual_value == 0.3

    def test_max_consecutive_failures_violation(self):
        """Test: Violation bei zu vielen Failures in Folge."""
        triggers = TestHealthTriggers(max_consecutive_failures=3)

        stats = TestHealthStats(
            total_runs=10,
            failed_runs=4,
            max_consecutive_failures=5,  # > 3
            hours_since_last_run=None,
            all_critical_groups_green=True,
        )

        violations = evaluate_triggers(triggers, stats)
        assert len(violations) == 1
        assert violations[0].trigger_name == "max_consecutive_failures"
        assert violations[0].severity == "error"
        assert violations[0].actual_value == 5
        assert violations[0].threshold_value == 3

    def test_max_hours_since_last_run_violation(self):
        """Test: Violation bei zu lange kein Run."""
        triggers = TestHealthTriggers(max_hours_since_last_run=24)

        stats = TestHealthStats(
            total_runs=5,
            failed_runs=0,
            max_consecutive_failures=0,
            hours_since_last_run=36.0,  # > 24
            all_critical_groups_green=True,
        )

        violations = evaluate_triggers(triggers, stats)
        assert len(violations) == 1
        assert violations[0].trigger_name == "max_hours_since_last_run"
        assert violations[0].severity == "warning"
        assert violations[0].actual_value == 36.0
        assert violations[0].threshold_value == 24

    def test_require_critical_green_violation(self):
        """Test: Violation bei nicht-grünen kritischen Gruppen."""
        triggers = TestHealthTriggers(require_critical_green=True)

        stats = TestHealthStats(
            total_runs=10,
            failed_runs=0,
            max_consecutive_failures=0,
            hours_since_last_run=None,
            all_critical_groups_green=False,  # Nicht grün!
        )

        violations = evaluate_triggers(triggers, stats)
        assert len(violations) == 1
        assert violations[0].trigger_name == "require_critical_green"
        assert violations[0].severity == "error"
        assert violations[0].actual_value is False
        assert violations[0].threshold_value is True

    def test_multiple_violations(self):
        """Test: Mehrere Violations gleichzeitig."""
        triggers = TestHealthTriggers(
            min_total_runs=10,
            max_fail_rate=0.1,
            max_consecutive_failures=2,
        )

        stats = TestHealthStats(
            total_runs=5,  # < 10
            failed_runs=2,  # 40% > 10%
            max_consecutive_failures=3,  # > 2
            hours_since_last_run=None,
            all_critical_groups_green=True,
        )

        violations = evaluate_triggers(triggers, stats)
        assert len(violations) == 3

        # Prüfe ob alle 3 Trigger verletzt wurden
        trigger_names = [v.trigger_name for v in violations]
        assert "min_total_runs" in trigger_names
        assert "max_fail_rate" in trigger_names
        assert "max_consecutive_failures" in trigger_names

    def test_max_hours_disabled_when_none(self):
        """Test: max_hours_since_last_run wird ignoriert wenn None."""
        triggers = TestHealthTriggers(max_hours_since_last_run=None)

        stats = TestHealthStats(
            total_runs=5,
            failed_runs=0,
            max_consecutive_failures=0,
            hours_since_last_run=9999.0,  # Sehr lange
            all_critical_groups_green=True,
        )

        violations = evaluate_triggers(triggers, stats)
        assert len(violations) == 0

    def test_zero_total_runs_no_fail_rate_violation(self):
        """Test: Bei 0 Runs keine fail_rate-Violation (Division by zero)."""
        triggers = TestHealthTriggers(max_fail_rate=0.1)

        stats = TestHealthStats(
            total_runs=0,
            failed_runs=0,
            max_consecutive_failures=0,
            hours_since_last_run=None,
            all_critical_groups_green=True,
        )

        violations = evaluate_triggers(triggers, stats)
        # Nur min_total_runs-Violation (falls konfiguriert), keine fail_rate
        fail_rate_violations = [
            v for v in violations if v.trigger_name == "max_fail_rate"
        ]
        assert len(fail_rate_violations) == 0


class TestLoadTestHealthProfileWithTriggers:
    """Tests für load_test_health_profile() mit Trigger-Config."""

    def test_load_profile_with_triggers(self, tmp_path):
        """Test: Profil mit Trigger-Config laden."""
        config_content = """
version = "0.1"
default_profile = "test_profile"

[profiles.test_profile]
description = "Test Profile mit Triggers"
time_window_days = 7

  [profiles.test_profile.triggers]
  min_total_runs = 5
  max_fail_rate = 0.20
  max_consecutive_failures = 3
  max_hours_since_last_run = 168
  require_critical_green = true

[[profiles.test_profile.checks]]
id = "test_check"
name = "Test Check"
cmd = "echo 'test'"
weight = 1
category = "tests"
"""
        config_path = tmp_path / "test_health_profiles.toml"
        config_path.write_text(config_content)

        checks, triggers = load_test_health_profile(config_path, "test_profile")

        # Checks validieren
        assert len(checks) == 1
        assert checks[0].id == "test_check"

        # Triggers validieren
        assert triggers.min_total_runs == 5
        assert triggers.max_fail_rate == 0.20
        assert triggers.max_consecutive_failures == 3
        assert triggers.max_hours_since_last_run == 168
        assert triggers.require_critical_green is True

    def test_load_profile_without_triggers(self, tmp_path):
        """Test: Profil ohne Trigger-Config → Default-Triggers."""
        config_content = """
version = "0.1"
default_profile = "test_profile"

[profiles.test_profile]
description = "Test Profile ohne Triggers"
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

        checks, triggers = load_test_health_profile(config_path, "test_profile")

        # Default-Triggers validieren
        assert triggers.min_total_runs == 0
        assert triggers.max_fail_rate == 1.0
        assert triggers.max_consecutive_failures == 999999
        assert triggers.max_hours_since_last_run is None
        assert triggers.require_critical_green is False

    def test_load_profile_partial_triggers(self, tmp_path):
        """Test: Profil mit teilweiser Trigger-Config → Rest Defaults."""
        config_content = """
version = "0.1"
default_profile = "test_profile"

[profiles.test_profile]
description = "Test Profile mit partiellen Triggers"
time_window_days = 1

  [profiles.test_profile.triggers]
  min_total_runs = 10
  max_fail_rate = 0.15
  # max_consecutive_failures fehlt → Default
  # max_hours_since_last_run fehlt → Default

[[profiles.test_profile.checks]]
id = "test_check"
name = "Test Check"
cmd = "echo 'test'"
weight = 1
category = "tests"
"""
        config_path = tmp_path / "test_health_profiles.toml"
        config_path.write_text(config_content)

        checks, triggers = load_test_health_profile(config_path, "test_profile")

        # Validiere gemischte Trigger
        assert triggers.min_total_runs == 10  # Custom
        assert triggers.max_fail_rate == 0.15  # Custom
        assert triggers.max_consecutive_failures == 999999  # Default
        assert triggers.max_hours_since_last_run is None  # Default
        assert triggers.require_critical_green is False  # Default


class TestTriggerViolationDataclass:
    """Tests für TriggerViolation dataclass."""

    def test_create_violation(self):
        """Test: Violation-Objekt erstellen."""
        violation = TriggerViolation(
            severity="error",
            trigger_name="max_fail_rate",
            message="Fail-Rate zu hoch: 30.00% > 20.00%",
            actual_value=0.3,
            threshold_value=0.2,
        )

        assert violation.severity == "error"
        assert violation.trigger_name == "max_fail_rate"
        assert "30.00%" in violation.message
        assert violation.actual_value == 0.3
        assert violation.threshold_value == 0.2
