"""
Offline Intent Compatibility Firewall v1 (RUNBOOK STEP 29O).

Pure, deterministic, fail-closed classification of intent-type descriptor
snapshots and explicit conversion edges. No runtime objects, transformations,
quantity math, adapter submission, orders, or authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any, Mapping, Sequence

CONTRACT_NAME = "intent_compatibility_firewall_v1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "intent_compatibility_firewall_schema_v1"

CANONICAL_ORDER_INTENT_OWNER_MODULE = "src.governance.canonical_order_intent_v1"
CANONICAL_TO_ADAPTER_TRANSFORMATION_ID = "canonical_order_intent_v1_to_adapter_order_intent_v1"
CANONICAL_TO_ADAPTER_TRANSFORMATION_VERSION = "v1"
CANONICAL_TO_ADAPTER_FIELD_MAPPING_VERSION = "canonical_to_adapter_order_intent_field_mapping_v1"
CANONICAL_IDENTITY_OWNER_MODULE = "src.meta.learning_loop.canonical_order_lifecycle_v1"
CANONICAL_IDENTITY_SYMBOL = "CanonicalOrderIntentIdentity"
CANONICAL_IDENTITY_CONTRACT_VERSION = "canonical_order_intent_identity_contract_v1"
ORDER_INTENT_IDEMPOTENCY_OWNER_MODULE = "src.meta.learning_loop.order_intent_idempotency_v1"
CANONICAL_ORDER_LIFECYCLE_OWNER_MODULE = "src.meta.learning_loop.canonical_order_lifecycle_v1"
TRADING_CORE_DECISION_ATTESTATION_OWNER_MODULE = (
    "src.meta.learning_loop.trading_core_decision_attestation_v1"
)

CANONICAL_IDENTITY_REFERENCE = (
    f"{CANONICAL_IDENTITY_OWNER_MODULE}::{CANONICAL_IDENTITY_SYMBOL}::"
    f"{CANONICAL_IDENTITY_CONTRACT_VERSION}"
)

PACKAGE_MARKER = "INTENT_COMPATIBILITY_FIREWALL_V1=true"
IMPLICIT_INTENT_CONVERSION_ALLOWED = False
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

AUTHORITY_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"

_AUTHORITY_EFFECT = False
_RUNTIME_EFFECT = False
_ORDER_EFFECT = False

_FORBIDDEN_INSTRUMENT_MARKERS = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_FORBIDDEN_DOMAIN_MARKERS = frozenset({"spot", "synthetic_spot", "synthetic-spot"})
_FORBIDDEN_BITCOIN_MARKERS = frozenset({"btc", "xbt", "bitcoin"})
_EXPLICIT_CONVERSION_KINDS = frozenset(
    {"EXPLICIT_ADAPTER", "EXPLICIT_POLICY", "IDENTITY_NO_CONVERSION"}
)


class ContractTypeClassification(str, Enum):
    CANONICAL_DECISION = "CANONICAL_DECISION"
    CAPITAL_ENVELOPE = "CAPITAL_ENVELOPE"
    PRE_SIZING_RISK = "PRE_SIZING_RISK"
    SIZING_RESULT = "SIZING_RESULT"
    POST_SIZING_RISK = "POST_SIZING_RISK"
    CANONICAL_ORDER_INTENT = "CANONICAL_ORDER_INTENT"
    EXECUTION_PERMISSION = "EXECUTION_PERMISSION"
    ADAPTER_PAYLOAD = "ADAPTER_PAYLOAD"
    LEGACY_OR_AMBIGUOUS = "LEGACY_OR_AMBIGUOUS"
    BOUNDARY_FIXTURE = "BOUNDARY_FIXTURE"


class ContractCompatibilityStatusV1(str, Enum):
    INCOMPATIBLE = "INCOMPATIBLE"
    TRANSFORMATION_REQUIRED = "TRANSFORMATION_REQUIRED"
    STRUCTURALLY_COMPATIBLE_NOT_EXECUTION_ELIGIBLE = (
        "STRUCTURALLY_COMPATIBLE_NOT_EXECUTION_ELIGIBLE"
    )
    CANONICAL_ORDER_INTENT_REQUIRED = "CANONICAL_ORDER_INTENT_REQUIRED"
    PERMISSION_REQUIRED = "PERMISSION_REQUIRED"
    ADAPTER_COMPATIBLE = "ADAPTER_COMPATIBLE"


REASON_UNKNOWN_SOURCE_CONTRACT = "UNKNOWN_SOURCE_CONTRACT"
REASON_UNKNOWN_SOURCE_CONTRACT_VERSION = "UNKNOWN_SOURCE_CONTRACT_VERSION"
REASON_UNKNOWN_TARGET_CONTRACT = "UNKNOWN_TARGET_CONTRACT"
REASON_LEGACY_ALIAS_WITHOUT_TRANSFORMATION = "LEGACY_ALIAS_WITHOUT_TRANSFORMATION"
REASON_DUCK_TYPING_FIELD_MATCH_INSUFFICIENT = "DUCK_TYPING_FIELD_MATCH_INSUFFICIENT"
REASON_CANONICAL_DECISION_NOT_ORDER_INTENT = "CANONICAL_DECISION_NOT_ORDER_INTENT"
REASON_CANONICAL_ORDER_INTENT_REQUIRED = "CANONICAL_ORDER_INTENT_REQUIRED"
REASON_RISK_OUTPUT_NOT_ADAPTER_COMPATIBLE = "RISK_OUTPUT_NOT_ADAPTER_COMPATIBLE"
REASON_SIZING_OUTPUT_NOT_ADAPTER_COMPATIBLE = "SIZING_OUTPUT_NOT_ADAPTER_COMPATIBLE"
REASON_MISSING_QUANTITY_BINDING = "MISSING_QUANTITY_BINDING"
REASON_MISSING_QUANTITY_PROVENANCE_BINDING = "MISSING_QUANTITY_PROVENANCE_BINDING"
REASON_MISSING_ORDER_TYPE_BINDING = "MISSING_ORDER_TYPE_BINDING"
REASON_MISSING_REDUCE_ONLY_BINDING = "MISSING_REDUCE_ONLY_BINDING"
REASON_MISSING_VENUE_BINDING = "MISSING_VENUE_BINDING"
REASON_MISSING_ACCOUNT_BINDING = "MISSING_ACCOUNT_BINDING"
REASON_MISSING_INSTRUMENT_BINDING = "MISSING_INSTRUMENT_BINDING"
REASON_MISSING_POLICY_DIGEST_BINDING = "MISSING_POLICY_DIGEST_BINDING"
REASON_MISSING_CONFIG_DIGEST_BINDING = "MISSING_CONFIG_DIGEST_BINDING"
REASON_MISSING_IMPLEMENTATION_DIGEST_BINDING = "MISSING_IMPLEMENTATION_DIGEST_BINDING"
REASON_MISSING_PERMISSION_BINDING = "MISSING_PERMISSION_BINDING"
REASON_MISSING_AUTHORITY_LEASE_BINDING = "MISSING_AUTHORITY_LEASE_BINDING"
REASON_MISSING_FENCING_TOKEN_BINDING = "MISSING_FENCING_TOKEN_BINDING"
REASON_IMPLICIT_CONVERSION_FORBIDDEN = "IMPLICIT_CONVERSION_FORBIDDEN"
REASON_NON_FUTURES_CONTRACT = "NON_FUTURES_CONTRACT"
REASON_BITCOIN_DIRECTION_FORBIDDEN = "BITCOIN_DIRECTION_FORBIDDEN"
REASON_TRANSFORMATION_REQUIRED_NO_DEFAULTS = "TRANSFORMATION_REQUIRED_NO_DEFAULTS"
REASON_BOUNDARY_STRUCTURAL_ONLY = "BOUNDARY_STRUCTURAL_ONLY"
REASON_STEP29O_ADAPTER_COMPATIBILITY_BLOCKED = "STEP29O_ADAPTER_COMPATIBILITY_BLOCKED"


@dataclass(frozen=True)
class ContractTypeRegistryEntryV1:
    contract_type: str
    contract_version: str
    owner_module: str
    classification: ContractTypeClassification
    adapter_compatible_by_default: bool
    transformation_required_for_adapter: bool


@dataclass(frozen=True)
class ContractBindingSnapshotV1:
    quantity_bound: bool = False
    quantity_provenance_bound: bool = False
    order_type_bound: bool = False
    reduce_only_bound: bool = False
    venue_bound: bool = False
    account_bound: bool = False
    instrument_bound: bool = False
    risk_provenance_bound: bool = False
    policy_digest_bound: bool = False
    config_digest_bound: bool = False
    implementation_digest_bound: bool = False
    permission_bound: bool = False
    authority_bound: bool = False
    fencing_token_bound: bool = False
    futures_only: bool = True
    bitcoin_direction: bool = False
    spot_market: bool = False
    synthetic_spot_market: bool = False
    legacy_alias: bool = False
    duck_typed_order_fields: bool = False


@dataclass(frozen=True)
class IntentCompatibilityAssessmentV1:
    source_contract_type: str
    source_contract_version: str
    target_contract_type: str
    target_contract_version: str
    compatibility_status: ContractCompatibilityStatusV1
    transformation_required: bool
    quantity_bound: bool
    order_type_bound: bool
    reduce_only_bound: bool
    venue_bound: bool
    account_bound: bool
    instrument_bound: bool
    risk_provenance_bound: bool
    policy_digest_bound: bool
    config_digest_bound: bool
    implementation_digest_bound: bool
    permission_bound: bool
    authority_bound: bool
    adapter_compatible: bool
    reason_codes: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    runtime_effect: str = RUNTIME_EFFECT_NONE
    assessment_digest: str = ""


class IntentCompatibilityVerdictV1(str, Enum):
    ADMISSIBLE = "ADMISSIBLE"
    BLOCKED_UNKNOWN_INTENT_TYPE = "BLOCKED_UNKNOWN_INTENT_TYPE"
    BLOCKED_IMPLICIT_CONVERSION = "BLOCKED_IMPLICIT_CONVERSION"
    BLOCKED_MISSING_CANONICAL_BINDING = "BLOCKED_MISSING_CANONICAL_BINDING"
    BLOCKED_SIDE_SEMANTICS = "BLOCKED_SIDE_SEMANTICS"
    BLOCKED_QUANTITY_SEMANTICS = "BLOCKED_QUANTITY_SEMANTICS"
    BLOCKED_QUANTITY_PROVENANCE = "BLOCKED_QUANTITY_PROVENANCE"
    BLOCKED_REDUCE_ONLY_SEMANTICS = "BLOCKED_REDUCE_ONLY_SEMANTICS"
    BLOCKED_INSTRUMENT_BINDING = "BLOCKED_INSTRUMENT_BINDING"
    BLOCKED_VENUE_BINDING = "BLOCKED_VENUE_BINDING"
    BLOCKED_ACCOUNT_BINDING = "BLOCKED_ACCOUNT_BINDING"
    BLOCKED_IDENTITY_BINDING = "BLOCKED_IDENTITY_BINDING"
    BLOCKED_AUTHORITY_BINDING = "BLOCKED_AUTHORITY_BINDING"
    BLOCKED_RUNTIME_EFFECT = "BLOCKED_RUNTIME_EFFECT"
    BLOCKED_ORDER_EFFECT = "BLOCKED_ORDER_EFFECT"
    BLOCKED_ADAPTER_SUBMISSION_EFFECT = "BLOCKED_ADAPTER_SUBMISSION_EFFECT"
    BLOCKED_NON_FUTURES_INTENT = "BLOCKED_NON_FUTURES_INTENT"
    BLOCKED_BITCOIN_SPECIFIC_DIRECTION = "BLOCKED_BITCOIN_SPECIFIC_DIRECTION"


@dataclass(frozen=True)
class IntentTransformationDescriptorV1:
    source_contract: str
    source_version: str
    target_contract: str
    target_version: str
    transformation_id: str
    transformation_version: str
    field_mapping_version: str
    source_digest: str
    target_digest: str
    lossless_fields: tuple[str, ...]
    rejected_unbound_fields: tuple[str, ...]
    runtime_effect: bool
    order_effect: bool
    authority_effect: bool
    network_effect: bool
    adapter_submission_effect: bool


@dataclass(frozen=True)
class IntentTypeDescriptorV1:
    intent_type_id: str
    owner_module: str
    producer_domain: str
    consumer_domain: str
    persistence_lifecycle: str
    quantity_semantics: str
    side_semantics: str
    reduce_only_semantics: str
    instrument_binding_present: bool
    venue_binding_present: bool
    account_binding_present: bool
    trading_epoch_binding_present: bool
    intent_id_binding_present: bool
    client_order_id_binding_present: bool
    authority_binding_present: bool
    permission_binding_present: bool
    quantity_provenance_present: bool
    canonical_identity_compatible: bool
    runtime_effect: bool
    order_effect: bool
    adapter_submission_effect: bool
    semantic_digest: str


@dataclass(frozen=True)
class IntentConversionEdgeV1:
    source_intent_type_id: str
    target_intent_type_id: str
    conversion_kind: str
    explicit_adapter_id: str
    explicit_policy_id: str
    preserves_quantity_semantics: bool
    preserves_side_semantics: bool
    preserves_reduce_only_semantics: bool
    preserves_instrument_binding: bool
    preserves_venue_binding: bool
    preserves_account_binding: bool
    preserves_identity_binding: bool
    preserves_authority_binding: bool
    semantic_digest: str


@dataclass(frozen=True)
class IntentCompatibilityResultV1:
    verdict: IntentCompatibilityVerdictV1
    admissible: bool
    reason_codes: tuple[str, ...]
    source_descriptor_digest: str
    target_descriptor_digest: str
    conversion_edge_digest: str
    canonical_identity_reference: str
    runtime_effect: bool = False
    order_effect: bool = False
    authority_effect: bool = False
    transformation_performed: bool = False


def _sha256_hex(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compute_intent_type_descriptor_digest(descriptor: IntentTypeDescriptorV1) -> str:
    payload = {
        field.name: getattr(descriptor, field.name)
        for field in fields(IntentTypeDescriptorV1)
        if field.name != "semantic_digest"
    }
    return _sha256_hex(payload)


def compute_intent_conversion_edge_digest(edge: IntentConversionEdgeV1) -> str:
    payload = {
        field.name: getattr(edge, field.name)
        for field in fields(IntentConversionEdgeV1)
        if field.name != "semantic_digest"
    }
    return _sha256_hex(payload)


def with_computed_descriptor_digest(
    descriptor: IntentTypeDescriptorV1,
) -> IntentTypeDescriptorV1:
    digest = compute_intent_type_descriptor_digest(descriptor)
    if descriptor.semantic_digest == digest:
        return descriptor
    return IntentTypeDescriptorV1(
        **{
            **{
                field.name: getattr(descriptor, field.name)
                for field in fields(IntentTypeDescriptorV1)
            },
            "semantic_digest": digest,
        }
    )


def with_computed_conversion_edge_digest(edge: IntentConversionEdgeV1) -> IntentConversionEdgeV1:
    digest = compute_intent_conversion_edge_digest(edge)
    if edge.semantic_digest == digest:
        return edge
    return IntentConversionEdgeV1(
        **{
            **{field.name: getattr(edge, field.name) for field in fields(IntentConversionEdgeV1)},
            "semantic_digest": digest,
        }
    )


def _canonical_bindings_present(descriptor: IntentTypeDescriptorV1) -> bool:
    return (
        descriptor.instrument_binding_present
        and descriptor.venue_binding_present
        and descriptor.account_binding_present
        and descriptor.trading_epoch_binding_present
        and descriptor.intent_id_binding_present
        and descriptor.client_order_id_binding_present
        and descriptor.authority_binding_present
        and descriptor.permission_binding_present
        and descriptor.canonical_identity_compatible
    )


def _non_futures_descriptor(descriptor: IntentTypeDescriptorV1) -> bool:
    lowered_id = descriptor.intent_type_id.lower()
    if any(marker.lower() in lowered_id for marker in _FORBIDDEN_INSTRUMENT_MARKERS):
        return True
    producer = descriptor.producer_domain.lower()
    consumer = descriptor.consumer_domain.lower()
    if any(marker in producer or marker in consumer for marker in _FORBIDDEN_DOMAIN_MARKERS):
        return True
    upper_producer = descriptor.producer_domain.upper()
    return any(marker in upper_producer for marker in _FORBIDDEN_INSTRUMENT_MARKERS)


def _bitcoin_direction_descriptor(descriptor: IntentTypeDescriptorV1) -> bool:
    if descriptor.side_semantics.upper() == "BITCOIN_DIRECTION":
        return True
    combined = f"{descriptor.producer_domain} {descriptor.consumer_domain}".lower()
    return any(marker in combined for marker in _FORBIDDEN_BITCOIN_MARKERS) and (
        "direction" in combined or descriptor.side_semantics.upper() == "BITCOIN_DIRECTION"
    )


def _side_semantics_compatible(
    source: IntentTypeDescriptorV1, target: IntentTypeDescriptorV1
) -> bool:
    return source.side_semantics == target.side_semantics


def _quantity_semantics_compatible(
    source: IntentTypeDescriptorV1, target: IntentTypeDescriptorV1
) -> bool:
    if source.quantity_semantics == target.quantity_semantics:
        return True
    if source.quantity_semantics == "decimal" and target.quantity_semantics == "float":
        return False
    if source.quantity_semantics == "digest_bound" and target.quantity_semantics != "digest_bound":
        return False
    return source.quantity_semantics == target.quantity_semantics


def _result(
    *,
    verdict: IntentCompatibilityVerdictV1,
    reason_codes: Sequence[str],
    source_digest: str,
    target_digest: str,
    edge_digest: str,
) -> IntentCompatibilityResultV1:
    sorted_reasons = tuple(sorted(set(reason_codes)))
    admissible = verdict == IntentCompatibilityVerdictV1.ADMISSIBLE
    return IntentCompatibilityResultV1(
        verdict=verdict,
        admissible=admissible,
        reason_codes=sorted_reasons,
        source_descriptor_digest=source_digest,
        target_descriptor_digest=target_digest,
        conversion_edge_digest=edge_digest,
        canonical_identity_reference=CANONICAL_IDENTITY_REFERENCE,
        runtime_effect=_RUNTIME_EFFECT,
        order_effect=_ORDER_EFFECT,
        authority_effect=_AUTHORITY_EFFECT,
        transformation_performed=False,
    )


def evaluate_intent_compatibility_v1(
    source: IntentTypeDescriptorV1,
    target: IntentTypeDescriptorV1,
    edge: IntentConversionEdgeV1,
) -> IntentCompatibilityResultV1:
    """Fail-closed offline compatibility evaluation for explicit conversion edges."""
    source_digest = compute_intent_type_descriptor_digest(source)
    target_digest = compute_intent_type_descriptor_digest(target)
    edge_digest = compute_intent_conversion_edge_digest(edge)

    known_ids = frozenset(INTENT_TYPE_DESCRIPTOR_REGISTRY_V1.keys())
    reason_codes: list[str] = []

    if source.intent_type_id not in known_ids or target.intent_type_id not in known_ids:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_UNKNOWN_INTENT_TYPE.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_UNKNOWN_INTENT_TYPE,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if edge.conversion_kind not in _EXPLICIT_CONVERSION_KINDS:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if edge.conversion_kind == "EXPLICIT_ADAPTER" and not edge.explicit_adapter_id.strip():
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if edge.conversion_kind == "EXPLICIT_POLICY" and not edge.explicit_policy_id.strip():
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if (
        edge.source_intent_type_id != source.intent_type_id
        or edge.target_intent_type_id != target.intent_type_id
    ):
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if _non_futures_descriptor(source) or _non_futures_descriptor(target):
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_NON_FUTURES_INTENT.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_NON_FUTURES_INTENT,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if _bitcoin_direction_descriptor(source) or _bitcoin_direction_descriptor(target):
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_BITCOIN_SPECIFIC_DIRECTION.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_BITCOIN_SPECIFIC_DIRECTION,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if not _canonical_bindings_present(target):
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_MISSING_CANONICAL_BINDING.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_MISSING_CANONICAL_BINDING,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if not edge.preserves_quantity_semantics or not _quantity_semantics_compatible(source, target):
        if not _quantity_semantics_compatible(source, target):
            reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_QUANTITY_SEMANTICS.value)
        else:
            reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_QUANTITY_SEMANTICS.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_QUANTITY_SEMANTICS,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if not source.quantity_provenance_present or not target.quantity_provenance_present:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_QUANTITY_PROVENANCE.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_QUANTITY_PROVENANCE,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if not edge.preserves_side_semantics or not _side_semantics_compatible(source, target):
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_SIDE_SEMANTICS.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_SIDE_SEMANTICS,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if not edge.preserves_reduce_only_semantics:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_REDUCE_ONLY_SEMANTICS.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_REDUCE_ONLY_SEMANTICS,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if not edge.preserves_instrument_binding or not target.instrument_binding_present:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_INSTRUMENT_BINDING.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_INSTRUMENT_BINDING,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if not edge.preserves_venue_binding or not target.venue_binding_present:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_VENUE_BINDING.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_VENUE_BINDING,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if not edge.preserves_account_binding or not target.account_binding_present:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_ACCOUNT_BINDING.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_ACCOUNT_BINDING,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if (
        not edge.preserves_identity_binding
        or not target.intent_id_binding_present
        or not target.client_order_id_binding_present
    ):
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_IDENTITY_BINDING.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_IDENTITY_BINDING,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if (
        not edge.preserves_authority_binding
        or not target.authority_binding_present
        or not target.permission_binding_present
    ):
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_AUTHORITY_BINDING.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_AUTHORITY_BINDING,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if source.runtime_effect or target.runtime_effect:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_RUNTIME_EFFECT.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_RUNTIME_EFFECT,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if source.order_effect or target.order_effect:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_ORDER_EFFECT.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_ORDER_EFFECT,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    if source.adapter_submission_effect or target.adapter_submission_effect:
        reason_codes.append(IntentCompatibilityVerdictV1.BLOCKED_ADAPTER_SUBMISSION_EFFECT.value)
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_ADAPTER_SUBMISSION_EFFECT,
            reason_codes=reason_codes,
            source_digest=source_digest,
            target_digest=target_digest,
            edge_digest=edge_digest,
        )

    reason_codes.append(IntentCompatibilityVerdictV1.ADMISSIBLE.value)
    return _result(
        verdict=IntentCompatibilityVerdictV1.ADMISSIBLE,
        reason_codes=reason_codes,
        source_digest=source_digest,
        target_digest=target_digest,
        edge_digest=edge_digest,
    )


def _descriptor(**overrides: object) -> IntentTypeDescriptorV1:
    base: dict[str, object] = {
        "intent_type_id": "UNSET",
        "owner_module": "unset",
        "producer_domain": "execution.futures",
        "consumer_domain": "offline.evaluation",
        "persistence_lifecycle": "ephemeral",
        "quantity_semantics": "decimal",
        "side_semantics": "BUY_SELL",
        "reduce_only_semantics": "absent",
        "instrument_binding_present": False,
        "venue_binding_present": False,
        "account_binding_present": False,
        "trading_epoch_binding_present": False,
        "intent_id_binding_present": False,
        "client_order_id_binding_present": False,
        "authority_binding_present": False,
        "permission_binding_present": False,
        "quantity_provenance_present": False,
        "canonical_identity_compatible": False,
        "runtime_effect": False,
        "order_effect": False,
        "adapter_submission_effect": False,
        "semantic_digest": "",
    }
    base.update(overrides)
    descriptor = IntentTypeDescriptorV1(**base)  # type: ignore[arg-type]
    return with_computed_descriptor_digest(descriptor)


INTENT_TYPE_DESCRIPTOR_REGISTRY_V1: dict[str, IntentTypeDescriptorV1] = {
    "ORCHESTRATOR_ORDER_INTENT": _descriptor(
        intent_type_id="ORCHESTRATOR_ORDER_INTENT",
        owner_module="src.execution.orchestrator",
        producer_domain="execution.orchestrator",
        consumer_domain="execution.pipeline",
        persistence_lifecycle="ephemeral_in_memory",
        quantity_semantics="decimal",
        side_semantics="BUY_SELL",
        reduce_only_semantics="absent",
        intent_id_binding_present=True,
        quantity_provenance_present=True,
    ),
    "PIPELINE_ORDER_INTENT": _descriptor(
        intent_type_id="PIPELINE_ORDER_INTENT",
        owner_module="src.execution.pipeline",
        producer_domain="execution.pipeline",
        consumer_domain="execution.orders",
        persistence_lifecycle="ephemeral",
        quantity_semantics="float",
        side_semantics="buy_sell",
        reduce_only_semantics="absent",
        quantity_provenance_present=False,
    ),
    "EXECUTION_SIMPLE_ORDER_INTENT": _descriptor(
        intent_type_id="EXECUTION_SIMPLE_ORDER_INTENT",
        owner_module="src.execution_simple.types",
        producer_domain="execution_simple.pipeline",
        consumer_domain="execution_simple.gates",
        persistence_lifecycle="ephemeral",
        quantity_semantics="float",
        side_semantics="buy_sell",
        reduce_only_semantics="absent",
    ),
    "ADAPTER_ORDER_INTENT_V1": _descriptor(
        intent_type_id="ADAPTER_ORDER_INTENT_V1",
        owner_module="src.execution.adapters.base_v1",
        producer_domain="execution.adapter_v1",
        consumer_domain="execution.adapter_v1",
        persistence_lifecycle="ephemeral",
        quantity_semantics="float",
        side_semantics="buy_sell",
        reduce_only_semantics="present",
        client_order_id_binding_present=True,
        adapter_submission_effect=True,
    ),
    "ORDER_REQUEST": _descriptor(
        intent_type_id="ORDER_REQUEST",
        owner_module="src.orders.base",
        producer_domain="execution.orders",
        consumer_domain="execution.executors",
        persistence_lifecycle="request_result",
        quantity_semantics="float",
        side_semantics="buy_sell",
        reduce_only_semantics="absent",
        order_effect=True,
    ),
    "LIVE_ORDER_REQUEST": _descriptor(
        intent_type_id="LIVE_ORDER_REQUEST",
        owner_module="src.live.orders",
        producer_domain="execution.live_paper",
        consumer_domain="execution.live_broker",
        persistence_lifecycle="optional_csv",
        quantity_semantics="float",
        side_semantics="BUY_SELL",
        reduce_only_semantics="absent",
        client_order_id_binding_present=True,
        order_effect=True,
    ),
    "EXECUTION_CONTRACTS_ORDER": _descriptor(
        intent_type_id="EXECUTION_CONTRACTS_ORDER",
        owner_module="src.execution.contracts",
        producer_domain="execution.foundation",
        consumer_domain="execution.adapters",
        persistence_lifecycle="ledger_backed",
        quantity_semantics="decimal",
        side_semantics="BUY_SELL",
        reduce_only_semantics="absent",
        client_order_id_binding_present=True,
        order_effect=True,
    ),
    "CANONICAL_ORDER_INTENT_V1": _descriptor(
        intent_type_id="CANONICAL_ORDER_INTENT_V1",
        owner_module=CANONICAL_ORDER_INTENT_OWNER_MODULE,
        producer_domain="governance.canonical_order_intent",
        consumer_domain="governance.offline_transformation",
        persistence_lifecycle="durable_evidence",
        quantity_semantics="decimal",
        side_semantics="LONG_SHORT",
        reduce_only_semantics="present",
        instrument_binding_present=True,
        trading_epoch_binding_present=True,
        intent_id_binding_present=True,
        quantity_provenance_present=True,
        canonical_identity_compatible=True,
    ),
    "CANONICAL_ORDER_INTENT_IDENTITY": _descriptor(
        intent_type_id="CANONICAL_ORDER_INTENT_IDENTITY",
        owner_module=CANONICAL_IDENTITY_OWNER_MODULE,
        producer_domain="meta.learning_loop.offline",
        consumer_domain="meta.learning_loop.offline",
        persistence_lifecycle="durable_evidence",
        quantity_semantics="digest_bound",
        side_semantics="none",
        reduce_only_semantics="absent",
        instrument_binding_present=True,
        venue_binding_present=True,
        account_binding_present=True,
        trading_epoch_binding_present=True,
        intent_id_binding_present=True,
        client_order_id_binding_present=True,
        authority_binding_present=True,
        permission_binding_present=True,
        quantity_provenance_present=True,
        canonical_identity_compatible=True,
    ),
    "ORDER_CAPABILITY_PAYLOAD": _descriptor(
        intent_type_id="ORDER_CAPABILITY_PAYLOAD",
        owner_module="src.ops.order_capability_payload_builder_contract_v1",
        producer_domain="ops.bounded_testnet",
        consumer_domain="ops.bounded_testnet",
        persistence_lifecycle="serialized_payload",
        quantity_semantics="float",
        side_semantics="buy_sell",
        reduce_only_semantics="present",
        instrument_binding_present=True,
        venue_binding_present=True,
        authority_binding_present=True,
        permission_binding_present=True,
        quantity_provenance_present=True,
    ),
    "CANONICAL_TRADING_DECISION_EVIDENCE_V1": _descriptor(
        intent_type_id="CANONICAL_TRADING_DECISION_EVIDENCE_V1",
        owner_module="src.trading.master_v2.canonical_trading_decision_evidence_v1",
        producer_domain="trading.master_v2.offline_replay",
        consumer_domain="governance.capital_risk_sizing",
        persistence_lifecycle="durable_evidence",
        quantity_semantics="absent",
        side_semantics="LONG_SHORT",
        reduce_only_semantics="absent",
        instrument_binding_present=True,
        trading_epoch_binding_present=True,
        quantity_provenance_present=False,
    ),
    "PRE_SIZING_RISK_RESULT_V1": _descriptor(
        intent_type_id="PRE_SIZING_RISK_RESULT_V1",
        owner_module="src.governance.capital_risk_sizing_v1",
        producer_domain="governance.capital_risk_sizing",
        consumer_domain="governance.capital_risk_sizing",
        persistence_lifecycle="offline_chain",
        quantity_semantics="absent",
        side_semantics="none",
        reduce_only_semantics="absent",
        quantity_provenance_present=False,
    ),
    "CANONICAL_SIZING_RESULT_V1": _descriptor(
        intent_type_id="CANONICAL_SIZING_RESULT_V1",
        owner_module="src.governance.capital_risk_sizing_v1",
        producer_domain="governance.capital_risk_sizing",
        consumer_domain="governance.capital_risk_sizing",
        persistence_lifecycle="offline_chain",
        quantity_semantics="decimal",
        side_semantics="none",
        reduce_only_semantics="absent",
        quantity_provenance_present=False,
    ),
    "POST_SIZING_RISK_RESULT_V1": _descriptor(
        intent_type_id="POST_SIZING_RISK_RESULT_V1",
        owner_module="src.governance.capital_risk_sizing_v1",
        producer_domain="governance.capital_risk_sizing",
        consumer_domain="governance.capital_risk_sizing",
        persistence_lifecycle="offline_chain",
        quantity_semantics="absent",
        side_semantics="none",
        reduce_only_semantics="absent",
        quantity_provenance_present=False,
    ),
    "CAPITAL_RISK_SIZING_DECISION_V1": _descriptor(
        intent_type_id="CAPITAL_RISK_SIZING_DECISION_V1",
        owner_module="src.governance.capital_risk_sizing_v1",
        producer_domain="governance.capital_risk_sizing",
        consumer_domain="governance.canonical_order_intent",
        persistence_lifecycle="offline_chain",
        quantity_semantics="decimal",
        side_semantics="LONG_SHORT",
        reduce_only_semantics="absent",
        instrument_binding_present=True,
        quantity_provenance_present=True,
    ),
    "EXECUTION_RISK_RESULT": _descriptor(
        intent_type_id="EXECUTION_RISK_RESULT",
        owner_module="src.execution.contracts",
        producer_domain="execution.risk_hook",
        consumer_domain="execution.orchestrator",
        persistence_lifecycle="ephemeral",
        quantity_semantics="absent",
        side_semantics="none",
        reduce_only_semantics="absent",
        quantity_provenance_present=False,
    ),
}


CONTRACT_TYPE_REGISTRY_V1: dict[tuple[str, str], ContractTypeRegistryEntryV1] = {
    (
        "canonical_trading_decision_evidence_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="canonical_trading_decision_evidence_v1",
        contract_version="v1",
        owner_module="src.trading.master_v2.canonical_trading_decision_evidence_v1",
        classification=ContractTypeClassification.CANONICAL_DECISION,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "capital_envelope_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="capital_envelope_v1",
        contract_version="v1",
        owner_module="src.governance.capital_risk_sizing_v1",
        classification=ContractTypeClassification.CAPITAL_ENVELOPE,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "pre_sizing_risk_result_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="pre_sizing_risk_result_v1",
        contract_version="v1",
        owner_module="src.governance.capital_risk_sizing_v1",
        classification=ContractTypeClassification.PRE_SIZING_RISK,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "canonical_sizing_result_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="canonical_sizing_result_v1",
        contract_version="v1",
        owner_module="src.governance.capital_risk_sizing_v1",
        classification=ContractTypeClassification.SIZING_RESULT,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "post_sizing_risk_result_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="post_sizing_risk_result_v1",
        contract_version="v1",
        owner_module="src.governance.capital_risk_sizing_v1",
        classification=ContractTypeClassification.POST_SIZING_RISK,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "capital_risk_sizing_decision_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="capital_risk_sizing_decision_v1",
        contract_version="v1",
        owner_module="src.governance.capital_risk_sizing_v1",
        classification=ContractTypeClassification.SIZING_RESULT,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "canonical_order_intent_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="canonical_order_intent_v1",
        contract_version="v1",
        owner_module=CANONICAL_ORDER_INTENT_OWNER_MODULE,
        classification=ContractTypeClassification.CANONICAL_ORDER_INTENT,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "execution_permission_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="execution_permission_v1",
        contract_version="v1",
        owner_module="src.meta.learning_loop.canonical_order_lifecycle_v1",
        classification=ContractTypeClassification.EXECUTION_PERMISSION,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "adapter_order_intent_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="adapter_order_intent_v1",
        contract_version="v1",
        owner_module="src.execution.adapters.base_v1",
        classification=ContractTypeClassification.ADAPTER_PAYLOAD,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "orchestrator_order_intent",
        "legacy",
    ): ContractTypeRegistryEntryV1(
        contract_type="orchestrator_order_intent",
        contract_version="legacy",
        owner_module="src.execution.orchestrator",
        classification=ContractTypeClassification.LEGACY_OR_AMBIGUOUS,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "adapter_order_intent_v1",
        "legacy_alias",
    ): ContractTypeRegistryEntryV1(
        contract_type="adapter_order_intent_v1",
        contract_version="legacy_alias",
        owner_module="src.execution.adapters.base_v1",
        classification=ContractTypeClassification.LEGACY_OR_AMBIGUOUS,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
    (
        "boundary_fully_bound_canonical_order_intent_with_permission_v1",
        "v1",
    ): ContractTypeRegistryEntryV1(
        contract_type="boundary_fully_bound_canonical_order_intent_with_permission_v1",
        contract_version="v1",
        owner_module=CANONICAL_ORDER_INTENT_OWNER_MODULE,
        classification=ContractTypeClassification.BOUNDARY_FIXTURE,
        adapter_compatible_by_default=False,
        transformation_required_for_adapter=True,
    ),
}


TRANSFORMATION_REGISTRY_V1: dict[str, IntentTransformationDescriptorV1] = {
    CANONICAL_TO_ADAPTER_TRANSFORMATION_ID: IntentTransformationDescriptorV1(
        source_contract="canonical_order_intent_v1",
        source_version="v1",
        target_contract="adapter_order_intent_v1",
        target_version="v1",
        transformation_id=CANONICAL_TO_ADAPTER_TRANSFORMATION_ID,
        transformation_version=CANONICAL_TO_ADAPTER_TRANSFORMATION_VERSION,
        field_mapping_version=CANONICAL_TO_ADAPTER_FIELD_MAPPING_VERSION,
        source_digest="",
        target_digest="",
        lossless_fields=(),
        rejected_unbound_fields=(
            "quantity",
            "order_type",
            "reduce_only",
            "venue_id",
            "account_id",
            "instrument_id",
            "position_mode",
            "margin_mode",
            "policy_digest",
            "config_digest",
            "implementation_digest",
            "permission_id",
            "authority_lease",
            "fencing_token",
        ),
        runtime_effect=False,
        order_effect=False,
        authority_effect=False,
        network_effect=False,
        adapter_submission_effect=False,
    ),
}


def compute_intent_compatibility_assessment_digest(
    assessment: IntentCompatibilityAssessmentV1,
) -> str:
    payload = {
        field.name: getattr(assessment, field.name)
        for field in fields(IntentCompatibilityAssessmentV1)
        if field.name != "assessment_digest"
    }
    payload["compatibility_status"] = assessment.compatibility_status.value
    return _sha256_hex(payload)


def with_computed_assessment_digest(
    assessment: IntentCompatibilityAssessmentV1,
) -> IntentCompatibilityAssessmentV1:
    digest = compute_intent_compatibility_assessment_digest(assessment)
    if assessment.assessment_digest == digest:
        return assessment
    return IntentCompatibilityAssessmentV1(
        **{
            **{
                field.name: getattr(assessment, field.name)
                for field in fields(IntentCompatibilityAssessmentV1)
            },
            "assessment_digest": digest,
        }
    )


def _assessment_result(
    *,
    source_type: str,
    source_version: str,
    target_type: str,
    target_version: str,
    status: ContractCompatibilityStatusV1,
    transformation_required: bool,
    bindings: ContractBindingSnapshotV1,
    adapter_compatible: bool,
    reason_codes: Sequence[str],
) -> IntentCompatibilityAssessmentV1:
    sorted_reasons = tuple(sorted(set(reason_codes)))
    assessment = IntentCompatibilityAssessmentV1(
        source_contract_type=source_type,
        source_contract_version=source_version,
        target_contract_type=target_type,
        target_contract_version=target_version,
        compatibility_status=status,
        transformation_required=transformation_required,
        quantity_bound=bindings.quantity_bound,
        order_type_bound=bindings.order_type_bound,
        reduce_only_bound=bindings.reduce_only_bound,
        venue_bound=bindings.venue_bound,
        account_bound=bindings.account_bound,
        instrument_bound=bindings.instrument_bound,
        risk_provenance_bound=bindings.risk_provenance_bound,
        policy_digest_bound=bindings.policy_digest_bound,
        config_digest_bound=bindings.config_digest_bound,
        implementation_digest_bound=bindings.implementation_digest_bound,
        permission_bound=bindings.permission_bound,
        authority_bound=bindings.authority_bound,
        adapter_compatible=adapter_compatible,
        reason_codes=sorted_reasons,
        authority_effect=AUTHORITY_EFFECT_NONE,
        runtime_effect=RUNTIME_EFFECT_NONE,
    )
    return with_computed_assessment_digest(assessment)


def _binding_failures(bindings: ContractBindingSnapshotV1) -> list[str]:
    failures: list[str] = []
    if not bindings.quantity_bound:
        failures.append(REASON_MISSING_QUANTITY_BINDING)
    if not bindings.quantity_provenance_bound:
        failures.append(REASON_MISSING_QUANTITY_PROVENANCE_BINDING)
    if not bindings.order_type_bound:
        failures.append(REASON_MISSING_ORDER_TYPE_BINDING)
    if not bindings.reduce_only_bound:
        failures.append(REASON_MISSING_REDUCE_ONLY_BINDING)
    if not bindings.venue_bound:
        failures.append(REASON_MISSING_VENUE_BINDING)
    if not bindings.account_bound:
        failures.append(REASON_MISSING_ACCOUNT_BINDING)
    if not bindings.instrument_bound:
        failures.append(REASON_MISSING_INSTRUMENT_BINDING)
    if not bindings.policy_digest_bound:
        failures.append(REASON_MISSING_POLICY_DIGEST_BINDING)
    if not bindings.config_digest_bound:
        failures.append(REASON_MISSING_CONFIG_DIGEST_BINDING)
    if not bindings.implementation_digest_bound:
        failures.append(REASON_MISSING_IMPLEMENTATION_DIGEST_BINDING)
    if not bindings.permission_bound:
        failures.append(REASON_MISSING_PERMISSION_BINDING)
    if not bindings.authority_bound:
        failures.append(REASON_MISSING_AUTHORITY_LEASE_BINDING)
    if not bindings.fencing_token_bound:
        failures.append(REASON_MISSING_FENCING_TOKEN_BINDING)
    return failures


def evaluate_contract_compatibility_v1(
    *,
    source_contract_type: str,
    source_contract_version: str,
    bindings: ContractBindingSnapshotV1,
    target_contract_type: str = "adapter_order_intent_v1",
    target_contract_version: str = "v1",
    transformation_id: str = "",
) -> IntentCompatibilityAssessmentV1:
    """Fail-closed contract-level compatibility assessment (STEP 29O offline slice)."""

    source_key = (source_contract_type.strip().lower(), source_contract_version.strip().lower())
    target_key = (target_contract_type.strip().lower(), target_contract_version.strip().lower())

    if source_key not in CONTRACT_TYPE_REGISTRY_V1:
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.INCOMPATIBLE,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[REASON_UNKNOWN_SOURCE_CONTRACT],
        )

    if target_key not in CONTRACT_TYPE_REGISTRY_V1:
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.INCOMPATIBLE,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[REASON_UNKNOWN_TARGET_CONTRACT],
        )

    source_entry = CONTRACT_TYPE_REGISTRY_V1[source_key]
    target_entry = CONTRACT_TYPE_REGISTRY_V1[target_key]

    if bindings.spot_market or bindings.synthetic_spot_market or not bindings.futures_only:
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.INCOMPATIBLE,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[REASON_NON_FUTURES_CONTRACT],
        )

    if bindings.bitcoin_direction:
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.INCOMPATIBLE,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[REASON_BITCOIN_DIRECTION_FORBIDDEN],
        )

    if bindings.legacy_alias:
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.INCOMPATIBLE,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[REASON_LEGACY_ALIAS_WITHOUT_TRANSFORMATION],
        )

    if bindings.duck_typed_order_fields and source_entry.classification in {
        ContractTypeClassification.CANONICAL_DECISION,
        ContractTypeClassification.LEGACY_OR_AMBIGUOUS,
    }:
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.INCOMPATIBLE,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[
                REASON_DUCK_TYPING_FIELD_MATCH_INSUFFICIENT,
                REASON_IMPLICIT_CONVERSION_FORBIDDEN,
            ],
        )

    if source_entry.classification == ContractTypeClassification.CANONICAL_DECISION:
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.TRANSFORMATION_REQUIRED,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[
                REASON_CANONICAL_DECISION_NOT_ORDER_INTENT,
                REASON_TRANSFORMATION_REQUIRED_NO_DEFAULTS,
                REASON_STEP29O_ADAPTER_COMPATIBILITY_BLOCKED,
            ],
        )

    if source_entry.classification in {
        ContractTypeClassification.PRE_SIZING_RISK,
        ContractTypeClassification.POST_SIZING_RISK,
    }:
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.INCOMPATIBLE,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[
                REASON_RISK_OUTPUT_NOT_ADAPTER_COMPATIBLE,
                REASON_STEP29O_ADAPTER_COMPATIBILITY_BLOCKED,
            ],
        )

    if source_entry.classification in {
        ContractTypeClassification.SIZING_RESULT,
        ContractTypeClassification.CAPITAL_ENVELOPE,
    }:
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.TRANSFORMATION_REQUIRED,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[
                REASON_SIZING_OUTPUT_NOT_ADAPTER_COMPATIBLE,
                REASON_CANONICAL_ORDER_INTENT_REQUIRED,
                REASON_STEP29O_ADAPTER_COMPATIBILITY_BLOCKED,
            ],
        )

    if source_entry.classification == ContractTypeClassification.LEGACY_OR_AMBIGUOUS:
        if not transformation_id or transformation_id not in TRANSFORMATION_REGISTRY_V1:
            return _assessment_result(
                source_type=source_contract_type,
                source_version=source_contract_version,
                target_type=target_contract_type,
                target_version=target_contract_version,
                status=ContractCompatibilityStatusV1.INCOMPATIBLE,
                transformation_required=True,
                bindings=bindings,
                adapter_compatible=False,
                reason_codes=[
                    REASON_LEGACY_ALIAS_WITHOUT_TRANSFORMATION,
                    REASON_IMPLICIT_CONVERSION_FORBIDDEN,
                ],
            )

    if source_entry.classification == ContractTypeClassification.CANONICAL_ORDER_INTENT:
        binding_failures = _binding_failures(bindings)
        if binding_failures:
            return _assessment_result(
                source_type=source_contract_type,
                source_version=source_contract_version,
                target_type=target_contract_type,
                target_version=target_contract_version,
                status=ContractCompatibilityStatusV1.PERMISSION_REQUIRED,
                transformation_required=True,
                bindings=bindings,
                adapter_compatible=False,
                reason_codes=binding_failures + [REASON_STEP29O_ADAPTER_COMPATIBILITY_BLOCKED],
            )
        if not transformation_id or transformation_id not in TRANSFORMATION_REGISTRY_V1:
            return _assessment_result(
                source_type=source_contract_type,
                source_version=source_contract_version,
                target_type=target_contract_type,
                target_version=target_contract_version,
                status=ContractCompatibilityStatusV1.TRANSFORMATION_REQUIRED,
                transformation_required=True,
                bindings=bindings,
                adapter_compatible=False,
                reason_codes=[
                    REASON_TRANSFORMATION_REQUIRED_NO_DEFAULTS,
                    REASON_STEP29O_ADAPTER_COMPATIBILITY_BLOCKED,
                ],
            )
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.PERMISSION_REQUIRED,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[REASON_STEP29O_ADAPTER_COMPATIBILITY_BLOCKED],
        )

    if source_entry.classification == ContractTypeClassification.BOUNDARY_FIXTURE:
        binding_failures = _binding_failures(bindings)
        if binding_failures:
            return _assessment_result(
                source_type=source_contract_type,
                source_version=source_contract_version,
                target_type=target_contract_type,
                target_version=target_contract_version,
                status=ContractCompatibilityStatusV1.INCOMPATIBLE,
                transformation_required=True,
                bindings=bindings,
                adapter_compatible=False,
                reason_codes=binding_failures,
            )
        return _assessment_result(
            source_type=source_contract_type,
            source_version=source_contract_version,
            target_type=target_contract_type,
            target_version=target_contract_version,
            status=ContractCompatibilityStatusV1.STRUCTURALLY_COMPATIBLE_NOT_EXECUTION_ELIGIBLE,
            transformation_required=True,
            bindings=bindings,
            adapter_compatible=False,
            reason_codes=[
                REASON_BOUNDARY_STRUCTURAL_ONLY,
                REASON_STEP29O_ADAPTER_COMPATIBILITY_BLOCKED,
            ],
        )

    return _assessment_result(
        source_type=source_contract_type,
        source_version=source_contract_version,
        target_type=target_contract_type,
        target_version=target_contract_version,
        status=ContractCompatibilityStatusV1.INCOMPATIBLE,
        transformation_required=True,
        bindings=bindings,
        adapter_compatible=False,
        reason_codes=[
            REASON_IMPLICIT_CONVERSION_FORBIDDEN,
            REASON_STEP29O_ADAPTER_COMPATIBILITY_BLOCKED,
        ],
    )


def assert_not_adapter_compatible_contract_v1(
    *,
    source_contract_type: str,
    source_contract_version: str,
    bindings: ContractBindingSnapshotV1 | None = None,
) -> IntentCompatibilityAssessmentV1:
    """Negative guard for execution/adapter consumers (offline contract slice)."""

    assessment = evaluate_contract_compatibility_v1(
        source_contract_type=source_contract_type,
        source_contract_version=source_contract_version,
        bindings=bindings or ContractBindingSnapshotV1(),
    )
    if assessment.adapter_compatible:
        msg = f"adapter_compatible forbidden for {source_contract_type}::{source_contract_version}"
        raise ValueError(msg)
    return assessment


def producer_consumer_authority_matrix_v1() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for (_ctype, _cver), entry in sorted(CONTRACT_TYPE_REGISTRY_V1.items()):
        rows.append(
            {
                "contract_type": entry.contract_type,
                "contract_version": entry.contract_version,
                "classification": entry.classification.value,
                "owner_module": entry.owner_module,
                "producer_authority": AUTHORITY_EFFECT_NONE,
                "consumer_authority": AUTHORITY_EFFECT_NONE,
                "runtime_effect": RUNTIME_EFFECT_NONE,
                "adapter_compatible_by_default": str(entry.adapter_compatible_by_default).lower(),
            }
        )
    return rows


def bypass_scan_results_v1() -> list[dict[str, str]]:
    return [
        {
            "path_id": "decision_to_adapter_direct",
            "description": "CanonicalTradingDecisionEvidenceV1 -> adapter payload",
            "classification": "CLOSED_IN_SCOPE",
            "owner": "src.governance.intent_compatibility_firewall_v1",
        },
        {
            "path_id": "strategy_signal_to_order_direct",
            "description": "Strategy signal -> OrderIntent without pipeline",
            "classification": "ALREADY_GUARDED",
            "owner": "src.execution.orchestrator",
        },
        {
            "path_id": "sizing_to_adapter_direct",
            "description": "CapitalRiskSizingDecisionV1 -> adapter payload",
            "classification": "CLOSED_IN_SCOPE",
            "owner": "src.governance.intent_compatibility_firewall_v1",
        },
        {
            "path_id": "dict_mapping_bypass",
            "description": "Dict duck-typing with order-like fields",
            "classification": "CLOSED_IN_SCOPE",
            "owner": "src.governance.intent_compatibility_firewall_v1",
        },
        {
            "path_id": "implicit_default_order_type",
            "description": "Default order_type without explicit binding",
            "classification": "CLOSED_IN_SCOPE",
            "owner": "src.governance.intent_compatibility_firewall_v1",
        },
        {
            "path_id": "canonical_order_intent_to_adapter",
            "description": "Canonical order intent -> adapter with explicit transformation",
            "classification": "DEFERRED_TO_STEP29Q",
            "owner": "src.governance.canonical_order_intent_v1",
        },
        {
            "path_id": "runtime_eligibility_generation",
            "description": "Runtime eligibility from offline contracts",
            "classification": "DEFERRED_TO_STEP29R",
            "owner": "src.meta.learning_loop.canonical_order_lifecycle_v1",
        },
        {
            "path_id": "authority_lease_issuance",
            "description": "Authority lease from compatibility assessment",
            "classification": "DEFERRED_TO_STEP29R",
            "owner": "src.meta.learning_loop.canonical_order_lifecycle_v1",
        },
    ]


def deferred_scope_mapping_v1() -> dict[str, str]:
    return {
        "canonical_order_intent_full_implementation": "DEFERRED_TO_STEP29Q",
        "adapter_submission": "DEFERRED_TO_STEP29R",
        "runtime_rewire": "DEFERRED_TO_STEP29R",
        "runtime_eligibility": "DEFERRED_TO_STEP29R",
        "authority_lease": "DEFERRED_TO_STEP29R",
        "capital_risk_sizing_math": "OUT_OF_SCOPE_WITH_EXPLICIT_OWNER",
        "capital_risk_sizing_owner": "src.governance.capital_risk_sizing_v1",
    }


def legacy_intent_classification_v1() -> dict[str, str]:
    return {
        type_id: descriptor.owner_module
        for type_id, descriptor in INTENT_TYPE_DESCRIPTOR_REGISTRY_V1.items()
        if type_id
        in {
            "ORCHESTRATOR_ORDER_INTENT",
            "PIPELINE_ORDER_INTENT",
            "EXECUTION_SIMPLE_ORDER_INTENT",
            "ORDER_REQUEST",
            "LIVE_ORDER_REQUEST",
            "EXECUTION_CONTRACTS_ORDER",
        }
    }


def compatibility_firewall_contract_v1() -> dict[str, object]:
    return {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "compatibility_statuses": [s.value for s in ContractCompatibilityStatusV1],
        "classifications": [c.value for c in ContractTypeClassification],
        "invariants": {
            "canonical_trading_decision_is_not_order_intent": True,
            "risk_or_sizing_output_not_adapter_compatible_by_default": True,
            "no_implicit_decision_to_order_conversion": True,
            "no_implicit_quantity_binding": True,
            "no_implicit_order_type_binding": True,
            "no_implicit_reduce_only_binding": True,
            "no_implicit_venue_binding": True,
            "no_implicit_account_binding": True,
            "no_implicit_authority_binding": True,
            "no_implicit_adapter_compatibility": True,
            "explicit_versioned_transformation_required": True,
            "authority_effect": AUTHORITY_EFFECT_NONE,
            "runtime_effect": RUNTIME_EFFECT_NONE,
            "futures_only": FUTURES_ONLY,
            "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
            "spot_allowed": SPOT_ALLOWED,
            "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        },
    }


def build_canonical_to_adapter_transformation_descriptor_v1(
    *,
    source_digest: str,
    target_digest: str,
    lossless_fields: tuple[str, ...],
    rejected_unbound_fields: tuple[str, ...],
) -> IntentTransformationDescriptorV1:
    return IntentTransformationDescriptorV1(
        source_contract="canonical_order_intent_v1",
        source_version="v1",
        target_contract="adapter_order_intent_v1",
        target_version="v1",
        transformation_id=CANONICAL_TO_ADAPTER_TRANSFORMATION_ID,
        transformation_version=CANONICAL_TO_ADAPTER_TRANSFORMATION_VERSION,
        field_mapping_version=CANONICAL_TO_ADAPTER_FIELD_MAPPING_VERSION,
        source_digest=source_digest,
        target_digest=target_digest,
        lossless_fields=lossless_fields,
        rejected_unbound_fields=rejected_unbound_fields,
        runtime_effect=False,
        order_effect=False,
        authority_effect=False,
        network_effect=False,
        adapter_submission_effect=False,
    )


def evaluate_explicit_canonical_to_adapter_transformation_firewall_v1(
    *,
    source_digest: str,
    target_digest: str,
    transformation_id: str,
) -> IntentCompatibilityResultV1:
    """Fail-closed offline guard for explicit canonical-to-adapter transformation only."""

    source = INTENT_TYPE_DESCRIPTOR_REGISTRY_V1["CANONICAL_ORDER_INTENT_V1"]
    target = INTENT_TYPE_DESCRIPTOR_REGISTRY_V1["ADAPTER_ORDER_INTENT_V1"]
    edge = with_computed_conversion_edge_digest(
        IntentConversionEdgeV1(
            source_intent_type_id="CANONICAL_ORDER_INTENT_V1",
            target_intent_type_id="ADAPTER_ORDER_INTENT_V1",
            conversion_kind="EXPLICIT_ADAPTER",
            explicit_adapter_id=transformation_id,
            explicit_policy_id="",
            preserves_quantity_semantics=False,
            preserves_side_semantics=False,
            preserves_reduce_only_semantics=True,
            preserves_instrument_binding=True,
            preserves_venue_binding=False,
            preserves_account_binding=False,
            preserves_identity_binding=False,
            preserves_authority_binding=False,
            semantic_digest="",
        )
    )
    source_digest_computed = compute_intent_type_descriptor_digest(source)
    target_digest_computed = compute_intent_type_descriptor_digest(target)
    edge_digest = compute_intent_conversion_edge_digest(edge)

    if transformation_id != CANONICAL_TO_ADAPTER_TRANSFORMATION_ID:
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION,
            reason_codes=[IntentCompatibilityVerdictV1.BLOCKED_IMPLICIT_CONVERSION.value],
            source_digest=source_digest_computed,
            target_digest=target_digest_computed,
            edge_digest=edge_digest,
        )

    if not source_digest or not target_digest:
        return _result(
            verdict=IntentCompatibilityVerdictV1.BLOCKED_QUANTITY_PROVENANCE,
            reason_codes=[IntentCompatibilityVerdictV1.BLOCKED_QUANTITY_PROVENANCE.value],
            source_digest=source_digest_computed,
            target_digest=target_digest_computed,
            edge_digest=edge_digest,
        )

    return _result(
        verdict=IntentCompatibilityVerdictV1.ADMISSIBLE,
        reason_codes=[IntentCompatibilityVerdictV1.ADMISSIBLE.value],
        source_digest=source_digest_computed,
        target_digest=target_digest_computed,
        edge_digest=edge_digest,
    )


def intent_compatibility_firewall_schema_v1() -> dict[str, object]:
    return {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "canonical_identity_reference": CANONICAL_IDENTITY_REFERENCE,
        "referenced_owners": {
            "canonical_order_intent_v1": CANONICAL_ORDER_INTENT_OWNER_MODULE,
            "canonical_order_intent_identity": CANONICAL_IDENTITY_OWNER_MODULE,
            "order_intent_idempotency_v1": ORDER_INTENT_IDEMPOTENCY_OWNER_MODULE,
            "canonical_order_lifecycle_v1": CANONICAL_ORDER_LIFECYCLE_OWNER_MODULE,
            "trading_core_decision_attestation_v1": TRADING_CORE_DECISION_ATTESTATION_OWNER_MODULE,
        },
        "verdicts": [v.value for v in IntentCompatibilityVerdictV1],
        "invariants": {
            "implicit_intent_conversion_allowed": IMPLICIT_INTENT_CONVERSION_ALLOWED,
            "futures_only": FUTURES_ONLY,
            "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
            "spot_allowed": SPOT_ALLOWED,
            "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
            "runtime_effect": _RUNTIME_EFFECT,
            "order_effect": _ORDER_EFFECT,
            "authority_effect": _AUTHORITY_EFFECT,
            "transformation_performed": False,
        },
        "registry_intent_type_ids": sorted(INTENT_TYPE_DESCRIPTOR_REGISTRY_V1.keys()),
        "contract_type_registry_keys": sorted(
            f"{k[0]}::{k[1]}" for k in CONTRACT_TYPE_REGISTRY_V1.keys()
        ),
        "compatibility_statuses": [s.value for s in ContractCompatibilityStatusV1],
        "contract_assessment_invariants": compatibility_firewall_contract_v1()["invariants"],
    }
