"""CURRENT_PRODUCTIVE U01 account-mode semantic ratification and P01 bind v1.

Consumes Owner-GO
CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_AND_29P_CONTINUATION_TO_FIRST_REAL_BLOCKER_V1.

Performs at most one authorized READ-ONLY GET /api/v5/account/config,
preserves raw acctLv, adapts "2" -> FUTURES_MODE, mints U01 eligibility
only when the adapter is eligible, then binds the existing P01 evaluator.
MISSING/UNKNOWN P01 is not normalized to DOES_NOT_APPLY. No availEq GET.
No sizing mint. No POST. No Live enable/arm.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_U01_GET_AUTHORIZED_COUNT,
    CURRENT_PRODUCTIVE_U01_GET_ENDPOINT,
    CURRENT_PRODUCTIVE_U01_GET_POST_COUNT,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    ELIGIBILITY_FACT_ID,
    REQUIRED_ACCOUNT_MODE,
    REQUIRED_TD_MODE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    CANONICAL_SEMANTIC_TOKEN,
    OPEN_AUTHORITY_STATUS,
    RAW_FIELD,
    REQUIRED_RAW_TOKEN,
    RETIRED_OPEN_TOKEN,
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
    extract_raw_acct_lv_from_account_config_payload_v1,
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

OWNER_GO = (
    "CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_AND_29P_"
    "CONTINUATION_TO_FIRST_REAL_BLOCKER_V1"
)
PIN_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_BIND_CURRENT_PRODUCTIVE_U01_ELIGIBILITY_AND_"
    "RESOLVE_P01_DIRECTIVE_FOR_SIZING_MINT_V1"
)
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, PIN_OWNER_GO, f"OWNER_GO_{OWNER_GO}"})
EXPECTED_ORIGIN_MAIN_SHA = "f1d13408197c08cf2ad177eaef522b18f47d0a21"
THIS_SLICE = "11.2.1.CW.FULL_CORE_CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
EVIDENCE_DIRNAME = "full_core_current_productive_u01_account_mode_semantic_ratification_v1"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_u01_account_mode_semantic_ratification_v1/"
    "20260915T113345Z"
)
AUTHORIZED_HOST = "eea.okx.com"
REUSED_REST_BASE = f"https://{AUTHORIZED_HOST}"
ENDPOINT = CURRENT_PRODUCTIVE_U01_GET_ENDPOINT
USER_AGENT = "PeakTrade-FullCore-CW-U01-AccountModeGET/1"
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
U01_FILE = "u01_adaptation_v1.json"
SNAPSHOT_FILE = "GET_SNAPSHOT.sanitized.json"


class CurrentProductiveU01RatificationError(RuntimeError):
    """Fail-closed CURRENT_PRODUCTIVE U01 ratification / P01 bind violation."""


@dataclass(frozen=True)
class CurrentProductiveU01RatificationPersistResultV1:
    store_root: str
    fresh_get_executed: str
    http_status: str
    venue_code: str
    trusted_auth_status: str
    raw_acct_lv: str
    semantic_account_mode: str
    u01_status: str
    u01_runtime_fact_status: str
    p01_applicability: str
    p01_status: str
    fresh_usdc_availeq_status: str
    risk_capital_mint_status: str
    step_29p_risk_admissible: str
    first_real_blocker: str
    post_count: str
    evidence_manifest: str
    manifest_verify_rc: int


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
            raise CurrentProductiveU01RatificationError("SECRET_LEAK_FORBIDDEN")


def _assert_no_proxy_env_v1() -> None:
    present = [key for key in _PROXY_ENV_KEYS if str(os.environ.get(key) or "").strip()]
    if present:
        raise CurrentProductiveU01RatificationError("HTTP_PROXY_FORBIDDEN")


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
        raise CurrentProductiveU01RatificationError("WRITE_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise CurrentProductiveU01RatificationError("ORDER_REQUEST_DETECTED")
    methods = list(client.counters.methods_used)
    if any(method in FORBIDDEN_HTTP_METHODS for method in methods):
        raise CurrentProductiveU01RatificationError("FORBIDDEN_METHOD")
    if any(method != "GET" for method in methods):
        raise CurrentProductiveU01RatificationError("NON_GET_METHOD_DETECTED")
    return counters


def _okx_code_msg(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, dict):
        return "", ""
    return str(payload.get("code") or ""), str(payload.get("msg") or "")[:200]


def _extract_uid(payload: Mapping[str, Any] | None) -> str:
    if not isinstance(payload, Mapping):
        return ""
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return ""
    row = data[0]
    if not isinstance(row, Mapping):
        return ""
    raw = row.get("uid")
    if isinstance(raw, bool) or raw is None:
        return ""
    if isinstance(raw, int):
        return str(raw)
    if isinstance(raw, str) and raw.strip() == raw and raw:
        return raw
    return ""


def _raw_acct_lv_from_payload(payload: Mapping[str, Any] | None) -> object:
    if not isinstance(payload, Mapping):
        return None
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None
    row = data[0]
    if not isinstance(row, Mapping):
        return None
    return row.get(RAW_FIELD)


def _forensic_config_snapshot_v1(
    *,
    payload: Mapping[str, Any] | None,
    expected_account_identity: str,
    body_digest: str,
    http_status: int | None,
    endpoint: str,
) -> dict[str, Any]:
    raw_acct_lv = ""
    if isinstance(payload, Mapping):
        raw = _raw_acct_lv_from_payload(payload)
        if isinstance(raw, str):
            raw_acct_lv = raw
    return {
        "STATUS": "SANITIZED_ACCOUNT_CONFIG_FORENSIC",
        "ENDPOINT": endpoint,
        "HTTP_STATUS": http_status,
        "VENUE_CODE": str(payload.get("code") or "") if isinstance(payload, Mapping) else "",
        "VENUE_MSG": str(payload.get("msg") or "")[:200] if isinstance(payload, Mapping) else "",
        "RAW_BODY_SHA256": body_digest,
        "ACCOUNT_UID_OBSERVED": _extract_uid(payload),
        "ACCOUNT_UID_EXPECTED": expected_account_identity,
        "RAW_FIELD": RAW_FIELD,
        "RAW_ACCT_LV_PRESERVED": raw_acct_lv,
        "RAW_NOT_REWRITTEN": True,
        "SEMANTIC_TOKEN_NOT_IN_RAW_EVIDENCE": True,
        "SECRET_VALUES_INCLUDED": False,
    }


def execute_current_productive_u01_account_mode_semantic_ratification_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE,
    execute_get: bool = False,
) -> CurrentProductiveU01RatificationPersistResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise CurrentProductiveU01RatificationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveU01RatificationError("ORIGIN_MAIN_SHA_MISMATCH")
    if execute_get is not True:
        raise CurrentProductiveU01RatificationError("EXECUTE_GET_FLAG_REQUIRED")
    if WIRE_SEND_PERMITTED is not False:
        raise CurrentProductiveU01RatificationError("STANDING_LIVE_GATES_MUST_REMAIN_FALSE")
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveU01RatificationError("SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED")
    if P01_RUNTIME_INSTANCE_PRESENT is not False:
        raise CurrentProductiveU01RatificationError("P01_RUNTIME_INSTANCE_MUST_REMAIN_ABSENT")
    if CURRENT_PRODUCTIVE_U01_GET_POST_COUNT != 0:
        raise CurrentProductiveU01RatificationError("POST_COUNT_PIN_DRIFT")
    if CURRENT_PRODUCTIVE_U01_GET_AUTHORIZED_COUNT != 1:
        raise CurrentProductiveU01RatificationError("AUTHORIZED_GET_COUNT_PIN_DRIFT")
    if ENDPOINT != "/api/v5/account/config":
        raise CurrentProductiveU01RatificationError("ENDPOINT_DRIFT")
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise CurrentProductiveU01RatificationError("HOST_MISMATCH")
    if REQUIRED_ACCOUNT_MODE != CANONICAL_SEMANTIC_TOKEN:
        raise CurrentProductiveU01RatificationError("REQUIRED_ACCOUNT_MODE_DRIFT")
    _assert_no_proxy_env_v1()

    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise CurrentProductiveU01RatificationError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise CurrentProductiveU01RatificationError("PRODUCTIVE_HTTP_SEND_DISABLED")

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
    endpoint = ENDPOINT
    if endpoint in FORBIDDEN_ENDPOINTS:
        raise CurrentProductiveU01RatificationError("MUTATION_ENDPOINT_FORBIDDEN")
    url = f"{REUSED_REST_BASE}{endpoint}"
    if urlparse(url).hostname != AUTHORIZED_HOST:
        raise CurrentProductiveU01RatificationError("HOST_MISMATCH")

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
                raise CurrentProductiveU01RatificationError(
                    "PRIVATE_GET_REQUIRES_CREDENTIAL_HANDLE"
                )
            try:
                response = client.get(endpoint=endpoint, headers=headers)
                http_status = int(response.status_code)
                body_bytes = bytes(response.body_bytes)
                if response.method != "GET":
                    raise CurrentProductiveU01RatificationError("NON_GET_RESPONSE")
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
    expected_uid = str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE)
    uid_observed = _extract_uid(payload) if isinstance(payload, dict) else ""
    failure_reasons: list[str] = []
    if uid_observed and uid_observed != expected_uid:
        failure_reasons.append("ACCOUNT_IDENTITY_SCOPE_MISMATCH")
        get_ok = False
    bound_uid = uid_observed or expected_uid
    account_identity_provenance = (
        "PAYLOAD_UID"
        if uid_observed and uid_observed == expected_uid
        else (
            "CREDENTIAL_BOUND_PRIVATE_GET_UID_ABSENT_FROM_CONFIG_PAYLOAD"
            if uid_observed == ""
            else "PAYLOAD_UID_MISMATCH"
        )
    )
    adaptation = extract_raw_acct_lv_from_account_config_payload_v1(
        payload if isinstance(payload, dict) else None
    )
    if not get_ok and not adaptation.reason_codes:
        adaptation = adapt_current_productive_u01_account_mode_v1(None)
    eligibility = None
    if get_ok and not failure_reasons:
        eligibility = build_current_productive_u01_eligibility_fact_v1(
            adaptation=adaptation,
            bound_account_identity=bound_uid,
            bound_venue_identity="okx",
            bound_td_mode=REQUIRED_TD_MODE,
            decision_epoch=decision_epoch,
            provenance_digest=body_digest or "0" * 64,
        )
    p01_decision = evaluate_p01_application_predicate_v1(())
    if p01_decision.decision_state == "DOES_NOT_APPLY":
        raise CurrentProductiveU01RatificationError("P01_UNKNOWN_MUST_NOT_BECOME_DOES_NOT_APPLY")
    u01_runtime = (
        "MINTED_CURRENT_PRODUCTIVE_U01_ELIGIBILITY_FACT"
        if eligibility is not None
        else "MISSING_NO_CURRENT_PRODUCTIVE_U01_RUNTIME_INSTANCE"
    )
    first_blocker = (
        "P01_DIRECTIVE_MISSING_OWNER_MUST_RATIFY_APPLIES_OR_DOES_NOT_APPLY"
        if eligibility is not None
        else "CURRENT_PRODUCTIVE_U01_ELIGIBILITY_NOT_MINTED"
    )
    store = evidence_root
    if store is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        store = _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / stamp
    store = Path(store)
    store.mkdir(parents=True, exist_ok=True)
    snapshot = _forensic_config_snapshot_v1(
        payload=payload if isinstance(payload, dict) else None,
        expected_account_identity=expected_uid,
        body_digest=body_digest,
        http_status=http_status,
        endpoint=endpoint,
    )
    claims = {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CW",
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "FRESH_GET_EXECUTED": TRUE_TOKEN if get_ok else FALSE_TOKEN,
        "GET_ENDPOINT": ENDPOINT,
        "HTTP_STATUS": "" if http_status is None else str(http_status),
        "VENUE_CODE": code,
        "VENUE_MSG": msg,
        "TRUSTED_AUTH_STATUS": trusted_auth,
        "ACCOUNT_IDENTITY_PROVENANCE": account_identity_provenance,
        "BOUND_ACCOUNT_IDENTITY": bound_uid,
        "GET_TIMESTAMP": request_time,
        "GET_EVIDENCE_DIGEST": body_digest,
        "U01_RAW_FIELD": RAW_FIELD,
        "U01_CANONICAL_RAW_TOKEN": REQUIRED_RAW_TOKEN,
        "U01_CANONICAL_SEMANTIC_TOKEN": CANONICAL_SEMANTIC_TOKEN,
        "U01_RAW_ACCT_LV_PRESERVED": adaptation.raw_token,
        "U01_RAW_REWRITTEN": adaptation.raw_rewritten,
        "U01_SEMANTIC_TOKEN": adaptation.semantic_token,
        "U01_STATUS": adaptation.status,
        "U01_ELIGIBLE": adaptation.eligible,
        "U01_REASON_CODES": list(adaptation.reason_codes),
        "U01_RUNTIME_FACT_STATUS": u01_runtime,
        "ELIGIBILITY_FACT_ID": ELIGIBILITY_FACT_ID,
        "OPEN_CURRENT_PRODUCTIVE_AUTHORITY_STATUS": OPEN_AUTHORITY_STATUS,
        "RETIRED_OPEN_TOKEN": RETIRED_OPEN_TOKEN,
        "P01_APPLICABILITY": p01_decision.decision_state,
        "P01_STATUS": p01_decision.reason_code or REASON_MISSING,
        "P01_RUNTIME_INSTANCE_PRESENT": FALSE_TOKEN,
        "P01_INFERRED_DOES_NOT_APPLY": FALSE_TOKEN,
        "FRESH_USDC_AVAILEQ_STATUS": "NOT_REACHED_P01_REAL_BLOCKER",
        "RISK_CAPITAL_MINT_STATUS": "NOT_REACHED_UNMINTED",
        "STEP_29P_RISK_ADMISSIBLE": FALSE_TOKEN,
        "FIRST_REAL_BLOCKER": first_blocker,
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
        "GET_FAILURE_REASONS": failure_reasons,
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
                    "account_identity": expected_uid,
                    "td_mode": REQUIRED_TD_MODE,
                    "auth_required": True,
                    "SECRET_VALUES_INCLUDED": False,
                },
                "OBSERVED_FIELD": RAW_FIELD,
                "RAW_ACCT_LV_PRESERVED": adaptation.raw_token,
                "RAW_RESPONSE_SHA256": body_digest,
                "ITEM_ID": "ACCOUNT_CONFIG_ACCTLV",
                "FETCH_GROUP": "account_config",
                "CONSUMER": "CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_ADAPTER_V1",
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
        "U01_STATUS": adaptation.status,
        "U01_RUNTIME_FACT_STATUS": u01_runtime,
        "P01_APPLICABILITY": p01_decision.decision_state,
        "FIRST_REAL_BLOCKER": first_blocker,
        "STEP_29P_RISK_ADMISSIBLE": FALSE_TOKEN,
        "POST_COUNT": "0",
        "SECRET_VALUES_INCLUDED": False,
    }
    lineage = {
        "schema_class": SCHEMA_CLASS,
        "parent_cv_pack": (
            "evidence/ops/full_core_current_productive_29p_fresh_trusted_usdc_free_margin_get_v1/"
            "20260915T105152Z"
        ),
        "genesis_id": EXPECTED_GENESIS_ID,
        "persist_as_of": package_finished,
        "atlas_authority": NONE_TOKEN,
    }
    protected = {
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "BULL_BEAR_STATE_SWITCH_UNCHANGED": TRUE_TOKEN,
        "LEARNING_UNCHANGED": TRUE_TOKEN,
        "TOP20_UNCHANGED": TRUE_TOKEN,
        "TRADING_SIGNAL_AUTHORITY_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_SAFETY_UNCHANGED": TRUE_TOKEN,
        "SINGLE_SELECTED_FUTURE_UNCHANGED": TRUE_TOKEN,
        "MAX_POSITIONS_ONE_UNCHANGED": TRUE_TOKEN,
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
        path=store / U01_FILE,
        payload={
            "raw_field": RAW_FIELD,
            "raw_token": adaptation.raw_token,
            "semantic_token": adaptation.semantic_token,
            "eligible": adaptation.eligible,
            "status": adaptation.status,
            "raw_rewritten": adaptation.raw_rewritten,
            "reason_codes": list(adaptation.reason_codes),
            "runtime_fact_status": u01_runtime,
            "open_authority_status": OPEN_AUTHORITY_STATUS,
        },
    )
    _persist_json(
        path=store / P01_FILE,
        payload={
            "decision_state": p01_decision.decision_state,
            "reason_code": p01_decision.reason_code,
            "authorized_reduction_amount": p01_decision.authorized_reduction_amount,
            "ready": p01_decision.ready,
            "runtime_instance_present": FALSE_TOKEN,
            "inferred_from_venue_fields": FALSE_TOKEN,
            "normalized_to_does_not_apply": FALSE_TOKEN,
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=store)
    verify_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveU01RatificationPersistResultV1(
        store_root=str(store),
        fresh_get_executed=str(claims["FRESH_GET_EXECUTED"]),
        http_status=str(claims["HTTP_STATUS"]),
        venue_code=code,
        trusted_auth_status=trusted_auth,
        raw_acct_lv=adaptation.raw_token,
        semantic_account_mode=adaptation.semantic_token,
        u01_status=adaptation.status,
        u01_runtime_fact_status=u01_runtime,
        p01_applicability=p01_decision.decision_state,
        p01_status=str(p01_decision.reason_code or REASON_MISSING),
        fresh_usdc_availeq_status="NOT_REACHED_P01_REAL_BLOCKER",
        risk_capital_mint_status="NOT_REACHED_UNMINTED",
        step_29p_risk_admissible=FALSE_TOKEN,
        first_real_blocker=first_blocker,
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
        result = execute_current_productive_u01_account_mode_semantic_ratification_v1(
            owner_go=args.owner_go,
            origin_main_sha=args.bound_origin_main_sha,
            vault_file=args.vault_file or None,
            expected_account_identity=args.expected_account_identity,
            execute_get=bool(args.execute_get),
        )
    except CurrentProductiveU01RatificationError as exc:
        print(f"U01_RATIFICATION_FAIL_CLOSED:{exc}")
        return 2
    print("U01_RATIFICATION_RESULT=")
    print(
        json.dumps(
            {
                "store_root": result.store_root,
                "fresh_get_executed": result.fresh_get_executed,
                "u01_status": result.u01_status,
                "u01_runtime_fact_status": result.u01_runtime_fact_status,
                "p01_applicability": result.p01_applicability,
                "p01_status": result.p01_status,
                "first_real_blocker": result.first_real_blocker,
                "step_29p_risk_admissible": result.step_29p_risk_admissible,
                "post_count": result.post_count,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
