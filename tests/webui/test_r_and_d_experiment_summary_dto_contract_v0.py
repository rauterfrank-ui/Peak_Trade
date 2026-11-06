"""In-memory contract for ``RnDExperimentSummary`` DTO (v0).

No TestClient, router/HTTP execution, filesystem, subprocess, env, or network.

Prod definition lives in ``src.webui.r_and_d_api``.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from src.webui.r_and_d_api import RnDExperimentSummary


def _model_dump_public(model: object) -> dict:
    """Stable dict shape; pydantic v2 primary with v1 ``dict()`` fallback."""
    dump = getattr(model, "model_dump", None)
    if callable(dump):
        return dump(mode="python")
    legacy = getattr(model, "dict", None)
    if callable(legacy):
        return legacy()
    raise AssertionError("expected BaseModel-like model_dump()/dict()")


def _minimal() -> RnDExperimentSummary:
    return RnDExperimentSummary(
        filename="exp_001.json",
        run_id="run_contract_001",
        timestamp="2026-05-03T12:00:00+00:00",
        tag="contract_tag",
        preset_id="preset_a",
        strategy="strategy_x",
        symbol="BTC/USD",
        timeframe="1h",
        total_return=0.25,
        sharpe=1.2,
        max_drawdown=-0.08,
        total_trades=42,
        win_rate=0.55,
        status="success",
    )


def test_rnd_experiment_summary_import_contract_v0() -> None:
    assert RnDExperimentSummary.__name__ == "RnDExperimentSummary"


def test_rnd_experiment_summary_required_fields_contract_v0() -> None:
    s = _minimal()
    assert s.filename == "exp_001.json"
    assert s.run_id == "run_contract_001"
    assert s.timestamp == "2026-05-03T12:00:00+00:00"
    assert s.tag == "contract_tag"
    assert s.preset_id == "preset_a"
    assert s.strategy == "strategy_x"
    assert s.symbol == "BTC/USD"
    assert s.timeframe == "1h"
    assert s.total_return == 0.25
    assert s.sharpe == 1.2
    assert s.max_drawdown == -0.08
    assert s.total_trades == 42
    assert s.win_rate == 0.55
    assert s.status == "success"


def test_rnd_experiment_summary_defaults_contract_v0() -> None:
    s = _minimal()
    assert s.use_dummy_data is False
    assert s.tier == "r_and_d"
    assert s.run_type == "backtest"
    assert s.experiment_category == ""
    assert s.date_str == ""


def test_rnd_experiment_summary_override_defaults_contract_v0() -> None:
    s = RnDExperimentSummary(
        filename="x.json",
        run_id="r",
        timestamp="2026-01-01T00:00:00Z",
        tag="",
        preset_id="p",
        strategy="s",
        symbol="SYM",
        timeframe="4h",
        total_return=0.0,
        sharpe=0.0,
        max_drawdown=0.0,
        total_trades=0,
        win_rate=0.0,
        status="running",
        use_dummy_data=True,
        tier="core",
        run_type="sweep",
        experiment_category="volatility",
        date_str="2026-05-03",
    )
    assert s.use_dummy_data is True
    assert s.tier == "core"
    assert s.run_type == "sweep"
    assert s.experiment_category == "volatility"
    assert s.date_str == "2026-05-03"


def test_rnd_experiment_summary_model_fields_public_contract_v0() -> None:
    assert set(RnDExperimentSummary.model_fields.keys()) == {
        "filename",
        "run_id",
        "timestamp",
        "tag",
        "preset_id",
        "strategy",
        "symbol",
        "timeframe",
        "total_return",
        "sharpe",
        "max_drawdown",
        "total_trades",
        "win_rate",
        "status",
        "use_dummy_data",
        "tier",
        "run_type",
        "experiment_category",
        "date_str",
    }


def test_rnd_experiment_summary_dump_shape_stable_contract_v0() -> None:
    s = _minimal()
    assert _model_dump_public(s) == {
        "filename": "exp_001.json",
        "run_id": "run_contract_001",
        "timestamp": "2026-05-03T12:00:00+00:00",
        "tag": "contract_tag",
        "preset_id": "preset_a",
        "strategy": "strategy_x",
        "symbol": "BTC/USD",
        "timeframe": "1h",
        "total_return": 0.25,
        "sharpe": 1.2,
        "max_drawdown": -0.08,
        "total_trades": 42,
        "win_rate": 0.55,
        "status": "success",
        "use_dummy_data": False,
        "tier": "r_and_d",
        "run_type": "backtest",
        "experiment_category": "",
        "date_str": "",
    }
