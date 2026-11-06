#!/usr/bin/env python3
"""CLI for Phase 9.2 productive public-MD restart/recovery network entrypoint.

Commands:
  preflight              — offline readiness / segment plan / boundary proof
  offline-integration    — fake public-MD transport + PR#5665 harness/verifier
  materialize-evidence   — write capability evidence fixtures
  productive-session     — Session-GO gate evaluation only (no runner side effects)
  execute-post-unlock    — explicit execute mode: after unlock, invoke canonical runner

Confirm tokens are never accepted as argv plaintext. Use --confirm-token-file,
env PEAK_TRADE_PSO_CONFIRM_TOKEN, or stdin only when a bound ACTIVE Session-GO
plus Owner flags authorize later execution. Real network remains forbidden here.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (  # noqa: E402
    EeaPublicMdTransportV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (  # noqa: E402
    redact_mapping_for_logs,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    CONTROLLED_RESTART_EXIT_CODE,
    DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
    DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
    EXIT_CODE_82_CLASSIFICATION,
    RESTART_CAMPAIGN_ID,
    SEGMENT_PLAN,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.evidence_v1 import (  # noqa: E402
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.fake_public_md_v1 import (  # noqa: E402
    build_fake_ticker_fetcher_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.network_boundary_v1 import (  # noqa: E402
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.orchestrator_v1 import (  # noqa: E402
    reject_productive_session_start_v1,
    run_offline_productive_restart_orchestration_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.parity_v1 import (  # noqa: E402
    prove_phase92_productive_entrypoint_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (  # noqa: E402
    build_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.invocation_v1 import (  # noqa: E402
    invoke_post_unlock_canonical_runtime_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (  # noqa: E402
    load_activation_config_v1,
)


class _Clock:
    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self._t = float(start)

    def time(self) -> float:
        return self._t

    def sleep(self, seconds: float) -> None:
        self._t += float(seconds)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=(
            "preflight",
            "offline-integration",
            "materialize-evidence",
            "productive-session",
            "execute-post-unlock",
        ),
    )
    p.add_argument("--persistence-root", type=Path, default=None)
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--confirm-token-file", type=Path, default=None)
    p.add_argument("--session-go-file", type=Path, default=None)
    p.add_argument("--owner-go", action="store_true")
    p.add_argument("--owner-session-go", action="store_true")
    p.add_argument("--authorization-present", action="store_true")
    p.add_argument("--confirm-token-present", action="store_true")
    p.add_argument("--real-network", action="store_true")
    p.add_argument(
        "--execute",
        action="store_true",
        help="Required for execute-post-unlock; keeps preflight/productive-session side-effect free.",
    )
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sha = args.expected_repository_sha or _repo_sha()

    if args.command == "preflight":
        boundary = prove_public_md_network_boundary_v1(environ={})
        parity = prove_phase92_productive_entrypoint_parity_v1()
        payload = {
            "ok": bool(boundary.get("ok") and parity.get("ok")),
            "capability_id": CAPABILITY_ID,
            "session_id": TARGET_SESSION_ID,
            "segment_plan": list(SEGMENT_PLAN),
            "controlled_restart_exit_code": CONTROLLED_RESTART_EXIT_CODE,
            "exit_code_82_classification": EXIT_CODE_82_CLASSIFICATION,
            "network_boundary": boundary,
            "parity": parity,
            "productive_session_authorized": False,
            "notes": [
                "OFFLINE_HARNESS_FROM_PR5665_REUSED",
                "NO_SESSION_STARTED",
                "NO_AUTHORIZATION_ISSUED",
            ],
        }
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        return 0 if payload["ok"] else 1

    if args.command == "materialize-evidence":
        summary = materialize_capability_evidence_v1(
            repository_sha=sha,
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(redact_mapping_for_logs(summary), sort_keys=True, indent=2))
        return 0 if summary.get("ok") else 1

    if args.command == "productive-session":
        # Gate-only evaluation: never issue/consume auth, lock, network, or start.
        cfg_digest = str(
            load_activation_config_v1(
                config_path=_REPO_ROOT
                / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
            ).config_digest
        )
        confirm_present = bool(args.confirm_token_present) or bool(args.confirm_token_file)
        payload = reject_productive_session_start_v1(
            use_real_network=bool(args.real_network),
            environ=os.environ,
            expected_repository_sha=sha,
            expected_config_digest=cfg_digest,
            now_unix=float(time.time()),
            owner_go=bool(args.owner_go),
            owner_session_go=bool(args.owner_session_go),
            session_go_path=args.session_go_file,
            authorization_present=bool(args.authorization_present),
            confirm_token_present=confirm_present,
            repo_root=_REPO_ROOT,
        )
        notes = list(payload.get("notes") or [])
        notes.extend(
            [
                "PRODUCTIVE_SESSION_COMMAND_IS_GATE_EVALUATION_ONLY",
                "NO_AUTHORIZATION_ISSUED",
                "NO_AUTHORIZATION_CONSUMED",
                "NO_SESSION_LOCK",
                "NO_NETWORK_REQUEST",
                "NO_SESSION_START",
            ]
        )
        payload = dict(payload)
        payload["notes"] = notes
        payload["network_session_started"] = False
        payload["authorization_consumed"] = False
        payload["session_started"] = False
        payload["network_request_count"] = 0
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        # Exit 0 only means Session-GO unlock evaluation passed; session is not started.
        return 0 if payload.get("productive_session_execution_permitted") else 2

    if args.command == "execute-post-unlock":
        # Explicit execute mode: unlock → consume → lock → canonical offline runner.
        # Real network remains forbidden in this capability step.
        if args.real_network:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blockers": ["REAL_NETWORK_FORBIDDEN_IN_POST_UNLOCK_CAPABILITY_DEFAULT"],
                        "canonical_runner_invoked": False,
                        "network_session_started": False,
                    },
                    sort_keys=True,
                    indent=2,
                )
            )
            return 2
        if args.persistence_root is None or args.session_go_file is None:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blockers": ["PERSISTENCE_ROOT_AND_SESSION_GO_FILE_REQUIRED"],
                        "canonical_runner_invoked": False,
                    },
                    sort_keys=True,
                    indent=2,
                )
            )
            return 2
        cfg = str(
            load_activation_config_v1(
                config_path=_REPO_ROOT
                / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
            ).config_digest
        )
        now = float(time.time())
        clock = _Clock(now)
        calls: list[tuple[str, str]] = []
        transport = EeaPublicMdTransportV1(
            fetcher=build_fake_ticker_fetcher_v1(calls=calls, clock=clock),
            sleep=clock.sleep,
            environ={},
        )
        pre = build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=SEGMENT_PRE_ID,
            repository_sha=sha,
            config_digest=cfg,
            authorization_id="phase92_cli_execute_pre_auth_v1",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:pre",
            expires_at=now + 3600,
            max_segment_duration_seconds=DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
            expected_successor_state="CHECKPOINT_MATERIALIZED",
        )

        def _post_builder(**kwargs):
            return build_segment_authorization_envelope_v1(
                segment_role=SEGMENT_ROLE_POST,
                segment_id=SEGMENT_POST_ID,
                repository_sha=sha,
                config_digest=kwargs["config_digest"],
                authorization_id="phase92_cli_execute_post_auth_v1",
                restart_campaign_id=RESTART_CAMPAIGN_ID,
                runtime_session_id=f"{TARGET_SESSION_ID}:post",
                expires_at=now + 3600,
                max_segment_duration_seconds=DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
                expected_successor_state="RECOVERED_CONTINUOUS",
                predecessor_checkpoint_digest=kwargs["predecessor_checkpoint_digest"],
            )

        confirm_present = bool(args.confirm_token_present) or bool(args.confirm_token_file)
        result = invoke_post_unlock_canonical_runtime_v1(
            persistence_root=args.persistence_root,
            repository_sha=sha,
            config_digest=cfg,
            now_unix=now,
            owner_go=bool(args.owner_go),
            owner_session_go=bool(args.owner_session_go),
            session_go_path=args.session_go_file,
            pre_envelope=pre,
            post_envelope_builder=_post_builder,
            transport=transport,
            confirm_token_present=confirm_present,
            authorization_present=True,
            execute=bool(args.execute),
            allow_real_network=False,
            environ=os.environ,
            repo_root=_REPO_ROOT,
            applied_confirmation_ids=["conf_cli_execute_001"],
            candidate_observation_id="conf_cli_execute_001",
        )
        payload = result.to_dict()
        payload["fake_md_get_count"] = len(calls)
        payload["fake_md_methods"] = sorted({m for m, _u in calls})
        payload["network_session_started"] = False
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        return 0 if result.ok else 2

    # offline-integration
    if args.persistence_root is None:
        print(
            json.dumps(
                {"ok": False, "blockers": ["PERSISTENCE_ROOT_REQUIRED"]},
                sort_keys=True,
                indent=2,
            )
        )
        return 2
    cfg = str(
        load_activation_config_v1(
            config_path=_REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )
    now = 1_700_000_000.0
    clock = _Clock(now)
    calls: list[tuple[str, str]] = []
    transport = EeaPublicMdTransportV1(
        fetcher=build_fake_ticker_fetcher_v1(calls=calls, clock=clock),
        sleep=clock.sleep,
        environ={},
    )
    pre = build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_PRE,
        segment_id=SEGMENT_PRE_ID,
        repository_sha=sha,
        config_digest=cfg,
        authorization_id="phase92_cli_pre_auth_v1",
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=now + 3600,
        max_segment_duration_seconds=DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )

    def _post_builder(**kwargs):
        return build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=sha,
            config_digest=kwargs["config_digest"],
            authorization_id="phase92_cli_post_auth_v1",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=now + 3600,
            max_segment_duration_seconds=DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
            expected_successor_state="RECOVERED_CONTINUOUS",
            predecessor_checkpoint_digest=kwargs["predecessor_checkpoint_digest"],
        )

    result = run_offline_productive_restart_orchestration_v1(
        persistence_root=args.persistence_root,
        repository_sha=sha,
        pre_envelope=pre,
        post_envelope_builder=_post_builder,
        transport=transport,
        now_unix=now,
        repo_root=_REPO_ROOT,
        applied_confirmation_ids=["conf_cli_001"],
        candidate_observation_id="conf_cli_001",
    )
    payload = result.to_dict()
    payload["fake_md_get_count"] = len(calls)
    payload["fake_md_methods"] = sorted({m for m, _u in calls})
    print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
    if result.ok and result.controlled_restart_exit_code == CONTROLLED_RESTART_EXIT_CODE:
        # Controlled segment transition classification (not a generic failure).
        return int(CONTROLLED_RESTART_EXIT_CODE)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
