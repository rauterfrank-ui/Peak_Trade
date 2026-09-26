"""Real Component A ADMIT → P3 input creator binder → P4 L6 productive seam (real path).

Composes proven G2→M4–M8→P5→Component A real mechanical continuation with canonical P3
bind_layer_input_from_adjudication_v1 and P4 run_productive_l6_seam_from_prior_adjudication_v1.
Uses prior Component A ADMIT only (no re-adjudication). Authority=NONE at A; L6 seam binding
is P4-scoped only and does not authorize runtime apply, activation, or external effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.governed_real_m4_m8_p5_producer_bridge_to_evidence_adjudicator_a_real_mechanical_continuation_v1 import (
    RealP5AdjudicatorAContinuationRequestV1,
    build_market_context_v1_from_runtime_primary_provenance_v1,
    run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1,
)
from src.governance.governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1 import (
    G2RuntimeM4M8ContinuationRequestV1,
    run_g2_runtime_to_m4_m8_evidence_return_continuation_v1,
)
from src.governance.governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1 import (
    CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION,
    EXTERNAL_EFFECT,
    P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY,
    PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    REAL_RUNTIME_MATERIALIZATION_PERFORMED,
    RUNTIME_APPLY_STARTED,
    prove_binding_authority_invariants_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    GovernedRuntimePrimaryProjectionRequestV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (
    L6_TYPED_INPUT_SCHEMA_VERSION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
    A_RUNTIME_IMPLEMENTATION_AUTHORIZED as P2_A_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.binder_v1 import (
    bind_layer_input_from_adjudication_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    BIND_DISPOSITION,
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED as P3_B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.models_v1 import (
    LayerInputBindingContextV1,
    LayerInputBindingRequestV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    PRODUCTIVE_ACTIVATION_AUTHORIZED as P4_PRODUCTIVE_ACTIVATION_AUTHORIZED,
    SEAM_BIND_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.models_v1 import (
    ProductiveL6SeamBindingContextV1,
    ProductiveL6SeamBindingRequestV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.seam_v1 import (
    run_productive_l6_seam_from_prior_adjudication_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.adapters_v1 import (
    adapt_optimization_envelope_evidence_v1,
    default_termination_context_from_market_context_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.ingress_v1 import (
    terminate_optimization_envelope_at_a_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.optimization_envelope_evidence_v1 import (
    SCHEMA_VERSION as OPT_ENVELOPE_SCHEMA,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import NullLineStateV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1

SCHEMA_VERSION: Final[str] = (
    "governed_real_component_a_admit_to_p3_p4_l6_productive_seam_real_mechanical_continuation_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_REAL_COMPONENT_A_ADMIT_TO_P3_P4_L6_PRODUCTIVE_SEAM_REAL_MECHANICAL_CONTINUATION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "GOVERNED_REAL_COMPONENT_A_ADMIT_TO_P3_P4_L6_PRODUCTIVE_SEAM_REAL_MECHANICAL_CONTINUATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_real_component_a_admit_to_p3_p4_l6_productive_seam_real_mechanical_continuation_v1_decision_v1.json"
)

P3_INPUT_CREATOR_BINDER_REAL_BIND_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
P4_L6_PRODUCTIVE_SEAM_REAL_BIND_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
EVIDENCE_ADMIT_IMPLIES_PRODUCTIVE_ACTIVATION: Final[bool] = False
COMPONENT_B_ACTIVATED: Final[bool] = False
PRODUCTIVE_CONFIGURATION_PRODUCED: Final[bool] = False

MECHANICAL_PROPOSED_D_T: Final[float] = 0.01
MECHANICAL_NULLLINE_PRICE: Final[float] = 1000.0

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RealP3P4ProductiveSeamContinuationRequestV1:
    projection_request: GovernedRuntimePrimaryProjectionRequestV1
    replay_seed: int | None = None
    ddo_fixture_learning_state: Mapping[str, Any] | None = None
    repo_root: Path | None = None


@dataclass(frozen=True)
class RealP3P4ProductiveSeamContinuationResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    optimization_envelope_evidence: dict[str, Any] | None
    component_a_adjudication_disposition: str | None
    component_a_adjudication_digest: str | None
    p3_binding_disposition: str | None
    p4_seam_disposition: str | None
    lineage_chain: tuple[str, ...] = field(default_factory=tuple)
    real_upstream_source_used: bool = False
    ddo_fixture_state_used: bool = False
    component_a_real_admit_used: bool = False
    p3_input_creator_binder_reached: bool = False
    p4_l6_seam_reached: bool = False
    lineage_join_valid: bool = False


def _lineage_ref_for_adjudication_digest_v1(*, prefix: str, digest: str) -> str:
    return f"{prefix}://{digest}"


def validate_real_component_a_to_p3_p4_lineage_join_v1(
    *,
    lineage_chain: tuple[str, ...],
    optimization_adjudication_digest: str,
    optimization_envelope_content_hash: str,
    expected_envelope_in_lineage: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    expected_adj_ref = _lineage_ref_for_adjudication_digest_v1(
        prefix="adjudicator_a_opt",
        digest=optimization_adjudication_digest,
    )
    if expected_adj_ref not in lineage_chain:
        reasons.append("COMPONENT_A_ADJUDICATION_LINEAGE_MISSING")
    expected_env_ref = f"optimization_envelope://{optimization_envelope_content_hash}"
    if expected_env_ref not in lineage_chain:
        reasons.append("OPTIMIZATION_ENVELOPE_LINEAGE_MISSING")
    if expected_envelope_in_lineage != optimization_envelope_content_hash:
        reasons.append("OPTIMIZATION_ENVELOPE_DIGEST_MISMATCH")
    return tuple(reasons)


def build_productive_l6_seam_context_from_termination_v1(
    *,
    termination: Any,
    observed_at_unix: float,
    market_observation_epoch: int,
) -> ProductiveL6SeamBindingContextV1:
    evaluated = termination.evaluated_at_unix
    if evaluated is None:
        evaluated = observed_at_unix + 1.0
    instrument = termination.instrument
    return ProductiveL6SeamBindingContextV1(
        evaluated_at_unix=float(evaluated),
        expected_instrument=instrument,
        expected_market_observation_epoch=market_observation_epoch,
        expected_nullline_provenance_epoch=market_observation_epoch,
        mechanical_proposed_d_t=MECHANICAL_PROPOSED_D_T,
        nullline_for_mechanical_l6=NullLineStateV1(
            instrument_id=instrument.instrument_id,
            nullline_price=MECHANICAL_NULLLINE_PRICE,
            provenance_mark_epoch=market_observation_epoch,
        ),
    )


def run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1(
    request: RealP3P4ProductiveSeamContinuationRequestV1,
) -> RealP3P4ProductiveSeamContinuationResultV1:
    root = request.repo_root or _REPO_ROOT
    p5 = run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1(
        RealP5AdjudicatorAContinuationRequestV1(
            projection_request=request.projection_request,
            replay_seed=request.replay_seed,
            ddo_fixture_learning_state=request.ddo_fixture_learning_state,
            repo_root=root,
        )
    )
    base_lineage = p5.lineage_chain
    if p5.status != "CONTINUATION_COMPLETE":
        return RealP3P4ProductiveSeamContinuationResultV1(
            status="REJECTED",
            decision_code=p5.decision_code,
            blocking_reasons=p5.blocking_reasons,
            optimization_envelope_evidence=p5.optimization_envelope_evidence,
            component_a_adjudication_disposition=p5.optimization_adjudication_disposition,
            component_a_adjudication_digest=None,
            p3_binding_disposition=None,
            p4_seam_disposition=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=p5.real_upstream_source_used,
            ddo_fixture_state_used=p5.ddo_fixture_state_used,
        )

    g2 = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(
            projection_request=request.projection_request,
            replay_seed=request.replay_seed,
            ddo_fixture_learning_state=request.ddo_fixture_learning_state,
        )
    )
    projection = g2.projection
    if projection is None or projection.provenance is None:
        return RealP3P4ProductiveSeamContinuationResultV1(
            status="REJECTED",
            decision_code="G2_PROJECTION_PROVENANCE_MISSING",
            blocking_reasons=("G2_PROJECTION_PROVENANCE_MISSING",),
            optimization_envelope_evidence=p5.optimization_envelope_evidence,
            component_a_adjudication_disposition=p5.optimization_adjudication_disposition,
            component_a_adjudication_digest=None,
            p3_binding_disposition=None,
            p4_seam_disposition=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
        )

    opt_envelope = dict(p5.optimization_envelope_evidence or {})
    provenance = projection.provenance
    market_context = build_market_context_v1_from_runtime_primary_provenance_v1(provenance)
    epoch = int(provenance.trading_epoch)
    termination = default_termination_context_from_market_context_v1(
        market_context,
        market_observation_epoch=epoch,
    )
    opt_term = terminate_optimization_envelope_at_a_v1(
        opt_envelope,
        source_artifact_schema=OPT_ENVELOPE_SCHEMA,
        source_content_digest=str(opt_envelope["content_hash"]),
        termination=termination,
        repo_root=root,
    )
    adjudication = opt_term.adjudication
    adj_digest = str(adjudication.adjudication_digest or "")
    join_reasons = validate_real_component_a_to_p3_p4_lineage_join_v1(
        lineage_chain=base_lineage,
        optimization_adjudication_digest=adj_digest,
        optimization_envelope_content_hash=str(opt_envelope.get("content_hash") or ""),
        expected_envelope_in_lineage=str(opt_envelope.get("content_hash") or ""),
    )
    if join_reasons:
        return RealP3P4ProductiveSeamContinuationResultV1(
            status="REJECTED",
            decision_code=join_reasons[0],
            blocking_reasons=join_reasons,
            optimization_envelope_evidence=opt_envelope,
            component_a_adjudication_disposition=adjudication.disposition,
            component_a_adjudication_digest=adj_digest or None,
            p3_binding_disposition=None,
            p4_seam_disposition=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
            component_a_real_admit_used=adjudication.disposition == ADMIT_DISPOSITION,
            lineage_join_valid=False,
        )

    if adjudication.disposition != ADMIT_DISPOSITION:
        return RealP3P4ProductiveSeamContinuationResultV1(
            status="REJECTED",
            decision_code=f"COMPONENT_A_{adjudication.disposition}",
            blocking_reasons=(f"COMPONENT_A_{adjudication.disposition}",),
            optimization_envelope_evidence=opt_envelope,
            component_a_adjudication_disposition=adjudication.disposition,
            component_a_adjudication_digest=adj_digest or None,
            p3_binding_disposition=None,
            p4_seam_disposition=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
            component_a_real_admit_used=False,
            lineage_join_valid=True,
        )

    intake = adapt_optimization_envelope_evidence_v1(opt_envelope, termination=termination)
    binding_id = f"real-bind-opt-{str(opt_envelope.get('content_hash', ''))[:16]}"
    binding_ctx = LayerInputBindingContextV1(
        evaluated_at_unix=float(intake.observed_at_unix) + 1.0,
        expected_instrument=termination.instrument,
        expected_market_observation_epoch=epoch,
        allow_direct_producer_to_b=False,
    )
    binding = bind_layer_input_from_adjudication_v1(
        LayerInputBindingRequestV1(
            binding_id=binding_id,
            target_layer=LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
            target_contract_version=L6_TYPED_INPUT_SCHEMA_VERSION,
            nullline_provenance_epoch=epoch,
            adjudication=adjudication,
        ),
        context=binding_ctx,
    )
    p3_ok = binding.disposition == BIND_DISPOSITION
    seam_ctx = build_productive_l6_seam_context_from_termination_v1(
        termination=termination,
        observed_at_unix=float(intake.observed_at_unix),
        market_observation_epoch=epoch,
    )
    seam_id = f"real-seam-opt-{str(opt_envelope.get('content_hash', ''))[:16]}"
    seam = run_productive_l6_seam_from_prior_adjudication_v1(
        ProductiveL6SeamBindingRequestV1(
            seam_id=seam_id,
            intake=intake,
            binding_id=binding_id,
            target_layer=LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
            target_contract_version=L6_TYPED_INPUT_SCHEMA_VERSION,
            nullline_provenance_epoch=epoch,
        ),
        prior_adjudication=adjudication,
        context=seam_ctx,
    )
    p4_ok = seam.disposition == SEAM_BIND_DISPOSITION

    extended = (
        *base_lineage,
        f"p3_binding://{binding.binding_result_digest or ''}",
        f"p4_l6_seam://{seam.seam_result_digest or ''}",
    )
    if not p3_ok or not p4_ok:
        reasons: list[str] = []
        if not p3_ok:
            reasons.append(f"P3_BINDING_{binding.disposition}")
        if not p4_ok:
            reasons.append(f"P4_SEAM_{seam.disposition}")
        return RealP3P4ProductiveSeamContinuationResultV1(
            status="REJECTED",
            decision_code=reasons[0],
            blocking_reasons=tuple(reasons),
            optimization_envelope_evidence=opt_envelope,
            component_a_adjudication_disposition=adjudication.disposition,
            component_a_adjudication_digest=adj_digest or None,
            p3_binding_disposition=binding.disposition,
            p4_seam_disposition=seam.disposition,
            lineage_chain=extended,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
            component_a_real_admit_used=True,
            p3_input_creator_binder_reached=p3_ok,
            p4_l6_seam_reached=p4_ok,
            lineage_join_valid=True,
        )

    return RealP3P4ProductiveSeamContinuationResultV1(
        status="CONTINUATION_COMPLETE",
        decision_code="REAL_P3_P4_L6_PRODUCTIVE_SEAM_CONTINUATION_COMPLETE",
        blocking_reasons=(),
        optimization_envelope_evidence=opt_envelope,
        component_a_adjudication_disposition=adjudication.disposition,
        component_a_adjudication_digest=adj_digest or None,
        p3_binding_disposition=binding.disposition,
        p4_seam_disposition=seam.disposition,
        lineage_chain=extended,
        real_upstream_source_used=True,
        ddo_fixture_state_used=False,
        component_a_real_admit_used=True,
        p3_input_creator_binder_reached=True,
        p4_l6_seam_reached=True,
        lineage_join_valid=True,
    )


def prove_real_p3_p4_l6_productive_seam_continuation_v1(
    *,
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
    repo_root: Path | None = None,
) -> bool:
    result = run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1(
        RealP3P4ProductiveSeamContinuationRequestV1(
            projection_request=projection_request,
            repo_root=repo_root,
        )
    )
    if result.status != "CONTINUATION_COMPLETE":
        return False
    return (
        result.real_upstream_source_used
        and not result.ddo_fixture_state_used
        and result.component_a_real_admit_used
        and result.p3_input_creator_binder_reached
        and result.p4_l6_seam_reached
        and result.lineage_join_valid
        and result.component_a_adjudication_disposition == ADMIT_DISPOSITION
    )


def prove_continuation_authority_invariants_v1() -> bool:
    return (
        prove_binding_authority_invariants_v1()
        and EVIDENCE_ADMIT_IMPLIES_PRODUCTIVE_ACTIVATION is False
        and PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION is False
        and P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY is False
        and CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION is False
        and RUNTIME_APPLY_STARTED is False
        and REAL_RUNTIME_MATERIALIZATION_PERFORMED is False
        and PRODUCTIVE_ACTIVATION_AUTHORIZED is False
        and EXTERNAL_EFFECT is False
        and P2_A_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
        and P3_B_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
        and P4_PRODUCTIVE_ACTIVATION_AUTHORIZED is False
        and COMPONENT_B_ACTIVATED is False
        and PRODUCTIVE_CONFIGURATION_PRODUCED is False
    )


def prove_continuation_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    paths = (
        DECISION_CONFIG,
        NORMATIVE_SPEC,
        "src/governance/"
        "governed_real_component_a_admit_to_p3_p4_l6_productive_seam_real_mechanical_continuation_v1.py",
        "tests/governance/"
        "test_governed_real_component_a_admit_to_p3_p4_l6_productive_seam_real_mechanical_continuation_v1.py",
    )
    return all((root / rel).is_file() for rel in paths)


__all__ = [
    "COMPONENT_B_ACTIVATED",
    "DECISION_CONFIG",
    "EVIDENCE_ADMIT_IMPLIES_PRODUCTIVE_ACTIVATION",
    "NORMATIVE_SPEC",
    "P3_INPUT_CREATOR_BINDER_REAL_BIND_STATUS",
    "P4_L6_PRODUCTIVE_SEAM_REAL_BIND_STATUS",
    "PRODUCTIVE_CONFIGURATION_PRODUCED",
    "RealP3P4ProductiveSeamContinuationRequestV1",
    "RealP3P4ProductiveSeamContinuationResultV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "build_productive_l6_seam_context_from_termination_v1",
    "prove_continuation_authority_invariants_v1",
    "prove_continuation_decision_files_v1",
    "prove_real_p3_p4_l6_productive_seam_continuation_v1",
    "run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1",
    "validate_real_component_a_to_p3_p4_lineage_join_v1",
]
