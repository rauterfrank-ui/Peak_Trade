"""Bounded Futures Testnet adapter capability lifecycle integration (v0, GLB-012/013).

Deterministic, offline, explicit-input-only contract binding PE-8/9/10/11 adapter
capability proofs to the PE-12 lifecycle matrix. Static integration only — no
adapter execution, network, testnet, runtime, orders, or authority lift.
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
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION,
    VENUE_OKX_EUROPE,
)
from src.ops.okx_europe_adapter_lifecycle_contract_v0 import (
    CONTRACT_VERSION as OKX_EUROPE_LIFECYCLE_CONTRACT_VERSION,
    PACKAGE_MARKER as OKX_EUROPE_LIFECYCLE_PACKAGE_MARKER,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_adapter_capability_lifecycle_integration.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_adapter_capability_lifecycle_integration.serialization.v0"
)
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

PE8_CONTRACT_VERSION = "bounded_futures_testnet_adapter.v0"
PE9_CONTRACT_VERSION = "bounded_futures_testnet_harness.v0"
PE10_CONTRACT_VERSION = "bounded_futures_testnet_runtime_harness.v0"
PE11_CONTRACT_VERSION = "bounded_futures_private_readonly.v0"

GLB012_013_GLOBAL_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_ADAPTER_VALIDATION_EXECUTED = False
LIFECYCLE_TRANSITION_EXECUTED = False
NETWORK_RUN_STARTED = False
TESTNET_RUN_STARTED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe8_adapter_capability": PE8_CONTRACT_VERSION,
    "pe9_capability_validation": PE9_CONTRACT_VERSION,
    "pe10_execution_boundary": PE10_CONTRACT_VERSION,
    "pe11_lifecycle_safety_binding": PE11_CONTRACT_VERSION,
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}

_CAPABILITY_PROOF_KEYS = frozenset(
    {
        "pe8_adapter_capability",
        "pe9_capability_validation",
        "pe10_execution_boundary",
        "pe11_lifecycle_safety_binding",
    }
)

_PHASE_REQUIRED_PROOFS: dict[str, frozenset[str]] = {
    PHASE_STATIC_PREFLIGHT: _CAPABILITY_PROOF_KEYS,
    PHASE_ZERO_ORDER: _CAPABILITY_PROOF_KEYS,
    "private_readonly": _CAPABILITY_PROOF_KEYS,
    "validate_only": _CAPABILITY_PROOF_KEYS,
    "tiny_order": _CAPABILITY_PROOF_KEYS,
    "reconciliation_review": frozenset({"pe8_adapter_capability", "pe11_lifecycle_safety_binding"}),
    "readiness_decision": frozenset({"pe8_adapter_capability", "pe11_lifecycle_safety_binding"}),
}

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD")


@dataclass(frozen=True)
class ContractVersionsInput:
    pe8_adapter_capability: str
    pe9_capability_validation: str
    pe10_execution_boundary: str
    pe11_lifecycle_safety_binding: str
    pe12_lifecycle: str
    integration: str


@dataclass(frozen=True)
class CapabilityProofBinding:
    proof_digest: str
    proof_pass: bool
    adapter_id: str
    contract_version: str


@dataclass(frozen=True)
class CapabilityProofsInput:
    pe8_adapter_capability: CapabilityProofBinding
    pe9_capability_validation: CapabilityProofBinding
    pe10_execution_boundary: CapabilityProofBinding
    pe11_lifecycle_safety_binding: CapabilityProofBinding


@dataclass(frozen=True)
class LifecycleMatrixProof:
    pe12_contract_version: str
    lifecycle_matrix_digest: str
    assigned_lifecycle_phase: str
    lifecycle_state_digest: str


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
class CapabilityLifecycleIntegrationInput:
    source_revision: str
    repository_identity: str
    adapter_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    capability_proofs: CapabilityProofsInput
    lifecycle_matrix_proof: LifecycleMatrixProof
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


def compute_okx_europe_adapter_lifecycle_slot_digest() -> str:
    """Deterministic digest binding OKX-Europe lifecycle contract to venue binding (not PE-12)."""
    slot = {
        "hash_algorithm": HASH_ALGORITHM,
        "okx_europe_lifecycle_contract_version": OKX_EUROPE_LIFECYCLE_CONTRACT_VERSION,
        "okx_europe_lifecycle_package_marker": OKX_EUROPE_LIFECYCLE_PACKAGE_MARKER,
        "venue": VENUE_OKX_EUROPE,
        "venue_binding_lifecycle_contract_version": OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION,
    }
    return hashlib.sha256(
        json.dumps(slot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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
    integration_input: CapabilityLifecycleIntegrationInput,
) -> dict[str, Any]:
    return {
        "integration_contract_version": CONTRACT_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": integration_input.source_revision,
        "repository_identity": integration_input.repository_identity,
        "adapter_id": integration_input.adapter_id,
        "instrument": integration_input.instrument,
        "market_type": integration_input.market_type,
        "contract_versions": asdict(integration_input.contract_versions),
        "capability_proofs": {
            key: asdict(getattr(integration_input.capability_proofs, key))
            for key in sorted(_CAPABILITY_PROOF_KEYS)
        },
        "lifecycle_matrix_proof": asdict(integration_input.lifecycle_matrix_proof),
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: CapabilityLifecycleIntegrationInput,
) -> str:
    """Deterministic JSON serialization with stable mapping order."""
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: CapabilityLifecycleIntegrationInput,
) -> str:
    """SHA-256 digest over canonical integration-input serialization."""
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _integration_proof_dict(
    integration_input: CapabilityLifecycleIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
) -> dict[str, Any]:
    payload = {
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "source_revision": integration_input.source_revision,
        "adapter_id": integration_input.adapter_id,
        "lifecycle_matrix_digest": integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest,
        "assigned_lifecycle_phase": integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase,
        "glb012_013_static_integration_proven": False,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_adapter_validation_executed": OPERATIVE_ADAPTER_VALIDATION_EXECUTED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "glb012_013_global_readiness": GLB012_013_GLOBAL_READINESS,
        "non_authorizing": True,
    }
    if integration_proof_digest is not None:
        payload["integration_proof_digest"] = integration_proof_digest
    return payload


def serialize_integration_proof_canonical(
    integration_input: CapabilityLifecycleIntegrationInput,
) -> str:
    """Deterministic JSON serialization excluding self-referential digest field."""
    return json.dumps(
        _integration_proof_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: CapabilityLifecycleIntegrationInput,
) -> str:
    """SHA-256 digest over canonical integration-proof serialization."""
    return hashlib.sha256(
        serialize_integration_proof_canonical(integration_input).encode("utf-8")
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


def _validate_capability_proof_binding(
    binding: CapabilityProofBinding,
    *,
    prefix: str,
    expected_contract_version: str,
    expected_adapter_id: str | None,
) -> list[str]:
    fail_reasons: list[str] = []
    if not binding.proof_digest:
        fail_reasons.append(f"{prefix}: proof_digest required")
    elif not _valid_sha256_digest(binding.proof_digest):
        fail_reasons.append(f"{prefix}: proof_digest must be 64-char lowercase sha256 hex")
    if binding.contract_version != expected_contract_version:
        fail_reasons.append(
            f"{prefix}: contract_version must be {expected_contract_version!r}, "
            f"got {binding.contract_version!r}"
        )
    if not binding.adapter_id:
        fail_reasons.append(f"{prefix}: adapter_id required")
    elif expected_adapter_id is not None and binding.adapter_id != expected_adapter_id:
        fail_reasons.append(f"{prefix}: adapter_id mismatch with integration adapter_id")
    if binding.proof_pass is not True:
        fail_reasons.append(f"{prefix}: proof_pass must be true for valid integration")
    return fail_reasons


def validate_capability_lifecycle_integration_input(
    integration_input: CapabilityLifecycleIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit integration input bindings."""
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

    proofs = integration_input.capability_proofs
    proof_bindings = {
        "pe8_adapter_capability": (
            proofs.pe8_adapter_capability,
            PE8_CONTRACT_VERSION,
        ),
        "pe9_capability_validation": (
            proofs.pe9_capability_validation,
            PE9_CONTRACT_VERSION,
        ),
        "pe10_execution_boundary": (
            proofs.pe10_execution_boundary,
            PE10_CONTRACT_VERSION,
        ),
        "pe11_lifecycle_safety_binding": (
            proofs.pe11_lifecycle_safety_binding,
            PE11_CONTRACT_VERSION,
        ),
    }
    for prefix, (binding, expected_version) in proof_bindings.items():
        fail_reasons.extend(
            _validate_capability_proof_binding(
                binding,
                prefix=prefix,
                expected_contract_version=expected_version,
                expected_adapter_id=integration_input.adapter_id,
            )
        )

    matrix = integration_input.lifecycle_matrix_proof
    if not matrix.pe12_contract_version:
        fail_reasons.append("lifecycle_matrix_proof: pe12_contract_version required")
    elif matrix.pe12_contract_version != PE12_CONTRACT_VERSION:
        fail_reasons.append(
            f"lifecycle_matrix_proof: pe12_contract_version must be {PE12_CONTRACT_VERSION!r}"
        )
    if not matrix.lifecycle_matrix_digest:
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest required")
    elif not _valid_sha256_digest(matrix.lifecycle_matrix_digest):
        fail_reasons.append(
            "lifecycle_matrix_proof: lifecycle_matrix_digest must be 64-char lowercase sha256 hex"
        )
    elif matrix.lifecycle_matrix_digest != compute_lifecycle_matrix_digest():
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest mismatch")
    if not matrix.lifecycle_state_digest:
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_state_digest required")
    elif not _valid_sha256_digest(matrix.lifecycle_state_digest):
        fail_reasons.append(
            "lifecycle_matrix_proof: lifecycle_state_digest must be 64-char lowercase sha256 hex"
        )
    if not matrix.assigned_lifecycle_phase:
        fail_reasons.append("lifecycle_matrix_proof: assigned_lifecycle_phase required")
    elif matrix.assigned_lifecycle_phase not in LIFECYCLE_PHASE_DESCRIPTORS:
        fail_reasons.append(
            f"lifecycle_matrix_proof: unsupported lifecycle phase {matrix.assigned_lifecycle_phase!r}"
        )

    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def _validate_capability_lifecycle_compatibility(
    integration_input: CapabilityLifecycleIntegrationInput,
) -> list[str]:
    """Static declarative compatibility between capability proofs and lifecycle phase."""
    fail_reasons: list[str] = []
    phase = integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase
    if phase not in _PHASE_REQUIRED_PROOFS:
        return [f"unsupported lifecycle phase for capability binding: {phase!r}"]

    required = _PHASE_REQUIRED_PROOFS[phase]
    proofs = integration_input.capability_proofs
    proof_map = {
        "pe8_adapter_capability": proofs.pe8_adapter_capability,
        "pe9_capability_validation": proofs.pe9_capability_validation,
        "pe10_execution_boundary": proofs.pe10_execution_boundary,
        "pe11_lifecycle_safety_binding": proofs.pe11_lifecycle_safety_binding,
    }
    for proof_key in required:
        binding = proof_map[proof_key]
        if binding.proof_pass is not True:
            fail_reasons.append(
                f"capability/lifecycle contradiction: {proof_key} required for phase {phase!r}"
            )

    descriptor = LIFECYCLE_PHASE_DESCRIPTORS[phase]
    snapshot = integration_input.safety_snapshot
    if descriptor.network_phase and snapshot.network_allowed:
        fail_reasons.append(
            f"capability/lifecycle contradiction: network_allowed true for phase {phase!r}"
        )
    if descriptor.orders_phase and snapshot.orders_allowed:
        fail_reasons.append(
            f"capability/lifecycle contradiction: orders_allowed true for phase {phase!r}"
        )
    if descriptor.credentials_phase and snapshot.credentials_allowed:
        fail_reasons.append(
            f"capability/lifecycle contradiction: credentials_allowed true for phase {phase!r}"
        )
    if phase == PHASE_STATIC_PREFLIGHT:
        for proof_key in _CAPABILITY_PROOF_KEYS:
            if proof_map[proof_key].proof_pass is not True:
                fail_reasons.append(
                    f"static_preflight requires all capability proofs pass; {proof_key} failed"
                )

    return fail_reasons


def evaluate_capability_lifecycle_integration(
    integration_input: CapabilityLifecycleIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    expected_capability_proof_digests: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Evaluate explicit PE-8/9/10/11-to-PE-12 integration proof (offline, non-authorizing)."""
    fail_reasons = validate_capability_lifecycle_integration_input(integration_input)

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    matrix = integration_input.lifecycle_matrix_proof
    if expected_lifecycle_state_digest is not None:
        if matrix.lifecycle_state_digest != expected_lifecycle_state_digest:
            fail_reasons.append("lifecycle_state_digest mismatch")

    if expected_capability_proof_digests:
        proofs = integration_input.capability_proofs
        digest_map = {
            "pe8_adapter_capability": proofs.pe8_adapter_capability.proof_digest,
            "pe9_capability_validation": proofs.pe9_capability_validation.proof_digest,
            "pe10_execution_boundary": proofs.pe10_execution_boundary.proof_digest,
            "pe11_lifecycle_safety_binding": proofs.pe11_lifecycle_safety_binding.proof_digest,
        }
        for key, expected_digest in expected_capability_proof_digests.items():
            actual = digest_map.get(key)
            if actual is None:
                fail_reasons.append(f"unknown capability proof key for digest check: {key!r}")
            elif actual != expected_digest:
                fail_reasons.append(f"{key}: proof_digest mismatch")

    if not fail_reasons:
        fail_reasons.extend(_validate_capability_lifecycle_compatibility(integration_input))

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    glb_proven = integration_pass

    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(integration_input) if integration_pass else None
        ),
        "lifecycle_matrix_digest": matrix.lifecycle_matrix_digest,
        "assigned_lifecycle_phase": matrix.assigned_lifecycle_phase,
        "glb012_013_static_integration_proven": glb_proven,
        "glb012_013_global_readiness": GLB012_013_GLOBAL_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_adapter_validation_executed": OPERATIVE_ADAPTER_VALIDATION_EXECUTED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": True,
        "ready_for_operator_arming": False,
        "execution_authorized": False,
        "live_authorized": False,
        "zero_order_authorized": False,
        "fail_reasons": fail_reasons,
    }


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


def default_minimal_capability_proof_binding(
    *,
    adapter_id: str,
    contract_version: str,
    proof_digest: str,
) -> CapabilityProofBinding:
    return CapabilityProofBinding(
        proof_digest=proof_digest,
        proof_pass=True,
        adapter_id=adapter_id,
        contract_version=contract_version,
    )


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> CapabilityLifecycleIntegrationInput:
    """Minimal valid futures-generic integration input for offline tests."""
    digest_a = "a" * 64
    digest_b = "b" * 64
    digest_c = "c" * 64
    digest_d = "d" * 64
    state_digest = lifecycle_state_digest or "e" * 64
    matrix_digest = compute_lifecycle_matrix_digest()

    proofs = CapabilityProofsInput(
        pe8_adapter_capability=default_minimal_capability_proof_binding(
            adapter_id=adapter_id,
            contract_version=PE8_CONTRACT_VERSION,
            proof_digest=digest_a,
        ),
        pe9_capability_validation=default_minimal_capability_proof_binding(
            adapter_id=adapter_id,
            contract_version=PE9_CONTRACT_VERSION,
            proof_digest=digest_b,
        ),
        pe10_execution_boundary=default_minimal_capability_proof_binding(
            adapter_id=adapter_id,
            contract_version=PE10_CONTRACT_VERSION,
            proof_digest=digest_c,
        ),
        pe11_lifecycle_safety_binding=default_minimal_capability_proof_binding(
            adapter_id=adapter_id,
            contract_version=PE11_CONTRACT_VERSION,
            proof_digest=digest_d,
        ),
    )
    return CapabilityLifecycleIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe8_adapter_capability=PE8_CONTRACT_VERSION,
            pe9_capability_validation=PE9_CONTRACT_VERSION,
            pe10_execution_boundary=PE10_CONTRACT_VERSION,
            pe11_lifecycle_safety_binding=PE11_CONTRACT_VERSION,
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        capability_proofs=proofs,
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=matrix_digest,
            assigned_lifecycle_phase=PHASE_STATIC_PREFLIGHT,
            lifecycle_state_digest=state_digest,
        ),
        safety_snapshot=default_minimal_safety_snapshot(),
    )
