"""Classify remaining necessary kinds from sealed evidence only.

Consumes the workpackage Owner-GO. Satisfies the CJ-named INCLUDE/EXCLUDE
or new-evidence GO. Builds an explicit U04/U05/U06/residual decision
matrix. Reuses sealed packs. Does not GET. Does not POST. Does not
Hope-GET. Does not resolve secrets. Does not INCLUDE or EXCLUDE from
plausibility, empty response, NONE_BINDABLE, GET_COUNT=0, account mode,
or another unknown. DURABLE_UNKNOWN is not INCLUDE or EXCLUDE and may
reopen only on genuinely new discriminating evidence. AUTHORITY_EFFECT=NONE.

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
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    CLASS_RESIDUAL,
    CLASS_U05,
    CLASS_U06,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
    TARGET_RESIDUAL,
    TARGET_U05,
    TARGET_U06,
    evaluate_current_absent_proofs_v1,
    evaluate_residual_primary_proof_v1,
    evaluate_u05_primary_proof_v1,
    evaluate_u06_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_NOT_EQUITY_STOCK,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_CLOSEOUT_STATUS,
    KIND_SET_EVIDENCE_PERSIST_STATUS,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    SEMANTIC_MAPPING_PROVEN,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_necessary_kind_set_closeout_contract_v1 import (
    FORBIDDEN_RECLASSIFY_IDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.kind_set_and_account_equity_source_mapping_architecture_ratification_v1 import (
    BLOCKER_ID as PARENT_BLOCKER_ID,
    CANONICAL_PACK_RELPATH as CANONICAL_CJ_PACK_RELPATH,
    COMPLETE_REQUIRES,
    NEXT_OWNER_GO as PIN_OWNER_GO,
    RATIFIED_MAPPING_ARCHITECTURE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
    UNRESOLVED_ALGEBRA_TERMS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CI_PACK_RELPATH,
    reject_durable_unknown_as_include_or_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

OWNER_GO = "OWNER_GO_REMAINING_NECESSARY_KIND_EVIDENCE_CLASSIFICATION_TO_NEXT_DEFINITIVE_BLOCK_V1"
EXPECTED_ORIGIN_MAIN_SHA = "de1d9ff99c45d4ce8e4d8c8ef60ff367896a6516"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_remaining_necessary_kind_evidence_classification_v1/2026-09-15T070000Z"
)
CANONICAL_CD_PACK_RELPATH = (
    "evidence/ops/full_core_u05_primary_proof_bound_interest_accrued_get_acquisition_v1/"
    "2026-09-15T010500Z"
)
CANONICAL_CE_PACK_RELPATH = (
    "evidence/ops/full_core_u05_durable_unknown_embedding_identity_pin_v1/2026-09-15T014000Z"
)
CANONICAL_CF_PACK_RELPATH = (
    "evidence/ops/full_core_u06_paired_fee_event_and_once_only_equity_stock_effect_"
    "primary_proof_surface_binding_v1/2026-09-15T021000Z"
)
CANONICAL_CG_PACK_RELPATH = (
    "evidence/ops/full_core_u06_equity_stock_placement_identity_durable_unknown_pin_v1/"
    "2026-09-15T030000Z"
)
CANONICAL_CH_PACK_RELPATH = (
    "evidence/ops/full_core_residual_positive_necessary_kind_exhaustiveness_"
    "primary_proof_v1/2026-09-15T040000Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-15T07:00:00Z"
SCHEMA_CLASS = "REMAINING_NECESSARY_KIND_EVIDENCE_CLASSIFICATION_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
DURABLE_UNKNOWN_TOKEN = "DURABLE_UNKNOWN"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
STATE_UNRESOLVED = "UNRESOLVED"
U04_CANDIDATE_ID = "U04_PENDING_ORDER_RESERVATION"
U04_PROPOSITION = (
    "WHETHER_U04_PENDING_ORDER_RESERVATION_IS_A_NECESSARY_EQUITY_STOCK_KIND_"
    "INCLUDE_OR_EXCLUDE_AND_WHETHER_ALGEBRA_INCLUSION_IS_IN_BASE_OR_NOT_IN_BASE"
)
U05_PROPOSITION = "WHETHER_U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND_IS_INCLUDE_OR_EXCLUDE"
U06_PROPOSITION = "WHETHER_U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND_IS_INCLUDE_OR_EXCLUDE"
RESIDUAL_PROPOSITION = (
    "WHETHER_RESIDUAL_UNNAMED_NECESSARY_EQUITY_STOCK_EVENT_CLASS_IS_EXCLUDE_"
    "BY_POSITIVE_EXHAUSTIVENESS_CERTIFICATE"
)
U04_KIND_SET_DISPOSITION = DISPOSITION_NOT_EQUITY_STOCK
U04_CLASSIFICATION = (
    "UNRESOLVED_ALGEBRA_INCLUSION_KIND_SET_DISPOSITION_NOT_EQUITY_STOCK_NOT_INCLUDE_NOT_EXCLUDE"
)
U05_CLASSIFICATION = "REMAIN_UNKNOWN_DURABLE_UNKNOWN"
U06_CLASSIFICATION = "REMAIN_UNKNOWN_DURABLE_UNKNOWN"
RESIDUAL_CLASSIFICATION = "REMAIN_UNKNOWN_DURABLE_UNKNOWN"
DECISION_MATRIX_RESULT = "NO_INCLUDE_OR_EXCLUDE_PROVEN_ALL_FOUR_ROWS"
CANDIDATE_U04_SURFACE = "GET_/api/v5/trade/orders-pending"
CANDIDATE_U05_SURFACE = "GET_/api/v5/account/interest-accrued"
CANDIDATE_U06_SURFACE = NONE_TOKEN
CANDIDATE_RESIDUAL_SURFACE = "INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_CERTIFICATE_NOT_GET"
MISSING_U04_GET_PREDICATES = (
    "EXACT_FULL_CORE_U04_DISCRIMINATOR_ENDPOINT_NOT_BOUND;"
    "RESULT_CANNOT_DISCRIMINATE_IN_BASE_VS_NOT_IN_BASE;"
    "EMPTY_PENDING_ROWS_ARE_NOT_EXCLUDE;"
    "HISTORICAL_11_14_ORDERS_PENDING_IS_DIFFERENT_AUTHORITY_NOT_UPLIFTABLE;"
    "DUPLICATE_ACQUISITION_FORBIDDEN"
)
MISSING_U05_GET_PREDICATES = (
    "CD_ONE_SHOT_ALREADY_CONSUMED;"
    "GET_ALONE_MAY_INCLUDE_FALSE;"
    "GET_ALONE_MAY_EXCLUDE_FALSE;"
    "EMPTY_DATA_IS_NOT_ABSENCE;"
    "EMBEDDING_WITNESS_UNBOUND;"
    "DURABLE_UNKNOWN_REOPEN_REQUIRES_NEW_DISCRIMINATING_EVIDENCE;"
    "DUPLICATE_ACQUISITION_FORBIDDEN"
)
MISSING_U06_GET_PREDICATES = (
    "EXACT_ENDPOINT_NOT_BOUND;"
    "CONCRETE_SURFACE_SELECTION_STATUS_NONE_BINDABLE;"
    "NONE_BINDABLE_IS_NOT_EXCLUDE;"
    "GET_COUNT_0_IS_PROVENANCE_NOT_ABSENCE;"
    "FURTHER_U06_PLACEMENT_ACQUISITION_STOPPED"
)
MISSING_RESIDUAL_GET_PREDICATES = (
    "EXACT_CERTIFICATE_SURFACE_NOT_BOUND;"
    "CONCRETE_SURFACE_SELECTION_STATUS_NONE_BINDABLE;"
    "NONE_BINDABLE_IS_NOT_EXCLUDE;"
    "RESIDUAL_IS_NOT_AN_INCLUDE_KIND;"
    "FURTHER_RESIDUAL_EXHAUSTIVENESS_ACQUISITION_STOPPED"
)
EXACT_MISSING_PREDICATE = (
    "NO_CURRENTLY_AUTHORIZED_DISCRIMINATING_SURFACE_CAN_PROVE_INCLUDE_OR_EXCLUDE_"
    "FOR_U05_U06_RESIDUAL_U05_MISSING_INDEPENDENT_NON_ALGEBRAIC_EMBEDDING_WITNESS_"
    "NOT_VENUE_EQ_U06_MISSING_BINDABLE_PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_"
    "EFFECT_SURFACE_RESIDUAL_MISSING_INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_"
    "CERTIFICATE_U04_ALGEBRA_IN_BASE_VS_NOT_IN_BASE_UNPROVEN_KIND_SET_CANNOT_"
    "RESOLVE_MAPPING_CANNOT_BECOME_CANONICALLY_VALID"
)
BLOCKER_ID = (
    "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_AFTER_SEALED_EVIDENCE_"
    "CLASSIFICATION_NO_INCLUDE_OR_EXCLUDE_PROVEN_NO_BINDABLE_DISCRIMINATING_GET"
)
ARCHITECTURE_BLOCKER = (
    "SEALED_EVIDENCE_AND_BJ_QUALIFICATION_LAW_YIELD_NONQUALIFYING_NOT_INCLUDE_"
    "NOT_EXCLUDE_DURABLE_UNKNOWN_MAY_NOT_REOPEN_WITHOUT_NEW_DISCRIMINATING_"
    "EVIDENCE_GET_PREDICATES_UNSATISFIED"
)
NEXT_PRODUCTIVE_NODE = (
    "NEW_DISCRIMINATING_EVIDENCE_SURFACE_FOR_NAMED_REMAINING_UNKNOWN_NECESSARY_KINDS"
)
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_OR_AUTHORIZE_A_NEW_DISCRIMINATING_EVIDENCE_"
    "SURFACE_NOT_ALREADY_ADJUDICATED_NONE_BINDABLE_OR_GET_ALONE_NONQUALIFYING_"
    "FOR_U05_EMBEDDING_WITNESS_AND_OR_U06_PAIRED_FEE_AND_OR_RESIDUAL_"
    "EXHAUSTIVENESS_CERTIFICATE_V1"
)
NEXT_ACTION = (
    "STOP_FIRST_DEFINITIVE_BLOCK_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_"
    "MAPPING_NO_INCLUDE_OR_EXCLUDE_PROVEN_NO_GET"
)
CLAIMS_FILE = "claims.json"
SECRET_MARKERS: tuple[str, ...] = (
    "ok-access",
    "api_secret",
    "api-secret",
    "passphrase",
    "secretref://",
)
_FORBIDDEN_CLASSIFICATION_TOKENS = frozenset(
    {
        OUTCOME_INCLUDE,
        OUTCOME_EXCLUDE,
        "INCLUDE",
        "EXCLUDE",
        "true",
        "TRUE",
        "ABSENT",
        "absent",
        "0",
        "zero",
        "NONE",
        "N/A",
        "NOT_APPLICABLE",
        "NO_RESIDUAL",
        "KIND_SET_RESOLVED_TRUE",
        "CANONICALLY_VALID",
    }
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class RemainingNecessaryKindEvidenceClassificationError(ValueError):
    """Fail-closed remaining-necessary-kind classification violation."""


@dataclass(frozen=True)
class RemainingNecessaryKindEvidenceClassificationResultV1:
    genesis_id: str
    persist_as_of: str
    store_root: str
    u04_classification: str
    u05_classification: str
    u06_classification: str
    residual_classification: str
    decision_matrix_result: str
    kind_set: str
    kind_set_resolved: str
    canonically_valid_account_equity_source_mapping: str
    first_definitive_block: str
    exact_missing_predicate: str
    reconstruction_status: str
    equity_stock_readiness: str
    risk_sizing_readiness: str
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
        raise RemainingNecessaryKindEvidenceClassificationError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _require_token(*, field: str, payload: Mapping[str, Any], expected: str) -> None:
    actual = str(payload.get(field) or "")
    if actual != expected:
        raise RemainingNecessaryKindEvidenceClassificationError(f"{field}_DRIFT:{actual}")


def reject_empty_none_bindable_or_get_count_zero_as_classification_v1(*, claimed: str) -> None:
    if claimed in _FORBIDDEN_CLASSIFICATION_TOKENS:
        raise RemainingNecessaryKindEvidenceClassificationError(
            f"EMPTY_NONE_BINDABLE_GET_COUNT_ZERO_IS_NOT_INCLUDE_OR_EXCLUDE:{claimed}"
        )


def reject_durable_unknown_reopen_without_new_evidence_v1(*, claimed_new_evidence: str) -> None:
    if claimed_new_evidence in {TRUE_TOKEN, "true", OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
        raise RemainingNecessaryKindEvidenceClassificationError(
            f"DURABLE_UNKNOWN_REOPEN_REQUIRES_NEW_DISCRIMINATING_EVIDENCE:{claimed_new_evidence}"
        )


def reject_kind_set_resolved_while_remaining_unknown_v1(*, claimed: str) -> None:
    if claimed in {"true", "TRUE", "RESOLVED", "KIND_SET_RESOLVED_TRUE"}:
        raise RemainingNecessaryKindEvidenceClassificationError(
            f"KIND_SET_CANNOT_RESOLVE_WHILE_REMAINING_UNKNOWN:{claimed}"
        )


def reject_u04_reclassify_as_equity_stock_kind_v1(*, claimed: str) -> None:
    if U04_CANDIDATE_ID in FORBIDDEN_RECLASSIFY_IDS and claimed in {
        OUTCOME_INCLUDE,
        "INCLUDE",
        DECISION_REMAIN_UNKNOWN,
        "UNKNOWN",
    }:
        raise RemainingNecessaryKindEvidenceClassificationError(
            f"U04_RECLASSIFY_AS_EQUITY_STOCK_KIND_FORBIDDEN:{claimed}"
        )


def _assert_standing_pins() -> None:
    if LIVE_ARMED is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("LIVE_ARMED_NOT_FALSE")
    if WIRE_SEND_PERMITTED is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("WIRE_SEND_PERMITTED_NOT_FALSE")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise RemainingNecessaryKindEvidenceClassificationError("U05_UNKNOWN_PRESERVED")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise RemainingNecessaryKindEvidenceClassificationError("U06_UNKNOWN_PRESERVED")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise RemainingNecessaryKindEvidenceClassificationError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise RemainingNecessaryKindEvidenceClassificationError("KIND_SET_MUST_REMAIN_EMPTY")
    if CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is not False:
        raise RemainingNecessaryKindEvidenceClassificationError(
            "MAPPING_MUST_REMAIN_NOT_CANONICALLY_VALID"
        )
    if MAPPING_PROVEN is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("MAPPING_PROVEN_NOT_FALSE")
    if SEMANTIC_MAPPING_PROVEN is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("SEMANTIC_MAPPING_PROVEN_NOT_FALSE")
    if RECONSTRUCTION_ALGEBRA_COMPLETE is not False:
        raise RemainingNecessaryKindEvidenceClassificationError(
            "RECONSTRUCTION_ALGEBRA_MUST_REMAIN_INCOMPLETE"
        )
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise RemainingNecessaryKindEvidenceClassificationError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise RemainingNecessaryKindEvidenceClassificationError(
            "EVENT_ACQUISITION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise RemainingNecessaryKindEvidenceClassificationError(
            "OBSERVATION_NETWORK_GET_MUST_REMAIN_UNAUTHORIZED"
        )
    if MS2_AUTHORIZED is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise RemainingNecessaryKindEvidenceClassificationError("RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE")
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise RemainingNecessaryKindEvidenceClassificationError(
            "ACCOUNT_BILLS_MUST_REMAIN_NONCANONICAL"
        )
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise RemainingNecessaryKindEvidenceClassificationError("DAG_PIN_DRIFT")
    if EARLIEST_UNRESOLVED_ALGEBRA_TERM != "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED":
        raise RemainingNecessaryKindEvidenceClassificationError("EARLIEST_ALGEBRA_TERM_DRIFT")
    if NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES != (
        TARGET_U05,
        TARGET_U06,
        TARGET_RESIDUAL,
    ):
        raise RemainingNecessaryKindEvidenceClassificationError(
            "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES_DRIFT"
        )


def _assert_sealed_pack(*, pack: Path, schema_class: str, field: str, expected: str) -> None:
    if verify_manifest_sha256_v1(store_root=pack) != 0:
        raise RemainingNecessaryKindEvidenceClassificationError(
            f"SEALED_MANIFEST_VERIFY_NOT_ZERO:{pack.name}"
        )
    claims = _load_json_object(path=pack / CLAIMS_FILE)
    _require_token(field="SCHEMA_CLASS", payload=claims, expected=schema_class)
    _require_token(field=field, payload=claims, expected=expected)


def _assert_parent_cj_pack(*, sealed_cj_pack: Path) -> None:
    if verify_manifest_sha256_v1(store_root=sealed_cj_pack) != 0:
        raise RemainingNecessaryKindEvidenceClassificationError(
            "PARENT_CJ_MANIFEST_VERIFY_NOT_ZERO"
        )
    claims = _load_json_object(path=sealed_cj_pack / CLAIMS_FILE)
    _require_token(
        field="SCHEMA_CLASS",
        payload=claims,
        expected="KIND_SET_AND_ACCOUNT_EQUITY_SOURCE_MAPPING_ARCHITECTURE_RATIFICATION_V1",
    )
    _require_token(field="NEXT_OWNER_GO_REQUIRED", payload=claims, expected=PIN_OWNER_GO)
    _require_token(field="KIND_SET", payload=claims, expected=KIND_SET_EMPTY)
    _require_token(field="KIND_SET_RESOLVED", payload=claims, expected=FALSE_TOKEN)
    _require_token(
        field="CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING",
        payload=claims,
        expected=FALSE_TOKEN,
    )
    _require_token(field="U04_STATUS", payload=claims, expected=STATE_UNRESOLVED)
    _require_token(field="U05_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U06_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="RESIDUAL_STATUS", payload=claims, expected=DECISION_REMAIN_UNKNOWN)
    _require_token(field="U05_EMBEDDING_IDENTITY", payload=claims, expected=DURABLE_UNKNOWN_TOKEN)
    _require_token(field="U06_PLACEMENT_IDENTITY", payload=claims, expected=DURABLE_UNKNOWN_TOKEN)
    _require_token(
        field="RESIDUAL_EXHAUSTIVENESS_IDENTITY",
        payload=claims,
        expected=DURABLE_UNKNOWN_TOKEN,
    )
    _require_token(field="ACTUAL_GET_COUNT", payload=claims, expected="0")
    _require_token(field="POST_COUNT", payload=claims, expected="0")


def _assert_reused_sealed_evidence(*, repo: Path) -> None:
    _assert_sealed_pack(
        pack=repo / CANONICAL_CD_PACK_RELPATH,
        schema_class="U05_PRIMARY_PROOF_BOUND_INTEREST_ACCRUED_GET_ACQUISITION_V1",
        field="U05_DECISION_AFTER",
        expected=DECISION_REMAIN_UNKNOWN,
    )
    _assert_sealed_pack(
        pack=repo / CANONICAL_CE_PACK_RELPATH,
        schema_class="U05_DURABLE_UNKNOWN_EMBEDDING_IDENTITY_PIN_V1",
        field="NON_ALGEBRAIC_EMBEDDING_IDENTITY",
        expected=DURABLE_UNKNOWN_TOKEN,
    )
    _assert_sealed_pack(
        pack=repo / CANONICAL_CF_PACK_RELPATH,
        schema_class=(
            "U06_PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_EFFECT_PRIMARY_PROOF_SURFACE_BINDING_V1"
        ),
        field="CONCRETE_SURFACE_SELECTION_STATUS",
        expected="NONE_BINDABLE",
    )
    _assert_sealed_pack(
        pack=repo / CANONICAL_CG_PACK_RELPATH,
        schema_class="U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN_V1",
        field="PLACEMENT_IDENTITY_STATUS",
        expected=DURABLE_UNKNOWN_TOKEN,
    )
    _assert_sealed_pack(
        pack=repo / CANONICAL_CH_PACK_RELPATH,
        schema_class="RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF_V1",
        field="CONCRETE_SURFACE_SELECTION_STATUS",
        expected="NONE_BINDABLE",
    )
    _assert_sealed_pack(
        pack=repo / CANONICAL_CI_PACK_RELPATH,
        schema_class="RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN_V1",
        field="EXHAUSTIVENESS_IDENTITY_STATUS",
        expected=DURABLE_UNKNOWN_TOKEN,
    )


def evaluate_read_only_get_predicates_v1() -> dict[str, Any]:
    rows = (
        {
            "unknown_id": "U04",
            "candidate_surface": CANDIDATE_U04_SURFACE,
            "exact_endpoint_canonically_bound": FALSE_TOKEN,
            "get_covered_by_current_owner_standing_read_only_authority": FALSE_TOKEN,
            "no_post_write_side_effect": TRUE_TOKEN,
            "query_account_instrument_scope_bounded": FALSE_TOKEN,
            "result_can_discriminate_named_include_vs_exclude": FALSE_TOKEN,
            "retry_policy_explicitly_bounded": FALSE_TOKEN,
            "secrets_consumed_only_through_already_authorized_mechanism": TRUE_TOKEN,
            "all_predicates_proven": FALSE_TOKEN,
            "get_authorized": FALSE_TOKEN,
            "missing_predicates": MISSING_U04_GET_PREDICATES,
        },
        {
            "unknown_id": "U05",
            "candidate_surface": CANDIDATE_U05_SURFACE,
            "exact_endpoint_canonically_bound": TRUE_TOKEN,
            "get_covered_by_current_owner_standing_read_only_authority": FALSE_TOKEN,
            "no_post_write_side_effect": TRUE_TOKEN,
            "query_account_instrument_scope_bounded": TRUE_TOKEN,
            "result_can_discriminate_named_include_vs_exclude": FALSE_TOKEN,
            "retry_policy_explicitly_bounded": TRUE_TOKEN,
            "secrets_consumed_only_through_already_authorized_mechanism": TRUE_TOKEN,
            "all_predicates_proven": FALSE_TOKEN,
            "get_authorized": FALSE_TOKEN,
            "missing_predicates": MISSING_U05_GET_PREDICATES,
        },
        {
            "unknown_id": "U06",
            "candidate_surface": CANDIDATE_U06_SURFACE,
            "exact_endpoint_canonically_bound": FALSE_TOKEN,
            "get_covered_by_current_owner_standing_read_only_authority": FALSE_TOKEN,
            "no_post_write_side_effect": TRUE_TOKEN,
            "query_account_instrument_scope_bounded": FALSE_TOKEN,
            "result_can_discriminate_named_include_vs_exclude": FALSE_TOKEN,
            "retry_policy_explicitly_bounded": FALSE_TOKEN,
            "secrets_consumed_only_through_already_authorized_mechanism": TRUE_TOKEN,
            "all_predicates_proven": FALSE_TOKEN,
            "get_authorized": FALSE_TOKEN,
            "missing_predicates": MISSING_U06_GET_PREDICATES,
        },
        {
            "unknown_id": "RESIDUAL",
            "candidate_surface": CANDIDATE_RESIDUAL_SURFACE,
            "exact_endpoint_canonically_bound": FALSE_TOKEN,
            "get_covered_by_current_owner_standing_read_only_authority": FALSE_TOKEN,
            "no_post_write_side_effect": TRUE_TOKEN,
            "query_account_instrument_scope_bounded": FALSE_TOKEN,
            "result_can_discriminate_named_include_vs_exclude": FALSE_TOKEN,
            "retry_policy_explicitly_bounded": FALSE_TOKEN,
            "secrets_consumed_only_through_already_authorized_mechanism": TRUE_TOKEN,
            "all_predicates_proven": FALSE_TOKEN,
            "get_authorized": FALSE_TOKEN,
            "missing_predicates": MISSING_RESIDUAL_GET_PREDICATES,
        },
    )
    if any(row["all_predicates_proven"] == TRUE_TOKEN for row in rows):
        raise RemainingNecessaryKindEvidenceClassificationError("GET_PREDICATE_FALSE_POSITIVE")
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "venue_get_count": "0",
        "venue_get_surfaces": NONE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "any_get_authorized": FALSE_TOKEN,
        "records": list(rows),
    }


def classify_unknowns_from_sealed_evidence_v1() -> dict[str, Any]:
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=U04_KIND_SET_DISPOSITION)
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DURABLE_UNKNOWN_TOKEN)
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    reject_empty_none_bindable_or_get_count_zero_as_classification_v1(
        claimed=DECISION_REMAIN_UNKNOWN
    )
    reject_durable_unknown_reopen_without_new_evidence_v1(claimed_new_evidence=FALSE_TOKEN)
    u05_empty, u06_empty, residual_empty = evaluate_current_absent_proofs_v1()
    u05_cd = evaluate_u05_primary_proof_v1(
        proof={
            "embedding_state": "UNKNOWN",
            "p01_overlap_state": "UNKNOWN",
            "independent_liability_event_proven": FALSE_TOKEN,
        }
    )
    u06_cf = evaluate_u06_primary_proof_v1(
        proof={
            "pairing_status": "UNRESOLVED",
            "base_or_event_or_reconciliation": "UNKNOWN",
        }
    )
    residual_ch = evaluate_residual_primary_proof_v1(proof={})
    for outcome in (u05_empty, u06_empty, residual_empty, u05_cd, u06_cf, residual_ch):
        if outcome.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
            raise RemainingNecessaryKindEvidenceClassificationError(
                f"SEALED_PROOF_MUST_REMAIN_NONQUALIFYING:{outcome.target_unknown}"
            )
        if outcome.outcome != OUTCOME_NONQUALIFYING:
            raise RemainingNecessaryKindEvidenceClassificationError(
                f"SEALED_PROOF_OUTCOME_DRIFT:{outcome.target_unknown}:{outcome.outcome}"
            )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "u04_kind_set_disposition": U04_KIND_SET_DISPOSITION,
        "u04_kind_set_disposition_source": "SEALED_AR_CLOSEOUT_REUSED_NOT_RECLASSIFIED",
        "u04_algebra_inclusion": STATE_UNRESOLVED,
        "u04_classification": U04_CLASSIFICATION,
        "u04_include_proven": FALSE_TOKEN,
        "u04_exclude_proven": FALSE_TOKEN,
        "u05_bj_empty_outcome": u05_empty.outcome,
        "u05_bj_cd_outcome": u05_cd.outcome,
        "u05_bj_cd_basis": u05_cd.basis,
        "u05_classification": U05_CLASSIFICATION,
        "u05_include_proven": FALSE_TOKEN,
        "u05_exclude_proven": FALSE_TOKEN,
        "u05_durable_unknown_reopened": FALSE_TOKEN,
        "u06_bj_empty_outcome": u06_empty.outcome,
        "u06_bj_cf_outcome": u06_cf.outcome,
        "u06_bj_cf_basis": u06_cf.basis,
        "u06_classification": U06_CLASSIFICATION,
        "u06_include_proven": FALSE_TOKEN,
        "u06_exclude_proven": FALSE_TOKEN,
        "u06_durable_unknown_reopened": FALSE_TOKEN,
        "residual_bj_empty_outcome": residual_empty.outcome,
        "residual_bj_ch_outcome": residual_ch.outcome,
        "residual_bj_ch_basis": residual_ch.basis,
        "residual_classification": RESIDUAL_CLASSIFICATION,
        "residual_include_proven": FALSE_TOKEN,
        "residual_exclude_proven": FALSE_TOKEN,
        "residual_durable_unknown_reopened": FALSE_TOKEN,
        "decision_matrix_result": DECISION_MATRIX_RESULT,
        "new_evidence_acquired": FALSE_TOKEN,
        "evidence_class_u05": CLASS_U05,
        "evidence_class_u06": CLASS_U06,
        "evidence_class_residual": CLASS_RESIDUAL,
    }


def build_decision_matrix_v1() -> dict[str, Any]:
    get_eval = evaluate_read_only_get_predicates_v1()
    by_id = {row["unknown_id"]: row for row in get_eval["records"]}
    rows = (
        {
            "unknown_id": "U04",
            "exact_unresolved_proposition": U04_PROPOSITION,
            "evidence_already_available": (
                "AR_CLOSEOUT_DISPOSITION_NOT_EQUITY_STOCK;"
                "CJ_U04_STATUS_UNRESOLVED;"
                "ALGEBRA_TERM_INCLUSION_UNRESOLVED;"
                "HISTORICAL_11_14_ORDERS_PENDING_EMPTY_NOT_UPLIFTABLE"
            ),
            "evidence_required_for_include": (
                "KIND_SET_INCLUDE_FORBIDDEN_U04_IS_FORBIDDEN_RECLASSIFY;"
                "ALGEBRA_INCLUDE_REQUIRES_POSITIVE_NOT_IN_BASE_RESERVATION_PROOF"
            ),
            "evidence_required_for_exclude": (
                "KIND_SET_EXCLUDE_OF_REMAINING_UNKNOWN_CLASS_NOT_APPLICABLE;"
                "ALGEBRA_EXCLUDE_REQUIRES_POSITIVE_IN_BASE_RESERVATION_PROOF"
            ),
            "existing_surface_can_discriminate": FALSE_TOKEN,
            "candidate_surface": by_id["U04"]["candidate_surface"],
            "acquisition_already_authorized": FALSE_TOKEN,
            "result_would_be_decision_capable": FALSE_TOKEN,
            "missing_acquisition_authority_or_evidence": by_id["U04"]["missing_predicates"],
            "classification": U04_CLASSIFICATION,
        },
        {
            "unknown_id": "U05",
            "exact_unresolved_proposition": U05_PROPOSITION,
            "evidence_already_available": (
                "CD_BOUND_INTEREST_ACCRUED_GET_EMPTY_DATA;"
                "GET_ALONE_MAY_INCLUDE_FALSE;"
                "GET_ALONE_MAY_EXCLUDE_FALSE;"
                "CE_EMBEDDING_IDENTITY_DURABLE_UNKNOWN;"
                "FURTHER_U05_EMBEDDING_WITNESS_ACQUISITION_STOPPED;"
                "BJ_QUALIFICATION_LAW"
            ),
            "evidence_required_for_include": (
                "POSITIVE_INDEPENDENT_LIABILITY_EVENT_AND_SEPARATE_NON_ALGEBRAIC_EMBEDDING"
            ),
            "evidence_required_for_exclude": (
                "POSITIVE_NON_ALGEBRAIC_EMBEDDING_IN_BASE_AND_U05_NOT_P01"
            ),
            "existing_surface_can_discriminate": FALSE_TOKEN,
            "candidate_surface": by_id["U05"]["candidate_surface"],
            "acquisition_already_authorized": FALSE_TOKEN,
            "result_would_be_decision_capable": FALSE_TOKEN,
            "missing_acquisition_authority_or_evidence": by_id["U05"]["missing_predicates"],
            "classification": U05_CLASSIFICATION,
        },
        {
            "unknown_id": "U06",
            "exact_unresolved_proposition": U06_PROPOSITION,
            "evidence_already_available": (
                "CF_NONE_BINDABLE;"
                "GET_COUNT_0;"
                "CG_PLACEMENT_IDENTITY_DURABLE_UNKNOWN;"
                "FURTHER_U06_PLACEMENT_ACQUISITION_STOPPED;"
                "BJ_QUALIFICATION_LAW"
            ),
            "evidence_required_for_include": (
                "POSITIVE_PAIRED_ONCE_ONLY_FEE_EVENT_SEPARATE_FROM_BASE"
            ),
            "evidence_required_for_exclude": (
                "POSITIVE_PAIRED_IN_BASE_FEE_COVERAGE_PROVES_U06_NOT_SEPARATE_KIND"
            ),
            "existing_surface_can_discriminate": FALSE_TOKEN,
            "candidate_surface": by_id["U06"]["candidate_surface"],
            "acquisition_already_authorized": FALSE_TOKEN,
            "result_would_be_decision_capable": FALSE_TOKEN,
            "missing_acquisition_authority_or_evidence": by_id["U06"]["missing_predicates"],
            "classification": U06_CLASSIFICATION,
        },
        {
            "unknown_id": "RESIDUAL",
            "exact_unresolved_proposition": RESIDUAL_PROPOSITION,
            "evidence_already_available": (
                "CH_NONE_BINDABLE;"
                "GET_COUNT_0;"
                "CI_EXHAUSTIVENESS_IDENTITY_DURABLE_UNKNOWN;"
                "FURTHER_RESIDUAL_EXHAUSTIVENESS_ACQUISITION_STOPPED;"
                "RESIDUAL_IS_NOT_AN_INCLUDE_KIND;"
                "BJ_QUALIFICATION_LAW"
            ),
            "evidence_required_for_include": "FORBIDDEN_RESIDUAL_IS_NOT_AN_INCLUDE_KIND",
            "evidence_required_for_exclude": (
                "POSITIVE_NECESSARY_KIND_INVENTORY_EXHAUSTIVENESS_CERTIFICATE"
            ),
            "existing_surface_can_discriminate": FALSE_TOKEN,
            "candidate_surface": by_id["RESIDUAL"]["candidate_surface"],
            "acquisition_already_authorized": FALSE_TOKEN,
            "result_would_be_decision_capable": FALSE_TOKEN,
            "missing_acquisition_authority_or_evidence": by_id["RESIDUAL"]["missing_predicates"],
            "classification": RESIDUAL_CLASSIFICATION,
        },
    )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "decision_matrix_result": DECISION_MATRIX_RESULT,
        "include_or_exclude_proven_count": "0",
        "records": list(rows),
    }


def reevaluate_kind_set_and_downstream_v1() -> dict[str, Any]:
    reject_kind_set_resolved_while_remaining_unknown_v1(claimed=FALSE_TOKEN)
    unresolved = ",".join(UNRESOLVED_ALGEBRA_TERMS)
    reconstruction_status = "INCOMPLETE_U04_U05_U06_UNRESOLVED_RESIDUAL_NOT_AN_ALGEBRA_TERM"
    equity_stock_readiness = "NOT_READY_KIND_SET_UNRESOLVED_AND_MAPPING_NOT_CANONICALLY_VALID"
    risk_sizing_readiness = (
        "NOT_READY_NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING_AND_"
        "29P_SEMANTIC_MAPPING_UNPROVEN"
    )
    kind_set_closure_provable = FALSE_TOKEN
    if kind_set_closure_provable == TRUE_TOKEN:
        raise RemainingNecessaryKindEvidenceClassificationError("KIND_SET_CLOSURE_FALSE_POSITIVE")
    records = (
        {
            "node_id": "DECISION_MATRIX",
            "classification": "CLOSED_THIS_SLICE",
            "status": DECISION_MATRIX_RESULT,
            "reason": "FOUR_ROWS_EVALUATED_NO_INCLUDE_OR_EXCLUDE",
        },
        {
            "node_id": "D6_KIND_SET",
            "classification": "REMAINS_EMPTY_FAIL_CLOSED",
            "status": KIND_SET_EMPTY,
            "reason": (
                "KIND_SET_CANNOT_RESOLVE_WHILE_U05_U06_RESIDUAL_REMAIN_UNKNOWN_"
                "DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE"
            ),
        },
        {
            "node_id": "ACCOUNT_EQUITY_SOURCE_MAPPING",
            "classification": "FIRST_DEFINITIVE_BLOCK",
            "status": DAG_PIN,
            "reason": ARCHITECTURE_BLOCKER,
        },
        {
            "node_id": "RECONSTRUCTION_ALGEBRA",
            "classification": "BLOCKED_BY_UNRESOLVED_TERMS",
            "status": "INCOMPLETE",
            "reason": (
                "EXISTING_UNRESOLVED_TERMS_U04_U05_U06_RESIDUAL_IS_NOT_AN_ALGEBRA_TERM_"
                "DURABLE_UNKNOWN_DOES_NOT_COMPLETE_ALGEBRA"
            ),
        },
        {
            "node_id": "EQUITY_STOCK_READINESS",
            "classification": "BLOCKED_BY_KIND_SET_AND_MAPPING",
            "status": "NOT_READY",
            "reason": "KIND_SET_UNRESOLVED_AND_MAPPING_NOT_CANONICALLY_VALID",
        },
        {
            "node_id": "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING",
            "classification": "BLOCKED_BY_MAPPING",
            "status": "UNBOUND",
            "reason": "29P_SOURCE_SEMANTIC_UNPROVEN",
        },
        {
            "node_id": "RISK_SIZING_READINESS",
            "classification": "BLOCKED_BY_MAPPING",
            "status": "NOT_READY",
            "reason": "29P_SEMANTIC_MAPPING_UNPROVEN_AND_NO_CANONICALLY_VALID_EQUITY_MAPPING",
        },
        {
            "node_id": "MS2",
            "classification": "BLOCKED_BY_KIND_SET",
            "status": "NOT_AUTHORIZED",
            "reason": "MS1_KIND_SET_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "D7",
            "classification": "BLOCKED_BY_D6",
            "status": "NOT_AUTHORIZED",
            "reason": "D6_NOT_FULLY_CLOSED",
        },
        {
            "node_id": "VENUE_GET",
            "classification": "FORBIDDEN_THIS_GO",
            "status": "NOT_AUTHORIZED",
            "reason": "GET_PREDICATES_UNSATISFIED_NO_HOPE_GET",
        },
    )
    return {
        "layer": "ADJUDICATED_CONCLUSION",
        "kind_set": KIND_SET_EMPTY,
        "kind_set_resolved": FALSE_TOKEN,
        "kind_set_closure_provable": kind_set_closure_provable,
        "ratified_kind_set": KIND_SET_EMPTY,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "reconstruction_algebra_complete": FALSE_TOKEN,
        "reconstruction_status": reconstruction_status,
        "earliest_unresolved_algebra_term": EARLIEST_UNRESOLVED_ALGEBRA_TERM,
        "unresolved_algebra_terms": unresolved,
        "residual_is_not_an_algebra_term": TRUE_TOKEN,
        "equity_stock_readiness": equity_stock_readiness,
        "running_account_equity_available_for_sizing_status": "UNBOUND_29P_SEMANTIC_MAPPING_UNPROVEN",
        "risk_sizing_readiness": risk_sizing_readiness,
        "complete_requires": COMPLETE_REQUIRES,
        "ratified_mapping_architecture": RATIFIED_MAPPING_ARCHITECTURE,
        "local_reconstruction_advancement_possible": FALSE_TOKEN,
        "local_equity_stock_advancement_possible": FALSE_TOKEN,
        "local_risk_sizing_advancement_possible": FALSE_TOKEN,
        "local_advancement_exhausted": TRUE_TOKEN,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_productive_classification": "REQUIRES_NEW_AUTHORITY_OR_NEW_EVIDENCE",
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "standing_full_core_dag_pin": DAG_PIN,
        "records": list(records),
    }


def execute_remaining_necessary_kind_evidence_classification_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    sealed_cj_pack: Path | str | None = None,
    persist_as_of: str | None = None,
) -> RemainingNecessaryKindEvidenceClassificationResultV1:
    if owner_go != OWNER_GO:
        raise RemainingNecessaryKindEvidenceClassificationError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise RemainingNecessaryKindEvidenceClassificationError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DURABLE_UNKNOWN_TOKEN)
    reject_kind_set_resolved_while_remaining_unknown_v1(claimed=FALSE_TOKEN)
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cj_pack = (
        Path(sealed_cj_pack) if sealed_cj_pack is not None else repo / CANONICAL_CJ_PACK_RELPATH
    )
    _assert_parent_cj_pack(sealed_cj_pack=cj_pack)
    _assert_reused_sealed_evidence(repo=repo)
    as_of = persist_as_of or CANONICAL_PERSIST_AS_OF
    if as_of is None or not isinstance(as_of, str) or as_of.strip() == "" or as_of != as_of.strip():
        raise RemainingNecessaryKindEvidenceClassificationError("FIELD_MISSING:persist_as_of")
    store = Path(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    get_eval = evaluate_read_only_get_predicates_v1()
    classifications = classify_unknowns_from_sealed_evidence_v1()
    matrix = build_decision_matrix_v1()
    downstream = reevaluate_kind_set_and_downstream_v1()
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "PIN_OWNER_GO": PIN_OWNER_GO,
        "PIN_OWNER_GO_STATUS": "SATISFIED_BY_WORKPACKAGE",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "PARENT_CJ_PACK": CANONICAL_CJ_PACK_RELPATH,
        "PARENT_CD_PACK": CANONICAL_CD_PACK_RELPATH,
        "PARENT_CE_PACK": CANONICAL_CE_PACK_RELPATH,
        "PARENT_CF_PACK": CANONICAL_CF_PACK_RELPATH,
        "PARENT_CG_PACK": CANONICAL_CG_PACK_RELPATH,
        "PARENT_CH_PACK": CANONICAL_CH_PACK_RELPATH,
        "PARENT_CI_PACK": CANONICAL_CI_PACK_RELPATH,
        "WORKPACKAGE": SCHEMA_CLASS,
        "START_BLOCK": DAG_PIN,
        "RATIFIED_MAPPING_ARCHITECTURE": RATIFIED_MAPPING_ARCHITECTURE,
        "COMPLETE_REQUIRES": COMPLETE_REQUIRES,
        "KIND_SET": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "KIND_SET_CLOSEOUT_STATUS": KIND_SET_CLOSEOUT_STATUS,
        "KIND_SET_EVIDENCE_PERSIST_STATUS": KIND_SET_EVIDENCE_PERSIST_STATUS,
        "KIND_SET_STATUS": KIND_SET_EMPTY,
        "RATIFIED_KIND_SET": KIND_SET_EMPTY,
        "ACCOUNT_EQUITY_SOURCE_MAPPING": DAG_PIN,
        "ACCOUNT_EQUITY_SOURCE_MAPPING_STATUS": DAG_PIN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": FALSE_TOKEN,
        "MAPPING_PROVEN": FALSE_TOKEN,
        "SEMANTIC_MAPPING_PROVEN": FALSE_TOKEN,
        "U04_STATUS": STATE_UNRESOLVED,
        "U04_KIND_SET_DISPOSITION": U04_KIND_SET_DISPOSITION,
        "U04_NOT_PINNED_DURABLE_UNKNOWN": TRUE_TOKEN,
        "U04_CLASSIFICATION": U04_CLASSIFICATION,
        "U05_STATUS": DECISION_REMAIN_UNKNOWN,
        "U06_STATUS": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_STATUS": DECISION_REMAIN_UNKNOWN,
        "U05_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "U06_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_KIND_DECISION": DECISION_REMAIN_UNKNOWN,
        "U05_CLASSIFICATION": U05_CLASSIFICATION,
        "U06_CLASSIFICATION": U06_CLASSIFICATION,
        "RESIDUAL_CLASSIFICATION": RESIDUAL_CLASSIFICATION,
        "U05_EMBEDDING_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "U06_PLACEMENT_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "RESIDUAL_EXHAUSTIVENESS_IDENTITY": DURABLE_UNKNOWN_TOKEN,
        "DURABLE_UNKNOWN_NOT_INCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_EXCLUDE": TRUE_TOKEN,
        "DURABLE_UNKNOWN_NOT_ABSENT_OR_ZERO": TRUE_TOKEN,
        "DECISION_MATRIX_RESULT": DECISION_MATRIX_RESULT,
        "NEW_EVIDENCE_ACQUIRED": FALSE_TOKEN,
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
        "parent_cj_pack": CANONICAL_CJ_PACK_RELPATH,
        "reused_packs": ",".join(
            (
                CANONICAL_CD_PACK_RELPATH,
                CANONICAL_CE_PACK_RELPATH,
                CANONICAL_CF_PACK_RELPATH,
                CANONICAL_CG_PACK_RELPATH,
                CANONICAL_CH_PACK_RELPATH,
                CANONICAL_CI_PACK_RELPATH,
                CANONICAL_CJ_PACK_RELPATH,
            )
        ),
        "new_evidence_acquired": FALSE_TOKEN,
        "hope_get_used": FALSE_TOKEN,
        "eq_source_authority_used": FALSE_TOKEN,
        "algebraic_uplift_used": FALSE_TOKEN,
        "duplicate_acquisition_used": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "trading_authority_unchanged": TRUE_TOKEN,
        "u04_not_reclassified_as_equity_stock_kind": TRUE_TOKEN,
        "u05_unchanged": TRUE_TOKEN,
        "u06_unchanged": TRUE_TOKEN,
        "residual_unchanged": TRUE_TOKEN,
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
        "kind_set_resolved": FALSE_TOKEN,
        "canonically_valid_account_equity_source_mapping": FALSE_TOKEN,
        "hope_get_forbidden": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "durable_unknown_is_not_include": TRUE_TOKEN,
        "durable_unknown_is_not_exclude": TRUE_TOKEN,
        "first_definitive_block": DAG_PIN,
        "exact_missing_predicate": EXACT_MISSING_PREDICATE,
        "next_productive_node": NEXT_PRODUCTIVE_NODE,
        "next_owner_go_required": NEXT_OWNER_GO,
        "next_action": NEXT_ACTION,
    }
    reused_vs_new = {
        "layer": "FORENSIC_RAW_EVIDENCE",
        "reused_sealed_packs": lineage["reused_packs"],
        "newly_acquired_evidence": NONE_TOKEN,
        "duplicate_acquisition": FALSE_TOKEN,
        "venue_get_count": "0",
        "venue_get_surfaces": NONE_TOKEN,
        "post_count": "0",
    }
    layers = {
        "CANONICAL_AUTHORITY": "architecture_blocker_v1.json",
        "FORENSIC_RAW_EVIDENCE": "reused_vs_new_evidence_v1.json",
        "ADJUDICATED_CONCLUSION": (
            "decision_matrix_v1.json,classification_proofs_v1.json,"
            "acquisition_predicate_evaluation_v1.json,"
            "downstream_dependency_tree_v1.json"
        ),
        "HISTORICAL": "LINEAGE.json",
        "NAVIGATION": "FORBIDDEN_AS_AUTHORITY",
        "INTERPRETATION": "FORBIDDEN",
        "HYPOTHESIS": "FORBIDDEN",
        "UNRESOLVED_OR_CONTRADICTORY": BLOCKER_ID,
    }
    _persist_json(path=store / CLAIMS_FILE, payload=claims)
    _persist_json(path=store / "decision_matrix_v1.json", payload=matrix)
    _persist_json(path=store / "classification_proofs_v1.json", payload=classifications)
    _persist_json(path=store / "acquisition_predicate_evaluation_v1.json", payload=get_eval)
    _persist_json(path=store / "downstream_dependency_tree_v1.json", payload=downstream)
    _persist_json(path=store / "architecture_blocker_v1.json", payload=architecture)
    _persist_json(path=store / "reused_vs_new_evidence_v1.json", payload=reused_vs_new)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "layers_v1.json", payload=layers)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=store)
    joined = "\n".join(path.read_text(encoding="utf-8") for path in store.glob("*.json"))
    lowered = joined.lower()
    if any(marker in lowered for marker in SECRET_MARKERS):
        raise RemainingNecessaryKindEvidenceClassificationError("SECRET_MARKER_PERSISTED")
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise RemainingNecessaryKindEvidenceClassificationError("MANIFEST_VERIFY_NOT_ZERO")
    return RemainingNecessaryKindEvidenceClassificationResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        persist_as_of=as_of,
        store_root=str(store),
        u04_classification=U04_CLASSIFICATION,
        u05_classification=U05_CLASSIFICATION,
        u06_classification=U06_CLASSIFICATION,
        residual_classification=RESIDUAL_CLASSIFICATION,
        decision_matrix_result=DECISION_MATRIX_RESULT,
        kind_set=KIND_SET_EMPTY,
        kind_set_resolved=FALSE_TOKEN,
        canonically_valid_account_equity_source_mapping=FALSE_TOKEN,
        first_definitive_block=DAG_PIN,
        exact_missing_predicate=EXACT_MISSING_PREDICATE,
        reconstruction_status=downstream["reconstruction_status"],
        equity_stock_readiness=downstream["equity_stock_readiness"],
        risk_sizing_readiness=downstream["risk_sizing_readiness"],
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
    "DECISION_MATRIX_RESULT",
    "EXACT_MISSING_PREDICATE",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "NEXT_ACTION",
    "NEXT_OWNER_GO",
    "NEXT_PRODUCTIVE_NODE",
    "OWNER_GO",
    "PARENT_BLOCKER_ID",
    "PIN_OWNER_GO",
    "RESIDUAL_CLASSIFICATION",
    "U04_CLASSIFICATION",
    "U05_CLASSIFICATION",
    "U06_CLASSIFICATION",
    "RemainingNecessaryKindEvidenceClassificationError",
    "build_decision_matrix_v1",
    "classify_unknowns_from_sealed_evidence_v1",
    "evaluate_read_only_get_predicates_v1",
    "execute_remaining_necessary_kind_evidence_classification_v1",
    "reevaluate_kind_set_and_downstream_v1",
    "reject_durable_unknown_reopen_without_new_evidence_v1",
    "reject_empty_none_bindable_or_get_count_zero_as_classification_v1",
    "reject_kind_set_resolved_while_remaining_unknown_v1",
    "reject_u04_reclassify_as_equity_stock_kind_v1",
)
