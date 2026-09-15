"""Ratify absence of an in-repo NON_EQ source-kind primary proof surface.

Consumes the workpackage Owner-GO. Satisfies the CP-named GO by an
explicit evidence-gap ratification: no producer, ledger, event,
checkpoint, or accounting-contract instance in existing repo, historical,
or forensic evidence qualifies as a NON_EQ equity-stock-affecting source
kind primary proof surface. Does not mint a source kind. Does not INCLUDE
or EXCLUDE. Does not set KIND_SET_RESOLVED. Does not treat venue eq as
source. Does not reintroduce U04. Does not import live TODAY stock as a
D6 source kind. Does not GET. Does not POST. Does not Hope-GET.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    RATIFIED_SOURCE_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    TARGET_RESIDUAL,
    TARGET_U05,
    TARGET_U06,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_NOT_EQUITY_STOCK,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    ACCOUNT_EQUITY_SOURCE_MAPPING_DENIED_THIS_WORKPACKAGE,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    COMPLETE_EVENT_STREAM_PROVEN,
    CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES,
    D6_ACCOUNT_EQUITY_SOURCE_MAPPING_COVERAGE_STATUS,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EQ_RECONCILIATION_TARGET_ONLY,
    EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES,
    KIND_SET_RESOLVED,
    KIND_SET_UPLIFT_THIS_WORKPACKAGE,
    MS2_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    PRIMARY_PROOF_SURFACE,
    PRIMARY_PROOF_SURFACE_BINDING_STATUS,
    PRIMARY_PROOF_SURFACE_BOUND_THIS_WORKPACKAGE,
    PRIMARY_PROOF_SURFACE_STATUS,
    PRODUCTIVE_RESIDUAL_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
    PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U04_EQUITY_STOCK_ROLE,
    PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U06_EQUITY_STOCK_KIND_MEMBERSHIP,
    RATIFIED_NON_EQ_EQUITY_STOCK_SOURCE_KINDS,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    SEMANTIC_MAPPING_PROVEN,
    SOURCE_KIND_COMPLETENESS_RATIFICATION,
    SOURCE_KIND_COMPLETENESS_STATUS,
    U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE,
    U04_LEGACY_INCLUDE_EXCLUDE_AS_EQUITY_STOCK_KIND_RETIRED_AS_PRODUCTIVE_BLOCKER,
    U04_LEGACY_STATUS,
    U04_PLACEMENT,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    TODAY_SOURCE_KIND,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.non_eq_equity_stock_source_kind_or_completeness_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CP_PACK_RELPATH,
    NEXT_OWNER_GO as PIN_OWNER_GO,
    reject_kind_set_uplift_v1,
    reject_today_as_account_equity_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.remaining_necessary_kind_evidence_classification_v1 import (
    U04_KIND_SET_DISPOSITION,
    reject_kind_set_resolved_while_remaining_unknown_v1,
    reject_u04_reclassify_as_equity_stock_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_candidate_census_v1 import (
    ACCEPTABLE_FOR_OWNER_RATIFICATION_COUNT,
    C17_CREATED as CENSUS_C17_CREATED,
    GENUINELY_NEW_CANDIDATE_COUNT,
    build_source_candidate_census_findings_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u04_pending_order_reservation_or_account_equity_mapping_v1 import (
    reject_eq_as_source_authority_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

OWNER_GO = (
    "OWNER_GO_SUPPLY_OR_AUTHORIZE_A_NEW_NON_EQ_EQUITY_STOCK_SOURCE_KIND_"
    "PRIMARY_PROOF_SURFACE_NOT_EQ_NOT_U04_AND_NOT_LIVE_TODAY_STOCK_UPLIFT_V1"
)
EXPECTED_ORIGIN_MAIN_SHA = "ceb87225da34d70fef2d516f081d931d8000d627"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_non_eq_equity_stock_source_kind_primary_proof_surface_v1/"
    "2026-09-15T100000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T10:00:00Z"
SCHEMA_CLASS = "NON_EQ_EQUITY_STOCK_SOURCE_KIND_PRIMARY_PROOF_SURFACE_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
STATE_UNRESOLVED = "UNRESOLVED"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
PRODUCTIVE_MEMBERSHIP = "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
STATUS_NOT_BINDABLE = "NOT_BINDABLE_EXISTING_EVIDENCE"
STATUS_RATIFIED_PRIMARY_PROOF_SURFACE = "RATIFIED_PRIMARY_PROOF_SURFACE"
SURFACE_PROOF_LAW = (
    "PRIMARY_PROOF_SURFACE_REQUIRES_SEALED_NON_EQ_EQUITY_STOCK_AFFECTING_"
    "PRODUCER_LEDGER_EVENT_CHECKPOINT_OR_ACCOUNTING_CONTRACT_INSTANCE_NOT_EQ_"
    "NOT_U04_NOT_LIVE_TODAY_NOT_SCHEMA_ONLY_NOT_HYPOTHESIS_NOT_ALREADY_"
    "ADJUDICATED_NONE_BINDABLE_WRONG_OBJECT_UNKNOWN_IS_NOT_INCLUDE"
)
SURFACE_EVIDENCE = (
    "SEALED_CP_NO_RATIFIABLE_KIND_PLUS_C01_C16_REJECTION_PLUS_SOURCE_"
    "CANDIDATE_CENSUS_GENUINELY_NEW_ZERO_PLUS_CA_CF_CH_CK_NONE_BINDABLE_OR_"
    "WRONG_PROOF_OBJECT_PLUS_BE_RATIFIED_SOURCE_KINDS_NONE_PLUS_SCHEMA_ONLY_"
    "NOT_RUNTIME_INSTANCE_PLUS_HYPOTHESIS_DEPOSIT_WITHDRAWAL_TRANSFER_FUNDING_"
    "NOT_CLASSIFIED"
)
EXACT_MISSING_PREDICATE = (
    "NO_IN_REPO_NON_EQ_EQUITY_STOCK_SOURCE_KIND_PRIMARY_PROOF_SURFACE_AFTER_"
    "SEALED_EXISTING_EVIDENCE_CENSUS_KIND_SET_UNRESOLVED_COMPLETENESS_"
    "INSUFFICIENT_EQ_IS_RECONCILIATION_TARGET_NOT_SOURCE_U04_SIZING_IN_BASE_"
    "VS_NOT_IN_BASE_REMAINS_UNRESOLVED"
)
BLOCKER_ID = (
    "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_AFTER_NON_EQ_SOURCE_"
    "KIND_PRIMARY_PROOF_SURFACE_ABSENCE_RATIFIED"
)
ARCHITECTURE_BLOCKER = (
    "NO_IN_REPO_NON_EQ_EQUITY_STOCK_SOURCE_KIND_PRIMARY_PROOF_SURFACE_"
    "COMPLETENESS_INSUFFICIENT_KIND_SET_EMPTY_EQ_RECONCILIATION_TARGET_ONLY_"
    "MAPPING_STILL_INVALID"
)
NEXT_PRODUCTIVE_NODE = "OWNER_SUPPLIED_NON_EQ_EQUITY_STOCK_SOURCE_KIND_PRIMARY_PROOF_ARTIFACT"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_AN_OWNER_SUPPLIED_NON_EQ_EQUITY_STOCK_"
    "SOURCE_KIND_PRIMARY_PROOF_ARTIFACT_NOT_ALREADY_IN_THE_SEALED_EXISTING_"
    "EVIDENCE_CENSUS_NOT_EQ_NOT_U04_AND_NOT_LIVE_TODAY_STOCK_UPLIFT_V1"
)
NEXT_ACTION = (
    "STOP_FIRST_DEFINITIVE_BLOCK_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_"
    "SOURCE_MAPPING_NO_IN_REPO_NON_EQ_SOURCE_KIND_PRIMARY_PROOF_SURFACE_NO_GET"
)
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SURFACE_ROWS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "CANONICAL_AUTHORITY",
        "C01_THROUGH_C16",
        "FORBIDDEN_AS_29P_EQUITY_AND_NOT_EVENT_TAXONOMY",
        "ALREADY_REJECTED_NOT_REVIVABLE",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA",
        "SCHEMA_ONLY_NO_RUNTIME_INSTANCE",
        "NOT_SOURCE_GENERATION",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "FORENSIC_RAW",
        "VENUE_WITNESS_OR_FRESH_AVAILABLE_MARGIN",
        "OBSERVATION_SCHEMA_OR_C01_CLASS",
        "NOT_29P_EQUITY_SOURCE_KIND",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "INTERNAL_RECONSTRUCTION_SCHEMA",
        "TYPED_SCHEMA_NOT_SOURCE",
        "NO_RUNTIME_INSTANCE",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "eq",
        "RECONCILIATION_TARGET_NOT_SOURCE",
        "EQ_FORBIDDEN_AS_PRIMARY_PROOF_SURFACE",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "U04_PENDING_ORDER_RESERVATION",
        "EXPLICITLY_NOT_EQUITY_STOCK",
        "U04_FORBIDDEN_AS_EQUITY_STOCK_KIND_OR_SOURCE",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "HISTORICAL_INTERMEDIATE",
        TODAY_SOURCE_KIND,
        "LIVE_EQUITY_STOCK_INITIAL_STOCK_NOT_D6_SOURCE",
        "LIVE_TODAY_STOCK_UPLIFT_FORBIDDEN",
        "LIVE_EQUITY_STOCK_KIND_SET_NOT_ACCOUNT_EQUITY_SOURCE",
    ),
    (
        "FORENSIC_RAW",
        "FILL_OR_EXECUTION_LEDGER",
        "EXCLUDED_UNPROVEN_C10_C11_C16_CLASS_RISK",
        "NOT_CLASSIFIED_EQUITY_STOCK_SOURCE_KIND",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "U02_U03_PNL",
        "EMBEDDED_IN_AVAILABLE_FOR_SIZING_BASE_NOT_EVENT_CLASS",
        "NOT_AN_EVENT_KIND",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "P01_GOVERNED_RISK_CAPITAL_REDUCTION",
        "EXPLICITLY_NOT_EQUITY_SOURCE_OR_EVENT_KIND",
        "NOT_EQUITY_STOCK",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "U05_GET_OR_OWNER_SUPPLIED_EMBEDDING_WITNESS",
        "NONE_BINDABLE_OR_ABSENT_WRONG_PROOF_OBJECT",
        "EMBEDDING_WITNESS_IS_NOT_SOURCE_KIND_PRIMARY_PROOF",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "U06_PAIRED_FEE_GET",
        "NONE_BINDABLE_NOT_EXCLUDE",
        "FEE_GET_IS_NOT_SOURCE_KIND_PRIMARY_PROOF",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "RESIDUAL_EXHAUSTIVENESS_GET",
        "NONE_BINDABLE_DURABLE_UNKNOWN",
        "EXHAUSTIVENESS_IS_NOT_SOURCE_KIND_PRIMARY_PROOF",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "CANONICAL_AUTHORITY",
        "ACCOUNT_BILLS",
        "CURRENT_NONCANONICAL",
        "NONCANONICAL_BILLS_ARE_NOT_SOURCE_KIND_PRIMARY_PROOF",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "INTERPRETATION_HYPOTHESIS_UNKNOWN",
        "HYPOTHESIS_DEPOSIT_WITHDRAWAL_TRANSFER_FUNDING",
        "HYPOTHESIS_ONLY_NOT_CLASSIFIED",
        "NAME_OR_CONSUMER_EXPECTATION_IS_NOT_PRIMARY_PROOF",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
    (
        "FORENSIC_RAW",
        "SECTION_11_14_POS_C17",
        "POSITION_EVIDENCE_DIFFERENT_DIMENSION",
        "POS_IS_NOT_ACCOUNT_EQUITY_SOURCE_KIND",
        "ACCOUNT_EQUITY_RECONSTRUCTION",
    ),
)


class NonEqEquityStockSourceKindPrimaryProofSurfaceError(ValueError):
    """Fail-closed NON_EQ source-kind primary-proof-surface violation."""


@dataclass(frozen=True)
class NonEqEquityStockSourceKindPrimaryProofSurfaceResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    primary_proof_surface_status: str
    primary_proof_surface: str
    primary_proof_provenance: str
    non_eq_equity_stock_source_kind_status: str
    ratified_source_kinds: str
    source_kind_completeness_status: str
    kind_set_resolved: str
    canonically_valid_account_equity_source_mapping: str
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
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(f"{field}_DRIFT:{actual}")


def reject_hypothesis_name_as_source_kind_v1(*, claimed: str) -> None:
    if claimed in HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES or claimed in {
        STATUS_RATIFIED_PRIMARY_PROOF_SURFACE,
        OUTCOME_INCLUDE,
        "RATIFIED_SOURCE_KIND",
    }:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            f"HYPOTHESIS_NAME_IS_NOT_PRIMARY_PROOF_SURFACE:{claimed}"
        )


def reject_existing_surface_as_bindable_v1(*, claimed: str) -> None:
    if claimed in {STATUS_RATIFIED_PRIMARY_PROOF_SURFACE, "BOUND", "SELECTED", TRUE_TOKEN, "true"}:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            f"EXISTING_EVIDENCE_SURFACE_IS_NOT_BINDABLE:{claimed}"
        )


def _assert_standing_pins() -> None:
    if LIVE_ARMED is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("LIVE_ARMED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("U05_UNKNOWN_PRESERVED")
    if PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("PRODUCTIVE_U05_MEMBERSHIP_DRIFT")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("U06_UNKNOWN_PRESERVED")
    if PRODUCTIVE_U06_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("PRODUCTIVE_U06_MEMBERSHIP_DRIFT")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("RESIDUAL_UNKNOWN_PRESERVED")
    if PRODUCTIVE_RESIDUAL_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "PRODUCTIVE_RESIDUAL_MEMBERSHIP_DRIFT"
        )
    if U04_LEGACY_STATUS != STATE_UNRESOLVED:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("LEGACY_U04_UNRESOLVED_PRESERVED")
    if U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE != STATE_UNRESOLVED:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "U04_INCLUSION_MUST_REMAIN_UNRESOLVED"
        )
    if U04_LEGACY_INCLUDE_EXCLUDE_AS_EQUITY_STOCK_KIND_RETIRED_AS_PRODUCTIVE_BLOCKER is not True:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("U04_LEGACY_NOT_RETIRED")
    if PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("PRODUCTIVE_U04_MEMBERSHIP_DRIFT")
    if PRODUCTIVE_U04_EQUITY_STOCK_ROLE != DISPOSITION_NOT_EQUITY_STOCK:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("U04_STOCK_ROLE_DRIFT")
    if PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("U04_SIZING_ROLE_DRIFT")
    if U04_KIND_SET_DISPOSITION != DISPOSITION_NOT_EQUITY_STOCK:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("U04_KIND_SET_DISPOSITION_DRIFT")
    if U04_PLACEMENT != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("U04_PLACEMENT_DRIFT")
    if CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES != ():
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "CURRENT_PRODUCTIVE_REMAINING_MUST_BE_EMPTY"
        )
    if NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES != (TARGET_U05, TARGET_U06, TARGET_RESIDUAL):
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "LEGACY_NAMED_REMAINING_MUST_REMAIN"
        )
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED":
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("U04_ALGEBRA_TERM_DRIFT")
    if KIND_SET_RESOLVED is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("KIND_SET_RESOLVED_NOT_FALSE")
    if KIND_SET_UPLIFT_THIS_WORKPACKAGE is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("KIND_SET_UPLIFT_NOT_FALSE")
    if PRIMARY_PROOF_SURFACE_BOUND_THIS_WORKPACKAGE is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "PRIMARY_PROOF_SURFACE_MUST_STAY_UNBOUND"
        )
    if PRIMARY_PROOF_SURFACE_STATUS != "NONE_IN_EXISTING_REPO_HISTORICAL_FORENSIC_EVIDENCE":
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "PRIMARY_PROOF_SURFACE_STATUS_DRIFT"
        )
    if PRIMARY_PROOF_SURFACE != NONE_TOKEN:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "PRIMARY_PROOF_SURFACE_MUST_REMAIN_NONE"
        )
    if PRIMARY_PROOF_SURFACE_BINDING_STATUS != "NOT_BOUND":
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "SURFACE_BINDING_MUST_REMAIN_NOT_BOUND"
        )
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("KIND_SET_MUST_REMAIN_EMPTY")
    if RATIFIED_SOURCE_KIND_SET:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "SOURCE_KIND_SET_MUST_REMAIN_EMPTY"
        )
    if RATIFIED_NON_EQ_EQUITY_STOCK_SOURCE_KINDS:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "NON_EQ_SOURCE_KINDS_MUST_REMAIN_EMPTY"
        )
    if NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS != "NONE_INSUFFICIENT_NO_RATIFIABLE_KIND":
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("SOURCE_KIND_STATUS_DRIFT")
    if SOURCE_KIND_COMPLETENESS_STATUS != "INSUFFICIENT_UNPROVEN":
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("COMPLETENESS_STATUS_DRIFT")
    if SOURCE_KIND_COMPLETENESS_RATIFICATION != "INSUFFICIENT_NOT_KIND_SET_CLOSURE":
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("COMPLETENESS_RATIFICATION_DRIFT")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("MAPPING_MUST_REMAIN_INVALID")
    if MAPPING_PROVEN is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("MAPPING_PROVEN_NOT_FALSE")
    if SEMANTIC_MAPPING_PROVEN is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("SEMANTIC_MAPPING_NOT_FALSE")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("ALGEBRA_MUST_REMAIN_INCOMPLETE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "EQ_MUST_REMAIN_RECONCILIATION_TARGET"
        )
    if EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("EQ_TREATED_AS_SOURCE_NOT_FALSE")
    if D6_ACCOUNT_EQUITY_SOURCE_MAPPING_COVERAGE_STATUS != (
        "PARTIAL_FAIL_CLOSED_NO_RATIFIED_SOURCE_KIND"
    ):
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("MAPPING_COVERAGE_DRIFT")
    if ACCOUNT_EQUITY_SOURCE_MAPPING_DENIED_THIS_WORKPACKAGE is not True:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("MAPPING_DENY_PIN_DRIFT")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("EVENT_GET_NOT_AUTHORIZED")
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("OBSERVATION_GET_NOT_AUTHORIZED")
    if MS2_AUTHORIZED is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False or CENSUS_C17_CREATED is not False:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("C17_CREATED_NOT_FALSE")
    if GENUINELY_NEW_CANDIDATE_COUNT != 0:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "GENUINELY_NEW_CANDIDATE_COUNT_DRIFT"
        )
    if ACCEPTABLE_FOR_OWNER_RATIFICATION_COUNT != 0:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "ACCEPTABLE_FOR_OWNER_RATIFICATION_COUNT_DRIFT"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("BILLS_CANONICALIZED_FORBIDDEN")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("DAG_PIN_DRIFT")


def _assert_parent_cp_pack(*, sealed_cp_pack: Path) -> None:
    if not sealed_cp_pack.is_dir():
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("PARENT_CP_PACK_MISSING")
    claims = _load_json_object(path=sealed_cp_pack / CLAIMS_FILE)
    _require_token(
        field="NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS",
        payload=claims,
        expected="NONE_INSUFFICIENT_NO_RATIFIABLE_KIND",
    )
    _require_token(field="RATIFIED_SOURCE_KINDS", payload=claims, expected=NONE_TOKEN)
    _require_token(
        field="SOURCE_KIND_COMPLETENESS_STATUS",
        payload=claims,
        expected="INSUFFICIENT_UNPROVEN",
    )
    _require_token(field="KIND_SET_RESOLVED", payload=claims, expected=FALSE_TOKEN)
    _require_token(
        field="CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
        payload=claims,
        expected=FALSE_TOKEN,
    )
    _require_token(
        field="RECONCILIATION_TARGET_STATUS",
        payload=claims,
        expected="EQ_RECONCILIATION_TARGET_ONLY",
    )
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=PIN_OWNER_GO)
    _require_token(
        field="NEXT_PRODUCTIVE_NODE",
        payload=claims,
        expected="NON_EQ_EQUITY_STOCK_SOURCE_KIND_PRIMARY_PROOF_SURFACE",
    )
    if verify_manifest_sha256_v1(store_root=sealed_cp_pack) != 0:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("PARENT_CP_MANIFEST_INVALID")


def classify_primary_proof_surface_candidates_v1() -> dict[str, Any]:
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=DISPOSITION_NOT_EQUITY_STOCK)
    reject_eq_as_source_authority_v1(claimed=FALSE_TOKEN)
    reject_today_as_account_equity_source_kind_v1(
        claimed="NOT_RATIFIABLE_LIVE_EQUITY_STOCK_NOT_ACCOUNT_EQUITY_SOURCE_KIND"
    )
    reject_kind_set_uplift_v1(claimed=FALSE_TOKEN)
    reject_hypothesis_name_as_source_kind_v1(claimed="HYPOTHESIS_ONLY")
    reject_existing_surface_as_bindable_v1(claimed=STATUS_NOT_BINDABLE)
    rows: list[dict[str, str]] = []
    for layer, surface_id, equity_status, reason, boundary in _SURFACE_ROWS:
        rows.append(
            {
                "layer": layer,
                "surface_id": surface_id,
                "equity_stock_affecting_status": equity_status,
                "selection_status": STATUS_NOT_BINDABLE,
                "gap_reason": reason,
                "boundary": boundary,
            }
        )
    census_findings = build_source_candidate_census_findings_v1()
    if any(finding.genuinely_new_source_generation == TRUE_TOKEN for finding in census_findings):
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "GENUINELY_NEW_SURFACE_MUST_REMAIN_EMPTY"
        )
    if any(row["selection_status"] == STATUS_RATIFIED_PRIMARY_PROOF_SURFACE for row in rows):
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "PRIMARY_PROOF_SURFACE_MUST_REMAIN_NONE"
        )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "primary_proof_surface_status": PRIMARY_PROOF_SURFACE_STATUS,
        "primary_proof_surface": NONE_TOKEN,
        "surface_binding_status": PRIMARY_PROOF_SURFACE_BINDING_STATUS,
        "candidate_count": str(len(rows)),
        "candidates": rows,
        "source_candidate_census_finding_count": str(len(census_findings)),
        "genuinely_new_candidate_count": str(GENUINELY_NEW_CANDIDATE_COUNT),
        "acceptable_for_owner_ratification_count": str(ACCEPTABLE_FOR_OWNER_RATIFICATION_COUNT),
        "surface_proof_law": SURFACE_PROOF_LAW,
        "surface_evidence": SURFACE_EVIDENCE,
        "eq_role": "EQ_RECONCILIATION_TARGET_ONLY",
        "u04_equity_stock_role": DISPOSITION_NOT_EQUITY_STOCK,
        "today_source_kind_status": "NOT_RATIFIABLE_LIVE_EQUITY_STOCK_NOT_ACCOUNT_EQUITY_SOURCE_KIND",
        "synthetic_witness_used": FALSE_TOKEN,
        "durable_unknown_reopened": FALSE_TOKEN,
        "kind_set_uplift": FALSE_TOKEN,
        "primary_proof_surface_bound": FALSE_TOKEN,
    }


def reevaluate_downstream_v1(*, surface: Mapping[str, Any]) -> dict[str, Any]:
    if surface["primary_proof_surface"] != NONE_TOKEN:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError(
            "PRIMARY_PROOF_SURFACE_MUST_REMAIN_NONE"
        )
    if surface["primary_proof_surface_status"] != PRIMARY_PROOF_SURFACE_STATUS:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("SURFACE_STATUS_MUST_REMAIN_NONE")
    reject_kind_set_resolved_while_remaining_unknown_v1(claimed=FALSE_TOKEN)
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "kind_set": KIND_SET_EMPTY,
        "kind_set_resolved": FALSE_TOKEN,
        "legacy_named_remaining_unknown_necessary_classes": ",".join(
            NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES
        ),
        "current_productive_remaining_necessary_equity_stock_classes": ",".join(
            CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
        ),
        "non_eq_equity_stock_source_kind_status": NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
        "ratified_source_kinds": NONE_TOKEN,
        "source_kind_completeness_status": SOURCE_KIND_COMPLETENESS_STATUS,
        "primary_proof_surface_status": PRIMARY_PROOF_SURFACE_STATUS,
        "primary_proof_surface": NONE_TOKEN,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "account_equity_source_mapping_status": DAG_PIN,
        "reconstruction_algebra_complete": FALSE_TOKEN,
        "reconstruction_status": (
            "INCOMPLETE_NO_IN_REPO_NON_EQ_SOURCE_KIND_PRIMARY_PROOF_SURFACE_"
            "COMPLETENESS_INSUFFICIENT_U04_SIZING_INCLUSION_UNRESOLVED_U05_U06_"
            "NOT_CURRENT_PRODUCTIVE_TERMS"
        ),
        "u04_status": STATE_UNRESOLVED,
        "u04_kind_set_disposition": DISPOSITION_NOT_EQUITY_STOCK,
        "u05_legacy_status": DECISION_REMAIN_UNKNOWN,
        "u06_legacy_status": DECISION_REMAIN_UNKNOWN,
        "residual_legacy_status": DECISION_REMAIN_UNKNOWN,
        "equity_stock_readiness": (
            "NOT_READY_KIND_SET_UNRESOLVED_AND_MAPPING_NOT_CANONICALLY_VALID"
        ),
        "running_account_equity_available_for_sizing_status": (
            "UNBOUND_29P_SEMANTIC_MAPPING_UNPROVEN_U04_IN_BASE_VS_NOT_IN_BASE_UNRESOLVED"
        ),
        "risk_sizing_readiness": (
            "NOT_READY_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_"
            "AND_29P_SEMANTIC_MAPPING_UNPROVEN"
        ),
        "local_advancement_exhausted": TRUE_TOKEN,
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "standing_full_core_dag_pin": DAG_PIN,
        "earliest_unresolved_algebra_term": EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    }


def execute_non_eq_equity_stock_source_kind_primary_proof_surface_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_cp_pack: Path | str | None = None,
    persist_as_of: str | None = None,
) -> NonEqEquityStockSourceKindPrimaryProofSurfaceResultV1:
    if owner_go != OWNER_GO:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=DISPOSITION_NOT_EQUITY_STOCK)
    reject_eq_as_source_authority_v1(claimed=FALSE_TOKEN)
    reject_today_as_account_equity_source_kind_v1(
        claimed="NOT_RATIFIABLE_LIVE_EQUITY_STOCK_NOT_ACCOUNT_EQUITY_SOURCE_KIND"
    )
    reject_kind_set_uplift_v1(claimed=FALSE_TOKEN)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cp_pack = (
        Path(sealed_cp_pack) if sealed_cp_pack is not None else repo / CANONICAL_CP_PACK_RELPATH
    )
    _assert_parent_cp_pack(sealed_cp_pack=cp_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    surface = classify_primary_proof_surface_candidates_v1()
    downstream = reevaluate_downstream_v1(surface=surface)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": (
            "SATISFIED_BY_EXPLICIT_ABSENCE_RATIFICATION_NO_IN_REPO_PRIMARY_PROOF_"
            "SURFACE_NO_KIND_NO_KIND_SET_UPLIFT_EQ_NOT_SOURCE"
        ),
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CP_PACK": CANONICAL_CP_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "START_BLOCK": DAG_PIN,
        "PRIMARY_PROOF_SURFACE_STATUS": PRIMARY_PROOF_SURFACE_STATUS,
        "PRIMARY_PROOF_SURFACE": NONE_TOKEN,
        "PRIMARY_PROOF_PROVENANCE": SURFACE_EVIDENCE,
        "SURFACE_BINDING_STATUS": PRIMARY_PROOF_SURFACE_BINDING_STATUS,
        "CONCRETE_SURFACE_SELECTION_STATUS": "NONE_IN_EXISTING_EVIDENCE",
        "CONCRETE_SURFACE_ID": NONE_TOKEN,
        "SURFACE_PROOF_LAW": SURFACE_PROOF_LAW,
        "SURFACE_EVIDENCE": SURFACE_EVIDENCE,
        "PRIMARY_PROOF_SURFACE_BOUND_THIS_WORKPACKAGE": FALSE_TOKEN,
        "NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS": NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
        "RATIFIED_SOURCE_KINDS": NONE_TOKEN,
        "SOURCE_KIND_COMPLETENESS_STATUS": SOURCE_KIND_COMPLETENESS_STATUS,
        "SOURCE_KIND_COMPLETENESS_RATIFICATION": SOURCE_KIND_COMPLETENESS_RATIFICATION,
        "KIND_SET_UPLIFT_THIS_WORKPACKAGE": FALSE_TOKEN,
        "EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE": FALSE_TOKEN,
        "U04_LEGACY_STATUS": STATE_UNRESOLVED,
        "U04_PRODUCTIVE_SCOPE_STATUS": PRODUCTIVE_MEMBERSHIP,
        "U04_EQUITY_STOCK_ROLE": DISPOSITION_NOT_EQUITY_STOCK,
        "U04_AVAILABLE_CAPITAL_ROLE": "AVAILABLE_FOR_SIZING_OR_RISK_SIZING",
        "U04_KIND_SET_DISPOSITION": DISPOSITION_NOT_EQUITY_STOCK,
        "U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE": STATE_UNRESOLVED,
        "PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP": PRODUCTIVE_MEMBERSHIP,
        "PRODUCTIVE_U04_EQUITY_STOCK_ROLE": DISPOSITION_NOT_EQUITY_STOCK,
        "TODAY_SOURCE_KIND": TODAY_SOURCE_KIND,
        "TODAY_SOURCE_KIND_STATUS": "NOT_RATIFIABLE_LIVE_EQUITY_STOCK_NOT_ACCOUNT_EQUITY_SOURCE_KIND",
        "AUTHORITY_CHANGE": (
            "ADDITIVE_ABSENCE_RATIFICATION_NO_SURFACE_NO_KIND_NO_KIND_SET_UPLIFT_EQ_NOT_SOURCE"
        ),
        "MIGRATION_STRATEGY": (
            "ADDITIVE_VERSIONED_ABSENCE_LEGACY_UNKNOWN_PRESERVED_NO_KIND_SET_UPLIFT"
        ),
        "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES": ",".join(
            NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES
        ),
        "CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES": ",".join(
            CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
        ),
        "U04_STATUS": STATE_UNRESOLVED,
        "EARLIEST_UNRESOLVED_ALGEBRA_TERM": EARLIEST_UNRESOLVED_ALGEBRA_TERM,
        "U05_STATUS": DECISION_REMAIN_UNKNOWN,
        "U05_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_LEGACY_STATUS": DECISION_REMAIN_UNKNOWN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_ABSENT_OR_ZERO": TRUE_TOKEN,
        "DURABLE_UNKNOWN_REOPENED": FALSE_TOKEN,
        "SYNTHETIC_WITNESS_USED": FALSE_TOKEN,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_STATUS": KIND_SET_EMPTY,
        "ACCOUNT_EQUITY_SOURCE_MAPPING": DAG_PIN,
        "ACCOUNT_EQUITY_SOURCE_MAPPING_STATUS": DAG_PIN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "MAPPING_PROVEN": FALSE_TOKEN,
        "SEMANTIC_MAPPING_PROVEN": FALSE_TOKEN,
        "RECONCILIATION_TARGET_STATUS": "EQ_RECONCILIATION_TARGET_ONLY",
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "EQ_RECONCILIATION_TARGET_ONLY": TRUE_TOKEN,
        "RECONSTRUCTION_ALGEBRA_COMPLETE": FALSE_TOKEN,
        "RECONSTRUCTION_STATUS": downstream["reconstruction_status"],
        "EQUITY_STOCK_READINESS": downstream["equity_stock_readiness"],
        "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING_STATUS": downstream[
            "running_account_equity_available_for_sizing_status"
        ],
        "RISK_SIZING_READINESS": downstream["risk_sizing_readiness"],
        "NO_GET_REQUIRED": TRUE_TOKEN,
        "NO_EQ_SOURCE_AUTHORITY": TRUE_TOKEN,
        "NO_ALGEBRAIC_UPLIFT": TRUE_TOKEN,
        "NO_HOPE_GET": TRUE_TOKEN,
        "NO_RETROACTIVE_SEALED_EVIDENCE_UPLIFT": TRUE_TOKEN,
        "MAX_GET_COUNT": "0",
        "AUTHORIZED_GET_COUNT": "0",
        "ACTUAL_GET_COUNT": "0",
        "VENUE_GET_COUNT": "0",
        "VENUE_GET_SURFACES": NONE_TOKEN,
        "RETRY_COUNT": "0",
        "POST_COUNT": "0",
        "SECRET_RESOLUTION_STATUS": "NOT_ATTEMPTED",
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "GATE_A_REOPENED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "PRODUCTIVE_ACQUISITION_AUTHORIZED": FALSE_TOKEN,
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "HOPE_GET_FORBIDDEN": TRUE_TOKEN,
        "LOCAL_ADVANCEMENT_EXHAUSTED": TRUE_TOKEN,
        "FIRST_DEFINITIVE_BLOCK": DAG_PIN,
        "EXACT_MISSING_PREDICATE": EXACT_MISSING_PREDICATE,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "NEXT_PRODUCTIVE_NODE": NEXT_PRODUCTIVE_NODE,
        "BLOCKER_ID": BLOCKER_ID,
        "ARCHITECTURE_BLOCKER": ARCHITECTURE_BLOCKER,
        "PARENT_BLOCKER_ID": PARENT_BLOCKER_ID,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "NEXT_ACTION": NEXT_ACTION,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
        "ATLAS_AUTHORITY": NONE_TOKEN,
    }
    lineage = {
        "layer": "HISTORICAL",
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "pin_owner_go": PIN_OWNER_GO,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_cp_pack": CANONICAL_CP_PACK_RELPATH,
        "historical_artifacts_rewritten": FALSE_TOKEN,
        "synthetic_witness_used": FALSE_TOKEN,
        "hope_get_used": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "include_or_exclude_normalized": FALSE_TOKEN,
        "today_imported_as_account_equity_source_kind": FALSE_TOKEN,
        "kind_set_resolved": FALSE_TOKEN,
        "mapping_ratified": FALSE_TOKEN,
        "primary_proof_surface_bound": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "trading_logic_unchanged": TRUE_TOKEN,
        "u04_not_reclassified_as_equity_stock_kind": TRUE_TOKEN,
        "u04_algebra_inclusion_not_normalized": TRUE_TOKEN,
        "legacy_u04_unresolved_preserved": TRUE_TOKEN,
        "legacy_u05_unknown_preserved": TRUE_TOKEN,
        "legacy_u06_unknown_preserved": TRUE_TOKEN,
        "legacy_residual_unknown_preserved": TRUE_TOKEN,
        "named_remaining_historical_tuple_unchanged": TRUE_TOKEN,
        "eq_not_elevated_to_source": TRUE_TOKEN,
        "today_not_imported_as_account_equity_source_kind": TRUE_TOKEN,
        "kind_set_not_uplifted": TRUE_TOKEN,
        "option_d_architecture_unchanged": TRUE_TOKEN,
        "gate_a_not_retried": TRUE_TOKEN,
        "gate_b_not_executed": TRUE_TOKEN,
        "bills_authority_unchanged": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
    }
    architecture = {
        "layer": "CANONICAL_AUTHORITY",
        "blocker_id": BLOCKER_ID,
        "architecture_blocker": ARCHITECTURE_BLOCKER,
        "parent_blocker_id": PARENT_BLOCKER_ID,
        "primary_proof_surface_status": PRIMARY_PROOF_SURFACE_STATUS,
        "primary_proof_surface": NONE_TOKEN,
        "non_eq_equity_stock_source_kind_status": NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
        "ratified_source_kinds": NONE_TOKEN,
        "source_kind_completeness_status": SOURCE_KIND_COMPLETENESS_STATUS,
        "kind_set_resolved": FALSE_TOKEN,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "u04_status": STATE_UNRESOLVED,
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
        "atlas_authority": NONE_TOKEN,
    }
    layers = {
        "CANONICAL_AUTHORITY": "architecture_blocker_v1.json",
        "FORENSIC_RAW_EVIDENCE": "NONE_NEW_RAW_BYTES_SEALED_CP_AV_BE_CA_CF_CH_CK_CONSUMED",
        "ADJUDICATED_CONCLUSION": "qualification_v1.json,downstream_dependency_tree_v1.json",
        "HISTORICAL": "LINEAGE.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN_AS_SOURCE_KIND",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
        "MIGRATION_RATIFICATION": "claims.json",
        "CURRENT_PRODUCTIVE_MAPPING_STATUS": DAG_PIN,
    }
    census_payload = {
        "layer": "FORENSIC_RAW",
        "candidate_count": surface["candidate_count"],
        "candidates": surface["candidates"],
        "primary_proof_surface": NONE_TOKEN,
        "primary_proof_surface_status": PRIMARY_PROOF_SURFACE_STATUS,
        "genuinely_new_candidate_count": str(GENUINELY_NEW_CANDIDATE_COUNT),
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "qualification_v1.json", payload=surface)
    _persist_json(path=store / "census_v1.json", payload=census_payload)
    _persist_json(path=store / "downstream_dependency_tree_v1.json", payload=downstream)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "layers_v1.json", payload=layers)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("MANIFEST_VERIFY_NOT_ZERO")
    if OUTCOME_EXCLUDE in claims["PRIMARY_PROOF_SURFACE_STATUS"]:
        raise NonEqEquityStockSourceKindPrimaryProofSurfaceError("ABSENCE_IS_NOT_EXCLUDE")
    return NonEqEquityStockSourceKindPrimaryProofSurfaceResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        primary_proof_surface_status=PRIMARY_PROOF_SURFACE_STATUS,
        primary_proof_surface=NONE_TOKEN,
        primary_proof_provenance=SURFACE_EVIDENCE,
        non_eq_equity_stock_source_kind_status=NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
        ratified_source_kinds=NONE_TOKEN,
        source_kind_completeness_status=SOURCE_KIND_COMPLETENESS_STATUS,
        kind_set_resolved=FALSE_TOKEN,
        canonically_valid_account_equity_source_mapping=FALSE_TOKEN,
        first_definitive_block=DAG_PIN,
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
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "NonEqEquityStockSourceKindPrimaryProofSurfaceError",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "STATUS_NOT_BINDABLE",
    "SURFACE_EVIDENCE",
    "SURFACE_PROOF_LAW",
    "classify_primary_proof_surface_candidates_v1",
    "execute_non_eq_equity_stock_source_kind_primary_proof_surface_v1",
    "reject_existing_surface_as_bindable_v1",
    "reject_hypothesis_name_as_source_kind_v1",
)
