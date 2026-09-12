"""Typed Cap 2.2 WP1 append-only 15m PIT persistence / collection contract."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.cap22_append_only_15m_pit_persistence_v1.constants_v1 import (
    APPEND_ONLY,
    AUTHORITY_EFFECT,
    AUTHORITY_SCOPE,
    BOUND_ORIGIN_MAIN_SHA,
    CAP21_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED,
    CAP21_EXISTING_PRODUCER_AUTHORITY_PRESERVED,
    CAP22_90D_EVIDENCE_CLOCK_STARTED,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    CAP22_PROSPECTIVE_COLLECTION_CONTRACTS_IMPLEMENTED,
    CAP22_PROSPECTIVE_COLLECTION_STARTED,
    COLLECTION_CADENCE_ID,
    COLLECTION_NETWORK_AUTHORIZED,
    COLLECTION_SCHEDULER_ENABLED,
    CONFLICTING_OVERWRITE_FORBIDDEN,
    CONTRACT_ID,
    DECISION_ID,
    DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK,
    ECONOMIC_MD_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED,
    ECONOMIC_MD_EXISTING_PRODUCER_AUTHORITY_PRESERVED,
    ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED,
    ECONOMIC_RANK_ACTIVATED,
    EXACT_T_BINDING_REQUIRED,
    FALSE_REQUIRED_FLAGS,
    FORWARD_LABEL_EXECUTION_IMPLEMENTED,
    HISTORICAL_EVIDENCE_GENERATED,
    IDENTICAL_DUPLICATE_IDEMPOTENT,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NEXT_CAP22_DEPENDENCY,
    NEXT_CANONICAL_DECISION,
    NO_NEAREST_LATEST_FALLBACK,
    NO_TODAY_UNIVERSE_MEMBERSHIP_RETROACTIVE,
    OWNER_GO_THIS_SLICE,
    PDF_STEP_5_STATUS,
    PDF_STEP_7_STATUS,
    POLICY_RATIFICATION_JUSTIFIED,
    PRODUCTIVE_SELECTION_OWNER,
    PROSPECTIVE_COLLECTION_STARTED,
    RUNTIME_AUTHORITY_GRANTED,
    SCHEMA_VERSION,
    TRUE_REQUIRED_FLAGS,
    WALK_FORWARD_EXECUTION_IMPLEMENTED,
)
from src.ops.cap22_append_only_15m_pit_persistence_v1.reason_codes_v1 import (
    Cap22AppendOnlyPitPersistenceFailureCodeV1,
)

from src.ops.cap22_append_only_15m_pit_persistence_v1.anchor_v1 import (
    Cap22AppendOnlyPitPersistenceError,
)


class Cap22AppendOnlyPitPersistenceContractError(Cap22AppendOnlyPitPersistenceError):
    """Fail-closed WP1 contract declaration error."""


def _require_mapping(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise Cap22AppendOnlyPitPersistenceContractError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.DIGEST_OR_SCHEMA_ERROR.value,
            "DECLARATION_NOT_A_MAPPING",
        )
    return payload


def _require_false_flags(raw: Mapping[str, Any]) -> None:
    for key in FALSE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not False:
            raise Cap22AppendOnlyPitPersistenceContractError(
                Cap22AppendOnlyPitPersistenceFailureCodeV1.DIGEST_OR_SCHEMA_ERROR.value,
                f"FALSE_FLAG_VIOLATION:{key}",
            )


def _require_true_flags(raw: Mapping[str, Any]) -> None:
    for key in TRUE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not True:
            raise Cap22AppendOnlyPitPersistenceContractError(
                Cap22AppendOnlyPitPersistenceFailureCodeV1.DIGEST_OR_SCHEMA_ERROR.value,
                f"TRUE_FLAG_VIOLATION:{key}",
            )


def classify_cap22_append_only_15m_pit_persistence_v1() -> dict[str, Any]:
    return {
        "authority_effect": AUTHORITY_EFFECT,
        "authority_scope": AUTHORITY_SCOPE,
        "cap21_append_only_at_t_persistence_implemented": (
            CAP21_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED
        ),
        "cap21_existing_producer_authority_preserved": (
            CAP21_EXISTING_PRODUCER_AUTHORITY_PRESERVED
        ),
        "cap22_prospective_collection_contracts_implemented": (
            CAP22_PROSPECTIVE_COLLECTION_CONTRACTS_IMPLEMENTED
        ),
        "cap22_prospective_collection_started": CAP22_PROSPECTIVE_COLLECTION_STARTED,
        "cap22_90d_evidence_clock_started": CAP22_90D_EVIDENCE_CLOCK_STARTED,
        "collection_cadence_id": COLLECTION_CADENCE_ID,
        "collection_network_authorized": COLLECTION_NETWORK_AUTHORIZED,
        "collection_scheduler_enabled": COLLECTION_SCHEDULER_ENABLED,
        "economic_md_append_only_at_t_persistence_implemented": (
            ECONOMIC_MD_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED
        ),
        "economic_md_existing_producer_authority_preserved": (
            ECONOMIC_MD_EXISTING_PRODUCER_AUTHORITY_PRESERVED
        ),
        "exact_t_binding_required": EXACT_T_BINDING_REQUIRED,
        "no_nearest_latest_fallback": NO_NEAREST_LATEST_FALLBACK,
        "no_today_universe_membership_retroactive": NO_TODAY_UNIVERSE_MEMBERSHIP_RETROACTIVE,
        "prospective_collection_started": PROSPECTIVE_COLLECTION_STARTED,
    }


def classify_preserved_program_invariants_v1() -> dict[str, Any]:
    return {
        "append_only": APPEND_ONLY,
        "bound_origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
        "conflicting_overwrite_forbidden": CONFLICTING_OVERWRITE_FORBIDDEN,
        "contract_id": CONTRACT_ID,
        "decision_id": DECISION_ID,
        "downstream_execution_must_not_re_rank": DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK,
        "economic_md_producer_productively_scheduled": (
            ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED
        ),
        "economic_rank_activated": ECONOMIC_RANK_ACTIVATED,
        "forward_label_execution_implemented": FORWARD_LABEL_EXECUTION_IMPLEMENTED,
        "historical_evidence_generated": HISTORICAL_EVIDENCE_GENERATED,
        "identical_duplicate_idempotent": IDENTICAL_DUPLICATE_IDEMPOTENT,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "next_cap22_dependency": NEXT_CAP22_DEPENDENCY,
        "next_canonical_decision": NEXT_CANONICAL_DECISION,
        "owner_go_this_slice": OWNER_GO_THIS_SLICE,
        "pdf_step_5_status": PDF_STEP_5_STATUS,
        "pdf_step_7_status": PDF_STEP_7_STATUS,
        "policy_ratification_justified": POLICY_RATIFICATION_JUSTIFIED,
        "productive_economic_runtime_wired": CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
        "productive_selection_owner": PRODUCTIVE_SELECTION_OWNER,
        "runtime_authority_granted": RUNTIME_AUTHORITY_GRANTED,
        "schema_version": SCHEMA_VERSION,
        "walk_forward_execution_implemented": WALK_FORWARD_EXECUTION_IMPLEMENTED,
    }


def validate_cap22_append_only_15m_pit_persistence_declaration_v1(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    raw = _require_mapping(payload)
    _require_false_flags(raw)
    _require_true_flags(raw)
    if raw.get("collection_cadence_id") not in (None, COLLECTION_CADENCE_ID):
        raise Cap22AppendOnlyPitPersistenceContractError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.DIGEST_OR_SCHEMA_ERROR.value,
            "COLLECTION_CADENCE_ID_MISMATCH",
        )
    if raw.get("pdf_step_5_status") not in (None, PDF_STEP_5_STATUS):
        raise Cap22AppendOnlyPitPersistenceContractError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.DIGEST_OR_SCHEMA_ERROR.value,
            "PDF_STEP_5_MUST_REMAIN_UNRESOLVED",
        )
    if raw.get("pdf_step_7_status") not in (None, PDF_STEP_7_STATUS):
        raise Cap22AppendOnlyPitPersistenceContractError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.DIGEST_OR_SCHEMA_ERROR.value,
            "PDF_STEP_7_MUST_REMAIN_FORBIDDEN",
        )
    if raw.get("next_cap22_dependency") not in (None, NEXT_CAP22_DEPENDENCY):
        raise Cap22AppendOnlyPitPersistenceContractError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.DIGEST_OR_SCHEMA_ERROR.value,
            "NEXT_CAP22_DEPENDENCY_MISMATCH",
        )
    return {
        "authority_effect": AUTHORITY_EFFECT,
        "contract_id": CONTRACT_ID,
        "collection_cadence_id": COLLECTION_CADENCE_ID,
        "schema_version": SCHEMA_VERSION,
        "valid": True,
    }
