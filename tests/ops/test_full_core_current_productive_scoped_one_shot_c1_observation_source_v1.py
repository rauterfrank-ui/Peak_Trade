"""MS01 authority persist, MS02 mapping, and MS03 cursor-floor fail-closed."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY as EG_AUTHORITY_BOUNDARY,
    JOIN_SEAM_ID as EG_JOIN_SEAM_ID,
    REASON_DUPLICATE_C1,
    REASON_LINEAGE_MISMATCH,
    REASON_STALE_C1,
    REASON_UNFINALIZED_C1,
    REQUIRED_BAR,
    CurrentProductiveC1ObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    AUTONOMY_CAN_CHANGE_TRADING_LOGIC,
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    AUTONOMY_CAN_RESELECT_DOWNSTREAM,
    BOUNDED_POLL_AUTHORIZED,
    CADENCE_OWNER_AUTHORIZED,
    CONFIRM_FINALIZED,
    CONTINUOUS_RUNTIME_AUTHORIZED,
    DAEMON_AUTHORIZED,
    DISPOSITION_EMITTED,
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_PRESENT,
    EG_AUTHORITY_BOUNDARY_UNCHANGED,
    JOIN_SEAM_ID,
    LIVE_GET_EXECUTED,
    MS01_IMPLEMENTATION_STATUS,
    MS02_AUTHORIZED,
    MS03_AUTHORIZED,
    MS04_AUTHORIZED,
    MS05_AUTHORIZED,
    OWNER_GO,
    OWNER_GO_SCOPE,
    PERFORM_GET_DEFAULT,
    PRESENCE_ABSENT,
    PRESENCE_PRESENT,
    PRODUCER_AUTHORITY,
    REASON_CURSOR_INVALID,
    REASON_CURSOR_MISSING,
    REASON_OWNER_GO_MISMATCH,
    REASON_UNFINALIZED_OR_ABSENT,
    RUNTIME_CYCLE_AUTHORIZED,
    THIS_SLICE,
    evaluate_current_productive_c1_observation_against_cursor_floor_v1,
    map_injected_candles_payload_to_current_productive_c1_observation_v1,
    resolve_current_productive_c1_cursor_floor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    CURSOR_LINEAGE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_CREATED,
    CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_CREATED,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    TRACKED_CURSOR,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs"
    / "FULL_CORE_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
OWNER_MODULE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_scoped_one_shot_c1_observation_source_v1.py"
)
EG_MODULE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1.py"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
)
EH_HEADING = "### 11.2.1.EH FULL_CORE_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE"
NATIVE_ID = "0G-USDT-SWAP"
OLDER_FINALIZED_TS_S = 1_789_527_720.0
NEWEST_FINALIZED_TS_S = 1_789_527_840.0
CURSOR_C1_FLOOR = 1_789_527_780.0
FORBIDDEN_SOURCE_SNIPPETS = (
    "while True",
    "time.sleep",
    "_evaluate_c1_gate_v1",
    "1789527780",
    "trigger_current_productive_next_c1_and_exactly_one_cycle_v1",
    "execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1",
    "FullCoreProductiveReadOnlyGetTransportV1",
    "execute_network=True",
    'execute_network": True',
    "scheduler",
    "PRODUCTIVE_CONTINUOUS_C1_OBSERVATION_SOURCE_OR_BOUNDED_POLL_OWNER_ABSENT",
)


def _candle_row(*, ts_s: float, confirm: str, close: str = "0.1880") -> list[str]:
    ts_ms = str(int(ts_s * 1000))
    return [ts_ms, close, close, close, close, "10", "100", "USDT", confirm]


def _candles_payload(*rows: list[str]) -> dict[str, object]:
    return {"code": "0", "msg": "", "data": list(rows)}


def test_ms01_created_flag_pins_and_docs() -> None:
    assert CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_CREATED is True
    assert (
        CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_CREATED
        is True
    )
    assert OWNER_GO == ("OWNER_GO_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_V1")
    assert OWNER_GO_SCOPE == "MS01_AUTHORITY_PERSIST_AND_OWNER_PINS_ONLY"
    assert PRODUCER_AUTHORITY == "ONE_SHOT_PUBLIC_1M_C1_OBSERVATION_ACQUISITION_ONLY"
    assert EG_AUTHORITY_BOUNDARY_UNCHANGED == (
        "NEXT_C1_TRIGGER_AND_SINGLE_CYCLE_ORCHESTRATION_ONLY"
    )
    assert EG_AUTHORITY_BOUNDARY == EG_AUTHORITY_BOUNDARY_UNCHANGED
    assert EG_JOIN_SEAM_ID == (
        "CURRENT_PRODUCTIVE_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_SEAM_V1"
    )
    assert MS01_IMPLEMENTATION_STATUS == "AUTHORITY_SCAFFOLD_ONLY"
    assert BOUNDED_POLL_AUTHORIZED is False
    assert DAEMON_AUTHORIZED is False
    assert CADENCE_OWNER_AUTHORIZED is False
    assert CONTINUOUS_RUNTIME_AUTHORIZED is False
    assert RUNTIME_CYCLE_AUTHORIZED is False
    assert PERFORM_GET_DEFAULT is False
    assert LIVE_GET_EXECUTED is False
    assert MS02_AUTHORIZED is False
    assert MS03_AUTHORIZED is False
    assert MS04_AUTHORIZED is False
    assert MS05_AUTHORIZED is False
    assert AUTONOMY_CAN_CHANGE_TRADING_LOGIC is False
    assert AUTONOMY_CAN_RESELECT_DOWNSTREAM is False
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert JOIN_SEAM_ID == ("CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_SEAM_V1")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert EH_HEADING in runbook
    assert THIS_SLICE in runbook
    assert "CURRENT_PHASE=11.2.1.DW.FULL_CORE_POST_SUBMIT_LIFECYCLE_ACTIVATION_AND_JOIN" in runbook
    assert "PRODUCTIVE_CONTINUOUS_C1_OBSERVATION_SOURCE_OR_BOUNDED_POLL_OWNER_ABSENT" not in runbook
    assert "FULL_CORE_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE" in mot
    assert "docs_token:" in spec
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_SCOPED_ONE_SHOT_C1_OBSERVATION_SOURCE_V1"
    ) in spec
    assert JOIN_SEAM_ID in atlas
    assert "MS03_CURSOR_FLOOR=true" in atlas
    assert "MS03_CURSOR_FLOOR_AND_ABSENCE_FAIL_CLOSED" in atlas
    for path in PROTECTED_ALGORITHM_FILES:
        assert (REPO_ROOT / path).is_file()


def test_ms01_source_guards_forbid_successor_and_runtime_surfaces() -> None:
    source = OWNER_MODULE.read_text(encoding="utf-8")
    for snippet in FORBIDDEN_SOURCE_SNIPPETS:
        assert snippet not in source
    assert "MS02 PAYLOAD-TO-OBSERVATION MAPPING" in source
    assert "MS03 CURSOR-FLOOR AND ABSENCE FAIL-CLOSED" in source
    assert "extract_finalized_candle_closes_v1" in source
    assert "def acquire_" not in source
    assert "urllib" not in source
    assert "http.client" not in source
    eg_source = EG_MODULE.read_text(encoding="utf-8")
    assert "while True" not in eg_source
    assert "time.sleep" not in eg_source
    assert 'execute_network": True' not in eg_source
    assert "execute_network = True" not in eg_source


def test_ms02_newest_finalized_confirm_1_maps_exactly_once() -> None:
    payload = _candles_payload(
        _candle_row(ts_s=OLDER_FINALIZED_TS_S, confirm="1"),
        _candle_row(ts_s=NEWEST_FINALIZED_TS_S, confirm="1"),
        _candle_row(ts_s=NEWEST_FINALIZED_TS_S + 60.0, confirm="0"),
    )
    result = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=OWNER_GO,
        candles_payload=payload,
        native_id=NATIVE_ID,
    )
    assert result.disposition == DISPOSITION_EMITTED
    assert result.get_count == 0
    assert result.reason_code == ""
    observation = result.observation
    assert observation is not None
    assert isinstance(observation, CurrentProductiveC1ObservationV1)
    assert observation.venue_event_time == NEWEST_FINALIZED_TS_S
    assert observation.confirm == CONFIRM_FINALIZED
    assert observation.confirm == "1"
    assert observation.native_id == NATIVE_ID
    assert observation.bar == REQUIRED_BAR
    assert observation.bar == "1m"
    assert observation.payload is payload


def test_ms02_multiple_finalized_bars_emit_only_newest() -> None:
    payload = _candles_payload(
        _candle_row(ts_s=NEWEST_FINALIZED_TS_S, confirm="1"),
        _candle_row(ts_s=OLDER_FINALIZED_TS_S, confirm="1"),
        _candle_row(ts_s=OLDER_FINALIZED_TS_S - 60.0, confirm="1"),
    )
    result = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=OWNER_GO,
        candles_payload=payload,
        native_id=NATIVE_ID,
    )
    assert result.disposition == DISPOSITION_EMITTED
    assert result.get_count == 0
    observation = result.observation
    assert observation is not None
    assert observation.venue_event_time == NEWEST_FINALIZED_TS_S
    assert observation.confirm == "1"
    assert observation.payload is payload


def test_ms02_raw_payload_preserved_for_eg_c1_gate_payload() -> None:
    payload = _candles_payload(_candle_row(ts_s=NEWEST_FINALIZED_TS_S, confirm="1"))
    result = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=OWNER_GO,
        candles_payload=payload,
        native_id=NATIVE_ID,
    )
    observation = result.observation
    assert observation is not None
    assert observation.payload is payload
    assert observation.payload == payload
    bound = dict(observation.payload)
    assert bound["code"] == "0"
    assert bound["data"] is payload["data"]
    assert result.get_count == 0


def test_ms02_unfinalized_or_absent_fail_closed_does_not_synthesize() -> None:
    payload = _candles_payload(
        _candle_row(ts_s=NEWEST_FINALIZED_TS_S, confirm="0"),
        _candle_row(ts_s=OLDER_FINALIZED_TS_S, confirm="0"),
    )
    result = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=OWNER_GO,
        candles_payload=payload,
        native_id=NATIVE_ID,
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.observation is None
    assert result.get_count == 0
    assert result.reason_code == REASON_UNFINALIZED_OR_ABSENT


def test_ms02_owner_go_mismatch_fail_closed() -> None:
    payload = _candles_payload(_candle_row(ts_s=NEWEST_FINALIZED_TS_S, confirm="1"))
    result = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go="OWNER_GO_WRONG",
        candles_payload=payload,
        native_id=NATIVE_ID,
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.observation is None
    assert result.get_count == 0
    assert result.reason_code == REASON_OWNER_GO_MISMATCH


def test_ms02_mapping_does_not_get_or_trigger() -> None:
    mapping_source = OWNER_MODULE.read_text(encoding="utf-8")
    mapping_fn = "def map_injected_candles_payload_to_current_productive_c1_observation_v1"
    mapping_start = mapping_source.index(mapping_fn)
    mapping_end = mapping_source.index("class CurrentProductiveScopedOneShotC1CursorFloorResultV1")
    mapping_body = mapping_source[mapping_start:mapping_end]
    assert "cursor_last_accepted_c1_venue_event_time_v1" not in mapping_body
    assert "resolve_current_productive_c1_cursor_floor_v1" not in mapping_body


def _seed_cursor(tmp_path: Path, *, event_time: float = CURSOR_C1_FLOOR) -> Path:
    payload = json.loads(TRACKED_CURSOR.read_text(encoding="utf-8"))
    payload["lineage_id"] = CURSOR_LINEAGE_ID
    payload["venue_native_id"] = NATIVE_ID
    payload["schema_name"] = "current_productive_sidestate_confirmation_cursor.v1"
    payload["cap61_confirmation_state"]["observation_acceptance_state"][
        "last_accepted_observation_identity"
    ]["venue_event_time"] = event_time
    store = tmp_path / "cursor"
    store.mkdir(parents=True, exist_ok=True)
    (store / CURSOR_FILENAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return store


def _observation(
    *,
    venue_event_time: float = NEWEST_FINALIZED_TS_S,
    confirm: str = "1",
    native_id: str = NATIVE_ID,
    bar: str = "1m",
) -> CurrentProductiveC1ObservationV1:
    return CurrentProductiveC1ObservationV1(
        venue_event_time=venue_event_time,
        confirm=confirm,
        native_id=native_id,
        bar=bar,
        payload=_candles_payload(_candle_row(ts_s=venue_event_time, confirm=confirm)),
    )


def test_ms03_present_floor_extracts_last_accepted_venue_event_time(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path)
    result = resolve_current_productive_c1_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=store,
    )
    assert result.disposition == DISPOSITION_PRESENT
    assert result.presence == PRESENCE_PRESENT
    assert result.floor_venue_event_time == CURSOR_C1_FLOOR
    assert result.get_count == 0
    assert result.reason_code == ""


def test_ms03_missing_cursor_fail_closed_does_not_synthesize(tmp_path: Path) -> None:
    empty = tmp_path / "empty-cursor"
    empty.mkdir()
    result = resolve_current_productive_c1_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=empty,
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.presence == PRESENCE_ABSENT
    assert result.floor_venue_event_time is None
    assert result.get_count == 0
    assert result.reason_code == REASON_CURSOR_MISSING


def test_ms03_malformed_cursor_fail_closed(tmp_path: Path) -> None:
    store = tmp_path / "bad-cursor"
    store.mkdir()
    (store / CURSOR_FILENAME).write_text("{not-json", encoding="utf-8")
    result = resolve_current_productive_c1_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=store,
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.presence == ""
    assert result.floor_venue_event_time is None
    assert result.get_count == 0
    assert result.reason_code == REASON_CURSOR_INVALID


def test_ms03_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path)
    payload = json.loads((store / CURSOR_FILENAME).read_text(encoding="utf-8"))
    payload["schema_name"] = "not-the-cursor-schema"
    (store / CURSOR_FILENAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result = resolve_current_productive_c1_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=store,
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.floor_venue_event_time is None
    assert result.get_count == 0
    assert result.reason_code == REASON_CURSOR_INVALID


def test_ms03_missing_last_accepted_identity_fail_closed(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path)
    payload = json.loads((store / CURSOR_FILENAME).read_text(encoding="utf-8"))
    del payload["cap61_confirmation_state"]["observation_acceptance_state"][
        "last_accepted_observation_identity"
    ]
    (store / CURSOR_FILENAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result = resolve_current_productive_c1_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=store,
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.floor_venue_event_time is None
    assert result.get_count == 0
    assert result.reason_code == REASON_CURSOR_INVALID


def test_ms03_owner_go_mismatch_fail_closed(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path)
    result = resolve_current_productive_c1_cursor_floor_v1(
        owner_go="OWNER_GO_WRONG",
        cursor_store_root=store,
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.floor_venue_event_time is None
    assert result.get_count == 0
    assert result.reason_code == REASON_OWNER_GO_MISMATCH


def test_ms03_newer_observation_emits_without_trigger(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path)
    result = evaluate_current_productive_c1_observation_against_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=store,
        observation=_observation(venue_event_time=NEWEST_FINALIZED_TS_S),
    )
    assert result.disposition == DISPOSITION_EMITTED
    assert result.presence == PRESENCE_PRESENT
    assert result.floor_venue_event_time == CURSOR_C1_FLOOR
    assert result.get_count == 0
    assert result.reason_code == ""


def test_ms03_duplicate_observation_fail_closed(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path)
    result = evaluate_current_productive_c1_observation_against_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=store,
        observation=_observation(venue_event_time=CURSOR_C1_FLOOR),
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.presence == PRESENCE_PRESENT
    assert result.floor_venue_event_time == CURSOR_C1_FLOOR
    assert result.get_count == 0
    assert result.reason_code == REASON_DUPLICATE_C1


def test_ms03_stale_observation_fail_closed(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path)
    result = evaluate_current_productive_c1_observation_against_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=store,
        observation=_observation(venue_event_time=OLDER_FINALIZED_TS_S),
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.presence == PRESENCE_PRESENT
    assert result.floor_venue_event_time == CURSOR_C1_FLOOR
    assert result.get_count == 0
    assert result.reason_code == REASON_STALE_C1


def test_ms03_lineage_mismatch_fail_closed(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path)
    result = evaluate_current_productive_c1_observation_against_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=store,
        observation=_observation(native_id="BTC-USDT-SWAP"),
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.get_count == 0
    assert result.reason_code == REASON_LINEAGE_MISMATCH


def test_ms03_unfinalized_observation_fail_closed(tmp_path: Path) -> None:
    store = _seed_cursor(tmp_path)
    result = evaluate_current_productive_c1_observation_against_cursor_floor_v1(
        owner_go=OWNER_GO,
        cursor_store_root=store,
        observation=_observation(confirm="0"),
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.get_count == 0
    assert result.reason_code == REASON_UNFINALIZED_C1


def test_ms03_does_not_start_ms04_get_or_ms05_trigger() -> None:
    source = OWNER_MODULE.read_text(encoding="utf-8")
    assert "load_current_productive_c1_cursor_or_reason_v1" in source
    assert "cursor_last_accepted_c1_venue_event_time_v1" in source
    assert "load_current_productive_sidestate_confirmation_cursor_v1" not in source
    assert "NO_NEW_C1" not in source
    assert "STALE_OBSERVED" not in source
    assert "perform_get" not in source
    assert "injected_get_transport" not in source
    assert "FullCoreFreshPretradeGetTransportV1" not in source
    assert "ENDPOINT_MARKET_CANDLES" not in source
    assert "trigger_current_productive_next_c1_and_exactly_one_cycle_v1" not in source
    assert "_evaluate_c1_gate_v1" not in source
    assert "1789527780" not in source
    assert "execute_network" not in source
    assert "def acquire_" not in source
    assert MS03_AUTHORIZED is False
    assert MS04_AUTHORIZED is False
    assert MS05_AUTHORIZED is False
