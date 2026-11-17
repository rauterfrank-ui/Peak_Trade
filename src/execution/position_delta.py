"""Signed position change shared by signal execution and net futures reversal."""

from decimal import Decimal
from typing import TypeVar

PositionQuantity = TypeVar("PositionQuantity", Decimal, float)


def signed_position_delta(current: PositionQuantity, target: PositionQuantity) -> PositionQuantity:
    return target - current
