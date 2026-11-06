"""Contract tests for productive natural market-data capture transport wrapper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    FreshPretradeGetTransportResultV1,
    METHOD_GET,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from src.ops.full_core_live_path_composition_root_v1.productive_natural_market_data_capture_sink_v1 import (
    CAPTURE_LEDGER_FILENAME,
    GET_KIND_CANDLES,
    GET_KIND_MARK,
    NATURAL_MARKET_DATA_CAPTURE_SCHEMA_VERSION,
    ProductiveNaturalMarketDataCaptureError,
    ProductiveNaturalMarketDataCaptureSinkV1,
    ProductiveNaturalMarketDataCaptureTransportV1,
    classify_natural_market_data_get_kind_v1,
    wrap_productive_transport_with_natural_market_data_capture_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    GET_PATH,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)


def _result(
    *,
    endpoint: str,
    payload: dict[str, Any] | None,
    body_sha256: str = "abc",
) -> FreshPretradeGetTransportResultV1:
    return FreshPretradeGetTransportResultV1(
        get_performed=payload is not None,
        method=METHOD_GET,
        endpoint=endpoint,
        http_status=200 if payload is not None else 500,
        payload=payload,
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
        venue_live_contact=payload is not None,
        historical_reuse=False,
        error_class="",
        body_sha256=body_sha256 if payload is not None else "",
    )


class _StubDelegate:
    def __init__(self, result: FreshPretradeGetTransportResultV1) -> None:
        self.result = result
        self.calls = 0
        self.request_count = 0

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
        get_cache_policy: str = "",
    ) -> FreshPretradeGetTransportResultV1:
        del endpoint, auth_required, pretrade_decision_id, get_cache_policy
        self.calls += 1
        self.request_count += 1
        return self.result


def test_classify_get_kind_v1() -> None:
    assert (
        classify_natural_market_data_get_kind_v1(
            endpoint=f"{GET_PATH}?instId=CT-USDT-SWAP&bar=1m&limit=100"
        )
        == GET_KIND_CANDLES
    )
    assert (
        classify_natural_market_data_get_kind_v1(
            endpoint=f"{ENDPOINT_PUBLIC_MARK_PRICE}?instId=CT-USDT-SWAP"
        )
        == GET_KIND_MARK
    )


def test_wrapper_single_delegate_call_and_return_identity(tmp_path: Path) -> None:
    endpoint = f"{GET_PATH}?instId=CT-USDT-SWAP&bar=1m&limit=2"
    payload = {"code": "0", "data": []}
    delegate_result = _result(endpoint=endpoint, payload=payload, body_sha256="deadbeef")
    delegate = _StubDelegate(delegate_result)
    sink = ProductiveNaturalMarketDataCaptureSinkV1(
        evidence_root=tmp_path,
        run_id="run-a",
        native_id="CT-USDT-SWAP",
    )
    wrapped = ProductiveNaturalMarketDataCaptureTransportV1(delegate=delegate, sink=sink)
    out = wrapped.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="continuous-run-run-a-poll-0",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    assert delegate.calls == 1
    assert out is delegate_result
    assert out.payload == payload
    assert out.body_sha256 == "deadbeef"
    assert wrapped.request_count == 1


def test_wrapper_skips_capture_on_unsuccessful_get(tmp_path: Path) -> None:
    endpoint = f"{GET_PATH}?instId=CT-USDT-SWAP&bar=1m&limit=2"
    delegate = _StubDelegate(_result(endpoint=endpoint, payload=None))
    sink = ProductiveNaturalMarketDataCaptureSinkV1(
        evidence_root=tmp_path,
        run_id="run-b",
        native_id="CT-USDT-SWAP",
    )
    wrapped = ProductiveNaturalMarketDataCaptureTransportV1(delegate=delegate, sink=sink)
    out = wrapped.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="x",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    assert out.get_performed is False
    assert not (tmp_path / CAPTURE_LEDGER_FILENAME).exists()


def test_wrapper_propagates_delegate_exception(tmp_path: Path) -> None:
    class _ExplodingDelegate:
        def get(self, **kwargs: Any) -> FreshPretradeGetTransportResultV1:
            del kwargs
            raise RuntimeError("delegate-boom")

        request_count = 0

    sink = ProductiveNaturalMarketDataCaptureSinkV1(
        evidence_root=tmp_path,
        run_id="run-c",
        native_id="CT-USDT-SWAP",
    )
    wrapped = ProductiveNaturalMarketDataCaptureTransportV1(
        delegate=_ExplodingDelegate(),  # type: ignore[arg-type]
        sink=sink,
    )
    with pytest.raises(RuntimeError, match="delegate-boom"):
        wrapped.get(
            endpoint=f"{GET_PATH}?instId=X",
            auth_required=False,
            pretrade_decision_id="x",
        )


def test_append_only_and_schema_fields(tmp_path: Path) -> None:
    sink = ProductiveNaturalMarketDataCaptureSinkV1(
        evidence_root=tmp_path,
        run_id="run-d",
        native_id="CT-USDT-SWAP",
    )
    endpoint = f"{GET_PATH}?instId=CT-USDT-SWAP&bar=1m&limit=2"
    payload = {"code": "0", "data": [["ts", "o", "h", "l", "c", "vol", "1"]]}
    result = _result(endpoint=endpoint, payload=payload, body_sha256="sha1")
    sink.append_successful_get_v1(
        result=result,
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="continuous-run-run-d-poll-3",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    sink.append_successful_get_v1(
        result=result,
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="continuous-run-run-d-mark-3",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    lines = (tmp_path / CAPTURE_LEDGER_FILENAME).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    row0 = json.loads(lines[0])
    row1 = json.loads(lines[1])
    assert row0["schema_version"] == NATURAL_MARKET_DATA_CAPTURE_SCHEMA_VERSION
    assert row0["capture_sequence"] == 0
    assert row1["capture_sequence"] == 1
    assert row0["payload"] == payload
    assert row0["body_sha256"] == "sha1"
    assert row0["get_cache_policy"] == GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED
    assert row0["get_kind"] == GET_KIND_CANDLES
    assert row0["complete_poll_bundle_proven"] is False
    assert row0["correlation_status"] == "PARTIAL"


def test_capture_write_failure_propagates(tmp_path: Path) -> None:
    sink = ProductiveNaturalMarketDataCaptureSinkV1(
        evidence_root=tmp_path,
        run_id="run-e",
        native_id="CT-USDT-SWAP",
    )
    endpoint = f"{GET_PATH}?instId=CT-USDT-SWAP"
    result = _result(endpoint=endpoint, payload={"code": "0", "data": []})
    with mock.patch.object(Path, "open", side_effect=OSError("disk-full")):
        with pytest.raises(OSError, match="disk-full"):
            sink.append_successful_get_v1(
                result=result,
                endpoint=endpoint,
                auth_required=False,
                pretrade_decision_id="x",
                get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
            )


def test_wrap_helper_returns_delegate_attributes() -> None:
    inner = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=7)
    wrapped = wrap_productive_transport_with_natural_market_data_capture_v1(
        inner,
        evidence_root=Path("/tmp/evidence"),
        run_id="r",
        native_id="CT-USDT-SWAP",
    )
    assert wrapped.max_request_count == 7


def test_product_entry_capture_flag_default_off() -> None:
    import scripts.ops.run_current_productive_policy_governed_live_c1_pre_external_convergence_v1 as mod

    parser = mod.argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--lane-state-root", type=Path)
    parser.add_argument("--productivity-root", type=Path)
    parser.add_argument("--binding-epoch", default=None)
    parser.add_argument("--wp-branch-evidence-run", action="store_true")
    parser.add_argument(
        "--enable-natural-market-data-capture-v1",
        action="store_true",
        help="Append-only capture of natural read-only GET payloads under evidence-root",
    )
    args = parser.parse_args([])
    assert args.enable_natural_market_data_capture_v1 is False
