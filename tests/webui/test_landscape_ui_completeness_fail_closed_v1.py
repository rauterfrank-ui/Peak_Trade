"""Landscape UI completeness: missing operator facts stay explicit, never blank."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
)
from src.webui.market_dashboard_landscape_v2.landscape_observability_common_v1 import (
    OPTIONAL_FIELD_ABSENT_DISPLAY,
    fail_closed_scalar_display_v1,
)
from src.webui.market_dashboard_landscape_v2.landscape_system_observability_completion_v1 import (
    build_v07_ohlcv_live_mark_fidelity_v1,
)
from src.webui.market_dashboard_landscape_v2.projections import (
    project_canonical_decision_snapshot_v1,
    project_risk_sizing_capital_snapshot_v1,
)
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
    LANDSCAPE_PHASE43A_MAX_AGE_SECONDS,
)
from src.webui.market_dashboard_landscape_v2.source_health_projection_fidelity_v1 import (
    FRESHNESS_UNAVAILABLE,
)
from src.webui.market_dashboard_landscape_v2.unavailable import (
    unavailable_canonical_decision,
    unavailable_regime_bull_bear_switch,
)

STAMP = datetime(2026, 9, 21, 18, 0, 0, tzinfo=timezone.utc)
PRODUCER = datetime(2026, 9, 21, 17, 0, 0, tzinfo=timezone.utc)
_LEAKS = (">null<", ">None<", ">undefined<", ">null</")


def _region(html: str, region: str) -> str:
    marker = f'data-mdl-region="{region}"'
    start = html.index(marker)
    rest = html[start:]
    nxt = rest.find('data-mdl-region="', len(marker))
    return rest if nxt < 0 else rest[:nxt]


def test_market_route_stays_available_without_sources() -> None:
    response = TestClient(create_app()).get("/market")
    assert response.status_code == 200
    html = response.text
    chart = _region(html, "PRIMARY_MARKET_WORKSPACE")
    assert 'data-mdl-chart-message="true"' in chart
    if 'data-chart-bound="false"' in chart or 'data-mdl-chart-has-series="false"' in chart:
        message = chart.split('data-mdl-chart-message="true"', 1)[1]
        text = message.split(">", 1)[1].split("<", 1)[0].strip()
        assert text
    volume_state = chart.split('data-mdl-volume-state="', 1)[1].split('"', 1)[0]
    assert 'data-mdl-volume-message="true"' in chart
    if volume_state in {"MISSING_SOURCE", "NOT_BOUND", "INVALID"}:
        volume_text = chart.split('data-mdl-volume-message="true"', 1)[1]
        volume_text = volume_text.split(">", 1)[1].split("<", 1)[0].strip()
        assert volume_text
        assert "Volume" in volume_text
    engineering = _region(html, "ENGINEERING_DRAWER")
    for leak in _LEAKS:
        assert leak not in engineering
    timeline = _region(html, "EVENT_DECISION_TIMELINE")
    assert "<canvas" not in timeline
    assert "NOT_BOUND" in timeline
    assert "no invented history" in timeline
    assert 'data-mdl-field="multi_decision_timeline_status"' not in html
    assert "timeline-chart" not in html
    page = MarketDashboardReadServiceV1().load_page_snapshot(generated_at=STAMP)
    ctx = present_market_landscape_v2(page)
    assert ctx["chart"]["message"]
    assert ctx["chart"]["volume_panel_message"]
    assert ctx["chart"]["has_browser_series"] is False


def test_v07_does_not_reconstruct_freshness_from_last_candle() -> None:
    v07 = build_v07_ohlcv_live_mark_fidelity_v1(
        chart={
            "availability": Availability.AVAILABLE.value,
            "bound": True,
            "bar_count": 3,
            "captured_at": None,
            "last_timestamp": "2026-01-01T00:00:00Z",
            "live_mark_price": None,
            "data_connection_state": "DEGRADED",
            "interval": "1m",
        }
    )
    assert v07["freshness_display"] == FRESHNESS_UNAVAILABLE
    assert "2026-01-01" not in v07["freshness_display"]
    fields = {row["field_id"]: row["display"] for row in v07["fields"]}
    assert fields["last_timestamp"] == "2026-01-01T00:00:00Z"
    assert fields["live_mark_price"] == OPTIONAL_FIELD_ABSENT_DISPLAY
    assert fields["bound"] == "BOUND"
    assert fields["bar_count"] == "3"
    assert fields["captured_at"] == OPTIONAL_FIELD_ABSENT_DISPLAY


def test_v07_unbound_chart_does_not_show_false_or_zero() -> None:
    v07 = build_v07_ohlcv_live_mark_fidelity_v1(
        chart={
            "availability": Availability.MISSING_SOURCE.value,
            "bound": False,
            "bar_count": 0,
            "captured_at": "",
            "last_timestamp": "2026-01-01T00:00:00Z",
            "data_connection_state": "",
        }
    )
    fields = {row["field_id"]: row["display"] for row in v07["fields"]}
    assert fields["bound"] == "MISSING_SOURCE"
    assert fields["bar_count"] == "MISSING_SOURCE"
    assert fields["bound"] not in {"False", "false", "0"}
    assert v07["freshness_display"] == FRESHNESS_UNAVAILABLE
    assert "2026-01-01" not in v07["freshness_display"]


def test_stale_regime_switch_does_not_stringify_none() -> None:
    snap = unavailable_regime_bull_bear_switch(
        availability=Availability.STALE,
        generated_at=STAMP,
        reason="projection_stale",
    )
    ctx = present_market_landscape_v2(
        MarketDashboardReadServiceV1().load_page_snapshot(
            generated_at=STAMP,
            slot_overrides={"regime_bull_bear_switch": snap},
        )
    )
    switch = ctx["switch"]["value_display"]
    assert "None" not in switch
    assert "null" not in switch
    assert OPTIONAL_FIELD_ABSENT_DISPLAY in switch
    fam = next(
        row
        for row in ctx["system_observability_completion"]["families"]
        if row["family_id"] == "S04_REGIME_BULL_BEAR_SWITCH"
    )
    switch_field = next(field for field in fam["fields"] if field["field_id"] == "switch")
    assert "None" not in switch_field["display"]


def test_optional_decision_id_absent_is_explicit() -> None:
    snap = project_canonical_decision_snapshot_v1(
        instrument_id="ETH-USDT-SWAP",
        decision="observe",
        direction="neutral_observe",
        reason_codes=(),
        blockers=(),
        decision_id=None,
        evidence_schema_version="canonical_trading_decision_evidence_v1",
        evidence_digest=None,
        generated_at=PRODUCER,
        effective_at=PRODUCER,
        source_reference="fixture",
        availability=Availability.AVAILABLE,
        max_age_seconds=LANDSCAPE_PHASE43A_MAX_AGE_SECONDS,
        is_stale=False,
    )
    ctx = present_market_landscape_v2(
        MarketDashboardReadServiceV1().load_page_snapshot(
            generated_at=STAMP,
            slot_overrides={"canonical_decision": snap},
        )
    )
    s05 = ctx["decision_double_play_observability"]["canonical_decision"]
    assert s05["decision_id_display"] == OPTIONAL_FIELD_ABSENT_DISPLAY
    assert s05["evidence_schema_version_display"] == "canonical_trading_decision_evidence_v1"
    assert s05["reason_codes_display"] == OPTIONAL_FIELD_ABSENT_DISPLAY
    missing = unavailable_canonical_decision(
        availability=Availability.MISSING_SOURCE,
        generated_at=STAMP,
        reason="not_persisted",
    )
    missing_ctx = present_market_landscape_v2(
        MarketDashboardReadServiceV1().load_page_snapshot(
            generated_at=STAMP,
            slot_overrides={"canonical_decision": missing},
        )
    )
    missing_s05 = missing_ctx["decision_double_play_observability"]["canonical_decision"]
    assert missing_s05["decision_id_display"] == "MISSING_SOURCE"


def test_available_quantity_renders_and_absent_quantity_is_not_zero() -> None:
    present = project_risk_sizing_capital_snapshot_v1(
        risk_status="PASS",
        sizing_status="PASS",
        capital_status="PASS",
        reason_codes=("RISK_OK",),
        quantity=2.5,
        generated_at=PRODUCER,
        effective_at=PRODUCER,
        source_reference="fixture",
        availability=Availability.AVAILABLE,
        max_age_seconds=LANDSCAPE_PHASE41_MAX_AGE_SECONDS,
        is_stale=False,
    )
    ctx = present_market_landscape_v2(
        MarketDashboardReadServiceV1().load_page_snapshot(
            generated_at=STAMP,
            slot_overrides={"risk_sizing_capital": present},
        )
    )
    assert ctx["risk"]["quantity_display"] == "2.5"
    fam = next(
        row
        for row in ctx["system_observability_completion"]["families"]
        if row["family_id"] == "S08_RISK_SIZING_CAPITAL"
    )
    quantity = next(field for field in fam["fields"] if field["field_id"] == "quantity")
    assert quantity["display"] == "2.5"
    assert fail_closed_scalar_display_v1(None, availability=Availability.NOT_BOUND) == "NOT_BOUND"
    assert fail_closed_scalar_display_v1(None, availability=Availability.INVALID) == "INVALID"
    assert (
        fail_closed_scalar_display_v1(None, availability=Availability.AVAILABLE)
        == OPTIONAL_FIELD_ABSENT_DISPLAY
    )
