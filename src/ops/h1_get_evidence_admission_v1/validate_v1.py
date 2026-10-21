"""Read-only admission of already captured GET evidence.

The validator never calls a venue, writes portfolio state, or emits a flat
authorization. ADMITTED requires six positive proofs. Anything missing or
contradictory is UNKNOWN_BLOCKED.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.h1_get_evidence_admission_v1.constants_v1 import (
    ACCOUNT_ENDPOINTS,
    AUTHORITY_EFFECT,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_FILLS,
    EXTERNAL_EFFECT_AUTHORIZED,
    FLAT_EMITTED,
    INSTRUMENT_SCOPED_ENDPOINTS,
    INVENTORY_ATTESTED_ROWS,
    INVENTORY_ATTESTED_ZERO,
    INVENTORY_UNPROVEN,
    POSITIVE_REASON_CODES,
    POST_ALLOWED,
    PRODUCTIVE_ACTIVATION,
    PRODUCTIVE_COMPLETENESS,
    REASON_ACCOUNT_IDENTITY_ABSENT,
    REASON_ACCOUNT_IDENTITY_MALFORMED,
    REASON_ACCOUNT_IDENTITY_MISMATCH,
    REASON_ACCOUNT_PARAMETER_ABSENT,
    REASON_ADMISSION_TIME_ABSENT,
    REASON_ADMISSION_WINDOW_ABSENT,
    REASON_CAPTURED_AT_ABSENT,
    REASON_DIGEST_ABSENT,
    REASON_DIGEST_MISMATCH,
    REASON_DUPLICATE_FILL_CONFLICT,
    REASON_DUPLICATE_RESPONSE,
    REASON_EMPTY_POSITIONS_WITHOUT_COMPLETENESS,
    REASON_FILL_TIMESTAMP_MALFORMED,
    REASON_FILL_TRADE_ID_ABSENT,
    REASON_FRESHNESS_WINDOW_ABSENT,
    REASON_INPUT_ABSENT,
    REASON_INPUT_MALFORMED,
    REASON_INSTRUMENT_ABSENT,
    REASON_INSTRUMENT_MALFORMED,
    REASON_INSTRUMENT_MISMATCH,
    REASON_INSTRUMENT_PARAMETER_ABSENT,
    REASON_LATE_FILL_OUTSIDE_WINDOW,
    REASON_MISSING_RESPONSE,
    REASON_PAGINATION_TERMINAL_ABSENT,
    REASON_PAGINATION_TERMINAL_SOURCE_ABSENT,
    REASON_RESPONSE_MALFORMED,
    REASON_STALE_EVIDENCE,
    REASON_TEMPORAL_INCONSISTENCY,
    REASON_VENUE_TIMESTAMP_ABSENT,
    REQUIRED_ENDPOINTS,
    STATUS_ADMITTED,
    STATUS_UNKNOWN_BLOCKED,
    WRITER_HANDOFF,
    extract_identity_fields_from_payload_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.state_contracts_v1 import body_digest


@dataclass(frozen=True)
class CapturedGetResponseV1:
    endpoint: str
    request_params: Mapping[str, str] | None
    payload: Mapping[str, Any] | None
    body_digest: str | None
    captured_at_ms: int | None
    venue_timestamp_ms: int | None
    pagination_terminal: bool | None
    pagination_terminal_source: str | None
    admission_window_id: str | None


@dataclass(frozen=True)
class AdmissionParametersV1:
    bound_account_uid: str | None
    bound_instrument_id: str | None
    freshness_window_ms: int | None
    admission_time_ms: int | None
    admission_window_id: str | None
    admission_window_start_ms: int | None
    admission_window_end_ms: int | None


@dataclass(frozen=True)
class AdmissionResultV1:
    status: str
    reason_codes: tuple[str, ...]
    admission_digest: str
    position_inventory: str
    fill_fact_count: int
    writer_handoff: str
    flat_emitted: bool
    authority_effect: str
    post_allowed: bool
    external_effect_authorized: bool
    productive_completeness: bool
    productive_activation: bool


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str) or value == "" or value != value.strip():
        return None
    return value


def _json_scalar(value: object) -> object:
    if value is None or isinstance(value, str) or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    return "UNSERIALIZABLE"


def _checked_params(params: object) -> tuple[dict[str, str] | None, bool]:
    if params is None:
        return None, False
    if not isinstance(params, Mapping):
        return None, True
    checked: dict[str, str] = {}
    for key, value in params.items():
        if not isinstance(key, str) or not isinstance(value, str):
            return None, True
        checked[key] = value
    return checked, False


def _canonical_row(row: Mapping[str, Any]) -> str:
    return json.dumps(dict(row), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _response_material(response: CapturedGetResponseV1) -> dict[str, Any]:
    params, malformed = _checked_params(response.request_params)
    payload_digest = None
    if isinstance(response.payload, Mapping) and not malformed:
        payload_digest = body_digest(response.payload)
    return {
        "admission_window_id": _json_scalar(response.admission_window_id),
        "body_digest": _json_scalar(response.body_digest),
        "captured_at_ms": _json_scalar(response.captured_at_ms),
        "endpoint": _json_scalar(response.endpoint),
        "pagination_terminal": _json_scalar(response.pagination_terminal),
        "pagination_terminal_source": _json_scalar(response.pagination_terminal_source),
        "payload_digest": payload_digest,
        "request_params": params,
        "venue_timestamp_ms": _json_scalar(response.venue_timestamp_ms),
    }


def _admission_digest(
    *,
    status: str,
    reason_codes: tuple[str, ...],
    position_inventory: str,
    fill_fact_count: int,
    parameters: AdmissionParametersV1 | None,
    responses: tuple[object, ...] | None,
) -> str:
    response_material: list[dict[str, Any]] | None = None
    if isinstance(responses, tuple):
        response_material = []
        for item in responses:
            if isinstance(item, CapturedGetResponseV1):
                response_material.append(_response_material(item))
        response_material.sort(key=lambda item: str(item["endpoint"]))
    parameter_material: dict[str, Any] | None = None
    if isinstance(parameters, AdmissionParametersV1):
        parameter_material = {
            "admission_time_ms": _json_scalar(parameters.admission_time_ms),
            "admission_window_end_ms": _json_scalar(parameters.admission_window_end_ms),
            "admission_window_id": _json_scalar(parameters.admission_window_id),
            "admission_window_start_ms": _json_scalar(parameters.admission_window_start_ms),
            "bound_account_uid": _json_scalar(parameters.bound_account_uid),
            "bound_instrument_id": _json_scalar(parameters.bound_instrument_id),
            "freshness_window_ms": _json_scalar(parameters.freshness_window_ms),
        }
    material = {
        "authority_effect": AUTHORITY_EFFECT,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "fill_fact_count": fill_fact_count,
        "flat_emitted": FLAT_EMITTED,
        "parameters": parameter_material,
        "position_inventory": position_inventory,
        "post_allowed": POST_ALLOWED,
        "productive_activation": PRODUCTIVE_ACTIVATION,
        "productive_completeness": PRODUCTIVE_COMPLETENESS,
        "reason_codes": list(reason_codes),
        "responses": response_material,
        "status": status,
        "writer_handoff": WRITER_HANDOFF,
    }
    return body_digest(material)


def _finish(
    reasons: set[str],
    *,
    positions_empty: bool,
    positions_rows: bool,
    fill_fact_count: int,
    parameters: AdmissionParametersV1 | None,
    responses: tuple[object, ...] | None,
) -> AdmissionResultV1:
    if reasons:
        status = STATUS_UNKNOWN_BLOCKED
        reason_codes = tuple(sorted(reasons))
        inventory = INVENTORY_UNPROVEN
        admitted_fills = 0
    else:
        status = STATUS_ADMITTED
        reason_codes = POSITIVE_REASON_CODES
        if positions_empty:
            inventory = INVENTORY_ATTESTED_ZERO
        elif positions_rows:
            inventory = INVENTORY_ATTESTED_ROWS
        else:
            inventory = INVENTORY_UNPROVEN
            status = STATUS_UNKNOWN_BLOCKED
            reason_codes = (REASON_RESPONSE_MALFORMED,)
        admitted_fills = fill_fact_count if status == STATUS_ADMITTED else 0
    return AdmissionResultV1(
        status=status,
        reason_codes=reason_codes,
        admission_digest=_admission_digest(
            status=status,
            reason_codes=reason_codes,
            position_inventory=inventory,
            fill_fact_count=admitted_fills,
            parameters=parameters,
            responses=responses,
        ),
        position_inventory=inventory,
        fill_fact_count=admitted_fills,
        writer_handoff=WRITER_HANDOFF,
        flat_emitted=FLAT_EMITTED,
        authority_effect=AUTHORITY_EFFECT,
        post_allowed=POST_ALLOWED,
        external_effect_authorized=EXTERNAL_EFFECT_AUTHORIZED,
        productive_completeness=PRODUCTIVE_COMPLETENESS,
        productive_activation=PRODUCTIVE_ACTIVATION,
    )


def _index_responses(
    responses: tuple[object, ...], reasons: set[str]
) -> dict[str, CapturedGetResponseV1]:
    indexed: dict[str, CapturedGetResponseV1] = {}
    for item in responses:
        if not isinstance(item, CapturedGetResponseV1):
            reasons.add(REASON_RESPONSE_MALFORMED)
            continue
        if item.endpoint not in REQUIRED_ENDPOINTS:
            reasons.add(REASON_RESPONSE_MALFORMED)
            continue
        if item.endpoint in indexed:
            reasons.add(REASON_DUPLICATE_RESPONSE)
            continue
        indexed[item.endpoint] = item
    for endpoint in REQUIRED_ENDPOINTS:
        if endpoint not in indexed:
            reasons.add(REASON_MISSING_RESPONSE)
    return indexed


def _account_identity(
    indexed: dict[str, CapturedGetResponseV1],
    bound_account: str | None,
    reasons: set[str],
) -> None:
    collected: list[str] = []
    for endpoint in ACCOUNT_ENDPOINTS:
        response = indexed.get(endpoint)
        if response is None:
            reasons.add(REASON_ACCOUNT_IDENTITY_ABSENT)
            continue
        payload = response.payload
        if not isinstance(payload, Mapping):
            reasons.add(REASON_RESPONSE_MALFORMED)
            reasons.add(REASON_ACCOUNT_IDENTITY_ABSENT)
            continue
        uids, _inst_ids, _modes, malformed = extract_identity_fields_from_payload_v1(payload)
        if malformed:
            reasons.add(REASON_ACCOUNT_IDENTITY_MALFORMED)
        data = payload.get("data")
        if not isinstance(data, list):
            reasons.add(REASON_RESPONSE_MALFORMED)
            reasons.add(REASON_ACCOUNT_IDENTITY_ABSENT)
            continue
        if not uids:
            reasons.add(REASON_ACCOUNT_IDENTITY_ABSENT)
        collected.extend(uids)
    if bound_account is not None and collected and set(collected) != {bound_account}:
        reasons.add(REASON_ACCOUNT_IDENTITY_MISMATCH)


def _instrument_and_pagination(
    indexed: dict[str, CapturedGetResponseV1],
    bound_instrument: str | None,
    reasons: set[str],
) -> tuple[bool, bool]:
    positions_empty = False
    positions_rows = False
    for endpoint in INSTRUMENT_SCOPED_ENDPOINTS:
        response = indexed.get(endpoint)
        if response is None:
            reasons.add(REASON_INSTRUMENT_ABSENT)
            reasons.add(REASON_PAGINATION_TERMINAL_ABSENT)
            continue
        params, malformed_params = _checked_params(response.request_params)
        if malformed_params:
            reasons.add(REASON_RESPONSE_MALFORMED)
        if params is None or "instId" not in params:
            reasons.add(REASON_INSTRUMENT_ABSENT)
        elif bound_instrument is not None and params["instId"] != bound_instrument:
            reasons.add(REASON_INSTRUMENT_MISMATCH)
        if response.pagination_terminal is not True:
            reasons.add(REASON_PAGINATION_TERMINAL_ABSENT)
        elif _clean_text(response.pagination_terminal_source) is None:
            reasons.add(REASON_PAGINATION_TERMINAL_SOURCE_ABSENT)
        payload = response.payload
        if not isinstance(payload, Mapping):
            reasons.add(REASON_RESPONSE_MALFORMED)
            continue
        _uids, _inst_ids, _modes, malformed = extract_identity_fields_from_payload_v1(payload)
        if malformed:
            reasons.add(REASON_INSTRUMENT_MALFORMED)
        data = payload.get("data")
        if not isinstance(data, list):
            reasons.add(REASON_RESPONSE_MALFORMED)
            continue
        if endpoint == ENDPOINT_ACCOUNT_POSITIONS:
            positions_empty = data == []
            positions_rows = len(data) > 0
            if data == [] and response.pagination_terminal is not True:
                reasons.add(REASON_EMPTY_POSITIONS_WITHOUT_COMPLETENESS)
        for row in data:
            if not isinstance(row, Mapping) or "instId" not in row:
                reasons.add(REASON_INSTRUMENT_ABSENT)
                continue
            inst = row.get("instId")
            if not isinstance(inst, str) or inst == "" or inst != inst.strip():
                reasons.add(REASON_INSTRUMENT_MALFORMED)
            elif bound_instrument is not None and inst != bound_instrument:
                reasons.add(REASON_INSTRUMENT_MISMATCH)
    return positions_empty, positions_rows


def _freshness_and_time(
    response: CapturedGetResponseV1,
    parameters: AdmissionParametersV1,
    *,
    freshness_ok: bool,
    admission_time_ok: bool,
    bounds_ok: bool,
    window_id: str | None,
    reasons: set[str],
) -> None:
    venue = response.venue_timestamp_ms
    captured = response.captured_at_ms
    if not _is_int(venue):
        reasons.add(REASON_VENUE_TIMESTAMP_ABSENT)
    if not _is_int(captured):
        reasons.add(REASON_CAPTURED_AT_ABSENT)
    if freshness_ok and admission_time_ok and _is_int(venue):
        if abs(venue - parameters.admission_time_ms) > parameters.freshness_window_ms:
            reasons.add(REASON_STALE_EVIDENCE)
    if freshness_ok and admission_time_ok and _is_int(captured):
        if abs(captured - parameters.admission_time_ms) > parameters.freshness_window_ms:
            reasons.add(REASON_STALE_EVIDENCE)
    if bounds_ok and _is_int(venue):
        if (
            venue < parameters.admission_window_start_ms
            or venue > parameters.admission_window_end_ms
        ):
            reasons.add(REASON_TEMPORAL_INCONSISTENCY)
    if bounds_ok and _is_int(captured):
        if (
            captured < parameters.admission_window_start_ms
            or captured > parameters.admission_window_end_ms
        ):
            reasons.add(REASON_TEMPORAL_INCONSISTENCY)
    if window_id is not None and _clean_text(response.admission_window_id) != window_id:
        reasons.add(REASON_TEMPORAL_INCONSISTENCY)


def _digest(response: CapturedGetResponseV1, reasons: set[str]) -> None:
    payload = response.payload
    if not isinstance(payload, Mapping):
        reasons.add(REASON_DIGEST_MISMATCH)
        return
    supplied = response.body_digest
    if not isinstance(supplied, str) or supplied == "":
        reasons.add(REASON_DIGEST_ABSENT)
        return
    if body_digest(payload) != supplied:
        reasons.add(REASON_DIGEST_MISMATCH)


def _fills(
    indexed: dict[str, CapturedGetResponseV1],
    parameters: AdmissionParametersV1,
    *,
    freshness_ok: bool,
    admission_time_ok: bool,
    bounds_ok: bool,
    reasons: set[str],
) -> int:
    response = indexed.get(ENDPOINT_FILLS)
    if response is None or not isinstance(response.payload, Mapping):
        return 0
    data = response.payload.get("data")
    if not isinstance(data, list):
        return 0
    unique: dict[str, str] = {}
    for row in data:
        if not isinstance(row, Mapping):
            reasons.add(REASON_RESPONSE_MALFORMED)
            continue
        trade_id = row.get("tradeId")
        if not isinstance(trade_id, str) or trade_id == "" or trade_id != trade_id.strip():
            reasons.add(REASON_FILL_TRADE_ID_ABSENT)
            continue
        if "fillTime" in row:
            fill_time = row.get("fillTime")
            if not _is_int(fill_time):
                reasons.add(REASON_FILL_TIMESTAMP_MALFORMED)
            elif bounds_ok and (
                fill_time < parameters.admission_window_start_ms
                or fill_time > parameters.admission_window_end_ms
            ):
                reasons.add(REASON_LATE_FILL_OUTSIDE_WINDOW)
            elif (
                freshness_ok
                and admission_time_ok
                and abs(fill_time - parameters.admission_time_ms) > parameters.freshness_window_ms
            ):
                reasons.add(REASON_STALE_EVIDENCE)
        try:
            canonical = _canonical_row(row)
        except TypeError:
            reasons.add(REASON_RESPONSE_MALFORMED)
            continue
        previous = unique.get(trade_id)
        if previous is None:
            unique[trade_id] = canonical
        elif previous != canonical:
            reasons.add(REASON_DUPLICATE_FILL_CONFLICT)
    return len(unique)


def validate_get_evidence_admission_v1(
    responses: tuple[object, ...] | None,
    parameters: AdmissionParametersV1 | None,
) -> AdmissionResultV1:
    """Admit explicit captured evidence, or block it. No defaults are applied."""
    reasons: set[str] = set()
    if responses is None or parameters is None:
        reasons.add(REASON_INPUT_ABSENT)
        return _finish(
            reasons,
            positions_empty=False,
            positions_rows=False,
            fill_fact_count=0,
            parameters=parameters if isinstance(parameters, AdmissionParametersV1) else None,
            responses=responses if isinstance(responses, tuple) else None,
        )
    if not isinstance(responses, tuple) or not isinstance(parameters, AdmissionParametersV1):
        reasons.add(REASON_INPUT_MALFORMED)
        return _finish(
            reasons,
            positions_empty=False,
            positions_rows=False,
            fill_fact_count=0,
            parameters=parameters if isinstance(parameters, AdmissionParametersV1) else None,
            responses=responses if isinstance(responses, tuple) else None,
        )

    bound_account = _clean_text(parameters.bound_account_uid)
    if bound_account is None:
        reasons.add(REASON_ACCOUNT_PARAMETER_ABSENT)
    bound_instrument = _clean_text(parameters.bound_instrument_id)
    if bound_instrument is None:
        reasons.add(REASON_INSTRUMENT_PARAMETER_ABSENT)
    freshness_ok = _is_int(parameters.freshness_window_ms) and parameters.freshness_window_ms > 0
    if not freshness_ok:
        reasons.add(REASON_FRESHNESS_WINDOW_ABSENT)
    admission_time_ok = _is_int(parameters.admission_time_ms)
    if not admission_time_ok:
        reasons.add(REASON_ADMISSION_TIME_ABSENT)
    window_id = _clean_text(parameters.admission_window_id)
    if window_id is None:
        reasons.add(REASON_ADMISSION_WINDOW_ABSENT)
    start_ok = _is_int(parameters.admission_window_start_ms)
    end_ok = _is_int(parameters.admission_window_end_ms)
    if not start_ok or not end_ok:
        reasons.add(REASON_ADMISSION_WINDOW_ABSENT)
    bounds_ok = start_ok and end_ok
    if bounds_ok and parameters.admission_window_start_ms > parameters.admission_window_end_ms:
        reasons.add(REASON_TEMPORAL_INCONSISTENCY)
        bounds_ok = False

    indexed = _index_responses(responses, reasons)
    _account_identity(indexed, bound_account, reasons)
    positions_empty, positions_rows = _instrument_and_pagination(indexed, bound_instrument, reasons)
    for response in indexed.values():
        _freshness_and_time(
            response,
            parameters,
            freshness_ok=freshness_ok,
            admission_time_ok=admission_time_ok,
            bounds_ok=bounds_ok,
            window_id=window_id,
            reasons=reasons,
        )
        _digest(response, reasons)
    fill_fact_count = _fills(
        indexed,
        parameters,
        freshness_ok=freshness_ok,
        admission_time_ok=admission_time_ok,
        bounds_ok=bounds_ok,
        reasons=reasons,
    )
    return _finish(
        reasons,
        positions_empty=positions_empty,
        positions_rows=positions_rows,
        fill_fact_count=fill_fact_count,
        parameters=parameters,
        responses=responses,
    )
