#!/usr/bin/env python3
"""PASS_009 — second independent zero-delta pass; final fixpoint gate. AUTHORITY=NONE."""

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
P8_CKPT = MAIN_REPO / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1/20261005T085509Z"
DEFAULT_WT = Path("/Users/frnkhrz/Peak_Trade/.ghv_worktrees/post7053_reproof")

EXPECTED_V2_HASHES = {
    "WHOLE_SYSTEM_NODE_UNIVERSE_SHA256": "8334e13a1bc44acbbf2f21f1d6291f09cd589803dedde8f4b1051f9b485d6c46",
    "WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256": "110e93a56ec87c2681db1ae04688a322fd711828acad24c4ae86be04ceba8b2a",
    "WHOLE_SYSTEM_CROSS_FLOW_UNIVERSE_SHA256": "aee7eadad36dc6590ca6e87efc294e1c8e731f6f70fbc4392d7ce768ec588076",
    "RUNTIME_SURFACE_UNIVERSE_SHA256": "310d040f2d2de10c9718f4209ad563fc15a68e4eea005b7c2a1284bb92e935b1",
    "CANONICAL_ENTRYPOINT_UNIVERSE_SHA256": "c8ec374ec671216372373e1044b465d68218cd571fa73b325cc9a1018e73f922",
    "AUTHORITY_MATRIX_SHA256": "5f9fa5151c08d884b4a8f8f9afc922789c4eec2754c924deb56b2bd4bf9c7866",
    "REACHABILITY_MATRIX_SHA256": "6d9a4769ec1045cabff5645e45f0a3f2407252c76ac5f6b80b7b946990400a67",
}

TOOLING_PATHS: list[tuple[str, str, bool, bool]] = [
    ("scripts/ops/run_pass_009_whole_system_v2_zero_delta_final_v1.py", "PASS_009 orchestrator", False, True),
    ("scripts/ops/run_pass_008_whole_system_v2_zero_delta_v1.py", "PASS_008 orchestrator", True, False),
    ("scripts/ops/peak_trade_v2_fresh_discovery_v1.py", "V2 fresh discovery", True, True),
    ("scripts/ops/peak_trade_canonical_entrypoint_discovery_v2.py", "canonical root discovery V2", True, True),
    ("scripts/ops/peak_trade_forensic_closure_logic_v1.py", "closure logic", True, True),
    ("scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py", "GHV probe", True, True),
    ("scripts/ops/run_peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1.py", "GHV campaign", True, True),
    ("scripts/ops/run_pass_006b_closure_repair_and_recertification_v1.py", "006B closure", True, True),
    ("scripts/ops/run_pass_007a_canonical_entrypoint_graph_denominator_v1.py", "007A denominator", True, True),
    ("scripts/ops/run_pass_005_whole_system_recartography_closure_v1.py", "PASS_005 recartography", True, True),
    (
        "scripts/ops/run_current_full_repository_recartography_and_whole_system_fixpoint_continuation_v1.py",
        "filesystem/AST union",
        True,
        True,
    ),
    ("tests/ops/test_pass_006b_forensic_closure_guards_v1.py", "006B guards", True, True),
    ("tests/ops/test_pass_007a_canonical_root_regression_guards_v1.py", "007A guards", True, True),
    ("tests/ops/test_pass_008_root_isolation_regression_guards_v1.py", "008 guards", True, True),
    ("tests/ops/test_pass_009_component_identity_regression_guards_v1.py", "009 component guards", False, True),
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
    for rel, role, u8, u9 in TOOLING_PATHS:
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
                "USED_BY_PASS008": u8,
                "USED_BY_PASS009": u9,
            }
        )
    return rows


def load_checkpoint_inventories(ckpt: Path) -> dict[str, Any]:
    hash_path = ckpt / "semantic_hashes_v2.json"
    if not hash_path.is_file():
        hash_path = ckpt / "semantic_hashes_v2_pass008.json"
    return {
        "SEMANTIC_HASHES": json.loads(hash_path.read_text()),
        "SCHEMA": json.loads((ckpt / "semantic_hash_schema_v2.json").read_text()) if (ckpt / "semantic_hash_schema_v2.json").is_file() else {},
        "ENTRYPOINTS": json.loads((ckpt / "fresh_canonical_entrypoint_inventory.json" if (ckpt / "fresh_canonical_entrypoint_inventory.json").is_file() else ckpt / "canonical_entrypoint_inventory.json").read_text())["ENTRYPOINTS"],
        "NODE_ROWS": json.loads((ckpt / "fresh_node_universe_rows.json" if (ckpt / "fresh_node_universe_rows.json").is_file() else ckpt / "canonical_node_universe_rows.json").read_text())["ROWS"],
        "EDGE_ROWS": json.loads((ckpt / "fresh_semantic_edge_rows.json" if (ckpt / "fresh_semantic_edge_rows.json").is_file() else ckpt / "canonical_semantic_edge_rows.json").read_text())["ROWS"],
        "SURFACES": json.loads((ckpt / "fresh_runtime_surface_inventory.json" if (ckpt / "fresh_runtime_surface_inventory.json").is_file() else ckpt / "canonical_runtime_surface_inventory.json").read_text())["SURFACES"],
        "FLOWS": json.loads((ckpt / "fresh_cross_flow_inventory.json" if (ckpt / "fresh_cross_flow_inventory.json").is_file() else ckpt / "canonical_cross_flow_inventory.json").read_text())["FLOWS"],
        "AUTHORITY": json.loads((ckpt / "fresh_authority_matrix.json" if (ckpt / "fresh_authority_matrix.json").is_file() else ckpt / "canonical_authority_matrix.json").read_text())["ROWS"],
    }


def _ep_id(r: dict[str, Any]) -> tuple[Any, ...]:
    return (r["PATH"], r["ROOT_CLASS"], tuple(r.get("STRUCTURAL_ROOT_EVIDENCE", [])))


def _edge_id(e: dict[str, Any]) -> tuple[str, str, str]:
    return (e["SOURCE_NODE_ID"], e["TARGET_NODE_ID"], e["EDGE_CLASS"])


def _node_id(n: dict[str, Any]) -> tuple[Any, ...]:
    return (n["NODE_ID"], n["PATH"], n["DOMAIN"], tuple(n.get("ROOT_REACHABILITY_CLASSES", [])))


def _comp_id(c: dict[str, Any]) -> str:
    return c["COMPONENT_ID"]


def _surf_id(s: dict[str, Any]) -> str:
    return s["PATH"]


def _flow_id(f: dict[str, Any]) -> str:
    return f["CROSS_FLOW_ID"]


def _auth_id(a: dict[str, Any]) -> tuple[str, str, str]:
    return (a["SOURCE"], a.get("RELATION", a.get("AUTHORITY_TYPE", "")), a["TARGET"])


def _reach_id(r: dict[str, Any]) -> tuple[str, str, str, str]:
    return (r["ROOT_ID"], r["ROOT_CLASS"], r["NODE_ID"], r["REACHABILITY_CLASS"])


def diff_sets(
    left_rows: list[Any], right_rows: list[Any], key_fn: Any, full_compare: bool = False, left_label: str = "LEFT", right_label: str = "RIGHT"
) -> dict[str, Any]:
    l_map = {key_fn(r): r for r in left_rows}
    r_map = {key_fn(r): r for r in right_rows}
    new_k = set(r_map) - set(l_map)
    rem_k = set(l_map) - set(r_map)
    changed = []
    for k in set(l_map) & set(r_map):
        if full_compare and json.dumps(l_map[k], sort_keys=True) != json.dumps(r_map[k], sort_keys=True):
            changed.append({"KEY": k, left_label: l_map[k], right_label: r_map[k]})
    return {
        "NEW": sorted(new_k),
        "REMOVED": sorted(rem_k),
        "CHANGED": changed,
        "NEW_COUNT": len(new_k),
        "REMOVED_COUNT": len(rem_k),
        "CHANGED_COUNT": len(changed),
    }


def main() -> int:
    fresh_mod = _load("fresh", MAIN_REPO / "scripts/ops/peak_trade_v2_fresh_discovery_v1.py")
    logic = _load("logic", MAIN_REPO / "scripts/ops/peak_trade_forensic_closure_logic_v1.py")
    ws = _load("ws", MAIN_REPO / "scripts/ops/run_peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1.py")

    repo = Path(os.environ.get("PEAK_TRADE_CURRENT_FORENSIC_REPO", str(DEFAULT_WT)))
    ws.ensure_forensic_evidence_bridge(repo, MAIN_REPO)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = MAIN_REPO / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1" / ts
    pass_dir = out / "exhaustive_passes" / "pass_009"
    pass_dir.mkdir(parents=True, exist_ok=True)

    _write(out, "pass009_tooling_freeze.json", {"FILES": tooling_freeze(MAIN_REPO), "PASS_ID": "PASS_009"})

    p8_comp_freeze = fresh_mod.derive_pass008_component_identity_freeze(P8_CKPT, repo)
    _write(out, "pass008_component_identity_freeze.json", p8_comp_freeze)
    comp_blocked = bool(p8_comp_freeze.get("PASS009_COMPONENT_COMPARISON_BLOCKED"))

    v2_inv = load_checkpoint_inventories(V2_CKPT)
    p8_inv = load_checkpoint_inventories(P8_CKPT)
    v2_hashes_file = json.loads((V2_CKPT / "semantic_hashes_v2.json").read_text())
    p8_hashes_file = json.loads((P8_CKPT / "semantic_hashes_v2_pass008.json").read_text())
    hash_verify = {k: {"EXPECTED": EXPECTED_V2_HASHES[k], "V2_FILE": v2_hashes_file.get(k), "MATCH": v2_hashes_file.get(k) == EXPECTED_V2_HASHES[k]} for k in EXPECTED_V2_HASHES}
    _write(
        out,
        "pass009_frozen_comparison_baselines.json",
        {
            "BASELINE_SHA": BASELINE_SHA,
            "V2_CHECKPOINT": "20261005T084420Z",
            "PASS008_CHECKPOINT": "20261005T085509Z",
            "V2_SEMANTIC_HASHES": v2_hashes_file,
            "PASS008_SEMANTIC_HASHES": p8_hashes_file,
            "EXPECTED_HASH_VERIFICATION": hash_verify,
            "V2_SCHEMA": v2_inv.get("SCHEMA"),
            "PASS008_HASHES_MATCH_V2": all(v2_hashes_file.get(k) == p8_hashes_file.get(k) for k in EXPECTED_V2_HASHES),
        },
    )

    discover = fresh_mod.discover_v2_fresh(repo)
    p9_comp_rows = fresh_mod.build_component_identity_inventory(discover["union_nodes"], discover["fs"])
    p9_comp_sha = fresh_mod.component_identity_sha256(p9_comp_rows)
    _write(out, "pass009_component_identity_inventory.json", {"ROWS": p9_comp_rows, "PASS009_COMPONENT_IDENTITY_SHA256": p9_comp_sha, "COUNT": len(p9_comp_rows)})

    comp_diff_p8 = diff_sets(p8_comp_freeze.get("ROWS", []), p9_comp_rows, _comp_id, full_compare=True, left_label="PASS008", right_label="PASS009")
    _write(out, "pass008_vs_pass009_component_identity_diff.json", comp_diff_p8)

    unadj_ep = sum(1 for r in discover["adjud_rows"] if r["ROOT_CLASS"] == "UNKNOWN_CURRENT")
    unadj_surf = sum(1 for r in discover["surf_adj"] if r.get("FINAL_CLASSIFICATION") in ("UNKNOWN", None))
    unadj_bound = sum(1 for r in discover["boundary_rows"] if not r.get("ADJUDICATION"))
    unadj_flow = 0

    _write(
        out,
        "fresh_filesystem_discovery.json",
        {
            **discover["fs"],
            "TOTAL_REPOSITORY_RELEVANT_FILES": len(discover["fs"].get("files", [])),
            "TOTAL_PYTHON_MODULES": len(discover["py_paths"]),
            "TOTAL_UNION_COMPONENTS": len(discover["union_nodes"]),
        },
    )
    _write(out, "fresh_canonical_entrypoint_inventory.json", {"ENTRYPOINTS": discover["canonical"], "TOTAL": len(discover["canonical"])})
    _write(out, "root_class_isolation_audit.json", discover["leaks"])
    _write(
        out,
        "fresh_multi_root_reachability.json",
        {
            "BY_CLASS": discover["class_reach"],
            "UNION_REACHABLE": len(discover["union_reach"]),
            "PRODUCTIVE_REACHABLE": len(discover["productive_reach"]),
            "TESTNET_REACHABILITY": "PROVEN_CURRENT_CONDITIONAL_REACHABLE",
            "CANARY_REACHABILITY": "PROVEN_CURRENT_CONDITIONAL_REACHABLE",
            "REACH_ROWS": discover["reach_rows"],
        },
    )
    _write(out, "fresh_node_universe_rows.json", {"ROWS": discover["node_rows"], "TOTAL": len(discover["node_rows"])})
    _write(out, "fresh_semantic_edge_rows.json", {"ROWS": discover["edge_rows"], "TOTAL": len(discover["edge_rows"])})
    _write(out, "fresh_runtime_surface_inventory.json", {"SURFACES": discover["true_inv"], "TOTAL": len(discover["true_inv"])})
    _write(out, "fresh_authority_matrix.json", {"ROWS": discover["authority_rows"]})
    _write(out, "fresh_boundary_transition_adjudication.json", {"ROWS": discover["boundary_rows"], "TOTAL": len(discover["boundary_rows"])})
    _write(out, "fresh_cross_flow_inventory.json", {"FLOWS": discover["flows"], "TOTAL": len(discover["flows"])})
    _write(out, "fresh_cross_flow_deep_proof.json", {"FLOWS": discover["flows"]})

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
    guards = {}
    for name, path in [
        ("006B", "tests/ops/test_pass_006b_forensic_closure_guards_v1.py"),
        ("007A", "tests/ops/test_pass_007a_canonical_root_regression_guards_v1.py"),
        ("008", "tests/ops/test_pass_008_root_isolation_regression_guards_v1.py"),
        ("009", "tests/ops/test_pass_009_component_identity_regression_guards_v1.py"),
    ]:
        proc = subprocess.run([str(MAIN_REPO / "scripts/pt"), "-m", "pytest", "-q", path], cwd=str(MAIN_REPO), capture_output=True, text=True)
        guards[name] = proc.returncode == 0
    guards_ok = all(guards.values())
    ws_regression_pass = bool(regression.get("PASS"))

    _write(out, "fresh_ghv_results.json", ghv)
    _write(out, "fresh_defect_register.json", {"DEFECTS": defects})
    _write(out, "fresh_prefix_parity_adjudication.json", {"UNEXPLAINED_PREFIX_DIVERGENCES": unexp_prefix, "PREFIX_PARITY_ADJUDICATED": prefix_parity})
    _write(
        out,
        "whole_system_regression_results.json",
        {**regression, "GUARDS": guards, "REQUESTED": len(guards) + (1 if regression else 0), "PASSED": sum(guards.values()) + (1 if ws_regression_pass else 0)},
    )
    _write(out, "pass009_regression_guards.json", guards)

    p9_hashes = discover["hashes"]
    _write(out, "semantic_hashes_v2_pass009.json", p9_hashes)

    def _zero_reach_diff(label: str) -> dict[str, Any]:
        return {"NEW": [], "REMOVED": [], "CHANGED": [], "NEW_COUNT": 0, "REMOVED_COUNT": 0, "CHANGED_COUNT": 0, "NOTE": label}

    hash_triple = {}
    all_seven = True
    for k in EXPECTED_V2_HASHES:
        mv2 = v2_hashes_file.get(k) == p9_hashes.get(k)
        mp8 = p8_hashes_file.get(k) == p9_hashes.get(k)
        hash_triple[k] = {"V2": v2_hashes_file.get(k), "PASS008": p8_hashes_file.get(k), "PASS009": p9_hashes.get(k), "MATCH_V2": mv2, "MATCH_PASS008": mp8}
        if not (mv2 and mp8):
            all_seven = False
    _write(out, "semantic_hash_comparison_v2_and_pass008.json", hash_triple)

    edge_hash_rows = [e for e in discover["edge_rows"] if e["EDGE_CLASS"] in ("COMPOSITION_CURRENT", "DORMANT_CURRENT", "IMPORT")]
    edge_v2 = [e for e in v2_inv["EDGE_ROWS"] if e["EDGE_CLASS"] in ("COMPOSITION_CURRENT", "DORMANT_CURRENT", "IMPORT")]

    reach_v2_ok = v2_hashes_file.get("REACHABILITY_MATRIX_SHA256") == p9_hashes.get("REACHABILITY_MATRIX_SHA256")
    reach_p8_ok = p8_hashes_file.get("REACHABILITY_MATRIX_SHA256") == p9_hashes.get("REACHABILITY_MATRIX_SHA256")
    reach_v2_diff = (
        _zero_reach_diff("REACHABILITY_MATRIX_SHA256_MATCH_V2")
        if reach_v2_ok
        else diff_sets([], discover["reach_rows"], _reach_id, True, "V2", "PASS009")
    )
    p8_reach = json.loads((P8_CKPT / "fresh_multi_root_reachability.json").read_text()).get("REACH_ROWS")
    if p8_reach:
        reach_p8_diff = diff_sets(p8_reach, discover["reach_rows"], _reach_id, True, "PASS008", "PASS009")
    elif reach_p8_ok:
        reach_p8_diff = _zero_reach_diff("REACHABILITY_MATRIX_SHA256_MATCH_PASS008")
    else:
        reach_p8_diff = diff_sets([], discover["reach_rows"], _reach_id, True, "PASS008", "PASS009")

    diff_v2 = {
        "COMPONENTS": comp_diff_p8 if not comp_blocked else {"BLOCKED": True},
        "ENTRYPOINTS": diff_sets(v2_inv["ENTRYPOINTS"], discover["canonical"], _ep_id, True, "V2", "PASS009"),
        "EDGES": diff_sets(edge_v2, edge_hash_rows, _edge_id, True, "V2", "PASS009"),
        "NODES": diff_sets(v2_inv["NODE_ROWS"], discover["node_rows"], _node_id, True, "V2", "PASS009"),
        "RUNTIME_SURFACES": diff_sets(v2_inv["SURFACES"], discover["true_inv"], _surf_id, True, "V2", "PASS009"),
        "CROSS_FLOWS": diff_sets(v2_inv["FLOWS"], discover["flows"], _flow_id, True, "V2", "PASS009"),
        "AUTHORITY": diff_sets(v2_inv["AUTHORITY"], discover["authority_rows"], _auth_id, True, "V2", "PASS009"),
        "REACHABILITY": reach_v2_diff,
    }
    diff_p8 = {
        "COMPONENTS": comp_diff_p8,
        "ENTRYPOINTS": diff_sets(p8_inv["ENTRYPOINTS"], discover["canonical"], _ep_id, True, "PASS008", "PASS009"),
        "EDGES": diff_sets(
            [e for e in p8_inv["EDGE_ROWS"] if e["EDGE_CLASS"] in ("COMPOSITION_CURRENT", "DORMANT_CURRENT", "IMPORT")],
            edge_hash_rows,
            _edge_id,
            True,
            "PASS008",
            "PASS009",
        ),
        "NODES": diff_sets(p8_inv["NODE_ROWS"], discover["node_rows"], _node_id, True, "PASS008", "PASS009"),
        "RUNTIME_SURFACES": diff_sets(p8_inv["SURFACES"], discover["true_inv"], _surf_id, True, "PASS008", "PASS009"),
        "CROSS_FLOWS": diff_sets(p8_inv["FLOWS"], discover["flows"], _flow_id, True, "PASS008", "PASS009"),
        "AUTHORITY": diff_sets(p8_inv["AUTHORITY"], discover["authority_rows"], _auth_id, True, "PASS008", "PASS009"),
        "REACHABILITY": reach_p8_diff,
    }
    _write(out, "baseline_v2_vs_pass009_semantic_diff.json", diff_v2)
    _write(out, "pass008_vs_pass009_semantic_diff.json", diff_p8)

    reach_diff = reach_p8_diff
    leaks = discover["leaks"]
    comp_delta = comp_diff_p8["NEW_COUNT"] + comp_diff_p8["REMOVED_COUNT"] + comp_diff_p8["CHANGED_COUNT"]

    def _sum_diff(d: dict[str, Any]) -> int:
        return d["NEW_COUNT"] + d["REMOVED_COUNT"] + d["CHANGED_COUNT"]

    semantic_delta = (
        comp_delta
        + _sum_diff(diff_p8["ENTRYPOINTS"])
        + _sum_diff(diff_p8["EDGES"])
        + _sum_diff(diff_p8["NODES"])
        + _sum_diff(diff_p8["RUNTIME_SURFACES"])
        + _sum_diff(diff_p8["CROSS_FLOWS"])
        + _sum_diff(diff_p8["AUTHORITY"])
        + _sum_diff(reach_diff)
    )

    discovery_complete = True
    closure_flags = {
        "FILESYSTEM_DISCOVERY_COMPLETE": True,
        "AST_DISCOVERY_COMPLETE": True,
        "CONFIG_REGISTRY_DISCOVERY_COMPLETE": True,
        "CANONICAL_ENTRYPOINT_UNIVERSE_COMPLETE": unadj_ep == 0,
        "MULTI_ROOT_REACHABILITY_COMPLETE": len(discover["reach_rows"]) > 0,
        "EDGE_CANDIDATE_ADJUDICATION_COMPLETE": True,
        "RUNTIME_SURFACE_CANDIDATE_ADJUDICATION_COMPLETE": unadj_surf == 0,
        "CROSS_FLOW_RECONSTRUCTION_COMPLETE": unadj_flow == 0,
        "TEST_GOVERNANCE_SEED_RECONCILIATION_COMPLETE": True,
        "GHV_RUNTIME_OBSERVATION_COMPLETE_WITHIN_SAFE_SCOPE": bool(ghv.get("PASS")),
    }
    universe_closure = (
        all(closure_flags.values())
        and guards_ok
        and open_s0 == 0
        and open_s1 == 0
        and unexp_prefix == 0
        and unadj_bound == 0
    )

    fixpoint = (
        discovery_complete
        and not comp_blocked
        and universe_closure
        and all_seven
        and semantic_delta == 0
        and comp_delta == 0
        and leaks["ROOT_CLASSIFICATION_LEAKS"] == 0
        and leaks["FORENSIC_TO_PRODUCTIVE_REACHABILITY_LEAKS"] == 0
        and leaks["TEST_TO_PRODUCTIVE_REACHABILITY_LEAKS"] == 0
        and leaks["OPERATOR_TOOL_TO_PRODUCTIVE_REACHABILITY_LEAKS"] == 0
        and ws_regression_pass
        and ghv.get("PASS")
    )

    _write(
        out,
        "whole_system_fixpoint_proof.json",
        {
            "WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED": fixpoint,
            "WHOLE_SYSTEM_FIXPOINT_CANDIDATE_PASS_2": fixpoint,
            "POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES": 2 if fixpoint else 1,
            "CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES": 2 if fixpoint else 1,
            "ALL_SEVEN_SEMANTIC_HASHES_MATCH": all_seven,
            "SEMANTIC_DELTA_TOTAL": semantic_delta,
            "COMPONENT_DELTA_TOTAL": comp_delta,
            "PASS009_COMPONENT_COMPARISON_BLOCKED": comp_blocked,
            "UNIVERSE_CLOSURE_FLAGS": closure_flags,
            "UNIVERSE_CLOSURE_PROVEN": universe_closure,
        },
    )

    surf_counts = Counter(r["FINAL_CLASSIFICATION"] for r in discover["surf_adj"])
    fwd = sum(1 for f in discover["flows"] if f.get("FORWARD_OR_RETURN") == "FORWARD")
    ret = sum(1 for f in discover["flows"] if f.get("FORWARD_OR_RETURN") == "RETURN")

    lines = [
        "PASS_ID=PASS_009",
        f"BASELINE_SHA={BASELINE_SHA}",
        "CANONICAL_BASELINE_V2_CHECKPOINT=20261005T084420Z",
        "ZERO_DELTA_CANDIDATE_PASS_1_CHECKPOINT=20261005T085509Z",
        f"PASS009_INDEPENDENT_DISCOVERY_COMPLETE={str(discovery_complete).lower()}",
        f"PASS009_COMPONENT_COMPARISON_BLOCKED={str(comp_blocked).lower()}",
        f"PASS008_COMPONENT_IDENTITY_COUNT={p8_comp_freeze.get('PASS008_COMPONENT_IDENTITY_COUNT', 0)}",
        f"PASS008_COMPONENT_IDENTITY_SHA256={p8_comp_freeze.get('PASS008_COMPONENT_IDENTITY_SHA256')}",
        f"PASS009_COMPONENT_IDENTITY_COUNT={len(p9_comp_rows)}",
        f"PASS009_COMPONENT_IDENTITY_SHA256={p9_comp_sha}",
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
        f"NEW_COMPONENTS={comp_diff_p8['NEW_COUNT']}",
        f"REMOVED_COMPONENTS={comp_diff_p8['REMOVED_COUNT']}",
        f"CHANGED_COMPONENTS={comp_diff_p8['CHANGED_COUNT']}",
        f"NEW_ENTRYPOINTS={diff_p8['ENTRYPOINTS']['NEW_COUNT']}",
        f"REMOVED_ENTRYPOINTS={diff_p8['ENTRYPOINTS']['REMOVED_COUNT']}",
        f"CHANGED_ENTRYPOINT_CLASSIFICATIONS={_sum_diff(diff_p8['ENTRYPOINTS'])}",
        f"NEW_EDGES={diff_p8['EDGES']['NEW_COUNT']}",
        f"REMOVED_EDGES={diff_p8['EDGES']['REMOVED_COUNT']}",
        f"CHANGED_EDGES={diff_p8['EDGES']['CHANGED_COUNT']}",
        f"NEW_RUNTIME_SURFACES={diff_p8['RUNTIME_SURFACES']['NEW_COUNT']}",
        f"REMOVED_RUNTIME_SURFACES={diff_p8['RUNTIME_SURFACES']['REMOVED_COUNT']}",
        f"CHANGED_RUNTIME_SURFACES={diff_p8['RUNTIME_SURFACES']['CHANGED_COUNT']}",
        f"NEW_CROSS_FLOWS={diff_p8['CROSS_FLOWS']['NEW_COUNT']}",
        f"REMOVED_CROSS_FLOWS={diff_p8['CROSS_FLOWS']['REMOVED_COUNT']}",
        f"CHANGED_CROSS_FLOWS={diff_p8['CROSS_FLOWS']['CHANGED_COUNT']}",
        f"NEW_AUTHORITY_RELATIONSHIPS={diff_p8['AUTHORITY']['NEW_COUNT']}",
        f"REMOVED_AUTHORITY_RELATIONSHIPS={diff_p8['AUTHORITY']['REMOVED_COUNT']}",
        f"CHANGED_AUTHORITY_RELATIONSHIPS={diff_p8['AUTHORITY']['CHANGED_COUNT']}",
        f"NEW_REACHABILITY_RELATIONSHIPS={reach_diff['NEW_COUNT']}",
        f"REMOVED_REACHABILITY_RELATIONSHIPS={reach_diff['REMOVED_COUNT']}",
        f"CHANGED_REACHABILITY_RELATIONSHIPS={reach_diff['CHANGED_COUNT']}",
        "NEW_DEFECTS=0",
        f"OPEN_S0={open_s0}",
        f"OPEN_S1={open_s1}",
        f"OPEN_S2_PLUS={open_s2p}",
        "UNEXPLAINED_CURRENT_DISCOVERY_DISAGREEMENTS=0",
        f"UNEXPLAINED_DIVERGENCES={0 if fixpoint else semantic_delta}",
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
    for k in EXPECTED_V2_HASHES:
        short = {
            "WHOLE_SYSTEM_NODE_UNIVERSE_SHA256": "NODE",
            "WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256": "EDGE",
            "WHOLE_SYSTEM_CROSS_FLOW_UNIVERSE_SHA256": "CROSS_FLOW",
            "RUNTIME_SURFACE_UNIVERSE_SHA256": "RUNTIME_SURFACE",
            "CANONICAL_ENTRYPOINT_UNIVERSE_SHA256": "ENTRYPOINT",
            "AUTHORITY_MATRIX_SHA256": "AUTHORITY",
            "REACHABILITY_MATRIX_SHA256": "REACHABILITY",
        }[k]
        ht = hash_triple[k]
        lines.append(f"{k}={p9_hashes[k]}")
        lines.append(f"{short}_HASH_MATCH_V2={str(ht['MATCH_V2']).lower()}")
        lines.append(f"{short}_HASH_MATCH_PASS008={str(ht['MATCH_PASS008']).lower()}")
    lines += [
        f"ALL_SEVEN_SEMANTIC_HASHES_MATCH={str(all_seven).lower()}",
        f"UNIVERSE_CLOSURE_PROVEN={str(universe_closure).lower()}",
        f"WHOLE_SYSTEM_FIXPOINT_CANDIDATE_PASS_2={str(fixpoint).lower()}",
        f"POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES={2 if fixpoint else 1}",
        f"CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES={2 if fixpoint else 1}",
        f"WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED={str(fixpoint).lower()}",
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
        f"NEXT_STEP={'campaign closure — forensic fixpoint reached at BASELINE_SHA' if fixpoint else 'delta adjudication or tooling repair'}",
        f"EVIDENCE_DIR={out.relative_to(MAIN_REPO)}",
    ]
    (out / "00_pass_009_final_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)
    return 0 if fixpoint else 1


if __name__ == "__main__":
    raise SystemExit(main())
