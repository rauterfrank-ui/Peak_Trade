"""BJ future-admissible evidence-class and INCLUDE/EXCLUDE qualification laws.

Law persist only. Does not GET. Does not POST. Does not execute GATE_A
or GATE_B. Does not decide U05/U06/Residual. Does not uplift sealed
historical packs. bills remains noncanonical. venue eq remains
reconciliation target only. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_KIND_DECISION,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.eq_identity_and_f12_f13_liability_stock_kind_ratification_v1 import (
    DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BJ_PIN_PACK_RELPATH,
    EXHAUSTED_OR_FORBIDDEN_CLASSES,
    GATE_A_ID,
    GATE_B_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.option_d_ssot_architecture_contract_v1 import (
    FORBIDDEN_SOURCE_FIELDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

OWNER_GO = (
    "OWNER_GO_REQUIRED_TO_CHANGE_BJ_FUTURE_ADMISSIBLE_EVIDENCE_CLASSES_"
    "AND_SURFACE_INCLUDE_EXCLUDE_QUALIFICATION_LAWS"
)
EXPECTED_ORIGIN_MAIN_SHA = "e73fff95df411bd471dbadd3f8ce380f61108743"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_bj_future_admissible_evidence_and_include_exclude_"
    "qualification_law_v1/2026-09-14T224500Z"
)
CANONICAL_PERSIST_AS_OF = "2026-09-14T22:45:00Z"
CANONICAL_GATE_A_PACK_RELPATH = (
    "evidence/ops/full_core_option_d_gate_a_independently_attested_"
    "productive_nonzero_liability_stock_v1/2026-09-14T200500Z"
)
SCHEMA_CLASS = "BJ_FUTURE_ADMISSIBLE_EVIDENCE_AND_INCLUDE_EXCLUDE_QUALIFICATION_LAW_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
KIND_SET_EMPTY = "EMPTY_FAIL_CLOSED"
OUTCOME_INCLUDE = "INCLUDE"
OUTCOME_EXCLUDE = "EXCLUDE"
OUTCOME_NONQUALIFYING = "NONQUALIFYING"
OUTCOME_REMAIN_UNKNOWN = DECISION_REMAIN_UNKNOWN
TARGET_U05 = "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND"
TARGET_U06 = "U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND"
TARGET_RESIDUAL = "RESIDUAL_UNNAMED_NECESSARY_EQUITY_STOCK_EVENT_CLASS"
CLASS_U05 = "U05_INDEPENDENT_LIABILITY_EVENT_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRIMARY_PROOF_V1"
CLASS_U06 = "U06_PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_EFFECT_PRIMARY_PROOF_V1"
CLASS_RESIDUAL = "RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF_V1"
NEW_FUTURE_ADMISSIBLE_EVIDENCE_CLASS_IDS: frozenset[str] = frozenset(
    {CLASS_U05, CLASS_U06, CLASS_RESIDUAL}
)
OLD_FUTURE_ADMISSIBLE_EVIDENCE_CLASSES: frozenset[str] = frozenset({GATE_A_ID, GATE_B_ID})
PROOF_OBJECT_U05 = "INDEPENDENT_LIABILITY_EVENT_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_V1"
PROOF_OBJECT_U06 = "PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_EFFECT_V1"
PROOF_OBJECT_RESIDUAL = "POSITIVE_NECESSARY_KIND_INVENTORY_EXHAUSTIVENESS_CERTIFICATE_V1"
PRODUCER = ACCOUNT_EQUITY_AUTHORITY_OWNER
ACQUISITION_SURFACE = (
    "FORENSIC_INDEPENDENT_EQUITY_STOCK_AFFECTING_EVENT_RECORD_NOT_BALANCE_SNAPSHOT_"
    "NOT_SOURCE_AUTHORITY"
)
FORBIDDEN_RETROACTIVE_PACKS: tuple[str, ...] = (
    CANONICAL_GATE_A_PACK_RELPATH,
    "evidence/ops/full_core_d6_f12_f13_primary_liability_stock_observation_v1/2026-09-13T221500Z",
    "evidence/ops/full_core_d6_eq_identity_and_f12_f13_liability_stock_kind_"
    "ratification_v1/2026-09-13T230000Z",
    CANONICAL_BJ_PIN_PACK_RELPATH,
)
FORBIDDEN_RETROACTIVE_MARKERS: tuple[str, ...] = (
    "gate_a_independently_attested",
    "bh_empty_zero_absent",
    "sealed_package_1_bills",
    "algebraic_eq_cashbal_upl_liab",
)
_SILENT_ZERO_MARKERS: tuple[str, ...] = (
    "0",
    "0.0",
    "zero",
    "no-op",
    "noop",
    "empty",
    "absent",
    "missing",
)
HYPOTHESIS_ONLY_TOKENS: tuple[str, ...] = (
    "DEPOSIT",
    "WITHDRAWAL",
    "TRANSFER",
    "FUNDING",
    "INTEREST",
    "LIQUIDATION",
    "CONVERT",
)
NEXT_OWNER_GO = (
    "OWNER_GO_REQUIRED_FOR_FORENSIC_ACQUISITION_OF_"
    "U05_INDEPENDENT_LIABILITY_EVENT_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRIMARY_PROOF_V1"
)
CLAIMS_FILE = "claims.json"


class BjFutureAdmissibleEvidenceAndQualificationLawError(ValueError):
    """Fail-closed BJ qualification-law persist violation."""


@dataclass(frozen=True)
class QualificationOutcomeV1:
    evidence_class_id: str
    target_unknown: str
    outcome: str
    basis: str


@dataclass(frozen=True)
class BjFutureAdmissibleEvidenceAndQualificationLawResultV1:
    genesis_id: str
    genesis_as_of: str
    persist_as_of: str
    store_root: str
    qualification_law_change_status: str
    new_evidence_class_count: str
    new_evidence_class_ids: str
    u05_decision_after: str
    u06_decision_after: str
    residual_decision_after: str
    ratified_classified_event_kind_set_after: str
    productive_acquisition_executed: str
    evidence_manifest: str


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None or isinstance(raw, bool) or not isinstance(raw, str):
        raise BjFutureAdmissibleEvidenceAndQualificationLawError(f"FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError(f"FIELD_MISSING:{field}")
    return text


def _assert_standing_pins() -> None:
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("AUTHORITY_OWNER_MUTATED")
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError(
            "U05_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError(
            "U06_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError(
            "RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN"
        )
    if KIND_SET_RESOLVED is not False:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("KIND_SET_MUST_REMAIN_EMPTY")
    if AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is not False:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("SOURCE_SEAM_MUST_REMAIN_ABSENT")
    if COMPLETE_EVENT_STREAM_PROVEN is not False:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError(
            "COMPLETE_STREAM_MUST_REMAIN_UNPROVEN"
        )
    if MS2_AUTHORIZED is not False:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("MS2_AUTHORIZED_NOT_FALSE")
    if D6_FULLY_CLOSED is not False:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("D6_FULLY_CLOSED_NOT_FALSE")
    if D7_AUTHORIZED is not False:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("D7_AUTHORIZED_NOT_FALSE")
    if C17_CREATED is not False:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("C17_CREATED_NOT_FALSE")
    if RAW_EQ_SOURCE_AUTHORITY is not False:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError(
            "RAW_EQ_SOURCE_AUTHORITY_NOT_FALSE"
        )
    if ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is not True:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("BILLS_CANONICALIZED_FORBIDDEN")
    if "eq" not in FORBIDDEN_SOURCE_FIELDS:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("EQ_FORBIDDEN_SOURCE_PIN_DRIFT")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("DAG_PIN_DRIFT")


def _is_silent_zero(raw: str) -> bool:
    return raw.strip().lower() in _SILENT_ZERO_MARKERS


def _reject_retroactive(*, proof: Mapping[str, Any]) -> str | None:
    blob = _canonical_json(proof).lower()
    for marker in FORBIDDEN_RETROACTIVE_MARKERS:
        if marker in blob:
            return f"RETROACTIVE_UPLIFT_FORBIDDEN:{marker}"
    source_pack = str(proof.get("source_pack") or "")
    if source_pack in FORBIDDEN_RETROACTIVE_PACKS:
        return f"RETROACTIVE_UPLIFT_FORBIDDEN:{source_pack}"
    return None


def _reject_exhausted_relabel(*, proof: Mapping[str, Any]) -> str | None:
    claimed = str(proof.get("claimed_exhausted_class_reuse") or "")
    if claimed and claimed in EXHAUSTED_OR_FORBIDDEN_CLASSES:
        return f"EXHAUSTED_CLASS_RELABEL_FORBIDDEN:{claimed}"
    return None


def evaluate_u05_primary_proof_v1(*, proof: Mapping[str, Any]) -> QualificationOutcomeV1:
    retro = _reject_retroactive(proof=proof)
    if retro:
        return QualificationOutcomeV1(CLASS_U05, TARGET_U05, OUTCOME_NONQUALIFYING, retro)
    exhausted = _reject_exhausted_relabel(proof=proof)
    if exhausted:
        return QualificationOutcomeV1(CLASS_U05, TARGET_U05, OUTCOME_NONQUALIFYING, exhausted)
    snapshot_token = str(proof.get("balance_snapshot_liability_token") or "")
    if snapshot_token != "":
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "BALANCE_SNAPSHOT_TOKEN_IS_NOT_U05_PRIMARY_PROOF",
        )
    if _is_silent_zero(str(proof.get("mapped_numeric_effect") or "absent")):
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "EMPTY_ZERO_ABSENT_IS_NOT_EXCLUDE_AND_NOT_INCLUDE",
        )
    algebraic = str(proof.get("algebraic_eq_identity_used") or "")
    if algebraic in {TRUE_TOKEN, "true", "USED"}:
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "ALGEBRAIC_EQ_IDENTITY_FORBIDDEN",
        )
    embedding = str(proof.get("embedding_state") or "")
    if embedding in {"", "UNRESOLVED", "UNKNOWN"}:
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "EMBEDDING_STATE_UNRESOLVED_NONQUALIFYING",
        )
    p01_overlap = str(proof.get("p01_overlap_state") or "")
    if p01_overlap in {"", "UNKNOWN", "UNRESOLVED"}:
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "P01_OVERLAP_UNRESOLVED_NONQUALIFYING",
        )
    required_include = (
        "unique_event_id",
        "event_digest",
        "ordering_key",
        "bound_account_identity_ref",
        "bound_account_identity_digest",
        "prior_anchor_id",
        "event_after_prior_as_of",
        "liability_event_semantic_class",
        "mapped_numeric_effect",
        "currency_domain",
        "embedding_proof_id",
        "independent_of_balance_snapshot",
        "independent_of_algebraic_eq_identity",
    )
    missing = [field for field in required_include if str(proof.get(field) or "").strip() == ""]
    if missing:
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            f"PRIMARY_PROOF_OBJECT_INCOMPLETE:{','.join(missing)}",
        )
    semantic = str(proof.get("liability_event_semantic_class") or "")
    if semantic in {"P01_GOVERNED_RISK_CAPITAL_REDUCTION", "U04_PENDING_ORDER_RESERVATION"}:
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "PLACEMENT_OR_ALGEBRA_TERM_IS_NOT_EVENT_KIND",
        )
    if str(proof.get("independent_of_balance_snapshot") or "") != TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "INDEPENDENCE_FROM_BALANCE_SNAPSHOT_REQUIRED",
        )
    if str(proof.get("independent_of_algebraic_eq_identity") or "") != TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "INDEPENDENCE_FROM_ALGEBRAIC_EQ_IDENTITY_REQUIRED",
        )
    if embedding == "IN_BASE" and p01_overlap == "U05_NOT_P01":
        if str(proof.get("empty_zero_absent_used_as_exclude") or "") == TRUE_TOKEN:
            return QualificationOutcomeV1(
                CLASS_U05,
                TARGET_U05,
                OUTCOME_NONQUALIFYING,
                "EMPTY_ZERO_ABSENT_IS_NOT_EXCLUDE",
            )
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_EXCLUDE,
            "POSITIVE_NON_ALGEBRAIC_EMBEDDING_IN_BASE_PROVES_U05_NOT_SEPARATE_KIND",
        )
    if embedding != "SEPARATE":
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "EMBEDDING_NOT_SEPARATE_AND_NOT_IN_BASE",
        )
    if p01_overlap not in {"NON_OVERLAPPING", "U05_NOT_P01"}:
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "P01_OVERLAP_NOT_DISPROVEN",
        )
    if str(proof.get("event_after_prior_as_of") or "") != TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_U05,
            TARGET_U05,
            OUTCOME_NONQUALIFYING,
            "EVENT_NOT_PROVEN_AFTER_PRIOR",
        )
    return QualificationOutcomeV1(
        CLASS_U05,
        TARGET_U05,
        OUTCOME_INCLUDE,
        "POSITIVE_INDEPENDENT_LIABILITY_EVENT_AND_SEPARATE_NON_ALGEBRAIC_EMBEDDING",
    )


def evaluate_u06_primary_proof_v1(*, proof: Mapping[str, Any]) -> QualificationOutcomeV1:
    retro = _reject_retroactive(proof=proof)
    if retro:
        return QualificationOutcomeV1(CLASS_U06, TARGET_U06, OUTCOME_NONQUALIFYING, retro)
    exhausted = _reject_exhausted_relabel(proof=proof)
    if exhausted:
        return QualificationOutcomeV1(CLASS_U06, TARGET_U06, OUTCOME_NONQUALIFYING, exhausted)
    if str(proof.get("fee_field_token_only") or "") == TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            "FEE_TOKEN_ALONE_IS_NOT_PRIMARY_PROOF",
        )
    if _is_silent_zero(str(proof.get("fee_amount") or "absent")):
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            "EMPTY_ZERO_ABSENT_FEE_IS_NOT_EXCLUDE_AND_NOT_INCLUDE",
        )
    pairing = str(proof.get("pairing_status") or "")
    placement = str(proof.get("base_or_event_or_reconciliation") or "")
    if pairing in {"", "UNPAIRED", "UNRESOLVED"}:
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            "UNPAIRED_FEE_EVENT_NONQUALIFYING",
        )
    if placement in {"", "UNRESOLVED", "UNKNOWN"}:
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            "BASE_EVENT_RECONCILIATION_UNRESOLVED_NONQUALIFYING",
        )
    required_include = (
        "unique_fee_event_id",
        "event_digest",
        "ordering_key",
        "bound_account_identity_ref",
        "bound_account_identity_digest",
        "prior_anchor_id",
        "event_after_prior_as_of",
        "fee_amount",
        "currency_domain",
        "pairing_equity_stock_observation_id",
        "pairing_observation_is_not_raw_eq_source",
        "once_only_guard_id",
    )
    missing = [field for field in required_include if str(proof.get(field) or "").strip() == ""]
    if missing:
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            f"PRIMARY_PROOF_OBJECT_INCOMPLETE:{','.join(missing)}",
        )
    if str(proof.get("pairing_observation_is_not_raw_eq_source") or "") != TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            "PAIRING_OBSERVATION_CANNOT_BE_RAW_EQ_SOURCE",
        )
    if str(proof.get("blind_subtraction") or "") == TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            "BLIND_FEE_SUBTRACTION_FORBIDDEN",
        )
    if placement == "IN_BASE" and str(proof.get("fee_coverage_complete") or "") == TRUE_TOKEN:
        if str(proof.get("empty_zero_absent_used_as_exclude") or "") == TRUE_TOKEN:
            return QualificationOutcomeV1(
                CLASS_U06,
                TARGET_U06,
                OUTCOME_NONQUALIFYING,
                "EMPTY_ZERO_ABSENT_IS_NOT_EXCLUDE",
            )
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_EXCLUDE,
            "POSITIVE_PAIRED_IN_BASE_FEE_COVERAGE_PROVES_U06_NOT_SEPARATE_KIND",
        )
    if placement != "EVENT_SEPARATE":
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            "PLACEMENT_NOT_EVENT_SEPARATE_AND_NOT_IN_BASE",
        )
    if str(proof.get("pairing_delta_matches_fee") or "") != TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            "PAIRING_DELTA_DOES_NOT_MATCH_FEE",
        )
    if str(proof.get("event_after_prior_as_of") or "") != TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_U06,
            TARGET_U06,
            OUTCOME_NONQUALIFYING,
            "FEE_EVENT_NOT_PROVEN_AFTER_PRIOR",
        )
    return QualificationOutcomeV1(
        CLASS_U06,
        TARGET_U06,
        OUTCOME_INCLUDE,
        "POSITIVE_PAIRED_ONCE_ONLY_FEE_EVENT_SEPARATE_FROM_BASE",
    )


def evaluate_residual_primary_proof_v1(*, proof: Mapping[str, Any]) -> QualificationOutcomeV1:
    retro = _reject_retroactive(proof=proof)
    if retro:
        return QualificationOutcomeV1(CLASS_RESIDUAL, TARGET_RESIDUAL, OUTCOME_NONQUALIFYING, retro)
    exhausted = _reject_exhausted_relabel(proof=proof)
    if exhausted:
        return QualificationOutcomeV1(
            CLASS_RESIDUAL, TARGET_RESIDUAL, OUTCOME_NONQUALIFYING, exhausted
        )
    inventory = str(proof.get("necessary_kind_inventory") or "")
    if any(token in inventory.split(",") for token in HYPOTHESIS_ONLY_TOKENS):
        return QualificationOutcomeV1(
            CLASS_RESIDUAL,
            TARGET_RESIDUAL,
            OUTCOME_NONQUALIFYING,
            "HYPOTHESIS_ONLY_LIST_IS_NOT_EXHAUSTIVENESS_PROOF",
        )
    if str(proof.get("path_c_used") or "") == TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_RESIDUAL,
            TARGET_RESIDUAL,
            OUTCOME_NONQUALIFYING,
            "PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT_REJECT",
        )
    if str(proof.get("no_rows_used_as_no_class") or "") == TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_RESIDUAL,
            TARGET_RESIDUAL,
            OUTCOME_NONQUALIFYING,
            "NON_OBSERVATION_IS_NOT_EXCLUDE",
        )
    required = (
        "exhaustiveness_certificate_id",
        "certificate_digest",
        "independent_taxonomy_authority",
        "necessary_kind_inventory",
        "window_id",
        "bound_account_identity_ref",
        "bound_account_identity_digest",
    )
    missing = [field for field in required if str(proof.get(field) or "").strip() == ""]
    if missing:
        return QualificationOutcomeV1(
            CLASS_RESIDUAL,
            TARGET_RESIDUAL,
            OUTCOME_NONQUALIFYING,
            f"PRIMARY_PROOF_OBJECT_INCOMPLETE:{','.join(missing)}",
        )
    if str(proof.get("proven_complete") or "") != TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_RESIDUAL,
            TARGET_RESIDUAL,
            OUTCOME_NONQUALIFYING,
            "EXHAUSTIVENESS_NOT_PROVEN",
        )
    if str(proof.get("empty_set_normalized_to_zero_events") or "") == TRUE_TOKEN:
        return QualificationOutcomeV1(
            CLASS_RESIDUAL,
            TARGET_RESIDUAL,
            OUTCOME_NONQUALIFYING,
            "EMPTY_SET_IS_NOT_ZERO_NECESSARY_EVENTS",
        )
    return QualificationOutcomeV1(
        CLASS_RESIDUAL,
        TARGET_RESIDUAL,
        OUTCOME_EXCLUDE,
        "POSITIVE_NECESSARY_KIND_INVENTORY_EXHAUSTIVENESS_CERTIFICATE",
    )


def evaluate_current_absent_proofs_v1() -> Tuple[QualificationOutcomeV1, ...]:
    empty: dict[str, Any] = {}
    return (
        evaluate_u05_primary_proof_v1(proof=empty),
        evaluate_u06_primary_proof_v1(proof=empty),
        evaluate_residual_primary_proof_v1(proof=empty),
    )


def build_evidence_class_definitions_v1() -> dict[str, Any]:
    return {
        "layer": "CANONICAL_AUTHORITY",
        "producer": PRODUCER,
        "acquisition_surface": ACQUISITION_SURFACE,
        "acquisition_authorized_this_go": FALSE_TOKEN,
        "bills_source_authority": FALSE_TOKEN,
        "bills_current_noncanonical": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "records": [
            {
                "evidence_class_id": CLASS_U05,
                "target_unknown": TARGET_U05,
                "primary_proof_object": PROOF_OBJECT_U05,
                "producer": PRODUCER,
                "acquisition_surface": ACQUISITION_SURFACE,
                "scope": "D4_BOUND_ACCOUNT_AND_TODAY_PRIOR_WINDOW",
                "provenance": "unique_event_id+event_digest+bound_account_identity",
                "positive_include_predicate": (
                    "independent_liability_event_after_prior_AND_embedding_SEPARATE_"
                    "by_non_algebraic_identity_AND_p01_overlap_disproven"
                ),
                "positive_exclude_predicate": (
                    "non_algebraic_embedding_IN_BASE_AND_not_from_empty_zero_absent"
                ),
                "nonqualifying_outcomes": (
                    "GATE_A_snapshot_tokens;empty_zero_absent;algebraic_eq_identity;"
                    "embedding_unresolved;p01_overlap_unresolved;incomplete_proof_object;"
                    "retroactive_sealed_pack"
                ),
                "independence_requirement": (
                    "event_not_balance_snapshot_AND_embedding_not_algebraic_eq_identity"
                ),
                "pairing_requirement": "liability_event_paired_to_non_eq_source_embedding_proof",
                "completeness_requirement": "NOT_APPLICABLE_SINGLE_EVENT_KIND",
                "dedup_idempotency": "unique_event_id_fail_closed_on_duplicate",
                "ordering_time_semantics": "ordering_key_after_prior_as_of",
                "amount_sign_currency": "nonzero_settlement_currency_once",
                "double_counting_protection": (
                    "SEPARATE_event_cannot_also_be_applied_as_embedded_base_without_fail_closed"
                ),
                "reconciliation_role": "NOT_FRESH_EQ_SOURCE",
                "replay_reproducibility": "digest_stable_proof_object_required",
            },
            {
                "evidence_class_id": CLASS_U06,
                "target_unknown": TARGET_U06,
                "primary_proof_object": PROOF_OBJECT_U06,
                "producer": PRODUCER,
                "acquisition_surface": ACQUISITION_SURFACE,
                "scope": "D4_BOUND_ACCOUNT_AND_TODAY_PRIOR_WINDOW",
                "provenance": "unique_fee_event_id+event_digest+bound_account_identity",
                "positive_include_predicate": (
                    "paired_fee_event_after_prior_AND_placement_EVENT_SEPARATE_"
                    "AND_once_only_AND_pairing_observation_not_raw_eq_source"
                ),
                "positive_exclude_predicate": (
                    "paired_IN_BASE_fee_coverage_complete_AND_not_from_empty_zero_absent"
                ),
                "nonqualifying_outcomes": (
                    "fee_token_alone;unpaired;placement_unresolved;blind_subtraction;"
                    "pairing_uses_raw_eq;incomplete_proof_object;retroactive_sealed_pack"
                ),
                "independence_requirement": "pairing_observation_is_not_raw_eq_source",
                "pairing_requirement": "fee_event_paired_to_equity_stock_effect_observation",
                "completeness_requirement": "EXCLUDE_REQUIRES_FEE_COVERAGE_COMPLETE",
                "dedup_idempotency": "unique_fee_event_id_once_only_guard",
                "ordering_time_semantics": "ordering_key_after_prior_as_of",
                "amount_sign_currency": "nonzero_settlement_currency_once",
                "double_counting_protection": "EVENT_SEPARATE_xor_IN_BASE_fail_closed",
                "reconciliation_role": "NOT_FRESH_EQ_SOURCE_NOT_BLIND_SUBTRACTION",
                "replay_reproducibility": "digest_stable_proof_object_required",
            },
            {
                "evidence_class_id": CLASS_RESIDUAL,
                "target_unknown": TARGET_RESIDUAL,
                "primary_proof_object": PROOF_OBJECT_RESIDUAL,
                "producer": PRODUCER,
                "acquisition_surface": "INDEPENDENT_TAXONOMY_EXHAUSTIVENESS_CERTIFICATE_NOT_GET",
                "scope": "D4_BOUND_ACCOUNT_AND_NAMED_WINDOW",
                "provenance": "exhaustiveness_certificate_id+certificate_digest",
                "positive_include_predicate": "NONE_RESIDUAL_IS_NOT_AN_INCLUDE_KIND",
                "positive_exclude_predicate": (
                    "positive_necessary_kind_inventory_exhaustiveness_certificate"
                ),
                "nonqualifying_outcomes": (
                    "hypothesis_only_list;path_c;no_rows_equals_no_class;"
                    "empty_set_as_zero_events;incomplete_certificate"
                ),
                "independence_requirement": "taxonomy_authority_not_hypothesis_and_not_path_c",
                "pairing_requirement": "NOT_APPLICABLE",
                "completeness_requirement": "POSITIVE_EXHAUSTIVENESS_REQUIRED_FOR_EXCLUDE",
                "dedup_idempotency": "certificate_digest_replay_identity",
                "ordering_time_semantics": "window_id_required",
                "amount_sign_currency": "NOT_APPLICABLE",
                "double_counting_protection": "NOT_APPLICABLE_INVENTORY_PROOF",
                "reconciliation_role": "NOT_FRESH_EQ_SOURCE",
                "replay_reproducibility": "digest_stable_certificate_required",
            },
        ],
    }


def execute_bj_future_admissible_evidence_and_include_exclude_qualification_law_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    persist_as_of: str,
) -> BjFutureAdmissibleEvidenceAndQualificationLawResultV1:
    if owner_go != OWNER_GO:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    as_of = _require_non_empty_str(field="persist_as_of", raw=persist_as_of)
    root = Path(evidence_root)
    outcomes = evaluate_current_absent_proofs_v1()
    for outcome in outcomes:
        if outcome.outcome in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}:
            raise BjFutureAdmissibleEvidenceAndQualificationLawError(
                f"LAW_MUST_NOT_DECIDE_WITHOUT_PROOF:{outcome.evidence_class_id}"
            )
        if outcome.outcome != OUTCOME_NONQUALIFYING:
            raise BjFutureAdmissibleEvidenceAndQualificationLawError(
                f"ABSENT_PROOF_MUST_BE_NONQUALIFYING:{outcome.evidence_class_id}"
            )
    definitions = build_evidence_class_definitions_v1()
    evaluation = {
        "layer": "ADJUDICATED_CONCLUSION",
        "current_primary_proof_present": FALSE_TOKEN,
        "records": [
            {
                "evidence_class_id": item.evidence_class_id,
                "target_unknown": item.target_unknown,
                "outcome": item.outcome,
                "basis": item.basis,
            }
            for item in outcomes
        ],
    }
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "PERSIST_AS_OF": as_of,
        "QUALIFICATION_LAW_CHANGE_STATUS": "RATIFIED",
        "OLD_FUTURE_ADMISSIBLE_EVIDENCE_CLASSES": ",".join(
            sorted(OLD_FUTURE_ADMISSIBLE_EVIDENCE_CLASSES)
        ),
        "NEW_EVIDENCE_CLASS_COUNT": str(len(NEW_FUTURE_ADMISSIBLE_EVIDENCE_CLASS_IDS)),
        "NEW_EVIDENCE_CLASS_IDS": ",".join(sorted(NEW_FUTURE_ADMISSIBLE_EVIDENCE_CLASS_IDS)),
        "U05_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "U06_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "RESIDUAL_DECISION_AFTER": DECISION_REMAIN_UNKNOWN,
        "RATIFIED_CLASSIFIED_EVENT_KIND_SET_AFTER": KIND_SET_EMPTY,
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "PRODUCTIVE_ACQUISITION_EXECUTED": FALSE_TOKEN,
        "GATE_A_RETRY_EXECUTED": FALSE_TOKEN,
        "GATE_B_REEXECUTED": FALSE_TOKEN,
        "VENUE_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "ACCOUNT_BILLS_CANONICALIZED": FALSE_TOKEN,
        "RETROACTIVE_UPLIFT_FORBIDDEN": TRUE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "C17_CREATED": FALSE_TOKEN,
        "STANDING_FULL_CORE_DAG_PIN": DAG_PIN,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "PROTECTED_SURFACES_UNCHANGED": TRUE_TOKEN,
    }
    lineage = {
        "origin_main_sha": origin_main_sha,
        "owner_go": OWNER_GO,
        "genesis_id": EXPECTED_GENESIS_ID,
        "genesis_as_of": EXPECTED_GENESIS_AS_OF,
        "persist_as_of": as_of,
        "parent_bj_pack": CANONICAL_BJ_PIN_PACK_RELPATH,
        "parent_gate_a_pack": CANONICAL_GATE_A_PACK_RELPATH,
        "reconstruction_source_authority": FALSE_TOKEN,
    }
    protected = {
        "master_v2_unchanged": TRUE_TOKEN,
        "double_play_unchanged": TRUE_TOKEN,
        "bull_bear_state_switch_unchanged": TRUE_TOKEN,
        "self_learning_unchanged": TRUE_TOKEN,
        "top20_unchanged": TRUE_TOKEN,
        "full_core_autonomy_unchanged": TRUE_TOKEN,
        "step_29p_unchanged": TRUE_TOKEN,
        "ms2_authorized": FALSE_TOKEN,
        "reconstruction_implemented": FALSE_TOKEN,
        "dag_pin": DAG_PIN,
    }
    retroactive = {
        "layer": "CANONICAL_AUTHORITY",
        "retroactive_uplift_forbidden": TRUE_TOKEN,
        "forbidden_packs": ",".join(FORBIDDEN_RETROACTIVE_PACKS),
        "gate_a_sealed_pack_nonqualifying": TRUE_TOKEN,
        "package_1_bills_forensic_nonqualifying": TRUE_TOKEN,
    }
    laws = {
        "layer": "CANONICAL_AUTHORITY",
        "empty_zero_absent_is_not_exclude": TRUE_TOKEN,
        "observation_is_not_kind_ratification": TRUE_TOKEN,
        "acquisition_evidence_is_not_source_authority": TRUE_TOKEN,
        "reconciliation_target_is_not_source_authority": TRUE_TOKEN,
        "venue_eq_source_authority": FALSE_TOKEN,
        "account_bills_canonicalized": FALSE_TOKEN,
        "hypothesis_only_is_not_kind": TRUE_TOKEN,
        "include_requires_positive_primary_proof": TRUE_TOKEN,
        "exclude_requires_positive_primary_proof": TRUE_TOKEN,
        "residual_none_requires_positive_exhaustiveness": TRUE_TOKEN,
        "placement_or_algebra_is_not_event_kind": TRUE_TOKEN,
        "missing_decision_capability_remain_unknown": TRUE_TOKEN,
        "retroactive_uplift_forbidden": TRUE_TOKEN,
        "exhausted_class_relabel_forbidden": TRUE_TOKEN,
        "law_change_does_not_decide_u05_u06_residual": TRUE_TOKEN,
        "classes": definitions["records"],
    }
    _persist_json(path=root / CLAIMS_FILE, payload=claims)
    _persist_json(path=root / "evidence_class_definitions_v1.json", payload=definitions)
    _persist_json(path=root / "current_proof_evaluation_v1.json", payload=evaluation)
    _persist_json(path=root / "qualification_laws_v1.json", payload=laws)
    _persist_json(path=root / "retroactive_uplift_guard_v1.json", payload=retroactive)
    _persist_json(path=root / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=root / "LINEAGE.json", payload=lineage)
    persist_manifest_sha256_v1(store_root=root)
    if verify_manifest_sha256_v1(store_root=root) != 0:
        raise BjFutureAdmissibleEvidenceAndQualificationLawError("MANIFEST_VERIFY_NOT_ZERO")
    return BjFutureAdmissibleEvidenceAndQualificationLawResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        persist_as_of=as_of,
        store_root=str(root),
        qualification_law_change_status="RATIFIED",
        new_evidence_class_count=str(len(NEW_FUTURE_ADMISSIBLE_EVIDENCE_CLASS_IDS)),
        new_evidence_class_ids=",".join(sorted(NEW_FUTURE_ADMISSIBLE_EVIDENCE_CLASS_IDS)),
        u05_decision_after=DECISION_REMAIN_UNKNOWN,
        u06_decision_after=DECISION_REMAIN_UNKNOWN,
        residual_decision_after=DECISION_REMAIN_UNKNOWN,
        ratified_classified_event_kind_set_after=KIND_SET_EMPTY,
        productive_acquisition_executed=FALSE_TOKEN,
        evidence_manifest=str(root / "MANIFEST.sha256"),
    )
