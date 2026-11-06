from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LabContractV2:
    tick_size: Decimal
    price_precision: int


def contract_for_p0_v2(p0: float) -> LabContractV2:
    mark = float(p0)
    if mark < 1:
        return LabContractV2(tick_size=Decimal("0.0001"), price_precision=4)
    if mark < 10:
        return LabContractV2(tick_size=Decimal("0.001"), price_precision=3)
    if mark < 1000:
        return LabContractV2(tick_size=Decimal("0.01"), price_precision=2)
    if mark < 10000:
        return LabContractV2(tick_size=Decimal("0.1"), price_precision=1)
    return LabContractV2(tick_size=Decimal("1"), price_precision=0)
