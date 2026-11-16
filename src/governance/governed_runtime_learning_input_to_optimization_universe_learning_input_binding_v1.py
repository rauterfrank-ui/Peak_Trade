"""Bind verified G2 outcome evidence to the canonical offline optimization input.

Runtime observation inputs retain their archive lineage. Source-specific readback
provides the original decision-linked Learning Evidence for optimization.
Authority=NONE; no DDO fixture state; no runtime apply or productive activation.
"""

from __future__ import annotations

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
    GovernedI17ShadowProjectionResultV1,
    GovernedPaperEpisodeProjectionResultV1,
    GovernedRuntimePrimaryProjectionError,
    GovernedRuntimePrimaryProjectionResultV1,
    RuntimePrimaryProvenanceBindingV1,
    read_verified_i17_shadow_for_g2_v1,
    read_verified_paper_episode_for_g2_v1,
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
    paper_episode_handoff: dict[str, Any] | None = None
    i17_shadow_outcome_receipt: dict[str, Any] | None = None


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

    # The runtime input validates archive observation lineage. Original outcomes
    # enter through the source-specific readback owners and keep their DDO identity.
    code = "G2_ORIGINAL_OUTCOME_EVIDENCE_REQUIRED"
    return RuntimeLearningInputOptimizationBindingResultV1(
        status="REJECTED",
        decision_code=code,
        blocking_reasons=(code,),
        learning_evidence=None,
        canonical_optimization_ack=None,
        binding_record_digest=None,
    )


def _bind_paper_episode_from_g2_v1(
    projection: GovernedPaperEpisodeProjectionResultV1, *, requested_productive_join: bool
) -> RuntimeLearningInputOptimizationBindingResultV1:
    try:
        if requested_productive_join:
            raise GovernedRuntimePrimaryProjectionError("FORBIDDEN_PRODUCTIVE_OR_SEARCH_REQUEST")
        handoff, digest = read_verified_paper_episode_for_g2_v1(projection.source)
        if digest != projection.projection_record_digest:
            raise GovernedRuntimePrimaryProjectionError(
                "G2_PAPER_EPISODE_PROJECTION_DIGEST_MISMATCH"
            )
        evidence = handoff["learning_evidence"]
        ack = validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
        )
        if (
            ack.get("status") != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
            or ack.get("learning_evidence_digest") != evidence["content_hash"]
        ):
            raise GovernedRuntimePrimaryProjectionError("G2_PAPER_EPISODE_OPTIMIZATION_REJECTED")
    except GovernedRuntimePrimaryProjectionError as exc:
        code, _, detail = str(exc).partition(":")
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(detail or code,),
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )

    measurement = handoff["measurement"]
    binding_digest = compute_content_sha256(
        {
            "schema_version": SCHEMA_VERSION,
            "projection_record_digest": digest,
            "paper_outcome_digest": measurement["outcome_digest"],
            "learning_evidence_digest": evidence["content_hash"],
            "canonical_optimization_result_digest": ack["result_digest"],
            "authority": "NONE",
        }
    )
    return RuntimeLearningInputOptimizationBindingResultV1(
        status="BOUND",
        decision_code="PAPER_EPISODE_BOUND_TO_CANONICAL_OPTIMIZATION_INPUT",
        blocking_reasons=(),
        learning_evidence=evidence,
        canonical_optimization_ack=ack,
        binding_record_digest=binding_digest,
        lineage_chain=(
            f"primary_manifest://{measurement['archive_manifest_sha256']}",
            f"paper.outcome.measurement:{measurement['outcome_digest']}",
            f"projection://{digest}",
            f"learning_evidence://{evidence['content_hash']}",
            f"optimization_input://{ack['result_digest']}",
            f"binding://{binding_digest}",
        ),
        path_classification=REAL_MECHANICAL_PATH_STATUS,
        paper_episode_handoff=handoff,
    )


def _bind_i17_shadow_from_g2_v1(
    projection: GovernedI17ShadowProjectionResultV1, *, requested_productive_join: bool
) -> RuntimeLearningInputOptimizationBindingResultV1:
    try:
        if requested_productive_join:
            raise GovernedRuntimePrimaryProjectionError("FORBIDDEN_PRODUCTIVE_OR_SEARCH_REQUEST")
        handoff, receipt, digest = read_verified_i17_shadow_for_g2_v1(projection.source)
        if digest != projection.projection_record_digest:
            raise GovernedRuntimePrimaryProjectionError("G2_I17_SHADOW_PROJECTION_DIGEST_MISMATCH")
        evidence = handoff["learning_evidence"]
        ack = validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
        )
        if (
            ack.get("status") != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
            or ack.get("learning_evidence_digest") != evidence["content_hash"]
        ):
            raise GovernedRuntimePrimaryProjectionError("G2_I17_SHADOW_OPTIMIZATION_REJECTED")
    except GovernedRuntimePrimaryProjectionError as exc:
        code, _, detail = str(exc).partition(":")
        return RuntimeLearningInputOptimizationBindingResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(detail or code,),
            learning_evidence=None,
            canonical_optimization_ack=None,
            binding_record_digest=None,
        )

    outcome_digest = receipt["exact_content_digest"]
    binding_digest = compute_content_sha256(
        {
            "schema_version": SCHEMA_VERSION,
            "projection_record_digest": digest,
            "shadow_outcome_receipt_digest": outcome_digest,
            "learning_evidence_digest": evidence["content_hash"],
            "canonical_optimization_result_digest": ack["result_digest"],
            "authority": "NONE",
        }
    )
    return RuntimeLearningInputOptimizationBindingResultV1(
        status="BOUND",
        decision_code="I17_SHADOW_BOUND_TO_CANONICAL_OPTIMIZATION_INPUT",
        blocking_reasons=(),
        learning_evidence=evidence,
        canonical_optimization_ack=ack,
        binding_record_digest=binding_digest,
        lineage_chain=(
            f"primary_manifest://{receipt['shadow_decision']['shadow_manifest_sha256']}",
            f"shadow.outcome.receipt:{outcome_digest}",
            f"projection://{digest}",
            f"learning_evidence://{evidence['content_hash']}",
            f"optimization_input://{ack['result_digest']}",
            f"binding://{binding_digest}",
        ),
        path_classification=REAL_MECHANICAL_PATH_STATUS,
        i17_shadow_outcome_receipt=receipt,
    )


def bind_from_g2_projection_result_v1(
    projection: (
        GovernedRuntimePrimaryProjectionResultV1
        | GovernedPaperEpisodeProjectionResultV1
        | GovernedI17ShadowProjectionResultV1
    ),
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
    if isinstance(projection, GovernedPaperEpisodeProjectionResultV1):
        return _bind_paper_episode_from_g2_v1(
            projection, requested_productive_join=requested_productive_join
        )
    if isinstance(projection, GovernedI17ShadowProjectionResultV1):
        return _bind_i17_shadow_from_g2_v1(
            projection, requested_productive_join=requested_productive_join
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
