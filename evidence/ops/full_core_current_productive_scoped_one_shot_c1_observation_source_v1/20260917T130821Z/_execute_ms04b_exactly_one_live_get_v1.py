"""MS04B one-shot bound EH live GET. Not a standing owner. Not a cycle host.

OWNER_GO_SCOPE=MS04B_EXACTLY_ONE_BOUND_EH_LIVE_GET_ONLY
Does not dispatch EG, invoke V5, mint a permit, POST, or mutate source/docs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    DISPOSITION_PRESENT,
    GET_AUTH_REQUIRED,
    GET_BAR,
    GET_CONNECT_TIMEOUT_SECONDS,
    GET_HOST,
    GET_LIMIT,
    GET_MAX_REQUEST_COUNT,
    GET_METHOD,
    GET_PATH,
    GET_TIMEOUT_SECONDS,
    GET_TRANSPORT_CAPABILITY,
    GET_TRANSPORT_CLASS,
    INST_ID_BINDING_SOURCE,
    JOIN_SEAM_ID,
    LIVE_GET_EXECUTED,
    MS04A_CONTRACT_BOUND,
    MS04A_SLICE,
    MS04_AUTHORIZED,
    MS05_AUTHORIZED,
    OWNER,
    OWNER_GO,
    PERFORM_GET_DEFAULT,
    PRODUCER_AUTHORITY,
    RUNTIME_CYCLE_AUTHORIZED,
    bind_current_productive_scoped_one_shot_c1_public_candles_get_request_contract_v1,
    evaluate_current_productive_c1_observation_against_cursor_floor_v1,
    map_injected_candles_payload_to_current_productive_c1_observation_v1,
    resolve_current_productive_c1_cursor_floor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    CURSOR_LINEAGE_ID,
    CURSOR_SCHEMA_NAME,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)

REQUIRED_ORIGIN_MAIN_SHA = "c5b89ee7871b0026bff31fbf74be5134261d0fce"
EXPECTED_TRANSPORT_CLASS_NAME = "FullCoreProductiveReadOnlyGetTransportV1"
OWNER_GO_SCOPE = "MS04B_EXACTLY_ONE_BOUND_EH_LIVE_GET_ONLY"
PACK = Path(__file__).resolve().parent
REPO_ROOT = next(
    parent for parent in PACK.parents if (parent / "pyproject.toml").is_file()
)
ORIGIN_MAIN_SHA_PATH = PACK / "ORIGIN_MAIN_SHA.txt"
EH_RELPATH = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_scoped_one_shot_c1_observation_source_v1.py"
)
FORBIDDEN_EH_SNIPPETS = (
    "FullCoreProductiveReadOnlyGetTransportV1(",
    "trigger_current_productive_next_c1_and_exactly_one_cycle_v1",
    "execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1",
    "opener.open",
    "execute_network",
)


def _write(name: str, payload: object) -> Path:
    path = PACK / name
    if isinstance(payload, (bytes, bytearray)):
        path.write_bytes(bytes(payload))
    else:
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
    return path


def _fail(report: dict[str, object], *, reason: str) -> int:
    report["PRE_EXECUTION_GATE"] = "FAIL_CLOSED"
    report["LIVE_GET_EXECUTED"] = False
    report["GET_COUNT"] = 0
    report["EARLIEST_BLOCKER"] = reason
    report["FINAL_VERDICT"] = "MS04B_FAIL_CLOSED_GET_COUNT_0"
    _write("pre_execution_gate.json", report)
    _write("claims.json", report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True))
    return 2


def main() -> int:
    if not ORIGIN_MAIN_SHA_PATH.is_file():
        origin_main_sha = ""
        report = {
            "BASELINE_VALIDATION": False,
            "BASE_SHA": "",
            "GET_COUNT": 0,
            "LIVE_GET_EXECUTED": False,
        }
        return _fail(report, reason="ORIGIN_MAIN_SHA_SNAPSHOT_MISSING")
    origin_main_sha = ORIGIN_MAIN_SHA_PATH.read_text(encoding="utf-8").strip()
    eh_source = (REPO_ROOT / EH_RELPATH).read_text(encoding="utf-8")
    report: dict[str, object] = {
        "BASELINE_VALIDATION": origin_main_sha == REQUIRED_ORIGIN_MAIN_SHA,
        "BASE_SHA": origin_main_sha,
        "MINI_SLICE": "MS04B",
        "OWNER_GO_SCOPE": OWNER_GO_SCOPE,
        "EH_OWNER": OWNER,
        "EH_SEAM_OWNER_GO": OWNER_GO,
        "JOIN_SEAM_ID": JOIN_SEAM_ID,
        "PRODUCER_AUTHORITY": PRODUCER_AUTHORITY,
        "TRANSPORT_CAPABILITY": GET_TRANSPORT_CAPABILITY,
        "TRANSPORT_CLASS": GET_TRANSPORT_CLASS,
        "V5_INVOKED": False,
        "MS04A_SLICE": MS04A_SLICE,
        "MS04A_CONTRACT_BOUND": MS04A_CONTRACT_BOUND,
        "MS04_AUTHORIZED_STANDING": MS04_AUTHORIZED,
        "MS05_AUTHORIZED": MS05_AUTHORIZED,
        "PERFORM_GET_DEFAULT": PERFORM_GET_DEFAULT,
        "LIVE_GET_EXECUTED_STANDING_PIN": LIVE_GET_EXECUTED,
        "RUNTIME_CYCLE_AUTHORIZED": RUNTIME_CYCLE_AUTHORIZED,
        "AUTH_REQUIRED": GET_AUTH_REQUIRED,
        "MAX_REQUEST_COUNT": GET_MAX_REQUEST_COUNT,
        "EG_TRIGGER_EXECUTED": False,
        "RUNTIME_CYCLE_EXECUTED": False,
        "AUTONOMOUS_PROCESS_STARTED": False,
        "EXTERNAL_MUTATION_OCCURRED": False,
        "PERSISTENT_GET_ENABLEMENT_CHANGED": False,
        "PARALLEL_AUTHORITY_CREATED": False,
        "PROTECTED_SURFACES_CHANGED": False,
        "MS05_STARTED": False,
        "RAW_RESPONSE_MUTATED": False,
        "GET_COUNT": 0,
        "LIVE_GET_EXECUTED": False,
    }
    if origin_main_sha != REQUIRED_ORIGIN_MAIN_SHA:
        return _fail(report, reason="ORIGIN_MAIN_SHA_MISMATCH")
    if OWNER != (
        "ops.full_core_live_path_composition_root_v1."
        "current_productive_scoped_one_shot_c1_observation_source_v1"
    ):
        return _fail(report, reason="EH_OWNER_DRIFT")
    if PRODUCER_AUTHORITY != "ONE_SHOT_PUBLIC_1M_C1_OBSERVATION_ACQUISITION_ONLY":
        return _fail(report, reason="PRODUCER_AUTHORITY_DRIFT")
    if GET_TRANSPORT_CAPABILITY != EXPECTED_TRANSPORT_CLASS_NAME:
        return _fail(report, reason="TRANSPORT_CAPABILITY_DRIFT")
    if FullCoreProductiveReadOnlyGetTransportV1.__name__ != EXPECTED_TRANSPORT_CLASS_NAME:
        return _fail(report, reason="TRANSPORT_CLASS_MISSING")
    if MS04A_CONTRACT_BOUND is not True:
        return _fail(report, reason="MS04A_CONTRACT_NOT_BOUND")
    if PERFORM_GET_DEFAULT is not False:
        return _fail(report, reason="PERFORM_GET_DEFAULT_NOT_FALSE")
    if LIVE_GET_EXECUTED is not False:
        return _fail(report, reason="STANDING_LIVE_GET_PIN_NOT_FALSE")
    if RUNTIME_CYCLE_AUTHORIZED is not False:
        return _fail(report, reason="RUNTIME_CYCLE_AUTHORIZED_NOT_FALSE")
    if MS05_AUTHORIZED is not False:
        return _fail(report, reason="MS05_AUTHORIZED_NOT_FALSE")
    if GET_AUTH_REQUIRED is not False:
        return _fail(report, reason="AUTH_REQUIRED_NOT_FALSE")
    if GET_MAX_REQUEST_COUNT != 1:
        return _fail(report, reason="MAX_REQUEST_COUNT_NOT_1")
    if GET_METHOD != "GET" or GET_HOST != "eea.okx.com" or GET_PATH != "/api/v5/market/candles":
        return _fail(report, reason="MS04A_REQUEST_SHAPE_DRIFT")
    if GET_BAR != "1m" or GET_LIMIT != "100":
        return _fail(report, reason="MS04A_QUERY_SHAPE_DRIFT")
    if INST_ID_BINDING_SOURCE != "CURRENT_PRODUCTIVE_CURSOR_VENUE_NATIVE_ID":
        return _fail(report, reason="INST_ID_BINDING_SOURCE_DRIFT")
    for snippet in FORBIDDEN_EH_SNIPPETS:
        if snippet in eh_source:
            return _fail(report, reason=f"EH_SOURCE_FORBIDDEN_SNIPPET:{snippet}")

    cursor_store = PACK / "cursor_store_origin_main_snapshot"
    cursor_path = cursor_store / CURSOR_FILENAME
    if not cursor_path.is_file():
        return _fail(report, reason="ORIGIN_MAIN_CURSOR_SNAPSHOT_MISSING")
    origin_cursor_text = cursor_path.read_text(encoding="utf-8")
    _write("cursor_snapshot_origin_main.json", json.loads(origin_cursor_text))

    floor = resolve_current_productive_c1_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=cursor_store,
    )
    contract = bind_current_productive_scoped_one_shot_c1_public_candles_get_request_contract_v1(
        owner_go=OWNER_GO,
        cursor_store_root=cursor_store,
    )
    report.update(
        {
            "CURSOR_SCHEMA": CURSOR_SCHEMA_NAME,
            "CURSOR_LINEAGE_ID": CURSOR_LINEAGE_ID,
            "CURSOR_FLOOR_RESOLVE_DISPOSITION": floor.disposition,
            "CURSOR_FLOOR_PRESENCE": floor.presence,
            "CURSOR_FLOOR_VENUE_EVENT_TIME": floor.floor_venue_event_time,
            "CURSOR_FLOOR_REASON": floor.reason_code,
            "CONTRACT_DISPOSITION": contract.disposition,
            "CONTRACT_REASON": contract.reason_code,
            "REQUEST_METHOD": contract.method,
            "REQUEST_HOST": contract.host,
            "REQUEST_PATH": contract.path,
            "REQUEST_BAR": contract.bar,
            "REQUEST_LIMIT": contract.limit,
            "REQUEST_INST_ID": contract.inst_id,
            "REQUEST_ENDPOINT": contract.endpoint,
            "CONTRACT_GET_COUNT": contract.get_count,
        }
    )
    if floor.disposition != DISPOSITION_PRESENT or floor.floor_venue_event_time is None:
        return _fail(report, reason=floor.reason_code or "CURSOR_NOT_PRESENT_VALID")
    if contract.disposition != DISPOSITION_PRESENT or contract.get_count != 0:
        return _fail(report, reason=contract.reason_code or "REQUEST_CONTRACT_NOT_PRESENT")
    if contract.host != GET_HOST or contract.method != GET_METHOD or contract.path != GET_PATH:
        return _fail(report, reason="BOUND_REQUEST_NOT_MS04A_CONTRACT")
    if contract.bar != GET_BAR or contract.limit != GET_LIMIT:
        return _fail(report, reason="BOUND_QUERY_NOT_MS04A_CONTRACT")
    if contract.auth_required is not False or contract.max_request_count != 1:
        return _fail(report, reason="BOUND_CARDINALITY_OR_AUTH_DRIFT")
    if contract.transport_capability != GET_TRANSPORT_CAPABILITY:
        return _fail(report, reason="BOUND_TRANSPORT_DRIFT")
    if not contract.inst_id:
        return _fail(report, reason="CURSOR_VENUE_NATIVE_ID_MISSING")
    expected_endpoint = f"{GET_PATH}?instId={contract.inst_id}&bar={GET_BAR}&limit={GET_LIMIT}"
    if contract.endpoint != expected_endpoint:
        return _fail(report, reason="BOUND_ENDPOINT_DRIFT")
    cursor_payload = json.loads(origin_cursor_text)
    report["CURSOR_VENUE_NATIVE_ID"] = cursor_payload.get("venue_native_id")
    report["PRE_EXECUTION_GATE"] = "PASS"
    _write("pre_execution_gate.json", report)
    _write(
        "request_contract.json",
        {
            "host": contract.host,
            "method": contract.method,
            "path": contract.path,
            "inst_id": contract.inst_id,
            "bar": contract.bar,
            "limit": contract.limit,
            "auth_required": contract.auth_required,
            "max_request_count": contract.max_request_count,
            "timeout_seconds": contract.timeout_seconds,
            "connect_timeout_seconds": contract.connect_timeout_seconds,
            "endpoint": contract.endpoint,
            "transport_capability": contract.transport_capability,
            "transport_class": contract.transport_class,
            "inst_id_binding_source": contract.inst_id_binding_source,
            "limit_binding_source": contract.limit_binding_source,
            "get_count": contract.get_count,
            "SECRET_VALUES_INCLUDED": False,
        },
    )

    transport = FullCoreProductiveReadOnlyGetTransportV1(
        handle=None,
        timeout_seconds=GET_TIMEOUT_SECONDS,
        max_request_count=GET_MAX_REQUEST_COUNT,
    )
    result = transport.get(
        endpoint=contract.endpoint,
        auth_required=contract.auth_required,
        pretrade_decision_id=OWNER_GO_SCOPE,
    )
    raw_payload = result.payload
    _write("raw_response.json", raw_payload if raw_payload is not None else None)
    _write(
        "request_metadata.json",
        {
            "method": result.method,
            "host": GET_HOST,
            "path": GET_PATH,
            "endpoint": result.endpoint,
            "http_status": result.http_status,
            "auth_header_sent": result.auth_header_sent,
            "auth_required": contract.auth_required,
            "transport_class": result.transport_class,
            "venue_live_contact": result.venue_live_contact,
            "historical_reuse": result.historical_reuse,
            "error_class": result.error_class,
            "body_sha256": result.body_sha256,
            "get_performed": result.get_performed,
            "transport_request_count": transport.request_count,
            "timeout_seconds": GET_TIMEOUT_SECONDS,
            "connect_timeout_seconds": GET_CONNECT_TIMEOUT_SECONDS,
            "SECRET_VALUES_INCLUDED": False,
        },
    )
    report.update(
        {
            "LIVE_GET_EXECUTED": True,
            "GET_COUNT": transport.request_count,
            "HTTP_STATUS": result.http_status,
            "RAW_RESPONSE_EVIDENCE": str(PACK / "raw_response.json"),
            "TRANSPORT_ERROR_CLASS": result.error_class,
            "AUTH_HEADER_SENT": result.auth_header_sent,
            "BODY_SHA256": result.body_sha256,
            "GET_PERFORMED": result.get_performed,
        }
    )
    fail_closed_reason = ""
    if transport.request_count != 1:
        fail_closed_reason = "GET_COUNT_NOT_1"
    elif result.method != "GET":
        fail_closed_reason = "NON_GET_METHOD"
    elif result.auth_header_sent is not False:
        fail_closed_reason = "AUTH_HEADER_SENT"
    elif result.error_class:
        fail_closed_reason = f"TRANSPORT_ERROR:{result.error_class}"
    elif result.http_status != 200:
        fail_closed_reason = f"NON_2XX:{result.http_status}"
    elif not isinstance(raw_payload, dict):
        fail_closed_reason = "EMPTY_OR_MALFORMED_PAYLOAD"
    if fail_closed_reason:
        report.update(
            {
                "MS02_MAPPING_RESULT": "NOT_REACHED",
                "MS03_FLOOR_COMPARISON": "NOT_REACHED",
                "OBSERVATION_DISPOSITION": "FAIL_CLOSED",
                "EARLIEST_BLOCKER": fail_closed_reason,
                "FINAL_VERDICT": "MS04B_GET_EXECUTED_FAIL_CLOSED",
            }
        )
        _write("claims.json", report)
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True))
        return 1

    mapped = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=OWNER_GO,
        candles_payload=raw_payload,
        native_id=str(contract.inst_id),
    )
    observation = mapped.observation
    report.update(
        {
            "MS02_MAPPING_RESULT": mapped.disposition,
            "MS02_REASON_CODE": mapped.reason_code,
            "MS02_GET_COUNT": mapped.get_count,
            "OBSERVATION_NATIVE_ID": None if observation is None else observation.native_id,
            "OBSERVATION_BAR": None if observation is None else observation.bar,
            "OBSERVATION_VENUE_EVENT_TIME": (
                None if observation is None else observation.venue_event_time
            ),
            "OBSERVATION_FINALIZED": None if observation is None else observation.confirm,
        }
    )
    _write(
        "ms02_mapping.json",
        {
            "disposition": mapped.disposition,
            "reason_code": mapped.reason_code,
            "get_count": mapped.get_count,
            "observation": None
            if observation is None
            else {
                "venue_event_time": observation.venue_event_time,
                "confirm": observation.confirm,
                "native_id": observation.native_id,
                "bar": observation.bar,
            },
        },
    )
    if observation is None:
        report.update(
            {
                "MS03_FLOOR_COMPARISON": "NOT_REACHED",
                "OBSERVATION_DISPOSITION": mapped.disposition,
                "EARLIEST_BLOCKER": mapped.reason_code or "MS02_UNFINALIZED_OR_ABSENT",
                "FINAL_VERDICT": "MS04B_GET_EXECUTED_MS02_FAIL_CLOSED",
            }
        )
        _write("claims.json", report)
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True))
        return 1

    floor_eval = evaluate_current_productive_c1_observation_against_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=cursor_store,
        observation=observation,
    )
    incoming = float(observation.venue_event_time)
    floor_value = float(floor.floor_venue_event_time)
    if incoming > floor_value:
        comparison = "NEWER_THAN_FLOOR"
    elif incoming == floor_value:
        comparison = "EQUAL_TO_FLOOR"
    else:
        comparison = "OLDER_THAN_FLOOR"
    report.update(
        {
            "MS03_FLOOR_COMPARISON": comparison,
            "MS03_DISPOSITION": floor_eval.disposition,
            "MS03_REASON_CODE": floor_eval.reason_code,
            "MS03_GET_COUNT": floor_eval.get_count,
            "OBSERVATION_DISPOSITION": floor_eval.disposition,
            "EARLIEST_BLOCKER": floor_eval.reason_code or "",
            "FINAL_VERDICT": (
                "MS04B_EXACTLY_ONE_LIVE_GET_AND_OBSERVATION_EVIDENCE_CLOSED"
                if floor_eval.reason_code == ""
                else "MS04B_GET_EXECUTED_MS03_FAIL_CLOSED"
            ),
        }
    )
    _write(
        "ms03_floor_evaluation.json",
        {
            "disposition": floor_eval.disposition,
            "presence": floor_eval.presence,
            "floor_venue_event_time": floor_eval.floor_venue_event_time,
            "observation_venue_event_time": observation.venue_event_time,
            "comparison": comparison,
            "reason_code": floor_eval.reason_code,
            "get_count": floor_eval.get_count,
        },
    )
    _write("claims.json", report)
    names = [
        "claims.json",
        "cursor_snapshot_origin_main.json",
        "ms02_mapping.json",
        "ms03_floor_evaluation.json",
        "pre_execution_gate.json",
        "raw_response.json",
        "request_contract.json",
        "request_metadata.json",
    ]
    manifest_lines = []
    for name in names:
        digest = hashlib.sha256((PACK / name).read_bytes()).hexdigest()
        manifest_lines.append(f"{digest}  {name}")
    (PACK / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if report["FINAL_VERDICT"] == (
        "MS04B_EXACTLY_ONE_LIVE_GET_AND_OBSERVATION_EVIDENCE_CLOSED"
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
