"""Thin governed consumer adapters (no selection/strategy authority)."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.economic_md_input_producer_v1.constants_v1 import MARK_ENDPOINT_PATH, MARK_SOURCE_CLASS
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import RawMarkCandleV1
from src.ops.economic_md_input_producer_v1.validation_v1 import (
    select_finalized_contiguous_pt1m_marks_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    O4_AUTHORITATIVE_INTERVAL,
    RANKING_FINALIZED_PT1M_MARK_COUNT,
    SELECTION_AUTHORITY,
)


def landscape_readmodel_from_live_facts_v1(
    *,
    mark_px: str,
    live_mark_captured_at: str,
    ohlcv_freshness_state: str,
    non_authorizing: bool = True,
) -> dict[str, Any]:
    return {
        "schema_name": "landscape_public_md_adapter.v1",
        "non_authorizing": non_authorizing,
        "dashboard_authority_effect": "NONE",
        "live_mark_price": mark_px,
        "live_mark_captured_at": live_mark_captured_at,
        "freshness_state": ohlcv_freshness_state,
        "ranking_authority": SELECTION_AUTHORITY,
    }


def ranking_b05_adapter_from_finalized_pt1m_marks_v1(
    marks: Sequence[RawMarkCandleV1],
) -> dict[str, Any]:
    selected, codes = select_finalized_contiguous_pt1m_marks_v1(tuple(marks))
    ok = not codes and len(selected) == RANKING_FINALIZED_PT1M_MARK_COUNT
    return {
        "adapter": "b05_cap22_economic_md",
        "ranking_safe": ok,
        "failure_codes": list(codes),
        "finalized_pt1m_mark_count": len(selected),
        "required_count": RANKING_FINALIZED_PT1M_MARK_COUNT,
        "source_class": MARK_SOURCE_CLASS,
        "source_endpoint": MARK_ENDPOINT_PATH,
        "ohlcv_substitution": False,
        "marks": [m.to_dict() for m in selected],
    }


def finalized_facts_to_raw_mark_candles_v1(
    facts: Sequence[Mapping[str, Any]], *, venue_native_id: str, captured_at: str
) -> tuple[RawMarkCandleV1, ...]:
    rows: list[RawMarkCandleV1] = []
    for fact in facts:
        if fact.get("fact_kind") != "FinalizedPt1mMarkFactV1":
            continue
        rows.append(
            RawMarkCandleV1(
                venue_native_id=venue_native_id,
                ts_ms=str(fact["interval_start_ms"]),
                mark_px=str(fact["mark_px"]),
                confirm=str(fact.get("confirm") or "1"),
                receive_or_capture_timestamp=captured_at,
            )
        )
    return tuple(rows)


def o4_n_bars_envelope_from_historical_facts_v1(
    pt1h_bars: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "adapter": "o4_n_bars_pt1h",
        "authoritative_interval": O4_AUTHORITATIVE_INTERVAL,
        "pt1m_semantic_migration": False,
        "forward_fill": False,
        "bars": list(pt1h_bars),
    }


def research_optimizer_historical_adapter_v1(
    query_result: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "adapter": "research_optimizer_historical",
        "promotion_authority": "NONE",
        "live_ws_required": query_result.get("live_ws_required", False),
        "fact_count": len(query_result.get("facts") or []),
    }
