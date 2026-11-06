"""Focused contracts for OKX_NATIVE_INSTRUMENT_AND_MARK_PRICE_RUNTIME_BINDING_FAIL_CLOSED_V1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

import pytest

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    EeaPublicMdTransportV1,
    parse_ticker_mid_price_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.authority_inventory_v1 import (
    verify_okx_native_instrument_mark_price_authority_inventory_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    CAPABILITY_ID,
    MARK_PRICE_ENDPOINT,
    MARK_PRICE_FIELD,
    VENUE_MAPPING_VERSION,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
    classify_transport_message_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.mark_price_contract_v1 import (
    parse_public_mark_price_response_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.offline_integration_probe_v1 import (
    load_fixture_json,
    run_offline_okx_native_mark_price_binding_probe_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.productive_md_fetch_v1 import (
    fetch_normalized_public_market_data_v1,
    resolve_mapping_with_transport_inventory_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.ticker_semantics_v1 import (
    parse_public_ticker_semantics_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.venue_instrument_mapping_v1 import (
    resolve_okx_venue_instrument_mapping_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    MARK_TO_MARKET_PRICE_SOURCE,
    REQUIRED_TICKER_PRICE_FIELD,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIX = (
    REPO_ROOT
    / "tests/fixtures/ops/okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1"
)
RECEIVE_TS = 1785442987.0
FAILED_AUTH = (
    REPO_ROOT
    / "evidence/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "authorization_1h_sha_bound_baa662ba406b_20260730T201621Z"
    / "authorization_artifact.json"
)
FAILED_CONS = (
    REPO_ROOT
    / "evidence/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "sessions"
    / "prereg_wallclock_full_canonical_1h_baa662ba406b_20260730T200959Z"
    / "authorization_consumptions_v1"
    / "cons_eba3914ae613dbdee38bccb1.json"
)


def _inv(name: str = "instruments_futures_live.json") -> list[Mapping[str, Any]]:
    return list(load_fixture_json(FIX / name)["data"])


def test_canonical_to_native_mapping_success() -> None:
    mapping = resolve_okx_venue_instrument_mapping_v1(
        canonical_instrument_id=CANONICAL_INSTRUMENT_ID,
        instruments_inventory=_inv(),
    )
    assert mapping.canonical_instrument_id == CANONICAL_INSTRUMENT_ID
    assert mapping.venue_instrument_id == CANONICAL_INSTRUMENT_ID
    assert mapping.mapping_version == VENUE_MAPPING_VERSION
    assert mapping.mapping_digest
    assert "bounded_futures_testnet_venue_binding" in mapping.mapping_source


def test_canonical_id_never_emitted_as_transport_default() -> None:
    src = (
        REPO_ROOT
        / "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
        / "eea_public_md_transport_v1.py"
    ).read_text(encoding="utf-8")
    assert "instrument_id: str = CANONICAL_INSTRUMENT_ID" not in src
    assert "venue_instrument_id" in src
    transport = EeaPublicMdTransportV1(
        fetcher=lambda *a, **k: (200, b'{"code":"0","data":[]}', {}),
        environ={},
    )
    transport.open()
    with pytest.raises(TypeError):
        transport.fetch_ticker()  # type: ignore[call-arg]


def test_missing_mapping_fail_closed() -> None:
    with pytest.raises(MarketDataBindingErrorV1) as exc:
        resolve_okx_venue_instrument_mapping_v1(
            canonical_instrument_id="UNKNOWN-CANONICAL",
            instruments_inventory=_inv(),
        )
    assert exc.value.error_class == "CANONICAL_INSTRUMENT_MAPPING_MISSING"


def test_ambiguous_mapping_fail_closed() -> None:
    with pytest.raises(MarketDataBindingErrorV1) as exc:
        resolve_okx_venue_instrument_mapping_v1(
            canonical_instrument_id=CANONICAL_INSTRUMENT_ID,
            instruments_inventory=_inv("instruments_ambiguous.json"),
        )
    assert exc.value.error_class == "CANONICAL_INSTRUMENT_MAPPING_AMBIGUOUS"


def test_inactive_venue_instrument_fail_closed() -> None:
    with pytest.raises(MarketDataBindingErrorV1) as exc:
        resolve_okx_venue_instrument_mapping_v1(
            canonical_instrument_id=CANONICAL_INSTRUMENT_ID,
            instruments_inventory=_inv("instruments_inactive.json"),
        )
    assert exc.value.error_class == "VENUE_INSTRUMENT_INACTIVE"


def test_returned_inst_id_mismatch_fail_closed() -> None:
    with pytest.raises(MarketDataBindingErrorV1) as exc:
        parse_public_mark_price_response_v1(
            load_fixture_json(FIX / "mark_price_mismatch_inst.json"),
            expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
            receive_ts_unix=RECEIVE_TS,
        )
    assert exc.value.error_class == "VENUE_INSTRUMENT_RESPONSE_MISMATCH"


def test_public_mark_price_valid_passes() -> None:
    mark = parse_public_mark_price_response_v1(
        load_fixture_json(FIX / "mark_price_valid.json"),
        expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
        receive_ts_unix=RECEIVE_TS,
        max_stale_seconds=5.0,
    )
    assert mark.mark_px == 3500.5
    assert mark.endpoint == MARK_PRICE_ENDPOINT
    assert mark.field == MARK_PRICE_FIELD


def test_empty_mark_price_fail_closed() -> None:
    with pytest.raises(MarketDataBindingErrorV1) as exc:
        parse_public_mark_price_response_v1(
            load_fixture_json(FIX / "mark_price_empty.json"),
            expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
            receive_ts_unix=RECEIVE_TS,
        )
    assert exc.value.error_class == "PUBLIC_MARK_PRICE_RESPONSE_EMPTY"


def test_missing_markpx_no_fallback() -> None:
    with pytest.raises(MarketDataBindingErrorV1) as exc:
        parse_public_mark_price_response_v1(
            load_fixture_json(FIX / "mark_price_missing_markpx.json"),
            expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
            receive_ts_unix=RECEIVE_TS,
        )
    assert exc.value.error_class == "REQUIRED_PRICE_FIELD_MISSING"


def test_invalid_markpx_fail_closed() -> None:
    with pytest.raises(MarketDataBindingErrorV1) as exc:
        parse_public_mark_price_response_v1(
            load_fixture_json(FIX / "mark_price_invalid.json"),
            expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
            receive_ts_unix=RECEIVE_TS,
        )
    assert exc.value.error_class == "INVALID_PRICE_VALUE"
    with pytest.raises(MarketDataBindingErrorV1):
        parse_public_mark_price_response_v1(
            {
                "code": "0",
                "data": [
                    {
                        "instId": CANONICAL_INSTRUMENT_ID,
                        "markPx": "nan",
                        "ts": str(int(RECEIVE_TS * 1000)),
                    }
                ],
            },
            expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
            receive_ts_unix=RECEIVE_TS,
        )


def test_missing_or_stale_timestamp_fail_closed() -> None:
    with pytest.raises(MarketDataBindingErrorV1) as exc:
        parse_public_mark_price_response_v1(
            load_fixture_json(FIX / "mark_price_missing_ts.json"),
            expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
            receive_ts_unix=RECEIVE_TS,
        )
    assert exc.value.error_class == "MARKET_DATA_TIMESTAMP_MISSING"
    with pytest.raises(MarketDataBindingErrorV1) as exc2:
        parse_public_mark_price_response_v1(
            load_fixture_json(FIX / "mark_price_stale.json"),
            expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
            receive_ts_unix=RECEIVE_TS,
            max_stale_seconds=5.0,
        )
    assert exc2.value.error_class == "MARKET_DATA_STALE"


def test_ticker_not_required_to_contain_markpx() -> None:
    assert REQUIRED_TICKER_PRICE_FIELD != "markPx"
    assert MARK_TO_MARKET_PRICE_SOURCE == "explicit_mid_price"
    ticker = parse_public_ticker_semantics_v1(
        load_fixture_json(FIX / "ticker_no_markpx.json"),
        expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
    )
    assert ticker.last == 3500.5
    assert ticker.bid_px == 3500.0
    with pytest.raises(EeaPublicMdTransportError) as exc:
        parse_ticker_mid_price_v1(
            {"code": "0", "data": [{"instId": CANONICAL_INSTRUMENT_ID, "markPx": "1"}]}
        )
    assert "markPx_not_on_ticker" in str(exc.value)


def test_ticker_fields_only_for_declared_semantics() -> None:
    ticker = parse_public_ticker_semantics_v1(
        load_fixture_json(FIX / "ticker_no_markpx.json"),
        expected_venue_instrument_id=CANONICAL_INSTRUMENT_ID,
    )
    assert ticker.endpoint == "/api/v5/market/ticker"
    assert set(ticker.to_dict()) >= {"last", "bid_px", "ask_px", "venue_instrument_id"}


def test_deterministic_schema_failure_does_not_reconnect() -> None:
    cls, reconnectable = classify_transport_message_v1("REQUIRED_PRICE_FIELD_MISSING:markPx")
    assert cls == "REQUIRED_PRICE_FIELD_MISSING"
    assert reconnectable is False
    err = MarketDataBindingErrorV1("REQUIRED_PRICE_FIELD_MISSING", "markPx")
    assert err.reconnectable is False


def test_transient_transport_failure_reconnectable() -> None:
    cls, reconnectable = classify_transport_message_v1("FETCH_FAILED:timeout")
    assert cls == "TRANSPORT_FAILURE"
    assert reconnectable is True
    cls2, reconnectable2 = classify_transport_message_v1("HTTP_503")
    assert reconnectable2 is True


def test_dual_identity_persisted_no_conflation() -> None:
    mapping = resolve_okx_venue_instrument_mapping_v1(
        canonical_instrument_id=CANONICAL_INSTRUMENT_ID,
        instruments_inventory=_inv(),
    )
    assert mapping.canonical_instrument_id == mapping.venue_instrument_id
    # Distinct fields must remain distinct keys even when values equal.
    d = mapping.to_dict()
    assert "canonical_instrument_id" in d and "venue_instrument_id" in d
    assert d["canonical_instrument_id"] != "ETH-USDT-SWAP"


def test_offline_probe_and_runtime_call_graph_to_first_normalization() -> None:
    probe = run_offline_okx_native_mark_price_binding_probe_v1(
        instruments_payload=load_fixture_json(FIX / "instruments_futures_live.json"),
        mark_price_payload=load_fixture_json(FIX / "mark_price_valid.json"),
        ticker_payload=load_fixture_json(FIX / "ticker_no_markpx.json"),
        receive_ts_unix=RECEIVE_TS,
        max_stale_seconds=5.0,
    )
    assert probe.ok, probe.blockers
    assert probe.authorization_consumed is False
    assert probe.wallclock_session_started is False
    assert probe.private_api_used is False
    assert probe.orders_created is False
    assert probe.normalized["canonical_instrument_id"] == CANONICAL_INSTRUMENT_ID
    assert probe.normalized["venue_instrument_id"] == CANONICAL_INSTRUMENT_ID
    assert probe.normalized["mark_price_endpoint"] == MARK_PRICE_ENDPOINT

    urls: list[str] = []

    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        urls.append(url)
        assert method == "GET"
        assert CANONICAL_HOST in url
        qs = parse_qs(urlparse(url).query)
        assert qs.get("instId") == [CANONICAL_INSTRUMENT_ID]
        if "/public/instruments" in url:
            body = load_fixture_json(FIX / "instruments_futures_live.json")
        elif "/public/mark-price" in url:
            body = load_fixture_json(FIX / "mark_price_valid.json")
        else:
            body = load_fixture_json(FIX / "ticker_no_markpx.json")
        return 200, json.dumps(body).encode("utf-8"), {}

    transport = EeaPublicMdTransportV1(fetcher=fetcher, environ={})
    transport.open()
    mapping = resolve_mapping_with_transport_inventory_v1(transport=transport)
    normalized = fetch_normalized_public_market_data_v1(
        transport=transport,
        mapping=mapping,
        receive_ts_unix=RECEIVE_TS,
        max_stale_seconds=5.0,
    )
    assert normalized.mark_px == 3500.5
    assert any("/public/mark-price" in u for u in urls)
    assert all("instId=ETH-USD_UM_XPERP-310404" in u for u in urls)


def test_no_private_order_testnet_live_reachability() -> None:
    from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1 import (
        constants_v1 as c,
    )

    assert c.PRIVATE_API_USED is False
    assert c.ORDER_ROUTING_REACHABLE is False
    assert c.ORDERS_CREATED is False
    assert c.TESTNET_EXECUTION_OCCURRED is False
    assert c.LIVE_EXECUTION_OCCURRED is False
    assert c.FORCED_FIXTURE_WALLCLOCK_REACHABLE is False
    pkg = REPO_ROOT / "src/ops/okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1"
    for path in pkg.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "/api/v5/trade/" not in text
        assert "/api/v5/account/" not in text


def test_failed_authorization_remains_consumed_exactly_once() -> None:
    assert FAILED_AUTH.is_file()
    assert FAILED_CONS.is_file()
    art = json.loads(FAILED_AUTH.read_text(encoding="utf-8"))
    cons = json.loads(FAILED_CONS.read_text(encoding="utf-8"))
    assert art["state"] == "CONSUMED"
    assert art["consumption_id"] == "cons_eba3914ae613dbdee38bccb1"
    assert cons["consumption_id"] == "cons_eba3914ae613dbdee38bccb1"
    assert (
        cons["authorization_digest_before"]
        == "fe99498326dd9e5f3a19dc07b1d56e969930f8eedc84068530d68179d5b1868f"
    )
    # No unconsume/reset helpers in new capability package.
    pkg = REPO_ROOT / "src/ops/okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1"
    for path in pkg.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "unconsume" not in text.lower()
        assert "reset_authorization" not in text.lower()
        assert "write_authorization_artifact" not in text


def test_no_automatic_replacement_authorization_or_implicit_retry() -> None:
    pkg = REPO_ROOT / "src/ops/okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1"
    for path in pkg.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "build_authorization_artifact" not in text
        assert "implicit_resume" not in text.lower() or "NO_IMPLICIT" in text
        assert "consume_authorization_artifact" not in text


def test_authority_inventory_complete() -> None:
    inv = verify_okx_native_instrument_mark_price_authority_inventory_v1(repo_root=REPO_ROOT)
    assert inv.ok, inv.blockers
    assert inv.canonical_instrument_authority_count == 1
    assert inv.venue_mapping_authority_count == 1
    assert inv.second_instrument_mapping_authority_present is False
    assert inv.direct_canonical_id_to_okx_transport_path_present is False
    assert inv.ticker_markpx_assumption_present is False
    assert inv.deterministic_schema_failure_reconnectable is False
    assert CAPABILITY_ID in inv.capability
