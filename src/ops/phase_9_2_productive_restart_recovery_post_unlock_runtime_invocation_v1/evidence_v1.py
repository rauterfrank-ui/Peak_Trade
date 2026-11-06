"""Evidence materialization for post-unlock runtime invocation capability."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (  # noqa: E501
    EeaPublicMdTransportV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (  # noqa: E501
    DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
    DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
    RESTART_CAMPAIGN_ID,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.fake_public_md_v1 import (  # noqa: E501
    build_fake_ticker_fetcher_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.network_boundary_v1 import (  # noqa: E501
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (  # noqa: E501
    build_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.constants_v1 import (  # noqa: E501
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    OWNER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.digest_v1 import (  # noqa: E501
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.failure_injection_v1 import (  # noqa: E501
    run_post_unlock_failure_injection_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.invocation_v1 import (  # noqa: E501
    invoke_post_unlock_canonical_runtime_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.parity_v1 import (  # noqa: E501
    prove_phase92_post_unlock_invocation_parity_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.verifier_v1 import (  # noqa: E501
    verify_post_unlock_invocation_manifest_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    ACTIVATION_STATUS_ACTIVE,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (
    build_session_go_authority_v1,
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
    campaign_root = fixtures / "offline_post_unlock_campaign_root"
    campaign_root.mkdir(parents=True, exist_ok=True)

    sgo = build_session_go_authority_v1(
        session_go_id="sgo_evidence_offline_v1",
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        issued_at=now - 10,
        not_before=now - 5,
        expires_at=now + 3600,
        activation_status=ACTIVATION_STATUS_ACTIVE,
    )
    sgo_path = campaign_root / "session_go.json"
    write_json_atomic_v1(sgo_path, sgo.to_dict())

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
        repository_sha=repository_sha,
        config_digest=cfg,
        authorization_id="phase92_post_unlock_pre_auth_v1",
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        expires_at=now + 3600,
        max_segment_duration_seconds=DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
        expected_successor_state="CHECKPOINT_MATERIALIZED",
    )

    def _post_builder(**kwargs: Any):
        return build_segment_authorization_envelope_v1(
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            repository_sha=repository_sha,
            config_digest=kwargs["config_digest"],
            authorization_id="phase92_post_unlock_post_auth_v1",
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            expires_at=now + 3600,
            max_segment_duration_seconds=DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
            expected_successor_state="RECOVERED_CONTINUOUS",
            predecessor_checkpoint_digest=kwargs["predecessor_checkpoint_digest"],
        )

    invocation = invoke_post_unlock_canonical_runtime_v1(
        persistence_root=campaign_root,
        repository_sha=repository_sha,
        config_digest=cfg,
        now_unix=now,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo_path,
        pre_envelope=pre,
        post_envelope_builder=_post_builder,
        transport=transport,
        confirm_token_present=True,
        authorization_present=True,
        execute=True,
        repo_root=root,
        applied_confirmation_ids=["conf_post_unlock_001"],
        candidate_observation_id="conf_post_unlock_001",
    )
    verified = verify_post_unlock_invocation_manifest_v1(
        persistence_root=campaign_root, expected_ok=True
    )
    boundary = prove_public_md_network_boundary_v1(environ={})
    parity = prove_phase92_post_unlock_invocation_parity_v1()
    failure = run_post_unlock_failure_injection_v1(
        work_root=fixtures / "failure_injection",
        repository_sha=repository_sha,
        config_digest=cfg,
        now_unix=now,
        repo_root=root,
    )

    write_json_atomic_v1(fixtures / "parity_proof_v1.json", parity)
    write_json_atomic_v1(fixtures / "network_boundary_proof_v1.json", boundary)
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", failure)
    write_json_atomic_v1(fixtures / "invocation_result_v1.json", invocation.to_dict())
    write_json_atomic_v1(fixtures / "verifier_result_v1.json", verified)

    claims = {
        "POST_UNLOCK_RUNTIME_INVOCATION_ADDED": True,
        "PRODUCTIVE_EXECUTE_MODE_EXPLICIT": True,
        "PREFLIGHT_MODE_SIDE_EFFECT_FREE": True,
        "CANONICAL_RUNTIME_RUNNER_REUSED": True,
        "PARALLEL_RUNNER_ADDED": False,
        "NETWORK_SESSION_STARTED": False,
        "REAL_AUTHORIZATION_ISSUED": False,
        "REAL_AUTHORIZATION_CONSUMED": False,
        "AUTHORIZATION_CONSUMED_EXACTLY_ONCE_IN_OFFLINE_PROOF": bool(
            invocation.authorization_consumed_exactly_once
        ),
        "SESSION_LOCK_RELEASED": bool(invocation.session_lock_released),
        "RESTART_RECOVERY_COMPLETED": bool(invocation.restart_recovery_completed),
        "RECONCILIATION_BEFORE_ALPHA": bool(invocation.reconciliation_before_alpha),
        "FAILURE_INJECTION_OK": bool(failure.get("ok")),
        "PARITY_OK": bool(parity.get("ok")),
        "NETWORK_BOUNDARY_OK": bool(boundary.get("ok")),
        "VERIFIER_OK": bool(verified.get("ok")),
    }
    summary = {
        "ok": bool(
            invocation.ok
            and verified.get("ok")
            and parity.get("ok")
            and boundary.get("ok")
            and failure.get("ok")
        ),
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "repository_sha": repository_sha,
        "session_id": TARGET_SESSION_ID,
        "claims": claims,
        "invocation_ok": bool(invocation.ok),
        "verifier_ok": bool(verified.get("ok")),
        "parity_ok": bool(parity.get("ok")),
        "network_boundary_ok": bool(boundary.get("ok")),
        "failure_injection_ok": bool(failure.get("ok")),
        "fake_md_get_count": len(calls),
    }
    summary["evidence_digest"] = sha256_canonical_v1(summary)
    write_json_atomic_v1(out / "SUMMARY.json", summary)

    manifest_lines: list[str] = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rel = path.relative_to(out).as_posix()
            digest = sha256_canonical_v1(path.read_text(encoding="utf-8"))
            manifest_lines.append(f"{digest}  {rel}")
    (out / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return summary
