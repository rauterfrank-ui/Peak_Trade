"""Ratify NON_EQ source-kind insufficiency or completeness without uplift.

Consumes the workpackage Owner-GO. Satisfies the CO-named GO by an
explicit insufficiency ratification: no non-eq equity-stock-affecting
source kind is ratifiable from sealed evidence, and source-kind
completeness is INSUFFICIENT_UNPROVEN. Does not INCLUDE or EXCLUDE.
Does not set KIND_SET_RESOLVED. Does not treat venue eq as source.
Does not reintroduce U04 into the kind set. Does not import live
TODAY initial-stock membership as an account-equity source kind.
Does not GET. Does not POST. Does not Hope-GET. AUTHORITY_EFFECT=NONE.

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
    STATUS_RATIFIED_NON_SOURCE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    TARGET_RESIDUAL,
    TARGET_U05,
    TARGET_U06,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_C01_C16_FORBIDDEN,
    DISPOSITION_EXCLUDED,
    DISPOSITION_NOT_EQUITY_STOCK,
    DISPOSITION_NOT_EVENT_KIND,
    DISPOSITION_UNKNOWN,
    build_forensic_event_kind_census_findings_v1,
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
    KIND_SET_RESOLVED,
    KIND_SET_UPLIFT_THIS_WORKPACKAGE,
    MS2_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1 import (
    reject_durable_unknown_as_include_or_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u04_pending_order_reservation_or_account_equity_mapping_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CO_PACK_RELPATH,
    NEXT_OWNER_GO as PIN_OWNER_GO,
    reject_eq_as_source_authority_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

OWNER_GO = (
    "OWNER_GO_RATIFY_NON_EQ_EQUITY_STOCK_SOURCE_KIND_OR_COMPLETENESS_"
    "WITHOUT_KIND_SET_UPLIFT_AND_WITHOUT_TREATING_EQ_AS_SOURCE_V1"
)
EXPECTED_ORIGIN_MAIN_SHA = "e7d68065394876d1aed2c2dd2483b2584db93486"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_non_eq_equity_stock_source_kind_or_completeness_v1/2026-09-15T180000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T18:00:00Z"
SCHEMA_CLASS = "NON_EQ_EQUITY_STOCK_SOURCE_KIND_OR_COMPLETENESS_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
STATE_UNRESOLVED = "UNRESOLVED"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
PRODUCTIVE_MEMBERSHIP = "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
STATUS_NOT_RATIFIABLE_UNKNOWN = "NOT_RATIFIABLE_UNKNOWN"
STATUS_NOT_RATIFIABLE_EXCLUDED = "NOT_RATIFIABLE_EXCLUDED"
STATUS_NOT_RATIFIABLE_NOT_EVENT_KIND = "NOT_RATIFIABLE_NOT_EVENT_KIND"
STATUS_NOT_RATIFIABLE_NOT_EQUITY_STOCK = "NOT_RATIFIABLE_NOT_EQUITY_STOCK"
STATUS_NOT_RATIFIABLE_FORBIDDEN = "NOT_RATIFIABLE_FORBIDDEN"
STATUS_NOT_RATIFIABLE_EQ_TARGET = "NOT_RATIFIABLE_EQ_RECONCILIATION_TARGET"
STATUS_NOT_RATIFIABLE_LIVE_TODAY = "NOT_RATIFIABLE_LIVE_EQUITY_STOCK_NOT_ACCOUNT_EQUITY_SOURCE_KIND"
STATUS_RATIFIED_SOURCE_KIND = "RATIFIED_SOURCE_KIND"
_DISPOSITION_REASON = {
    DISPOSITION_UNKNOWN: STATUS_NOT_RATIFIABLE_UNKNOWN,
    DISPOSITION_EXCLUDED: STATUS_NOT_RATIFIABLE_EXCLUDED,
    DISPOSITION_NOT_EVENT_KIND: STATUS_NOT_RATIFIABLE_NOT_EVENT_KIND,
    DISPOSITION_NOT_EQUITY_STOCK: STATUS_NOT_RATIFIABLE_NOT_EQUITY_STOCK,
    DISPOSITION_C01_C16_FORBIDDEN: STATUS_NOT_RATIFIABLE_FORBIDDEN,
}
SOURCE_KIND_PROOF_LAW = (
    "NON_EQ_EQUITY_STOCK_SOURCE_KIND_REQUIRES_SEALED_EQUITY_STOCK_AFFECTING_"
    "CLASSIFIED_KIND_INSIDE_ACCOUNT_EQUITY_RECONSTRUCTION_BOUNDARY_EQ_IS_"
    "RECONCILIATION_TARGET_NOT_SOURCE_U04_IS_NOT_EQUITY_STOCK_AFFECTING_"
    "LIVE_TODAY_STOCK_MEMBERSHIP_IS_NOT_D6_SOURCE_KIND_UNKNOWN_IS_NOT_INCLUDE"
)
COMPLETENESS_PROOF_LAW = (
    "SOURCE_KIND_COMPLETENESS_REQUIRES_PROVEN_EXHAUSTIVE_NON_EQ_EQUITY_"
    "STOCK_AFFECTING_SOURCE_KIND_SET_EMPTY_PRODUCTIVE_REMAINING_IS_NOT_"
    "COMPLETENESS_NAMED_REMAINING_UNKNOWN_PRESERVED_SINGLE_KIND_WOULD_NOT_"
    "PROVE_COMPLETENESS_KIND_SET_RESOLVED_REMAINS_FALSE"
)
SOURCE_KIND_EVIDENCE = (
    "SEALED_AV_CENSUS_NO_INCLUDED_CLASSIFIED_EQUITY_STOCK_KIND_PLUS_BE_"
    "RATIFIED_SOURCE_KINDS_NONE_PLUS_CO_U04_NOT_EQUITY_STOCK_PLUS_AR_EQ_"
    "RECONCILIATION_TARGET_ONLY_PLUS_BW_TODAY_LIVE_KIND_SET_MEMBER_NOT_"
    "ACCOUNT_EQUITY_SOURCE_KIND_PLUS_AX_U05_U06_RESIDUAL_REMAIN_UNKNOWN"
)
COMPLETENESS_EVIDENCE = (
    "SEALED_AX_NAMED_REMAINING_UNKNOWN_PRESERVED_PLUS_CI_RESIDUAL_"
    "EXHAUSTIVENESS_DURABLE_UNKNOWN_PLUS_CN_EMPTY_PRODUCTIVE_REMAINING_"
    "IS_NOT_KIND_SET_CLOSURE_PLUS_AU_COMPLETE_EVENT_STREAM_UNPROVEN_PLUS_"
    "NO_RATIFIED_SOURCE_KIND"
)
EXACT_MISSING_PREDICATE = (
    "NO_RATIFIED_NON_EQ_EQUITY_STOCK_SOURCE_KIND_AFTER_SEALED_CENSUS_"
    "COMPLETENESS_INSUFFICIENT_KIND_SET_UNRESOLVED_EQ_IS_RECONCILIATION_"
    "TARGET_NOT_SOURCE_U04_SIZING_IN_BASE_VS_NOT_IN_BASE_REMAINS_UNRESOLVED"
)
BLOCKER_ID = (
    "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_AFTER_NON_EQ_"
    "SOURCE_KIND_AND_COMPLETENESS_INSUFFICIENCY_RATIFIED"
)
ARCHITECTURE_BLOCKER = (
    "NO_RATIFIABLE_NON_EQ_EQUITY_STOCK_SOURCE_KIND_COMPLETENESS_"
    "INSUFFICIENT_KIND_SET_EMPTY_EQ_RECONCILIATION_TARGET_ONLY_MAPPING_"
    "STILL_INVALID"
)
NEXT_PRODUCTIVE_NODE = "NON_EQ_EQUITY_STOCK_SOURCE_KIND_PRIMARY_PROOF_SURFACE"
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_OR_AUTHORIZE_A_NEW_NON_EQ_EQUITY_STOCK_"
    "SOURCE_KIND_PRIMARY_PROOF_SURFACE_NOT_EQ_NOT_U04_AND_NOT_LIVE_TODAY_"
    "STOCK_UPLIFT_V1"
)
NEXT_ACTION = (
    "STOP_FIRST_DEFINITIVE_BLOCK_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_"
    "SOURCE_MAPPING_NON_EQ_SOURCE_KIND_AND_COMPLETENESS_INSUFFICIENT_NO_GET"
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


class NonEqEquityStockSourceKindOrCompletenessError(ValueError):
    """Fail-closed non-eq source-kind / completeness ratification violation."""


@dataclass(frozen=True)
class NonEqEquityStockSourceKindOrCompletenessResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    non_eq_equity_stock_source_kind_status: str
    ratified_source_kinds: str
    source_kind_completeness_status: str
    kind_set_resolved: str
    canonically_valid_account_equity_source_mapping: str
    account_equity_source_mapping_status: str
    reconciliation_target_status: str
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
        raise NonEqEquityStockSourceKindOrCompletenessError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise NonEqEquityStockSourceKindOrCompletenessError(f"{field}_DRIFT:{actual}")


def reject_today_as_account_equity_source_kind_v1(*, claimed: str) -> None:
    if claimed in {TODAY_SOURCE_KIND, STATUS_RATIFIED_SOURCE_KIND, "INCLUDE", OUTCOME_INCLUDE}:
        raise NonEqEquityStockSourceKindOrCompletenessError(
            f"LIVE_TODAY_STOCK_IS_NOT_ACCOUNT_EQUITY_SOURCE_KIND:{claimed}"
        )


def reject_empty_productive_remaining_as_completeness_v1(*, claimed: str) -> None:
    if claimed in {"COMPLETE", "PROVEN", "KIND_SET_RESOLVED", "true", "TRUE"}:
        raise NonEqEquityStockSourceKindOrCompletenessError(
            f"EMPTY_PRODUCTIVE_REMAINING_IS_NOT_COMPLETENESS:{claimed}"
        )


def reject_single_kind_as_completeness_v1(*, claimed: str) -> None:
    if claimed in {"COMPLETE", "PROVEN", "KIND_SET_RESOLVED", "true", "TRUE"}:
        raise NonEqEquityStockSourceKindOrCompletenessError(
            f"SINGLE_KIND_DOES_NOT_PROVE_COMPLETENESS:{claimed}"
        )


def reject_kind_set_uplift_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "RESOLVED", "KIND_SET_RESOLVED_TRUE"}:
        raise NonEqEquityStockSourceKindOrCompletenessError(f"KIND_SET_UPLIFT_FORBIDDEN:{claimed}")


def _assert_standing_pins() -> None:
    if WIRE_SEND_PERMITTED is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise NonEqEquityStockSourceKindOrCompletenessError("U05_UNKNOWN_PRESERVED")
    if PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise NonEqEquityStockSourceKindOrCompletenessError("PRODUCTIVE_U05_MEMBERSHIP_DRIFT")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise NonEqEquityStockSourceKindOrCompletenessError("U06_UNKNOWN_PRESERVED")
    if PRODUCTIVE_U06_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise NonEqEquityStockSourceKindOrCompletenessError("PRODUCTIVE_U06_MEMBERSHIP_DRIFT")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise NonEqEquityStockSourceKindOrCompletenessError("RESIDUAL_UNKNOWN_PRESERVED")
    if PRODUCTIVE_RESIDUAL_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise NonEqEquityStockSourceKindOrCompletenessError("PRODUCTIVE_RESIDUAL_MEMBERSHIP_DRIFT")
    if U04_LEGACY_STATUS != STATE_UNRESOLVED:
        raise NonEqEquityStockSourceKindOrCompletenessError("LEGACY_U04_UNRESOLVED_PRESERVED")
    if U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE != STATE_UNRESOLVED:
        raise NonEqEquityStockSourceKindOrCompletenessError("U04_INCLUSION_MUST_REMAIN_UNRESOLVED")
    if U04_LEGACY_INCLUDE_EXCLUDE_AS_EQUITY_STOCK_KIND_RETIRED_AS_PRODUCTIVE_BLOCKER is not True:
        raise NonEqEquityStockSourceKindOrCompletenessError("U04_LEGACY_NOT_RETIRED")
    if PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP != PRODUCTIVE_MEMBERSHIP:
        raise NonEqEquityStockSourceKindOrCompletenessError("PRODUCTIVE_U04_MEMBERSHIP_DRIFT")
    if PRODUCTIVE_U04_EQUITY_STOCK_ROLE != DISPOSITION_NOT_EQUITY_STOCK:
        raise NonEqEquityStockSourceKindOrCompletenessError("U04_STOCK_ROLE_DRIFT")
    if PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise NonEqEquityStockSourceKindOrCompletenessError("U04_SIZING_ROLE_DRIFT")
    if U04_KIND_SET_DISPOSITION != DISPOSITION_NOT_EQUITY_STOCK:
        raise NonEqEquityStockSourceKindOrCompletenessError("U04_KIND_SET_DISPOSITION_DRIFT")
    if U04_PLACEMENT != "AVAILABLE_FOR_SIZING_OR_RISK_SIZING":
        raise NonEqEquityStockSourceKindOrCompletenessError("U04_PLACEMENT_DRIFT")
    if CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES != ():
        raise NonEqEquityStockSourceKindOrCompletenessError(
            "CURRENT_PRODUCTIVE_REMAINING_MUST_BE_EMPTY"
        )
    if NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES != (TARGET_U05, TARGET_U06, TARGET_RESIDUAL):
        raise NonEqEquityStockSourceKindOrCompletenessError("LEGACY_NAMED_REMAINING_MUST_REMAIN")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED":
        raise NonEqEquityStockSourceKindOrCompletenessError("U04_ALGEBRA_TERM_DRIFT")
    if KIND_SET_RESOLVED is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("KIND_SET_RESOLVED_NOT_FALSE")
    if KIND_SET_UPLIFT_THIS_WORKPACKAGE is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("KIND_SET_UPLIFT_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise NonEqEquityStockSourceKindOrCompletenessError("KIND_SET_MUST_REMAIN_EMPTY")
    if RATIFIED_SOURCE_KIND_SET:
        raise NonEqEquityStockSourceKindOrCompletenessError("SOURCE_KIND_SET_MUST_REMAIN_EMPTY")
    if RATIFIED_NON_EQ_EQUITY_STOCK_SOURCE_KINDS:
        raise NonEqEquityStockSourceKindOrCompletenessError("NON_EQ_SOURCE_KINDS_MUST_REMAIN_EMPTY")
    if NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS != "NONE_INSUFFICIENT_NO_RATIFIABLE_KIND":
        raise NonEqEquityStockSourceKindOrCompletenessError("SOURCE_KIND_STATUS_DRIFT")
    if SOURCE_KIND_COMPLETENESS_STATUS != "INSUFFICIENT_UNPROVEN":
        raise NonEqEquityStockSourceKindOrCompletenessError("COMPLETENESS_STATUS_DRIFT")
    if SOURCE_KIND_COMPLETENESS_RATIFICATION != "INSUFFICIENT_NOT_KIND_SET_CLOSURE":
        raise NonEqEquityStockSourceKindOrCompletenessError("COMPLETENESS_RATIFICATION_DRIFT")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("MAPPING_MUST_REMAIN_INVALID")
    if MAPPING_PROVEN is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("MAPPING_PROVEN_NOT_FALSE")
    if SEMANTIC_MAPPING_PROVEN is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("SEMANTIC_MAPPING_NOT_FALSE")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("ALGEBRA_MUST_REMAIN_INCOMPLETE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if EQ_RECONCILIATION_TARGET_ONLY is not True:
        raise NonEqEquityStockSourceKindOrCompletenessError("EQ_MUST_REMAIN_RECONCILIATION_TARGET")
    if EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("EQ_TREATED_AS_SOURCE_NOT_FALSE")
    if D6_ACCOUNT_EQUITY_SOURCE_MAPPING_COVERAGE_STATUS != (
        "PARTIAL_FAIL_CLOSED_NO_RATIFIED_SOURCE_KIND"
    ):
        raise NonEqEquityStockSourceKindOrCompletenessError("MAPPING_COVERAGE_DRIFT")
    if ACCOUNT_EQUITY_SOURCE_MAPPING_DENIED_THIS_WORKPACKAGE is not True:
        raise NonEqEquityStockSourceKindOrCompletenessError("MAPPING_DENY_PIN_DRIFT")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("COMPLETE_STREAM_MUST_REMAIN_UNPROVEN")
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("EVENT_GET_NOT_AUTHORIZED")
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("OBSERVATION_GET_NOT_AUTHORIZED")
    if MS2_AUTHORIZED is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise NonEqEquityStockSourceKindOrCompletenessError("C17_CREATED_NOT_FALSE")
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise NonEqEquityStockSourceKindOrCompletenessError("BILLS_CANONICALIZED_FORBIDDEN")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise NonEqEquityStockSourceKindOrCompletenessError("DAG_PIN_DRIFT")


def _assert_parent_co_pack(*, sealed_co_pack: Path) -> None:
    if not sealed_co_pack.is_dir():
        raise NonEqEquityStockSourceKindOrCompletenessError("PARENT_CO_PACK_MISSING")
    claims = _load_json_object(path=sealed_co_pack / CLAIMS_FILE)
    _require_token(field="U04_LEGACY_STATUS", payload=claims, expected=STATE_UNRESOLVED)
    _require_token(
        field="U04_EQUITY_STOCK_ROLE", payload=claims, expected=DISPOSITION_NOT_EQUITY_STOCK
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
        expected="NO_RATIFIED_EQUITY_STOCK_SOURCE_KIND",
    )
    if verify_manifest_sha256_v1(store_root=sealed_co_pack) != 0:
        raise NonEqEquityStockSourceKindOrCompletenessError("PARENT_CO_MANIFEST_INVALID")


def classify_non_eq_source_kind_candidates_v1() -> dict[str, Any]:
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=DISPOSITION_NOT_EQUITY_STOCK)
    reject_eq_as_source_authority_v1(claimed=FALSE_TOKEN)
    reject_today_as_account_equity_source_kind_v1(claimed=STATUS_NOT_RATIFIABLE_LIVE_TODAY)
    reject_kind_set_uplift_v1(claimed=FALSE_TOKEN)
    rows: list[dict[str, str]] = []
    for finding in build_forensic_event_kind_census_findings_v1():
        reason = _DISPOSITION_REASON.get(finding.disposition)
        if reason is None:
            raise NonEqEquityStockSourceKindOrCompletenessError(
                f"CENSUS_DISPOSITION_UNMAPPED:{finding.candidate_id}:{finding.disposition}"
            )
        if reason == STATUS_RATIFIED_SOURCE_KIND:
            raise NonEqEquityStockSourceKindOrCompletenessError(
                f"CENSUS_CANNOT_MINT_SOURCE_KIND:{finding.candidate_id}"
            )
        rows.append(
            {
                "layer": finding.layer,
                "candidate_id": finding.candidate_id,
                "equity_stock_affecting_status": finding.equity_stock_affecting_status,
                "disposition": finding.disposition,
                "ratification_status": reason,
                "boundary": "ACCOUNT_EQUITY_RECONSTRUCTION",
            }
        )
    rows.append(
        {
            "layer": "CANONICAL_AUTHORITY",
            "candidate_id": "eq",
            "equity_stock_affecting_status": "RECONCILIATION_TARGET_NOT_SOURCE",
            "disposition": STATUS_RATIFIED_NON_SOURCE,
            "ratification_status": STATUS_NOT_RATIFIABLE_EQ_TARGET,
            "boundary": "ACCOUNT_EQUITY_RECONSTRUCTION",
        }
    )
    rows.append(
        {
            "layer": "HISTORICAL_INTERMEDIATE",
            "candidate_id": TODAY_SOURCE_KIND,
            "equity_stock_affecting_status": "LIVE_EQUITY_STOCK_INITIAL_STOCK_NOT_D6_SOURCE",
            "disposition": STATUS_NOT_RATIFIABLE_LIVE_TODAY,
            "ratification_status": STATUS_NOT_RATIFIABLE_LIVE_TODAY,
            "boundary": "LIVE_EQUITY_STOCK_KIND_SET_NOT_ACCOUNT_EQUITY_SOURCE",
        }
    )
    if any(row["ratification_status"] == STATUS_RATIFIED_SOURCE_KIND for row in rows):
        raise NonEqEquityStockSourceKindOrCompletenessError(
            "RATIFIED_SOURCE_KIND_MUST_REMAIN_EMPTY"
        )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "non_eq_equity_stock_source_kind_status": NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
        "ratified_source_kinds": NONE_TOKEN,
        "candidate_count": str(len(rows)),
        "candidates": rows,
        "source_kind_proof_law": SOURCE_KIND_PROOF_LAW,
        "source_kind_evidence": SOURCE_KIND_EVIDENCE,
        "eq_role": "EQ_RECONCILIATION_TARGET_ONLY",
        "u04_equity_stock_role": DISPOSITION_NOT_EQUITY_STOCK,
        "today_source_kind_status": STATUS_NOT_RATIFIABLE_LIVE_TODAY,
        "synthetic_witness_used": FALSE_TOKEN,
        "durable_unknown_reopened": FALSE_TOKEN,
        "kind_set_uplift": FALSE_TOKEN,
    }


def classify_source_kind_completeness_v1(*, source: Mapping[str, Any]) -> dict[str, str]:
    if source["ratified_source_kinds"] != NONE_TOKEN:
        raise NonEqEquityStockSourceKindOrCompletenessError(
            "RATIFIED_SOURCE_KINDS_MUST_REMAIN_NONE"
        )
    reject_empty_productive_remaining_as_completeness_v1(claimed=SOURCE_KIND_COMPLETENESS_STATUS)
    reject_single_kind_as_completeness_v1(claimed=SOURCE_KIND_COMPLETENESS_STATUS)
    reject_kind_set_resolved_while_remaining_unknown_v1(claimed=FALSE_TOKEN)
    reject_durable_unknown_as_include_or_exclude_v1(claimed="DURABLE_UNKNOWN")
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "source_kind_completeness_status": SOURCE_KIND_COMPLETENESS_STATUS,
        "source_kind_completeness_ratification": SOURCE_KIND_COMPLETENESS_RATIFICATION,
        "completeness_proof_law": COMPLETENESS_PROOF_LAW,
        "completeness_evidence": COMPLETENESS_EVIDENCE,
        "empty_productive_remaining_is_not_completeness": TRUE_TOKEN,
        "named_remaining_unknown_blocks_completeness": TRUE_TOKEN,
        "single_kind_would_not_prove_completeness": TRUE_TOKEN,
        "kind_set_resolved": FALSE_TOKEN,
        "kind_set": KIND_SET_EMPTY,
    }


def reevaluate_downstream_v1(
    *,
    source: Mapping[str, Any],
    completeness: Mapping[str, str],
) -> dict[str, Any]:
    if source["non_eq_equity_stock_source_kind_status"] != NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS:
        raise NonEqEquityStockSourceKindOrCompletenessError("SOURCE_KIND_STATUS_MUST_REMAIN_NONE")
    if completeness["source_kind_completeness_status"] != SOURCE_KIND_COMPLETENESS_STATUS:
        raise NonEqEquityStockSourceKindOrCompletenessError("COMPLETENESS_MUST_REMAIN_INSUFFICIENT")
    if completeness["kind_set_resolved"] != FALSE_TOKEN:
        raise NonEqEquityStockSourceKindOrCompletenessError("KIND_SET_RESOLVED_MUST_REMAIN_FALSE")
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
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "account_equity_source_mapping_status": DAG_PIN,
        "reconstruction_algebra_complete": FALSE_TOKEN,
        "reconstruction_status": (
            "INCOMPLETE_NO_RATIFIED_NON_EQ_SOURCE_KIND_COMPLETENESS_INSUFFICIENT_"
            "U04_SIZING_INCLUSION_UNRESOLVED_U05_U06_NOT_CURRENT_PRODUCTIVE_TERMS"
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


def execute_non_eq_equity_stock_source_kind_or_completeness_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_co_pack: Path | str | None = None,
    persist_as_of: str | None = None,
) -> NonEqEquityStockSourceKindOrCompletenessResultV1:
    if owner_go != OWNER_GO:
        raise NonEqEquityStockSourceKindOrCompletenessError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise NonEqEquityStockSourceKindOrCompletenessError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=DISPOSITION_NOT_EQUITY_STOCK)
    reject_eq_as_source_authority_v1(claimed=FALSE_TOKEN)
    reject_today_as_account_equity_source_kind_v1(claimed=STATUS_NOT_RATIFIABLE_LIVE_TODAY)
    reject_kind_set_uplift_v1(claimed=FALSE_TOKEN)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    co_pack = (
        Path(sealed_co_pack) if sealed_co_pack is not None else repo / CANONICAL_CO_PACK_RELPATH
    )
    _assert_parent_co_pack(sealed_co_pack=co_pack)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise NonEqEquityStockSourceKindOrCompletenessError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    source = classify_non_eq_source_kind_candidates_v1()
    completeness = classify_source_kind_completeness_v1(source=source)
    downstream = reevaluate_downstream_v1(source=source, completeness=completeness)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": (
            "SATISFIED_BY_EXPLICIT_INSUFFICIENCY_RATIFICATION_NO_KIND_NO_KIND_SET_"
            "UPLIFT_EQ_NOT_SOURCE"
        ),
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CO_PACK": CANONICAL_CO_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "START_BLOCK": DAG_PIN,
        "NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS": NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
        "RATIFIED_SOURCE_KINDS": NONE_TOKEN,
        "SOURCE_KIND_PROOF_LAW": SOURCE_KIND_PROOF_LAW,
        "SOURCE_KIND_EVIDENCE": SOURCE_KIND_EVIDENCE,
        "SOURCE_KIND_COMPLETENESS_STATUS": SOURCE_KIND_COMPLETENESS_STATUS,
        "SOURCE_KIND_COMPLETENESS_RATIFICATION": SOURCE_KIND_COMPLETENESS_RATIFICATION,
        "COMPLETENESS_PROOF_LAW": COMPLETENESS_PROOF_LAW,
        "COMPLETENESS_EVIDENCE": COMPLETENESS_EVIDENCE,
        "EMPTY_PRODUCTIVE_REMAINING_IS_NOT_COMPLETENESS": TRUE_TOKEN,
        "SINGLE_KIND_WOULD_NOT_PROVE_COMPLETENESS": TRUE_TOKEN,
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
        "TODAY_SOURCE_KIND_STATUS": STATUS_NOT_RATIFIABLE_LIVE_TODAY,
        "AUTHORITY_CHANGE": (
            "ADDITIVE_INSUFFICIENCY_RATIFICATION_NO_KIND_NO_KIND_SET_UPLIFT_EQ_NOT_SOURCE"
        ),
        "MIGRATION_STRATEGY": (
            "ADDITIVE_VERSIONED_INSUFFICIENCY_LEGACY_UNKNOWN_PRESERVED_NO_KIND_SET_UPLIFT"
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
        "parent_co_pack": CANONICAL_CO_PACK_RELPATH,
        "historical_artifacts_rewritten": FALSE_TOKEN,
        "synthetic_witness_used": FALSE_TOKEN,
        "hope_get_used": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "include_or_exclude_normalized": FALSE_TOKEN,
        "today_imported_as_account_equity_source_kind": FALSE_TOKEN,
        "kind_set_resolved": FALSE_TOKEN,
        "mapping_ratified": FALSE_TOKEN,
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
        "FORENSIC_RAW_EVIDENCE": "NONE_NEW_RAW_BYTES_SEALED_AV_BE_AX_CI_CO_CONSUMED",
        "ADJUDICATED_CONCLUSION": (
            "qualification_v1.json,completeness_v1.json,downstream_dependency_tree_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
        "MIGRATION_RATIFICATION": "claims.json",
        "CURRENT_PRODUCTIVE_MAPPING_STATUS": DAG_PIN,
    }
    census_payload = {
        "layer": "FORENSIC_RAW",
        "candidate_count": source["candidate_count"],
        "candidates": source["candidates"],
        "ratified_source_kinds": NONE_TOKEN,
        "non_eq_equity_stock_source_kind_status": NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "qualification_v1.json", payload=source)
    _persist_json(path=store / "completeness_v1.json", payload=completeness)
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
        raise NonEqEquityStockSourceKindOrCompletenessError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise NonEqEquityStockSourceKindOrCompletenessError("MANIFEST_VERIFY_NOT_ZERO")
    return NonEqEquityStockSourceKindOrCompletenessResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        non_eq_equity_stock_source_kind_status=NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
        ratified_source_kinds=NONE_TOKEN,
        source_kind_completeness_status=SOURCE_KIND_COMPLETENESS_STATUS,
        kind_set_resolved=FALSE_TOKEN,
        canonically_valid_account_equity_source_mapping=FALSE_TOKEN,
        account_equity_source_mapping_status=DAG_PIN,
        reconciliation_target_status="EQ_RECONCILIATION_TARGET_ONLY",
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
    "COMPLETENESS_EVIDENCE",
    "COMPLETENESS_PROOF_LAW",
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "NonEqEquityStockSourceKindOrCompletenessError",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "SOURCE_KIND_EVIDENCE",
    "SOURCE_KIND_PROOF_LAW",
    "STATUS_NOT_RATIFIABLE_EQ_TARGET",
    "STATUS_NOT_RATIFIABLE_LIVE_TODAY",
    "classify_non_eq_source_kind_candidates_v1",
    "classify_source_kind_completeness_v1",
    "execute_non_eq_equity_stock_source_kind_or_completeness_v1",
    "reject_empty_productive_remaining_as_completeness_v1",
    "reject_kind_set_uplift_v1",
    "reject_single_kind_as_completeness_v1",
    "reject_today_as_account_equity_source_kind_v1",
)
