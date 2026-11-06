"""Unit tests for ``build_system_state_observation``."""

from __future__ import annotations

from src.ops.system_state_observation import (
    READER_SCHEMA_VERSION,
    build_system_state_observation,
)


def test_system_state_observation_missing_returns_unknown() -> None:
    out = build_system_state_observation(
        system_state=None,  # type: ignore[arg-type]
        policy_state={},
    )
    assert out["status"] == "unknown"
    assert out["observation_reason"] == "missing_system_state_dict"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION


def test_system_state_observation_degraded_unavailable() -> None:
    out = build_system_state_observation(
        system_state={
            "mode": "x",
            "execution_model": "y",
            "config_load_status": "unavailable",
            "environment": "unknown",
            "bounded_pilot_mode": None,
            "gating_posture_observation": "blocked",
        },
        policy_state={"summary": "blocked"},
    )
    assert out["status"] == "degraded"
    assert out["observation_reason"] == "config_load_unavailable"


def test_system_state_observation_caution_not_loaded() -> None:
    out = build_system_state_observation(
        system_state={
            "mode": "truth_first_ops_cockpit_v3",
            "execution_model": "guarded_execution",
            "config_load_status": "not_loaded",
            "environment": "unknown",
            "bounded_pilot_mode": None,
            "gating_posture_observation": "blocked",
        },
        policy_state={"summary": "blocked"},
    )
    assert out["status"] == "caution"
    assert out["observation_reason"] == "config_not_loaded"


def test_system_state_observation_caution_unknown_environment() -> None:
    out = build_system_state_observation(
        system_state={
            "mode": "truth_first_ops_cockpit_v3",
            "execution_model": "guarded_execution",
            "config_load_status": "loaded",
            "environment": "unknown",
            "bounded_pilot_mode": False,
            "gating_posture_observation": "armed",
        },
        policy_state={"summary": "armed"},
    )
    assert out["status"] == "caution"
    assert out["observation_reason"] == "environment_unknown"


def test_system_state_observation_nominal_loaded() -> None:
    out = build_system_state_observation(
        system_state={
            "mode": "truth_first_ops_cockpit_v3",
            "execution_model": "guarded_execution",
            "config_load_status": "loaded",
            "environment": "paper",
            "bounded_pilot_mode": True,
            "gating_posture_observation": "armed",
        },
        policy_state={"summary": "armed"},
    )
    assert out["status"] == "nominal"
    assert "not broker truth" in out["summary"].lower()
    assert any("bounded_pilot_mode" in n for n in out["consistency_notes"])


def test_system_state_observation_gating_mismatch() -> None:
    out = build_system_state_observation(
        system_state={
            "mode": "truth_first_ops_cockpit_v3",
            "execution_model": "guarded_execution",
            "config_load_status": "loaded",
            "environment": "paper",
            "bounded_pilot_mode": False,
            "gating_posture_observation": "armed",
        },
        policy_state={"summary": "blocked"},
    )
    assert out["status"] == "caution"
    assert out["observation_reason"] == "gating_mirror_mismatch"


def test_system_state_observation_unexpected_config_status() -> None:
    out = build_system_state_observation(
        system_state={
            "mode": "m",
            "execution_model": "e",
            "config_load_status": "custom",
            "environment": "paper",
            "bounded_pilot_mode": False,
            "gating_posture_observation": "armed",
        },
        policy_state={"summary": "armed"},
    )
    assert out["status"] == "caution"
    assert out["observation_reason"] == "unexpected_config_load_status"
