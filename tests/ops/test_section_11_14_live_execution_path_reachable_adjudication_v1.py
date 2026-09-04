"""Predicate tests for LIVE_EXECUTION_PATH_REACHABLE adjudication."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_FILL_OBSERVED,
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    LIVE_SUBMIT_ACK_OBSERVED,
    OWNER_GO,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.path_reachable_adjudication_v1 import (
    adjudicate_live_execution_path_reachable_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.path_reachable_predicate_v1 import (
    REACHABILITY_CONSTITUENT_COUNT,
    REACHABILITY_CONSTITUENTS,
    evaluate_reachability_conjunction_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.reachability_private_get_v1 import (
    execute_reachability_private_get_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.runtime_gate_classification_v1 import (
    classify_runtime_gates_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _all_true() -> dict[str, bool | None]:
    return {name: True for name in REACHABILITY_CONSTITUENTS}


def _successful_get_evidence() -> dict[str, object]:
    return {
        "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE": True,
        "AUTHENTICATION_PATH_FUNCTIONAL": True,
        "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL": True,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "POST_USED": False,
        "PRIVATE_GET_USED": True,
        "CREDENTIAL_USE": True,
        "VENUE_REQUESTS": 1,
        "METHOD": "GET",
        "RESPONSE_TIME_UTC": "2026-09-04T13:00:00Z",
    }


def test_static_code_exists_does_not_imply_reachable_without_get() -> None:
    assert LIVE_EXECUTION_CODE_EXISTS is True
    proof = adjudicate_live_execution_path_reachable_v1(repo_root=REPO_ROOT)
    assert proof["adjudicated_value"] is False
    assert "UNOBSERVED" in proof["reason"] or "FALSE" in proof["reason"]


def test_historical_success_is_not_current_reachable() -> None:
    values = _all_true()
    values["AUTHENTICATION_PATH_FUNCTIONAL"] = None
    result = evaluate_reachability_conjunction_v1(constituent_values=values)
    assert result["claim_value"] is False
    assert "AUTHENTICATION_PATH_FUNCTIONAL" in result["unobserved_required"]


def test_configured_credentials_do_not_imply_auth_success() -> None:
    values = _all_true()
    values["REQUIRED_CREDENTIAL_MATERIAL_AVAILABLE"] = True
    values["AUTHENTICATION_PATH_FUNCTIONAL"] = False
    result = evaluate_reachability_conjunction_v1(constituent_values=values)
    assert result["claim_value"] is False
    assert "AUTHENTICATION_PATH_FUNCTIONAL" in result["false_required"]


def test_successful_auth_does_not_imply_submit_authorization() -> None:
    proof = adjudicate_live_execution_path_reachable_v1(
        repo_root=REPO_ROOT,
        credential_presence={"available": True, "VALUES_INCLUDED": False},
        private_get_evidence=_successful_get_evidence(),
    )
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert CANARY_AUTHORIZED is False
    assert proof["submit_authorization_inferred"] is False
    gates = classify_runtime_gates_v1()
    assert gates["mutation_performed"] is False
    assert gates["all_standing_live_submit_gates_false"] is True


def test_venue_connectivity_does_not_promote_later_ladder_fields() -> None:
    proof = adjudicate_live_execution_path_reachable_v1(
        repo_root=REPO_ROOT,
        credential_presence={"available": True, "VALUES_INCLUDED": False},
        private_get_evidence=_successful_get_evidence(),
    )
    assert proof["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False
    assert proof["LIVE_ORDER_PLAN_OBSERVED"] is False
    assert LIVE_PRIVATE_READ_ONLY_PROVEN is True
    assert LIVE_ORDER_PLAN_OBSERVED is False
    assert LIVE_SUBMIT_ACK_OBSERVED is False
    assert LIVE_FILL_OBSERVED is False


def test_false_required_constituent_makes_path_reachable_false() -> None:
    values = _all_true()
    values["TRANSPORT_CONSTRUCTIBLE"] = False
    result = evaluate_reachability_conjunction_v1(constituent_values=values)
    assert result["claim_value"] is False
    assert result["adjudication"] == "FALSE_REQUIRED_CONSTITUENT"


def test_unobserved_required_constituent_makes_path_reachable_false() -> None:
    values = _all_true()
    values["TARGET_HOST_RESOLVABLE_OR_CONNECTABLE"] = None
    result = evaluate_reachability_conjunction_v1(constituent_values=values)
    assert result["claim_value"] is False
    assert result["adjudication"] == "FALSE_UNOBSERVED_REQUIRED_CONSTITUENT"


def test_true_requires_full_conjunction() -> None:
    result = evaluate_reachability_conjunction_v1(constituent_values=_all_true())
    assert result["claim_value"] is True
    assert result["adjudication"] == "TRUE_PRE_SUBMIT_PATH_REACHABLE"
    assert REACHABILITY_CONSTITUENT_COUNT == 10
    assert len(REACHABILITY_CONSTITUENTS) == 10


def test_private_get_evidence_does_not_promote_live_private_read_only_proven() -> None:
    bad = dict(_successful_get_evidence())
    bad["LIVE_PRIVATE_READ_ONLY_PROVEN"] = True
    with pytest.raises(
        Section1114OfflineSurfaceError,
        match="GET_EVIDENCE_PROMOTED_LIVE_PRIVATE_READ_ONLY_PROVEN",
    ):
        adjudicate_live_execution_path_reachable_v1(
            repo_root=REPO_ROOT,
            credential_presence={"available": True, "VALUES_INCLUDED": False},
            private_get_evidence=bad,
        )


def test_no_post_path_can_be_invoked_by_reachability_proof() -> None:
    fake = RecordingFakeCanaryTransportV1(
        body=b'{"code":"0","data":[{"posMode":"net_mode","acctLv":"2"}]}'
    )
    result = execute_reachability_private_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        transport=fake,
    )
    assert result["METHOD"] == "GET"
    assert result["POST_USED"] is False
    assert result["RETRY_USED"] is False
    assert result["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False
    assert fake.calls and fake.calls[0].method == "GET"
    assert all(call.method != "POST" for call in fake.calls)
    with pytest.raises(Section1114OfflineSurfaceError, match="OWNER_GO_MISMATCH"):
        execute_reachability_private_get_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            transport=fake,
        )


def test_no_gate_mutation_is_permitted() -> None:
    assert_contract_invariants_v1()
    gates = classify_runtime_gates_v1()
    assert gates["mutation_performed"] is False
    for row in gates["rows"]:
        assert row["mutated_by_this_go"] is False
        assert row["repo_default"] is False


def test_fixture_source_rejected_for_reachability() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
        evaluate_reachability_conjunction_v1(
            constituent_values=_all_true(),
            source_kind="FIXTURE",
        )
