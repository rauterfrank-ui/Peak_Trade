"""Ten disabled parent slots. Optimization is the only provisional binding."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.ops.guardian_parent_slot_loader_v1.load_v1 import load_parent_slots_v1


def test_registry_loads_ten_disabled_slots() -> None:
    result = load_parent_slots_v1()

    assert result["status"] == "ACCEPTED"
    assert result["parent_count"] == 10
    assert result["activation"] == "DISABLED"
    assert result["authority"] == "NONE"
    assert result["guardian_ratified"] is False
    assert result["gcc_role"] == "COORDINATION_ONLY"
    assert result["runtime_connection"] is False
    assert {slot["parent_id"] for slot in result["slots"]} == {
        "PARENT_MASTER_V2",
        "PARENT_EXECUTION",
        "PARENT_SELF_LEARNING",
        "PARENT_OPTIMIZATION",
        "PARENT_MARKET_INTELLIGENCE",
        "PARENT_SELECTION",
        "PARENT_MARKET_OBSERVATION",
        "PARENT_CAPITAL",
        "PARENT_SAFETY",
        "PARENT_ORCHESTRATION",
    }
    optimization = next(
        slot for slot in result["slots"] if slot["parent_id"] == "PARENT_OPTIMIZATION"
    )
    assert optimization["membership_ratified"] is False
    assert optimization["calibration_status"] == "PROVISIONAL_BOUND"
    assert len(optimization["scope"]["domain_functional_members"]) == 4
    for slot in result["slots"]:
        assert slot["activation"] == "DISABLED"
        assert slot["authority"] == "NONE"
        assert slot["guardian_ratified"] is False
        assert slot["ghv_id"] == f"{slot['parent_id']}_GHV"
        assert slot["causal_graph_id"] == f"{slot['parent_id']}_CURRENT_CAUSAL_GRAPH"
        assert slot["ghosv_id"] == f"{slot['parent_id']}_GHOSV"
        if slot["parent_id"] != "PARENT_OPTIMIZATION":
            assert slot["calibration_status"] == "UNCALIBRATED"
            assert all(slot["scope"][field] == [] for field in slot["scope"])


def test_active_slot_is_rejected(tmp_path: Path) -> None:
    loaded = load_parent_slots_v1()
    loaded_slots = loaded["slots"]
    loaded_slots[0]["activation"] = "ACTIVE"
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(
            {
                "gcc": {"role": "COORDINATION_ONLY", "guardian": False},
                "slots": loaded_slots,
            }
        ),
        encoding="utf-8",
    )

    result = load_parent_slots_v1(path)

    assert result["status"] == "REJECTED"
    assert result["slots"] == []
    assert "activation:PARENT_MASTER_V2" in result["reasons"]


def _rejected_registry(tmp_path: Path, parent_index: int, **changes: object) -> dict[str, object]:
    loaded = load_parent_slots_v1()
    slots = loaded["slots"]
    slots[parent_index] = {**slots[parent_index], **changes}
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps({"gcc": {"role": "COORDINATION_ONLY", "guardian": False}, "slots": slots}),
        encoding="utf-8",
    )
    return load_parent_slots_v1(path)


def test_foreign_authority_is_rejected(tmp_path: Path) -> None:
    result = _rejected_registry(tmp_path, 1, authority="EXECUTE")

    assert result["status"] == "REJECTED"
    assert result["slots"] == []
    assert "authority:PARENT_EXECUTION" in result["reasons"]


def test_ratification_is_rejected(tmp_path: Path) -> None:
    result = _rejected_registry(tmp_path, 2, guardian_ratified=True)

    assert result["status"] == "REJECTED"
    assert "ratified:PARENT_SELF_LEARNING" in result["reasons"]


def test_non_optimization_membership_is_rejected(tmp_path: Path) -> None:
    result = _rejected_registry(tmp_path, 4, membership_ratified=True)

    assert result["status"] == "REJECTED"
    assert "membership:PARENT_MARKET_INTELLIGENCE" in result["reasons"]
