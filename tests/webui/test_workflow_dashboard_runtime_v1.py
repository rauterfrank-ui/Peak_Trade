"""Dedicated contract tests for canonical workflow dashboard runtime v1."""

from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.webui.workflow_dashboard_readmodel_v1 import (
    READMODEL_ID,
    SCHEMA_VERSION,
    build_workflow_dashboard_readmodel_v1,
)
from src.webui.workflow_dashboard_runtime_v1 import (
    ENV_ARCHIVE_ROOT,
    ENV_ENABLED,
    build_workflow_dashboard_display_context,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ARCHIVE = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "pipeline_minimal"
    / "archive_root"
).resolve()

_EXPECTED_DISPLAY_CONTEXT_KEYS = frozenset(
    {
        "section_visible",
        "gate_enabled",
        "display_status",
        "readmodel",
        "error",
    }
)

_EXPECTED_READMODEL_PANEL_KEYS = (
    "universe_missing",
    "top20_missing",
    "selected_future_missing",
    "pipeline",
    "killswitch_recovery",
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
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(FIXTURE_ARCHIVE))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")
    return build_workflow_dashboard_display_context()


def test_public_runtime_entrypoints_are_canonical() -> None:
    assert ENV_ENABLED == "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED"
    assert ENV_ARCHIVE_ROOT == "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT"
    assert inspect.isfunction(build_workflow_dashboard_display_context)


def test_display_context_disabled_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    ctx = build_workflow_dashboard_display_context()
    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["section_visible"] is False
    assert ctx["gate_enabled"] is False
    assert ctx["display_status"] == "disabled"
    assert ctx["readmodel"] is None
    assert ctx["error"] is None


def test_display_context_invalid_enabled_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "0")
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(FIXTURE_ARCHIVE))
    ctx = build_workflow_dashboard_display_context()
    assert ctx["gate_enabled"] is False
    assert ctx["display_status"] == "disabled"
    assert ctx["readmodel"] is None


def test_display_context_unconfigured_fail_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    ctx = build_workflow_dashboard_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["section_visible"] is False
    assert ctx["display_status"] == "unconfigured"
    assert ctx["readmodel"] is None
    assert ctx["error"] is None


def test_display_context_invalid_archive_root_fail_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, "/nonexistent/peak_trade_workflow_dashboard_archive_root")
    ctx = build_workflow_dashboard_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["section_visible"] is False
    assert ctx["display_status"] == "unconfigured"
    assert ctx["readmodel"] is None


def test_display_context_ready_from_canonical_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    model = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)

    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["gate_enabled"] is True
    assert ctx["section_visible"] is True
    assert ctx["display_status"] in ("ready", "ready_with_warnings")
    assert ctx["error"] is None
    assert isinstance(ctx["readmodel"], dict)
    assert ctx["readmodel"]["schema_version"] == SCHEMA_VERSION
    assert ctx["readmodel"]["readmodel_id"] == READMODEL_ID
    assert ctx["readmodel"]["non_authorizing"] is True
    assert ctx["readmodel"]["load_status"] == model.load_status
    assert ctx["readmodel"]["pipeline"]["stage_count"] == model.pipeline.stage_count


def test_display_context_empty_archive_fail_soft(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty_archive = tmp_path / "empty_archive"
    empty_archive.mkdir()
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(empty_archive))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")
    ctx = build_workflow_dashboard_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["section_visible"] is True
    assert ctx["display_status"] == "ready_with_warnings"
    assert ctx["error"] is None
    assert isinstance(ctx["readmodel"], dict)
    assert "runs_directory_missing" in ctx["readmodel"]["load_errors"]
    assert ctx["readmodel"]["universe_selection"]["universe"] == []
    assert ctx["readmodel"]["universe_selection"]["ranking"] == []


def test_display_context_is_deterministic_for_identical_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _ready_context_from_fixture(monkeypatch)
    second = build_workflow_dashboard_display_context()
    assert first == second
    assert json.loads(json.dumps(first)) == first


def test_display_context_does_not_mutate_fixture_archive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = {path: path.read_bytes() for path in FIXTURE_ARCHIVE.rglob("*") if path.is_file()}
    _ready_context_from_fixture(monkeypatch)
    after = {path: path.read_bytes() for path in FIXTURE_ARCHIVE.rglob("*") if path.is_file()}
    assert before == after


def test_futures_operator_consumer_wires_runtime_builder() -> None:
    source = (PROJECT_ROOT / "src" / "webui" / "market_surface.py").read_text(encoding="utf-8")
    assert "build_workflow_dashboard_display_context" in source
    assert "workflow_dashboard" in source
    assert "market_single_page_consolidation" in source


def test_ready_readmodel_panel_contracts_present(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    readmodel = ctx["readmodel"]
    for panel_key in _EXPECTED_READMODEL_PANEL_KEYS:
        assert panel_key in readmodel

    assert readmodel["universe_missing"]["truth_status"] == "UNIVERSE_SOURCE_NOT_PERSISTED"
    assert readmodel["top20_missing"]["truth_status"] == "TOP20_RANKING_NOT_PERSISTED"
    assert readmodel["selected_future_missing"]["truth_status"] == "SELECTED_FUTURE_NOT_PERSISTED"
    assert readmodel["pipeline"]["stage_count"] == 7
    assert len(readmodel["pipeline"]["stages"]) == 7
    assert isinstance(readmodel["killswitch_recovery"]["entries"], list)


def test_ready_readmodel_panel_ordering_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    keys = list(ctx["readmodel"].keys())
    panel_indices = [keys.index(panel_key) for panel_key in _EXPECTED_READMODEL_PANEL_KEYS]
    assert panel_indices == sorted(panel_indices)


def test_ready_readmodel_empty_universe_and_ranking(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    selection = ctx["readmodel"]["universe_selection"]
    assert selection["loaded"] is False
    assert selection["universe"] == []
    assert selection["ranking"] == []
    assert selection["selected_future"] is None


def test_ready_readmodel_has_no_bitcoin_symbols(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    serialized = json.dumps(ctx["readmodel"])
    assert "BTC/USD" not in serialized
    assert "BTCUSD" not in serialized
    for row in ctx["readmodel"]["universe_selection"]["universe"]:
        symbol = str(row.get("symbol", "")).upper()
        for token in _BITCOIN_TOKENS:
            assert token not in symbol
    for row in ctx["readmodel"]["universe_selection"]["ranking"]:
        symbol = str(row.get("symbol", "")).upper()
        for token in _BITCOIN_TOKENS:
            assert token not in symbol


def test_runtime_outputs_have_no_forbidden_execution_authority_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    collected: set[str] = set()
    _collect_object_keys(ctx, collected)
    assert collected.isdisjoint(_FORBIDDEN_JSON_KEYS)
    assert ctx["readmodel"]["safety"]["LIVE_AUTHORIZED"] is False
    assert ctx["readmodel"]["safety"]["READY_FOR_OPERATOR_ARMING"] is False


def test_runtime_module_source_has_no_network_or_exchange_tokens() -> None:
    source = (PROJECT_ROOT / "src" / "webui" / "workflow_dashboard_runtime_v1.py").read_text(
        encoding="utf-8"
    )
    forbidden_tokens = ("ccxt", "kraken", "requests", "httpx", "aiohttp", "urllib")
    lowered = source.lower()
    for token in forbidden_tokens:
        assert token not in lowered


def test_disabled_context_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    first = build_workflow_dashboard_display_context()
    second = build_workflow_dashboard_display_context()
    assert first == second


def test_unconfigured_context_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    first = build_workflow_dashboard_display_context()
    second = deepcopy(first)
    assert build_workflow_dashboard_display_context() == second
