"""Dedicated contract tests for canonical F5 futures read-only market dashboard runtime v0."""

from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT,
    ENV_ENABLED,
    F1_FIELDS,
    F2_FIELDS,
    F3_FIELDS,
    F4_FIELDS,
    KRAKEN_FUTURES_TESTNET_ENV_NAME,
    READMODEL_ID,
    STATUS_MODEL_VALUES,
    build_futures_read_only_market_dashboard_display_context,
    enabled_explicitly_on,
    resolved_bundle_root_or_none,
)
from src.webui.market_instrument_eligibility_v0 import is_eligible_market_dashboard_instrument

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "futures_read_only_market_dashboard_v0"
    / "complete_minimal"
)
CANONICAL_INSTRUMENT_ID = "PF_ETHUSD"

_EXPECTED_DISPLAY_CONTEXT_KEYS = frozenset(
    {
        "gate_enabled",
        "display_status",
        "readmodel_id",
        "non_authorizing",
        "summary_line",
        "overall_status",
        "env_name",
        "kraken_futures_testnet_label",
        "status_model_values",
        "authority",
        "f1",
        "f2",
        "f3",
        "f4",
    }
)

_EXPECTED_AUTHORITY_KEYS = frozenset(
    {
        "provider_truth",
        "dashboard_truth",
        "trading_readiness",
        "selected_future_truth",
        "execution_readiness",
        "liquidity_truth",
        "slippage_truth",
        "depth_truth",
    }
)

_FORBIDDEN_JSON_KEYS = frozenset(
    {
        "order",
        "orders",
        "order_id",
        "create_order",
        "submit_order",
        "execute",
        "execution",
        "execution_authorized",
        "live_authorized",
        "ready_for_operator_arming",
        "armed",
        "enabled",
        "credentials",
        "credential",
        "api_key",
        "api_secret",
        "private_key",
        "authority_lift",
        "promotion",
        "approve",
        "approved",
        "side_recommendation",
        "trade_recommendation",
    }
)

_BITCOIN_TOKENS = ("BTC", "XBT", "BITCOIN")


def _collect_object_keys(obj: object, out: set[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                out.add(key)
            _collect_object_keys(value, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_object_keys(item, out)


def _ready_context_from_fixture(monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(FIXTURE_ROOT))
    return build_futures_read_only_market_dashboard_display_context()


def _section_row_fields(section: dict) -> list[str]:
    return [row["field"] for row in section["rows"]]


def test_public_runtime_entrypoints_are_canonical() -> None:
    assert ENV_ENABLED == "PEAK_TRADE_F5_MARKET_DASHBOARD_ENABLED"
    assert ENV_BUNDLE_ROOT == "PEAK_TRADE_F5_MARKET_DASHBOARD_BUNDLE_ROOT"
    assert READMODEL_ID == "futures_read_only_market_dashboard_v0"
    for fn in (
        enabled_explicitly_on,
        resolved_bundle_root_or_none,
        build_futures_read_only_market_dashboard_display_context,
    ):
        assert inspect.isfunction(fn)


def test_enabled_explicitly_on_fail_closed_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    assert enabled_explicitly_on() is False
    monkeypatch.setenv(ENV_ENABLED, "0")
    assert enabled_explicitly_on() is False
    monkeypatch.setenv(ENV_ENABLED, "invalid")
    assert enabled_explicitly_on() is False
    monkeypatch.setenv(ENV_ENABLED, "1")
    assert enabled_explicitly_on() is True


def test_resolved_bundle_root_or_none_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    assert resolved_bundle_root_or_none() is None
    monkeypatch.setenv(ENV_BUNDLE_ROOT, "")
    assert resolved_bundle_root_or_none() is None
    monkeypatch.setenv(ENV_BUNDLE_ROOT, "/nonexistent/path/for/f5/runtime")
    assert resolved_bundle_root_or_none() is None
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(FIXTURE_ROOT))
    assert resolved_bundle_root_or_none() == FIXTURE_ROOT.resolve()


def test_display_context_disabled_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    ctx = build_futures_read_only_market_dashboard_display_context()
    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["gate_enabled"] is False
    assert ctx["display_status"] == "disabled"
    assert ctx["readmodel_id"] == READMODEL_ID
    assert ctx["non_authorizing"] is True
    assert ctx["overall_status"] == "futures_metadata_missing"
    assert ctx["f1"]["status"] == "futures_metadata_missing"
    assert ctx["f2"]["status"] == "provenance_missing"
    assert ctx["f3"]["status"] == "backtest_realism_incomplete"
    assert ctx["f4"]["status"] == "risk_safety_incomplete"


def test_display_context_unconfigured_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    ctx = build_futures_read_only_market_dashboard_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "unconfigured"
    assert ctx["overall_status"] == "futures_metadata_missing"
    assert ctx["non_authorizing"] is True


def test_display_context_missing_dashboard_json_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(tmp_path))
    ctx = build_futures_read_only_market_dashboard_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "builder_error"
    assert ctx["overall_status"] == "futures_metadata_missing"


def test_display_context_malformed_dashboard_json_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "dashboard.json").write_text("{not-valid-json", encoding="utf-8")
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(tmp_path))
    ctx = build_futures_read_only_market_dashboard_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "builder_error"
    assert ctx["overall_status"] == "futures_metadata_missing"


def test_display_context_non_dict_dashboard_payload_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "dashboard.json").write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(tmp_path))
    ctx = build_futures_read_only_market_dashboard_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "builder_error"


def test_display_context_ready_from_canonical_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    fixture = json.loads((FIXTURE_ROOT / "dashboard.json").read_text(encoding="utf-8"))

    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "ready"
    assert ctx["readmodel_id"] == READMODEL_ID
    assert ctx["non_authorizing"] is True
    assert ctx["overall_status"] == fixture["overall_status"]
    assert ctx["env_name"] == KRAKEN_FUTURES_TESTNET_ENV_NAME
    assert ctx["kraken_futures_testnet_label"] is True
    assert ctx["status_model_values"] == list(STATUS_MODEL_VALUES)
    assert ctx["f1"]["status"] == "futures_metadata_partial"
    assert ctx["f2"]["status"] == "provenance_missing"
    assert ctx["f3"]["status"] == "backtest_realism_incomplete"
    assert ctx["f4"]["status"] == "risk_safety_incomplete"


def test_f1_metadata_field_ordering_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    assert _section_row_fields(ctx["f1"]) == list(F1_FIELDS)


def test_f2_metadata_field_ordering_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    assert _section_row_fields(ctx["f2"]) == list(F2_FIELDS)


def test_f3_metadata_field_ordering_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    assert _section_row_fields(ctx["f3"]) == list(F3_FIELDS)


def test_f4_metadata_field_ordering_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    assert _section_row_fields(ctx["f4"]) == list(F4_FIELDS)


def test_f1_partial_metadata_from_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    rows = {row["field"]: row for row in ctx["f1"]["rows"]}
    assert rows["instrument_id"]["value"] == CANONICAL_INSTRUMENT_ID
    assert rows["instrument_id"]["display_status"] == "present"
    assert rows["exchange"]["value"] == "kraken"
    assert rows["market_type"]["value"] == "futures"
    assert rows["lot_size"]["value"] == "missing"
    assert rows["lot_size"]["display_status"] == "missing"


def test_malformed_f1_section_normalizes_to_missing_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.loads((FIXTURE_ROOT / "dashboard.json").read_text(encoding="utf-8"))
    payload["f1"] = "not-a-dict"
    (tmp_path / "dashboard.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(tmp_path))
    ctx = build_futures_read_only_market_dashboard_display_context()
    assert ctx["display_status"] == "ready"
    assert ctx["f1"]["status"] == "futures_metadata_partial"
    assert all(row["display_status"] == "missing" for row in ctx["f1"]["rows"])


def test_display_context_is_deterministic_for_identical_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _ready_context_from_fixture(monkeypatch)
    second = build_futures_read_only_market_dashboard_display_context()
    assert first == second
    assert json.loads(json.dumps(first)) == first


def test_display_context_does_not_mutate_fixture_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = (FIXTURE_ROOT / "dashboard.json").read_text(encoding="utf-8")
    _ready_context_from_fixture(monkeypatch)
    after = (FIXTURE_ROOT / "dashboard.json").read_text(encoding="utf-8")
    assert before == after


def test_authority_boundaries_all_false_on_fail_closed_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    disabled = build_futures_read_only_market_dashboard_display_context()
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    unconfigured = build_futures_read_only_market_dashboard_display_context()
    for ctx in (disabled, unconfigured):
        assert set(ctx["authority"].keys()) == _EXPECTED_AUTHORITY_KEYS
        assert all(value is False for value in ctx["authority"].values())


def test_authority_boundaries_all_false_on_ready_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    assert set(ctx["authority"].keys()) == _EXPECTED_AUTHORITY_KEYS
    assert all(value is False for value in ctx["authority"].values())


def test_futures_only_non_bitcoin_instrument_in_ready_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    instrument_id = next(
        row["value"]
        for row in ctx["f1"]["rows"]
        if row["field"] == "instrument_id" and row["display_status"] == "present"
    )
    assert instrument_id == CANONICAL_INSTRUMENT_ID
    assert is_eligible_market_dashboard_instrument(instrument_id)
    upper = instrument_id.upper()
    for token in _BITCOIN_TOKENS:
        assert token not in upper


def test_display_context_non_authorizing_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    assert ctx["non_authorizing"] is True


def test_runtime_outputs_have_no_forbidden_execution_authority_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    disabled = build_futures_read_only_market_dashboard_display_context()
    ready = _ready_context_from_fixture(monkeypatch)
    for ctx in (disabled, ready):
        collected: set[str] = set()
        _collect_object_keys(ctx, collected)
        assert collected.isdisjoint(_FORBIDDEN_JSON_KEYS)


def test_runtime_module_source_has_no_network_or_exchange_imports() -> None:
    source = (
        PROJECT_ROOT / "src" / "webui" / "futures_read_only_market_dashboard_runtime_v0.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden_import in (
        "import requests",
        "import httpx",
        "import aiohttp",
        "from src.execution",
        "from src.broker",
        "from src.exchange",
    ):
        assert forbidden_import not in lowered
    assert "build_market_payload" not in source


def test_fail_closed_paths_preserve_metadata_section_structure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    ctx = build_futures_read_only_market_dashboard_display_context()
    for section_name, fields in (
        ("f1", F1_FIELDS),
        ("f2", F2_FIELDS),
        ("f3", F3_FIELDS),
        ("f4", F4_FIELDS),
    ):
        section = ctx[section_name]
        assert _section_row_fields(section) == list(fields)
        assert deepcopy(section["rows"]) == section["rows"]
