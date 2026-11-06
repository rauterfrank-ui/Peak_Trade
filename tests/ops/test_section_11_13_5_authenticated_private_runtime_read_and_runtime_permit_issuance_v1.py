"""Authenticated private GET and runtime permit issuance tests. Recording transport only."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_D_TARGET_NOT_OBSERVED,
    CASE_E_HTTP_OR_OKX_ERROR,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EMPTY_DATA_IS_ZERO_VALUE,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FRESHNESS_POLICY_MAX_AGE_MS,
    GET_ALLOWED,
    NEXT_AUTHORITY_BOUNDARY,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    POST_ALLOWED,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.execute_v1 import (
    AuthenticatedPrivateRuntimeReadError,
    execute_authenticated_private_runtime_read_and_permit_issuance_v1,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.runtime_permit_v1 import (
    REASON_EMPTY_DATA,
    REASON_NOT_OBSERVED,
    REASON_OBSERVATION_NOT_FRESH,
    REASON_ZERO_POSITION,
    evaluate_runtime_permit_issuance_v1,
    runtime_permit_identity_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
)

NONZERO_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"1","posSide":"net","mgnMode":"isolated"}]}'
)
ZERO_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"0","posSide":"net","mgnMode":"isolated"}]}'
)
EMPTY_BODY = b'{"code":"0","msg":"","data":[]}'
OTHER_INST_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"BTC-USDT-SWAP","pos":"2",'
    b'"posSide":"net","mgnMode":"isolated"}]}'
)
FAIL_401_BODY = (
    b'{"code":"50110","msg":"Your IP 203.0.113.50 is not included in your API '
    b'key\'s IP whitelist.","data":[]}'
)


def _run(tmp_path: Path, body: bytes, *, status: int = 200) -> dict:
    transport = RecordingFakeCanaryTransportV1(status_code=status, body=body)
    return execute_authenticated_private_runtime_read_and_permit_issuance_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )


def test_standing_flags_remain_fail_closed() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert POST_ALLOWED is False
    assert GET_ALLOWED is True
    assert EMPTY_DATA_IS_ZERO_VALUE is False
    assert FRESHNESS_POLICY_MAX_AGE_MS == 5000
    assert POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS == 5000
    assert ENDPOINT == "/api/v5/account/positions"
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert TARGET_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"
    assert THIS_SLICE == "11.13.5.AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE"
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION"
    assert NEXT_AUTHORITY_BOUNDARY == "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION"
    assert NEXT_OWNER_GO_REQUIRED == "NOT_PERSISTED_IN_CURRENT_REPO_EVIDENCE"
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert CLAIMS["NETWORK_SESSION_AUTHORIZED"] is False
    assert CLAIMS["LIVE_AUTHORIZED"] is False if "LIVE_AUTHORIZED" in CLAIMS else True
    assert CLAIMS["PRODUCTIVE_FLATTEN_POST_AUTHORIZED"] is False
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False


def test_nonzero_observation_issues_permit(tmp_path: Path) -> None:
    result = _run(tmp_path, NONZERO_BODY)
    summary = result["summary"]
    observation = result["runtime_facts"]["OBSERVATION"]
    assert observation["POSITION_OBSERVATION_CLASS"] == CASE_A_TARGET_NONZERO
    assert summary["GET_PERFORMED_THIS_PERSIST"] is True
    assert summary["POST_PERFORMED"] is False
    assert summary["RUNTIME_PERMIT_ISSUED"] is True
    assert summary["PERMIT_ISSUANCE_RESULT"] == "PASS"
    assert summary["PERMIT_ID_OR_HASH"]
    assert summary["NETWORK_SESSION_AUTHORIZED"] is False
    assert summary["FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert summary["G06_STATUS"] == "CLOSED_SIZE_AND_OBSERVATION_BINDING"
    assert result["MANIFEST_VERIFY_RC"] == 0
    permit = result["RUNTIME_PERMIT"]["permit"]
    assert permit["size_binding"]
    assert permit["observation_identity"]
    assert permit["observation_body_sha256"]
    digest = runtime_permit_identity_sha256_v1(permit)
    assert digest == result["RUNTIME_PERMIT"]["permit_identity_sha256"]
    replay = runtime_permit_identity_sha256_v1(permit)
    assert replay == digest


def test_empty_data_is_not_zero_and_denies_permit(tmp_path: Path) -> None:
    result = _run(tmp_path, EMPTY_BODY)
    observation = result["runtime_facts"]["OBSERVATION"]
    assert observation["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
    assert observation["TARGET_POSITION_ZERO_PROVEN"] is False
    assert result["summary"]["RUNTIME_PERMIT_ISSUED"] is False
    assert result["summary"]["PERMIT_ISSUANCE_RESULT"] == "FAIL_CLOSED"
    assert REASON_EMPTY_DATA in result["adjudication"]["PERMIT_DENY_REASONS"]


def test_zero_row_denies_permit(tmp_path: Path) -> None:
    result = _run(tmp_path, ZERO_BODY)
    observation = result["runtime_facts"]["OBSERVATION"]
    assert observation["POSITION_OBSERVATION_CLASS"] == CASE_B_TARGET_ZERO
    assert result["summary"]["RUNTIME_PERMIT_ISSUED"] is False
    assert REASON_ZERO_POSITION in result["adjudication"]["PERMIT_DENY_REASONS"]


def test_other_instrument_is_not_observed(tmp_path: Path) -> None:
    result = _run(tmp_path, OTHER_INST_BODY)
    observation = result["runtime_facts"]["OBSERVATION"]
    assert observation["POSITION_OBSERVATION_CLASS"] == CASE_D_TARGET_NOT_OBSERVED
    assert result["summary"]["RUNTIME_PERMIT_ISSUED"] is False
    assert REASON_NOT_OBSERVED in result["adjudication"]["PERMIT_DENY_REASONS"]


def test_auth_failure_denies_permit(tmp_path: Path) -> None:
    result = _run(tmp_path, FAIL_401_BODY, status=401)
    observation = result["runtime_facts"]["OBSERVATION"]
    assert observation["POSITION_OBSERVATION_CLASS"] == CASE_E_HTTP_OR_OKX_ERROR
    assert result["summary"]["RUNTIME_PERMIT_ISSUED"] is False
    assert result["summary"]["POST_PERFORMED"] is False


def test_unsigned_flatten_transport_is_rejected(tmp_path: Path) -> None:
    transport = GatedProductiveFlattenTransportV1()
    with pytest.raises(AuthenticatedPrivateRuntimeReadError, match="UNSIGNED_FLATTEN"):
        execute_authenticated_private_runtime_read_and_permit_issuance_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=transport,
        )


def test_wrong_owner_go_denied(tmp_path: Path) -> None:
    with pytest.raises(AuthenticatedPrivateRuntimeReadError, match="OWNER_GO_MISMATCH"):
        execute_authenticated_private_runtime_read_and_permit_issuance_v1(
            owner_go="SECTION_11_13_5_BOUNDED_ACTIVATION_OWNER_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(body=NONZERO_BODY),
        )


def test_stale_observation_denies_issuance() -> None:
    permit, reasons = evaluate_runtime_permit_issuance_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET_INSTRUMENT_ID,
        observation_class=CASE_A_TARGET_NONZERO,
        observation_identity="a" * 64,
        observation_body_sha256="b" * 64,
        size_binding="1",
        freshness_allowed=False,
        freshness_reject_reason="STALE_POSITION_OBSERVATION",
        issuance_monotonic_ms=10_000,
        response_received_monotonic_ms=0,
        result_class="HTTP_200_OKX_0",
    )
    assert permit is None
    assert REASON_OBSERVATION_NOT_FRESH in reasons


def test_missing_observation_denies_issuance() -> None:
    permit, reasons = evaluate_runtime_permit_issuance_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET_INSTRUMENT_ID,
        observation_class=None,
        observation_identity=None,
        observation_body_sha256=None,
        size_binding=None,
        freshness_allowed=False,
        freshness_reject_reason="FRESHNESS_UNKNOWN",
        issuance_monotonic_ms=1,
        response_received_monotonic_ms=None,
        result_class=None,
    )
    assert permit is None
    assert reasons


def test_implementation_go_cannot_be_permit_owner_go() -> None:
    permit, reasons = evaluate_runtime_permit_issuance_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        instrument_id=TARGET_INSTRUMENT_ID,
        observation_class=CASE_A_TARGET_NONZERO,
        observation_identity="a" * 64,
        observation_body_sha256="b" * 64,
        size_binding="1",
        freshness_allowed=True,
        freshness_reject_reason=None,
        issuance_monotonic_ms=10,
        response_received_monotonic_ms=0,
        result_class="HTTP_200_OKX_0",
        permit_owner_go=OWNER_GO,
    )
    assert permit is None
    assert "RUNTIME_PERMIT_IMPLEMENTATION_GO_FORBIDDEN_AS_PERMIT_OWNER_GO" in reasons


def test_no_post_in_recording_path(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=NONZERO_BODY)
    result = execute_authenticated_private_runtime_read_and_permit_issuance_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    assert all(call.method == "GET" for call in transport.calls)
    assert result["summary"]["POST_COUNT"] == 0
    assert result["summary"]["WRITE_REQUEST_COUNT"] == 0
    assert result["runtime_facts"]["ENDPOINTS_USED"] == [ENDPOINT]
