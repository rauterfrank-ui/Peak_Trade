"""In-memory contract for Stage1 trend sub-models (v0).

No filesystem, reports, subprocess, env, or network.

Prod definitions live in ``src.obs.stage1.models``.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.obs.stage1.models import Stage1TrendRange, Stage1TrendRollups, Stage1TrendSeries


def _model_dump_public(model: object) -> dict:
    dump = getattr(model, "model_dump", None)
    if callable(dump):
        return dump(mode="python")
    legacy = getattr(model, "dict", None)
    if callable(legacy):
        return legacy()
    raise AssertionError("expected BaseModel-like model_dump()/dict()")


def test_stage1_trend_range_minimal_defaults_contract_v0() -> None:
    r = Stage1TrendRange(days=7)
    assert r.days == 7
    assert r.start is None
    assert r.end is None


def test_stage1_trend_range_optional_bounds_contract_v0() -> None:
    r = Stage1TrendRange(days=14, start="2026-01-01", end="2026-01-14")
    assert r.days == 14
    assert r.start == "2026-01-01"
    assert r.end == "2026-01-14"


def test_stage1_trend_range_rejects_invalid_days_contract_v0() -> None:
    with pytest.raises(ValidationError):
        Stage1TrendRange(days=0)


def test_stage1_trend_range_model_fields_public_contract_v0() -> None:
    assert set(Stage1TrendRange.model_fields.keys()) == {"days", "start", "end"}


def test_stage1_trend_range_dump_shape_stable_contract_v0() -> None:
    r = Stage1TrendRange(days=3)
    assert _model_dump_public(r) == {"days": 3, "start": None, "end": None}


def test_stage1_trend_series_minimal_contract_v0() -> None:
    s = Stage1TrendSeries(
        date="2026-05-04",
        new_alerts=1,
        critical_alerts=0,
        parse_errors=0,
        operator_actions=2,
    )
    assert s.date == "2026-05-04"
    assert s.new_alerts == 1
    assert s.operator_actions == 2


def test_stage1_trend_series_rejects_negative_counts_contract_v0() -> None:
    with pytest.raises(ValidationError):
        Stage1TrendSeries(
            date="2026-05-04",
            new_alerts=-1,
            critical_alerts=0,
            parse_errors=0,
            operator_actions=0,
        )


def test_stage1_trend_series_model_fields_public_contract_v0() -> None:
    assert set(Stage1TrendSeries.model_fields.keys()) == {
        "date",
        "new_alerts",
        "critical_alerts",
        "parse_errors",
        "operator_actions",
    }


def test_stage1_trend_series_dump_shape_stable_contract_v0() -> None:
    s = Stage1TrendSeries(
        date="2026-05-01",
        new_alerts=0,
        critical_alerts=1,
        parse_errors=2,
        operator_actions=3,
    )
    assert _model_dump_public(s) == {
        "date": "2026-05-01",
        "new_alerts": 0,
        "critical_alerts": 1,
        "parse_errors": 2,
        "operator_actions": 3,
    }


def test_stage1_trend_rollups_go_and_default_reasons_contract_v0() -> None:
    u = Stage1TrendRollups(
        new_alerts_total=0,
        new_alerts_avg=0.0,
        critical_days=0,
        parse_error_days=0,
        operator_action_days=0,
        go_no_go="GO",
    )
    assert u.go_no_go == "GO"
    assert u.reasons == []


def test_stage1_trend_rollups_with_reasons_and_hold_contract_v0() -> None:
    u = Stage1TrendRollups(
        new_alerts_total=10,
        new_alerts_avg=2.5,
        critical_days=0,
        parse_error_days=1,
        operator_action_days=2,
        go_no_go="HOLD",
        reasons=["threshold"],
    )
    assert u.go_no_go == "HOLD"
    assert u.reasons == ["threshold"]


def test_stage1_trend_rollups_no_go_contract_v0() -> None:
    u = Stage1TrendRollups(
        new_alerts_total=3,
        new_alerts_avg=1.0,
        critical_days=2,
        parse_error_days=0,
        operator_action_days=0,
        go_no_go="NO_GO",
    )
    assert u.go_no_go == "NO_GO"


def test_stage1_trend_rollups_rejects_invalid_go_no_go_contract_v0() -> None:
    with pytest.raises(ValidationError):
        Stage1TrendRollups(
            new_alerts_total=0,
            new_alerts_avg=0.0,
            critical_days=0,
            parse_error_days=0,
            operator_action_days=0,
            go_no_go="MAYBE",  # type: ignore[arg-type]
        )


def test_stage1_trend_rollups_model_fields_public_contract_v0() -> None:
    assert set(Stage1TrendRollups.model_fields.keys()) == {
        "new_alerts_total",
        "new_alerts_avg",
        "critical_days",
        "parse_error_days",
        "operator_action_days",
        "go_no_go",
        "reasons",
    }


def test_stage1_trend_rollups_dump_shape_stable_contract_v0() -> None:
    u = Stage1TrendRollups(
        new_alerts_total=5,
        new_alerts_avg=1.25,
        critical_days=0,
        parse_error_days=0,
        operator_action_days=1,
        go_no_go="GO",
        reasons=[],
    )
    assert _model_dump_public(u) == {
        "new_alerts_total": 5,
        "new_alerts_avg": 1.25,
        "critical_days": 0,
        "parse_error_days": 0,
        "operator_action_days": 1,
        "go_no_go": "GO",
        "reasons": [],
    }


def test_stage1_trend_rollups_rejects_negative_float_avg_contract_v0() -> None:
    with pytest.raises(ValidationError):
        Stage1TrendRollups(
            new_alerts_total=0,
            new_alerts_avg=-0.1,
            critical_days=0,
            parse_error_days=0,
            operator_action_days=0,
            go_no_go="GO",
        )
