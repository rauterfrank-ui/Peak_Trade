"""Pure unbound derive_scope_event_distances_v1.

Unbound: productive hosts/generators must not import or call this module.
No config mutation, no venue/clock/IO, no Dual Envelope substitution.
"""

from __future__ import annotations

import math

from src.ops.derive_scope_event_distances_v1.constants_v1 import (
    OQ_C2_ADVERSE_NUMERATOR,
    OQ_C2_RATIO_DENOMINATOR,
    OQ_C2_REVERSAL_NUMERATOR,
)
from src.ops.derive_scope_event_distances_v1.result_v1 import (
    DerivedScopeEventDistancesResultV1,
    invalid_result_v1,
    ok_result_v1,
)


def _current_hysteresis_band_is_valid(value: object) -> bool:
    return type(value) is float and math.isfinite(value) and value > 0.0


def derive_scope_event_distances_v1(
    current_hysteresis_band: object,
) -> DerivedScopeEventDistancesResultV1:
    """Map a valid hysteresis band to OQ-C1/OQ-C2 distances, else fail closed.

    Valid: ok=true and the three derived distances only.
    Invalid: ok=false, no usable distances, failure_reason=INVALID_INPUT.
    Does not raise for invalid-band domain cases. Does not coerce int/Decimal/str.
    """

    if not _current_hysteresis_band_is_valid(current_hysteresis_band):
        return invalid_result_v1()

    up_distance = current_hysteresis_band
    adverse_exit_distance = up_distance * (OQ_C2_ADVERSE_NUMERATOR / OQ_C2_RATIO_DENOMINATOR)
    reversal_distance = up_distance * (OQ_C2_REVERSAL_NUMERATOR / OQ_C2_RATIO_DENOMINATOR)
    return ok_result_v1(
        up_distance=up_distance,
        adverse_exit_distance=adverse_exit_distance,
        reversal_distance=reversal_distance,
    )
