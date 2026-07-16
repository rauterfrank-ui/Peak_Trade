"""Contract tests: market visual operator surface v1 (read-only, non-authorizing).

All bundles are built in ``tmp_path`` from tiny real-shaped payloads. These are NOT
production display fixtures — they only exercise the read-only view models and SSR route.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.market_visual_operator_surface_v1 import (
    ENV_EVIDENCE_ROOT,
    ENV_LINEAR_DIAGNOSTICS_ROOT,
    build_market_visual_operator_surface_context,
)
from src.webui.market_visual_operator_surface_v1.contracts import ActivityState
from src.webui.market_visual_operator_surface_v1.decision_funnel_display_v1 import (
    FUNNEL_STAGES,
    build_decision_funnel_display_v1,
)
from src.webui.market_visual_operator_surface_v1.economic_observability_display_v1 import (
    build_economic_observability_display_v1,
)
from src.webui.market_visual_operator_surface_v1.ai_linear_diagnostics_display_v1 import (
    build_ai_linear_diagnostics_display_v1,
)
from src.webui.market_futures_ohlcv_runtime_v0 import (
    ENV_BUNDLE_ROOT as OHLCV_ENV_BUNDLE_ROOT,
    ENV_ENABLED as OHLCV_ENV_ENABLED,
    build_market_futures_ohlcv_display_context,
)
from src.webui.market_ranking_funnel_runtime_v0 import (
    ENV_BUNDLE_ROOT as RANKING_ENV_BUNDLE_ROOT,
    ENV_ENABLED as RANKING_ENV_ENABLED,
    build_market_ranking_funnel_display_context,
)
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT as F5_ENV_BUNDLE_ROOT,
    ENV_ENABLED as F5_ENV_ENABLED,
    build_futures_read_only_market_dashboard_display_context,
)
from src.webui.market_surface import build_market_governed_top20_display_context


def _bars(base: float, n: int) -> list[dict[str, object]]:
    bars: list[dict[str, object]] = []
    for i in range(n):
        close = base + i
        bars.append(
            {
                "ts": f"2024-05-25T{i:02d}:00:00Z",
                "open": close - 0.5,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1000.0 + i * 10.0,
            }
        )
    return bars


def _write_ohlcv_bundle(
    root: Path,
    *,
    symbols: dict[str, list[dict[str, object]]],
    stale: bool = False,
) -> Path:
    bundle = root / "futures_ohlcv"
    bundle.mkdir(parents=True, exist_ok=True)
    payload = {
        "readmodel_id": "market_futures_ohlcv_readmodel.v0",
        "generated_at_iso": "2026-07-16T00:00:00Z",
        "source": "test:tiny_real_shaped",
        "stale": stale,
        "stale_reason": "test_stale" if stale else None,
        "non_authorizing": True,
        "series": {sym: {"timeframe": "1h", "bars": bars} for sym, bars in symbols.items()},
    }
    (bundle / "futures_ohlcv.json").write_text(json.dumps(payload), encoding="utf-8")
    return bundle


def _write_ranking_bundle(root: Path, *, symbols: list[str]) -> Path:
    bundle = root / "ranking_funnel"
    bundle.mkdir(parents=True, exist_ok=True)
    rows = [
        {"row_id": f"r{i:03d}", "symbol": sym, "rank": i + 1, "display_score": 1.0 - i / 100.0}
        for i, sym in enumerate(symbols)
    ]
    payload = {
        "readmodel_id": "market_ranking_funnel_readmodel.v0",
        "generated_at_iso": "2026-07-16T00:00:00Z",
        "source": "test:tiny_real_shaped",
        "stale": False,
        "stale_reason": None,
        "non_authorizing": True,
        "stages": {"universe": rows, "shortlist": rows[:50], "selected": rows[:50]},
    }
    (bundle / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")
    return bundle


def _write_f5_bundle(root: Path) -> Path:
    bundle = root / "f5_dashboard"
    bundle.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "futures_read_only_market_dashboard.v0",
        "readmodel_id": "futures_read_only_market_dashboard_v0",
        "non_authorizing": True,
        "display_status": "ready",
        "overall_status": "futures_metadata_partial",
        "env_name": "okx_linear_perpetual_offline_panel",
        "f1": {"status": "futures_metadata_partial", "exchange": "okx", "symbol": "ETHUSDT"},
        "f2": {"status": "provenance_missing"},
        "f3": {"status": "backtest_realism_incomplete"},
        "f4": {"status": "risk_safety_incomplete"},
    }
    (bundle / "dashboard.json").write_text(json.dumps(payload), encoding="utf-8")
    return bundle


def _write_economic_evidence(
    root: Path,
    *,
    bar_count: int = 2953,
    trade_count: int = 0,
    include_funnel: bool = True,
) -> Path:
    evidence = root / "economic_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    if include_funnel:
        (evidence / "compact_decision_funnel.json").write_text(
            json.dumps(
                {
                    "bar_count": bar_count,
                    "trade_count": trade_count,
                    "zero_trade_degeneration": trade_count == 0,
                    "most_frequent_block_reasons": [],
                    "block_reason_counts": {},
                }
            ),
            encoding="utf-8",
        )
    (evidence / "baseline_metrics.json").write_text(
        json.dumps(
            {
                "gross_return": {"semantic": "COMPUTED", "value": 0.0},
                "net_return": {"semantic": "COMPUTED", "value": 0.0},
                "net_expectancy": {"semantic": "COMPUTED", "value": 0.0},
                "profit_factor": {"semantic": "COMPUTED", "value": 0.0},
                "max_drawdown": {"semantic": "COMPUTED", "value": 0.0},
                "trade_count": {"semantic": "COMPUTED", "value": 0.0},
            }
        ),
        encoding="utf-8",
    )
    (evidence / "cost_attribution.json").write_text(
        json.dumps(
            {
                "roundtrip_cost_bps": 40.0,
                "funding_drag": 0.0,
                "fee_drag": {"semantic": "NOT_COMPUTED", "reason_code": "not_bound"},
                "slippage_impact": {"semantic": "NOT_COMPUTED", "reason_code": "not_bound"},
            }
        ),
        encoding="utf-8",
    )
    (evidence / "economic_validity_evaluation_v1.json").write_text(
        json.dumps(
            {
                "evaluation_status": "FAIL",
                "gates_pass": False,
                "reason_codes": ["TRADE_COUNT_BELOW_THRESHOLD", "PROFIT_FACTOR_BELOW_THRESHOLD"],
            }
        ),
        encoding="utf-8",
    )
    return evidence


def _configure_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    ohlcv_root: Path | None = None,
    ranking_root: Path | None = None,
    f5_root: Path | None = None,
    evidence_root: Path | None = None,
    linear_root: Path | None = None,
) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    for env, value in (
        (OHLCV_ENV_ENABLED, ohlcv_root),
        (RANKING_ENV_ENABLED, ranking_root),
        (F5_ENV_ENABLED, f5_root),
    ):
        if value is not None:
            monkeypatch.setenv(env, "1")
        else:
            monkeypatch.delenv(env, raising=False)
    for env, value in (
        (OHLCV_ENV_BUNDLE_ROOT, ohlcv_root),
        (RANKING_ENV_BUNDLE_ROOT, ranking_root),
        (F5_ENV_BUNDLE_ROOT, f5_root),
        (ENV_EVIDENCE_ROOT, evidence_root),
        (ENV_LINEAR_DIAGNOSTICS_ROOT, linear_root),
    ):
        if value is not None:
            monkeypatch.setenv(env, str(value))
        else:
            monkeypatch.delenv(env, raising=False)


# --- decision funnel VM contracts -------------------------------------------------


def test_decision_funnel_missing_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_EVIDENCE_ROOT, raising=False)
    vm = build_decision_funnel_display_v1()
    assert vm["activity_state"] == ActivityState.NOT_AVAILABLE
    assert [s["stage_id"] for s in vm["stages"]] == list(FUNNEL_STAGES)
    assert all(s["count"] is None for s in vm["stages"])


def test_decision_funnel_stage_order_exact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence = _write_economic_evidence(tmp_path)
    _configure_env(monkeypatch, evidence_root=evidence)
    vm = build_decision_funnel_display_v1()
    assert [s["stage_id"] for s in vm["stages"]] == list(FUNNEL_STAGES)
    assert vm["activity_state"] == ActivityState.PROCESSED


def test_decision_funnel_no_invented_intermediate_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = _write_economic_evidence(tmp_path, bar_count=2953, trade_count=0)
    _configure_env(monkeypatch, evidence_root=evidence)
    vm = build_decision_funnel_display_v1()
    by_id = {s["stage_id"]: s for s in vm["stages"]}
    assert by_id["market_epochs"]["count"] == 2953
    assert by_id["trades_opened"]["count"] == 0
    # Intermediate stages have no evidence and must never be invented.
    for stage in FUNNEL_STAGES[1:-1]:
        assert by_id[stage]["count"] is None
        assert by_id[stage]["status"] == ActivityState.AVAILABLE_NOT_RUN


def test_decision_funnel_failed_on_parse_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = tmp_path / "bad_evidence"
    evidence.mkdir()
    (evidence / "compact_decision_funnel.json").write_text("{bad json", encoding="utf-8")
    _configure_env(monkeypatch, evidence_root=evidence)
    vm = build_decision_funnel_display_v1()
    assert vm["activity_state"] == ActivityState.FAILED


# --- AI activity state --------------------------------------------------------------


def test_ai_active_only_with_processing_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = _write_economic_evidence(tmp_path, bar_count=2953, trade_count=0)
    _configure_env(monkeypatch, evidence_root=evidence)
    ctx = build_market_visual_operator_surface_context(source="futures")
    assert ctx["ai_activity_state"] == ActivityState.ACTIVE


def test_ai_available_not_run_distinct_from_active(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Evidence root configured but no funnel artifact present.
    evidence = _write_economic_evidence(tmp_path, include_funnel=False)
    _configure_env(monkeypatch, evidence_root=evidence)
    ctx = build_market_visual_operator_surface_context(source="futures")
    assert ctx["ai_activity_state"] == ActivityState.AVAILABLE_NOT_RUN
    assert ctx["ai_activity_state"] != ActivityState.ACTIVE


def test_ai_not_available_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_EVIDENCE_ROOT, raising=False)
    ctx = build_market_visual_operator_surface_context(source="futures")
    assert ctx["ai_activity_state"] == ActivityState.NOT_AVAILABLE


# --- economic observability VM ------------------------------------------------------


def test_economic_fail_and_zero_trades_visible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = _write_economic_evidence(tmp_path)
    _configure_env(monkeypatch, evidence_root=evidence)
    vm = build_economic_observability_display_v1()
    assert vm["economic_status"] == "FAIL"
    assert vm["gates_pass"] is False
    assert vm["trade_count"]["value"] == 0.0
    assert vm["profit_factor"]["value"] == 0.0
    # NOT_COMPUTED preserved honestly.
    assert vm["fee_drag"]["semantic"] == "NOT_COMPUTED"
    assert vm["slippage_impact"]["semantic"] == "NOT_COMPUTED"
    # No invented equity/drawdown curve.
    assert vm["equity_series_status"] == "MISSING_SOURCE"
    assert vm["equity_series"] == []


def test_economic_missing_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_EVIDENCE_ROOT, raising=False)
    vm = build_economic_observability_display_v1()
    assert vm["activity_state"] == ActivityState.NOT_AVAILABLE
    assert vm["equity_series_status"] == "MISSING_SOURCE"


# --- linear diagnostics VM ----------------------------------------------------------


def test_linear_diagnostics_missing_source_names_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_LINEAR_DIAGNOSTICS_ROOT, raising=False)
    vm = build_ai_linear_diagnostics_display_v1()
    assert vm["bundle_status"] == "MISSING_SOURCE"
    assert ENV_LINEAR_DIAGNOSTICS_ROOT in vm["recovery_hint"]


def test_linear_diagnostics_reads_offline_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "linear"
    bundle.mkdir()
    (bundle / "factor_exposure_diagnostics.json").write_text(
        json.dumps(
            {
                "feature_names": ["f1", "f2"],
                "coefficients": [0.5, -0.25],
                "condition_number": 1234.5,
                "matrix_rank": 2,
                "rank_deficient": False,
                "dominant_factor_exposures": ["f1"],
            }
        ),
        encoding="utf-8",
    )
    _configure_env(monkeypatch, linear_root=bundle)
    vm = build_ai_linear_diagnostics_display_v1()
    assert vm["bundle_status"] == "loaded"
    assert vm["condition_number"] == 1234.5
    assert {c["feature"] for c in vm["coefficients"]} == {"f1", "f2"}


# --- operator header authority boundaries ------------------------------------------


def test_operator_header_no_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    evidence = _write_economic_evidence(tmp_path)
    _configure_env(monkeypatch, evidence_root=evidence)
    ctx = build_market_visual_operator_surface_context(source="futures")
    header = ctx["visual_operator_header"]
    assert header["runtime_authority"] == "NONE"
    assert header["orders_allowed"] is False
    assert header["live_allowed"] is False
    assert header["promotion_allowed"] is False
    assert header["futures_only"] is True
    assert header["spot_allowed"] is False
    assert header["synthetic_allowed"] is False


# --- governed top20/top50 + candles -------------------------------------------------


def test_top20_and_top50_data_driven_difference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    symbols = [f"SYM{i:03d}USDT" for i in range(55)]
    ohlcv_root = _write_ohlcv_bundle(
        tmp_path, symbols={"SYM000USDT": _bars(100.0, 5), "SYM001USDT": _bars(50.0, 5)}
    )
    ranking_root = _write_ranking_bundle(tmp_path, symbols=symbols)
    f5_root = _write_f5_bundle(tmp_path)
    _configure_env(monkeypatch, ohlcv_root=ohlcv_root, ranking_root=ranking_root, f5_root=f5_root)
    ranking = build_market_ranking_funnel_display_context()
    f5 = build_futures_read_only_market_dashboard_display_context()
    ohlcv = build_market_futures_ohlcv_display_context()
    top20 = build_market_governed_top20_display_context(
        ranking_funnel=ranking, f5_dashboard=f5, futures_ohlcv=ohlcv, timeframe="1h", top_n=20
    )
    top50 = build_market_governed_top20_display_context(
        ranking_funnel=ranking, f5_dashboard=f5, futures_ohlcv=ohlcv, timeframe="1h", top_n=50
    )
    assert top20["row_count"] == 20
    assert top50["row_count"] == 50
    assert top20["row_count"] != top50["row_count"]


def test_candles_from_canonical_ohlcv_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bars = _bars(100.0, 6)
    ohlcv_root = _write_ohlcv_bundle(tmp_path, symbols={"ETHUSDT": bars})
    ranking_root = _write_ranking_bundle(tmp_path, symbols=["ETHUSDT"])
    f5_root = _write_f5_bundle(tmp_path)
    _configure_env(monkeypatch, ohlcv_root=ohlcv_root, ranking_root=ranking_root, f5_root=f5_root)
    ohlcv = build_market_futures_ohlcv_display_context()
    ranking = build_market_ranking_funnel_display_context()
    f5 = build_futures_read_only_market_dashboard_display_context()
    top20 = build_market_governed_top20_display_context(
        ranking_funnel=ranking, f5_dashboard=f5, futures_ohlcv=ohlcv, timeframe="1h", top_n=20
    )
    row = top20["rows"][0]
    # Liquidity derived from the real last-bar volume (no invention).
    assert row["liquidity_sort"] == bars[-1]["volume"]
    assert row["momentum_display"] != "unavailable"


def test_empty_ohlcv_series_compact_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ohlcv_root = _write_ohlcv_bundle(tmp_path, symbols={})
    ranking_root = _write_ranking_bundle(tmp_path, symbols=["ETHUSDT"])
    f5_root = _write_f5_bundle(tmp_path)
    _configure_env(monkeypatch, ohlcv_root=ohlcv_root, ranking_root=ranking_root, f5_root=f5_root)
    ohlcv = build_market_futures_ohlcv_display_context()
    ranking = build_market_ranking_funnel_display_context()
    f5 = build_futures_read_only_market_dashboard_display_context()
    top20 = build_market_governed_top20_display_context(
        ranking_funnel=ranking, f5_dashboard=f5, futures_ohlcv=ohlcv, timeframe="1h", top_n=20
    )
    row = top20["rows"][0]
    assert row["momentum_display"] == "unavailable"
    assert row["liquidity_display"] == "unavailable"


def test_stale_ohlcv_yields_unavailable_visual_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ohlcv_root = _write_ohlcv_bundle(tmp_path, symbols={"ETHUSDT": _bars(100.0, 5)}, stale=True)
    ranking_root = _write_ranking_bundle(tmp_path, symbols=["ETHUSDT"])
    f5_root = _write_f5_bundle(tmp_path)
    _configure_env(monkeypatch, ohlcv_root=ohlcv_root, ranking_root=ranking_root, f5_root=f5_root)
    ohlcv = build_market_futures_ohlcv_display_context()
    ranking = build_market_ranking_funnel_display_context()
    f5 = build_futures_read_only_market_dashboard_display_context()
    top20 = build_market_governed_top20_display_context(
        ranking_funnel=ranking, f5_dashboard=f5, futures_ohlcv=ohlcv, timeframe="1h", top_n=20
    )
    assert top20["rows"][0]["momentum_display"] == "unavailable"


# --- SSR route ----------------------------------------------------------------------


@pytest.fixture()
def client_full(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    ohlcv_root = _write_ohlcv_bundle(
        tmp_path, symbols={"ETHUSDT": _bars(100.0, 8), "ADAUSDT": _bars(1.0, 8)}
    )
    ranking_root = _write_ranking_bundle(tmp_path, symbols=["ETHUSDT", "ADAUSDT"])
    f5_root = _write_f5_bundle(tmp_path)
    evidence = _write_economic_evidence(tmp_path)
    _configure_env(
        monkeypatch,
        ohlcv_root=ohlcv_root,
        ranking_root=ranking_root,
        f5_root=f5_root,
        evidence_root=evidence,
    )
    kraken_mock = MagicMock(side_effect=AssertionError("fetch_ohlcv_df must not run"))
    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", kraken_mock)
    with TestClient(create_app()) as test_client:
        yield test_client


def test_market_route_200_with_bundles(client_full: TestClient) -> None:
    resp = client_full.get("/market?timeframe=1h")
    assert resp.status_code == 200
    body = resp.text
    assert 'data-market-visual-operator-surface-v1="true"' in body
    assert 'data-market-visual-operator-header-v1="true"' in body
    assert 'data-market-decision-funnel-visual-v1="true"' in body
    assert 'data-market-economic-observability-visual-v1="true"' in body
    assert 'data-market-ai-linear-diagnostics-visual-v1="true"' in body


def test_market_route_authority_and_futures_only_markers(client_full: TestClient) -> None:
    body = client_full.get("/market?timeframe=1h").text
    assert 'data-market-visual-operator-runtime-authority="NONE"' in body
    assert 'data-market-visual-operator-orders-allowed="false"' in body
    assert 'data-market-visual-operator-live-allowed="false"' in body
    assert 'data-market-visual-operator-futures-only="true"' in body
    assert 'data-market-source="futures"' in body


def test_market_route_ai_active_and_economic_fail_visible(client_full: TestClient) -> None:
    body = client_full.get("/market?timeframe=1h").text
    assert f'data-market-ai-activity-state="{ActivityState.ACTIVE}"' in body
    assert 'data-market-economic-status="FAIL"' in body
    assert 'data-market-economic-equity-missing-source-v1="true"' in body


def test_market_route_current_state_still_present_in_governance_details(
    client_full: TestClient,
) -> None:
    body = client_full.get("/market?timeframe=1h").text
    # Existing current_state surface not broken — still rendered (now collapsed).
    assert 'data-market-system-governance-details-v1="true"' in body
    assert 'data-market-current-state-compact-v1="true"' in body


def test_market_route_no_bitcoin_no_spot_no_synthetic(client_full: TestClient) -> None:
    body = client_full.get("/market?timeframe=1h").text
    assert "BTCUSDT" not in body
    assert 'data-market-dummy-explicit-synthetic-v1="true"' not in body
