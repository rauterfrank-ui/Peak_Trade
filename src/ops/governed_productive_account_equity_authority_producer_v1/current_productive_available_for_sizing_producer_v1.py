"""Governed CURRENT_PRODUCTIVE AVAILABLE_FOR_SIZING producer v1.

Consumes Owner-GO DESIGN_AND_BUILD_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1.
Satisfies the CS-named GO by selecting this producer as the source object
outside eq, forbidden venue fields, legacy KIND_SET, max-size contracts,
and U04-as-source. Does not reopen the sealed census. Does not treat
venue eq as source. Does not bind forbidden venue fields. Does not bind
unclassified fields by plausibility. Does not mint a productive value
while BASE remains unbound. Does not POST. GET is evidence, not
authority, and is not required to define this producer. AUTHORITY_EFFECT=NONE.

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
    CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS,
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
    CURRENT_PRODUCTIVE_ARCHITECTURE_IS_NOT_HISTORICAL_RECONSTRUCTION,
    CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_29P_BINDING_STATUS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_OUTPUT_CLASS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_ALGEBRA,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_CREATED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IS_SOURCE_OBJECT,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_RESTART_POLICY,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_RATIFIED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE,
    CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED,
    CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
    CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
    CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE,
    CURRENT_PRODUCTIVE_SOURCE_SELECTED,
    CURRENT_PRODUCTIVE_U04_CURRENT_APPLICATION,
    EQ_RECONCILIATION_TARGET_ONLY,
    EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE,
    GOVERNED_PRODUCER_CREATED,
    KIND_SET_RESOLVED,
    KIND_SET_UPLIFT_THIS_WORKPACKAGE,
    LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
    PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
    PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U04_EQUITY_STOCK_ROLE,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    SEALED_LEGACY_CENSUS_REOPENED,
    SLOT_IS_EMPTY,
    SOURCE_SELECTED,
    STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER,
    U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE,
    U04_LEGACY_STATUS,
    U04_PLACEMENT,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_account_equity_source_architecture_v1 import (
    FORBIDDEN_AUTHORITY_FIELDS,
    LAYER_AVAILABLE_FOR_SIZING,
    reject_available_for_sizing_mint_without_source_v1,
    reject_eq_authority_uplift_v1,
    reject_equity_stock_as_29p_sizing_input_v1,
    reject_layer_mix_stock_and_sizing_v1,
    reject_legacy_reconstruction_as_live_requirement_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_source_selection_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CS_PACK_RELPATH,
    NEXT_OWNER_GO as PIN_OWNER_GO,
    reject_empty_producer_slot_as_source_v1,
    reject_forbidden_venue_field_as_source_v1,
    reject_max_size_contracts_as_usdc_equity_source_v1,
    reject_u04_as_sizing_source_v1,
    reject_unclassified_field_plausibility_bind_v1,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.non_eq_equity_stock_source_kind_or_completeness_v1 import (
    reject_kind_set_uplift_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.remaining_necessary_kind_evidence_classification_v1 import (
    reject_u04_reclassify_as_equity_stock_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u04_pending_order_reservation_or_account_equity_mapping_v1 import (
    reject_eq_as_source_authority_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

OWNER_GO = "OWNER_GO_DESIGN_AND_BUILD_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1"
EXPECTED_ORIGIN_MAIN_SHA = "664495f4a87ca51c1063d2a6877082b023d164ed"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_available_for_sizing_producer_v1/2026-09-15T112400Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T11:24:00Z"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
STATE_UNRESOLVED = "UNRESOLVED"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
REQUIRED_TD_MODE = "cross"
REQUIRED_ACCOUNT_MODE = "FUTURES_MODE"
P01_APPLIES = "APPLIES"
P01_DOES_NOT_APPLY = "DOES_NOT_APPLY"
P01_UNKNOWN = "UNKNOWN_FAIL_CLOSED"
U04_FACT_ID = "CURRENT_PRODUCTIVE_U04_PENDING_ORDER_RESERVATION"
P01_FACT_ID = "CURRENT_PRODUCTIVE_P01_GOVERNED_REDUCTION"
ELIGIBILITY_FACT_ID = "CURRENT_PRODUCTIVE_U01_ACCOUNT_ELIGIBILITY"
RECONCILIATION_FACT_ID = "CURRENT_PRODUCTIVE_EQ_RECONCILIATION_TARGET"
OUTPUT_UNIT = "USDC_ACCOUNT_EQUITY"
ALGEBRA_ID = CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_ALGEBRA
PRODUCER_IDENTITY = CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY
FRESH_GET_NOT_REQUIRED_JUSTIFIED = (
    "PRODUCER_ALGEBRA_AND_BASE_FACT_CONTRACT_ARE_DECISION_READY_FROM_SEALED_"
    "CS_CR_AND_POLICY_SEMANTICS_HOPE_GET_CANNOT_UNFORBID_VENUE_FIELDS_OR_"
    "AUTHORIZE_UNCLASSIFIED_FIELDS_OR_BIND_THE_NEW_BASE_FACT"
)
EXACT_MISSING_PREDICATE = (
    "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_UNBOUND_AFTER_PRODUCER_"
    "DEFINED_EQ_RECONCILIATION_TARGET_ONLY_FORBIDDEN_FIELDS_NOT_IN_ALGEBRA_"
    "U04_REDUCTION_AFTER_BASE_P01_CONDITIONAL_LEGACY_KIND_SET_NOT_SOURCE"
)
BLOCKER_ID = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_UNBOUND_AFTER_PRODUCER_DEFINED"
ARCHITECTURE_BLOCKER = (
    "PRODUCER_DEFINED_BASE_FACT_UNBOUND_EQ_REMAINS_RECONCILIATION_TARGET_"
    "FORBIDDEN_FIELDS_NOT_IN_ALGEBRA_U04_REDUCTION_NOT_SOURCE_LEGACY_CENSUS_SEALED"
)
NEXT_PRODUCTIVE_NODE = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_OBSERVATION_BINDING"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_BIND_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_"
    "TO_A_NON_FORBIDDEN_NON_EQ_NON_STOCK_USDC_CURRENT_PRODUCTIVE_OBSERVATION_V1"
)
NEXT_ACTION = (
    "STOP_PRODUCER_DEFINED_BASE_UNBOUND_NO_FORBIDDEN_FIELD_BIND_NO_HOPE_GET_"
    "NO_LEGACY_RECONSTRUCTION_NO_MINT"
)
PIN_OWNER_GO_STATUS = "SATISFIED_BY_PRODUCER_AS_CURRENT_PRODUCTIVE_SOURCE_OBJECT"
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_FORBIDDEN_SOURCE_MARKERS: tuple[str, ...] = (
    "availeq",
    "totaleq",
    "adjeq",
    "availbal",
    "cashbal",
    "frozenbal",
    "isoeq",
    "ordfrozen",
    "mgnratio",
    "kind_set",
    "maxbuy",
    "maxsell",
)
_BARE_FORBIDDEN_SOURCE_TOKENS: tuple[str, ...] = ("eq", "upl")
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductiveAvailableForSizingProducerError(ValueError):
    """Fail-closed current-productive AVAILABLE_FOR_SIZING producer violation."""


@dataclass(frozen=True)
class CurrentProductiveAvailableForSizingBaseFactV1:
    fact_id: str
    value: str
    settlement_currency: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    decision_epoch: str
    observed_at_as_of: str
    age_seconds: str
    freshness_max_age: str
    provenance_digest: str
    source_class: str
    already_net_of_u04: str


@dataclass(frozen=True)
class CurrentProductiveU04ReservationFactV1:
    fact_id: str
    value: str
    settlement_currency: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    decision_epoch: str
    observed_at_as_of: str
    age_seconds: str
    freshness_max_age: str
    provenance_digest: str
    source_class: str
    empty_reservation_proven: str


@dataclass(frozen=True)
class CurrentProductiveP01ReductionFactV1:
    fact_id: str
    applicability_state: str
    value: str
    settlement_currency: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    decision_epoch: str
    observed_at_as_of: str
    age_seconds: str
    freshness_max_age: str
    provenance_digest: str
    source_class: str


@dataclass(frozen=True)
class CurrentProductiveAccountEligibilityFactV1:
    fact_id: str
    account_mode: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    decision_epoch: str
    provenance_digest: str


@dataclass(frozen=True)
class CurrentProductiveEqReconciliationTargetV1:
    fact_id: str
    value: str
    settlement_currency: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    decision_epoch: str
    observed_at_as_of: str
    provenance_digest: str
    compare_requested: str


@dataclass(frozen=True)
class CurrentProductiveAvailableForSizingProducerOutputV1:
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
    u04_applied: str
    p01_applied: str
    double_counting_guard: str
    reconciliation_status: str
    restart_reconstruction_status: str
    reason_codes: Tuple[str, ...]
    step_29p_risk_admissible: str


@dataclass(frozen=True)
class CurrentProductiveAvailableForSizingProducerPersistResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    producer_created: str
    producer_identity: str
    algebra_id: str
    selected_source_object: str
    base_status: str
    available_for_sizing_source_status: str
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


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CurrentProductiveAvailableForSizingProducerError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _fold(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "").replace("-", "")


def _source_class_is_forbidden(source_class: str) -> bool:
    folded = _fold(source_class)
    if not folded:
        return True
    if folded in _BARE_FORBIDDEN_SOURCE_TOKENS:
        return True
    return any(marker in folded for marker in _FORBIDDEN_SOURCE_MARKERS)


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


def _parse_age_seconds(raw: str) -> int | None:
    text = str(raw or "").strip()
    if text == "" or text != str(raw):
        return None
    try:
        age = int(text)
    except ValueError:
        return None
    if str(age) != text or age < 0:
        return None
    return age


def reject_kind_set_restart_restore_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "KIND_SET", "RESTORE_FROM_KIND_SET"}:
        raise CurrentProductiveAvailableForSizingProducerError(
            f"KIND_SET_RESTORE_FORBIDDEN_FOR_AVAILABLE_FOR_SIZING_RESTART:{claimed}"
        )


def reject_eq_copied_into_sizing_value_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "EQ_AS_VALUE", "COPY_EQ"}:
        raise CurrentProductiveAvailableForSizingProducerError(
            f"EQ_MUST_NOT_BE_COPIED_INTO_AVAILABLE_FOR_SIZING:{claimed}"
        )


def reject_unclassified_algebra_input_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "UNCLASSIFIED", "PLAUSIBLE"}:
        raise CurrentProductiveAvailableForSizingProducerError(
            f"UNCLASSIFIED_FIELD_NOT_ALGEBRA_INPUT:{claimed}"
        )


def classify_producer_input_facts_v1() -> Tuple[dict[str, str], ...]:
    return (
        {
            "fact_id": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
            "role": "BASE_BEFORE_U04_AND_P01",
            "unit": OUTPUT_UNIT,
            "authority": "CURRENT_PRODUCTIVE_TYPED_FACT_DEFINED_THIS_GO",
            "binding_status": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
            "forbidden_as": "eq,availEq,totalEq,adjEq,availBal,cashBal,stock,max-size,KIND_SET",
            "already_net_of_u04": FALSE_TOKEN,
        },
        {
            "fact_id": U04_FACT_ID,
            "role": "REDUCTION_AFTER_BASE_ONCE",
            "unit": OUTPUT_UNIT,
            "authority": PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
            "binding_status": "VALUE_UNBOUND_ROLE_RATIFIED",
            "forbidden_as": "SOURCE,EQUITY_STOCK",
            "already_net_of_u04": FALSE_TOKEN,
        },
        {
            "fact_id": P01_FACT_ID,
            "role": "CONDITIONAL_REDUCTION_AFTER_U04",
            "unit": "ABSOLUTE_MONETARY_REDUCTION_AMOUNT",
            "authority": "GOVERNED_CONDITIONAL",
            "binding_status": "APPLICABILITY_AND_VALUE_MUST_BE_EXPLICIT",
            "forbidden_as": "U04,ordFrozen,FORBIDDEN_VENUE_FIELD",
            "already_net_of_u04": FALSE_TOKEN,
        },
        {
            "fact_id": ELIGIBILITY_FACT_ID,
            "role": "ELIGIBILITY_CONTEXT_NOT_NUMERIC_TERM",
            "unit": "NONE",
            "authority": "U01_ACCOUNT_MODE_ROLE",
            "binding_status": "REQUIRED_AT_PRODUCE",
            "forbidden_as": "NUMERIC_EQUITY_TERM",
            "already_net_of_u04": FALSE_TOKEN,
        },
        {
            "fact_id": RECONCILIATION_FACT_ID,
            "role": "RECONCILIATION_TARGET_ONLY",
            "unit": "NOT_SIZING_SOURCE",
            "authority": CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
            "binding_status": "OPTIONAL_COMPARE_NEVER_SOURCE",
            "forbidden_as": "SOURCE,VALUE_COPY",
            "already_net_of_u04": FALSE_TOKEN,
        },
    )


def classify_producer_algebra_v1() -> dict[str, str]:
    return {
        "algebra_id": ALGEBRA_ID,
        "formula": "AVAILABLE_FOR_SIZING=BASE-U04-P01_IF_APPLIES",
        "base_already_net_of_u04": FALSE_TOKEN,
        "u04_application": CURRENT_PRODUCTIVE_U04_CURRENT_APPLICATION,
        "p01_application": "SUBTRACT_ONLY_IF_APPLIES_UNKNOWN_FAIL_CLOSED_ZERO_ONLY_EXPLICIT",
        "output_unit": OUTPUT_UNIT,
        "output_currency": REQUIRED_SETTLEMENT_CURRENCY,
        "double_counting_guard": "U04_ONCE_P01_NOT_U04_EQ_NOT_IN_FORMULA_FORBIDDEN_FIELDS_NOT_IN_FORMULA",
        "minting": FALSE_TOKEN,
        "legacy_kind_set_input": FALSE_TOKEN,
        "eq_role": CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
        "freshness_policy": PRETRADE_FRESHNESS_POLICY,
        "restart_policy": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_RESTART_POLICY,
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
    u04_applied: str = FALSE_TOKEN,
    p01_applied: str = FALSE_TOKEN,
    reconciliation_status: str = "NOT_COMPARED",
) -> CurrentProductiveAvailableForSizingProducerOutputV1:
    unique = tuple(dict.fromkeys(reasons))
    return CurrentProductiveAvailableForSizingProducerOutputV1(
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
        u04_applied=u04_applied,
        p01_applied=p01_applied,
        double_counting_guard="U04_ONCE_AFTER_BASE_P01_DISTINCT_EQ_NOT_IN_FORMULA",
        reconciliation_status=reconciliation_status,
        restart_reconstruction_status=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_RESTART_POLICY,
        reason_codes=unique,
        step_29p_risk_admissible=FALSE_TOKEN,
    )


def _validate_scope_and_freshness(
    *,
    settlement_currency: str,
    bound_account_identity: str,
    bound_venue_identity: str,
    bound_td_mode: str,
    decision_epoch: str,
    observed_at_as_of: str,
    age_seconds: str,
    freshness_max_age: str,
    expected_account: str,
    expected_venue: str,
    expected_td_mode: str,
    expected_epoch: str,
    source_class: str,
    field: str,
) -> list[str]:
    reasons: list[str] = []
    if settlement_currency != REQUIRED_SETTLEMENT_CURRENCY:
        reasons.append(f"{field}_CURRENCY_NOT_USDC")
    if bound_account_identity == "" or bound_venue_identity == "" or bound_td_mode == "":
        reasons.append(f"{field}_ACCOUNT_SCOPE_MISSING")
    elif (
        bound_account_identity != expected_account
        or bound_venue_identity != expected_venue
        or bound_td_mode != expected_td_mode
    ):
        reasons.append(f"{field}_ACCOUNT_SCOPE_MISMATCH")
    if bound_td_mode != REQUIRED_TD_MODE:
        reasons.append(f"{field}_TD_MODE_NOT_CROSS")
    if decision_epoch == "" or observed_at_as_of == "":
        reasons.append(f"{field}_EPOCH_MISSING")
    elif decision_epoch != expected_epoch or observed_at_as_of != expected_epoch:
        reasons.append(f"{field}_EPOCH_MISMATCH")
    age = _parse_age_seconds(age_seconds)
    max_age = _parse_age_seconds(freshness_max_age)
    if age is None or max_age is None:
        reasons.append(f"{field}_FRESHNESS_UNKNOWN")
    else:
        if (
            max_age > NUMERIC_EQUITY_TTL_SECONDS
            or age > max_age
            or age > NUMERIC_EQUITY_TTL_SECONDS
        ):
            reasons.append(f"{field}_STALE")
    if _source_class_is_forbidden(source_class):
        reasons.append(f"{field}_FORBIDDEN_OR_UNCLASSIFIED_SOURCE_CLASS")
    return reasons


def produce_current_productive_available_for_sizing_v1(
    *,
    base: CurrentProductiveAvailableForSizingBaseFactV1 | None,
    u04: CurrentProductiveU04ReservationFactV1 | None,
    p01: CurrentProductiveP01ReductionFactV1 | None,
    eligibility: CurrentProductiveAccountEligibilityFactV1 | None,
    eq_target: CurrentProductiveEqReconciliationTargetV1 | None = None,
    restart_from_kind_set: str = FALSE_TOKEN,
) -> CurrentProductiveAvailableForSizingProducerOutputV1:
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_MINT_AUTHORIZED is True:
        raise CurrentProductiveAvailableForSizingProducerError(
            "PRODUCER_MINT_MUST_REMAIN_UNAUTHORIZED"
        )
    if restart_from_kind_set != FALSE_TOKEN:
        reject_kind_set_restart_restore_v1(claimed=restart_from_kind_set)
    reasons: list[str] = []
    if base is None:
        return _fail(reasons=("BASE_FACT_MISSING", "NO_MINT_WITHOUT_BOUND_INPUTS"))
    if u04 is None:
        reasons.append("U04_FACT_MISSING")
    if p01 is None:
        reasons.append("P01_FACT_MISSING")
    if eligibility is None:
        reasons.append("ELIGIBILITY_FACT_MISSING")
    if reasons:
        return _fail(
            reasons=tuple(reasons),
            decision_epoch=base.decision_epoch,
            observed_at_as_of=base.observed_at_as_of,
            bound_account_identity=base.bound_account_identity,
            bound_venue_identity=base.bound_venue_identity,
            bound_td_mode=base.bound_td_mode,
        )
    assert u04 is not None
    assert p01 is not None
    assert eligibility is not None
    if base.fact_id != CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID:
        reasons.append("BASE_FACT_ID_MISMATCH")
    if u04.fact_id != U04_FACT_ID:
        reasons.append("U04_FACT_ID_MISMATCH")
    if p01.fact_id != P01_FACT_ID:
        reasons.append("P01_FACT_ID_MISMATCH")
    if eligibility.fact_id != ELIGIBILITY_FACT_ID:
        reasons.append("ELIGIBILITY_FACT_ID_MISMATCH")
    if base.already_net_of_u04 != FALSE_TOKEN:
        reasons.append("BASE_MUST_NOT_BE_NET_OF_U04")
    if eligibility.account_mode != REQUIRED_ACCOUNT_MODE:
        reasons.append("ACCOUNT_MODE_INELIGIBLE")
    reasons.extend(
        _validate_scope_and_freshness(
            settlement_currency=base.settlement_currency,
            bound_account_identity=base.bound_account_identity,
            bound_venue_identity=base.bound_venue_identity,
            bound_td_mode=base.bound_td_mode,
            decision_epoch=base.decision_epoch,
            observed_at_as_of=base.observed_at_as_of,
            age_seconds=base.age_seconds,
            freshness_max_age=base.freshness_max_age,
            expected_account=base.bound_account_identity,
            expected_venue=base.bound_venue_identity,
            expected_td_mode=base.bound_td_mode,
            expected_epoch=base.decision_epoch,
            source_class=base.source_class,
            field="BASE",
        )
    )
    reasons.extend(
        _validate_scope_and_freshness(
            settlement_currency=u04.settlement_currency,
            bound_account_identity=u04.bound_account_identity,
            bound_venue_identity=u04.bound_venue_identity,
            bound_td_mode=u04.bound_td_mode,
            decision_epoch=u04.decision_epoch,
            observed_at_as_of=u04.observed_at_as_of,
            age_seconds=u04.age_seconds,
            freshness_max_age=u04.freshness_max_age,
            expected_account=base.bound_account_identity,
            expected_venue=base.bound_venue_identity,
            expected_td_mode=base.bound_td_mode,
            expected_epoch=base.decision_epoch,
            source_class=u04.source_class,
            field="U04",
        )
    )
    reasons.extend(
        _validate_scope_and_freshness(
            settlement_currency=p01.settlement_currency,
            bound_account_identity=p01.bound_account_identity,
            bound_venue_identity=p01.bound_venue_identity,
            bound_td_mode=p01.bound_td_mode,
            decision_epoch=p01.decision_epoch,
            observed_at_as_of=p01.observed_at_as_of,
            age_seconds=p01.age_seconds,
            freshness_max_age=p01.freshness_max_age,
            expected_account=base.bound_account_identity,
            expected_venue=base.bound_venue_identity,
            expected_td_mode=base.bound_td_mode,
            expected_epoch=base.decision_epoch,
            source_class=p01.source_class,
            field="P01",
        )
    )
    if (
        eligibility.bound_account_identity != base.bound_account_identity
        or eligibility.bound_venue_identity != base.bound_venue_identity
        or eligibility.bound_td_mode != base.bound_td_mode
        or eligibility.decision_epoch != base.decision_epoch
    ):
        reasons.append("ELIGIBILITY_SCOPE_OR_EPOCH_MISMATCH")
    if "u04" in _fold(p01.source_class) or "ordfrozen" in _fold(p01.source_class):
        reasons.append("P01_MUST_NOT_ENCODE_U04")
    base_value = _parse_non_negative_decimal(base.value, field="base")
    if base_value is None:
        reasons.append("BASE_VALUE_INVALID")
    u04_value = _parse_non_negative_decimal(u04.value, field="u04")
    if u04_value is None:
        reasons.append("U04_VALUE_INVALID")
    elif u04_value == 0 and u04.empty_reservation_proven != TRUE_TOKEN:
        reasons.append("U04_ZERO_WITHOUT_EMPTY_RESERVATION_PROOF")
    p01_state = str(p01.applicability_state or "").strip()
    p01_value = Decimal("0")
    p01_applied = FALSE_TOKEN
    if p01_state == P01_UNKNOWN or p01_state == "":
        reasons.append("P01_APPLICABILITY_UNKNOWN_FAIL_CLOSED")
    elif p01_state == P01_DOES_NOT_APPLY:
        parsed_p01 = _parse_non_negative_decimal(p01.value, field="p01")
        if p01.value not in {"", "0"} and parsed_p01 not in {None, Decimal("0")}:
            reasons.append("P01_DOES_NOT_APPLY_NONZERO_FORBIDDEN")
    elif p01_state == P01_APPLIES:
        parsed_p01 = _parse_non_negative_decimal(p01.value, field="p01")
        if parsed_p01 is None:
            reasons.append("P01_VALUE_INVALID")
        else:
            p01_value = parsed_p01
            p01_applied = TRUE_TOKEN
    else:
        reasons.append("P01_APPLICABILITY_UNKNOWN_FAIL_CLOSED")
    digest = hashlib.sha256(
        _canonical_json(
            {
                "base": base.__dict__,
                "u04": u04.__dict__,
                "p01": p01.__dict__,
                "eligibility": eligibility.__dict__,
            }
        ).encode("utf-8")
    ).hexdigest()
    if reasons:
        return _fail(
            reasons=tuple(reasons),
            decision_epoch=base.decision_epoch,
            observed_at_as_of=base.observed_at_as_of,
            bound_account_identity=base.bound_account_identity,
            bound_venue_identity=base.bound_venue_identity,
            bound_td_mode=base.bound_td_mode,
            input_set_digest=digest,
        )
    assert base_value is not None
    assert u04_value is not None
    available = base_value - u04_value - p01_value
    if available < 0 or not available.is_finite():
        return _fail(
            reasons=("AVAILABLE_FOR_SIZING_NEGATIVE_OR_NON_FINITE",),
            decision_epoch=base.decision_epoch,
            observed_at_as_of=base.observed_at_as_of,
            bound_account_identity=base.bound_account_identity,
            bound_venue_identity=base.bound_venue_identity,
            bound_td_mode=base.bound_td_mode,
            input_set_digest=digest,
            u04_applied=TRUE_TOKEN,
            p01_applied=p01_applied,
        )
    reconciliation_status = "NOT_COMPARED"
    if eq_target is not None:
        if eq_target.fact_id != RECONCILIATION_FACT_ID:
            return _fail(
                reasons=("EQ_TARGET_FACT_ID_MISMATCH",),
                decision_epoch=base.decision_epoch,
                observed_at_as_of=base.observed_at_as_of,
                bound_account_identity=base.bound_account_identity,
                bound_venue_identity=base.bound_venue_identity,
                bound_td_mode=base.bound_td_mode,
                input_set_digest=digest,
                u04_applied=TRUE_TOKEN,
                p01_applied=p01_applied,
            )
        if eq_target.compare_requested == TRUE_TOKEN:
            eq_value = _parse_non_negative_decimal(eq_target.value, field="eq")
            if eq_value is None:
                reconciliation_status = "EQ_TARGET_INVALID_BLOCK"
                return _fail(
                    reasons=("EQ_RECONCILIATION_TARGET_INVALID",),
                    decision_epoch=base.decision_epoch,
                    observed_at_as_of=base.observed_at_as_of,
                    bound_account_identity=base.bound_account_identity,
                    bound_venue_identity=base.bound_venue_identity,
                    bound_td_mode=base.bound_td_mode,
                    input_set_digest=digest,
                    u04_applied=TRUE_TOKEN,
                    p01_applied=p01_applied,
                    reconciliation_status=reconciliation_status,
                )
            if (
                eq_target.bound_account_identity != base.bound_account_identity
                or eq_target.bound_venue_identity != base.bound_venue_identity
                or eq_target.bound_td_mode != base.bound_td_mode
                or eq_target.decision_epoch != base.decision_epoch
                or eq_target.settlement_currency != REQUIRED_SETTLEMENT_CURRENCY
            ):
                return _fail(
                    reasons=("EQ_RECONCILIATION_SCOPE_MISMATCH",),
                    decision_epoch=base.decision_epoch,
                    observed_at_as_of=base.observed_at_as_of,
                    bound_account_identity=base.bound_account_identity,
                    bound_venue_identity=base.bound_venue_identity,
                    bound_td_mode=base.bound_td_mode,
                    input_set_digest=digest,
                    u04_applied=TRUE_TOKEN,
                    p01_applied=p01_applied,
                    reconciliation_status="EQ_SCOPE_BLOCK",
                )
            if eq_value < available:
                return _fail(
                    reasons=("EQ_RECONCILIATION_DIVERGENCE_BLOCK",),
                    decision_epoch=base.decision_epoch,
                    observed_at_as_of=base.observed_at_as_of,
                    bound_account_identity=base.bound_account_identity,
                    bound_venue_identity=base.bound_venue_identity,
                    bound_td_mode=base.bound_td_mode,
                    input_set_digest=digest,
                    u04_applied=TRUE_TOKEN,
                    p01_applied=p01_applied,
                    reconciliation_status="DIVERGENCE_BLOCK_EQ_NOT_SOURCE",
                )
            reconciliation_status = "COMPARED_NO_BLOCKING_DIVERGENCE_EQ_NOT_SOURCE"
    value_text = format(available, "f")
    return CurrentProductiveAvailableForSizingProducerOutputV1(
        produced=TRUE_TOKEN,
        value=value_text,
        settlement_currency=REQUIRED_SETTLEMENT_CURRENCY,
        dimension_id=RISK_EQUITY_DIMENSION,
        producer_identity=PRODUCER_IDENTITY,
        algebra_id=ALGEBRA_ID,
        output_unit=OUTPUT_UNIT,
        output_class=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_OUTPUT_CLASS,
        bound_account_identity=base.bound_account_identity,
        bound_venue_identity=base.bound_venue_identity,
        bound_td_mode=base.bound_td_mode,
        decision_epoch=base.decision_epoch,
        observed_at_as_of=base.observed_at_as_of,
        input_set_digest=digest,
        u04_applied=TRUE_TOKEN,
        p01_applied=p01_applied,
        double_counting_guard="U04_ONCE_AFTER_BASE_P01_DISTINCT_EQ_NOT_IN_FORMULA",
        reconciliation_status=reconciliation_status,
        restart_reconstruction_status=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_RESTART_POLICY,
        reason_codes=("AVAILABLE_FOR_SIZING_PRODUCED", ALGEBRA_ID),
        step_29p_risk_admissible=FALSE_TOKEN,
    )


def restart_current_productive_available_for_sizing_v1(
    *,
    restore_from_kind_set: str,
    base: CurrentProductiveAvailableForSizingBaseFactV1 | None,
    u04: CurrentProductiveU04ReservationFactV1 | None,
    p01: CurrentProductiveP01ReductionFactV1 | None,
    eligibility: CurrentProductiveAccountEligibilityFactV1 | None,
    eq_target: CurrentProductiveEqReconciliationTargetV1 | None = None,
) -> CurrentProductiveAvailableForSizingProducerOutputV1:
    reject_kind_set_restart_restore_v1(claimed=restore_from_kind_set)
    return produce_current_productive_available_for_sizing_v1(
        base=base,
        u04=u04,
        p01=p01,
        eligibility=eligibility,
        eq_target=eq_target,
        restart_from_kind_set=FALSE_TOKEN,
    )


def bind_step_29p_typed_equity_from_producer_v1(
    *,
    output: CurrentProductiveAvailableForSizingProducerOutputV1,
    fresh_pretrade_get_status: str,
    live_account_bound_status: str,
    expected_instrument_id: str,
    observed_instrument_id: str,
    fresh_evidence_fetched: bool,
    fresh_evidence_validated: bool,
) -> Step29PCapitalRiskAdmissibilityClaimV1:
    raw = output.value if output.produced == TRUE_TOKEN else ""
    source_field = PRODUCER_IDENTITY if output.produced == TRUE_TOKEN else ""
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
    if LIVE_ARMED is not False:
        raise CurrentProductiveAvailableForSizingProducerError("LIVE_ARMED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise CurrentProductiveAvailableForSizingProducerError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED is not True:
        raise CurrentProductiveAvailableForSizingProducerError(
            "CURRENT_PRODUCTIVE_ARCHITECTURE_NOT_RATIFIED"
        )
    if CURRENT_PRODUCTIVE_ARCHITECTURE_IS_NOT_HISTORICAL_RECONSTRUCTION is not True:
        raise CurrentProductiveAvailableForSizingProducerError(
            "ARCHITECTURE_MUST_NOT_BE_HISTORICAL_RECONSTRUCTION"
        )
    if LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE is not False:
        raise CurrentProductiveAvailableForSizingProducerError(
            "LEGACY_RECONSTRUCTION_MUST_NOT_BE_REQUIRED_FOR_LIVE"
        )
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveAvailableForSizingProducerError(
            "SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED"
        )
    if CURRENT_PRODUCTIVE_SOURCE_SELECTED is not False:
        raise CurrentProductiveAvailableForSizingProducerError(
            "VENUE_OR_CENSUS_SOURCE_MUST_REMAIN_UNSELECTED"
        )
    if CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED is not False:
        raise CurrentProductiveAvailableForSizingProducerError(
            "EQUITY_AUTHORITY_PRODUCER_MINT_MUST_REMAIN_UNAUTHORIZED"
        )
    if GOVERNED_PRODUCER_CREATED is not False:
        raise CurrentProductiveAvailableForSizingProducerError(
            "ACCOUNT_EQUITY_AUTHORITY_PRODUCER_SLOT_MUST_REMAIN_EMPTY"
        )
    if SLOT_IS_EMPTY is not True:
        raise CurrentProductiveAvailableForSizingProducerError("PRODUCER_SLOT_MUST_BE_EMPTY")
    if SOURCE_SELECTED is not False:
        raise CurrentProductiveAvailableForSizingProducerError("SOURCE_SELECTED_MUST_BE_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise CurrentProductiveAvailableForSizingProducerError("RAW_EQ_SOURCE_AUTHORITY_TRUE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise CurrentProductiveAvailableForSizingProducerError(
            "EQ_MUST_REMAIN_RECONCILIATION_TARGET_ONLY"
        )
    if EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is not False:
        raise CurrentProductiveAvailableForSizingProducerError("EQ_TREATED_AS_SOURCE")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise CurrentProductiveAvailableForSizingProducerError("MAPPING_MUST_REMAIN_INVALID")
    if MAPPING_PROVEN is not False:
        raise CurrentProductiveAvailableForSizingProducerError("MAPPING_PROVEN_TRUE")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise CurrentProductiveAvailableForSizingProducerError("ALGEBRA_MUST_REMAIN_INCOMPLETE")
    if KIND_SET_RESOLVED is not False:
        raise CurrentProductiveAvailableForSizingProducerError("KIND_SET_RESOLVED_TRUE")
    if KIND_SET_UPLIFT_THIS_WORKPACKAGE is not False:
        raise CurrentProductiveAvailableForSizingProducerError("KIND_SET_UPLIFT_FORBIDDEN")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_RATIFIED is not True:
        raise CurrentProductiveAvailableForSizingProducerError("CS_SELECTION_MUST_REMAIN_RATIFIED")
    if CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE != NONE_TOKEN:
        raise CurrentProductiveAvailableForSizingProducerError(
            "VENUE_SELECTED_SOURCE_MUST_REMAIN_NONE"
        )
    if CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED is not False:
        raise CurrentProductiveAvailableForSizingProducerError("FRESH_GET_MUST_REMAIN_FALSE")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_CREATED is not True:
        raise CurrentProductiveAvailableForSizingProducerError("SIZING_PRODUCER_MUST_BE_CREATED")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IS_SOURCE_OBJECT is not True:
        raise CurrentProductiveAvailableForSizingProducerError("PRODUCER_MUST_BE_THE_SOURCE_OBJECT")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_MINT_AUTHORIZED is not False:
        raise CurrentProductiveAvailableForSizingProducerError("SIZING_PRODUCER_MINT_FORBIDDEN")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS != "UNBOUND":
        raise CurrentProductiveAvailableForSizingProducerError("BASE_MUST_REMAIN_UNBOUND")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS != "UNBOUND":
        raise CurrentProductiveAvailableForSizingProducerError(
            "SIZING_SOURCE_VALUE_MUST_REMAIN_UNBOUND"
        )
    if CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS != "UNBOUND":
        raise CurrentProductiveAvailableForSizingProducerError("STOCK_SOURCE_MUST_REMAIN_UNBOUND")
    if CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY != (
        "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND"
    ):
        raise CurrentProductiveAvailableForSizingProducerError("STANDING_UNBOUND_DEPENDENCY_DRIFT")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION != RISK_EQUITY_DIMENSION:
        raise CurrentProductiveAvailableForSizingProducerError("SIZING_DIMENSION_DRIFT")
    if CURRENT_PRODUCTIVE_U04_CURRENT_APPLICATION != "SUBTRACT_AFTER_BASE_ONCE_NOT_SOURCE":
        raise CurrentProductiveAvailableForSizingProducerError("U04_CURRENT_APPLICATION_DRIFT")
    if U04_LEGACY_STATUS != STATE_UNRESOLVED:
        raise CurrentProductiveAvailableForSizingProducerError("LEGACY_U04_UNRESOLVED_PRESERVED")
    if U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE != STATE_UNRESOLVED:
        raise CurrentProductiveAvailableForSizingProducerError(
            "U04_INCLUSION_MUST_REMAIN_UNRESOLVED"
        )
    if PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP != "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET":
        raise CurrentProductiveAvailableForSizingProducerError("PRODUCTIVE_U04_MEMBERSHIP_DRIFT")
    if PRODUCTIVE_U04_EQUITY_STOCK_ROLE != DISPOSITION_NOT_EQUITY_STOCK:
        raise CurrentProductiveAvailableForSizingProducerError("U04_STOCK_ROLE_DRIFT")
    if PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise CurrentProductiveAvailableForSizingProducerError("U04_SIZING_ROLE_DRIFT")
    if U04_PLACEMENT != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise CurrentProductiveAvailableForSizingProducerError("U04_PLACEMENT_DRIFT")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductiveAvailableForSizingProducerError("U05_UNKNOWN_PRESERVED")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductiveAvailableForSizingProducerError("U06_UNKNOWN_PRESERVED")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductiveAvailableForSizingProducerError("RESIDUAL_UNKNOWN_PRESERVED")
    if STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER is not True:
        raise CurrentProductiveAvailableForSizingProducerError("STEP_29P_MUST_REMAIN_CONSUMER")
    if CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS != "BOUND_AVAILABLE_FOR_SIZING_ONLY":
        raise CurrentProductiveAvailableForSizingProducerError("29P_CONSUMER_BINDING_DRIFT")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise CurrentProductiveAvailableForSizingProducerError("LEGACY_DAG_PIN_DRIFT")
    reject_eq_as_source_authority_v1(claimed=FALSE_TOKEN)
    reject_eq_authority_uplift_v1(claimed=FALSE_TOKEN)
    reject_kind_set_uplift_v1(claimed=FALSE_TOKEN)
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=DISPOSITION_NOT_EQUITY_STOCK)
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_equity_stock_as_29p_sizing_input_v1(claimed=FALSE_TOKEN)
    reject_available_for_sizing_mint_without_source_v1(claimed=FALSE_TOKEN)
    reject_layer_mix_stock_and_sizing_v1(claimed=FALSE_TOKEN)
    reject_legacy_reconstruction_as_live_requirement_v1(claimed=FALSE_TOKEN)
    reject_forbidden_venue_field_as_source_v1(claimed="cashBal_not_bound")
    reject_max_size_contracts_as_usdc_equity_source_v1(claimed=FALSE_TOKEN)
    reject_u04_as_sizing_source_v1(claimed=FALSE_TOKEN)
    reject_unclassified_field_plausibility_bind_v1(claimed=FALSE_TOKEN)
    reject_empty_producer_slot_as_source_v1(claimed=FALSE_TOKEN)
    reject_eq_copied_into_sizing_value_v1(claimed=FALSE_TOKEN)
    reject_unclassified_algebra_input_v1(claimed=FALSE_TOKEN)
    reject_kind_set_restart_restore_v1(claimed=FALSE_TOKEN)


def _assert_parent_cs_pack_sealed(*, repo_root: Path) -> None:
    pack = repo_root / CANONICAL_CS_PACK_RELPATH
    claims_path = pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise CurrentProductiveAvailableForSizingProducerError("PARENT_CS_PACK_MISSING")
    claims = _load_json_object(path=claims_path)
    if claims.get("AVAILABLE_FOR_SIZING_SOURCE_STATUS") != "UNBOUND":
        raise CurrentProductiveAvailableForSizingProducerError("PARENT_CS_SOURCE_DRIFT")
    if claims.get("SELECTED_SOURCE") != NONE_TOKEN:
        raise CurrentProductiveAvailableForSizingProducerError("PARENT_CS_SELECTED_DRIFT")
    if claims.get("SEALED_LEGACY_CENSUS_REOPENED") != FALSE_TOKEN:
        raise CurrentProductiveAvailableForSizingProducerError("PARENT_CS_CENSUS_REOPENED")
    if claims.get("NEXT_OWNER_GO_REQUIRED") != PIN_OWNER_GO:
        raise CurrentProductiveAvailableForSizingProducerError("PARENT_CS_NEXT_GO_DRIFT")
    if verify_manifest_sha256_v1(store_root=pack) != 0:
        raise CurrentProductiveAvailableForSizingProducerError("PARENT_CS_MANIFEST_VERIFY_NOT_ZERO")


def execute_current_productive_available_for_sizing_producer_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    persist_as_of: str = CANONICAL_PERSIST_AS_OF,
    repo_root: Path | str | None = None,
) -> CurrentProductiveAvailableForSizingProducerPersistResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveAvailableForSizingProducerError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveAvailableForSizingProducerError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    _assert_parent_cs_pack_sealed(repo_root=root)
    as_of = str(persist_as_of or "").strip()
    if as_of == "":
        raise CurrentProductiveAvailableForSizingProducerError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    facts = classify_producer_input_facts_v1()
    algebra = classify_producer_algebra_v1()
    missing = produce_current_productive_available_for_sizing_v1(
        base=None,
        u04=None,
        p01=None,
        eligibility=None,
    )
    if missing.produced != FALSE_TOKEN or missing.value != "":
        raise CurrentProductiveAvailableForSizingProducerError("UNBOUND_PRODUCE_MUST_NOT_MINT")
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": PIN_OWNER_GO_STATUS,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CS_PACK": CANONICAL_CS_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "EPISTEMIC_CLASS": "CURRENT_PRODUCTIVE_DESIGN",
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CT",
        "LEGACY_SEALED_UNKNOWN": "CQ_KIND_SET_EMPTY_AND_CR_FOUR_LAYER_MODEL_AND_CS_NO_VENUE_FIELD",
        "FORENSIC_EVIDENCE": "CURRENT_29P_CONSUMER_AND_CURRENT_PRODUCTIVE_TYPED_FACTS",
        "ADJUDICATED": "PRODUCER_DEFINED_AS_SOURCE_OBJECT_BASE_FACT_UNBOUND",
        "INTERPRETATION": "PRODUCER_PRESENT_NO_MINT",
        "HYPOTHESIS": "BASE_REQUIRES_NON_FORBIDDEN_CURRENT_PRODUCTIVE_OBSERVATION",
        "UNRESOLVED": BLOCKER_ID,
        "START_BLOCK": PARENT_BLOCKER_ID,
        "LEGACY_SEALED_FULL_CORE_DAG_PIN": DAG_PIN,
        "LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE": FALSE_TOKEN,
        "SEALED_LEGACY_CENSUS_REOPENED": FALSE_TOKEN,
        "CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL": CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
        "CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED": TRUE_TOKEN,
        "CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE": CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE,
        "CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE": CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS,
        "CURRENT_PRODUCTIVE_EQUITY_SOURCE": "PRODUCER_DEFINED_BASE_INPUT_UNBOUND",
        "RECONCILIATION_TARGET": "eq",
        "RECONCILIATION_TARGET_STATUS": CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
        "AVAILABLE_FOR_SIZING_MODEL": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
        "AVAILABLE_FOR_SIZING_SOURCE_STATUS": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
        "AVAILABLE_FOR_SIZING_PRODUCER_CREATED": TRUE_TOKEN,
        "AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY": PRODUCER_IDENTITY,
        "AVAILABLE_FOR_SIZING_PRODUCER_ALGEBRA": ALGEBRA_ID,
        "AVAILABLE_FOR_SIZING_BASE_FACT": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
        "AVAILABLE_FOR_SIZING_BASE_STATUS": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
        "SELECTED_SOURCE_OBJECT": PRODUCER_IDENTITY,
        "VENUE_SELECTED_SOURCE": NONE_TOKEN,
        "U04_ROLE": PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
        "U04_EQUITY_STOCK_ROLE": DISPOSITION_NOT_EQUITY_STOCK,
        "U04_APPLICATION": CURRENT_PRODUCTIVE_U04_CURRENT_APPLICATION,
        "U04_LEGACY_STATUS": STATE_UNRESOLVED,
        "U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE": STATE_UNRESOLVED,
        "U05_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_REOPENED": FALSE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_UPLIFT_THIS_WORKPACKAGE": FALSE_TOKEN,
        "EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE": FALSE_TOKEN,
        "AUTHORITY_UPLIFT": FALSE_TOKEN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "MAPPING_PROVEN": FALSE_TOKEN,
        "SOURCE_SELECTED": FALSE_TOKEN,
        "GOVERNED_PRODUCER_CREATED": FALSE_TOKEN,
        "PRODUCER_MINT_AUTHORIZED": FALSE_TOKEN,
        "STEP_29P_CONSUMER_BINDING_STATUS": CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS,
        "STEP_29P_PRODUCER_BINDING_STATUS": (
            CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_29P_BINDING_STATUS
        ),
        "STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER": TRUE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE": FALSE_TOKEN,
        "RESTART_RECONSTRUCTION_STATUS": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_RESTART_POLICY,
        "STEP_29P_BINDING_STATUS": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_29P_BINDING_STATUS,
        "CURRENT_LIVE_CRITICAL_BLOCKER": BLOCKER_ID,
        "CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "LIVE_CRITICAL_PATH_FOLLOWS": "CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY",
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "FIRST_DEFINITIVE_BLOCK": BLOCKER_ID,
        "EXACT_MISSING_PREDICATE": EXACT_MISSING_PREDICATE,
        "FRESH_GET_EXECUTED": FALSE_TOKEN,
        "FRESH_GET_NOT_REQUIRED_FOR_PRODUCER_DEFINITION": TRUE_TOKEN,
        "FRESH_GET_NOT_REQUIRED_JUSTIFIED": FRESH_GET_NOT_REQUIRED_JUSTIFIED,
        "NO_GET_REQUIRED": TRUE_TOKEN,
        "NO_HOPE_GET": TRUE_TOKEN,
        "NO_EQ_SOURCE_AUTHORITY": TRUE_TOKEN,
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "VENUE_GET_COUNT": "0",
        "POST_COUNT": "0",
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "LIVE_ENABLED": FALSE_TOKEN,
        "LIVE_ARMED": FALSE_TOKEN,
        "WIRE_SEND_PERMITTED": FALSE_TOKEN,
        "LOCAL_ADVANCEMENT_EXHAUSTED": TRUE_TOKEN,
        "PARENT_BLOCKER_ID": PARENT_BLOCKER_ID,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "NEXT_PRODUCTIVE_NODE": NEXT_PRODUCTIVE_NODE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "ATLAS_AUTHORITY": NONE_TOKEN,
        "FRESHNESS_POLICY": PRETRADE_FRESHNESS_POLICY,
        "OUTPUT_UNIT": OUTPUT_UNIT,
        "OUTPUT_CLASS": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_OUTPUT_CLASS,
        "LAYER": LAYER_AVAILABLE_FOR_SIZING,
        "CONSUMER": STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
    }
    lineage = {
        "layer": "CURRENT_PRODUCTIVE_DESIGN",
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "pin_owner_go": PIN_OWNER_GO,
        "pin_owner_go_status": PIN_OWNER_GO_STATUS,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_cs_pack": CANONICAL_CS_PACK_RELPATH,
        "sealed_legacy_census_reopened": FALSE_TOKEN,
        "historical_artifacts_rewritten": FALSE_TOKEN,
        "legacy_reconstruction_required_for_live": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "venue_source_selected": FALSE_TOKEN,
        "producer_created": TRUE_TOKEN,
        "producer_minted": FALSE_TOKEN,
        "fresh_get_executed": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_consumer_semantics_unchanged": TRUE_TOKEN,
        "trading_logic_unchanged": TRUE_TOKEN,
        "trading_signal_authority_unchanged": TRUE_TOKEN,
        "u04_not_reclassified_as_equity_stock_kind": TRUE_TOKEN,
        "u04_not_used_as_source": TRUE_TOKEN,
        "legacy_u04_unresolved_preserved": TRUE_TOKEN,
        "legacy_u05_unknown_preserved": TRUE_TOKEN,
        "legacy_u06_unknown_preserved": TRUE_TOKEN,
        "legacy_residual_unknown_preserved": TRUE_TOKEN,
        "eq_not_elevated_to_source": TRUE_TOKEN,
        "kind_set_not_uplifted": TRUE_TOKEN,
        "sealed_legacy_census_not_reopened": TRUE_TOKEN,
        "single_selected_future_unchanged": TRUE_TOKEN,
        "max_positions_one_unchanged": TRUE_TOKEN,
        "treasury_untouched": TRUE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "account_equity_authority_slot_empty": TRUE_TOKEN,
        "legacy_dag_pin": DAG_PIN,
    }
    architecture = {
        "layer": "CURRENT_CANONICAL_AUTHORITY",
        "model_version": CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
        "producer_created": TRUE_TOKEN,
        "producer_identity": PRODUCER_IDENTITY,
        "algebra_id": ALGEBRA_ID,
        "selected_source_object": PRODUCER_IDENTITY,
        "venue_selected_source": NONE_TOKEN,
        "base_status": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "current_live_critical_blocker": BLOCKER_ID,
        "standing_unbound_dependency": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "legacy_sealed_dag_pin": DAG_PIN,
        "producer_minted": FALSE_TOKEN,
        "fresh_get_executed": FALSE_TOKEN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
        "atlas_authority": NONE_TOKEN,
    }
    epistemic = {
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CT",
        "CURRENT_PRODUCTIVE_DESIGN": SCHEMA_CLASS,
        "LEGACY_SEALED_UNKNOWN": "CQ_KIND_SET_EMPTY_AND_CR_FOUR_LAYER_MODEL_AND_CS_NO_VENUE_FIELD",
        "FORENSIC_EVIDENCE": "CURRENT_29P_CONSUMER_AND_CURRENT_PRODUCTIVE_TYPED_FACTS",
        "ADJUDICATED": "PRODUCER_DEFINED_AS_SOURCE_OBJECT_BASE_FACT_UNBOUND",
        "INTERPRETATION": "PRODUCER_PRESENT_NO_MINT",
        "HYPOTHESIS": "BASE_REQUIRES_NON_FORBIDDEN_CURRENT_PRODUCTIVE_OBSERVATION",
        "UNRESOLVED": BLOCKER_ID,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(
        path=store / "input_facts_v1.json",
        payload={
            "facts": list(facts),
            "base_status": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
        },
    )
    _persist_json(path=store / "producer_algebra_v1.json", payload=algebra)
    _persist_json(
        path=store / "unbound_produce_v1.json",
        payload={
            "produced": missing.produced,
            "value": missing.value,
            "reason_codes": list(missing.reason_codes),
        },
    )
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "epistemic_separation_v1.json", payload=epistemic)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise CurrentProductiveAvailableForSizingProducerError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise CurrentProductiveAvailableForSizingProducerError("MANIFEST_VERIFY_NOT_ZERO")
    return CurrentProductiveAvailableForSizingProducerPersistResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        producer_created=TRUE_TOKEN,
        producer_identity=PRODUCER_IDENTITY,
        algebra_id=ALGEBRA_ID,
        selected_source_object=PRODUCER_IDENTITY,
        base_status=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
        available_for_sizing_source_status=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
        fresh_get_executed=FALSE_TOKEN,
        current_live_critical_blocker=BLOCKER_ID,
        first_definitive_block=BLOCKER_ID,
        exact_missing_predicate=EXACT_MISSING_PREDICATE,
        authorized_get_count="0",
        actual_get_count="0",
        post_count="0",
        evidence_manifest=str(store / "MANIFEST.sha256"),
    )


__all__ = (
    "ALGEBRA_ID",
    "ARCHITECTURE_BLOCKER",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "CurrentProductiveAccountEligibilityFactV1",
    "CurrentProductiveAvailableForSizingBaseFactV1",
    "CurrentProductiveAvailableForSizingProducerError",
    "CurrentProductiveAvailableForSizingProducerOutputV1",
    "CurrentProductiveAvailableForSizingProducerPersistResultV1",
    "CurrentProductiveEqReconciliationTargetV1",
    "CurrentProductiveP01ReductionFactV1",
    "CurrentProductiveU04ReservationFactV1",
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "FRESH_GET_NOT_REQUIRED_JUSTIFIED",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "OUTPUT_UNIT",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "PIN_OWNER_GO_STATUS",
    "PRODUCER_IDENTITY",
    "bind_step_29p_typed_equity_from_producer_v1",
    "classify_producer_algebra_v1",
    "classify_producer_input_facts_v1",
    "execute_current_productive_available_for_sizing_producer_v1",
    "produce_current_productive_available_for_sizing_v1",
    "reject_eq_copied_into_sizing_value_v1",
    "reject_kind_set_restart_restore_v1",
    "reject_unclassified_algebra_input_v1",
    "restart_current_productive_available_for_sizing_v1",
)
