"""Capability 1.1 — productive reconciliation runtime binding tests."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.productive_reconciliation_runtime_binding_v1.classifier_v1 import (
    classify_productive_reconciliation_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    PORTFOLIO_STATE_FILENAME,
    PRODUCTIVE_RECONCILIATION_BOUND,
    SINGLE_WRITER_IDENTITY,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    load_persisted_portfolio_state,
    verify_manifest,
)
from src.ops.productive_reconciliation_runtime_binding_v1.single_writer_v1 import (
    ConflictingWriterError,
    ProductivePortfolioSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
    run_productive_reconciliation_startup_gate_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    CALL_GRAPH_V1,
    run_bridge_cycle_v1,
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    REQUIRED_CALL_GRAPH,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ReconciliationState

REPO_SHA = "5824af75e9c65592b362c935ac707064cfaea099"


def _pos(instrument: str, qty: str | float, *, source: str = "local") -> PositionTruthV1:
    return PositionTruthV1.from_signed(
        instrument_id=instrument,
        signed_quantity=qty,
        source_id=source,
        event_time_unix=1_700_000_000.0,
        wall_time_unix=1_700_000_000.0,
    )


def _snap(
    positions: tuple[PositionTruthV1, ...] = (),
    **kwargs,
) -> PortfolioTruthSnapshotV1:
    return PortfolioTruthSnapshotV1(
        positions=positions,
        event_time_unix=1_700_000_000.0,
        wall_time_unix=1_700_000_000.0,
        **kwargs,
    )


def _seed_persisted(root: Path, positions: tuple[PositionTruthV1, ...]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = _snap(positions, source_id="seed").to_dict()
    (root / PORTFOLIO_STATE_FILENAME).write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def test_constants_bound_not_activated() -> None:
    assert CAPABILITY_ID == "CAPABILITY_1_1_PRODUCTIVE_RECONCILIATION_RUNTIME_BINDING_V1"
    assert PRODUCTIVE_RECONCILIATION_BOUND is True
    assert "productive_reconciliation_startup_gate" in CALL_GRAPH_V1
    assert CALL_GRAPH_V1[0] == "persisted_single_selected_future"
    assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH


def test_no_position_clean_start(tmp_path: Path) -> None:
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap(),
        session_id="s-clean",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert gate.alpha_enabled is True
    assert gate.classification == ProductiveReconciliationClass.MATCH
    assert gate.evidence.pre_state_digest
    assert gate.evidence.observed_state_digest
    assert gate.evidence.post_state_digest
    assert gate.evidence.repository_sha == REPO_SHA
    assert gate.evidence.config_digest
    assert gate.evidence.verification_result.get("ok") is True
    verify_manifest(tmp_path)


def test_matching_open_position(tmp_path: Path) -> None:
    pos = _pos("ETH-USDT-SWAP", "1.5")
    _seed_persisted(tmp_path, (pos,))
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap((_pos("ETH-USDT-SWAP", "1.5", source="observed"),)),
        session_id="s-match",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert gate.classification == ProductiveReconciliationClass.MATCH
    assert gate.alpha_enabled is True


def test_quantity_drift_recoverable_reduce_only(tmp_path: Path) -> None:
    _seed_persisted(tmp_path, (_pos("ETH-USDT-SWAP", "2"),))
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap((_pos("ETH-USDT-SWAP", "1", source="observed"),)),
        session_id="s-qty",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert gate.classification == ProductiveReconciliationClass.RECOVERABLE_DRIFT or (
        gate.alpha_enabled and gate.evidence.recovery_verified
    )
    assert gate.alpha_enabled is True
    assert gate.evidence.recovery_attempted is True
    assert gate.evidence.recovery_verified is True
    assert gate.evidence.mutation_plan.get("admissible") is True
    for step in gate.evidence.mutation_plan.get("steps") or []:
        assert step["reduce_only"] is True
        assert step["opens_new_position"] is False
    reloaded = load_persisted_portfolio_state(tmp_path, require_present=True)
    assert abs(reloaded.positions[0].signed_quantity - Decimal("1")) < Decimal("0.0001")


def test_side_drift_unrecoverable(tmp_path: Path) -> None:
    _seed_persisted(tmp_path, (_pos("ETH-USDT-SWAP", "1"),))
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap((_pos("ETH-USDT-SWAP", "-1", source="observed"),)),
        session_id="s-side",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert gate.classification == ProductiveReconciliationClass.UNRECOVERABLE_DRIFT
    assert gate.alpha_enabled is False
    assert gate.hard_stop is True


def test_missing_truth_hard_stop(tmp_path: Path) -> None:
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap(missing=True),
        session_id="s-miss",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert gate.classification == ProductiveReconciliationClass.MISSING_TRUTH
    assert gate.alpha_enabled is False


def test_unknown_external_position_hard_stop(tmp_path: Path) -> None:
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap((_pos("ETH-USDT-SWAP", "1", source="observed"),)),
        session_id="s-unknown",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert gate.classification == ProductiveReconciliationClass.UNRECOVERABLE_DRIFT
    assert gate.alpha_enabled is False
    assert any("UNKNOWN_EXTERNAL" in r for r in gate.evidence.reason_codes)


def test_stale_snapshot_hard_stop(tmp_path: Path) -> None:
    stale = _snap(stale=True)
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=stale,
        session_id="s-stale",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert gate.classification == ProductiveReconciliationClass.STALE_SOURCE
    assert gate.alpha_enabled is False


def test_stale_by_max_age(tmp_path: Path) -> None:
    observed = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=1_700_000_000.0,
        wall_time_unix=1_700_000_000.0,
        max_age_seconds=10.0,
    )
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=observed,
        session_id="s-maxage",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_100.0,
    )
    assert gate.classification == ProductiveReconciliationClass.STALE_SOURCE
    assert gate.alpha_enabled is False


def test_duplicate_snapshot_hard_stop(tmp_path: Path) -> None:
    _seed_persisted(tmp_path, ())
    (tmp_path / "productive_portfolio_state_v1.copy.json").write_text("{}", encoding="utf-8")
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap(),
        session_id="s-dup",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert gate.classification == ProductiveReconciliationClass.DUPLICATE_STATE
    assert gate.alpha_enabled is False


def test_conflicting_writer_hard_stop(tmp_path: Path) -> None:
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap(),
        session_id="s-conflict",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
        inject_conflicting_writer=True,
    )
    assert gate.classification == ProductiveReconciliationClass.CONFLICTING_WRITER
    assert gate.alpha_enabled is False


def test_single_writer_exclusive_lock(tmp_path: Path) -> None:
    w1 = ProductivePortfolioSingleWriterV1(
        state_root=tmp_path, writer_identity=SINGLE_WRITER_IDENTITY, session_id="a"
    )
    w1.acquire(now_unix=1.0)
    w2 = ProductivePortfolioSingleWriterV1(
        state_root=tmp_path, writer_identity="other", session_id="b"
    )
    with pytest.raises(ConflictingWriterError):
        w2.acquire(now_unix=2.0)
    w1.release()


def test_crash_after_persist_before_verify_blocks_alpha(tmp_path: Path) -> None:
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap(),
        session_id="s-crash",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
        simulate_crash_after_persist_before_verify=True,
    )
    assert gate.alpha_enabled is False
    assert gate.hard_stop is True
    assert "CRASH_AFTER_PERSIST_BEFORE_VERIFY" in gate.blockers
    assert (tmp_path / PORTFOLIO_STATE_FILENAME).is_file()
    assert (tmp_path / EVIDENCE_FILENAME).is_file()


def test_restart_during_recovery_requires_regate(tmp_path: Path) -> None:
    _seed_persisted(tmp_path, (_pos("ETH-USDT-SWAP", "2"),))
    first = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap((_pos("ETH-USDT-SWAP", "1", source="observed"),)),
        session_id="s-restart-1",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert first.alpha_enabled is True
    # Simulate process restart: new gate against persisted repaired state.
    second = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=_snap((_pos("ETH-USDT-SWAP", "1", source="observed"),)),
        session_id="s-restart-2",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_001.0,
    )
    assert second.classification == ProductiveReconciliationClass.MATCH
    assert second.alpha_enabled is True


def test_idempotent_replay_of_match(tmp_path: Path) -> None:
    observed = _snap()
    a = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=observed,
        session_id="s-idemp-1",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    b = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=observed,
        session_id="s-idemp-2",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert a.alpha_enabled and b.alpha_enabled
    assert a.evidence.post_state_digest == b.evidence.post_state_digest


def test_recovery_never_opens_new_position() -> None:
    persisted = _snap()
    observed = _snap((_pos("ETH-USDT-SWAP", "1", source="observed"),))
    classification, plan, reasons = classify_productive_reconciliation_v1(
        persisted=persisted, observed=observed
    )
    assert classification == ProductiveReconciliationClass.UNRECOVERABLE_DRIFT
    assert plan.admissible is False
    assert any("UNKNOWN_EXTERNAL" in r for r in reasons)


def test_bridge_productive_caller_gates_before_alpha(tmp_path: Path) -> None:
    # Cap 1.1 recon proof on the shared bridge host; Cap 2.4 selection binding is
    # proven in test_single_selected_future_runtime_binding_v1 (require_selection_binding).
    state, cycles = run_bridge_cycles_from_mids_v1(
        [3500.0, 3510.0, 3520.0],
        session_id="bridge-recon",
        repository_sha=REPO_SHA,
        reconciliation_state_root=tmp_path,
        require_selection_binding=False,
    )
    assert state.reconciliation_gate_completed is True
    assert state.reconciliation_alpha_enabled is True
    assert state.reconciliation_state is ReconciliationState.RECONCILED
    assert state.portfolio_single_writer_identity == SINGLE_WRITER_IDENTITY
    assert len(cycles) == 3
    assert all("productive_reconciliation_startup_gate" in c.call_graph for c in cycles)
    assert (tmp_path / EVIDENCE_FILENAME).is_file()
    evidence = json.loads((tmp_path / EVIDENCE_FILENAME).read_text(encoding="utf-8"))
    assert evidence["capability_id"] == CAPABILITY_ID
    assert evidence["alpha_enabled"] is True
    assert evidence["repository_sha"] == REPO_SHA
    assert evidence["config_digest"]


def test_bridge_blocks_alpha_on_unrecoverable(tmp_path: Path) -> None:
    _seed_persisted(tmp_path, (_pos("ETH-USDT-SWAP", "1"),))
    state = BridgeSessionStateV1(require_selection_binding=False)
    state.reconciliation_state_root = str(tmp_path)
    # Observed opposite side via poisoned portfolio truth path: inject through gate observed.
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
        ensure_productive_reconciliation_startup_gate_v1,
    )

    gate = ensure_productive_reconciliation_startup_gate_v1(
        state,
        session_id="blocked",
        event_ts_unix=1_700_000_000.0,
        repository_sha=REPO_SHA,
        state_root=tmp_path,
        observed=_snap((_pos("ETH-USDT-SWAP", "-1", source="observed"),)),
    )
    assert gate.alpha_enabled is False
    with pytest.raises(RuntimeError, match="RECONCILIATION_ALPHA_BLOCKED"):
        run_bridge_cycle_v1(
            state,
            mid_price=3500.0,
            event_ts_unix=1_700_000_000.0,
            session_id="blocked",
            repository_sha=REPO_SHA,
            reconciliation_state_root=tmp_path,
        )


def test_bridge_no_longer_hardcodes_reconciled_assumption() -> None:
    src = Path(
        "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
        "decision_economics_cycle_bridge_v1.py"
    ).read_text(encoding="utf-8")
    assert "reconciliation_state=ReconciliationState.RECONCILED" not in src
    assert "reconciliation_state=state.reconciliation_state" in src
    assert "ensure_productive_reconciliation_startup_gate_v1" in src
