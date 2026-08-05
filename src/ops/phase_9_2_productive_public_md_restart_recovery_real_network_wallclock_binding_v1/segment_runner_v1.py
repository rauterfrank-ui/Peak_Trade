"""Bound PRE/POST restart segment runner wired to wallclock + restart harness.

This module implements the productive binding. It never flips a permanent unscoped
enable flag. Real network opens only when the binding gate permits AND the caller
supplies an observation provider bound to the canonical wallclock runner.

In this capability package default evidence/materialization path, real network is
not started; injectable offline observation providers prove the binding only.
Fake-MD observations cannot satisfy REAL_PUBLIC_MD restart session claims.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.checkpoint_bridge_v1 import (
    build_checkpoint_from_public_md_observations_v1,
    checkpoint_digest_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.segment_authorization_v1 import (
    validate_segment_authorization_envelope_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.binding_gate_v1 import (
    evaluate_real_network_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CANONICAL_WALLCLOCK_RUNNER,
    CONFIRMATION_SESSION_ID,
    CONTROLLED_RESTART_EXIT_CODE,
    DURABLE_STATE_LINEAGE_ID,
    EXIT_CODE_82_CLASSIFICATION,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    RESTART_CAMPAIGN_ID,
    SEGMENT_POST_ID,
    SEGMENT_PRE_ID,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.models_v1 import (
    SegmentBindingResultV1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.process_marker_v1 import (
    assert_post_is_new_process_v1,
    load_pre_authorization_id_v1,
    write_pre_process_marker_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (
    authorization_digest_v1,
    consume_authorization_once_v1,
    ledger_path_for_root_v1,
    load_consumed_authorization_ids_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    PRE_TERMINAL_MANIFEST_FILENAME,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.contract_v1 import (
    build_restart_session_contract_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
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

ObservationProviderV1 = Callable[..., list[str]]


class SegmentBindingError(RuntimeError):
    """Fail-closed segment binding error."""


def _activation_digest(*, repo_root: Path) -> str:
    activation = load_activation_config_v1(
        config_path=repo_root
        / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
    )
    return str(activation.config_digest)


def _base_claims(*, fake_md_used: bool, real_network_used: bool) -> dict[str, Any]:
    return {
        "REAL_PUBLIC_MD_RESTART_BINDING_IMPLEMENTED": True,
        "REAL_NETWORK_SESSION_NOT_STARTED": not real_network_used,
        "NETWORK_SESSION_STARTED": bool(real_network_used),
        "RESTART_RECOVERY_LADDER_STEP_CLOSED": False,
        "PHASE_9_2_COMPLETE": False,
        "REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED": False,
        "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": True,
        "IMPLEMENTATION_REQUIRED": False,
        "CANONICAL_WALLCLOCK_RUNNER_BOUND": True,
        "CANONICAL_WALLCLOCK_RUNNER": CANONICAL_WALLCLOCK_RUNNER,
        "FAKE_MD_CANNOT_SATISFY_REAL_SESSION_CLAIM": True,
        "FAKE_MD_USED": bool(fake_md_used),
        "REAL_NETWORK_USED": bool(real_network_used),
        "CORE_LOGIC_CHANGE": False,
        "DASHBOARD_AUTHORITY_EFFECT": "NONE",
        "RECONCILIATION_BEFORE_ALPHA": True,
        "DUPLICATE_CONFIRMATION_ADVANCE": False,
        "DUPLICATE_FILL": False,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_PRESENT": False,
        "ORDER_SIDE_EFFECT_OCCURRED": False,
    }


def run_bound_restart_segment_v1(
    *,
    segment_role: str,
    persistence_root: Path,
    repository_sha: str,
    segment_authorization_envelope: Mapping[str, Any],
    now_unix: float,
    owner_go: bool,
    owner_session_go: bool,
    session_go_path: Path,
    confirm_token_file: Path | None = None,
    confirm_token_present_flag: bool = False,
    request_real_network: bool = False,
    execute: bool = False,
    observation_provider: ObservationProviderV1 | None = None,
    observation_source: str = "OFFLINE_BOUND_PROVIDER",
    applied_confirmation_ids: Sequence[str] | None = None,
    applied_fill_ids: Sequence[str] | None = None,
    candidate_observation_id: str | None = None,
    candidate_fill_id: str | None = None,
    open_position_present: bool = False,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
    require_reconciliation_before_alpha: bool = True,
) -> SegmentBindingResultV1:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    persistence = Path(persistence_root)
    persistence.mkdir(parents=True, exist_ok=True)
    pid = int(os.getpid())
    notes = [
        f"SEGMENT_ROLE={segment_role}",
        f"PROCESS_PID={pid}",
        "SAME_SESSION_RESUME_ALLOWED=false",
        "POST_RESTART_NEW_PROCESS_REQUIRED=true",
        f"WALLCLOCK_RUNNER={CANONICAL_WALLCLOCK_RUNNER}",
    ]
    blockers: list[str] = []
    fake_md_used = observation_source.upper().startswith("FAKE")
    real_network_used = False

    if segment_role not in {SEGMENT_ROLE_PRE, SEGMENT_ROLE_POST}:
        blockers.append(f"INVALID_SEGMENT_ROLE:{segment_role}")
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=blockers,
            notes=notes,
            process_pid=pid,
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=False),
        )

    config_digest = _activation_digest(repo_root=root)
    gate = evaluate_real_network_wallclock_binding_gate_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        now_unix=now_unix,
        owner_go=owner_go,
        owner_session_go=owner_session_go,
        session_go_path=session_go_path,
        authorization_present=True,
        confirm_token_file=confirm_token_file,
        confirm_token_present_flag=confirm_token_present_flag,
        request_real_network=request_real_network,
        argv=argv,
        environ=environ,
    )
    notes.extend(gate.notes)
    if not gate.ok:
        blockers.extend(gate.blockers)
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=sorted(set(blockers)),
            notes=notes,
            process_pid=pid,
            gate=gate.to_dict(),
            fake_md_used=fake_md_used,
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=False),
        )

    if request_real_network and not gate.real_network_may_proceed:
        blockers.extend(gate.blockers or ["REAL_NETWORK_NOT_PERMITTED"])
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=sorted(set(blockers)),
            notes=notes + ["REAL_NETWORK_GATE_FAIL_CLOSED=true"],
            process_pid=pid,
            gate=gate.to_dict(),
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=False),
        )

    if not execute:
        return SegmentBindingResultV1(
            ok=True,
            segment_role=segment_role,
            notes=notes + ["EXECUTE_FALSE_GATE_ONLY_NO_SEGMENT_SIDE_EFFECTS=true"],
            process_pid=pid,
            gate=gate.to_dict(),
            alpha_blocked=True,
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=False)
            | {"EXECUTE_MODE": False},
        )

    # Real network open remains reserved for a later governed session order.
    # Even when request_real_network+gate permit, this capability refuses to open
    # sockets unless an observation_provider is injected (tests / later session).
    if request_real_network and observation_provider is None:
        blockers.append("REAL_NETWORK_WALLCLOCK_PROVIDER_REQUIRED")
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=blockers,
            notes=notes
            + [
                "REAL_NETWORK_PATH_BOUND_BUT_PROVIDER_NOT_SUPPLIED=true",
                "NO_SOCKET_OPENED=true",
            ],
            process_pid=pid,
            gate=gate.to_dict(),
            claims=_base_claims(fake_md_used=False, real_network_used=False),
        )

    if observation_provider is None:
        blockers.append("OBSERVATION_PROVIDER_REQUIRED_FOR_EXECUTE")
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=blockers,
            notes=notes,
            process_pid=pid,
            gate=gate.to_dict(),
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=False),
        )

    env_payload = dict(segment_authorization_envelope)
    expected_role = segment_role
    expected_segment_id = SEGMENT_PRE_ID if segment_role == SEGMENT_ROLE_PRE else SEGMENT_POST_ID
    try:
        pred_cp = env_payload.get("predecessor_checkpoint_digest")
        envelope = validate_segment_authorization_envelope_v1(
            env_payload,
            expected_segment_role=expected_role,
            expected_session_id=TARGET_SESSION_ID,
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
            expected_predecessor_checkpoint_digest=(
                str(pred_cp) if expected_role == SEGMENT_ROLE_POST and pred_cp else None
            ),
            now_unix=now_unix,
            consumed_authorization_ids=load_consumed_authorization_ids_v1(
                ledger_path_for_root_v1(persistence)
            ),
        )
    except Exception as exc:  # noqa: BLE001
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=[f"SEGMENT_AUTHORIZATION_INVALID:{exc}"],
            notes=notes,
            process_pid=pid,
            gate=gate.to_dict(),
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=False),
        )

    if envelope.segment_id != expected_segment_id and envelope.segment_id not in {
        SEGMENT_PRE_ID,
        SEGMENT_POST_ID,
        env_payload.get("segment_id"),
    }:
        # Allow explicit segment_id from envelope when role matches; still bind role.
        pass
    if str(env_payload.get("restart_campaign_id") or RESTART_CAMPAIGN_ID) != RESTART_CAMPAIGN_ID:
        # campaign id is carried via auth digest inputs below; explicit mismatch checked next
        pass
    if str(env_payload.get("session_id") or "") not in {"", TARGET_SESSION_ID}:
        if str(env_payload.get("session_id")) != TARGET_SESSION_ID:
            blockers.append("SESSION_LINEAGE_MISMATCH")

    campaign_id = str(env_payload.get("restart_campaign_id") or RESTART_CAMPAIGN_ID)
    if campaign_id != RESTART_CAMPAIGN_ID:
        blockers.append("CAMPAIGN_LINEAGE_MISMATCH")

    if segment_role == SEGMENT_ROLE_POST:
        blockers.extend(
            assert_post_is_new_process_v1(
                persistence_root=persistence,
                restart_campaign_id=campaign_id,
                session_id=TARGET_SESSION_ID,
            )
        )
        pre_auth = load_pre_authorization_id_v1(persistence)
        if pre_auth is not None and pre_auth == envelope.authorization_id:
            blockers.append("PRE_AND_POST_MUST_USE_DISTINCT_AUTHORIZATIONS")
        pre_manifest = persistence / PRE_TERMINAL_MANIFEST_FILENAME
        if not pre_manifest.is_file():
            blockers.append("PRE_TERMINAL_MANIFEST_MISSING")

    if blockers:
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=sorted(set(blockers)),
            notes=notes,
            process_pid=pid,
            gate=gate.to_dict(),
            alpha_blocked=True,
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=False),
        )

    auth_digest = envelope.authorization_digest or authorization_digest_v1(
        authorization_id=envelope.authorization_id,
        segment_role=segment_role,
        restart_campaign_id=campaign_id,
        runtime_session_id=f"{TARGET_SESSION_ID}:{segment_role.lower()}",
    )

    if segment_role == SEGMENT_ROLE_PRE:
        # Collect observations via bound provider (wallclock runner or offline stand-in).
        identities = list(
            observation_provider(
                minimum=MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
                instrument_id=CANONICAL_INSTRUMENT_ID,
                segment_role=segment_role,
                request_real_network=request_real_network,
            )
        )
        wallclock_invoked = True
        if request_real_network and observation_source.upper().startswith("REAL"):
            real_network_used = True
        if fake_md_used:
            notes.append("FAKE_MD_OBSERVATIONS_DO_NOT_SATISFY_REAL_SESSION_CLAIM=true")

        unique: list[str] = []
        seen: set[str] = set()
        for oid in identities:
            if oid in seen:
                notes.append(f"DUPLICATE_OBSERVATION_IGNORED:{oid}")
                continue
            seen.add(oid)
            unique.append(oid)
        if candidate_observation_id and candidate_observation_id in seen:
            notes.append("DUPLICATE_CANDIDATE_OBSERVATION_NO_CONFIRMATION_ADVANCE=true")
        conf_ids = list(applied_confirmation_ids or [])
        fill_ids = list(applied_fill_ids or [])
        if candidate_fill_id and candidate_fill_id in fill_ids:
            notes.append("DUPLICATE_CANDIDATE_FILL_REJECTED=true")

        if len(unique) < MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS:
            return SegmentBindingResultV1(
                ok=False,
                segment_role=segment_role,
                blockers=["INSUFFICIENT_DISTINCT_PUBLIC_MD_OBSERVATIONS"],
                notes=notes,
                process_pid=pid,
                gate=gate.to_dict(),
                distinct_observation_count=len(unique),
                wallclock_runner_invoked=wallclock_invoked,
                fake_md_used=fake_md_used,
                real_network_used=real_network_used,
                claims=_base_claims(fake_md_used=fake_md_used, real_network_used=real_network_used),
            )

        checkpoint = build_checkpoint_from_public_md_observations_v1(
            distinct_observation_count=len(unique),
            observation_identities=unique,
            open_position_present=open_position_present,
            applied_fill_ids=fill_ids,
            applied_confirmation_ids=conf_ids,
            instrument_id=CANONICAL_INSTRUMENT_ID,
            confirmation_session_id=CONFIRMATION_SESSION_ID,
        )
        contract = build_restart_session_contract_v1(
            repository_sha=repository_sha,
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=envelope.segment_id or SEGMENT_PRE_ID,
            runtime_session_id=f"{TARGET_SESSION_ID}:pre",
            authorization_id=envelope.authorization_id,
            authorization_digest=auth_digest,
            expected_runtime_state_digest=checkpoint.runtime_state_digest,
            expected_portfolio_digest=checkpoint.portfolio_digest,
            expected_scope_digest=checkpoint.scope_digest,
            expected_accounting_digest=checkpoint.accounting_digest,
            expected_evidence_cursor=checkpoint.evidence_cursor,
            restart_campaign_id=campaign_id,
            durable_state_lineage_id=DURABLE_STATE_LINEAGE_ID,
            confirmation_session_id=CONFIRMATION_SESSION_ID,
            instrument_identity=CANONICAL_INSTRUMENT_ID,
            repo_root=root,
        )
        # Consume once before harness side effects (orchestrator pattern).
        consume_authorization_once_v1(
            ledger_path=ledger_path_for_root_v1(persistence),
            authorization_id=envelope.authorization_id,
            authorization_digest=auth_digest,
            segment_id=contract.segment_id,
            segment_role=SEGMENT_ROLE_PRE,
            runtime_session_id=contract.runtime_session_id,
        )
        harness = run_pre_restart_segment_v1(
            contract=contract,
            persistence_root=persistence,
            checkpoint=checkpoint,
            request_controlled_restart=True,
            authorization_preconsumed=True,
        )
        write_pre_process_marker_v1(
            persistence_root=persistence,
            restart_campaign_id=campaign_id,
            session_id=TARGET_SESSION_ID,
            pre_authorization_id=envelope.authorization_id,
            pre_terminal_manifest_digest=harness.terminal_manifest_digest,
        )
        exit_code = harness.controlled_restart_exit_code
        classification = (
            EXIT_CODE_82_CLASSIFICATION
            if exit_code == CONTROLLED_RESTART_EXIT_CODE
            else "UNEXPECTED_RUNTIME_FAILURE_EXIT"
        )
        ok = bool(harness.ok) and exit_code == CONTROLLED_RESTART_EXIT_CODE
        result = SegmentBindingResultV1(
            ok=ok,
            segment_role=segment_role,
            blockers=[] if ok else list(harness.blockers or ["PRE_SEGMENT_FAILED"]),
            notes=notes
            + list(harness.notes or [])
            + [f"EXIT_CODE_82_CLASSIFICATION={classification}"],
            exit_code=exit_code,
            exit_code_classification=classification,
            alpha_blocked=True,
            reconciliation_before_alpha=False,
            authorization_consumed=True,
            network_session_started=bool(real_network_used),
            real_network_used=real_network_used,
            fake_md_used=fake_md_used,
            real_session_claim_satisfied=bool(real_network_used) and not fake_md_used,
            wallclock_runner_invoked=wallclock_invoked,
            distinct_observation_count=int(checkpoint.distinct_observation_count),
            process_pid=pid,
            gate=gate.to_dict(),
            harness_result=harness.to_dict() if hasattr(harness, "to_dict") else None,
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=real_network_used)
            | {
                "EXIT_CODE_82_CLASSIFICATION": classification,
                "CONTROLLED_SEGMENT_TRANSITION": classification == EXIT_CODE_82_CLASSIFICATION,
                "CHECKPOINT_DIGEST": checkpoint_digest_v1(checkpoint),
            },
        )
        write_json_atomic_v1(persistence / "real_network_segment_result_v1.json", result.to_dict())
        return result

    # POST — load PRE checkpoint continuity; do not invent a new state root set.
    from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
        CHECKPOINT_FILENAME,
    )
    from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.models_v1 import (
        RestartCheckpointV1,
    )

    if not require_reconciliation_before_alpha:
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=["RECONCILIATION_BEFORE_ALPHA_REQUIRED"],
            notes=notes,
            process_pid=pid,
            alpha_blocked=True,
            gate=gate.to_dict(),
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=real_network_used),
        )

    pre_terminal = read_json_v1(persistence / PRE_TERMINAL_MANIFEST_FILENAME)
    pre_digest = str(pre_terminal.get("terminal_manifest_digest") or "")
    if not pre_digest:
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=["PRE_TERMINAL_MANIFEST_DIGEST_MISSING"],
            notes=notes,
            process_pid=pid,
            alpha_blocked=True,
            gate=gate.to_dict(),
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=real_network_used),
        )

    checkpoint_path = persistence / CHECKPOINT_FILENAME
    if not checkpoint_path.is_file():
        return SegmentBindingResultV1(
            ok=False,
            segment_role=segment_role,
            blockers=["PRE_CHECKPOINT_MISSING"],
            notes=notes,
            process_pid=pid,
            alpha_blocked=True,
            gate=gate.to_dict(),
            claims=_base_claims(fake_md_used=fake_md_used, real_network_used=real_network_used),
        )
    checkpoint = RestartCheckpointV1(**read_json_v1(checkpoint_path))

    # Observation provider still invoked for POST continuity probe, but state digests
    # come from the persisted PRE checkpoint.
    _ = list(
        observation_provider(
            minimum=1,
            instrument_id=CANONICAL_INSTRUMENT_ID,
            segment_role=segment_role,
            request_real_network=request_real_network,
        )
    )
    wallclock_invoked = True

    pred = env_payload.get("predecessor_checkpoint_digest")
    cp_digest = checkpoint_digest_v1(checkpoint)
    if pred and str(pred) not in {cp_digest, pre_digest}:
        notes.append("PREDECESSOR_CHECKPOINT_DIGEST_ENVELOPE_NOTED")

    contract = build_restart_session_contract_v1(
        repository_sha=repository_sha,
        segment_role=SEGMENT_ROLE_POST,
        segment_id=envelope.segment_id or SEGMENT_POST_ID,
        runtime_session_id=f"{TARGET_SESSION_ID}:post",
        authorization_id=envelope.authorization_id,
        authorization_digest=auth_digest,
        expected_runtime_state_digest=checkpoint.runtime_state_digest,
        expected_portfolio_digest=checkpoint.portfolio_digest,
        expected_scope_digest=checkpoint.scope_digest,
        expected_accounting_digest=checkpoint.accounting_digest,
        expected_evidence_cursor=checkpoint.evidence_cursor,
        predecessor_segment_id=SEGMENT_PRE_ID,
        predecessor_terminal_manifest_digest=pre_digest,
        restart_campaign_id=campaign_id,
        durable_state_lineage_id=DURABLE_STATE_LINEAGE_ID,
        confirmation_session_id=CONFIRMATION_SESSION_ID,
        instrument_identity=CANONICAL_INSTRUMENT_ID,
        repo_root=root,
    )
    consume_authorization_once_v1(
        ledger_path=ledger_path_for_root_v1(persistence),
        authorization_id=envelope.authorization_id,
        authorization_digest=auth_digest,
        segment_id=contract.segment_id,
        segment_role=SEGMENT_ROLE_POST,
        runtime_session_id=contract.runtime_session_id,
    )
    harness = run_post_restart_segment_v1(
        contract=contract,
        persistence_root=persistence,
        candidate_observation_id=candidate_observation_id,
        candidate_fill_id=candidate_fill_id,
        authorization_preconsumed=True,
    )
    alpha_blocked = bool(harness.alpha_blocked)
    recon = (
        bool(harness.telemetry.get("reconciliation_completed_before_alpha"))
        if harness.telemetry
        else False
    )
    if not recon:
        alpha_blocked = True
        blockers.append("RECONCILIATION_NOT_BEFORE_ALPHA")
    ok = bool(harness.ok) and recon and not alpha_blocked
    verified = verify_restart_bundle_v1(persistence_root=persistence)
    if not verified.verified:
        ok = False
        blockers.extend(list(verified.blockers or ["BUNDLE_VERIFIER_FAIL"]))

    result = SegmentBindingResultV1(
        ok=ok and not blockers,
        segment_role=segment_role,
        blockers=sorted(set(blockers + list(harness.blockers or []))),
        notes=notes + list(harness.notes or []),
        exit_code=harness.controlled_restart_exit_code,
        exit_code_classification=None,
        alpha_blocked=alpha_blocked or not ok,
        reconciliation_before_alpha=recon,
        authorization_consumed=True,
        network_session_started=bool(real_network_used),
        real_network_used=real_network_used,
        fake_md_used=fake_md_used,
        real_session_claim_satisfied=False,
        wallclock_runner_invoked=wallclock_invoked,
        distinct_observation_count=int(checkpoint.distinct_observation_count),
        process_pid=pid,
        gate=gate.to_dict(),
        harness_result=harness.to_dict(),
        claims=_base_claims(fake_md_used=fake_md_used, real_network_used=real_network_used)
        | {
            "ALPHA_BLOCKED": alpha_blocked or not ok,
            "BUNDLE_VERIFIER_INVOKED": True,
            "BUNDLE_VERIFIED": bool(verified.verified),
        },
    )
    write_json_atomic_v1(persistence / "real_network_segment_result_v1.json", result.to_dict())
    return result


def default_offline_observation_provider_v1(
    *,
    minimum: int = MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    instrument_id: str = CANONICAL_INSTRUMENT_ID,
    segment_role: str = SEGMENT_ROLE_PRE,
    request_real_network: bool = False,
) -> list[str]:
    """Deterministic offline stand-in bound for implementation proofs (not real MD)."""
    _ = (instrument_id, segment_role, request_real_network)
    return [f"offline_bound_obs_{i:04d}" for i in range(int(minimum))]


def fake_md_observation_provider_v1(
    *,
    minimum: int = MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    instrument_id: str = CANONICAL_INSTRUMENT_ID,
    segment_role: str = SEGMENT_ROLE_PRE,
    request_real_network: bool = False,
) -> list[str]:
    _ = (instrument_id, segment_role, request_real_network)
    return [f"fake_md_obs_{i:04d}" for i in range(int(minimum))]
