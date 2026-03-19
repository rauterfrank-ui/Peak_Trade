#!/usr/bin/env python3
"""Run bounded pilot with local secrets from a dedicated env file.

Reference: LOCAL_BOUNDED_SECRET_ENV_FILE_CONTRACT, LOCAL_BOUNDED_SECRET_LAUNCH_PATH_PROPOSAL
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_ENV_FILE = Path(".bounded_pilot.env")
REQUIRED_VARS = ("KRAKEN_API_KEY", "KRAKEN_API_SECRET")
ALLOWED_MODES = {"bounded_pilot", "acceptance"}


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"invalid env line: {raw_line!r}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _load_local_env(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"local bounded secret env file missing: {path}")
    data = _parse_env_file(path)
    missing = [k for k in REQUIRED_VARS if not data.get(k)]
    if missing:
        raise RuntimeError(
            "missing required vars in local bounded secret env file: " + ", ".join(missing)
        )
    return data


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run bounded pilot with local secrets from a dedicated env file"
    )
    p.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    p.add_argument("--steps", type=int, default=25)
    p.add_argument("--position-fraction", type=float, default=0.0005)
    p.add_argument("--mode", default="bounded_pilot")
    p.add_argument("--dry-check", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mode not in ALLOWED_MODES:
        print(
            f"FAIL_CLOSED: unsupported mode for local bounded secret launcher: {args.mode}",
            file=sys.stderr,
        )
        return 2

    env_path = Path(args.env_file).expanduser()
    try:
        loaded = _load_local_env(env_path)
    except Exception as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2

    child_env = os.environ.copy()
    child_env.update({k: loaded[k] for k in REQUIRED_VARS})
    child_env["PT_EXEC_EVENTS_ENABLED"] = (
        loaded.get("PT_EXEC_EVENTS_ENABLED") or child_env.get("PT_EXEC_EVENTS_ENABLED") or "true"
    )

    cmd = [
        sys.executable,
        "scripts/ops/run_bounded_pilot_session.py",
        "--steps",
        str(args.steps),
        "--position-fraction",
        str(args.position_fraction),
    ]

    print(f"LOCAL_BOUNDED_SECRET_SOURCE={env_path}")
    print(f"LOCAL_BOUNDED_SECRET_MODE={args.mode}")
    print("LOCAL_BOUNDED_SECRET_REQUIRED_VARS=KRAKEN_API_KEY,KRAKEN_API_SECRET")
    print(f"LOCAL_BOUNDED_SECRET_PT_EXEC_EVENTS_ENABLED={child_env['PT_EXEC_EVENTS_ENABLED']}")

    if args.dry_check:
        return 0

    return subprocess.run(cmd, env=child_env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
