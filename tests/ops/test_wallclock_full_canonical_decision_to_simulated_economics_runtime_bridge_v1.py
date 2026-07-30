"""Contract tests for WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1."""

from __future__ import annotations

import ast
from pathlib import Path

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    CAPABILITY_ID,
    CLOSES_NEXT_CAPABILITY_ALIAS,
    DECISION_AUTHORITY_OWNER,
    ECONOMIC_VALIDITY_PASS,
    LIVE_AUTHORIZED,
    ORDERS_AUTHORIZED,
    OWNER,
    PAPER_EXECUTION_AUTHORIZED,
    PROMOTION_PASS,
    RUNTIME_BRIDGE_LIVE_ACTIVATED,
    TESTNET_AUTHORIZED,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1,
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.feature_regime_pipeline_v1 import (
    compute_feature_regime_from_mid_prices_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    REQUIRED_CALL_GRAPH,
    verify_full_economic_reconstruction_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG = (
    REPO_ROOT / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
)


def test_capability_identity_and_invariants() -> None:
    assert CAPABILITY_ID == (
        "WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1"
    )
    assert CLOSES_NEXT_CAPABILITY_ALIAS.startswith("INTEGRATED_PAPER_SHADOW_STRATEGY_INTENT")
    assert OWNER.endswith("runtime_bridge_v1")
    assert DECISION_AUTHORITY_OWNER.endswith("run_integrated_offline_trading_logic_replay_v1")
    assert ORDERS_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_AUTHORIZED is False
    assert PAPER_EXECUTION_AUTHORIZED is False
    assert ECONOMIC_VALIDITY_PASS is False
    assert PROMOTION_PASS is False
    assert RUNTIME_BRIDGE_LIVE_ACTIVATED is False


def test_feature_regime_warmup_and_trending() -> None:
    cold = compute_feature_regime_from_mid_prices_v1([3500.0])
    assert cold.warmup_complete is False
    assert "FEATURE_WARMUP_INCOMPLETE" in cold.blockers
    hot = compute_feature_regime_from_mid_prices_v1([3500.0, 3550.0, 3600.0, 3700.0])
    assert hot.ok is True
    assert hot.warmup_complete is True
    assert hot.regime_id in {"trending", "ranging", "volatile"}


def test_full_call_graph_executes_with_fill_and_persistent_portfolio() -> None:
    mids = [3500.0, 3510.0, 3520.0, 3550.0, 3600.0, 3650.0, 3700.0, 3750.0]
    state, cycles = run_bridge_cycles_from_mids_v1(mids, session_id="unit-bridge")
    assert len(cycles) == len(mids)
    assert all(c.execution_eligible is False for c in cycles)
    assert all(c.orders_authorized is False for c in cycles)
    assert all(c.live_authorized is False for c in cycles)
    assert all(set(REQUIRED_CALL_GRAPH).issubset(set(c.call_graph)) for c in cycles)
    assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH

    actionable = [c for c in cycles if c.intended_action["intended_side"] in {"BUY", "SELL"}]
    assert actionable, "expected at least one actionable analytical intent on rising path"
    assert state.fill_ledger, "expected at least one simulated fill"
    assert int(state.portfolio.economic_metrics().fill_count) >= 1
    # Portfolio persists across cycles (not ephemeral per cycle).
    assert state.cycle_index == len(mids)
    assert len(state.cycle_ledger) == len(mids)

    verification = verify_full_economic_reconstruction_v1(
        cycle_ledger=state.cycle_ledger,
        fill_ledger=state.fill_ledger,
        final_portfolio_snapshot=state.portfolio.snapshot(),
    )
    assert verification.ok is True
    assert verification.reconstructed_fill_count == len(state.fill_ledger)


def test_fail_closed_rejects_authority_flags_in_reconstruction() -> None:
    mids = [3500.0, 3510.0, 3520.0]
    state, _ = run_bridge_cycles_from_mids_v1(mids, session_id="unit-bridge-fc")
    poisoned = list(state.cycle_ledger)
    poisoned[-1] = dict(poisoned[-1])
    poisoned[-1]["orders_authorized"] = True
    bad = verify_full_economic_reconstruction_v1(
        cycle_ledger=poisoned,
        fill_ledger=state.fill_ledger,
        final_portfolio_snapshot=state.portfolio.snapshot(),
    )
    assert bad.ok is False
    assert any(x.startswith("ORDERS_AUTHORIZED_TRUE") for x in bad.blockers)


def test_no_order_client_imports_in_bridge_package() -> None:
    for path in PKG.glob("*.py"):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        lowered = src.lower()
        assert "place_order" not in lowered
        assert "submit_order" not in lowered
        assert "okx.account" not in lowered
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "broker" not in alias.name.lower()
                    assert not alias.name.startswith("src.execution.venue")
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("src.execution.venue")
                assert "private" not in node.module.lower()


def test_session_runtime_defaults_bridge_enabled() -> None:
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
        WallclockRuntimeConfigV1,
    )

    cfg = WallclockRuntimeConfigV1()
    assert cfg.decision_economics_bridge_enabled is True


def test_runbook_and_config_exist() -> None:
    runbook = (
        REPO_ROOT
        / "docs/ops/runbooks/WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1.md"
    )
    cfg = (
        REPO_ROOT
        / "config/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.toml"
    )
    assert runbook.is_file()
    assert cfg.is_file()
    text = runbook.read_text(encoding="utf-8")
    assert CAPABILITY_ID in text
    assert "ORDERS" in text.upper() or "orders_authorized=false" in text
