"""Phase 22 — versioned incremental information-set identity (B0–B5; AUTHORITY=NONE).

Research-only classification of which MARKET_CONTEXT families are admissible at each
incremental stage. Does not grant feature admission, promotion, or runtime activation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    CONTEXT_FAMILY_SLOT_SCHEMA,
    CONTRACT_ID,
    CROSS_MARKET_CONTEXT_ONLY,
    ContextFamilyPresence,
    MARKET_CONTEXT_AUTHORITY,
    MICROSTRUCTURE_KIND_PROXY_OHLCV,
    MICROSTRUCTURE_KIND_TRUE_L2,
    N_BARS_BACKBONE_TOKEN,
    SCHEMA_VERSION as MARKET_CONTEXT_SCHEMA_VERSION,
    derive_context_id_v1,
    derive_information_set_ref_v1,
    validate_market_context_v1,
)

INCREMENTAL_INFORMATION_SET_SCHEMA: Final[str] = "incremental_information_set_v1"
BEHAVIOR_CONTRACT_VERSION: Final[str] = "realized_behavior_v1"
CONTEXT_CONTRACT_VERSION: Final[str] = MARKET_CONTEXT_SCHEMA_VERSION

STAGE_B0: Final[str] = "B0"
STAGE_B1: Final[str] = "B1"
STAGE_B2: Final[str] = "B2"
STAGE_B3: Final[str] = "B3"
STAGE_B4: Final[str] = "B4"
STAGE_B5: Final[str] = "B5"

STAGE_CHAIN: Final[tuple[str, ...]] = (STAGE_B0, STAGE_B1, STAGE_B2, STAGE_B3, STAGE_B4, STAGE_B5)

FAMILY_PRICE_STATE: Final[str] = "PRICE_STATE"
FAMILY_FLOW_STATE: Final[str] = "FLOW_STATE"
FAMILY_LIQUIDITY_MICROSTRUCTURE: Final[str] = "LIQUIDITY_MICROSTRUCTURE"
FAMILY_DERIVATIVES_STATE: Final[str] = "DERIVATIVES_STATE"
FAMILY_CROSS_MARKET_STATE: Final[str] = "CROSS_MARKET_STATE"
FAMILY_VOLATILITY_STATE: Final[str] = "VOLATILITY_STATE"

_ALL_FAMILIES: Final[tuple[str, ...]] = (
    FAMILY_PRICE_STATE,
    FAMILY_FLOW_STATE,
    FAMILY_LIQUIDITY_MICROSTRUCTURE,
    FAMILY_DERIVATIVES_STATE,
    FAMILY_CROSS_MARKET_STATE,
    FAMILY_VOLATILITY_STATE,
)

FAMILY_TO_CONTEXT_FIELD: Final[Mapping[str, str]] = MappingProxyType(
    {
        FAMILY_PRICE_STATE: "price_state_ref",
        FAMILY_FLOW_STATE: "flow_state_ref",
        FAMILY_LIQUIDITY_MICROSTRUCTURE: "liquidity_microstructure_state_ref",
        FAMILY_DERIVATIVES_STATE: "derivatives_state_ref",
        FAMILY_CROSS_MARKET_STATE: "cross_market_state_ref",
        FAMILY_VOLATILITY_STATE: "volatility_state_ref",
    }
)

_STAGE_INCLUDED_FAMILIES: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {
        STAGE_B0: frozenset({FAMILY_PRICE_STATE, FAMILY_FLOW_STATE}),
        STAGE_B1: frozenset(
            {FAMILY_PRICE_STATE, FAMILY_FLOW_STATE, FAMILY_LIQUIDITY_MICROSTRUCTURE}
        ),
        STAGE_B2: frozenset(
            {
                FAMILY_PRICE_STATE,
                FAMILY_FLOW_STATE,
                FAMILY_LIQUIDITY_MICROSTRUCTURE,
                FAMILY_DERIVATIVES_STATE,
            }
        ),
        STAGE_B3: frozenset(
            {
                FAMILY_PRICE_STATE,
                FAMILY_FLOW_STATE,
                FAMILY_LIQUIDITY_MICROSTRUCTURE,
                FAMILY_DERIVATIVES_STATE,
                FAMILY_CROSS_MARKET_STATE,
            }
        ),
        STAGE_B4: frozenset(_ALL_FAMILIES),
        STAGE_B5: frozenset(_ALL_FAMILIES),
    }
)

_STAGE_PREDECESSOR: Final[Mapping[str, str | None]] = MappingProxyType(
    {
        STAGE_B0: None,
        STAGE_B1: STAGE_B0,
        STAGE_B2: STAGE_B1,
        STAGE_B3: STAGE_B2,
        STAGE_B4: STAGE_B3,
        STAGE_B5: STAGE_B4,
    }
)

EXCLUDED_MISSING_REASON_PREFIX: Final[str] = "phase_22_stage_excluded"
B5_TRUE_L2_REQUIRED: Final[str] = "B5_REQUIRES_TRUE_L2_NOT_PROXY"


class IncrementalInformationSetError(ValueError):
    """Fail-closed incremental information-set validation."""


class TrueL2AdmissibilityStatus(str, Enum):
    DEFERRED_NOT_CURRENTLY_ADMISSIBLE = "DEFERRED_NOT_CURRENTLY_ADMISSIBLE"
    ADMISSIBLE = "ADMISSIBLE"


def predecessor_stage_id_v1(stage_id: str) -> str | None:
    if stage_id not in _STAGE_PREDECESSOR:
        raise IncrementalInformationSetError("STAGE_ID_UNKNOWN")
    return _STAGE_PREDECESSOR[stage_id]


def included_context_families_v1(stage_id: str) -> frozenset[str]:
    families = _STAGE_INCLUDED_FAMILIES.get(stage_id)
    if families is None:
        raise IncrementalInformationSetError("STAGE_ID_UNKNOWN")
    return families


def excluded_context_families_v1(stage_id: str) -> frozenset[str]:
    return frozenset(set(_ALL_FAMILIES) - set(included_context_families_v1(stage_id)))


def census_true_l2_research_substrate_v1() -> MappingProxyType[str, Any]:
    """Re-census whether CURRENT supports admissible true-L2 incremental research (B5)."""
    return MappingProxyType(
        {
            "true_l2_canonical_facts": "NOT_CURRENT",
            "true_l2_provenance": "NOT_CURRENT",
            "true_l2_replay_coverage": "NOT_CURRENT",
            "research_history_usable": False,
            "b5_status": TrueL2AdmissibilityStatus.DEFERRED_NOT_CURRENTLY_ADMISSIBLE.value,
            "authority": "NONE",
        }
    )


@dataclass(frozen=True)
class IncrementalInformationSetRequestV1:
    stage_id: str
    horizon_identity: Mapping[str, Any]
    feature_versions: Mapping[str, str]
    provenance_refs: Sequence[str]
    behavior_contract_version: str = BEHAVIOR_CONTRACT_VERSION
    context_contract_version: str = CONTEXT_CONTRACT_VERSION
    microstructure_kind: str | None = None


def derive_information_set_id_v1(*, identity_body: Mapping[str, Any]) -> str:
    digest = compute_content_hash_v0(dict(identity_body))
    return f"mi.phase22.info_set.{digest[:48]}"


def build_incremental_information_set_v1(
    request: IncrementalInformationSetRequestV1,
) -> MappingProxyType[str, Any]:
    stage_id = request.stage_id
    if stage_id not in _STAGE_INCLUDED_FAMILIES:
        raise IncrementalInformationSetError("STAGE_ID_UNKNOWN")

    predecessor = predecessor_stage_id_v1(stage_id)
    included = sorted(included_context_families_v1(stage_id))
    excluded = sorted(excluded_context_families_v1(stage_id))

    if stage_id == STAGE_B5:
        census = census_true_l2_research_substrate_v1()
        if census["b5_status"] != TrueL2AdmissibilityStatus.ADMISSIBLE.value:
            body = {
                "schema_version": INCREMENTAL_INFORMATION_SET_SCHEMA,
                "stage_id": stage_id,
                "predecessor_stage_id": predecessor,
                "included_context_families": included,
                "excluded_context_families": excluded,
                "feature_versions": dict(request.feature_versions),
                "context_contract_version": request.context_contract_version,
                "behavior_contract_version": request.behavior_contract_version,
                "horizon_identity": dict(request.horizon_identity),
                "provenance_refs": list(request.provenance_refs),
                "microstructure_kind": request.microstructure_kind,
                "b5_status": census["b5_status"],
                "research_authority": "NONE",
            }
            info_id = derive_information_set_id_v1(identity_body=body)
            digest = compute_content_hash_v0({**body, "information_set_id": info_id})
            return MappingProxyType(
                {**body, "information_set_id": info_id, "content_digest": digest}
            )

    identity_body = {
        "schema_version": INCREMENTAL_INFORMATION_SET_SCHEMA,
        "stage_id": stage_id,
        "predecessor_stage_id": predecessor,
        "included_context_families": included,
        "excluded_context_families": excluded,
        "feature_versions": dict(request.feature_versions),
        "context_contract_version": request.context_contract_version,
        "behavior_contract_version": request.behavior_contract_version,
        "horizon_identity": dict(request.horizon_identity),
        "provenance_refs": list(request.provenance_refs),
        "microstructure_kind": request.microstructure_kind,
        "research_authority": "NONE",
    }
    info_id = derive_information_set_id_v1(identity_body=identity_body)
    digest = compute_content_hash_v0({**identity_body, "information_set_id": info_id})
    return MappingProxyType(
        {**identity_body, "information_set_id": info_id, "content_digest": digest}
    )


def _slot_presence(context: Mapping[str, Any], family: str) -> str:
    field = FAMILY_TO_CONTEXT_FIELD[family]
    slot = context.get(field)
    if not isinstance(slot, Mapping):
        raise IncrementalInformationSetError(f"{field}_INVALID")
    return str(slot.get("presence") or "")


def _expected_missing_reason(stage_id: str, family: str) -> str:
    return f"{EXCLUDED_MISSING_REASON_PREFIX}:{stage_id}:{family}"


def assert_market_context_respects_stage_boundary_v1(
    market_context: Mapping[str, Any],
    *,
    stage_id: str,
) -> None:
    """Prove B-stage feature boundary: excluded families MUST be explicit MISSING."""
    context = validate_market_context_v1(market_context)
    included = included_context_families_v1(stage_id)
    excluded = excluded_context_families_v1(stage_id)

    for family in included:
        field = FAMILY_TO_CONTEXT_FIELD[family]
        presence = _slot_presence(context, family)
        if presence != ContextFamilyPresence.PRESENT.value:
            raise IncrementalInformationSetError(f"INCLUDED_FAMILY_NOT_PRESENT:{stage_id}:{family}")
        if family == FAMILY_LIQUIDITY_MICROSTRUCTURE:
            slot = context[field]
            kind = slot.get("microstructure_kind")
            if stage_id == STAGE_B5:
                if kind != MICROSTRUCTURE_KIND_TRUE_L2:
                    raise IncrementalInformationSetError("B5_REQUIRES_TRUE_L2_MICROSTRUCTURE")
            elif stage_id in (STAGE_B1, STAGE_B2, STAGE_B3, STAGE_B4):
                if kind != MICROSTRUCTURE_KIND_PROXY_OHLCV:
                    raise IncrementalInformationSetError("STAGE_REQUIRES_PROXY_MICROSTRUCTURE")
        if family == FAMILY_CROSS_MARKET_STATE:
            slot = context[field]
            if slot.get("cross_market_authority") != CROSS_MARKET_CONTEXT_ONLY:
                raise IncrementalInformationSetError("CROSS_MARKET_MUST_BE_CONTEXT_ONLY")

    for family in excluded:
        field = FAMILY_TO_CONTEXT_FIELD[family]
        slot = context.get(field)
        if not isinstance(slot, Mapping):
            raise IncrementalInformationSetError(f"{field}_INVALID")
        if slot.get("presence") != ContextFamilyPresence.MISSING.value:
            raise IncrementalInformationSetError(
                f"EXCLUDED_FAMILY_MUST_BE_MISSING:{stage_id}:{family}"
            )
        reason = str(slot.get("missing_reason") or "")
        expected = _expected_missing_reason(stage_id, family)
        if not reason.startswith(EXCLUDED_MISSING_REASON_PREFIX):
            raise IncrementalInformationSetError(
                f"EXCLUDED_FAMILY_MISSING_REASON_INVALID:{stage_id}:{family}"
            )
        if expected not in reason:
            raise IncrementalInformationSetError(
                f"EXCLUDED_FAMILY_MISSING_REASON_MISMATCH:{stage_id}:{family}"
            )


def _present_slot_from_context(context: Mapping[str, Any], field: str) -> dict[str, Any]:
    slot = context.get(field)
    if not isinstance(slot, Mapping):
        raise IncrementalInformationSetError(f"{field}_INVALID")
    if slot.get("presence") != ContextFamilyPresence.PRESENT.value:
        raise IncrementalInformationSetError(f"{field}_NOT_PRESENT")
    return dict(slot)


def project_market_context_to_stage_v1(
    source_context: Mapping[str, Any],
    *,
    stage_id: str,
    information_set_id: str,
) -> MappingProxyType[str, Any]:
    """Derive a replayable MARKET_CONTEXT slice for a B-stage (fail-closed on leakage)."""
    source = validate_market_context_v1(source_context)
    included = included_context_families_v1(stage_id)

    if stage_id == STAGE_B5:
        census = census_true_l2_research_substrate_v1()
        if census["b5_status"] != TrueL2AdmissibilityStatus.ADMISSIBLE.value:
            raise IncrementalInformationSetError("B5_DEFERRED_NOT_ADMISSIBLE")

    def _family_slot(family: str) -> dict[str, Any] | None:
        field = FAMILY_TO_CONTEXT_FIELD[family]
        if family not in included:
            return None
        return _present_slot_from_context(source, field)

    for family in included:
        field = FAMILY_TO_CONTEXT_FIELD[family]
        if _slot_presence(source, family) != ContextFamilyPresence.PRESENT.value:
            raise IncrementalInformationSetError(
                f"SOURCE_MISSING_REQUIRED_FAMILY:{stage_id}:{family}"
            )
        if family == FAMILY_LIQUIDITY_MICROSTRUCTURE and stage_id != STAGE_B5:
            slot = source[field]
            if slot.get("microstructure_kind") != MICROSTRUCTURE_KIND_PROXY_OHLCV:
                raise IncrementalInformationSetError("SOURCE_MICROSTRUCTURE_MUST_BE_PROXY")

    feature_versions = dict(source.get("feature_versions") or {})
    feature_versions["phase_22_stage_id"] = stage_id
    feature_versions["phase_22_information_set_id"] = information_set_id

    info_identity = {
        "phase_22_stage_id": stage_id,
        "phase_22_information_set_id": information_set_id,
        "source_context_id": source["context_id"],
    }
    information_set_ref = derive_information_set_ref_v1(identity_body=info_identity)

    family_slots: dict[str, Any] = {}
    for family in _ALL_FAMILIES:
        field = FAMILY_TO_CONTEXT_FIELD[family]
        if family in included:
            family_slots[field] = _family_slot(family)
        else:
            family_slots[field] = {
                "schema_version": CONTEXT_FAMILY_SLOT_SCHEMA,
                "presence": ContextFamilyPresence.MISSING.value,
                "state_ref": None,
                "missing_reason": _expected_missing_reason(stage_id, family),
                "producer_owner": "phase_22.incremental_information_set_v1",
                "producer_ownership": "GOVERNED_MISSING",
            }
    family_slots["quality_state_ref"] = {
        "schema_version": CONTEXT_FAMILY_SLOT_SCHEMA,
        "presence": ContextFamilyPresence.MISSING.value,
        "state_ref": None,
        "missing_reason": "NO_GOVERNED_QUALITY_FACT_REF_SUPPLIED",
        "producer_owner": "phase_22.incremental_information_set_v1",
        "producer_ownership": "GOVERNED_MISSING",
    }

    identity_body = {
        "schema_version": MARKET_CONTEXT_SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "observed_at": source["observed_at"],
        "instrument_ref": source["instrument_ref"],
        "information_set_ref": information_set_ref,
        **family_slots,
        "provenance_refs": tuple(source.get("provenance_refs") or []),
        "feature_versions": feature_versions,
    }
    digest = compute_content_hash_v0(identity_body)
    payload = {
        **identity_body,
        "context_id": derive_context_id_v1(identity_body=identity_body),
        "provenance_refs": list(identity_body["provenance_refs"]),
        "market_context_authority": MARKET_CONTEXT_AUTHORITY,
        "n_bars_backbone_semantics": N_BARS_BACKBONE_TOKEN,
        "content_digest": digest,
    }
    projected = validate_market_context_v1(payload)
    assert_market_context_respects_stage_boundary_v1(projected, stage_id=stage_id)
    return projected


__all__ = [
    "BEHAVIOR_CONTRACT_VERSION",
    "B5_TRUE_L2_REQUIRED",
    "CONTEXT_CONTRACT_VERSION",
    "FAMILY_CROSS_MARKET_STATE",
    "FAMILY_TO_CONTEXT_FIELD",
    "FAMILY_DERIVATIVES_STATE",
    "FAMILY_FLOW_STATE",
    "FAMILY_LIQUIDITY_MICROSTRUCTURE",
    "FAMILY_PRICE_STATE",
    "FAMILY_VOLATILITY_STATE",
    "INCREMENTAL_INFORMATION_SET_SCHEMA",
    "IncrementalInformationSetError",
    "IncrementalInformationSetRequestV1",
    "STAGE_B0",
    "STAGE_B1",
    "STAGE_B2",
    "STAGE_B3",
    "STAGE_B4",
    "STAGE_B5",
    "STAGE_CHAIN",
    "TrueL2AdmissibilityStatus",
    "assert_market_context_respects_stage_boundary_v1",
    "build_incremental_information_set_v1",
    "census_true_l2_research_substrate_v1",
    "derive_information_set_id_v1",
    "excluded_context_families_v1",
    "included_context_families_v1",
    "predecessor_stage_id_v1",
    "project_market_context_to_stage_v1",
]
