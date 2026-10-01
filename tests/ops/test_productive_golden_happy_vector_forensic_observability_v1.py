"""Golden Happy Vector forensic observability (signal + entry snapshot)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    RECONCILIATION_NO_PERSISTED_CURSOR,
    RECONCILIATION_SELECTION_ROTATION_FRESH_LANE,
    RECONCILIATION_SAME_INSTRUMENT_CONTINUATION,
    SelectionRotationCursorReconciliationV1,
    reconcile_selection_rotation_with_persisted_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
    DIRECTIONAL_SIGNAL_LEDGER_FILENAME,
    ENTRY_STATE_SNAPSHOT_FILENAME,
    GoldenHappyVectorForensicObservabilityError,
    GoldenHappyVectorForensicObservabilitySessionV1,
    MISSING_BY_DESIGN_AFTER_ROTATION,
    OBSERVABILITY_DEFAULT_ENABLED,
    append_directional_signal_observability_v1,
    bind_golden_happy_vector_forensic_observability_session_v1,
    build_directional_signal_observability_record_v1,
    persist_continuous_run_entry_state_snapshot_v1,
    reset_golden_happy_vector_forensic_observability_session_v1,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _bound,
)
from tests.trading.master_v2.test_directional_assessment_confirmation_integration_v1 import (
    _candidate,
    _carrier,
    _eval_c1,
    _key,
    _policy,
    _progress_side,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)
from trading.market_state.directional_confirmation_progress_v1 import ConfirmationSideV1
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    initial_observation_acceptance_state_v1,
)
from trading.master_v2.directional_assessment_v1 import compute_signal_strength
from tests.ops.test_full_core_current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    _seed_cursor,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)


def test_observability_default_disabled() -> None:
    assert OBSERVABILITY_DEFAULT_ENABLED is False


def test_default_off_no_evidence_files(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    assert not (evidence / DIRECTIONAL_SIGNAL_LEDGER_FILENAME).exists()
    assert not (evidence / ENTRY_STATE_SNAPSHOT_FILENAME).exists()
    c1_state = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    acceptor, _ = _eval_c1(c1_state, _candidate(event_time=1.0, mark=3500.0))
    c3 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=_carrier(),
        acceptor=acceptor,
        price_path=(3500.0, 3550.0),
    )
    assert (
        append_directional_signal_observability_v1(
            c3_result=c3,
            policy=_policy(),
            observation_acceptance_result=acceptor,
            instrument_id="ETH-USD-SWAP-CANON",
            side="LONG",
        )
        is None
    )


def test_signal_capture_persists_runtime_signal_strength(tmp_path: Path) -> None:
    policy = _policy()
    c1_state = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    obs, _ = _eval_c1(c1_state, _candidate(event_time=1.0, mark=3500.0))
    c3 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=_carrier(),
        acceptor=obs,
        price_path=(3500.0, 3550.0),
        policy=policy,
    )
    session = GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=tmp_path,
        run_id="run-1",
        continuous_run_id="run-1",
    )
    token = bind_golden_happy_vector_forensic_observability_session_v1(session)
    try:
        with patch(
            "trading.master_v2.directional_assessment_v1.compute_signal_strength",
            side_effect=AssertionError("SIGNAL_RECOMPUTE_FORBIDDEN"),
        ):
            append_directional_signal_observability_v1(
                c3_result=c3,
                policy=policy,
                observation_acceptance_result=obs,
                instrument_id="BTC-USDT-SWAP",
                side="LONG",
            )
    finally:
        reset_golden_happy_vector_forensic_observability_session_v1(token)
    lines = (tmp_path / DIRECTIONAL_SIGNAL_LEDGER_FILENAME).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["signal_strength"] == c3.assessment.signal_strength
    assert row["candidate_threshold_met"] == (
        float(c3.assessment.signal_strength) >= float(policy.candidate_signal_threshold)
    )
    assert row["confirmation_threshold_met"] == (
        float(c3.assessment.signal_strength) >= float(policy.confirmation_signal_threshold)
    )
    assert row["assessment_signal"] == c3.assessment_signal.value


def test_threshold_flags_match_same_strength_and_policy() -> None:
    policy = _policy()
    c1_state = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    obs, _ = _eval_c1(c1_state, _candidate(event_time=1.0, mark=3500.0))
    c3 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=_carrier(),
        acceptor=obs,
        price_path=(3500.0, 3550.0),
        policy=policy,
    )
    record = build_directional_signal_observability_record_v1(
        session=GoldenHappyVectorForensicObservabilitySessionV1(
            enabled=True,
            product_evidence_root=Path("/tmp/unused"),
            run_id="r",
            continuous_run_id="r",
        ),
        c3_result=c3,
        policy=policy,
        observation_acceptance_result=obs,
        instrument_id="ETH-USD-SWAP-CANON",
        side="LONG",
    )
    strength = float(c3.assessment.signal_strength)
    assert record["candidate_threshold_met"] is (
        strength >= float(policy.candidate_signal_threshold)
    )
    assert record["confirmation_threshold_met"] is (
        strength >= float(policy.confirmation_signal_threshold)
    )


def test_replay_decision_identity_with_and_without_observability_hook() -> None:
    inp = _replay_input()
    baseline = run_integrated_offline_trading_logic_replay_v1(inp)
    session = GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=Path("/tmp/unused"),
        run_id="run-x",
        continuous_run_id="run-x",
    )
    token = bind_golden_happy_vector_forensic_observability_session_v1(session)
    try:
        with patch(
            "src.ops.full_core_live_path_composition_root_v1."
            "productive_golden_happy_vector_forensic_observability_v1._append_jsonl_v1"
        ):
            observed = run_integrated_offline_trading_logic_replay_v1(inp)
    finally:
        reset_golden_happy_vector_forensic_observability_session_v1(token)
    assert observed.evidence.decision_outcome == baseline.evidence.decision_outcome
    assert observed.replay_pass == baseline.replay_pass
    assert observed.fail_reasons == baseline.fail_reasons


def test_entry_snapshot_written_once(tmp_path: Path) -> None:
    bound = _bound(lane_id="LANE_1")
    session = GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=tmp_path,
        run_id="run-1",
        continuous_run_id="run-1",
    )
    reconciliation = SelectionRotationCursorReconciliationV1(
        action=RECONCILIATION_NO_PERSISTED_CURSOR,
        persisted_native_id="",
        selected_native_id=str(bound.venue_native_id),
    )
    persist_continuous_run_entry_state_snapshot_v1(
        session=session,
        bound=bound,
        reconciliation=reconciliation,
        cursor_store_root=tmp_path / "cursor",
        expected_cursor_floor=0.0,
    )
    with pytest.raises(GoldenHappyVectorForensicObservabilityError):
        persist_continuous_run_entry_state_snapshot_v1(
            session=session,
            bound=bound,
            reconciliation=reconciliation,
            cursor_store_root=tmp_path / "cursor",
            expected_cursor_floor=0.0,
        )


def test_entry_snapshot_rotation_missing_by_design(tmp_path: Path) -> None:
    bound = _bound(lane_id="LANE_1")
    session = GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=tmp_path,
        run_id="run-rot",
        continuous_run_id="run-rot",
    )
    reconciliation = SelectionRotationCursorReconciliationV1(
        action=RECONCILIATION_SELECTION_ROTATION_FRESH_LANE,
        persisted_native_id="OLD-USDT-SWAP",
        selected_native_id=str(bound.venue_native_id),
        archived_cursor_path=str(tmp_path / "archived.json"),
    )
    persist_continuous_run_entry_state_snapshot_v1(
        session=session,
        bound=bound,
        reconciliation=reconciliation,
        cursor_store_root=tmp_path / "cursor",
        expected_cursor_floor=0.0,
    )
    payload = json.loads((tmp_path / ENTRY_STATE_SNAPSHOT_FILENAME).read_text(encoding="utf-8"))
    carrier = payload["entry_confirmation_and_sidestate_carrier"]
    assert carrier["present"] is False
    assert carrier["reason"] == MISSING_BY_DESIGN_AFTER_ROTATION
    assert payload["rotation_reconciliation"]["rotation_performed"] is True


def test_entry_snapshot_same_instrument_reads_persisted_cursor(tmp_path: Path) -> None:
    bound = _bound(lane_id="LANE_1")
    cursor_root = _seed_cursor(tmp_path)
    reconciliation = SelectionRotationCursorReconciliationV1(
        action=RECONCILIATION_SAME_INSTRUMENT_CONTINUATION,
        persisted_native_id=str(bound.venue_native_id),
        selected_native_id=str(bound.venue_native_id),
    )
    session = GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=tmp_path,
        run_id="run-same",
        continuous_run_id="run-same",
    )
    persist_continuous_run_entry_state_snapshot_v1(
        session=session,
        bound=bound,
        reconciliation=reconciliation,
        cursor_store_root=cursor_root,
        expected_cursor_floor=1.0,
    )
    payload = json.loads((tmp_path / ENTRY_STATE_SNAPSHOT_FILENAME).read_text(encoding="utf-8"))
    assert payload["entry_confirmation_and_sidestate_carrier"]["present"] is True
    assert (cursor_root / CURSOR_FILENAME).is_file()


def test_rotation_reconciliation_archives_cursor(tmp_path: Path) -> None:
    bound_old = _bound(lane_id="LANE_1")
    bound_new = replace(bound_old, venue_native_id="NEW-USDT-SWAP")
    cursor_root = _seed_cursor(tmp_path)
    payload = json.loads((cursor_root / CURSOR_FILENAME).read_text(encoding="utf-8"))
    payload["venue_native_id"] = "OLD-USDT-SWAP"
    (cursor_root / CURSOR_FILENAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = reconcile_selection_rotation_with_persisted_cursor_v1(
        cursor_store_root=cursor_root,
        bound=bound_new,
    )
    assert result.action == RECONCILIATION_SELECTION_ROTATION_FRESH_LANE
    assert result.archived_cursor_path
    assert not (cursor_root / CURSOR_FILENAME).is_file()


def test_post_and_external_effect_authority_unchanged() -> None:
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_compute_signal_strength_still_used_in_c3_path() -> None:
    c1_state = initial_observation_acceptance_state_v1(bound_instrument_key=_key())
    obs, _ = _eval_c1(c1_state, _candidate(event_time=1.0, mark=3500.0))
    c3 = _progress_side(
        side=ConfirmationSideV1.LONG,
        prior_carrier=_carrier(),
        acceptor=obs,
        price_path=(3500.0, 3550.0),
    )
    expected = compute_signal_strength(
        price_path=(3500.0, 3550.0),
        side=c3.assessment.side,
        reference_price=3500.0,
    )
    assert c3.assessment.signal_strength == expected
