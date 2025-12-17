"""Tests für Execution Latency Tracker Modul."""
import pandas as pd
import pytest

from src.execution.metrics.execution_latency import (
    ExecutionLatencyMeasures,
    ExecutionLatencySummary,
    ExecutionLatencyTimestamps,
    compute_latency_measures,
    create_latency_timestamps_from_trades_and_signals,
    latency_measures_to_df,
    latency_summary_to_dict,
    summarize_latency,
)


class TestExecutionLatency:
    """Test-Suite für Execution Latency Tracker."""

    def test_compute_latency_measures_full(self):
        """Test: Vollständige Latenz-Berechnung mit allen Timestamps."""
        ts = ExecutionLatencyTimestamps(
            session_id="TEST",
            order_id="ORDER_1",
            symbol="BTCEUR",
            side="BUY",
            qty=0.1,
            signal_timestamp=pd.Timestamp("2025-01-01 10:00:00.000"),
            order_sent_timestamp=pd.Timestamp("2025-01-01 10:00:00.500"),
            exchange_ack_timestamp=pd.Timestamp("2025-01-01 10:00:00.600"),
            first_fill_timestamp=pd.Timestamp("2025-01-01 10:00:00.750"),
            last_fill_timestamp=pd.Timestamp("2025-01-01 10:00:01.000"),
            reference_price=30000.0,
            avg_fill_price=30010.0,
        )

        measures = compute_latency_measures(ts)

        assert measures.order_id == "ORDER_1"
        assert measures.symbol == "BTCEUR"
        assert measures.trigger_delay_ms == pytest.approx(500.0, abs=1.0)
        assert measures.send_to_ack_ms == pytest.approx(100.0, abs=1.0)
        assert measures.send_to_first_fill_ms == pytest.approx(250.0, abs=1.0)
        assert measures.send_to_last_fill_ms == pytest.approx(500.0, abs=1.0)
        assert measures.total_delay_ms == pytest.approx(1000.0, abs=1.0)
        assert measures.slippage == pytest.approx(10.0, abs=0.1)  # (30010 - 30000) * 1 (BUY)

    def test_compute_latency_measures_minimal(self):
        """Test: Minimale Latenz-Berechnung (nur order_sent)."""
        ts = ExecutionLatencyTimestamps(
            session_id="TEST",
            order_id="ORDER_1",
            symbol="BTCEUR",
            side="BUY",
            qty=0.1,
            order_sent_timestamp=pd.Timestamp("2025-01-01 10:00:00.500"),
        )

        measures = compute_latency_measures(ts)

        assert measures.trigger_delay_ms is None
        assert measures.send_to_ack_ms is None
        assert measures.send_to_first_fill_ms is None
        assert measures.total_delay_ms is None
        assert measures.slippage is None

    def test_compute_latency_measures_slippage_sell(self):
        """Test: Slippage-Berechnung für SELL-Order."""
        ts = ExecutionLatencyTimestamps(
            session_id="TEST",
            order_id="ORDER_1",
            symbol="BTCEUR",
            side="SELL",
            qty=0.1,
            order_sent_timestamp=pd.Timestamp("2025-01-01 10:00:00.500"),
            reference_price=30000.0,
            avg_fill_price=29990.0,  # Schlechterer Fill beim SELL
        )

        measures = compute_latency_measures(ts)

        # SELL: (29990 - 30000) * (-1) = 10.0 (positiver Slippage = ungünstig)
        assert measures.slippage == pytest.approx(10.0, abs=0.1)

    def test_summarize_latency_multiple_orders(self):
        """Test: Aggregation über mehrere Orders."""
        measures = [
            ExecutionLatencyMeasures(
                order_id=f"ORDER_{i}",
                symbol="BTCEUR",
                trigger_delay_ms=100.0 + i * 100,
                send_to_ack_ms=50.0 + i * 10,
                send_to_first_fill_ms=200.0 + i * 50,
                send_to_last_fill_ms=300.0 + i * 50,
                total_delay_ms=400.0 + i * 100,
                slippage=1.0 + i * 0.5,
            )
            for i in range(5)
        ]

        summary = summarize_latency(measures)

        assert summary.count_orders == 5
        assert summary.mean_trigger_delay_ms == pytest.approx(300.0, abs=1.0)  # (100+200+300+400+500)/5
        assert summary.median_trigger_delay_ms == pytest.approx(300.0, abs=1.0)
        assert summary.mean_send_to_first_fill_ms == pytest.approx(300.0, abs=1.0)
        assert summary.mean_slippage == pytest.approx(2.0, abs=0.1)  # (1.0+1.5+2.0+2.5+3.0)/5

    def test_summarize_latency_empty(self):
        """Test: Leere Measures-Liste."""
        summary = summarize_latency([])

        assert summary.count_orders == 0
        assert summary.mean_trigger_delay_ms is None

    def test_summarize_latency_partial_data(self):
        """Test: Nur manche Orders haben alle Felder."""
        measures = [
            ExecutionLatencyMeasures(
                order_id="ORDER_1",
                symbol="BTCEUR",
                trigger_delay_ms=100.0,
                send_to_first_fill_ms=200.0,
            ),
            ExecutionLatencyMeasures(
                order_id="ORDER_2",
                symbol="BTCEUR",
                trigger_delay_ms=None,  # Kein Signal-Timestamp
                send_to_first_fill_ms=300.0,
            ),
        ]

        summary = summarize_latency(measures)

        assert summary.count_orders == 2
        assert summary.mean_trigger_delay_ms == pytest.approx(100.0, abs=1.0)  # Nur ORDER_1
        assert summary.mean_send_to_first_fill_ms == pytest.approx(250.0, abs=1.0)  # (200+300)/2

    def test_latency_measures_to_df(self):
        """Test: Konvertierung zu DataFrame."""
        measures = [
            ExecutionLatencyMeasures(
                order_id="ORDER_1",
                symbol="BTCEUR",
                trigger_delay_ms=100.0,
                send_to_first_fill_ms=200.0,
                slippage=1.5,
            )
        ]

        df = latency_measures_to_df(measures)

        assert len(df) == 1
        assert df["order_id"].iloc[0] == "ORDER_1"
        assert df["trigger_delay_ms"].iloc[0] == pytest.approx(100.0)
        assert df["slippage"].iloc[0] == pytest.approx(1.5)

    def test_latency_measures_to_df_empty(self):
        """Test: Leere Measures-Liste zu DataFrame."""
        df = latency_measures_to_df([])

        assert df.empty
        assert "order_id" in df.columns

    def test_latency_summary_to_dict(self):
        """Test: Summary zu Dictionary."""
        summary = ExecutionLatencySummary(
            count_orders=10,
            mean_trigger_delay_ms=500.0,
            median_trigger_delay_ms=450.0,
            p90_trigger_delay_ms=700.0,
        )

        d = latency_summary_to_dict(summary)

        assert d["count_orders"] == 10
        assert d["mean_trigger_delay_ms"] == 500.0
        assert d["p90_trigger_delay_ms"] == 700.0

    def test_create_latency_timestamps_from_trades(self):
        """Test: Erstelle LatencyTimestamps aus Trades DataFrame."""
        trades_df = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01 10:00:00", periods=3, freq="1min"),
            "price": [30000.0, 30010.0, 30020.0],
            "qty": [0.1, -0.05, 0.15],  # BUY, SELL, BUY
            "symbol": ["BTCEUR"] * 3,
        })

        timestamps = create_latency_timestamps_from_trades_and_signals(
            trades_df=trades_df,
            session_id="TEST_SESSION",
        )

        assert len(timestamps) == 3
        assert timestamps[0].side == "BUY"
        assert timestamps[1].side == "SELL"
        assert timestamps[2].side == "BUY"
        assert timestamps[0].symbol == "BTCEUR"
        assert timestamps[0].session_id == "TEST_SESSION"

    def test_create_latency_timestamps_with_signals(self):
        """Test: Timestamps mit Signal-Verknüpfung."""
        signals_df = pd.DataFrame({
            "signal_id": [1, 2],
            "timestamp": pd.date_range("2025-01-01 10:00:00", periods=2, freq="1min"),
            "symbol": ["BTCEUR"] * 2,
        })

        trades_df = pd.DataFrame({
            "timestamp": [
                pd.Timestamp("2025-01-01 10:00:00.500"),
                pd.Timestamp("2025-01-01 10:01:00.750"),
            ],
            "price": [30000.0, 30010.0],
            "qty": [0.1, 0.05],
            "signal_id": [1, 2],
            "symbol": ["BTCEUR"] * 2,
        })

        timestamps = create_latency_timestamps_from_trades_and_signals(
            trades_df=trades_df,
            signals_df=signals_df,
            session_id="TEST",
        )

        assert len(timestamps) == 2
        assert timestamps[0].signal_id == 1
        assert timestamps[0].signal_timestamp is not None
        assert timestamps[1].signal_id == 2

    def test_create_latency_timestamps_empty(self):
        """Test: Leerer Trades DataFrame."""
        trades_df = pd.DataFrame(columns=["timestamp", "price", "qty"])

        timestamps = create_latency_timestamps_from_trades_and_signals(
            trades_df=trades_df,
            session_id="TEST",
        )

        assert len(timestamps) == 0

    def test_percentile_calculations(self):
        """Test: Perzentil-Berechnungen (P90, P95, P99)."""
        # 100 Orders mit Latenzen von 100 bis 10000 ms
        measures = [
            ExecutionLatencyMeasures(
                order_id=f"ORDER_{i}",
                symbol="BTCEUR",
                trigger_delay_ms=100.0 + i * 100,
            )
            for i in range(100)
        ]

        summary = summarize_latency(measures)

        # P90: 90. Order = 9000 + 100 = 9100 ms
        # P95: 95. Order = 9500 + 100 = 9600 ms
        # P99: 99. Order = 9900 + 100 = 10000 ms
        assert summary.p90_trigger_delay_ms == pytest.approx(9100.0, rel=0.05)
        assert summary.p95_trigger_delay_ms == pytest.approx(9600.0, rel=0.05)
        assert summary.p99_trigger_delay_ms == pytest.approx(10000.0, rel=0.05)
