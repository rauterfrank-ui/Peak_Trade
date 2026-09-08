"""Versioned observation of DoublePlayEntryExitPolicyInputV0.

Observation-only. Does not import trading at module load (avoids a capture
circular import). Does not re-run evaluate_double_play_entry_exit_policy_v0.
Does not rewrite producer input_digest semantics.

TRADING_AUTHORITY=NONE
DDO_MAY_REWRITE_PRODUCER_SEMANTICS=false
RUNTIME_EFFECT=OBSERVATION_ONLY
HINDSIGHT_LEAKAGE_ALLOWED=false
"""

from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    FieldSpecV0,
    attach_content_hash,
    freeze_record,
    optional_record_id,
    reject_unknown_fields,
    require_enum,
    require_event_time_utc,
    require_id_list,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
    require_schema,
    require_sha256_or_unknown,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    canonical_json_dumps_v0,
    sha256_hex_v0,
)

SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE: Final[str] = (
    "double_play_entry_exit_policy_input_evidence"
)
SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1: Final[str] = (
    "double_play_entry_exit_policy_input_evidence_v1"
)
PROJECTION_ID: Final[str] = (
    "peak_trade.learning.ddo.double_play_entry_exit_policy_input_evidence_v1"
)
PRODUCER_OWNER: Final[str] = "trading.master_v2.double_play_entry_exit_policy_v0"
PRODUCER_FUNCTION_NAME: Final[str] = "evaluate_double_play_entry_exit_policy_v0"
PRODUCER_ID: Final[str] = "double_play_entry_exit_policy_v0"
TRADING_AUTHORITY_NONE: Final[str] = "NONE"
AUTHORITY_OWNER_NONE: Final[str] = "NONE"
RUNTIME_EFFECT_OBSERVATION_ONLY: Final[str] = "OBSERVATION_ONLY"
TYPED_PROJECTION_STATUS: Final[str] = "TYPED_PRODUCER_INPUT"
UNAVAILABLE_PROJECTION_STATUS: Final[str] = "UNAVAILABLE"
CAPTURE_TIMING_BEFORE_PRODUCER_CALL: Final[str] = "BEFORE_PRODUCER_CALL"
CAPTURE_TIMING_FROM_CALL_ARGS: Final[str] = "FROM_CALL_ARGS"
CAPTURE_TIMING_UNAVAILABLE: Final[str] = "UNAVAILABLE"
DIGEST_ALGORITHM_ID: Final[str] = "sha256"
PRODUCER_JSON_DIALECT: Final[str] = "json.dumps.sort_keys.separators_comma_colon"
DIGEST_RELATION_SUBSET_SCOPE: Final[str] = (
    "PRODUCER_INPUT_DIGEST_IS_REDUCED_CANONICAL_SCOPE_NOT_EQUAL_TO_DDO_EVIDENCE_HASH"
)

# Exact key set of serialize_entry_exit_policy_input_canonical.
PRODUCER_DIGEST_CANONICAL_KEYS: Final[tuple[str, ...]] = (
    "instrument_id",
    "trading_epoch",
    "context_reference",
    "composition_result_ref",
    "composition_semantic_digest",
    "direction_state",
    "position_state",
    "reconciliation_state",
    "trading_gate",
    "safety_mode",
    "data_integrity_state",
    "clock_trust_status",
    "clock_trust_valid",
    "cooldown_pass",
    "existing_position_side",
    "venue_flat",
    "scope_adverse_exit_signal",
    "profit_protection_signal",
    "time_exit_signal",
    "strategy_invalidation_signal",
    "hard_risk_reduction_signal",
    "safety_exit_signal",
    "input_complete",
    "explicit_blocked_reasons",
    "policy_version",
)

# Exact DoublePlayEntryExitPolicyInputV0 field names. No aliases.
PRODUCER_INPUT_FIELD_KEYS: Final[tuple[str, ...]] = (
    "instrument_id",
    "trading_epoch",
    "context_reference",
    "composition_result",
    "direction_state",
    "position_state",
    "reconciliation_state",
    "trading_gate",
    "safety_mode",
    "data_integrity_state",
    "clock_trust_status",
    "clock_trust_valid",
    "cooldown_pass",
    "existing_position_side",
    "venue_flat",
    "scope_adverse_exit_signal",
    "profit_protection_signal",
    "time_exit_signal",
    "strategy_invalidation_signal",
    "hard_risk_reduction_signal",
    "safety_exit_signal",
    "input_complete",
    "input_digest",
    "explicit_blocked_reasons",
    "policy_version",
)

SIGNAL_FIELD_KEYS: Final[tuple[str, ...]] = (
    "scope_adverse_exit_signal",
    "profit_protection_signal",
    "time_exit_signal",
    "strategy_invalidation_signal",
    "hard_risk_reduction_signal",
    "safety_exit_signal",
)

COMPOSITION_CANONICAL_KEYS: Final[tuple[str, ...]] = (
    "composition_id",
    "instrument_id",
    "trading_epoch",
    "context_reference",
    "bull_assessment_ref",
    "bear_assessment_ref",
    "bull_survival_ref",
    "bear_survival_ref",
    "bull_suitability_ref",
    "bear_suitability_ref",
    "previous_direction_state",
    "position_management_context",
    "composition_status",
    "selected_side",
    "conflict_status",
    "chop_guard_status",
    "reason_codes",
    "policy_version",
    "input_digest",
    "authority_effect",
    "runtime_effect",
    "order_effect",
    "risk_effect",
    "sizing_effect",
)

_HINDSIGHT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "later_price",
        "later_prices",
        "later_position",
        "later_positions",
        "fill",
        "fills",
        "pnl",
        "later_pnl",
        "outcome_record",
        "attribution",
        "counterfactual",
        "future_bar",
        "future_bars",
        "hindsight",
        "hindsight_label",
        "later_reconciliation",
    }
)
_SECRET_KEYS: Final[frozenset[str]] = frozenset(
    {
        "api_key",
        "api_keys",
        "secret",
        "secrets",
        "auth_header",
        "authorization",
        "bearer",
        "signature",
        "session_credential",
        "session_credentials",
        "confirm_token",
        "password",
        "private_key",
        "private_transport_handle",
    }
)

PROJECTION_STATUS_V1: Final[tuple[str, ...]] = (
    TYPED_PROJECTION_STATUS,
    UNAVAILABLE_PROJECTION_STATUS,
)
TRADING_AUTHORITY_V1: Final[tuple[str, ...]] = (TRADING_AUTHORITY_NONE,)
AUTHORITY_OWNER_V1: Final[tuple[str, ...]] = (AUTHORITY_OWNER_NONE,)
RUNTIME_EFFECT_V1: Final[tuple[str, ...]] = (RUNTIME_EFFECT_OBSERVATION_ONLY,)
CAPTURE_TIMING_V1: Final[tuple[str, ...]] = (
    CAPTURE_TIMING_BEFORE_PRODUCER_CALL,
    CAPTURE_TIMING_FROM_CALL_ARGS,
    CAPTURE_TIMING_UNAVAILABLE,
    UNKNOWN,
)

DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_FIELD_SPECS_V1: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("schema_name", "REQUIRED", "string", True, "Input evidence schema identity."),
    FieldSpecV0(
        "schema_version",
        "REQUIRED",
        "string",
        True,
        "Version token double_play_entry_exit_policy_input_evidence_v1.",
    ),
    FieldSpecV0("record_id", "REQUIRED", "record_id", True, "Immutable evidence identity."),
    FieldSpecV0("event_time_utc", "REQUIRED", "utc_timestamp", True, "Capture event time UTC."),
    FieldSpecV0("correlation_id", "REQUIRED", "record_id", True, "Correlation identity."),
    FieldSpecV0(
        "cycle_id",
        "CONDITIONALLY_REQUIRED",
        "record_id|null",
        True,
        "Null until a proven cycle producer exists.",
    ),
    FieldSpecV0(
        "decision_event_ref",
        "REQUIRED",
        "record_id",
        True,
        "Lineage to the generic DecisionEvent. Not trading authority.",
    ),
    FieldSpecV0(
        "typed_output_observation_ref",
        "CONDITIONALLY_REQUIRED",
        "record_id|null",
        True,
        "Lineage to the sibling typed output observation, or null if unavailable.",
    ),
    FieldSpecV0("projection_id", "REQUIRED", "string", True, "Versioned projection identity."),
    FieldSpecV0(
        "projection_status",
        "REQUIRED",
        "enum:PROJECTION_STATUS_V1",
        True,
        "TYPED_PRODUCER_INPUT or UNAVAILABLE.",
    ),
    FieldSpecV0(
        "trading_authority",
        "REQUIRED",
        "enum:TRADING_AUTHORITY_V1",
        True,
        "Always NONE. DDO does not own trading semantics.",
    ),
    FieldSpecV0(
        "authority_owner",
        "REQUIRED",
        "enum:AUTHORITY_OWNER_V1",
        True,
        "Always NONE.",
    ),
    FieldSpecV0(
        "runtime_effect",
        "REQUIRED",
        "enum:RUNTIME_EFFECT_V1",
        True,
        "Always OBSERVATION_ONLY.",
    ),
    FieldSpecV0("producer_owner", "REQUIRED", "string", True, "Producer-declared owner label."),
    FieldSpecV0("producer_id", "REQUIRED", "string", True, "Producer identity. Not authority."),
    FieldSpecV0(
        "producer_version",
        "REQUIRED",
        "string",
        True,
        "Exact inp.policy_version or UNAVAILABLE.",
    ),
    FieldSpecV0(
        "producer_function_name",
        "REQUIRED",
        "string",
        True,
        "evaluate_double_play_entry_exit_policy_v0.",
    ),
    FieldSpecV0(
        "producer_call_policy_version",
        "REQUIRED",
        "string",
        True,
        "Second-argument policy.policy_version or UNAVAILABLE. Not a second policy.",
    ),
    FieldSpecV0(
        "capture_timing",
        "REQUIRED",
        "enum:CAPTURE_TIMING_V1",
        True,
        "When the decision-time input snapshot was taken.",
    ),
    FieldSpecV0(
        "producer_digest_canonical_payload",
        "CONDITIONALLY_REQUIRED",
        "object|null",
        True,
        "Exact serialize_entry_exit_policy_input_canonical object, or null.",
    ),
    FieldSpecV0(
        "producer_input_digest",
        "CONDITIONALLY_REQUIRED",
        "sha256|UNKNOWN|null",
        True,
        "Existing producer input_digest. Null when typed input is unavailable.",
    ),
    FieldSpecV0(
        "producer_input_digest_algorithm",
        "REQUIRED",
        "string",
        True,
        "sha256 over producer JSON dialect.",
    ),
    FieldSpecV0(
        "digest_relation",
        "REQUIRED",
        "string",
        True,
        "Explicit relation between producer digest and DDO evidence hash.",
    ),
    FieldSpecV0(
        "producer_input_fields",
        "CONDITIONALLY_REQUIRED",
        "object|null",
        True,
        "Exact typed input fields required for later reconstruction, or null.",
    ),
    FieldSpecV0(
        "input_evidence_payload_hash",
        "CONDITIONALLY_REQUIRED",
        "sha256|null",
        True,
        "Hash of producer_input_fields only. Null when typed input is unavailable.",
    ),
    FieldSpecV0("code_sha", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN is explicit semantics."),
    FieldSpecV0(
        "evidence_hash", "REQUIRED", "sha256|UNKNOWN", True, "UNKNOWN is explicit semantics."
    ),
    FieldSpecV0(
        "causal_parent_ids", "REQUIRED", "record_id[]", True, "DecisionEvent is the parent."
    ),
    FieldSpecV0("content_hash", "REQUIRED", "sha256", False, "Computed; excluded from hash scope."),
)

DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_FIELD_SPECS_V1
)

_REQUIRED_TYPED_INPUT_ATTRS: Final[tuple[str, ...]] = PRODUCER_INPUT_FIELD_KEYS


def is_typed_entry_exit_policy_input_v1(obj: Any) -> bool:
    """True when obj is the current typed producer input (class or duck-typed)."""
    if obj is None or isinstance(obj, Mapping):
        return False
    typed_cls = _entry_exit_input_class()
    if typed_cls is not None and isinstance(obj, typed_cls):
        return True
    return all(hasattr(obj, key) for key in _REQUIRED_TYPED_INPUT_ATTRS)


def extract_double_play_producer_call_args_v1(
    args: tuple[Any, ...] | None,
    kwargs: Mapping[str, Any] | None,
) -> tuple[Any, Any]:
    """Return (inp, policy) from the producer call without mutating arguments."""
    inp = None
    policy = None
    if kwargs:
        if "inp" in kwargs:
            inp = kwargs["inp"]
        if "policy" in kwargs:
            policy = kwargs["policy"]
    if args:
        if inp is None and len(args) >= 1:
            inp = args[0]
        if policy is None and len(args) >= 2:
            policy = args[1]
    return inp, policy


def snapshot_double_play_producer_input_fields_v1(inp: Any) -> dict[str, Any]:
    """Decision-time typed input fields. Does not mutate inp."""
    if not is_typed_entry_exit_policy_input_v1(inp):
        raise DdoValidationError("DOUBLE_PLAY_INPUT_EVIDENCE_REQUIRES_TYPED_INPUT")
    _reject_hindsight_and_secrets_object(inp)
    composition = getattr(inp, "composition_result")
    composition_payload = _composition_fields_from_result(composition)
    fields: dict[str, Any] = {
        "instrument_id": _token(inp.instrument_id),
        "trading_epoch": _require_int(inp.trading_epoch, "trading_epoch"),
        "context_reference": _token(inp.context_reference),
        "composition_result": composition_payload,
        "direction_state": _token(inp.direction_state),
        "position_state": _token(inp.position_state),
        "reconciliation_state": _token(inp.reconciliation_state),
        "trading_gate": _token(inp.trading_gate),
        "safety_mode": _token(inp.safety_mode),
        "data_integrity_state": _token(inp.data_integrity_state),
        "clock_trust_status": _token(inp.clock_trust_status),
        "clock_trust_valid": _require_bool(inp.clock_trust_valid, "clock_trust_valid"),
        "cooldown_pass": _require_bool(inp.cooldown_pass, "cooldown_pass"),
        "existing_position_side": _token(inp.existing_position_side),
        "venue_flat": _require_bool(inp.venue_flat, "venue_flat"),
        "scope_adverse_exit_signal": _signal_fields(inp.scope_adverse_exit_signal),
        "profit_protection_signal": _signal_fields(inp.profit_protection_signal),
        "time_exit_signal": _signal_fields(inp.time_exit_signal),
        "strategy_invalidation_signal": _signal_fields(inp.strategy_invalidation_signal),
        "hard_risk_reduction_signal": _signal_fields(inp.hard_risk_reduction_signal),
        "safety_exit_signal": _signal_fields(inp.safety_exit_signal),
        "input_complete": _require_bool(inp.input_complete, "input_complete"),
        "input_digest": _digest_or_empty(inp.input_digest),
        "explicit_blocked_reasons": [_token(item) for item in inp.explicit_blocked_reasons],
        "policy_version": _token(inp.policy_version),
    }
    missing = [key for key in PRODUCER_INPUT_FIELD_KEYS if key not in fields]
    if missing:
        raise DdoValidationError(f"PRODUCER_INPUT_FIELDS_MISSING:{missing}")
    extra = sorted(set(fields.keys()) - set(PRODUCER_INPUT_FIELD_KEYS))
    if extra:
        raise DdoValidationError(f"PRODUCER_INPUT_FIELDS_UNEXPECTED:{extra}")
    _reject_hindsight_and_secrets_mapping(fields)
    return fields


def producer_digest_canonical_payload_from_input_v1(inp: Any) -> dict[str, Any]:
    """Exact producer digest-scope payload. Prefers the producer serializer."""
    if not is_typed_entry_exit_policy_input_v1(inp):
        raise DdoValidationError("DOUBLE_PLAY_INPUT_EVIDENCE_REQUIRES_TYPED_INPUT")
    serializer = _canonical_input_serializer()
    if serializer is not None:
        raw = serializer(inp)
        if not isinstance(raw, str):
            raise DdoValidationError("PRODUCER_INPUT_SERIALIZER_MUST_RETURN_STRING")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise DdoValidationError("PRODUCER_DIGEST_CANONICAL_PAYLOAD_MUST_BE_OBJECT")
        _require_digest_canonical_keys(payload)
        return payload
    return _duck_typed_digest_canonical_payload(inp)


def compute_producer_input_digest_from_canonical_payload_v1(payload: Mapping[str, Any]) -> str:
    """Reproduce the existing producer input_digest dialect. Does not redefine it."""
    _require_digest_canonical_keys(payload)
    canonical = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def project_double_play_entry_exit_policy_input_v1(
    inp: Any,
    *,
    record_id: str,
    event_time_utc: str,
    correlation_id: str,
    cycle_id: str | None,
    decision_event_ref: str,
    typed_output_observation_ref: str | None,
    producer_call_policy_version: str,
    capture_timing: str,
) -> MappingProxyType[str, Any]:
    """Build a frozen input-evidence record from a typed producer input."""
    if not is_typed_entry_exit_policy_input_v1(inp):
        return build_double_play_entry_exit_policy_input_evidence_v1(
            {
                "schema_name": SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
                "schema_version": SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1,
                "record_id": record_id,
                "event_time_utc": event_time_utc,
                "correlation_id": correlation_id,
                "cycle_id": cycle_id,
                "decision_event_ref": decision_event_ref,
                "typed_output_observation_ref": typed_output_observation_ref,
                "projection_id": PROJECTION_ID,
                "projection_status": UNAVAILABLE_PROJECTION_STATUS,
                "trading_authority": TRADING_AUTHORITY_NONE,
                "authority_owner": AUTHORITY_OWNER_NONE,
                "runtime_effect": RUNTIME_EFFECT_OBSERVATION_ONLY,
                "producer_owner": PRODUCER_OWNER,
                "producer_id": PRODUCER_ID,
                "producer_version": UNAVAILABLE_PROJECTION_STATUS,
                "producer_function_name": PRODUCER_FUNCTION_NAME,
                "producer_call_policy_version": producer_call_policy_version or UNKNOWN,
                "capture_timing": capture_timing or CAPTURE_TIMING_UNAVAILABLE,
                "producer_digest_canonical_payload": None,
                "producer_input_digest": None,
                "producer_input_digest_algorithm": DIGEST_ALGORITHM_ID,
                "digest_relation": DIGEST_RELATION_SUBSET_SCOPE,
                "producer_input_fields": None,
                "input_evidence_payload_hash": None,
                "code_sha": UNKNOWN,
                "evidence_hash": UNKNOWN,
                "causal_parent_ids": [decision_event_ref],
            }
        )
    fields = snapshot_double_play_producer_input_fields_v1(inp)
    digest_payload = producer_digest_canonical_payload_from_input_v1(inp)
    digest_fn = _producer_input_digest_fn()
    if digest_fn is not None:
        producer_digest = digest_fn(inp)
    else:
        producer_digest = compute_producer_input_digest_from_canonical_payload_v1(digest_payload)
    if not isinstance(producer_digest, str) or not producer_digest:
        raise DdoValidationError("PRODUCER_INPUT_DIGEST_MISSING")
    reproduced = compute_producer_input_digest_from_canonical_payload_v1(digest_payload)
    if reproduced != producer_digest:
        raise DdoValidationError("PRODUCER_INPUT_DIGEST_CANONICAL_PAYLOAD_MISMATCH")
    payload_hash = sha256_hex_v0(canonical_json_dumps_v0(fields))
    policy_version = _token(inp.policy_version)
    return build_double_play_entry_exit_policy_input_evidence_v1(
        {
            "schema_name": SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
            "schema_version": SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1,
            "record_id": record_id,
            "event_time_utc": event_time_utc,
            "correlation_id": correlation_id,
            "cycle_id": cycle_id,
            "decision_event_ref": decision_event_ref,
            "typed_output_observation_ref": typed_output_observation_ref,
            "projection_id": PROJECTION_ID,
            "projection_status": TYPED_PROJECTION_STATUS,
            "trading_authority": TRADING_AUTHORITY_NONE,
            "authority_owner": AUTHORITY_OWNER_NONE,
            "runtime_effect": RUNTIME_EFFECT_OBSERVATION_ONLY,
            "producer_owner": PRODUCER_OWNER,
            "producer_id": PRODUCER_ID,
            "producer_version": policy_version,
            "producer_function_name": PRODUCER_FUNCTION_NAME,
            "producer_call_policy_version": producer_call_policy_version or UNKNOWN,
            "capture_timing": capture_timing,
            "producer_digest_canonical_payload": digest_payload,
            "producer_input_digest": producer_digest,
            "producer_input_digest_algorithm": DIGEST_ALGORITHM_ID,
            "digest_relation": DIGEST_RELATION_SUBSET_SCOPE,
            "producer_input_fields": fields,
            "input_evidence_payload_hash": payload_hash,
            "code_sha": UNKNOWN,
            "evidence_hash": UNKNOWN,
            "causal_parent_ids": [decision_event_ref],
        }
    )


def reconstruct_typed_double_play_entry_exit_policy_input_v1(
    evidence: Mapping[str, Any],
) -> Any:
    """Rebuild DoublePlayEntryExitPolicyInputV0 from immutable evidence.

    This is reconstruction of the typed input object, not producer-function replay.
    """
    validated = validate_double_play_entry_exit_policy_input_evidence_v1(evidence)
    if validated["projection_status"] != TYPED_PROJECTION_STATUS:
        raise DdoValidationError("TYPED_INPUT_RECONSTRUCTION_REQUIRES_TYPED_PROJECTION")
    fields = validated["producer_input_fields"]
    if not isinstance(fields, Mapping):
        raise DdoValidationError("TYPED_INPUT_RECONSTRUCTION_REQUIRES_INPUT_FIELDS")
    constructors = _reconstruction_constructors()
    if constructors is None:
        raise DdoValidationError("TYPED_INPUT_RECONSTRUCTION_CONSTRUCTORS_UNAVAILABLE")
    composition = _reconstruct_composition(fields["composition_result"], constructors)
    signal_cls = constructors["PolicySignalV0"]
    inp_cls = constructors["DoublePlayEntryExitPolicyInputV0"]
    return inp_cls(
        instrument_id=str(fields["instrument_id"]),
        trading_epoch=int(fields["trading_epoch"]),
        context_reference=str(fields["context_reference"]),
        composition_result=composition,
        direction_state=constructors["EntryExitDirectionState"](fields["direction_state"]),
        position_state=constructors["PositionState"](fields["position_state"]),
        reconciliation_state=constructors["ReconciliationState"](fields["reconciliation_state"]),
        trading_gate=constructors["TradingGate"](fields["trading_gate"]),
        safety_mode=constructors["SafetyMode"](fields["safety_mode"]),
        data_integrity_state=constructors["DataIntegrityStatus"](fields["data_integrity_state"]),
        clock_trust_status=constructors["ClockTrustStatus"](fields["clock_trust_status"]),
        clock_trust_valid=bool(fields["clock_trust_valid"]),
        cooldown_pass=bool(fields["cooldown_pass"]),
        existing_position_side=constructors["ExistingPositionSide"](
            fields["existing_position_side"]
        ),
        venue_flat=bool(fields["venue_flat"]),
        scope_adverse_exit_signal=_reconstruct_signal(
            fields["scope_adverse_exit_signal"], signal_cls
        ),
        profit_protection_signal=_reconstruct_signal(
            fields["profit_protection_signal"], signal_cls
        ),
        time_exit_signal=_reconstruct_signal(fields["time_exit_signal"], signal_cls),
        strategy_invalidation_signal=_reconstruct_signal(
            fields["strategy_invalidation_signal"], signal_cls
        ),
        hard_risk_reduction_signal=_reconstruct_signal(
            fields["hard_risk_reduction_signal"], signal_cls
        ),
        safety_exit_signal=_reconstruct_signal(fields["safety_exit_signal"], signal_cls),
        input_complete=bool(fields["input_complete"]),
        input_digest=str(fields["input_digest"]),
        explicit_blocked_reasons=tuple(
            constructors["PolicyBlockedReason"](item) for item in fields["explicit_blocked_reasons"]
        ),
        policy_version=str(fields["policy_version"]),
    )


def build_double_play_entry_exit_policy_input_evidence_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "double_play_entry_exit_policy_input_evidence")
    reject_unknown_fields(raw, DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_ALLOWED_FIELDS)
    require_schema(
        raw,
        SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
        SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1,
    )
    status = require_enum(raw.get("projection_status"), "projection_status", PROJECTION_STATUS_V1)
    digest_payload_raw = raw.get("producer_digest_canonical_payload")
    fields_raw = raw.get("producer_input_fields")
    digest_raw = raw.get("producer_input_digest")
    payload_hash_raw = raw.get("input_evidence_payload_hash")
    if status == TYPED_PROJECTION_STATUS:
        if not isinstance(digest_payload_raw, dict):
            raise DdoValidationError("TYPED_INPUT_REQUIRES_DIGEST_CANONICAL_PAYLOAD")
        _require_digest_canonical_keys(digest_payload_raw)
        digest_payload: dict[str, Any] | None = dict(digest_payload_raw)
        if not isinstance(fields_raw, dict):
            raise DdoValidationError("TYPED_INPUT_REQUIRES_PRODUCER_INPUT_FIELDS")
        _require_input_field_keys(fields_raw)
        _reject_hindsight_and_secrets_mapping(fields_raw)
        fields: dict[str, Any] | None = dict(fields_raw)
        digest = require_sha256_or_unknown(digest_raw, "producer_input_digest")
        reproduced = compute_producer_input_digest_from_canonical_payload_v1(digest_payload)
        if digest != UNKNOWN and digest != reproduced:
            raise DdoValidationError("PRODUCER_INPUT_DIGEST_DOES_NOT_MATCH_CANONICAL_PAYLOAD")
        expected_payload_hash = sha256_hex_v0(canonical_json_dumps_v0(fields))
        payload_hash = require_sha256_or_unknown(payload_hash_raw, "input_evidence_payload_hash")
        if payload_hash != expected_payload_hash:
            raise DdoValidationError("INPUT_EVIDENCE_PAYLOAD_HASH_MISMATCH")
    else:
        if digest_payload_raw is not None:
            raise DdoValidationError("UNAVAILABLE_INPUT_MUST_NOT_CARRY_DIGEST_PAYLOAD")
        if fields_raw is not None:
            raise DdoValidationError("UNAVAILABLE_INPUT_MUST_NOT_CARRY_INPUT_FIELDS")
        if digest_raw is not None:
            raise DdoValidationError("UNAVAILABLE_INPUT_MUST_NOT_CARRY_PRODUCER_INPUT_DIGEST")
        if payload_hash_raw is not None:
            raise DdoValidationError("UNAVAILABLE_INPUT_MUST_NOT_CARRY_PAYLOAD_HASH")
        digest_payload = None
        fields = None
        digest = None
        payload_hash = None
    decision_ref = require_record_id(raw.get("decision_event_ref"), "decision_event_ref")
    output_ref = optional_record_id(
        raw.get("typed_output_observation_ref"), "typed_output_observation_ref"
    )
    canonical_record: dict[str, Any] = {
        "schema_name": SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
        "schema_version": SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1,
        "record_id": require_record_id(raw.get("record_id"), "record_id"),
        "event_time_utc": require_event_time_utc(raw.get("event_time_utc"), "event_time_utc"),
        "correlation_id": require_record_id(raw.get("correlation_id"), "correlation_id"),
        "cycle_id": optional_record_id(raw.get("cycle_id"), "cycle_id"),
        "decision_event_ref": decision_ref,
        "typed_output_observation_ref": output_ref,
        "projection_id": require_non_empty_string_or_unknown(
            raw.get("projection_id"), "projection_id"
        ),
        "projection_status": status,
        "trading_authority": require_enum(
            raw.get("trading_authority"), "trading_authority", TRADING_AUTHORITY_V1
        ),
        "authority_owner": require_enum(
            raw.get("authority_owner"), "authority_owner", AUTHORITY_OWNER_V1
        ),
        "runtime_effect": require_enum(
            raw.get("runtime_effect"), "runtime_effect", RUNTIME_EFFECT_V1
        ),
        "producer_owner": require_non_empty_string_or_unknown(
            raw.get("producer_owner"), "producer_owner"
        ),
        "producer_id": require_non_empty_string_or_unknown(raw.get("producer_id"), "producer_id"),
        "producer_version": require_non_empty_string_or_unknown(
            raw.get("producer_version"), "producer_version"
        ),
        "producer_function_name": require_non_empty_string_or_unknown(
            raw.get("producer_function_name"), "producer_function_name"
        ),
        "producer_call_policy_version": require_non_empty_string_or_unknown(
            raw.get("producer_call_policy_version"), "producer_call_policy_version"
        ),
        "capture_timing": require_enum(
            raw.get("capture_timing"), "capture_timing", CAPTURE_TIMING_V1
        ),
        "producer_digest_canonical_payload": digest_payload,
        "producer_input_digest": digest,
        "producer_input_digest_algorithm": require_non_empty_string_or_unknown(
            raw.get("producer_input_digest_algorithm"), "producer_input_digest_algorithm"
        ),
        "digest_relation": require_non_empty_string_or_unknown(
            raw.get("digest_relation"), "digest_relation"
        ),
        "producer_input_fields": fields,
        "input_evidence_payload_hash": payload_hash,
        "code_sha": require_sha256_or_unknown(raw.get("code_sha"), "code_sha"),
        "evidence_hash": require_sha256_or_unknown(raw.get("evidence_hash"), "evidence_hash"),
        "causal_parent_ids": require_id_list(raw.get("causal_parent_ids"), "causal_parent_ids"),
    }
    if decision_ref not in canonical_record["causal_parent_ids"]:
        raise DdoValidationError("INPUT_EVIDENCE_PARENT_MUST_INCLUDE_DECISION_EVENT_REF")
    hashed = attach_content_hash(canonical_record)
    if "content_hash" in raw and raw["content_hash"] != hashed["content_hash"]:
        raise DdoValidationError("CONTENT_HASH_MISMATCH")
    return freeze_record(hashed)


def validate_double_play_entry_exit_policy_input_evidence_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    return build_double_play_entry_exit_policy_input_evidence_v1(payload)


def policy_version_from_policy_object_v1(policy: Any) -> str:
    if policy is None:
        return UNKNOWN
    version = getattr(policy, "policy_version", None)
    if not isinstance(version, str) or not version:
        return UNKNOWN
    return version


def _require_digest_canonical_keys(payload: Mapping[str, Any]) -> None:
    missing = [key for key in PRODUCER_DIGEST_CANONICAL_KEYS if key not in payload]
    if missing:
        raise DdoValidationError(f"PRODUCER_DIGEST_CANONICAL_KEYS_MISSING:{missing}")
    extra = sorted(set(payload.keys()) - set(PRODUCER_DIGEST_CANONICAL_KEYS))
    if extra:
        raise DdoValidationError(f"PRODUCER_DIGEST_CANONICAL_UNEXPECTED_KEY:{extra}")


def _require_input_field_keys(payload: Mapping[str, Any]) -> None:
    missing = [key for key in PRODUCER_INPUT_FIELD_KEYS if key not in payload]
    if missing:
        raise DdoValidationError(f"PRODUCER_INPUT_FIELDS_MISSING:{missing}")
    extra = sorted(set(payload.keys()) - set(PRODUCER_INPUT_FIELD_KEYS))
    if extra:
        raise DdoValidationError(f"PRODUCER_INPUT_FIELDS_UNEXPECTED:{extra}")
    composition = payload.get("composition_result")
    if not isinstance(composition, Mapping):
        raise DdoValidationError("COMPOSITION_RESULT_MUST_BE_OBJECT")
    missing_comp = [key for key in COMPOSITION_CANONICAL_KEYS if key not in composition]
    if missing_comp:
        raise DdoValidationError(f"COMPOSITION_CANONICAL_KEYS_MISSING:{missing_comp}")
    if "semantic_digest" not in composition:
        raise DdoValidationError("COMPOSITION_SEMANTIC_DIGEST_MISSING")
    for signal_key in SIGNAL_FIELD_KEYS:
        signal = payload.get(signal_key)
        if not isinstance(signal, Mapping):
            raise DdoValidationError(f"SIGNAL_MUST_BE_OBJECT:{signal_key}")
        if "triggered" not in signal or "reason_code" not in signal:
            raise DdoValidationError(f"SIGNAL_FIELDS_MISSING:{signal_key}")
        extra_signal = sorted(set(signal.keys()) - {"triggered", "reason_code"})
        if extra_signal:
            raise DdoValidationError(f"SIGNAL_UNEXPECTED_KEY:{signal_key}:{extra_signal}")


def _composition_fields_from_result(composition: Any) -> dict[str, Any]:
    serializer = _canonical_composition_serializer()
    if serializer is None:
        raise DdoValidationError("COMPOSITION_SERIALIZER_UNAVAILABLE")
    raw = serializer(composition)
    if not isinstance(raw, str):
        raise DdoValidationError("COMPOSITION_SERIALIZER_MUST_RETURN_STRING")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise DdoValidationError("COMPOSITION_CANONICAL_PAYLOAD_MUST_BE_OBJECT")
    missing = [key for key in COMPOSITION_CANONICAL_KEYS if key not in payload]
    if missing:
        raise DdoValidationError(f"COMPOSITION_CANONICAL_KEYS_MISSING:{missing}")
    semantic = getattr(composition, "semantic_digest", None)
    if not isinstance(semantic, str):
        raise DdoValidationError("COMPOSITION_SEMANTIC_DIGEST_MUST_BE_STRING")
    payload["semantic_digest"] = semantic
    return payload


def _signal_fields(signal: Any) -> dict[str, Any]:
    triggered = getattr(signal, "triggered", None)
    reason = getattr(signal, "reason_code", None)
    if reason is None:
        reason = ""
    if not isinstance(reason, str):
        raise DdoValidationError("SIGNAL_REASON_CODE_MUST_BE_STRING")
    return {
        "triggered": _require_bool(triggered, "triggered"),
        "reason_code": reason,
    }


def _duck_typed_digest_canonical_payload(inp: Any) -> dict[str, Any]:
    composition = getattr(inp, "composition_result")
    payload: dict[str, Any] = {
        "instrument_id": _token(inp.instrument_id),
        "trading_epoch": _require_int(inp.trading_epoch, "trading_epoch"),
        "context_reference": _token(inp.context_reference),
        "composition_result_ref": _token(composition.composition_id),
        "composition_semantic_digest": _token(composition.semantic_digest),
        "direction_state": _token(inp.direction_state),
        "position_state": _token(inp.position_state),
        "reconciliation_state": _token(inp.reconciliation_state),
        "trading_gate": _token(inp.trading_gate),
        "safety_mode": _token(inp.safety_mode),
        "data_integrity_state": _token(inp.data_integrity_state),
        "clock_trust_status": _token(inp.clock_trust_status),
        "clock_trust_valid": _require_bool(inp.clock_trust_valid, "clock_trust_valid"),
        "cooldown_pass": _require_bool(inp.cooldown_pass, "cooldown_pass"),
        "existing_position_side": _token(inp.existing_position_side),
        "venue_flat": _require_bool(inp.venue_flat, "venue_flat"),
        "scope_adverse_exit_signal": _require_bool(
            inp.scope_adverse_exit_signal.triggered, "scope_adverse_exit_signal"
        ),
        "profit_protection_signal": _require_bool(
            inp.profit_protection_signal.triggered, "profit_protection_signal"
        ),
        "time_exit_signal": _require_bool(inp.time_exit_signal.triggered, "time_exit_signal"),
        "strategy_invalidation_signal": _require_bool(
            inp.strategy_invalidation_signal.triggered, "strategy_invalidation_signal"
        ),
        "hard_risk_reduction_signal": _require_bool(
            inp.hard_risk_reduction_signal.triggered, "hard_risk_reduction_signal"
        ),
        "safety_exit_signal": _require_bool(inp.safety_exit_signal.triggered, "safety_exit_signal"),
        "input_complete": _require_bool(inp.input_complete, "input_complete"),
        "explicit_blocked_reasons": sorted(_token(item) for item in inp.explicit_blocked_reasons),
        "policy_version": _token(inp.policy_version),
    }
    _require_digest_canonical_keys(payload)
    return payload


def _reconstruct_signal(payload: Mapping[str, Any], signal_cls: Any) -> Any:
    return signal_cls(
        triggered=bool(payload["triggered"]),
        reason_code=str(payload["reason_code"]),
    )


def _reconstruct_composition(payload: Mapping[str, Any], constructors: Mapping[str, Any]) -> Any:
    side_cls = constructors["DirectionalAssessmentSide"]
    return constructors["DoublePlayCompositionResultV1"](
        composition_id=str(payload["composition_id"]),
        instrument_id=str(payload["instrument_id"]),
        trading_epoch=int(payload["trading_epoch"]),
        context_reference=str(payload["context_reference"]),
        bull_assessment_ref=_reconstruct_directional_ref(
            payload["bull_assessment_ref"], constructors, side_cls
        ),
        bear_assessment_ref=_reconstruct_directional_ref(
            payload["bear_assessment_ref"], constructors, side_cls
        ),
        bull_survival_ref=_reconstruct_survival_ref(
            payload["bull_survival_ref"], constructors, side_cls
        ),
        bear_survival_ref=_reconstruct_survival_ref(
            payload["bear_survival_ref"], constructors, side_cls
        ),
        bull_suitability_ref=_reconstruct_suitability_ref(
            payload["bull_suitability_ref"], constructors, side_cls
        ),
        bear_suitability_ref=_reconstruct_suitability_ref(
            payload["bear_suitability_ref"], constructors, side_cls
        ),
        previous_direction_state=constructors["CompositionDirectionState"](
            payload["previous_direction_state"]
        ),
        position_management_context=constructors["PositionManagementContext"](
            payload["position_management_context"]
        ),
        composition_status=constructors["CompositionStatus"](payload["composition_status"]),
        selected_side=constructors["CompositionSelectedSide"](payload["selected_side"]),
        conflict_status=constructors["CompositionConflictStatus"](payload["conflict_status"]),
        chop_guard_status=constructors["CompositionChopGuardStatus"](payload["chop_guard_status"]),
        reason_codes=tuple(str(item) for item in payload["reason_codes"]),
        policy_version=str(payload["policy_version"]),
        input_digest=str(payload["input_digest"]),
        semantic_digest=str(payload["semantic_digest"]),
        authority_effect=str(payload["authority_effect"]),
        runtime_effect=str(payload["runtime_effect"]),
        order_effect=str(payload["order_effect"]),
        risk_effect=str(payload["risk_effect"]),
        sizing_effect=str(payload["sizing_effect"]),
    )


def _reconstruct_directional_ref(
    payload: Mapping[str, Any],
    constructors: Mapping[str, Any],
    side_cls: Any,
) -> Any:
    return constructors["DirectionalAssessmentRefV1"](
        assessment_id=str(payload["assessment_id"]),
        semantic_digest=str(payload["semantic_digest"]),
        trading_epoch=int(payload["trading_epoch"]),
        side=side_cls(payload["side"]),
        status=str(payload["status"]),
    )


def _reconstruct_survival_ref(
    payload: Mapping[str, Any],
    constructors: Mapping[str, Any],
    side_cls: Any,
) -> Any:
    return constructors["SurvivalResultRefV1"](
        survival_id=str(payload["survival_id"]),
        semantic_digest=str(payload["semantic_digest"]),
        trading_epoch=int(payload["trading_epoch"]),
        side=side_cls(payload["side"]),
        status=constructors["SurvivalAssessmentStatus"](payload["status"]),
    )


def _reconstruct_suitability_ref(
    payload: Mapping[str, Any],
    constructors: Mapping[str, Any],
    side_cls: Any,
) -> Any:
    return constructors["SuitabilityResultRefV1"](
        suitability_id=str(payload["suitability_id"]),
        semantic_digest=str(payload["semantic_digest"]),
        trading_epoch=int(payload["trading_epoch"]),
        side=side_cls(payload["side"]),
        status=constructors["SuitabilityBindingStatus"](payload["status"]),
    )


def _reject_hindsight_and_secrets_object(obj: Any) -> None:
    names = getattr(obj, "__annotations__", None)
    keys: Sequence[str]
    if isinstance(names, Mapping):
        keys = tuple(names)
    else:
        keys = tuple(getattr(obj, "__dataclass_fields__", {}) or ())
    extra_hindsight = sorted(key for key in keys if key in _HINDSIGHT_KEYS)
    if extra_hindsight:
        raise DdoValidationError(f"HINDSIGHT_FIELD_FORBIDDEN:{extra_hindsight}")
    extra_secret = sorted(key for key in keys if key in _SECRET_KEYS)
    if extra_secret:
        raise DdoValidationError(f"SECRET_FIELD_FORBIDDEN:{extra_secret}")


def _reject_hindsight_and_secrets_mapping(payload: Mapping[str, Any]) -> None:
    _scan_forbidden(payload)


def _scan_forbidden(value: Any) -> None:
    if isinstance(value, Mapping):
        extra_hindsight = sorted(key for key in value if key in _HINDSIGHT_KEYS)
        if extra_hindsight:
            raise DdoValidationError(f"HINDSIGHT_FIELD_FORBIDDEN:{extra_hindsight}")
        extra_secret = sorted(key for key in value if key in _SECRET_KEYS)
        if extra_secret:
            raise DdoValidationError(f"SECRET_FIELD_FORBIDDEN:{extra_secret}")
        for inner in value.values():
            _scan_forbidden(inner)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _scan_forbidden(item)


def _token(value: Any) -> str:
    raw = getattr(value, "value", value)
    if not isinstance(raw, str):
        raise DdoValidationError("PRODUCER_TOKEN_MUST_BE_STRING")
    return raw


def _digest_or_empty(value: Any) -> str:
    if not isinstance(value, str):
        raise DdoValidationError("INPUT_DIGEST_MUST_BE_STRING")
    return value


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise DdoValidationError(f"PRODUCER_FIELD_MUST_BE_BOOL:{field}")
    return value


def _require_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise DdoValidationError(f"PRODUCER_FIELD_MUST_BE_INT:{field}")
    return value


def _entry_exit_input_class() -> type[Any] | None:
    try:
        from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
            DoublePlayEntryExitPolicyInputV0,
        )
    except ImportError:
        return None
    return DoublePlayEntryExitPolicyInputV0


def _canonical_input_serializer() -> Any | None:
    try:
        from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
            serialize_entry_exit_policy_input_canonical,
        )
    except ImportError:
        return None
    return serialize_entry_exit_policy_input_canonical


def _producer_input_digest_fn() -> Any | None:
    try:
        from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
            compute_entry_exit_policy_input_digest,
        )
    except ImportError:
        return None
    return compute_entry_exit_policy_input_digest


def _canonical_composition_serializer() -> Any | None:
    try:
        from trading.master_v2.double_play_composition_matrix_v1 import (  # noqa: PLC0415
            serialize_composition_result_canonical,
        )
    except ImportError:
        return None
    return serialize_composition_result_canonical


def _reconstruction_constructors() -> dict[str, Any] | None:
    try:
        from trading.master_v2.canonical_market_context_v1 import (  # noqa: PLC0415
            ClockTrustStatus,
            DataIntegrityStatus,
        )
        from trading.master_v2.directional_assessment_v1 import (  # noqa: PLC0415
            DirectionalAssessmentSide,
        )
        from trading.master_v2.double_play_composition_matrix_v1 import (  # noqa: PLC0415
            CompositionChopGuardStatus,
            CompositionConflictStatus,
            CompositionDirectionState,
            CompositionSelectedSide,
            CompositionStatus,
            DoublePlayCompositionResultV1,
            PositionManagementContext,
            SuitabilityResultRefV1,
        )
        from trading.master_v2.double_play_entry_exit_policy_v0 import (  # noqa: PLC0415
            DoublePlayEntryExitPolicyInputV0,
            EntryExitDirectionState,
            ExistingPositionSide,
            PolicyBlockedReason,
            PolicySignalV0,
            PositionState,
            ReconciliationState,
            SafetyMode,
            TradingGate,
        )
        from trading.master_v2.suitability_binding_v1 import (  # noqa: PLC0415
            DirectionalAssessmentRefV1,
            SuitabilityBindingStatus,
            SurvivalResultRefV1,
        )
        from trading.master_v2.survival_assessment_v1 import (  # noqa: PLC0415
            SurvivalAssessmentStatus,
        )
    except ImportError:
        return None
    return {
        "ClockTrustStatus": ClockTrustStatus,
        "DataIntegrityStatus": DataIntegrityStatus,
        "DirectionalAssessmentSide": DirectionalAssessmentSide,
        "CompositionChopGuardStatus": CompositionChopGuardStatus,
        "CompositionConflictStatus": CompositionConflictStatus,
        "CompositionDirectionState": CompositionDirectionState,
        "CompositionSelectedSide": CompositionSelectedSide,
        "CompositionStatus": CompositionStatus,
        "DoublePlayCompositionResultV1": DoublePlayCompositionResultV1,
        "PositionManagementContext": PositionManagementContext,
        "SuitabilityResultRefV1": SuitabilityResultRefV1,
        "DoublePlayEntryExitPolicyInputV0": DoublePlayEntryExitPolicyInputV0,
        "EntryExitDirectionState": EntryExitDirectionState,
        "ExistingPositionSide": ExistingPositionSide,
        "PolicyBlockedReason": PolicyBlockedReason,
        "PolicySignalV0": PolicySignalV0,
        "PositionState": PositionState,
        "ReconciliationState": ReconciliationState,
        "SafetyMode": SafetyMode,
        "TradingGate": TradingGate,
        "DirectionalAssessmentRefV1": DirectionalAssessmentRefV1,
        "SuitabilityBindingStatus": SuitabilityBindingStatus,
        "SurvivalResultRefV1": SurvivalResultRefV1,
        "SurvivalAssessmentStatus": SurvivalAssessmentStatus,
    }
