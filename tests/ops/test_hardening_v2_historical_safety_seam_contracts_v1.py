"""Hardening-v2 host safety-seam contracts: Cap 6.5 producers, EXIT preservation, mapper."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_UP_DISTANCE,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    CALL_GRAPH_EXIT_PRODUCER_STEP,
    SAFETY_PRODUCER_OWNER,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    BRIDGE_SAFETY_ROLE,
    CANONICAL_REPLAY_SAFETY_OWNER,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    CALL_GRAPH_V2,
    HardenedBridgeSessionStateV2,
    apply_hardening_v2_downstream_new_exposure_guard_v2,
    historical_exit_or_reduce_host_action_v2,
    run_hardened_bridge_cycle_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    map_replay_result_to_intended_analytical_action_v1,
)
from trading.master_v2.double_play_composition_matrix_v1 import PositionManagementContext
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    EntryExitDirectionState,
    ExistingPositionSide,
    PositionState,
)
from trading.master_v2.double_play_state import SideState

REPO_ROOT = Path(__file__).resolve().parents[2]
HARDENING_CYCLE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    / "hardening_cycle_bridge_v2.py"
)
MAPPER = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "intended_action_mapper_v1.py"
)
SAFETY_KERNEL = (
    REPO_ROOT / "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py"
)
CRS_OWNER = REPO_ROOT / "src/governance/capital_risk_sizing_v1.py"
INTENT_OWNER = REPO_ROOT / "src/governance/canonical_order_intent_v1.py"
SIDESTATE_OWNER = REPO_ROOT / "src/trading/master_v2/double_play_state.py"
ENTRY_EXIT_OWNER = REPO_ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
REPLAY_OWNER = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/MASTER_V2_HARDENING_V2_HISTORICAL_SAFETY_SEAM_REMEDIATION_V1.md"
)

_TRENDING_MIDS = (3500.0, 3520.0, 3540.0, 3560.0)


def _mapper_result(
    *,
    outcome: str,
    reasons: tuple[str, ...] = (),
    replay_pass: bool = True,
    coi_action: str | None = None,
    coi_qty: str | None = None,
    sizing_qty: str | None = None,
) -> SimpleNamespace:
    coi = None
    if coi_action is not None:
        coi = SimpleNamespace(intent_action=coi_action, quantity=Decimal(str(coi_qty or "0")))
    sizing = None
    if sizing_qty is not None:
        sizing = SimpleNamespace(final_quantity=Decimal(str(sizing_qty)))
    return SimpleNamespace(
        replay_pass=replay_pass,
        evidence=SimpleNamespace(
            decision_outcome=outcome,
            selected_side="long",
            reason_codes=reasons,
        ),
        intermediate=SimpleNamespace(
            canonical_order_intent=coi,
            capital_risk_sizing_decision=sizing,
        ),
    )


def _seed_open_long(state: HardenedBridgeSessionStateV2, *, mark: float) -> None:
    state.portfolio.apply_intended_action(
        instrument_id=state.instrument_id,
        side="BUY",
        quantity=Decimal("0.1"),
        mark_price=Decimal(str(mark)),
        intent_id="seed-open-long",
        fill_id="seed-open-long-fill",
    )
    state.venue_flat = False
    state.existing_position_side = ExistingPositionSide.LONG
    state.position_state = PositionState.OPEN_FULL
    state.position_management_context = PositionManagementContext.LONG_POSITION
    state.side_state = SideState.LONG_ACTIVE
    state.direction_state = EntryExitDirectionState.LONG_ACTIVE


def _warmup_trending(state: HardenedBridgeSessionStateV2, *, session_id: str) -> list[dict]:
    cycles: list[dict] = []
    for i, mid in enumerate(_TRENDING_MIDS[:-1]):
        cycles.append(
            run_hardened_bridge_cycle_v2(
                state,
                mid_price=float(mid),
                event_ts_unix=1_700_000_000.0 + float(i),
                session_id=session_id,
            )
        )
    return cycles


def test_contract_historical_core_owners_not_mutated_by_this_slice() -> None:
    for path in (
        SAFETY_KERNEL,
        CRS_OWNER,
        INTENT_OWNER,
        SIDESTATE_OWNER,
        ENTRY_EXIT_OWNER,
        REPLAY_OWNER,
    ):
        assert path.is_file()
    src = HARDENING_CYCLE.read_text(encoding="utf-8")
    assert "evaluate_offline_safety_kernel_boundary_v0" not in src
    assert "bind_canonical_order_intent_offline_replay_evidence_v0" not in src
    assert SPEC_PATH.is_file()
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert "CANONICAL_SAFETY_OWNER_CHANGED=false" in spec
    assert "BRIDGE_SAFETY_ROLE=INPUT_PRODUCER_ONLY" in spec


def test_contract_01_cap65_producers_feed_hardening_v2_without_stubbed_exits() -> None:
    src = HARDENING_CYCLE.read_text(encoding="utf-8")
    assert "evaluate_host_exit_policy_producers_v1" in src
    assert "scope_adverse_exit_signal=PolicySignalV0(triggered=False)" not in src
    assert "profit_protection_signal=PolicySignalV0(triggered=False)" not in src
    assert "time_exit_signal=PolicySignalV0(triggered=False)" not in src
    assert "strategy_invalidation_signal=PolicySignalV0(triggered=False)" not in src
    assert CALL_GRAPH_EXIT_PRODUCER_STEP in CALL_GRAPH_V2
    assert CALL_GRAPH_V2.index(CALL_GRAPH_EXIT_PRODUCER_STEP) < CALL_GRAPH_V2.index(
        "master_v2_double_play_integrated_offline_replay"
    )
    state = HardenedBridgeSessionStateV2()
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=3500.0,
        event_ts_unix=1_700_000_000.0,
        session_id="cap65-no-stub",
    )
    producers = cycle["cap65_exit_producers"]
    assert producers["evaluation_bound"] is True
    assert producers["placeholder_false_signal_used_as_unbound_stub"] is False
    for key in (
        "scope_adverse_exit",
        "profit_protection",
        "time_exit",
        "strategy_invalidation",
        "safety_exit",
        "hard_risk_reduction",
    ):
        assert producers[key]["evaluation_bound"] is True


def test_contract_06_bridge_safety_is_input_producer_not_second_replay_owner() -> None:
    src = HARDENING_CYCLE.read_text(encoding="utf-8")
    assert "evaluate_bridge_safety_v2(" not in src
    state = HardenedBridgeSessionStateV2()
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=3500.0,
        event_ts_unix=1_700_000_000.0,
        session_id="bridge-role",
    )
    assert cycle["bridge_safety_role"] == BRIDGE_SAFETY_ROLE == "INPUT_PRODUCER_ONLY"
    assert cycle["canonical_replay_safety_owner"] == CANONICAL_REPLAY_SAFETY_OWNER
    assert SAFETY_PRODUCER_OWNER in cycle["safety_evaluation"]["safety_inputs"]["evaluation_owner"]
    assert (
        cycle["safety_evaluation"]["safety_inputs"]["bridge_safety_role"] == "INPUT_PRODUCER_ONLY"
    )
    assert cycle["execution_eligible"] is False
    assert cycle["orders_authorized"] is False
    assert cycle["live_authorized"] is False


def test_contract_03_and_12_downstream_guard_does_not_hold_historical_exit() -> None:
    assert historical_exit_or_reduce_host_action_v2(
        intent_action="EXIT",
        decision_outcome="exit",
    )
    guarded = apply_hardening_v2_downstream_new_exposure_guard_v2(
        {
            "intended_side": "SELL",
            "intended_quantity": "0.1",
            "decision_outcome": "exit",
            "selected_side": "long",
            "intent_action": "EXIT",
            "quantity_source": "exit_or_reduce",
            "safety_blocked": False,
            "reason_codes": ["safety_exit"],
        },
        producer_safety_result="BLOCKED",
        warmup_complete=False,
    )
    assert guarded["intended_side"] == "SELL"
    assert guarded["intent_action"] == "EXIT"
    assert guarded["quantity_source"] == "exit_or_reduce"


def test_contract_11_downstream_guard_holds_new_exposure_when_producer_blocked() -> None:
    guarded = apply_hardening_v2_downstream_new_exposure_guard_v2(
        {
            "intended_side": "BUY",
            "intended_quantity": "0.1",
            "decision_outcome": "enter_long",
            "selected_side": "long",
            "intent_action": "ENTER_LONG",
            "quantity_source": "canonical_order_intent",
            "safety_blocked": False,
            "reason_codes": [],
        },
        producer_safety_result="BLOCKED",
        warmup_complete=True,
    )
    assert guarded["intended_side"] == "HOLD"
    assert guarded["quantity_source"] == "downstream_new_exposure_execution_guard"
    assert "DOWNSTREAM_NEW_EXPOSURE_NOT_ELIGIBLE" in guarded["reason_codes"]


def test_contract_05_enter_without_coi_cannot_become_buy_via_sizing_fallback() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(outcome="enter_long", sizing_qty="1.0"),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        portfolio_snapshot={"state": {"positions": {}}},
    )
    assert mapped.intended_side == "HOLD"
    assert mapped.quantity_source == "enter_without_canonical_order_intent"
    assert "NO_CANONICAL_ORDER_INTENT" in mapped.reason_codes


def test_contract_05_enter_with_coi_still_maps_buy() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(outcome="enter_long", coi_action="ENTER_LONG", coi_qty="0.2"),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        portfolio_snapshot={"state": {"positions": {}}},
    )
    assert mapped.intended_side == "BUY"
    assert mapped.intended_quantity == Decimal("0.2")
    assert mapped.quantity_source == "canonical_order_intent"


def test_mapper_safety_exit_does_not_hold_close_action() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(
            outcome="exit",
            reasons=("safety_exit", "TEST_KILL", "TYPED_VOLATILITY_ESTIMATE_MISSING"),
            replay_pass=False,
        ),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        portfolio_snapshot={
            "state": {
                "positions": {
                    PRODUCTION_INSTRUMENT_ID: {"quantity": "0.1", "avg_entry_price": "3500"}
                }
            }
        },
    )
    assert mapped.intended_side == "SELL"
    assert mapped.decision_outcome == "exit"
    assert mapped.quantity_source == "exit_or_reduce"
    assert mapped.intent_action in {"EXIT", "NONE"}


def test_case_a_normal_pass_cap65_then_replay_then_simulated_boundary() -> None:
    state = HardenedBridgeSessionStateV2()
    _warmup_trending(state, session_id="case-a")
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=_TRENDING_MIDS[-1],
        event_ts_unix=1_700_000_004.0,
        session_id="case-a",
    )
    assert cycle["ok"] is True
    assert cycle["bridge_safety_role"] == "INPUT_PRODUCER_ONLY"
    assert cycle["execution_class"] == "ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION"
    assert cycle["execution_eligible"] is False
    assert CALL_GRAPH_EXIT_PRODUCER_STEP in cycle["call_graph"]
    assert cycle["cap65_exit_producers"]["evaluation_bound"] is True
    assert cycle["intended_action"]["intended_side"] in {"BUY", "SELL", "HOLD"}
    if str(cycle["decision_outcome"]).lower() in {"enter_long", "enter_short"}:
        if cycle["intended_action"]["intended_side"] in {"BUY", "SELL"}:
            assert cycle["intended_action"]["quantity_source"] == "canonical_order_intent"


def test_case_b_enter_safety_block_no_buy_fallback() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(
            outcome="enter_long",
            reasons=("safety_mode_blocked", "trading_gate_blocked"),
            sizing_qty="9.0",
        ),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert mapped.intended_side == "HOLD"
    assert mapped.intended_quantity == Decimal("0")


def test_case_c_safety_exit_while_blocked_is_not_rewritten_to_hold() -> None:
    state = HardenedBridgeSessionStateV2()
    _warmup_trending(state, session_id="case-c")
    _seed_open_long(state, mark=_TRENDING_MIDS[-2])
    state.killstate_active = True
    state.killstate_trigger = "TEST_KILL"
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=_TRENDING_MIDS[-1],
        event_ts_unix=1_700_000_010.0,
        session_id="case-c",
    )
    assert cycle["safety_result"] == "BLOCKED"
    assert cycle["cap65_exit_producers"]["safety_exit"]["triggered"] is True
    assert str(cycle["decision_outcome"]).lower() == "exit"
    assert cycle["intended_action"]["intended_side"] == "SELL"
    assert str(cycle["intended_action"]["decision_outcome"]).lower() == "exit"
    assert cycle["intended_action"]["quantity_source"] in {"exit_or_reduce", "exit_flat"}
    assert cycle["intended_action"]["quantity_source"] != "safety_veto"
    assert cycle["intended_action"]["quantity_source"] != "downstream_new_exposure_execution_guard"


def test_case_d_adverse_exit_uses_canonical_producer() -> None:
    state = HardenedBridgeSessionStateV2()
    _warmup_trending(state, session_id="case-d")
    entry = _TRENDING_MIDS[-2]
    _seed_open_long(state, mark=entry)
    adverse_mark = float(entry) - float(CANONICAL_ADVERSE_EXIT_DISTANCE) - 1.0
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=adverse_mark,
        event_ts_unix=1_700_000_020.0,
        session_id="case-d",
    )
    assert cycle["cap65_exit_producers"]["scope_adverse_exit"]["triggered"] is True
    assert cycle["cap65_exit_producers"]["scope_adverse_exit"]["reason_code"] != ""
    assert str(cycle["decision_outcome"]).lower() in {"exit", "reduce"}


def test_case_e_profit_exit_uses_canonical_producer() -> None:
    state = HardenedBridgeSessionStateV2()
    _warmup_trending(state, session_id="case-e")
    entry = _TRENDING_MIDS[-2]
    _seed_open_long(state, mark=entry)
    profit_mark = float(entry) + float(CANONICAL_UP_DISTANCE) + 1.0
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=profit_mark,
        event_ts_unix=1_700_000_030.0,
        session_id="case-e",
    )
    assert cycle["cap65_exit_producers"]["profit_protection"]["triggered"] is True
    assert str(cycle["decision_outcome"]).lower() in {"exit", "reduce"}


def test_case_f_time_exit_uses_canonical_producer() -> None:
    state = HardenedBridgeSessionStateV2()
    _warmup_trending(state, session_id="case-f")
    entry_mark = _TRENDING_MIDS[-2]
    _seed_open_long(state, mark=entry_mark)
    state.exit_policy_binding.has_open_position = True
    state.exit_policy_binding.entry_price = float(entry_mark)
    state.exit_policy_binding.entry_event_time = 1_700_000_000.0
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=_TRENDING_MIDS[-1],
        event_ts_unix=1_700_000_000.0 + 4000.0,
        session_id="case-f",
    )
    assert cycle["cap65_exit_producers"]["time_exit"]["triggered"] is True
    assert str(cycle["decision_outcome"]).lower() in {"exit", "reduce"}


def test_case_g_warmup_incomplete_flat_no_new_exposure() -> None:
    state = HardenedBridgeSessionStateV2()
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=3500.0,
        event_ts_unix=1_700_000_000.0,
        session_id="case-g",
    )
    assert cycle["feature_regime"]["warmup_complete"] is False
    assert cycle["intended_action"]["intended_side"] == "HOLD"
    assert cycle["fill"] is None
    assert cycle["execution_eligible"] is False


def test_case_h_regime_not_ready_with_required_exit_not_held() -> None:
    """Warmup complete but regime unclassified (EXIT_ONLY) must not suppress safety EXIT."""
    state = HardenedBridgeSessionStateV2()
    for i, mid in enumerate((3500.0, 3500.05, 3500.08)):
        run_hardened_bridge_cycle_v2(
            state,
            mid_price=float(mid),
            event_ts_unix=1_700_000_000.0 + float(i),
            session_id="case-h",
        )
    _seed_open_long(state, mark=3500.08)
    state.killstate_active = True
    state.killstate_trigger = "TEST_KILL"
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=3500.10,
        event_ts_unix=1_700_000_004.0,
        session_id="case-h",
    )
    assert cycle["feature_regime"]["warmup_complete"] is True
    assert cycle["safety_result"] in {"BLOCKED", "EXIT_ONLY"}
    assert str(cycle["decision_outcome"]).lower() == "exit"
    assert cycle["intended_action"]["intended_side"] == "SELL"
    assert cycle["intended_action"]["intent_action"] in {"EXIT", "exit", "NONE"}


def test_no_live_or_real_submission_in_hardening_cycle_source() -> None:
    src = HARDENING_CYCLE.read_text(encoding="utf-8") + MAPPER.read_text(encoding="utf-8")
    for token in ("submit_order", "place_order", "create_order", "cancel_order"):
        assert token not in src
