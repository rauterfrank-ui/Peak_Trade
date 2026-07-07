"""Contract: Promotion Gate boundary backtest state-file binding v0 (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
from src.backtest.mv2_research_wiring_v1 import (
    PromotionGateBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from src.governance.promotion_loop import promotion_economic_gate_v1 as gate
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
)
from trading.master_v2.promotion_gate_boundary_backtest_state_file_binding_adapter_v0 import (
    PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    backtest_promotion_gate_state_file_binding_non_authority_ok_v0,
    bind_promotion_gate_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_promotion_gate_state_file_boundary_only_v0,
    parse_promotion_gate_backtest_state_file_v0,
    verify_promotion_gate_backtest_state_file_digest_v0,
)
from src.governance.promotion_loop.promotion_economic_gate_v1 import (
    PROMOTION_ECONOMIC_GATE_POLICY_VERSION,
)
from trading.master_v2.promotion_gate_boundary_offline_replay_binding_adapter_v0 import (
    PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg

REPO_ROOT = Path(__file__).resolve().parents[3]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/promotion_gate_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT / "scripts/ops/run_backtest_promotion_gate_boundary_wiring_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_promotion_gate_boundary_backtest_state_file_binding_contract_v0.py",
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


def _state_file_payload(**kwargs: object) -> dict[str, object]:
    economic_policy_digest = canonical_economic_validity_policy_v1().policy_digest()
    base = {
        "schema_version": PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "promotion_gate_owner_digest_ref": PROMOTION_ECONOMIC_GATE_POLICY_VERSION,
        "strategy_id": "mv2_offline_research",
        "strategy_version": "v1",
        "candidate_id": "candidate-001",
        "economic_viability_evidence_ref": "evidence://admissible/futures/v1/bundle-001",
        "economic_validity_status": gate.PASS_STATUS,
        "robustness_status": gate.PASS_STATUS,
        "data_admissibility_status": gate.PASS_STATUS,
        "evidence_admissibility_status": gate.PASS_STATUS,
        "policy_threshold_status": gate.PASS_STATUS,
        "walk_forward_status": gate.PASS_STATUS,
        "out_of_sample_status": gate.PASS_STATUS,
        "monte_carlo_status": gate.PASS_STATUS,
        "stress_status": gate.PASS_STATUS,
        "parameter_sensitivity_status": gate.PASS_STATUS,
        "reproducibility_status": gate.PASS_STATUS,
        "digest_binding_status": gate.PASS_STATUS,
        "manifest_binding_status": gate.PASS_STATUS,
        "safety_policy_status": gate.PASS_STATUS,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "config_digest": "a" * 64,
        "implementation_digest": "b" * 64,
        "policy_digest": economic_policy_digest,
        "evidence_manifest_digest": "c" * 64,
        "economic_validity_proven": True,
        "profitability_claim_allowed": True,
        **kwargs,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def _base_evidence():
    return build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-promotion-gate-state-file-decision",
        replay_id="backtest-promotion-gate-state-file-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
        composition_result_id="composition",
        entry_exit_policy_ref="policy",
        selected_side="long",
        decision_outcome="observe",
        reason_codes=("PASS",),
        decision_precedence_trace=("observe",),
        config_digest="config",
        implementation_digest="impl",
    )


def _record(**kwargs: object):
    return parse_promotion_gate_backtest_state_file_v0(payload=_state_file_payload(**kwargs))


def test_owner_constants_reuse_surface_m_adapter_v0() -> None:
    assert PROMOTION_GATE_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "promotion_gate_boundary_backtest_state_file_binding_adapter_v0"
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


def test_eligible_candidate_represents_promotion_gate_boundary_v0() -> None:
    evidence = evaluate_backtest_promotion_gate_state_file_boundary_only_v0(_record())
    assert evidence.promotion_gate_semantics_represented_in_backtest is True
    assert evidence.promotion_eligible is True
    assert backtest_promotion_gate_state_file_binding_non_authority_ok_v0(evidence)


def test_backtest_binding_uses_surface_m_adapter_v0() -> None:
    bound = bind_promotion_gate_boundary_backtest_state_file_evidence_v0(
        _base_evidence(),
        state_file=_record(),
    )
    assert (
        bound.surface_m_adapter_owner_ref
        == PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )


def test_parity_gap_assessment_surface_m_pass_v0() -> None:
    promotion = next(item for item in parity_surface_assessments_v0() if item.surface_id == "M")
    assert promotion.parity_status == "PASS"
    assert NEXT_RECOMMENDED_SLICE == "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"


def test_mv2_research_wiring_binds_state_file_v0(tmp_path: Path) -> None:
    payload = _state_file_payload()
    state_path = tmp_path / "promotion_gate_backtest_state.json"
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=4),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        promotion_gate_state_file_binding=PromotionGateBacktestStateFileBindingConfigV1(
            state_file_path=state_path,
            expected_state_file_digest_ref=str(payload["state_file_digest_ref"]),
        ),
    )
    assert all(
        o.promotion_gate_backtest_state_file_evidence is not None for o in result.bar_outcomes
    )


def test_verify_state_file_digest_ref_v0() -> None:
    record = _record()
    verify_promotion_gate_backtest_state_file_digest_v0(
        record,
        expected_digest_ref=record.state_file_digest_ref,
    )
    with pytest.raises(ValueError, match="promotion_gate_backtest_state_file_digest_mismatch"):
        verify_promotion_gate_backtest_state_file_digest_v0(record, expected_digest_ref="0" * 64)
