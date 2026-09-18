"""S2A: Composition-boundary pin at FreshPretradeGetTransportResultV1.

Pins the S2 adjudication offline:
- Earliest common typed carrier / composition candidate is
  FreshPretradeGetTransportResultV1 (post-get, pre-unwrap).
- Stamp-loss points A1/A2/A3 remain stamp-lossy.
- C1 does not require provenance.
- No DataSafetyGate join. No usage_context/LIVE_TRADE ratification.
- REAL is not regenerated outside FullCoreProductiveReadOnlyGetTransportV1.get.

AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.data.safety import DataSourceKind
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PInjectedGetV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    CurrentProductiveC1ObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    METHOD_GET,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    TRANSPORT_CLASS_MISSING,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    FreshPretradeGetItemEvidenceV1,
    FreshPretradeGetTransportResultV1,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    _transport_payload,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC_FRESH = (
    REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/fresh_pretrade_runtime_get_v1.py"
)
_SRC_TRANSPORT = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1/productive_read_only_get_transport_v1.py"
)
_SRC_V5 = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5.py"
)
_THIS_TEST = Path(__file__)
_PUBLIC_CANDLES = "/api/v5/market/candles?instId=0G-USDT-SWAP&bar=1m"
_FORENSIC_STAMP = DataSourceKind.REAL.value
_TRUSTED_PAYLOAD: dict[str, Any] = {"code": "0", "data": [{"instId": "BTC-USDT-SWAP"}]}


def _field_names(cls: type) -> set[str]:
    return {f.name for f in dataclasses.fields(cls)}


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


class _ForensicStampCarryingTransport:
    """Injected double that carries a non-None stamp only to prove A1/A2 drop.

    This is not a productive REAL producer. S1 producer authority is unchanged.
    """

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
    ) -> FreshPretradeGetTransportResultV1:
        del pretrade_decision_id
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method=METHOD_GET,
            endpoint=endpoint,
            http_status=200,
            payload=dict(_TRUSTED_PAYLOAD),
            auth_header_sent=bool(auth_required),
            transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
            venue_live_contact=False,
            historical_reuse=False,
            error_class="",
            data_safety_source_kind=_FORENSIC_STAMP,
        )


def test_carrier_surface_exposes_data_safety_source_kind() -> None:
    assert "data_safety_source_kind" in _field_names(FreshPretradeGetTransportResultV1)
    result = FreshPretradeGetTransportResultV1(
        get_performed=True,
        method=METHOD_GET,
        endpoint=_PUBLIC_CANDLES,
        http_status=200,
        payload={"code": "0", "data": []},
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
        venue_live_contact=True,
        historical_reuse=False,
        error_class="",
        data_safety_source_kind=_FORENSIC_STAMP,
    )
    assert result.data_safety_source_kind == _FORENSIC_STAMP


def test_item_evidence_and_c1_observation_do_not_expose_stamp_field() -> None:
    assert "data_safety_source_kind" not in _field_names(FreshPretradeGetItemEvidenceV1)
    assert "data_safety_source_kind" not in _field_names(CurrentProductiveC1ObservationV1)
    item = FreshPretradeGetItemEvidenceV1(
        item_id="INSTRUMENT_STATE",
        endpoint_path="/api/v5/public/instruments",
        auth_required=False,
        evidence_status="TRUSTED_PRESENT",
        reason_codes=(),
        get_performed=True,
        method=METHOD_GET,
        http_status=200,
        auth_header_sent=False,
        historical_reuse=False,
        transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
        venue_live_contact=True,
    )
    obs = CurrentProductiveC1ObservationV1(
        venue_event_time=1.0,
        confirm="1",
        native_id="BTC-USDT-SWAP",
        payload={"code": "0", "data": []},
    )
    assert not hasattr(item, "data_safety_source_kind")
    assert not hasattr(obs, "data_safety_source_kind")
    assert getattr(item, "data_safety_source_kind", None) is None
    assert getattr(obs, "data_safety_source_kind", None) is None


def test_a1_collect_item_evidence_drops_stamp() -> None:
    evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id="s2a-a1-decision",
        instrument_id="BTC-USDT-SWAP",
        td_mode="cross",
        transport=_ForensicStampCarryingTransport(),
        require_collection=True,
    )
    assert evidence.items
    for item in evidence.items:
        assert "data_safety_source_kind" not in _field_names(type(item))
        assert getattr(item, "data_safety_source_kind", None) is None
    fresh_src = _SRC_FRESH.read_text(encoding="utf-8")
    ctor_idx = fresh_src.index("FreshPretradeGetItemEvidenceV1(")
    ctor_window = fresh_src[ctor_idx : ctor_idx + 900]
    assert "data_safety_source_kind" not in ctor_window


def test_a2_transport_payload_unwrap_is_stamp_lossy() -> None:
    transport = _ForensicStampCarryingTransport()
    stamped = transport.get(
        endpoint=_PUBLIC_CANDLES,
        auth_required=False,
        pretrade_decision_id="s2a-a2",
    )
    assert stamped.data_safety_source_kind == _FORENSIC_STAMP
    payload, err = _transport_payload(
        transport,
        path="/api/v5/market/candles",
        query={"instId": "0G-USDT-SWAP", "bar": "1m"},
        auth_required=False,
        native_id="s2a-a2",
    )
    assert err == ""
    assert payload == _TRUSTED_PAYLOAD
    assert not isinstance(payload, FreshPretradeGetTransportResultV1)
    assert getattr(payload, "data_safety_source_kind", None) is None
    v5_src = _SRC_V5.read_text(encoding="utf-8")
    assert 'return result.payload, ""' in v5_src or "return result.payload, ''" in v5_src
    assert "data_safety_source_kind" not in inspect.getsource(_transport_payload)


def test_a3_payloads_by_path_stores_payload_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.dumps(_TRUSTED_PAYLOAD).encode("utf-8")
    url = f"https://{AUTHORIZED_HOST}{_PUBLIC_CANDLES}"
    _patch_opener(monkeypatch, status=200, body=body, url=url)
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=2)
    result = transport.get(
        endpoint=_PUBLIC_CANDLES,
        auth_required=False,
        pretrade_decision_id="s2a-a3",
    )
    assert result.data_safety_source_kind == DataSourceKind.REAL.value
    path_only = _PUBLIC_CANDLES.split("?", 1)[0]
    cached = transport.payloads_by_path[path_only]
    assert cached == result.payload
    assert not isinstance(cached, FreshPretradeGetTransportResultV1)
    assert getattr(cached, "data_safety_source_kind", None) is None
    transport_src = _SRC_TRANSPORT.read_text(encoding="utf-8")
    assert "self.payloads_by_path[path_only] = payload" in transport_src


def test_default_and_injected_remain_none() -> None:
    omitted = FreshPretradeGetTransportResultV1(
        get_performed=True,
        method=METHOD_GET,
        endpoint=_PUBLIC_CANDLES,
        http_status=200,
        payload={"code": "0", "data": []},
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
        venue_live_contact=False,
        historical_reuse=False,
        error_class="",
    )
    assert omitted.data_safety_source_kind is None
    missing = FreshPretradeGetTransportResultV1(
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
    assert missing.data_safety_source_kind is None
    injected = CurrentProductiveEnterLive29PInjectedGetV1(
        payload={"code": "0", "data": []},
        get_performed=True,
        http_status=200,
    )
    assert not hasattr(injected, "data_safety_source_kind")
    assert getattr(injected, "data_safety_source_kind", None) is None


def test_real_not_regenerated_outside_s1_producer() -> None:
    fresh_src = _SRC_FRESH.read_text(encoding="utf-8")
    transport_src = _SRC_TRANSPORT.read_text(encoding="utf-8")
    assert "VENUE_NATIVE_" not in transport_src
    assert "VENUE_NATIVE_" not in fresh_src
    assert transport_src.count("DataSourceKind.REAL.value") == 1
    assert "DataSourceKind.REAL" not in fresh_src
    assert "DataSourceKind.REAL.value if get_performed and venue_live_contact" in transport_src
    # Collector must not assign/copy the stamp.
    assert fresh_src.count("data_safety_source_kind:") == 1
    assert "data_safety_source_kind=" not in fresh_src.split("data_safety_source_kind:")[1][:200]


def test_pin_introduces_no_datasafetygate_or_usage_context_semantics() -> None:
    tree = ast.parse(_THIS_TEST.read_text(encoding="utf-8"))
    imported: set[str] = set()
    forbidden_names = frozenset(
        {
            "DataSafetyGate",
            "DataSafetyContext",
            "DataUsageContextKind",
            "ensure_allowed",
        }
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("src.data.safety"):
            for alias in node.names:
                imported.add(alias.name)
        if isinstance(node, ast.Name) and node.id in forbidden_names:
            raise AssertionError(f"unexpected safety symbol reference: {node.id}")
        if isinstance(node, ast.Attribute) and node.attr in {
            "DataSafetyGate",
            "DataSafetyContext",
            "DataUsageContextKind",
            "LIVE_TRADE",
        }:
            raise AssertionError(f"unexpected safety attribute reference: {node.attr}")
    # Only the DataSourceKind enum value is imported; no gate/context/usage join.
    assert imported == {"DataSourceKind"}
