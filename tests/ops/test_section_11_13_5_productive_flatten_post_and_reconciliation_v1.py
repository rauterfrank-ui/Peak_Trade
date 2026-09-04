"""Productive flatten POST and reconciliation tests. Recording transports only."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.runtime_permit_v1 import (
    runtime_permit_identity_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    RecordingAuthenticatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
    RecordingFakeCanaryTransportV1,
    sanitize_redirect_location_v1,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.constants_v1 import (
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_E_HTTP_OR_OKX_ERROR,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EMPTY_DATA_IS_ZERO_VALUE,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_AUTHORITY_BOUNDARY,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    RETRY_ALLOWED_VALUE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.execute_v1 import (
    ProductiveFlattenPostExecuteError,
    execute_productive_flatten_post_and_reconciliation_v1,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.persist_v1 import (
    assert_no_secrets_in_payload_v1,
)

TARGET = TARGET_INSTRUMENT_ID
NONZERO_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"1","posSide":"net","mgnMode":"cross"}]}'
)
ZERO_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"0","posSide":"net","mgnMode":"cross"}]}'
)
EMPTY_BODY = b'{"code":"0","msg":"","data":[]}'
PENDING_EMPTY = b'{"code":"0","msg":"","data":[]}'
PENDING_OPEN = b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404","ordId":"1"}]}'
FAIL_401_BODY = (
    b'{"code":"50110","msg":"Your IP 203.0.113.50 is not included in your API '
    b'key\'s IP whitelist.","data":[]}'
)
MALFORMED_BODY = b"not-json"
POST_ACCEPTED = (
    b'{"code":"0","data":[{"sCode":"0","ordId":"synthetic-flatten","clOrdId":"x","sz":"1"}]}'
)
POST_ACCEPTED_NOT_FILLED = (
    b'{"code":"0","data":[{"sCode":"1","sMsg":"pending","ordId":"synthetic-pending"}]}'
)


def _ticker_body(*, now_ms: int | None = None) -> bytes:
    ts = str(now_ms if now_ms is not None else int(time.time() * 1000))
    return (
        b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
        b'"bidPx":"0.7716","askPx":"0.7717","last":"0.7716","ts":"' + ts.encode("utf-8") + b'"}]}'
    )


@dataclass
class SequentialRecordingGetTransportV1:
    """Offline GET queue. Distinct pre/post position bodies. Never POSTs."""

    get_bodies: list[bytes]
    status_code: int = 200
    transport_class: str = TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    venue_live_contact: bool = False
    calls: list[LiveCanaryHttpRequestV1] = field(default_factory=list)
    raise_timeout: bool = False
    _idx: int = 0

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        self.calls.append(request)
        if request.method != "GET":
            raise AssertionError("GET_TRANSPORT_MUST_NOT_POST")
        if self.raise_timeout:
            raise TimeoutError("fake-timeout")
        if self._idx >= len(self.get_bodies):
            raise AssertionError("GET_BODY_QUEUE_EXHAUSTED")
        body = self.get_bodies[self._idx]
        self._idx += 1
        return LiveCanaryHttpResponseV1(
            status_code=int(self.status_code),
            body_bytes=body,
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method="GET",
            send_attempted=True,
            wire_body_sha256=hashlib.sha256(b"").hexdigest(),
            wire_body_byte_len=0,
            redirect_followed=False,
            redirect_status=None,
            redirect_location=sanitize_redirect_location_v1(None),
            response_headers_safe={},
        )


def _run(
    tmp_path: Path,
    get_transport: Any,
    *,
    post_transport: Any | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    return execute_productive_flatten_post_and_reconciliation_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        get_transport=get_transport,
        post_transport=post_transport,
        persist=persist,
    )


def _happy_get_queue() -> SequentialRecordingGetTransportV1:
    return SequentialRecordingGetTransportV1(
        get_bodies=[
            _ticker_body(),
            PENDING_EMPTY,
            NONZERO_BODY,
            ZERO_BODY,
            PENDING_EMPTY,
            EMPTY_BODY,
        ]
    )


def test_standing_flags_remain_fail_closed() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert EMPTY_DATA_IS_ZERO_VALUE is False
    assert RETRY_ALLOWED_VALUE is False
    assert TARGET_INSTRUMENT_ID == "SUI-USD_UM_XPERP-310404"
    assert THIS_SLICE == "11.13.5.PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION"
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "OWNER_MERGE_GO_THEN_SECTION_11_14_IF_FLATTEN_PROVEN"
    assert NEXT_AUTHORITY_BOUNDARY == "OWNER_MERGE_GO"
    assert NEXT_OWNER_GO_REQUIRED == "OWNER_MERGE_GO"
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert CLAIMS["PRODUCTIVE_FLATTEN_POST_AUTHORIZED"] is True
    assert CLAIMS["STANDING_LIVE_AUTHORIZED"] is False
    assert CLAIMS["RETRY_ALLOWED"] is False
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
    assert CLAIMS["MERGE_AUTHORIZED_BY_THIS_PERSIST"] is False


def test_exact_permit_binding_and_flatten_lineage(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        _happy_get_queue(),
        post_transport=RecordingAuthenticatedProductiveFlattenTransportV1(),
    )
    facts = result["runtime_facts"]
    summary = result["summary"]
    assert facts["OBSERVATION"]["POSITION_OBSERVATION_CLASS"] == CASE_A_TARGET_NONZERO
    assert facts["PERMIT_AUDIT"]["issued"] is True
    permit = facts["PERMIT_AUDIT"]["permit"]
    assert permit["instrument_id"] == TARGET
    assert permit["bound_origin_main_sha"] == EXPECTED_ORIGIN_MAIN_SHA
    assert permit["size_binding"]
    assert permit["observation_identity"]
    assert permit["observation_body_sha256"]
    digest = runtime_permit_identity_sha256_v1(permit)
    assert digest == facts["PERMIT_AUDIT"]["permit_identity_sha256"]
    replay = runtime_permit_identity_sha256_v1(permit)
    assert replay == digest
    assert summary["POST_USED"] is True
    assert summary["POST_RESULT"] == "POST_ACCEPTED"
    assert summary["RECONCILIATION_ATTEMPTED"] is True
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is True
    assert summary["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    assert facts["POST_ACTION_VERDICT"]["offline_contract_satisfied"] is True
    assert facts["POST_ACTION_VERDICT"]["post_pos_zero"] is True
    assert facts["POST_ACTION_VERDICT"]["pending_empty"] is True
    assert facts["POST_ACTION_VERDICT"]["no_flip"] is True
    assert (
        "PRODUCTIVE_LIVE_FLATTEN_SEQUENCE_NOT_EXECUTED"
        in facts["POST_ACTION_VERDICT"]["blocking_reasons"]
    )
    assert summary["RETRY_USED"] is False
    assert summary["LIVE_AUTHORIZED"] is False
    assert summary["CANARY_AUTHORIZED"] is False
    assert facts["WRITE_REQUEST_COUNT"] == 0
    assert facts["POST_COUNT"] == 1
    assert result["MANIFEST_VERIFY_RC"] == 0
    pack = Path(result["EVIDENCE_PACK"])
    for name in (
        "CENSUS.json",
        "LINEAGE.json",
        "ADJUDICATION.json",
        "SUMMARY.json",
        "claims.json",
        "OBSERVATIONS.sanitized.json",
        "RUNTIME_PERMIT.json",
        "POST_ACTION.sanitized.json",
        "MANIFEST.sha256",
    ):
        assert (pack / name).is_file()
    payload = json.loads((pack / "SUMMARY.json").read_text(encoding="utf-8"))
    assert_no_secrets_in_payload_v1(payload)


def test_already_zero_does_not_post(tmp_path: Path) -> None:
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[_ticker_body(), PENDING_EMPTY, ZERO_BODY]
    )
    result = _run(tmp_path, transport)
    facts = result["runtime_facts"]
    assert facts["OBSERVATION"]["POSITION_OBSERVATION_CLASS"] == CASE_B_TARGET_ZERO
    assert facts["POST_USED"] is False
    assert facts["POST_ATTEMPTED"] is False
    assert "POSITION_ALREADY_ZERO_NO_POST" in str(facts["FAIL_CLOSED_REASON"])
    assert result["summary"]["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False


def test_empty_data_is_not_zero_and_does_not_post(tmp_path: Path) -> None:
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[_ticker_body(), PENDING_EMPTY, EMPTY_BODY]
    )
    result = _run(tmp_path, transport)
    facts = result["runtime_facts"]
    assert facts["OBSERVATION"]["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
    assert facts["OBSERVATION"]["TARGET_POSITION_ZERO_PROVEN"] is False
    assert facts["POST_USED"] is False
    assert facts["PERMIT_AUDIT"]["issued"] is False


def test_stale_ticker_rejects_before_wire(tmp_path: Path) -> None:
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[_ticker_body(now_ms=1), PENDING_EMPTY, NONZERO_BODY]
    )
    result = _run(
        tmp_path,
        transport,
        post_transport=RecordingAuthenticatedProductiveFlattenTransportV1(),
    )
    facts = result["runtime_facts"]
    assert facts["POST_USED"] is False
    assert "PRE_SEND_GATE_DENIED" in str(facts["FAIL_CLOSED_REASON"] or "") or (
        facts["POST_RESULT"].startswith("POST_NOT_SENT")
    )


def test_open_order_conflict_rejects(tmp_path: Path) -> None:
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[_ticker_body(), PENDING_OPEN, NONZERO_BODY]
    )
    result = _run(
        tmp_path,
        transport,
        post_transport=RecordingAuthenticatedProductiveFlattenTransportV1(),
    )
    facts = result["runtime_facts"]
    assert facts["POST_USED"] is False
    assert "OPEN_ORDER_CONFLICT" in str(facts["FAIL_CLOSED_REASON"] or facts["POST_RESULT"])


def test_auth_failure_does_not_post(tmp_path: Path) -> None:
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[_ticker_body(), PENDING_EMPTY, FAIL_401_BODY],
        status_code=401,
    )
    result = _run(tmp_path, transport)
    facts = result["runtime_facts"]
    assert facts["OBSERVATION"]["POSITION_OBSERVATION_CLASS"] == CASE_E_HTTP_OR_OKX_ERROR
    assert facts["POST_USED"] is False


def test_malformed_response_does_not_post(tmp_path: Path) -> None:
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[_ticker_body(), PENDING_EMPTY, MALFORMED_BODY]
    )
    result = _run(tmp_path, transport)
    facts = result["runtime_facts"]
    assert facts["POST_USED"] is False
    assert facts["OBSERVATION"]["POSITION_OBSERVATION_CLASS"] == CASE_E_HTTP_OR_OKX_ERROR


def test_transport_failure_does_not_post(tmp_path: Path) -> None:
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[_ticker_body(), PENDING_EMPTY, NONZERO_BODY],
        raise_timeout=True,
    )
    result = _run(tmp_path, transport)
    facts = result["runtime_facts"]
    assert facts["POST_USED"] is False


def test_accepted_not_filled_is_not_flatten_proven(tmp_path: Path) -> None:
    post = RecordingAuthenticatedProductiveFlattenTransportV1(post_body=POST_ACCEPTED_NOT_FILLED)
    result = _run(tmp_path, _happy_get_queue(), post_transport=post)
    facts = result["runtime_facts"]
    assert facts["POST_USED"] is True
    assert (
        facts["POST_RESULT"] != "POST_ACCEPTED" or facts["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    )
    assert facts["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False


def test_contradictory_post_position_is_not_flatten_proven(tmp_path: Path) -> None:
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[
            _ticker_body(),
            PENDING_EMPTY,
            NONZERO_BODY,
            NONZERO_BODY,
            PENDING_EMPTY,
            EMPTY_BODY,
        ]
    )
    result = _run(
        tmp_path,
        transport,
        post_transport=RecordingAuthenticatedProductiveFlattenTransportV1(),
    )
    facts = result["runtime_facts"]
    assert facts["POST_USED"] is True
    assert facts["TARGET_POSITION_ZERO_PROVEN"] is False
    assert facts["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False


def test_no_second_submit_without_retry_authority(tmp_path: Path) -> None:
    post = RecordingAuthenticatedProductiveFlattenTransportV1()
    result = _run(tmp_path, _happy_get_queue(), post_transport=post)
    assert result["runtime_facts"]["POST_COUNT"] == 1
    assert len(post.calls) == 1
    with pytest.raises(Exception, match="DUPLICATE_POST_FORBIDDEN"):
        post.send(post.calls[0])


def test_wrong_owner_go_denied(tmp_path: Path) -> None:
    with pytest.raises(ProductiveFlattenPostExecuteError, match="OWNER_GO_MISMATCH"):
        execute_productive_flatten_post_and_reconciliation_v1(
            owner_go="SECTION_11_13_5_BOUNDED_ACTIVATION_OWNER_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            get_transport=RecordingFakeCanaryTransportV1(body=NONZERO_BODY),
        )


def test_get_client_cannot_be_flatten_post_transport(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
        AuthenticatedGatedProductiveFlattenTransportV1,
    )

    with pytest.raises(
        ProductiveFlattenPostExecuteError,
        match="FLATTEN_POST_TRANSPORT_FORBIDDEN_ON_GET_PATH",
    ):
        execute_productive_flatten_post_and_reconciliation_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            get_transport=AuthenticatedGatedProductiveFlattenTransportV1(),
        )


def test_recovery_empty_data_is_not_zero_even_with_fill(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.execute_v1 import (
        recovery_read_only_reobservation_v1,
    )

    fills = (
        b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
        b'"clOrdId":"ptokxeprod508b7b41508b7b4101","ordId":"1","side":"sell",'
        b'"fillSz":"1","fillPx":"0.7675"}]}'
    )
    transport = SequentialRecordingGetTransportV1(get_bodies=[EMPTY_BODY, PENDING_EMPTY, fills])
    result = recovery_read_only_reobservation_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        vault_file=None,
        evidence_pack=tmp_path / "primary",
        get_transport=transport,
    )
    assert result["OBSERVATION"]["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
    assert result["OBSERVATION"]["TARGET_POSITION_ZERO_PROVEN"] is False
    assert result["TARGET_POSITION_ZERO_PROVEN"] is False
    assert result["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    assert result["ORDER_FILLED_FOR_THIS_CLORDID"] is True
    assert result["PENDING_ROW_COUNT"] == 0
    assert result["POST_USED"] is False
    assert result["RETRY_USED"] is False
    assert result["MANIFEST_VERIFY_RC"] == 0


def test_wrong_origin_main_sha_denied(tmp_path: Path) -> None:
    with pytest.raises(ProductiveFlattenPostExecuteError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_productive_flatten_post_and_reconciliation_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path,
            get_transport=RecordingFakeCanaryTransportV1(body=NONZERO_BODY),
        )


def test_pending_order_after_post_is_not_flatten_proven(tmp_path: Path) -> None:
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[
            _ticker_body(),
            PENDING_EMPTY,
            NONZERO_BODY,
            NONZERO_BODY,
            PENDING_OPEN,
            EMPTY_BODY,
        ]
    )
    result = _run(
        tmp_path,
        transport,
        post_transport=RecordingAuthenticatedProductiveFlattenTransportV1(),
    )
    facts = result["runtime_facts"]
    assert facts["POST_USED"] is True
    assert facts["TARGET_POSITION_ZERO_PROVEN"] is False
    assert facts["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    assert facts["RETRY_USED"] is False


def test_partial_fill_is_not_flatten_proven(tmp_path: Path) -> None:
    partial_fills = (
        b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
        b'"clOrdId":"ptokxeprod508b7b41508b7b4101","side":"sell","fillSz":"0.5"}]}'
    )
    transport = SequentialRecordingGetTransportV1(
        get_bodies=[
            _ticker_body(),
            PENDING_EMPTY,
            NONZERO_BODY,
            NONZERO_BODY,
            PENDING_EMPTY,
            partial_fills,
        ]
    )
    result = _run(
        tmp_path,
        transport,
        post_transport=RecordingAuthenticatedProductiveFlattenTransportV1(),
    )
    facts = result["runtime_facts"]
    assert facts["POST_USED"] is True
    assert facts["TARGET_POSITION_ZERO_PROVEN"] is False
    assert facts["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    assert facts["RETRY_USED"] is False


def test_reduce_only_limit_body_does_not_reverse_or_over_close(tmp_path: Path) -> None:
    post = RecordingAuthenticatedProductiveFlattenTransportV1()
    result = _run(tmp_path, _happy_get_queue(), post_transport=post)
    assert result["runtime_facts"]["POST_USED"] is True
    assert len(post.calls) == 1
    body = json.loads(post.calls[0].body_text)
    assert body["instId"] == TARGET
    assert body["side"] == "sell"
    assert str(body["sz"]) == "1"
    assert body["reduceOnly"] is True
    assert body["ordType"] == "limit"
    assert body["tdMode"] == "cross"
    assert body.get("posSide") in (None, "net")
