"""
Trade Journal - WP1B (Phase 1 Shadow Trading)

Append-only trade journal in JSONL format.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.execution.contracts import OrderSide, OrderState

logger = logging.getLogger(__name__)


@dataclass
class JournalEntry:
    """
    Single journal entry (one trade).

    Attributes:
        timestamp: Entry timestamp
        client_order_id: Order ID
        symbol: Symbol traded
        side: Order side (BUY/SELL)
        quantity: Quantity filled
        avg_price: Average fill price
        total_fee: Total fees
        order_state: Final order state
        metadata: Additional metadata
    """

    timestamp: datetime
    client_order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    avg_price: Decimal
    total_fee: Decimal
    order_state: OrderState
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": str(self.quantity),
            "avg_price": str(self.avg_price),
            "total_fee": str(self.total_fee),
            "order_state": self.order_state.value,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)


class TradeJournal:
    """
    Append-only trade journal.

    Stores all trades in memory and optionally persists to JSONL file.

    Usage:
        >>> journal = TradeJournal(persist_path="trades.jsonl")
        >>> journal.add_entry(entry)
        >>> journal.write_to_file()
    """

    def __init__(self, persist_path: Optional[Path] = None):
        """
        Initialize trade journal.

        Args:
            persist_path: Optional path to persist journal
        """
        self.entries: List[JournalEntry] = []
        self.persist_path = persist_path

        if persist_path:
            logger.info(f"Trade journal will persist to: {persist_path}")

    def add_entry(self, entry: JournalEntry) -> None:
        """
        Add entry to journal.

        Args:
            entry: Journal entry to add
        """
        self.entries.append(entry)
        logger.debug(
            f"Journal entry added: {entry.client_order_id} "
            f"{entry.side.value} {entry.quantity} {entry.symbol} @ {entry.avg_price}"
        )

    def write_to_file(self, path: Optional[Path] = None) -> None:
        """
        Write journal to JSONL file.

        Args:
            path: Path to write to (overrides persist_path)
        """
        target_path = path or self.persist_path

        if not target_path:
            logger.warning("No persist path configured, skipping write")
            return

        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSONL
        with open(target_path, "w") as f:
            for entry in self.entries:
                f.write(entry.to_json() + "\n")

        logger.info(
            f"Journal written: {len(self.entries)} entries to {target_path}"
        )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get journal summary statistics.

        Returns:
            Summary dict
        """
        if not self.entries:
            return {
                "total_trades": 0,
                "total_volume": "0",
                "total_fees": "0",
                "symbols": [],
            }

        total_volume = sum(
            entry.quantity * entry.avg_price for entry in self.entries
        )
        total_fees = sum(entry.total_fee for entry in self.entries)
        symbols = sorted(set(entry.symbol for entry in self.entries))

        # Count by side
        buy_count = sum(1 for e in self.entries if e.side == OrderSide.BUY)
        sell_count = sum(1 for e in self.entries if e.side == OrderSide.SELL)

        return {
            "total_trades": len(self.entries),
            "total_volume": str(total_volume),
            "total_fees": str(total_fees),
            "symbols": symbols,
            "buy_count": buy_count,
            "sell_count": sell_count,
        }

    def get_trades_by_symbol(self, symbol: str) -> List[JournalEntry]:
        """
        Get all trades for a symbol.

        Args:
            symbol: Symbol to filter

        Returns:
            List of journal entries
        """
        return [e for e in self.entries if e.symbol == symbol]

    def get_trades_by_date(self, date: datetime) -> List[JournalEntry]:
        """
        Get all trades for a specific date.

        Args:
            date: Date to filter (only date part used)

        Returns:
            List of journal entries
        """
        target_date = date.date()
        return [e for e in self.entries if e.timestamp.date() == target_date]
