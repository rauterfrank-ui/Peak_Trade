"""CURRENT_PRODUCTIVE Live Account Bound and STEP-29P instrument scope v1.

Consumes Owner-GO
CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_TO_FIRST_REAL_BLOCKER_V1.

Binds STEP-29P to an explicit Cap-2.4 BoundInstrument (exactly one selected
future, MAX_POSITIONS=1) and evaluates LIVE_ACCOUNT_BOUND through the
existing typed seam. Does not import canary DEFAULT_INSTRUMENT_ID as
Full-Core instrument authority. Does not re-select. No POST. No Live
enable/arm.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionClaimV1,
    evaluate_capital_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_ENABLED,
    NUMERIC_EQUITY_TTL_SECONDS,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_SOURCE_OBSERVED_VENUE,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_account_bound_v1 import (
    LIVE_ACCOUNT_BOUND_AUTHORITY,
    evaluate_live_account_bound_v1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
    persist_class_fields_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED,
    CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
    CURRENT_PRODUCTIVE_29P_LAB_AND_INSTRUMENT_SCOPE_ADAPTER_CREATED,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
    CURRENT_PRODUCTIVE_P01_POLICY_DECISION,
    CURRENT_PRODUCTIVE_U01_GET_ENDPOINT,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
    PRODUCER_IDENTITY,
    REQUIRED_TD_MODE,
    CurrentProductiveUsdcFreeMarginObservationV1,
    bind_step_29p_typed_equity_from_risk_capital_v1,
    produce_current_productive_29p_risk_capital_v1,
    reject_direct_avail_eq_29p_claim_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_p01_policy_v1 import (
    AUTHORIZED_INPUTS,
    EVIDENCE_REF,
    POLICY_FORMULA,
    bind_current_productive_p01_policy_fact_v1,
    current_productive_p01_policy_pins_v1,
    evaluate_current_productive_p01_policy_v1,
    reject_missing_as_does_not_apply_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
    extract_raw_acct_lv_from_account_config_payload_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    AVAILABLE_MARGIN_OUTPUT_DOMAIN,
    AVAILABLE_MARGIN_REQUIRED_CCY,
    AVAILABLE_MARGIN_REQUIRED_TD_MODE,
    LiveCanaryAvailableMarginObservationError,
    account_balance_query_path_v1,
    acquire_fresh_available_margin_observation_from_payload_v1,
    validate_fresh_available_margin_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
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
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    SELECTED_FUTURE_COUNT,
    SELECTION_AUTHORITY_OWNER,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

OWNER_GO = (
    "CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_TO_FIRST_REAL_BLOCKER_V1"
)
PIN_OWNER_GO = "OWNER_GO_REQUIRED_TO_BIND_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1"
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, PIN_OWNER_GO, f"OWNER_GO_{OWNER_GO}"})
EXPECTED_ORIGIN_MAIN_SHA = "4f38931f050df06471c9b71fa0174eca13a2bb48"
THIS_SLICE = (
    "11.2.1.CY.FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P"
)
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
EVIDENCE_DIRNAME = "full_core_current_productive_live_account_bound_and_instrument_scope_for_29p_v1"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_live_account_bound_and_instrument_scope_for_29p_v1/"
    "20260915T143000Z"
)
AUTHORIZED_HOST = "eea.okx.com"
REUSED_REST_BASE = f"https://{AUTHORIZED_HOST}"
USER_AGENT = "PeakTrade-FullCore-CY-LAB-InstrumentScope-29P/1"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_RETRIES = 0
MAX_NETWORK_REQUEST_COUNT = 2
FORBIDDEN_HTTP_METHODS = ("POST", "PUT", "DELETE", "PATCH")
FORBIDDEN_ENDPOINTS = (
    "/api/v5/trade/order",
    "/api/v5/trade/cancel-order",
    "/api/v5/asset/withdrawal",
    "/api/v5/asset/transfer",
)
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)
_REPO_ROOT = Path(__file__).resolve().parents[3]
INSTRUMENT_SCOPE_AUTHORITY = SELECTION_AUTHORITY_OWNER
LAB_AUTHORITY = LIVE_ACCOUNT_BOUND_AUTHORITY
_REQUIRED_BOUND_FIELDS = (
    "instrument_id",
    "venue_native_id",
    "ranking_snapshot_id",
    "ranking_integrity_digest",
    "universe_snapshot_id",
    "selection_id",
    "selection_integrity_digest",
)


class CurrentProductiveLabInstrumentScopeError(RuntimeError):
    """Fail-closed CURRENT_PRODUCTIVE LAB / instrument-scope violation."""


@dataclass(frozen=True)
class CurrentProductiveLabInstrumentScopeResultV1:
    store_root: str
    live_account_bound_status: str
    instrument_scope_status: str
    selected_instrument_id: str
    single_selected_future_proven: str
    max_positions_effective: str
    u01_status: str
    p01_status: str
    fresh_usdc_availeq_status: str
    risk_capital_mint_status: str
    step_29p_risk_admissible: str
    first_real_blocker: str
    blocker_class: str
    post_count: str
    evidence_manifest: str
    manifest_verify_rc: int


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for marker in SECRET_MARKERS:
        if marker in blob:
            raise CurrentProductiveLabInstrumentScopeError("SECRET_LEAK_FORBIDDEN")


def _assert_no_proxy_env_v1() -> None:
    present = [key for key in _PROXY_ENV_KEYS if str(os.environ.get(key) or "").strip()]
    if present:
        raise CurrentProductiveLabInstrumentScopeError("HTTP_PROXY_FORBIDDEN")


def _okx_code_msg(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, dict):
        return "", ""
    return str(payload.get("code") or ""), str(payload.get("msg") or "")[:200]


def _age_seconds(*, observed_at_as_of: str, now_iso: str) -> str:
    try:
        observed = datetime.strptime(observed_at_as_of, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        now = datetime.strptime(now_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return "UNPARSEABLE"
    delta = (now - observed).total_seconds()
    if delta < 0:
        return "NEGATIVE"
    return format(Decimal(str(int(delta))), "f")


def _extract_uid(payload: Mapping[str, Any] | None) -> str:
    if not isinstance(payload, Mapping):
        return ""
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], Mapping):
        return ""
    uid = data[0].get("uid")
    if uid is None or isinstance(uid, bool):
        return ""
    if isinstance(uid, int):
        return str(uid)
    if isinstance(uid, str):
        return uid.strip()
    return ""


def _header_presence_v1(headers: dict[str, str]) -> dict[str, Any]:
    keys = {str(k).upper() for k in headers}
    return {
        "AUTH_KEY_HEADER_PRESENT": "OK-ACCESS-KEY" in keys,
        "AUTH_SIGN_HEADER_PRESENT": "OK-ACCESS-SIGN" in keys,
        "AUTH_TIMESTAMP_HEADER_PRESENT": "OK-ACCESS-TIMESTAMP" in keys,
        "AUTH_PP_HEADER_PRESENT": "OK-ACCESS-PASSPHRASE" in keys,
        "USER_AGENT": USER_AGENT,
        "SECRET_VALUES_INCLUDED": False,
    }


def _assert_get_only_client(client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise CurrentProductiveLabInstrumentScopeError("WRITE_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise CurrentProductiveLabInstrumentScopeError("ORDER_REQUEST_DETECTED")
    methods = tuple(counters.get("methods_used") or ())
    if any(method in FORBIDDEN_HTTP_METHODS for method in methods):
        raise CurrentProductiveLabInstrumentScopeError("FORBIDDEN_HTTP_METHOD")
    endpoints = tuple(counters.get("endpoints_used") or ())
    for endpoint in endpoints:
        path = urlparse(str(endpoint)).path or str(endpoint)
        if path in FORBIDDEN_ENDPOINTS:
            raise CurrentProductiveLabInstrumentScopeError("FORBIDDEN_ENDPOINT")
    return counters


def require_current_productive_29p_bound_instrument_v1(
    bound_instrument: BoundInstrumentV1 | None,
) -> BoundInstrumentV1:
    if CURRENT_PRODUCTIVE_29P_LAB_AND_INSTRUMENT_SCOPE_ADAPTER_CREATED is not True:
        raise CurrentProductiveLabInstrumentScopeError("LAB_INSTRUMENT_ADAPTER_NOT_CREATED")
    if CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED is not False:
        raise CurrentProductiveLabInstrumentScopeError("CANARY_INSTRUMENT_AUTHORITY_IMPORTED")
    if bound_instrument is None:
        raise CurrentProductiveLabInstrumentScopeError("BOUND_INSTRUMENT_MISSING")
    if not isinstance(bound_instrument, BoundInstrumentV1):
        raise CurrentProductiveLabInstrumentScopeError("BOUND_INSTRUMENT_TYPE_INVALID")
    payload = bound_instrument.to_dict()
    for field in _REQUIRED_BOUND_FIELDS:
        raw = str(payload.get(field) or "").strip()
        if raw == "" or raw != str(payload.get(field) or ""):
            raise CurrentProductiveLabInstrumentScopeError(
                f"BOUND_INSTRUMENT_FIELD_MISSING:{field}"
            )
    if int(bound_instrument.selected_future_count) != SELECTED_FUTURE_COUNT:
        raise CurrentProductiveLabInstrumentScopeError("SELECTED_FUTURE_COUNT_NOT_ONE")
    if int(bound_instrument.max_positions_effective) != MAX_POSITIONS_EFFECTIVE:
        raise CurrentProductiveLabInstrumentScopeError("MAX_POSITIONS_NOT_ONE")
    if str(bound_instrument.selection_state) != STATE_SELECTED_ACTIVE:
        raise CurrentProductiveLabInstrumentScopeError("BOUND_INSTRUMENT_NOT_SELECTED_ACTIVE")
    return bound_instrument


def expected_venue_instrument_id_v1(bound_instrument: BoundInstrumentV1) -> str:
    return str(bound_instrument.venue_native_id)


def _signed_get(
    *,
    client: LiveCanaryHttpClientV1,
    endpoint: str,
    productive: bool,
    handle: Any,
) -> tuple[int | None, bytes, dict[str, str], str, Any, str | None]:
    request_time = _utc_now_iso_v1()
    url = f"{REUSED_REST_BASE}{endpoint}"
    headers = {"User-Agent": USER_AGENT}
    if handle is not None:
        headers = build_okx_live_canary_auth_headers_v1(handle=handle, url=url, method="GET")
        headers["User-Agent"] = USER_AGENT
    elif productive:
        raise CurrentProductiveLabInstrumentScopeError("PRIVATE_GET_REQUIRES_CREDENTIAL_HANDLE")
    try:
        response = client.get(endpoint=endpoint, headers=headers)
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        if response.method != "GET":
            raise CurrentProductiveLabInstrumentScopeError("NON_GET_RESPONSE")
        if bool(response.redirect_followed):
            return http_status, body_bytes, headers, request_time, None, "REDIRECT_FOLLOWED"
        payload = parse_json_object_v1(body_bytes)
        return http_status, body_bytes, headers, request_time, payload, None
    except LiveCanaryHttpError as exc:
        return None, b"", headers, request_time, None, str(exc)[:200]
    except (ValueError, json.JSONDecodeError):
        return None, b"", headers, request_time, None, "MALFORMED_JSON"


def execute_current_productive_lab_and_instrument_scope_for_29p_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    bound_instrument: BoundInstrumentV1 | None,
    evidence_root: Path | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE,
    execute_get: bool = False,
) -> CurrentProductiveLabInstrumentScopeResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise CurrentProductiveLabInstrumentScopeError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveLabInstrumentScopeError("ORIGIN_MAIN_SHA_MISMATCH")
    if execute_get is not True:
        raise CurrentProductiveLabInstrumentScopeError("EXECUTE_GET_FLAG_REQUIRED")
    if WIRE_SEND_PERMITTED is not False:
        raise CurrentProductiveLabInstrumentScopeError("STANDING_LIVE_GATES_MUST_REMAIN_FALSE")
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveLabInstrumentScopeError("SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED")
    if P01_RUNTIME_INSTANCE_PRESENT is not False:
        raise CurrentProductiveLabInstrumentScopeError(
            "RECONSTRUCTION_P01_RUNTIME_INSTANCE_MUST_REMAIN_FALSE"
        )
    if CURRENT_PRODUCTIVE_U01_GET_ENDPOINT != "/api/v5/account/config":
        raise CurrentProductiveLabInstrumentScopeError("U01_ENDPOINT_DRIFT")
    if CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT != "/api/v5/account/balance":
        raise CurrentProductiveLabInstrumentScopeError("BALANCE_ENDPOINT_DRIFT")
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise CurrentProductiveLabInstrumentScopeError("HOST_MISMATCH")
    reject_direct_avail_eq_29p_claim_v1(claimed="false")
    missing = reject_missing_as_does_not_apply_v1()
    p01_decision = evaluate_current_productive_p01_policy_v1()
    if p01_decision.decision_state != CURRENT_PRODUCTIVE_P01_POLICY_DECISION:
        raise CurrentProductiveLabInstrumentScopeError("P01_POLICY_MUST_BE_DOES_NOT_APPLY")
    if missing.decision_state == CURRENT_PRODUCTIVE_P01_POLICY_DECISION:
        raise CurrentProductiveLabInstrumentScopeError("MISSING_MUST_NOT_BECOME_DOES_NOT_APPLY")
    _assert_no_proxy_env_v1()

    bound: BoundInstrumentV1 | None
    instrument_scope_status = "MISSING"
    selected_instrument_id = ""
    try:
        bound = require_current_productive_29p_bound_instrument_v1(bound_instrument)
        selected_instrument_id = expected_venue_instrument_id_v1(bound)
        instrument_scope_status = "BOUND_TO_CAP24_SINGLE_SELECTED_FUTURE"
    except CurrentProductiveLabInstrumentScopeError as exc:
        bound = None
        selected_instrument_id = ""
        instrument_scope_status = f"FAIL_CLOSED:{exc}"

    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise CurrentProductiveLabInstrumentScopeError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    package_started = _utc_now_iso_v1()
    decision_epoch = package_started
    handle = None
    expected_uid = str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE)
    config_payload: Any = None
    balance_payload: Any = None
    config_status: int | None = None
    balance_status: int | None = None
    config_digest = ""
    balance_digest = ""
    config_time = ""
    balance_time = ""
    config_headers: dict[str, str] = {}
    balance_headers: dict[str, str] = {}
    config_error: str | None = None
    balance_error: str | None = None
    try:
        if productive:
            backend = build_file_secretref_vault_backend_v1(vault_file=Path(str(vault_file)))
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REQUIRED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REQUIRED_CREDENTIAL_CLASS,
            )
        (
            config_status,
            config_bytes,
            config_headers,
            config_time,
            config_payload,
            config_error,
        ) = _signed_get(
            client=client,
            endpoint=CURRENT_PRODUCTIVE_U01_GET_ENDPOINT,
            productive=productive,
            handle=handle,
        )
        config_digest = _sha256_bytes(config_bytes) if config_bytes else ""
        (
            balance_status,
            balance_bytes,
            balance_headers,
            balance_time,
            balance_payload,
            balance_error,
        ) = _signed_get(
            client=client,
            endpoint=account_balance_query_path_v1(),
            productive=productive,
            handle=handle,
        )
        balance_digest = _sha256_bytes(balance_bytes) if balance_bytes else ""
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    counters = _assert_get_only_client(client)
    package_finished = _utc_now_iso_v1()
    config_code, _config_msg = _okx_code_msg(config_payload)
    balance_code, _balance_msg = _okx_code_msg(balance_payload)
    productive_contact = productive is True and bool(
        getattr(transport, "venue_live_contact", False)
    )
    config_auth = _header_presence_v1(config_headers)
    balance_auth = _header_presence_v1(balance_headers)
    config_ok = (
        config_error is None
        and config_status == 200
        and config_code == "0"
        and isinstance(config_payload, dict)
        and (config_auth["AUTH_KEY_HEADER_PRESENT"] is True if productive else True)
    )
    balance_ok = (
        balance_error is None
        and balance_status == 200
        and balance_code == "0"
        and isinstance(balance_payload, dict)
        and (balance_auth["AUTH_KEY_HEADER_PRESENT"] is True if productive else True)
    )
    trusted_auth = (
        "TRUSTED_AUTHENTICATED_READ_ONLY"
        if productive_contact and config_ok and balance_ok
        else (
            "INJECTED_TEST_DOUBLE_NOT_PRODUCTIVE"
            if (not productive) and config_ok and balance_ok
            else "NOT_TRUSTED"
        )
    )
    uid_config = _extract_uid(config_payload if isinstance(config_payload, dict) else None)
    uid_balance = _extract_uid(balance_payload if isinstance(balance_payload, dict) else None)
    failure_reasons: list[str] = []
    if uid_config and uid_config != expected_uid:
        failure_reasons.append("ACCOUNT_IDENTITY_SCOPE_MISMATCH")
        config_ok = False
    if uid_balance and uid_balance != expected_uid:
        failure_reasons.append("ACCOUNT_IDENTITY_SCOPE_MISMATCH")
        balance_ok = False
    bound_uid = uid_config or uid_balance or expected_uid
    if config_ok and isinstance(config_payload, dict):
        adaptation = extract_raw_acct_lv_from_account_config_payload_v1(config_payload)
    else:
        adaptation = adapt_current_productive_u01_account_mode_v1(None)
    eligibility = None
    if config_ok:
        eligibility = build_current_productive_u01_eligibility_fact_v1(
            adaptation=adaptation,
            bound_account_identity=bound_uid,
            bound_venue_identity="okx",
            bound_td_mode=REQUIRED_TD_MODE,
            decision_epoch=decision_epoch,
            provenance_digest=config_digest or "0" * 64,
        )
    observation = None
    raw_availeq = ""
    row_status = "NOT_OBSERVED"
    observation_instrument = selected_instrument_id or (
        "ACCOUNT_LEVEL_USDC_NOT_29P_INSTRUMENT_AUTHORITY"
    )
    if balance_ok and isinstance(balance_payload, dict):
        try:
            raw_obs = acquire_fresh_available_margin_observation_from_payload_v1(
                pretrade_decision_id=decision_epoch,
                payload=balance_payload,
                instrument_id=observation_instrument,
                planned_td_mode=AVAILABLE_MARGIN_REQUIRED_TD_MODE,
                observed_at_utc=balance_time or decision_epoch,
                endpoint=account_balance_query_path_v1(),
                http_status=int(balance_status or 0),
                get_performed=True,
                rest_host=REUSED_BINDING_REST_HOST,
            )
            validated = validate_fresh_available_margin_observation_v1(
                raw_obs,
                pretrade_decision_id=decision_epoch,
                instrument_id=observation_instrument,
                available_margin_domain=AVAILABLE_MARGIN_OUTPUT_DOMAIN,
                planned_td_mode=AVAILABLE_MARGIN_REQUIRED_TD_MODE,
            )
            if validated.selected_ccy != AVAILABLE_MARGIN_REQUIRED_CCY:
                raise CurrentProductiveLabInstrumentScopeError("SELECTED_CCY_NOT_USDC")
            age = _age_seconds(
                observed_at_as_of=balance_time or decision_epoch,
                now_iso=package_finished,
            )
            observation = CurrentProductiveUsdcFreeMarginObservationV1(
                fact_id=OBSERVATION_FACT_ID,
                surface=OBSERVATION_SURFACE,
                value=str(validated.avail_eq_raw),
                settlement_currency=AVAILABLE_MARGIN_REQUIRED_CCY,
                selected_ccy=validated.selected_ccy,
                bound_account_identity=bound_uid,
                bound_venue_identity="okx",
                bound_td_mode=REQUIRED_TD_MODE,
                decision_epoch=decision_epoch,
                observed_at_as_of=balance_time or decision_epoch,
                age_seconds=age,
                freshness_max_age=str(NUMERIC_EQUITY_TTL_SECONDS),
                provenance_digest=balance_digest,
                already_net_of_in_use=TRUE_TOKEN,
                account_level_avail_eq_used=FALSE_TOKEN,
                fallback_chain_used=FALSE_TOKEN,
            )
            raw_availeq = str(validated.avail_eq_raw)
            row_status = "EXACTLY_ONE_USDC_DETAILS_ROW_VALID"
        except (
            LiveCanaryAvailableMarginObservationError,
            CurrentProductiveLabInstrumentScopeError,
            TypeError,
            ValueError,
            KeyError,
        ) as exc:
            row_status = f"FAIL_CLOSED:{type(exc).__name__}"
            failure_reasons.append(str(exc)[:200])
            observation = None
    p01_fact = None
    if observation is not None:
        p01_digest = _sha256_text(
            _canonical_json(
                {
                    "policy": EVIDENCE_REF,
                    "epoch": observation.decision_epoch,
                    "account": observation.bound_account_identity,
                    "instrument": selected_instrument_id,
                }
            )
        )
        p01_fact = bind_current_productive_p01_policy_fact_v1(
            bound_account_identity=observation.bound_account_identity,
            bound_venue_identity=observation.bound_venue_identity,
            bound_td_mode=observation.bound_td_mode,
            decision_epoch=observation.decision_epoch,
            observed_at_as_of=observation.observed_at_as_of,
            age_seconds=observation.age_seconds,
            freshness_max_age=observation.freshness_max_age,
            provenance_digest=p01_digest,
        )
    output = produce_current_productive_29p_risk_capital_v1(
        observation=observation,
        p01=p01_fact,
        eligibility=eligibility,
        eq_target=None,
        u04=None,
        restart_from_kind_set=FALSE_TOKEN,
    )
    if output.u04_applied != FALSE_TOKEN:
        raise CurrentProductiveLabInstrumentScopeError("U04_DOUBLE_COUNTING_GUARD_BROKEN")
    produced = output.produced == TRUE_TOKEN

    lab_status = LiveAccountBoundStatusV1.MISSING.value
    observed_instrument_id = ""
    lab_reasons: tuple[str, ...] = ()
    get_status = FreshPretradeGetStatusV1.MISSING.value
    if bound is not None and fresh_get_transport is not None:
        get_evidence = collect_fresh_pretrade_runtime_get_v1(
            pretrade_decision_id=decision_epoch,
            instrument_id=selected_instrument_id,
            td_mode=REQUIRED_TD_MODE,
            limit_px="",
            inst_type="FUTURES",
            transport=fresh_get_transport,
            require_collection=True,
        )
        get_status = str(get_evidence.evidence_status or "")
        lab = evaluate_live_account_bound_v1(
            get_evidence=get_evidence,
            expected_account_identity=expected_uid,
            expected_instrument_id=selected_instrument_id,
            expected_td_mode=REQUIRED_TD_MODE,
        )
        lab_status = lab.evidence_status
        lab_reasons = lab.reason_codes
        if lab.observed_inst_ids == (selected_instrument_id,):
            observed_instrument_id = selected_instrument_id
        elif lab.observed_inst_ids:
            observed_instrument_id = ""
    elif bound is None:
        lab_reasons = ("LIVE_ACCOUNT_BOUND_EXPECTED_IDENTITY_MISSING",)
    else:
        lab_reasons = ("LIVE_ACCOUNT_BOUND_REQUIRES_TRUSTED_FRESH_GET",)

    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status=get_status,
        live_account_bound_status=lab_status,
        expected_instrument_id=selected_instrument_id,
        observed_instrument_id=observed_instrument_id,
        fresh_evidence_fetched=balance_ok and get_status != FreshPretradeGetStatusV1.MISSING.value,
        fresh_evidence_validated=(
            observation is not None
            and balance_ok
            and get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
        ),
    )
    capital = evaluate_capital_admission_v1(
        claim=CapitalAdmissionClaimV1(
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            account_identity=bound_uid,
            instrument_id=selected_instrument_id,
            observed_capital_raw=output.value if produced else "",
            observed_field_name=PRODUCER_IDENTITY if produced else "",
            evidence_class="LIVE_TYPED",
            evidence_id=decision_epoch,
        )
        if produced and selected_instrument_id
        else None,
        expected_account_identity=expected_uid,
        expected_instrument_id=selected_instrument_id,
        admission_context=ADMISSION_CONTEXT_LIVE,
    )
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    persist_classes = persist_class_fields_v1(admissibility)
    evaluator_29p = persist_classes.get("STEP_29P_RISK_ADMISSIBLE") is True
    if evaluator_29p is True and produced is not True:
        raise CurrentProductiveLabInstrumentScopeError("29P_TRUE_WITHOUT_PRODUCER_OUTPUT")
    current_productive_29p = evaluator_29p is True and productive_contact is True
    lab_trusted = lab_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    instrument_bound = (
        bool(observed_instrument_id)
        and selected_instrument_id == observed_instrument_id
        and bound is not None
    )
    predicate_matrix = {
        "PREDICATE": [
            {
                "PREDICATE": "U01_ELIGIBLE",
                "CURRENT_VALUE": adaptation.status,
                "AUTHORITY": "CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_ADAPTER_V1",
                "EVIDENCE": CURRENT_PRODUCTIVE_U01_GET_ENDPOINT,
                "EPOCH_FRESHNESS": decision_epoch if eligibility is not None else "",
                "BLOCKING": eligibility is None,
            },
            {
                "PREDICATE": "P01_DOES_NOT_APPLY",
                "CURRENT_VALUE": p01_decision.decision_state,
                "AUTHORITY": "CURRENT_PRODUCTIVE_P01_POLICY_V1",
                "EVIDENCE": EVIDENCE_REF,
                "EPOCH_FRESHNESS": "STANDING_POLICY",
                "BLOCKING": p01_decision.decision_state != "DOES_NOT_APPLY",
            },
            {
                "PREDICATE": "FRESH_USDC_AVAILEQ",
                "CURRENT_VALUE": "OBSERVED_THIS_EPOCH"
                if observation is not None
                else "NOT_OBSERVED",
                "AUTHORITY": OBSERVATION_SURFACE,
                "EVIDENCE": CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
                "EPOCH_FRESHNESS": decision_epoch if observation is not None else "",
                "BLOCKING": observation is None,
            },
            {
                "PREDICATE": "RISK_CAPITAL_MINTED",
                "CURRENT_VALUE": "MINTED" if produced else "UNMINTED",
                "AUTHORITY": PRODUCER_IDENTITY,
                "EVIDENCE": output.value,
                "EPOCH_FRESHNESS": decision_epoch if produced else "",
                "BLOCKING": produced is not True,
            },
            {
                "PREDICATE": "LIVE_ACCOUNT_BOUND_TRUSTED",
                "CURRENT_VALUE": lab_status,
                "AUTHORITY": LAB_AUTHORITY,
                "EVIDENCE": list(lab_reasons),
                "EPOCH_FRESHNESS": decision_epoch,
                "BLOCKING": lab_trusted is not True,
            },
            {
                "PREDICATE": "INSTRUMENT_SCOPE_BOUND",
                "CURRENT_VALUE": instrument_scope_status,
                "AUTHORITY": INSTRUMENT_SCOPE_AUTHORITY,
                "EVIDENCE": {
                    "EXPECTED": selected_instrument_id,
                    "OBSERVED": observed_instrument_id,
                    "MAX_POSITIONS": MAX_POSITIONS_EFFECTIVE,
                },
                "EPOCH_FRESHNESS": decision_epoch,
                "BLOCKING": instrument_bound is not True,
            },
            {
                "PREDICATE": "FRESH_PRETRADE_GET_TRUSTED",
                "CURRENT_VALUE": get_status,
                "AUTHORITY": "VENUE_PRETRADE_GATES",
                "EVIDENCE": "collect_fresh_pretrade_runtime_get_v1",
                "EPOCH_FRESHNESS": decision_epoch,
                "BLOCKING": get_status != FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
            },
            {
                "PREDICATE": "STEP_29P_RISK_ADMISSIBLE_EVALUATOR",
                "CURRENT_VALUE": evaluator_29p,
                "AUTHORITY": "capital_risk_sizing_v1/STEP_29P",
                "EVIDENCE": list(admissibility.reason_codes),
                "EPOCH_FRESHNESS": decision_epoch,
                "BLOCKING": evaluator_29p is not True,
            },
            {
                "PREDICATE": "CURRENT_PRODUCTIVE_STEP_29P_RISK_ADMISSIBLE",
                "CURRENT_VALUE": current_productive_29p,
                "AUTHORITY": THIS_SLICE,
                "EVIDENCE": trusted_auth,
                "EPOCH_FRESHNESS": decision_epoch,
                "BLOCKING": current_productive_29p is not True,
            },
        ],
        "REASON_CODES": list(admissibility.reason_codes),
        "U04_NOT_SUBTRACTED": output.u04_applied == FALSE_TOKEN,
        "CURRENCY_BOUND": claim.observed_currency == claim.expected_currency,
        "EQUITY_DIMENSION_BOUND": produced,
        "SECRET_VALUES_INCLUDED": False,
    }
    if bound is None:
        first_blocker = "CURRENT_PRODUCTIVE_CAP24_BOUND_INSTRUMENT_INSTANCE_MISSING"
        blocker_class = "B"
        next_go = (
            "OWNER_GO_REQUIRED_TO_SUPPLY_CURRENT_CAP24_BOUND_INSTRUMENT_INSTANCE_"
            "FOR_29P_WITHOUT_CANARY_IMPORT_OR_RESELECTION_V1"
        )
    elif lab_trusted is not True:
        first_blocker = "LIVE_ACCOUNT_BOUND_NOT_TRUSTED_FOR_29P"
        blocker_class = "C"
        next_go = PIN_OWNER_GO
    elif instrument_bound is not True:
        first_blocker = "STEP_29P_INSTRUMENT_SCOPE_MISSING"
        blocker_class = "B"
        next_go = PIN_OWNER_GO
    elif eligibility is None:
        first_blocker = "CURRENT_PRODUCTIVE_U01_ELIGIBILITY_NOT_MINTED"
        blocker_class = "C"
        next_go = PIN_OWNER_GO
    elif observation is None:
        first_blocker = "FRESH_USDC_AVAILEQ_NOT_OBSERVED"
        blocker_class = "C"
        next_go = PIN_OWNER_GO
    elif produced is not True:
        first_blocker = "RISK_CAPITAL_MINT_FAIL_CLOSED"
        blocker_class = "C"
        next_go = PIN_OWNER_GO
    elif productive_contact is not True:
        first_blocker = (
            "CURRENT_PRODUCTIVE_29P_REQUIRES_PRODUCTIVE_TRUSTED_GET_AND_CAP24_BOUND_INSTRUMENT"
        )
        blocker_class = "C"
        next_go = (
            "OWNER_GO_REQUIRED_TO_SUPPLY_CURRENT_CAP24_BOUND_INSTRUMENT_INSTANCE_"
            "AND_PRODUCTIVE_READ_ONLY_GET_FOR_29P_V1"
        )
    elif current_productive_29p is True:
        first_blocker = "LIVE_ENABLED_STANDING_GATE_REMAINS_FALSE"
        blocker_class = "E"
        next_go = "OWNER_GO_REQUIRED_FOR_LIVE_ENABLED_NOT_AUTHORIZED_BY_THIS_SLICE"
    else:
        first_blocker = "STEP_29P_RISK_ADMISSIBLE_FALSE"
        blocker_class = "C"
        next_go = PIN_OWNER_GO
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = (
        Path(evidence_root)
        if evidence_root is not None
        else _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / run_id
    )
    store.mkdir(parents=True, exist_ok=True)
    pins = current_productive_p01_policy_pins_v1()
    claims = {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CY",
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "LIVE_ACCOUNT_BOUND_STATUS": lab_status,
        "LIVE_ACCOUNT_BOUND_AUTHORITY": LAB_AUTHORITY,
        "LIVE_ACCOUNT_BOUND_EVIDENCE": list(lab_reasons),
        "SECRET_MATERIAL_PERSISTED": False,
        "INSTRUMENT_SCOPE_STATUS": instrument_scope_status,
        "SELECTED_INSTRUMENT_ID": selected_instrument_id,
        "OBSERVED_INSTRUMENT_ID": observed_instrument_id,
        "INSTRUMENT_SCOPE_AUTHORITY": INSTRUMENT_SCOPE_AUTHORITY,
        "SINGLE_SELECTED_FUTURE_PROVEN": TRUE_TOKEN
        if bound is not None and int(bound.selected_future_count) == 1
        else FALSE_TOKEN,
        "MAX_POSITIONS_EFFECTIVE": str(MAX_POSITIONS_EFFECTIVE),
        "DECISION_EPOCH_BINDING": decision_epoch,
        "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": FALSE_TOKEN,
        "CANARY_DEFAULT_INSTRUMENT_NOT_FALLBACK_AUTHORITY": TRUE_TOKEN
        if selected_instrument_id != CANARY_DEFAULT_INSTRUMENT_ID or bound is not None
        else FALSE_TOKEN,
        "P01_POLICY_DECISION": pins["P01_POLICY_DECISION"],
        "P01_DECISION_BASIS": pins["P01_DECISION_BASIS"],
        "P01_APPLICABILITY": p01_decision.decision_state,
        "P01_STATUS": p01_decision.reason_code,
        "P01_DIRECTIVE_STATUS": "RATIFIED_CURRENT_PRODUCTIVE_DOES_NOT_APPLY",
        "P01_RUNTIME_INSTANCE_PRESENT": FALSE_TOKEN,
        "P01_LEGACY_RECONSTRUCTION_PERFORMED": FALSE_TOKEN,
        "U01_STATUS": adaptation.status,
        "U01_RUNTIME_FACT_STATUS": (
            "MINTED_CURRENT_PRODUCTIVE_U01_ELIGIBILITY_FACT"
            if eligibility is not None
            else "MISSING_NO_CURRENT_PRODUCTIVE_U01_RUNTIME_INSTANCE"
        ),
        "FRESH_USDC_AVAILEQ_STATUS": (
            "OBSERVED_THIS_EPOCH" if observation is not None else "NOT_OBSERVED"
        ),
        "RAW_USDC_AVAILEQ": raw_availeq,
        "USDC_DETAILS_ROW_STATUS": row_status,
        "TRUSTED_AUTH_STATUS": trusted_auth,
        "GET_ENDPOINT_U01": CURRENT_PRODUCTIVE_U01_GET_ENDPOINT,
        "GET_ENDPOINT_BALANCE": CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
        "HTTP_STATUS_U01": "" if config_status is None else str(config_status),
        "HTTP_STATUS_BALANCE": "" if balance_status is None else str(balance_status),
        "U04_SUBTRACTED": output.u04_applied,
        "DOUBLE_COUNTING_GUARD": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
        "EQ_USED_AS_SOURCE": FALSE_TOKEN,
        "FORBIDDEN_FALLBACK_USED": FALSE_TOKEN,
        "PRODUCER_ALGEBRA": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
        "PRODUCER_IDENTITY": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
        "PRODUCER_OUTPUT_STATUS": "MINTED" if produced else "FAIL_CLOSED",
        "PRODUCER_OUTPUT_VALUE_USDC": output.value,
        "PRODUCER_REASON_CODES": list(output.reason_codes),
        "RISK_CAPITAL_MINT_STATUS": "MINTED" if produced else "UNMINTED",
        "STEP_29P_RISK_ADMISSIBLE": TRUE_TOKEN if current_productive_29p else FALSE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE_EVALUATOR": TRUE_TOKEN if evaluator_29p else FALSE_TOKEN,
        "29P_PREDICATE_MATRIX": predicate_matrix,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "NEXT_OWNER_GO_REQUIRED": next_go,
        "POST_COUNT": "0",
        "LIVE_ENABLED": FALSE_TOKEN,
        "LIVE_ARMED": FALSE_TOKEN,
        "WIRE_SEND_PERMITTED": FALSE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "GET_FAILURE_REASONS": failure_reasons,
        "CONFIG_ERROR": config_error or "",
        "BALANCE_ERROR": balance_error or "",
        "CLIENT_COUNTERS": counters,
        "SECRET_VALUES_INCLUDED": False,
        "P01_FORMULA": POLICY_FORMULA,
        "P01_AUTHORIZED_INPUTS": AUTHORIZED_INPUTS,
        "P01_INDEPENDENT_SAFETY_FUNCTION": pins["P01_INDEPENDENT_SAFETY_FUNCTION"],
    }
    summary = {
        "DOCUMENT_CLASS": SCHEMA_CLASS,
        "LIVE_ACCOUNT_BOUND_STATUS": lab_status,
        "INSTRUMENT_SCOPE_STATUS": instrument_scope_status,
        "SELECTED_INSTRUMENT_ID": selected_instrument_id,
        "P01_POLICY_DECISION": "DOES_NOT_APPLY",
        "FRESH_GET_EXECUTED": TRUE_TOKEN if config_ok and balance_ok else FALSE_TOKEN,
        "RISK_CAPITAL_MINT_STATUS": claims["RISK_CAPITAL_MINT_STATUS"],
        "STEP_29P_RISK_ADMISSIBLE": claims["STEP_29P_RISK_ADMISSIBLE"],
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "POST_COUNT": "0",
        "SECRET_VALUES_INCLUDED": False,
    }
    lineage = {
        "PARENT_SECTIONS": ["11.2.1.CX", "11.2.1.CW", "11.2.1.CV", "11.2.1.CU", "11.2.1.M"],
        "OWNER_GO": OWNER_GO,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "ATLAS_AUTHORITY": "NONE",
        "INSTRUMENT_SCOPE_AUTHORITY": INSTRUMENT_SCOPE_AUTHORITY,
        "LIVE_ACCOUNT_BOUND_AUTHORITY": LAB_AUTHORITY,
    }
    protected = {
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "BULL_BEAR_STATE_SWITCH_UNCHANGED": TRUE_TOKEN,
        "TOP20_UNCHANGED": TRUE_TOKEN,
        "SELF_LEARNING_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_AUTONOMY_UNCHANGED": TRUE_TOKEN,
        "SINGLE_SELECTED_FUTURE_UNCHANGED": TRUE_TOKEN,
        "MAX_POSITIONS_ONE_UNCHANGED": TRUE_TOKEN,
        "CANARY_INSTRUMENT_AUTHORITY_NOT_IMPORTED": TRUE_TOKEN,
    }
    bound_dump = None if bound is None else bound.to_dict()
    for payload in (claims, summary, lineage, protected, {"BOUND_INSTRUMENT": bound_dump}):
        _assert_no_secrets(payload)
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "SUMMARY.json", payload=summary)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "bound_instrument_v1.json", payload={"BOUND_INSTRUMENT": bound_dump})
    _persist_json(
        path=store / "predicate_matrix_v1.json",
        payload={"29P_PREDICATE_MATRIX": predicate_matrix},
    )
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveLabInstrumentScopeResultV1(
        store_root=str(store),
        live_account_bound_status=lab_status,
        instrument_scope_status=instrument_scope_status,
        selected_instrument_id=selected_instrument_id,
        single_selected_future_proven=str(claims["SINGLE_SELECTED_FUTURE_PROVEN"]),
        max_positions_effective=str(MAX_POSITIONS_EFFECTIVE),
        u01_status=adaptation.status,
        p01_status=p01_decision.decision_state,
        fresh_usdc_availeq_status=str(claims["FRESH_USDC_AVAILEQ_STATUS"]),
        risk_capital_mint_status=str(claims["RISK_CAPITAL_MINT_STATUS"]),
        step_29p_risk_admissible=str(claims["STEP_29P_RISK_ADMISSIBLE"]),
        first_real_blocker=first_blocker,
        blocker_class=blocker_class,
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--origin-main-sha", required=True)
    parser.add_argument("--vault-file")
    parser.add_argument("--evidence-root")
    parser.add_argument("--execute-get", action="store_true")
    args = parser.parse_args()
    result = execute_current_productive_lab_and_instrument_scope_for_29p_v1(
        owner_go=args.owner_go,
        origin_main_sha=args.origin_main_sha,
        bound_instrument=None,
        vault_file=args.vault_file,
        evidence_root=Path(args.evidence_root) if args.evidence_root else None,
        execute_get=bool(args.execute_get),
    )
    print(_canonical_json({"FIRST_REAL_BLOCKER": result.first_real_blocker}))
    return 0 if result.manifest_verify_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
