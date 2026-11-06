"""Offline failure-injection matrix for real-network wallclock binding."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (
    build_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.binding_gate_v1 import (
    evaluate_real_network_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.constants_v1 import (
    CONTROLLED_RESTART_EXIT_CODE,
    EXIT_CODE_82_CLASSIFICATION,
    PRODUCTIVE_ENTRYPOINT_ID,
    PRODUCTIVE_ENTRYPOINT_PATH,
    RESTART_CAMPAIGN_ID,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.segment_runner_v1 import (
    default_offline_observation_provider_v1,
    fake_md_observation_provider_v1,
    run_bound_restart_segment_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    ACTIVATION_STATUS_ACTIVE,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (
    build_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (
    RestartSegmentLockV1,
    lock_path_for_root_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def _cfg(repo_root: Path) -> str:
    return str(
        load_activation_config_v1(
            config_path=repo_root
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _issue_session_go(
    *,
    path: Path,
    repository_sha: str,
    config_digest: str,
    now: float,
    network_authorized: bool = True,
) -> None:
    auth = build_session_go_authority_v1(
        session_go_id="sgo_phase92_binding_fi_v1",
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        session_id=TARGET_SESSION_ID,
        entrypoint_id=PRODUCTIVE_ENTRYPOINT_ID,
        entrypoint_path=PRODUCTIVE_ENTRYPOINT_PATH,
        issued_at=now,
        not_before=now,
        expires_at=now + 3600,
        activation_status=ACTIVATION_STATUS_ACTIVE,
        network_session_execution_authorized_by_this_go=network_authorized,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(path, auth.to_dict())


def run_real_network_binding_failure_injection_v1(
    *,
    persistence_root: Path,
    repository_sha: str,
    repo_root: Path,
    now_unix: float = 1_700_000_000.0,
) -> dict[str, Any]:
    root = Path(repo_root)
    base = Path(persistence_root)
    base.mkdir(parents=True, exist_ok=True)
    cfg = _cfg(root)
    results: dict[str, Any] = {}

    def _case(name: str, fn: Callable[[], dict[str, Any]]) -> None:
        results[name] = fn()

    # 1 session-go missing
    _case(
        "session_go_missing",
        lambda: evaluate_real_network_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=True,
            session_go_path=None,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )

    sgo = base / "session_go.json"
    _issue_session_go(path=sgo, repository_sha=repository_sha, config_digest=cfg, now=now_unix)

    # 2 owner-go missing
    _case(
        "owner_go_missing",
        lambda: evaluate_real_network_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=False,
            owner_session_go=True,
            session_go_path=sgo,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )

    # 3 owner-session-go missing
    _case(
        "owner_session_go_missing",
        lambda: evaluate_real_network_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=False,
            session_go_path=sgo,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )

    # 4 authorization missing
    _case(
        "authorization_missing",
        lambda: evaluate_real_network_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=True,
            session_go_path=sgo,
            authorization_present=False,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )

    # 7 wrong repository sha
    _case(
        "wrong_repository_sha",
        lambda: evaluate_real_network_wallclock_binding_gate_v1(
            expected_repository_sha="deadbeef" * 5,
            expected_config_digest=cfg,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=True,
            session_go_path=sgo,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )

    # 8 wrong config digest
    _case(
        "wrong_config_digest",
        lambda: evaluate_real_network_wallclock_binding_gate_v1(
            expected_repository_sha=repository_sha,
            expected_config_digest="0" * 64,
            now_unix=now_unix,
            owner_go=True,
            owner_session_go=True,
            session_go_path=sgo,
            authorization_present=True,
            confirm_token_present_flag=True,
            request_real_network=True,
        ).to_dict(),
    )

    # 11 confirm token argv
    _case(
        "confirm_token_argv",
        lambda: {
            "ok": False,
            "blockers": reject_confirm_token_argv_v1(["--confirm-token", "secret"]),
        },
    )

    # Happy PRE for reuse / POST cases
    pre_root = base / "pre_ok"
    pre_env = build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_PRE,
        segment_id=SEGMENT_PRE_ID,
        repository_sha=repository_sha,
        config_digest=cfg,
        authorization_id="phase92_binding_pre_auth_v1",
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=now_unix + 3600,
        max_segment_duration_seconds=180,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )
    pre = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=pre_root,
        repository_sha=repository_sha,
        segment_authorization_envelope=pre_env.to_dict(),
        now_unix=now_unix,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        request_real_network=False,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        observation_source="OFFLINE_BOUND_PROVIDER",
        applied_confirmation_ids=["conf_binding_001"],
        repo_root=root,
    )
    results["pre_exit_82"] = {
        "ok": pre.ok,
        "exit_code": pre.exit_code,
        "classification": pre.exit_code_classification,
        "expected_classification": EXIT_CODE_82_CLASSIFICATION,
        "expected_exit": CONTROLLED_RESTART_EXIT_CODE,
    }

    # 12 fake md cannot satisfy real claim
    fake_root = base / "fake_md"
    fake = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=fake_root,
        repository_sha=repository_sha,
        segment_authorization_envelope=build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=SEGMENT_PRE_ID,
            repository_sha=repository_sha,
            config_digest=cfg,
            authorization_id="phase92_binding_fake_pre_auth_v1",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:pre",
            expires_at=now_unix + 3600,
            max_segment_duration_seconds=180,
            expected_successor_state="CHECKPOINT_MATERIALIZED",
        ).to_dict(),
        now_unix=now_unix,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=fake_md_observation_provider_v1,
        observation_source="FAKE_MD",
        repo_root=root,
    )
    results["fake_md_real_claim"] = {
        "ok": fake.ok,
        "real_session_claim_satisfied": fake.real_session_claim_satisfied,
        "fake_md_used": fake.fake_md_used,
    }

    # 14 POST same process
    from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.checkpoint_bridge_v1 import (
        checkpoint_digest_v1,
    )
    from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
        CHECKPOINT_FILENAME,
    )
    from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
        read_json_v1,
    )
    from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.models_v1 import (
        RestartCheckpointV1,
    )

    cp = RestartCheckpointV1(**read_json_v1(pre_root / CHECKPOINT_FILENAME))
    post_same = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_POST,
        persistence_root=pre_root,
        repository_sha=repository_sha,
        segment_authorization_envelope=build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=repository_sha,
            config_digest=cfg,
            authorization_id="phase92_binding_post_auth_v1",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=now_unix + 3600,
            max_segment_duration_seconds=180,
            expected_successor_state="RECOVERED_CONTINUOUS",
            predecessor_checkpoint_digest=checkpoint_digest_v1(cp),
        ).to_dict(),
        now_unix=now_unix,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        observation_source="OFFLINE_BOUND_PROVIDER",
        repo_root=root,
    )
    results["post_same_process"] = {
        "ok": post_same.ok,
        "blockers": post_same.blockers,
    }

    # 10 identical auth PRE/POST — mutate marker pre auth id equal
    # (reuse pre_root marker which has pre auth; use same auth id)
    post_same_auth = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_POST,
        persistence_root=pre_root,
        repository_sha=repository_sha,
        segment_authorization_envelope=build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=repository_sha,
            config_digest=cfg,
            authorization_id="phase92_binding_pre_auth_v1",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=now_unix + 3600,
            max_segment_duration_seconds=180,
            expected_successor_state="RECOVERED_CONTINUOUS",
            predecessor_checkpoint_digest=checkpoint_digest_v1(cp),
        ).to_dict(),
        now_unix=now_unix,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        repo_root=root,
    )
    results["identical_pre_post_auth"] = {
        "ok": post_same_auth.ok,
        "blockers": post_same_auth.blockers,
    }

    # 20 orphan lock
    orphan_root = base / "orphan_lock"
    orphan_root.mkdir(parents=True, exist_ok=True)
    lock = RestartSegmentLockV1(
        lock_path=lock_path_for_root_v1(orphan_root),
        runtime_session_id="foreign",
        owner="foreign_owner",
    )
    lock.acquire()
    orphan = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=orphan_root,
        repository_sha=repository_sha,
        segment_authorization_envelope=build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=SEGMENT_PRE_ID,
            repository_sha=repository_sha,
            config_digest=cfg,
            authorization_id="phase92_binding_orphan_pre_auth_v1",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:pre",
            expires_at=now_unix + 3600,
            max_segment_duration_seconds=180,
            expected_successor_state="CHECKPOINT_MATERIALIZED",
        ).to_dict(),
        now_unix=now_unix,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        repo_root=root,
    )
    results["orphan_lock"] = {"ok": orphan.ok, "blockers": orphan.blockers}

    # Aggregate expected fail-closed cases
    expected_fail = {
        "session_go_missing",
        "owner_go_missing",
        "owner_session_go_missing",
        "authorization_missing",
        "wrong_repository_sha",
        "wrong_config_digest",
        "confirm_token_argv",
        "post_same_process",
        "identical_pre_post_auth",
        "orphan_lock",
    }
    fail_ok = True
    for name in expected_fail:
        payload = results[name]
        if name == "confirm_token_argv":
            if "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" not in payload.get("blockers", []):
                fail_ok = False
        elif name == "pre_exit_82":
            continue
        elif payload.get("ok") is True:
            fail_ok = False
    if results["pre_exit_82"]["exit_code"] != CONTROLLED_RESTART_EXIT_CODE:
        fail_ok = False
    if results["pre_exit_82"]["classification"] != EXIT_CODE_82_CLASSIFICATION:
        fail_ok = False
    if results["fake_md_real_claim"].get("real_session_claim_satisfied"):
        fail_ok = False

    return {
        "ok": fail_ok,
        "cases": results,
        "pid": os.getpid(),
    }
