#!/usr/bin/env python3
"""Operational CLI for Dynamic Scope archive sibling export (PR B).

Reads canonical Dynamic Scope durable state unchanged and exports the existing
source-sibling payload via ``export_archive_sibling_json_v1`` only.

Invariants:
- DEFAULT_DRY_RUN=true
- write only when dry_run=false AND write_authorized=true
- target relative path fixed: readmodels/dynamic_scope_state_v1.json
- no archive discovery / latest fallback / active-archive auto-selection
- no producer, scheduler, runtime, dashboard, or trading mutation
- AUTHORITY_EFFECT=NONE
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.archive_sibling_export_contract_v1 import (
    ArchiveSiblingExportEffectV1,
    export_archive_sibling_json_v1,
)
from src.ops.dynamic_scope_archive_sibling_exporter_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    SOURCE_SCHEMA,
    SOURCE_STATE_VERSION,
    TARGET_RELATIVE_PATH,
)
from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    SCHEMA_VERSION,
    STATE_VERSION,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.persistence_v1 import (
    DynamicScopePersistenceError,
    load_dynamic_scope_state_v1,
    scope_state_path,
)
from src.ops.dynamic_scope_persistence_binding_v1.reason_codes_v1 import (
    DynamicScopeBindingFailureCodeV1,
)

CLI_ID = "run_dynamic_scope_archive_sibling_exporter_v1"
CONTRACT_NAME = SOURCE_SCHEMA
DEFAULT_DRY_RUN = True
REQUIRED_PAYLOAD_FIELDS: tuple[str, ...] = (
    "schema_version",
    "state_version",
    "scope_session_id",
    "instrument_id",
)

ERROR_SOURCE_MISSING = "DYNAMIC_SCOPE_CLI_SOURCE_MISSING"
ERROR_SOURCE_CORRUPT = "DYNAMIC_SCOPE_CLI_SOURCE_CORRUPT"
ERROR_SOURCE_SCHEMA_MISMATCH = "DYNAMIC_SCOPE_CLI_SOURCE_SCHEMA_MISMATCH"
ERROR_SOURCE_STATE_VERSION_MISMATCH = "DYNAMIC_SCOPE_CLI_SOURCE_STATE_VERSION_MISMATCH"
ERROR_SOURCE_LOAD_FAILED = "DYNAMIC_SCOPE_CLI_SOURCE_LOAD_FAILED"
ERROR_SOURCE_TYPE_MISMATCH = "DYNAMIC_SCOPE_CLI_SOURCE_TYPE_MISMATCH"
ERROR_EXPORT_BLOCKED = "DYNAMIC_SCOPE_CLI_EXPORT_BLOCKED"


@dataclass(frozen=True)
class CliExportOutcomeV1:
    """Machine-readable CLI outcome without payload content or secrets."""

    ok: bool
    effect: str
    write_performed: bool
    dry_run: bool
    write_authorized: bool
    archive_root: str
    dynamic_scope_state_root: str
    source_path: str
    target_relative_path: str
    target_path: str | None
    contract_name: str
    source_digest: str | None = None
    target_digest_before: str | None = None
    target_digest_after: str | None = None
    expected_target_digest: str | None = None
    block_reason: str | None = None
    error_code: str | None = None
    schema_version: str | None = None
    state_version: str | None = None
    capability_id: str = CAPABILITY_ID
    cli_id: str = CLI_ID
    authority_effect: str = AUTHORITY_EFFECT
    export_contract: str = "export_archive_sibling_json_v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "effect": self.effect,
            "write_performed": self.write_performed,
            "dry_run": self.dry_run,
            "write_authorized": self.write_authorized,
            "archive_root": self.archive_root,
            "dynamic_scope_state_root": self.dynamic_scope_state_root,
            "source_path": self.source_path,
            "target_relative_path": self.target_relative_path,
            "target_path": self.target_path,
            "contract_name": self.contract_name,
            "source_digest": self.source_digest,
            "target_digest_before": self.target_digest_before,
            "target_digest_after": self.target_digest_after,
            "expected_target_digest": self.expected_target_digest,
            "block_reason": self.block_reason,
            "error_code": self.error_code,
            "schema_version": self.schema_version,
            "state_version": self.state_version,
            "capability_id": self.capability_id,
            "cli_id": self.cli_id,
            "authority_effect": self.authority_effect,
            "export_contract": self.export_contract,
            "default_dry_run": DEFAULT_DRY_RUN,
        }


def _blocked_outcome(
    *,
    dry_run: bool,
    write_authorized: bool,
    archive_root: str,
    dynamic_scope_state_root: str,
    source_path: str,
    error_code: str,
    block_reason: str,
    schema_version: str | None = None,
    state_version: str | None = None,
) -> CliExportOutcomeV1:
    return CliExportOutcomeV1(
        ok=False,
        effect=ArchiveSiblingExportEffectV1.BLOCKED.value,
        write_performed=False,
        dry_run=dry_run,
        write_authorized=write_authorized,
        archive_root=archive_root,
        dynamic_scope_state_root=dynamic_scope_state_root,
        source_path=source_path,
        target_relative_path=TARGET_RELATIVE_PATH,
        target_path=None,
        contract_name=CONTRACT_NAME,
        block_reason=block_reason,
        error_code=error_code,
        schema_version=schema_version,
        state_version=state_version,
    )


def _map_load_error(exc: DynamicScopePersistenceError) -> tuple[str, str]:
    detail = " ".join(str(a) for a in exc.args)
    if (
        exc.code is DynamicScopeBindingFailureCodeV1.STATE_VERSION_MISMATCH
        or "UNSUPPORTED_DYNAMIC_SCOPE_STATE_VERSION:" in detail
    ):
        return ERROR_SOURCE_STATE_VERSION_MISMATCH, detail or ERROR_SOURCE_STATE_VERSION_MISMATCH
    if exc.code is DynamicScopeBindingFailureCodeV1.CORRUPTED_CHECKPOINT:
        return ERROR_SOURCE_CORRUPT, detail or ERROR_SOURCE_CORRUPT
    if exc.code in {
        DynamicScopeBindingFailureCodeV1.CHECKPOINT_MISSING_BEFORE_FIRST_STATE,
        DynamicScopeBindingFailureCodeV1.CHECKPOINT_MISSING_AFTER_PRIOR_COMMIT,
    }:
        return ERROR_SOURCE_MISSING, detail or ERROR_SOURCE_MISSING
    return ERROR_SOURCE_LOAD_FAILED, detail or ERROR_SOURCE_LOAD_FAILED


def load_dynamic_scope_export_payload_v1(
    *,
    dynamic_scope_state_root: Path | str,
) -> tuple[dict[str, Any], Path] | CliExportOutcomeV1:
    """Load canonical durable state and return ``to_dict()`` payload + source path.

    On failure returns a blocked CLI outcome (fail-closed; no write attempted).
    """
    state_root = Path(dynamic_scope_state_root).expanduser()
    source_path = scope_state_path(state_root)
    root_str = str(state_root)
    source_str = str(source_path)

    if not source_path.is_file():
        return _blocked_outcome(
            dry_run=True,
            write_authorized=False,
            archive_root="",
            dynamic_scope_state_root=root_str,
            source_path=source_str,
            error_code=ERROR_SOURCE_MISSING,
            block_reason=f"missing source file: {source_str}",
        )

    try:
        loaded = load_dynamic_scope_state_v1(state_root, require_present=True)
    except DynamicScopePersistenceError as exc:
        code, reason = _map_load_error(exc)
        return _blocked_outcome(
            dry_run=True,
            write_authorized=False,
            archive_root="",
            dynamic_scope_state_root=root_str,
            source_path=source_str,
            error_code=code,
            block_reason=reason,
        )
    except Exception as exc:  # noqa: BLE001 — fail-closed wrapper
        return _blocked_outcome(
            dry_run=True,
            write_authorized=False,
            archive_root="",
            dynamic_scope_state_root=root_str,
            source_path=source_str,
            error_code=ERROR_SOURCE_LOAD_FAILED,
            block_reason=str(exc),
        )

    if loaded is None:
        return _blocked_outcome(
            dry_run=True,
            write_authorized=False,
            archive_root="",
            dynamic_scope_state_root=root_str,
            source_path=source_str,
            error_code=ERROR_SOURCE_MISSING,
            block_reason="load_dynamic_scope_state_v1 returned None",
        )

    if not isinstance(loaded, CanonicalDynamicScopeStateV1):
        return _blocked_outcome(
            dry_run=True,
            write_authorized=False,
            archive_root="",
            dynamic_scope_state_root=root_str,
            source_path=source_str,
            error_code=ERROR_SOURCE_TYPE_MISMATCH,
            block_reason="loaded object is not CanonicalDynamicScopeStateV1",
        )

    payload = loaded.to_dict()
    schema_version = str(payload.get("schema_version") or "")
    state_version = str(payload.get("state_version") or "")
    if schema_version != SCHEMA_VERSION or schema_version != SOURCE_SCHEMA:
        return _blocked_outcome(
            dry_run=True,
            write_authorized=False,
            archive_root="",
            dynamic_scope_state_root=root_str,
            source_path=source_str,
            error_code=ERROR_SOURCE_SCHEMA_MISMATCH,
            block_reason=f"schema_version={schema_version!r} expected={SCHEMA_VERSION!r}",
            schema_version=schema_version or None,
            state_version=state_version or None,
        )
    if state_version != STATE_VERSION or state_version != SOURCE_STATE_VERSION:
        return _blocked_outcome(
            dry_run=True,
            write_authorized=False,
            archive_root="",
            dynamic_scope_state_root=root_str,
            source_path=source_str,
            error_code=ERROR_SOURCE_STATE_VERSION_MISMATCH,
            block_reason=f"state_version={state_version!r} expected={STATE_VERSION!r}",
            schema_version=schema_version or None,
            state_version=state_version or None,
        )

    return payload, source_path


def run_dynamic_scope_archive_sibling_exporter_cli_v1(
    *,
    archive_root: Path | str,
    dynamic_scope_state_root: Path | str,
    dry_run: bool = DEFAULT_DRY_RUN,
    write_authorized: bool = False,
) -> CliExportOutcomeV1:
    """Export Dynamic Scope source sibling via PR-A contract only."""
    archive = Path(archive_root).expanduser()
    state_root = Path(dynamic_scope_state_root).expanduser()
    effective_dry_run = bool(dry_run)
    authorized = bool(write_authorized)

    loaded = load_dynamic_scope_export_payload_v1(dynamic_scope_state_root=state_root)
    if isinstance(loaded, CliExportOutcomeV1):
        # Preserve caller dry_run / write_authorized flags on source failures.
        return CliExportOutcomeV1(
            ok=False,
            effect=loaded.effect,
            write_performed=False,
            dry_run=effective_dry_run,
            write_authorized=authorized,
            archive_root=str(archive),
            dynamic_scope_state_root=str(state_root),
            source_path=loaded.source_path,
            target_relative_path=TARGET_RELATIVE_PATH,
            target_path=None,
            contract_name=CONTRACT_NAME,
            block_reason=loaded.block_reason,
            error_code=loaded.error_code,
            schema_version=loaded.schema_version,
            state_version=loaded.state_version,
        )

    payload, source_path = loaded
    schema_version = str(payload.get("schema_version") or "")
    state_version = str(payload.get("state_version") or "")

    # Exclusive write path: PR-A contract only (no local atomic/digest/path guard).
    result = export_archive_sibling_json_v1(
        payload=payload,
        archive_root=archive,
        target_relative_path=TARGET_RELATIVE_PATH,
        contract_name=CONTRACT_NAME,
        required_fields=REQUIRED_PAYLOAD_FIELDS,
        dry_run=effective_dry_run,
        write_authorized=authorized,
    )

    ok = result.effect != ArchiveSiblingExportEffectV1.BLOCKED and result.block_reason is None
    error_code = None if ok else ERROR_EXPORT_BLOCKED
    return CliExportOutcomeV1(
        ok=ok,
        effect=result.effect.value,
        write_performed=bool(result.write_performed),
        dry_run=bool(result.dry_run),
        write_authorized=authorized,
        archive_root=str(archive),
        dynamic_scope_state_root=str(state_root),
        source_path=str(source_path),
        target_relative_path=TARGET_RELATIVE_PATH,
        target_path=result.target_path,
        contract_name=result.contract_name,
        source_digest=result.source_digest,
        target_digest_before=result.target_digest_before,
        target_digest_after=result.target_digest_after,
        expected_target_digest=result.expected_target_digest,
        block_reason=result.block_reason,
        error_code=error_code,
        schema_version=schema_version or None,
        state_version=state_version or None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export CanonicalDynamicScopeStateV1 as archive sibling under "
            "readmodels/dynamic_scope_state_v1.json via export_archive_sibling_json_v1. "
            "Default is dry-run; write requires --no-dry-run and --write-authorized. "
            "Does not discover archives or select latest."
        )
    )
    parser.add_argument(
        "--archive-root",
        required=True,
        help="Explicit archive root (no discovery / no latest fallback).",
    )
    parser.add_argument(
        "--dynamic-scope-state-root",
        required=True,
        help=(
            "Repository-backed Dynamic Scope durable state root containing "
            "dynamic_scope_state_v1.json (canonical loader path)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_DRY_RUN,
        help=f"Dry-run mode (default: {str(DEFAULT_DRY_RUN).lower()}).",
    )
    parser.add_argument(
        "--write-authorized",
        action="store_true",
        default=False,
        help="Explicit write authorization; required together with --no-dry-run.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    outcome = run_dynamic_scope_archive_sibling_exporter_cli_v1(
        archive_root=args.archive_root,
        dynamic_scope_state_root=args.dynamic_scope_state_root,
        dry_run=bool(args.dry_run),
        write_authorized=bool(args.write_authorized),
    )
    print(json.dumps(outcome.to_dict(), sort_keys=True, ensure_ascii=False))
    return 0 if outcome.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
