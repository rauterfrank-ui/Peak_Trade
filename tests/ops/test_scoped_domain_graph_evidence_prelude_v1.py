"""Evidence prelude accepts only lines that contain the named symbol."""

from __future__ import annotations

from scripts.ops.scoped_domain_graph_evidence_prelude_v1.build_v1 import (
    build_code_reference_prelude_v1,
)
from tests.ops.guardian_framework_fixtures_v1 import AUTHORIZED_COMMIT, AUTHORIZED_TREE


def _nodes() -> list[dict[str, str]]:
    return [
        {"object_id": "node-a", "scope_class": "DOMAIN_FUNCTIONAL_MEMBER"},
        {"object_id": "node-b", "scope_class": "EXTERNAL_REFERENCE_ONLY"},
    ]


def _reference(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "edge_id": "edge-1",
        "source_native_id": "node-a",
        "target_native_id": "node-b",
        "edge_type": "CALLS",
        "path": "src/experiments/canonical_optimization_universe_v1.py",
        "line": 299,
        "symbol": "validate_canonical_optimization_universe_learning_input_v1",
    }
    body.update(overrides)
    return body


def test_evidenced_call_stays_unverified() -> None:
    result = build_code_reference_prelude_v1(
        declared_commit_sha=AUTHORIZED_COMMIT,
        declared_tree_sha=AUTHORIZED_TREE,
        nodes=_nodes(),
        references=[_reference()],
    )

    assert result["ok"] is True
    assert result["current_verified"] is False
    assert result["reachability"] == "UNKNOWN"
    assert result["candidate_edges"][0]["typed_edge"]["trading_authority_implied"] is False
    assert result["candidate_edges"][0]["reachability"] == "UNKNOWN"


def test_missing_symbol_is_rejected() -> None:
    result = build_code_reference_prelude_v1(
        declared_commit_sha=AUTHORIZED_COMMIT,
        declared_tree_sha=AUTHORIZED_TREE,
        nodes=_nodes(),
        references=[_reference(symbol="not_in_this_line")],
    )

    assert result["ok"] is False
    assert result["candidate_edges"] == []
    assert result["reasons"] == ["evidence_symbol_absent:edge-1"]


def test_authority_edge_is_rejected() -> None:
    result = build_code_reference_prelude_v1(
        declared_commit_sha=AUTHORIZED_COMMIT,
        declared_tree_sha=AUTHORIZED_TREE,
        nodes=_nodes(),
        references=[_reference(edge_type="AUTHORIZES")],
    )

    assert result["ok"] is False
    assert "authority_implied:edge-1" in result["reasons"]
    assert result["candidate_edges"] == []
