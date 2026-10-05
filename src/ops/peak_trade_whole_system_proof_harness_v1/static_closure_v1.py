"""Static forward/reverse closure for operation-scoped and import-scoped graphs."""

from __future__ import annotations

import importlib.util
import json
from collections import deque
from pathlib import Path
from typing import Any

from src.ops.peak_trade_whole_system_proof_harness_v1.identity_v1 import (
    component_identity_v1,
    edge_identity_v1,
)


def _load_script_module(name: str, path: Path) -> Any:
    import sys

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def resolve_location_to_paths_v1(repo: Path, location: str) -> list[str]:
    loc = location.strip()
    if loc.endswith(".py") and (repo / loc).is_file():
        return [loc]
    if ".py" in loc and "/" in loc:
        candidate = loc.split(".py")[0] + ".py"
        if (repo / candidate).is_file():
            return [candidate]
    slug = loc.split(".")[-1] if "." in loc else loc
    hits: list[str] = []
    for path in repo.glob("src/**/*.py"):
        if slug in path.name:
            hits.append(path.relative_to(repo).as_posix())
    for path in repo.glob("scripts/**/*.py"):
        if slug in path.name:
            hits.append(path.relative_to(repo).as_posix())
    return sorted(set(hits))


def load_operation_spec_v1(repo: Path, rel: str) -> dict[str, Any]:
    spec_path = repo / rel
    return json.loads(spec_path.read_text(encoding="utf-8"))


def enrich_operation_nodes_v1(repo: Path, spec: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in spec.get("SEMANTIC_NODES", []):
        paths = resolve_location_to_paths_v1(repo, str(node.get("location", "")))
        enriched = dict(node)
        enriched["resolved_paths"] = paths
        enriched["resolved_path"] = paths[0] if paths else None
        enriched["resolution_status"] = "RESOLVED" if paths else "UNKNOWN"
        enriched["component_identity"] = component_identity_v1(enriched)
        out.append(enriched)
    return out


def semantic_forward_graph_v1(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> dict[str, Any]:
    node_ids = {n["id"] for n in nodes}
    fwd: list[dict[str, Any]] = []
    for e in edges:
        if e["producer"] not in node_ids or e["consumer"] not in node_ids:
            continue
        row = dict(e)
        row["edge_identity"] = edge_identity_v1(row)
        fwd.append(row)
    return {
        "nodes": nodes,
        "edges": fwd,
        "node_count": len(nodes),
        "edge_count": len(fwd),
        "discovery_method": "operation_semantic_spec_forward",
    }


def semantic_reverse_graph_v1(forward: dict[str, Any]) -> dict[str, Any]:
    rev_edges = []
    for e in forward.get("edges", []):
        rev_edges.append(
            {
                "producer": e["consumer"],
                "consumer": e["producer"],
                "contract": e.get("contract"),
                "condition": f"reverse_of:{e.get('condition')}",
                "edge_identity": edge_identity_v1(
                    {
                        "producer": e["consumer"],
                        "consumer": e["producer"],
                        "contract": e.get("contract"),
                        "condition": e.get("condition"),
                    }
                ),
            }
        )
    return {
        "nodes": forward.get("nodes", []),
        "edges": rev_edges,
        "node_count": forward.get("node_count"),
        "edge_count": len(rev_edges),
        "discovery_method": "operation_semantic_spec_reverse",
    }


def _lazy_import_neighbors(repo: Path, rel: str) -> set[str]:
    import ast

    path = repo / rel
    if not path.is_file():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return set()
    out: set[str] = set()
    for node in ast.walk(tree):
        mod = None
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(("src.", "trading.")):
                    mod = alias.name
        if not mod:
            continue
        if mod.startswith("src.") or mod.startswith("trading."):
            tgt = mod.replace(".", "/") + ".py"
            if mod.startswith("trading."):
                tgt = "src/" + tgt
            if (repo / tgt).is_file():
                out.add(tgt)
    return out


def import_forward_closure_v1(repo: Path, launcher_rel: str) -> dict[str, Any]:
    seen: set[str] = set()
    q: deque[str] = deque()
    if (repo / launcher_rel).is_file():
        q.append(launcher_rel)
    while q:
        cur = q.popleft()
        if cur in seen:
            continue
        seen.add(cur)
        for nxt in _lazy_import_neighbors(repo, cur):
            if nxt not in seen:
                q.append(nxt)
    return {
        "launcher": launcher_rel,
        "reachable_module_count": len(seen),
        "reachable_modules": sorted(seen),
        "discovery_method": "lazy_import_bfs_forward_from_launcher",
    }


def import_reverse_closure_v1(
    repo: Path, terminal_paths: list[str], universe: set[str]
) -> dict[str, Any]:
    importers: dict[str, set[str]] = {}
    for mod in universe:
        for tgt in _lazy_import_neighbors(repo, mod):
            importers.setdefault(tgt, set()).add(mod)
    seen: set[str] = set()
    q: deque[str] = deque(p for p in terminal_paths if p in universe)
    while q:
        cur = q.popleft()
        if cur in seen:
            continue
        seen.add(cur)
        for imp in importers.get(cur, ()):
            if imp in universe and imp not in seen:
                q.append(imp)
    return {
        "terminal_seeds": terminal_paths,
        "reverse_reachable_count": len(seen),
        "reverse_reachable_modules": sorted(seen),
        "discovery_method": "lazy_import_bfs_reverse_within_forward_universe",
    }
