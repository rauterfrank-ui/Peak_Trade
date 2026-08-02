"""Host binding for Cap 6.4 atomic decision-path commit / restart recovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.decision_config_ownership_and_consumer_closure_v1.models_v1 import (
    DecisionConfigBindingStateV1,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.constants_v1 import (
    OWNER,
    STATE_VERSION,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.persistence_v1 import (
    DecisionPathAtomicPersistenceError,
    commit_decision_path_atomic_transaction_v1,
    load_commit_marker_v1,
    materialize_evidence_idempotent_v1,
    prior_commit_exists,
    recover_decision_path_atomic_v1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.reason_codes_v1 import (
    DecisionPathAtomicFailureCodeV1,
)
from src.ops.full_decision_path_atomic_restart_closure_v1.single_writer_v1 import (
    ConflictingWriterError,
    DecisionPathAtomicSingleWriterV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.models_v1 import (
    CanonicalConfirmationStateV1,
)


@dataclass
class HostDecisionPathAtomicBindingV1:
    enabled: bool = False
    initialized: bool = False
    state_root: Optional[str] = None
    repository_sha: str = ""
    config_digest: str = ""
    instrument_id: str = ""
    commit_sequence: int = 0
    commit_identity: str = ""
    prior_commit_seen: bool = False
    alpha_blocked: bool = False
    alpha_block_reason: str = ""
    last_commit: dict[str, Any] = field(default_factory=dict)
    last_recovery: dict[str, Any] = field(default_factory=dict)
    pending_evidence: dict[str, Any] = field(default_factory=dict)


def ensure_host_decision_path_atomic_binding_v1(
    binding: HostDecisionPathAtomicBindingV1,
    *,
    instrument_id: str,
    repository_sha: str,
    config_digest: str,
    state_root: Path | None,
) -> HostDecisionPathAtomicBindingV1:
    """Recover coordinator state before alpha; fail-closed on unrecoverable marker."""
    binding.enabled = True
    binding.instrument_id = instrument_id
    binding.repository_sha = repository_sha
    binding.config_digest = config_digest
    if state_root is None:
        binding.initialized = True
        return binding
    root = Path(state_root)
    binding.state_root = str(root)
    try:
        recovery = recover_decision_path_atomic_v1(
            coordinator_root=root,
            expected_repository_sha=repository_sha,
            expected_config_digest=config_digest,
        )
    except DecisionPathAtomicPersistenceError as exc:
        binding.alpha_blocked = True
        binding.alpha_block_reason = exc.code.value
        binding.initialized = True
        binding.prior_commit_seen = prior_commit_exists(root)
        raise
    binding.last_recovery = dict(recovery)
    binding.prior_commit_seen = bool(recovery.get("recovered"))
    if recovery.get("recovered"):
        binding.commit_identity = str(recovery.get("commit_identity") or "")
        binding.commit_sequence = int(recovery.get("commit_sequence") or 0)
        binding.pending_evidence = dict(recovery.get("pending_evidence") or {})
        # Drain pending evidence idempotently (does not alter runtime commit).
        if binding.pending_evidence and binding.pending_evidence.get("status") == "PENDING":
            drained = materialize_evidence_idempotent_v1(
                coordinator_root=root,
                evidence_payload={
                    "capability_id": OWNER,
                    "commit_identity": binding.commit_identity,
                    "recovery": True,
                },
                fail=False,
            )
            binding.pending_evidence = {
                "status": "MATERIALIZED" if drained.get("ok") else "PENDING",
                "drain": drained,
            }
    binding.initialized = True
    binding.alpha_blocked = False
    binding.alpha_block_reason = ""
    return binding


def commit_host_decision_path_atomic_v1(
    binding: HostDecisionPathAtomicBindingV1,
    *,
    confirmation_state: CanonicalConfirmationStateV1,
    confirmation_state_root: Path,
    dynamic_scope_state: CanonicalDynamicScopeStateV1 | None,
    dynamic_scope_state_root: Path | None,
    decision_config_state: DecisionConfigBindingStateV1 | None,
    decision_config_state_root: Path | None,
    accounting_session: ProductiveFuturesAccountingSessionV1 | None,
    accounting_state_root: Path | None,
    observation_epoch: int,
    fill_idempotency_key: str = "",
    writer_session_id: str | None = None,
    evidence_payload: Mapping[str, Any] | None = None,
    evidence_fail: bool = False,
    persist_scope: bool = True,
    persist_accounting: bool = True,
    persist_config: bool = True,
    interrupt_before_state_write: bool = False,
    interrupt_during_state_write: bool = False,
    interrupt_after_state_before_marker: bool = False,
    interrupt_after_runtime_before_evidence: bool = False,
    interrupt_after_fill_before_portfolio: bool = False,
    interrupt_after_portfolio_before_evidence_cursor: bool = False,
) -> Mapping[str, Any]:
    if binding.alpha_blocked:
        raise DecisionPathAtomicPersistenceError(
            DecisionPathAtomicFailureCodeV1.ALPHA_BLOCKED_ATOMIC_STATE_UNRECOVERABLE,
            binding.alpha_block_reason,
        )
    if not binding.state_root:
        raise RuntimeError("DECISION_PATH_ATOMIC_STATE_ROOT_REQUIRED")
    root = Path(binding.state_root)
    writer = DecisionPathAtomicSingleWriterV1(
        state_root=root,
        session_id=writer_session_id or f"cap64-{binding.instrument_id}",
        instrument_id=binding.instrument_id,
    )
    try:
        writer.acquire()
    except ConflictingWriterError:
        raise
    try:
        out = commit_decision_path_atomic_transaction_v1(
            coordinator_root=root,
            writer=writer,
            confirmation_state=confirmation_state,
            confirmation_state_root=Path(confirmation_state_root),
            dynamic_scope_state=dynamic_scope_state,
            dynamic_scope_state_root=(
                Path(dynamic_scope_state_root) if dynamic_scope_state_root is not None else None
            ),
            decision_config_state=decision_config_state,
            decision_config_state_root=(
                Path(decision_config_state_root) if decision_config_state_root is not None else None
            ),
            accounting_session=accounting_session,
            accounting_state_root=(
                Path(accounting_state_root) if accounting_state_root is not None else None
            ),
            repository_sha=binding.repository_sha,
            config_digest=binding.config_digest,
            instrument_id=binding.instrument_id,
            observation_epoch=int(observation_epoch),
            fill_idempotency_key=fill_idempotency_key,
            persist_scope=persist_scope,
            persist_accounting=persist_accounting,
            persist_config=persist_config,
            evidence_payload=evidence_payload,
            evidence_fail=evidence_fail,
            interrupt_before_state_write=interrupt_before_state_write,
            interrupt_during_state_write=interrupt_during_state_write,
            interrupt_after_state_before_marker=interrupt_after_state_before_marker,
            interrupt_after_runtime_before_evidence=interrupt_after_runtime_before_evidence,
            interrupt_after_fill_before_portfolio=interrupt_after_fill_before_portfolio,
            interrupt_after_portfolio_before_evidence_cursor=(
                interrupt_after_portfolio_before_evidence_cursor
            ),
        )
    finally:
        writer.release()
    binding.last_commit = dict(out)
    binding.commit_identity = str(out.get("commit_identity") or "")
    binding.commit_sequence = int(out.get("commit_sequence") or 0)
    binding.prior_commit_seen = True
    marker = load_commit_marker_v1(root)
    if marker is not None:
        binding.pending_evidence = {
            "evidence_status": marker.evidence_status,
            "commit_identity": marker.commit_identity,
        }
    return out
