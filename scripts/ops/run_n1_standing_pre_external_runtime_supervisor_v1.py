#!/usr/bin/env python3
"""Canonical entry: N=1 standing PRE_EXTERNAL runtime supervisor (orchestration only)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _origin_main_sha() -> str:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "origin/main"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    return ""


def _head_sha() -> str:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    return ""


def _run_offline_inject_session(
    *, session_root: Path, origin_main_sha: str, max_cycles: int
) -> int:
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
        POST_ALLOWED,
        REAL_VENUE_POST_ALLOWED,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.constants_v1 import (
        TRANSPORT_SCOPE_OFFLINE_INJECT,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.errors_v1 import (
        StandingSupervisorError,
    )
    from tests.ops._n1_standing_supervisor_offline_inject_harness_v1 import (
        OWNER_GO_BASELINE_SHA,
        run_offline_inject_supervisor_session_v1,
    )

    try:
        result = run_offline_inject_supervisor_session_v1(
            repo_root=REPO_ROOT,
            session_root=session_root,
            origin_main_sha=origin_main_sha,
            max_cycles=max_cycles,
        )
    except StandingSupervisorError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "launcher_invoked_supervisor": True}))
        return 1

    summary = {
        "ok": result.ok,
        "launcher_invoked_supervisor": True,
        "run_id": result.run_id,
        "cycles_completed": result.trace.governed_cycle_count,
        "accepted_c1_count": result.trace.accepted_c1_count,
        "governed_cycle_count": result.trace.governed_cycle_count,
        "POST_COUNT": result.trace.post_count,
        "post_allowed": POST_ALLOWED,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "real_venue_post_allowed": REAL_VENUE_POST_ALLOWED,
        "owner_go_consumed": result.owner_go_consumed,
        "recovery_before_cycle": result.trace.recovery_completed,
        "transport_scope": TRANSPORT_SCOPE_OFFLINE_INJECT,
        "authority_invariants_ok": result.authority_invariants_ok,
        "origin_main_sha_used": origin_main_sha,
        "owner_go_baseline_sha": OWNER_GO_BASELINE_SHA,
        "tested_code_sha_hint": _head_sha(),
    }
    print(json.dumps(summary, indent=2))
    return 0 if result.ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start N=1 standing PRE_EXTERNAL runtime supervisor (one session)."
    )
    parser.add_argument("--public-store", type=Path)
    parser.add_argument("--private-store", type=Path)
    parser.add_argument("--lane-state", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--origin-main-sha", default="")
    parser.add_argument("--dry-run-config", action="store_true")
    parser.add_argument(
        "--offline-inject-session",
        action="store_true",
        help="Run one offline/inject supervisor session (CI/WP-01; no live credentials).",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=2,
        help="Max governed cycles for offline inject session (default 2).",
    )
    args = parser.parse_args()

    owner_go_baseline = "7a3597e61966749a9e30d06f3514e23a9179fb9e"
    origin_for_owner_go = args.origin_main_sha or owner_go_baseline

    if args.dry_run_config:
        print(
            json.dumps(
                {
                    "launcher": "run_n1_standing_pre_external_runtime_supervisor_v1.py",
                    "repo_root": str(REPO_ROOT),
                    "origin_main_sha": args.origin_main_sha or _origin_main_sha(),
                    "modes": {
                        "offline_inject_session": "--offline-inject-session with optional durable path roots",
                    },
                    "transport_scope_offline_inject": True,
                },
                indent=2,
            )
        )
        return 0

    if args.offline_inject_session:
        max_cycles = max(1, int(args.max_cycles))
        if args.public_store and args.private_store and args.lane_state and args.evidence_root:
            session_root = args.public_store.parent
            for root in (
                args.public_store,
                args.private_store,
                args.lane_state,
                args.evidence_root,
            ):
                root.mkdir(parents=True, exist_ok=True)
            return _run_offline_inject_session(
                session_root=session_root,
                origin_main_sha=origin_for_owner_go,
                max_cycles=max_cycles,
            )
        with tempfile.TemporaryDirectory(prefix="n1_standing_supervisor_") as tmp:
            return _run_offline_inject_session(
                session_root=Path(tmp),
                origin_main_sha=owner_go_baseline,
                max_cycles=max_cycles,
            )

    print(
        "ERROR:REQUIRES_OFFLINE_INJECT_OR_OPERATOR_HARNESS",
        file=sys.stderr,
    )
    print(
        "Use --offline-inject-session for WP-01 inject transport, or --dry-run-config.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
