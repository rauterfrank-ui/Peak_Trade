"""Validate the guardian planning fixture. AUTHORITY=NONE.

The fixture records planning labels. It does not bind domains, ratify
guardians, or emit a WP-B0 tool-slot status. PLANNING_UNBOUND is
fixture-internal and is not a WP-B0 slot status.
"""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.guardian_domain_scope_manifest_v1.constants_v1 import (
    TOOL_SLOT_NAMES,
    TOOL_SLOT_STATUSES,
)
from scripts.ops.guardian_planning_fixture_v1.constants_v1 import (
    ARCHITECTURE_STATUS,
    AUTHORITY,
    COORDINATOR_COUNT,
    COORDINATOR_ROLE,
    EXECUTION_AUTHORITY,
    FAULT_PRIORITY,
    FINAL_GUARDIAN_COUNT,
    PLANNING_SLOT_STATUS,
    RETAINED_SPLIT_SURFACES,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    SCHEMA_ID,
    SCHEMA_VERSION,
    SEAT_ROWS,
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
    TRADING_AUTHORITY,
    UNASSIGNED_ROWS,
    WP_B0_BINDABLE,
)

_TOP_FIELDS = ("coordinator", "invariants", "schema_id", "schema_version", "seats", "unassigned")
_EXPECTED_SEATS = {row[0]: row for row in SEAT_ROWS}
_EXPECTED_AREAS = {row[0]: row for row in UNASSIGNED_ROWS}
_UNASSIGNED_IDS = frozenset(_EXPECTED_AREAS)
_AUTHORITY_FIELDS = ("authority", "execution_authority", "safety_authority", "trading_authority")


def canonical_planning_fixture_v1() -> dict[str, Any]:
    """Return the canonical planning fixture. Callers may copy and mutate it."""
    seats = []
    for seat_id, subject, universe, is_universe in SEAT_ROWS:
        seats.append(
            {
                "seat_id": seat_id,
                "subject": subject,
                "architecture_universe": universe,
                "is_architecture_universe": is_universe,
                "sixth_architecture_universe": False,
                "assigned_areas": [],
                "tool_slots": {name: PLANNING_SLOT_STATUS for name in TOOL_SLOT_NAMES},
            }
        )
    unassigned = [
        {"area_id": area_id, "subject": subject, "retained_from": retained}
        for area_id, subject, retained in UNASSIGNED_ROWS
    ]
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "coordinator": {
            "count": COORDINATOR_COUNT,
            "authority": AUTHORITY,
            "role": COORDINATOR_ROLE,
            "architecture_status": ARCHITECTURE_STATUS,
            "gcc_ratification": False,
        },
        "seats": seats,
        "unassigned": unassigned,
        "invariants": {
            "guardian_ratification": False,
            "domain_binding": False,
            "trading_authority": TRADING_AUTHORITY,
            "safety_authority": SAFETY_AUTHORITY,
            "execution_authority": EXECUTION_AUTHORITY,
            "productive_activation": False,
            "final_guardian_count": FINAL_GUARDIAN_COUNT,
            "current_coverage": False,
            "wp_b0_bindable": WP_B0_BINDABLE,
        },
    }


def validate_guardian_planning_fixture_v1(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Accept the canonical fixture, or return one deterministic fail-closed status."""
    if not isinstance(fixture, Mapping):
        return _output(STATUS_INVALID_FIXTURE, ["fixture_not_object"])
    faults = _faults(fixture)
    if faults:
        status = _select_status(faults)
        reasons = sorted(reason for fault_status, reason in faults if fault_status == status)
        return _output(status, reasons)
    if fixture != canonical_planning_fixture_v1():
        return _output(STATUS_INVALID_FIXTURE, ["fixture_drift"])
    return _output(STATUS_ACCEPTED, [])


def _faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    faults.extend(_shape_faults(fixture))
    faults.extend(_authority_faults(fixture))
    faults.extend(_ratification_faults(fixture))
    faults.extend(_coverage_faults(fixture))
    faults.extend(_count_faults(fixture))
    faults.extend(_slot_faults(fixture))
    faults.extend(_duplicate_faults(fixture))
    faults.extend(_assignment_faults(fixture))
    faults.extend(_missing_faults(fixture))
    return faults


def _shape_faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    if fixture.get("schema_id") != SCHEMA_ID:
        faults.append((STATUS_INVALID_FIXTURE, "schema_id_rejected"))
    if fixture.get("schema_version") != SCHEMA_VERSION:
        faults.append((STATUS_INVALID_FIXTURE, "schema_version_rejected"))
    extra = sorted(set(fixture) - set(_TOP_FIELDS))
    faults.extend((STATUS_INVALID_FIXTURE, f"fixture_extra:{name}") for name in extra)
    for name in _TOP_FIELDS:
        if name not in fixture:
            faults.append((STATUS_INVALID_FIXTURE, f"fixture_missing:{name}"))
    return faults


def _authority_faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    for path, value in _walk(fixture):
        key = path.rsplit(".", 1)[-1]
        if key in _AUTHORITY_FIELDS and value not in (None, AUTHORITY):
            faults.append((STATUS_PRODUCTIVE_AUTHORITY, f"productive_authority:{path}"))
        if key == "productive_activation" and value is True:
            faults.append((STATUS_PRODUCTIVE_AUTHORITY, f"productive_activation:{path}"))
        if key in {"live_authorized", "post_allowed"} and value is True:
            faults.append((STATUS_PRODUCTIVE_AUTHORITY, f"productive_authority:{path}"))
    return faults


def _ratification_faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    for path, value in _walk(fixture):
        key = path.rsplit(".", 1)[-1]
        if key in {"guardian_ratification", "guardian_ratified", "gcc_ratification"} and (
            value is True
        ):
            faults.append((STATUS_IMPLICIT_GUARDIAN_RATIFICATION, f"ratification:{path}"))
        if key == "architecture_status" and value != ARCHITECTURE_STATUS:
            faults.append((STATUS_IMPLICIT_GUARDIAN_RATIFICATION, f"architecture_status:{path}"))
    return faults


def _coverage_faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    for path, value in _walk(fixture):
        key = path.rsplit(".", 1)[-1]
        if key in {"current_coverage", "current_proven", "coverage_proof"} and value is True:
            faults.append((STATUS_CLAIMED_CURRENT_COVERAGE, f"current_coverage:{path}"))
    for seat_index, seat in _enumerate_maps(fixture.get("seats")):
        slots = seat.get("tool_slots")
        if not isinstance(slots, Mapping):
            continue
        for name, value in slots.items():
            if name in TOOL_SLOT_NAMES and value != PLANNING_SLOT_STATUS:
                faults.append(
                    (
                        STATUS_CLAIMED_CURRENT_COVERAGE,
                        f"slot_status:{seat_index}:{name}",
                    )
                )
            if value in TOOL_SLOT_STATUSES:
                faults.append(
                    (
                        STATUS_CLAIMED_CURRENT_COVERAGE,
                        f"wp_b0_status_rejected:{seat_index}:{name}",
                    )
                )
    return faults


def _count_faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    coordinator = fixture.get("coordinator")
    if isinstance(coordinator, Mapping):
        if coordinator.get("count") != COORDINATOR_COUNT:
            faults.append((STATUS_COORDINATOR_COUNT_CONFLICT, "coordinator_count"))
        if coordinator.get("role") != COORDINATOR_ROLE:
            faults.append((STATUS_COORDINATOR_COUNT_CONFLICT, "coordinator_role"))
    else:
        faults.append((STATUS_COORDINATOR_COUNT_CONFLICT, "coordinator_not_object"))
    invariants = fixture.get("invariants")
    if isinstance(invariants, Mapping) and (
        invariants.get("final_guardian_count") != FINAL_GUARDIAN_COUNT
    ):
        faults.append((STATUS_COORDINATOR_COUNT_CONFLICT, "final_guardian_count"))
    return faults


def _slot_faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    for seat_index, seat in _enumerate_maps(fixture.get("seats")):
        slots = seat.get("tool_slots")
        if not isinstance(slots, Mapping):
            faults.append((STATUS_INVALID_FIXTURE, f"tool_slots_not_object:{seat_index}"))
            continue
        for name in sorted(set(slots) - set(TOOL_SLOT_NAMES)):
            faults.append((STATUS_UNKNOWN_TOOL_SLOT, f"unknown_tool_slot:{seat_index}:{name}"))
        for name in TOOL_SLOT_NAMES:
            if name not in slots:
                faults.append((STATUS_INVALID_FIXTURE, f"tool_slot_missing:{seat_index}:{name}"))
    return faults


def _duplicate_faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    seen_seats: set[str] = set()
    for _seat_index, seat in _enumerate_maps(fixture.get("seats")):
        seat_id = seat.get("seat_id")
        if isinstance(seat_id, str) and seat_id in seen_seats:
            faults.append((STATUS_DUPLICATE_IDENTIFIER, f"duplicate_seat:{seat_id}"))
        if isinstance(seat_id, str):
            seen_seats.add(seat_id)
    seen_areas: set[str] = set()
    for _index, area in _enumerate_maps(fixture.get("unassigned")):
        area_id = area.get("area_id")
        if isinstance(area_id, str) and area_id in seen_areas:
            faults.append((STATUS_DUPLICATE_IDENTIFIER, f"duplicate_area:{area_id}"))
        if isinstance(area_id, str):
            seen_areas.add(area_id)
    return faults


def _assignment_faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    invariants = fixture.get("invariants")
    if isinstance(invariants, Mapping) and invariants.get("domain_binding") is True:
        faults.append((STATUS_ILLEGAL_SEAT_ASSIGNMENT, "domain_binding"))
    for seat_index, seat in _enumerate_maps(fixture.get("seats")):
        seat_id = seat.get("seat_id")
        if seat_id in _UNASSIGNED_IDS:
            faults.append((STATUS_ILLEGAL_SEAT_ASSIGNMENT, f"unassigned_used_as_seat:{seat_id}"))
        assigned = seat.get("assigned_areas")
        if isinstance(assigned, list) and assigned:
            faults.append((STATUS_ILLEGAL_SEAT_ASSIGNMENT, f"assigned_areas:{seat_index}"))
        elif not isinstance(assigned, list):
            faults.append((STATUS_INVALID_FIXTURE, f"assigned_areas_not_list:{seat_index}"))
        expected = _EXPECTED_SEATS.get(seat_id) if isinstance(seat_id, str) else None
        if expected is None:
            if isinstance(seat_id, str) and seat_id not in _UNASSIGNED_IDS:
                faults.append((STATUS_ILLEGAL_SEAT_ASSIGNMENT, f"unknown_seat:{seat_id}"))
            continue
        _seat_id, subject, universe, is_universe = expected
        if seat.get("subject") != subject:
            faults.append((STATUS_ILLEGAL_SEAT_ASSIGNMENT, f"subject:{seat_id}"))
        if seat.get("architecture_universe") != universe:
            faults.append((STATUS_ILLEGAL_SEAT_ASSIGNMENT, f"universe:{seat_id}"))
        if seat.get("is_architecture_universe") is not is_universe:
            faults.append((STATUS_ILLEGAL_SEAT_ASSIGNMENT, f"universe_flag:{seat_id}"))
        if seat.get("sixth_architecture_universe") is not False:
            faults.append((STATUS_ILLEGAL_SEAT_ASSIGNMENT, f"sixth_universe:{seat_id}"))
    return faults


def _missing_faults(fixture: Mapping[str, Any]) -> list[tuple[str, str]]:
    faults: list[tuple[str, str]] = []
    present_seats = {
        seat.get("seat_id")
        for _index, seat in _enumerate_maps(fixture.get("seats"))
        if isinstance(seat.get("seat_id"), str)
    }
    for seat_id in _EXPECTED_SEATS:
        if seat_id not in present_seats:
            faults.append((STATUS_MISSING_RESPONSIBILITY_AREA, f"missing_seat:{seat_id}"))
    present_areas = {
        area.get("area_id")
        for _index, area in _enumerate_maps(fixture.get("unassigned"))
        if isinstance(area.get("area_id"), str)
    }
    for area_id in _EXPECTED_AREAS:
        if area_id not in present_areas:
            faults.append((STATUS_MISSING_UNASSIGNED_SURFACE, f"missing_unassigned:{area_id}"))
    for source, surfaces in RETAINED_SPLIT_SURFACES.items():
        retained = sorted(
            area.get("area_id")
            for _index, area in _enumerate_maps(fixture.get("unassigned"))
            if area.get("retained_from") == source and isinstance(area.get("area_id"), str)
        )
        if tuple(retained) != surfaces:
            faults.append((STATUS_MISSING_UNASSIGNED_SURFACE, f"retained_split:{source}"))
    return faults


def _enumerate_maps(raw: Any) -> list[tuple[int, Mapping[str, Any]]]:
    if not isinstance(raw, list):
        return []
    return [(index, item) for index, item in enumerate(raw) if isinstance(item, Mapping)]


def _walk(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, Mapping):
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else str(key)
            found.append((path, value[key]))
            found.extend(_walk(value[key], path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_walk(item, f"{prefix}[{index}]"))
    return found


def _select_status(faults: list[tuple[str, str]]) -> str:
    present = {status for status, _reason in faults}
    for status in FAULT_PRIORITY:
        if status in present:
            return status
    return STATUS_INVALID_FIXTURE


def _output(status: str, reasons: list[str]) -> dict[str, Any]:
    accepted = status == STATUS_ACCEPTED
    canonical = canonical_planning_fixture_v1() if accepted else None
    seat_ids = [row[0] for row in SEAT_ROWS] if accepted else []
    area_ids = [row[0] for row in UNASSIGNED_ROWS] if accepted else []
    retained = (
        {key: list(value) for key, value in RETAINED_SPLIT_SURFACES.items()} if accepted else {}
    )
    if canonical is not None:
        seat_ids = [seat["seat_id"] for seat in canonical["seats"]]
        area_ids = [area["area_id"] for area in canonical["unassigned"]]
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "runtime_authorization_effect": RUNTIME_AUTHORIZATION_EFFECT,
        "guardian_ratification": False,
        "domain_binding": False,
        "productive_activation": False,
        "current_coverage": False,
        "wp_b0_bindable": WP_B0_BINDABLE,
        "wp_b0_slot_status_compatible": False,
        "planning_slot_status": PLANNING_SLOT_STATUS,
        "coordinator_count": COORDINATOR_COUNT if accepted else None,
        "coordinator_role": COORDINATOR_ROLE if accepted else None,
        "architecture_status": ARCHITECTURE_STATUS if accepted else None,
        "gcc_ratification": False,
        "final_guardian_count": FINAL_GUARDIAN_COUNT if accepted else None,
        "provisional_seat_count": len(SEAT_ROWS) if accepted else None,
        "seat_ids": seat_ids,
        "unassigned_area_ids": area_ids,
        "retained_split_surfaces": retained,
        "reasons": list(reasons),
    }
