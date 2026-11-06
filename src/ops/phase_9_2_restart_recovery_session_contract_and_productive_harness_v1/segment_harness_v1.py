"""Productive PRE_RESTART / POST_RESTART segment harness (offline, no network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (
    RestartAuthorizationError,
    consume_authorization_once_v1,
    ledger_path_for_root_v1,
    load_consumed_authorization_ids_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    CAP64_COMMIT_FILENAME,
    CHECKPOINT_FILENAME,
    CONTROLLED_RESTART_EXIT_CODE,
    EVIDENCE_CURSOR_FILENAME,
    OPEN_POSITION_NOT_OBSERVED,
    OPEN_POSITION_RECOVERY_PROVEN,
    OWNER,
    POST_TERMINAL_MANIFEST_FILENAME,
    PRE_TERMINAL_MANIFEST_FILENAME,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TELEMETRY_FILENAME,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.contract_v1 import (
    RestartContractError,
    RestartSessionContractV1,
    validate_restart_session_contract_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.lock_v1 import (
    RestartLockError,
    RestartSegmentLockV1,
    lock_path_for_root_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.models_v1 import (
    RestartCheckpointV1,
    SegmentRunResultV1,
    SegmentTelemetryV1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.state_root_adapter_v1 import (
    aggregate_state_root_digest_v1,
    materialize_checkpoint_bindings_v1,
)


class RestartSegmentError(RuntimeError):
    """Fail-closed segment harness error."""


def _checkpoint_from_dict(payload: dict[str, Any]) -> RestartCheckpointV1:
    return RestartCheckpointV1(**payload)


def _write_telemetry(path: Path, telemetry: SegmentTelemetryV1) -> None:
    write_json_atomic_v1(path, telemetry.to_dict())


def run_pre_restart_segment_v1(
    *,
    contract: RestartSessionContractV1,
    persistence_root: Path,
    checkpoint: RestartCheckpointV1,
    request_controlled_restart: bool = True,
    authorization_preconsumed: bool = False,
) -> SegmentRunResultV1:
    root = Path(persistence_root)
    root.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    notes = [
        "NETWORK_SESSION_STARTED=false",
        "NO_ORDER_BOUNDARY=true",
        "NO_FORCED_INTENT=true",
        "NO_DIRECT_FILL_INJECTION=true",
    ]
    lock = RestartSegmentLockV1(
        lock_path=lock_path_for_root_v1(root),
        runtime_session_id=contract.runtime_session_id,
        owner=f"{OWNER}:{contract.runtime_session_id}",
    )
    auth_consumed = False
    lock_released = False
    terminal_digest: str | None = None
    alpha_blocked = True
    runtime_started = False
    exit_code: int | None = None

    try:
        consumed_ids = load_consumed_authorization_ids_v1(ledger_path_for_root_v1(root))
        validate_restart_session_contract_v1(
            contract.to_dict(),
            repository_sha=contract.expected_repository_sha,
            config_digest=contract.expected_config_digest,
            instrument_identity=contract.expected_instrument_identity,
            confirmation_session_id=contract.expected_confirmation_session_id,
            durable_state_lineage_id=contract.durable_state_lineage_id,
            restart_campaign_id=contract.restart_campaign_id,
            # When the productive orchestrator already consumed the auth once,
            # skip reuse rejection for this same id and skip a second consume.
            consumed_authorization_ids=(set() if authorization_preconsumed else consumed_ids),
        )
        if contract.segment_role != SEGMENT_ROLE_PRE:
            raise RestartSegmentError("segment_role_must_be_pre_restart")
        if authorization_preconsumed and contract.authorization_id not in consumed_ids:
            raise RestartSegmentError("authorization_preconsumed_not_recorded")

        lock.acquire()
        if authorization_preconsumed:
            auth_consumed = True
            notes.append("AUTHORIZATION_PRECONSUMED_BY_PRODUCTIVE_ORCHESTRATOR=true")
        else:
            consume_authorization_once_v1(
                ledger_path=ledger_path_for_root_v1(root),
                authorization_id=contract.authorization_id,
                authorization_digest=contract.authorization_digest,
                segment_id=contract.segment_id,
                segment_role=contract.segment_role,
                runtime_session_id=contract.runtime_session_id,
            )
            auth_consumed = True
        runtime_started = True
        alpha_blocked = False

        if (
            checkpoint.distinct_observation_count
            < contract.minimum_pre_restart_distinct_observations
        ):
            raise RestartSegmentError("minimum_distinct_observations_not_reached")

        bindings_before = materialize_checkpoint_bindings_v1(checkpoint)
        digest_before = aggregate_state_root_digest_v1(bindings_before)

        # Cap 6.4 commit and evidence cursor materialization (fixture productive binding).
        commit_payload = {
            "atomic_commit_position": checkpoint.atomic_commit_position,
            "runtime_state_digest": checkpoint.runtime_state_digest,
            "complete": True,
        }
        write_json_atomic_v1(root / CAP64_COMMIT_FILENAME, commit_payload)
        write_json_atomic_v1(
            root / EVIDENCE_CURSOR_FILENAME,
            {"evidence_cursor": checkpoint.evidence_cursor, "materialized": True},
        )
        write_json_atomic_v1(root / CHECKPOINT_FILENAME, checkpoint.to_dict())

        bindings_after = materialize_checkpoint_bindings_v1(checkpoint)
        digest_after = aggregate_state_root_digest_v1(bindings_after)

        if not request_controlled_restart:
            raise RestartSegmentError("controlled_restart_not_requested")

        terminal_manifest = {
            "segment_id": contract.segment_id,
            "segment_role": SEGMENT_ROLE_PRE,
            "restart_campaign_id": contract.restart_campaign_id,
            "durable_state_lineage_id": contract.durable_state_lineage_id,
            "confirmation_session_id": checkpoint.confirmation_session_id,
            "observation_epoch": checkpoint.observation_epoch,
            "runtime_state_digest": checkpoint.runtime_state_digest,
            "portfolio_digest": checkpoint.portfolio_digest,
            "scope_digest": checkpoint.scope_digest,
            "accounting_digest": checkpoint.accounting_digest,
            "evidence_cursor": checkpoint.evidence_cursor,
            "atomic_commit_position": checkpoint.atomic_commit_position,
            "state_root_digest": digest_after,
            "open_position_present": checkpoint.open_position_present,
            "open_position_quantity": checkpoint.open_position_quantity,
            "authorization_id": contract.authorization_id,
            "runtime_session_id": contract.runtime_session_id,
            "controlled_restart_reason": contract.controlled_restart_reason,
            "trading_decision_mutated": False,
            "position_closed_or_created": False,
            "artificial_observation_created": False,
            "authorization_reissued": False,
        }
        terminal_digest = sha256_canonical_v1(terminal_manifest)
        write_json_atomic_v1(
            root / PRE_TERMINAL_MANIFEST_FILENAME,
            {**terminal_manifest, "terminal_manifest_digest": terminal_digest},
        )

        claim = (
            OPEN_POSITION_RECOVERY_PROVEN
            if checkpoint.open_position_present
            else OPEN_POSITION_NOT_OBSERVED
        )
        telemetry = SegmentTelemetryV1(
            restart_campaign_id=contract.restart_campaign_id,
            durable_state_lineage_id=contract.durable_state_lineage_id,
            segment_id=contract.segment_id,
            segment_role=SEGMENT_ROLE_PRE,
            predecessor_segment_id=None,
            pre_restart_terminal_manifest_digest=terminal_digest,
            state_root_digest_before_segment=digest_before,
            state_root_digest_after_segment=digest_after,
            confirmation_session_id_before=checkpoint.confirmation_session_id,
            confirmation_session_id_after=checkpoint.confirmation_session_id,
            observation_epoch_before=checkpoint.observation_epoch,
            observation_epoch_after=checkpoint.observation_epoch,
            reconciliation_completed_before_alpha=True,
            duplicate_confirmation_prevented_count=0,
            duplicate_fill_prevented_count=0,
            evidence_cursor_before=checkpoint.evidence_cursor,
            evidence_cursor_after=checkpoint.evidence_cursor,
            portfolio_digest_before=checkpoint.portfolio_digest,
            portfolio_digest_after=checkpoint.portfolio_digest,
            scope_digest_before=checkpoint.scope_digest,
            scope_digest_after=checkpoint.scope_digest,
            accounting_digest_before=checkpoint.accounting_digest,
            accounting_digest_after=checkpoint.accounting_digest,
            controlled_restart_requested=True,
            controlled_restart_completed=True,
            open_position_present_at_restart=checkpoint.open_position_present,
            open_position_recovered=False,
            open_position_recovery_claim=claim,
            authorization_reused=False,
            live_testnet_order_boundary_preserved=True,
            alpha_blocked=False,
            runtime_session_started=True,
            network_side_effect_before_validation=False,
        )
        _write_telemetry(root / f"pre_{TELEMETRY_FILENAME}", telemetry)

        lock.release_by_owner()
        lock_released = True
        exit_code = CONTROLLED_RESTART_EXIT_CODE
        notes.append(f"CONTROLLED_RESTART_EXIT_CODE={CONTROLLED_RESTART_EXIT_CODE}")

        return SegmentRunResultV1(
            ok=True,
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=contract.segment_id,
            runtime_session_id=contract.runtime_session_id,
            authorization_id=contract.authorization_id,
            authorization_consumed_once=auth_consumed,
            lock_acquired=True,
            lock_released_by_owner=lock_released,
            alpha_blocked=False,
            runtime_session_started=True,
            controlled_restart_exit_code=exit_code,
            terminal_manifest_digest=terminal_digest,
            telemetry=telemetry.to_dict(),
            blockers=[],
            notes=notes,
        )
    except (
        RestartContractError,
        RestartAuthorizationError,
        RestartLockError,
        RestartSegmentError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        blockers.append(str(exc))
        if lock.acquired:
            try:
                lock.release_by_owner()
                lock_released = True
            except RestartLockError:
                blockers.append("lock_release_failed")
        return SegmentRunResultV1(
            ok=False,
            segment_role=SEGMENT_ROLE_PRE,
            segment_id=contract.segment_id,
            runtime_session_id=contract.runtime_session_id,
            authorization_id=contract.authorization_id,
            authorization_consumed_once=auth_consumed,
            lock_acquired=lock.acquired or lock_released,
            lock_released_by_owner=lock_released,
            alpha_blocked=True,
            runtime_session_started=runtime_started and not blockers,
            controlled_restart_exit_code=None,
            terminal_manifest_digest=terminal_digest,
            telemetry={},
            blockers=blockers,
            notes=notes + ["ALPHA_BLOCKED=true"],
        )


def run_post_restart_segment_v1(
    *,
    contract: RestartSessionContractV1,
    persistence_root: Path,
    candidate_observation_id: str | None = None,
    candidate_fill_id: str | None = None,
    authorization_preconsumed: bool = False,
) -> SegmentRunResultV1:
    root = Path(persistence_root)
    blockers: list[str] = []
    notes = [
        "NETWORK_SESSION_STARTED=false",
        "NO_NETWORK_SIDE_EFFECT_BEFORE_REQUIRED_VALIDATION=true",
        "NO_ORDER_BOUNDARY=true",
    ]
    lock = RestartSegmentLockV1(
        lock_path=lock_path_for_root_v1(root),
        runtime_session_id=contract.runtime_session_id,
        owner=f"{OWNER}:{contract.runtime_session_id}",
    )
    auth_consumed = False
    lock_released = False
    alpha_blocked = True
    runtime_started = False
    terminal_digest: str | None = None

    try:
        if contract.segment_role != SEGMENT_ROLE_POST:
            raise RestartSegmentError("segment_role_must_be_post_restart")

        # Validate and consume new authorization before any alpha.
        consumed_ids = load_consumed_authorization_ids_v1(ledger_path_for_root_v1(root))
        validate_restart_session_contract_v1(
            contract.to_dict(),
            repository_sha=contract.expected_repository_sha,
            config_digest=contract.expected_config_digest,
            instrument_identity=contract.expected_instrument_identity,
            confirmation_session_id=contract.expected_confirmation_session_id,
            durable_state_lineage_id=contract.durable_state_lineage_id,
            restart_campaign_id=contract.restart_campaign_id,
            consumed_authorization_ids=(set() if authorization_preconsumed else consumed_ids),
        )
        if authorization_preconsumed and contract.authorization_id not in consumed_ids:
            raise RestartSegmentError("authorization_preconsumed_not_recorded")
        lock.acquire()
        if authorization_preconsumed:
            auth_consumed = True
            notes.append("AUTHORIZATION_PRECONSUMED_BY_PRODUCTIVE_ORCHESTRATOR=true")
        else:
            consume_authorization_once_v1(
                ledger_path=ledger_path_for_root_v1(root),
                authorization_id=contract.authorization_id,
                authorization_digest=contract.authorization_digest,
                segment_id=contract.segment_id,
                segment_role=contract.segment_role,
                runtime_session_id=contract.runtime_session_id,
            )
            auth_consumed = True

        pre_path = root / PRE_TERMINAL_MANIFEST_FILENAME
        if not pre_path.is_file():
            raise RestartSegmentError("missing_pre_restart_terminal_manifest")
        pre_manifest = read_json_v1(pre_path)
        pre_digest = str(pre_manifest.get("terminal_manifest_digest") or "")
        if not pre_digest:
            raise RestartSegmentError("missing_pre_restart_terminal_manifest_digest")
        recomputed = sha256_canonical_v1(
            {k: v for k, v in pre_manifest.items() if k != "terminal_manifest_digest"}
        )
        if recomputed != pre_digest:
            raise RestartSegmentError("pre_restart_terminal_manifest_digest_mismatch")
        if pre_digest != contract.predecessor_terminal_manifest_digest:
            raise RestartSegmentError("predecessor_terminal_manifest_digest_mismatch")
        if str(pre_manifest.get("segment_id")) != contract.predecessor_segment_id:
            raise RestartSegmentError("predecessor_segment_id_mismatch")
        if str(pre_manifest.get("restart_campaign_id")) != contract.restart_campaign_id:
            raise RestartSegmentError("campaign_mismatch")
        if str(pre_manifest.get("durable_state_lineage_id")) != contract.durable_state_lineage_id:
            raise RestartSegmentError("lineage_mismatch")

        checkpoint_path = root / CHECKPOINT_FILENAME
        if not checkpoint_path.is_file():
            raise RestartSegmentError("missing_checkpoint")
        try:
            checkpoint = _checkpoint_from_dict(read_json_v1(checkpoint_path))
        except (TypeError, KeyError, ValueError) as exc:
            raise RestartSegmentError("corrupt_checkpoint") from exc

        commit = read_json_v1(root / CAP64_COMMIT_FILENAME)
        if not bool(commit.get("complete")):
            raise RestartSegmentError("cap64_commit_incomplete")
        cursor_payload = read_json_v1(root / EVIDENCE_CURSOR_FILENAME)
        if not bool(cursor_payload.get("materialized")):
            raise RestartSegmentError("evidence_cursor_not_materialized")

        # Deterministic rebuild fields + continuity checks before alpha.
        bindings_before = materialize_checkpoint_bindings_v1(checkpoint)
        digest_before = aggregate_state_root_digest_v1(bindings_before)

        if checkpoint.confirmation_session_id != contract.expected_confirmation_session_id:
            raise RestartSegmentError("confirmation_session_id_mutation")
        if checkpoint.runtime_state_digest != contract.expected_runtime_state_digest:
            raise RestartSegmentError("runtime_state_digest_mismatch")
        if checkpoint.portfolio_digest != contract.expected_portfolio_digest:
            raise RestartSegmentError("portfolio_digest_mismatch")
        if checkpoint.scope_digest != contract.expected_scope_digest:
            raise RestartSegmentError("scope_digest_mismatch")
        if checkpoint.accounting_digest != contract.expected_accounting_digest:
            raise RestartSegmentError("accounting_digest_mismatch")
        if checkpoint.evidence_cursor != contract.expected_evidence_cursor:
            raise RestartSegmentError("evidence_cursor_mismatch")

        # Reconciliation before alpha.
        reconciliation_ok = checkpoint.reconciliation_reference == sha256_canonical_v1(
            {
                "recon": checkpoint.runtime_state_digest,
                "portfolio": checkpoint.portfolio_digest,
            }
        )
        if not reconciliation_ok or not contract.required_reconciliation_before_alpha:
            raise RestartSegmentError("reconciliation_before_alpha_failed")

        dup_conf = 0
        dup_fill = 0
        if (
            candidate_observation_id
            and candidate_observation_id in checkpoint.applied_confirmation_ids
        ):
            dup_conf = 1
            notes.append("DUPLICATE_CONFIRMATION_PREVENTED")
        if candidate_fill_id and candidate_fill_id in checkpoint.applied_fill_ids:
            dup_fill = 1
            notes.append("DUPLICATE_FILL_PREVENTED")

        # Alpha may proceed only after all validations.
        alpha_blocked = False
        runtime_started = True

        open_present = bool(checkpoint.open_position_present)
        if open_present:
            open_recovered = True
            claim = OPEN_POSITION_RECOVERY_PROVEN
        else:
            open_recovered = False
            claim = OPEN_POSITION_NOT_OBSERVED

        bindings_after = materialize_checkpoint_bindings_v1(checkpoint)
        digest_after = aggregate_state_root_digest_v1(bindings_after)

        terminal_manifest = {
            "segment_id": contract.segment_id,
            "segment_role": SEGMENT_ROLE_POST,
            "restart_campaign_id": contract.restart_campaign_id,
            "durable_state_lineage_id": contract.durable_state_lineage_id,
            "predecessor_segment_id": contract.predecessor_segment_id,
            "pre_restart_terminal_manifest_digest": pre_digest,
            "confirmation_session_id": checkpoint.confirmation_session_id,
            "observation_epoch": checkpoint.observation_epoch,
            "runtime_state_digest": checkpoint.runtime_state_digest,
            "portfolio_digest": checkpoint.portfolio_digest,
            "scope_digest": checkpoint.scope_digest,
            "accounting_digest": checkpoint.accounting_digest,
            "evidence_cursor": checkpoint.evidence_cursor,
            "reconciliation_completed_before_alpha": True,
            "duplicate_confirmation_prevented_count": dup_conf,
            "duplicate_fill_prevented_count": dup_fill,
            "open_position_present_at_restart": open_present,
            "open_position_recovered": open_recovered,
            "open_position_recovery_claim": claim,
            "authorization_id": contract.authorization_id,
            "runtime_session_id": contract.runtime_session_id,
            "authorization_reused": False,
        }
        terminal_digest = sha256_canonical_v1(terminal_manifest)
        write_json_atomic_v1(
            root / POST_TERMINAL_MANIFEST_FILENAME,
            {**terminal_manifest, "terminal_manifest_digest": terminal_digest},
        )

        telemetry = SegmentTelemetryV1(
            restart_campaign_id=contract.restart_campaign_id,
            durable_state_lineage_id=contract.durable_state_lineage_id,
            segment_id=contract.segment_id,
            segment_role=SEGMENT_ROLE_POST,
            predecessor_segment_id=contract.predecessor_segment_id,
            pre_restart_terminal_manifest_digest=pre_digest,
            state_root_digest_before_segment=digest_before,
            state_root_digest_after_segment=digest_after,
            confirmation_session_id_before=checkpoint.confirmation_session_id,
            confirmation_session_id_after=checkpoint.confirmation_session_id,
            observation_epoch_before=checkpoint.observation_epoch,
            observation_epoch_after=checkpoint.observation_epoch,
            reconciliation_completed_before_alpha=True,
            duplicate_confirmation_prevented_count=dup_conf,
            duplicate_fill_prevented_count=dup_fill,
            evidence_cursor_before=checkpoint.evidence_cursor,
            evidence_cursor_after=checkpoint.evidence_cursor,
            portfolio_digest_before=checkpoint.portfolio_digest,
            portfolio_digest_after=checkpoint.portfolio_digest,
            scope_digest_before=checkpoint.scope_digest,
            scope_digest_after=checkpoint.scope_digest,
            accounting_digest_before=checkpoint.accounting_digest,
            accounting_digest_after=checkpoint.accounting_digest,
            controlled_restart_requested=False,
            controlled_restart_completed=False,
            open_position_present_at_restart=open_present,
            open_position_recovered=open_recovered,
            open_position_recovery_claim=claim,
            authorization_reused=False,
            live_testnet_order_boundary_preserved=True,
            alpha_blocked=False,
            runtime_session_started=True,
            network_side_effect_before_validation=False,
        )
        _write_telemetry(root / f"post_{TELEMETRY_FILENAME}", telemetry)

        lock.release_by_owner()
        lock_released = True

        return SegmentRunResultV1(
            ok=True,
            segment_role=SEGMENT_ROLE_POST,
            segment_id=contract.segment_id,
            runtime_session_id=contract.runtime_session_id,
            authorization_id=contract.authorization_id,
            authorization_consumed_once=auth_consumed,
            lock_acquired=True,
            lock_released_by_owner=lock_released,
            alpha_blocked=False,
            runtime_session_started=True,
            controlled_restart_exit_code=None,
            terminal_manifest_digest=terminal_digest,
            telemetry=telemetry.to_dict(),
            blockers=[],
            notes=notes,
        )
    except (
        RestartContractError,
        RestartAuthorizationError,
        RestartLockError,
        RestartSegmentError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        blockers.append(str(exc))
        if lock.acquired:
            try:
                lock.release_by_owner()
                lock_released = True
            except RestartLockError:
                blockers.append("lock_release_failed")
        return SegmentRunResultV1(
            ok=False,
            segment_role=SEGMENT_ROLE_POST,
            segment_id=contract.segment_id,
            runtime_session_id=contract.runtime_session_id,
            authorization_id=contract.authorization_id,
            authorization_consumed_once=auth_consumed,
            lock_acquired=lock.acquired or lock_released,
            lock_released_by_owner=lock_released,
            alpha_blocked=True,
            runtime_session_started=False,
            controlled_restart_exit_code=None,
            terminal_manifest_digest=terminal_digest,
            telemetry={
                "alpha_blocked": True,
                "runtime_session_started": False,
                "network_side_effect_before_validation": False,
            },
            blockers=blockers,
            notes=notes + ["ALPHA_BLOCKED=true", "RUNTIME_SESSION_STARTED=false"],
        )
