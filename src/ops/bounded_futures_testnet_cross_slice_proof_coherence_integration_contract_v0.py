"""Bounded Futures Testnet cross-slice proof-coherence integration (v0, PE-33).

Deterministic, offline, explicit-input-only fail-closed coherence guard over canonical
PE-21..PE-32 proof bindings including the explicit PE-25 cross-slice operator-closure
binding. Compares source revisions, owner identities, upstream digest bindings, and the
static PE-12 lifecycle sequence without recalculating upstream proof semantics.

Static integration only — no network, testnet, runtime, credentials, orders, adapter calls,
exchange queries, readiness decisions, blocker lifts, authority lift, or operative assembly.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_ORDER,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
    PHASE_PRIVATE_READONLY,
    PHASE_READINESS_DECISION,
    PHASE_RECONCILIATION_REVIEW,
    PHASE_TINY_ORDER,
    PHASE_VALIDATE_ONLY,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE23_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE24_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    CONTRACT_VERSION as PE21_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE28_CONTRACT_VERSION,
    compute_integration_proof_digest as compute_pe28_integration_proof_digest,
)
from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE32_CONTRACT_VERSION,
    compute_integration_proof_digest as compute_pe32_integration_proof_digest,
    default_minimal_integration_input as default_minimal_pe32_integration_input,
)
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE31_CONTRACT_VERSION,
    compute_integration_proof_digest as compute_pe31_integration_proof_digest,
)
from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE22_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE30_CONTRACT_VERSION,
    compute_integration_proof_digest as compute_pe30_integration_proof_digest,
)
from src.ops.bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE29_CONTRACT_VERSION,
    compute_integration_proof_digest as compute_pe29_integration_proof_digest,
)
from src.ops.bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE27_CONTRACT_VERSION,
    compute_integration_proof_digest as compute_pe27_integration_proof_digest,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_CROSS_SLICE_PROOF_COHERENCE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_cross_slice_proof_coherence_integration.v0"
SERIALIZATION_VERSION = (
    "bounded_futures_testnet_cross_slice_proof_coherence_integration.serialization.v0"
)
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"

COHERENCE_MODE = "static_cross_slice_proof_coherence_for_separate_operator_review_only"
COHERENCE_OWNER = CONTRACT_VERSION

GLOBAL_CROSS_SLICE_PROOF_COHERENCE = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_READINESS_DECISION_CREATED = False
OPERATIVE_OPERATOR_DECISION_CREATED = False
OPERATIVE_OPERATOR_CLOSURE_EXECUTED = False
OPERATIVE_BLOCKER_LIFT_EXECUTED = False
OPERATIVE_PREFLIGHT_ASSEMBLY_CREATED = False
LIFECYCLE_TRANSITION_EXECUTED = False
NETWORK_RUN_STARTED = False
TESTNET_RUN_STARTED = False
RUNTIME_STARTED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

REQUIRED_SLOT_IDS: tuple[str, ...] = (
    "pe21",
    "pe22",
    "pe23",
    "pe24",
    "pe25",
    "pe26",
    "pe27",
    "pe28",
    "pe29",
    "pe30",
    "pe31",
    "pe32",
)

CANONICAL_SLOT_OWNERS: dict[str, str] = {
    "pe21": PE21_CONTRACT_VERSION,
    "pe22": PE22_CONTRACT_VERSION,
    "pe23": PE23_CONTRACT_VERSION,
    "pe24": PE24_CONTRACT_VERSION,
    "pe25": PE25_CONTRACT_VERSION,
    "pe26": PE26_CONTRACT_VERSION,
    "pe27": PE27_CONTRACT_VERSION,
    "pe28": PE28_CONTRACT_VERSION,
    "pe29": PE29_CONTRACT_VERSION,
    "pe30": PE30_CONTRACT_VERSION,
    "pe31": PE31_CONTRACT_VERSION,
    "pe32": PE32_CONTRACT_VERSION,
}

EXPECTED_UPSTREAM_SLOT_IDS: dict[str, tuple[str, ...]] = {
    "pe21": (),
    "pe22": (),
    "pe23": ("pe22",),
    "pe24": ("pe22", "pe23"),
    "pe25": ("pe22", "pe23", "pe24"),
    "pe26": ("pe21", "pe22", "pe23", "pe24", "pe25"),
    "pe27": ("pe26",),
    "pe28": ("pe27",),
    "pe29": ("pe28",),
    "pe30": ("pe29",),
    "pe31": ("pe30", "pe21"),
    "pe32": ("pe31", "pe25"),
}

LIFECYCLE_SLOT_PHASES: dict[str, str] = {
    "pe27": PHASE_ZERO_ORDER,
    "pe28": PHASE_PRIVATE_READONLY,
    "pe29": PHASE_VALIDATE_ONLY,
    "pe30": PHASE_TINY_ORDER,
    "pe31": PHASE_RECONCILIATION_REVIEW,
    "pe32": PHASE_READINESS_DECISION,
}

LIFECYCLE_SEQUENCE: tuple[str, ...] = (
    "pe27",
    "pe28",
    "pe29",
    "pe30",
    "pe31",
    "pe32",
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe21_reconciliation_primary_evidence": PE21_CONTRACT_VERSION,
    "pe22_risk_killswitch_flatten": PE22_CONTRACT_VERSION,
    "pe23_capital_slot_ratchet_release": PE23_CONTRACT_VERSION,
    "pe24_pilot_envelope": PE24_CONTRACT_VERSION,
    "pe25_operator_closure": PE25_CONTRACT_VERSION,
    "pe26_preflight_execution_readiness_assembly": PE26_CONTRACT_VERSION,
    "pe27_zero_order": PE27_CONTRACT_VERSION,
    "pe28_private_readonly": PE28_CONTRACT_VERSION,
    "pe29_validate_only": PE29_CONTRACT_VERSION,
    "pe30_tiny_order": PE30_CONTRACT_VERSION,
    "pe31_reconciliation_review": PE31_CONTRACT_VERSION,
    "pe32_readiness_decision": PE32_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe21_reconciliation_primary_evidence: str
    pe22_risk_killswitch_flatten: str
    pe23_capital_slot_ratchet_release: str
    pe24_pilot_envelope: str
    pe25_operator_closure: str
    pe26_preflight_execution_readiness_assembly: str
    pe27_zero_order: str
    pe28_private_readonly: str
    pe29_validate_only: str
    pe30_tiny_order: str
    pe31_reconciliation_review: str
    pe32_readiness_decision: str
    integration: str


@dataclass(frozen=True)
class UpstreamDigestBinding:
    upstream_slot_id: str
    upstream_proof_digest: str


@dataclass(frozen=True)
class ProofSlotBinding:
    slot_id: str
    canonical_owner: str
    source_revision: str
    proof_digest: str
    integration_pass: bool
    upstream_bindings: tuple[UpstreamDigestBinding, ...]
    lifecycle_phase: str | None = None


@dataclass(frozen=True)
class CrossSliceSafetySnapshot:
    preflight_remains_blocked: bool
    global_blocker_lift_authorized: bool
    preflight_lift_authorized: bool
    ready_for_operator_arming: bool
    readiness_decision_authorized: bool
    operator_decision_authorized: bool
    operator_closure_authorized: bool
    execution_authorized: bool
    zero_order_authorized: bool
    private_readonly_authorized: bool
    validate_only_authorized: bool
    tiny_order_authorized: bool
    reconciliation_authorized: bool
    evidence_acceptance_authorized: bool
    pilot_start_authorized: bool
    promotion_authorized: bool
    live_authorized: bool
    network_allowed: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    futures_only: bool
    bitcoin_direction_allowed: bool
    followup_run_gate: str


@dataclass(frozen=True)
class CrossSliceProofCoherenceIntegrationInput:
    source_revision: str
    repository_identity: str
    adapter_id: str
    integration_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    proof_slots: tuple[ProofSlotBinding, ...]
    safety_snapshot: CrossSliceSafetySnapshot
    futures_only: bool = True
    environment: str = ENVIRONMENT_TESTNET
    non_authorizing: bool = True


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def _slot_map(slots: tuple[ProofSlotBinding, ...]) -> dict[str, ProofSlotBinding]:
    return {slot.slot_id: slot for slot in slots}


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


def _validate_safety_snapshot(snapshot: CrossSliceSafetySnapshot) -> list[str]:
    fail_reasons: list[str] = []
    required_bools = (
        ("preflight_remains_blocked", True),
        ("global_blocker_lift_authorized", False),
        ("preflight_lift_authorized", False),
        ("ready_for_operator_arming", False),
        ("readiness_decision_authorized", False),
        ("operator_decision_authorized", False),
        ("operator_closure_authorized", False),
        ("execution_authorized", False),
        ("zero_order_authorized", False),
        ("private_readonly_authorized", False),
        ("validate_only_authorized", False),
        ("tiny_order_authorized", False),
        ("reconciliation_authorized", False),
        ("evidence_acceptance_authorized", False),
        ("pilot_start_authorized", False),
        ("promotion_authorized", False),
        ("live_authorized", False),
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


def _validate_proof_slot_binding(
    slot: ProofSlotBinding,
    *,
    canonical_source_revision: str,
) -> list[str]:
    fail_reasons: list[str] = []
    prefix = f"proof_slot[{slot.slot_id}]"

    expected_owner = CANONICAL_SLOT_OWNERS.get(slot.slot_id)
    if expected_owner is None:
        fail_reasons.append(f"{prefix}: unknown slot_id")
        return fail_reasons

    if slot.canonical_owner != expected_owner:
        fail_reasons.append(
            f"{prefix}: canonical_owner must be {expected_owner!r}, got {slot.canonical_owner!r}"
        )

    if not slot.source_revision:
        fail_reasons.append(f"{prefix}: source_revision required")
    elif not _valid_commit_sha(slot.source_revision):
        fail_reasons.append(f"{prefix}: source_revision must be full 40-char lowercase commit SHA")
    elif slot.source_revision != canonical_source_revision:
        fail_reasons.append(f"{prefix}: source_revision mismatch with canonical source_revision")

    if not slot.proof_digest:
        fail_reasons.append(f"{prefix}: proof_digest required")
    elif not _valid_sha256_digest(slot.proof_digest):
        fail_reasons.append(f"{prefix}: proof_digest must be 64-char lowercase sha256 hex")

    if slot.integration_pass is not True:
        fail_reasons.append(f"{prefix}: integration_pass must be true")

    expected_upstream = EXPECTED_UPSTREAM_SLOT_IDS[slot.slot_id]
    actual_upstream_ids = tuple(binding.upstream_slot_id for binding in slot.upstream_bindings)
    if actual_upstream_ids != expected_upstream:
        fail_reasons.append(
            f"{prefix}: upstream slot ids must be {expected_upstream!r}, got {actual_upstream_ids!r}"
        )

    seen_upstream: set[str] = set()
    for binding in slot.upstream_bindings:
        if binding.upstream_slot_id in seen_upstream:
            fail_reasons.append(
                f"{prefix}: duplicate upstream binding for {binding.upstream_slot_id!r}"
            )
        seen_upstream.add(binding.upstream_slot_id)
        if binding.upstream_slot_id == slot.slot_id:
            fail_reasons.append(f"{prefix}: self-referential upstream binding")
        if not binding.upstream_proof_digest:
            fail_reasons.append(
                f"{prefix}: upstream {binding.upstream_slot_id}: upstream_proof_digest required"
            )
        elif not _valid_sha256_digest(binding.upstream_proof_digest):
            fail_reasons.append(
                f"{prefix}: upstream {binding.upstream_slot_id}: "
                "upstream_proof_digest must be 64-char lowercase sha256 hex"
            )

    if slot.slot_id in LIFECYCLE_SLOT_PHASES:
        expected_phase = LIFECYCLE_SLOT_PHASES[slot.slot_id]
        if slot.lifecycle_phase != expected_phase:
            fail_reasons.append(
                f"{prefix}: lifecycle_phase must be {expected_phase!r}, got {slot.lifecycle_phase!r}"
            )
    elif slot.slot_id == "pe25":
        if slot.lifecycle_phase != PHASE_READINESS_DECISION:
            fail_reasons.append(
                f"{prefix}: lifecycle_phase must be {PHASE_READINESS_DECISION!r} "
                "for cross-slice operator-closure binding"
            )
    elif slot.lifecycle_phase is not None:
        fail_reasons.append(f"{prefix}: lifecycle_phase must be null for non-lifecycle slot")

    return fail_reasons


def _validate_upstream_digest_coherence(slots: tuple[ProofSlotBinding, ...]) -> list[str]:
    fail_reasons: list[str] = []
    slot_by_id = _slot_map(slots)

    for slot in slots:
        for binding in slot.upstream_bindings:
            upstream = slot_by_id.get(binding.upstream_slot_id)
            if upstream is None:
                fail_reasons.append(
                    f"proof_slot[{slot.slot_id}]: upstream slot {binding.upstream_slot_id!r} missing"
                )
                continue
            if binding.upstream_proof_digest != upstream.proof_digest:
                fail_reasons.append(
                    f"proof_slot[{slot.slot_id}]: upstream {binding.upstream_slot_id} "
                    "proof_digest mismatch"
                )

    return fail_reasons


def _validate_cross_slice_safety_digest_coherence(slots: tuple[ProofSlotBinding, ...]) -> list[str]:
    """PE-22/23/24 digests referenced by PE-25 and PE-26 must be identical."""
    fail_reasons: list[str] = []
    slot_by_id = _slot_map(slots)

    for safety_slot in ("pe22", "pe23", "pe24"):
        canonical_digest = slot_by_id[safety_slot].proof_digest
        for consumer in ("pe25", "pe26"):
            consumer_slot = slot_by_id[consumer]
            for binding in consumer_slot.upstream_bindings:
                if binding.upstream_slot_id == safety_slot:
                    if binding.upstream_proof_digest != canonical_digest:
                        fail_reasons.append(
                            f"cross_slice safety digest mismatch: {consumer} {safety_slot} binding"
                        )

    pe21_digest = slot_by_id["pe21"].proof_digest
    for consumer in ("pe26", "pe31"):
        consumer_slot = slot_by_id[consumer]
        for binding in consumer_slot.upstream_bindings:
            if binding.upstream_slot_id == "pe21":
                if binding.upstream_proof_digest != pe21_digest:
                    fail_reasons.append(
                        f"cross_slice reconciliation digest mismatch: {consumer} pe21 binding"
                    )

    pe25_digest = slot_by_id["pe25"].proof_digest
    for consumer in ("pe26", "pe32"):
        consumer_slot = slot_by_id[consumer]
        for binding in consumer_slot.upstream_bindings:
            if binding.upstream_slot_id == "pe25":
                if binding.upstream_proof_digest != pe25_digest:
                    fail_reasons.append(
                        f"cross_slice closure digest mismatch: {consumer} pe25 binding"
                    )

    return fail_reasons


def _validate_pe25_cross_slice_binding(slots: tuple[ProofSlotBinding, ...]) -> list[str]:
    """PE-25 explicit cross-slice binding with PE-32 readiness_decision phase."""
    fail_reasons: list[str] = []
    slot_by_id = _slot_map(slots)
    pe25 = slot_by_id["pe25"]
    pe32 = slot_by_id["pe32"]

    if pe25.lifecycle_phase != PHASE_READINESS_DECISION:
        fail_reasons.append(
            f"proof_slot[pe25]: lifecycle_phase must be {PHASE_READINESS_DECISION!r} "
            "for cross-slice operator-closure binding"
        )
    if pe32.lifecycle_phase != PHASE_READINESS_DECISION:
        fail_reasons.append(
            f"proof_slot[pe32]: lifecycle_phase must be {PHASE_READINESS_DECISION!r}"
        )

    pe25_bound_to_pe32 = any(
        binding.upstream_slot_id == "pe25" for binding in pe32.upstream_bindings
    )
    if not pe25_bound_to_pe32:
        fail_reasons.append("proof_slot[pe32]: explicit PE-25 cross-slice binding required")

    return fail_reasons


def _validate_lifecycle_sequence_coherence(slots: tuple[ProofSlotBinding, ...]) -> list[str]:
    fail_reasons: list[str] = []
    slot_by_id = _slot_map(slots)

    lifecycle_slots = [slot_by_id[slot_id] for slot_id in LIFECYCLE_SEQUENCE]
    phase_ids = [slot.lifecycle_phase for slot in lifecycle_slots]
    expected_phases = [LIFECYCLE_SLOT_PHASES[slot_id] for slot_id in LIFECYCLE_SEQUENCE]
    if phase_ids != expected_phases:
        fail_reasons.append(
            f"lifecycle sequence: phases must be {expected_phases!r}, got {phase_ids!r}"
        )

    phase_indices = [
        LIFECYCLE_PHASE_ORDER.index(phase_id)
        for phase_id in phase_ids
        if phase_id in LIFECYCLE_PHASE_ORDER
    ]
    if len(phase_indices) != len(LIFECYCLE_SEQUENCE):
        fail_reasons.append("lifecycle sequence: unsupported lifecycle phase in sequence")
    elif phase_indices != sorted(phase_indices):
        fail_reasons.append("lifecycle sequence: phases are not in canonical order")

    for index in range(1, len(LIFECYCLE_SEQUENCE)):
        current_id = LIFECYCLE_SEQUENCE[index]
        previous_id = LIFECYCLE_SEQUENCE[index - 1]
        current_slot = slot_by_id[current_id]
        previous_slot = slot_by_id[previous_id]
        bound_previous = any(
            binding.upstream_slot_id == previous_id for binding in current_slot.upstream_bindings
        )
        if not bound_previous:
            fail_reasons.append(
                f"lifecycle sequence: {current_id} must bind upstream {previous_id}"
            )
        else:
            for binding in current_slot.upstream_bindings:
                if binding.upstream_slot_id == previous_id:
                    if binding.upstream_proof_digest != previous_slot.proof_digest:
                        fail_reasons.append(
                            f"lifecycle sequence: {current_id} upstream {previous_id} digest mismatch"
                        )

    return fail_reasons


def _detect_dependency_cycles(slots: tuple[ProofSlotBinding, ...]) -> list[str]:
    fail_reasons: list[str] = []
    graph: dict[str, set[str]] = {slot.slot_id: set() for slot in slots}
    for slot in slots:
        for binding in slot.upstream_bindings:
            graph[slot.slot_id].add(binding.upstream_slot_id)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in visiting:
            fail_reasons.append(f"proof dependency cycle detected: {' -> '.join(path + [node])}")
            return
        if node in visited:
            return
        visiting.add(node)
        for neighbor in sorted(graph.get(node, ())):
            visit(neighbor, path + [node])
        visiting.remove(node)
        visited.add(node)

    for slot_id in sorted(graph):
        if slot_id not in visited:
            visit(slot_id, [])

    return _sorted_unique(fail_reasons)


def _integration_input_dict(
    integration_input: CrossSliceProofCoherenceIntegrationInput,
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
        "proof_slots": [
            {
                "slot_id": slot.slot_id,
                "canonical_owner": slot.canonical_owner,
                "source_revision": slot.source_revision,
                "proof_digest": slot.proof_digest,
                "integration_pass": slot.integration_pass,
                "lifecycle_phase": slot.lifecycle_phase,
                "upstream_bindings": [asdict(binding) for binding in slot.upstream_bindings],
            }
            for slot in sorted(integration_input.proof_slots, key=lambda item: item.slot_id)
        ],
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "futures_only": integration_input.futures_only,
        "environment": integration_input.environment,
        "non_authorizing": integration_input.non_authorizing,
    }


def serialize_integration_input_canonical(
    integration_input: CrossSliceProofCoherenceIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_input_digest(
    integration_input: CrossSliceProofCoherenceIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def compute_integration_proof_digest(
    integration_input: CrossSliceProofCoherenceIntegrationInput,
    *,
    cross_slice_proof_coherence_for_separate_operator_review: bool,
) -> str:
    payload = {
        "coherence_mode": COHERENCE_MODE,
        "coherence_owner": COHERENCE_OWNER,
        "cross_slice_proof_coherence_for_separate_operator_review": (
            cross_slice_proof_coherence_for_separate_operator_review
        ),
        "hash_algorithm": HASH_ALGORITHM,
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "package_marker": PACKAGE_MARKER,
        "pe12_package_marker": PE12_PACKAGE_MARKER,
        "proof_slot_digests": {
            slot.slot_id: slot.proof_digest
            for slot in sorted(integration_input.proof_slots, key=lambda item: item.slot_id)
        },
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": integration_input.source_revision,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_cross_slice_proof_coherence_integration_input(
    integration_input: CrossSliceProofCoherenceIntegrationInput,
) -> list[str]:
    """Fail-closed validation of explicit PE-33 cross-slice proof coherence bindings."""
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
            fail_reasons.append(f"contract_versions: {field_name} must be {expected!r}")

    slot_ids = [slot.slot_id for slot in integration_input.proof_slots]
    if len(slot_ids) != len(set(slot_ids)):
        fail_reasons.append("proof_slots: duplicate slot_id")
    unknown_slots = sorted(set(slot_ids) - set(REQUIRED_SLOT_IDS))
    if unknown_slots:
        fail_reasons.append(f"proof_slots: unknown slot ids {unknown_slots!r}")
    missing_slots = sorted(set(REQUIRED_SLOT_IDS) - set(slot_ids))
    if missing_slots:
        fail_reasons.append(f"proof_slots: missing required slot ids {missing_slots!r}")

    for slot in integration_input.proof_slots:
        fail_reasons.extend(
            _validate_proof_slot_binding(
                slot,
                canonical_source_revision=integration_input.source_revision,
            )
        )

    if not fail_reasons:
        fail_reasons.extend(_validate_upstream_digest_coherence(integration_input.proof_slots))
        fail_reasons.extend(
            _validate_cross_slice_safety_digest_coherence(integration_input.proof_slots)
        )
        fail_reasons.extend(_validate_pe25_cross_slice_binding(integration_input.proof_slots))
        fail_reasons.extend(_validate_lifecycle_sequence_coherence(integration_input.proof_slots))
        fail_reasons.extend(_detect_dependency_cycles(integration_input.proof_slots))

    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def evaluate_cross_slice_proof_coherence_integration(
    integration_input: CrossSliceProofCoherenceIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    loose_boolean_eligibility: bool = False,
) -> dict[str, Any]:
    """Evaluate explicit PE-33 cross-slice proof coherence without recalculating upstream proofs."""
    fail_reasons = validate_cross_slice_proof_coherence_integration_input(integration_input)

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    if loose_boolean_eligibility:
        fail_reasons.append("loose boolean eligibility cannot replace proof digest bindings")

    integration_pass = len(fail_reasons) == 0
    coherence = integration_pass and not loose_boolean_eligibility

    return {
        "integration_pass": integration_pass,
        "cross_slice_proof_coherence_for_separate_operator_review": coherence,
        "pe33_cross_slice_proof_coherence_static_integration_proven": coherence,
        "static_pe12_lifecycle_chain_complete": coherence,
        "source_revision_coherent": integration_pass,
        "owner_identities_coherent": integration_pass,
        "proof_digests_coherent": integration_pass,
        "lifecycle_sequence_coherent": integration_pass,
        "assigned_lifecycle_phase": PHASE_READINESS_DECISION if coherence else None,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(
                integration_input,
                cross_slice_proof_coherence_for_separate_operator_review=coherence,
            )
            if integration_pass
            else None
        ),
        "coherence_mode": COHERENCE_MODE,
        "coherence_owner": COHERENCE_OWNER,
        "contract_version": CONTRACT_VERSION,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "global_cross_slice_proof_coherence": GLOBAL_CROSS_SLICE_PROOF_COHERENCE,
        "operative_readiness_decision_created": OPERATIVE_READINESS_DECISION_CREATED,
        "operative_operator_decision_created": OPERATIVE_OPERATOR_DECISION_CREATED,
        "operative_operator_closure_executed": OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
        "operative_blocker_lift_executed": OPERATIVE_BLOCKER_LIFT_EXECUTED,
        "operative_preflight_assembly_created": OPERATIVE_PREFLIGHT_ASSEMBLY_CREATED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "runtime_started": RUNTIME_STARTED,
        "authority_lift": AUTHORITY_LIFT,
        "preflight_remains_blocked": True,
        "global_blocker_lift_authorized": False,
        "preflight_lift_authorized": False,
        "ready_for_operator_arming": False,
        "readiness_decision_authorized": False,
        "operator_decision_authorized": False,
        "operator_closure_authorized": False,
        "execution_authorized": False,
        "zero_order_authorized": False,
        "private_readonly_authorized": False,
        "validate_only_authorized": False,
        "tiny_order_authorized": False,
        "reconciliation_authorized": False,
        "evidence_acceptance_authorized": False,
        "pilot_start_authorized": False,
        "promotion_authorized": False,
        "live_authorized": False,
        "network_allowed": False,
        "credentials_allowed": False,
        "orders_allowed": False,
        "scheduler_runtime_allowed": False,
        "network_used": False,
        "credentials_used": False,
        "secret_material_read": False,
        "secret_material_stored": False,
        "exchange_api_called": False,
        "exchange_request_count": 0,
        "orders_created": 0,
        "orders_cancelled": 0,
        "orders_amended": 0,
        "positions_changed": 0,
        "adapter_called": False,
        "testnet_started": False,
        "harness_started": False,
        "subprocess_started": False,
        "account_state_queried": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
        "fail_reasons": fail_reasons,
    }


def default_minimal_safety_snapshot() -> CrossSliceSafetySnapshot:
    return CrossSliceSafetySnapshot(
        preflight_remains_blocked=True,
        global_blocker_lift_authorized=False,
        preflight_lift_authorized=False,
        ready_for_operator_arming=False,
        readiness_decision_authorized=False,
        operator_decision_authorized=False,
        operator_closure_authorized=False,
        execution_authorized=False,
        zero_order_authorized=False,
        private_readonly_authorized=False,
        validate_only_authorized=False,
        tiny_order_authorized=False,
        reconciliation_authorized=False,
        evidence_acceptance_authorized=False,
        pilot_start_authorized=False,
        promotion_authorized=False,
        live_authorized=False,
        network_allowed=False,
        credentials_allowed=False,
        orders_allowed=False,
        scheduler_runtime_allowed=False,
        futures_only=True,
        bitcoin_direction_allowed=False,
        followup_run_gate=FOLLOWUP_RUN_GATE,
    )


def _upstream(*pairs: tuple[str, str]) -> tuple[UpstreamDigestBinding, ...]:
    return tuple(
        UpstreamDigestBinding(upstream_slot_id=slot_id, upstream_proof_digest=digest)
        for slot_id, digest in pairs
    )


def _proof_slot(
    slot_id: str,
    proof_digest: str,
    *,
    source_revision: str,
    upstream: tuple[UpstreamDigestBinding, ...] = (),
    lifecycle_phase: str | None = None,
) -> ProofSlotBinding:
    return ProofSlotBinding(
        slot_id=slot_id,
        canonical_owner=CANONICAL_SLOT_OWNERS[slot_id],
        source_revision=source_revision,
        proof_digest=proof_digest,
        integration_pass=True,
        upstream_bindings=upstream,
        lifecycle_phase=lifecycle_phase,
    )


def build_coherent_proof_slots_from_pe32_default(
    *,
    source_revision: str,
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> tuple[ProofSlotBinding, ...]:
    """Build coherent PE-21..PE-32 proof slots from the canonical PE-32 default chain."""
    state_digest = lifecycle_state_digest or "f" * 64
    pe32_input = default_minimal_pe32_integration_input(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=state_digest,
    )

    pe31_input = pe32_input.pe31_reconciliation_review_integration_input
    pe30_input = pe31_input.pe30_tiny_order_integration_input
    pe29_input = pe30_input.pe29_validate_only_integration_input
    pe27_input = pe29_input.pe27_zero_order_integration_input
    pe26_asm_input = pe27_input.pe26_assembly_input
    pe26_proof = pe27_input.pe26_assembly_proof
    pe25_input = pe32_input.pe25_operator_closure_integration_input
    pe25_proof = pe32_input.pe25_operator_closure_integration_proof

    pe21_digest = pe26_asm_input.pe21_reconciliation_primary_evidence_proof.integration_proof_digest
    pe22_digest = pe26_asm_input.pe22_risk_killswitch_flatten_proof.integration_proof_digest
    pe23_digest = pe26_asm_input.pe23_capital_slot_ratchet_release_proof.integration_proof_digest
    pe24_digest = pe26_asm_input.pe24_pilot_envelope_proof.integration_proof_digest
    pe25_digest = pe25_proof.closure_result_digest
    pe26_digest = pe26_proof.assembly_result_digest
    pe27_digest = compute_pe27_integration_proof_digest(
        pe27_input,
        zero_order_lifecycle_eligibility=True,
    )
    pe28_digest = compute_pe28_integration_proof_digest(
        pe29_input.pe28_private_readonly_integration_input,
        private_readonly_lifecycle_eligibility=True,
    )
    pe29_digest = compute_pe29_integration_proof_digest(
        pe29_input,
        validate_only_lifecycle_eligibility=True,
    )
    pe30_digest = compute_pe30_integration_proof_digest(
        pe30_input,
        tiny_order_lifecycle_eligibility_for_separate_operator_review=True,
    )
    pe31_digest = compute_pe31_integration_proof_digest(
        pe31_input,
        reconciliation_review_lifecycle_eligibility_for_separate_operator_review=True,
    )
    pe32_digest = compute_pe32_integration_proof_digest(
        pe32_input,
        readiness_decision_lifecycle_eligibility_for_separate_operator_review=True,
    )

    _ = pe25_input  # explicit PE-25 chain participant for cross-slice binding review

    return (
        _proof_slot("pe21", pe21_digest, source_revision=source_revision),
        _proof_slot("pe22", pe22_digest, source_revision=source_revision),
        _proof_slot(
            "pe23",
            pe23_digest,
            source_revision=source_revision,
            upstream=_upstream(("pe22", pe22_digest)),
        ),
        _proof_slot(
            "pe24",
            pe24_digest,
            source_revision=source_revision,
            upstream=_upstream(("pe22", pe22_digest), ("pe23", pe23_digest)),
        ),
        _proof_slot(
            "pe25",
            pe25_digest,
            source_revision=source_revision,
            upstream=_upstream(
                ("pe22", pe22_digest),
                ("pe23", pe23_digest),
                ("pe24", pe24_digest),
            ),
            lifecycle_phase=PHASE_READINESS_DECISION,
        ),
        _proof_slot(
            "pe26",
            pe26_digest,
            source_revision=source_revision,
            upstream=_upstream(
                ("pe21", pe21_digest),
                ("pe22", pe22_digest),
                ("pe23", pe23_digest),
                ("pe24", pe24_digest),
                ("pe25", pe25_digest),
            ),
        ),
        _proof_slot(
            "pe27",
            pe27_digest,
            source_revision=source_revision,
            upstream=_upstream(("pe26", pe26_digest)),
            lifecycle_phase=PHASE_ZERO_ORDER,
        ),
        _proof_slot(
            "pe28",
            pe28_digest,
            source_revision=source_revision,
            upstream=_upstream(("pe27", pe27_digest)),
            lifecycle_phase=PHASE_PRIVATE_READONLY,
        ),
        _proof_slot(
            "pe29",
            pe29_digest,
            source_revision=source_revision,
            upstream=_upstream(("pe28", pe28_digest)),
            lifecycle_phase=PHASE_VALIDATE_ONLY,
        ),
        _proof_slot(
            "pe30",
            pe30_digest,
            source_revision=source_revision,
            upstream=_upstream(("pe29", pe29_digest)),
            lifecycle_phase=PHASE_TINY_ORDER,
        ),
        _proof_slot(
            "pe31",
            pe31_digest,
            source_revision=source_revision,
            upstream=_upstream(("pe30", pe30_digest), ("pe21", pe21_digest)),
            lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
        ),
        _proof_slot(
            "pe32",
            pe32_digest,
            source_revision=source_revision,
            upstream=_upstream(("pe31", pe31_digest), ("pe25", pe25_digest)),
            lifecycle_phase=PHASE_READINESS_DECISION,
        ),
    )


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    integration_id: str = "cross-slice-proof-coherence-integration-001",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> CrossSliceProofCoherenceIntegrationInput:
    """Minimal valid futures-generic PE-33 cross-slice coherence input for offline tests."""
    proof_slots = build_coherent_proof_slots_from_pe32_default(
        source_revision=source_revision,
        adapter_id=adapter_id,
        instrument=instrument,
        lifecycle_state_digest=lifecycle_state_digest,
    )
    return CrossSliceProofCoherenceIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        integration_id=integration_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe21_reconciliation_primary_evidence=PE21_CONTRACT_VERSION,
            pe22_risk_killswitch_flatten=PE22_CONTRACT_VERSION,
            pe23_capital_slot_ratchet_release=PE23_CONTRACT_VERSION,
            pe24_pilot_envelope=PE24_CONTRACT_VERSION,
            pe25_operator_closure=PE25_CONTRACT_VERSION,
            pe26_preflight_execution_readiness_assembly=PE26_CONTRACT_VERSION,
            pe27_zero_order=PE27_CONTRACT_VERSION,
            pe28_private_readonly=PE28_CONTRACT_VERSION,
            pe29_validate_only=PE29_CONTRACT_VERSION,
            pe30_tiny_order=PE30_CONTRACT_VERSION,
            pe31_reconciliation_review=PE31_CONTRACT_VERSION,
            pe32_readiness_decision=PE32_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        proof_slots=proof_slots,
        safety_snapshot=default_minimal_safety_snapshot(),
    )


def replace_proof_slot(
    slots: tuple[ProofSlotBinding, ...],
    updated_slot: ProofSlotBinding,
) -> tuple[ProofSlotBinding, ...]:
    return tuple(updated_slot if slot.slot_id == updated_slot.slot_id else slot for slot in slots)
