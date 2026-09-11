"""Bounded tests for the Cap-2.2 Economic-MD MVR raw-input producer."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    ALLOWED_PUBLIC_GET_PATHS,
    CALL_GRAPH,
    CAPABILITY_ID,
    ECONOMIC_MD_PRODUCER_IMPLEMENTED,
    ECONOMIC_MD_PRODUCER_MAY_APPLY_POLICY_A,
    ECONOMIC_MD_PRODUCER_MAY_DEFINE_ACTIVE_SET,
    ECONOMIC_MD_PRODUCER_MAY_DEFINE_TOP20,
    ECONOMIC_MD_PRODUCER_MAY_RANK,
    ECONOMIC_MD_PRODUCER_MAY_SELECT,
    ECONOMIC_MD_PRODUCER_MAY_TRIGGER_EXECUTION,
    ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED,
    ECONOMIC_RANK_ACTIVATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    LIBRARY_REUSE_AUTHORITY_TRANSFER,
    MARK_ENDPOINT_PATH,
    MINIMUM_FINALIZED_PT1M_MARKS,
    NO_IMPLICIT_FILL,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    TICKER_ENDPOINT_PATH,
)
from src.ops.economic_md_input_producer_v1.models_v1 import EconomicMdInputSnapshotV1
from src.ops.economic_md_input_producer_v1.producer_v1 import (
    produce_economic_md_input_snapshot_v1,
    replay_economic_md_snapshot_v1,
    run_economic_md_input_producer_v1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    EconomicMdPublicSourceError,
    InjectedEconomicMdPublicSourceV1,
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
    assert_public_get_path_allowed_v1,
)
from src.ops.economic_md_input_producer_v1.reason_codes_v1 import EconomicMdFailureCodeV1
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)

REPO = Path(__file__).resolve().parents[2]
REPO_SHA = "ecc74a93cada6a8d605107d3958bd510f6d5bb19"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"
START_UNIX = 1_700_000_200.0
COMPLETE_UNIX = 1_700_000_260.0
BASE_TS_MS = 1_700_000_000_000
CAPTURE_TS = "1700000260000"

PRODUCER_SRC = REPO / "src/ops/economic_md_input_producer_v1/producer_v1.py"
PUBLIC_MD_SRC = REPO / "src/ops/economic_md_input_producer_v1/public_md_source_v1.py"


def _perp(
    inst_id: str = "ETH-USDT-SWAP",
    *,
    state: str = "live",
    tick: str = "0.01",
    lot: str = "1",
    min_sz: str = "1",
    ct_val: str = "0.01",
    ct_val_ccy: str = "ETH",
    base: str = "ETH",
    quote: str = "USDT",
    settle: str = "USDT",
    ct_type: str = "linear",
    inst_type: str = "SWAP",
    exp: str = "",
) -> dict:
    return {
        "instId": inst_id,
        "instType": inst_type,
        "state": state,
        "baseCcy": base,
        "quoteCcy": quote,
        "settleCcy": settle,
        "ctType": ct_type,
        "ctVal": ct_val,
        "ctValCcy": ct_val_ccy,
        "tickSz": tick,
        "lotSz": lot,
        "minSz": min_sz,
        "uly": f"{base}-{quote}",
        "expTime": exp,
    }


def _universe_snapshot(rows: list[dict]) -> dict:
    mark_ids = [r["instId"] for r in rows]
    return produce_governed_futures_universe_v1(
        source_payload={"code": "0", "msg": "", "data": rows},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [{"instId": i, "markPx": "100.5"} for i in mark_ids],
        },
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    ).snapshot.to_dict()


def _eligible_ids(universe: dict) -> list[tuple[str, str]]:
    return [
        (str(row["canonical_instrument_id"]), str(row["venue_native_inst_id"]))
        for row in universe["instruments"]
        if row.get("eligibility") is True
    ]


def _marks(
    n: int, *, confirm: str = "1", skip_index: int | None = None
) -> tuple[RawMarkCandleV1, ...]:
    rows: list[RawMarkCandleV1] = []
    for i in range(n):
        if skip_index is not None and i == skip_index:
            continue
        rows.append(
            RawMarkCandleV1(
                venue_native_id="ETH-USDT-SWAP",
                ts_ms=str(BASE_TS_MS + i * 60_000),
                mark_px=str(100 + i),
                confirm=confirm if i != n - 1 or confirm == "1" else confirm,
                receive_or_capture_timestamp=CAPTURE_TS,
            )
        )
    return tuple(rows)


def _marks_with_last_unfinalized(n: int) -> tuple[RawMarkCandleV1, ...]:
    rows = list(_marks(n))
    last = rows[-1]
    rows[-1] = RawMarkCandleV1(
        venue_native_id=last.venue_native_id,
        ts_ms=last.ts_ms,
        mark_px=last.mark_px,
        confirm="0",
        receive_or_capture_timestamp=last.receive_or_capture_timestamp,
    )
    return tuple(rows)


def _ticker(
    *,
    bid: str | None = "100.1",
    ask: str | None = "100.3",
    event_ts: str | None = "1700000259000",
) -> RawTickerQuoteV1:
    return RawTickerQuoteV1(
        venue_native_id="ETH-USDT-SWAP",
        bid_px=bid,
        ask_px=ask,
        ticker_event_timestamp=event_ts,
        capture_or_receive_timestamp=CAPTURE_TS,
    )


def _bundle(
    *,
    marks: tuple[RawMarkCandleV1, ...] | None = None,
    ticker: RawTickerQuoteV1 | None = None,
    venue_native_id: str = "ETH-USDT-SWAP",
) -> InstrumentPublicMdBundleV1:
    return InstrumentPublicMdBundleV1(
        venue_native_id=venue_native_id,
        marks=_marks(MINIMUM_FINALIZED_PT1M_MARKS) if marks is None else marks,
        ticker=_ticker() if ticker is None else ticker,
    )


def _source_for(universe: dict, bundles: dict[str, InstrumentPublicMdBundleV1] | None = None):
    eligible = _eligible_ids(universe)
    built = dict(bundles or {})
    if not built:
        for _canonical, venue_id in eligible:
            built[venue_id] = _bundle(venue_native_id=venue_id)
    return InjectedEconomicMdPublicSourceV1(built)


def _produce(universe: dict, source: InjectedEconomicMdPublicSourceV1):
    return produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe,
        public_md_source=source,
        collection_started_at_unix=START_UNIX,
        collection_completed_at_unix=COMPLETE_UNIX,
    )


def test_schema_round_trip_and_digest_deterministic() -> None:
    universe = _universe_snapshot([_perp()])
    produced = _produce(universe, _source_for(universe))
    assert produced.ok is True
    snap = produced.snapshot
    round_trip = EconomicMdInputSnapshotV1.from_dict(json.loads(json.dumps(snap.to_dict())))
    assert round_trip.to_dict() == snap.to_dict()
    assert round_trip.payload_digest == snap.payload_digest
    assert round_trip.compute_payload_digest() == snap.payload_digest
    again = _produce(universe, _source_for(universe))
    assert again.snapshot.economic_input_snapshot_id == snap.economic_input_snapshot_id
    assert again.snapshot.payload_digest == snap.payload_digest


def test_cap21_ineligible_cannot_be_injected() -> None:
    universe = _universe_snapshot(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("BTC-USDT-SWAP", base="BTC", ct_val_ccy="BTC"),
        ]
    )
    eligible = _eligible_ids(universe)
    assert all(vid != "BTC-USDT-SWAP" for _cid, vid in eligible)
    btc_bundle = _bundle(venue_native_id="BTC-USDT-SWAP")
    eth_id = eligible[0][1]
    source = InjectedEconomicMdPublicSourceV1(
        {eth_id: _bundle(venue_native_id=eth_id), "BTC-USDT-SWAP": btc_bundle}
    )
    produced = _produce(universe, source)
    ids = [row.canonical_instrument_id for row in produced.snapshot.instruments]
    venue_ids = [row.venue_native_id for row in produced.snapshot.instruments]
    assert "BTC-USDT-SWAP" not in venue_ids
    assert all("btc" not in item.lower() for row in produced.snapshot.instruments for item in ids)
    extra = produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe,
        public_md_source=source,
        collection_started_at_unix=START_UNIX,
        collection_completed_at_unix=COMPLETE_UNIX,
        extra_instrument_ids=("BTC-USDT-SWAP",),
    )
    assert extra.ok is False
    assert EconomicMdFailureCodeV1.INSTRUMENT_NOT_IN_CAP21_ELIGIBLE_SET.value in extra.failure_codes


def test_sixty_marks_not_rankable_sixty_one_finalized_eligible() -> None:
    universe = _universe_snapshot([_perp()])
    venue_id = _eligible_ids(universe)[0][1]
    short = _produce(
        universe,
        InjectedEconomicMdPublicSourceV1(
            {venue_id: _bundle(marks=_marks(60), venue_native_id=venue_id)}
        ),
    )
    assert short.snapshot.instrument_count_rankable_raw_input == 0
    assert short.snapshot.instruments[0].raw_input_eligible is False
    assert (
        EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value
        in short.snapshot.instruments[0].exclusion_reason_codes
        or EconomicMdFailureCodeV1.NON_FINALIZED_MARK.value
        in short.snapshot.instruments[0].exclusion_reason_codes
    )
    full = _produce(universe, _source_for(universe))
    assert full.snapshot.instrument_count_rankable_raw_input == 1
    assert full.snapshot.instruments[0].raw_input_eligible is True
    assert len(full.snapshot.instruments[0].finalized_pt1m_marks) == 61


def test_missing_mark_and_non_finalized_fail_closed() -> None:
    universe = _universe_snapshot([_perp()])
    venue_id = _eligible_ids(universe)[0][1]
    gapped = _produce(
        universe,
        InjectedEconomicMdPublicSourceV1(
            {
                venue_id: _bundle(
                    marks=_marks(62, skip_index=10),
                    venue_native_id=venue_id,
                )
            }
        ),
    )
    assert gapped.snapshot.instruments[0].raw_input_eligible is False
    assert (
        EconomicMdFailureCodeV1.MISSING_MARK_BAR_NO_IMPLICIT_FILL.value
        in gapped.snapshot.instruments[0].exclusion_reason_codes
        or EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value
        in gapped.snapshot.instruments[0].exclusion_reason_codes
    )
    unfinalized = _produce(
        universe,
        InjectedEconomicMdPublicSourceV1(
            {
                venue_id: _bundle(
                    marks=_marks_with_last_unfinalized(61),
                    venue_native_id=venue_id,
                )
            }
        ),
    )
    assert unfinalized.snapshot.instruments[0].raw_input_eligible is False
    assert (
        EconomicMdFailureCodeV1.NON_FINALIZED_MARK.value
        in unfinalized.snapshot.instruments[0].exclusion_reason_codes
        or EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value
        in unfinalized.snapshot.instruments[0].exclusion_reason_codes
    )


def test_bid_ask_fail_closed_and_raw_quotes_persisted() -> None:
    universe = _universe_snapshot([_perp()])
    venue_id = _eligible_ids(universe)[0][1]

    def _run(ticker: RawTickerQuoteV1):
        return _produce(
            universe,
            InjectedEconomicMdPublicSourceV1(
                {venue_id: _bundle(ticker=ticker, venue_native_id=venue_id)}
            ),
        )

    missing_bid = _run(_ticker(bid=None))
    assert missing_bid.snapshot.instruments[0].raw_input_eligible is False
    assert (
        EconomicMdFailureCodeV1.MISSING_BIDPX.value
        in missing_bid.snapshot.instruments[0].exclusion_reason_codes
    )
    missing_ask = _run(_ticker(ask=None))
    assert (
        EconomicMdFailureCodeV1.MISSING_ASKPX.value
        in missing_ask.snapshot.instruments[0].exclusion_reason_codes
    )
    zero = _run(_ticker(bid="0", ask="100.2"))
    assert (
        EconomicMdFailureCodeV1.NON_POSITIVE_BIDPX.value
        in zero.snapshot.instruments[0].exclusion_reason_codes
    )
    negative_ask = _run(_ticker(bid="100.1", ask="-1"))
    assert (
        EconomicMdFailureCodeV1.NON_POSITIVE_ASKPX.value
        in negative_ask.snapshot.instruments[0].exclusion_reason_codes
    )
    crossed = _run(_ticker(bid="101", ask="100"))
    assert crossed.snapshot.instruments[0].raw_input_eligible is False
    assert (
        EconomicMdFailureCodeV1.CROSSED_MARKET_BID_GT_ASK.value
        in crossed.snapshot.instruments[0].exclusion_reason_codes
    )
    assert crossed.snapshot.instruments[0].ticker is not None
    assert crossed.snapshot.instruments[0].ticker.bid_px == "101"
    assert crossed.snapshot.instruments[0].ticker.ask_px == "100"
    ok = _produce(universe, _source_for(universe))
    ticker = ok.snapshot.instruments[0].ticker
    assert ticker is not None
    assert ticker.bid_px == "100.1"
    assert ticker.ask_px == "100.3"


def test_no_ranking_selection_policy_or_execution_authority() -> None:
    universe = _universe_snapshot([_perp()])
    produced = _produce(universe, _source_for(universe))
    blob = json.dumps(produced.snapshot.to_dict())
    payload = produced.snapshot.to_dict()
    assert "total_score" not in blob
    assert "ranked_candidates" not in payload
    assert "top20_candidate_context" not in blob.lower()
    assert payload.get("instrument_count_rankable_raw_input") == 1
    assert "rank" not in payload
    assert produced.snapshot.authority["ECONOMIC_MD_PRODUCER_MAY_RANK"] is False
    assert produced.snapshot.authority["ECONOMIC_MD_PRODUCER_MAY_SELECT"] is False
    assert produced.snapshot.authority["ECONOMIC_MD_PRODUCER_MAY_DEFINE_TOP20"] is False
    assert produced.snapshot.authority["ECONOMIC_MD_PRODUCER_MAY_APPLY_POLICY_A"] is False
    assert produced.snapshot.authority["ECONOMIC_MD_PRODUCER_MAY_TRIGGER_EXECUTION"] is False
    assert ECONOMIC_MD_PRODUCER_MAY_RANK is False
    assert ECONOMIC_MD_PRODUCER_MAY_SELECT is False
    assert ECONOMIC_MD_PRODUCER_MAY_DEFINE_TOP20 is False
    assert ECONOMIC_MD_PRODUCER_MAY_APPLY_POLICY_A is False
    assert ECONOMIC_MD_PRODUCER_MAY_DEFINE_ACTIVE_SET is False
    assert ECONOMIC_MD_PRODUCER_MAY_TRIGGER_EXECUTION is False
    assert ECONOMIC_RANK_ACTIVATED is False
    assert ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED is False
    assert ECONOMIC_MD_PRODUCER_IMPLEMENTED is True
    source = PRODUCER_SRC.read_text(encoding="utf-8")
    assert "productive_futures_ranking_producer_v1.ranking_v1" not in source
    assert "evaluate_policy_a_v1" not in source
    assert "src.execution" not in source
    assert "live_authorized=True" not in source
    md_src = PUBLIC_MD_SRC.read_text(encoding="utf-8")
    assert "single_future_canonical_runtime_public_md" not in md_src
    assert "canonical_volatility_numeric_max_age_preregistered" not in md_src
    assert "section_11_13_5_live_canary" not in md_src
    assert LIBRARY_REUSE_AUTHORITY_TRANSFER is False
    assert "ranking" in FORBIDDEN_CALL_GRAPH_TARGETS


def test_offline_replay_requires_no_network_and_survives_round_trip(tmp_path: Path) -> None:
    universe = _universe_snapshot([_perp()])
    source = _source_for(universe)
    result = run_economic_md_input_producer_v1(
        state_root=tmp_path,
        universe_snapshot=universe,
        public_md_source=source,
        collection_started_at_unix=START_UNIX,
        collection_completed_at_unix=COMPLETE_UNIX,
    )
    assert result["ok"] is True
    replay = replay_economic_md_snapshot_v1(tmp_path)
    assert replay["ok"] is True
    assert replay["network_read"] is False
    assert replay["payload_digest"] == result["snapshot"]["payload_digest"]
    loaded = EconomicMdInputSnapshotV1.from_dict(replay["snapshot"])
    assert loaded.payload_digest == loaded.compute_payload_digest()
    assert (
        loaded.instruments[0].raw_input_digest == loaded.instruments[0].compute_raw_input_digest()
    )


def test_public_path_allowlist_rejects_private_and_trade() -> None:
    assert MARK_ENDPOINT_PATH in ALLOWED_PUBLIC_GET_PATHS
    assert TICKER_ENDPOINT_PATH in ALLOWED_PUBLIC_GET_PATHS
    assert_public_get_path_allowed_v1(MARK_ENDPOINT_PATH)
    try:
        assert_public_get_path_allowed_v1("/api/v5/trade/order")
        raise AssertionError("trade path must fail closed")
    except EconomicMdPublicSourceError as exc:
        assert exc.failure_code == EconomicMdFailureCodeV1.FORBIDDEN_NETWORK_PATH.value


def test_constants_and_schema_identity() -> None:
    assert CAPABILITY_ID == "CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_V1"
    assert SCHEMA_VERSION == "economic_md_input_snapshot.v1"
    assert PRODUCER_VERSION == "economic_md_input_producer.v1"
    assert MINIMUM_FINALIZED_PT1M_MARKS == 61
    assert NO_IMPLICIT_FILL is True
    assert "ranking" not in CALL_GRAPH
    spec = REPO / "docs/ops/specs/CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_V1.md"
    text = spec.read_text(encoding="utf-8")
    assert (
        "docs_"
        + "token: "
        + "DOCS_TOKEN_CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_V1"
        in text
    )
    assert "ECONOMIC_MD_PRODUCER_IMPLEMENTED=true" in text
    assert "ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false" in text
    assert "ECONOMIC_MD_PRODUCER_MAY_RANK=false" in text
