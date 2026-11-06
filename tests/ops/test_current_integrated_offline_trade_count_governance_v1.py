"""Contract tests for CURRENT integrated-offline trade-count governance closure v1."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from src.ops.integrated_offline_economic_evidence_v1.current_integrated_offline_economic_policy_v1 import (
    CURRENT_INTEGRATED_OFFLINE_ECONOMIC_POLICY_ID,
    TRADE_COUNT_SEMANTIC_COMPLETED_POSITION_ROUND_TRIP,
    load_current_integrated_offline_economic_policy_v1,
    verify_economic_policy_reference_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.integrated_offline_economic_validity_adjudication_v1 import (
    evaluate_integrated_offline_economic_validity_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.integrated_verifier_v1 import (
    verify_integrated_offline_economic_evidence_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_economic_completion_v1 import (
    produce_productive_offline_economic_completion_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedPortfolioEconomicsModelV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTRUMENT = "ETH-USD_UM_XPERP-310404"


def _apply(
    portfolio: SimulatedPortfolioEconomicsModelV1,
    *,
    side: str,
    quantity: str,
    mark: str = "3500",
) -> None:
    portfolio.apply_intended_action(
        instrument_id=INSTRUMENT,
        side=side,
        quantity=Decimal(quantity),
        mark_price=Decimal(mark),
    )


def test_a_flat_to_short_entry_trade_count_zero() -> None:
    p = SimulatedPortfolioEconomicsModelV1()
    _apply(p, side="SELL", quantity="1")
    assert p.completed_trade_count == 0
    assert p.entry_count == 1


def test_b_flat_short_partial_reduce_trade_count_zero() -> None:
    p = SimulatedPortfolioEconomicsModelV1()
    _apply(p, side="SELL", quantity="2")
    _apply(p, side="BUY", quantity="1")
    assert p.completed_trade_count == 0
    assert p.realized_leg_count == 1


def test_c_flat_short_partial_flat_one_completed_trade() -> None:
    p = SimulatedPortfolioEconomicsModelV1()
    _apply(p, side="SELL", quantity="2")
    _apply(p, side="BUY", quantity="1")
    _apply(p, side="BUY", quantity="1")
    assert p.completed_trade_count == 1


def test_d_multiple_partial_reductions_before_flat_one_trade() -> None:
    p = SimulatedPortfolioEconomicsModelV1()
    _apply(p, side="SELL", quantity="4")
    _apply(p, side="BUY", quantity="1")
    _apply(p, side="BUY", quantity="1")
    _apply(p, side="BUY", quantity="2")
    assert p.completed_trade_count == 1
    assert p.realized_leg_count == 3


def test_e_two_independent_lifecycles_two_trades() -> None:
    p = SimulatedPortfolioEconomicsModelV1()
    _apply(p, side="SELL", quantity="1")
    _apply(p, side="BUY", quantity="1")
    _apply(p, side="SELL", quantity="1")
    _apply(p, side="BUY", quantity="1")
    assert p.completed_trade_count == 2


def test_f_fills_alone_do_not_increment_trade_count() -> None:
    p = SimulatedPortfolioEconomicsModelV1()
    _apply(p, side="BUY", quantity="1")
    assert p.state.fill_count == 1
    assert p.completed_trade_count == 0


def test_g_realized_legs_without_flat_do_not_increment_trade_count() -> None:
    p = SimulatedPortfolioEconomicsModelV1()
    _apply(p, side="SELL", quantity="3")
    _apply(p, side="BUY", quantity="1", mark="3400")
    assert p.realized_leg_count >= 1
    assert p.completed_trade_count == 0


def test_h_adjudication_uses_completed_round_trip_trade_count() -> None:
    rel = "evidence/ops/integrated_offline_economic_evidence_v1/trade_count_gov_test_v1"
    produced = produce_productive_offline_economic_completion_bundle_v1(
        repo_root=REPO_ROOT,
        evidence_relpath=rel,
    )
    verified = verify_integrated_offline_economic_evidence_v1(
        repo_root=REPO_ROOT,
        evidence_root=REPO_ROOT / rel,
        expected_proven_source_sha=produced.proven_source_sha,
    )
    assert verified.verified
    metrics = json.loads(
        (REPO_ROOT / rel / "economic_metrics_domain_v1.json").read_text(encoding="utf-8")
    )
    assert metrics.get("trade_count_semantic") == TRADE_COUNT_SEMANTIC_COMPLETED_POSITION_ROUND_TRIP
    adjudicated = evaluate_integrated_offline_economic_validity_v1(
        repo_root=REPO_ROOT,
        evidence_root=REPO_ROOT / rel,
        expected_proven_source_sha=produced.proven_source_sha,
        verification=verified,
    )
    assert adjudicated.economic_validity_evaluated
    if int(metrics.get("trade_count") or 0) < 50:
        assert adjudicated.economic_validity_pass is False


def test_i_minimum_trade_count_resolves_to_50_from_current_policy() -> None:
    policy = load_current_integrated_offline_economic_policy_v1(repo_root=REPO_ROOT)
    assert policy.policy_id == CURRENT_INTEGRATED_OFFLINE_ECONOMIC_POLICY_ID
    assert policy.minimum_trade_count == 50
    assert policy.trade_count_semantic == TRADE_COUNT_SEMANTIC_COMPLETED_POSITION_ROUND_TRIP


def test_j_policy_digest_mismatch_fails_closed() -> None:
    policy = load_current_integrated_offline_economic_policy_v1(repo_root=REPO_ROOT)
    ref = policy.economic_policy_reference_v1()
    ref = dict(ref)
    ref["policy_digest_sha256"] = "0" * 64
    _, blockers = verify_economic_policy_reference_v1(repo_root=REPO_ROOT, policy_ref=ref)
    assert "POLICY:POLICY_DIGEST_MISMATCH" in blockers


def test_k_runner_has_no_hardcoded_50_policy_authority() -> None:
    runner = (
        REPO_ROOT
        / "scripts/ops/run_current_historical_productive_offline_economic_qualification_v1.py"
    )
    text = runner.read_text(encoding="utf-8")
    assert "min_trades_for_policy_pass=50" not in text
    assert "trade_count < 50" not in text


def test_l_portfolio_broker_writes_invariant_unchanged() -> None:
    p = SimulatedPortfolioEconomicsModelV1()
    snap = p.snapshot()
    assert snap["broker_writes"] is False
    assert snap["orders_submitted"] is False
