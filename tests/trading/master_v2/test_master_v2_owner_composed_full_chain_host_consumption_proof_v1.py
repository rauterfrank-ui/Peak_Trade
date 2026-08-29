"""Owner-composed full-chain proof: Replay → Mapper → simulated execution/accounting.

Semantics-neutral. No runtime mutation. No frozen golden-vector JSON corpus.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import pytest

from src.governance.canonical_order_intent_v1 import IntentAction
from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_UP_DISTANCE,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
    ensure_accounting_session_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
    construct_simulated_execution_port_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    run_hardened_bridge_cycle_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1 as CAP72_CALL_GRAPH_V1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    IntendedAnalyticalActionV1,
    map_replay_result_to_intended_analytical_action_v1,
)
from trading.master_v2.canonical_market_context_v1 import WarmupStatus
from trading.master_v2.canonical_scope_initialization_v1 import ScopeReinitializationGuardV1
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_composition_matrix_v1 import PositionManagementContext
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    run_integrated_offline_trading_logic_replay_v1,
)
from tests.ops.test_hardening_v2_historical_safety_seam_contracts_v1 import (
    _seed_open_long,
    _warmup_trending,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _INSTRUMENT,
    _market_context,
    _replay_input,
)
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
    _exit_replay_input,
    _patch_replay_owners,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/MASTER_V2_DOUBLE_PLAY_HOST_GRAPH_SSOT_AND_OWNER_COMPOSED_FULL_CHAIN_PROOF_V1.md"
)
REPLAY_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
MAPPER_MODULE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "intended_action_mapper_v1.py"
)
HARDENING_MODULE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    / "hardening_cycle_bridge_v2.py"
)
PORT_MODULE = (
    REPO_ROOT
    / "src/ops/single_future_stateful_no_order_runtime_activation_v1"
    / "simulated_execution_port_v1.py"
)
CAP72_CYCLE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)

_ENTER_OUTCOMES = frozenset({DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value})
_ENTER_ACTIONS = frozenset({IntentAction.ENTER_LONG.value, IntentAction.ENTER_SHORT.value})
_MARK = Decimal("3500")
_TRENDING_MIDS = (3500.0, 3520.0, 3540.0, 3560.0)


@dataclass(frozen=True)
class _Joined:
    replay: Any
    order: list[str]
    counts: dict[str, int]
    mapped: IntendedAnalyticalActionV1
    port_result: dict[str, Any]
    qty_before: Decimal
    qty_after: Decimal
    equity_before: Decimal
    equity_after: Decimal
    fill_present: bool
    port: SimulatedExecutionPortV1


def _signed_qty(portfolio: SimulatedPortfolioEconomicsModelV1, instrument_id: str) -> Decimal:
    pos = portfolio.state.positions.get(instrument_id)
    if pos is None:
        return Decimal("0")
    return Decimal(str(pos.quantity))


def _apply_via_canonical_port(
    mapped: IntendedAnalyticalActionV1,
    *,
    instrument_id: str,
    mark: Decimal,
    seed_side: Optional[str] = None,
    seed_qty: Decimal = Decimal("0"),
    session_id: str,
) -> tuple[SimulatedExecutionPortV1, dict[str, Any], Decimal, Decimal, Decimal, Decimal]:
    port = construct_simulated_execution_port_v1()
    assert port.PORT_KIND == SimulatedExecutionPortV1.PORT_KIND
    session = ensure_accounting_session_v1(instrument_id=instrument_id, state_root=None)
    portfolio = SimulatedPortfolioEconomicsModelV1()
    if seed_side in {"BUY", "SELL"} and seed_qty > 0:
        port.apply_intended_action(
            session=session,
            portfolio=portfolio,
            instrument_id=instrument_id,
            side=seed_side,
            quantity=seed_qty,
            mark_price=mark,
            session_id=f"{session_id}-seed",
            cycle_index=0,
            persist=False,
        )
    qty_before = _signed_qty(portfolio, instrument_id)
    equity_before = Decimal(str(portfolio.state.equity))
    result = port.apply_intended_action(
        session=session,
        portfolio=portfolio,
        instrument_id=instrument_id,
        side=mapped.intended_side,
        quantity=mapped.intended_quantity,
        mark_price=mark,
        session_id=session_id,
        cycle_index=1,
        persist=False,
    )
    qty_after = _signed_qty(portfolio, instrument_id)
    equity_after = Decimal(str(portfolio.state.equity))
    assert port.REAL_EXECUTION_ADAPTER_CONSTRUCTED is False
    assert port.EXCHANGE_ORDER_SUBMIT_REACHABLE is False
    assert port.ORDER_SIDE_EFFECT_OCCURRED is False
    assert result.get("ok") is True
    return port, result, qty_before, qty_after, equity_before, equity_after


def _join_replay(
    monkeypatch: pytest.MonkeyPatch,
    replay_input: Any,
    *,
    session_id: str,
    force_safety_hard_block: bool = False,
    seed_side: Optional[str] = None,
    seed_qty: Decimal = Decimal("0"),
    instrument_id: Optional[str] = None,
    mark: Decimal = _MARK,
) -> _Joined:
    order, counts = _patch_replay_owners(
        monkeypatch, force_safety_hard_block=force_safety_hard_block
    )
    replay = run_integrated_offline_trading_logic_replay_v1(replay_input)
    inst = instrument_id or str(replay_input.instrument_id)
    snap: dict[str, Any] = {"state": {"positions": {}}}
    if seed_side == "BUY" and seed_qty > 0:
        snap = {
            "state": {
                "positions": {inst: {"quantity": str(seed_qty), "avg_entry_price": str(mark)}}
            }
        }
    elif seed_side == "SELL" and seed_qty > 0:
        snap = {
            "state": {
                "positions": {inst: {"quantity": str(-seed_qty), "avg_entry_price": str(mark)}}
            }
        }
    mapped = map_replay_result_to_intended_analytical_action_v1(
        replay,
        instrument_id=inst,
        portfolio_snapshot=snap,
    )
    port, result, qty_before, qty_after, equity_before, equity_after = _apply_via_canonical_port(
        mapped,
        instrument_id=inst,
        mark=mark,
        seed_side=seed_side,
        seed_qty=seed_qty,
        session_id=session_id,
    )
    return _Joined(
        replay=replay,
        order=order,
        counts=counts,
        mapped=mapped,
        port_result=result,
        qty_before=qty_before,
        qty_after=qty_after,
        equity_before=equity_before,
        equity_after=equity_after,
        fill_present=result.get("fill") is not None,
        port=port,
    )


def _assert_no_live_submit_tokens() -> None:
    decision_blob = REPLAY_MODULE.read_text(encoding="utf-8") + MAPPER_MODULE.read_text(
        encoding="utf-8"
    )
    for token in ("submit_order", "place_order", "create_order", "cancel_order"):
        assert token not in decision_blob
    port_src = PORT_MODULE.read_text(encoding="utf-8")
    assert "_FORBIDDEN_CALL_NAMES" in port_src
    port = construct_simulated_execution_port_v1()
    assert not hasattr(port, "submit_order")


def _assert_plan_only(intent: Any) -> None:
    if intent is None:
        return
    assert intent.submission_authorized is False
    assert intent.execution_eligible is False


def test_spec_and_owner_identity_are_proof_only() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "FULL_CHAIN_GOLDEN_VECTOR_STRATEGY=OWNER_COMPOSED" in spec
    assert "GOLDEN_VECTOR_CORPUS_STATUS=ABSENT" in spec
    assert "RUNTIME_MUTATION=false" in spec
    assert "POST_SIM_OBLIGATION_IN_REPLAY=false" in spec
    assert INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER.endswith(
        "integrated_offline_trading_logic_replay_v1"
    )
    src = CAP72_CYCLE.read_text(encoding="utf-8")
    assert "host_simulated_execution_port_v1" in src
    assert "apply_intended_action_via_canonical_accounting_v1" in src
    assert CAP72_CALL_GRAPH_V1.index("master_v2_double_play_integrated_offline_replay") < (
        CAP72_CALL_GRAPH_V1.index("risk_position_sizing")
    )


def test_case_a_normal_enter_pass_joined_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    joined = _join_replay(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        session_id="full-chain-a",
    )
    assert joined.replay.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert joined.order == ["29P", "SAFETY", "29Q", "RECON", "KS"]
    assert joined.counts["29P"] == 1
    assert joined.counts["SAFETY"] == 1
    assert joined.counts["29Q"] == 1
    assert joined.order.index("SAFETY") < joined.order.index("29Q")
    intent = joined.replay.intermediate.canonical_order_intent
    assert intent is not None
    assert intent.intent_action == IntentAction.ENTER_LONG.value
    _assert_plan_only(intent)
    assert joined.mapped.intended_side == "BUY"
    assert joined.mapped.intended_quantity > 0
    assert joined.mapped.quantity_source == "canonical_order_intent"
    assert joined.mapped.intent_action == IntentAction.ENTER_LONG.value
    assert joined.fill_present is True
    assert joined.qty_before == 0
    assert joined.qty_after > 0
    assert joined.port_result["fill"]["side"] == "BUY"
    _assert_no_live_submit_tokens()


def test_case_b_enter_hard_block_no_exposure(monkeypatch: pytest.MonkeyPatch) -> None:
    joined = _join_replay(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        session_id="full-chain-b",
        force_safety_hard_block=True,
    )
    assert joined.replay.evidence.decision_outcome in _ENTER_OUTCOMES
    assert joined.counts["29P"] == 1
    assert joined.counts["SAFETY"] == 1
    assert joined.counts["29Q"] == 0
    assert "29Q" not in joined.order
    assert joined.replay.intermediate.canonical_order_intent is None
    assert joined.mapped.intended_side == "HOLD"
    assert joined.mapped.intended_quantity == Decimal("0")
    assert joined.fill_present is False
    assert joined.qty_before == 0
    assert joined.qty_after == 0
    assert "entry_blocked_by_safety_kernel_boundary" in joined.replay.evidence.reason_codes


def test_case_c_safety_exit_under_block_not_hold(monkeypatch: pytest.MonkeyPatch) -> None:
    seed = Decimal("0.1")
    joined = _join_replay(
        monkeypatch,
        _exit_replay_input(),
        session_id="full-chain-c",
        seed_side="BUY",
        seed_qty=seed,
        instrument_id=_INSTRUMENT,
    )
    assert joined.replay.evidence.decision_outcome == DecisionOutcome.EXIT.value
    assert joined.counts["SAFETY"] == 1
    assert joined.counts["29Q"] == 1
    assert joined.order.index("SAFETY") < joined.order.index("29Q")
    intent = joined.replay.intermediate.canonical_order_intent
    if intent is not None:
        assert intent.intent_action not in _ENTER_ACTIONS
        _assert_plan_only(intent)
    assert joined.mapped.intended_side == "SELL"
    assert joined.mapped.intended_side != "HOLD"
    assert joined.mapped.quantity_source in {"exit_or_reduce", "canonical_order_intent"}
    assert joined.fill_present is True
    assert joined.qty_before > 0
    assert joined.qty_after < joined.qty_before


def test_case_d_adverse_exit_host_and_canonical_port() -> None:
    state = HardenedBridgeSessionStateV2()
    _warmup_trending(state, session_id="full-chain-d")
    entry = _TRENDING_MIDS[-2]
    _seed_open_long(state, mark=entry)
    qty_before = Decimal(
        str(
            ((state.portfolio.snapshot().get("state") or {}).get("positions") or {})
            .get(state.instrument_id, {})
            .get("quantity", "0")
        )
    )
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=float(entry) - float(CANONICAL_ADVERSE_EXIT_DISTANCE) - 1.0,
        event_ts_unix=1_700_000_020.0,
        session_id="full-chain-d",
    )
    assert cycle["cap65_exit_producers"]["scope_adverse_exit"]["triggered"] is True
    assert str(cycle["decision_outcome"]).lower() in {"exit", "reduce"}
    assert cycle["intended_action"]["intended_side"] == "SELL"
    assert cycle["intended_action"]["intended_side"] != "HOLD"
    qty_after = Decimal(
        str(
            ((state.portfolio.snapshot().get("state") or {}).get("positions") or {})
            .get(state.instrument_id, {})
            .get("quantity", "0")
        )
    )
    assert qty_before > 0
    assert qty_after < qty_before
    mapped = IntendedAnalyticalActionV1(
        intended_side=str(cycle["intended_action"]["intended_side"]),
        intended_quantity=Decimal(str(cycle["intended_action"]["intended_quantity"])),
        decision_outcome=str(cycle["intended_action"]["decision_outcome"]),
        selected_side=str(cycle["intended_action"]["selected_side"]),
        intent_action=str(cycle["intended_action"]["intent_action"]),
        quantity_source=str(cycle["intended_action"]["quantity_source"]),
        safety_blocked=bool(cycle["intended_action"]["safety_blocked"]),
        reason_codes=tuple(cycle["intended_action"]["reason_codes"]),
    )
    _, port_result, p_before, p_after, _, _ = _apply_via_canonical_port(
        mapped,
        instrument_id=str(state.instrument_id),
        mark=Decimal(str(entry)),
        seed_side="BUY",
        seed_qty=qty_before,
        session_id="full-chain-d-port",
    )
    assert port_result["fill"] is not None
    assert p_before > 0
    assert p_after < p_before
    assert cycle["execution_eligible"] is False
    assert cycle["execution_class"] == "ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION"


def test_case_e_profit_exit_host_and_canonical_port() -> None:
    state = HardenedBridgeSessionStateV2()
    _warmup_trending(state, session_id="full-chain-e")
    entry = _TRENDING_MIDS[-2]
    _seed_open_long(state, mark=entry)
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=float(entry) + float(CANONICAL_UP_DISTANCE) + 1.0,
        event_ts_unix=1_700_000_030.0,
        session_id="full-chain-e",
    )
    assert cycle["cap65_exit_producers"]["profit_protection"]["triggered"] is True
    assert str(cycle["decision_outcome"]).lower() in {"exit", "reduce"}
    assert cycle["intended_action"]["intended_side"] == "SELL"
    assert cycle["fill"] is not None
    mapped = IntendedAnalyticalActionV1(
        intended_side="SELL",
        intended_quantity=Decimal(str(cycle["intended_action"]["intended_quantity"])),
        decision_outcome=str(cycle["intended_action"]["decision_outcome"]),
        selected_side="long",
        intent_action=str(cycle["intended_action"]["intent_action"]),
        quantity_source=str(cycle["intended_action"]["quantity_source"]),
        safety_blocked=False,
        reason_codes=tuple(cycle["intended_action"]["reason_codes"]),
    )
    _, port_result, p_before, p_after, _, _ = _apply_via_canonical_port(
        mapped,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        mark=Decimal(str(entry)),
        seed_side="BUY",
        seed_qty=Decimal("0.1"),
        session_id="full-chain-e-port",
    )
    assert port_result["fill"] is not None
    assert p_after < p_before


def test_case_f_time_exit_host_and_canonical_port() -> None:
    state = HardenedBridgeSessionStateV2()
    _warmup_trending(state, session_id="full-chain-f")
    entry_mark = _TRENDING_MIDS[-2]
    _seed_open_long(state, mark=entry_mark)
    state.exit_policy_binding.has_open_position = True
    state.exit_policy_binding.entry_price = float(entry_mark)
    state.exit_policy_binding.entry_event_time = 1_700_000_000.0
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=_TRENDING_MIDS[-1],
        event_ts_unix=1_700_000_000.0 + 4000.0,
        session_id="full-chain-f",
    )
    assert cycle["cap65_exit_producers"]["time_exit"]["triggered"] is True
    assert str(cycle["decision_outcome"]).lower() in {"exit", "reduce"}
    assert cycle["intended_action"]["intended_side"] == "SELL"
    mapped = IntendedAnalyticalActionV1(
        intended_side="SELL",
        intended_quantity=Decimal(str(cycle["intended_action"]["intended_quantity"])),
        decision_outcome=str(cycle["intended_action"]["decision_outcome"]),
        selected_side="long",
        intent_action=str(cycle["intended_action"]["intent_action"]),
        quantity_source=str(cycle["intended_action"]["quantity_source"]),
        safety_blocked=False,
        reason_codes=tuple(cycle["intended_action"]["reason_codes"]),
    )
    _, port_result, p_before, p_after, _, _ = _apply_via_canonical_port(
        mapped,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        mark=Decimal(str(entry_mark)),
        seed_side="BUY",
        seed_qty=Decimal("0.1"),
        session_id="full-chain-f-port",
    )
    assert port_result["fill"] is not None
    assert p_after < p_before


def test_case_g_reconcile_only_no_new_exposure(monkeypatch: pytest.MonkeyPatch) -> None:
    joined = _join_replay(
        monkeypatch,
        _replay_input(position_state=PositionState.RECONCILIATION_REQUIRED),
        session_id="full-chain-g",
    )
    assert joined.replay.evidence.decision_outcome == DecisionOutcome.RECONCILE_ONLY.value
    assert joined.replay.evidence.reconciliation_unknown_outcome_ref
    assert joined.mapped.intended_side == "HOLD"
    assert joined.fill_present is False
    assert joined.qty_after == 0
    intent = (
        joined.replay.intermediate.canonical_order_intent if joined.replay.intermediate else None
    )
    if intent is not None:
        assert intent.intent_action not in _ENTER_ACTIONS
        _assert_plan_only(intent)


def test_case_h_unknown_position_or_outcome_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    joined = _join_replay(
        monkeypatch,
        _replay_input(
            position_state=PositionState.SUBMISSION_UNKNOWN,
            reconciliation_state=ReconciliationState.UNKNOWN,
            scope_reinitialization_guard=ScopeReinitializationGuardV1(has_unknown_position=True),
        ),
        session_id="full-chain-h",
    )
    outcome = str(joined.replay.evidence.decision_outcome)
    assert outcome not in _ENTER_OUTCOMES
    assert joined.mapped.intended_side == "HOLD"
    assert joined.fill_present is False
    assert joined.qty_after == 0
    intent = (
        joined.replay.intermediate.canonical_order_intent if joined.replay.intermediate else None
    )
    if intent is not None:
        assert intent.intent_action not in _ENTER_ACTIONS
        _assert_plan_only(intent)


def test_case_i_warmup_or_regime_not_ready_flat(monkeypatch: pytest.MonkeyPatch) -> None:
    joined = _join_replay(
        monkeypatch,
        _replay_input(
            canonical_market_context=_market_context(warmup_status=WarmupStatus.WARMUP_REQUIRED)
        ),
        session_id="full-chain-i",
    )
    assert str(joined.replay.evidence.decision_outcome) not in _ENTER_OUTCOMES
    assert joined.mapped.intended_side == "HOLD"
    assert joined.fill_present is False
    assert joined.qty_after == 0
    state = HardenedBridgeSessionStateV2()
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=3500.0,
        event_ts_unix=1_700_000_000.0,
        session_id="full-chain-i-host",
    )
    assert cycle["feature_regime"]["warmup_complete"] is False
    assert cycle["intended_action"]["intended_side"] == "HOLD"
    assert cycle["fill"] is None


def test_case_j_warmup_or_regime_not_ready_required_exit_preserved() -> None:
    state = HardenedBridgeSessionStateV2()
    for i, mid in enumerate((3500.0, 3500.05, 3500.08)):
        run_hardened_bridge_cycle_v2(
            state,
            mid_price=float(mid),
            event_ts_unix=1_700_000_000.0 + float(i),
            session_id="full-chain-j",
        )
    _seed_open_long(state, mark=3500.08)
    state.killstate_active = True
    state.killstate_trigger = "TEST_KILL"
    qty_before = Decimal(
        str(
            ((state.portfolio.snapshot().get("state") or {}).get("positions") or {})
            .get(state.instrument_id, {})
            .get("quantity", "0")
        )
    )
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=3500.10,
        event_ts_unix=1_700_000_004.0,
        session_id="full-chain-j",
    )
    assert cycle["feature_regime"]["warmup_complete"] is True
    assert cycle["safety_result"] in {"BLOCKED", "EXIT_ONLY"}
    assert str(cycle["decision_outcome"]).lower() == "exit"
    assert cycle["intended_action"]["intended_side"] == "SELL"
    assert cycle["intended_action"]["intended_side"] != "HOLD"
    qty_after = Decimal(
        str(
            ((state.portfolio.snapshot().get("state") or {}).get("positions") or {})
            .get(state.instrument_id, {})
            .get("quantity", "0")
        )
    )
    assert qty_before > 0
    assert qty_after < qty_before


def test_case_k_reversal_flat_before_opposite(monkeypatch: pytest.MonkeyPatch) -> None:
    seed = Decimal("0.1")
    joined = _join_replay(
        monkeypatch,
        _replay_input(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.LONG,
            side_state=SideState.LONG_ACTIVE,
            direction_state=EntryExitDirectionState.LONG_ACTIVE,
            position_management_context=PositionManagementContext.LONG_POSITION,
            price_path=(3500.0, 3400.0),
            scope_direction_state=ScopeDirectionState.SHORT,
        ),
        session_id="full-chain-k",
        seed_side="BUY",
        seed_qty=seed,
        instrument_id=_INSTRUMENT,
        mark=Decimal("3400"),
    )
    assert joined.replay.evidence.decision_outcome != DecisionOutcome.ENTER_SHORT.value
    intent = (
        joined.replay.intermediate.canonical_order_intent if joined.replay.intermediate else None
    )
    if intent is not None:
        assert intent.intent_action != IntentAction.ENTER_SHORT.value
        _assert_plan_only(intent)
    assert (
        joined.mapped.intended_side != "SELL"
        or joined.mapped.intent_action != IntentAction.ENTER_SHORT.value
    )
    if joined.mapped.intended_side in {"BUY", "SELL"}:
        assert joined.mapped.intent_action not in _ENTER_ACTIONS
        assert joined.qty_after <= joined.qty_before
        assert joined.qty_after >= 0
    else:
        assert joined.mapped.intended_side == "HOLD"
        assert joined.qty_after == joined.qty_before


def test_simulated_execution_mode_classification_in_sources() -> None:
    cap72 = CAP72_CYCLE.read_text(encoding="utf-8")
    assert "activated no-order host must use SimulatedExecutionPort only" in cap72
    assert (
        "When activation is disabled (Cap 7.1 path), keep the direct productive delegate" in cap72
    )
    hardening = HARDENING_MODULE.read_text(encoding="utf-8")
    assert "state.portfolio.apply_intended_action" in hardening
    assert "evaluate_offline_safety_kernel_boundary_v0" not in hardening
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "DIRECT_PORTFOLIO_MUTATION_BYPASS_CLASS=MODE_SPECIFIC_VALID" in spec
    assert (
        "SIMULATED_EXECUTIONPORT_IS_CANONICAL_OWNER=true_for_cap72_activated_no_order_host" in spec
    )


def test_appendix_a_conservation_and_host_extension_axes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pass_join = _join_replay(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        session_id="full-chain-axes-a",
    )
    assert pass_join.counts["29P"] == 1
    assert pass_join.counts["SAFETY"] == 1
    assert pass_join.counts["29Q"] == 1
    assert pass_join.mapped.intended_side == "BUY"
    assert pass_join.fill_present is True
    assert pass_join.port.PORT_KIND == "SIMULATED_EXECUTION_PORT_V1"
    assert pass_join.port.EXCHANGE_ORDER_SUBMIT_REACHABLE is False
    _assert_no_live_submit_tokens()
