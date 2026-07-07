"""Contract: AI Observability + Feedback Learning boundary backtest wiring v0 (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    AiObservabilityBacktestStateFileBindingConfigV1,
    FeedbackLearningBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from src.meta.learning_loop.deploy_inactive_v1 import DEPLOYMENT_CANDIDATE_CONTRACT_NAME
from src.meta.learning_loop.runtime_observation_feedback_v1 import OBSERVATION_CONTRACT_NAME
from trading.master_v2.ai_observability_boundary_backtest_state_file_binding_adapter_v0 import (
    AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    apply_backtest_ai_observability_exposure_gate_v0,
    backtest_ai_observability_state_file_binding_non_authority_ok_v0,
    bind_ai_observability_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0 as ai_observability_digest,
    evaluate_backtest_ai_observability_state_file_boundary_only_v0,
    parse_ai_observability_backtest_state_file_v0,
    verify_ai_observability_backtest_state_file_digest_v0,
    ai_observability_boundary_semantics_represented_in_backtest_v0,
)
from trading.master_v2.ai_observability_boundary_offline_replay_binding_adapter_v0 import (
    AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED,
    AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import EVIDENCE_SCHEMA_VERSION
from trading.master_v2.decision_packet_v1 import MASTER_V2_DECISION_PACKET_LAYER_VERSION
from trading.master_v2.feedback_learning_boundary_backtest_state_file_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    apply_backtest_feedback_learning_exposure_gate_v0,
    backtest_feedback_learning_state_file_binding_non_authority_ok_v0,
    bind_feedback_learning_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0 as feedback_learning_digest,
    evaluate_backtest_feedback_learning_state_file_boundary_only_v0,
    parse_feedback_learning_backtest_state_file_v0,
    verify_feedback_learning_backtest_state_file_digest_v0,
    feedback_learning_boundary_semantics_represented_in_backtest_v0,
)
from trading.master_v2.feedback_learning_boundary_offline_replay_binding_adapter_v0 import (
    FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED,
    FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION,
)
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg

REPO_ROOT = Path(__file__).resolve().parents[1]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/ai_observability_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/feedback_learning_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT / "scripts/ops/run_backtest_ai_observability_feedback_boundary_wiring_v0.py",
    REPO_ROOT / "tests/test_backtest_ai_observability_feedback_boundary_wiring_v0.py",
)


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def _ai_observability_payload(**kwargs: object) -> dict[str, object]:
    base = {
        "schema_version": AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "explainability_envelope_mode": EXPLAINABILITY_MODE_READ_ONLY_EVIDENCE_ONLY,
        "ai_layer_owner_digest_ref": EVIDENCE_SCHEMA_VERSION,
        "decision_packet_owner_digest_ref": MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        **kwargs,
    }
    digest = ai_observability_digest(base)
    return {**base, "state_file_digest_ref": digest}


def _feedback_learning_payload(**kwargs: object) -> dict[str, object]:
    base = {
        "schema_version": FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "feedback_learning_mode": FEEDBACK_LEARNING_MODE_OBSERVE_ONLY_NO_MUTATION,
        "feedback_observation_contract_ref": OBSERVATION_CONTRACT_NAME,
        "learning_deploy_inactive_contract_ref": DEPLOYMENT_CANDIDATE_CONTRACT_NAME,
        **kwargs,
    }
    digest = feedback_learning_digest(base)
    return {**base, "state_file_digest_ref": digest}


def _ai_record(**kwargs: object):
    return parse_ai_observability_backtest_state_file_v0(
        payload=_ai_observability_payload(**kwargs)
    )


def _feedback_record(**kwargs: object):
    return parse_feedback_learning_backtest_state_file_v0(
        payload=_feedback_learning_payload(**kwargs)
    )


def _base_evidence():
    return build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-ai-feedback-decision",
        replay_id="backtest-ai-feedback-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
        composition_result_id="composition",
        entry_exit_policy_ref="policy",
        selected_side="long",
        decision_outcome="enter_long",
        reason_codes=("PASS",),
        decision_precedence_trace=("enter_long",),
        config_digest="config",
        implementation_digest="impl",
    )


def test_owner_constants_reuse_surface_adapters_v0() -> None:
    assert AI_OBSERVABILITY_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "ai_observability_boundary_backtest_state_file_binding_adapter_v0"
    )
    assert FEEDBACK_LEARNING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "feedback_learning_boundary_backtest_state_file_binding_adapter_v0"
    )


def test_slice_sources_exclude_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
            "risk_layer.kill_switch.core",
        }
    )
    for path in _FORBIDDEN_IMPORT_SCAN_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_ai_layer_observability_boundary_documented_v0() -> None:
    assert AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED is True
    evidence = evaluate_backtest_ai_observability_state_file_boundary_only_v0(_ai_record())
    assert evidence.ai_layer_observability_boundary_documented is True
    assert evidence.read_only_evidence_only is True
    assert ai_observability_boundary_semantics_represented_in_backtest_v0(evidence)


def test_feedback_learning_boundary_documented_v0() -> None:
    assert FEEDBACK_LEARNING_BOUNDARY_DOCUMENTED is True
    evidence = evaluate_backtest_feedback_learning_state_file_boundary_only_v0(_feedback_record())
    assert evidence.feedback_learning_boundary_documented is True
    assert evidence.observe_only_no_mutation_in_backtest is True
    assert feedback_learning_boundary_semantics_represented_in_backtest_v0(evidence)


def test_ai_observability_read_only_evidence_only_in_backtest_v0() -> None:
    evidence = evaluate_backtest_ai_observability_state_file_boundary_only_v0(_ai_record())
    assert evidence.explainability_envelope_represented_in_backtest is True
    assert evidence.no_ai_trade_authority_in_backtest is True
    assert backtest_ai_observability_state_file_binding_non_authority_ok_v0(evidence)


def test_feedback_learning_no_mutation_invariants_represented_v0() -> None:
    evidence = evaluate_backtest_feedback_learning_state_file_boundary_only_v0(_feedback_record())
    assert evidence.no_strategy_selection_mutation_represented_in_backtest is True
    assert evidence.no_promotion_mutation_represented_in_backtest is True
    assert evidence.no_runtime_eligibility_mutation_represented_in_backtest is True
    assert evidence.no_sizing_mutation_represented_in_backtest is True
    assert evidence.no_order_intent_mutation_represented_in_backtest is True
    assert evidence.no_safety_mutation_represented_in_backtest is True
    assert evidence.no_reconciliation_mutation_represented_in_backtest is True
    assert evidence.no_economic_results_mutation_represented_in_backtest is True
    assert backtest_feedback_learning_state_file_binding_non_authority_ok_v0(evidence)


def test_backtest_binding_uses_surface_adapters_not_duplicate_semantics_v0() -> None:
    ai_bound = bind_ai_observability_boundary_backtest_state_file_evidence_v0(
        _base_evidence(),
        state_file=_ai_record(),
    )
    assert (
        ai_bound.surface_n_adapter_owner_ref
        == AI_OBSERVABILITY_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )
    feedback_bound = bind_feedback_learning_boundary_backtest_state_file_evidence_v0(
        _base_evidence(),
        state_file=_feedback_record(),
    )
    assert (
        feedback_bound.surface_o_adapter_owner_ref
        == FEEDBACK_LEARNING_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )


def test_non_authority_invariants_v0() -> None:
    ai_evidence = evaluate_backtest_ai_observability_state_file_boundary_only_v0(_ai_record())
    feedback_evidence = evaluate_backtest_feedback_learning_state_file_boundary_only_v0(
        _feedback_record()
    )
    for evidence in (ai_evidence, feedback_evidence):
        assert evidence.runtime_authority is False
        assert evidence.orders_allowed is False
        assert evidence.credentials_used is False
        assert evidence.economic_evaluation is False


def test_exposure_gate_pass_through_no_runtime_authority_v0() -> None:
    ai_evidence = evaluate_backtest_ai_observability_state_file_boundary_only_v0(_ai_record())
    feedback_evidence = evaluate_backtest_feedback_learning_state_file_boundary_only_v0(
        _feedback_record()
    )
    assert apply_backtest_ai_observability_exposure_gate_v0(1, evidence=ai_evidence) == 1
    assert apply_backtest_feedback_learning_exposure_gate_v0(1, evidence=feedback_evidence) == 1


def test_parity_gap_assessment_surfaces_n_o_backtest_wiring_pass_v0() -> None:
    ai_surface = next(item for item in parity_surface_assessments_v0() if item.surface_id == "N")
    feedback_surface = next(
        item for item in parity_surface_assessments_v0() if item.surface_id == "O"
    )
    assert ai_surface.parity_status == "PASS"
    assert feedback_surface.parity_status == "PASS"
    assert ai_surface.missing_binding_if_any == ""
    assert feedback_surface.missing_binding_if_any == ""
    assert "bind_ai_observability_boundary_backtest_state_file_evidence_v0" in (
        ai_surface.current_backtest_binding
    )
    assert "bind_feedback_learning_boundary_backtest_state_file_evidence_v0" in (
        feedback_surface.current_backtest_binding
    )
    assert (
        NEXT_RECOMMENDED_SLICE == "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
    )


def test_mv2_research_wiring_binds_state_files_and_represents_boundaries_v0(
    tmp_path: Path,
) -> None:
    ai_payload = _ai_observability_payload()
    feedback_payload = _feedback_learning_payload()
    ai_path = tmp_path / "ai_observability_backtest_state.json"
    feedback_path = tmp_path / "feedback_learning_backtest_state.json"
    ai_path.write_text(json.dumps(ai_payload, indent=2), encoding="utf-8")
    feedback_path.write_text(json.dumps(feedback_payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        ai_observability_state_file_binding=AiObservabilityBacktestStateFileBindingConfigV1(
            state_file_path=ai_path,
            expected_state_file_digest_ref=str(ai_payload["state_file_digest_ref"]),
        ),
        feedback_learning_state_file_binding=FeedbackLearningBacktestStateFileBindingConfigV1(
            state_file_path=feedback_path,
            expected_state_file_digest_ref=str(feedback_payload["state_file_digest_ref"]),
        ),
    )
    assert result.bar_outcomes
    sample = result.bar_outcomes[0]
    assert sample.ai_observability_backtest_state_file_evidence is not None
    assert sample.feedback_learning_backtest_state_file_evidence is not None
    assert (
        sample.ai_observability_backtest_state_file_evidence.explainability_envelope_represented_in_backtest
        is True
    )
    assert (
        sample.feedback_learning_backtest_state_file_evidence.observe_only_no_mutation_in_backtest
        is True
    )


def test_mv2_research_wiring_legacy_without_state_files_unchanged_v0() -> None:
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
    )
    assert all(o.ai_observability_backtest_state_file_evidence is None for o in result.bar_outcomes)
    assert all(
        o.feedback_learning_backtest_state_file_evidence is None for o in result.bar_outcomes
    )


def test_required_ai_observability_state_file_missing_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="ai_observability_backtest_state_file_missing"):
        run_mv2_research_backtest_wiring_v1(
            _bars(n=4),
            strategy_id="ma_crossover",
            cfg=_cfg(),
            explicit_zero_cost_non_economic=True,
            ai_observability_state_file_binding=AiObservabilityBacktestStateFileBindingConfigV1(
                require_state_file=True,
            ),
        )


def test_required_feedback_learning_state_file_missing_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="feedback_learning_backtest_state_file_missing"):
        run_mv2_research_backtest_wiring_v1(
            _bars(n=4),
            strategy_id="ma_crossover",
            cfg=_cfg(),
            explicit_zero_cost_non_economic=True,
            feedback_learning_state_file_binding=FeedbackLearningBacktestStateFileBindingConfigV1(
                require_state_file=True,
            ),
        )


def test_verify_state_file_digest_refs_v0() -> None:
    ai_record = _ai_record()
    verify_ai_observability_backtest_state_file_digest_v0(
        ai_record,
        expected_digest_ref=ai_record.state_file_digest_ref,
    )
    with pytest.raises(ValueError, match="ai_observability_backtest_state_file_digest_mismatch"):
        verify_ai_observability_backtest_state_file_digest_v0(
            ai_record, expected_digest_ref="0" * 64
        )

    feedback_record = _feedback_record()
    verify_feedback_learning_backtest_state_file_digest_v0(
        feedback_record,
        expected_digest_ref=feedback_record.state_file_digest_ref,
    )
    with pytest.raises(ValueError, match="feedback_learning_backtest_state_file_digest_mismatch"):
        verify_feedback_learning_backtest_state_file_digest_v0(
            feedback_record,
            expected_digest_ref="0" * 64,
        )
