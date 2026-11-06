"""Deterministic non-authoritative catalog selection interface.

Does not replace SINGLE_SELECTED_FUTURE instrument selection.
Does not replace evaluate_suitability_binding_v1 / select_strategy_deterministic.
Does not consult MAX_AGE. Does not grant trading, promotion, or runtime authority.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Sequence

from src.strategies.canonical_strategy_registry_suitability_selection_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    HOST_COMPOSITION_STUB_ID,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.eligibility_v1 import (
    classify_entry_v1,
    evaluate_eligibility_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.identity_v1 import (
    assert_unique_requested_ids_v1,
    resolve_canonical_identity_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.lineage_v1 import (
    envelope_digest,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.models_v1 import (
    SelectionIntent,
    SelectionResultV1,
    StrategyRegistrySuitabilitySelectionError,
)
from src.strategies.registry import build_registry_snapshot
from src.strategies.suitability_registry_adapter_v1 import (
    build_suitability_registry_from_snapshot,
)
from src.trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingStatus,
    SuitabilityRankingPolicyV1,
    rank_eligible_strategies,
)


def _ranking_policy() -> SuitabilityRankingPolicyV1:
    return SuitabilityRankingPolicyV1(
        validity_epochs=1,
        no_match_status=SuitabilityBindingStatus.FAIL,
        policy_version=SUITABILITY_RANKING_POLICY_VERSION,
        tie_break_field="strategy_id",
    )


def _suitability_snapshot_digest() -> tuple[str, object]:
    snapshot = build_registry_snapshot()
    suitability = build_suitability_registry_from_snapshot(snapshot)
    payload = {
        "entries": [
            {
                "disabled": entry.disabled,
                "priority_rank": entry.priority_rank,
                "strategy_id": entry.strategy_id,
            }
            for entry in sorted(suitability.entries, key=lambda e: e.strategy_id)
        ]
    }
    return envelope_digest(kind="suitability_snapshot_v1", payload=payload), suitability


def select_registered_strategies_v1(
    *,
    requested_ids: Sequence[str] | None = None,
    intent: SelectionIntent = SelectionIntent.CATALOG_ENUMERATE,
) -> SelectionResultV1:
    if intent in (SelectionIntent.TRADING_ACTIVATE, SelectionIntent.PROMOTE):
        raise StrategyRegistrySuitabilitySelectionError(
            f"forbidden_selection_intent:{intent.value}"
        )
    if intent is SelectionIntent.RUNTIME_AUTHORITY:
        raise StrategyRegistrySuitabilitySelectionError("runtime_authority_denied_until_promotion")

    snapshot = build_registry_snapshot()
    suitability_digest, suitability = _suitability_snapshot_digest()
    requested = tuple(requested_ids) if requested_ids is not None else ()
    if requested:
        assert_unique_requested_ids_v1(requested)

    if intent is SelectionIntent.CATALOG_ENUMERATE:
        source_ids = requested or snapshot.strategy_ids_sorted
        resolved: list[str] = []
        classifications: dict[str, str] = {}
        for raw in source_ids:
            identity = resolve_canonical_identity_v1(raw)
            resolved.append(identity.canonical_strategy_id)
            classifications[identity.canonical_strategy_id] = classify_entry_v1(
                identity.canonical_strategy_id
            ).value
        if len(resolved) != len(set(resolved)):
            raise StrategyRegistrySuitabilitySelectionError("ambiguous_canonical_identity")
        result = SelectionResultV1(
            intent=intent,
            requested_ids=requested,
            resolved_ids=tuple(resolved),
            eligible_ids=(),
            selected_strategy_id=None,
            classification_by_id=MappingProxyType(classifications),
            selection_digest="",
            registry_semantic_digest=snapshot.semantic_digest,
            suitability_snapshot_digest=suitability_digest,
            authority_effect=AUTHORITY_EFFECT,
            trading_grant=False,
            runtime_effect=False,
            max_age_consulted=False,
            reason_codes=("catalog_enumerate_non_authoritative",),
        )
        digest = envelope_digest(kind="selection_result_v1", payload=dict(result.to_mapping()))
        return SelectionResultV1(
            intent=result.intent,
            requested_ids=result.requested_ids,
            resolved_ids=result.resolved_ids,
            eligible_ids=result.eligible_ids,
            selected_strategy_id=result.selected_strategy_id,
            classification_by_id=result.classification_by_id,
            selection_digest=digest,
            registry_semantic_digest=result.registry_semantic_digest,
            suitability_snapshot_digest=result.suitability_snapshot_digest,
            authority_effect=result.authority_effect,
            trading_grant=result.trading_grant,
            runtime_effect=result.runtime_effect,
            max_age_consulted=result.max_age_consulted,
            reason_codes=result.reason_codes,
        )

    if intent is SelectionIntent.COMPOSITION_CANDIDATE:
        source_ids = requested or (HOST_COMPOSITION_STUB_ID,)
        eligible_entries = []
        resolved_ids: list[str] = []
        classifications: dict[str, str] = {}
        for raw in source_ids:
            eligibility = evaluate_eligibility_v1(raw)
            classifications[eligibility.strategy_id] = eligibility.classification
            resolved_ids.append(eligibility.strategy_id)
            if not eligibility.composition_eligible:
                raise StrategyRegistrySuitabilitySelectionError(
                    f"composition_input_denied:{raw}:{eligibility.reason_code}"
                )
            match = next(
                (entry for entry in suitability.entries if entry.strategy_id == raw),
                None,
            )
            if match is not None:
                eligible_entries.append(match)
        if HOST_COMPOSITION_STUB_ID in source_ids and not eligible_entries:
            ranked_ids = (HOST_COMPOSITION_STUB_ID,)
            selected = HOST_COMPOSITION_STUB_ID
            reason = "host_composition_stub_only_no_decision_authority"
        else:
            ranked = rank_eligible_strategies(tuple(eligible_entries), policy=_ranking_policy())
            ranked_ids = tuple(entry.strategy_id for entry in ranked)
            selected = ranked_ids[0] if ranked_ids else None
            reason = "composition_candidate_non_authoritative"
        result = SelectionResultV1(
            intent=intent,
            requested_ids=requested,
            resolved_ids=tuple(resolved_ids),
            eligible_ids=ranked_ids,
            selected_strategy_id=selected,
            classification_by_id=MappingProxyType(classifications),
            selection_digest="",
            registry_semantic_digest=snapshot.semantic_digest,
            suitability_snapshot_digest=suitability_digest,
            authority_effect=AUTHORITY_EFFECT,
            trading_grant=False,
            runtime_effect=False,
            max_age_consulted=False,
            reason_codes=(reason,),
        )
        digest = envelope_digest(kind="selection_result_v1", payload=dict(result.to_mapping()))
        return SelectionResultV1(
            intent=result.intent,
            requested_ids=result.requested_ids,
            resolved_ids=result.resolved_ids,
            eligible_ids=result.eligible_ids,
            selected_strategy_id=result.selected_strategy_id,
            classification_by_id=result.classification_by_id,
            selection_digest=digest,
            registry_semantic_digest=result.registry_semantic_digest,
            suitability_snapshot_digest=result.suitability_snapshot_digest,
            authority_effect=result.authority_effect,
            trading_grant=result.trading_grant,
            runtime_effect=result.runtime_effect,
            max_age_consulted=result.max_age_consulted,
            reason_codes=result.reason_codes,
        )

    raise StrategyRegistrySuitabilitySelectionError(f"unsupported_selection_intent:{intent.value}")
