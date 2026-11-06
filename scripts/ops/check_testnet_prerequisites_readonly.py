#!/usr/bin/env python3
"""Read-only Testnet prerequisite inventory (stdlib only).

Checks presence (not validity) of a small explicit env/config key set. Never
reads secret contents into output, never connects to brokers/exchanges, and
never authorizes Testnet or Live execution.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Literal

SCHEMA_VERSION = "peak_trade.testnet_prerequisites_readonly.v0"

# Explicit conservative gates: presence-only, no value semantics in this slice.
REQUIRED_KEYS: tuple[str, ...] = (
    "PEAK_TRADE_TESTNET_OPERATOR_GATE_ACK",
    "PEAK_TRADE_TESTNET_CONFIG_DECLARED",
)

Status = Literal["BLOCKED", "READY_FOR_OPERATOR_REVIEW"]

INVALID_INPUT_EXIT = 2


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=value lines; values are kept in-memory for presence checks only."""
    parsed: dict[str, str] = {}
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _sep, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            parsed[key] = val
    return parsed


def _resolve_presence(key: str, file_values: dict[str, str]) -> tuple[bool, str]:
    env_val = os.environ.get(key, "")
    if str(env_val).strip() != "":
        return True, "env"
    if key in file_values and str(file_values[key]).strip() != "":
        return True, "env_file"
    return False, "absent"


def build_checker_boundary_v0() -> dict[str, Any]:
    return {
        "non_authorizing": True,
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_exchange_order_paths_authorized": False,
        "order_submission_authorized": False,
        "checker_does_not_connect_to_exchange": True,
        "checker_does_not_validate_credentials": True,
    }


def run_check(
    *,
    env_file: Path | None,
) -> tuple[dict[str, Any], int]:
    """Return (payload, exit_code). exit_code 0 for normal run, 2 for bad input."""
    if env_file is not None:
        if not env_file.is_file():
            print(
                f"check_testnet_prerequisites_readonly: --env-file not a file: {env_file}",
                file=sys.stderr,
            )
            return {}, INVALID_INPUT_EXIT

    file_values: dict[str, str] = {}
    if env_file is not None:
        file_values = _parse_env_file(env_file)

    prerequisites: list[dict[str, Any]] = []
    missing: list[str] = []

    for key in REQUIRED_KEYS:
        present, source = _resolve_presence(key, file_values)
        prerequisites.append(
            {
                "name": key,
                "present": present,
                "value_redacted": True,
                "source": source,
            }
        )
        if not present:
            missing.append(key)

    present_count = sum(1 for p in prerequisites if p["present"])
    status: Status = "READY_FOR_OPERATOR_REVIEW" if not missing else "BLOCKED"

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "required_key_count": len(REQUIRED_KEYS),
        "required_present_count": present_count,
        "missing_count": len(missing),
        "prerequisites": prerequisites,
        "missing": missing,
        "checker_boundary_v0": build_checker_boundary_v0(),
    }
    return payload, 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Read-only Testnet prerequisite key presence check (no secrets, no network)."
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON to stdout.",
    )
    p.add_argument(
        "--env-file",
        type=Path,
        default=None,
        metavar="PATH",
        help="Optional env-style file (KEY=value); only key presence is inspected.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    env_path = args.env_file.expanduser().resolve() if args.env_file is not None else None

    payload, code = run_check(env_file=env_path)
    if code != 0:
        return code

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        cb = payload["checker_boundary_v0"]
        print(f"status={payload['status']}")
        print(f"required_present_count={payload['required_present_count']}")
        print(f"missing_count={payload['missing_count']}")
        for pr in payload["prerequisites"]:
            print(
                f"prerequisite name={pr['name']} present={str(pr['present']).lower()} "
                f"value_redacted={str(pr['value_redacted']).lower()} source={pr['source']}"
            )
        print(f"non_authorizing={str(cb['non_authorizing']).lower()}")
        print(f"testnet_authorized={str(cb['testnet_authorized']).lower()}")
        print(f"live_authorized={str(cb['live_authorized']).lower()}")
        print(
            "broker_exchange_order_paths_authorized="
            f"{str(cb['broker_exchange_order_paths_authorized']).lower()}"
        )
        print(f"order_submission_authorized={str(cb['order_submission_authorized']).lower()}")
        print(
            "checker_does_not_connect_to_exchange="
            f"{str(cb['checker_does_not_connect_to_exchange']).lower()}"
        )
        print(
            "checker_does_not_validate_credentials="
            f"{str(cb['checker_does_not_validate_credentials']).lower()}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
