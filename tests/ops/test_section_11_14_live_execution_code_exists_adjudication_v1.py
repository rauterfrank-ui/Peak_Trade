"""Predicate tests for LIVE_EXECUTION_CODE_EXISTS static adjudication."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_SUBMIT_TRANSPORT_PATH,
    FLATTEN_EXECUTE_PATH,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_PATH_REACHABLE,
    LIVE_FILL_OBSERVED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    LIVE_SUBMIT_ACK_OBSERVED,
    SP01_PATH,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.static_execution_graph_v1 import (
    canonical_graph_nodes_v1,
    evaluate_live_execution_code_exists_predicate_v1,
    file_presence_alone_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.static_field_adjudication_v1 import (
    adjudicate_static_fields_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_positive_current_main_satisfies_predicate() -> None:
    result = evaluate_live_execution_code_exists_predicate_v1(
        repo_root=REPO_ROOT,
        source_kind="REPOSITORY_IMPLEMENTATION",
    )
    assert result["admissible"] is True
    assert result["claim_value"] is True
    assert result["graph_status"] == "COMPLETE"
    assert result["missing_required_nodes"] == []
    assert LIVE_EXECUTION_CODE_EXISTS is True


def test_missing_component_rejects_predicate() -> None:
    nodes = list(canonical_graph_nodes_v1())
    required = next(node for node in nodes if node.required_for_predicate is True)
    nodes[nodes.index(required)] = replace(required, path="does/not/exist_live_exec.py")
    result = evaluate_live_execution_code_exists_predicate_v1(
        repo_root=REPO_ROOT,
        source_kind="REPOSITORY_IMPLEMENTATION",
        nodes=tuple(nodes),
    )
    assert result["admissible"] is False
    assert result["claim_value"] is False
    assert required.node_id in result["missing_required_nodes"]


def test_code_presence_alone_is_inadmissible() -> None:
    presence = file_presence_alone_v1(
        repo_root=REPO_ROOT,
        paths=(SP01_PATH, FLATTEN_EXECUTE_PATH, CANARY_SUBMIT_TRANSPORT_PATH),
    )
    assert presence["all_listed_files_exist"] is True
    assert presence["admissible_as_live_execution_code_exists"] is False
    assert presence["reason"] == "CODE_PRESENCE_ALONE_INADMISSIBLE"


def test_historical_only_required_node_rejects_predicate() -> None:
    nodes = list(canonical_graph_nodes_v1())
    required = next(node for node in nodes if node.required_for_predicate is True)
    nodes[nodes.index(required)] = replace(required, classification="HISTORICAL_ONLY")
    result = evaluate_live_execution_code_exists_predicate_v1(
        repo_root=REPO_ROOT,
        source_kind="REPOSITORY_IMPLEMENTATION",
        nodes=tuple(nodes),
    )
    assert result["admissible"] is False
    assert required.node_id in result["disallowed_required_nodes"]


def test_fixture_source_is_rejected() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
        evaluate_live_execution_code_exists_predicate_v1(
            repo_root=REPO_ROOT,
            source_kind="FIXTURE",
        )


def test_testnet_source_is_rejected() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
        evaluate_live_execution_code_exists_predicate_v1(
            repo_root=REPO_ROOT,
            source_kind="TESTNET",
        )


def test_simulation_source_is_rejected() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
        evaluate_live_execution_code_exists_predicate_v1(
            repo_root=REPO_ROOT,
            source_kind="SIMULATION",
        )


def test_true_does_not_imply_path_reachable_or_authorization_or_later_fields() -> None:
    proof = adjudicate_static_fields_v1(repo_root=REPO_ROOT)
    assert proof["LIVE_EXECUTION_CODE_EXISTS_VALUE"] is True
    assert proof["LIVE_EXECUTION_PATH_REACHABLE_VALUE"] is False
    assert LIVE_EXECUTION_PATH_REACHABLE is True
    assert LIVE_AUTHORIZED is False
    assert LIVE_PRIVATE_READ_ONLY_PROVEN is True
    assert LIVE_SUBMIT_ACK_OBSERVED is True
    assert LIVE_FILL_OBSERVED is False
