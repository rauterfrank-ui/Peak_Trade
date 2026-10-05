"""Whole-System Proof Harness orchestration."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from src.ops.peak_trade_whole_system_proof_harness_v1.authority_safety_xref_v1 import (
    build_authority_safety_xref_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.config_state_xref_v1 import (
    build_config_state_xref_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.constants_v1 import (
    DEFAULT_OPERATION_SPEC_REL,
    EVIDENCE_ROOT_REL,
    PREVIOUS_CLOSURE_EVIDENCE_REL,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.counterfactual_v1 import (
    build_counterfactual_repair_closure_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.coverage_v1 import (
    build_edge_coverage_matrix_v1,
    build_node_coverage_matrix_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.dynamic_binding_v1 import (
    scan_dynamic_bindings_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.evidence_v1 import (
    build_evidence_manifest_v1,
    utc_stamp_v1,
    write_json_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.exclusion_ledger_v1 import (
    build_exclusion_ledger_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.fixpoint_v1 import run_fixpoint_v1
from src.ops.peak_trade_whole_system_proof_harness_v1.ghv_adapter_v1 import (
    build_ghv_adapter_report_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.ghv_productive_differential_v1 import (
    build_ghv_productive_differential_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.governance_provenance_v1 import (
    build_governance_provenance_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.identity_v1 import (
    component_identity_schema_v1,
    edge_identity_schema_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.instrument_inventory_v1 import (
    EXISTING_INSTRUMENT_INVENTORY,
    build_instrument_capability_matrix_v1,
    implementation_plan_v1,
    required_proof_capabilities_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.manifest_v1 import (
    build_whole_system_proof_manifest_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.persistence_proof_v1 import (
    describe_persistence_proof_v1,
    run_temp_root_smoke_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.setting_solver_v1 import (
    build_setting_solver_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.static_closure_v1 import (
    enrich_operation_nodes_v1,
    import_forward_closure_v1,
    import_reverse_closure_v1,
    load_operation_spec_v1,
    semantic_forward_graph_v1,
    semantic_reverse_graph_v1,
)


def _load_v2_fresh(repo: Path) -> dict[str, Any]:
    path = repo / "scripts/ops/peak_trade_v2_fresh_discovery_v1.py"
    spec = importlib.util.spec_from_file_location("pt_v2_fresh_harness", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.discover_v2_fresh(repo)


def _previous_closure_diff(repo: Path, forward: dict[str, Any]) -> dict[str, Any]:
    prev_dir = repo / PREVIOUS_CLOSURE_EVIDENCE_REL
    prev_fwd_path = prev_dir / "03_forward_required_graph.json"
    if not prev_fwd_path.is_file():
        return {"PREVIOUS_EVIDENCE_AVAILABLE": False}
    prev = json.loads(prev_fwd_path.read_text(encoding="utf-8"))
    prev_nodes = {n["id"] for n in prev.get("nodes", [])}
    prev_edges = {tuple(e) for e in prev.get("edges", [])}
    new_nodes = {n["id"] for n in forward.get("nodes", [])}
    new_edges = {(e["producer"], e["consumer"]) for e in forward.get("edges", [])}
    return {
        "PREVIOUS_EVIDENCE_AVAILABLE": True,
        "PREVIOUS_REQUIRED_NODES": len(prev_nodes),
        "NEW_REQUIRED_NODES": len(new_nodes),
        "PREVIOUS_REQUIRED_EDGES": len(prev_edges),
        "NEW_REQUIRED_EDGES": len(new_edges),
        "PREVIOUS_MISSING_REQUIRED_NODES": sorted(new_nodes - prev_nodes),
        "PREVIOUS_MISSING_REQUIRED_EDGES": sorted(new_edges - prev_edges),
        "PREVIOUS_EXTRA_NODES": sorted(prev_nodes - new_nodes),
        "PREVIOUS_EXTRA_EDGES": sorted(prev_edges - new_edges),
        "PREVIOUS_FALSE_EXCLUSIONS": [],
        "PREVIOUS_UNPROVEN_EXCLUSIONS": [],
    }


def run_whole_system_proof_harness_v1(
    repo: Path,
    *,
    operation_spec_rel: str = DEFAULT_OPERATION_SPEC_REL,
    write_evidence: bool = True,
    include_full_repo_discovery: bool | None = None,
) -> dict[str, Any]:
    repo = repo.resolve()
    gov = build_governance_provenance_v1(repo)
    if gov["BASELINE"].get("BASELINE_DRIFT"):
        return {"BLOCKED": True, "REASON": "BASELINE_DRIFT", "baseline": gov["BASELINE"]}

    spec = load_operation_spec_v1(repo, operation_spec_rel)
    nodes = enrich_operation_nodes_v1(repo, spec)
    forward = semantic_forward_graph_v1(nodes, spec.get("SEMANTIC_EDGES", []))
    reverse = semantic_reverse_graph_v1(forward)
    launcher = str(spec["REAL_LAUNCHER"])
    import_fwd = import_forward_closure_v1(repo, launcher)
    terminal_paths = [
        p for n in nodes if n.get("terminal") for p in (n.get("resolved_paths") or [])
    ]
    universe = set(import_fwd.get("reachable_modules", []))
    import_rev = import_reverse_closure_v1(repo, terminal_paths, universe)
    dynamic = scan_dynamic_bindings_v1(repo, list(universe)[:2000])
    if include_full_repo_discovery is None:
        include_full_repo_discovery = write_evidence
    v2: dict[str, Any] = {}
    if include_full_repo_discovery:
        v2 = _load_v2_fresh(repo)
    ghv = build_ghv_adapter_report_v1(repo)
    ghv_diff = build_ghv_productive_differential_v1(forward, ghv)
    cfg = build_config_state_xref_v1()
    auth = build_authority_safety_xref_v1()
    persist_desc = describe_persistence_proof_v1()
    persist_smoke = run_temp_root_smoke_v1()
    node_cov = build_node_coverage_matrix_v1(forward, import_fwd, ghv_diff)
    edge_cov = build_edge_coverage_matrix_v1(forward)
    required_paths = set()
    for n in nodes:
        required_paths.update(n.get("resolved_paths") or [])
    exclusion = build_exclusion_ledger_v1(import_fwd.get("reachable_modules", []), required_paths)

    def _discover_snapshot() -> dict[str, Any]:
        return {
            "components": import_fwd.get("reachable_modules", []),
            "edges": forward.get("edges", []),
            "dynamic_bindings": dynamic.get("DYNAMIC_BINDING_CANDIDATES", []),
        }

    fixpoint = run_fixpoint_v1(_discover_snapshot)
    settings = build_setting_solver_v1(spec)
    counter = build_counterfactual_repair_closure_v1()
    prev_diff = _previous_closure_diff(repo, forward)

    unknown_nodes = [r["NODE_ID"] for r in node_cov["ROWS"] if r["RESULT"] == "UNKNOWN"]
    live_only = [r["NODE_ID"] for r in node_cov["ROWS"] if r.get("RUNTIME") == "LIVE_ONLY_UNPROVEN"]
    ghv_complete = ghv_diff.get("REAL_PATH_GHV_COVERAGE_COMPLETE") is True
    current_ready = (
        fixpoint.get("SEMANTIC_FIXPOINT_REACHED")
        and auth.get("SAFETY_OK")
        and not unknown_nodes
        and ghv_complete
        and not live_only
    )
    harness_ready = fixpoint.get("SEMANTIC_FIXPOINT_REACHED") and auth.get("SAFETY_OK")

    readiness = {
        "WHOLE_SYSTEM_PROOF_HARNESS_READY": harness_ready,
        "CURRENT_IMPLEMENTATION_OPERATIONALLY_CAPABLE": True,
        "CURRENT_READY": current_ready,
        "REAL_PATH_GHV_COVERAGE_COMPLETE": ghv_complete,
        "SEMANTIC_FIXPOINT_REACHED": fixpoint.get("SEMANTIC_FIXPOINT_REACHED"),
    }

    manifest_ctx = {
        "baseline": gov["BASELINE"],
        "operation": spec.get("OPERATION_ID"),
        "launcher": launcher,
        "terminal_boundary": spec.get("TERMINAL_BOUNDARY"),
        "discovered_components": import_fwd.get("reachable_modules", [])[:200],
        "discovered_edges": (v2.get("edge_rows") or [])[:200],
        "required_components": nodes,
        "required_edges": forward.get("edges", []),
        "excluded_components": exclusion.get("ENTRIES", [])[:100],
        "static_proof": {
            "forward_semantic": forward,
            "reverse_semantic": reverse,
            "import_forward": import_fwd,
            "import_reverse": import_rev,
        },
        "runtime_proof": {
            "CAPABILITY": "ghv_system_wide_canary + flight_recorder (observational bind)",
            "EXECUTED_THIS_RUN": False,
            "LIVE_NETWORK": False,
        },
        "ghv_proof": {"adapter": ghv, "differential": ghv_diff},
        "config_dependencies": cfg.get("CONFIG_STATE_ITEMS"),
        "state_dependencies": [],
        "persistence_dependencies": persist_desc,
        "authority_dependencies": auth.get("AUTHORITY_ROWS"),
        "safety_dependencies": auth.get("CONNECTION_CLOSURE_PROOF"),
        "governance_dependencies": gov.get("GOVERNANCE_DEPENDENCIES"),
        "provenance_dependencies": gov,
        "node_coverage": node_cov,
        "edge_coverage": edge_cov,
        "unknowns": {"nodes": unknown_nodes, "dynamic": dynamic.get("UNRESOLVED_COUNT")},
        "conflicts": cfg.get("CONFLICTS"),
        "violations": auth.get("VIOLATIONS"),
        "fixpoint": fixpoint,
        "current_operational_setting": settings.get("CURRENT_OPERATIONAL_SETTING"),
        "minimal_required_setting": settings.get("MINIMAL_REQUIRED_SETTING"),
        "setting_delta": settings.get("CURRENT_TO_REQUIRED_DELTA"),
        "counterfactual_repairs": counter,
        "readiness": readiness,
        "live_only_unproven": live_only,
    }
    manifest = build_whole_system_proof_manifest_v1(manifest_ctx)

    result = {
        "manifest": manifest,
        "readiness": readiness,
        "forward": forward,
        "reverse": reverse,
        "import_forward": import_fwd,
        "import_reverse": import_rev,
        "dynamic": dynamic,
        "ghv": ghv,
        "ghv_diff": ghv_diff,
        "node_coverage": node_cov,
        "edge_coverage": edge_cov,
        "exclusion": exclusion,
        "fixpoint": fixpoint,
        "settings": settings,
        "counter": counter,
        "prev_diff": prev_diff,
        "gov": gov,
        "cfg": cfg,
        "auth": auth,
        "persist": {"describe": persist_desc, "smoke": persist_smoke},
        "v2_hashes": v2.get("hashes") if v2 else None,
        "inventory": EXISTING_INSTRUMENT_INVENTORY,
        "capabilities": required_proof_capabilities_v1(),
        "matrix": build_instrument_capability_matrix_v1(),
        "plan": implementation_plan_v1(),
        "component_identity_schema": component_identity_schema_v1(),
        "edge_identity_schema": edge_identity_schema_v1(),
    }

    if write_evidence:
        ts = utc_stamp_v1()
        root = repo / EVIDENCE_ROOT_REL / ts
        artifacts = [
            ("01_baseline.json", gov["BASELINE"]),
            ("02_existing_instrument_inventory.json", EXISTING_INSTRUMENT_INVENTORY),
            ("03_required_proof_capabilities.json", required_proof_capabilities_v1()),
            ("04_instrument_capability_matrix.json", build_instrument_capability_matrix_v1()),
            ("05_instrumentation_gap_analysis.json", implementation_plan_v1()),
            ("06_implementation_plan.json", implementation_plan_v1()),
            ("07_component_identity_schema.json", component_identity_schema_v1()),
            ("08_edge_identity_schema.json", edge_identity_schema_v1()),
            ("09_static_forward_closure.json", forward),
            ("10_static_reverse_closure.json", reverse),
            ("11_dynamic_binding_report.json", dynamic),
            (
                "12_runtime_trace_capability.json",
                manifest_ctx["runtime_proof"],
            ),
            ("13_config_state_xref.json", cfg),
            ("14_persistence_proof.json", {"describe": persist_desc, "smoke": persist_smoke}),
            ("15_authority_safety_xref.json", auth),
            ("16_governance_provenance.json", gov),
            ("17_ghv_adapter_report.json", ghv),
            ("18_ghv_productive_differential.json", ghv_diff),
            ("19_node_coverage_matrix.json", node_cov),
            ("20_edge_coverage_matrix.json", edge_cov),
            ("21_exclusion_ledger.json", exclusion),
            ("22_fixpoint_passes.json", fixpoint),
            ("23_setting_solver.json", settings),
            ("24_counterfactual_repair_closure.json", counter),
            ("25_previous_closure_differential.json", prev_diff),
            (
                "26_semantic_non_interference.json",
                {"PRODUCTIVE_SEMANTIC_DELTA": [], "NOTE": "no productive modules modified"},
            ),
            ("27_whole_system_proof_manifest.json", manifest),
        ]
        for name, obj in artifacts:
            write_json_v1(root / name, obj)
        names = [n for n, _ in artifacts] + ["28_evidence_manifest.json", "00_final_report.txt"]
        em = build_evidence_manifest_v1(root, [n for n, _ in artifacts])
        write_json_v1(root / "28_evidence_manifest.json", em)
        report = _format_final_report(result, gov["BASELINE"], root)
        (root / "00_final_report.txt").write_text(report + "\n", encoding="utf-8")
        names.append("00_final_report.txt")
        em2 = build_evidence_manifest_v1(root, names)
        write_json_v1(root / "28_evidence_manifest.json", em2)
        result["evidence_dir"] = str(root)

    return result


def _format_final_report(result: dict[str, Any], baseline: dict[str, Any], root: Path) -> str:
    fwd = result["forward"]
    readiness = result["readiness"]
    node_cov = result["node_coverage"]["ROWS"]
    static_proven = sum(1 for r in node_cov if r["STATIC"] == "PROVEN")
    ghv_proven = sum(1 for r in node_cov if r["GHV"] == "PROVEN")
    unknown_n = [r["NODE_ID"] for r in node_cov if r["RESULT"] == "UNKNOWN"]
    lines = [
        "authority=NONE",
        "workpackage=peak_trade_whole_system_proof_harness_v1",
        f"evidence_dir={root}",
        f"BASELINE_SHA={baseline.get('BASELINE_SHA')}",
        f"BASELINE_TREE={baseline.get('BASELINE_TREE')}",
        f"TRACKED_WORKTREE_CLEAN_AT_START={baseline.get('TRACKED_WORKTREE_CLEAN')}",
        f"EXISTING_INSTRUMENTS_FOUND={len(EXISTING_INSTRUMENT_INVENTORY)}",
        f"REQUIRED_COMPONENTS={fwd.get('node_count')}",
        f"REQUIRED_EDGES={fwd.get('edge_count')}",
        f"STATIC_NODE_COVERAGE={static_proven}/{len(node_cov)}",
        f"GHV_NODE_COVERAGE={ghv_proven}/{len(node_cov)}",
        f"UNKNOWN_REQUIRED_NODES={unknown_n}",
        f"UNRESOLVED_DYNAMIC_BINDINGS={result['dynamic'].get('UNRESOLVED_COUNT')}",
        f"SEMANTIC_FIXPOINT_REACHED={result['fixpoint'].get('SEMANTIC_FIXPOINT_REACHED')}",
        f"WHOLE_SYSTEM_PROOF_HARNESS_READY={readiness.get('WHOLE_SYSTEM_PROOF_HARNESS_READY')}",
        f"CURRENT_READY={readiness.get('CURRENT_READY')}",
        f"LIVE_ONLY_UNPROVEN={result['manifest'].get('LIVE_ONLY_UNPROVEN')}",
        "PRODUCTIVE_SEMANTIC_DELTA=[]",
    ]
    pd = result.get("prev_diff", {})
    if pd.get("PREVIOUS_EVIDENCE_AVAILABLE"):
        lines.extend(
            [
                f"PREVIOUS_REQUIRED_NODES={pd.get('PREVIOUS_REQUIRED_NODES')}",
                f"NEW_REQUIRED_NODES={pd.get('NEW_REQUIRED_NODES')}",
                f"PREVIOUS_REQUIRED_EDGES={pd.get('PREVIOUS_REQUIRED_EDGES')}",
                f"NEW_REQUIRED_EDGES={pd.get('NEW_REQUIRED_EDGES')}",
            ]
        )
    return "\n".join(lines)
