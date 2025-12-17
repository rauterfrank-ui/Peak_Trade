"""
Execution Latency Tracker – Technische Execution-Metriken (v1)

Dieses Modul misst die technische Ausführungslatenz von Orders:
  - Trigger-Delay: Signal → Order-Sent
  - Send-to-Ack: Order-Sent → Exchange-Ack
  - Send-to-Fill: Order-Sent → First/Last Fill
  - Total-Delay: Signal → Last Fill
  - Slippage: Expected Price vs. Avg Fill Price

Alle Metriken sind rein offline / paper / drill – keine Live-Order-Execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class ExecutionLatencyTimestamps:
    """Rohe Timestamps für eine Order.

    Attributes
    ----------
    session_id : str
        Session-Identifikator
    run_id : Optional[str]
        Run-Identifikator (für Backtests / Paper-Sessions)
    order_id : str
        Eindeutige Order-ID
    signal_id : Optional[int]
        Verknüpfung zu Signal (falls vorhanden)
    symbol : str
        Trading-Symbol
    side : str
        Order-Seite ("BUY" / "SELL")
    qty : float
        Order-Menge
    signal_timestamp : Optional[pd.Timestamp]
        Zeitstempel des ursprünglichen Signals
    order_sent_timestamp : pd.Timestamp
        Zeitstempel: Order wurde gesendet
    exchange_ack_timestamp : Optional[pd.Timestamp]
        Zeitstempel: Exchange hat Order bestätigt
    first_fill_timestamp : Optional[pd.Timestamp]
        Zeitstempel: Erste Fill
    last_fill_timestamp : Optional[pd.Timestamp]
        Zeitstempel: Letzte Fill
    reference_price : Optional[float]
        Erwarteter Preis (z.B. Signal-Preis)
    avg_fill_price : Optional[float]
        Durchschnittlicher Fill-Preis
    """
    session_id: str
    order_id: str
    symbol: str
    side: str
    qty: float
    order_sent_timestamp: pd.Timestamp
    run_id: str | None = None
    signal_id: int | None = None
    signal_timestamp: pd.Timestamp | None = None
    exchange_ack_timestamp: pd.Timestamp | None = None
    first_fill_timestamp: pd.Timestamp | None = None
    last_fill_timestamp: pd.Timestamp | None = None
    reference_price: float | None = None
    avg_fill_price: float | None = None


@dataclass
class ExecutionLatencyMeasures:
    """Berechnete Latenz-Metriken für eine Order.

    Attributes
    ----------
    order_id : str
        Eindeutige Order-ID
    symbol : str
        Trading-Symbol
    trigger_delay_ms : Optional[float]
        Signal → Order-Sent (falls Signal-Timestamp vorhanden)
    send_to_ack_ms : Optional[float]
        Order-Sent → Exchange-Ack
    send_to_first_fill_ms : Optional[float]
        Order-Sent → First Fill
    send_to_last_fill_ms : Optional[float]
        Order-Sent → Last Fill
    total_delay_ms : Optional[float]
        Signal → Last Fill (volle Verzögerung)
    slippage : Optional[float]
        (Avg Fill Price - Reference Price) * Direction
        Positiv = ungünstiger Fill, Negativ = besserer Fill
    """
    order_id: str
    symbol: str
    trigger_delay_ms: float | None = None
    send_to_ack_ms: float | None = None
    send_to_first_fill_ms: float | None = None
    send_to_last_fill_ms: float | None = None
    total_delay_ms: float | None = None
    slippage: float | None = None


@dataclass
class ExecutionLatencySummary:
    """Aggregierte Execution-Latenz-Statistiken über mehrere Orders.

    Attributes
    ----------
    count_orders : int
        Anzahl Orders
    mean_trigger_delay_ms : Optional[float]
        Durchschnittliche Trigger-Delay
    median_trigger_delay_ms : Optional[float]
        Median Trigger-Delay
    p90_trigger_delay_ms : Optional[float]
        90. Perzentil Trigger-Delay
    p95_trigger_delay_ms : Optional[float]
        95. Perzentil Trigger-Delay
    p99_trigger_delay_ms : Optional[float]
        99. Perzentil Trigger-Delay
    mean_send_to_ack_ms : Optional[float]
        Durchschnittliche Send-to-Ack Latenz
    median_send_to_ack_ms : Optional[float]
        Median Send-to-Ack Latenz
    mean_send_to_first_fill_ms : Optional[float]
        Durchschnittliche Send-to-First-Fill Latenz
    median_send_to_first_fill_ms : Optional[float]
        Median Send-to-First-Fill Latenz
    p90_send_to_first_fill_ms : Optional[float]
        90. Perzentil Send-to-First-Fill
    p95_send_to_first_fill_ms : Optional[float]
        95. Perzentil Send-to-First-Fill
    p99_send_to_first_fill_ms : Optional[float]
        99. Perzentil Send-to-First-Fill
    mean_send_to_last_fill_ms : Optional[float]
        Durchschnittliche Send-to-Last-Fill Latenz
    median_send_to_last_fill_ms : Optional[float]
        Median Send-to-Last-Fill Latenz
    mean_total_delay_ms : Optional[float]
        Durchschnittliche Total-Delay (Signal → Last Fill)
    median_total_delay_ms : Optional[float]
        Median Total-Delay
    p90_total_delay_ms : Optional[float]
        90. Perzentil Total-Delay
    p95_total_delay_ms : Optional[float]
        95. Perzentil Total-Delay
    p99_total_delay_ms : Optional[float]
        99. Perzentil Total-Delay
    mean_slippage : Optional[float]
        Durchschnittlicher Slippage
    median_slippage : Optional[float]
        Median Slippage
    """
    count_orders: int = 0
    mean_trigger_delay_ms: float | None = None
    median_trigger_delay_ms: float | None = None
    p90_trigger_delay_ms: float | None = None
    p95_trigger_delay_ms: float | None = None
    p99_trigger_delay_ms: float | None = None
    mean_send_to_ack_ms: float | None = None
    median_send_to_ack_ms: float | None = None
    mean_send_to_first_fill_ms: float | None = None
    median_send_to_first_fill_ms: float | None = None
    p90_send_to_first_fill_ms: float | None = None
    p95_send_to_first_fill_ms: float | None = None
    p99_send_to_first_fill_ms: float | None = None
    mean_send_to_last_fill_ms: float | None = None
    median_send_to_last_fill_ms: float | None = None
    mean_total_delay_ms: float | None = None
    median_total_delay_ms: float | None = None
    p90_total_delay_ms: float | None = None
    p95_total_delay_ms: float | None = None
    p99_total_delay_ms: float | None = None
    mean_slippage: float | None = None
    median_slippage: float | None = None


def compute_latency_measures(
    timestamps: ExecutionLatencyTimestamps
) -> ExecutionLatencyMeasures:
    """Berechnet Latenz-Metriken aus rohen Timestamps.

    Parameters
    ----------
    timestamps : ExecutionLatencyTimestamps
        Rohe Timestamp-Daten

    Returns
    -------
    ExecutionLatencyMeasures
        Berechnete Latenz-Metriken

    Examples
    --------
    >>> ts = ExecutionLatencyTimestamps(
    ...     session_id="TEST",
    ...     order_id="ORDER_1",
    ...     symbol="BTCEUR",
    ...     side="BUY",
    ...     qty=0.1,
    ...     signal_timestamp=pd.Timestamp("2025-01-01 10:00:00"),
    ...     order_sent_timestamp=pd.Timestamp("2025-01-01 10:00:00.500"),
    ...     first_fill_timestamp=pd.Timestamp("2025-01-01 10:00:00.750"),
    ...     last_fill_timestamp=pd.Timestamp("2025-01-01 10:00:01.000"),
    ... )
    >>> measures = compute_latency_measures(ts)
    >>> measures.trigger_delay_ms
    500.0
    >>> measures.send_to_first_fill_ms
    250.0
    """
    trigger_delay_ms: float | None = None
    if timestamps.signal_timestamp is not None:
        delta = timestamps.order_sent_timestamp - timestamps.signal_timestamp
        trigger_delay_ms = delta.total_seconds() * 1000.0

    send_to_ack_ms: float | None = None
    if timestamps.exchange_ack_timestamp is not None:
        delta = timestamps.exchange_ack_timestamp - timestamps.order_sent_timestamp
        send_to_ack_ms = delta.total_seconds() * 1000.0

    send_to_first_fill_ms: float | None = None
    if timestamps.first_fill_timestamp is not None:
        delta = timestamps.first_fill_timestamp - timestamps.order_sent_timestamp
        send_to_first_fill_ms = delta.total_seconds() * 1000.0

    send_to_last_fill_ms: float | None = None
    if timestamps.last_fill_timestamp is not None:
        delta = timestamps.last_fill_timestamp - timestamps.order_sent_timestamp
        send_to_last_fill_ms = delta.total_seconds() * 1000.0

    total_delay_ms: float | None = None
    if (timestamps.signal_timestamp is not None and
        timestamps.last_fill_timestamp is not None):
        delta = timestamps.last_fill_timestamp - timestamps.signal_timestamp
        total_delay_ms = delta.total_seconds() * 1000.0

    slippage: float | None = None
    if (timestamps.reference_price is not None and
        timestamps.avg_fill_price is not None):
        # Slippage: Positiv = ungünstiger Fill
        direction = 1.0 if timestamps.side.upper() == "BUY" else -1.0
        slippage = (timestamps.avg_fill_price - timestamps.reference_price) * direction

    return ExecutionLatencyMeasures(
        order_id=timestamps.order_id,
        symbol=timestamps.symbol,
        trigger_delay_ms=trigger_delay_ms,
        send_to_ack_ms=send_to_ack_ms,
        send_to_first_fill_ms=send_to_first_fill_ms,
        send_to_last_fill_ms=send_to_last_fill_ms,
        total_delay_ms=total_delay_ms,
        slippage=slippage,
    )


def summarize_latency(
    measures: list[ExecutionLatencyMeasures]
) -> ExecutionLatencySummary:
    """Aggregiert Latenz-Metriken über mehrere Orders.

    Parameters
    ----------
    measures : List[ExecutionLatencyMeasures]
        Liste von Latenz-Metriken

    Returns
    -------
    ExecutionLatencySummary
        Aggregierte Statistiken

    Examples
    --------
    >>> measures = [...]  # Liste von ExecutionLatencyMeasures
    >>> summary = summarize_latency(measures)
    >>> summary.count_orders
    50
    >>> summary.mean_send_to_first_fill_ms
    123.4
    """
    if not measures:
        return ExecutionLatencySummary()

    def _safe_stats(values: list[float]) -> dict[str, float | None]:
        """Helper: Berechnet Stats nur wenn Werte vorhanden."""
        if not values:
            return {
                "mean": None,
                "median": None,
                "p90": None,
                "p95": None,
                "p99": None,
            }
        arr = np.array(values)
        return {
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "p90": float(np.percentile(arr, 90)),
            "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99)),
        }

    # Trigger-Delay
    trigger_delays = [m.trigger_delay_ms for m in measures if m.trigger_delay_ms is not None]
    trigger_stats = _safe_stats(trigger_delays)

    # Send-to-Ack
    send_to_ack = [m.send_to_ack_ms for m in measures if m.send_to_ack_ms is not None]
    ack_stats = {"mean": None, "median": None}
    if send_to_ack:
        arr = np.array(send_to_ack)
        ack_stats = {
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
        }

    # Send-to-First-Fill
    send_to_first = [m.send_to_first_fill_ms for m in measures if m.send_to_first_fill_ms is not None]
    first_fill_stats = _safe_stats(send_to_first)

    # Send-to-Last-Fill
    send_to_last = [m.send_to_last_fill_ms for m in measures if m.send_to_last_fill_ms is not None]
    last_fill_stats = {"mean": None, "median": None}
    if send_to_last:
        arr = np.array(send_to_last)
        last_fill_stats = {
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
        }

    # Total-Delay
    total_delays = [m.total_delay_ms for m in measures if m.total_delay_ms is not None]
    total_stats = _safe_stats(total_delays)

    # Slippage
    slippages = [m.slippage for m in measures if m.slippage is not None]
    slippage_stats = {"mean": None, "median": None}
    if slippages:
        arr = np.array(slippages)
        slippage_stats = {
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
        }

    return ExecutionLatencySummary(
        count_orders=len(measures),
        mean_trigger_delay_ms=trigger_stats["mean"],
        median_trigger_delay_ms=trigger_stats["median"],
        p90_trigger_delay_ms=trigger_stats["p90"],
        p95_trigger_delay_ms=trigger_stats["p95"],
        p99_trigger_delay_ms=trigger_stats["p99"],
        mean_send_to_ack_ms=ack_stats["mean"],
        median_send_to_ack_ms=ack_stats["median"],
        mean_send_to_first_fill_ms=first_fill_stats["mean"],
        median_send_to_first_fill_ms=first_fill_stats["median"],
        p90_send_to_first_fill_ms=first_fill_stats["p90"],
        p95_send_to_first_fill_ms=first_fill_stats["p95"],
        p99_send_to_first_fill_ms=first_fill_stats["p99"],
        mean_send_to_last_fill_ms=last_fill_stats["mean"],
        median_send_to_last_fill_ms=last_fill_stats["median"],
        mean_total_delay_ms=total_stats["mean"],
        median_total_delay_ms=total_stats["median"],
        p90_total_delay_ms=total_stats["p90"],
        p95_total_delay_ms=total_stats["p95"],
        p99_total_delay_ms=total_stats["p99"],
        mean_slippage=slippage_stats["mean"],
        median_slippage=slippage_stats["median"],
    )


def latency_measures_to_df(
    measures: list[ExecutionLatencyMeasures]
) -> pd.DataFrame:
    """Konvertiert Latenz-Metriken in ein pandas DataFrame.

    Parameters
    ----------
    measures : List[ExecutionLatencyMeasures]
        Liste von Latenz-Metriken

    Returns
    -------
    pd.DataFrame
        DataFrame mit allen Measure-Feldern
    """
    if not measures:
        return pd.DataFrame(columns=[
            "order_id", "symbol", "trigger_delay_ms",
            "send_to_ack_ms", "send_to_first_fill_ms",
            "send_to_last_fill_ms", "total_delay_ms", "slippage"
        ])

    data = []
    for m in measures:
        data.append({
            "order_id": m.order_id,
            "symbol": m.symbol,
            "trigger_delay_ms": m.trigger_delay_ms,
            "send_to_ack_ms": m.send_to_ack_ms,
            "send_to_first_fill_ms": m.send_to_first_fill_ms,
            "send_to_last_fill_ms": m.send_to_last_fill_ms,
            "total_delay_ms": m.total_delay_ms,
            "slippage": m.slippage,
        })

    return pd.DataFrame(data)


def latency_summary_to_dict(
    summary: ExecutionLatencySummary
) -> dict[str, Any]:
    """Konvertiert ExecutionLatencySummary in ein Dictionary (für JSON/HTML).

    Parameters
    ----------
    summary : ExecutionLatencySummary
        Summary-Objekt

    Returns
    -------
    Dict[str, Any]
        Dictionary mit allen Summary-Feldern
    """
    return {
        "count_orders": summary.count_orders,
        "mean_trigger_delay_ms": summary.mean_trigger_delay_ms,
        "median_trigger_delay_ms": summary.median_trigger_delay_ms,
        "p90_trigger_delay_ms": summary.p90_trigger_delay_ms,
        "p95_trigger_delay_ms": summary.p95_trigger_delay_ms,
        "p99_trigger_delay_ms": summary.p99_trigger_delay_ms,
        "mean_send_to_ack_ms": summary.mean_send_to_ack_ms,
        "median_send_to_ack_ms": summary.median_send_to_ack_ms,
        "mean_send_to_first_fill_ms": summary.mean_send_to_first_fill_ms,
        "median_send_to_first_fill_ms": summary.median_send_to_first_fill_ms,
        "p90_send_to_first_fill_ms": summary.p90_send_to_first_fill_ms,
        "p95_send_to_first_fill_ms": summary.p95_send_to_first_fill_ms,
        "p99_send_to_first_fill_ms": summary.p99_send_to_first_fill_ms,
        "mean_send_to_last_fill_ms": summary.mean_send_to_last_fill_ms,
        "median_send_to_last_fill_ms": summary.median_send_to_last_fill_ms,
        "mean_total_delay_ms": summary.mean_total_delay_ms,
        "median_total_delay_ms": summary.median_total_delay_ms,
        "p90_total_delay_ms": summary.p90_total_delay_ms,
        "p95_total_delay_ms": summary.p95_total_delay_ms,
        "p99_total_delay_ms": summary.p99_total_delay_ms,
        "mean_slippage": summary.mean_slippage,
        "median_slippage": summary.median_slippage,
    }


def create_latency_timestamps_from_trades_and_signals(
    trades_df: pd.DataFrame,
    signals_df: pd.DataFrame | None = None,
    session_id: str = "default",
) -> list[ExecutionLatencyTimestamps]:
    """Convenience-Funktion: Erstellt LatencyTimestamps aus Trades & Signals DataFrames.

    Diese Funktion ist besonders nützlich für Offline/Paper-Trade-Sessions,
    wo keine echten Exchange-Acks existieren.

    Parameters
    ----------
    trades_df : pd.DataFrame
        Trades DataFrame mit Spalten:
        - timestamp (datetime): Trade-Zeitstempel
        - price (float): Fill-Preis
        - qty (float): Menge (signed)
        - optional: symbol, order_id
    signals_df : Optional[pd.DataFrame]
        Signals DataFrame mit Spalten:
        - signal_id (int): Signal-ID
        - timestamp (datetime): Signal-Zeitstempel
        - optional: symbol, recommended_action
    session_id : str
        Session-Identifikator

    Returns
    -------
    List[ExecutionLatencyTimestamps]
        Liste von Timestamp-Objekten (vereinfacht für Offline-Drill)

    Notes
    -----
    - Für Offline/Paper: Wir setzen order_sent_timestamp ≈ trade_timestamp
    - exchange_ack_timestamp bleibt None (kein echter Exchange)
    - first_fill_timestamp = last_fill_timestamp (vereinfacht)
    """
    if trades_df.empty:
        return []

    trades = trades_df.copy()
    trades["timestamp"] = pd.to_datetime(trades["timestamp"])

    # Sortiere nach timestamp für korrekte Gruppierung
    trades = trades.sort_values("timestamp")

    # Optional: Signals mergen (falls vorhanden)
    signal_map = {}
    if signals_df is not None and not signals_df.empty:
        signals = signals_df.copy()
        signals["timestamp"] = pd.to_datetime(signals["timestamp"])
        for _, sig in signals.iterrows():
            sig_id = sig.get("signal_id")
            if sig_id is not None:
                signal_map[sig_id] = sig

    timestamps_list: list[ExecutionLatencyTimestamps] = []

    for idx, trade in trades.iterrows():
        # Order-ID generieren (falls nicht vorhanden)
        order_id = trade.get("order_id")
        if pd.isna(order_id):
            order_id = f"ORDER_{idx}"
        else:
            order_id = str(order_id)

        # Symbol
        symbol = trade.get("symbol")
        if pd.isna(symbol):
            symbol = "UNKNOWN"
        else:
            symbol = str(symbol)

        # Side & Qty
        qty = float(trade["qty"])
        side = "BUY" if qty > 0 else "SELL"

        # Timestamps (vereinfacht für Offline)
        trade_ts = pd.to_datetime(trade["timestamp"])
        order_sent_ts = trade_ts  # Offline: Order-Sent ≈ Fill-Time

        # Signal-Timestamp (falls Signal vorhanden)
        signal_id = trade.get("signal_id")
        signal_ts = None
        reference_price = None

        if signal_id is not None and signal_id in signal_map:
            sig = signal_map[signal_id]
            signal_ts = pd.to_datetime(sig["timestamp"])
            # Reference-Price = Signal-Price (falls vorhanden, sonst Trade-Price)
            reference_price = trade.get("price")

        # Fill-Price
        avg_fill_price = float(trade["price"])

        timestamps_list.append(
            ExecutionLatencyTimestamps(
                session_id=session_id,
                order_id=order_id,
                symbol=symbol,
                side=side,
                qty=abs(qty),
                signal_timestamp=signal_ts,
                order_sent_timestamp=order_sent_ts,
                exchange_ack_timestamp=None,  # Offline: Kein Exchange-Ack
                first_fill_timestamp=trade_ts,
                last_fill_timestamp=trade_ts,
                reference_price=reference_price,
                avg_fill_price=avg_fill_price,
                signal_id=int(signal_id) if signal_id is not None else None,
            )
        )

    return timestamps_list
