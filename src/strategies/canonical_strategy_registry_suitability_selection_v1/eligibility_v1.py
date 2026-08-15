"""Classification + catalog eligibility. Reuses Phase 9.1 and suitability snapshot.

MAX_AGE is not consulted. Does not activate trading, regime, or promotion.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from src.ops.phase_9_1_strategy_registry_closure_v1.classifications_v1 import (
    non_registry_target_classification,
    registry_target_classification,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.models_v1 import StrategyAuthorityClassV1
from src.strategies.canonical_strategy_registry_suitability_selection_v1.constants_v1 import (
    AUTHORITY_NON_STRATEGY_IDS,
    HOST_COMPOSITION_STUB_ID,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.identity_v1 import (
    resolve_canonical_identity_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.models_v1 import (
    EligibilityRecordV1,
    EligibilityStatus,
    StrategyRegistrySuitabilitySelectionError,
)
from src.strategies.registry import build_registry_snapshot
from src.strategies.suitability_registry_adapter_v1 import (
    build_suitability_registry_from_snapshot,
)


def classify_entry_v1(entry_id: str) -> StrategyAuthorityClassV1:
    try:
        identity = resolve_canonical_identity_v1(entry_id)
        return registry_target_classification(identity.canonical_strategy_id)
    except StrategyRegistrySuitabilitySelectionError:
        pass
    try:
        return non_registry_target_classification(entry_id)
    except KeyError as exc:
        raise StrategyRegistrySuitabilitySelectionError(
            f"unclassified_or_unknown_strategy:{entry_id!r}"
        ) from exc


def _suitability_disabled_by_id() -> Mapping[str, bool]:
    snapshot = build_registry_snapshot()
    suitability = build_suitability_registry_from_snapshot(snapshot)
    seen: dict[str, bool] = {}
    for entry in suitability.entries:
        if entry.strategy_id in seen:
            raise StrategyRegistrySuitabilitySelectionError(
                f"duplicate_suitability_snapshot_id:{entry.strategy_id}"
            )
        seen[entry.strategy_id] = bool(entry.disabled)
    return MappingProxyType(seen)


def evaluate_eligibility_v1(entry_id: str) -> EligibilityRecordV1:
    classification = classify_entry_v1(entry_id)
    catalog_present = False
    strategy_id = entry_id
    suitability_disabled = False
    try:
        identity = resolve_canonical_identity_v1(entry_id)
        strategy_id = identity.canonical_strategy_id
        catalog_present = True
        disabled_map = _suitability_disabled_by_id()
        suitability_disabled = bool(disabled_map.get(strategy_id, False))
    except StrategyRegistrySuitabilitySelectionError:
        catalog_present = False

    composition_eligible = (
        classification is StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT
        and not suitability_disabled
    )
    runtime_authority_eligible = False
    if classification is StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED:
        status = EligibilityStatus.LEGACY_DEAUTHORIZED
        reason = "legacy_deauthorized_rejected"
    elif classification is StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT:
        status = EligibilityStatus.COMPOSITION_INPUT_ONLY
        reason = "composition_input_only_no_decision_authority"
    elif classification is StrategyAuthorityClassV1.CANONICAL_AUTHORITY:
        status = EligibilityStatus.AUTHORITY_OWNER_NOT_STRATEGY
        reason = "authority_owner_not_strategy_catalog_entry"
    else:
        status = EligibilityStatus.CATALOGED_NON_AUTHORITY
        reason = "classified_non_authoritative_until_promotion"

    if entry_id in AUTHORITY_NON_STRATEGY_IDS or strategy_id in AUTHORITY_NON_STRATEGY_IDS:
        status = EligibilityStatus.AUTHORITY_OWNER_NOT_STRATEGY
        composition_eligible = False
        reason = "authority_owner_not_strategy_catalog_entry"
    if entry_id == HOST_COMPOSITION_STUB_ID:
        catalog_present = False

    return EligibilityRecordV1(
        strategy_id=strategy_id,
        classification=classification.value,
        status=status,
        composition_eligible=composition_eligible,
        runtime_authority_eligible=runtime_authority_eligible,
        suitability_disabled=suitability_disabled,
        catalog_present=catalog_present,
        max_age_consulted=False,
        reason_code=reason,
    )
