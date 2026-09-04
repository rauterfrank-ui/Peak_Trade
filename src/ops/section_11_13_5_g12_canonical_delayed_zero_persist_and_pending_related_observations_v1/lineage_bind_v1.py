"""Bind historical flatten lineage from already persisted first-party evidence.

Does not GET. Does not invent fill, acceptance, or timestamps.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.constants_v1 import (
    CL_ORD_ID,
    FLATTEN_EVIDENCE_DIR,
    FLATTEN_RECOVERY_DIR,
    IMMEDIATE_POST_ACTION_IDENTITY,
    PRE_OBSERVATION_IDENTITY,
    PRE_REQUEST_TIME_UTC,
    PROVEN_POS_ID,
    SUBMIT_TIME_UTC,
    TARGET_INSTRUMENT_ID_VALUE,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.contract_v1 import (
    G12CanonicalDelayedZeroPersistError,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.types_v1 import (
    FlattenLineageSlotV1,
    ObservationSlotV1,
)


def _load_json(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise G12CanonicalDelayedZeroPersistError(f"LINEAGE_FILE_MISSING:{path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise G12CanonicalDelayedZeroPersistError(f"LINEAGE_FILE_NOT_MAPPING:{path.name}")
    return payload


def _okx_ms_to_utc(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text:
        raise G12CanonicalDelayedZeroPersistError("FILL_TIME_MISSING")
    try:
        millis = int(text)
    except (TypeError, ValueError) as exc:
        raise G12CanonicalDelayedZeroPersistError("FILL_TIME_UNPARSEABLE") from exc
    parsed = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def bind_flatten_lineage_v1(*, repo_root: Path) -> FlattenLineageSlotV1:
    observations = _load_json(
        Path(repo_root) / FLATTEN_EVIDENCE_DIR / "OBSERVATIONS.sanitized.json"
    )
    post_action = _load_json(Path(repo_root) / FLATTEN_EVIDENCE_DIR / "POST_ACTION.sanitized.json")
    recovery = _load_json(Path(repo_root) / FLATTEN_RECOVERY_DIR / "RECOVERY_RECON.sanitized.json")
    obs_map = observations.get("OBSERVATIONS")
    if not isinstance(obs_map, Mapping):
        raise G12CanonicalDelayedZeroPersistError("FLATTEN_OBSERVATIONS_MISSING")
    pre = obs_map.get("GET_ACCOUNT_POSITIONS_PRE")
    if not isinstance(pre, Mapping):
        raise G12CanonicalDelayedZeroPersistError("PRE_OBSERVATION_MISSING")
    if str(pre.get("OBSERVATION_IDENTITY") or "") != PRE_OBSERVATION_IDENTITY:
        raise G12CanonicalDelayedZeroPersistError("PRE_OBSERVATION_IDENTITY_MISMATCH")
    if str(pre.get("REQUEST_TIME_UTC") or "") != PRE_REQUEST_TIME_UTC:
        raise G12CanonicalDelayedZeroPersistError("PRE_TIMESTAMP_MISMATCH")
    pre_payload = pre.get("REDACTED_PAYLOAD")
    if not isinstance(pre_payload, Mapping):
        raise G12CanonicalDelayedZeroPersistError("PRE_PAYLOAD_MISSING")
    post_pos = obs_map.get("GET_ACCOUNT_POSITIONS_POST")
    if not isinstance(post_pos, Mapping):
        raise G12CanonicalDelayedZeroPersistError("IMMEDIATE_POST_OBSERVATION_MISSING")
    if str(post_pos.get("OBSERVATION_IDENTITY") or "") != IMMEDIATE_POST_ACTION_IDENTITY:
        raise G12CanonicalDelayedZeroPersistError("IMMEDIATE_POST_IDENTITY_MISMATCH")

    submit = post_action.get("SUBMIT_RESULT")
    if not isinstance(submit, Mapping):
        raise G12CanonicalDelayedZeroPersistError("SUBMIT_RESULT_MISSING")
    if submit.get("venue_acceptance_proven") is not True:
        raise G12CanonicalDelayedZeroPersistError("VENUE_ACCEPTANCE_NOT_IN_LINEAGE")
    http_status = submit.get("http_status")
    receipt = post_action.get("GATE_RECEIPT")
    if not isinstance(receipt, Mapping):
        raise G12CanonicalDelayedZeroPersistError("GATE_RECEIPT_MISSING")
    request_body = receipt.get("request_body")
    if not isinstance(request_body, Mapping):
        raise G12CanonicalDelayedZeroPersistError("SUBMIT_BODY_MISSING")
    if str(request_body.get("clOrdId") or "") != CL_ORD_ID:
        raise G12CanonicalDelayedZeroPersistError("SUBMIT_CLORDID_MISMATCH")
    if str(request_body.get("instId") or "") != TARGET_INSTRUMENT_ID_VALUE:
        raise G12CanonicalDelayedZeroPersistError("SUBMIT_INSTID_MISMATCH")
    if str(request_body.get("ordType") or "").lower() != "limit":
        raise G12CanonicalDelayedZeroPersistError("SUBMIT_NOT_LIMIT")
    reduce_only_raw = request_body.get("reduceOnly")
    reduce_only = reduce_only_raw is True or str(reduce_only_raw).lower() == "true"
    if not reduce_only:
        raise G12CanonicalDelayedZeroPersistError("SUBMIT_NOT_REDUCE_ONLY")
    if str(post_action.get("OWNER_GO") or "") == "":
        raise G12CanonicalDelayedZeroPersistError("SUBMIT_OWNER_GO_MISSING")

    recovery_obs = recovery.get("OBSERVATIONS")
    if not isinstance(recovery_obs, Mapping):
        raise G12CanonicalDelayedZeroPersistError("RECOVERY_OBSERVATIONS_MISSING")
    fills = recovery_obs.get("GET_TRADE_FILLS_RECOVERY")
    if not isinstance(fills, Mapping):
        raise G12CanonicalDelayedZeroPersistError("RECOVERY_FILLS_MISSING")
    fills_payload = fills.get("REDACTED_PAYLOAD")
    if not isinstance(fills_payload, Mapping):
        raise G12CanonicalDelayedZeroPersistError("RECOVERY_FILLS_PAYLOAD_MISSING")
    fill_data = fills_payload.get("data")
    if not isinstance(fill_data, list):
        raise G12CanonicalDelayedZeroPersistError("RECOVERY_FILLS_DATA_MISSING")
    bound_fill: Mapping[str, Any] | None = None
    for row in fill_data:
        if isinstance(row, Mapping) and str(row.get("clOrdId") or "") == CL_ORD_ID:
            bound_fill = row
            break
    if bound_fill is None:
        raise G12CanonicalDelayedZeroPersistError("FLATTEN_FILL_CLORDID_NOT_FOUND")
    if str(bound_fill.get("instId") or "") != TARGET_INSTRUMENT_ID_VALUE:
        raise G12CanonicalDelayedZeroPersistError("FILL_INSTID_MISMATCH")
    fill_sz = str(bound_fill.get("fillSz") or "").strip()
    fill_side = str(bound_fill.get("side") or "").strip()
    if not fill_sz or not fill_side:
        raise G12CanonicalDelayedZeroPersistError("FILL_FIELDS_MISSING")
    fill_time_utc = _okx_ms_to_utc(bound_fill.get("fillTime"))

    pre_rows = pre_payload.get("data")
    if not isinstance(pre_rows, list) or not pre_rows:
        raise G12CanonicalDelayedZeroPersistError("PRE_DATA_MISSING")
    pre_row = pre_rows[0]
    if not isinstance(pre_row, Mapping):
        raise G12CanonicalDelayedZeroPersistError("PRE_ROW_NOT_MAPPING")
    if str(pre_row.get("posId") or "") != PROVEN_POS_ID:
        raise G12CanonicalDelayedZeroPersistError("PRE_POSID_MISMATCH")

    return FlattenLineageSlotV1(
        authorized=True,
        reduce_only=True,
        ord_type="limit",
        side=str(request_body.get("side") or ""),
        sz=str(request_body.get("sz") or ""),
        px=str(request_body.get("px") or ""),
        cl_ord_id=CL_ORD_ID,
        instrument_id=TARGET_INSTRUMENT_ID_VALUE,
        venue_accepted=True,
        submit_time_utc=SUBMIT_TIME_UTC,
        submit_http_status=int(http_status) if http_status is not None else None,
        pre_observation=ObservationSlotV1(
            endpoint=str(pre.get("ENDPOINT") or ""),
            observation_identity=PRE_OBSERVATION_IDENTITY,
            request_time_utc=PRE_REQUEST_TIME_UTC,
            payload=pre_payload,
            query={},
            body_sha256=str(pre.get("BODY_SHA256") or "") or None,
            http_status=int(pre.get("HTTP_STATUS") or 0) or None,
            venue_code=str(pre.get("VENUE_CODE") or "") or None,
        ),
        fill_cl_ord_id=CL_ORD_ID,
        fill_instrument_id=TARGET_INSTRUMENT_ID_VALUE,
        fill_side=fill_side,
        fill_sz=fill_sz,
        fill_px=str(bound_fill.get("fillPx") or "") or None,
        fill_time_utc=fill_time_utc,
        immediate_post_action_identity=IMMEDIATE_POST_ACTION_IDENTITY,
        proven_pos_id=PROVEN_POS_ID,
    )
