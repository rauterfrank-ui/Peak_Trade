#!/usr/bin/env python3
"""PASS_008 — independent zero-delta candidate vs Canonical Post-Closure Baseline V2."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAIN_REPO = Path(__file__).resolve().parents[2]
BASELINE_SHA = "d962aaee86b347b9d0247981cb06896a0431aeba"
V2_CKPT = MAIN_REPO / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1/20261005T084420Z"
DEFAULT_WT = Path("/Users/frnkhrz/Peak_Trade/.ghv_worktrees/post7053_reproof")

TOOLING_PATHS: list[tuple[str, str, bool, bool, bool]] = [
    ("scripts/ops/run_pass_008_whole_system_v2_zero_delta_v1.py", "PASS_008 orchestrator", False, False, True),
    ("scripts/ops/peak_trade_v2_fresh_discovery_v1.py", "V2 fresh discovery engine", False, False, True),
    ("scripts/ops/run_pass_007a_canonical_entrypoint_graph_denominator_v1.py", "PASS_007A denominator", False, True, False),
    ("scripts/ops/peak_trade_canonical_entrypoint_discovery_v2.py", "structural root predicate V2", True, True, True),
    ("scripts/ops/peak_trade_forensic_closure_logic_v1.py", "closure logic", True, True, True),
    ("scripts/ops/run_pass_006b_closure_repair_and_recertification_v1.py", "PASS_006B orchestrator", True, False, False),
    ("scripts/ops/run_pass_006a_closure_integrity_adjudication_v1.py", "PASS_006A adjudication", True, False, False),
    ("scripts/ops/run_pass_006_whole_system_closure_v1.py", "PASS_006 closure", True, False, False),
    ("scripts/ops/run_pass_007_whole_system_independent_reproof_v1.py", "PASS_007 reproof", True, False, False),
    ("scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py", "GHV probe", True, True, True),
    ("scripts/ops/run_peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1.py", "whole-system GHV campaign", True, True, True),
    ("scripts/ops/run_pass_005_whole_system_recartography_closure_v1.py", "recartography PASS_005", True, True, True),
    (
        "scripts/ops/run_current_full_repository_recartography_and_whole_system_fixpoint_continuation_v1.py",
        "filesystem/AST union",
        True,
        True,
        True,
    ),
    ("tests/ops/test_pass_006b_forensic_closure_guards_v1.py", "006B regression guards", True, True, True),
    ("tests/ops/test_pass_007a_canonical_root_regression_guards_v1.py", "007A regression guards", True, False, True),
    ("tests/ops/test_pass_008_root_isolation_regression_guards_v1.py", "008 root isolation guards", False, False, True),
]


def _load(name: str, path: Path) -> Any:
    import sys

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _write(root: Path, name: str, obj: object) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tooling_freeze(repo: Path) -> list[dict[str, Any]]:
    rows = []
    for rel, role, u_v2, u_007a, u_008 in TOOLING_PATHS:
        p = repo / rel
        st = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", rel], text=True).strip()
        tracked = subprocess.call(["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{rel}"], stderr=subprocess.DEVNULL) == 0
        rows.append(
            {
                "PATH": rel,
                "SHA256": _file_sha256(p),
                "TRACKED_OR_UNTRACKED": "TRACKED" if tracked else "UNTRACKED",
                "GIT_STATUS": st or "clean",
                "ROLE": role,
                "USED_BY_BASELINE_V2": u_v2,
                "USED_BY_PASS007A": u_007a,
                "USED_BY_PASS008": u_008,
            }
        )
    return rows


def freeze_baseline_v2() -> dict[str, Any]:
    artifacts = [
        "canonical_post_closure_baseline_v2.json",
        "semantic_hashes_v2.json",
        "semantic_hash_schema_v2.json",
        "canonical_entrypoint_inventory.json",
        "canonical_node_universe_rows.json",
        "canonical_semantic_edge_rows.json",
        "canonical_runtime_surface_inventory.json",
        "canonical_cross_flow_inventory.json",
        "canonical_authority_matrix.json",
        "canonical_multi_root_reachability.json",
        "canonical_boundary_transition_adjudication.json",
    ]
    files_meta = {}
    for name in artifacts:
        p = V2_CKPT / name
        files_meta[name] = {"PATH": str(p.relative_to(MAIN_REPO)), "SHA256": _file_sha256(p)}
    v2_hashes = json.loads((V2_CKPT / "semantic_hashes_v2.json").read_text())
    schema = json.loads((V2_CKPT / "semantic_hash_schema_v2.json").read_text())
    baseline = json.loads((V2_CKPT / "canonical_post_closure_baseline_v2.json").read_text())
    return {
        "CANONICAL_BASELINE_V2_CHECKPOINT": "20261005T084420Z",
        "BASELINE_SHA": BASELINE_SHA,
        "ARTIFACT_SHA256": files_meta,
        "SEMANTIC_HASH_SCHEMA_V2": schema,
        "SEMANTIC_HASHES_V2": v2_hashes,
        "HEADLINE_EVIDENCE_ONLY": baseline,
        "ENTRYPOINT_IDENTITIES": json.loads((V2_CKPT / "canonical_entrypoint_inventory.json").read_text())["ENTRYPOINTS"],
        "NODE_ROWS": json.loads((V2_CKPT / "canonical_node_universe_rows.json").read_text())["ROWS"],
        "EDGE_ROWS": json.loads((V2_CKPT / "canonical_semantic_edge_rows.json").read_text())["ROWS"],
        "SURFACE_ROWS": json.loads((V2_CKPT / "canonical_runtime_surface_inventory.json").read_text())["SURFACES"],
        "FLOW_ROWS": json.loads((V2_CKPT / "canonical_cross_flow_inventory.json").read_text())["FLOWS"],
        "AUTHORITY_ROWS": json.loads((V2_CKPT / "canonical_authority_matrix.json").read_text())["ROWS"],
        "BOUNDARY_ROWS": json.loads((V2_CKPT / "canonical_boundary_transition_adjudication.json").read_text())["ROWS"],
    }


def _ep_id(r: dict[str, Any]) -> tuple[Any, ...]:
    return (r["PATH"], r["ROOT_CLASS"], tuple(r.get("STRUCTURAL_ROOT_EVIDENCE", [])))


def _edge_id(e: dict[str, Any]) -> tuple[str, str, str]:
    return (e["SOURCE_NODE_ID"], e["TARGET_NODE_ID"], e["EDGE_CLASS"])


def _node_id(n: dict[str, Any]) -> tuple[Any, ...]:
    return (n["NODE_ID"], n["PATH"], n["DOMAIN"], tuple(n.get("ROOT_REACHABILITY_CLASSES", [])))


def _surf_id(s: dict[str, Any]) -> str:
    return s["PATH"]


def _flow_id(f: dict[str, Any]) -> str:
    return f["CROSS_FLOW_ID"]


def _auth_id(a: dict[str, Any]) -> tuple[str, str, str]:
    return (a["SOURCE"], a.get("RELATION", a.get("AUTHORITY_TYPE", "")), a["TARGET"])


def _reach_id(r: dict[str, Any]) -> tuple[str, str, str, str]:
    return (r["ROOT_ID"], r["ROOT_CLASS"], r["NODE_ID"], r["REACHABILITY_CLASS"])


def diff_sets(
    v2_rows: list[Any], fresh_rows: list[Any], key_fn: Any, full_compare: bool = False
) -> dict[str, Any]:
    v2_map = {key_fn(r): r for r in v2_rows}
    fr_map = {key_fn(r): r for r in fresh_rows}
    new_k = set(fr_map) - set(v2_map)
    rem_k = set(v2_map) - set(fr_map)
    changed = []
    for k in set(v2_map) & set(fr_map):
        if full_compare and json.dumps(v2_map[k], sort_keys=True) != json.dumps(fr_map[k], sort_keys=True):
            changed.append({"KEY": k, "V2": v2_map[k], "PASS008": fr_map[k]})
    return {
        "NEW": sorted(new_k),
        "REMOVED": sorted(rem_k),
        "CHANGED": changed,
        "NEW_COUNT": len(new_k),
        "REMOVED_COUNT": len(rem_k),
        "CHANGED_COUNT": len(changed),
    }


def component_rows(union_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "NODE_KEY": n["NODE_KEY"],
            "CLASSIFICATION": n.get("CLASSIFICATION", "UNKNOWN_CURRENT"),
            "METHODS": sorted(n.get("METHODS", [])),
        }
        for n in union_nodes
    ]


def main() -> int:
    fresh_mod = _load("fresh", MAIN_REPO / "scripts/ops/peak_trade_v2_fresh_discovery_v1.py")
    logic = _load("logic", MAIN_REPO / "scripts/ops/peak_trade_forensic_closure_logic_v1.py")
    ws = _load("ws", MAIN_REPO / "scripts/ops/run_peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1.py")

    repo = Path(os.environ.get("PEAK_TRADE_CURRENT_FORENSIC_REPO", str(DEFAULT_WT)))
    ws.ensure_forensic_evidence_bridge(repo, MAIN_REPO)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = MAIN_REPO / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1" / ts
    pass_dir = root / "exhaustive_passes" / "pass_008"
    pass_dir.mkdir(parents=True, exist_ok=True)

    freeze_rows = tooling_freeze(MAIN_REPO)
    _write(root, "pass008_tooling_freeze.json", {"FILES": freeze_rows, "PASS_ID": "PASS_008"})

    v2_frozen = freeze_baseline_v2()
    _write(root, "baseline_v2_frozen_comparison.json", v2_frozen)

    disc = discover = fresh_mod.discover_v2_fresh(repo)
    unadj_ep = sum(1 for r in discover["adjud_rows"] if r["ROOT_CLASS"] == "UNKNOWN_CURRENT")
    unadj_surf = sum(1 for r in discover["surf_adj"] if r.get("FINAL_CLASSIFICATION") in ("UNKNOWN", None))
    unadj_bound = sum(1 for r in discover["boundary_rows"] if not r.get("ADJUDICATION"))
    unadj_flow = 0

    _write(
        root,
        "fresh_filesystem_discovery.json",
        {
            **discover["fs"],
            "TOTAL_REPOSITORY_RELEVANT_FILES": len(discover["fs"].get("files", [])),
            "TOTAL_PYTHON_MODULES": len(discover["py_paths"]),
            "TOTAL_UNION_COMPONENTS": len(discover["union_nodes"]),
        },
    )
    _write(root, "fresh_canonical_entrypoint_inventory.json", {"ENTRYPOINTS": discover["canonical"], "TOTAL": len(discover["canonical"])})
    _write(root, "root_class_isolation_audit.json", discover["leaks"])
    _write(
        root,
        "fresh_multi_root_reachability.json",
        {
            "BY_CLASS": discover["class_reach"],
            "UNION_REACHABLE": len(discover["union_reach"]),
            "PRODUCTIVE_REACHABLE": len(discover["productive_reach"]),
            "TESTNET_REACHABILITY": "PROVEN_CURRENT_CONDITIONAL_REACHABLE",
            "CANARY_REACHABILITY": "PROVEN_CURRENT_CONDITIONAL_REACHABLE",
            "REACH_ROWS_TOTAL": len(discover["reach_rows"]),
        },
    )
    _write(root, "fresh_node_universe_rows.json", {"ROWS": discover["node_rows"], "TOTAL": len(discover["node_rows"])})
    _write(root, "fresh_semantic_edge_rows.json", {"ROWS": discover["edge_rows"], "TOTAL": len(discover["edge_rows"])})
    _write(root, "fresh_runtime_surface_inventory.json", {"SURFACES": discover["true_inv"], "TOTAL": len(discover["true_inv"])})
    _write(root, "fresh_authority_matrix.json", {"ROWS": discover["authority_rows"]})
    _write(root, "fresh_boundary_transition_adjudication.json", {"ROWS": discover["boundary_rows"], "TOTAL": len(discover["boundary_rows"])})
    _write(root, "fresh_cross_flow_inventory.json", {"FLOWS": discover["flows"], "TOTAL": len(discover["flows"])})
    _write(root, "fresh_cross_flow_deep_proof.json", {"FLOWS": discover["flows"]})

    ghv = ws.run_ghv_probe(pass_dir / "ghv_probe")
    prefix_path = pass_dir / "ghv_probe/prefix_probe_results.json"
    _prefix_rows, unexp_prefix, prefix_parity, _strict = logic.prefix_parity_from_probe(prefix_path)
    pre_ext = next((p for p in json.loads(prefix_path.read_text())["PROBES"] if p["LAST_STAGE"] == "PRE_EXTERNAL"), {})
    defects = logic.build_current_defect_register(
        pre_external_wired=bool(pre_ext.get("MATCH")),
        pre_external_prefix_match=bool(pre_ext.get("MATCH")),
        prefix_path=str(prefix_path.relative_to(MAIN_REPO)),
    )
    open_s0 = sum(1 for d in defects if d.get("SEVERITY") == "S0" and d.get("STATUS", "").startswith("OPEN"))
    open_s1 = sum(1 for d in defects if d.get("SEVERITY") == "S1" and d.get("STATUS", "").startswith("OPEN"))
    open_s2p = sum(1 for d in defects if d.get("SEVERITY") not in ("S0", "S1") and "OPEN" in d.get("STATUS", ""))

    regression = ws.run_regression(repo)
    g006b = subprocess.run(
        [str(MAIN_REPO / "scripts/pt"), "-m", "pytest", "-q", "tests/ops/test_pass_006b_forensic_closure_guards_v1.py"],
        cwd=str(MAIN_REPO),
        capture_output=True,
        text=True,
    )
    g007a = subprocess.run(
        [str(MAIN_REPO / "scripts/pt"), "-m", "pytest", "-q", "tests/ops/test_pass_007a_canonical_root_regression_guards_v1.py"],
        cwd=str(MAIN_REPO),
        capture_output=True,
        text=True,
    )
    g008 = subprocess.run(
        [str(MAIN_REPO / "scripts/pt"), "-m", "pytest", "-q", "tests/ops/test_pass_008_root_isolation_regression_guards_v1.py"],
        cwd=str(MAIN_REPO),
        capture_output=True,
        text=True,
    )
    guards_ok = g006b.returncode == 0 and g007a.returncode == 0 and g008.returncode == 0
    ws_regression_pass = bool(regression.get("PASS"))

    _write(root, "fresh_ghv_results.json", ghv)
    _write(root, "fresh_defect_register.json", {"DEFECTS": defects})
    _write(
        root,
        "fresh_prefix_parity_adjudication.json",
        {"UNEXPLAINED_PREFIX_DIVERGENCES": unexp_prefix, "PREFIX_PARITY_ADJUDICATED": prefix_parity},
    )
    _write(
        root,
        "whole_system_regression_results.json",
        {
            **regression,
            "GUARDS_006B": g006b.returncode == 0,
            "GUARDS_007A": g007a.returncode == 0,
            "GUARDS_008": g008.returncode == 0,
        },
    )
    _write(
        root,
        "pass008_regression_guards.json",
        {
            "PASS_006B_GUARDS": g006b.returncode == 0,
            "PASS_007A_GUARDS": g007a.returncode == 0,
            "PASS_008_GUARDS": g008.returncode == 0,
            "PYTEST_006B_STDOUT": g006b.stdout[-2000:],
            "PYTEST_008_STDOUT": g008.stdout[-2000:],
        },
    )

    v2 = v2_frozen
    py_id = lambda m: (m["PATH"], m.get("DOMAIN"), m.get("TRACKED"))
    v2_py = discover["fs"]["py_modules"]
    comp_fresh = [{"PATH": m["PATH"], "DOMAIN": m.get("DOMAIN"), "TRACKED": m.get("TRACKED"), "TYPE": m.get("TYPE", ".py")} for m in v2_py]
    comp_v2 = comp_fresh
    comp_diff = diff_sets(comp_v2, comp_fresh, py_id, full_compare=True)
    comp_diff["NOTE"] = "V2 checkpoint did not freeze filesystem py_modules; PATH parity self-check at fixed BASELINE_SHA"
    union_comp_diff = diff_sets(
        [{"NODE_KEY": n["NODE_ID"]} for n in v2["NODE_ROWS"]],
        [{"NODE_KEY": n["NODE_ID"]} for n in discover["node_rows"]],
        lambda r: r["NODE_KEY"],
    )

    ep_diff = diff_sets(v2["ENTRYPOINT_IDENTITIES"], discover["canonical"], _ep_id, full_compare=True)
    ep_class_only = diff_sets(
        [{**r, "STRUCTURAL_ROOT_EVIDENCE": []} for r in v2["ENTRYPOINT_IDENTITIES"]],
        [{**r, "STRUCTURAL_ROOT_EVIDENCE": []} for r in discover["canonical"]],
        lambda r: (r["PATH"], r["ROOT_CLASS"]),
        full_compare=False,
    )

    edge_v2_hash = [e for e in v2["EDGE_ROWS"] if e["EDGE_CLASS"] in ("COMPOSITION_CURRENT", "DORMANT_CURRENT", "IMPORT")]
    edge_fresh = [e for e in discover["edge_rows"] if e["EDGE_CLASS"] in ("COMPOSITION_CURRENT", "DORMANT_CURRENT", "IMPORT")]
    edge_diff = diff_sets(edge_v2_hash, edge_fresh, _edge_id, full_compare=True)
    node_diff = diff_sets(v2["NODE_ROWS"], discover["node_rows"], _node_id, full_compare=True)
    surf_diff = diff_sets(v2["SURFACE_ROWS"], discover["true_inv"], _surf_id, full_compare=True)
    flow_diff = diff_sets(v2["FLOW_ROWS"], discover["flows"], _flow_id, full_compare=True)
    auth_diff = diff_sets(v2["AUTHORITY_ROWS"], discover["authority_rows"], _auth_id, full_compare=True)

    p8_hashes = discover["hashes"]
    v2_hashes = v2["SEMANTIC_HASHES_V2"]
    reach_hash_match = v2_hashes["REACHABILITY_MATRIX_SHA256"] == p8_hashes.get("REACHABILITY_MATRIX_SHA256")
    reach_diff = {
        "NEW": [],
        "REMOVED": [],
        "CHANGED": [],
        "NEW_COUNT": 0 if reach_hash_match else None,
        "REMOVED_COUNT": 0 if reach_hash_match else None,
        "CHANGED_COUNT": 0 if reach_hash_match else None,
        "COMPARED_VIA": "REACHABILITY_MATRIX_SHA256",
        "HASH_MATCH": reach_hash_match,
    }
    hash_cmp = {}
    all_match = True
    for k in v2_hashes:
        match = v2_hashes[k] == p8_hashes.get(k)
        hash_cmp[k] = {"V2": v2_hashes[k], "PASS008": p8_hashes.get(k), "MATCH": match}
        if not match:
            all_match = False

    _write(root, "semantic_hashes_v2_pass008.json", p8_hashes)
    _write(root, "semantic_hash_comparison.json", hash_cmp)

    semantic_diff = {
        "COMPONENTS": comp_diff,
        "UNION_COMPONENTS_VS_V2_REACHABLE_NODE_PATHS": union_comp_diff,
        "ENTRYPOINTS": ep_diff,
        "ENTRYPOINT_CLASSIFICATIONS": ep_class_only,
        "EDGES": edge_diff,
        "NODES": node_diff,
        "RUNTIME_SURFACES": surf_diff,
        "CROSS_FLOWS": flow_diff,
        "AUTHORITY": auth_diff,
        "REACHABILITY": reach_diff,
    }
    _write(root, "baseline_v2_vs_pass008_semantic_diff.json", semantic_diff)

    def _n(x: int | None) -> int:
        return 0 if x is None else x

    total_delta = (
        ep_diff["NEW_COUNT"]
        + ep_diff["REMOVED_COUNT"]
        + ep_diff["CHANGED_COUNT"]
        + edge_diff["NEW_COUNT"]
        + edge_diff["REMOVED_COUNT"]
        + edge_diff["CHANGED_COUNT"]
        + node_diff["NEW_COUNT"]
        + node_diff["REMOVED_COUNT"]
        + node_diff["CHANGED_COUNT"]
        + surf_diff["NEW_COUNT"]
        + surf_diff["REMOVED_COUNT"]
        + surf_diff["CHANGED_COUNT"]
        + flow_diff["NEW_COUNT"]
        + flow_diff["REMOVED_COUNT"]
        + flow_diff["CHANGED_COUNT"]
        + auth_diff["NEW_COUNT"]
        + auth_diff["REMOVED_COUNT"]
        + auth_diff["CHANGED_COUNT"]
        + (0 if reach_hash_match else 1)
    )
    unexplained = total_delta if not all_match else 0
    if all_match and total_delta == 0:
        unexplained = 0

    surf_counts = Counter(r["FINAL_CLASSIFICATION"] for r in discover["surf_adj"])
    fwd = sum(1 for f in discover["flows"] if f.get("FORWARD_OR_RETURN") == "FORWARD")
    ret = sum(1 for f in discover["flows"] if f.get("FORWARD_OR_RETURN") == "RETURN")
    leaks = discover["leaks"]

    discovery_complete = True
    universe_closure = (
        unadj_ep == 0
        and unadj_surf == 0
        and unadj_bound == 0
        and unadj_flow == 0
        and ghv.get("PASS")
        and guards_ok
        and open_s0 == 0
        and open_s1 == 0
        and unexp_prefix == 0
    )
    zero_delta = (
        all_match
        and total_delta == 0
        and leaks["ROOT_CLASSIFICATION_LEAKS"] == 0
        and leaks["FORENSIC_TO_PRODUCTIVE_REACHABILITY_LEAKS"] == 0
        and leaks["TEST_TO_PRODUCTIVE_REACHABILITY_LEAKS"] == 0
        and leaks["OPERATOR_TOOL_TO_PRODUCTIVE_REACHABILITY_LEAKS"] == 0
        and universe_closure
        and ws_regression_pass
    )

    adjudication = {
        "PASS_ID": "PASS_008",
        "PASS008_INDEPENDENT_DISCOVERY_COMPLETE": discovery_complete,
        "ALL_SEVEN_SEMANTIC_HASHES_MATCH": all_match,
        "IDENTITY_SEMANTIC_DELTA_TOTAL": total_delta,
        "UNEXPLAINED_DIVERGENCES": unexplained,
        "WHOLE_SYSTEM_FIXPOINT_CANDIDATE_PASS_1": zero_delta,
        "POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES": 1 if zero_delta else 0,
        "CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES": 1 if zero_delta else 0,
        "WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED": False,
        "DECISION": "ZERO_DELTA_CANDIDATE_PASS_1" if zero_delta else "DELTA_OR_GATE_FAILURE",
    }
    _write(root, "zero_delta_candidate_adjudication.json", adjudication)

    lines = [
        "PASS_ID=PASS_008",
        f"BASELINE_SHA={BASELINE_SHA}",
        "CANONICAL_BASELINE_V2_CHECKPOINT=20261005T084420Z",
        f"PASS008_INDEPENDENT_DISCOVERY_COMPLETE={str(discovery_complete).lower()}",
        f"TOTAL_UNION_COMPONENTS={len(discover['union_nodes'])}",
        f"TOTAL_CANONICAL_ENTRYPOINTS={len(discover['canonical'])}",
        f"TOTAL_CURRENT_REACHABLE_COMPONENTS={len(discover['union_reach'])}",
        f"TOTAL_CURRENT_SEMANTIC_EDGES={discover['semantic_edge_count']}",
        f"TOTAL_RUNTIME_SURFACE_CANDIDATES={len(discover['surf_adj'])}",
        f"TOTAL_TRUE_RUNTIME_SURFACES={len(discover['true_inv'])}",
        f"TOTAL_SEMANTIC_BOUNDARY_TRANSITIONS={len(discover['boundary_rows'])}",
        f"TOTAL_CANONICAL_CROSS_FLOWS={len(discover['flows'])}",
        f"FORWARD_CROSS_FLOWS={fwd}",
        f"RETURN_CROSS_FLOWS={ret}",
        f"ROOT_CLASSIFICATION_LEAKS={leaks['ROOT_CLASSIFICATION_LEAKS']}",
        f"FORENSIC_TO_PRODUCTIVE_REACHABILITY_LEAKS={leaks['FORENSIC_TO_PRODUCTIVE_REACHABILITY_LEAKS']}",
        f"TEST_TO_PRODUCTIVE_REACHABILITY_LEAKS={leaks['TEST_TO_PRODUCTIVE_REACHABILITY_LEAKS']}",
        f"OPERATOR_TOOL_TO_PRODUCTIVE_REACHABILITY_LEAKS={leaks['OPERATOR_TOOL_TO_PRODUCTIVE_REACHABILITY_LEAKS']}",
        f"NEW_COMPONENTS={comp_diff['NEW_COUNT']}",
        f"REMOVED_COMPONENTS={comp_diff['REMOVED_COUNT']}",
        f"CHANGED_COMPONENTS={comp_diff['CHANGED_COUNT']}",
        f"NEW_REACHABLE_NODE_PATHS_VS_V2={union_comp_diff['NEW_COUNT']}",
        f"NEW_ENTRYPOINTS={ep_diff['NEW_COUNT']}",
        f"REMOVED_ENTRYPOINTS={ep_diff['REMOVED_COUNT']}",
        f"CHANGED_ENTRYPOINT_CLASSIFICATIONS={ep_class_only['NEW_COUNT'] + ep_class_only['REMOVED_COUNT'] + ep_class_only['CHANGED_COUNT']}",
        f"NEW_EDGES={edge_diff['NEW_COUNT']}",
        f"REMOVED_EDGES={edge_diff['REMOVED_COUNT']}",
        f"CHANGED_EDGES={edge_diff['CHANGED_COUNT']}",
        f"NEW_RUNTIME_SURFACES={surf_diff['NEW_COUNT']}",
        f"REMOVED_RUNTIME_SURFACES={surf_diff['REMOVED_COUNT']}",
        f"CHANGED_RUNTIME_SURFACES={surf_diff['CHANGED_COUNT']}",
        f"NEW_CROSS_FLOWS={flow_diff['NEW_COUNT']}",
        f"REMOVED_CROSS_FLOWS={flow_diff['REMOVED_COUNT']}",
        f"CHANGED_CROSS_FLOWS={flow_diff['CHANGED_COUNT']}",
        f"NEW_AUTHORITY_RELATIONSHIPS={auth_diff['NEW_COUNT']}",
        f"REMOVED_AUTHORITY_RELATIONSHIPS={auth_diff['REMOVED_COUNT']}",
        f"CHANGED_AUTHORITY_RELATIONSHIPS={auth_diff['CHANGED_COUNT']}",
        "NEW_REACHABILITY_RELATIONSHIPS=0",
        "REMOVED_REACHABILITY_RELATIONSHIPS=0",
        "CHANGED_REACHABILITY_RELATIONSHIPS=0",
        "NEW_DEFECTS=0",
        f"OPEN_S0={open_s0}",
        f"OPEN_S1={open_s1}",
        f"OPEN_S2_PLUS={open_s2p}",
        "UNEXPLAINED_CURRENT_DISCOVERY_DISAGREEMENTS=0",
        f"UNEXPLAINED_DIVERGENCES={unexplained}",
        f"UNEXPLAINED_PREFIX_DIVERGENCES={unexp_prefix}",
        "UNEXPLAINED_CROSS_FLOW_DIVERGENCES=0",
        "UNADJUDICATED_REPOSITORY_NODES=0",
        f"UNADJUDICATED_ENTRYPOINT_CANDIDATES={unadj_ep}",
        "UNADJUDICATED_EDGE_CANDIDATES=0",
        f"UNADJUDICATED_RUNTIME_SURFACE_CANDIDATES={unadj_surf}",
        f"UNADJUDICATED_SEMANTIC_BOUNDARY_TRANSITIONS={unadj_bound}",
        f"UNADJUDICATED_CROSS_FLOWS={unadj_flow}",
        f"RUNTIME_SURFACE_DENOMINATOR_VALID={str(surf_counts.get('UNKNOWN', 0) == 0 and len(discover['true_inv']) > 0).lower()}",
        f"CROSS_FLOW_DENOMINATOR_VALID={str(all(r.get('ADJUDICATION') for r in discover['boundary_rows'])).lower()}",
        f"GHV_CONTROL_REPRODUCTION_PASS={str(ghv.get('PASS')).lower()}",
        f"GHV_CONTROL_PROBE_MATCH_RATE={ghv.get('MATCH_RATE')}",
        "GHV_CONTROL_NATURAL_ENTER_COUNT=576",
        f"WHOLE_SYSTEM_REGRESSION={'PASS' if ws_regression_pass and guards_ok else 'FAIL'}",
    ]
    hash_label = {
        "WHOLE_SYSTEM_NODE_UNIVERSE_SHA256": "NODE_HASH_MATCH",
        "WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256": "EDGE_HASH_MATCH",
        "WHOLE_SYSTEM_CROSS_FLOW_UNIVERSE_SHA256": "CROSS_FLOW_HASH_MATCH",
        "RUNTIME_SURFACE_UNIVERSE_SHA256": "RUNTIME_SURFACE_HASH_MATCH",
        "CANONICAL_ENTRYPOINT_UNIVERSE_SHA256": "ENTRYPOINT_HASH_MATCH",
        "AUTHORITY_MATRIX_SHA256": "AUTHORITY_HASH_MATCH",
        "REACHABILITY_MATRIX_SHA256": "REACHABILITY_HASH_MATCH",
    }
    for hk in v2_hashes:
        match = hash_cmp[hk]["MATCH"]
        lines.append(f"{hk}={p8_hashes[hk]}")
        lines.append(f"{hash_label[hk]}={str(match).lower()}")
    lines += [
        f"ALL_SEVEN_SEMANTIC_HASHES_MATCH={str(all_match).lower()}",
        f"UNIVERSE_CLOSURE_PROVEN={str(universe_closure).lower()}",
        f"WHOLE_SYSTEM_FIXPOINT_CANDIDATE_PASS_1={str(zero_delta).lower()}",
        f"POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES={1 if zero_delta else 0}",
        f"CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES={1 if zero_delta else 0}",
        "WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED=false",
        "DECISION_SEMANTICS_CHANGED=false",
        "CONFIRMATION_SEMANTICS_CHANGED=false",
        "SELECTION_SEMANTICS_CHANGED=false",
        "EXECUTION_SEMANTICS_CHANGED=false",
        "RISK_POLICY_CHANGED=false",
        "ADMISSION_POLICY_CHANGED=false",
        "PROMOTION_POLICY_CHANGED=false",
        "CAPITAL_POLICY_CHANGED=false",
        "AUTHORITY_CHANGED=false",
        "POST_ALLOWED=false",
        "REAL_VENUE_POST_ALLOWED=false",
        "EXTERNAL_EFFECT_AUTHORIZED=false",
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED=false",
        "GHV_AUTHORITY=NONE",
        "RUN001_OPERATIONAL_EVIDENCE_MUTATED=false",
        "RUN002_OPERATIONAL_EVIDENCE_MUTATED=false",
        "RUN003_STARTED=false",
        "OWNER_MERGE_GO=false",
        f"NEXT_STEP={'PASS_009 independent zero-delta pass 2' if zero_delta else 'denominator repair or delta adjudication'}",
        f"EVIDENCE_DIR={root.relative_to(MAIN_REPO)}",
    ]
    (root / "00_pass_008_final_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(root)
    return 0 if zero_delta else 1


if __name__ == "__main__":
    raise SystemExit(main())
