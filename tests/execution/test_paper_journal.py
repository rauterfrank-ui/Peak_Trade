"""
Tests for WP1B - Trade Journal & Daily Summary

Tests:
- Journal entry creation
- JSONL persistence
- Daily summary generation
- Deterministic output
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import tempfile

import pytest

from src.execution.contracts import OrderSide, OrderState
from src.execution.paper.daily_summary import DailySummary, DailySummaryGenerator
from src.execution.paper.journal import JournalEntry, TradeJournal
from src.execution.position_ledger import PositionLedger


class TestTradeJournal:
    """Test trade journal."""

    def test_add_entry(self):
        """Test adding entry to journal."""
        journal = TradeJournal()

        entry = JournalEntry(
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            client_order_id="test_001",
            symbol="BTC/USD",
            side=OrderSide.BUY,
            quantity=Decimal("1.0"),
            avg_price=Decimal("50000"),
            total_fee=Decimal("50"),
            order_state=OrderState.FILLED,
        )

        journal.add_entry(entry)

        assert len(journal.entries) == 1
        assert journal.entries[0].client_order_id == "test_001"

    def test_journal_summary(self):
        """Test journal summary statistics."""
        journal = TradeJournal()

        # Add 3 entries
        for i in range(3):
            entry = JournalEntry(
                timestamp=datetime(2025, 1, 1, 10, i, 0),
                client_order_id=f"test_{i:03d}",
                symbol="BTC/USD",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                quantity=Decimal("1.0"),
                avg_price=Decimal("50000"),
                total_fee=Decimal("50"),
                order_state=OrderState.FILLED,
            )
            journal.add_entry(entry)

        summary = journal.get_summary()

        assert summary["total_trades"] == 3
        assert summary["buy_count"] == 2
        assert summary["sell_count"] == 1
        assert Decimal(summary["total_volume"]) == Decimal("150000")  # 3 * 50000
        assert Decimal(summary["total_fees"]) == Decimal("150")  # 3 * 50

    def test_journal_persist_jsonl(self):
        """Test journal persists to JSONL."""
        journal = TradeJournal()

        entry = JournalEntry(
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            client_order_id="test_001",
            symbol="BTC/USD",
            side=OrderSide.BUY,
            quantity=Decimal("1.0"),
            avg_price=Decimal("50000"),
            total_fee=Decimal("50"),
            order_state=OrderState.FILLED,
        )
        journal.add_entry(entry)

        # Write to temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "journal.jsonl"
            journal.write_to_file(output_path)

            # Check file exists
            assert output_path.exists()

            # Read back
            with open(output_path) as f:
                lines = f.readlines()

            assert len(lines) == 1
            assert "test_001" in lines[0]
            assert "BTC/USD" in lines[0]

    def test_journal_entry_to_dict(self):
        """Test journal entry serialization."""
        entry = JournalEntry(
            timestamp=datetime(2025, 1, 1, 10, 0, 0),
            client_order_id="test_001",
            symbol="BTC/USD",
            side=OrderSide.BUY,
            quantity=Decimal("1.0"),
            avg_price=Decimal("50000"),
            total_fee=Decimal("50"),
            order_state=OrderState.FILLED,
            metadata={"test": "value"},
        )

        d = entry.to_dict()

        assert d["client_order_id"] == "test_001"
        assert d["symbol"] == "BTC/USD"
        assert d["side"] == "BUY"
        assert d["quantity"] == "1.0"
        assert d["metadata"]["test"] == "value"

    def test_get_trades_by_symbol(self):
        """Test filtering trades by symbol."""
        journal = TradeJournal()

        # Add BTC and ETH trades
        journal.add_entry(
            JournalEntry(
                timestamp=datetime.utcnow(),
                client_order_id="btc_001",
                symbol="BTC/USD",
                side=OrderSide.BUY,
                quantity=Decimal("1.0"),
                avg_price=Decimal("50000"),
                total_fee=Decimal("50"),
                order_state=OrderState.FILLED,
            )
        )
        journal.add_entry(
            JournalEntry(
                timestamp=datetime.utcnow(),
                client_order_id="eth_001",
                symbol="ETH/USD",
                side=OrderSide.BUY,
                quantity=Decimal("10.0"),
                avg_price=Decimal("3000"),
                total_fee=Decimal("30"),
                order_state=OrderState.FILLED,
            )
        )

        btc_trades = journal.get_trades_by_symbol("BTC/USD")
        assert len(btc_trades) == 1
        assert btc_trades[0].symbol == "BTC/USD"

    def test_get_trades_by_date(self):
        """Test filtering trades by date."""
        journal = TradeJournal()

        # Add trades on different dates
        journal.add_entry(
            JournalEntry(
                timestamp=datetime(2025, 1, 1, 10, 0, 0),
                client_order_id="jan1_001",
                symbol="BTC/USD",
                side=OrderSide.BUY,
                quantity=Decimal("1.0"),
                avg_price=Decimal("50000"),
                total_fee=Decimal("50"),
                order_state=OrderState.FILLED,
            )
        )
        journal.add_entry(
            JournalEntry(
                timestamp=datetime(2025, 1, 2, 10, 0, 0),
                client_order_id="jan2_001",
                symbol="BTC/USD",
                side=OrderSide.BUY,
                quantity=Decimal("1.0"),
                avg_price=Decimal("50000"),
                total_fee=Decimal("50"),
                order_state=OrderState.FILLED,
            )
        )

        jan1_trades = journal.get_trades_by_date(datetime(2025, 1, 1))
        assert len(jan1_trades) == 1
        assert jan1_trades[0].client_order_id == "jan1_001"


class TestDailySummaryGenerator:
    """Test daily summary generator."""

    def test_generate_summary(self):
        """Test daily summary generation."""
        journal = TradeJournal()
        position_ledger = PositionLedger(initial_cash=Decimal("100000"))

        # Add trade
        journal.add_entry(
            JournalEntry(
                timestamp=datetime(2025, 1, 1, 10, 0, 0),
                client_order_id="test_001",
                symbol="BTC/USD",
                side=OrderSide.BUY,
                quantity=Decimal("1.0"),
                avg_price=Decimal("50000"),
                total_fee=Decimal("50"),
                order_state=OrderState.FILLED,
            )
        )

        generator = DailySummaryGenerator()
        summary = generator.generate(
            journal=journal,
            position_ledger=position_ledger,
            date=datetime(2025, 1, 1),
        )

        assert summary.date == datetime(2025, 1, 1)
        assert summary.total_trades == 1
        assert summary.total_volume == Decimal("50000")
        assert summary.total_fees == Decimal("50")

    def test_write_markdown(self):
        """Test markdown summary generation."""
        summary = DailySummary(
            date=datetime(2025, 1, 1),
            total_trades=5,
            total_volume=Decimal("250000"),
            total_fees=Decimal("250"),
            net_pnl=Decimal("1500"),
            ending_cash=Decimal("101500"),
            symbols_traded=["BTC/USD", "ETH/USD"],
        )

        generator = DailySummaryGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.md"
            generator.write_markdown(summary, output_path)

            # Check file exists
            assert output_path.exists()

            # Read back
            with open(output_path) as f:
                content = f.read()

            assert "2025-01-01" in content
            assert "Total Trades** | 5" in content
            assert "BTC/USD" in content
            assert "ETH/USD" in content

    def test_empty_journal_summary(self):
        """Test summary with empty journal."""
        journal = TradeJournal()
        position_ledger = PositionLedger(initial_cash=Decimal("100000"))

        generator = DailySummaryGenerator()
        summary = generator.generate(
            journal=journal,
            position_ledger=position_ledger,
            date=datetime(2025, 1, 1),
        )

        assert summary.total_trades == 0
        assert summary.total_volume == Decimal("0")
        assert summary.total_fees == Decimal("0")
