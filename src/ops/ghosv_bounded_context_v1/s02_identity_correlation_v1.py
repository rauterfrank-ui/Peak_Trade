"""S02 — identity correlation (explicit IDs only)."""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from src.ops.ghosv_bounded_context_v1.constants_v1 import (
    CORRELATION_CONFLICT,
    CORRELATION_EXPLICIT,
    CORRELATION_UNKNOWN,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import GhosvCorrelationGroupV1, GhosvEvidenceRecordV1


def correlate_evidence_v1(
    records: Sequence[GhosvEvidenceRecordV1],
) -> tuple[GhosvCorrelationGroupV1, ...]:
    by_trade: dict[str, list[GhosvEvidenceRecordV1]] = defaultdict(list)
    for rec in records:
        key = rec.trade_id.strip()
        if not key:
            continue
        by_trade[key].append(rec)

    groups: list[GhosvCorrelationGroupV1] = []
    for trade_id, items in sorted(by_trade.items()):
        client_ids = {r.client_order_id for r in items if r.client_order_id}
        exchange_ids = {r.exchange_order_id for r in items if r.exchange_order_id}
        instruments = {r.instrument_id for r in items if r.instrument_id}
        reasons: list[str] = []
        status = CORRELATION_EXPLICIT
        if len(client_ids) > 1:
            status = CORRELATION_CONFLICT
            reasons.append("CLIENT_ORDER_ID_CONFLICT")
        if len(exchange_ids) > 1:
            status = CORRELATION_CONFLICT
            reasons.append("EXCHANGE_ORDER_ID_CONFLICT")
        if len(instruments) > 1:
            status = CORRELATION_CONFLICT
            reasons.append("INSTRUMENT_ID_CONFLICT")
        if not client_ids and not exchange_ids:
            if status != CORRELATION_CONFLICT:
                status = CORRELATION_UNKNOWN
            reasons.append("NO_ORDER_IDENTITY")
        client_order_id = next(iter(client_ids), "")
        exchange_order_id = next(iter(exchange_ids), "")
        instrument_id = next(iter(instruments), "")
        groups.append(
            GhosvCorrelationGroupV1(
                trade_id=trade_id,
                instrument_id=instrument_id,
                client_order_id=client_order_id,
                exchange_order_id=exchange_order_id,
                status=status,
                record_event_ids=tuple(r.event_id for r in items),
                reason_codes=tuple(reasons),
            )
        )
    return tuple(groups)
