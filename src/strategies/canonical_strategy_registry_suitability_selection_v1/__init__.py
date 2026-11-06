"""Canonical Strategy Registry / Suitability / Selection v1 (R2 / G14 / I15).

Additive, fail-closed, non-activating. Not a second registry. Not trading authority.
"""

from __future__ import annotations

from src.strategies.canonical_strategy_registry_suitability_selection_v1.constants_v1 import (
    CAPABILITY_ID,
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    REMEDIATION_ID,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.eligibility_v1 import (
    evaluate_eligibility_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.identity_v1 import (
    resolve_canonical_identity_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.models_v1 import (
    SelectionIntent,
    StrategyRegistrySuitabilitySelectionError,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.selection_v1 import (
    select_registered_strategies_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.verifier_v1 import (
    evaluate_r2_registry_suitability_selection_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_VERSION",
    "PACKAGE_MARKER",
    "REMEDIATION_ID",
    "SelectionIntent",
    "StrategyRegistrySuitabilitySelectionError",
    "evaluate_eligibility_v1",
    "evaluate_r2_registry_suitability_selection_v1",
    "resolve_canonical_identity_v1",
    "select_registered_strategies_v1",
]
