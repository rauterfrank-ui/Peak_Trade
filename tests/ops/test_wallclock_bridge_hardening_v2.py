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
    # Natural mid-path entry is blocked by typed-volatility presence gate after
    # productive CMC typed cutover; prove fill-ledger contract via explicit
    # forced_actionable fixture path (wallclock unreachable; economic excluded).
    state = HardenedBridgeSessionStateV2()
    cycles: list[dict] = []
    for i, mid in enumerate([3500.0, 3510.0, 3520.0]):
        cycles.append(
            run_hardened_bridge_cycle_v2(
                state,
                mid_price=float(mid),
                event_ts_unix=1_700_000_000.0 + float(i),
                session_id="fill-ledger-contract",
            )
        )
    cycles.append(
        run_hardened_bridge_cycle_v2(
            state,
            mid_price=3600.0,
            event_ts_unix=1_700_000_003.0,
            session_id="fill-ledger-contract",
            forced_actionable={"intended_side": "BUY", "intended_quantity": "0.1"},
        )
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
    # Ticker contract requires declared ticker field (last), not markPx.
    with pytest.raises(PriceBasisErrorV2):
        extract_explicit_ticker_price_v2({"data": [{"markPx": "3500"}]})
    px = extract_explicit_ticker_price_v2({"data": [{"last": "3500"}]})
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


def test_ai_layer_non_authority_on_cycle() -> None:
    state, cycles = run_hardened_bridge_cycles_from_mids_v2(
        [3500.0, 3510.0, 3520.0],
        session_id="ai-non-auth",
    )
    assert cycles
    for c in cycles:
        assert c["ai_layer_non_authority"] is True
        assert c["ai_layer_can_override_decisions"] is False
        assert "AI_LAYER_NON_AUTHORITY" in c["notes"]


def test_productive_evidence_streams_bound_in_wallclock_schema() -> None:
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.wallclock_evidence_v1 import (
        APPEND_ONLY,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
        PRODUCTIVE_WALLCLOCK_REQUIRED_APPEND_STREAMS,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.evidence_streams_v2 import (
        append_productive_cycle_evidence_streams_v2,
    )

    for stream in PRODUCTIVE_WALLCLOCK_REQUIRED_APPEND_STREAMS:
        assert stream in APPEND_ONLY
    runtime = (
        REPO_ROOT / "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
        "session_runtime_v1.py"
    ).read_text(encoding="utf-8")
    assert "append_productive_cycle_evidence_streams_v2" in runtime
    assert "completion_verdict.json" in runtime

    state, cycles = run_hardened_bridge_cycles_from_mids_v2(
        [3500.0, 3510.0, 3520.0, 3600.0],
        session_id="prod-streams",
    )
    written: dict[str, list[dict]] = {}

    def _append(name: str, payload: dict) -> None:
        written.setdefault(name, []).append(dict(payload))

    for cycle in cycles:
        append_productive_cycle_evidence_streams_v2(
            append_event=_append,
            session_id="prod-streams",
            cycle=cycle,
        )
    assert written["feature_trace.jsonl"]
    assert written["regime_trace.jsonl"]
    assert written["risk_sizing_trace.jsonl"]
    assert written["order_intent_trace.jsonl"]
    assert written["portfolio_snapshots.jsonl"]
    assert written["equity_curve.jsonl"]
    assert written["runtime_events.jsonl"]
    assert all(e["ai_layer_non_authority"] is True for e in written["order_intent_trace.jsonl"])


def test_observation_adapter_no_default_hold() -> None:
    adapter = (
        REPO_ROOT / "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
        "observation_cycle_adapter_v1.py"
    ).read_text(encoding="utf-8")
    assert 'intended_side: str = "HOLD"' not in adapter
    assert 'intended_quantity: Decimal = Decimal("0")' not in adapter
    assert "INTENDED_SIDE_REQUIRED_NO_DEFAULT_HOLD" in adapter


@pytest.mark.parametrize(
    ("warmup_complete", "features_ok", "expected"),
    [
        (False, False, False),
        (False, True, False),
        (True, True, True),
        (True, False, True),
    ],
)
def test_required_window_complete_boolean_matrix_decoupled_from_features_ok(
    warmup_complete: bool,
    features_ok: bool,
    expected: bool,
) -> None:
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        derive_required_window_complete_v2,
    )

    assert (
        derive_required_window_complete_v2(
            warmup_complete=warmup_complete,
            features_ok=features_ok,
        )
        is expected
    )


def test_required_window_complete_bridge_v1_v2_semantic_parity_source() -> None:
    """Bridge-v1 and Hardening-v2 must both bind required_window_complete to warmup only."""
    v1 = (
        REPO_ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
        "decision_economics_cycle_bridge_v1.py"
    ).read_text(encoding="utf-8")
    v2 = (
        REPO_ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/"
        "hardening_cycle_bridge_v2.py"
    ).read_text(encoding="utf-8")
    assert "required_window_complete=features.warmup_complete," in v1
    assert "features.warmup_complete and features.ok" not in v2
    assert "derive_required_window_complete_v2(" in v2


def test_warmup_complete_true_features_ok_false_no_required_window_incomplete() -> None:
    """Productive call-graph regression for REGIME_UNCLASSIFIED after feature warmup."""
    from trading.master_v2.canonical_scope_initialization_v1 import (
        CanonicalScopeBlockReason,
        CanonicalScopeInitializationPolicyV1,
        SCOPE_INITIALIZATION_POLICY_VERSION,
        ScopeInitializationPrerequisitesV1,
        initialize_canonical_scope,
    )
    from trading.master_v2.canonical_market_context_v1 import (
        FEATURE_CONTRACT_VERSION,
        BarFinalityStatus,
        CanonicalMarketContextV1,
        ClockTrustStatus,
        DataIntegrityStatus,
        WarmupStatus,
        with_computed_input_digest,
    )
    from trading.master_v2.double_play_futures_input import FuturesMarketType

    # Flat path → warmup complete, regime unclassified fail-closed.
    features = compute_feature_regime_from_mid_prices_v2([3500.0, 3500.01, 3500.02])
    assert features.warmup_complete is True
    assert features.ok is False
    assert features.regime_id == "unclassified"
    assert "REGIME_UNCLASSIFIED_FAIL_CLOSED" in features.blockers

    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        derive_required_window_complete_v2,
    )

    required = derive_required_window_complete_v2(
        warmup_complete=features.warmup_complete,
        features_ok=features.ok,
    )
    assert required is True

    ctx = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id="ctx-required-window-decouple",
            instrument_id="ETH-USD_UM_XPERP-310404",
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=1,
            market_event_time="2026-08-03T00:00:00+00:00",
            decision_time="2026-08-03T00:00:00.001+00:00",
            bar_interval="tick",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=float(features.mark_price),
            index_price=float(features.mark_price),
            best_bid=float(features.mark_price),
            best_ask=float(features.mark_price),
            spread=0.0,
            volume=1_000_000.0,
            open_interest=50_000_000.0,
            funding_rate=0.0001,
            volatility_estimate=0.0,
            trend_feature_set=dict(features.trend_features),
            momentum_feature_set=dict(features.momentum_features),
            liquidity_feature_set=dict(features.liquidity_features),
            market_structure_feature_set=dict(features.market_structure_features),
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=WarmupStatus.WARMUP_COMPLETE,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
        )
    )
    scope = initialize_canonical_scope(
        ctx,
        CanonicalScopeInitializationPolicyV1(
            min_scope_band=50.0,
            max_scope_band=500.0,
            policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
        ),
        ScopeInitializationPrerequisitesV1(
            required_window_complete=required,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
    )
    assert CanonicalScopeBlockReason.REQUIRED_WINDOW_INCOMPLETE not in scope.block_reasons
    assert scope.scope is not None

    state, cycles = run_hardened_bridge_cycles_from_mids_v2(
        [3500.0, 3500.01, 3500.02],
        session_id="required-window-decouple-unclassified",
    )
    assert len(state.mid_prices) == 3
    last = cycles[-1]
    assert last["required_window_complete"] is True
    assert last["required_window_complete_inputs"]["warmup_complete"] is True
    assert last["required_window_complete_inputs"]["features_ok"] is False
    assert last["mid_prices_len"] == 3
    assert last["feature_window_min"] == 3
    assert last["regime_id"] == "unclassified"
    assert "REGIME_UNCLASSIFIED_FAIL_CLOSED" in last["feature_blockers"]
    assert "required_window_incomplete" not in list(last.get("reason_codes") or [])
    assert "required_window_incomplete" not in list(
        (last.get("intended_action") or {}).get("reason_codes") or []
    )
    assert last["intended_action"]["intended_quantity"] == "0"
    assert last["intended_action"]["intended_side"] == "HOLD"
    assert last["intended_action"]["intent_action"] in {"NONE", "HOLD", "OBSERVE"}
    entry_intents = [
        c
        for c in cycles
        if str((c.get("intended_action") or {}).get("intent_action", "")).startswith("ENTER")
    ]
    assert entry_intents == []
    assert all(Decimal(str(c["intended_action"]["intended_quantity"])) == 0 for c in cycles)


def test_required_window_incomplete_still_emitted_when_warmup_incomplete() -> None:
    from trading.master_v2.canonical_scope_initialization_v1 import (
        CanonicalScopeBlockReason,
        CanonicalScopeInitializationPolicyV1,
        SCOPE_INITIALIZATION_POLICY_VERSION,
        ScopeInitializationPrerequisitesV1,
        initialize_canonical_scope,
    )
    from trading.master_v2.canonical_market_context_v1 import (
        FEATURE_CONTRACT_VERSION,
        BarFinalityStatus,
        CanonicalMarketContextV1,
        ClockTrustStatus,
        DataIntegrityStatus,
        WarmupStatus,
        with_computed_input_digest,
    )
    from trading.master_v2.double_play_futures_input import FuturesMarketType
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        derive_required_window_complete_v2,
    )

    features = compute_feature_regime_from_mid_prices_v2([3500.0])
    assert features.warmup_complete is False
    required = derive_required_window_complete_v2(
        warmup_complete=features.warmup_complete,
        features_ok=True,  # even if ok were true, window incomplete must remain false
    )
    assert required is False
    ctx = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id="ctx-window-incomplete",
            instrument_id="ETH-USD_UM_XPERP-310404",
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=1,
            market_event_time="2026-08-03T00:00:00+00:00",
            decision_time="2026-08-03T00:00:00.001+00:00",
            bar_interval="tick",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=3500.0,
            index_price=3500.0,
            best_bid=3500.0,
            best_ask=3500.0,
            spread=0.0,
            volume=1.0,
            open_interest=1.0,
            funding_rate=0.0,
            volatility_estimate=0.0,
            trend_feature_set={"slope": 0.0, "strength": 0.0},
            momentum_feature_set={"rsi": 50.0, "roc": 0.0},
            liquidity_feature_set={"depth_score": 0.0},
            market_structure_feature_set={"range_ratio": 0.0},
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=WarmupStatus.WARMUP_REQUIRED,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
        )
    )
    scope = initialize_canonical_scope(
        ctx,
        CanonicalScopeInitializationPolicyV1(
            min_scope_band=50.0,
            max_scope_band=500.0,
            policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
        ),
        ScopeInitializationPrerequisitesV1(
            required_window_complete=required,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
    )
    assert CanonicalScopeBlockReason.REQUIRED_WINDOW_INCOMPLETE in scope.block_reasons

    state, cycles = run_hardened_bridge_cycles_from_mids_v2(
        [3500.0],
        session_id="required-window-still-incomplete",
    )
    assert cycles[0]["required_window_complete"] is False
    assert cycles[0]["mid_prices_len"] == 1
    assert state.cycle_index == 1
