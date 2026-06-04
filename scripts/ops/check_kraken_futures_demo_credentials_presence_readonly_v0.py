#!/usr/bin/env python3
"""Read-only Kraken Futures Demo credential key presence check (v0).

Checks presence (not validity) of KRAKEN_FUTURES_DEMO_API_KEY and
KRAKEN_FUTURES_DEMO_API_SECRET only. Never emits secret values, never calls
private API or network, and never authorizes futures execute.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.kraken_futures_demo_credential_presence_contract_v0 import (
    CONFIRM_TOKEN_PRESENCE_ONLY_MANUAL,
    FORBIDDEN_ALTERNATE_ENV_KEYS,
    REQUIRED_CREDENTIAL_ENV_KEYS,
    build_checker_boundary_v0,
)

SCHEMA_VERSION = "peak_trade.kraken_futures_demo_credentials_presence_readonly.v0"

Status = Literal["BLOCKED", "READY_FOR_OPERATOR_REVIEW"]

INVALID_INPUT_EXIT = 2
CONFIRM_TOKEN_REQUIRED_EXIT = 3

GetEnvValue = Callable[[str], str]


def _default_get_env_value(key: str) -> str:
    return os.environ.get(key, "")


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=value lines; values kept in-memory for presence only, never emitted."""
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


def _resolve_presence(
    key: str,
    *,
    get_env_value: GetEnvValue,
    file_values: dict[str, str],
) -> tuple[bool, str]:
    if str(get_env_value(key)).strip() != "":
        return True, "env"
    if key in file_values and str(file_values[key]).strip() != "":
        return True, "env_file"
    return False, "absent"


def _forbidden_alternates_present(
    *,
    get_env_value: GetEnvValue,
    file_values: dict[str, str],
) -> list[str]:
    found: list[str] = []
    for key in sorted(FORBIDDEN_ALTERNATE_ENV_KEYS):
        present, _ = _resolve_presence(key, get_env_value=get_env_value, file_values=file_values)
        if present:
            found.append(key)
    return found


def run_presence_check(
    *,
    env_file: Path | None = None,
    get_env_value: GetEnvValue | None = None,
) -> tuple[dict[str, Any], int]:
    """Return (payload, exit_code). exit_code 0 for normal run, 2 for bad input."""
    if env_file is not None and not env_file.is_file():
        print(
            "check_kraken_futures_demo_credentials_presence_readonly_v0: "
            f"--env-file not a file: {env_file}",
            file=sys.stderr,
        )
        return {}, INVALID_INPUT_EXIT

    lookup = get_env_value or _default_get_env_value
    file_values: dict[str, str] = {}
    if env_file is not None:
        file_values = _parse_env_file(env_file)

    prerequisites: list[dict[str, Any]] = []
    missing: list[str] = []

    for key in REQUIRED_CREDENTIAL_ENV_KEYS:
        present, source = _resolve_presence(key, get_env_value=lookup, file_values=file_values)
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

    alternates_present = _forbidden_alternates_present(
        get_env_value=lookup,
        file_values=file_values,
    )

    present_count = sum(1 for p in prerequisites if p["present"])
    status: Status = "BLOCKED"
    if not missing and not alternates_present:
        status = "READY_FOR_OPERATOR_REVIEW"

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "required_key_count": len(REQUIRED_CREDENTIAL_ENV_KEYS),
        "required_present_count": present_count,
        "missing_count": len(missing),
        "prerequisites": prerequisites,
        "missing": missing,
        "forbidden_alternate_keys_present": alternates_present,
        "checker_boundary_v0": build_checker_boundary_v0(),
    }
    return payload, 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Kraken Futures Demo credential presence-only check "
            "(no secret values in output, no network)."
        )
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        metavar="PATH",
        help="Optional env-style file (KEY=value); presence only, values never printed.",
    )
    parser.add_argument(
        "--confirm-token",
        default=None,
        help=f"Required operator GO token ({CONFIRM_TOKEN_PRESENCE_ONLY_MANUAL!r}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.confirm_token != CONFIRM_TOKEN_PRESENCE_ONLY_MANUAL:
        print(
            "check_kraken_futures_demo_credentials_presence_readonly_v0: "
            "missing or invalid --confirm-token (operator GO required)",
            file=sys.stderr,
        )
        return CONFIRM_TOKEN_REQUIRED_EXIT

    env_path = args.env_file.expanduser().resolve() if args.env_file is not None else None
    payload, code = run_presence_check(env_file=env_path)
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
        if payload["forbidden_alternate_keys_present"]:
            print(
                "forbidden_alternate_keys_present="
                + ",".join(payload["forbidden_alternate_keys_present"])
            )
        print(f"non_authorizing={str(cb['non_authorizing']).lower()}")
        print(f"futures_private_api_authorized={str(cb['futures_private_api_authorized']).lower()}")
        print(f"next_execute_allowed={str(cb['next_execute_allowed']).lower()}")
        print(
            "checker_does_not_read_credential_values="
            f"{str(cb['checker_does_not_read_credential_values']).lower()}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
