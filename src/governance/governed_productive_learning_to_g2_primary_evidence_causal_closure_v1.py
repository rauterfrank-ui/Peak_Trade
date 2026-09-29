"""Productive MV2/N5 DDO learning → G2 primary-evidence ingress semantic closure (Case B).

Adjudicates that ACCEPTED_OFFLINE_RESEARCH_INPUT from productive DDO export cannot
legitimately enter bounded_runtime_primary_evidence / G2 projection ingress.
Provides fail-closed evaluation only; does not fabricate Paper/Shadow/Testnet lifecycle.

RUNTIME_AUTHORIZATION_EFFECT=NONE
PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED=false
LIFECYCLE_STATE_FABRICATED=false
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
)
from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import LOOP_STATUS_COMPLETE
from src.governance.governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1 import (
    G2RuntimeM4M8ContinuationRequestV1,
    G2RuntimeM4M8ContinuationResultV1,
    run_g2_runtime_to_m4_m8_evidence_return_continuation_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    GovernedRuntimePrimaryProjectionRequestV1,
    RuntimePrimarySourceModeV1,
    validate_primary_evidence_for_projection_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    EXPORT_ID as DDO_LEARNING_EVIDENCE_EXPORT_ID,
    PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_ddo_capture_to_offline_export_join_v1 import (
    JOIN_SEAM_ID as PRODUCTIVE_DDO_OFFLINE_EXPORT_JOIN_SEAM_ID,
)

SCHEMA_VERSION: Final[str] = "governed_productive_learning_to_g2_primary_evidence_causal_closure_v1"
WORKPACKAGE_ID: Final[str] = "CURRENT_PRODUCTIVE_LEARNING_TO_G2_PRIMARY_EVIDENCE_CAUSAL_CLOSURE_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/CURRENT_PRODUCTIVE_LEARNING_TO_G2_PRIMARY_EVIDENCE_CAUSAL_CLOSURE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_productive_learning_to_g2_primary_evidence_causal_closure_v1_decision_v1.json"
)

SEMANTIC_ADJUDICATION_CASE_A: Final[str] = "A"
SEMANTIC_ADJUDICATION_CASE_B: Final[str] = "B"
SEMANTIC_ADJUDICATION_CASE_C: Final[str] = "C"

G2_PRIMARY_EVIDENCE_DOMAIN: Final[str] = "bounded_runtime_primary_evidence"
G2_PRIMARY_SUPPORTED_MODES: Final[tuple[str, ...]] = ("PAPER", "SHADOW", "TESTNET")
PRODUCTIVE_RUNTIME_CLASS: Final[str] = "CURRENT_PRODUCTIVE_MV2_N5_DDO_OFFLINE_EXPORT"

BRIDGE_IMPLEMENTATION_AUTHORIZED: Final[bool] = False
LIFECYCLE_STATE_FABRICATED: Final[bool] = False
EXTERNAL_EFFECT: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]

_REJECT_PRODUCTIVE_AS_G2_PRIMARY: Final[tuple[str, ...]] = (
    "PRODUCTIVE_DDO_LINEAGE_NOT_BOUNDED_RUNTIME_PRIMARY_EVIDENCE",
    "G2_INGRESS_REQUIRES_PAPER_SHADOW_TESTNET_DURABLE_ARCHIVE",
    "LIFECYCLE_PROVENANCE_LAUNDERING_FORBIDDEN",
    "DISTINCT_FROM=g2_primary_evidence_to_offline_projection",
    "ACCEPTED_OFFLINE_RESEARCH_INPUT_DOES_NOT_IMPLY_G2_PRIMARY_ADMISSIBILITY",
)


@dataclass(frozen=True)
class ProductiveDdoOfflineExportHandoffSnapshotV1:
    join_seam_id: str
    optimization_ack_status: str
    session_id: str
    cycle_id: str
    correlation_id: str
    learning_evidence_record_id: str
    learning_state_record_ref: str
    export_id: str
    handoff_artifact_path: str | None = None


@dataclass(frozen=True)
class ProductiveLearningToG2PrimaryIngressEvaluationV1:
    semantic_adjudication: str
    bridge_authorized_by_owner_go: bool
    bridge_implemented: bool
    g2_ingress_admitted: bool
    fail_closed: bool
    reason_codes: tuple[str, ...]
    source_terminal: str
    g2_required_primary_evidence_semantics: str
    lifecycle_state_fabricated: bool
    productive_optimization_join_authorized: bool
    lineage_preserved: bool


@dataclass(frozen=True)
class LegitimateG2M4M8ReferenceContinuationResultV1:
    classification: str
    g2_result: G2RuntimeM4M8ContinuationResultV1
    m8_reached: bool
    productive_apply_reached: bool


def load_decision_config_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    path = root / DECISION_CONFIG
    if not path.is_file():
        raise ValueError("DECISION_CONFIG_MISSING")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("DECISION_CONFIG_INVALID")
    return payload


def snapshot_from_productive_ddo_handoff_mapping_v1(
    handoff: Mapping[str, Any],
) -> ProductiveDdoOfflineExportHandoffSnapshotV1:
    return ProductiveDdoOfflineExportHandoffSnapshotV1(
        join_seam_id=str(handoff.get("join_seam_id") or ""),
        optimization_ack_status=str(handoff.get("optimization_ack_status") or ""),
        session_id=str(handoff.get("session_id") or ""),
        cycle_id=str(handoff.get("cycle_id") or ""),
        correlation_id=str(handoff.get("correlation_id") or ""),
        learning_evidence_record_id=str(handoff.get("learning_evidence_record_id") or ""),
        learning_state_record_ref=str(handoff.get("learning_state_record_ref") or ""),
        export_id=str(handoff.get("export_id") or ""),
        handoff_artifact_path=(
            str(handoff["handoff_artifact_path"]) if handoff.get("handoff_artifact_path") else None
        ),
    )


def _validate_handoff_shape_v1(
    snapshot: ProductiveDdoOfflineExportHandoffSnapshotV1,
) -> tuple[str, ...]:
    blocking: list[str] = []
    if snapshot.join_seam_id != PRODUCTIVE_DDO_OFFLINE_EXPORT_JOIN_SEAM_ID:
        blocking.append("HANDOFF_JOIN_SEAM_MISMATCH")
    if snapshot.export_id != DDO_LEARNING_EVIDENCE_EXPORT_ID:
        blocking.append("HANDOFF_EXPORT_PRODUCER_MISMATCH")
    if not snapshot.session_id.strip():
        blocking.append("HANDOFF_SESSION_ID_MISSING")
    if not snapshot.learning_evidence_record_id.strip():
        blocking.append("HANDOFF_LEARNING_EVIDENCE_ID_MISSING")
    return tuple(dict.fromkeys(blocking))


def evaluate_productive_ddo_export_for_g2_primary_evidence_ingress_v1(
    handoff: Mapping[str, Any],
) -> ProductiveLearningToG2PrimaryIngressEvaluationV1:
    """Fail-closed: productive offline export handoff is not G2 primary evidence."""
    snapshot = snapshot_from_productive_ddo_handoff_mapping_v1(handoff)
    shape_blocks = _validate_handoff_shape_v1(snapshot)
    reasons = list(_REJECT_PRODUCTIVE_AS_G2_PRIMARY)
    reasons.extend(shape_blocks)
    if snapshot.optimization_ack_status != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        reasons.append("OFFLINE_RESEARCH_INPUT_ACK_NOT_ESTABLISHED")
    reasons = tuple(dict.fromkeys(reasons))
    return ProductiveLearningToG2PrimaryIngressEvaluationV1(
        semantic_adjudication=SEMANTIC_ADJUDICATION_CASE_B,
        bridge_authorized_by_owner_go=BRIDGE_IMPLEMENTATION_AUTHORIZED,
        bridge_implemented=False,
        g2_ingress_admitted=False,
        fail_closed=True,
        reason_codes=reasons,
        source_terminal=STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
        g2_required_primary_evidence_semantics=(
            "PREEXISTING_DURABLE_PAPER_SHADOW_TESTNET_PRIMARY_ARCHIVE_ONLY"
        ),
        lifecycle_state_fabricated=LIFECYCLE_STATE_FABRICATED,
        productive_optimization_join_authorized=PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED is True,
        lineage_preserved=True,
    )


def evaluate_handoff_artifact_path_as_primary_evidence_root_v1(
    artifact_path: Path,
) -> ProductiveLearningToG2PrimaryIngressEvaluationV1:
    """Prove handoff JSON path fails durable primary-evidence validation for every G2 mode."""
    root = artifact_path.resolve().parent if artifact_path.is_file() else artifact_path
    mode_failures: list[str] = []
    for mode in (
        RuntimePrimarySourceModeV1.PAPER,
        RuntimePrimarySourceModeV1.SHADOW,
        RuntimePrimarySourceModeV1.TESTNET,
    ):
        ok, code, _detail = validate_primary_evidence_for_projection_v1(
            source_mode=mode,
            primary_evidence_root=root,
        )
        if ok:
            mode_failures.append(f"UNEXPECTED_PRIMARY_VALIDATION_PASS:{mode.value}")
        elif code:
            mode_failures.append(f"PRIMARY_VALIDATION_{mode.value}:{code}")
    base = evaluate_productive_ddo_export_for_g2_primary_evidence_ingress_v1(
        json.loads(artifact_path.read_text(encoding="utf-8"))
        if artifact_path.is_file()
        else {"join_seam_id": "", "optimization_ack_status": ""}
    )
    merged = tuple(dict.fromkeys(base.reason_codes + tuple(mode_failures)))
    return ProductiveLearningToG2PrimaryIngressEvaluationV1(
        semantic_adjudication=base.semantic_adjudication,
        bridge_authorized_by_owner_go=base.bridge_authorized_by_owner_go,
        bridge_implemented=base.bridge_implemented,
        g2_ingress_admitted=False,
        fail_closed=True,
        reason_codes=merged,
        source_terminal=base.source_terminal,
        g2_required_primary_evidence_semantics=base.g2_required_primary_evidence_semantics,
        lifecycle_state_fabricated=LIFECYCLE_STATE_FABRICATED,
        productive_optimization_join_authorized=PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED is True,
        lineage_preserved=True,
    )


def prove_semantic_adjudication_case_b_invariants_v1(*, repo_root: Path | None = None) -> bool:
    """Static corroboration against decision config and G2 projection admission contract."""
    cfg = load_decision_config_v1(repo_root=repo_root)
    if cfg.get("semantic_adjudication") != SEMANTIC_ADJUDICATION_CASE_B:
        return False
    if cfg.get("bridge_implementation_authorized") is True:
        return False
    if cfg.get("lifecycle_state_fabricated") is True:
        return False
    if cfg.get("productive_optimization_join_authorized") is True:
        return False
    if cfg.get("external_effect") is True:
        return False
    supported = tuple(str(x).upper() for x in cfg.get("g2_primary_supported_modes") or ())
    if supported != G2_PRIMARY_SUPPORTED_MODES:
        return False
    if PRODUCTIVE_RUNTIME_CLASS in supported:
        return False
    return True


def run_legitimate_g2_primary_to_m4_m8_reference_continuation_v1(
    *,
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
    replay_seed: int | None = None,
    classification: str = "LEGITIMATE_PRIMARY_EVIDENCE_FIXTURE_OR_DURABLE_ARCHIVE",
) -> LegitimateG2M4M8ReferenceContinuationResultV1:
    """Reference continuation through existing G2→M4–M8 owner (no productive bridge)."""
    if projection_request.source_mode.value not in G2_PRIMARY_SUPPORTED_MODES:
        raise ValueError("SOURCE_MODE_NOT_G2_PRIMARY_SUPPORTED")
    g2 = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(
            projection_request=projection_request,
            replay_seed=replay_seed,
            ddo_fixture_learning_state=None,
        )
    )
    loop = g2.m4_m8_loop or {}
    m8 = (
        loop.get("status") == LOOP_STATUS_COMPLETE
        and loop.get("forward_return_loop_closed") is True
    )
    return LegitimateG2M4M8ReferenceContinuationResultV1(
        classification=classification,
        g2_result=g2,
        m8_reached=m8,
        productive_apply_reached=False,
    )


__all__ = [
    "BRIDGE_IMPLEMENTATION_AUTHORIZED",
    "DECISION_CONFIG",
    "G2_PRIMARY_EVIDENCE_DOMAIN",
    "G2_PRIMARY_SUPPORTED_MODES",
    "LIFECYCLE_STATE_FABRICATED",
    "NORMATIVE_SPEC",
    "PRODUCTIVE_RUNTIME_CLASS",
    "ProductiveDdoOfflineExportHandoffSnapshotV1",
    "ProductiveLearningToG2PrimaryIngressEvaluationV1",
    "LegitimateG2M4M8ReferenceContinuationResultV1",
    "SEMANTIC_ADJUDICATION_CASE_B",
    "WORKPACKAGE_ID",
    "evaluate_handoff_artifact_path_as_primary_evidence_root_v1",
    "evaluate_productive_ddo_export_for_g2_primary_evidence_ingress_v1",
    "load_decision_config_v1",
    "prove_semantic_adjudication_case_b_invariants_v1",
    "run_legitimate_g2_primary_to_m4_m8_reference_continuation_v1",
    "snapshot_from_productive_ddo_handoff_mapping_v1",
]
