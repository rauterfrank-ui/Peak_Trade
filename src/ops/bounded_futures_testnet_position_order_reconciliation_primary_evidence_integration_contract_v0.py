"""Bounded Futures Testnet position/order reconciliation primary evidence integration (v0, PE-21).

Deterministic, offline, explicit-input-only contract binding PE-12 reconciliation_review
to position/order state reconciliation and PE-16 durable primary evidence semantics.
Static integration only — no reconciliation execution, network, testnet, runtime, orders,
evidence persistence, or authority lift.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.ops.primary_evidence_retention_v0 import (
    MANIFEST_FILENAME,
    is_under_tmp,
)
from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_DESCRIPTORS,
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_RECONCILIATION_REVIEW,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
    SPOT_INSTRUMENTS,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    ARCHIVE_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    ENVIRONMENT_TESTNET,
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
    PRIMARY_EVIDENCE_OWNER,
    RECONCILIATION_OWNER,
)
from src.ops.recon.models import BalanceSnapshot, DriftReport, PositionSnapshot
from src.ops.recon.reconcile import ReconTolerances, reconcile

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_POSITION_ORDER_RECONCILIATION_PRIMARY_EVIDENCE_INTEGRATION_CONTRACT_V0=true"
CONTRACT_VERSION = (
    "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration.v0"
)
SERIALIZATION_VERSION = "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration.serialization.v0"
HASH_ALGORITHM = "sha256"
REPOSITORY_IDENTITY = "Peak_Trade"
PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION = "primary_evidence_retention.v0"

CLASSIFICATION_RECONCILED = "reconciled"
CLASSIFICATION_PARTIAL = "partial"
CLASSIFICATION_AMBIGUOUS = "ambiguous"
CLASSIFICATION_UNRESOLVED = "unresolved"

GLOBAL_RECONCILIATION_READINESS = False
CONTRACT_IMPLEMENTATION_ONLY = True
OPERATIVE_RECONCILIATION_EXECUTED = False
PRIMARY_EVIDENCE_PACKAGE_CREATED = False
PRIMARY_EVIDENCE_RUN_EXECUTED = False
POSITION_STATE_QUERIED = False
ORDER_STATE_QUERIED = False
EXCHANGE_STATE_QUERIED = False
NETWORK_RUN_STARTED = False
TESTNET_RUN_STARTED = False
LIFECYCLE_TRANSITION_EXECUTED = False
AUTHORITY_LIFT = False

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_INSTRUMENT_FRAGMENTS = ("BTC/EUR", "ETH/EUR", "BTCUSDT", "XBTUSD", "PF_XBT")

ARTIFACT_POSITION_STATE_SNAPSHOT = "POSITION_STATE_SNAPSHOT.json"
ARTIFACT_ORDER_STATE_SNAPSHOT = "ORDER_STATE_SNAPSHOT.json"
ARTIFACT_ADAPTER_LIFECYCLE_STATE = "ADAPTER_LIFECYCLE_STATE.json"
ARTIFACT_RECONCILIATION_INPUT = "RECONCILIATION_INPUT.json"
ARTIFACT_RECONCILIATION_RESULT = "RECONCILIATION_RESULT.json"
ARTIFACT_RECONCILIATION_PROOF = "RECONCILIATION_PROOF.json"
ARTIFACT_PRIMARY_EVIDENCE_BINDING = "PRIMARY_EVIDENCE_BINDING.json"
ARTIFACT_SAFETY_SNAPSHOT = "SAFETY_SNAPSHOT.json"
ARTIFACT_PACKAGE_METADATA = "PACKAGE_METADATA.json"
ARTIFACT_PACKAGE_SUMMARY = "PACKAGE_SUMMARY.md"

REQUIRED_ARTIFACT_FILENAMES: tuple[str, ...] = (
    ARTIFACT_POSITION_STATE_SNAPSHOT,
    ARTIFACT_ORDER_STATE_SNAPSHOT,
    ARTIFACT_ADAPTER_LIFECYCLE_STATE,
    ARTIFACT_RECONCILIATION_INPUT,
    ARTIFACT_RECONCILIATION_RESULT,
    ARTIFACT_RECONCILIATION_PROOF,
    ARTIFACT_PRIMARY_EVIDENCE_BINDING,
    ARTIFACT_SAFETY_SNAPSHOT,
    ARTIFACT_PACKAGE_METADATA,
    ARTIFACT_PACKAGE_SUMMARY,
    MANIFEST_FILENAME,
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe16_archive": ARCHIVE_CONTRACT_VERSION,
    "pe16_primary_evidence_retention": PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION,
    "integration": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe16_archive: str
    pe16_primary_evidence_retention: str
    integration: str


@dataclass(frozen=True)
class PositionStateBinding:
    snapshot_id: str
    snapshot_digest: str
    instrument: str
    market_type: str
    quantity: float
    side: str


@dataclass(frozen=True)
class OrderRecord:
    order_id: str
    instrument: str
    side: str
    quantity: float
    status: str


@dataclass(frozen=True)
class OrderStateBinding:
    snapshot_id: str
    snapshot_digest: str
    orders: tuple[OrderRecord, ...]


@dataclass(frozen=True)
class AdapterLifecycleStateBinding:
    state_id: str
    state_digest: str
    adapter_id: str
    assigned_lifecycle_phase: str


@dataclass(frozen=True)
class ReconciliationStateBinding:
    expected_position: PositionStateBinding
    observed_position: PositionStateBinding
    expected_orders: tuple[OrderRecord, ...]
    observed_orders: tuple[OrderRecord, ...]
    input_digest: str
    result_digest: str
    classification: str
    reconciled: bool
    unresolved_count: int
    mismatch_count: int
    orphaned_order_count: int
    duplicate_order_count: int
    orphaned_position_count: int


@dataclass(frozen=True)
class ManifestEntry:
    digest: str
    relative_path: str


@dataclass(frozen=True)
class PrimaryEvidenceBindingInput:
    retention_contract_version: str
    durable_archive_root: str
    archive_identity: str
    expected_artifact_filenames: tuple[str, ...]
    manifest_proof_identity: str
    manifest_digest: str
    manifest_verify_rc: int
    manifest_entries: tuple[ManifestEntry, ...]


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
class ReconciliationPrimaryEvidenceIntegrationInput:
    source_revision: str
    repository_identity: str
    adapter_id: str
    instrument: str
    market_type: str
    contract_versions: ContractVersionsInput
    position_state: PositionStateBinding
    order_state: OrderStateBinding
    adapter_lifecycle_state: AdapterLifecycleStateBinding
    reconciliation_binding: ReconciliationStateBinding
    lifecycle_matrix_proof: LifecycleMatrixProof
    primary_evidence_binding: PrimaryEvidenceBindingInput
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
    from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
        LIFECYCLE_PHASE_DESCRIPTORS as _DESCRIPTORS,
    )

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
            for phase_id, descriptor in sorted(_DESCRIPTORS.items())
        },
    }
    return hashlib.sha256(
        json.dumps(matrix, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _order_record_dict(order: OrderRecord) -> dict[str, Any]:
    return {
        "instrument": order.instrument,
        "order_id": order.order_id,
        "quantity": order.quantity,
        "side": order.side,
        "status": order.status,
    }


def _position_binding_dict(position: PositionStateBinding, *, include_digest: bool = True) -> dict[str, Any]:
    data = asdict(position)
    if not include_digest:
        data.pop("snapshot_digest", None)
    return data


def serialize_position_state_canonical(position: PositionStateBinding) -> str:
    return json.dumps(
        _position_binding_dict(position, include_digest=False),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_position_state_digest(position: PositionStateBinding) -> str:
    return hashlib.sha256(serialize_position_state_canonical(position).encode("utf-8")).hexdigest()


def serialize_order_state_canonical(order_state: OrderStateBinding) -> str:
    payload = {
        "orders": [_order_record_dict(order) for order in order_state.orders],
        "snapshot_id": order_state.snapshot_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_order_state_digest(order_state: OrderStateBinding) -> str:
    return hashlib.sha256(serialize_order_state_canonical(order_state).encode("utf-8")).hexdigest()


def serialize_adapter_lifecycle_state_canonical(binding: AdapterLifecycleStateBinding) -> str:
    payload = {
        "adapter_id": binding.adapter_id,
        "assigned_lifecycle_phase": binding.assigned_lifecycle_phase,
        "state_id": binding.state_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_adapter_lifecycle_state_digest(binding: AdapterLifecycleStateBinding) -> str:
    return hashlib.sha256(
        serialize_adapter_lifecycle_state_canonical(binding).encode("utf-8")
    ).hexdigest()


def _reconciliation_input_payload(
    *,
    expected_position: PositionStateBinding,
    observed_position: PositionStateBinding,
    expected_orders: tuple[OrderRecord, ...],
    observed_orders: tuple[OrderRecord, ...],
) -> dict[str, Any]:
    return {
        "expected_orders": [_order_record_dict(order) for order in expected_orders],
        "expected_position": _position_binding_dict(expected_position, include_digest=False),
        "observed_orders": [_order_record_dict(order) for order in observed_orders],
        "observed_position": _position_binding_dict(observed_position, include_digest=False),
        "reconciliation_owner": RECONCILIATION_OWNER,
    }


def serialize_reconciliation_input_canonical(
    *,
    expected_position: PositionStateBinding,
    observed_position: PositionStateBinding,
    expected_orders: tuple[OrderRecord, ...],
    observed_orders: tuple[OrderRecord, ...],
) -> str:
    return json.dumps(
        _reconciliation_input_payload(
            expected_position=expected_position,
            observed_position=observed_position,
            expected_orders=expected_orders,
            observed_orders=observed_orders,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_reconciliation_input_digest(
    *,
    expected_position: PositionStateBinding,
    observed_position: PositionStateBinding,
    expected_orders: tuple[OrderRecord, ...],
    observed_orders: tuple[OrderRecord, ...],
) -> str:
    return hashlib.sha256(
        serialize_reconciliation_input_canonical(
            expected_position=expected_position,
            observed_position=observed_position,
            expected_orders=expected_orders,
            observed_orders=observed_orders,
        ).encode("utf-8")
    ).hexdigest()


def evaluate_order_reconciliation_static(
    *,
    expected_orders: tuple[OrderRecord, ...],
    observed_orders: tuple[OrderRecord, ...],
    instrument: str,
) -> dict[str, Any]:
    """Static order reconciliation classification (explicit inputs only)."""
    fail_reasons: list[str] = []
    duplicate_order_count = 0
    orphaned_order_count = 0
    mismatch_count = 0
    unresolved_count = 0

    observed_ids = [order.order_id for order in observed_orders]
    if len(observed_ids) != len(set(observed_ids)):
        duplicate_order_count = len(observed_ids) - len(set(observed_ids))
        fail_reasons.append("duplicate order_id in observed orders")

    expected_by_id = {order.order_id: order for order in expected_orders}
    observed_by_id: dict[str, OrderRecord] = {}
    for order in observed_orders:
        if order.order_id in observed_by_id:
            continue
        observed_by_id[order.order_id] = order

    for order_id, expected in expected_by_id.items():
        observed = observed_by_id.get(order_id)
        if observed is None:
            orphaned_order_count += 1
            fail_reasons.append(f"orphaned expected order: {order_id!r}")
            continue
        if expected.instrument != instrument or observed.instrument != instrument:
            mismatch_count += 1
            fail_reasons.append(f"instrument mismatch for order {order_id!r}")
        if expected.side != observed.side:
            mismatch_count += 1
            fail_reasons.append(f"contradictory side for order {order_id!r}")
        if expected.quantity != observed.quantity:
            mismatch_count += 1
            fail_reasons.append(f"quantity mismatch for order {order_id!r}")
        if expected.status != observed.status:
            mismatch_count += 1
            fail_reasons.append(f"status mismatch for order {order_id!r}")

    for order_id in observed_by_id:
        if order_id not in expected_by_id:
            orphaned_order_count += 1
            fail_reasons.append(f"orphaned observed order: {order_id!r}")

    if fail_reasons:
        if duplicate_order_count > 0 or mismatch_count > 0:
            classification = CLASSIFICATION_AMBIGUOUS
        elif orphaned_order_count > 0:
            classification = CLASSIFICATION_PARTIAL
        else:
            classification = CLASSIFICATION_UNRESOLVED
        unresolved_count = duplicate_order_count + orphaned_order_count + mismatch_count
        reconciled = False
    else:
        classification = CLASSIFICATION_RECONCILED
        reconciled = True

    return {
        "classification": classification,
        "reconciled": reconciled,
        "unresolved_count": unresolved_count,
        "mismatch_count": mismatch_count,
        "orphaned_order_count": orphaned_order_count,
        "duplicate_order_count": duplicate_order_count,
        "fail_reasons": _sorted_unique(fail_reasons),
    }


def evaluate_position_reconciliation_static(
    *,
    expected_position: PositionStateBinding,
    observed_position: PositionStateBinding,
) -> tuple[DriftReport, int]:
    """Reuse src.ops.recon.reconcile for position drift detection."""
    expected_snapshot = PositionSnapshot(
        epoch=0,
        positions={expected_position.instrument: expected_position.quantity},
    )
    observed_snapshot = PositionSnapshot(
        epoch=0,
        positions={observed_position.instrument: observed_position.quantity},
    )
    empty_balances_expected = BalanceSnapshot(epoch=0, balances={})
    empty_balances_observed = BalanceSnapshot(epoch=0, balances={})
    drift_report = reconcile(
        empty_balances_expected,
        empty_balances_observed,
        expected_positions=expected_snapshot,
        observed_positions=observed_snapshot,
        tolerances=ReconTolerances(position_abs=0.0),
    )
    orphaned_position_count = 0
    if expected_position.instrument != observed_position.instrument:
        orphaned_position_count = 1
    elif not drift_report.ok:
        orphaned_position_count = 1
    return drift_report, orphaned_position_count


def evaluate_reconciliation_static(
    *,
    expected_position: PositionStateBinding,
    observed_position: PositionStateBinding,
    expected_orders: tuple[OrderRecord, ...],
    observed_orders: tuple[OrderRecord, ...],
    instrument: str,
) -> dict[str, Any]:
    """Evaluate full position/order reconciliation from explicit bindings."""
    order_result = evaluate_order_reconciliation_static(
        expected_orders=expected_orders,
        observed_orders=observed_orders,
        instrument=instrument,
    )
    position_drift, orphaned_position_count = evaluate_position_reconciliation_static(
        expected_position=expected_position,
        observed_position=observed_position,
    )
    fail_reasons = list(order_result["fail_reasons"])
    if expected_position.instrument != observed_position.instrument:
        fail_reasons.append("position instrument mismatch")
    if not position_drift.ok:
        fail_reasons.extend(position_drift.drifts)

    reconciled = (
        order_result["reconciled"]
        and not fail_reasons
        and orphaned_position_count == 0
        and order_result["classification"] == CLASSIFICATION_RECONCILED
    )
    classification = order_result["classification"]
    if fail_reasons and classification == CLASSIFICATION_RECONCILED:
        classification = CLASSIFICATION_UNRESOLVED

    unresolved_count = (
        order_result["unresolved_count"] + orphaned_position_count + len(position_drift.drifts)
    )
    mismatch_count = order_result["mismatch_count"] + len(position_drift.drifts)

    result_payload = {
        "classification": classification,
        "duplicate_order_count": order_result["duplicate_order_count"],
        "mismatch_count": mismatch_count,
        "orphaned_order_count": order_result["orphaned_order_count"],
        "orphaned_position_count": orphaned_position_count,
        "reconciled": reconciled,
        "reconciliation_owner": RECONCILIATION_OWNER,
        "unresolved_count": unresolved_count,
    }
    result_digest = hashlib.sha256(
        json.dumps(result_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        **result_payload,
        "result_digest": result_digest,
        "fail_reasons": _sorted_unique(fail_reasons),
    }


def compute_manifest_digest(entries: tuple[ManifestEntry, ...]) -> str:
    lines = [
        f"{entry.digest}  {entry.relative_path}"
        for entry in sorted(entries, key=lambda e: e.relative_path)
    ]
    body = "\n".join(lines) + ("\n" if lines else "")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def serialize_primary_evidence_binding_canonical(binding: PrimaryEvidenceBindingInput) -> str:
    payload = {
        "archive_identity": binding.archive_identity,
        "durable_archive_root": binding.durable_archive_root,
        "expected_artifact_filenames": list(binding.expected_artifact_filenames),
        "manifest_digest": binding.manifest_digest,
        "manifest_entries": [
            {"digest": entry.digest, "relative_path": entry.relative_path}
            for entry in sorted(binding.manifest_entries, key=lambda e: e.relative_path)
        ],
        "manifest_proof_identity": binding.manifest_proof_identity,
        "manifest_verify_rc": binding.manifest_verify_rc,
        "primary_evidence_owner": PRIMARY_EVIDENCE_OWNER,
        "retention_contract_version": binding.retention_contract_version,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_primary_evidence_binding_digest(binding: PrimaryEvidenceBindingInput) -> str:
    return hashlib.sha256(
        serialize_primary_evidence_binding_canonical(binding).encode("utf-8")
    ).hexdigest()


def _integration_input_dict(
    integration_input: ReconciliationPrimaryEvidenceIntegrationInput,
) -> dict[str, Any]:
    return {
        "adapter_id": integration_input.adapter_id,
        "adapter_lifecycle_state": asdict(integration_input.adapter_lifecycle_state),
        "contract_versions": asdict(integration_input.contract_versions),
        "environment": integration_input.environment,
        "futures_only": integration_input.futures_only,
        "instrument": integration_input.instrument,
        "integration_contract_version": CONTRACT_VERSION,
        "lifecycle_matrix_proof": asdict(integration_input.lifecycle_matrix_proof),
        "market_type": integration_input.market_type,
        "non_authorizing": integration_input.non_authorizing,
        "order_state": {
            "orders": [_order_record_dict(order) for order in integration_input.order_state.orders],
            "snapshot_digest": integration_input.order_state.snapshot_digest,
            "snapshot_id": integration_input.order_state.snapshot_id,
        },
        "position_state": _position_binding_dict(integration_input.position_state),
        "primary_evidence_binding": serialize_primary_evidence_binding_canonical(
            integration_input.primary_evidence_binding
        ),
        "reconciliation_binding": asdict(integration_input.reconciliation_binding),
        "repository_identity": integration_input.repository_identity,
        "safety_snapshot": asdict(integration_input.safety_snapshot),
        "serialization_version": SERIALIZATION_VERSION,
        "source_revision": integration_input.source_revision,
    }


def serialize_integration_input_canonical(
    integration_input: ReconciliationPrimaryEvidenceIntegrationInput,
) -> str:
    return json.dumps(
        _integration_input_dict(integration_input), sort_keys=True, separators=(",", ":")
    )


def compute_integration_input_digest(
    integration_input: ReconciliationPrimaryEvidenceIntegrationInput,
) -> str:
    return hashlib.sha256(
        serialize_integration_input_canonical(integration_input).encode("utf-8")
    ).hexdigest()


def _integration_proof_dict(
    integration_input: ReconciliationPrimaryEvidenceIntegrationInput,
    *,
    integration_proof_digest: str | None = None,
) -> dict[str, Any]:
    payload = {
        "adapter_id": integration_input.adapter_id,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "durable_primary_evidence_binding_proven": False,
        "global_reconciliation_readiness": GLOBAL_RECONCILIATION_READINESS,
        "integration_contract_version": CONTRACT_VERSION,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "lifecycle_matrix_digest": integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest,
        "operative_reconciliation_executed": OPERATIVE_RECONCILIATION_EXECUTED,
        "pe12_reconciliation_review_static_integration_proven": False,
        "primary_evidence_package_created": PRIMARY_EVIDENCE_PACKAGE_CREATED,
        "primary_evidence_run_executed": PRIMARY_EVIDENCE_RUN_EXECUTED,
        "reconciliation_classification": integration_input.reconciliation_binding.classification,
        "reconciliation_result_digest": integration_input.reconciliation_binding.result_digest,
        "source_revision": integration_input.source_revision,
        "non_authorizing": True,
    }
    if integration_proof_digest is not None:
        payload["integration_proof_digest"] = integration_proof_digest
    return payload


def serialize_integration_proof_canonical(
    integration_input: ReconciliationPrimaryEvidenceIntegrationInput,
) -> str:
    return json.dumps(
        _integration_proof_dict(integration_input),
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_integration_proof_digest(
    integration_input: ReconciliationPrimaryEvidenceIntegrationInput,
) -> str:
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
    upper = instrument.upper()
    for fragment in _FORBIDDEN_INSTRUMENT_FRAGMENTS:
        if fragment.upper() in upper:
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


def _validate_archive_root_identity(archive_root: str, archive_identity: str) -> list[str]:
    fail_reasons: list[str] = []
    if not archive_root:
        fail_reasons.append("durable_archive_root required")
    else:
        root_path = Path(archive_root)
        if is_under_tmp(root_path):
            fail_reasons.append("durable_archive_root must be outside /tmp")
    if not archive_identity:
        fail_reasons.append("archive_identity required")
    elif archive_identity.startswith("/"):
        fail_reasons.append("archive_identity must be relative")
    elif ".." in Path(archive_identity).parts:
        fail_reasons.append("archive_identity must not contain '..'")
    combined = f"{archive_root.rstrip('/')}/{archive_identity}".replace("\\", "/")
    if "/../" in f"/{combined}/" or combined.endswith("/.."):
        fail_reasons.append("archive path traversal rejected")
    return fail_reasons


def validate_primary_evidence_binding(binding: PrimaryEvidenceBindingInput) -> list[str]:
    """Fail-closed validation of explicit PE-16 primary evidence binding (no persistence)."""
    fail_reasons: list[str] = []
    if binding.retention_contract_version != PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION:
        fail_reasons.append(
            f"retention_contract_version must be {PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION!r}"
        )
    fail_reasons.extend(
        _validate_archive_root_identity(binding.durable_archive_root, binding.archive_identity)
    )

    missing = sorted(set(REQUIRED_ARTIFACT_FILENAMES) - set(binding.expected_artifact_filenames))
    if missing:
        fail_reasons.append(f"missing required artifact filenames: {missing}")

    if binding.manifest_verify_rc != 0:
        fail_reasons.append("manifest_verify_rc must be 0")

    if not binding.manifest_proof_identity:
        fail_reasons.append("manifest_proof_identity required")
    elif not _valid_sha256_digest(binding.manifest_proof_identity):
        fail_reasons.append("manifest_proof_identity must be 64-char lowercase sha256 hex")

    if not binding.manifest_digest:
        fail_reasons.append("manifest_digest required")
    elif not _valid_sha256_digest(binding.manifest_digest):
        fail_reasons.append("manifest_digest must be 64-char lowercase sha256 hex")

    entry_paths = [entry.relative_path for entry in binding.manifest_entries]
    if len(entry_paths) != len(set(entry_paths)):
        fail_reasons.append("duplicate manifest entry paths")
    for entry in binding.manifest_entries:
        if not _valid_sha256_digest(entry.digest):
            fail_reasons.append(f"invalid manifest entry digest for {entry.relative_path!r}")
        if entry.relative_path.startswith("/"):
            fail_reasons.append(f"absolute manifest path rejected: {entry.relative_path!r}")
        if ".." in Path(entry.relative_path).parts:
            fail_reasons.append(
                f"path traversal rejected in manifest entry: {entry.relative_path!r}"
            )

    computed_manifest_digest = compute_manifest_digest(binding.manifest_entries)
    if binding.manifest_digest != computed_manifest_digest:
        fail_reasons.append("manifest_digest mismatch")

    if binding.manifest_proof_identity != computed_manifest_digest:
        fail_reasons.append("manifest_proof_identity mismatch with computed manifest digest")

    return _sorted_unique(fail_reasons)


def validate_reconciliation_primary_evidence_integration_input(
    integration_input: ReconciliationPrimaryEvidenceIntegrationInput,
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

    position = integration_input.position_state
    if not position.snapshot_id:
        fail_reasons.append("position_state: snapshot_id required")
    if not position.snapshot_digest:
        fail_reasons.append("position_state: snapshot_digest required")
    elif not _valid_sha256_digest(position.snapshot_digest):
        fail_reasons.append("position_state: snapshot_digest must be 64-char lowercase sha256 hex")
    elif position.snapshot_digest != compute_position_state_digest(position):
        fail_reasons.append("position_state: snapshot_digest mismatch")
    if position.instrument != integration_input.instrument:
        fail_reasons.append("position_state: instrument mismatch with integration instrument")
    fail_reasons.extend(_validate_instrument_scope(position.instrument, position.market_type))

    order_state = integration_input.order_state
    if not order_state.snapshot_id:
        fail_reasons.append("order_state: snapshot_id required")
    if not order_state.snapshot_digest:
        fail_reasons.append("order_state: snapshot_digest required")
    elif not _valid_sha256_digest(order_state.snapshot_digest):
        fail_reasons.append("order_state: snapshot_digest must be 64-char lowercase sha256 hex")
    elif order_state.snapshot_digest != compute_order_state_digest(order_state):
        fail_reasons.append("order_state: snapshot_digest mismatch")
    for order in order_state.orders:
        if order.instrument != integration_input.instrument:
            fail_reasons.append(f"order_state: instrument mismatch for order {order.order_id!r}")

    lifecycle = integration_input.adapter_lifecycle_state
    if not lifecycle.state_id:
        fail_reasons.append("adapter_lifecycle_state: state_id required")
    if not lifecycle.state_digest:
        fail_reasons.append("adapter_lifecycle_state: state_digest required")
    elif not _valid_sha256_digest(lifecycle.state_digest):
        fail_reasons.append(
            "adapter_lifecycle_state: state_digest must be 64-char lowercase sha256 hex"
        )
    elif lifecycle.state_digest != compute_adapter_lifecycle_state_digest(lifecycle):
        fail_reasons.append("adapter_lifecycle_state: state_digest mismatch")
    if lifecycle.adapter_id != integration_input.adapter_id:
        fail_reasons.append("adapter_lifecycle_state: adapter_id mismatch")

    matrix = integration_input.lifecycle_matrix_proof
    if matrix.pe12_contract_version != PE12_CONTRACT_VERSION:
        fail_reasons.append(
            f"lifecycle_matrix_proof: pe12_contract_version must be {PE12_CONTRACT_VERSION!r}"
        )
    if not matrix.lifecycle_matrix_digest:
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest required")
    elif matrix.lifecycle_matrix_digest != compute_lifecycle_matrix_digest():
        fail_reasons.append("lifecycle_matrix_proof: lifecycle_matrix_digest mismatch")
    if matrix.assigned_lifecycle_phase != PHASE_RECONCILIATION_REVIEW:
        fail_reasons.append(
            f"lifecycle_matrix_proof: assigned_lifecycle_phase must be {PHASE_RECONCILIATION_REVIEW!r}"
        )
    elif matrix.assigned_lifecycle_phase not in LIFECYCLE_PHASE_DESCRIPTORS:
        fail_reasons.append("lifecycle_matrix_proof: unsupported lifecycle phase")
    if lifecycle.assigned_lifecycle_phase != PHASE_RECONCILIATION_REVIEW:
        fail_reasons.append(
            f"adapter_lifecycle_state: assigned_lifecycle_phase must be {PHASE_RECONCILIATION_REVIEW!r}"
        )

    recon = integration_input.reconciliation_binding
    computed_input_digest = compute_reconciliation_input_digest(
        expected_position=recon.expected_position,
        observed_position=recon.observed_position,
        expected_orders=recon.expected_orders,
        observed_orders=recon.observed_orders,
    )
    if recon.input_digest != computed_input_digest:
        fail_reasons.append("reconciliation_binding: input_digest mismatch")

    static_recon = evaluate_reconciliation_static(
        expected_position=recon.expected_position,
        observed_position=recon.observed_position,
        expected_orders=recon.expected_orders,
        observed_orders=recon.observed_orders,
        instrument=integration_input.instrument,
    )
    if recon.result_digest != static_recon["result_digest"]:
        fail_reasons.append("reconciliation_binding: result_digest mismatch")
    if recon.classification != static_recon["classification"]:
        fail_reasons.append("reconciliation_binding: classification mismatch")
    if recon.reconciled != static_recon["reconciled"]:
        fail_reasons.append("reconciliation_binding: reconciled flag mismatch")
    if recon.unresolved_count != static_recon["unresolved_count"]:
        fail_reasons.append("reconciliation_binding: unresolved_count mismatch")
    if recon.mismatch_count != static_recon["mismatch_count"]:
        fail_reasons.append("reconciliation_binding: mismatch_count mismatch")
    if recon.orphaned_order_count != static_recon["orphaned_order_count"]:
        fail_reasons.append("reconciliation_binding: orphaned_order_count mismatch")
    if recon.duplicate_order_count != static_recon["duplicate_order_count"]:
        fail_reasons.append("reconciliation_binding: duplicate_order_count mismatch")
    if recon.orphaned_position_count != static_recon["orphaned_position_count"]:
        fail_reasons.append("reconciliation_binding: orphaned_position_count mismatch")

    fail_reasons.extend(
        validate_primary_evidence_binding(integration_input.primary_evidence_binding)
    )
    fail_reasons.extend(_validate_safety_snapshot(integration_input.safety_snapshot))

    if integration_input.futures_only is not True:
        fail_reasons.append("futures_only must be true")
    if integration_input.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if integration_input.non_authorizing is not True:
        fail_reasons.append("non_authorizing must be true")

    return _sorted_unique(fail_reasons)


def evaluate_position_order_reconciliation_primary_evidence_integration(
    integration_input: ReconciliationPrimaryEvidenceIntegrationInput,
    *,
    expected_source_revision: str | None = None,
    expected_position_digest: str | None = None,
    expected_order_digest: str | None = None,
    expected_lifecycle_state_digest: str | None = None,
    reconciled_claim_without_proof_chain: bool = False,
) -> dict[str, Any]:
    """Evaluate explicit PE-12/PE-16 reconciliation primary evidence integration proof."""
    fail_reasons = validate_reconciliation_primary_evidence_integration_input(integration_input)

    if expected_source_revision is not None:
        if integration_input.source_revision != expected_source_revision:
            fail_reasons.append("source_revision mismatch with expected revision")

    if expected_position_digest is not None:
        if integration_input.position_state.snapshot_digest != expected_position_digest:
            fail_reasons.append("position_state snapshot_digest mismatch")

    if expected_order_digest is not None:
        if integration_input.order_state.snapshot_digest != expected_order_digest:
            fail_reasons.append("order_state snapshot_digest mismatch")

    if expected_lifecycle_state_digest is not None:
        if (
            integration_input.adapter_lifecycle_state.state_digest
            != expected_lifecycle_state_digest
        ):
            fail_reasons.append("adapter_lifecycle_state state_digest mismatch")

    recon = integration_input.reconciliation_binding
    if reconciled_claim_without_proof_chain and recon.reconciled:
        fail_reasons.append("reconciled=true without full proof chain is insufficient")

    if not fail_reasons and not recon.reconciled:
        fail_reasons.append("unresolved reconciliation")

    fail_reasons = _sorted_unique(fail_reasons)
    integration_pass = not fail_reasons
    pe12_proven = integration_pass
    durable_binding_proven = integration_pass

    return {
        "integration_pass": integration_pass,
        "integration_input_digest": compute_integration_input_digest(integration_input),
        "integration_proof_digest": (
            compute_integration_proof_digest(integration_input) if integration_pass else None
        ),
        "reconciliation_classification": recon.classification,
        "reconciliation_result_digest": recon.result_digest,
        "reconciled": recon.reconciled and integration_pass,
        "pe12_reconciliation_review_static_integration_proven": pe12_proven,
        "durable_primary_evidence_binding_proven": durable_binding_proven,
        "global_reconciliation_readiness": GLOBAL_RECONCILIATION_READINESS,
        "contract_implementation_only": CONTRACT_IMPLEMENTATION_ONLY,
        "operative_reconciliation_executed": OPERATIVE_RECONCILIATION_EXECUTED,
        "primary_evidence_package_created": PRIMARY_EVIDENCE_PACKAGE_CREATED,
        "primary_evidence_run_executed": PRIMARY_EVIDENCE_RUN_EXECUTED,
        "position_state_queried": POSITION_STATE_QUERIED,
        "order_state_queried": ORDER_STATE_QUERIED,
        "exchange_state_queried": EXCHANGE_STATE_QUERIED,
        "network_run_started": NETWORK_RUN_STARTED,
        "testnet_run_started": TESTNET_RUN_STARTED,
        "lifecycle_transition_executed": LIFECYCLE_TRANSITION_EXECUTED,
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


def _default_order_record(
    *,
    order_id: str = "offline-order-001",
    instrument: str = "PF_ETHUSD",
) -> OrderRecord:
    return OrderRecord(
        order_id=order_id,
        instrument=instrument,
        side="buy",
        quantity=1.0,
        status="open",
    )


def _default_position_binding(*, instrument: str = "PF_ETHUSD") -> PositionStateBinding:
    binding = PositionStateBinding(
        snapshot_id="position-snapshot-001",
        snapshot_digest="",
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        quantity=0.0,
        side="flat",
    )
    return PositionStateBinding(
        snapshot_id=binding.snapshot_id,
        snapshot_digest=compute_position_state_digest(binding),
        instrument=binding.instrument,
        market_type=binding.market_type,
        quantity=binding.quantity,
        side=binding.side,
    )


def _default_manifest_entries(
    *,
    position_digest: str,
    order_digest: str,
    lifecycle_digest: str,
    reconciliation_input_digest: str,
    reconciliation_result_digest: str,
) -> tuple[ManifestEntry, ...]:
    artifact_digests = {
        ARTIFACT_POSITION_STATE_SNAPSHOT: position_digest,
        ARTIFACT_ORDER_STATE_SNAPSHOT: order_digest,
        ARTIFACT_ADAPTER_LIFECYCLE_STATE: lifecycle_digest,
        ARTIFACT_RECONCILIATION_INPUT: reconciliation_input_digest,
        ARTIFACT_RECONCILIATION_RESULT: reconciliation_result_digest,
        ARTIFACT_RECONCILIATION_PROOF: "f" * 64,
        ARTIFACT_PRIMARY_EVIDENCE_BINDING: "e" * 64,
        ARTIFACT_SAFETY_SNAPSHOT: "d" * 64,
        ARTIFACT_PACKAGE_METADATA: "c" * 64,
        ARTIFACT_PACKAGE_SUMMARY: "b" * 64,
    }
    entries = tuple(
        ManifestEntry(digest=digest, relative_path=filename)
        for filename, digest in sorted(artifact_digests.items())
    )
    return entries


def default_minimal_primary_evidence_binding(
    *,
    durable_archive_root: str = "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z",
    archive_identity: str = "bounded_futures_testnet_reconciliation_proof/offline-v0",
    manifest_entries: tuple[ManifestEntry, ...] | None = None,
) -> PrimaryEvidenceBindingInput:
    entries = manifest_entries or _default_manifest_entries(
        position_digest="1" * 64,
        order_digest="2" * 64,
        lifecycle_digest="3" * 64,
        reconciliation_input_digest="4" * 64,
        reconciliation_result_digest="5" * 64,
    )
    manifest_digest = compute_manifest_digest(entries)
    return PrimaryEvidenceBindingInput(
        retention_contract_version=PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION,
        durable_archive_root=durable_archive_root,
        archive_identity=archive_identity,
        expected_artifact_filenames=REQUIRED_ARTIFACT_FILENAMES,
        manifest_proof_identity=manifest_digest,
        manifest_digest=manifest_digest,
        manifest_verify_rc=0,
        manifest_entries=entries,
    )


def default_minimal_integration_input(
    *,
    source_revision: str = "abcdef0123456789abcdef0123456789abcdef01",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    instrument: str = "PF_ETHUSD",
    lifecycle_state_digest: str | None = None,
) -> ReconciliationPrimaryEvidenceIntegrationInput:
    """Minimal valid futures-generic integration input for offline tests."""
    position = _default_position_binding(instrument=instrument)
    order = _default_order_record(instrument=instrument)
    order_state_binding = OrderStateBinding(
        snapshot_id="order-snapshot-001",
        snapshot_digest="",
        orders=(order,),
    )
    order_state = OrderStateBinding(
        snapshot_id=order_state_binding.snapshot_id,
        snapshot_digest=compute_order_state_digest(order_state_binding),
        orders=order_state_binding.orders,
    )
    lifecycle_binding = AdapterLifecycleStateBinding(
        state_id="lifecycle-state-001",
        state_digest="",
        adapter_id=adapter_id,
        assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
    )
    lifecycle = AdapterLifecycleStateBinding(
        state_id=lifecycle_binding.state_id,
        state_digest=lifecycle_state_digest
        or compute_adapter_lifecycle_state_digest(lifecycle_binding),
        adapter_id=lifecycle_binding.adapter_id,
        assigned_lifecycle_phase=lifecycle_binding.assigned_lifecycle_phase,
    )

    static_recon = evaluate_reconciliation_static(
        expected_position=position,
        observed_position=position,
        expected_orders=(order,),
        observed_orders=(order,),
        instrument=instrument,
    )
    recon_binding = ReconciliationStateBinding(
        expected_position=position,
        observed_position=position,
        expected_orders=(order,),
        observed_orders=(order,),
        input_digest=compute_reconciliation_input_digest(
            expected_position=position,
            observed_position=position,
            expected_orders=(order,),
            observed_orders=(order,),
        ),
        result_digest=static_recon["result_digest"],
        classification=static_recon["classification"],
        reconciled=static_recon["reconciled"],
        unresolved_count=static_recon["unresolved_count"],
        mismatch_count=static_recon["mismatch_count"],
        orphaned_order_count=static_recon["orphaned_order_count"],
        duplicate_order_count=static_recon["duplicate_order_count"],
        orphaned_position_count=static_recon["orphaned_position_count"],
    )

    manifest_entries = _default_manifest_entries(
        position_digest=position.snapshot_digest,
        order_digest=order_state.snapshot_digest,
        lifecycle_digest=lifecycle.state_digest,
        reconciliation_input_digest=recon_binding.input_digest,
        reconciliation_result_digest=recon_binding.result_digest,
    )
    evidence_binding = default_minimal_primary_evidence_binding(manifest_entries=manifest_entries)

    return ReconciliationPrimaryEvidenceIntegrationInput(
        source_revision=source_revision,
        repository_identity=REPOSITORY_IDENTITY,
        adapter_id=adapter_id,
        instrument=instrument,
        market_type=DEFAULT_MARKET_TYPE,
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe16_archive=ARCHIVE_CONTRACT_VERSION,
            pe16_primary_evidence_retention=PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION,
            integration=CONTRACT_VERSION,
        ),
        position_state=position,
        order_state=order_state,
        adapter_lifecycle_state=lifecycle,
        reconciliation_binding=recon_binding,
        lifecycle_matrix_proof=LifecycleMatrixProof(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            lifecycle_matrix_digest=compute_lifecycle_matrix_digest(),
            assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
            lifecycle_state_digest=lifecycle.state_digest,
        ),
        primary_evidence_binding=evidence_binding,
        safety_snapshot=default_minimal_safety_snapshot(),
    )
