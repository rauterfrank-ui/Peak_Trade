"""Canonical UTC 15-minute PIT anchor parsing. No rounding. No as-of guessing."""

from __future__ import annotations

from datetime import datetime

from src.ops.cap22_append_only_15m_pit_persistence_v1.constants_v1 import (
    COLLECTION_ANCHOR_MINUTE_MODULUS,
    COLLECTION_CADENCE_ID,
)
from src.ops.cap22_append_only_15m_pit_persistence_v1.reason_codes_v1 import (
    Cap22AppendOnlyPitPersistenceFailureCodeV1,
)
from src.ops.cap22_historical_evidence_time_semantics_contract_v1 import (
    is_valid_pt1m_15m_anchor_utc,
)

CANONICAL_ANCHOR_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
CANONICAL_PATH_KEY_FORMAT = "%Y-%m-%dT%H%M%SZ"


class Cap22AppendOnlyPitPersistenceError(ValueError):
    """Fail-closed append-only PIT persistence error."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def parse_canonical_15m_anchor_utc(value: str) -> str:
    """Return the canonical RFC3339 Z anchor or fail closed.

    Only exact ``YYYY-MM-DDTHH:MM:00Z`` values on the ratified
    ``PT1M_15_MINUTE_ANCHORS_V1`` grid are accepted.
    """
    text = str(value or "").strip()
    if not text:
        raise Cap22AppendOnlyPitPersistenceError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.EVENT_TIME_MISSING.value
        )
    try:
        parsed = datetime.strptime(text, CANONICAL_ANCHOR_FORMAT)
    except ValueError as exc:
        raise Cap22AppendOnlyPitPersistenceError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.INVALID_ANCHOR.value,
            text,
        ) from exc
    if parsed.tzinfo is not None:
        raise Cap22AppendOnlyPitPersistenceError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.INVALID_ANCHOR.value,
            text,
        )
    if not is_valid_pt1m_15m_anchor_utc(
        minute=parsed.minute,
        second=parsed.second,
        microsecond=parsed.microsecond,
    ):
        raise Cap22AppendOnlyPitPersistenceError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.INVALID_ANCHOR.value,
            text,
        )
    canonical = parsed.strftime(CANONICAL_ANCHOR_FORMAT)
    if canonical != text:
        raise Cap22AppendOnlyPitPersistenceError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.INVALID_ANCHOR.value,
            text,
        )
    return canonical


def canonical_path_key_for_anchor(anchor: str) -> str:
    """Filesystem-safe deterministic key for a validated 15m UTC anchor."""
    parsed = datetime.strptime(
        parse_canonical_15m_anchor_utc(value=anchor), CANONICAL_ANCHOR_FORMAT
    )
    return parsed.strftime(CANONICAL_PATH_KEY_FORMAT)


def require_anchor_equals(*, expected: str, actual: str, field: str) -> str:
    """Fail closed when two timestamps are not the same canonical 15m anchor."""
    expected_canonical = parse_canonical_15m_anchor_utc(expected)
    try:
        actual_canonical = parse_canonical_15m_anchor_utc(actual)
    except Cap22AppendOnlyPitPersistenceError as exc:
        if exc.failure_code == Cap22AppendOnlyPitPersistenceFailureCodeV1.EVENT_TIME_MISSING.value:
            raise
        raise Cap22AppendOnlyPitPersistenceError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.EVENT_TIME_MISMATCH.value,
            f"{field}:{actual}",
        ) from exc
    if actual_canonical != expected_canonical:
        raise Cap22AppendOnlyPitPersistenceError(
            Cap22AppendOnlyPitPersistenceFailureCodeV1.EVENT_TIME_MISMATCH.value,
            f"{field}:{actual_canonical}!={expected_canonical}",
        )
    return expected_canonical


def cadence_id() -> str:
    return COLLECTION_CADENCE_ID


def anchor_minute_modulus() -> int:
    return COLLECTION_ANCHOR_MINUTE_MODULUS
