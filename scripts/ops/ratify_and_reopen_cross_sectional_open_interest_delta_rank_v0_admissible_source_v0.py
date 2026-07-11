#!/usr/bin/env python3
"""Offline admissible source ratification and scope parking reopen v0.

Formal classification of corrected self-accumulated OKX forward OI source and bounded
scope reopen when reopen_requires contract is satisfied. Default-off; no runtime authority.
Operator GO: GO_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_ADMISSIBLE_SOURCE_RATIFICATION_AND_SCOPE_PARKING_REOPEN_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_open_interest_delta_rank_v0_admissible_source_ratification_and_scope_parking_reopen_v0 import (  # noqa: E402
    CONFIRM_GO,
    CONFIG_REL_PATH,
    DATASET_REGISTRY_REL_PATH,
    PARKING_CONFIG_REL_PATH,
    RatificationVerdict,
    execute_source_ratification_and_scope_reopen_v0,
    ratification_result_to_dict_v0,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Offline admissible source ratification and scope parking reopen for "
            "cross_sectional_open_interest_delta_rank/v0."
        )
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        help=f"Required operator GO token ({CONFIRM_GO})",
    )
    parser.add_argument(
        "--as-of-utc",
        required=True,
        help="Deterministic as-of UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)",
    )
    parser.add_argument(
        "--enabled",
        action="store_true",
        help="Explicit enable flag; default-off without this flag",
    )
    parser.add_argument(
        "--write-configs",
        action="store_true",
        help="Write ratified registration and registry configs to repo paths",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional JSON result output path",
    )
    args = parser.parse_args(argv)

    if not args.enabled:
        _die("ERR: DEFAULT_OFF_ENABLED_FLAG_REQUIRED")
    if args.confirm_go_token != CONFIRM_GO:
        _die(f"ERR: OPERATOR_GO_MISMATCH expected={CONFIRM_GO}")

    result = execute_source_ratification_and_scope_reopen_v0(
        confirm_go=args.confirm_go_token,
        as_of_utc=args.as_of_utc,
        enabled=True,
    )
    report = ratification_result_to_dict_v0(result)
    serialized = json.dumps(report, sort_keys=True, indent=2)
    print(serialized)

    if args.write_configs and result.verdict is RatificationVerdict.PASS:
        registry_path = _REPO_ROOT / DATASET_REGISTRY_REL_PATH
        ratification_config_path = _REPO_ROOT / CONFIG_REL_PATH
        parking_config_path = _REPO_ROOT / PARKING_CONFIG_REL_PATH
        registry_path.write_text(
            json.dumps(result.dataset_registry, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        ratification_config = json.loads(ratification_config_path.read_text(encoding="utf-8"))
        ratification_config["source_ratification_status"] = result.source_ratification_status.value
        ratification_config["scope_status_before"] = result.scope_status_before
        ratification_config["scope_status_after"] = result.scope_status_after
        ratification_config["observation_count_bound"] = result.assessment.observation_count
        ratification_config["ratification_evidence_dir"] = str(
            args.output_file.parent if args.output_file is not None else ""
        )
        ratification_config_path.write_text(
            json.dumps(ratification_config, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        parking_config = json.loads(parking_config_path.read_text(encoding="utf-8"))
        parking_config["source_ratification_ref"] = result.registration_config.get("ratification_owner")
        parking_config["scope_reopen_status"] = result.scope_status_after
        parking_config["prior_scope_status"] = result.scope_status_before
        parking_config_path.write_text(
            json.dumps(parking_config, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.output_file is not None:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(serialized + "\n", encoding="utf-8")

    return 0 if result.verdict is RatificationVerdict.PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
