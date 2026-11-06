# tests/test_reporting_regime_reporting.py
"""
Tests für Regime-Aware Reporting (Phase - Regime-Aware Reporting)
==================================================================
"""

from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.reporting.regime_reporting import (
    RegimeBucketMetrics,
    RegimeStatsSummary,
    compute_regime_stats,
    build_regime_report_section,
)


class TestRegimeBucketMetrics:
    """Tests für RegimeBucketMetrics Dataclass."""

    def test_to_dict(self):
        """Test Konvertierung zu Dictionary."""
        bucket = RegimeBucketMetrics(
            regime_value=1,
            name="Risk-On",
            time_fraction=0.5,
            return_total=0.15,
            return_annualized=0.20,
            sharpe=1.5,
            max_drawdown=-0.10,
            num_trades=10,
            win_rate=0.6,
        )

        result = bucket.to_dict()
        assert result["Regime"] == "Risk-On"
        assert result["Time Fraction"] == "50.0%"
        assert "15.00%" in result["Total Return"]
        assert result["Trades"] == "10"


class TestComputeRegimeStats:
    """Tests für compute_regime_stats Funktion."""

    def test_basic_regime_stats(self):
        """Test grundlegende Regime-Statistik-Berechnung."""
        # Erstelle synthetische Daten
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")

        # Equity: Start bei 10000, steigt in Risk-On, fällt in Risk-Off
        equity = pd.Series(10000.0, index=dates)
        equity.iloc[0:50] = np.linspace(10000, 11000, 50)  # Risk-On: +10%
        equity.iloc[50:80] = np.linspace(11000, 10800, 30)  # Neutral: -1.8%
        equity.iloc[80:100] = np.linspace(10800, 10500, 20)  # Risk-Off: -2.8%

        # Returns
        returns = equity.pct_change().fillna(0)

        # Regime: 50 Risk-On, 30 Neutral, 20 Risk-Off
        regimes = pd.Series(1, index=dates)
        regimes.iloc[50:80] = 0
        regimes.iloc[80:100] = -1

        # Berechne Stats
        stats = compute_regime_stats(equity, returns, regimes)

        assert len(stats.buckets) == 3
        assert stats.overall_return > 0  # Gesamt-Rendite sollte positiv sein

        # Prüfe Time Fractions
        risk_on = next((b for b in stats.buckets if b.regime_value == 1), None)
        neutral = next((b for b in stats.buckets if b.regime_value == 0), None)
        risk_off = next((b for b in stats.buckets if b.regime_value == -1), None)

        assert risk_on is not None
        assert neutral is not None
        assert risk_off is not None

        assert abs(risk_on.time_fraction - 0.5) < 0.01  # 50/100
        assert abs(neutral.time_fraction - 0.3) < 0.01  # 30/100
        assert abs(risk_off.time_fraction - 0.2) < 0.01  # 20/100

        # Risk-On sollte positive Rendite haben
        assert risk_on.return_total > 0

    def test_regime_stats_with_trades(self):
        """Test Regime-Stats mit Trade-Daten."""
        dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
        equity = pd.Series(10000.0, index=dates)
        returns = equity.pct_change().fillna(0)
        regimes = pd.Series([1] * 25 + [0] * 25, index=dates)

        # Erstelle Trades
        trades = pd.DataFrame(
            {
                "entry_time": [dates[5], dates[15], dates[30], dates[40]],
                "pnl": [100, -50, 75, -25],
            }
        )

        stats = compute_regime_stats(equity, returns, regimes, trades=trades)

        risk_on = next((b for b in stats.buckets if b.regime_value == 1), None)
        neutral = next((b for b in stats.buckets if b.regime_value == 0), None)

        assert risk_on is not None
        assert neutral is not None

        # Risk-On sollte 2 Trades haben (indices 5, 15)
        assert risk_on.num_trades == 2
        # Neutral sollte 2 Trades haben (indices 30, 40)
        assert neutral.num_trades == 2

    def test_incompatible_series_length(self):
        """Test Fehlerbehandlung bei inkompatiblen Series-Längen."""
        equity = pd.Series([10000, 10100, 10200])
        returns = pd.Series([0.01, 0.01])
        regimes = pd.Series([1, 0, -1])

        with pytest.raises(ValueError, match="gleiche Länge"):
            compute_regime_stats(equity, returns, regimes)

    def test_empty_regime_series(self):
        """Test mit leerer Regime-Series."""
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        equity = pd.Series(10000.0, index=dates)
        returns = equity.pct_change().fillna(0)
        regimes = pd.Series([], index=pd.DatetimeIndex([]))

        # Leere Series hat Länge 0 -> Längen-Mismatch
        with pytest.raises(ValueError, match="gleiche Länge"):
            compute_regime_stats(equity, returns, regimes)


class TestBuildRegimeReportSection:
    """Tests für build_regime_report_section Funktion."""

    def test_build_section_with_buckets(self):
        """Test Erstellung einer ReportSection mit Buckets."""
        buckets = [
            RegimeBucketMetrics(
                regime_value=1,
                name="Risk-On",
                time_fraction=0.5,
                return_total=0.15,
                return_annualized=0.20,
                sharpe=1.5,
                max_drawdown=-0.05,
                num_trades=10,
                win_rate=0.6,
            ),
            RegimeBucketMetrics(
                regime_value=-1,
                name="Risk-Off",
                time_fraction=0.2,
                return_total=-0.05,
                return_annualized=-0.10,
                sharpe=-0.5,
                max_drawdown=-0.15,
                num_trades=2,
                win_rate=0.0,
            ),
        ]

        summary = RegimeStatsSummary(
            buckets=buckets,
            overall_return=0.10,
            overall_sharpe=1.0,
        )

        section = build_regime_report_section(summary)

        assert section.title == "Regime-Analyse"
        assert "Risk-On" in section.content_markdown
        assert "Risk-Off" in section.content_markdown
        assert "|" in section.content_markdown  # Tabelle vorhanden

    def test_build_section_empty_buckets(self):
        """Test mit leeren Buckets."""
        summary = RegimeStatsSummary(
            buckets=[],
            overall_return=0.0,
            overall_sharpe=0.0,
        )

        section = build_regime_report_section(summary)

        assert section.title == "Regime-Analyse"
        assert "Keine Regime-Daten" in section.content_markdown

    def test_regime_stats_contribution_and_time_share(self):
        """Test Contribution & Time-Share Berechnung."""
        # Erstelle synthetische Daten mit klaren Regime-Phasen
        dates = pd.date_range(start="2023-01-01", periods=6, freq="D")

        # Equity: Start bei 10000
        equity = pd.Series(10000.0, index=dates)
        # Returns: Risk-Off: [0.01, -0.01], Neutral: [0.02, 0.00], Risk-On: [0.03, 0.01]
        returns = pd.Series([0.01, -0.01, 0.02, 0.00, 0.03, 0.01], index=dates)
        # Equity berechnen
        equity.iloc[0] = 10000.0
        for i in range(1, len(equity)):
            equity.iloc[i] = equity.iloc[i - 1] * (1.0 + returns.iloc[i])

        # Regime: 2 Risk-Off, 2 Neutral, 2 Risk-On
        regimes = pd.Series([-1, -1, 0, 0, 1, 1], index=dates)

        # Berechne Stats
        stats = compute_regime_stats(equity, returns, regimes)

        assert len(stats.buckets) == 3

        # Prüfe Time Share (jeder Regime sollte ~33.33% haben: 2/6)
        for bucket in stats.buckets:
            assert bucket.time_share_pct is not None
            assert abs(bucket.time_share_pct - (100.0 * 2 / 6)) < 1.0  # ~33.33%

        # Prüfe Return Contribution
        # Gesamt-Return = (10000 -> 10000*1.01*0.99*1.02*1.00*1.03*1.01) / 10000 - 1
        # = 1.01 * 0.99 * 1.02 * 1.00 * 1.03 * 1.01 - 1
        # ≈ 0.0606 (6.06%)
        # Risk-Off: (1.01 * 0.99 - 1) ≈ -0.0001 ≈ 0%
        # Neutral: (1.02 * 1.00 - 1) = 0.02 = 2%
        # Risk-On: (1.03 * 1.01 - 1) ≈ 0.0403 = 4.03%

        risk_off = next((b for b in stats.buckets if b.regime_value == -1), None)
        neutral = next((b for b in stats.buckets if b.regime_value == 0), None)
        risk_on = next((b for b in stats.buckets if b.regime_value == 1), None)

        assert risk_off is not None
        assert neutral is not None
        assert risk_on is not None

        # Contribution sollte gesetzt sein
        assert risk_off.return_contribution_pct is not None
        assert neutral.return_contribution_pct is not None
        assert risk_on.return_contribution_pct is not None

        # Risk-On sollte den größten Beitrag haben
        assert risk_on.return_contribution_pct > neutral.return_contribution_pct
        assert risk_on.return_contribution_pct > risk_off.return_contribution_pct

    def test_regime_stats_contribution_sum_approximately_100(self):
        """Test dass Contribution-Summe ungefähr 100% ergibt."""
        dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
        equity = pd.Series(10000.0, index=dates)
        returns = pd.Series([0.01] * 5 + [-0.01] * 5, index=dates)
        # Equity berechnen
        equity.iloc[0] = 10000.0
        for i in range(1, len(equity)):
            equity.iloc[i] = equity.iloc[i - 1] * (1.0 + returns.iloc[i])

        regimes = pd.Series([1] * 5 + [-1] * 5, index=dates)

        stats = compute_regime_stats(equity, returns, regimes)

        # Summe der Contributions sollte ~100% sein
        contrib_sum = sum(
            b.return_contribution_pct
            for b in stats.buckets
            if b.return_contribution_pct is not None
        )

        # Toleranz: ±5% (wegen Rundungsfehlern)
        assert abs(contrib_sum - 100.0) < 5.0 or contrib_sum == 0.0  # 0% wenn total_return_sum = 0
