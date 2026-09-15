"""CURRENT_PRODUCTIVE 29P risk-capital model redesign v1.

Consumes Owner-GO
CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_REDESIGN_AND_VENUE_FIELD_AUTHORITY_ADJUDICATION_V1.

Starts from STEP-29P. The needed quantity is USDC free margin available to
size new cross-futures risk. Official venue semantics identify that as
details[ccy=USDC].availEq (already net of in-use including open orders).
BASE is retired as an unobservable intermediate. U04 is not subtracted
again. P01 remains a Peak_Trade conditional reduction. eq remains
reconciliation-target only. Account-level availEq, totalEq, adjEq,
availBal, cashBal, and optimistic fallbacks stay forbidden. No GET. No
POST. No mint without a typed observation. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    NUMERIC_EQUITY_TTL_SECONDS,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FRESHNESS_POLICY as PRETRADE_FRESHNESS_POLICY,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    REQUIRED_SETTLEMENT_CURRENCY,
    RISK_EQUITY_DIMENSION,
    STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
    Step29PCapitalRiskAdmissibilityClaimV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_NOT_EQUITY_STOCK,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_29P_BINDING_STATUS,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ACCOUNT_LEVEL_AVAIL_EQ_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ADJ_EQ_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_AVAIL_BAL_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_AVAIL_EQ_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_BASE_ABSTRACTION,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_CASH_BAL_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_EQ_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_FALLBACK_CHAIN_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_CREATED,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_CLASS,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_P01_APPLICATION,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SELECTED_OPTION,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_TOTAL_EQ_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
    CURRENT_PRODUCTIVE_ARCHITECTURE_IS_NOT_HISTORICAL_RECONSTRUCTION,
    CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_OUTPUT_CLASS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_CREATED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IS_SOURCE_OBJECT,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED,
    CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
    CURRENT_PRODUCTIVE_SOURCE_SELECTED,
    EQ_RECONCILIATION_TARGET_ONLY,
    EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE,
    GOVERNED_PRODUCER_CREATED,
    KIND_SET_RESOLVED,
    KIND_SET_UPLIFT_THIS_WORKPACKAGE,
    LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
    PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
    PRODUCTIVE_U04_EQUITY_STOCK_ROLE,
    RAW_EQ_SOURCE_AUTHORITY,
    SEALED_LEGACY_CENSUS_REOPENED,
    SLOT_IS_EMPTY,
    SOURCE_SELECTED,
    STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER,
    U04_LEGACY_STATUS,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_account_equity_source_architecture_v1 import (
    FORBIDDEN_AUTHORITY_FIELDS,
    reject_eq_authority_uplift_v1,
    reject_legacy_reconstruction_as_live_requirement_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveEqReconciliationTargetV1,
    CurrentProductiveP01ReductionFactV1,
    CurrentProductiveU04ReservationFactV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u04_pending_order_reservation_or_account_equity_mapping_v1 import (
    reject_eq_as_source_authority_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY,
    AVAIL_BAL_IS_NOT_AUTHORITY,
    AVAILABLE_MARGIN_REQUIRED_CCY,
    AVAILABLE_MARGIN_RESPONSE_FIELD,
    AVAILABLE_MARGIN_SEMANTIC_CLASS,
    USD_USDC_EQUIVALENCE_ASSUMED,
)

OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_REDESIGN_AND_"
    "VENUE_FIELD_AUTHORITY_ADJUDICATION_V1"
)
EXPECTED_ORIGIN_MAIN_SHA = "5a426cbb9d9067baec7b208d25812730a5c5f276"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_29p_risk_capital_model_v1/2026-09-15T120300Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T12:03:00Z"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KEEP_FORBIDDEN = "KEEP_FORBIDDEN"
RECLASSIFIED = "CURRENT_PRODUCTIVE_RECLASSIFICATION_JUSTIFIED"
REQUIRED_TD_MODE = "cross"
REQUIRED_ACCOUNT_MODE = "FUTURES_MODE"
P01_APPLIES = "APPLIES"
P01_DOES_NOT_APPLY = "DOES_NOT_APPLY"
P01_UNKNOWN = "UNKNOWN_FAIL_CLOSED"
P01_FACT_ID = "CURRENT_PRODUCTIVE_P01_GOVERNED_REDUCTION"
ELIGIBILITY_FACT_ID = "CURRENT_PRODUCTIVE_U01_ACCOUNT_ELIGIBILITY"
RECONCILIATION_FACT_ID = "CURRENT_PRODUCTIVE_EQ_RECONCILIATION_TARGET"
U04_FACT_ID = "CURRENT_PRODUCTIVE_U04_PENDING_ORDER_RESERVATION"
OBSERVATION_FACT_ID = "CURRENT_PRODUCTIVE_USDC_FREE_MARGIN_OBSERVATION"
OUTPUT_UNIT = "USDC_ACCOUNT_EQUITY"
ALGEBRA_ID = CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA
PRODUCER_IDENTITY = CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY
OBSERVATION_SURFACE = CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE
FRESH_GET_NOT_REQUIRED_JUSTIFIED = (
    "OFFICIAL_VENUE_FREE_MARGIN_SEMANTICS_AND_IN_REPO_AVAILABLE_MARGIN_"
    "CONTRACT_MAKE_DETAILS_USDC_AVAILEQ_DECISION_READY_HOPE_GET_NOT_REQUIRED"
)
BLOCKER_ID = "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
EXACT_MISSING_PREDICATE = (
    "DETAILS_USDC_AVAILEQ_SURFACE_BOUND_PRODUCTIVE_VALUE_UNOBSERVED_"
    "NO_GET_THIS_WP_P01_CONDITIONAL_U04_NOT_SUBTRACTED_EQ_RECONCILIATION_ONLY"
)
ARCHITECTURE_BLOCKER = (
    "OPTION_B_SURFACE_BOUND_NO_MINT_WITHOUT_FRESH_OBSERVATION_"
    "EQ_REMAINS_RECONCILIATION_TARGET_FALLBACK_CHAIN_REMAINS_FORBIDDEN"
)
NEXT_PRODUCTIVE_NODE = "CURRENT_PRODUCTIVE_29P_FRESH_TRUSTED_USDC_FREE_MARGIN_GET"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_PERFORM_FRESH_TRUSTED_READ_ONLY_GET_OF_"
    "DETAILS_USDC_AVAILEQ_AND_PRODUCE_29P_SIZING_VALUE_V1"
)
NEXT_ACTION = (
    "STOP_SURFACE_BOUND_NO_GET_NO_POST_NO_MINT_NO_LIVE_ENABLE_NO_FALLBACK_CHAIN_NO_EQ_SOURCE"
)
PIN_OWNER_GO_STATUS = "SATISFIED_BY_OPTION_B_DETAILS_USDC_AVAILEQ_MINUS_CONDITIONAL_P01"
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_FORBIDDEN_OBSERVATION_MARKERS: tuple[str, ...] = (
    "totaleq",
    "adjeq",
    "availbal",
    "cashbal",
    "frozenbal",
    "isoeq",
    "kind_set",
    "maxbuy",
    "maxsell",
)
_BARE_FORBIDDEN_TOKENS: tuple[str, ...] = ("eq", "upl")
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductive29PRiskCapitalModelError(ValueError):
    """Fail-closed 29P risk-capital model violation."""


@dataclass(frozen=True)
class CurrentProductiveUsdcFreeMarginObservationV1:
    fact_id: str
    surface: str
    value: str
    settlement_currency: str
    selected_ccy: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    decision_epoch: str
    observed_at_as_of: str
    age_seconds: str
    freshness_max_age: str
    provenance_digest: str
    already_net_of_in_use: str
    account_level_avail_eq_used: str
    fallback_chain_used: str


@dataclass(frozen=True)
class CurrentProductive29PRiskCapitalOutputV1:
    produced: str
    value: str
    settlement_currency: str
    dimension_id: str
    producer_identity: str
    algebra_id: str
    output_unit: str
    output_class: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    decision_epoch: str
    observed_at_as_of: str
    input_set_digest: str
    observation_surface: str
    u04_applied: str
    p01_applied: str
    double_counting_guard: str
    reconciliation_status: str
    restart_reconstruction_status: str
    reason_codes: Tuple[str, ...]


@dataclass(frozen=True)
class CurrentProductive29PRiskCapitalPersistResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    selected_option: str
    producer_identity: str
    algebra_id: str
    observation_surface: str
    base_abstraction: str
    fresh_get_executed: str
    current_live_critical_blocker: str
    first_definitive_block: str
    exact_missing_predicate: str
    authorized_get_count: str
    actual_get_count: str
    post_count: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_non_negative_decimal(raw: str, *, field: str) -> Decimal | None:
    text = str(raw or "").strip()
    if text == "" or text != str(raw):
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value < 0:
        return None
    _ = field
    return value


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "").replace(" ", "")


def _observation_is_forbidden_surface(surface: str) -> bool:
    folded = _fold(surface)
    if folded == _fold(OBSERVATION_SURFACE):
        return False
    if folded in {_fold(token) for token in FORBIDDEN_AUTHORITY_FIELDS}:
        return True
    if folded in _BARE_FORBIDDEN_TOKENS:
        return True
    return any(marker in folded for marker in _FORBIDDEN_OBSERVATION_MARKERS)


def classify_step_29p_actual_economic_requirement_v1() -> dict[str, str]:
    return {
        "consumer": "capital_risk_sizing_v1/STEP_29P",
        "authority": STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
        "required_quantity": "USDC_CROSS_MARGIN_FREE_MARGIN_AVAILABLE_TO_SIZE_NEW_RISK",
        "required_dimension": RISK_EQUITY_DIMENSION,
        "required_unit": OUTPUT_UNIT,
        "required_currency": REQUIRED_SETTLEMENT_CURRENCY,
        "required_td_mode": REQUIRED_TD_MODE,
        "empty_data_is_zero": FALSE_TOKEN,
        "usd_is_not_usdc": TRUE_TOKEN,
        "stock_is_not_input": TRUE_TOKEN,
        "contracts_are_not_input": TRUE_TOKEN,
        "optimistic_fallback_forbidden": TRUE_TOKEN,
        "freshness_policy": PRETRADE_FRESHNESS_POLICY,
        "step_29p_is_not_equity_authority_owner": TRUE_TOKEN,
    }


def classify_current_venue_field_adjudication_v1() -> Tuple[dict[str, str], ...]:
    return (
        {
            "field": "details[ccy=USDC].availEq",
            "venue_semantics": "CURRENCY_SCOPED_CROSS_MARGIN_FREE_MARGIN",
            "unit": "USDC_NATIVE",
            "account_scope": "DETAILS_ROW_CCY_USDC",
            "reservation_semantics": "ALREADY_NET_OF_IN_USE_INCLUDING_OPEN_ORDERS",
            "u04_netted": TRUE_TOKEN,
            "p01_netted": FALSE_TOKEN,
            "freshness": PRETRADE_FRESHNESS_POLICY,
            "restart": "FRESH_REOBSERVE_SAME_EPOCH",
            "suitability_29p": "ADMISSIBLE_AS_PRODUCER_OBSERVATION_NOT_DIRECT_CLAIM_FIELD",
            "reconciliation_role": "NOT_EQ",
            "double_counting_risk": "U04_DOUBLE_COUNT_IF_SUBTRACTED_AGAIN",
            "verdict": RECLASSIFIED,
            "prohibition_rationale": (
                "PREVIOUS_FORBID_WAS_ANTI_FALLBACK_AND_DISTINCT_AVAILABLE_MARGIN_"
                "CONSUMER_NOT_A_DENIAL_THAT_FREE_MARGIN_IS_THE_29P_QUANTITY"
            ),
        },
        {
            "field": "account.availEq",
            "venue_semantics": "ACCOUNT_LEVEL_AVAILABLE_EQUITY_USD_MULTICCY",
            "unit": "USD_NOT_USDC",
            "account_scope": "ACCOUNT_ROOT",
            "reservation_semantics": "NOT_USDC_DETAILS_FREE_MARGIN",
            "u04_netted": "UNKNOWN_WRONG_OBJECT",
            "p01_netted": FALSE_TOKEN,
            "freshness": PRETRADE_FRESHNESS_POLICY,
            "restart": "MUST_NOT_RESTART_FROM_ACCOUNT_LEVEL_AVAILEQ",
            "suitability_29p": "UNSUITABLE",
            "reconciliation_role": "NONE",
            "double_counting_risk": "WRONG_UNIT",
            "verdict": KEEP_FORBIDDEN,
            "prohibition_rationale": "USD_ACCOUNT_LEVEL_NOT_USDC_FREE_MARGIN",
        },
        {
            "field": "eq",
            "venue_semantics": "CURRENCY_EQUITY_STOCK_INCLUDING_UPL",
            "unit": "CCY_NATIVE",
            "account_scope": "DETAILS_OR_AMBIGUOUS_BARE_FIELD",
            "reservation_semantics": "NOT_FREE_MARGIN",
            "u04_netted": FALSE_TOKEN,
            "p01_netted": FALSE_TOKEN,
            "freshness": PRETRADE_FRESHNESS_POLICY,
            "restart": "MUST_NOT_RECONSTRUCT_SIZING_FROM_EQ",
            "suitability_29p": "UNSUITABLE_AS_SOURCE",
            "reconciliation_role": "RECONCILIATION_TARGET_ONLY",
            "double_counting_risk": "WOULD_IGNORE_IN_USE",
            "verdict": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_EQ_VERDICT,
            "prohibition_rationale": "STANDING_RECONCILIATION_TARGET_NOT_SIZING_SOURCE",
        },
        {
            "field": "totalEq",
            "venue_semantics": "ACCOUNT_TOTAL_EQUITY_USD",
            "unit": "USD_NOT_USDC",
            "account_scope": "ACCOUNT_ROOT",
            "reservation_semantics": "NOT_USDC_FREE_MARGIN",
            "u04_netted": "UNKNOWN_WRONG_OBJECT",
            "p01_netted": FALSE_TOKEN,
            "freshness": PRETRADE_FRESHNESS_POLICY,
            "restart": "MUST_NOT_RESTART_FROM_TOTALEQ",
            "suitability_29p": "UNSUITABLE",
            "reconciliation_role": "NONE",
            "double_counting_risk": "WRONG_UNIT",
            "verdict": KEEP_FORBIDDEN,
            "prohibition_rationale": "USD_ACCOUNT_EQUITY_NOT_USDC_FREE_MARGIN",
        },
        {
            "field": "adjEq",
            "venue_semantics": "DISCOUNTED_USD_EQUITY_FOR_MARGIN_RATIO",
            "unit": "USD_NOT_USDC",
            "account_scope": "ACCOUNT_ROOT",
            "reservation_semantics": "HAIRCUT_USD_NOT_USDC_SIZING",
            "u04_netted": "UNKNOWN_WRONG_OBJECT",
            "p01_netted": FALSE_TOKEN,
            "freshness": PRETRADE_FRESHNESS_POLICY,
            "restart": "MUST_NOT_RESTART_FROM_ADJEQ",
            "suitability_29p": "UNSUITABLE",
            "reconciliation_role": "NONE",
            "double_counting_risk": "WRONG_UNIT_AND_DISCOUNT",
            "verdict": KEEP_FORBIDDEN,
            "prohibition_rationale": "USD_DISCOUNTED_EQUITY_NOT_USDC_FREE_MARGIN",
        },
        {
            "field": "availBal",
            "venue_semantics": "AVAILABLE_BALANCE_FOR_SPOT_ISOLATED_OPTIONS_LONG",
            "unit": "CCY_NATIVE",
            "account_scope": "DETAILS_ROW",
            "reservation_semantics": "NOT_CROSS_FUTURES_FREE_MARGIN",
            "u04_netted": "NOT_THE_CROSS_FUTURES_IN_USE_OBJECT",
            "p01_netted": FALSE_TOKEN,
            "freshness": PRETRADE_FRESHNESS_POLICY,
            "restart": "MUST_NOT_RESTART_FROM_AVAILBAL",
            "suitability_29p": "UNSUITABLE",
            "reconciliation_role": "NONE",
            "double_counting_risk": "WRONG_PRODUCT_SEMANTICS",
            "verdict": KEEP_FORBIDDEN,
            "prohibition_rationale": "SPOT_ISOLATED_AVAILABLE_BALANCE_NOT_CROSS_FREE_MARGIN",
        },
        {
            "field": "cashBal",
            "venue_semantics": "CASH_BALANCE_WITHOUT_UPL",
            "unit": "CCY_NATIVE",
            "account_scope": "DETAILS_ROW",
            "reservation_semantics": "NOT_FREE_MARGIN",
            "u04_netted": FALSE_TOKEN,
            "p01_netted": FALSE_TOKEN,
            "freshness": PRETRADE_FRESHNESS_POLICY,
            "restart": "MUST_NOT_RESTART_FROM_CASHBAL",
            "suitability_29p": "UNSUITABLE",
            "reconciliation_role": "NONE",
            "double_counting_risk": "IGNORES_UPL_AND_IN_USE",
            "verdict": KEEP_FORBIDDEN,
            "prohibition_rationale": "CASH_NOT_CROSS_FUTURES_FREE_MARGIN",
        },
        {
            "field": "ordFrozen",
            "venue_semantics": "MARGIN_FROZEN_FOR_OPEN_ORDERS",
            "unit": "CCY_NATIVE",
            "account_scope": "DETAILS_ROW",
            "reservation_semantics": "U04_LIKE_COMPONENT_OF_IN_USE",
            "u04_netted": "THIS_IS_THE_RESERVATION",
            "p01_netted": FALSE_TOKEN,
            "freshness": PRETRADE_FRESHNESS_POLICY,
            "restart": "MUST_NOT_BECOME_SIZING_SOURCE",
            "suitability_29p": "REDUCTION_COMPONENT_NOT_SOURCE",
            "reconciliation_role": "NONE",
            "double_counting_risk": "SUBTRACTING_AGAIN_AFTER_AVAILEQ",
            "verdict": "REDUCTION_ALREADY_IN_AVAILEQ_DO_NOT_SUBTRACT",
            "prohibition_rationale": "ALREADY_INCLUDED_IN_VENUE_FREE_MARGIN_IN_USE",
        },
    )


def classify_existing_base_abstraction_verdict_v1() -> dict[str, str]:
    return {
        "verdict": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_BASE_ABSTRACTION,
        "reason": (
            "BASE_HAS_NO_CURRENT_OBSERVATION_SURFACE_AND_THE_29P_QUANTITY_"
            "IS_VENUE_FREE_MARGIN_ALREADY_NET_OF_U04"
        ),
        "ct_algebra": "BASE_MINUS_U04_MINUS_CONDITIONAL_P01_USDC_V1",
        "replacement_algebra": ALGEBRA_ID,
        "selected_option": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SELECTED_OPTION,
    }


def _fail(
    *,
    reasons: Tuple[str, ...],
    decision_epoch: str = "",
    observed_at_as_of: str = "",
    bound_account_identity: str = "",
    bound_venue_identity: str = "",
    bound_td_mode: str = "",
    input_set_digest: str = "",
    p01_applied: str = FALSE_TOKEN,
    reconciliation_status: str = "NOT_COMPARED",
) -> CurrentProductive29PRiskCapitalOutputV1:
    unique = tuple(dict.fromkeys(reasons))
    return CurrentProductive29PRiskCapitalOutputV1(
        produced=FALSE_TOKEN,
        value="",
        settlement_currency=REQUIRED_SETTLEMENT_CURRENCY,
        dimension_id=RISK_EQUITY_DIMENSION,
        producer_identity=PRODUCER_IDENTITY,
        algebra_id=ALGEBRA_ID,
        output_unit=OUTPUT_UNIT,
        output_class=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_OUTPUT_CLASS,
        bound_account_identity=bound_account_identity,
        bound_venue_identity=bound_venue_identity,
        bound_td_mode=bound_td_mode,
        decision_epoch=decision_epoch,
        observed_at_as_of=observed_at_as_of,
        input_set_digest=input_set_digest,
        observation_surface=OBSERVATION_SURFACE,
        u04_applied=FALSE_TOKEN,
        p01_applied=p01_applied,
        double_counting_guard=CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
        reconciliation_status=reconciliation_status,
        restart_reconstruction_status="FAIL_CLOSED",
        reason_codes=unique,
    )


def _validate_scope_and_freshness(
    *,
    bound_account_identity: str,
    bound_venue_identity: str,
    bound_td_mode: str,
    settlement_currency: str,
    decision_epoch: str,
    observed_at_as_of: str,
    age_seconds: str,
    freshness_max_age: str,
    provenance_digest: str,
    field: str,
) -> Tuple[str, ...]:
    reasons: list[str] = []
    if not bound_account_identity.strip():
        reasons.append(f"{field}_ACCOUNT_UNBOUND")
    if bound_venue_identity != "okx":
        reasons.append(f"{field}_VENUE_UNBOUND")
    if bound_td_mode != REQUIRED_TD_MODE:
        reasons.append(f"{field}_TD_MODE_INELIGIBLE")
    if settlement_currency != REQUIRED_SETTLEMENT_CURRENCY:
        reasons.append(f"{field}_CURRENCY_NOT_USDC")
    if not decision_epoch.strip() or not observed_at_as_of.strip():
        reasons.append(f"{field}_TIMESTAMP_MISSING")
    try:
        age = Decimal(str(age_seconds))
        max_age = Decimal(str(freshness_max_age))
    except (InvalidOperation, ValueError):
        reasons.append(f"{field}_FRESHNESS_UNPARSEABLE")
    else:
        if age < 0 or max_age <= 0 or age > max_age:
            reasons.append(f"{field}_STALE")
        if max_age > Decimal(str(NUMERIC_EQUITY_TTL_SECONDS)):
            reasons.append(f"{field}_TTL_EXCEEDS_POLICY")
    digest = str(provenance_digest or "").strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        reasons.append(f"{field}_PROVENANCE_INVALID")
    return tuple(reasons)


def produce_current_productive_29p_risk_capital_v1(
    *,
    observation: CurrentProductiveUsdcFreeMarginObservationV1 | None,
    p01: CurrentProductiveP01ReductionFactV1 | None,
    eligibility: CurrentProductiveAccountEligibilityFactV1 | None,
    eq_target: CurrentProductiveEqReconciliationTargetV1 | None = None,
    u04: CurrentProductiveU04ReservationFactV1 | None = None,
    restart_from_kind_set: str = FALSE_TOKEN,
) -> CurrentProductive29PRiskCapitalOutputV1:
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_MINT_AUTHORIZED is True:
        raise CurrentProductive29PRiskCapitalModelError("PRODUCER_MINT_MUST_REMAIN_UNAUTHORIZED")
    if restart_from_kind_set != FALSE_TOKEN:
        raise CurrentProductive29PRiskCapitalModelError(
            f"KIND_SET_RESTORE_FORBIDDEN:{restart_from_kind_set}"
        )
    if observation is None:
        return _fail(reasons=("FREE_MARGIN_OBSERVATION_MISSING", "NO_MINT_WITHOUT_BOUND_INPUTS"))
    reasons: list[str] = []
    if p01 is None:
        reasons.append("P01_FACT_MISSING")
    if eligibility is None:
        reasons.append("ELIGIBILITY_FACT_MISSING")
    if reasons:
        return _fail(
            reasons=tuple(reasons),
            decision_epoch=observation.decision_epoch,
            observed_at_as_of=observation.observed_at_as_of,
            bound_account_identity=observation.bound_account_identity,
            bound_venue_identity=observation.bound_venue_identity,
            bound_td_mode=observation.bound_td_mode,
        )
    assert p01 is not None
    assert eligibility is not None
    if observation.fact_id != OBSERVATION_FACT_ID:
        reasons.append("OBSERVATION_FACT_ID_MISMATCH")
    if observation.surface != OBSERVATION_SURFACE:
        reasons.append("OBSERVATION_SURFACE_MISMATCH")
    if _observation_is_forbidden_surface(observation.surface):
        reasons.append("FORBIDDEN_OBSERVATION_SURFACE")
    if observation.fallback_chain_used != FALSE_TOKEN:
        reasons.append("FALLBACK_CHAIN_FORBIDDEN")
    if observation.account_level_avail_eq_used != FALSE_TOKEN:
        reasons.append("ACCOUNT_LEVEL_AVAILEQ_FORBIDDEN")
    if observation.already_net_of_in_use != TRUE_TOKEN:
        reasons.append("OBSERVATION_MUST_BE_NET_OF_IN_USE")
    if observation.selected_ccy != AVAILABLE_MARGIN_REQUIRED_CCY:
        reasons.append("OBSERVATION_CCY_NOT_USDC")
    if observation.selected_ccy == "USD":
        reasons.append("USD_USDC_EQUIVALENCE_ASSUMED")
    if p01.fact_id != P01_FACT_ID:
        reasons.append("P01_FACT_ID_MISMATCH")
    if eligibility.fact_id != ELIGIBILITY_FACT_ID:
        reasons.append("ELIGIBILITY_FACT_ID_MISMATCH")
    if eligibility.account_mode != REQUIRED_ACCOUNT_MODE:
        reasons.append("ACCOUNT_MODE_INELIGIBLE")
    if u04 is not None:
        reasons.append("U04_MUST_NOT_BE_SUBTRACTED_AFTER_AVAILEQ")
    reasons.extend(
        _validate_scope_and_freshness(
            bound_account_identity=observation.bound_account_identity,
            bound_venue_identity=observation.bound_venue_identity,
            bound_td_mode=observation.bound_td_mode,
            settlement_currency=observation.settlement_currency,
            decision_epoch=observation.decision_epoch,
            observed_at_as_of=observation.observed_at_as_of,
            age_seconds=observation.age_seconds,
            freshness_max_age=observation.freshness_max_age,
            provenance_digest=observation.provenance_digest,
            field="OBSERVATION",
        )
    )
    for peer, name in ((p01, "P01"), (eligibility, "ELIGIBILITY")):
        if peer.bound_account_identity != observation.bound_account_identity:
            reasons.append(f"{name}_ACCOUNT_SCOPE_MISMATCH")
        if peer.bound_venue_identity != observation.bound_venue_identity:
            reasons.append(f"{name}_VENUE_SCOPE_MISMATCH")
        if peer.bound_td_mode != observation.bound_td_mode:
            reasons.append(f"{name}_TD_MODE_MISMATCH")
        if peer.decision_epoch != observation.decision_epoch:
            reasons.append(f"{name}_EPOCH_MISMATCH")
    if p01.settlement_currency not in {REQUIRED_SETTLEMENT_CURRENCY, "NONE"}:
        reasons.append("P01_CURRENCY_NOT_USDC")
    free_margin = _parse_non_negative_decimal(observation.value, field="availEq")
    if free_margin is None:
        reasons.append("FREE_MARGIN_VALUE_INVALID")
    p01_state = str(p01.applicability_state or "").strip()
    p01_amount = Decimal("0")
    p01_applied = FALSE_TOKEN
    if p01_state == P01_UNKNOWN or p01_state == "":
        reasons.append("P01_UNKNOWN_FAIL_CLOSED")
    elif p01_state == P01_APPLIES:
        parsed = _parse_non_negative_decimal(p01.value, field="P01")
        if parsed is None or parsed <= 0:
            reasons.append("P01_APPLIES_REQUIRES_POSITIVE_AMOUNT")
        else:
            p01_amount = parsed
            p01_applied = TRUE_TOKEN
        reasons.extend(
            _validate_scope_and_freshness(
                bound_account_identity=p01.bound_account_identity,
                bound_venue_identity=p01.bound_venue_identity,
                bound_td_mode=p01.bound_td_mode,
                settlement_currency=p01.settlement_currency,
                decision_epoch=p01.decision_epoch,
                observed_at_as_of=p01.observed_at_as_of,
                age_seconds=p01.age_seconds,
                freshness_max_age=p01.freshness_max_age,
                provenance_digest=p01.provenance_digest,
                field="P01",
            )
        )
    elif p01_state == P01_DOES_NOT_APPLY:
        if str(p01.value or "").strip() not in {"", "0", "0.0", "0.00"}:
            reasons.append("P01_DOES_NOT_APPLY_MUST_NOT_CARRY_AMOUNT")
    else:
        reasons.append("P01_APPLICABILITY_INVALID")
    reconciliation_status = "NOT_COMPARED"
    if eq_target is not None:
        if eq_target.fact_id != RECONCILIATION_FACT_ID:
            reasons.append("EQ_TARGET_FACT_ID_MISMATCH")
        if eq_target.compare_requested == TRUE_TOKEN:
            eq_value = _parse_non_negative_decimal(eq_target.value, field="eq")
            if eq_value is None:
                reasons.append("EQ_TARGET_VALUE_INVALID")
            elif free_margin is not None and free_margin > eq_value:
                reasons.append("EQ_RECONCILIATION_DIVERGENCE")
                reconciliation_status = "DIVERGENCE_BLOCKED"
            else:
                reconciliation_status = "COMPARED_NO_DIVERGENCE"
            reject_eq_as_source_authority_v1(claimed="false")
            reject_eq_authority_uplift_v1(claimed="false")
    if reasons:
        return _fail(
            reasons=tuple(reasons),
            decision_epoch=observation.decision_epoch,
            observed_at_as_of=observation.observed_at_as_of,
            bound_account_identity=observation.bound_account_identity,
            bound_venue_identity=observation.bound_venue_identity,
            bound_td_mode=observation.bound_td_mode,
            p01_applied=p01_applied,
            reconciliation_status=reconciliation_status,
        )
    assert free_margin is not None
    sized = free_margin - p01_amount
    if sized < 0:
        return _fail(
            reasons=("AVAILABLE_FOR_SIZING_NEGATIVE_AFTER_P01",),
            decision_epoch=observation.decision_epoch,
            observed_at_as_of=observation.observed_at_as_of,
            bound_account_identity=observation.bound_account_identity,
            bound_venue_identity=observation.bound_venue_identity,
            bound_td_mode=observation.bound_td_mode,
            p01_applied=p01_applied,
            reconciliation_status=reconciliation_status,
        )
    digest = _sha256_text(
        _canonical_json(
            {
                "observation": observation.value,
                "surface": observation.surface,
                "p01_state": p01_state,
                "p01_value": str(p01_amount),
                "epoch": observation.decision_epoch,
                "account": observation.bound_account_identity,
            }
        )
    )
    return CurrentProductive29PRiskCapitalOutputV1(
        produced=TRUE_TOKEN,
        value=format(sized, "f"),
        settlement_currency=REQUIRED_SETTLEMENT_CURRENCY,
        dimension_id=RISK_EQUITY_DIMENSION,
        producer_identity=PRODUCER_IDENTITY,
        algebra_id=ALGEBRA_ID,
        output_unit=OUTPUT_UNIT,
        output_class=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_OUTPUT_CLASS,
        bound_account_identity=observation.bound_account_identity,
        bound_venue_identity=observation.bound_venue_identity,
        bound_td_mode=observation.bound_td_mode,
        decision_epoch=observation.decision_epoch,
        observed_at_as_of=observation.observed_at_as_of,
        input_set_digest=digest,
        observation_surface=OBSERVATION_SURFACE,
        u04_applied=FALSE_TOKEN,
        p01_applied=p01_applied,
        double_counting_guard=CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
        reconciliation_status=reconciliation_status,
        restart_reconstruction_status="RECOMPUTE_FROM_FRESH_CURRENT_FACTS_SAME_EPOCH",
        reason_codes=("PRODUCED",),
    )


def restart_current_productive_29p_risk_capital_v1(
    *,
    observation: CurrentProductiveUsdcFreeMarginObservationV1,
    p01: CurrentProductiveP01ReductionFactV1,
    eligibility: CurrentProductiveAccountEligibilityFactV1,
    restore_from_kind_set: str = FALSE_TOKEN,
) -> CurrentProductive29PRiskCapitalOutputV1:
    if restore_from_kind_set != FALSE_TOKEN:
        raise CurrentProductive29PRiskCapitalModelError(
            f"KIND_SET_RESTORE_FORBIDDEN:{restore_from_kind_set}"
        )
    return produce_current_productive_29p_risk_capital_v1(
        observation=observation,
        p01=p01,
        eligibility=eligibility,
        restart_from_kind_set=FALSE_TOKEN,
    )


def bind_step_29p_typed_equity_from_risk_capital_v1(
    *,
    output: CurrentProductive29PRiskCapitalOutputV1,
    fresh_pretrade_get_status: str,
    live_account_bound_status: str,
    expected_instrument_id: str,
    observed_instrument_id: str,
    fresh_evidence_fetched: bool,
    fresh_evidence_validated: bool,
) -> Step29PCapitalRiskAdmissibilityClaimV1:
    raw = output.value if output.produced == TRUE_TOKEN else ""
    source_field = PRODUCER_IDENTITY if output.produced == TRUE_TOKEN else ""
    if source_field and _observation_is_forbidden_surface(source_field):
        raise CurrentProductive29PRiskCapitalModelError("29P_SOURCE_FIELD_MUST_BE_PRODUCER")
    return Step29PCapitalRiskAdmissibilityClaimV1(
        fresh_pretrade_get_status=fresh_pretrade_get_status,
        live_account_bound_status=live_account_bound_status,
        expected_instrument_id=expected_instrument_id,
        observed_instrument_id=observed_instrument_id,
        expected_currency=REQUIRED_SETTLEMENT_CURRENCY,
        observed_currency=output.settlement_currency,
        equity_dimension=RISK_EQUITY_DIMENSION,
        typed_account_equity_raw=raw,
        typed_account_equity_source_field=source_field,
        fresh_evidence_fetched=fresh_evidence_fetched,
        fresh_evidence_validated=fresh_evidence_validated,
    )


def _assert_standing_pins() -> None:
    if WIRE_SEND_PERMITTED is not False:
        raise CurrentProductive29PRiskCapitalModelError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED is not True:
        raise CurrentProductive29PRiskCapitalModelError("ARCHITECTURE_NOT_RATIFIED")
    if CURRENT_PRODUCTIVE_ARCHITECTURE_IS_NOT_HISTORICAL_RECONSTRUCTION is not True:
        raise CurrentProductive29PRiskCapitalModelError("MUST_NOT_BE_HISTORICAL_RECONSTRUCTION")
    if LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE is not False:
        raise CurrentProductive29PRiskCapitalModelError("LEGACY_RECONSTRUCTION_MUST_REMAIN_FALSE")
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductive29PRiskCapitalModelError("SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED")
    if GOVERNED_PRODUCER_CREATED is not False:
        raise CurrentProductive29PRiskCapitalModelError(
            "ACCOUNT_EQUITY_AUTHORITY_PRODUCER_SLOT_MUST_REMAIN_EMPTY"
        )
    if SLOT_IS_EMPTY is not True:
        raise CurrentProductive29PRiskCapitalModelError("PRODUCER_SLOT_MUST_BE_EMPTY")
    if SOURCE_SELECTED is not False:
        raise CurrentProductive29PRiskCapitalModelError(
            "CS_VENUE_SOURCE_SELECTED_MUST_REMAIN_FALSE"
        )
    if CURRENT_PRODUCTIVE_SOURCE_SELECTED is not False:
        raise CurrentProductive29PRiskCapitalModelError("CENSUS_SOURCE_MUST_REMAIN_UNSELECTED")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise CurrentProductive29PRiskCapitalModelError("RAW_EQ_SOURCE_AUTHORITY_TRUE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise CurrentProductive29PRiskCapitalModelError("EQ_MUST_REMAIN_RECONCILIATION_TARGET")
    if EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is not False:
        raise CurrentProductive29PRiskCapitalModelError("EQ_TREATED_AS_SOURCE")
    if CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED is not False:
        raise CurrentProductive29PRiskCapitalModelError("EQUITY_AUTHORITY_MINT_MUST_REMAIN_FALSE")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_MINT_AUTHORIZED is not False:
        raise CurrentProductive29PRiskCapitalModelError("SIZING_PRODUCER_MINT_MUST_REMAIN_FALSE")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_CREATED is not True:
        raise CurrentProductive29PRiskCapitalModelError("SIZING_PRODUCER_MUST_REMAIN_CREATED")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IS_SOURCE_OBJECT is not True:
        raise CurrentProductive29PRiskCapitalModelError("SIZING_PRODUCER_MUST_REMAIN_SOURCE_OBJECT")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_CREATED is not True:
        raise CurrentProductive29PRiskCapitalModelError("RISK_CAPITAL_MODEL_MUST_BE_CREATED")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SELECTED_OPTION != "OPTION_B":
        raise CurrentProductive29PRiskCapitalModelError("SELECTED_OPTION_MUST_BE_OPTION_B")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_AVAIL_EQ_VERDICT != RECLASSIFIED:
        raise CurrentProductive29PRiskCapitalModelError("AVAILEQ_DETAILS_MUST_BE_RECLASSIFIED")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_TOTAL_EQ_VERDICT != KEEP_FORBIDDEN:
        raise CurrentProductive29PRiskCapitalModelError("TOTALEQ_MUST_STAY_FORBIDDEN")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ADJ_EQ_VERDICT != KEEP_FORBIDDEN:
        raise CurrentProductive29PRiskCapitalModelError("ADJEQ_MUST_STAY_FORBIDDEN")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_AVAIL_BAL_VERDICT != KEEP_FORBIDDEN:
        raise CurrentProductive29PRiskCapitalModelError("AVAILBAL_MUST_STAY_FORBIDDEN")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_CASH_BAL_VERDICT != KEEP_FORBIDDEN:
        raise CurrentProductive29PRiskCapitalModelError("CASHBAL_MUST_STAY_FORBIDDEN")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ACCOUNT_LEVEL_AVAIL_EQ_VERDICT != KEEP_FORBIDDEN:
        raise CurrentProductive29PRiskCapitalModelError("ACCOUNT_LEVEL_AVAILEQ_MUST_STAY_FORBIDDEN")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_FALLBACK_CHAIN_VERDICT != KEEP_FORBIDDEN:
        raise CurrentProductive29PRiskCapitalModelError("FALLBACK_CHAIN_MUST_STAY_FORBIDDEN")
    if CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_EQ_VERDICT != "KEEP_RECONCILIATION_TARGET_ONLY":
        raise CurrentProductive29PRiskCapitalModelError("EQ_ROLE_MUST_REMAIN_RECONCILIATION")
    if ACCOUNT_AVAIL_EQ_IS_NOT_AUTHORITY is not True:
        raise CurrentProductive29PRiskCapitalModelError("ACCOUNT_AVAILEQ_AUTHORITY_DRIFT")
    if AVAIL_BAL_IS_NOT_AUTHORITY is not True:
        raise CurrentProductive29PRiskCapitalModelError("AVAILBAL_AUTHORITY_DRIFT")
    if USD_USDC_EQUIVALENCE_ASSUMED is not False:
        raise CurrentProductive29PRiskCapitalModelError("USD_USDC_EQUIVALENCE_ASSUMED")
    if AVAILABLE_MARGIN_RESPONSE_FIELD != "details.availEq":
        raise CurrentProductive29PRiskCapitalModelError("AVAILABLE_MARGIN_FIELD_DRIFT")
    if AVAILABLE_MARGIN_SEMANTIC_CLASS != (
        "CURRENCY_SCOPED_CROSS_MARGIN_FREE_MARGIN_DETAILS_AVAILEQ"
    ):
        raise CurrentProductive29PRiskCapitalModelError("AVAILABLE_MARGIN_CLASS_DRIFT")
    if KIND_SET_RESOLVED is not False:
        raise CurrentProductive29PRiskCapitalModelError("KIND_SET_RESOLVED_TRUE")
    if KIND_SET_UPLIFT_THIS_WORKPACKAGE is not False:
        raise CurrentProductive29PRiskCapitalModelError("KIND_SET_UPLIFT")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise CurrentProductive29PRiskCapitalModelError("MAPPING_MUST_REMAIN_INVALID")
    if MAPPING_PROVEN is not False:
        raise CurrentProductive29PRiskCapitalModelError("MAPPING_PROVEN_TRUE")
    if CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED is not False:
        raise CurrentProductive29PRiskCapitalModelError("STANDING_FRESH_GET_FLAG_MUST_REMAIN_FALSE")
    if PRODUCTIVE_U04_EQUITY_STOCK_ROLE != DISPOSITION_NOT_EQUITY_STOCK:
        raise CurrentProductive29PRiskCapitalModelError("U04_STOCK_ROLE_DRIFT")
    if PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise CurrentProductive29PRiskCapitalModelError("U04_CAPITAL_ROLE_DRIFT")
    if U04_LEGACY_STATUS != "UNRESOLVED":
        raise CurrentProductive29PRiskCapitalModelError("U04_LEGACY_STATUS_DRIFT")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductive29PRiskCapitalModelError("U05_UPLIFT")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductive29PRiskCapitalModelError("U06_UPLIFT")
    if STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER is not True:
        raise CurrentProductive29PRiskCapitalModelError("29P_MUST_NOT_OWN_EQUITY_AUTHORITY")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise CurrentProductive29PRiskCapitalModelError("DAG_PIN_DRIFT")
    reject_legacy_reconstruction_as_live_requirement_v1(claimed="false")
    reject_eq_as_source_authority_v1(claimed="false")
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")


def execute_current_productive_29p_risk_capital_model_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
) -> CurrentProductive29PRiskCapitalPersistResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductive29PRiskCapitalModelError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductive29PRiskCapitalModelError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    as_of = CANONICAL_PERSIST_AS_OF
    store = (
        Path(evidence_root) if evidence_root is not None else _REPO_ROOT / CANONICAL_PACK_RELPATH
    )
    store.mkdir(parents=True, exist_ok=True)
    missing = produce_current_productive_29p_risk_capital_v1(
        observation=None,
        p01=None,
        eligibility=None,
    )
    claims = {
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO_STATUS": PIN_OWNER_GO_STATUS,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CU",
        "CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL": (
            CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION
        ),
        "SELECTED_ARCHITECTURE_OPTION": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SELECTED_OPTION,
        "EXISTING_BASE_ABSTRACTION_VERDICT": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_BASE_ABSTRACTION,
        "TARGET_29P_INPUT_MODEL": "USDC_CROSS_MARGIN_FREE_MARGIN_MINUS_CONDITIONAL_P01",
        "PRODUCER_MODEL": PRODUCER_IDENTITY,
        "PRODUCER_ALGEBRA": ALGEBRA_ID,
        "OBSERVATION_SURFACE": OBSERVATION_SURFACE,
        "OBSERVATION_CLASS": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_CLASS,
        "AVAILABLE_MARGIN_REUSED_SURFACE": AVAILABLE_MARGIN_RESPONSE_FIELD,
        "AVAIL_EQ_VERDICT": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_AVAIL_EQ_VERDICT,
        "TOTAL_EQ_VERDICT": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_TOTAL_EQ_VERDICT,
        "ADJ_EQ_VERDICT": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ADJ_EQ_VERDICT,
        "AVAIL_BAL_VERDICT": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_AVAIL_BAL_VERDICT,
        "CASH_BAL_VERDICT": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_CASH_BAL_VERDICT,
        "ACCOUNT_LEVEL_AVAIL_EQ_VERDICT": (
            CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ACCOUNT_LEVEL_AVAIL_EQ_VERDICT
        ),
        "FALLBACK_CHAIN_VERDICT": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_FALLBACK_CHAIN_VERDICT,
        "EQ_ROLE": CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
        "EQ_VERDICT": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_EQ_VERDICT,
        "U04_APPLICATION": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
        "P01_APPLICATION": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_P01_APPLICATION,
        "DOUBLE_COUNTING_GUARD": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
        "FRESHNESS_POLICY": PRETRADE_FRESHNESS_POLICY,
        "FRESH_GET_EXECUTED": FALSE_TOKEN,
        "FRESH_GET_NOT_REQUIRED_JUSTIFIED": FRESH_GET_NOT_REQUIRED_JUSTIFIED,
        "NO_HOPE_GET": TRUE_TOKEN,
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "POST_COUNT": "0",
        "PRODUCER_MINT_AUTHORIZED": FALSE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE": FALSE_TOKEN,
        "STEP_29P_BINDING_STATUS": CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_29P_BINDING_STATUS,
        "RESTART_RECONSTRUCTION_STATUS": (
            "FRESH_REOBSERVE_DETAILS_USDC_AVAILEQ_SAME_EPOCH_ELSE_FAIL_CLOSED"
        ),
        "CURRENT_LIVE_CRITICAL_BLOCKER": BLOCKER_ID,
        "FIRST_DEFINITIVE_BLOCK": BLOCKER_ID,
        "EXACT_MISSING_PREDICATE": EXACT_MISSING_PREDICATE,
        "NEXT_PRODUCTIVE_NODE": NEXT_PRODUCTIVE_NODE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE": FALSE_TOKEN,
        "SEALED_LEGACY_CENSUS_REOPENED": FALSE_TOKEN,
        "KIND_SET": "EMPTY_FAIL_CLOSED",
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "MAPPING_PROVEN": FALSE_TOKEN,
        "AUTHORITY_UPLIFT": FALSE_TOKEN,
        "EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE": FALSE_TOKEN,
        "LIVE_ENABLED": FALSE_TOKEN,
        "LIVE_ARMED": FALSE_TOKEN,
        "WIRE_SEND_PERMITTED": FALSE_TOKEN,
        "ATLAS_AUTHORITY": NONE_TOKEN,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "PERSIST_AS_OF": as_of,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "WORKPACKAGE": "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_V1",
        "UNBOUND_PRODUCE_REASON_CODES": ",".join(missing.reason_codes),
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(
        path=store / "venue_field_adjudication_v1.json",
        payload={"fields": list(classify_current_venue_field_adjudication_v1())},
    )
    _persist_json(
        path=store / "consumer_requirement_v1.json",
        payload=classify_step_29p_actual_economic_requirement_v1(),
    )
    _persist_json(
        path=store / "base_abstraction_verdict_v1.json",
        payload=classify_existing_base_abstraction_verdict_v1(),
    )
    _persist_json(
        path=store / "unbound_produce_v1.json",
        payload={
            "produced": missing.produced,
            "value": missing.value,
            "reason_codes": list(missing.reason_codes),
        },
    )
    _persist_json(
        path=store / "protected_surfaces_v1.json",
        payload={
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
            "treasury_untouched": TRUE_TOKEN,
            "live_not_enabled": TRUE_TOKEN,
        },
    )
    _persist_json(
        path=store / "LINEAGE.json",
        payload={
            "schema_class": SCHEMA_CLASS,
            "parent_ct_pack": (
                "evidence/ops/full_core_current_productive_available_for_sizing_"
                "producer_v1/2026-09-15T112400Z"
            ),
            "genesis_id": EXPECTED_GENESIS_ID,
            "persist_as_of": as_of,
            "sealed_legacy_census_reopened": FALSE_TOKEN,
            "fresh_get_executed": FALSE_TOKEN,
        },
    )
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    if any(marker in joined.lower() for marker in SECRET_MARKERS):
        raise CurrentProductive29PRiskCapitalModelError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise CurrentProductive29PRiskCapitalModelError("MANIFEST_VERIFY_NOT_ZERO")
    return CurrentProductive29PRiskCapitalPersistResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        selected_option=CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SELECTED_OPTION,
        producer_identity=PRODUCER_IDENTITY,
        algebra_id=ALGEBRA_ID,
        observation_surface=OBSERVATION_SURFACE,
        base_abstraction=CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_BASE_ABSTRACTION,
        fresh_get_executed=FALSE_TOKEN,
        current_live_critical_blocker=BLOCKER_ID,
        first_definitive_block=BLOCKER_ID,
        exact_missing_predicate=EXACT_MISSING_PREDICATE,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
    )


def reject_direct_avail_eq_29p_claim_v1(*, claimed: str) -> None:
    folded = _fold(claimed)
    if folded in {"availeq", "details.availeq"}:
        raise CurrentProductive29PRiskCapitalModelError(
            "DIRECT_AVAILEQ_29P_CLAIM_FORBIDDEN_USE_PRODUCER"
        )


__all__ = (
    "ALGEBRA_ID",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CurrentProductive29PRiskCapitalModelError",
    "CurrentProductive29PRiskCapitalOutputV1",
    "CurrentProductive29PRiskCapitalPersistResultV1",
    "CurrentProductiveUsdcFreeMarginObservationV1",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_OWNER_GO",
    "OBSERVATION_SURFACE",
    "OWNER_GO",
    "bind_step_29p_typed_equity_from_risk_capital_v1",
    "classify_current_venue_field_adjudication_v1",
    "classify_existing_base_abstraction_verdict_v1",
    "classify_step_29p_actual_economic_requirement_v1",
    "execute_current_productive_29p_risk_capital_model_v1",
    "produce_current_productive_29p_risk_capital_v1",
    "reject_direct_avail_eq_29p_claim_v1",
    "restart_current_productive_29p_risk_capital_v1",
)
