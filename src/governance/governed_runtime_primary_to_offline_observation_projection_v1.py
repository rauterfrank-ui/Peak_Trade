"""Governed runtime-primary → offline observation projection v1 (Owner GO; authority=NONE).

Projects preexisting durable Paper/Shadow/Testnet primary evidence into
OfflineExperimentObservationsV1 and runtime learning ingress contracts only.
Does not execute Paper/Shadow/Testnet, mutate primary archives, or grant apply authority.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS,
    BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
    MANIFEST_FILENAME,
    PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    is_under_tmp,
    validate_durable_primary_evidence_root,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.experiments.canonical_automated_offline_research_loop_v1 import (
    OfflineExperimentObservationsV1,
)
from src.experiments.canonical_identity_bound_offline_observation_binding_v1 import (
    CanonicalIdentityBoundOfflineObservationBindingRequestV1,
    OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1,
    STATUS_BOUND,
    bind_canonical_identity_bound_offline_observation_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    EvidenceFieldBinding,
    RuntimeObservationBundleInput,
    RuntimeToLearningInputRequest,
    build_runtime_observation_bundle_v1,
    build_runtime_to_learning_input_v1,
    verify_source_evidence_bundle,
)

SCHEMA_VERSION: Final[str] = "governed_runtime_primary_to_offline_observation_projection_v1"
WORKPACKAGE_ID: Final[str] = "GOVERNED_RUNTIME_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/GOVERNED_RUNTIME_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/governed_runtime_primary_to_offline_observation_projection_v1_decision_v1.json"
)
FIELD_MAPPING_LEDGER: Final[str] = (
    "config/governance/"
    "governed_runtime_primary_to_offline_observation_projection_v1_field_mapping_ledger_v1.json"
)

PROJECTION_ARTIFACT_REL: Final[str] = (
    "governed_runtime_primary_offline_observation_projection_v1.json"
)
PROJECTION_STAGING_PREFIX: Final[str] = ".g2_primary_offline_projection_staging_"

PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION: Final[bool] = False
P5_EVIDENCE_INTAKE_IMPLIES_PRODUCTIVE_AUTHORIZATION: Final[bool] = False
P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY: Final[bool] = False
RUNTIME_APPLY_STARTED: Final[bool] = False
REAL_RUNTIME_MATERIALIZATION_PERFORMED: Final[bool] = False
PRODUCTIVE_CONFIGURATION_MUTATED: Final[bool] = False
PRODUCTIVE_ACTIVATION_AUTHORIZED: Final[bool] = False
M11_STARTED: Final[bool] = False
EXTERNAL_EFFECT: Final[bool] = False

OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
META_LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
TRADING_SELECTION_EFFECT: Final[str] = "NONE"
TRADING_DECISION_AUTHORITY_CHANGE: Final[str] = "NONE"
RISK_AUTHORITY_CHANGE: Final[str] = "NONE"
PROMOTION_AUTHORITY_CHANGE: Final[str] = "NONE"
RUNTIME_APPLY_AUTHORITY_CHANGE: Final[str] = "NONE"

CROSS_MODE_NORMALIZATION_STATUS: Final[str] = "PARTIAL_CURRENT"

_ENV_BY_MODE: Final[dict[str, str]] = {
    "PAPER": "PAPER_BOUNDED_OBSERVATION",
    "SHADOW": "SHADOW_BOUNDED_OBSERVATION",
    "TESTNET": "TESTNET_BOUNDED_OBSERVATION",
}

_REPO_ROOT = Path(__file__).resolve().parents[2]

_REQUIRED_PATHS_BY_MODE: Final[dict[str, tuple[str, ...]]] = {
    "PAPER": PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    "SHADOW": BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS,
    "TESTNET": BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS,
}


class RuntimePrimarySourceModeV1(str, Enum):
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    TESTNET = "TESTNET"


class GovernedRuntimePrimaryProjectionError(ValueError):
    """Fail-closed projection error."""


@dataclass(frozen=True)
class RuntimePrimaryProvenanceBindingV1:
    source_execution_mode: str
    source_run_session_identity: str
    source_archive_root_ref: str
    primary_evidence_manifest_digest: str
    runtime_out_evidence_manifest_digest: str | None
    wrapper_evidence_manifest_digest: str | None
    observation_time_utc: str
    instrument_identity: str
    venue_identity: str
    trading_epoch: int
    strategy_config_identity: str
    repository_code_provenance: str
    review_verdict: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "instrument_identity": self.instrument_identity,
            "observation_time_utc": self.observation_time_utc,
            "primary_evidence_manifest_digest": self.primary_evidence_manifest_digest,
            "repository_code_provenance": self.repository_code_provenance,
            "review_verdict": self.review_verdict,
            "runtime_out_evidence_manifest_digest": self.runtime_out_evidence_manifest_digest,
            "source_archive_root_ref": self.source_archive_root_ref,
            "source_execution_mode": self.source_execution_mode,
            "source_run_session_identity": self.source_run_session_identity,
            "strategy_config_identity": self.strategy_config_identity,
            "trading_epoch": self.trading_epoch,
            "venue_identity": self.venue_identity,
            "wrapper_evidence_manifest_digest": self.wrapper_evidence_manifest_digest,
        }


@dataclass(frozen=True)
class GovernedRuntimePrimaryProjectionRequestV1:
    source_mode: RuntimePrimarySourceModeV1
    primary_evidence_root: Path
    phase1_identity: Mapping[str, Any]
    hypothesis_id: str
    hypothesis_fingerprint: str
    strategy_family: str
    created_at: str
    claimed_identity_digest: str
    claimed_experiment_id: str
    claimed_parent_lineage_ref: str | None = None
    start_runtime_execution: bool = False
    request_promotion: bool = False
    request_runtime_apply: bool = False
    request_external_effect: bool = False


@dataclass(frozen=True)
class GovernedRuntimePrimaryProjectionResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    provenance: RuntimePrimaryProvenanceBindingV1 | None
    offline_observations: OfflineExperimentObservationsV1 | None
    identity_binding_status: str | None
    runtime_observation_bundle: dict[str, Any] | None
    runtime_learning_input: dict[str, Any] | None
    projection_record_digest: str | None
    lineage_chain: tuple[str, ...] = field(default_factory=tuple)


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_relative_ref(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        raise GovernedRuntimePrimaryProjectionError(
            "PRIMARY_EVIDENCE_ROOT_OUTSIDE_REPO_FOR_ARTIFACT_REF"
        ) from None


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise GovernedRuntimePrimaryProjectionError(f"missing {label}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GovernedRuntimePrimaryProjectionError(f"invalid JSON in {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise GovernedRuntimePrimaryProjectionError(f"{label} must be a JSON object")
    return payload


def _require_non_empty_str(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernedRuntimePrimaryProjectionError(f"MISSING_MANDATORY_{field_name.upper()}")
    return value.strip()


def _require_int(value: Any, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise GovernedRuntimePrimaryProjectionError(f"MISSING_MANDATORY_{field_name.upper()}")
    return value


def validate_primary_evidence_for_projection_v1(
    *,
    source_mode: RuntimePrimarySourceModeV1,
    primary_evidence_root: Path,
) -> tuple[bool, str, dict[str, Any]]:
    root = primary_evidence_root.resolve()
    if not root.is_dir():
        return False, "SOURCE_ARCHIVE_MISSING", {"root": str(root)}
    if is_under_tmp(root):
        return False, "TMP_ONLY_SOURCE_REJECTED", {"root": str(root)}
    metadata_path = root / "RUN_METADATA.json"
    if metadata_path.is_file():
        try:
            metadata = _load_json_object(metadata_path, "RUN_METADATA.json")
        except GovernedRuntimePrimaryProjectionError:
            metadata = {}
        else:
            declared = str(metadata.get("source_execution_mode", "")).upper()
            if declared and declared != source_mode.value:
                return (
                    False,
                    "SOURCE_MODE_MISMATCH",
                    {
                        "declared": declared,
                        "expected": source_mode.value,
                    },
                )
    required = _REQUIRED_PATHS_BY_MODE[source_mode.value]
    ok, msg, detail = validate_durable_primary_evidence_root(root, required_rel_paths=required)
    if not ok:
        return False, "DURABLE_PRIMARY_VALIDATION_FAILED", {"message": msg, **detail}
    metadata = _load_json_object(root / "RUN_METADATA.json", "RUN_METADATA.json")
    declared = str(metadata.get("source_execution_mode", "")).upper()
    if declared and declared != source_mode.value:
        return False, "SOURCE_MODE_MISMATCH", {"declared": declared, "expected": source_mode.value}
    return True, "", {"checks": detail.get("checks", {}), "metadata": metadata}


def extract_runtime_primary_provenance_binding_v1(
    *,
    source_mode: RuntimePrimarySourceModeV1,
    primary_evidence_root: Path,
) -> RuntimePrimaryProvenanceBindingV1:
    root = primary_evidence_root.resolve()
    metadata = _load_json_object(root / "RUN_METADATA.json", "RUN_METADATA.json")
    review = _load_json_object(root / "review" / "REVIEW_RESULT.json", "review/REVIEW_RESULT.json")

    run_id = _require_non_empty_str(metadata.get("run_id"), field_name="run_session_identity")
    instrument = _require_non_empty_str(metadata.get("instrument"), field_name="instrument_binding")
    venue = _require_non_empty_str(metadata.get("venue"), field_name="venue_identity")
    strategy_version = _require_non_empty_str(
        metadata.get("strategy_version"), field_name="config_identity"
    )
    repo_prefix = _require_non_empty_str(
        metadata.get("repo_head_sha_prefix"), field_name="repository_provenance"
    )
    trading_epoch = _require_int(metadata.get("trading_epoch"), field_name="observation_epoch")

    observation_time = metadata.get("observation_time_utc")
    if source_mode in (RuntimePrimarySourceModeV1.SHADOW, RuntimePrimarySourceModeV1.TESTNET):
        wallclock_path = root / "WALLCLOCK_EVIDENCE.json"
        wallclock = _load_json_object(wallclock_path, "WALLCLOCK_EVIDENCE.json")
        observation_time = wallclock.get("end_wall_clock_iso") or observation_time
    observation_time_utc = _require_non_empty_str(observation_time, field_name="observation_time")

    manifest_path = root / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise GovernedRuntimePrimaryProjectionError("MANIFEST_SHA256_MISSING")
    ok, msg = verify_manifest_sha256(root)
    if not ok:
        raise GovernedRuntimePrimaryProjectionError(f"MANIFEST_VERIFY_FAILED: {msg}")
    primary_manifest_digest = _file_digest(manifest_path)

    runtime_out_digest: str | None = None
    paper_manifest = root / "runtime_out" / "evidence_manifest.json"
    if paper_manifest.is_file():
        runtime_out_digest = _file_digest(paper_manifest)

    wrapper_digest: str | None = None
    wrapper_manifest = root / "wrapper_evidence" / "manifest.json"
    if wrapper_manifest.is_file():
        wrapper_digest = _file_digest(wrapper_manifest)

    if source_mode is RuntimePrimarySourceModeV1.PAPER and runtime_out_digest is None:
        raise GovernedRuntimePrimaryProjectionError("PAPER_EVIDENCE_MANIFEST_MISSING")
    if source_mode is not RuntimePrimarySourceModeV1.PAPER and wrapper_digest is None:
        raise GovernedRuntimePrimaryProjectionError("WRAPPER_EVIDENCE_MANIFEST_MISSING")

    verdict = str(review.get("verdict", ""))
    if verdict != "PASS":
        raise GovernedRuntimePrimaryProjectionError("REVIEW_VERDICT_NOT_PASS")

    return RuntimePrimaryProvenanceBindingV1(
        source_execution_mode=source_mode.value,
        source_run_session_identity=run_id,
        source_archive_root_ref=str(root),
        primary_evidence_manifest_digest=primary_manifest_digest,
        runtime_out_evidence_manifest_digest=runtime_out_digest,
        wrapper_evidence_manifest_digest=wrapper_digest,
        observation_time_utc=observation_time_utc,
        instrument_identity=instrument,
        venue_identity=venue,
        trading_epoch=trading_epoch,
        strategy_config_identity=strategy_version,
        repository_code_provenance=repo_prefix,
        review_verdict=verdict,
    )


def build_offline_experiment_observations_from_primary_v1(
    *,
    provenance: RuntimePrimaryProvenanceBindingV1,
    primary_evidence_root: Path,
) -> OfflineExperimentObservationsV1:
    review = _load_json_object(
        primary_evidence_root / "review" / "REVIEW_RESULT.json",
        "review/REVIEW_RESULT.json",
    )
    metrics_raw = review.get("metrics")
    metrics: dict[str, Any]
    if isinstance(metrics_raw, dict) and metrics_raw:
        metrics = dict(metrics_raw)
    else:
        metrics = {"primary_review_verdict": provenance.review_verdict}

    bundle_ref = _repo_relative_ref(primary_evidence_root)
    artifacts: list[dict[str, Any]] = [
        {
            "kind": "REPO_RELATIVE",
            "ref": bundle_ref,
            "digest": provenance.primary_evidence_manifest_digest,
            "media_type": "application/x-peak-trade-primary-evidence-bundle",
        }
    ]
    if provenance.runtime_out_evidence_manifest_digest:
        artifacts.append(
            {
                "kind": "REPO_RELATIVE",
                "ref": "runtime_out/evidence_manifest.json",
                "digest": provenance.runtime_out_evidence_manifest_digest,
                "media_type": "application/json",
            }
        )
    if provenance.wrapper_evidence_manifest_digest:
        artifacts.append(
            {
                "kind": "REPO_RELATIVE",
                "ref": "wrapper_evidence/manifest.json",
                "digest": provenance.wrapper_evidence_manifest_digest,
                "media_type": "application/json",
            }
        )

    return OfflineExperimentObservationsV1(
        metrics=metrics,
        robustness_results={},
        regime_results={},
        artifacts=artifacts,
        robustness_observations={
            "source_execution_mode": provenance.source_execution_mode,
            "observation_time_utc": provenance.observation_time_utc,
        },
        robustness_policy=None,
    )


def _evidence_binding_from_digest(ref: str, digest: str) -> EvidenceFieldBinding:
    return EvidenceFieldBinding(ref=ref, digest=digest, status="BOUND")


def build_runtime_observation_bundle_input_from_primary_v1(
    *,
    provenance: RuntimePrimaryProvenanceBindingV1,
) -> RuntimeObservationBundleInput:
    root_ref = provenance.source_archive_root_ref
    manifest_digest = provenance.primary_evidence_manifest_digest
    bundle_id = (
        f"g2-{provenance.source_execution_mode.lower()}-{provenance.source_run_session_identity}"
    )

    return RuntimeObservationBundleInput(
        observation_bundle_id=bundle_id,
        source_evidence_bundle_dir=root_ref,
        source_manifest_digest=manifest_digest,
        runtime_session_id=provenance.source_run_session_identity,
        trading_epoch=provenance.trading_epoch,
        executor_epoch=provenance.trading_epoch,
        venue=provenance.venue_identity,
        instrument=provenance.instrument_identity,
        environment=_ENV_BY_MODE[provenance.source_execution_mode],
        market_type="FUTURES",
        strategy_version=provenance.strategy_config_identity,
        model_version=provenance.strategy_config_identity,
        parameter_version=provenance.strategy_config_identity,
        signal_version=provenance.strategy_config_identity,
        order_evidence=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        fill_evidence=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        position_evidence=_evidence_binding_from_digest(
            f"primary://{root_ref}/RUN_METADATA.json",
            provenance.primary_evidence_manifest_digest,
        ),
        pnl_evidence=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        fee_evidence=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        funding_evidence=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        slippage_evidence=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        latency_evidence=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        risk_event=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        kill_switch_event=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        reconciliation_event=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        runtime_health=_evidence_binding_from_digest(
            f"primary://{root_ref}/review/REVIEW_RESULT.json",
            provenance.primary_evidence_manifest_digest,
        ),
        input_refs=(f"primary://{root_ref}",),
        input_digests=(manifest_digest,),
        parent_refs=(f"primary_manifest://{manifest_digest}",),
        source_manifest_refs=(f"manifest://{root_ref}/{MANIFEST_FILENAME}",),
    )


def _authority_boundary_block(request: GovernedRuntimePrimaryProjectionRequestV1) -> str | None:
    if request.start_runtime_execution:
        return "RUNTIME_PROCESS_START_REQUESTED"
    if request.request_promotion:
        return "PROMOTION_AUTHORIZATION_REQUESTED"
    if request.request_runtime_apply:
        return "RUNTIME_APPLY_REQUESTED"
    if request.request_external_effect:
        return "EXTERNAL_EFFECT_REQUESTED"
    return None


def run_governed_runtime_primary_to_offline_observation_projection_v1(
    request: GovernedRuntimePrimaryProjectionRequestV1,
) -> GovernedRuntimePrimaryProjectionResultV1:
    boundary = _authority_boundary_block(request)
    if boundary:
        return GovernedRuntimePrimaryProjectionResultV1(
            status="REJECTED",
            decision_code=boundary,
            blocking_reasons=(boundary,),
            provenance=None,
            offline_observations=None,
            identity_binding_status=None,
            runtime_observation_bundle=None,
            runtime_learning_input=None,
            projection_record_digest=None,
        )

    ok, code, _detail = validate_primary_evidence_for_projection_v1(
        source_mode=request.source_mode,
        primary_evidence_root=request.primary_evidence_root,
    )
    if not ok:
        return GovernedRuntimePrimaryProjectionResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code,),
            provenance=None,
            offline_observations=None,
            identity_binding_status=None,
            runtime_observation_bundle=None,
            runtime_learning_input=None,
            projection_record_digest=None,
        )

    try:
        provenance = extract_runtime_primary_provenance_binding_v1(
            source_mode=request.source_mode,
            primary_evidence_root=request.primary_evidence_root,
        )
        observations = build_offline_experiment_observations_from_primary_v1(
            provenance=provenance,
            primary_evidence_root=request.primary_evidence_root,
        )
    except GovernedRuntimePrimaryProjectionError as exc:
        return GovernedRuntimePrimaryProjectionResultV1(
            status="REJECTED",
            decision_code=str(exc),
            blocking_reasons=(str(exc),),
            provenance=None,
            offline_observations=None,
            identity_binding_status=None,
            runtime_observation_bundle=None,
            runtime_learning_input=None,
            projection_record_digest=None,
        )

    binding = bind_canonical_identity_bound_offline_observation_v1(
        CanonicalIdentityBoundOfflineObservationBindingRequestV1(
            phase1_identity=dict(request.phase1_identity),
            observation_owner=OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1,
            observations=observations,
            claimed_identity_digest=request.claimed_identity_digest,
            claimed_experiment_id=request.claimed_experiment_id,
            claimed_parent_lineage_ref=request.claimed_parent_lineage_ref,
            hypothesis_id=request.hypothesis_id,
            hypothesis_fingerprint=request.hypothesis_fingerprint,
            strategy_family=request.strategy_family,
            created_at=request.created_at,
        )
    )
    identity_status = str(binding.get("status", ""))
    if identity_status != STATUS_BOUND:
        return GovernedRuntimePrimaryProjectionResultV1(
            status="REJECTED",
            decision_code="IDENTITY_BOUND_OBSERVATION_REJECTED",
            blocking_reasons=(identity_status,),
            provenance=provenance,
            offline_observations=observations,
            identity_binding_status=identity_status,
            runtime_observation_bundle=None,
            runtime_learning_input=None,
            projection_record_digest=None,
        )

    obs_input = build_runtime_observation_bundle_input_from_primary_v1(provenance=provenance)
    try:
        verify_source_evidence_bundle(provenance.source_archive_root_ref)
    except Exception as exc:  # noqa: BLE001 — contract surfaces ValueError subclasses
        return GovernedRuntimePrimaryProjectionResultV1(
            status="REJECTED",
            decision_code="SOURCE_MANIFEST_VERIFY_FAILED",
            blocking_reasons=(str(exc),),
            provenance=provenance,
            offline_observations=observations,
            identity_binding_status=identity_status,
            runtime_observation_bundle=None,
            runtime_learning_input=None,
            projection_record_digest=None,
        )

    runtime_observation = build_runtime_observation_bundle_v1(obs_input)
    if str(runtime_observation.get("observation_status")) != "COMPLETE":
        return GovernedRuntimePrimaryProjectionResultV1(
            status="REJECTED",
            decision_code="RUNTIME_OBSERVATION_NOT_COMPLETE",
            blocking_reasons=tuple(runtime_observation.get("blocking_reasons", ())),
            provenance=provenance,
            offline_observations=observations,
            identity_binding_status=identity_status,
            runtime_observation_bundle=runtime_observation,
            runtime_learning_input=None,
            projection_record_digest=None,
        )

    learning_request = RuntimeToLearningInputRequest(
        learning_input_id=f"rtli-g2-{uuid.uuid4().hex[:12]}",
        source_observation_ref=f"bundle://{runtime_observation.get('observation_bundle_id', '')}",
        source_observation_digest=str(runtime_observation.get("output_digest", "")),
        source_observation_body=runtime_observation,
        source_observation_status=str(runtime_observation.get("observation_status", "")),
        realized_performance_refs=(f"primary://{provenance.source_archive_root_ref}/review",),
        cost_refs=(),
        execution_quality_refs=(),
        risk_event_refs=(),
        reconciliation_refs=(),
        data_quality_status="VERIFIED",
        completeness_status="COMPLETE",
        input_refs=tuple(str(r) for r in runtime_observation.get("input_refs", ())),
        input_digests=tuple(str(d) for d in runtime_observation.get("input_digests", ())),
        parent_refs=(f"primary_manifest://{provenance.primary_evidence_manifest_digest}",),
    )
    learning_input = build_runtime_to_learning_input_v1(learning_request)
    if str(learning_input.get("decision_code")) != "LEARNING_INPUT_VALID":
        return GovernedRuntimePrimaryProjectionResultV1(
            status="REJECTED",
            decision_code="LEARNING_INGRESS_REJECTED",
            blocking_reasons=tuple(learning_input.get("blocking_reasons", ())),
            provenance=provenance,
            offline_observations=observations,
            identity_binding_status=identity_status,
            runtime_observation_bundle=runtime_observation,
            runtime_learning_input=learning_input,
            projection_record_digest=None,
        )

    record_body = {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "provenance": provenance.as_dict(),
        "identity_binding_status": identity_status,
        "offline_observations_digest": compute_content_sha256(
            {
                "metrics": dict(observations.metrics),
                "artifacts": list(observations.artifacts),
            }
        ),
        "runtime_observation_digest": str(runtime_observation.get("output_digest", "")),
        "runtime_learning_input_digest": str(learning_input.get("output_digest", "")),
        "primary_evidence_implies_productive_authorization": PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION,
    }
    projection_digest = compute_content_sha256(record_body)
    lineage = (
        f"primary_manifest://{provenance.primary_evidence_manifest_digest}",
        f"projection://{projection_digest}",
        f"runtime_learning://{learning_input.get('output_digest', '')}",
    )
    return GovernedRuntimePrimaryProjectionResultV1(
        status="PROJECTED",
        decision_code="GOVERNED_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTED",
        blocking_reasons=(),
        provenance=provenance,
        offline_observations=observations,
        identity_binding_status=identity_status,
        runtime_observation_bundle=runtime_observation,
        runtime_learning_input=learning_input,
        projection_record_digest=projection_digest,
        lineage_chain=lineage,
    )


def produce_governed_runtime_primary_projection_artifact_v1(
    *,
    result: GovernedRuntimePrimaryProjectionResultV1,
    output_dir: Path,
) -> Path:
    if result.status != "PROJECTED" or result.provenance is None:
        raise GovernedRuntimePrimaryProjectionError("projection not complete; artifact refused")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    staging = out / f"{PROJECTION_STAGING_PREFIX}{uuid.uuid4().hex}"
    staging.mkdir()
    body = {
        "schema_version": SCHEMA_VERSION,
        "projection_status": result.status,
        "decision_code": result.decision_code,
        "provenance": result.provenance.as_dict(),
        "identity_binding_status": result.identity_binding_status,
        "projection_record_digest": result.projection_record_digest,
        "lineage_chain": list(result.lineage_chain),
        "authority_invariants": {
            "projection_authority": "NONE",
            "runtime_apply_started": RUNTIME_APPLY_STARTED,
            "external_effect": EXTERNAL_EFFECT,
        },
    }
    artifact_path = staging / PROJECTION_ARTIFACT_REL
    artifact_path.write_text(deterministic_json_dumps(body) + "\n", encoding="utf-8")
    write_manifest_sha256(staging)
    ok, msg = verify_manifest_sha256(staging)
    if not ok:
        raise GovernedRuntimePrimaryProjectionError(f"projection artifact manifest failed: {msg}")
    final_artifact = out / PROJECTION_ARTIFACT_REL
    if final_artifact.exists():
        raise GovernedRuntimePrimaryProjectionError("projection artifact output already exists")
    artifact_path.replace(final_artifact)
    (staging / MANIFEST_FILENAME).replace(out / MANIFEST_FILENAME)
    staging.rmdir()
    return out


def load_field_mapping_ledger_v1(*, repo_root: Path) -> Mapping[str, Any]:
    path = repo_root / FIELD_MAPPING_LEDGER
    return json.loads(path.read_text(encoding="utf-8"))


def primary_evidence_implies_productive_authorization_v1() -> bool:
    return PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION


def p5_evidence_intake_implies_productive_authorization_v1() -> bool:
    return P5_EVIDENCE_INTAKE_IMPLIES_PRODUCTIVE_AUTHORIZATION


def p5_evidence_intake_implies_runtime_apply_v1() -> bool:
    return P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY


__all__ = [
    "CROSS_MODE_NORMALIZATION_STATUS",
    "DECISION_CONFIG",
    "EXTERNAL_EFFECT",
    "FIELD_MAPPING_LEDGER",
    "GovernedRuntimePrimaryProjectionError",
    "GovernedRuntimePrimaryProjectionRequestV1",
    "GovernedRuntimePrimaryProjectionResultV1",
    "M11_STARTED",
    "NORMATIVE_SPEC",
    "PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION",
    "P5_EVIDENCE_INTAKE_IMPLIES_PRODUCTIVE_AUTHORIZATION",
    "P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY",
    "PROJECTION_ARTIFACT_REL",
    "REAL_RUNTIME_MATERIALIZATION_PERFORMED",
    "RUNTIME_APPLY_STARTED",
    "RuntimePrimaryProvenanceBindingV1",
    "RuntimePrimarySourceModeV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "build_offline_experiment_observations_from_primary_v1",
    "build_runtime_observation_bundle_input_from_primary_v1",
    "extract_runtime_primary_provenance_binding_v1",
    "load_field_mapping_ledger_v1",
    "p5_evidence_intake_implies_productive_authorization_v1",
    "p5_evidence_intake_implies_runtime_apply_v1",
    "primary_evidence_implies_productive_authorization_v1",
    "produce_governed_runtime_primary_projection_artifact_v1",
    "run_governed_runtime_primary_to_offline_observation_projection_v1",
    "validate_primary_evidence_for_projection_v1",
]
