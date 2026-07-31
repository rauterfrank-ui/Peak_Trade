"""Focused tests for typed runtime producer scaffold v1."""

from __future__ import annotations

import ast
import math
from datetime import datetime, timezone
from pathlib import Path

import pytest

from trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as contract
from trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer
from trading.master_v2 import (
    canonical_volatility_estimate_typed_consumption_contract_v1 as typed,
)
from trading.master_v2 import (
    canonical_volatility_runtime_mark_history_v1 as history_mod,
)
from trading.master_v2 import (
    canonical_volatility_typed_runtime_producer_scaffold_v1 as producer_mod,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)

ROOT = Path(__file__).resolve().parents[3]
VENUE = "okx"
CANON = "BTC-USD-SWAP-CANON"
VENUE_INST = "BTC-USD-SWAP"
T0 = 1_700_000_000.0


def _module_code_without_docstrings(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(getattr(node.body[0], "value", None), ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body[0].value = ast.Constant(value="")
    if hasattr(ast, "unparse"):
        return ast.unparse(tree)
    return source


def _price_at(i: int) -> float:
    return 100.0 * math.exp(0.001 * i)


def _sample(
    i: int, *, venue: str = VENUE, canon: str = CANON, mark: float | None = None
) -> MarketSampleIdentityV1:
    return MarketSampleIdentityV1(
        venue=venue,
        canonical_instrument_id=canon,
        venue_instrument_id=VENUE_INST if venue == VENUE else f"{venue}-INST",
        event_time=EventTimeInstantV1(unix_seconds=T0 + float(i * 60)),
        mark_price=_price_at(i) if mark is None else mark,
    )


def _producer(
    tmp_path: Path | None = None,
) -> producer_mod.CanonicalVolatilityTypedRuntimeProducerScaffoldV1:
    path = None if tmp_path is None else tmp_path / "mark_history.json"
    return producer_mod.CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=path,
    )


def _ingest_range(
    producer: producer_mod.CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    start: int,
    end_inclusive: int,
) -> list[producer_mod.TypedRuntimeProducerResultV1]:
    results: list[producer_mod.TypedRuntimeProducerResultV1] = []
    for i in range(start, end_inclusive + 1):
        results.append(
            producer.ingest_finalized_pt1m_mark_sample_v1(
                sample=_sample(i),
                transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
            )
        )
    return results


def test_guards_and_package_marker() -> None:
    guards = producer_mod.assert_capability_guards_v1()
    assert guards["SINGLE_CANONICAL_VOLATILITY_ESTIMATOR"] is True
    assert guards["PRODUCTIVE_BIND_TYPED_CALLER"] is False
    assert guards["NO_RUNTIME_CUTOVER"] is True
    assert producer_mod.PACKAGE_MARKER.endswith("=true")
    assert producer_mod.PRODUCER_OWNER.endswith("typed_runtime_producer_scaffold_v1")


def test_warmup_exactly_60_prices_no_estimate() -> None:
    producer = _producer()
    results = _ingest_range(producer, 0, 59)
    assert all(r.outcome is producer_mod.TypedRuntimeProducerOutcomeV1.WARMUP for r in results)
    assert results[-1].estimate is None
    assert results[-1].observation_count_prices == 60
    assert producer.output_port_v1().estimate is None


def test_produced_exactly_61_prices_matches_materializer_fixture() -> None:
    producer = _producer()
    results = _ingest_range(producer, 0, 60)
    assert results[-2].outcome is producer_mod.TypedRuntimeProducerOutcomeV1.WARMUP
    last = results[-1]
    assert last.outcome is producer_mod.TypedRuntimeProducerOutcomeV1.PRODUCED
    assert last.estimate is not None
    fixture = materializer.exact_known_61_price_fixture_v1()
    expected = materializer.expected_population_std_for_fixture_v1(fixture["mark_price"].tolist())
    assert last.estimate.value == pytest.approx(expected)
    assert last.estimate.fallback_used is False
    assert last.estimate.unit == typed.CANONICAL_UNIT
    assert last.estimate.horizon_seconds == 3600
    assert last.estimate.estimator == "POPULATION_STANDARD_DEVIATION_OF_LOG_RETURNS"
    assert last.estimate.annualized is False


def test_observation_count_from_return_window_provenance() -> None:
    producer = _producer()
    _ingest_range(producer, 0, 60)
    estimate = producer.output_port_v1().estimate
    assert estimate is not None
    series = producer.history.mark_price_series_v1()
    derived = typed.derive_return_observation_count_from_closed_window_v1(
        series,
        as_of_index=series.index[-1],
    )
    assert estimate.observation_count == derived
    assert estimate.observation_count == contract.WARMUP_REQUIRED_RETURN_COUNT
    assert estimate.observation_count != 61  # prices ≠ returns


def test_as_of_event_time_from_event_time_instant() -> None:
    producer = _producer()
    _ingest_range(producer, 0, 60)
    estimate = producer.output_port_v1().estimate
    assert estimate is not None
    expected = datetime.fromtimestamp(T0 + 60.0 * 60.0, tz=timezone.utc)
    assert estimate.as_of_event_time == expected
    assert estimate.as_of_event_time.tzinfo is not None


def test_duplicate_noop_preserves_history_and_estimate_digests() -> None:
    producer = _producer()
    _ingest_range(producer, 0, 60)
    before_hist = producer.history.history_digest
    before_src = producer.output_port_v1().estimate.source_digest  # type: ignore[union-attr]
    before_count = producer.history.observation_count_prices
    dup = producer.ingest_finalized_pt1m_mark_sample_v1(sample=_sample(60))
    assert dup.outcome is producer_mod.TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP
    assert producer.history.history_digest == before_hist
    assert producer.history.observation_count_prices == before_count
    assert producer.output_port_v1().estimate.source_digest == before_src  # type: ignore[union-attr]


def test_out_of_order_rejected_fail_closed() -> None:
    producer = _producer()
    _ingest_range(producer, 0, 10)
    before = producer.history.history_digest
    ooo = producer.ingest_finalized_pt1m_mark_sample_v1(sample=_sample(5))
    assert ooo.outcome is producer_mod.TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED
    assert producer.history.history_digest == before


def test_gap_exceeds_pt1m_rejects_estimate() -> None:
    producer = _producer()
    _ingest_range(producer, 0, 59)
    gapped = MarketSampleIdentityV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        event_time=EventTimeInstantV1(unix_seconds=T0 + 59 * 60 + 120),
        mark_price=_price_at(60),
    )
    result = producer.ingest_finalized_pt1m_mark_sample_v1(sample=gapped)
    assert result.outcome is producer_mod.TypedRuntimeProducerOutcomeV1.HISTORY_GAP_REJECTED
    assert result.estimate is None
    assert producer.output_port_v1().estimate is None


def test_wrong_instrument_rejected() -> None:
    producer = _producer()
    _ingest_range(producer, 0, 2)
    bad = _sample(3, canon="ETH-USD-SWAP-CANON")
    result = producer.ingest_finalized_pt1m_mark_sample_v1(sample=bad)
    assert result.outcome is producer_mod.TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED


def test_wrong_venue_rejected() -> None:
    producer = _producer()
    _ingest_range(producer, 0, 2)
    bad = _sample(3, venue="binance")
    result = producer.ingest_finalized_pt1m_mark_sample_v1(sample=bad)
    assert result.outcome is producer_mod.TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED


def test_unfinalized_and_invalid_mark_prices_rejected() -> None:
    producer = _producer()
    unfinal = producer.ingest_finalized_pt1m_mark_sample_v1(
        event_time_unix_seconds=T0,
        mark_price=100.0,
        is_final=False,
    )
    assert unfinal.outcome is producer_mod.TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED

    for bad_price in (math.nan, math.inf, None, 0.0, -1.0):
        result = producer.ingest_finalized_pt1m_mark_sample_v1(
            event_time_unix_seconds=T0 + 60,
            mark_price=bad_price,
            is_final=True,
        )
        assert (
            result.outcome is producer_mod.TypedRuntimeProducerOutcomeV1.INVALID_SAMPLE_REJECTED
        ), bad_price


def test_restart_persistence_reproduces_identical_estimate(tmp_path: Path) -> None:
    producer = _producer(tmp_path)
    _ingest_range(producer, 0, 60)
    first = producer.output_port_v1().estimate
    assert first is not None
    restored = (
        producer_mod.CanonicalVolatilityTypedRuntimeProducerScaffoldV1.restore_from_persistence_v1(
            persistence_path=tmp_path / "mark_history.json"
        )
    )
    assert restored.history.history_digest == producer.history.history_digest
    series = restored.history.mark_price_series_v1().iloc[-61:]
    as_of = datetime.fromtimestamp(T0 + 60.0 * 60.0, tz=timezone.utc)
    second = typed.materialize_typed_canonical_volatility_estimate_v1(
        series, as_of_event_time=as_of
    )
    assert second.value == pytest.approx(first.value)
    assert second.source_digest == first.source_digest
    assert second.observation_count == first.observation_count


def test_corrupt_persistence_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "mark_history.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(history_mod.RuntimeMarkHistoryError, match="CORRUPT_HISTORY_PERSISTENCE"):
        producer_mod.CanonicalVolatilityTypedRuntimeProducerScaffoldV1.restore_from_persistence_v1(
            persistence_path=path
        )


def test_incompatible_contract_version_fail_closed(tmp_path: Path) -> None:
    producer = _producer(tmp_path)
    _ingest_range(producer, 0, 2)
    path = tmp_path / "mark_history.json"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        history_mod.HISTORY_SCHEMA_VERSION,
        "canonical_volatility_runtime_mark_history/v0-incompatible",
        1,
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(history_mod.RuntimeMarkHistoryError, match="INCOMPATIBLE_HISTORY_SCHEMA"):
        producer_mod.CanonicalVolatilityTypedRuntimeProducerScaffoldV1.restore_from_persistence_v1(
            persistence_path=path
        )


def test_no_forbidden_fallback_literals_in_producer_path() -> None:
    producer = _producer()
    _ingest_range(producer, 0, 60)
    estimate = producer.output_port_v1().estimate
    assert estimate is not None
    assert estimate.fallback_used is False
    code = _module_code_without_docstrings(Path(producer_mod.__file__))
    hist_code = _module_code_without_docstrings(Path(history_mod.__file__))
    assert "feature_regime" not in code
    assert "feature_regime" not in hist_code
    assert "bind_typed_canonical_volatility_estimate_into_market_context_v1(" not in code
    assert "FORBIDDEN_FALLBACK_LITERALS" in code


def test_no_productive_bind_typed_or_double_play_caller() -> None:
    code = _module_code_without_docstrings(Path(producer_mod.__file__))
    assert "bind_typed_canonical_volatility_estimate_into_market_context_v1(" not in code
    assert "DynamicScopeRules" not in code
    assert producer_mod.PRODUCTIVE_BIND_TYPED_CALLER is False
    assert producer_mod.CMC_RUNTIME_WIRING is False
    assert producer_mod.DOUBLE_PLAY_RUNTIME_WIRING is False
    port = _producer().output_port_v1()
    assert port.to_dict()["productive_bind_typed_caller"] is False


def test_digest_stability_and_divergence() -> None:
    a = _producer()
    b = _producer()
    _ingest_range(a, 0, 60)
    _ingest_range(b, 0, 60)
    ea = a.output_port_v1().estimate
    eb = b.output_port_v1().estimate
    assert ea is not None and eb is not None
    assert ea.source_digest == eb.source_digest
    assert a.history.history_digest == b.history.history_digest

    c = _producer()
    for i in range(0, 61):
        sample = MarketSampleIdentityV1(
            venue=VENUE,
            canonical_instrument_id=CANON,
            venue_instrument_id=VENUE_INST,
            event_time=EventTimeInstantV1(unix_seconds=T0 + float(i * 60)),
            mark_price=100.0 * math.exp(0.002 * i),
        )
        c.ingest_finalized_pt1m_mark_sample_v1(sample=sample)
    ec = c.output_port_v1().estimate
    assert ec is not None
    assert ec.source_digest != ea.source_digest
    assert c.history.history_digest != a.history.history_digest


def test_runtime_cycle_without_sample_produces_no_estimate() -> None:
    producer = _producer()
    _ingest_range(producer, 0, 60)
    before = producer.output_port_v1().estimate
    assert before is not None
    before_digest = before.source_digest
    cycle = producer.on_runtime_cycle_without_sample_v1()
    assert cycle.estimate is None
    assert cycle.reason.startswith("runtime_cycle_without_new_sample")
    assert producer.output_port_v1().estimate is not None
    assert producer.output_port_v1().estimate.source_digest == before_digest


def test_existing_p1_p2_contracts_still_green() -> None:
    fixture = materializer.exact_known_61_price_fixture_v1()
    series = materializer.compute_canonical_volatility_estimate_from_mark_prices_v1(
        fixture["mark_price"]
    )
    expected = materializer.expected_population_std_for_fixture_v1(fixture["mark_price"].tolist())
    assert float(series.iloc[-1]) == pytest.approx(expected)
    estimate = typed.materialize_typed_canonical_volatility_estimate_v1(fixture["mark_price"])
    assert estimate.value == pytest.approx(expected)
    assert estimate.observation_count == 60
    assert estimate.fallback_used is False


def test_docs_token_present() -> None:
    doc = (
        ROOT / "docs/ops/specs/MASTER_V2_CANONICAL_VOLATILITY_TYPED_RUNTIME_PRODUCER_SCAFFOLD_V1.md"
    )
    text = doc.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_TYPED_RUNTIME_PRODUCER_SCAFFOLD_V1" in text
    assert "RUNTIME_PRODUCER_CUTOVER" in text
