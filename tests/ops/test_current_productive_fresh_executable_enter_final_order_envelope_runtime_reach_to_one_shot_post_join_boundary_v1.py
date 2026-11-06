"""Runtime reach: PRE_EXTERNAL typed Enter envelope → #6900 join boundary (no POST)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_boundary_v1 import (
    BLOCKER_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_UNAVAILABLE_AT_RUNTIME,
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    OWNER_GO,
    FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError,
    prove_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_v1,
    resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_RUNTIME_REACH_TO_ONE_SHOT_POST_JOIN_BOUNDARY_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    OWNER_GO as POST_OWNER_GO,
    prove_pre_live_actual_venue_post_readiness_from_pre_external_closure_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    CurrentProductiveFullCorePreExternalClosureResultV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/"
    "FULL_CORE_CURRENT_PRODUCTIVE_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_"
    "RUNTIME_REACH_TO_ONE_SHOT_POST_JOIN_BOUNDARY_V1.md"
)


def _sample_envelope():
    plan = VenuePlanCandidateV1(
        instrument_id="okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        side="buy",
        quantity="1",
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="pt-fc-runtime-reach-v1",
        venue_native_payload={
            "instId": "okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
            "ordType": "market",
            "side": "buy",
            "sz": "1",
            "tdMode": "cross",
        },
        quantity_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        side_source="TEST_FIXTURE_NOT_LIVE_ENVELOPE",
        instrument_source="DH_CAP24_BOUND_INSTRUMENT_ID",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
    )
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="adm",
        provenance_ref="prov",
        creation_epoch="2026-09-27T00:00:00Z",
    )


def _executable_closure(
    *, envelope_present: bool
) -> CurrentProductiveFullCorePreExternalClosureResultV1:
    envelope = _sample_envelope() if envelope_present else None
    return CurrentProductiveFullCorePreExternalClosureResultV1(
        store_root="/tmp/unused",
        base_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        head_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        branch="main",
        wp1_status="PASS",
        wp2_status="PASS",
        common_epoch_status="PASS",
        common_epoch_id="epoch-1",
        u01_status="PASS",
        p01_status="DOES_NOT_APPLY",
        live_account_bound_status="PASS",
        equity_producer_status="MINTED",
        bound_value_29p_status="BOUND",
        admissibility_29p_status="true",
        instrument_metadata_status="TRUSTED_CURRENT",
        reference_price_status="GOVERNED_MV2_MARK",
        mv2_capital_context_rebind_status="PASS",
        portfolio_reservation_status="PASS",
        venue_plan_status="PASS",
        final_order_envelope_status="PASS",
        terminal_disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
        gets_actually_performed=1,
        private_get_auth_path="test",
        runtime_owner_gos_consumed=(),
        synthetic_contamination=False,
        fixture_contamination=False,
        manual_injection_contamination=False,
        post_count=0,
        permit_created=False,
        external_effect_occurred=False,
        blockers_closed=("E2E-B06",),
        earliest_remaining_blocker=(
            "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
        ),
        manifest_verify_rc=0,
        current_productive_decision_result="EXECUTABLE_VENUE_PLAN_BOUND",
        decision_execution_eligible="true",
        envelope_readiness="true",
        pre_external_effect_boundary_reached="true",
        capital_context_bound="true",
        fresh_executable_enter_final_order_envelope=envelope,
    )


def test_created_flag_and_spec() -> None:
    assert (
        CURRENT_PRODUCTIVE_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_RUNTIME_REACH_TO_ONE_SHOT_POST_JOIN_BOUNDARY_CREATED
        is True
    )
    assert SPEC_PATH.is_file()
    assert OWNER_GO.startswith("OWNER_GO_")


def test_missing_typed_envelope_is_fail_closed_blocker() -> None:
    closure = _executable_closure(envelope_present=False)
    with pytest.raises(
        FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError,
        match=BLOCKER_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_UNAVAILABLE_AT_RUNTIME,
    ):
        resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1(closure)


def test_executable_closure_reaches_pre_live_boundary_without_post(tmp_path: Path) -> None:
    closure = _executable_closure(envelope_present=True)
    reach = (
        prove_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            closure=closure,
            store_root=tmp_path / "reach",
        )
    )
    assert reach.one_shot_post_join_boundary_reachable == "true"
    pre = prove_pre_live_actual_venue_post_readiness_from_pre_external_closure_v1(
        owner_go=POST_OWNER_GO,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        closure=closure,
        store_root=tmp_path / "prelive",
        k1_backend=None,
    )
    assert pre["FRESH_ENVELOPE_VALIDATED"] == "true"
    assert pre["OWNER_GO_CONSUMED"] == "false"


def test_stale_parent_baseline_sha_mismatch_fail_closed() -> None:
    stale_parent = "04345330c0898ccf2682c88fd58c32f102a8001d"
    assert stale_parent != EXPECTED_BASELINE_ORIGIN_MAIN_SHA
    closure = _executable_closure(envelope_present=True)
    with pytest.raises(
        FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError,
        match="BASELINE_SHA_MISMATCH",
    ):
        prove_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=stale_parent,
            closure=closure,
            store_root="/tmp/unused-reach-baseline-mismatch",
        )


def test_hold_closure_still_unavailable() -> None:
    closure = replace(
        _executable_closure(envelope_present=True),
        current_productive_decision_result="NO_EXECUTABLE_DECISION",
        envelope_readiness="false",
        terminal_disposition="HOLD",
        pre_external_effect_boundary_reached="false",
    )
    with pytest.raises(
        FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError,
        match="DECISION_NOT_EXECUTABLE",
    ):
        resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1(closure)
