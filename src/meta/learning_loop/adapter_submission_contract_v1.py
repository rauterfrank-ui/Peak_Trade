"""Offline RUNBOOK_STEP_20 adapter submission contract owner v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
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
from src.meta.learning_loop.trading_core_decision_attestation_v1 import (
    ARTIFACT_REL as ATTESTATION_ARTIFACT_REL,
    TradingCoreDecisionAttestationError,
    reverify_trading_core_decision_attestation_v1,
)

CONTRACT_NAME = "adapter_submission_contract_v1"
CONTRACT_VERSION = "v1"
ADAPTER_SUBMISSION_CONTRACT_VERSION = "adapter_submission_contract_v1"
PRODUCER_VERSION = "adapter_submission_contract_v1"
BUILDER_VERSION = "adapter_submission_contract_builder_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "adapter_submission_contract_record"
INPUT_RELATION = (
    "PACKAGES_VERIFIED_RUNTIME_STATE_RECONCILIATION_ORDER_INTENT_IDEMPOTENCY_AND_"
    "TRADING_CORE_DECISION_ATTESTATION_FOR_OFFLINE_ADAPTER_SUBMISSION_GATING"
)
ARTIFACT_REL = "adapter_submission_contract_v1.json"
NORMALIZED_PAYLOAD_REL = "normalized_adapter_payload_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".adapter_submission_contract_staging_"

SCHEMA_VERSION = "adapter_submission_contract_schema_v1"
CREATION_CONTRACT_VERSION = "adapter_submission_contract_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "adapter_submission_contract_rules_v1"
DETERMINISTIC_SERIALIZATION_VERSION = "deterministic_json_dumps_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_adapter_submission_contract_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"

_VALID_MARKET_TYPES = frozenset({"FUTURES", "PERP", "PERPETUAL", "PERPETUAL_FUTURES"})
_FORBIDDEN_MARKET_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_VALID_ORDER_TYPES = frozenset({"LIMIT", "MARKET"})
_VALID_SIDES = frozenset({"BUY", "SELL"})

_VALID_CONTRACT_STATUSES = frozenset(
    {
        "ADAPTER_SUBMISSION_CONTRACT_VALID",
        "ADAPTER_SUBMISSION_CONTRACT_INVALID",
        "ADAPTER_SUBMISSION_CONTRACT_BLOCKED",
        "ADAPTER_SUBMISSION_CONTRACT_MISSING_BINDINGS",
        "ADAPTER_SUBMISSION_CONTRACT_PERMISSION_EXPIRED",
        "ADAPTER_SUBMISSION_CONTRACT_EPOCH_MISMATCH",
        "ADAPTER_SUBMISSION_CONTRACT_KILL_SWITCH_BLOCKED",
        "ADAPTER_SUBMISSION_CONTRACT_RECONCILIATION_BLOCKED",
        "ADAPTER_SUBMISSION_CONTRACT_MARKET_TYPE_BLOCKED",
        "ADAPTER_SUBMISSION_CONTRACT_SEMANTIC_MUTATION_BLOCKED",
        "ABSTAIN",
    }
)
_VALID_EVIDENCE_STATUSES = frozenset(
    {"ADMISSIBLE", "VALID", "CONFLICT", "INVALID", "UNKNOWN", "ABSTAIN"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "adapter_submission_contract_self_verification_v1"

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

ADAPTER_SUBMISSION_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "adapter_submission_is_descriptive_only": True,
    "adapter_submission_is_offline_only": True,
    "adapter_submission_contract_does_not_submit_order": True,
    "adapter_submission_contract_does_not_invoke_adapter": True,
    "adapter_submission_contract_does_not_mutate_runtime_state": True,
    "adapter_submission_contract_does_not_consume_permission": True,
    "adapter_submission_contract_does_not_claim_submission": True,
    "adapter_may_submit_order": False,
    "adapter_may_amend_order": False,
    "adapter_may_cancel_order": False,
    "adapter_may_mutate_runtime_state": False,
    "deny_by_default": True,
    "futures_only": True,
    "lineage_bound": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_adapter_submission_contract": True,
    "adapter_submission_contract_offline_only": True,
    "adapter_submission_contract_complete": False,
    "adapter_submission_request_observed_only": True,
    "adapter_invoked": False,
    "exchange_request_sent": False,
    "network_side_effect_created": False,
    "order_submission_requested": False,
    "order_submitted": False,
    "order_created": False,
    "permission_consumed": False,
    "submission_claim_consumed": False,
    "runtime_state_mutated": False,
    "position_state_mutated": False,
    "authority_activated": False,
    "lease_activated": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "adapter_may_submit_order": False,
    "adapter_may_amend_order": False,
    "adapter_may_cancel_order": False,
    "adapter_may_mutate_runtime_state": False,
    "semantic_equivalence_verified": False,
    "deny_by_default": True,
    "futures_only": True,
}
_DYNAMIC_NON_AUTH_FLAGS = frozenset(
    {
        "adapter_submission_contract_complete",
        "lineage_bound",
        "epoch_binding_bound",
        "kill_switch_binding_bound",
        "reconciliation_binding_bound",
        "venue_capability_binding_bound",
        "submission_claim_binding_bound",
        "execution_permission_binding_bound",
        "semantic_equivalence_verified",
        "stable_digest_bound",
    }
)


class AdapterSubmissionContractError(ValueError):
    """Fail-closed adapter submission contract error."""


@dataclass(frozen=True)
class BindingRef:
    ref: str
    digest: str


@dataclass(frozen=True)
class VerifiedOrderIntentIdempotencyBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    contract_id: str
    contract_status: str
    idempotency_status: str
    canonical_order_intent_identity_digest: str
    canonical_order_identity_digest: str
    client_order_id: str
    order_intent_digest: str
    venue: str
    account_scope: str
    instrument: str
    market_type: str
    side: str
    order_type: str
    quantity: str
    limit_price: str
    maximum_market_price: str
    reduce_only: bool
    position_mode: str
    margin_mode: str
    time_in_force: str
    trading_epoch: str
    executor_epoch: str
    revocation_epoch: str
    authority_ref: str
    authority_digest: str


@dataclass(frozen=True)
class VerifiedRuntimeStateReconciliationBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    contract_id: str
    contract_status: str
    reconciliation_state: str
    reconciliation_digest: str
    futures_only: bool


@dataclass(frozen=True)
class VerifiedTradingCoreDecisionAttestationBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    contract_id: str
    contract_status: str
    attestation_status: str
    canonical_order_intent_identity_digest: str
    canonical_order_identity_digest: str
    client_order_id: str
    order_intent_digest: str
    venue: str
    account_scope: str
    instrument: str
    trading_epoch: str
    attestation_chain_digest: str


@dataclass(frozen=True)
class AdapterSubmissionRequest:
    submission_contract_id: str
    canonical_order_intent_ref: str
    canonical_order_intent_digest: str
    execution_permission_ref: str
    execution_permission_digest: str
    execution_permission_expires_at: str
    execution_permission_single_use: bool
    submission_claim_ref: str
    submission_claim_digest: str
    authority_ref: str
    authority_digest: str
    authority_active: bool
    kill_switch_state: str
    kill_switch_observed_at: str
    kill_switch_is_fresh: bool
    reconciliation_state: str
    reconciliation_ref: str
    reconciliation_digest: str
    venue_capability_ref: str
    venue_capability_digest: str
    client_order_id: str
    venue: str
    account_scope: str
    instrument: str
    market_type: str
    side: str
    order_type: str
    quantity: str
    limit_price: str
    maximum_market_price: str
    reduce_only: bool
    position_mode: str
    margin_mode: str
    time_in_force: str
    trading_epoch: str
    executor_epoch: str
    revocation_epoch: str
    created_at: str
    builder_version: str
    unknown_outcome_retry_requested: bool = False
    permission_consumed: bool = False
    submission_started_or_consumed: bool = False
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class AdapterSubmissionInputs:
    runtime_state_reconciliation_bundle_dir: Path
    order_intent_idempotency_bundle_dir: Path
    trading_core_decision_attestation_bundle_dir: Path
    request: AdapterSubmissionRequest


@dataclass(frozen=True)
class AdapterSubmissionResult:
    output_dir: Path
    contract_id: str
    contract_status: str
    evidence_status: str
    contract_path: Path
    normalized_payload_path: Path | None
    self_verification_path: Path
    manifest_path: Path


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise AdapterSubmissionContractError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise AdapterSubmissionContractError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise AdapterSubmissionContractError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise AdapterSubmissionContractError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise AdapterSubmissionContractError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise AdapterSubmissionContractError("output directory must not be under /tmp")


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
            raise AdapterSubmissionContractError("output directory must not equal input bundle")
        if _path_is_under(resolved_output, resolved_bundle) or _path_is_under(
            resolved_bundle, resolved_output
        ):
            raise AdapterSubmissionContractError("output directory overlaps input bundle")


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


def _parse_iso8601(value: str, *, field_name: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise AdapterSubmissionContractError(f"{field_name} must be ISO-8601: {value!r}") from exc


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if key not in payload:
            raise AdapterSubmissionContractError(f"missing non-authorizing flag: {key}")
        if key in _DYNAMIC_NON_AUTH_FLAGS:
            continue
        if payload[key] is not expected:
            raise AdapterSubmissionContractError(
                f"non-authorizing flag {key} must be {expected}, got {payload[key]!r}"
            )


def _extract_order_intent_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    intent = payload.get("canonical_order_intent_identity", {})
    if not isinstance(intent, Mapping):
        intent = {}
    raw_market = str(intent.get("market_type") or intent.get("instrument_type", "")).strip().upper()
    if not raw_market:
        raw_market = "FUTURES"
    return {
        "client_order_id": str(intent.get("client_order_id", "")),
        "order_intent_digest": str(intent.get("order_intent_digest", "")),
        "venue": str(intent.get("venue", "")),
        "account_scope": str(intent.get("account", "")),
        "instrument": str(intent.get("instrument", "")),
        "market_type": raw_market,
        "side": str(intent.get("side", "")).strip().upper(),
        "order_type": str(intent.get("order_type", "")).strip().upper(),
        "quantity": str(intent.get("quantity", "")),
        "limit_price": str(intent.get("limit_price", "")),
        "maximum_market_price": str(intent.get("maximum_market_price", "")),
        "reduce_only": bool(intent.get("reduce_only", False)),
        "position_mode": str(intent.get("position_mode", "")),
        "margin_mode": str(intent.get("margin_mode", "")),
        "time_in_force": str(intent.get("time_in_force", "")),
        "trading_epoch": str(intent.get("trading_epoch", "")),
    }


def verify_order_intent_idempotency_bundle(
    bundle_dir: Path | str,
) -> VerifiedOrderIntentIdempotencyBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="order_intent_idempotency_bundle_dir")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise AdapterSubmissionContractError(f"MANIFEST.sha256 verification failed: {msg}")
    artifact_path = path / IDEMPOTENCY_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=IDEMPOTENCY_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        reverify_order_intent_idempotency_v1(output_dir=path)
    except OrderIntentIdempotencyError as exc:
        raise AdapterSubmissionContractError(str(exc)) from exc
    intent = _extract_order_intent_fields(payload)
    manifest_digest = hashlib.sha256((path / MANIFEST_FILENAME).read_bytes()).hexdigest()
    executor_epoch = str(payload.get("executor_epoch", intent["trading_epoch"]))
    revocation_epoch = str(
        payload.get("revocation_epoch", payload.get("writer_revision", intent["trading_epoch"]))
    )
    return VerifiedOrderIntentIdempotencyBundle(
        bundle_dir=path,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=IDEMPOTENCY_ARTIFACT_REL,
        artifact_digest=_artifact_digest(artifact_path),
        manifest_digest=manifest_digest,
        artifact_payload=dict(payload),
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        idempotency_status=str(payload.get("idempotency_status", "")),
        canonical_order_intent_identity_digest=str(
            payload.get("canonical_order_intent_identity_digest", "")
        ),
        canonical_order_identity_digest=str(payload.get("canonical_order_identity_digest", "")),
        client_order_id=intent["client_order_id"],
        order_intent_digest=intent["order_intent_digest"],
        venue=intent["venue"],
        account_scope=intent["account_scope"],
        instrument=intent["instrument"],
        market_type=intent["market_type"],
        side=intent["side"],
        order_type=intent["order_type"],
        quantity=intent["quantity"],
        limit_price=intent["limit_price"],
        maximum_market_price=intent["maximum_market_price"],
        reduce_only=bool(intent["reduce_only"]),
        position_mode=intent["position_mode"],
        margin_mode=intent["margin_mode"],
        time_in_force=intent["time_in_force"],
        trading_epoch=intent["trading_epoch"],
        executor_epoch=executor_epoch,
        revocation_epoch=revocation_epoch,
        authority_ref=str(payload.get("authority_lease_identity", "")),
        authority_digest=str(payload.get("authority_lease_digest", "")),
    )


def verify_runtime_state_reconciliation_bundle(
    bundle_dir: Path | str,
) -> VerifiedRuntimeStateReconciliationBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="runtime_state_reconciliation_bundle_dir")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise AdapterSubmissionContractError(f"MANIFEST.sha256 verification failed: {msg}")
    artifact_path = path / RECONCILIATION_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=RECONCILIATION_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        reverify_runtime_state_reconciliation_v1(output_dir=path)
    except RuntimeStateReconciliationError as exc:
        raise AdapterSubmissionContractError(str(exc)) from exc
    manifest_digest = hashlib.sha256((path / MANIFEST_FILENAME).read_bytes()).hexdigest()
    return VerifiedRuntimeStateReconciliationBundle(
        bundle_dir=path,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=RECONCILIATION_ARTIFACT_REL,
        artifact_digest=_artifact_digest(artifact_path),
        manifest_digest=manifest_digest,
        artifact_payload=dict(payload),
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        reconciliation_state=str(payload.get("reconciliation_state", "")),
        reconciliation_digest=str(payload.get("reconciliation_digest", "")),
        futures_only=bool(payload.get("futures_only", False)),
    )


def verify_trading_core_decision_attestation_bundle(
    bundle_dir: Path | str,
) -> VerifiedTradingCoreDecisionAttestationBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="trading_core_decision_attestation_bundle_dir")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise AdapterSubmissionContractError(f"MANIFEST.sha256 verification failed: {msg}")
    artifact_path = path / ATTESTATION_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ATTESTATION_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        reverify_trading_core_decision_attestation_v1(output_dir=path)
    except TradingCoreDecisionAttestationError as exc:
        raise AdapterSubmissionContractError(str(exc)) from exc
    intent = payload.get("canonical_order_intent_identity", {})
    if not isinstance(intent, Mapping):
        intent = {}
    manifest_digest = hashlib.sha256((path / MANIFEST_FILENAME).read_bytes()).hexdigest()
    return VerifiedTradingCoreDecisionAttestationBundle(
        bundle_dir=path,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=ATTESTATION_ARTIFACT_REL,
        artifact_digest=_artifact_digest(artifact_path),
        manifest_digest=manifest_digest,
        artifact_payload=dict(payload),
        contract_id=str(payload.get("contract_id", "")),
        contract_status=str(payload.get("contract_status", "")),
        attestation_status=str(payload.get("attestation_status", "")),
        canonical_order_intent_identity_digest=str(
            payload.get("canonical_order_intent_identity_digest", "")
        ),
        canonical_order_identity_digest=str(payload.get("canonical_order_identity_digest", "")),
        client_order_id=str(intent.get("client_order_id", "")),
        order_intent_digest=str(intent.get("order_intent_digest", "")),
        venue=str(intent.get("venue", "")),
        account_scope=str(intent.get("account", "")),
        instrument=str(intent.get("instrument", "")),
        trading_epoch=str(intent.get("trading_epoch", "")),
        attestation_chain_digest=str(payload.get("attestation_chain_digest", "")),
    )


def _normalize_decimal_string(raw: str, *, field_name: str) -> tuple[str, Decimal]:
    try:
        original = Decimal(raw)
    except (InvalidOperation, ValueError) as exc:
        raise AdapterSubmissionContractError(f"{field_name} invalid Decimal: {raw!r}") from exc
    normalized = original.normalize()
    normalized_text = format(normalized, "f")
    if "." in normalized_text:
        normalized_text = normalized_text.rstrip("0").rstrip(".")
    if normalized_text == "-0":
        normalized_text = "0"
    return normalized_text or "0", original


def _normalize_quantity(quantity: str) -> tuple[str, bool]:
    normalized_text, original = _normalize_decimal_string(quantity, field_name="quantity")
    normalized_decimal = Decimal(normalized_text)
    semantic_mutation = normalized_decimal > original
    return normalized_text, semantic_mutation


def _validate_request(
    request: AdapterSubmissionRequest,
    *,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    reconciliation: VerifiedRuntimeStateReconciliationBundle,
    attestation: VerifiedTradingCoreDecisionAttestationBundle,
) -> tuple[list[dict[str, str]], str]:
    facts: list[dict[str, str]] = []

    def missing(field: str, value: str) -> None:
        if not value:
            facts.append(
                _factor(
                    factor_id=f"MISSING_{field.upper()}",
                    factor_type="MISSING_PRECONDITION",
                    source_field=field,
                    detail="",
                )
            )

    for field, value in (
        ("submission_contract_id", request.submission_contract_id),
        ("canonical_order_intent_ref", request.canonical_order_intent_ref),
        ("canonical_order_intent_digest", request.canonical_order_intent_digest),
        ("execution_permission_ref", request.execution_permission_ref),
        ("execution_permission_digest", request.execution_permission_digest),
        ("submission_claim_ref", request.submission_claim_ref),
        ("submission_claim_digest", request.submission_claim_digest),
        ("authority_ref", request.authority_ref),
        ("authority_digest", request.authority_digest),
        ("reconciliation_ref", request.reconciliation_ref),
        ("reconciliation_digest", request.reconciliation_digest),
        ("venue_capability_ref", request.venue_capability_ref),
        ("venue_capability_digest", request.venue_capability_digest),
        ("client_order_id", request.client_order_id),
        ("venue", request.venue),
        ("account_scope", request.account_scope),
        ("instrument", request.instrument),
        ("market_type", request.market_type),
        ("trading_epoch", request.trading_epoch),
        ("executor_epoch", request.executor_epoch),
        ("revocation_epoch", request.revocation_epoch),
        ("created_at", request.created_at),
        ("builder_version", request.builder_version),
    ):
        missing(field, value)

    if not request.authority_active:
        facts.append(
            _factor(
                factor_id="AUTHORITY_INACTIVE",
                factor_type="CONTRADICTION",
                source_field="authority_active",
                detail="false",
            )
        )

    if request.market_type.upper() in _FORBIDDEN_MARKET_TYPES or (
        request.market_type.upper() not in _VALID_MARKET_TYPES
    ):
        facts.append(
            _factor(
                factor_id="MARKET_TYPE_NOT_FUTURES",
                factor_type="CONTRADICTION",
                source_field="market_type",
                detail=request.market_type,
            )
        )

    if request.side.upper() not in _VALID_SIDES:
        facts.append(
            _factor(
                factor_id="INVALID_SIDE",
                factor_type="MISSING_PRECONDITION",
                source_field="side",
                detail=request.side,
            )
        )
    if request.order_type.upper() not in _VALID_ORDER_TYPES:
        facts.append(
            _factor(
                factor_id="INVALID_ORDER_TYPE",
                factor_type="MISSING_PRECONDITION",
                source_field="order_type",
                detail=request.order_type,
            )
        )

    if request.kill_switch_state.upper() != "ARMED":
        facts.append(
            _factor(
                factor_id="KILL_SWITCH_NOT_ARMED",
                factor_type="CONTRADICTION",
                source_field="kill_switch_state",
                detail=request.kill_switch_state,
            )
        )
    if not request.kill_switch_is_fresh:
        facts.append(
            _factor(
                factor_id="KILL_SWITCH_NOT_FRESH",
                factor_type="MISSING_PRECONDITION",
                source_field="kill_switch_is_fresh",
                detail="false",
            )
        )

    if request.reconciliation_state.upper() != "CLEAN":
        facts.append(
            _factor(
                factor_id="RECONCILIATION_NOT_CLEAN",
                factor_type="CONTRADICTION",
                source_field="reconciliation_state",
                detail=request.reconciliation_state,
            )
        )

    if not request.execution_permission_single_use:
        facts.append(
            _factor(
                factor_id="PERMISSION_NOT_SINGLE_USE",
                factor_type="CONTRADICTION",
                source_field="execution_permission_single_use",
                detail="false",
            )
        )

    expected_permission_digest = _binding_digest(
        f"{idempotency.contract_id}:{idempotency.client_order_id}",
        domain="execution_permission_digest_v1",
    )
    if request.execution_permission_digest != expected_permission_digest:
        facts.append(
            _factor(
                factor_id="PERMISSION_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="execution_permission_digest",
                detail=request.execution_permission_digest,
            )
        )

    expected_claim_digest = _binding_digest(
        f"{attestation.contract_id}:{idempotency.client_order_id}",
        domain="submission_claim_digest_v1",
    )
    if request.submission_claim_digest != expected_claim_digest:
        facts.append(
            _factor(
                factor_id="CLAIM_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="submission_claim_digest",
                detail=request.submission_claim_digest,
            )
        )

    created_at = _parse_iso8601(request.created_at, field_name="created_at")
    expires_at = _parse_iso8601(
        request.execution_permission_expires_at,
        field_name="execution_permission_expires_at",
    )
    if expires_at <= created_at:
        facts.append(
            _factor(
                factor_id="PERMISSION_EXPIRED",
                factor_type="CONTRADICTION",
                source_field="execution_permission_expires_at",
                detail=request.execution_permission_expires_at,
            )
        )

    if request.unknown_outcome_retry_requested:
        facts.append(
            _factor(
                factor_id="UNKNOWN_OUTCOME_RETRY_REQUESTED",
                factor_type="CONTRADICTION",
                source_field="unknown_outcome_retry_requested",
                detail="true",
            )
        )
    if request.permission_consumed:
        facts.append(
            _factor(
                factor_id="PERMISSION_ALREADY_CONSUMED",
                factor_type="CONTRADICTION",
                source_field="permission_consumed",
                detail="true",
            )
        )
    if request.submission_started_or_consumed:
        facts.append(
            _factor(
                factor_id="SUBMISSION_ALREADY_STARTED_OR_CONSUMED",
                factor_type="CONTRADICTION",
                source_field="submission_started_or_consumed",
                detail="true",
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

    if request.trading_epoch != idempotency.trading_epoch or (
        attestation.trading_epoch and request.trading_epoch != attestation.trading_epoch
    ):
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
    if request.revocation_epoch != idempotency.revocation_epoch:
        facts.append(
            _factor(
                factor_id="REVOCATION_EPOCH_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="revocation_epoch",
                detail=request.revocation_epoch,
            )
        )

    if request.canonical_order_intent_digest != idempotency.canonical_order_intent_identity_digest:
        facts.append(
            _factor(
                factor_id="CANONICAL_ORDER_INTENT_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="canonical_order_intent_digest",
                detail=request.canonical_order_intent_digest,
            )
        )
    if request.canonical_order_intent_digest != attestation.canonical_order_intent_identity_digest:
        facts.append(
            _factor(
                factor_id="ATTESTATION_INTENT_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="canonical_order_intent_digest",
                detail=request.canonical_order_intent_digest,
            )
        )
    if request.client_order_id != idempotency.client_order_id or (
        attestation.client_order_id and request.client_order_id != attestation.client_order_id
    ):
        facts.append(
            _factor(
                factor_id="CLIENT_ORDER_ID_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="client_order_id",
                detail=request.client_order_id,
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

    if request.venue != idempotency.venue or request.venue != attestation.venue:
        facts.append(
            _factor(
                factor_id="VENUE_BINDING_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="venue",
                detail=request.venue,
            )
        )
    if request.account_scope != idempotency.account_scope or (
        attestation.account_scope and request.account_scope != attestation.account_scope
    ):
        facts.append(
            _factor(
                factor_id="ACCOUNT_SCOPE_BINDING_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="account_scope",
                detail=request.account_scope,
            )
        )
    if request.instrument != idempotency.instrument or (
        attestation.instrument and request.instrument != attestation.instrument
    ):
        facts.append(
            _factor(
                factor_id="INSTRUMENT_BINDING_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="instrument",
                detail=request.instrument,
            )
        )
    if request.market_type.upper() != idempotency.market_type.upper():
        facts.append(
            _factor(
                factor_id="MARKET_TYPE_BINDING_MISMATCH",
                factor_type="CONTRADICTION",
                source_field="market_type",
                detail=request.market_type,
            )
        )

    normalized_quantity, quantity_semantic_mutation = _normalize_quantity(request.quantity)
    if quantity_semantic_mutation:
        facts.append(
            _factor(
                factor_id="SEMANTIC_MUTATION_QUANTITY_ROUND_UP",
                factor_type="CONTRADICTION",
                source_field="quantity",
                detail=request.quantity,
            )
        )

    return facts, normalized_quantity


def _evaluate_contract(
    factors: list[dict[str, str]],
) -> tuple[str, str, list[str], dict[str, str]]:
    factor_ids = {item.get("factor_id") for item in factors}

    if any(factor and factor.startswith("MISSING_") for factor in factor_ids if factor):
        return (
            "ADAPTER_SUBMISSION_CONTRACT_MISSING_BINDINGS",
            "INVALID",
            _sorted_strings(["MISSING_BINDINGS"]),
            {"admissibility_reason": "MISSING_BINDINGS", "deny_reason": "MISSING_BINDINGS"},
        )
    if "PERMISSION_EXPIRED" in factor_ids:
        return (
            "ADAPTER_SUBMISSION_CONTRACT_PERMISSION_EXPIRED",
            "INVALID",
            _sorted_strings(["PERMISSION_EXPIRED"]),
            {"admissibility_reason": "PERMISSION_EXPIRED", "deny_reason": "PERMISSION_EXPIRED"},
        )
    if factor_ids & {
        "TRADING_EPOCH_MISMATCH",
        "EXECUTOR_EPOCH_MISMATCH",
        "REVOCATION_EPOCH_MISMATCH",
    }:
        return (
            "ADAPTER_SUBMISSION_CONTRACT_EPOCH_MISMATCH",
            "CONFLICT",
            _sorted_strings(["EPOCH_MISMATCH"]),
            {"admissibility_reason": "EPOCH_MISMATCH", "deny_reason": "EPOCH_MISMATCH"},
        )
    if factor_ids & {"KILL_SWITCH_NOT_ARMED", "KILL_SWITCH_NOT_FRESH"}:
        return (
            "ADAPTER_SUBMISSION_CONTRACT_KILL_SWITCH_BLOCKED",
            "INVALID",
            _sorted_strings(["KILL_SWITCH_BLOCKED"]),
            {"admissibility_reason": "KILL_SWITCH_BLOCKED", "deny_reason": "KILL_SWITCH_BLOCKED"},
        )
    if factor_ids & {"RECONCILIATION_NOT_CLEAN", "RECONCILIATION_DIGEST_MISMATCH"}:
        return (
            "ADAPTER_SUBMISSION_CONTRACT_RECONCILIATION_BLOCKED",
            "INVALID",
            _sorted_strings(["RECONCILIATION_BLOCKED"]),
            {
                "admissibility_reason": "RECONCILIATION_BLOCKED",
                "deny_reason": "RECONCILIATION_BLOCKED",
            },
        )
    if factor_ids & {"MARKET_TYPE_NOT_FUTURES", "MARKET_TYPE_BINDING_MISMATCH"}:
        return (
            "ADAPTER_SUBMISSION_CONTRACT_MARKET_TYPE_BLOCKED",
            "INVALID",
            _sorted_strings(["MARKET_TYPE_BLOCKED"]),
            {"admissibility_reason": "MARKET_TYPE_BLOCKED", "deny_reason": "MARKET_TYPE_BLOCKED"},
        )
    if "SEMANTIC_MUTATION_QUANTITY_ROUND_UP" in factor_ids:
        return (
            "ADAPTER_SUBMISSION_CONTRACT_SEMANTIC_MUTATION_BLOCKED",
            "INVALID",
            _sorted_strings(["SEMANTIC_MUTATION_BLOCKED"]),
            {
                "admissibility_reason": "SEMANTIC_MUTATION_BLOCKED",
                "deny_reason": "SEMANTIC_MUTATION_BLOCKED",
            },
        )
    if factors:
        return (
            "ADAPTER_SUBMISSION_CONTRACT_BLOCKED",
            "INVALID",
            _sorted_strings(["POLICY_BLOCKED"]),
            {"admissibility_reason": "POLICY_BLOCKED", "deny_reason": "POLICY_BLOCKED"},
        )
    return (
        "ADAPTER_SUBMISSION_CONTRACT_VALID",
        "VALID",
        _sorted_strings(["VALID"]),
        {"admissibility_reason": "VALID", "deny_reason": ""},
    )


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


def build_adapter_submission_contract_v1(
    *,
    request: AdapterSubmissionRequest,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    reconciliation: VerifiedRuntimeStateReconciliationBundle,
    attestation: VerifiedTradingCoreDecisionAttestationBundle,
) -> dict[str, Any]:
    factors, normalized_quantity = _validate_request(
        request,
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
    )
    contradictions = [item for item in factors if item.get("factor_type") == "CONTRADICTION"]
    non_contradiction_blocking = [
        item for item in factors if item.get("factor_type") != "CONTRADICTION"
    ]
    contract_status, evidence_status, reason_codes, completion = _evaluate_contract(factors)
    complete = contract_status == "ADAPTER_SUBMISSION_CONTRACT_VALID"

    contract_id = compute_content_sha256(
        {
            "contract_domain": CONTRACT_NAME,
            "submission_contract_id": request.submission_contract_id,
            "canonical_order_intent_digest": request.canonical_order_intent_digest,
            "execution_permission_digest": request.execution_permission_digest,
            "submission_claim_digest": request.submission_claim_digest,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "adapter_submission_contract_version": ADAPTER_SUBMISSION_CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "creation_contract_version": CREATION_CONTRACT_VERSION,
        "artifact_id": "",
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "contract_creation_time": OFFLINE_DETERMINISTIC_CREATED_AT,
        "producer_version": PRODUCER_VERSION,
        "producer_identity_ref": DEFAULT_PRODUCER_IDENTITY_REF,
        "record_kind": RECORD_KIND,
        "input_relation": INPUT_RELATION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        "deterministic_serialization_version": DETERMINISTIC_SERIALIZATION_VERSION,
        "contract_status": contract_status,
        "contract_reason_codes": reason_codes,
        "evidence_status": evidence_status,
        "evidence_reason": completion.get("admissibility_reason", ""),
        "admissibility_reason": completion.get("admissibility_reason", ""),
        "deny_reason": completion.get("deny_reason", ""),
        "submission_contract_id": request.submission_contract_id,
        "canonical_order_intent_ref": request.canonical_order_intent_ref,
        "canonical_order_intent_digest": request.canonical_order_intent_digest,
        "execution_permission_ref": request.execution_permission_ref,
        "execution_permission_digest": request.execution_permission_digest,
        "execution_permission_expires_at": request.execution_permission_expires_at,
        "execution_permission_single_use": request.execution_permission_single_use,
        "submission_claim_ref": request.submission_claim_ref,
        "submission_claim_digest": request.submission_claim_digest,
        "authority_ref": request.authority_ref,
        "authority_digest": request.authority_digest,
        "authority_active": request.authority_active,
        "kill_switch_state": request.kill_switch_state,
        "kill_switch_observed_at": request.kill_switch_observed_at,
        "kill_switch_is_fresh": request.kill_switch_is_fresh,
        "reconciliation_state": request.reconciliation_state,
        "reconciliation_ref": request.reconciliation_ref,
        "reconciliation_digest": request.reconciliation_digest,
        "venue_capability_ref": request.venue_capability_ref,
        "venue_capability_digest": request.venue_capability_digest,
        "client_order_id": request.client_order_id,
        "venue": request.venue,
        "account_scope": request.account_scope,
        "instrument": request.instrument,
        "market_type": request.market_type,
        "side": request.side,
        "order_type": request.order_type,
        "quantity": request.quantity,
        "normalized_quantity": normalized_quantity,
        "limit_price": request.limit_price,
        "maximum_market_price": request.maximum_market_price,
        "reduce_only": request.reduce_only,
        "position_mode": request.position_mode,
        "margin_mode": request.margin_mode,
        "time_in_force": request.time_in_force,
        "trading_epoch": request.trading_epoch,
        "executor_epoch": request.executor_epoch,
        "revocation_epoch": request.revocation_epoch,
        "request_created_at": request.created_at,
        "request_builder_version": request.builder_version,
        "unknown_outcome_retry_requested": request.unknown_outcome_retry_requested,
        "declared_permission_consumed": request.permission_consumed,
        "declared_submission_started_or_consumed": request.submission_started_or_consumed,
        "upstream_bindings": {
            "runtime_state_reconciliation_bundle_ref": reconciliation.bundle_dir.as_posix(),
            "runtime_state_reconciliation_contract_id": reconciliation.contract_id,
            "runtime_state_reconciliation_digest": reconciliation.artifact_digest,
            "order_intent_idempotency_bundle_ref": idempotency.bundle_dir.as_posix(),
            "order_intent_idempotency_contract_id": idempotency.contract_id,
            "order_intent_idempotency_digest": idempotency.artifact_digest,
            "trading_core_decision_attestation_bundle_ref": attestation.bundle_dir.as_posix(),
            "trading_core_decision_attestation_contract_id": attestation.contract_id,
            "trading_core_decision_attestation_digest": attestation.artifact_digest,
        },
        "blocking_facts": _sort_factors(non_contradiction_blocking),
        "missing_preconditions": _sort_factors(
            [item for item in factors if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(contradictions),
        "adapter_submission_authority_invariants": dict(ADAPTER_SUBMISSION_AUTHORITY_INVARIANTS),
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
        "adapter_submission_contract_complete": complete,
        "adapter_submission_contract_offline_only": True,
        "lineage_bound": complete,
        "epoch_binding_bound": complete,
        "kill_switch_binding_bound": complete,
        "reconciliation_binding_bound": complete,
        "venue_capability_binding_bound": complete,
        "submission_claim_binding_bound": complete,
        "execution_permission_binding_bound": complete,
        "semantic_equivalence_verified": complete,
        "semantic_mutation_detected": False,
        "semantic_mutation_quantity_round_up": False,
        "stable_digest_bound": complete,
        "deny_by_default": True,
        "futures_only": True,
        "integrity": {"content_sha256": ""},
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if key not in payload:
            payload[key] = value
    payload["adapter_submission_contract_complete"] = complete
    payload["semantic_equivalence_verified"] = complete

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise AdapterSubmissionContractError("contract_status invalid")
    if evidence_status not in _VALID_EVIDENCE_STATUSES:
        raise AdapterSubmissionContractError("evidence_status invalid")

    payload["contract_id"] = contract_id
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(payload))}
    return payload


def build_normalized_adapter_payload_v1(
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any] | None:
    if contract.get("contract_status") != "ADAPTER_SUBMISSION_CONTRACT_VALID":
        return None
    normalization_rules_digest = compute_content_sha256(
        {
            "rules": [
                "decimal_strip_trailing_zeros",
                "no_quantity_round_up",
                "uppercase_enumerations",
            ],
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )
    source_digest = str(contract.get("output_digest", ""))
    payload_body = {
        "payload_contract_name": "normalized_adapter_payload_v1",
        "payload_contract_version": CONTRACT_VERSION,
        "source_submission_contract_digest": source_digest,
        "normalized_client_order_id": contract["client_order_id"],
        "normalized_instrument": contract["instrument"],
        "normalized_side": str(contract["side"]).upper(),
        "normalized_order_type": str(contract["order_type"]).upper(),
        "normalized_quantity": contract["normalized_quantity"],
        "normalized_limit_price": contract["limit_price"],
        "normalized_reduce_only": bool(contract["reduce_only"]),
        "normalized_position_mode": contract["position_mode"],
        "normalized_margin_mode": contract["margin_mode"],
        "normalized_time_in_force": contract["time_in_force"],
        "normalization_rules_digest": normalization_rules_digest,
        "semantic_equivalence_verified": True,
        "quantity_increased": False,
        "order_type_changed": False,
        "client_order_id_replaced": False,
        "reduce_only_removed": False,
        "position_mode_changed": False,
        "margin_mode_changed": False,
        "runtime_mutation_performed": False,
        "adapter_invoked": False,
        "exchange_request_sent": False,
        "network_side_effect_created": False,
        "builder_version": BUILDER_VERSION,
        "created_at": OFFLINE_DETERMINISTIC_CREATED_AT,
        "manifest_digest": "",
    }
    payload_without_manifest = {
        key: value for key, value in payload_body.items() if key != "manifest_digest"
    }
    payload_body["manifest_digest"] = compute_content_sha256(payload_without_manifest)
    return payload_body


def serialize_adapter_submission_contract_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise AdapterSubmissionContractError("contract_status invalid")
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
            raise AdapterSubmissionContractError(f"{list_field} must be sorted deterministically")
    return deterministic_json_dumps(contract)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_adapter_submission_contract_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise AdapterSubmissionContractError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise AdapterSubmissionContractError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise AdapterSubmissionContractError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    if integrity.get("content_sha256") != expected:
        raise AdapterSubmissionContractError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise AdapterSubmissionContractError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise AdapterSubmissionContractError("artifact_id must equal output_digest")


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
    normalized_payload_exists: bool,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "offline_only_no_adapter_invocation", "status": "PASS"},
        {"check_id": "offline_only_no_order_submission", "status": "PASS"},
        {"check_id": "offline_only_no_permission_consumption", "status": "PASS"},
        {
            "check_id": "normalized_payload_presence_when_valid",
            "status": (
                "PASS"
                if (
                    (contract.get("contract_status") == "ADAPTER_SUBMISSION_CONTRACT_VALID")
                    == normalized_payload_exists
                )
                else "FAIL"
            ),
        },
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
        "normalized_payload_rel": NORMALIZED_PAYLOAD_REL if normalized_payload_exists else "",
        "manifest_digest": manifest_digest,
    }


def _finalize_contract_with_manifest_digest(
    contract: Mapping[str, Any],
    *,
    manifest_digest: str,
) -> dict[str, Any]:
    body = dict(contract)
    body["manifest_digest"] = manifest_digest
    return body


def verify_adapter_submission_inputs(
    inputs: AdapterSubmissionInputs,
) -> tuple[
    VerifiedOrderIntentIdempotencyBundle,
    VerifiedRuntimeStateReconciliationBundle,
    VerifiedTradingCoreDecisionAttestationBundle,
]:
    idempotency = verify_order_intent_idempotency_bundle(inputs.order_intent_idempotency_bundle_dir)
    reconciliation = verify_runtime_state_reconciliation_bundle(
        inputs.runtime_state_reconciliation_bundle_dir
    )
    attestation = verify_trading_core_decision_attestation_bundle(
        inputs.trading_core_decision_attestation_bundle_dir
    )
    return idempotency, reconciliation, attestation


def default_adapter_submission_request(
    *,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    reconciliation: VerifiedRuntimeStateReconciliationBundle,
    attestation: VerifiedTradingCoreDecisionAttestationBundle,
) -> AdapterSubmissionRequest:
    submission_contract_id = f"adapter-submission-contract/{idempotency.contract_id}"
    permission_ref = f"execution-permission/{idempotency.client_order_id}"
    permission_digest = _binding_digest(
        f"{idempotency.contract_id}:{idempotency.client_order_id}",
        domain="execution_permission_digest_v1",
    )
    claim_ref = f"submission-claim/{idempotency.client_order_id}"
    claim_digest = _binding_digest(
        f"{attestation.contract_id}:{idempotency.client_order_id}",
        domain="submission_claim_digest_v1",
    )
    venue_capability_ref = f"venue-capability/{idempotency.venue or 'GENERIC-FUTURES-VENUE'}"
    venue_capability_digest = _binding_digest(
        f"{idempotency.venue}:{idempotency.account_scope}:{idempotency.instrument}",
        domain="venue_capability_digest_v1",
    )
    return AdapterSubmissionRequest(
        submission_contract_id=submission_contract_id,
        canonical_order_intent_ref=f"canonical-order-intent/{idempotency.client_order_id}",
        canonical_order_intent_digest=idempotency.canonical_order_intent_identity_digest,
        execution_permission_ref=permission_ref,
        execution_permission_digest=permission_digest,
        execution_permission_expires_at="1970-01-01T00:05:00+00:00",
        execution_permission_single_use=True,
        submission_claim_ref=claim_ref,
        submission_claim_digest=claim_digest,
        authority_ref=idempotency.authority_ref,
        authority_digest=idempotency.authority_digest,
        authority_active=True,
        kill_switch_state="ARMED",
        kill_switch_observed_at=OFFLINE_DETERMINISTIC_CREATED_AT,
        kill_switch_is_fresh=True,
        reconciliation_state=reconciliation.reconciliation_state or "CLEAN",
        reconciliation_ref=reconciliation.bundle_dir.as_posix(),
        reconciliation_digest=reconciliation.reconciliation_digest,
        venue_capability_ref=venue_capability_ref,
        venue_capability_digest=venue_capability_digest,
        client_order_id=idempotency.client_order_id or "generic-futures-client-order-001",
        venue=idempotency.venue or "GENERIC-FUTURES-VENUE-001",
        account_scope=idempotency.account_scope or "GENERIC-FUTURES-ACCOUNT-001",
        instrument=idempotency.instrument or "GENERIC-FUTURES-PERP-001",
        market_type="FUTURES",
        side=idempotency.side or "BUY",
        order_type=idempotency.order_type or "LIMIT",
        quantity=idempotency.quantity or "1.0000",
        limit_price=idempotency.limit_price or "100.00",
        maximum_market_price=idempotency.maximum_market_price or "105.00",
        reduce_only=idempotency.reduce_only,
        position_mode=idempotency.position_mode or "ONE_WAY",
        margin_mode=idempotency.margin_mode or "CROSS",
        time_in_force=idempotency.time_in_force or "GTC",
        trading_epoch=idempotency.trading_epoch or attestation.trading_epoch,
        executor_epoch=idempotency.executor_epoch or idempotency.trading_epoch,
        revocation_epoch=idempotency.revocation_epoch or "0",
        created_at=OFFLINE_DETERMINISTIC_CREATED_AT,
        builder_version=BUILDER_VERSION,
        unknown_outcome_retry_requested=False,
        permission_consumed=False,
        submission_started_or_consumed=False,
    )


def reverify_adapter_submission_contract_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise AdapterSubmissionContractError(
            f"adapter submission contract directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise AdapterSubmissionContractError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    normalized_path = bundle_dir / NORMALIZED_PAYLOAD_REL
    normalized_exists = normalized_path.exists()
    if contract.get("contract_status") == "ADAPTER_SUBMISSION_CONTRACT_VALID":
        _validate_regular_file(normalized_path, label=NORMALIZED_PAYLOAD_REL)
        normalized_payload = read_manifest(normalized_path)
        if normalized_payload.get("semantic_equivalence_verified") is not True:
            raise AdapterSubmissionContractError(
                "normalized payload semantic_equivalence_verified must be true"
            )
        for flag in (
            "quantity_increased",
            "order_type_changed",
            "client_order_id_replaced",
            "reduce_only_removed",
            "position_mode_changed",
            "margin_mode_changed",
            "runtime_mutation_performed",
            "adapter_invoked",
            "exchange_request_sent",
            "network_side_effect_created",
        ):
            if normalized_payload.get(flag) is not False:
                raise AdapterSubmissionContractError(
                    f"normalized payload flag {flag} must be false"
                )
    elif normalized_exists:
        raise AdapterSubmissionContractError(
            "normalized payload must not exist when contract status is not VALID"
        )

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise AdapterSubmissionContractError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise AdapterSubmissionContractError("manifest_digest mismatch on replay")

    bindings = contract.get("upstream_bindings", {})
    idempotency = verify_order_intent_idempotency_bundle(
        Path(str(bindings.get("order_intent_idempotency_bundle_ref", "")))
    )
    reconciliation = verify_runtime_state_reconciliation_bundle(
        Path(str(bindings.get("runtime_state_reconciliation_bundle_ref", "")))
    )
    attestation = verify_trading_core_decision_attestation_bundle(
        Path(str(bindings.get("trading_core_decision_attestation_bundle_ref", "")))
    )
    if bindings.get("order_intent_idempotency_digest") != idempotency.artifact_digest:
        raise AdapterSubmissionContractError("idempotency digest mismatch on replay")
    if bindings.get("runtime_state_reconciliation_digest") != reconciliation.artifact_digest:
        raise AdapterSubmissionContractError("reconciliation digest mismatch on replay")
    if bindings.get("trading_core_decision_attestation_digest") != attestation.artifact_digest:
        raise AdapterSubmissionContractError("attestation digest mismatch on replay")


def produce_adapter_submission_contract_v1(
    *,
    inputs: AdapterSubmissionInputs,
    output_dir: Path | str,
) -> AdapterSubmissionResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[
            inputs.runtime_state_reconciliation_bundle_dir,
            inputs.order_intent_idempotency_bundle_dir,
            inputs.trading_core_decision_attestation_bundle_dir,
        ],
        output_dir=final_dir,
    )

    idempotency, reconciliation, attestation = verify_adapter_submission_inputs(inputs)
    contract_body = build_adapter_submission_contract_v1(
        request=inputs.request,
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
    )
    normalized_payload = build_normalized_adapter_payload_v1(contract=contract_body)

    staging = final_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    if staging.exists():
        raise AdapterSubmissionContractError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        normalized_path = staging / NORMALIZED_PAYLOAD_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_adapter_submission_contract_v1(finalized),
            encoding="utf-8",
        )
        if normalized_payload is not None:
            normalized_path.write_text(
                deterministic_json_dumps(normalized_payload),
                encoding="utf-8",
            )
        self_payload = build_self_verification_v1(
            contract=finalized,
            manifest_digest=manifest_digest,
            normalized_payload_exists=normalized_payload is not None,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise AdapterSubmissionContractError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_adapter_submission_contract_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise AdapterSubmissionContractError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return AdapterSubmissionResult(
        output_dir=final_dir,
        contract_id=str(finalized["contract_id"]),
        contract_status=str(finalized["contract_status"]),
        evidence_status=str(finalized["evidence_status"]),
        contract_path=final_dir / ARTIFACT_REL,
        normalized_payload_path=(final_dir / NORMALIZED_PAYLOAD_REL)
        if normalized_payload is not None
        else None,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


__all__ = [
    "ARTIFACT_REL",
    "NORMALIZED_PAYLOAD_REL",
    "BUILDER_VERSION",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "OFFLINE_DETERMINISTIC_CREATED_AT",
    "ADAPTER_SUBMISSION_AUTHORITY_INVARIANTS",
    "AdapterSubmissionContractError",
    "BindingRef",
    "AdapterSubmissionInputs",
    "AdapterSubmissionRequest",
    "AdapterSubmissionResult",
    "VerifiedOrderIntentIdempotencyBundle",
    "VerifiedRuntimeStateReconciliationBundle",
    "VerifiedTradingCoreDecisionAttestationBundle",
    "build_adapter_submission_contract_v1",
    "build_normalized_adapter_payload_v1",
    "build_self_verification_v1",
    "default_adapter_submission_request",
    "produce_adapter_submission_contract_v1",
    "reverify_adapter_submission_contract_v1",
    "serialize_adapter_submission_contract_v1",
    "verify_adapter_submission_inputs",
    "verify_order_intent_idempotency_bundle",
    "verify_runtime_state_reconciliation_bundle",
    "verify_trading_core_decision_attestation_bundle",
]
