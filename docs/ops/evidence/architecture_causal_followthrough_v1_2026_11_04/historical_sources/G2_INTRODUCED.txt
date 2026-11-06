"""Governed mechanical binding: runtime_to_learning_input_v1 → optimization learning input.

Projects validated G2 runtime learning ingress into learning_evidence_record_v1 and
feeds the existing canonical optimization-universe learning-input validator only.
Authority=NONE; no DDO fixture state; no runtime apply or productive activation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.governance.governed_productive_configuration_apply_authority_v1 import (
    PRIMARY_EVIDENCE_IMPLIES_APPLY,
    RUNTIME_APPLY_STARTED as M10_RUNTIME_APPLY_STARTED,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    GovernedRuntimePrimaryProjectionResultV1,
    RuntimePrimaryProvenanceBindingV1,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_LEARNING_EVIDENCE_RECORD,
    SCHEMA_VERSION_LEARNING_EVIDENCE_RECORD_V1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_evidence_record_v1 import (
    EVIDENCE_CLASS_LEARNING,
    UNIVERSE_CLASS_SELF_LEARNING,
    build_learning_evidence_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = (
    "governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_RUNTIME_LEARNING_INPUT_TO_OPTIMIZATION_UNIVERSE_LEARNING_INPUT_BINDING_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "GOVERNED_RUNTIME_LEARNING_INPUT_TO_OPTIMIZATION_UNIVERSE_LEARNING_INPUT_BINDING_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1_decision_v1.json"
)
FIELD_MAPPING_LEDGER: Final[str] = (
    "config/governance/"
    "governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1_field_mapping_ledger_v1.json"
)

BINDING_PRODUCER_ID: Final[str] = (
    "peak_trade.governance.runtime_learning_input_to_optimization_universe_binding_v1"
)

PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION: Final[bool] = False
P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY: Final[bool] = False
CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION: Final[bool] = False
RUNTIME_APPLY_STARTED: Final[bool] = False
REAL_RUNTIME_MATERIALIZATION_PERFORMED: Final[bool] = False
PRODUCTIVE_ACTIVATION_AUTHORIZED: Final[bool] = False
EXTERNAL_EFFECT: Final[bool] = False

REAL_MECHANICAL_PATH_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
FIXTURE_ONLY_PATH_STATUS: Final[str] = "PROVEN_FIXTURE_PATH"

_ENV_BY_MODE: Final[dict[str, str]] = {
    "PAPER": "PAPER_BOUNDED_OBSERVATION",
    "SHADOW": "SHADOW_BOUNDED_OBSERVATION",
    "TESTNET": "TESTNET_BOUNDED_OBSERVATION",
}

_REPO_ROOT = Path(__file__).resolve().parents[2]


class GovernedRuntimeLearningInputBindingError(ValueError):
    """Fail-closed binding error."""


@dataclass(frozen=True)
class RuntimeLearningInputOptimizationBindingRequestV1:
    runtime_learning_input: Mapping[str, Any]
    provenance: RuntimePrimaryProvenanceBindingV1
    projection_record_digest: str
    requested_productive_join: bool = False
    requested_auto_search: bool = False
    requested_envelope_mutation: bool = False
    ddo_fixture_learning_state: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RuntimeLearningInputOptimizationBindingResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    learning_evidence: dict[str, Any] | None
    canonical_optimization_ack: MappingProxyType[str, Any] | None
    binding_record_digest: str | None
    lineage_chain: tuple[str, ...] = field(default_factory=tuple)
    path_classification: str = ""


def load_field_mapping_ledger_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    path = root / FIELD_MAPPING_LEDGER
    if not path.is_file():
        raise GovernedRuntimeLearningInputBindingError("FIELD_MAPPING_LEDGER_MISSING")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GovernedRuntimeLearningInputBindingError("FIELD_MAPPING_LEDGER_INVALID")
    return payload


def _reject_fixture_rescue(request: RuntimeLearningInputOptimizationBindingRequestV1) -> str | None:
    if request.ddo_fixture_learning_state is not None:
        return "DDO_FIXTURE_STATE_IN_BINDING_REQUEST_FORBIDDEN"
    return None


def _validate_provenance_alignment_v1(
    body: Mapping[str, Any],
    provenance: RuntimePrimaryProvenanceBindingV1,
) -> tuple[str, ...]:
    blocking: list[str] = []
    expected_env = _ENV_BY_MODE.get(provenance.source_execution_mode, "")
    if str(body.get("source_session_identity", "")) != provenance.source_run_session_identity:
        blocking.append("SOURCE_SESSION_IDENTITY_MISMATCH")
    if str(body.get("source_instrument", "")) != provenance.instrument_identity:
        blocking.append("SOURCE_INSTRUMENT_MISMATCH")
    if expected_env and str(body.get("source_environment", "")) != expected_env:
        blocking.append("SOURCE_ENVIRONMENT_MISMATCH")
    if str(body.get("source_venue", "")) != provenance.venue_identity:
        blocking.append("SOURCE_VENUE_MISMATCH")
    parent_refs = tuple(str(r) for r in body.get("parent_refs", ()))
    expected_parent = f"primary_manifest://{provenance.primary_evidence_manifest_digest}"
    if expected_parent not in parent_refs:
        blocking.append("PRIMARY_MANIFEST_PARENT_REF_MISSING")
    return tuple(dict.fromkeys(blocking))


def _validate_runtime_learning_input_contract(body: Mapping[str, Any]) -> tuple[str, ...]:
    blocking: list[str] = []
    if str(body.get("decision_code", "")) != "LEARNING_INPUT_VALID":
        blocking.append("RUNTIME_LEARNING_INPUT_NOT_VALID")
    if str(body.get("learning_input_status", "")) != "VALID":
        blocking.append("RUNTIME_LEARNING_INPUT_STATUS_NOT_VALID")
    digest = str(body.get("output_digest", ""))
    if not is_valid_sha256_hex(digest):
        blocking.append("RUNTIME_LEARNING_INPUT_DIGEST_MISSING")
    integrity = body.get("integrity") or {}
    if str(integrity.get("content_sha256", "")) != digest:
        blocking.append("RUNTIME_LEARNING_INPUT_INTEGRITY_MISMATCH")
    if not str(body.get("source_observation_ref", "")):
        blocking.append("MISSING_SOURCE_OBSERVATION_REF")
    if not is_valid_sha256_hex(str(body.get("source_observation_digest", ""))):
        blocking.append("MISSING_SOURCE_OBSERVATION_DIGEST")
    return tuple(dict.fromkeys(blocking))


def _derive_runtime_derived_state_record_ref_v1(*, runtime_learning_input_digest: str) -> str:
    return f"g2.rtls.{runtime_learning_input_digest[:40]}"


def _derive_decision_event_ref_v1(*, primary_evidence_manifest_digest: str) -> str:
    return f"g2.primary.{primary_evidence_manifest_digest[:48]}"


def _lineage_record_id_v1(*, prefix: str, digest: str) -> str:
    return f"g2.{prefix}.{digest[:48]}"


def _derive_evaluation_bundle_fingerprint_v1(
    *,
    runtime_learning_input_digest: str,
    source_observation_digest: str,
    primary_evidence_manifest_digest: str,
    projection_record_digest: str,
) -> str:
    material = {
        "primary_evidence_manifest_digest": primary_evidence_manifest_digest,
        "projection_record_digest": projection_record_digest,
        "runtime_learning_input_digest": runtime_learning_input_digest,
        "source_observation_digest": source_observation_digest,
    }
    return compute_content_sha256(material)


def _derive_learning_evidence_record_id_v1(
    *,
    source_learning_state_record_ref: str,
    evaluation_bundle_fingerprint: str,
) -> str:
    digest = hashlib.sha256(
        f"{source_learning_state_record_ref}|{evaluation_bundle_fingerprint}".encode("utf-8")
    ).hexdigest()
    return f"g2.lev.{digest[:40]}"


def _project_learning_evidence_from_runtime_v1(
    *,
    runtime_learning_input: Mapping[str, Any],
    provenance: RuntimePrimaryProvenanceBindingV1,
    projection_record_digest: str,
) -> dict[str, Any]:
    runtime_digest = str(runtime_learning_input["output_digest"])
    source_obs_digest = str(runtime_learning_input["source_observation_digest"])
    primary_digest = provenance.primary_evidence_manifest_digest
    if not is_valid_sha256_hex(projection_record_digest):
        raise GovernedRuntimeLearningInputBindingError("PROJECTION_RECORD_DIGEST_INVALID")

    state_ref = _derive_runtime_derived_state_record_ref_v1(
        runtime_learning_input_digest=runtime_digest
    )
    bundle_fp = _derive_evaluation_bundle_fingerprint_v1(
        runtime_learning_input_digest=runtime_digest,
        source_observation_digest=source_obs_digest,
        primary_evidence_manifest_digest=primary_digest,
        projection_record_digest=projection_record_digest,
    )
    record_id = _derive_learning_evidence_record_id_v1(
        source_learning_state_record_ref=state_ref,
        evaluation_bundle_fingerprint=bundle_fp,
    )
    decision_ref = _derive_decision_event_ref_v1(primary_evidence_manifest_digest=primary_digest)
    economic_label = f"g2.review.{provenance.review_verdict}"
    horizon_token = f"g2.mode.{provenance.source_execution_mode}.bounded_observation"
    outcome_ref = str(runtime_learning_input.get("source_observation_ref", ""))
    causal = list(
        dict.fromkeys(
            [
                state_ref,
                decision_ref,
                _lineage_record_id_v1(prefix="proj", digest=projection_record_digest),
                _lineage_record_id_v1(prefix="rtli", digest=runtime_digest),
            ]
        )
    )
    evidence_source_refs = list(
        dict.fromkeys(
            [
                str(runtime_learning_input.get("source_observation_ref", "")),
                f"primary_manifest://{primary_digest}",
                f"projection://{projection_record_digest}",
                *list(runtime_learning_input.get("realized_performance_refs", ())),
            ]
        )
    )
    payload = {
        "schema_name": SCHEMA_NAME_LEARNING_EVIDENCE_RECORD,
        "schema_version": SCHEMA_VERSION_LEARNING_EVIDENCE_RECORD_V1,
        "record_id": record_id,
        "source_learning_state_record_ref": state_ref,
        "state_scope_id": f"g2.scope.{provenance.source_run_session_identity}",
        "state_version": 1,
        "evaluation_bundle_fingerprint": bundle_fp,
        "decision_event_ref": decision_ref,
        "observed_at_utc": provenance.observation_time_utc,
        "economic_score_label": economic_label,
        "evaluation_horizon": horizon_token,
        "actual_outcome_ref": outcome_ref,
        "decision_score_label": None,
        "safety_score_label": None,
        "universe_class": UNIVERSE_CLASS_SELF_LEARNING,
        "evidence_class": EVIDENCE_CLASS_LEARNING,
        "event_time_utc": provenance.observation_time_utc,
        "correlation_id": provenance.source_run_session_identity,
        "cycle_id": None,
        "causal_parent_ids": causal,
        "producer_id": BINDING_PRODUCER_ID,
        "authority_owner": UNKNOWN,
        "code_sha": UNKNOWN,
        "config_hash": UNKNOWN,
        "evidence_hash": bundle_fp,
        "evidence_source_refs": evidence_source_refs,
        "productive_authority": "NONE",
        "runtime_reachability": False,
        "can_auto_promote": False,
        "can_mutate_core": False,
        "can_mutate_risk": False,
        "can_mutate_safety": False,
        "can_deploy": False,
    }
    return dict(build_learning_evidence_record_v1(payload))


def bind_runtime_to_learning_input_to_canonical_optimization_universe_learning_input_v1(
    request: RuntimeLearningInputOptimizationBindingRequestV1,
) -> RuntimeLearningInputOptimizationBindingResultV1:
    fixture_block = _reject_fixture_rescue(request)
    if fixture_block:
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=fixture_block,
            blocking_reasons=(fixture_block,),
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )
    if (
        request.requested_productive_join
        or request.requested_auto_search
        or request.requested_envelope_mutation
    ):
        code = "FORBIDDEN_PRODUCTIVE_OR_SEARCH_REQUEST"
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code,),
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )

    body = request.runtime_learning_input
    blocking = _validate_runtime_learning_input_contract(body)
    blocking += _validate_provenance_alignment_v1(body, request.provenance)
    blocking = tuple(dict.fromkeys(blocking))
    if blocking:
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=blocking[0],
            blocking_reasons=blocking,
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )

    if not is_valid_sha256_hex(request.projection_record_digest):
        code = "PROJECTION_RECORD_DIGEST_INVALID"
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code,),
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )

    try:
        learning_evidence = _project_learning_evidence_from_runtime_v1(
            runtime_learning_input=body,
            provenance=request.provenance,
            projection_record_digest=request.projection_record_digest,
        )
    except (GovernedRuntimeLearningInputBindingError, DdoValidationError) as exc:
        code = str(exc)
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code,),
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )

    ack = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(
            learning_evidence=learning_evidence,
            requested_productive_join=request.requested_productive_join,
            requested_auto_search=request.requested_auto_search,
            requested_envelope_mutation=request.requested_envelope_mutation,
        )
    )
    if ack.get("status") != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        reason = str(ack.get("reason", "CANONICAL_OPTIMIZATION_INPUT_REJECTED"))
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=reason,
            blocking_reasons=(reason,),
            learning_evidence=learning_evidence,
            canonical_optimization_ack=ack,
            binding_record_digest=None,
        )

    binding_body = {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "runtime_learning_input_digest": str(body.get("output_digest", "")),
        "projection_record_digest": request.projection_record_digest,
        "primary_evidence_manifest_digest": request.provenance.primary_evidence_manifest_digest,
        "learning_evidence_digest": str(learning_evidence.get("content_hash", "")),
        "canonical_optimization_result_digest": str(ack.get("result_digest", "")),
        "path_classification": REAL_MECHANICAL_PATH_STATUS,
        "primary_evidence_implies_productive_authorization": PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION,
        "canonical_learning_input_implies_productive_activation": (
            CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION
        ),
    }
    binding_digest = compute_content_sha256(binding_body)
    lineage = (
        f"primary_manifest://{request.provenance.primary_evidence_manifest_digest}",
        f"projection://{request.projection_record_digest}",
        f"runtime_learning://{body.get('output_digest', '')}",
        f"learning_evidence://{learning_evidence.get('content_hash', '')}",
        f"optimization_input://{ack.get('result_digest', '')}",
        f"binding://{binding_digest}",
    )
    return RuntimeLearningInputOptimizationBindingResultV1(
        status="BOUND",
        decision_code="RUNTIME_LEARNING_INPUT_BOUND_TO_CANONICAL_OPTIMIZATION_INPUT",
        blocking_reasons=(),
        learning_evidence=learning_evidence,
        canonical_optimization_ack=ack,
        binding_record_digest=binding_digest,
        lineage_chain=lineage,
        path_classification=REAL_MECHANICAL_PATH_STATUS,
    )


def bind_from_g2_projection_result_v1(
    projection: GovernedRuntimePrimaryProjectionResultV1,
    *,
    requested_productive_join: bool = False,
) -> RuntimeLearningInputOptimizationBindingResultV1:
    if projection.status != "PROJECTED":
        code = "G2_PROJECTION_NOT_PROJECTED"
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code, *projection.blocking_reasons),
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )
    if projection.runtime_learning_input is None or projection.provenance is None:
        code = "G2_PROJECTION_MISSING_RUNTIME_LEARNING_INPUT"
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code,),
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )
    if not projection.projection_record_digest:
        code = "G2_PROJECTION_RECORD_DIGEST_MISSING"
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code,),
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )
    return bind_runtime_to_learning_input_to_canonical_optimization_universe_learning_input_v1(
        RuntimeLearningInputOptimizationBindingRequestV1(
            runtime_learning_input=projection.runtime_learning_input,
            provenance=projection.provenance,
            projection_record_digest=projection.projection_record_digest,
            requested_productive_join=requested_productive_join,
        )
    )


def prove_binding_authority_invariants_v1() -> bool:
    return (
        PRIMARY_EVIDENCE_IMPLIES_APPLY is False
        and M10_RUNTIME_APPLY_STARTED is False
        and PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION is False
        and P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY is False
        and CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION is False
        and RUNTIME_APPLY_STARTED is False
        and EXTERNAL_EFFECT is False
    )


__all__ = [
    "BINDING_PRODUCER_ID",
    "CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION",
    "DECISION_CONFIG",
    "EXTERNAL_EFFECT",
    "FIELD_MAPPING_LEDGER",
    "FIXTURE_ONLY_PATH_STATUS",
    "GovernedRuntimeLearningInputBindingError",
    "NORMATIVE_SPEC",
    "P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY",
    "PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION",
    "PRODUCTIVE_ACTIVATION_AUTHORIZED",
    "REAL_MECHANICAL_PATH_STATUS",
    "REAL_RUNTIME_MATERIALIZATION_PERFORMED",
    "RUNTIME_APPLY_STARTED",
    "RuntimeLearningInputOptimizationBindingRequestV1",
    "RuntimeLearningInputOptimizationBindingResultV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "bind_from_g2_projection_result_v1",
    "bind_runtime_to_learning_input_to_canonical_optimization_universe_learning_input_v1",
    "load_field_mapping_ledger_v1",
    "prove_binding_authority_invariants_v1",
]
