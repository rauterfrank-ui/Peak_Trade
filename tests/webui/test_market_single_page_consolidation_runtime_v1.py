"""Dedicated contract tests for canonical market single-page consolidation runtime v1."""

from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.webui.market_surface import (
    MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV,
    build_market_payload_for_page,
    build_market_single_page_consolidation_display_context,
    build_market_v0_page_template_context,
)
from src.webui.workflow_dashboard_runtime_v1 import (
    ENV_ARCHIVE_ROOT as WORKFLOW_ENV_ARCHIVE_ROOT,
    ENV_ENABLED as WORKFLOW_ENV_ENABLED,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_FIXTURE_ARCHIVE = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "pipeline_minimal"
    / "archive_root"
).resolve()
LPR_FIXTURE_ROOT = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "last_paper_run_panel_readmodel_v0"
    / "p1_complete_minimal"
).resolve()

_EXPECTED_DISPLAY_CONTEXT_KEYS = frozenset({"section_visible", "gate_enabled"})

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


def _minimal_page_template_context(monkeypatch: pytest.MonkeyPatch) -> dict:
    payload, data_unavailable = build_market_payload_for_page(
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        source="dummy",
    )
    return build_market_v0_page_template_context(
        get_project_status=lambda: {"ok": True},
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        source="dummy",
        payload=payload,
        data_unavailable=data_unavailable,
    )


def _configure_consolidation_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, "1")
    monkeypatch.setenv(WORKFLOW_ENV_ENABLED, "1")
    monkeypatch.setenv(WORKFLOW_ENV_ARCHIVE_ROOT, str(WORKFLOW_FIXTURE_ARCHIVE))
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT", str(LPR_FIXTURE_ROOT))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")


def test_public_runtime_entrypoints_are_canonical() -> None:
    assert MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV == (
        "PEAK_TRADE_MARKET_SINGLE_PAGE_CONSOLIDATION_V1_ENABLED"
    )
    assert inspect.isfunction(build_market_single_page_consolidation_display_context)


def test_display_context_disabled_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, raising=False)
    ctx = build_market_single_page_consolidation_display_context()
    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["section_visible"] is False
    assert ctx["gate_enabled"] is False


def test_display_context_invalid_enabled_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    for invalid in ("0", "invalid", "true", "yes"):
        monkeypatch.setenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, invalid)
        ctx = build_market_single_page_consolidation_display_context()
        assert ctx["gate_enabled"] is False
        assert ctx["section_visible"] is False


def test_display_context_enabled_gate_open(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, "1")
    ctx = build_market_single_page_consolidation_display_context()
    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["gate_enabled"] is True
    assert ctx["section_visible"] is True


def test_display_context_unconfigured_matches_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, raising=False)
    ctx = build_market_single_page_consolidation_display_context()
    assert ctx["gate_enabled"] is False
    assert ctx["section_visible"] is False


def test_display_context_is_deterministic_for_identical_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, "1")
    first = build_market_single_page_consolidation_display_context()
    second = build_market_single_page_consolidation_display_context()
    assert first == second
    assert json.loads(json.dumps(first)) == first


def test_display_context_does_not_mutate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, "1")
    before = dict(__import__("os").environ)
    build_market_single_page_consolidation_display_context()
    assert dict(__import__("os").environ) == before


def test_futures_operator_consumer_wires_consolidation_and_panel_builders() -> None:
    source = (PROJECT_ROOT / "src" / "webui" / "market_surface.py").read_text(encoding="utf-8")
    assert "build_market_single_page_consolidation_display_context" in source
    assert "build_workflow_dashboard_display_context" in source
    assert "build_last_paper_run_panel_display_context" in source
    assert 'if market_single_page_consolidation["section_visible"]:' in source
    assert "f5_dashboard" in source
    assert "futures_ohlcv" in source


def test_page_template_omits_panels_when_consolidation_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, raising=False)
    ctx = _minimal_page_template_context(monkeypatch)
    consolidation = ctx["market_single_page_consolidation"]
    assert consolidation["gate_enabled"] is False
    assert consolidation["section_visible"] is False
    assert ctx["workflow_dashboard"] is None
    assert ctx["last_paper_run_panel"] is None


def test_page_template_embeds_workflow_panel_when_consolidation_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_consolidation_on(monkeypatch)
    ctx = _minimal_page_template_context(monkeypatch)
    assert ctx["market_single_page_consolidation"]["section_visible"] is True
    workflow = ctx["workflow_dashboard"]
    assert isinstance(workflow, dict)
    assert workflow["gate_enabled"] is True
    assert workflow["section_visible"] is True
    assert workflow["display_status"] in {"ready", "ready_with_warnings"}
    assert isinstance(workflow["readmodel"], dict)


def test_page_template_embeds_last_paper_run_panel_when_consolidation_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_consolidation_on(monkeypatch)
    ctx = _minimal_page_template_context(monkeypatch)
    panel = ctx["last_paper_run_panel"]
    assert isinstance(panel, dict)
    assert panel["gate_enabled"] is True
    assert panel["section_visible"] is True
    assert panel["display_status"] == "ready"
    assert isinstance(panel["readmodel"], dict)


def test_page_template_panel_ordering_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_consolidation_on(monkeypatch)
    ctx = _minimal_page_template_context(monkeypatch)
    keys = list(ctx.keys())
    assert keys.index("workflow_dashboard") < keys.index("last_paper_run_panel")


def test_page_template_missing_workflow_env_fail_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, "1")
    monkeypatch.delenv(WORKFLOW_ENV_ENABLED, raising=False)
    monkeypatch.delenv(WORKFLOW_ENV_ARCHIVE_ROOT, raising=False)
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT", str(LPR_FIXTURE_ROOT))
    ctx = _minimal_page_template_context(monkeypatch)
    workflow = ctx["workflow_dashboard"]
    assert isinstance(workflow, dict)
    assert workflow["display_status"] == "disabled"
    assert workflow["readmodel"] is None


def test_page_template_missing_last_paper_env_fail_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, "1")
    monkeypatch.setenv(WORKFLOW_ENV_ENABLED, "1")
    monkeypatch.setenv(WORKFLOW_ENV_ARCHIVE_ROOT, str(WORKFLOW_FIXTURE_ARCHIVE))
    monkeypatch.delenv("PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT", raising=False)
    ctx = _minimal_page_template_context(monkeypatch)
    panel = ctx["last_paper_run_panel"]
    assert isinstance(panel, dict)
    assert panel["display_status"] == "disabled"
    assert panel["readmodel"] is None


def test_page_template_malformed_workflow_archive_fail_soft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, "1")
    monkeypatch.setenv(WORKFLOW_ENV_ENABLED, "1")
    monkeypatch.setenv(
        WORKFLOW_ENV_ARCHIVE_ROOT, str(PROJECT_ROOT / "tests" / "fixtures" / "missing")
    )
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT", str(LPR_FIXTURE_ROOT))
    ctx = _minimal_page_template_context(monkeypatch)
    workflow = ctx["workflow_dashboard"]
    assert isinstance(workflow, dict)
    assert workflow["gate_enabled"] is True
    assert workflow["display_status"] in {"unconfigured", "ready_with_warnings", "error", "disabled"}
    assert workflow["readmodel"] is None or isinstance(workflow["readmodel"], dict)


def test_consolidation_outputs_have_no_forbidden_execution_authority_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_consolidation_on(monkeypatch)
    ctx = _minimal_page_template_context(monkeypatch)
    collected: set[str] = set()
    _collect_object_keys(ctx["market_single_page_consolidation"], collected)
    assert collected.isdisjoint(_FORBIDDEN_JSON_KEYS)


def test_page_template_futures_context_present_with_consolidation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_consolidation_on(monkeypatch)
    ctx = _minimal_page_template_context(monkeypatch)
    assert isinstance(ctx["f5_dashboard"], dict)
    assert isinstance(ctx["futures_ohlcv"], dict)
    assert isinstance(ctx["governed_top20"], dict)


def test_page_template_has_no_bitcoin_symbols_in_consolidation_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_consolidation_on(monkeypatch)
    ctx = _minimal_page_template_context(monkeypatch)
    serialized = json.dumps(
        {
            "consolidation": ctx["market_single_page_consolidation"],
            "workflow": ctx["workflow_dashboard"],
            "last_paper_run": ctx["last_paper_run_panel"],
        }
    )
    assert "BTC/USD" not in serialized
    assert "BTCUSD" not in serialized
    for token in _BITCOIN_TOKENS:
        assert token not in serialized.upper()


def test_consolidation_builder_source_has_no_network_or_exchange_tokens() -> None:
    source = (PROJECT_ROOT / "src" / "webui" / "market_surface.py").read_text(encoding="utf-8")
    start = source.index("def build_market_single_page_consolidation_display_context")
    end = source.index("def build_market_run_projection_display_context", start)
    section = source[start:end].lower()
    for token in ("ccxt", "requests", "httpx", "aiohttp", "urllib"):
        assert token not in section


def test_disabled_context_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, raising=False)
    first = build_market_single_page_consolidation_display_context()
    second = build_market_single_page_consolidation_display_context()
    assert first == second


def test_enabled_context_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(MARKET_SINGLE_PAGE_CONSOLIDATION_ENABLED_ENV, "1")
    first = build_market_single_page_consolidation_display_context()
    second = deepcopy(first)
    assert build_market_single_page_consolidation_display_context() == second
