"""Contract tests for wallclock bridge hardening v2."""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.acceptance_gates_v2 import (
    derive_acceptance_gates_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.canonical_strategy_probe_v2 import (
    run_canonical_strategy_probe_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    CANONICAL_FILL_LEDGER_ATTR,
    CAPABILITY_ID,
    DEFAULT_REGIME_FALLBACK_ACTIVE,
    FORCED_FIXTURE_WALLCLOCK_REACHABLE,
    HARDCODED_HOLD_PRESENT,
    SESSION_RESTART_POLICY,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.feature_regime_pipeline_v2 import (
    compute_feature_regime_from_mid_prices_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.forced_wiring_fixture_v2 import (
    FORCED_WIRING_FIXTURE_MODULE,
    run_forced_wiring_fixture_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.full_economic_reconstruction_verifier_v2 import (
    verify_full_economic_reconstruction_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    run_hardened_bridge_cycle_v2,
    run_hardened_bridge_cycles_from_mids_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (
    IdempotencyErrorV2,
    IdempotentPortfolioV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.market_data_price_basis_v2 import (
    PriceBasisErrorV2,
    extract_explicit_ticker_price_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.stub_fallback_scan_v2 import (
    run_stub_fallback_scan_v2,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_fill_ledger_contract_canonical_attr() -> None:
    assert CANONICAL_FILL_LEDGER_ATTR == "fill_ledger"
    state, cycles = run_hardened_bridge_cycles_from_mids_v2(
        [3500.0, 3510.0, 3520.0, 3550.0, 3600.0, 3650.0, 3700.0, 3750.0],
        session_id="fill-ledger-contract",
    )
    assert hasattr(state, "fill_ledger")
    assert not hasattr(state, "fills_ledger")
    assert isinstance(state.fill_ledger, list)
    assert any(c.get("fill") for c in cycles)
    assert len(state.fill_ledger) >= 1
    verification = verify_full_economic_reconstruction_v2(
        cycle_ledger=cycles,
        fill_ledger=state.fill_ledger,
        final_portfolio_snapshot=state.portfolio.snapshot(),
    )
    assert verification.ok is True


def test_stable_provenance_linkage() -> None:
    state, cycles = run_hardened_bridge_cycles_from_mids_v2(
        [3500.0, 3510.0, 3520.0, 3550.0, 3600.0],
        session_id="prov-link",
    )
    for c in cycles:
        assert c["session_id"] == "prov-link"
        assert c["cycle_id"]
        assert c["decision_id"]
        assert c["risk_decision_id"]
        assert c["intent_id"]
        action = c["intended_action"]
        assert action["decision_id"] == c["decision_id"]
        assert action["risk_decision_id"] == c["risk_decision_id"]
        assert action["intent_id"] == c["intent_id"]
        assert c["feature_digest"]
        assert c["regime_digest"]
        assert c["config_digest"]
        assert c["portfolio_state_before_hash"]
        assert c["portfolio_state_after_hash"]
        if c.get("fill"):
            assert c["fill"]["fill_id"] == c["fill_id"]
            assert c["fill"]["intent_id"] == c["intent_id"]


def test_intent_and_fill_idempotency() -> None:
    portfolio = IdempotentPortfolioV2.from_params(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    fill = portfolio.apply_intended_action(
        instrument_id="ETH-USD_UM_XPERP-310404",
        side="BUY",
        quantity=Decimal("0.1"),
        mark_price=Decimal("3500"),
        intent_id="intent_a",
        fill_id="fill_a",
    )
    assert fill is not None
    snap = portfolio.snapshot()
    with pytest.raises(IdempotencyErrorV2):
        portfolio.apply_intended_action(
            instrument_id="ETH-USD_UM_XPERP-310404",
            side="BUY",
            quantity=Decimal("0.1"),
            mark_price=Decimal("3500"),
            intent_id="intent_a",
            fill_id="fill_b",
        )
    assert portfolio.snapshot() == snap
    with pytest.raises(IdempotencyErrorV2):
        portfolio.apply_intended_action(
            instrument_id="ETH-USD_UM_XPERP-310404",
            side="BUY",
            quantity=Decimal("0.1"),
            mark_price=Decimal("3500"),
            intent_id="intent_b",
            fill_id="fill_a",
        )
    assert portfolio.snapshot() == snap


def test_default_regime_fallback_absent() -> None:
    assert DEFAULT_REGIME_FALLBACK_ACTIVE is False
    cold = compute_feature_regime_from_mid_prices_v2([3500.0, 3500.01, 3500.02])
    assert cold.default_regime_fallback_active is False
    assert cold.regime_id != "trending" or cold.ok is True
    # Nearly flat → unclassified fail-closed (not silent trending).
    if not cold.ok:
        assert "REGIME_UNCLASSIFIED_FAIL_CLOSED" in cold.blockers or "INSUFFICIENT" in ",".join(
            cold.blockers
        )


def test_explicit_price_basis_no_silent_chain() -> None:
    with pytest.raises(PriceBasisErrorV2):
        extract_explicit_ticker_price_v2({"data": [{"last": "3500"}]})
    px = extract_explicit_ticker_price_v2({"data": [{"markPx": "3500"}]})
    assert px == 3500.0


def test_forced_wiring_and_canonical_probe(tmp_path: Path) -> None:
    forced = run_forced_wiring_fixture_v2(evidence_root=tmp_path / "forced")
    assert forced["forced_wiring_fixture_pass"] is True
    assert forced["forced_fixture_wallclock_reachable"] is False
    assert forced["forced_fixture_economic_metrics_excluded"] is True
    assert Decimal(forced["fee"]) > 0
    assert Decimal(forced["slippage"]) > 0
    assert (tmp_path / "forced" / "economic_metrics.json").is_file()
    metrics = (tmp_path / "forced" / "economic_metrics.json").read_text(encoding="utf-8")
    assert "excluded" in metrics

    canonical = run_canonical_strategy_probe_v2(evidence_root=tmp_path / "canonical")
    assert canonical["canonical_strategy_probe_pass"] is True
    assert canonical["canonical_strategy_probe_forced_action"] is False
    assert canonical["hold_provenance_complete"] is True


def test_forced_fixture_not_imported_by_wallclock() -> None:
    runtime = (
        REPO_ROOT
        / "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/session_runtime_v1.py"
    ).read_text(encoding="utf-8")
    assert "forced_wiring_fixture_v2" not in runtime
    assert FORCED_FIXTURE_WALLCLOCK_REACHABLE is False
    assert FORCED_WIRING_FIXTURE_MODULE.endswith("forced_wiring_fixture_v2")


def test_stub_scan_and_acceptance_gates(tmp_path: Path) -> None:
    assert HARDCODED_HOLD_PRESENT is False
    assert SESSION_RESTART_POLICY == "NO_IMPLICIT_RESUME"
    scan = run_stub_fallback_scan_v2(repo_root=REPO_ROOT)
    assert scan.ok is True, scan.blockers
    forced = run_forced_wiring_fixture_v2(evidence_root=tmp_path / "forced2")
    canonical = run_canonical_strategy_probe_v2(evidence_root=tmp_path / "canonical2")
    gates = derive_acceptance_gates_v2(
        canonical_probe=canonical,
        forced_fixture=forced,
        stub_scan=scan.to_dict(),
        verification=canonical.get("verification"),
    )
    assert gates.go_for_preregistration is False
    assert gates.go_for_authorization is False
    assert gates.go_for_1h_run is False
    assert gates.fail_closed is True
    assert gates.ok is True, gates.blockers


def test_no_private_api_or_order_routing_in_hardening_package() -> None:
    pkg = (
        REPO_ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    )
    forbidden_calls = {"place_order", "submit_order", "create_order", "cancel_order"}
    for path in pkg.glob("*.py"):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                assert name not in forbidden_calls
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "private" not in node.module.lower()
                assert not node.module.startswith("src.execution.venue")


def test_safety_veto_on_killstate() -> None:
    state = HardenedBridgeSessionStateV2()
    state.killstate_active = True
    state.killstate_trigger = "TEST_KILL"
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=3600.0,
        event_ts_unix=1_700_000_000.0,
        session_id="safety-veto",
    )
    assert cycle["safety_result"] == "BLOCKED"
    assert cycle["intended_action"]["intended_side"] == "HOLD"
    assert cycle["safety_evaluation"]["evaluation_bound"] is True


def test_capability_identity() -> None:
    assert CAPABILITY_ID.endswith("HARDENING_V2")
