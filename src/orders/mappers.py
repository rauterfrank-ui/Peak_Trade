# src/orders/mappers.py
"""
Peak_Trade: Mapping-Helpers fuer Order-Strukturen
=================================================

Stellt Funktionen bereit, um bestehende Order-Formate
(LiveOrderRequest, CSV-Zeilen) in das neue OrderRequest-Format
zu konvertieren.

Unterstuetzte Quellen:
- LiveOrderRequest (aus src/live/orders.py)
- CSV-Zeilen (aus Orders-CSV, erzeugt von preview_live_orders.py)
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional, Sequence

from .base import OrderRequest, OrderSide, OrderType


def _normalize_side(side: str) -> OrderSide:
    """
    Normalisiert die Order-Seite auf lowercase.

    Args:
        side: Order-Seite (z.B. "BUY", "SELL", "buy", "sell")

    Returns:
        Normalisierte Seite ("buy" oder "sell")

    Raises:
        ValueError: Bei unbekannter Seite
    """
    s = side.strip().lower()
    if s in ("buy", "long"):
        return "buy"
    if s in ("sell", "short"):
        return "sell"
    raise ValueError(f"Unbekannte Order-Seite: {side!r}")


def _normalize_order_type(order_type: str) -> OrderType:
    """
    Normalisiert den Order-Typ auf lowercase.

    Args:
        order_type: Order-Typ (z.B. "MARKET", "LIMIT", "market", "limit")

    Returns:
        Normalisierter Typ ("market" oder "limit")

    Raises:
        ValueError: Bei unbekanntem Typ
    """
    t = order_type.strip().lower()
    if t in ("market", "mkt"):
        return "market"
    if t in ("limit", "lmt"):
        return "limit"
    raise ValueError(f"Unbekannter Order-Typ: {order_type!r}")


def from_live_order_request(live_req: Any) -> OrderRequest:
    """
    Konvertiert eine LiveOrderRequest in eine OrderRequest.

    Args:
        live_req: LiveOrderRequest-Objekt (aus src/live/orders.py)
                  Erwartet Attribute: symbol, side, quantity, order_type,
                  client_order_id, extra, strategy_key, run_name, signal_as_of, comment

    Returns:
        OrderRequest-Objekt

    Raises:
        ValueError: Bei fehlenden/ungueltigen Attributen
    """
    # Symbol extrahieren
    symbol = getattr(live_req, "symbol", None)
    if not symbol:
        raise ValueError("LiveOrderRequest hat kein 'symbol'-Attribut")

    # Side extrahieren und normalisieren
    side_raw = getattr(live_req, "side", None)
    if not side_raw:
        raise ValueError("LiveOrderRequest hat kein 'side'-Attribut")
    side = _normalize_side(str(side_raw))

    # Order-Typ extrahieren und normalisieren
    order_type_raw = getattr(live_req, "order_type", "MARKET")
    order_type = _normalize_order_type(str(order_type_raw))

    # Quantity bestimmen
    quantity = getattr(live_req, "quantity", None)
    notional = getattr(live_req, "notional", None)
    extra = getattr(live_req, "extra", None) or {}

    # Wenn quantity fehlt aber notional und current_price vorhanden sind
    if quantity is None and notional is not None:
        current_price = extra.get("current_price") or extra.get("last_price")
        if current_price and float(current_price) > 0:
            quantity = float(notional) / float(current_price)

    if quantity is None or float(quantity) <= 0:
        raise ValueError(
            f"Kann quantity nicht bestimmen fuer Symbol {symbol}: "
            f"quantity={quantity}, notional={notional}"
        )

    quantity = float(quantity)

    # Client-ID
    client_id = getattr(live_req, "client_order_id", None)
    if not client_id:
        client_id = f"order_{uuid.uuid4().hex[:8]}"

    # Limit-Preis (falls vorhanden)
    limit_price: Optional[float] = None
    if order_type == "limit":
        limit_price = extra.get("limit_price")
        if limit_price is not None:
            limit_price = float(limit_price)

    # Metadata zusammenstellen
    metadata: Dict[str, Any] = {}
    if getattr(live_req, "strategy_key", None):
        metadata["strategy_key"] = str(live_req.strategy_key)
    if getattr(live_req, "run_name", None):
        metadata["run_name"] = str(live_req.run_name)
    if getattr(live_req, "signal_as_of", None):
        metadata["signal_as_of"] = str(live_req.signal_as_of)
    if getattr(live_req, "comment", None):
        metadata["comment"] = str(live_req.comment)
    if notional is not None:
        metadata["notional"] = float(notional)
    if extra.get("current_price"):
        metadata["current_price"] = float(extra["current_price"])
    if extra.get("original_direction"):
        metadata["original_direction"] = float(extra["original_direction"])

    return OrderRequest(
        symbol=str(symbol),
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        client_id=client_id,
        metadata=metadata,
    )


def from_orders_csv_row(row: Dict[str, Any]) -> OrderRequest:
    """
    Konvertiert eine CSV-Zeile (Dict) in eine OrderRequest.

    Erwartet die Spalten aus save_orders_to_csv():
    - client_order_id, symbol, side, order_type, quantity, notional,
      time_in_force, strategy_key, run_name, signal_as_of, comment, extra_json

    Args:
        row: Dictionary mit CSV-Spaltenwerten

    Returns:
        OrderRequest-Objekt

    Raises:
        ValueError: Bei fehlenden/ungueltigen Werten
    """
    # Symbol extrahieren
    symbol = row.get("symbol")
    if not symbol:
        raise ValueError("CSV-Zeile hat kein 'symbol'-Feld")
    symbol = str(symbol)

    # Side extrahieren und normalisieren
    side_raw = row.get("side")
    if not side_raw:
        raise ValueError("CSV-Zeile hat kein 'side'-Feld")
    side = _normalize_side(str(side_raw))

    # Order-Typ extrahieren und normalisieren
    order_type_raw = row.get("order_type", "MARKET")
    order_type = _normalize_order_type(str(order_type_raw))

    # Extra-JSON parsen
    extra: Dict[str, Any] = {}
    extra_json = row.get("extra_json")
    if extra_json and str(extra_json).strip():
        try:
            parsed = json.loads(str(extra_json))
            if isinstance(parsed, dict):
                extra = parsed
        except json.JSONDecodeError:
            pass

    # Quantity bestimmen
    quantity = row.get("quantity")
    notional = row.get("notional")

    # NaN-Check fuer pandas
    import math
    if quantity is not None:
        try:
            if math.isnan(float(quantity)):
                quantity = None
        except (ValueError, TypeError):
            pass

    if notional is not None:
        try:
            if math.isnan(float(notional)):
                notional = None
        except (ValueError, TypeError):
            pass

    # Wenn quantity fehlt aber notional und current_price vorhanden sind
    if quantity is None and notional is not None:
        current_price = extra.get("current_price") or extra.get("last_price")
        if current_price and float(current_price) > 0:
            quantity = float(notional) / float(current_price)

    if quantity is None or float(quantity) <= 0:
        raise ValueError(
            f"Kann quantity nicht bestimmen fuer Symbol {symbol}: "
            f"quantity={quantity}, notional={notional}"
        )

    quantity = float(quantity)

    # Client-ID
    client_id = row.get("client_order_id")
    if not client_id or str(client_id) == "nan":
        client_id = f"order_{uuid.uuid4().hex[:8]}"
    else:
        client_id = str(client_id)

    # Limit-Preis (falls vorhanden)
    limit_price: Optional[float] = None
    if order_type == "limit":
        limit_price = extra.get("limit_price")
        if limit_price is not None:
            limit_price = float(limit_price)

    # Metadata zusammenstellen
    metadata: Dict[str, Any] = {}

    strategy_key = row.get("strategy_key")
    if strategy_key and str(strategy_key) != "nan":
        metadata["strategy_key"] = str(strategy_key)

    run_name = row.get("run_name")
    if run_name and str(run_name) != "nan":
        metadata["run_name"] = str(run_name)

    signal_as_of = row.get("signal_as_of")
    if signal_as_of and str(signal_as_of) != "nan":
        metadata["signal_as_of"] = str(signal_as_of)

    comment = row.get("comment")
    if comment and str(comment) != "nan":
        metadata["comment"] = str(comment)

    if notional is not None:
        metadata["notional"] = float(notional)

    if extra.get("current_price"):
        metadata["current_price"] = float(extra["current_price"])

    if extra.get("original_direction"):
        metadata["original_direction"] = float(extra["original_direction"])

    return OrderRequest(
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        client_id=client_id,
        metadata=metadata,
    )


def to_order_requests(
    live_orders: Sequence[Any],
) -> List[OrderRequest]:
    """
    Konvertiert eine Liste von LiveOrderRequest-Objekten in OrderRequests.

    Args:
        live_orders: Liste von LiveOrderRequest-Objekten

    Returns:
        Liste von OrderRequest-Objekten
    """
    return [from_live_order_request(req) for req in live_orders]
