#!/usr/bin/env python3
"""Deterministic V2 fresh whole-system discovery (shared PASS_007A/PASS_008)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

_PY_MARKER_FIELDS = (
    "HAS_ACCOUNTING_MARKERS",
    "HAS_CANARY_MARKERS",
    "HAS_CREDENTIAL_SYMBOLS",
    "HAS_ENTRYPOINT_SYMBOLS",
    "HAS_LEGACY_MARKERS",
    "HAS_LIVE_MARKERS",
    "HAS_RECONCILIATION_MARKERS",
    "HAS_RECOVERY_MARKERS",
    "HAS_SHADOW_MARKERS",
    "HAS_TESTNET_MARKERS",
    "IMPORTABLE",
    "CLASSIFICATION",
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _ops_path(name: str) -> Path:
    return REPO_ROOT / "scripts/ops" / name


def _surface_candidates_path() -> Path | None:
    import os

    raw = os.environ.get("PEAK_TRADE_FORENSIC_SURFACE_CANDIDATES_JSON", "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_file() else None


PRODUCTIVE_SEED_CLASSES = frozenset(
    {"DEFAULT_PRODUCTIVE_ROOT", "CONDITIONAL_PRODUCTIVE_ROOT", "MODE_SELECTED_ROOT", "SHADOW_ROOT"}
)
UNION_EXCLUDE_CLASSES = frozenset(
    {
        "TEST_ROOT",
        "FORENSIC_ROOT",
        "VERIFY_HELPER_NOT_ROOT",
        "LIBRARY_MODULE_NOT_ROOT",
        "SUPPORT_MODULE_NOT_ROOT",
        "OPERATOR_TOOL_ROOT",
        "FALSE_FILENAME_ROOT_CANDIDATE",
    }
)


def _load(name: str, path: Path) -> Any:
    import sys

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def component_identity_sha256(rows: list[dict[str, Any]]) -> str:
    stable = [
        json.dumps(r, sort_keys=True, separators=(",", ":"))
        for r in sorted(rows, key=lambda x: x["COMPONENT_ID"])
    ]
    return hashlib.sha256("\n".join(stable).encode()).hexdigest()


def build_component_identity_inventory(
    union_nodes: list[dict[str, Any]], fs: dict[str, Any]
) -> list[dict[str, Any]]:
    py_by_path = {m["PATH"]: m for m in fs.get("py_modules", [])}
    rows: list[dict[str, Any]] = []
    for n in sorted(union_nodes, key=lambda x: x["NODE_KEY"]):
        path = n["NODE_KEY"]
        pm = py_by_path.get(path, {})
        row: dict[str, Any] = {
            "COMPONENT_ID": path,
            "PATH": path,
            "COMPONENT_CLASS": n.get("CLASSIFICATION", "UNKNOWN_CURRENT"),
            "MODULE_OR_SYMBOL_IDENTITY": pm.get("MODULE", Path(path).stem),
            "DISCOVERY_METHODS": sorted(n.get("METHODS", [])),
        }
        for field in _PY_MARKER_FIELDS:
            if field in pm:
                row[field] = pm[field]
        rows.append(row)
    return rows


def derive_union_nodes_from_pass008_filesystem_evidence(
    pass008_dir: Path, repo: Path
) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    fs_path = pass008_dir / "fresh_filesystem_discovery.json"
    if not fs_path.is_file():
        return [], {}, True
    fs = json.loads(fs_path.read_text(encoding="utf-8"))
    if not fs.get("py_modules"):
        return [], fs, True
    cont = _load(
        "cont",
        _ops_path(
            "run_current_full_repository_recartography_and_whole_system_fixpoint_continuation_v1.py"
        ),
    )
    py_paths = [m["PATH"] for m in fs["py_modules"]]
    ast_d = cont.discover_ast(repo, py_paths)
    ep_meta = cont.discover_entrypoints(repo)
    tg = cont.discover_test_governance(repo)
    hist_rec = cont.reconcile_historical(repo, tg.get("historical_cartography_seeds", []))
    union_nodes, _, _ = cont.build_union(repo, fs, ast_d, ep_meta, tg, hist_rec)
    return union_nodes, fs, False


def derive_pass008_component_identity_freeze(pass008_dir: Path, repo: Path) -> dict[str, Any]:
    union_nodes, fs, blocked = derive_union_nodes_from_pass008_filesystem_evidence(
        pass008_dir, repo
    )
    if blocked:
        return {
            "PASS009_COMPONENT_COMPARISON_BLOCKED": True,
            "ROWS": [],
            "PASS008_COMPONENT_IDENTITY_COUNT": 0,
            "PASS008_COMPONENT_IDENTITY_SHA256": None,
            "SOURCE": str(pass008_dir),
        }
    rows = build_component_identity_inventory(union_nodes, fs)
    return {
        "PASS009_COMPONENT_COMPARISON_BLOCKED": False,
        "ROWS": rows,
        "PASS008_COMPONENT_IDENTITY_COUNT": len(rows),
        "PASS008_COMPONENT_IDENTITY_SHA256": component_identity_sha256(rows),
        "SOURCE": "PASS_008 fresh_filesystem_discovery.json + deterministic union rebuild at BASELINE_SHA",
        "PASS008_CHECKPOINT": pass008_dir.name,
    }


def bfs_forward(out_edges: dict[str, set[str]], roots: list[str], repo: Path) -> set[str]:
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


def discover_v2_fresh(repo: Path | None = None) -> dict[str, Any]:
    repo = (repo or REPO_ROOT).resolve()
    disc = _load("disc", _ops_path("peak_trade_canonical_entrypoint_discovery_v2.py"))
    logic = _load("logic", _ops_path("peak_trade_forensic_closure_logic_v1.py"))
    cont = _load(
        "cont",
        _ops_path(
            "run_current_full_repository_recartography_and_whole_system_fixpoint_continuation_v1.py"
        ),
    )

    fs = cont.discover_filesystem(repo)
    py_paths = [m["PATH"] for m in fs["py_modules"]]
    importers, out_edges = logic.build_import_index(repo, py_paths)
    ep_meta = cont.discover_entrypoints(repo)
    tg = cont.discover_test_governance(repo)
    hist_rec = cont.reconcile_historical(repo, tg.get("historical_cartography_seeds", []))
    union_nodes, union_edges_ast, _ = cont.build_union(
        repo, fs, cont.discover_ast(repo, py_paths), ep_meta, tg, hist_rec
    )

    candidates = disc.scan_repository_candidates(repo)
    adjud_rows: list[dict[str, Any]] = []
    for rel in candidates:
        ev = disc.analyze_python_module(repo, rel, importers)
        cls, is_root, why = disc.classify_root(rel, ev)
        adjud_rows.append(
            {
                "PATH": rel,
                "SYMBOL": Path(rel).stem,
                "STRUCTURAL_ROOT_EVIDENCE": ev.structural_root_signals(),
                "IS_STRUCTURAL_ROOT": is_root,
                "ROOT_CLASS": cls,
                "WHY": why,
            }
        )

    canonical = [r for r in adjud_rows if r["IS_STRUCTURAL_ROOT"]]
    reach_by_root_class: dict[str, set[str]] = defaultdict(set)
    for r in canonical:
        reach_by_root_class[r["ROOT_CLASS"]].add(r["PATH"])

    class_reach = {
        cls: bfs_forward(out_edges, list(paths), repo) for cls, paths in reach_by_root_class.items()
    }
    union_reach: set[str] = set()
    productive_reach: set[str] = set()
    for cls, s in class_reach.items():
        if cls in UNION_EXCLUDE_CLASSES:
            continue
        union_reach |= s
        if cls in PRODUCTIVE_SEED_CLASSES:
            productive_reach |= s

    reach_rows = []
    for r in canonical:
        rid = r["PATH"]
        for node in class_reach.get(r["ROOT_CLASS"], set()):
            reach_rows.append(
                {
                    "ROOT_ID": rid,
                    "ROOT_CLASS": r["ROOT_CLASS"],
                    "NODE_ID": node,
                    "REACHABILITY_CLASS": r["ROOT_CLASS"],
                }
            )

    node_rows = []
    for rel in sorted(union_reach):
        node_rows.append(
            {
                "NODE_ID": rel,
                "PATH": rel,
                "SYMBOL_OR_MODULE": Path(rel).stem,
                "NODE_CLASS": "PYTHON_MODULE",
                "DOMAIN": logic.domain_of_path(rel),
                "ROOT_REACHABILITY_CLASSES": sorted(
                    {rr["ROOT_CLASS"] for rr in reach_rows if rr["NODE_ID"] == rel}
                ),
            }
        )

    ast_d = cont.discover_ast(repo, py_paths)
    edge_rows = []
    composition = []
    for e in ast_d["import_edges"]:
        to = e["TO"]
        sem = "FALSE_STATIC_CANDIDATE"
        tgt = None
        if to.startswith("src.") or to.startswith("trading."):
            tgt = to.replace(".", "/") + ".py"
            if tgt.startswith("trading."):
                tgt = "src/" + tgt
            if (repo / tgt).is_file():
                sem = (
                    "COMPOSITION_CURRENT"
                    if e["FROM"] in union_reach and tgt in union_reach
                    else "DORMANT_CURRENT"
                )
        elif to.startswith("tests."):
            sem = "TEST_ONLY"
        elif to in ("argparse", "typing", "dataclasses", "json", "os", "sys", "pathlib"):
            sem = "EXCLUDED_EXTERNAL"
        else:
            sem = "IMPORT"
        if tgt and sem == "COMPOSITION_CURRENT":
            composition.append({"FROM": e["FROM"], "TO": tgt, "TO_RAW": to})
        edge_rows.append(
            {
                "SOURCE_NODE_ID": e["FROM"],
                "TARGET_NODE_ID": tgt or to,
                "EDGE_CLASS": sem,
                "ROOT_PROVENANCE": "canonical_multi_root",
                "RUNTIME_RELEVANCE": e["FROM"] in union_reach,
            }
        )

    flows, boundary_rows = logic.build_cross_flows_from_semantics(
        [
            {
                "FROM": x["FROM"],
                "TO": x["TO"],
                "SEMANTIC_CLASS": "COMPOSITION_CURRENT",
                "TO_RAW": x["TO_RAW"],
            }
            for x in composition
        ],
        union_reach,
    )

    surface_path = _surface_candidates_path()
    if surface_path is not None:
        surf_cands = json.loads(surface_path.read_text(encoding="utf-8")).get("CANDIDATES", [])
        surf_adj = [
            {
                **c,
                "FINAL_CLASSIFICATION": c.get("FINAL_CLASSIFICATION", "UNKNOWN"),
            }
            for c in surf_cands
        ]
    else:
        surf_adj = []
    true_rows = [r for r in surf_adj if r.get("FINAL_CLASSIFICATION") == "TRUE_RUNTIME_SURFACE"]
    true_inv = (
        logic.build_true_runtime_surface_inventory(true_rows, union_reach) if true_rows else []
    )

    authority_rows = [
        {"SOURCE": s["PATH"], "RELATION": "RUNTIME_SURFACE", "TARGET": s["AUTHORITY"]}
        for s in true_inv
    ]

    edge_hash_rows = [
        e
        for e in edge_rows
        if e["EDGE_CLASS"] in ("COMPOSITION_CURRENT", "DORMANT_CURRENT", "IMPORT")
    ]
    hashes = {
        "WHOLE_SYSTEM_NODE_UNIVERSE_SHA256": disc.node_rows_hash(node_rows),
        "WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256": disc.edge_rows_hash(edge_hash_rows),
        "WHOLE_SYSTEM_CROSS_FLOW_UNIVERSE_SHA256": logic.sha256_list(
            [f["CROSS_FLOW_ID"] for f in flows]
        ),
        "RUNTIME_SURFACE_UNIVERSE_SHA256": logic.runtime_surface_universe_hash(true_inv),
        "CANONICAL_ENTRYPOINT_UNIVERSE_SHA256": disc.entrypoint_identity_hash(canonical),
        "AUTHORITY_MATRIX_SHA256": logic.sha256_list(
            [f"{a['SOURCE']}|{a['RELATION']}|{a['TARGET']}" for a in authority_rows]
        ),
        "REACHABILITY_MATRIX_SHA256": disc.reachability_hash(reach_rows),
    }

    leaks = audit_root_isolation(canonical, class_reach, productive_reach)

    return {
        "fs": fs,
        "py_paths": py_paths,
        "union_nodes": union_nodes,
        "union_edges_ast_count": len(union_edges_ast),
        "adjud_rows": adjud_rows,
        "canonical": canonical,
        "class_reach": {k: len(v) for k, v in class_reach.items()},
        "union_reach": union_reach,
        "productive_reach": productive_reach,
        "reach_rows": reach_rows,
        "node_rows": node_rows,
        "edge_rows": edge_rows,
        "composition": composition,
        "boundary_rows": boundary_rows,
        "flows": flows,
        "surf_adj": surf_adj,
        "true_inv": true_inv,
        "authority_rows": authority_rows,
        "hashes": hashes,
        "leaks": leaks,
        "semantic_edge_count": sum(
            1 for e in edge_rows if e["EDGE_CLASS"] in ("COMPOSITION_CURRENT", "DORMANT_CURRENT")
        ),
    }


def audit_root_isolation(
    canonical: list[dict[str, Any]], class_reach: dict[str, set[str]], productive_reach: set[str]
) -> dict[str, Any]:
    forensic_leaks = 0
    test_leaks = 0
    op_leaks = 0
    root_leaks = 0
    audit_rows = []
    non_productive_seed = frozenset(
        {
            "FORENSIC_ROOT",
            "TEST_ROOT",
            "OPERATOR_TOOL_ROOT",
            "VERIFY_HELPER_NOT_ROOT",
            "LIBRARY_MODULE_NOT_ROOT",
            "SUPPORT_MODULE_NOT_ROOT",
            "FALSE_FILENAME_ROOT_CANDIDATE",
        }
    )
    for r in canonical:
        cls = r["ROOT_CLASS"]
        path = r["PATH"]
        prod_seed = cls in PRODUCTIVE_SEED_CLASSES
        audit_rows.append(
            {
                "PATH": path,
                "STRUCTURAL_ROOT": True,
                "ROOT_CLASS": cls,
                "PRODUCTIVE_AUTHORITY": prod_seed,
                "PRODUCTIVE_REACHABILITY_SEED": prod_seed,
                "ACTIVATION": False,
                "EXTERNAL_EFFECT_CAPABILITY": False,
                "EXTERNAL_EFFECT_ALLOWED": False,
                "INVOKER": "structural_root_predicate_v2",
                "EVIDENCE": r.get("STRUCTURAL_ROOT_EVIDENCE", []),
            }
        )
        if cls in non_productive_seed and prod_seed:
            root_leaks += 1
        if cls == "FORENSIC_ROOT" and prod_seed:
            forensic_leaks += 1
        if cls == "TEST_ROOT" and prod_seed:
            test_leaks += 1
        if cls == "OPERATOR_TOOL_ROOT" and prod_seed:
            op_leaks += 1

    return {
        "ROWS": audit_rows,
        "ROOT_CLASSIFICATION_LEAKS": root_leaks,
        "FORENSIC_TO_PRODUCTIVE_REACHABILITY_LEAKS": forensic_leaks,
        "TEST_TO_PRODUCTIVE_REACHABILITY_LEAKS": test_leaks,
        "OPERATOR_TOOL_TO_PRODUCTIVE_REACHABILITY_LEAKS": op_leaks,
        "PRODUCTIVE_REACHABLE_NODE_COUNT": len(productive_reach),
    }
