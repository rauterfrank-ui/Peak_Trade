# tests/ops/test_test_health_runner_verification.py
"""
P0: Deterministic verification tests for test_health_runner and governance health profiles.

No network, no external tools. Asserts that:
- Profile loads from repo config (known profile yields checks + triggers).
- Profile -> selected checks are stable (same profile twice yields same check ids).
- Runner refuses unknown profile (ValueError with message).
- aggregate_health emits deterministic summary (fixed results -> deterministic scores/counts).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from src.ops.test_health_runner import (
    TestCheckResult,
    TestHealthSummary,
    aggregate_health,
    load_test_health_profile,
)

# Repo config path (relative to project root)
REPO_PROFILES_PATH = Path("config/test_health_profiles.toml")


def _repo_config_path() -> Path:
    """Path to config/test_health_profiles.toml from project root."""
    root = Path(__file__).resolve().parents[2]
    return root / REPO_PROFILES_PATH


class TestProfileLoads:
    """Profile loads from repo config."""

    def test_known_profile_loads(self) -> None:
        """Known profile (governance_strategy_switch_sanity) loads and has checks + triggers."""
        config_path = _repo_config_path()
        if not config_path.exists():
            pytest.skip(f"Repo config not found: {config_path}")
        checks, triggers = load_test_health_profile(
            config_path, "governance_strategy_switch_sanity"
        )
        assert len(checks) >= 1
        assert all(hasattr(c, "id") and c.id for c in checks)
        assert triggers is not None
        assert hasattr(triggers, "max_fail_rate")

    def test_daily_quick_profile_loads(self) -> None:
        """Default profile daily_quick loads and has checks."""
        config_path = _repo_config_path()
        if not config_path.exists():
            pytest.skip(f"Repo config not found: {config_path}")
        checks, triggers = load_test_health_profile(config_path, "daily_quick")
        assert len(checks) >= 1
        assert any(c.id == "pytest_smoke_quick" for c in checks)


class TestProfileStable:
    """Profile -> selected check ids are stable across loads."""

    def test_same_profile_same_check_ids_twice(self) -> None:
        """Loading same profile twice yields same check ids in same order."""
        config_path = _repo_config_path()
        if not config_path.exists():
            pytest.skip(f"Repo config not found: {config_path}")
        checks1, _ = load_test_health_profile(config_path, "governance_strategy_switch_sanity")
        checks2, _ = load_test_health_profile(config_path, "governance_strategy_switch_sanity")
        ids1 = [c.id for c in checks1]
        ids2 = [c.id for c in checks2]
        assert ids1 == ids2


class TestUnknownProfileRefused:
    """Runner refuses unknown profile."""

    def test_unknown_profile_raises_value_error(self) -> None:
        """load_test_health_profile(unknown) raises ValueError with message."""
        config_path = _repo_config_path()
        if not config_path.exists():
            pytest.skip(f"Repo config not found: {config_path}")
        with pytest.raises(ValueError, match="nicht gefunden"):
            load_test_health_profile(config_path, "nonexistent_profile_xyz")

    def test_unknown_profile_message_lists_available(self) -> None:
        """Error message contains profile name and available list."""
        config_path = _repo_config_path()
        if not config_path.exists():
            pytest.skip(f"Repo config not found: {config_path}")
        with pytest.raises(ValueError) as exc_info:
            load_test_health_profile(config_path, "nonexistent_profile_xyz")
        msg = str(exc_info.value)
        assert "nonexistent_profile_xyz" in msg
        assert "Verfügbar" in msg or "available" in msg.lower()


class TestAggregateHealthDeterministic:
    """aggregate_health emits deterministic summary for fixed results."""

    @staticmethod
    def _make_result(
        check_id: str,
        status: str,
        weight: int = 1,
        started_at: dt.datetime | None = None,
        finished_at: dt.datetime | None = None,
    ) -> TestCheckResult:
        """Build a TestCheckResult with fixed timestamps for determinism."""
        t1 = started_at or dt.datetime(2025, 1, 1, 12, 0, 0)
        t2 = finished_at or dt.datetime(2025, 1, 1, 12, 0, 5)
        return TestCheckResult(
            id=check_id,
            name=check_id,
            category="tests",
            cmd="echo ok",
            status=status,
            weight=weight,
            started_at=t1,
            finished_at=t2,
            duration_seconds=5.0,
            return_code=0 if status == "PASS" else 1,
        )

    def test_empty_results_deterministic_summary(self) -> None:
        """aggregate_health(profile_name, []) yields summary with score 0 and zero counts."""
        summary = aggregate_health("test_profile", [])
        assert summary.profile_name == "test_profile"
        assert summary.health_score == 0.0
        assert summary.passed_checks == 0
        assert summary.failed_checks == 0
        assert summary.skipped_checks == 0
        assert summary.total_weight == 0
        assert summary.passed_weight == 0
        assert summary.checks == []

    def test_fixed_results_deterministic_scores(self) -> None:
        """aggregate_health with fixed results yields deterministic health_score and counts."""
        t0 = dt.datetime(2025, 1, 1, 12, 0, 0)
        t1 = dt.datetime(2025, 1, 1, 12, 0, 1)
        results = [
            self._make_result("a", "PASS", weight=2, started_at=t0, finished_at=t1),
            self._make_result("b", "FAIL", weight=1, started_at=t0, finished_at=t1),
            self._make_result("c", "PASS", weight=1, started_at=t0, finished_at=t1),
        ]
        summary = aggregate_health("deterministic_profile", results)
        assert summary.profile_name == "deterministic_profile"
        assert summary.passed_checks == 2
        assert summary.failed_checks == 1
        assert summary.total_weight == 4
        assert summary.passed_weight == 3
        assert summary.health_score == 75.0  # 3/4 * 100
