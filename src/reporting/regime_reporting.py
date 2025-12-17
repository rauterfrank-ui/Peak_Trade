# src/reporting/regime_reporting.py
"""
Peak_Trade Regime-Aware Reporting (Phase - Regime-Aware Reporting)
===================================================================

Spezialisierte Funktionen und Dataclasses für Regime-Aware-Auswertungen.

Komponenten:
- RegimeBucketMetrics: Metriken für einen Regime-Bucket
- RegimeStatsSummary: Zusammenfassung aller Regime-Buckets
- compute_regime_stats: Berechnet Regime-spezifische Kennzahlen
- build_regime_report_section: Erstellt ReportSection für Regime-Analyse

Usage:
    from src.reporting.regime_reporting import compute_regime_stats, build_regime_report_section

    regime_stats = compute_regime_stats(
        equity_series=equity,
        returns_series=returns,
        regime_series=regimes,  # 1=Risk-On, 0=Neutral, -1=Risk-Off
    )
    section = build_regime_report_section(regime_stats)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import ReportSection, df_to_markdown, format_metric

# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class RegimeBucketMetrics:
    """
    Metriken für einen Regime-Bucket (z.B. Risk-On, Neutral, Risk-Off).

    Attributes:
        regime_value: Regime-Wert (1=Risk-On, 0=Neutral, -1=Risk-Off)
        name: Lesbarer Name (z.B. "Risk-On", "Neutral", "Risk-Off")
        time_fraction: Anteil der Bars in diesem Regime (0.0-1.0)
        return_total: Gesamtrendite in diesem Regime
        return_annualized: Annualisierte Rendite (wenn möglich)
        sharpe: Sharpe-Ratio (optional, None wenn zu wenig Daten)
        max_drawdown: Maximaler Drawdown in diesem Regime
        num_trades: Anzahl Trades in diesem Regime (optional)
        win_rate: Win-Rate in diesem Regime (optional, None wenn keine Trades)
    """

    regime_value: int
    name: str
    time_fraction: float
    return_total: float
    return_annualized: float
    sharpe: float | None = None
    max_drawdown: float = 0.0
    num_trades: int = 0
    win_rate: float | None = None
    return_contribution_pct: float | None = None
    time_share_pct: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary für Tabellen."""
        return {
            "Regime": self.name,
            "Bars [%]": f"{self.time_share_pct:.1f}%" if self.time_share_pct is not None else f"{self.time_fraction:.1%}",
            "Time Fraction": f"{self.time_fraction:.1%}",
            "Total Return": format_metric(self.return_total, "return"),
            "Return Contribution [%]": f"{self.return_contribution_pct:.1f}%" if self.return_contribution_pct is not None else "N/A",
            "Annualized Return": format_metric(self.return_annualized, "return") if self.return_annualized else "N/A",
            "Sharpe": f"{self.sharpe:.2f}" if self.sharpe is not None else "N/A",
            "Max Drawdown": format_metric(self.max_drawdown, "drawdown"),
            "Trades": str(self.num_trades),
            "Win Rate": format_metric(self.win_rate, "win_rate") if self.win_rate is not None else "N/A",
        }


@dataclass
class RegimeStatsSummary:
    """
    Zusammenfassung der Regime-Statistiken.

    Attributes:
        buckets: Liste von RegimeBucketMetrics für jeden Regime-Bucket
        overall_return: Gesamtrendite über alle Regimes
        overall_sharpe: Gesamt-Sharpe-Ratio
        notes: Optionale Hinweise (z.B. bei sehr kurzem Sample)
    """

    buckets: list[RegimeBucketMetrics]
    overall_return: float
    overall_sharpe: float
    notes: list[str] = None

    def __post_init__(self):
        """Initialisiert notes als leere Liste falls None."""
        if self.notes is None:
            self.notes = []


# =============================================================================
# REGIME STATS COMPUTATION
# =============================================================================


def compute_regime_stats(
    equity_series: pd.Series,
    returns_series: pd.Series,
    regime_series: pd.Series,
    trades: pd.DataFrame | None = None,
) -> RegimeStatsSummary:
    """
    Berechnet Regime-spezifische Kennzahlen.

    Args:
        equity_series: Equity-Curve (Portfolio-Wert über Zeit)
        returns_series: Returns-Serie (gleicher Index wie equity_series)
        regime_series: Regime-Serie mit Werten 1 (Risk-On), 0 (Neutral), -1 (Risk-Off)
        trades: Optional DataFrame mit Trades (Spalten: entry_time, pnl, etc.)

    Returns:
        RegimeStatsSummary mit Metriken pro Regime-Bucket

    Raises:
        ValueError: Wenn Series nicht kompatibel sind
    """
    # Validierung
    if len(equity_series) != len(returns_series) or len(equity_series) != len(regime_series):
        raise ValueError(
            f"Series müssen gleiche Länge haben: equity={len(equity_series)}, "
            f"returns={len(returns_series)}, regime={len(regime_series)}"
        )

    # Aligniere Indizes
    common_index = equity_series.index.intersection(returns_series.index).intersection(regime_series.index)
    if len(common_index) == 0:
        raise ValueError("Keine gemeinsamen Indizes zwischen Series gefunden")

    equity_aligned = equity_series.reindex(common_index)
    returns_aligned = returns_series.reindex(common_index)
    regime_aligned = regime_series.reindex(common_index).fillna(0).astype(int)

    # Gesamt-Metriken
    overall_return = float((equity_aligned.iloc[-1] / equity_aligned.iloc[0]) - 1.0) if len(equity_aligned) > 0 else 0.0

    # Sharpe-Ratio (annualisiert, falls möglich)
    overall_sharpe = None
    if len(returns_aligned) > 1:
        mean_return = returns_aligned.mean()
        std_return = returns_aligned.std()
        if std_return > 0:
            # Annualisierung (252 Trading-Tage)
            periods_per_year = 252  # Default für tägliche Daten
            if isinstance(returns_aligned.index, pd.DatetimeIndex) and len(returns_aligned) > 1:
                # Berechne tatsächliche Perioden pro Jahr
                time_span = (returns_aligned.index[-1] - returns_aligned.index[0]).days
                if time_span > 0:
                    periods_per_year = (len(returns_aligned) / time_span) * 365.25

            overall_sharpe = float((mean_return / std_return) * np.sqrt(periods_per_year))

    # Regime-Buckets
    unique_regimes = sorted(regime_aligned.unique())
    buckets: list[RegimeBucketMetrics] = []
    notes: list[str] = []

    # Regime-Namen-Mapping
    regime_names = {
        1: "Risk-On",
        0: "Neutral",
        -1: "Risk-Off",
    }

    for regime_val in unique_regimes:
        regime_mask = regime_aligned == regime_val
        regime_returns = returns_aligned[regime_mask]
        regime_equity = equity_aligned[regime_mask]

        if len(regime_returns) == 0:
            continue

        # Time Fraction
        time_fraction = float(regime_mask.sum() / len(regime_aligned))

        # Total Return
        if len(regime_equity) > 1:
            regime_return = float((regime_equity.iloc[-1] / regime_equity.iloc[0]) - 1.0)
        else:
            regime_return = 0.0

        # Annualized Return
        regime_return_annualized = None
        if len(regime_returns) > 1 and isinstance(regime_returns.index, pd.DatetimeIndex):
            time_span_days = (regime_returns.index[-1] - regime_returns.index[0]).days
            if time_span_days > 0:
                periods_per_year = (len(regime_returns) / time_span_days) * 365.25
                regime_return_annualized = float((1.0 + regime_return) ** (periods_per_year / len(regime_returns)) - 1.0)

        # Sharpe-Ratio
        sharpe = None
        if len(regime_returns) > 1:
            mean_ret = regime_returns.mean()
            std_ret = regime_returns.std()
            if std_ret > 0:
                periods_per_year = 252  # Default
                if isinstance(regime_returns.index, pd.DatetimeIndex) and len(regime_returns) > 1:
                    time_span = (regime_returns.index[-1] - regime_returns.index[0]).days
                    if time_span > 0:
                        periods_per_year = (len(regime_returns) / time_span) * 365.25
                sharpe = float((mean_ret / std_ret) * np.sqrt(periods_per_year))

        # Max Drawdown
        max_dd = 0.0
        if len(regime_equity) > 1:
            peak = regime_equity.expanding(min_periods=1).max()
            dd = (regime_equity - peak) / peak
            max_dd = float(dd.min())

        # Trade-Statistiken (optional)
        num_trades = 0
        win_rate = None
        if trades is not None and len(trades) > 0:
            # Versuche entry_time zu finden
            entry_col = None
            for col in ["entry_time", "timestamp", "time", "date"]:
                if col in trades.columns:
                    entry_col = col
                    break

            if entry_col:
                # Konvertiere zu DatetimeIndex falls nötig
                trade_times = pd.to_datetime(trades[entry_col])
                regime_trades = trades[trade_times.isin(regime_returns.index)]
                num_trades = len(regime_trades)

                if num_trades > 0 and "pnl" in regime_trades.columns:
                    winning = (regime_trades["pnl"] > 0).sum()
                    win_rate = float(winning / num_trades) if num_trades > 0 else None

        # Warnung bei sehr kurzem Sample
        if time_fraction < 0.05:
            notes.append(f"{regime_names.get(regime_val, f'Regime {regime_val}')} hat nur {time_fraction:.1%} der Zeit - Metriken möglicherweise unzuverlässig")

        bucket = RegimeBucketMetrics(
            regime_value=regime_val,
            name=regime_names.get(regime_val, f"Regime {regime_val}"),
            time_fraction=time_fraction,
            return_total=regime_return,
            return_annualized=regime_return_annualized if regime_return_annualized is not None else 0.0,
            sharpe=sharpe,
            max_drawdown=max_dd,
            num_trades=num_trades,
            win_rate=win_rate,
            return_contribution_pct=None,  # Wird nach Berechnung aller Buckets gesetzt
            time_share_pct=None,  # Wird nach Berechnung aller Buckets gesetzt
        )
        buckets.append(bucket)

    # Berechne Contribution & Time-Share für alle Buckets
    # Gesamt-Return über alle Regimes (kumuliert)
    total_return_sum = sum(bucket.return_total for bucket in buckets)
    len(regime_aligned)

    for bucket in buckets:
        # Time Share als Prozent
        bucket.time_share_pct = float(bucket.time_fraction * 100.0)

        # Return Contribution als Prozent
        if total_return_sum != 0.0:
            bucket.return_contribution_pct = float((bucket.return_total / total_return_sum) * 100.0)
        elif overall_return != 0.0:
            # Fallback: Nutze overall_return wenn total_return_sum 0 ist
            bucket.return_contribution_pct = float((bucket.return_total / overall_return) * 100.0) if overall_return != 0.0 else None
        else:
            bucket.return_contribution_pct = None

    return RegimeStatsSummary(
        buckets=buckets,
        overall_return=overall_return,
        overall_sharpe=overall_sharpe if overall_sharpe is not None else 0.0,
        notes=notes,
    )


# =============================================================================
# REPORT SECTION BUILDERS
# =============================================================================


def build_regime_report_section(regime_stats: RegimeStatsSummary) -> ReportSection:
    """
    Erstellt eine ReportSection mit Regime-Analyse.

    Args:
        regime_stats: RegimeStatsSummary mit berechneten Metriken

    Returns:
        ReportSection mit Tabelle und Summary-Text
    """
    if not regime_stats.buckets:
        return ReportSection(
            title="Regime-Analyse",
            content_markdown="*Keine Regime-Daten verfügbar*",
        )

    # Erstelle DataFrame für Tabelle
    rows = []
    for bucket in regime_stats.buckets:
        rows.append(bucket.to_dict())

    df = pd.DataFrame(rows)

    # Markdown-Tabelle
    table_md = df_to_markdown(df, float_format=".4f")

    # Summary-Text
    summary_lines = []

    # Finde wichtigste Regime
    risk_on_bucket = next((b for b in regime_stats.buckets if b.regime_value == 1), None)
    risk_off_bucket = next((b for b in regime_stats.buckets if b.regime_value == -1), None)
    neutral_bucket = next((b for b in regime_stats.buckets if b.regime_value == 0), None)

    if risk_on_bucket:
        contribution_pct = (risk_on_bucket.return_total / regime_stats.overall_return * 100) if regime_stats.overall_return != 0 else 0
        summary_lines.append(
            f"- **Risk-On** trägt {contribution_pct:.1f}% zur Gesamtrendite bei "
            f"({risk_on_bucket.time_fraction:.1%} der Zeit, {risk_on_bucket.num_trades} Trades)"
        )

    if risk_off_bucket:
        summary_lines.append(
            f"- **Risk-Off** hat einen Max-Drawdown von {format_metric(risk_off_bucket.max_drawdown, 'drawdown')} "
            f"({risk_off_bucket.time_fraction:.1%} der Zeit)"
        )

    if neutral_bucket:
        summary_lines.append(
            f"- **Neutral** hat {neutral_bucket.num_trades} Trades "
            f"({neutral_bucket.time_fraction:.1%} der Zeit)"
        )

    # Gesamt-Sharpe
    if regime_stats.overall_sharpe is not None and regime_stats.overall_sharpe != 0:
        summary_lines.append(f"- **Gesamt-Sharpe:** {regime_stats.overall_sharpe:.2f}")

    # Warnungen/Hinweise
    if regime_stats.notes:
        summary_lines.append("")
        summary_lines.append("**Hinweise:**")
        for note in regime_stats.notes:
            summary_lines.append(f"- {note}")

    content = "\n\n".join([
        "### Regime-Performance Übersicht",
        "",
        table_md,
        "",
        "### Zusammenfassung",
        "",
        "\n".join(summary_lines) if summary_lines else "*Keine zusätzlichen Informationen verfügbar*",
    ])

    return ReportSection(
        title="Regime-Analyse",
        content_markdown=content,
    )

