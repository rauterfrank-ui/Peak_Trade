"""Tests for productive learning → G2 primary-evidence Case B causal closure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import LOOP_STATUS_COMPLETE
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
)
from src.governance.governed_productive_learning_to_g2_primary_evidence_causal_closure_v1 import (
    DECISION_CONFIG,
    PRODUCTIVE_DDO_OFFLINE_EXPORT_JOIN_SEAM_ID,
    SEMANTIC_ADJUDICATION_CASE_B,
    evaluate_handoff_artifact_path_as_primary_evidence_root_v1,
    evaluate_productive_ddo_export_for_g2_primary_evidence_ingress_v1,
    prove_semantic_adjudication_case_b_invariants_v1,
    run_legitimate_g2_primary_to_m4_m8_reference_continuation_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    RuntimePrimarySourceModeV1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    EXPORT_ID,
    PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
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


def _sample_handoff() -> dict[str, str | int | bool | list[str]]:
    return {
        "join_seam_id": PRODUCTIVE_DDO_OFFLINE_EXPORT_JOIN_SEAM_ID,
        "session_id": "wsccstz:LANE_1:LANE_1",
        "cycle_id": "wsccstz:LANE_1:LANE_1:cycle:2",
        "correlation_id": "ddo.corr.wsccstz:LANE_1:LANE_1",
        "learning_evidence_record_id": "ddo.lev.test0123456789abcdef0123456789abcdef01234567",
        "learning_state_record_ref": "ls.test0123456789abcdef0123456789abcdef0123456789ab",
        "optimization_ack_status": STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
        "optimization_ack_reason": "OFFLINE_RESEARCH_INPUT_ONLY",
        "export_id": EXPORT_ID,
        "productive_optimization_join_authorized": PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
        "external_effect_authorized": False,
        "post_count": 0,
        "capture_record_ids": ["ddo.dec:abc"],
    }


def test_case_b_rejects_productive_handoff_for_g2_ingress() -> None:
    ev = evaluate_productive_ddo_export_for_g2_primary_evidence_ingress_v1(_sample_handoff())
    assert ev.semantic_adjudication == SEMANTIC_ADJUDICATION_CASE_B
    assert ev.g2_ingress_admitted is False
    assert ev.bridge_implemented is False
    assert ev.fail_closed is True
    assert ev.productive_optimization_join_authorized is False
    assert "G2_INGRESS_REQUIRES_PAPER_SHADOW_TESTNET_DURABLE_ARCHIVE" in ev.reason_codes


def test_handoff_json_path_fails_primary_evidence_validation(tmp_path: Path) -> None:
    handoff_path = tmp_path / "ddo_offline_export_handoff_v1.json"
    handoff_path.write_text(json.dumps(_sample_handoff(), indent=2) + "\n", encoding="utf-8")
    ev = evaluate_handoff_artifact_path_as_primary_evidence_root_v1(handoff_path)
    assert ev.g2_ingress_admitted is False
    assert any("PRIMARY_VALIDATION_PAPER:" in code for code in ev.reason_codes)


def test_decision_config_and_static_invariants() -> None:
    cfg = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert cfg["semantic_adjudication"] == SEMANTIC_ADJUDICATION_CASE_B
    assert cfg["bridge_implementation_authorized"] is False
    assert prove_semantic_adjudication_case_b_invariants_v1()


def test_legitimate_paper_primary_g2_to_m4_m8_reference(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    ref = run_legitimate_g2_primary_to_m4_m8_reference_continuation_v1(
        projection_request=req,
        classification="FIXTURE_CLASSIFIED_PAPER_PRIMARY_EVIDENCE",
    )
    assert ref.g2_result.status == "CONTINUATION_COMPLETE", ref.g2_result.blocking_reasons
    assert ref.m8_reached is True
    assert ref.productive_apply_reached is False
    loop = ref.g2_result.m4_m8_loop or {}
    assert loop.get("status") == LOOP_STATUS_COMPLETE
