"""Deterministic delayed G12 conjunction evaluator. Never GETs. Never POSTs.

Does not claim LIVE_FLATTEN_PROVEN from delayed zero alone. Same-session
CHOICE_B semantics remain in flatten_post_action_proof_contract_v1.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.constants_v1 import (
    ACCOUNT_MUTATION_EFFECT_NONE,
    G12_STATUS,
    NETWORK_EFFECT_NONE,
    OFFLINE_LIVE_FLATTEN_PROVABILITY_STATUS,
    ORDER_EFFECT_NONE,
    PENDING_ENDPOINT,
    POSITIONS_ENDPOINT,
    SCHEMA_VERSION,
    STATUS_FAIL,
    STATUS_NOT_PROVEN,
    STATUS_PASS,
    TARGET_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.contract_v1 import (
    DelayedG12ConjunctionContractError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.types_v1 import (
    DelayedG12ConjunctionInputV1,
    FlattenLineageSlotV1,
    ObservationSlotV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
)


@dataclass(frozen=True)
class ConjunctVerdictV1:
    """One independently evaluated proposition."""

    proposition: str
    status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposition": self.proposition,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DelayedG12ConjunctionVerdictV1:
    """Offline conjunction result. Not a canonical SSOT write."""

    instrument_id: str
    conjuncts: tuple[ConjunctVerdictV1, ...]
    full_conjunction_proven: bool
    live_flatten_provability_proven: bool
    delayed_explicit_target_zero: bool
    canonical_ssot_g12_status: str
    live_flatten_provability_status: str
    blocking_reasons: tuple[str, ...]
    provenance_sha256: str
    network_effect: str
    order_effect: str
    account_mutation_effect: str
    schema_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "conjuncts": [item.to_dict() for item in self.conjuncts],
            "full_conjunction_proven": self.full_conjunction_proven,
            "live_flatten_provability_proven": self.live_flatten_provability_proven,
            "delayed_explicit_target_zero": self.delayed_explicit_target_zero,
            "canonical_ssot_g12_status": self.canonical_ssot_g12_status,
            "live_flatten_provability_status": self.live_flatten_provability_status,
            "blocking_reasons": list(self.blocking_reasons),
            "provenance_sha256": self.provenance_sha256,
            "network_effect": self.network_effect,
            "order_effect": self.order_effect,
            "account_mutation_effect": self.account_mutation_effect,
            "schema_version": self.schema_version,
        }


def _conjunct(proposition: str, status: str, reason: str) -> ConjunctVerdictV1:
    return ConjunctVerdictV1(proposition=proposition, status=status, reason=reason)


def _not_proven(proposition: str, reason: str) -> ConjunctVerdictV1:
    return _conjunct(proposition, STATUS_NOT_PROVEN, reason)


def _fail(proposition: str, reason: str) -> ConjunctVerdictV1:
    return _conjunct(proposition, STATUS_FAIL, reason)


def _pass(proposition: str, reason: str) -> ConjunctVerdictV1:
    return _conjunct(proposition, STATUS_PASS, reason)


def _parse_utc(value: str | None, *, label: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise DelayedG12ConjunctionContractError(f"{label}_TIMESTAMP_UNPARSEABLE") from None
    if parsed.tzinfo is None:
        raise DelayedG12ConjunctionContractError(f"{label}_TIMESTAMP_NAIVE")
    return parsed.astimezone(timezone.utc)


def _query_map(slot: ObservationSlotV1) -> dict[str, str]:
    if slot.query:
        return {str(key): str(value) for key, value in slot.query.items()}
    parsed = urlparse(slot.endpoint)
    out: dict[str, str] = {}
    for key, values in parse_qs(parsed.query).items():
        if values:
            out[str(key)] = str(values[0])
    return out


def _endpoint_path(slot: ObservationSlotV1) -> str:
    parsed = urlparse(slot.endpoint)
    path = parsed.path or slot.endpoint.split("?", 1)[0]
    return str(path).strip()


def _envelope_rows(
    payload: Mapping[str, Any] | None, *, label: str
) -> tuple[list[Mapping[str, Any]] | None, str | None]:
    if payload is None:
        return None, f"{label}_PAYLOAD_MISSING"
    if not isinstance(payload, Mapping):
        return None, f"{label}_PAYLOAD_NOT_MAPPING"
    if "code" not in payload:
        return None, f"{label}_CODE_MISSING"
    if str(payload.get("code") or "") != "0":
        return None, f"{label}_EXCHANGE_STATE_PAYLOAD_NOT_OK"
    if "data" not in payload:
        return None, f"{label}_DATA_MISSING"
    data = payload["data"]
    if data is None:
        return None, f"{label}_DATA_NONE"
    if not isinstance(data, list):
        return None, f"{label}_DATA_NOT_LIST"
    rows: list[Mapping[str, Any]] = []
    for row in data:
        if not isinstance(row, Mapping):
            return None, f"{label}_ROW_NOT_MAPPING"
        rows.append(row)
    return rows, None


def _signed_pos(row: Mapping[str, Any]) -> tuple[Decimal | None, str | None]:
    if "pos" in row and row["pos"] is not None:
        raw = row["pos"]
    elif "posSize" in row and row["posSize"] is not None:
        raw = row["posSize"]
    else:
        return None, "POSITION_SIZE_MISSING"
    text = str(raw).strip()
    if not text:
        return None, "POSITION_SIZE_MISSING"
    try:
        return Decimal(text), None
    except (InvalidOperation, TypeError, ValueError):
        return None, "POSITION_SIZE_UNPARSEABLE"


def _nonzero_related(
    rows: list[Mapping[str, Any]], *, target: str
) -> tuple[tuple[str, ...], str | None]:
    related: list[str] = []
    seen: dict[str, int] = {}
    for row in rows:
        inst = str(row.get("instId") or "").strip()
        if not inst:
            return (), "POSITION_INSTID_MISSING"
        seen[inst] = seen.get(inst, 0) + 1
        signed, err = _signed_pos(row)
        if err:
            return (), err
        assert signed is not None
        if signed != 0 and inst != target:
            related.append(inst)
    for inst, count in seen.items():
        if count != 1:
            return (), "AMBIGUOUS_TARGET_POSITION_ROWS"
    return tuple(sorted(set(related))), None


def _pre_signed(lineage: FlattenLineageSlotV1, *, target: str) -> tuple[Decimal | None, str | None]:
    rows, err = _envelope_rows(lineage.pre_observation.payload, label="PRE")
    if err:
        return None, err
    assert rows is not None
    matching = [row for row in rows if str(row.get("instId") or "").strip() == target]
    if not matching:
        return None, "PRE_TARGET_NOT_OBSERVED"
    if len(matching) != 1:
        return None, "PRE_TARGET_AMBIGUOUS"
    return _signed_pos(matching[0])


def evaluate_delayed_g12_conjunction_v1(
    payload: DelayedG12ConjunctionInputV1,
) -> DelayedG12ConjunctionVerdictV1:
    """Evaluate P1..P10 independently. Delayed zero never implies the rest."""
    assert_contract_invariants_v1(
        {"forensic_local_treated_as_canonical": payload.forensic_local_treated_as_canonical}
    )
    target = str(payload.instrument_id or "").strip()
    if not target:
        raise DelayedG12ConjunctionContractError("TARGET_INSTRUMENT_REQUIRED")
    if target != TARGET_INSTRUMENT_ID:
        raise DelayedG12ConjunctionContractError("INSTRUMENT_BINDING_MISMATCH")

    lineage = payload.flatten_lineage
    delayed = payload.delayed_target_zero
    pending = payload.pending_orders
    related = payload.related_positions

    p1 = _evaluate_p1(lineage, target)
    p2 = _evaluate_p2(lineage)
    p3 = _evaluate_p3(lineage, target)
    p4 = _evaluate_p4(lineage, target)
    p5 = _evaluate_p5(delayed, target, lineage)
    p6 = _evaluate_p6(lineage, delayed, target)
    p7 = _evaluate_p7(pending, delayed)
    p8 = _evaluate_p8(lineage, delayed, target)
    p9 = _evaluate_p9(related, delayed, lineage, target)
    p10 = _evaluate_p10(lineage, delayed, pending, related)

    conjuncts = (p1, p2, p3, p4, p5, p6, p7, p8, p9, p10)
    blocking = tuple(item.reason for item in conjuncts if item.status != STATUS_PASS)
    full = all(item.status == STATUS_PASS for item in conjuncts)
    delayed_zero = p5.status == STATUS_PASS
    live_proven = bool(full)
    provenance = _provenance_sha256(
        {
            "instrument_id": target,
            "conjuncts": [item.to_dict() for item in conjuncts],
            "full_conjunction_proven": full,
            "live_flatten_provability_proven": live_proven,
            "schema_version": SCHEMA_VERSION,
        }
    )
    return DelayedG12ConjunctionVerdictV1(
        instrument_id=target,
        conjuncts=conjuncts,
        full_conjunction_proven=full,
        live_flatten_provability_proven=live_proven,
        delayed_explicit_target_zero=delayed_zero,
        canonical_ssot_g12_status=G12_STATUS,
        live_flatten_provability_status=(
            "PROVEN" if live_proven else OFFLINE_LIVE_FLATTEN_PROVABILITY_STATUS
        ),
        blocking_reasons=blocking,
        provenance_sha256=provenance,
        network_effect=NETWORK_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        account_mutation_effect=ACCOUNT_MUTATION_EFFECT_NONE,
        schema_version=SCHEMA_VERSION,
    )


def _evaluate_p1(lineage: FlattenLineageSlotV1 | None, target: str) -> ConjunctVerdictV1:
    prop = "P1_AUTHORIZED_FLATTEN"
    if lineage is None:
        return _not_proven(prop, "FLATTEN_LINEAGE_SLOT_MISSING")
    if lineage.instrument_id != target:
        return _fail(prop, "FLATTEN_INSTRUMENT_MISMATCH")
    if not lineage.authorized:
        return _fail(prop, "FLATTEN_NOT_AUTHORIZED")
    if lineage.reduce_only is not True:
        return _fail(prop, "FLATTEN_NOT_REDUCE_ONLY")
    if str(lineage.ord_type or "").strip().lower() != "limit":
        return _fail(prop, "FLATTEN_NOT_LIMIT")
    if not str(lineage.cl_ord_id or "").strip():
        return _fail(prop, "FLATTEN_CLORDID_MISSING")
    return _pass(prop, "AUTHORIZED_REDUCE_ONLY_LIMIT_FLATTEN")


def _evaluate_p2(lineage: FlattenLineageSlotV1 | None) -> ConjunctVerdictV1:
    prop = "P2_VENUE_ACCEPTED"
    if lineage is None:
        return _not_proven(prop, "FLATTEN_LINEAGE_SLOT_MISSING")
    status = lineage.submit_http_status
    if lineage.venue_accepted is not True:
        return _fail(prop, "VENUE_ACCEPTANCE_NOT_PROVEN")
    if status is None or not (200 <= int(status) < 300):
        return _fail(prop, "SUBMIT_HTTP_NOT_2XX")
    return _pass(prop, "VENUE_ACCEPTED")


def _evaluate_p3(lineage: FlattenLineageSlotV1 | None, target: str) -> ConjunctVerdictV1:
    prop = "P3_ORDER_FILLED"
    if lineage is None:
        return _not_proven(prop, "FLATTEN_LINEAGE_SLOT_MISSING")
    fill_id = str(lineage.fill_cl_ord_id or "").strip()
    if not fill_id:
        return _not_proven(prop, "FILL_CLORDID_MISSING")
    if fill_id != str(lineage.cl_ord_id or "").strip():
        return _fail(prop, "FILL_CLORDID_MISMATCH")
    if str(lineage.fill_instrument_id or "").strip() != target:
        return _fail(prop, "FILL_INSTRUMENT_MISMATCH")
    if not str(lineage.fill_sz or "").strip():
        return _fail(prop, "FILL_SZ_MISSING")
    if not str(lineage.fill_side or "").strip():
        return _fail(prop, "FILL_SIDE_MISSING")
    return _pass(prop, "FILL_BOUND_TO_CLORDID")


def _evaluate_p4(lineage: FlattenLineageSlotV1 | None, target: str) -> ConjunctVerdictV1:
    prop = "P4_PRE_ACTION_NONZERO"
    if lineage is None:
        return _not_proven(prop, "FLATTEN_LINEAGE_SLOT_MISSING")
    signed, err = _pre_signed(lineage, target=target)
    if err:
        if err in {"PRE_TARGET_NOT_OBSERVED", "PRE_DATA_MISSING", "PRE_PAYLOAD_MISSING"}:
            return _not_proven(prop, err)
        return _fail(prop, err)
    assert signed is not None
    if signed == 0:
        return _fail(prop, "PRE_POS_ZERO")
    return _pass(prop, "PRE_TARGET_NONZERO")


def _evaluate_p5(
    delayed: ObservationSlotV1 | None,
    target: str,
    lineage: FlattenLineageSlotV1 | None,
) -> ConjunctVerdictV1:
    prop = "P5_DELAYED_TARGET_ZERO"
    if delayed is None:
        return _not_proven(prop, "DELAYED_ZERO_SLOT_MISSING")
    if delayed.http_status is not None and not (200 <= int(delayed.http_status) < 300):
        return _fail(prop, "DELAYED_ZERO_HTTP_NOT_2XX")
    rows, err = _envelope_rows(delayed.payload, label="DELAYED_ZERO")
    if err:
        return _fail(prop, err)
    assert rows is not None
    if not rows:
        return _fail(prop, "DELAYED_ZERO_EMPTY_DATA_IS_NOT_ZERO")
    classified = classify_target_position_state_v1(
        positions_payload=delayed.payload,
        instrument_id=target,
    )
    if classified.state != TARGET_POSITION_ZERO_PROVEN:
        return _fail(prop, classified.reason)
    query = _query_map(delayed)
    pos_id = str(query.get("posId") or "").strip()
    if not pos_id:
        return _fail(prop, "DELAYED_ZERO_POSID_QUERY_MISSING")
    if _endpoint_path(delayed) != POSITIONS_ENDPOINT:
        return _fail(prop, "DELAYED_ZERO_ENDPOINT_MISMATCH")
    if len(rows) != 1:
        return _fail(prop, "DELAYED_ZERO_ROW_COUNT_NOT_UNIQUE")
    row_pos_id = str(rows[0].get("posId") or "").strip()
    if row_pos_id != pos_id:
        return _fail(prop, "DELAYED_ZERO_ROW_POSID_MISMATCH")
    if lineage is not None:
        proven = str(lineage.proven_pos_id or "").strip()
        if proven and proven != pos_id:
            return _fail(prop, "DELAYED_ZERO_POSID_NOT_LINEAGE_POSID")
    return _pass(prop, "UNIQUE_EXPLICIT_POS_EQ_0_TARGET_ROW")


def _evaluate_p6(
    lineage: FlattenLineageSlotV1 | None,
    delayed: ObservationSlotV1 | None,
    target: str,
) -> ConjunctVerdictV1:
    prop = "P6_CAUSAL_LINEAGE"
    if lineage is None or delayed is None:
        return _not_proven(prop, "LINEAGE_OR_DELAYED_SLOT_MISSING")
    delayed_id = str(delayed.observation_identity or "").strip()
    pre_id = str(lineage.pre_observation.observation_identity or "").strip()
    immediate_id = str(lineage.immediate_post_action_identity or "").strip()
    if not delayed_id:
        return _fail(prop, "DELAYED_OBSERVATION_IDENTITY_MISSING")
    if delayed_id == pre_id:
        return _fail(prop, "DELAYED_IDENTITY_EQUALS_PRE_IDENTITY")
    if immediate_id and delayed_id == immediate_id:
        return _fail(prop, "DELAYED_IDENTITY_EQUALS_IMMEDIATE_POST_READBACK")
    query = _query_map(delayed)
    pos_id = str(query.get("posId") or "").strip()
    proven = str(lineage.proven_pos_id or "").strip()
    if not proven:
        return _not_proven(prop, "LINEAGE_POSID_MISSING")
    if not pos_id:
        return _fail(prop, "DELAYED_POSID_MISSING")
    if pos_id != proven:
        return _fail(prop, "POSID_LINEAGE_MISMATCH")
    if lineage.instrument_id != target:
        return _fail(prop, "LINEAGE_INSTRUMENT_MISMATCH")
    return _pass(prop, "CAUSAL_POSID_INSTID_LINEAGE_NOT_IDENTITY_EQUALITY")


def _evaluate_p7(
    pending: ObservationSlotV1 | None,
    delayed: ObservationSlotV1 | None,
) -> ConjunctVerdictV1:
    prop = "P7_PENDING_EMPTY"
    if pending is None:
        return _not_proven(prop, "PENDING_SLOT_MISSING")
    if _endpoint_path(pending) != PENDING_ENDPOINT:
        return _fail(prop, "PENDING_ENDPOINT_MISMATCH")
    query = _query_map(pending)
    if query:
        return _fail(prop, "PENDING_QUERY_MUST_BE_UNFILTERED")
    rows, err = _envelope_rows(pending.payload, label="PENDING")
    if err:
        return _fail(prop, err)
    assert rows is not None
    if any(not str(row.get("instId") or row.get("instID") or "").strip() for row in rows):
        return _fail(prop, "PENDING_INSTID_MISSING")
    if rows:
        return _fail(prop, "PENDING_NOT_EMPTY")
    if delayed is not None:
        pending_ts = _parse_utc(pending.request_time_utc, label="PENDING")
        delayed_ts = _parse_utc(delayed.request_time_utc, label="DELAYED_ZERO")
        if pending_ts is None or delayed_ts is None:
            return _not_proven(prop, "PENDING_OR_DELAYED_TIMESTAMP_MISSING")
        if pending_ts < delayed_ts:
            return _fail(prop, "PENDING_OBSERVATION_STALE_BEFORE_DELAYED_ZERO")
    return _pass(prop, "REGULAR_PENDING_EMPTY_AFTER_DELAYED_ZERO")


def _evaluate_p8(
    lineage: FlattenLineageSlotV1 | None,
    delayed: ObservationSlotV1 | None,
    target: str,
) -> ConjunctVerdictV1:
    prop = "P8_NO_FLIP"
    if lineage is None or delayed is None:
        return _not_proven(prop, "LINEAGE_OR_DELAYED_SLOT_MISSING")
    pre_signed, pre_err = _pre_signed(lineage, target=target)
    if pre_err:
        return _not_proven(prop, pre_err)
    classified = classify_target_position_state_v1(
        positions_payload=delayed.payload,
        instrument_id=target,
    )
    if classified.state != TARGET_POSITION_ZERO_PROVEN or classified.signed_pos is None:
        return _not_proven(prop, "NO_FLIP_REQUIRES_EXPLICIT_DELAYED_ZERO_ROW")
    post_signed = Decimal(classified.signed_pos)
    assert pre_signed is not None
    flipped = pre_signed != 0 and post_signed != 0 and (pre_signed > 0) != (post_signed > 0)
    if flipped:
        return _fail(prop, "FLIP_DETECTED")
    return _pass(prop, "PAIRWISE_PRE_NONZERO_DELAYED_EXPLICIT_ZERO")


def _evaluate_p9(
    related: ObservationSlotV1 | None,
    delayed: ObservationSlotV1 | None,
    lineage: FlattenLineageSlotV1 | None,
    target: str,
) -> ConjunctVerdictV1:
    prop = "P9_NO_UNEXPECTED_RELATED_NONZERO"
    if related is None:
        return _not_proven(prop, "RELATED_SLOT_MISSING")
    if _endpoint_path(related) != POSITIONS_ENDPOINT:
        return _fail(prop, "RELATED_ENDPOINT_MISMATCH")
    query = _query_map(related)
    if "posId" in query:
        return _fail(prop, "POSID_FILTERED_ENVELOPE_CANNOT_PROVE_RELATED")
    if "instId" in query:
        return _fail(prop, "INSTID_FILTERED_ENVELOPE_CANNOT_PROVE_RELATED")
    rows, err = _envelope_rows(related.payload, label="RELATED")
    if err:
        return _fail(prop, err)
    assert rows is not None
    found, rel_err = _nonzero_related(rows, target=target)
    if rel_err:
        return _fail(prop, rel_err)
    if found:
        return _fail(prop, "UNEXPECTED_RELATED_INSTRUMENT_POSITION")
    if lineage is not None:
        pre_rows, pre_err = _envelope_rows(lineage.pre_observation.payload, label="PRE")
        if pre_err:
            return _fail(prop, pre_err)
        assert pre_rows is not None
        pre_related, pre_rel_err = _nonzero_related(pre_rows, target=target)
        if pre_rel_err:
            return _fail(prop, pre_rel_err)
        if pre_related:
            return _fail(prop, "UNEXPECTED_RELATED_INSTRUMENT_POSITION_PRE")
    if delayed is not None:
        related_ts = _parse_utc(related.request_time_utc, label="RELATED")
        delayed_ts = _parse_utc(delayed.request_time_utc, label="DELAYED_ZERO")
        if related_ts is None or delayed_ts is None:
            return _not_proven(prop, "RELATED_OR_DELAYED_TIMESTAMP_MISSING")
        if related_ts < delayed_ts:
            return _fail(prop, "RELATED_OBSERVATION_STALE_BEFORE_DELAYED_ZERO")
    return _pass(prop, "UNFILTERED_NO_RELATED_NONZERO_AFTER_DELAYED_ZERO")


def _evaluate_p10(
    lineage: FlattenLineageSlotV1 | None,
    delayed: ObservationSlotV1 | None,
    pending: ObservationSlotV1 | None,
    related: ObservationSlotV1 | None,
) -> ConjunctVerdictV1:
    prop = "P10_TEMPORAL_ORDER"
    if lineage is None or delayed is None:
        return _not_proven(prop, "LINEAGE_OR_DELAYED_SLOT_MISSING")
    pre_ts = _parse_utc(lineage.pre_observation.request_time_utc, label="PRE")
    submit_ts = _parse_utc(lineage.submit_time_utc, label="SUBMIT")
    fill_ts = _parse_utc(lineage.fill_time_utc, label="FILL")
    delayed_ts = _parse_utc(delayed.request_time_utc, label="DELAYED_ZERO")
    if pre_ts is None or submit_ts is None or delayed_ts is None:
        return _not_proven(prop, "REQUIRED_TIMESTAMP_MISSING")
    if not (pre_ts < submit_ts < delayed_ts):
        return _fail(prop, "TEMPORAL_INVERSION_PRE_SUBMIT_DELAYED")
    if fill_ts is not None and not (submit_ts <= fill_ts < delayed_ts):
        return _fail(prop, "TEMPORAL_INVERSION_SUBMIT_FILL_DELAYED")
    if pending is not None:
        pending_ts = _parse_utc(pending.request_time_utc, label="PENDING")
        if pending_ts is None:
            return _not_proven(prop, "PENDING_TIMESTAMP_MISSING")
        if pending_ts < delayed_ts:
            return _fail(prop, "TEMPORAL_INVERSION_PENDING_BEFORE_DELAYED")
    if related is not None:
        related_ts = _parse_utc(related.request_time_utc, label="RELATED")
        if related_ts is None:
            return _not_proven(prop, "RELATED_TIMESTAMP_MISSING")
        if related_ts < delayed_ts:
            return _fail(prop, "TEMPORAL_INVERSION_RELATED_BEFORE_DELAYED")
    return _pass(prop, "PRE_LT_SUBMIT_LT_DELAYED_ZERO")


def _provenance_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
