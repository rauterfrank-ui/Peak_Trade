"""Real M4–M8 → P5 producer bridges → Evidence Adjudicator A tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.governed_real_m4_m8_p5_producer_bridge_to_evidence_adjudicator_a_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    EVIDENCE_ACCEPTANCE_IMPLIES_PRODUCTIVE_AUTHORIZATION,
    EVIDENCE_ADJUDICATOR_A_REAL_INGRESS_STATUS,
    P5_META_LEARNING_ROUTED_BRIDGE_STATUS,
    P5_OPTIMIZATION_ENVELOPE_BRIDGE_STATUS,
    RealP5AdjudicatorAContinuationRequestV1,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
    prove_real_p5_adjudicator_a_continuation_v1,
    run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1,
    validate_p5_bridge_lineage_join_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
    RUNTIME_APPLY_STARTED,
    RuntimePrimarySourceModeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.p5_m4_m8_producer_bridge_v1 import (
    bridge_m5_to_optimization_envelope_evidence_v1,
    bridge_m6_to_meta_learning_routed_evidence_v1,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)
from tests.governance.test_p5_m4_m8_optimization_meta_producer_final_closure_v1 import _m4_m8_cycle
from tests.learning.test_loop_a_conditioned_learning_evidence_v1 import _observation_for_n
from tests.learning.test_market_context_realized_behavior_join_v1 import _context_for_observation

pytest_plugins = [
    "tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures"
]

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _cleanup_archives():
    yield
    cleanup_durable_archive_roots()


@pytest.mark.parametrize(
    "mode",
    [
        RuntimePrimarySourceModeV1.PAPER,
        RuntimePrimarySourceModeV1.SHADOW,
        RuntimePrimarySourceModeV1.TESTNET,
    ],
)
def test_observation_archive_cannot_reach_p5_or_component_a(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    req = projection_request(source_mode=mode, primary_root=root)
    result = run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1(
        RealP5AdjudicatorAContinuationRequestV1(
            projection_request=req,
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "G2_ORIGINAL_OUTCOME_EVIDENCE_REQUIRED"
    assert result.ddo_fixture_state_used is False
    assert result.p5_producer_bridge_reached is False
    assert result.evidence_adjudicator_a_reached is False
    assert result.optimization_envelope_evidence is None
    assert result.meta_learning_routed_evidence is None
    assert result.optimization_adjudication_disposition is None
    assert result.meta_adjudication_disposition is None
    assert not prove_real_p5_adjudicator_a_continuation_v1(
        projection_request=req,
        repo_root=REPO_ROOT,
    )


def test_ddo_fixture_forbidden_on_real_p5_path(tmp_path: Path) -> None:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    result = run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1(
        RealP5AdjudicatorAContinuationRequestV1(
            projection_request=req,
            ddo_fixture_learning_state=_learning_state(tmp_path / "ddo"),
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "DDO_FIXTURE_LEARNING_STATE_FORBIDDEN_ON_REAL_PATH"
    assert result.ddo_fixture_state_used is False


def test_p5_lineage_join_rejects_tampered_envelope_digest(tmp_path: Path) -> None:
    cycle = _m4_m8_cycle(tmp_path)["cycle"]
    m5 = cycle["optimization_experiment_evidence"]
    m6 = cycle["meta_learning_evidence"]
    context = _context_for_observation(_observation_for_n(n_bars=2))
    opt = dict(
        bridge_m5_to_optimization_envelope_evidence_v1(
            optimization_experiment_evidence=m5, market_context=context
        )
    )
    meta = bridge_m6_to_meta_learning_routed_evidence_v1(
        meta_learning_evidence=m6, market_context=context
    )
    assert not validate_p5_bridge_lineage_join_v1(
        optimization_experiment_evidence=m5,
        meta_learning_evidence=m6,
        optimization_envelope=opt,
        meta_routed=meta,
    )
    opt["source_optimization_experiment_evidence_digest"] = "f" * 64
    reasons = validate_p5_bridge_lineage_join_v1(
        optimization_experiment_evidence=m5,
        meta_learning_evidence=m6,
        optimization_envelope=opt,
        meta_routed=meta,
    )
    assert "OPT_ENVELOPE_M5_DIGEST_MISMATCH" in reasons


def test_authority_invariants_and_decision_config() -> None:
    assert prove_continuation_authority_invariants_v1() is True
    assert prove_continuation_decision_files_v1(repo_root=REPO_ROOT) is True
    assert EVIDENCE_ACCEPTANCE_IMPLIES_PRODUCTIVE_AUTHORIZATION is False
    assert RUNTIME_APPLY_STARTED is False
    assert EXTERNAL_EFFECT is False
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert (
        decision["p5_optimization_envelope_bridge_status"] == P5_OPTIMIZATION_ENVELOPE_BRIDGE_STATUS
    )
    assert (
        decision["p5_meta_learning_routed_bridge_status"] == P5_META_LEARNING_ROUTED_BRIDGE_STATUS
    )
    assert (
        decision["evidence_adjudicator_a_real_ingress_status"]
        == EVIDENCE_ADJUDICATOR_A_REAL_INGRESS_STATUS
    )
