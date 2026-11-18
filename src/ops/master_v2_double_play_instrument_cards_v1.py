"""Instrument candidate contracts owned by the Master V2 Double Play universe."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
        OccupiedLaneRuntimeInstrumentIdentityV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        ProductiveCycleCanonicalPriceProvenanceV1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        IntegratedOfflineReplayInputV1,
    )

MASTER_V2_DOUBLE_PLAY_UNIVERSE = "Master V2 Double Play"


@dataclass(frozen=True)
class OfflineInstrumentCandidateCardV1:
    source_mode: str
    binding: BoundInstrumentV1
    replay_input: IntegratedOfflineReplayInputV1
    price_provenance: ProductiveCycleCanonicalPriceProvenanceV1
    market_captures: Mapping[str, Mapping[str, Any]]
    slot_identity: OccupiedLaneRuntimeInstrumentIdentityV1 | None = None
    owner_universe: str = field(default=MASTER_V2_DOUBLE_PLAY_UNIVERSE, init=False)


@dataclass(frozen=True)
class OfflineInstrumentCandidateReviewV1:
    status: str
    reasons: tuple[str, ...]
    card_digest: str | None = None
    source_mode: str | None = None
    decision_outcome: str | None = None
    decision_time: str | None = None
    market_context_digest: str | None = None
    gge_input_digest: str | None = None
    decision_digest: str | None = None
    lane_id: str | None = None
    instrument_epoch: str | None = None
    owner_universe: str = field(default=MASTER_V2_DOUBLE_PLAY_UNIVERSE, init=False)
