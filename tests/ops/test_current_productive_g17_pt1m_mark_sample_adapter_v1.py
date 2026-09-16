"""Full-Core G17 PT1M mark-sample adapter: extract fields only. No ingest host."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.economic_md_input_producer_v1.models_v1 import (
    FinalizedPt1mMarkObservationV1 as EconomicMdFinalizedPt1mMarkObservationV1,
)
from src.ops.economic_md_input_producer_v1.reason_codes_v1 import EconomicMdFailureCodeV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1 import (
    ADAPTER_OWNER,
    CMC_BINDING_PERFORMED,
    COLD_START_FINALIZED_PT1M_MARK_COUNT,
    ECONOMIC_MD_PRODUCER_SCHEDULED_BY_ADAPTER,
    ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
    MARK_HISTORY_BAR,
    MARK_HISTORY_LIMIT_PARAM,
    PACKAGE_MARKER,
    PRESENCE_GATE_MUTATED,
    TYPED_VOL_HOST_PERSISTENCE_PERFORMED,
    FullCoreG17MarkSampleAdapterError,
    FullCoreG17Pt1mMarkIngestFieldsV1,
    extract_full_core_g17_pt1m_mark_ingest_fields_v1,
    g17_ingest_kwargs_from_extracted_sample_v1,
    mark_history_get_query_v1,
    refuse_forbidden_mark_source_endpoint_v1,
    refuse_homonym_dto_as_g17_sample_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    DEFAULT_VENUE,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    TypedRuntimeProducerOutcomeV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)
from tests.ops.test_economic_md_input_producer_v1 import (
    test_missing_mark_and_non_finalized_fail_closed,
    test_sixty_marks_not_rankable_sixty_one_finalized_eligible,
)
from tests.ops.test_full_core_current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1 import (
    _eligible_transport,
    _fresh_get_transport,
)
from tests.ops.test_full_core_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    SATISFIED_TS_MS,
    OWNER_GO,
    V5_HOST,
    _candles,
    _execute,
)
from tests.trading.master_v2.test_canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    test_duplicate_noop_preserves_history_and_estimate_digests,
    test_gap_exceeds_pt1m_rejects_estimate,
    test_out_of_order_rejected_fail_closed,
    test_produced_exactly_61_prices_matches_materializer_fixture,
    test_warmup_exactly_60_prices_no_estimate,
)

REPO = Path(__file__).resolve().parents[2]
ADAPTER_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_g17_pt1m_mark_sample_adapter_v1.py"
)
V5_SRC = (
    REPO
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5.py"
)
BASE_TS_MS = 1_700_000_000_000
CAPTURE_TS = "1700000061000"
CANON = "BTC-USDT-SWAP-CANON"
NATIVE = "BTC-USDT-SWAP"
VENUE = DEFAULT_VENUE


def _mark_row(index: int, *, confirm: str = "1", px: str | None = None) -> list[str]:
    ts = str(BASE_TS_MS + index * 60_000)
    price = px if px is not None else str(100 + index)
    return [ts, price, price, price, price, confirm]


def _market_candle_row(index: int, *, confirm: str = "1") -> list[str]:
    ts = str(BASE_TS_MS + index * 60_000)
    price = str(100 + index)
    return [ts, price, price, price, price, "10", "100", "USDT", confirm]


def _payload(rows: list[list[str]]) -> dict[str, object]:
    return {"code": "0", "msg": "", "data": rows}


def _extract(
    rows: list[list[str]],
    *,
    newest_first: bool = True,
    source_endpoint: str = ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
    venue: str = VENUE,
    canonical_instrument_id: str = CANON,
    venue_instrument_id: str = NATIVE,
):
    ordered = list(reversed(rows)) if newest_first else list(rows)
    return extract_full_core_g17_pt1m_mark_ingest_fields_v1(
        _payload(ordered),
        venue=venue,
        canonical_instrument_id=canonical_instrument_id,
        venue_instrument_id=venue_instrument_id,
        receive_or_capture_timestamp=CAPTURE_TS,
        source_endpoint=source_endpoint,
    )


def test_package_marker_and_authority_non_transfer() -> None:
    assert PACKAGE_MARKER == "FULL_CORE_G17_PT1M_MARK_SAMPLE_ADAPTER_V1=true"
    assert ADAPTER_OWNER.endswith("current_productive_g17_pt1m_mark_sample_adapter_v1")
    assert ENDPOINT_HISTORY_MARK_PRICE_CANDLES == "/api/v5/market/history-mark-price-candles"
    assert MARK_HISTORY_BAR == "1m"
    assert MARK_HISTORY_LIMIT_PARAM == "100"
    assert COLD_START_FINALIZED_PT1M_MARK_COUNT == 61
    assert ECONOMIC_MD_PRODUCER_SCHEDULED_BY_ADAPTER is False
    assert CMC_BINDING_PERFORMED is False
    assert TYPED_VOL_HOST_PERSISTENCE_PERFORMED is False
    assert PRESENCE_GATE_MUTATED is False
    source = ADAPTER_SRC.read_text(encoding="utf-8")
    assert "parse_okx_mark_candles_v1" in source
    assert "select_finalized_contiguous_pt1m_marks_v1" in source
    assert "produce_economic_md_input_snapshot_v1" not in source
    assert "run_economic_md_input_producer_v1" not in source
    assert "bind_typed_canonical_volatility_estimate" not in source


def test_mark_history_get_query_is_bar_1m_limit_100() -> None:
    assert mark_history_get_query_v1(venue_native_id=NATIVE) == {
        "instId": NATIVE,
        "bar": "1m",
        "limit": "100",
    }


def test_row_mapping_event_time_and_mark_price_explicit_g17_fields() -> None:
    result = _extract([_mark_row(i) for i in range(61)])
    assert result.failure_codes == ()
    assert len(result.samples) == 61
    first = result.samples[0]
    last = result.samples[-1]
    assert first.venue == VENUE
    assert first.canonical_instrument_id == CANON
    assert first.venue_instrument_id == NATIVE
    assert first.event_time_unix_seconds == int(BASE_TS_MS) / 1000.0
    assert first.mark_price == 100.0
    assert first.is_final is True
    assert last.event_time_unix_seconds == int(BASE_TS_MS + 60 * 60_000) / 1000.0
    assert last.mark_price == 160.0
    kwargs = g17_ingest_kwargs_from_extracted_sample_v1(first)
    assert kwargs == {
        "venue": VENUE,
        "canonical_instrument_id": CANON,
        "venue_instrument_id": NATIVE,
        "event_time_unix_seconds": int(BASE_TS_MS) / 1000.0,
        "mark_price": 100.0,
        "is_final": True,
    }
    assert "sample" not in kwargs


def test_newest_first_payload_ingests_oldest_to_newest() -> None:
    result = _extract([_mark_row(i) for i in range(61)], newest_first=True)
    times = [sample.event_time_unix_seconds for sample in result.samples]
    assert times == sorted(times)
    assert times[0] < times[-1]
    assert all(later - earlier == 60.0 for earlier, later in zip(times, times[1:]))


def test_confirm_not_1_is_not_finalized_mark_sample() -> None:
    rows = [_mark_row(i) for i in range(61)]
    rows[-1] = _mark_row(60, confirm="0")
    result = _extract(rows)
    assert result.samples == ()
    assert EconomicMdFailureCodeV1.NON_FINALIZED_MARK.value in result.failure_codes
    mixed = [_mark_row(i, confirm="1" if i % 2 == 0 else "0") for i in range(80)]
    filtered = _extract(mixed)
    assert filtered.samples == ()
    assert any(
        code
        in {
            EconomicMdFailureCodeV1.NON_FINALIZED_MARK.value,
            EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value,
            EconomicMdFailureCodeV1.MISSING_MARK_BAR_NO_IMPLICIT_FILL.value,
        }
        for code in filtered.failure_codes
    )


def test_sixty_finalized_insufficient_sixty_one_extracted() -> None:
    short = _extract([_mark_row(i) for i in range(60)])
    assert short.samples == ()
    assert (
        EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value in short.failure_codes
        or EconomicMdFailureCodeV1.NON_FINALIZED_MARK.value in short.failure_codes
    )
    full = _extract([_mark_row(i) for i in range(61)])
    assert len(full.samples) == 61
    assert full.failure_codes == ()


def test_duplicate_conflicting_mark_bar_fail_closed_no_implicit_fill() -> None:
    rows = [_mark_row(i) for i in range(61)]
    rows.append(_mark_row(10, px="999"))
    result = _extract(rows)
    assert result.samples == ()
    assert EconomicMdFailureCodeV1.MISSING_MARK_BAR_NO_IMPLICIT_FILL.value in result.failure_codes


def test_gap_in_trailing_window_fail_closed_no_implicit_fill() -> None:
    rows = [_mark_row(i) for i in range(62) if i != 10]
    result = _extract(rows)
    assert result.samples == ()
    assert (
        EconomicMdFailureCodeV1.MISSING_MARK_BAR_NO_IMPLICIT_FILL.value in result.failure_codes
        or EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value in result.failure_codes
    )


def test_out_of_order_native_rows_are_sorted_oldest_to_newest_when_contiguous() -> None:
    rows = [_mark_row(i) for i in range(61)]
    shuffled = rows[::2] + rows[1::2]
    result = _extract(shuffled, newest_first=False)
    times = [sample.event_time_unix_seconds for sample in result.samples]
    assert times == sorted(times)
    assert len(result.samples) == 61


def test_market_candles_endpoint_is_not_a_mark_sample_source() -> None:
    with pytest.raises(FullCoreG17MarkSampleAdapterError, match="FORBIDDEN_MARK_SOURCE_ENDPOINT"):
        refuse_forbidden_mark_source_endpoint_v1("/api/v5/market/candles")
    with pytest.raises(FullCoreG17MarkSampleAdapterError, match="FORBIDDEN_MARK_SOURCE_ENDPOINT"):
        extract_full_core_g17_pt1m_mark_ingest_fields_v1(
            _payload([_mark_row(i) for i in range(61)]),
            venue=VENUE,
            canonical_instrument_id=CANON,
            venue_instrument_id=NATIVE,
            receive_or_capture_timestamp=CAPTURE_TS,
            source_endpoint="/api/v5/market/candles",
        )


def test_nine_column_market_candle_rows_are_not_mark_samples() -> None:
    result = extract_full_core_g17_pt1m_mark_ingest_fields_v1(
        _payload([_market_candle_row(i) for i in range(61)]),
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=NATIVE,
        receive_or_capture_timestamp=CAPTURE_TS,
        source_endpoint=ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
    )
    assert result.samples == ()
    assert "MARKET_CANDLE_CLOSE_SUBSTITUTION_FORBIDDEN" in result.failure_codes


def test_homonym_economic_md_dto_is_not_g17_sample() -> None:
    homonym = EconomicMdFinalizedPt1mMarkObservationV1(
        mark_px="100.0",
        event_timestamp=str(BASE_TS_MS),
        receive_or_capture_timestamp=CAPTURE_TS,
        finalization_status="FINALIZED",
        source_class="HOMONYM",
        source_endpoint=ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
    )
    with pytest.raises(FullCoreG17MarkSampleAdapterError, match="HOMONYM_DTO_IS_NOT_G17_SAMPLE"):
        refuse_homonym_dto_as_g17_sample_v1(homonym)
    with pytest.raises(FullCoreG17MarkSampleAdapterError, match="HOMONYM_DTO_IS_NOT_G17_SAMPLE"):
        g17_ingest_kwargs_from_extracted_sample_v1(homonym)  # type: ignore[arg-type]
    with pytest.raises(
        FullCoreG17MarkSampleAdapterError, match="HOMONYM_MAPPING_IS_NOT_G17_SAMPLE"
    ):
        refuse_homonym_dto_as_g17_sample_v1(
            {"mark_px": "100.0", "event_timestamp": str(BASE_TS_MS)}
        )
    identity = MarketSampleIdentityV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=NATIVE,
        event_time=EventTimeInstantV1(unix_seconds=int(BASE_TS_MS) / 1000.0),
        mark_price=100.0,
    )
    with pytest.raises(FullCoreG17MarkSampleAdapterError, match="INGEST_FIELDS_TYPE_MISMATCH"):
        g17_ingest_kwargs_from_extracted_sample_v1(identity)  # type: ignore[arg-type]


def test_extracted_kwargs_feed_g17_ingest_without_sample_dto_cast() -> None:
    extracted = _extract([_mark_row(i) for i in range(61)])
    producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=NATIVE,
    )
    results = []
    for sample in extracted.samples:
        assert isinstance(sample, FullCoreG17Pt1mMarkIngestFieldsV1)
        results.append(
            producer.ingest_finalized_pt1m_mark_sample_v1(
                **g17_ingest_kwargs_from_extracted_sample_v1(sample)
            )
        )
    assert results[-2].outcome is TypedRuntimeProducerOutcomeV1.WARMUP
    assert results[-1].outcome is TypedRuntimeProducerOutcomeV1.PRODUCED
    assert producer.history.observation_count_prices == 61
    dup = producer.ingest_finalized_pt1m_mark_sample_v1(
        **g17_ingest_kwargs_from_extracted_sample_v1(extracted.samples[-1])
    )
    assert dup.outcome is TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP
    ooo = producer.ingest_finalized_pt1m_mark_sample_v1(
        **g17_ingest_kwargs_from_extracted_sample_v1(extracted.samples[0])
    )
    assert ooo.outcome is TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED
    gapped_fields = FullCoreG17Pt1mMarkIngestFieldsV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=NATIVE,
        event_time_unix_seconds=extracted.samples[-1].event_time_unix_seconds + 120.0,
        mark_price=200.0,
        is_final=True,
    )
    gapped = producer.ingest_finalized_pt1m_mark_sample_v1(
        **g17_ingest_kwargs_from_extracted_sample_v1(gapped_fields)
    )
    assert gapped.outcome is TypedRuntimeProducerOutcomeV1.HISTORY_GAP_REJECTED


def test_reuse_existing_economic_md_sixty_vs_sixty_one_eligibility() -> None:
    test_sixty_marks_not_rankable_sixty_one_finalized_eligible()


def test_reuse_existing_economic_md_gap_and_non_finalized() -> None:
    test_missing_mark_and_non_finalized_fail_closed()


def test_reuse_existing_g17_warmup_60_and_produced_61() -> None:
    test_warmup_exactly_60_prices_no_estimate()
    test_produced_exactly_61_prices_matches_materializer_fixture()


def test_reuse_existing_g17_duplicate_out_of_order_and_gap() -> None:
    test_duplicate_noop_preserves_history_and_estimate_digests()
    test_out_of_order_rejected_fail_closed()
    test_gap_exceeds_pt1m_rejects_estimate()


def test_v5_cycle_issues_bounded_mark_history_get_without_ingest_or_missing_gate(
    tmp_path: Path,
) -> None:
    transport = _fresh_get_transport()
    recorded: list[str] = []
    original_get = transport.get

    def _record(*, endpoint, auth_required, pretrade_decision_id):
        recorded.append(str(endpoint))
        return original_get(
            endpoint=endpoint,
            auth_required=auth_required,
            pretrade_decision_id=pretrade_decision_id,
        )

    transport.get = _record  # type: ignore[method-assign]
    result = _execute(
        owner_go=OWNER_GO,
        evidence_root=tmp_path / "store",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=transport,
        c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        producer_observed_at_unix=1_700_000_100.0,
    )
    mark_gets = [
        endpoint
        for endpoint in recorded
        if endpoint.split("?", 1)[0] == ENDPOINT_HISTORY_MARK_PRICE_CANDLES
    ]
    assert mark_gets, recorded
    assert "bar=1m" in mark_gets[0]
    assert "limit=100" in mark_gets[0]
    assert result.post_count == "0"
    host = V5_HOST.read_text(encoding="utf-8")
    assert "ENDPOINT_HISTORY_MARK_PRICE_CANDLES" in host
    assert "extract_full_core_g17_pt1m_mark_ingest_fields_v1" in host
    assert "ingest_finalized_pt1m_mark_sample_v1" not in host
    assert 'missing.append("G17' not in host
    assert "run_economic_md_input_producer_v1" not in host
    assert "bind_typed_canonical_volatility_estimate" not in host
