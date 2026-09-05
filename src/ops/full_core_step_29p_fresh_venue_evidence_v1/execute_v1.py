"""Execute the STEP-29P fresh venue GET set. GET only. No POST. No wire send.

Constructs LiveCanaryHttpClientV1 as a reusable GET mechanism in this sibling
package. Full-Core composition root must not import this module's HTTP client.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    REQUIRED_GET_ITEM_SPECS,
    build_required_get_endpoint_v1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    REQUIRED_SETTLEMENT_CURRENCY,
    RISK_EQUITY_DIMENSION,
    persist_class_fields_v1,
    evaluate_step_29p_capital_risk_admissibility_v1,
    Step29PCapitalRiskAdmissibilityClaimV1,
)
from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionClaimV1,
    evaluate_capital_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_step_29p_fresh_venue_evidence_v1.constants_v1 import (
    AUTHORIZED_HOST,
    AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY,
    BOUND_ACCOUNT_IDENTITY,
    BOUND_INST_TYPE,
    BOUND_INSTRUMENT_ID,
    BOUND_SETTLEMENT_CURRENCY,
    BOUND_TD_MODE,
    CANARY_EXECUTE_AUTHORIZED,
    CAP_11_1_CONSTRUCTION_POLICY_LIFT_AUTHORIZED,
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_AUTHORIZED,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    EMPTY_DATA_IS_ZERO,
    ENDPOINT_PUBLIC_TICKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_ENDPOINTS,
    FORBIDDEN_HTTP_METHODS,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    POST_ALLOWED,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    THIS_SLICE,
    TICKER_CONSUMER,
    TICKER_IS_NOT_29P_PRICE_AUTHORITY,
    USER_AGENT_STEP_29P_FRESH_GET,
    WIRE_SEND_ALLOWED,
)
from src.ops.full_core_step_29p_fresh_venue_evidence_v1.persist_v1 import (
    persist_step_29p_fresh_venue_evidence_v1,
)
from src.ops.full_core_step_29p_fresh_venue_evidence_v1.requirement_matrix_v1 import (
    FRESH_EVIDENCE_REQUIREMENT_MATRIX,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)

_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


class Step29PFreshVenueEvidenceGetError(RuntimeError):
    """Fail-closed STEP-29P fresh GET violation."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _header_presence_v1(headers: dict[str, str]) -> dict[str, Any]:
    keys = {str(k).upper() for k in headers}
    return {
        "AUTH_KEY_HEADER_PRESENT": "OK-ACCESS-KEY" in keys,
        "AUTH_SIGN_HEADER_PRESENT": "OK-ACCESS-SIGN" in keys,
        "AUTH_TIMESTAMP_HEADER_PRESENT": "OK-ACCESS-TIMESTAMP" in keys,
        "AUTH_PASSPHRASE_HEADER_PRESENT": "OK-ACCESS-PASSPHRASE" in keys,
        "USER_AGENT": USER_AGENT_STEP_29P_FRESH_GET,
        "SECRET_VALUES_INCLUDED": False,
    }


def _assert_no_proxy_env_v1() -> None:
    present = [key for key in _PROXY_ENV_KEYS if str(os.environ.get(key) or "").strip()]
    if present:
        raise Step29PFreshVenueEvidenceGetError("HTTP_PROXY_FORBIDDEN")


def _assert_get_only_client(client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise Step29PFreshVenueEvidenceGetError("WRITE_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise Step29PFreshVenueEvidenceGetError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise Step29PFreshVenueEvidenceGetError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise Step29PFreshVenueEvidenceGetError("FLATTEN_SUBMIT_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise Step29PFreshVenueEvidenceGetError("TRANSFER_REQUEST_DETECTED")
    methods = list(client.counters.methods_used)
    if any(method in FORBIDDEN_HTTP_METHODS for method in methods):
        raise Step29PFreshVenueEvidenceGetError("FORBIDDEN_METHOD")
    if any(method != "GET" for method in methods):
        raise Step29PFreshVenueEvidenceGetError("NON_GET_METHOD_DETECTED")
    return counters


def _okx_code_msg(payload: Any) -> tuple[str | None, str | None]:
    if not isinstance(payload, dict):
        return None, None
    code = payload.get("code")
    msg = payload.get("msg")
    return (None if code is None else str(code), None if msg is None else str(msg)[:200])


def _extract_ticker_last_px(payload: Any) -> str:
    if not isinstance(payload, dict) or str(payload.get("code") or "") != "0":
        return ""
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return ""
    return str(data[0].get("last") or "").strip()


def _classify_positions(payload: Any, *, instrument_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"ROW_STATUS": "MALFORMED", "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO}
    code, _msg = _okx_code_msg(payload)
    if code != "0":
        return {"ROW_STATUS": "NONZERO_OKX_CODE", "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO}
    data = payload.get("data")
    if not isinstance(data, list):
        return {"ROW_STATUS": "MALFORMED", "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO}
    if len(data) == 0:
        return {
            "ROW_STATUS": "NOT_OBSERVED",
            "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO,
            "INTERPRETED_AS_ZERO": False,
        }
    matching = [
        row
        for row in data
        if isinstance(row, dict) and str(row.get("instId") or "") == instrument_id
    ]
    if not matching:
        return {"ROW_STATUS": "NOT_OBSERVED", "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO}
    return {
        "ROW_STATUS": "OBSERVED",
        "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO,
        "tdMode": str(matching[0].get("tdMode") or ""),
        "pos": str(matching[0].get("pos") or ""),
        "mgnMode": str(matching[0].get("mgnMode") or matching[0].get("tdMode") or ""),
    }


def _classify_balance_usdc(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"ROW_STATUS": "MALFORMED", "AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY": True}
    code, _msg = _okx_code_msg(payload)
    if code != "0":
        return {"ROW_STATUS": "NONZERO_OKX_CODE", "AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY": True}
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return {"ROW_STATUS": "NOT_OBSERVED", "AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY": True}
    details = data[0].get("details")
    if not isinstance(details, list):
        return {"ROW_STATUS": "NOT_OBSERVED", "AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY": True}
    matching = [
        row
        for row in details
        if isinstance(row, dict) and str(row.get("ccy") or "") == BOUND_SETTLEMENT_CURRENCY
    ]
    if not matching:
        return {
            "ROW_STATUS": "NOT_OBSERVED",
            "CURRENCY": BOUND_SETTLEMENT_CURRENCY,
            "AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY": AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY,
        }
    observed = str(matching[0].get("availEq") or "")
    return {
        "ROW_STATUS": "OBSERVED",
        "CURRENCY": BOUND_SETTLEMENT_CURRENCY,
        "observed_field": "details[ccy=USDC].availEq",
        "observed_availEq": observed,
        "AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY": AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY,
        "MAPPED_TO_STEP_29P_ACCOUNT_EQUITY": False,
        "EQUITY_DIMENSION": RISK_EQUITY_DIMENSION,
        "EQUITY_DIMENSION_BOUND": False,
    }


def _planned_gets(*, limit_px: str) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    seen_groups: set[str] = set()
    planned.append(
        {
            "item_id": "TICKER_LAST_FOR_MAX_SIZE_QUERY_PX",
            "endpoint": f"{ENDPOINT_PUBLIC_TICKER}?{urlencode({'instId': BOUND_INSTRUMENT_ID})}",
            "auth_required": False,
            "fetch_group": "ticker",
            "consumer": TICKER_CONSUMER,
        }
    )
    for spec in REQUIRED_GET_ITEM_SPECS:
        if spec.fetch_group in seen_groups:
            continue
        seen_groups.add(spec.fetch_group)
        planned.append(
            {
                "item_id": spec.item_id,
                "endpoint": build_required_get_endpoint_v1(
                    spec,
                    instrument_id=BOUND_INSTRUMENT_ID,
                    td_mode=BOUND_TD_MODE,
                    limit_px=limit_px,
                    inst_type=BOUND_INST_TYPE,
                ),
                "auth_required": spec.auth_required,
                "fetch_group": spec.fetch_group,
                "consumer": spec.item_id,
            }
        )
    return planned


def execute_step_29p_fresh_venue_evidence_gets_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    expected_account_identity: str = BOUND_ACCOUNT_IDENTITY,
) -> dict[str, Any]:
    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise Step29PFreshVenueEvidenceGetError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise Step29PFreshVenueEvidenceGetError("ORIGIN_MAIN_SHA_MISMATCH")
    if REUSED_REST_HOST != AUTHORIZED_HOST:
        raise Step29PFreshVenueEvidenceGetError("HOST_MISMATCH")
    _assert_no_proxy_env_v1()

    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise Step29PFreshVenueEvidenceGetError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise Step29PFreshVenueEvidenceGetError("PRODUCTIVE_WIRE_DISABLED")

    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    package_started = _utc_now_iso_v1()
    handle = None
    records: list[dict[str, Any]] = []
    ticker_px = ""
    gets_failed = 0
    gets_succeeded = 0
    try:
        if productive:
            backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REUSED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REUSED_CREDENTIAL_CLASS,
            )
        planned = _planned_gets(limit_px="")
        for item in planned:
            endpoint = str(item["endpoint"])
            path_only = endpoint.split("?", 1)[0]
            if path_only in FORBIDDEN_ENDPOINTS:
                raise Step29PFreshVenueEvidenceGetError("MUTATION_ENDPOINT_FORBIDDEN")
            if item["item_id"] != "TICKER_LAST_FOR_MAX_SIZE_QUERY_PX" and ticker_px:
                for spec in REQUIRED_GET_ITEM_SPECS:
                    if spec.item_id == item["item_id"] or spec.fetch_group == item["fetch_group"]:
                        endpoint = build_required_get_endpoint_v1(
                            spec,
                            instrument_id=BOUND_INSTRUMENT_ID,
                            td_mode=BOUND_TD_MODE,
                            limit_px=ticker_px,
                            inst_type=BOUND_INST_TYPE,
                        )
                        break
            url = f"{REUSED_REST_BASE}{endpoint}"
            parsed = urlparse(url)
            if parsed.hostname != AUTHORIZED_HOST:
                raise Step29PFreshVenueEvidenceGetError("HOST_MISMATCH")
            request_time = _utc_now_iso_v1()
            headers: dict[str, str] = {"User-Agent": USER_AGENT_STEP_29P_FRESH_GET}
            http_status: int | None = None
            body_bytes = b""
            get_error: str | None = None
            payload: Any = None
            try:
                if item["auth_required"] is True:
                    if handle is None and productive:
                        raise Step29PFreshVenueEvidenceGetError(
                            "PRIVATE_GET_REQUIRES_CREDENTIAL_HANDLE"
                        )
                    if handle is not None:
                        headers = build_okx_live_canary_auth_headers_v1(
                            handle=handle, url=url, method="GET"
                        )
                        headers["User-Agent"] = USER_AGENT_STEP_29P_FRESH_GET
                response = client.get(endpoint=endpoint, headers=headers)
                http_status = int(response.status_code)
                body_bytes = bytes(response.body_bytes)
                if response.method != "GET":
                    raise Step29PFreshVenueEvidenceGetError("NON_GET_RESPONSE")
                if bool(response.redirect_followed):
                    get_error = "REDIRECT_FOLLOWED"
                try:
                    payload = parse_json_object_v1(body_bytes)
                except (LiveCanaryHttpError, ValueError, json.JSONDecodeError):
                    payload = None
                    get_error = get_error or "MALFORMED_JSON"
            except LiveCanaryHttpError as exc:
                get_error = str(exc)[:200]
            except Step29PFreshVenueEvidenceGetError:
                raise
            code, msg = _okx_code_msg(payload)
            classification: dict[str, Any] = {}
            if item["fetch_group"] == "ticker":
                ticker_px = _extract_ticker_last_px(payload)
                classification = {
                    "ticker_last": ticker_px,
                    "TICKER_IS_NOT_29P_PRICE_AUTHORITY": TICKER_IS_NOT_29P_PRICE_AUTHORITY,
                    "CONSUMER": TICKER_CONSUMER,
                }
            elif item["fetch_group"] == "positions":
                classification = _classify_positions(payload, instrument_id=BOUND_INSTRUMENT_ID)
            elif item["fetch_group"] == "balance":
                classification = _classify_balance_usdc(payload)
            ok = (
                get_error is None
                and http_status == 200
                and code == "0"
                and isinstance(payload, dict)
            )
            if ok:
                gets_succeeded += 1
            else:
                gets_failed += 1
            records.append(
                {
                    "UTC": request_time,
                    "ENDPOINT": endpoint,
                    "HTTP_STATUS": http_status,
                    "OKX_CODE": code,
                    "OKX_MSG": msg,
                    "REQUEST_SCOPE": {
                        "instrument_id": BOUND_INSTRUMENT_ID,
                        "td_mode": BOUND_TD_MODE,
                        "inst_type": BOUND_INST_TYPE,
                        "currency": BOUND_SETTLEMENT_CURRENCY
                        if item["fetch_group"] == "balance"
                        else None,
                        "auth_required": item["auth_required"],
                        "SECRET_VALUES_INCLUDED": False,
                    },
                    "INSTRUMENT_ID": BOUND_INSTRUMENT_ID,
                    "CURRENCY_SCOPE": BOUND_SETTLEMENT_CURRENCY
                    if item["fetch_group"] == "balance"
                    else None,
                    "RAW_RESPONSE_SHA256": _sha256_hex(body_bytes) if body_bytes else "",
                    "ITEM_ID": item["item_id"],
                    "FETCH_GROUP": item["fetch_group"],
                    "CONSUMER": item["consumer"],
                    "FRESHNESS_CLASSIFICATION": "FRESH_GET_THIS_SLICE"
                    if ok
                    else "NOT_TRUSTED_OR_FAILED",
                    "AUTH_HEADER_PRESENCE": _header_presence_v1(headers),
                    "GET_ERROR": get_error,
                    "NORMALIZED": classification,
                    "SECRET_VALUES_INCLUDED": False,
                }
            )
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)

    counters = _assert_get_only_client(client)
    package_finished = _utc_now_iso_v1()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id

    observed_avail = ""
    for record in records:
        if record.get("FETCH_GROUP") == "balance":
            normalized = record.get("NORMALIZED") or {}
            if normalized.get("ROW_STATUS") == "OBSERVED":
                observed_avail = str(normalized.get("observed_availEq") or "")
    account = str(expected_account_identity or BOUND_ACCOUNT_IDENTITY)
    capital = evaluate_capital_admission_v1(
        claim=CapitalAdmissionClaimV1(
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            account_identity=account,
            instrument_id=BOUND_INSTRUMENT_ID,
            observed_capital_raw=observed_avail,
            observed_field_name="details.availEq",
            evidence_class="LIVE_TYPED",
            evidence_id=run_id,
        ),
        expected_account_identity=account,
        expected_instrument_id=BOUND_INSTRUMENT_ID,
        admission_context=ADMISSION_CONTEXT_LIVE,
    )
    claim = Step29PCapitalRiskAdmissibilityClaimV1(
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
        if gets_failed == 0 and gets_succeeded > 0
        else FreshPretradeGetStatusV1.MISSING.value,
        live_account_bound_status=LiveAccountBoundStatusV1.MISSING.value,
        expected_instrument_id=BOUND_INSTRUMENT_ID,
        observed_instrument_id=BOUND_INSTRUMENT_ID,
        expected_currency=REQUIRED_SETTLEMENT_CURRENCY,
        observed_currency=BOUND_SETTLEMENT_CURRENCY,
        equity_dimension="",
        typed_account_equity_raw="",
        typed_account_equity_source_field="",
        fresh_evidence_fetched=gets_succeeded > 0,
        fresh_evidence_validated=gets_failed == 0 and gets_succeeded > 0,
    )
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    persist_classes = persist_class_fields_v1(admissibility)
    snapshot = {
        "DOCUMENT_CLASS": "FULL_CORE_STEP_29P_FRESH_VENUE_EVIDENCE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_RUNTIME_EVIDENCE_NON_SSOT",
        "AUTHORITY": "NONE",
        "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
        "OWNER_GO": owned,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "PACKAGE_STARTED_UTC": package_started,
        "PACKAGE_FINISHED_UTC": package_finished,
        "HOST": REUSED_REST_HOST,
        "METHOD_ALLOWLIST": ["GET"],
        "REQUESTS": records,
        "COUNTERS": counters,
        "GETS_ATTEMPTED": len(records),
        "GETS_SUCCEEDED": gets_succeeded,
        "GETS_FAILED": gets_failed,
        "NETWORK_GET_TO_OKX_OCCURRED": productive and len(records) > 0,
        "MUTATING_NETWORK_CALL_OCCURRED": False,
        "ORDER_SUBMIT_OCCURRED": False,
        "WIRE_SEND_OCCURRED": False,
        "POST_PERFORMED": False,
        "CANARY_EXECUTE_AUTHORIZED": CANARY_EXECUTE_AUTHORIZED,
        "CAP_11_1_CONSTRUCTION_POLICY_LIFT_AUTHORIZED": (
            CAP_11_1_CONSTRUCTION_POLICY_LIFT_AUTHORIZED
        ),
        "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_AUTHORIZED": (
            CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_AUTHORIZED
        ),
        "POST_ALLOWED": POST_ALLOWED,
        "WIRE_SEND_ALLOWED": WIRE_SEND_ALLOWED,
        "SECRET_VALUES_INCLUDED": False,
        "TICKER_LAST_FOR_MAX_SIZE_QUERY": ticker_px,
        "TICKER_IS_NOT_29P_PRICE_AUTHORITY": TICKER_IS_NOT_29P_PRICE_AUTHORITY,
        "EMPTY_DATA_IS_ZERO": EMPTY_DATA_IS_ZERO,
        "AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY": AVAILEQ_IS_NOT_29P_EQUITY_AUTHORITY,
        "STEP_29P_RISK_ADMISSIBLE": admissibility.risk_admissible,
        "PERSIST_CLASSES": persist_classes,
        "ADMISSIBILITY_REASONS": list(admissibility.reason_codes),
        "CAPITAL_ADMISSION_STATUS": capital.evidence_status,
        "PRODUCTIVE": productive,
    }
    summary = {
        "DOCUMENT_CLASS": "FULL_CORE_STEP_29P_FRESH_VENUE_EVIDENCE_V1",
        "OWNER_GO": owned,
        "THIS_SLICE": THIS_SLICE,
        "HOST": REUSED_REST_HOST,
        "GETS_ATTEMPTED": len(records),
        "GETS_SUCCEEDED": gets_succeeded,
        "GETS_FAILED": gets_failed,
        "NETWORK_GET_TO_OKX_OCCURRED": productive and len(records) > 0,
        "MUTATING_NETWORK_CALL_OCCURRED": False,
        "ORDER_SUBMIT_OCCURRED": False,
        "WIRE_SEND_OCCURRED": False,
        "STEP_29P_RISK_ADMISSIBLE": admissibility.risk_admissible,
        "MISSING_REQUIRED_EVIDENCE": list(admissibility.reason_codes),
        "PERSIST_CLASSES": persist_classes,
        "SECRET_VALUES_INCLUDED": False,
    }
    claims = {
        "FRESH_EVIDENCE_FETCHED": persist_classes["FRESH_EVIDENCE_FETCHED"],
        "FRESH_EVIDENCE_VALIDATED": persist_classes["FRESH_EVIDENCE_VALIDATED"],
        "CAPITAL_EVIDENCE_COMPLETE": persist_classes["CAPITAL_EVIDENCE_COMPLETE"],
        "STEP_29P_RISK_ADMISSIBLE": persist_classes["STEP_29P_RISK_ADMISSIBLE"],
        "STANDING_GATES_SATISFIED": persist_classes["STANDING_GATES_SATISFIED"],
        "PORT_CONSTRUCTION_AUTHORIZED": persist_classes["PORT_CONSTRUCTION_AUTHORIZED"],
        "PORT_CONSTRUCTED": persist_classes["PORT_CONSTRUCTED"],
        "WIRE_SEND_AUTHORIZED": persist_classes["WIRE_SEND_AUTHORIZED"],
        "WIRE_SEND_EXECUTED": persist_classes["WIRE_SEND_EXECUTED"],
        "SECRET_VALUES_INCLUDED": False,
    }
    persisted = persist_step_29p_fresh_venue_evidence_v1(
        pack=pack,
        snapshot=snapshot,
        summary=summary,
        claims=claims,
        requirement_matrix={"rows": list(FRESH_EVIDENCE_REQUIREMENT_MATRIX)},
        gets={"REQUESTS": records, "SECRET_VALUES_INCLUDED": False},
    )
    return {
        **persisted,
        "summary": summary,
        "snapshot": snapshot,
        "admissibility": admissibility,
        "NETWORK_GET_TO_OKX_OCCURRED": productive and len(records) > 0,
        "MUTATING_NETWORK_CALL_OCCURRED": False,
    }
