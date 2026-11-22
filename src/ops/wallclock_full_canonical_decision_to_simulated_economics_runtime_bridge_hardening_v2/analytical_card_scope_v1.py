"""Instrument-bound geometry for the analytical instrument-card consumer."""

from dataclasses import dataclass, replace

from trading.market_state.time_sample_epoch_semantics_v1 import InstrumentObservationKeyV1
from trading.master_v2.double_play_state import (
    ActiveSide,
    RuntimeScopeState,
)
from trading.master_v2.golden_geometry_engine_v1 import (
    compute_canonical_base_geometry_magnitude_from_market_context_v1,
)
from trading.master_v2.naked_mv2_dp_single_boundary_purification_v1 import (
    update_scope_internal_reference_state_v1,
)


@dataclass(frozen=True)
class AnalyticalCardGeometryV1:
    key: InstrumentObservationKeyV1
    position_side: ActiveSide
    distance: float
    input_digest: str

    @classmethod
    def from_context(cls, *, key, context, position, acceptance):
        if (
            acceptance is None
            or acceptance.observation_identity is None
            or acceptance.observation_identity.instrument_key() != key
            or acceptance.observation_identity.mark_price != context.mark_price
            or key.canonical_instrument_id != context.instrument_id
            or position is None
            or position.instrument_id != context.instrument_id
            or not key.venue_instrument_id
        ):
            raise ValueError("CARD_GEOMETRY_INSTRUMENT_MISMATCH")
        result = compute_canonical_base_geometry_magnitude_from_market_context_v1(context)
        if (
            not result.ok
            or result.output is None
            or result.output.instrument_id != key.canonical_instrument_id
        ):
            raise ValueError("CARD_GEOMETRY_UNAVAILABLE")
        qty = position.signed_quantity
        if not qty.is_finite() or position.venue_flat != (qty == 0):
            raise ValueError("CARD_GEOMETRY_POSITION_MISMATCH")
        side = ActiveSide.LONG if qty > 0 else ActiveSide.SHORT if qty < 0 else ActiveSide.NEUTRAL
        return cls(key, side, result.output.magnitude, result.output.input_digest)

    def advance(self, state: RuntimeScopeState, mark: float) -> RuntimeScopeState:
        # While flat only the current decision's base distance is available.
        # The moving reference belongs to the side of the booked position.
        if state.chop_latched:
            return state
        reference = update_scope_internal_reference_state_v1(
            mark_price=mark, side=self.position_side, st=state
        )
        return replace(
            reference,
            scope_distance_mode="gge_raw_v2",
            current_hysteresis_band=self.distance,
            current_upscope_boundary=reference.anchor_price + self.distance,
            current_downscope_boundary=reference.anchor_price - self.distance,
        )

    def verify_consumption(self, intermediate, *, mark, carried):
        if intermediate is None:
            return
        binding = intermediate.scope_event.semantic_binding
        distance = (
            self.distance
            if carried is None or not carried.chop_latched
            else carried.current_hysteresis_band
        )
        if (
            intermediate.market_context.instrument_id != self.key.canonical_instrument_id
            or intermediate.scope_event.instrument_id != self.key.canonical_instrument_id
            or binding.current_price != mark
            or intermediate.effective_scope_magnitude != distance
            or (carried is not None and binding.trailing_anchor != carried.anchor_price)
            or (
                carried is not None
                and binding.current_direction_state.value != self.position_side.value
            )
        ):
            raise ValueError("CARD_GEOMETRY_CONSUMPTION_MISMATCH")
