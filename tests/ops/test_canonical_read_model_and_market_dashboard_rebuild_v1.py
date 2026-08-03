"""Deterministic contract tests for CAPABILITY_O5."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.authority_declaration_v1 import (
    assert_authority_invariants_v1,
    authority_declaration_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.connection_state_v1 import (
    ConnectionStateContractErrorV1,
    assert_no_healthy_render_for_cached_bad_state_v1,
    classify_connection_state_v1,
    connection_state_contract_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    CAPABILITY_ID,
    CLOSED_FROM_O4_DEFERRED,
    CONNECTION_DEGRADED,
    CONNECTION_DISCONNECTED,
    CONNECTION_HEALTHY,
    CONNECTION_MISSING_SOURCE,
    CONNECTION_STALE,
    DASHBOARD_TRANSPORT,
    O4_AUTHORITATIVE_BAR_PRODUCER,
    READ_MODEL_AUTHORITY_EFFECT,
    READ_MODEL_CLASSIFICATION,
    READ_MODEL_SCHEMA_NAME,
    READ_MODEL_SSOT,
    SAFETY_INVARIANTS,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.dashboard_lifecycle_v1 import (
    assert_dashboard_has_no_trading_authority_v1,
    dashboard_lifecycle_contract_v1,
    materialize_dashboard_lifecycle_status_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.isolation_proofs_v1 import (
    run_all_o5_isolation_proofs_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.ohlcv_adapter_v1 import (
    adapt_derived_ohlcv_payload_to_o5_read_model_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.read_model_v1 import (
    bind_dashboard_backend_to_read_model_v1,
    build_missing_source_read_model_v1,
    project_o4_envelopes_to_canonical_dashboard_read_model_v1,
    read_model_path_contract_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)


def _md(
    *, mark: float, event_ts: float, canonical: str = "ETH-USDT-SWAP"
) -> NormalizedPublicMarketDataV1:
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id=canonical,
        venue_instrument_id=canonical,
        venue="okx",
        mark_px=mark,
        event_ts_unix=event_ts,
        receive_ts_unix=event_ts + 0.2,
        mark_price_endpoint="/api/v5/public/mark-price",
        mark_price_field="markPx",
        mapping_digest="o5-digest",
        mapping_version="v1",
    )


def _producer() -> CanonicalPublicMdBarProducerV1:
    return CanonicalPublicMdBarProducerV1(
        session_id="o5-session",
        repository_sha="d" * 40,
        config_digest="cfg-o5",
    )


def test_capability_constants_and_safety() -> None:
    assert CAPABILITY_ID.endswith("_V1")
    assert READ_MODEL_CLASSIFICATION == "DERIVED"
    assert READ_MODEL_SSOT is False
    assert READ_MODEL_AUTHORITY_EFFECT == "NONE"
    assert SAFETY_INVARIANTS["DASHBOARD_TRADING_AUTHORITY"] is False
    assert SAFETY_INVARIANTS["PARALLEL_OHLCV_PRODUCER_FORBIDDEN"] is True
    assert SAFETY_INVARIANTS["STALE_CANNOT_RENDER_HEALTHY"] is True
    assert SAFETY_INVARIANTS["ORDERS_ALLOWED"] is False
    assert "DURABLE_READ_MODEL_BINDING_CLOSURE" in CLOSED_FROM_O4_DEFERRED


def test_authority_declaration_and_invariants() -> None:
    decl = authority_declaration_v1()
    assert decl["authoritative_bar_producer"] == O4_AUTHORITATIVE_BAR_PRODUCER
    assert decl["parallel_ohlcv_producer_created"] is False
    assert decl["dashboard_trading_authority"] is False
    assert assert_authority_invariants_v1()["ok"] is True


def test_read_model_path_is_versioned_derived() -> None:
    path = read_model_path_contract_v1()
    assert path["schema_name"] == READ_MODEL_SCHEMA_NAME
    assert path["classification"] == "DERIVED"
    assert path["ssot"] is False
    assert path["authority_effect"] == "NONE"
    assert path["dashboard_transport"] == DASHBOARD_TRANSPORT
    assert path["parallel_ohlcv_producer_allowed"] is False


def test_project_o4_envelopes_to_o5_read_model_surfaces_identity() -> None:
    producer = _producer()
    producer.ingest_normalized_event(_md(mark=150.0, event_ts=1_700_100_100.0))
    model = project_o4_envelopes_to_canonical_dashboard_read_model_v1(
        producer.list_envelopes(),
        selection_bundle_id="bundle-o5",
        projection_time_unix=1_700_100_110.0,
    )
    assert model["schema_name"] == READ_MODEL_SCHEMA_NAME
    assert model["source_session_id"] == "o5-session"
    assert model["repository_sha"] == "d" * 40
    assert model["config_digest"] == "cfg-o5"
    assert model["instrument"] == "ETH-USDT-SWAP"
    assert model["interval"] == "PT1H"
    assert model["last_event_time"] is not None
    assert model["last_projection_time"] is not None
    assert model["freshness_age_seconds"] == pytest.approx(10.0)
    assert model["connection_state"] == CONNECTION_HEALTHY
    assert model["trading_authority"] is False
    assert model["orders"] is False
    assert model["parallel_ohlcv_producer"] is False
    binding = bind_dashboard_backend_to_read_model_v1(model)
    assert binding["exclusive_to_canonical_read_model"] is True
    assert binding["trading_authority"] is False


def test_missing_source_and_stale_disconnected_cannot_render_healthy() -> None:
    missing = build_missing_source_read_model_v1(
        selection_bundle_id="b",
        projection_time_unix=1.0,
    )
    assert missing["connection_state"] == CONNECTION_MISSING_SOURCE
    assert missing.get("may_render_healthy") is False

    assert classify_connection_state_v1(source_present=False) == CONNECTION_MISSING_SOURCE
    assert (
        classify_connection_state_v1(source_present=True, disconnected=True)
        == CONNECTION_DISCONNECTED
    )
    assert classify_connection_state_v1(source_present=True, is_stale=True) == CONNECTION_STALE
    assert (
        classify_connection_state_v1(source_present=True, freshness_age_seconds=60.0)
        == CONNECTION_DEGRADED
    )
    assert (
        classify_connection_state_v1(source_present=True, freshness_age_seconds=5.0)
        == CONNECTION_HEALTHY
    )

    for bad in (
        CONNECTION_STALE,
        CONNECTION_DISCONNECTED,
        CONNECTION_MISSING_SOURCE,
        CONNECTION_DEGRADED,
    ):
        with pytest.raises(ConnectionStateContractErrorV1):
            assert_no_healthy_render_for_cached_bad_state_v1(
                connection_state=bad,
                render_as_healthy=True,
            )
        assert assert_no_healthy_render_for_cached_bad_state_v1(
            connection_state=bad,
            render_as_healthy=False,
        )["ok"]

    contract = connection_state_contract_v1()
    assert contract["stale_cannot_render_healthy"] is True
    assert contract["disconnected_cannot_render_healthy"] is True


def test_dashboard_lifecycle_read_only() -> None:
    life = dashboard_lifecycle_contract_v1()
    assert life["transport"] == "HTTP_JSON_POLL"
    assert life["websocket_required"] is False
    assert life["trading_authority"] is False
    status = materialize_dashboard_lifecycle_status_v1(
        backend_alive=True,
        frontend_armed=True,
        poll_transport_ok=True,
        read_model_present=True,
        health_endpoint_ok=True,
        connection_state=CONNECTION_HEALTHY,
    )
    assert status["overall_connection_state"] == CONNECTION_HEALTHY
    assert assert_dashboard_has_no_trading_authority_v1(status)["ok"] is True
    disconnected = materialize_dashboard_lifecycle_status_v1(
        backend_alive=True,
        frontend_armed=True,
        poll_transport_ok=False,
        read_model_present=True,
        health_endpoint_ok=True,
        connection_state=CONNECTION_DISCONNECTED,
    )
    assert disconnected["overall_connection_state"] == CONNECTION_DISCONNECTED


def test_isolation_proofs() -> None:
    result = run_all_o5_isolation_proofs_v1()
    assert result["ok"] is True
    names = {p["proof"] for p in result["proofs"]}
    assert "INSTRUMENT_ISOLATION" in names
    assert "INTERVAL_ISOLATION" in names


def test_ohlcv_adapter_stamps_o5_chrome_without_parallel_producer() -> None:
    adapted = adapt_derived_ohlcv_payload_to_o5_read_model_v1(
        {
            "schema_name": "okx_selected_instrument_ohlcv_readmodel.v1",
            "authority_classification": "DERIVED",
            "instrument_id": "ETH-USDT-SWAP",
            "interval": "PT1H",
            "session_id": "sess-1",
            "repository_sha": "e" * 40,
            "config_digest": "cfg",
            "last_timestamp": "2023-11-15T00:01:40Z",
            "is_stale": False,
            "bar_count": 1,
        },
        projection_time_unix=1_700_000_110.0,
    )
    assert adapted["schema_name"] == READ_MODEL_SCHEMA_NAME
    assert adapted["parallel_ohlcv_producer"] is False
    assert adapted["source_session_id"] == "sess-1"
    assert adapted["repository_sha"] == "e" * 40
    assert adapted["config_digest"] == "cfg"
    assert adapted["instrument"] == "ETH-USDT-SWAP"
    assert adapted["interval"] == "PT1H"
    assert adapted["trading_authority"] is False

    stale = adapt_derived_ohlcv_payload_to_o5_read_model_v1(
        {
            "instrument_id": "ETH-USDT-SWAP",
            "is_stale": True,
            "last_timestamp": "2023-11-15T00:01:40Z",
        },
        projection_time_unix=1_700_000_110.0,
    )
    assert stale["connection_state"] == CONNECTION_STALE


def test_presenter_connection_state_uses_o5_vocabulary() -> None:
    from src.webui.market_dashboard_landscape_v2.availability import Availability
    from src.webui.market_dashboard_landscape_v2.presenter import _ohlcv_data_connection_state

    assert (
        _ohlcv_data_connection_state(
            browser_payload=None,
            ohlcv_payload=None,
            chart_availability=Availability.MISSING_SOURCE,
        )
        == CONNECTION_MISSING_SOURCE
    )
    assert (
        _ohlcv_data_connection_state(
            browser_payload={"bars": [{"open": "1", "high": "1", "low": "1", "close": "1"}]},
            ohlcv_payload={"is_stale": True, "captured_at": "2023-11-15T00:01:40Z"},
            chart_availability=Availability.STALE,
        )
        == CONNECTION_STALE
    )
    assert (
        _ohlcv_data_connection_state(
            browser_payload={"bars": []},
            ohlcv_payload={"captured_at": "2023-11-15T00:01:40Z"},
            chart_availability=Availability.AVAILABLE,
            disconnected=True,
        )
        == CONNECTION_DISCONNECTED
    )


def test_no_network_or_order_side_effects_in_o5_package() -> None:
    root = Path(__file__).resolve().parents[2]
    pkg = root / "src/ops/canonical_read_model_and_market_dashboard_rebuild_v1"
    forbidden = (
        "urlopen(",
        "OkxPublicMarketDataClientV1(",
        "requests.get",
        "httpx.",
        "submit_order",
        "place_order",
        "exchange_credentials",
    )
    for path in pkg.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains {token}"


def test_frontend_css_js_do_not_paint_stale_as_healthy() -> None:
    root = Path(__file__).resolve().parents[2]
    css = (root / "static/css/market_dashboard_landscape_v2.css").read_text(encoding="utf-8")
    js = (root / "static/js/market_dashboard_landscape_v2.js").read_text(encoding="utf-8")
    assert 'data-connection-state="HEALTHY"' in css
    assert 'data-connection-state="DISCONNECTED"' in css
    assert 'data-connection-state="DEGRADED"' in css
    # STALE and DISCONNECTED share the red style block — not the HEALTHY green block.
    healthy_block = css.split('data-connection-state="HEALTHY"')[1].split("}")[0]
    assert "STALE" not in healthy_block
    assert "DISCONNECTED" not in healthy_block
    assert "never promote stale/disconnected/missing to HEALTHY" in js
    assert 'setConnectionState("DISCONNECTED")' in js or "DISCONNECTED" in js
