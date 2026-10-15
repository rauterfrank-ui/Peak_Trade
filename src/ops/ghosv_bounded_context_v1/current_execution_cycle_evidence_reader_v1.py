"""Read-only binding for governed-cycle ledger/transitions and optional G004 disposition.

RUNTIME_AUTHORIZATION_EFFECT=NONE — no producer mutation, no exchange actions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    LEDGER_FILENAME as GOVERNED_CYCLE_LEDGER_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persisted_reconciliation_disposition_v1 import (
    CONTRACT_ID as G004_CONTRACT_ID,
    attempt_digest_v1,
    load_persisted_reconciliation_disposition_v1,
)
from src.ops.ghosv_bounded_context_v1.constants_v1 import PACKAGE_ID
from src.ops.ghosv_bounded_context_v1.s01_evidence_ingest_v1 import (
    GhosvEvidenceIngestError,
    normalize_evidence_record_v1,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import (
    GhosvCompleteness,
    GhosvEvidenceKind,
    GhosvEvidenceRecordV1,
)

CYCLE_READER_CONTRACT = "ghosv_current_execution_cycle_evidence_reader.v1"
CYCLE_SOURCE_MODULE = f"{PACKAGE_ID}.current_execution_cycle_evidence_reader_v1"
GOVERNED_CYCLE_LEDGER_CONTRACT = "governed_cycle_orchestrator_ledger.v1"
GOVERNED_CYCLE_TRANSITION_CONTRACT = "governed_cycle_orchestrator_transition.v1"
GOVERNED_CYCLE_POST_WITNESS_CONTRACT = "governed_cycle_orchestrator_post_count_witness.v1"
G004_DISPOSITION_CONTRACT = "full_core_post_attempt_exchange_reconciliation_disposition.v1"
TRANSITIONS_FILENAME = "transitions.jsonl"

_LOCAL_STOP_STATE_TOKENS = frozenset(
    {
        "CANCELLED_STOP",
        "CANCELLED",
        "FAILED_STOP",
    }
)


@dataclass(frozen=True)
class GovernedCycleEvidenceOptionsV1:
    """Optional fail-closed correlation guards (read-only)."""

    expected_native_id: str = ""
    expected_binding_digest: str = ""
    g004_expected_submit_attempt_id: str = ""
    g004_expected_clordid: str = ""


def parse_post_count_field_v1(data: Mapping[str, Any]) -> tuple[int | None, bool]:
    """Return (post_count, known). Missing or non-numeric POST_COUNT is unknown."""
    if "POST_COUNT" not in data:
        return None, False
    raw = data.get("POST_COUNT")
    if raw is None:
        return None, False
    if isinstance(raw, str) and not raw.strip():
        return None, False
    try:
        return int(raw), True
    except (TypeError, ValueError):
        return None, False


def _read_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GhosvEvidenceIngestError(f"NOT_OBJECT:{path}")
    return data


def _stable_event_id(prefix: str, material: str) -> str:
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}-{digest}"


def _ledger_completeness(payload: Mapping[str, Any], *, post_count_conflict: bool) -> str:
    if post_count_conflict:
        return GhosvCompleteness.UNKNOWN.value
    _pc, known = parse_post_count_field_v1(payload)
    if "POST_COUNT" in payload and not known:
        return GhosvCompleteness.UNKNOWN.value
    state = str(payload.get("state") or "").strip()
    if not state:
        return GhosvCompleteness.UNKNOWN.value
    return GhosvCompleteness.COMPLETE.value


def _transition_sequence_flags_v1(
    transitions: Sequence[Mapping[str, Any]],
) -> tuple[bool, bool, bool]:
    """Return (post_count_conflict, sequence_anomaly, duplicate_adjacent)."""
    post_values: list[int | None] = []
    post_known_flags: list[bool] = []
    for row in transitions:
        pc, known = parse_post_count_field_v1(row)
        post_known_flags.append(known)
        post_values.append(pc if known else None)

    post_count_conflict = False
    known_ints = [v for v in post_values if v is not None]
    if len(set(known_ints)) > 1:
        post_count_conflict = True

    sequence_anomaly = False
    states = [str(r.get("state") or "") for r in transitions]
    terminal_seen = False
    for state in states:
        if terminal_seen and state in {"IN_PROGRESS", "IDLE"}:
            sequence_anomaly = True
        if state in {"COMPLETED", "FAILED_STOP", "CANCELLED_STOP", "CANCELLED"}:
            terminal_seen = True

    duplicate_adjacent = False
    if len(transitions) >= 2:
        for idx in range(1, len(transitions)):
            prev = transitions[idx - 1]
            cur = transitions[idx]
            if json.dumps(prev, sort_keys=True) == json.dumps(cur, sort_keys=True):
                duplicate_adjacent = True
                break

    return post_count_conflict, sequence_anomaly, duplicate_adjacent


def _local_stop_semantics_v1(row: Mapping[str, Any]) -> dict[str, Any]:
    state = str(row.get("state") or "").strip()
    reason = str(row.get("reason_code") or row.get("result_reason") or "").strip()
    local_stop = state in _LOCAL_STOP_STATE_TOKENS or reason.upper() == "CANCELLED"
    return {
        "local_orchestrator_stop": local_stop,
        "venue_cancel_witness": False,
        "venue_cancel_requested": False,
        "orchestrator_state": state,
        "orchestrator_reason_code": reason,
    }


def _post_witness_record_v1(
    *,
    trade_id: str,
    instrument_id: str,
    row: Mapping[str, Any],
    source_contract: str,
    payload_ref: str,
    line_index: int | None,
    post_count_conflict: bool,
) -> GhosvEvidenceRecordV1:
    post_count, post_count_known = parse_post_count_field_v1(row)
    attempt_payload: dict[str, Any] = {
        "witness_scope": "GOVERNED_CYCLE_ORCHESTRATOR",
        "pre_external_witness": False,
        "post_submission_witness": True,
        "post_count_known": post_count_known,
        "post_count_conflict": post_count_conflict,
    }
    if post_count_known:
        assert post_count is not None
        attempt_payload["post_count"] = post_count
        attempt_payload["post_occurred"] = post_count > 0
    if post_count_conflict or not post_count_known:
        completeness = GhosvCompleteness.UNKNOWN.value
    else:
        completeness = GhosvCompleteness.COMPLETE.value
    suffix = f"line-{line_index}" if line_index is not None else "ledger"
    return normalize_evidence_record_v1(
        {
            "kind": GhosvEvidenceKind.EXECUTION_ATTEMPT.value,
            "source_module": CYCLE_SOURCE_MODULE,
            "source_contract": source_contract,
            "trade_id": trade_id,
            "instrument_id": instrument_id,
            "client_order_id": "",
            "exchange_order_id": "",
            "fill_id": "",
            "observation_timestamp": str(row.get("binding_digest") or suffix),
            "source_timestamp": str(row.get("state") or ""),
            "correlation_context": f"{payload_ref}:{suffix}",
            "completeness": completeness,
            "payload_ref": payload_ref,
            "payload": {**attempt_payload, **_local_stop_semantics_v1(row)},
            "event_id": _stable_event_id(
                "gc-post",
                f"{trade_id}|{source_contract}|{suffix}|{json.dumps(row, sort_keys=True)}",
            ),
        }
    )


def _runtime_observation_from_row_v1(
    *,
    trade_id: str,
    instrument_id: str,
    row: Mapping[str, Any],
    source_contract: str,
    payload_ref: str,
    line_index: int | None,
    extra_payload: Mapping[str, Any] | None = None,
) -> GhosvEvidenceRecordV1:
    suffix = f"line-{line_index}" if line_index is not None else "ledger-final"
    payload = dict(row)
    payload.update(_local_stop_semantics_v1(row))
    if extra_payload:
        payload.update(dict(extra_payload))
    completeness = _ledger_completeness(
        row,
        post_count_conflict=bool(payload.get("post_count_conflict")),
    )
    return normalize_evidence_record_v1(
        {
            "kind": GhosvEvidenceKind.RUNTIME_OBSERVATION.value,
            "source_module": "ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1",
            "source_contract": source_contract,
            "trade_id": trade_id,
            "instrument_id": instrument_id,
            "client_order_id": "",
            "exchange_order_id": "",
            "fill_id": "",
            "observation_timestamp": str(row.get("binding_digest") or suffix),
            "source_timestamp": str(row.get("state") or ""),
            "correlation_context": f"{payload_ref}:{suffix}",
            "completeness": completeness,
            "payload_ref": payload_ref,
            "payload": payload,
            "event_id": _stable_event_id(
                "gc-obs",
                f"{trade_id}|{source_contract}|{suffix}|{json.dumps(row, sort_keys=True)}",
            ),
        }
    )


def load_governed_cycle_ledger_evidence_v1(
    ledger_path: Path,
    *,
    trade_id: str,
    options: GovernedCycleEvidenceOptionsV1 | None = None,
    post_count_conflict: bool = False,
) -> tuple[GhosvEvidenceRecordV1, ...]:
    """Map final governed-cycle orchestrator ledger JSON (read-only)."""
    opts = options or GovernedCycleEvidenceOptionsV1()
    ledger = _read_json_object(Path(ledger_path))
    native_id = str(ledger.get("native_id") or "").strip()
    if opts.expected_native_id.strip() and native_id != opts.expected_native_id.strip():
        raise GhosvEvidenceIngestError("CYCLE_NATIVE_ID_MISMATCH")
    binding_digest = str(ledger.get("binding_digest") or "").strip()
    if (
        opts.expected_binding_digest.strip()
        and binding_digest != opts.expected_binding_digest.strip()
    ):
        raise GhosvEvidenceIngestError("CYCLE_BINDING_DIGEST_MISMATCH")

    records: list[GhosvEvidenceRecordV1] = []
    ledger_extra = {"post_count_conflict": post_count_conflict}
    records.append(
        _runtime_observation_from_row_v1(
            trade_id=trade_id,
            instrument_id=native_id,
            row=ledger,
            source_contract=GOVERNED_CYCLE_LEDGER_CONTRACT,
            payload_ref=str(ledger_path),
            line_index=None,
            extra_payload=ledger_extra,
        )
    )
    records.append(
        _post_witness_record_v1(
            trade_id=trade_id,
            instrument_id=native_id,
            row=ledger,
            source_contract=GOVERNED_CYCLE_POST_WITNESS_CONTRACT,
            payload_ref=str(ledger_path),
            line_index=None,
            post_count_conflict=post_count_conflict,
        )
    )
    return tuple(records)


def load_governed_cycle_transitions_evidence_v1(
    transitions_path: Path,
    *,
    trade_id: str,
    ledger_path: Path | None = None,
    options: GovernedCycleEvidenceOptionsV1 | None = None,
) -> tuple[GhosvEvidenceRecordV1, ...]:
    """Map governed-cycle transitions JSONL (read-only)."""
    opts = options or GovernedCycleEvidenceOptionsV1()
    path = Path(transitions_path)
    if not path.is_file():
        return ()

    parsed_rows: list[dict[str, Any]] = []
    malformed_lines: list[int] = []
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = raw_line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            malformed_lines.append(line_no)
            continue
        if not isinstance(row, dict):
            malformed_lines.append(line_no)
            continue
        parsed_rows.append(row)

    if malformed_lines and not parsed_rows:
        return (
            normalize_evidence_record_v1(
                {
                    "kind": GhosvEvidenceKind.RUNTIME_OBSERVATION.value,
                    "source_module": CYCLE_SOURCE_MODULE,
                    "source_contract": GOVERNED_CYCLE_TRANSITION_CONTRACT,
                    "trade_id": trade_id,
                    "instrument_id": "",
                    "client_order_id": "",
                    "exchange_order_id": "",
                    "fill_id": "",
                    "observation_timestamp": "",
                    "source_timestamp": "",
                    "correlation_context": str(path),
                    "completeness": GhosvCompleteness.UNKNOWN.value,
                    "payload_ref": str(path),
                    "payload": {
                        "malformed_line_numbers": malformed_lines,
                        "truncated_jsonl": True,
                    },
                    "event_id": _stable_event_id(
                        "gc-malformed", f"{trade_id}|{path}|{malformed_lines}"
                    ),
                }
            ),
        )

    post_conflict, sequence_anomaly, duplicate_adjacent = _transition_sequence_flags_v1(parsed_rows)

    ledger_post: tuple[int | None, bool] = (None, False)
    ledger_native = ""
    if ledger_path is not None and Path(ledger_path).is_file():
        ledger_obj = _read_json_object(Path(ledger_path))
        ledger_post = parse_post_count_field_v1(ledger_obj)
        ledger_native = str(ledger_obj.get("native_id") or "").strip()
        if ledger_post[1] and post_conflict is False:
            last_pc, last_known = (
                parse_post_count_field_v1(parsed_rows[-1])
                if parsed_rows
                else (
                    None,
                    False,
                )
            )
            if last_known and ledger_post[0] != last_pc:
                post_conflict = True

    records: list[GhosvEvidenceRecordV1] = []
    if malformed_lines:
        records.append(
            normalize_evidence_record_v1(
                {
                    "kind": GhosvEvidenceKind.RUNTIME_OBSERVATION.value,
                    "source_module": CYCLE_SOURCE_MODULE,
                    "source_contract": GOVERNED_CYCLE_TRANSITION_CONTRACT,
                    "trade_id": trade_id,
                    "instrument_id": ledger_native,
                    "client_order_id": "",
                    "exchange_order_id": "",
                    "fill_id": "",
                    "observation_timestamp": "",
                    "source_timestamp": "",
                    "correlation_context": str(path),
                    "completeness": GhosvCompleteness.UNKNOWN.value,
                    "payload_ref": str(path),
                    "payload": {
                        "malformed_line_numbers": malformed_lines,
                        "truncated_jsonl": True,
                    },
                    "event_id": _stable_event_id(
                        "gc-malformed", f"{trade_id}|{path}|{malformed_lines}"
                    ),
                }
            )
        )

    for idx, row in enumerate(parsed_rows):
        native_id = str(row.get("native_id") or ledger_native or "").strip()
        if opts.expected_native_id.strip() and native_id != opts.expected_native_id.strip():
            raise GhosvEvidenceIngestError("TRANSITION_NATIVE_ID_MISMATCH")
        if ledger_native and native_id and native_id != ledger_native:
            raise GhosvEvidenceIngestError("TRANSITION_INSTRUMENT_CROSS_CONTAMINATION")

        extra = {
            "transition_index": idx,
            "post_count_conflict": post_conflict,
            "sequence_anomaly": sequence_anomaly,
            "duplicate_adjacent_transition": duplicate_adjacent,
        }
        records.append(
            _runtime_observation_from_row_v1(
                trade_id=trade_id,
                instrument_id=native_id,
                row=row,
                source_contract=GOVERNED_CYCLE_TRANSITION_CONTRACT,
                payload_ref=str(path),
                line_index=idx,
                extra_payload=extra,
            )
        )
        records.append(
            _post_witness_record_v1(
                trade_id=trade_id,
                instrument_id=native_id,
                row=row,
                source_contract=GOVERNED_CYCLE_POST_WITNESS_CONTRACT,
                payload_ref=str(path),
                line_index=idx,
                post_count_conflict=post_conflict,
            )
        )

    return tuple(records)


def load_governed_cycle_evidence_dir_v1(
    evidence_dir: Path,
    *,
    trade_id: str,
    options: GovernedCycleEvidenceOptionsV1 | None = None,
) -> tuple[GhosvEvidenceRecordV1, ...]:
    """Load ledger + optional transitions from a cycle evidence directory."""
    root = Path(evidence_dir)
    ledger_path = root / GOVERNED_CYCLE_LEDGER_FILENAME
    if not ledger_path.is_file():
        raise GhosvEvidenceIngestError(f"MISSING_LEDGER:{ledger_path}")
    trans_path = root / TRANSITIONS_FILENAME
    parsed_rows, _malformed = _parse_transitions_file_v1(trans_path)
    post_conflict, _, _ = _transition_sequence_flags_v1(parsed_rows)
    if parsed_rows:
        ledger_obj = _read_json_object(ledger_path)
        ledger_post = parse_post_count_field_v1(ledger_obj)
        last_pc, last_known = parse_post_count_field_v1(parsed_rows[-1])
        if ledger_post[1] and last_known and ledger_post[0] != last_pc:
            post_conflict = True

    out: list[GhosvEvidenceRecordV1] = []
    out.extend(
        load_governed_cycle_ledger_evidence_v1(
            ledger_path,
            trade_id=trade_id,
            options=options,
            post_count_conflict=post_conflict,
        )
    )
    out.extend(
        load_governed_cycle_transitions_evidence_v1(
            trans_path,
            trade_id=trade_id,
            ledger_path=ledger_path,
            options=options,
        )
    )
    return tuple(out)


def _parse_transitions_file_v1(path: Path) -> tuple[list[dict[str, Any]], list[int]]:
    parsed_rows: list[dict[str, Any]] = []
    malformed_lines: list[int] = []
    if not path.is_file():
        return parsed_rows, malformed_lines
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = raw_line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            malformed_lines.append(line_no)
            continue
        if not isinstance(row, dict):
            malformed_lines.append(line_no)
            continue
        parsed_rows.append(row)
    return parsed_rows, malformed_lines


def _validate_g004_record_v1(
    record: Mapping[str, Any],
    *,
    options: GovernedCycleEvidenceOptionsV1,
) -> None:
    if str(record.get("contract_id") or "") != G004_CONTRACT_ID:
        raise GhosvEvidenceIngestError("G004_CONTRACT_MISMATCH")
    submit_attempt_id = str(record.get("submit_attempt_id") or "").strip()
    clordid = str(record.get("clordid") or "").strip()
    envelope_digest = str(record.get("envelope_digest") or "").strip()
    if not submit_attempt_id or not clordid or not envelope_digest:
        raise GhosvEvidenceIngestError("G004_IDENTITY_INCOMPLETE")
    expected_attempt = options.g004_expected_submit_attempt_id.strip()
    if expected_attempt and submit_attempt_id != expected_attempt:
        raise GhosvEvidenceIngestError("G004_SUBMIT_ATTEMPT_MISMATCH")
    expected_clord = options.g004_expected_clordid.strip()
    if expected_clord and clordid != expected_clord:
        raise GhosvEvidenceIngestError("G004_CLORDID_MISMATCH")
    expected_digest = attempt_digest_v1(
        submit_attempt_id=submit_attempt_id,
        envelope_digest=envelope_digest,
    )
    if str(record.get("attempt_digest") or "").strip() != expected_digest:
        raise GhosvEvidenceIngestError("G004_ATTEMPT_DIGEST_MISMATCH")


def load_g004_disposition_evidence_v1(
    store_root: Path,
    *,
    trade_id: str,
    options: GovernedCycleEvidenceOptionsV1 | None = None,
) -> tuple[GhosvEvidenceRecordV1, ...]:
    """Optional G004 disposition binding. Returns () if file absent."""
    opts = options or GovernedCycleEvidenceOptionsV1()
    record = load_persisted_reconciliation_disposition_v1(store_root=Path(store_root))
    if record is None:
        return ()
    _validate_g004_record_v1(record, options=opts)

    clordid = str(record.get("clordid") or "").strip()
    venue_ord = str(record.get("venue_ord_id") or "").strip()
    native_id = str(record.get("native_id") or record.get("instrument_id") or "").strip()
    reconciliation_outcome = str(record.get("reconciliation_outcome") or "").strip()
    typed_post = str(record.get("typed_post_submit_outcome") or "").strip()
    local_submit = str(record.get("local_submit_outcome") or "").strip()
    path = Path(store_root) / "full_core_post_attempt_exchange_reconciliation_disposition_v1.json"

    base_payload = {
        **record,
        "g004_witness": True,
        "reconciliation_is_not_fill": True,
        "ack_is_not_fill": record.get("ack_is_not_fill") is True,
    }

    records: list[GhosvEvidenceRecordV1] = []

    records.append(
        normalize_evidence_record_v1(
            {
                "kind": GhosvEvidenceKind.RECONCILIATION_GATE.value,
                "source_module": "ops.full_core_live_path_composition_root_v1.current_productive_persisted_reconciliation_disposition_v1",
                "source_contract": G004_DISPOSITION_CONTRACT,
                "trade_id": trade_id,
                "instrument_id": native_id,
                "client_order_id": clordid,
                "exchange_order_id": venue_ord,
                "fill_id": "",
                "observation_timestamp": str(record.get("persisted_at_utc") or ""),
                "source_timestamp": str(record.get("persisted_at_utc") or ""),
                "correlation_context": str(record.get("submit_attempt_id") or ""),
                "completeness": GhosvCompleteness.COMPLETE.value
                if reconciliation_outcome
                else GhosvCompleteness.UNKNOWN.value,
                "payload_ref": str(path),
                "payload": base_payload,
                "event_id": _stable_event_id(
                    "g004-recon",
                    f"{trade_id}|{record.get('submit_attempt_id')}|{reconciliation_outcome}",
                ),
            }
        )
    )

    records.append(
        normalize_evidence_record_v1(
            {
                "kind": GhosvEvidenceKind.ORDER_STATUS.value,
                "source_module": CYCLE_SOURCE_MODULE,
                "source_contract": G004_DISPOSITION_CONTRACT,
                "trade_id": trade_id,
                "instrument_id": native_id,
                "client_order_id": clordid,
                "exchange_order_id": venue_ord,
                "fill_id": "",
                "observation_timestamp": str(record.get("persisted_at_utc") or ""),
                "source_timestamp": reconciliation_outcome,
                "correlation_context": str(record.get("submit_attempt_id") or ""),
                "completeness": GhosvCompleteness.COMPLETE.value
                if reconciliation_outcome
                else GhosvCompleteness.UNKNOWN.value,
                "payload_ref": str(path),
                "payload": {
                    **base_payload,
                    "exchange_order_state_witness": reconciliation_outcome,
                    "not_a_fill_event": True,
                },
                "event_id": _stable_event_id(
                    "g004-status",
                    f"{trade_id}|{reconciliation_outcome}|{typed_post}",
                ),
            }
        )
    )

    if typed_post == "ACKNOWLEDGED":
        records.append(
            normalize_evidence_record_v1(
                {
                    "kind": GhosvEvidenceKind.ORDER_ACK.value,
                    "source_module": CYCLE_SOURCE_MODULE,
                    "source_contract": G004_DISPOSITION_CONTRACT,
                    "trade_id": trade_id,
                    "instrument_id": native_id,
                    "client_order_id": clordid,
                    "exchange_order_id": venue_ord,
                    "fill_id": "",
                    "observation_timestamp": str(record.get("persisted_at_utc") or ""),
                    "source_timestamp": local_submit,
                    "correlation_context": str(record.get("submit_attempt_id") or ""),
                    "completeness": GhosvCompleteness.COMPLETE.value,
                    "payload_ref": str(path),
                    "payload": {
                        **base_payload,
                        "treated_as_fill": False,
                        "transport_submit_ack_only": True,
                    },
                    "event_id": _stable_event_id("g004-ack", f"{trade_id}|{clordid}|{venue_ord}"),
                }
            )
        )
    elif typed_post == "REJECTED":
        records.append(
            normalize_evidence_record_v1(
                {
                    "kind": GhosvEvidenceKind.ORDER_REJECT.value,
                    "source_module": CYCLE_SOURCE_MODULE,
                    "source_contract": G004_DISPOSITION_CONTRACT,
                    "trade_id": trade_id,
                    "instrument_id": native_id,
                    "client_order_id": clordid,
                    "exchange_order_id": venue_ord,
                    "fill_id": "",
                    "observation_timestamp": str(record.get("persisted_at_utc") or ""),
                    "source_timestamp": local_submit,
                    "correlation_context": str(record.get("submit_attempt_id") or ""),
                    "completeness": GhosvCompleteness.COMPLETE.value,
                    "payload_ref": str(path),
                    "payload": base_payload,
                    "event_id": _stable_event_id(
                        "g004-reject", f"{trade_id}|{clordid}|{typed_post}"
                    ),
                }
            )
        )

    return tuple(records)


__all__ = [
    "CYCLE_READER_CONTRACT",
    "GOVERNED_CYCLE_LEDGER_CONTRACT",
    "G004_DISPOSITION_CONTRACT",
    "GovernedCycleEvidenceOptionsV1",
    "load_g004_disposition_evidence_v1",
    "load_governed_cycle_evidence_dir_v1",
    "load_governed_cycle_ledger_evidence_v1",
    "load_governed_cycle_transitions_evidence_v1",
    "parse_post_count_field_v1",
]
