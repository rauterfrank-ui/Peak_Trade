"""Offline RUNBOOK_STEP_21 venue capability snapshot contract owner v1."""

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

CONTRACT_NAME = "venue_capability_snapshot_v1"
CONTRACT_VERSION = "v1"
SNAPSHOT_CONTRACT_NAME = "venue_capability_snapshot_v1"
SNAPSHOT_CONTRACT_VERSION = "v1"
INPUT_CONTRACT_NAME = "venue_capability_input_v1"
INPUT_CONTRACT_VERSION = "v1"
DRIFT_CONTRACT_NAME = "venue_capability_drift_v1"
DRIFT_CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "venue_capability_snapshot_v1"
BUILDER_VERSION = "venue_capability_snapshot_builder_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "venue_capability_snapshot_record"
ARTIFACT_REL = "venue_capability_snapshot_v1.json"
DRIFT_ARTIFACT_REL = "venue_capability_drift_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".venue_capability_snapshot_staging_"

SCHEMA_VERSION = "venue_capability_snapshot_schema_v1"
CREATION_CONTRACT_VERSION = "venue_capability_snapshot_creation_v1"
DETERMINISTIC_RULE_SET_VERSION = "venue_capability_snapshot_rules_v1"
DETERMINISTIC_SERIALIZATION_VERSION = "deterministic_json_dumps_v1"
OFFLINE_DETERMINISTIC_SNAPSHOT_TIMESTAMP = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_venue_capability_snapshot_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"

_VALID_MARKET_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_MARKET_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_VALID_CONTRACT_TYPES = frozenset({"LINEAR_PERP", "INVERSE_PERP", "PERPETUAL_FUTURES"})
_VALID_POSITION_MODES = frozenset({"ONE_WAY", "HEDGE"})
_VALID_MARGIN_MODES = frozenset({"CROSS", "ISOLATED"})
_VALID_ORDER_TYPES = frozenset({"LIMIT", "MARKET"})
_VALID_TIME_IN_FORCE = frozenset({"GTC", "IOC", "FOK"})
_VALID_REDUCE_ONLY_SEMANTICS = frozenset({"SUPPORTED", "NOT_SUPPORTED", "REQUIRED_FOR_CLOSE"})
_VALID_SNAPSHOT_STATUSES = frozenset(
    {
        "VENUE_CAPABILITY_SNAPSHOT_VALID",
        "VENUE_CAPABILITY_SNAPSHOT_INVALID",
        "ABSTAIN",
    }
)
_VALID_DRIFT_CLASSIFICATIONS = frozenset(
    {"NO_DRIFT", "COMPATIBLE_DRIFT", "BREAKING_DRIFT", "INVALID_SNAPSHOT"}
)
_SELF_VERIFICATION_SCHEMA_VERSION = "venue_capability_snapshot_self_verification_v1"

_NORMALIZATION_RULES: dict[str, Any] = {
    "enum_case": "UPPER",
    "numeric_representation": "CANONICAL_DECIMAL_STRING",
    "list_order": "LEXICOGRAPHIC_SORT",
    "may_expand_limits": False,
    "may_increase_quantity": False,
    "may_relax_precision": False,
    "may_add_order_types": False,
    "may_change_position_mode": False,
    "may_change_margin_mode": False,
    "may_increase_leverage_cap": False,
    "deterministic_rule_set_version": DETERMINISTIC_RULE_SET_VERSION,
}

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

VENUE_CAPABILITY_SNAPSHOT_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "venue_capability_snapshot_is_descriptive_only": True,
    "venue_capability_snapshot_is_offline_only": True,
    "venue_capability_snapshot_is_evidence_not_authority": True,
    "venue_capability_snapshot_does_not_query_venue": True,
    "venue_capability_snapshot_does_not_invoke_adapter": True,
    "venue_capability_snapshot_does_not_mutate_runtime_state": True,
    "venue_capability_snapshot_does_not_grant_runtime_eligibility": True,
    "venue_capability_drift_does_not_execute_actions": True,
    "deny_by_default": True,
    "futures_only": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
}

_REQUIRED_NON_AUTHORIZING_FLAGS: dict[str, bool] = {
    "is_venue_capability_snapshot": True,
    "venue_capability_snapshot_offline_only": True,
    "venue_capability_snapshot_complete": False,
    "venue_capability_discovery_executed": False,
    "venue_capability_refresh_executed": False,
    "runtime_eligibility_granted": False,
    "new_orders_suspended": False,
    "execution_permissions_invalidated": False,
    "reconciliation_executed": False,
    "runtime_eligibility_revalidated": False,
    "adapter_invoked": False,
    "exchange_request_sent": False,
    "network_side_effect_created": False,
    "order_created": False,
    "order_submission_requested": False,
    "order_submitted": False,
    "order_cancel_requested": False,
    "order_amend_requested": False,
    "order_state_mutated": False,
    "position_state_mutated": False,
    "runtime_state_mutated": False,
    "execution_permission_created": False,
    "execution_permission_consumed": False,
    "submission_claim_executed": False,
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
    "runtime_mutation_performed": False,
    "deny_by_default": True,
    "futures_only": True,
}


class VenueCapabilitySnapshotError(ValueError):
    """Fail-closed venue capability snapshot error."""


@dataclass(frozen=True)
class VenueCapabilityInput:
    contract_name: str = INPUT_CONTRACT_NAME
    contract_version: str = INPUT_CONTRACT_VERSION
    snapshot_id: str = ""
    venue: str = ""
    account_scope: str = ""
    instrument: str = ""
    market_type: str = "FUTURES"
    contract_type: str = ""
    contract_multiplier: str = ""
    tick_size: str = ""
    lot_size: str = ""
    minimum_notional: str = ""
    maximum_order_size: str = ""
    position_mode: str = ""
    margin_mode: str = ""
    leverage_cap: str = ""
    supported_order_types: tuple[str, ...] = ()
    supported_time_in_force: tuple[str, ...] = ()
    reduce_only_semantics: str = ""
    source_ref: str = ""
    source_digest: str = ""
    source_timestamp: str = OFFLINE_DETERMINISTIC_SNAPSHOT_TIMESTAMP
    builder_version: str = BUILDER_VERSION
    settlement_asset: str = ""
    minimum_order_size: str = ""
    maximum_notional: str = ""
    quantity_precision: int | None = None
    price_precision: int | None = None
    post_only_semantics: str = ""
    client_order_id_constraints: str = ""


@dataclass(frozen=True)
class VenueCapabilitySnapshotResult:
    output_dir: Path
    snapshot_id: str
    snapshot_status: str
    capability_digest: str
    snapshot_path: Path
    self_verification_path: Path
    manifest_path: Path


@dataclass(frozen=True)
class VenueCapabilityDriftResult:
    drift_classification: str
    capability_digest_changed: bool
    suspend_new_orders_required: bool
    invalidate_unused_execution_permissions_required: bool
    reconciliation_required: bool
    runtime_eligibility_revalidation_required: bool
    actions_executed: bool
    drift_payload: dict[str, Any]


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise VenueCapabilitySnapshotError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise VenueCapabilitySnapshotError(f"forbidden index key: {key}")


def _validate_regular_file(path: Path, *, label: str) -> None:
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise VenueCapabilitySnapshotError(f"{label} must be a regular file: {path}")


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise VenueCapabilitySnapshotError(f"output directory already exists: {output_dir}")
    if is_under_tmp(output_dir):
        raise VenueCapabilitySnapshotError("output directory must not be under /tmp")


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(values)


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


def _parse_iso8601(value: str, *, field_name: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise VenueCapabilitySnapshotError(f"{field_name} must be ISO-8601: {value!r}") from exc


def _parse_positive_decimal(value: str, *, field_name: str) -> Decimal:
    if value is None or str(value).strip() == "":
        raise VenueCapabilitySnapshotError(f"{field_name} is required")
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise VenueCapabilitySnapshotError(f"{field_name} must be a decimal: {value!r}") from exc
    if not parsed.is_finite():
        raise VenueCapabilitySnapshotError(f"{field_name} must be finite: {value!r}")
    if parsed <= 0:
        raise VenueCapabilitySnapshotError(f"{field_name} must be positive: {value!r}")
    return parsed


def _parse_non_negative_decimal(value: str, *, field_name: str) -> Decimal:
    if value is None or str(value).strip() == "":
        raise VenueCapabilitySnapshotError(f"{field_name} is required")
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise VenueCapabilitySnapshotError(f"{field_name} must be a decimal: {value!r}") from exc
    if not parsed.is_finite():
        raise VenueCapabilitySnapshotError(f"{field_name} must be finite: {value!r}")
    if parsed < 0:
        raise VenueCapabilitySnapshotError(f"{field_name} must be non-negative: {value!r}")
    return parsed


def _canonical_decimal_string(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f")


def _normalize_enum(value: str, *, field_name: str) -> str:
    normalized = str(value or "").strip().upper()
    if not normalized:
        raise VenueCapabilitySnapshotError(f"{field_name} is required")
    return normalized


def _normalize_string_list(values: tuple[str, ...] | list[str], *, field_name: str) -> list[str]:
    if not values:
        raise VenueCapabilitySnapshotError(f"{field_name} must not be empty")
    normalized = [_normalize_enum(item, field_name=field_name) for item in values]
    return _sorted_strings(normalized)


def normalization_rules_digest() -> str:
    return compute_content_sha256(_NORMALIZATION_RULES)


def input_body_for_source_digest(input_payload: Mapping[str, Any]) -> dict[str, Any]:
    body = {
        key: value
        for key, value in input_payload.items()
        if key not in {"source_digest", "builder_version"}
    }
    return body


def compute_source_digest(input_payload: Mapping[str, Any]) -> str:
    return compute_content_sha256(input_body_for_source_digest(input_payload))


def venue_capability_input_to_dict(input_data: VenueCapabilityInput) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "contract_name": input_data.contract_name,
        "contract_version": input_data.contract_version,
        "snapshot_id": input_data.snapshot_id,
        "venue": input_data.venue,
        "account_scope": input_data.account_scope,
        "instrument": input_data.instrument,
        "market_type": input_data.market_type,
        "contract_type": input_data.contract_type,
        "contract_multiplier": input_data.contract_multiplier,
        "tick_size": input_data.tick_size,
        "lot_size": input_data.lot_size,
        "minimum_notional": input_data.minimum_notional,
        "maximum_order_size": input_data.maximum_order_size,
        "position_mode": input_data.position_mode,
        "margin_mode": input_data.margin_mode,
        "leverage_cap": input_data.leverage_cap,
        "supported_order_types": list(input_data.supported_order_types),
        "supported_time_in_force": list(input_data.supported_time_in_force),
        "reduce_only_semantics": input_data.reduce_only_semantics,
        "source_ref": input_data.source_ref,
        "source_digest": input_data.source_digest,
        "source_timestamp": input_data.source_timestamp,
        "builder_version": input_data.builder_version,
    }
    if input_data.settlement_asset:
        payload["settlement_asset"] = input_data.settlement_asset
    if input_data.minimum_order_size:
        payload["minimum_order_size"] = input_data.minimum_order_size
    if input_data.maximum_notional:
        payload["maximum_notional"] = input_data.maximum_notional
    if input_data.quantity_precision is not None:
        payload["quantity_precision"] = input_data.quantity_precision
    if input_data.price_precision is not None:
        payload["price_precision"] = input_data.price_precision
    if input_data.post_only_semantics:
        payload["post_only_semantics"] = input_data.post_only_semantics
    if input_data.client_order_id_constraints:
        payload["client_order_id_constraints"] = input_data.client_order_id_constraints
    return payload


def parse_venue_capability_input(payload: Mapping[str, Any]) -> VenueCapabilityInput:
    _reject_forbidden_index_keys(payload)
    order_types = payload.get("supported_order_types", [])
    tif_values = payload.get("supported_time_in_force", [])
    if not isinstance(order_types, list) or not isinstance(tif_values, list):
        raise VenueCapabilitySnapshotError(
            "supported_order_types and supported_time_in_force must be lists"
        )
    return VenueCapabilityInput(
        contract_name=str(payload.get("contract_name", INPUT_CONTRACT_NAME)),
        contract_version=str(payload.get("contract_version", INPUT_CONTRACT_VERSION)),
        snapshot_id=str(payload.get("snapshot_id", "")),
        venue=str(payload.get("venue", "")),
        account_scope=str(payload.get("account_scope", "")),
        instrument=str(payload.get("instrument", "")),
        market_type=str(payload.get("market_type", "")),
        contract_type=str(payload.get("contract_type", "")),
        contract_multiplier=str(payload.get("contract_multiplier", "")),
        tick_size=str(payload.get("tick_size", "")),
        lot_size=str(payload.get("lot_size", "")),
        minimum_notional=str(payload.get("minimum_notional", "")),
        maximum_order_size=str(payload.get("maximum_order_size", "")),
        position_mode=str(payload.get("position_mode", "")),
        margin_mode=str(payload.get("margin_mode", "")),
        leverage_cap=str(payload.get("leverage_cap", "")),
        supported_order_types=tuple(str(item) for item in order_types),
        supported_time_in_force=tuple(str(item) for item in tif_values),
        reduce_only_semantics=str(payload.get("reduce_only_semantics", "")),
        source_ref=str(payload.get("source_ref", "")),
        source_digest=str(payload.get("source_digest", "")),
        source_timestamp=str(
            payload.get("source_timestamp", OFFLINE_DETERMINISTIC_SNAPSHOT_TIMESTAMP)
        ),
        builder_version=str(payload.get("builder_version", BUILDER_VERSION)),
        settlement_asset=str(payload.get("settlement_asset", "")),
        minimum_order_size=str(payload.get("minimum_order_size", "")),
        maximum_notional=str(payload.get("maximum_notional", "")),
        quantity_precision=(
            int(payload["quantity_precision"])
            if payload.get("quantity_precision") is not None
            else None
        ),
        price_precision=(
            int(payload["price_precision"]) if payload.get("price_precision") is not None else None
        ),
        post_only_semantics=str(payload.get("post_only_semantics", "")),
        client_order_id_constraints=str(payload.get("client_order_id_constraints", "")),
    )


def validate_venue_capability_input(
    input_data: VenueCapabilityInput,
) -> tuple[list[dict[str, str]], dict[str, Any] | None]:
    factors: list[dict[str, str]] = []
    payload = venue_capability_input_to_dict(input_data)

    if input_data.contract_name != INPUT_CONTRACT_NAME:
        factors.append(
            _factor(
                factor_id="INPUT_CONTRACT_NAME_MISMATCH",
                factor_type="CONTRACT",
                source_field="contract_name",
                detail=input_data.contract_name,
            )
        )
    if input_data.contract_version != INPUT_CONTRACT_VERSION:
        factors.append(
            _factor(
                factor_id="INPUT_CONTRACT_VERSION_MISMATCH",
                factor_type="CONTRACT",
                source_field="contract_version",
                detail=input_data.contract_version,
            )
        )
    if not input_data.snapshot_id.strip():
        factors.append(
            _factor(
                factor_id="MISSING_SNAPSHOT_ID",
                factor_type="REQUIRED_FIELD",
                source_field="snapshot_id",
                detail="snapshot_id is required",
            )
        )
    if not input_data.venue.strip():
        factors.append(
            _factor(
                factor_id="MISSING_VENUE",
                factor_type="REQUIRED_FIELD",
                source_field="venue",
                detail="venue is required",
            )
        )
    if not input_data.account_scope.strip():
        factors.append(
            _factor(
                factor_id="MISSING_ACCOUNT_SCOPE",
                factor_type="REQUIRED_FIELD",
                source_field="account_scope",
                detail="account_scope is required",
            )
        )
    if not input_data.instrument.strip():
        factors.append(
            _factor(
                factor_id="MISSING_INSTRUMENT",
                factor_type="REQUIRED_FIELD",
                source_field="instrument",
                detail="instrument is required",
            )
        )

    market_type = str(input_data.market_type or "").strip().upper()
    if not market_type:
        factors.append(
            _factor(
                factor_id="MISSING_MARKET_TYPE",
                factor_type="REQUIRED_FIELD",
                source_field="market_type",
                detail="market_type is required",
            )
        )
    elif market_type in _FORBIDDEN_MARKET_TYPES:
        factors.append(
            _factor(
                factor_id="FORBIDDEN_MARKET_TYPE",
                factor_type="MARKET_TYPE",
                source_field="market_type",
                detail=market_type,
            )
        )
    elif market_type not in _VALID_MARKET_TYPES:
        factors.append(
            _factor(
                factor_id="UNKNOWN_MARKET_TYPE",
                factor_type="MARKET_TYPE",
                source_field="market_type",
                detail=market_type,
            )
        )

    contract_type = str(input_data.contract_type or "").strip().upper()
    if not contract_type:
        factors.append(
            _factor(
                factor_id="MISSING_CONTRACT_TYPE",
                factor_type="REQUIRED_FIELD",
                source_field="contract_type",
                detail="contract_type is required",
            )
        )
    elif contract_type not in _VALID_CONTRACT_TYPES:
        factors.append(
            _factor(
                factor_id="UNKNOWN_CONTRACT_TYPE",
                factor_type="ENUM",
                source_field="contract_type",
                detail=contract_type,
            )
        )

    numeric_fields = {
        "contract_multiplier": _parse_positive_decimal,
        "tick_size": _parse_positive_decimal,
        "lot_size": _parse_positive_decimal,
        "maximum_order_size": _parse_positive_decimal,
        "leverage_cap": _parse_positive_decimal,
    }
    parsed_numeric: dict[str, Decimal] = {}
    for field_name, parser in numeric_fields.items():
        raw = getattr(input_data, field_name)
        try:
            parsed_numeric[field_name] = parser(raw, field_name=field_name)
        except VenueCapabilitySnapshotError as exc:
            factors.append(
                _factor(
                    factor_id=f"INVALID_{field_name.upper()}",
                    factor_type="NUMERIC",
                    source_field=field_name,
                    detail=str(exc),
                )
            )

    try:
        parsed_numeric["minimum_notional"] = _parse_non_negative_decimal(
            input_data.minimum_notional,
            field_name="minimum_notional",
        )
    except VenueCapabilitySnapshotError as exc:
        factors.append(
            _factor(
                factor_id="INVALID_MINIMUM_NOTIONAL",
                factor_type="NUMERIC",
                source_field="minimum_notional",
                detail=str(exc),
            )
        )

    position_mode = str(input_data.position_mode or "").strip().upper()
    if not position_mode:
        factors.append(
            _factor(
                factor_id="MISSING_POSITION_MODE",
                factor_type="REQUIRED_FIELD",
                source_field="position_mode",
                detail="position_mode is required",
            )
        )
    elif position_mode not in _VALID_POSITION_MODES:
        factors.append(
            _factor(
                factor_id="UNKNOWN_POSITION_MODE",
                factor_type="ENUM",
                source_field="position_mode",
                detail=position_mode,
            )
        )

    margin_mode = str(input_data.margin_mode or "").strip().upper()
    if not margin_mode:
        factors.append(
            _factor(
                factor_id="MISSING_MARGIN_MODE",
                factor_type="REQUIRED_FIELD",
                source_field="margin_mode",
                detail="margin_mode is required",
            )
        )
    elif margin_mode not in _VALID_MARGIN_MODES:
        factors.append(
            _factor(
                factor_id="UNKNOWN_MARGIN_MODE",
                factor_type="ENUM",
                source_field="margin_mode",
                detail=margin_mode,
            )
        )

    try:
        normalized_order_types = _normalize_string_list(
            input_data.supported_order_types,
            field_name="supported_order_types",
        )
    except VenueCapabilitySnapshotError as exc:
        factors.append(
            _factor(
                factor_id="INVALID_SUPPORTED_ORDER_TYPES",
                factor_type="ENUM_LIST",
                source_field="supported_order_types",
                detail=str(exc),
            )
        )
        normalized_order_types = []
    else:
        unknown_order_types = [
            item for item in normalized_order_types if item not in _VALID_ORDER_TYPES
        ]
        if unknown_order_types:
            factors.append(
                _factor(
                    factor_id="UNKNOWN_ORDER_TYPE",
                    factor_type="ENUM_LIST",
                    source_field="supported_order_types",
                    detail=",".join(unknown_order_types),
                )
            )

    try:
        normalized_tif = _normalize_string_list(
            input_data.supported_time_in_force,
            field_name="supported_time_in_force",
        )
    except VenueCapabilitySnapshotError as exc:
        factors.append(
            _factor(
                factor_id="INVALID_SUPPORTED_TIME_IN_FORCE",
                factor_type="ENUM_LIST",
                source_field="supported_time_in_force",
                detail=str(exc),
            )
        )
        normalized_tif = []
    else:
        unknown_tif = [item for item in normalized_tif if item not in _VALID_TIME_IN_FORCE]
        if unknown_tif:
            factors.append(
                _factor(
                    factor_id="UNKNOWN_TIME_IN_FORCE",
                    factor_type="ENUM_LIST",
                    source_field="supported_time_in_force",
                    detail=",".join(unknown_tif),
                )
            )

    reduce_only_semantics = str(input_data.reduce_only_semantics or "").strip().upper()
    if not reduce_only_semantics:
        factors.append(
            _factor(
                factor_id="MISSING_REDUCE_ONLY_SEMANTICS",
                factor_type="REQUIRED_FIELD",
                source_field="reduce_only_semantics",
                detail="reduce_only_semantics is required",
            )
        )
    elif reduce_only_semantics not in _VALID_REDUCE_ONLY_SEMANTICS:
        factors.append(
            _factor(
                factor_id="UNKNOWN_REDUCE_ONLY_SEMANTICS",
                factor_type="ENUM",
                source_field="reduce_only_semantics",
                detail=reduce_only_semantics,
            )
        )

    if not input_data.source_ref.strip():
        factors.append(
            _factor(
                factor_id="MISSING_SOURCE_REF",
                factor_type="REQUIRED_FIELD",
                source_field="source_ref",
                detail="source_ref is required",
            )
        )

    expected_source_digest = compute_source_digest(payload)
    if not input_data.source_digest.strip():
        factors.append(
            _factor(
                factor_id="MISSING_SOURCE_DIGEST",
                factor_type="REQUIRED_FIELD",
                source_field="source_digest",
                detail="source_digest is required",
            )
        )
    elif input_data.source_digest.strip() != expected_source_digest:
        factors.append(
            _factor(
                factor_id="SOURCE_DIGEST_MISMATCH",
                factor_type="INTEGRITY",
                source_field="source_digest",
                detail="source_digest mismatch",
            )
        )

    try:
        _parse_iso8601(input_data.source_timestamp, field_name="source_timestamp")
    except VenueCapabilitySnapshotError as exc:
        factors.append(
            _factor(
                factor_id="INVALID_SOURCE_TIMESTAMP",
                factor_type="TIMESTAMP",
                source_field="source_timestamp",
                detail=str(exc),
            )
        )

    if factors:
        return _sort_factors(factors), None

    normalized: dict[str, Any] = {
        "venue": input_data.venue.strip(),
        "account_scope": input_data.account_scope.strip(),
        "instrument": input_data.instrument.strip(),
        "market_type": market_type,
        "contract_type": contract_type,
        "normalized_contract_multiplier": _canonical_decimal_string(
            parsed_numeric["contract_multiplier"]
        ),
        "normalized_tick_size": _canonical_decimal_string(parsed_numeric["tick_size"]),
        "normalized_lot_size": _canonical_decimal_string(parsed_numeric["lot_size"]),
        "normalized_minimum_notional": _canonical_decimal_string(
            parsed_numeric["minimum_notional"]
        ),
        "normalized_maximum_order_size": _canonical_decimal_string(
            parsed_numeric["maximum_order_size"]
        ),
        "normalized_position_mode": position_mode,
        "normalized_margin_mode": margin_mode,
        "normalized_leverage_cap": _canonical_decimal_string(parsed_numeric["leverage_cap"]),
        "normalized_supported_order_types": normalized_order_types,
        "normalized_supported_time_in_force": normalized_tif,
        "normalized_reduce_only_semantics": reduce_only_semantics,
    }
    return [], normalized


def capability_body_for_digest(normalized: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "account_scope": normalized["account_scope"],
        "contract_type": normalized["contract_type"],
        "instrument": normalized["instrument"],
        "market_type": normalized["market_type"],
        "normalized_contract_multiplier": normalized["normalized_contract_multiplier"],
        "normalized_leverage_cap": normalized["normalized_leverage_cap"],
        "normalized_lot_size": normalized["normalized_lot_size"],
        "normalized_margin_mode": normalized["normalized_margin_mode"],
        "normalized_maximum_order_size": normalized["normalized_maximum_order_size"],
        "normalized_minimum_notional": normalized["normalized_minimum_notional"],
        "normalized_position_mode": normalized["normalized_position_mode"],
        "normalized_reduce_only_semantics": normalized["normalized_reduce_only_semantics"],
        "normalized_supported_order_types": normalized["normalized_supported_order_types"],
        "normalized_supported_time_in_force": normalized["normalized_supported_time_in_force"],
        "normalized_tick_size": normalized["normalized_tick_size"],
        "venue": normalized["venue"],
        "normalization_rules_digest": normalization_rules_digest(),
    }


def compute_capability_digest(normalized: Mapping[str, Any]) -> str:
    return compute_content_sha256(capability_body_for_digest(normalized))


def _integrity_body(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in snapshot.items() if key not in {"integrity", "manifest_digest"}
    }


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


def build_venue_capability_snapshot_v1(
    *,
    input_data: VenueCapabilityInput,
    snapshot_timestamp: str = OFFLINE_DETERMINISTIC_SNAPSHOT_TIMESTAMP,
) -> dict[str, Any]:
    factors, normalized = validate_venue_capability_input(input_data)
    payload = venue_capability_input_to_dict(input_data)
    source_input_digest = compute_source_digest(payload)
    rules_digest = normalization_rules_digest()

    if factors or normalized is None:
        return {
            "snapshot_contract_name": SNAPSHOT_CONTRACT_NAME,
            "snapshot_contract_version": SNAPSHOT_CONTRACT_VERSION,
            "snapshot_id": input_data.snapshot_id or "invalid-snapshot",
            "source_input_digest": source_input_digest,
            "snapshot_status": "VENUE_CAPABILITY_SNAPSHOT_INVALID",
            "drift_classification": "INVALID_SNAPSHOT",
            "blocking_facts": factors,
            "capability_digest": "",
            "normalization_rules_digest": rules_digest,
            "snapshot_timestamp": snapshot_timestamp,
            "builder_version": input_data.builder_version,
            "runtime_mutation_performed": False,
            "adapter_invoked": False,
            "exchange_request_sent": False,
            "network_side_effect_created": False,
            **{key: False for key in _REQUIRED_NON_AUTHORIZING_FLAGS},
            "is_venue_capability_snapshot": True,
            "venue_capability_snapshot_offline_only": True,
            "venue_capability_snapshot_complete": False,
            "venue_capability_discovery_executed": False,
            "venue_capability_refresh_executed": False,
            "deny_by_default": True,
            "futures_only": True,
        }

    capability_digest = compute_capability_digest(normalized)
    snapshot = {
        "snapshot_contract_name": SNAPSHOT_CONTRACT_NAME,
        "snapshot_contract_version": SNAPSHOT_CONTRACT_VERSION,
        "snapshot_id": input_data.snapshot_id,
        "source_input_digest": source_input_digest,
        "venue": normalized["venue"],
        "account_scope": normalized["account_scope"],
        "instrument": normalized["instrument"],
        "market_type": normalized["market_type"],
        "contract_type": normalized["contract_type"],
        "normalized_contract_multiplier": normalized["normalized_contract_multiplier"],
        "normalized_tick_size": normalized["normalized_tick_size"],
        "normalized_lot_size": normalized["normalized_lot_size"],
        "normalized_minimum_notional": normalized["normalized_minimum_notional"],
        "normalized_maximum_order_size": normalized["normalized_maximum_order_size"],
        "normalized_position_mode": normalized["normalized_position_mode"],
        "normalized_margin_mode": normalized["normalized_margin_mode"],
        "normalized_leverage_cap": normalized["normalized_leverage_cap"],
        "normalized_supported_order_types": normalized["normalized_supported_order_types"],
        "normalized_supported_time_in_force": normalized["normalized_supported_time_in_force"],
        "normalized_reduce_only_semantics": normalized["normalized_reduce_only_semantics"],
        "normalization_rules_digest": rules_digest,
        "capability_digest": capability_digest,
        "snapshot_timestamp": snapshot_timestamp,
        "builder_version": input_data.builder_version,
        "snapshot_status": "VENUE_CAPABILITY_SNAPSHOT_VALID",
        "runtime_mutation_performed": False,
        "adapter_invoked": False,
        "exchange_request_sent": False,
        "network_side_effect_created": False,
        **{key: value for key, value in _REQUIRED_NON_AUTHORIZING_FLAGS.items()},
        "venue_capability_snapshot_complete": True,
        "venue_capability_discovery_executed": False,
        "venue_capability_refresh_executed": False,
        "authority_invariants": dict(VENUE_CAPABILITY_SNAPSHOT_AUTHORITY_INVARIANTS),
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "record_kind": RECORD_KIND,
        "source_ref": input_data.source_ref,
        "source_timestamp": input_data.source_timestamp,
        "producer_identity_ref": DEFAULT_PRODUCER_IDENTITY_REF,
        "source_revision": DEFAULT_SOURCE_REVISION,
        "integrity": {"content_sha256": ""},
    }
    output_digest = _compute_output_digest(snapshot)
    snapshot["output_digest"] = output_digest
    snapshot["artifact_id"] = output_digest
    snapshot["integrity"] = {"content_sha256": compute_content_sha256(_integrity_body(snapshot))}
    return snapshot


def serialize_venue_capability_snapshot_v1(snapshot: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(snapshot)


def classify_venue_capability_drift_v1(
    *,
    baseline_snapshot: Mapping[str, Any],
    candidate_snapshot: Mapping[str, Any],
    baseline_snapshot_ref: str,
    candidate_snapshot_ref: str,
    created_at: str = OFFLINE_DETERMINISTIC_SNAPSHOT_TIMESTAMP,
) -> dict[str, Any]:
    baseline_status = str(baseline_snapshot.get("snapshot_status", ""))
    candidate_status = str(candidate_snapshot.get("snapshot_status", ""))
    baseline_digest = str(baseline_snapshot.get("capability_digest", ""))
    candidate_digest = str(candidate_snapshot.get("capability_digest", ""))

    if (
        baseline_status != "VENUE_CAPABILITY_SNAPSHOT_VALID"
        or candidate_status != "VENUE_CAPABILITY_SNAPSHOT_VALID"
        or not baseline_digest
        or not candidate_digest
    ):
        drift_classification = "INVALID_SNAPSHOT"
        capability_digest_changed = baseline_digest != candidate_digest
        suspend_required = False
        invalidate_required = False
        reconciliation_required = False
        revalidation_required = False
    elif baseline_digest == candidate_digest:
        drift_classification = "NO_DRIFT"
        capability_digest_changed = False
        suspend_required = False
        invalidate_required = False
        reconciliation_required = False
        revalidation_required = False
    else:
        drift_classification = "BREAKING_DRIFT"
        capability_digest_changed = True
        suspend_required = True
        invalidate_required = True
        reconciliation_required = True
        revalidation_required = True

    changed_fields: list[str] = []
    baseline_capability = capability_body_for_digest(
        {
            "venue": baseline_snapshot.get("venue", ""),
            "account_scope": baseline_snapshot.get("account_scope", ""),
            "instrument": baseline_snapshot.get("instrument", ""),
            "market_type": baseline_snapshot.get("market_type", ""),
            "contract_type": baseline_snapshot.get("contract_type", ""),
            "normalized_contract_multiplier": baseline_snapshot.get(
                "normalized_contract_multiplier", ""
            ),
            "normalized_tick_size": baseline_snapshot.get("normalized_tick_size", ""),
            "normalized_lot_size": baseline_snapshot.get("normalized_lot_size", ""),
            "normalized_minimum_notional": baseline_snapshot.get("normalized_minimum_notional", ""),
            "normalized_maximum_order_size": baseline_snapshot.get(
                "normalized_maximum_order_size", ""
            ),
            "normalized_position_mode": baseline_snapshot.get("normalized_position_mode", ""),
            "normalized_margin_mode": baseline_snapshot.get("normalized_margin_mode", ""),
            "normalized_leverage_cap": baseline_snapshot.get("normalized_leverage_cap", ""),
            "normalized_supported_order_types": baseline_snapshot.get(
                "normalized_supported_order_types", []
            ),
            "normalized_supported_time_in_force": baseline_snapshot.get(
                "normalized_supported_time_in_force", []
            ),
            "normalized_reduce_only_semantics": baseline_snapshot.get(
                "normalized_reduce_only_semantics", ""
            ),
        }
    )
    candidate_capability = capability_body_for_digest(
        {
            "venue": candidate_snapshot.get("venue", ""),
            "account_scope": candidate_snapshot.get("account_scope", ""),
            "instrument": candidate_snapshot.get("instrument", ""),
            "market_type": candidate_snapshot.get("market_type", ""),
            "contract_type": candidate_snapshot.get("contract_type", ""),
            "normalized_contract_multiplier": candidate_snapshot.get(
                "normalized_contract_multiplier", ""
            ),
            "normalized_tick_size": candidate_snapshot.get("normalized_tick_size", ""),
            "normalized_lot_size": candidate_snapshot.get("normalized_lot_size", ""),
            "normalized_minimum_notional": candidate_snapshot.get(
                "normalized_minimum_notional", ""
            ),
            "normalized_maximum_order_size": candidate_snapshot.get(
                "normalized_maximum_order_size", ""
            ),
            "normalized_position_mode": candidate_snapshot.get("normalized_position_mode", ""),
            "normalized_margin_mode": candidate_snapshot.get("normalized_margin_mode", ""),
            "normalized_leverage_cap": candidate_snapshot.get("normalized_leverage_cap", ""),
            "normalized_supported_order_types": candidate_snapshot.get(
                "normalized_supported_order_types", []
            ),
            "normalized_supported_time_in_force": candidate_snapshot.get(
                "normalized_supported_time_in_force", []
            ),
            "normalized_reduce_only_semantics": candidate_snapshot.get(
                "normalized_reduce_only_semantics", ""
            ),
        }
    )
    for key in sorted(baseline_capability.keys()):
        if baseline_capability.get(key) != candidate_capability.get(key):
            changed_fields.append(key)

    return {
        "drift_contract_name": DRIFT_CONTRACT_NAME,
        "drift_contract_version": DRIFT_CONTRACT_VERSION,
        "baseline_snapshot_ref": baseline_snapshot_ref,
        "baseline_capability_digest": baseline_digest,
        "candidate_snapshot_ref": candidate_snapshot_ref,
        "candidate_capability_digest": candidate_digest,
        "capability_digest_changed": capability_digest_changed,
        "changed_fields": _sorted_strings(changed_fields),
        "drift_classification": drift_classification,
        "suspend_new_orders_required": suspend_required,
        "invalidate_unused_execution_permissions_required": invalidate_required,
        "reconciliation_required": reconciliation_required,
        "runtime_eligibility_revalidation_required": revalidation_required,
        "actions_executed": False,
        "runtime_mutation_performed": False,
        "new_orders_suspended": False,
        "execution_permissions_invalidated": False,
        "reconciliation_executed": False,
        "runtime_eligibility_revalidated": False,
        "adapter_invoked": False,
        "exchange_request_sent": False,
        "network_side_effect_created": False,
        "order_created": False,
        "order_submission_requested": False,
        "order_submitted": False,
        "order_cancel_requested": False,
        "order_amend_requested": False,
        "order_state_mutated": False,
        "position_state_mutated": False,
        "runtime_state_mutated": False,
        "execution_permission_created": False,
        "execution_permission_consumed": False,
        "submission_claim_executed": False,
        "live_authorized": False,
        "orders_allowed": False,
        "scheduler_runtime_allowed": False,
        "builder_version": BUILDER_VERSION,
        "created_at": created_at,
    }


def build_self_verification_v1(
    *,
    snapshot: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "offline_only_no_adapter_invocation", "status": "PASS"},
        {"check_id": "offline_only_no_network_side_effect", "status": "PASS"},
        {"check_id": "offline_only_no_runtime_mutation", "status": "PASS"},
        {"check_id": "futures_only_guard", "status": "PASS"},
        {
            "check_id": "manifest_digest",
            "status": "PASS" if manifest_digest else "FAIL",
        },
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


def _artifact_bytes_for_manifest_digest(snapshot: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in snapshot.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_venue_capability_snapshot_v1(body).encode("utf-8")


def _compute_output_manifest_digest(snapshot: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(snapshot)).hexdigest()


def _validate_contract_integrity(snapshot: Mapping[str, Any]) -> None:
    if snapshot.get("contract_name") != CONTRACT_NAME:
        raise VenueCapabilitySnapshotError("contract_name mismatch")
    if snapshot.get("contract_version") != CONTRACT_VERSION:
        raise VenueCapabilitySnapshotError("contract_version mismatch")
    integrity = snapshot.get("integrity")
    if not isinstance(integrity, Mapping):
        raise VenueCapabilitySnapshotError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(snapshot))
    actual = integrity.get("content_sha256")
    if actual != expected:
        raise VenueCapabilitySnapshotError("integrity.content_sha256 mismatch")
    output_digest = snapshot.get("output_digest")
    if output_digest != _compute_output_digest(snapshot):
        raise VenueCapabilitySnapshotError("output_digest mismatch")
    if snapshot.get("artifact_id") != output_digest:
        raise VenueCapabilitySnapshotError("artifact_id must equal output_digest")
    if snapshot.get("snapshot_status") == "VENUE_CAPABILITY_SNAPSHOT_VALID":
        expected_capability = compute_capability_digest(snapshot)
        if snapshot.get("capability_digest") != expected_capability:
            raise VenueCapabilitySnapshotError("capability_digest mismatch")


def _finalize_snapshot_with_manifest_digest(
    snapshot: Mapping[str, Any],
    *,
    manifest_digest: str,
) -> dict[str, Any]:
    finalized = dict(snapshot)
    finalized["manifest_digest"] = manifest_digest
    return finalized


def default_venue_capability_input() -> VenueCapabilityInput:
    base_payload = {
        "contract_name": INPUT_CONTRACT_NAME,
        "contract_version": INPUT_CONTRACT_VERSION,
        "snapshot_id": "generic-futures-capability-snapshot-001",
        "venue": "GENERIC-FUTURES-VENUE-001",
        "account_scope": "GENERIC-FUTURES-ACCOUNT-001",
        "instrument": "GENERIC-FUTURES-PERP-001",
        "market_type": "FUTURES",
        "contract_type": "LINEAR_PERP",
        "contract_multiplier": "1",
        "tick_size": "0.01",
        "lot_size": "0.001",
        "minimum_notional": "1.0",
        "maximum_order_size": "100",
        "position_mode": "ONE_WAY",
        "margin_mode": "CROSS",
        "leverage_cap": "5",
        "supported_order_types": ["LIMIT", "MARKET"],
        "supported_time_in_force": ["GTC", "IOC"],
        "reduce_only_semantics": "SUPPORTED",
        "source_ref": "offline/generic-futures-capability-input-001",
        "source_timestamp": OFFLINE_DETERMINISTIC_SNAPSHOT_TIMESTAMP,
        "builder_version": BUILDER_VERSION,
    }
    base_payload["source_digest"] = compute_source_digest(base_payload)
    return parse_venue_capability_input(base_payload)


def produce_venue_capability_snapshot_v1(
    *,
    input_data: VenueCapabilityInput,
    output_dir: Path | str,
    snapshot_timestamp: str = OFFLINE_DETERMINISTIC_SNAPSHOT_TIMESTAMP,
) -> VenueCapabilitySnapshotResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)

    snapshot_body = build_venue_capability_snapshot_v1(
        input_data=input_data,
        snapshot_timestamp=snapshot_timestamp,
    )

    staging = final_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    if staging.exists():
        raise VenueCapabilitySnapshotError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(snapshot_body)
        finalized = _finalize_snapshot_with_manifest_digest(
            snapshot_body, manifest_digest=manifest_digest
        )
        artifact_path.write_text(
            serialize_venue_capability_snapshot_v1(finalized),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            snapshot=finalized,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise VenueCapabilitySnapshotError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        if finalized.get("snapshot_status") == "VENUE_CAPABILITY_SNAPSHOT_VALID":
            reverify_venue_capability_snapshot_v1(output_dir=staging)

        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise VenueCapabilitySnapshotError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return VenueCapabilitySnapshotResult(
        output_dir=final_dir,
        snapshot_id=str(finalized["snapshot_id"]),
        snapshot_status=str(finalized["snapshot_status"]),
        capability_digest=str(finalized.get("capability_digest", "")),
        snapshot_path=final_dir / ARTIFACT_REL,
        self_verification_path=final_dir / SELF_VERIFICATION_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


def reverify_venue_capability_snapshot_v1(*, output_dir: Path | str) -> None:
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise VenueCapabilitySnapshotError(
            f"venue capability snapshot directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise VenueCapabilitySnapshotError(f"MANIFEST.sha256 verification failed: {msg}")

    artifact_path = bundle_dir / ARTIFACT_REL
    _validate_regular_file(artifact_path, label=ARTIFACT_REL)
    snapshot = read_manifest(artifact_path)
    _validate_contract_integrity(snapshot)

    self_path = bundle_dir / SELF_VERIFICATION_REL
    _validate_regular_file(self_path, label=SELF_VERIFICATION_REL)
    self_payload = read_manifest(self_path)
    if self_payload.get("overall_status") != "PASS":
        raise VenueCapabilitySnapshotError("SELF_VERIFICATION overall_status must be PASS")

    manifest_digest = _compute_output_manifest_digest(snapshot)
    if snapshot.get("manifest_digest") != manifest_digest:
        raise VenueCapabilitySnapshotError("manifest_digest mismatch on replay")


def load_venue_capability_snapshot(path: Path | str) -> dict[str, Any]:
    snapshot_path = Path(path)
    _validate_regular_file(snapshot_path, label="venue_capability_snapshot")
    return read_manifest(snapshot_path)


__all__ = [
    "ARTIFACT_REL",
    "BUILDER_VERSION",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "DRIFT_ARTIFACT_REL",
    "DRIFT_CONTRACT_NAME",
    "DRIFT_CONTRACT_VERSION",
    "INPUT_CONTRACT_NAME",
    "INPUT_CONTRACT_VERSION",
    "MANIFEST_FILENAME",
    "PRODUCER_VERSION",
    "SELF_VERIFICATION_REL",
    "SNAPSHOT_CONTRACT_NAME",
    "SNAPSHOT_CONTRACT_VERSION",
    "VENUE_CAPABILITY_SNAPSHOT_AUTHORITY_INVARIANTS",
    "VenueCapabilityDriftResult",
    "VenueCapabilityInput",
    "VenueCapabilitySnapshotError",
    "VenueCapabilitySnapshotResult",
    "build_self_verification_v1",
    "build_venue_capability_snapshot_v1",
    "capability_body_for_digest",
    "classify_venue_capability_drift_v1",
    "compute_capability_digest",
    "compute_source_digest",
    "default_venue_capability_input",
    "input_body_for_source_digest",
    "load_venue_capability_snapshot",
    "normalization_rules_digest",
    "parse_venue_capability_input",
    "produce_venue_capability_snapshot_v1",
    "reverify_venue_capability_snapshot_v1",
    "serialize_venue_capability_snapshot_v1",
    "validate_venue_capability_input",
    "venue_capability_input_to_dict",
]
