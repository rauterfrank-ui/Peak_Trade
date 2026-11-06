# src/backtest/result.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from . import stats as stats_mod


@dataclass
class BacktestResult:
    """
    Standard-Ergebnisstruktur für einen Backtest.

    Kernfelder:
    - equity_curve: Zeitreihe der Equity (Index = Zeit)
    - drawdown: Zeitreihe des Drawdowns (gleicher Index wie equity_curve)
    - trades: optionaler DataFrame (oder None), z.B. mit Spalten:
        ["timestamp", "side", "units", "price", "pnl", ...]
    - stats: Kennzahlen als Dict, z.B.:
        {"total_return": 0.23, "max_drawdown": -0.15, ...}
    - metadata: Freitext/Meta-Infos (Strategiename, Symbol, Zeitraum etc.)
    """

    equity_curve: pd.Series
    drawdown: pd.Series
    trades: Optional[pd.DataFrame] = None
    stats: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """
        Menschlich lesbare Zusammenfassung der wichtigsten Kennzahlen.
        """
        lines: list[str] = []

        name = self.metadata.get("name", "Backtest")
        lines.append(f"=== {name} – Backtest Summary ===")

        if "total_return" in self.stats:
            lines.append(f"Total Return: {self.stats['total_return']:.2%}")
        if "cagr" in self.stats:
            lines.append(f"CAGR:         {self.stats['cagr']:.2%}")
        if "max_drawdown" in self.stats:
            lines.append(f"Max Drawdown: {self.stats['max_drawdown']:.2%}")
        if "sharpe" in self.stats:
            lines.append(f"Sharpe:       {self.stats['sharpe']:.2f}")

        # Fallback, falls wenig Stats vorhanden sind
        if len(lines) == 1:
            lines.append("Keine detaillierten Stats verfügbar.")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert das Ergebnis in ein Dict mit leicht serialisierbaren Strukturen.
        (Equity/Drawdown/Trades werden separat gespeichert, siehe save_* Methoden.)
        """
        d = asdict(self)
        d["equity_curve"] = "pd.Series(len=%d)" % len(self.equity_curve)
        d["drawdown"] = "pd.Series(len=%d)" % len(self.drawdown)
        if isinstance(self.trades, pd.DataFrame):
            d["trades"] = f"pd.DataFrame(shape={self.trades.shape})"
        else:
            d["trades"] = None
        return d

    # Convenience-Wrapper, delegiert an reporting-Funktionen (siehe src/backtest/reporting.py)
    def save_all_reports(
        self,
        output_dir: str | Path,
        run_name: str = "run",
        save_plots: bool = True,
        save_html: bool = True,
    ) -> None:
        """
        Speichert Equity, Drawdown, Trades, Stats, optional Plots und HTML-Report.
        Die Implementierung erfolgt in src/backtest/reporting.py – diese Methode
        ruft nur den dortigen Helper auf.

        Args:
            output_dir: Output-Verzeichnis
            run_name: Name des Runs
            save_plots: Ob Plots (PNG) erstellt werden sollen
            save_html: Ob HTML-Report erstellt werden soll
        """
        from . import reporting  # lokaler Import, um Zirkularimporte zu vermeiden

        reporting.save_full_report(
            result=self,
            output_dir=output_dir,
            run_name=run_name,
            save_plots_flag=save_plots,
            save_html_flag=save_html,
        )
