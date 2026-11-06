"""Symbol-endpoint resolver: pinned citations, no membership, no ratification."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops.mv2_outer_boundary_projector_v1.constants_v1 import (
    FORBIDDEN_BOUNDARY_STATUSES,
    RESOLVER_ID,
)
from scripts.ops.mv2_outer_boundary_projector_v1.countercheck_v1 import (
    scan_package_imports_v1,
    scan_reverse_importers_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.input_contract_v1 import (
    ProjectorFailClosedV1,
    ProjectorRequestV1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.run_v1 import (
    run_mv2_outer_boundary_projector_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.source_pins_v1 import validate_pin_v1
from scripts.ops.mv2_outer_boundary_projector_v1.symbol_endpoint_resolver_v1 import (
    CYCLE,
    DP_EXPORT,
    FAMILY,
    G17,
    resolve_symbol_endpoints_v1,
)

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "scripts" / "ops" / "mv2_outer_boundary_projector_v1"
PIN_COMMIT = "7628005ae495c115ff341d32fa932b7f4642f456"
PIN_TREE = "e652f8d7b86c469311a068c34b0fb3f708c87d73"
RESOLVER_SOURCE = PACKAGE / "symbol_endpoint_resolver_v1.py"


def _flow_mapper(edge: dict[str, object]) -> tuple[str | None, str]:
    mapped = {
        "DATA_FLOW": "PRODUCES",
        "DECISION_FLOW": "HANDOFF",
        "CONSTRAINT_FLOW": "BLOCKS",
        "EVIDENCE_FLOW": "OBSERVES",
    }.get(str(edge.get("flow_type") or ""))
    return mapped, "TEST_MAPPER"


def _resolve(
    texts: dict[str, str],
    edges: list[dict[str, object]] | None = None,
    candidates: list[dict[str, object]] | None = None,
    ignored: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return resolve_symbol_endpoints_v1(
        commit=PIN_COMMIT,
        tree=PIN_TREE,
        texts=texts,
        census_edges=list(edges or []),
        candidates=list(candidates or []),
        flow_mapper=_flow_mapper,
        ignored_observations=list(ignored or []),
        causal_graph_status="NOT_MATERIALIZED",
    )


def _by_id(records: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(item["relation_id"]): item for item in records}


def test_wrong_tree_fails_closed_before_resolution() -> None:
    with pytest.raises(ProjectorFailClosedV1) as caught:
        validate_pin_v1(REPO, PIN_COMMIT, "1" * 40)
    assert caught.value.code == "TREE_MISMATCH"


def test_ambiguous_symbol_is_not_a_proven_relation() -> None:
    texts = {
        G17: (
            "def apply_current_productive_g17_typed_vol_cmc_bind_v1(\n"
            "def apply_current_productive_g17_typed_vol_cmc_bind_v1(\n"
        ),
        CYCLE: (
            "apply_current_productive_g17_typed_vol_cmc_bind_v1(\n"
            "market_context = g17_cmc_bind.context\n"
            "canonical_market_context=market_context\n"
        ),
    }
    report = _resolve(
        texts,
        edges=[
            {
                "edge_id": "g17_bind_into_mv2_cycle",
                "original_flow_type": "DATA_FLOW",
                "observed_direction": "INBOUND",
                "source_id": "pkg:g17",
                "target_id": "pkg:trading",
            }
        ],
    )
    record = _by_id(report["UNRESOLVED_SYMBOL_ENDPOINTS"])["g17_bind_into_mv2_cycle"]
    assert record["binding_status"] == "AMBIGUOUS_SYMBOL"
    assert record["endpoint_classification"] == "UNRESOLVED_EDGE"
    assert report["PROVEN_SYMBOL_RELATIONS"] == []


def test_missing_producer_binding_stays_unresolved() -> None:
    texts = {
        G17: "def apply_current_productive_g17_typed_vol_cmc_bind_v1(\n",
        CYCLE: "",
    }
    report = _resolve(
        texts,
        edges=[
            {
                "edge_id": "g17_bind_into_mv2_cycle",
                "original_flow_type": "DATA_FLOW",
                "observed_direction": "INBOUND",
                "source_id": "pkg:g17",
                "target_id": "pkg:trading",
            }
        ],
    )
    record = _by_id(report["UNRESOLVED_SYMBOL_ENDPOINTS"])["g17_bind_into_mv2_cycle"]
    assert record["binding_status"] == "MISSING_BINDING"
    assert record["relation_class"] == "UNKNOWN"


def test_resolved_symbols_with_unknown_class_are_not_proven() -> None:
    texts = {
        FAMILY: (
            "def export_families_after_runtime_commit_v1(\n"
            "export_double_play_display_to_archive_sibling_from_replay_commit_v1(\n"
        ),
        DP_EXPORT: "def export_double_play_display_to_archive_sibling_from_replay_commit_v1(\n",
    }
    report = _resolve(
        texts,
        edges=[
            {
                "edge_id": "archive_smoke_host_to_double_play_exporter",
                "original_flow_type": "EVIDENCE_FLOW",
                "observed_direction": "OUTBOUND",
                "source_id": "pkg:archive",
                "target_id": "pkg:double_play_exporter",
            }
        ],
    )
    record = _by_id(report["RESOLVED_SYMBOL_ENDPOINTS"])[
        "archive_smoke_host_to_double_play_exporter"
    ]
    assert record["relation_class"] == "UNKNOWN"
    assert record["class_derived_from_ghv_type"] is False
    assert record["ghv_edge_type"] == "OBSERVES"
    assert record["original_flow_type"] == "EVIDENCE_FLOW"
    assert report["PROVEN_SYMBOL_RELATIONS"] == []


def test_package_census_and_neighborhood_do_not_grant_membership() -> None:
    report = _resolve(
        {},
        candidates=[
            {
                "component_id": "census:SO-SRC-PKG:trading",
                "basis": "CENSUS_TAXONOMY",
                "classification": "POSSIBLE_MV2_MEMBER_UNCLASSIFIED",
            },
            {
                "component_id": "name:master_v2_neighbor",
                "basis": "GRAPH_NEIGHBORHOOD",
                "classification": "POSSIBLE_MV2_MEMBER_UNCLASSIFIED",
            },
        ],
        ignored=[{"edge_id": "historical-neighbor", "kind": "HISTORICAL_GRAPH"}],
    )
    unresolved = _by_id(report["UNRESOLVED_SYMBOL_ENDPOINTS"])
    package = unresolved["candidate:census:SO-SRC-PKG:trading"]
    neighbor = unresolved["candidate:name:master_v2_neighbor"]
    assert package["endpoint_classification"] == "UNRESOLVED_COMPONENT"
    assert package["membership_granted"] is False
    assert neighbor["membership_granted"] is False
    assert neighbor["membership_basis"] == "GRAPH_NEIGHBORHOOD"
    assert "historical-neighbor" not in {
        item["relation_id"] for item in report["PROVEN_SYMBOL_RELATIONS"]
    }
    assert "historical-neighbor" not in {
        item["relation_id"] for item in report["RESOLVED_SYMBOL_ENDPOINTS"]
    }


def test_original_flow_is_kept_beside_the_ghv_type() -> None:
    texts = {
        G17: "def apply_current_productive_g17_typed_vol_cmc_bind_v1(\n",
        CYCLE: (
            "apply_current_productive_g17_typed_vol_cmc_bind_v1(\n"
            "market_context = g17_cmc_bind.context\n"
            "canonical_market_context=market_context\n"
        ),
    }
    report = _resolve(
        texts,
        edges=[
            {
                "edge_id": "g17_bind_into_mv2_cycle",
                "original_flow_type": "DATA_FLOW",
                "observed_direction": "INBOUND",
                "source_id": "pkg:g17",
                "target_id": "pkg:trading",
            }
        ],
    )
    record = _by_id(report["PROVEN_SYMBOL_RELATIONS"])["g17_bind_into_mv2_cycle"]
    assert record["original_flow_type"] == "DATA_FLOW"
    assert record["relation_class"] == "DATA"
    assert record["ghv_edge_type"] == "PRODUCES"
    assert record["ghv_edge_type_replaces_flow"] is False
    assert record["class_derived_from_census_flow"] is False
    assert record["synthetic"] is False
    assert record["universe_ratification"] is False
    assert report["ORIGINAL_FLOW_PRESERVATION"]["synthetic_edge_count"] == 0


def test_unlisted_text_cannot_create_a_relation() -> None:
    report = _resolve({"src/trading/not_a_probe.py": "def invented_symbol_v1(\n"})
    paths = {
        item.get("producer_path")
        for item in report["RESOLVED_SYMBOL_ENDPOINTS"]
        if item.get("producer_path")
    }
    assert "src/trading/not_a_probe.py" not in paths
    assert report["PROVEN_SYMBOL_RELATIONS"] == []


def test_resolver_output_is_deterministic() -> None:
    first = _resolve({})
    second = _resolve({})
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["RESOLVER_ID"] == RESOLVER_ID


def test_resolver_does_not_import_productive_modules_or_ghosv() -> None:
    source = RESOLVER_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    assert all("trading" not in module for module in modules)
    assert all("execution" not in module for module in modules)
    assert all("risk" not in module for module in modules)
    assert all("ghosv_bounded_context_v1" not in module for module in modules)
    assert "write_text(" not in source
    assert "run_causal_integration_v1(" not in source
    assert scan_reverse_importers_v1(REPO, PACKAGE) == []
    assert all(
        "ghosv_bounded_context_v1" not in module for module in scan_package_imports_v1(PACKAGE)
    )


def test_pinned_run_reproduces_symbol_relations_without_ratification() -> None:
    report = run_mv2_outer_boundary_projector_v1(
        ProjectorRequestV1(commit=PIN_COMMIT, tree=PIN_TREE),
        repo_root=REPO,
    )
    assert report["RESOLVER_ID"] == RESOLVER_ID
    assert report["BOUNDARY_VERIFICATION_STATUS"] == "BLOCKED_BY_EVIDENCE"
    assert report["BOUNDARY_VERIFICATION_STATUS"] not in FORBIDDEN_BOUNDARY_STATUSES
    assert report["UNIVERSE_RATIFICATION"] is False
    assert report["INBOUND_BOUNDARY_EDGES"] == []
    assert report["OUTBOUND_BOUNDARY_EDGES"] == []
    proven = report["PROVEN_SYMBOL_RELATIONS"]
    assert [item["relation_id"] for item in proven] == [
        "binding_to_mv2",
        "g17_bind_into_mv2_cycle",
        "learning_capture",
        "partner:crs",
        "safety_signals_into_integrated_replay",
    ]
    by_proven = _by_id(proven)
    g17 = by_proven["g17_bind_into_mv2_cycle"]
    assert g17["original_flow_type"] == "DATA_FLOW"
    assert g17["relation_class"] == "DATA"
    assert g17["ghv_edge_type"] == "PRODUCES"
    assert g17["ghv_edge_type_replaces_flow"] is False
    safety = by_proven["safety_signals_into_integrated_replay"]
    assert safety["original_flow_type"] == "CONSTRAINT_FLOW"
    assert safety["relation_class"] == "SAFETY"
    assert safety["ghv_edge_type"] == "BLOCKS"
    assert safety["census_source_status"] == "WIDERLEGT"
    assert safety["producer_symbol"] == "evaluate_host_exit_policy_producers_v1"
    learning = by_proven["learning_capture"]
    assert learning["original_flow_type"] == "EVIDENCE_FLOW"
    assert learning["relation_class"] == "EVIDENCE"
    assert learning["ghv_edge_type"] == "OBSERVES"
    assert learning["uncertainty"] == "CONDITIONAL_ON_DDO_LEDGER_PATH"
    binding = by_proven["binding_to_mv2"]
    assert binding["original_flow_type"] == "DECISION_FLOW"
    assert binding["relation_class"] == "DATA"
    assert binding["ghv_edge_type"] == "HANDOFF"
    crs = by_proven["partner:crs"]
    assert crs["census_edge_id"] is None
    assert crs["relation_class"] == "DATA"
    assert crs["synthetic"] is False
    resolved = _by_id(report["RESOLVED_SYMBOL_ENDPOINTS"])
    archive = resolved["archive_smoke_host_to_double_play_exporter"]
    assert archive["relation_class"] == "UNKNOWN"
    assert archive["direct_replay_relation"] is False
    reconciliation = resolved["partner:reconciliation"]
    assert reconciliation["relation_class"] == "UNKNOWN"
    unresolved = _by_id(report["UNRESOLVED_SYMBOL_ENDPOINTS"])
    assert unresolved["CE-004"]["counterevidence_status"] == "WIDERLEGT"
    assert unresolved["fa_compose_mv2_dp_handoff_join"]["counterevidence_status"] == "WIDERLEGT"
    assert unresolved["governed_cycle_t2_mv2_stack"]["binding_status"] == "MISSING_BINDING"
    trading = unresolved["candidate:census:SO-SRC-PKG:trading"]
    assert trading["endpoint_classification"] == "UNRESOLVED_COMPONENT"
    assert trading["membership_granted"] is False
    role = unresolved["candidate:role:DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA"]
    assert role["membership_granted"] is False
    assert report["ORIGINAL_FLOW_PRESERVATION"]["historical_graph_edges_admitted"] == 0
    assert report["ORIGINAL_FLOW_PRESERVATION"]["synthetic_edge_count"] == 0
    assert [item["component_id"] for item in report["PROVEN_MEMBERS"]] == [
        "symbol:trading.master_v2.integrated_offline_trading_logic_replay_v1."
        "run_integrated_offline_trading_logic_replay_v1"
    ]
    causal = next(
        item for item in report["SOURCE_PROVENANCE"] if item["source_id"] == "S_CAUSAL_INTEGRATION"
    )
    assert causal["invoked"] is False
    assert causal["current_causal_graph"] == "NOT_MATERIALIZED"
    ghosv = next(
        item for item in report["SOURCE_PROVENANCE"] if item["source_id"] == "S_GHOSV_EXECUTION"
    )
    assert ghosv["imported"] is False
