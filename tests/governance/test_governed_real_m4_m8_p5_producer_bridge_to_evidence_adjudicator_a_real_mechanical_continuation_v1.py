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
from src.governance.governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1 import (
    G2RuntimeM4M8ContinuationRequestV1,
    run_g2_runtime_to_m4_m8_evidence_return_continuation_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
    RUNTIME_APPLY_STARTED,
    RuntimePrimarySourceModeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)

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
def test_real_runtime_through_p5_to_adjudicator_a(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    req = projection_request(source_mode=mode, primary_root=root)
    result = run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1(
        RealP5AdjudicatorAContinuationRequestV1(
            projection_request=req,
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "CONTINUATION_COMPLETE", result.blocking_reasons
    assert result.real_upstream_source_used is True
    assert result.ddo_fixture_state_used is False
    assert result.p5_producer_bridge_reached is True
    assert result.evidence_adjudicator_a_reached is True
    assert result.lineage_join_valid is True
    assert result.optimization_adjudication_disposition == ADMIT_DISPOSITION
    assert result.meta_adjudication_disposition == ADMIT_DISPOSITION
    opt = result.optimization_envelope_evidence or {}
    meta = result.meta_learning_routed_evidence or {}
    assert opt.get("optimization_productive_authority") == "NONE"
    assert meta.get("meta_evidence_authority") == "NONE"
    assert prove_real_p5_adjudicator_a_continuation_v1(
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
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    g2 = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(projection_request=req)
    )
    assert g2.status == "CONTINUATION_COMPLETE"
    ok = run_real_runtime_to_p5_evidence_adjudicator_a_continuation_v1(
        RealP5AdjudicatorAContinuationRequestV1(projection_request=req, repo_root=REPO_ROOT)
    )
    cycle = (g2.m4_m8_loop or {}).get("cycle") or {}
    m5 = cycle.get("optimization_experiment_evidence") or {}
    m6 = cycle.get("meta_learning_evidence") or {}
    opt = dict(ok.optimization_envelope_evidence or {})
    opt["source_optimization_experiment_evidence_digest"] = "f" * 64
    reasons = validate_p5_bridge_lineage_join_v1(
        optimization_experiment_evidence=m5,
        meta_learning_evidence=m6,
        optimization_envelope=opt,
        meta_routed=dict(ok.meta_learning_routed_evidence or {}),
    )
    assert "OPT_ENVELOPE_M5_DIGEST_MISMATCH" in reasons
    assert ok.status == "CONTINUATION_COMPLETE"


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
