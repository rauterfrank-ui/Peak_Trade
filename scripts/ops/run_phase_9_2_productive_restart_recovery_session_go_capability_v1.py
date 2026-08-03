#!/usr/bin/env python3
"""CLI for Phase 9.2 productive restart/recovery Session-GO capability.

Commands:
  preflight — schema/authority surface readiness (no session)
  validate  — validate a Session-GO artifact against bindings (no side effects)
  issue     — write an ephemeral ACTIVE Session-GO artifact via build_session_go_authority_v1
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (  # noqa: E402
    ACTIVATION_STATUS_ACTIVE,
    CAPABILITY_ID,
    CONFIG_RELATIVE_PATH,
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    TARGET_ENTRYPOINT_PATH,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (  # noqa: E402
    build_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.digest_v1 import (  # noqa: E402
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.gate_v1 import (  # noqa: E402
    evaluate_session_go_gate_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.parity_v1 import (  # noqa: E402
    prove_phase92_session_go_parity_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (  # noqa: E402
    load_activation_config_v1,
)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("preflight", "validate", "issue"))
    p.add_argument("--session-go-file", type=Path, default=None)
    p.add_argument("--output", type=Path, default=None, help="Destination for issue command")
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--owner-go", action="store_true")
    p.add_argument("--owner-session-go", action="store_true")
    p.add_argument("--authorization-present", action="store_true")
    p.add_argument("--confirm-token-present", action="store_true")
    p.add_argument(
        "--max-session-duration-seconds",
        type=int,
        default=DEFAULT_MAX_SESSION_DURATION_SECONDS,
    )
    p.add_argument("--expires-in-seconds", type=int, default=DEFAULT_MAX_SESSION_DURATION_SECONDS)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "preflight":
        parity = prove_phase92_session_go_parity_v1()
        cfg_path = _REPO_ROOT / CONFIG_RELATIVE_PATH
        payload = {
            "ok": bool(parity.get("ok") and cfg_path.is_file()),
            "capability_id": CAPABILITY_ID,
            "session_id": TARGET_SESSION_ID,
            "entrypoint_path": TARGET_ENTRYPOINT_PATH,
            "config_path": CONFIG_RELATIVE_PATH,
            "config_present": cfg_path.is_file(),
            "parity": parity,
            "session_started": False,
            "authorization_consumed": False,
            "network_request_count": 0,
            "notes": [
                "SESSION_GO_AUTHORITY_SURFACE_READY",
                "NO_SESSION_STARTED",
                "NO_AUTHORIZATION_ISSUED",
                "DEFAULT_ACTIVATION_INACTIVE_IN_CAPABILITY_CONFIG",
            ],
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if payload["ok"] else 1

    sha = args.expected_repository_sha or _repo_sha()
    cfg = str(
        load_activation_config_v1(
            config_path=_REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )

    if args.command == "issue":
        if args.output is None:
            print(
                json.dumps(
                    {"ok": False, "blockers": ["SESSION_GO_OUTPUT_REQUIRED"]},
                    sort_keys=True,
                    indent=2,
                )
            )
            return 2
        now = float(time.time())
        max_duration = int(args.max_session_duration_seconds)
        expires_in = int(args.expires_in_seconds)
        if max_duration <= 0 or max_duration > DEFAULT_MAX_SESSION_DURATION_SECONDS:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blockers": [f"SESSION_GO_MAX_DURATION_INVALID:{max_duration}"],
                    },
                    sort_keys=True,
                    indent=2,
                )
            )
            return 2
        if expires_in <= 0 or expires_in > DEFAULT_MAX_SESSION_DURATION_SECONDS:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blockers": [f"SESSION_GO_EXPIRES_IN_INVALID:{expires_in}"],
                    },
                    sort_keys=True,
                    indent=2,
                )
            )
            return 2
        authority = build_session_go_authority_v1(
            session_go_id=f"sgo_ephemeral_{uuid.uuid4().hex[:16]}",
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            issued_at=now,
            not_before=now,
            expires_at=now + float(expires_in),
            activation_status=ACTIVATION_STATUS_ACTIVE,
            max_session_duration_seconds=max_duration,
            network_session_execution_authorized_by_this_go=True,
            fixture_non_authoritative=False,
            notes=(
                "EPHEMERAL_ACTIVE_SESSION_GO",
                "ISSUED_VIA_CANONICAL_BUILDER",
                "NOT_A_REPOSITORY_STATIC_ENABLE",
            ),
        )
        out = Path(args.output)
        write_json_atomic_v1(out, authority.to_dict())
        # Re-read/validate immediately (no secrets in artifact).
        gate = evaluate_session_go_gate_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=now,
            owner_go=True,
            owner_session_go=True,
            session_go_path=out,
            authorization_present=True,
            confirm_token_present=True,
        )
        payload = {
            "ok": bool(gate.session_go_authority_satisfied),
            "session_go_path": str(out),
            "session_go_id": authority.session_go_id,
            "session_go_digest": authority.session_go_digest,
            "activation_status": authority.activation_status,
            "expires_at": authority.expires_at,
            "session_started": False,
            "authorization_consumed": False,
            "network_request_count": 0,
            "notes": [
                "SESSION_GO_ISSUED_EPHEMERAL",
                "SESSION_GO_REVALIDATED_AFTER_WRITE",
                "NO_TOKEN_PLAINTEXT",
                "NO_SESSION_STARTED",
            ],
            "blockers": list(gate.blockers) if not gate.session_go_authority_satisfied else [],
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if payload["ok"] else 2

    if args.session_go_file is None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "blockers": ["SESSION_GO_MISSING"],
                    "session_started": False,
                    "authorization_consumed": False,
                    "network_request_count": 0,
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 2

    result = evaluate_session_go_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=float(time.time()),
        owner_go=bool(args.owner_go),
        owner_session_go=bool(args.owner_session_go),
        session_go_path=args.session_go_file,
        authorization_present=bool(args.authorization_present),
        confirm_token_present=bool(args.confirm_token_present),
    )
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
