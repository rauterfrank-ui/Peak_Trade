"""In-memory contract for Alerts API response models (v0).

No TestClient, router/HTTP, filesystem, subprocess, env, or network.

Prod models live in ``src.webui.alerts_api``.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from src.webui.alerts_api import AlertListResponse, AlertStats, AlertSummary


def _model_dump_public(model: object) -> dict:
    dump = getattr(model, "model_dump", None)
    if callable(dump):
        return dump(mode="python")
    legacy = getattr(model, "dict", None)
    if callable(legacy):
        return legacy()
    raise AssertionError("expected BaseModel-like model_dump()/dict()")


def _minimal_alert_summary() -> AlertSummary:
    return AlertSummary(
        id="alert_contract_001",
        title="Contract title",
        body="Contract body text.",
        severity="INFO",
        category="SYSTEM",
        source="contract.source",
        timestamp="2026-05-04T12:00:00+00:00",
        timestamp_display="04.05.2026 12:00:00",
    )


def test_alert_stats_minimal_and_defaults_contract_v0() -> None:
    s = AlertStats(
        total=0,
        by_severity={},
        by_category={},
        sessions_with_alerts=0,
        hours=24,
    )
    assert s.total == 0
    assert s.by_severity == {}
    assert s.by_category == {}
    assert s.sessions_with_alerts == 0
    assert s.last_critical is None
    assert s.hours == 24


def test_alert_stats_last_critical_explicit_contract_v0() -> None:
    payload = {"id": "crit1", "title": "critical sample"}
    s = AlertStats(
        total=1,
        by_severity={"CRITICAL": 1},
        by_category={"SYSTEM": 1},
        sessions_with_alerts=1,
        hours=12,
        last_critical=payload,
    )
    assert s.last_critical == payload


def test_alert_stats_model_fields_public_contract_v0() -> None:
    assert set(AlertStats.model_fields.keys()) == {
        "total",
        "by_severity",
        "by_category",
        "sessions_with_alerts",
        "last_critical",
        "hours",
    }


def test_alert_stats_dump_shape_stable_contract_v0() -> None:
    s = AlertStats(
        total=3,
        by_severity={"WARN": 2, "INFO": 1},
        by_category={"RISK": 1, "SYSTEM": 2},
        sessions_with_alerts=2,
        hours=48,
    )
    assert _model_dump_public(s) == {
        "total": 3,
        "by_severity": {"WARN": 2, "INFO": 1},
        "by_category": {"RISK": 1, "SYSTEM": 2},
        "sessions_with_alerts": 2,
        "last_critical": None,
        "hours": 48,
    }


def test_alert_list_response_minimal_contract_v0() -> None:
    a = _minimal_alert_summary()
    r = AlertListResponse(
        alerts=[a],
        total=100,
        filtered=1,
        limit=50,
        filters={"hours": "24"},
    )
    assert len(r.alerts) == 1
    assert r.alerts[0].id == a.id
    assert r.total == 100
    assert r.filtered == 1
    assert r.limit == 50
    assert r.filters == {"hours": "24"}


def test_alert_list_response_empty_alerts_contract_v0() -> None:
    r = AlertListResponse(
        alerts=[],
        total=0,
        filtered=0,
        limit=100,
        filters={},
    )
    assert r.alerts == []
    assert r.total == 0


def test_alert_list_response_model_fields_public_contract_v0() -> None:
    assert set(AlertListResponse.model_fields.keys()) == {
        "alerts",
        "total",
        "filtered",
        "limit",
        "filters",
    }


def test_alert_list_response_dump_shape_stable_contract_v0() -> None:
    r = AlertListResponse(
        alerts=[_minimal_alert_summary()],
        total=10,
        filtered=1,
        limit=100,
        filters={"severity": ["INFO"], "hours": None},
    )
    assert _model_dump_public(r) == {
        "alerts": [
            {
                "id": "alert_contract_001",
                "title": "Contract title",
                "body": "Contract body text.",
                "severity": "INFO",
                "category": "SYSTEM",
                "source": "contract.source",
                "session_id": None,
                "timestamp": "2026-05-04T12:00:00+00:00",
                "timestamp_display": "04.05.2026 12:00:00",
                "runbooks": [],
            },
        ],
        "total": 10,
        "filtered": 1,
        "limit": 100,
        "filters": {"severity": ["INFO"], "hours": None},
    }
