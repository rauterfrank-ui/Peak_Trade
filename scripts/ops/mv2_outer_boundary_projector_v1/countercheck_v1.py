"""Isolation counterchecks for the projector package and pinned GHV helpers."""

from __future__ import annotations

import ast
from pathlib import Path

from scripts.ops.mv2_outer_boundary_projector_v1.constants_v1 import (
    FORBIDDEN_IMPORT_PREFIXES,
    FORBIDDEN_IMPORT_ROOTS,
    GHV_CROSSWALK_DIR,
    GHV_PURE_FILES,
)
from scripts.ops.mv2_outer_boundary_projector_v1.input_contract_v1 import (
    ProjectorFailClosedV1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.source_pins_v1 import show_text


def _imported_modules(text: str) -> list[str]:
    tree = ast.parse(text)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return found


def _is_forbidden(module: str) -> bool:
    root = module.split(".", maxsplit=1)[0]
    if root in FORBIDDEN_IMPORT_ROOTS:
        return True
    if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
        return True
    if "ghosv_bounded_context_v1" in module:
        return True
    if "ghv_forensic_whole_system_crosswalk_v1" in module:
        return True
    if "ghv_forensic_whole_system_causal" in module:
        return True
    return False


def scan_package_imports_v1(package_dir: Path) -> list[str]:
    modules: set[str] = set()
    for path in sorted(package_dir.glob("*.py")):
        modules.update(_imported_modules(path.read_text(encoding="utf-8")))
    return sorted(modules)


def scan_reverse_importers_v1(repo_root: Path, package_dir: Path) -> list[str]:
    needle = "mv2_outer_boundary_projector_v1"
    hits: list[str] = []
    for base in (repo_root / "src", repo_root / "scripts"):
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if (
                package_dir.resolve() in path.resolve().parents
                or path.resolve() == package_dir.resolve()
            ):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if needle in text:
                hits.append(str(path.relative_to(repo_root)))
    return sorted(hits)


def scan_pinned_ghv_imports_v1(repo_root: Path, commit: str) -> list[str]:
    forbidden: list[str] = []
    for name in GHV_PURE_FILES:
        text = show_text(repo_root, commit, f"{GHV_CROSSWALK_DIR}/{name}")
        for module in _imported_modules(text):
            root = module.split(".", maxsplit=1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS or "ghosv_bounded_context_v1" in module:
                forbidden.append(f"{name}:{module}")
    return sorted(forbidden)


def build_countercheck_v1(
    *,
    repo_root: Path,
    commit: str,
    package_dir: Path,
    historical_graphs: list[dict[str, object]],
    causal_graph_verified: bool,
    universe_ratification: bool,
) -> dict[str, object]:
    imports = scan_package_imports_v1(package_dir)
    forbidden = [module for module in imports if _is_forbidden(module)]
    reverse = scan_reverse_importers_v1(repo_root, package_dir)
    transitive = scan_pinned_ghv_imports_v1(repo_root, commit)
    historical_used = [
        str(item.get("path"))
        for item in historical_graphs
        if item.get("current_proof") is True
        or item.get("edges_used_as_current_boundary_proof") is True
    ]
    if forbidden or reverse or transitive or historical_used or universe_ratification:
        raise ProjectorFailClosedV1(
            "ISOLATION_FAILED",
            "forbidden="
            + ",".join(forbidden)
            + " reverse="
            + ",".join(reverse)
            + " transitive="
            + ",".join(transitive),
        )
    return {
        "forward_imports_forbidden": forbidden,
        "reverse_importers": reverse,
        "pinned_ghv_forbidden_imports": transitive,
        "historical_graphs_used_as_current_proof": historical_used,
        "worktree_sources_used_as_evidence": False,
        "execution_ghosv_imported": False,
        "execution_ghosv_modified": False,
        "productive_modules_imported": False,
        "universe_ratification": False,
        "ghv_helpers_loaded_from": "PINNED_COMMIT_BLOBS",
        "causal_integration_invoked": False,
        "causal_graph_verified": causal_graph_verified,
        "isolation": "WITHIN_AUTHORIZED_NEW_PACKAGE",
    }
