"""Compose per-lane identity closure ingress bundle (D1–D6 contract surface)."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_POSITION_SHARED_FORBIDDEN,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.c1_fanout_v1 import (
    C1FanoutError,
    extract_lane_closes_v1,
    resolve_per_lane_c1_payloads_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    LaneOwnershipIndexV1,
    PerLaneGovernedIngressV1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.ownership_v1 import (
    LaneOwnershipError,
    assert_lane_ownership_index_v1,
    build_identities_from_composed_pairs_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
    PerLanePositionTruthError,
    resolve_all_lane_position_truths_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.reconciliation_admission_v1 import (
    ReconciliationAdmissionError,
    assert_lane_reconciliation_admitted_v1,
    build_per_lane_reconciliation_admission_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class InstrumentRuntimeIdentityClosureError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def compose_per_lane_n5_identity_closure_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    *,
    candles_payload: Mapping[str, Any] | None,
    candles_payload_by_lane: Mapping[str, Mapping[str, Any]] | None,
    occupancy_payloads: Mapping[str, Any],
    observed_portfolio: PortfolioTruthSnapshotV1 | None,
    venue_flat: bool,
    existing_position_side: ExistingPositionSide,
    last_finalized_event_ts_unix: float,
    finalized_closes: tuple[float, ...] | list[float],
    require_reconciliation_admission: bool = True,
) -> tuple[dict[str, PerLaneGovernedIngressV1], LaneOwnershipIndexV1]:
    try:
        identities = build_identities_from_composed_pairs_v1(composed_pairs)
        native_ids = {identities[l].venue_native_id for l in identities}
        if len(identities) > 1 and len(native_ids) > 1:
            if (not venue_flat) or existing_position_side != ExistingPositionSide.NONE:
                raise InstrumentRuntimeIdentityClosureError(
                    FAILURE_POSITION_SHARED_FORBIDDEN,
                    "global_position_kwarg_multi_lane",
                )
        ownership = assert_lane_ownership_index_v1(identities)
        c1_by_lane = resolve_per_lane_c1_payloads_v1(
            identities=identities,
            candles_payload=candles_payload,
            candles_payload_by_lane=candles_payload_by_lane,
        )
        multi_lane = len(identities) > 1
        positions = resolve_all_lane_position_truths_v1(
            identities=identities,
            occupancy_payloads=occupancy_payloads,
            global_venue_flat=venue_flat,
            global_existing_position_side=existing_position_side,
            multi_lane=multi_lane,
        )
    except (C1FanoutError, LaneOwnershipError, PerLanePositionTruthError) as exc:
        raise InstrumentRuntimeIdentityClosureError(exc.failure_code, exc.detail) from exc

    ingress: dict[str, PerLaneGovernedIngressV1] = {}
    for lane_id, identity in sorted(identities.items()):
        payload = c1_by_lane[lane_id]
        extracted, last_ts = extract_lane_closes_v1(payload)
        closes = extracted if extracted else tuple(finalized_closes)
        event_ts = float(last_ts if last_ts is not None else last_finalized_event_ts_unix)
        recon = build_per_lane_reconciliation_admission_v1(
            identity=identity,
            portfolio=observed_portfolio,
        )
        if require_reconciliation_admission:
            try:
                assert_lane_reconciliation_admitted_v1(recon, lane_id=lane_id)
            except ReconciliationAdmissionError as exc:
                raise InstrumentRuntimeIdentityClosureError(exc.failure_code, exc.detail) from exc
        pos = positions[lane_id]
        ingress[lane_id] = PerLaneGovernedIngressV1(
            identity=identity,
            candles_payload=payload,
            finalized_closes=closes,
            last_finalized_event_ts_unix=event_ts,
            position=pos,
            reconciliation=recon,
        )
    return ingress, ownership
