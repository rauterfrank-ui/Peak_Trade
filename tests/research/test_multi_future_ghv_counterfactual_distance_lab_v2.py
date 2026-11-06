from __future__ import annotations

from research.multi_future_ghv_counterfactual_distance_lab_v2.cmc_builder_v2 import (
    build_finalized_cmc_v2,
    spread_consistent_quotes_v2,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.proof_gates_v2 import (
    prove_natural_enter_harness_v2,
    prove_symmetric_fork_v2,
    run_pre_run_gates_v2,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.replay_input_v2 import (
    build_integrated_replay_input_v2,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.symmetric_fork_v2 import (
    run_replay_symmetric_v2,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.canonical_market_context_v1 import (
    CanonicalMarketContextBlockReason,
    validate_canonical_market_context_fields,
)


def test_spread_consistent_cmc_passes_validation() -> None:
    ctx = build_finalized_cmc_v2(
        instrument_id="inst-eth-usdt-perp", mark_price=0.2, volatility_estimate=0.04, trading_epoch=1
    )
    blocks = validate_canonical_market_context_fields(ctx)
    assert CanonicalMarketContextBlockReason.SPREAD_INCONSISTENT not in blocks


def test_symmetric_fork_matches_reference() -> None:
    proof = prove_symmetric_fork_v2()
    assert proof["MODEL_B_V2_VS_CURRENT_REFERENCE_PASS"] is True


def test_natural_enter_witness() -> None:
    w = prove_natural_enter_harness_v2()
    assert w["NATURAL_ENTER_HARNESS_CAPABILITY_PROVEN"] is True


def test_v2_replay_not_blocked_on_spread() -> None:
    inp = build_integrated_replay_input_v2(
        replay_id="t",
        instrument_id="inst-eth-usdt-perp",
        mark_price=100.0,
        volatility_estimate=0.04,
        price_path=(100.0, 101.0),
        trading_epoch=10,
    )
    r = run_integrated_offline_trading_logic_replay_v1(inp)
    assert "spread_inconsistent" not in r.fail_reasons


def test_pre_run_gates() -> None:
    gates = run_pre_run_gates_v2()
    assert gates["gates_ok"] is True


def test_symmetric_replay_smoke() -> None:
    inp = build_integrated_replay_input_v2(
        replay_id="sym",
        instrument_id="inst-eth-usdt-perp",
        mark_price=3500.0,
        volatility_estimate=0.38,
        price_path=(3500.0, 3570.0),
        trading_epoch=44,
    )
    r, _fork = run_replay_symmetric_v2(inp, model_id="MODEL_B_CURRENT_LAYER_C")
    assert r.evidence.decision_outcome != "blocked" or "spread_inconsistent" not in r.fail_reasons
