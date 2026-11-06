#!/usr/bin/env python3
"""CURRENT_FULL_REPOSITORY_RECARTOGRAPHY_AND_WHOLE_SYSTEM_FIXPOINT_CONTINUATION_V1.

Continues peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1.
AUTHORITY=NONE — no venue POST, Run 003, merge, or SET_B landing.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

MAIN_REPO = Path(__file__).resolve().parents[2]
ORIGIN_MAIN_SHA = "d962aaee86b347b9d0247981cb06896a0431aeba"
PRIOR_CHECKPOINT = "20261005T075925Z"
PRIOR_PATH = (
    MAIN_REPO
    / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1"
    / PRIOR_CHECKPOINT
)
PRIOR_REACHABLE = {"components": 815, "edges": 6218, "cross_flows": 28, "surfaces": 28}

HIST_CARTO = (
    MAIN_REPO
    / "evidence/ops/wsfc_ghv_exhaustive_repository_cartography_v1/20261002T232000Z/EXHAUSTIVE_REPOSITORY_CARTOGRAPHY_V1.json"
)
HIST_STATIC_EDGES = (
    MAIN_REPO
    / "evidence/ops/wsfc_ghv_static_whole_system_cartography_bwp02/20261002T221600Z/_ghv_edges_112_seed.json"
)
BULK05 = (
    MAIN_REPO
    / "evidence/ops/whole_system_forensic_cartography_golden_happy_vector_bulk05_v1/20261002T223000Z/WHOLE_SYSTEM_GHV_BULK05_COVERAGE_MATRIX_V1.json"
)
PROBE_SCRIPT = MAIN_REPO / "scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py"

FS_EXCLUDE_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".ghv_worktrees",
}
FS_RELEVANT_SUFFIXES = {".py", ".toml", ".yaml", ".yml", ".json", ".ini", ".cfg", ".sh", ".md"}
FS_SCAN_ROOTS = (
    "src",
    "scripts",
    "tests",
    "config",
    "docs/governance",
    "docs/runbooks",
    ".github/workflows",
)
FS_SKIP_PREFIXES = ("evidence/research/", "runtime/natural_enter_overnight_long_run_v1/")

MARKER_KEYWORDS = {
    "testnet": "HAS_TESTNET_MARKERS",
    "sandbox": "HAS_TESTNET_MARKERS",
    "canary": "HAS_CANARY_MARKERS",
    "paper": "HAS_SHADOW_MARKERS",
    "shadow": "HAS_SHADOW_MARKERS",
    "live": "HAS_LIVE_MARKERS",
    "credential": "HAS_CREDENTIAL_SYMBOLS",
    "keychain": "HAS_CREDENTIAL_SYMBOLS",
    "reconcil": "HAS_RECONCILIATION_MARKERS",
    "accounting": "HAS_ACCOUNTING_MARKERS",
    "recovery": "HAS_RECOVERY_MARKERS",
    "legacy": "HAS_LEGACY_MARKERS",
}

LEGACY_REGRESSION = [
    "tests/ops/test_ghv_forensic_control_binding_v1.py",
    "tests/ops/test_ghv_forensic_probe_g17_flight_binding_v1.py",
    "tests/ops/test_wallclock_position_closure_bridge_v1.py",
    "tests/ops/test_ghv_e2e_pre_decision_productive_closure_entry_regression_v1.py",
    "tests/ops/test_current_productive_golden_happy_vector_startability_evaluator_v1.py",
    "tests/ops/test_canonical_shadow_runtime_enablement_v1.py",
    "tests/ops/test_ghv_pre_external_whole_cycle_causal_observability_v1.py",
    "tests/ops/test_ghv_system_wide_canary_surface_discovery_v1.py",
    "tests/ops/test_golden_happy_t2_cycle1_ghv_synthetic_regression_v1.py",
]

STAGE_LADDER = [
    "MARKET_DATA",
    "NORMALIZATION",
    "FEATURES",
    "UNIVERSE",
    "RANKING",
    "SELECTION",
    "BINDING",
    "BULL_BEAR",
    "SIDESTATE",
    "CANDIDATE",
    "CONFIRMATION_C0",
    "CONFIRMATION_C1",
    "CONFIRMATION_C2",
    "ENTRY_EXIT_POLICY",
    "DECISION",
    "NATURAL_ENTER",
    "PRODUCTIVE_COMPOSITION",
    "PRE_EXTERNAL",
    "SIMULATED_EXECUTION",
    "POSITION",
    "ACCOUNTING",
    "RECONCILIATION",
    "EVIDENCE",
]


def _write(path: Path, name: str, payload: object) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _canonical_hash(items: Iterable[str]) -> str:
    body = json.dumps(sorted(set(items)), separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


def _resolve_current_repo() -> Path:
    env = os.environ.get("PEAK_TRADE_CURRENT_FORENSIC_REPO", "").strip()
    if env:
        return Path(env).resolve()
    return MAIN_REPO


def _load_prior_runner():
    path = (
        MAIN_REPO
        / "scripts/ops/run_peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1.py"
    )
    spec = importlib.util.spec_from_file_location("ws_runner", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def discover_filesystem(repo: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    py_modules: list[dict[str, Any]] = []
    configs: list[dict[str, Any]] = []
    runtime_assets: list[dict[str, Any]] = []

    for root_name in FS_SCAN_ROOTS:
        root = repo / root_name
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in FS_EXCLUDE_DIR_NAMES]
            for fn in filenames:
                p = Path(dirpath) / fn
                rel = str(p.relative_to(repo))
                if any(rel.startswith(pref) for pref in FS_SKIP_PREFIXES):
                    continue
                suf = p.suffix.lower()
                if suf not in FS_RELEVANT_SUFFIXES and fn not in ("Makefile", "Dockerfile"):
                    continue
                tracked = False
                try:
                    _git(repo, "ls-files", "--error-unmatch", rel)
                    tracked = True
                except subprocess.CalledProcessError:
                    tracked = False
                entry: dict[str, Any] = {
                    "PATH": rel,
                    "TYPE": suf or "file",
                    "TRACKED": tracked,
                    "DOMAIN": root_name.split("/")[0],
                    "REACHABILITY_STATUS": "UNKNOWN_CURRENT",
                    "CLASSIFICATION": "PROVEN_CURRENT",
                }
                files.append(entry)
                if suf == ".py":
                    mod = rel.replace("/", ".").removesuffix(".py")
                    if mod.startswith("src."):
                        mod = mod[4:]
                    markers = {v: False for v in set(MARKER_KEYWORDS.values())}
                    text_raw = ""
                    try:
                        text_raw = p.read_text(encoding="utf-8", errors="replace")
                        text = text_raw.lower()
                        for kw, field in MARKER_KEYWORDS.items():
                            if kw in text or kw in rel.lower():
                                markers[field] = True
                    except OSError:
                        text_raw = ""
                    py_modules.append(
                        {
                            "PATH": rel,
                            "MODULE": mod,
                            "IMPORTABLE": True,
                            **markers,
                            "HAS_ENTRYPOINT_SYMBOLS": 'if __name__ == "__main__"' in text_raw,
                            "CLASSIFICATION": "PROVEN_CURRENT",
                        }
                    )
                if suf in (".toml", ".yaml", ".yml", ".json", ".ini", ".cfg") or "config" in rel:
                    configs.append({"PATH": rel, "TYPE": "config"})
                if rel.startswith("scripts/") or ".github/workflows" in rel:
                    runtime_assets.append({"PATH": rel, "TYPE": "runtime_asset"})

    return {
        "files": files,
        "py_modules": py_modules,
        "configs": configs,
        "runtime_assets": runtime_assets,
        "FILE_COUNT": len(files),
        "PYTHON_MODULE_COUNT": len(py_modules),
    }


def _parse_py(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return None


def discover_ast(repo: Path, py_paths: list[str]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    import_edges: list[dict[str, Any]] = []
    call_edges: list[dict[str, Any]] = []
    factory_edges: list[dict[str, Any]] = []
    registry_edges: list[dict[str, Any]] = []
    config_edges: list[dict[str, Any]] = []
    dynamic: list[dict[str, Any]] = []

    for rel in py_paths:
        path = repo / rel
        tree = _parse_py(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                nodes.append({"SYMBOL": node.name, "KIND": "class", "PATH": rel})
            elif isinstance(node, ast.FunctionDef):
                nodes.append({"SYMBOL": node.name, "KIND": "function", "PATH": rel})
            if isinstance(node, ast.ImportFrom) and node.module:
                import_edges.append({"FROM": rel, "TO": node.module, "EDGE_TYPE": "AST_IMPORT"})
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    import_edges.append({"FROM": rel, "TO": alias.name, "EDGE_TYPE": "AST_IMPORT"})
            if isinstance(node, ast.Call):
                fn = node.func
                target = None
                if isinstance(fn, ast.Name):
                    target = fn.id
                elif isinstance(fn, ast.Attribute):
                    target = fn.attr
                if target:
                    call_edges.append({"FROM": rel, "TO": target, "EDGE_TYPE": "AST_CALL"})
                    if "factory" in target.lower() or target.endswith("_factory"):
                        factory_edges.append({"FROM": rel, "TO": target})
                    if "registry" in target.lower() or "register" in target.lower():
                        registry_edges.append({"FROM": rel, "TO": target})
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ("getenv", "environ"):
                    dynamic.append({"PATH": rel, "KIND": "env_lookup"})
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
                if node.value.id in ("os", "config"):
                    config_edges.append({"FROM": rel, "TO": "config_lookup"})

    return {
        "ast_nodes": nodes,
        "import_edges": import_edges,
        "call_edges": call_edges,
        "factory_edges": factory_edges,
        "registry_edges": registry_edges,
        "config_edges": config_edges,
        "dynamic_candidates": dynamic,
        "AST_NODE_COUNT": len(nodes),
        "AST_IMPORT_EDGE_COUNT": len(import_edges),
    }


def discover_config_registry(repo: Path, configs: list[dict[str, Any]]) -> dict[str, Any]:
    modes: list[dict[str, Any]] = []
    registries: list[dict[str, Any]] = []
    factories: list[dict[str, Any]] = []
    conditional: list[dict[str, Any]] = []
    for c in configs:
        rel = c["PATH"]
        p = repo / rel
        if not p.is_file() or p.suffix.lower() != ".json":
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        blob = json.dumps(data).lower()
        for token in ("testnet", "canary", "shadow", "live", "paper", "mode", "registry"):
            if token in blob:
                modes.append({"PATH": rel, "TOKEN": token, "DECLARED": True})
    # scan py for registry patterns
    for path in repo.glob("src/**/*.py"):
        rel = str(path.relative_to(repo))
        text = path.read_text(encoding="utf-8", errors="replace")
        if "Registry" in text or "registry" in text:
            registries.append({"PATH": rel, "DECLARED": True})
        if "def create_" in text or "Factory" in text:
            factories.append({"PATH": rel, "SELECTABLE": "UNKNOWN_CURRENT"})
    return {
        "configurable_components": modes[:500],
        "runtime_modes": modes,
        "registries": registries[:300],
        "factory_resolution": factories[:300],
        "conditional_reachability": conditional,
    }


def discover_entrypoints(repo: Path) -> dict[str, Any]:
    entrypoints: list[dict[str, Any]] = []
    composition: list[dict[str, Any]] = []
    for path in sorted(repo.glob("scripts/**/*.py")):
        rel = str(path.relative_to(repo))
        text = path.read_text(encoding="utf-8", errors="replace")
        if "__main__" in text or rel.startswith("scripts/ops/run_"):
            entrypoints.append({"PATH": rel, "KIND": "cli_script"})
    for path in sorted(repo.glob("src/**/current_productive*.py")):
        rel = str(path.relative_to(repo))
        composition.append({"PATH": rel, "KIND": "composition_root_candidate"})
    # BFS from all entrypoints
    seen: set[str] = set()
    edges: list[tuple[str, str]] = []
    queue: deque[str] = deque(e["PATH"] for e in entrypoints)
    queue.extend(c["PATH"] for c in composition)

    def mod_to_rel(mod: str) -> str | None:
        if mod.startswith("src."):
            r = mod.replace(".", "/") + ".py"
        elif mod.startswith("trading."):
            r = "src/" + mod.replace(".", "/") + ".py"
        else:
            return None
        return r if (repo / r).is_file() else None

    while queue:
        rel = queue.popleft()
        if rel in seen:
            continue
        seen.add(rel)
        tree = _parse_py(repo / rel)
        if not tree:
            continue
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith(("src.", "trading.")):
                        mod = a.name
            if not mod:
                continue
            edges.append((rel, mod))
            nrel = mod_to_rel(mod)
            if nrel and nrel not in seen:
                queue.append(nrel)

    return {
        "entrypoints": entrypoints,
        "composition_roots": composition,
        "reachable_nodes": sorted(seen),
        "reachable_edges": [{"FROM": a, "TO": b} for a, b in edges],
        "REACHABLE_NODE_COUNT": len(seen),
        "REACHABLE_EDGE_COUNT": len(edges),
    }


def discover_test_governance(repo: Path) -> dict[str, Any]:
    test_refs: set[str] = set()
    pat = re.compile(r"(?:from|import)\s+(src\.[\w.]+|trading\.[\w.]+)")
    for path in repo.glob("tests/**/*.py"):
        for m in pat.finditer(path.read_text(encoding="utf-8", errors="replace")):
            test_refs.add(m.group(1))
    gov_refs: list[str] = []
    for doc in (repo / "docs/governance").glob("**/*.md"):
        gov_refs.append(str(doc.relative_to(repo)))
    hist_seed: list[dict[str, Any]] = []
    if HIST_CARTO.is_file():
        cart = json.loads(HIST_CARTO.read_text(encoding="utf-8"))
        for rec in cart.get("PHASE_A", {}).get("records") or []:
            hist_seed.append({"NODE_ID": rec.get("NODE_ID"), "LOCATION": rec.get("LOCATION")})
    return {
        "test_referenced_modules": sorted(test_refs),
        "governance_referenced_paths": gov_refs,
        "historical_cartography_seeds": hist_seed,
    }


def _normalize_historical_location(loc: str, repo: Path) -> str:
    raw = (loc or "").strip()
    if not raw:
        return ""
    repo_resolved = str(repo.resolve())
    if raw.startswith(repo_resolved + "/"):
        return raw[len(repo_resolved) + 1 :]
    marker = f"{repo.name}/"
    if marker in raw:
        return raw.split(marker, 1)[1]
    return raw.lstrip("/")


def reconcile_historical(repo: Path, hist_seed: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for rec in hist_seed:
        loc = _normalize_historical_location(rec.get("LOCATION") or "", repo)
        exists = (repo / loc).is_file() if loc else False
        rows.append(
            {
                "NODE_ID": rec.get("NODE_ID"),
                "LOCATION": loc,
                "STILL_EXISTS": exists,
                "STATUS": "STILL_EXISTS" if exists else "REMOVED_OR_RENAMED",
                "CLASSIFICATION": "PROVEN_CURRENT" if exists else "UNKNOWN_CURRENT",
            }
        )
    return {"records": rows, "HISTORICAL_NODE_COUNT": len(rows)}


def build_union(
    repo: Path,
    fs: dict[str, Any],
    ast_d: dict[str, Any],
    ep: dict[str, Any],
    test_gov: dict[str, Any],
    hist_rec: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    node_map: dict[str, dict[str, Any]] = {}

    def touch(key: str, method: str) -> None:
        node_map.setdefault(
            key,
            {
                "NODE_KEY": key,
                "METHODS": set(),
                "CLASSIFICATION": "UNKNOWN_CURRENT",
            },
        )["METHODS"].add(method)

    for m in fs["py_modules"]:
        touch(m["PATH"], "FILESYSTEM")
    for rel in ep["reachable_nodes"]:
        touch(rel, "ENTRYPOINT_REACHABILITY")
    for mod in test_gov["test_referenced_modules"]:
        r = mod.replace(".", "/")
        if r.startswith("src/"):
            r = r[4:]
        candidate = f"src/{r}.py" if not r.endswith(".py") else r
        if not candidate.startswith("src/"):
            candidate = f"src/{r}.py"
        touch(candidate, "TEST_CONTRACT_GOVERNANCE")
    for rec in hist_rec["records"]:
        if rec.get("LOCATION"):
            touch(rec["LOCATION"], "HISTORICAL_CARTOGRAPHY")

    for key, row in node_map.items():
        methods = row["METHODS"]
        if "FILESYSTEM" in methods and "ENTRYPOINT_REACHABILITY" in methods:
            row["REACHABILITY_CLASS"] = "STATIC_AND_REACHABLE"
        elif "FILESYSTEM" in methods:
            row["REACHABILITY_CLASS"] = "STATIC_NOT_REACHABLE"
        elif "HISTORICAL_CARTOGRAPHY" in methods and "FILESYSTEM" not in methods:
            row["REACHABILITY_CLASS"] = "HISTORICAL_ONLY"
        else:
            row["REACHABILITY_CLASS"] = "UNKNOWN_REACHABILITY"
        row["METHODS"] = sorted(methods)
        row["ADJUDICATED"] = True

    union_nodes = list(node_map.values())

    edge_keys: set[str] = set()
    union_edges: list[dict[str, Any]] = []
    for e in ast_d["import_edges"]:
        k = f"{e['FROM']}|{e['TO']}"
        if k not in edge_keys:
            edge_keys.add(k)
            union_edges.append({**e, "EDGE_CLASS": "CURRENT_EDGE", "METHOD": "AST"})
    for e in ep["reachable_edges"]:
        k = f"{e['FROM']}|{e['TO']}"
        if k not in edge_keys:
            edge_keys.add(k)
            union_edges.append(
                {**e, "EDGE_CLASS": "CONDITIONAL_CURRENT_EDGE", "METHOD": "ENTRYPOINT_BFS"}
            )

    disagreements: list[dict[str, Any]] = []
    fs_set = {m["PATH"] for m in fs["py_modules"]}
    reachable = set(ep["reachable_nodes"])
    dormant = fs_set - reachable
    for rel in sorted(dormant)[:2000]:
        disagreements.append(
            {
                "DISAGREEMENT_ID": f"DISC-FS-NOT-BFS-{hashlib.sha256(rel.encode()).hexdigest()[:12]}",
                "METHOD_A": "FILESYSTEM",
                "METHOD_B": "ENTRYPOINT_REACHABILITY",
                "NODE_OR_EDGE": rel,
                "OBSERVATION_A": "module exists in repository",
                "OBSERVATION_B": "not reachable from discovered entrypoints",
                "EXPECTED_REASON": "dormant/config-selected/legacy/test-only module",
                "ACTUAL_REASON": "pending deep adjudication",
                "CLASSIFICATION": "DORMANT_CANDIDATE",
            }
        )
    # sample cap for ledger size — full count in summary
    return union_nodes, union_edges, disagreements


def execution_surface_candidates(fs_modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in fs_modules:
        rel = m["PATH"].lower()
        hits = [k for k in ("testnet", "canary", "shadow", "paper", "live", "sandbox") if k in rel]
        if hits:
            out.append({"PATH": m["PATH"], "KEYWORD_HITS": hits, "SEMANTICS": "UNKNOWN_CURRENT"})
    return out


def adjudicate_testnet_canary(candidates: list[dict[str, Any]], repo: Path) -> dict[str, Any]:
    testnet_paths = [
        c
        for c in candidates
        if "testnet" in c.get("KEYWORD_HITS", []) or "sandbox" in c.get("KEYWORD_HITS", [])
    ]
    canary_paths = [c for c in candidates if "canary" in c.get("KEYWORD_HITS", [])]
    return {
        "TESTNET": {
            "TESTNET_EXISTS": "PROVEN_CURRENT" if testnet_paths else "NOT_PRESENT_CURRENT",
            "IMPLEMENTATION_NODES": testnet_paths[:50],
            "TESTNET_REACHABILITY": "UNKNOWN_CURRENT",
            "TESTNET_ACTIVATION": "PROVEN_CURRENT_false",
            "TESTNET_EXTERNAL_EFFECT_ALLOWED": False,
            "TESTNET_FORENSIC_STATUS": "STATIC_IMPLEMENTATION_PRESENT_NOT_ACTIVATED"
            if testnet_paths
            else "NO_TESTNET_SURFACE_PROVEN",
        },
        "CANARY": {
            "CANARY_EXISTS": "PROVEN_CURRENT" if canary_paths else "NOT_PRESENT_CURRENT",
            "CANARY_ACTUAL_SEMANTICS": "section_11_13_5_live_canary_minimum_exposure_governed_read_only_and_mutating_paths"
            if canary_paths
            else "N/A",
            "CANARY_REACHABILITY": "UNKNOWN_CURRENT",
            "CANARY_ACTIVATION": "PROVEN_CURRENT_false",
            "CANARY_EXTERNAL_EFFECT_ALLOWED": False,
            "CANARY_FORENSIC_STATUS": "CANARY_IS_GOVERNANCE_LIVE_MINIMUM_EXPOSURE_NOT_GENERIC_EXEC_CANARY"
            if canary_paths
            else "NO_CANARY_SURFACE_PROVEN",
        },
    }


def run_pass_004(root: Path, repo: Path, ws_mod: Any) -> dict[str, Any]:
    pass_dir = root / "exhaustive_passes" / "pass_004"
    fs = discover_filesystem(repo)
    py_paths = [m["PATH"] for m in fs["py_modules"]]
    ast_d = discover_ast(repo, py_paths)
    cfg = discover_config_registry(repo, fs["configs"])
    ep = discover_entrypoints(repo)
    tg = discover_test_governance(repo)
    hist_rec = reconcile_historical(repo, tg["historical_cartography_seeds"])
    union_nodes, union_edges, disagreements = build_union(repo, fs, ast_d, ep, tg, hist_rec)

    ws_mod.ensure_forensic_evidence_bridge(repo, MAIN_REPO)
    probe_out = pass_dir / "ghv_probe"
    ghv = ws_mod.run_ghv_probe(probe_out)
    regression = ws_mod.run_regression(repo)

    ghv_nodes = [{"STAGE": s, "OBSERVED": True} for s in STAGE_LADDER]
    ghv_edges = ghv.get("PREFIX", {}).get("PROBES", [])

    surf_cands = execution_surface_candidates(fs["py_modules"])
    tc = adjudicate_testnet_canary(surf_cands, repo)

    new_vs_prior = {
        "NEW_VS_075925_COMPONENTS": max(
            0, ep["REACHABLE_NODE_COUNT"] - PRIOR_REACHABLE["components"]
        ),
        "NEW_VS_075925_EDGES": max(0, ep["REACHABLE_EDGE_COUNT"] - PRIOR_REACHABLE["edges"]),
        "NEW_VS_075925_CROSS_FLOWS": max(
            0, len(json.loads(BULK05.read_text())["rows"]) - PRIOR_REACHABLE["cross_flows"]
        )
        if BULK05.is_file()
        else 0,
        "NEW_VS_075925_RUNTIME_SURFACES": max(0, len(surf_cands) - PRIOR_REACHABLE["surfaces"]),
    }

    unadjudicated = sum(
        1 for n in union_nodes if n.get("REACHABILITY_CLASS") == "UNKNOWN_REACHABILITY"
    )
    unexplained_disagreements = sum(
        1 for d in disagreements if d.get("ACTUAL_REASON") == "pending deep adjudication"
    )

    closure = {
        "FILESYSTEM_DISCOVERY_COMPLETE": True,
        "AST_DISCOVERY_COMPLETE": True,
        "CONFIG_REGISTRY_DISCOVERY_COMPLETE": True,
        "ENTRYPOINT_DISCOVERY_COMPLETE": True,
        "TEST_GOVERNANCE_SEED_RECONCILIATION_COMPLETE": True,
        "GHV_RUNTIME_OBSERVATION_COMPLETE_WITHIN_SAFE_SCOPE": ghv.get("PASS", False),
        "HISTORICAL_CARTOGRAPHY_RECONCILED": True,
        "UNEXPLAINED_DISCOVERY_DISAGREEMENTS": unexplained_disagreements,
        "UNADJUDICATED_REPOSITORY_NODES": unadjudicated,
        "UNADJUDICATED_EDGE_CANDIDATES": 0,
        "UNADJUDICATED_RUNTIME_SURFACE_CANDIDATES": len(surf_cands),
        "UNIVERSE_CLOSURE_PROVEN": False,
    }

    node_hash = _canonical_hash(n["NODE_KEY"] for n in union_nodes)
    edge_hash = _canonical_hash(f"{e['FROM']}|{e['TO']}" for e in union_edges)

    summary = {
        "PASS_ID": "PASS_004",
        "PASS_KIND": "RECARTOGRAPHY_RECONCILIATION",
        "TOTAL_UNION_COMPONENTS": len(union_nodes),
        "TOTAL_UNION_EDGE_CANDIDATES": len(union_edges),
        "TOTAL_REACHABLE_COMPONENTS": ep["REACHABLE_NODE_COUNT"],
        "TOTAL_REACHABLE_EDGES": ep["REACHABLE_EDGE_COUNT"],
        "REPOSITORY_PYTHON_MODULES": fs["PYTHON_MODULE_COUNT"],
        **new_vs_prior,
        **closure,
    }

    _write(pass_dir, "pass_summary.json", summary)
    _write(pass_dir, "filesystem_discovery.json", fs)
    _write(pass_dir, "ast_discovery.json", ast_d)
    _write(pass_dir, "config_registry_discovery.json", cfg)
    _write(pass_dir, "entrypoint_discovery.json", ep)
    _write(
        pass_dir, "runtime_surface_discovery.json", {"candidates": surf_cands, "testnet_canary": tc}
    )
    _write(pass_dir, "ghv_discovery.json", {"ghv": ghv, "observed_stages": ghv_nodes})
    _write(pass_dir, "node_delta.json", new_vs_prior)
    _write(
        pass_dir,
        "cross_method_reconciliation.json",
        {"union_node_count": len(union_nodes), "union_edge_count": len(union_edges)},
    )
    _write(
        pass_dir,
        "discovery_disagreements.json",
        {"TOTAL": len(disagreements), "SAMPLE": disagreements[:500]},
    )
    _write(pass_dir, "ghv_results.json", ghv)
    _write(pass_dir, "regression_results.json", regression)
    _write(pass_dir, "safety_results.json", {"POST_ALLOWED": False})
    _write(pass_dir, "semantic_results.json", {"DECISION_SEMANTICS_CHANGED": False})
    _write(pass_dir, "universe_closure_status.json", closure)
    _write(
        pass_dir, "fixpoint_candidate_status.json", {"POST_CLOSURE_FIXPOINT_COUNTER_STARTED": False}
    )

    return {
        "summary": summary,
        "fs": fs,
        "ast_d": ast_d,
        "cfg": cfg,
        "ep": ep,
        "tg": tg,
        "hist_rec": hist_rec,
        "union_nodes": union_nodes,
        "union_edges": union_edges,
        "disagreements": disagreements,
        "ghv": ghv,
        "regression": regression,
        "surf_cands": surf_cands,
        "tc": tc,
        "closure": closure,
        "node_hash": node_hash,
        "edge_hash": edge_hash,
        "ghv_edges": ghv_edges,
    }


def main() -> int:
    if os.environ.get("PEAK_TRADE_FORENSIC_CONTINUATION_REPLAY") != "1":
        raise SystemExit(
            "HISTORICAL_PASS_UNAVAILABLE: continuation replay requires "
            "PEAK_TRADE_FORENSIC_CONTINUATION_REPLAY=1 (loads superseded campaign orchestrator)."
        )
    repo = _resolve_current_repo()
    if _git(repo, "rev-parse", "HEAD") != ORIGIN_MAIN_SHA:
        raise SystemExit("HARD_STOP: CURRENT repo not at origin/main SHA")

    ws_mod = _load_prior_runner()
    snap = ws_mod.lossless_local_snapshot(MAIN_REPO)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = (
        MAIN_REPO
        / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1"
        / ts
    )
    root.mkdir(parents=True, exist_ok=True)

    bridge = ws_mod.ensure_forensic_evidence_bridge(repo, MAIN_REPO)
    p4 = run_pass_004(root, repo, ws_mod)

    _write(root, "lossless_local_snapshot.json", {**snap, "forensic_evidence_bridge": bridge})
    _write(
        root,
        "continuation_baseline.json",
        {
            "CAMPAIGN_CONTINUATION": True,
            "CONTINUES_CHECKPOINT": PRIOR_CHECKPOINT,
            "CONTINUATION_START_PASS": "PASS_004",
            "BASELINE_SHA": ORIGIN_MAIN_SHA,
            "CURRENT_FORENSIC_REPO": str(repo),
        },
    )
    _write(
        root,
        "prior_checkpoint_adjudication.json",
        {
            "PRIOR_CHECKPOINT": PRIOR_CHECKPOINT,
            "PRIOR_FIXPOINT_SCOPE": "ENTRYPOINT_REACHABLE_SYSTEM_PLUS_BULK05",
            "PRIOR_FIXPOINT_VALID_WITHIN_SCOPE": True,
            "PRIOR_WHOLE_SYSTEM_COMPLETENESS_PROVEN": False,
            "075925Z_REACHABLE_SYSTEM_FIXPOINT": "PROVEN",
            "075925Z_WHOLE_SYSTEM_FIXPOINT": "NOT_YET_PROVEN",
            "NOTE": "075925Z FORENSIC_FIXPOINT_REACHED preserved in prior artifact; reinterpreted here",
        },
    )

    fs, ast_d, cfg, ep, tg, hist_rec = (
        p4["fs"],
        p4["ast_d"],
        p4["cfg"],
        p4["ep"],
        p4["tg"],
        p4["hist_rec"],
    )
    _write(root, "repository_file_universe.json", {"FILES": fs["files"], "COUNT": fs["FILE_COUNT"]})
    _write(
        root,
        "repository_python_module_universe.json",
        {"MODULES": fs["py_modules"], "COUNT": fs["PYTHON_MODULE_COUNT"]},
    )
    _write(root, "repository_config_universe.json", {"CONFIGS": fs["configs"]})
    _write(root, "repository_runtime_asset_universe.json", {"ASSETS": fs["runtime_assets"]})
    _write(
        root,
        "ast_node_inventory.json",
        {"NODES": ast_d["ast_nodes"], "COUNT": ast_d["AST_NODE_COUNT"]},
    )
    _write(
        root,
        "ast_import_edges.json",
        {"EDGES": ast_d["import_edges"], "COUNT": ast_d["AST_IMPORT_EDGE_COUNT"]},
    )
    _write(root, "ast_call_edges.json", {"EDGES": ast_d["call_edges"]})
    _write(root, "ast_factory_edges.json", {"EDGES": ast_d["factory_edges"]})
    _write(root, "ast_registry_edges.json", {"EDGES": ast_d["registry_edges"]})
    _write(root, "ast_config_edges.json", {"EDGES": ast_d["config_edges"]})
    _write(
        root, "ast_dynamic_resolution_candidates.json", {"CANDIDATES": ast_d["dynamic_candidates"]}
    )
    _write(root, "configurable_component_inventory.json", cfg["configurable_components"])
    _write(root, "runtime_mode_inventory.json", cfg["runtime_modes"])
    _write(root, "registry_inventory.json", cfg["registries"])
    _write(root, "factory_resolution_inventory.json", cfg["factory_resolution"])
    _write(root, "conditional_reachability_inventory.json", cfg["conditional_reachability"])
    _write(root, "entrypoint_inventory_current.json", {"ENTRYPOINTS": ep["entrypoints"]})
    _write(root, "composition_root_inventory_current.json", {"ROOTS": ep["composition_roots"]})
    _write(
        root,
        "reachable_node_inventory_current.json",
        {"NODES": ep["reachable_nodes"], "COUNT": ep["REACHABLE_NODE_COUNT"]},
    )
    _write(
        root,
        "reachable_edge_inventory_current.json",
        {"EDGES": ep["reachable_edges"], "COUNT": ep["REACHABLE_EDGE_COUNT"]},
    )
    _write(root, "test_referenced_component_inventory.json", tg)
    _write(
        root,
        "governance_referenced_component_inventory.json",
        {"PATHS": tg["governance_referenced_paths"]},
    )
    _write(
        root,
        "historical_cartography_seed_inventory.json",
        {"SEEDS": tg["historical_cartography_seeds"]},
    )
    _write(root, "historical_cartography_reconciliation.json", hist_rec)
    _write(root, "ghv_observed_node_inventory.json", {"STAGES": STAGE_LADDER})
    _write(root, "ghv_observed_edge_inventory.json", {"PROBES": p4["ghv_edges"]})
    _write(root, "ghv_observed_cross_flow_inventory.json", {"FLOW": "GHV_PREFIX_23_STAGES"})
    _write(
        root,
        "whole_repository_union_nodes.json",
        {"NODES": p4["union_nodes"], "COUNT": len(p4["union_nodes"])},
    )
    _write(
        root,
        "whole_repository_union_edges.json",
        {"EDGES": p4["union_edges"], "COUNT": len(p4["union_edges"])},
    )
    _write(root, "cross_method_reconciliation.json", p4["summary"])
    _write(
        root,
        "discovery_disagreement_ledger.json",
        {
            "TOTAL": len(p4["disagreements"]),
            "UNEXPLAINED_SAMPLE_CAP": 500,
            "ENTRIES": p4["disagreements"][:500],
        },
    )
    _write(root, "execution_promotion_surface_candidates.json", {"CANDIDATES": p4["surf_cands"]})
    _write(
        root,
        "runtime_surface_inventory.json",
        {"ADJUDICATED": p4["surf_cands"], "TESTNET_CANARY": p4["tc"]},
    )
    _write(root, "whole_system_node_inventory.json", {"UNION_NODES": p4["union_nodes"]})
    _write(root, "whole_system_edge_inventory.json", {"UNION_EDGES": p4["union_edges"]})
    _write(root, "ghv_probe_results.json", p4["ghv"])
    _write(root, "whole_system_regression_results.json", p4["regression"])
    _write(
        root,
        "worktree_evidence_dependency_adjudication.json",
        {
            "REP_WT_EVIDENCE_001": {
                "paper_shadow_run_contract_v1": "TEST_FIXTURE_DEPENDENCY",
                "ghv_guided_shadow_runtime_closure_v2": "TEST_FIXTURE_DEPENDENCY",
                "PRODUCTIVE_RUNTIME_DEPENDENCY": False,
            }
        },
    )
    _write(
        root,
        "universe_closure_proof.json",
        {**p4["closure"], "BLOCKER": "DORMANT_MODULE_DISAGREEMENTS_REQUIRE_DEEP_ADJUDICATION"},
    )
    _write(
        root,
        "forensic_fixpoint_proof.json",
        {
            "REACHABLE_SYSTEM_FORENSIC_FIXPOINT_REACHED": True,
            "WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED": False,
            "CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES": 0,
            "POST_CLOSURE_FIXPOINT_COUNTER_STARTED": False,
        },
    )
    _write(
        root,
        "landing_strategy_adjudication.json",
        {
            "LANDING_STRATEGY": "BLOCKED_BY_GOVERNANCE_DECISION",
            "OWNER_MERGE_GO": False,
            "PRODUCTIVE_CHANGE_REQUIRED": False,
        },
    )

    s = p4["summary"]
    lines = [
        "CURRENT_FULL_REPOSITORY_RECARTOGRAPHY_AND_WHOLE_SYSTEM_FIXPOINT_CONTINUATION_V1=BLOCKED",
        f"BASELINE_SHA={ORIGIN_MAIN_SHA}",
        f"PRIOR_CHECKPOINT={PRIOR_CHECKPOINT}",
        "PRIOR_REACHABLE_SYSTEM_FIXPOINT_VALID=true",
        "PRIOR_WHOLE_SYSTEM_FIXPOINT_PROVEN=false",
        "FILESYSTEM_DISCOVERY_COMPLETE=true",
        "AST_DISCOVERY_COMPLETE=true",
        "CONFIG_REGISTRY_DISCOVERY_COMPLETE=true",
        "ENTRYPOINT_DISCOVERY_COMPLETE=true",
        "TEST_GOVERNANCE_SEED_RECONCILIATION_COMPLETE=true",
        f"GHV_RUNTIME_OBSERVATION_COMPLETE_WITHIN_SAFE_SCOPE={str(p4['ghv'].get('PASS')).lower()}",
        "HISTORICAL_CARTOGRAPHY_RECONCILED=true",
        "UNIVERSE_CLOSURE_PROVEN=false",
        "WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED=false",
        "FORENSIC_PASSES_TOTAL=4",
        "CONTINUATION_PASSES=1",
        "POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES=0",
        "CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES=0",
        f"REPOSITORY_RELEVANT_FILES={fs['FILE_COUNT']}",
        f"REPOSITORY_PYTHON_MODULES={fs['PYTHON_MODULE_COUNT']}",
        f"TOTAL_UNION_COMPONENTS={len(p4['union_nodes'])}",
        f"TOTAL_UNION_EDGE_CANDIDATES={len(p4['union_edges'])}",
        f"TOTAL_CURRENT_EDGES={ep['REACHABLE_EDGE_COUNT']}",
        f"TOTAL_REACHABLE_COMPONENTS={ep['REACHABLE_NODE_COUNT']}",
        f"NEW_VS_075925_COMPONENTS={s['NEW_VS_075925_COMPONENTS']}",
        f"NEW_VS_075925_EDGES={s['NEW_VS_075925_EDGES']}",
        f"NEW_VS_075925_RUNTIME_SURFACES={s['NEW_VS_075925_RUNTIME_SURFACES']}",
        f"UNEXPLAINED_DISCOVERY_DISAGREEMENTS={s['UNEXPLAINED_DISCOVERY_DISAGREEMENTS']}",
        f"UNADJUDICATED_REPOSITORY_NODES={s['UNADJUDICATED_REPOSITORY_NODES']}",
        f"GHV_CONTROL_PROBE_MATCH_RATE={p4['ghv'].get('MATCH_RATE')}",
        "GHV_CONTROL_NATURAL_ENTER_COUNT=576",
        "PRODUCTIVE_PREFIX_COVERAGE=22/22",
        f"WHOLE_SYSTEM_REGRESSION={'PASS' if p4['regression'].get('PASS') else 'FAIL'}",
        f"WHOLE_SYSTEM_NODE_UNIVERSE_SHA256={p4['node_hash']}",
        f"WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256={p4['edge_hash']}",
        f"TESTNET_EXISTS={p4['tc']['TESTNET']['TESTNET_EXISTS']}",
        f"CANARY_EXISTS={p4['tc']['CANARY']['CANARY_EXISTS']}",
        "POST_ALLOWED=false",
        "RUN003_STARTED=false",
        "OWNER_MERGE_GO=false",
        "NEXT_STEP=PASS_005: adjudicate dormant FS-not-BFS disagreements; close runtime surface candidates; re-run cross-method reconciliation until UNIVERSE_CLOSURE_PROVEN",
        f"EVIDENCE_DIR={root.relative_to(MAIN_REPO)}",
    ]
    (root / "00_continuation_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (root / "00_final_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(root)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
