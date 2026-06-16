"""
HTTP contract for GET /api/ops-cockpit: minimal stable JSON top-level shape.

Aligns with ``EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS`` from the payload
contract test (same invariant as ``build_ops_cockpit_payload``, via HTTP).
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from tests.ops.test_ops_cockpit_payload_top_level_contract import (
    EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS,
)


@pytest.fixture
def ops_client() -> TestClient:
    from src.webui.app import app

    return TestClient(app)


def test_api_ops_cockpit_json_contract_top_level_keys(ops_client: TestClient) -> None:
    """GET /api/ops-cockpit: 200, JSON object, stable top-level key set (no value assertions)."""
    response = ops_client.get("/api/ops-cockpit")
    assert response.status_code == 200
    assert "application/json" in (response.headers.get("content-type") or "")
    data = response.json()
    assert isinstance(data, dict)
    assert set(data.keys()) == EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS


def test_api_ops_cockpit_json_contract_nested_safety_state(ops_client: TestClient) -> None:
    """GET /api/ops-cockpit: safety_state nested JSON types, child keys, non-authority wording."""
    response = ops_client.get("/api/ops-cockpit")
    assert response.status_code == 200
    data = response.json()

    sstate = data["safety_state"]
    assert isinstance(sstate, dict)
    assert isinstance(sstate["summary"], str)
    assert isinstance(sstate["data_source"], str)
    assert sstate["reader_schema_version"].startswith("safety_state/")
    assert "not approval" in sstate["summary"].lower() or "not unlock" in sstate["summary"].lower()

    posture = sstate["posture_observation"]
    assert isinstance(posture, dict)
    assert isinstance(posture["status"], str)
    assert posture["reader_schema_version"].startswith("safety_posture_observation/")

    inc_safe = sstate["incident_safety_observation"]
    assert isinstance(inc_safe, dict)
    assert isinstance(inc_safe["status"], str)
    assert inc_safe["status"] in ("nominal", "caution", "degraded", "unknown")

    subset = sstate["incident_signal_subset"]
    assert isinstance(subset, dict)
    assert isinstance(subset["status"], str)
    assert isinstance(subset["summary"], str)
    assert isinstance(subset["blocked"], bool)
    assert isinstance(subset["kill_switch_active"], bool)
    assert isinstance(subset["degraded"], bool)
    assert isinstance(subset["requires_operator_attention"], bool)

    spo = data["safety_posture_observation"]
    assert isinstance(spo, dict)
    assert isinstance(spo["status"], str)
    assert spo["data_source"] == "cockpit_payload_aggregate"
    assert spo["reader_schema_version"].startswith("safety_posture_observation/")
    assert spo["status"] in ("nominal", "caution", "degraded", "blocking", "unknown")
    assert (
        "not an approval" in spo["summary"].lower()
        or "cockpit observation" in spo["summary"].lower()
    )


def test_api_ops_cockpit_json_contract_nested_human_supervision_state(
    ops_client: TestClient,
) -> None:
    """GET /api/ops-cockpit: human_supervision_state nested JSON contract (supervision invariants)."""
    response = ops_client.get("/api/ops-cockpit")
    assert response.status_code == 200
    data = response.json()

    sup = data["human_supervision_state"]
    assert isinstance(sup, dict)
    assert isinstance(sup["status"], str)
    assert isinstance(sup["mode"], str)
    assert isinstance(sup["summary"], str)
    assert sup["status"] == "operator_supervised"
    assert sup["mode"] == "intended"
    assert "operator supervision" in sup["summary"].lower()


def test_api_ops_cockpit_json_contract_nested_operator_state(ops_client: TestClient) -> None:
    """GET /api/ops-cockpit: operator_state nested JSON types and non-authorizing scalars."""
    response = ops_client.get("/api/ops-cockpit")
    assert response.status_code == 200
    data = response.json()

    op = data["operator_state"]
    assert isinstance(op, dict)
    for key in ("disabled", "enabled", "armed", "dry_run", "blocked", "kill_switch_active"):
        assert isinstance(op[key], bool)
    assert op["armed"] is False
    assert op["enabled"] is False


def test_api_ops_cockpit_json_contract_nested_run_state(ops_client: TestClient) -> None:
    """GET /api/ops-cockpit: run_state nested JSON types and runtime posture enums."""
    response = ops_client.get("/api/ops-cockpit")
    assert response.status_code == 200
    data = response.json()

    rs = data["run_state"]
    assert isinstance(rs, dict)
    assert isinstance(rs["status"], str)
    assert isinstance(rs["active"], bool)
    assert isinstance(rs["last_run_status"], str)
    assert isinstance(rs["session_active"], bool)
    assert isinstance(rs["generated_at"], str)
    assert isinstance(rs["freshness_status"], str)
    assert rs["status"] in ("idle", "active")
    assert rs["last_run_status"] in ("unknown", "completed", "failed", "aborted")
    assert rs["freshness_status"] == data["freshness_status"]
    assert rs["generated_at"] == data["truth_state"]["last_verified_utc"]


def test_api_ops_cockpit_json_contract_nested_session_end_mismatch_state(
    ops_client: TestClient,
) -> None:
    """GET /api/ops-cockpit: session_end_mismatch_state nested blocker and schema contract."""
    response = ops_client.get("/api/ops-cockpit")
    assert response.status_code == 200
    data = response.json()

    sem = data["session_end_mismatch_state"]
    assert isinstance(sem, dict)
    assert isinstance(sem["status"], str)
    assert isinstance(sem["summary"], str)
    assert isinstance(sem["blocked_next_session"], bool)
    assert isinstance(sem["runbook"], str)
    assert isinstance(sem["data_source"], str)
    assert isinstance(sem["observation_reason"], str)
    assert sem["reader_schema_version"].startswith("session_end_mismatch_reader")
    assert sem["runbook"] == "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH"
    assert sem["status"] in (
        "unknown",
        "nominal",
        "mismatch_signal",
        "caution",
        "degraded",
        "aligned",
        "ambiguous",
    )


def test_api_ops_cockpit_json_contract_nested_transfer_ambiguity_state(
    ops_client: TestClient,
) -> None:
    """GET /api/ops-cockpit: transfer_ambiguity_state nested JSON contract and runbook ref."""
    response = ops_client.get("/api/ops-cockpit")
    assert response.status_code == 200
    data = response.json()

    ta = data["transfer_ambiguity_state"]
    assert isinstance(ta, dict)
    assert isinstance(ta["status"], str)
    assert isinstance(ta["summary"], str)
    assert isinstance(ta["data_source"], str)
    assert isinstance(ta["observation_reason"], str)
    assert isinstance(ta["runbook_ref"], str)
    assert ta["reader_schema_version"].startswith("transfer_ambiguity_reader")
    assert ta["runbook_ref"] == "RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY"
    assert ta["status"] in ("unknown", "nominal", "caution", "degraded", "ambiguous")
