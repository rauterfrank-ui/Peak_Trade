"""O2 dashboard-only supervised worker: heartbeat + loopback FastAPI HTTP host."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _pick_free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run_dashboard_http_worker(
    *,
    session_id: str,
    heartbeat_path: Path,
    marker_path: Path,
    state_root: Path,
    http_host: str = "127.0.0.1",
    http_port: int = 0,
    ignore_sigterm: bool = False,
) -> int:
    """Long-running supervised dashboard: heartbeat + loopback FastAPI host."""
    from src.ops.canonical_local_launcher_and_process_supervision_v1.dashboard_http_host_v1 import (
        LOOPBACK_HOSTS,
        create_o2_dashboard_http_app_v1,
        run_uvicorn_loopback_v1,
    )

    if http_host not in LOOPBACK_HOSTS:
        raise SystemExit(f"LOOPBACK_BIND_REQUIRED:{http_host}")

    stopping = {"value": False}
    port = int(http_port) if int(http_port) > 0 else _pick_free_loopback_port()

    def _handle_term(signum: int, _frame: object) -> None:  # noqa: ARG001
        if ignore_sigterm:
            return
        stopping["value"] = True

    signal.signal(signal.SIGTERM, _handle_term)
    signal.signal(signal.SIGINT, _handle_term)

    app = create_o2_dashboard_http_app_v1(state_root=Path(state_root), session_id=session_id)
    server = run_uvicorn_loopback_v1(app=app, host=http_host, port=port)

    def _serve() -> None:
        server.run()

    thread = threading.Thread(target=_serve, name="o2-dashboard-http", daemon=True)
    thread.start()

    # Wait until port accepts connections.
    deadline = time.time() + 5.0
    while time.time() < deadline:
        try:
            with socket.create_connection((http_host, port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)

    _write_json(
        marker_path,
        {
            "schema": "o2_dashboard_only_http_worker_v1",
            "session_id": session_id,
            "pid": os.getpid(),
            "pgid": os.getpgrp(),
            "http_host": http_host,
            "http_port": port,
            "loopback_only": True,
            "state_root": str(Path(state_root)),
            "network_session_started": False,
            "authorization_consumed": False,
            "confirm_token_minted": False,
            "orders_submitted": False,
            "credentials_used": False,
            "trading_authority": False,
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
                "http_host": http_host,
                "http_port": port,
            },
        )
        time.sleep(0.2)

    server.should_exit = True
    thread.join(timeout=3.0)
    _write_json(
        heartbeat_path,
        {
            "session_id": session_id,
            "pid": os.getpid(),
            "pgid": os.getpgrp(),
            "ts_unix": time.time(),
            "healthy": False,
            "lifecycle_hint": "STOPPING",
            "http_host": http_host,
            "http_port": port,
        },
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="O2 dashboard-only supervised HTTP worker (loopback FastAPI)."
    )
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--heartbeat-path", required=True)
    parser.add_argument("--marker-path", required=True)
    parser.add_argument(
        "--state-root",
        default=os.environ.get("PEAK_TRADE_STATE_ROOT", ""),
        help="Durable O5 read-model root (defaults to PEAK_TRADE_STATE_ROOT).",
    )
    parser.add_argument(
        "--http-host", default=os.environ.get("PEAK_TRADE_DASHBOARD_HTTP_HOST", "127.0.0.1")
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=int(os.environ.get("PEAK_TRADE_DASHBOARD_HTTP_PORT", "0") or "0"),
    )
    parser.add_argument(
        "--ignore-sigterm",
        action="store_true",
        help="Test-only: ignore SIGTERM to force escalation to SIGKILL.",
    )
    # Backward-compatible alias: scaffold mode without HTTP is no longer the default.
    parser.add_argument(
        "--heartbeat-only",
        action="store_true",
        help="Legacy non-HTTP scaffold (tests for SIGTERM escalation only).",
    )
    args = parser.parse_args(argv)

    if args.heartbeat_only:
        from src.ops.canonical_local_launcher_and_process_supervision_v1.dashboard_scaffold_worker_v1 import (
            run_scaffold_worker,
        )

        return run_scaffold_worker(
            session_id=str(args.session_id),
            heartbeat_path=Path(args.heartbeat_path),
            marker_path=Path(args.marker_path),
            ignore_sigterm=bool(args.ignore_sigterm),
        )

    state_root = str(args.state_root or "").strip()
    if not state_root:
        raise SystemExit("STATE_ROOT_REQUIRED")
    return run_dashboard_http_worker(
        session_id=str(args.session_id),
        heartbeat_path=Path(args.heartbeat_path),
        marker_path=Path(args.marker_path),
        state_root=Path(state_root),
        http_host=str(args.http_host),
        http_port=int(args.http_port),
        ignore_sigterm=bool(args.ignore_sigterm),
    )


if __name__ == "__main__":
    sys.exit(main())
