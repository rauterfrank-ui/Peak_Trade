"""S1: DataSafety source_kind stamp at productive Venue-GET producer only.

REAL may be produced only by FullCoreProductiveReadOnlyGetTransportV1.get when
direct venue-acquisition evidence is present. Injected / missing / failed paths
remain UNBOUND (None). No VENUE_NATIVE_* remapping. No DataSafetyGate join.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.data.safety import DataSourceKind
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PInjectedGetV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    METHOD_GET,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    TRANSPORT_CLASS_MISSING,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreProductiveReadOnlyGetTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC_FRESH = (
    REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/fresh_pretrade_runtime_get_v1.py"
)
_SRC_TRANSPORT = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1/productive_read_only_get_transport_v1.py"
)
_PUBLIC_CANDLES = "/api/v5/market/candles?instId=0G-USDT-SWAP&bar=1m"


class _FakeResp:
    def __init__(self, *, status: int, body: bytes, url: str) -> None:
        self.status = status
        self._body = body
        self.url = url

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _patch_opener(monkeypatch: pytest.MonkeyPatch, *, status: int, body: bytes, url: str) -> None:
    opener = MagicMock()
    opener.open.return_value = _FakeResp(status=status, body=body, url=url)

    def _build_opener(*_args: object, **_kwargs: object) -> MagicMock:
        return opener

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1"
        ".productive_read_only_get_transport_v1.build_opener",
        _build_opener,
    )


def test_successful_productive_venue_get_stamps_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.dumps({"code": "0", "data": [{"ts": "1", "confirm": "1"}]}).encode("utf-8")
    url = f"https://{AUTHORIZED_HOST}{_PUBLIC_CANDLES}"
    _patch_opener(monkeypatch, status=200, body=body, url=url)
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=4)
    result = transport.get(
        endpoint=_PUBLIC_CANDLES,
        auth_required=False,
        pretrade_decision_id="s1-decision",
    )
    assert result.get_performed is True
    assert result.venue_live_contact is True
    assert result.historical_reuse is False
    assert result.transport_class == TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
    assert result.data_safety_source_kind == DataSourceKind.REAL.value


def test_failed_productive_get_leaves_source_kind_unbound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = f"https://{AUTHORIZED_HOST}{_PUBLIC_CANDLES}"
    _patch_opener(monkeypatch, status=500, body=b"{}", url=url)
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=4)
    result = transport.get(
        endpoint=_PUBLIC_CANDLES,
        auth_required=False,
        pretrade_decision_id="s1-decision",
    )
    assert result.get_performed is False
    assert result.data_safety_source_kind is None


def test_injected_test_double_result_constructor_defaults_to_none() -> None:
    result = FreshPretradeGetTransportResultV1(
        get_performed=True,
        method=METHOD_GET,
        endpoint=_PUBLIC_CANDLES,
        http_status=200,
        payload={"code": "0", "data": []},
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        venue_live_contact=True,
        historical_reuse=False,
        error_class="",
    )
    assert result.data_safety_source_kind is None


def test_transport_missing_constructor_defaults_to_none() -> None:
    result = FreshPretradeGetTransportResultV1(
        get_performed=False,
        method=METHOD_GET,
        endpoint=_PUBLIC_CANDLES,
        http_status=0,
        payload=None,
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_MISSING,
        venue_live_contact=False,
        historical_reuse=False,
        error_class="TRANSPORT_MISSING",
    )
    assert result.data_safety_source_kind is None


def test_enter_live_29p_injected_get_has_no_real_source_kind() -> None:
    injected = CurrentProductiveEnterLive29PInjectedGetV1(
        payload={"code": "0", "data": []},
        get_performed=True,
        http_status=200,
    )
    assert not hasattr(injected, "data_safety_source_kind")
    assert getattr(injected, "data_safety_source_kind", None) is None


def test_backward_compatible_constructor_omitting_field_is_none() -> None:
    result = FreshPretradeGetTransportResultV1(
        get_performed=True,
        method=METHOD_GET,
        endpoint="/api/v5/public/instruments",
        http_status=200,
        payload={"code": "0", "data": []},
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        venue_live_contact=False,
        historical_reuse=False,
        error_class="",
        body_sha256="abc",
    )
    assert result.data_safety_source_kind is None


def test_no_venue_native_remap_and_sole_real_producer_in_allowed_sources() -> None:
    fresh_src = _SRC_FRESH.read_text(encoding="utf-8")
    transport_src = _SRC_TRANSPORT.read_text(encoding="utf-8")
    assert "VENUE_NATIVE_" not in transport_src
    assert "VENUE_NATIVE_" not in fresh_src
    assert "DataSourceKind.REAL.value" in transport_src
    assert "DataSourceKind.REAL" not in fresh_src
    assert transport_src.count("DataSourceKind.REAL.value") == 1
    assert "data_safety_source_kind=" in transport_src
    assert "if transport_class" not in transport_src
    assert "DataSourceKind.REAL.value if get_performed and venue_live_contact" in transport_src
    # Only the productive GET producer module assigns REAL.
    assert fresh_src.count("data_safety_source_kind:") == 1
    assert "data_safety_source_kind=" not in fresh_src.split("data_safety_source_kind:")[1][:200]
