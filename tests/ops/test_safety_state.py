"""Tests for ``build_safety_state`` — defensive shapes only (no value snapshots)."""

from __future__ import annotations

from typing import Any, cast

from src.ops.safety_state import READER_SCHEMA_VERSION, build_safety_state


def test_build_safety_state_missing_inputs_returns_defensive_object() -> None:
    out = build_safety_state(
        safety_posture_observation=cast(Any, None),
        incident_state=cast(Any, None),
        incident_safety_observation=cast(Any, None),
    )
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION
    assert out["data_source"] == "cockpit_payload_aggregate"
    assert "provenance" in out
    assert out["provenance"].get("observation_reason") == "missing_required_projection_inputs"
