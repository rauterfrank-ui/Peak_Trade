"""CURRENT_PRODUCTIVE P01 policy replacement and 29P continuation v1.

Consumes Owner-GO CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_AND_29P_CONTINUATION_V1.

Binds the standing DOES_NOT_APPLY P01 policy, reobserves same-epoch U01
via READ-ONLY /api/v5/account/config, observes details[ccy=USDC].availEq
via READ-ONLY /api/v5/account/balance, mints CU sizing when inputs are
complete, and reevaluates STEP-29P predicates. No POST. No Live enable/arm.

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
    CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
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
    OWNER_GO as POLICY_OWNER_GO,
    POLICY_FORMULA,
    bind_current_productive_p01_policy_fact_v1,
    current_productive_p01_coverage_matrix_v1,
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


def _fail_closed_credential_unavailable_v1(*_a, **_k):
    raise RuntimeError("CREDENTIAL_HANDLE_FAIL_CLOSED")


OWNER_GO = POLICY_OWNER_GO
PIN_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_RATIFY_P01_APPLIES_WITH_AMOUNT_OR_DOES_NOT_APPLY_"
    "FOR_CURRENT_PRODUCTIVE_SIZING_V1"
)
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, PIN_OWNER_GO, f"OWNER_GO_{OWNER_GO}"})
EXPECTED_ORIGIN_MAIN_SHA = "3568168b7b68c6619906be6533209c0cca32501c"
THIS_SLICE = "11.2.1.CX.FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_AND_29P_CONTINUATION"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_AND_29P_CONTINUATION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
EVIDENCE_DIRNAME = "full_core_current_productive_p01_policy_replacement_and_29p_continuation_v1"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_p01_policy_replacement_and_29p_continuation_v1/"
    "20260915T120000Z"
)
AUTHORIZED_HOST = "eea.okx.com"
REUSED_REST_BASE = f"https://{AUTHORIZED_HOST}"
USER_AGENT = "PeakTrade-FullCore-CX-P01-Policy-29P/1"
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


class CurrentProductiveP01PolicyContinuationError(RuntimeError):
    """Fail-closed CURRENT_PRODUCTIVE P01 policy continuation violation."""


@dataclass(frozen=True)
class CurrentProductiveP01PolicyContinuationResultV1:
    store_root: str
    p01_applicability: str
    p01_status: str
    p01_directive_status: str
    u01_status: str
    fresh_usdc_availeq_status: str
    raw_usdc_availeq: str
    risk_capital_mint_status: str
    producer_output_value_usdc: str
    step_29p_risk_admissible: str
    first_real_blocker: str
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
            raise CurrentProductiveP01PolicyContinuationError("SECRET_LEAK_FORBIDDEN")


def _assert_no_proxy_env_v1() -> None:
    present = [key for key in _PROXY_ENV_KEYS if str(os.environ.get(key) or "").strip()]
    if present:
        raise CurrentProductiveP01PolicyContinuationError("HTTP_PROXY_FORBIDDEN")


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
        raise CurrentProductiveP01PolicyContinuationError("WRITE_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise CurrentProductiveP01PolicyContinuationError("ORDER_REQUEST_DETECTED")
    methods = list(client.counters.methods_used)
    if any(method in FORBIDDEN_HTTP_METHODS for method in methods):
        raise CurrentProductiveP01PolicyContinuationError("FORBIDDEN_METHOD")
    return counters


def _signed_get(
    *,
    client: LiveCanaryHttpClientV1,
    endpoint: str,
    productive: bool,
    handle: Any,
) -> tuple[int | None, bytes, dict[str, str], str, Any, str | None]:
    if endpoint in FORBIDDEN_ENDPOINTS:
        raise CurrentProductiveP01PolicyContinuationError("MUTATION_ENDPOINT_FORBIDDEN")
    url = f"{REUSED_REST_BASE}{endpoint}"
    if urlparse(url).hostname != AUTHORIZED_HOST:
        raise CurrentProductiveP01PolicyContinuationError("HOST_MISMATCH")
    request_time = _utc_now_iso_v1()
    headers = {"User-Agent": USER_AGENT}
    if handle is not None:
        headers = _fail_closed_credential_unavailable_v1(handle=handle, url=url, method="GET")
        headers["User-Agent"] = USER_AGENT
    elif productive:
        raise CurrentProductiveP01PolicyContinuationError("PRIVATE_GET_REQUIRES_CREDENTIAL_HANDLE")
    try:
        response = client.get(endpoint=endpoint, headers=headers)
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        if response.method != "GET":
            raise CurrentProductiveP01PolicyContinuationError("NON_GET_RESPONSE")
        if bool(response.redirect_followed):
            return http_status, body_bytes, headers, request_time, None, "REDIRECT_FOLLOWED"
        payload = parse_json_object_v1(body_bytes)
        return http_status, body_bytes, headers, request_time, payload, None
    except LiveCanaryHttpError as exc:
        return None, b"", headers, request_time, None, str(exc)[:200]
    except (ValueError, json.JSONDecodeError):
        return None, b"", headers, request_time, None, "MALFORMED_JSON"


def execute_current_productive_p01_policy_replacement_and_29p_continuation_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE,
    execute_get: bool = False,
) -> CurrentProductiveP01PolicyContinuationResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise CurrentProductiveP01PolicyContinuationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveP01PolicyContinuationError("ORIGIN_MAIN_SHA_MISMATCH")
    if execute_get is not True:
        raise CurrentProductiveP01PolicyContinuationError("EXECUTE_GET_FLAG_REQUIRED")
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveP01PolicyContinuationError("SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED")
    if P01_RUNTIME_INSTANCE_PRESENT is not False:
        raise CurrentProductiveP01PolicyContinuationError(
            "RECONSTRUCTION_P01_RUNTIME_INSTANCE_MUST_REMAIN_FALSE"
        )
    if CURRENT_PRODUCTIVE_U01_GET_ENDPOINT != "/api/v5/account/config":
        raise CurrentProductiveP01PolicyContinuationError("U01_ENDPOINT_DRIFT")
    if CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT != "/api/v5/account/balance":
        raise CurrentProductiveP01PolicyContinuationError("BALANCE_ENDPOINT_DRIFT")
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise CurrentProductiveP01PolicyContinuationError("HOST_MISMATCH")
    reject_direct_avail_eq_29p_claim_v1(claimed="false")
    missing = reject_missing_as_does_not_apply_v1()
    p01_decision = evaluate_current_productive_p01_policy_v1()
    if p01_decision.decision_state != CURRENT_PRODUCTIVE_P01_POLICY_DECISION:
        raise CurrentProductiveP01PolicyContinuationError("P01_POLICY_MUST_BE_DOES_NOT_APPLY")
    if missing.decision_state == CURRENT_PRODUCTIVE_P01_POLICY_DECISION:
        raise CurrentProductiveP01PolicyContinuationError("MISSING_MUST_NOT_BECOME_DOES_NOT_APPLY")
    _assert_no_proxy_env_v1()

    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise CurrentProductiveP01PolicyContinuationError("VAULT_FILE_REQUIRED")
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
            backend = _fail_closed_credential_unavailable_v1(vault_file=Path(str(vault_file)))
            handle = _fail_closed_credential_unavailable_v1(
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
            _fail_closed_credential_unavailable_v1(handle)
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
    if balance_ok and isinstance(balance_payload, dict):
        try:
            raw_obs = acquire_fresh_available_margin_observation_from_payload_v1(
                pretrade_decision_id=decision_epoch,
                payload=balance_payload,
                instrument_id=DEFAULT_INSTRUMENT_ID,
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
                instrument_id=DEFAULT_INSTRUMENT_ID,
                available_margin_domain=AVAILABLE_MARGIN_OUTPUT_DOMAIN,
                planned_td_mode=AVAILABLE_MARGIN_REQUIRED_TD_MODE,
            )
            if validated.selected_ccy != AVAILABLE_MARGIN_REQUIRED_CCY:
                raise CurrentProductiveP01PolicyContinuationError("SELECTED_CCY_NOT_USDC")
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
            CurrentProductiveP01PolicyContinuationError,
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
        raise CurrentProductiveP01PolicyContinuationError("U04_DOUBLE_COUNTING_GUARD_BROKEN")
    produced = output.produced == TRUE_TOKEN
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status=(
            FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
            if productive_contact and balance_ok
            else FreshPretradeGetStatusV1.MISSING.value
        ),
        live_account_bound_status=LiveAccountBoundStatusV1.MISSING.value,
        expected_instrument_id=DEFAULT_INSTRUMENT_ID,
        observed_instrument_id="",
        fresh_evidence_fetched=balance_ok,
        fresh_evidence_validated=observation is not None and balance_ok,
    )
    capital = evaluate_capital_admission_v1(
        claim=CapitalAdmissionClaimV1(
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            account_identity=bound_uid,
            instrument_id=DEFAULT_INSTRUMENT_ID,
            observed_capital_raw=output.value if produced else "",
            observed_field_name=PRODUCER_IDENTITY if produced else "",
            evidence_class="LIVE_TYPED",
            evidence_id=decision_epoch,
        )
        if produced
        else None,
        expected_account_identity=expected_uid,
        expected_instrument_id=DEFAULT_INSTRUMENT_ID,
        admission_context=ADMISSION_CONTEXT_LIVE,
    )
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    persist_classes = persist_class_fields_v1(admissibility)
    if persist_classes.get("STEP_29P_RISK_ADMISSIBLE") is True and produced is not True:
        raise CurrentProductiveP01PolicyContinuationError("29P_TRUE_WITHOUT_PRODUCER_OUTPUT")
    predicate_matrix = {
        "FRESH_EVIDENCE_FETCHED": persist_classes.get("FRESH_EVIDENCE_FETCHED"),
        "FRESH_EVIDENCE_VALIDATED": persist_classes.get("FRESH_EVIDENCE_VALIDATED"),
        "CAPITAL_EVIDENCE_COMPLETE": persist_classes.get("CAPITAL_EVIDENCE_COMPLETE"),
        "STEP_29P_RISK_ADMISSIBLE": persist_classes.get("STEP_29P_RISK_ADMISSIBLE"),
        "LIVE_ACCOUNT_BOUND_TRUSTED": claim.live_account_bound_status
        == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        "INSTRUMENT_SCOPE_BOUND": bool(claim.observed_instrument_id)
        and claim.expected_instrument_id == claim.observed_instrument_id,
        "CURRENCY_BOUND": claim.observed_currency == claim.expected_currency,
        "EQUITY_DIMENSION_BOUND": produced,
        "U04_NOT_SUBTRACTED": output.u04_applied == FALSE_TOKEN,
        "P01_DOES_NOT_APPLY": p01_decision.decision_state == "DOES_NOT_APPLY",
        "REASON_CODES": list(admissibility.reason_codes),
    }
    if produced:
        first_blocker = "LIVE_ACCOUNT_BOUND_NOT_TRUSTED_FOR_29P"
        if "STEP_29P_INSTRUMENT_SCOPE_MISSING" in admissibility.reason_codes:
            first_blocker = "LIVE_ACCOUNT_BOUND_NOT_TRUSTED_AND_STEP_29P_INSTRUMENT_SCOPE_MISSING"
    elif eligibility is None:
        first_blocker = "CURRENT_PRODUCTIVE_U01_ELIGIBILITY_NOT_MINTED"
    elif observation is None:
        first_blocker = "FRESH_USDC_AVAILEQ_NOT_OBSERVED"
    else:
        first_blocker = "RISK_CAPITAL_MINT_FAIL_CLOSED"
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = (
        Path(evidence_root)
        if evidence_root is not None
        else _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / run_id
    )
    store.mkdir(parents=True, exist_ok=True)
    coverage = [
        {
            "RISK_OR_CONSTRAINT": row.risk_or_constraint,
            "CURRENT_OWNER": row.current_owner,
            "ALREADY_REFLECTED_IN_AVAILEQ": row.already_reflected_in_availeq,
            "EXISTING_PEAK_TRADE_GATE": row.existing_peak_trade_gate,
            "P01_NEEDED": row.p01_needed,
            "EVIDENCE": row.evidence,
        }
        for row in current_productive_p01_coverage_matrix_v1()
    ]
    pins = current_productive_p01_policy_pins_v1()
    claims = {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": "CONSUMED",
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CX",
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": origin_main_sha,
        "P01_POLICY_DECISION": pins["P01_POLICY_DECISION"],
        "P01_DECISION_BASIS": pins["P01_DECISION_BASIS"],
        "P01_INDEPENDENT_SAFETY_FUNCTION": pins["P01_INDEPENDENT_SAFETY_FUNCTION"],
        "P01_FORMULA": POLICY_FORMULA,
        "P01_AUTHORIZED_INPUTS": AUTHORIZED_INPUTS,
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
        "STEP_29P_RISK_ADMISSIBLE": TRUE_TOKEN
        if persist_classes.get("STEP_29P_RISK_ADMISSIBLE") is True
        else FALSE_TOKEN,
        "29P_PREDICATE_MATRIX": predicate_matrix,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": "LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE",
        "NEXT_OWNER_GO_REQUIRED": (
            "OWNER_GO_REQUIRED_TO_BIND_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1"
        ),
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
    }
    summary = {
        "DOCUMENT_CLASS": SCHEMA_CLASS,
        "P01_POLICY_DECISION": "DOES_NOT_APPLY",
        "P01_DECISION_BASIS": pins["P01_DECISION_BASIS"],
        "FRESH_GET_EXECUTED": TRUE_TOKEN if config_ok and balance_ok else FALSE_TOKEN,
        "RISK_CAPITAL_MINT_STATUS": claims["RISK_CAPITAL_MINT_STATUS"],
        "STEP_29P_RISK_ADMISSIBLE": claims["STEP_29P_RISK_ADMISSIBLE"],
        "FIRST_REAL_BLOCKER": first_blocker,
        "POST_COUNT": "0",
        "SECRET_VALUES_INCLUDED": False,
    }
    lineage = {
        "PARENT_SECTIONS": ["11.2.1.CW", "11.2.1.CV", "11.2.1.CU", "11.2.1.AP"],
        "OWNER_GO": OWNER_GO,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "ATLAS_AUTHORITY": "NONE",
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
    }
    for payload in (claims, summary, lineage, protected, {"COVERAGE": coverage}):
        _assert_no_secrets(payload)
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "SUMMARY.json", payload=summary)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "coverage_matrix_v1.json", payload={"COVERAGE": coverage})
    _persist_json(
        path=store / "p01_resolution_v1.json",
        payload={
            "decision_state": p01_decision.decision_state,
            "reason_code": p01_decision.reason_code,
            "authorized_reduction_amount": p01_decision.authorized_reduction_amount,
            "ready": p01_decision.ready,
            "runtime_instance_present": FALSE_TOKEN,
            "normalized_from_missing": FALSE_TOKEN,
            "policy_evidence_ref": EVIDENCE_REF,
        },
    )
    _persist_json(
        path=store / "GETS.json",
        payload={
            "REQUESTS": [
                {
                    "ENDPOINT": CURRENT_PRODUCTIVE_U01_GET_ENDPOINT,
                    "METHOD": "GET",
                    "HTTP_STATUS": config_status,
                    "BODY_SHA256": config_digest,
                    "REQUEST_TIME": config_time,
                },
                {
                    "ENDPOINT": CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
                    "METHOD": "GET",
                    "HTTP_STATUS": balance_status,
                    "BODY_SHA256": balance_digest,
                    "REQUEST_TIME": balance_time,
                    "OBSERVED_FIELD": OBSERVATION_SURFACE,
                },
            ]
        },
    )
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveP01PolicyContinuationResultV1(
        store_root=str(store),
        p01_applicability=p01_decision.decision_state,
        p01_status=str(p01_decision.reason_code),
        p01_directive_status="RATIFIED_CURRENT_PRODUCTIVE_DOES_NOT_APPLY",
        u01_status=adaptation.status,
        fresh_usdc_availeq_status=str(claims["FRESH_USDC_AVAILEQ_STATUS"]),
        raw_usdc_availeq=raw_availeq,
        risk_capital_mint_status=str(claims["RISK_CAPITAL_MINT_STATUS"]),
        producer_output_value_usdc=output.value,
        step_29p_risk_admissible=str(claims["STEP_29P_RISK_ADMISSIBLE"]),
        first_real_blocker=first_blocker,
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
    result = execute_current_productive_p01_policy_replacement_and_29p_continuation_v1(
        owner_go=args.owner_go,
        origin_main_sha=args.origin_main_sha,
        vault_file=args.vault_file,
        evidence_root=Path(args.evidence_root) if args.evidence_root else None,
        execute_get=bool(args.execute_get),
    )
    print(_canonical_json(result.__dict__))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
