"""Natural-Enter accounting for PRE_EXTERNAL convergence reports (reporting-only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

PRODUCTIVE_LIVE_C1_DDO_SESSION_MARKER = "persistent-natural-enter-live-c1"
BOOTSTRAP_DDO_SESSION_MARKER = "persistent-natural-enter-bootstrap"
PRODUCTIVE_LANE_ID = "LANE_1"
S5_PRE_EXTERNAL_DISPOSITION = "PRE_EXTERNAL_EFFECT"
_ENTER_OUTCOMES = frozenset({"enter_long", "enter_short"})


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


@dataclass(frozen=True)
class NaturalEnterReportingResultV1:
    reporting_s5_cycle_index: int | None
    reporting_s5_disposition: str
    dpo: dict[str, str]
    natural_enter_observed: bool
    natural_pre_external_reached: bool
    enter_side: str


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
    return ProductiveDpoObservationV1(
        cycle_id=cycle_id,
        trading_epoch=trading_epoch,
        decision_outcome=str(canon.get("decision_outcome") or "").strip().lower(),
        selected_side=str(canon.get("selected_side") or "").strip().lower(),
        execution_eligible=str(canon.get("execution_eligible") or "").strip().lower(),
        decision_event_ref=str(payload.get("decision_event_ref") or ""),
        dpo_ref=str(row.get("record_id") or payload.get("record_id") or ""),
        s5_cycle_index=None,
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

    def _sort_key(item: ProductiveDpoObservationV1) -> tuple[int, str]:
        if item.trading_epoch is not None:
            return (item.trading_epoch, item.cycle_id)
        suffix = item.cycle_id.rsplit(":cycle:", 1)[-1]
        try:
            return (int(suffix), item.cycle_id)
        except ValueError:
            return (0, item.cycle_id)

    ordered = sorted(observations, key=_sort_key)
    correlated: list[ProductiveDpoObservationV1] = []
    for index, item in enumerate(ordered, start=1):
        correlated.append(
            ProductiveDpoObservationV1(
                cycle_id=item.cycle_id,
                trading_epoch=item.trading_epoch,
                decision_outcome=item.decision_outcome,
                selected_side=item.selected_side,
                execution_eligible=item.execution_eligible,
                decision_event_ref=item.decision_event_ref,
                dpo_ref=item.dpo_ref,
                s5_cycle_index=index,
            )
        )
    return tuple(correlated)


def select_reporting_s5_cycle_record_v1(
    cycle_records: Sequence[_CycleRecordLike],
    *,
    terminal_disposition: str,
) -> _CycleRecordLike | None:
    if not cycle_records:
        return None
    if str(terminal_disposition or "") == S5_PRE_EXTERNAL_DISPOSITION:
        for record in cycle_records:
            if str(record.s5_disposition or "") == S5_PRE_EXTERNAL_DISPOSITION:
                return record
    return cycle_records[-1]


def correlate_dpo_to_s5_cycle_index_v1(
    observations: Sequence[ProductiveDpoObservationV1],
    *,
    s5_cycle_index: int,
) -> ProductiveDpoObservationV1 | None:
    if s5_cycle_index < 1:
        return None
    for item in observations:
        if item.s5_cycle_index == s5_cycle_index:
            return item
    return None


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
    }


def evaluate_natural_enter_reporting_v1(
    *,
    cycle_records: Sequence[_CycleRecordLike],
    terminal_disposition: str,
    ddo_jsonl: Path,
) -> NaturalEnterReportingResultV1:
    reporting = select_reporting_s5_cycle_record_v1(
        cycle_records,
        terminal_disposition=terminal_disposition,
    )
    observations = load_productive_live_dpo_observations_v1(ddo_jsonl)
    if reporting is None:
        return NaturalEnterReportingResultV1(
            reporting_s5_cycle_index=None,
            reporting_s5_disposition="",
            dpo={},
            natural_enter_observed=False,
            natural_pre_external_reached=False,
            enter_side="",
        )
    correlated = correlate_dpo_to_s5_cycle_index_v1(
        observations,
        s5_cycle_index=int(reporting.cycle_index),
    )
    if correlated is None:
        return NaturalEnterReportingResultV1(
            reporting_s5_cycle_index=int(reporting.cycle_index),
            reporting_s5_disposition=str(reporting.s5_disposition or ""),
            dpo={},
            natural_enter_observed=False,
            natural_pre_external_reached=False,
            enter_side="",
        )
    dpo = dpo_observation_to_report_dict_v1(correlated)
    outcome = correlated.decision_outcome
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
    )


def extract_productive_dpo_for_pre_external_report_v1(
    lane_state_root: Path,
    *,
    cycle_records: Sequence[_CycleRecordLike],
    terminal_disposition: str,
) -> dict[str, str]:
    ddo = lane_state_root / "LANE_1/ddo_learning_capture_v1.jsonl"
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=cycle_records,
        terminal_disposition=terminal_disposition,
        ddo_jsonl=ddo,
    )
    return dict(result.dpo)
