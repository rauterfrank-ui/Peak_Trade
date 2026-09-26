"""Real P4 L6 SEAM_BOUND → governed runtime apply materialization (real mechanical path).

Composes proven P3/P4 L6 real continuation with canonical runtime apply materialization
ingress, admission, operation, and fail-closed consumer boundary. Authority=NONE for
productive activation, Component B, venue POST, and external effects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from src.governance.governed_real_component_a_admit_to_p3_p4_l6_productive_seam_real_mechanical_continuation_v1 import (
    RealP3P4ProductiveSeamContinuationRequestV1,
    run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1,
    validate_real_component_a_to_p3_p4_lineage_join_v1,
)
from src.governance.governed_runtime_apply_materialization_record_v1 import (
    RuntimeApplyMaterializationDecisionStateV1,
)
from src.governance.governed_runtime_apply_materialization_v1 import (
    COMPONENT_B_ACTIVATED,
    CONFIGURATION_APPLIED,
    EXTERNAL_EFFECT_AUTHORIZED,
    NORMATIVE_SPEC,
    OWNER_WP_DECISION_CONFIG,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    RUNTIME_APPLY_STARTED,
    RuntimeApplyMaterializationEvaluateRequestV1,
    RuntimeApplyMaterializationIngressV1,
    evaluate_runtime_apply_materialization_v1,
    prove_negative_runtime_apply_materialization_safety_invariants_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    GovernedRuntimePrimaryProjectionRequestV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    A_RUNTIME_IMPLEMENTATION_AUTHORIZED as P2_A_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED as P3_B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    PRODUCTIVE_ACTIVATION_AUTHORIZED as P4_PRODUCTIVE_ACTIVATION_AUTHORIZED,
    SEAM_BIND_DISPOSITION,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = (
    "governed_p4_l6_seam_to_runtime_apply_materialization_real_mechanical_continuation_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_P4_L6_SEAM_TO_RUNTIME_APPLY_MATERIALIZATION_REAL_MECHANICAL_CONTINUATION_V1"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_p4_l6_seam_to_runtime_apply_materialization_real_mechanical_continuation_v1_decision_v1.json"
)

P4_L6_REAL_SEAM_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
RUNTIME_APPLY_INGRESS_STATUS: Final[str] = "PROVEN_ON_SUCCESS"
RUNTIME_APPLY_AUTHORIZATION_STATUS: Final[str] = "BOUNDED_MATERIALIZATION_RECORD_ONLY"
RUNTIME_MATERIALIZATION_STATUS: Final[str] = "SEAM_SCOPED_TYPED_RECORD"
APPLY_RECORD_STATUS: Final[str] = "MATERIALIZATION_RECORD_PRODUCED"

CONFIGURATION_MATERIALIZED: Final[bool] = False
RUNTIME_APPLY_COMPLETED: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RealP4RuntimeApplyMaterializationContinuationRequestV1:
    projection_request: GovernedRuntimePrimaryProjectionRequestV1
    replay_seed: int | None = None
    ddo_fixture_learning_state: dict[str, Any] | None = None
    repo_root: Path | None = None
    request_materialization_authorization: bool = True


@dataclass(frozen=True)
class RealP4RuntimeApplyMaterializationContinuationResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    p4_seam_disposition: str | None
    p4_l6_seam_result_digest: str | None
    p3_binding_result_digest: str | None
    materialization_decision_state: str | None
    materialization_record_digest: str | None
    materialization_record: dict[str, Any] | None = None
    lineage_chain: tuple[str, ...] = field(default_factory=tuple)
    real_upstream_source_used: bool = False
    ddo_fixture_state_used: bool = False
    p4_l6_real_seam_used: bool = False
    runtime_apply_ingress_reached: bool = False
    runtime_apply_authorization_valid: bool = False
    runtime_materialization_performed: bool = False
    apply_record_produced: bool = False
    configuration_materialized: bool = False
    configuration_applied: bool = False
    lineage_join_valid: bool = False


def _digest_from_lineage_v1(*, prefix: str, lineage_chain: tuple[str, ...]) -> str | None:
    needle = f"{prefix}://"
    for ref in lineage_chain:
        if ref.startswith(needle):
            digest = ref[len(needle) :]
            if is_valid_sha256_hex(digest):
                return digest
    return None


def run_real_runtime_p4_l6_to_runtime_apply_materialization_continuation_v1(
    request: RealP4RuntimeApplyMaterializationContinuationRequestV1,
) -> RealP4RuntimeApplyMaterializationContinuationResultV1:
    root = request.repo_root or _REPO_ROOT
    prior = run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1(
        RealP3P4ProductiveSeamContinuationRequestV1(
            projection_request=request.projection_request,
            replay_seed=request.replay_seed,
            ddo_fixture_learning_state=request.ddo_fixture_learning_state,
            repo_root=root,
        )
    )
    base_lineage = prior.lineage_chain
    if prior.status != "CONTINUATION_COMPLETE":
        return RealP4RuntimeApplyMaterializationContinuationResultV1(
            status="REJECTED",
            decision_code=prior.decision_code,
            blocking_reasons=prior.blocking_reasons,
            p4_seam_disposition=prior.p4_seam_disposition,
            p4_l6_seam_result_digest=prior.p4_seam_result_digest,
            p3_binding_result_digest=prior.p3_binding_result_digest,
            materialization_decision_state=None,
            materialization_record_digest=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=prior.real_upstream_source_used,
            ddo_fixture_state_used=prior.ddo_fixture_state_used,
            p4_l6_real_seam_used=prior.p4_l6_seam_reached,
            lineage_join_valid=prior.lineage_join_valid,
        )

    p4_digest = prior.p4_seam_result_digest or _digest_from_lineage_v1(
        prefix="p4_l6_seam", lineage_chain=base_lineage
    )
    p3_digest = prior.p3_binding_result_digest or _digest_from_lineage_v1(
        prefix="p3_binding", lineage_chain=base_lineage
    )
    adj_digest = prior.component_a_adjudication_digest or _digest_from_lineage_v1(
        prefix="adjudicator_a_opt", lineage_chain=base_lineage
    )
    env_hash = str((prior.optimization_envelope_evidence or {}).get("content_hash") or "")
    if not env_hash:
        env_hash = (
            _digest_from_lineage_v1(prefix="optimization_envelope", lineage_chain=base_lineage)
            or ""
        )

    join_reasons = validate_real_component_a_to_p3_p4_lineage_join_v1(
        lineage_chain=base_lineage,
        optimization_adjudication_digest=str(adj_digest or ""),
        optimization_envelope_content_hash=env_hash,
        expected_envelope_in_lineage=env_hash,
    )
    if join_reasons or not p4_digest or not p3_digest or not adj_digest or not env_hash:
        reasons = list(join_reasons)
        if not p4_digest:
            reasons.append("P4_L6_SEAM_DIGEST_MISSING")
        if not p3_digest:
            reasons.append("P3_BINDING_DIGEST_MISSING")
        if not adj_digest:
            reasons.append("COMPONENT_A_ADJUDICATION_DIGEST_MISSING")
        if not env_hash:
            reasons.append("OPTIMIZATION_ENVELOPE_HASH_MISSING")
        return RealP4RuntimeApplyMaterializationContinuationResultV1(
            status="REJECTED",
            decision_code=reasons[0] if reasons else "LINEAGE_JOIN_INVALID",
            blocking_reasons=tuple(reasons),
            p4_seam_disposition=prior.p4_seam_disposition,
            p4_l6_seam_result_digest=p4_digest,
            p3_binding_result_digest=p3_digest,
            materialization_decision_state=None,
            materialization_record_digest=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
            p4_l6_real_seam_used=True,
            lineage_join_valid=False,
        )

    ingress = RuntimeApplyMaterializationIngressV1(
        p4_l6_seam_result_digest=p4_digest,
        p3_binding_result_digest=p3_digest,
        component_a_adjudication_digest=adj_digest,
        optimization_envelope_content_hash=env_hash,
        p4_seam_disposition=str(prior.p4_seam_disposition or SEAM_BIND_DISPOSITION),
        lineage_chain=base_lineage,
        real_upstream_source_used=True,
        ddo_fixture_state_used=False,
    )
    mat = evaluate_runtime_apply_materialization_v1(
        RuntimeApplyMaterializationEvaluateRequestV1(
            ingress=ingress,
            request_materialization_authorization=request.request_materialization_authorization,
        ),
        repo_root=root,
    )
    if mat.decision_state == RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_DENIED:
        return RealP4RuntimeApplyMaterializationContinuationResultV1(
            status="REJECTED",
            decision_code=mat.reason_codes[0] if mat.reason_codes else "MATERIALIZATION_DENIED",
            blocking_reasons=mat.reason_codes,
            p4_seam_disposition=prior.p4_seam_disposition,
            p4_l6_seam_result_digest=p4_digest,
            p3_binding_result_digest=p3_digest,
            materialization_decision_state=mat.decision_state.value,
            materialization_record_digest=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
            p4_l6_real_seam_used=True,
            runtime_apply_ingress_reached=mat.runtime_apply_ingress_reached,
            runtime_apply_authorization_valid=False,
            lineage_join_valid=True,
        )

    record_digest = (
        mat.materialization_record.materialization_record_digest
        if mat.materialization_record
        else None
    )
    extended = (
        *base_lineage,
        f"runtime_apply_materialization://{record_digest or ''}",
    )
    return RealP4RuntimeApplyMaterializationContinuationResultV1(
        status="CONTINUATION_COMPLETE",
        decision_code="REAL_P4_L6_RUNTIME_APPLY_MATERIALIZATION_CONTINUATION_COMPLETE",
        blocking_reasons=(),
        p4_seam_disposition=prior.p4_seam_disposition,
        p4_l6_seam_result_digest=p4_digest,
        p3_binding_result_digest=p3_digest,
        materialization_decision_state=mat.decision_state.value,
        materialization_record_digest=record_digest,
        materialization_record=(
            dict(mat.materialization_record.materialization_record)
            if mat.materialization_record
            else None
        ),
        lineage_chain=extended,
        real_upstream_source_used=True,
        ddo_fixture_state_used=False,
        p4_l6_real_seam_used=True,
        runtime_apply_ingress_reached=mat.runtime_apply_ingress_reached,
        runtime_apply_authorization_valid=mat.runtime_apply_authorization_valid,
        runtime_materialization_performed=mat.real_runtime_materialization_performed,
        apply_record_produced=mat.materialization_record is not None,
        configuration_materialized=mat.configuration_materialized,
        configuration_applied=mat.configuration_applied,
        lineage_join_valid=True,
    )


def prove_real_p4_l6_runtime_apply_materialization_continuation_v1(
    *,
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
    repo_root: Path | None = None,
) -> bool:
    result = run_real_runtime_p4_l6_to_runtime_apply_materialization_continuation_v1(
        RealP4RuntimeApplyMaterializationContinuationRequestV1(
            projection_request=projection_request,
            repo_root=repo_root,
        )
    )
    if result.status != "CONTINUATION_COMPLETE":
        return False
    return (
        result.real_upstream_source_used
        and not result.ddo_fixture_state_used
        and result.p4_l6_real_seam_used
        and result.runtime_apply_ingress_reached
        and result.runtime_materialization_performed
        and result.apply_record_produced
        and result.configuration_materialized
        and not result.configuration_applied
        and result.lineage_join_valid
    )


def prove_continuation_authority_invariants_v1() -> bool:
    return (
        prove_negative_runtime_apply_materialization_safety_invariants_v1()
        and RUNTIME_APPLY_STARTED is False
        and CONFIGURATION_APPLIED is False
        and PRODUCTIVE_ACTIVATION_AUTHORIZED is False
        and EXTERNAL_EFFECT_AUTHORIZED is False
        and COMPONENT_B_ACTIVATED is False
        and P2_A_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
        and P3_B_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
        and P4_PRODUCTIVE_ACTIVATION_AUTHORIZED is False
        and RUNTIME_APPLY_COMPLETED is False
    )


def prove_continuation_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    paths = (
        DECISION_CONFIG,
        OWNER_WP_DECISION_CONFIG,
        NORMATIVE_SPEC,
        "src/governance/governed_runtime_apply_materialization_v1.py",
        "src/governance/governed_runtime_apply_materialization_record_v1.py",
        "src/governance/"
        "governed_p4_l6_seam_to_runtime_apply_materialization_real_mechanical_continuation_v1.py",
        "tests/governance/"
        "test_governed_p4_l6_seam_to_runtime_apply_materialization_real_mechanical_continuation_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))
    return (
        decision.get("workpackage_id") == WORKPACKAGE_ID
        and owner.get("runtime_apply_wp_authorized") is True
        and decision.get("runtime_apply_started") is False
        and decision.get("productive_activation_authorized") is False
    )


__all__ = [
    "APPLY_RECORD_STATUS",
    "CONFIGURATION_APPLIED",
    "CONFIGURATION_MATERIALIZED",
    "DECISION_CONFIG",
    "NORMATIVE_SPEC",
    "OWNER_WP_DECISION_CONFIG",
    "P4_L6_REAL_SEAM_STATUS",
    "RUNTIME_APPLY_AUTHORIZATION_STATUS",
    "RUNTIME_APPLY_COMPLETED",
    "RUNTIME_APPLY_INGRESS_STATUS",
    "RUNTIME_APPLY_STARTED",
    "RUNTIME_MATERIALIZATION_STATUS",
    "RealP4RuntimeApplyMaterializationContinuationRequestV1",
    "RealP4RuntimeApplyMaterializationContinuationResultV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_continuation_authority_invariants_v1",
    "prove_continuation_decision_files_v1",
    "prove_real_p4_l6_runtime_apply_materialization_continuation_v1",
    "run_real_runtime_p4_l6_to_runtime_apply_materialization_continuation_v1",
]
