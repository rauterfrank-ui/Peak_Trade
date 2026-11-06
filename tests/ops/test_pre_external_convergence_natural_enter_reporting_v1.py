"""Regression tests for PRE_EXTERNAL convergence Natural-Enter reporting correlation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
    S5_PRE_EXTERNAL_DISPOSITION,
    correlate_dpo_to_trading_epoch_v1,
    evaluate_natural_enter_reporting_v1,
    load_productive_live_dpo_observations_v1,
)


@dataclass(frozen=True)
class _Rec:
    cycle_index: int
    s5_disposition: str


def _dpo_line(
    *,
    cycle_id: str,
    trading_epoch: int,
    decision_outcome: str,
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
            "producer_canonical_payload": {
                "decision_outcome": decision_outcome,
                "selected_side": selected_side,
                "execution_eligible": execution_eligible,
                "trading_epoch": trading_epoch,
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
            record_id="ddo.dpo:bootstrap",
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="observe",
            record_id="ddo.dpo:c2",
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:3",
            trading_epoch=3,
            decision_outcome="observe",
            record_id="ddo.dpo:c3",
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:4",
            trading_epoch=4,
            decision_outcome="enter_long",
            selected_side="long",
            execution_eligible=False,
            record_id="ddo.dpo:c4",
            decision_event_ref="ddo.dec:760c2046de67378ee16fdf54",
        ),
    )
    records = (
        _Rec(1, "HOLD_CLOSED"),
        _Rec(2, "HOLD_CLOSED"),
        _Rec(3, S5_PRE_EXTERNAL_DISPOSITION),
    )
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=S5_PRE_EXTERNAL_DISPOSITION,
        ddo_jsonl=ddo,
    )
    assert result.natural_enter_observed is True
    assert result.natural_pre_external_reached is True
    assert result.enter_side == "LONG"
    assert result.reporting_s5_cycle_index == 3
    assert result.dpo.get("decision_outcome") == "enter_long"
    assert result.dpo.get("s5_cycle_index") == "3"


def test_case2_enter_short_on_reporting_cycle(tmp_path: Path) -> None:
    ddo = _write_ddo(
        tmp_path,
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="enter_short",
            selected_side="short",
            record_id="ddo.dpo:short",
        ),
    )
    records = (_Rec(1, S5_PRE_EXTERNAL_DISPOSITION),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=S5_PRE_EXTERNAL_DISPOSITION,
        ddo_jsonl=ddo,
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
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:3",
            trading_epoch=3,
            decision_outcome="observe",
        ),
    )
    records = (
        _Rec(1, "HOLD_CLOSED"),
        _Rec(2, S5_PRE_EXTERNAL_DISPOSITION),
    )
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=S5_PRE_EXTERNAL_DISPOSITION,
        ddo_jsonl=ddo,
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
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="observe",
        ),
    )
    records = (_Rec(1, S5_PRE_EXTERNAL_DISPOSITION),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=S5_PRE_EXTERNAL_DISPOSITION,
        ddo_jsonl=ddo,
    )
    assert result.dpo.get("decision_outcome") == "observe"
    assert result.natural_enter_observed is False


def test_case5_no_productive_enter(tmp_path: Path) -> None:
    ddo = _write_ddo(
        tmp_path,
        _dpo_line(cycle_id=f"{_LIVE}:cycle:2", trading_epoch=2, decision_outcome="observe"),
    )
    records = (_Rec(1, "HOLD_CLOSED"),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition="MAX_CYCLES",
        ddo_jsonl=ddo,
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
        ),
    )
    records = (_Rec(1, "HOLD_CLOSED"),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition="MAX_CYCLES",
        ddo_jsonl=ddo,
    )
    assert result.natural_enter_observed is True
    assert result.natural_pre_external_reached is False


def test_trading_epoch_correlation_prefers_canonical_epoch_over_list_position(
    tmp_path: Path,
) -> None:
    ddo = _write_ddo(
        tmp_path,
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:2",
            trading_epoch=2,
            decision_outcome="no_action",
            record_id="ddo.dpo:old",
        ),
        _dpo_line(
            cycle_id=f"{_LIVE}:cycle:14",
            trading_epoch=14,
            decision_outcome="observe",
            record_id="ddo.dpo:epoch14",
        ),
    )
    lane = tmp_path / "lane"
    (lane / "LANE_1").mkdir(parents=True)
    cursor = {
        "trading_epoch": 14,
        "schema_name": "current_productive_sidestate_confirmation_cursor.v1",
        "schema_version": "v1",
    }
    (lane / "LANE_1/current_productive_sidestate_confirmation_cursor_v1.json").write_text(
        json.dumps(cursor) + "\n",
        encoding="utf-8",
    )
    observations = load_productive_live_dpo_observations_v1(ddo)
    picked = correlate_dpo_to_trading_epoch_v1(observations, trading_epoch=14)
    assert picked is not None
    assert picked.dpo_ref == "ddo.dpo:epoch14"
    records = (_Rec(1, "FAIL_CLOSED"),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition="FAIL_CLOSED",
        ddo_jsonl=ddo,
        lane_state_root=lane,
    )
    assert result.dpo.get("trading_epoch") == "14"
    assert result.dpo.get("dpo_ref") == "ddo.dpo:epoch14"


def test_historical_evidence_rerun_post_7065_without_live_execution() -> None:
    repo = Path(__file__).resolve().parents[2]
    evidence = repo / "evidence/research/natural_enter_rerun_post_7065_v1/20261006T064200Z"
    ddo = evidence / "lane_state/LANE_1/ddo_learning_capture_v1.jsonl"
    report = json.loads(
        (evidence / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text(encoding="utf-8")
    )
    summaries = report.get("S5_CYCLE_SUMMARIES") or []
    records = tuple(
        _Rec(int(item["cycle_index"]), str(item["s5_disposition"])) for item in summaries
    )
    live = load_productive_live_dpo_observations_v1(ddo)
    assert len(live) == 3
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=str(report.get("TERMINAL_DISPOSITION") or ""),
        ddo_jsonl=ddo,
    )
    assert result.natural_enter_observed is True
    assert result.enter_side == "LONG"
    assert result.natural_pre_external_reached is True
    assert result.dpo.get("decision_outcome") == "enter_long"
    assert result.dpo.get("trading_epoch") == "4"
    assert result.reporting_s5_cycle_index == 3
