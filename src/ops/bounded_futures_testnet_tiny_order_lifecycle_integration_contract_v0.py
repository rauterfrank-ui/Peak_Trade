"""Bounded Futures Testnet tiny-order lifecycle integration (v0, PE-30).

Deterministic, offline, explicit-input-only contract binding a canonically verified
PE-26 preflight execution readiness assembly, PE-27 zero-order lifecycle integration,
PE-28 private-readonly lifecycle integration, PE-29 validate-only lifecycle integration,
and a canonical static tiny-order plan proof from bounded_futures_testnet_contract_v0
to the PE-12 tiny_order lifecycle phase.

Static integration only — no network, testnet, runtime, credentials, orders, adapter calls,
exchange queries, tiny-order execution, or authority lift.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, replace
from typing import Any

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_DESCRIPTORS,
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
    PHASE_TINY_ORDER,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    FUTURES_SESSION_AUTHORIZED_NOW,
    PACKAGE_MARKER as TESTNET_PACKAGE_MARKER,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
    default_bounded_futures_normal_v0_spec,
    evaluate_bounded_futures_testnet_evidence,
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
from src.ops.bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE28_CONTRACT_VERSION,
    PrivateReadonlyLifecycleIntegrationInput,
    compute_integration_input_digest as compute_pe28_integration_input_digest,
    compute_integration_proof_digest as compute_pe28_integration_proof_digest,
    default_minimal_integration_input as default_minimal_pe28_integration_input,
    evaluate_private_readonly_lifecycle_integration,
)

from src.ops.bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE29_CONTRACT_VERSION,
    ValidateOnlyLifecycleIntegrationInput,
    compute_integration_input_digest as compute_pe29_integration_input_digest,
    compute_integration_proof_digest as compute_pe29_integration_proof_digest,
    default_minimal_integration_input as default_minimal_pe29_integration_input,
    evaluate_validate_only_lifecycle_integration,
)

from src.ops.bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE27_CONTRACT_VERSION,
    ZeroOrderLifecycleIntegrationInput,
    compute_integration_input_digest as compute_pe27_integration_input_digest,
    compute_integration_proof_digest as compute_pe27_integration_proof_digest,
    default_minimal_integration_input as default_minimal_pe27_integration_input,
    evaluate_zero_order_lifecycle_integration,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_TINY_ORDER_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_tiny_order_lifecycle_integration.v0"
SERIALIZATION_VERSION = "bounded_futures_testnet_tiny_order_lifecycle_integration.serialization.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

TESTNET_CONTRACT_VERSION = "bounded_futures_testnet.v0"
TINY_ORDER_MODE = "tiny_order_static_plan_binding_only"
TINY_ORDER_OWNER = PHASE_CANONICAL_OWNERS[PHASE_TINY_ORDER]
PE26_ASSEMBLY_OWNER = PE26_CONTRACT_VERSION
PE27_INTEGRATION_OWNER = PE27_CONTRACT_VERSION
PE28_INTEGRATION_OWNER = PE28_CONTRACT_VERSION
PE29_INTEGRATION_OWNER = PE29_CONTRACT_VERSION

GLOBAL_TINY_ORDER_LIFECYCLE_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_TINY_ORDER_EXECUTED = False
OPERATIVE_ADAPTER_CALLED = False
EXCHANGE_API_CALLED = False
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
    "pe27_zero_order": PE27_CONTRACT_VERSION,
    "pe28_private_readonly": PE28_CONTRACT_VERSION,
    "pe29_validate_only": PE29_CONTRACT_VERSION,
    "pe8_testnet_contract": TESTNET_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe26_assembly: str
    pe27_zero_order: str
    pe28_private_readonly: str
    pe29_validate_only: str
    pe8_testnet_contract: str
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
class Pe27ZeroOrderIntegrationProofBinding:
    integration_owner: str
    integration_input_digest: str
    integration_proof_digest: str
    pe27_integration_pass: bool
    zero_order_lifecycle_eligibility: bool


@dataclass(frozen=True)
class Pe28PrivateReadonlyIntegrationProofBinding:
    integration_owner: str
    integration_input_digest: str
    integration_proof_digest: str
    pe28_integration_pass: bool
    private_readonly_lifecycle_eligibility: bool


@dataclass(frozen=True)
class Pe29ValidateOnlyIntegrationProofBinding:
    integration_owner: str
    integration_input_digest: str
    integration_proof_digest: str
    pe29_integration_pass: bool
    validate_only_lifecycle_eligibility: bool


@dataclass(frozen=True)
class TinyOrderProofBinding:
    tiny_order_owner: str
    testnet_contract_version: str
    tiny_order_mode: str
    plan_only: bool
    tiny_order_plan_static_proven: bool
    tiny_order_static_plan_capability: bool
    plan_notional_eur: float
    plan_quantity: float
    plan_price: float
    tiny_order_proof_digest: str
    request_count: int
    exchange_request_count: int
    orders_created: int
    orders_cancelled: int
    orders_amended: int
    positions_changed: int
    network_used: bool
    credentials_used: bool
    secret_material_read: bool
    secret_material_stored: bool
    exchange_api_called: bool
    account_state_queried: bool
    adapter_called: bool
    runtime_started: bool
    testnet_started: bool
    harness_started: bool
    subprocess_started: bool
    trading_capability: bool
    order_capability: bool
    cancel_capability: bool
    amend_capability: bool
    flatten_capability: bool
    transfer_capability: bool
    withdrawal_capability: bool
    deposit_capability: bool


@dataclass(frozen=True)
class IntegrationSafetySnapshot:
    preflight_remains_blocked: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool
    zero_order_authorized: bool
    private_readonly_authorized: bool
    validate_only_authorized: bool
    tiny_order_authorized: bool
    network_allowed: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class TinyOrderLifecycleIntegrationInput:
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
    pe27_zero_order_integration_input: ZeroOrderLifecycleIntegrationInput
    pe27_zero_order_integration_proof: Pe27ZeroOrderIntegrationProofBinding
    pe28_private_readonly_integration_input: PrivateReadonlyLifecycleIntegrationInput
    pe28_private_readonly_integration_proof: Pe28PrivateReadonlyIntegrationProofBinding
    pe29_validate_only_integration_input: ValidateOnlyLifecycleIntegrationInput
    pe29_validate_only_integration_proof: Pe29ValidateOnlyIntegrationProofBinding
    tiny_order_proof: TinyOrderProofBinding
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
    integration_input: TinyOrderLifecycleIntegrationInput,
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
        "pe27_zero_order_integration_input_digest": compute_pe27_integration_input_digest(
            integration_input.pe27_zero_order_integration_input
        ),
        "pe27_zero_order_integration_proof": asdict(
            integration_input.pe27_zero_order_integration_proof
        ),
        "pe28_private_readonly_integration_input_digest": compute_pe28_integration_input_digest(
            integration_input.pe28_private_readonly_integration_input
        ),
        "pe28_private_readonly_integration_proof": asdict(
            integration_input.pe28_private_readonly_integration_proof
        ),
        "pe29_validate_only_integration_input_digest": compute_pe29_integration_input_digest(
            integration_input.pe29_validate_only_integration_input
        ),
        "pe29_validate_only_integration_proof": asdict(
            integration_input.pe29_validate_only_integration_proof
        ),
        "tiny_order_proof": asdict(integration_input.tiny_order_proof),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: TinyOrderLifecycleIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: TinyOrderLifecycleIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _tiny_order_proof_dict(binding: TinyOrderProofBinding) -> dict[str, Any]:
    return {
        "account_state_queried": binding.account_state_queried,
        "adapter_called": binding.adapter_called,
        "amend_capability": binding.amend_capability,
        "cancel_capability": binding.cancel_capability,
        "credentials_used": binding.credentials_used,
        "deposit_capability": binding.deposit_capability,
        "exchange_api_called": binding.exchange_api_called,
        "exchange_request_count": binding.exchange_request_count,
        "flatten_capability": binding.flatten_capability,
        "network_used": binding.network_used,
        "order_capability": binding.order_capability,
        "orders_amended": binding.orders_amended,
        "orders_cancelled": binding.orders_cancelled,
        "orders_created": binding.orders_created,
        "plan_notional_eur": binding.plan_notional_eur,
        "plan_price": binding.plan_price,
        "plan_quantity": binding.plan_quantity,
        "plan_only": binding.plan_only,
        "positions_changed": binding.positions_changed,
        "request_count": binding.request_count,
        "runtime_started": binding.runtime_started,
        "testnet_started": binding.testnet_started,
        "harness_started": binding.harness_started,
        "subprocess_started": binding.subprocess_started,
        "secret_material_read": binding.secret_material_read,
        "secret_material_stored": binding.secret_material_stored,
        "tiny_order_static_plan_capability": binding.tiny_order_static_plan_capability,
        "testnet_contract_version": binding.testnet_contract_version,
        "trading_capability": binding.trading_capability,
        "transfer_capability": binding.transfer_capability,
        "tiny_order_mode": binding.tiny_order_mode,
        "tiny_order_owner": binding.tiny_order_owner,
        "tiny_order_plan_static_proven": binding.tiny_order_plan_static_proven,
        "withdrawal_capability": binding.withdrawal_capability,
    }


def serialize_tiny_order_proof_canonical(binding: TinyOrderProofBinding) -> str:
    return json.dumps(_tiny_order_proof_dict(binding), sort_keys=True, separators=(",", ":"))


def compute_tiny_order_proof_digest(binding: TinyOrderProofBinding) -> str:
    return hashlib.sha256(serialize_tiny_order_proof_canonical(binding).encode("utf-8")).hexdigest()


def _integration_result_dict(
    integration_input: TinyOrderLifecycleIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
    tiny_order_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> dict[str, Any]:
    matrix = integration_input.lifecycle_matrix_proof
    proof = integration_input.tiny_order_proof
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
        "pe27_integration_input_digest": integration_input.pe27_zero_order_integration_proof.integration_input_digest,
        "pe27_integration_proof_digest": integration_input.pe27_zero_order_integration_proof.integration_proof_digest,
        "pe28_integration_input_digest": integration_input.pe28_private_readonly_integration_proof.integration_input_digest,
        "pe28_integration_proof_digest": integration_input.pe28_private_readonly_integration_proof.integration_proof_digest,
        "pe29_integration_proof_digest": integration_input.pe29_validate_only_integration_proof.integration_proof_digest,
        "tiny_order_proof_digest": proof.tiny_order_proof_digest,
        "tiny_order_owner": proof.tiny_order_owner,
        "tiny_order_lifecycle_eligibility_for_separate_operator_review": tiny_order_lifecycle_eligibility_for_separate_operator_review,
        "pe30_tiny_order_lifecycle_static_integration_proven": (
            tiny_order_lifecycle_eligibility_for_separate_operator_review
        ),
        "global_tiny_order_lifecycle_readiness": GLOBAL_TINY_ORDER_LIFECYCLE_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_tiny_order_executed": OPERATIVE_TINY_ORDER_EXECUTED,
        "operative_adapter_called": OPERATIVE_ADAPTER_CALLED,
        "exchange_api_called": EXCHANGE_API_CALLED,
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
    integration_input: TinyOrderLifecycleIntegrationInput,
    *,
    tiny_order_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> str:
    return json.dumps(
        _integration_result_dict(
            integration_input,
            tiny_order_lifecycle_eligibility_for_separate_operator_review=tiny_order_lifecycle_eligibility_for_separate_operator_review,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: TinyOrderLifecycleIntegrationInput,
    *,
    tiny_order_lifecycle_eligibility_for_separate_operator_review: bool = False,
) -> str:
    return hashlib.sha256(
        serialize_integration_result_canonical(
            integration_input,
            tiny_order_lifecycle_eligibility_for_separate_operator_review=tiny_order_lifecycle_eligibility_for_separate_operator_review,
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
        ("private_readonly_authorized", False),
        ("validate_only_authorized", False),
        ("tiny_order_authorized", False),
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
    integration_input: TinyOrderLifecycleIntegrationInput,
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


def _validate_pe27_integration_proof(
    integration_input: TinyOrderLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe27_zero_order_integration_proof
    pe27_input = integration_input.pe27_zero_order_integration_input

    if proof.integration_owner != PE27_INTEGRATION_OWNER:
        fail_reasons.append(
            f"pe27_zero_order_integration_proof: integration_owner must be {PE27_INTEGRATION_OWNER!r}"
        )
    if not proof.integration_input_digest:
        fail_reasons.append("pe27_zero_order_integration_proof: integration_input_digest required")
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe27_zero_order_integration_proof: integration_input_digest must be "
            "64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe27_integration_input_digest(pe27_input):
        fail_reasons.append("pe27_zero_order_integration_proof: integration_input_digest mismatch")

    if not proof.integration_proof_digest:
        fail_reasons.append("pe27_zero_order_integration_proof: integration_proof_digest required")
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe27_zero_order_integration_proof: integration_proof_digest must be "
            "64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe27_integration_proof_digest(
            pe27_input,
            zero_order_lifecycle_eligibility=True,
        )
        if proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append(
                "pe27_zero_order_integration_proof: integration_proof_digest mismatch"
            )

    if proof.pe27_integration_pass is not True:
        fail_reasons.append("pe27_zero_order_integration_proof: pe27_integration_pass must be true")
    if proof.zero_order_lifecycle_eligibility is not True:
        fail_reasons.append(
            "pe27_zero_order_integration_proof: zero_order_lifecycle_eligibility must be true"
        )

    pe27_result = evaluate_zero_order_lifecycle_integration(pe27_input)
    if not pe27_result["integration_pass"]:
        fail_reasons.append("pe27_zero_order_integration_input: PE-27 evaluation failed")
        fail_reasons.extend(
            f"pe27_zero_order_integration_input: {reason}" for reason in pe27_result["fail_reasons"]
        )
    elif not pe27_result["zero_order_lifecycle_eligibility"]:
        fail_reasons.append(
            "pe27_zero_order_integration_input: zero_order_lifecycle_eligibility required"
        )

    if pe27_input.source_revision != integration_input.source_revision:
        fail_reasons.append("pe27_zero_order_integration_input: source_revision mismatch")
    if pe27_input.adapter_id != integration_input.adapter_id:
        fail_reasons.append("pe27_zero_order_integration_input: adapter_id mismatch")
    if pe27_input.instrument != integration_input.instrument:
        fail_reasons.append("pe27_zero_order_integration_input: instrument mismatch")

    pe27_assembly_digest = compute_assembly_input_digest(pe27_input.pe26_assembly_input)
    pe29_assembly_digest = compute_assembly_input_digest(integration_input.pe26_assembly_input)
    if pe27_assembly_digest != pe29_assembly_digest:
        fail_reasons.append(
            "pe27_zero_order_integration_input: pe26_assembly_input_digest mismatch with PE-30"
        )

    return fail_reasons


def _validate_pe28_integration_proof(
    integration_input: TinyOrderLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe28_private_readonly_integration_proof
    pe28_input = integration_input.pe28_private_readonly_integration_input

    if proof.integration_owner != PE28_INTEGRATION_OWNER:
        fail_reasons.append(
            f"pe28_private_readonly_integration_proof: integration_owner must be "
            f"{PE28_INTEGRATION_OWNER!r}"
        )
    if not proof.integration_input_digest:
        fail_reasons.append(
            "pe28_private_readonly_integration_proof: integration_input_digest required"
        )
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe28_private_readonly_integration_proof: integration_input_digest must be "
            "64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe28_integration_input_digest(pe28_input):
        fail_reasons.append(
            "pe28_private_readonly_integration_proof: integration_input_digest mismatch"
        )

    if not proof.integration_proof_digest:
        fail_reasons.append(
            "pe28_private_readonly_integration_proof: integration_proof_digest required"
        )
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe28_private_readonly_integration_proof: integration_proof_digest must be "
            "64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe28_integration_proof_digest(
            pe28_input,
            private_readonly_lifecycle_eligibility=True,
        )
        if proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append(
                "pe28_private_readonly_integration_proof: integration_proof_digest mismatch"
            )

    if proof.pe28_integration_pass is not True:
        fail_reasons.append(
            "pe28_private_readonly_integration_proof: pe28_integration_pass must be true"
        )
    if proof.private_readonly_lifecycle_eligibility is not True:
        fail_reasons.append(
            "pe28_private_readonly_integration_proof: private_readonly_lifecycle_eligibility "
            "must be true"
        )

    pe28_result = evaluate_private_readonly_lifecycle_integration(pe28_input)
    if not pe28_result["integration_pass"]:
        fail_reasons.append("pe28_private_readonly_integration_input: PE-28 evaluation failed")
        fail_reasons.extend(
            f"pe28_private_readonly_integration_input: {reason}"
            for reason in pe28_result["fail_reasons"]
        )
    elif not pe28_result["private_readonly_lifecycle_eligibility"]:
        fail_reasons.append(
            "pe28_private_readonly_integration_input: private_readonly_lifecycle_eligibility "
            "required"
        )

    if pe28_input.source_revision != integration_input.source_revision:
        fail_reasons.append("pe28_private_readonly_integration_input: source_revision mismatch")
    if pe28_input.adapter_id != integration_input.adapter_id:
        fail_reasons.append("pe28_private_readonly_integration_input: adapter_id mismatch")
    if pe28_input.instrument != integration_input.instrument:
        fail_reasons.append("pe28_private_readonly_integration_input: instrument mismatch")

    pe28_assembly_digest = compute_assembly_input_digest(pe28_input.pe26_assembly_input)
    pe30_assembly_digest = compute_assembly_input_digest(integration_input.pe26_assembly_input)
    if pe28_assembly_digest != pe30_assembly_digest:
        fail_reasons.append(
            "pe28_private_readonly_integration_input: pe26_assembly_input_digest mismatch with PE-30"
        )

    return fail_reasons


def _validate_pe29_integration_proof(
    integration_input: TinyOrderLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    proof = integration_input.pe29_validate_only_integration_proof
    pe29_input = integration_input.pe29_validate_only_integration_input

    if proof.integration_owner != PE29_INTEGRATION_OWNER:
        fail_reasons.append(
            f"pe29_validate_only_integration_proof: integration_owner must be "
            f"{PE29_INTEGRATION_OWNER!r}"
        )
    if not proof.integration_input_digest:
        fail_reasons.append(
            "pe29_validate_only_integration_proof: integration_input_digest required"
        )
    elif not _valid_sha256_digest(proof.integration_input_digest):
        fail_reasons.append(
            "pe29_validate_only_integration_proof: integration_input_digest must be "
            "64-char lowercase sha256 hex"
        )
    elif proof.integration_input_digest != compute_pe29_integration_input_digest(pe29_input):
        fail_reasons.append(
            "pe29_validate_only_integration_proof: integration_input_digest mismatch"
        )

    if not proof.integration_proof_digest:
        fail_reasons.append(
            "pe29_validate_only_integration_proof: integration_proof_digest required"
        )
    elif not _valid_sha256_digest(proof.integration_proof_digest):
        fail_reasons.append(
            "pe29_validate_only_integration_proof: integration_proof_digest must be "
            "64-char lowercase sha256 hex"
        )
    else:
        expected_proof_digest = compute_pe29_integration_proof_digest(
            pe29_input,
            validate_only_lifecycle_eligibility=True,
        )
        if proof.integration_proof_digest != expected_proof_digest:
            fail_reasons.append(
                "pe29_validate_only_integration_proof: integration_proof_digest mismatch"
            )

    if proof.pe29_integration_pass is not True:
        fail_reasons.append(
            "pe29_validate_only_integration_proof: pe29_integration_pass must be true"
        )
    if proof.validate_only_lifecycle_eligibility is not True:
        fail_reasons.append(
            "pe29_validate_only_integration_proof: validate_only_lifecycle_eligibility must be true"
        )

    pe29_result = evaluate_validate_only_lifecycle_integration(pe29_input)
    if not pe29_result["integration_pass"]:
        fail_reasons.append("pe29_validate_only_integration_input: PE-29 evaluation failed")
        fail_reasons.extend(
            f"pe29_validate_only_integration_input: {reason}"
            for reason in pe29_result["fail_reasons"]
        )
    elif not pe29_result["validate_only_lifecycle_eligibility"]:
        fail_reasons.append(
            "pe29_validate_only_integration_input: validate_only_lifecycle_eligibility required"
        )

    if pe29_input.source_revision != integration_input.source_revision:
        fail_reasons.append("pe29_validate_only_integration_input: source_revision mismatch")
    if pe29_input.adapter_id != integration_input.adapter_id:
        fail_reasons.append("pe29_validate_only_integration_input: adapter_id mismatch")
    if pe29_input.instrument != integration_input.instrument:
        fail_reasons.append("pe29_validate_only_integration_input: instrument mismatch")

    pe29_assembly_digest = compute_assembly_input_digest(pe29_input.pe26_assembly_input)
    pe30_assembly_digest = compute_assembly_input_digest(integration_input.pe26_assembly_input)
    if pe29_assembly_digest != pe30_assembly_digest:
        fail_reasons.append(
            "pe29_validate_only_integration_input: pe26_assembly_input_digest mismatch with PE-30"
        )

    return fail_reasons


def _canonical_tiny_order_static_plan_evidence(
    instrument: str,
    *,
    plan_notional_eur: float,
    plan_quantity: float,
    plan_price: float,
) -> dict[str, Any]:
    spec = replace(default_bounded_futures_normal_v0_spec(), instrument=instrument)
    return {
        "session_class": spec.session_class,
        "order_policy": spec.order_policy,
        "instrument": instrument,
        "market_type": spec.market_type,
        "margin_mode": spec.margin_mode,
        "max_leverage": spec.max_leverage,
        "leverage_within_cap": True,
        "position_mode": spec.position_mode,
        "order_side_semantics": "long_or_short_bounded",
        "reduce_only_supported": True,
        "order_attempt_count": 0,
        "real_orders_created_count": 0,
        "cancel_or_close_attempt_count": 0,
        "order_notional_eur": plan_notional_eur,
        "order_notional_within_cap": plan_notional_eur <= spec.max_notional_eur,
        "position_flattened_by_end": True,
        "cancel_or_close_evidence_valid": True,
        "futures_endpoint_isolation_pass": True,
        "spot_endpoint_isolation_pass": True,
        "funding_risk_acknowledged": True,
        "liquidation_risk_acknowledged": True,
        "risk_killswitch_scope_active": True,
        "risk_killswitch_scope_pass": True,
        "master_v2_double_play_authority_used": False,
        "scheduler_started": False,
        "runtime_started": False,
        "live_env_present": False,
        "futures_session_authorized_now": False,
        "plan_quantity": plan_quantity,
        "plan_price": plan_price,
    }


def _validate_tiny_order_proof(
    integration_input: TinyOrderLifecycleIntegrationInput,
) -> list[str]:
    fail_reasons: list[str] = []
    binding = integration_input.tiny_order_proof
    canonical_owner = PHASE_CANONICAL_OWNERS[PHASE_TINY_ORDER]

    if binding.tiny_order_owner != TINY_ORDER_OWNER:
        fail_reasons.append(f"tiny_order_proof: tiny_order_owner must be {TINY_ORDER_OWNER!r}")
    if binding.tiny_order_owner != canonical_owner:
        fail_reasons.append(
            f"tiny_order_proof: tiny_order_owner must match PE-12 canonical owner "
            f"{canonical_owner!r}"
        )
    if binding.testnet_contract_version != TESTNET_CONTRACT_VERSION:
        fail_reasons.append(
            f"tiny_order_proof: testnet_contract_version must be {TESTNET_CONTRACT_VERSION!r}"
        )
    if binding.tiny_order_mode != TINY_ORDER_MODE:
        fail_reasons.append(f"tiny_order_proof: tiny_order_mode must be {TINY_ORDER_MODE!r}")
    if binding.plan_only is not True:
        fail_reasons.append("tiny_order_proof: plan_only must be true")
    if binding.tiny_order_plan_static_proven is not True:
        fail_reasons.append("tiny_order_proof: tiny_order_plan_static_proven must be true")
    if binding.tiny_order_static_plan_capability is not True:
        fail_reasons.append("tiny_order_proof: tiny_order_static_plan_capability must be true")

    for field_name, value in (
        ("plan_notional_eur", binding.plan_notional_eur),
        ("plan_quantity", binding.plan_quantity),
        ("plan_price", binding.plan_price),
    ):
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            fail_reasons.append(f"tiny_order_proof: {field_name} must be positive finite")
        elif float(value) <= 0:
            fail_reasons.append(f"tiny_order_proof: {field_name} must be positive")
    spec = replace(
        default_bounded_futures_normal_v0_spec(),
        instrument=integration_input.instrument,
    )
    if binding.plan_notional_eur > spec.max_notional_eur:
        fail_reasons.append("tiny_order_proof: plan_notional_eur exceeds bounded cap")
    if binding.testnet_started is not False:
        fail_reasons.append("tiny_order_proof: testnet_started must be false")
    if binding.harness_started is not False:
        fail_reasons.append("tiny_order_proof: harness_started must be false")
    if binding.subprocess_started is not False:
        fail_reasons.append("tiny_order_proof: subprocess_started must be false")

    mutation_flags = (
        ("trading_capability", binding.trading_capability),
        ("order_capability", binding.order_capability),
        ("cancel_capability", binding.cancel_capability),
        ("amend_capability", binding.amend_capability),
        ("flatten_capability", binding.flatten_capability),
        ("transfer_capability", binding.transfer_capability),
        ("withdrawal_capability", binding.withdrawal_capability),
        ("deposit_capability", binding.deposit_capability),
    )
    for field_name, value in mutation_flags:
        if value is not False:
            fail_reasons.append(f"tiny_order_proof: {field_name} must be false")

    if binding.request_count != 0:
        fail_reasons.append("tiny_order_proof: request_count must be 0")
    if binding.exchange_request_count != 0:
        fail_reasons.append("tiny_order_proof: exchange_request_count must be 0")
    if binding.orders_created != 0:
        fail_reasons.append("tiny_order_proof: orders_created must be 0")
    if binding.orders_cancelled != 0:
        fail_reasons.append("tiny_order_proof: orders_cancelled must be 0")
    if binding.orders_amended != 0:
        fail_reasons.append("tiny_order_proof: orders_amended must be 0")
    if binding.positions_changed != 0:
        fail_reasons.append("tiny_order_proof: positions_changed must be 0")
    if binding.network_used is not False:
        fail_reasons.append("tiny_order_proof: network_used must be false")
    if binding.credentials_used is not False:
        fail_reasons.append("tiny_order_proof: credentials_used must be false")
    if binding.secret_material_read is not False:
        fail_reasons.append("tiny_order_proof: secret_material_read must be false")
    if binding.secret_material_stored is not False:
        fail_reasons.append("tiny_order_proof: secret_material_stored must be false")
    if binding.exchange_api_called is not False:
        fail_reasons.append("tiny_order_proof: exchange_api_called must be false")
    if binding.account_state_queried is not False:
        fail_reasons.append("tiny_order_proof: account_state_queried must be false")
    if binding.adapter_called is not False:
        fail_reasons.append("tiny_order_proof: adapter_called must be false")
    if binding.runtime_started is not False:
        fail_reasons.append("tiny_order_proof: runtime_started must be false")

    if not binding.tiny_order_proof_digest:
        fail_reasons.append("tiny_order_proof: tiny_order_proof_digest required")
    elif not _valid_sha256_digest(binding.tiny_order_proof_digest):
        fail_reasons.append(
            "tiny_order_proof: tiny_order_proof_digest must be 64-char lowercase sha256 hex"
        )
    elif binding.tiny_order_proof_digest != compute_tiny_order_proof_digest(binding):
        fail_reasons.append("tiny_order_proof: tiny_order_proof_digest mismatch")

    if FUTURES_SESSION_AUTHORIZED_NOW:
        fail_reasons.append("FUTURES_SESSION_AUTHORIZED_NOW must be false")
    if TESTNET_PACKAGE_MARKER != "BOUNDED_FUTURES_TESTNET_CONTRACT_V0=true":
        fail_reasons.append("canonical testnet contract package marker mismatch")

    spec = replace(
        default_bounded_futures_normal_v0_spec(),
        instrument=integration_input.instrument,
    )
    evidence = _canonical_tiny_order_static_plan_evidence(
        integration_input.instrument,
        plan_notional_eur=binding.plan_notional_eur,
        plan_quantity=binding.plan_quantity,
        plan_price=binding.plan_price,
    )
    contract_result = evaluate_bounded_futures_testnet_evidence(evidence, spec=spec)
    if not contract_result.get("bounded_futures_testnet_pass"):
        fail_reasons.append("tiny_order_proof: canonical testnet contract evaluation failed")
        fail_reasons.extend(
            f"tiny_order_proof: {reason}" for reason in contract_result.get("fail_reasons", [])
        )

    return fail_reasons


def validate_tiny_order_lifecycle_integration_input(
    integration_input: TinyOrderLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-30 integration input bindings."""
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
    if matrix.assigned_lifecycle_phase != PHASE_TINY_ORDER:
        fail_reasons.append(
            f"lifecycle_matrix_proof: assigned_lifecycle_phase must be {PHASE_TINY_ORDER!r}"
        )
    elif matrix.assigned_lifecycle_phase not in LIFECYCLE_PHASE_DESCRIPTORS:
        fail_reasons.append("lifecycle_matrix_proof: unsupported lifecycle phase")

    fail_reasons.extend(_validate_pe26_assembly_proof(integration_input))
    fail_reasons.extend(_validate_pe27_integration_proof(integration_input))
    fail_reasons.extend(_validate_pe28_integration_proof(integration_input))
    fail_reasons.extend(_validate_pe29_integration_proof(integration_input))
    fail_reasons.extend(_validate_tiny_order_proof(integration_input))
    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _validate_tiny_order_lifecycle_compatibility(
    integration_input: TinyOrderLifecycleIntegrationInput,
) -> list[str]:
    """Static declarative compatibility for PE-12 tiny_order phase gates."""
    fail_reasons: list[str] = []
    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[PHASE_TINY_ORDER]
    snapshot = integration_input.safety_snapshot
    proof = integration_input.tiny_order_proof

    if descriptor.orders_phase and snapshot.orders_allowed:
        fail_reasons.append("lifecycle/gate contradiction: orders_allowed true for tiny_order")
    if descriptor.credentials_phase and snapshot.credentials_allowed:
        fail_reasons.append("lifecycle/gate contradiction: credentials_allowed true for tiny_order")
    if snapshot.execution_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: execution_authorized true for tiny_order"
        )
    if snapshot.live_authorized:
        fail_reasons.append("lifecycle/gate contradiction: live_authorized true for tiny_order")
    if snapshot.zero_order_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: zero_order_authorized true for tiny_order"
        )
    if snapshot.private_readonly_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: private_readonly_authorized true for tiny_order"
        )
    if snapshot.validate_only_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: validate_only_authorized true for tiny_order"
        )
    if snapshot.tiny_order_authorized:
        fail_reasons.append(
            "lifecycle/gate contradiction: tiny_order_authorized true for tiny_order"
        )
    if snapshot.network_allowed and proof.network_used:
        fail_reasons.append("lifecycle/gate contradiction: network_used with network_allowed")
    if proof.network_used:
        fail_reasons.append("plan-only tiny_order proof requires network_used false")
    if not proof.plan_only or not proof.tiny_order_plan_static_proven:
        fail_reasons.append("plan-only tiny_order proof not established")
    if not proof.tiny_order_static_plan_capability:
        fail_reasons.append("tiny_order requires tiny_order_static_plan_capability true")

    return fail_reasons


def evaluate_tiny_order_lifecycle_integration(
    integration_input: TinyOrderLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    expected_assembly_input_digest: str | None = None,
    expected_assembly_result_digest: str | None = None,
    expected_pe27_integration_proof_digest: str | None = None,
    expected_pe28_integration_proof_digest: str | None = None,
    expected_pe29_integration_proof_digest: str | None = None,
    expected_tiny_order_proof_digest: str | None = None,
    loose_boolean_eligibility: bool = False,
    execution_authorized: bool = False,
    live_authorized: bool = False,
    zero_order_authorized: bool = False,
    private_readonly_authorized: bool = False,
    validate_only_authorized: bool = False,
    tiny_order_authorized: bool = False,
    network_allowed: bool = False,
    credentials_allowed: bool = False,
    orders_allowed: bool = False,
    runtime_started: bool = False,
    adapter_called: bool = False,
    exchange_api_called_override: bool = False,
    account_state_queried_override: bool = False,
    unknown_lifecycle_state: str | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-30 tiny-order lifecycle static integration proof."""
    fail_reasons = validate_tiny_order_lifecycle_integration_input(integration_input)

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

    if expected_pe27_integration_proof_digest is not None:
        if (
            integration_input.pe27_zero_order_integration_proof.integration_proof_digest
            != expected_pe27_integration_proof_digest
        ):
            fail_reasons.append(
                "pe27_zero_order_integration_proof: integration_proof_digest mismatch"
            )

    if expected_pe28_integration_proof_digest is not None:
        if (
            integration_input.pe28_private_readonly_integration_proof.integration_proof_digest
            != expected_pe28_integration_proof_digest
        ):
            fail_reasons.append(
                "pe28_private_readonly_integration_proof: integration_proof_digest mismatch"
            )

    if expected_pe29_integration_proof_digest is not None:
        if (
            integration_input.pe29_validate_only_integration_proof.integration_proof_digest
            != expected_pe29_integration_proof_digest
        ):
            fail_reasons.append(
                "pe29_validate_only_integration_proof: integration_proof_digest mismatch"
            )

    if expected_tiny_order_proof_digest is not None:
        if (
            integration_input.tiny_order_proof.tiny_order_proof_digest
            != expected_tiny_order_proof_digest
        ):
            fail_reasons.append("tiny_order_proof: tiny_order_proof_digest mismatch")

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
    if private_readonly_authorized:
        fail_reasons.append("private_readonly_authorized=true without authority lift is forbidden")
    if validate_only_authorized:
        fail_reasons.append("validate_only_authorized=true without authority lift is forbidden")
    if tiny_order_authorized:
        fail_reasons.append("tiny_order_authorized=true without authority lift is forbidden")
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
    if exchange_api_called_override:
        fail_reasons.append("exchange_api_called=true without exchange proof is forbidden")
    if account_state_queried_override:
        fail_reasons.append("account_state_queried=true without query proof is forbidden")

    if unknown_lifecycle_state is not None:
        if unknown_lifecycle_state not in LIFECYCLE_PHASE_DESCRIPTORS:
            fail_reasons.append(f"unknown lifecycle state: {unknown_lifecycle_state!r}")

    if not fail_reasons:
        fail_reasons.extend(_validate_tiny_order_lifecycle_compatibility(integration_input))

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    tiny_order_lifecycle_eligibility_for_separate_operator_review = integration_pass

    proof = integration_input.tiny_order_proof
    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(
                integration_input,
                tiny_order_lifecycle_eligibility_for_separate_operator_review=tiny_order_lifecycle_eligibility_for_separate_operator_review,
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
        "pe27_integration_proof_digest": (
            integration_input.pe27_zero_order_integration_proof.integration_proof_digest
        ),
        "pe28_integration_proof_digest": (
            integration_input.pe28_private_readonly_integration_proof.integration_proof_digest
        ),
        "pe29_integration_proof_digest": (
            integration_input.pe29_validate_only_integration_proof.integration_proof_digest
        ),
        "tiny_order_proof_digest": proof.tiny_order_proof_digest,
        "tiny_order_owner": proof.tiny_order_owner,
        "tiny_order_lifecycle_eligibility_for_separate_operator_review": tiny_order_lifecycle_eligibility_for_separate_operator_review,
        "pe30_tiny_order_lifecycle_static_integration_proven": (
            tiny_order_lifecycle_eligibility_for_separate_operator_review
        ),
        "global_tiny_order_lifecycle_readiness": GLOBAL_TINY_ORDER_LIFECYCLE_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_tiny_order_executed": OPERATIVE_TINY_ORDER_EXECUTED,
        "operative_adapter_called": OPERATIVE_ADAPTER_CALLED,
        "exchange_api_called": EXCHANGE_API_CALLED,
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
        "private_readonly_authorized": False,
        "validate_only_authorized": False,
        "tiny_order_authorized": False,
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
        "secret_material_read": False,
        "secret_material_stored": False,
        "exchange_request_count": 0,
        "orders_created": 0,
        "orders_cancelled": 0,
        "orders_amended": 0,
        "positions_changed": 0,
        "adapter_called": False,
        "testnet_started": False,
        "harness_started": False,
        "subprocess_started": False,
        "fail_reasons": fail_reasons,
    }


def default_minimal_tiny_order_proof(
    *,
    tiny_order_proof_digest: str | None = None,
) -> TinyOrderProofBinding:
    binding = TinyOrderProofBinding(
        tiny_order_owner=TINY_ORDER_OWNER,
        testnet_contract_version=TESTNET_CONTRACT_VERSION,
        tiny_order_mode=TINY_ORDER_MODE,
        plan_only=True,
        tiny_order_plan_static_proven=True,
        tiny_order_static_plan_capability=True,
        plan_notional_eur=5.0,
        plan_quantity=0.01,
        plan_price=2500.0,
        tiny_order_proof_digest="",
        request_count=0,
        exchange_request_count=0,
        orders_created=0,
        orders_cancelled=0,
        orders_amended=0,
        positions_changed=0,
        network_used=False,
        credentials_used=False,
        secret_material_read=False,
        secret_material_stored=False,
        exchange_api_called=False,
        account_state_queried=False,
        adapter_called=False,
        runtime_started=False,
        testnet_started=False,
        harness_started=False,
        subprocess_started=False,
        trading_capability=False,
        order_capability=False,
        cancel_capability=False,
        amend_capability=False,
        flatten_capability=False,
        transfer_capability=False,
        withdrawal_capability=False,
        deposit_capability=False,
    )
    digest = tiny_order_proof_digest or compute_tiny_order_proof_digest(binding)
    return TinyOrderProofBinding(
        tiny_order_owner=binding.tiny_order_owner,
        testnet_contract_version=binding.testnet_contract_version,
        tiny_order_mode=binding.tiny_order_mode,
        plan_only=binding.plan_only,
        tiny_order_plan_static_proven=binding.tiny_order_plan_static_proven,
        tiny_order_static_plan_capability=binding.tiny_order_static_plan_capability,
        plan_notional_eur=binding.plan_notional_eur,
        plan_quantity=binding.plan_quantity,
        plan_price=binding.plan_price,
        tiny_order_proof_digest=digest,
        request_count=binding.request_count,
        exchange_request_count=binding.exchange_request_count,
        orders_created=binding.orders_created,
        orders_cancelled=binding.orders_cancelled,
        orders_amended=binding.orders_amended,
        positions_changed=binding.positions_changed,
        network_used=binding.network_used,
        credentials_used=binding.credentials_used,
        secret_material_read=binding.secret_material_read,
        secret_material_stored=binding.secret_material_stored,
        exchange_api_called=binding.exchange_api_called,
        account_state_queried=binding.account_state_queried,
        adapter_called=binding.adapter_called,
        runtime_started=binding.runtime_started,
        testnet_started=binding.testnet_started,
        harness_started=binding.harness_started,
        subprocess_started=binding.subprocess_started,
        trading_capability=binding.trading_capability,
        order_capability=binding.order_capability,
        cancel_capability=binding.cancel_capability,
        amend_capability=binding.amend_capability,
        flatten_capability=binding.flatten_capability,
        transfer_capability=binding.transfer_capability,
        withdrawal_capability=binding.withdrawal_capability,
        deposit_capability=binding.deposit_capability,
    )


def default_minimal_safety_snapshot() -> IntegrationSafetySnapshot:
    return IntegrationSafetySnapshot(
        preflight_remains_blocked=True,
        ready_for_operator_arming=False,
        execution_authorized=False,
        live_authorized=False,
        zero_order_authorized=False,
        private_readonly_authorized=False,
        validate_only_authorized=False,
        tiny_order_authorized=False,
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


def default_minimal_pe27_integration_proof(
    pe27_input: ZeroOrderLifecycleIntegrationInput,
) -> Pe27ZeroOrderIntegrationProofBinding:
    return Pe27ZeroOrderIntegrationProofBinding(
        integration_owner=PE27_INTEGRATION_OWNER,
        integration_input_digest=compute_pe27_integration_input_digest(pe27_input),
        integration_proof_digest=compute_pe27_integration_proof_digest(
            pe27_input,
            zero_order_lifecycle_eligibility=True,
        ),
        pe27_integration_pass=True,
        zero_order_lifecycle_eligibility=True,
    )


def default_minimal_pe28_integration_proof(
    pe28_input: PrivateReadonlyLifecycleIntegrationInput,
) -> Pe28PrivateReadonlyIntegrationProofBinding:
    return Pe28PrivateReadonlyIntegrationProofBinding(
        integration_owner=PE28_INTEGRATION_OWNER,
        integration_input_digest=compute_pe28_integration_input_digest(pe28_input),
        integration_proof_digest=compute_pe28_integration_proof_digest(
            pe28_input,
            private_readonly_lifecycle_eligibility=True,
        ),
        pe28_integration_pass=True,
        private_readonly_lifecycle_eligibility=True,
    )


def default_minimal_pe29_integration_proof(
    pe29_input: ValidateOnlyLifecycleIntegrationInput,
) -> Pe29ValidateOnlyIntegrationProofBinding:
    return Pe29ValidateOnlyIntegrationProofBinding(
        integration_owner=PE29_INTEGRATION_OWNER,
        integration_input_digest=compute_pe29_integration_input_digest(pe29_input),
        integration_proof_digest=compute_pe29_integration_proof_digest(
            pe29_input,
            validate_only_lifecycle_eligibility=True,
        ),
        pe29_integration_pass=True,
        validate_only_lifecycle_eligibility=True,
    )


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    integration_id: str = "tiny-order-lifecycle-integration-001",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> TinyOrderLifecycleIntegrationInput:
    """Minimal valid futures-generic PE-30 integration input for offline tests."""
    state_digest = lifecycle_state_digest or "e" * 64
    matrix_digest = compute_lifecycle_matrix_digest()
    assembly_input = default_minimal_assembly_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=state_digest,
    )
    pe27_input = default_minimal_pe27_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=state_digest,
    )
    pe28_input = default_minimal_pe28_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=state_digest,
    )
    pe29_input = default_minimal_pe29_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=state_digest,
    )
    tiny_order_proof = default_minimal_tiny_order_proof()

    return TinyOrderLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        integration_id=integration_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe26_assembly=PE26_CONTRACT_VERSION,
            pe27_zero_order=PE27_CONTRACT_VERSION,
            pe28_private_readonly=PE28_CONTRACT_VERSION,
            pe29_validate_only=PE29_CONTRACT_VERSION,
            pe8_testnet_contract=TESTNET_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=matrix_digest,
            assigned_lifecycle_phase=PHASE_TINY_ORDER,
            lifecycle_state_digest=state_digest,
        ),
        pe26_assembly_input=assembly_input,
        pe26_assembly_proof=default_minimal_pe26_assembly_proof(assembly_input),
        pe27_zero_order_integration_input=pe27_input,
        pe27_zero_order_integration_proof=default_minimal_pe27_integration_proof(pe27_input),
        pe28_private_readonly_integration_input=pe28_input,
        pe28_private_readonly_integration_proof=default_minimal_pe28_integration_proof(pe28_input),
        pe29_validate_only_integration_input=pe29_input,
        pe29_validate_only_integration_proof=default_minimal_pe29_integration_proof(pe29_input),
        tiny_order_proof=tiny_order_proof,
        safety_snapshot=default_minimal_safety_snapshot(),
    )
