"""Offline tests for ghv_forensic_whole_system_crosswalk_v1."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

import pytest

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.compose_v1 import (
    run_forensic_crosswalk_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.graph_mode_v1 import GraphMode
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.edges_v1 import (
    assert_known_edge_type,
    census_flow_to_typed_edge,
    edge_semantics_flags,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.identity_v1 import (
    build_cfi_v1,
    snapshot_id_from_bindings,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.snapshot_v1 import (
    build_code_snapshot_v1,
    dirty_fingerprint,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = REPO_ROOT / "scripts" / "ops" / "ghv_forensic_whole_system_crosswalk_v1"
RULES = PACKAGE / "crosswalk_rules.v1.json"
_RELAX = {"strict_repo_invariants": False, "graph_mode": GraphMode.NAVIGATION_ONLY}
_REPO_NAV = {"strict_repo_invariants": True, "graph_mode": GraphMode.NAVIGATION_ONLY}
_STRICT = {"strict_repo_invariants": True, "graph_mode": GraphMode.STRICT_CURRENT}


def _minimal_census(*, extra_edge: dict | None = None) -> dict:
    objs = [
        {
            "object_id": "SO-A",
            "current_status": "PROVEN_CURRENT",
            "epistemic_status": "PROVEN_CURRENT",
            "primary_class": "SHARED_INFRASTRUCTURE",
            "paths": ["src/a.py"],
        },
        {
            "object_id": "SO-B",
            "current_status": "PROVEN_CURRENT",
            "epistemic_status": "PROVEN_CURRENT",
            "primary_class": "SHARED_INFRASTRUCTURE",
            "paths": ["src/b.py"],
        },
    ]
    edges = [
        {
            "edge_id": "E1",
            "source_object": "SO-A",
            "target_object": "SO-B",
            "flow_type": "DATA_FLOW",
            "epistemic_status": "PROVEN_CURRENT",
            "contract_or_payload": "payload.v1",
        },
        {
            "edge_id": "E2",
            "source_object": "SO-A",
            "target_object": "SO-B",
            "flow_type": "DECISION_FLOW",
            "epistemic_status": "PROVEN_CURRENT",
            "contract_or_payload": "",
        },
    ]
    if extra_edge:
        edges.append(extra_edge)
    return {
        "artifact_id": "current_system_census_graph_v1",
        "schema_version": "current_system_census_graph.v1",
        "authority": "NONE",
        "map_authority": "NONE",
        "runtime_authority": "NONE",
        "decision_authority": "NONE",
        "not_a_runtime_authority": True,
        "not_a_universe_ratification": True,
        "source_baseline_head": "abc123",
        "census_objects": objs,
        "semantic_edges": edges,
        "topology_domains": [{"topology_id": "TD-1"}],
        "websocket_topology": {},
        "intelligence_topology": {},
        "productive_hot_path": {},
        "productive_terminal": {},
        "authority_map_reconciliation": {},
        "census_discrepancies": [{"discrepancy_id": "D1"}],
        "taxonomy_status": "OPEN_CURRENT",
        "canonical_universe_count_asserted": False,
    }


def _minimal_landscape() -> dict:
    return {
        "authority_effect": "NONE",
        "runtime_authorization_effect": "NONE",
        "not_operational_ssot": True,
        "companion_navigation_doc": "docs/test.md",
        "evidence_baseline_sha": "land1",
        "surfaces": [
            {
                "surface_id": "S1",
                "status": "PROVEN_CURRENT",
                "positive_membership": "TD-1",
                "responsibility": "test",
            }
        ],
    }


def _write_fixture_tree(root: Path, *, census: dict, landscape: dict | None = None) -> None:
    import shutil

    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    census_path = root / "config/governance/current_system_census_graph_v1/source_v1.json"
    census_path.parent.mkdir(parents=True, exist_ok=True)
    census_path.write_text(json.dumps(census), encoding="utf-8")
    land = landscape or _minimal_landscape()
    land_path = root / "config/governance/current_universe_landscape_snapshot_v1/source_v1.json"
    land_path.parent.mkdir(parents=True, exist_ok=True)
    land_path.write_text(json.dumps(land), encoding="utf-8")
    atlas_dir = root / "docs/system_atlas"
    (atlas_dir / "entities").mkdir(parents=True)
    (atlas_dir / "relations").mkdir(parents=True)
    (atlas_dir / "census").mkdir(parents=True)
    (atlas_dir / "entities/catalog.yaml").write_text(
        "entities:\n"
        "  - id: ENT-1\n"
        "    kind: COMPONENT\n"
        "    current_canonical: true\n"
        "    current_status: CURRENT\n"
        "    evidence_sources:\n"
        "      - src/a.py\n",
        encoding="utf-8",
    )
    (atlas_dir / "relations/structural.yaml").write_text(
        "relations:\n"
        "  - id: R1\n"
        "    type: DEPENDS_ON\n"
        "    source: ENT-1\n"
        "    target: ENT-1\n"
        "    epistemic_status: ADJUDICATED\n"
        "    evidence_sources:\n"
        "      - src/a.py\n",
        encoding="utf-8",
    )
    (atlas_dir / "census/census_meta.yaml").write_text(
        "origin_main_sha: meta1\n",
        encoding="utf-8",
    )


def test_valid_identity_mapping_and_cfi_deterministic() -> None:
    snap = "snap0001"
    a = build_cfi_v1(
        entity_type="COMPONENT",
        snapshot_id=snap,
        source_system="SYS",
        source_native_id="SO-A",
    )
    b = build_cfi_v1(
        entity_type="COMPONENT",
        snapshot_id=snap,
        source_system="SYS",
        source_native_id="SO-A",
    )
    assert a == b
    assert a.startswith("CFI/v1/COMPONENT/")


def test_one_to_many_and_many_to_one_rules_in_manifest() -> None:
    rules = {
        "schema_version": "crosswalk_rules.v1",
        "rules": [
            {
                "SOURCE_ID": "a",
                "TARGET_ID": "b",
                "CURRENT_EVIDENCE": "e",
                "CONTRACT_JUSTIFICATION": "j",
                "VALIDATION_STATUS": "APPROVED",
                "mapping_kind": "1:n",
            },
            {
                "SOURCE_ID": "c",
                "TARGET_ID": "d",
                "CURRENT_EVIDENCE": "e2",
                "CONTRACT_JUSTIFICATION": "j2",
                "VALIDATION_STATUS": "APPROVED",
                "mapping_kind": "n:1",
            },
        ],
    }
    path = Path("/tmp/crosswalk_rules_test.json")
    path.write_text(json.dumps(rules), encoding="utf-8")
    out = Path("/tmp/ghv_crosswalk_test_1n")
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=path,
        include_atlas=False,
        **_REPO_NAV,
    )
    assert result.coverage.get("explicit_rules_applied")


def test_ambiguous_identity_collision_native_id() -> None:
    with pytest.raises(ValueError, match="control characters"):
        build_cfi_v1(
            entity_type="COMPONENT",
            snapshot_id="s",
            source_system="SYS",
            source_native_id="bad\x00id",
        )


def test_missing_revision_snapshot_binding() -> None:
    bindings = {
        "git_head": "",
        "census_revision": "",
        "landscape_revision": "",
        "atlas_revision": "",
        "dirty_fingerprint": "x",
    }
    sid = snapshot_id_from_bindings(bindings)
    assert len(sid) == 32


def test_schema_mismatch_unknown_edge() -> None:
    with pytest.raises(ValueError, match="unknown_edge_type"):
        assert_known_edge_type("NOT_A_REAL_EDGE")


def test_dirty_worktree_snapshot_changes_fingerprint() -> None:
    fp = dirty_fingerprint(REPO_ROOT)
    assert len(fp) == 16


def test_baseline_c1_isolation_cli_blocks_c1_path() -> None:
    c1 = REPO_ROOT / ".worktrees/pl_c1_p510a_entry_exit_alignment_v1"
    if not c1.is_dir():
        pytest.skip("C1 worktree not present locally")
    proc = subprocess.run(
        [
            str(REPO_ROOT / "scripts/pt"),
            "-m",
            "scripts.ops.ghv_forensic_whole_system_crosswalk_v1.cli",
            "--repo-root",
            str(c1),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "C1_WORKTREE_NOT_ALLOWED" in proc.stdout or proc.stdout


def _git_init_commit(root: Path) -> str:
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-m", "init", "--allow-empty"],
        check=True,
        capture_output=True,
    )
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def _sync_governance_baselines_to_head(root: Path, head: str) -> None:
    census_path = root / "config/governance/current_system_census_graph_v1/source_v1.json"
    census = json.loads(census_path.read_text(encoding="utf-8"))
    census["source_baseline_head"] = head
    census_path.write_text(json.dumps(census), encoding="utf-8")
    land_path = root / "config/governance/current_universe_landscape_snapshot_v1/source_v1.json"
    land = json.loads(land_path.read_text(encoding="utf-8"))
    land["evidence_baseline_sha"] = head
    land_path.write_text(json.dumps(land), encoding="utf-8")


def test_historical_entity_exclusion_atlas() -> None:
    root = Path("/tmp/ghv_crosswalk_hist_entity")
    root.mkdir(exist_ok=True)
    census = _minimal_census()
    _write_fixture_tree(root, census=census)
    catalog = root / "docs/system_atlas/entities/catalog.yaml"
    catalog.write_text(
        "entities:\n  - id: HIST-1\n    kind: COMPONENT\n    epistemic_class: HISTORICAL\n",
        encoding="utf-8",
    )
    _git_init_commit(root)
    out = root / "out"
    result = run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=out,
        rules_path=RULES,
        **_RELAX,
    )
    ids = {e["id"] for e in result.excluded if e.get("kind") == "atlas_entity"}
    assert "HIST-1" in ids


def test_historical_edge_exclusion_census_epistemic() -> None:
    edge = {
        "edge_id": "HE",
        "source_object": "SO-A",
        "target_object": "SO-B",
        "flow_type": "DATA_FLOW",
        "epistemic_status": "HISTORICAL",
    }
    root = Path("/tmp/ghv_crosswalk_hist_edge")
    _write_fixture_tree(root, census=_minimal_census(extra_edge=edge))
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=root / "out",
        rules_path=RULES,
        **_RELAX,
    )
    assert any(e.get("id") == "HE" and e.get("kind") == "census_edge" for e in result.excluded)


def test_conditionally_active_current_path_offline_research_excluded() -> None:
    census = _minimal_census()
    census["census_objects"].append(
        {
            "object_id": "SO-OFF",
            "current_status": "PROVEN_CURRENT",
            "epistemic_status": "PROVEN_CURRENT",
            "primary_class": "OFFLINE_RESEARCH",
            "productive_reachability": False,
            "paths": [],
        }
    )
    root = Path("/tmp/ghv_crosswalk_conditional")
    _write_fixture_tree(root, census=census)
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=root / "out",
        rules_path=RULES,
        **_RELAX,
    )
    assert any(e.get("id") == "SO-OFF" for e in result.excluded)


def test_structural_vs_causal_edge() -> None:
    flags = edge_semantics_flags("IMPORTS")
    assert flags["structural_only"] is True
    assert flags["causal_propagation_allowed"] is False
    flags2 = edge_semantics_flags("HANDOFF")
    assert flags2["causal_propagation_allowed"] is True


def test_unknown_edge_rejection() -> None:
    with pytest.raises(ValueError):
        edge_semantics_flags("MYSTERY")


def test_decision_flow_without_contract_unresolved() -> None:
    edge_type, note = census_flow_to_typed_edge(
        {"flow_type": "DECISION_FLOW", "contract_or_payload": ""}
    )
    assert edge_type is None
    assert "UNRESOLVED" in note


def test_ghv_evidence_missing_repository_sha_excluded(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "ghv_pre_external_runtime_capture_manifest_v1.json").write_text(
        json.dumps({}),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        evidence_root=evidence,
        include_atlas=False,
        **_REPO_NAV,
    )
    assert "ghv_evidence_attached" not in result.coverage
    assert any(
        e.get("reason") == "missing_repository_sha_in_capture_manifest" for e in result.excluded
    )


def test_conflicting_provenance_ghv_sha_mismatch(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "ghv_pre_external_runtime_capture_manifest_v1.json").write_text(
        json.dumps({"repository_sha": "deadbeef" * 5}),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        evidence_root=evidence,
        include_atlas=False,
        **_REPO_NAV,
    )
    assert any(
        "ghv_evidence" in str(e.get("reason", "")) or "repository_sha" in str(e.get("reason", ""))
        for e in result.excluded
    )


def test_cross_universe_identity() -> None:
    snap = "s1"
    u = build_cfi_v1(
        entity_type="UNIVERSE",
        snapshot_id=snap,
        source_system="CURRENT_UNIVERSE_LANDSCAPE",
        source_native_id="TD-1",
    )
    s = build_cfi_v1(
        entity_type="SURFACE",
        snapshot_id=snap,
        source_system="CURRENT_UNIVERSE_LANDSCAPE",
        source_native_id="S1",
    )
    assert u != s


def test_state_persistence_identity_types() -> None:
    for et in ("STATE_OWNER", "PERSISTENCE_OBJECT"):
        cfi = build_cfi_v1(
            entity_type=et,
            snapshot_id="s",
            source_system="SYS",
            source_native_id="native",
        )
        assert f"CFI/v1/{et}/" in cfi


def test_deterministic_repeated_execution(tmp_path: Path) -> None:
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out1,
        rules_path=RULES,
        include_atlas=False,
        **_REPO_NAV,
    )
    run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out2,
        rules_path=RULES,
        include_atlas=False,
        **_REPO_NAV,
    )
    g1 = (out1 / "composed_forensic_graph.v1.json").read_text(encoding="utf-8")
    g2 = (out2 / "composed_forensic_graph.v1.json").read_text(encoding="utf-8")
    assert json.loads(g1)["snapshot_id"] == json.loads(g2)["snapshot_id"]


def test_partial_graph_ingestion_no_atlas(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        include_atlas=False,
        **_REPO_NAV,
    )
    assert result.coverage["CROSSWALK_EXECUTION_SUCCESS"] is True
    assert result.coverage["IDENTITY_COVERAGE_COMPLETE"] is False


def test_no_productive_runtime_import_in_package() -> None:
    forbidden = (
        "src.trading",
        "full_core_live_path_composition_root",
        "master_v2",
    )
    for py in PACKAGE.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for bad in forbidden:
                        assert bad not in alias.name
            if isinstance(node, ast.ImportFrom) and node.module:
                for bad in forbidden:
                    assert bad not in node.module


def test_no_productive_state_mutation_paths_only_tmp(tmp_path: Path) -> None:
    out = tmp_path / "forensic_out"
    run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        include_atlas=False,
        **_REPO_NAV,
    )
    for name in (
        "composed_forensic_graph.v1.json",
        "crosswalk_manifest.v1.json",
        "coverage_report.v1.json",
        "ambiguity_report.v1.json",
        "excluded_non_current_report.v1.json",
    ):
        assert (out / name).is_file()


def test_full_repo_crosswalk_smoke(tmp_path: Path) -> None:
    out = tmp_path / "smoke"
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        include_atlas=True,
        **_REPO_NAV,
    )
    assert result.ok
    assert len(result.nodes) > 0
    assert result.coverage["historical_graph_ingestion"] is False
    assert result.coverage["SOURCE_VALIDATION_PASS"] is True
    assert result.coverage["GRAPH_AUTHORITY"] == "NAVIGATION_ONLY"
    assert result.coverage["CURRENT_GRAPH_VERIFIED"] is False
    assert result.coverage["CURRENT_ONLY_GRAPH"] is False
    assert result.coverage["ATLAS_CURRENT_ANCHOR_ENFORCED"] is True


def test_missing_retirement_marker_atlas_unknown(tmp_path: Path) -> None:
    root = tmp_path / "no_marker"
    census = _minimal_census()
    _write_fixture_tree(root, census=census)
    (root / "docs/system_atlas/entities/catalog.yaml").write_text(
        "entities:\n  - id: NO-MARKER\n    kind: COMPONENT\n    name: x\n",
        encoding="utf-8",
    )
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=root / "out",
        rules_path=RULES,
        **_RELAX,
    )
    assert any(
        e.get("id") == "NO-MARKER" and e.get("relevance_state") == "UNKNOWN"
        for e in result.excluded
    )


def test_atlas_without_census_anchor_excluded(tmp_path: Path) -> None:
    root = tmp_path / "no_anchor"
    _write_fixture_tree(root, census=_minimal_census())
    (root / "docs/system_atlas/entities/catalog.yaml").write_text(
        "entities:\n"
        "  - id: ORPHAN\n    kind: COMPONENT\n"
        "    current_canonical: true\n"
        "    evidence_sources:\n"
        "      - src/not_in_census.py\n",
        encoding="utf-8",
    )
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root, output_dir=root / "out", rules_path=RULES, **_RELAX
    )
    assert result.coverage["UNKNOWN_ENTITIES_EXCLUDED"] >= 1


def test_valid_conditional_offline_research_included(tmp_path: Path) -> None:
    census = _minimal_census()
    census["census_objects"].append(
        {
            "object_id": "SO-ON",
            "current_status": "PROVEN_CURRENT",
            "epistemic_status": "PROVEN_CURRENT",
            "primary_class": "OFFLINE_RESEARCH",
            "productive_reachability": True,
            "paths": ["src/on.py"],
        }
    )
    root = tmp_path / "conditional_on"
    _write_fixture_tree(root, census=census)
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root, output_dir=root / "out", rules_path=RULES, **_RELAX
    )
    states = {n["current_relevance"]["CURRENT_RELEVANCE_STATE"] for n in result.nodes}
    assert "CURRENT_CONDITIONAL" in states


def test_invalid_census_schema_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "bad_census"
    bad = {"census_objects": [], "semantic_edges": []}
    _write_fixture_tree(root, census=bad)
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root, output_dir=root / "out", rules_path=RULES, **_RELAX
    )
    assert result.ok is False
    assert result.coverage.get("SOURCE_VALIDATION_PASS") is False


def test_snapshot_mismatch_fail_closed_on_repo(tmp_path: Path) -> None:
    out = tmp_path / "snap_fail"
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        include_atlas=False,
        graph_mode=GraphMode.STRICT_CURRENT,
        strict_repo_invariants=True,
    )
    assert result.coverage.get("SOURCE_VALIDATION_PASS") is False
    assert result.coverage.get("EVERY_REQUIRED_VALIDATOR_EXECUTED_AND_PASSED") is True
    assert result.coverage.get("CURRENT_GRAPH_VERIFIED") is False
    assert result.coverage.get("GRAPH_MODE") == "STRICT_CURRENT"
    assert result.ok is False


def test_validator_coverage_repo_root_mismatch_skipped(tmp_path: Path) -> None:
    root = tmp_path / "aligned_fixture_skip"
    _write_fixture_tree(root, census=_minimal_census())
    head = _git_init_commit(root)
    _sync_governance_baselines_to_head(root, head)
    result = run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=root / "out",
        rules_path=RULES,
        include_atlas=False,
        graph_mode=GraphMode.STRICT_CURRENT,
        strict_repo_invariants=True,
        pt_launcher=REPO_ROOT / "scripts/pt",
    )
    assert result.ok is False
    assert result.coverage["EVERY_REQUIRED_VALIDATOR_EXECUTED_AND_PASSED"] is False
    assert result.coverage["SOURCE_VALIDATION_PASS"] is False
    assert result.coverage["CENSUS_SUBPROCESS_EXECUTED"] is False


def test_validator_coverage_subprocess_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1 import source_validation_v1 as sv

    def _fail_census(*, repo_root: Path, pt_launcher: Path) -> tuple[list[str], bool]:
        return (["census_subprocess_failed:test"], True)

    monkeypatch.setattr(sv, "run_census_validator_subprocess", _fail_census)
    out = tmp_path / "subprocess_fail"
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        include_atlas=False,
        graph_mode=GraphMode.STRICT_CURRENT,
        strict_repo_invariants=True,
    )
    assert result.ok is False
    assert result.coverage["EVERY_REQUIRED_VALIDATOR_EXECUTED_AND_PASSED"] is False
    assert result.coverage["SOURCE_VALIDATION_PASS"] is False


def test_validator_coverage_all_pass_strict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1 import source_validation_v1 as sv

    monkeypatch.setattr(
        sv,
        "validate_snapshot_compatibility",
        lambda **kwargs: [],
    )
    out = tmp_path / "all_pass_strict"
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        include_atlas=False,
        graph_mode=GraphMode.STRICT_CURRENT,
        strict_repo_invariants=True,
    )
    assert result.coverage["EVERY_REQUIRED_VALIDATOR_EXECUTED_AND_PASSED"] is True
    assert result.coverage["SOURCE_VALIDATION_PASS"] is True


def test_navigation_only_snapshot_drift_authority(tmp_path: Path) -> None:
    out = tmp_path / "nav_drift"
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        include_atlas=False,
        **_REPO_NAV,
    )
    assert result.coverage["GRAPH_AUTHORITY"] == "NAVIGATION_ONLY"
    assert result.coverage["CURRENT_GRAPH_VERIFIED"] is False
    assert result.coverage["SNAPSHOT_BINDING_VERIFIED"] is False


def test_source_validation_connected_on_repo() -> None:
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.source_validation_v1 import (
        validate_sources_v1,
    )
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.load_sources_v1 import (
        load_sources_v1,
    )

    sources = load_sources_v1(repo_root=REPO_ROOT, rules_path=RULES)
    head = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    vr = validate_sources_v1(
        repo_root=REPO_ROOT,
        census_doc=sources.census,
        landscape_doc=sources.landscape,
        git_head=head,
        strict_repo_invariants=True,
        pt_launcher=REPO_ROOT / "scripts/pt",
    )
    assert vr.census_subprocess_executed is True
    assert vr.landscape_subprocess_executed is True
    assert vr.every_required_validator_executed_and_passed is True
    assert vr.census_validator_connected is True
    assert vr.landscape_validator_connected is True
    assert not vr.census_errors


def test_obsolete_edge_non_current_endpoint(tmp_path: Path) -> None:
    census = _minimal_census()
    census["census_objects"][1]["epistemic_status"] = "HISTORICAL"
    root = tmp_path / "obsolete_edge"
    _write_fixture_tree(root, census=census)
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root, output_dir=root / "out", rules_path=RULES, **_RELAX
    )
    assert result.coverage["NON_CURRENT_EDGES_EXCLUDED"] >= 1


def test_stale_cartography_reference_excluded_via_landscape(tmp_path: Path) -> None:
    census = _minimal_census()
    census["topology_domains"] = []
    land = _minimal_landscape()
    root = tmp_path / "stale_carto"
    _write_fixture_tree(root, census=census, landscape=land)
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=root / "out",
        rules_path=RULES,
        include_atlas=False,
        **_RELAX,
    )
    assert result.coverage["SOURCE_VALIDATION_PASS"] is True


def test_fail_closed_cli_on_validation(tmp_path: Path) -> None:
    root = tmp_path / "cli_fail"
    _write_fixture_tree(root, census={"bad": True})
    _git_init_commit(root)
    proc = subprocess.run(
        [
            str(REPO_ROOT / "scripts/pt"),
            "-m",
            "scripts.ops.ghv_forensic_whole_system_crosswalk_v1.cli",
            "--repo-root",
            str(root),
            "--output-dir",
            str(root / "out"),
            "--no-atlas",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1


def test_strict_matching_snapshots_fixture(tmp_path: Path) -> None:
    root = tmp_path / "strict_match"
    _write_fixture_tree(root, census=_minimal_census())
    head = _git_init_commit(root)
    _sync_governance_baselines_to_head(root, head)
    result = run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=root / "out",
        rules_path=RULES,
        graph_mode=GraphMode.STRICT_CURRENT,
        strict_repo_invariants=False,
    )
    assert result.coverage["SNAPSHOT_BINDING_VERIFIED"] is True
    assert result.coverage["GRAPH_MODE"] == "STRICT_CURRENT"


def test_navigation_only_with_drift(tmp_path: Path) -> None:
    root = tmp_path / "nav_drift"
    _write_fixture_tree(root, census=_minimal_census())
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=root / "out",
        rules_path=RULES,
        **_RELAX,
    )
    assert result.ok is True
    assert result.coverage["SNAPSHOT_BINDING_VERIFIED"] is False
    assert result.coverage["GRAPH_AUTHORITY"] == "NAVIGATION_ONLY"
    assert result.coverage["CURRENT_GRAPH_VERIFIED"] is False
    assert result.coverage["CAUSAL_CLOSURE_PROVEN"] is False


def test_navigation_cannot_claim_current_verification(tmp_path: Path) -> None:
    root = tmp_path / "nav_no_current"
    _write_fixture_tree(root, census=_minimal_census())
    head = _git_init_commit(root)
    _sync_governance_baselines_to_head(root, head)
    result = run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=root / "out",
        rules_path=RULES,
        **_RELAX,
    )
    assert result.coverage["CURRENT_GRAPH_VERIFIED"] is False
    assert result.coverage["CURRENT_ONLY_GRAPH"] is False


def test_no_implicit_strict_to_navigation_cli(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            str(REPO_ROOT / "scripts/pt"),
            "-m",
            "scripts.ops.ghv_forensic_whole_system_crosswalk_v1.cli",
            "--output-dir",
            str(tmp_path / "strict_cli"),
            "--no-atlas",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["graph_mode"] == "STRICT_CURRENT"


def test_navigation_cli_smoke(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            str(REPO_ROOT / "scripts/pt"),
            "-m",
            "scripts.ops.ghv_forensic_whole_system_crosswalk_v1.cli",
            "--navigation-only",
            "--output-dir",
            str(tmp_path / "nav_cli"),
            "--no-atlas",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["graph_authority"] == "NAVIGATION_ONLY"
    assert payload["coverage"]["CURRENT_GRAPH_VERIFIED"] is False


def test_manifest_graph_authority_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "manifest_auth"
    _write_fixture_tree(root, census=_minimal_census())
    _git_init_commit(root)
    out = root / "out"
    run_forensic_crosswalk_v1(
        repo_root=root,
        output_dir=out,
        rules_path=RULES,
        **_RELAX,
    )
    manifest = json.loads((out / "crosswalk_manifest.v1.json").read_text(encoding="utf-8"))
    assert manifest["GRAPH_AUTHORITY"] == "NAVIGATION_ONLY"
    assert manifest["SNAPSHOT_BINDING_VERIFIED"] is False


def test_historical_excluded_both_modes(tmp_path: Path) -> None:
    for mode in (GraphMode.STRICT_CURRENT, GraphMode.NAVIGATION_ONLY):
        root = tmp_path / f"hist_{mode.value}"
        census = _minimal_census()
        census["census_objects"].append(
            {
                "object_id": "SO-H",
                "current_status": "PROVEN_CURRENT",
                "epistemic_status": "HISTORICAL",
                "primary_class": "SHARED_INFRASTRUCTURE",
                "paths": [],
            }
        )
        _write_fixture_tree(root, census=census)
        _git_init_commit(root)
        result = run_forensic_crosswalk_v1(
            repo_root=root,
            output_dir=root / "out",
            rules_path=RULES,
            graph_mode=mode,
            strict_repo_invariants=False,
        )
        assert result.coverage["HISTORICAL_ENTITIES_INGESTED"] == 0


def test_source_validation_repo_root_mismatch_fails_strict(tmp_path: Path) -> None:
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.source_validation_v1 import (
        validate_sources_v1,
    )
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.load_sources_v1 import (
        load_sources_v1,
    )

    root = tmp_path / "fixture"
    _write_fixture_tree(root, census=_minimal_census())
    _git_init_commit(root)
    sources = load_sources_v1(repo_root=root, rules_path=RULES)
    vr = validate_sources_v1(
        repo_root=root,
        census_doc=sources.census,
        landscape_doc=sources.landscape,
        git_head="abc",
        strict_repo_invariants=True,
        pt_launcher=REPO_ROOT / "scripts/pt",
    )
    assert vr.ok is False
    assert vr.every_required_validator_executed_and_passed is False
    assert vr.census_subprocess_executed is False
    assert vr.landscape_subprocess_executed is False
    assert any("repo_root_mismatch" in e for e in vr.all_errors())


def test_source_validation_aligned_repo_executes_subprocess() -> None:
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.source_validation_v1 import (
        validate_sources_v1,
    )
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.load_sources_v1 import (
        load_sources_v1,
    )

    sources = load_sources_v1(repo_root=REPO_ROOT, rules_path=RULES)
    head = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    vr = validate_sources_v1(
        repo_root=REPO_ROOT,
        census_doc=sources.census,
        landscape_doc=sources.landscape,
        git_head=head,
        strict_repo_invariants=True,
        pt_launcher=REPO_ROOT / "scripts/pt",
    )
    assert vr.census_subprocess_executed is True
    assert vr.landscape_subprocess_executed is True
    assert not vr.census_errors
    assert not vr.landscape_errors


def test_navigation_requires_source_validation_pass(tmp_path: Path) -> None:
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=tmp_path / "nav",
        rules_path=RULES,
        **_REPO_NAV,
    )
    assert result.coverage["EVERY_REQUIRED_VALIDATOR_EXECUTED_AND_PASSED"] is True
    assert result.coverage["SOURCE_VALIDATION_PASS"] is True


def test_atlas_hypothesis_entity_excluded(tmp_path: Path) -> None:
    root = tmp_path / "hypothesis"
    _write_fixture_tree(root, census=_minimal_census())
    (root / "docs/system_atlas/entities/catalog.yaml").write_text(
        "entities:\n"
        "  - id: HYP-1\n    kind: COMPONENT\n"
        "    epistemic_class: HYPOTHESIS\n"
        "    current_canonical: true\n"
        "    evidence_sources:\n      - src/a.py\n",
        encoding="utf-8",
    )
    _git_init_commit(root)
    result = run_forensic_crosswalk_v1(
        repo_root=root, output_dir=root / "out", rules_path=RULES, **_RELAX
    )
    assert any(e.get("id") == "HYP-1" for e in result.excluded)


def test_evidence_flow_maps_to_observes_structural() -> None:
    edge_type, _ = census_flow_to_typed_edge(
        {"flow_type": "EVIDENCE_FLOW", "contract_or_payload": "x"}
    )
    assert edge_type == "OBSERVES"
    flags = edge_semantics_flags(edge_type)
    assert flags["structural_only"] is True


def test_code_snapshot_from_repo() -> None:
    from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.load_sources_v1 import (
        load_sources_v1,
    )

    sources = load_sources_v1(repo_root=REPO_ROOT, rules_path=RULES)
    snap = build_code_snapshot_v1(
        repo_root=REPO_ROOT,
        census_doc=sources.census,
        landscape_doc=sources.landscape,
        atlas_meta=sources.atlas_meta,
    )
    assert len(snap.git_head) == 40
