"""Offline read-only Market Ranking Funnel readmodel v0 builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

READMODEL_ID = "market_ranking_funnel_readmodel.v0"
STAGES = ("universe", "shortlist", "selected")
FORBIDDEN_ROW_FIELDS = {
    "order_id",
    "side",
    "quantity",
    "leverage",
    "approval",
    "approved",
    "live_authorized",
    "strategy_activation",
}


class MarketRankingFunnelReadmodelError(ValueError):
    """Raised when the ranking funnel readmodel payload is invalid."""


def _as_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MarketRankingFunnelReadmodelError(f"{field} must be an object")
    return value


def _as_bool(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise MarketRankingFunnelReadmodelError(f"{field} must be a boolean")
    return value


def _as_optional_string(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise MarketRankingFunnelReadmodelError(f"{field} must be a string or null")
    return value


def _as_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarketRankingFunnelReadmodelError(f"{field} must be a non-empty string")
    return value


def _as_int(value: Any, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise MarketRankingFunnelReadmodelError(f"{field} must be an integer")
    return value


def _normalize_row(row: Any, *, stage: str, index: int) -> dict[str, Any]:
    row_map = _as_mapping(row, field=f"stages.{stage}[{index}]")
    forbidden = sorted(FORBIDDEN_ROW_FIELDS.intersection(row_map))
    if forbidden:
        raise MarketRankingFunnelReadmodelError(
            f"stages.{stage}[{index}] contains forbidden fields: {', '.join(forbidden)}"
        )

    normalized: dict[str, Any] = {
        "row_id": _as_string(row_map.get("row_id"), field=f"stages.{stage}[{index}].row_id"),
        "symbol": _as_string(row_map.get("symbol"), field=f"stages.{stage}[{index}].symbol"),
        "rank": _as_int(row_map.get("rank"), field=f"stages.{stage}[{index}].rank"),
    }

    if "display_score" in row_map:
        score = row_map["display_score"]
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise MarketRankingFunnelReadmodelError(
                f"stages.{stage}[{index}].display_score must be numeric"
            )
        normalized["display_score"] = float(score)

    if "notes" in row_map:
        normalized["notes"] = _as_optional_string(
            row_map["notes"],
            field=f"stages.{stage}[{index}].notes",
        )

    return normalized


def _normalize_stage_rows(value: Any, *, stage: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise MarketRankingFunnelReadmodelError(f"stages.{stage} must be a list")
    return [_normalize_row(row, stage=stage, index=index) for index, row in enumerate(value)]


def build_market_ranking_funnel_readmodel(bundle_root: str | Path) -> dict[str, Any]:
    """Build a deterministic, read-only ranking funnel readmodel from an offline bundle."""
    root = Path(bundle_root)
    payload_path = root / "ranking_funnel.json"
    if not payload_path.is_file():
        raise MarketRankingFunnelReadmodelError(
            f"missing ranking funnel payload: {payload_path}"
        )

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MarketRankingFunnelReadmodelError(f"invalid JSON: {exc}") from exc

    payload_map = _as_mapping(payload, field="payload")
    readmodel_id = _as_string(payload_map.get("readmodel_id"), field="readmodel_id")
    if readmodel_id != READMODEL_ID:
        raise MarketRankingFunnelReadmodelError(
            f"readmodel_id must be {READMODEL_ID!r}"
        )

    non_authorizing = _as_bool(
        payload_map.get("non_authorizing"),
        field="non_authorizing",
    )
    if not non_authorizing:
        raise MarketRankingFunnelReadmodelError("non_authorizing must be true")

    stages = _as_mapping(payload_map.get("stages"), field="stages")
    normalized_stages = {
        stage: _normalize_stage_rows(stages.get(stage), stage=stage)
        for stage in STAGES
    }

    return {
        "readmodel_id": readmodel_id,
        "generated_at_iso": _as_string(
            payload_map.get("generated_at_iso"),
            field="generated_at_iso",
        ),
        "source": _as_string(payload_map.get("source"), field="source"),
        "stale": _as_bool(payload_map.get("stale"), field="stale"),
        "stale_reason": _as_optional_string(
            payload_map.get("stale_reason"),
            field="stale_reason",
        ),
        "non_authorizing": non_authorizing,
        "stages": normalized_stages,
        "stage_counts": {
            stage: len(rows)
            for stage, rows in normalized_stages.items()
        },
    }
