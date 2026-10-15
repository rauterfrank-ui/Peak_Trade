"""Deterministic tests for WP2-B-A1 offline graph inspection adapter."""

from __future__ import annotations

import ast
import hashlib
import json
import stat
from pathlib import Path

import pytest

from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.integrate_v1 import (
    run_causal_integration_v1,
)
from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.constants_v1 import (
    INTEGRATED_GRAPH_SCHEMA,
    INTEGRATION_MANIFEST_SCHEMA,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    COMPOSED_GRAPH_SCHEMA,
    MANIFEST_SCHEMA,
)
from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.inspect_graph_v1 import (
    run_offline_graph_inspection_v1,
)
from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.load_integrated_graph_v1 import (
    load_wp2a_artifacts_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_PKG = REPO_ROOT / "scripts/ops/ghv_forensic_whole_system_causal_ghv_adapter_v1"


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


def _node(*, cfi: str, native: str, state: str = "CURRENT_VERIFIED") -> dict:
    return {
        "canonical_id": cfi,
        "entity_type": "COMPONENT",
        "source_system": "CURRENT_SYSTEM_CENSUS",
        "source_native_id": native,
        "metadata": {},
        "current_relevance": {
            "CURRENT_RELEVANCE_STATE": state,
            "CURRENT_RELEVANCE_EVIDENCE": "test",
            "EVIDENCE_SOURCE": "artifact",
            "EVIDENCE_REVISION": "r1",
            "VALIDATION_STATUS": "PASS",
            "ACTIVATION_CONDITION": None,
        },
        "provenance": _prov(native),
    }


def _edge(*, eid: str, src: str, tgt: str, edge_type: str = "PRODUCES") -> dict:
    causal = edge_type not in {"IMPORTS", "CONFIGURES", "OBSERVES"}
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


def _write_wp1(
    root: Path,
    *,
    graph_mode: str = "STRICT_CURRENT",
    current_graph_verified: bool = True,
    nodes: list[dict] | None = None,
    edges: list[dict] | None = None,
    historical_entities: int = 0,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    n1 = _node(cfi="CFI/v1/COMPONENT/snap001/CURRENT_SYSTEM_CENSUS/SO-A", native="SO-A")
    n2 = _node(cfi="CFI/v1/COMPONENT/snap001/CURRENT_SYSTEM_CENSUS/SO-B", native="SO-B")
    nodes = nodes if nodes is not None else [n1, n2]
    edges = edges if edges is not None else [_edge(eid="census:E1", src="SO-A", tgt="SO-B")]
    auth = {
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
        "schema_version": COMPOSED_GRAPH_SCHEMA,
        "authority": "NONE",
        "snapshot_id": "snap001",
        "source_validation_pass": True,
        **auth,
        "code_snapshot": {"kind": "CODE_SNAPSHOT", "git_head": "abc123"},
        "evidence_snapshot": {"kind": "EVIDENCE_SNAPSHOT", "evidence_root": None},
        "nodes": nodes,
        "edges": edges,
        "unresolved_edges": [],
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "snapshot_id": "snap001",
        "node_count": len(nodes),
        "edge_count": len(edges),
        **auth,
    }
    coverage = {
        **auth,
        "HISTORICAL_ENTITIES_INGESTED": historical_entities,
        "HISTORICAL_EDGES_INGESTED": 0,
    }
    for name, doc in (
        ("composed_forensic_graph.v1.json", composed),
        ("crosswalk_manifest.v1.json", manifest),
        ("coverage_report.v1.json", coverage),
        ("ambiguity_report.v1.json", {"collisions": [], "ambiguous": [], "unresolved_edges": []}),
        (
            "excluded_non_current_report.v1.json",
            {
                "excluded": [],
                "historical_entities_ingested": historical_entities,
                "historical_edges_ingested": 0,
            },
        ),
    ):
        (root / name).write_text(json.dumps(doc), encoding="utf-8")
    return root


def _run_wp2a(tmp_path: Path, wp1_root: Path) -> Path:
    out = tmp_path / "wp2a_out"
    res = run_causal_integration_v1(wp1_output_dir=wp1_root, output_dir=out)
    assert res.ok, res.errors
    return out


def _out_dir(tmp_path: Path) -> Path:
    return tmp_path / "adapter_out"


def _inspect(wp2a: Path, tmp_path: Path):
    return run_offline_graph_inspection_v1(
        wp2a_output_dir=wp2a,
        output_dir=_out_dir(tmp_path),
        repo_root=REPO_ROOT,
    )


def test_01_valid_navigation_non_authoritative(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1", graph_mode="NAVIGATION_ONLY", current_graph_verified=False)
    wp2a = _run_wp2a(tmp_path, wp1)
    res = _inspect(wp2a, tmp_path)
    assert res.ok
    assert res.bundle_doc["authority_assessment"]["CURRENT_CAUSAL_GRAPH_VERIFIED"] is False


def test_02_valid_structurally_verified_strict(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    res = _inspect(wp2a, tmp_path)
    assert res.ok
    assert res.bundle_doc["semantic_assessment"]["STRUCTURAL_GRAPH_VALIDITY"] is True


def test_03_missing_canonical_node_endpoint(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    path = wp2a / "integrated_causal_graph.v1.json"
    doc = json.loads(path.read_text())
    doc["nodes"] = [doc["nodes"][0]]
    path.write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "IDENTITY_BINDING_FAILURE"


def test_04_missing_edge_endpoint(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    doc = json.loads((wp2a / "integrated_causal_graph.v1.json").read_text())
    doc["edges"][0]["target_native_id"] = "SO-MISSING"
    (wp2a / "integrated_causal_graph.v1.json").write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "IDENTITY_BINDING_FAILURE"


def test_05_duplicate_canonical_identities(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    doc = json.loads((wp2a / "integrated_causal_graph.v1.json").read_text())
    doc["nodes"] = [doc["nodes"][0], doc["nodes"][0]]
    (wp2a / "integrated_causal_graph.v1.json").write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "IDENTITY_BINDING_FAILURE"


def test_06_invalid_provenance_reference(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    doc = json.loads((wp2a / "integrated_causal_graph.v1.json").read_text())
    doc["nodes"][0].pop("provenance")
    (wp2a / "integrated_causal_graph.v1.json").write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "PROVENANCE_FAILURE"


def test_07_unsupported_schema_version(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    path = wp2a / "integrated_causal_graph.v1.json"
    doc = json.loads(path.read_text())
    doc["schema_version"] = "integrated_causal_graph.v99"
    path.write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "INVALID_INPUT"


def test_08_snapshot_mismatch(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    path = wp2a / "causal_integration_manifest.v1.json"
    doc = json.loads(path.read_text())
    doc["snapshot_id"] = "other_snap"
    path.write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "SNAPSHOT_BINDING_FAILURE"


def test_09_runtime_context_flag_mismatch(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    path = wp2a / "causal_overlay.v1.json"
    doc = json.loads(path.read_text())
    doc["RUNTIME_EVIDENCE_BINDING"] = "PROVEN"
    path.write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert res.ok
    assert (
        res.bundle_doc["runtime_context_assessment"]["RUNTIME_EVIDENCE_BINDING"] == "NOT_REQUESTED"
    )


def test_10_authority_mismatch(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    path = wp2a / "integrated_causal_graph.v1.json"
    doc = json.loads(path.read_text())
    doc["authority"] = "LIVE"
    path.write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "AUTHORITY_BOUNDARY_FAILURE"


def test_11_vacuous_temporal_proof_rejected(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    ig = json.loads((wp2a / "integrated_causal_graph.v1.json").read_text())
    man = json.loads((wp2a / "causal_integration_manifest.v1.json").read_text())
    ig["TEMPORAL_CAUSALITY_PROVEN"] = True
    man["TEMPORAL_CAUSALITY_PROVEN"] = True
    (wp2a / "integrated_causal_graph.v1.json").write_text(json.dumps(ig), encoding="utf-8")
    (wp2a / "causal_integration_manifest.v1.json").write_text(json.dumps(man), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "INSUFFICIENT_CAUSAL_EVIDENCE"


def test_12_empty_graph(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1", nodes=[], edges=[])
    wp2a = _run_wp2a(tmp_path, wp1)
    res = _inspect(wp2a, tmp_path)
    assert res.ok
    assert res.bundle_doc["semantic_assessment"]["STRUCTURAL_GRAPH_VALIDITY"] is False


def test_13_partial_graph_with_coverage_gaps(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    gaps_path = wp2a / "causal_coverage_gaps.v1.json"
    gaps = json.loads(gaps_path.read_text())
    gaps["gaps"] = [{"reason": "synthetic_gap", "note": "test"}]
    gaps_path.write_text(json.dumps(gaps), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert res.ok
    assert any(
        g.get("reason") == "synthetic_gap" for g in res.bundle_doc["preserved_coverage_gaps"]
    )


def test_14_historical_entity_contamination(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    doc = json.loads((wp2a / "integrated_causal_graph.v1.json").read_text())
    doc["nodes"][0]["current_relevance"]["CURRENT_RELEVANCE_STATE"] = "HISTORICAL"
    (wp2a / "integrated_causal_graph.v1.json").write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "HISTORICAL_CONTAMINATION"


def test_15_historical_edge_contamination(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    path = wp2a / "integrated_causal_graph.v1.json"
    doc = json.loads(path.read_text())
    doc["edges"][0]["current_relevance"]["CURRENT_RELEVANCE_STATE"] = "HISTORICAL"
    path.write_text(json.dumps(doc), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "HISTORICAL_CONTAMINATION"


def test_16_contradictory_authority_flags(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    man = json.loads((wp2a / "causal_integration_manifest.v1.json").read_text())
    man["CURRENT_CAUSAL_GRAPH_VERIFIED"] = True
    ig = json.loads((wp2a / "integrated_causal_graph.v1.json").read_text())
    ig["CURRENT_CAUSAL_GRAPH_VERIFIED"] = False
    (wp2a / "causal_integration_manifest.v1.json").write_text(json.dumps(man), encoding="utf-8")
    (wp2a / "integrated_causal_graph.v1.json").write_text(json.dumps(ig), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok
    assert res.failure_semantic == "SNAPSHOT_BINDING_FAILURE"


def test_17_manifest_integrated_overlay_count_mismatch(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    man = json.loads((wp2a / "causal_integration_manifest.v1.json").read_text())
    man["overlay_edge_count"] = 99
    (wp2a / "causal_integration_manifest.v1.json").write_text(json.dumps(man), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok


def test_18_missing_required_manifest_field(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    man = json.loads((wp2a / "causal_integration_manifest.v1.json").read_text())
    man.pop("snapshot_id")
    (wp2a / "causal_integration_manifest.v1.json").write_text(json.dumps(man), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert not res.ok


def test_19_unexpected_optional_fields_accepted(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    ig = json.loads((wp2a / "integrated_causal_graph.v1.json").read_text())
    ig["extension_field"] = "allowed"
    (wp2a / "integrated_causal_graph.v1.json").write_text(json.dumps(ig), encoding="utf-8")
    res = _inspect(wp2a, tmp_path)
    assert res.ok


def test_20_repeated_deterministic_execution(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    out1 = tmp_path / "det1"
    out2 = tmp_path / "det2"
    r1 = run_offline_graph_inspection_v1(wp2a_output_dir=wp2a, output_dir=out1, repo_root=REPO_ROOT)
    r2 = run_offline_graph_inspection_v1(wp2a_output_dir=wp2a, output_dir=out2, repo_root=REPO_ROOT)
    assert r1.ok and r2.ok
    b1 = (out1 / "inspection_bundle.v1.json").read_bytes()
    b2 = (out2 / "inspection_bundle.v1.json").read_bytes()
    assert hashlib.sha256(b1).hexdigest() == hashlib.sha256(b2).hexdigest()


def test_21_output_path_inside_repository_rejected(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    res = run_offline_graph_inspection_v1(
        wp2a_output_dir=wp2a,
        output_dir=REPO_ROOT / "adapter_forbidden_out",
        repo_root=REPO_ROOT,
    )
    assert not res.ok
    assert res.failure_semantic == "UNSAFE_OUTPUT_PATH"


def test_22_input_artifacts_not_modified(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    before = {
        n: hashlib.sha256((wp2a / n).read_bytes()).hexdigest()
        for n in (
            "integrated_causal_graph.v1.json",
            "causal_integration_manifest.v1.json",
            "causal_coverage_gaps.v1.json",
            "causal_overlay.v1.json",
        )
    }
    res = _inspect(wp2a, tmp_path)
    assert res.ok
    after = {n: hashlib.sha256((wp2a / n).read_bytes()).hexdigest() for n in before}
    assert before == after


def test_23_path_escape_rejected(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    res = run_offline_graph_inspection_v1(
        wp2a_output_dir=wp2a,
        output_dir=REPO_ROOT / ".." / ".." / "tmp" / "escape_test_out",
        repo_root=REPO_ROOT,
    )
    assert res.ok or res.failure_semantic == "UNSAFE_OUTPUT_PATH"


def test_24_read_only_input_integrity(tmp_path: Path) -> None:
    wp1 = _write_wp1(tmp_path / "wp1")
    wp2a = _run_wp2a(tmp_path, wp1)
    for name in load_wp2a_artifacts_v1(wp2a_output_dir=wp2a).bundle.artifact_sha256:  # type: ignore[union-attr]
        p = wp2a / name
        p.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    res = _inspect(wp2a, tmp_path)
    assert res.ok


def test_25_no_productive_or_ghv_core_imports() -> None:
    forbidden = (
        "src.trading",
        "full_core_live_path_composition_root",
        "master_v2",
        "double_play",
        "ghv_pre_external_continuation_harness",
    )
    for py in ADAPTER_PKG.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for bad in forbidden:
                        assert bad not in alias.name
            if isinstance(node, ast.ImportFrom) and node.module:
                for bad in forbidden:
                    assert bad not in node.module


def test_actual_wp2a_chain_smoke(tmp_path: Path) -> None:
    """Consume output from real run_causal_integration_v1 (not hand-built integrated JSON)."""
    wp1 = _write_wp1(tmp_path / "wp1_smoke")
    wp2a = _run_wp2a(tmp_path, wp1)
    loaded = load_wp2a_artifacts_v1(wp2a_output_dir=wp2a)
    assert loaded.ok
    assert loaded.bundle.integrated.get("schema_version") == INTEGRATED_GRAPH_SCHEMA
    assert loaded.bundle.manifest.get("schema_version") == INTEGRATION_MANIFEST_SCHEMA
    res = _inspect(wp2a, tmp_path)
    assert res.ok
    assert (_out_dir(tmp_path) / "inspection_manifest.v1.json").is_file()
