# tests/test_strategy_profiles.py
"""
Tests für Strategy-Profile und Tiering (Phase 41B).

Testet:
- StrategyProfile Datenmodell
- JSON Import/Export
- Markdown-Generierung
- Tiering-Config Parsing
- StrategyProfileBuilder
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest


class TestPerformanceMetrics:
    """Tests für PerformanceMetrics."""

    def test_from_backtest_stats_basic(self):
        """Erstellt PerformanceMetrics aus Backtest-Stats."""
        from src.experiments.strategy_profiles import PerformanceMetrics

        stats = {
            "sharpe": 1.5,
            "cagr": 0.15,
            "max_drawdown": -0.12,
            "total_return": 0.25,
            "win_rate": 0.55,
            "total_trades": 100,
        }

        perf = PerformanceMetrics.from_backtest_stats(stats)

        assert perf.sharpe == 1.5
        assert perf.cagr == 0.15
        assert perf.max_drawdown == -0.12
        assert perf.total_return == 0.25
        assert perf.winrate == 0.55
        assert perf.trade_count == 100

    def test_from_backtest_stats_alternative_keys(self):
        """Testet alternative Key-Namen."""
        from src.experiments.strategy_profiles import PerformanceMetrics

        stats = {
            "sharpe_ratio": 1.8,  # Alternative zu 'sharpe'
            "trade_count": 50,  # Alternative zu 'total_trades'
            "expectancy": 0.01,  # Alternative zu 'avg_trade'
        }

        perf = PerformanceMetrics.from_backtest_stats(stats)

        assert perf.sharpe == 1.8
        assert perf.trade_count == 50
        assert perf.avg_trade == 0.01

    def test_to_dict(self):
        """Konvertiert PerformanceMetrics zu Dict."""
        from src.experiments.strategy_profiles import PerformanceMetrics

        perf = PerformanceMetrics(
            sharpe=1.5,
            cagr=0.15,
            max_drawdown=-0.10,
            volatility=0.20,
            trade_count=100,
        )

        d = perf.to_dict()

        assert d["sharpe"] == 1.5
        assert d["cagr"] == 0.15
        assert d["max_drawdown"] == -0.10
        assert d["volatility"] == 0.20
        assert d["trade_count"] == 100


class TestRobustnessMetrics:
    """Tests für RobustnessMetrics."""

    def test_default_values(self):
        """Testet Default-Werte."""
        from src.experiments.strategy_profiles import RobustnessMetrics

        rob = RobustnessMetrics()

        assert rob.montecarlo_p5 is None
        assert rob.montecarlo_p50 is None
        assert rob.montecarlo_p95 is None
        assert rob.stress_min is None
        assert rob.num_montecarlo_runs == 0
        assert rob.num_stress_scenarios == 0

    def test_to_dict(self):
        """Konvertiert RobustnessMetrics zu Dict."""
        from src.experiments.strategy_profiles import RobustnessMetrics

        rob = RobustnessMetrics(
            montecarlo_p5=0.05,
            montecarlo_p50=0.15,
            montecarlo_p95=0.30,
            num_montecarlo_runs=1000,
            stress_min=-0.20,
            stress_max=0.10,
            num_stress_scenarios=4,
        )

        d = rob.to_dict()

        assert d["montecarlo_p5"] == 0.05
        assert d["montecarlo_p50"] == 0.15
        assert d["montecarlo_p95"] == 0.30
        assert d["num_montecarlo_runs"] == 1000
        assert d["stress_min"] == -0.20


class TestRegimeProfile:
    """Tests für RegimeProfile und SingleRegimeProfile."""

    def test_single_regime_profile(self):
        """Erstellt SingleRegimeProfile."""
        from src.experiments.strategy_profiles import SingleRegimeProfile

        regime = SingleRegimeProfile(
            name="risk_on",
            contribution_return=0.15,
            time_share=0.40,
            efficiency_ratio=0.375,
            trade_count=40,
            avg_return=0.01,
        )

        assert regime.name == "risk_on"
        assert regime.contribution_return == 0.15
        assert regime.time_share == 0.40
        assert regime.efficiency_ratio == 0.375

    def test_regime_profile_to_dict(self):
        """Konvertiert RegimeProfile zu Dict."""
        from src.experiments.strategy_profiles import RegimeProfile, SingleRegimeProfile

        profile = RegimeProfile(
            regimes=[
                SingleRegimeProfile(name="risk_on", contribution_return=0.15, time_share=0.40),
                SingleRegimeProfile(name="neutral", contribution_return=0.05, time_share=0.30),
                SingleRegimeProfile(name="risk_off", contribution_return=-0.02, time_share=0.30),
            ],
            dominant_regime="risk_on",
            weakest_regime="risk_off",
        )

        d = profile.to_dict()

        assert len(d["regimes"]) == 3
        assert d["dominant_regime"] == "risk_on"
        assert d["weakest_regime"] == "risk_off"


class TestStrategyTieringInfo:
    """Tests für StrategyTieringInfo."""

    def test_default_tier(self):
        """Testet Default-Tier."""
        from src.experiments.strategy_profiles import StrategyTieringInfo

        tiering = StrategyTieringInfo()

        assert tiering.tier == "unclassified"
        assert tiering.allow_live is False

    def test_core_tier(self):
        """Erstellt Core-Tier-Info."""
        from src.experiments.strategy_profiles import StrategyTieringInfo

        tiering = StrategyTieringInfo(
            tier="core",
            reason="Robust über mehrere Regime",
            recommended_config_id="rsi_reversion_v1_core",
            allow_live=False,
        )

        assert tiering.tier == "core"
        assert "Robust" in tiering.reason
        assert tiering.recommended_config_id == "rsi_reversion_v1_core"


class TestStrategyProfile:
    """Tests für StrategyProfile."""

    def test_create_minimal_profile(self):
        """Erstellt minimales Profil."""
        from src.experiments.strategy_profiles import (
            Metadata,
            PerformanceMetrics,
            StrategyProfile,
        )

        profile = StrategyProfile(
            metadata=Metadata(strategy_id="test_strategy"),
            performance=PerformanceMetrics(sharpe=1.5, total_return=0.20),
        )

        assert profile.metadata.strategy_id == "test_strategy"
        assert profile.performance.sharpe == 1.5
        assert profile.regimes is None
        assert profile.tiering is None

    def test_to_dict(self):
        """Konvertiert Profil zu Dict."""
        from src.experiments.strategy_profiles import (
            Metadata,
            PerformanceMetrics,
            RobustnessMetrics,
            StrategyProfile,
            StrategyTieringInfo,
        )

        profile = StrategyProfile(
            metadata=Metadata(
                strategy_id="rsi_reversion",
                timeframe="1h",
                symbols=["BTC/EUR"],
            ),
            performance=PerformanceMetrics(sharpe=1.5, max_drawdown=-0.10),
            robustness=RobustnessMetrics(num_montecarlo_runs=100),
            tiering=StrategyTieringInfo(tier="core"),
        )

        d = profile.to_dict()

        assert d["metadata"]["strategy_id"] == "rsi_reversion"
        assert d["performance"]["sharpe"] == 1.5
        assert d["robustness"]["num_montecarlo_runs"] == 100
        assert d["tiering"]["tier"] == "core"

    def test_json_roundtrip(self):
        """Testet JSON Export und Re-Import."""
        from src.experiments.strategy_profiles import (
            Metadata,
            PerformanceMetrics,
            StrategyProfile,
            StrategyTieringInfo,
        )

        profile = StrategyProfile(
            metadata=Metadata(
                strategy_id="test_json",
                data_range="2024-01-01..2024-12-31",
            ),
            performance=PerformanceMetrics(
                sharpe=1.8,
                cagr=0.12,
                max_drawdown=-0.08,
            ),
            tiering=StrategyTieringInfo(tier="aux", notes="Test"),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test_profile.json"

            # Export
            profile.to_json(json_path)
            assert json_path.exists()

            # Re-Import
            loaded = StrategyProfile.from_json(json_path)

            assert loaded.metadata.strategy_id == "test_json"
            assert loaded.metadata.data_range == "2024-01-01..2024-12-31"
            assert loaded.performance.sharpe == 1.8
            assert loaded.tiering.tier == "aux"

    def test_markdown_export(self):
        """Testet Markdown-Export."""
        from src.experiments.strategy_profiles import (
            Metadata,
            PerformanceMetrics,
            RegimeProfile,
            SingleRegimeProfile,
            StrategyProfile,
            StrategyTieringInfo,
        )

        profile = StrategyProfile(
            metadata=Metadata(
                strategy_id="md_test",
                symbols=["BTC/EUR", "ETH/EUR"],
            ),
            performance=PerformanceMetrics(
                sharpe=2.0,
                cagr=0.20,
                max_drawdown=-0.12,
                trade_count=150,
            ),
            regimes=RegimeProfile(
                regimes=[
                    SingleRegimeProfile(name="risk_on", contribution_return=0.15, time_share=0.5),
                ],
                dominant_regime="risk_on",
            ),
            tiering=StrategyTieringInfo(tier="core", notes="Robuste Strategie"),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"

            profile.to_markdown(md_path)
            assert md_path.exists()

            content = md_path.read_text()

            assert "MD_TEST" in content
            assert "Sharpe" in content
            assert "Regime" in content
            assert "Tiering" in content
            assert "core" in content.lower()


class TestStrategyProfileBuilder:
    """Tests für StrategyProfileBuilder."""

    def test_basic_builder(self):
        """Testet grundlegenden Builder-Workflow."""
        from src.experiments.strategy_profiles import StrategyProfileBuilder

        builder = StrategyProfileBuilder(
            strategy_id="builder_test",
            timeframe="4h",
            symbols=["ETH/EUR"],
        )

        builder.set_data_range("2024-01-01", "2024-06-30")
        builder.set_performance(sharpe=1.6, cagr=0.18, max_drawdown=-0.09)

        profile = builder.build()

        assert profile.metadata.strategy_id == "builder_test"
        assert profile.metadata.timeframe == "4h"
        assert profile.metadata.data_range == "2024-01-01..2024-06-30"
        assert profile.performance.sharpe == 1.6

    def test_builder_with_montecarlo(self):
        """Testet Builder mit Monte-Carlo-Ergebnissen."""
        from src.experiments.strategy_profiles import StrategyProfileBuilder

        builder = StrategyProfileBuilder("mc_test")
        builder.set_montecarlo_results(
            p5=0.05,
            p50=0.15,
            p95=0.30,
            num_runs=1000,
            sharpe_p5=0.8,
            sharpe_p95=2.2,
        )

        profile = builder.build()

        assert profile.robustness.montecarlo_p5 == 0.05
        assert profile.robustness.montecarlo_p95 == 0.30
        assert profile.robustness.num_montecarlo_runs == 1000

    def test_builder_with_stress(self):
        """Testet Builder mit Stress-Test-Ergebnissen."""
        from src.experiments.strategy_profiles import StrategyProfileBuilder

        builder = StrategyProfileBuilder("stress_test")
        builder.set_stress_results(
            min_return=-0.25,
            max_return=0.10,
            avg_return=-0.05,
            num_scenarios=4,
        )

        profile = builder.build()

        assert profile.robustness.stress_min == -0.25
        assert profile.robustness.stress_max == 0.10
        assert profile.robustness.num_stress_scenarios == 4

    def test_builder_with_regimes(self):
        """Testet Builder mit Regime-Analyse."""
        from src.experiments.strategy_profiles import StrategyProfileBuilder

        builder = StrategyProfileBuilder("regime_test")
        builder.add_regime("risk_on", contribution_return=0.20, time_share=0.4)
        builder.add_regime("neutral", contribution_return=0.05, time_share=0.35)
        builder.add_regime("risk_off", contribution_return=-0.03, time_share=0.25)
        builder.finalize_regimes()

        profile = builder.build()

        assert len(profile.regimes.regimes) == 3
        assert profile.regimes.dominant_regime == "risk_on"
        assert profile.regimes.weakest_regime == "risk_off"

    def test_builder_with_tiering(self):
        """Testet Builder mit Tiering."""
        from src.experiments.strategy_profiles import StrategyProfileBuilder

        builder = StrategyProfileBuilder("tiering_test")
        builder.set_tiering(
            tier="core",
            reason="Robust über alle Regime",
            recommended_config_id="tiering_test_v1",
            allow_live=False,
        )

        profile = builder.build()

        assert profile.tiering.tier == "core"
        assert profile.tiering.recommended_config_id == "tiering_test_v1"


class TestTieringConfig:
    """Tests für Tiering-Config-Loading."""

    def test_load_tiering_config_from_file(self):
        """Lädt Tiering-Config aus temporärer Datei."""
        from src.experiments.strategy_profiles import load_tiering_config

        config_content = """
[strategy.test_strategy]
tier = "core"
recommended_config_id = "test_v1"
allow_live = false
notes = "Test-Strategie"

[strategy.another_strategy]
tier = "aux"
notes = "Ergänzende Strategie"
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_tiering.toml"
            config_path.write_text(config_content)

            tiering = load_tiering_config(config_path)

            assert "test_strategy" in tiering
            assert tiering["test_strategy"].tier == "core"
            assert tiering["test_strategy"].recommended_config_id == "test_v1"

            assert "another_strategy" in tiering
            assert tiering["another_strategy"].tier == "aux"

    def test_load_tiering_config_missing_file(self):
        """Gibt leeres Dict zurück bei fehlender Datei."""
        from src.experiments.strategy_profiles import load_tiering_config

        tiering = load_tiering_config("/nonexistent/path/config.toml")

        assert tiering == {}

    def test_get_tiering_for_strategy(self):
        """Holt Tiering für bestimmte Strategie."""
        from src.experiments.strategy_profiles import (
            StrategyTieringInfo,
            get_tiering_for_strategy,
        )

        tiering_config = {
            "rsi_reversion": StrategyTieringInfo(tier="core", notes="Test"),
        }

        info = get_tiering_for_strategy("rsi_reversion", tiering_config)
        assert info.tier == "core"

        # Unbekannte Strategie
        unknown = get_tiering_for_strategy("unknown_strategy", tiering_config)
        assert unknown.tier == "unclassified"


class TestMarkdownGeneration:
    """Tests für Markdown-Generierung."""

    def test_generate_markdown_basic(self):
        """Generiert Markdown für einfaches Profil."""
        from src.experiments.strategy_profiles import (
            Metadata,
            PerformanceMetrics,
            StrategyProfile,
            generate_markdown_profile,
        )

        profile = StrategyProfile(
            metadata=Metadata(strategy_id="md_basic"),
            performance=PerformanceMetrics(
                sharpe=1.5,
                cagr=0.15,
                max_drawdown=-0.10,
            ),
        )

        md = generate_markdown_profile(profile)

        assert "# Strategy Profile - MD_BASIC" in md
        assert "1.50" in md  # Sharpe
        assert "15.00%" in md  # CAGR
        assert "-10.00%" in md  # Max DD

    def test_generate_markdown_with_regime(self):
        """Generiert Markdown mit Regime-Tabelle."""
        from src.experiments.strategy_profiles import (
            Metadata,
            PerformanceMetrics,
            RegimeProfile,
            SingleRegimeProfile,
            StrategyProfile,
            generate_markdown_profile,
        )

        profile = StrategyProfile(
            metadata=Metadata(strategy_id="md_regime"),
            performance=PerformanceMetrics(),
            regimes=RegimeProfile(
                regimes=[
                    SingleRegimeProfile(name="risk_on", contribution_return=0.10, time_share=0.5),
                ],
            ),
        )

        md = generate_markdown_profile(profile)

        assert "Regime-Profil" in md
        assert "risk_on" in md


class TestIntegrationWithRealConfig:
    """Integration-Tests mit echter Tiering-Config."""

    def test_load_real_tiering_config(self):
        """Lädt die echte Tiering-Config."""
        from src.experiments.strategy_profiles import load_tiering_config

        config_path = Path("config/strategy_tiering.toml")

        if config_path.exists():
            tiering = load_tiering_config(config_path)

            # Prüfe, dass einige Strategien geladen wurden
            assert len(tiering) > 0

            # Prüfe bekannte Strategien
            if "rsi_reversion" in tiering:
                assert tiering["rsi_reversion"].tier in ("core", "aux", "legacy")
        else:
            pytest.skip("Tiering-Config nicht vorhanden")
