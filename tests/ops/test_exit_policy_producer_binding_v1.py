"""Capability 6.5 — Exit policy producer binding tests."""

from __future__ import annotations

import ast
from pathlib import Path

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_CONFIRMATION_EPOCHS,
    CANONICAL_REVERSAL_DISTANCE,
    CANONICAL_UP_DISTANCE,
)
from src.ops.exit_policy_producer_binding_v1.authority_matrix_v1 import (
    inventory_exit_policy_authority_v1,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CALL_GRAPH_EXIT_PRODUCER_STEP,
    CALL_GRAPH_EXIT_STATE_COMMIT_STEP,
    CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    FROZEN_ADVERSE_EXIT_DISTANCE,
    FROZEN_PROFIT_PROTECTION_DISTANCE,
    OWNER,
    PACKAGE_MARKER,
    POSITION_FLIP_ALLOWED,
    PROFIT_PROTECTION_DISTANCE_CONFIG_OWNER,
    PROFIT_PROTECTION_DISTANCE_REUSES_SWITCH_EVENT_UP_DISTANCE,
)
from src.ops.exit_policy_producer_binding_v1.cycle_harness_v1 import (
    build_capability_evidence_v1,
    prove_deterministic_replay_v1,
    prove_exit_independence_v1,
    prove_exit_state_restart_v1,
    prove_precedence_with_producers_v1,
    run_failure_injections_v1,
    run_producer_unit_matrix_v1,
    run_productive_host_exit_cycles_v1,
)
from src.ops.exit_policy_producer_binding_v1.parity_v1 import prove_trading_logic_parity_v1
from src.ops.exit_policy_producer_binding_v1.producers_v1 import (
    evaluate_adverse_exit_producer_v1,
    evaluate_profit_protection_producer_v1,
    evaluate_strategy_invalidation_producer_v1,
    evaluate_time_exit_producer_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    REQUIRED_CALL_GRAPH,
)

REPO_SHA = "ca2a132adc86b8551c0b87bede0427c198cf3e47"


def test_constants_and_call_graph_bound() -> None:
    assert CAPABILITY_ID.endswith("EXIT_POLICY_PRODUCER_BINDING_V1")
    assert PACKAGE_MARKER.endswith("=true")
    assert CORE_LOGIC_CHANGE is False
    assert POSITION_FLIP_ALLOWED is False
    assert FROZEN_ADVERSE_EXIT_DISTANCE == float(CANONICAL_ADVERSE_EXIT_DISTANCE) == 80.0
    assert FROZEN_PROFIT_PROTECTION_DISTANCE == 200.0
    assert float(CANONICAL_UP_DISTANCE) == 200.0
    assert float(CANONICAL_REVERSAL_DISTANCE) == 120.0
    assert int(CANONICAL_CONFIRMATION_EPOCHS) == 2
    assert PROFIT_PROTECTION_DISTANCE_REUSES_SWITCH_EVENT_UP_DISTANCE is False
    assert PROFIT_PROTECTION_DISTANCE_CONFIG_OWNER == OWNER
    assert CALL_GRAPH_EXIT_PRODUCER_STEP in CALL_GRAPH_AFTER
    assert CALL_GRAPH_EXIT_STATE_COMMIT_STEP in CALL_GRAPH_AFTER
    assert CALL_GRAPH_EXIT_PRODUCER_STEP not in CALL_GRAPH_BEFORE
    # Full CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH is preexisting label-only drift
    # (PREEXISTING_CALL_GRAPH_DRIFT_IN_SCOPE=false). Cap 6.5 proves its steps
    # are present in both graphs; this GO does not repair the label drift.
    assert CALL_GRAPH_EXIT_PRODUCER_STEP in CALL_GRAPH_V1
    assert CALL_GRAPH_EXIT_STATE_COMMIT_STEP in CALL_GRAPH_V1
    assert CALL_GRAPH_EXIT_PRODUCER_STEP in REQUIRED_CALL_GRAPH
    assert CALL_GRAPH_EXIT_STATE_COMMIT_STEP in REQUIRED_CALL_GRAPH
    inv = inventory_exit_policy_authority_v1()
    assert inv["parallel_exit_authority_created"] is False
    assert inv["core_logic_changed"] is False


def test_producer_true_false_evaluations() -> None:
    units = run_producer_unit_matrix_v1()
    assert units["flat_all_false_evaluated"] is True
    assert units["adverse_true"] is True
    assert units["profit_true"] is True
    assert units["time_true"] is True
    assert units["invalidation_true"] is True
    assert units["safety_true"] is True
    assert units["hard_risk_true"] is True
    assert units["all_evaluation_bound"] is True

    adverse_false = evaluate_adverse_exit_producer_v1(
        has_open_position=True,
        existing_position_side="long",
        entry_price=100.0,
        mark_price=100.0,
    )
    assert adverse_false.triggered is False
    assert adverse_false.evaluation_bound is True
    profit_false = evaluate_profit_protection_producer_v1(
        has_open_position=True,
        existing_position_side="long",
        entry_price=100.0,
        mark_price=100.0,
    )
    assert profit_false.triggered is False
    time_false = evaluate_time_exit_producer_v1(
        has_open_position=True,
        entry_event_time=1_700_000_000.0,
        current_event_time=1_700_000_001.0,
        max_hold_seconds=CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
    )
    assert time_false.triggered is False
    inval_false = evaluate_strategy_invalidation_producer_v1(
        has_open_position=True,
        confirmation_assessment_invalid=False,
    )
    assert inval_false.triggered is False


def test_open_long_short_partial_and_flat() -> None:
    long_adverse = evaluate_adverse_exit_producer_v1(
        has_open_position=True,
        existing_position_side="long",
        entry_price=200.0,
        mark_price=200.0 - FROZEN_ADVERSE_EXIT_DISTANCE,
    )
    short_adverse = evaluate_adverse_exit_producer_v1(
        has_open_position=True,
        existing_position_side="short",
        entry_price=200.0,
        mark_price=200.0 + FROZEN_ADVERSE_EXIT_DISTANCE,
    )
    flat = evaluate_adverse_exit_producer_v1(
        has_open_position=False,
        existing_position_side="none",
        entry_price=None,
        mark_price=200.0,
    )
    assert long_adverse.triggered is True
    assert short_adverse.triggered is True
    assert flat.triggered is False
    # Partial: open position still evaluates (no stub).
    partial = evaluate_profit_protection_producer_v1(
        has_open_position=True,
        existing_position_side="long",
        entry_price=100.0,
        mark_price=100.0 + FROZEN_PROFIT_PROTECTION_DISTANCE,
    )
    assert partial.triggered is True


def test_precedence_and_parity() -> None:
    precedence = prove_precedence_with_producers_v1()
    assert precedence["SAFETY_EXIT_PRECEDES_ALPHA"] is True
    assert precedence["HARD_RISK_REDUCE_PRECEDES_ALPHA"] is True
    assert precedence["RECONCILIATION_PRECEDES_ALPHA"] is True
    assert precedence["MANDATORY_EXIT_PRECEDES_NEW_ENTRY"] is True
    assert precedence["POSITION_FLIP_ALLOWED"] is False
    assert precedence["multi_true_tie_break_adverse_over_profit"] is True
    parity = prove_trading_logic_parity_v1()
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True
    assert parity["EFFECTIVE_NUMERIC_VALUES_UNCHANGED"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False


def test_productive_host_binding(tmp_path: Path) -> None:
    out = run_productive_host_exit_cycles_v1(repository_sha=REPO_SHA, work_root=tmp_path / "host")
    assert out["ok"] is True
    assert out["placeholder_false_signal_used_as_unbound_stub"] is False
    assert out["exit_bundle"]["evaluation_bound"] is True


def test_restart_and_duplicate_observation(tmp_path: Path) -> None:
    restart = prove_exit_state_restart_v1(repository_sha=REPO_SHA, work_root=tmp_path / "restart")
    assert restart["EXIT_POLICY_STATE_RESTART_PROVEN"] is True
    assert restart["RUNTIME_RESTART_DOES_NOT_RESET_EXIT_STATE"] is True
    assert restart["NO_LOST_EXIT_TRIGGER"] is True
    assert restart["DUPLICATE_OBSERVATION_DOES_NOT_TRIGGER_NEW_EXIT"] is True
    assert restart["NO_DUPLICATE_EXIT_INTENT"] is True
    assert restart["manifest_verify_rc"] == 0


def test_failure_injection_and_replay(tmp_path: Path) -> None:
    failures = run_failure_injections_v1(repository_sha=REPO_SHA, work_root=tmp_path / "fi")
    assert failures["FAILURE_INJECTION_PROVEN"] is True
    replay = prove_deterministic_replay_v1(repository_sha=REPO_SHA, work_root=tmp_path / "replay")
    assert replay["DETERMINISTIC_REPLAY_PROVEN"] is True
    independence = prove_exit_independence_v1()
    assert independence["EXIT_INDEPENDENCE_PROVEN"] is True
    assert independence["EXIT_PATH_RUNTIME_REACHABLE"] is True


def test_profit_protection_distance_authority_split_from_switch_event_up_distance() -> None:
    repo = Path(__file__).resolve().parents[2]
    constants_path = repo / "src/ops/exit_policy_producer_binding_v1/constants_v1.py"
    constants_src = constants_path.read_text(encoding="utf-8")
    assert "FROZEN_PROFIT_PROTECTION_DISTANCE = float(CANONICAL_UP_DISTANCE)" not in constants_src
    assert "FROZEN_PROFIT_PROTECTION_DISTANCE = 200.0" in constants_src
    imported_names: list[str] = []
    for node in ast.walk(ast.parse(constants_src)):
        if isinstance(node, ast.ImportFrom):
            imported_names.extend(alias.name for alias in node.names)
    assert "CANONICAL_UP_DISTANCE" not in imported_names
    assert "CANONICAL_ADVERSE_EXIT_DISTANCE" in imported_names
    hosts = (
        repo
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        / "decision_economics_cycle_bridge_v1.py",
        repo
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py",
    )
    for host in hosts:
        src = host.read_text(encoding="utf-8")
        assert "profit_protection_distance=float(decision_cfg.up_distance)" not in src
        assert "profit_protection_distance=float(FROZEN_PROFIT_PROTECTION_DISTANCE)" in src
    parity = prove_trading_logic_parity_v1()
    assert parity["frozen_thresholds"]["profit_protection_distance"] == 200.0
    assert parity["frozen_thresholds"]["up_distance"] == 200.0
    assert parity["frozen_thresholds"]["profit_protection_distance_reuses_up_distance"] is False
    profit_rows = [
        row
        for row in inventory_exit_policy_authority_v1()["matrix"]
        if row["EXIT_CLASS"] == "Profit Exit"
    ]
    assert len(profit_rows) == 1
    assert "not Cap 6.3 up_distance" in profit_rows[0]["CONFIG_OWNER"]


def test_capability_evidence_bundle(tmp_path: Path) -> None:
    evidence = build_capability_evidence_v1(
        repository_sha=REPO_SHA, work_root=tmp_path / "evidence"
    )
    payload = evidence.to_dict()
    assert evidence.ok is True
    assert payload["claims"]["EXIT_POLICY_PRODUCERS_BOUND"] is True
    assert payload["claims"]["PLACEHOLDER_FALSE_SIGNAL_USED_AS_UNBOUND_STUB"] is False
    assert payload["claims"]["EXIT_PATH_RUNTIME_REACHABLE"] is True
    assert payload["claims"]["EXIT_INDEPENDENCE_PROVEN"] is True
    assert payload["claims"]["EXIT_END_TO_END_EVIDENCE_PROVEN"] is False
    assert payload["claims"]["EXIT_FILL_OBSERVED"] is False
