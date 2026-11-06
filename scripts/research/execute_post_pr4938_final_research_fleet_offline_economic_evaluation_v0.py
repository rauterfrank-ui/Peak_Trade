#!/usr/bin/env python3
"""Execute post-PR4938 final research fleet offline economic evaluation v0.

Operator GO:
GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_ONLY_NO_RUNTIME_AUTHORITY_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.post_pr4938_final_research_fleet_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    CONFIRM_GO,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    run_bounded_scope_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute post-PR4938 final research fleet offline economic evaluation v0"
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ARCHIVE_ROOT)
    args = parser.parse_args()

    try:
        result = run_bounded_scope_v0(
            confirm=args.confirm_go_token,
            repo_root=_REPO_ROOT,
            durable_evidence_root=args.durable_evidence_root,
        )
    except ValueError as exc:
        _die(f"ERR:{exc}")

    payload = {
        "verdict": result.fleet_verdict.value,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "fleet_status": result.fleet_status.value,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "candidate_terminal": result.candidate_terminal,
        "binding_integrity": result.binding_integrity,
        "manifest_verify_rc": result.manifest_verify_rc,
        "durable_evidence_path": str(result.evidence_root),
        "evaluation_executed": True,
        "runtime_authority_touched": False,
        "promotion_granted": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    for key, value in payload.items():
        print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
