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

_AUTHORITY_EFFECT = False
_RUNTIME_EFFECT = False
_ORDER_EFFECT = False

_FORBIDDEN_INSTRUMENT_MARKERS = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_FORBIDDEN_DOMAIN_MARKERS = frozenset({"spot", "synthetic_spot", "synthetic-spot"})
_FORBIDDEN_BITCOIN_MARKERS = frozenset({"btc", "xbt", "bitcoin"})
_EXPLICIT_CONVERSION_KINDS = frozenset(
    {"EXPLICIT_ADAPTER", "EXPLICIT_POLICY", "IDENTITY_NO_CONVERSION"}
)


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
    }
