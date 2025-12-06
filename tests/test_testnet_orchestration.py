# tests/test_testnet_orchestration.py
"""
Tests fuer scripts/orchestrate_testnet_runs.py (Phase 37)

Testet:
- OrchestrationConfig
- TestnetOrchestrator
- CLI-Funktionen (mit Mocks)
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.peak_config import load_config
from src.live.testnet_limits import (
    TestnetLimitsController,
    TestnetRunLimits,
    TestnetDailyLimits,
    TestnetSymbolPolicy,
    TestnetUsageStore,
    load_testnet_limits_from_config,
)
from src.live.testnet_profiles import (
    TestnetSessionProfile,
    load_testnet_profiles,
)

# Import Orchestrator components
from scripts.orchestrate_testnet_runs import (
    OrchestrationConfig,
    OrchestrationResult,
    TestnetOrchestrator,
    cmd_list_profiles,
    cmd_show_budget,
)


# =============================================================================
# OrchestrationConfig Tests
# =============================================================================


class TestOrchestrationConfig:
    """Tests fuer OrchestrationConfig."""

    def test_from_config(self, test_config_path):
        """Test: OrchestrationConfig aus Config laden."""
        cfg = load_config(test_config_path)
        orch_config = OrchestrationConfig.from_config(cfg)

        assert orch_config.runs_base_dir == Path("test_runs/")
        assert orch_config.reports_dir == Path("test_results/reports/")
        assert orch_config.auto_generate_report is False
        assert orch_config.report_format == "markdown"
        assert orch_config.usage_retention_days == 7

    def test_default_values(self):
        """Test: Default-Werte werden verwendet wenn nicht in Config."""
        # Leere Config simulieren
        from src.core.peak_config import PeakConfig

        empty_cfg = PeakConfig(raw={})
        orch_config = OrchestrationConfig.from_config(empty_cfg)

        assert orch_config.runs_base_dir == Path("test_runs/")
        assert orch_config.reports_dir == Path("test_results/reports/")


# =============================================================================
# OrchestrationResult Tests
# =============================================================================


class TestOrchestrationResult:
    """Tests fuer OrchestrationResult."""

    def test_successful_result(self):
        """Test: Erfolgreicher Result."""
        result = OrchestrationResult(
            success=True,
            profile_id="test",
            run_id="testnet_test_123",
        )
        assert result.success is True
        assert result.profile_id == "test"
        assert result.run_id == "testnet_test_123"
        assert result.error is None

    def test_failed_result(self):
        """Test: Fehlgeschlagener Result."""
        result = OrchestrationResult(
            success=False,
            profile_id="test",
            error="Limit-Verletzung",
        )
        assert result.success is False
        assert result.error == "Limit-Verletzung"

    def test_dry_run_result(self):
        """Test: Dry-Run Result."""
        result = OrchestrationResult(
            success=True,
            profile_id="test",
            dry_run=True,
        )
        assert result.success is True
        assert result.dry_run is True
        assert result.run_id is None


# =============================================================================
# TestnetOrchestrator Tests
# =============================================================================


class TestTestnetOrchestrator:
    """Tests fuer TestnetOrchestrator."""

    @pytest.fixture
    def orchestrator(self, test_config_path):
        """Fixture: Orchestrator mit Test-Config."""
        cfg = load_config(test_config_path)
        limits_controller = load_testnet_limits_from_config(cfg)
        orch_config = OrchestrationConfig.from_config(cfg)

        return TestnetOrchestrator(
            cfg=cfg,
            limits_controller=limits_controller,
            orch_config=orch_config,
        )

    def test_profiles_loaded(self, orchestrator):
        """Test: Profile werden geladen."""
        assert len(orchestrator.profiles) >= 2
        assert "test_profile" in orchestrator.profiles

    def test_list_profiles(self, orchestrator):
        """Test: Profile auflisten."""
        profile_ids = orchestrator.list_profiles()
        assert "test_profile" in profile_ids
        assert "test_profile_eth" in profile_ids

    def test_get_profile(self, orchestrator):
        """Test: Profil abrufen."""
        profile = orchestrator.get_profile("test_profile")
        assert profile is not None
        assert profile.id == "test_profile"

        # Nicht existierend
        missing = orchestrator.get_profile("non_existent")
        assert missing is None

    def test_check_profile_ok(self, orchestrator):
        """Test: Profil-Check bestanden."""
        profile = orchestrator.get_profile("test_profile")
        result = orchestrator.check_profile(profile)

        assert result.allowed is True
        assert len(result.reasons) == 0

    def test_check_profile_symbol_not_allowed(self, orchestrator):
        """Test: Profil-Check mit nicht erlaubtem Symbol."""
        profile = TestnetSessionProfile(
            id="bad_symbol",
            strategy="ma_crossover",
            symbol="DOGE/EUR",  # Nicht in Whitelist
        )
        result = orchestrator.check_profile(profile)

        assert result.allowed is False
        assert any("symbol" in r.lower() for r in result.reasons)

    def test_run_profile_not_found(self, orchestrator):
        """Test: Run mit nicht existierendem Profil."""
        result = orchestrator.run_profile("non_existent", dry_run=True)

        assert result.success is False
        assert "nicht gefunden" in result.error

    def test_run_profile_dry_run(self, orchestrator):
        """Test: Dry-Run fuehrt keine Session aus."""
        result = orchestrator.run_profile("test_profile", dry_run=True)

        assert result.success is True
        assert result.dry_run is True
        assert result.run_id is None  # Kein Run gestartet

    def test_run_profile_with_overrides_dry_run(self, orchestrator):
        """Test: Dry-Run mit Overrides."""
        result = orchestrator.run_profile(
            "test_profile",
            dry_run=True,
            override_duration=3,
            override_max_notional=50.0,
        )

        assert result.success is True
        assert result.dry_run is True

    def test_run_profile_limit_violation_dry_run(self):
        """Test: Limit-Verletzung wird im Dry-Run erkannt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Controller mit sehr niedrigen Limits
            store = TestnetUsageStore(base_dir=Path(tmpdir))
            controller = TestnetLimitsController(
                run_limits=TestnetRunLimits(max_notional_per_run=10.0),  # Sehr niedrig
                daily_limits=TestnetDailyLimits(),
                symbol_policy=TestnetSymbolPolicy(),
                usage_store=store,
            )

            # Profil das Limit uebersteigt
            profiles = {
                "high_notional": TestnetSessionProfile(
                    id="high_notional",
                    strategy="ma_crossover",
                    symbol="BTC/EUR",
                    max_notional=100.0,  # Uebersteigt Limit
                )
            }

            # Mock-Config
            mock_cfg = MagicMock()
            mock_cfg.get.return_value = None

            with patch("scripts.orchestrate_testnet_runs.load_testnet_profiles", return_value=profiles):
                orchestrator = TestnetOrchestrator(
                    cfg=mock_cfg,
                    limits_controller=controller,
                    orch_config=OrchestrationConfig(
                        runs_base_dir=Path(tmpdir),
                        reports_dir=Path(tmpdir),
                        auto_generate_report=False,
                        report_format="markdown",
                        usage_retention_days=7,
                    ),
                )

            result = orchestrator.run_profile("high_notional", dry_run=True)

            assert result.success is False
            assert "Limit-Verletzung" in result.error


# =============================================================================
# CLI Function Tests
# =============================================================================


class TestCLIFunctions:
    """Tests fuer CLI-Funktionen."""

    def test_cmd_list_profiles(self, test_config_path, capsys):
        """Test: cmd_list_profiles() gibt Profile aus."""
        cfg = load_config(test_config_path)
        logger = MagicMock()

        exit_code = cmd_list_profiles(cfg, logger)

        assert exit_code == 0

        captured = capsys.readouterr()
        assert "test_profile" in captured.out

    def test_cmd_show_budget(self, test_config_path, capsys):
        """Test: cmd_show_budget() zeigt Budget an."""
        cfg = load_config(test_config_path)
        logger = MagicMock()

        exit_code = cmd_show_budget(cfg, logger)

        assert exit_code == 0

        captured = capsys.readouterr()
        assert "Budget" in captured.out
        assert "Verbraucht" in captured.out or "Notional" in captured.out


# =============================================================================
# Integration Tests
# =============================================================================


class TestOrchestratorIntegration:
    """Integration-Tests fuer Orchestrator."""

    def test_full_dry_run_workflow(self, test_config_path):
        """Test: Kompletter Dry-Run Workflow."""
        cfg = load_config(test_config_path)
        limits_controller = load_testnet_limits_from_config(cfg)
        orch_config = OrchestrationConfig.from_config(cfg)

        orchestrator = TestnetOrchestrator(
            cfg=cfg,
            limits_controller=limits_controller,
            orch_config=orch_config,
        )

        # 1. Profile auflisten
        profiles = orchestrator.list_profiles()
        assert len(profiles) >= 1

        # 2. Profil holen
        profile = orchestrator.get_profile(profiles[0])
        assert profile is not None

        # 3. Profil pruefen
        check = orchestrator.check_profile(profile)
        assert check.allowed is True

        # 4. Dry-Run
        result = orchestrator.run_profile(profiles[0], dry_run=True)
        assert result.success is True
        assert result.dry_run is True

    def test_budget_tracking(self, test_config_path):
        """Test: Budget-Tracking ueber Controller."""
        cfg = load_config(test_config_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            limits_controller = load_testnet_limits_from_config(cfg, base_dir=Path(tmpdir))

            # Initial Budget
            budget1 = limits_controller.get_remaining_budget()
            initial_remaining = budget1["remaining_notional"]

            # Verbrauch simulieren
            limits_controller.register_run_consumption(notional=100.0, trades=5)

            # Aktualisiertes Budget
            budget2 = limits_controller.get_remaining_budget()
            assert budget2["remaining_notional"] == initial_remaining - 100.0
            assert budget2["notional_used"] == 100.0
            assert budget2["trades_executed"] == 5
            assert budget2["runs_completed"] == 1


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_config_path():
    """Gibt den Pfad zur Test-Config zurueck."""
    return Path(__file__).parent.parent / "config" / "config.test.toml"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
