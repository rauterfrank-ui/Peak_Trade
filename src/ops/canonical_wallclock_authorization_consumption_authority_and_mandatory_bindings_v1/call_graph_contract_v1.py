"""Architecture contract: all productive wallclock starts use the v2 gatekeeper."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


GATEKEEPER_FUNC = "consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1"
LEGACY_CONSUME_FUNC = "consume_authorization_for_wallclock_start_v1"
SESSION_RUNTIME_RELPATH = "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/session_runtime_v1.py"
PRODUCTIVE_ENTRY_RELPATH = (
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1/"
    "productive_run_entrypoint_v1.py"
)
LEGACY_CONSUME_RELPATH = (
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
    "authorization_consumption_runtime_v1.py"
)
CLI_RELPATH = "scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py"


@dataclass
class CallGraphContractResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "all_productive_wallclock_start_paths_use_canonical_v2_gate": self.ok,
        }


def _calls_name(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == name:
                return True
            if isinstance(func, ast.Attribute) and func.attr == name:
                return True
    return False


def _imports_name(tree: ast.AST, name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == name:
                    return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.endswith(name):
                    return True
    return False


def verify_wallclock_v2_gate_call_graph_v1(*, repo_root: Path) -> CallGraphContractResultV1:
    blockers: list[str] = []
    notes: list[str] = []

    session_path = repo_root / SESSION_RUNTIME_RELPATH
    entry_path = repo_root / PRODUCTIVE_ENTRY_RELPATH
    legacy_path = repo_root / LEGACY_CONSUME_RELPATH
    cli_path = repo_root / CLI_RELPATH

    for path in (session_path, entry_path, legacy_path, cli_path):
        if not path.is_file():
            blockers.append(f"MISSING_SOURCE:{path.relative_to(repo_root)}")

    if blockers:
        return CallGraphContractResultV1(ok=False, blockers=blockers)

    session_tree = ast.parse(session_path.read_text(encoding="utf-8"))
    if not _imports_name(session_tree, GATEKEEPER_FUNC) and not _calls_name(
        session_tree, GATEKEEPER_FUNC
    ):
        blockers.append("SESSION_RUNTIME_MISSING_V2_GATEKEEPER_CALL")
    if _calls_name(session_tree, LEGACY_CONSUME_FUNC):
        # Allowed only if it is not the productive consume path — fail if still called.
        blockers.append("SESSION_RUNTIME_STILL_CALLS_LEGACY_CONSUME")
    else:
        notes.append("SESSION_RUNTIME_USES_V2_GATEKEEPER")

    legacy_tree = ast.parse(legacy_path.read_text(encoding="utf-8"))
    # Legacy wrapper must quarantine / delegate, not productively consume V1 transitions.
    legacy_src = legacy_path.read_text(encoding="utf-8")
    if "AUTHORIZATION_SCHEMA_REJECTED_LEGACY" not in legacy_src:
        blockers.append("LEGACY_CONSUME_MISSING_QUARANTINE_REJECT")
    if "transition_consume_authorization_artifact_v1" in legacy_src:
        blockers.append("LEGACY_CONSUME_STILL_TRANSITIONS_V1")
    else:
        notes.append("LEGACY_CONSUME_V1_TRANSITION_REMOVED")

    entry_tree = ast.parse(entry_path.read_text(encoding="utf-8"))
    entry_src = entry_path.read_text(encoding="utf-8")
    if (
        "load_authorization_artifact_v1" in entry_src
        and "AUTHORIZATION_SCHEMA_REJECTED_LEGACY" not in entry_src
    ):
        blockers.append("PRODUCTIVE_ENTRY_LOADS_V1_WITHOUT_QUARANTINE")
    if "WallclockSessionRuntimeV1" not in entry_src:
        blockers.append("PRODUCTIVE_ENTRY_MISSING_SESSION_RUNTIME")
    else:
        notes.append("PRODUCTIVE_ENTRY_DELEGATES_TO_SESSION_RUNTIME")

    cli_src = cli_path.read_text(encoding="utf-8")
    if "run_productive_wallclock_session_from_paths_v1" not in cli_src:
        blockers.append("CLI_MISSING_PRODUCTIVE_ENTRYPOINT")
    else:
        notes.append("CLI_DELEGATES_TO_PRODUCTIVE_ENTRYPOINT")

    # Ensure gatekeeper module exists and defines the function.
    gk = (
        repo_root
        / "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1"
        / "wallclock_v2_gatekeeper_v1.py"
    )
    if not gk.is_file():
        blockers.append("GATEKEEPER_MODULE_MISSING")
    else:
        gk_tree = ast.parse(gk.read_text(encoding="utf-8"))
        defined = {
            n.name for n in gk_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        if GATEKEEPER_FUNC not in defined:
            blockers.append("GATEKEEPER_FUNC_UNDEFINED")
        else:
            notes.append("GATEKEEPER_FUNC_DEFINED")

    return CallGraphContractResultV1(ok=not blockers, blockers=sorted(set(blockers)), notes=notes)
