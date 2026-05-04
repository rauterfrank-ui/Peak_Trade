# tests/trading/master_v2/test_minimal_raw_input_optional_layers_v1.py
"""Wire-shape anchor for OPTIONAL_LAYERS_MISSING minimal adapter raw input.

Separate concern from canonical full happy-wire (`test_happy_raw_input_v1.py`).
"""

from __future__ import annotations

from typing import Any

from trading.master_v2.input_adapter_v1 import (
    adapt_inputs_to_master_v2_flow_v1,
    iter_unexpected_top_level_keys,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    get_master_v2_scenario_case_v1,
)

_EXPECTED_TOP_LEVEL_KEYS = frozenset({"correlation_id", "staged"})
_EXPECTED_STAGED_KEYS = frozenset(
    {
        "current_stage",
        "requested_stage",
        "safety_decision_allowed",
        "live_authority_acknowledged",
    }
)


def _build_minimal_optional_layers_raw_v1() -> tuple[dict[str, Any], object]:
    """Return `(raw_mapping, scenario_packet)` for OPTIONAL_LAYERS_MISSING minimal wire."""
    c = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    p = c.packet
    raw: dict[str, Any] = {
        "correlation_id": p.correlation_id,
        "staged": {
            "current_stage": p.staged.current_stage.value,
            "requested_stage": p.staged.requested_stage.value,
            "safety_decision_allowed": p.staged.safety_decision_allowed,
            "live_authority_acknowledged": p.staged.live_authority_acknowledged,
        },
    }
    return raw, p


def test_optional_layers_missing_minimal_raw_top_level_wire_shape_v1() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    assert isinstance(raw, dict)
    assert frozenset(raw.keys()) == _EXPECTED_TOP_LEVEL_KEYS


def test_optional_layers_missing_minimal_raw_has_no_unexpected_adapter_keys_v1() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    assert iter_unexpected_top_level_keys(raw) == frozenset()


def test_optional_layers_missing_minimal_raw_staged_section_contract_v1() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    staged = raw["staged"]
    assert isinstance(staged, dict)
    assert frozenset(staged.keys()) == _EXPECTED_STAGED_KEYS
    assert isinstance(staged["current_stage"], str)
    assert isinstance(staged["requested_stage"], str)
    assert staged["current_stage"].strip()
    assert staged["requested_stage"].strip()
    assert isinstance(staged["safety_decision_allowed"], bool)
    assert isinstance(staged["live_authority_acknowledged"], bool)


def test_optional_layers_missing_minimal_raw_adapter_smoke_v1() -> None:
    """Offline smoke: adapter maps minimal wire back to scenario packet."""

    raw, p = _build_minimal_optional_layers_raw_v1()
    r = adapt_inputs_to_master_v2_flow_v1(raw)
    assert r.ok is True
    assert r.rejection_reason is None
    assert r.packet == p
