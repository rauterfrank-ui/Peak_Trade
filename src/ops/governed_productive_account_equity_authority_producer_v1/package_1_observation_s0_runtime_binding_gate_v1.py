"""PACKAGE_1 Observation S0 runtime-binding gate.

Observation remains fail-closed until both a D4 runtime instance and a
D5 window binding are actually persisted. Does not execute observation.
Does not GET. Does not mint identity. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    BoundAccountIdentityRuntimeBindingError,
    inspect_bound_account_identity_runtime_binding_status_v1,
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    CheckpointObservationWindowBindingContractError,
    inspect_checkpoint_observation_window_binding_status_v1,
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    EXECUTION_READY,
    OBSERVATION_EXECUTED,
    OBSERVATION_EXECUTION_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT,
    D4_D5_GENESIS_RUNTIME_STORE_RELPATH,
)

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
S0_BLOCKED = "OBSERVATION_S0_BLOCKED_MISSING_D4_OR_D5_RUNTIME_PAYLOAD"
_REPO_ROOT = Path(__file__).resolve().parents[3]


def resolve_canonical_d4_d5_genesis_runtime_store_root_v1(
    *,
    repo_root: Path | str | None = None,
) -> Path | None:
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    base = root / D4_D5_GENESIS_RUNTIME_STORE_RELPATH
    if not base.exists():
        return None
    if (base / "d4_bound_account_identity_runtime_instance_v1.json").is_file() and (
        base / "d5_checkpoint_observation_window_binding_v1.json"
    ).is_file():
        return base
    candidates = sorted(path for path in base.iterdir() if path.is_dir())
    for candidate in reversed(candidates):
        if (candidate / "d4_bound_account_identity_runtime_instance_v1.json").is_file() and (
            candidate / "d5_checkpoint_observation_window_binding_v1.json"
        ).is_file():
            return candidate
    return None


class Package1ObservationS0RuntimeBindingGateError(ValueError):
    """Fail-closed PACKAGE_1 Observation S0 runtime-binding gate."""


@dataclass(frozen=True)
class Package1ObservationS0RuntimeBindingGateV1:
    d4_contract_status: str
    d4_runtime_instance_present: str
    d4_concrete_uid_corroborated: str
    d5_contract_status: str
    d5_runtime_instance_present: str
    observation_s0_runtime_payloads_present: str
    observation_executed: str
    observation_execution_authorized: str
    observation_execution_ready: str
    gate_status: str


def inspect_package_1_observation_s0_runtime_binding_gate_v1(
    *,
    store_root: Path | str | None = None,
) -> Package1ObservationS0RuntimeBindingGateV1:
    if OBSERVATION_EXECUTED is not False:
        raise Package1ObservationS0RuntimeBindingGateError("OBSERVATION_EXECUTED_MUST_REMAIN_FALSE")
    if OBSERVATION_EXECUTION_AUTHORIZED is not False:
        raise Package1ObservationS0RuntimeBindingGateError(
            "OBSERVATION_EXECUTION_AUTHORIZED_MUST_REMAIN_FALSE"
        )
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise Package1ObservationS0RuntimeBindingGateError(
            "OBSERVATION_NETWORK_GET_AUTHORIZED_MUST_REMAIN_FALSE"
        )
    if EXECUTION_READY is not False:
        raise Package1ObservationS0RuntimeBindingGateError("EXECUTION_READY_MUST_REMAIN_FALSE")
    if OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT is True:
        if store_root is None:
            store_root = resolve_canonical_d4_d5_genesis_runtime_store_root_v1()
            if store_root is None:
                raise Package1ObservationS0RuntimeBindingGateError(
                    "OBSERVATION_S0_RUNTIME_PAYLOADS_CLAIMED_BUT_ARTIFACT_ABSENT"
                )
    elif OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT is not False:
        raise Package1ObservationS0RuntimeBindingGateError(
            "OBSERVATION_S0_RUNTIME_PAYLOADS_MUST_REMAIN_ABSENT_WITHOUT_ARTIFACT"
        )
    d4_status = inspect_bound_account_identity_runtime_binding_status_v1(store_root=store_root)
    d5_status = inspect_checkpoint_observation_window_binding_status_v1(store_root=store_root)
    payloads_present = (
        d4_status.artifact_present == TRUE_TOKEN and d5_status.artifact_present == TRUE_TOKEN
    )
    if payloads_present:
        gate_status = "OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT_EXECUTION_STILL_UNAUTHORIZED"
    else:
        gate_status = S0_BLOCKED
    return Package1ObservationS0RuntimeBindingGateV1(
        d4_contract_status=d4_status.contract_status,
        d4_runtime_instance_present=d4_status.runtime_instance_present,
        d4_concrete_uid_corroborated=d4_status.concrete_uid_corroborated,
        d5_contract_status=d5_status.contract_status,
        d5_runtime_instance_present=d5_status.runtime_instance_present,
        observation_s0_runtime_payloads_present=(TRUE_TOKEN if payloads_present else FALSE_TOKEN),
        observation_executed=FALSE_TOKEN,
        observation_execution_authorized=FALSE_TOKEN,
        observation_execution_ready=FALSE_TOKEN,
        gate_status=gate_status,
    )


def assert_package_1_observation_s0_runtime_payloads_present_v1(
    *,
    store_root: Path | str | None,
) -> None:
    gate = inspect_package_1_observation_s0_runtime_binding_gate_v1(store_root=store_root)
    if gate.observation_s0_runtime_payloads_present != TRUE_TOKEN:
        raise Package1ObservationS0RuntimeBindingGateError(S0_BLOCKED)
    try:
        load_bound_account_identity_runtime_binding_v1(store_root=store_root)
        load_checkpoint_observation_window_binding_v1(store_root=store_root)
    except (
        BoundAccountIdentityRuntimeBindingError,
        CheckpointObservationWindowBindingContractError,
    ) as exc:
        raise Package1ObservationS0RuntimeBindingGateError(S0_BLOCKED) from exc
    if gate.observation_execution_authorized != FALSE_TOKEN:
        raise Package1ObservationS0RuntimeBindingGateError(
            "OBSERVATION_EXECUTION_AUTHORIZED_MUST_REMAIN_FALSE"
        )
    if gate.observation_executed != FALSE_TOKEN:
        raise Package1ObservationS0RuntimeBindingGateError("OBSERVATION_EXECUTED_MUST_REMAIN_FALSE")


def reject_package_1_observation_execution_without_runtime_payloads_v1(
    *,
    store_root: Path | str | None = None,
) -> None:
    gate = inspect_package_1_observation_s0_runtime_binding_gate_v1(store_root=store_root)
    if gate.observation_s0_runtime_payloads_present != TRUE_TOKEN:
        raise Package1ObservationS0RuntimeBindingGateError(S0_BLOCKED)
    raise Package1ObservationS0RuntimeBindingGateError("OBSERVATION_EXECUTION_UNAUTHORIZED")
