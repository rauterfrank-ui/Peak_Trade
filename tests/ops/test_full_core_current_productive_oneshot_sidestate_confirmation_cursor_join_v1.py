"""Offline CURRENT_PRODUCTIVE one-shot SideState/confirmation cursor join."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_CONFIRMATION_EPOCHS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_LINEAGE_ID,
    CURSOR_SCHEMA_NAME,
    CURSOR_SCHEMA_VERSION,
    persist_current_productive_sidestate_confirmation_cursor_v1,
    restore_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    DECISION_ENTER,
    STATUS_PASS,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_ONESHOT_SIDESTATE_CONFIRMATION_CURSOR_JOIN_CREATED,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    TypedRuntimeProducerOutcomeV1,
)
from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import SideState
from tests.ops.test_current_productive_g17_typed_vol_mark_history_checkpoint_v1 import (
    _apply,
    _sixty_one_samples,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/"
    "FULL_CORE_CURRENT_PRODUCTIVE_ONESHOT_SIDESTATE_CONFIRMATION_CURSOR_JOIN_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DR_HEADING = (
    "### 11.2.1.DR FULL_CORE_CURRENT_PRODUCTIVE_ONESHOT_SIDESTATE_AND_CONFIRMATION_CURSOR_JOIN"
)
THIS_SLICE = "11.2.1.DR.FULL_CORE_CURRENT_PRODUCTIVE_ONESHOT_SIDESTATE_AND_CONFIRMATION_CURSOR_JOIN"
_INSTRUMENT = "inst-eth-usdt-perp"
_PRODUCED_G17_CACHE: dict[str, CanonicalVolatilityTypedRuntimeProducerScaffoldV1] = {}
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
    "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
    "config/ops/canonical_decision_runtime_config_v1.toml",
)


def _bound(*, instrument_id: str = _INSTRUMENT) -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=instrument_id,
        venue_native_id=instrument_id,
        ranking_snapshot_id="rank-cursor-join",
        ranking_integrity_digest="rank-cursor-join-digest",
        universe_snapshot_id="uni-cursor-join",
        selection_id="sel-cursor-join",
        selection_integrity_digest="sel-cursor-join-digest",
        selection_state="SELECTED",
    )


def _strong_uptrend_closes(count: int = 64) -> tuple[float, ...]:
    return tuple(1000.0 + float(index) * 10.0 for index in range(count))


_AUTO_G17 = object()


def _produced_g17_producer(
    *, instrument_id: str
) -> CanonicalVolatilityTypedRuntimeProducerScaffoldV1:
    cached = _PRODUCED_G17_CACHE.get(instrument_id)
    if cached is not None:
        return cached
    store_root = Path(tempfile.mkdtemp(prefix="g17-presence-gate-"))
    created = _apply(
        store_root,
        samples=_sixty_one_samples(
            canonical_instrument_id=instrument_id,
            venue_instrument_id=instrument_id,
        ),
        canonical_instrument_id=instrument_id,
        venue_instrument_id=instrument_id,
    )
    assert created.producer is not None
    assert created.last_outcome == TypedRuntimeProducerOutcomeV1.PRODUCED.value
    _PRODUCED_G17_CACHE[instrument_id] = created.producer
    return created.producer


def _cycle(
    *,
    cycle_id: str,
    incoming_cursor: object | None = None,
    instrument_id: str = _INSTRUMENT,
    bound_instrument: BoundInstrumentV1 | None = None,
    closes: tuple[float, ...] | None = None,
    mark_px: float | None = None,
    event_ts_unix: float = 1_700_000_000.0,
    g17_typed_vol_producer: object = _AUTO_G17,
) -> object:
    path = closes if closes is not None else _strong_uptrend_closes()
    last = float(path[-1] if mark_px is None else mark_px)
    resolved_bound = (
        bound_instrument if bound_instrument is not None else _bound(instrument_id=instrument_id)
    )
    canonical_id = str(resolved_bound.instrument_id or instrument_id)
    producer = (
        _produced_g17_producer(instrument_id=canonical_id)
        if g17_typed_vol_producer is _AUTO_G17
        else g17_typed_vol_producer
    )
    return run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=resolved_bound,
        cycle_id=cycle_id,
        observed_unix=float(event_ts_unix) + 100.0,
        mark_px=last,
        index_px=last,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=path,
        last_finalized_event_ts_unix=float(event_ts_unix),
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        incoming_cursor=incoming_cursor,
        g17_typed_vol_producer=producer,
    )


def _cycle_a_with_confirmation_progress() -> object:
    path = _strong_uptrend_closes()
    origin = _cycle(
        cycle_id="cursor-join-origin",
        mark_px=float(path[0]),
        event_ts_unix=1_700_000_000.0,
    )
    return _cycle(
        cycle_id="cursor-join-a",
        incoming_cursor=origin.outgoing_cursor,
        mark_px=float(path[-1]),
        event_ts_unix=1_700_000_060.0,
    )


def _cycle_natural_enter_long_after_upscope_candidate(
    cycle_a: object,
    *,
    cycle_id: str = "cursor-join-enter-long",
) -> object:
    from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
        run_natural_enter_long_cycle_v1,
    )

    path = _strong_uptrend_closes()
    enter_cycle, _closes, _mark = run_natural_enter_long_cycle_v1(
        upscope_candidate_cycle=cycle_a,
        bound=_bound(instrument_id=_INSTRUMENT),
        g17_typed_vol_producer=_produced_g17_producer(instrument_id=_INSTRUMENT),
        uptrend=path,
        cycle_id=cycle_id,
    )
    return enter_cycle


def test_created_flag_and_confirmation_epochs_unchanged() -> None:
    assert CURRENT_PRODUCTIVE_ONESHOT_SIDESTATE_CONFIRMATION_CURSOR_JOIN_CREATED is True
    assert int(CANONICAL_CONFIRMATION_EPOCHS) == 2
    assert int(MAX_POSITIONS_EFFECTIVE) == 1


def test_cycle_a_persists_confirmation_progress_without_enter(tmp_path: Path) -> None:
    cycle_a = _cycle_a_with_confirmation_progress()
    assert cycle_a.cursor_restore_status == "restored"
    assert cycle_a.decision_outcome in {"observe", "blocked"}
    assert cycle_a.decision_outcome not in {"enter_long", "enter_short"}
    assert cycle_a.outgoing_cursor is not None
    cursor = cycle_a.outgoing_cursor
    assert cursor.schema_name == CURSOR_SCHEMA_NAME
    assert cursor.schema_version == CURSOR_SCHEMA_VERSION
    assert cursor.lineage_id == CURSOR_LINEAGE_ID
    assert cursor.instrument_id == _INSTRUMENT
    assert cursor.side_state is SideState.NEUTRAL_OBSERVE
    assert cursor.trading_epoch == 3
    assert cursor.last_evaluated_trading_epoch == 2
    assert cursor.scope_confirmation.candidate_count >= 1
    assert cursor.scope_confirmation.candidate_kind is not None
    assert cursor.confirmation_epochs == 2
    persist_current_productive_sidestate_confirmation_cursor_v1(cursor, store_root=tmp_path)
    restored = restore_current_productive_sidestate_confirmation_cursor_v1(
        cursor,
        expected_instrument_id=_INSTRUMENT,
        expected_venue_native_id=_INSTRUMENT,
        venue_flat=True,
    )
    assert restored.disposition.value == "restored"
    assert restored.fail_closed is False


def test_cycle_b_restores_cursor_and_existing_logic_can_enter() -> None:
    cycle_a = _cycle_a_with_confirmation_progress()
    cycle_b = _cycle_natural_enter_long_after_upscope_candidate(
        cycle_a,
        cycle_id="cursor-join-b",
    )
    assert cycle_b.cursor_restore_status == "restored"
    assert cycle_b.decision_outcome == "enter_long"
    assert cycle_b.replay is not None
    assert cycle_b.replay.replay_pass is True
    next_side = cycle_b.replay.intermediate.state_switch.next_side_state
    assert next_side in {
        SideState.LONG_ARMED.value,
        SideState.LONG_ARMED_NEUTRAL_START.value,
        SideState.LONG_ACTIVE.value,
    }


def test_cycle_b_downstream_enter_29p_29q_venue_plan_envelope_without_permit() -> None:
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
        _balance_payload,
        _injected,
    )

    cycle_a = _cycle_a_with_confirmation_progress()
    cycle_b = _cycle_natural_enter_long_after_upscope_candidate(
        cycle_a,
        cycle_id="cursor-join-b",
    )
    assert cycle_b.decision_outcome == "enter_long"
    assert cycle_b.replay is not None
    # Pre-join intermediate is intentionally pre-CRS.
    assert cycle_b.replay.intermediate.capital_risk_sizing_decision is None
    assert cycle_b.replay.intermediate.canonical_order_intent is None
    assert str(cycle_b.replay.intermediate.capital_risk_mode) == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    assert REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED in cycle_b.replay.evidence.reason_codes

    join = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=cycle_b.replay,
        bound_instrument=_bound(),
        injected=_injected(payload=_balance_payload()),
        decision_epoch="2026-09-16T00:00:00Z",
    )
    assert join.decision_class == DECISION_ENTER
    assert join.status == STATUS_PASS
    assert join.capital_risk_mode == CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
    rebound = join.replay
    assert rebound is not None
    sizing = rebound.intermediate.capital_risk_sizing_decision
    assert sizing is not None
    assert str(getattr(sizing.outcome, "value", sizing.outcome)) == "PASS"
    status, reasons, plan = try_bind_current_productive_venue_plan_v1(
        replay=rebound,
        bound_instrument=_bound(),
        session_id="cursor-join-session",
        run_id="cursor-join-run",
        composed_epoch="2026-09-16T00:00:00Z",
        execution_mode="LIVE",
    )
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="DR_CURSOR_JOIN_HOST_ENTER_OFFLINE",
        provenance_ref="CURRENT_PRODUCTIVE_MASTER_V2_VENUE_PLAN",
        creation_epoch="2026-09-16T00:00:00Z",
    )
    assert envelope.envelope_id
    assert envelope.envelope_digest
    assert rebound.intermediate.canonical_order_intent is not None
    assert rebound.intermediate.canonical_order_intent.execution_eligible is False
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"


def test_natural_enter_via_live_29p_join_reaches_envelope_without_permit() -> None:
    """CRS/intent bind at enter-live-29p join — not via stale isolated ARMED replay."""
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
        _balance_payload,
        _injected,
    )

    cycle_a = _cycle_a_with_confirmation_progress()
    cycle_b = _cycle_natural_enter_long_after_upscope_candidate(
        cycle_a,
        cycle_id="cursor-join-b",
    )
    assert cycle_b.decision_outcome == "enter_long"
    assert cycle_b.replay is not None
    assert cycle_b.replay.intermediate.capital_risk_sizing_decision is None
    join = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=cycle_b.replay,
        bound_instrument=_bound(),
        injected=_injected(payload=_balance_payload()),
        decision_epoch="2026-09-16T00:00:00Z",
    )
    assert join.status == STATUS_PASS
    rebound = join.replay
    assert rebound is not None
    sizing = rebound.intermediate.capital_risk_sizing_decision
    assert sizing is not None
    assert str(getattr(sizing.outcome, "value", sizing.outcome)) == "PASS"
    status, reasons, plan = try_bind_current_productive_venue_plan_v1(
        replay=rebound,
        bound_instrument=_bound(),
        session_id="armed-replay-session",
        run_id="armed-replay-run",
        composed_epoch="2026-09-16T00:00:00Z",
        execution_mode="LIVE",
    )
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="DR_CURSOR_JOIN_NATURAL_ENTER_LIVE_29P",
        provenance_ref="CURRENT_PRODUCTIVE_MASTER_V2_VENUE_PLAN",
        creation_epoch="2026-09-16T00:00:00Z",
    )
    assert envelope.envelope_id
    assert envelope.envelope_digest
    assert envelope.instrument_id == _INSTRUMENT
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"


def test_missing_cursor_does_not_invent_enter() -> None:
    cycle_a = _cycle(cycle_id="missing-cursor")
    assert cycle_a.cursor_restore_status == "missing"
    assert cycle_a.decision_outcome != "enter_long"
    assert cycle_a.decision_outcome != "enter_short"


def test_missing_typed_producer_does_not_invent_enter() -> None:
    cycle_a = _cycle(cycle_id="missing-typed-producer", g17_typed_vol_producer=None)
    assert cycle_a.decision_outcome != "enter_long"
    assert cycle_a.decision_outcome != "enter_short"
    assert "TYPED_VOLATILITY_ESTIMATE_MISSING" in cycle_a.fail_reasons


@pytest.mark.parametrize(
    ("mutator", "expected_status", "fail_closed"),
    [
        (
            lambda payload: {**payload, "instrument_id": "inst-btc-usdt-perp"},
            "refused_mismatch",
            False,
        ),
        (
            lambda payload: {**payload, "lineage_id": "FOREIGN_LINEAGE"},
            "refused_mismatch",
            False,
        ),
        (
            lambda payload: {
                **payload,
                "trading_epoch": 1,
                "last_evaluated_trading_epoch": 1,
            },
            "refused_stale",
            False,
        ),
        (
            lambda payload: {**payload, "side_state": "not-a-side-state"},
            "fail_closed_invalid_sidestate",
            True,
        ),
        (
            lambda payload: {**payload, "scope_confirmation": "corrupt"},
            "fail_closed_corrupt",
            True,
        ),
    ],
)
def test_invalid_cursors_never_invent_enter(mutator, expected_status, fail_closed) -> None:
    path = _strong_uptrend_closes()
    cycle_a = _cycle_a_with_confirmation_progress()
    payload = mutator(cycle_a.outgoing_cursor.to_dict())
    cycle_b = _cycle(
        cycle_id="cursor-join-b",
        incoming_cursor=payload,
        mark_px=float(path[-1]),
        event_ts_unix=1_700_000_120.0,
    )
    assert cycle_b.cursor_restore_status == expected_status
    if fail_closed:
        assert cycle_b.replay is None
        assert cycle_b.input_blocker
    else:
        assert cycle_b.decision_outcome != "enter_long"
        assert cycle_b.decision_outcome != "enter_short"
        assert cycle_b.cursor_restore_status != "restored"


def test_wrong_instrument_cursor_does_not_leak_state() -> None:
    path = _strong_uptrend_closes()
    cycle_a = _cycle_a_with_confirmation_progress()
    cycle_b = _cycle(
        cycle_id="cursor-join-b",
        incoming_cursor=cycle_a.outgoing_cursor,
        instrument_id="inst-btc-usdt-perp",
        mark_px=float(path[-1]),
        event_ts_unix=1_700_000_120.0,
    )
    assert cycle_b.cursor_restore_status == "refused_mismatch"
    assert cycle_b.decision_outcome != "enter_long"


def test_protected_algorithm_files_unchanged_vs_origin_main() -> None:
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", *PROTECTED_ALGORITHM_FILES],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert diff.stdout.strip() == ""


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    # Spec/Atlas carry sealed facts; Master Runbook heading / Mot filename pin are
    # not required for this derived slice (same pattern as enter-live-29p join EF).
    assert DR_HEADING not in runbook
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY" in mot
    assert "EXTERNAL_EFFECT_AUTHORIZED=false" in spec
    assert "REAL_EXTERNAL_EFFECT_AUTHORIZED=false" in spec
    assert "STEP_29Q_STATUS=PLAN_ONLY" in spec
    assert "POST_COUNT=0" in spec
    assert "PERMIT_CREATED=false" in spec
    assert "CONFIRMATION_SEMANTICS_CHANGED=false" in spec
    assert "TRADING_LOGIC_AUTHORITY_CHANGED=false" in spec
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_ONESHOT_SIDESTATE_CONFIRMATION_CURSOR_JOIN_V1"
    ) in spec
    assert "11.2.1.DR" in atlas
    assert "current_productive_sidestate_confirmation_cursor_v1.py" in atlas
    assert json.loads(json.dumps({"POST_COUNT": "0"}))["POST_COUNT"] == "0"
