"""Tests for the read-only Market Ranking Funnel readmodel v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.webui.market_ranking_funnel_readmodel_v0 import (
    MarketRankingFunnelReadmodelError,
    build_market_ranking_funnel_readmodel,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "market_ranking_funnel_readmodel_v0"
    / "complete_minimal"
)


def test_market_ranking_funnel_readmodel_builds_complete_minimal_fixture_v0() -> None:
    model = build_market_ranking_funnel_readmodel(FIXTURE_ROOT)

    assert model["readmodel_id"] == "market_ranking_funnel_readmodel.v0"
    assert model["generated_at_iso"] == "2026-05-27T00:00:00Z"
    assert model["source"] == "fixture:complete_minimal"
    assert model["stale"] is False
    assert model["stale_reason"] is None
    assert model["non_authorizing"] is True
    assert model["stage_counts"] == {
        "universe": 1,
        "shortlist": 1,
        "selected": 1,
    }
    assert model["stages"]["universe"][0] == {
        "row_id": "universe-1",
        "symbol": "BTCUSDT",
        "rank": 1,
        "display_score": 0.91,
        "notes": "fixture row",
    }


def test_market_ranking_funnel_readmodel_rejects_missing_payload_v0(tmp_path: Path) -> None:
    with pytest.raises(MarketRankingFunnelReadmodelError, match="missing ranking funnel payload"):
        build_market_ranking_funnel_readmodel(tmp_path)


def test_market_ranking_funnel_readmodel_rejects_wrong_readmodel_id_v0(tmp_path: Path) -> None:
    payload = json.loads((FIXTURE_ROOT / "ranking_funnel.json").read_text(encoding="utf-8"))
    payload["readmodel_id"] = "wrong.v0"
    (tmp_path / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MarketRankingFunnelReadmodelError, match="readmodel_id"):
        build_market_ranking_funnel_readmodel(tmp_path)


@pytest.mark.parametrize(
    "field",
    [
        "order_id",
        "side",
        "quantity",
        "leverage",
        "approval",
        "approved",
        "live_authorized",
        "strategy_activation",
    ],
)
def test_market_ranking_funnel_readmodel_rejects_authority_fields_v0(
    tmp_path: Path,
    field: str,
) -> None:
    payload = json.loads((FIXTURE_ROOT / "ranking_funnel.json").read_text(encoding="utf-8"))
    payload["stages"]["selected"][0][field] = "forbidden"
    (tmp_path / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MarketRankingFunnelReadmodelError, match="forbidden fields"):
        build_market_ranking_funnel_readmodel(tmp_path)


def test_market_ranking_funnel_readmodel_rejects_missing_required_stage_v0(
    tmp_path: Path,
) -> None:
    payload = json.loads((FIXTURE_ROOT / "ranking_funnel.json").read_text(encoding="utf-8"))
    del payload["stages"]["shortlist"]
    (tmp_path / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MarketRankingFunnelReadmodelError, match="stages.shortlist"):
        build_market_ranking_funnel_readmodel(tmp_path)


def test_market_ranking_funnel_readmodel_rejects_authorizing_payload_v0(
    tmp_path: Path,
) -> None:
    payload = json.loads((FIXTURE_ROOT / "ranking_funnel.json").read_text(encoding="utf-8"))
    payload["non_authorizing"] = False
    (tmp_path / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MarketRankingFunnelReadmodelError, match="non_authorizing"):
        build_market_ranking_funnel_readmodel(tmp_path)
