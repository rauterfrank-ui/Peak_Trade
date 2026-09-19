"""Staged N=5 productive runtime admission, recovery, and audit tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1 import (
    CONTRACT_ID,
    ENTRYPOINT_SYMBOL,
    EXTERNAL_EFFECT_AUTHORIZATION,
    N5_ARCHITECTURE_COMPLETE,
    N5_PRODUCTIVE_COMPOSITION_COMPLETE,
    N_GT_1_CAPABILITY_PRESENT,
    N_GT_1_ENABLED,
    N_GT_1_PRODUCTIVE_AUTHORIZATION,
    OWNER,
    PORTFOLIO_RESTART_STATUS,
    PRODUCTIVE_CONTROL_PLANE_ENTRYPOINT,
    TARGET_CARDINALITY_RANGE,
    run_staged_productive_full_autonomy_n5_runtime_control_plane_v1,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.constants_v1 import (
    ADMISSION_ARCHITECTURAL_HARNESS,
    ADMISSION_DENIED_N_GT_1,
    ADMISSION_PRODUCTIVE,
    AGGREGATE_ADMISSION_DENIED,
    EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PERMIT_MINT_STATUS,
    POST_ALLOWED,
    VENUE_SUBMISSION_STATUS,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.staged_cardinality_v1 import (
    StagedTargetCardinalityError,
    evaluate_staged_target_cardinality_v1,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    ProductiveFullAutonomyCap24BindContextV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from tests.ops.test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 import (
    OBSERVED_UNIX,
    REPO_SHA,
    _cid,
    _empty_portfolio,
    _five_rows,
    _held_writer,
    _membership,
    _persist_universe_and_ranking,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    ORIGIN_SHA,
    _market_kwargs,
    _memory_g17_producer,
)

PACKAGE = Path(__file__).resolve().parents[2] / (
    "src/ops/current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1"
)
CONTROL_SOURCE = (PACKAGE / "control_plane_v1.py").read_text(encoding="utf-8")


def _g17(chain: dict, natives: list[str], n: int) -> dict[str, object]:
    return {
        LANE_IDS[i]: _memory_g17_producer(
            instrument_id=_cid(chain["ranking"], natives[i]),
            venue_native_id=natives[i],
        )
        for i in range(n)
    }


def _run_control(
    tmp_path: Path,
    *,
    requested: int,
    instrument_rows: list[str],
    harness: bool = False,
):
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    topology_root = tmp_path / "topology"
    topology_root.mkdir()
    instruments = [_cid(chain["ranking"], n) for n in instrument_rows]
    membership = _membership(chain["ranking"], instruments)
    writer = _held_writer(topology_root)
    cap24 = ProductiveFullAutonomyCap24BindContextV1(
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        reconciliation_state_root=chain["recon_root"],
        observed_portfolio=_empty_portfolio(),
        mark_price_by_native_id=chain["mark_price_by_native_id"],
        session_id="pr3-control",
        now_unix=OBSERVED_UNIX,
    )
    cycle = _market_kwargs(cycle_id_prefix="pr3-cp")
    cycle.pop("origin_main_sha", None)
    cycle["g17_typed_vol_producers"] = _g17(
        chain, instrument_rows, requested if harness else min(requested, len(instrument_rows))
    )
    try:
        return run_staged_productive_full_autonomy_n5_runtime_control_plane_v1(
            membership=membership,
            ranking_snapshot=chain["ranking"],
            topology_state_root_base=topology_root,
            lane_assignment_writer=writer,
            cap24_bind=cap24,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX,
            origin_main_sha=ORIGIN_SHA,
            requested_target_cardinality=requested,
            portfolio_budget_owner=PortfolioCapitalReservationBudgetOwnerV1(),
            architectural_composition_harness=harness,
            **cycle,
        )
    finally:
        writer.release()


def test_constants_and_final_architecture_adjudication() -> None:
    assert CONTRACT_ID == (
        "CURRENT_MF_N5_STAGED_PRODUCTIVE_RUNTIME_ADMISSION_RECOVERY_AUDIT_CONTRACT_V1"
    )
    assert OWNER == "ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1"
    assert ENTRYPOINT_SYMBOL == "run_staged_productive_full_autonomy_n5_runtime_control_plane_v1"
    assert TARGET_CARDINALITY_RANGE == "1..5"
    assert N5_ARCHITECTURE_COMPLETE is True
    assert N5_PRODUCTIVE_COMPOSITION_COMPLETE is True
    assert N_GT_1_CAPABILITY_PRESENT is True
    assert N_GT_1_PRODUCTIVE_AUTHORIZATION is False
    assert EXTERNAL_EFFECT_AUTHORIZATION is False
    assert N_GT_1_ENABLED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert PERMIT_MINT_STATUS == "FORBIDDEN"
    assert VENUE_SUBMISSION_STATUS == "FORBIDDEN"
    assert PORTFOLIO_RESTART_STATUS == "FAIL_CLOSED_NO_UNPROVEN_RESTORE"


def test_control_plane_composes_orchestrator_not_mv2_directly() -> None:
    called = {
        node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        for node in ast.walk(ast.parse(CONTROL_SOURCE))
        if isinstance(node, ast.Call)
    }
    assert "run_productive_full_autonomy_n5_runtime_orchestrator_v1" in called
    assert "run_current_productive_master_v2_runtime_cycle_v1" not in called


def test_staged_cardinality_bounds_and_authorization_negative() -> None:
    d1 = evaluate_staged_target_cardinality_v1(requested_target_cardinality=1)
    assert d1.admission_class == ADMISSION_PRODUCTIVE
    assert d1.invocation_cardinality == 1
    assert d1.productive_admitted is True

    d5_denied = evaluate_staged_target_cardinality_v1(requested_target_cardinality=5)
    assert d5_denied.admission_class == ADMISSION_DENIED_N_GT_1
    assert d5_denied.invocation_cardinality == 0
    assert d5_denied.productive_admitted is False

    d5_harness = evaluate_staged_target_cardinality_v1(
        requested_target_cardinality=5,
        architectural_composition_harness=True,
    )
    assert d5_harness.admission_class == ADMISSION_ARCHITECTURAL_HARNESS
    assert d5_harness.invocation_cardinality == 5
    assert d5_harness.productive_admitted is False

    with pytest.raises(StagedTargetCardinalityError):
        evaluate_staged_target_cardinality_v1(requested_target_cardinality=0)


def test_productive_n1_regression_via_control_plane(tmp_path: Path) -> None:
    result = _run_control(
        tmp_path,
        requested=1,
        instrument_rows=["SOL-USDT-SWAP"],
    )
    assert result.cardinality.admission_class == ADMISSION_PRODUCTIVE
    assert result.orchestrator_result is not None
    assert result.aggregate.admission_denied_before_orchestration is False
    assert result.external_effect_authorized is False
    assert result.audit.permit_mint_status == "FORBIDDEN"
    assert result.recovery.restart_self_authorization_forbidden is True
    assert result.recovery.portfolio_reconstruction_attempted is False


def test_requested_n_gt_1_fail_closed_without_harness(tmp_path: Path) -> None:
    result = _run_control(
        tmp_path,
        requested=3,
        instrument_rows=["SOL-USDT-SWAP", "ETH-USDT-SWAP", "ADA-USDT-SWAP"],
    )
    assert result.orchestrator_result is None
    assert result.cardinality.admission_class == ADMISSION_DENIED_N_GT_1
    assert result.aggregate.aggregate_class == AGGREGATE_ADMISSION_DENIED
    assert result.aggregate.aggregate_disposition == DISPOSITION_FAIL_CLOSED
    assert result.audit.invocation_cardinality == 0


def test_ranking_membership_count_cannot_self_authorize(tmp_path: Path) -> None:
    result = _run_control(
        tmp_path,
        requested=2,
        instrument_rows=["SOL-USDT-SWAP", "ETH-USDT-SWAP", "ADA-USDT-SWAP"],
    )
    assert result.orchestrator_result is None
    assert result.cardinality.productive_admitted is False


@pytest.mark.parametrize("target", (2, 5))
def test_architectural_harness_composition(tmp_path: Path, target: int) -> None:
    natives = ["SOL-USDT-SWAP", "ETH-USDT-SWAP", "ADA-USDT-SWAP", "LINK-USDT-SWAP", "APT-USDT-SWAP"]
    result = _run_control(
        tmp_path,
        requested=target,
        instrument_rows=natives[:target],
        harness=True,
    )
    assert result.cardinality.admission_class == ADMISSION_ARCHITECTURAL_HARNESS
    assert result.cardinality.productive_admitted is False
    assert result.orchestrator_result is not None
    assert len(result.orchestrator_result.lane_rollups) == target
    roots = {r.cursor_store_root for r in result.orchestrator_result.lane_rollups}
    assert len(roots) == target
    assert result.aggregate.aggregate_disposition in {
        DISPOSITION_PRE_EXTERNAL_EFFECT,
        DISPOSITION_HOLD,
    }
    assert result.audit.n_gt_1_productive_authorization is False
