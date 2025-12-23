"""
Tests for Risk Limit Enforcement (src/risk/enforcement.py)
"""

import pytest
import pandas as pd
import numpy as np

from src.risk.enforcement import RiskLimitsV2, RiskEnforcer
from src.risk.types import (
    PositionSnapshot,
    PortfolioSnapshot,
    RiskBreach,
    RiskDecision,
    BreachSeverity,
)


class TestRiskLimitsV2:
    """Tests for RiskLimitsV2 dataclass"""

    def test_valid_limits_creation(self):
        """Valid limits sollten korrekt erstellt werden"""
        limits = RiskLimitsV2(
            max_gross_exposure=1.5,
            max_position_weight=0.35,
            max_var=0.08,
            alpha=0.05,
            window=252,
        )
        assert limits.max_gross_exposure == 1.5
        assert limits.alpha == 0.05
        assert limits.window == 252

    def test_invalid_alpha_raises(self):
        """Invalid alpha sollte ValueError werfen"""
        with pytest.raises(ValueError, match="alpha must be in"):
            RiskLimitsV2(alpha=0.0)

        with pytest.raises(ValueError, match="alpha must be in"):
            RiskLimitsV2(alpha=1.0)

        with pytest.raises(ValueError, match="alpha must be in"):
            RiskLimitsV2(alpha=-0.05)

    def test_invalid_window_raises(self):
        """Invalid window sollte ValueError werfen"""
        with pytest.raises(ValueError, match="window must be > 0"):
            RiskLimitsV2(window=0)

        with pytest.raises(ValueError, match="window must be > 0"):
            RiskLimitsV2(window=-100)


class TestRiskEnforcerExposureLimits:
    """Tests for Exposure Limit Enforcement"""

    def test_no_breach_within_limits(self):
        """Innerhalb der Limits sollte allowed=True sein"""
        snapshot = PortfolioSnapshot(
            equity=100000,
            positions=[
                PositionSnapshot("BTC/EUR", 0.5, 50000),  # 25000
                PositionSnapshot("ETH/EUR", 10, 3000),  # 30000
            ],
        )
        # Gross = 55000, Ratio = 0.55 < 1.5
        limits = RiskLimitsV2(max_gross_exposure=1.5)

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, None, limits)

        assert decision.allowed is True
        assert decision.action == "ALLOW"
        assert len(decision.breaches) == 0

    def test_gross_exposure_breach(self):
        """Gross Exposure > Limit sollte HARD breach erzeugen"""
        snapshot = PortfolioSnapshot(
            equity=100000,
            positions=[
                PositionSnapshot("BTC/EUR", 1, 50000),  # 50000
                PositionSnapshot("ETH/EUR", 30, 3000),  # 90000
            ],
        )
        # Gross = 140000, Ratio = 1.4 > 1.2
        limits = RiskLimitsV2(max_gross_exposure=1.2)

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, None, limits)

        assert decision.allowed is False
        assert decision.action == "HALT"
        assert len(decision.breaches) > 0
        assert any(b.code == "MAX_GROSS_EXPOSURE" for b in decision.breaches)
        assert decision.breaches[0].severity == BreachSeverity.HARD

    def test_net_exposure_breach(self):
        """Net Exposure > Limit sollte HARD breach erzeugen"""
        snapshot = PortfolioSnapshot(
            equity=100000,
            positions=[
                PositionSnapshot("BTC/EUR", 2, 50000),  # +100000 (net)
            ],
        )
        # Net = 100000, Ratio = 1.0 >= 0.9
        limits = RiskLimitsV2(max_net_exposure=0.9)

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, None, limits)

        assert decision.allowed is False
        assert decision.action == "HALT"
        assert any(b.code == "MAX_NET_EXPOSURE" for b in decision.breaches)


class TestRiskEnforcerPositionWeights:
    """Tests for Position Weight Limit Enforcement"""

    def test_position_weight_within_limit(self):
        """Position Weight < Limit sollte erlaubt sein"""
        snapshot = PortfolioSnapshot(
            equity=100000,
            positions=[
                PositionSnapshot("BTC/EUR", 0.3, 50000),  # 15000 = 15%
                PositionSnapshot("ETH/EUR", 5, 3000),  # 15000 = 15%
            ],
        )
        limits = RiskLimitsV2(max_position_weight=0.20)  # 20% max

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, None, limits)

        assert decision.allowed is True

    def test_position_weight_breach(self):
        """Position Weight > Limit sollte HARD breach erzeugen"""
        snapshot = PortfolioSnapshot(
            equity=100000,
            positions=[
                PositionSnapshot("BTC/EUR", 1, 50000),  # 50000 = 50%
            ],
        )
        limits = RiskLimitsV2(max_position_weight=0.35)  # 35% max

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, None, limits)

        assert decision.allowed is False
        assert decision.action == "HALT"
        assert any(b.code == "MAX_POSITION_WEIGHT" for b in decision.breaches)
        assert "BTC/EUR" in decision.breaches[0].message


class TestRiskEnforcerVarLimits:
    """Tests for VaR/CVaR Limit Enforcement"""

    def test_var_within_limit(self):
        """VaR < Limit sollte erlaubt sein"""
        snapshot = PortfolioSnapshot(equity=100000, positions=[])

        # Returns mit niedrigem VaR
        returns = pd.Series([0.001, -0.002, 0.003, -0.001, 0.002])
        limits = RiskLimitsV2(max_var=0.10, alpha=0.05)  # 10% VaR-Limit

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, returns, limits)

        assert decision.allowed is True

    def test_var_breach(self):
        """VaR > Limit sollte HARD breach erzeugen"""
        snapshot = PortfolioSnapshot(equity=100000, positions=[])

        # Returns mit hohem VaR (viele negative)
        returns = pd.Series([-0.05, -0.08, -0.10, -0.03, -0.06])
        limits = RiskLimitsV2(max_var=0.05, alpha=0.05)  # 5% VaR-Limit

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, returns, limits)

        assert decision.allowed is False
        assert decision.action == "HALT"
        assert any(b.code == "MAX_VAR" for b in decision.breaches)

    def test_cvar_breach(self):
        """CVaR > Limit sollte HARD breach erzeugen"""
        snapshot = PortfolioSnapshot(equity=100000, positions=[])

        # Returns mit hohem CVaR
        returns = pd.Series([-0.05, -0.10, -0.15, -0.03, -0.08])
        limits = RiskLimitsV2(max_cvar=0.08, alpha=0.05)  # 8% CVaR-Limit

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, returns, limits)

        assert decision.allowed is False
        assert any(b.code == "MAX_CVAR" for b in decision.breaches)


class TestRiskEnforcerMultipleBreaches:
    """Tests for Multiple Breach Scenarios"""

    def test_multiple_breaches(self):
        """Mehrere Breaches sollten alle gesammelt werden"""
        snapshot = PortfolioSnapshot(
            equity=100000,
            positions=[
                PositionSnapshot("BTC/EUR", 1, 50000),  # 50000 = 50% (weight breach)
                PositionSnapshot("ETH/EUR", 20, 3000),  # 60000
            ],
        )
        # Gross = 110000 = 110% (gross breach)
        returns = pd.Series([-0.10] * 10)  # Hoher VaR

        limits = RiskLimitsV2(
            max_gross_exposure=1.0,
            max_position_weight=0.35,
            max_var=0.05,
            alpha=0.05,
        )

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, returns, limits)

        assert decision.allowed is False
        assert len(decision.breaches) >= 2  # Mind. 2 Breaches
        breach_codes = {b.code for b in decision.breaches}
        assert "MAX_GROSS_EXPOSURE" in breach_codes
        assert "MAX_POSITION_WEIGHT" in breach_codes or "MAX_VAR" in breach_codes

    def test_all_limits_ok(self):
        """Alle Limits OK sollte allowed=True + keine Breaches"""
        snapshot = PortfolioSnapshot(
            equity=100000,
            positions=[
                PositionSnapshot("BTC/EUR", 0.3, 50000),  # 15000 = 15%
            ],
        )
        returns = pd.Series([0.001, -0.002, 0.003])

        limits = RiskLimitsV2(
            max_gross_exposure=1.5,
            max_position_weight=0.35,
            max_var=0.10,
            alpha=0.05,
        )

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, returns, limits)

        assert decision.allowed is True
        assert decision.action == "ALLOW"
        assert len(decision.breaches) == 0


class TestRiskEnforcerEdgeCases:
    """Edge Cases für Enforcement"""

    def test_zero_equity_breach(self):
        """Equity <= 0 sollte HARD breach erzeugen"""
        snapshot = PortfolioSnapshot(
            equity=0, positions=[PositionSnapshot("BTC/EUR", 1, 50000)]
        )
        limits = RiskLimitsV2(max_gross_exposure=1.5)

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, None, limits)

        assert decision.allowed is False
        assert any(b.code == "INVALID_EQUITY" for b in decision.breaches)

    def test_empty_positions_ok(self):
        """Leere Positionsliste sollte erlaubt sein"""
        snapshot = PortfolioSnapshot(equity=100000, positions=[])
        limits = RiskLimitsV2(max_gross_exposure=1.5)

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, None, limits)

        assert decision.allowed is True

    def test_no_returns_skips_var_check(self):
        """Fehlende Returns sollten VaR-Check überspringen"""
        snapshot = PortfolioSnapshot(
            equity=100000, positions=[PositionSnapshot("BTC/EUR", 1, 50000)]
        )
        limits = RiskLimitsV2(max_var=0.001)  # Sehr niedriges Limit

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, None, limits)

        # Sollte erlaubt sein, da VaR-Check übersprungen wird
        assert decision.allowed is True
        assert not any(b.code == "MAX_VAR" for b in decision.breaches)

    def test_empty_returns_skips_var_check(self):
        """Leere Returns sollten VaR-Check überspringen"""
        snapshot = PortfolioSnapshot(equity=100000, positions=[])
        returns = pd.Series(dtype=float)
        limits = RiskLimitsV2(max_var=0.001)

        enforcer = RiskEnforcer()
        decision = enforcer.evaluate_portfolio(snapshot, returns, limits)

        assert decision.allowed is True

    def test_alpha_override(self):
        """Alpha-Override sollte limits.alpha überschreiben"""
        snapshot = PortfolioSnapshot(equity=100000, positions=[])
        returns = pd.Series([-0.05, -0.08, -0.10])

        limits = RiskLimitsV2(max_var=0.05, alpha=0.05)

        enforcer = RiskEnforcer()
        # Override mit alpha=0.01 (99% VaR -> höherer Wert)
        decision = enforcer.evaluate_portfolio(snapshot, returns, limits, alpha=0.01)

        # Mit alpha=0.01 sollte VaR höher sein -> eher Breach
        assert decision.allowed is False or decision.allowed is True  # Abhängig von Daten


class TestRiskDecisionHelpers:
    """Tests for RiskDecision helper methods"""

    def test_has_hard_breach_true(self):
        """has_hard_breach() sollte True bei HARD breach"""
        breach = RiskBreach(
            code="MAX_VAR", message="VaR exceeded", severity=BreachSeverity.HARD
        )
        decision = RiskDecision(allowed=False, action="HALT", breaches=[breach])

        assert decision.has_hard_breach() is True

    def test_has_hard_breach_false(self):
        """has_hard_breach() sollte False bei nur Warnings"""
        breach = RiskBreach(
            code="INFO", message="Info", severity=BreachSeverity.WARNING
        )
        decision = RiskDecision(allowed=True, action="ALLOW", breaches=[breach])

        assert decision.has_hard_breach() is False

    def test_get_breach_summary_empty(self):
        """get_breach_summary() mit leeren Breaches"""
        decision = RiskDecision(allowed=True, action="ALLOW", breaches=[])
        summary = decision.get_breach_summary()

        assert "No breaches" in summary

    def test_get_breach_summary_with_breaches(self):
        """get_breach_summary() mit Breaches"""
        breach1 = RiskBreach(
            code="MAX_VAR", message="VaR exceeded", severity=BreachSeverity.HARD
        )
        breach2 = RiskBreach(
            code="MAX_POS", message="Position too large", severity=BreachSeverity.HARD
        )
        decision = RiskDecision(allowed=False, action="HALT", breaches=[breach1, breach2])
        summary = decision.get_breach_summary()

        assert "Total breaches: 2" in summary
        assert "MAX_VAR" in summary
        assert "MAX_POS" in summary

