"""Dedicated contract tests for canonical market ranking funnel runtime v0."""

from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.webui.market_instrument_eligibility_v0 import is_eligible_market_dashboard_instrument
from src.webui.market_ranking_funnel_readmodel_v0 import build_market_ranking_funnel_readmodel
from src.webui.market_ranking_funnel_readmodel_v0.builder import READMODEL_ID
from src.webui.market_ranking_funnel_runtime_v0 import (
    ENV_BUNDLE_ROOT,
    ENV_ENABLED,
    STAGE_DISPLAY_LABELS,
    build_market_ranking_funnel_display_context,
    enabled_explicitly_on,
    resolved_bundle_root_or_none,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = (
    PROJECT_ROOT / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "complete_minimal"
)
TOP50_FIXTURE_ROOT = (
    PROJECT_ROOT / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "top50_minimal"
)
CANONICAL_STAGE_ORDER = ("universe", "shortlist", "selected")

_EXPECTED_DISPLAY_CONTEXT_KEYS = frozenset(
    {
        "gate_enabled",
        "display_status",
        "readmodel_id",
        "has_rows",
        "non_authorizing",
        "stale",
        "stale_reason",
        "source",
        "generated_at_iso",
        "summary_line",
        "stage_counts",
        "stages",
        "stage_labels",
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
    return build_market_ranking_funnel_display_context()


def test_public_runtime_entrypoints_are_canonical() -> None:
    assert ENV_ENABLED == "PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED"
    assert ENV_BUNDLE_ROOT == "PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT"
    assert list(STAGE_DISPLAY_LABELS.keys()) == list(CANONICAL_STAGE_ORDER)
    for fn in (
        enabled_explicitly_on,
        resolved_bundle_root_or_none,
        build_market_ranking_funnel_display_context,
    ):
        assert inspect.isfunction(fn)


def test_enabled_explicitly_on_fail_closed_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    assert enabled_explicitly_on() is False
    monkeypatch.setenv(ENV_ENABLED, "0")
    assert enabled_explicitly_on() is False
    monkeypatch.setenv(ENV_ENABLED, "1")
    assert enabled_explicitly_on() is True


def test_resolved_bundle_root_or_none_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    assert resolved_bundle_root_or_none() is None
    monkeypatch.setenv(ENV_BUNDLE_ROOT, "")
    assert resolved_bundle_root_or_none() is None
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(FIXTURE_ROOT))
    assert resolved_bundle_root_or_none() == FIXTURE_ROOT.resolve()


def test_display_context_disabled_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    ctx = build_market_ranking_funnel_display_context()
    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["gate_enabled"] is False
    assert ctx["display_status"] == "disabled"
    assert ctx["stale_reason"] == "source_disabled"
    assert ctx["has_rows"] is False
    assert ctx["stage_counts"] == {"universe": 0, "shortlist": 0, "selected": 0}
    assert ctx["stages"] == {"universe": [], "shortlist": [], "selected": []}
    assert ctx["non_authorizing"] is True


def test_display_context_unconfigured_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    ctx = build_market_ranking_funnel_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "unconfigured"
    assert ctx["stale_reason"] == "bundle_root_unconfigured"
    assert ctx["has_rows"] is False


def test_display_context_missing_funnel_payload_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(tmp_path))
    ctx = build_market_ranking_funnel_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "builder_error"
    assert ctx["stale_reason"] == "bundle_build_failed"
    assert ctx["has_rows"] is False


def test_display_context_malformed_payload_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.loads((FIXTURE_ROOT / "ranking_funnel.json").read_text(encoding="utf-8"))
    payload["readmodel_id"] = "wrong.v0"
    (tmp_path / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(tmp_path))
    ctx = build_market_ranking_funnel_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "builder_error"
    assert ctx["stale_reason"] == "bundle_build_failed"
    assert ctx["has_rows"] is False


def test_display_context_ready_from_canonical_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    readmodel = build_market_ranking_funnel_readmodel(FIXTURE_ROOT)

    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "ready"
    assert ctx["readmodel_id"] == READMODEL_ID
    assert ctx["has_rows"] is True
    assert ctx["non_authorizing"] is True
    assert ctx["stale"] is False
    assert ctx["source"] == readmodel["source"]
    assert ctx["generated_at_iso"] == readmodel["generated_at_iso"]
    assert ctx["stage_counts"] == readmodel["stage_counts"]
    assert ctx["stages"] == readmodel["stages"]
    assert ctx["stage_labels"] == dict(STAGE_DISPLAY_LABELS)


def test_display_context_empty_stage_lists_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.loads((FIXTURE_ROOT / "ranking_funnel.json").read_text(encoding="utf-8"))
    payload["stages"] = {stage: [] for stage in CANONICAL_STAGE_ORDER}
    (tmp_path / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(tmp_path))
    ctx = build_market_ranking_funnel_display_context()
    assert ctx["display_status"] == "empty"
    assert ctx["has_rows"] is False
    assert ctx["stage_counts"] == {"universe": 0, "shortlist": 0, "selected": 0}
    assert all(ctx["stages"][stage] == [] for stage in CANONICAL_STAGE_ORDER)


def test_stage_ordering_and_counts_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    assert list(ctx["stages"].keys()) == list(CANONICAL_STAGE_ORDER)
    assert list(ctx["stage_counts"].keys()) == list(CANONICAL_STAGE_ORDER)
    for stage in CANONICAL_STAGE_ORDER:
        assert ctx["stage_counts"][stage] == len(ctx["stages"][stage])
    assert ctx["stage_counts"] == {"universe": 8, "shortlist": 8, "selected": 8}


def test_unknown_stage_keys_are_not_exposed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.loads((FIXTURE_ROOT / "ranking_funnel.json").read_text(encoding="utf-8"))
    payload["stages"]["unknown_stage"] = [
        {"row_id": "x-1", "symbol": "ETHUSDT", "rank": 1, "display_score": 0.5}
    ]
    (tmp_path / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(tmp_path))
    ctx = build_market_ranking_funnel_display_context()
    assert set(ctx["stages"].keys()) == set(CANONICAL_STAGE_ORDER)
    assert "unknown_stage" not in ctx["stages"]


def test_top50_fixture_stage_resolution_preserves_selected_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(TOP50_FIXTURE_ROOT))
    ctx = build_market_ranking_funnel_display_context()
    assert ctx["display_status"] == "ready"
    assert ctx["stage_counts"]["selected"] == 5
    assert ctx["stage_counts"]["universe"] == 0
    assert ctx["stage_counts"]["shortlist"] == 0
    symbols = [row["symbol"] for row in ctx["stages"]["selected"]]
    assert symbols == ["ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT"]


def test_display_context_is_deterministic_for_identical_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _ready_context_from_fixture(monkeypatch)
    second = build_market_ranking_funnel_display_context()
    assert first == second
    assert json.loads(json.dumps(first)) == first


def test_display_context_does_not_mutate_fixture_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = (FIXTURE_ROOT / "ranking_funnel.json").read_text(encoding="utf-8")
    _ready_context_from_fixture(monkeypatch)
    after = (FIXTURE_ROOT / "ranking_funnel.json").read_text(encoding="utf-8")
    assert before == after


def test_futures_only_non_bitcoin_symbols_in_ready_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    symbols: list[str] = []
    for stage in CANONICAL_STAGE_ORDER:
        for row in ctx["stages"][stage]:
            symbols.append(str(row["symbol"]))
    assert symbols
    for symbol in symbols:
        assert "/" not in symbol
        assert is_eligible_market_dashboard_instrument(symbol)
        upper = symbol.upper()
        for token in _BITCOIN_TOKENS:
            assert token not in upper


def test_display_context_non_authorizing_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    assert ctx["non_authorizing"] is True


def test_runtime_outputs_have_no_forbidden_execution_authority_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    collected: set[str] = set()
    _collect_object_keys(ctx, collected)
    assert collected.isdisjoint(_FORBIDDEN_JSON_KEYS)


def test_runtime_module_source_has_no_network_or_exchange_tokens() -> None:
    source = (PROJECT_ROOT / "src" / "webui" / "market_ranking_funnel_runtime_v0.py").read_text(
        encoding="utf-8"
    )
    forbidden_tokens = ("ccxt", "kraken", "requests", "httpx", "aiohttp", "urllib")
    lowered = source.lower()
    for token in forbidden_tokens:
        assert token not in lowered


def test_base_context_structure_on_fail_closed_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    disabled = build_market_ranking_funnel_display_context()
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    unconfigured = build_market_ranking_funnel_display_context()
    for ctx in (disabled, unconfigured):
        assert ctx["stage_labels"] == dict(STAGE_DISPLAY_LABELS)
        assert deepcopy(ctx["stages"]) == ctx["stages"]
