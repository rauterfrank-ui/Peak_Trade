"""Capability 6.4 — Full decision-path atomic restart closure tests."""

from __future__ import annotations

from pathlib import Path

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_CONFIRMATION_EPOCHS,
    CANONICAL_DECISION_CONFIG_DIGEST,
    CANONICAL_REVERSAL_DISTANCE,
    CANONICAL_UP_DISTANCE,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.authority_inventory_v1 import (
    inventory_decision_path_atomic_authority_v1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.constants_v1 import (
    ATOMICITY_MODEL,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_ATOMIC_COMMIT_STEP,
    CALL_GRAPH_BEFORE,
    CALL_GRAPH_PENDING_EVIDENCE_STEP,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    PACKAGE_MARKER,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.cycle_harness_v1 import (
    build_capability_evidence_v1,
    prove_deterministic_replay_v1,
    prove_restart_decision_path_v1,
    run_failure_injections_v1,
    run_productive_host_atomic_cycles_v1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.state_classification_v1 import (
    classify_fields_by_bucket_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    REQUIRED_CALL_GRAPH,
)

REPO_SHA = "89d0c03f99ad883d0d748f7767db67cc25d83f74"


def test_constants_and_call_graph_bound() -> None:
    assert CAPABILITY_ID.endswith("FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1")
    assert PACKAGE_MARKER.endswith("=true")
    assert CORE_LOGIC_CHANGE is False
    assert ATOMICITY_MODEL == ("VERSIONED_MULTI_RECORD_TRANSACTION_WITH_COMMIT_MARKER_AND_REPLAY")
    assert CALL_GRAPH_ATOMIC_COMMIT_STEP in CALL_GRAPH_AFTER
    assert CALL_GRAPH_PENDING_EVIDENCE_STEP in CALL_GRAPH_AFTER
    assert CALL_GRAPH_ATOMIC_COMMIT_STEP not in CALL_GRAPH_BEFORE
    assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH
    assert CALL_GRAPH_ATOMIC_COMMIT_STEP in CALL_GRAPH_V1
    assert CALL_GRAPH_PENDING_EVIDENCE_STEP in CALL_GRAPH_V1
    assert CANONICAL_CONFIRMATION_EPOCHS == 2
    assert CANONICAL_UP_DISTANCE == 200.0
    assert CANONICAL_ADVERSE_EXIT_DISTANCE == 80.0
    assert CANONICAL_REVERSAL_DISTANCE == 120.0
    assert len(CANONICAL_DECISION_CONFIG_DIGEST) == 64


def test_state_classification_buckets() -> None:
    buckets = classify_fields_by_bucket_v1()
    assert "c1_observation_acceptance_state" in buckets["PERSIST_DIRECTLY"]
    assert "feature_vectors" in buckets["REBUILD_DETERMINISTICALLY"]
    assert "transport_metadata" in buckets["EPHEMERAL_ONLY"]
    assert "capability_evidence_artifacts" in buckets["EVIDENCE_ONLY"]
    assert "master_v2_full_decision_blob" in buckets["FORBIDDEN_TO_PERSIST"]
    inv = inventory_decision_path_atomic_authority_v1()
    assert inv["parallel_state_authority_created"] is False
    assert inv["core_logic_changed"] is False
    assert inv["no_new_parallel_state_model"] is True


def test_parity_contract() -> None:
    parity = prove_trading_logic_parity_v1()
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["CALL_ORDER_PARITY_PROVEN"] is True
    assert parity["INPUT_OUTPUT_PARITY_PROVEN"] is True
    assert parity["STATE_TRANSITION_PARITY_PROVEN"] is True
    assert parity["DECISION_REASON_PARITY_PROVEN"] is True
    assert parity["MASTER_V2_PARITY_PROVEN"] is True
    assert parity["DOUBLE_PLAY_PARITY_PROVEN"] is True
    assert parity["BULL_BEAR_PARITY_PROVEN"] is True
    assert parity["DYNAMIC_SCOPE_RULE_PARITY_PROVEN"] is True
    assert parity["RISK_PARITY_PROVEN"] is True
    assert parity["SAFETY_PARITY_PROVEN"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True
    assert parity["EFFECTIVE_NUMERIC_VALUES_UNCHANGED"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False


def test_productive_host_atomic_cycles(tmp_path: Path) -> None:
    out = run_productive_host_atomic_cycles_v1(
        repository_sha=REPO_SHA,
        work_root=tmp_path / "primary",
    )
    assert out["ok"] is True
    assert out["final_commit_sequence"] >= 1
    assert out["config_digest"] == CANONICAL_DECISION_CONFIG_DIGEST
    assert out["confirmation_session_id"]
    assert out["scope_session_id"]


def test_restart_and_replay(tmp_path: Path) -> None:
    restart = prove_restart_decision_path_v1(
        repository_sha=REPO_SHA,
        work_root=tmp_path / "restart",
    )
    assert restart["ok"] is True
    assert restart["runtime_restart_does_not_reset_trading_state"] is True
    assert restart["digest_match_after_restart"] is True
    assert restart["config_digest_match_after_restart"] is True
    replay = prove_deterministic_replay_v1(
        repository_sha=REPO_SHA,
        work_root=tmp_path / "replay",
    )
    assert replay["ok"] is True
    assert replay["digest_a"] == replay["digest_b"]


def test_failure_injections(tmp_path: Path) -> None:
    failures = run_failure_injections_v1(
        work_root=tmp_path / "failures",
        repository_sha=REPO_SHA,
    )
    assert failures["ok"] is True
    for key in (
        "crash_before_state_write",
        "crash_during_state_write",
        "crash_after_state_before_marker",
        "crash_after_runtime_before_evidence",
        "crash_after_fill_before_portfolio",
        "crash_after_portfolio_before_evidence_cursor",
        "duplicate_replay_after_restart",
        "duplicate_observation_after_restart",
        "restart_during_confirmation_observe",
        "restart_during_candidate",
        "restart_during_confirmed",
        "restart_during_active_dynamic_scope",
        "restart_with_open_simulated_position",
        "corrupt_checkpoint",
        "missing_commit_marker",
        "config_digest_mismatch",
        "repository_sha_mismatch",
        "writer_conflict",
        "evidence_materialization_repeated_fail",
        "recovery_idempotent_restart",
    ):
        assert failures[key]["ok"] is True, key


def test_build_capability_evidence(tmp_path: Path) -> None:
    evidence = build_capability_evidence_v1(
        repository_sha=REPO_SHA,
        work_root=tmp_path / "evidence",
    )
    payload = evidence.to_dict()
    assert evidence.ok is True
    assert payload["ok"] is True
    assert payload["atomicity_model"] == ATOMICITY_MODEL
    assert payload["claims"]["DECISION_PATH_RESTART_PROVEN"] is True
    assert payload["claims"]["EVIDENCE_RECOVERY_IDEMPOTENT"] is True
    assert payload["claims"]["CORE_LOGIC_UNCHANGED"] is True
    assert payload["claims"]["EFFECTIVE_NUMERIC_VALUES_UNCHANGED"] is True
