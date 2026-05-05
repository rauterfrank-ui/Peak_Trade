#!/usr/bin/env python3
"""Report the current Paper/Shadow 24/7 preflight status.

This reporter is intentionally read-only and non-authorizing. It does not run
the scheduler, does not start daemons, and does not activate Paper, Shadow,
Testnet, or Live runtime paths.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CONTRACT = "paper_shadow_247_preflight_status_v0"
CONTRACT_DOC = "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
SCHEDULER_DOC = "docs/SCHEDULER_DAEMON.md"
SCHEDULER_CONFIG = "config/scheduler/jobs.toml"
DRY_RUN_COMMAND = (
    "python3 scripts/run_scheduler.py --config config/scheduler/jobs.toml "
    "--dry-run --once --verbose"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_paper_shadow_247_preflight_status(repo_root: Path | None = None) -> dict[str, Any]:
    root = (repo_root or _repo_root()).resolve()
    contract_path = root / CONTRACT_DOC
    scheduler_doc_path = root / SCHEDULER_DOC
    scheduler_config_path = root / SCHEDULER_CONFIG

    contract_text = contract_path.read_text(encoding="utf-8") if contract_path.exists() else ""
    scheduler_doc_text = (
        scheduler_doc_path.read_text(encoding="utf-8") if scheduler_doc_path.exists() else ""
    )
    scheduler_config_text = (
        scheduler_config_path.read_text(encoding="utf-8") if scheduler_config_path.exists() else ""
    )

    required_files = {
        CONTRACT_DOC: contract_path.exists(),
        SCHEDULER_DOC: scheduler_doc_path.exists(),
        SCHEDULER_CONFIG: scheduler_config_path.exists(),
    }

    blockers = [
        "canonical_owner_missing",
        "paper_shadow_job_set_missing",
        "output_paths_missing",
        "stop_commands_missing",
    ]

    return {
        "contract": CONTRACT,
        "schema_version": 0,
        "status": "BLOCKED",
        "activation_authorized": False,
        "daemon_activation_authorized": False,
        "paper_runtime_authorized": False,
        "shadow_runtime_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
        "scheduler_execution_authorized": False,
        "dry_run_command": DRY_RUN_COMMAND,
        "dry_run_only": True,
        "required_files": required_files,
        "contract_markers": {
            "contract_doc_exists": required_files[CONTRACT_DOC],
            "contract_states_blocked": "Current status: **BLOCKED**." in contract_text,
            "contract_mentions_stop": "STOP" in contract_text
            and "do not activate Paper/Shadow 24/7" in contract_text,
            "contract_non_authority": "not trading authority" in contract_text
            or "Non-authority" in contract_text,
            "scheduler_doc_links_contract": "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
            in scheduler_doc_text,
            "scheduler_config_has_direct_247_job": any(
                token in scheduler_config_text.lower()
                for token in ("paper_shadow_247", "paper-shadow-247", "24/7")
            ),
        },
        "canonical_owner": None,
        "paper_jobs": [],
        "shadow_jobs": [],
        "commands": [],
        "output_paths": [],
        "state_files": [],
        "log_paths": [],
        "stop_command": None,
        "emergency_stop_command": None,
        "risk_flags": {
            "live": False,
            "testnet": False,
            "broker": False,
            "exchange": False,
            "orders": False,
            "network": False,
        },
        "status_reasons": blockers,
        "blockers": blockers,
        "notes": [
            "read_only_reporter",
            "does_not_run_scheduler",
            "does_not_start_daemon",
            "does_not_activate_paper_or_shadow_runtime",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root to inspect. Defaults to the current Peak_Trade checkout.",
    )
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve() if args.repo_root else None
    payload = build_paper_shadow_247_preflight_status(root)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status={payload['status']}")
        print(f"activation_authorized={str(payload['activation_authorized']).lower()}")
        print("dry_run_only=true")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
