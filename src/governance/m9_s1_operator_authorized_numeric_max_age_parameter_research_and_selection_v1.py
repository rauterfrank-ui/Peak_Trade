"""M9-S1: operator-authorized numeric max-age parameter research and selection boundary v1.

Research execution reuses canonical_volatility_numeric_max_age_parameter_research_execution_v1.
This slice adds fail-closed operator authorization and owner-review selection evidence only.
It must not ratify, promote, enforce, or productively apply a numeric max-age value.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping, Optional, Sequence

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    EXPECTED_PREREGISTRATION_DIGEST,
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
)
from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.runner_v1 import (
    run_max_age_parameter_research_execution_v1,
)
from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.serialization_v1 import (
    canonical_json_dumps,
    digest_excluding_keys,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    PREREGISTERED_SELECTION_CRITERIA,
)

SCHEMA_VERSION: Final[str] = (
    "m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection/v1"
)
AUTHORIZATION_DOMAIN: Final[str] = (
    "peak_trade.governance.m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection.v1"
)
WORKPACKAGE_ID: Final[str] = (
    "M9_S1_OPERATOR_AUTHORIZED_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_AND_SELECTION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/M9_S1_OPERATOR_AUTHORIZED_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_AND_SELECTION_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1_decision_v1.json"
)
OWNER_BOUNDARY_CONFIG: Final[str] = (
    "config/governance/m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1_owner_boundary_v1.json"
)
DEFAULT_OWNER_INPUT_CONFIG: Final[str] = (
    "config/governance/m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_v1_owner_input_v1.json"
)
M9_OWNER_GRANT_CONFIG: Final[str] = (
    "config/governance/m9_volatility_numeric_max_age_optimizable_surface_owner_grant_v1.json"
)
DISCRETE_BOUNDS_CONFIG: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_discrete_bounds_v1.json"
)

OWNER_INPUT_SCHEMA_VERSION: Final[str] = (
    "m9_s1_operator_authorized_numeric_max_age_research_selection_owner_input/v1"
)
DEFAULT_OWNER_AUTHORIZATION_ID: Final[str] = (
    "m9_s1_operator_authorized_numeric_max_age_parameter_research_and_selection_owner_input/v1"
)

AUTHORIZED_SURFACE_ID: Final[str] = "VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1"
OPTIMIZATION_SURFACE_ID: Final[str] = AUTHORIZED_SURFACE_ID
CANDIDATE_PARAMETER: Final[str] = "candidate_max_age_seconds"

STATUS_AUTHORIZED_RESEARCH: Final[str] = "AUTHORIZED_FOR_OPERATOR_BOUND_PARAMETER_RESEARCH"
STATUS_DENIED: Final[str] = "DENIED_FAIL_CLOSED"

SELECTION_RESULT_UNRESOLVED: Final[str] = "UNRESOLVED_OWNER_DECISION"
SELECTION_RULE_STATUS_NO_DETERMINISTIC_POINT: Final[str] = (
    "NO_AUTHORIZED_DETERMINISTIC_NUMERIC_POINT_SELECTION_RULE"
)

NUMERIC_MAX_AGE_DECIDED: Final[bool] = False
ENFORCEMENT_ENABLED: Final[bool] = False
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE: Final[str] = "FORBIDDEN"
TRADING_DECISION_AUTHORITY_UNCHANGED: Final[bool] = True
PRODUCTIVE_PARAMETER_MUTATED: Final[bool] = False

SELECTION_BOUNDARY_SCHEMA_VERSION: Final[str] = (
    "m9_s1_owner_review_numeric_max_age_selection_boundary/v1"
)
LINEAGE_ATTESTATION_SCHEMA_VERSION: Final[str] = (
    "m9_s1_numeric_max_age_research_selection_lineage_attestation/v1"
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

_OWNER_RECORD_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "owner_authorization_id",
    "owner_authorization_version",
    "authorizer_identity",
    "bound_origin_main_sha",
    "bound_workpackage_id",
    "bound_authorized_surface_id",
    "bound_m9_owner_grant_config_ref",
    "bound_preregistration_digest",
    "bound_discrete_bounds_config_ref",
    "bound_discrete_candidate_max_age_seconds",
    "bound_optimization_surface_owner_ref",
    "research_execution_authorized",
    "numeric_threshold_selection_authorized",
    "parameter_promotion_authorized",
    "enforcement_authorized",
    "productive_configuration_authorization",
    "external_effect_authorized",
)


class M9S1OperatorAuthorizedResearchSelectionError(ValueError):
    """Fail-closed M9-S1 operator research / selection boundary error."""


@dataclass(frozen=True)
class OwnerM9S1ResearchAuthorizationInputV1:
    owner_authorization_record: Mapping[str, Any]
    owner_authorization_record_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_authorization_record": dict(self.owner_authorization_record),
            "owner_authorization_record_digest": self.owner_authorization_record_digest,
        }


@dataclass(frozen=True)
class M9S1OperatorResearchAuthorizationResultV1:
    authorization_status: str
    reason_codes: tuple[str, ...]
    authorization_digest: str | None
    authorization_record: MappingProxyType[str, Any] | None
    numeric_max_age_decided: bool = NUMERIC_MAX_AGE_DECIDED
    enforcement_enabled: bool = ENFORCEMENT_ENABLED
    external_effect_authorized: bool = EXTERNAL_EFFECT_AUTHORIZED


def _load_json(relative_path: str) -> dict[str, Any]:
    path = _REPO_ROOT / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise M9S1OperatorAuthorizedResearchSelectionError(f"config_not_mapping:{relative_path}")
    return payload


def compute_authoritative_candidate_domain_fingerprint_v1() -> str:
    """Stable fingerprint for operator-bound discrete domain (not per-execution bind)."""
    return compute_content_sha256(
        {
            "candidate_parameter": CANDIDATE_PARAMETER,
            "candidate_max_age_seconds": list(OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS),
            "preregistration_digest": EXPECTED_PREREGISTRATION_DIGEST,
            "discrete_bounds_config": DISCRETE_BOUNDS_CONFIG,
        }
    )


def load_owner_boundary_v1() -> MappingProxyType[str, Any]:
    return MappingProxyType(_load_json(OWNER_BOUNDARY_CONFIG))


def build_owner_m9_s1_research_authorization_record_v1(
    *,
    bound_origin_main_sha: str,
    owner_authorization_id: str = DEFAULT_OWNER_AUTHORIZATION_ID,
    owner_authorization_version: str = OWNER_INPUT_SCHEMA_VERSION,
    authorizer_identity: str = "OWNER_M9_S1_OPERATOR_AUTHORIZED_PARAMETER_RESEARCH",
) -> MappingProxyType[str, Any]:
    grant = _load_json(M9_OWNER_GRANT_CONFIG)
    record = {
        "schema_version": OWNER_INPUT_SCHEMA_VERSION,
        "owner_authorization_id": owner_authorization_id,
        "owner_authorization_version": owner_authorization_version,
        "authorizer_identity": authorizer_identity,
        "bound_origin_main_sha": bound_origin_main_sha,
        "bound_workpackage_id": WORKPACKAGE_ID,
        "bound_authorized_surface_id": str(grant.get("authorized_surface_id") or ""),
        "bound_m9_owner_grant_config_ref": M9_OWNER_GRANT_CONFIG,
        "bound_preregistration_digest": EXPECTED_PREREGISTRATION_DIGEST,
        "bound_discrete_bounds_config_ref": DISCRETE_BOUNDS_CONFIG,
        "bound_discrete_candidate_max_age_seconds": list(OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS),
        "bound_optimization_surface_owner_ref": str(grant.get("surface_owner_ref") or ""),
        "research_execution_authorized": True,
        "numeric_threshold_selection_authorized": False,
        "parameter_promotion_authorized": False,
        "enforcement_authorized": False,
        "productive_configuration_authorization": False,
        "external_effect_authorized": False,
    }
    missing = [key for key in _OWNER_RECORD_KEYS if key not in record]
    if missing:
        raise M9S1OperatorAuthorizedResearchSelectionError(
            f"OWNER_RECORD_INCOMPLETE:{','.join(missing)}"
        )
    return MappingProxyType(record)


def compute_owner_authorization_record_digest_v1(
    owner_authorization_record: Mapping[str, Any],
) -> str:
    body = {key: owner_authorization_record[key] for key in _OWNER_RECORD_KEYS}
    return compute_content_sha256(body)


def build_owner_m9_s1_research_authorization_input_v1(
    *,
    bound_origin_main_sha: str,
    owner_authorization_id: str = DEFAULT_OWNER_AUTHORIZATION_ID,
    authorizer_identity: str = "OWNER_M9_S1_OPERATOR_AUTHORIZED_PARAMETER_RESEARCH",
) -> OwnerM9S1ResearchAuthorizationInputV1:
    record = build_owner_m9_s1_research_authorization_record_v1(
        bound_origin_main_sha=bound_origin_main_sha,
        owner_authorization_id=owner_authorization_id,
        authorizer_identity=authorizer_identity,
    )
    digest = compute_owner_authorization_record_digest_v1(record)
    return OwnerM9S1ResearchAuthorizationInputV1(
        owner_authorization_record=record,
        owner_authorization_record_digest=digest,
    )


def load_committed_owner_m9_s1_research_authorization_input_v1() -> (
    OwnerM9S1ResearchAuthorizationInputV1
):
    payload = _load_json(DEFAULT_OWNER_INPUT_CONFIG)
    record = payload.get("owner_authorization_record")
    digest = payload.get("owner_authorization_record_digest")
    if not isinstance(record, dict):
        raise M9S1OperatorAuthorizedResearchSelectionError("OWNER_INPUT_RECORD_INVALID")
    if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
        raise M9S1OperatorAuthorizedResearchSelectionError("OWNER_INPUT_DIGEST_INVALID")
    expected = compute_owner_authorization_record_digest_v1(record)
    if digest != expected:
        raise M9S1OperatorAuthorizedResearchSelectionError("OWNER_INPUT_DIGEST_MISMATCH")
    return OwnerM9S1ResearchAuthorizationInputV1(
        owner_authorization_record=MappingProxyType(record),
        owner_authorization_record_digest=digest,
    )


def evaluate_m9_s1_operator_research_authorization_v1(
    *,
    owner_authorization_input: OwnerM9S1ResearchAuthorizationInputV1 | None,
    repository_sha: str,
) -> M9S1OperatorResearchAuthorizationResultV1:
    """Fail-closed; missing or mismatched owner input never authorizes research execution."""
    reason_codes: list[str] = []
    if owner_authorization_input is None:
        return M9S1OperatorResearchAuthorizationResultV1(
            authorization_status=STATUS_DENIED,
            reason_codes=("OWNER_AUTHORIZATION_INPUT_REQUIRED",),
            authorization_digest=None,
            authorization_record=None,
        )

    record = dict(owner_authorization_input.owner_authorization_record)
    digest = owner_authorization_input.owner_authorization_record_digest
    if compute_owner_authorization_record_digest_v1(record) != digest:
        reason_codes.append("OWNER_AUTHORIZATION_DIGEST_MISMATCH")

    boundary = load_owner_boundary_v1()
    decision = _load_json(DECISION_CONFIG)
    if str(decision.get("workpackage_id") or "") != WORKPACKAGE_ID:
        reason_codes.append("DECISION_WORKPACKAGE_MISMATCH")

    if record.get("schema_version") != OWNER_INPUT_SCHEMA_VERSION:
        reason_codes.append("OWNER_SCHEMA_VERSION_MISMATCH")
    if str(record.get("bound_workpackage_id") or "") != WORKPACKAGE_ID:
        reason_codes.append("OWNER_WORKPACKAGE_MISMATCH")
    if str(record.get("bound_preregistration_digest") or "") != EXPECTED_PREREGISTRATION_DIGEST:
        reason_codes.append("PREREGISTRATION_DIGEST_MISMATCH")
    if tuple(record.get("bound_discrete_candidate_max_age_seconds") or ()) != tuple(
        OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS
    ):
        reason_codes.append("CANDIDATE_DOMAIN_MISMATCH")

    grant = _load_json(M9_OWNER_GRANT_CONFIG)
    if str(record.get("bound_authorized_surface_id") or "") != str(
        grant.get("authorized_surface_id") or ""
    ):
        reason_codes.append("SURFACE_ID_MISMATCH")
    if grant.get("threshold_selection_authorized") is not False:
        reason_codes.append("M9_GRANT_THRESHOLD_SELECTION_NOT_FORBIDDEN")
    if grant.get("enforcement_authorized") is not False:
        reason_codes.append("M9_GRANT_ENFORCEMENT_NOT_FORBIDDEN")

    forbidden_flags = (
        ("numeric_threshold_selection_authorized", False),
        ("parameter_promotion_authorized", False),
        ("enforcement_authorized", False),
        ("productive_configuration_authorization", False),
        ("external_effect_authorized", False),
    )
    for key, expected in forbidden_flags:
        if record.get(key) is not expected:
            reason_codes.append(f"FORBIDDEN_FLAG:{key}")

    if record.get("research_execution_authorized") is not True:
        reason_codes.append("RESEARCH_EXECUTION_NOT_AUTHORIZED")

    allowed_ids = boundary.get("allowed_owner_authorization_ids")
    if not isinstance(allowed_ids, list) or record.get("owner_authorization_id") not in allowed_ids:
        reason_codes.append("OWNER_AUTHORIZATION_ID_NOT_ALLOWED")

    bound_sha = str(record.get("bound_origin_main_sha") or "")
    if boundary.get("require_repository_sha_match") is True and bound_sha != repository_sha:
        reason_codes.append("BOUND_ORIGIN_MAIN_SHA_MISMATCH")

    if reason_codes:
        return M9S1OperatorResearchAuthorizationResultV1(
            authorization_status=STATUS_DENIED,
            reason_codes=tuple(reason_codes),
            authorization_digest=None,
            authorization_record=None,
        )

    authorization_record = MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "authorization_domain": AUTHORIZATION_DOMAIN,
            "workpackage_id": WORKPACKAGE_ID,
            "authorization_status": STATUS_AUTHORIZED_RESEARCH,
            "authorized_surface_id": AUTHORIZED_SURFACE_ID,
            "candidate_parameter": CANDIDATE_PARAMETER,
            "candidate_domain_fingerprint": compute_authoritative_candidate_domain_fingerprint_v1(),
            "owner_authorization_record_digest": digest,
            "repository_sha": repository_sha,
            "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
            "enforcement_enabled": ENFORCEMENT_ENABLED,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "optimization_direct_productive_write": OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
            "productive_parameter_mutated": PRODUCTIVE_PARAMETER_MUTATED,
        }
    )
    authorization_digest = compute_content_sha256(dict(authorization_record))
    return M9S1OperatorResearchAuthorizationResultV1(
        authorization_status=STATUS_AUTHORIZED_RESEARCH,
        reason_codes=("AUTHORIZED",),
        authorization_digest=authorization_digest,
        authorization_record=authorization_record,
    )


def _evidence_completeness_from_execution_v1(
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    conclusion = execution.get("conclusion") or {}
    return {
        "input_evidence_valid": bool(execution.get("input_evidence_valid")),
        "insufficient_research_evidence": bool(execution.get("insufficient_research_evidence")),
        "walk_forward_executed": bool(execution.get("walk_forward_executed")),
        "final_holdout_executed": bool(execution.get("final_holdout_executed")),
        "regime_slices_executed": bool(execution.get("regime_slices_executed")),
        "session_slices_executed": bool(execution.get("session_slices_executed")),
        "parameter_perturbation_executed": bool(execution.get("parameter_perturbation_executed")),
        "bootstrap_executed": bool(execution.get("bootstrap_executed")),
        "deterministic_reexecution_pass": bool(execution.get("deterministic_reexecution_pass")),
        "ledger_resume_equivalence_pass": bool(execution.get("ledger_resume_equivalence_pass")),
        "research_conclusion": execution.get("research_conclusion"),
        "robust_candidate_region_identified": bool(
            conclusion.get("robust_candidate_region_identified")
        ),
        "robust_candidate_region": conclusion.get("robust_candidate_region"),
    }


def _deterministic_comparison_digest_v1(
    *,
    candidate_results: Sequence[Mapping[str, Any]],
    rejection_matrix: Sequence[Mapping[str, Any]],
) -> str:
    comparison = {
        "candidate_results": [
            {
                "candidate_id": row.get("candidate_id"),
                "candidate_max_age_seconds_argument": row.get("candidate_max_age_seconds_argument"),
                "rejected": (row.get("parameter_stability") or {}).get("rejected"),
                "rejection_reasons": (row.get("parameter_stability") or {}).get(
                    "rejection_reasons"
                ),
                "stale_rejection_rate": row.get("stale_rejection_rate"),
                "decision_coverage": row.get("decision_coverage"),
            }
            for row in sorted(
                candidate_results,
                key=lambda r: str(r.get("candidate_id") or ""),
            )
        ],
        "rejection_matrix": [
            {
                "candidate_id": row.get("candidate_id"),
                "rejected": row.get("rejected"),
                "rejection_reasons": row.get("rejection_reasons"),
            }
            for row in sorted(
                rejection_matrix,
                key=lambda r: str(r.get("candidate_id") or ""),
            )
        ],
    }
    return compute_content_sha256(comparison)


def build_owner_review_selection_boundary_evidence_v1(
    *,
    execution_result: Mapping[str, Any],
    authorization_digest: str,
) -> dict[str, Any]:
    """Owner-review selection boundary; never emits a ratified numeric max-age."""
    candidate_set = list(OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS)
    candidate_results = list(execution_result.get("candidate_results") or [])
    rejection_matrix = list(execution_result.get("rejection_matrix") or [])

    evaluated_seconds = sorted(
        {
            int(row["candidate_max_age_seconds_argument"])
            for row in candidate_results
            if row.get("candidate_max_age_seconds_argument") is not None
            and row.get("candidate_id") != "UNRESOLVED_MAX_AGE_NON_ENFORCING"
        }
    )
    admissible_evaluated = [value for value in evaluated_seconds if value in candidate_set]
    rejected_candidates: list[dict[str, Any]] = []
    for row in rejection_matrix:
        if row.get("rejected"):
            rejected_candidates.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "rejection_reasons": list(row.get("rejection_reasons") or ()),
                }
            )

    robust_region = execution_result.get("robust_candidate_region")
    unresolved_ambiguity: list[str] = []
    if isinstance(robust_region, list) and len(robust_region) > 1:
        unresolved_ambiguity.append("ROBUST_REGION_CONTAINS_MULTIPLE_DISCRETE_CANDIDATES")
    if execution_result.get("insufficient_research_evidence"):
        unresolved_ambiguity.append("INSUFFICIENT_RESEARCH_EVIDENCE")
    if not execution_result.get("input_evidence_valid"):
        unresolved_ambiguity.append("INPUT_EVIDENCE_INVALID")

    comparison_digest = _deterministic_comparison_digest_v1(
        candidate_results=candidate_results,
        rejection_matrix=rejection_matrix,
    )

    boundary: dict[str, Any] = {
        "schema_version": SELECTION_BOUNDARY_SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "authorization_digest": authorization_digest,
        "execution_id": execution_result.get("execution_id"),
        "repository_sha": execution_result.get("repository_sha"),
        "preregistration_digest": execution_result.get("preregistration_digest"),
        "candidate_parameter": CANDIDATE_PARAMETER,
        "candidate_set": candidate_set,
        "admissible_evaluated_candidates": admissible_evaluated,
        "rejected_candidates": rejected_candidates,
        "evidence_completeness": _evidence_completeness_from_execution_v1(execution_result),
        "deterministic_comparison_digest": comparison_digest,
        "preregistered_selection_criteria": list(PREREGISTERED_SELECTION_CRITERIA),
        "selection_rule_status": SELECTION_RULE_STATUS_NO_DETERMINISTIC_POINT,
        "selection_result": SELECTION_RESULT_UNRESOLVED,
        "proposed_candidate_max_age_seconds": None,
        "proposed_numeric_max_age_seconds": None,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "numeric_threshold_selected": False,
        "parameter_promoted": False,
        "enforcement_enabled": ENFORCEMENT_ENABLED,
        "enforcement_applied": False,
        "unresolved_ambiguity": unresolved_ambiguity,
        "next_owner_decision": (
            "SEPARATE_OWNER_AUTHORIZED_THRESHOLD_SELECTION_OR_FURTHER_EVIDENCE_ACCUMULATION"
        ),
    }
    boundary["selection_boundary_digest"] = digest_excluding_keys(
        boundary, exclude={"selection_boundary_digest"}
    )
    return boundary


def build_m9_s1_lineage_attestation_v1(
    *,
    authorization_record: Mapping[str, Any],
    selection_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    attestation = {
        "schema_version": LINEAGE_ATTESTATION_SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "chain_research_lane": [
            "OPTIMIZATION_SURFACE_VOLATILITY_NUMERIC_MAX_AGE",
            "OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS",
            "CANONICAL_RESEARCH_EXECUTION_V1",
            "EVIDENCE_ARTIFACTS",
            "PROPOSAL_ONLY_OWNER_REVIEW_SELECTION_BOUNDARY",
        ],
        "chain_productive_lane_not_activated": [
            "EXPLICIT_PRODUCTIVE_AUTHORIZATION",
            "GOVERNED_PRODUCTIVE_PARAMETER_SEAM",
            "CURRENT_PRODUCTIVE_CONSUMER",
        ],
        "productive_lane_activated": False,
        "optimization_direct_productive_write": OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "enforcement_enabled": ENFORCEMENT_ENABLED,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "trading_decision_authority_unchanged": TRADING_DECISION_AUTHORITY_UNCHANGED,
        "authorization_digest": authorization_record.get("owner_authorization_record_digest"),
        "selection_boundary_digest": selection_boundary.get("selection_boundary_digest"),
        "selection_result": selection_boundary.get("selection_result"),
    }
    attestation["lineage_attestation_digest"] = digest_excluding_keys(
        attestation, exclude={"lineage_attestation_digest"}
    )
    return attestation


def run_m9_s1_operator_authorized_parameter_research_and_selection_v1(
    *,
    repo_root: Path,
    owner_authorization_input: OwnerM9S1ResearchAuthorizationInputV1 | None,
    output_root: Path,
    records: Optional[Sequence[Any]] = None,
    ledger_path: Optional[Path] = None,
    repository_sha: Optional[str] = None,
    created_at_utc: Optional[str] = None,
) -> dict[str, Any]:
    """Operator-gated research execution plus owner-review selection boundary artifacts."""
    from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.runner_v1 import (
        resolve_repository_sha_v1,
    )

    sha = repository_sha or resolve_repository_sha_v1(repo_root)
    auth = evaluate_m9_s1_operator_research_authorization_v1(
        owner_authorization_input=owner_authorization_input,
        repository_sha=sha,
    )
    if auth.authorization_status != STATUS_AUTHORIZED_RESEARCH:
        failure = {
            "workpackage_id": WORKPACKAGE_ID,
            "authorization_status": auth.authorization_status,
            "reason_codes": list(auth.reason_codes),
            "research_execution_status": "NOT_STARTED",
            "selection_result": SELECTION_RESULT_UNRESOLVED,
            "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
            "enforcement_enabled": ENFORCEMENT_ENABLED,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
        failure["failure_digest"] = compute_content_sha256(failure)
        out = output_root / "m9_s1_authorization_denied.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(canonical_json_dumps(failure) + "\n", encoding="utf-8")
        return failure

    assert auth.authorization_record is not None
    assert auth.authorization_digest is not None

    execution = run_max_age_parameter_research_execution_v1(
        repo_root=repo_root,
        ledger_path=ledger_path,
        output_root=output_root / "research_execution",
        repository_sha=sha,
        records=records,
        created_at_utc=created_at_utc,
    )

    selection_boundary = build_owner_review_selection_boundary_evidence_v1(
        execution_result=execution,
        authorization_digest=auth.authorization_digest,
    )
    lineage = build_m9_s1_lineage_attestation_v1(
        authorization_record=dict(auth.authorization_record),
        selection_boundary=selection_boundary,
    )

    package = {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "authorization_status": auth.authorization_status,
        "authorization_digest": auth.authorization_digest,
        "research_execution_status": execution.get("status"),
        "execution_id": execution.get("execution_id"),
        "evidence_status": "EMITTED" if execution.get("input_evidence_valid") else "BLOCKED",
        "selection_rule_status": SELECTION_RULE_STATUS_NO_DETERMINISTIC_POINT,
        "selection_result": SELECTION_RESULT_UNRESOLVED,
        "selection_boundary": selection_boundary,
        "lineage_attestation": lineage,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "productive_parameter_mutated": PRODUCTIVE_PARAMETER_MUTATED,
        "enforcement_enabled": ENFORCEMENT_ENABLED,
        "trading_decision_authority_unchanged": TRADING_DECISION_AUTHORITY_UNCHANGED,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "real_blocker_for_numeric_ratification": ("SEPARATE_OWNER_AUTHORIZED_THRESHOLD_SELECTION"),
    }
    package["package_digest"] = digest_excluding_keys(package, exclude={"package_digest"})

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "m9_s1_owner_review_selection_boundary.json").write_text(
        canonical_json_dumps(selection_boundary) + "\n",
        encoding="utf-8",
    )
    (output_root / "m9_s1_lineage_attestation.json").write_text(
        canonical_json_dumps(lineage) + "\n",
        encoding="utf-8",
    )
    (output_root / "m9_s1_owner_review_package.json").write_text(
        canonical_json_dumps(package) + "\n",
        encoding="utf-8",
    )
    return package


__all__ = [
    "AUTHORIZATION_DOMAIN",
    "CANDIDATE_PARAMETER",
    "DECISION_CONFIG",
    "ENFORCEMENT_ENABLED",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "M9S1OperatorAuthorizedResearchSelectionError",
    "M9S1OperatorResearchAuthorizationResultV1",
    "NUMERIC_MAX_AGE_DECIDED",
    "OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE",
    "OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS",
    "OwnerM9S1ResearchAuthorizationInputV1",
    "SELECTION_RESULT_UNRESOLVED",
    "SELECTION_RULE_STATUS_NO_DETERMINISTIC_POINT",
    "STATUS_AUTHORIZED_RESEARCH",
    "STATUS_DENIED",
    "TRADING_DECISION_AUTHORITY_UNCHANGED",
    "WORKPACKAGE_ID",
    "build_m9_s1_lineage_attestation_v1",
    "build_owner_m9_s1_research_authorization_input_v1",
    "build_owner_m9_s1_research_authorization_record_v1",
    "build_owner_review_selection_boundary_evidence_v1",
    "compute_authoritative_candidate_domain_fingerprint_v1",
    "compute_owner_authorization_record_digest_v1",
    "evaluate_m9_s1_operator_research_authorization_v1",
    "load_committed_owner_m9_s1_research_authorization_input_v1",
    "run_m9_s1_operator_authorized_parameter_research_and_selection_v1",
]
