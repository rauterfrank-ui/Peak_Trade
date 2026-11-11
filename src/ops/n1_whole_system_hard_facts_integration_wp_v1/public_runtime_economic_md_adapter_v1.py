"""Bridge durable public-runtime facts → Economic-MD raw input (real observation path)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping

from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
)
from src.ops.economic_md_input_producer_v1.reason_codes_v1 import EconomicMdFailureCodeV1
from src.ops.economic_md_input_producer_v1.purpose_admission_v1 import (
    PublicFactPurposePolicyV1,
    admit_public_facts_for_purpose_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.historical_query_v1 import (
    query_historical_facts_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.canonical_fact_decoder_v1 import (
    canonical_fact_source_v1,
    fact_capture_timestamp_v1,
    fact_event_time_ms_v1,
    capture_order_key_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import MARK_HISTORY_CANDLES_PATH
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import InstrumentRefV1, fact_digest
from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
    PublicRestRecoveryError,
    RestGetJson,
    collect_bound_rest_pt1m_mark_window_v1,
)


@dataclass(frozen=True)
class BoundRankingMarkWindowV1:
    instrument_ref: InstrumentRefV1
    fact_digests: frozenset[str]
    collection_started_at_unix: float
    collection_completed_at_unix: float


def persist_bound_ranking_mark_window_v1(
    *, store_root: Path, fetch_json: RestGetJson, instrument_ref: InstrumentRefV1, session_id: str
) -> BoundRankingMarkWindowV1:
    """Validate the complete page before writing and retain the exact durable rows for B05."""
    facts, started, captured = collect_bound_rest_pt1m_mark_window_v1(
        fetch_json, instrument_ref=instrument_ref, session_id=session_id
    )
    native = instrument_ref.venue_native_id
    paths = default_store_paths_v1(store_root)
    window = {fact.interval_start_ms: fact.to_dict() for fact in facts}
    instrument = instrument_ref.to_dict()
    existing = query_historical_facts_v1(
        store_root, venue_native_id=native, fact_kind="FinalizedPt1mMarkFactV1"
    )
    reuse: dict[int, str] = {}
    for payload in existing.facts:
        interval = payload.get("interval_start_ms")
        provenance = payload.get("provenance") or {}
        if (
            payload.get("instrument") != instrument
            or type(interval) is not int
            or interval not in window
            or not isinstance(provenance, Mapping)
            or provenance.get("endpoint_or_channel") != MARK_HISTORY_CANDLES_PATH
            or not provenance.get("raw_payload_digest")
        ):
            continue
        candidate = window[interval]
        try:
            matches = (
                payload.get("confirm") == "1"
                and fact_event_time_ms_v1(payload) == interval
                and Decimal(str(payload.get("mark_px"))) == Decimal(candidate["mark_px"])
                and capture_order_key_v1(fact_capture_timestamp_v1(payload))
                <= capture_order_key_v1(fact_capture_timestamp_v1(candidate))
            )
        except (ValueError, InvalidOperation) as exc:
            raise PublicRestRecoveryError("PUBLIC_PT1M_STORED_FACT_CONFLICT") from exc
        if not matches:
            raise PublicRestRecoveryError("PUBLIC_PT1M_STORED_FACT_CONFLICT")
        reuse.setdefault(interval, fact_digest(payload))

    digests = {
        reuse[interval] if interval in reuse else append_fact_v1(paths, payload).fact_digest
        for interval, payload in window.items()
    }
    return BoundRankingMarkWindowV1(instrument_ref, frozenset(digests), started, captured)


@dataclass(frozen=True)
class PublicRuntimeEconomicMdPublicSourceV1:
    """Reads finalized public facts from a public MD runtime store (no www fallback)."""

    store_root: Path
    admission_policy: PublicFactPurposePolicyV1 | None = None
    as_of_ms: int | None = None
    bound_mark_window: BoundRankingMarkWindowV1 | None = None

    def collect_instrument_raw_input_v1(
        self, *, venue_native_id: str
    ) -> InstrumentPublicMdBundleV1:
        hist = query_historical_facts_v1(self.store_root, venue_native_id=venue_native_id)
        facts = hist.facts
        window = self.bound_mark_window
        if window is not None and venue_native_id == window.instrument_ref.venue_native_id:
            # This instrument is ranked from the verified page even if the same
            # store still contains older windows or other mapping generations.
            marks_by_digest = {
                fact_digest(fact): fact
                for fact in facts
                if fact.get("fact_kind") == "FinalizedPt1mMarkFactV1"
            }
            if not window.fact_digests <= marks_by_digest.keys():
                raise ValueError("PUBLIC_PT1M_BOUND_WINDOW_READBACK_UNPROVEN")
            facts = tuple(
                f for f in facts if f.get("fact_kind") != "FinalizedPt1mMarkFactV1"
            ) + tuple(marks_by_digest[digest] for digest in sorted(window.fact_digests))
        if self.admission_policy is not None or self.as_of_ms is not None:
            facts = admit_public_facts_for_purpose_v1(
                tuple(
                    f
                    for f in facts
                    if f.get("fact_kind") in {"FinalizedPt1mMarkFactV1", "BestBidAskFactV1"}
                ),
                policy=self.admission_policy,
                purpose="RANKING",
                consumer="PublicRuntimeEconomicMdPublicSourceV1",
                venue_native_id=venue_native_id,
                as_of_ms=self.as_of_ms,
            )
        marks: list[RawMarkCandleV1] = []
        ticker: RawTickerQuoteV1 | None = None
        ticker_key = None
        for fact in facts:
            inst = fact.get("instrument") if isinstance(fact, dict) else None
            vid = str((inst or {}).get("venue_native_id") or "")
            if vid != venue_native_id:
                continue
            kind = str(fact.get("fact_kind") or "")
            if kind == "FinalizedPt1mMarkFactV1":
                marks.append(
                    RawMarkCandleV1(
                        venue_native_id=venue_native_id,
                        ts_ms=str(fact.get("interval_start_ms") or ""),
                        mark_px=str(fact.get("mark_px") or ""),
                        confirm=str(fact.get("confirm", "")),
                        receive_or_capture_timestamp=fact_capture_timestamp_v1(fact),
                        **(canonical_fact_source_v1(fact) if "timestamps" in fact else {}),
                    )
                )
            elif kind == "BestBidAskFactV1":
                capture = fact_capture_timestamp_v1(fact)
                event = fact_event_time_ms_v1(fact)
                if "timestamps" in fact:
                    bid_px = fact.get("bid_px")
                    ask_px = fact.get("ask_px")
                else:
                    bids = fact.get("bids") or []
                    asks = fact.get("asks") or []
                    bid_px = str(bids[0][0]) if bids else None
                    ask_px = str(asks[0][0]) if asks else None
                quote = RawTickerQuoteV1(
                    venue_native_id=venue_native_id,
                    bid_px=bid_px,
                    ask_px=ask_px,
                    ticker_event_timestamp=str(event),
                    capture_or_receive_timestamp=capture,
                    **(canonical_fact_source_v1(fact) if "timestamps" in fact else {}),
                )
                key = (event, capture_order_key_v1(capture))
                if ticker_key is None or key > ticker_key:
                    ticker, ticker_key = quote, key
                elif key == ticker_key and quote != ticker:
                    raise ValueError("conflicting public quotes at same event and capture")
        if not marks:
            return InstrumentPublicMdBundleV1(
                venue_native_id=venue_native_id,
                marks=(),
                ticker=ticker,
                failure_codes=(EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value,),
            )
        marks.sort(key=lambda m: int(m.ts_ms))
        return InstrumentPublicMdBundleV1(
            venue_native_id=venue_native_id,
            marks=tuple(marks),
            ticker=ticker,
            failure_codes=(),
        )
