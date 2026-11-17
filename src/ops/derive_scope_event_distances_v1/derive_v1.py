"""Pure binding of the full Dynamic Scope to Layer-C distances.

Productive runtime must not import this module directly. The authorized
productive adapter is
``trading.master_v2.layer_c_scope_event_distance_binding_v1`` (Owner-GO
Layer-C cutover). No config mutation, no venue/clock/IO, no Dual Envelope
substitution.
"""

from __future__ import annotations

import math

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
    """Bind the effective hysteresis band without rescaling, else fail closed.

    Valid: ok=true and the three derived distances only.
    Invalid: ok=false, no usable distances, failure_reason=INVALID_INPUT.
    Does not raise for invalid-band domain cases. Does not coerce int/Decimal/str.
    """

    if not _current_hysteresis_band_is_valid(current_hysteresis_band):
        return invalid_result_v1()

    # The V1 adverse distance field supplies protection geometry. Its
    # coincident boundary does not represent a separate Scope exit event.
    return ok_result_v1(
        up_distance=current_hysteresis_band,
        adverse_exit_distance=current_hysteresis_band,
        reversal_distance=current_hysteresis_band,
    )
