from __future__ import annotations

import pytest

from src.obs import (
    OTelNotAvailableError,
    get_tracer,
    init_otel,
    instrument_lake,
    is_otel_available,
)


def test_is_otel_available_returns_bool():
    v = is_otel_available()
    assert isinstance(v, bool)


def test_get_tracer_never_crashes():
    tr = get_tracer("test")
    assert tr is not None


def test_init_otel_none_always_returns_noop_handle():
    h = init_otel("peak_trade", exporter="none")
    assert h.is_noop is True
    assert h.exporter_type == "none"


def test_init_otel_console_requires_deps_or_raises():
    if not is_otel_available():
        with pytest.raises(OTelNotAvailableError):
            init_otel("peak_trade", exporter="console")
    else:
        h = init_otel("peak_trade", exporter="console")
        assert h.is_noop is False
        assert h.provider is not None


def test_instrument_lake_returns_same_object():
    class DummyLake:
        def query(self, sql: str):
            return {"ok": True, "sql": sql}

    lake = DummyLake()
    out = instrument_lake(lake)
    assert out is lake


@pytest.mark.skipif(not is_otel_available(), reason="OpenTelemetry deps not installed")
def test_instrument_lake_emits_spans_with_provider():
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    class DummyLake:
        def query(self, sql: str):
            return {"ok": True}

    lake = DummyLake()
    instrument_lake(lake, provider=provider)

    lake.query("select 1")
    spans = exporter.get_finished_spans()
    assert any(s.name == "lake.query" for s in spans)


@pytest.mark.skipif(not is_otel_available(), reason="OpenTelemetry deps not installed")
def test_instrument_lake_records_exception_and_reraises():
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from opentelemetry.trace.status import StatusCode

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    class DummyLake:
        def query(self, sql: str):
            raise ValueError("boom")

    lake = DummyLake()
    instrument_lake(lake, provider=provider)

    with pytest.raises(ValueError):
        lake.query("select 1")

    spans = exporter.get_finished_spans()
    err_spans = [s for s in spans if s.name == "lake.query"]
    assert err_spans, "expected lake.query span"
    assert err_spans[0].status.status_code == StatusCode.ERROR
