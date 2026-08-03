"""CLI helpers for scripts/ops/peak_trade_runtime.py."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    CAPABILITY_ID,
    MODE_DASHBOARD_ONLY,
    SUPERVISION_BACKEND,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    CanonicalLauncherError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1 import (
    CanonicalLocalLauncherV1,
    LauncherPathsV1,
)
from src.ops.canonical_runtime_operations_activation_v1.constants_v1 import (
    CAPABILITY_ID as O8_CAPABILITY_ID,
)


def _repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="peak_trade_runtime",
        description=(
            f"{CAPABILITY_ID}/{O8_CAPABILITY_ID} — canonical local launcher "
            f"(backend={SUPERVISION_BACKEND})"
        ),
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=None,
        help="Real local repository root (default: auto-detect).",
    )
    parser.add_argument(
        "--state-root",
        type=Path,
        default=None,
        help="Durable launcher state root.",
    )
    parser.add_argument(
        "--log-root",
        type=Path,
        default=None,
        help="Log root for supervised sessions.",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=None,
        help="Optional evidence root binding.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pre = sub.add_parser("preflight", help="Run O1-consuming launcher preflight.")
    p_pre.add_argument("--session-id", default="preflight")
    p_pre.add_argument("--mode", default=MODE_DASHBOARD_ONLY)
    p_pre.add_argument("--config-path", type=Path, required=True)
    p_pre.add_argument("--repository-sha", default=None)
    p_pre.add_argument("--config-digest", default=None)

    p_start = sub.add_parser("start", help="Start dashboard-only supervised session.")
    p_start.add_argument("--session-id", default=None)
    p_start.add_argument("--mode", default=MODE_DASHBOARD_ONLY)
    p_start.add_argument("--config-path", type=Path, required=True)
    p_start.add_argument("--repository-sha", default=None)
    p_start.add_argument("--config-digest", default=None)

    for name, help_text in (
        ("status", "Report session lifecycle and process identity."),
        ("health", "Report health from identity + heartbeat."),
        ("stop", "Graceful stop with escalation."),
        ("restart", "Stop then start with identity binding."),
        ("recover", "Minimal stale PID / registry recovery."),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--session-id", required=True)

    p_logs = sub.add_parser(
        "logs",
        help="Read-only session log inspection (no process start, no token reads).",
    )
    p_logs.add_argument("--session-id", required=True)
    p_logs.add_argument(
        "--name",
        default=None,
        help="Optional basename under the session log dir (no path separators).",
    )
    p_logs.add_argument(
        "--tail",
        type=int,
        default=200,
        help="Max trailing lines per file (default 200, max 5000).",
    )

    p_verify = sub.add_parser(
        "verify",
        help="Read-only activation/session binding verification (no mutation/network).",
    )
    p_verify.add_argument("--session-id", default=None)
    p_verify.add_argument("--expected-repository-sha", default=None)
    p_verify.add_argument(
        "--require-clean-tracked-worktree",
        action="store_true",
        default=False,
    )
    p_verify.add_argument(
        "--require-health-artifact",
        action="store_true",
        default=False,
    )
    p_verify.add_argument(
        "--activation-contract-path",
        type=Path,
        default=None,
        help="Optional override path for the O8 activation contract.",
    )

    return parser


def _paths_from_args(args: argparse.Namespace) -> LauncherPathsV1:
    repo = Path(args.repository_root) if args.repository_root else _repo_root_from_here()
    state = (
        Path(args.state_root)
        if args.state_root
        else repo / ".runtime" / "canonical_local_launcher_v1"
    )
    logs = Path(args.log_root) if args.log_root else state / "logs"
    evidence = Path(args.evidence_root) if args.evidence_root else state / "evidence"
    return LauncherPathsV1(
        repository_root=repo.resolve(),
        state_root=state.resolve(),
        log_root=logs.resolve(),
        evidence_root=evidence.resolve(),
    )


def dispatch(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    paths = _paths_from_args(args)
    launcher = CanonicalLocalLauncherV1(paths)
    try:
        result: dict[str, Any]
        if args.command == "preflight":
            result = launcher.preflight(
                mode=str(args.mode),
                session_id=str(args.session_id or "preflight"),
                config_path=Path(args.config_path),
                repository_sha=args.repository_sha,
                config_digest=args.config_digest,
            )
        elif args.command == "start":
            result = launcher.start(
                mode=str(args.mode),
                session_id=args.session_id,
                config_path=Path(args.config_path),
                repository_sha=args.repository_sha,
                config_digest=args.config_digest,
            )
        elif args.command == "status":
            result = launcher.status(str(args.session_id))
        elif args.command == "health":
            result = launcher.health(str(args.session_id))
        elif args.command == "logs":
            result = launcher.logs(
                str(args.session_id),
                log_name=args.name,
                tail_lines=int(args.tail),
            )
        elif args.command == "stop":
            result = launcher.stop(str(args.session_id))
        elif args.command == "restart":
            result = launcher.restart(str(args.session_id))
        elif args.command == "recover":
            result = launcher.recover(str(args.session_id))
        elif args.command == "verify":
            result = launcher.verify(
                session_id=args.session_id,
                expected_repository_sha=args.expected_repository_sha,
                require_clean_tracked_worktree=bool(args.require_clean_tracked_worktree),
                require_health_artifact=bool(args.require_health_artifact),
                activation_contract_path=args.activation_contract_path,
            )
            print(json.dumps(result, sort_keys=True, indent=2))
            return 0 if result.get("ok") is True else 1
        else:
            parser.error(f"unknown command: {args.command}")
            return 2
    except CanonicalLauncherError as exc:
        payload = {
            "ok": False,
            "error_code": exc.code,
            "detail": exc.detail,
            "payload": exc.payload,
            "capability_id": CAPABILITY_ID,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    return dispatch(argv)


if __name__ == "__main__":
    sys.exit(main())
