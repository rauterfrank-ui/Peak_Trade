"""P5 final closure: M4–M8 Optimization + Meta-Learning producers terminate at Component A."""

from __future__ import annotations

from pathlib import Path

from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
    M4M8EvidenceReturnLoopRequestV1,
    run_m4_m8_evidence_return_loop_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
    REJECT_DISPOSITION,
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
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.reason_codes_v1 import (
    ProducerIngressFailureCodeV1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state
from tests.learning.test_loop_a_conditioned_learning_evidence_v1 import _observation_for_n
from tests.learning.test_market_context_realized_behavior_join_v1 import _context_for_observation

REPO_ROOT = Path(__file__).resolve().parents[2]


def _m4_m8_cycle(tmp_path: Path) -> dict:
    state = _learning_state(tmp_path)
    from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
        export_learning_evidence_from_state_v1,
    )

    learning_evidence = export_learning_evidence_from_state_v1(state)
    return dict(
        run_m4_m8_evidence_return_loop_v1(
            M4M8EvidenceReturnLoopRequestV1(
                learning_evidence=learning_evidence,
                plane_request=_plane_request(learning_evidence),
                replay_seed=42,
            )
        )
    )


def test_m4_m8_to_p5_optimization_and_meta_admit_at_a(tmp_path: Path) -> None:
    loop = _m4_m8_cycle(tmp_path)
    cycle = loop["cycle"]
    m5 = cycle["optimization_experiment_evidence"]
    m6 = cycle["meta_learning_evidence"]
    ctx = _context_for_observation(_observation_for_n(n_bars=2))
    termination = default_termination_context_from_market_context_v1(
        ctx, market_observation_epoch=0
    )

    opt_envelope = bridge_m5_to_optimization_envelope_evidence_v1(
        optimization_experiment_evidence=m5,
        market_context=ctx,
    )
    meta_routed = bridge_m6_to_meta_learning_routed_evidence_v1(
        meta_learning_evidence=m6,
        market_context=ctx,
    )

    opt = terminate_optimization_envelope_at_a_v1(
        opt_envelope,
        source_artifact_schema=OPT_ENVELOPE_SCHEMA,
        source_content_digest=str(opt_envelope["content_hash"]),
        termination=termination,
        repo_root=REPO_ROOT,
    )
    meta = terminate_meta_learning_routed_at_a_v1(
        meta_routed,
        source_artifact_schema=META_ROUTED_SCHEMA,
        source_content_digest=str(meta_routed["content_hash"]),
        termination=termination,
        repo_root=REPO_ROOT,
    )

    assert opt.adjudication.disposition == ADMIT_DISPOSITION
    assert meta.adjudication.disposition == ADMIT_DISPOSITION
    assert opt.adjudication.envelope is not None
    assert meta.adjudication.envelope is not None
    assert opt.adjudication.envelope.trading_authority == "NONE"
    assert meta.adjudication.envelope.trading_authority == "NONE"
    assert opt.ingress_provenance.source_content_digest == str(opt_envelope["content_hash"])


def test_p5_bridge_fail_closed_on_binding_mismatch(tmp_path: Path) -> None:
    loop = _m4_m8_cycle(tmp_path)
    cycle = loop["cycle"]
    m5 = cycle["optimization_experiment_evidence"]
    m6 = cycle["meta_learning_evidence"]
    ctx = _context_for_observation(_observation_for_n(n_bars=2))
    termination = default_termination_context_from_market_context_v1(
        ctx, market_observation_epoch=0
    )
    opt_envelope = bridge_m5_to_optimization_envelope_evidence_v1(
        optimization_experiment_evidence=m5,
        market_context=ctx,
    )
    tampered_opt = dict(opt_envelope)
    tampered_opt["instrument_ref"] = "TAMPERED_INSTRUMENT"
    rejected = terminate_optimization_envelope_at_a_v1(
        tampered_opt,
        source_artifact_schema=OPT_ENVELOPE_SCHEMA,
        source_content_digest=str(opt_envelope["content_hash"]),
        termination=termination,
        repo_root=REPO_ROOT,
    )
    assert rejected.adjudication.disposition == REJECT_DISPOSITION

    meta_routed = bridge_m6_to_meta_learning_routed_evidence_v1(
        meta_learning_evidence=m6,
        market_context=ctx,
    )
    tampered = dict(meta_routed)
    tampered["instrument_ref"] = "TAMPERED"
    bad_meta = terminate_meta_learning_routed_at_a_v1(
        tampered,
        source_artifact_schema=META_ROUTED_SCHEMA,
        source_content_digest=str(meta_routed["content_hash"]),
        termination=termination,
        repo_root=REPO_ROOT,
    )
    assert bad_meta.adjudication.disposition == REJECT_DISPOSITION


def test_wrong_schema_still_blocked_at_promotion() -> None:
    ctx = _context_for_observation(_observation_for_n(n_bars=2))
    termination = default_termination_context_from_market_context_v1(
        ctx, market_observation_epoch=0
    )
    opt = terminate_optimization_envelope_at_a_v1(
        {"schema_version": "canonical_optimization_experiment_evidence_v1"},
        source_artifact_schema="canonical_optimization_experiment_evidence_v1",
        source_content_digest="a" * 64,
        termination=termination,
        repo_root=REPO_ROOT,
    )
    assert opt.blocked_at_promotion is True
    assert (
        ProducerIngressFailureCodeV1.PROMOTION_ADMISSION_ABSENT.value
        in opt.adjudication.reason_codes
    )
