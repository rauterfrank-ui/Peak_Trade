"""Dedicated contract tests for canonical last paper run panel runtime v0."""

from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.webui.last_paper_run_panel_readmodel_v0 import (
    READMODEL_ID,
    SCHEMA_VERSION,
    build_last_paper_run_panel_readmodel_v0,
)
from src.webui.last_paper_run_panel_runtime_v0 import (
    ENV_BUNDLE_ROOT,
    ENV_ENABLED,
    build_last_paper_run_panel_display_context,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "last_paper_run_panel_readmodel_v0"
    / "p1_complete_minimal"
)

_EXPECTED_DISPLAY_CONTEXT_KEYS = frozenset(
    {
        "section_visible",
        "gate_enabled",
        "display_status",
        "readmodel",
        "error",
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
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T00:00:02+00:00")
    return build_last_paper_run_panel_display_context()


def test_public_runtime_entrypoints_are_canonical() -> None:
    assert ENV_ENABLED == "PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED"
    assert ENV_BUNDLE_ROOT == "PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT"
    assert inspect.isfunction(build_last_paper_run_panel_display_context)


def test_display_context_disabled_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    ctx = build_last_paper_run_panel_display_context()
    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["section_visible"] is False
    assert ctx["gate_enabled"] is False
    assert ctx["display_status"] == "disabled"
    assert ctx["readmodel"] is None
    assert ctx["error"] is None


def test_display_context_invalid_enabled_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "0")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(FIXTURE_ROOT))
    ctx = build_last_paper_run_panel_display_context()
    assert ctx["gate_enabled"] is False
    assert ctx["display_status"] == "disabled"
    assert ctx["readmodel"] is None


def test_display_context_unconfigured_fail_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    ctx = build_last_paper_run_panel_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["section_visible"] is False
    assert ctx["display_status"] == "unconfigured"
    assert ctx["readmodel"] is None
    assert ctx["error"] is None


def test_display_context_invalid_bundle_root_fail_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, "/nonexistent/peak_trade_last_paper_run_bundle_root")
    ctx = build_last_paper_run_panel_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["section_visible"] is False
    assert ctx["display_status"] == "unconfigured"
    assert ctx["readmodel"] is None


def test_display_context_ready_from_canonical_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    model = build_last_paper_run_panel_readmodel_v0(FIXTURE_ROOT)

    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["gate_enabled"] is True
    assert ctx["section_visible"] is True
    assert ctx["display_status"] == "ready"
    assert ctx["error"] is None
    assert isinstance(ctx["readmodel"], dict)
    assert ctx["readmodel"]["schema_version"] == SCHEMA_VERSION
    assert ctx["readmodel"]["readmodel_id"] == READMODEL_ID
    assert ctx["readmodel"]["non_authorizing"] is True
    assert ctx["readmodel"]["last_run"]["run_id"] == model.last_run.run_id
    assert ctx["readmodel"]["instrument"]["instrument_truth_status"] == "NOT_PERSISTED"


def test_display_context_malformed_bundle_fail_soft(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty_bundle = tmp_path / "empty_bundle"
    empty_bundle.mkdir()
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(empty_bundle))
    ctx = build_last_paper_run_panel_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["section_visible"] is True
    assert ctx["display_status"] == "error"
    assert ctx["error"] == "ValueError"
    assert ctx["readmodel"] is None


def test_display_context_is_deterministic_for_identical_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _ready_context_from_fixture(monkeypatch)
    second = build_last_paper_run_panel_display_context()
    assert first == second
    assert json.loads(json.dumps(first)) == first


def test_display_context_does_not_mutate_fixture_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = {path: path.read_bytes() for path in FIXTURE_ROOT.rglob("*") if path.is_file()}
    _ready_context_from_fixture(monkeypatch)
    after = {path: path.read_bytes() for path in FIXTURE_ROOT.rglob("*") if path.is_file()}
    assert before == after


def test_futures_operator_consumer_wires_runtime_builder() -> None:
    source = (PROJECT_ROOT / "src" / "webui" / "market_surface.py").read_text(encoding="utf-8")
    assert "build_last_paper_run_panel_display_context" in source
    assert "last_paper_run_panel" in source
    assert "market_single_page_consolidation" in source


def test_ready_readmodel_has_no_bitcoin_or_spot_symbols(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    instrument = ctx["readmodel"]["instrument"]
    assert instrument["selected_symbol"] is None
    assert instrument["selected_future"] is None
    assert instrument["selected_instrument"] is None
    for field in ("selected_symbol", "selected_future", "selected_instrument"):
        value = instrument[field]
        if isinstance(value, str):
            upper = value.upper()
            for token in _BITCOIN_TOKENS:
                assert token not in upper
            assert "/" not in value


def test_runtime_outputs_have_no_forbidden_execution_authority_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    collected: set[str] = set()
    _collect_object_keys(ctx, collected)
    assert collected.isdisjoint(_FORBIDDEN_JSON_KEYS)


def test_runtime_module_source_has_no_network_or_exchange_tokens() -> None:
    source = (PROJECT_ROOT / "src" / "webui" / "last_paper_run_panel_runtime_v0.py").read_text(
        encoding="utf-8"
    )
    forbidden_tokens = ("ccxt", "kraken", "requests", "httpx", "aiohttp", "urllib")
    lowered = source.lower()
    for token in forbidden_tokens:
        assert token not in lowered


def test_disabled_context_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    first = build_last_paper_run_panel_display_context()
    second = build_last_paper_run_panel_display_context()
    assert first == second


def test_unconfigured_context_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    first = build_last_paper_run_panel_display_context()
    second = deepcopy(first)
    assert build_last_paper_run_panel_display_context() == second
