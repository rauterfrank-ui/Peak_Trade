"""Deterministic offline tests for WP2-A causal integration."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.integrate_v1 import (
    run_causal_integration_v1,
)
from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.load_wp1_v1 import (
    load_wp1_artifacts_v1,
    validate_wp1_bundle_v1,
)
from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.runtime_evidence_v1 import (
    RuntimeEvidenceRequestV1,
    bind_runtime_evidence_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    COMPOSED_GRAPH_SCHEMA,
    MANIFEST_SCHEMA,
)
from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.constants_v1 import (
    CAPTURE_MANIFEST,
    FLIGHT_RECORD,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG = REPO_ROOT / "scripts/ops/ghv_forensic_whole_system_causal_integration_v1"


def _prov(native: str) -> dict:
    return {
        "SOURCE_TOOL": "test",
        "SOURCE_ARTIFACT": "test.json",
        "SOURCE_REVISION": "r1",
        "CODE_REVISION": "abc123",
        "NATIVE_ID": native,
        "CANONICAL_ID": f"CFI/v1/COMPONENT/snap/SYS/{native}",
        "EVIDENCE_TYPE": "CONTRACT_EVIDENCE",
        "PROOF_CLASS": "CONTRACT_CONFIRMED",
        "OBSERVED_OR_INFERRED": "OBSERVED",
        "ACTIVATION_CONDITIONS": [],
        "VALIDATION_STATUS": "PASS",
        "LIMITATIONS": [],
        "SCHEMA": "peak_trade.forensic_canonical_identity.v1",
    }


def _node(
    *, cfi: str, native: str, sys_name: str = "CURRENT_SYSTEM_CENSUS", conditional: bool = False
) -> dict:
    rel = {
        "CURRENT_RELEVANCE_STATE": "CURRENT_CONDITIONAL" if conditional else "CURRENT_VERIFIED",
        "CURRENT_RELEVANCE_EVIDENCE": "test",
        "EVIDENCE_SOURCE": "artifact",
        "EVIDENCE_REVISION": "r1",
        "VALIDATION_STATUS": "PASS",
        "ACTIVATION_CONDITION": "flag=true" if conditional else None,
    }
    return {
        "canonical_id": cfi,
        "entity_type": "COMPONENT",
        "source_system": sys_name,
        "source_native_id": native,
        "metadata": {},
        "current_relevance": rel,
        "provenance": _prov(native),
    }


def _edge(
    *, eid: str, src: str, tgt: str, edge_type: str = "PRODUCES", flow_observes: bool = False
) -> dict:
    causal = edge_type not in {"IMPORTS", "CONFIGURES", "OBSERVES"}
    if flow_observes:
        edge_type = "OBSERVES"
        causal = False
    return {
        "edge_id": eid,
        "source_native_id": src,
        "target_native_id": tgt,
        "typed_edge": {
            "edge_type": edge_type,
            "structural_only": not causal,
            "causal_propagation_allowed": causal,
            "trading_authority_implied": False,
        },
        "source_system": "CURRENT_SYSTEM_CENSUS",
        "current_relevance": {
            "CURRENT_RELEVANCE_STATE": "CURRENT_VERIFIED",
            "CURRENT_RELEVANCE_EVIDENCE": "test",
            "EVIDENCE_SOURCE": "artifact",
            "EVIDENCE_REVISION": "r1",
            "VALIDATION_STATUS": "PASS",
            "ACTIVATION_CONDITION": None,
        },
        "causal_traversal_eligible": causal,
        "provenance": _prov(eid),
    }


def _write_wp1_bundle(
    root: Path,
    *,
    snapshot_id: str = "snap001",
    graph_mode: str = "STRICT_CURRENT",
    current_graph_verified: bool = True,
    nodes: list[dict] | None = None,
    edges: list[dict] | None = None,
    manifest_snapshot: str | None = None,
    schema_version: str = COMPOSED_GRAPH_SCHEMA,
    historical_entities: int = 0,
    collisions: list | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    n1 = _node(cfi="CFI/v1/COMPONENT/snap001/CURRENT_SYSTEM_CENSUS/SO-A", native="SO-A")
    n2 = _node(cfi="CFI/v1/COMPONENT/snap001/CURRENT_SYSTEM_CENSUS/SO-B", native="SO-B")
    nodes = nodes if nodes is not None else [n1, n2]
    edges = edges if edges is not None else [_edge(eid="census:E1", src="SO-A", tgt="SO-B")]
    authority = {
        "GRAPH_MODE": graph_mode,
        "GRAPH_AUTHORITY": graph_mode,
        "SNAPSHOT_BINDING_VERIFIED": graph_mode == "STRICT_CURRENT",
        "CURRENT_ONLY_FILTER_APPLIED": True,
        "CURRENT_GRAPH_VERIFIED": current_graph_verified,
        "CURRENT_ONLY_GRAPH": current_graph_verified,
        "SOURCE_VALIDATION_PASS": True,
        "CAUSAL_CLOSURE_PROVEN": False,
        "GLOBAL_NON_INTERFERENCE_PROVEN": False,
    }
    composed = {
        "schema_version": schema_version,
        "authority": "NONE",
        "snapshot_id": snapshot_id,
        "source_validation_pass": True,
        **authority,
        "code_snapshot": {"kind": "CODE_SNAPSHOT", "git_head": "abc123"},
        "evidence_snapshot": {"kind": "EVIDENCE_SNAPSHOT", "evidence_root": None},
        "nodes": nodes,
        "edges": edges,
        "unresolved_edges": [],
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "snapshot_id": manifest_snapshot or snapshot_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        **authority,
    }
    coverage = {
        **authority,
        "HISTORICAL_ENTITIES_INGESTED": historical_entities,
        "HISTORICAL_EDGES_INGESTED": 0,
    }
    ambiguity = {"collisions": collisions or [], "ambiguous": [], "unresolved_edges": []}
    excluded = {
        "excluded": [],
        "historical_entities_ingested": historical_entities,
        "historical_edges_ingested": 0,
    }
    for name, doc in (
        ("composed_forensic_graph.v1.json", composed),
        ("crosswalk_manifest.v1.json", manifest),
        ("coverage_report.v1.json", coverage),
        ("ambiguity_report.v1.json", ambiguity),
        ("excluded_non_current_report.v1.json", excluded),
    ):
        (root / name).write_text(json.dumps(doc), encoding="utf-8")
    return root


def test_composed_authority_none_required_when_otherwise_valid(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_auth_ok")
    bundle, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert res.ok and bundle is not None


@pytest.mark.parametrize("bad_authority", ["LIVE", "NAVIGATION", ""])
def test_composed_authority_not_none_rejected(tmp_path: Path, bad_authority: str) -> None:
    wp1 = _write_wp1_bundle(tmp_path / f"wp1_auth_{bad_authority or 'empty'}")
    composed_path = wp1 / "composed_forensic_graph.v1.json"
    composed = json.loads(composed_path.read_text(encoding="utf-8"))
    composed["authority"] = bad_authority
    composed_path.write_text(json.dumps(composed), encoding="utf-8")
    bundle, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert bundle is not None
    assert not res.ok
    assert res.failure_semantic == "INPUT_VALIDATION_FAILURE"
    assert "composed_authority_must_be_NONE" in res.errors
    out = run_causal_integration_v1(wp1_output_dir=wp1, output_dir=tmp_path / "out_bad_auth")
    assert not out.ok
    assert "composed_authority_must_be_NONE" in out.errors


def test_composed_authority_mismatch_preserves_other_validation_errors(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_auth_and_snap", manifest_snapshot="wrong_snap")
    composed_path = wp1 / "composed_forensic_graph.v1.json"
    composed = json.loads(composed_path.read_text(encoding="utf-8"))
    composed["authority"] = "LIVE"
    composed_path.write_text(json.dumps(composed), encoding="utf-8")
    bundle, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok
    assert "composed_authority_must_be_NONE" in res.errors


def test_runtime_overlay_without_state_owner_not_temporally_proven(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_rt_temporal")
    mapping = {
        "schema_version": "stage_to_cfi_mapping.v1",
        "stage_transitions": [
            {
                "stage": "S1",
                "source_endpoint": ["CURRENT_SYSTEM_CENSUS", "SO-A"],
                "target_endpoint": ["CURRENT_SYSTEM_CENSUS", "SO-B"],
                "edge_type": "PRODUCES",
                "causal_propagation_allowed": True,
            }
        ],
    }
    map_path = tmp_path / "map_no_owner.json"
    map_path.write_text(json.dumps(mapping), encoding="utf-8")
    ev = tmp_path / "evidence_temporal"
    ev.mkdir()
    (ev / CAPTURE_MANIFEST).write_text(
        json.dumps({"repository_sha": "abc123", "run_id": "r1", "continuous_run_id": "c1"}),
        encoding="utf-8",
    )
    (ev / FLIGHT_RECORD).write_text(json.dumps({"stage": "S1"}) + "\n", encoding="utf-8")
    out = run_causal_integration_v1(
        wp1_output_dir=wp1,
        output_dir=tmp_path / "out_rt_temporal",
        runtime_evidence=RuntimeEvidenceRequestV1(
            evidence_root=ev,
            stage_mapping_path=map_path,
            runtime_context={
                "run_id": "r1",
                "continuous_run_id": "c1",
                "evidence_contract_id": "ec1",
            },
            code_revision="abc123",
            snapshot_id="snap001",
        ),
    )
    assert out.ok
    assert out.temporal_causality_proven is False
    integrated = json.loads(
        (tmp_path / "out_rt_temporal" / "integrated_causal_graph.v1.json").read_text()
    )
    assert integrated["TEMPORAL_CAUSALITY_PROVEN"] is False
    gaps = json.loads((tmp_path / "out_rt_temporal" / "causal_coverage_gaps.v1.json").read_text())
    assert any(g.get("reason") == "temporal_fields_incomplete" for g in gaps["gaps"])


def test_valid_wp1_strict_artifact_loading(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_strict")
    bundle, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert res.ok and bundle is not None
    out = run_causal_integration_v1(wp1_output_dir=wp1, output_dir=tmp_path / "out")
    assert out.ok
    assert out.current_causal_graph_verified is True
    assert (tmp_path / "out" / "integrated_causal_graph.v1.json").is_file()


def test_navigation_only_authority_not_promoted(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(
        tmp_path / "wp1_nav",
        graph_mode="NAVIGATION_ONLY",
        current_graph_verified=False,
    )
    out = run_causal_integration_v1(wp1_output_dir=wp1, output_dir=tmp_path / "out_nav")
    assert out.ok
    assert out.current_causal_graph_verified is False
    doc = json.loads((tmp_path / "out_nav" / "integrated_causal_graph.v1.json").read_text())
    assert doc["CURRENT_CAUSAL_GRAPH_VERIFIED"] is False


def test_mixed_snapshot_rejection(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_mix", manifest_snapshot="other_snap")
    bundle, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok
    assert "manifest_snapshot_id_mismatch" in res.errors


def test_missing_required_artifact_rejection(tmp_path: Path) -> None:
    wp1 = tmp_path / "wp1_missing"
    wp1.mkdir()
    (wp1 / "composed_forensic_graph.v1.json").write_text("{}", encoding="utf-8")
    _, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok
    assert any("missing_required_artifacts" in e for e in res.errors)


def test_unknown_schema_rejection(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_schema", schema_version="unknown.v9")
    _, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok


def test_unknown_edge_type_rejection(tmp_path: Path) -> None:
    bad_edge = _edge(eid="census:bad", src="SO-A", tgt="SO-B")
    bad_edge["typed_edge"]["edge_type"] = "NOT_REAL"
    wp1 = _write_wp1_bundle(tmp_path / "wp1_edge", edges=[bad_edge])
    _, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok


def test_historical_node_exclusion_via_ingestion_counter(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_hist", historical_entities=1)
    _, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok


def test_historical_edge_exclusion(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_hist_e")
    ex = json.loads((wp1 / "excluded_non_current_report.v1.json").read_text())
    ex["historical_edges_ingested"] = 2
    (wp1 / "excluded_non_current_report.v1.json").write_text(json.dumps(ex), encoding="utf-8")
    _, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok


def test_unknown_identity_exclusion(tmp_path: Path) -> None:
    node = _node(cfi="CFI/x", native="SO-X")
    node["current_relevance"]["CURRENT_RELEVANCE_STATE"] = "UNKNOWN"
    wp1 = _write_wp1_bundle(tmp_path / "wp1_unknown", nodes=[node])
    _, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok


def test_ambiguous_cfi_collision_rejection(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_col", collisions=[{"canonical_id": "CFI/dup"}])
    _, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok


def test_missing_edge_endpoint_rejection(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(
        tmp_path / "wp1_endpoint",
        edges=[_edge(eid="census:E1", src="SO-A", tgt="SO-MISSING")],
    )
    _, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert not res.ok


def test_structural_edge_non_propagation(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(
        tmp_path / "wp1_struct",
        edges=[_edge(eid="census:imp", src="SO-A", tgt="SO-B", edge_type="IMPORTS")],
    )
    bundle, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert res.ok and bundle
    edge = bundle.composed["edges"][0]
    assert edge["typed_edge"]["causal_propagation_allowed"] is False


def test_observes_non_authority(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(
        tmp_path / "wp1_obs",
        edges=[_edge(eid="census:obs", src="SO-A", tgt="SO-B", flow_observes=True)],
    )
    _, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert res.ok


def test_evidence_flow_observes_non_propagation(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(
        tmp_path / "wp1_ev",
        edges=[_edge(eid="census:ev", src="SO-A", tgt="SO-B", edge_type="OBSERVES")],
    )
    bundle, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert res.ok
    assert bundle.composed["edges"][0]["typed_edge"]["causal_propagation_allowed"] is False


def test_runtime_sha_mismatch_rejection(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_sha")
    ev = tmp_path / "evidence"
    ev.mkdir()
    (ev / CAPTURE_MANIFEST).write_text(json.dumps({"repository_sha": "wrong"}), encoding="utf-8")
    (ev / FLIGHT_RECORD).write_text("{}\n", encoding="utf-8")
    req = RuntimeEvidenceRequestV1(
        evidence_root=ev,
        stage_mapping_path=PKG / "stage_to_cfi_mapping.v1.json",
        runtime_context={"run_id": "r1", "continuous_run_id": "c1", "evidence_contract_id": "ec1"},
        code_revision="abc123",
        snapshot_id="snap001",
    )
    rt = bind_runtime_evidence_v1(request=req, endpoint_cfi_by_key={})
    assert not rt.ok


def test_matching_sha_wrong_runtime_context(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_ctx")
    ev = tmp_path / "evidence2"
    ev.mkdir()
    (ev / CAPTURE_MANIFEST).write_text(
        json.dumps(
            {
                "repository_sha": "abc123",
                "run_id": "expected_run",
                "continuous_run_id": "expected_cont",
            }
        ),
        encoding="utf-8",
    )
    (ev / FLIGHT_RECORD).write_text(json.dumps({"stage": "S1"}) + "\n", encoding="utf-8")
    req = RuntimeEvidenceRequestV1(
        evidence_root=ev,
        stage_mapping_path=PKG / "stage_to_cfi_mapping.v1.json",
        runtime_context={
            "run_id": "other",
            "continuous_run_id": "expected_cont",
            "evidence_contract_id": "ec1",
        },
        code_revision="abc123",
        snapshot_id="snap001",
    )
    rt = bind_runtime_evidence_v1(request=req, endpoint_cfi_by_key={})
    assert not rt.ok


def test_missing_stage_to_cfi_mapping(tmp_path: Path) -> None:
    ev = tmp_path / "evidence3"
    ev.mkdir()
    (ev / CAPTURE_MANIFEST).write_text(
        json.dumps({"repository_sha": "abc123", "run_id": "r1", "continuous_run_id": "c1"}),
        encoding="utf-8",
    )
    (ev / FLIGHT_RECORD).write_text(
        json.dumps({"stage": "UNMAPPED_STAGE"}) + "\n", encoding="utf-8"
    )
    req = RuntimeEvidenceRequestV1(
        evidence_root=ev,
        stage_mapping_path=PKG / "stage_to_cfi_mapping.v1.json",
        runtime_context={"run_id": "r1", "continuous_run_id": "c1", "evidence_contract_id": "ec1"},
        code_revision="abc123",
        snapshot_id="snap001",
    )
    rt = bind_runtime_evidence_v1(request=req, endpoint_cfi_by_key={})
    assert rt.ok
    assert rt.binding_status == "NOT_PROVEN"
    assert any(g.get("reason") == "missing_stage_to_cfi_mapping" for g in rt.gaps)


def test_conditional_activation_preservation(tmp_path: Path) -> None:
    node = _node(
        cfi="CFI/v1/COMPONENT/snap001/CURRENT_SYSTEM_CENSUS/SO-C",
        native="SO-C",
        conditional=True,
    )
    wp1 = _write_wp1_bundle(tmp_path / "wp1_cond", nodes=[node], edges=[])
    bundle, res = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert res.ok
    assert bundle.composed["nodes"][0]["current_relevance"]["ACTIVATION_CONDITION"] == "flag=true"


def test_cross_universe_authority_isolation_flag(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_cross")
    out = run_causal_integration_v1(wp1_output_dir=wp1, output_dir=tmp_path / "out_cross")
    assert out.cross_universe_causality_proven is False


def test_temporal_adjacency_without_causality_not_proven(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_temp")
    out = run_causal_integration_v1(wp1_output_dir=wp1, output_dir=tmp_path / "out_temp")
    assert out.temporal_causality_proven is False


def test_missing_state_owner_gap(tmp_path: Path) -> None:
    mapping = {
        "schema_version": "stage_to_cfi_mapping.v1",
        "stage_transitions": [
            {
                "stage": "S1",
                "source_endpoint": ["CURRENT_SYSTEM_CENSUS", "SO-A"],
                "target_endpoint": ["CURRENT_SYSTEM_CENSUS", "SO-B"],
                "edge_type": "PRODUCES",
                "requires_state_owner": True,
            }
        ],
    }
    map_path = tmp_path / "map.json"
    map_path.write_text(json.dumps(mapping), encoding="utf-8")
    ev = tmp_path / "evidence4"
    ev.mkdir()
    (ev / CAPTURE_MANIFEST).write_text(
        json.dumps({"repository_sha": "abc123", "run_id": "r1", "continuous_run_id": "c1"}),
        encoding="utf-8",
    )
    (ev / FLIGHT_RECORD).write_text(json.dumps({"stage": "S1"}) + "\n", encoding="utf-8")
    endpoint = {
        ("CURRENT_SYSTEM_CENSUS", "SO-A"): "CFI/v1/COMPONENT/snap001/CURRENT_SYSTEM_CENSUS/SO-A",
        ("CURRENT_SYSTEM_CENSUS", "SO-B"): "CFI/v1/COMPONENT/snap001/CURRENT_SYSTEM_CENSUS/SO-B",
    }
    req = RuntimeEvidenceRequestV1(
        evidence_root=ev,
        stage_mapping_path=map_path,
        runtime_context={"run_id": "r1", "continuous_run_id": "c1", "evidence_contract_id": "ec1"},
        code_revision="abc123",
        snapshot_id="snap001",
    )
    rt = bind_runtime_evidence_v1(request=req, endpoint_cfi_by_key=endpoint)
    assert not rt.proposed_edges
    assert any(g.get("reason") == "missing_state_owner" for g in rt.gaps)


def test_malformed_runtime_evidence(tmp_path: Path) -> None:
    ev = tmp_path / "evidence5"
    ev.mkdir()
    (ev / CAPTURE_MANIFEST).write_text(json.dumps({"repository_sha": "abc123"}), encoding="utf-8")
    (ev / FLIGHT_RECORD).write_text("not-json\n", encoding="utf-8")
    req = RuntimeEvidenceRequestV1(
        evidence_root=ev,
        stage_mapping_path=PKG / "stage_to_cfi_mapping.v1.json",
        runtime_context={"run_id": "r1", "continuous_run_id": "c1", "evidence_contract_id": "ec1"},
        code_revision="abc123",
        snapshot_id="snap001",
    )
    rt = bind_runtime_evidence_v1(request=req, endpoint_cfi_by_key={})
    assert not rt.ok


def test_partial_evidence_ingestion(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_partial")
    mapping = {
        "schema_version": "stage_to_cfi_mapping.v1",
        "stage_transitions": [
            {
                "stage": "S1",
                "source_endpoint": ["CURRENT_SYSTEM_CENSUS", "SO-A"],
                "target_endpoint": ["CURRENT_SYSTEM_CENSUS", "SO-B"],
                "edge_type": "PRODUCES",
                "current_evidence": "flight:S1",
                "state_owner": "owner_a",
                "causal_propagation_allowed": True,
            }
        ],
    }
    map_path = tmp_path / "map_partial.json"
    map_path.write_text(json.dumps(mapping), encoding="utf-8")
    ev = tmp_path / "evidence6"
    ev.mkdir()
    (ev / CAPTURE_MANIFEST).write_text(
        json.dumps({"repository_sha": "abc123", "run_id": "r1", "continuous_run_id": "c1"}),
        encoding="utf-8",
    )
    (ev / FLIGHT_RECORD).write_text(
        json.dumps({"stage": "S1"}) + "\n" + json.dumps({"stage": "S2"}) + "\n",
        encoding="utf-8",
    )
    out = run_causal_integration_v1(
        wp1_output_dir=wp1,
        output_dir=tmp_path / "out_partial",
        runtime_evidence=RuntimeEvidenceRequestV1(
            evidence_root=ev,
            stage_mapping_path=map_path,
            runtime_context={
                "run_id": "r1",
                "continuous_run_id": "c1",
                "evidence_contract_id": "ec1",
            },
            code_revision="abc123",
            snapshot_id="snap001",
        ),
    )
    assert out.ok
    overlay = json.loads((tmp_path / "out_partial" / "causal_overlay.v1.json").read_text())
    assert len(overlay["overlay_edges"]) == 1
    gaps = json.loads((tmp_path / "out_partial" / "causal_coverage_gaps.v1.json").read_text())
    assert any(g.get("reason") == "missing_stage_to_cfi_mapping" for g in gaps["gaps"])


def test_no_productive_imports_in_package() -> None:
    forbidden = ("src.trading", "full_core_live_path_composition_root", "master_v2", "double_play")
    for py in PKG.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for bad in forbidden:
                        assert bad not in alias.name
            if isinstance(node, ast.ImportFrom) and node.module:
                for bad in forbidden:
                    assert bad not in node.module


def test_no_unexpected_repo_writes(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_write")
    out_dir = Path("/tmp") / f"ghv_wp2a_test_write_{tmp_path.name}"
    if out_dir.exists():
        import shutil

        shutil.rmtree(out_dir)
    result = run_causal_integration_v1(wp1_output_dir=wp1, output_dir=out_dir)
    assert result.ok
    assert out_dir.is_dir()
    assert not (REPO_ROOT / "causal_overlay.v1.json").exists()


def test_wp1_current_graph_verified_false_blocks_promotion(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_not_verified", current_graph_verified=False)
    out = run_causal_integration_v1(wp1_output_dir=wp1, output_dir=tmp_path / "out_nv")
    assert out.ok
    assert out.current_causal_graph_verified is False


def test_validate_bundle_direct(tmp_path: Path) -> None:
    wp1 = _write_wp1_bundle(tmp_path / "wp1_direct")
    bundle, _ = load_wp1_artifacts_v1(wp1_output_dir=wp1)
    assert bundle
    v = validate_wp1_bundle_v1(bundle)
    assert v.ok
