"""Predicate tests for LIVE_ORDER_PLAN_OBSERVED adjudication."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED as CANARY_LIVE_ARMED,
    LIVE_ENABLED as CANARY_LIVE_ENABLED,
    SUBMIT_UNLOCKED as CANARY_SUBMIT_UNLOCKED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_ORDER_PLAN_OWNER_GO,
    HISTORICAL_ORDER_PLAN_SHA,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_SUBMIT_ACK_OBSERVED,
    POST_REQUIRED_FOR_LIVE_ORDER_PLAN_OBSERVED,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.order_plan_observe_execute_v1 import (
    execute_order_plan_observe_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.order_plan_observed_adjudication_v1 import (
    adjudicate_live_order_plan_observed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.order_plan_observed_predicate_v1 import (
    ORDER_PLAN_OBSERVED_CONSTITUENT_COUNT,
    ORDER_PLAN_OBSERVED_CONSTITUENTS,
    evaluate_order_plan_observed_conjunction_v1,
)

from tests.ops.test_section_11_13_5_canary_submit_transport_v1 import _MemVault, _fake_transport

REPO_ROOT = Path(__file__).resolve().parents[2]


def _all_true() -> dict[str, bool | None]:
    return {name: True for name in ORDER_PLAN_OBSERVED_CONSTITUENTS}


def _successful_order_plan_evidence() -> dict[str, object]:
    return {
        "LIVE_EXECUTION_CODE_EXISTS": True,
        "LIVE_EXECUTION_PATH_REACHABLE": True,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": True,
        "PRODUCED_ON_CANONICAL_SUBMIT_PATH": True,
        "AFTER_REFUSE_SUBMIT_UNLESS_GATES_PASS": True,
        "CURRENT_VENUE_DERIVED_INPUTS": True,
        "ORDER_PLAN_ARTIFACT_PRESENT": True,
        "NOT_BLOCKED_DRY_RUN": True,
        "NOT_DIRECT_BUILDER_INVOCATION": True,
        "NO_POST_REQUIRED": True,
        "POST_USED": False,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "LIVE_ORDER_PLAN_OBSERVED": True,
    }


def test_missing_evidence_does_not_prove_order_plan() -> None:
    proof = adjudicate_live_order_plan_observed_v1()
    assert proof["adjudicated_value"] is False
    assert "UNOBSERVED" in proof["reason"]
    assert LIVE_SUBMIT_ACK_OBSERVED is False


def test_blocked_dry_run_constituent_prevents_claim() -> None:
    values = _all_true()
    values["NOT_BLOCKED_DRY_RUN"] = False
    result = evaluate_order_plan_observed_conjunction_v1(constituent_values=values)
    assert result["claim_value"] is False
    assert "NOT_BLOCKED_DRY_RUN" in result["false_required"]


def test_full_conjunction_proves_order_plan_without_submit_ack() -> None:
    result = evaluate_order_plan_observed_conjunction_v1(constituent_values=_all_true())
    assert result["claim_value"] is True
    assert ORDER_PLAN_OBSERVED_CONSTITUENT_COUNT == 10
    assert POST_REQUIRED_FOR_LIVE_ORDER_PLAN_OBSERVED is False
    proof = adjudicate_live_order_plan_observed_v1(
        order_plan_evidence=_successful_order_plan_evidence()
    )
    assert proof["adjudicated_value"] is True
    assert LIVE_ORDER_PLAN_OBSERVED is True
    assert proof["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert CANARY_LIVE_ENABLED is False
    assert CANARY_LIVE_ARMED is False
    assert CANARY_SUBMIT_UNLOCKED is False


def test_post_in_order_plan_evidence_is_rejected() -> None:
    bad = dict(_successful_order_plan_evidence())
    bad["POST_USED"] = True
    with pytest.raises(Section1114OfflineSurfaceError, match="POST_INVOKED"):
        adjudicate_live_order_plan_observed_v1(order_plan_evidence=bad)


def test_submit_ack_promotion_in_order_plan_evidence_is_rejected() -> None:
    bad = dict(_successful_order_plan_evidence())
    bad["LIVE_SUBMIT_ACK_OBSERVED"] = True
    with pytest.raises(Section1114OfflineSurfaceError, match="SUBMIT_ACK"):
        adjudicate_live_order_plan_observed_v1(order_plan_evidence=bad)


def test_fixture_source_rejected() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
        evaluate_order_plan_observed_conjunction_v1(
            constituent_values=_all_true(),
            source_kind="FIXTURE",
        )


def test_execute_observe_path_with_fake_transport_does_not_post() -> None:
    fake = _fake_transport()
    result = execute_order_plan_observe_v1(
        owner_go=HISTORICAL_ORDER_PLAN_OWNER_GO,
        origin_main_sha=HISTORICAL_ORDER_PLAN_SHA,
        transport=fake,
        vault_backend=_MemVault(),
    )
    assert result["POST_USED"] is False
    assert result["SUBMIT_USED"] is False
    assert result["LIVE_SUBMIT_ACK_OBSERVED"] is False
    assert result["LIVE_GATE_ACTIVATION_USED"] is True
    assert result["LIVE_GATES_RETURNED_FAIL_CLOSED"] is True
    assert result["LIVE_ORDER_PLAN_OBSERVED"] is True
    assert result["plan"]["instrument_id"] == DEFAULT_INSTRUMENT_ID
    assert result["plan"]["quantity"] == "1"
    assert [call.method for call in fake.calls if call.method == "POST"] == []
    with pytest.raises(Section1114OfflineSurfaceError, match="OWNER_GO_MISMATCH"):
        execute_order_plan_observe_v1(
            owner_go="WRONG",
            origin_main_sha=HISTORICAL_ORDER_PLAN_SHA,
            transport=fake,
            vault_backend=_MemVault(),
        )
    proof = adjudicate_live_order_plan_observed_v1(order_plan_evidence=result)
    assert proof["adjudicated_value"] is True


def test_standing_gates_remain_false_after_observe() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert LIVE_AUTHORIZED is False
    assert REPO_ROOT.is_dir()
