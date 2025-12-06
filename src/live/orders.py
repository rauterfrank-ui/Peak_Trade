# src/live/orders.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Sequence

import json
import pandas as pd


Side = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]
TimeInForce = Literal["GTC", "IOC", "FOK"]


@dataclass
class LiveOrderRequest:
    """
    Standard-Order-Request für Live-/Paper-Trading.

    Wichtig:
    - Dies ist nur ein generisches Format, keine Broker-spezifische API.
    - quantity UND/ODER notional können gesetzt sein.
    """

    client_order_id: str
    symbol: str
    side: Side

    order_type: OrderType = "MARKET"
    quantity: float | None = None
    notional: float | None = None
    time_in_force: TimeInForce = "GTC"

    strategy_key: str | None = None
    run_name: str | None = None
    signal_as_of: str | None = None
    comment: str | None = None

    extra: Dict[str, Any] | None = None


@dataclass
class LiveExecutionReport:
    """
    Generischer Execution-Report.

    In diesem Skeleton wird er vom DryRunBroker verwendet, um Rückmeldungen zu simulieren.
    """

    client_order_id: str
    status: str  # z.B. "ACKNOWLEDGED", "FILLED", "REJECTED"

    filled_quantity: float | None = None
    avg_price: float | None = None
    ts: str | None = None

    message: str | None = None
    extra: Dict[str, Any] | None = None


ORDERS_COLUMNS: Sequence[str] = [
    "client_order_id",
    "symbol",
    "side",
    "order_type",
    "quantity",
    "notional",
    "time_in_force",
    "strategy_key",
    "run_name",
    "signal_as_of",
    "comment",
    "extra_json",
]


def side_from_direction(direction: float) -> Side | None:
    """
    Hilfsfunktion: Mapping von Strategie-Signal-Richtung → Order-Seite.

    direction > 0 → BUY
    direction < 0 → SELL
    direction == 0 → None (kein Trade)
    """
    if direction > 0:
        return "BUY"
    if direction < 0:
        return "SELL"
    return None


def orders_to_dataframe(orders: Iterable[LiveOrderRequest]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for order in orders:
        d = asdict(order)
        extra = d.pop("extra", None)
        d["extra_json"] = json.dumps(extra, ensure_ascii=False) if extra is not None else None
        rows.append(d)

    if not rows:
        return pd.DataFrame(columns=list(ORDERS_COLUMNS))

    df = pd.DataFrame(rows)
    # Spaltenreihenfolge erzwingen
    for col in ORDERS_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[list(ORDERS_COLUMNS)]
    return df


def save_orders_to_csv(orders: Iterable[LiveOrderRequest], path: Path | str) -> pd.DataFrame:
    """
    Speichert eine Liste von LiveOrderRequest als CSV und gibt das DataFrame zurück.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = orders_to_dataframe(list(orders))
    df.to_csv(path, index=False)
    return df


def load_orders_csv(path: Path | str) -> List[LiveOrderRequest]:
    """
    Lädt Orders aus einer CSV, die mit save_orders_to_csv geschrieben wurde.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Orders-CSV nicht gefunden: {path}")

    df = pd.read_csv(path)
    orders: List[LiveOrderRequest] = []

    for _, row in df.iterrows():
        extra = None
        raw_extra = row.get("extra_json")
        if isinstance(raw_extra, str) and raw_extra.strip():
            try:
                extra = json.loads(raw_extra)
            except json.JSONDecodeError:
                extra = {"raw_extra_json": raw_extra}

        quantity = row.get("quantity")
        notional = row.get("notional")

        orders.append(
            LiveOrderRequest(
                client_order_id=str(row.get("client_order_id")),
                symbol=str(row.get("symbol")),
                side=str(row.get("side")),
                order_type=str(row.get("order_type") or "MARKET"),
                quantity=float(quantity) if quantity is not None and not pd.isna(quantity) else None,
                notional=float(notional) if notional is not None and not pd.isna(notional) else None,
                time_in_force=str(row.get("time_in_force") or "GTC"),
                strategy_key=str(row.get("strategy_key")) if row.get("strategy_key") is not None else None,
                run_name=str(row.get("run_name")) if row.get("run_name") is not None else None,
                signal_as_of=str(row.get("signal_as_of")) if row.get("signal_as_of") is not None else None,
                comment=str(row.get("comment")) if row.get("comment") is not None else None,
                extra=extra,
            )
        )

    return orders
