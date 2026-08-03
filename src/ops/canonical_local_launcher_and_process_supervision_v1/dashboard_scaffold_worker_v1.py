"""Non-executing dashboard-only scaffold worker (no network / auth / orders)."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def run_scaffold_worker(
    *,
    session_id: str,
    heartbeat_path: Path,
    marker_path: Path,
    ignore_sigterm: bool = False,
) -> int:
    """Long-running scaffold: heartbeat only. No sockets, credentials, or orders."""
    stopping = {"value": False}

    def _handle_term(signum: int, _frame: object) -> None:  # noqa: ARG001
        if ignore_sigterm:
            return
        stopping["value"] = True

    signal.signal(signal.SIGTERM, _handle_term)
    signal.signal(signal.SIGINT, _handle_term)

    _write_json(
        marker_path,
        {
            "schema": "o2_dashboard_only_scaffold_worker_v1",
            "session_id": session_id,
            "pid": os.getpid(),
            "pgid": os.getpgrp(),
            "network_session_started": False,
            "authorization_consumed": False,
            "confirm_token_minted": False,
            "orders_submitted": False,
            "credentials_used": False,
            "started_at_unix": time.time(),
        },
    )

    while not stopping["value"]:
        _write_json(
            heartbeat_path,
            {
                "session_id": session_id,
                "pid": os.getpid(),
                "pgid": os.getpgrp(),
                "ts_unix": time.time(),
                "healthy": True,
                "lifecycle_hint": "RUNNING",
            },
        )
        time.sleep(0.2)

    _write_json(
        heartbeat_path,
        {
            "session_id": session_id,
            "pid": os.getpid(),
            "pgid": os.getpgrp(),
            "ts_unix": time.time(),
            "healthy": False,
            "lifecycle_hint": "STOPPING",
        },
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="O2 dashboard-only scaffold worker (non-executing)."
    )
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--heartbeat-path", required=True)
    parser.add_argument("--marker-path", required=True)
    parser.add_argument(
        "--ignore-sigterm",
        action="store_true",
        help="Test-only: ignore SIGTERM to force escalation to SIGKILL.",
    )
    args = parser.parse_args(argv)
    return run_scaffold_worker(
        session_id=str(args.session_id),
        heartbeat_path=Path(args.heartbeat_path),
        marker_path=Path(args.marker_path),
        ignore_sigterm=bool(args.ignore_sigterm),
    )


if __name__ == "__main__":
    sys.exit(main())
