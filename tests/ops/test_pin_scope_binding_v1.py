"""Pin and scope binding. Historical artifact pins are checked, not relabeled."""

from __future__ import annotations

from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    AUTHORITY,
    COVERAGE_PROOF,
    GUARDIAN_IDENTITY,
    SAFETY_AUTHORITY,
    STATUS_ACCEPTED,
    STATUS_FORGED_PROVENANCE,
    STATUS_INVALID_PROVENANCE,
    STATUS_INVALID_SCOPE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_CONFLICT,
    STATUS_SCOPE_EMPTY,
    TRADING_AUTHORITY,
)
from tests.ops.guardian_framework_fixtures_v1 import (
    AUTHORIZED_COMMIT,
    AUTHORIZED_TREE,
    CENSUS_EMBEDDED_PIN,
    GRAPH_LEGACY_PIN,
    LANDSCAPE_EMBEDDED_TREE,
    honest_provenance,
    scope_of,
)


def _bind(**overrides: object) -> dict[str, object]:
    payload = {
        "authoritative_commit_sha": AUTHORIZED_COMMIT,
        "authoritative_tree_sha": AUTHORIZED_TREE,
        "declared_commit_sha": AUTHORIZED_COMMIT,
        "declared_tree_sha": AUTHORIZED_TREE,
        "provenance": honest_provenance(),
        "scope": scope_of(excluded=["node-b"]),
    }
    payload.update(overrides)
    return bind_pin_and_scope_v1(**payload)


def test_current_commit_and_tree_are_accepted() -> None:
    result = _bind()

    assert result["status"] == STATUS_ACCEPTED
    assert result["declared_commit_sha"] == AUTHORIZED_COMMIT
    assert result["declared_tree_sha"] == AUTHORIZED_TREE
    assert result["domain_functional_members"] == ["node-a"]
    assert result["explicitly_out_of_scope"] == ["node-b"]
    assert result["unresolved"] == []
    assert result["stale_sources"] == ["census", "landscape_commit", "landscape_tree", "graph"]
    assert result["embedded_pins"]["census"] == CENSUS_EMBEDDED_PIN
    assert result["coverage_gap"] is False
    assert result["coverage_proof"] is COVERAGE_PROOF
    assert result["authority"] == AUTHORITY
    assert result["trading_authority"] == TRADING_AUTHORITY
    assert result["safety_authority"] == SAFETY_AUTHORITY
    assert result["guardian_identity"] is GUARDIAN_IDENTITY
    assert result["implicit_scope_expansion"] is False


def test_wrong_commit_sha_is_pin_mismatch() -> None:
    result = _bind(declared_commit_sha=CENSUS_EMBEDDED_PIN)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert "commit" in result["mismatches"]
    assert result["coverage_proof"] is False


def test_wrong_tree_sha_is_pin_mismatch() -> None:
    result = _bind(declared_tree_sha=LANDSCAPE_EMBEDDED_TREE)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert result["mismatches"] == ["tree"]


def test_forged_census_current_pin_is_rejected() -> None:
    result = _bind(
        provenance=honest_provenance(census_pin=AUTHORIZED_COMMIT, census_currency="CURRENT")
    )

    assert result["status"] == STATUS_FORGED_PROVENANCE
    assert "census_pin_not_embedded" in result["reasons"]
    assert result["coverage_proof"] is False


def test_forged_landscape_current_currency_is_rejected() -> None:
    result = _bind(provenance=honest_provenance(landscape_currency="CURRENT"))

    assert result["status"] == STATUS_FORGED_PROVENANCE
    assert "landscape_currency_forged_current" in result["reasons"]


def test_forged_graph_legacy_pin_is_rejected() -> None:
    result = _bind(provenance=honest_provenance(graph_pin=GRAPH_LEGACY_PIN))

    assert result["status"] == STATUS_FORGED_PROVENANCE
    assert "graph_pin_not_absent_sentinel" in result["reasons"]


def test_empty_scope_is_a_coverage_gap() -> None:
    result = _bind(scope=scope_of(members=[]))

    assert result["status"] == STATUS_SCOPE_EMPTY
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False
    assert result["domain_functional_members"] == []


def test_unresolved_only_scope_stays_accepted_with_gap() -> None:
    result = _bind(scope=scope_of(members=[], unresolved=["area-open"]))

    assert result["status"] == STATUS_ACCEPTED
    assert result["domain_functional_members"] == []
    assert result["unresolved"] == ["area-open"]
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_class_overlap_is_scope_conflict() -> None:
    result = _bind(scope=scope_of(members=["node-a"], excluded=["node-a"]))

    assert result["status"] == STATUS_SCOPE_CONFLICT
    assert result["conflicts"] == [
        {
            "node": "node-a",
            "sets": ["domain_functional_members", "explicitly_out_of_scope"],
        }
    ]


def test_invalid_provenance_is_rejected() -> None:
    provenance = honest_provenance()
    provenance["census"] = {"pin": "not-a-sha", "currency": "HISTORICAL"}
    provenance["guardian"] = {"pin": AUTHORIZED_COMMIT}

    result = _bind(provenance=provenance)

    assert result["status"] == STATUS_INVALID_PROVENANCE
    assert "census.pin_malformed" in result["reasons"]
    assert "provenance_extra:guardian" in result["reasons"]


def test_exclusions_only_is_a_scope_gap_without_proof() -> None:
    result = _bind(scope=scope_of(members=[], excluded=["node-x"]))

    assert result["status"] == STATUS_ACCEPTED
    assert result["scope_coverage_gap"] is True
    assert result["graph_coverage_gap"] is False
    assert result["observation_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_unresolved_scope_gap_is_independent_of_other_dimensions() -> None:
    result = _bind(scope=scope_of(unresolved=["node-u"]))

    assert result["scope_coverage_gap"] is True
    assert result["graph_coverage_gap"] is False
    assert result["observation_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_old_three_field_scope_is_invalid() -> None:
    result = _bind(scope={"allowed_nodes": ["node-a"], "exclusions": [], "unassigned": []})

    assert result["status"] == STATUS_INVALID_SCOPE
    assert "scope_extra:allowed_nodes" in result["reasons"]
    assert "scope_missing:domain_functional_members" in result["reasons"]
