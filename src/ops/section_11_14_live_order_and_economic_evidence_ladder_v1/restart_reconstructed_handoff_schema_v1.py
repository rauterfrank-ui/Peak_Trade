"""Bound Peak_Trade Live durable pre-restart handoff schema.

This is a clarification of the already bound LIVE_RESTART_RECONSTRUCTED
identity equation. It does not invent a new Live policy. It does not write
productive runtime state.
"""

from __future__ import annotations

REQUIRED_HANDOFF_FIELDS: tuple[str, ...] = (
    "clOrdId",
    "ordId",
    "instId",
    "posSide",
    "pos",
)
OPTIONAL_TEMPORAL_FIELDS: tuple[str, ...] = (
    "captured_at_utc",
    "written_at_utc",
)
HANDOFF_DOCUMENT_CLASS = "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_V1"
HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET = True
VENUE_GET_ARTIFACT_NAMES: frozenset[str] = frozenset(
    {
        "GET_FILLS.raw.json",
        "GET_POSITIONS.raw.json",
        "GET_ORDER_STATUS.raw.json",
        "ACCOUNTING_RECONSTRUCTED_ADJUDICATION.json",
        "ACCOUNTING_IDENTITY.json",
    }
)
