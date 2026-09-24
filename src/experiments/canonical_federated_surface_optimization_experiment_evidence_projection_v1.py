"""Federated surface execution → M5-shaped optimization experiment evidence projection v1.

Evidence-only seam. Does not execute M4 plane, F1/F2 executors, promotion, or productive apply.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    ENVELOPE_CONTRACT_VERSION,
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    SCHEMA_VERSION as OPTIMIZABLE_ENVELOPE_SCHEMA_VERSION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    CLASS_CHALLENGER_EVIDENCE,
    CLASS_ECONOMIC_EVIDENCE,
    CLASS_FAILURE_EVIDENCE,
    CLASS_META_EVIDENCE_SOURCE_REF,
    CLASS_OOS_EVIDENCE,
    CLASS_ROBUSTNESS_EVIDENCE,
    CLASS_SEARCH_EVIDENCE,
    EVIDENCE_CLASS_OPTIMIZATION_EXPERIMENT,
    EXTERNAL_EFFECT_AUTHORIZED,
    OPTIMIZATION_EXPERIMENT_EVIDENCE_DOMAIN,
    OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    PROPOSAL_NOT_AUTHORITY,
    REQUIRED_EVIDENCE_CLASSES,
    SCHEMA_VERSION as M5_EVIDENCE_SCHEMA_VERSION,
    UNIVERSE_CLASS_OPTIMIZATION,
    validate_optimization_experiment_evidence_v1,
)
from src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1 import (
    list_test_ready_surface_ids_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = (
    "canonical_federated_surface_optimization_experiment_evidence_projection_v1"
)
PROJECTION_DOMAIN: Final[str] = (
    "peak_trade.canonical_federated_surface_optimization_experiment_evidence_projection.v1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/FEDERATED_SURFACE_OPTIMIZATION_EXPERIMENT_EVIDENCE_PROJECTION_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "federated_surface_optimization_experiment_evidence_projection_v1_decision_v1.json"
)

PROVENANCE_SOURCE: Final[str] = (
    "canonical_federated_surface_optimization_experiment_evidence_projection_v1"
)
SURFACE_EXECUTION_IDENTITY_DOMAIN: Final[str] = "peak_trade.federated_surface_execution_identity.v1"

PROJECTION_BINDING_SURFACE_NATIVE_REF_ONLY: Final[str] = "SURFACE_NATIVE_REF_ONLY"
SEMANTIC_STATUS_NOT_MAPPED: Final[str] = "NOT_MAPPED_FROM_SURFACE_EXECUTOR"
SEMANTIC_STATUS_EXPLICIT_REF: Final[str] = "EXPLICIT_SURFACE_NATIVE_REF"

EXECUTOR_OWNER_F1: Final[str] = (
    "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1."
    "runner_v1.run_max_age_parameter_research_execution_v1"
)
EXECUTOR_OWNER_F2: Final[str] = (
    "src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1."
    "run_f2_research_backtest_cost_grid_offline_v1"
)

M4_PLANE_EXECUTION: Final[bool] = False
PRODUCTIVE_TRADING_EFFECT: Final[str] = "NONE"
PROMOTION_PERFORMED: Final[bool] = False

_ALLOWED_EXPLICIT_SLICE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "surface_native_evidence_ref",
        "surface_native_evidence_digest",
        "semantic_status",
        "projection_binding",
        "surface_id",
        "notes",
    }
)

_LOGGER = logging.getLogger(__name__)


class FederatedSurfaceEvidenceProjectionError(ValueError):
    """Fail-closed federated surface evidence projection error."""


@dataclass(frozen=True)
class FederatedSurfaceEvidenceProjectionRequestV1:
    surface_id: str
    envelope_identity: str
    envelope_resolution_digest: str
    surface_execution_digest: str
    surface_native_evidence_ref: str
    surface_native_evidence_digest: str
    executor_semantic_owner: str
    repository_sha: str | None = None
    code_provenance: Mapping[str, Any] | None = None
    explicit_slice_bindings: Mapping[str, Mapping[str, Any]] | None = None
    explicit_candidate_experiment_id: str | None = None
    explicit_candidate_ref: str | None = None
    learning_evidence_digest: str | None = None


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def derive_surface_execution_identity_v1(
    *,
    surface_id: str,
    surface_execution_digest: str,
    envelope_identity: str,
) -> str:
    body = {
        "domain": SURFACE_EXECUTION_IDENTITY_DOMAIN,
        "surface_id": surface_id,
        "surface_execution_digest": surface_execution_digest,
        "envelope_identity": envelope_identity,
    }
    return compute_content_sha256(body)


def derive_federated_optimization_experiment_evidence_id_v1(
    *,
    surface_execution_identity: str,
) -> str:
    digest = hashlib.sha256(surface_execution_identity.encode("utf-8")).hexdigest()
    return f"opt.exp_ev.{digest[:40]}"


def _authorized_projection_surface_ids_v1() -> frozenset[str]:
    return frozenset(list_test_ready_surface_ids_v1())


def _default_slice_v1(
    *,
    evidence_class: str,
    surface_id: str,
    surface_native_evidence_ref: str,
    surface_native_evidence_digest: str,
) -> dict[str, Any]:
    return {
        "evidence_class": evidence_class,
        "projection_binding": PROJECTION_BINDING_SURFACE_NATIVE_REF_ONLY,
        "semantic_status": SEMANTIC_STATUS_NOT_MAPPED,
        "surface_id": surface_id,
        "surface_native_evidence_ref": surface_native_evidence_ref,
        "surface_native_evidence_digest": surface_native_evidence_digest,
    }


def _merge_explicit_slice_v1(
    base: dict[str, Any],
    explicit: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if explicit is None:
        return base
    unknown = frozenset(explicit.keys()) - _ALLOWED_EXPLICIT_SLICE_KEYS
    if unknown:
        raise FederatedSurfaceEvidenceProjectionError(
            f"EXPLICIT_SLICE_UNKNOWN_KEYS:{sorted(unknown)}"
        )
    ref = explicit.get("surface_native_evidence_ref")
    digest = explicit.get("surface_native_evidence_digest")
    if ref is not None and not str(ref).strip():
        raise FederatedSurfaceEvidenceProjectionError("EXPLICIT_SLICE_REF_EMPTY")
    if digest is not None and not is_valid_sha256_hex(str(digest)):
        raise FederatedSurfaceEvidenceProjectionError("EXPLICIT_SLICE_DIGEST_INVALID")
    merged = dict(base)
    merged.update({key: explicit[key] for key in explicit if key in _ALLOWED_EXPLICIT_SLICE_KEYS})
    if ref is not None or digest is not None:
        merged["semantic_status"] = SEMANTIC_STATUS_EXPLICIT_REF
    return merged


def _validate_request_v1(request: FederatedSurfaceEvidenceProjectionRequestV1) -> None:
    surface_id = request.surface_id.strip()
    if surface_id not in _authorized_projection_surface_ids_v1():
        raise FederatedSurfaceEvidenceProjectionError(
            f"SURFACE_NOT_AUTHORIZED_FOR_PROJECTION:{surface_id}"
        )

    if not is_valid_sha256_hex(request.envelope_identity):
        raise FederatedSurfaceEvidenceProjectionError("ENVELOPE_IDENTITY_INVALID")
    if not is_valid_sha256_hex(request.envelope_resolution_digest):
        raise FederatedSurfaceEvidenceProjectionError("ENVELOPE_RESOLUTION_DIGEST_INVALID")
    if not is_valid_sha256_hex(request.surface_execution_digest):
        raise FederatedSurfaceEvidenceProjectionError("SURFACE_EXECUTION_DIGEST_INVALID")
    if not is_valid_sha256_hex(request.surface_native_evidence_digest):
        raise FederatedSurfaceEvidenceProjectionError("SURFACE_NATIVE_EVIDENCE_DIGEST_INVALID")

    ref = request.surface_native_evidence_ref.strip()
    if not ref:
        raise FederatedSurfaceEvidenceProjectionError("SURFACE_NATIVE_EVIDENCE_REF_MISSING")

    owner = request.executor_semantic_owner.strip()
    if not owner:
        raise FederatedSurfaceEvidenceProjectionError("EXECUTOR_SEMANTIC_OWNER_MISSING")
    if surface_id == F1_SURFACE_ID and owner != EXECUTOR_OWNER_F1:
        raise FederatedSurfaceEvidenceProjectionError("F1_EXECUTOR_OWNER_MISMATCH")
    if surface_id == F2_SURFACE_ID and owner != EXECUTOR_OWNER_F2:
        raise FederatedSurfaceEvidenceProjectionError("F2_EXECUTOR_OWNER_MISMATCH")

    resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=surface_id)
    )
    if resolution.get("resolution") != RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION:
        raise FederatedSurfaceEvidenceProjectionError(
            f"ENVELOPE_RESOLUTION_NOT_AUTHORIZED:{resolution.get('reason')}"
        )
    resolved_identity = str(resolution.get("envelope_identity") or "")
    resolved_digest = str(resolution.get("result_digest") or "")
    if resolved_identity != request.envelope_identity:
        raise FederatedSurfaceEvidenceProjectionError("ENVELOPE_IDENTITY_MISMATCH")
    if resolved_digest != request.envelope_resolution_digest:
        raise FederatedSurfaceEvidenceProjectionError("ENVELOPE_RESOLUTION_DIGEST_MISMATCH")

    if request.explicit_slice_bindings is not None:
        for key in request.explicit_slice_bindings:
            if key not in REQUIRED_EVIDENCE_CLASSES:
                raise FederatedSurfaceEvidenceProjectionError(f"EXPLICIT_SLICE_CLASS_UNKNOWN:{key}")

    if request.learning_evidence_digest is not None and not is_valid_sha256_hex(
        request.learning_evidence_digest
    ):
        raise FederatedSurfaceEvidenceProjectionError("LEARNING_EVIDENCE_DIGEST_INVALID")

    if request.repository_sha is not None and not is_valid_sha256_hex(request.repository_sha):
        raise FederatedSurfaceEvidenceProjectionError("REPOSITORY_SHA_INVALID")


def build_federated_surface_optimization_experiment_evidence_projection_v1(
    request: FederatedSurfaceEvidenceProjectionRequestV1,
) -> MappingProxyType[str, Any]:
    """Project surface-native execution evidence into an M5-compatible evidence record."""
    _validate_request_v1(request)

    surface_id = request.surface_id.strip()
    surface_execution_identity = derive_surface_execution_identity_v1(
        surface_id=surface_id,
        surface_execution_digest=request.surface_execution_digest,
        envelope_identity=request.envelope_identity,
    )

    explicit = request.explicit_slice_bindings or {}
    ref = request.surface_native_evidence_ref.strip()
    native_digest = request.surface_native_evidence_digest

    def slice_for(class_name: str) -> dict[str, Any]:
        return _merge_explicit_slice_v1(
            _default_slice_v1(
                evidence_class=class_name,
                surface_id=surface_id,
                surface_native_evidence_ref=ref,
                surface_native_evidence_digest=native_digest,
            ),
            explicit.get(class_name),
        )

    evidence_slices = {
        CLASS_SEARCH_EVIDENCE: slice_for(CLASS_SEARCH_EVIDENCE),
        CLASS_CHALLENGER_EVIDENCE: slice_for(CLASS_CHALLENGER_EVIDENCE),
        CLASS_OOS_EVIDENCE: slice_for(CLASS_OOS_EVIDENCE),
        CLASS_ROBUSTNESS_EVIDENCE: slice_for(CLASS_ROBUSTNESS_EVIDENCE),
        CLASS_ECONOMIC_EVIDENCE: slice_for(CLASS_ECONOMIC_EVIDENCE),
        CLASS_FAILURE_EVIDENCE: slice_for(CLASS_FAILURE_EVIDENCE),
        CLASS_META_EVIDENCE_SOURCE_REF: {
            **_default_slice_v1(
                evidence_class=CLASS_META_EVIDENCE_SOURCE_REF,
                surface_id=surface_id,
                surface_native_evidence_ref=ref,
                surface_native_evidence_digest=native_digest,
            ),
            "meta_learning_ingest_status": "NOT_INGESTED_M6_DEFERRED",
            "capability_ref": PROJECTION_DOMAIN,
            "schema_version": SCHEMA_VERSION,
        },
    }

    version_bindings = {
        "federated_projection_schema_version": SCHEMA_VERSION,
        "optimizable_envelope_schema_version": OPTIMIZABLE_ENVELOPE_SCHEMA_VERSION,
        "optimizable_envelope_contract_version": ENVELOPE_CONTRACT_VERSION,
        "m5_evidence_schema_version": M5_EVIDENCE_SCHEMA_VERSION,
    }

    reproducibility_body = {
        "surface_execution_identity": surface_execution_identity,
        "surface_id": surface_id,
        "surface_execution_digest": request.surface_execution_digest,
        "surface_native_evidence_digest": native_digest,
        "envelope_identity": request.envelope_identity,
        "evidence_slices": evidence_slices,
        "version_bindings": version_bindings,
    }
    reproducibility_digest = compute_content_sha256(reproducibility_body)
    record_id = derive_federated_optimization_experiment_evidence_id_v1(
        surface_execution_identity=surface_execution_identity
    )

    provenance: dict[str, Any] = {
        "source": PROVENANCE_SOURCE,
        "projection_schema_version": SCHEMA_VERSION,
        "projection_domain": PROJECTION_DOMAIN,
        "decision_config_ref": DECISION_CONFIG,
        "normative_spec_ref": NORMATIVE_SPEC,
        "surface_id": surface_id,
        "surface_execution_identity": surface_execution_identity,
        "surface_execution_digest": request.surface_execution_digest,
        "surface_native_evidence_ref": ref,
        "surface_native_evidence_digest": native_digest,
        "executor_semantic_owner": request.executor_semantic_owner.strip(),
        "m4_plane_execution": M4_PLANE_EXECUTION,
        "envelope_identity": request.envelope_identity,
        "envelope_resolution_digest": request.envelope_resolution_digest,
    }
    if request.repository_sha:
        provenance["repository_sha"] = request.repository_sha
    if request.code_provenance is not None:
        provenance["code_provenance"] = _json_safe(request.code_provenance)

    canonical: dict[str, Any] = {
        "schema_version": M5_EVIDENCE_SCHEMA_VERSION,
        "domain": OPTIMIZATION_EXPERIMENT_EVIDENCE_DOMAIN,
        "record_id": record_id,
        "universe_class": UNIVERSE_CLASS_OPTIMIZATION,
        "evidence_class": EVIDENCE_CLASS_OPTIMIZATION_EXPERIMENT,
        "surface_execution_identity": surface_execution_identity,
        "source_projection_schema_version": SCHEMA_VERSION,
        "envelope_resolution_digest": request.envelope_resolution_digest,
        "version_bindings": version_bindings,
        "evidence_slices": evidence_slices,
        "provenance": provenance,
        "reproducibility_digest": reproducibility_digest,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "proposal_not_authority": PROPOSAL_NOT_AUTHORITY,
        "learning_state_mutation": False,
        "meta_learning_ingest": False,
        "federated_projection": True,
        "m4_plane_identity_omitted_by_contract": True,
    }
    if request.learning_evidence_digest:
        canonical["learning_evidence_digest"] = request.learning_evidence_digest
    if request.explicit_candidate_experiment_id:
        canonical["candidate_experiment_id"] = request.explicit_candidate_experiment_id
    if request.explicit_candidate_ref:
        canonical["candidate_ref"] = request.explicit_candidate_ref

    canonical["content_hash"] = compute_content_sha256(
        _json_safe({key: value for key, value in canonical.items() if key != "content_hash"})
    )

    validated = validate_optimization_experiment_evidence_v1(canonical)
    validate_federated_projected_optimization_experiment_evidence_v1(validated)
    _LOGGER.debug(
        "federated projection built surface_id=%s record_id=%s",
        surface_id,
        record_id,
    )
    return validated


def validate_federated_projected_optimization_experiment_evidence_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    """Fail-closed federated extension checks on top of M5 validation."""
    record = validate_optimization_experiment_evidence_v1(payload)
    if record.get("plane_identity") is not None:
        raise FederatedSurfaceEvidenceProjectionError(
            "PLANE_IDENTITY_FORBIDDEN_ON_FEDERATED_RECORD"
        )
    if record.get("source_plane_schema_version") is not None:
        raise FederatedSurfaceEvidenceProjectionError(
            "SOURCE_PLANE_SCHEMA_VERSION_FORBIDDEN_ON_FEDERATED_RECORD"
        )
    surface_execution_identity = str(record.get("surface_execution_identity") or "")
    if not is_valid_sha256_hex(surface_execution_identity):
        raise FederatedSurfaceEvidenceProjectionError("SURFACE_EXECUTION_IDENTITY_INVALID")
    provenance = record.get("provenance")
    if not isinstance(provenance, Mapping):
        raise FederatedSurfaceEvidenceProjectionError("PROVENANCE_MISSING")
    if provenance.get("source") != PROVENANCE_SOURCE:
        raise FederatedSurfaceEvidenceProjectionError("PROVENANCE_SOURCE_MISMATCH")
    if provenance.get("m4_plane_execution") is not False:
        raise FederatedSurfaceEvidenceProjectionError("M4_PLANE_EXECUTION_MUST_BE_FALSE")
    if record.get("federated_projection") is not True:
        raise FederatedSurfaceEvidenceProjectionError("FEDERATED_PROJECTION_FLAG_REQUIRED")
    return MappingProxyType(dict(record))


def bind_f1_surface_execution_projection_request_v1(
    f1_execution_result: Mapping[str, Any],
    *,
    surface_native_evidence_ref: str,
    surface_native_evidence_digest: str,
    envelope_identity: str,
    envelope_resolution_digest: str,
) -> FederatedSurfaceEvidenceProjectionRequestV1:
    """Build projection request from F1 runner output (no executor invocation)."""
    execution_id = str(f1_execution_result.get("execution_id") or "")
    if not execution_id:
        raise FederatedSurfaceEvidenceProjectionError("F1_EXECUTION_ID_MISSING")
    repository_sha = f1_execution_result.get("repository_sha")
    sha_str = str(repository_sha) if repository_sha else None
    if sha_str and not is_valid_sha256_hex(sha_str):
        raise FederatedSurfaceEvidenceProjectionError("F1_REPOSITORY_SHA_INVALID")

    surface_execution_digest = compute_content_sha256(
        {
            "surface_id": F1_SURFACE_ID,
            "execution_id": execution_id,
            "repository_sha": sha_str,
            "candidate_domain_digest": f1_execution_result.get("candidate_domain_digest"),
            "input_evidence_manifest_digest": f1_execution_result.get(
                "input_evidence_manifest_digest"
            ),
        }
    )
    return FederatedSurfaceEvidenceProjectionRequestV1(
        surface_id=F1_SURFACE_ID,
        envelope_identity=envelope_identity,
        envelope_resolution_digest=envelope_resolution_digest,
        surface_execution_digest=surface_execution_digest,
        surface_native_evidence_ref=surface_native_evidence_ref,
        surface_native_evidence_digest=surface_native_evidence_digest,
        executor_semantic_owner=EXECUTOR_OWNER_F1,
        repository_sha=sha_str,
        code_provenance=None,
        explicit_slice_bindings=None,
        explicit_candidate_experiment_id=None,
        explicit_candidate_ref=None,
        learning_evidence_digest=None,
    )


def bind_f2_surface_execution_projection_request_v1(
    f2_execution_result: Mapping[str, Any],
    *,
    surface_native_evidence_ref: str,
    envelope_identity: str,
    envelope_resolution_digest: str,
    explicit_slice_bindings: Mapping[str, Mapping[str, Any]] | None = None,
) -> FederatedSurfaceEvidenceProjectionRequestV1:
    """Build projection request from F2 runner output (no executor invocation)."""
    execution_digest = str(f2_execution_result.get("execution_digest") or "")
    if not is_valid_sha256_hex(execution_digest):
        raise FederatedSurfaceEvidenceProjectionError("F2_EXECUTION_DIGEST_INVALID")

    bundle = f2_execution_result.get("required_evidence_materialization") or {}
    bundle_digest = str(bundle.get("evidence_bundle_digest") or "")
    if is_valid_sha256_hex(bundle_digest):
        native_digest = bundle_digest
    else:
        native_digest = execution_digest

    code_provenance = f2_execution_result.get("code_provenance")
    repo_sha = None
    if isinstance(code_provenance, Mapping):
        git_sha = code_provenance.get("git_sha")
        if git_sha and is_valid_sha256_hex(str(git_sha)):
            repo_sha = str(git_sha)

    return FederatedSurfaceEvidenceProjectionRequestV1(
        surface_id=F2_SURFACE_ID,
        envelope_identity=envelope_identity,
        envelope_resolution_digest=envelope_resolution_digest,
        surface_execution_digest=execution_digest,
        surface_native_evidence_ref=surface_native_evidence_ref,
        surface_native_evidence_digest=native_digest,
        executor_semantic_owner=EXECUTOR_OWNER_F2,
        repository_sha=repo_sha,
        code_provenance=code_provenance if isinstance(code_provenance, Mapping) else None,
        explicit_slice_bindings=explicit_slice_bindings,
        explicit_candidate_experiment_id=None,
        explicit_candidate_ref=None,
        learning_evidence_digest=None,
    )


__all__ = [
    "DECISION_CONFIG",
    "EXECUTOR_OWNER_F1",
    "EXECUTOR_OWNER_F2",
    "FederatedSurfaceEvidenceProjectionError",
    "FederatedSurfaceEvidenceProjectionRequestV1",
    "M4_PLANE_EXECUTION",
    "NORMATIVE_SPEC",
    "PROJECTION_DOMAIN",
    "SCHEMA_VERSION",
    "bind_f1_surface_execution_projection_request_v1",
    "bind_f2_surface_execution_projection_request_v1",
    "build_federated_surface_optimization_experiment_evidence_projection_v1",
    "derive_federated_optimization_experiment_evidence_id_v1",
    "derive_surface_execution_identity_v1",
    "validate_federated_projected_optimization_experiment_evidence_v1",
]
