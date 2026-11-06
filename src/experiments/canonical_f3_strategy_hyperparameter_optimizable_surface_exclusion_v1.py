"""F3 global strategy hyperparameter optimizable surface exclusion v1 (Owner D4).

Documents CURRENT authority boundary: no global strategy.* envelope, no legacy path activation.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED: Final[bool] = False
F3_FAMILY_GATE_ID: Final[str] = "F3"
EXCLUSION_REASON: Final[str] = "EXCLUDED_BY_AUTHORITY_BOUNDARY"
OWNER_DECISION_ID: Final[str] = "D4"
DECISION_CONFIG: Final[str] = (
    "config/governance/f3_global_optimizable_surface_exclusion_v1_decision_v1.json"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/OPTIMIZATION_SURFACE_OWNER_GRANTS_MATERIALIZATION_V1.md"
)
NAMED_BINDING_FUTURE_OWNER_SCOPE: Final[str] = (
    "SEPARATE_NAMED_BINDING_OWNER_DECISION_REQUIRED_NOT_CURRENT"
)

_FORBIDDEN_SURFACE_PATTERNS: Final[frozenset[str]] = frozenset(
    {
        "STRATEGY_HYPERPARAMETER_RESEARCH_OPTIMIZATION_V1",
        "F3_STRATEGY_HYPERPARAMETER_OPTIMIZATION_V1",
        "GLOBAL_STRATEGY_PARAM_OPTIMIZABLE_SURFACE_V1",
    }
)


def assert_global_f3_surface_not_authorized_v1(*, surface_id: str | None) -> None:
    if surface_id is None:
        return
    normalized = surface_id.strip().upper()
    if normalized in _FORBIDDEN_SURFACE_PATTERNS or normalized.startswith("F3_STRATEGY"):
        raise ValueError(f"f3_global_surface_excluded:{surface_id}")


def build_f3_exclusion_record_v1() -> Mapping[str, Any]:
    return MappingProxyType(
        {
            "family_gate_id": F3_FAMILY_GATE_ID,
            "global_f3_optimizable_surface_authorized": GLOBAL_F3_OPTIMIZABLE_SURFACE_AUTHORIZED,
            "exclusion_reason": EXCLUSION_REASON,
            "owner_decision_id": OWNER_DECISION_ID,
            "strategy_param_envelope_materialization_authorized": False,
            "legacy_configured_strategy_path_activation_authorized": False,
            "mv2_double_play_trading_semantics_mutation_authorized": False,
            "named_binding_future_owner_scope": NAMED_BINDING_FUTURE_OWNER_SCOPE,
            "productive_effect": "NONE",
            "external_effect_authorized": False,
        }
    )
