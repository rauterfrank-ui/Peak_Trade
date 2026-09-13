"""D6 PATH_B CLASS_C PACKAGE_1 trading-account observation rules.

Persists selected observation surfaces and fail-closed semantic laws.
Does not execute observation. Does not authorize GET. Does not mint D4
identity. Does not rehabilitate C01. Does not ratify kinds. Does not
release Mini-Slice 2 or D7. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    FORBIDDEN_PROVENANCE_CLASSES,
    PROVENANCE_EXPLICIT_TYPED_BINDING,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_ATLAS_AUTHORITY,
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    BALANCE_OBSERVATION_ALLOWED_FIELDS,
    BALANCE_OBSERVATION_DOES_NOT_REHABILITATE_C01,
    BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN,
    C01_REHABILITATION_FORBIDDEN,
    C17_CREATED,
    CANDIDATE_SURFACE_SELECTION,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_COMPLETENESS_PRECONDITIONS_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EMPTY_ROWS_MEAN_ONLY_NO_ROWS_OBSERVED_WITHIN_EXECUTED_QUERY,
    EMPTY_ROWS_PROVE_KIND_ABSENCE,
    EMPTY_ROWS_PROVE_ZERO_EVENTS,
    EMBEDDING_OPTION,
    EQ_ROLE,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    EXECUTION_READY,
    KIND_SET_RESOLVED,
    MS1_KIND_SET_FULLY_CLOSED,
    MS2_AUTHORIZED,
    OBSERVATION_EXECUTED,
    OBSERVATION_EXECUTION_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    OBSERVED_COMPONENT_FIELDS_HAVE_AUTHORITY_EFFECT,
    ORDERING_OR_TIE_AMBIGUITY_FAIL_CLOSED,
    PACKAGE_1_AUTHORITY_EFFECT,
    PACKAGE_1_PERSISTED,
    PAGINATION_EXHAUSTION_PROVES_COMPLETENESS,
    PAGINATION_EXHAUSTION_PROVES_QUERY_TRAVERSAL_COMPLETED,
    PATH_A_ARCHIVE_OR_REPO_SEARCH,
    PATH_B_CLASS_C_PACKAGE_1_SELECTED,
    PATH_B_PREAUTHORIZATION_READY,
    PATH_B_SCOPED_READ_ONLY_OBSERVATION,
    PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RETENTION_GAP_FAIL_CLOSED,
    SELECTED_OBSERVATION_SURFACES,
    SOURCE_SELECTED,
    UNKNOWN_EMBEDDING_FACTS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)

SCHEMA_CLASS = "PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
SELECTION_NONE = "NONE_SELECTED"
ATLAS_AUTHORITY_NONE = "NONE"
PATH_A_REJECT = "REJECT"
PATH_B_SELECTED_BUT_BLOCKED = "SELECTED_BUT_BLOCKED_ON_NEW_AUTHORIZATION"
PATH_C_REJECT = "REJECT"
EQ_ROLE_RECONCILIATION_OR_EMBEDDING_TARGET_ONLY = "RECONCILIATION_OR_EMBEDDING_TARGET_ONLY"
EMBEDDING_OPTION_A = "E_OPTION_A_FAIL_CLOSED_UNKNOWN_ALLOWED"
EMBEDDING_STATUS_UNKNOWN = "UNKNOWN"
SURFACE_CLASS_SELECTED_OBSERVATION = "SELECTED_OBSERVATION_SURFACE_AUTHORITY_NONE"

SURFACE_ACCOUNT_CONFIG = "GET_/api/v5/account/config"
SURFACE_ACCOUNT_BALANCE = "GET_/api/v5/account/balance"
SURFACE_ACCOUNT_BILLS = "GET_/api/v5/account/bills"
SURFACE_ACCOUNT_BILLS_ARCHIVE = "GET_/api/v5/account/bills-archive"
SURFACE_ACCOUNT_SUBTYPES = "GET_/api/v5/account/subtypes"

BALANCE_ALLOWED_OBSERVATION_FIELDS: Tuple[str, ...] = (
    "eq",
    "cashBal",
    "liab",
    "crossLiab",
    "isoLiab",
    "interest",
    "upl",
    "uplLiab",
    "uTime",
)
FORBIDDEN_BALANCE_AUTHORITY_USES: Tuple[str, ...] = (
    "EQUITY_STOCK_SOURCE_AUTHORITY",
    "P01_AUTHORITY_OR_INPUT",
    "SIZING_AUTHORITY",
    "D5_CLAIMED_EQUITY_AUTHORITY",
    "KIND_RATIFICATION_EVIDENCE_BY_ITSELF",
)
EMBEDDING_FACTS_REMAIN_UNKNOWN: Tuple[str, ...] = (
    "F12_LIABILITY_AFFECTS_EQUITY_STOCK",
    "F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
    "F16_FEE_ALREADY_EMBEDDED_IN_EQ",
    "F17_FEE_SEPARATE_ACCOUNT_DELTA",
    "F18_FEE_RECONCILIATION_ONLY",
)


class PathBClassCPackage1TradingAccountObservationRulesContractError(ValueError):
    """Fail-closed PATH_B CLASS_C PACKAGE_1 observation-rule violation."""


@dataclass(frozen=True)
class SelectedObservationSurfaceRecordV1:
    surface_id: str
    classification: str
    atlas_authority: str
    authority_effect: str
    selected: str
    observation_executed: str
    forbidden_use: str


@dataclass(frozen=True)
class UnknownEmbeddingFactRecordV1:
    fact_id: str
    status: str
    include_from_unknown: str
    exclude_from_unknown: str
    algebraic_inference_allowed: str


@dataclass(frozen=True)
class PathBClassCPackage1TradingAccountObservationRulesContractV1:
    persist_id: str
    package_1_persisted: str
    selected_observation_surfaces: str
    d4_rule_persisted: str
    balance_rule_persisted: str
    empty_coverage_rule_persisted: str
    embedding_rule_persisted: str
    path_b_preauthorization_ready: str
    execution_ready: str
    observation_executed: str
    observation_execution_authorized: str
    observation_network_get_authorized: str
    candidate_surface_selection: str
    account_bills_atlas_authority: str
    c01_rehabilitation_forbidden: str
    raw_eq_source_authority: str
    eq_role: str
    observed_component_fields_have_authority_effect: str
    empty_rows_prove_zero_events: str
    empty_rows_prove_kind_absence: str
    pagination_exhaustion_proves_completeness: str
    embedding_option: str
    kind_set_resolved: str
    ms2_authorized: str
    d6_fully_closed: str
    d7_authorized: str
    authority_effect: str
    provenance_digest: str


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_package_1_observation_rules_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"PACKAGE_1_FIELD_MISSING:{field}"
        )
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"PACKAGE_1_FIELD_NOT_STRING:{field}"
        )
    text = raw.strip()
    if text == "" or text != raw:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"PACKAGE_1_FIELD_MISSING:{field}"
        )
    return text


def _assert_shared_pins() -> None:
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PACKAGE_1_AUTHORITY_OWNER_MUTATED"
        )
    if PACKAGE_1_PERSISTED is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PACKAGE_1_PERSISTED_NOT_TRUE"
        )
    if PATH_B_CLASS_C_PACKAGE_1_SELECTED is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PACKAGE_1_NOT_SELECTED"
        )
    if PATH_B_PREAUTHORIZATION_READY is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PATH_B_PREAUTHORIZATION_READY_NOT_TRUE"
        )
    if EXECUTION_READY is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "EXECUTION_READY_MUST_REMAIN_FALSE"
        )
    if OBSERVATION_EXECUTED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "OBSERVATION_EXECUTED_MUST_REMAIN_FALSE"
        )
    if OBSERVATION_EXECUTION_AUTHORIZED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "OBSERVATION_EXECUTION_AUTHORIZED_MUST_REMAIN_FALSE"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "OBSERVATION_NETWORK_GET_AUTHORIZED_MUST_REMAIN_FALSE"
        )
    if CANDIDATE_SURFACE_SELECTION != SELECTION_NONE:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "CANDIDATE_SURFACE_MUST_REMAIN_UNSELECTED"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "ACCOUNT_BILLS_MUST_REMAIN_CURRENT_NONCANONICAL"
        )
    if ACCOUNT_BILLS_ATLAS_AUTHORITY != ATLAS_AUTHORITY_NONE:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "ACCOUNT_BILLS_ATLAS_AUTHORITY_MUST_REMAIN_NONE"
        )
    if PACKAGE_1_AUTHORITY_EFFECT != AUTHORITY_EFFECT:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PACKAGE_1_AUTHORITY_EFFECT_MUST_REMAIN_NONE"
        )
    if PATH_A_ARCHIVE_OR_REPO_SEARCH != PATH_A_REJECT:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PATH_A_MUST_REMAIN_REJECT"
        )
    if PATH_B_SCOPED_READ_ONLY_OBSERVATION != PATH_B_SELECTED_BUT_BLOCKED:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PATH_B_EXECUTION_MUST_REMAIN_BLOCKED"
        )
    if PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT != PATH_C_REJECT:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PATH_C_MUST_REMAIN_REJECT"
        )
    if C01_REHABILITATION_FORBIDDEN is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "C01_REHABILITATION_MUST_REMAIN_FORBIDDEN"
        )
    if BALANCE_OBSERVATION_DOES_NOT_REHABILITATE_C01 is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "BALANCE_MUST_NOT_REHABILITATE_C01"
        )
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if EQ_ROLE != EQ_ROLE_RECONCILIATION_OR_EMBEDDING_TARGET_ONLY:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "EQ_ROLE_MUST_REMAIN_RECONCILIATION_OR_EMBEDDING_TARGET_ONLY"
        )
    if OBSERVED_COMPONENT_FIELDS_HAVE_AUTHORITY_EFFECT != AUTHORITY_EFFECT:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "OBSERVED_COMPONENT_FIELDS_MUST_HAVE_AUTHORITY_NONE"
        )
    if EMPTY_ROWS_MEAN_ONLY_NO_ROWS_OBSERVED_WITHIN_EXECUTED_QUERY is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "EMPTY_ROWS_MEANING_DRIFT"
        )
    if EMPTY_ROWS_PROVE_ZERO_EVENTS is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "EMPTY_ROWS_MUST_NOT_PROVE_ZERO_EVENTS"
        )
    if EMPTY_ROWS_PROVE_KIND_ABSENCE is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "EMPTY_ROWS_MUST_NOT_PROVE_KIND_ABSENCE"
        )
    if PAGINATION_EXHAUSTION_PROVES_QUERY_TRAVERSAL_COMPLETED is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PAGINATION_EXHAUSTION_TRAVERSAL_PIN_DRIFT"
        )
    if PAGINATION_EXHAUSTION_PROVES_COMPLETENESS is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "PAGINATION_EXHAUSTION_MUST_NOT_PROVE_COMPLETENESS"
        )
    if RETENTION_GAP_FAIL_CLOSED is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "RETENTION_GAP_MUST_FAIL_CLOSED"
        )
    if ORDERING_OR_TIE_AMBIGUITY_FAIL_CLOSED is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "ORDERING_OR_TIE_AMBIGUITY_MUST_FAIL_CLOSED"
        )
    if EMBEDDING_OPTION != EMBEDDING_OPTION_A:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "EMBEDDING_OPTION_MUST_REMAIN_E_OPTION_A"
        )
    if UNKNOWN_EMBEDDING_FACTS != EMBEDDING_FACTS_REMAIN_UNKNOWN:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "UNKNOWN_EMBEDDING_FACTS_DRIFT"
        )
    if SELECTED_OBSERVATION_SURFACES != (
        SURFACE_ACCOUNT_CONFIG,
        SURFACE_ACCOUNT_BALANCE,
        SURFACE_ACCOUNT_BILLS,
        SURFACE_ACCOUNT_BILLS_ARCHIVE,
        SURFACE_ACCOUNT_SUBTYPES,
    ):
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "SELECTED_OBSERVATION_SURFACES_DRIFT"
        )
    if BALANCE_OBSERVATION_ALLOWED_FIELDS != BALANCE_ALLOWED_OBSERVATION_FIELDS:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "BALANCE_ALLOWED_FIELDS_DRIFT"
        )
    if BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "D4_FROM_ENV_MUST_REMAIN_FORBIDDEN"
        )
    if BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "D4_FROM_CREDENTIAL_MUST_REMAIN_FORBIDDEN"
        )
    if BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN is not True:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "D4_IMPLICIT_DEFAULT_MUST_REMAIN_FORBIDDEN"
        )
    if KIND_SET_RESOLVED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "TAXONOMY_KIND_SET_RESOLVED_NOT_FALSE"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "CLASSIFIED_KIND_SET_MUST_REMAIN_EMPTY_FAIL_CLOSED"
        )
    if MS1_KIND_SET_FULLY_CLOSED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "MS1_KIND_SET_FULLY_CLOSED_NOT_FALSE"
        )
    if MS2_AUTHORIZED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "MS2_AUTHORIZED_NOT_FALSE"
        )
    if D6_FULLY_CLOSED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "D6_FULLY_CLOSED_NOT_FALSE"
        )
    if D7_AUTHORIZED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "D7_AUTHORIZED_NOT_FALSE"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_NOT_ABSENT"
        )
    if EVENT_KIND_SOURCE_SEAM_SELECTED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "EVENT_KIND_SOURCE_SEAM_SELECTED_NOT_FALSE"
        )
    if SOURCE_SELECTED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "SOURCE_SELECTED_NOT_FALSE"
        )
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "COMPLETE_EVENT_STREAM_PROVEN_NOT_FALSE"
        )
    if D6_COMPLETENESS_PRECONDITIONS_PROVEN is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "D6_COMPLETENESS_PRECONDITIONS_PROVEN_NOT_FALSE"
        )
    if C17_CREATED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "C17_CREATED_NOT_FALSE"
        )
    if RECONSTRUCTION_ENGINE_CREATED is not False:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "RECONSTRUCTION_ENGINE_CREATED_NOT_FALSE"
        )


def build_selected_observation_surface_records_v1() -> Tuple[
    SelectedObservationSurfaceRecordV1, ...
]:
    _assert_shared_pins()
    forbidden = (
        "ATLAS_UPLIFT_OR_MS2_SOURCE_SEAM_OR_KIND_RATIFICATION_OR_C01_REHABILITATION_"
        "OR_D7_OR_LIVE_CANARY_OR_D4_IDENTITY_MINT"
    )
    return tuple(
        SelectedObservationSurfaceRecordV1(
            surface_id=surface_id,
            classification=SURFACE_CLASS_SELECTED_OBSERVATION,
            atlas_authority=ATLAS_AUTHORITY_NONE,
            authority_effect=AUTHORITY_EFFECT,
            selected=TRUE_TOKEN,
            observation_executed=FALSE_TOKEN,
            forbidden_use=forbidden,
        )
        for surface_id in SELECTED_OBSERVATION_SURFACES
    )


def build_unknown_embedding_fact_records_v1() -> Tuple[UnknownEmbeddingFactRecordV1, ...]:
    _assert_shared_pins()
    return tuple(
        UnknownEmbeddingFactRecordV1(
            fact_id=fact_id,
            status=EMBEDDING_STATUS_UNKNOWN,
            include_from_unknown=FALSE_TOKEN,
            exclude_from_unknown=FALSE_TOKEN,
            algebraic_inference_allowed=FALSE_TOKEN,
        )
        for fact_id in EMBEDDING_FACTS_REMAIN_UNKNOWN
    )


def corroborate_d4_identity_from_account_config_observation_v1(
    *,
    bound_account_identity: str,
    bound_settlement_currency: str,
    observed_uid: str,
    observed_main_uid: str,
    observed_settle_ccy: str,
    observed_account_mode: str,
    identity_provenance_class: str,
) -> str:
    _assert_shared_pins()
    bound_account = _require_non_empty_str(
        field="bound_account_identity", raw=bound_account_identity
    )
    bound_settle = _require_non_empty_str(
        field="bound_settlement_currency", raw=bound_settlement_currency
    )
    observed_uid_text = _require_non_empty_str(field="observed_uid", raw=observed_uid)
    _require_non_empty_str(field="observed_main_uid", raw=observed_main_uid)
    observed_settle = _require_non_empty_str(field="observed_settle_ccy", raw=observed_settle_ccy)
    _require_non_empty_str(field="observed_account_mode", raw=observed_account_mode)
    provenance = _require_non_empty_str(
        field="identity_provenance_class", raw=identity_provenance_class
    )
    if provenance in FORBIDDEN_PROVENANCE_CLASSES:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"D4_OBSERVATION_PROVENANCE_FORBIDDEN:{provenance}"
        )
    if provenance != PROVENANCE_EXPLICIT_TYPED_BINDING:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"D4_OBSERVATION_MUST_NOT_MINT_IDENTITY:{provenance}"
        )
    if observed_uid_text != bound_account or observed_settle != bound_settle:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "D4_OBSERVATION_MISMATCH_FAIL_CLOSED"
        )
    return "D4_RUNTIME_EVIDENCE_CORROBORATED_IDENTITY_NOT_MINTED"


def assert_balance_observation_cannot_become_authority_v1(*, claimed_use: str) -> None:
    _assert_shared_pins()
    use = _require_non_empty_str(field="claimed_use", raw=claimed_use)
    if use in FORBIDDEN_BALANCE_AUTHORITY_USES:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"BALANCE_OBSERVATION_FORBIDDEN_AUTHORITY_USE:{use}"
        )
    raise PathBClassCPackage1TradingAccountObservationRulesContractError(
        f"BALANCE_OBSERVATION_UNKNOWN_CLAIMED_USE:{use}"
    )


def assert_empty_rows_are_not_zero_or_kind_absence_v1(*, claimed_proof: str) -> None:
    _assert_shared_pins()
    proof = _require_non_empty_str(field="claimed_proof", raw=claimed_proof)
    if proof in {"ZERO_EVENTS", "KIND_ABSENCE", "COMPLETENESS"}:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"EMPTY_COVERAGE_FORBIDDEN_PROOF:{proof}"
        )
    if proof != "NO_ROWS_OBSERVED_WITHIN_EXECUTED_QUERY":
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"EMPTY_COVERAGE_UNKNOWN_CLAIM:{proof}"
        )


def reject_include_exclude_from_unknown_embedding_v1(*, decision: str, fact_id: str) -> None:
    _assert_shared_pins()
    fact = _require_non_empty_str(field="fact_id", raw=fact_id)
    action = _require_non_empty_str(field="decision", raw=decision)
    if fact not in EMBEDDING_FACTS_REMAIN_UNKNOWN:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"EMBEDDING_FACT_NOT_IN_UNKNOWN_SET:{fact}"
        )
    if action in {"INCLUDE", "EXCLUDE"}:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"EMBEDDING_UNKNOWN_CANNOT_{action}:{fact}"
        )
    if action != DECISION_REMAIN_UNKNOWN:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            f"EMBEDDING_DECISION_NOT_REMAIN_UNKNOWN:{action}"
        )


def build_path_b_class_c_package_1_trading_account_observation_rules_v1(
    *,
    persist_id: str,
) -> PathBClassCPackage1TradingAccountObservationRulesContractV1:
    _assert_shared_pins()
    persist = _require_non_empty_str(field="persist_id", raw=persist_id)
    surfaces = build_selected_observation_surface_records_v1()
    facts = build_unknown_embedding_fact_records_v1()
    if tuple(record.surface_id for record in surfaces) != SELECTED_OBSERVATION_SURFACES:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "SELECTED_OBSERVATION_SURFACE_SET_DRIFT"
        )
    if any(record.atlas_authority != ATLAS_AUTHORITY_NONE for record in surfaces):
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "SELECTED_OBSERVATION_SURFACE_ATLAS_UPLIFT_FORBIDDEN"
        )
    if any(record.authority_effect != AUTHORITY_EFFECT for record in surfaces):
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "SELECTED_OBSERVATION_SURFACE_AUTHORITY_EFFECT_NOT_NONE"
        )
    if any(record.observation_executed != FALSE_TOKEN for record in surfaces):
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "SELECTED_OBSERVATION_SURFACE_EXECUTED_FORBIDDEN"
        )
    if tuple(record.fact_id for record in facts) != EMBEDDING_FACTS_REMAIN_UNKNOWN:
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "UNKNOWN_EMBEDDING_FACT_SET_DRIFT"
        )
    if any(record.status != EMBEDDING_STATUS_UNKNOWN for record in facts):
        raise PathBClassCPackage1TradingAccountObservationRulesContractError(
            "EMBEDDING_FACT_MUST_REMAIN_UNKNOWN"
        )
    payload = {
        "persist_id": persist,
        "package_1_persisted": TRUE_TOKEN,
        "selected_observation_surfaces": ",".join(SELECTED_OBSERVATION_SURFACES),
        "d4_rule_persisted": TRUE_TOKEN,
        "balance_rule_persisted": TRUE_TOKEN,
        "empty_coverage_rule_persisted": TRUE_TOKEN,
        "embedding_rule_persisted": TRUE_TOKEN,
        "path_b_preauthorization_ready": TRUE_TOKEN,
        "execution_ready": FALSE_TOKEN,
        "observation_executed": FALSE_TOKEN,
        "observation_execution_authorized": FALSE_TOKEN,
        "observation_network_get_authorized": FALSE_TOKEN,
        "candidate_surface_selection": SELECTION_NONE,
        "account_bills_atlas_authority": ATLAS_AUTHORITY_NONE,
        "c01_rehabilitation_forbidden": TRUE_TOKEN,
        "raw_eq_source_authority": FALSE_TOKEN,
        "eq_role": EQ_ROLE_RECONCILIATION_OR_EMBEDDING_TARGET_ONLY,
        "observed_component_fields_have_authority_effect": AUTHORITY_EFFECT,
        "empty_rows_prove_zero_events": FALSE_TOKEN,
        "empty_rows_prove_kind_absence": FALSE_TOKEN,
        "pagination_exhaustion_proves_completeness": FALSE_TOKEN,
        "embedding_option": EMBEDDING_OPTION_A,
        "kind_set_resolved": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "d6_fully_closed": FALSE_TOKEN,
        "d7_authorized": FALSE_TOKEN,
        "authority_effect": AUTHORITY_EFFECT,
        "d4_observed_fields_are_runtime_evidence_only": TRUE_TOKEN,
        "d4_observation_must_not_mint_identity": TRUE_TOKEN,
    }
    return PathBClassCPackage1TradingAccountObservationRulesContractV1(
        persist_id=persist,
        package_1_persisted=payload["package_1_persisted"],
        selected_observation_surfaces=payload["selected_observation_surfaces"],
        d4_rule_persisted=payload["d4_rule_persisted"],
        balance_rule_persisted=payload["balance_rule_persisted"],
        empty_coverage_rule_persisted=payload["empty_coverage_rule_persisted"],
        embedding_rule_persisted=payload["embedding_rule_persisted"],
        path_b_preauthorization_ready=payload["path_b_preauthorization_ready"],
        execution_ready=payload["execution_ready"],
        observation_executed=payload["observation_executed"],
        observation_execution_authorized=payload["observation_execution_authorized"],
        observation_network_get_authorized=payload["observation_network_get_authorized"],
        candidate_surface_selection=payload["candidate_surface_selection"],
        account_bills_atlas_authority=payload["account_bills_atlas_authority"],
        c01_rehabilitation_forbidden=payload["c01_rehabilitation_forbidden"],
        raw_eq_source_authority=payload["raw_eq_source_authority"],
        eq_role=payload["eq_role"],
        observed_component_fields_have_authority_effect=payload[
            "observed_component_fields_have_authority_effect"
        ],
        empty_rows_prove_zero_events=payload["empty_rows_prove_zero_events"],
        empty_rows_prove_kind_absence=payload["empty_rows_prove_kind_absence"],
        pagination_exhaustion_proves_completeness=payload[
            "pagination_exhaustion_proves_completeness"
        ],
        embedding_option=payload["embedding_option"],
        kind_set_resolved=payload["kind_set_resolved"],
        ms2_authorized=payload["ms2_authorized"],
        d6_fully_closed=payload["d6_fully_closed"],
        d7_authorized=payload["d7_authorized"],
        authority_effect=payload["authority_effect"],
        provenance_digest=compute_package_1_observation_rules_digest_v1(payload),
    )
