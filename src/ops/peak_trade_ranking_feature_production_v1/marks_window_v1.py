"""Extract and re-validate B03 Input-2 mark windows from Economic-MD raw input.

Fail-closed: no implicit fill, no guessed marks, no stale cache substitution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from src.ops.economic_md_input_producer_v1.models_v1 import FinalizedPt1mMarkObservationV1
from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    MARK_COUNT,
    PT1M_STEP_MS,
)
from src.ops.peak_trade_ranking_feature_production_v1.reason_codes_v1 import (
    RankingFeatureProductionReasonCodeV1,
)


@dataclass(frozen=True)
class ContiguousFinalizedPt1mMarkWindowV1:
    mark_px: tuple[str, ...]
    event_timestamps: tuple[str, ...]
    as_of_event_time: str
    source_class: str
    source_endpoint: str
    receive_or_capture_timestamps: tuple[str, ...]


@dataclass(frozen=True)
class MarkWindowExtractionResultV1:
    ok: bool
    window: Optional[ContiguousFinalizedPt1mMarkWindowV1]
    reason_code: Optional[RankingFeatureProductionReasonCodeV1]


def _parse_ts_ms(raw: str) -> Optional[int]:
    text = str(raw or "").strip()
    if not text.isdigit():
        return None
    value = int(text)
    return value if value > 0 else None


def extract_contiguous_finalized_pt1m_mark_window_v1(
    marks: Sequence[FinalizedPt1mMarkObservationV1],
) -> MarkWindowExtractionResultV1:
    if not marks:
        return MarkWindowExtractionResultV1(
            ok=False,
            window=None,
            reason_code=RankingFeatureProductionReasonCodeV1.MISSING_MARK_PRICE,
        )
    if len(marks) < MARK_COUNT:
        return MarkWindowExtractionResultV1(
            ok=False,
            window=None,
            reason_code=RankingFeatureProductionReasonCodeV1.INSUFFICIENT_PT1M_MARK_WARMUP,
        )

    trailing = tuple(marks[-MARK_COUNT:])
    parsed_ts: list[int] = []
    for row in trailing:
        if str(row.finalization_status).strip().upper() != "FINALIZED":
            return MarkWindowExtractionResultV1(
                ok=False,
                window=None,
                reason_code=RankingFeatureProductionReasonCodeV1.NON_FINALIZED_MARK,
            )
        if row.mark_px is None or not str(row.mark_px).strip():
            return MarkWindowExtractionResultV1(
                ok=False,
                window=None,
                reason_code=RankingFeatureProductionReasonCodeV1.MISSING_MARK_PRICE,
            )
        ts = _parse_ts_ms(row.event_timestamp)
        if ts is None:
            return MarkWindowExtractionResultV1(
                ok=False,
                window=None,
                reason_code=RankingFeatureProductionReasonCodeV1.NON_CONTIGUOUS_PT1M,
            )
        parsed_ts.append(ts)

    for prev, cur in zip(parsed_ts, parsed_ts[1:]):
        if cur - prev != PT1M_STEP_MS:
            return MarkWindowExtractionResultV1(
                ok=False,
                window=None,
                reason_code=RankingFeatureProductionReasonCodeV1.NON_CONTIGUOUS_PT1M,
            )

    source_classes = {str(row.source_class).strip() for row in trailing}
    source_endpoints = {str(row.source_endpoint).strip() for row in trailing}
    if len(source_classes) != 1 or not next(iter(source_classes)):
        return MarkWindowExtractionResultV1(
            ok=False,
            window=None,
            reason_code=RankingFeatureProductionReasonCodeV1.COMPUTE_ERROR,
        )
    if len(source_endpoints) != 1 or not next(iter(source_endpoints)):
        return MarkWindowExtractionResultV1(
            ok=False,
            window=None,
            reason_code=RankingFeatureProductionReasonCodeV1.COMPUTE_ERROR,
        )

    window = ContiguousFinalizedPt1mMarkWindowV1(
        mark_px=tuple(str(row.mark_px) for row in trailing),
        event_timestamps=tuple(str(row.event_timestamp) for row in trailing),
        as_of_event_time=str(trailing[-1].event_timestamp),
        source_class=next(iter(source_classes)),
        source_endpoint=next(iter(source_endpoints)),
        receive_or_capture_timestamps=tuple(
            str(row.receive_or_capture_timestamp) for row in trailing
        ),
    )
    return MarkWindowExtractionResultV1(ok=True, window=window, reason_code=None)
