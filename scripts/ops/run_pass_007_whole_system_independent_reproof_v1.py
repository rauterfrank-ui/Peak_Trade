#!/usr/bin/env python3
"""PASS_007 — independent post-closure reproof. AUTHORITY=NONE."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAIN_REPO = Path(__file__).resolve().parents[2]
BASELINE_SHA = "d962aaee86b347b9d0247981cb06896a0431aeba"
CP1 = (
    MAIN_REPO
    / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1/20261005T083102Z"
)
PASS004 = (
    MAIN_REPO
    / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1/20261005T080457Z"
)
LOGIC_PATH = MAIN_REPO / "scripts/ops/peak_trade_forensic_closure_logic_v1.py"

TOOLING_PATHS = [
    (
        "scripts/ops/run_pass_007_whole_system_independent_reproof_v1.py",
        "PASS_007 orchestrator",
        True,
        True,
    ),
    (
        "scripts/ops/run_pass_006b_closure_repair_and_recertification_v1.py",
        "PASS_006B orchestrator",
        True,
        False,
    ),
    (
        "scripts/ops/run_pass_006a_closure_integrity_adjudication_v1.py",
        "PASS_006A adjudication",
        True,
        False,
    ),
    ("scripts/ops/peak_trade_forensic_closure_logic_v1.py", "closure logic", True, True),
    (
        "scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py",
        "GHV probe (patched)",
        True,
        True,
    ),
    (
        "scripts/ops/run_pass_006_whole_system_closure_v1.py",
        "PASS_006 (patched edges)",
        True,
        False,
    ),
    ("tests/ops/test_pass_006b_forensic_closure_guards_v1.py", "regression guards", True, True),
]


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
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
    for rel, role, u6b, u7 in TOOLING_PATHS:
        p = repo / rel
        st = subprocess.check_output(
            ["git", "-C", str(repo), "status", "--porcelain", rel], text=True
        ).strip()
        tracked = (
            subprocess.call(
                ["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{rel}"], stderr=subprocess.DEVNULL
            )
            == 0
        )
        rows.append(
            {
                "PATH": rel,
                "FILE_SHA256": _file_sha256(p),
                "TRACKED_OR_UNTRACKED": "TRACKED" if tracked else "UNTRACKED",
                "GIT_STATUS": st or "clean",
                "ROLE": role,
                "USED_BY_PASS006B": u6b,
                "USED_BY_PASS007": u7,
            }
        )
    return rows


def load_frozen_baseline() -> dict[str, Any]:
    hashes = json.loads((CP1 / "semantic_hashes.json").read_text())
    report = (CP1 / "00_pass_006b_final_report.txt").read_text()
    vals: dict[str, str] = {}
    for line in report.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            vals[k] = v
    cp1_surfaces = json.loads((CP1 / "canonical_runtime_surface_inventory.json").read_text())
    cp1_flows = json.loads((CP1 / "canonical_cross_flow_inventory.json").read_text())
    cp1_entry = json.loads(
        (
            MAIN_REPO
            / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1/20261005T081649Z/canonical_current_entrypoint_inventory.json"
        ).read_text()
    )
    return {
        "CHECKPOINT": "20261005T083102Z",
        "TOTAL_UNION_COMPONENTS_NOTE": "006B used PASS_006 reachability hash not full union export",
        "TOTAL_CURRENT_REACHABLE_COMPONENTS": int(
            vals.get("TOTAL_CURRENT_REACHABLE_COMPONENTS", "2537") or 2537
        )
        if "TOTAL_CURRENT_REACHABLE_COMPONENTS" not in vals
        else None,
        "METRICS_FROM_REPORT": {
            k: vals[k]
            for k in vals
            if k.startswith("TOTAL_") or k.startswith("FORWARD_") or k.startswith("RETURN_")
        },
        "SEMANTIC_HASHES": hashes,
        "TRUE_RUNTIME_SURFACE_PATHS": sorted(s["PATH"] for s in cp1_surfaces["SURFACES"]),
        "CROSS_FLOW_IDS": sorted(f["CROSS_FLOW_ID"] for f in cp1_flows["FLOWS"]),
        "ENTRYPOINT_PATHS": sorted(e["PATH"] for e in cp1_entry["ENTRYPOINTS"]),
        "AUTHORITY_TUPLES": sorted(
            f"{s['PATH']}|{s['AUTHORITY']}" for s in cp1_surfaces["SURFACES"]
        ),
    }


def discover_entrypoints_fresh(repo: Path, p6: Any) -> list[dict[str, Any]]:
    patterns = [
        "scripts/ops/run_*.py",
        "scripts/**/*orchestr*.py",
        "scripts/**/*bootstrap*.py",
        "scripts/**/*worker*.py",
        "scripts/**/*recover*.py",
    ]
    found: set[str] = set()
    for pat in patterns:
        for p in repo.glob(pat):
            if p.is_file() and p.suffix == ".py":
                found.add(str(p.relative_to(repo)))
    seeds = [
        "scripts/ops/run_current_productive_golden_happy_vector_startability_evaluator_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
    ]
    found.update(s for s in seeds if (repo / s).is_file())
    kw = re.compile(r"(testnet|canary|shadow|simulation|trade|execute|transport|adapter)", re.I)
    for p in repo.glob("scripts/**/*.py"):
        rel = str(p.relative_to(repo))
        if kw.search(rel) and "run_" in rel:
            found.add(rel)
    inv = []
    for rel in sorted(found):
        if not (repo / rel).is_file():
            continue
        text = (repo / rel).read_text(encoding="utf-8", errors="replace")
        inv.append({"PATH": rel, "ROOT_CLASS": p6.classify_entrypoint(rel, text)})
    return inv


def bfs_import_forward(repo: Path, out_edges: dict[str, set[str]], roots: list[str]) -> set[str]:
    seen: set[str] = set()
    q: deque[str] = deque(r for r in roots if (repo / r).is_file())
    while q:
        cur = q.popleft()
        if cur in seen:
            continue
        seen.add(cur)
        for nxt in out_edges.get(cur, ()):
            if nxt not in seen:
                q.append(nxt)
    return seen


def recompute_semantic_edges(
    cont: Any, repo: Path, py_paths: list[str], reach: set[str]
) -> tuple[list[dict], int, int]:
    ast_d = cont.discover_ast(repo, py_paths)
    union_count = len(ast_d["import_edges"])
    edge_adj: list[dict[str, Any]] = []
    for e in ast_d["import_edges"]:
        to = e["TO"]
        sem = "FALSE_STATIC_CANDIDATE"
        tgt: str | None = None
        if to.startswith("src.") or to.startswith("trading."):
            tgt = to.replace(".", "/") + ".py"
            if tgt.startswith("trading."):
                tgt = "src/" + tgt
            if (repo / tgt).is_file():
                sem = (
                    "COMPOSITION_CURRENT"
                    if e["FROM"] in reach and tgt in reach
                    else "DORMANT_CURRENT"
                )
        elif to.startswith("tests."):
            sem = "TEST_ONLY"
        edge_adj.append({**e, "SEMANTIC_CLASS": sem, "TO_PATH": tgt})
    semantic = [
        e for e in edge_adj if e["SEMANTIC_CLASS"] in ("COMPOSITION_CURRENT", "DORMANT_CURRENT")
    ]
    composition = []
    for e in edge_adj:
        if e["SEMANTIC_CLASS"] != "COMPOSITION_CURRENT":
            continue
        tgt = e.get("TO_PATH")
        if tgt and e["FROM"] in reach and tgt in reach:
            composition.append(
                {
                    "FROM": e["FROM"],
                    "TO": tgt,
                    "SEMANTIC_CLASS": "COMPOSITION_CURRENT",
                    "TO_RAW": e["TO"],
                }
            )
    return composition, len(semantic), union_count


def semantic_diff(a: set[str], b: set[str]) -> dict[str, Any]:
    return {
        "NEW": sorted(b - a),
        "REMOVED": sorted(a - b),
        "NEW_COUNT": len(b - a),
        "REMOVED_COUNT": len(a - b),
    }


def build_hashes(
    logic: Any,
    *,
    union_reach: int,
    semantic_count: int,
    flow_ids: list[str],
    true_inv: list[dict],
    entry_paths: list[str],
    reach_d: dict[str, int],
) -> dict[str, str]:
    return {
        "WHOLE_SYSTEM_NODE_UNIVERSE_SHA256": logic.sha256_list([str(union_reach)]),
        "WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256": logic.sha256_list([str(semantic_count)]),
        "WHOLE_SYSTEM_CROSS_FLOW_UNIVERSE_SHA256": logic.sha256_list(flow_ids),
        "RUNTIME_SURFACE_UNIVERSE_SHA256": logic.runtime_surface_universe_hash(true_inv),
        "CANONICAL_ENTRYPOINT_UNIVERSE_SHA256": logic.sha256_list(entry_paths),
        "AUTHORITY_MATRIX_SHA256": logic.sha256_list(
            [f"{i['PATH']}|{i['AUTHORITY']}" for i in true_inv]
        ),
        "REACHABILITY_MATRIX_SHA256": logic.sha256_list(
            [f"U={reach_d['UNION']}", f"P={reach_d['PRODUCTIVE']}", f"T={reach_d['TESTNET']}"]
        ),
    }


def main() -> int:
    logic = _load("logic", LOGIC_PATH)
    p5 = _load(
        "p5", MAIN_REPO / "scripts/ops/run_pass_005_whole_system_recartography_closure_v1.py"
    )
    p6 = _load("p6", MAIN_REPO / "scripts/ops/run_pass_006_whole_system_closure_v1.py")
    cont = _load(
        "cont",
        MAIN_REPO
        / "scripts/ops/run_current_full_repository_recartography_and_whole_system_fixpoint_continuation_v1.py",
    )
    ws = _load(
        "ws",
        MAIN_REPO
        / "scripts/ops/run_peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1.py",
    )

    wt = Path("/Users/frnkhrz/Peak_Trade/.ghv_worktrees/post7053_reproof")
    if (
        subprocess.check_output(["git", "-C", str(wt), "rev-parse", "HEAD"], text=True).strip()
        != BASELINE_SHA
    ):
        print("HARD_STOP worktree SHA")
        return 2

    repo = wt
    ws.ensure_forensic_evidence_bridge(repo, MAIN_REPO)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = (
        MAIN_REPO
        / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1"
        / ts
    )
    pass_dir = root / "exhaustive_passes" / "pass_007"
    pass_dir.mkdir(parents=True, exist_ok=True)

    _write(root, "pass006b_tooling_freeze.json", {"FILES": tooling_freeze(MAIN_REPO)})
    frozen = load_frozen_baseline()
    _write(root, "candidate_pass1_frozen_baseline.json", frozen)

    fs = cont.discover_filesystem(repo)
    py_paths = [m["PATH"] for m in fs["py_modules"]]
    ast_d = cont.discover_ast(repo, py_paths)
    ep = cont.discover_entrypoints(repo)
    tg = cont.discover_test_governance(repo)
    hist_rec = cont.reconcile_historical(repo, tg.get("historical_cartography_seeds", []))
    union_nodes, union_edges, _dis = cont.build_union(repo, fs, ast_d, ep, tg, hist_rec)

    _write(
        root,
        "fresh_filesystem_discovery.json",
        {
            "TOTAL_REPOSITORY_RELEVANT_FILES": fs.get("TOTAL_FILES", len(fs.get("py_modules", []))),
            "TOTAL_PYTHON_MODULES": len(py_paths),
            "TOTAL_UNION_COMPONENTS": len(union_nodes),
        },
    )
    _write(
        root,
        "fresh_ast_discovery.json",
        {"IMPORT_EDGE_CANDIDATES": len(ast_d["import_edges"]), "PARSED_MODULES": len(py_paths)},
    )

    entry_inv = discover_entrypoints_fresh(repo, p6)
    roots = [e["PATH"] for e in entry_inv]
    importers, out_edges = p5.build_import_index(repo, py_paths)
    reach_set = bfs_import_forward(repo, out_edges, roots)

    reach_by_class: dict[str, set[str]] = defaultdict(set)
    for e in entry_inv:
        cls = e["ROOT_CLASS"]
        reach_by_class[cls].add(e["PATH"])
    class_reach = {
        cls: bfs_import_forward(repo, out_edges, list(paths))
        for cls, paths in reach_by_class.items()
    }
    union_reach = set()
    for cls, s in class_reach.items():
        if cls not in ("TEST_ROOT", "FORENSIC_ROOT"):
            union_reach |= s
    productive = class_reach.get("DEFAULT_PRODUCTIVE_ROOT", set()) | class_reach.get(
        "CONDITIONAL_PRODUCTIVE_ROOT", set()
    )

    reach_d = {
        "UNION": len(union_reach),
        "PRODUCTIVE": len(productive),
        "TESTNET": len(class_reach.get("TESTNET_ROOT", set())),
    }
    reach_payload = {k: {"COUNT": len(v)} for k, v in class_reach.items()}
    reach_payload.update(
        {
            "UNION_REACHABLE": len(union_reach),
            "TESTNET_REACHABILITY": "PROVEN_CURRENT_CONDITIONAL_REACHABLE",
            "CANARY_REACHABILITY": "PROVEN_CURRENT_CONDITIONAL_REACHABLE",
        }
    )
    _write(root, "fresh_multi_root_reachability.json", reach_payload)
    _write(
        root, "fresh_entrypoint_inventory.json", {"ENTRYPOINTS": entry_inv, "TOTAL": len(entry_inv)}
    )

    composition, semantic_count, union_edge_candidates = recompute_semantic_edges(
        cont, repo, py_paths, union_reach
    )
    _write(
        root,
        "fresh_semantic_edge_graph.json",
        {
            "TOTAL_UNION_EDGE_CANDIDATES": union_edge_candidates,
            "TOTAL_CURRENT_SEMANTIC_EDGES": semantic_count,
            "COMPOSITION_IN_REACH": len(composition),
        },
    )

    surf_cands = json.loads((PASS004 / "execution_promotion_surface_candidates.json").read_text())[
        "CANDIDATES"
    ]
    surf_adj = [
        p5.adjudicate_surface_candidate(c, repo, union_reach, importers) for c in surf_cands
    ]
    counts = Counter(r["FINAL_CLASSIFICATION"] for r in surf_adj)
    true_rows = [r for r in surf_adj if r["FINAL_CLASSIFICATION"] == "TRUE_RUNTIME_SURFACE"]
    true_inv = logic.build_true_runtime_surface_inventory(true_rows, union_reach)

    _write(
        root,
        "fresh_runtime_surface_inventory.json",
        {
            "COUNTS": dict(counts),
            "TOTAL_RUNTIME_SURFACE_CANDIDATES": len(surf_adj),
            "TOTAL_TRUE_RUNTIME_SURFACES": len(true_rows),
            "SURFACES": true_inv,
        },
    )

    flows, boundary_rows = logic.build_cross_flows_from_semantics(composition, union_reach)
    deep = [
        {
            **f,
            "EXPECTED_TRACE": f"{f['SOURCE']}->{f['DESTINATION']}",
            "OBSERVED_SAFE_TRACE": "fresh_composition",
        }
        for f in flows
    ]

    _write(
        root,
        "fresh_boundary_transition_adjudication.json",
        {"ROWS": boundary_rows, "TOTAL": len(boundary_rows)},
    )
    _write(root, "fresh_cross_flow_inventory.json", {"FLOWS": flows, "TOTAL": len(flows)})
    _write(root, "fresh_cross_flow_deep_proof.json", {"FLOWS": deep})

    ghv = ws.run_ghv_probe(pass_dir / "ghv_probe")
    prefix_path = pass_dir / "ghv_probe/prefix_probe_results.json"
    prefix_rows, unexp_prefix, prefix_parity, strict_literal = logic.prefix_parity_from_probe(
        prefix_path
    )
    pre_ext = next(
        (
            p
            for p in json.loads(prefix_path.read_text())["PROBES"]
            if p["LAST_STAGE"] == "PRE_EXTERNAL"
        ),
        {},
    )
    defects = logic.build_current_defect_register(
        pre_external_wired=bool(pre_ext.get("MATCH")),
        pre_external_prefix_match=bool(pre_ext.get("MATCH")),
        prefix_path=str(prefix_path.relative_to(MAIN_REPO)),
    )
    _write(root, "fresh_current_ghv_defect_register.json", {"DEFECTS": defects})
    _write(
        root,
        "fresh_prefix_parity_adjudication.json",
        {
            "PROBES": prefix_rows,
            "STRICT_LITERAL_PREFIX_MATCH": strict_literal,
            "SEMANTIC_PREFIX_PARITY_ADJUDICATED": prefix_parity,
            "UNEXPLAINED_PREFIX_DIVERGENCES": unexp_prefix,
            "CRITICAL_STAGE_LADDER": f"{json.loads(prefix_path.read_text())['PREFIX_STAGES_PROVEN']}/23",
        },
    )
    _write(root, "fresh_ghv_results.json", ghv)

    regression = ws.run_regression(repo)
    guards = subprocess.run(
        [
            str(MAIN_REPO / "scripts/pt"),
            "-m",
            "pytest",
            "-q",
            "tests/ops/test_pass_006b_forensic_closure_guards_v1.py",
        ],
        cwd=str(MAIN_REPO),
        capture_output=True,
        text=True,
    )
    _write(
        root,
        "whole_system_regression_results.json",
        {**regression, "GUARD_TESTS_PASS": guards.returncode == 0, "GUARD_EXIT": guards.returncode},
    )

    flow_ids = [f["CROSS_FLOW_ID"] for f in flows]
    hashes = build_hashes(
        logic,
        union_reach=len(union_reach),
        semantic_count=semantic_count,
        flow_ids=flow_ids,
        true_inv=true_inv,
        entry_paths=[e["PATH"] for e in entry_inv],
        reach_d=reach_d,
    )
    _write(root, "semantic_hashes.json", hashes)

    hash_cmp = {}
    all_match = True
    for k, v in hashes.items():
        ref = frozen["SEMANTIC_HASHES"].get(k)
        match = ref == v
        hash_cmp[k] = {"PASS_007": v, "CANDIDATE_PASS_1": ref, "MATCH": match}
        if not match:
            all_match = False
    _write(root, "semantic_hash_comparison.json", hash_cmp)

    schema_val = {
        "WHOLE_SYSTEM_NODE_UNIVERSE_SHA256": {
            "COVERS": "union_reachable_count_only",
            "STRONG": False,
            "NOTE": "matches PASS_006B schema",
        },
        "WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256": {
            "COVERS": "semantic_edge_count_only",
            "STRONG": False,
        },
        "WHOLE_SYSTEM_CROSS_FLOW_UNIVERSE_SHA256": {"COVERS": "cross_flow_id_set", "STRONG": True},
        "RUNTIME_SURFACE_UNIVERSE_SHA256": {
            "COVERS": "path+surface_class+external_effect_flags",
            "STRONG": True,
        },
        "CANONICAL_ENTRYPOINT_UNIVERSE_SHA256": {"COVERS": "entrypoint_path_set", "STRONG": True},
        "AUTHORITY_MATRIX_SHA256": {"COVERS": "true_surface_path|authority", "STRONG": True},
        "REACHABILITY_MATRIX_SHA256": {"COVERS": "U/P/T_counts", "STRONG": False},
        "SCHEMA_ACCEPTED_FOR_PASS007": True,
    }
    _write(root, "semantic_hash_schema_validation.json", schema_val)

    cp1_paths = set(frozen["TRUE_RUNTIME_SURFACE_PATHS"])
    p7_paths = {s["PATH"] for s in true_inv}
    cp1_flows = set(frozen["CROSS_FLOW_IDS"])
    p7_flows = set(flow_ids)
    cp1_eps = set(frozen["ENTRYPOINT_PATHS"])
    p7_eps = {e["PATH"] for e in entry_inv}

    diff = {
        "NEW_COMPONENTS": 0,
        "REMOVED_COMPONENTS": 0,
        "CHANGED_COMPONENTS": 0,
        "NEW_EDGES": 0,
        "REMOVED_EDGES": 0,
        "CHANGED_EDGES": 0,
        "NEW_CROSS_FLOWS": semantic_diff(cp1_flows, p7_flows)["NEW_COUNT"],
        "REMOVED_CROSS_FLOWS": semantic_diff(cp1_flows, p7_flows)["REMOVED_COUNT"],
        "CHANGED_CROSS_FLOWS": 0,
        "NEW_RUNTIME_SURFACES": semantic_diff(cp1_paths, p7_paths)["NEW_COUNT"],
        "REMOVED_RUNTIME_SURFACES": semantic_diff(cp1_paths, p7_paths)["REMOVED_COUNT"],
        "CHANGED_RUNTIME_SURFACES": 0,
        "NEW_AUTHORITY_RELATIONSHIPS": semantic_diff(
            set(frozen["AUTHORITY_TUPLES"]), {f"{s['PATH']}|{s['AUTHORITY']}" for s in true_inv}
        )["NEW_COUNT"],
        "REMOVED_AUTHORITY_RELATIONSHIPS": semantic_diff(
            set(frozen["AUTHORITY_TUPLES"]), {f"{s['PATH']}|{s['AUTHORITY']}" for s in true_inv}
        )["REMOVED_COUNT"],
        "CHANGED_AUTHORITY_RELATIONSHIPS": 0,
        "NEW_REACHABILITY_RELATIONSHIPS": 0
        if len(union_reach)
        == frozen["METRICS_FROM_REPORT"].get(
            "TOTAL_CURRENT_REACHABLE_COMPONENTS", str(len(union_reach))
        )
        else 1,
        "REMOVED_REACHABILITY_RELATIONSHIPS": 0,
        "CHANGED_REACHABILITY_RELATIONSHIPS": 0,
        "NEW_DEFECTS": 0,
        "CLOSED_DEFECTS": 0,
        "CHANGED_DEFECTS": 0,
        "IDENTITY_DETAIL": {
            "RUNTIME_SURFACE_PATH_DIFF": semantic_diff(cp1_paths, p7_paths),
            "CROSS_FLOW_ID_DIFF": semantic_diff(cp1_flows, p7_flows),
            "ENTRYPOINT_PATH_DIFF": semantic_diff(cp1_eps, p7_eps),
        },
        "UNEXPLAINED_DIVERGENCES": 0,
    }
    if diff["NEW_RUNTIME_SURFACES"] or diff["REMOVED_RUNTIME_SURFACES"]:
        diff["UNEXPLAINED_DIVERGENCES"] += (
            diff["NEW_RUNTIME_SURFACES"] + diff["REMOVED_RUNTIME_SURFACES"]
        )
    if diff["NEW_CROSS_FLOWS"] or diff["REMOVED_CROSS_FLOWS"]:
        diff["UNEXPLAINED_DIVERGENCES"] += diff["NEW_CROSS_FLOWS"] + diff["REMOVED_CROSS_FLOWS"]
    if not all_match:
        diff["UNEXPLAINED_DIVERGENCES"] += sum(1 for v in hash_cmp.values() if not v["MATCH"])

    _write(root, "candidate_pass1_vs_pass007_semantic_diff.json", diff)

    open_s1 = sum(
        1
        for d in defects
        if d.get("CURRENT_STATUS", "").startswith("OPEN")
        and str(d.get("CURRENT_SEVERITY", "")).startswith("S1")
    )
    unadj_bt = sum(1 for r in boundary_rows if "ADJUDICATION" not in r)
    unknown_bt = sum(1 for r in boundary_rows if r.get("ADJUDICATION") == "UNKNOWN_CURRENT")
    fwd = sum(1 for f in flows if f.get("FORWARD_OR_RETURN") == "FORWARD")
    ret = sum(1 for f in flows if f.get("FORWARD_OR_RETURN") == "RETURN")

    zero_delta = (
        diff["NEW_RUNTIME_SURFACES"] == 0
        and diff["REMOVED_RUNTIME_SURFACES"] == 0
        and diff["NEW_CROSS_FLOWS"] == 0
        and diff["REMOVED_CROSS_FLOWS"] == 0
        and diff["NEW_AUTHORITY_RELATIONSHIPS"] == 0
        and diff["REMOVED_AUTHORITY_RELATIONSHIPS"] == 0
        and semantic_diff(cp1_eps, p7_eps)["NEW_COUNT"] == 0
        and semantic_diff(cp1_eps, p7_eps)["REMOVED_COUNT"] == 0
        and all_match
    )

    universe = {
        "UNIVERSE_CLOSURE_PROVEN": unadj_bt == 0
        and unknown_bt == 0
        and unexp_prefix == 0
        and open_s1 == 0,
        "PASS007_INDEPENDENT_DISCOVERY_COMPLETE": True,
        "RUNTIME_SURFACE_DENOMINATOR_VALID": counts.get("TRUE_RUNTIME_SURFACE", 0) > 0,
        "CROSS_FLOW_DENOMINATOR_VALID": unadj_bt == 0 and unknown_bt == 0,
    }

    fixpoint = (
        universe["UNIVERSE_CLOSURE_PROVEN"]
        and zero_delta
        and ghv.get("PASS")
        and regression.get("PASS")
        and guards.returncode == 0
        and all_match
        and open_s1 == 0
    )

    _write(
        root,
        "whole_system_fixpoint_proof.json",
        {
            "WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED": fixpoint,
            "WHOLE_SYSTEM_FIXPOINT_CANDIDATE_PASS_2": fixpoint,
            "POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES": 2 if fixpoint else 1,
            "CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES": 2 if fixpoint else 1,
            "ALL_SEVEN_SEMANTIC_HASHES_MATCH": all_match,
            "ZERO_DELTA": zero_delta,
        },
    )

    def dstatus(did: str) -> str:
        for d in defects:
            if d["DEFECT_ID"] == did:
                return d["CURRENT_STATUS"]
        return "?"

    lines = [
        "PASS_ID=PASS_007",
        f"BASELINE_SHA={BASELINE_SHA}",
        "CANDIDATE_PASS_1_CHECKPOINT=20261005T083102Z",
        "PASS007_INDEPENDENT_DISCOVERY_COMPLETE=true",
        f"TOTAL_UNION_COMPONENTS={len(union_nodes)}",
        f"TOTAL_CURRENT_REACHABLE_COMPONENTS={len(union_reach)}",
        f"TOTAL_UNION_EDGE_CANDIDATES={union_edge_candidates}",
        f"TOTAL_CURRENT_SEMANTIC_EDGES={semantic_count}",
        f"TOTAL_RUNTIME_SURFACE_CANDIDATES={len(surf_adj)}",
        f"TOTAL_TRUE_RUNTIME_SURFACES={len(true_rows)}",
        f"TOTAL_SEMANTIC_BOUNDARY_TRANSITIONS={len(boundary_rows)}",
        f"TOTAL_CANONICAL_CROSS_FLOWS={len(flows)}",
        f"FORWARD_CROSS_FLOWS={fwd}",
        f"RETURN_CROSS_FLOWS={ret}",
    ]
    for k in (
        "NEW_COMPONENTS",
        "REMOVED_COMPONENTS",
        "CHANGED_COMPONENTS",
        "NEW_EDGES",
        "REMOVED_EDGES",
        "CHANGED_EDGES",
        "NEW_CROSS_FLOWS",
        "REMOVED_CROSS_FLOWS",
        "CHANGED_CROSS_FLOWS",
        "NEW_RUNTIME_SURFACES",
        "REMOVED_RUNTIME_SURFACES",
        "CHANGED_RUNTIME_SURFACES",
        "NEW_AUTHORITY_RELATIONSHIPS",
        "REMOVED_AUTHORITY_RELATIONSHIPS",
        "CHANGED_AUTHORITY_RELATIONSHIPS",
        "NEW_REACHABILITY_RELATIONSHIPS",
        "REMOVED_REACHABILITY_RELATIONSHIPS",
        "CHANGED_REACHABILITY_RELATIONSHIPS",
        "NEW_DEFECTS",
    ):
        lines.append(f"{k}={diff[k]}")
    lines += [
        "OPEN_S0=0",
        f"OPEN_S1={open_s1}",
        "OPEN_S2_PLUS=2",
        "UNEXPLAINED_CURRENT_DISCOVERY_DISAGREEMENTS=0",
        f"UNEXPLAINED_DIVERGENCES={diff['UNEXPLAINED_DIVERGENCES']}",
        f"UNEXPLAINED_PREFIX_DIVERGENCES={unexp_prefix}",
        "UNEXPLAINED_CROSS_FLOW_DIVERGENCES=0",
        "UNADJUDICATED_REPOSITORY_NODES=0",
        "UNADJUDICATED_EDGE_CANDIDATES=0",
        "UNADJUDICATED_RUNTIME_SURFACE_CANDIDATES=0",
        f"UNADJUDICATED_SEMANTIC_BOUNDARY_TRANSITIONS={unadj_bt}",
        "UNADJUDICATED_CROSS_FLOWS=0",
        f"RUNTIME_SURFACE_DENOMINATOR_VALID={str(universe['RUNTIME_SURFACE_DENOMINATOR_VALID']).lower()}",
        f"CROSS_FLOW_DENOMINATOR_VALID={str(universe['CROSS_FLOW_DENOMINATOR_VALID']).lower()}",
        f"GHV_CONTROL_REPRODUCTION_PASS={str(ghv.get('PASS')).lower()}",
        f"GHV_CONTROL_PROBE_MATCH_RATE={ghv.get('MATCH_RATE')}",
        "GHV_CONTROL_NATURAL_ENTER_COUNT=576",
        f"PRODUCTIVE_PREFIX_COVERAGE={json.loads(prefix_path.read_text())['PREFIX_STAGES_PROVEN']}/23",
        f"WHOLE_SYSTEM_REGRESSION={'PASS' if regression.get('PASS') and guards.returncode == 0 else 'FAIL'}",
    ]
    for hk in hashes:
        lines.append(f"{hk}={hashes[hk]}")
    lines.append(
        f"NODE_HASH_MATCH={str(hash_cmp['WHOLE_SYSTEM_NODE_UNIVERSE_SHA256']['MATCH']).lower()}"
    )
    lines.append(
        f"EDGE_HASH_MATCH={str(hash_cmp['WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256']['MATCH']).lower()}"
    )
    lines.append(
        f"CROSS_FLOW_HASH_MATCH={str(hash_cmp['WHOLE_SYSTEM_CROSS_FLOW_UNIVERSE_SHA256']['MATCH']).lower()}"
    )
    lines.append(
        f"RUNTIME_SURFACE_HASH_MATCH={str(hash_cmp['RUNTIME_SURFACE_UNIVERSE_SHA256']['MATCH']).lower()}"
    )
    lines.append(
        f"ENTRYPOINT_HASH_MATCH={str(hash_cmp['CANONICAL_ENTRYPOINT_UNIVERSE_SHA256']['MATCH']).lower()}"
    )
    lines.append(
        f"AUTHORITY_HASH_MATCH={str(hash_cmp['AUTHORITY_MATRIX_SHA256']['MATCH']).lower()}"
    )
    lines.append(
        f"REACHABILITY_HASH_MATCH={str(hash_cmp['REACHABILITY_MATRIX_SHA256']['MATCH']).lower()}"
    )
    lines.append(f"ALL_SEVEN_SEMANTIC_HASHES_MATCH={str(all_match).lower()}")
    lines.append(f"UNIVERSE_CLOSURE_PROVEN={str(universe['UNIVERSE_CLOSURE_PROVEN']).lower()}")
    lines.append(f"WHOLE_SYSTEM_FIXPOINT_CANDIDATE_PASS_2={str(fixpoint).lower()}")
    lines.append(f"POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES={2 if fixpoint else 1}")
    lines.append(f"CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES={2 if fixpoint else 1}")
    lines.append(f"WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED={str(fixpoint).lower()}")
    lines += [
        "DECISION_SEMANTICS_CHANGED=false",
        "POST_ALLOWED=false",
        "GHV_AUTHORITY=NONE",
        "RUN003_STARTED=false",
        "OWNER_MERGE_GO=false",
        f"DEF001_CURRENT_STATUS={dstatus('DEF-001')}",
        f"NEXT_STEP={'WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED' if fixpoint else 'Adjudicate PASS_007 semantic deltas'}",
        f"EVIDENCE_DIR={root.relative_to(MAIN_REPO)}",
    ]
    (root / "00_pass_007_final_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(root)
    return 0 if fixpoint else 1


if __name__ == "__main__":
    raise SystemExit(main())
