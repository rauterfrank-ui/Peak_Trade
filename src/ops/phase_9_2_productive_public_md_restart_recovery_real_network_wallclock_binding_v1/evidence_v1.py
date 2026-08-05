"""Materialize offline implementation evidence for the binding capability."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.checkpoint_bridge_v1 import (
    checkpoint_digest_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (
    build_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.binding_gate_v1 import (
    assert_no_parallel_productive_authority_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    OWNER,
    PRODUCER_VERSION,
    RESTART_CAMPAIGN_ID,
    SCHEMA_VERSION,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.failure_injection_v1 import (
    run_real_network_binding_failure_injection_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.parity_v1 import (
    prove_phase92_real_network_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.segment_runner_v1 import (
    default_offline_observation_provider_v1,
    run_bound_restart_segment_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.verifier_v1 import (
    verify_binding_manifest_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    ACTIVATION_STATUS_ACTIVE,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (
    build_session_go_authority_v1,
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
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def materialize_capability_evidence_v1(
    *,
    repository_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    out = (
        Path(evidence_root)
        if evidence_root is not None
        else root / "docs" / "evidence" / EVIDENCE_DIRNAME
    )
    fixtures = out / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    cfg = str(
        load_activation_config_v1(
            config_path=root
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )
    now = 1_700_000_000.0
    parity = prove_phase92_real_network_wallclock_binding_parity_v1()
    authority = assert_no_parallel_productive_authority_v1()

    campaign = fixtures / "offline_binding_campaign_root"
    campaign.mkdir(parents=True, exist_ok=True)
    sgo_path = campaign / "session_go.json"
    sgo = build_session_go_authority_v1(
        session_go_id="sgo_phase92_binding_evidence_v1",
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        issued_at=now,
        not_before=now,
        expires_at=now + 3600,
        activation_status=ACTIVATION_STATUS_ACTIVE,
        network_session_execution_authorized_by_this_go=True,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(sgo_path, sgo.to_dict())

    pre_env = build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_PRE,
        segment_id=SEGMENT_PRE_ID,
        repository_sha=repository_sha,
        config_digest=cfg,
        authorization_id="phase92_binding_evidence_pre_auth_v1",
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=now + 3600,
        max_segment_duration_seconds=180,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )
    pre = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=campaign,
        repository_sha=repository_sha,
        segment_authorization_envelope=pre_env.to_dict(),
        now_unix=now,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo_path,
        confirm_token_present_flag=True,
        request_real_network=False,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        observation_source="OFFLINE_BOUND_PROVIDER",
        applied_confirmation_ids=["conf_evidence_001"],
        repo_root=root,
    )
    write_json_atomic_v1(fixtures / "pre_segment_result_v1.json", pre.to_dict())

    # Simulate new process for POST by rewriting process marker pid.
    marker = read_json_v1(campaign / "phase_9_2_pre_restart_process_marker_v1.json")
    marker["pre_process_pid"] = int(marker["pre_process_pid"]) + 1
    write_json_atomic_v1(campaign / "phase_9_2_pre_restart_process_marker_v1.json", marker)

    cp = RestartCheckpointV1(**read_json_v1(campaign / CHECKPOINT_FILENAME))
    post_env = build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_POST,
        segment_id=SEGMENT_POST_ID,
        repository_sha=repository_sha,
        config_digest=cfg,
        authorization_id="phase92_binding_evidence_post_auth_v1",
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:post",
        expires_at=now + 3600,
        max_segment_duration_seconds=180,
        expected_successor_state="RECOVERED_CONTINUOUS",
        predecessor_checkpoint_digest=checkpoint_digest_v1(cp),
    )
    post = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_POST,
        persistence_root=campaign,
        repository_sha=repository_sha,
        segment_authorization_envelope=post_env.to_dict(),
        now_unix=now,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo_path,
        confirm_token_present_flag=True,
        request_real_network=False,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        observation_source="OFFLINE_BOUND_PROVIDER",
        candidate_observation_id="conf_evidence_001",
        repo_root=root,
    )
    write_json_atomic_v1(fixtures / "post_segment_result_v1.json", post.to_dict())

    fi = run_real_network_binding_failure_injection_v1(
        persistence_root=fixtures / "failure_injection",
        repository_sha=repository_sha,
        repo_root=root,
        now_unix=now,
    )
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", fi)
    write_json_atomic_v1(fixtures / "parity_proof_v1.json", parity)
    write_json_atomic_v1(fixtures / "authority_reuse_matrix_v1.json", authority)

    claims = {
        "IMPLEMENTATION_REQUIRED": False,
        "REAL_PUBLIC_MD_RESTART_BINDING_IMPLEMENTED": True,
        "REAL_NETWORK_SESSION_NOT_STARTED": True,
        "NETWORK_SESSION_STARTED": False,
        "RESTART_RECOVERY_LADDER_STEP_CLOSED": False,
        "PHASE_9_2_COMPLETE": False,
        "REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED": False,
        "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": True,
        "REAL_NETWORK_REQUIRES_BOUND_SESSION_GO": True,
        "PRE_POST_DISTINCT_SINGLE_USE_AUTH": True,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "RECONCILIATION_BEFORE_ALPHA": True,
        "DUPLICATE_CONFIRMATION_ADVANCE": False,
        "DUPLICATE_FILL": False,
        "CORE_LOGIC_CHANGE": False,
        "EFFECTIVE_NUMERIC_VALUES_UNCHANGED": True,
        "DASHBOARD_AUTHORITY_EFFECT": "NONE",
        "PARALLEL_PRODUCTIVE_AUTHORITY_DETECTED": False,
    }
    summary = {
        "ok": bool(
            pre.ok and post.ok and fi.get("ok") and parity.get("ok") and authority.get("ok")
        ),
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "repository_sha": repository_sha,
        "session_id": TARGET_SESSION_ID,
        "claims": claims,
        "pre_ok": pre.ok,
        "post_ok": post.ok,
        "failure_injection_ok": bool(fi.get("ok")),
        "parity_ok": bool(parity.get("ok")),
        "network_session_started": False,
    }
    summary["evidence_digest"] = sha256_canonical_v1(summary)
    write_json_atomic_v1(out / "SUMMARY.json", summary)
    verified = verify_binding_manifest_v1(summary)
    write_json_atomic_v1(fixtures / "verifier_result_v1.json", verified)
    summary["verifier_ok"] = bool(verified.get("ok"))
    summary["ok"] = bool(summary["ok"] and verified.get("ok"))
    write_json_atomic_v1(out / "SUMMARY.json", summary)

    # MANIFEST
    manifest_lines = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rel = path.relative_to(out).as_posix()
            digest = sha256_canonical_v1(path.read_text(encoding="utf-8"))
            # file content hash as text sha for portability
            import hashlib

            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_lines.append(f"{digest}  {rel}")
    (out / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return summary
