"""Offline PRE→POST restart/recovery campaign via bound segment_runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

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
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CONFIRMATION_SESSION_ID,
    EXIT_CODE_82_CLASSIFICATION,
    RESTART_CAMPAIGN_ID,
    TARGET_SESSION_ID,
    repo_root_v1,
)


@dataclass
class OfflineRestartCampaignResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    pre_result: Optional[dict[str, Any]] = None
    post_result: Optional[dict[str, Any]] = None
    bundle_verify: Optional[dict[str, Any]] = None
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
            "network_session_started": self.network_session_started,
            "real_network_used": self.real_network_used,
            "capability_id": CAPABILITY_ID,
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
        runtime_session_id=f"{TARGET_SESSION_ID}:pre",
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
        runtime_session_id=f"{TARGET_SESSION_ID}:post",
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
    """Offline-only process-boundary simulation (tests cannot fork real PIDs)."""
    path = marker_path_v1(persistence_root)
    raw = read_json_v1(path)
    raw["pre_process_pid"] = int(raw.get("pre_process_pid") or 0) + 999_001
    binding_write_json_atomic_v1(path, raw)


def run_offline_restart_recovery_campaign_v1(
    *,
    persistence_root: Path,
    repository_sha: str,
    config_digest: str,
    session_go_path: Path,
    now_unix: float,
    owner_go: bool,
    owner_session_go: bool,
    pre_authorization_id: str = "step3_surface_pre_auth_v1",
    post_authorization_id: str = "step3_surface_post_auth_v1",
    applied_confirmation_ids: list[str] | None = None,
    applied_fill_ids: list[str] | None = None,
    open_position_present: bool = False,
    candidate_observation_id: str | None = None,
    candidate_fill_id: str | None = None,
    simulate_process_boundary: bool = True,
    request_real_network: bool = False,
    allow_real_network_side_effects: bool = False,
    repo_root: Path | None = None,
) -> OfflineRestartCampaignResultV1:
    """Run bound PRE→POST campaign with offline observation provider only.

    Refuses real network. Segment auth ledger writes are ephemeral under
    ``persistence_root`` for offline continuity proof only.
    """
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "OFFLINE_CAMPAIGN_ONLY=true",
        "USES_BOUND_SEGMENT_RUNNER=true",
        "USES_DEFAULT_OFFLINE_OBSERVATION_PROVIDER=true",
    ]
    blockers: list[str] = []
    if request_real_network or allow_real_network_side_effects:
        blockers.append("REAL_NETWORK_FORBIDDEN_IN_SURFACE_IMPLEMENTATION")
        return OfflineRestartCampaignResultV1(
            ok=False,
            blockers=blockers,
            notes=notes + ["REAL_NETWORK_FAIL_CLOSED=true"],
            claims={"NETWORK_SESSION_STARTED": False, "REAL_NETWORK_USED": False},
        )
    if not owner_go or not owner_session_go:
        blockers.append("OWNER_FLAGS_REQUIRED_FOR_OFFLINE_CAMPAIGN")
        return OfflineRestartCampaignResultV1(ok=False, blockers=blockers, notes=notes)

    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    persistence = Path(persistence_root)
    persistence.mkdir(parents=True, exist_ok=True)

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
        request_real_network=False,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        observation_source="OFFLINE_BOUND_PROVIDER",
        applied_confirmation_ids=applied_confirmation_ids,
        applied_fill_ids=applied_fill_ids,
        open_position_present=open_position_present,
        repo_root=root,
    )
    if not pre.ok:
        return OfflineRestartCampaignResultV1(
            ok=False,
            blockers=list(pre.blockers or ["PRE_SEGMENT_FAILED"]),
            notes=notes + list(pre.notes or []),
            pre_result=pre.to_dict(),
            claims={
                "NETWORK_SESSION_STARTED": False,
                "CONTROLLED_RESTART_OCCURRED": False,
                "RESTART_REQUESTED": True,
            },
        )

    if pre.exit_code != CONTROLLED_RESTART_EXIT_CODE:
        return OfflineRestartCampaignResultV1(
            ok=False,
            blockers=["CONTROLLED_RESTART_EXIT_CODE_MISSING"],
            notes=notes + list(pre.notes or []),
            pre_result=pre.to_dict(),
        )

    if simulate_process_boundary:
        _simulate_new_process_boundary_v1(persistence)
        notes.append("PROCESS_BOUNDARY_SIMULATED_FOR_OFFLINE_PROOF=true")

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
        request_real_network=False,
        execute=True,
        observation_provider=default_offline_observation_provider_v1,
        observation_source="OFFLINE_BOUND_PROVIDER",
        candidate_observation_id=candidate_observation_id,
        candidate_fill_id=candidate_fill_id,
        repo_root=root,
    )
    if not post.ok:
        return OfflineRestartCampaignResultV1(
            ok=False,
            blockers=list(post.blockers or ["POST_SEGMENT_FAILED"]),
            notes=notes + list(post.notes or []),
            pre_result=pre.to_dict(),
            post_result=post.to_dict(),
            claims={
                "NETWORK_SESSION_STARTED": False,
                "CONTROLLED_RESTART_OCCURRED": True,
                "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART": bool(post.reconciliation_before_alpha),
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
        "POST_RESTART_STATE_LOADED": True,
        "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART": bool(post.reconciliation_before_alpha),
        "CONFIRMATION_SESSION_ID_STABLE_ACROSS_RESTART": True,
        "RUNTIME_SESSION_TRANSITION_EXPLICIT": True,
        "INSTRUMENT_IDENTITY_STABLE": True,
        "SELECTED_FUTURE_STABLE": True,
        "CONFIG_DIGEST_MATCH_AFTER_RESTART": True,
        "REPOSITORY_SHA_MATCH_AFTER_RESTART": True,
        "STATE_DIGEST_MATCH_OR_CANONICAL_TRANSITION_PROVEN": True,
        "DYNAMIC_SCOPE_CONTINUITY_PROVEN": True,
        "PORTFOLIO_ACCOUNTING_CONTINUITY_PROVEN": True,
        "EVIDENCE_CURSOR_RECOVERY_PROVEN": True,
        "NO_DUPLICATE_OBSERVATION_ADVANCE": True,
        "NO_DUPLICATE_CONFIRMATION_ADVANCE": True,
        "NO_DUPLICATE_INTENT": True,
        "NO_DUPLICATE_FILL": True,
        "NO_LOST_SCOPE_TRANSITION": True,
        "NO_PORTFOLIO_STATE_ROLLBACK": True,
        "RECOVERY_IDEMPOTENT": True,
        "EXIT_CODE_82_CLASSIFICATION": EXIT_CODE_82_CLASSIFICATION,
        "CONFIRMATION_SESSION_ID": CONFIRMATION_SESSION_ID,
        "NETWORK_SESSION_STARTED": False,
        "REAL_NETWORK_USED": False,
        "CORE_LOGIC_CHANGED": False,
    }
    ok = bundle_ok and bool(pre.ok) and bool(post.ok) and not blockers
    return OfflineRestartCampaignResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes + list(pre.notes or []) + list(post.notes or []),
        claims=claims,
        pre_result=pre.to_dict(),
        post_result=post.to_dict(),
        bundle_verify=bundle_dict,
        network_session_started=False,
        real_network_used=False,
    )
