"""P1 position-evidence cases. No orders and no second position authority."""

from __future__ import annotations

from decimal import Decimal

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_RECONCILIATION_GLOBAL,
    FAILURE_RECONCILIATION_INSTRUMENT,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
    evidence_for_instrument_ids_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.reconciliation_admission_v1 import (
    build_per_lane_reconciliation_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    PositionState,
    okx_positions_payload_to_portfolio_snapshot_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def _identity(native: str = "BTC-USDT-SWAP") -> OccupiedLaneRuntimeInstrumentIdentityV1:
    bound = BoundInstrumentV1(
        instrument_id="INST-BTC",
        venue_native_id=native,
        ranking_snapshot_id="r",
        ranking_integrity_digest="d",
        universe_snapshot_id="u",
        selection_id="s",
        selection_integrity_digest="sd",
        selection_state="SELECTED_ACTIVE",
    )
    return OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(lane_id="LANE_1", bound=bound)


def _state_for(evidence_class: str) -> PositionState:
    if evidence_class == "VERIFIED_EMPTY":
        return PositionState.FLAT_RECONCILED
    if evidence_class == "VERIFIED_NET":
        return PositionState.OPEN_FULL
    raise AssertionError(evidence_class)


def test_missing_evidence_is_fail_closed() -> None:
    snapshot = okx_positions_payload_to_portfolio_snapshot_v1(None)
    evidence = evidence_for_instrument_ids_v1(snapshot, {"BTC-USDT-SWAP"})
    assert evidence.evidence_class == "MISSING"
    assert evidence.venue_flat is False
    admission = build_per_lane_reconciliation_admission_v1(
        identity=_identity(),
        portfolio=snapshot,
    )
    assert admission.admitted is False
    assert admission.reason_code == FAILURE_RECONCILIATION_GLOBAL


def test_verified_empty_snapshot_is_flat_reconciled() -> None:
    payload = {"code": "0", "data": []}
    snapshot = okx_positions_payload_to_portfolio_snapshot_v1(payload)
    evidence = evidence_for_instrument_ids_v1(snapshot, {"BTC-USDT-SWAP", "INST-BTC"})
    assert evidence.evidence_class == "VERIFIED_EMPTY"
    assert evidence.signed_quantity == Decimal("0")
    assert _state_for(evidence.evidence_class) is PositionState.FLAT_RECONCILED
    admission = build_per_lane_reconciliation_admission_v1(
        identity=_identity(),
        portfolio=snapshot,
    )
    assert admission.admitted is True
    assert admission.reason_code == "NO_POSITION_CLEAN"


def test_one_net_row_preserves_identity_side_and_quantity() -> None:
    snapshot = okx_positions_payload_to_portfolio_snapshot_v1(
        {"code": "0", "data": [{"instId": "BTC-USDT-SWAP", "posSide": "long", "pos": "1.5"}]}
    )
    evidence = evidence_for_instrument_ids_v1(snapshot, {"BTC-USDT-SWAP", "INST-BTC"})
    assert evidence.evidence_class == "VERIFIED_NET"
    assert evidence.matched_instrument_id == "BTC-USDT-SWAP"
    assert evidence.existing_position_side.value == "long"
    assert evidence.signed_quantity == Decimal("1.5")
    assert _state_for(evidence.evidence_class) is PositionState.OPEN_FULL
    assert "entry_price" not in snapshot.to_dict()["positions"][0]


def test_duplicate_rows_fail_closed() -> None:
    snapshot = okx_positions_payload_to_portfolio_snapshot_v1(
        {
            "code": "0",
            "data": [
                {"instId": "BTC-USDT-SWAP", "posSide": "long", "pos": "1"},
                {"instId": "BTC-USDT-SWAP", "posSide": "short", "pos": "-1"},
            ],
        }
    )
    evidence = evidence_for_instrument_ids_v1(snapshot, {"BTC-USDT-SWAP"})
    assert evidence.evidence_class == "DUPLICATE"
    assert evidence.venue_flat is False
    admission = build_per_lane_reconciliation_admission_v1(
        identity=_identity(),
        portfolio=snapshot,
    )
    assert admission.admitted is False


def test_foreign_instrument_does_not_become_flat() -> None:
    snapshot = PortfolioTruthSnapshotV1(
        positions=(
            PositionTruthV1.from_signed(
                instrument_id="ETH-USDT-SWAP", signed_quantity=Decimal("2")
            ),
        )
    )
    evidence = evidence_for_instrument_ids_v1(snapshot, {"BTC-USDT-SWAP", "INST-BTC"})
    assert evidence.evidence_class == "FOREIGN"
    assert evidence.venue_flat is False
    admission = build_per_lane_reconciliation_admission_v1(
        identity=_identity(),
        portfolio=snapshot,
    )
    assert admission.admitted is False
    assert admission.reason_code == FAILURE_RECONCILIATION_INSTRUMENT
