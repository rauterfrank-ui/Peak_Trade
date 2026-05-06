#!/usr/bin/env python3
"""Report the current Paper/Shadow 24/7 preflight status.

This reporter is intentionally read-only and non-authorizing. It does not run
the scheduler, does not start daemons, and does not activate Paper, Shadow,
Testnet, or Live runtime paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


CONTRACT = "paper_shadow_247_preflight_status_v0"
CONTRACT_DOC = "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
SCHEDULER_DOC = "docs/SCHEDULER_DAEMON.md"
SCHEDULER_CONFIG = "config/scheduler/jobs.toml"
PAPER_SHADOW_247_PREFLIGHT_METADATA = Path("config") / "ops" / "paper_shadow_247_preflight.toml"
DRY_RUN_COMMAND = (
    "python3 scripts/run_scheduler.py --config config/scheduler/jobs.toml "
    "--dry-run --once --verbose"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_paper_shadow_247_preflight_metadata(root: Path) -> dict[str, Any]:
    cfg = root / PAPER_SHADOW_247_PREFLIGHT_METADATA
    if not cfg.is_file():
        return {}
    return tomllib.loads(cfg.read_text(encoding="utf-8"))


def build_paper_shadow_247_preflight_status(repo_root: Path | None = None) -> dict[str, Any]:
    root = (repo_root or _repo_root()).resolve()
    metadata = _load_paper_shadow_247_preflight_metadata(root)

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

    canonical_owner_any = metadata.get("canonical_owner")
    canonical_owner = canonical_owner_any if isinstance(canonical_owner_any, str) else None

    paper_jobs = [str(x) for x in metadata.get("paper_jobs", []) if isinstance(x, str)]
    shadow_jobs = [str(x) for x in metadata.get("shadow_jobs", []) if isinstance(x, str)]
    output_paths = [str(x) for x in metadata.get("output_paths", []) if isinstance(x, str)]

    stop_any = metadata.get("stop_command")
    emergency_any = metadata.get("emergency_stop_command")
    stop_command = stop_any if isinstance(stop_any, str) else None
    emergency_stop_command = emergency_any if isinstance(emergency_any, str) else None

    blockers: list[str] = []
    if not canonical_owner:
        blockers.append("canonical_owner_missing")
    if not paper_jobs or not shadow_jobs:
        blockers.append("paper_shadow_job_set_missing")
    if not output_paths:
        blockers.append("output_paths_missing")
    if not stop_command or not emergency_stop_command:
        blockers.append("stop_commands_missing")

    # Authorization flags: never inferred from metadata alone (documentation-only TOML keys).
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
        "broker_authorized": False,
        "exchange_authorized": False,
        "order_submission_authorized": False,
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
        "canonical_owner": canonical_owner,
        "paper_jobs": paper_jobs,
        "shadow_jobs": shadow_jobs,
        "commands": [],
        "output_paths": output_paths,
        "state_files": [],
        "log_paths": [],
        "stop_command": stop_command,
        "emergency_stop_command": emergency_stop_command,
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
