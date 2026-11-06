"""
Daily Summary Generator - WP1B (Phase 1 Shadow Trading)

Generates daily trading summaries in Markdown format.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

from src.execution.paper.journal import TradeJournal
from src.execution.position_ledger import PositionLedger

logger = logging.getLogger(__name__)


@dataclass
class DailySummary:
    """
    Daily trading summary.

    Attributes:
        date: Summary date
        total_trades: Number of trades
        total_volume: Total notional volume
        total_fees: Total fees paid
        net_pnl: Net PnL for the day
        ending_cash: Cash balance at end of day
        symbols_traded: List of symbols traded
        metadata: Additional metadata
    """

    date: datetime
    total_trades: int
    total_volume: Decimal
    total_fees: Decimal
    net_pnl: Decimal
    ending_cash: Decimal
    symbols_traded: List[str]
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DailySummaryGenerator:
    """
    Generates daily trading summaries.

    Usage:
        >>> generator = DailySummaryGenerator()
        >>> summary = generator.generate(journal, position_ledger, date)
        >>> generator.write_markdown(summary, Path("daily_summary.md"))
    """

    def generate(
        self,
        journal: TradeJournal,
        position_ledger: PositionLedger,
        date: datetime,
        current_prices: Optional[Dict[str, Decimal]] = None,
    ) -> DailySummary:
        """
        Generate daily summary.

        Args:
            journal: Trade journal
            position_ledger: Position ledger
            date: Date to summarize
            current_prices: Current market prices (for PnL calc)

        Returns:
            DailySummary
        """
        if current_prices is None:
            current_prices = {}

        # Filter journal entries for date
        entries = journal.get_trades_by_date(date)

        # Calculate statistics
        total_trades = len(entries)
        total_volume = sum(e.quantity * e.avg_price for e in entries)
        total_fees = sum(e.total_fee for e in entries)
        symbols_traded = sorted(set(e.symbol for e in entries))

        # Calculate PnL
        net_pnl = position_ledger.get_total_pnl(current_prices)

        # Get ending cash
        ending_cash = position_ledger.get_cash_balance()

        return DailySummary(
            date=date,
            total_trades=total_trades,
            total_volume=total_volume,
            total_fees=total_fees,
            net_pnl=net_pnl,
            ending_cash=ending_cash,
            symbols_traded=symbols_traded,
        )

    def write_markdown(
        self,
        summary: DailySummary,
        output_path: Path,
    ) -> None:
        """
        Write summary to Markdown file.

        Args:
            summary: Daily summary
            output_path: Path to write to
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate markdown
        md = self._generate_markdown(summary)

        # Write to file
        with open(output_path, "w") as f:
            f.write(md)

        logger.info(f"Daily summary written to {output_path}")

    def _generate_markdown(self, summary: DailySummary) -> str:
        """
        Generate markdown for summary.

        Args:
            summary: Daily summary

        Returns:
            Markdown string
        """
        date_str = summary.date.strftime("%Y-%m-%d")

        md = f"""# Daily Trading Summary - {date_str}

## 📊 Overview

| Metric | Value |
|--------|-------|
| **Date** | {date_str} |
| **Total Trades** | {summary.total_trades} |
| **Total Volume** | ${summary.total_volume:,.2f} |
| **Total Fees** | ${summary.total_fees:,.2f} |
| **Net PnL** | ${summary.net_pnl:,.2f} |
| **Ending Cash** | ${summary.ending_cash:,.2f} |

---

## 📈 Performance Metrics

**Return on Capital:**
```
Net PnL / Initial Capital = {(summary.net_pnl / summary.ending_cash * 100) if summary.ending_cash > 0 else Decimal("0"):.4f}%
```

**Fee Ratio:**
```
Total Fees / Total Volume = {(summary.total_fees / summary.total_volume * 100) if summary.total_volume > 0 else Decimal("0"):.4f}%
```

---

## 🎯 Symbols Traded

{self._format_symbols_list(summary.symbols_traded)}

---

## 📝 Notes

- This is a **shadow trading** (paper) summary
- All fills are simulated with deterministic slippage/fees
- PnL is mark-to-market based on current prices

---

**Generated:** {datetime.utcnow().isoformat()}Z
"""

        return md

    def _format_symbols_list(self, symbols: List[str]) -> str:
        """
        Format symbols list for markdown.

        Args:
            symbols: List of symbols

        Returns:
            Markdown string
        """
        if not symbols:
            return "_(No trades)_"

        return "\n".join(f"- {symbol}" for symbol in symbols)
