"""Verify the gitignored delayed-zero capture against recorded identities.

Does not GET. Does not treat `.ops_local` as canonical SSOT. Extracts only
sanitized admissible fields for later governed persistence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.constants_v1 import (
    DELAYED_ZERO_REQUEST_PATH,
    HISTORY_REQUEST_PATH,
    OPS_LOCAL_CAPTURE_PATH,
    PROVEN_POS_ID,
    RECORDED_HISTORY_BODY_SHA256,
    RECORDED_HISTORY_OBSERVATION_IDENTITY,
    RECORDED_HISTORY_REQUEST_TIME_UTC,
    RECORDED_ZERO_BODY_SHA256,
    RECORDED_ZERO_OBSERVATION_IDENTITY,
    RECORDED_ZERO_REQUEST_TIME_UTC,
    TARGET_INSTRUMENT_ID_VALUE,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.contract_v1 import (
    G12CanonicalDelayedZeroPersistError,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.constants_v1 import (
    HISTORY_ENDPOINT,
    POSITIONS_ENDPOINT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
)

_HISTORY_ROW_ALLOWLIST = frozenset(
    {
        "cTime",
        "closeAvgPx",
        "closeTotalPos",
        "direction",
        "instId",
        "instType",
        "lever",
        "mgnMode",
        "openAvgPx",
        "pnl",
        "pnlRatio",
        "posId",
        "posSide",
        "type",
        "uTime",
        "uly",
    }
)
_ZERO_ROW_ALLOWLIST = frozenset(
    {
        "avgPx",
        "cTime",
        "ccy",
        "instId",
        "instType",
        "lever",
        "mgnMode",
        "mmr",
        "pos",
        "posId",
        "posSide",
        "uTime",
    }
)


def _require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise G12CanonicalDelayedZeroPersistError(f"{label}_NOT_MAPPING")
    return value


def _sanitize_row(row: Mapping[str, Any], allowlist: frozenset[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in dict(row).items():
        if str(key) not in allowlist:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            out[str(key)] = value
    return out


def _envelope(*, code: str, msg: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"code": code, "msg": msg, "data": rows}


def verify_local_delayed_zero_capture_v1(
    *,
    repo_root: Path,
    capture_path: Path | None = None,
) -> dict[str, Any]:
    path = capture_path or (Path(repo_root) / OPS_LOCAL_CAPTURE_PATH)
    if not path.is_file():
        raise G12CanonicalDelayedZeroPersistError("LOCAL_CAPTURE_MISSING")
    raw_bytes = path.read_bytes()
    capture_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise G12CanonicalDelayedZeroPersistError("LOCAL_CAPTURE_NOT_JSON") from exc
    capture = _require_mapping(payload, label="LOCAL_CAPTURE")
    if capture.get("HOST") != "eea.okx.com":
        raise G12CanonicalDelayedZeroPersistError("LOCAL_CAPTURE_HOST_MISMATCH")
    if capture.get("POST_USED") is True:
        raise G12CanonicalDelayedZeroPersistError("LOCAL_CAPTURE_POST_USED")
    if int(capture.get("WRITE_REQUEST_COUNT") or 0) != 0:
        raise G12CanonicalDelayedZeroPersistError("LOCAL_CAPTURE_WRITE_USED")
    if capture.get("EMPTY_DATA_IS_ZERO") is True:
        raise G12CanonicalDelayedZeroPersistError("LOCAL_CAPTURE_EMPTY_PROMOTED")
    if str(capture.get("TARGET_INSTRUMENT") or "") != TARGET_INSTRUMENT_ID_VALUE:
        raise G12CanonicalDelayedZeroPersistError("LOCAL_CAPTURE_INSTRUMENT_MISMATCH")

    history = _require_mapping(capture.get("STAGE_1"), label="HISTORY")
    delayed = _require_mapping(capture.get("STAGE_2"), label="DELAYED_ZERO")

    if str(history.get("ENDPOINT") or "") != HISTORY_REQUEST_PATH:
        raise G12CanonicalDelayedZeroPersistError("HISTORY_ENDPOINT_MISMATCH")
    if str(history.get("BODY_SHA256") or "") != RECORDED_HISTORY_BODY_SHA256:
        raise G12CanonicalDelayedZeroPersistError("HISTORY_BODY_SHA256_MISMATCH")
    if str(history.get("OBSERVATION_IDENTITY") or "") != RECORDED_HISTORY_OBSERVATION_IDENTITY:
        raise G12CanonicalDelayedZeroPersistError("HISTORY_OBSERVATION_IDENTITY_MISMATCH")
    if str(history.get("REQUEST_TIME_UTC") or "") != RECORDED_HISTORY_REQUEST_TIME_UTC:
        raise G12CanonicalDelayedZeroPersistError("HISTORY_TIMESTAMP_MISMATCH")
    if int(history.get("HTTP_STATUS") or 0) != 200:
        raise G12CanonicalDelayedZeroPersistError("HISTORY_HTTP_NOT_200")
    if str(history.get("VENUE_RESPONSE_CODE") or "") != "0":
        raise G12CanonicalDelayedZeroPersistError("HISTORY_VENUE_CODE_NOT_0")

    history_payload = _require_mapping(history.get("REDACTED_PAYLOAD"), label="HISTORY_PAYLOAD")
    history_data = history_payload.get("data")
    if not isinstance(history_data, list) or len(history_data) != 1:
        raise G12CanonicalDelayedZeroPersistError("HISTORY_ROW_COUNT_NOT_ONE")
    history_row = _require_mapping(history_data[0], label="HISTORY_ROW")
    if str(history_row.get("instId") or "") != TARGET_INSTRUMENT_ID_VALUE:
        raise G12CanonicalDelayedZeroPersistError("HISTORY_INSTID_MISMATCH")
    if str(history_row.get("posId") or "") != PROVEN_POS_ID:
        raise G12CanonicalDelayedZeroPersistError("HISTORY_POSID_MISMATCH")
    sanitized_history = _envelope(
        code=str(history_payload.get("code") or ""),
        msg=str(history_payload.get("msg") or ""),
        rows=[_sanitize_row(history_row, _HISTORY_ROW_ALLOWLIST)],
    )

    if str(delayed.get("ENDPOINT") or "") != DELAYED_ZERO_REQUEST_PATH:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_ENDPOINT_MISMATCH")
    if str(delayed.get("BODY_SHA256") or "") != RECORDED_ZERO_BODY_SHA256:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_BODY_SHA256_MISMATCH")
    if str(delayed.get("OBSERVATION_IDENTITY") or "") != RECORDED_ZERO_OBSERVATION_IDENTITY:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_OBSERVATION_IDENTITY_MISMATCH")
    if str(delayed.get("REQUEST_TIME_UTC") or "") != RECORDED_ZERO_REQUEST_TIME_UTC:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_TIMESTAMP_MISMATCH")
    if int(delayed.get("HTTP_STATUS") or 0) != 200:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_HTTP_NOT_200")
    if str(delayed.get("VENUE_RESPONSE_CODE") or "") != "0":
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_VENUE_CODE_NOT_0")
    if delayed.get("OBSERVATION_IDENTITY") == history.get("OBSERVATION_IDENTITY"):
        raise G12CanonicalDelayedZeroPersistError("HISTORY_AND_ZERO_IDENTITY_COLLAPSED")

    delayed_payload = _require_mapping(delayed.get("REDACTED_PAYLOAD"), label="DELAYED_PAYLOAD")
    delayed_data = delayed_payload.get("data")
    if not isinstance(delayed_data, list) or len(delayed_data) != 1:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_ROW_COUNT_NOT_ONE")
    delayed_row = _require_mapping(delayed_data[0], label="DELAYED_ROW")
    if str(delayed_row.get("instId") or "") != TARGET_INSTRUMENT_ID_VALUE:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_INSTID_MISMATCH")
    if str(delayed_row.get("posId") or "") != PROVEN_POS_ID:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_POSID_MISMATCH")
    if str(delayed_row.get("pos") or "").strip() != "0":
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_POS_NOT_EXPLICIT_ZERO")
    sanitized_delayed = _envelope(
        code=str(delayed_payload.get("code") or ""),
        msg=str(delayed_payload.get("msg") or ""),
        rows=[_sanitize_row(delayed_row, _ZERO_ROW_ALLOWLIST)],
    )
    classified = classify_target_position_state_v1(
        positions_payload=sanitized_delayed,
        instrument_id=TARGET_INSTRUMENT_ID_VALUE,
    )
    if classified.state != TARGET_POSITION_ZERO_PROVEN:
        raise G12CanonicalDelayedZeroPersistError("DELAYED_ZERO_CLASSIFIER_NOT_ZERO")

    redacted_history_sha = hashlib.sha256(
        json.dumps(sanitized_history, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    redacted_delayed_sha = hashlib.sha256(
        json.dumps(sanitized_delayed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "P5_SOURCE_LOCAL_CAPTURE_VERIFIED": True,
        "FORENSIC_LOCAL_CAPTURE_PATH": OPS_LOCAL_CAPTURE_PATH,
        "FORENSIC_LOCAL_CAPTURE_SHA256": capture_sha256,
        "FORENSIC_LOCAL_IS_NOT_CANONICAL": True,
        "ORIGINAL_WIRE_BODY_BYTES_AVAILABLE": False,
        "HISTORY": {
            "ENDPOINT": HISTORY_REQUEST_PATH,
            "ENDPOINT_PATH": HISTORY_ENDPOINT,
            "QUERY": {"instType": "FUTURES", "instId": TARGET_INSTRUMENT_ID_VALUE, "limit": "100"},
            "HTTP_STATUS": 200,
            "VENUE_CODE": "0",
            "VENUE_MSG": str(history_payload.get("msg") or ""),
            "REQUEST_TIME_UTC": RECORDED_HISTORY_REQUEST_TIME_UTC,
            "OBSERVATION_IDENTITY": RECORDED_HISTORY_OBSERVATION_IDENTITY,
            "BODY_SHA256": RECORDED_HISTORY_BODY_SHA256,
            "BODY_BYTES": int(history.get("BODY_BYTES") or 0),
            "DATA_ROW_COUNT": 1,
            "REDACTED_PAYLOAD": sanitized_history,
            "REDACTED_PAYLOAD_SHA256": redacted_history_sha,
            "EPISTEMIC_CLASS": "HISTORY_POSID_PROVEN_NOT_CURRENT_ZERO",
            "HISTORY_IS_NOT_TARGET_POSITION_ZERO_PROVEN": True,
            "TARGET_POS_ID": PROVEN_POS_ID,
        },
        "DELAYED_ZERO": {
            "ENDPOINT": DELAYED_ZERO_REQUEST_PATH,
            "ENDPOINT_PATH": POSITIONS_ENDPOINT,
            "QUERY": {"posId": PROVEN_POS_ID},
            "HTTP_STATUS": 200,
            "VENUE_CODE": "0",
            "VENUE_MSG": str(delayed_payload.get("msg") or ""),
            "REQUEST_TIME_UTC": RECORDED_ZERO_REQUEST_TIME_UTC,
            "OBSERVATION_IDENTITY": RECORDED_ZERO_OBSERVATION_IDENTITY,
            "BODY_SHA256": RECORDED_ZERO_BODY_SHA256,
            "BODY_BYTES": int(delayed.get("BODY_BYTES") or 0),
            "DATA_ROW_COUNT": 1,
            "REDACTED_PAYLOAD": sanitized_delayed,
            "REDACTED_PAYLOAD_SHA256": redacted_delayed_sha,
            "EPISTEMIC_CLASS": "DELAYED_POST_FLATTEN_EXPLICIT_POSID_ZERO_NOT_IMMEDIATE_POST_READBACK",
            "TARGET_POSITION_ZERO_WINDOW_PROVEN": True,
            "CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN": False,
            "CLASSIFIER_STATE": classified.state,
            "CLASSIFIER_REASON": classified.reason,
            "SIGNED_POS": classified.signed_pos,
            "POSID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS": True,
        },
        "P5_CANONICAL_PERSIST": "READY",
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID_VALUE,
        "P5_POSID": PROVEN_POS_ID,
    }
