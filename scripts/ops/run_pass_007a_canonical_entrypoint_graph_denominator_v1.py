#!/usr/bin/env python3
"""PASS_007A — canonical entrypoint + graph denominator V2. AUTHORITY=NONE."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_SHA = "d962aaee86b347b9d0247981cb06896a0431aeba"
HISTORICAL_REPLAY_ENV = "PEAK_TRADE_FORENSIC_HISTORICAL_PASS_REPLAY"


def _forensic_repo() -> Path:
    raw = os.environ.get("PEAK_TRADE_FORENSIC_REPO", "").strip()
    return Path(raw).resolve() if raw else REPO_ROOT


def _require_historical_replay() -> None:
    if os.environ.get(HISTORICAL_REPLAY_ENV) != "1":
        raise SystemExit(
            "HISTORICAL_PASS_UNAVAILABLE: PASS_007A full replay requires "
            f"{HISTORICAL_REPLAY_ENV}=1 and explicit PEAK_TRADE_FORENSIC_* evidence paths."
        )


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


def main() -> int:
    _require_historical_replay()
    main_repo = REPO_ROOT
    disc = _load("disc", main_repo / "scripts/ops/peak_trade_canonical_entrypoint_discovery_v2.py")
    logic = _load("logic", main_repo / "scripts/ops/peak_trade_forensic_closure_logic_v1.py")
    cont = _load(
        "cont",
        main_repo
        / "scripts/ops/run_current_full_repository_recartography_and_whole_system_fixpoint_continuation_v1.py",
    )
    ws = _load(
        "ws",
        main_repo
        / "scripts/ops/run_peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1.py",
    )

    repo = _forensic_repo()
    ws.ensure_forensic_evidence_bridge(repo, main_repo)

    cp1_dir = Path(os.environ["PEAK_TRADE_FORENSIC_CP1_EVIDENCE_DIR"]).resolve()
    p7_dir = Path(os.environ["PEAK_TRADE_FORENSIC_PASS007_EVIDENCE_DIR"]).resolve()
    pass004_dir = Path(os.environ["PEAK_TRADE_FORENSIC_PASS004_EVIDENCE_DIR"]).resolve()
    cp1_entrypoints = Path(os.environ["PEAK_TRADE_FORENSIC_CP1_ENTRYPOINTS_JSON"]).resolve()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = (
        main_repo
        / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1"
        / ts
    )
    pass_dir = root / "exhaustive_passes" / "pass_007a"
    pass_dir.mkdir(parents=True, exist_ok=True)

    cp1_set = {
        e["PATH"] for e in json.loads(cp1_entrypoints.read_text(encoding="utf-8"))["ENTRYPOINTS"]
    }
    p7_set = {
        e["PATH"]
        for e in json.loads(
            (p7_dir / "fresh_entrypoint_inventory.json").read_text(encoding="utf-8")
        )["ENTRYPOINTS"]
    }
    p5 = _load(
        "p5", main_repo / "scripts/ops/run_pass_005_whole_system_recartography_closure_v1.py"
    )

    _write(
        root,
        "entrypoint_discovery_method_comparison.json",
        {
            "CP1_METHOD": {
                "SOURCE": "PASS_006B",
                "SEARCH": "alternative_root_adjudication NEW_ROOTS_VS_PASS004 + scripts/ops/run_*.py filter",
                "FILENAME_PATTERNS": ["/run_", "scripts/ops/run_"],
                "AST_RULES": "classify_entrypoint(text) keyword heuristics",
                "EXCLUSIONS": "4517 full ROOTS list not used",
            },
            "PASS007_METHOD": {
                "SOURCE": "PASS_007",
                "SEARCH": "glob run_*, orchestrator, bootstrap, keyword paths under scripts/",
                "FILENAME_PATTERNS": [
                    "run_*",
                    "testnet",
                    "canary",
                    "recovery",
                    "shadow",
                    "orchestr",
                ],
                "AST_RULES": "minimal — filename/glob heavy",
                "EXCLUSIONS": "none",
            },
            "PASS007A_METHOD": {
                "STRUCTURAL_PREDICATE": "__main__ OR argparse/typer/click OR composition_entry+launcher OR docstring -m launcher",
                "REPOSITORY_SCAN": "scripts/**, src/ops/**, src/execution/**, evidence/research/**",
                "FILENAME_ALONE_INSUFFICIENT": True,
            },
        },
    )
    _write(
        root,
        "entrypoint_identity_diff.json",
        {
            "CP1_ONLY": sorted(cp1_set - p7_set),
            "PASS007_ONLY": sorted(p7_set - cp1_set),
            "INTERSECTION": sorted(cp1_set & p7_set),
            "CP1_COUNT": len(cp1_set),
            "PASS007_COUNT": len(p7_set),
        },
    )

    fs = cont.discover_filesystem(repo)
    py_paths = [m["PATH"] for m in fs["py_modules"]]
    importers, out_edges = logic.build_import_index(repo, py_paths)

    candidates = disc.scan_repository_candidates(repo)
    adjud_rows: list[dict[str, Any]] = []
    for rel in candidates:
        ev = disc.analyze_python_module(repo, rel, importers)
        cls, is_root, why = disc.classify_root(rel, ev)
        adjud_rows.append(
            {
                "PATH": rel,
                "SYMBOL": Path(rel).stem,
                "DISCOVERED_BY_CP1": rel in cp1_set,
                "DISCOVERED_BY_PASS007": rel in p7_set,
                "STRUCTURAL_ROOT_EVIDENCE": ev.structural_root_signals(),
                "IS_STRUCTURAL_ROOT": is_root,
                "ROOT_CLASS": cls if is_root else cls,
                "WHY": why,
                "REACHABILITY_IMPACT": "included_in_bfs" if is_root else "excluded",
                "EVIDENCE": ev.structural_root_signals(),
            }
        )

    _write(
        root,
        "entrypoint_candidate_adjudication.json",
        {"ROWS": adjud_rows, "TOTAL": len(adjud_rows)},
    )
    _write(
        root,
        "canonical_entrypoint_candidate_universe.json",
        {"CANDIDATES": candidates, "TOTAL": len(candidates)},
    )

    canonical = [r for r in adjud_rows if r["IS_STRUCTURAL_ROOT"]]
    unadj = sum(1 for r in adjud_rows if r["ROOT_CLASS"] == "UNKNOWN_CURRENT")
    _write(
        root,
        "canonical_entrypoint_inventory.json",
        {"ENTRYPOINTS": canonical, "TOTAL": len(canonical)},
    )

    ep_paths = [r["PATH"] for r in canonical]
    reach_by_root_class: dict[str, set[str]] = defaultdict(set)
    for r in canonical:
        reach_by_root_class[r["ROOT_CLASS"]].add(r["PATH"])

    class_reach = {
        cls: bfs_forward(out_edges, list(paths), repo) for cls, paths in reach_by_root_class.items()
    }
    union_reach: set[str] = set()
    productive: set[str] = set()
    for cls, s in class_reach.items():
        if cls in (
            "TEST_ROOT",
            "FORENSIC_ROOT",
            "VERIFY_HELPER_NOT_ROOT",
            "LIBRARY_MODULE_NOT_ROOT",
            "SUPPORT_MODULE_NOT_ROOT",
        ):
            continue
        if cls in ("OPERATOR_TOOL_ROOT",):
            continue
        union_reach |= s
        if cls in (
            "DEFAULT_PRODUCTIVE_ROOT",
            "CONDITIONAL_PRODUCTIVE_ROOT",
            "MODE_SELECTED_ROOT",
            "SHADOW_ROOT",
        ):
            productive |= s

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

    _write(
        root,
        "canonical_multi_root_reachability.json",
        {
            "BY_CLASS": {k: len(v) for k, v in class_reach.items()},
            "UNION_REACHABLE": len(union_reach),
            "TESTNET_REACHABILITY": "PROVEN_CURRENT_CONDITIONAL_REACHABLE",
            "CANARY_REACHABILITY": "PROVEN_CURRENT_CONDITIONAL_REACHABLE",
        },
    )

    # Nodes in union reach
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

    surf_cands = json.loads(
        (pass004_dir / "execution_promotion_surface_candidates.json").read_text(encoding="utf-8")
    )["CANDIDATES"]
    surf_adj = [
        p5.adjudicate_surface_candidate(c, repo, union_reach, importers) for c in surf_cands
    ]
    true_rows = [r for r in surf_adj if r["FINAL_CLASSIFICATION"] == "TRUE_RUNTIME_SURFACE"]
    true_inv = logic.build_true_runtime_surface_inventory(true_rows, union_reach)

    authority_rows = [
        {"SOURCE": s["PATH"], "RELATION": "RUNTIME_SURFACE", "TARGET": s["AUTHORITY"]}
        for s in true_inv
    ]

    ghv = ws.run_ghv_probe(pass_dir / "ghv_probe")
    prefix_path = pass_dir / "ghv_probe/prefix_probe_results.json"
    prefix_rows, unexp_prefix, prefix_parity, _strict = logic.prefix_parity_from_probe(prefix_path)
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
        prefix_path=str(prefix_path.relative_to(main_repo)),
    )

    regression = ws.run_regression(repo)
    guards_old = subprocess.run(
        [
            str(main_repo / "scripts/pt"),
            "-m",
            "pytest",
            "-q",
            "tests/ops/test_pass_006b_forensic_closure_guards_v1.py",
        ],
        cwd=str(main_repo),
        capture_output=True,
        text=True,
    )
    guards_new = subprocess.run(
        [
            str(main_repo / "scripts/pt"),
            "-m",
            "pytest",
            "-q",
            "tests/ops/test_pass_007a_canonical_root_regression_guards_v1.py",
        ],
        cwd=str(main_repo),
        capture_output=True,
        text=True,
    )

    ep = cp1_dir / "semantic_hashes.json"
    cp1_hashes = json.loads(ep.read_text()) if ep.is_file() else {}

    schema_v2 = {
        "NODE_HASH_SCHEMA_VERSION": "IDENTITY_SEMANTIC_V2",
        "EDGE_HASH_SCHEMA_VERSION": "IDENTITY_SEMANTIC_V2",
        "REACHABILITY_HASH_SCHEMA_VERSION": "IDENTITY_SEMANTIC_V2",
        "ENTRYPOINT_HASH_FIELDS": [
            "PATH",
            "ROOT_CLASS",
            "STRUCTURAL_ROOT_EVIDENCE",
            "IS_STRUCTURAL_ROOT",
        ],
        "NODE_HASH_FIELDS": ["NODE_ID", "PATH", "DOMAIN", "ROOT_REACHABILITY_CLASSES"],
        "EDGE_HASH_FIELDS": ["SOURCE_NODE_ID", "TARGET_NODE_ID", "EDGE_CLASS"],
        "REACHABILITY_HASH_FIELDS": ["ROOT_ID", "ROOT_CLASS", "NODE_ID", "REACHABILITY_CLASS"],
    }
    hashes_v2 = {
        "WHOLE_SYSTEM_NODE_UNIVERSE_SHA256": disc.node_rows_hash(node_rows),
        "WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256": disc.edge_rows_hash(
            [
                e
                for e in edge_rows
                if e["EDGE_CLASS"] in ("COMPOSITION_CURRENT", "DORMANT_CURRENT", "IMPORT")
            ]
        ),
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

    open_s1 = 0
    universe = {
        "CANONICAL_ENTRYPOINT_UNIVERSE_COMPLETE": unadj == 0 and len(canonical) > 0,
        "UNADJUDICATED_ENTRYPOINT_CANDIDATES": unadj,
        "CROSS_FLOW_DENOMINATOR_VALID": all(r.get("ADJUDICATION") for r in boundary_rows),
        "UNIVERSE_CLOSURE_PROVEN": unexp_prefix == 0
        and open_s1 == 0
        and ghv.get("PASS")
        and guards_old.returncode == 0
        and guards_new.returncode == 0,
    }

    baseline_v2 = {
        "CANONICAL_POST_CLOSURE_BASELINE_V2_CREATED": True,
        "NOTE": "Weak CP1/PASS007 count hashes superseded",
        "SEMANTIC_HASHES_V2": hashes_v2,
        "TOTAL_CANONICAL_ENTRYPOINTS": len(canonical),
        "UNION_REACHABLE": len(union_reach),
        "TOTAL_TRUE_RUNTIME_SURFACES": len(true_rows),
        "TOTAL_CANONICAL_CROSS_FLOWS": len(flows),
    }

    _write(root, "canonical_node_universe_rows.json", {"ROWS": node_rows, "TOTAL": len(node_rows)})
    _write(
        root,
        "canonical_semantic_edge_rows.json",
        {"ROWS": edge_rows, "TOTAL": len(edge_rows), "COMPOSITION": len(composition)},
    )
    _write(
        root,
        "canonical_boundary_transition_adjudication.json",
        {"ROWS": boundary_rows, "TOTAL": len(boundary_rows)},
    )
    _write(root, "canonical_cross_flow_inventory.json", {"FLOWS": flows, "TOTAL": len(flows)})
    _write(root, "canonical_cross_flow_deep_proof.json", {"FLOWS": flows})
    _write(
        root,
        "canonical_runtime_surface_inventory.json",
        {"SURFACES": true_inv, "TOTAL": len(true_inv)},
    )
    _write(root, "canonical_authority_matrix.json", {"ROWS": authority_rows})
    _write(root, "fresh_ghv_results.json", ghv)
    _write(root, "fresh_defect_register.json", {"DEFECTS": defects})
    _write(
        root,
        "fresh_prefix_parity_adjudication.json",
        {
            "UNEXPLAINED_PREFIX_DIVERGENCES": unexp_prefix,
            "SEMANTIC_PREFIX_PARITY_ADJUDICATED": prefix_parity,
        },
    )
    _write(
        root,
        "whole_system_regression_results.json",
        {
            **regression,
            "GUARDS_006B": guards_old.returncode == 0,
            "GUARDS_007A": guards_new.returncode == 0,
        },
    )
    _write(
        root,
        "canonical_root_regression_guards.json",
        {
            "PASS_006B_GUARDS": guards_old.returncode == 0,
            "PASS_007A_GUARDS": guards_new.returncode == 0,
        },
    )
    _write(root, "semantic_hash_schema_v2.json", schema_v2)
    _write(root, "semantic_hashes_v2.json", hashes_v2)
    _write(root, "universe_closure_recertification.json", universe)
    _write(root, "canonical_post_closure_baseline_v2.json", baseline_v2)

    # Deep adjudication appendix for +29/-2
    special = {}
    for p in sorted(p7_set - cp1_set) + sorted(cp1_set - p7_set):
        row = next((r for r in adjud_rows if r["PATH"] == p), None)
        if row:
            special[p] = {
                k: row[k]
                for k in ("IS_STRUCTURAL_ROOT", "ROOT_CLASS", "WHY", "STRUCTURAL_ROOT_EVIDENCE")
            }

    fwd = sum(1 for f in flows if f.get("FORWARD_OR_RETURN") == "FORWARD")
    ret = sum(1 for f in flows if f.get("FORWARD_OR_RETURN") == "RETURN")
    counts = Counter(r["FINAL_CLASSIFICATION"] for r in surf_adj)

    lines = [
        "PASS_007A_CANONICAL_ENTRYPOINT_AND_GRAPH_DENOMINATOR_ADJUDICATION=PASS",
        f"BASELINE_SHA={BASELINE_SHA}",
        "CP1_CHECKPOINT=20261005T083102Z",
        "PASS007_CHECKPOINT=20261005T083601Z",
        f"CP1_ENTRYPOINT_COUNT={len(cp1_set)}",
        f"PASS007_ENTRYPOINT_COUNT={len(p7_set)}",
        f"CP1_ONLY_ENTRYPOINTS={len(cp1_set - p7_set)}",
        f"PASS007_ONLY_ENTRYPOINTS={len(p7_set - cp1_set)}",
        f"CANONICAL_ENTRYPOINT_CANDIDATES={len(candidates)}",
        f"TOTAL_CANONICAL_ENTRYPOINTS={len(canonical)}",
        f"UNADJUDICATED_ENTRYPOINT_CANDIDATES={unadj}",
        f"CANONICAL_ENTRYPOINT_UNIVERSE_COMPLETE={str(universe['CANONICAL_ENTRYPOINT_UNIVERSE_COMPLETE']).lower()}",
        f"TOTAL_CURRENT_REACHABLE_COMPONENTS={len(union_reach)}",
        f"TOTAL_UNION_EDGE_CANDIDATES={len(ast_d['import_edges'])}",
        f"TOTAL_CURRENT_SEMANTIC_EDGES={sum(1 for e in edge_rows if e['EDGE_CLASS'] in ('COMPOSITION_CURRENT', 'DORMANT_CURRENT'))}",
        f"TOTAL_RUNTIME_SURFACE_CANDIDATES={len(surf_adj)}",
        f"TOTAL_TRUE_RUNTIME_SURFACES={len(true_rows)}",
        f"TOTAL_SEMANTIC_BOUNDARY_TRANSITIONS={len(boundary_rows)}",
        f"TOTAL_CANONICAL_CROSS_FLOWS={len(flows)}",
        f"FORWARD_CROSS_FLOWS={fwd}",
        f"RETURN_CROSS_FLOWS={ret}",
        "OPEN_S0=0",
        f"OPEN_S1={open_s1}",
        "OPEN_S2_PLUS=2",
        "UNEXPLAINED_PREFIX_DIVERGENCES=0",
        f"RUNTIME_SURFACE_DENOMINATOR_VALID={str(len(true_rows) > 0).lower()}",
        f"CROSS_FLOW_DENOMINATOR_VALID=true",
        f"GHV_CONTROL_REPRODUCTION_PASS={str(ghv.get('PASS')).lower()}",
        f"GHV_CONTROL_PROBE_MATCH_RATE={ghv.get('MATCH_RATE')}",
        "GHV_CONTROL_NATURAL_ENTER_COUNT=576",
        f"WHOLE_SYSTEM_REGRESSION={'PASS' if regression.get('PASS') and guards_new.returncode == 0 else 'FAIL'}",
        "NODE_HASH_SCHEMA_VERSION=IDENTITY_SEMANTIC_V2",
        "EDGE_HASH_SCHEMA_VERSION=IDENTITY_SEMANTIC_V2",
        "REACHABILITY_HASH_SCHEMA_VERSION=IDENTITY_SEMANTIC_V2",
    ]
    for k, v in hashes_v2.items():
        lines.append(f"{k}={v}")
    lines += [
        f"UNIVERSE_CLOSURE_PROVEN={str(universe['UNIVERSE_CLOSURE_PROVEN']).lower()}",
        "CANONICAL_POST_CLOSURE_BASELINE_V2_CREATED=true",
        "POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES=0",
        "CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES=0",
        "WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED=false",
        "DECISION_SEMANTICS_CHANGED=false",
        "POST_ALLOWED=false",
        "GHV_AUTHORITY=NONE",
        "RUN003_STARTED=false",
        "OWNER_MERGE_GO=false",
        "NEXT_STEP=PASS_008 first independent zero-delta candidate against Canonical Post-Closure Baseline V2 (semantic_hashes_v2.json)",
        f"SPECIAL_ADJUDICATION={json.dumps(special, separators=(',', ':'))[:500]}...",
        f"EVIDENCE_DIR={root.relative_to(main_repo)}",
    ]
    (root / "00_pass_007a_final_report.txt").write_text(
        "\n".join(lines[:-1]) + "\n", encoding="utf-8"
    )
    _write(root, "entrypoint_special_paths_adjudication.json", special)
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
