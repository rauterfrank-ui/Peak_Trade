"""Bounded Futures Testnet zero-order lifecycle integration (v0, PE-27).

Deterministic, offline, explicit-input-only contract binding a canonically verified
PE-26 preflight execution readiness assembly to the PE-12 zero_order lifecycle phase
and a canonical plan-only zero-order harness proof from archive_futures_testnet_harness_v0.

Static integration only — no harness execution, network, testnet, runtime, credentials,
orders, adapter calls, exchange queries, or authority lift.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_DESCRIPTORS,
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
    PreflightExecutionReadinessAssemblyInput,
    compute_assembly_input_digest,
    compute_assembly_result_digest,
    default_minimal_assembly_input,
    evaluate_preflight_execution_readiness_assembly_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_runtime_harness_contract_v0 import (
    ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW,
    ARCHIVE_HARNESS_SCRIPT_PRESENT,
    ARCHIVE_HARNESS_SCRIPT_REL_PATH,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_ZERO_ORDER_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_zero_order_lifecycle_integration.v0"
SERIALIZATION_VERSION = "bounded_futures_testnet_zero_order_lifecycle_integration.serialization.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

PE9_CONTRACT_VERSION = "bounded_futures_testnet_harness.v0"
PE10_CONTRACT_VERSION = "bounded_futures_testnet_runtime_harness.v0"
HARNESS_VERSION = "archive_futures_testnet_harness_v0"
HARNESS_MODE_ZERO_ORDER = "zero_order_reachability_only"
HARNESS_OWNER = ARCHIVE_HARNESS_SCRIPT_REL_PATH
PE26_ASSEMBLY_OWNER = PE26_CONTRACT_VERSION

GLOBAL_ZERO_ORDER_LIFECYCLE_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_HARNESS_EXECUTED = False
OPERATIVE_ADAPTER_CALLED = False
EXCHANGE_STATE_QUERIED = False
LIFECYCLE_TRANSITION_EXECUTED = False
NETWORK_RUN_STARTED = False
TESTNET_RUN_STARTED = False
RUNTIME_STARTED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe26_assembly": PE26_CONTRACT_VERSION,
    "pe9_harness": PE9_CONTRACT_VERSION,
    "pe10_runtime_harness": PE10_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe26_assembly: str
    pe9_harness: str
    pe10_runtime_harness: str
    integration: str


@dataclass(frozen=True)
class LifecycleMatrixProof:
    pe12_contract_version: str
    lifecycle_matrix_digest: str
    assigned_lifecycle_phase: str
    lifecycle_state_digest: str


@dataclass(frozen=True)
class Pe26AssemblyProofBinding:
    assembly_owner: str
    assembly_input_digest: str
    assembly_result_digest: str
    pe26_integration_pass: bool
    preflight_execution_readiness_assembly_complete: bool


@dataclass(frozen=True)
class HarnessZeroOrderProofBinding:
    harness_owner: str
    harness_version: str
    harness_mode: str
    plan_only: bool
    zero_order_plan_only_proven: bool
    harness_proof_digest: str
    request_count: int
    orders_created: int
    cancel_count: int
    position_mutation_count: int
    network_used: bool
    credentials_used: bool
    runtime_started: bool
    adapter_called: bool
    exchange_state_queried: bool


@dataclass(frozen=True)
class IntegrationSafetySnapshot:
    preflight_remains_blocked: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool
    zero_order_authorized: bool
    network_allowed: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class ZeroOrderLifecycleIntegrationInput:
    source_revision: str
    repository_identity: str
    adapter_id: str
    integration_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    lifecycle_matrix_proof: LifecycleMatrixProof
    pe26_assembly_input: PreflightExecutionReadinessAssemblyInput
    pe26_assembly_proof: Pe26AssemblyProofBinding
    harness_zero_order_proof: HarnessZeroOrderProofBinding
    safety_snapshot: IntegrationSafetySnapshot
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET
    non_authorizing: bool = True


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def compute_lifecycle_matrix_digest() -> str:
    """Deterministic digest of the canonical PE-12 lifecycle matrix identity."""
    matrix = {
        "hash_algorithm": HASH_ALGORITHM,
        "lifecycle_phase_order": list(LIFECYCLE_PHASE_ORDER),
        "network_execution_phases": sorted(NETWORK_EXECUTION_PHASES),
        "package_marker": PE12_PACKAGE_MARKER,
        "pe12_contract_version": PE12_CONTRACT_VERSION,
        "phase_descriptors": {
            phase_id: {
                "canonical_owner": descriptor.canonical_owner,
                "credentials_phase": descriptor.credentials_phase,
                "network_phase": descriptor.network_phase,
                "operator_go_token": descriptor.operator_go_token,
                "orders_phase": descriptor.orders_phase,
                "sequence_index": descriptor.sequence_index,
            }
            for phase_id, descriptor in sorted(LIFECYCLE_PHASE_DESCRIPTORS.items())
        },
    }
    return hashlib.sha256(
        json.dumps(matrix, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _integration_input_dict(
    integration_input: ZeroOrderLifecycleIntegrationInput,
) -> dict[str, Any]:
    return {
        "integration_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": integration_input.source_revision,
        "repository_identity": integration_input.repository_identity,
        "adapter_id": integration_input.adapter_id,
        "integration_id": integration_input.integration_id,
        "instrument": integration_input.instrument,
        "market_type": integration_input.market_type,
        "contract_versions": asdict(integration_input.contract_versions),
        "lifecycle_matrix_proof": asdict(integration_input.lifecycle_matrix_proof),
        "pe26_assembly_input_digest": compute_assembly_input_digest(
            integration_input.pe26_assembly_input
        ),
        "pe26_assembly_proof": asdict(integration_input.pe26_assembly_proof),
        "harness_zero_order_proof": asdict(integration_input.harness_zero_order_proof),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: ZeroOrderLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: ZeroOrderLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _harness_proof_dict(binding: HarnessZeroOrderProofBinding) -> dict[str, Any]:
    return {
        "adapter_called": binding.adapter_called,
        "cancel_count": binding.cancel_count,
        "credentials_used": binding.credentials_used,
        "exchange_state_queried": binding.exchange_state_queried,
        "harness_mode": binding.harness_mode,
        "harness_owner": binding.harness_owner,
        "harness_version": binding.harness_version,
        "network_used": binding.network_used,
        "orders_created": binding.orders_created,
        "plan_only": binding.plan_only,
        "position_mutation_count": binding.position_mutation_count,
        "request_count": binding.request_count,
        "runtime_started": binding.runtime_started,
        "zero_order_plan_only_proven": binding.zero_order_plan_only_proven,
    }


def serialize_harness_proof_canonical(binding: HarnessZeroOrderProofBinding) -> str:
    return json.dumps(_harness_proof_dict(binding), sort_keys=True, separators=(",", ":"))


def compute_harness_proof_digest(binding: HarnessZeroOrderProofBinding) -> str:
    return hashlib.sha256(serialize_harness_proof_canonical(binding).encode("utf-8")).hexdigest()


def _integration_result_dict(
    integration_input: ZeroOrderLifecycleIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
    zero_order_lifecycle_eligibility: bool = False,
) -> dict[str, Any]:
    matrix = integration_input.lifecycle_matrix_proof
    harness = integration_input.harness_zero_order_proof
    payload: dict[str, Any] = {
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "source_revision": integration_input.source_revision,
        "adapter_id": integration_input.adapter_id,
        "integration_id": integration_input.integration_id,
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "pe26_assembly_input_digest": compute_assembly_input_digest(
            integration_input.pe26_assembly_input
        ),
        "pe26_assembly_result_digest": integration_input.pe26_assembly_proof.assembly_result_digest,
        "harness_proof_digest": harness.harness_proof_digest,
        "harness_owner": harness.harness_owner,
        "zero_order_lifecycle_eligibility": zero_order_lifecycle_eligibility,
        "pe27_zero_order_lifecycle_static_integration_proven": zero_order_lifecycle_eligibility,
        "global_zero_order_lifecycle_readiness": GLOBAL_ZERO_ORDER_LIFECYCLE_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_harness_executed": OPERATIVE_HARNESS_EXECUTED,
        "operative_adapter_called": OPERATIVE_ADAPTER_CALLED,
        "exchange_state_queried": EXCHANGE_STATE_QUERIED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "runtime_started": RUNTIME_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "non_authorizing": True,
    }
    if integration_proof_digest is not None:
        payload["integration_proof_digest"] = integration_proof_digest
    return payload


def serialize_integration_result_canonical(
    integration_input: ZeroOrderLifecycleIntegrationInput,
    *,
    zero_order_lifecycle_eligibility: bool = False,
) -> str:
    return json.dumps(
        _integration_result_dict(
            integration_input,
            zero_order_lifecycle_eligibility=zero_order_lifecycle_eligibility,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: ZeroOrderLifecycleIntegrationInput,
    *,
    zero_order_lifecycle_eligibility: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_integration_result_canonical(
            integration_input,
            zero_order_lifecycle_eligibility=zero_order_lifecycle_eligibility,
        ).encode("utf-8")
    ).hexdigest()


def _validate_instrument_scope(instrument: str, market_type: str) -> list[str]:
    fail_reasons: list[str] = []
    if market_type != DEFAULT_MARKET_TYPE:
        fail_reasons.append(f"market_type must be {DEFAULT_MARKET_TYPE!r}")
    if not instrument:
        fail_reasons.append("instrument required")
    if instrument in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS:
        fail_reasons.append(f"instrument {instrument!r} is a rejected futures placeholder")
    if instrument in SPOT_INSTRUMENTS:
        fail_reasons.append(f"instrument {instrument!r} is a spot instrument")
    for fragment in _FORBIDDEN_INSTRUMENT_FRAGMENTS:
        if fragment in instrument:
            fail_reasons.append(f"instrument {instrument!r} has forbidden orientation {fragment!r}")
    return fail_reasons


def _validate_safety_snapshot(snapshot: IntegrationSafetySnapshot) -> list[str]:
    fail_reasons: list[str] = []
    required_bools = (
        ("preflight_remains_blocked", True),
        ("ready_for_operator_arming", False),
        ("execution_authorized", False),
        ("live_authorized", False),
        ("zero_order_authorized", False),
        ("network_allowed", False),
        ("credentials_allowed", False),
        ("orders_allowed", False),
        ("scheduler_runtime_allowed", False),
        ("futures_only", True),
        ("bitcoin_direction_allowed", False),
    )
    for field_name, expected in required_bools:
        actual = getattr(snapshot, field_name)
        if actual is not expected:
            fail_reasons.append(f"safety_snapshot: {field_name} must be {expected}")
    if snapshot.followup_run_gate != FOLLOWUP_RUN_GATE:
        fail_reasons.append(f"safety_snapshot: followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")
    return fail_reasons


def _validate_pe26_assembly_proof(
    integration_input: ZeroOrderLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe26_assembly_proof
    assembly_input = integration_input.pe26_assembly_input

    if proof.assembly_owner != PE26_ASSEMBLY_OWNER:
        fail_reasons.append(f"pe26_assembly_proof: assembly_owner must be {PE26_ASSEMBLY_OWNER!r}")
    if not proof.assembly_input_digest:
        fail_reasons.append("pe26_assembly_proof: assembly_input_digest required")
    elif not _valid_sha256_digest(proof.assembly_input_digest):
        fail_reasons.append(
            "pe26_assembly_proof: assembly_input_digest must be 64-char lowercase sha256 hex"
        )
    elif proof.assembly_input_digest != compute_assembly_input_digest(assembly_input):
        fail_reasons.append("pe26_assembly_proof: assembly_input_digest mismatch")

    if not proof.assembly_result_digest:
        fail_reasons.append("pe26_assembly_proof: assembly_result_digest required")
    elif not _valid_sha256_digest(proof.assembly_result_digest):
        fail_reasons.append(
            "pe26_assembly_proof: assembly_result_digest must be 64-char lowercase sha256 hex"
        )
    else:
        expected_result_digest = compute_assembly_result_digest(
            assembly_input,
            preflight_execution_readiness_assembly_complete=True,
        )
        if proof.assembly_result_digest != expected_result_digest:
            fail_reasons.append("pe26_assembly_proof: assembly_result_digest mismatch")

    if proof.pe26_integration_pass is not True:
        fail_reasons.append("pe26_assembly_proof: pe26_integration_pass must be true")
    if proof.preflight_execution_readiness_assembly_complete is not True:
        fail_reasons.append(
            "pe26_assembly_proof: preflight_execution_readiness_assembly_complete must be true"
        )

    pe26_result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input
    )
    if not pe26_result["integration_pass"]:
        fail_reasons.append("pe26_assembly_input: PE-26 assembly evaluation failed")
        fail_reasons.extend(
            f"pe26_assembly_input: {reason}" for reason in pe26_result["fail_reasons"]
        )
    elif not pe26_result["preflight_execution_readiness_assembly_complete"]:
        fail_reasons.append(
            "pe26_assembly_input: preflight_execution_readiness_assembly_complete required"
        )

    if assembly_input.source_revision != integration_input.source_revision:
        fail_reasons.append("pe26_assembly_input: source_revision mismatch")
    if assembly_input.adapter_id != integration_input.adapter_id:
        fail_reasons.append("pe26_assembly_input: adapter_id mismatch")
    if assembly_input.instrument != integration_input.instrument:
        fail_reasons.append("pe26_assembly_input: instrument mismatch")
    if assembly_input.market_type != integration_input.market_type:
        fail_reasons.append("pe26_assembly_input: market_type mismatch")
    if assembly_input.non_authorizing is not True:
        fail_reasons.append("pe26_assembly_input: non_authorizing must be true")

    return fail_reasons


def _validate_harness_zero_order_proof(binding: HarnessZeroOrderProofBinding) -> list[str]:
    fail_reasons: list[str] = []
    canonical_owner = PHASE_CANONICAL_OWNERS[PHASE_ZERO_ORDER]

    if binding.harness_owner != HARNESS_OWNER:
        fail_reasons.append(f"harness_zero_order_proof: harness_owner must be {HARNESS_OWNER!r}")
    if binding.harness_owner != canonical_owner:
        fail_reasons.append(
            f"harness_zero_order_proof: harness_owner must match PE-12 canonical owner "
            f"{canonical_owner!r}"
        )
    if binding.harness_version != HARNESS_VERSION:
        fail_reasons.append(
            f"harness_zero_order_proof: harness_version must be {HARNESS_VERSION!r}"
        )
    if binding.harness_mode != HARNESS_MODE_ZERO_ORDER:
        fail_reasons.append(
            f"harness_zero_order_proof: harness_mode must be {HARNESS_MODE_ZERO_ORDER!r}"
        )
    if binding.plan_only is not True:
        fail_reasons.append("harness_zero_order_proof: plan_only must be true")
    if binding.zero_order_plan_only_proven is not True:
        fail_reasons.append("harness_zero_order_proof: zero_order_plan_only_proven must be true")
    if binding.request_count != 0:
        fail_reasons.append("harness_zero_order_proof: request_count must be 0")
    if binding.orders_created != 0:
        fail_reasons.append("harness_zero_order_proof: orders_created must be 0")
    if binding.cancel_count != 0:
        fail_reasons.append("harness_zero_order_proof: cancel_count must be 0")
    if binding.position_mutation_count != 0:
        fail_reasons.append("harness_zero_order_proof: position_mutation_count must be 0")
    if binding.network_used is not False:
        fail_reasons.append("harness_zero_order_proof: network_used must be false")
    if binding.credentials_used is not False:
        fail_reasons.append("harness_zero_order_proof: credentials_used must be false")
    if binding.runtime_started is not False:
        fail_reasons.append("harness_zero_order_proof: runtime_started must be false")
    if binding.adapter_called is not False:
        fail_reasons.append("harness_zero_order_proof: adapter_called must be false")
    if binding.exchange_state_queried is not False:
        fail_reasons.append("harness_zero_order_proof: exchange_state_queried must be false")

    if not binding.harness_proof_digest:
        fail_reasons.append("harness_zero_order_proof: harness_proof_digest required")
    elif not _valid_sha256_digest(binding.harness_proof_digest):
        fail_reasons.append(
            "harness_zero_order_proof: harness_proof_digest must be 64-char lowercase sha256 hex"
        )
    elif binding.harness_proof_digest != compute_harness_proof_digest(binding):
        fail_reasons.append("harness_zero_order_proof: harness_proof_digest mismatch")

    if not ARCHIVE_HARNESS_SCRIPT_PRESENT:
        fail_reasons.append("ARCHIVE_HARNESS_SCRIPT_PRESENT must be true")
    if ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW:
        fail_reasons.append("ARCHIVE_HARNESS_SCRIPT_EXECUTE_AUTHORIZED_NOW must be false")

    return fail_reasons


def validate_zero_order_lifecycle_integration_input(
    integration_input: ZeroOrderLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-27 integration input bindings."""
    fail_reasons: list[str] = []

    if not integration_input.source_revision:
        fail_reasons.append("source_revision required")
    elif not _valid_commit_sha(integration_input.source_revision):
        fail_reasons.append("source_revision must be full 40-char lowercase commit SHA")
    if not integration_input.repository_identity:
        fail_reasons.append("repository_identity required")
    elif integration_input.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository_identity must be {REPOSITORY_IDENTITY!r}")
    if not integration_input.adapter_id:
        fail_reasons.append("adapter_id required")
    if not integration_input.integration_id:
        fail_reasons.append("integration_id required")

    fail_reasons.extend(
        _validate_instrument_scope(integration_input.instrument, integration_input.market_type)
    )

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        actual = getattr(integration_input.contract_versions, field_name)
        if not actual:
            fail_reasons.append(f"contract_versions: {field_name} required")
        elif actual != expected:
            fail_reasons.append(
                f"contract_versions: {field_name} must be {expected!r}, got {actual!r}"
            )

    matrix = integration_input.lifecycle_matrix_proof
    if matrix.pe12_contract_version != PE12_CONTRACT_VERSION:
        fail_reasons.append(
            f"lifecycle_matrix_proof: pe12_contract_version must be {PE12_CONTRACT_VERSION!r}"
        )
    if not matrix.lifecycle_matrix_digest:
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest required")
    elif matrix.lifecycle_matrix_digest != compute_lifecycle_matrix_digest():
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest mismatch")
    if not matrix.lifecycle_state_digest:
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_state_digest required")
    elif not _valid_sha256_digest(matrix.lifecycle_state_digest):
        fail_reasons.append(
            "lifecycle_matrix_proof: lifecycle_state_digest must be 64-char lowercase sha256 hex"
        )
    if matrix.assigned_lifecycle_phase != PHASE_ZERO_ORDER:
        fail_reasons.append(
            f"lifecycle_matrix_proof: assigned_lifecycle_phase must be {PHASE_ZERO_ORDER!r}"
        )
    elif matrix.assigned_lifecycle_phase not in LIFECYCLE_PHASE_DESCRIPTORS:
        fail_reasons.append("lifecycle_matrix_proof: unsupported lifecycle phase")

    fail_reasons.extend(_validate_pe26_assembly_proof(integration_input))
    fail_reasons.extend(
        _validate_harness_zero_order_proof(integration_input.harness_zero_order_proof)
    )
    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    harness_owner = integration_input.harness_zero_order_proof.harness_owner
    zero_order_owner = (
        integration_input.pe26_assembly_input.zero_order_capability_proof.capability_owner
    )
    if zero_order_owner != harness_owner:
        fail_reasons.append(
            "zero_order_capability_proof: capability_owner must match harness_owner"
        )

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _validate_zero_order_lifecycle_compatibility(
    integration_input: ZeroOrderLifecycleIntegrationInput,
) -> list[str]:
    """Static declarative compatibility for PE-12 zero_order phase gates."""
    fail_reasons: list[str] = []
    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[PHASE_ZERO_ORDER]
    snapshot = integration_input.safety_snapshot
    harness = integration_input.harness_zero_order_proof

    if descriptor.orders_phase and snapshot.orders_allowed:
        fail_reasons.append("lifecycle/gate contradiction: orders_allowed true for zero_order")
    if descriptor.credentials_phase and snapshot.credentials_allowed:
        fail_reasons.append("lifecycle/gate contradiction: credentials_allowed true for zero_order")
    if snapshot.execution_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: execution_authorized true for zero_order"
        )
    if snapshot.live_authorized:
        fail_reasons.append("lifecycle/gate contradiction: live_authorized true for zero_order")
    if snapshot.zero_order_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: zero_order_authorized true for zero_order"
        )
    if snapshot.network_allowed and harness.network_used:
        fail_reasons.append("lifecycle/gate contradiction: network_used with network_allowed")
    if harness.network_used:
        fail_reasons.append("plan-only zero_order harness proof requires network_used false")
    if not harness.plan_only or not harness.zero_order_plan_only_proven:
        fail_reasons.append("plan-only zero_order harness proof not established")

    return fail_reasons


def evaluate_zero_order_lifecycle_integration(
    integration_input: ZeroOrderLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    expected_assembly_input_digest: str | None = None,
    expected_assembly_result_digest: str | None = None,
    expected_harness_proof_digest: str | None = None,
    loose_boolean_eligibility: bool = False,
    execution_authorized: bool = False,
    live_authorized: bool = False,
    zero_order_authorized: bool = False,
    network_allowed: bool = False,
    credentials_allowed: bool = False,
    orders_allowed: bool = False,
    runtime_started: bool = False,
    adapter_called: bool = False,
    exchange_state_queried_override: bool = False,
    unknown_lifecycle_state: str | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-27 zero-order lifecycle static integration proof."""
    fail_reasons = validate_zero_order_lifecycle_integration_input(integration_input)

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    matrix = integration_input.lifecycle_matrix_proof
    if expected_lifecycle_state_digest is not None:
        if matrix.lifecycle_state_digest != expected_lifecycle_state_digest:
            fail_reasons.append("lifecycle_state_digest mismatch")

    if expected_assembly_input_digest is not None:
        computed = compute_assembly_input_digest(integration_input.pe26_assembly_input)
        if computed != expected_assembly_input_digest:
            fail_reasons.append("pe26_assembly_proof: assembly_input_digest mismatch")

    if expected_assembly_result_digest is not None:
        if (
            integration_input.pe26_assembly_proof.assembly_result_digest
            != expected_assembly_result_digest
        ):
            fail_reasons.append("pe26_assembly_proof: assembly_result_digest mismatch")

    if expected_harness_proof_digest is not None:
        if (
            integration_input.harness_zero_order_proof.harness_proof_digest
            != expected_harness_proof_digest
        ):
            fail_reasons.append("harness_zero_order_proof: harness_proof_digest mismatch")

    if loose_boolean_eligibility:
        fail_reasons.append(
            "loose_boolean_eligibility=true without canonical proof is insufficient"
        )
    if execution_authorized:
        fail_reasons.append("execution_authorized=true without authority lift is forbidden")
    if live_authorized:
        fail_reasons.append("live_authorized=true without authority lift is forbidden")
    if zero_order_authorized:
        fail_reasons.append("zero_order_authorized=true without authority lift is forbidden")
    if network_allowed:
        fail_reasons.append("network_allowed=true without authority lift is forbidden")
    if credentials_allowed:
        fail_reasons.append("credentials_allowed=true without authority lift is forbidden")
    if orders_allowed:
        fail_reasons.append("orders_allowed=true without authority lift is forbidden")
    if runtime_started:
        fail_reasons.append("runtime_started=true without runtime execution is forbidden")
    if adapter_called:
        fail_reasons.append("adapter_called=true without adapter execution is forbidden")
    if exchange_state_queried_override:
        fail_reasons.append("exchange_state_queried=true without query proof is forbidden")

    if unknown_lifecycle_state is not None:
        if unknown_lifecycle_state not in LIFECYCLE_PHASE_DESCRIPTORS:
            fail_reasons.append(f"unknown lifecycle state: {unknown_lifecycle_state!r}")

    if not fail_reasons:
        fail_reasons.extend(_validate_zero_order_lifecycle_compatibility(integration_input))

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    zero_order_lifecycle_eligibility = integration_pass

    harness = integration_input.harness_zero_order_proof
    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(
                integration_input,
                zero_order_lifecycle_eligibility=zero_order_lifecycle_eligibility,
            )
            if integration_pass
            else None
        ),
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "pe26_assembly_input_digest": compute_assembly_input_digest(
            integration_input.pe26_assembly_input
        ),
        "pe26_assembly_result_digest": integration_input.pe26_assembly_proof.assembly_result_digest,
        "harness_proof_digest": harness.harness_proof_digest,
        "harness_owner": harness.harness_owner,
        "zero_order_lifecycle_eligibility": zero_order_lifecycle_eligibility,
        "pe27_zero_order_lifecycle_static_integration_proven": zero_order_lifecycle_eligibility,
        "global_zero_order_lifecycle_readiness": GLOBAL_ZERO_ORDER_LIFECYCLE_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_harness_executed": OPERATIVE_HARNESS_EXECUTED,
        "operative_adapter_called": OPERATIVE_ADAPTER_CALLED,
        "exchange_state_queried": EXCHANGE_STATE_QUERIED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "runtime_started": RUNTIME_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": True,
        "ready_for_operator_arming": False,
        "execution_authorized": False,
        "live_authorized": False,
        "zero_order_authorized": False,
        "pilot_start_authorized": False,
        "promotion_authorized": False,
        "operator_closure_authorized": False,
        "operator_decision_authorized": False,
        "network_allowed": False,
        "credentials_allowed": False,
        "orders_allowed": False,
        "scheduler_runtime_allowed": False,
        "network_used": False,
        "credentials_used": False,
        "orders_created": 0,
        "cancels_created": 0,
        "positions_changed": 0,
        "adapter_called": False,
        "fail_reasons": fail_reasons,
    }


def default_minimal_harness_zero_order_proof(
    *,
    harness_proof_digest: str | None = None,
) -> HarnessZeroOrderProofBinding:
    binding = HarnessZeroOrderProofBinding(
        harness_owner=HARNESS_OWNER,
        harness_version=HARNESS_VERSION,
        harness_mode=HARNESS_MODE_ZERO_ORDER,
        plan_only=True,
        zero_order_plan_only_proven=True,
        harness_proof_digest="",
        request_count=0,
        orders_created=0,
        cancel_count=0,
        position_mutation_count=0,
        network_used=False,
        credentials_used=False,
        runtime_started=False,
        adapter_called=False,
        exchange_state_queried=False,
    )
    digest = harness_proof_digest or compute_harness_proof_digest(binding)
    return HarnessZeroOrderProofBinding(
        harness_owner=binding.harness_owner,
        harness_version=binding.harness_version,
        harness_mode=binding.harness_mode,
        plan_only=binding.plan_only,
        zero_order_plan_only_proven=binding.zero_order_plan_only_proven,
        harness_proof_digest=digest,
        request_count=binding.request_count,
        orders_created=binding.orders_created,
        cancel_count=binding.cancel_count,
        position_mutation_count=binding.position_mutation_count,
        network_used=binding.network_used,
        credentials_used=binding.credentials_used,
        runtime_started=binding.runtime_started,
        adapter_called=binding.adapter_called,
        exchange_state_queried=binding.exchange_state_queried,
    )


def default_minimal_safety_snapshot() -> IntegrationSafetySnapshot:
    return IntegrationSafetySnapshot(
        preflight_remains_blocked=True,
        ready_for_operator_arming=False,
        execution_authorized=False,
        live_authorized=False,
        zero_order_authorized=False,
        network_allowed=False,
        credentials_allowed=False,
        orders_allowed=False,
        scheduler_runtime_allowed=False,
        futures_only=True,
        bitcoin_direction_allowed=False,
        followup_run_gate=FOLLOWUP_RUN_GATE,
    )


def default_minimal_pe26_assembly_proof(
    assembly_input: PreflightExecutionReadinessAssemblyInput,
) -> Pe26AssemblyProofBinding:
    return Pe26AssemblyProofBinding(
        assembly_owner=PE26_ASSEMBLY_OWNER,
        assembly_input_digest=compute_assembly_input_digest(assembly_input),
        assembly_result_digest=compute_assembly_result_digest(
            assembly_input,
            preflight_execution_readiness_assembly_complete=True,
        ),
        pe26_integration_pass=True,
        preflight_execution_readiness_assembly_complete=True,
    )


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    integration_id: str = "zero-order-lifecycle-integration-001",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> ZeroOrderLifecycleIntegrationInput:
    """Minimal valid futures-generic PE-27 integration input for offline tests."""
    state_digest = lifecycle_state_digest or "e" * 64
    matrix_digest = compute_lifecycle_matrix_digest()
    assembly_input = default_minimal_assembly_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=state_digest,
    )
    harness_proof = default_minimal_harness_zero_order_proof()

    return ZeroOrderLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        integration_id=integration_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe26_assembly=PE26_CONTRACT_VERSION,
            pe9_harness=PE9_CONTRACT_VERSION,
            pe10_runtime_harness=PE10_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=matrix_digest,
            assigned_lifecycle_phase=PHASE_ZERO_ORDER,
            lifecycle_state_digest=state_digest,
        ),
        pe26_assembly_input=assembly_input,
        pe26_assembly_proof=default_minimal_pe26_assembly_proof(assembly_input),
        harness_zero_order_proof=harness_proof,
        safety_snapshot=default_minimal_safety_snapshot(),
    )
