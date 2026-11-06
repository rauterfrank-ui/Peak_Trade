"""Deterministic adjudication reason codes for P2 Component A runtime."""

from __future__ import annotations

from enum import Enum


class AdjudicationIntakeFailureCodeV1(str, Enum):
    INTAKE_MISSING = "intake_missing"
    INTAKE_MALFORMED = "intake_malformed"
    DELIVERY_ID_MISSING = "delivery_id_missing"
    ENVELOPE_ID_MISSING = "envelope_id_missing"
    PRODUCER_ID_MISSING = "producer_id_missing"
    PRODUCER_VERSION_MISSING = "producer_version_missing"
    EVIDENCE_TYPE_VERSION_MISSING = "evidence_type_version_missing"
    PRODUCER_UNREGISTERED = "producer_unregistered"
    PRODUCER_VERSION_UNREGISTERED = "producer_version_unregistered"
    EVIDENCE_TYPE_VERSION_UNREGISTERED = "evidence_type_version_unregistered"
    PRODUCER_FAMILY_REGISTRY_MISMATCH = "producer_family_registry_mismatch"
    EVIDENCE_KIND_REGISTRY_MISMATCH = "evidence_kind_registry_mismatch"
    INSTRUMENT_BINDING_MISMATCH = "instrument_binding_mismatch"
    EPOCH_BINDING_MISMATCH = "epoch_binding_mismatch"
    EVIDENCE_CONFLICT = "evidence_conflict"
    DUPLICATE_DELIVERY_DIVERGENT = "duplicate_delivery_divergent"
    DEDUP_REPLAY = "dedup_replay"
    LINEAGE_MISSING = "lineage_refs_missing"
