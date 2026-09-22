"""Select or bind a current-productive AVAILABLE_FOR_SIZING source.

Consumes Owner-GO SELECT_OR_BIND_A_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE
_NOT_EQ_NOT_LEGACY_KIND_SET_AND_NOT_FORBIDDEN_VENUE_FIELD_V1. Does not reopen
the sealed KIND_SET census. Does not treat venue eq as source. Does not bind
forbidden venue fields. Does not bind unclassified fields by plausibility.
Does not mint. Does not POST. GET is not required for this binding decision
because it cannot un-forbid fields, change the max-size unit contract, or
authorize unclassified fields. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FRESHNESS_POLICY as PRETRADE_FRESHNESS_POLICY,
    REQUIRED_GET_ITEM_SPECS,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    REQUIRED_SETTLEMENT_CURRENCY,
    RISK_EQUITY_DIMENSION,
    STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
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
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_RATIFIED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_STATUS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_TRANSFORMATION,
    CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE,
    CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED,
    CURRENT_PRODUCTIVE_FRESH_GET_NOT_REQUIRED_FOR_BINDING_DECISION,
    CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
    CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
    CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS,
    CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE,
    CURRENT_PRODUCTIVE_SOURCE_SELECTED,
    CURRENT_PRODUCTIVE_U04_APPLICATION_STATUS,
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
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CR_PACK_RELPATH,
    FORBIDDEN_AUTHORITY_FIELDS,
    LAYER_AVAILABLE_FOR_SIZING,
    NEXT_OWNER_GO as PIN_OWNER_GO,
    reject_available_for_sizing_mint_without_source_v1,
    reject_eq_authority_uplift_v1,
    reject_equity_stock_as_29p_sizing_input_v1,
    reject_layer_mix_stock_and_sizing_v1,
    reject_legacy_reconstruction_as_live_requirement_v1,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_observation_v1 import (
    MAX_AVAILABLE_COMPARISON_DOMAIN,
    MAX_AVAILABLE_UNIT,
)

OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SELECT_OR_BIND_A_CURRENT_PRODUCTIVE_AVAILABLE_FOR_"
    "SIZING_SOURCE_NOT_EQ_NOT_LEGACY_KIND_SET_AND_NOT_FORBIDDEN_VENUE_FIELD_V1"
)
EXPECTED_ORIGIN_MAIN_SHA = "4a71bfda358e64d0c136c2ea18b22e08424106b6"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_available_for_sizing_source_selection_v1/"
    "2026-09-15T090000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T09:00:00Z"
SCHEMA_CLASS = "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
STATE_UNRESOLVED = "UNRESOLVED"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
STATUS_REJECTED = "REJECTED"
STATUS_NON_AUTHORITY = "NON_AUTHORITY_UNCLASSIFIED"
SELECTED_SOURCE = NONE_TOKEN
CONSUMER_STEP_29P = "STEP_29P_CAPITAL_RISK_ADMISSIBILITY"
REQUIRED_UNIT = "USDC_ACCOUNT_EQUITY"
FRESH_GET_NOT_REQUIRED_JUSTIFIED = (
    "HOPE_GET_CANNOT_UNFORBID_VENUE_FIELDS_OR_AUTHORIZE_UNCLASSIFIED_FIELDS_"
    "OR_CHANGE_MAX_SIZE_CONTRACTS_UNIT_OR_MINT_EMPTY_PRODUCER_SLOT"
)
EXACT_MISSING_PREDICATE = (
    "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_NO_SEMANTICALLY_ADMISSIBLE_"
    "NON_FORBIDDEN_CANDIDATE_EQ_RECONCILIATION_TARGET_ONLY_FORBIDDEN_FIELDS_"
    "NOT_BOUND_MAX_SIZE_CONTRACTS_NOT_USDC_EQUITY_U04_REDUCTION_NOT_SOURCE_"
    "LEGACY_KIND_SET_NOT_SOURCE_UNCLASSIFIED_FIELDS_NOT_BOUND_BY_PLAUSIBILITY"
)
BLOCKER_ID = (
    "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_NO_SEMANTICALLY_ADMISSIBLE_"
    "NON_FORBIDDEN_CANDIDATE_AFTER_SELECTION"
)
ARCHITECTURE_BLOCKER = (
    "NO_SEMANTICALLY_ADMISSIBLE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_"
    "EQ_REMAINS_RECONCILIATION_TARGET_FORBIDDEN_FIELDS_NOT_BOUND_MAX_SIZE_"
    "WRONG_UNIT_U04_NOT_SOURCE_LEGACY_CENSUS_SEALED"
)
NEXT_PRODUCTIVE_NODE = (
    "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_OBJECT_OUTSIDE_REJECTED_CLASSES"
)
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_OR_AUTHORIZE_A_CURRENT_PRODUCTIVE_AVAILABLE_"
    "FOR_SIZING_SOURCE_OBJECT_OUTSIDE_EQ_FORBIDDEN_VENUE_FIELDS_LEGACY_KIND_"
    "SET_MAX_SIZE_CONTRACTS_AND_U04_AS_SOURCE_V1"
)
NEXT_ACTION = (
    "STOP_NO_SEMANTICALLY_ADMISSIBLE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_"
    "SOURCE_NO_FORBIDDEN_FIELD_BIND_NO_HOPE_GET_NO_LEGACY_RECONSTRUCTION"
)
PIN_OWNER_GO_STATUS = "CONSUMED_SOURCE_NOT_BOUND_NO_ADMISSIBLE_CANDIDATE"
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductiveAvailableForSizingSourceSelectionError(ValueError):
    """Fail-closed current-productive AVAILABLE_FOR_SIZING source selection."""


@dataclass(frozen=True)
class CurrentProductiveAvailableForSizingSourceSelectionResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    selection_ratified: str
    selected_source: str
    selection_status: str
    available_for_sizing_source_status: str
    acceptable_candidate_count: str
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
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            f"JSON_NOT_OBJECT:{path.name}"
        )
    return payload


def reject_forbidden_venue_field_as_source_v1(*, claimed: str) -> None:
    folded = str(claimed or "").strip()
    if folded in FORBIDDEN_AUTHORITY_FIELDS or folded in {
        "details.availEq",
        "details.eq",
        "AVAILEQ",
        "FORBIDDEN_FIELD_BOUND",
    }:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            f"FORBIDDEN_VENUE_FIELD_NOT_AVAILABLE_FOR_SIZING_SOURCE:{claimed}"
        )


def reject_max_size_contracts_as_usdc_equity_source_v1(*, claimed: str) -> None:
    if claimed in {
        "true",
        "TRUE",
        "maxBuy",
        "maxSell",
        "MAX_AVAILABLE",
        "contracts",
        MAX_AVAILABLE_UNIT,
    }:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            f"MAX_SIZE_CONTRACTS_ARE_NOT_USDC_AVAILABLE_FOR_SIZING:{claimed}"
        )


def reject_u04_as_sizing_source_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "SOURCE", "U04_AS_SOURCE", "EQUITY_STOCK_UPLIFT"}:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            f"U04_IS_REDUCTION_NOT_AVAILABLE_FOR_SIZING_SOURCE:{claimed}"
        )


def reject_unclassified_field_plausibility_bind_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "PLAUSIBLE", "BOUND_BY_PLAUSIBILITY"}:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            f"UNCLASSIFIED_VENUE_FIELD_NOT_BOUND_BY_PLAUSIBILITY:{claimed}"
        )


def reject_empty_producer_slot_as_source_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "SOURCE", "MINTED", "SLOT_IS_SOURCE"}:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            f"EMPTY_GOVERNED_PRODUCER_SLOT_IS_NOT_SOURCE:{claimed}"
        )


def _candidate(
    *,
    candidate_id: str,
    surface: str,
    semantic_fit: str,
    unit_currency: str,
    freshness: str,
    availability: str,
    account_scope: str,
    reservation_margin_semantics: str,
    deterministic_transformation: str,
    restart_behavior: str,
    reconciliation: str,
    fail_closed_behavior: str,
    disposition: str,
    rejection_reason: str,
) -> dict[str, str]:
    return {
        "candidate_id": candidate_id,
        "surface": surface,
        "semantic_fit": semantic_fit,
        "unit_currency": unit_currency,
        "freshness": freshness,
        "availability": availability,
        "account_scope": account_scope,
        "reservation_margin_semantics": reservation_margin_semantics,
        "deterministic_transformation": deterministic_transformation,
        "restart_behavior": restart_behavior,
        "reconciliation": reconciliation,
        "fail_closed_behavior": fail_closed_behavior,
        "selected": FALSE_TOKEN,
        "disposition": disposition,
        "rejection_reason": rejection_reason,
    }


def classify_step_29p_required_semantics_v1() -> dict[str, str]:
    return {
        "consumer": CONSUMER_STEP_29P,
        "authority": STEP_29P_RISK_ADMISSIBILITY_AUTHORITY,
        "required_dimension": RISK_EQUITY_DIMENSION,
        "required_settlement_currency": REQUIRED_SETTLEMENT_CURRENCY,
        "required_unit": REQUIRED_UNIT,
        "layer": LAYER_AVAILABLE_FOR_SIZING,
        "consumer_binding_status": CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS,
        "source_binding_status": "CONSUMER_BOUND_SOURCE_UNBOUND",
        "stock_is_not_29p_input": TRUE_TOKEN,
        "eq_is_not_source": TRUE_TOKEN,
        "u04_is_not_source": TRUE_TOKEN,
        "freshness_policy": PRETRADE_FRESHNESS_POLICY,
        "empty_data_is_zero": FALSE_TOKEN,
        "typed_account_equity_required": TRUE_TOKEN,
        "forbidden_authority_fields": ",".join(FORBIDDEN_AUTHORITY_FIELDS),
        "step_29p_is_not_equity_authority_owner": TRUE_TOKEN,
    }


def classify_current_productive_source_candidates_v1() -> Tuple[dict[str, str], ...]:
    other_gets = ",".join(
        spec.item_id
        for spec in REQUIRED_GET_ITEM_SPECS
        if spec.item_id not in {"AVAILABLE_MARGIN", "MAX_AVAILABLE"}
    )
    return (
        _candidate(
            candidate_id="CP_S01_VENUE_EQ",
            surface="eq",
            semantic_fit="RECONCILIATION_TARGET_NOT_AVAILABLE_FOR_SIZING",
            unit_currency="NOT_SIZING_SOURCE",
            freshness="IRRELEVANT_AS_FORBIDDEN_SOURCE",
            availability="PRESENT_AS_RECONCILIATION_OBJECT_ONLY",
            account_scope="TRADING_ACCOUNT_IF_OBSERVED",
            reservation_margin_semantics="NOT_RESERVATION",
            deterministic_transformation="FORBIDDEN",
            restart_behavior="MUST_NOT_RECONSTRUCT_SIZING_FROM_EQ",
            reconciliation="EQ_RECONCILIATION_TARGET_ONLY",
            fail_closed_behavior="REJECT_AS_SOURCE",
            disposition=STATUS_REJECTED,
            rejection_reason="EQ_RECONCILIATION_TARGET_ONLY",
        ),
        _candidate(
            candidate_id="CP_S02_FORBIDDEN_AVAILEQ",
            surface="availEq|details.availEq",
            semantic_fit="AVAILABLE_MARGIN_OBSERVATION_NOT_29P_AUTHORITY",
            unit_currency="USDC_OR_OBSERVED_CCY_BUT_FORBIDDEN_AS_SOURCE",
            freshness="FRESH_GET_WOULD_NOT_UNFORBID",
            availability="CURRENT_PRODUCTIVE_GET_SURFACE_AVAILABLE_MARGIN",
            account_scope="BOUND_TRADING_ACCOUNT",
            reservation_margin_semantics="AVAILABLE_MARGIN_NOT_SIZING_AUTHORITY",
            deterministic_transformation="FORBIDDEN",
            restart_behavior="MUST_NOT_RESTART_FROM_FORBIDDEN_FIELD",
            reconciliation="NOT_EQ_AND_NOT_SIZING_SOURCE",
            fail_closed_behavior="REJECT_FORBIDDEN_VENUE_FIELD",
            disposition=STATUS_REJECTED,
            rejection_reason="FORBIDDEN_VENUE_FIELD",
        ),
        _candidate(
            candidate_id="CP_S03_FORBIDDEN_RAW_EQUITY_BALANCE_FIELDS",
            surface="totalEq|adjEq|availBal|cashBal",
            semantic_fit="STOCK_OR_BALANCE_NOT_RATIFIED_AVAILABLE_FOR_SIZING",
            unit_currency="MIXED_OR_NON_AUTHORITY",
            freshness="FRESH_GET_WOULD_NOT_UNFORBID",
            availability="VENUE_BALANCE_PAYLOAD_FIELDS",
            account_scope="BOUND_TRADING_ACCOUNT",
            reservation_margin_semantics="NOT_RATIFIED_AVAILABLE_FOR_SIZING",
            deterministic_transformation="FORBIDDEN",
            restart_behavior="MUST_NOT_RESTART_FROM_FORBIDDEN_FIELD",
            reconciliation="NOT_SOURCE",
            fail_closed_behavior="REJECT_FORBIDDEN_VENUE_FIELD",
            disposition=STATUS_REJECTED,
            rejection_reason="FORBIDDEN_VENUE_FIELD",
        ),
        _candidate(
            candidate_id="CP_S04_MAX_SIZE_CONTRACTS",
            surface="GET /api/v5/account/max-size maxBuy|maxSell",
            semantic_fit="VENUE_MAX_AVAILABLE_QUANTITY_NOT_ACCOUNT_EQUITY",
            unit_currency=f"{MAX_AVAILABLE_UNIT}:{MAX_AVAILABLE_COMPARISON_DOMAIN}",
            freshness="FRESH_GET_PER_PRETRADE_WHEN_PERFORMED",
            availability="CURRENT_PRODUCTIVE_REQUIRED_GET_ITEM_MAX_AVAILABLE",
            account_scope="INSTRUMENT_AND_TD_MODE_SCOPED",
            reservation_margin_semantics="POSITION_CAPACITY_NOT_USDC_EQUITY",
            deterministic_transformation=(
                "WOULD_REQUIRE_NON_AUTHORITY_PRICE_TO_INVENT_USDC_EQUITY"
            ),
            restart_behavior="NOT_29P_EQUITY_RESTART",
            reconciliation="NOT_EQ_AND_NOT_USDC_EQUITY",
            fail_closed_behavior="REJECT_UNIT_MISMATCH",
            disposition=STATUS_REJECTED,
            rejection_reason="CONTRACT_QUANTITY_NOT_USDC_RUNNING_ACCOUNT_EQUITY",
        ),
        _candidate(
            candidate_id="CP_S05_U04_RESERVATION_REDUCTION",
            surface="U04_PENDING_ORDER_RESERVATION",
            semantic_fit="RATIFIED_REDUCTION_ROLE_NOT_SOURCE",
            unit_currency="PARENT_DIMENSION_REDUCTION_IF_APPLIED",
            freshness="NOT_A_SOURCE_FRESHNESS_OBJECT",
            availability="ROLE_RATIFIED_VALUE_UNBOUND",
            account_scope="INHERITS_IF_BASE_SOURCE_BOUND",
            reservation_margin_semantics="AVAILABLE_FOR_SIZING_OR_RISK_SIZING_REDUCTION",
            deterministic_transformation="SUBTRACT_ONLY_AFTER_SOURCE_BOUND",
            restart_behavior="MUST_NOT_RECONSTRUCT_BASE_FROM_U04",
            reconciliation="NOT_EQ_SOURCE",
            fail_closed_behavior="REJECT_AS_SOURCE_KEEP_REDUCTION_ROLE",
            disposition=STATUS_REJECTED,
            rejection_reason="U04_REDUCTION_NOT_SOURCE",
        ),
        _candidate(
            candidate_id="CP_S06_EMPTY_GOVERNED_PRODUCER_SLOT",
            surface="GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER",
            semantic_fit="EMPTY_OWNER_SLOT_NOT_SOURCE",
            unit_currency="UNBOUND",
            freshness="NONE",
            availability="SLOT_IS_EMPTY",
            account_scope="UNBOUND",
            reservation_margin_semantics="NONE",
            deterministic_transformation="MINT_FORBIDDEN_UNTIL_SOURCE_BOUND",
            restart_behavior="FAIL_CLOSED_UNTIL_SOURCE_BOUND",
            reconciliation="NONE",
            fail_closed_behavior="REJECT_EMPTY_SLOT_AS_SOURCE",
            disposition=STATUS_REJECTED,
            rejection_reason="GOVERNED_PRODUCER_CREATED=false",
        ),
        _candidate(
            candidate_id="CP_S07_SAMPLE_SCHEMA_NOT_SOURCE",
            surface="GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_V1",
            semantic_fit="TYPED_SCHEMA_NOT_RUNTIME_SOURCE",
            unit_currency="USDC_REQUIRED_BY_SCHEMA",
            freshness="SCHEMA_FIELDS_ONLY",
            availability="SCHEMA_PRESENT_INSTANCE_ABSENT",
            account_scope="SCHEMA_REQUIRES_BOUND_ACCOUNT",
            reservation_margin_semantics="NONE_AS_SCHEMA",
            deterministic_transformation="NOT_A_TRANSFORMATION",
            restart_behavior="UNPROVEN",
            reconciliation="SCHEMA_ONLY",
            fail_closed_behavior="REJECT_SCHEMA_AS_SOURCE",
            disposition=STATUS_REJECTED,
            rejection_reason="SOURCE_OBJECT_PRESENT=false",
        ),
        _candidate(
            candidate_id="CP_S08_ACCOUNT_EQUITY_STOCK",
            surface="ACCOUNT_EQUITY_STOCK",
            semantic_fit="STOCK_IS_NOT_29P_SIZING_INPUT",
            unit_currency="UNBOUND_STOCK",
            freshness="IRRELEVANT_AS_NON_29P_INPUT",
            availability="UNBOUND",
            account_scope="UNBOUND",
            reservation_margin_semantics="MUST_REMAIN_DISTINCT_FROM_SIZING",
            deterministic_transformation="LAYER_MIX_FORBIDDEN",
            restart_behavior="MISSING_STOCK_DOES_NOT_ADMIT_29P",
            reconciliation="COMPARE_TO_EQ_WHEN_BOTH_PRESENT",
            fail_closed_behavior="REJECT_STOCK_AS_SIZING_SOURCE",
            disposition=STATUS_REJECTED,
            rejection_reason="ACCOUNT_EQUITY_STOCK_NOT_29P_SIZING_INPUT",
        ),
        _candidate(
            candidate_id="CP_S09_LEGACY_KIND_SET",
            surface="KIND_SET=EMPTY_FAIL_CLOSED",
            semantic_fit="SEALED_UNKNOWN_NOT_LIVE_CRITICAL_SOURCE",
            unit_currency="NONE",
            freshness="HISTORICAL_NOT_CURRENT_PRODUCTIVE",
            availability="SEALED",
            account_scope="LEGACY",
            reservation_margin_semantics="NONE",
            deterministic_transformation="FORBIDDEN",
            restart_behavior="MUST_NOT_RECONSTRUCT_FROM_KIND_SET",
            reconciliation="NOT_SOURCE",
            fail_closed_behavior="REJECT_LEGACY_KIND_SET_AS_SOURCE",
            disposition=STATUS_REJECTED,
            rejection_reason="LEGACY_KIND_SET_FORBIDDEN_AS_SOURCE",
        ),
        _candidate(
            candidate_id="CP_S10_OTHER_REQUIRED_GET_ITEMS",
            surface=other_gets,
            semantic_fit="PRETRADE_GATES_NOT_AVAILABLE_FOR_SIZING_EQUITY",
            unit_currency="NOT_USDC_ACCOUNT_EQUITY",
            freshness="FRESH_GET_PER_PRETRADE_WHEN_PERFORMED",
            availability="CURRENT_PRODUCTIVE_REQUIRED_GET_SET",
            account_scope="INSTRUMENT_OR_ACCOUNT_CONFIG",
            reservation_margin_semantics="NOT_SIZING_EQUITY",
            deterministic_transformation="NONE_CANONICAL",
            restart_behavior="NOT_29P_EQUITY_RESTART",
            reconciliation="NOT_SOURCE",
            fail_closed_behavior="REJECT_WRONG_DIMENSION",
            disposition=STATUS_REJECTED,
            rejection_reason="NOT_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING",
        ),
        _candidate(
            candidate_id="CP_S11_UNCLASSIFIED_VENUE_FIELDS",
            surface="ANY_OTHER_VENUE_FIELD",
            semantic_fit="UNCLASSIFIED_NON_AUTHORITY",
            unit_currency="UNCLASSIFIED",
            freshness="GET_WOULD_REMAIN_EVIDENCE_NOT_AUTHORITY",
            availability="UNKNOWN_NOT_NEEDED",
            account_scope="UNCLASSIFIED",
            reservation_margin_semantics="UNCLASSIFIED",
            deterministic_transformation="PLAUSIBILITY_FORBIDDEN",
            restart_behavior="MUST_NOT_INVENT",
            reconciliation="NON_AUTHORITY",
            fail_closed_behavior="LEAVE_UNCLASSIFIED_DO_NOT_BIND",
            disposition=STATUS_NON_AUTHORITY,
            rejection_reason="UNCLASSIFIED_FIELD_NOT_BOUND_BY_PLAUSIBILITY",
        ),
    )


def classify_source_selection_verdict_v1() -> dict[str, str]:
    candidates = classify_current_productive_source_candidates_v1()
    selected = [item for item in candidates if item["selected"] == TRUE_TOKEN]
    acceptable = [
        item
        for item in candidates
        if item["disposition"] not in {STATUS_REJECTED, STATUS_NON_AUTHORITY}
    ]
    if selected or acceptable:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "ADMISSIBLE_OR_SELECTED_CANDIDATE_DRIFT"
        )
    return {
        "candidate_count": str(len(candidates)),
        "acceptable_candidate_count": "0",
        "selected_source": SELECTED_SOURCE,
        "selection_status": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_STATUS,
        "source_selected": FALSE_TOKEN,
        "fresh_get_executed": FALSE_TOKEN,
        "fresh_get_not_required_for_binding_decision": TRUE_TOKEN,
        "fresh_get_not_required_justified": FRESH_GET_NOT_REQUIRED_JUSTIFIED,
        "no_hope_get": TRUE_TOKEN,
        "transformation": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_TRANSFORMATION,
        "u04_application": CURRENT_PRODUCTIVE_U04_APPLICATION_STATUS,
        "eq_role": CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
        "freshness_policy": PRETRADE_FRESHNESS_POLICY,
        "restart_reconstruction_status": CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS,
    }


def _assert_standing_pins() -> None:
    if CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED is not True:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "CURRENT_PRODUCTIVE_ARCHITECTURE_NOT_RATIFIED"
        )
    if CURRENT_PRODUCTIVE_ARCHITECTURE_IS_NOT_HISTORICAL_RECONSTRUCTION is not True:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "ARCHITECTURE_MUST_NOT_BE_HISTORICAL_RECONSTRUCTION"
        )
    if LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "LEGACY_RECONSTRUCTION_MUST_NOT_BE_REQUIRED_FOR_LIVE"
        )
    if SEALED_LEGACY_CENSUS_REOPENED is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "SEALED_LEGACY_CENSUS_MUST_REMAIN_CLOSED"
        )
    if CURRENT_PRODUCTIVE_SOURCE_SELECTED is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "CURRENT_PRODUCTIVE_SOURCE_MUST_REMAIN_UNSELECTED"
        )
    if CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "PRODUCER_MINT_MUST_REMAIN_UNAUTHORIZED"
        )
    if GOVERNED_PRODUCER_CREATED is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "GOVERNED_PRODUCER_MUST_REMAIN_ABSENT"
        )
    if SLOT_IS_EMPTY is not True:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("PRODUCER_SLOT_MUST_BE_EMPTY")
    if SOURCE_SELECTED is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "SOURCE_SELECTED_MUST_BE_FALSE"
        )
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "RAW_EQ_SOURCE_AUTHORITY_TRUE"
        )
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "EQ_MUST_REMAIN_RECONCILIATION_TARGET_ONLY"
        )
    if EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("EQ_TREATED_AS_SOURCE")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("MAPPING_MUST_REMAIN_INVALID")
    if MAPPING_PROVEN is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("MAPPING_PROVEN_TRUE")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "ALGEBRA_MUST_REMAIN_INCOMPLETE"
        )
    if KIND_SET_RESOLVED is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("KIND_SET_RESOLVED_TRUE")
    if KIND_SET_UPLIFT_THIS_WORKPACKAGE is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("KIND_SET_UPLIFT_FORBIDDEN")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_RATIFIED is not True:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "SELECTION_MUST_BE_RATIFIED_FAIL_CLOSED"
        )
    if CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE != NONE_TOKEN:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "SELECTED_SOURCE_MUST_BE_NONE"
        )
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_STATUS != (
        "NO_SEMANTICALLY_ADMISSIBLE_CANDIDATE"
    ):
        raise CurrentProductiveAvailableForSizingSourceSelectionError("SELECTION_STATUS_DRIFT")
    if CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED is not False:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("FRESH_GET_MUST_REMAIN_FALSE")
    if CURRENT_PRODUCTIVE_FRESH_GET_NOT_REQUIRED_FOR_BINDING_DECISION is not True:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "FRESH_GET_NOT_REQUIRED_JUSTIFICATION_DRIFT"
        )
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_TRANSFORMATION != "NONE_NO_SOURCE":
        raise CurrentProductiveAvailableForSizingSourceSelectionError("TRANSFORMATION_DRIFT")
    if CURRENT_PRODUCTIVE_U04_APPLICATION_STATUS != "REDUCTION_ONLY_NOT_SOURCE_NOT_APPLIED":
        raise CurrentProductiveAvailableForSizingSourceSelectionError("U04_APPLICATION_DRIFT")
    if U04_LEGACY_STATUS != STATE_UNRESOLVED:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "LEGACY_U04_UNRESOLVED_PRESERVED"
        )
    if U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE != STATE_UNRESOLVED:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "U04_INCLUSION_MUST_REMAIN_UNRESOLVED"
        )
    if PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP != "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET":
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "PRODUCTIVE_U04_MEMBERSHIP_DRIFT"
        )
    if PRODUCTIVE_U04_EQUITY_STOCK_ROLE != DISPOSITION_NOT_EQUITY_STOCK:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("U04_STOCK_ROLE_DRIFT")
    if PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise CurrentProductiveAvailableForSizingSourceSelectionError("U04_SIZING_ROLE_DRIFT")
    if U04_PLACEMENT != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise CurrentProductiveAvailableForSizingSourceSelectionError("U04_PLACEMENT_DRIFT")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("U05_UNKNOWN_PRESERVED")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("U06_UNKNOWN_PRESERVED")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("RESIDUAL_UNKNOWN_PRESERVED")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION != RISK_EQUITY_DIMENSION:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("SIZING_DIMENSION_DRIFT")
    if CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS != "UNBOUND":
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "SIZING_SOURCE_MUST_REMAIN_UNBOUND"
        )
    if CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS != "UNBOUND":
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "STOCK_SOURCE_MUST_REMAIN_UNBOUND"
        )
    if CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY != (
        "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND"
    ):
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "STANDING_UNBOUND_DEPENDENCY_DRIFT"
        )
    if STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER is not True:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "STEP_29P_MUST_REMAIN_CONSUMER"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise CurrentProductiveAvailableForSizingSourceSelectionError("LEGACY_DAG_PIN_DRIFT")
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


def _assert_parent_cr_pack_sealed(*, repo_root: Path) -> None:
    pack = repo_root / CANONICAL_CR_PACK_RELPATH
    claims_path = pack / CLAIMS_FILE
    if not claims_path.is_file():
        raise CurrentProductiveAvailableForSizingSourceSelectionError("PARENT_CR_PACK_MISSING")
    claims = _load_json_object(path=claims_path)
    if claims.get("AVAILABLE_FOR_SIZING_SOURCE_STATUS") != "UNBOUND":
        raise CurrentProductiveAvailableForSizingSourceSelectionError("PARENT_CR_SOURCE_DRIFT")
    if claims.get("SOURCE_SELECTED") != FALSE_TOKEN:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("PARENT_CR_SELECTED_DRIFT")
    if claims.get("SEALED_LEGACY_CENSUS_REOPENED") != FALSE_TOKEN:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("PARENT_CR_CENSUS_REOPENED")
    if claims.get("NEXT_OWNER_GO_REQUIRED") != PIN_OWNER_GO:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("PARENT_CR_NEXT_GO_DRIFT")
    if verify_manifest_sha256_v1(store_root=pack) != 0:
        raise CurrentProductiveAvailableForSizingSourceSelectionError(
            "PARENT_CR_MANIFEST_VERIFY_NOT_ZERO"
        )


def execute_current_productive_available_for_sizing_source_selection_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    persist_as_of: str = CANONICAL_PERSIST_AS_OF,
    repo_root: Path | str | None = None,
) -> CurrentProductiveAvailableForSizingSourceSelectionResultV1:
    from src.ops.governed_productive_account_equity_authority_producer_v1.source_to_semantic_mapping_and_sizing_producer_bind_under_parallel_decoupled_tracks_v1 import (
        reject_consume_execute_after_mapping_ratification_v1,
    )

    if owner_go != OWNER_GO:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("ORIGIN_MAIN_SHA_MISMATCH")
    reject_consume_execute_after_mapping_ratification_v1(
        wp_label="CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_V1"
    )
    _assert_standing_pins()
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    _assert_parent_cr_pack_sealed(repo_root=root)
    as_of = str(persist_as_of or "").strip()
    if as_of == "":
        raise CurrentProductiveAvailableForSizingSourceSelectionError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    semantics = classify_step_29p_required_semantics_v1()
    candidates = classify_current_productive_source_candidates_v1()
    verdict = classify_source_selection_verdict_v1()
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
        "PARENT_CR_PACK": CANONICAL_CR_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "EPISTEMIC_CLASS": "CURRENT_PRODUCTIVE_DESIGN",
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CS",
        "LEGACY_SEALED_UNKNOWN": "CQ_KIND_SET_EMPTY_AND_CR_FOUR_LAYER_MODEL",
        "FORENSIC_EVIDENCE": "CURRENT_29P_CONSUMER_AND_CURRENT_PRODUCTIVE_GET_SURFACES",
        "ADJUDICATED": "NO_SEMANTICALLY_ADMISSIBLE_AVAILABLE_FOR_SIZING_SOURCE",
        "INTERPRETATION": "SOURCE_NOT_BOUND",
        "HYPOTHESIS": "FORBIDDEN_OR_WRONG_UNIT_OR_NON_AUTHORITY",
        "UNRESOLVED": BLOCKER_ID,
        "START_BLOCK": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "LEGACY_SEALED_FULL_CORE_DAG_PIN": DAG_PIN,
        "LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE": FALSE_TOKEN,
        "SEALED_LEGACY_CENSUS_REOPENED": FALSE_TOKEN,
        "CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL": CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
        "CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED": TRUE_TOKEN,
        "CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE": CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE,
        "CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE": CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS,
        "CURRENT_PRODUCTIVE_EQUITY_SOURCE": "UNBOUND_AVAILABLE_FOR_SIZING_SOURCE",
        "RECONCILIATION_TARGET": "eq",
        "RECONCILIATION_TARGET_STATUS": CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
        "AVAILABLE_FOR_SIZING_MODEL": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
        "AVAILABLE_FOR_SIZING_SOURCE_STATUS": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
        "AVAILABLE_FOR_SIZING_TRANSFORMATION": (
            CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_TRANSFORMATION
        ),
        "SELECTED_SOURCE": SELECTED_SOURCE,
        "SELECTION_STATUS": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_STATUS,
        "SELECTION_RATIFIED": TRUE_TOKEN,
        "ACCEPTABLE_CANDIDATE_COUNT": "0",
        "U04_ROLE": PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
        "U04_EQUITY_STOCK_ROLE": DISPOSITION_NOT_EQUITY_STOCK,
        "U04_APPLICATION": CURRENT_PRODUCTIVE_U04_APPLICATION_STATUS,
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
        "STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER": TRUE_TOKEN,
        "STEP_29P_RISK_ADMISSIBLE": FALSE_TOKEN,
        "RESTART_RECONSTRUCTION_STATUS": CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS,
        "STEP_29P_BINDING_STATUS": "CONSUMER_BOUND_SOURCE_UNBOUND",
        "CURRENT_LIVE_CRITICAL_BLOCKER": BLOCKER_ID,
        "CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "LIVE_CRITICAL_PATH_FOLLOWS": "CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY",
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "FIRST_DEFINITIVE_BLOCK": BLOCKER_ID,
        "EXACT_MISSING_PREDICATE": EXACT_MISSING_PREDICATE,
        "FRESH_GET_EXECUTED": FALSE_TOKEN,
        "FRESH_GET_NOT_REQUIRED_FOR_BINDING_DECISION": TRUE_TOKEN,
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
        "parent_cr_pack": CANONICAL_CR_PACK_RELPATH,
        "sealed_legacy_census_reopened": FALSE_TOKEN,
        "historical_artifacts_rewritten": FALSE_TOKEN,
        "legacy_reconstruction_required_for_live": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "source_selected": FALSE_TOKEN,
        "fresh_get_executed": FALSE_TOKEN,
        "producer_minted": FALSE_TOKEN,
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
        "legacy_dag_pin": DAG_PIN,
    }
    architecture = {
        "layer": "CURRENT_CANONICAL_AUTHORITY",
        "model_version": CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
        "selection_ratified": TRUE_TOKEN,
        "selected_source": SELECTED_SOURCE,
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "current_live_critical_blocker": BLOCKER_ID,
        "standing_unbound_dependency": CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
        "legacy_sealed_dag_pin": DAG_PIN,
        "source_selected": FALSE_TOKEN,
        "fresh_get_executed": FALSE_TOKEN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
        "atlas_authority": NONE_TOKEN,
    }
    epistemic = {
        "CURRENT_CANONICAL_AUTHORITY": "MASTER_RUNBOOK_11_2_1_CS",
        "CURRENT_PRODUCTIVE_DESIGN": SCHEMA_CLASS,
        "LEGACY_SEALED_UNKNOWN": "CQ_KIND_SET_EMPTY_AND_CR_FOUR_LAYER_MODEL",
        "FORENSIC_EVIDENCE": "CURRENT_29P_CONSUMER_AND_CURRENT_PRODUCTIVE_GET_SURFACES",
        "ADJUDICATED": "NO_SEMANTICALLY_ADMISSIBLE_AVAILABLE_FOR_SIZING_SOURCE",
        "INTERPRETATION": "SOURCE_NOT_BOUND",
        "HYPOTHESIS": "FORBIDDEN_OR_WRONG_UNIT_OR_NON_AUTHORITY",
        "UNRESOLVED": BLOCKER_ID,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "required_semantics_v1.json", payload=semantics)
    _persist_json(
        path=store / "source_candidates_v1.json",
        payload={"candidates": list(candidates), "acceptable_count": "0"},
    )
    _persist_json(path=store / "selection_verdict_v1.json", payload=verdict)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "epistemic_separation_v1.json", payload=epistemic)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise CurrentProductiveAvailableForSizingSourceSelectionError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise CurrentProductiveAvailableForSizingSourceSelectionError("MANIFEST_VERIFY_NOT_ZERO")
    return CurrentProductiveAvailableForSizingSourceSelectionResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        selection_ratified=TRUE_TOKEN,
        selected_source=SELECTED_SOURCE,
        selection_status=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_STATUS,
        available_for_sizing_source_status=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
        acceptable_candidate_count="0",
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
    "ARCHITECTURE_BLOCKER",
    "BLOCKER_ID",
    "CANONICAL_PACK_RELPATH",
    "CANONICAL_PERSIST_AS_OF",
    "CurrentProductiveAvailableForSizingSourceSelectionError",
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "FRESH_GET_NOT_REQUIRED_JUSTIFIED",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "PIN_OWNER_GO_STATUS",
    "SELECTED_SOURCE",
    "classify_current_productive_source_candidates_v1",
    "classify_source_selection_verdict_v1",
    "classify_step_29p_required_semantics_v1",
    "execute_current_productive_available_for_sizing_source_selection_v1",
    "reject_empty_producer_slot_as_source_v1",
    "reject_forbidden_venue_field_as_source_v1",
    "reject_max_size_contracts_as_usdc_equity_source_v1",
    "reject_u04_as_sizing_source_v1",
    "reject_unclassified_field_plausibility_bind_v1",
)
