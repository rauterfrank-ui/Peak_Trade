"""Deterministic regressions for the DPO instrument-and-candle correlation fix."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
    DPO_AMBIGUOUS,
    DPO_BOUND,
    DPO_CURSOR_INCONSISTENT,
    DPO_UNBOUND,
    S5_PRE_EXTERNAL_DISPOSITION,
    evaluate_natural_enter_reporting_v1,
    format_utc_second_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
    INDEX_BASENAME,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.creation_v1 import (
    maybe_create_natural_enter_pending_outcome_v1,
)

DOS = "okx_eea:linear_perpetual:DOS:USDT:USDT:dos-usdt-swap"
DNA = "okx_eea:linear_perpetual:DNA:USDT:USDT:dna-usdt-swap"
STRK = "okx_eea:linear_perpetual:STRK:USDT:USDT:strk-usdt-swap"
W = "okx_eea:linear_perpetual:W:USDT:USDT:w-usdt-swap"
LIVE = "persistent-natural-enter-live-c1:s5:LANE_1:LANE_1"
DOS_ENTER_UNIX = 1_791_832_380.0
STRK_EPOCH9_UNIX = 1_791_828_740.0
PRE = S5_PRE_EXTERNAL_DISPOSITION


@dataclass(frozen=True)
class _Rec:
    cycle_index: int
    s5_disposition: str
    c1_venue_event_time: float | None = None


def _line(
    *,
    instrument_id: str,
    trading_epoch: int,
    decision_outcome: str,
    event_unix: float,
    record_id: str,
    decision_event_ref: str,
    selected_side: str = "none",
) -> str:
    row = {
        "record_type": "double_play_entry_exit_observation",
        "record_id": record_id,
        "payload": {
            "cycle_id": f"{LIVE}:cycle:{trading_epoch}",
            "decision_event_ref": decision_event_ref,
            "event_time_utc": format_utc_second_v1(event_unix),
            "producer_canonical_payload": {
                "instrument_id": instrument_id,
                "trading_epoch": trading_epoch,
                "decision_outcome": decision_outcome,
                "selected_side": selected_side,
                "execution_eligible": False,
            },
        },
    }
    return json.dumps(row, sort_keys=True)


def _write(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "ddo_learning_capture_v1.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _cursor(
    lane: Path,
    *,
    instrument_id: str | None = None,
    last_evaluated: int | None = None,
    trading_epoch: int | None = None,
) -> None:
    payload: dict[str, object] = {}
    if instrument_id is not None:
        payload["instrument_id"] = instrument_id
    if last_evaluated is not None:
        payload["last_evaluated_trading_epoch"] = last_evaluated
    if trading_epoch is not None:
        payload["trading_epoch"] = trading_epoch
    directory = lane / "LANE_1"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current_productive_sidestate_confirmation_cursor_v1.json").write_text(
        json.dumps(payload) + "\n",
        encoding="utf-8",
    )


def _eval(
    ddo: Path,
    *,
    instrument_id: str,
    event_unix: float | None,
    lane: Path | None = None,
    disposition: str = PRE,
):
    record = _Rec(7, disposition, event_unix)
    return evaluate_natural_enter_reporting_v1(
        cycle_records=(record,),
        terminal_disposition=disposition,
        ddo_jsonl=ddo,
        lane_state_root=lane,
        expected_instrument_id=instrument_id,
    )


def test_01_dos_pre_external_enter_long_is_bound(tmp_path: Path) -> None:
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=STRK,
            trading_epoch=9,
            decision_outcome="no_action",
            event_unix=STRK_EPOCH9_UNIX,
            record_id="ddo.dpo:d738cfb09cb65b33f96babd0",
            decision_event_ref="ddo.dec:e5a1e45641829eb46345295e",
        ),
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:bfa8c553f6fae0a74e418bdb",
            decision_event_ref="ddo.dec:f73940c1c7b66fc4d15ba71b",
            selected_side="long",
        ),
    )
    lane = tmp_path / "lane"
    _cursor(lane, instrument_id=DOS, last_evaluated=8, trading_epoch=9)
    result = _eval(ddo, instrument_id=DOS, event_unix=DOS_ENTER_UNIX, lane=lane)
    assert result.correlation_status == DPO_BOUND
    assert result.natural_enter_observed is True
    assert result.natural_pre_external_reached is True
    assert result.enter_side == "LONG"
    assert result.dpo.get("dpo_ref") == "ddo.dpo:bfa8c553f6fae0a74e418bdb"
    assert result.dpo.get("instrument_id") == DOS
    assert result.dpo.get("trading_epoch") == "8"


def test_02_dna_does_not_take_foreign_w_dpo(tmp_path: Path) -> None:
    dna_unix = DOS_ENTER_UNIX + 86_400.0
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=W,
            trading_epoch=8,
            decision_outcome="no_action",
            event_unix=DOS_ENTER_UNIX - 7200,
            record_id="ddo.dpo:w-epoch8",
            decision_event_ref="ddo.dec:w-epoch8",
        ),
        _line(
            instrument_id=DNA,
            trading_epoch=8,
            decision_outcome="no_action",
            event_unix=dna_unix,
            record_id="ddo.dpo:dna-epoch8",
            decision_event_ref="ddo.dec:dna-epoch8",
        ),
    )
    result = _eval(ddo, instrument_id=DNA, event_unix=dna_unix)
    assert result.correlation_status == DPO_BOUND
    assert result.dpo.get("dpo_ref") == "ddo.dpo:dna-epoch8"
    assert result.dpo.get("instrument_id") == DNA
    assert result.natural_enter_observed is False


def test_03_strk_does_not_take_foreign_w_dpo(tmp_path: Path) -> None:
    strk_unix = DOS_ENTER_UNIX - 3600.0
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=W,
            trading_epoch=8,
            decision_outcome="no_action",
            event_unix=DOS_ENTER_UNIX - 7200,
            record_id="ddo.dpo:w-epoch8",
            decision_event_ref="ddo.dec:w-epoch8",
        ),
        _line(
            instrument_id=STRK,
            trading_epoch=8,
            decision_outcome="no_action",
            event_unix=strk_unix,
            record_id="ddo.dpo:strk-epoch8",
            decision_event_ref="ddo.dec:strk-epoch8",
        ),
    )
    result = _eval(ddo, instrument_id=STRK, event_unix=strk_unix)
    assert result.dpo.get("dpo_ref") == "ddo.dpo:strk-epoch8"
    assert result.dpo.get("instrument_id") == STRK


def test_04_rotation_same_epoch_binds_only_reporting_instrument(tmp_path: Path) -> None:
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=W,
            trading_epoch=8,
            decision_outcome="no_action",
            event_unix=DOS_ENTER_UNIX - 5000,
            record_id="ddo.dpo:w8",
            decision_event_ref="ddo.dec:w8",
        ),
        _line(
            instrument_id=STRK,
            trading_epoch=8,
            decision_outcome="no_action",
            event_unix=DOS_ENTER_UNIX - 3000,
            record_id="ddo.dpo:strk8",
            decision_event_ref="ddo.dec:strk8",
        ),
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:dos8",
            decision_event_ref="ddo.dec:dos8",
            selected_side="long",
        ),
        _line(
            instrument_id=DNA,
            trading_epoch=8,
            decision_outcome="no_action",
            event_unix=DOS_ENTER_UNIX + 400_000,
            record_id="ddo.dpo:dna8",
            decision_event_ref="ddo.dec:dna8",
        ),
    )
    result = _eval(ddo, instrument_id=DOS, event_unix=DOS_ENTER_UNIX)
    assert result.dpo.get("dpo_ref") == "ddo.dpo:dos8"
    assert result.natural_enter_observed is True


def test_05_shared_lane_journal_keeps_session_candle(tmp_path: Path) -> None:
    first = DOS_ENTER_UNIX - 10_000.0
    second = DOS_ENTER_UNIX
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="observe",
            event_unix=first,
            record_id="ddo.dpo:dos-earlier-session",
            decision_event_ref="ddo.dec:dos-earlier",
        ),
        _line(
            instrument_id=STRK,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=second - 100,
            record_id="ddo.dpo:strk-shared",
            decision_event_ref="ddo.dec:strk-shared",
            selected_side="long",
        ),
        _line(
            instrument_id=DOS,
            trading_epoch=4,
            decision_outcome="enter_long",
            event_unix=second,
            record_id="ddo.dpo:dos-this-session",
            decision_event_ref="ddo.dec:dos-this",
            selected_side="long",
        ),
    )
    result = _eval(ddo, instrument_id=DOS, event_unix=second)
    assert result.dpo.get("dpo_ref") == "ddo.dpo:dos-this-session"
    assert result.dpo.get("decision_event_ref") == "ddo.dec:dos-this"


def test_06_missing_instrument_identity_is_unbound(tmp_path: Path) -> None:
    raw = json.loads(
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:no-inst",
            decision_event_ref="ddo.dec:no-inst",
            selected_side="long",
        )
    )
    raw["payload"]["producer_canonical_payload"].pop("instrument_id")
    ddo = _write(tmp_path, json.dumps(raw))
    result = _eval(ddo, instrument_id=DOS, event_unix=DOS_ENTER_UNIX)
    assert result.correlation_status == DPO_UNBOUND
    assert result.dpo == {}
    assert result.natural_enter_observed is False


def test_07_missing_candle_time_is_unbound(tmp_path: Path) -> None:
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:dos",
            decision_event_ref="ddo.dec:dos",
            selected_side="long",
        ),
    )
    result = _eval(ddo, instrument_id=DOS, event_unix=None)
    assert result.correlation_status == DPO_UNBOUND
    assert result.natural_enter_observed is False


def test_08_no_matching_dpo_is_unbound(tmp_path: Path) -> None:
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=DOS_ENTER_UNIX - 60,
            record_id="ddo.dpo:other-minute",
            decision_event_ref="ddo.dec:other-minute",
            selected_side="long",
        ),
    )
    result = _eval(ddo, instrument_id=DOS, event_unix=DOS_ENTER_UNIX)
    assert result.correlation_status == DPO_UNBOUND
    assert result.dpo == {}


def test_09_multiple_matching_dpos_are_ambiguous(tmp_path: Path) -> None:
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:one",
            decision_event_ref="ddo.dec:one",
            selected_side="long",
        ),
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="observe",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:two",
            decision_event_ref="ddo.dec:two",
        ),
    )
    result = _eval(ddo, instrument_id=DOS, event_unix=DOS_ENTER_UNIX)
    assert result.correlation_status == DPO_AMBIGUOUS
    assert result.dpo == {}
    assert result.natural_enter_observed is False


def test_10_foreign_enter_long_is_not_adopted(tmp_path: Path) -> None:
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=W,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=DOS_ENTER_UNIX - 120,
            record_id="ddo.dpo:w-enter",
            decision_event_ref="ddo.dec:w-enter",
            selected_side="long",
        ),
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="no_action",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:dos-hold",
            decision_event_ref="ddo.dec:dos-hold",
        ),
    )
    result = _eval(ddo, instrument_id=DOS, event_unix=DOS_ENTER_UNIX)
    assert result.correlation_status == DPO_BOUND
    assert result.dpo.get("dpo_ref") == "ddo.dpo:dos-hold"
    assert result.natural_enter_observed is False
    assert result.dpo.get("instrument_id") == DOS


def test_11_cursor_off_by_one_uses_last_evaluated_not_trading_epoch(tmp_path: Path) -> None:
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:evaluated",
            decision_event_ref="ddo.dec:evaluated",
            selected_side="long",
        ),
        _line(
            instrument_id=STRK,
            trading_epoch=9,
            decision_outcome="no_action",
            event_unix=STRK_EPOCH9_UNIX,
            record_id="ddo.dpo:next-epoch-foreign",
            decision_event_ref="ddo.dec:next-epoch-foreign",
        ),
    )
    lane = tmp_path / "lane"
    _cursor(lane, instrument_id=DOS, last_evaluated=8, trading_epoch=9)
    result = _eval(ddo, instrument_id=DOS, event_unix=DOS_ENTER_UNIX, lane=lane)
    assert result.correlation_status == DPO_BOUND
    assert result.dpo.get("trading_epoch") == "8"
    assert result.dpo.get("dpo_ref") == "ddo.dpo:evaluated"
    mismatched = _write(
        tmp_path / "only_next",
        _line(
            instrument_id=DOS,
            trading_epoch=9,
            decision_outcome="no_action",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:cursor-next",
            decision_event_ref="ddo.dec:cursor-next",
        ),
    )
    rejected = _eval(mismatched, instrument_id=DOS, event_unix=DOS_ENTER_UNIX, lane=lane)
    assert rejected.correlation_status == DPO_CURSOR_INCONSISTENT
    assert rejected.dpo == {}


def test_12_and_14_pending_created_once(tmp_path: Path) -> None:
    ddo = _write(
        tmp_path,
        _line(
            instrument_id=DOS,
            trading_epoch=8,
            decision_outcome="enter_long",
            event_unix=DOS_ENTER_UNIX,
            record_id="ddo.dpo:bfa8c553f6fae0a74e418bdb",
            decision_event_ref="ddo.dec:f73940c1c7b66fc4d15ba71b",
            selected_side="long",
        ),
    )
    lane = tmp_path / "lane"
    _cursor(lane, instrument_id=DOS, last_evaluated=8, trading_epoch=9)
    # The journal the reporter reads is also the lane ledger path used by creation.
    lane_ddo = lane / "LANE_1/ddo_learning_capture_v1.jsonl"
    lane_ddo.write_text(ddo.read_text(encoding="utf-8"), encoding="utf-8")
    reporting = evaluate_natural_enter_reporting_v1(
        cycle_records=(_Rec(7, PRE, DOS_ENTER_UNIX),),
        terminal_disposition=PRE,
        ddo_jsonl=lane_ddo,
        lane_state_root=lane,
        expected_instrument_id=DOS,
    )
    created = maybe_create_natural_enter_pending_outcome_v1(
        lane_state_root=lane,
        reporting=reporting,
        run_id="run-dos",
        evidence_root=tmp_path / "evidence",
        canonical_instrument_id=DOS,
        native_id="DOS-USDT-SWAP",
        decision_timestamp_unix=DOS_ENTER_UNIX,
        decision_reference_price=1.0,
    )
    assert created.created is True
    assert created.reason == "CREATED"
    assert created.record is not None
    assert created.record.canonical_instrument_id == DOS
    assert created.record.decision_event_ref == "ddo.dec:f73940c1c7b66fc4d15ba71b"
    again = maybe_create_natural_enter_pending_outcome_v1(
        lane_state_root=lane,
        reporting=reporting,
        run_id="run-dos-2",
        evidence_root=tmp_path / "evidence-2",
        canonical_instrument_id=DOS,
        native_id="DOS-USDT-SWAP",
        decision_timestamp_unix=DOS_ENTER_UNIX,
        decision_reference_price=1.0,
    )
    assert again.created is False
    assert again.reason == "PENDING_ALREADY_EXISTS"
    assert again.pending_outcome_id == created.pending_outcome_id


def test_13_instrument_mismatch_does_not_mutate_pending_ledger(tmp_path: Path) -> None:
    reporting = evaluate_natural_enter_reporting_v1(
        cycle_records=(_Rec(7, PRE, DOS_ENTER_UNIX),),
        terminal_disposition=PRE,
        ddo_jsonl=_write(
            tmp_path,
            _line(
                instrument_id=STRK,
                trading_epoch=9,
                decision_outcome="enter_long",
                event_unix=DOS_ENTER_UNIX,
                record_id="ddo.dpo:foreign-enter",
                decision_event_ref="ddo.dec:foreign-enter",
                selected_side="long",
            ),
        ),
        expected_instrument_id=STRK,
    )
    assert reporting.natural_enter_observed is True
    lane = tmp_path / "lane"
    (lane / "LANE_1").mkdir(parents=True)
    before = sorted(path.name for path in (lane / "LANE_1").iterdir())
    refused = maybe_create_natural_enter_pending_outcome_v1(
        lane_state_root=lane,
        reporting=reporting,
        run_id="run",
        evidence_root=tmp_path / "evidence",
        canonical_instrument_id=DOS,
        native_id="DOS-USDT-SWAP",
        decision_timestamp_unix=DOS_ENTER_UNIX,
        decision_reference_price=1.0,
    )
    after = sorted(path.name for path in (lane / "LANE_1").iterdir())
    assert refused.created is False
    assert refused.skipped is True
    assert refused.reason == "DPO_INSTRUMENT_MISMATCH"
    assert refused.record is None
    assert INDEX_BASENAME not in after
    assert before == after


def test_15_api3_golden_fixture_compatibility() -> None:
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
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition=str(report["TERMINAL_DISPOSITION"]),
        ddo_jsonl=root / "lane_state/LANE_1/ddo_learning_capture_v1.jsonl",
        lane_state_root=root / "lane_state",
        expected_instrument_id=str(manifest["INSTRUMENT_ID"]),
    )
    assert result.correlation_status == DPO_BOUND
    assert result.natural_enter_observed is True
    assert result.enter_side == "LONG"
    assert result.reporting_s5_cycle_index == 3
    assert result.dpo.get("decision_event_ref") == manifest["ENTER_DECISION_EVENT"]


def test_16_reporter_and_pending_do_not_reach_decision_or_apply_writers() -> None:
    repo = Path(__file__).resolve().parents[2]
    reporter = (
        repo / "scripts/ops/pre_external_convergence_natural_enter_reporting_v1.py"
    ).read_text(encoding="utf-8")
    creation = (
        repo
        / "src/ops/full_core_live_path_composition_root_v1/natural_enter_cross_session_outcome_closure_v1/creation_v1.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "run_integrated_offline_trading_logic_replay_v1",
        "append_apply_ledger_entry_v1",
        "double_play_entry_exit_policy_v0",
    )
    for token in forbidden:
        assert token not in reporter
        assert token not in creation
