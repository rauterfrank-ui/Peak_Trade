"""Synthetic manifest contract tests. No guardian catalog and no domain binding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.ops.guardian_domain_scope_manifest_v1.constants_v1 import (
    FORBIDDEN_OUTPUT_KEYS,
    STATUS_BINDER_RESULT_REJECTED,
    STATUS_INVALID_MANIFEST,
    STATUS_MANIFEST_RECORDED,
    TOOL_SLOT_NAMES,
)
from scripts.ops.guardian_domain_scope_manifest_v1.validate_v1 import (
    validate_guardian_domain_scope_manifest_v1,
)
from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    COVERAGE_PROOF,
    GUARDIAN_IDENTITY,
    STATUS_ACCEPTED,
    STATUS_INPUT_SOURCE_STALE,
    STATUS_INVALID_PROVENANCE,
    STATUS_INVALID_SCOPE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_CONFLICT,
    STATUS_SCOPE_EMPTY,
)

CURRENT_COMMIT = "1228f33f4f4bdd660afb2e59d7e20cbf8f25569c"
CURRENT_TREE = "f85db3ef095050c722ac0ce1e524afb45b745502"
OTHER_COMMIT = "e1059ebea40399ca02ee1f303874f8e09b9d54b1"
OTHER_TREE = "fb5bea3e2760a25b47efe05038821e1d1180e1bb"
STALE_GRAPH_PIN = "b6ffca1d3b39b3dd8814c7c795a8aa6e04bc177a"

_PACKAGE = (
    Path(__file__).resolve().parents[2] / "scripts" / "ops" / "guardian_domain_scope_manifest_v1"
)


def _provenance(
    *,
    census_pin: str = CURRENT_COMMIT,
    landscape_commit: str = CURRENT_COMMIT,
    landscape_tree: str = CURRENT_TREE,
    graph_pin: str = CURRENT_COMMIT,
) -> dict[str, dict[str, str]]:
    return {
        "census": {"pin": census_pin},
        "landscape": {"commit_pin": landscape_commit, "tree_pin": landscape_tree},
        "graph": {"pin": graph_pin},
    }


def _scope(
    allowed: list[str] | None = None,
    exclusions: list[str] | None = None,
    unassigned: list[str] | None = None,
) -> dict[str, list[str]]:
    return {
        "allowed_nodes": ["node-a"] if allowed is None else allowed,
        "exclusions": [] if exclusions is None else exclusions,
        "unassigned": [] if unassigned is None else unassigned,
    }


def _slots(**overrides: str) -> dict[str, str]:
    slots = {name: "ABSENT" for name in TOOL_SLOT_NAMES}
    slots.update(overrides)
    return slots


def _manifest(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "manifest_id": "SYNTHETIC-AREA-1",
        "declared_commit_sha": CURRENT_COMMIT,
        "declared_tree_sha": CURRENT_TREE,
        "provenance": _provenance(),
        "scope": _scope(),
        "tool_slots": _slots(),
    }
    payload.update(overrides)
    return payload


def _validate(
    manifest: dict[str, Any] | None = None,
    *,
    binder: Any = None,
    authoritative_commit_sha: str = CURRENT_COMMIT,
    authoritative_tree_sha: str = CURRENT_TREE,
) -> dict[str, Any]:
    return validate_guardian_domain_scope_manifest_v1(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        manifest=_manifest() if manifest is None else manifest,
        binder=binder,
    )


def _assert_denials(result: dict[str, Any]) -> None:
    assert result["authority"] == "NONE"
    assert result["trading_authority"] == "NONE"
    assert result["safety_authority"] == "NONE"
    assert result["execution_authority"] == "NONE"
    assert result["runtime_authorization_effect"] == "NONE"
    assert result["guardian_identity"] is GUARDIAN_IDENTITY
    assert result["guardian_ratification"] is False
    assert result["current_proven"] is False
    assert result["coverage_proof"] is COVERAGE_PROOF
    assert result["live_gate"] is False
    assert result["network_access"] is False
    assert result["implicit_scope_expansion"] is False
    assert result["tool_slot_inference"] is False
    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(result)


def test_unassigned_only_scope_is_recorded_with_gap() -> None:
    result = _validate(
        _manifest(
            scope=_scope(allowed=[], unassigned=["area-open"]),
            tool_slots=_slots(),
        )
    )

    assert result["status"] == STATUS_MANIFEST_RECORDED
    assert result["wp_a0_status"] == STATUS_ACCEPTED
    assert result["allowed_nodes"] == []
    assert result["unassigned"] == ["area-open"]
    assert result["scope_coverage_gap"] is True
    assert result["coverage_gap"] is True
    _assert_denials(result)


def test_identical_pin_mismatch_statuses_are_recorded() -> None:
    result = _validate(
        _manifest(tool_slots=_slots(**{name: "PRESENT_PIN_MISMATCH" for name in TOOL_SLOT_NAMES}))
    )

    assert result["status"] == STATUS_MANIFEST_RECORDED
    assert result["tool_slots"] == {name: "PRESENT_PIN_MISMATCH" for name in TOOL_SLOT_NAMES}


def test_mixed_tool_statuses_are_recorded() -> None:
    slots = _slots(
        DOMAIN_GHV="ABSENT",
        DOMAIN_CURRENT_CAUSAL_GRAPH="PRESENT_UNBOUND",
        DOMAIN_GHOSV="PRESENT_PIN_MISMATCH",
    )

    result = _validate(_manifest(tool_slots=slots))

    assert result["status"] == STATUS_MANIFEST_RECORDED
    assert result["tool_slots"] == slots


def test_exclusions_only_keeps_the_scope_gap() -> None:
    result = _validate(_manifest(scope=_scope(allowed=[], exclusions=["node-x"])))

    assert result["status"] == STATUS_MANIFEST_RECORDED
    assert result["scope_coverage_gap"] is True
    assert result["coverage_proof"] is False
    assert result["allowed_nodes"] == []


def test_disjoint_scope_records_without_coverage_proof() -> None:
    result = _validate(_manifest(scope=_scope(allowed=["node-a"], exclusions=["node-b"])))

    assert result["status"] == STATUS_MANIFEST_RECORDED
    assert result["scope_coverage_gap"] is False
    assert result["coverage_gap"] is False
    assert result["coverage_proof"] is False
    assert result["current_proven"] is False
    assert result["guardian_ratification"] is False


def test_wrong_commit_is_pin_mismatch() -> None:
    result = _validate(_manifest(declared_commit_sha=OTHER_COMMIT))

    assert result["status"] == STATUS_PIN_MISMATCH
    assert result["wp_a0_status"] == STATUS_PIN_MISMATCH
    assert result["wp_a0_invoked"] is True
    _assert_denials(result)


def test_wrong_tree_is_pin_mismatch() -> None:
    result = _validate(_manifest(declared_tree_sha=OTHER_TREE))

    assert result["status"] == STATUS_PIN_MISMATCH


def test_stale_provenance_pins_stay_stale() -> None:
    census = _validate(_manifest(provenance=_provenance(census_pin=OTHER_COMMIT)))
    landscape = _validate(
        _manifest(provenance=_provenance(landscape_commit=OTHER_COMMIT, landscape_tree=OTHER_TREE))
    )
    graph = _validate(_manifest(provenance=_provenance(graph_pin=STALE_GRAPH_PIN)))

    assert census["status"] == STATUS_INPUT_SOURCE_STALE
    assert landscape["status"] == STATUS_INPUT_SOURCE_STALE
    assert graph["status"] == STATUS_INPUT_SOURCE_STALE
    assert "graph" in graph["wp_a0_result"]["stale_sources"]


def test_malformed_sha_and_bad_provenance_are_rejected() -> None:
    uppercase = _validate(_manifest(declared_commit_sha=CURRENT_COMMIT.upper()))
    provenance = _provenance()
    del provenance["census"]
    provenance["guardian"] = {"pin": CURRENT_COMMIT}
    invalid = _validate(_manifest(provenance=provenance))

    assert uppercase["status"] == STATUS_INVALID_PROVENANCE
    assert invalid["status"] == STATUS_INVALID_PROVENANCE
    assert "provenance_missing:census" in invalid["reasons"]
    assert "provenance_extra:guardian" in invalid["reasons"]


def test_malformed_scope_is_invalid_scope() -> None:
    missing = _validate(_manifest(scope={"allowed_nodes": ["node-a"], "exclusions": []}))
    duplicate = _validate(_manifest(scope=_scope(allowed=["node-a", "node-a"])))
    blank = _validate(_manifest(scope=_scope(allowed=["  "])))

    assert missing["status"] == STATUS_INVALID_SCOPE
    assert "scope_missing:unassigned" in missing["reasons"]
    assert duplicate["status"] == STATUS_INVALID_SCOPE
    assert blank["status"] == STATUS_INVALID_SCOPE


def test_overlapping_scope_is_a_conflict() -> None:
    result = _validate(_manifest(scope=_scope(allowed=["node-a"], unassigned=["node-a"])))

    assert result["status"] == STATUS_SCOPE_CONFLICT
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_empty_scope_stays_empty() -> None:
    result = _validate(_manifest(scope=_scope(allowed=[], exclusions=[], unassigned=[])))

    assert result["status"] == STATUS_SCOPE_EMPTY
    assert result["coverage_gap"] is True
    assert result["allowed_nodes"] == []


def test_missing_slot_with_wrong_pin_keeps_pin_mismatch() -> None:
    slots = _slots()
    del slots["DOMAIN_GHOSV"]
    result = _validate(_manifest(declared_commit_sha=OTHER_COMMIT, tool_slots=slots))

    assert result["status"] == STATUS_PIN_MISMATCH
    assert "DOMAIN_GHOSV" not in result["tool_slots"]


def test_missing_slot_is_not_filled_from_a_sibling() -> None:
    slots = _slots(DOMAIN_GHV="PRESENT_UNBOUND", DOMAIN_CURRENT_CAUSAL_GRAPH="ABSENT")
    del slots["DOMAIN_GHOSV"]

    result = _validate(_manifest(tool_slots=slots))

    assert result["status"] == STATUS_INVALID_MANIFEST
    assert result["wp_a0_status"] == STATUS_ACCEPTED
    assert "tool_slot_missing:DOMAIN_GHOSV" in result["reasons"]
    assert "DOMAIN_GHOSV" not in result["tool_slots"]
    assert result["tool_slots"]["DOMAIN_GHV"] == "PRESENT_UNBOUND"
    assert result["tool_slots"]["DOMAIN_CURRENT_CAUSAL_GRAPH"] == "ABSENT"


def test_extra_slot_and_evidence_object_are_rejected() -> None:
    extra = _slots()
    extra["DOMAIN_EXECUTION_GHOSV"] = "ABSENT"
    evidence = _slots()
    evidence["DOMAIN_GHV"] = {"status": "ABSENT", "pin": OTHER_COMMIT}  # type: ignore[assignment]

    extra_result = _validate(_manifest(tool_slots=extra))
    evidence_result = _validate(_manifest(tool_slots=evidence))

    assert extra_result["status"] == STATUS_INVALID_MANIFEST
    assert "tool_slot_extra:DOMAIN_EXECUTION_GHOSV" in extra_result["reasons"]
    assert evidence_result["status"] == STATUS_INVALID_MANIFEST
    assert "tool_slot_evidence_rejected:DOMAIN_GHV" in evidence_result["reasons"]
    assert "DOMAIN_GHV" not in evidence_result["tool_slots"]


def test_tool_status_key_does_not_supply_a_missing_slot() -> None:
    slots = _slots()
    del slots["DOMAIN_CURRENT_CAUSAL_GRAPH"]
    manifest = _manifest(tool_slots=slots)
    manifest["tool_status"] = "ABSENT"

    result = _validate(manifest)

    assert result["status"] == STATUS_INVALID_MANIFEST
    assert "manifest_extra:tool_status" in result["reasons"]
    assert "tool_slot_missing:DOMAIN_CURRENT_CAUSAL_GRAPH" in result["reasons"]
    assert "DOMAIN_CURRENT_CAUSAL_GRAPH" not in result["tool_slots"]


def test_forbidden_claims_are_rejected_after_a_matching_pin() -> None:
    proven = _manifest()
    proven["current_proven"] = True
    proof = _manifest()
    proof["coverage_proof"] = True
    trading = _manifest()
    trading["trading_authority"] = "LIVE"

    proven_result = _validate(proven)
    proof_result = _validate(proof)
    trading_result = _validate(trading)

    assert proven_result["status"] == STATUS_INVALID_MANIFEST
    assert "forbidden_claim:current_proven" in proven_result["reasons"]
    assert proven_result["current_proven"] is False
    assert proof_result["status"] == STATUS_INVALID_MANIFEST
    assert "forbidden_claim:coverage_proof" in proof_result["reasons"]
    assert trading_result["status"] == STATUS_INVALID_MANIFEST
    assert "forbidden_claim:trading_authority" in trading_result["reasons"]
    assert trading_result["trading_authority"] == "NONE"


def test_manifest_id_does_not_become_a_node() -> None:
    result = _validate(
        _manifest(
            manifest_id="GV-01",
            scope=_scope(allowed=[], unassigned=["area-open"]),
        )
    )

    assert result["status"] == STATUS_MANIFEST_RECORDED
    assert result["manifest_id"] == "GV-01"
    assert "GV-01" not in result["allowed_nodes"]
    assert "GV-01" not in result["exclusions"]
    assert "GV-01" not in result["unassigned"]


def test_binder_added_node_is_rejected() -> None:
    def _binder(**kwargs: Any) -> dict[str, Any]:
        result = bind_pin_and_scope_v1(**kwargs)
        result["allowed_nodes"] = [*result["allowed_nodes"], "GV-01"]
        return result

    result = _validate(binder=_binder)

    assert result["status"] == STATUS_BINDER_RESULT_REJECTED
    assert "binder_scope_rejected:allowed_nodes" in result["reasons"]
    assert result["wp_a0_result"]["allowed_nodes"] == ["node-a", "GV-01"]
    assert result["current_proven"] is False


def test_binder_coverage_proof_is_rejected() -> None:
    def _binder(**kwargs: Any) -> dict[str, Any]:
        result = bind_pin_and_scope_v1(**kwargs)
        result["coverage_proof"] = True
        return result

    result = _validate(binder=_binder)

    assert result["status"] == STATUS_BINDER_RESULT_REJECTED
    assert "binder_coverage_proof_rejected" in result["reasons"]
    assert result["coverage_proof"] is False
    assert result["wp_a0_result"]["coverage_proof"] is True


def test_binder_guardian_identity_and_scope_expansion_are_rejected() -> None:
    def _guardian(**kwargs: Any) -> dict[str, Any]:
        result = bind_pin_and_scope_v1(**kwargs)
        result["guardian_identity"] = True
        return result

    def _expansion(**kwargs: Any) -> dict[str, Any]:
        result = bind_pin_and_scope_v1(**kwargs)
        result["implicit_scope_expansion"] = True
        return result

    guardian = _validate(binder=_guardian)
    expansion = _validate(binder=_expansion)

    assert guardian["status"] == STATUS_BINDER_RESULT_REJECTED
    assert "binder_guardian_identity_rejected" in guardian["reasons"]
    assert guardian["guardian_identity"] is False
    assert guardian["guardian_ratification"] is False
    assert expansion["status"] == STATUS_BINDER_RESULT_REJECTED
    assert "binder_implicit_scope_expansion_rejected" in expansion["reasons"]
    assert expansion["implicit_scope_expansion"] is False


def test_repeated_calls_are_identical() -> None:
    manifest = _manifest(
        tool_slots=_slots(
            DOMAIN_GHV="PRESENT_UNBOUND",
            DOMAIN_CURRENT_CAUSAL_GRAPH="ABSENT",
            DOMAIN_GHOSV="PRESENT_PIN_MISMATCH",
        )
    )

    assert _validate(manifest) == _validate(manifest)


def test_constants_and_validator_have_no_area_catalog() -> None:
    constants = (_PACKAGE / "constants_v1.py").read_text(encoding="utf-8")
    validator = (_PACKAGE / "validate_v1.py").read_text(encoding="utf-8")
    for number in range(1, 19):
        token = f"GV-{number:02d}"
        assert token not in constants
        assert token not in validator
    assert "scoped_ghv_crosswalk_adapter_v1" not in validator
    assert "scoped_causal_graph_adapter_v1" not in validator
    assert "generic_ghosv_kernel_v1" not in validator
    assert "bind_pin_and_scope_v1" in validator
