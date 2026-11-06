#!/usr/bin/env python3
"""Operational CLI for Canonical Decision archive sibling export.

Reads an already-produced CanonicalTradingDecisionEvidenceV1 JSON from an
explicit path and exports it via ``export_archive_sibling_json_v1`` only.

Invariants:
- DEFAULT_DRY_RUN=true
- write only when dry_run=false AND write_authorized=true
- target relative path fixed: readmodels/canonical_trading_decision_evidence.v1.json
- no archive discovery / latest fallback / active-archive auto-selection
- no decision recomputation, producer, scheduler, runtime, dashboard mutation
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
from src.ops.canonical_decision_archive_sibling_exporter_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    CONTRACT_NAME,
    DECISION_AUTHORITY_EFFECT,
    ERROR_PATH_REQUIRED,
    ERROR_SOURCE_CORRUPT,
    ERROR_SOURCE_INVALID,
    ERROR_SOURCE_LOAD_FAILED,
    ERROR_SOURCE_MISSING,
    ERROR_SOURCE_SCHEMA_MISMATCH,
    REQUIRED_EVIDENCE_FIELDS,
    SOURCE_EVIDENCE_SCHEMA_VERSION,
    TARGET_RELATIVE_PATH,
)
from src.ops.canonical_decision_archive_sibling_exporter_v1.exporter_v1 import (
    load_canonical_decision_evidence_export_payload_v1,
)

CLI_ID = "run_canonical_decision_archive_sibling_exporter_v1"
DEFAULT_DRY_RUN = True
REQUIRED_PAYLOAD_FIELDS: tuple[str, ...] = REQUIRED_EVIDENCE_FIELDS

ERROR_SOURCE_MISSING_CLI = "CANONICAL_DECISION_CLI_SOURCE_MISSING"
ERROR_SOURCE_CORRUPT_CLI = "CANONICAL_DECISION_CLI_SOURCE_CORRUPT"
ERROR_SOURCE_SCHEMA_MISMATCH_CLI = "CANONICAL_DECISION_CLI_SOURCE_SCHEMA_MISMATCH"
ERROR_SOURCE_INVALID_CLI = "CANONICAL_DECISION_CLI_SOURCE_INVALID"
ERROR_SOURCE_LOAD_FAILED_CLI = "CANONICAL_DECISION_CLI_SOURCE_LOAD_FAILED"
ERROR_EXPORT_BLOCKED = "CANONICAL_DECISION_CLI_EXPORT_BLOCKED"
ERROR_PATH_REQUIRED_CLI = "CANONICAL_DECISION_CLI_PATH_REQUIRED"

_LOAD_ERROR_MAP = {
    ERROR_SOURCE_MISSING: ERROR_SOURCE_MISSING_CLI,
    ERROR_SOURCE_CORRUPT: ERROR_SOURCE_CORRUPT_CLI,
    ERROR_SOURCE_SCHEMA_MISMATCH: ERROR_SOURCE_SCHEMA_MISMATCH_CLI,
    ERROR_SOURCE_INVALID: ERROR_SOURCE_INVALID_CLI,
    ERROR_SOURCE_LOAD_FAILED: ERROR_SOURCE_LOAD_FAILED_CLI,
    ERROR_PATH_REQUIRED: ERROR_PATH_REQUIRED_CLI,
}


@dataclass(frozen=True)
class CliExportOutcomeV1:
    """Machine-readable CLI outcome without payload content or secrets."""

    ok: bool
    effect: str
    write_performed: bool
    dry_run: bool
    write_authorized: bool
    archive_root: str
    evidence_source_path: str
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
    evidence_schema_version: str | None = None
    decision_id: str | None = None
    capability_id: str = CAPABILITY_ID
    cli_id: str = CLI_ID
    authority_effect: str = AUTHORITY_EFFECT
    decision_authority_effect: str = DECISION_AUTHORITY_EFFECT
    export_contract: str = "export_archive_sibling_json_v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "effect": self.effect,
            "write_performed": self.write_performed,
            "dry_run": self.dry_run,
            "write_authorized": self.write_authorized,
            "archive_root": self.archive_root,
            "evidence_source_path": self.evidence_source_path,
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
            "evidence_schema_version": self.evidence_schema_version,
            "decision_id": self.decision_id,
            "capability_id": self.capability_id,
            "cli_id": self.cli_id,
            "authority_effect": self.authority_effect,
            "decision_authority_effect": self.decision_authority_effect,
            "export_contract": self.export_contract,
            "default_dry_run": DEFAULT_DRY_RUN,
        }


def _blocked_outcome(
    *,
    dry_run: bool,
    write_authorized: bool,
    archive_root: str,
    evidence_source_path: str,
    source_path: str,
    error_code: str,
    block_reason: str,
    evidence_schema_version: str | None = None,
    decision_id: str | None = None,
) -> CliExportOutcomeV1:
    return CliExportOutcomeV1(
        ok=False,
        effect=ArchiveSiblingExportEffectV1.BLOCKED.value,
        write_performed=False,
        dry_run=dry_run,
        write_authorized=write_authorized,
        archive_root=archive_root,
        evidence_source_path=evidence_source_path,
        source_path=source_path,
        target_relative_path=TARGET_RELATIVE_PATH,
        target_path=None,
        contract_name=CONTRACT_NAME,
        block_reason=block_reason,
        error_code=error_code,
        evidence_schema_version=evidence_schema_version,
        decision_id=decision_id,
    )


def run_canonical_decision_archive_sibling_exporter_cli_v1(
    *,
    archive_root: Path | str,
    evidence_source_path: Path | str,
    dry_run: bool = DEFAULT_DRY_RUN,
    write_authorized: bool = False,
) -> CliExportOutcomeV1:
    """Export Canonical Decision source sibling via PR-A contract only."""
    archive = Path(archive_root).expanduser()
    source_arg = Path(evidence_source_path).expanduser()
    effective_dry_run = bool(dry_run)
    authorized = bool(write_authorized)

    evidence, source_path, load_error = load_canonical_decision_evidence_export_payload_v1(
        source_arg
    )
    if evidence is None:
        mapped = _LOAD_ERROR_MAP.get(load_error or "", ERROR_SOURCE_LOAD_FAILED_CLI)
        return _blocked_outcome(
            dry_run=effective_dry_run,
            write_authorized=authorized,
            archive_root=str(archive),
            evidence_source_path=str(source_arg),
            source_path=source_path or str(source_arg),
            error_code=mapped,
            block_reason=load_error or mapped,
        )

    schema_version = str(evidence.get("evidence_schema_version") or "")
    decision_id = str(evidence.get("decision_id") or "")

    result = export_archive_sibling_json_v1(
        payload=evidence,
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
        evidence_source_path=str(source_arg),
        source_path=source_path,
        target_relative_path=TARGET_RELATIVE_PATH,
        target_path=result.target_path,
        contract_name=result.contract_name,
        source_digest=result.source_digest,
        target_digest_before=result.target_digest_before,
        target_digest_after=result.target_digest_after,
        expected_target_digest=result.expected_target_digest,
        block_reason=result.block_reason,
        error_code=error_code,
        evidence_schema_version=schema_version or None,
        decision_id=decision_id or None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export already-produced CanonicalTradingDecisionEvidenceV1 as archive "
            "sibling under readmodels/canonical_trading_decision_evidence.v1.json via "
            "export_archive_sibling_json_v1. Default is dry-run; write requires "
            "--no-dry-run and --write-authorized. Does not discover archives, select "
            "latest, or recompute decisions."
        )
    )
    parser.add_argument(
        "--archive-root",
        required=True,
        help="Explicit archive root (no discovery / no latest fallback).",
    )
    parser.add_argument(
        "--evidence-source-path",
        required=True,
        help=(
            "Explicit path to an already-produced CanonicalTradingDecisionEvidenceV1 "
            f"JSON file (schema {SOURCE_EVIDENCE_SCHEMA_VERSION})."
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

    outcome = run_canonical_decision_archive_sibling_exporter_cli_v1(
        archive_root=args.archive_root,
        evidence_source_path=args.evidence_source_path,
        dry_run=bool(args.dry_run),
        write_authorized=bool(args.write_authorized),
    )
    print(json.dumps(outcome.to_dict(), sort_keys=True, ensure_ascii=False))
    return 0 if outcome.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
