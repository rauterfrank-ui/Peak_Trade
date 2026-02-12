from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class BalanceSnapshot:
    epoch: int
    balances: Dict[str, float]  # asset -> amount


@dataclass(frozen=True)
class PositionSnapshot:
    epoch: int
    positions: Dict[str, float]  # symbol -> base units


@dataclass(frozen=True)
class OrderSnapshot:
    epoch: int
    open_orders: List[dict]  # normalized dict schema (caller-defined)


@dataclass(frozen=True)
class FillSnapshot:
    epoch: int
    fills: List[dict]  # normalized dict schema (caller-defined)


@dataclass(frozen=True)
class DriftReport:
    ok: bool
    drifts: List[str]
