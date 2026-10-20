"""Pin and scope binding fixtures use the pinned mainline and recorded legacy pins."""

from __future__ import annotations

from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    AUTHORITY,
    COVERAGE_PROOF,
    GUARDIAN_IDENTITY,
    SAFETY_AUTHORITY,
    STATUS_ACCEPTED,
    STATUS_INPUT_SOURCE_STALE,
    STATUS_INVALID_PROVENANCE,
    STATUS_INVALID_SCOPE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_CONFLICT,
    STATUS_SCOPE_EMPTY,
    TRADING_AUTHORITY,
)

CURRENT_COMMIT = "e1059ebea40399ca02ee1f303874f8e09b9d54b1"
CURRENT_TREE = "fb5bea3e2760a25b47efe05038821e1d1180e1bb"
CENSUS_LEGACY_PIN = "6216201d7acbc771f84b6b6884eccc41359927cf"
LANDSCAPE_LEGACY_COMMIT = "e5d9296fb269208b06980518d410b4f2b616bf5b"
LANDSCAPE_LEGACY_TREE = "6422bfde79fd5aa45d2939a821980abf9aa4e3df"
GRAPH_LEGACY_PIN = "b6ffca1d3b39b3dd8814c7c795a8aa6e04bc177a"


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


def _bind(**overrides: object) -> dict[str, object]:
    payload = {
        "authoritative_commit_sha": CURRENT_COMMIT,
        "authoritative_tree_sha": CURRENT_TREE,
        "declared_commit_sha": CURRENT_COMMIT,
        "declared_tree_sha": CURRENT_TREE,
        "provenance": _provenance(),
        "scope": _scope(),
    }
    payload.update(overrides)
    return bind_pin_and_scope_v1(**payload)


def test_current_commit_and_tree_are_accepted() -> None:
    result = _bind(scope=_scope(allowed=["node-a"], exclusions=["node-b"]))

    assert result["status"] == STATUS_ACCEPTED
    assert result["declared_commit_sha"] == CURRENT_COMMIT
    assert result["declared_tree_sha"] == CURRENT_TREE
    assert result["allowed_nodes"] == ["node-a"]
    assert result["exclusions"] == ["node-b"]
    assert result["unassigned"] == []
    assert result["coverage_gap"] is False
    assert result["coverage_proof"] is COVERAGE_PROOF
    assert result["authority"] == AUTHORITY
    assert result["trading_authority"] == TRADING_AUTHORITY
    assert result["safety_authority"] == SAFETY_AUTHORITY
    assert result["guardian_identity"] is GUARDIAN_IDENTITY
    assert result["implicit_scope_expansion"] is False


def test_wrong_commit_sha_is_pin_mismatch() -> None:
    result = _bind(declared_commit_sha=CENSUS_LEGACY_PIN)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert result["mismatches"] == ["commit"]
    assert result["coverage_proof"] is False


def test_wrong_tree_sha_is_pin_mismatch() -> None:
    result = _bind(declared_tree_sha=LANDSCAPE_LEGACY_TREE)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert result["mismatches"] == ["tree"]


def test_stale_census_pin_is_input_source_stale() -> None:
    result = _bind(provenance=_provenance(census_pin=CENSUS_LEGACY_PIN))

    assert result["status"] == STATUS_INPUT_SOURCE_STALE
    assert result["stale_sources"] == ["census"]


def test_stale_landscape_pins_are_input_source_stale() -> None:
    result = _bind(
        provenance=_provenance(
            landscape_commit=LANDSCAPE_LEGACY_COMMIT,
            landscape_tree=LANDSCAPE_LEGACY_TREE,
        )
    )

    assert result["status"] == STATUS_INPUT_SOURCE_STALE
    assert result["stale_sources"] == ["landscape_commit", "landscape_tree"]


def test_stale_graph_pin_is_input_source_stale() -> None:
    result = _bind(provenance=_provenance(graph_pin=GRAPH_LEGACY_PIN))

    assert result["status"] == STATUS_INPUT_SOURCE_STALE
    assert result["stale_sources"] == ["graph"]


def test_empty_scope_is_a_coverage_gap() -> None:
    result = _bind(scope=_scope(allowed=[], exclusions=[], unassigned=[]))

    assert result["status"] == STATUS_SCOPE_EMPTY
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False
    assert result["allowed_nodes"] == []


def test_unassigned_only_scope_stays_accepted_with_gap() -> None:
    result = _bind(scope=_scope(allowed=[], exclusions=[], unassigned=["area-open"]))

    assert result["status"] == STATUS_ACCEPTED
    assert result["allowed_nodes"] == []
    assert result["unassigned"] == ["area-open"]
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_exclusion_overlap_is_scope_conflict() -> None:
    result = _bind(scope=_scope(allowed=["node-a"], exclusions=["node-a"]))

    assert result["status"] == STATUS_SCOPE_CONFLICT
    assert result["conflicts"] == [{"node": "node-a", "sets": ["allowed_nodes", "exclusions"]}]
    assert result["allowed_nodes"] == ["node-a"]
    assert result["exclusions"] == ["node-a"]


def test_invalid_provenance_is_rejected() -> None:
    provenance = _provenance()
    provenance["census"] = {"pin": "not-a-sha"}
    provenance["guardian"] = {"pin": CURRENT_COMMIT}

    result = _bind(provenance=provenance)

    assert result["status"] == STATUS_INVALID_PROVENANCE
    assert "census.pin_malformed" in result["reasons"]
    assert "provenance_extra:guardian" in result["reasons"]


def test_exclusions_only_is_a_scope_gap_without_proof() -> None:
    result = _bind(scope=_scope(allowed=[], exclusions=["node-x"], unassigned=[]))

    assert result["status"] == STATUS_ACCEPTED
    assert result["scope_coverage_gap"] is True
    assert result["graph_coverage_gap"] is False
    assert result["observation_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False
    assert result["allowed_nodes"] == []


def test_unassigned_scope_gap_is_independent_of_other_dimensions() -> None:
    result = _bind(scope=_scope(allowed=["node-a"], unassigned=["node-u"]))

    assert result["scope_coverage_gap"] is True
    assert result["graph_coverage_gap"] is False
    assert result["observation_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_malformed_scope_is_invalid_scope() -> None:
    result = _bind(scope={"allowed_nodes": ["node-a"], "exclusions": "node-b"})

    assert result["status"] == STATUS_INVALID_SCOPE
    assert "scope_missing:unassigned" in result["reasons"]
    assert "exclusions_not_list" in result["reasons"]
