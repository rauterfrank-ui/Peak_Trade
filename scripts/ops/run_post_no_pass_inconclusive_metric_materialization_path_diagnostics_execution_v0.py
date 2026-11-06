#!/usr/bin/env python3
"""Run post-no-pass inconclusive metric materialization path diagnostics execution v0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.research.post_no_pass_inconclusive_metric_materialization_path_diagnostics_v0 import (  # noqa: E402
    CONFIRM_GO,
    CURRENT_STATE,
    DEFAULT_ARCHIVE_ROOT,
    EVIDENCE_CLASS_ID,
    PROCESS_CLASSIFICATION,
    run_diagnostics_execution_v0,
)

DEFAULT_CONFIG = (
    _REPO_ROOT
    / "config/research/post_no_pass_inconclusive_metric_materialization_path_diagnostics_evidence_class_v0.json"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Execute post-no-pass inconclusive metric materialization path diagnostics v0 "
            "over manifest-verified PR4881/4883/4884 source evidence."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()

    command_log = [
        " ".join(
            [
                "uv",
                "run",
                "python",
                str(
                    _REPO_ROOT
                    / "scripts/ops/run_post_no_pass_inconclusive_metric_materialization_path_diagnostics_execution_v0.py"
                ),
                "--confirm-go-token",
                CONFIRM_GO,
            ]
        )
    ]

    try:
        result = run_diagnostics_execution_v0(
            confirm_go_token=args.confirm_go_token,
            config_path=args.config,
            archive_root=args.archive_root,
            command_log=command_log,
        )
    except SystemExit as exc:
        raise exc
    except ValueError as exc:
        _die(f"ERR:{exc}")

    payload = {
        "process_classification": PROCESS_CLASSIFICATION,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "current_state": CURRENT_STATE,
        "execution_id": result["execution_id"],
        "new_evidence_dir": result["new_evidence_dir"],
        "manifest_verify_rc": result["manifest_verify_rc"],
        "diagnostic_mapped_ratio": result["diagnostic_mapped_ratio"],
        "primary_cause": result["cause_taxonomy"]["PRIMARY_CAUSE"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
