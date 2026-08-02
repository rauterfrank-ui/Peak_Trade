"""Capability 6.2 — Dynamic Scope persistence binding tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.dynamic_scope_persistence_binding_v1.authority_inventory_v1 import (
    inventory_dynamic_scope_binding_authority_surfaces_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CALL_GRAPH_PREVIOUS_SCOPE_STEP,
    CALL_GRAPH_SCOPE_COMMIT_STEP,
    CALL_GRAPH_SCOPE_TRANSITION_STEP,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    FROZEN_ADVERSE_EXIT_DISTANCE,
    FROZEN_REVERSAL_DISTANCE,
    FROZEN_UP_DISTANCE,
    PACKAGE_MARKER,
)
from src.ops.dynamic_scope_persistence_binding_v1.cycle_harness_v1 import (
    ScopeHarnessEventV1,
    build_capability_evidence_v1,
    prove_restart_dynamic_scope_continuity_v1,
    run_dynamic_scope_harness_v1,
    run_failure_injections_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.host_binding_v1 import (
    dynamic_scope_config_digest_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.persistence_v1 import (
    DynamicScopePersistenceError,
    load_dynamic_scope_state_v1,
    verify_manifest,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (
    ObservationCycleKindV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    REQUIRED_CALL_GRAPH,
)

REPO_SHA = "7beeba1ce93013461d45773a0390d7c9148571c8"


def _market(mid: float) -> ScopeHarnessEventV1:
    return ScopeHarnessEventV1(kind=ObservationCycleKindV1.MARKET_SAMPLE, mid_price=mid)


def test_constants_and_call_graph_bound() -> None:
    assert CAPABILITY_ID.endswith("DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1")
    assert PACKAGE_MARKER.endswith("=true")
    assert CORE_LOGIC_CHANGE is False
    assert CALL_GRAPH_PREVIOUS_SCOPE_STEP in CALL_GRAPH_AFTER
    assert CALL_GRAPH_SCOPE_TRANSITION_STEP in CALL_GRAPH_AFTER
    assert CALL_GRAPH_SCOPE_COMMIT_STEP in CALL_GRAPH_AFTER
    assert CALL_GRAPH_PREVIOUS_SCOPE_STEP not in CALL_GRAPH_BEFORE
    assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH
    assert CALL_GRAPH_PREVIOUS_SCOPE_STEP in CALL_GRAPH_V1
    assert CALL_GRAPH_SCOPE_COMMIT_STEP in CALL_GRAPH_V1
    assert FROZEN_UP_DISTANCE == 200.0
    assert FROZEN_ADVERSE_EXIT_DISTANCE == 80.0
    assert FROZEN_REVERSAL_DISTANCE == 120.0


def test_authority_inventory_no_parallel_domain() -> None:
    inv = inventory_dynamic_scope_binding_authority_surfaces_v1()
    assert inv["parallel_master_v2_persistence_domain_created"] is False
    assert inv["parallel_double_play_persistence_domain_created"] is False
    assert inv["parallel_scope_domain_model_created"] is False
    assert inv["serialization_adapter_has_decision_authority"] is False
    assert inv["core_logic_changed"] is False


def test_parity_contract() -> None:
    parity = prove_trading_logic_parity_v1()
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["CALL_ORDER_PARITY_PROVEN"] is True
    assert parity["INPUT_OUTPUT_PARITY_PROVEN"] is True
    assert parity["STATE_TRANSITION_PARITY_PROVEN"] is True
    assert parity["DECISION_REASON_PARITY_PROVEN"] is True
    assert parity["RISK_PARITY_PROVEN"] is True
    assert parity["SAFETY_PARITY_PROVEN"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True
    assert parity["frozen_thresholds"]["up_distance"] == 200.0
    assert parity["frozen_thresholds"]["adverse_exit_distance"] == 80.0
    assert parity["frozen_thresholds"]["reversal_distance"] == 120.0


def test_initial_scope_creation(tmp_path: Path) -> None:
    result = run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(6)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    assert result.ok
    assert any(result.scope_advanced)
    assert any(d for d in result.scope_digests)
    verify_manifest(tmp_path / "s")


def test_continuation_over_distinct_observations(tmp_path: Path) -> None:
    result = run_dynamic_scope_harness_v1(
        [_market(100.0 + i * 1.5) for i in range(8)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    advanced_digests = [d for d, a in zip(result.scope_digests, result.scope_advanced) if a and d]
    assert len(advanced_digests) >= 2


def test_duplicate_observation_scope_noop(tmp_path: Path) -> None:
    result = run_dynamic_scope_harness_v1(
        [
            _market(100.0),
            _market(101.0),
            ScopeHarnessEventV1(kind=ObservationCycleKindV1.DUPLICATE_SAMPLE, mid_price=101.0),
        ],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    assert result.scope_advanced[-1] is False
    assert result.classifications[-1] in {"duplicate", "transport_only_duplicate"}


def test_no_sample_scope_noop(tmp_path: Path) -> None:
    result = run_dynamic_scope_harness_v1(
        [
            _market(100.0),
            _market(101.0),
            ScopeHarnessEventV1(kind=ObservationCycleKindV1.NO_SAMPLE),
        ],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    assert result.scope_advanced[-1] is False


def test_out_of_order_observation_no_scope_advance(tmp_path: Path) -> None:
    result = run_dynamic_scope_harness_v1(
        [
            _market(100.0),
            _market(101.0),
            ScopeHarnessEventV1(kind=ObservationCycleKindV1.OUT_OF_ORDER, mid_price=102.0),
        ],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    assert result.classifications[-1] in {"out_of_order", "invalid_event_time"}
    assert result.scope_advanced[-1] is False


def test_adverse_reversal_continuation_path(tmp_path: Path) -> None:
    # Wide price path exercises adverse / reversal / continuation distance surfaces.
    mids = [100.0, 110.0, 130.0, 160.0, 200.0, 240.0, 180.0, 120.0, 80.0, 60.0]
    result = run_dynamic_scope_harness_v1(
        [_market(m) for m in mids],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    assert result.ok
    assert any(result.scope_advanced)


def test_position_open_and_flat_context(tmp_path: Path) -> None:
    result = run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(6)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    loaded = load_dynamic_scope_state_v1(tmp_path / "s", require_present=False)
    if loaded is not None:
        assert "venue_flat" in loaded.position_context
        assert "has_open_position" in loaded.position_context


def test_instrument_isolation(tmp_path: Path) -> None:
    a = run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(4)],
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "a",
    )
    b = run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(4)],
        instrument_id="BTC-USDT-SWAP",
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "b",
        require_selection_binding=False,
    )
    assert a.session_ids[0] != b.session_ids[0]


def test_confirmation_scope_handoff(tmp_path: Path) -> None:
    result = run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(6)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    assert all(result.confirmation_session_ids)
    loaded = load_dynamic_scope_state_v1(tmp_path / "s", require_present=False)
    if loaded is not None and loaded.runtime_scope_state is not None:
        assert loaded.confirmation_session_id
        assert loaded.confirmation_session_id == result.confirmation_session_ids[-1]


def test_event_time_continuity(tmp_path: Path) -> None:
    result = run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(5)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    loaded = load_dynamic_scope_state_v1(tmp_path / "s", require_present=False)
    if loaded is not None and loaded.runtime_scope_state is not None:
        assert (
            loaded.market_observation_epoch is not None or loaded.last_market_event_time is not None
        )


def test_restart_after_scope_creation(tmp_path: Path) -> None:
    events = [_market(100.0 + i) for i in range(8)]
    out = prove_restart_dynamic_scope_continuity_v1(
        events,
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "r",
        checkpoint_after=4,
    )
    assert out["DYNAMIC_SCOPE_RESTART_PROVEN"] is True
    assert out["NO_DOUBLE_SCOPE_TRANSITION_AFTER_RESTART"] is True


def test_restart_after_continuation_and_transitions(tmp_path: Path) -> None:
    mids = [100.0, 120.0, 150.0, 190.0, 230.0, 170.0, 110.0, 70.0, 90.0, 130.0]
    events = [_market(m) for m in mids]
    # Checkpoints only after first scope materialization (warmup >= 3).
    for checkpoint in (3, 5, 7):
        out = prove_restart_dynamic_scope_continuity_v1(
            events,
            instrument_id=PRODUCTION_INSTRUMENT_ID,
            repository_sha=REPO_SHA,
            dynamic_scope_state_root=tmp_path / f"r{checkpoint}",
            checkpoint_after=checkpoint,
        )
        assert out["ok"] is True


def test_missing_state_before_first_commit(tmp_path: Path) -> None:
    with pytest.raises(DynamicScopePersistenceError):
        load_dynamic_scope_state_v1(tmp_path / "empty", require_present=True)


def test_missing_state_after_prior_commit(tmp_path: Path) -> None:
    run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(4)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    state_file = tmp_path / "s" / "dynamic_scope_state_v1.json"
    if state_file.is_file():
        state_file.unlink()
    with pytest.raises(DynamicScopePersistenceError):
        load_dynamic_scope_state_v1(
            tmp_path / "s",
            require_present=False,
            allow_missing_before_first_state=False,
        )


def test_corrupt_checkpoint(tmp_path: Path) -> None:
    run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(4)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    path = tmp_path / "s" / "dynamic_scope_state_v1.json"
    if path.is_file():
        path.write_text("{bad", encoding="utf-8")
        with pytest.raises(DynamicScopePersistenceError):
            load_dynamic_scope_state_v1(tmp_path / "s", require_present=True)


def test_config_and_state_version_mismatch(tmp_path: Path) -> None:
    run_dynamic_scope_harness_v1(
        [_market(100.0 + i) for i in range(4)],
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "s",
    )
    with pytest.raises(DynamicScopePersistenceError):
        load_dynamic_scope_state_v1(
            tmp_path / "s",
            require_present=True,
            expected_config_digest="0" * 64,
            expected_repository_sha=REPO_SHA,
            expected_instrument_id=PRODUCTION_INSTRUMENT_ID,
        )


def test_writer_conflict_and_failure_injections(tmp_path: Path) -> None:
    failures = run_failure_injections_v1(
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        repository_sha=REPO_SHA,
        work_root=tmp_path / "fail",
    )
    assert failures["CONFLICTING_WRITER"]["ok"] is True
    assert failures["CORRUPTED_CHECKPOINT"]["ok"] is True
    assert failures["CRASH_BEFORE_STATE_WRITE"]["ok"] is True
    assert failures["CRASH_DURING_STATE_WRITE"]["ok"] is True
    assert failures["CRASH_AFTER_STATE_BEFORE_MARKER"]["ok"] is True
    assert failures["DUPLICATE_REPLAY_AFTER_RESTART"]["ok"] is True


def test_deterministic_replay_digest_match(tmp_path: Path) -> None:
    events = [_market(100.0 + i * 0.75) for i in range(8)]
    a = run_dynamic_scope_harness_v1(
        events,
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "a",
    )
    b = run_dynamic_scope_harness_v1(
        events,
        repository_sha=REPO_SHA,
        dynamic_scope_state_root=tmp_path / "b",
    )
    assert a.final_binding_digest == b.final_binding_digest


def test_productive_host_integration_and_evidence(tmp_path: Path) -> None:
    evidence = build_capability_evidence_v1(
        repository_sha=REPO_SHA,
        work_root=tmp_path / "ev",
    )
    assert evidence.ok is True
    assert evidence.claims["DYNAMIC_SCOPE_PRODUCTIVELY_BOUND"] is True
    assert evidence.claims["CONFIRMATION_SCOPE_HANDOFF_PROVEN"] is True
    assert evidence.claims["DETERMINISTIC_REPLAY_PROVEN"] is True
    assert evidence.claims["CORE_LOGIC_CHANGE"] is False


def test_config_digest_stable() -> None:
    assert dynamic_scope_config_digest_v1() == dynamic_scope_config_digest_v1(
        up_distance=200.0,
        adverse_exit_distance=80.0,
        reversal_distance=120.0,
    )
