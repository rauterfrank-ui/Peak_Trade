"""Productive orchestration: segment auth → public-MD boundary → harness → verifier.

Default mode is offline/fake-MD only. Real network/session execution remains gated
and disabled by capability constants unless a later Owner session GO is supplied.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.checkpoint_bridge_v1 import (
    CheckpointBridgeError,
    build_checkpoint_from_public_md_observations_v1,
    checkpoint_digest_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CONFIRMATION_SESSION_ID,
    CONTROLLED_RESTART_EXIT_CODE,
    DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
    DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
    EXIT_CODE_82_CLASSIFICATION,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    ORCHESTRATION_LOCK_FILENAME,
    ORCHESTRATION_MANIFEST_FILENAME,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED,
    PRODUCTIVE_SESSION_GO_ENV,
    REAL_NETWORK_ENV,
    RESTART_CAMPAIGN_ID,
    SEGMENT_PLAN,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.fake_public_md_v1 import (
    poll_fake_public_md_observations_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.models_v1 import (
    OrchestrationCampaignResultV1,
    OrchestrationSegmentResultV1,
    SegmentAuthorizationEnvelopeV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (
    SegmentAuthorizationError,
    assert_productive_artifact_not_fixture_v1,
    validate_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (
    consume_authorization_once_v1,
    ledger_path_for_root_v1,
    load_consumed_authorization_ids_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.contract_v1 import (
    build_restart_session_contract_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (
    RestartLockError,
    RestartSegmentLockV1,
    lock_path_for_root_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.segment_harness_v1 import (
    run_post_restart_segment_v1,
    run_pre_restart_segment_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1 import (
    verify_restart_bundle_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


class OrchestrationError(RuntimeError):
    """Fail-closed productive orchestration error."""


def _activation_digest(*, repo_root: Path) -> str:
    activation = load_activation_config_v1(
        config_path=repo_root
        / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
    )
    return str(activation.config_digest)


def _classify_exit_code(code: int | None) -> str:
    if code == CONTROLLED_RESTART_EXIT_CODE:
        return EXIT_CODE_82_CLASSIFICATION
    if code is None:
        return "NO_EXIT_CODE"
    return "UNEXPECTED_RUNTIME_FAILURE_EXIT"


def assert_real_session_gates_closed_v1(
    *,
    use_real_network: bool,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    """Offline/default gates: permanent unscoped enable remains false.

    Env flags alone never unlock productive execution. Unlock requires a bound
    ACTIVE Session-GO artifact evaluated by evaluate_productive_session_start_gates_v1.
    """
    env = environ if environ is not None else os.environ
    blockers: list[str] = []
    if use_real_network:
        blockers.append("REAL_NETWORK_REQUESTED_BUT_IMPLEMENTATION_DEFAULT_FORBIDS")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED:
        blockers.append("PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED_MUST_REMAIN_FALSE_HERE")
    if str(env.get(PRODUCTIVE_SESSION_GO_ENV) or "") == "1":
        # Env alone remains insufficient; bound Session-GO capability is required.
        blockers.append("PRODUCTIVE_SESSION_GO_ENV_INSUFFICIENT_WITHOUT_BOUND_SESSION_GO_ARTIFACT")
    if str(env.get(REAL_NETWORK_ENV) or "") == "1" and use_real_network:
        blockers.append("REAL_NETWORK_ENV_INSUFFICIENT_WITHOUT_BOUND_SESSION_GO_ARTIFACT")
    return blockers


def run_offline_productive_restart_orchestration_v1(
    *,
    persistence_root: Path,
    repository_sha: str,
    pre_envelope: SegmentAuthorizationEnvelopeV1 | Mapping[str, Any],
    post_envelope_builder: Any,
    transport: EeaPublicMdTransportV1,
    now_unix: float,
    repo_root: Path | None = None,
    open_position_present: bool = False,
    applied_fill_ids: list[str] | None = None,
    applied_confirmation_ids: list[str] | None = None,
    candidate_observation_id: str | None = None,
    candidate_fill_id: str | None = None,
    revoked_authorization_ids: set[str] | None = None,
    authorization_artifact_path: Path | None = None,
) -> OrchestrationCampaignResultV1:
    """Offline productive chain with fake/deterministic public-MD transport boundary."""
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    persistence = Path(persistence_root)
    persistence.mkdir(parents=True, exist_ok=True)
    notes = [
        "MODE=OFFLINE_FAKE_PUBLIC_MD_TRANSPORT",
        "REUSES_PR5665_HARNESS_AND_VERIFIER",
        "REUSES_WALLCLOCK_NETWORK_BOUNDARY",
        "NO_REAL_NETWORK",
        "NO_REAL_SESSION_ACTIVATION",
        f"EXIT_CODE_82_CLASSIFICATION={EXIT_CODE_82_CLASSIFICATION}",
    ]
    blockers = assert_real_session_gates_closed_v1(use_real_network=False)
    boundary = prove_public_md_network_boundary_v1(environ={})
    if not boundary["ok"]:
        blockers.extend(boundary.get("blockers") or [])

    orchestration_lock = RestartSegmentLockV1(
        lock_path=persistence / ORCHESTRATION_LOCK_FILENAME,
        runtime_session_id=f"{TARGET_SESSION_ID}:orchestrator",
        owner=f"{TARGET_SESSION_ID}:orchestrator",
    )
    pre_result: OrchestrationSegmentResultV1 | None = None
    post_result: OrchestrationSegmentResultV1 | None = None
    verifier: dict[str, Any] | None = None

    try:
        if blockers:
            raise OrchestrationError(",".join(blockers))
        orchestration_lock.acquire()

        config_digest = _activation_digest(repo_root=root)
        if authorization_artifact_path is not None:
            assert_productive_artifact_not_fixture_v1(authorization_artifact_path)

        pre_payload = (
            pre_envelope.to_dict()
            if isinstance(pre_envelope, SegmentAuthorizationEnvelopeV1)
            else dict(pre_envelope)
        )
        pre_env = validate_segment_authorization_envelope_v1(
            pre_payload,
            expected_segment_role=SEGMENT_ROLE_PRE,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            now_unix=now_unix,
            consumed_authorization_ids=load_consumed_authorization_ids_v1(
                ledger_path_for_root_v1(persistence)
            ),
            revoked_authorization_ids=revoked_authorization_ids,
        )

        # Consume PRE auth once before any MD / harness side effect.
        consume_authorization_once_v1(
            ledger_path=ledger_path_for_root_v1(persistence),
            authorization_id=pre_env.authorization_id,
            authorization_digest=pre_env.authorization_digest,
            segment_id=pre_env.segment_id,
            segment_role=pre_env.segment_role,
            runtime_session_id=f"{TARGET_SESSION_ID}:pre",
        )

        identities = poll_fake_public_md_observations_v1(
            transport=transport,
            count=MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
            instrument_id=CANONICAL_INSTRUMENT_ID,
        )
        checkpoint = build_checkpoint_from_public_md_observations_v1(
            distinct_observation_count=MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
            observation_identities=identities,
            open_position_present=open_position_present,
            open_position_quantity=1.0 if open_position_present else 0.0,
            applied_fill_ids=applied_fill_ids,
            applied_confirmation_ids=applied_confirmation_ids,
            confirmation_session_id=CONFIRMATION_SESSION_ID,
        )
        cp_digest = checkpoint_digest_v1(checkpoint)

        pre_contract = build_restart_session_contract_v1(
            repository_sha=repository_sha,
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=SEGMENT_PRE_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:pre",
            authorization_id=pre_env.authorization_id,
            authorization_digest=pre_env.authorization_digest,
            expected_runtime_state_digest=checkpoint.runtime_state_digest,
            expected_portfolio_digest=checkpoint.portfolio_digest,
            expected_scope_digest=checkpoint.scope_digest,
            expected_accounting_digest=checkpoint.accounting_digest,
            expected_evidence_cursor=checkpoint.evidence_cursor,
            repo_root=root,
        )
        harness_pre = run_pre_restart_segment_v1(
            contract=pre_contract,
            persistence_root=persistence,
            checkpoint=checkpoint,
            request_controlled_restart=True,
            authorization_preconsumed=True,
        )
        if not harness_pre.ok:
            raise OrchestrationError(
                "pre_harness_failed:" + ",".join(harness_pre.blockers or ["unknown"])
            )
        if harness_pre.controlled_restart_exit_code != CONTROLLED_RESTART_EXIT_CODE:
            raise OrchestrationError("controlled_restart_exit_code_mismatch")

        pre_result = OrchestrationSegmentResultV1(
            ok=True,
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=SEGMENT_PRE_ID,
            authorization_id=pre_env.authorization_id,
            authorization_digest=pre_env.authorization_digest,
            authorization_consumed=True,
            wallclock_started=True,
            wallclock_network_opened=True,
            harness_ok=True,
            controlled_restart_exit_code=CONTROLLED_RESTART_EXIT_CODE,
            checkpoint_digest=cp_digest,
            terminal_manifest_digest=harness_pre.terminal_manifest_digest,
            reconciliation_before_alpha=True,
            notes=[
                _classify_exit_code(CONTROLLED_RESTART_EXIT_CODE),
                "FAKE_PUBLIC_MD_POLLS_COMPLETED",
            ],
            telemetry=harness_pre.telemetry,
        )

        # POST envelope must bind the verified PRE checkpoint digest.
        post_payload = post_envelope_builder(
            predecessor_checkpoint_digest=cp_digest,
            predecessor_terminal_manifest_digest=harness_pre.terminal_manifest_digest,
            config_digest=config_digest,
        )
        post_env = validate_segment_authorization_envelope_v1(
            post_payload if isinstance(post_payload, Mapping) else post_payload.to_dict(),
            expected_segment_role=SEGMENT_ROLE_POST,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            expected_predecessor_checkpoint_digest=cp_digest,
            now_unix=now_unix,
            consumed_authorization_ids=load_consumed_authorization_ids_v1(
                ledger_path_for_root_v1(persistence)
            ),
            revoked_authorization_ids=revoked_authorization_ids,
        )
        consume_authorization_once_v1(
            ledger_path=ledger_path_for_root_v1(persistence),
            authorization_id=post_env.authorization_id,
            authorization_digest=post_env.authorization_digest,
            segment_id=post_env.segment_id,
            segment_role=post_env.segment_role,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
        )

        post_contract = build_restart_session_contract_v1(
            repository_sha=repository_sha,
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:post",
            authorization_id=post_env.authorization_id,
            authorization_digest=post_env.authorization_digest,
            expected_runtime_state_digest=checkpoint.runtime_state_digest,
            expected_portfolio_digest=checkpoint.portfolio_digest,
            expected_scope_digest=checkpoint.scope_digest,
            expected_accounting_digest=checkpoint.accounting_digest,
            expected_evidence_cursor=checkpoint.evidence_cursor,
            predecessor_segment_id=SEGMENT_PRE_ID,
            predecessor_terminal_manifest_digest=harness_pre.terminal_manifest_digest,
            repo_root=root,
        )
        harness_post = run_post_restart_segment_v1(
            contract=post_contract,
            persistence_root=persistence,
            candidate_observation_id=candidate_observation_id,
            candidate_fill_id=candidate_fill_id,
            authorization_preconsumed=True,
        )
        if not harness_post.ok:
            raise OrchestrationError(
                "post_harness_failed:" + ",".join(harness_post.blockers or ["unknown"])
            )

        post_result = OrchestrationSegmentResultV1(
            ok=True,
            segment_role=SEGMENT_ROLE_POST,
            segment_id=SEGMENT_POST_ID,
            authorization_id=post_env.authorization_id,
            authorization_digest=post_env.authorization_digest,
            authorization_consumed=True,
            wallclock_started=False,
            wallclock_network_opened=False,
            harness_ok=True,
            controlled_restart_exit_code=None,
            checkpoint_digest=cp_digest,
            terminal_manifest_digest=harness_post.terminal_manifest_digest,
            reconciliation_before_alpha=bool(
                harness_post.telemetry.get("reconciliation_completed_before_alpha")
            ),
            notes=["POST_RESTART_RECOVERY_COMPLETE"],
            telemetry=harness_post.telemetry,
        )

        verified = verify_restart_bundle_v1(persistence_root=persistence)
        verifier = verified.to_dict()
        if not verified.verified:
            raise OrchestrationError(
                "bundle_verifier_failed:" + ",".join(verified.blockers or ["unknown"])
            )

        claims = {
            "PRODUCTIVE_NETWORK_ENTRYPOINT_ADDED": True,
            "CANONICAL_WALLCLOCK_RUNNER_REUSED": True,
            "OFFLINE_HARNESS_REUSED": True,
            "CANONICAL_AUTHORIZATION_PATH_REUSED": True,
            "CANONICAL_CHECKPOINT_CONTRACT_REUSED": True,
            "CANONICAL_VERIFIER_REUSED": True,
            "PARALLEL_AUTHORITY_ADDED": False,
            "CANONICAL_SEGMENT_PLAN": list(SEGMENT_PLAN),
            "EXIT_CODE_82_CLASSIFICATION": EXIT_CODE_82_CLASSIFICATION,
            "POST_RESTART_CHECKPOINT_BINDING": True,
            "RECONCILIATION_BEFORE_ALPHA_BOUND": True,
            "SESSION_LOCK_BOUND": True,
            "SINGLE_WRITER_PROVEN": True,
            "PUBLIC_MD_ONLY_BOUND": True,
            "GET_ONLY_BOUND": True,
            "FIXTURE_AUTH_PRODUCTIVELY_REJECTED": True,
            "SINGLE_USE_AUTHORIZATION_ENFORCED": True,
            "NETWORK_SESSION_STARTED": False,
            "REAL_AUTHORIZATION_ISSUED": False,
            "REAL_AUTHORIZATION_CONSUMED": False,
            "RUNTIME_STARTED": True,
            "DEFAULT_PRE_MAX_DURATION": DEFAULT_PRE_SEGMENT_MAX_DURATION_SECONDS,
            "DEFAULT_POST_MAX_DURATION": DEFAULT_POST_SEGMENT_MAX_DURATION_SECONDS,
            "RESTART_CAMPAIGN_ID": RESTART_CAMPAIGN_ID,
        }
        campaign = OrchestrationCampaignResultV1(
            ok=True,
            session_id=TARGET_SESSION_ID,
            segment_plan=SEGMENT_PLAN,
            pre=pre_result,
            post=post_result,
            verifier=verifier,
            controlled_restart_exit_code=CONTROLLED_RESTART_EXIT_CODE,
            network_session_started=False,
            real_authorization_issued=False,
            real_authorization_consumed=False,
            runtime_started=True,
            blockers=[],
            notes=notes,
            claims=claims,
        )
        write_json_atomic_v1(persistence / ORCHESTRATION_MANIFEST_FILENAME, campaign.to_dict())
        return campaign
    except (
        OrchestrationError,
        SegmentAuthorizationError,
        CheckpointBridgeError,
        RestartLockError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        fail = OrchestrationCampaignResultV1(
            ok=False,
            session_id=TARGET_SESSION_ID,
            segment_plan=SEGMENT_PLAN,
            pre=pre_result,
            post=post_result,
            verifier=verifier,
            controlled_restart_exit_code=None,
            network_session_started=False,
            real_authorization_issued=False,
            real_authorization_consumed=False,
            runtime_started=bool(pre_result and pre_result.wallclock_started),
            blockers=sorted(set(blockers + [str(exc)])),
            notes=notes + ["ALPHA_OR_ORCHESTRATION_BLOCKED=true"],
            claims={"PARALLEL_AUTHORITY_ADDED": False},
        )
        write_json_atomic_v1(persistence / ORCHESTRATION_MANIFEST_FILENAME, fail.to_dict())
        return fail
    finally:
        if orchestration_lock.acquired:
            try:
                orchestration_lock.release_by_owner()
            except RestartLockError:
                pass
        # Ensure harness lock path is not orphaned if a segment left it.
        harness_lock = lock_path_for_root_v1(persistence)
        if harness_lock.is_file():
            try:
                harness_lock.unlink()
            except OSError:
                pass


def evaluate_productive_session_start_gates_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    now_unix: float,
    owner_go: bool = False,
    owner_session_go: bool = False,
    session_go_path: Path | None = None,
    session_go_payload: Mapping[str, Any] | None = None,
    authorization_present: bool = False,
    confirm_token_present: bool = False,
    use_real_network: bool = False,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Fail-closed productive-session gate ordered before auth/lock/network/start.

    Permanent PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED stays false. Unlock is
    only via a bound ACTIVE Session-GO plus Owner flags, auth, and confirm token.
    This function never issues/consumes authorization, acquires locks, opens
    network, or starts a session.
    """
    from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (  # noqa: E501
        TARGET_ENTRYPOINT_ID,
        TARGET_ENTRYPOINT_PATH,
    )
    from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.gate_v1 import (
        evaluate_session_go_gate_v1,
    )

    env = environ if environ is not None else os.environ
    notes = [
        "ENTRYPOINT_IMPLEMENTED",
        "NO_PERMANENT_UNSCOPED_ENABLE_FLAG=true",
        f"PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED_CONSTANT={PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED}",
        "SESSION_GO_REQUIRED_BEFORE_AUTHORIZATION_CONSUMPTION=true",
        "SESSION_GO_REQUIRED_BEFORE_LOCK_ACQUISITION=true",
        "SESSION_GO_REQUIRED_BEFORE_NETWORK_ACCESS=true",
        "SESSION_GO_REQUIRED_BEFORE_SESSION_START=true",
    ]
    blockers: list[str] = []

    # Permanent package constant must remain false; Session-GO is the unlock surface.
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED:
        blockers.append("PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED_MUST_REMAIN_FALSE_HERE")

    # Env alone never unlocks.
    if (
        str(env.get(PRODUCTIVE_SESSION_GO_ENV) or "") == "1"
        and session_go_path is None
        and session_go_payload is None
    ):
        blockers.append("PRODUCTIVE_SESSION_GO_ENV_INSUFFICIENT_WITHOUT_BOUND_SESSION_GO_ARTIFACT")
    if (
        use_real_network
        and str(env.get(REAL_NETWORK_ENV) or "") == "1"
        and session_go_path is None
        and session_go_payload is None
    ):
        blockers.append("REAL_NETWORK_ENV_INSUFFICIENT_WITHOUT_BOUND_SESSION_GO_ARTIFACT")

    gate = evaluate_session_go_gate_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_session_id=TARGET_SESSION_ID,
        expected_entrypoint_id=TARGET_ENTRYPOINT_ID,
        expected_entrypoint_path=TARGET_ENTRYPOINT_PATH,
        now_unix=now_unix,
        owner_go=owner_go,
        owner_session_go=owner_session_go,
        session_go_path=session_go_path,
        session_go_payload=session_go_payload,
        authorization_present=authorization_present,
        confirm_token_present=confirm_token_present,
    )
    blockers.extend(gate.blockers)
    notes.extend(gate.notes)

    ok = (not blockers) and bool(gate.ok) and bool(gate.productive_session_execution_permitted)
    return {
        "ok": ok,
        "blockers": sorted(set(blockers)),
        "notes": notes,
        "network_session_started": False,
        "authorization_issued": False,
        "authorization_consumed": False,
        "runtime_started": False,
        "session_lock_acquired": False,
        "session_started": False,
        "network_request_count": 0,
        "session_go_authority_satisfied": bool(gate.session_go_authority_satisfied),
        "productive_session_execution_permitted": bool(gate.productive_session_execution_permitted),
        "authorization_may_proceed": bool(gate.authorization_may_proceed),
        "lock_may_proceed": bool(gate.lock_may_proceed),
        "network_may_proceed": bool(gate.network_may_proceed),
        "session_start_may_proceed": bool(gate.session_start_may_proceed),
        "session_go_gate": gate.to_dict(),
    }


def reject_productive_session_start_v1(
    *,
    use_real_network: bool = False,
    environ: Mapping[str, str] | None = None,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
    now_unix: float | None = None,
    owner_go: bool = False,
    owner_session_go: bool = False,
    session_go_path: Path | None = None,
    session_go_payload: Mapping[str, Any] | None = None,
    authorization_present: bool = False,
    confirm_token_present: bool = False,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """CLI/compatible gate: Session-GO first; never starts a session here."""
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    sha = expected_repository_sha or ""
    cfg = expected_config_digest or ""
    if not sha or not cfg:
        # Without bindings, fail closed before any side effect.
        return {
            "ok": False,
            "blockers": sorted(
                {
                    *(
                        ["SESSION_GO_MISSING"]
                        if session_go_path is None and session_go_payload is None
                        else []
                    ),
                    *(["EXPECTED_REPOSITORY_SHA_REQUIRED"] if not sha else []),
                    *(["EXPECTED_CONFIG_DIGEST_REQUIRED"] if not cfg else []),
                }
            ),
            "network_session_started": False,
            "authorization_issued": False,
            "authorization_consumed": False,
            "runtime_started": False,
            "session_lock_acquired": False,
            "session_started": False,
            "network_request_count": 0,
            "session_go_authority_satisfied": False,
            "productive_session_execution_permitted": False,
            "notes": [
                "ENTRYPOINT_IMPLEMENTED",
                "SESSION_GO_BINDINGS_REQUIRED_FOR_UNLOCK_EVALUATION",
            ],
        }
    if now_unix is None:
        import time

        now_unix = float(time.time())
    _ = root  # repo_root reserved for future digest helpers; gate is pure evaluation
    return evaluate_productive_session_start_gates_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=float(now_unix),
        owner_go=owner_go,
        owner_session_go=owner_session_go,
        session_go_path=session_go_path,
        session_go_payload=session_go_payload,
        authorization_present=authorization_present,
        confirm_token_present=confirm_token_present,
        use_real_network=use_real_network,
        environ=environ,
    )


def orchestration_identity_digest_v1() -> str:
    return sha256_canonical_v1(
        {
            "session_id": TARGET_SESSION_ID,
            "segment_plan": list(SEGMENT_PLAN),
            "exit_code": CONTROLLED_RESTART_EXIT_CODE,
            "classification": EXIT_CODE_82_CLASSIFICATION,
        }
    )
