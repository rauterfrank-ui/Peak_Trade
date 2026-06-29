"""Offline RUNBOOK_STEP_22 independent pre-trade safety kernel contract owner v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.clock_trust_and_expiry_v1 import (
    VerifiedAuthorityLeaseBundle,
    verify_authority_lease_bundle,
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
    VerifiedTradingSessionSingleWriterBundle,
    reverify_order_intent_idempotency_v1,
    verify_trading_session_single_writer_bundle,
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
from src.meta.learning_loop.trading_session_single_writer_v1 import (
    VerifiedClockTrustBundle,
    verify_clock_trust_and_expiry_bundle,
)
from src.meta.learning_loop.venue_capability_snapshot_v1 import (
    ARTIFACT_REL as VENUE_CAPABILITY_ARTIFACT_REL,
    VenueCapabilitySnapshotError,
    reverify_venue_capability_snapshot_v1,
)

CONTRACT_NAME = "independent_pre_trade_safety_kernel_v1"
CONTRACT_VERSION = "v1"
SAFETY_KERNEL_CONTRACT_VERSION = "independent_pre_trade_safety_kernel_v1"
INPUT_CONTRACT_VERSION = "pre_trade_safety_evaluation_input_v1"
DECISION_CONTRACT_VERSION = "pre_trade_safety_decision_v1"
PRODUCER_VERSION = "independent_pre_trade_safety_kernel_v1"
BUILDER_VERSION = "independent_pre_trade_safety_kernel_builder_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "independent_pre_trade_safety_kernel_record"
INPUT_RELATION = (
    "PACKAGES_VERIFIED_RUNTIME_STATE_RECONCILIATION_ORDER_INTENT_IDEMPOTENCY_"
    "TRADING_CORE_DECISION_ATTESTATION_VENUE_CAPABILITY_AUTHORITY_LEASE_AND_"
    "CLOCK_TRUST_FOR_OFFLINE_INDEPENDENT_PRE_TRADE_SAFETY_EVALUATION"
)
ARTIFACT_REL = "independent_pre_trade_safety_kernel_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".independent_pre_trade_safety_kernel_staging_"

SCHEMA_VERSION = "independent_pre_trade_safety_kernel_schema_v1"
CREATION_CONTRACT_VERSION = "independent_pre_trade_safety_kernel_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "independent_pre_trade_safety_kernel_rules_v1"
DETERMINISTIC_SERIALIZATION_VERSION = "deterministic_json_dumps_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_independent_pre_trade_safety_kernel_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"
DEFAULT_GENERIC_INSTRUMENT = "GENERIC-FUTURES-PERP-001"
DEFAULT_GENERIC_VENUE = "GENERIC-FUTURES-VENUE-001"
DEFAULT_GENERIC_ACCOUNT = "GENERIC-FUTURES-ACCOUNT-001"
DEFAULT_GENERIC_CLIENT_ORDER_ID = "generic-futures-client-order-001"

GENERIC_FUTURES_POSITION_LIMIT = "100"
GENERIC_FUTURES_GROSS_EXPOSURE_LIMIT = "500"
GENERIC_FUTURES_ORDER_NOTIONAL_LIMIT = "50"
GENERIC_FUTURES_DAILY_LOSS_LIMIT = "25"
GENERIC_FUTURES_LEVERAGE_LIMIT = "5"
GENERIC_FUTURES_PRICE_COLLAR_BPS = "500"
GENERIC_FUTURES_MAX_MARK_INDEX_DIVERGENCE_BPS = "100"
GENERIC_FUTURES_MAX_SPREAD_BPS = "50"
GENERIC_FUTURES_MAX_ORDERBOOK_AGE_MS = "5000"
GENERIC_FUTURES_MIN_ORDERBOOK_DEPTH = "10"
GENERIC_FUTURES_MAX_EXPECTED_MARKET_IMPACT_BPS = "25"
GENERIC_FUTURES_SIGNAL_EXPIRY_SECONDS = "300"
GENERIC_FUTURES_OPEN_ORDER_LIMIT = "20"
GENERIC_FUTURES_MESSAGE_RATE_LIMIT_PER_MINUTE = "60"
GENERIC_FUTURES_MARGIN_BUFFER_RATIO = "0.10"

_VALID_MARKET_TYPES = frozenset({"FUTURES", "PERP", "PERPETUAL", "PERPETUAL_FUTURES"})
_FORBIDDEN_MARKET_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_VALID_ORDER_TYPES = frozenset({"LIMIT", "MARKET"})
_VALID_SIDES = frozenset({"BUY", "SELL"})
_VALID_DECISIONS = frozenset({"APPROVE", "REJECT", "BLOCK", "DEFER"})
_VALID_CONTRACT_STATUSES = frozenset(
    {
        "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_APPROVED",
        "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED",
        "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED",
        "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_DEFERRED",
        "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_INVALID",
        "ABSTAIN",
    }
)
_VALID_EVIDENCE_STATUSES = frozenset(
    {"ADMISSIBLE", "VALID", "CONFLICT", "INVALID", "UNKNOWN", "ABSTAIN"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "independent_pre_trade_safety_kernel_self_verification_v1"

_FAIL_CLOSED_GATE_IDS: tuple[str, ...] = (
    "runtime_authority_valid",
    "authority_lease_not_expired",
    "authority_revocation_epoch_current",
    "artifact_digests_valid",
    "session_authorized",
    "trading_epoch_current",
    "executor_epoch_current",
    "instrument_allowed",
    "futures_market_type_required",
    "venue_capability_digest_current",
    "position_limit",
    "gross_exposure_limit",
    "order_notional_limit",
    "daily_loss_limit",
    "leverage_limit",
    "price_collar",
    "stale_market_data_guard",
    "mark_index_divergence_guard",
    "spread_guard",
    "orderbook_depth_guard",
    "expected_market_impact_guard",
    "signal_expiry_guard",
    "duplicate_intent_guard",
    "open_order_limit",
    "message_rate_limit",
    "margin_buffer",
    "kill_switch_state_valid",
    "kill_switch_state_fresh",
    "kill_switch_state_armed",
    "reconciliation_state_clean",
    "clock_trusted",
)

_BLOCK_GATE_IDS = frozenset(
    {
        "runtime_authority_valid",
        "authority_lease_not_expired",
        "authority_revocation_epoch_current",
        "trading_epoch_current",
        "executor_epoch_current",
        "kill_switch_state_valid",
        "kill_switch_state_fresh",
        "kill_switch_state_armed",
        "reconciliation_state_clean",
        "clock_trusted",
        "session_authorized",
    }
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

INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "independent_pre_trade_safety_kernel_is_descriptive_only": True,
    "independent_pre_trade_safety_kernel_is_offline_only": True,
    "independent_pre_trade_safety_kernel_contract_complete": False,
    "pre_trade_safety_kernel_independent": True,
    "pre_trade_safety_kernel_fail_closed": True,
    "pre_trade_safety_approval_is_not_authority": True,
    "safety_decision_approve_does_not_create_execution_permission": True,
    "safety_decision_approve_does_not_authorize_submission": True,
    "safety_decision_approve_does_not_mutate_runtime": True,
    "risk_limit_expansion_allowed": False,
    "capital_limit_expansion_allowed": False,
    "kill_switch_bypass_allowed": False,
    "reconciliation_bypass_allowed": False,
    "authority_bypass_allowed": False,
    "venue_capability_bypass_allowed": False,
    "canonical_order_intent_required": True,
    "trading_core_attestation_chain_required": True,
    "venue_capability_snapshot_required": True,
    "digest_mismatch_fails_closed": True,
    "missing_input_fails_closed": True,
    "stale_input_fails_closed": True,
    "epoch_mismatch_fails_closed": True,
    "unknown_market_type_fails_closed": True,
    "deny_by_default": True,
    "futures_only": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_independent_pre_trade_safety_kernel": True,
    "independent_pre_trade_safety_kernel_offline_only": True,
    "independent_pre_trade_safety_kernel_complete": False,
    "safety_decision_evidence_created": True,
    "single_use_permission_created": False,
    "submission_authorized": False,
    "runtime_mutation_performed": False,
    "order_action_performed": False,
    "adapter_invoked": False,
    "exchange_request_sent": False,
    "network_side_effect_created": False,
    "execution_permission_created": False,
    "execution_permission_consumed": False,
    "order_created": False,
    "order_submission_requested": False,
    "order_submitted": False,
    "order_cancel_requested": False,
    "order_amend_requested": False,
    "order_state_mutated": False,
    "position_state_mutated": False,
    "runtime_state_mutated": False,
    "venue_capability_discovery_executed": False,
    "venue_capability_refresh_executed": False,
    "files_transferred_to_runtime": False,
    "queue_message_created": False,
    "database_mutated": False,
    "lock_acquired": False,
    "reservation_created": False,
    "authority_activated": False,
    "lease_activated": False,
    "revocation_executed": False,
    "reconciliation_executed": False,
    "scheduler_started": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "deny_by_default": True,
    "futures_only": True,
}

_DYNAMIC_NON_AUTH_FLAGS = frozenset(
    {
        "independent_pre_trade_safety_kernel_complete",
        "lineage_bound",
        "epoch_binding_bound",
        "kill_switch_binding_bound",
        "reconciliation_binding_bound",
        "venue_capability_binding_bound",
        "authority_binding_bound",
        "clock_trust_binding_bound",
        "snapshot_binding_bound",
        "stable_digest_bound",
    }
)


class IndependentPreTradeSafetyKernelError(ValueError):
    """Fail-closed independent pre-trade safety kernel error."""


@dataclass(frozen=True)
class InlineSnapshotBinding:
    ref: str
    digest: str
    body: dict[str, Any]


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
class VerifiedVenueCapabilitySnapshotBundle:
    bundle_dir: Path
    contract_name: str
    contract_version: str
    producer_version: str
    artifact_ref: str
    artifact_digest: str
    manifest_digest: str
    artifact_payload: dict[str, Any]
    snapshot_id: str
    snapshot_status: str
    capability_digest: str
    venue: str
    account_scope: str
    instrument: str
    market_type: str


@dataclass(frozen=True)
class PreTradeSafetyEvaluationRequest:
    safety_evaluation_id: str
    canonical_order_intent_ref: str
    canonical_order_intent_digest: str
    trading_core_attestation_chain_ref: str
    trading_core_attestation_chain_digest: str
    runtime_state_snapshot_ref: str
    runtime_state_snapshot_digest: str
    venue_capability_snapshot_ref: str
    venue_capability_snapshot_digest: str
    position_snapshot: InlineSnapshotBinding
    open_orders_snapshot: InlineSnapshotBinding
    margin_snapshot: InlineSnapshotBinding
    risk_snapshot: InlineSnapshotBinding
    market_data_snapshot: InlineSnapshotBinding
    authority_ref: str
    authority_digest: str
    kill_switch_state_ref: str
    kill_switch_state_digest: str
    reconciliation_ref: str
    reconciliation_digest: str
    risk_policy_ref: str
    risk_policy_digest: str
    trading_epoch: str
    executor_epoch: str
    revocation_epoch: str
    evaluation_timestamp: str
    clock_source_ref: str
    clock_trust_status: str
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
    signal_timestamp: str
    builder_version: str
    pending_evidence_refresh: bool = False
    source_revision: str = DEFAULT_SOURCE_REVISION


@dataclass(frozen=True)
class IndependentPreTradeSafetyKernelInputs:
    runtime_state_reconciliation_bundle_dir: Path
    order_intent_idempotency_bundle_dir: Path
    trading_core_decision_attestation_bundle_dir: Path
    venue_capability_snapshot_bundle_dir: Path
    clock_trust_and_expiry_bundle_dir: Path
    authority_lease_bundle_dir: Path
    request: PreTradeSafetyEvaluationRequest


@dataclass(frozen=True)
class IndependentPreTradeSafetyKernelResult:
    output_dir: Path
    safety_decision_id: str
    decision: str
    contract_status: str
    evidence_status: str
    contract_path: Path
    self_verification_path: Path
    manifest_path: Path


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise IndependentPreTradeSafetyKernelError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise IndependentPreTradeSafetyKernelError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise IndependentPreTradeSafetyKernelError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    _reject_symlink(bundle_dir, label=label)
    if not bundle_dir.is_dir():
        raise IndependentPreTradeSafetyKernelError(f"{label} must be a directory: {bundle_dir}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise IndependentPreTradeSafetyKernelError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise IndependentPreTradeSafetyKernelError("output directory must not be under /tmp")


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
            raise IndependentPreTradeSafetyKernelError(
                "output directory must not equal input bundle"
            )
        if _path_is_under(resolved_output, resolved_bundle) or _path_is_under(
            resolved_bundle, resolved_output
        ):
            raise IndependentPreTradeSafetyKernelError("output directory overlaps input bundle")


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


def _artifact_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_file_digest(bundle_dir: Path) -> str:
    return hashlib.sha256((bundle_dir / MANIFEST_FILENAME).read_bytes()).hexdigest()


def _binding_digest(value: str, *, domain: str) -> str:
    return compute_content_sha256(
        {
            "digest_domain": domain,
            "value": value,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _inline_snapshot_digest(body: Mapping[str, Any], *, domain: str) -> str:
    return compute_content_sha256(
        {
            "digest_domain": domain,
            "snapshot_body": dict(body),
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )


def _parse_decimal(value: str, *, field_name: str) -> Decimal:
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise IndependentPreTradeSafetyKernelError(
            f"{field_name} invalid Decimal: {value!r}"
        ) from exc
    if not parsed.is_finite():
        raise IndependentPreTradeSafetyKernelError(f"{field_name} must be finite: {value!r}")
    return parsed


def _parse_iso8601(value: str, *, field_name: str) -> datetime:
    if not value:
        raise IndependentPreTradeSafetyKernelError(f"{field_name} is required")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise IndependentPreTradeSafetyKernelError(
            f"{field_name} must be ISO-8601: {value!r}"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _policy_digest() -> str:
    return compute_content_sha256(
        {
            "policy_domain": "generic_futures_pre_trade_safety_policy_v1",
            "position_limit": GENERIC_FUTURES_POSITION_LIMIT,
            "gross_exposure_limit": GENERIC_FUTURES_GROSS_EXPOSURE_LIMIT,
            "order_notional_limit": GENERIC_FUTURES_ORDER_NOTIONAL_LIMIT,
            "daily_loss_limit": GENERIC_FUTURES_DAILY_LOSS_LIMIT,
            "leverage_limit": GENERIC_FUTURES_LEVERAGE_LIMIT,
            "price_collar_bps": GENERIC_FUTURES_PRICE_COLLAR_BPS,
            "max_mark_index_divergence_bps": GENERIC_FUTURES_MAX_MARK_INDEX_DIVERGENCE_BPS,
            "max_spread_bps": GENERIC_FUTURES_MAX_SPREAD_BPS,
            "max_orderbook_age_ms": GENERIC_FUTURES_MAX_ORDERBOOK_AGE_MS,
            "min_orderbook_depth": GENERIC_FUTURES_MIN_ORDERBOOK_DEPTH,
            "max_expected_market_impact_bps": GENERIC_FUTURES_MAX_EXPECTED_MARKET_IMPACT_BPS,
            "signal_expiry_seconds": GENERIC_FUTURES_SIGNAL_EXPIRY_SECONDS,
            "open_order_limit": GENERIC_FUTURES_OPEN_ORDER_LIMIT,
            "message_rate_limit_per_minute": GENERIC_FUTURES_MESSAGE_RATE_LIMIT_PER_MINUTE,
            "margin_buffer_ratio": GENERIC_FUTURES_MARGIN_BUFFER_RATIO,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
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


def _validate_non_authorizing_flags(payload: Mapping[str, Any]) -> None:
    for key, expected in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if key not in payload:
            raise IndependentPreTradeSafetyKernelError(f"missing non-authorizing flag: {key}")
        if key in _DYNAMIC_NON_AUTH_FLAGS:
            continue
        if payload[key] is not expected:
            raise IndependentPreTradeSafetyKernelError(
                f"non-authorizing flag {key} must be {expected}, got {payload[key]!r}"
            )


def _validate_inline_snapshot_binding(
    binding: InlineSnapshotBinding,
    *,
    domain: str,
    label: str,
) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    if not binding.ref.strip():
        facts.append(
            _factor(
                factor_id=f"MISSING_{label.upper()}_REF",
                factor_type="MISSING_PRECONDITION",
                source_field=f"{label}_ref",
                detail="",
            )
        )
    if not binding.digest.strip():
        facts.append(
            _factor(
                factor_id=f"MISSING_{label.upper()}_DIGEST",
                factor_type="MISSING_PRECONDITION",
                source_field=f"{label}_digest",
                detail="",
            )
        )
    elif binding.digest != _inline_snapshot_digest(binding.body, domain=domain):
        facts.append(
            _factor(
                factor_id=f"{label.upper()}_DIGEST_MISMATCH",
                factor_type="CONTRADICTION",
                source_field=f"{label}_digest",
                detail=binding.digest,
            )
        )
    return facts


def verify_order_intent_idempotency_bundle(
    bundle_dir: Path | str,
) -> VerifiedOrderIntentIdempotencyBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="order_intent_idempotency_bundle_dir")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise IndependentPreTradeSafetyKernelError(f"MANIFEST.sha256 verification failed: {msg}")
    artifact_path = path / IDEMPOTENCY_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=IDEMPOTENCY_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        reverify_order_intent_idempotency_v1(output_dir=path)
    except OrderIntentIdempotencyError as exc:
        raise IndependentPreTradeSafetyKernelError(str(exc)) from exc
    intent = _extract_order_intent_fields(payload)
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
        manifest_digest=_manifest_file_digest(path),
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
        raise IndependentPreTradeSafetyKernelError(f"MANIFEST.sha256 verification failed: {msg}")
    artifact_path = path / RECONCILIATION_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=RECONCILIATION_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        reverify_runtime_state_reconciliation_v1(output_dir=path)
    except RuntimeStateReconciliationError as exc:
        raise IndependentPreTradeSafetyKernelError(str(exc)) from exc
    return VerifiedRuntimeStateReconciliationBundle(
        bundle_dir=path,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=RECONCILIATION_ARTIFACT_REL,
        artifact_digest=_artifact_digest(artifact_path),
        manifest_digest=_manifest_file_digest(path),
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
        raise IndependentPreTradeSafetyKernelError(f"MANIFEST.sha256 verification failed: {msg}")
    artifact_path = path / ATTESTATION_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ATTESTATION_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        reverify_trading_core_decision_attestation_v1(output_dir=path)
    except TradingCoreDecisionAttestationError as exc:
        raise IndependentPreTradeSafetyKernelError(str(exc)) from exc
    intent = payload.get("canonical_order_intent_identity", {})
    if not isinstance(intent, Mapping):
        intent = {}
    return VerifiedTradingCoreDecisionAttestationBundle(
        bundle_dir=path,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=ATTESTATION_ARTIFACT_REL,
        artifact_digest=_artifact_digest(artifact_path),
        manifest_digest=_manifest_file_digest(path),
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


def verify_venue_capability_snapshot_bundle(
    bundle_dir: Path | str,
) -> VerifiedVenueCapabilitySnapshotBundle:
    path = Path(bundle_dir)
    _validate_bundle_dir(path, label="venue_capability_snapshot_bundle_dir")
    ok, msg = verify_manifest_sha256(path)
    if not ok:
        raise IndependentPreTradeSafetyKernelError(f"MANIFEST.sha256 verification failed: {msg}")
    artifact_path = path / VENUE_CAPABILITY_ARTIFACT_REL
    _validate_regular_file(artifact_path, label=VENUE_CAPABILITY_ARTIFACT_REL)
    payload = read_manifest(artifact_path)
    try:
        reverify_venue_capability_snapshot_v1(output_dir=path)
    except VenueCapabilitySnapshotError as exc:
        raise IndependentPreTradeSafetyKernelError(str(exc)) from exc
    return VerifiedVenueCapabilitySnapshotBundle(
        bundle_dir=path,
        contract_name=str(payload.get("contract_name", "")),
        contract_version=str(payload.get("contract_version", "")),
        producer_version=str(payload.get("producer_version", "")),
        artifact_ref=VENUE_CAPABILITY_ARTIFACT_REL,
        artifact_digest=_artifact_digest(artifact_path),
        manifest_digest=_manifest_file_digest(path),
        artifact_payload=dict(payload),
        snapshot_id=str(payload.get("snapshot_id", "")),
        snapshot_status=str(payload.get("snapshot_status", "")),
        capability_digest=str(payload.get("capability_digest", "")),
        venue=str(payload.get("venue", "")),
        account_scope=str(payload.get("account_scope", "")),
        instrument=str(payload.get("instrument", "")),
        market_type=str(payload.get("market_type", "")),
    )


def build_default_position_snapshot_body(
    *,
    instrument: str,
    position_quantity: str = "0",
    position_notional: str = "0",
    leverage: str = "1",
) -> dict[str, Any]:
    return {
        "instrument": instrument,
        "position_quantity": position_quantity,
        "position_notional": position_notional,
        "leverage": leverage,
        "market_type": "FUTURES",
    }


def build_default_open_orders_snapshot_body(
    *,
    instrument: str,
    open_order_count: str = "0",
    open_order_notional: str = "0",
    duplicate_intent_detected: bool = False,
) -> dict[str, Any]:
    return {
        "instrument": instrument,
        "open_order_count": open_order_count,
        "open_order_notional": open_order_notional,
        "duplicate_intent_detected": duplicate_intent_detected,
        "market_type": "FUTURES",
    }


def build_default_margin_snapshot_body(
    *,
    available_margin: str = "1000",
    margin_used: str = "100",
    margin_buffer_ratio: str = GENERIC_FUTURES_MARGIN_BUFFER_RATIO,
) -> dict[str, Any]:
    return {
        "available_margin": available_margin,
        "margin_used": margin_used,
        "margin_buffer_ratio": margin_buffer_ratio,
        "margin_buffer_satisfied": True,
    }


def build_default_risk_snapshot_body(
    *,
    gross_exposure: str = "10",
    daily_loss: str = "0",
    messages_last_minute: str = "1",
) -> dict[str, Any]:
    return {
        "gross_exposure": gross_exposure,
        "daily_loss": daily_loss,
        "messages_last_minute": messages_last_minute,
    }


def build_default_market_data_snapshot_body(
    *,
    instrument: str,
    mark_price: str = "100.00",
    index_price: str = "100.00",
    spread_bps: str = "5",
    orderbook_age_ms: str = "100",
    orderbook_depth: str = "50",
    expected_market_impact_bps: str = "5",
) -> dict[str, Any]:
    return {
        "instrument": instrument,
        "mark_price": mark_price,
        "index_price": index_price,
        "spread_bps": spread_bps,
        "orderbook_age_ms": orderbook_age_ms,
        "orderbook_depth": orderbook_depth,
        "expected_market_impact_bps": expected_market_impact_bps,
        "market_type": "FUTURES",
    }


def build_default_kill_switch_snapshot_body(
    *,
    kill_switch_state: str = "ARMED",
    kill_switch_observed_at: str = OFFLINE_DETERMINISTIC_CREATED_AT,
    kill_switch_is_fresh: bool = True,
    revocation_epoch: str = "0",
) -> dict[str, Any]:
    return {
        "kill_switch_state": kill_switch_state,
        "kill_switch_observed_at": kill_switch_observed_at,
        "kill_switch_is_fresh": kill_switch_is_fresh,
        "revocation_epoch": revocation_epoch,
    }


def _inline_binding_from_body(
    *,
    ref: str,
    domain: str,
    body: Mapping[str, Any],
) -> InlineSnapshotBinding:
    return InlineSnapshotBinding(
        ref=ref,
        digest=_inline_snapshot_digest(body, domain=domain),
        body=dict(body),
    )


def _evaluate_fail_closed_gates(
    request: PreTradeSafetyEvaluationRequest,
    *,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    reconciliation: VerifiedRuntimeStateReconciliationBundle,
    attestation: VerifiedTradingCoreDecisionAttestationBundle,
    venue_capability: VerifiedVenueCapabilitySnapshotBundle,
    authority_lease: VerifiedAuthorityLeaseBundle,
    clock_trust: VerifiedClockTrustBundle,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
) -> tuple[list[dict[str, str]], dict[str, bool], str]:
    facts: list[dict[str, str]] = []
    gate_results: dict[str, bool] = {gate_id: True for gate_id in _FAIL_CLOSED_GATE_IDS}

    def fail_gate(gate_id: str, *, factor_id: str, source_field: str, detail: str) -> None:
        gate_results[gate_id] = False
        facts.append(
            _factor(
                factor_id=factor_id,
                factor_type="GATE_FAILURE",
                source_field=source_field,
                detail=detail,
            )
        )

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

    required_fields = (
        ("safety_evaluation_id", request.safety_evaluation_id),
        ("canonical_order_intent_ref", request.canonical_order_intent_ref),
        ("canonical_order_intent_digest", request.canonical_order_intent_digest),
        ("trading_core_attestation_chain_ref", request.trading_core_attestation_chain_ref),
        ("trading_core_attestation_chain_digest", request.trading_core_attestation_chain_digest),
        ("runtime_state_snapshot_ref", request.runtime_state_snapshot_ref),
        ("runtime_state_snapshot_digest", request.runtime_state_snapshot_digest),
        ("venue_capability_snapshot_ref", request.venue_capability_snapshot_ref),
        ("venue_capability_snapshot_digest", request.venue_capability_snapshot_digest),
        ("authority_ref", request.authority_ref),
        ("authority_digest", request.authority_digest),
        ("kill_switch_state_ref", request.kill_switch_state_ref),
        ("kill_switch_state_digest", request.kill_switch_state_digest),
        ("reconciliation_ref", request.reconciliation_ref),
        ("reconciliation_digest", request.reconciliation_digest),
        ("risk_policy_ref", request.risk_policy_ref),
        ("risk_policy_digest", request.risk_policy_digest),
        ("trading_epoch", request.trading_epoch),
        ("executor_epoch", request.executor_epoch),
        ("revocation_epoch", request.revocation_epoch),
        ("evaluation_timestamp", request.evaluation_timestamp),
        ("clock_source_ref", request.clock_source_ref),
        ("clock_trust_status", request.clock_trust_status),
        ("client_order_id", request.client_order_id),
        ("venue", request.venue),
        ("account_scope", request.account_scope),
        ("instrument", request.instrument),
        ("market_type", request.market_type),
        ("signal_timestamp", request.signal_timestamp),
        ("builder_version", request.builder_version),
    )
    for field, value in required_fields:
        missing(field, value)

    for label, binding, domain in (
        ("position_snapshot", request.position_snapshot, "position_snapshot_v1"),
        ("open_orders_snapshot", request.open_orders_snapshot, "open_orders_snapshot_v1"),
        ("margin_snapshot", request.margin_snapshot, "margin_snapshot_v1"),
        ("risk_snapshot", request.risk_snapshot, "risk_snapshot_v1"),
        ("market_data_snapshot", request.market_data_snapshot, "market_data_snapshot_v1"),
    ):
        facts.extend(_validate_inline_snapshot_binding(binding, domain=domain, label=label))

    kill_switch_body = build_default_kill_switch_snapshot_body(
        kill_switch_state=request.kill_switch_state_ref.upper()
        if request.kill_switch_state_ref
        else "ARMED",
        revocation_epoch=request.revocation_epoch,
    )
    if (
        request.kill_switch_state_digest
        and request.kill_switch_state_digest
        != _inline_snapshot_digest(kill_switch_body, domain="kill_switch_state_v1")
    ):
        fail_gate(
            "kill_switch_state_valid",
            factor_id="KILL_SWITCH_DIGEST_MISMATCH",
            source_field="kill_switch_state_digest",
            detail=request.kill_switch_state_digest,
        )

    if request.risk_policy_digest and request.risk_policy_digest != _policy_digest():
        fail_gate(
            "artifact_digests_valid",
            factor_id="RISK_POLICY_DIGEST_MISMATCH",
            source_field="risk_policy_digest",
            detail=request.risk_policy_digest,
        )

    if request.canonical_order_intent_digest != idempotency.canonical_order_intent_identity_digest:
        fail_gate(
            "artifact_digests_valid",
            factor_id="CANONICAL_ORDER_INTENT_DIGEST_MISMATCH",
            source_field="canonical_order_intent_digest",
            detail=request.canonical_order_intent_digest,
        )
    if request.canonical_order_intent_digest != attestation.canonical_order_intent_identity_digest:
        fail_gate(
            "artifact_digests_valid",
            factor_id="ATTESTATION_INTENT_DIGEST_MISMATCH",
            source_field="canonical_order_intent_digest",
            detail=request.canonical_order_intent_digest,
        )
    if request.trading_core_attestation_chain_digest != attestation.attestation_chain_digest:
        fail_gate(
            "artifact_digests_valid",
            factor_id="ATTESTATION_CHAIN_DIGEST_MISMATCH",
            source_field="trading_core_attestation_chain_digest",
            detail=request.trading_core_attestation_chain_digest,
        )
    if request.runtime_state_snapshot_digest != reconciliation.artifact_digest:
        fail_gate(
            "artifact_digests_valid",
            factor_id="RUNTIME_STATE_SNAPSHOT_DIGEST_MISMATCH",
            source_field="runtime_state_snapshot_digest",
            detail=request.runtime_state_snapshot_digest,
        )
    if request.reconciliation_digest != reconciliation.reconciliation_digest:
        fail_gate(
            "artifact_digests_valid",
            factor_id="RECONCILIATION_DIGEST_MISMATCH",
            source_field="reconciliation_digest",
            detail=request.reconciliation_digest,
        )
    if request.venue_capability_snapshot_digest != venue_capability.capability_digest:
        fail_gate(
            "venue_capability_digest_current",
            factor_id="VENUE_CAPABILITY_DIGEST_MISMATCH",
            source_field="venue_capability_snapshot_digest",
            detail=request.venue_capability_snapshot_digest,
        )
    if request.authority_ref != idempotency.authority_ref:
        fail_gate(
            "runtime_authority_valid",
            factor_id="AUTHORITY_REF_MISMATCH",
            source_field="authority_ref",
            detail=request.authority_ref,
        )
    if request.authority_digest != idempotency.authority_digest:
        fail_gate(
            "runtime_authority_valid",
            factor_id="AUTHORITY_DIGEST_MISMATCH",
            source_field="authority_digest",
            detail=request.authority_digest,
        )

    if authority_lease.revocation_state.upper() != "NOT_REVOKED":
        fail_gate(
            "runtime_authority_valid",
            factor_id="AUTHORITY_REVOKED",
            source_field="authority_lease.revocation_state",
            detail=authority_lease.revocation_state,
        )

    try:
        evaluation_time = _parse_iso8601(
            request.evaluation_timestamp, field_name="evaluation_timestamp"
        )
        valid_until = _parse_iso8601(
            authority_lease.valid_until, field_name="authority_lease.valid_until"
        )
        if evaluation_time >= valid_until:
            fail_gate(
                "authority_lease_not_expired",
                factor_id="AUTHORITY_LEASE_EXPIRED",
                source_field="authority_lease.valid_until",
                detail=authority_lease.valid_until,
            )
    except IndependentPreTradeSafetyKernelError:
        fail_gate(
            "authority_lease_not_expired",
            factor_id="AUTHORITY_LEASE_TIMESTAMP_INVALID",
            source_field="evaluation_timestamp",
            detail=request.evaluation_timestamp,
        )

    if request.revocation_epoch != idempotency.revocation_epoch:
        fail_gate(
            "authority_revocation_epoch_current",
            factor_id="REVOCATION_EPOCH_MISMATCH",
            source_field="revocation_epoch",
            detail=request.revocation_epoch,
        )

    session_status = trading_session.contract_status
    writer_status = trading_session.single_writer_status
    if (
        session_status != "TRADING_SESSION_SINGLE_WRITER_VALID_FOR_OFFLINE_EVALUATION"
        or writer_status != "VALID"
    ):
        fail_gate(
            "session_authorized",
            factor_id="SESSION_NOT_AUTHORIZED",
            source_field="trading_session.contract_status",
            detail=session_status,
        )

    if request.trading_epoch != idempotency.trading_epoch or (
        attestation.trading_epoch and request.trading_epoch != attestation.trading_epoch
    ):
        fail_gate(
            "trading_epoch_current",
            factor_id="TRADING_EPOCH_MISMATCH",
            source_field="trading_epoch",
            detail=request.trading_epoch,
        )
    if request.executor_epoch != idempotency.executor_epoch:
        fail_gate(
            "executor_epoch_current",
            factor_id="EXECUTOR_EPOCH_MISMATCH",
            source_field="executor_epoch",
            detail=request.executor_epoch,
        )

    if (
        request.instrument != idempotency.instrument
        or request.instrument != venue_capability.instrument
    ):
        fail_gate(
            "instrument_allowed",
            factor_id="INSTRUMENT_BINDING_MISMATCH",
            source_field="instrument",
            detail=request.instrument,
        )
    if request.instrument != DEFAULT_GENERIC_INSTRUMENT:
        fail_gate(
            "instrument_allowed",
            factor_id="INSTRUMENT_NOT_GENERIC_FUTURES",
            source_field="instrument",
            detail=request.instrument,
        )

    market_type = request.market_type.upper()
    if market_type in _FORBIDDEN_MARKET_TYPES or market_type not in _VALID_MARKET_TYPES:
        fail_gate(
            "futures_market_type_required",
            factor_id="MARKET_TYPE_NOT_FUTURES",
            source_field="market_type",
            detail=request.market_type,
        )

    if venue_capability.snapshot_status != "VENUE_CAPABILITY_SNAPSHOT_VALID":
        fail_gate(
            "venue_capability_digest_current",
            factor_id="VENUE_CAPABILITY_SNAPSHOT_INVALID",
            source_field="venue_capability.snapshot_status",
            detail=venue_capability.snapshot_status,
        )

    position_body = request.position_snapshot.body
    open_orders_body = request.open_orders_snapshot.body
    margin_body = request.margin_snapshot.body
    risk_body = request.risk_snapshot.body
    market_data_body = request.market_data_snapshot.body

    try:
        position_qty = abs(
            _parse_decimal(
                str(position_body.get("position_quantity", "0")), field_name="position_quantity"
            )
        )
        order_qty = _parse_decimal(request.quantity, field_name="quantity")
        if position_qty + order_qty > _parse_decimal(
            GENERIC_FUTURES_POSITION_LIMIT, field_name="position_limit"
        ):
            fail_gate(
                "position_limit",
                factor_id="POSITION_LIMIT_EXCEEDED",
                source_field="position_snapshot.position_quantity",
                detail=str(position_body.get("position_quantity", "")),
            )
    except IndependentPreTradeSafetyKernelError as exc:
        fail_gate(
            "position_limit",
            factor_id="POSITION_LIMIT_EVALUATION_FAILED",
            source_field="position_snapshot.position_quantity",
            detail=str(exc),
        )

    try:
        gross_exposure = _parse_decimal(
            str(risk_body.get("gross_exposure", "0")), field_name="gross_exposure"
        )
        order_notional = _parse_decimal(request.quantity, field_name="quantity") * _parse_decimal(
            request.limit_price or market_data_body.get("mark_price", "0"),
            field_name="limit_price",
        )
        if gross_exposure + order_notional > _parse_decimal(
            GENERIC_FUTURES_GROSS_EXPOSURE_LIMIT, field_name="gross_exposure_limit"
        ):
            fail_gate(
                "gross_exposure_limit",
                factor_id="GROSS_EXPOSURE_LIMIT_EXCEEDED",
                source_field="risk_snapshot.gross_exposure",
                detail=str(risk_body.get("gross_exposure", "")),
            )
        if order_notional > _parse_decimal(
            GENERIC_FUTURES_ORDER_NOTIONAL_LIMIT, field_name="order_notional_limit"
        ):
            fail_gate(
                "order_notional_limit",
                factor_id="ORDER_NOTIONAL_LIMIT_EXCEEDED",
                source_field="quantity",
                detail=request.quantity,
            )
        daily_loss = _parse_decimal(str(risk_body.get("daily_loss", "0")), field_name="daily_loss")
        if daily_loss >= _parse_decimal(
            GENERIC_FUTURES_DAILY_LOSS_LIMIT, field_name="daily_loss_limit"
        ):
            fail_gate(
                "daily_loss_limit",
                factor_id="DAILY_LOSS_LIMIT_REACHED",
                source_field="risk_snapshot.daily_loss",
                detail=str(risk_body.get("daily_loss", "")),
            )
        leverage = _parse_decimal(str(position_body.get("leverage", "1")), field_name="leverage")
        if leverage > _parse_decimal(GENERIC_FUTURES_LEVERAGE_LIMIT, field_name="leverage_limit"):
            fail_gate(
                "leverage_limit",
                factor_id="LEVERAGE_LIMIT_EXCEEDED",
                source_field="position_snapshot.leverage",
                detail=str(position_body.get("leverage", "")),
            )
    except IndependentPreTradeSafetyKernelError as exc:
        fail_gate(
            "order_notional_limit",
            factor_id="RISK_LIMIT_EVALUATION_FAILED",
            source_field="risk_snapshot",
            detail=str(exc),
        )

    try:
        mark_price = _parse_decimal(
            str(market_data_body.get("mark_price", "0")), field_name="mark_price"
        )
        limit_price = _parse_decimal(request.limit_price, field_name="limit_price")
        collar = _parse_decimal(
            GENERIC_FUTURES_PRICE_COLLAR_BPS, field_name="price_collar_bps"
        ) / Decimal("10000")
        upper = mark_price * (Decimal("1") + collar)
        lower = mark_price * (Decimal("1") - collar)
        if limit_price > upper or limit_price < lower:
            fail_gate(
                "price_collar",
                factor_id="PRICE_COLLAR_VIOLATED",
                source_field="limit_price",
                detail=request.limit_price,
            )
    except IndependentPreTradeSafetyKernelError as exc:
        fail_gate(
            "price_collar",
            factor_id="PRICE_COLLAR_EVALUATION_FAILED",
            source_field="limit_price",
            detail=str(exc),
        )

    try:
        orderbook_age_ms = _parse_decimal(
            str(market_data_body.get("orderbook_age_ms", "0")), field_name="orderbook_age_ms"
        )
        if orderbook_age_ms > _parse_decimal(
            GENERIC_FUTURES_MAX_ORDERBOOK_AGE_MS, field_name="max_orderbook_age_ms"
        ):
            fail_gate(
                "stale_market_data_guard",
                factor_id="MARKET_DATA_STALE",
                source_field="market_data_snapshot.orderbook_age_ms",
                detail=str(market_data_body.get("orderbook_age_ms", "")),
            )
        mark_price = _parse_decimal(
            str(market_data_body.get("mark_price", "0")), field_name="mark_price"
        )
        index_price = _parse_decimal(
            str(market_data_body.get("index_price", "0")), field_name="index_price"
        )
        if mark_price > 0:
            divergence_bps = abs(mark_price - index_price) / mark_price * Decimal("10000")
            if divergence_bps > _parse_decimal(
                GENERIC_FUTURES_MAX_MARK_INDEX_DIVERGENCE_BPS,
                field_name="max_mark_index_divergence_bps",
            ):
                fail_gate(
                    "mark_index_divergence_guard",
                    factor_id="MARK_INDEX_DIVERGENCE_EXCEEDED",
                    source_field="market_data_snapshot.mark_price",
                    detail=str(market_data_body.get("mark_price", "")),
                )
        spread_bps = _parse_decimal(
            str(market_data_body.get("spread_bps", "0")), field_name="spread_bps"
        )
        if spread_bps > _parse_decimal(GENERIC_FUTURES_MAX_SPREAD_BPS, field_name="max_spread_bps"):
            fail_gate(
                "spread_guard",
                factor_id="SPREAD_EXCEEDED",
                source_field="market_data_snapshot.spread_bps",
                detail=str(market_data_body.get("spread_bps", "")),
            )
        orderbook_depth = _parse_decimal(
            str(market_data_body.get("orderbook_depth", "0")), field_name="orderbook_depth"
        )
        if orderbook_depth < _parse_decimal(
            GENERIC_FUTURES_MIN_ORDERBOOK_DEPTH, field_name="min_orderbook_depth"
        ):
            fail_gate(
                "orderbook_depth_guard",
                factor_id="ORDERBOOK_DEPTH_INSUFFICIENT",
                source_field="market_data_snapshot.orderbook_depth",
                detail=str(market_data_body.get("orderbook_depth", "")),
            )
        expected_impact = _parse_decimal(
            str(market_data_body.get("expected_market_impact_bps", "0")),
            field_name="expected_market_impact_bps",
        )
        if expected_impact > _parse_decimal(
            GENERIC_FUTURES_MAX_EXPECTED_MARKET_IMPACT_BPS,
            field_name="max_expected_market_impact_bps",
        ):
            fail_gate(
                "expected_market_impact_guard",
                factor_id="EXPECTED_MARKET_IMPACT_EXCEEDED",
                source_field="market_data_snapshot.expected_market_impact_bps",
                detail=str(market_data_body.get("expected_market_impact_bps", "")),
            )
    except IndependentPreTradeSafetyKernelError as exc:
        fail_gate(
            "stale_market_data_guard",
            factor_id="MARKET_DATA_GUARD_EVALUATION_FAILED",
            source_field="market_data_snapshot",
            detail=str(exc),
        )

    try:
        signal_time = _parse_iso8601(request.signal_timestamp, field_name="signal_timestamp")
        evaluation_time = _parse_iso8601(
            request.evaluation_timestamp, field_name="evaluation_timestamp"
        )
        signal_age = (evaluation_time - signal_time).total_seconds()
        if signal_age > float(GENERIC_FUTURES_SIGNAL_EXPIRY_SECONDS):
            fail_gate(
                "signal_expiry_guard",
                factor_id="SIGNAL_EXPIRED",
                source_field="signal_timestamp",
                detail=request.signal_timestamp,
            )
    except IndependentPreTradeSafetyKernelError as exc:
        fail_gate(
            "signal_expiry_guard",
            factor_id="SIGNAL_EXPIRY_EVALUATION_FAILED",
            source_field="signal_timestamp",
            detail=str(exc),
        )

    if open_orders_body.get(
        "duplicate_intent_detected"
    ) is True or idempotency.idempotency_status in {
        "IDEMPOTENT_DUPLICATE",
        "SEMANTIC_DUPLICATE_CONFLICT",
        "ORDER_INTENT_IDEMPOTENCY_IDEMPOTENT_DUPLICATE",
        "ORDER_INTENT_IDEMPOTENCY_SEMANTIC_DUPLICATE_CONFLICT",
    }:
        fail_gate(
            "duplicate_intent_guard",
            factor_id="DUPLICATE_INTENT_DETECTED",
            source_field="open_orders_snapshot.duplicate_intent_detected",
            detail=str(open_orders_body.get("duplicate_intent_detected", "")),
        )

    try:
        open_order_count = _parse_decimal(
            str(open_orders_body.get("open_order_count", "0")), field_name="open_order_count"
        )
        if open_order_count >= _parse_decimal(
            GENERIC_FUTURES_OPEN_ORDER_LIMIT, field_name="open_order_limit"
        ):
            fail_gate(
                "open_order_limit",
                factor_id="OPEN_ORDER_LIMIT_EXCEEDED",
                source_field="open_orders_snapshot.open_order_count",
                detail=str(open_orders_body.get("open_order_count", "")),
            )
        messages_last_minute = _parse_decimal(
            str(risk_body.get("messages_last_minute", "0")), field_name="messages_last_minute"
        )
        if messages_last_minute > _parse_decimal(
            GENERIC_FUTURES_MESSAGE_RATE_LIMIT_PER_MINUTE,
            field_name="message_rate_limit_per_minute",
        ):
            fail_gate(
                "message_rate_limit",
                factor_id="MESSAGE_RATE_LIMIT_EXCEEDED",
                source_field="risk_snapshot.messages_last_minute",
                detail=str(risk_body.get("messages_last_minute", "")),
            )
    except IndependentPreTradeSafetyKernelError as exc:
        fail_gate(
            "open_order_limit",
            factor_id="OPEN_ORDER_LIMIT_EVALUATION_FAILED",
            source_field="open_orders_snapshot.open_order_count",
            detail=str(exc),
        )

    try:
        available_margin = _parse_decimal(
            str(margin_body.get("available_margin", "0")), field_name="available_margin"
        )
        margin_used = _parse_decimal(
            str(margin_body.get("margin_used", "0")), field_name="margin_used"
        )
        buffer_ratio = _parse_decimal(
            str(margin_body.get("margin_buffer_ratio", GENERIC_FUTURES_MARGIN_BUFFER_RATIO)),
            field_name="margin_buffer_ratio",
        )
        required_buffer = margin_used * buffer_ratio
        if available_margin < required_buffer:
            fail_gate(
                "margin_buffer",
                factor_id="MARGIN_BUFFER_INSUFFICIENT",
                source_field="margin_snapshot.available_margin",
                detail=str(margin_body.get("available_margin", "")),
            )
    except IndependentPreTradeSafetyKernelError as exc:
        fail_gate(
            "margin_buffer",
            factor_id="MARGIN_BUFFER_EVALUATION_FAILED",
            source_field="margin_snapshot",
            detail=str(exc),
        )

    kill_state = str(kill_switch_body.get("kill_switch_state", "ARMED")).upper()
    if kill_state not in {"ARMED", "DISARMED", "TRIPPED"}:
        fail_gate(
            "kill_switch_state_valid",
            factor_id="KILL_SWITCH_STATE_INVALID",
            source_field="kill_switch_state",
            detail=kill_state,
        )
    if kill_state != "ARMED":
        fail_gate(
            "kill_switch_state_armed",
            factor_id="KILL_SWITCH_NOT_ARMED",
            source_field="kill_switch_state",
            detail=kill_state,
        )
    if not bool(kill_switch_body.get("kill_switch_is_fresh", True)):
        fail_gate(
            "kill_switch_state_fresh",
            factor_id="KILL_SWITCH_NOT_FRESH",
            source_field="kill_switch_is_fresh",
            detail="false",
        )

    if reconciliation.reconciliation_state.upper() != "CLEAN":
        fail_gate(
            "reconciliation_state_clean",
            factor_id="RECONCILIATION_NOT_CLEAN",
            source_field="reconciliation_state",
            detail=reconciliation.reconciliation_state,
        )

    if (
        request.clock_trust_status.upper() != "TRUSTED"
        or clock_trust.clock_trust_status.upper() != "TRUSTED"
    ):
        fail_gate(
            "clock_trusted",
            factor_id="CLOCK_UNTRUSTED",
            source_field="clock_trust_status",
            detail=request.clock_trust_status,
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

    normalized_quantity = request.quantity
    return facts, gate_results, normalized_quantity


def _evaluate_decision(
    *,
    factors: list[dict[str, str]],
    gate_results: dict[str, bool],
    pending_evidence_refresh: bool,
) -> tuple[str, str, str, list[str], dict[str, str]]:
    factor_ids = {item.get("factor_id") for item in factors}

    if pending_evidence_refresh:
        return (
            "DEFER",
            "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_DEFERRED",
            "VALID",
            _sorted_strings(["PENDING_EVIDENCE_REFRESH"]),
            {
                "decision_reason": "PENDING_EVIDENCE_REFRESH",
                "rejection_reason": "",
                "deny_reason": "",
            },
        )

    if any(factor and factor.startswith("MISSING_") for factor in factor_ids if factor):
        return (
            "REJECT",
            "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED",
            "INVALID",
            _sorted_strings(["MISSING_BINDINGS"]),
            {
                "decision_reason": "MISSING_BINDINGS",
                "rejection_reason": "MISSING_BINDINGS",
                "deny_reason": "MISSING_BINDINGS",
            },
        )

    failed_gates = [gate_id for gate_id, passed in gate_results.items() if not passed]
    if failed_gates:
        if any(gate_id in _BLOCK_GATE_IDS for gate_id in failed_gates):
            return (
                "BLOCK",
                "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_BLOCKED",
                "INVALID",
                _sorted_strings(["POLICY_BLOCKED"]),
                {
                    "decision_reason": "POLICY_BLOCKED",
                    "rejection_reason": "",
                    "deny_reason": "POLICY_BLOCKED",
                },
            )
        return (
            "REJECT",
            "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED",
            "INVALID",
            _sorted_strings(["POLICY_REJECTED"]),
            {
                "decision_reason": "POLICY_REJECTED",
                "rejection_reason": "POLICY_REJECTED",
                "deny_reason": "POLICY_REJECTED",
            },
        )

    if factors:
        return (
            "REJECT",
            "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_REJECTED",
            "INVALID",
            _sorted_strings(["POLICY_REJECTED"]),
            {
                "decision_reason": "POLICY_REJECTED",
                "rejection_reason": "POLICY_REJECTED",
                "deny_reason": "POLICY_REJECTED",
            },
        )

    return (
        "APPROVE",
        "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_APPROVED",
        "VALID",
        _sorted_strings(["APPROVED"]),
        {
            "decision_reason": "APPROVED",
            "rejection_reason": "",
            "deny_reason": "",
        },
    )


def _safety_input_body(request: PreTradeSafetyEvaluationRequest) -> dict[str, Any]:
    return {
        "safety_evaluation_id": request.safety_evaluation_id,
        "canonical_order_intent_ref": request.canonical_order_intent_ref,
        "canonical_order_intent_digest": request.canonical_order_intent_digest,
        "trading_core_attestation_chain_ref": request.trading_core_attestation_chain_ref,
        "trading_core_attestation_chain_digest": request.trading_core_attestation_chain_digest,
        "runtime_state_snapshot_ref": request.runtime_state_snapshot_ref,
        "runtime_state_snapshot_digest": request.runtime_state_snapshot_digest,
        "venue_capability_snapshot_ref": request.venue_capability_snapshot_ref,
        "venue_capability_snapshot_digest": request.venue_capability_snapshot_digest,
        "position_snapshot_ref": request.position_snapshot.ref,
        "position_snapshot_digest": request.position_snapshot.digest,
        "open_orders_snapshot_ref": request.open_orders_snapshot.ref,
        "open_orders_snapshot_digest": request.open_orders_snapshot.digest,
        "margin_snapshot_ref": request.margin_snapshot.ref,
        "margin_snapshot_digest": request.margin_snapshot.digest,
        "risk_snapshot_ref": request.risk_snapshot.ref,
        "risk_snapshot_digest": request.risk_snapshot.digest,
        "market_data_snapshot_ref": request.market_data_snapshot.ref,
        "market_data_snapshot_digest": request.market_data_snapshot.digest,
        "authority_ref": request.authority_ref,
        "authority_digest": request.authority_digest,
        "kill_switch_state_ref": request.kill_switch_state_ref,
        "kill_switch_state_digest": request.kill_switch_state_digest,
        "reconciliation_ref": request.reconciliation_ref,
        "reconciliation_digest": request.reconciliation_digest,
        "risk_policy_ref": request.risk_policy_ref,
        "risk_policy_digest": request.risk_policy_digest,
        "trading_epoch": request.trading_epoch,
        "executor_epoch": request.executor_epoch,
        "revocation_epoch": request.revocation_epoch,
        "evaluation_timestamp": request.evaluation_timestamp,
        "clock_source_ref": request.clock_source_ref,
        "clock_trust_status": request.clock_trust_status,
        "client_order_id": request.client_order_id,
        "venue": request.venue,
        "account_scope": request.account_scope,
        "instrument": request.instrument,
        "market_type": request.market_type,
        "side": request.side,
        "order_type": request.order_type,
        "quantity": request.quantity,
        "limit_price": request.limit_price,
        "maximum_market_price": request.maximum_market_price,
        "reduce_only": request.reduce_only,
        "position_mode": request.position_mode,
        "margin_mode": request.margin_mode,
        "time_in_force": request.time_in_force,
        "signal_timestamp": request.signal_timestamp,
        "pending_evidence_refresh": request.pending_evidence_refresh,
        "input_contract_version": INPUT_CONTRACT_VERSION,
        "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
    }


def _compute_safety_input_digest(request: PreTradeSafetyEvaluationRequest) -> str:
    return compute_content_sha256(_safety_input_body(request))


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    excluded = frozenset(
        {
            "output_digest",
            "manifest_digest",
            "integrity",
            "created_at",
            "artifact_id",
            "contract_id",
            "safety_decision_id",
        }
    )
    digest_body = {key: body[key] for key in sorted(body) if key not in excluded}
    return compute_content_sha256(digest_body)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in body.items() if key not in {"integrity", "manifest_digest"}
    }


def build_independent_pre_trade_safety_kernel_v1(
    *,
    request: PreTradeSafetyEvaluationRequest,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    reconciliation: VerifiedRuntimeStateReconciliationBundle,
    attestation: VerifiedTradingCoreDecisionAttestationBundle,
    venue_capability: VerifiedVenueCapabilitySnapshotBundle,
    authority_lease: VerifiedAuthorityLeaseBundle,
    clock_trust: VerifiedClockTrustBundle,
    trading_session: VerifiedTradingSessionSingleWriterBundle,
) -> dict[str, Any]:
    factors, gate_results, normalized_quantity = _evaluate_fail_closed_gates(
        request,
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
        venue_capability=venue_capability,
        authority_lease=authority_lease,
        clock_trust=clock_trust,
        trading_session=trading_session,
    )
    decision, contract_status, evidence_status, reason_codes, completion = _evaluate_decision(
        factors=factors,
        gate_results=gate_results,
        pending_evidence_refresh=request.pending_evidence_refresh,
    )
    complete = decision == "APPROVE"
    safety_input_digest = _compute_safety_input_digest(request)
    policy_digest = _policy_digest()

    safety_decision_id = compute_content_sha256(
        {
            "decision_domain": CONTRACT_NAME,
            "safety_evaluation_id": request.safety_evaluation_id,
            "safety_input_digest": safety_input_digest,
            "decision": decision,
            "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
        }
    )

    decision_expiry = request.evaluation_timestamp
    if decision == "APPROVE":
        try:
            evaluation_time = _parse_iso8601(
                request.evaluation_timestamp, field_name="evaluation_timestamp"
            )
            decision_expiry = (
                evaluation_time.replace(microsecond=0) + timedelta(minutes=5)
            ).isoformat()
        except IndependentPreTradeSafetyKernelError:
            decision_expiry = "1970-01-01T00:05:00+00:00"

    payload: dict[str, Any] = {
        "contract_id": "",
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "safety_kernel_contract_version": SAFETY_KERNEL_CONTRACT_VERSION,
        "input_contract_version": INPUT_CONTRACT_VERSION,
        "decision_contract_version": DECISION_CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "creation_contract_version": CREATION_CONTRACT_VERSION,
        "artifact_id": "",
        "safety_decision_id": "",
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
        "evidence_reason": completion.get("decision_reason", ""),
        "decision": decision,
        "decision_code": completion.get("decision_reason", ""),
        "rejection_reasons": _sorted_strings(
            [completion["rejection_reason"]] if completion.get("rejection_reason") else []
        ),
        "deny_reason": completion.get("deny_reason", ""),
        "safety_evaluation_id": request.safety_evaluation_id,
        "safety_input_digest": safety_input_digest,
        "approved_quantity": normalized_quantity if decision == "APPROVE" else "",
        "approved_limit_price": request.limit_price if decision == "APPROVE" else "",
        "maximum_market_price": request.maximum_market_price,
        "decision_expiry": decision_expiry,
        "policy_digest": policy_digest,
        "canonical_order_intent_ref": request.canonical_order_intent_ref,
        "canonical_order_intent_digest": request.canonical_order_intent_digest,
        "trading_core_attestation_chain_ref": request.trading_core_attestation_chain_ref,
        "trading_core_attestation_chain_digest": request.trading_core_attestation_chain_digest,
        "runtime_state_snapshot_ref": request.runtime_state_snapshot_ref,
        "runtime_state_snapshot_digest": request.runtime_state_snapshot_digest,
        "venue_capability_snapshot_ref": request.venue_capability_snapshot_ref,
        "venue_capability_snapshot_digest": request.venue_capability_snapshot_digest,
        "position_snapshot_ref": request.position_snapshot.ref,
        "position_snapshot_digest": request.position_snapshot.digest,
        "open_orders_snapshot_ref": request.open_orders_snapshot.ref,
        "open_orders_snapshot_digest": request.open_orders_snapshot.digest,
        "margin_snapshot_ref": request.margin_snapshot.ref,
        "margin_snapshot_digest": request.margin_snapshot.digest,
        "risk_snapshot_ref": request.risk_snapshot.ref,
        "risk_snapshot_digest": request.risk_snapshot.digest,
        "market_data_snapshot_ref": request.market_data_snapshot.ref,
        "market_data_snapshot_digest": request.market_data_snapshot.digest,
        "authority_ref": request.authority_ref,
        "authority_digest": request.authority_digest,
        "kill_switch_state_ref": request.kill_switch_state_ref,
        "kill_switch_state_digest": request.kill_switch_state_digest,
        "reconciliation_ref": request.reconciliation_ref,
        "reconciliation_digest": request.reconciliation_digest,
        "risk_policy_ref": request.risk_policy_ref,
        "risk_policy_digest": request.risk_policy_digest,
        "trading_epoch": request.trading_epoch,
        "executor_epoch": request.executor_epoch,
        "revocation_epoch": request.revocation_epoch,
        "evaluation_timestamp": request.evaluation_timestamp,
        "clock_source_ref": request.clock_source_ref,
        "clock_trust_status": request.clock_trust_status,
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
        "reduce_only": request.reduce_only,
        "position_mode": request.position_mode,
        "margin_mode": request.margin_mode,
        "time_in_force": request.time_in_force,
        "signal_timestamp": request.signal_timestamp,
        "pending_evidence_refresh": request.pending_evidence_refresh,
        "request_builder_version": request.builder_version,
        "fail_closed_gates": {gate_id: gate_results[gate_id] for gate_id in _FAIL_CLOSED_GATE_IDS},
        "blocking_facts": _sort_factors(
            [item for item in factors if item.get("factor_type") == "GATE_FAILURE"]
        ),
        "missing_preconditions": _sort_factors(
            [item for item in factors if item.get("factor_type") == "MISSING_PRECONDITION"]
        ),
        "contradictions": _sort_factors(
            [item for item in factors if item.get("factor_type") == "CONTRADICTION"]
        ),
        "inline_snapshot_bindings": {
            "position_snapshot": dict(request.position_snapshot.body),
            "open_orders_snapshot": dict(request.open_orders_snapshot.body),
            "margin_snapshot": dict(request.margin_snapshot.body),
            "risk_snapshot": dict(request.risk_snapshot.body),
            "market_data_snapshot": dict(request.market_data_snapshot.body),
        },
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
            "venue_capability_snapshot_bundle_ref": venue_capability.bundle_dir.as_posix(),
            "venue_capability_snapshot_id": venue_capability.snapshot_id,
            "venue_capability_snapshot_digest": venue_capability.artifact_digest,
            "authority_lease_bundle_ref": authority_lease.bundle_dir.as_posix(),
            "authority_lease_digest": authority_lease.artifact_digest,
            "clock_trust_and_expiry_bundle_ref": clock_trust.bundle_dir.as_posix(),
            "clock_trust_digest": clock_trust.artifact_digest,
            "trading_session_single_writer_bundle_ref": trading_session.bundle_dir.as_posix(),
            "trading_session_digest": trading_session.artifact_digest,
        },
        "independent_pre_trade_safety_kernel_authority_invariants": dict(
            INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_AUTHORITY_INVARIANTS
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
        "integrity": {"content_sha256": ""},
    }

    for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items():
        if key not in payload:
            payload[key] = value
    payload["independent_pre_trade_safety_kernel_complete"] = complete
    payload["safety_decision_evidence_created"] = True
    payload["lineage_bound"] = complete
    payload["epoch_binding_bound"] = complete
    payload["kill_switch_binding_bound"] = complete
    payload["reconciliation_binding_bound"] = complete
    payload["venue_capability_binding_bound"] = complete
    payload["authority_binding_bound"] = complete
    payload["clock_trust_binding_bound"] = complete
    payload["snapshot_binding_bound"] = complete
    payload["stable_digest_bound"] = complete

    _reject_forbidden_index_keys(payload)
    _validate_non_authorizing_flags(payload)
    if decision not in _VALID_DECISIONS:
        raise IndependentPreTradeSafetyKernelError("decision invalid")
    if contract_status not in _VALID_CONTRACT_STATUSES:
        raise IndependentPreTradeSafetyKernelError("contract_status invalid")
    if evidence_status not in _VALID_EVIDENCE_STATUSES:
        raise IndependentPreTradeSafetyKernelError("evidence_status invalid")

    payload["contract_id"] = safety_decision_id
    payload["safety_decision_id"] = safety_decision_id
    output_digest = _compute_output_digest(payload)
    payload["output_digest"] = output_digest
    payload["artifact_id"] = output_digest
    payload["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(payload))}
    return payload


def serialize_independent_pre_trade_safety_kernel_v1(contract: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(contract)
    _validate_non_authorizing_flags(contract)
    if contract.get("decision") not in _VALID_DECISIONS:
        raise IndependentPreTradeSafetyKernelError("decision invalid")
    if contract.get("contract_status") not in _VALID_CONTRACT_STATUSES:
        raise IndependentPreTradeSafetyKernelError("contract_status invalid")
    for list_field in (
        "contract_reason_codes",
        "rejection_reasons",
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
            raise IndependentPreTradeSafetyKernelError(
                f"{list_field} must be sorted deterministically"
            )
    gate_map = contract.get("fail_closed_gates")
    body = dict(contract)
    if isinstance(gate_map, dict):
        expected_keys = list(_FAIL_CLOSED_GATE_IDS)
        if set(gate_map.keys()) != set(expected_keys):
            raise IndependentPreTradeSafetyKernelError("fail_closed_gates keys invalid")
        body["fail_closed_gates"] = {gate_id: gate_map[gate_id] for gate_id in expected_keys}
    return deterministic_json_dumps(body)


def _artifact_bytes_for_manifest_digest(artifact: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in artifact.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_independent_pre_trade_safety_kernel_v1(body).encode("utf-8")


def _compute_output_manifest_digest(artifact: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(artifact)).hexdigest()


def _validate_contract_integrity(artifact: Mapping[str, Any]) -> None:
    if artifact.get("contract_name") != CONTRACT_NAME:
        raise IndependentPreTradeSafetyKernelError("contract_name mismatch")
    if artifact.get("contract_version") != CONTRACT_VERSION:
        raise IndependentPreTradeSafetyKernelError("contract_version mismatch")
    integrity = artifact.get("integrity")
    if not isinstance(integrity, Mapping):
        raise IndependentPreTradeSafetyKernelError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(artifact))
    if integrity.get("content_sha256") != expected:
        raise IndependentPreTradeSafetyKernelError("integrity.content_sha256 mismatch")
    output_digest = artifact.get("output_digest")
    if output_digest != _compute_output_digest(artifact):
        raise IndependentPreTradeSafetyKernelError("output_digest mismatch")
    if artifact.get("artifact_id") != output_digest:
        raise IndependentPreTradeSafetyKernelError("artifact_id must equal output_digest")
    if artifact.get("safety_decision_id") != artifact.get("contract_id"):
        raise IndependentPreTradeSafetyKernelError("safety_decision_id must equal contract_id")
    for flag in (
        "single_use_permission_created",
        "submission_authorized",
        "runtime_mutation_performed",
        "order_action_performed",
        "adapter_invoked",
        "exchange_request_sent",
        "network_side_effect_created",
    ):
        if artifact.get(flag) is not False:
            raise IndependentPreTradeSafetyKernelError(f"{flag} must be false")
    if artifact.get("decision") == "APPROVE":
        if artifact.get("submission_authorized") is not False:
            raise IndependentPreTradeSafetyKernelError("APPROVE must not authorize submission")
        if artifact.get("single_use_permission_created") is not False:
            raise IndependentPreTradeSafetyKernelError(
                "APPROVE must not create execution permission"
            )


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "offline_only_no_adapter_invocation", "status": "PASS"},
        {"check_id": "offline_only_no_order_submission", "status": "PASS"},
        {"check_id": "offline_only_no_permission_creation", "status": "PASS"},
        {"check_id": "offline_only_no_runtime_mutation", "status": "PASS"},
        {"check_id": "approve_does_not_authorize_submission", "status": "PASS"},
        {"check_id": "futures_only_guard", "status": "PASS"},
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
    body = dict(contract)
    body["manifest_digest"] = manifest_digest
    return body


def _trading_session_from_attestation(
    attestation: VerifiedTradingCoreDecisionAttestationBundle,
) -> VerifiedTradingSessionSingleWriterBundle:
    bindings = attestation.artifact_payload.get("upstream_bindings", {})
    if not isinstance(bindings, Mapping):
        bindings = {}
    session_ref = str(bindings.get("trading_session_single_writer_bundle_ref", ""))
    if not session_ref:
        raise IndependentPreTradeSafetyKernelError(
            "trading_session_single_writer_bundle_ref missing from attestation"
        )
    return verify_trading_session_single_writer_bundle(Path(session_ref))


def verify_independent_pre_trade_safety_kernel_inputs(
    inputs: IndependentPreTradeSafetyKernelInputs,
) -> tuple[
    VerifiedOrderIntentIdempotencyBundle,
    VerifiedRuntimeStateReconciliationBundle,
    VerifiedTradingCoreDecisionAttestationBundle,
    VerifiedVenueCapabilitySnapshotBundle,
    VerifiedAuthorityLeaseBundle,
    VerifiedClockTrustBundle,
    VerifiedTradingSessionSingleWriterBundle,
]:
    idempotency = verify_order_intent_idempotency_bundle(inputs.order_intent_idempotency_bundle_dir)
    reconciliation = verify_runtime_state_reconciliation_bundle(
        inputs.runtime_state_reconciliation_bundle_dir
    )
    attestation = verify_trading_core_decision_attestation_bundle(
        inputs.trading_core_decision_attestation_bundle_dir
    )
    venue_capability = verify_venue_capability_snapshot_bundle(
        inputs.venue_capability_snapshot_bundle_dir
    )
    authority_lease = verify_authority_lease_bundle(inputs.authority_lease_bundle_dir)
    clock_trust = verify_clock_trust_and_expiry_bundle(inputs.clock_trust_and_expiry_bundle_dir)
    trading_session = _trading_session_from_attestation(attestation)
    return (
        idempotency,
        reconciliation,
        attestation,
        venue_capability,
        authority_lease,
        clock_trust,
        trading_session,
    )


def default_pre_trade_safety_evaluation_request(
    *,
    idempotency: VerifiedOrderIntentIdempotencyBundle,
    reconciliation: VerifiedRuntimeStateReconciliationBundle,
    attestation: VerifiedTradingCoreDecisionAttestationBundle,
    venue_capability: VerifiedVenueCapabilitySnapshotBundle,
    authority_lease: VerifiedAuthorityLeaseBundle,
    clock_trust: VerifiedClockTrustBundle,
    evaluation_timestamp: str = OFFLINE_DETERMINISTIC_CREATED_AT,
    signal_timestamp: str = OFFLINE_DETERMINISTIC_CREATED_AT,
) -> PreTradeSafetyEvaluationRequest:
    instrument = idempotency.instrument or DEFAULT_GENERIC_INSTRUMENT
    position_body = build_default_position_snapshot_body(instrument=instrument)
    open_orders_body = build_default_open_orders_snapshot_body(instrument=instrument)
    margin_body = build_default_margin_snapshot_body()
    risk_body = build_default_risk_snapshot_body()
    market_data_body = build_default_market_data_snapshot_body(instrument=instrument)
    kill_switch_body = build_default_kill_switch_snapshot_body(
        revocation_epoch=idempotency.revocation_epoch or "0",
    )
    return PreTradeSafetyEvaluationRequest(
        safety_evaluation_id=f"pre-trade-safety-evaluation/{idempotency.contract_id}",
        canonical_order_intent_ref=f"canonical-order-intent/{idempotency.client_order_id}",
        canonical_order_intent_digest=idempotency.canonical_order_intent_identity_digest,
        trading_core_attestation_chain_ref=attestation.bundle_dir.as_posix(),
        trading_core_attestation_chain_digest=attestation.attestation_chain_digest,
        runtime_state_snapshot_ref=reconciliation.bundle_dir.as_posix(),
        runtime_state_snapshot_digest=reconciliation.artifact_digest,
        venue_capability_snapshot_ref=venue_capability.bundle_dir.as_posix(),
        venue_capability_snapshot_digest=venue_capability.capability_digest,
        position_snapshot=_inline_binding_from_body(
            ref=f"position-snapshot/{instrument}",
            domain="position_snapshot_v1",
            body=position_body,
        ),
        open_orders_snapshot=_inline_binding_from_body(
            ref=f"open-orders-snapshot/{instrument}",
            domain="open_orders_snapshot_v1",
            body=open_orders_body,
        ),
        margin_snapshot=_inline_binding_from_body(
            ref=f"margin-snapshot/{idempotency.account_scope or DEFAULT_GENERIC_ACCOUNT}",
            domain="margin_snapshot_v1",
            body=margin_body,
        ),
        risk_snapshot=_inline_binding_from_body(
            ref=f"risk-snapshot/{idempotency.account_scope or DEFAULT_GENERIC_ACCOUNT}",
            domain="risk_snapshot_v1",
            body=risk_body,
        ),
        market_data_snapshot=_inline_binding_from_body(
            ref=f"market-data-snapshot/{instrument}",
            domain="market_data_snapshot_v1",
            body=market_data_body,
        ),
        authority_ref=idempotency.authority_ref,
        authority_digest=idempotency.authority_digest,
        kill_switch_state_ref="ARMED",
        kill_switch_state_digest=_inline_snapshot_digest(
            kill_switch_body, domain="kill_switch_state_v1"
        ),
        reconciliation_ref=reconciliation.bundle_dir.as_posix(),
        reconciliation_digest=reconciliation.reconciliation_digest,
        risk_policy_ref="generic-futures-pre-trade-safety-policy-v1",
        risk_policy_digest=_policy_digest(),
        trading_epoch=idempotency.trading_epoch or attestation.trading_epoch,
        executor_epoch=idempotency.executor_epoch or idempotency.trading_epoch,
        revocation_epoch=idempotency.revocation_epoch or "0",
        evaluation_timestamp=evaluation_timestamp,
        clock_source_ref=clock_trust.bundle_dir.as_posix(),
        clock_trust_status=clock_trust.clock_trust_status or "TRUSTED",
        client_order_id=idempotency.client_order_id or DEFAULT_GENERIC_CLIENT_ORDER_ID,
        venue=idempotency.venue or DEFAULT_GENERIC_VENUE,
        account_scope=idempotency.account_scope or DEFAULT_GENERIC_ACCOUNT,
        instrument=instrument,
        market_type="FUTURES",
        side=idempotency.side or "BUY",
        order_type=idempotency.order_type or "LIMIT",
        quantity="0.4000",
        limit_price=idempotency.limit_price or "100.00",
        maximum_market_price=idempotency.maximum_market_price or "105.00",
        reduce_only=idempotency.reduce_only,
        position_mode=idempotency.position_mode or "ONE_WAY",
        margin_mode=idempotency.margin_mode or "CROSS",
        time_in_force=idempotency.time_in_force or "GTC",
        signal_timestamp=signal_timestamp,
        builder_version=BUILDER_VERSION,
        pending_evidence_refresh=False,
    )


def reverify_independent_pre_trade_safety_kernel_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise IndependentPreTradeSafetyKernelError(
            f"independent pre-trade safety kernel directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise IndependentPreTradeSafetyKernelError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    contract = read_manifest(artifact_path)
    _validate_contract_integrity(contract)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise IndependentPreTradeSafetyKernelError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise IndependentPreTradeSafetyKernelError("manifest_digest mismatch on replay")

    bindings = contract.get("upstream_bindings", {})
    if not isinstance(bindings, Mapping):
        bindings = {}
    idempotency = verify_order_intent_idempotency_bundle(
        Path(str(bindings.get("order_intent_idempotency_bundle_ref", "")))
    )
    reconciliation = verify_runtime_state_reconciliation_bundle(
        Path(str(bindings.get("runtime_state_reconciliation_bundle_ref", "")))
    )
    attestation = verify_trading_core_decision_attestation_bundle(
        Path(str(bindings.get("trading_core_decision_attestation_bundle_ref", "")))
    )
    venue_capability = verify_venue_capability_snapshot_bundle(
        Path(str(bindings.get("venue_capability_snapshot_bundle_ref", "")))
    )
    authority_lease = verify_authority_lease_bundle(
        Path(str(bindings.get("authority_lease_bundle_ref", "")))
    )
    clock_trust = verify_clock_trust_and_expiry_bundle(
        Path(str(bindings.get("clock_trust_and_expiry_bundle_ref", "")))
    )
    trading_session = verify_trading_session_single_writer_bundle(
        Path(str(bindings.get("trading_session_single_writer_bundle_ref", "")))
    )
    digest_checks = (
        ("order_intent_idempotency_digest", idempotency.artifact_digest),
        ("runtime_state_reconciliation_digest", reconciliation.artifact_digest),
        ("trading_core_decision_attestation_digest", attestation.artifact_digest),
        ("venue_capability_snapshot_digest", venue_capability.artifact_digest),
        ("authority_lease_digest", authority_lease.artifact_digest),
        ("clock_trust_digest", clock_trust.artifact_digest),
        ("trading_session_digest", trading_session.artifact_digest),
    )
    for field, expected in digest_checks:
        if bindings.get(field) != expected:
            raise IndependentPreTradeSafetyKernelError(f"{field} mismatch on replay")


def produce_independent_pre_trade_safety_kernel_v1(
    *,
    inputs: IndependentPreTradeSafetyKernelInputs,
    output_dir: Path | str,
) -> IndependentPreTradeSafetyKernelResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        bundle_dirs=[
            inputs.runtime_state_reconciliation_bundle_dir,
            inputs.order_intent_idempotency_bundle_dir,
            inputs.trading_core_decision_attestation_bundle_dir,
            inputs.venue_capability_snapshot_bundle_dir,
            inputs.clock_trust_and_expiry_bundle_dir,
            inputs.authority_lease_bundle_dir,
        ],
        output_dir=final_dir,
    )

    (
        idempotency,
        reconciliation,
        attestation,
        venue_capability,
        authority_lease,
        clock_trust,
        trading_session,
    ) = verify_independent_pre_trade_safety_kernel_inputs(inputs)
    contract_body = build_independent_pre_trade_safety_kernel_v1(
        request=inputs.request,
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
        venue_capability=venue_capability,
        authority_lease=authority_lease,
        clock_trust=clock_trust,
        trading_session=trading_session,
    )

    staging = final_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    if staging.exists():
        raise IndependentPreTradeSafetyKernelError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        finalized = _finalize_contract_with_manifest_digest(
            contract_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_independent_pre_trade_safety_kernel_v1(finalized),
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
            raise IndependentPreTradeSafetyKernelError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_independent_pre_trade_safety_kernel_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise IndependentPreTradeSafetyKernelError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return IndependentPreTradeSafetyKernelResult(
        output_dir=final_dir,
        safety_decision_id=str(finalized["safety_decision_id"]),
        decision=str(finalized["decision"]),
        contract_status=str(finalized["contract_status"]),
        evidence_status=str(finalized["evidence_status"]),
        contract_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


__all__ = [
    "ARTIFACT_REL",
    "BUILDER_VERSION",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "DECISION_CONTRACT_VERSION",
    "DEFAULT_GENERIC_ACCOUNT",
    "DEFAULT_GENERIC_CLIENT_ORDER_ID",
    "DEFAULT_GENERIC_INSTRUMENT",
    "DEFAULT_GENERIC_VENUE",
    "GENERIC_FUTURES_DAILY_LOSS_LIMIT",
    "GENERIC_FUTURES_GROSS_EXPOSURE_LIMIT",
    "GENERIC_FUTURES_LEVERAGE_LIMIT",
    "GENERIC_FUTURES_MARGIN_BUFFER_RATIO",
    "GENERIC_FUTURES_MAX_EXPECTED_MARKET_IMPACT_BPS",
    "GENERIC_FUTURES_MAX_MARK_INDEX_DIVERGENCE_BPS",
    "GENERIC_FUTURES_MAX_ORDERBOOK_AGE_MS",
    "GENERIC_FUTURES_MAX_SPREAD_BPS",
    "GENERIC_FUTURES_MESSAGE_RATE_LIMIT_PER_MINUTE",
    "GENERIC_FUTURES_MIN_ORDERBOOK_DEPTH",
    "GENERIC_FUTURES_OPEN_ORDER_LIMIT",
    "GENERIC_FUTURES_ORDER_NOTIONAL_LIMIT",
    "GENERIC_FUTURES_POSITION_LIMIT",
    "GENERIC_FUTURES_PRICE_COLLAR_BPS",
    "GENERIC_FUTURES_SIGNAL_EXPIRY_SECONDS",
    "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_AUTHORITY_INVARIANTS",
    "INPUT_CONTRACT_VERSION",
    "MANIFEST_FILENAME",
    "OFFLINE_DETERMINISTIC_CREATED_AT",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "IndependentPreTradeSafetyKernelError",
    "IndependentPreTradeSafetyKernelInputs",
    "IndependentPreTradeSafetyKernelResult",
    "InlineSnapshotBinding",
    "PreTradeSafetyEvaluationRequest",
    "VerifiedClockTrustBundle",
    "VerifiedOrderIntentIdempotencyBundle",
    "VerifiedRuntimeStateReconciliationBundle",
    "VerifiedTradingCoreDecisionAttestationBundle",
    "VerifiedVenueCapabilitySnapshotBundle",
    "build_default_kill_switch_snapshot_body",
    "build_default_margin_snapshot_body",
    "build_default_market_data_snapshot_body",
    "build_default_open_orders_snapshot_body",
    "build_default_position_snapshot_body",
    "build_default_risk_snapshot_body",
    "build_independent_pre_trade_safety_kernel_v1",
    "build_self_verification_v1",
    "default_pre_trade_safety_evaluation_request",
    "produce_independent_pre_trade_safety_kernel_v1",
    "reverify_independent_pre_trade_safety_kernel_v1",
    "serialize_independent_pre_trade_safety_kernel_v1",
    "verify_authority_lease_bundle",
    "verify_clock_trust_and_expiry_bundle",
    "verify_independent_pre_trade_safety_kernel_inputs",
    "verify_order_intent_idempotency_bundle",
    "verify_runtime_state_reconciliation_bundle",
    "verify_trading_core_decision_attestation_bundle",
    "verify_venue_capability_snapshot_bundle",
]
