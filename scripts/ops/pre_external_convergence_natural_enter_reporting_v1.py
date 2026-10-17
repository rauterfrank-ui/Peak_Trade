"""Natural-Enter accounting for PRE_EXTERNAL convergence reports (reporting-only)."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from src.learning.deterministic_decision_outcome_v0.common_v0 import UTC_EVENT_TIME_RE

PRODUCTIVE_LIVE_C1_DDO_SESSION_MARKER = "persistent-natural-enter-live-c1"
BOOTSTRAP_DDO_SESSION_MARKER = "persistent-natural-enter-bootstrap"
PRODUCTIVE_LANE_ID = "LANE_1"
S5_PRE_EXTERNAL_DISPOSITION = "PRE_EXTERNAL_EFFECT"
_ENTER_OUTCOMES = frozenset({"enter_long", "enter_short"})
CURSOR_FILENAME = "current_productive_sidestate_confirmation_cursor_v1.json"
DPO_BOUND = "DPO_BOUND"
DPO_UNBOUND = "DPO_UNBOUND"
DPO_AMBIGUOUS = "DPO_AMBIGUOUS"
DPO_CURSOR_INCONSISTENT = "DPO_CURSOR_INCONSISTENT"
REPORTING_CYCLE_AMBIGUOUS = "REPORTING_CYCLE_AMBIGUOUS"
_UTC_SECOND_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class _CycleRecordLike(Protocol):
    cycle_index: int
    s5_disposition: str


@dataclass(frozen=True)
class ProductiveDpoObservationV1:
    cycle_id: str
    trading_epoch: int | None
    decision_outcome: str
    selected_side: str
    execution_eligible: str
    decision_event_ref: str
    dpo_ref: str
    s5_cycle_index: int | None
    instrument_id: str
    event_time_utc: str


@dataclass(frozen=True)
class NaturalEnterReportingResultV1:
    reporting_s5_cycle_index: int | None
    reporting_s5_disposition: str
    dpo: dict[str, str]
    natural_enter_observed: bool
    natural_pre_external_reached: bool
    enter_side: str
    correlation_status: str = ""


@dataclass(frozen=True)
class _CursorCorrelationFieldsV1:
    file_present: bool
    parse_ok: bool
    instrument_id: str | None
    last_evaluated_trading_epoch: int | None
    field_invalid: bool


def _utc_second_from_event_time_text_v1(text: str) -> str:
    """Truncate a DDO-contract UTC event time to its second; never rounds."""
    if not UTC_EVENT_TIME_RE.fullmatch(text):
        return ""
    second = text[:19] + "Z"
    try:
        datetime.strptime(second, _UTC_SECOND_FORMAT)
    except ValueError:
        return ""
    return second


def format_utc_second_v1(value: object) -> str:
    """Format a candle instant the same way DPO capture writes event_time_utc."""
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        return _utc_second_from_event_time_text_v1(value.strip())
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return ""
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).strftime(
                _UTC_SECOND_FORMAT
            )
        except (OverflowError, OSError, ValueError):
            return ""
    return ""


def _parse_dpo_row(row: Mapping[str, Any]) -> ProductiveDpoObservationV1 | None:
    if row.get("record_type") != "double_play_entry_exit_observation":
        return None
    payload = row.get("payload")
    if not isinstance(payload, Mapping):
        return None
    cycle_id = str(payload.get("cycle_id") or "").strip()
    if not cycle_id:
        return None
    canon = payload.get("producer_canonical_payload")
    if not isinstance(canon, Mapping):
        canon = {}
    trading_epoch_raw = canon.get("trading_epoch")
    trading_epoch: int | None
    try:
        trading_epoch = int(trading_epoch_raw) if trading_epoch_raw is not None else None
    except (TypeError, ValueError):
        trading_epoch = None
    raw_event_time = payload.get("event_time_utc")
    event_time = (
        _utc_second_from_event_time_text_v1(raw_event_time)
        if isinstance(raw_event_time, str)
        else ""
    )
    return ProductiveDpoObservationV1(
        cycle_id=cycle_id,
        trading_epoch=trading_epoch,
        decision_outcome=str(canon.get("decision_outcome") or "").strip().lower(),
        selected_side=str(canon.get("selected_side") or "").strip().lower(),
        execution_eligible=str(canon.get("execution_eligible") or "").strip().lower(),
        decision_event_ref=str(payload.get("decision_event_ref") or ""),
        dpo_ref=str(row.get("record_id") or payload.get("record_id") or ""),
        s5_cycle_index=None,
        instrument_id=str(canon.get("instrument_id") or "").strip(),
        event_time_utc=event_time,
    )


def is_productive_live_c1_dpo_cycle_id(cycle_id: str) -> bool:
    cid = str(cycle_id or "")
    if BOOTSTRAP_DDO_SESSION_MARKER in cid:
        return False
    if PRODUCTIVE_LIVE_C1_DDO_SESSION_MARKER not in cid:
        return False
    return f":{PRODUCTIVE_LANE_ID}:" in cid


def load_productive_live_dpo_observations_v1(
    ddo_jsonl: Path,
) -> tuple[ProductiveDpoObservationV1, ...]:
    if not ddo_jsonl.is_file():
        return ()
    observations: list[ProductiveDpoObservationV1] = []
    for line in ddo_jsonl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        parsed = _parse_dpo_row(row)
        if parsed is None:
            continue
        if not is_productive_live_c1_dpo_cycle_id(parsed.cycle_id):
            continue
        observations.append(parsed)
    return tuple(observations)


def select_reporting_s5_cycle_record_v1(
    cycle_records: Sequence[_CycleRecordLike],
    *,
    terminal_disposition: str,
) -> _CycleRecordLike | None:
    record, _status = _select_reporting_cycle_v1(
        cycle_records,
        terminal_disposition=terminal_disposition,
    )
    return record


def _select_reporting_cycle_v1(
    cycle_records: Sequence[_CycleRecordLike],
    *,
    terminal_disposition: str,
) -> tuple[_CycleRecordLike | None, str]:
    if not cycle_records:
        return None, DPO_UNBOUND
    if str(terminal_disposition or "") == S5_PRE_EXTERNAL_DISPOSITION:
        matches = [
            record
            for record in cycle_records
            if str(record.s5_disposition or "") == S5_PRE_EXTERNAL_DISPOSITION
        ]
        if len(matches) > 1:
            return None, REPORTING_CYCLE_AMBIGUOUS
        if len(matches) == 1:
            return matches[0], ""
    return cycle_records[-1], ""


def read_lane_trading_epoch_v1(lane_state_root: Path) -> int | None:
    cursor_path = Path(lane_state_root) / PRODUCTIVE_LANE_ID / CURSOR_FILENAME
    if not cursor_path.is_file():
        return None
    try:
        payload = json.loads(cursor_path.read_text(encoding="utf-8"))
        return int(payload["trading_epoch"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def read_lane_cursor_correlation_fields_v1(lane_state_root: Path) -> _CursorCorrelationFieldsV1:
    cursor_path = Path(lane_state_root) / PRODUCTIVE_LANE_ID / CURSOR_FILENAME
    if not cursor_path.is_file():
        return _CursorCorrelationFieldsV1(
            file_present=False,
            parse_ok=True,
            instrument_id=None,
            last_evaluated_trading_epoch=None,
            field_invalid=False,
        )
    try:
        payload = json.loads(cursor_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _CursorCorrelationFieldsV1(
            file_present=True,
            parse_ok=False,
            instrument_id=None,
            last_evaluated_trading_epoch=None,
            field_invalid=True,
        )
    if not isinstance(payload, Mapping):
        return _CursorCorrelationFieldsV1(
            file_present=True,
            parse_ok=False,
            instrument_id=None,
            last_evaluated_trading_epoch=None,
            field_invalid=True,
        )
    instrument: str | None
    if "instrument_id" not in payload:
        instrument = None
    else:
        instrument = str(payload.get("instrument_id") or "").strip() or None
    last_evaluated: int | None
    field_invalid = False
    if "last_evaluated_trading_epoch" not in payload:
        last_evaluated = None
    else:
        raw = payload.get("last_evaluated_trading_epoch")
        if isinstance(raw, bool) or not isinstance(raw, int):
            last_evaluated = None
            field_invalid = True
        else:
            last_evaluated = int(raw)
    return _CursorCorrelationFieldsV1(
        file_present=True,
        parse_ok=True,
        instrument_id=instrument,
        last_evaluated_trading_epoch=last_evaluated,
        field_invalid=field_invalid,
    )


def dpo_observation_to_report_dict_v1(obs: ProductiveDpoObservationV1) -> dict[str, str]:
    return {
        "cycle_id": obs.cycle_id,
        "trading_epoch": "" if obs.trading_epoch is None else str(obs.trading_epoch),
        "s5_cycle_index": "" if obs.s5_cycle_index is None else str(obs.s5_cycle_index),
        "decision_event_ref": obs.decision_event_ref,
        "dpo_ref": obs.dpo_ref,
        "decision_outcome": obs.decision_outcome,
        "selected_side": obs.selected_side,
        "execution_eligible": obs.execution_eligible,
        "instrument_id": obs.instrument_id,
        "event_time_utc": obs.event_time_utc,
    }


def _empty_result(
    *,
    reporting: _CycleRecordLike | None,
    correlation_status: str,
) -> NaturalEnterReportingResultV1:
    if reporting is None:
        return NaturalEnterReportingResultV1(
            reporting_s5_cycle_index=None,
            reporting_s5_disposition="",
            dpo={},
            natural_enter_observed=False,
            natural_pre_external_reached=False,
            enter_side="",
            correlation_status=correlation_status,
        )
    return NaturalEnterReportingResultV1(
        reporting_s5_cycle_index=int(reporting.cycle_index),
        reporting_s5_disposition=str(reporting.s5_disposition or ""),
        dpo={},
        natural_enter_observed=False,
        natural_pre_external_reached=False,
        enter_side="",
        correlation_status=correlation_status,
    )


def _cursor_identity_available_v1(
    cursor: _CursorCorrelationFieldsV1,
    *,
    expected_instrument_id: str,
) -> str:
    """Reject a cursor that cannot be used as an epoch-consistency check."""
    if not cursor.file_present:
        return ""
    if not cursor.parse_ok or cursor.field_invalid:
        return DPO_CURSOR_INCONSISTENT
    has_instrument = cursor.instrument_id is not None
    has_epoch = cursor.last_evaluated_trading_epoch is not None
    if has_instrument != has_epoch:
        return DPO_CURSOR_INCONSISTENT
    if has_instrument and cursor.instrument_id != expected_instrument_id:
        return DPO_CURSOR_INCONSISTENT
    return ""


def _cursor_blocks_match_v1(
    cursor: _CursorCorrelationFieldsV1 | None,
    *,
    expected_instrument_id: str,
    matched_epoch: int | None,
) -> str:
    if cursor is None or not cursor.file_present:
        return ""
    if not cursor.parse_ok or cursor.field_invalid:
        return DPO_CURSOR_INCONSISTENT
    has_instrument = cursor.instrument_id is not None
    has_epoch = cursor.last_evaluated_trading_epoch is not None
    if has_instrument != has_epoch:
        return DPO_CURSOR_INCONSISTENT
    if not has_instrument or not has_epoch:
        return ""
    if cursor.instrument_id != expected_instrument_id:
        return DPO_CURSOR_INCONSISTENT
    if matched_epoch is None or int(matched_epoch) != int(cursor.last_evaluated_trading_epoch):
        return DPO_CURSOR_INCONSISTENT
    return ""


def evaluate_natural_enter_reporting_v1(
    *,
    cycle_records: Sequence[_CycleRecordLike],
    terminal_disposition: str,
    ddo_jsonl: Path,
    lane_state_root: Path | None = None,
    expected_instrument_id: str = "",
) -> NaturalEnterReportingResultV1:
    reporting, select_status = _select_reporting_cycle_v1(
        cycle_records,
        terminal_disposition=terminal_disposition,
    )
    if reporting is None:
        return _empty_result(reporting=None, correlation_status=select_status or DPO_UNBOUND)
    expected_instrument = str(expected_instrument_id or "").strip()
    target_time = format_utc_second_v1(getattr(reporting, "c1_venue_event_time", None))
    if not expected_instrument or not target_time:
        return _empty_result(reporting=reporting, correlation_status=DPO_UNBOUND)
    cursor: _CursorCorrelationFieldsV1 | None = None
    if lane_state_root is not None:
        cursor = read_lane_cursor_correlation_fields_v1(Path(lane_state_root))
        early_status = _cursor_identity_available_v1(
            cursor,
            expected_instrument_id=expected_instrument,
        )
        if early_status:
            return _empty_result(reporting=reporting, correlation_status=early_status)
    observations = load_productive_live_dpo_observations_v1(ddo_jsonl)
    matches = [
        item
        for item in observations
        if item.instrument_id == expected_instrument and item.event_time_utc == target_time
    ]
    if not matches:
        return _empty_result(reporting=reporting, correlation_status=DPO_UNBOUND)
    if len(matches) != 1:
        return _empty_result(reporting=reporting, correlation_status=DPO_AMBIGUOUS)
    chosen = matches[0]
    cursor_status = _cursor_blocks_match_v1(
        cursor,
        expected_instrument_id=expected_instrument,
        matched_epoch=chosen.trading_epoch,
    )
    if cursor_status:
        return _empty_result(reporting=reporting, correlation_status=cursor_status)
    dpo = dpo_observation_to_report_dict_v1(chosen)
    dpo["s5_cycle_index"] = str(int(reporting.cycle_index))
    outcome = chosen.decision_outcome
    natural_enter = outcome in _ENTER_OUTCOMES
    enter_side = ""
    if outcome == "enter_long":
        enter_side = "LONG"
    elif outcome == "enter_short":
        enter_side = "SHORT"
    same_cycle_pre_external = (
        str(reporting.s5_disposition or "") == S5_PRE_EXTERNAL_DISPOSITION and natural_enter
    )
    return NaturalEnterReportingResultV1(
        reporting_s5_cycle_index=int(reporting.cycle_index),
        reporting_s5_disposition=str(reporting.s5_disposition or ""),
        dpo=dpo,
        natural_enter_observed=natural_enter,
        natural_pre_external_reached=same_cycle_pre_external,
        enter_side=enter_side,
        correlation_status=DPO_BOUND,
    )


def extract_productive_dpo_for_pre_external_report_v1(
    lane_state_root: Path,
    *,
    cycle_records: Sequence[_CycleRecordLike],
    terminal_disposition: str,
    expected_instrument_id: str = "",
) -> dict[str, str]:
    ddo = lane_state_root / "LANE_1/ddo_learning_capture_v1.jsonl"
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=cycle_records,
        terminal_disposition=terminal_disposition,
        ddo_jsonl=ddo,
        lane_state_root=lane_state_root,
        expected_instrument_id=expected_instrument_id,
    )
    return dict(result.dpo)
