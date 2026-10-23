"""Per-lane position truth from PortfolioTruthSnapshotV1 (D2)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_POSITION_SHARED_FORBIDDEN,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
    PerLanePositionTruthV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
    okx_positions_payload_to_portfolio_snapshot_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.classifier_v1 import (
    classify_productive_reconciliation_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)


class PerLanePositionTruthError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _positions_payload(occupancy_payloads: Mapping[str, Any] | None) -> Any:
    if occupancy_payloads is None:
        return None
    positions = occupancy_payloads.get("POSITIONS")
    if positions is not None:
        return positions
    return None


def _nonzero(snapshot: PortfolioTruthSnapshotV1):
    return tuple(pos for pos in snapshot.positions if pos.signed_quantity != 0)


def combine_position_snapshots_v1(
    occupancy_payloads: Mapping[str, Any] | None,
    observed_portfolio: PortfolioTruthSnapshotV1 | None,
) -> PortfolioTruthSnapshotV1:
    """One snapshot. A caller boolean is not an input."""
    parsed = okx_positions_payload_to_portfolio_snapshot_v1(_positions_payload(occupancy_payloads))
    if observed_portfolio is None:
        return parsed
    if (
        observed_portfolio.missing
        or observed_portfolio.stale
        or observed_portfolio.duplicate
        or observed_portfolio.writer_conflict
    ):
        return observed_portfolio
    if parsed.missing:
        return observed_portfolio
    parsed_ids = {pos.instrument_id for pos in _nonzero(parsed)}
    observed_ids = {pos.instrument_id for pos in _nonzero(observed_portfolio)}
    if parsed_ids != observed_ids:
        return PortfolioTruthSnapshotV1(duplicate=True, source_id="position_snapshot_conflict")
    return observed_portfolio


def evidence_for_instrument_ids_v1(
    snapshot: PortfolioTruthSnapshotV1,
    instrument_ids: set[str],
) -> PerLanePositionTruthV1:
    """Classify one instrument from the authoritative snapshot."""
    classification, _plan, reasons = classify_productive_reconciliation_v1(
        persisted=snapshot,
        observed=snapshot,
    )
    if snapshot.duplicate or classification is ProductiveReconciliationClass.DUPLICATE_STATE:
        return PerLanePositionTruthV1(
            status="POSITION_EVIDENCE_DUPLICATE",
            venue_flat=False,
            existing_position_side=ExistingPositionSide.NONE,
            position_status_source="portfolio_snapshot",
            evidence_class="DUPLICATE",
        )
    blocked = {
        ProductiveReconciliationClass.MISSING_TRUTH,
        ProductiveReconciliationClass.STALE_SOURCE,
        ProductiveReconciliationClass.CONFLICTING_WRITER,
    }
    if snapshot.missing or snapshot.stale or snapshot.writer_conflict or classification in blocked:
        return PerLanePositionTruthV1(
            status="POSITION_EVIDENCE_MISSING",
            venue_flat=False,
            existing_position_side=ExistingPositionSide.NONE,
            position_status_source="portfolio_snapshot",
            evidence_class="MISSING",
        )
    nonzero = _nonzero(snapshot)
    if classification is ProductiveReconciliationClass.UNRECOVERABLE_DRIFT and len(nonzero) > 1:
        matched = [pos for pos in nonzero if pos.instrument_id in instrument_ids]
        if len(matched) == 1:
            return PerLanePositionTruthV1(
                status="POSITION_EVIDENCE_FOREIGN",
                venue_flat=False,
                existing_position_side=ExistingPositionSide.NONE,
                position_status_source="portfolio_snapshot",
                evidence_class="FOREIGN",
            )
        return PerLanePositionTruthV1(
            status="POSITION_EVIDENCE_DUPLICATE",
            venue_flat=False,
            existing_position_side=ExistingPositionSide.NONE,
            position_status_source="portfolio_snapshot",
            evidence_class="DUPLICATE",
        )
    if not nonzero and classification is ProductiveReconciliationClass.MATCH:
        if "NO_POSITION_CLEAN" not in reasons:
            return PerLanePositionTruthV1(
                status="POSITION_EVIDENCE_MISSING",
                venue_flat=False,
                existing_position_side=ExistingPositionSide.NONE,
                position_status_source="portfolio_snapshot",
                evidence_class="MISSING",
            )
        return PerLanePositionTruthV1(
            status="FLAT",
            venue_flat=True,
            existing_position_side=ExistingPositionSide.NONE,
            position_status_source="portfolio_snapshot",
            signed_quantity=Decimal("0"),
            evidence_class="VERIFIED_EMPTY",
        )
    matched = [pos for pos in nonzero if pos.instrument_id in instrument_ids]
    if len(matched) == 1 and len(nonzero) == 1 and matched[0].side in {"LONG", "SHORT"}:
        pos = matched[0]
        side = ExistingPositionSide.LONG if pos.side == "LONG" else ExistingPositionSide.SHORT
        return PerLanePositionTruthV1(
            status="BOUND_INSTRUMENT_OPEN",
            venue_flat=False,
            existing_position_side=side,
            position_status_source="portfolio_snapshot",
            signed_quantity=pos.signed_quantity,
            matched_instrument_id=pos.instrument_id,
            evidence_class="VERIFIED_NET",
        )
    if nonzero and not matched:
        return PerLanePositionTruthV1(
            status="FOREIGN_OPEN_POSITION_MAX_POSITIONS_1",
            venue_flat=False,
            existing_position_side=ExistingPositionSide.NONE,
            position_status_source="portfolio_snapshot",
            evidence_class="FOREIGN",
        )
    return PerLanePositionTruthV1(
        status="POSITION_EVIDENCE_DUPLICATE",
        venue_flat=False,
        existing_position_side=ExistingPositionSide.NONE,
        position_status_source="portfolio_snapshot",
        evidence_class="DUPLICATE",
    )


def resolve_per_lane_position_truth_v1(
    *,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    occupancy_payloads: Mapping[str, Any] | None,
    global_venue_flat: bool | None = None,
    global_existing_side: ExistingPositionSide | None = None,
    allow_global_fallback: bool,
    snapshot: PortfolioTruthSnapshotV1 | None = None,
) -> PerLanePositionTruthV1:
    _ = (global_venue_flat, global_existing_side, allow_global_fallback)
    chosen = snapshot
    if chosen is None:
        chosen = combine_position_snapshots_v1(occupancy_payloads, None)
    return evidence_for_instrument_ids_v1(
        chosen,
        {identity.canonical_instrument_id, identity.venue_native_id},
    )


def resolve_all_lane_position_truths_v1(
    *,
    identities: Mapping[str, OccupiedLaneRuntimeInstrumentIdentityV1],
    occupancy_payloads: Mapping[str, Any] | None,
    global_venue_flat: bool,
    global_existing_position_side: ExistingPositionSide,
    multi_lane: bool,
    snapshot: PortfolioTruthSnapshotV1 | None = None,
) -> dict[str, PerLanePositionTruthV1]:
    allow_global = not multi_lane
    if multi_lane:
        native_ids = {identities[l].venue_native_id for l in identities}
        if len(native_ids) == 1:
            allow_global = True
    out: dict[str, PerLanePositionTruthV1] = {}
    for lane_id, identity in sorted(identities.items()):
        out[lane_id] = resolve_per_lane_position_truth_v1(
            identity=identity,
            occupancy_payloads=occupancy_payloads,
            global_venue_flat=global_venue_flat,
            global_existing_side=global_existing_position_side,
            allow_global_fallback=allow_global,
            snapshot=snapshot,
        )
    if multi_lane and len({identities[l].venue_native_id for l in identities}) > 1:
        for lane_id in identities:
            if out[lane_id].position_status_source == "global_kwarg":
                raise PerLanePositionTruthError(
                    FAILURE_POSITION_SHARED_FORBIDDEN,
                    lane_id,
                )
    return out
