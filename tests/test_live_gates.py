# tests/test_live_gates.py
"""
Tests für Phase 83: Live-Gating & Risk Policies v1.0

Testet:
- Strategy-Eligibility basierend auf Tiering
- Portfolio-Eligibility basierend auf Komponenten
- Policy-Loading und -Validierung
- Positive und Negative Cases
"""
import pytest
from pathlib import Path

from src.live.live_gates import (
    LiveGateResult,
    LivePolicies,
    load_live_policies,
    check_strategy_live_eligibility,
    check_portfolio_live_eligibility,
    get_eligible_strategies,
    assert_strategy_eligible,
    assert_portfolio_eligible,
    get_eligibility_summary,
)
from src.experiments.strategy_profiles import StrategyProfile, StrategyProfileBuilder


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def default_policies():
    """Default LivePolicies."""
    return LivePolicies()


@pytest.fixture
def strict_policies():
    """Strenge Policies (require_allow_live_flag=True)."""
    return LivePolicies(
        min_sharpe_core=1.5,
        min_sharpe_aux=1.0,
        max_maxdd_core=-0.15,
        max_maxdd_aux=-0.20,
        allow_legacy=False,
        require_allow_live_flag=True,  # Streng
        require_diversification=True,
        max_concentration=0.5,
    )


@pytest.fixture
def relaxed_policies():
    """Entspannte Policies (Legacy erlaubt)."""
    return LivePolicies(
        min_sharpe_core=1.0,
        min_sharpe_aux=0.5,
        max_maxdd_core=-0.25,
        max_maxdd_aux=-0.30,
        allow_legacy=True,
        require_allow_live_flag=False,
        require_diversification=False,
        max_concentration=1.0,
    )


@pytest.fixture
def core_strategy_profile():
    """StrategyProfile für eine Core-Strategie."""
    builder = StrategyProfileBuilder("rsi_reversion")
    builder.set_performance(sharpe=1.8, cagr=0.20, max_drawdown=-0.10)
    builder.set_tiering("core", "Test core strategy")
    return builder.build()


@pytest.fixture
def weak_strategy_profile():
    """StrategyProfile mit schwacher Performance."""
    builder = StrategyProfileBuilder("weak_strategy")
    builder.set_performance(sharpe=0.5, cagr=0.05, max_drawdown=-0.30)
    builder.set_tiering("aux", "Test weak strategy")
    return builder.build()


# =============================================================================
# TESTS: LIVE POLICIES
# =============================================================================

class TestLivePolicies:
    """Tests für LivePolicies Datenmodell."""

    def test_default_policies(self):
        """Default-Policies haben erwartete Werte."""
        policies = LivePolicies()

        assert policies.min_sharpe_core == 1.5
        assert policies.min_sharpe_aux == 1.0
        assert policies.max_maxdd_core == -0.15
        assert policies.max_maxdd_aux == -0.20
        assert policies.allow_legacy is False
        assert policies.require_allow_live_flag is False

    def test_from_dict(self):
        """LivePolicies.from_dict funktioniert."""
        data = {
            "min_sharpe_core": 2.0,
            "max_maxdd_core": -0.10,
            "allow_legacy": True,
        }

        policies = LivePolicies.from_dict(data)

        assert policies.min_sharpe_core == 2.0
        assert policies.max_maxdd_core == -0.10
        assert policies.allow_legacy is True
        # Defaults für nicht gesetzte Werte
        assert policies.min_sharpe_aux == 1.0

    def test_load_live_policies(self):
        """Policies können aus Datei geladen werden."""
        policies = load_live_policies()

        # Sollte immer ein LivePolicies-Objekt zurückgeben
        assert isinstance(policies, LivePolicies)


# =============================================================================
# TESTS: STRATEGY ELIGIBILITY - POSITIVE CASES
# =============================================================================

class TestStrategyEligibilityPositive:
    """Positive Tests für Strategy-Eligibility."""

    def test_core_strategy_is_eligible(self, default_policies):
        """Core-Strategie ohne allow_live-Requirement ist eligible."""
        result = check_strategy_live_eligibility(
            "rsi_reversion",
            policies=default_policies,
        )

        assert result.is_eligible, f"Core strategy should be eligible: {result}"
        assert result.tier == "core"

    def test_aux_strategy_is_eligible(self, default_policies):
        """Aux-Strategie ohne allow_live-Requirement ist eligible."""
        result = check_strategy_live_eligibility(
            "breakout",
            policies=default_policies,
        )

        assert result.is_eligible, f"Aux strategy should be eligible: {result}"
        assert result.tier == "aux"

    def test_core_with_good_profile_is_eligible(self, default_policies, core_strategy_profile):
        """Core-Strategie mit gutem Profil ist eligible."""
        result = check_strategy_live_eligibility(
            "rsi_reversion",
            profile=core_strategy_profile,
            policies=default_policies,
        )

        assert result.is_eligible, f"Core with good profile should be eligible: {result}"

    def test_all_core_strategies_eligible_by_default(self, default_policies):
        """Alle Core-Strategien sind mit Default-Policies eligible."""
        from src.experiments.portfolio_presets import get_strategies_by_tier

        core_strategies = get_strategies_by_tier("core")

        for strategy_id in core_strategies:
            result = check_strategy_live_eligibility(
                strategy_id,
                policies=default_policies,
            )
            assert result.is_eligible, f"Core strategy {strategy_id} should be eligible: {result}"


# =============================================================================
# TESTS: STRATEGY ELIGIBILITY - NEGATIVE CASES
# =============================================================================

class TestStrategyEligibilityNegative:
    """Negative Tests für Strategy-Eligibility."""

    def test_legacy_strategy_not_eligible(self, default_policies):
        """Legacy-Strategie ist nicht eligible."""
        result = check_strategy_live_eligibility(
            "breakout_donchian",
            policies=default_policies,
        )

        assert not result.is_eligible, "Legacy strategy should not be eligible"
        assert result.tier == "legacy"
        assert any("legacy" in r.lower() for r in result.reasons)

    def test_unknown_strategy_not_eligible(self, default_policies):
        """Unbekannte Strategie ist nicht eligible."""
        result = check_strategy_live_eligibility(
            "nonexistent_strategy",
            policies=default_policies,
        )

        assert not result.is_eligible, "Unknown strategy should not be eligible"
        assert "not found" in str(result.reasons).lower()

    def test_strategy_without_allow_live_not_eligible_when_required(self, strict_policies):
        """Strategie ohne allow_live=True ist nicht eligible wenn enforced."""
        result = check_strategy_live_eligibility(
            "rsi_reversion",  # Hat allow_live=False
            policies=strict_policies,
        )

        assert not result.is_eligible, "Strategy without allow_live should fail with strict policies"
        assert any("allow_live" in r.lower() for r in result.reasons)

    def test_strategy_with_weak_profile_not_eligible(self, default_policies, weak_strategy_profile):
        """Strategie mit schwachem Profil ist nicht eligible."""
        # Erstelle ein schwaches Profil für eine aux-Strategie
        builder = StrategyProfileBuilder("breakout")
        builder.set_performance(sharpe=0.3, cagr=0.02, max_drawdown=-0.35)
        weak_aux_profile = builder.build()

        result = check_strategy_live_eligibility(
            "breakout",
            profile=weak_aux_profile,
            policies=default_policies,
        )

        # Aux mit Sharpe 0.3 < 1.0 sollte scheitern
        assert not result.is_eligible, "Aux with low Sharpe should not be eligible"
        assert any("sharpe" in r.lower() for r in result.reasons)


class TestStrategyEligibilityEdgeCases:
    """Edge-Case Tests für Strategy-Eligibility."""

    def test_legacy_allowed_with_relaxed_policies(self, relaxed_policies):
        """Legacy-Strategie ist mit relaxed policies eligible."""
        result = check_strategy_live_eligibility(
            "breakout_donchian",
            policies=relaxed_policies,
        )

        assert result.is_eligible, "Legacy should be eligible with allow_legacy=True"

    def test_eligibility_result_str(self, default_policies):
        """LiveGateResult.__str__ funktioniert."""
        result = check_strategy_live_eligibility(
            "rsi_reversion",
            policies=default_policies,
        )

        str_output = str(result)
        assert "rsi_reversion" in str_output
        assert "ELIGIBLE" in str_output


# =============================================================================
# TESTS: PORTFOLIO ELIGIBILITY
# =============================================================================

class TestPortfolioEligibility:
    """Tests für Portfolio-Eligibility."""

    def test_core_balanced_is_eligible(self, default_policies):
        """core_balanced Portfolio ist eligible."""
        result = check_portfolio_live_eligibility(
            "core_balanced",
            strategies=["rsi_reversion", "ma_crossover", "bollinger_bands"],
            weights=[0.34, 0.33, 0.33],
            policies=default_policies,
        )

        assert result.is_eligible, f"core_balanced should be eligible: {result}"

    def test_portfolio_with_legacy_not_eligible(self, default_policies):
        """Portfolio mit Legacy-Strategie ist nicht eligible."""
        result = check_portfolio_live_eligibility(
            "test_with_legacy",
            strategies=["rsi_reversion", "breakout_donchian"],  # Legacy!
            weights=[0.5, 0.5],
            policies=default_policies,
        )

        assert not result.is_eligible, "Portfolio with legacy should not be eligible"
        assert "ineligible strategies" in str(result.reasons).lower()

    def test_empty_portfolio_not_eligible(self, default_policies):
        """Leeres Portfolio ist nicht eligible."""
        result = check_portfolio_live_eligibility(
            "empty_portfolio",
            strategies=[],
            weights=[],
            policies=default_policies,
        )

        assert not result.is_eligible, "Empty portfolio should not be eligible"
        assert "no strategies" in str(result.reasons).lower()

    def test_concentrated_portfolio_not_eligible(self):
        """Zu konzentriertes Portfolio ist nicht eligible."""
        # Policies mit max_concentration=0.5
        strict_diversification = LivePolicies(max_concentration=0.5)

        result = check_portfolio_live_eligibility(
            "concentrated",
            strategies=["rsi_reversion", "ma_crossover"],
            weights=[0.9, 0.1],  # 90% in einer Strategie!
            policies=strict_diversification,
        )

        assert not result.is_eligible, "Concentrated portfolio should not be eligible"
        assert "concentration" in str(result.reasons).lower()

    def test_diversification_not_checked_when_disabled(self, relaxed_policies):
        """Diversifikation wird nicht geprüft wenn deaktiviert."""
        result = check_portfolio_live_eligibility(
            "concentrated_allowed",
            strategies=["rsi_reversion", "ma_crossover"],
            weights=[0.9, 0.1],  # Normalerweise zu konzentriert
            policies=relaxed_policies,  # require_diversification=False
        )

        assert result.is_eligible, "Should be eligible with diversification check disabled"


# =============================================================================
# TESTS: HELPER FUNCTIONS
# =============================================================================

class TestHelperFunctions:
    """Tests für Helper-Funktionen."""

    def test_get_eligible_strategies(self, default_policies):
        """get_eligible_strategies gibt Liste zurück."""
        eligible = get_eligible_strategies(policies=default_policies)

        assert isinstance(eligible, list)
        assert len(eligible) > 0, "Should have at least one eligible strategy"

        # Alle Core-Strategien sollten dabei sein
        assert "rsi_reversion" in eligible
        assert "ma_crossover" in eligible

        # Legacy sollte nicht dabei sein
        assert "breakout_donchian" not in eligible

    def test_assert_strategy_eligible_passes(self, default_policies):
        """assert_strategy_eligible wirft keine Exception für eligible Strategie."""
        # Sollte ohne Exception durchlaufen
        assert_strategy_eligible("rsi_reversion", policies=default_policies)

    def test_assert_strategy_eligible_fails(self, default_policies):
        """assert_strategy_eligible wirft Exception für nicht-eligible Strategie."""
        with pytest.raises(ValueError) as exc_info:
            assert_strategy_eligible("breakout_donchian", policies=default_policies)

        assert "not live-eligible" in str(exc_info.value)

    def test_assert_portfolio_eligible_passes(self, default_policies):
        """assert_portfolio_eligible wirft keine Exception für eligible Portfolio."""
        assert_portfolio_eligible(
            "test_portfolio",
            strategies=["rsi_reversion", "ma_crossover"],
            weights=[0.5, 0.5],
            policies=default_policies,
        )

    def test_assert_portfolio_eligible_fails(self, default_policies):
        """assert_portfolio_eligible wirft Exception für nicht-eligible Portfolio."""
        with pytest.raises(ValueError) as exc_info:
            assert_portfolio_eligible(
                "test_with_legacy",
                strategies=["rsi_reversion", "breakout_donchian"],
                weights=[0.5, 0.5],
                policies=default_policies,
            )

        assert "not live-eligible" in str(exc_info.value)

    def test_get_eligibility_summary(self, default_policies):
        """get_eligibility_summary gibt Zusammenfassung zurück."""
        summary = get_eligibility_summary()

        assert "total_strategies" in summary
        assert "eligible" in summary
        assert "ineligible" in summary
        assert "by_tier" in summary

        # Prüfe Struktur
        assert isinstance(summary["eligible"], list)
        assert isinstance(summary["ineligible"], list)
        assert summary["num_eligible"] == len(summary["eligible"])
        assert summary["num_ineligible"] == len(summary["ineligible"])


# =============================================================================
# TESTS: INTEGRATION
# =============================================================================

class TestLiveGatesIntegration:
    """Integration Tests für Live-Gates."""

    def test_tiered_presets_are_eligible(self, default_policies):
        """Alle Phase-80 tiered Presets sind eligible."""
        presets = [
            ("core_balanced", ["rsi_reversion", "ma_crossover", "bollinger_bands"]),
            ("core_trend_meanreversion", ["ma_crossover", "rsi_reversion", "bollinger_bands"]),
        ]

        for preset_name, strategies in presets:
            result = check_portfolio_live_eligibility(
                preset_name,
                strategies=strategies,
                weights=[1/len(strategies)] * len(strategies),
                policies=default_policies,
            )
            assert result.is_eligible, f"Preset {preset_name} should be eligible: {result}"

    def test_core_plus_aux_preset_eligible(self, default_policies):
        """Core+Aux Preset ist eligible."""
        strategies = [
            "rsi_reversion", "ma_crossover", "bollinger_bands",  # Core
            "breakout", "macd", "momentum_1h",  # Aux
        ]

        result = check_portfolio_live_eligibility(
            "core_plus_aux_aggro",
            strategies=strategies,
            weights=[0.183, 0.184, 0.183, 0.15, 0.15, 0.15],
            policies=default_policies,
        )

        assert result.is_eligible, f"Core+Aux preset should be eligible: {result}"

    def test_full_workflow(self):
        """Vollständiger Workflow: Policies laden → Eligibility prüfen."""
        # 1. Policies laden
        policies = load_live_policies()

        # 2. Eligibility-Summary holen
        summary = get_eligibility_summary()

        # 3. Prüfen dass Core-Strategien eligible sind
        for strategy_id in summary["by_tier"]["core"]["eligible"]:
            result = check_strategy_live_eligibility(strategy_id, policies=policies)
            assert result.is_eligible

        # 4. Portfolio aus eligible Strategien bauen und prüfen
        if summary["eligible"]:
            eligible_strategies = summary["eligible"][:3]  # Max 3
            weights = [1/len(eligible_strategies)] * len(eligible_strategies)

            result = check_portfolio_live_eligibility(
                "test_dynamic_portfolio",
                strategies=eligible_strategies,
                weights=weights,
                policies=policies,
            )

            assert result.is_eligible
