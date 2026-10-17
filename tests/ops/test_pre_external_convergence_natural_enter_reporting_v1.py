"""Regression tests for PRE_EXTERNAL convergence Natural-Enter reporting correlation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
    DPO_BOUND,
    S5_PRE_EXTERNAL_DISPOSITION,
    evaluate_natural_enter_reporting_v1,
    format_utc_second_v1,
    load_productive_live_dpo_observations_v1,
)

INST = "okx_eea:linear_perpetual:DOS:USDT:USDT:dos-usdt-swap"
T2 = 1_700_000_120.0
T3 = 1_700_000_180.0
T4 = 1_700_000_240.0


@dataclass(frozen=True)
class _Rec:
    cycle_index: int
    s5_disposition: str
    c1_venue_event_time: float | None = None


def _dpo_line(
    *,
    cycle_id: str,
    trading_epoch: int,
    decision_outcome: str,
    event_time_utc: str,
    instrument_id: str = INST,
    selected_side: str = "none",
    execution_eligible: bool = False,
    record_id: str = "ddo.dpo:test",
    decision_event_ref: str = "ddo.dec:test",
) -> str:
    row = {
        "record_type": "double_play_entry_exit_observation",
        "record_id": record_id,
        "payload": {
            "cycle_id": cycle_id,
            "decision_event_ref": decision_event_ref,
            "event_time_utc": event_time_utc,
            "producer_canonical_payload": {
                "decision_outcome": decision_outcome,
                "selected_side": selected_side,
                "execution_eligible": execution_eligible,
                "trading_epoch": trading_epoch,
                "instrument_id": instrument_id,
            },
        },
    }
    return json.dumps(row, sort_keys=True)


def _write_ddo(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "ddo_learning_capture_v1.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


_LIVE = "persistent-natural-enter-live-c1:s5:LANE_1:LANE_1"
_BOOT = "persistent-natural-enter-bootstrap:LANE_1:cycle:1"


def test_case1_historical_regression_shape(tmp_path: Path) -> None:
    ddo = _write_ddo(
        tmp_path,
        _dpo_line(
            cycle_id=f"{_BOOT}",
            trading_epoch=1,
            decision_outcome="no_action",
            event_time_utc=format_utc_second_v1(T2 - 60),
            record_id="ddo.dpo:bootstrap",
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="observe",
            event_time_utc=format_utc_second_v1(T2),
            record_id="ddo.dpo:c2",
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:3",
            trading_epoch=3,
            decision_outcome="observe",
            event_time_utc=format_utc_second_v1(T3),
            record_id="ddo.dpo:c3",
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:4",
            trading_epoch=4,
            decision_outcome="enter_long",
            selected_side="long",
            execution_eligible=False,
            event_time_utc=format_utc_second_v1(T4),
            record_id="ddo.dpo:c4",
            decision_event_ref="ddo.dec:760c2046de67378ee16fdf54",
        ),
    )
    records = (
        _Rec(1, "HOLD_CLOSED", T2),
        _Rec(2, "HOLD_CLOSED", T3),
        _Rec(3, S5_PRE_EXTERNAL_DISPOSITION, T4),
    )
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=S5_PRE_EXTERNAL_DISPOSITION,
        ddo_jsonl=ddo,
        expected_instrument_id=INST,
    )
    assert result.correlation_status == DPO_BOUND
    assert result.natural_enter_observed is True
    assert result.natural_pre_external_reached is True
    assert result.enter_side == "LONG"
    assert result.reporting_s5_cycle_index == 3
    assert result.dpo.get("decision_outcome") == "enter_long"
    assert result.dpo.get("s5_cycle_index") == "3"
    assert result.dpo.get("instrument_id") == INST


def test_case2_enter_short_on_reporting_cycle(tmp_path: Path) -> None:
    ddo = _write_ddo(
        tmp_path,
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="enter_short",
            selected_side="short",
            event_time_utc=format_utc_second_v1(T2),
            record_id="ddo.dpo:short",
        ),
    )
    records = (_Rec(1, S5_PRE_EXTERNAL_DISPOSITION, T2),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=S5_PRE_EXTERNAL_DISPOSITION,
        ddo_jsonl=ddo,
        expected_instrument_id=INST,
    )
    assert result.natural_enter_observed is True
    assert result.enter_side == "SHORT"


def test_case3_do_not_correlate_old_enter_with_later_pre_external(tmp_path: Path) -> None:
    ddo = _write_ddo(
        tmp_path,
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="enter_long",
            selected_side="long",
            event_time_utc=format_utc_second_v1(T2),
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:3",
            trading_epoch=3,
            decision_outcome="observe",
            event_time_utc=format_utc_second_v1(T3),
        ),
    )
    records = (
        _Rec(1, "HOLD_CLOSED", T2),
        _Rec(2, S5_PRE_EXTERNAL_DISPOSITION, T3),
    )
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=S5_PRE_EXTERNAL_DISPOSITION,
        ddo_jsonl=ddo,
        expected_instrument_id=INST,
    )
    assert result.reporting_s5_cycle_index == 2
    assert result.dpo.get("decision_outcome") == "observe"
    assert result.natural_enter_observed is False
    assert result.natural_pre_external_reached is False


def test_case4_bootstrap_enter_ignored(tmp_path: Path) -> None:
    ddo = _write_ddo(
        tmp_path,
        _dpo_line(
            cycle_id=_BOOT,
            trading_epoch=1,
            decision_outcome="enter_long",
            selected_side="long",
            event_time_utc=format_utc_second_v1(T2),
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="observe",
            event_time_utc=format_utc_second_v1(T3),
        ),
    )
    records = (_Rec(1, S5_PRE_EXTERNAL_DISPOSITION, T3),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=S5_PRE_EXTERNAL_DISPOSITION,
        ddo_jsonl=ddo,
        expected_instrument_id=INST,
    )
    assert result.dpo.get("decision_outcome") == "observe"
    assert result.natural_enter_observed is False


def test_case5_no_productive_enter(tmp_path: Path) -> None:
    ddo = _write_ddo(
        tmp_path,
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="observe",
            event_time_utc=format_utc_second_v1(T2),
        ),
    )
    records = (_Rec(1, "HOLD_CLOSED", T2),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition="MAX_CYCLES",
        ddo_jsonl=ddo,
        expected_instrument_id=INST,
    )
    assert result.natural_enter_observed is False
    assert result.natural_pre_external_reached is False


def test_case6_enter_without_pre_external_on_same_cycle(tmp_path: Path) -> None:
    ddo = _write_ddo(
        tmp_path,
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="enter_long",
            selected_side="long",
            event_time_utc=format_utc_second_v1(T2),
        ),
    )
    records = (_Rec(1, "HOLD_CLOSED", T2),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition="MAX_CYCLES",
        ddo_jsonl=ddo,
        expected_instrument_id=INST,
    )
    assert result.natural_enter_observed is True
    assert result.natural_pre_external_reached is False


def test_api3_fixture_binds_by_instrument_and_c1_time() -> None:
    repo = Path(__file__).resolve().parents[2]
    root = repo / "tests/fixtures/current_productive_golden_happy_vector_post_7065_reference_v1"
    manifest = json.loads((root / "golden_vector_manifest_v1.json").read_text(encoding="utf-8"))
    report = json.loads((root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text(encoding="utf-8"))
    records = tuple(
        _Rec(
            int(item["cycle_index"]),
            str(item["s5_disposition"]),
            float(item["c1_venue_event_time"]),
        )
        for item in report["S5_CYCLE_SUMMARIES"]
    )
    ddo = root / "lane_state/LANE_1/ddo_learning_capture_v1.jsonl"
    live = load_productive_live_dpo_observations_v1(ddo)
    assert len(live) == 3
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=str(report.get("TERMINAL_DISPOSITION") or ""),
        ddo_jsonl=ddo,
        lane_state_root=root / "lane_state",
        expected_instrument_id=str(manifest["INSTRUMENT_ID"]),
    )
    assert result.correlation_status == DPO_BOUND
    assert result.natural_enter_observed is True
    assert result.enter_side == "LONG"
    assert result.natural_pre_external_reached is True
    assert result.dpo.get("decision_outcome") == "enter_long"
    assert result.dpo.get("trading_epoch") == "4"
    assert result.reporting_s5_cycle_index == 3
    assert result.dpo.get("instrument_id") == manifest["INSTRUMENT_ID"]
