#!/usr/bin/env python3
"""Structural canonical entrypoint discovery (PASS_007A). AUTHORITY=NONE."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PRODUCTIVE_HINTS = (
    "run_paper_shadow_bounded_orchestrator",
    "run_integrated_paper_shadow",
    "current_productive_master_v2_runtime_cycle",
    "operational_run",
    "full_core_live_path",
)

COMPOSITION_ENTRY_FUNCS = (
    "run_paper_shadow_bounded_operational_run_v1",
    "run_current_productive_master_v2_runtime_cycle_v1",
)


@dataclass
class StructuralEvidence:
    path: str
    has_main_guard: bool = False
    has_argparse: bool = False
    has_typer: bool = False
    has_click: bool = False
    has_subprocess_launch: bool = False
    composition_entry_fn: str | None = None
    launcher_importers: list[str] = field(default_factory=list)
    docstring_launcher: bool = False

    def structural_root_signals(self) -> list[str]:
        out: list[str] = []
        if self.has_main_guard:
            out.append("__main__")
        if self.has_argparse:
            out.append("argparse")
        if self.has_typer:
            out.append("typer")
        if self.has_click:
            out.append("click")
        if self.composition_entry_fn:
            out.append(f"composition_entry:{self.composition_entry_fn}")
        if self.launcher_importers:
            out.append(f"launcher_imports:n={len(self.launcher_importers)}")
        if self.docstring_launcher:
            out.append("docstring_cli_usage")
        return out

    @property
    def is_structural_root(self) -> bool:
        return bool(self.structural_root_signals())


def analyze_python_module(
    repo: Path, rel: str, importers: dict[str, set[str]] | None = None
) -> StructuralEvidence:
    p = repo / rel
    ev = StructuralEvidence(path=rel)
    if not p.is_file():
        return ev
    text = p.read_text(encoding="utf-8", errors="replace")
    if 'if __name__ == "__main__"' in text or "if __name__ == '__main__'" in text:
        ev.has_main_guard = True
    if "argparse" in text:
        ev.has_argparse = True
    if "import typer" in text or "from typer" in text:
        ev.has_typer = True
    if "import click" in text or "from click" in text:
        ev.has_click = True
    if "subprocess" in text and ("run(" in text or "Popen" in text):
        ev.has_subprocess_launch = True
    if re.search(r"python\s+-m\s+scripts\.", text[:4000]):
        ev.docstring_launcher = True
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ev
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in COMPOSITION_ENTRY_FUNCS:
            ev.composition_entry_fn = node.name
    if importers:
        ev.launcher_importers = sorted(
            x for x in importers.get(rel, set()) if x.startswith("scripts/")
        )
    return ev


def classify_root(rel: str, ev: StructuralEvidence) -> tuple[str, bool, str]:
    """Returns CLASSIFICATION, IS_STRUCTURAL_ROOT, WHY."""
    low = rel.lower()
    if rel.startswith("tests/"):
        return "TEST_ROOT", False, "test_path_not_productive_root"
    if not ev.is_structural_root:
        if low.startswith("scripts/ops/verify_") or "/verify_" in low:
            return "VERIFY_HELPER_NOT_ROOT", False, "verify_helper_without_executable_main"
        if low.startswith("scripts/ops/generate_"):
            return "OPERATOR_TOOL_ROOT", False, "generate_materialize_without_main"
        if "run_fingerprint" in low:
            return "LIBRARY_MODULE_NOT_ROOT", False, "pure_library_function_no_launcher"
        if "operational_run_v1" in low and ev.composition_entry_fn:
            return "CONDITIONAL_PRODUCTIVE_ROOT", True, "composition_entry_fn_with_script_launchers"
        return "SUPPORT_MODULE_NOT_ROOT", False, "no_structural_launch_evidence"

    # structural root — classify by role
    if "testnet" in low or "sandbox" in low:
        return "TESTNET_ROOT", True, "cli_main_testnet_launcher"
    if "canary" in low or "section_11_13_5" in low:
        return "CANARY_RELATED_ROOT", True, "cli_main_canary_governance_launcher"
    if "paper_shadow" in low or ("shadow" in low and "session" in low):
        return "SHADOW_ROOT", True, "shadow_session_launcher"
    if "simulation" in low or "simulated" in low:
        return "SIMULATION_ROOT", True, "simulation_launcher"
    if "recover" in low or "resume" in low:
        return "RECOVERY_ROOT", True, "recovery_launcher"
    if "forensic" in low or "ghv" in low:
        return "FORENSIC_ROOT", True, "forensic_launcher"
    if "legacy" in low:
        return "LEGACY_ROOT", True, "legacy_launcher"
    if any(h in low for h in PRODUCTIVE_HINTS):
        return "DEFAULT_PRODUCTIVE_ROOT", True, "productive_launcher"
    if low.startswith("scripts/ops/run_"):
        return "CONDITIONAL_PRODUCTIVE_ROOT", True, "ops_run_script_with_main"
    if low.startswith("scripts/run_") or low.startswith("scripts/aiops/run_"):
        return "CONDITIONAL_PRODUCTIVE_ROOT", True, "scripts_run_with_main"
    if ev.composition_entry_fn and ev.launcher_importers:
        return "CONDITIONAL_PRODUCTIVE_ROOT", True, "invoked_composition_root"
    return "MODE_SELECTED_ROOT", True, "generic_cli_main"


def scan_repository_candidates(repo: Path) -> list[str]:
    roots: set[str] = set()
    for base in ("scripts", "src/ops", "src/execution", "evidence/research"):
        bd = repo / base
        if not bd.is_dir():
            continue
        for p in bd.rglob("*.py"):
            rel = str(p.relative_to(repo))
            if "__pycache__" in rel or "/.ghv_" in rel:
                continue
            roots.add(rel)
    return sorted(roots)


def entrypoint_identity_hash(rows: list[dict[str, Any]]) -> str:
    stable = [
        json.dumps(
            {
                "PATH": r["PATH"],
                "ROOT_CLASS": r["ROOT_CLASS"],
                "STRUCTURAL_ROOT_IDENTITY": r.get("STRUCTURAL_ROOT_EVIDENCE", []),
                "IS_STRUCTURAL_ROOT": r.get("IS_STRUCTURAL_ROOT"),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        for r in sorted(rows, key=lambda x: x["PATH"])
        if r.get("IS_STRUCTURAL_ROOT")
    ]
    return hashlib.sha256("\n".join(stable).encode()).hexdigest()


def node_rows_hash(rows: list[dict[str, Any]]) -> str:
    stable = [
        json.dumps(r, sort_keys=True, separators=(",", ":"))
        for r in sorted(rows, key=lambda x: x["NODE_ID"])
    ]
    return hashlib.sha256("\n".join(stable).encode()).hexdigest()


def edge_rows_hash(rows: list[dict[str, Any]]) -> str:
    stable = [
        json.dumps(r, sort_keys=True, separators=(",", ":"))
        for r in sorted(
            rows, key=lambda x: (x["SOURCE_NODE_ID"], x["TARGET_NODE_ID"], x["EDGE_CLASS"])
        )
    ]
    return hashlib.sha256("\n".join(stable).encode()).hexdigest()


def reachability_hash(rows: list[dict[str, Any]]) -> str:
    stable = [
        json.dumps(r, sort_keys=True, separators=(",", ":"))
        for r in sorted(rows, key=lambda x: (x["ROOT_ID"], x["NODE_ID"]))
    ]
    return hashlib.sha256("\n".join(stable).encode()).hexdigest()
