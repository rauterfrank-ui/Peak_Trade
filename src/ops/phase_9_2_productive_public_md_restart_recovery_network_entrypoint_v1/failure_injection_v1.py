"""Failure-injection matrix for productive restart network entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (
    DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
    DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
    RESTART_CAMPAIGN_ID,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.fake_public_md_v1 import (
    build_fake_ticker_fetcher_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.orchestrator_v1 import (
    run_offline_productive_restart_orchestration_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (
    SegmentAuthorizationError,
    build_segment_authorization_envelope_v1,
    validate_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (
    RestartSegmentLockV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


class _Clock:
    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self._t = float(start)

    def time(self) -> float:
        return self._t

    def sleep(self, seconds: float) -> None:
        self._t += float(seconds)


def _config_digest(repo_root: Path) -> str:
    return str(
        load_activation_config_v1(
            config_path=repo_root
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _pre_envelope(*, repo_sha: str, config_digest: str, auth_id: str, now: float):
    return build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_PRE,
        segment_id=SEGMENT_PRE_ID,
        repository_sha=repo_sha,
        config_digest=config_digest,
        authorization_id=auth_id,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=now + 3600,
        max_segment_duration_seconds=DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )


def run_failure_injection_matrix_v1(
    *,
    tmp_root: Path,
    repository_sha: str,
    repo_root: Path,
    now_unix: float = 1_700_000_000.0,
) -> dict[str, Any]:
    cfg = _config_digest(repo_root)
    results: dict[str, Any] = {}

    # 1) fixture auth rejected
    try:
        build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=SEGMENT_PRE_ID,
            repository_sha=repository_sha,
            config_digest=cfg,
            authorization_id="fixture_auth",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id="rt",
            expires_at=now_unix + 10,
            max_segment_duration_seconds=60,
            expected_successor_state="X",
            fixture=True,
            productive=False,
        )
        results["fixture_auth_rejected"] = False
    except SegmentAuthorizationError as exc:
        results["fixture_auth_rejected"] = "fixture" in str(exc)

    # 2) SHA mismatch
    env = _pre_envelope(
        repo_sha=repository_sha, config_digest=cfg, auth_id="auth_sha", now=now_unix
    ).to_dict()
    try:
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha="deadbeef" * 5,
            expected_config_digest=cfg,
            now_unix=now_unix,
        )
        results["sha_mismatch_rejected"] = False
    except SegmentAuthorizationError as exc:
        results["sha_mismatch_rejected"] = "repository_sha_mismatch" in str(exc)

    # 3) config mismatch
    try:
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest="0" * 64,
            now_unix=now_unix,
        )
        results["config_mismatch_rejected"] = False
    except SegmentAuthorizationError as exc:
        results["config_mismatch_rejected"] = "config_digest_mismatch" in str(exc)

    # 4) segment mismatch
    try:
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_POST,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            expected_predecessor_checkpoint_digest="a" * 64,
            now_unix=now_unix,
        )
        results["segment_mismatch_rejected"] = False
    except SegmentAuthorizationError as exc:
        results["segment_mismatch_rejected"] = "segment_role_mismatch" in str(exc)

    # 5) session mismatch
    try:
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id="wrong_session",
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
        )
        results["session_mismatch_rejected"] = False
    except SegmentAuthorizationError as exc:
        results["session_mismatch_rejected"] = "session_id_mismatch" in str(exc)

    # 6) revoked
    try:
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            revoked_authorization_ids={"auth_sha"},
        )
        results["revoked_rejected"] = False
    except SegmentAuthorizationError as exc:
        results["revoked_rejected"] = "authorization_revoked" in str(exc)

    # 7) consumed
    try:
        validate_segment_authorization_envelope_v1(
            env,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            consumed_authorization_ids={"auth_sha"},
        )
        results["consumed_rejected"] = False
    except SegmentAuthorizationError as exc:
        results["consumed_rejected"] = "authorization_already_consumed" in str(exc)

    # 8) POST without checkpoint
    try:
        build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=repository_sha,
            config_digest=cfg,
            authorization_id="auth_post",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=now_unix + 3600,
            max_segment_duration_seconds=DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
            expected_successor_state="RECOVERED",
            predecessor_checkpoint_digest=None,
        )
        results["post_without_checkpoint_rejected"] = False
    except SegmentAuthorizationError as exc:
        results["post_without_checkpoint_rejected"] = "predecessor_checkpoint" in str(exc)

    # 9) POST wrong checkpoint digest
    post = build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_POST,
        segment_id=SEGMENT_POST_ID,
        repository_sha=repository_sha,
        config_digest=cfg,
        authorization_id="auth_post_bad",
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:post",
        expires_at=now_unix + 3600,
        max_segment_duration_seconds=DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
        expected_successor_state="RECOVERED",
        predecessor_checkpoint_digest="b" * 64,
    ).to_dict()
    try:
        validate_segment_authorization_envelope_v1(
            post,
            expected_segment_role=SEGMENT_ROLE_POST,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            expected_predecessor_checkpoint_digest="c" * 64,
            now_unix=now_unix,
        )
        results["post_wrong_checkpoint_rejected"] = False
    except SegmentAuthorizationError as exc:
        results["post_wrong_checkpoint_rejected"] = "predecessor_checkpoint_digest_mismatch" in str(
            exc
        )

    # 10) parallel lock conflict
    lock_root = tmp_root / "lock_conflict"
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_path = lock_root / "productive_restart_orchestration.lock"
    holder = RestartSegmentLockV1(
        lock_path=lock_path,
        runtime_session_id="holder",
        owner="holder",
    )
    holder.acquire()
    clock = _Clock(now_unix)
    calls: list[tuple[str, str]] = []
    transport = EeaPublicMdTransportV1(
        fetcher=build_fake_ticker_fetcher_v1(calls=calls, clock=clock),
        sleep=clock.sleep,
        environ={},
    )

    def _post_builder(**kwargs: Any):
        return build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=repository_sha,
            config_digest=kwargs["config_digest"],
            authorization_id="auth_post_lock",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=now_unix + 3600,
            max_segment_duration_seconds=DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
            expected_successor_state="RECOVERED",
            predecessor_checkpoint_digest=kwargs["predecessor_checkpoint_digest"],
        )

    conflict = run_offline_productive_restart_orchestration_v1(
        persistence_root=lock_root,
        repository_sha=repository_sha,
        pre_envelope=_pre_envelope(
            repo_sha=repository_sha, config_digest=cfg, auth_id="auth_pre_lock", now=now_unix
        ),
        post_envelope_builder=_post_builder,
        transport=transport,
        now_unix=now_unix,
        repo_root=repo_root,
    )
    results["parallel_lock_rejected"] = (not conflict.ok) and any(
        "lock" in b.lower() or "exists" in b.lower() or "duplicate" in b.lower()
        for b in conflict.blockers
    )
    holder.release_by_owner()

    results["ok"] = all(bool(v) for v in results.values())
    return results
