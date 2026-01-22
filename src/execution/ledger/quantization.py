from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Mapping, Optional

from .models import QuantizationPolicy


def d(value: Any) -> Decimal:
    """
    Deterministic Decimal parser.

    Contract:
    - Reject float inputs (float -> string is not stable enough for bit-identical outputs).
    - Accept Decimal, int, str.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    if isinstance(value, float):
        raise TypeError(
            "float inputs are forbidden for deterministic accounting; pass str or Decimal"
        )
    raise TypeError(f"Unsupported numeric type: {type(value)!r}")


def q(value: Decimal, quant: Decimal, *, policy: QuantizationPolicy) -> Decimal:
    return value.quantize(quant, rounding=policy.rounding)


def q_qty(value: Decimal, *, policy: QuantizationPolicy) -> Decimal:
    return q(value, policy.qty_quant, policy=policy)


def q_price(value: Decimal, *, policy: QuantizationPolicy) -> Decimal:
    return q(value, policy.price_quant, policy=policy)


def q_money(value: Decimal, *, policy: QuantizationPolicy) -> Decimal:
    return q(value, policy.money_quant, policy=policy)


def canonical_json(obj: Mapping[str, Any]) -> str:
    """
    Canonical JSON for stable hashing / golden tests.
    """
    return json.dumps(dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def parse_symbol(symbol: str) -> tuple[str, str]:
    """
    Parse base/quote from symbols like "BTC/EUR" or "BTC-USD".
    """
    if "/" in symbol:
        base, quote = symbol.split("/", 1)
        return base, quote
    if "-" in symbol:
        base, quote = symbol.split("-", 1)
        return base, quote
    raise ValueError(
        f"Unsupported symbol format (expected 'BASE/QUOTE' or 'BASE-QUOTE'): {symbol!r}"
    )
