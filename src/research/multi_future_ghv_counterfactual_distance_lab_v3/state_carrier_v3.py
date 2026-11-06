from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from trading.market_state.distinct_market_observation_acceptor_v1 import ObservationAcceptanceStateV1
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DirectionalConfirmationSideStateCarrierV1,
)
from trading.master_v2.double_play_composition_matrix_v1 import CompositionDirectionState
from trading.master_v2.double_play_state import RuntimeScopeState, SideState
from trading.master_v2.canonical_scope_initialization_v1 import CanonicalScopeSnapshotV1


@dataclass
class FlightLaneStateRootV3:
    """Isolated state root per flight × model lane."""

    side_state: SideState = SideState.LONG_ARMED
    existing_scope: Optional[CanonicalScopeSnapshotV1] = None
    runtime_scope_state: Optional[RuntimeScopeState] = None
    directional_confirmation_progress: Optional[DirectionalConfirmationSideStateCarrierV1] = None
    c1_acceptance_state: Optional[ObservationAcceptanceStateV1] = None
    scope_confirmation_state: Optional[ScopeConfirmationStateV1] = None
    scope_cooldown_state: Optional[ScopeCooldownStateV1] = None
    previous_mark: Optional[float] = None
    previous_composition_direction: CompositionDirectionState = CompositionDirectionState.NEUTRAL
    last_evaluated_trading_epoch: int = 0
    confirmation_session_id: str = ""
    confirmation_venue: str = "okx_eea"
    confirmation_instrument: Optional[InstrumentObservationKeyV1] = None
    c1_event_time_base: float = 1_700_000_000.0


@dataclass
class FlightLaneStateStoreV3:
    roots: dict[str, FlightLaneStateRootV3] = field(default_factory=dict)

    def root_for_lane(self, lane_id: str) -> FlightLaneStateRootV3:
        if lane_id not in self.roots:
            self.roots[lane_id] = FlightLaneStateRootV3()
        return self.roots[lane_id]
