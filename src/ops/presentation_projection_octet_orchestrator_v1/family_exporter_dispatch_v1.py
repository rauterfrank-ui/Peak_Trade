"""Family exporter dispatch for the presentation projection octet orchestrator.

PR-C integrates exactly one family (``dynamic_scope``) by invoking the existing
exporter CLI via subprocess. No export logic is duplicated here.

Invariants:
- DEFAULT_DRY_RUN=true
- write only when dry_run=false AND write_authorized=true (both gates)
- CLI path only: scripts/ops/run_dynamic_scope_archive_sibling_exporter_v1.py
- no other families integrated
- fail-closed on unknown family, missing inputs, subprocess/exit failures
- AUTHORITY_EFFECT=NONE
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.ops.presentation_projection_octet_orchestrator_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    DEFAULT_DRY_RUN,
    ERROR_ARCHIVE_ROOT_REQUIRED,
    ERROR_EXPORTER_CLI_MISSING,
    ERROR_EXPORTER_FAMILY_NOT_INTEGRATED,
    ERROR_EXPORTER_NONZERO_EXIT,
    ERROR_EXPORTER_STATE_ROOT_REQUIRED,
    ERROR_EXPORTER_SUBPROCESS_FAILED,
    EXPORTER_CLI_RELATIVE_PATH_BY_FAMILY,
    EXPORTER_INTEGRATED_FAMILIES,
    FAMILY_DYNAMIC_SCOPE,
    ORCHESTRATOR_AUTHORITY_EFFECT,
    OWNER,
)


def integrated_exporter_families_v1() -> tuple[str, ...]:
    """Return the ratified exporter-integrated family ids (PR-C: dynamic_scope only)."""
    return EXPORTER_INTEGRATED_FAMILIES


def exporter_cli_relative_path_for_family_v1(family_id: str) -> str | None:
    """Return the repository-relative exporter CLI path for an integrated family."""
    return EXPORTER_CLI_RELATIVE_PATH_BY_FAMILY.get(family_id)


@dataclass(frozen=True)
class OctetFamilyExporterResultV1:
    """Fail-closed outcome of one family exporter CLI invocation."""

    family_id: str
    ok: bool
    dry_run: bool
    write_authorized: bool
    write_gate_open: bool
    archive_root: str
    dynamic_scope_state_root: str | None
    cli_relative_path: str | None
    argv: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    errors: tuple[str, ...]
    cli_ok: bool | None = None
    cli_effect: str | None = None
    write_performed: bool = False
    capability_id: str = CAPABILITY_ID
    authority_effect: str = AUTHORITY_EFFECT
    orchestrator_authority_effect: str = ORCHESTRATOR_AUTHORITY_EFFECT
    owner: str = OWNER
    default_dry_run: bool = DEFAULT_DRY_RUN

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require_nonempty_str(value: object | None) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _repo_root() -> Path:
    # src/ops/<package>/<module>.py -> repository root
    return Path(__file__).resolve().parents[3]


def _write_gate_open(*, dry_run: bool, write_authorized: bool) -> bool:
    return (not bool(dry_run)) and bool(write_authorized)


def build_family_exporter_argv_v1(
    *,
    family_id: str,
    archive_root: str | Path,
    dynamic_scope_state_root: str | Path | None,
    dry_run: bool = DEFAULT_DRY_RUN,
    write_authorized: bool = False,
    python_executable: str | None = None,
    repo_root: str | Path | None = None,
) -> tuple[list[str] | None, tuple[str, ...]]:
    """Build a safe argv for an integrated family exporter CLI.

    Returns ``(argv, errors)``. On any contract failure ``argv`` is ``None``.
    """
    family = _require_nonempty_str(family_id)
    if family is None or family not in EXPORTER_INTEGRATED_FAMILIES:
        return None, (ERROR_EXPORTER_FAMILY_NOT_INTEGRATED,)

    archive = _require_nonempty_str(str(archive_root) if archive_root is not None else None)
    if archive is None:
        return None, (ERROR_ARCHIVE_ROOT_REQUIRED,)

    cli_rel = EXPORTER_CLI_RELATIVE_PATH_BY_FAMILY.get(family)
    if cli_rel is None:
        return None, (ERROR_EXPORTER_FAMILY_NOT_INTEGRATED,)

    root = Path(repo_root).expanduser().resolve() if repo_root is not None else _repo_root()
    cli_path = (root / cli_rel).resolve()
    if not cli_path.is_file():
        return None, (ERROR_EXPORTER_CLI_MISSING,)

    python = python_executable if _require_nonempty_str(python_executable) else sys.executable
    argv: list[str] = [
        str(python),
        str(cli_path),
        "--archive-root",
        str(Path(archive).expanduser()),
    ]

    if family == FAMILY_DYNAMIC_SCOPE:
        state_root = _require_nonempty_str(
            str(dynamic_scope_state_root) if dynamic_scope_state_root is not None else None
        )
        if state_root is None:
            return None, (ERROR_EXPORTER_STATE_ROOT_REQUIRED,)
        argv.extend(
            [
                "--dynamic-scope-state-root",
                str(Path(state_root).expanduser()),
            ]
        )
    else:
        # Defensive: registry must remain dynamic_scope-only for PR-C.
        return None, (ERROR_EXPORTER_FAMILY_NOT_INTEGRATED,)

    # Explicit BooleanOptionalAction tokens; never imply write from absence.
    if bool(dry_run):
        argv.append("--dry-run")
    else:
        argv.append("--no-dry-run")

    if bool(write_authorized):
        argv.append("--write-authorized")

    return argv, ()


def _parse_cli_stdout(stdout: str) -> tuple[bool | None, str | None, bool]:
    text = (stdout or "").strip()
    if not text:
        return None, None, False
    try:
        payload = json.loads(text.splitlines()[-1])
    except (json.JSONDecodeError, TypeError, ValueError):
        return None, None, False
    if not isinstance(payload, Mapping):
        return None, None, False
    cli_ok = payload.get("ok")
    effect = payload.get("effect")
    write_performed = bool(payload.get("write_performed"))
    return (
        bool(cli_ok) if isinstance(cli_ok, bool) else None,
        str(effect) if isinstance(effect, str) else None,
        write_performed,
    )


def run_octet_family_exporter_v1(
    *,
    family_id: str,
    archive_root: str | Path,
    dynamic_scope_state_root: str | Path | None = None,
    dry_run: bool = DEFAULT_DRY_RUN,
    write_authorized: bool = False,
    python_executable: str | None = None,
    repo_root: str | Path | None = None,
    subprocess_runner: Any | None = None,
) -> OctetFamilyExporterResultV1:
    """Invoke one integrated family exporter CLI fail-closed via subprocess."""
    effective_dry_run = bool(dry_run)
    authorized = bool(write_authorized)
    gate_open = _write_gate_open(dry_run=effective_dry_run, write_authorized=authorized)
    family = _require_nonempty_str(family_id) or str(family_id)
    archive_str = (
        _require_nonempty_str(str(archive_root) if archive_root is not None else None) or ""
    )
    state_str = _require_nonempty_str(
        str(dynamic_scope_state_root) if dynamic_scope_state_root is not None else None
    )
    cli_rel = exporter_cli_relative_path_for_family_v1(family)

    argv, errors = build_family_exporter_argv_v1(
        family_id=family,
        archive_root=archive_root,
        dynamic_scope_state_root=dynamic_scope_state_root,
        dry_run=effective_dry_run,
        write_authorized=authorized,
        python_executable=python_executable,
        repo_root=repo_root,
    )
    if argv is None:
        return OctetFamilyExporterResultV1(
            family_id=family,
            ok=False,
            dry_run=effective_dry_run,
            write_authorized=authorized,
            write_gate_open=gate_open,
            archive_root=archive_str,
            dynamic_scope_state_root=state_str,
            cli_relative_path=cli_rel,
            argv=(),
            exit_code=None,
            stdout="",
            stderr="",
            errors=errors,
            write_performed=False,
        )

    runner = subprocess.run if subprocess_runner is None else subprocess_runner
    try:
        completed = runner(
            argv,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return OctetFamilyExporterResultV1(
            family_id=family,
            ok=False,
            dry_run=effective_dry_run,
            write_authorized=authorized,
            write_gate_open=gate_open,
            archive_root=archive_str,
            dynamic_scope_state_root=state_str,
            cli_relative_path=cli_rel,
            argv=tuple(argv),
            exit_code=None,
            stdout="",
            stderr=str(exc),
            errors=(ERROR_EXPORTER_SUBPROCESS_FAILED,),
            write_performed=False,
        )

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    exit_code = int(completed.returncode)
    cli_ok, cli_effect, write_performed = _parse_cli_stdout(stdout)

    if exit_code != 0:
        return OctetFamilyExporterResultV1(
            family_id=family,
            ok=False,
            dry_run=effective_dry_run,
            write_authorized=authorized,
            write_gate_open=gate_open,
            archive_root=archive_str,
            dynamic_scope_state_root=state_str,
            cli_relative_path=cli_rel,
            argv=tuple(argv),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            errors=(ERROR_EXPORTER_NONZERO_EXIT,),
            cli_ok=cli_ok,
            cli_effect=cli_effect,
            write_performed=write_performed if gate_open else False,
        )

    # Nonzero already handled; still fail-closed if CLI JSON reports not ok.
    if cli_ok is False:
        return OctetFamilyExporterResultV1(
            family_id=family,
            ok=False,
            dry_run=effective_dry_run,
            write_authorized=authorized,
            write_gate_open=gate_open,
            archive_root=archive_str,
            dynamic_scope_state_root=state_str,
            cli_relative_path=cli_rel,
            argv=tuple(argv),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            errors=(ERROR_EXPORTER_NONZERO_EXIT,),
            cli_ok=cli_ok,
            cli_effect=cli_effect,
            write_performed=False,
        )

    return OctetFamilyExporterResultV1(
        family_id=family,
        ok=True,
        dry_run=effective_dry_run,
        write_authorized=authorized,
        write_gate_open=gate_open,
        archive_root=archive_str,
        dynamic_scope_state_root=state_str,
        cli_relative_path=cli_rel,
        argv=tuple(argv),
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        errors=(),
        cli_ok=True if cli_ok is None else cli_ok,
        cli_effect=cli_effect,
        write_performed=write_performed if gate_open else False,
    )


def run_octet_family_exporters_v1(
    *,
    archive_root: str | Path,
    families: Sequence[str] | None = None,
    dynamic_scope_state_root: str | Path | None = None,
    dry_run: bool = DEFAULT_DRY_RUN,
    write_authorized: bool = False,
    python_executable: str | None = None,
    repo_root: str | Path | None = None,
    subprocess_runner: Any | None = None,
) -> tuple[OctetFamilyExporterResultV1, ...]:
    """Dispatch exporter CLIs for selected integrated families (fail-closed per family).

    Default selection is exactly the integrated set (``dynamic_scope`` only).
    Unknown / non-integrated families return a blocked fail-closed result and do
    not abort sibling integrated families.
    """
    if families is None:
        selected: list[str] = list(EXPORTER_INTEGRATED_FAMILIES)
    else:
        selected = []
        seen: set[str] = set()
        for raw in families:
            family_id = str(raw).strip()
            if not family_id or family_id in seen:
                continue
            seen.add(family_id)
            selected.append(family_id)

    results: list[OctetFamilyExporterResultV1] = []
    for family_id in selected:
        results.append(
            run_octet_family_exporter_v1(
                family_id=family_id,
                archive_root=archive_root,
                dynamic_scope_state_root=dynamic_scope_state_root,
                dry_run=dry_run,
                write_authorized=write_authorized,
                python_executable=python_executable,
                repo_root=repo_root,
                subprocess_runner=subprocess_runner,
            )
        )
    return tuple(results)
