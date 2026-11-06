from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Tuple

from research.multi_future_ghv_counterfactual_distance_lab_v1.constants_v1 import (
    REAL_CONTRACT_PROFILE_IDS,
)


@dataclass(frozen=True)
class ContractProfileV1:
    profile_id: str
    kind: str
    price_scale_hint: float
    tick_size: Decimal
    lot_size: Decimal
    contract_value: Decimal
    min_size: Decimal
    min_notional: Decimal
    price_precision: int
    size_precision: int
    leverage_context: Decimal
    instrument_type: str
    contract_type: str


def _tick_for_price(p0: float) -> Decimal:
    if p0 < 1:
        return Decimal("0.0001")
    if p0 < 10:
        return Decimal("0.001")
    if p0 < 1000:
        return Decimal("0.01")
    if p0 < 10000:
        return Decimal("0.1")
    return Decimal("1")


def synthetic_contract_profile_v1(*, future_profile_id: str, p0: float) -> ContractProfileV1:
    tick = _tick_for_price(p0)
    return ContractProfileV1(
        profile_id=f"SYNTH_{future_profile_id}_P0_{p0}",
        kind="SYNTHETIC_FUTURE_ARCHETYPE",
        price_scale_hint=float(p0),
        tick_size=tick,
        lot_size=Decimal("1"),
        contract_value=Decimal("1"),
        min_size=Decimal("1"),
        min_notional=Decimal("5"),
        price_precision=max(0, -tick.as_tuple().exponent),
        size_precision=0,
        leverage_context=Decimal("3"),
        instrument_type="SWAP",
        contract_type="LINEAR_PERP",
    )


REAL_CONTRACT_PROFILES: Mapping[str, ContractProfileV1] = {
    "SUB_DOLLAR_PERP_PROFILE": ContractProfileV1(
        profile_id="SUB_DOLLAR_PERP_PROFILE",
        kind="REAL_CONTRACT_PROFILE_REPLAY",
        price_scale_hint=0.35,
        tick_size=Decimal("0.0001"),
        lot_size=Decimal("1"),
        contract_value=Decimal("1"),
        min_size=Decimal("1"),
        min_notional=Decimal("5"),
        price_precision=4,
        size_precision=0,
        leverage_context=Decimal("3"),
        instrument_type="SWAP",
        contract_type="LINEAR_PERP",
    ),
    "LOW_PRICE_PERP_PROFILE": ContractProfileV1(
        profile_id="LOW_PRICE_PERP_PROFILE",
        kind="REAL_CONTRACT_PROFILE_REPLAY",
        price_scale_hint=8.5,
        tick_size=Decimal("0.001"),
        lot_size=Decimal("1"),
        contract_value=Decimal("1"),
        min_size=Decimal("1"),
        min_notional=Decimal("5"),
        price_precision=3,
        size_precision=0,
        leverage_context=Decimal("5"),
        instrument_type="SWAP",
        contract_type="LINEAR_PERP",
    ),
    "MID_PRICE_PERP_PROFILE": ContractProfileV1(
        profile_id="MID_PRICE_PERP_PROFILE",
        kind="REAL_CONTRACT_PROFILE_REPLAY",
        price_scale_hint=3500.0,
        tick_size=Decimal("0.01"),
        lot_size=Decimal("0.01"),
        contract_value=Decimal("1"),
        min_size=Decimal("0.01"),
        min_notional=Decimal("5"),
        price_precision=2,
        size_precision=2,
        leverage_context=Decimal("10"),
        instrument_type="SWAP",
        contract_type="LINEAR_PERP",
    ),
    "HIGH_PRICE_PERP_PROFILE": ContractProfileV1(
        profile_id="HIGH_PRICE_PERP_PROFILE",
        kind="REAL_CONTRACT_PROFILE_REPLAY",
        price_scale_hint=95000.0,
        tick_size=Decimal("0.1"),
        lot_size=Decimal("0.001"),
        contract_value=Decimal("1"),
        min_size=Decimal("0.001"),
        min_notional=Decimal("5"),
        price_precision=1,
        size_precision=3,
        leverage_context=Decimal("20"),
        instrument_type="SWAP",
        contract_type="LINEAR_PERP",
    ),
}


def all_real_contract_profiles() -> Tuple[ContractProfileV1, ...]:
    return tuple(REAL_CONTRACT_PROFILES[k] for k in REAL_CONTRACT_PROFILE_IDS)
