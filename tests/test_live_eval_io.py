"""Tests for live session evaluation IO."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.live_eval.live_session_io import read_fills_csv


def test_read_fills_csv_basic():
    """Test basic CSV parsing with valid data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "fills.csv"
        csv_path.write_text(
            "ts,symbol,side,qty,fill_price\n"
            "2025-01-15T10:00:00Z,BTC/USD,buy,0.1,50000.0\n"
            "2025-01-15T10:05:00Z,ETH/USD,sell,1.5,3000.0\n"
        )

        fills = read_fills_csv(csv_path)

        assert len(fills) == 2

        # First fill
        assert fills[0].ts == datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)
        assert fills[0].symbol == "BTC/USD"
        assert fills[0].side == "buy"
        assert fills[0].qty == 0.1
        assert fills[0].fill_price == 50000.0

        # Second fill
        assert fills[1].ts == datetime(2025, 1, 15, 10, 5, 0, tzinfo=UTC)
        assert fills[1].symbol == "ETH/USD"
        assert fills[1].side == "sell"
        assert fills[1].qty == 1.5
        assert fills[1].fill_price == 3000.0


def test_read_fills_csv_timezone_aware():
    """Test that timestamps are timezone-aware (UTC)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "fills.csv"
        csv_path.write_text(
            "ts,symbol,side,qty,fill_price\n"
            "2025-01-15T10:00:00Z,BTC/USD,buy,0.1,50000.0\n"
        )

        fills = read_fills_csv(csv_path)
        assert fills[0].ts.tzinfo is not None
        assert fills[0].ts.tzinfo == UTC


def test_read_fills_csv_side_validation():
    """Test that invalid sides are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "fills.csv"
        csv_path.write_text(
            "ts,symbol,side,qty,fill_price\n"
            "2025-01-15T10:00:00Z,BTC/USD,invalid_side,0.1,50000.0\n"
        )

        with pytest.raises(ValueError, match="Invalid side"):
            read_fills_csv(csv_path, strict=True)


def test_read_fills_csv_invalid_float():
    """Test handling of invalid float values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "fills.csv"
        csv_path.write_text(
            "ts,symbol,side,qty,fill_price\n"
            "2025-01-15T10:00:00Z,BTC/USD,buy,not_a_number,50000.0\n"
        )

        with pytest.raises(ValueError, match="Parse error"):
            read_fills_csv(csv_path, strict=True)


def test_read_fills_csv_missing_columns():
    """Test error handling for missing required columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "fills.csv"
        csv_path.write_text(
            "ts,symbol,side\n"
            "2025-01-15T10:00:00Z,BTC/USD,buy\n"
        )

        with pytest.raises(ValueError, match="must contain columns"):
            read_fills_csv(csv_path)


def test_read_fills_csv_file_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        read_fills_csv(Path("/nonexistent/fills.csv"))


def test_read_fills_csv_best_effort_mode():
    """Test best-effort mode skips invalid rows."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "fills.csv"
        csv_path.write_text(
            "ts,symbol,side,qty,fill_price\n"
            "2025-01-15T10:00:00Z,BTC/USD,buy,0.1,50000.0\n"
            "invalid_timestamp,ETH/USD,sell,1.5,3000.0\n"
            "2025-01-15T10:10:00Z,LTC/USD,buy,2.0,100.0\n"
        )

        # Should not raise in best-effort mode
        fills = read_fills_csv(csv_path, strict=False)

        # Should have 2 valid fills (skipped the invalid one)
        assert len(fills) == 2
        assert fills[0].symbol == "BTC/USD"
        assert fills[1].symbol == "LTC/USD"


def test_read_fills_csv_case_insensitive_side():
    """Test that side values are case-insensitive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "fills.csv"
        csv_path.write_text(
            "ts,symbol,side,qty,fill_price\n"
            "2025-01-15T10:00:00Z,BTC/USD,BUY,0.1,50000.0\n"
            "2025-01-15T10:05:00Z,ETH/USD,SELL,1.5,3000.0\n"
        )

        fills = read_fills_csv(csv_path)

        assert fills[0].side == "buy"
        assert fills[1].side == "sell"
