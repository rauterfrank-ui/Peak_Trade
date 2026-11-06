"""Capability 7.1 — simulated entry/reduce/exit actionability evidence tests."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_UP_DISTANCE,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.authority_matrix_v1 import (
    inventory_actionability_authority_v1,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.constants_v1 import (
    CALL_GRAPH_V1,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    PACKAGE_MARKER,
    POSITION_FLIP_ALLOWED,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.cycle_harness_v1 import (
    build_capability_evidence_v1,
    prove_duplicate_and_replay_v1,
    run_adverse_exit_v1,
    run_failure_injections_v1,
    run_long_lifecycle_v1,
    run_short_lifecycle_v1,
    run_time_exit_v1,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1 as HOST_CALL_GRAPH,
)

REPO_SHA = "5d09b88c8ee415cc39ddff3cde1ab1348e1147b3"


def test_constants_and_call_graph_bound() -> None:
    assert CAPABILITY_ID.endswith("ACTIONABILITY_EVIDENCE_V1")
    assert PACKAGE_MARKER.endswith("=true")
    assert CORE_LOGIC_CHANGE is False
    assert POSITION_FLIP_ALLOWED is False
    assert float(CANONICAL_ADVERSE_EXIT_DISTANCE) == 80.0
    assert float(CANONICAL_UP_DISTANCE) == 200.0
    assert "analytical_simulated_execution" in CALL_GRAPH_V1
    assert "exit_policy_producer_evaluation" in CALL_GRAPH_V1
    assert all(n in HOST_CALL_GRAPH for n in CALL_GRAPH_V1)
    inv = inventory_actionability_authority_v1()
    assert inv["parallel_decision_authority_created"] is False
    assert inv["forced_intent_allowed"] is False
    assert len(inv["matrix"]) >= 5


def test_long_and_short_lifecycles(tmp_path: Path) -> None:
    long = run_long_lifecycle_v1(repository_sha=REPO_SHA, work_root=tmp_path / "long")
    short = run_short_lifecycle_v1(repository_sha=REPO_SHA, work_root=tmp_path / "short")
    assert long.metrics["entry_fill_count"] > 0
    assert long.metrics["simulated_fill_count"] > 0
    assert Decimal(str(long.metrics["total_fees"])) > 0
    assert Decimal(str(long.metrics["total_slippage"])) > 0
    assert short.claims["ENTRY_FILL_OBSERVED"] is True
    assert short.claims["EXIT_FILL_OBSERVED"] is True


def test_adverse_and_time_exit(tmp_path: Path) -> None:
    adverse = run_adverse_exit_v1(repository_sha=REPO_SHA, work_root=tmp_path / "adverse")
    time_exit = run_time_exit_v1(repository_sha=REPO_SHA, work_root=tmp_path / "time")
    assert adverse.claims["ADVERSE_EXIT_PROVEN"] is True
    assert adverse.claims["EXIT_FILL_OBSERVED"] is True
    assert time_exit.claims["TIME_OR_INVALIDATION_EXIT_PROVEN"] is True
    assert time_exit.claims["EXIT_FILL_OBSERVED"] is True


def test_duplicate_replay_and_failures(tmp_path: Path) -> None:
    dup = prove_duplicate_and_replay_v1(repository_sha=REPO_SHA, work_root=tmp_path / "dup")
    assert dup["DETERMINISTIC_REPLAY_PROVEN"] is True
    assert dup["DUPLICATE_OBSERVATION_NO_NEW_FILL"] is True
    failures = run_failure_injections_v1(repository_sha=REPO_SHA, work_root=tmp_path / "fi")
    assert failures["corrupt_checkpoint_fail_closed"] is True
    assert failures["writer_conflict_hard_stop"] is True
    assert failures["FAILURE_INJECTION_PROVEN"] is True


def test_parity_and_capability_evidence(tmp_path: Path) -> None:
    parity = prove_trading_logic_parity_v1()
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    evidence = build_capability_evidence_v1(
        repository_sha=REPO_SHA, work_root=tmp_path / "evidence"
    )
    payload = evidence.to_dict()
    assert evidence.ok is True
    assert payload["claims"]["ENTRY_END_TO_END_EVIDENCE_PROVEN"] is True
    assert payload["claims"]["EXIT_END_TO_END_EVIDENCE_PROVEN"] is True
    assert payload["claims"]["NONZERO_FEE_EVIDENCE_PROVEN"] is True
    assert payload["claims"]["NONZERO_SLIPPAGE_EVIDENCE_PROVEN"] is True
    assert payload["claims"]["SHORT_LIFECYCLE_PROVEN"] is True
    assert payload["claims"]["NETWORK_SESSION_STARTED"] is False
    assert payload["claims"]["AUTHORIZATION_CONSUMED"] is False
    assert payload["claims"]["POSITION_FLIP_ALLOWED"] is False
