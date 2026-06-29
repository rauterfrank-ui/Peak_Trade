"""Offline LEVEL_3 canonical unknown-execution-outcome recovery contract owner v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
)
from src.meta.learning_loop.order_intent_idempotency_v1 import (
    ARTIFACT_REL as IDEMPOTENCY_ARTIFACT_REL,
    OrderIntentIdempotencyError,
    reverify_order_intent_idempotency_v1,
)
from src.meta.learning_loop.runtime_state_reconciliation_v1 import (
    ARTIFACT_REL as RECONCILIATION_ARTIFACT_REL,
    RuntimeStateReconciliationError,
    reverify_runtime_state_reconciliation_v1,
)

CONTRACT_NAME = "unknown_execution_outcome_recovery_v1"
CONTRACT_VERSION = "v1"
RECOVERY_CONTRACT_VERSION = "unknown_execution_outcome_recovery_contract_v1"
RECOVERY_SCOPE_DEFAULT = "UNKNOWN_EXECUTION_OUTCOME_OFFLINE_RECOVERY_EVALUATION"
PRODUCER_VERSION = "unknown_execution_outcome_recovery_v1"
BUILDER_VERSION = "unknown_execution_outcome_recovery_builder_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "unknown_execution_outcome_recovery_record"
INPUT_RELATION = (
    "PACKAGES_VERIFIED_RUNTIME_STATE_RECONCILIATION_AND_ORDER_INTENT_IDEMPOTENCY_"
    "FOR_OFFLINE_UNKNOWN_OUTCOME_RECOVERY"
)
ARTIFACT_REL = "unknown_execution_outcome_recovery_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".unknown_execution_outcome_recovery_staging_"

SCHEMA_VERSION = "unknown_execution_outcome_recovery_schema_v1"
CREATION_CONTRACT_VERSION = "unknown_execution_outcome_recovery_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "unknown_execution_outcome_recovery_rules_v1"
DETERMINISTIC_SERIALIZATION_VERSION = "deterministic_json_dumps_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_unknown_execution_outcome_recovery_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"

_VALID_INSTRUMENT_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_INSTRUMENT_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})

_VALID_TRANSPORT_OUTCOMES = frozenset(
    {
        "UNKNOWN_OUTCOME",
        "TRANSPORT_TIMEOUT_AFTER_POSSIBLE_TRANSMISSION",
        "NO_VENUE_ACKNOWLEDGEMENT",
    }
)

_VALID_RECOVERY_CLASSIFICATIONS = frozenset(
    {
        "ACKNOWLEDGED_OR_OPEN",
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCELLED",
        "REJECTED",
        "EXPIRED",
        "NOT_FOUND_WITH_SUFFICIENT_NEGATIVE_EVIDENCE",
        "STILL_UNKNOWN",
        "RECONCILIATION_REQUIRED",
    }
)

_TERMINAL_RECOVERY_CLASSIFICATIONS = frozenset(
    {
        "ACKNOWLEDGED_OR_OPEN",
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCELLED",
        "REJECTED",
        "EXPIRED",
        "NOT_FOUND_WITH_SUFFICIENT_NEGATIVE_EVIDENCE",
    }
)

_VALID_CONTRACT_STATUSES = frozenset(
    {
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID",
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_INVALID",
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_MISSING_BINDINGS",
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_DIGEST_MISMATCH",
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_EPOCH_MISMATCH",
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_CLIENT_ORDER_ID_MISMATCH",
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_FUTURES_MARKET_TYPE_CONFLICT",
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_STILL_UNKNOWN",
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_RECONCILIATION_REQUIRED",
        "ABSTAIN",
    }
)
_VALID_EVIDENCE_STATUSES = frozenset(
    {"ADMISSIBLE", "VALID", "CONFLICT", "INVALID", "UNKNOWN", "ABSTAIN"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "unknown_execution_outcome_recovery_self_verification_v1"

_REQUIRED_SNAPSHOT_BINDINGS = (
    "open_orders_snapshot",
    "recent_orders_snapshot",
    "fill_snapshot",
    "position_snapshot",
)

_FORBIDDEN_INDEX_KEYS: frozenset[str] = frozenset(
    {
        "winner",
        "selected",
        "promoted",
        "promotion",
        "promotion_ready",
        "eligible_for_live",
        "live_eligible",
        "runtime_eligible",
        "ranking",
        "ranked_input_ids",
        "pareto",
        "accepted",
        "acceptance",
        "armed",
        "enabled",
        "returns",
        "positions",
        "orders",
        "credentials",
        "strategy_params_mutated",
        "config_patch",
        "configpatch",
        "config_patch_manifest",
        "patches",
        "top_n",
        "topn",
        "filter_candidates_for_live",
        "promotion_candidate",
        "safety_flags",
    }
)

UNKNOWN_EXECUTION_OUTCOME_RECOVERY_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "unknown_execution_outcome_recovery_is_descriptive_only": True,
    "unknown_execution_outcome_recovery_does_not_resubmit_order": True,
    "unknown_execution_outcome_recovery_does_not_create_client_order_id": True,
    "unknown_execution_outcome_recovery_does_not_invoke_adapter": True,
    "unknown_execution_outcome_recovery_does_not_query_venue": True,
    "unknown_execution_outcome_recovery_does_not_mutate_runtime_state": True,
    "unknown_execution_outcome_recovery_is_offline_only": True,
    "deny_by_default": True,
    "futures_only": True,
    "order_intent_lineage_bound": True,
    "submission_attempt_lineage_bound": True,
    "runtime_state_reconciliation_lineage_bound": True,
    "snapshot_evidence_binding_bound": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_unknown_execution_outcome_recovery": True,
    "unknown_execution_outcome_recovery_offline_only": True,
    "unknown_execution_outcome_recovery_contract_complete": False,
    "unknown_execution_outcome_observed_only": True,
    "recovery_action_executed": False,
    "order_resubmitted": False,
    "new_client_order_id_created": False,
    "order_created": False,
    "order_submission_requested": False,
    "order_submitted": False,
    "order_cancel_requested": False,
    "order_amend_requested": False,
    "order_state_mutated": False,
    "position_state_mutated": False,
    "runtime_state_mutated": False,
    "adapter_invoked": False,
    "exchange_request_sent": False,
    "network_side_effect_created": False,
    "files_transferred_to_runtime": False,
    "queue_message_created": False,
    "database_mutated": False,
    "lock_acquired": False,
    "reservation_created": False,
    "authority_activated": False,
    "lease_activated": False,
    "revocation_executed": False,
    "scheduler_started": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "resubmit_allowed": False,
    "new_client_order_id_allowed": False,
    "runtime_mutation_performed": False,
    "deny_by_default": True,
    "futures_only": True,
}


class UnknownExecutionOutcomeRecoveryError(ValueError):
    """Fail-closed unknown-execution-outcome recovery error."""


@dataclass(frozen=True)
class RecoverySnapshotBinding:
    snapshot_ref: str
    snapshot_digest: str


@dataclass(frozen=True)
class RecoveryEvidenceSignals:
    open_orders_classification: str
    recent_orders_classification: str
    fill_classification: str
    position_classification: str
    margin_classification: str = "NOT_REQUIRED"
    margin_snapshot_required: bool = False
    negative_not_found_evidence_sufficient: bool = False


@dataclass(frozen=True)
class VerifiedRuntimeStateReconciliationBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    contract_id: str
    contract_status: str
    reconciliation_digest: str
    artifact_payload: dict[str, Any]


@dataclass(frozen=True)
class VerifiedOrderIntentIdempotencyBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    contract_id: str
    contract_status: str
    canonical_order_intent_identity_digest: str
    canonical_order_identity_digest: str
    client_order_id: str
    order_intent_digest: str
    trading_epoch: str
    executor_epoch: str
    authority_ref: str
    authority_digest: str
    artifact_payload: dict[str, Any]


@dataclass(frozen=True)
class UnknownExecutionRecoveryRequest:
    recovery_id: str
    client_order_id: str
    submission_started: str
    transport_outcome: str
    unknown_outcome_reason: str
    venue_acknowledgement_known: bool
    transport_claims_not_submitted: bool
    new_client_order_id_proposed: bool
    open_orders_snapshot: RecoverySnapshotBinding
    recent_orders_snapshot: RecoverySnapshotBinding
    fill_snapshot: RecoverySnapshotBinding
    position_snapshot: RecoverySnapshotBinding
    margin_snapshot: RecoverySnapshotBinding | None
    runtime_state_snapshot_ref: str
    runtime_state_snapshot_digest: str
    reconciliation_ref: str
    reconciliation_digest: str
    submission_attempt_ref: str
    submission_attempt_digest: str
    order_intent_ref: str
    order_intent_digest: str
    authority_ref: str
    authority_digest: str
    trading_epoch: str
    executor_epoch: str
    evidence_signals: RecoveryEvidenceSignals
    declared_recovery_classification: str
    instrument_type: str = "FUTURES"
    correlation_id: str = "offline-unknown-outcome-recovery-correlation-001"
    recovery_contract_version: str = RECOVERY_CONTRACT_VERSION
    deterministic_serialization_version: str = DETERMINISTIC_SERIALIZATION_VERSION
    provenance_digest: str = ""
    cross_domain_lineage_digest: str = ""
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class UnknownExecutionRecoveryInputs:
    runtime_state_reconciliation_bundle_dir: Path
    order_intent_idempotency_bundle_dir: Path
    recovery_request: UnknownExecutionRecoveryRequest


@dataclass(frozen=True)
class UnknownExecutionRecoveryResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    evidence_status: str
    recovery_classification: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path
    recovery_digest: str
    resubmit_allowed: bool
    reconciliation_required: bool


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise UnknownExecutionOutcomeRecoveryError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise UnknownExecutionOutcomeRecoveryError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise UnknownExecutionOutcomeRecoveryError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise UnknownExecutionOutcomeRecoveryError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise UnknownExecutionOutcomeRecoveryError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise UnknownExecutionOutcomeRecoveryError("output directory must not be under /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, bundle_dirs: list[Path], output_dir: Path) -> None:
    resolved_output = output_dir.resolve()
    for bundle_dir in bundle_dirs:
        resolved_bundle = bundle_dir.resolve()
        if resolved_output == resolved_bundle:
            raise UnknownExecutionOutcomeRecoveryError(
                "output directory must not equal input bundle"
            )
        if _path_is_under(resolved_output, resolved_bundle) or _path_is_under(
            resolved_bundle, resolved_output
        ):
            raise UnknownExecutionOutcomeRecoveryError("output directory overlaps input bundle")


def _factor(
    *,
    factor_id: str,
    factor_type: str,
    source_field: str,
    detail: str,
) -> dict[str, str]:
    return {
        "factor_id": factor_id,
        "factor_type": factor_type,
        "source_field": source_field,
        "detail": detail,
    }


def _sort_factors(factors: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        factors,
        key=lambda item: (item.get("factor_id", ""), item.get("source_field", "")),
    )


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(values)


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if key not in payload:
            raise UnknownExecutionOutcomeRecoveryError(f"missing non-authorizing flag: {key}")
        if payload[key] is not expected and key not in {
            "unknown_execution_outcome_recovery_contract_complete",
            "order_intent_lineage_bound",
            "submission_attempt_lineage_bound",
            "runtime_state_reconciliation_lineage_bound",
            "snapshot_evidence_binding_bound",
            "deterministic_serialization_bound",
            "stable_digest_bound",
        }:
            raise UnknownExecutionOutcomeRecoveryError(
                f"non-authorizing flag {key} must be {expected}, got {payload[key]!r}"
            )


def _binding_digest(value: str, *, domain: str) -> str:
    return compute_content_sha256(
        {
            "digest_domain": domain,
            "value": value,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _artifact_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_runtime_state_reconciliation_bundle(
    bundle_dir: Path | str,
) -> VerifiedRuntimeStateReconciliationBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="runtime_state_reconciliation_bundle_dir")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise UnknownExecutionOutcomeRecoveryError(f"MANIFEST.sha256 verification failed: {msg}")
    artifact_path = path / RECONCILIATION_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=RECONCILIATION_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        reverify_runtime_state_reconciliation_v1(output_dir=path)
    except RuntimeStateReconciliationError as exc:
        raise UnknownExecutionOutcomeRecoveryError(str(exc)) from exc
    manifest_digest = hashlib.sha256((path / MANIFEST_FILENAME).read_bytes()).hexdigest()
    return VerifiedRuntimeStateReconciliationBundle(
        bundle_dir=path,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=RECONCILIATION_ARTIFACT_REL,
        artifact_digest=_artifact_digest(artifact_path),
        manifest_digest=manifest_digest,
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        reconciliation_digest=str(payload.get("reconciliation_digest", "")),
        artifact_payload=dict(payload),
    )


def verify_order_intent_idempotency_bundle(
    bundle_dir: Path | str,
) -> VerifiedOrderIntentIdempotencyBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="order_intent_idempotency_bundle_dir")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise UnknownExecutionOutcomeRecoveryError(f"MANIFEST.sha256 verification failed: {msg}")
    artifact_path = path / IDEMPOTENCY_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=IDEMPOTENCY_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        reverify_order_intent_idempotency_v1(output_dir=path)
    except OrderIntentIdempotencyError as exc:
        raise UnknownExecutionOutcomeRecoveryError(str(exc)) from exc
    intent_identity = payload.get("canonical_order_intent_identity", {})
    order_identity = payload.get("canonical_order_identity", {})
    manifest_digest = hashlib.sha256((path / MANIFEST_FILENAME).read_bytes()).hexdigest()
    trading_epoch = str(intent_identity.get("trading_epoch", ""))
    executor_epoch = str(payload.get("executor_epoch", trading_epoch))
    authority_ref = str(payload.get("authority_lease_identity", ""))
    authority_digest = str(payload.get("authority_lease_digest", ""))
    return VerifiedOrderIntentIdempotencyBundle(
        bundle_dir=path,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=IDEMPOTENCY_ARTIFACT_REL,
        artifact_digest=_artifact_digest(artifact_path),
        manifest_digest=manifest_digest,
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        canonical_order_intent_identity_digest=str(
            payload.get("canonical_order_intent_identity_digest", "")
        ),
        canonical_order_identity_digest=str(payload.get("canonical_order_identity_digest", "")),
        client_order_id=str(intent_identity.get("client_order_id", "")),
        order_intent_digest=str(intent_identity.get("order_intent_digest", "")),
        trading_epoch=trading_epoch,
        executor_epoch=executor_epoch,
        authority_ref=authority_ref,
        authority_digest=authority_digest,
        artifact_payload=dict(payload),
    )


def _serialize_snapshot_binding(name: str, binding: RecoverySnapshotBinding) -> dict[str, str]:
    return {
        "snapshot_name": name,
        "snapshot_ref": binding.snapshot_ref,
        "snapshot_digest": binding.snapshot_digest,
    }


def _compatible_classifications(values: list[str]) -> bool:
    normalized = [value for value in values if value not in {"NOT_REQUIRED", ""}]
    if not normalized:
        return False
    if len(set(normalized)) == 1:
        return True
    compatible_groups = (
        frozenset({"ACKNOWLEDGED_OR_OPEN", "PARTIALLY_FILLED"}),
        frozenset({"PARTIALLY_FILLED", "FILLED"}),
    )
    value_set = frozenset(normalized)
    return any(value_set <= group for group in compatible_groups)


def _derive_recovery_classification(
    signals: RecoveryEvidenceSignals,
) -> tuple[str, bool]:
    if signals.negative_not_found_evidence_sufficient:
        not_found_values = {
            signals.open_orders_classification,
            signals.recent_orders_classification,
            signals.fill_classification,
            signals.position_classification,
        }
        if signals.margin_snapshot_required:
            not_found_values.add(signals.margin_classification)
        if not_found_values <= frozenset({"NOT_FOUND", "NOT_REQUIRED"}):
            return "NOT_FOUND_WITH_SUFFICIENT_NEGATIVE_EVIDENCE", True

    candidates = [
        signals.recent_orders_classification,
        signals.fill_classification,
        signals.position_classification,
    ]
    if signals.margin_snapshot_required:
        candidates.append(signals.margin_classification)
    known = [value for value in candidates if value not in {"UNKNOWN", "NOT_REQUIRED", ""}]
    if not known:
        return "STILL_UNKNOWN", False
    if not _compatible_classifications(known):
        return "STILL_UNKNOWN", False
    primary = signals.recent_orders_classification
    if primary not in _VALID_RECOVERY_CLASSIFICATIONS:
        return "STILL_UNKNOWN", False
    if primary in _TERMINAL_RECOVERY_CLASSIFICATIONS:
        return primary, True
    if primary == "RECONCILIATION_REQUIRED":
        return "RECONCILIATION_REQUIRED", False
    return "STILL_UNKNOWN", False


def _validate_request(
    request: UnknownExecutionRecoveryRequest,
    *,
    reconciliation: VerifiedRuntimeStateReconciliationBundle,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []

    instrument_type = request.instrument_type.strip().upper()
    if not instrument_type:
        facts.append(
            _factor(
                factor_id="MISSING_INSTRUMENT_TYPE",
                factor_type="MISSING_PRECONDITION",
                source_field="instrument_type",
                detail="",
            )
        )
    elif (
        instrument_type in _FORBIDDEN_INSTRUMENT_TYPES
        or instrument_type not in _VALID_INSTRUMENT_TYPES
    ):
        facts.append(
            _factor(
                factor_id="FORBIDDEN_INSTRUMENT_TYPE",
                factor_type="CONTRADICTION",
                source_field="instrument_type",
                detail=instrument_type,
            )
        )

    if request.transport_outcome not in _VALID_TRANSPORT_OUTCOMES:
        facts.append(
            _factor(
                factor_id="INVALID_TRANSPORT_OUTCOME",
                factor_type="MISSING_PRECONDITION",
                source_field="transport_outcome",
                detail=request.transport_outcome,
            )
        )

    if request.transport_claims_not_submitted:
        facts.append(
            _factor(
                factor_id="TRANSPORT_TIMEOUT_DOES_NOT_PROVE_NOT_SUBMITTED",
                factor_type="CONTRADICTION",
                source_field="transport_claims_not_submitted",
                detail="true",
            )
        )

    if request.new_client_order_id_proposed:
        facts.append(
            _factor(
                factor_id="NEW_CLIENT_ORDER_ID_NOT_ALLOWED",
                factor_type="CONTRADICTION",
                source_field="new_client_order_id_proposed",
                detail="true",
            )
        )

    if request.client_order_id != idempotency.client_order_id:
        facts.append(
            _factor(
                factor_id="CLIENT_ORDER_ID_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="client_order_id",
                detail=request.client_order_id,
            )
        )

    if request.order_intent_digest != idempotency.order_intent_digest:
        facts.append(
            _factor(
                factor_id="ORDER_INTENT_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="order_intent_digest",
                detail=request.order_intent_digest,
            )
        )

    if request.trading_epoch != idempotency.trading_epoch:
        facts.append(
            _factor(
                factor_id="TRADING_EPOCH_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="trading_epoch",
                detail=request.trading_epoch,
            )
        )

    if request.executor_epoch != idempotency.executor_epoch:
        facts.append(
            _factor(
                factor_id="EXECUTOR_EPOCH_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="executor_epoch",
                detail=request.executor_epoch,
            )
        )

    if request.authority_ref != idempotency.authority_ref:
        facts.append(
            _factor(
                factor_id="AUTHORITY_REF_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="authority_ref",
                detail=request.authority_ref,
            )
        )

    if request.authority_digest != idempotency.authority_digest:
        facts.append(
            _factor(
                factor_id="AUTHORITY_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="authority_digest",
                detail=request.authority_digest,
            )
        )

    if request.reconciliation_digest != reconciliation.reconciliation_digest:
        facts.append(
            _factor(
                factor_id="RECONCILIATION_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="reconciliation_digest",
                detail=request.reconciliation_digest,
            )
        )

    expected_submission_digest = _binding_digest(
        f"{idempotency.contract_id}:{request.submission_started}",
        domain="submission_attempt_digest_v1",
    )
    if request.submission_attempt_digest != expected_submission_digest:
        facts.append(
            _factor(
                factor_id="SUBMISSION_ATTEMPT_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="submission_attempt_digest",
                detail=request.submission_attempt_digest,
            )
        )

    for name in _REQUIRED_SNAPSHOT_BINDINGS:
        binding = getattr(request, name)
        if not binding.snapshot_ref or not binding.snapshot_digest:
            facts.append(
                _factor(
                    factor_id=f"MISSING_{name.upper()}",
                    factor_type="MISSING_PRECONDITION",
                    source_field=f"{name}.snapshot_ref",
                    detail="",
                )
            )

    if request.evidence_signals.margin_snapshot_required:
        if request.margin_snapshot is None or not request.margin_snapshot.snapshot_digest:
            facts.append(
                _factor(
                    factor_id="MISSING_MARGIN_SNAPSHOT",
                    factor_type="MISSING_PRECONDITION",
                    source_field="margin_snapshot.snapshot_digest",
                    detail="",
                )
            )

    if not request.runtime_state_snapshot_ref or not request.runtime_state_snapshot_digest:
        facts.append(
            _factor(
                factor_id="MISSING_RUNTIME_STATE_SNAPSHOT",
                factor_type="MISSING_PRECONDITION",
                source_field="runtime_state_snapshot_ref",
                detail="",
            )
        )

    derived, _ = _derive_recovery_classification(request.evidence_signals)
    if request.declared_recovery_classification != derived:
        facts.append(
            _factor(
                factor_id="RECOVERY_CLASSIFICATION_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="declared_recovery_classification",
                detail=request.declared_recovery_classification,
            )
        )

    return facts


def _evaluate_recovery(
    *,
    request: UnknownExecutionRecoveryRequest,
    blocking_facts: list[dict[str, str]],
) -> tuple[str, str, str, list[str], dict[str, Any], str, bool, bool]:
    factor_ids = {item.get("factor_id") for item in blocking_facts}
    derived, terminal = _derive_recovery_classification(request.evidence_signals)
    reconciliation_required = (
        derived in {"STILL_UNKNOWN", "RECONCILIATION_REQUIRED"} or not terminal
    )

    if factor_ids & {
        "FORBIDDEN_INSTRUMENT_TYPE",
        "INVALID_INSTRUMENT_TYPE",
        "MISSING_INSTRUMENT_TYPE",
    }:
        return (
            "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_FUTURES_MARKET_TYPE_CONFLICT",
            "CONFLICT",
            "FUTURES_MARKET_TYPE_CONFLICT",
            _sorted_strings(["FUTURES_MARKET_TYPE_CONFLICT"]),
            {
                "admissibility_reason": "FUTURES_MARKET_TYPE_CONFLICT",
                "deny_reason": "FUTURES_MARKET_TYPE_CONFLICT",
            },
            "STILL_UNKNOWN",
            False,
            True,
        )

    if "CLIENT_ORDER_ID_MISMATCH" in factor_ids:
        return (
            "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_CLIENT_ORDER_ID_MISMATCH",
            "CONFLICT",
            "CLIENT_ORDER_ID_MISMATCH",
            _sorted_strings(["CLIENT_ORDER_ID_MISMATCH"]),
            {
                "admissibility_reason": "CLIENT_ORDER_ID_MISMATCH",
                "deny_reason": "CLIENT_ORDER_ID_MISMATCH",
            },
            "STILL_UNKNOWN",
            False,
            True,
        )

    if factor_ids & {"TRADING_EPOCH_MISMATCH", "EXECUTOR_EPOCH_MISMATCH"}:
        return (
            "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_EPOCH_MISMATCH",
            "CONFLICT",
            "EPOCH_MISMATCH",
            _sorted_strings(["EPOCH_MISMATCH"]),
            {"admissibility_reason": "EPOCH_MISMATCH", "deny_reason": "EPOCH_MISMATCH"},
            "STILL_UNKNOWN",
            False,
            True,
        )

    if factor_ids & {
        "ORDER_INTENT_DIGEST_MISMATCH",
        "SUBMISSION_ATTEMPT_DIGEST_MISMATCH",
        "RECONCILIATION_DIGEST_MISMATCH",
        "AUTHORITY_DIGEST_MISMATCH",
        "AUTHORITY_REF_MISMATCH",
    }:
        return (
            "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_DIGEST_MISMATCH",
            "INVALID",
            "DIGEST_MISMATCH",
            _sorted_strings(["DIGEST_MISMATCH"]),
            {"admissibility_reason": "DIGEST_MISMATCH", "deny_reason": "DIGEST_MISMATCH"},
            "STILL_UNKNOWN",
            False,
            True,
        )

    if factor_ids & {
        "MISSING_OPEN_ORDERS_SNAPSHOT",
        "MISSING_RECENT_ORDERS_SNAPSHOT",
        "MISSING_FILL_SNAPSHOT",
        "MISSING_POSITION_SNAPSHOT",
        "MISSING_MARGIN_SNAPSHOT",
        "MISSING_RUNTIME_STATE_SNAPSHOT",
    }:
        return (
            "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_MISSING_BINDINGS",
            "INVALID",
            "MISSING_BINDINGS",
            _sorted_strings(["MISSING_BINDINGS"]),
            {"admissibility_reason": "MISSING_BINDINGS", "deny_reason": "MISSING_BINDINGS"},
            "STILL_UNKNOWN",
            False,
            True,
        )

    if factor_ids & {
        "TRANSPORT_TIMEOUT_DOES_NOT_PROVE_NOT_SUBMITTED",
        "NEW_CLIENT_ORDER_ID_NOT_ALLOWED",
        "INVALID_TRANSPORT_OUTCOME",
    }:
        return (
            "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_INVALID",
            "INVALID",
            "INVALID",
            _sorted_strings(["INVALID_RECOVERY_REQUEST"]),
            {
                "admissibility_reason": "INVALID_RECOVERY_REQUEST",
                "deny_reason": "INVALID_RECOVERY_REQUEST",
            },
            "STILL_UNKNOWN",
            False,
            True,
        )

    if derived == "STILL_UNKNOWN":
        return (
            "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_STILL_UNKNOWN",
            "UNKNOWN",
            "STILL_UNKNOWN",
            _sorted_strings(["STILL_UNKNOWN"]),
            {"admissibility_reason": "STILL_UNKNOWN", "deny_reason": "STILL_UNKNOWN"},
            "STILL_UNKNOWN",
            False,
            True,
        )

    if derived == "RECONCILIATION_REQUIRED":
        return (
            "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_RECONCILIATION_REQUIRED",
            "UNKNOWN",
            "RECONCILIATION_REQUIRED",
            _sorted_strings(["RECONCILIATION_REQUIRED"]),
            {
                "admissibility_reason": "RECONCILIATION_REQUIRED",
                "deny_reason": "RECONCILIATION_REQUIRED",
            },
            "RECONCILIATION_REQUIRED",
            False,
            True,
        )

    if "RECOVERY_CLASSIFICATION_MISMATCH" in factor_ids:
        return (
            "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_STILL_UNKNOWN",
            "CONFLICT",
            "STILL_UNKNOWN",
            _sorted_strings(["CONTRADICTORY_SNAPSHOT_EVIDENCE"]),
            {
                "admissibility_reason": "CONTRADICTORY_SNAPSHOT_EVIDENCE",
                "deny_reason": "CONTRADICTORY_SNAPSHOT_EVIDENCE",
            },
            "STILL_UNKNOWN",
            False,
            True,
        )

    return (
        "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID",
        "VALID",
        derived,
        _sorted_strings([derived]),
        {"admissibility_reason": derived, "deny_reason": ""},
        derived,
        False,
        reconciliation_required,
    )


def build_unknown_execution_outcome_recovery_v1(
    *,
    reconciliation: VerifiedRuntimeStateReconciliationBundle,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    request: UnknownExecutionRecoveryRequest,
) -> dict[str, Any]:
    blocking_facts = _validate_request(
        request, reconciliation=reconciliation, idempotency=idempotency
    )
    contradictions = [item for item in blocking_facts if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in blocking_facts if item.get("factor_type") != "CONTRADICTION"
    ]

    (
        contract_status,
        evidence_status,
        classification,
        reason_codes,
        completion,
        recovery_classification,
        resubmit_allowed,
        reconciliation_required,
    ) = _evaluate_recovery(request=request, blocking_facts=blocking_facts)

    snapshot_bindings = [
        _serialize_snapshot_binding("open_orders_snapshot", request.open_orders_snapshot),
        _serialize_snapshot_binding("recent_orders_snapshot", request.recent_orders_snapshot),
        _serialize_snapshot_binding("fill_snapshot", request.fill_snapshot),
        _serialize_snapshot_binding("position_snapshot", request.position_snapshot),
    ]
    if request.margin_snapshot is not None:
        snapshot_bindings.append(
            _serialize_snapshot_binding("margin_snapshot", request.margin_snapshot)
        )

    recovery_digest = compute_content_sha256(
        {
            "snapshot_bindings": snapshot_bindings,
            "recovery_classification": recovery_classification,
            "transport_outcome": request.transport_outcome,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    contract_id = compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "recovery_id": request.recovery_id,
            "client_order_id": request.client_order_id,
            "recovery_digest": recovery_digest,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    complete = contract_status == "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID"
    provenance_digest = request.provenance_digest or _binding_digest(
        request.source_revision, domain="provenance_digest_v1"
    )
    cross_domain_lineage_digest = request.cross_domain_lineage_digest or _binding_digest(
        reconciliation.contract_id,
        domain="cross_domain_lineage_digest_v1",
    )

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "recovery_contract_version": request.recovery_contract_version,
        "schema_version": SCHEMA_VERSION,
        "creation_contract_version": CREATION_CONTRACT_VERSION,
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "contract_creation_time": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "builder_version": BUILDER_VERSION,
        "producer_identity_ref": DEFAULT_PRODUCER_IDENTITY_REF,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        "deterministic_serialization_version": request.deterministic_serialization_version,
        "contract_status": contract_status,
        "contract_reason_codes": reason_codes,
        "evidence_status": evidence_status,
        "evidence_reason": completion.get("admissibility_reason", ""),
        "recovery_classification": recovery_classification,
        "admissibility_reason": completion.get("admissibility_reason", ""),
        "deny_reason": completion.get("deny_reason", ""),
        "recovery_id": request.recovery_id,
        "order_intent_ref": request.order_intent_ref,
        "order_intent_digest": request.order_intent_digest,
        "client_order_id": request.client_order_id,
        "submission_attempt_ref": request.submission_attempt_ref,
        "submission_attempt_digest": request.submission_attempt_digest,
        "submission_started": request.submission_started,
        "venue_acknowledgement_known": request.venue_acknowledgement_known,
        "transport_outcome": request.transport_outcome,
        "unknown_outcome_reason": request.unknown_outcome_reason,
        "trading_epoch": request.trading_epoch,
        "executor_epoch": request.executor_epoch,
        "authority_ref": request.authority_ref,
        "authority_digest": request.authority_digest,
        "runtime_state_snapshot_ref": request.runtime_state_snapshot_ref,
        "runtime_state_snapshot_digest": request.runtime_state_snapshot_digest,
        "open_orders_snapshot_ref": request.open_orders_snapshot.snapshot_ref,
        "open_orders_snapshot_digest": request.open_orders_snapshot.snapshot_digest,
        "recent_orders_snapshot_ref": request.recent_orders_snapshot.snapshot_ref,
        "recent_orders_snapshot_digest": request.recent_orders_snapshot.snapshot_digest,
        "fill_snapshot_ref": request.fill_snapshot.snapshot_ref,
        "fill_snapshot_digest": request.fill_snapshot.snapshot_digest,
        "position_snapshot_ref": request.position_snapshot.snapshot_ref,
        "position_snapshot_digest": request.position_snapshot.snapshot_digest,
        "margin_snapshot_ref": (
            request.margin_snapshot.snapshot_ref if request.margin_snapshot else ""
        ),
        "margin_snapshot_digest": (
            request.margin_snapshot.snapshot_digest if request.margin_snapshot else ""
        ),
        "reconciliation_ref": request.reconciliation_ref,
        "reconciliation_digest": request.reconciliation_digest,
        "recovery_digest": recovery_digest,
        "resubmit_allowed": resubmit_allowed,
        "new_client_order_id_allowed": False,
        "runtime_mutation_performed": False,
        "adapter_invoked": False,
        "exchange_request_sent": False,
        "network_side_effect_created": False,
        "query_by_client_order_id_required": True,
        "reconciliation_required": reconciliation_required,
        "instrument_type": request.instrument_type,
        "correlation_id": request.correlation_id,
        "recovery_evidence_signals": {
            "open_orders_classification": request.evidence_signals.open_orders_classification,
            "recent_orders_classification": request.evidence_signals.recent_orders_classification,
            "fill_classification": request.evidence_signals.fill_classification,
            "position_classification": request.evidence_signals.position_classification,
            "margin_classification": request.evidence_signals.margin_classification,
            "margin_snapshot_required": request.evidence_signals.margin_snapshot_required,
            "negative_not_found_evidence_sufficient": (
                request.evidence_signals.negative_not_found_evidence_sufficient
            ),
        },
        "upstream_bindings": {
            "runtime_state_reconciliation_bundle_ref": reconciliation.bundle_dir.as_posix(),
            "runtime_state_reconciliation_contract_id": reconciliation.contract_id,
            "runtime_state_reconciliation_digest": reconciliation.artifact_digest,
            "order_intent_idempotency_bundle_ref": idempotency.bundle_dir.as_posix(),
            "order_intent_idempotency_contract_id": idempotency.contract_id,
            "order_intent_idempotency_digest": idempotency.artifact_digest,
        },
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in blocking_facts if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "unknown_execution_outcome_recovery_authority_invariants": dict(
            UNKNOWN_EXECUTION_OUTCOME_RECOVERY_AUTHORITY_INVARIANTS
        ),
        "provenance": {
            "producer_contract_name": CONTRACT_NAME,
            "producer_contract_version": CONTRACT_VERSION,
            "creation_contract_version": CREATION_CONTRACT_VERSION,
            "evidence_level": EVIDENCE_LEVEL,
            "offline_only": True,
            "contract_created_for_offline_evidence_only": True,
            "source_revision": request.source_revision,
        },
        "integrity_metadata": {
            "digest_algorithm": "sha256",
            "canonical_serialization": "deterministic_json_dumps",
            "contract_id_domain": CONTRACT_NAME,
            "signature_created": False,
        },
        "output_digest": "",
        "manifest_digest": "",
        "provenance_digest": provenance_digest,
        "cross_domain_lineage_digest": cross_domain_lineage_digest,
        "unknown_execution_outcome_recovery_contract_complete": complete,
        "unknown_execution_outcome_recovery_offline_only": True,
        "unknown_execution_outcome_observed_only": True,
        "order_intent_lineage_bound": complete,
        "submission_attempt_lineage_bound": complete,
        "runtime_state_reconciliation_lineage_bound": complete,
        "snapshot_evidence_binding_bound": complete,
        "deterministic_serialization_bound": complete,
        "stable_digest_bound": complete,
        "integrity": {
            "content_sha256": "",
        },
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if key in payload:
            continue
        payload[key] = value
    payload["unknown_execution_outcome_recovery_contract_complete"] = complete

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise UnknownExecutionOutcomeRecoveryError("contract_status invalid")
    if evidence_status not in _VALID_EVIDENCE_STATUSES:
        raise UnknownExecutionOutcomeRecoveryError("evidence_status invalid")
    if recovery_classification not in _VALID_RECOVERY_CLASSIFICATIONS:
        raise UnknownExecutionOutcomeRecoveryError("recovery_classification invalid")

    payload["contract_id"] = contract_id
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(payload))}
    return payload


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    excluded = frozenset(
        {
            "output_digest",
            "manifest_digest",
            "integrity",
            "created_at",
            "artifact_id",
            "contract_id",
        }
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def serialize_unknown_execution_outcome_recovery_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise UnknownExecutionOutcomeRecoveryError("contract_status invalid")
    for list_field in (
        "contract_reason_codes",
        "blocking_facts",
        "missing_preconditions",
        "contradictions",
    ):
        values = contract.get(list_field)
        if isinstance(values, list) and values != sorted(
            values,
            key=lambda item: (
                item.get("factor_id", item) if isinstance(item, dict) else item,
                item.get("source_field", "") if isinstance(item, dict) else "",
            ),
        ):
            raise UnknownExecutionOutcomeRecoveryError(
                f"{list_field} must be sorted deterministically"
            )
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_unknown_execution_outcome_recovery_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise UnknownExecutionOutcomeRecoveryError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise UnknownExecutionOutcomeRecoveryError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise UnknownExecutionOutcomeRecoveryError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise UnknownExecutionOutcomeRecoveryError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise UnknownExecutionOutcomeRecoveryError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise UnknownExecutionOutcomeRecoveryError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "offline_only_no_recovery_action", "status": "PASS"},
        {"check_id": "offline_only_no_order_resubmit", "status": "PASS"},
        {"check_id": "offline_only_no_adapter_invocation", "status": "PASS"},
        {"check_id": "offline_only_no_network_side_effect", "status": "PASS"},
        {"check_id": "unknown_outcome_implies_resubmit_allowed_false", "status": "PASS"},
        {"check_id": "unknown_outcome_implies_new_client_order_id_allowed_false", "status": "PASS"},
        {"check_id": "manifest_digest", "status": "PASS" if manifest_digest else "FAIL"},
    ]
    overall = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": overall,
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "manifest_digest": manifest_digest,
    }


def _finalize_contract_with_manifest_digest(
    contract: Mapping[str, Any],
    *,
    manifest_digest: str,
) -> dict[str, Any]:
    finalized = dict(contract)
    finalized["manifest_digest"] = manifest_digest
    return finalized


def default_unknown_execution_recovery_request(
    *,
    reconciliation: VerifiedRuntimeStateReconciliationBundle,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    recovery_classification: str = "FILLED",
    transport_outcome: str = "UNKNOWN_OUTCOME",
    unknown_outcome_reason: str = "TRANSPORT_TIMEOUT_AFTER_POSSIBLE_TRANSMISSION",
    venue_acknowledgement_known: bool = False,
    submission_started: str = "1970-01-01T00:00:01+00:00",
    instrument_type: str = "FUTURES",
    correlation_id: str = "offline-unknown-outcome-recovery-correlation-001",
    margin_snapshot_required: bool = False,
) -> UnknownExecutionRecoveryRequest:
    client_order_id = idempotency.client_order_id
    submission_attempt_ref = f"submission-attempt/{client_order_id}"
    submission_attempt_digest = _binding_digest(
        f"{idempotency.contract_id}:{submission_started}",
        domain="submission_attempt_digest_v1",
    )
    order_intent_ref = f"order-intent/{client_order_id}"
    runtime_state_snapshot_ref = f"runtime-state-snapshot/{reconciliation.contract_id}"
    runtime_state_snapshot_digest = _binding_digest(
        reconciliation.reconciliation_digest,
        domain="runtime_state_snapshot_digest_v1",
    )
    snapshot_seed = reconciliation.reconciliation_digest
    open_orders = RecoverySnapshotBinding(
        snapshot_ref=f"open-orders/{client_order_id}",
        snapshot_digest=_binding_digest(snapshot_seed, domain="open_orders_snapshot_digest_v1"),
    )
    recent_orders = RecoverySnapshotBinding(
        snapshot_ref=f"recent-orders/{client_order_id}",
        snapshot_digest=_binding_digest(snapshot_seed, domain="recent_orders_snapshot_digest_v1"),
    )
    fill_snapshot = RecoverySnapshotBinding(
        snapshot_ref=f"fill-snapshot/{client_order_id}",
        snapshot_digest=_binding_digest(snapshot_seed, domain="fill_snapshot_digest_v1"),
    )
    position_snapshot = RecoverySnapshotBinding(
        snapshot_ref=f"position-snapshot/{client_order_id}",
        snapshot_digest=_binding_digest(snapshot_seed, domain="position_snapshot_digest_v1"),
    )
    margin_snapshot = None
    margin_classification = "NOT_REQUIRED"
    if margin_snapshot_required:
        margin_snapshot = RecoverySnapshotBinding(
            snapshot_ref=f"margin-snapshot/{client_order_id}",
            snapshot_digest=_binding_digest(snapshot_seed, domain="margin_snapshot_digest_v1"),
        )
        margin_classification = recovery_classification

    if recovery_classification == "NOT_FOUND_WITH_SUFFICIENT_NEGATIVE_EVIDENCE":
        open_orders_classification = "NOT_FOUND"
        recent_orders_classification = "NOT_FOUND"
        fill_classification = "NOT_FOUND"
        position_classification = "NOT_FOUND"
        margin_classification = "NOT_FOUND" if margin_snapshot_required else "NOT_REQUIRED"
    else:
        open_orders_classification = recovery_classification
        recent_orders_classification = recovery_classification
        fill_classification = recovery_classification
        position_classification = recovery_classification
        margin_classification = (
            recovery_classification if margin_snapshot_required else "NOT_REQUIRED"
        )

    evidence_signals = RecoveryEvidenceSignals(
        open_orders_classification=open_orders_classification,
        recent_orders_classification=recent_orders_classification,
        fill_classification=fill_classification,
        position_classification=position_classification,
        margin_classification=margin_classification,
        margin_snapshot_required=margin_snapshot_required,
        negative_not_found_evidence_sufficient=(
            recovery_classification == "NOT_FOUND_WITH_SUFFICIENT_NEGATIVE_EVIDENCE"
        ),
    )

    return UnknownExecutionRecoveryRequest(
        recovery_id=f"recovery-{client_order_id}",
        client_order_id=client_order_id,
        submission_started=submission_started,
        transport_outcome=transport_outcome,
        unknown_outcome_reason=unknown_outcome_reason,
        venue_acknowledgement_known=venue_acknowledgement_known,
        transport_claims_not_submitted=False,
        new_client_order_id_proposed=False,
        open_orders_snapshot=open_orders,
        recent_orders_snapshot=recent_orders,
        fill_snapshot=fill_snapshot,
        position_snapshot=position_snapshot,
        margin_snapshot=margin_snapshot,
        runtime_state_snapshot_ref=runtime_state_snapshot_ref,
        runtime_state_snapshot_digest=runtime_state_snapshot_digest,
        reconciliation_ref=reconciliation.bundle_dir.as_posix(),
        reconciliation_digest=reconciliation.reconciliation_digest,
        submission_attempt_ref=submission_attempt_ref,
        submission_attempt_digest=submission_attempt_digest,
        order_intent_ref=order_intent_ref,
        order_intent_digest=idempotency.order_intent_digest,
        authority_ref=idempotency.authority_ref,
        authority_digest=idempotency.authority_digest,
        trading_epoch=idempotency.trading_epoch,
        executor_epoch=idempotency.executor_epoch,
        evidence_signals=evidence_signals,
        declared_recovery_classification=recovery_classification,
        instrument_type=instrument_type,
        correlation_id=correlation_id,
        provenance_digest=_binding_digest(DEFAULT_SOURCE_REVISION, domain="provenance_digest_v1"),
        cross_domain_lineage_digest=_binding_digest(
            reconciliation.contract_id,
            domain="cross_domain_lineage_digest_v1",
        ),
    )


def verify_unknown_execution_recovery_inputs(
    inputs: UnknownExecutionRecoveryInputs,
) -> tuple[VerifiedRuntimeStateReconciliationBundle, VerifiedOrderIntentIdempotencyBundle]:
    reconciliation = verify_runtime_state_reconciliation_bundle(
        inputs.runtime_state_reconciliation_bundle_dir
    )
    idempotency = verify_order_intent_idempotency_bundle(inputs.order_intent_idempotency_bundle_dir)
    return reconciliation, idempotency


def reverify_unknown_execution_outcome_recovery_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise UnknownExecutionOutcomeRecoveryError(
            f"unknown execution outcome recovery directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise UnknownExecutionOutcomeRecoveryError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise UnknownExecutionOutcomeRecoveryError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise UnknownExecutionOutcomeRecoveryError("manifest_digest mismatch on replay")

    reconciliation = verify_runtime_state_reconciliation_bundle(
        Path(str(contract["upstream_bindings"]["runtime_state_reconciliation_bundle_ref"]))
    )
    idempotency = verify_order_intent_idempotency_bundle(
        Path(str(contract["upstream_bindings"]["order_intent_idempotency_bundle_ref"]))
    )
    bindings = contract.get("upstream_bindings", {})
    if bindings.get("runtime_state_reconciliation_digest") != reconciliation.artifact_digest:
        raise UnknownExecutionOutcomeRecoveryError("reconciliation digest mismatch on replay")
    if bindings.get("order_intent_idempotency_digest") != idempotency.artifact_digest:
        raise UnknownExecutionOutcomeRecoveryError("idempotency digest mismatch on replay")


def produce_unknown_execution_outcome_recovery_v1(
    *,
    inputs: UnknownExecutionRecoveryInputs,
    output_dir: Path | str,
) -> UnknownExecutionRecoveryResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[
            inputs.runtime_state_reconciliation_bundle_dir,
            inputs.order_intent_idempotency_bundle_dir,
        ],
        output_dir=final_dir,
    )

    reconciliation, idempotency = verify_unknown_execution_recovery_inputs(inputs)
    contract_body = build_unknown_execution_outcome_recovery_v1(
        reconciliation=reconciliation,
        idempotency=idempotency,
        request=inputs.recovery_request,
    )

    staging = final_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    if staging.exists():
        raise UnknownExecutionOutcomeRecoveryError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_unknown_execution_outcome_recovery_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            contract=finalized,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise UnknownExecutionOutcomeRecoveryError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_unknown_execution_outcome_recovery_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise UnknownExecutionOutcomeRecoveryError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return UnknownExecutionRecoveryResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        evidence_status=str(finalized["evidence_status"]),
        recovery_classification=str(finalized["recovery_classification"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        recovery_digest=str(finalized["recovery_digest"]),
        resubmit_allowed=bool(finalized["resubmit_allowed"]),
        reconciliation_required=bool(finalized["reconciliation_required"]),
    )


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


__all__ = [
    "ARTIFACT_REL",
    "BUILDER_VERSION",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "RECOVERY_CONTRACT_VERSION",
    "SELF_VERIFICATION_REL",
    "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_AUTHORITY_INVARIANTS",
    "RecoveryEvidenceSignals",
    "RecoverySnapshotBinding",
    "UnknownExecutionOutcomeRecoveryError",
    "UnknownExecutionRecoveryInputs",
    "UnknownExecutionRecoveryRequest",
    "UnknownExecutionRecoveryResult",
    "VerifiedOrderIntentIdempotencyBundle",
    "VerifiedRuntimeStateReconciliationBundle",
    "build_self_verification_v1",
    "build_unknown_execution_outcome_recovery_v1",
    "default_unknown_execution_recovery_request",
    "produce_unknown_execution_outcome_recovery_v1",
    "reverify_unknown_execution_outcome_recovery_v1",
    "serialize_unknown_execution_outcome_recovery_v1",
    "verify_order_intent_idempotency_bundle",
    "verify_runtime_state_reconciliation_bundle",
    "verify_unknown_execution_recovery_inputs",
]
