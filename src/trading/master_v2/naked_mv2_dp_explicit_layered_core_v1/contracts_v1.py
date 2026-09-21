"""Explicit contracts and isolated state carriers for L1–L10 (v1)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol, Tuple

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationAcceptanceStateV1,
    ObservationCandidateV1,
)
from trading.market_state.elementary_direction_v1 import ElementaryDirectionResultV1
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import NakedRegimeV1


class LayerReachabilityV1(str, Enum):
    REACHED = "reached"
    NOT_REACHED = "not_reached"
    FAIL_CLOSED = "fail_closed"


@dataclass(frozen=True)
class SelectedFutureStateV1:
    """L1 — caller-owned instrument binding for the naked chain."""

    instrument_id: str
    instrument_key: InstrumentObservationKeyV1


@dataclass(frozen=True)
class SelectedFutureInputV1:
    instrument_id: str
    instrument_key: InstrumentObservationKeyV1


@dataclass(frozen=True)
class SelectedFutureOutputV1:
    state: SelectedFutureStateV1


@dataclass(frozen=True)
class MarketObservationStateV1:
    """L2 — C1 acceptance state scoped to selected future."""

    selected: SelectedFutureStateV1
    acceptance_state: ObservationAcceptanceStateV1


@dataclass(frozen=True)
class MarketObservationInputV1:
    observation_state: MarketObservationStateV1
    candidate: ObservationCandidateV1


@dataclass(frozen=True)
class MarketObservationOutputV1:
    observation_state: MarketObservationStateV1
    acceptance_result: ObservationAcceptanceResultV1


@dataclass(frozen=True)
class InitialDirectionInputV1:
    acceptance_result: ObservationAcceptanceResultV1
    bound_instrument_key: InstrumentObservationKeyV1
    current_mark: float


@dataclass(frozen=True)
class InitialDirectionOutputV1:
    direction_result: ElementaryDirectionResultV1


@dataclass(frozen=True)
class InitialRegimeStateV1:
    """L4 — initial BULL/BEAR only; no neutral fallback."""

    instrument_id: str
    regime: NakedRegimeV1


@dataclass(frozen=True)
class InitialStateInitializationInputV1:
    selected: SelectedFutureStateV1
    direction: InitialDirectionOutputV1
    initialization_mark: float


@dataclass(frozen=True)
class InitialStateInitializationOutputV1:
    regime_state: InitialRegimeStateV1
    fail_closed: bool
    fail_reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class NullLineStateV1:
    """L5 — immutable initial price basis; distinct from R_t."""

    instrument_id: str
    nullline_price: float
    provenance_mark_epoch: int


@dataclass(frozen=True)
class NullLineInputV1:
    regime_state: InitialRegimeStateV1
    initialization_mark: float
    market_observation_epoch: int


@dataclass(frozen=True)
class NullLineOutputV1:
    nullline: NullLineStateV1


@dataclass(frozen=True)
class DynamicScopeGeneratorInputV1:
    nullline: NullLineStateV1
    proposed_d_t: Optional[float]


@dataclass(frozen=True)
class DynamicScopeGeneratorOutputV1:
    d_t: Optional[float]
    fail_closed: bool
    fail_reasons: Tuple[str, ...]
    generator_id: str


class DynamicScopeGeneratorV1(Protocol):
    """Replaceable L6 contract — validates/passes explicit D_t only."""

    generator_id: str

    def generate(self, inp: DynamicScopeGeneratorInputV1) -> DynamicScopeGeneratorOutputV1:
        ...


@dataclass(frozen=True)
class ScopeStateV1:
    """L7 — scope distance + nullline provenance; no switch authority."""

    instrument_id: str
    d_t: float
    nullline_price: float
    nullline_provenance_epoch: int
    generator_id: str
    valid: bool


@dataclass(frozen=True)
class ScopeStateMaterializationInputV1:
    nullline: NullLineStateV1
    generator_output: DynamicScopeGeneratorOutputV1


@dataclass(frozen=True)
class ScopeStateMaterializationOutputV1:
    scope: Optional[ScopeStateV1]
    fail_closed: bool
    fail_reasons: Tuple[str, ...]


@dataclass(frozen=True)
class RunningReferenceStateV1:
    """L8 — R_t lifecycle state; never aliases NullLine."""

    instrument_id: str
    reference_price_r_t: float


@dataclass(frozen=True)
class RunningReferenceStepInputV1:
    regime: NakedRegimeV1
    mark_price_m_t: float
    previous: RunningReferenceStateV1


@dataclass(frozen=True)
class RunningReferenceStepOutputV1:
    previous_r_t: float
    updated_r_t: float
    state: RunningReferenceStateV1


@dataclass(frozen=True)
class CounterMoveStateV1:
    """L9 — ephemeral CM identity (no persisted CM authority)."""

    instrument_id: str
    cm_t: float


@dataclass(frozen=True)
class CounterMoveInputV1:
    regime: NakedRegimeV1
    mark_price_m_t: float
    running_reference: RunningReferenceStateV1


@dataclass(frozen=True)
class CounterMoveOutputV1:
    counter_move: CounterMoveStateV1


@dataclass(frozen=True)
class BullBearSwitchInputV1:
    regime_pre: NakedRegimeV1
    cm_t: float
    d_t: float
    mark_price_m_t: float
    running_reference_post: RunningReferenceStateV1


@dataclass(frozen=True)
class BullBearSwitchOutputV1:
    regime_pre: NakedRegimeV1
    regime_post: NakedRegimeV1
    switch_condition_met: bool
    r_t_reset_performed: bool
    persisted_r_t: float


@dataclass(frozen=True)
class LayeredCorePersistedStateV1:
    selected: SelectedFutureStateV1
    observation: MarketObservationStateV1
    regime: NakedRegimeV1
    nullline: NullLineStateV1
    scope: ScopeStateV1
    running_reference: RunningReferenceStateV1
    initialized: bool


__all__ = [
    "LayerReachabilityV1",
    "SelectedFutureStateV1",
    "SelectedFutureInputV1",
    "SelectedFutureOutputV1",
    "MarketObservationStateV1",
    "MarketObservationInputV1",
    "MarketObservationOutputV1",
    "InitialDirectionInputV1",
    "InitialDirectionOutputV1",
    "InitialRegimeStateV1",
    "InitialStateInitializationInputV1",
    "InitialStateInitializationOutputV1",
    "NullLineStateV1",
    "NullLineInputV1",
    "NullLineOutputV1",
    "DynamicScopeGeneratorInputV1",
    "DynamicScopeGeneratorOutputV1",
    "DynamicScopeGeneratorV1",
    "ScopeStateV1",
    "ScopeStateMaterializationInputV1",
    "ScopeStateMaterializationOutputV1",
    "RunningReferenceStateV1",
    "RunningReferenceStepInputV1",
    "RunningReferenceStepOutputV1",
    "CounterMoveStateV1",
    "CounterMoveInputV1",
    "CounterMoveOutputV1",
    "BullBearSwitchInputV1",
    "BullBearSwitchOutputV1",
    "LayeredCorePersistedStateV1",
]
