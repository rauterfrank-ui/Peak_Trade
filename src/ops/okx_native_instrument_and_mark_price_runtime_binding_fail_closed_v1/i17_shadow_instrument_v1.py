"""The exact instrument scopes of the existing I17 observation path."""

from collections.abc import Sequence
from dataclasses import dataclass

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
)


@dataclass(frozen=True)
class I17ShadowInstrumentV1:
    canonical_id: str
    native_id: str
    base: str
    lane_id: str | None = None


ETH_I17 = I17ShadowInstrumentV1(CANONICAL_INSTRUMENT_ID, CANONICAL_INSTRUMENT_ID, "ETH")
SOPH_I17 = I17ShadowInstrumentV1(
    "okx_eea:linear_dated_future:SOPH:USD:USD:soph-usd_um_xperp-310912",
    "SOPH-USD_UM_XPERP-310912",
    "SOPH",
    "LANE_5",
)


def require_i17_shadow_instrument_v1(allowlist: Sequence[str]) -> I17ShadowInstrumentV1:
    for instrument in (ETH_I17, SOPH_I17):
        if tuple(allowlist) == (instrument.native_id,):
            return instrument
    raise ValueError("I17_SHADOW_INSTRUMENT_SCOPE_MISMATCH")
