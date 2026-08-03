"""Post-unlock handoff to the existing canonical Phase-9.2 productive restart runner.

Call graph (after Session-GO unlock):
  evaluate_productive_session_start_gates_v1
  → validate Session-GO binding on segment auth envelopes
  → run_offline_productive_restart_orchestration_v1  (canonical runner)
      → consume auth once → lock → fake/public-MD boundary → PRE harness (exit 82)
      → POST harness recovery + reconciliation-before-alpha → verifier
  → materialize invocation manifest

This module never invents a parallel runner. Real network remains gated off by the
existing PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED=false constant and by this
capability's NETWORK_SESSION_ALLOWED=false default.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (  # noqa: E501
    EeaPublicMdTransportV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (  # noqa: E501
    TARGET_SESSION_ID as ENTRYPOINT_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.models_v1 import (  # noqa: E501
    OrchestrationCampaignResultV1,
    SegmentAuthorizationEnvelopeV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.orchestrator_v1 import (  # noqa: E501
    evaluate_productive_session_start_gates_v1,
    run_offline_productive_restart_orchestration_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.constants_v1 import (  # noqa: E501
    AUTHORITY_OWNER,
    AUTHORIZATION_AUTHORITY,
    CANONICAL_RUNTIME_RUNNER,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    INVOCATION_MANIFEST_FILENAME,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_ENTRYPOINT_ID,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED,
    SESSION_GO_AUTHORITY,
    SESSION_LOCK_AUTHORITY,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.digest_v1 import (  # noqa: E501
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_post_unlock_runtime_invocation_v1.models_v1 import (  # noqa: E501
    PostUnlockInvocationResultV1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (  # noqa: E501
    load_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.models_v1 import (  # noqa: E501
    SessionGoAuthorityV1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (  # noqa: E501
    ledger_path_for_root_v1,
    load_consumed_authorization_ids_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (  # noqa: E501
    lock_path_for_root_v1,
)


class PostUnlockInvocationError(RuntimeError):
    """Fail-closed post-unlock invocation error."""


CanonicalRuntimeRunnerV1 = Callable[..., OrchestrationCampaignResultV1]


def _envelope_dict(
    envelope: SegmentAuthorizationEnvelopeV1 | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(envelope, SegmentAuthorizationEnvelopeV1):
        return envelope.to_dict()
    return dict(envelope)


def _validate_session_go_auth_bindings_v1(
    *,
    authority: SessionGoAuthorityV1,
    pre_envelope: Mapping[str, Any],
    expected_repository_sha: str,
    expected_config_digest: str,
) -> list[str]:
    blockers: list[str] = []
    if authority.session_id != TARGET_SESSION_ID:
        blockers.append("SESSION_GO_SESSION_ID_MISMATCH")
    if authority.expected_repository_sha != expected_repository_sha:
        blockers.append("SESSION_GO_REPOSITORY_SHA_MISMATCH")
    if authority.expected_config_digest != expected_config_digest:
        blockers.append("SESSION_GO_CONFIG_DIGEST_MISMATCH")
    if authority.entrypoint_id != PRODUCTIVE_ENTRYPOINT_ID:
        blockers.append("SESSION_GO_ENTRYPOINT_ID_MISMATCH")
    if authority.entrypoint_path != PRODUCTIVE_ENTRYPOINT_PATH:
        blockers.append("SESSION_GO_ENTRYPOINT_PATH_MISMATCH")
    if not authority.public_md_only:
        blockers.append("SESSION_GO_PUBLIC_MD_ONLY_REQUIRED")
    if not authority.http_get_only:
        blockers.append("SESSION_GO_HTTP_GET_ONLY_REQUIRED")
    if str(pre_envelope.get("session_id") or "") != authority.session_id:
        blockers.append("AUTHORIZATION_SESSION_ID_SESSION_GO_MISMATCH")
    if str(pre_envelope.get("repository_sha") or "") != expected_repository_sha:
        blockers.append("AUTHORIZATION_REPOSITORY_SHA_MISMATCH")
    if str(pre_envelope.get("config_digest") or "") != expected_config_digest:
        blockers.append("AUTHORIZATION_CONFIG_DIGEST_MISMATCH")
    return sorted(set(blockers))


def invoke_post_unlock_canonical_runtime_v1(
    *,
    persistence_root: Path,
    repository_sha: str,
    config_digest: str,
    now_unix: float,
    owner_go: bool,
    owner_session_go: bool,
    session_go_path: Path,
    pre_envelope: SegmentAuthorizationEnvelopeV1 | Mapping[str, Any],
    post_envelope_builder: Any,
    transport: EeaPublicMdTransportV1,
    confirm_token_present: bool,
    authorization_present: bool = True,
    execute: bool = False,
    allow_real_network: bool = False,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
    runtime_runner: CanonicalRuntimeRunnerV1 | None = None,
    applied_confirmation_ids: list[str] | None = None,
    candidate_observation_id: str | None = None,
    open_position_present: bool = False,
) -> PostUnlockInvocationResultV1:
    """Fail-closed post-unlock invocation of the existing canonical restart runner.

    Requires explicit execute=True. Gate-only callers must leave execute=False.
    Real network remains forbidden by default in this capability.
    """
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    persistence = Path(persistence_root)
    persistence.mkdir(parents=True, exist_ok=True)
    env = environ if environ is not None else os.environ
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"AUTHORITY_OWNER={AUTHORITY_OWNER}",
        f"CANONICAL_RUNTIME_RUNNER={CANONICAL_RUNTIME_RUNNER}",
        f"CANONICAL_WALLCLOCK_RUNNER={CANONICAL_WALLCLOCK_RUNNER}",
        f"SESSION_GO_AUTHORITY={SESSION_GO_AUTHORITY}",
        f"AUTHORIZATION_AUTHORITY={AUTHORIZATION_AUTHORITY}",
        f"SESSION_LOCK_AUTHORITY={SESSION_LOCK_AUTHORITY}",
        "NO_PARALLEL_RUNNER=true",
        "CONSUME_BEFORE_SIDE_EFFECTS=true",
        f"NETWORK_SESSION_ALLOWED_CONSTANT={NETWORK_SESSION_ALLOWED}",
        (
            "PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED_CONSTANT="
            f"{PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED}"
        ),
    ]
    blockers: list[str] = []
    runner_calls = {"count": 0}
    result = PostUnlockInvocationResultV1(
        ok=False,
        notes=notes,
        session_id=TARGET_SESSION_ID,
        terminal_state="HARD_STOP",
    )

    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED or NETWORK_SESSION_ALLOWED:
        blockers.append("PERMANENT_UNSCOPED_ENABLE_MUST_REMAIN_FALSE")
    if allow_real_network:
        blockers.append("REAL_NETWORK_FORBIDDEN_IN_POST_UNLOCK_CAPABILITY_DEFAULT")
    if not execute:
        blockers.append("EXECUTE_MODE_REQUIRED")
        result.blockers = sorted(set(blockers))
        result.notes = notes + ["PREFLIGHT_OR_GATE_ONLY_NO_RUNNER_INVOCATION=true"]
        _write_manifest(persistence, result)
        return result

    gate = evaluate_productive_session_start_gates_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        now_unix=now_unix,
        owner_go=owner_go,
        owner_session_go=owner_session_go,
        session_go_path=session_go_path,
        authorization_present=authorization_present,
        confirm_token_present=confirm_token_present,
        use_real_network=False,
        environ=env,
    )
    result.session_go_authority_satisfied = bool(gate.get("session_go_authority_satisfied"))
    result.productive_session_execution_permitted = bool(
        gate.get("productive_session_execution_permitted")
    )
    notes.extend(list(gate.get("notes") or []))
    if not gate.get("ok") or not gate.get("productive_session_execution_permitted"):
        blockers.extend(list(gate.get("blockers") or ["SESSION_GO_GATE_FAILED"]))
        result.blockers = sorted(set(blockers))
        result.notes = notes + ["GATE_FALSE_NO_RUNNER_INVOCATION=true"]
        _write_manifest(persistence, result)
        return result

    try:
        authority = load_session_go_authority_v1(Path(session_go_path))
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"SESSION_GO_LOAD_FAILED:{type(exc).__name__}")
        result.blockers = sorted(set(blockers))
        result.notes = notes
        _write_manifest(persistence, result)
        return result

    result.session_go_id = authority.session_go_id
    result.session_go_digest = authority.session_go_digest
    pre_payload = _envelope_dict(pre_envelope)
    bind_blockers = _validate_session_go_auth_bindings_v1(
        authority=authority,
        pre_envelope=pre_payload,
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
    )
    if bind_blockers:
        result.blockers = sorted(set(blockers + bind_blockers))
        result.notes = notes + ["AUTHORIZATION_SESSION_GO_BINDING_FAILED=true"]
        _write_manifest(persistence, result)
        return result
    result.authorization_validated = True

    if ENTRYPOINT_SESSION_ID != TARGET_SESSION_ID:
        blockers.append("ENTRYPOINT_SESSION_ID_DRIFT")
        result.blockers = sorted(set(blockers))
        _write_manifest(persistence, result)
        return result

    consumed_before = load_consumed_authorization_ids_v1(ledger_path_for_root_v1(persistence))
    if str(pre_payload.get("authorization_id") or "") in consumed_before:
        blockers.append("AUTHORIZATION_ALREADY_CONSUMED_FAIL_CLOSED")
        result.blockers = sorted(set(blockers))
        result.notes = notes + ["DOUBLE_INVOCATION_OR_REPLAY_BLOCKED=true"]
        _write_manifest(persistence, result)
        return result

    runner = runtime_runner or run_offline_productive_restart_orchestration_v1

    def _counted_runner(**kwargs: Any) -> OrchestrationCampaignResultV1:
        runner_calls["count"] += 1
        if runner_calls["count"] > 1:
            raise PostUnlockInvocationError("DOUBLE_CANONICAL_RUNNER_INVOCATION_FORBIDDEN")
        return runner(**kwargs)

    campaign: Optional[OrchestrationCampaignResultV1] = None
    try:
        campaign = _counted_runner(
            persistence_root=persistence,
            repository_sha=repository_sha,
            pre_envelope=pre_payload,
            post_envelope_builder=post_envelope_builder,
            transport=transport,
            now_unix=now_unix,
            repo_root=root,
            open_position_present=open_position_present,
            applied_confirmation_ids=applied_confirmation_ids,
            candidate_observation_id=candidate_observation_id,
        )
    except Exception as exc:  # noqa: BLE001
        lock_present = lock_path_for_root_v1(persistence).is_file()
        result.canonical_runner_invoked = runner_calls["count"] >= 1
        result.canonical_runner_invocation_count = int(runner_calls["count"])
        result.session_lock_acquired = False
        result.session_lock_released = not lock_present
        result.blockers = sorted(set(blockers + [f"RUNNER_EXCEPTION:{type(exc).__name__}:{exc}"]))
        result.notes = notes + ["RUNNER_EXCEPTION_ABORT=true", "NO_BLIND_RETRY=true"]
        result.terminal_state = "ABORT"
        result.claims = {
            "POST_UNLOCK_RUNTIME_INVOCATION_ADDED": True,
            "CANONICAL_RUNTIME_RUNNER_REUSED": True,
            "PARALLEL_RUNNER_ADDED": False,
            "BLIND_RETRY_PERFORMED": False,
            "SESSION_LOCK_ABSENT_AFTER_EXCEPTION": bool(result.session_lock_released),
        }
        _write_manifest(persistence, result)
        return result

    consumed_after = load_consumed_authorization_ids_v1(ledger_path_for_root_v1(persistence))
    pre_auth_id = str(pre_payload.get("authorization_id") or "")
    auth_consumed = pre_auth_id in consumed_after and pre_auth_id not in consumed_before
    lock_present_after = lock_path_for_root_v1(persistence).is_file()

    result.canonical_runner_invoked = runner_calls["count"] == 1
    result.canonical_runner_invocation_count = int(runner_calls["count"])
    result.authorization_consumed = auth_consumed
    result.authorization_consumed_exactly_once = auth_consumed
    result.session_lock_acquired = True
    result.session_lock_released = not lock_present_after
    result.runtime_started = bool(campaign.runtime_started) if campaign else False
    result.network_session_started = bool(campaign.network_session_started) if campaign else False
    result.network_request_count = 0
    result.restart_recovery_completed = bool(
        campaign and campaign.ok and campaign.post is not None and campaign.post.ok
    )
    result.reconciliation_before_alpha = bool(
        campaign and campaign.post is not None and bool(campaign.post.reconciliation_before_alpha)
    )
    result.campaign = None if campaign is None else campaign.to_dict()
    result.claims = {
        "POST_UNLOCK_RUNTIME_INVOCATION_ADDED": True,
        "PRODUCTIVE_EXECUTE_MODE_EXPLICIT": True,
        "CANONICAL_RUNTIME_RUNNER_REUSED": True,
        "CANONICAL_WALLCLOCK_RUNNER_REFERENCED": True,
        "PARALLEL_RUNNER_ADDED": False,
        "SESSION_GO_BOUND": True,
        "AUTHORIZATION_SESSION_GO_BINDING": True,
        "AUTHORIZATION_CONSUME_BEFORE_SIDE_EFFECTS": True,
        "AUTHORIZATION_CONSUMED_EXACTLY_ONCE": bool(result.authorization_consumed_exactly_once),
        "SESSION_LOCK_ACQUIRE_BEFORE_NETWORK": True,
        "SESSION_LOCK_RELEASED": bool(result.session_lock_released),
        "RESTART_TRIGGER_BOUND_TO_CANONICAL_RUNTIME": True,
        "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART": bool(result.reconciliation_before_alpha),
        "NETWORK_SESSION_STARTED": False,
        "REAL_NETWORK_FORBIDDEN_IN_THIS_CAPABILITY": True,
        "NO_PERMANENT_UNSCOPED_ENABLE_FLAG": True,
    }
    if campaign is None or not campaign.ok:
        blockers.extend(list((campaign.blockers if campaign else []) or ["CAMPAIGN_FAILED"]))
        result.ok = False
        result.blockers = sorted(set(blockers))
        result.notes = notes + ["CAMPAIGN_FAIL_CLOSED=true"]
        result.terminal_state = "ABORT"
        _write_manifest(persistence, result)
        return result

    result.ok = (
        result.canonical_runner_invoked
        and result.authorization_consumed_exactly_once
        and result.session_lock_released
        and result.restart_recovery_completed
        and result.reconciliation_before_alpha
        and not result.network_session_started
    )
    result.blockers = []
    result.notes = notes + [
        "POST_UNLOCK_CANONICAL_RUNTIME_INVOCATION_COMPLETE=true",
        "NO_REAL_NETWORK=true",
        "NO_BLIND_RETRY=true",
    ]
    result.terminal_state = "PASS" if result.ok else "ABORT"
    if not result.ok:
        result.blockers.append("POST_UNLOCK_INVOCATION_INVARIANT_FAILED")
    _write_manifest(persistence, result)
    return result


def _write_manifest(persistence: Path, result: PostUnlockInvocationResultV1) -> None:
    write_json_atomic_v1(Path(persistence) / INVOCATION_MANIFEST_FILENAME, result.to_dict())
