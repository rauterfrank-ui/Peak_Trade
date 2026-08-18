"""Canonical Experiment Identity to Package-N I16 promotion admission v1.

Attaches a Phase-1 COMPLETE identity as a research-evidence parent onto an
existing Package-N experiment_identity_id for manual_only I16 assessment.
Does not recompute Package-N hashes, apply promotions, or grant runtime
authority.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_experiment_identity_v1 import (
    COMPLETENESS_COMPLETE,
    CanonicalExperimentIdentityError,
    IDENTITY_DOMAIN as PHASE1_IDENTITY_DOMAIN,
    SCHEMA_VERSION as PHASE1_SCHEMA_VERSION,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.cross_lane_identity_join_v1 import (
    CrossLaneIdentityJoinV1,
    is_package_n_sha256_canonical_id,
)
from src.experiments.experiment_identity_manifest_v1 import (
    ExperimentIdentityManifestError,
    PACKAGE_N_IDENTITY_COMPLETENESS,
    validate_experiment_identity_manifest_v1,
)
from src.governance.promotion_loop.i16_remaining_planes_join_attachment_v1 import (
    I16RemainingPlanesJoinAttachmentError,
    attach_i16_remaining_planes_join_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "canonical_experiment_identity_to_package_n_i16_promotion_admission_v1"
ADMISSION_DOMAIN: Final[str] = (
    "peak_trade.canonical_experiment_identity_to_package_n_i16_promotion_admission.v1"
)
ADMISSION_PRESENT: Final[bool] = True
ADMISSION_AUTHORITY: Final[str] = "RESEARCH_EVIDENCE_PARENT_ONLY"
PROMOTION_AUTHORITY: Final[str] = "NONE"
PROMOTION_APPLY_ALLOWED: Final[bool] = False
BOUNDED_AUTO_ALLOWED: Final[bool] = False
REQUIRED_PROMOTION_MODE: Final[str] = "manual_only"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"
SELF_LEARNING_NOT_SELF_AUTHORIZING: Final[bool] = True

STATUS_ADMITTED: Final[str] = "ADMITTED"
STATUS_REJECTED_MISSING_DIMENSION: Final[str] = "REJECTED_MISSING_DIMENSION"
STATUS_REJECTED_INCOMPATIBLE_DIMENSION: Final[str] = "REJECTED_INCOMPATIBLE_DIMENSION"
STATUS_REJECTED_AMBIGUOUS_IDENTITY: Final[str] = "REJECTED_AMBIGUOUS_IDENTITY"
STATUS_REJECTED_UNSUPPORTED_PROJECTION: Final[str] = "REJECTED_UNSUPPORTED_PROJECTION"
STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED: Final[str] = (
    "REJECTED_HASH_REINTERPRETATION_REQUIRED"
)
STATUS_REJECTED_AUTHORITY_BOUNDARY: Final[str] = "REJECTED_AUTHORITY_BOUNDARY"
STATUS_REJECTED_INCOMPLETE_IDENTITY: Final[str] = "REJECTED_INCOMPLETE_IDENTITY"
STATUS_REJECTED_INVALID_PACKAGE_N: Final[str] = "REJECTED_INVALID_PACKAGE_N"

NON_PROJECTABLE_PHASE1_DIMENSIONS: Final[tuple[str, ...]] = (
    "dataset_digest",
    "feature_pipeline_digest",
    "fee_model_digest",
    "slippage_model_digest",
    "funding_model_digest",
    "risk_policy_digest",
    "portfolio_digest",
    "split_policy_digest",
    "seed",
    "git_sha",
    "working_tree_status",
    "trading_decision_core_digest",
    "environment_digest",
)

_LOGGER = logging.getLogger(__name__)


class CanonicalIdentityToPackageNI16AdmissionError(ValueError):
    """Fail-closed malformed admission request error."""


@dataclass(frozen=True)
class CanonicalIdentityToPackageNI16AdmissionRequestV1:
    phase1_identity: Mapping[str, Any]
    package_n_manifest: Mapping[str, Any]
    claimed_package_n_is_phase1_complete: bool = False
    claimed_recomputed_package_n_id: str | None = None
    requested_promotion_mode: str = REQUIRED_PROMOTION_MODE
    requested_apply: bool = False


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _plain_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()}


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CanonicalIdentityToPackageNI16AdmissionError(f"{label} must be a mapping")
    return value


def _rejected(
    status: str,
    reason: str,
    *,
    package_n_id: str | None = None,
    parent_digest: str | None = None,
    parent_integrity: str | None = None,
    requested_mode: str = REQUIRED_PROMOTION_MODE,
) -> Mapping[str, Any]:
    return _build_result(
        status=status,
        rejection_reason=reason,
        package_n_id=package_n_id,
        parent_digest=parent_digest,
        parent_integrity=parent_integrity,
        i16_assessment_consumable=False,
        i16_join=None,
        requested_mode=requested_mode,
    )


def _authority_invariants() -> dict[str, Any]:
    return {
        "admission_authority": ADMISSION_AUTHORITY,
        "bounded_auto_allowed": BOUNDED_AUTO_ALLOWED,
        "promotion_apply_allowed": PROMOTION_APPLY_ALLOWED,
        "promotion_authority": PROMOTION_AUTHORITY,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "self_learning_not_self_authorizing": SELF_LEARNING_NOT_SELF_AUTHORIZING,
        "live_authorized": False,
        "testnet_authorized": False,
        "order_effect": False,
        "account_mutation_effect": False,
        "multi_future_auth_effect": False,
        "funding_auth_effect": False,
        "i82_full_migration": False,
        "md5_removal": False,
        "identity_backfill": False,
    }


def _build_result(
    *,
    status: str,
    rejection_reason: str | None,
    package_n_id: str | None,
    parent_digest: str | None,
    parent_integrity: str | None,
    i16_assessment_consumable: bool,
    i16_join: Mapping[str, Any] | None,
    requested_mode: str,
) -> Mapping[str, Any]:
    admitted = status == STATUS_ADMITTED
    body = {
        "schema_version": SCHEMA_VERSION,
        "admission_domain": ADMISSION_DOMAIN,
        "admission_present": ADMISSION_PRESENT,
        "status": status,
        "rejection_reason": rejection_reason,
        "package_n_experiment_identity_id": package_n_id,
        "package_n_identity_completeness": PACKAGE_N_IDENTITY_COMPLETENESS,
        "package_n_experiment_identity_id_mutated": False,
        "hash_reinterpreted": False,
        "research_evidence_parent_identity_digest": parent_digest,
        "research_evidence_parent_integrity_sha256": parent_integrity,
        "i16_assessment_consumable": i16_assessment_consumable and admitted,
        "requested_promotion_mode": requested_mode,
        "required_promotion_mode": REQUIRED_PROMOTION_MODE,
        "i16_join": None if i16_join is None else dict(i16_join),
        "authority_invariants": _authority_invariants(),
    }
    body["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in body.items() if key != "integrity"}
        )
    }
    return MappingProxyType(_freeze(body))


def _package_n_strategy_name(manifest: Mapping[str, Any]) -> str | None:
    identity_config = manifest.get("identity_config")
    if not isinstance(identity_config, Mapping):
        return None
    raw = identity_config.get("strategy_name")
    if not isinstance(raw, str) or not raw.strip() or raw != raw.strip():
        return None
    return raw


def evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1(
    request: CanonicalIdentityToPackageNI16AdmissionRequestV1,
) -> Mapping[str, Any]:
    """Evaluate admission. Never mutates Package-N hashes or writes config."""
    phase1 = _require_mapping(request.phase1_identity, "phase1_identity")
    package_n = _require_mapping(request.package_n_manifest, "package_n_manifest")
    requested_mode = request.requested_promotion_mode
    phase1_plain = _plain_mapping(phase1)
    package_n_plain = _plain_mapping(package_n)

    if request.requested_apply is True:
        return _rejected(
            STATUS_REJECTED_AUTHORITY_BOUNDARY,
            "requested_apply is forbidden; admission is not promotion apply",
            requested_mode=requested_mode,
        )
    if requested_mode != REQUIRED_PROMOTION_MODE:
        return _rejected(
            STATUS_REJECTED_AUTHORITY_BOUNDARY,
            "requested_promotion_mode must be manual_only",
            requested_mode=requested_mode,
        )
    if request.claimed_package_n_is_phase1_complete is True:
        return _rejected(
            STATUS_REJECTED_UNSUPPORTED_PROJECTION,
            "Package N cannot be claimed as Phase-1 COMPLETE; incomplete projection retained",
            requested_mode=requested_mode,
        )
    if request.claimed_recomputed_package_n_id is not None:
        return _rejected(
            STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED,
            "Package-N experiment_identity_id must not be recomputed or reinterpreted",
            requested_mode=requested_mode,
        )

    try:
        validate_canonical_experiment_identity_v1(phase1_plain)
    except CanonicalExperimentIdentityError as exc:
        message = str(exc)
        status = (
            STATUS_REJECTED_MISSING_DIMENSION
            if "must" in message.lower() and "complete" not in message.lower()
            else STATUS_REJECTED_INCOMPLETE_IDENTITY
        )
        if phase1_plain.get("completeness") != COMPLETENESS_COMPLETE:
            status = STATUS_REJECTED_INCOMPLETE_IDENTITY
        return _rejected(status, message, requested_mode=requested_mode)

    parent_digest = phase1_plain.get("identity_digest")
    integrity = phase1_plain.get("integrity")
    parent_integrity = integrity.get("content_sha256") if isinstance(integrity, Mapping) else None
    if not isinstance(parent_digest, str) or not parent_digest.strip():
        return _rejected(
            STATUS_REJECTED_MISSING_DIMENSION,
            "phase1 identity_digest missing",
            requested_mode=requested_mode,
        )
    if not isinstance(parent_integrity, str) or not parent_integrity.strip():
        return _rejected(
            STATUS_REJECTED_MISSING_DIMENSION,
            "phase1 integrity.content_sha256 missing",
            parent_digest=parent_digest,
            requested_mode=requested_mode,
        )

    try:
        validate_experiment_identity_manifest_v1(package_n_plain)
    except ExperimentIdentityManifestError as exc:
        return _rejected(
            STATUS_REJECTED_INVALID_PACKAGE_N,
            str(exc),
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )

    package_n_id = package_n_plain.get("experiment_identity_id")
    if not isinstance(package_n_id, str) or not package_n_id.strip():
        return _rejected(
            STATUS_REJECTED_MISSING_DIMENSION,
            "package_n experiment_identity_id missing",
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )
    if not is_package_n_sha256_canonical_id(package_n_id):
        return _rejected(
            STATUS_REJECTED_INVALID_PACKAGE_N,
            "package_n experiment_identity_id must be Package-N SHA256",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )
    if package_n_id == parent_digest:
        return _rejected(
            STATUS_REJECTED_AMBIGUOUS_IDENTITY,
            "Phase-1 identity_digest must remain distinct from Package-N experiment_identity_id",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )

    strategy_identity = phase1_plain.get("strategy_identity")
    package_n_strategy = _package_n_strategy_name(package_n_plain)
    if not isinstance(strategy_identity, str) or not strategy_identity.strip():
        return _rejected(
            STATUS_REJECTED_MISSING_DIMENSION,
            "phase1 strategy_identity missing",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )
    if package_n_strategy is None:
        return _rejected(
            STATUS_REJECTED_MISSING_DIMENSION,
            "package_n identity_config.strategy_name missing",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )
    if strategy_identity != package_n_strategy:
        return _rejected(
            STATUS_REJECTED_INCOMPATIBLE_DIMENSION,
            "strategy_identity is incompatible with package_n identity_config.strategy_name",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )

    if phase1_plain.get("schema_version") == package_n_plain.get("schema_version"):
        return _rejected(
            STATUS_REJECTED_AMBIGUOUS_IDENTITY,
            "Phase-1 and Package-N schema_version must remain distinct identity planes",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )
    if phase1_plain.get("identity_domain") == package_n_plain.get("identity_domain"):
        return _rejected(
            STATUS_REJECTED_AMBIGUOUS_IDENTITY,
            "Phase-1 and Package-N identity_domain must remain distinct identity planes",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )
    if phase1_plain.get("schema_version") != PHASE1_SCHEMA_VERSION:
        return _rejected(
            STATUS_REJECTED_INCOMPLETE_IDENTITY,
            "phase1 schema_version mismatch",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )
    if phase1_plain.get("identity_domain") != PHASE1_IDENTITY_DOMAIN:
        return _rejected(
            STATUS_REJECTED_INCOMPLETE_IDENTITY,
            "phase1 identity_domain mismatch",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )

    try:
        join = attach_i16_remaining_planes_join_v1(
            {
                "experiment_identity_id": package_n_id,
                "ref_id": package_n_id,
                "evidence_ref": parent_integrity,
                "content_sha256": parent_integrity,
            }
        )
    except I16RemainingPlanesJoinAttachmentError as exc:
        return _rejected(
            STATUS_REJECTED_INVALID_PACKAGE_N,
            f"I16 assessment attachment rejected: {exc}",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )
    if not isinstance(join, CrossLaneIdentityJoinV1):
        return _rejected(
            STATUS_REJECTED_INVALID_PACKAGE_N,
            "I16 assessment attachment did not return a join record",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )
    if join.experiment_identity_id != package_n_id:
        return _rejected(
            STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED,
            "I16 join mutated Package-N experiment_identity_id",
            package_n_id=package_n_id,
            parent_digest=parent_digest,
            parent_integrity=parent_integrity,
            requested_mode=requested_mode,
        )

    result = _build_result(
        status=STATUS_ADMITTED,
        rejection_reason=None,
        package_n_id=package_n_id,
        parent_digest=parent_digest,
        parent_integrity=parent_integrity,
        i16_assessment_consumable=True,
        i16_join=join.to_canonical_mapping(),
        requested_mode=requested_mode,
    )
    _LOGGER.info(
        "identity_admission status=%s package_n_id=%s parent_digest=%s apply_allowed=%s",
        STATUS_ADMITTED,
        package_n_id,
        parent_digest,
        PROMOTION_APPLY_ALLOWED,
    )
    return result


__all__ = [
    "ADMISSION_AUTHORITY",
    "ADMISSION_DOMAIN",
    "ADMISSION_PRESENT",
    "BOUNDED_AUTO_ALLOWED",
    "CanonicalIdentityToPackageNI16AdmissionError",
    "CanonicalIdentityToPackageNI16AdmissionRequestV1",
    "NON_PROJECTABLE_PHASE1_DIMENSIONS",
    "PROMOTION_APPLY_ALLOWED",
    "PROMOTION_AUTHORITY",
    "REQUIRED_PROMOTION_MODE",
    "RUNTIME_AUTHORITY_IMPACT",
    "SCHEMA_VERSION",
    "SELF_LEARNING_NOT_SELF_AUTHORIZING",
    "STATUS_ADMITTED",
    "STATUS_REJECTED_AMBIGUOUS_IDENTITY",
    "STATUS_REJECTED_AUTHORITY_BOUNDARY",
    "STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED",
    "STATUS_REJECTED_INCOMPATIBLE_DIMENSION",
    "STATUS_REJECTED_INCOMPLETE_IDENTITY",
    "STATUS_REJECTED_INVALID_PACKAGE_N",
    "STATUS_REJECTED_MISSING_DIMENSION",
    "STATUS_REJECTED_UNSUPPORTED_PROJECTION",
    "evaluate_canonical_experiment_identity_to_package_n_i16_promotion_admission_v1",
]
