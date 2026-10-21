"""Provenance and completeness facts for already captured GET evidence.

AUTHORITY_EFFECT=NONE. This module does not call a venue, read a clock, or
admit evidence. Account UID provenance is the ``uid`` on
``/api/v5/account/config`` data[0], the same field the CURRENT account-config
extractor reads. ``acctLv`` and ``posMode`` are not account identity.

Venue time is a single positive row ``uTime`` or ``cTime``. Capture time stays
on the capture record. The ratified freshness policy has no threshold for these
private GETs, so none is applied. No CURRENT contract names a positive
pagination terminal for the six admission GETs. Account-flat and REST/WS
consistency stay UNPROVEN.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from src.ops.h1_get_evidence_admission_v1.constants_v1 import (
    CONTRACT_PAGINATION_TERMINAL_SOURCES,
    ENDPOINT_ACCOUNT_CONFIG,
    PRIVATE_GET_FRESHNESS_SOURCE_TYPE,
    REASON_ACCOUNT_IDENTITY_ABSENT,
    REASON_ACCOUNT_IDENTITY_MALFORMED,
    REASON_ACCOUNT_IDENTITY_MISMATCH,
    REASON_DUPLICATE_FILL_CONFLICT,
    REASON_FILL_TIMESTAMP_MALFORMED,
    REASON_FILL_TRADE_ID_ABSENT,
    REASON_LATE_FILL_OUTSIDE_WINDOW,
    REASON_RESPONSE_MALFORMED,
    REASON_VENUE_TIMESTAMP_ABSENT,
    REASON_VENUE_TIMESTAMP_CONTRADICTION,
    REASON_VENUE_TIMESTAMP_NOT_PAYLOAD_WITNESS,
)
from src.ops.okx_captured_at_freshness_policy_v1 import load_freshness_policy_v1

_VENUE_TIME_FIELDS = ("uTime", "cTime")
_UID_FIELDS = ("uid", "mainUid")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_ms(value: object) -> int | None:
    if isinstance(value, bool) or isinstance(value, float):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.isdigit():
        parsed = int(value)
        return parsed if parsed > 0 else None
    return None


def venue_timestamp_from_payload_v1(payload: Mapping[str, Any]) -> int | None:
    """Return one positive uTime/cTime. Zero, absent, or disagreeing values stay unset."""
    found: set[int] = set()
    data = payload.get("data")
    if not isinstance(data, list):
        return None
    for row in data:
        if not isinstance(row, Mapping):
            continue
        for key in _VENUE_TIME_FIELDS:
            if key not in row:
                continue
            parsed = _positive_ms(row.get(key))
            if parsed is not None:
                found.add(parsed)
    if len(found) == 1:
        return next(iter(found))
    return None


def bind_venue_and_capture_clocks_v1(
    payload: object,
    supplied_venue_ms: object,
) -> tuple[int | None, set[str]]:
    """Bind venue time only from the payload. A detached integer is not a witness."""
    reasons: set[str] = set()
    derived = venue_timestamp_from_payload_v1(payload) if isinstance(payload, Mapping) else None
    supplied_ok = _is_int(supplied_venue_ms)
    if derived is None:
        reasons.add(REASON_VENUE_TIMESTAMP_ABSENT)
        if supplied_venue_ms is not None:
            reasons.add(REASON_VENUE_TIMESTAMP_NOT_PAYLOAD_WITNESS)
        return None, reasons
    if supplied_venue_ms is not None and (not supplied_ok or supplied_venue_ms != derived):
        reasons.add(REASON_VENUE_TIMESTAMP_CONTRADICTION)
    return derived, reasons


def private_get_freshness_ratified_v1() -> bool:
    """True only when the ratified policy names the private-GET source type."""
    policy = load_freshness_policy_v1()
    thresholds = policy.get("freshness_thresholds_seconds")
    if not isinstance(thresholds, Mapping):
        return False
    return PRIVATE_GET_FRESHNESS_SOURCE_TYPE in thresholds


def pagination_contract_witness_v1(terminal: object, source: object) -> bool:
    """Positive terminal only for an explicit CURRENT source. The allowlist is empty."""
    return (
        terminal is True
        and isinstance(source, str)
        and source in CONTRACT_PAGINATION_TERMINAL_SOURCES
    )


def account_wide_position_completeness_proven_v1() -> bool:
    """CURRENT position GETs are instrument- or instType-scoped, not account-wide."""
    return False


def parse_exact_uid_v1(value: object) -> tuple[str | None, bool]:
    """Accept the CURRENT string-or-int uid shape. Bool and blank values are malformed."""
    if isinstance(value, bool):
        return None, True
    if isinstance(value, int):
        value = str(value)
    if not isinstance(value, str) or value == "" or value != value.strip():
        return None, True
    return value, False


def observed_config_uid_v1(payload: object) -> tuple[str | None, set[str]]:
    """UID origin is account-config data[0].uid. Mode fields and later rows cannot mint it."""
    reasons: set[str] = set()
    if not isinstance(payload, Mapping):
        reasons.add(REASON_RESPONSE_MALFORMED)
        reasons.add(REASON_ACCOUNT_IDENTITY_ABSENT)
        return None, reasons
    data = payload.get("data")
    if not isinstance(data, list):
        reasons.add(REASON_RESPONSE_MALFORMED)
        reasons.add(REASON_ACCOUNT_IDENTITY_ABSENT)
        return None, reasons
    if not data or not isinstance(data[0], Mapping):
        reasons.add(REASON_ACCOUNT_IDENTITY_ABSENT)
        if data and not isinstance(data[0], Mapping):
            reasons.add(REASON_ACCOUNT_IDENTITY_MALFORMED)
        return None, reasons
    row = data[0]
    uid: str | None
    if "uid" not in row:
        reasons.add(REASON_ACCOUNT_IDENTITY_ABSENT)
        uid = None
    else:
        uid, malformed = parse_exact_uid_v1(row.get("uid"))
        if malformed or uid is None:
            reasons.add(REASON_ACCOUNT_IDENTITY_MALFORMED)
            reasons.add(REASON_ACCOUNT_IDENTITY_ABSENT)
            uid = None
    reasons.update(_main_uid_reasons(row, uid))
    for extra in data[1:]:
        if not isinstance(extra, Mapping):
            reasons.add(REASON_ACCOUNT_IDENTITY_MALFORMED)
            continue
        if "uid" in extra:
            extra_uid, malformed = parse_exact_uid_v1(extra.get("uid"))
            if malformed or extra_uid is None:
                reasons.add(REASON_ACCOUNT_IDENTITY_MALFORMED)
            elif uid is None or extra_uid != uid:
                reasons.add(REASON_ACCOUNT_IDENTITY_MISMATCH)
        reasons.update(_main_uid_reasons(extra, uid))
    return uid, reasons


def _main_uid_reasons(row: Mapping[str, Any], uid: str | None) -> set[str]:
    if "mainUid" not in row:
        return set()
    main_uid, malformed = parse_exact_uid_v1(row.get("mainUid"))
    reasons: set[str] = set()
    if malformed or main_uid is None:
        reasons.add(REASON_ACCOUNT_IDENTITY_MALFORMED)
    elif uid is None or main_uid != uid:
        reasons.add(REASON_ACCOUNT_IDENTITY_MISMATCH)
    return reasons


def foreign_uid_reasons_v1(payload: object, config_uid: str | None) -> set[str]:
    """A uid on any other GET must match config. Its absence does not mint or erase identity."""
    reasons: set[str] = set()
    if payload is None:
        return reasons
    if not isinstance(payload, Mapping):
        reasons.add(REASON_RESPONSE_MALFORMED)
        return reasons
    data = payload.get("data")
    if data is None:
        return reasons
    if not isinstance(data, list):
        reasons.add(REASON_RESPONSE_MALFORMED)
        return reasons
    found: set[str] = set()
    for row in data:
        if not isinstance(row, Mapping):
            continue
        for key in _UID_FIELDS:
            if key not in row:
                continue
            parsed, malformed = parse_exact_uid_v1(row.get(key))
            if malformed or parsed is None:
                reasons.add(REASON_ACCOUNT_IDENTITY_MALFORMED)
            else:
                found.add(parsed)
    if not found:
        return reasons
    if config_uid is None or found != {config_uid}:
        reasons.add(REASON_ACCOUNT_IDENTITY_MISMATCH)
    return reasons


def payload_claims_private_ws_v1(payload: object) -> bool:
    """OKX private WS envelopes are not REST consistency evidence."""
    if not isinstance(payload, Mapping):
        return False
    arg = payload.get("arg")
    return isinstance(arg, Mapping) and "channel" in arg


def config_endpoint_v1() -> str:
    return ENDPOINT_ACCOUNT_CONFIG


def _canonical_row(row: Mapping[str, Any]) -> str:
    return json.dumps(dict(row), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def classify_fills_v1(
    rows: object,
    *,
    window_start_ms: object,
    window_end_ms: object,
    bounds_ok: bool,
) -> tuple[int, set[str]]:
    """Count contradictory fills. No freshness threshold is applied here."""
    reasons: set[str] = set()
    if not isinstance(rows, list):
        return 0, reasons
    unique: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            reasons.add(REASON_RESPONSE_MALFORMED)
            continue
        trade_id = row.get("tradeId")
        if not isinstance(trade_id, str) or trade_id == "" or trade_id != trade_id.strip():
            reasons.add(REASON_FILL_TRADE_ID_ABSENT)
            continue
        if "fillTime" in row:
            fill_time = row.get("fillTime")
            if not _is_int(fill_time):
                reasons.add(REASON_FILL_TIMESTAMP_MALFORMED)
            elif bounds_ok and (fill_time < window_start_ms or fill_time > window_end_ms):
                reasons.add(REASON_LATE_FILL_OUTSIDE_WINDOW)
        try:
            canonical = _canonical_row(row)
        except TypeError:
            reasons.add(REASON_RESPONSE_MALFORMED)
            continue
        previous = unique.get(trade_id)
        if previous is None:
            unique[trade_id] = canonical
        elif previous != canonical:
            reasons.add(REASON_DUPLICATE_FILL_CONFLICT)
    return len(unique), reasons
