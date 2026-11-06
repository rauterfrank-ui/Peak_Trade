"""Real M4–M8 upstream → P5 producer bridges → Evidence Adjudicator A (real path).

Composes proven G2→M4–M8→M6/M7 real mechanical continuation with existing P5 bridges and
Component A termination. Market context is derived from G2 primary provenance only.
Authority=NONE; evidence acceptance does not imply productive authorization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.governed_m4_m8_evidence_return_to_meta_learning_optimization_feedback_real_mechanical_continuation_v1 import (
    validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1,
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
    RuntimePrimaryProvenanceBindingV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.adapters_v1 import (
    default_termination_context_from_market_context_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.ingress_v1 import (
    terminate_meta_learning_routed_at_a_v1,
    terminate_optimization_envelope_at_a_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.meta_learning_routed_evidence_v1 import (
    SCHEMA_VERSION as META_ROUTED_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.optimization_envelope_evidence_v1 import (
    SCHEMA_VERSION as OPT_ENVELOPE_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.p5_m4_m8_producer_bridge_v1 import (
    bridge_m5_to_optimization_envelope_evidence_v1,
    bridge_m6_to_meta_learning_routed_evidence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    GovernedMarketContextInputsV1,
    compose_market_context_v1_from_governed_inputs,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = (
    "governed_real_m4_m8_p5_producer_bridge_to_evidence_adjudicator_a_real_mechanical_continuation_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_REAL_M4_M8_P5_PRODUCER_BRIDGE_TO_EVIDENCE_ADJUDICATOR_A_REAL_MECHANICAL_CONTINUATION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "GOVERNED_REAL_M4_M8_P5_PRODUCER_BRIDGE_TO_EVIDENCE_ADJUDICATOR_A_REAL_MECHANICAL_CONTINUATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_real_m4_m8_p5_producer_bridge_to_evidence_adjudicator_a_real_mechanical_continuation_v1_decision_v1.json"
)

P5_OPTIMIZATION_ENVELOPE_BRIDGE_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
P5_META_LEARNING_ROUTED_BRIDGE_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
EVIDENCE_ADJUDICATOR_A_REAL_INGRESS_STATUS: Final[str] = "PROVEN_REAL_MECHANICAL_PATH"
EVIDENCE_ACCEPTANCE_IMPLIES_PRODUCTIVE_AUTHORIZATION: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RealP5AdjudicatorAContinuationRequestV1:
    projection_request: GovernedRuntimePrimaryProjectionRequestV1
    replay_seed: int | None = None
    ddo_fixture_learning_state: Mapping[str, Any] | None = None
    repo_root: Path | None = None


@dataclass(frozen=True)
class RealP5AdjudicatorAContinuationResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    optimization_envelope_evidence: dict[str, Any] | None
    meta_learning_routed_evidence: dict[str, Any] | None
    optimization_adjudication_disposition: str | None
    meta_adjudication_disposition: str | None
    lineage_chain: tuple[str, ...] = field(default_factory=tuple)
    real_upstream_source_used: bool = False
    ddo_fixture_state_used: bool = False
    p5_producer_bridge_reached: bool = False
    evidence_adjudicator_a_reached: bool = False
    lineage_join_valid: bool = False


def build_market_context_v1_from_runtime_primary_provenance_v1(
    provenance: RuntimePrimaryProvenanceBindingV1,
) -> dict[str, Any]:
    """Mechanical market_context_v1 from G2 primary provenance (no instrument/time fabrication)."""
    instrument = str(provenance.instrument_identity).strip()
    observed_at = str(provenance.observation_time_utc).strip()
    primary_digest = str(provenance.primary_evidence_manifest_digest).strip()
    if not instrument or not observed_at:
        raise ValueError("RUNTIME_PRIMARY_PROVENANCE_INCOMPLETE")
    if not is_valid_sha256_hex(primary_digest):
        raise ValueError("PRIMARY_MANIFEST_DIGEST_INVALID")
    provenance_ref = f"g2.primary.{primary_digest}"
    inputs = GovernedMarketContextInputsV1(
        observed_at=observed_at,
        instrument_ref=instrument,
        information_set_identity_body={
            "pit_observed_at_utc": observed_at,
            "instrument_ref": instrument,
            "primary_evidence_manifest_digest": primary_digest,
            "source_execution_mode": provenance.source_execution_mode,
        },
        provenance_refs=(provenance_ref,),
        feature_versions={
            "market_context_v1": "market_context_v1",
            "g2_runtime_primary_provenance_binding_v1": SCHEMA_VERSION,
        },
    )
    try:
        return dict(compose_market_context_v1_from_governed_inputs(inputs))
    except Exception as exc:
        raise ValueError(f"MARKET_CONTEXT_COMPOSE_FAILED:{exc}") from exc


def validate_p5_bridge_lineage_join_v1(
    *,
    optimization_experiment_evidence: Mapping[str, Any],
    meta_learning_evidence: Mapping[str, Any],
    optimization_envelope: Mapping[str, Any],
    meta_routed: Mapping[str, Any],
) -> tuple[str, ...]:
    reasons: list[str] = []
    m5_digest = str(optimization_experiment_evidence.get("content_hash") or "")
    m6_digest = str(meta_learning_evidence.get("reproducibility_digest") or "")
    if optimization_envelope.get("source_optimization_experiment_evidence_digest") != m5_digest:
        reasons.append("OPT_ENVELOPE_M5_DIGEST_MISMATCH")
    if meta_routed.get("source_meta_learning_reproducibility_digest") != m6_digest:
        reasons.append("META_ROUTED_M6_DIGEST_MISMATCH")
    if meta_routed.get("source_optimization_experiment_evidence_digest") != str(
        meta_learning_evidence.get("source_optimization_experiment_evidence_digest") or ""
    ):
        reasons.append("META_ROUTED_M6_LINEAGE_MISMATCH")
    return tuple(reasons)


def run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1(
    request: RealP5AdjudicatorAContinuationRequestV1,
) -> RealP5AdjudicatorAContinuationResultV1:
    root = request.repo_root or _REPO_ROOT
    g2_request = G2RuntimeM4M8ContinuationRequestV1(
        projection_request=request.projection_request,
        replay_seed=request.replay_seed,
        ddo_fixture_learning_state=request.ddo_fixture_learning_state,
    )
    g2 = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(g2_request)
    base_lineage = g2.lineage_chain

    if g2.status != "CONTINUATION_COMPLETE":
        return RealP5AdjudicatorAContinuationResultV1(
            status="REJECTED",
            decision_code=g2.decision_code,
            blocking_reasons=g2.blocking_reasons,
            optimization_envelope_evidence=None,
            meta_learning_routed_evidence=None,
            optimization_adjudication_disposition=None,
            meta_adjudication_disposition=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=g2.g2_real_source_used,
            ddo_fixture_state_used=g2.ddo_fixture_learning_state_used,
        )

    learning_evidence = g2.learning_evidence or {}
    loop = dict(g2.m4_m8_loop or {})
    join_reasons = validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1(
        learning_evidence=learning_evidence,
        m4_m8_loop=loop,
        require_runtime_g2_producer=True,
    )
    if join_reasons:
        return RealP5AdjudicatorAContinuationResultV1(
            status="REJECTED",
            decision_code=join_reasons[0],
            blocking_reasons=join_reasons,
            optimization_envelope_evidence=None,
            meta_learning_routed_evidence=None,
            optimization_adjudication_disposition=None,
            meta_adjudication_disposition=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
            p5_producer_bridge_reached=False,
        )

    projection = g2.projection
    if projection is None or projection.provenance is None:
        return RealP5AdjudicatorAContinuationResultV1(
            status="REJECTED",
            decision_code="G2_PROJECTION_PROVENANCE_MISSING",
            blocking_reasons=("G2_PROJECTION_PROVENANCE_MISSING",),
            optimization_envelope_evidence=None,
            meta_learning_routed_evidence=None,
            optimization_adjudication_disposition=None,
            meta_adjudication_disposition=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
        )

    provenance = projection.provenance
    try:
        market_context = build_market_context_v1_from_runtime_primary_provenance_v1(provenance)
    except ValueError as exc:
        code = str(exc)
        return RealP5AdjudicatorAContinuationResultV1(
            status="REJECTED",
            decision_code=code,
            blocking_reasons=(code,),
            optimization_envelope_evidence=None,
            meta_learning_routed_evidence=None,
            optimization_adjudication_disposition=None,
            meta_adjudication_disposition=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
        )

    cycle = loop.get("cycle") or {}
    m5 = cycle.get("optimization_experiment_evidence") or {}
    m6 = cycle.get("meta_learning_evidence") or {}
    epoch = int(provenance.trading_epoch)

    opt_envelope = dict(
        bridge_m5_to_optimization_envelope_evidence_v1(
            optimization_experiment_evidence=m5,
            market_context=market_context,
            market_observation_epoch=epoch,
        )
    )
    meta_routed = dict(
        bridge_m6_to_meta_learning_routed_evidence_v1(
            meta_learning_evidence=m6,
            market_context=market_context,
            market_observation_epoch=epoch,
        )
    )
    bridge_lineage_reasons = validate_p5_bridge_lineage_join_v1(
        optimization_experiment_evidence=m5,
        meta_learning_evidence=m6,
        optimization_envelope=opt_envelope,
        meta_routed=meta_routed,
    )
    if bridge_lineage_reasons:
        return RealP5AdjudicatorAContinuationResultV1(
            status="REJECTED",
            decision_code=bridge_lineage_reasons[0],
            blocking_reasons=bridge_lineage_reasons,
            optimization_envelope_evidence=opt_envelope,
            meta_learning_routed_evidence=meta_routed,
            optimization_adjudication_disposition=None,
            meta_adjudication_disposition=None,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
            p5_producer_bridge_reached=True,
            lineage_join_valid=False,
        )

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
    meta_term = terminate_meta_learning_routed_at_a_v1(
        meta_routed,
        source_artifact_schema=META_ROUTED_SCHEMA,
        source_content_digest=str(meta_routed["content_hash"]),
        termination=termination,
        repo_root=root,
    )
    opt_disp = opt_term.adjudication.disposition
    meta_disp = meta_term.adjudication.disposition
    a_reached = opt_disp == ADMIT_DISPOSITION and meta_disp == ADMIT_DISPOSITION

    if not a_reached:
        reasons = (
            f"OPT_ADJUDICATION_{opt_disp}",
            f"META_ADJUDICATION_{meta_disp}",
        )
        return RealP5AdjudicatorAContinuationResultV1(
            status="REJECTED",
            decision_code=reasons[0],
            blocking_reasons=reasons,
            optimization_envelope_evidence=opt_envelope,
            meta_learning_routed_evidence=meta_routed,
            optimization_adjudication_disposition=opt_disp,
            meta_adjudication_disposition=meta_disp,
            lineage_chain=base_lineage,
            real_upstream_source_used=True,
            ddo_fixture_state_used=False,
            p5_producer_bridge_reached=True,
            evidence_adjudicator_a_reached=False,
            lineage_join_valid=True,
        )

    extended = (
        *base_lineage,
        f"market_context://{market_context.get('content_digest', market_context.get('context_id', ''))}",
        f"optimization_envelope://{opt_envelope.get('content_hash', '')}",
        f"meta_learning_routed://{meta_routed.get('content_hash', '')}",
        f"adjudicator_a_opt://{opt_term.adjudication.adjudication_digest}",
        f"adjudicator_a_meta://{meta_term.adjudication.adjudication_digest}",
    )
    return RealP5AdjudicatorAContinuationResultV1(
        status="CONTINUATION_COMPLETE",
        decision_code="REAL_P5_BRIDGE_EVIDENCE_ADJUDICATOR_A_CONTINUATION_COMPLETE",
        blocking_reasons=(),
        optimization_envelope_evidence=opt_envelope,
        meta_learning_routed_evidence=meta_routed,
        optimization_adjudication_disposition=opt_disp,
        meta_adjudication_disposition=meta_disp,
        lineage_chain=extended,
        real_upstream_source_used=True,
        ddo_fixture_state_used=False,
        p5_producer_bridge_reached=True,
        evidence_adjudicator_a_reached=True,
        lineage_join_valid=True,
    )


def prove_real_p5_adjudicator_a_continuation_v1(
    *,
    projection_request: GovernedRuntimePrimaryProjectionRequestV1,
    repo_root: Path | None = None,
) -> bool:
    result = run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1(
        RealP5AdjudicatorAContinuationRequestV1(
            projection_request=projection_request,
            repo_root=repo_root,
        )
    )
    if result.status != "CONTINUATION_COMPLETE":
        return False
    return (
        result.real_upstream_source_used
        and not result.ddo_fixture_state_used
        and result.p5_producer_bridge_reached
        and result.evidence_adjudicator_a_reached
        and result.lineage_join_valid
        and result.optimization_adjudication_disposition == ADMIT_DISPOSITION
        and result.meta_adjudication_disposition == ADMIT_DISPOSITION
    )


def prove_continuation_authority_invariants_v1() -> bool:
    return (
        prove_binding_authority_invariants_v1()
        and EVIDENCE_ACCEPTANCE_IMPLIES_PRODUCTIVE_AUTHORIZATION is False
        and PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION is False
        and P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY is False
        and CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION is False
        and RUNTIME_APPLY_STARTED is False
        and REAL_RUNTIME_MATERIALIZATION_PERFORMED is False
        and PRODUCTIVE_ACTIVATION_AUTHORIZED is False
        and EXTERNAL_EFFECT is False
    )


def prove_continuation_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    paths = (
        DECISION_CONFIG,
        NORMATIVE_SPEC,
        "src/governance/"
        "governed_real_m4_m8_p5_producer_bridge_to_evidence_adjudicator_a_real_mechanical_continuation_v1.py",
        "tests/governance/"
        "test_governed_real_m4_m8_p5_producer_bridge_to_evidence_adjudicator_a_real_mechanical_continuation_v1.py",
    )
    return all((root / rel).is_file() for rel in paths)


__all__ = [
    "DECISION_CONFIG",
    "EVIDENCE_ACCEPTANCE_IMPLIES_PRODUCTIVE_AUTHORIZATION",
    "EVIDENCE_ADJUDICATOR_A_REAL_INGRESS_STATUS",
    "NORMATIVE_SPEC",
    "P5_META_LEARNING_ROUTED_BRIDGE_STATUS",
    "P5_OPTIMIZATION_ENVELOPE_BRIDGE_STATUS",
    "RealP5AdjudicatorAContinuationRequestV1",
    "RealP5AdjudicatorAContinuationResultV1",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "build_market_context_v1_from_runtime_primary_provenance_v1",
    "prove_continuation_authority_invariants_v1",
    "prove_continuation_decision_files_v1",
    "prove_real_p5_adjudicator_a_continuation_v1",
    "run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1",
    "validate_p5_bridge_lineage_join_v1",
]
