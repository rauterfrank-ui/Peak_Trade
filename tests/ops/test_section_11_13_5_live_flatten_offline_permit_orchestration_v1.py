"""LF-03 offline flatten permit and orchestration contract tests. No network."""

from __future__ import annotations

import inspect
from typing import Any, Mapping

import pytest

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    REDUCE_ONLY_WIRE_TYPE_STATUS,
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    ENDPOINT_CANCEL,
    ENDPOINT_SUBMIT,
    ORDER_COUNT_LIMIT,
    POST_ENDPOINTS_GATED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_orchestration_contract_v1 import (
    FLATTEN_PERMIT_KIND,
    FLATTEN_SUBMIT_UNREACHABLE_REASON,
    CanaryFlattenSubmitPermitV1,
    LiveCanaryFlattenOrchestrationError,
    evaluate_canary_flatten_orchestration_contract_v1,
    issue_canary_flatten_submit_permit_v1,
    refuse_canary_flatten_submit_transport_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryEntrySubmitPermitV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.lifecycle_v1 import (
    build_lifecycle_and_closeout_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    FLATTEN_LIMIT_PRICE_GATE_STATUS,
    serialize_canary_clordid_v1,
    serialize_canary_flatten_clordid_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    run_canary_submit_transport_v1,
)

OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "aa421d84cd0223146ab63f94405e81ed813d40c3"
TARGET = DEFAULT_INSTRUMENT_ID


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def test_long_observed_position_issues_sell_flatten_permit() -> None:
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "2"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        submitted_entry_sz="1",
        entry_lifecycle_context="ENTRY_FILLED_CONTEXT",
    )
    assert verdict.permit_issued is True
    assert verdict.permit is not None
    assert verdict.permit.side == "SELL"
    assert verdict.permit.quantity == "2"
    assert verdict.permit.kind == FLATTEN_PERMIT_KIND
    assert verdict.flatten_plan is not None
    assert verdict.flatten_plan.side == "SELL"


def test_short_observed_position_issues_buy_flatten_permit() -> None:
    permit = issue_canary_flatten_submit_permit_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "-3"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        submitted_entry_sz="1",
    )
    assert permit.side == "BUY"
    assert permit.quantity == "3"
    assert permit.reduce_only is True


def test_flatten_qty_equals_abs_observed_pos_not_submitted_entry_sz() -> None:
    permit = issue_canary_flatten_submit_permit_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "-4"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        submitted_entry_sz="1",
    )
    assert permit.quantity == "4"
    assert permit.quantity != "1"
    assert permit.submitted_entry_sz_used is False
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "5"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        submitted_entry_sz="1",
    )
    assert verdict.submitted_entry_qty_used_as_authority is False
    assert verdict.permit is not None
    assert verdict.permit.quantity == "5"


def test_zero_position_issues_no_permit_and_no_submit() -> None:
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "0"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert verdict.permit_issued is False
    assert verdict.permit is None
    assert verdict.submit_reachable is False
    assert verdict.observation_status == "ZERO_POSITION"
    with pytest.raises(LiveCanaryFlattenOrchestrationError, match="ZERO_POSITION_NO_FLATTEN_ORDER"):
        issue_canary_flatten_submit_permit_v1(
            positions_payload=_positions({"instId": TARGET, "pos": "0"}),
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )


def test_missing_target_position_fail_closed() -> None:
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": "BTC-USDT-SWAP", "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert verdict.permit_issued is False
    assert verdict.observation_status == "TARGET_INSTRUMENT_NOT_OBSERVED"
    with pytest.raises(LiveCanaryFlattenOrchestrationError, match="TARGET_INSTRUMENT_NOT_OBSERVED"):
        issue_canary_flatten_submit_permit_v1(
            positions_payload={"code": "0", "data": []},
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )


def test_malformed_pos_fail_closed() -> None:
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "not-a-number"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert verdict.permit_issued is False
    assert verdict.observation_status == "MALFORMED_POSITION"
    with pytest.raises(LiveCanaryFlattenOrchestrationError, match="POSITION_SIZE_MISSING"):
        issue_canary_flatten_submit_permit_v1(
            positions_payload=_positions({"instId": TARGET}),
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )


def test_duplicate_target_rows_fail_closed() -> None:
    payload = _positions(
        {"instId": TARGET, "pos": "1"},
        {"instId": TARGET, "pos": "1"},
    )
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=payload,
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert verdict.permit_issued is False
    assert verdict.observation_status == "AMBIGUOUS_TARGET_POSITION_ROWS"
    with pytest.raises(LiveCanaryFlattenOrchestrationError, match="AMBIGUOUS_TARGET_POSITION_ROWS"):
        issue_canary_flatten_submit_permit_v1(
            positions_payload=payload,
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )


def test_flatten_clordid_distinct_from_entry() -> None:
    entry = serialize_canary_clordid_v1(owner_go=OWNER_GO, origin_main_sha=ORIGIN_SHA)
    flatten = serialize_canary_flatten_clordid_v1(owner_go=OWNER_GO, origin_main_sha=ORIGIN_SHA)
    permit = issue_canary_flatten_submit_permit_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        entry_clordid=entry,
    )
    assert permit.clordid == flatten
    assert permit.clordid != entry
    assert (
        permit.kind
        != CanaryEntrySubmitPermitV1(owner_go=OWNER_GO, clordid=entry, permit_id="x").kind
    )


def test_flatten_requires_reduce_only_true_and_entry_omits_reduce_only() -> None:
    permit = issue_canary_flatten_submit_permit_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert permit.reduce_only is True
    entry_body = build_venue_native_order_body_v1(
        client_order_id="c1",
        instrument=TARGET,
        order_type="LIMIT",
        side="buy",
        quantity="1",
        px="10000",
    )
    assert "reduceOnly" not in entry_body
    assert REDUCE_ONLY_WIRE_TYPE_STATUS == "UNPROVEN"
    with pytest.raises(
        LiveCanaryFlattenOrchestrationError, match="FLATTEN_PERMIT_REDUCE_ONLY_REQUIRED"
    ):
        CanaryFlattenSubmitPermitV1(
            owner_go=OWNER_GO,
            clordid=permit.clordid,
            permit_id=permit.permit_id,
            instrument_id=TARGET,
            side="SELL",
            quantity="1",
            reduce_only=False,
            price_gate_status=FLATTEN_LIMIT_PRICE_GATE_STATUS,
            submitted_entry_sz_used=False,
        )


def test_missing_price_policy_blocks_submit_and_serialization() -> None:
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert verdict.permit_issued is True
    assert verdict.submit_reachable is False
    assert verdict.serialization_reachable is False
    assert verdict.permit is not None
    assert verdict.permit.submit_reachable is False
    assert verdict.permit.price_gate_status == FLATTEN_LIMIT_PRICE_GATE_STATUS
    assert FLATTEN_SUBMIT_UNREACHABLE_REASON in verdict.blocking_reasons
    with pytest.raises(LiveCanaryFlattenOrchestrationError, match="FLATTEN_NAKED_PX_FAIL_CLOSED"):
        refuse_canary_flatten_submit_transport_v1(verdict.permit, px="63028.1")
    with pytest.raises(
        LiveCanaryFlattenOrchestrationError, match="FLATTEN_SUBMIT_REACHABLE_FORBIDDEN"
    ):
        CanaryFlattenSubmitPermitV1(
            owner_go=OWNER_GO,
            clordid=verdict.permit.clordid,
            permit_id=verdict.permit.permit_id,
            instrument_id=TARGET,
            side="SELL",
            quantity="1",
            reduce_only=True,
            price_gate_status=FLATTEN_LIMIT_PRICE_GATE_STATUS,
            submitted_entry_sz_used=False,
            submit_reachable=True,
        )


def test_no_market_fallback_and_limit_only_preserved() -> None:
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert verdict.market_fallback_used is False
    assert verdict.flatten_plan is not None
    assert verdict.flatten_plan.order_type == "LIMIT"
    assert DEFAULT_ORDER_TYPE == "LIMIT"
    lifecycle = build_lifecycle_and_closeout_contract_v1()
    assert lifecycle["order_type_semantics"] == "LIMIT_ONLY_NO_MARKET"
    assert lifecycle["ACTIVATED"] is False


def test_no_second_entry_allowance_and_allowlist_unchanged() -> None:
    assert ORDER_COUNT_LIMIT == 1
    assert POST_ENDPOINTS_GATED == (
        "/api/v5/trade/order",
        "/api/v5/trade/cancel-order",
    )
    assert ENDPOINT_SUBMIT == "/api/v5/trade/order"
    assert ENDPOINT_CANCEL == "/api/v5/trade/cancel-order"
    assert "/api/v5/trade/close-position" not in POST_ENDPOINTS_GATED
    lifecycle = build_lifecycle_and_closeout_contract_v1()
    assert lifecycle["order_count_limit"] == 1
    entry = CanaryEntrySubmitPermitV1(owner_go=OWNER_GO, clordid="entry", permit_id="e1")
    assert entry.kind == "ENTRY_SUBMIT"
    flatten = issue_canary_flatten_submit_permit_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert flatten.kind == FLATTEN_PERMIT_KIND
    assert flatten.kind != entry.kind


def test_lf03_offline_path_invokes_no_transport() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import (
        flatten_orchestration_contract_v1,
        http_client_v1,
    )

    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert verdict.transport_invoked is False
    orch_src = inspect.getsource(flatten_orchestration_contract_v1)
    assert "transport.send" not in orch_src
    assert "post_flatten_order" not in orch_src
    assert "post_entry_order" not in orch_src
    assert "urllib" not in orch_src
    transport_src = inspect.getsource(run_canary_submit_transport_v1)
    assert "issue_canary_flatten_submit_permit_v1" not in transport_src
    assert "evaluate_canary_flatten_orchestration_contract_v1" not in transport_src
    assert "evaluate_canary_flatten_lifecycle_failure_matrix_v1" not in transport_src
    http_src = inspect.getsource(http_client_v1)
    assert "post_flatten_order" in http_src
    assert "CanaryFlattenHttpPermitV1" in http_src
    assert "FLATTEN_SUBMIT" in http_src
