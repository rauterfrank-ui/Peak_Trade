"""Identity-bound offline observation binding from existing observation owners.

Binds Phase-10 caller-supplied observations to a Phase-1 COMPLETE identity and
writes a Phase-2 immutable experiment-memory record. Does not invent identity,
run a research loop, apply promotions, or grant runtime authority.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_experiment_identity_v1 import (
    COMPLETENESS_COMPLETE,
    CanonicalExperimentIdentityError,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_experiment_memory_v1 import (
    CanonicalExperimentMemoryRecordRequestV1,
    ExperimentMemoryValidationError,
    ExperimentRecordConflictError,
    REF_KIND_IDENTITY_DIGEST_BOUND,
    build_canonical_experiment_memory_record_v1,
    derive_experiment_id_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "canonical_identity_bound_offline_observation_binding_v1"
BINDING_DOMAIN: Final[str] = "peak_trade.canonical_identity_bound_offline_observation_binding.v1"
BINDING_PRESENT: Final[bool] = True
BINDING_AUTHORITY: Final[str] = "RESEARCH_EVIDENCE_ONLY"
PROMOTION_AUTHORITY: Final[str] = "NONE"
PROMOTION_APPLY_ALLOWED: Final[bool] = False
BOUNDED_AUTO_ALLOWED: Final[bool] = False
NEW_RUNNER_ARCHITECTURE: Final[bool] = False
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"
SELF_LEARNING_NOT_SELF_AUTHORIZING: Final[bool] = True

OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1: Final[str] = (
    "OFFLINE_EXPERIMENT_OBSERVATIONS_V1"
)
ALLOWED_OBSERVATION_OWNERS: Final[frozenset[str]] = frozenset(
    {OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1}
)
DISPOSITION_RESEARCH_ONLY: Final[str] = "RESEARCH_ONLY"
COMPARISON_STATUS_NOT_COMPARED: Final[str] = "NOT_COMPARED"
CANDIDATE_ROLE_RESEARCH: Final[str] = "RESEARCH"

STATUS_BOUND: Final[str] = "BOUND"
STATUS_REJECTED_MISSING_DIMENSION: Final[str] = "REJECTED_MISSING_DIMENSION"
STATUS_REJECTED_INCOMPATIBLE_DIMENSION: Final[str] = "REJECTED_INCOMPATIBLE_DIMENSION"
STATUS_REJECTED_INCOMPLETE_IDENTITY: Final[str] = "REJECTED_INCOMPLETE_IDENTITY"
STATUS_REJECTED_IDENTITY_MISMATCH: Final[str] = "REJECTED_IDENTITY_MISMATCH"
STATUS_REJECTED_EXPERIMENT_ID_MISMATCH: Final[str] = "REJECTED_EXPERIMENT_ID_MISMATCH"
STATUS_REJECTED_LINEAGE_DIGEST_MISMATCH: Final[str] = "REJECTED_LINEAGE_DIGEST_MISMATCH"
STATUS_REJECTED_WRONG_OBSERVATION_OWNER: Final[str] = "REJECTED_WRONG_OBSERVATION_OWNER"
STATUS_REJECTED_DIVERGENT_DUPLICATE: Final[str] = "REJECTED_DIVERGENT_DUPLICATE"
STATUS_REJECTED_UNSUPPORTED_PROJECTION: Final[str] = "REJECTED_UNSUPPORTED_PROJECTION"
STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED: Final[str] = (
    "REJECTED_HASH_REINTERPRETATION_REQUIRED"
)
STATUS_REJECTED_AUTHORITY_BOUNDARY: Final[str] = "REJECTED_AUTHORITY_BOUNDARY"

_LOGGER = logging.getLogger(__name__)


class CanonicalIdentityBoundOfflineObservationBindingError(ValueError):
    """Fail-closed malformed observation-binding request error."""


@dataclass(frozen=True)
class CanonicalIdentityBoundOfflineObservationBindingRequestV1:
    phase1_identity: Mapping[str, Any] | None
    observation_owner: str
    observations: Any
    claimed_identity_digest: str | None
    claimed_experiment_id: str | None
    claimed_parent_lineage_ref: str | None
    hypothesis_id: str
    hypothesis_fingerprint: str
    strategy_family: str
    created_at: str
    parent_experiment: str | None = None
    candidate_role: str = CANDIDATE_ROLE_RESEARCH
    disposition: str = DISPOSITION_RESEARCH_ONLY
    rejection_reason: str | None = None
    claimed_dataset_digest: str | None = None
    claimed_cost_model_digest: str | None = None
    claimed_risk_policy_digest: str | None = None
    claimed_portfolio_digest: str | None = None
    claimed_legacy_is_phase1_complete: bool = False
    claimed_recomputed_identity_digest: str | None = None
    claimed_recomputed_experiment_id: str | None = None
    requested_apply: bool = False
    requested_bounded_auto: bool = False
    experiment_memory_store: CanonicalExperimentMemoryStoreV1 | None = None


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_freeze(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _plain_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_mapping(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_mapping(item) for item in value]
    if isinstance(value, tuple):
        return [_plain_mapping(item) for item in value]
    return value


def _authority_invariants() -> dict[str, Any]:
    return {
        "binding_authority": BINDING_AUTHORITY,
        "bounded_auto_allowed": BOUNDED_AUTO_ALLOWED,
        "bounded_auto_effect": False,
        "promotion_apply_allowed": PROMOTION_APPLY_ALLOWED,
        "promotion_apply_effect": False,
        "promotion_authority": PROMOTION_AUTHORITY,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "runtime_authority_effect": False,
        "new_runner_architecture": NEW_RUNNER_ARCHITECTURE,
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
    observation_owner: str,
    identity_digest: str | None,
    experiment_id: str | None,
    parent_lineage_ref: str | None,
    identity_bound_observation: Mapping[str, Any] | None,
    experiment_record: Mapping[str, Any] | None,
    persisted_experiment_id: str | None,
) -> Mapping[str, Any]:
    bound = status == STATUS_BOUND
    body = {
        "schema_version": SCHEMA_VERSION,
        "binding_domain": BINDING_DOMAIN,
        "binding_present": BINDING_PRESENT,
        "status": status,
        "rejection_reason": rejection_reason,
        "observation_owner": observation_owner,
        "allowed_observation_owners": sorted(ALLOWED_OBSERVATION_OWNERS),
        "identity_digest": identity_digest,
        "experiment_id": experiment_id,
        "parent_lineage_ref": parent_lineage_ref,
        "identity_bound_observation": (
            None if identity_bound_observation is None else dict(identity_bound_observation)
        ),
        "experiment_record": (
            None if experiment_record is None else _plain_mapping(experiment_record)
        ),
        "persist": {"experiment_record_id": persisted_experiment_id},
        "identity_reinterpreted": False,
        "experiment_id_reinterpreted": False,
        "package_n_experiment_identity_id_mutated": False,
        "hash_reinterpreted": False,
        "phase10_runtime_authority": False,
        "authority_invariants": _authority_invariants(),
        "bound": bound,
    }
    body["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in body.items() if key != "integrity"}
        )
    }
    return MappingProxyType(_freeze(body))


def _rejected(
    status: str,
    reason: str,
    *,
    observation_owner: str = "",
    identity_digest: str | None = None,
    experiment_id: str | None = None,
    parent_lineage_ref: str | None = None,
) -> Mapping[str, Any]:
    return _build_result(
        status=status,
        rejection_reason=reason,
        observation_owner=observation_owner,
        identity_digest=identity_digest,
        experiment_id=experiment_id,
        parent_lineage_ref=parent_lineage_ref,
        identity_bound_observation=None,
        experiment_record=None,
        persisted_experiment_id=None,
    )


def _parent_lineage_ref(identity: Mapping[str, Any]) -> str | None:
    parent_lineage = identity.get("parent_lineage")
    if not isinstance(parent_lineage, Mapping):
        return None
    value = parent_lineage.get("parent_lineage_ref")
    return value if isinstance(value, str) else None


def _observation_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        payload = _plain_mapping(value)
    else:
        required = ("metrics", "robustness_results", "regime_results", "artifacts")
        if not all(hasattr(value, field) for field in required):
            raise CanonicalIdentityBoundOfflineObservationBindingError(
                "observations must be OfflineExperimentObservationsV1 or a mapping"
            )
        payload = {
            "metrics": getattr(value, "metrics"),
            "robustness_results": getattr(value, "robustness_results"),
            "regime_results": getattr(value, "regime_results"),
            "artifacts": getattr(value, "artifacts"),
        }
    for field_name in ("metrics", "robustness_results", "regime_results"):
        if not isinstance(payload.get(field_name), Mapping):
            raise CanonicalIdentityBoundOfflineObservationBindingError(
                f"observations.{field_name} must be a mapping"
            )
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, (list, tuple)):
        raise CanonicalIdentityBoundOfflineObservationBindingError(
            "observations.artifacts must be a sequence"
        )
    return {
        "metrics": dict(payload["metrics"]),
        "robustness_results": dict(payload["robustness_results"]),
        "regime_results": dict(payload["regime_results"]),
        "artifacts": list(artifacts),
    }


def _bound_ref(digest: str) -> dict[str, str]:
    return {"digest": digest, "kind": REF_KIND_IDENTITY_DIGEST_BOUND}


def _optional_sha256_claim(field_name: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise CanonicalIdentityBoundOfflineObservationBindingError(
            f"{field_name} must be a sha256 hex digest"
        )
    return value


def bind_canonical_identity_bound_offline_observation_v1(
    request: CanonicalIdentityBoundOfflineObservationBindingRequestV1,
) -> Mapping[str, Any]:
    """Bind allowed observations to Phase-1 COMPLETE identity and Phase-2 memory."""
    owner = request.observation_owner
    if request.requested_apply is True:
        return _rejected(
            STATUS_REJECTED_AUTHORITY_BOUNDARY,
            "requested_apply is forbidden; binding is not promotion apply",
            observation_owner=owner,
        )
    if request.requested_bounded_auto is True:
        return _rejected(
            STATUS_REJECTED_AUTHORITY_BOUNDARY,
            "requested_bounded_auto is forbidden; binding has no bounded_auto capability",
            observation_owner=owner,
        )
    if request.claimed_legacy_is_phase1_complete is True:
        return _rejected(
            STATUS_REJECTED_UNSUPPORTED_PROJECTION,
            "legacy or Package-N records cannot be claimed as Phase-1 COMPLETE",
            observation_owner=owner,
        )
    if request.claimed_recomputed_identity_digest is not None:
        return _rejected(
            STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED,
            "Phase-1 identity_digest must not be recomputed or reinterpreted",
            observation_owner=owner,
        )
    if request.claimed_recomputed_experiment_id is not None:
        return _rejected(
            STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED,
            "Phase-2 experiment_id must not be recomputed or reinterpreted",
            observation_owner=owner,
        )
    if owner not in ALLOWED_OBSERVATION_OWNERS:
        return _rejected(
            STATUS_REJECTED_WRONG_OBSERVATION_OWNER,
            "observation_owner is not the existing Phase-10 observation owner",
            observation_owner=owner,
        )
    if request.phase1_identity is None:
        return _rejected(
            STATUS_REJECTED_MISSING_DIMENSION,
            "phase1_identity is required",
            observation_owner=owner,
        )
    if not isinstance(request.phase1_identity, Mapping):
        raise CanonicalIdentityBoundOfflineObservationBindingError(
            "phase1_identity must be a mapping"
        )

    phase1_plain = _plain_mapping(request.phase1_identity)
    try:
        validate_canonical_experiment_identity_v1(phase1_plain)
    except CanonicalExperimentIdentityError as exc:
        status = STATUS_REJECTED_INCOMPLETE_IDENTITY
        if phase1_plain.get("completeness") == COMPLETENESS_COMPLETE and "must" in str(exc).lower():
            status = STATUS_REJECTED_MISSING_DIMENSION
        if phase1_plain.get("completeness") != COMPLETENESS_COMPLETE:
            status = STATUS_REJECTED_INCOMPLETE_IDENTITY
        return _rejected(status, str(exc), observation_owner=owner)

    identity_digest = phase1_plain.get("identity_digest")
    if not isinstance(identity_digest, str) or not is_valid_sha256_hex(identity_digest):
        return _rejected(
            STATUS_REJECTED_MISSING_DIMENSION,
            "phase1 identity_digest missing",
            observation_owner=owner,
        )
    experiment_id = derive_experiment_id_v1(identity_digest)
    parent_lineage_ref = _parent_lineage_ref(phase1_plain)

    if request.claimed_identity_digest is None:
        return _rejected(
            STATUS_REJECTED_MISSING_DIMENSION,
            "claimed_identity_digest is required",
            observation_owner=owner,
            identity_digest=identity_digest,
            experiment_id=experiment_id,
            parent_lineage_ref=parent_lineage_ref,
        )
    if request.claimed_identity_digest != identity_digest:
        return _rejected(
            STATUS_REJECTED_IDENTITY_MISMATCH,
            "claimed_identity_digest does not match Phase-1 identity_digest",
            observation_owner=owner,
            identity_digest=identity_digest,
            experiment_id=experiment_id,
            parent_lineage_ref=parent_lineage_ref,
        )
    if request.claimed_experiment_id is None:
        return _rejected(
            STATUS_REJECTED_MISSING_DIMENSION,
            "claimed_experiment_id is required",
            observation_owner=owner,
            identity_digest=identity_digest,
            experiment_id=experiment_id,
            parent_lineage_ref=parent_lineage_ref,
        )
    if request.claimed_experiment_id != experiment_id:
        return _rejected(
            STATUS_REJECTED_EXPERIMENT_ID_MISMATCH,
            "claimed_experiment_id is not bound to the Phase-1 identity digest",
            observation_owner=owner,
            identity_digest=identity_digest,
            experiment_id=experiment_id,
            parent_lineage_ref=parent_lineage_ref,
        )
    if request.claimed_parent_lineage_ref != parent_lineage_ref:
        return _rejected(
            STATUS_REJECTED_LINEAGE_DIGEST_MISMATCH,
            "claimed_parent_lineage_ref does not match Phase-1 parent_lineage_ref",
            observation_owner=owner,
            identity_digest=identity_digest,
            experiment_id=experiment_id,
            parent_lineage_ref=parent_lineage_ref,
        )

    digest_claims = (
        ("claimed_dataset_digest", "dataset_digest"),
        ("claimed_cost_model_digest", "cost_model_digest"),
        ("claimed_risk_policy_digest", "risk_policy_digest"),
        ("claimed_portfolio_digest", "portfolio_digest"),
    )
    for claim_field, identity_field in digest_claims:
        claimed = _optional_sha256_claim(claim_field, getattr(request, claim_field))
        if claimed is None:
            continue
        expected = phase1_plain.get(identity_field)
        if claimed != expected:
            return _rejected(
                STATUS_REJECTED_LINEAGE_DIGEST_MISMATCH,
                f"{claim_field} does not match Phase-1 {identity_field}",
                observation_owner=owner,
                identity_digest=identity_digest,
                experiment_id=experiment_id,
                parent_lineage_ref=parent_lineage_ref,
            )

    observations = _observation_mapping(request.observations)
    identity_bound_observation = {
        "artifacts": observations["artifacts"],
        "experiment_id": experiment_id,
        "identity_digest": identity_digest,
        "metrics": observations["metrics"],
        "observation_owner": owner,
        "parent_lineage_ref": parent_lineage_ref,
        "regime_results": observations["regime_results"],
        "robustness_results": observations["robustness_results"],
    }
    try:
        experiment_record = build_canonical_experiment_memory_record_v1(
            CanonicalExperimentMemoryRecordRequestV1(
                experiment_identity=phase1_plain,
                hypothesis_id=request.hypothesis_id,
                hypothesis_fingerprint=request.hypothesis_fingerprint,
                parent_experiment=request.parent_experiment,
                strategy_family=request.strategy_family,
                candidate_role=request.candidate_role,
                dataset_ref=_bound_ref(str(phase1_plain["dataset_digest"])),
                cost_model_ref=_bound_ref(str(phase1_plain["cost_model_digest"])),
                risk_policy_ref=_bound_ref(str(phase1_plain["risk_policy_digest"])),
                portfolio_ref=_bound_ref(str(phase1_plain["portfolio_digest"])),
                metrics=observations["metrics"],
                robustness_results=observations["robustness_results"],
                regime_results=observations["regime_results"],
                comparison_status=COMPARISON_STATUS_NOT_COMPARED,
                disposition=request.disposition,
                rejection_reason=request.rejection_reason,
                created_at=request.created_at,
                artifacts=observations["artifacts"],
                experiment_id=experiment_id,
            )
        )
    except ExperimentMemoryValidationError as exc:
        return _rejected(
            STATUS_REJECTED_INCOMPATIBLE_DIMENSION,
            str(exc),
            observation_owner=owner,
            identity_digest=identity_digest,
            experiment_id=experiment_id,
            parent_lineage_ref=parent_lineage_ref,
        )

    persisted_id: str | None = None
    if request.experiment_memory_store is not None:
        try:
            stored = request.experiment_memory_store.append(experiment_record)
        except ExperimentRecordConflictError as exc:
            return _rejected(
                STATUS_REJECTED_DIVERGENT_DUPLICATE,
                str(exc),
                observation_owner=owner,
                identity_digest=identity_digest,
                experiment_id=experiment_id,
                parent_lineage_ref=parent_lineage_ref,
            )
        persisted_id = str(stored["experiment_id"])

    result = _build_result(
        status=STATUS_BOUND,
        rejection_reason=None,
        observation_owner=owner,
        identity_digest=identity_digest,
        experiment_id=experiment_id,
        parent_lineage_ref=parent_lineage_ref,
        identity_bound_observation=identity_bound_observation,
        experiment_record=experiment_record,
        persisted_experiment_id=persisted_id,
    )
    _LOGGER.info(
        "identity_bound_offline_observation status=%s experiment_id=%s owner=%s apply=%s",
        STATUS_BOUND,
        experiment_id,
        owner,
        PROMOTION_APPLY_ALLOWED,
    )
    return result


__all__ = [
    "ALLOWED_OBSERVATION_OWNERS",
    "BINDING_AUTHORITY",
    "BINDING_DOMAIN",
    "BINDING_PRESENT",
    "BOUNDED_AUTO_ALLOWED",
    "CanonicalIdentityBoundOfflineObservationBindingError",
    "CanonicalIdentityBoundOfflineObservationBindingRequestV1",
    "NEW_RUNNER_ARCHITECTURE",
    "OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1",
    "PROMOTION_APPLY_ALLOWED",
    "PROMOTION_AUTHORITY",
    "RUNTIME_AUTHORITY_IMPACT",
    "SCHEMA_VERSION",
    "SELF_LEARNING_NOT_SELF_AUTHORIZING",
    "STATUS_BOUND",
    "STATUS_REJECTED_AUTHORITY_BOUNDARY",
    "STATUS_REJECTED_DIVERGENT_DUPLICATE",
    "STATUS_REJECTED_EXPERIMENT_ID_MISMATCH",
    "STATUS_REJECTED_HASH_REINTERPRETATION_REQUIRED",
    "STATUS_REJECTED_IDENTITY_MISMATCH",
    "STATUS_REJECTED_INCOMPATIBLE_DIMENSION",
    "STATUS_REJECTED_INCOMPLETE_IDENTITY",
    "STATUS_REJECTED_LINEAGE_DIGEST_MISMATCH",
    "STATUS_REJECTED_MISSING_DIMENSION",
    "STATUS_REJECTED_UNSUPPORTED_PROJECTION",
    "STATUS_REJECTED_WRONG_OBSERVATION_OWNER",
    "bind_canonical_identity_bound_offline_observation_v1",
]
