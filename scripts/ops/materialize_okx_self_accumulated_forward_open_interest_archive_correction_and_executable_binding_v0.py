#!/usr/bin/env python3
"""Materialize OKX self-accumulated forward OI archive correction and executable binding v0.

Contract-only slice: classifies fixture provenance, validates executable binding,
and emits a non-authorizing correction execution plan.
Operator GO: GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_CORRECTION_AND_EXECUTABLE_BINDING_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0 import (  # noqa: E402
    CONFIRM_GO,
    exit_code_for_materialization_result_v0,
    materialization_result_to_dict_v0,
    materialize_contract_bundle_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize OKX self-accumulated forward OI archive correction "
            "and executable binding contract v0."
        )
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        help=f"Required operator GO token ({CONFIRM_GO})",
    )
    parser.add_argument(
        "--source-snapshot-dir",
        type=Path,
        required=True,
        help="Existing self-accumulated archive snapshot directory",
    )
    parser.add_argument(
        "--collection-binding",
        type=Path,
        required=True,
        help="Collection binding JSON describing collector provenance",
    )
    parser.add_argument(
        "--evidence-ref",
        default=None,
        help="Optional durable evidence reference for collection execution",
    )
    parser.add_argument(
        "--collection-execution-id",
        required=True,
        help="Collection execution identifier for provenance binding",
    )
    parser.add_argument(
        "--external-reference-input",
        type=Path,
        default=None,
        help="Optional external reference snapshot for validation-only planning",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory for contract artifacts",
    )
    parser.add_argument(
        "--enabled",
        action="store_true",
        help="Explicit enable flag; default-off without this flag",
    )
    args = parser.parse_args(argv)

    if not args.enabled:
        _die("ERR: DEFAULT_OFF_ENABLED_FLAG_REQUIRED")

    created_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = materialize_contract_bundle_v0(
        confirm=args.confirm_go_token,
        enabled=True,
        source_snapshot_dir=args.source_snapshot_dir,
        collection_binding_path=args.collection_binding,
        evidence_ref=args.evidence_ref,
        collection_execution_id=args.collection_execution_id,
        created_at_utc=created_at_utc,
        external_reference_input=(
            str(args.external_reference_input)
            if args.external_reference_input is not None
            else None
        ),
    )
    report = materialization_result_to_dict_v0(result)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    artifact_map = {
        "archive_correction_contract.json": report["archive_correction_contract"],
        "archive_observation_provenance_contract.json": report["provenance_records"],
        "archive_admissibility_contract.json": report["admissibility_assessments"],
        "archive_generation_binding_contract.json": report["generation_binding"],
        "archive_supersession_contract.json": report["supersession_records"],
        "executable_binding_contract.json": report["executable_binding"],
        "correction_execution_plan.json": report["correction_execution_plan"],
        "materialization_report.json": report,
    }
    for name, payload in artifact_map.items():
        (args.output_dir / name).write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, sort_keys=True, indent=2))
    return exit_code_for_materialization_result_v0(result)


if __name__ == "__main__":
    raise SystemExit(main())
