"""Gated Regime/Meta candidate-context contract.

Reuses R2 identity/eligibility. Does not call Phase 28 silent-fallback switching
as authority. Does not rewire Master V2 / Double Play. MAX_AGE is not consulted.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping, Sequence

from src.regime.canonical_regime_meta_gated_selection_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    KNOWN_REGIME_LABELS,
    LLM_REGIME_IDENTITIES,
    RAW_LLM_TRADING_AUTHORITY,
    RUNTIME_AUTHORITY_IMPACT,
    UNKNOWN_REGIME_LABEL,
)
from src.regime.canonical_regime_meta_gated_selection_v1.lineage_v1 import (
    envelope_digest,
    load_layer_config_v1,
)
from src.regime.canonical_regime_meta_gated_selection_v1.models_v1 import (
    GateIntent,
    RegimeMetaGateInputV1,
    RegimeMetaGateResultV1,
    RegimeMetaGatedSelectionError,
    SourceClass,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.eligibility_v1 import (
    evaluate_eligibility_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.identity_v1 import (
    assert_unique_requested_ids_v1,
    resolve_canonical_identity_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.models_v1 import (
    StrategyRegistrySuitabilitySelectionError,
)

_ALLOWED_META_KEYS = frozenset({"note", "advisory_text", "evidence_ref"})
_FORBIDDEN_INTENTS = frozenset(
    {
        GateIntent.EMIT_INTENT,
        GateIntent.SUBMIT_ORDER,
        GateIntent.PROMOTE,
        GateIntent.MUTATE_THRESHOLD,
        GateIntent.ACTIVATE_RUNTIME,
    }
)
_GATING_SOURCE_CLASSES = frozenset(
    {
        SourceClass.MARKET_STATE,
        SourceClass.REGIME_CONTEXT,
        SourceClass.META_DECISION_INPUT,
    }
)
_NON_ADJUSTING_SOURCE_CLASSES = frozenset(
    {
        SourceClass.ADVISORY_LLM_CONTEXT,
        SourceClass.STRATEGY_ELIGIBILITY,
        SourceClass.DETERMINISTIC_SELECTION,
    }
)


def _reject(message: str) -> None:
    raise RegimeMetaGatedSelectionError(message)


def _mapping_from_config(payload: Mapping[str, Any]) -> Mapping[str, tuple[str, ...]]:
    raw = payload.get("regime_candidate_mapping")
    if not isinstance(raw, dict) or not raw:
        _reject("malformed_meta_context:regime_candidate_mapping")
    mapping: dict[str, tuple[str, ...]] = {}
    for regime, ids in raw.items():
        if regime not in KNOWN_REGIME_LABELS:
            _reject(f"malformed_meta_context:mapping_regime:{regime}")
        if not isinstance(ids, list) or not ids:
            _reject(f"malformed_meta_context:mapping_ids:{regime}")
        mapping[str(regime)] = tuple(str(item) for item in ids)
    return MappingProxyType(mapping)


def _validate_meta_context(meta_context: Mapping[str, Any]) -> None:
    if not isinstance(meta_context, Mapping):
        _reject("malformed_meta_context:not_mapping")
    extra = set(meta_context) - _ALLOWED_META_KEYS
    if extra:
        _reject(f"malformed_meta_context:unsupported_keys:{sorted(extra)}")
    for key, value in meta_context.items():
        if not isinstance(value, str) or not value.strip():
            _reject(f"malformed_meta_context:invalid_{key}")


def _resolve_canonical_candidates(candidate_ids: Sequence[str]) -> tuple[str, ...]:
    requested = tuple(candidate_ids)
    try:
        assert_unique_requested_ids_v1(requested)
    except StrategyRegistrySuitabilitySelectionError as exc:
        _reject(str(exc))
    resolved: list[str] = []
    seen_canonical: set[str] = set()
    for raw in requested:
        try:
            identity = resolve_canonical_identity_v1(raw)
        except StrategyRegistrySuitabilitySelectionError as exc:
            _reject(str(exc))
        if identity.canonical_strategy_id in seen_canonical:
            _reject(f"alias_collision:{raw}:{identity.canonical_strategy_id}")
        seen_canonical.add(identity.canonical_strategy_id)
        eligibility = evaluate_eligibility_v1(identity.canonical_strategy_id)
        if eligibility.runtime_authority_eligible:
            _reject(f"runtime_authority_claimed:{identity.canonical_strategy_id}")
        resolved.append(identity.canonical_strategy_id)
    return tuple(resolved)


def apply_regime_meta_gate_v1(
    inp: RegimeMetaGateInputV1,
    *,
    config: Mapping[str, Any] | None = None,
) -> RegimeMetaGateResultV1:
    if inp.intent in _FORBIDDEN_INTENTS:
        _reject(f"forbidden_gate_intent:{inp.intent.value}")
    if inp.source_class is SourceClass.TRADING_AUTHORITY:
        _reject("source_class_trading_authority_forbidden")
    if inp.source_class is SourceClass.ADVISORY_LLM_CONTEXT:
        if inp.intent is not GateIntent.ADVISORY_RECORD_ONLY:
            _reject("llm_context_requires_advisory_record_only")
    elif inp.intent is not GateIntent.APPLY_GATED_CONTEXT:
        _reject(f"unsupported_gate_intent:{inp.intent.value}")

    _validate_meta_context(inp.meta_context)
    payload = dict(config) if config is not None else load_layer_config_v1()
    mapping_version = str(payload.get("mapping_version", ""))
    if not mapping_version or mapping_version != inp.mapping_version:
        _reject("mapping_version_mismatch")
    mapping = _mapping_from_config(payload)

    resolved = _resolve_canonical_candidates(inp.candidate_ids)
    identity_digest = envelope_digest(
        kind="r3_candidate_identity_v1",
        payload={"canonical_ids": list(resolved)},
    )
    mapping_digest = envelope_digest(
        kind="r3_regime_mapping_v1",
        payload={
            "mapping": {key: list(value) for key, value in mapping.items()},
            "mapping_version": mapping_version,
        },
    )

    adjustment_applied = False
    gated = resolved
    reasons: list[str] = []

    if inp.source_class in _NON_ADJUSTING_SOURCE_CLASSES:
        if inp.source_class is SourceClass.ADVISORY_LLM_CONTEXT:
            reasons.append("advisory_llm_non_authority_passthrough")
        else:
            reasons.append("source_class_recorded_without_adjustment")
    elif inp.source_class in _GATING_SOURCE_CLASSES:
        if inp.regime_id in LLM_REGIME_IDENTITIES:
            _reject("malformed_meta_context:llm_identity_used_as_market_regime")
        if inp.regime_id == UNKNOWN_REGIME_LABEL or inp.regime_id not in KNOWN_REGIME_LABELS:
            _reject(f"unknown_regime:{inp.regime_id!r}")
        allowed = mapping.get(inp.regime_id)
        if allowed is None:
            _reject(f"unknown_regime:{inp.regime_id!r}")
        gated = tuple(item for item in resolved if item in allowed)
        adjustment_applied = True
        if not gated:
            _reject("no_gated_candidates_after_regime_filter")
        reasons.append("regime_meta_candidate_context_adjusted")
        reasons.append("no_trading_authority_from_regime_meta")
    else:
        _reject(f"unsupported_source_class:{inp.source_class.value}")

    unsigned = RegimeMetaGateResultV1(
        regime_id=inp.regime_id,
        source_class=inp.source_class,
        candidates_before=resolved,
        candidates_after=gated,
        selected_strategy_id=None,
        adjustment_applied=adjustment_applied,
        identity_digest=identity_digest,
        mapping_digest=mapping_digest,
        result_digest="",
        authority_effect=AUTHORITY_EFFECT,
        runtime_authority_impact=RUNTIME_AUTHORITY_IMPACT,
        trading_grant=False,
        promotion_authority=False,
        raw_llm_trading_authority=RAW_LLM_TRADING_AUTHORITY,
        max_age_consulted=False,
        silent_threshold_mutation=False,
        reason_codes=tuple(reasons),
    )
    digest = envelope_digest(kind="r3_gate_result_v1", payload=dict(unsigned.to_mapping()))
    return RegimeMetaGateResultV1(
        regime_id=unsigned.regime_id,
        source_class=unsigned.source_class,
        candidates_before=unsigned.candidates_before,
        candidates_after=unsigned.candidates_after,
        selected_strategy_id=unsigned.selected_strategy_id,
        adjustment_applied=unsigned.adjustment_applied,
        identity_digest=unsigned.identity_digest,
        mapping_digest=unsigned.mapping_digest,
        result_digest=digest,
        authority_effect=unsigned.authority_effect,
        runtime_authority_impact=unsigned.runtime_authority_impact,
        trading_grant=unsigned.trading_grant,
        promotion_authority=unsigned.promotion_authority,
        raw_llm_trading_authority=unsigned.raw_llm_trading_authority,
        max_age_consulted=unsigned.max_age_consulted,
        silent_threshold_mutation=unsigned.silent_threshold_mutation,
        reason_codes=unsigned.reason_codes,
    )
