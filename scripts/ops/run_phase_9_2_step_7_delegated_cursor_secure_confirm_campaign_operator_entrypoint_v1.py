#!/usr/bin/env python3
"""Delegated Cursor secure-confirm operator entrypoint for Step-7 campaign.

COPY/PASTE (later separate OWNER_GO only; not authorized by this implementation PR):

  cd /path/to/Peak_Trade
  python3 scripts/ops/run_phase_9_2_step_7_delegated_cursor_secure_confirm_campaign_operator_entrypoint_v1.py \\
    --owner-go --operator-authorization-explicit --network-session-go \\
    --request-real-network --planned-session-count 2 \\
    --authorization-valid \\
    --expected-capability-id PHASE_9_2_STEP_7_REPEATED_MULTI_SESSION_CONTINUITY_CAMPAIGN_EXECUTION_V1

Governance:
  - AUTHORIZATION_CHANNEL=DELEGATED_CURSOR_SECURE_CONFIRM
  - TOKEN_ROLE=EPHEMERAL_EXECUTION_LATCH (not human TTY presence proof)
  - requires OWNER_GO + OPERATOR_AUTHORIZATION_EXPLICIT + NETWORK_SESSION_GO
  - requires HEAD == origin/main and tracked worktree clean
  - one-time latch minted locally; never argv/env/stdout/stderr/evidence plaintext
  - only SHA-256 digest may appear in evidence
  - REAL_TTY_VERIFIED may be false; DELEGATED_SECURE_CONFIRM_VERIFIED must be true
  - no Order / Live / Testnet / credential authorization
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.confirm_token_path_v1 import (  # noqa: E402
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (  # noqa: E402
    AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
    TARGET_CAMPAIGN_CAPABILITY_ID,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.delegated_cursor_secure_confirm_broker_v1 import (  # noqa: E402
    mint_delegated_cursor_secure_confirm_latch_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.governed_campaign_execution_v1 import (  # noqa: E402
    execute_governed_step7_campaign_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.wallclock_packaging_v1 import (  # noqa: E402
    prove_step7_wallclock_packaging_bound_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (  # noqa: E402
    load_activation_config_v1,
)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=_REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner-go", action="store_true")
    p.add_argument("--operator-authorization-explicit", action="store_true")
    p.add_argument("--network-session-go", action="store_true")
    p.add_argument("--request-real-network", action="store_true")
    p.add_argument("--authorization-valid", action="store_true")
    p.add_argument("--planned-session-count", type=int, default=2)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument(
        "--expected-capability-id",
        default=TARGET_CAMPAIGN_CAPABILITY_ID,
    )
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    argv_blockers = reject_confirm_token_argv_v1(raw)
    env_blockers = reject_confirm_token_env_fallback_v1(os.environ)
    parser = build_parser()
    args = parser.parse_args(raw)

    if argv_blockers or env_blockers:
        payload = {
            "ok": False,
            "blockers": sorted(set(argv_blockers + env_blockers)),
            "AUTHORIZATION_CHANNEL": AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
            "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
            "network_session_started": False,
            "confirm_token_minted": False,
            "confirm_token_consumed": False,
            "confirm_token_plaintext_exposed": False,
            "REAL_TTY_VERIFIED": False,
            "DELEGATED_SECURE_CONFIRM_VERIFIED": False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        return 2

    packaging = prove_step7_wallclock_packaging_bound_v1()
    if not packaging.get("ok"):
        payload = {
            "ok": False,
            "blockers": sorted(
                set(
                    list(packaging.get("blockers") or [])
                    + ["STEP7_WALLCLOCK_PACKAGING_BINDING_FAILED"]
                )
            ),
            "AUTHORIZATION_CHANNEL": AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
            "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
            "network_session_started": False,
            "confirm_token_minted": False,
            "confirm_token_consumed": False,
            "confirm_token_plaintext_exposed": False,
            "STEP7_WALLCLOCK_PACKAGING_BOUND": False,
            "REAL_TTY_VERIFIED": False,
            "DELEGATED_SECURE_CONFIRM_VERIFIED": False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        return 2

    sha = args.expected_repository_sha or _repo_sha()
    cfg = _cfg()
    latch = mint_delegated_cursor_secure_confirm_latch_v1()
    # Digest may be referenced for operator audit; plaintext never printed.
    token_digest = latch.digest
    try:
        result = execute_governed_step7_campaign_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            owner_go=bool(args.owner_go),
            operator_authorization_explicit=bool(args.operator_authorization_explicit),
            network_session_go=bool(args.network_session_go),
            authorization_valid=bool(args.authorization_valid),
            confirm_token_valid=True,
            planned_session_count=int(args.planned_session_count),
            allow_real_network_side_effects=bool(args.request_real_network),
            invoke_executor=True,
            stdin_isatty=False,
            getpass_fn=None,
            argv=raw,
            environ=os.environ,
            repo_root=_REPO_ROOT,
            expected_capability_id=str(args.expected_capability_id),
            campaign_start_state={},
            authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
            delegated_confirm_latch=latch,
        )
        payload = result.to_dict()
        payload["confirm_token_digest_sha256"] = token_digest
        payload["AUTHORIZATION_CHANNEL"] = AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM
        payload["TOKEN_ROLE"] = CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH
        payload["STEP7_WALLCLOCK_PACKAGING_BOUND"] = True
        # Hard disclosure guard: never emit latch repr secrets (digest-only already).
        blob = json.dumps(payload, sort_keys=True, indent=2 if args.json else None)
        print(blob)
        return 0 if result.ok else 2
    finally:
        try:
            latch.cleanup_temp_secret_v1()
        except Exception:
            pass
        try:
            latch.clear_v1()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
