"""Predicate tests for LIVE_PRIVATE_READ_ONLY_PROVEN adjudication."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    OWNER_GO,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.private_read_only_adjudication_v1 import (
    adjudicate_live_private_read_only_proven_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.private_read_only_gets_v1 import (
    execute_private_read_only_gets_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.private_read_only_predicate_v1 import (
    PRIVATE_READ_ONLY_CONSTITUENT_COUNT,
    PRIVATE_READ_ONLY_CONSTITUENTS,
    evaluate_private_read_only_conjunction_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _all_true() -> dict[str, bool | None]:
    return {name: True for name in PRIVATE_READ_ONLY_CONSTITUENTS}


def _successful_read_only_evidence() -> dict[str, object]:
    return {
        "CURRENT_PRIVATE_GET_CONFIG_HTTP_200_OKX_0": True,
        "CURRENT_PRIVATE_GET_BALANCE_HTTP_200_OKX_0": True,
        "BOTH_METHODS_GET": True,
        "NO_POST": True,
        "PARSEABLE_ACCOUNT_CONFIG_DATA": True,
        "PARSEABLE_ACCOUNT_BALANCE_DATA": True,
        "NO_REDIRECT": True,
        "LIVE_ORDER_PLAN_OBSERVED": False,
        "POST_USED": False,
        "PRIVATE_GET_USED": True,
        "CREDENTIAL_USE": True,
        "VENUE_REQUESTS": 2,
        "METHOD": "GET",
        "RESPONSE_TIME_UTC": "2026-09-04T13:32:00Z",
    }


def test_missing_get_does_not_prove_private_read_only() -> None:
    proof = adjudicate_live_private_read_only_proven_v1()
    assert proof["adjudicated_value"] is False
    assert "UNOBSERVED" in proof["reason"]


def test_single_config_get_is_not_private_read_only() -> None:
    values = _all_true()
    values["CURRENT_PRIVATE_GET_BALANCE_HTTP_200_OKX_0"] = False
    result = evaluate_private_read_only_conjunction_v1(constituent_values=values)
    assert result["claim_value"] is False
    assert "CURRENT_PRIVATE_GET_BALANCE_HTTP_200_OKX_0" in result["false_required"]


def test_full_conjunction_proves_private_read_only_without_order_plan() -> None:
    result = evaluate_private_read_only_conjunction_v1(constituent_values=_all_true())
    assert result["claim_value"] is True
    assert result["adjudication"] == "TRUE_CURRENT_PRIVATE_READ_ONLY"
    assert PRIVATE_READ_ONLY_CONSTITUENT_COUNT == 9
    proof = adjudicate_live_private_read_only_proven_v1(
        private_read_only_evidence=_successful_read_only_evidence()
    )
    assert proof["adjudicated_value"] is True
    assert proof["LIVE_ORDER_PLAN_OBSERVED"] is False
    assert LIVE_PRIVATE_READ_ONLY_PROVEN is True
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_post_in_evidence_is_rejected() -> None:
    bad = dict(_successful_read_only_evidence())
    bad["POST_USED"] = True
    with pytest.raises(Section1114OfflineSurfaceError, match="POST_INVOKED"):
        adjudicate_live_private_read_only_proven_v1(private_read_only_evidence=bad)


def test_order_plan_promotion_in_get_evidence_is_rejected() -> None:
    bad = dict(_successful_read_only_evidence())
    bad["LIVE_ORDER_PLAN_OBSERVED"] = True
    with pytest.raises(Section1114OfflineSurfaceError, match="ORDER_PLAN"):
        adjudicate_live_private_read_only_proven_v1(private_read_only_evidence=bad)


def test_fake_transport_issues_exactly_two_gets_and_no_post() -> None:
    fake = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={
            ENDPOINT_ACCOUNT_CONFIG: b'{"code":"0","data":[{"posMode":"net_mode","acctLv":"2"}]}',
            ENDPOINT_ACCOUNT_BALANCE: b'{"code":"0","data":[{"details":[{"ccy":"USDC"}]}]}',
        }
    )
    result = execute_private_read_only_gets_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        transport=fake,
    )
    assert result["METHOD"] == "GET"
    assert result["POST_USED"] is False
    assert result["RETRY_USED"] is False
    assert result["VENUE_REQUESTS"] == 2
    assert result["LIVE_PRIVATE_READ_ONLY_PROVEN"] is True
    assert result["LIVE_ORDER_PLAN_OBSERVED"] is False
    assert [call.method for call in fake.calls] == ["GET", "GET"]
    endpoints = [call.endpoint for call in fake.calls]
    assert ENDPOINT_ACCOUNT_CONFIG in endpoints[0]
    assert ENDPOINT_ACCOUNT_BALANCE in endpoints[1]
    with pytest.raises(Section1114OfflineSurfaceError, match="OWNER_GO_MISMATCH"):
        execute_private_read_only_gets_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            transport=fake,
        )


def test_fixture_source_rejected() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
        evaluate_private_read_only_conjunction_v1(
            constituent_values=_all_true(),
            source_kind="FIXTURE",
        )


def test_contract_keeps_submit_gates_false() -> None:
    assert_contract_invariants_v1()
    assert LIVE_ENABLED is False
    assert SUBMIT_UNLOCKED is False
