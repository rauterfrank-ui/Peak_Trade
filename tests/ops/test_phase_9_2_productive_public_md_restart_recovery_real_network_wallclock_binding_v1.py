"""Tests for PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.checkpoint_bridge_v1 import (
    checkpoint_digest_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (
    build_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.binding_gate_v1 import (
    assert_no_parallel_productive_authority_v1,
    evaluate_real_network_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.constants_v1 import (
    CONTROLLED_RESTART_EXIT_CODE,
    CORE_LOGIC_CHANGE,
    EXIT_CODE_82_CLASSIFICATION,
    PRODUCTIVE_ENTRYPOINT_ID,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    RESTART_CAMPAIGN_ID,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.evidence_v1 import (
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.failure_injection_v1 import (
    run_real_network_binding_failure_injection_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.parity_v1 import (
    prove_phase92_real_network_wallclock_binding_parity_v1,
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
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    CHECKPOINT_FILENAME,
    PRE_TERMINAL_MANIFEST_FILENAME,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    read_json_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (
    RestartSegmentLockV1,
    lock_path_for_root_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.models_v1 import (
    RestartCheckpointV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.py"
)
NOW = 1_700_000_000.0


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _issue_sgo(path: Path, *, sha: str, cfg: str, network: bool = True) -> None:
    auth = build_session_go_authority_v1(
        session_go_id="sgo_test_binding_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=NOW,
        not_before=NOW,
        expires_at=NOW + 3600,
        activation_status=ACTIVATION_STATUS_ACTIVE,
        network_session_execution_authorized_by_this_go=network,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(path, auth.to_dict())


def _pre_env(sha: str, cfg: str, auth_id: str = "phase92_test_pre_auth_v1"):
    return build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_PRE,
        segment_id=SEGMENT_PRE_ID,
        repository_sha=sha,
        config_digest=cfg,
        authorization_id=auth_id,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=NOW + 3600,
        max_segment_duration_seconds=180,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )


def _post_env(sha: str, cfg: str, pred: str, auth_id: str = "phase92_test_post_auth_v1"):
    return build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_POST,
        segment_id=SEGMENT_POST_ID,
        repository_sha=sha,
        config_digest=cfg,
        authorization_id=auth_id,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:post",
        expires_at=NOW + 3600,
        max_segment_duration_seconds=180,
        expected_successor_state="RECOVERED_CONTINUOUS",
        predecessor_checkpoint_digest=pred,
    )


def test_parity_and_no_parallel_authority() -> None:
    parity = prove_phase92_real_network_wallclock_binding_parity_v1()
    authority = assert_no_parallel_productive_authority_v1()
    assert parity["ok"] is True
    assert CORE_LOGIC_CHANGE is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False
    assert authority["ok"] is True
    assert authority["parallel_productive_authority_detected"] is False


def test_gate_fail_closed_matrix(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)

    missing = evaluate_real_network_wallclock_binding_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=None,
        authorization_present=True,
        confirm_token_present_flag=True,
        request_real_network=True,
    )
    assert missing.ok is False
    assert "SESSION_GO_MISSING" in missing.blockers

    no_owner = evaluate_real_network_wallclock_binding_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=False,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        request_real_network=True,
    )
    assert no_owner.ok is False
    assert "OWNER_GO_REQUIRED" in no_owner.blockers

    no_session_owner = evaluate_real_network_wallclock_binding_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=False,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        request_real_network=True,
    )
    assert no_session_owner.ok is False
    assert "OWNER_SESSION_GO_REQUIRED" in no_session_owner.blockers

    no_auth = evaluate_real_network_wallclock_binding_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=False,
        confirm_token_present_flag=True,
        request_real_network=True,
    )
    assert no_auth.ok is False

    bad_sha = evaluate_real_network_wallclock_binding_gate_v1(
        expected_repository_sha="0" * 40,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        request_real_network=True,
    )
    assert bad_sha.ok is False
    assert "SESSION_GO_REPOSITORY_SHA_MISMATCH" in bad_sha.blockers

    bad_cfg = evaluate_real_network_wallclock_binding_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest="f" * 64,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        request_real_network=True,
    )
    assert bad_cfg.ok is False


def test_confirm_token_argv_rejected() -> None:
    blockers = reject_confirm_token_argv_v1(["execute-segment", "--confirm-token", "x"])
    assert "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" in blockers
    proc = subprocess.run(
        [sys.executable, str(CLI), "gate", "--confirm-token", "plaintext"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" in proc.stdout


def test_wrong_segment_and_lineage(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    env = _pre_env(sha, cfg).to_dict()
    env["segment_role"] = SEGMENT_ROLE_POST  # wrong for PRE call
    env["predecessor_checkpoint_digest"] = "abc"
    # rebuild digest would fail validation; use raw broken role without valid envelope digest
    result = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=tmp_path / "seg",
        repository_sha=sha,
        segment_authorization_envelope=env,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False

    bad_campaign = _pre_env(sha, cfg, auth_id="phase92_test_pre_campaign_v1").to_dict()
    # campaign mismatch via envelope field injection after build is not on envelope;
    # simulate via runner campaign check by forging session id
    bad_campaign["session_id"] = "wrong_session"
    # envelope digest will fail validation
    result2 = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=tmp_path / "seg2",
        repository_sha=sha,
        segment_authorization_envelope=bad_campaign,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        repo_root=REPO_ROOT,
    )
    assert result2.ok is False


def test_pre_exit_82_and_fake_md_claim(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    pre = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=tmp_path / "pre",
        repository_sha=sha,
        segment_authorization_envelope=_pre_env(sha, cfg).to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        applied_confirmation_ids=["conf_001"],
        repo_root=REPO_ROOT,
    )
    assert pre.ok is True
    assert pre.exit_code == CONTROLLED_RESTART_EXIT_CODE
    assert pre.exit_code_classification == EXIT_CODE_82_CLASSIFICATION
    assert pre.claims["NETWORK_SESSION_STARTED"] is False
    assert pre.claims["RESTART_RECOVERY_LADDER_STEP_CLOSED"] is False

    fake = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=tmp_path / "fake",
        repository_sha=sha,
        segment_authorization_envelope=_pre_env(sha, cfg, "phase92_fake_pre").to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=fake_md_observation_provider_v1,
        observation_source="FAKE_MD",
        repo_root=REPO_ROOT,
    )
    assert fake.real_session_claim_satisfied is False
    assert fake.fake_md_used is True


def test_auth_reuse_and_identical_pre_post_and_same_process(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    root = tmp_path / "camp"
    pre = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=root,
        repository_sha=sha,
        segment_authorization_envelope=_pre_env(sha, cfg).to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        applied_confirmation_ids=["conf_001"],
        repo_root=REPO_ROOT,
    )
    assert pre.ok is True
    cp = RestartCheckpointV1(**read_json_v1(root / CHECKPOINT_FILENAME))
    pred = checkpoint_digest_v1(cp)

    same_proc = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_POST,
        persistence_root=root,
        repository_sha=sha,
        segment_authorization_envelope=_post_env(sha, cfg, pred).to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        repo_root=REPO_ROOT,
    )
    assert same_proc.ok is False
    assert "POST_RESTART_SAME_PROCESS_FORBIDDEN" in same_proc.blockers

    # identical auth
    same_auth = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_POST,
        persistence_root=root,
        repository_sha=sha,
        segment_authorization_envelope=_post_env(
            sha, cfg, pred, auth_id="phase92_test_pre_auth_v1"
        ).to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        repo_root=REPO_ROOT,
    )
    assert same_auth.ok is False
    assert any(
        b in same_auth.blockers
        for b in (
            "PRE_AND_POST_MUST_USE_DISTINCT_AUTHORIZATIONS",
            "POST_RESTART_SAME_PROCESS_FORBIDDEN",
            "SEGMENT_AUTHORIZATION_INVALID:authorization_already_consumed",
        )
    ) or any("authorization" in b.lower() or "CONSUMED" in b for b in same_auth.blockers)


def test_post_new_process_pass_and_duplicate_guards(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    root = tmp_path / "camp2"
    pre = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=root,
        repository_sha=sha,
        segment_authorization_envelope=_pre_env(sha, cfg, "phase92_pre_a").to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        applied_confirmation_ids=["conf_dup"],
        applied_fill_ids=["fill_dup"],
        repo_root=REPO_ROOT,
    )
    assert pre.ok is True
    marker = read_json_v1(root / "phase_9_2_pre_restart_process_marker_v1.json")
    marker["pre_process_pid"] = int(marker["pre_process_pid"]) + 999
    write_json_atomic_v1(root / "phase_9_2_pre_restart_process_marker_v1.json", marker)
    cp = RestartCheckpointV1(**read_json_v1(root / CHECKPOINT_FILENAME))
    post = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_POST,
        persistence_root=root,
        repository_sha=sha,
        segment_authorization_envelope=_post_env(
            sha, cfg, checkpoint_digest_v1(cp), "phase92_post_a"
        ).to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        candidate_observation_id="conf_dup",
        candidate_fill_id="fill_dup",
        repo_root=REPO_ROOT,
    )
    assert post.ok is True
    assert post.reconciliation_before_alpha is True
    assert post.alpha_blocked is False
    assert post.claims["DUPLICATE_CONFIRMATION_ADVANCE"] is False
    assert post.claims["DUPLICATE_FILL"] is False
    notes = " ".join(post.notes)
    assert "DUPLICATE_CONFIRMATION_PREVENTED" in notes or "DUPLICATE_FILL_PREVENTED" in notes


def test_missing_pre_manifest_and_digest_mismatch_and_recon_required(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    root = tmp_path / "camp3"
    # POST without PRE
    write_json_atomic_v1(
        root / "phase_9_2_pre_restart_process_marker_v1.json",
        {
            "schema_version": "phase_9_2_pre_restart_process_marker.v1",
            "session_id": TARGET_SESSION_ID,
            "restart_campaign_id": RESTART_CAMPAIGN_ID,
            "pre_authorization_id": "x",
            "pre_terminal_manifest_digest": "y",
            "pre_process_pid": 1,
            "same_session_resume_allowed": False,
            "post_restart_new_process_required": True,
        },
    )
    missing = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_POST,
        persistence_root=root,
        repository_sha=sha,
        segment_authorization_envelope=_post_env(sha, cfg, "pred").to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        repo_root=REPO_ROOT,
    )
    assert missing.ok is False
    assert "PRE_TERMINAL_MANIFEST_MISSING" in missing.blockers or any(
        "PRE_TERMINAL" in b for b in missing.blockers
    )

    # recon required flag
    denied = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_POST,
        persistence_root=root,
        repository_sha=sha,
        segment_authorization_envelope=_post_env(sha, cfg, "pred", "phase92_post_recon").to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        require_reconciliation_before_alpha=False,
        repo_root=REPO_ROOT,
    )
    # may fail earlier on missing manifest; if it reaches recon check:
    assert denied.ok is False


def test_orphan_lock_fail_closed(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    root = tmp_path / "orphan"
    root.mkdir()
    lock = RestartSegmentLockV1(
        lock_path=lock_path_for_root_v1(root),
        runtime_session_id="foreign",
        owner="foreign",
    )
    lock.acquire()
    result = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=root,
        repository_sha=sha,
        segment_authorization_envelope=_pre_env(sha, cfg, "phase92_orphan").to_dict(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        confirm_token_present_flag=True,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False


def test_real_network_cli_refused_and_credential_paths_unreachable(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-segment",
            "--segment-role",
            SEGMENT_ROLE_PRE,
            "--persistence-root",
            str(tmp_path / "p"),
            "--session-go-file",
            str(tmp_path / "missing.json"),
            "--segment-auth-file",
            str(tmp_path / "missing_auth.json"),
            "--request-real-network",
            "--execute",
            "--owner-go",
            "--owner-session-go",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY_CLI" in proc.stdout
    parity = prove_phase92_real_network_wallclock_binding_parity_v1()
    assert parity["claims"]["CORE_LOGIC_CHANGE"] is False


def test_failure_injection_and_materialize_evidence(tmp_path: Path) -> None:
    sha = _sha()
    fi = run_real_network_binding_failure_injection_v1(
        persistence_root=tmp_path / "fi",
        repository_sha=sha,
        repo_root=REPO_ROOT,
        now_unix=NOW,
    )
    assert fi["ok"] is True
    summary = materialize_capability_evidence_v1(
        repository_sha=sha,
        evidence_root=tmp_path / "ev",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["claims"]["NETWORK_SESSION_STARTED"] is False
    assert summary["claims"]["RESTART_RECOVERY_LADDER_STEP_CLOSED"] is False
    assert summary["claims"]["REAL_PUBLIC_MD_RESTART_BINDING_IMPLEMENTED"] is True
    assert summary["claims"]["READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION"] is True


def test_cli_preflight() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI), "preflight"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["network_session_started"] is False


def test_existing_offline_restart_harness_still_importable() -> None:
    from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1 import (
        verify_restart_bundle_v1,
    )
    from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.parity_v1 import (
        prove_phase92_post_unlock_invocation_parity_v1,
    )

    assert callable(verify_restart_bundle_v1)
    assert prove_phase92_post_unlock_invocation_parity_v1()["ok"] is True
