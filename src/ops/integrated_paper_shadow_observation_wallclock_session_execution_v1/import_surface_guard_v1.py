"""AST import / dependency surface guard for wallclock package."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    FORBIDDEN_IMPORT_PREFIXES,
)

IMPORT_SURFACE_GUARD_ID = "ops.paper_shadow_wallclock_import_surface_guard_v1"

_EXTRA_FORBIDDEN = frozenset(
    {
        "src.webui",
        "src.dashboard",
    }
)
_FORBIDDEN_CALL_NAMES = frozenset(
    {
        "place_order",
        "submit_order",
        "cancel_order",
        "amend_order",
        "create_order",
        "send_order",
        "broker_write",
    }
)

CAPABILITY_SOURCE_RELPATHS: tuple[str, ...] = (
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/__init__.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/constants_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/network_boundary_guard_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/eea_public_md_transport_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/authorization_consumption_runtime_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/session_runtime_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/session_state_machine_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/heartbeat_staleness_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/session_lock_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/killstate_runtime_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/wallclock_evidence_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/bundle_verifier_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/import_surface_guard_v1.py",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/observation_cycle_adapter_v1.py",
)


@dataclass
class ImportSurfaceAttestationV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    scanned_modules: list[str] = field(default_factory=list)
    dependency_manifest: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scan_source_for_forbidden_surfaces_v1(source: str, *, module_name: str) -> list[str]:
    blockers: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"SOURCE_PARSE_FAILED:{module_name}:{exc}"]
    prefixes = tuple(FORBIDDEN_IMPORT_PREFIXES) + tuple(_EXTRA_FORBIDDEN)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                for prefix in prefixes:
                    if name == prefix or name.startswith(prefix + "."):
                        blockers.append(f"FORBIDDEN_IMPORT:{module_name}:{name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for prefix in prefixes:
                if mod == prefix or mod.startswith(prefix + "."):
                    blockers.append(f"FORBIDDEN_IMPORT_FROM:{module_name}:{mod}")
            if "okx" in mod.lower() and "private" in mod.lower():
                blockers.append(f"PRIVATE_OKX_CLIENT_IMPORT:{module_name}:{mod}")
        elif isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in _FORBIDDEN_CALL_NAMES:
                blockers.append(f"FORBIDDEN_CALL:{module_name}:{name}")
    return blockers


def attest_wallclock_import_surface_v1(
    *,
    repo_root: Path,
    relative_paths: Sequence[str] | None = None,
) -> ImportSurfaceAttestationV1:
    root = repo_root.resolve()
    paths = tuple(relative_paths or CAPABILITY_SOURCE_RELPATHS)
    blockers: list[str] = []
    scanned: list[str] = []
    deps: list[str] = []
    for rel in paths:
        path = (root / rel).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            blockers.append(f"PATH_OUTSIDE_REPO:{rel}")
            continue
        if not path.is_file():
            blockers.append(f"SOURCE_MISSING:{rel}")
            continue
        scanned.append(rel)
        src = path.read_text(encoding="utf-8")
        blockers.extend(scan_source_for_forbidden_surfaces_v1(src, module_name=rel))
        try:
            tree = ast.parse(src)
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    deps.append(ast.dump(node, include_attributes=False))
        except SyntaxError:
            pass
    return ImportSurfaceAttestationV1(
        ok=not blockers,
        blockers=sorted(set(blockers)),
        scanned_modules=scanned,
        dependency_manifest=deps,
    )
