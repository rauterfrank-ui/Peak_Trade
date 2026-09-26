"""Real Component A ADMIT → P3 binder → P4 L6 productive seam tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.governance.governed_real_component_a_admit_to_p3_p4_l6_productive_seam_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    EVIDENCE_ADMIT_IMPLIES_PRODUCTIVE_ACTIVATION,
    P3_INPUT_CREATOR_BINDER_REAL_BIND_STATUS,
    P4_L6_PRODUCTIVE_SEAM_REAL_BIND_STATUS,
    RealP3P4ProductiveSeamContinuationRequestV1,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
    prove_real_p3_p4_l6_productive_seam_continuation_v1,
    run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1,
    validate_real_component_a_to_p3_p4_lineage_join_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
    RUNTIME_APPLY_STARTED,
    RuntimePrimarySourceModeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
    A_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    REJECT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.models_v1 import (
    LayerInputBindingContextV1,
    LayerInputBindingRequestV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.binder_v1 import (
    bind_layer_input_from_adjudication_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.constants_v1 import (
    L6_TYPED_INPUT_SCHEMA_VERSION,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1

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
def test_real_runtime_through_p3_p4_l6_seam(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    req = projection_request(source_mode=mode, primary_root=root)
    result = run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1(
        RealP3P4ProductiveSeamContinuationRequestV1(
            projection_request=req,
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "CONTINUATION_COMPLETE", result.blocking_reasons
    assert result.real_upstream_source_used is True
    assert result.ddo_fixture_state_used is False
    assert result.component_a_real_admit_used is True
    assert result.p3_input_creator_binder_reached is True
    assert result.p4_l6_seam_reached is True
    assert result.lineage_join_valid is True
    assert result.component_a_adjudication_disposition == ADMIT_DISPOSITION
    assert prove_real_p3_p4_l6_productive_seam_continuation_v1(
        projection_request=req,
        repo_root=REPO_ROOT,
    )


def test_ddo_fixture_forbidden_on_real_p3_p4_path(tmp_path: Path) -> None:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    result = run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1(
        RealP3P4ProductiveSeamContinuationRequestV1(
            projection_request=req,
            ddo_fixture_learning_state=_learning_state(tmp_path / "ddo"),
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "DDO_FIXTURE_LEARNING_STATE_FORBIDDEN_ON_REAL_PATH"
    assert result.ddo_fixture_state_used is False


def test_lineage_join_rejects_missing_adjudication_ref() -> None:
    reasons = validate_real_component_a_to_p3_p4_lineage_join_v1(
        lineage_chain=("optimization_envelope://" + "a" * 64,),
        optimization_adjudication_digest="b" * 64,
        optimization_envelope_content_hash="a" * 64,
        expected_envelope_in_lineage="a" * 64,
    )
    assert "COMPONENT_A_ADJUDICATION_LINEAGE_MISSING" in reasons


def test_non_admit_component_a_rejects_p3_bind(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    ok = run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1(
        RealP3P4ProductiveSeamContinuationRequestV1(
            projection_request=req,
            repo_root=REPO_ROOT,
        )
    )
    assert ok.status == "CONTINUATION_COMPLETE"
    from src.governance.governed_real_m4_m8_p5_producer_bridge_to_evidence_adjudicator_a_real_mechanical_continuation_v1 import (
        build_market_context_v1_from_runtime_primary_provenance_v1,
    )
    from src.governance.governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1 import (
        G2RuntimeM4M8ContinuationRequestV1,
        run_g2_runtime_to_m4_m8_evidence_return_continuation_v1,
    )
    from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.adapters_v1 import (
        adapt_optimization_envelope_evidence_v1,
        default_termination_context_from_market_context_v1,
    )
    from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.ingress_v1 import (
        terminate_optimization_envelope_at_a_v1,
    )
    from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.optimization_envelope_evidence_v1 import (
        SCHEMA_VERSION,
    )

    g2 = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(projection_request=req)
    )
    prov = g2.projection.provenance
    mc = build_market_context_v1_from_runtime_primary_provenance_v1(prov)
    epoch = int(prov.trading_epoch)
    term = default_termination_context_from_market_context_v1(mc, market_observation_epoch=epoch)
    opt = dict(ok.optimization_envelope_evidence or {})
    term_res = terminate_optimization_envelope_at_a_v1(
        opt,
        source_artifact_schema=SCHEMA_VERSION,
        source_content_digest=str(opt["content_hash"]),
        termination=term,
        repo_root=REPO_ROOT,
    )
    reject_adj = replace(term_res.adjudication, disposition=REJECT_DISPOSITION)
    intake = adapt_optimization_envelope_evidence_v1(opt, termination=term)
    binding = bind_layer_input_from_adjudication_v1(
        LayerInputBindingRequestV1(
            binding_id="neg-bind",
            target_layer=LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
            target_contract_version=L6_TYPED_INPUT_SCHEMA_VERSION,
            nullline_provenance_epoch=epoch,
            adjudication=reject_adj,
        ),
        context=LayerInputBindingContextV1(
            evaluated_at_unix=float(intake.observed_at_unix) + 1.0,
            expected_instrument=term.instrument,
            expected_market_observation_epoch=epoch,
        ),
    )
    assert binding.disposition == "NO_BIND"


def test_authority_gates_unchanged_and_invariants() -> None:
    assert A_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert B_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert RUNTIME_APPLY_STARTED is False
    assert EXTERNAL_EFFECT is False
    assert EVIDENCE_ADMIT_IMPLIES_PRODUCTIVE_ACTIVATION is False
    assert prove_continuation_authority_invariants_v1()


def test_decision_config_and_files() -> None:
    assert prove_continuation_decision_files_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert (
        decision["p3_input_creator_binder_real_bind_status"]
        == P3_INPUT_CREATOR_BINDER_REAL_BIND_STATUS
    )
    assert (
        decision["p4_l6_productive_seam_real_bind_status"] == P4_L6_PRODUCTIVE_SEAM_REAL_BIND_STATUS
    )
    assert decision["runtime_apply_started"] is False
    assert decision["component_b_activated"] is False
