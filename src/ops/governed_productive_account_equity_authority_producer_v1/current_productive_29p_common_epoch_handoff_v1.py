"""CURRENT_PRODUCTIVE 29P common-epoch runtime composition handoff v1.

Shared EEA-CZ-tail composition: Cap-2.4 BoundInstrument consumer,
FullCoreProductiveReadOnlyGetTransportV1 + collect_fresh_pretrade_runtime_get_v1,
U01, USDC availEq observation, P01, producer, LiveAccountBound, instrument scope,
STEP-29P conjunction. AUTHORITY=NONE for new trading/selection/risk decisions.

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

from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionClaimV1,
    evaluate_capital_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    EXECUTION_ADMISSION_REMAINDER_CLOSED,
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
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    FreshPretradeRuntimeGetEvidenceV1,
    FullCoreFreshPretradeGetTransportV1,
    REQUIRED_GET_ITEM_SPECS,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_account_bound_v1 import (
    LiveAccountBoundEvidenceV1,
    evaluate_live_account_bound_v1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
    persist_class_fields_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED,
    CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF_CREATED,
    CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT,
    CURRENT_PRODUCTIVE_P01_POLICY_DECISION,
    CURRENT_PRODUCTIVE_U01_GET_ENDPOINT,
    P01_RUNTIME_INSTANCE_PRESENT,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    CurrentProductive29PCap24ProvenanceHandoffError,
    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    default_current_productive_cap24_runtime_state_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_live_account_bound_and_instrument_scope_v1 import (
    CurrentProductiveLabInstrumentScopeError,
    require_current_productive_29p_bound_instrument_v1,
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
    EVIDENCE_REF,
    bind_current_productive_p01_policy_fact_v1,
    evaluate_current_productive_p01_policy_v1,
    reject_missing_as_does_not_apply_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    CurrentProductiveU01AccountModeAdaptationV1,
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
    AVAILABLE_MARGIN_REQUIRED_CCY,
    account_balance_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

OWNER_GO = "CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF_TO_FIRST_REAL_BLOCKER_V1"
PIN_OWNER_GO = "OWNER_GO_REQUIRED_TO_COMPOSE_CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF_V1"
CAP24_SUPPLY_PIN_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_CURRENT_CAP24_BOUND_INSTRUMENT_INSTANCE_FOR_29P_"
    "WITHOUT_CANARY_IMPORT_OR_RESELECTION_V1"
)
ALLOWED_OWNER_GOS = frozenset(
    {
        OWNER_GO,
        PIN_OWNER_GO,
        CAP24_SUPPLY_PIN_OWNER_GO,
        f"OWNER_GO_{OWNER_GO}",
    }
)
EXPECTED_ORIGIN_MAIN_SHA = "ac227cf8be852b0987833c5eb354610ee37e3cf5"
THIS_SLICE = "11.2.1.EI.FULL_CORE_CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
EVIDENCE_DIRNAME = "full_core_current_productive_29p_common_epoch_handoff_v1"
HISTORICAL_PROVENANCE_REF_ONLY = (
    "evidence/ops/full_core_current_productive_29p_fresh_trusted_usdc_free_margin_get_v1/"
    "20260922T051458Z"
)
AUTHORIZED_HOST = "eea.okx.com"
MINIMUM_DEDUPLICATED_GET_COUNT = 7
MAXIMUM_AUTHORIZED_DEDUPLICATED_GET_COUNT = 7
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


class CurrentProductive29PCommonEpochHandoffError(RuntimeError):
    """Fail-closed CURRENT_PRODUCTIVE 29P common-epoch handoff violation."""


@dataclass(frozen=True)
class CurrentProductive29PCommonEpochHandoffResultV1:
    decision_epoch: str
    bound_instrument: BoundInstrumentV1
    get_evidence: FreshPretradeRuntimeGetEvidenceV1
    get_status: str
    lab: LiveAccountBoundEvidenceV1
    lab_status: str
    adaptation: CurrentProductiveU01AccountModeAdaptationV1
    eligibility: Any
    observation: CurrentProductiveUsdcFreeMarginObservationV1 | None
    raw_availeq: str
    p01_fact: Any
    output: Any
    produced: bool
    claim: Any
    capital: Any
    admissibility: Any
    evaluator_29p: bool
    observed_instrument_id: str
    instrument_bound: bool
    lab_trusted: bool
    deduplicated_get_count: int
    config_get_count: int
    balance_get_count: int
    bound_uid: str


@dataclass(frozen=True)
class CurrentProductive29PCommonEpochHandoffExecuteResultV1:
    store_root: str
    decision_epoch: str
    bound_instrument_id: str
    live_account_bound_status: str
    fresh_pretrade_get_status: str
    u01_status: str
    p01_status: str
    fresh_usdc_availeq_status: str
    risk_capital_mint_status: str
    instrument_scope_status: str
    step_29p_risk_admissible: str
    deduplicated_get_count: int
    first_real_blocker: str
    blocker_class: str
    post_count: str
    evidence_manifest: str
    manifest_verify_rc: int


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
            raise CurrentProductive29PCommonEpochHandoffError("SECRET_LEAK_FORBIDDEN")


def _assert_no_proxy_env_v1() -> None:
    present = [key for key in _PROXY_ENV_KEYS if str(os.environ.get(key) or "").strip()]
    if present:
        raise CurrentProductive29PCommonEpochHandoffError("HTTP_PROXY_FORBIDDEN")


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


def extract_usdc_details_availeq_from_balance_payload_v1(payload: Mapping[str, Any]) -> str:
    """CURRENT_PRODUCTIVE details[ccy=USDC].availEq from balance payload."""
    if str(payload.get("code") or "") != "0":
        raise CurrentProductive29PCommonEpochHandoffError("BALANCE_VENUE_CODE_NOT_ZERO")
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], Mapping):
        raise CurrentProductive29PCommonEpochHandoffError("BALANCE_DATA_MISSING")
    details = data[0].get("details")
    if not isinstance(details, list):
        raise CurrentProductive29PCommonEpochHandoffError("BALANCE_DETAILS_MISSING")
    usdc_rows = [
        item
        for item in details
        if isinstance(item, Mapping) and str(item.get("ccy") or "").strip() == "USDC"
    ]
    if len(usdc_rows) != 1:
        raise CurrentProductive29PCommonEpochHandoffError("USDC_DETAILS_ROW_NOT_EXACTLY_ONE")
    raw = "" if usdc_rows[0].get("availEq") is None else str(usdc_rows[0].get("availEq")).strip()
    if not raw:
        raise CurrentProductive29PCommonEpochHandoffError("USDC_AVAILEQ_EMPTY")
    try:
        value = Decimal(raw)
    except Exception as exc:
        raise CurrentProductive29PCommonEpochHandoffError("USDC_AVAILEQ_MALFORMED") from exc
    if value != value or value.is_infinite():
        raise CurrentProductive29PCommonEpochHandoffError("USDC_AVAILEQ_NON_FINITE")
    if value < 0:
        raise CurrentProductive29PCommonEpochHandoffError("USDC_AVAILEQ_NEGATIVE")
    return raw


def payload_from_fresh_get_transport_v1(
    transport: FullCoreFreshPretradeGetTransportV1,
    *,
    endpoint: str,
    auth_required: bool,
    decision_epoch: str,
) -> Any:
    result = transport.get(
        endpoint=endpoint,
        auth_required=auth_required,
        pretrade_decision_id=decision_epoch,
    )
    return result.payload


_ITEM_ID_TO_FETCH_GROUP = {spec.item_id: spec.fetch_group for spec in REQUIRED_GET_ITEM_SPECS}


def _count_get_budget_from_evidence_v1(
    *,
    get_evidence: FreshPretradeRuntimeGetEvidenceV1,
) -> tuple[int, int, int]:
    performed = [item for item in get_evidence.items if item.get_performed is True]
    groups = {_ITEM_ID_TO_FETCH_GROUP.get(item.item_id, item.endpoint_path) for item in performed}
    dedup = len(groups)
    config_groups = {
        _ITEM_ID_TO_FETCH_GROUP.get(item.item_id, item.endpoint_path)
        for item in performed
        if item.endpoint_path == ENDPOINT_ACCOUNT_CONFIG
    }
    balance_groups = {
        _ITEM_ID_TO_FETCH_GROUP.get(item.item_id, item.endpoint_path)
        for item in performed
        if item.endpoint_path in {ENDPOINT_ACCOUNT_BALANCE, account_balance_query_path_v1()}
    }
    return dedup, len(config_groups), len(balance_groups)


def enforce_deduplicated_get_budget_v1(
    *,
    deduplicated_get_count: int,
    config_get_count: int,
    balance_get_count: int,
) -> None:
    if deduplicated_get_count < MINIMUM_DEDUPLICATED_GET_COUNT:
        raise CurrentProductive29PCommonEpochHandoffError("GET_BUDGET_BELOW_MINIMUM")
    if deduplicated_get_count > MAXIMUM_AUTHORIZED_DEDUPLICATED_GET_COUNT:
        raise CurrentProductive29PCommonEpochHandoffError("GET_BUDGET_EXCEEDS_MAXIMUM")
    if config_get_count > 1:
        raise CurrentProductive29PCommonEpochHandoffError("CONFIG_GET_COUNT_EXCEEDS_ONE")
    if balance_get_count > 1:
        raise CurrentProductive29PCommonEpochHandoffError("BALANCE_GET_COUNT_EXCEEDS_ONE")


def _validate_decision_epoch_v1(decision_epoch: str) -> str:
    epoch = str(decision_epoch or "")
    if epoch == "" or epoch != epoch.strip():
        raise CurrentProductive29PCommonEpochHandoffError("DECISION_EPOCH_MALFORMED")
    return epoch


def compose_current_productive_29p_common_epoch_handoff_v1(
    *,
    decision_epoch: str,
    bound_instrument: BoundInstrumentV1 | None,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1,
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE,
    inst_type: str = "FUTURES",
    package_finished_iso: str | None = None,
    p01_decision_state: str | None = None,
) -> CurrentProductive29PCommonEpochHandoffResultV1:
    if CURRENT_PRODUCTIVE_29P_COMMON_EPOCH_HANDOFF_CREATED is not True:
        raise CurrentProductive29PCommonEpochHandoffError("COMMON_EPOCH_HANDOFF_NOT_CREATED")
    epoch = _validate_decision_epoch_v1(decision_epoch)
    try:
        bound = require_current_productive_29p_bound_instrument_v1(bound_instrument)
    except CurrentProductiveLabInstrumentScopeError as exc:
        raise CurrentProductive29PCommonEpochHandoffError(str(exc)) from exc
    if bound.venue_native_id == CANARY_DEFAULT_INSTRUMENT_ID:
        raise CurrentProductive29PCommonEpochHandoffError("CANARY_INSTRUMENT_AUTHORITY_IMPORTED")
    if fresh_get_transport is None:
        raise CurrentProductive29PCommonEpochHandoffError(
            "LIVE_ACCOUNT_BOUND_REQUIRES_TRUSTED_FRESH_GET"
        )
    p01_state = p01_decision_state
    if p01_state is None:
        p01_state = evaluate_current_productive_p01_policy_v1().decision_state
    if p01_state != CURRENT_PRODUCTIVE_P01_POLICY_DECISION:
        raise CurrentProductive29PCommonEpochHandoffError("P01_POLICY_MUST_BE_DOES_NOT_APPLY")

    package_finished = package_finished_iso or _utc_now_iso_v1()
    expected_uid = str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE)

    get_evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id=epoch,
        instrument_id=bound.venue_native_id,
        td_mode=REQUIRED_TD_MODE,
        limit_px="",
        inst_type=inst_type,
        transport=fresh_get_transport,
        require_collection=True,
    )
    dedup_count, config_count, balance_count = _count_get_budget_from_evidence_v1(
        get_evidence=get_evidence
    )
    enforce_deduplicated_get_budget_v1(
        deduplicated_get_count=dedup_count,
        config_get_count=config_count,
        balance_get_count=balance_count,
    )
    get_status = str(get_evidence.evidence_status or "")

    lab = evaluate_live_account_bound_v1(
        get_evidence=get_evidence,
        expected_account_identity=expected_uid,
        expected_instrument_id=bound.venue_native_id,
        expected_td_mode=REQUIRED_TD_MODE,
    )
    lab_status = lab.evidence_status

    payloads = getattr(fresh_get_transport, "payloads_by_path", {}) or {}
    config_payload = payloads.get(ENDPOINT_ACCOUNT_CONFIG)
    balance_payload = payloads.get(ENDPOINT_ACCOUNT_BALANCE)
    if config_payload is None or balance_payload is None:
        config_payload = config_payload or payload_from_fresh_get_transport_v1(
            fresh_get_transport,
            endpoint=ENDPOINT_ACCOUNT_CONFIG,
            auth_required=True,
            decision_epoch=epoch,
        )
        balance_payload = balance_payload or payload_from_fresh_get_transport_v1(
            fresh_get_transport,
            endpoint=account_balance_query_path_v1(),
            auth_required=True,
            decision_epoch=epoch,
        )

    uid_config = _extract_uid(config_payload if isinstance(config_payload, dict) else None)
    uid_balance = _extract_uid(balance_payload if isinstance(balance_payload, dict) else None)
    bound_uid = uid_config or uid_balance or expected_uid

    if isinstance(config_payload, dict):
        adaptation = extract_raw_acct_lv_from_account_config_payload_v1(config_payload)
    else:
        adaptation = adapt_current_productive_u01_account_mode_v1(None)

    eligibility = None
    if adaptation.status == "ELIGIBLE" and isinstance(config_payload, dict):
        eligibility = build_current_productive_u01_eligibility_fact_v1(
            adaptation=adaptation,
            bound_account_identity=bound_uid,
            bound_venue_identity="okx",
            bound_td_mode=REQUIRED_TD_MODE,
            decision_epoch=epoch,
            provenance_digest=_sha256_text(_canonical_json(config_payload)),
        )

    observation = None
    raw_availeq = ""
    if isinstance(balance_payload, dict):
        try:
            raw_availeq = extract_usdc_details_availeq_from_balance_payload_v1(balance_payload)
            observation = CurrentProductiveUsdcFreeMarginObservationV1(
                fact_id=OBSERVATION_FACT_ID,
                surface=OBSERVATION_SURFACE,
                value=raw_availeq,
                settlement_currency=AVAILABLE_MARGIN_REQUIRED_CCY,
                selected_ccy=AVAILABLE_MARGIN_REQUIRED_CCY,
                bound_account_identity=bound_uid,
                bound_venue_identity="okx",
                bound_td_mode=REQUIRED_TD_MODE,
                decision_epoch=epoch,
                observed_at_as_of=package_finished,
                age_seconds=_age_seconds(
                    observed_at_as_of=package_finished, now_iso=package_finished
                ),
                freshness_max_age=str(NUMERIC_EQUITY_TTL_SECONDS),
                provenance_digest=_sha256_text(_canonical_json(balance_payload)),
                already_net_of_in_use=TRUE_TOKEN,
                account_level_avail_eq_used=FALSE_TOKEN,
                fallback_chain_used=FALSE_TOKEN,
            )
        except (
            CurrentProductive29PCommonEpochHandoffError,
            TypeError,
            ValueError,
            KeyError,
        ):
            observation = None
            raw_availeq = ""

    if observation is not None and observation.decision_epoch != epoch:
        raise CurrentProductive29PCommonEpochHandoffError("EPOCH_MISMATCH_OBSERVATION")
    if eligibility is not None and eligibility.decision_epoch != epoch:
        raise CurrentProductive29PCommonEpochHandoffError("EPOCH_MISMATCH_U01")

    p01_fact = None
    if observation is not None:
        p01_fact = bind_current_productive_p01_policy_fact_v1(
            bound_account_identity=observation.bound_account_identity,
            bound_venue_identity=observation.bound_venue_identity,
            bound_td_mode=observation.bound_td_mode,
            decision_epoch=observation.decision_epoch,
            observed_at_as_of=observation.observed_at_as_of,
            age_seconds=observation.age_seconds,
            freshness_max_age=observation.freshness_max_age,
            provenance_digest=_sha256_text(
                _canonical_json(
                    {
                        "policy": EVIDENCE_REF,
                        "epoch": observation.decision_epoch,
                        "account": observation.bound_account_identity,
                        "instrument": bound.venue_native_id,
                    }
                )
            ),
        )

    output = produce_current_productive_29p_risk_capital_v1(
        observation=observation,
        p01=p01_fact,
        eligibility=eligibility,
        eq_target=None,
        u04=None,
        restart_from_kind_set=FALSE_TOKEN,
    )
    produced = output.produced == TRUE_TOKEN
    lab_trusted = lab_status == LiveAccountBoundStatusV1.TRUSTED_PRESENT.value
    observed_instrument_id = ""
    if lab.observed_inst_ids == (bound.venue_native_id,):
        observed_instrument_id = bound.venue_native_id
    elif lab.observed_inst_ids:
        observed_instrument_id = ""
    instrument_bound = (
        bool(observed_instrument_id)
        and observed_instrument_id == bound.venue_native_id
        and bound.selection_state == STATE_SELECTED_ACTIVE
    )

    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status=get_status,
        live_account_bound_status=lab_status,
        expected_instrument_id=bound.venue_native_id,
        observed_instrument_id=observed_instrument_id,
        fresh_evidence_fetched=get_status != FreshPretradeGetStatusV1.MISSING.value,
        fresh_evidence_validated=(
            observation is not None and get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
        ),
    )
    capital = evaluate_capital_admission_v1(
        claim=CapitalAdmissionClaimV1(
            source_class=CAPITAL_SOURCE_OBSERVED_VENUE,
            account_identity=bound_uid,
            instrument_id=bound.venue_native_id,
            observed_capital_raw=output.value if produced else "",
            observed_field_name=PRODUCER_IDENTITY if produced else "",
            evidence_class="LIVE_TYPED",
            evidence_id=epoch,
        )
        if produced
        else None,
        expected_account_identity=expected_uid,
        expected_instrument_id=bound.venue_native_id,
        admission_context=ADMISSION_CONTEXT_LIVE,
    )
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    persist_classes = persist_class_fields_v1(admissibility)
    evaluator_29p = persist_classes.get("STEP_29P_RISK_ADMISSIBLE") is True

    return CurrentProductive29PCommonEpochHandoffResultV1(
        decision_epoch=epoch,
        bound_instrument=bound,
        get_evidence=get_evidence,
        get_status=get_status,
        lab=lab,
        lab_status=lab_status,
        adaptation=adaptation,
        eligibility=eligibility,
        observation=observation,
        raw_availeq=raw_availeq,
        p01_fact=p01_fact,
        output=output,
        produced=produced,
        claim=claim,
        capital=capital,
        admissibility=admissibility,
        evaluator_29p=evaluator_29p,
        observed_instrument_id=observed_instrument_id,
        instrument_bound=instrument_bound,
        lab_trusted=lab_trusted,
        deduplicated_get_count=dedup_count,
        config_get_count=config_count,
        balance_get_count=balance_count,
        bound_uid=bound_uid,
    )


def _first_blocker_from_handoff_v1(
    *,
    handoff: CurrentProductive29PCommonEpochHandoffResultV1,
    productive_contact: bool,
) -> tuple[str, str]:
    if handoff.lab_trusted is not True:
        return "LIVE_ACCOUNT_BOUND_NOT_TRUSTED_FOR_29P", "C"
    if handoff.instrument_bound is not True:
        return "STEP_29P_INSTRUMENT_SCOPE_MISMATCH_OR_MISSING", "B"
    if handoff.eligibility is None:
        return "CURRENT_PRODUCTIVE_U01_ELIGIBILITY_NOT_MINTED", "C"
    if handoff.observation is None:
        return "FRESH_USDC_AVAILEQ_NOT_OBSERVED", "C"
    if handoff.produced is not True:
        return "RISK_CAPITAL_MINT_FAIL_CLOSED", "C"
    if productive_contact is not True:
        return (
            "CURRENT_PRODUCTIVE_29P_REQUIRES_PRODUCTIVE_TRUSTED_GET_AND_CAP24_BOUND_INSTRUMENT",
            "C",
        )
    if handoff.evaluator_29p is True:
        if EXECUTION_ADMISSION_REMAINDER_CLOSED is True:
            return "LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINS_FORBIDDEN", "E"
        if WIRE_SEND_PERMITTED is True:
            return "EXECUTION_ADMISSION_REMAINS_FAIL_CLOSED", "E"
        if LIVE_ARMED is True:
            return "WIRE_SEND_PERMITTED_STANDING_GATE_REMAINS_FALSE", "E"
        if LIVE_ENABLED is True:
            return "LIVE_ARMED_STANDING_GATE_REMAINS_FALSE", "E"
        return "LIVE_ENABLED_STANDING_GATE_REMAINS_FALSE", "E"
    return "STEP_29P_RISK_ADMISSIBLE_FALSE", "C"


def execute_current_productive_29p_common_epoch_handoff_to_first_blocker_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    bound_instrument: BoundInstrumentV1 | None,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1 | None,
    evidence_root: Path | None = None,
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE,
    inst_type: str = "FUTURES",
    offline_compose_only: bool = True,
    cap24_productivity_root: Path | None = None,
) -> CurrentProductive29PCommonEpochHandoffExecuteResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise CurrentProductive29PCommonEpochHandoffError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductive29PCommonEpochHandoffError("ORIGIN_MAIN_SHA_MISMATCH")
    if offline_compose_only is not True:
        raise CurrentProductive29PCommonEpochHandoffError("OFFLINE_COMPOSE_ONLY_REQUIRED")
    if fresh_get_transport is None:
        raise CurrentProductive29PCommonEpochHandoffError("FRESH_GET_TRANSPORT_REQUIRED")
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductive29PCommonEpochHandoffError("SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED")
    if P01_RUNTIME_INSTANCE_PRESENT is not False:
        raise CurrentProductive29PCommonEpochHandoffError(
            "RECONSTRUCTION_P01_RUNTIME_INSTANCE_MUST_REMAIN_FALSE"
        )
    if CURRENT_PRODUCTIVE_29P_CANARY_INSTRUMENT_AUTHORITY_IMPORTED is not False:
        raise CurrentProductive29PCommonEpochHandoffError("CANARY_INSTRUMENT_AUTHORITY_IMPORTED")
    if CURRENT_PRODUCTIVE_U01_GET_ENDPOINT != "/api/v5/account/config":
        raise CurrentProductive29PCommonEpochHandoffError("U01_ENDPOINT_DRIFT")
    if CURRENT_PRODUCTIVE_29P_FRESH_GET_ENDPOINT != "/api/v5/account/balance":
        raise CurrentProductive29PCommonEpochHandoffError("BALANCE_ENDPOINT_DRIFT")
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise CurrentProductive29PCommonEpochHandoffError("HOST_MISMATCH")
    reject_direct_avail_eq_29p_claim_v1(claimed="false")
    missing = reject_missing_as_does_not_apply_v1()
    p01_decision = evaluate_current_productive_p01_policy_v1()
    if p01_decision.decision_state != CURRENT_PRODUCTIVE_P01_POLICY_DECISION:
        raise CurrentProductive29PCommonEpochHandoffError("P01_POLICY_MUST_BE_DOES_NOT_APPLY")
    if missing.decision_state == CURRENT_PRODUCTIVE_P01_POLICY_DECISION:
        raise CurrentProductive29PCommonEpochHandoffError("MISSING_MUST_NOT_BECOME_DOES_NOT_APPLY")
    _assert_no_proxy_env_v1()

    package_started = _utc_now_iso_v1()
    decision_epoch = package_started
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = (
        Path(evidence_root)
        if evidence_root is not None
        else _REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / run_id
    )
    store.mkdir(parents=True, exist_ok=True)

    instrument_scope_status = "MISSING"
    bound: BoundInstrumentV1 | None = None
    bound_input = bound_instrument
    cap24_handoff_status = "NOT_ATTEMPTED"
    cap24_provenance_digest = ""
    if bound_input is None:
        prod_root = cap24_productivity_root
        if prod_root is None:
            default_root = default_current_productive_cap24_runtime_state_root_v1()
            prod_root = default_root if default_root.exists() else None
        if prod_root is not None:
            cap24_handoff_status = "ATTEMPTED"
            try:
                cap24_handoff = (
                    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
                        productivity_root=prod_root,
                        repository_sha=origin_main_sha,
                        binding_epoch=decision_epoch,
                    )
                )
                bound_input = cap24_handoff.bound_instrument
                cap24_handoff_status = "ACQUIRED"
                cap24_provenance_digest = cap24_handoff.selection_integrity_digest
            except CurrentProductive29PCap24ProvenanceHandoffError:
                bound_input = None
                cap24_handoff_status = "FAIL_CLOSED"
    try:
        bound = require_current_productive_29p_bound_instrument_v1(bound_input)
        instrument_scope_status = "BOUND_TO_CAP24_SINGLE_SELECTED_FUTURE"
    except Exception as exc:
        instrument_scope_status = f"FAIL_CLOSED:{type(exc).__name__}"
        first_blocker = "CURRENT_PRODUCTIVE_CAP24_BOUND_INSTRUMENT_INSTANCE_MISSING"
        if bound_instrument is not None or cap24_handoff_status == "FAIL_CLOSED":
            first_blocker = "CAP24_BOUND_INSTRUMENT_FAIL_CLOSED"
        claims = {
            "THIS_SLICE": THIS_SLICE,
            "OWNER_GO": owner_go,
            "EXPECTED_ORIGIN_MAIN": origin_main_sha,
            "DECISION_EPOCH": decision_epoch,
            "POST_COUNT": "0",
            "FIRST_REAL_BLOCKER": first_blocker,
            "BLOCKER_CLASS": "B" if bound_instrument is None else "C",
            "P01_STATUS": p01_decision.decision_state,
            "STEP_29P_RISK_ADMISSIBLE": FALSE_TOKEN,
            "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": FALSE_TOKEN,
            "HISTORICAL_EVIDENCE_INPUT": FALSE_TOKEN,
            "HISTORICAL_PROVENANCE_REF_ONLY": HISTORICAL_PROVENANCE_REF_ONLY,
            "VENUE_GET_PERFORMED": FALSE_TOKEN,
            "DEDUPLICATED_GET_COUNT": "0",
            "CAP24_PROVENANCE_HANDOFF_STATUS": cap24_handoff_status,
            "CAP24_PROVENANCE_DIGEST": cap24_provenance_digest,
        }
        _assert_no_secrets(claims)
        _persist_json(path=store / "claims.json", payload=claims)
        _persist_json(
            path=store / "SUMMARY.json",
            payload={"FIRST_REAL_BLOCKER": first_blocker, "POST_COUNT": "0"},
        )
        persist_manifest_sha256_v1(store_root=store)
        manifest_rc = verify_manifest_sha256_v1(store_root=store)
        return CurrentProductive29PCommonEpochHandoffExecuteResultV1(
            store_root=str(store),
            decision_epoch=decision_epoch,
            bound_instrument_id="",
            live_account_bound_status=LiveAccountBoundStatusV1.MISSING.value,
            fresh_pretrade_get_status=FreshPretradeGetStatusV1.MISSING.value,
            u01_status="NOT_REACHED",
            p01_status=p01_decision.decision_state,
            fresh_usdc_availeq_status="NOT_OBSERVED",
            risk_capital_mint_status="UNMINTED",
            instrument_scope_status=instrument_scope_status,
            step_29p_risk_admissible=FALSE_TOKEN,
            deduplicated_get_count=0,
            first_real_blocker=first_blocker,
            blocker_class="B" if bound_instrument is None else "C",
            post_count="0",
            evidence_manifest=str(store / "MANIFEST.sha256"),
            manifest_verify_rc=manifest_rc,
        )

    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch=decision_epoch,
        bound_instrument=bound,
        fresh_get_transport=fresh_get_transport,
        expected_account_identity=expected_account_identity,
        inst_type=inst_type,
        package_finished_iso=package_started,
        p01_decision_state=p01_decision.decision_state,
    )
    transport_class = str(getattr(fresh_get_transport, "transport_class", "") or "")
    venue_contact = bool(getattr(fresh_get_transport, "venue_live_contact", False))
    productive_contact = (
        venue_contact is True and transport_class == TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
    )
    first_blocker, blocker_class = _first_blocker_from_handoff_v1(
        handoff=handoff,
        productive_contact=productive_contact,
    )
    fresh_status = "OBSERVED_THIS_EPOCH" if handoff.observation is not None else "NOT_OBSERVED"
    mint_status = "MINTED" if handoff.produced else "UNMINTED"
    step_29p = FALSE_TOKEN
    if handoff.evaluator_29p is True and productive_contact is True:
        step_29p = TRUE_TOKEN

    claims = {
        "THIS_SLICE": THIS_SLICE,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "OWNER_GO": owner_go,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "DECISION_EPOCH": decision_epoch,
        "POST_COUNT": "0",
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "P01_STATUS": p01_decision.decision_state,
        "U01_STATUS": handoff.adaptation.status,
        "FRESH_USDC_AVAILEQ_STATUS": fresh_status,
        "RISK_CAPITAL_MINT_STATUS": mint_status,
        "INSTRUMENT_SCOPE_STATUS": instrument_scope_status,
        "STEP_29P_RISK_ADMISSIBLE": step_29p,
        "STEP_29P_RISK_ADMISSIBLE_EVALUATOR": TRUE_TOKEN if handoff.evaluator_29p else FALSE_TOKEN,
        "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": FALSE_TOKEN,
        "HISTORICAL_EVIDENCE_INPUT": FALSE_TOKEN,
        "HISTORICAL_PROVENANCE_REF_ONLY": HISTORICAL_PROVENANCE_REF_ONLY,
        "VENUE_GET_PERFORMED": FALSE_TOKEN,
        "DEDUPLICATED_GET_COUNT": str(handoff.deduplicated_get_count),
        "CONFIG_GET_COUNT": str(handoff.config_get_count),
        "BALANCE_GET_COUNT": str(handoff.balance_get_count),
        "CAP24_BOUND_INSTRUMENT_ID": bound.instrument_id,
        "CAP24_PROVENANCE_HANDOFF_STATUS": cap24_handoff_status,
        "CAP24_PROVENANCE_DIGEST": cap24_provenance_digest,
        "LIVE_ACCOUNT_BOUND_STATUS": handoff.lab_status,
        "FRESH_PRETRADE_GET_STATUS": handoff.get_status,
    }
    _assert_no_secrets(claims)
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(
        path=store / "SUMMARY.json",
        payload={
            "FIRST_REAL_BLOCKER": first_blocker,
            "BLOCKER_CLASS": blocker_class,
            "POST_COUNT": "0",
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "DECISION_EPOCH": decision_epoch,
            "HISTORICAL_PROVENANCE_REF_ONLY": HISTORICAL_PROVENANCE_REF_ONLY,
            "HISTORICAL_EVIDENCE_USED_AS_INPUT": False,
        },
    )
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductive29PCommonEpochHandoffExecuteResultV1(
        store_root=str(store),
        decision_epoch=decision_epoch,
        bound_instrument_id=bound.instrument_id,
        live_account_bound_status=handoff.lab_status,
        fresh_pretrade_get_status=handoff.get_status,
        u01_status=handoff.adaptation.status,
        p01_status=p01_decision.decision_state,
        fresh_usdc_availeq_status=fresh_status,
        risk_capital_mint_status=mint_status,
        instrument_scope_status=instrument_scope_status,
        step_29p_risk_admissible=step_29p,
        deduplicated_get_count=handoff.deduplicated_get_count,
        first_real_blocker=first_blocker,
        blocker_class=blocker_class,
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )


def _cli_v1() -> int:
    parser = argparse.ArgumentParser(description="29P common-epoch handoff v1 (offline only)")
    parser.add_argument("--owner-go", required=True)
    parser.add_argument("--origin-main-sha", required=True)
    parser.add_argument("--evidence-root", type=Path, default=None)
    args = parser.parse_args()
    raise CurrentProductive29PCommonEpochHandoffError(
        "CLI_REQUIRES_INJECTED_TRANSPORT_OFFLINE_TESTS_ONLY"
    )


if __name__ == "__main__":
    raise SystemExit(_cli_v1())
