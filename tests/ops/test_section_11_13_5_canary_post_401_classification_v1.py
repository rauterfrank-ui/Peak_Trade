"""§11.13.5 POST HTTP-401 classification: keep shots distinct; never grant retry."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.incident_classification_v1 import (
    HISTORICAL_FIRST_401_ROOT_CAUSE,
    HTTP_401_REQUEST_CLASS_ONESHOT_TRADING_POST,
    OKX_50113_INVALID_SIGN,
    OKX_50124_OBSERVED_ONESHOT_TRADING_POST,
    UNPROVEN_FAIL_CLOSED,
    attach_canary_post_401_classification_v1,
    classify_canary_post_http_401_root_cause_v1,
    historical_first_401_root_cause_v1,
    retry_safe_now_from_401_classification_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.owner_input_contract_v1 import (
    build_owner_execute_input_contract_v1,
)

EVIDENCE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "evidence"
    / "ops"
    / "section_11_13_5_okx_50124_oneshot_post_classification_v1"
    / "20260816T002530Z"
)


def test_401_without_parseable_body_is_unproven() -> None:
    assert (
        classify_canary_post_http_401_root_cause_v1(
            http_status=401,
            json_parse_ok=False,
            okx_code=None,
        )
        == UNPROVEN_FAIL_CLOSED
    )
    assert (
        classify_canary_post_http_401_root_cause_v1(
            http_status=401,
            json_parse_ok=True,
            okx_code="",
        )
        == UNPROVEN_FAIL_CLOSED
    )


def test_401_with_50124_classifies_observed_trading_post_not_instrument_get() -> None:
    assert (
        classify_canary_post_http_401_root_cause_v1(
            http_status=401,
            json_parse_ok=True,
            okx_code="50124",
            okx_msg="This API Key does not have trading permission for the market",
        )
        == OKX_50124_OBSERVED_ONESHOT_TRADING_POST
    )


def test_401_with_50113_classifies_exact_and_does_not_rewrite_history() -> None:
    shot = classify_canary_post_http_401_root_cause_v1(
        http_status=401,
        json_parse_ok=True,
        okx_code="50113",
        okx_msg="Invalid Sign",
    )
    assert shot == OKX_50113_INVALID_SIGN
    assert historical_first_401_root_cause_v1() == UNPROVEN_FAIL_CLOSED
    assert shot != HISTORICAL_FIRST_401_ROOT_CAUSE


def test_historical_first_401_remains_unproven() -> None:
    assert HISTORICAL_FIRST_401_ROOT_CAUSE == UNPROVEN_FAIL_CLOSED
    latest = classify_canary_post_http_401_root_cause_v1(
        http_status=401,
        json_parse_ok=True,
        okx_code="50124",
        okx_msg="This API Key does not have trading permission for the market",
    )
    assert latest == OKX_50124_OBSERVED_ONESHOT_TRADING_POST
    assert HISTORICAL_FIRST_401_ROOT_CAUSE != latest


def test_classification_never_sets_retry_safe_or_live_authority() -> None:
    for cause in (
        UNPROVEN_FAIL_CLOSED,
        OKX_50124_OBSERVED_ONESHOT_TRADING_POST,
        OKX_50113_INVALID_SIGN,
        "OKX_50110_OBSERVED_PARSEABLE_BODY",
    ):
        assert retry_safe_now_from_401_classification_v1(cause) is False
    attached = attach_canary_post_401_classification_v1(
        {"ok": False},
        http_evidence={
            "http_status": 401,
            "json_parse_ok": True,
            "okx_code": "50124",
            "okx_msg": "This API Key does not have trading permission for the market",
        },
        http_status=401,
    )
    assert attached["RETRY_SAFE_NOW"] is False
    assert attached["CANARY_RETRY_AUTHORIZED"] is False
    assert attached["GENERAL_LIVE_SUBMIT_UNLOCKED"] is False
    assert attached["LIVE_AUTHORIZED"] is False
    assert attached["ROOT_CAUSE_PROVEN"] is False
    assert attached["HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN"] is False
    assert attached["HTTP_401_REQUEST_CLASS"] == HTTP_401_REQUEST_CLASS_ONESHOT_TRADING_POST
    assert attached["HISTORICAL_FIRST_401_ROOT_CAUSE"] == UNPROVEN_FAIL_CLOSED
    assert attached["POST_401_ROOT_CAUSE"] == OKX_50124_OBSERVED_ONESHOT_TRADING_POST


def test_owner_input_contract_keeps_historical_and_latest_distinct() -> None:
    contract = build_owner_execute_input_contract_v1()
    assert contract["POST_401_ROOT_CAUSE"] == UNPROVEN_FAIL_CLOSED
    assert contract["HISTORICAL_FIRST_401_ROOT_CAUSE"] == UNPROVEN_FAIL_CLOSED
    assert contract["LATEST_50124_CLASSIFICATION"] == OKX_50124_OBSERVED_ONESHOT_TRADING_POST
    assert contract["HTTP_401_REQUEST_CLASS"] == HTTP_401_REQUEST_CLASS_ONESHOT_TRADING_POST
    assert contract["HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN"] is False
    assert contract["ROOT_CAUSE_PROVEN"] is False
    assert contract["RETRY_SAFE_NOW"] is False
    assert contract["LIVE_AUTHORIZED"] is False
    assert contract["HISTORICAL_FIRST_401_ROOT_CAUSE"] != contract["LATEST_50124_CLASSIFICATION"]


def test_50124_evidence_pack_keeps_shots_distinct_and_zero_writes() -> None:
    summary = json.loads((EVIDENCE_ROOT / "SUMMARY.json").read_text(encoding="utf-8"))
    result = json.loads((EVIDENCE_ROOT / "PREPARATION_RESULT.json").read_text(encoding="utf-8"))
    zero = json.loads((EVIDENCE_ROOT / "zero_write_assertions.json").read_text(encoding="utf-8"))
    assert summary["LIVE_AUTHORIZED"] is False
    assert summary["RETRY_SAFE_NOW"] is False
    assert summary["CANARY_RETRY_AUTHORIZED"] is False
    assert result["HISTORICAL_FIRST_401_ROOT_CAUSE"] == UNPROVEN_FAIL_CLOSED
    assert result["LATEST_50124_CLASSIFICATION"] == OKX_50124_OBSERVED_ONESHOT_TRADING_POST
    assert result["HTTP_401_REQUEST_CLASS"] == HTTP_401_REQUEST_CLASS_ONESHOT_TRADING_POST
    assert result["HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN"] is False
    assert result["ROOT_CAUSE_PROVEN"] is False
    assert result["INSTRUMENT_GET_HTTP_STATUS"] == 200
    assert result["INSTRUMENT_GET_401_COUNT"] == 0
    assert result["AUTHENTICATED_GET_STATUS"] == "200_OKX_CODE_0"
    assert result["ACCOUNT_INSTRUMENTS_NOT_ON_SUBMIT_PATH"] is True
    assert result["ACCOUNT_INSTRUMENTS_CAUSAL_RELATION_TO_50124"] == "UNPROVEN"
    assert result["ACCOUNT_INSTRUMENTS_SWAP_EMPTY_LIST_EFFECT_ON_SUBMIT"] == (
        "NONE_NOT_ON_SUBMIT_PATH"
    )
    assert result["ROOT_CAUSE_CANDIDATES"] == "NONE_PROVEN"
    assert result["50124_SUBTYPE"] == "UNKNOWN_NOT_PROVEN"
    assert (
        result["HISTORICAL_OWNER_GO_TOKEN_NAME_IS_NOT_PROVEN_MARKET_PERMISSION_ROOT_CAUSE"] is True
    )
    assert "DIAGNOSTIC_CANDIDATES_NOT_PROVEN" not in result
    assert "50124_PERMISSION_ROOT_CAUSE" not in result
    assert result["HISTORICAL_FIRST_401_ROOT_CAUSE"] != result["LATEST_50124_CLASSIFICATION"]
    assert result["RETRY_SAFE_NOW"] is False
    assert zero["WRITE_REQUEST_COUNT"] == 0
    assert zero["ORDER_REQUEST_COUNT"] == 0
    dumped = json.dumps(result)
    assert "ok-access-sign" not in dumped.lower()
    assert "passphrase" not in dumped.lower()
