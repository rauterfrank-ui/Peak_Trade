"""Activation gate: integrity → no-order mode → activation state → alpha release."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    ActivationConfigError,
    load_activation_config_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    OWNER,
    PUBLIC_MD_NETWORK_SESSION_OBSERVED,
    RUNTIME_MODE,
    SINGLE_WRITER_IDENTITY,
    STATE_VERSION,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.models_v1 import (
    ActivationStatusV1,
    CanonicalActivationStateV1,
    RuntimeModeV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.persistence_v1 import (
    ActivationPersistenceError,
    load_activation_state_v1,
    persist_activation_state_atomic_v1,
    prior_commit_exists,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.reason_codes_v1 import (
    ActivationFailureCodeV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    prove_execution_port_separation_v1,
)


@dataclass
class ActivationGateResultV1:
    ok: bool
    alpha_enabled: bool
    alpha_blocked: bool
    blockers: list[str] = field(default_factory=list)
    state: Optional[CanonicalActivationStateV1] = None
    claims: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "alpha_enabled": bool(self.alpha_enabled),
            "alpha_blocked": bool(self.alpha_blocked),
            "blockers": list(self.blockers),
            "state": None if self.state is None else self.state.to_dict(),
            "claims": dict(self.claims),
            "owner": OWNER,
        }


def _inactive_state(
    *,
    repository_sha: str,
    config_digest: str,
    instrument_id: str,
    reason: str,
    failure_code: str = "",
) -> CanonicalActivationStateV1:
    return CanonicalActivationStateV1(
        state_version=STATE_VERSION,
        status=ActivationStatusV1.ROLLBACK_INACTIVE
        if failure_code
        else ActivationStatusV1.INACTIVE,
        runtime_mode=RuntimeModeV1(RUNTIME_MODE),
        repository_sha=repository_sha,
        config_digest=config_digest,
        instrument_id=instrument_id,
        writer_identity=SINGLE_WRITER_IDENTITY,
        commit_sequence=0,
        stateful_runtime_ready_for_activation=False,
        full_canonical_stateful_runtime_active=False,
        simulated_execution_active=False,
        public_md_runtime_capable=True,
        public_md_network_session_observed=False,
        alpha_blocked=True,
        alpha_block_reason=reason,
        exit_risk_safety_state_preserved=True,
        rollback_applied=bool(failure_code),
        last_failure_code=failure_code,
    )


def validate_no_order_mode_v1() -> list[str]:
    from src.ops.single_future_stateful_no_order_runtime_activation_v1.preconditions_v1 import (
        _read_bridge_authority_flags_from_source,
    )

    flags = _read_bridge_authority_flags_from_source()
    blockers: list[str] = []
    if (
        flags["ORDERS_AUTHORIZED"]
        or flags["LIVE_AUTHORIZED"]
        or flags["TESTNET_AUTHORIZED"]
        or flags["PAPER_EXECUTION_AUTHORIZED"]
    ):
        blockers.append(ActivationFailureCodeV1.NO_ORDER_MODE_VIOLATION.value)
    if flags["RUNTIME_BRIDGE_LIVE_ACTIVATED"]:
        blockers.append("RUNTIME_BRIDGE_LIVE_ACTIVATED")
    if PUBLIC_MD_NETWORK_SESSION_OBSERVED:
        blockers.append("PUBLIC_MD_NETWORK_SESSION_OBSERVED")
    return blockers


def run_activation_gate_v1(
    *,
    repository_sha: str,
    instrument_id: str,
    state_root: Path | None,
    writer_session_id: str,
    config_path: Path | None = None,
    require_selected_future: bool = True,
    selected_future_present: bool = True,
    instrument_binding_valid: bool = True,
    reconciliation_ok: bool = True,
    persist: bool = True,
    skip_preconditions: bool = False,
) -> ActivationGateResultV1:
    """Full Cap 7.2 activation attempt. Failures leave runtime inactive + alpha blocked."""
    blockers: list[str] = []
    try:
        cfg = load_activation_config_v1(config_path=config_path, require_active_claim=True)
    except ActivationConfigError as exc:
        state = _inactive_state(
            repository_sha=repository_sha,
            config_digest="",
            instrument_id=instrument_id,
            reason=str(exc),
            failure_code=exc.code.value,
        )
        return ActivationGateResultV1(
            ok=False, alpha_enabled=False, alpha_blocked=True, blockers=[str(exc)], state=state
        )

    # Config records the Cap 7.1 predecessor merge baseline; activation state binds the
    # live repository_sha. Mismatch vs persisted prior activation state is fail-closed.
    if not cfg.repository_sha_bound:
        blockers.append(ActivationFailureCodeV1.REPOSITORY_SHA_MISMATCH.value)
    blockers.extend(validate_no_order_mode_v1())
    if require_selected_future and not selected_future_present:
        blockers.append(ActivationFailureCodeV1.MISSING_SELECTED_FUTURE.value)
    if not instrument_binding_valid:
        blockers.append(ActivationFailureCodeV1.INVALID_INSTRUMENT_BINDING.value)
    if not reconciliation_ok:
        blockers.append(ActivationFailureCodeV1.RECONCILIATION_MISMATCH.value)

    port = prove_execution_port_separation_v1()
    if not port.get("ok"):
        blockers.append(ActivationFailureCodeV1.INVALID_EXECUTION_PORT.value)

    if not skip_preconditions:
        from src.ops.single_future_stateful_no_order_runtime_activation_v1.preconditions_v1 import (
            PreconditionGapError,
            prove_preconditions_v1,
        )

        try:
            prove_preconditions_v1(repository_sha=repository_sha)
        except PreconditionGapError as exc:
            blockers.append(str(exc))

    if state_root is not None and prior_commit_exists(state_root):
        try:
            prior = load_activation_state_v1(state_root, require_present=True)
        except ActivationPersistenceError as exc:
            blockers.append(str(exc))
            prior = None
        if prior is not None:
            if prior.config_digest and prior.config_digest != cfg.config_digest:
                blockers.append(ActivationFailureCodeV1.CONFIG_DIGEST_MISMATCH.value)
            if prior.repository_sha and prior.repository_sha != repository_sha:
                blockers.append(ActivationFailureCodeV1.REPOSITORY_SHA_MISMATCH.value)

    if blockers:
        state = _inactive_state(
            repository_sha=repository_sha,
            config_digest=cfg.config_digest,
            instrument_id=instrument_id,
            reason=",".join(blockers),
            failure_code=blockers[0],
        )
        if persist and state_root is not None:
            try:
                persist_activation_state_atomic_v1(
                    state_root, state, writer_session_id=writer_session_id
                )
            except Exception:  # noqa: BLE001
                pass
        return ActivationGateResultV1(
            ok=False,
            alpha_enabled=False,
            alpha_blocked=True,
            blockers=blockers,
            state=state,
            claims={
                "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": False,
                "ALPHA_BLOCKED": True,
                "EXIT_RISK_SAFETY_STATE_PRESERVED": True,
            },
        )

    seq = 1
    if state_root is not None:
        prior = load_activation_state_v1(state_root, require_present=False)
        if prior is not None:
            seq = int(prior.commit_sequence) + 1

    state = CanonicalActivationStateV1(
        state_version=STATE_VERSION,
        status=ActivationStatusV1.ACTIVE,
        runtime_mode=RuntimeModeV1(RUNTIME_MODE),
        repository_sha=repository_sha,
        config_digest=cfg.config_digest,
        instrument_id=instrument_id,
        writer_identity=SINGLE_WRITER_IDENTITY,
        commit_sequence=seq,
        stateful_runtime_ready_for_activation=True,
        full_canonical_stateful_runtime_active=True,
        simulated_execution_active=True,
        public_md_runtime_capable=True,
        public_md_network_session_observed=False,
        alpha_blocked=False,
        alpha_block_reason="",
        exit_risk_safety_state_preserved=True,
    )
    if persist and state_root is not None:
        try:
            persist_activation_state_atomic_v1(
                state_root, state, writer_session_id=writer_session_id
            )
        except ActivationPersistenceError as exc:
            failed = _inactive_state(
                repository_sha=repository_sha,
                config_digest=cfg.config_digest,
                instrument_id=instrument_id,
                reason=str(exc),
                failure_code=exc.code.value,
            )
            return ActivationGateResultV1(
                ok=False,
                alpha_enabled=False,
                alpha_blocked=True,
                blockers=[str(exc)],
                state=failed,
                claims={
                    "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": False,
                    "ALPHA_BLOCKED": True,
                    "EXIT_RISK_SAFETY_STATE_PRESERVED": True,
                },
            )

    return ActivationGateResultV1(
        ok=True,
        alpha_enabled=True,
        alpha_blocked=False,
        blockers=[],
        state=state,
        claims={
            "STATEFUL_RUNTIME_READY_FOR_ACTIVATION": True,
            "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": True,
            "SIMULATED_EXECUTION_ACTIVE": True,
            "PUBLIC_MD_RUNTIME_CAPABLE": True,
            "PUBLIC_MD_NETWORK_SESSION_OBSERVED": False,
            "ALPHA_BLOCKED": False,
        },
    )
