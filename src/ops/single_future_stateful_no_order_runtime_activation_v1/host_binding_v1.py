"""Productive host binding for Cap 7.2 activation (single stateful host)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.ops.single_future_stateful_no_order_runtime_activation_v1.activation_gate_v1 import (
    ActivationGateResultV1,
    run_activation_gate_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    OWNER,
    RUNTIME_MODE,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.models_v1 import (
    ActivationStatusV1,
    CanonicalActivationStateV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.persistence_v1 import (
    load_activation_state_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.reason_codes_v1 import (
    ActivationFailureCodeV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
    construct_simulated_execution_port_v1,
)


@dataclass
class HostActivationBindingV1:
    """Cap 7.2 activation binding on the productive wallclock host.

    When ``enabled`` is False (default), Cap 7.1 / prior hosts remain unchanged.
    When ``enabled`` is True, activation gate must pass before alpha.
    """

    enabled: bool = False
    initialized: bool = False
    state_root: Optional[str] = None
    config_path: Optional[str] = None
    repository_sha: str = ""
    config_digest: str = ""
    instrument_id: str = ""
    alpha_blocked: bool = False
    alpha_block_reason: str = ""
    full_canonical_stateful_runtime_active: bool = False
    simulated_execution_active: bool = False
    stateful_runtime_ready_for_activation: bool = False
    public_md_runtime_capable: bool = True
    public_md_network_session_observed: bool = False
    runtime_mode: str = RUNTIME_MODE
    last_gate: dict[str, Any] = field(default_factory=dict)
    execution_port: Optional[SimulatedExecutionPortV1] = None

    def to_canonical_state(self) -> CanonicalActivationStateV1 | None:
        loaded = None
        if self.state_root:
            loaded = load_activation_state_v1(Path(self.state_root), require_present=False)
        return loaded


def ensure_host_activation_binding_v1(
    binding: HostActivationBindingV1,
    *,
    instrument_id: str,
    repository_sha: str,
    state_root: Path | None,
    writer_session_id: str,
    config_path: Path | None = None,
    selected_future_present: bool = True,
    instrument_binding_valid: bool = True,
    reconciliation_ok: bool = True,
    persist: bool = True,
) -> ActivationGateResultV1:
    """Ensure Cap 7.2 activation on the productive host when enabled."""
    if not binding.enabled:
        # Legacy / Cap 7.1 path: no Cap 7.2 activation authority effect.
        binding.initialized = True
        binding.alpha_blocked = False
        binding.alpha_block_reason = ""
        binding.full_canonical_stateful_runtime_active = False
        binding.simulated_execution_active = False
        binding.stateful_runtime_ready_for_activation = False
        return ActivationGateResultV1(
            ok=True,
            alpha_enabled=True,
            alpha_blocked=False,
            blockers=[],
            claims={"CAP72_ACTIVATION_ENABLED": False},
        )

    if state_root is not None:
        binding.state_root = str(state_root)
    if config_path is not None:
        binding.config_path = str(config_path)
    binding.instrument_id = instrument_id
    binding.repository_sha = repository_sha

    # Restart: reload prior activation state before re-validating.
    if binding.state_root:
        prior = load_activation_state_v1(Path(binding.state_root), require_present=False)
        if prior is not None and prior.status == ActivationStatusV1.ACTIVE:
            # Restart must re-validate; corruption / mismatch fail closed.
            pass

    if binding.execution_port is None:
        binding.execution_port = construct_simulated_execution_port_v1()
    if not isinstance(binding.execution_port, SimulatedExecutionPortV1):
        raise RuntimeError(
            f"{ActivationFailureCodeV1.INVALID_EXECUTION_PORT.value}:non_simulated_port"
        )

    gate = run_activation_gate_v1(
        repository_sha=repository_sha,
        instrument_id=instrument_id,
        state_root=Path(binding.state_root) if binding.state_root else None,
        writer_session_id=writer_session_id,
        config_path=Path(binding.config_path) if binding.config_path else None,
        selected_future_present=selected_future_present,
        instrument_binding_valid=instrument_binding_valid,
        reconciliation_ok=reconciliation_ok,
        persist=persist,
    )
    binding.initialized = True
    binding.last_gate = gate.to_dict()
    binding.alpha_blocked = bool(gate.alpha_blocked)
    binding.alpha_block_reason = ",".join(gate.blockers)
    if gate.state is not None:
        binding.config_digest = gate.state.config_digest
        binding.full_canonical_stateful_runtime_active = bool(
            gate.state.full_canonical_stateful_runtime_active
        )
        binding.simulated_execution_active = bool(gate.state.simulated_execution_active)
        binding.stateful_runtime_ready_for_activation = bool(
            gate.state.stateful_runtime_ready_for_activation
        )
        binding.public_md_runtime_capable = bool(gate.state.public_md_runtime_capable)
        binding.public_md_network_session_observed = bool(
            gate.state.public_md_network_session_observed
        )
        binding.runtime_mode = gate.state.runtime_mode.value
    return gate


def host_simulated_execution_port_v1(
    binding: HostActivationBindingV1,
) -> SimulatedExecutionPortV1:
    """Return the sole constructible execution port for the no-order host."""
    if binding.execution_port is None:
        binding.execution_port = construct_simulated_execution_port_v1()
    if not isinstance(binding.execution_port, SimulatedExecutionPortV1):
        raise RuntimeError(ActivationFailureCodeV1.INVALID_EXECUTION_PORT.value)
    return binding.execution_port


def activation_status_snapshot_v1(binding: HostActivationBindingV1) -> dict[str, Any]:
    return {
        "owner": OWNER,
        "enabled": bool(binding.enabled),
        "runtime_mode": binding.runtime_mode,
        "STATEFUL_RUNTIME_READY_FOR_ACTIVATION": bool(
            binding.stateful_runtime_ready_for_activation
        ),
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": bool(
            binding.full_canonical_stateful_runtime_active
        ),
        "SIMULATED_EXECUTION_ACTIVE": bool(binding.simulated_execution_active),
        "PUBLIC_MD_RUNTIME_CAPABLE": bool(binding.public_md_runtime_capable),
        "PUBLIC_MD_NETWORK_SESSION_OBSERVED": bool(binding.public_md_network_session_observed),
        "ALPHA_BLOCKED": bool(binding.alpha_blocked),
        "alpha_block_reason": binding.alpha_block_reason,
        "LIVE_ORDERS": False,
        "TESTNET_ORDERS": False,
        "PAPER_EXCHANGE_ORDERS": False,
        "EXCHANGE_CREDENTIAL_USE": False,
        "REAL_CAPITAL_MOVEMENT": False,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
    }
