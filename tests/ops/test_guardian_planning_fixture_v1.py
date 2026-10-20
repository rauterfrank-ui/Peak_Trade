"""Fail-closed tests for the guardian planning fixture. No domain binding."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from scripts.ops.guardian_domain_scope_manifest_v1.constants_v1 import (
    TOOL_SLOT_NAMES,
    TOOL_SLOT_STATUSES,
)
from scripts.ops.guardian_domain_scope_manifest_v1.validate_v1 import (
    validate_guardian_domain_scope_manifest_v1,
)
from scripts.ops.guardian_planning_fixture_v1.constants_v1 import (
    PLANNING_SLOT_STATUS,
    STATUS_ACCEPTED,
    STATUS_CLAIMED_CURRENT_COVERAGE,
    STATUS_COORDINATOR_COUNT_CONFLICT,
    STATUS_DUPLICATE_IDENTIFIER,
    STATUS_ILLEGAL_SEAT_ASSIGNMENT,
    STATUS_IMPLICIT_GUARDIAN_RATIFICATION,
    STATUS_INVALID_FIXTURE,
    STATUS_MISSING_RESPONSIBILITY_AREA,
    STATUS_MISSING_UNASSIGNED_SURFACE,
    STATUS_PRODUCTIVE_AUTHORITY,
    STATUS_UNKNOWN_TOOL_SLOT,
)
from scripts.ops.guardian_planning_fixture_v1.validate_v1 import (
    canonical_planning_fixture_v1,
    validate_guardian_planning_fixture_v1,
)
from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import AUTHORITY, GUARDIAN_IDENTITY

_PACKAGE = Path(__file__).resolve().parents[2] / "scripts" / "ops" / "guardian_planning_fixture_v1"
_COMMIT = "89d8230fddfd2e5b8af2da46b080f1db204fd4e5"
_TREE = "e22edccfe30b5fd68b2a9a511ad21dc3e7449c0f"


def _fixture() -> dict[str, Any]:
    return canonical_planning_fixture_v1()


def _validate(fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    return validate_guardian_planning_fixture_v1(_fixture() if fixture is None else fixture)


def _assert_denials(result: dict[str, Any]) -> None:
    assert result["authority"] == "NONE"
    assert result["trading_authority"] == "NONE"
    assert result["safety_authority"] == "NONE"
    assert result["execution_authority"] == "NONE"
    assert result["runtime_authorization_effect"] == "NONE"
    assert result["guardian_ratification"] is False
    assert result["domain_binding"] is False
    assert result["productive_activation"] is False
    assert result["current_coverage"] is False
    assert result["wp_b0_bindable"] is False
    assert result["wp_b0_slot_status_compatible"] is False
    assert result["gcc_ratification"] is False
    assert "overall_pass" not in result
    assert "guardian_pass" not in result
    assert "universe_pass" not in result
    assert "live_authorized" not in result


def test_canonical_fixture_is_accepted() -> None:
    result = _validate()
    assert result["status"] == STATUS_ACCEPTED
    assert result["coordinator_count"] == 1
    assert result["coordinator_role"] == "FINDING_AGGREGATION_ONLY"
    assert result["architecture_status"] == "PLANNING_ONLY"
    assert result["final_guardian_count"] == "OPEN"
    assert result["provisional_seat_count"] == 6
    assert result["planning_slot_status"] == PLANNING_SLOT_STATUS
    assert result["seat_ids"] == ["SG-01", "SG-02", "SG-03", "SG-04", "SG-05", "SG-06"]
    assert result["reasons"] == []
    _assert_denials(result)
    fixture = _fixture()
    subjects = {seat["seat_id"]: seat["subject"] for seat in fixture["seats"]}
    assert subjects == {
        "SG-01": "Master V2",
        "SG-02": "Cap21–Cap23",
        "SG-03": "Execution",
        "SG-04": "Self-Learning",
        "SG-05": "Optimization",
        "SG-06": "Market Intelligence",
    }
    cap23 = next(seat for seat in fixture["seats"] if seat["seat_id"] == "SG-02")
    assert cap23["is_architecture_universe"] is False
    assert cap23["sixth_architecture_universe"] is False
    assert cap23["architecture_universe"] is None
    assert cap23["assigned_areas"] == []
    for seat in fixture["seats"]:
        assert seat["tool_slots"] == {name: PLANNING_SLOT_STATUS for name in TOOL_SLOT_NAMES}
        assert set(seat["tool_slots"]) == set(TOOL_SLOT_NAMES)


def test_unassigned_surfaces_stay_outside_the_six_seats() -> None:
    fixture = _fixture()
    area_ids = [area["area_id"] for area in fixture["unassigned"]]
    assert area_ids == [
        "GV-07",
        "GV-08",
        "GV-09",
        "GV-10",
        "GV-11",
        "GV-12",
        "GV-13",
        "GV-14",
        "GV-15",
        "FULL_CORE",
        "N5",
        "HOST",
        "SEND",
        "WIRE",
        "CAP24",
        "ORDER_INTENT",
        "SAFETY_LAYERS",
        "RESEARCH_CORPUS",
    ]
    retained = {
        source: [
            area["area_id"] for area in fixture["unassigned"] if area["retained_from"] == source
        ]
        for source in ("GV-16", "GV-17", "GV-18")
    }
    assert retained == {
        "GV-16": ["FULL_CORE", "N5"],
        "GV-17": ["SAFETY_LAYERS"],
        "GV-18": ["ORDER_INTENT"],
    }
    result = _validate(fixture)
    assert result["retained_split_surfaces"] == {
        "GV-16": ["FULL_CORE", "N5"],
        "GV-17": ["SAFETY_LAYERS"],
        "GV-18": ["ORDER_INTENT"],
    }
    assert result["status"] == STATUS_ACCEPTED


def test_missing_seat_is_rejected() -> None:
    fixture = _fixture()
    fixture["seats"] = [seat for seat in fixture["seats"] if seat["seat_id"] != "SG-04"]
    result = _validate(fixture)
    assert result["status"] == STATUS_MISSING_RESPONSIBILITY_AREA
    assert result["reasons"] == ["missing_seat:SG-04"]
    _assert_denials(result)


def test_duplicate_seat_is_rejected() -> None:
    fixture = _fixture()
    fixture["seats"].append(deepcopy(fixture["seats"][0]))
    result = _validate(fixture)
    assert result["status"] == STATUS_DUPLICATE_IDENTIFIER
    assert result["reasons"] == ["duplicate_seat:SG-01"]
    _assert_denials(result)


def test_host_assignment_and_sixth_universe_are_rejected() -> None:
    assigned = _fixture()
    assigned["seats"][2]["assigned_areas"] = ["HOST"]
    universe = _fixture()
    universe["seats"][1]["is_architecture_universe"] = True
    universe["seats"][1]["sixth_architecture_universe"] = True
    assigned_result = _validate(assigned)
    universe_result = _validate(universe)
    assert assigned_result["status"] == STATUS_ILLEGAL_SEAT_ASSIGNMENT
    assert assigned_result["reasons"] == ["assigned_areas:2"]
    assert universe_result["status"] == STATUS_ILLEGAL_SEAT_ASSIGNMENT
    assert "sixth_universe:SG-02" in universe_result["reasons"]
    assert "universe_flag:SG-02" in universe_result["reasons"]
    _assert_denials(assigned_result)
    _assert_denials(universe_result)


def test_unknown_tool_slot_is_rejected() -> None:
    fixture = _fixture()
    fixture["seats"][0]["tool_slots"]["DOMAIN_EXECUTION_GHOSV"] = PLANNING_SLOT_STATUS
    result = _validate(fixture)
    assert result["status"] == STATUS_UNKNOWN_TOOL_SLOT
    assert result["reasons"] == ["unknown_tool_slot:0:DOMAIN_EXECUTION_GHOSV"]
    _assert_denials(result)


def test_implicit_ratification_is_rejected() -> None:
    fixture = _fixture()
    fixture["invariants"]["guardian_ratification"] = True
    result = _validate(fixture)
    assert result["status"] == STATUS_IMPLICIT_GUARDIAN_RATIFICATION
    assert result["guardian_ratification"] is False
    assert "ratification:invariants.guardian_ratification" in result["reasons"]
    _assert_denials(result)


def test_claimed_current_coverage_is_rejected() -> None:
    flagged = _fixture()
    flagged["invariants"]["current_coverage"] = True
    slotted = _fixture()
    slotted["seats"][2]["tool_slots"]["DOMAIN_GHV"] = "PRESENT_UNBOUND"
    flagged_result = _validate(flagged)
    slotted_result = _validate(slotted)
    assert flagged_result["status"] == STATUS_CLAIMED_CURRENT_COVERAGE
    assert flagged_result["current_coverage"] is False
    assert slotted_result["status"] == STATUS_CLAIMED_CURRENT_COVERAGE
    assert "wp_b0_status_rejected:2:DOMAIN_GHV" in slotted_result["reasons"]
    _assert_denials(flagged_result)
    _assert_denials(slotted_result)


def test_productive_authority_is_rejected() -> None:
    fixture = _fixture()
    fixture["invariants"]["trading_authority"] = "LIVE"
    fixture["coordinator"]["authority"] = "EXECUTION"
    result = _validate(fixture)
    assert result["status"] == STATUS_PRODUCTIVE_AUTHORITY
    assert result["authority"] == "NONE"
    assert result["trading_authority"] == "NONE"
    _assert_denials(result)


def test_coordinator_count_conflict_is_rejected() -> None:
    counted = _fixture()
    counted["coordinator"]["count"] = 2
    closed = _fixture()
    closed["invariants"]["final_guardian_count"] = "6"
    counted_result = _validate(counted)
    closed_result = _validate(closed)
    assert counted_result["status"] == STATUS_COORDINATOR_COUNT_CONFLICT
    assert counted_result["reasons"] == ["coordinator_count"]
    assert counted_result["coordinator_count"] is None
    assert closed_result["status"] == STATUS_COORDINATOR_COUNT_CONFLICT
    assert closed_result["reasons"] == ["final_guardian_count"]
    _assert_denials(counted_result)
    _assert_denials(closed_result)


def test_missing_unassigned_surface_is_rejected() -> None:
    fixture = _fixture()
    fixture["unassigned"] = [
        area for area in fixture["unassigned"] if area["area_id"] != "RESEARCH_CORPUS"
    ]
    result = _validate(fixture)
    assert result["status"] == STATUS_MISSING_UNASSIGNED_SURFACE
    assert "missing_unassigned:RESEARCH_CORPUS" in result["reasons"]
    _assert_denials(result)


def test_repeated_calls_are_identical() -> None:
    first = _validate()
    second = _validate()
    assert first == second
    rejected = _fixture()
    rejected["coordinator"]["count"] = 0
    assert _validate(rejected) == _validate(deepcopy(rejected))


def test_phase_a_and_wp_b0_contracts_stay_unbound() -> None:
    assert PLANNING_SLOT_STATUS not in TOOL_SLOT_STATUSES
    assert tuple(TOOL_SLOT_NAMES) == (
        "DOMAIN_GHV",
        "DOMAIN_CURRENT_CAUSAL_GRAPH",
        "DOMAIN_GHOSV",
    )
    binding = bind_pin_and_scope_v1(
        authoritative_commit_sha=_COMMIT,
        authoritative_tree_sha=_TREE,
        declared_commit_sha=_COMMIT,
        declared_tree_sha=_TREE,
        provenance={
            "census": {"pin": _COMMIT},
            "landscape": {"commit_pin": _COMMIT, "tree_pin": _TREE},
            "graph": {"pin": _COMMIT},
        },
        scope={"allowed_nodes": ["synthetic-node"], "exclusions": [], "unassigned": []},
    )
    assert binding["authority"] == AUTHORITY
    assert binding["guardian_identity"] is GUARDIAN_IDENTITY
    assert binding["coverage_proof"] is False
    manifest = validate_guardian_domain_scope_manifest_v1(
        authoritative_commit_sha=_COMMIT,
        authoritative_tree_sha=_TREE,
        manifest={
            "manifest_id": "PLANNING-FIXTURE-SLOT-PROBE",
            "declared_commit_sha": _COMMIT,
            "declared_tree_sha": _TREE,
            "provenance": {
                "census": {"pin": _COMMIT},
                "landscape": {"commit_pin": _COMMIT, "tree_pin": _TREE},
                "graph": {"pin": _COMMIT},
            },
            "scope": {"allowed_nodes": ["synthetic-node"], "exclusions": [], "unassigned": []},
            "tool_slots": {name: PLANNING_SLOT_STATUS for name in TOOL_SLOT_NAMES},
        },
    )
    assert manifest["status"] == "INVALID_MANIFEST"
    assert manifest["current_proven"] is False
    assert manifest["guardian_ratification"] is False
    for name in TOOL_SLOT_NAMES:
        assert f"tool_slot_status_invalid:{name}" in manifest["reasons"]
    source = "\n".join(path.read_text(encoding="utf-8") for path in _PACKAGE.glob("*.py"))
    assert "execution_guardian_binding_verifier_v1" not in source
    assert "scoped_causal_graph_adapter_v1" not in source
    assert "TOOL_SLOT_STATUSES" in (_PACKAGE / "validate_v1.py").read_text(encoding="utf-8")


def test_non_object_fixture_is_rejected() -> None:
    result = validate_guardian_planning_fixture_v1([])  # type: ignore[arg-type]
    assert result["status"] == STATUS_INVALID_FIXTURE
    assert result["reasons"] == ["fixture_not_object"]
    _assert_denials(result)
