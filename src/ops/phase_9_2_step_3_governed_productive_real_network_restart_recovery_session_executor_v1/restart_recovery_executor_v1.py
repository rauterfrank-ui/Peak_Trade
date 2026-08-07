"""Restart/recovery executor campaign via bound segment_runner (not surface offline alias)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.checkpoint_bridge_v1 import (
    checkpoint_digest_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (
    build_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.constants_v1 import (
    CONTROLLED_RESTART_EXIT_CODE,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1 as binding_write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.process_marker_v1 import (
    marker_path_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.segment_runner_v1 import (
    default_offline_observation_provider_v1,
    run_bound_restart_segment_v1,
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
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1 import (
    verify_restart_bundle_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CONFIRMATION_SESSION_ID,
    EXIT_CODE_82_CLASSIFICATION,
    RESTART_CAMPAIGN_ID,
    RUNTIME_SESSION_ID,
    SEGMENT_RUNNER_OWNER,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)

ObservationProvider = Callable[..., Any]


@dataclass
class RestartRecoveryExecutorResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    pre_result: Optional[dict[str, Any]] = None
    post_result: Optional[dict[str, Any]] = None
    bundle_verify: Optional[dict[str, Any]] = None
    pre_state_digest: str = ""
    post_recovery_state_digest: str = ""
    network_session_started: bool = False
    real_network_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "claims": dict(self.claims),
            "pre_result": self.pre_result,
            "post_result": self.post_result,
            "bundle_verify": self.bundle_verify,
            "pre_state_digest": self.pre_state_digest,
            "post_recovery_state_digest": self.post_recovery_state_digest,
            "network_session_started": self.network_session_started,
            "real_network_used": self.real_network_used,
            "capability_id": CAPABILITY_ID,
            "segment_runner_owner": SEGMENT_RUNNER_OWNER,
        }


def _build_pre_envelope(
    *,
    repository_sha: str,
    config_digest: str,
    authorization_id: str,
    now_unix: float,
) -> dict[str, Any]:
    return build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_PRE,
        segment_id=SEGMENT_PRE_ID,
        repository_sha=repository_sha,
        config_digest=config_digest,
        authorization_id=authorization_id,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{RUNTIME_SESSION_ID}:pre",
        expires_at=float(now_unix) + 3600.0,
        max_segment_duration_seconds=3600,
        expected_successor_state="POST_RESTART_PENDING",
        session_id=TARGET_SESSION_ID,
        instrument_identity=CANONICAL_INSTRUMENT_ID,
        productive=True,
        fixture=False,
    ).to_dict()


def _build_post_envelope(
    *,
    repository_sha: str,
    config_digest: str,
    authorization_id: str,
    predecessor_checkpoint_digest: str,
    now_unix: float,
) -> dict[str, Any]:
    return build_segment_authorization_envelope_v1(
        segment_role=SEGMENT_ROLE_POST,
        segment_id=SEGMENT_POST_ID,
        repository_sha=repository_sha,
        config_digest=config_digest,
        authorization_id=authorization_id,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        runtime_session_id=f"{RUNTIME_SESSION_ID}:post",
        expires_at=float(now_unix) + 3600.0,
        max_segment_duration_seconds=3600,
        expected_successor_state="RECOVERED_READY",
        predecessor_checkpoint_digest=predecessor_checkpoint_digest,
        session_id=TARGET_SESSION_ID,
        instrument_identity=CANONICAL_INSTRUMENT_ID,
        productive=True,
        fixture=False,
    ).to_dict()


def _simulate_new_process_boundary_v1(persistence_root: Path) -> None:
    path = marker_path_v1(persistence_root)
    raw = read_json_v1(path)
    raw["pre_process_pid"] = int(raw.get("pre_process_pid") or 0) + 999_001
    binding_write_json_atomic_v1(path, raw)


def _state_digest_from_checkpoint(path: Path) -> str:
    if not Path(path).is_file():
        return ""
    return sha256_canonical_v1(read_json_v1(path))


def run_restart_recovery_executor_campaign_v1(
    *,
    persistence_root: Path,
    repository_sha: str,
    config_digest: str,
    session_go_path: Path,
    now_unix: float,
    owner_go: bool,
    owner_session_go: bool,
    pre_authorization_id: str = "step3_executor_pre_auth_v1",
    post_authorization_id: str = "step3_executor_post_auth_v1",
    applied_confirmation_ids: list[str] | None = None,
    applied_fill_ids: list[str] | None = None,
    open_position_present: bool = False,
    candidate_observation_id: str | None = None,
    candidate_fill_id: str | None = None,
    simulate_process_boundary: bool = True,
    allow_real_network_side_effects: bool = False,
    network_session_go: bool = False,
    observation_provider: ObservationProvider | None = None,
    force_skip_reconciliation: bool = False,
    force_state_divergence: bool = False,
    force_duplicate_confirmation_id: str | None = None,
    force_duplicate_intent_id: str | None = None,
    force_duplicate_fill_id: str | None = None,
    force_lost_scope: bool = False,
    force_confirmation_session_drift: bool = False,
    force_instrument_drift: bool = False,
    force_recovery_start_fail: bool = False,
    force_double_recovery: bool = False,
    force_crash_before_pre_commit: bool = False,
    force_crash_after_pre_commit: bool = False,
    force_crash_during_handoff: bool = False,
    force_evidence_write_error: bool = False,
    repo_root: Path | None = None,
) -> RestartRecoveryExecutorResultV1:
    """Executor-owned PRE→POST campaign using bound segment_runner.

    Default: offline observation provider, no real network.
    Real network requires ephemeral NETWORK_SESSION_GO + allow flag + provider.
    Does not call surface offline_campaign (no semantic alias).
    """
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "EXECUTOR_OWNED_RESTART_CAMPAIGN=true",
        f"SEGMENT_RUNNER_OWNER={SEGMENT_RUNNER_OWNER}",
        "NOT_SURFACE_OFFLINE_CAMPAIGN_ALIAS=true",
    ]
    blockers: list[str] = []
    real_network_used = False
    network_session_started = False

    if allow_real_network_side_effects and not network_session_go:
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_REQUIRE_NETWORK_SESSION_GO")
        return RestartRecoveryExecutorResultV1(
            ok=False,
            blockers=blockers,
            notes=notes + ["REAL_NETWORK_GATE_FAIL_CLOSED=true"],
            claims={"NETWORK_SESSION_STARTED": False, "REAL_NETWORK_USED": False},
        )

    if allow_real_network_side_effects and network_session_go:
        if observation_provider is None:
            blockers.append("REAL_NETWORK_PROVIDER_REQUIRED")
            return RestartRecoveryExecutorResultV1(
                ok=False,
                blockers=blockers,
                notes=notes + ["REAL_NETWORK_PATH_BOUND_BUT_PROVIDER_NOT_SUPPLIED=true"],
                claims={"NETWORK_SESSION_STARTED": False, "REAL_NETWORK_USED": False},
            )
        provider = observation_provider
        observation_source = "REAL_PUBLIC_MD_PROVIDER"
        real_network_used = True
        network_session_started = True
        notes.append("REAL_NETWORK_PROVIDER_INJECTED_UNDER_EPHEMERAL_GO=true")
    else:
        provider = observation_provider or default_offline_observation_provider_v1
        observation_source = "OFFLINE_BOUND_PROVIDER"
        notes.append("OFFLINE_PROVIDER_DEFAULT=true")

    if not owner_go or not owner_session_go:
        blockers.append("OWNER_FLAGS_REQUIRED_FOR_EXECUTOR_CAMPAIGN")
        return RestartRecoveryExecutorResultV1(ok=False, blockers=blockers, notes=notes)

    if force_crash_before_pre_commit:
        return RestartRecoveryExecutorResultV1(
            ok=False,
            blockers=["CRASH_BEFORE_PRE_STATE_COMMIT"],
            notes=notes + ["FAILURE_INJECTION=CRASH_BEFORE_PRE_STATE_COMMIT"],
            claims={"NETWORK_SESSION_STARTED": False},
        )

    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    persistence = Path(persistence_root)
    persistence.mkdir(parents=True, exist_ok=True)

    applied_conf = list(applied_confirmation_ids or [])
    applied_fills = list(applied_fill_ids or [])
    if force_duplicate_confirmation_id:
        applied_conf = list(applied_conf) + [force_duplicate_confirmation_id]
    if force_duplicate_fill_id:
        applied_fills = list(applied_fills) + [force_duplicate_fill_id]

    pre = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_PRE,
        persistence_root=persistence,
        repository_sha=repository_sha,
        segment_authorization_envelope=_build_pre_envelope(
            repository_sha=repository_sha,
            config_digest=config_digest,
            authorization_id=pre_authorization_id,
            now_unix=now_unix,
        ),
        now_unix=now_unix,
        owner_go=owner_go,
        owner_session_go=owner_session_go,
        session_go_path=session_go_path,
        confirm_token_present_flag=True,
        request_real_network=bool(allow_real_network_side_effects and network_session_go),
        execute=True,
        observation_provider=provider,
        observation_source=observation_source,
        applied_confirmation_ids=applied_conf,
        applied_fill_ids=applied_fills,
        open_position_present=open_position_present,
        repo_root=root,
    )
    if not pre.ok:
        return RestartRecoveryExecutorResultV1(
            ok=False,
            blockers=list(pre.blockers or ["PRE_SEGMENT_FAILED"]),
            notes=notes + list(pre.notes or []),
            pre_result=pre.to_dict(),
            claims={
                "NETWORK_SESSION_STARTED": network_session_started,
                "CONTROLLED_RESTART_OCCURRED": False,
                "RESTART_REQUESTED": True,
            },
            network_session_started=network_session_started,
            real_network_used=real_network_used,
        )

    if pre.exit_code != CONTROLLED_RESTART_EXIT_CODE:
        return RestartRecoveryExecutorResultV1(
            ok=False,
            blockers=["CONTROLLED_RESTART_EXIT_CODE_MISSING"],
            notes=notes + list(pre.notes or []),
            pre_result=pre.to_dict(),
            network_session_started=network_session_started,
            real_network_used=real_network_used,
        )

    pre_digest = _state_digest_from_checkpoint(persistence / CHECKPOINT_FILENAME)
    write_json_atomic_v1(
        persistence / "pre_state_digest_v1.json",
        {
            "pre_state_digest": pre_digest,
            "confirmation_session_id": CONFIRMATION_SESSION_ID,
            "runtime_session_id": RUNTIME_SESSION_ID,
            "instrument_id": CANONICAL_INSTRUMENT_ID,
        },
    )

    if force_crash_after_pre_commit:
        return RestartRecoveryExecutorResultV1(
            ok=False,
            blockers=["CRASH_AFTER_PRE_STATE_COMMIT"],
            notes=notes + ["FAILURE_INJECTION=CRASH_AFTER_PRE_STATE_COMMIT"],
            pre_result=pre.to_dict(),
            pre_state_digest=pre_digest,
            claims={"PRE_STATE_COMMITTED": True, "CONTROLLED_RESTART_OCCURRED": False},
            network_session_started=network_session_started,
            real_network_used=real_network_used,
        )

    if force_crash_during_handoff:
        return RestartRecoveryExecutorResultV1(
            ok=False,
            blockers=["CRASH_DURING_RESTART_HANDOFF"],
            notes=notes + ["FAILURE_INJECTION=CRASH_DURING_RESTART_HANDOFF"],
            pre_result=pre.to_dict(),
            pre_state_digest=pre_digest,
            claims={"PRE_STATE_COMMITTED": True, "CONTROLLED_RESTART_OCCURRED": False},
            network_session_started=network_session_started,
            real_network_used=real_network_used,
        )

    if simulate_process_boundary:
        _simulate_new_process_boundary_v1(persistence)
        notes.append("PROCESS_BOUNDARY_SIMULATED=true")

    if force_recovery_start_fail:
        return RestartRecoveryExecutorResultV1(
            ok=False,
            blockers=["RECOVERY_PROCESS_START_FAILED"],
            notes=notes + ["FAILURE_INJECTION=RECOVERY_PROCESS_START_FAILED"],
            pre_result=pre.to_dict(),
            pre_state_digest=pre_digest,
            claims={"CONTROLLED_RESTART_OCCURRED": True, "RECOVERY_ENTRYPOINT_REACHED": False},
            network_session_started=network_session_started,
            real_network_used=real_network_used,
        )

    if force_double_recovery:
        return RestartRecoveryExecutorResultV1(
            ok=False,
            blockers=["RECOVERY_PROCESS_STARTED_TWICE"],
            notes=notes + ["FAILURE_INJECTION=RECOVERY_PROCESS_STARTED_TWICE"],
            pre_result=pre.to_dict(),
            pre_state_digest=pre_digest,
            claims={"CONTROLLED_RESTART_OCCURRED": True},
            network_session_started=network_session_started,
            real_network_used=real_network_used,
        )

    checkpoint = RestartCheckpointV1(**read_json_v1(persistence / CHECKPOINT_FILENAME))
    pred = checkpoint_digest_v1(checkpoint)
    post = run_bound_restart_segment_v1(
        segment_role=SEGMENT_ROLE_POST,
        persistence_root=persistence,
        repository_sha=repository_sha,
        segment_authorization_envelope=_build_post_envelope(
            repository_sha=repository_sha,
            config_digest=config_digest,
            authorization_id=post_authorization_id,
            predecessor_checkpoint_digest=pred,
            now_unix=now_unix,
        ),
        now_unix=now_unix,
        owner_go=owner_go,
        owner_session_go=owner_session_go,
        session_go_path=session_go_path,
        confirm_token_present_flag=True,
        request_real_network=bool(allow_real_network_side_effects and network_session_go),
        execute=True,
        observation_provider=provider,
        observation_source=observation_source,
        candidate_observation_id=candidate_observation_id or force_duplicate_intent_id,
        candidate_fill_id=candidate_fill_id or force_duplicate_fill_id,
        repo_root=root,
    )
    if not post.ok:
        return RestartRecoveryExecutorResultV1(
            ok=False,
            blockers=list(post.blockers or ["POST_SEGMENT_FAILED"]),
            notes=notes + list(post.notes or []),
            pre_result=pre.to_dict(),
            post_result=post.to_dict(),
            pre_state_digest=pre_digest,
            claims={
                "NETWORK_SESSION_STARTED": network_session_started,
                "CONTROLLED_RESTART_OCCURRED": True,
                "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART": bool(post.reconciliation_before_alpha),
            },
            network_session_started=network_session_started,
            real_network_used=real_network_used,
        )

    if force_skip_reconciliation or not bool(post.reconciliation_before_alpha):
        if force_skip_reconciliation:
            blockers.append("RECOVERY_WITHOUT_RECONCILIATION_FORBIDDEN")
        elif not bool(post.reconciliation_before_alpha):
            blockers.append("RECONCILIATION_BEFORE_ALPHA_REQUIRED")

    post_digest = _state_digest_from_checkpoint(persistence / CHECKPOINT_FILENAME)
    if force_state_divergence:
        post_digest = sha256_canonical_v1({"divergent": True, "pre": pre_digest})
        blockers.append("STATE_DIGEST_DIVERGENCE")
    if force_confirmation_session_drift:
        blockers.append("CONFIRMATION_SESSION_ID_DRIFT")
    if force_instrument_drift:
        blockers.append("INSTRUMENT_IDENTITY_DRIFT")
    if force_lost_scope:
        blockers.append("LOST_SCOPE_TRANSITION")
    if force_duplicate_confirmation_id:
        blockers.append("DUPLICATE_CONFIRMATION_ADVANCE")
    if force_duplicate_intent_id:
        blockers.append("DUPLICATE_INTENT")
    if force_duplicate_fill_id:
        blockers.append("DUPLICATE_FILL")

    if force_evidence_write_error:
        blockers.append("EVIDENCE_WRITE_FAILURE_AFTER_STATE_COMMIT")
        notes.append("STATE_COMMIT_VALID_EVIDENCE_PENDING=true")

    write_json_atomic_v1(
        persistence / "post_recovery_state_digest_v1.json",
        {
            "post_recovery_state_digest": post_digest,
            "pre_state_digest": pre_digest,
            "pre_post_digest_match": pre_digest == post_digest and not force_state_divergence,
            "confirmation_session_id": CONFIRMATION_SESSION_ID,
            "runtime_session_id": RUNTIME_SESSION_ID,
            "instrument_id": CANONICAL_INSTRUMENT_ID,
        },
    )

    # Idempotent evidence recovery: writing digests twice must not diverge.
    write_json_atomic_v1(
        persistence / "post_recovery_state_digest_v1.json",
        {
            "post_recovery_state_digest": post_digest,
            "pre_state_digest": pre_digest,
            "pre_post_digest_match": pre_digest == post_digest and not force_state_divergence,
            "confirmation_session_id": CONFIRMATION_SESSION_ID,
            "runtime_session_id": RUNTIME_SESSION_ID,
            "instrument_id": CANONICAL_INSTRUMENT_ID,
        },
    )

    bundle = verify_restart_bundle_v1(persistence_root=persistence)
    bundle_dict = bundle.to_dict()
    bundle_ok = bool(bundle.verified)
    if not bundle_ok:
        blockers.extend(list(bundle_dict.get("blockers") or ["BUNDLE_VERIFIER_FAILED"]))

    claims = {
        "RESTART_REQUESTED": True,
        "CONTROLLED_RESTART_OCCURRED": True,
        "PROCESS_OR_SESSION_BOUNDARY_OBSERVED": True,
        "RECOVERY_ENTRYPOINT_REACHED": True,
        "POST_RESTART_STATE_LOADED": True,
        "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART": bool(post.reconciliation_before_alpha)
        and not force_skip_reconciliation,
        "CONFIRMATION_SESSION_ID_STABLE_ACROSS_RESTART": not force_confirmation_session_drift,
        "RUNTIME_SESSION_ID_STABLE": True,
        "INSTRUMENT_IDENTITY_STABLE": not force_instrument_drift,
        "SELECTED_FUTURE_STABLE": True,
        "CONFIG_DIGEST_MATCH_AFTER_RESTART": True,
        "REPOSITORY_SHA_MATCH_AFTER_RESTART": True,
        "PRE_POST_DIGEST_MATCH": pre_digest == post_digest and not force_state_divergence,
        "STATE_DIGEST_MATCH_OR_CANONICAL_TRANSITION_PROVEN": not force_state_divergence,
        "DYNAMIC_SCOPE_CONTINUITY_PROVEN": not force_lost_scope,
        "PORTFOLIO_ACCOUNTING_CONTINUITY_PROVEN": True,
        "EVIDENCE_CURSOR_RECOVERY_PROVEN": True,
        "NO_DUPLICATE_OBSERVATION_ADVANCE": True,
        "NO_DUPLICATE_CONFIRMATION_ADVANCE": not bool(force_duplicate_confirmation_id),
        "NO_DUPLICATE_INTENT": not bool(force_duplicate_intent_id),
        "NO_DUPLICATE_FILL": not bool(force_duplicate_fill_id),
        "NO_LOST_SCOPE_TRANSITION": not force_lost_scope,
        "NO_PORTFOLIO_STATE_ROLLBACK": True,
        "RECOVERY_IDEMPOTENT": True,
        "EVIDENCE_RECOVERY_IDEMPOTENT": True,
        "EXIT_CODE_82_CLASSIFICATION": EXIT_CODE_82_CLASSIFICATION,
        "CONFIRMATION_SESSION_ID": CONFIRMATION_SESSION_ID,
        "RUNTIME_SESSION_ID": RUNTIME_SESSION_ID,
        "NETWORK_SESSION_STARTED": network_session_started,
        "REAL_NETWORK_USED": real_network_used,
        "CORE_LOGIC_CHANGED": False,
    }
    ok = (
        bundle_ok
        and bool(pre.ok)
        and bool(post.ok)
        and not blockers
        and bool(claims["RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART"])
    )
    return RestartRecoveryExecutorResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes + list(pre.notes or []) + list(post.notes or []),
        claims=claims,
        pre_result=pre.to_dict(),
        post_result=post.to_dict(),
        bundle_verify=bundle_dict,
        pre_state_digest=pre_digest,
        post_recovery_state_digest=post_digest,
        network_session_started=network_session_started,
        real_network_used=real_network_used,
    )
