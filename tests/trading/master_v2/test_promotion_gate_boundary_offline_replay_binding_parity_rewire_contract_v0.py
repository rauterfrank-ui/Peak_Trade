"""Contract: Promotion Gate boundary offline replay binding parity rewire v0 (offline only)."""

from __future__ import annotations

import ast
from pathlib import Path

from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
from src.governance.promotion_loop import promotion_economic_gate_v1 as gate
from trading.master_v2.promotion_gate_boundary_offline_replay_binding_adapter_v0 import (
    PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    PROMOTION_GATE_CANONICAL_OWNER,
    PromotionGateBoundaryOfflineReplayContextV0,
    bind_promotion_gate_boundary_offline_replay_evidence_v0,
    promotion_gate_boundary_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_promotion_gate_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
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


def _valid_context(**kwargs: object) -> PromotionGateBoundaryOfflineReplayContextV0:
    economic_policy_digest = canonical_economic_validity_policy_v1().policy_digest()
    base = {
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
    }
    base.update(kwargs)
    return PromotionGateBoundaryOfflineReplayContextV0(**base)


def _base_evidence():
    return build_scenario_tick_decision_evidence_v0(
        decision_id="offline-promotion-gate-decision",
        replay_id="offline-promotion-gate-replay",
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


def test_owner_constants_reuse_canonical_promotion_gate_v0() -> None:
    assert PROMOTION_GATE_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER.endswith(
        "promotion_gate_boundary_offline_replay_binding_adapter_v0"
    )
    assert PROMOTION_GATE_CANONICAL_OWNER == gate.PROMOTION_ECONOMIC_GATE_POLICY_OWNER


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
        }
    )
    for path in _FORBIDDEN_IMPORT_SCAN_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_offline_binding_reuses_canonical_gate_without_runtime_authority_v0() -> None:
    binding = bind_promotion_gate_boundary_offline_replay_evidence_v0(
        _base_evidence(),
        context=_valid_context(),
    )
    assert binding.binding_applied is True
    assert binding.boundary.promotion_gate_boundary_bound is True
    assert binding.boundary.no_runtime_authority_from_promotion_represented is True
    assert binding.gate_result.promotion_eligible is True
    assert binding.gate_result.runtime_eligible is False
    assert binding.gate_result.execution_allowed is False
    assert promotion_gate_boundary_binding_non_authority_boundary_ok_v0(binding)


def test_confidence_only_blocked_by_canonical_gate_v0() -> None:
    binding = bind_promotion_gate_boundary_offline_replay_evidence_v0(
        _base_evidence(),
        context=_valid_context(promotion_basis_confidence_only=True),
    )
    assert binding.boundary.no_promotion_from_confidence_only_represented is True
    assert binding.gate_result.promotion_eligible is False
    assert gate.REASON_CONFIDENCE_SCORE_ONLY in binding.gate_result.reason_codes
