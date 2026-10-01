"""Selection rotation vs persisted sidestate cursor reconciliation (offline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    DISPOSITION_NO_DISPATCH,
    REASON_LINEAGE_MISMATCH,
    evaluate_current_productive_c1_reject_reason_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    RECONCILIATION_NO_PERSISTED_CURSOR,
    RECONCILIATION_SAME_INSTRUMENT_CONTINUATION,
    RECONCILIATION_SELECTION_ROTATION_FRESH_LANE,
    persisted_cursor_venue_native_id_v1,
    reconcile_selection_rotation_with_persisted_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    CURSOR_LINEAGE_ID,
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.current_productive_c1_cycle_test_fixtures_v1 import TRACKED_CURSOR
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _bound,
)
from tests.ops.test_full_core_current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    _observation,
    _seed_cursor,
    _stub_result,
    _trigger,
)

INSTRUMENT_A = "SYNTH-A-USDT-SWAP"
INSTRUMENT_B = "SYNTH-B-USDT-SWAP"
C1_A = 1790880600.0
C1_B = 1790881200.0


def _bound_native(*, native_id: str) -> BoundInstrumentV1:
    base = _bound(lane_id="LANE_1")
    inst = f"inst-{native_id.lower().replace('-', '_')}"
    return base.__class__(
        instrument_id=inst,
        venue_native_id=native_id,
        ranking_snapshot_id=base.ranking_snapshot_id,
        ranking_integrity_digest=base.ranking_integrity_digest,
        universe_snapshot_id=base.universe_snapshot_id,
        selection_id=base.selection_id,
        selection_integrity_digest=base.selection_integrity_digest,
        selection_state=base.selection_state,
    )


def _seed_native_cursor(
    tmp_path: Path,
    *,
    native_id: str,
    event_time: float,
) -> Path:
    payload = json.loads(TRACKED_CURSOR.read_text(encoding="utf-8"))
    payload["lineage_id"] = CURSOR_LINEAGE_ID
    payload["venue_native_id"] = native_id
    payload["instrument_id"] = f"okx_eea:linear_perpetual:{native_id.replace('-SWAP', '')}"
    payload["schema_name"] = "current_productive_sidestate_confirmation_cursor.v1"
    payload["confirmation_epochs"] = 2
    payload["trading_epoch"] = 5
    cap61 = payload["cap61_confirmation_state"]
    cap61["instrument_id"] = payload["instrument_id"]
    oas = cap61["observation_acceptance_state"]
    oas["bound_instrument_key"]["venue_instrument_id"] = native_id
    oas["last_accepted_observation_identity"]["venue_event_time"] = event_time
    oas["last_accepted_observation_identity"]["venue_instrument_id"] = native_id
    store = tmp_path / "lane" / "LANE_1"
    store.mkdir(parents=True, exist_ok=True)
    path = store / CURSOR_FILENAME
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return store


def test_same_instrument_continuation_preserves_cursor(tmp_path: Path) -> None:
    store = _seed_native_cursor(tmp_path, native_id=INSTRUMENT_A, event_time=C1_A)
    before = (store / CURSOR_FILENAME).read_text(encoding="utf-8")
    bound = _bound_native(native_id=INSTRUMENT_A)
    result = reconcile_selection_rotation_with_persisted_cursor_v1(
        cursor_store_root=store,
        bound=bound,
    )
    assert result.action == RECONCILIATION_SAME_INSTRUMENT_CONTINUATION
    assert (store / CURSOR_FILENAME).read_text(encoding="utf-8") == before
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(store)
    assert loaded is not None
    assert persisted_cursor_venue_native_id_v1(loaded) == INSTRUMENT_A
    assert (
        loaded["cap61_confirmation_state"]["observation_acceptance_state"][
            "last_accepted_observation_identity"
        ]["venue_event_time"]
        == C1_A
    )


def test_rotation_archives_a_and_clears_active_cursor(tmp_path: Path) -> None:
    store = _seed_native_cursor(tmp_path, native_id=INSTRUMENT_A, event_time=C1_A)
    bound = _bound_native(native_id=INSTRUMENT_B)
    result = reconcile_selection_rotation_with_persisted_cursor_v1(
        cursor_store_root=store,
        bound=bound,
    )
    assert result.action == RECONCILIATION_SELECTION_ROTATION_FRESH_LANE
    assert result.persisted_native_id == INSTRUMENT_A
    assert result.selected_native_id == INSTRUMENT_B
    assert not (store / CURSOR_FILENAME).is_file()
    archive = Path(result.archived_cursor_path)
    assert archive.is_file()
    archived = json.loads(archive.read_text(encoding="utf-8"))
    assert archived["venue_native_id"] == INSTRUMENT_A
    assert load_current_productive_sidestate_confirmation_cursor_v1(store) is None


def test_no_cursor_reports_neutral_bootstrap_path(tmp_path: Path) -> None:
    store = tmp_path / "lane" / "LANE_1"
    store.mkdir(parents=True)
    bound = _bound_native(native_id=INSTRUMENT_B)
    result = reconcile_selection_rotation_with_persisted_cursor_v1(
        cursor_store_root=store,
        bound=bound,
    )
    assert result.action == RECONCILIATION_NO_PERSISTED_CURSOR
    assert not (store / CURSOR_FILENAME).is_file()


def test_lineage_mismatch_defense_in_depth_unchanged(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path, event_time=C1_A)
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(store)
    assert loaded is not None
    reason = evaluate_current_productive_c1_reject_reason_v1(
        observation=_observation(native_id=INSTRUMENT_B, venue_event_time=C1_B),
        cursor=loaded,
    )
    assert reason == REASON_LINEAGE_MISMATCH

    calls: list[object] = []

    def _dispatch(**kwargs: object) -> object:
        calls.append(kwargs)
        return _stub_result()

    result = _trigger(
        tmp_path,
        _observation(native_id=INSTRUMENT_B, venue_event_time=C1_B),
        cursor_store_root=store,
        cycle_dispatch=_dispatch,
    )
    assert result.disposition == DISPOSITION_NO_DISPATCH
    assert result.reason_code == REASON_LINEAGE_MISMATCH
    assert calls == []


def test_rotation_does_not_relabel_or_copy_a_state_into_active_lane(tmp_path: Path) -> None:
    store = _seed_native_cursor(tmp_path, native_id=INSTRUMENT_A, event_time=C1_A)
    reconcile_selection_rotation_with_persisted_cursor_v1(
        cursor_store_root=store,
        bound=_bound_native(native_id=INSTRUMENT_B),
    )
    active = load_current_productive_sidestate_confirmation_cursor_v1(store)
    assert active is None


def test_selection_authority_remains_bound_b_native_id(tmp_path: Path) -> None:
    bound = _bound_native(native_id=INSTRUMENT_B)
    reconcile_selection_rotation_with_persisted_cursor_v1(
        cursor_store_root=_seed_native_cursor(tmp_path, native_id=INSTRUMENT_A, event_time=C1_A),
        bound=bound,
    )
    assert str(bound.venue_native_id) == INSTRUMENT_B


def test_single_active_future_invariants_unchanged() -> None:
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False


def test_generic_native_ids_not_hardcoded_apr_at(tmp_path: Path) -> None:
    store = _seed_native_cursor(tmp_path, native_id=INSTRUMENT_A, event_time=C1_A)
    result = reconcile_selection_rotation_with_persisted_cursor_v1(
        cursor_store_root=store,
        bound=_bound_native(native_id=INSTRUMENT_B),
    )
    assert INSTRUMENT_A in result.archived_cursor_path
    assert result.selected_native_id == INSTRUMENT_B
