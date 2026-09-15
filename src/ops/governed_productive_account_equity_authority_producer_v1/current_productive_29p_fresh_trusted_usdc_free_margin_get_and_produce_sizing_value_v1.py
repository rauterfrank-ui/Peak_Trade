"""Fresh trusted USDC free-margin GET and 29P sizing-value produce v1.

Consumes Owner-GO
CURRENT_PRODUCTIVE_29P_FRESH_TRUSTED_USDC_FREE_MARGIN_GET_AND_PRODUCE_SIZING_VALUE_V1.

Performs exactly one authorized READ-ONLY GET /api/v5/account/balance,
observes details[ccy=USDC].availEq, resolves P01 only through the
already-authorized CURRENT_PRODUCTIVE evaluator, and mints
RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING only when every required
fact validates. U04 is not subtracted again. eq is not a source.
Account-level availEq/totalEq/adjEq/availBal/cashBal/fallback remain
forbidden. No POST. No Live enable/arm. No wire send.

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
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
    persist_class_fields_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_FRESH_GET_AUTHORIZED_COUNT,
    CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
    CURRENT_PRODUCTIVE_29P_FRESH_GET_POST_COUNT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_P01_APPLICATION,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    ELIGIBILITY_FACT_ID,
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
    P01_FACT_ID,
    PRODUCER_IDENTITY,
    REQUIRED_TD_MODE,
    bind_step_29p_typed_equity_from_risk_capital_v1,
    produce_current_productive_29p_risk_capital_v1,
    reject_direct_avail_eq_29p_claim_v1,
    CurrentProductiveUsdcFreeMarginObservationV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveP01ReductionFactV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_governed_reduction_directive_evaluator_v1 import (
    REASON_MISSING,
    evaluate_p01_application_predicate_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    AVAILABLE_MARGIN_ENDPOINT_PATH,
    AVAILABLE_MARGIN_OUTPUT_DOMAIN,
    AVAILABLE_MARGIN_REQUIRED_CCY,
    AVAILABLE_MARGIN_REQUIRED_TD_MODE,
    LiveCanaryAvailableMarginObservationError,
    account_balance_query_path_v1,
    acquire_fresh_available_margin_observation_from_payload_v1,
    validate_fresh_available_margin_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
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

OWNER_GO = "CURRENT_PRODUCTIVE_29P_FRESH_TRUSTED_USDC_FREE_MARGIN_GET_AND_PRODUCE_SIZING_VALUE_V1"
PIN_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_PERFORM_FRESH_TRUSTED_READ_ONLY_GET_OF_"
    "DETAILS_USDC_AVAILEQ_AND_PRODUCE_29P_SIZING_VALUE_V1"
)
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, PIN_OWNER_GO, f"OWNER_GO_{OWNER_GO}"})
EXPECTED_ORIGIN_MAIN_SHA = "62ac12d8167757aeaa145af03d0e972772385195"
THIS_SLICE = (
    "11.2.1.CV.FULL_CORE_CURRENT_PRODUCTIVE_29P_FRESH_TRUSTED_USDC_"
    "FREE_MARGIN_GET_AND_PRODUCE_SIZING_VALUE"
)
SCHEMA_CLASS = (
    "CURRENT_PRODUCTIVE_29P_FRESH_TRUSTED_USDC_FREE_MARGIN_GET_AND_PRODUCE_SIZING_VALUE_V1"
)
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
EVIDENCE_DIRNAME = "full_core_current_productive_29p_fresh_trusted_usdc_free_margin_get_v1"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_29p_fresh_trusted_usdc_free_margin_get_v1/"
    "20260915T105152Z"
)
AUTHORIZED_HOST = "eea.okx.com"
REUSED_REST_BASE = f"https://{AUTHORIZED_HOST}"
ENDPOINT = CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT
USER_AGENT = "PeakTrade-FullCore-CU-29P-USDC-FreeMarginGET/1"
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
_TRANSIENT_GET_MARKERS = ("TIMEOUT", "NETWORK_ERROR")
_REPO_ROOT = Path(__file__).resolve().parents[3]
CLAIMS_FILE = "claims.json"
GETS_FILE = "GETS.json"
SUMMARY_FILE = "SUMMARY.json"
LINEAGE_FILE = "LINEAGE.json"
PROTECTED_FILE = "protected_surfaces_v1.json"
P01_FILE = "p01_resolution_v1.json"
PRODUCER_FILE = "producer_output_v1.json"
ADMISSIBILITY_FILE = "step_29p_admissibility_v1.json"
SNAPSHOT_FILE = "GET_SNAPSHOT.sanitized.json"


class CurrentProductive29PFreshGetError(RuntimeError):
    """Fail-closed fresh USDC free-margin GET / produce violation."""


@dataclass(frozen=True)
class CurrentProductive29PFreshGetPersistResultV1:
    store_root: str
    fresh_get_executed: str
    http_status: str
    venue_code: str
    trusted_auth_status: str
    usdc_details_row_status: str
    raw_usdc_availeq: str
    producer_output_status: str
    producer_output_value_usdc: str
    producer_output_digest: str
    step_29p_value_binding_status: str
    step_29p_risk_admissible: str
    p01_applicability: str
    p01_status: str
    u04_subtracted: str
    forbidden_fallback_used: str
    eq_used_as_source: str
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
            raise CurrentProductive29PFreshGetError("SECRET_LEAK_FORBIDDEN")


def _assert_no_proxy_env_v1() -> None:
    present = [key for key in _PROXY_ENV_KEYS if str(os.environ.get(key) or "").strip()]
    if present:
        raise CurrentProductive29PFreshGetError("HTTP_PROXY_FORBIDDEN")


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
        raise CurrentProductive29PFreshGetError("WRITE_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise CurrentProductive29PFreshGetError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise CurrentProductive29PFreshGetError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise CurrentProductive29PFreshGetError("FLATTEN_SUBMIT_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise CurrentProductive29PFreshGetError("TRANSFER_REQUEST_DETECTED")
    methods = list(client.counters.methods_used)
    if any(method in FORBIDDEN_HTTP_METHODS for method in methods):
        raise CurrentProductive29PFreshGetError("FORBIDDEN_METHOD")
    if any(method != "GET" for method in methods):
        raise CurrentProductive29PFreshGetError("NON_GET_METHOD_DETECTED")
    return counters


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


def _extract_uid(payload: Mapping[str, Any]) -> str:
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


def _forensic_balance_snapshot_v1(
    *,
    payload: Mapping[str, Any] | None,
    expected_account_identity: str,
    body_digest: str,
    http_status: int | None,
    endpoint: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "STATUS": "NO_JSON_OBJECT",
            "ENDPOINT": endpoint,
            "HTTP_STATUS": http_status,
            "RAW_BODY_SHA256": body_digest,
            "SECRET_VALUES_INCLUDED": False,
        }
    data = payload.get("data")
    account_keys: list[str] = []
    ccy_list: list[str] = []
    usdc_rows = 0
    usdc_availeq = ""
    usdc_utime = ""
    account_utime = ""
    if isinstance(data, list) and data and isinstance(data[0], Mapping):
        row = data[0]
        account_keys = sorted(str(key) for key in row.keys() if key != "details")
        account_utime = "" if row.get("uTime") is None else str(row.get("uTime"))
        details = row.get("details")
        if isinstance(details, list):
            for item in details:
                if not isinstance(item, Mapping):
                    continue
                ccy = str(item.get("ccy") or "").strip()
                if ccy:
                    ccy_list.append(ccy)
                if ccy == AVAILABLE_MARGIN_REQUIRED_CCY:
                    usdc_rows += 1
                    usdc_availeq = "" if item.get("availEq") is None else str(item.get("availEq"))
                    usdc_utime = "" if item.get("uTime") is None else str(item.get("uTime"))
    uid_observed = _extract_uid(payload)
    return {
        "STATUS": "SANITIZED_BALANCE_FORENSIC",
        "ENDPOINT": endpoint,
        "HTTP_STATUS": http_status,
        "VENUE_CODE": str(payload.get("code") or ""),
        "VENUE_MSG": str(payload.get("msg") or "")[:200],
        "RAW_BODY_SHA256": body_digest,
        "ACCOUNT_UID_OBSERVED": uid_observed,
        "ACCOUNT_UID_EXPECTED": expected_account_identity,
        "ACCOUNT_UTIME": account_utime,
        "DETAILS_CCY_LIST": ccy_list,
        "USDC_ROW_COUNT": usdc_rows,
        "USDC_ROW": {
            "ccy": AVAILABLE_MARGIN_REQUIRED_CCY,
            "availEq": usdc_availeq,
            "uTime": usdc_utime,
        },
        "ACCOUNT_LEVEL_KEYS_PRESENT_NOT_USED": account_keys,
        "FORBIDDEN_ACCOUNT_LEVEL_FIELDS_NOT_USED_AS_SOURCE": True,
        "SECRET_VALUES_INCLUDED": False,
    }


def execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE,
    execute_get: bool = False,
) -> CurrentProductive29PFreshGetPersistResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise CurrentProductive29PFreshGetError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductive29PFreshGetError("ORIGIN_MAIN_SHA_MISMATCH")
    if execute_get is not True:
        raise CurrentProductive29PFreshGetError("EXECUTE_GET_FLAG_REQUIRED")
    if LIVE_ENABLED is not False or LIVE_ARMED is not False or WIRE_SEND_PERMITTED is not False:
        raise CurrentProductive29PFreshGetError("STANDING_LIVE_GATES_MUST_REMAIN_FALSE")
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductive29PFreshGetError("SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED")
    if CURRENT_PRODUCTIVE_29P_FRESH_GET_POST_COUNT != 0:
        raise CurrentProductive29PFreshGetError("POST_COUNT_PIN_DRIFT")
    if CURRENT_PRODUCTIVE_29P_FRESH_GET_AUTHORIZED_COUNT != 1:
        raise CurrentProductive29PFreshGetError("AUTHORIZED_GET_COUNT_PIN_DRIFT")
    if ENDPOINT != AVAILABLE_MARGIN_ENDPOINT_PATH:
        raise CurrentProductive29PFreshGetError("ENDPOINT_DRIFT")
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise CurrentProductive29PFreshGetError("HOST_MISMATCH")
    _assert_no_proxy_env_v1()
    reject_direct_avail_eq_29p_claim_v1(claimed="producer")

    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise CurrentProductive29PFreshGetError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise CurrentProductive29PFreshGetError("PRODUCTIVE_HTTP_SEND_DISABLED")

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
    endpoint = account_balance_query_path_v1()
    if endpoint in FORBIDDEN_ENDPOINTS or endpoint != ENDPOINT:
        raise CurrentProductive29PFreshGetError("MUTATION_ENDPOINT_FORBIDDEN")
    url = f"{REUSED_REST_BASE}{endpoint}"
    if urlparse(url).hostname != AUTHORIZED_HOST:
        raise CurrentProductive29PFreshGetError("HOST_MISMATCH")

    request_time = ""
    http_status: int | None = None
    body_bytes = b""
    get_error: str | None = None
    payload: Any = None
    retry_used = FALSE_TOKEN
    headers: dict[str, str] = {"User-Agent": USER_AGENT}
    try:
        if productive:
            backend = build_file_secretref_vault_backend_v1(vault_file=Path(str(vault_file)))
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REQUIRED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REQUIRED_CREDENTIAL_CLASS,
            )
        for attempt in (1, 2):
            request_time = _utc_now_iso_v1()
            headers = {"User-Agent": USER_AGENT}
            if handle is not None:
                headers = build_okx_live_canary_auth_headers_v1(
                    handle=handle, url=url, method="GET"
                )
                headers["User-Agent"] = USER_AGENT
            elif productive:
                raise CurrentProductive29PFreshGetError("PRIVATE_GET_REQUIRES_CREDENTIAL_HANDLE")
            try:
                response = client.get(endpoint=endpoint, headers=headers)
                http_status = int(response.status_code)
                body_bytes = bytes(response.body_bytes)
                if response.method != "GET":
                    raise CurrentProductive29PFreshGetError("NON_GET_RESPONSE")
                if bool(response.redirect_followed):
                    get_error = "REDIRECT_FOLLOWED"
                    break
                try:
                    payload = parse_json_object_v1(body_bytes)
                    get_error = None
                except (LiveCanaryHttpError, ValueError, json.JSONDecodeError):
                    payload = None
                    get_error = "MALFORMED_JSON"
                break
            except LiveCanaryHttpError as exc:
                get_error = str(exc)[:200]
                http_status = None
                payload = None
                body_bytes = b""
                transient = any(marker in get_error for marker in _TRANSIENT_GET_MARKERS)
                if attempt == 1 and transient:
                    retry_used = TRUE_TOKEN
                    continue
                break
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)

    counters = _assert_get_only_client(client)
    package_finished = _utc_now_iso_v1()
    code, msg = _okx_code_msg(payload)
    auth_presence = _header_presence_v1(headers)
    body_digest = _sha256_bytes(body_bytes) if body_bytes else ""
    productive_contact = productive is True and bool(
        getattr(transport, "venue_live_contact", False)
    )
    get_ok = (
        get_error is None
        and http_status == 200
        and code == "0"
        and isinstance(payload, dict)
        and auth_presence["AUTH_KEY_HEADER_PRESENT"] is True
        if productive
        else (
            get_error is None and http_status == 200 and code == "0" and isinstance(payload, dict)
        )
    )
    trusted_auth = (
        "TRUSTED_AUTHENTICATED_READ_ONLY"
        if productive_contact and get_ok
        else (
            "INJECTED_TEST_DOUBLE_NOT_PRODUCTIVE" if (not productive) and get_ok else "NOT_TRUSTED"
        )
    )
    row_status = "NOT_OBSERVED"
    raw_availeq = ""
    observation = None
    fallback_used = FALSE_TOKEN
    eq_used = FALSE_TOKEN
    forbidden_reasons: list[str] = []
    if get_ok and isinstance(payload, dict):
        try:
            raw_obs = acquire_fresh_available_margin_observation_from_payload_v1(
                pretrade_decision_id=decision_epoch,
                payload=payload,
                instrument_id=DEFAULT_INSTRUMENT_ID,
                planned_td_mode=AVAILABLE_MARGIN_REQUIRED_TD_MODE,
                observed_at_utc=request_time,
                endpoint=endpoint,
                http_status=int(http_status or 0),
                get_performed=True,
                rest_host=REUSED_BINDING_REST_HOST,
                auth_header_sent=auth_presence["AUTH_SIGN_HEADER_PRESENT"] if productive else True,
                historical_reuse=False,
                body_sha256=body_digest,
            )
            validated = validate_fresh_available_margin_observation_v1(
                raw_obs,
                pretrade_decision_id=decision_epoch,
                instrument_id=DEFAULT_INSTRUMENT_ID,
                available_margin_domain=AVAILABLE_MARGIN_OUTPUT_DOMAIN,
                planned_td_mode=AVAILABLE_MARGIN_REQUIRED_TD_MODE,
            )
            if str(raw_obs.account_avail_eq_raw or "") and validated.avail_eq_raw == str(
                raw_obs.account_avail_eq_raw
            ):
                if validated.selected_ccy != AVAILABLE_MARGIN_REQUIRED_CCY:
                    fallback_used = TRUE_TOKEN
            uid_observed = _extract_uid(payload)
            expected_uid = str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE)
            if uid_observed and uid_observed != expected_uid:
                raise CurrentProductive29PFreshGetError("ACCOUNT_IDENTITY_SCOPE_MISMATCH")
            bound_uid = uid_observed or expected_uid
            age = _age_seconds(observed_at_as_of=request_time, now_iso=package_finished)
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
                observed_at_as_of=request_time,
                age_seconds=age,
                freshness_max_age=str(NUMERIC_EQUITY_TTL_SECONDS),
                provenance_digest=body_digest,
                already_net_of_in_use=TRUE_TOKEN,
                account_level_avail_eq_used=FALSE_TOKEN,
                fallback_chain_used=FALSE_TOKEN,
            )
            raw_availeq = str(validated.avail_eq_raw)
            row_status = "EXACTLY_ONE_USDC_DETAILS_ROW_VALID"
        except (
            LiveCanaryAvailableMarginObservationError,
            CurrentProductive29PFreshGetError,
            TypeError,
            ValueError,
            KeyError,
        ) as exc:
            row_status = f"FAIL_CLOSED:{type(exc).__name__}"
            forbidden_reasons.append(str(exc)[:200])
            observation = None

    p01_decision = evaluate_p01_application_predicate_v1(())
    if P01_RUNTIME_INSTANCE_PRESENT is True:
        raise CurrentProductive29PFreshGetError("P01_RUNTIME_INSTANCE_MUST_REMAIN_ABSENT")
    p01_fact = None
    if observation is not None:
        p01_digest = _sha256_text(
            _canonical_json(
                {
                    "decision_state": p01_decision.decision_state,
                    "reason_code": p01_decision.reason_code,
                    "ready": p01_decision.ready,
                    "runtime_instance_present": FALSE_TOKEN,
                    "epoch": observation.decision_epoch,
                }
            )
        )
        p01_fact = CurrentProductiveP01ReductionFactV1(
            fact_id=P01_FACT_ID,
            applicability_state=p01_decision.decision_state,
            value="",
            settlement_currency="NONE",
            bound_account_identity=observation.bound_account_identity,
            bound_venue_identity=observation.bound_venue_identity,
            bound_td_mode=observation.bound_td_mode,
            decision_epoch=observation.decision_epoch,
            observed_at_as_of=observation.observed_at_as_of,
            age_seconds=observation.age_seconds,
            freshness_max_age=observation.freshness_max_age,
            provenance_digest=p01_digest,
            source_class="GOVERNED_CONDITIONAL",
        )
    output = produce_current_productive_29p_risk_capital_v1(
        observation=observation,
        p01=p01_fact,
        eligibility=None,
        eq_target=None,
        u04=None,
        restart_from_kind_set=FALSE_TOKEN,
    )
    if output.u04_applied != FALSE_TOKEN:
        raise CurrentProductive29PFreshGetError("U04_DOUBLE_COUNTING_GUARD_BROKEN")
    produced = output.produced == TRUE_TOKEN
    binding_status = (
        "CONSUMER_BOUND_VALUE_BOUND_THIS_EPOCH_EPHEMERAL"
        if produced
        else "CONSUMER_BOUND_TO_PRODUCER_OUTPUT_SURFACE_BOUND_VALUE_UNBOUND"
    )
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status=(
            FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
            if productive_contact and get_ok
            else FreshPretradeGetStatusV1.MISSING.value
        ),
        live_account_bound_status=LiveAccountBoundStatusV1.MISSING.value,
        expected_instrument_id=DEFAULT_INSTRUMENT_ID,
        observed_instrument_id="",
        fresh_evidence_fetched=get_ok,
        fresh_evidence_validated=observation is not None and get_ok,
    )
    capital = evaluate_capital_admission_v1(
        claim=CapitalAdmissionClaimV1(
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            account_identity=str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE),
            instrument_id=DEFAULT_INSTRUMENT_ID,
            observed_capital_raw=output.value if produced else "",
            observed_field_name=PRODUCER_IDENTITY if produced else "",
            evidence_class="LIVE_TYPED",
            evidence_id=decision_epoch,
        )
        if produced
        else None,
        expected_account_identity=str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE),
        expected_instrument_id=DEFAULT_INSTRUMENT_ID,
        admission_context=ADMISSION_CONTEXT_LIVE,
    )
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    persist_classes = persist_class_fields_v1(admissibility)
    if persist_classes.get("STEP_29P_RISK_ADMISSIBLE") is True and produced is not True:
        raise CurrentProductive29PFreshGetError("29P_TRUE_WITHOUT_PRODUCER_OUTPUT_FORBIDDEN")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = (
        Path(evidence_root)
        if evidence_root is not None
        else _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / run_id
    )
    store.mkdir(parents=True, exist_ok=True)
    other_29p = [code for code in admissibility.reason_codes if code]
    expected_uid = str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE)
    uid_observed = _extract_uid(payload) if isinstance(payload, dict) else ""
    account_identity_provenance = (
        "PAYLOAD_UID"
        if uid_observed and uid_observed == expected_uid
        else (
            "CREDENTIAL_BOUND_PRIVATE_GET_UID_ABSENT_FROM_BALANCE_PAYLOAD"
            if uid_observed == ""
            else "PAYLOAD_UID_MISMATCH"
        )
    )
    snapshot = _forensic_balance_snapshot_v1(
        payload=payload if isinstance(payload, dict) else None,
        expected_account_identity=expected_uid,
        body_digest=body_digest,
        http_status=http_status,
        endpoint=endpoint,
    )
    snapshot_availeq = str((snapshot.get("USDC_ROW") or {}).get("availEq") or "")
    if snapshot.get("USDC_ROW_COUNT") == 1 and snapshot_availeq and not raw_availeq:
        raw_availeq = snapshot_availeq
    claims = {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CV",
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "FRESH_GET_EXECUTED": TRUE_TOKEN if get_ok else FALSE_TOKEN,
        "GET_ENDPOINT": ENDPOINT,
        "HTTP_STATUS": "" if http_status is None else str(http_status),
        "VENUE_CODE": code,
        "VENUE_MSG": msg,
        "TRUSTED_AUTH_STATUS": trusted_auth,
        "USDC_DETAILS_ROW_STATUS": row_status,
        "RAW_USDC_AVAILEQ": raw_availeq,
        "AVAILEQ_UNIT": "USDC",
        "ACCOUNT_IDENTITY_PROVENANCE": account_identity_provenance,
        "BOUND_ACCOUNT_IDENTITY": expected_uid,
        "GET_TIMESTAMP": request_time,
        "GET_FRESHNESS": "FRESH_GET_PER_PRETRADE_DECISION" if get_ok else "NOT_FRESH",
        "GET_EVIDENCE_DIGEST": body_digest,
        "FORBIDDEN_FALLBACK_USED": fallback_used,
        "EQ_USED_AS_SOURCE": eq_used,
        "U04_SUBTRACTED": output.u04_applied,
        "DOUBLE_COUNTING_GUARD": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
        "P01_APPLICABILITY": p01_decision.decision_state,
        "P01_VALUE_USDC": p01_decision.authorized_reduction_amount,
        "P01_STATUS": p01_decision.reason_code or REASON_MISSING,
        "P01_RUNTIME_INSTANCE_PRESENT": FALSE_TOKEN,
        "P01_APPLICATION": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_P01_APPLICATION,
        "ELIGIBILITY_FACT_ID": ELIGIBILITY_FACT_ID,
        "ELIGIBILITY_STATUS": "MISSING_NO_CURRENT_PRODUCTIVE_U01_RUNTIME_INSTANCE",
        "PRODUCER_ALGEBRA": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
        "PRODUCER_IDENTITY": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
        "PRODUCER_OUTPUT_VALUE_USDC": output.value,
        "PRODUCER_OUTPUT_STATUS": "PRODUCED" if produced else "FAIL_CLOSED",
        "PRODUCER_OUTPUT_DIGEST": output.input_set_digest,
        "PRODUCER_REASON_CODES": list(output.reason_codes),
        "STEP_29P_VALUE_BINDING_STATUS": binding_status,
        "STEP_29P_RISK_ADMISSIBLE": TRUE_TOKEN
        if admissibility.risk_admissible is True
        else FALSE_TOKEN,
        "OTHER_29P_BLOCKERS": other_29p,
        "CURRENT_LIVE_CRITICAL_BLOCKER": (
            other_29p[0] if other_29p else "NONE_29P_VALUE_BOUND_THIS_EPOCH_EPHEMERAL"
        ),
        "RESTART_STATUS": "FRESH_REOBSERVE_DETAILS_USDC_AVAILEQ_SAME_EPOCH_ELSE_FAIL_CLOSED",
        "LEGACY_CENSUS_REOPENED": FALSE_TOKEN,
        "PROTECTED_SURFACES_NON_REGRESSION": TRUE_TOKEN,
        "AUTHORIZED_GET_COUNT": "1",
        "ACTUAL_GET_COUNT": str(int(counters.get("GET_REQUEST_COUNT", 0) or 0)),
        "POST_COUNT": "0",
        "RETRY_USED": retry_used,
        "LIVE_ENABLED": FALSE_TOKEN,
        "LIVE_ARMED": FALSE_TOKEN,
        "WIRE_SEND_PERMITTED": FALSE_TOKEN,
        "ATLAS_AUTHORITY": NONE_TOKEN,
        "VALUE_EPHEMERAL_NOT_DURABLE_ACROSS_RESTART": TRUE_TOKEN,
        "GET_FAILURE_REASONS": forbidden_reasons,
        "PERSIST_CLASSES": persist_classes,
        "PACKAGE_STARTED_UTC": package_started,
        "PACKAGE_FINISHED_UTC": package_finished,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
    }
    gets = {
        "REQUESTS": [
            {
                "UTC": request_time,
                "ENDPOINT": endpoint,
                "HTTP_STATUS": http_status,
                "OKX_CODE": code,
                "OKX_MSG": msg,
                "REQUEST_SCOPE": {
                    "account_identity": str(
                        expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE
                    ),
                    "td_mode": REQUIRED_TD_MODE,
                    "currency": AVAILABLE_MARGIN_REQUIRED_CCY,
                    "auth_required": True,
                    "SECRET_VALUES_INCLUDED": False,
                },
                "CURRENCY_SCOPE": AVAILABLE_MARGIN_REQUIRED_CCY,
                "OBSERVED_FIELD": OBSERVATION_SURFACE,
                "RAW_USDC_AVAILEQ": raw_availeq,
                "VENUE_UTIME": str((snapshot.get("USDC_ROW") or {}).get("uTime") or ""),
                "ACCOUNT_IDENTITY_PROVENANCE": account_identity_provenance,
                "RAW_RESPONSE_SHA256": body_digest,
                "ITEM_ID": "DETAILS_USDC_AVAILEQ",
                "FETCH_GROUP": "balance",
                "CONSUMER": PRODUCER_IDENTITY,
                "FRESHNESS_CLASSIFICATION": (
                    "FRESH_GET_THIS_SLICE" if get_ok else "NOT_TRUSTED_OR_FAILED"
                ),
                "AUTH_HEADER_PRESENCE": auth_presence,
                "GET_ERROR": get_error,
                "RETRY_USED": retry_used,
                "PRODUCTIVE_VENUE_CONTACT": productive_contact,
                "SECRET_VALUES_INCLUDED": False,
            }
        ]
    }
    summary = {
        "DOCUMENT_CLASS": SCHEMA_CLASS,
        "FRESH_GET_EXECUTED": claims["FRESH_GET_EXECUTED"],
        "GET_ENDPOINT": ENDPOINT,
        "HTTP_STATUS": claims["HTTP_STATUS"],
        "VENUE_CODE": code,
        "TRUSTED_AUTH_STATUS": trusted_auth,
        "USDC_DETAILS_ROW_STATUS": row_status,
        "RAW_USDC_AVAILEQ": raw_availeq,
        "PRODUCER_OUTPUT_STATUS": claims["PRODUCER_OUTPUT_STATUS"],
        "STEP_29P_RISK_ADMISSIBLE": claims["STEP_29P_RISK_ADMISSIBLE"],
        "POST_COUNT": "0",
        "SECRET_VALUES_INCLUDED": False,
    }
    lineage = {
        "schema_class": SCHEMA_CLASS,
        "parent_cu_pack": (
            "evidence/ops/full_core_current_productive_29p_risk_capital_model_v1/2026-09-15T120300Z"
        ),
        "genesis_id": EXPECTED_GENESIS_ID,
        "persist_as_of": package_finished,
        "sealed_legacy_census_reopened": FALSE_TOKEN,
        "fresh_get_executed": claims["FRESH_GET_EXECUTED"],
        "value_ephemeral": TRUE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "trading_signal_authority_unchanged": TRUE_TOKEN,
        "eq_not_elevated_to_source": TRUE_TOKEN,
        "fallback_chain_still_forbidden": TRUE_TOKEN,
        "account_level_avail_eq_still_forbidden": TRUE_TOKEN,
        "legacy_census_not_reopened": TRUE_TOKEN,
        "single_selected_future_unchanged": TRUE_TOKEN,
        "max_positions_one_unchanged": TRUE_TOKEN,
        "live_not_enabled": TRUE_TOKEN,
        "no_post": TRUE_TOKEN,
    }
    for item in (claims, gets, summary, lineage, protected, snapshot):
        _assert_no_secrets(item)
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / GETS_FILE, payload=gets)
    _persist_json(path=store / SNAPSHOT_FILE, payload=snapshot)
    _persist_json(path=store / SUMMARY_FILE, payload=summary)
    _persist_json(path=store / LINEAGE_FILE, payload=lineage)
    _persist_json(path=store / PROTECTED_FILE, payload=protected)
    _persist_json(
        path=store / P01_FILE,
        payload={
            "decision_state": p01_decision.decision_state,
            "reason_code": p01_decision.reason_code,
            "authorized_reduction_amount": p01_decision.authorized_reduction_amount,
            "ready": p01_decision.ready,
            "runtime_instance_present": FALSE_TOKEN,
            "inferred_from_venue_fields": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=store / PRODUCER_FILE,
        payload={
            "produced": output.produced,
            "value": output.value,
            "producer_identity": output.producer_identity,
            "algebra_id": output.algebra_id,
            "u04_applied": output.u04_applied,
            "p01_applied": output.p01_applied,
            "double_counting_guard": output.double_counting_guard,
            "reason_codes": list(output.reason_codes),
            "input_set_digest": output.input_set_digest,
        },
    )
    _persist_json(
        path=store / ADMISSIBILITY_FILE,
        payload={
            "risk_admissible": admissibility.risk_admissible,
            "reason_codes": list(admissibility.reason_codes),
            "value_binding_status": binding_status,
            "typed_account_equity_source_field": claim.typed_account_equity_source_field,
            "live_account_bound_status": claim.live_account_bound_status,
            "fresh_pretrade_get_status": claim.fresh_pretrade_get_status,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    verify_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductive29PFreshGetPersistResultV1(
        store_root=str(store),
        fresh_get_executed=str(claims["FRESH_GET_EXECUTED"]),
        http_status=str(claims["HTTP_STATUS"]),
        venue_code=code,
        trusted_auth_status=trusted_auth,
        usdc_details_row_status=row_status,
        raw_usdc_availeq=raw_availeq,
        producer_output_status=str(claims["PRODUCER_OUTPUT_STATUS"]),
        producer_output_value_usdc=output.value,
        producer_output_digest=output.input_set_digest,
        step_29p_value_binding_status=binding_status,
        step_29p_risk_admissible=str(claims["STEP_29P_RISK_ADMISSIBLE"]),
        p01_applicability=p01_decision.decision_state,
        p01_status=str(p01_decision.reason_code or REASON_MISSING),
        u04_subtracted=output.u04_applied,
        forbidden_fallback_used=fallback_used,
        eq_used_as_source=eq_used,
        post_count="0",
        evidence_manifest=str(manifest),
        manifest_verify_rc=int(verify_rc),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--bound-origin-main-sha", required=True)
    parser.add_argument("--vault-file", default="")
    parser.add_argument("--expected-account-identity", default=REUSED_BINDING_ACCOUNT_SCOPE)
    parser.add_argument("--execute-get", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = execute_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_v1(
            owner_go=args.owner_go,
            origin_main_sha=args.bound_origin_main_sha,
            vault_file=args.vault_file or None,
            expected_account_identity=args.expected_account_identity,
            execute_get=bool(args.execute_get),
        )
    except CurrentProductive29PFreshGetError as exc:
        print(f"FRESH_USDC_AVAILEQ_GET_FAIL_CLOSED:{exc}")
        return 2
    print("FRESH_USDC_AVAILEQ_GET_RESULT=")
    print(
        json.dumps(
            {
                "store_root": result.store_root,
                "fresh_get_executed": result.fresh_get_executed,
                "http_status": result.http_status,
                "venue_code": result.venue_code,
                "trusted_auth_status": result.trusted_auth_status,
                "usdc_details_row_status": result.usdc_details_row_status,
                "raw_usdc_availeq": result.raw_usdc_availeq,
                "producer_output_status": result.producer_output_status,
                "producer_output_value_usdc": result.producer_output_value_usdc,
                "step_29p_risk_admissible": result.step_29p_risk_admissible,
                "p01_status": result.p01_status,
                "manifest_verify_rc": result.manifest_verify_rc,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
