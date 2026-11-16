"""Tests for runtime learning input → canonical optimization universe binding v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance import (
    governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1 as g2_binding,
)
from src.governance.governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1 import (
    DECISION_CONFIG,
    FIELD_MAPPING_LEDGER,
    RuntimeLearningInputOptimizationBindingRequestV1,
    bind_from_g2_projection_result_v1,
    bind_runtime_to_learning_input_to_canonical_optimization_universe_learning_input_v1,
    load_field_mapping_ledger_v1,
    prove_binding_authority_invariants_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_closure_v1 import (
    G2_RUNTIME_TO_CANONICAL_OPTIMIZATION_INPUT_STATUS,
    prove_g2_runtime_to_canonical_optimization_learning_input_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
    RUNTIME_APPLY_STARTED,
    RuntimePrimarySourceModeV1,
    run_governed_runtime_primary_to_offline_observation_projection_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
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
def test_observation_archive_does_not_reach_optimization_without_an_outcome(
    tmp_path: Path, mode, monkeypatch
) -> None:
    root = build_mode_bundle(tmp_path, mode)
    projection = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request(source_mode=mode, primary_root=root)
    )
    assert projection.status == "PROJECTED"

    def unexpected_optimization_input(_request):
        pytest.fail("Observation-only archive reached canonical optimization")

    monkeypatch.setattr(
        g2_binding,
        "validate_canonical_optimization_universe_learning_input_v1",
        unexpected_optimization_input,
    )
    binding = bind_from_g2_projection_result_v1(projection)
    assert binding.status == "REJECTED"
    assert binding.decision_code == "G2_ORIGINAL_OUTCOME_EVIDENCE_REQUIRED"
    assert binding.learning_evidence is None
    assert binding.canonical_optimization_ack is None
    assert binding.binding_record_digest is None


@pytest.mark.parametrize(
    "mode",
    [
        RuntimePrimarySourceModeV1.PAPER,
        RuntimePrimarySourceModeV1.SHADOW,
        RuntimePrimarySourceModeV1.TESTNET,
    ],
)
def test_closure_does_not_prove_an_outcome_from_an_observation_archive(
    tmp_path: Path, mode
) -> None:
    root = build_mode_bundle(tmp_path, mode)
    assert not prove_g2_runtime_to_canonical_optimization_learning_input_v1(
        projection_request=projection_request(source_mode=mode, primary_root=root)
    )


def test_observation_keeps_its_archive_lineage(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    projection = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    )
    assert projection.status == "PROJECTED"
    assert projection.provenance is not None
    body = projection.runtime_learning_input
    assert body is not None
    assert body["source_session_identity"] == projection.provenance.source_run_session_identity
    primary_ref = f"primary_manifest://{projection.provenance.primary_evidence_manifest_digest}"
    assert primary_ref in body["parent_refs"]
    assert body["source_observation_ref"]


def test_malformed_runtime_input_rejects() -> None:
    result = bind_runtime_to_learning_input_to_canonical_optimization_universe_learning_input_v1(
        RuntimeLearningInputOptimizationBindingRequestV1(
            runtime_learning_input={"decision_code": "INVALID"},
            provenance=_minimal_provenance(),
            projection_record_digest="0" * 64,
        )
    )
    assert result.status == "REJECTED"


def test_missing_provenance_alignment_rejects(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.SHADOW)
    projection = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request(source_mode=RuntimePrimarySourceModeV1.SHADOW, primary_root=root)
    )
    assert projection.runtime_learning_input is not None
    assert projection.provenance is not None
    tampered = dict(projection.runtime_learning_input)
    tampered["source_session_identity"] = "tampered-session"
    result = bind_runtime_to_learning_input_to_canonical_optimization_universe_learning_input_v1(
        RuntimeLearningInputOptimizationBindingRequestV1(
            runtime_learning_input=tampered,
            provenance=projection.provenance,
            projection_record_digest=str(projection.projection_record_digest),
        )
    )
    assert result.status == "REJECTED"
    assert "SOURCE_SESSION_IDENTITY_MISMATCH" in result.blocking_reasons


def test_ddo_fixture_cannot_rescue_binding_request(tmp_path: Path) -> None:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    projection = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    )
    assert projection.provenance is not None
    fixture_state = _learning_state(tmp_path / "ddo")
    result = bind_runtime_to_learning_input_to_canonical_optimization_universe_learning_input_v1(
        RuntimeLearningInputOptimizationBindingRequestV1(
            runtime_learning_input={"decision_code": "INVALID"},
            provenance=projection.provenance,
            projection_record_digest=str(projection.projection_record_digest or ("f" * 64)),
            ddo_fixture_learning_state=fixture_state,
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "DDO_FIXTURE_STATE_IN_BINDING_REQUEST_FORBIDDEN"


def test_observation_input_cannot_supply_its_own_outcome_class_or_fixture(tmp_path: Path) -> None:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    state = _learning_state(tmp_path)
    fixture_evidence = export_learning_evidence_from_state_v1(state)
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.TESTNET)
    projection = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request(source_mode=RuntimePrimarySourceModeV1.TESTNET, primary_root=root)
    )
    assert projection.runtime_learning_input is not None
    assert projection.provenance is not None
    assert projection.projection_record_digest is not None
    binding = bind_runtime_to_learning_input_to_canonical_optimization_universe_learning_input_v1(
        RuntimeLearningInputOptimizationBindingRequestV1(
            runtime_learning_input={
                **projection.runtime_learning_input,
                "outcome_semantic_class": "SHADOW_COUNTERFACTUAL",
                "learning_evidence": fixture_evidence,
            },
            provenance=projection.provenance,
            projection_record_digest=projection.projection_record_digest,
        )
    )
    assert binding.decision_code == "G2_ORIGINAL_OUTCOME_EVIDENCE_REQUIRED"
    assert binding.learning_evidence is None
    assert binding.canonical_optimization_ack is None


def test_authority_non_escalation_constants() -> None:
    assert prove_binding_authority_invariants_v1() is True
    assert RUNTIME_APPLY_STARTED is False
    assert EXTERNAL_EFFECT is False


def test_decision_config_and_field_mapping_ledger() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert (
        decision["workpackage_id"]
        == "GOVERNED_RUNTIME_LEARNING_INPUT_TO_OPTIMIZATION_UNIVERSE_LEARNING_INPUT_BINDING_V1"
    )
    assert decision["ddo_fixture_required_for_real_path"] is False
    assert (
        decision["real_runtime_g2_to_canonical_optimization_input_status"]
        == G2_RUNTIME_TO_CANONICAL_OPTIMIZATION_INPUT_STATUS
    )
    ledger = load_field_mapping_ledger_v1(repo_root=REPO_ROOT)
    assert ledger["workpackage_id"].endswith("LEARNING_INPUT_BINDING_V1")
    assert ledger["destination_contract"] == "learning_evidence_record_v1"
    assert ledger["admission_predicates"]["observation_only_binding"] == (
        "G2_ORIGINAL_OUTCOME_EVIDENCE_REQUIRED"
    )
    assert ledger["mappings"]["archive_review_verdict"]["adjudication"] == "ARCHIVE_INTEGRITY_ONLY"
    assert ledger["mappings"]["learning_evidence"]["adjudication"] == "ORIGINAL_VERIFIED_RECORD"


def _minimal_provenance():
    from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
        RuntimePrimaryProvenanceBindingV1,
    )

    return RuntimePrimaryProvenanceBindingV1(
        source_execution_mode="PAPER",
        source_run_session_identity="run.minimal",
        source_archive_root_ref="tests/fixture",
        primary_evidence_manifest_digest="a" * 64,
        runtime_out_evidence_manifest_digest="b" * 64,
        wrapper_evidence_manifest_digest=None,
        observation_time_utc="2026-01-01T00:00:00Z",
        instrument_identity="ETH-USDT-SWAP",
        venue_identity="SIM",
        trading_epoch=1,
        strategy_config_identity="strat.v1",
        repository_code_provenance="01234567",
        review_verdict="PASS",
    )
