import importlib.util
from pathlib import Path
from typing import Any, Optional

import pytest

prometheus_client = pytest.importorskip("prometheus_client")
from prometheus_client.core import REGISTRY  # type: ignore  # noqa: E402
from prometheus_client.exposition import generate_latest  # type: ignore  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_ai_live_exporter_module():
    p = PROJECT_ROOT / "scripts" / "obs" / "ai_live_exporter.py"
    spec = importlib.util.spec_from_file_location("ai_live_exporter", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


def _metrics_text() -> str:
    return generate_latest(REGISTRY).decode("utf-8")


def _parse_labels(raw: str) -> dict[str, str]:
    raw = raw.strip()
    if not raw:
        return {}
    out: dict[str, str] = {}
    for part in raw.split(","):
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        out[k] = v
    return out


def _series_value(text: str, *, name: str, labels: Optional[dict[str, str]] = None) -> Optional[float]:
    """
    Return the first matching sample value for a metric+labelset from Prometheus text exposition.
    """
    labels = labels or {}
    for ln in text.splitlines():
        if not ln or ln.startswith("#"):
            continue
        if not ln.startswith(name):
            continue
        # With labels: name{...} <value>
        if "{" in ln:
            prefix, rest = ln.split("{", 1)
            if prefix != name:
                continue
            label_str, value_str = rest.split("}", 1)
            got = _parse_labels(label_str)
            if got != labels:
                continue
            return float(value_str.strip().split()[0])
        # Without labels: name <value>
        if labels:
            continue
        parts = ln.split()
        if parts and parts[0] == name and len(parts) >= 2:
            return float(parts[1])
    return None


@pytest.fixture(scope="module")
def exporter_mod():
    return _load_ai_live_exporter_module()


def test_histogram_count_increments_only_when_latency_ms_present(exporter_mod: Any) -> None:
    warn = exporter_mod._RateLimitedWarn(min_interval_s=0.0)

    before = _series_value(
        _metrics_text(),
        name="peaktrade_ai_decision_latency_ms_count",
        labels={"source": "sample_v1", "decision": "accept"},
    )
    before = before or 0.0

    # No latency_ms -> should not observe
    exporter_mod._process_line(
        '{"v":1,"decision":"accept","reason":"none","ts_utc":"2026-01-01T00:00:00Z"}',
        default_component="execution_watch",
        default_run_id="na",
        warn=warn,
    )

    mid = _series_value(
        _metrics_text(),
        name="peaktrade_ai_decision_latency_ms_count",
        labels={"source": "sample_v1", "decision": "accept"},
    )
    mid = mid or 0.0
    assert mid == before

    # With latency_ms -> should observe
    exporter_mod._process_line(
        '{"v":1,"decision":"accept","reason":"none","latency_ms":10,"ts_utc":"2026-01-01T00:00:01Z"}',
        default_component="execution_watch",
        default_run_id="na",
        warn=warn,
    )

    after = _series_value(
        _metrics_text(),
        name="peaktrade_ai_decision_latency_ms_count",
        labels={"source": "sample_v1", "decision": "accept"},
    )
    after = after or 0.0
    assert after == before + 1.0


def test_parse_errors_and_bad_json_drop_increment_on_malformed_json(exporter_mod: Any) -> None:
    warn = exporter_mod._RateLimitedWarn(min_interval_s=0.0)

    txt0 = _metrics_text()
    p0 = _series_value(txt0, name="peaktrade_ai_events_parse_errors_total", labels={"source": "unknown"}) or 0.0
    d0 = (
        _series_value(
            txt0,
            name="peaktrade_ai_events_dropped_total",
            labels={"source": "unknown", "reason": "bad_json"},
        )
        or 0.0
    )

    exporter_mod._process_line(
        '{"not valid json"',
        default_component="execution_watch",
        default_run_id="na",
        warn=warn,
    )

    txt1 = _metrics_text()
    p1 = _series_value(txt1, name="peaktrade_ai_events_parse_errors_total", labels={"source": "unknown"}) or 0.0
    d1 = (
        _series_value(
            txt1,
            name="peaktrade_ai_events_dropped_total",
            labels={"source": "unknown", "reason": "bad_json"},
        )
        or 0.0
    )

    assert p1 == p0 + 1.0
    assert d1 == d0 + 1.0


def test_dropped_increments_on_unknown_schema_and_missing_fields(exporter_mod: Any) -> None:
    warn = exporter_mod._RateLimitedWarn(min_interval_s=0.0)

    # Unknown schema (known source: beta_exec_v1, unknown event_type)
    txt0 = _metrics_text()
    u0 = (
        _series_value(
            txt0,
            name="peaktrade_ai_events_dropped_total",
            labels={"source": "beta_exec_v1", "reason": "unknown_schema"},
        )
        or 0.0
    )

    exporter_mod._process_line(
        '{"schema_version":"BETA_EXEC_V1","event_type":"SOMETHING_NEW","ts_utc":"2026-01-01T00:00:02Z"}',
        default_component="execution_watch",
        default_run_id="na",
        warn=warn,
    )

    txt1 = _metrics_text()
    u1 = (
        _series_value(
            txt1,
            name="peaktrade_ai_events_dropped_total",
            labels={"source": "beta_exec_v1", "reason": "unknown_schema"},
        )
        or 0.0
    )
    assert u1 == u0 + 1.0

    # Missing mandatory fields (v=1 missing decision)
    txt2 = _metrics_text()
    m0 = (
        _series_value(
            txt2,
            name="peaktrade_ai_events_dropped_total",
            labels={"source": "sample_v1", "reason": "missing_fields"},
        )
        or 0.0
    )

    exporter_mod._process_line(
        '{"v":1,"reason":"none","latency_ms":5,"ts_utc":"2026-01-01T00:00:03Z"}',
        default_component="execution_watch",
        default_run_id="na",
        warn=warn,
    )

    txt3 = _metrics_text()
    m1 = (
        _series_value(
            txt3,
            name="peaktrade_ai_events_dropped_total",
            labels={"source": "sample_v1", "reason": "missing_fields"},
        )
        or 0.0
    )
    assert m1 == m0 + 1.0


def test_freshness_updates_only_on_valid_events(exporter_mod: Any) -> None:
    warn = exporter_mod._RateLimitedWarn(min_interval_s=0.0)

    # Valid event with timestamp: should set freshness to event ts
    exporter_mod._process_line(
        '{"v":1,"decision":"accept","reason":"none","ts_utc":"2026-01-01T00:00:10Z"}',
        default_component="execution_watch",
        default_run_id="na",
        warn=warn,
    )
    v1 = _series_value(
        _metrics_text(),
        name="peaktrade_ai_last_event_timestamp_seconds",
        labels={"source": "sample_v1"},
    )
    assert v1 is not None

    # Invalid/missing decision: should NOT update freshness
    exporter_mod._process_line(
        '{"v":1,"reason":"none","ts_utc":"2026-01-01T00:00:20Z"}',
        default_component="execution_watch",
        default_run_id="na",
        warn=warn,
    )
    v2 = _series_value(
        _metrics_text(),
        name="peaktrade_ai_last_event_timestamp_seconds",
        labels={"source": "sample_v1"},
    )
    assert v2 == v1
