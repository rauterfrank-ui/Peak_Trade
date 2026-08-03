"""macOS portability preflight for O1 (no launcher / no supervisor)."""

from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.canonical_runtime_environment_contract_v1.constants_v1 import (
    MACOS_PORTABILITY_CONTRACT,
)


@dataclass(frozen=True)
class MacOsPortabilityPreflightResultV1:
    ok: bool
    setsid_cli_required: bool
    setsid_cli_present: bool
    python_os_setsid_available: bool
    start_new_session_allowed: bool
    launch_backend_deferred_to_o2: bool
    platform: str
    blockers: tuple[str, ...]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_macos_portability_preflight_v1() -> MacOsPortabilityPreflightResultV1:
    """O1 contract: setsid CLI must not be required; os.setsid may exist."""
    setsid_cli_required = bool(MACOS_PORTABILITY_CONTRACT["SETSID_CLI_REQUIRED"])
    setsid_cli_present = shutil.which("setsid") is not None
    python_os_setsid_available = hasattr(os, "setsid")
    start_new_session_allowed = bool(
        MACOS_PORTABILITY_CONTRACT["PYTHON_OS_SETSID_OR_START_NEW_SESSION_ALLOWED"]
    )
    launch_deferred = bool(MACOS_PORTABILITY_CONTRACT["LAUNCH_BACKEND_DEFERRED_TO_O2"])
    blockers: list[str] = []
    notes: list[str] = [
        "SETSID_CLI_REQUIRED=false",
        "PYTHON_OS_SETSID_OR_START_NEW_SESSION_ALLOWED=true",
        "LAUNCH_BACKEND_DEFERRED_TO_O2=true",
        "NO_PROCESS_SUPERVISOR_IN_O1",
        "NO_CANONICAL_LAUNCHER_IN_O1",
    ]
    if setsid_cli_required:
        blockers.append("PLATFORM_PORTABILITY_FAILURE:SETSID_CLI_REQUIRED_TRUE")
    if setsid_cli_required and not setsid_cli_present:
        blockers.append("PLATFORM_PORTABILITY_FAILURE:SETSID_CLI_MISSING")
    if start_new_session_allowed and not python_os_setsid_available:
        # Not a hard failure on exotic platforms; note only. Darwin has os.setsid.
        notes.append("PYTHON_OS_SETSID_ABSENT_NOTED")
    return MacOsPortabilityPreflightResultV1(
        ok=not blockers,
        setsid_cli_required=setsid_cli_required,
        setsid_cli_present=setsid_cli_present,
        python_os_setsid_available=python_os_setsid_available,
        start_new_session_allowed=start_new_session_allowed,
        launch_backend_deferred_to_o2=launch_deferred,
        platform=os.uname().sysname if hasattr(os, "uname") else "unknown",
        blockers=tuple(blockers),
        notes=tuple(notes),
    )
