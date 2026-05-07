#!/usr/bin/env python3
"""Run a subprocess with a hard wall-clock timeout using only the stdlib.

Useful on macOS and elsewhere when GNU ``timeout`` is not installed.
On timeout, exits with code **124** (GNU ``timeout`` convention).
"""

from __future__ import annotations

import argparse
import subprocess
import sys

TIMEOUT_EXIT = 124
USAGE_EXIT = 2


def main(argv: list[str] | None = None) -> int:
    args_list = sys.argv if argv is None else argv
    rest = list(args_list[1:])
    if "--" not in rest:
        print(
            "run_with_timeout: missing `--` separator before command "
            "(example: ... --timeout-seconds 600 -- python -c 'print(1)')",
            file=sys.stderr,
        )
        return USAGE_EXIT

    sep = rest.index("--")
    head, cmd = rest[:sep], rest[sep + 1 :]

    parser = argparse.ArgumentParser(
        prog=args_list[0] if args_list else "run_with_timeout.py",
        description="Run COMMAND with subprocess timeout (no shell).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        required=True,
        help="Maximum wall-clock seconds for the child process (must be > 0).",
    )
    try:
        opts = parser.parse_args(head)
    except SystemExit:
        return USAGE_EXIT

    if opts.timeout_seconds <= 0:
        print("run_with_timeout: --timeout-seconds must be > 0", file=sys.stderr)
        return USAGE_EXIT

    if not cmd:
        print("run_with_timeout: no command after --", file=sys.stderr)
        return USAGE_EXIT

    try:
        proc = subprocess.run(
            cmd,
            timeout=opts.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(
            f"run_with_timeout: exceeded --timeout-seconds={opts.timeout_seconds!r}; "
            f"terminated: {cmd!r}",
            file=sys.stderr,
        )
        return TIMEOUT_EXIT
    except OSError as e:
        print(f"run_with_timeout: failed to start process: {e}", file=sys.stderr)
        return USAGE_EXIT

    rc = proc.returncode
    return USAGE_EXIT if rc is None else int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
