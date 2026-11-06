"""Thin adapters into existing governed pretrade/observation seams."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FRESHNESS_POLICY,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    FRESH_PRETRADE_FRESHNESS_POLICY,
    PRIVATE_BALANCE_EQUITY_OBSERVATION_ALLOWED,
    PRIVATE_STATE_PLANE_EQUITY_SIZING_AUTHORITY,
    RUNNING_ACCOUNT_EQUITY_MINT_ALLOWED,
    SELECTION_AUTHORITY,
)
from src.ops.okx_eea_private_account_state_runtime_v1.rest_baseline_v1 import (
    cached_state_may_not_substitute_fresh_pretrade_get_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.state_contracts_v1 import BalanceSnapshotV1


def wp_b_to_fresh_pretrade_observation_hint_v1(
    *,
    endpoint_path: str,
    cached_wp_b_fact: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Expose WP-B facts as non-authoritative hints only; fresh GET owner unchanged."""
    substitute_forbidden = cached_state_may_not_substitute_fresh_pretrade_get_v1(endpoint_path)
    return {
        "adapter": "wp_b_to_fresh_pretrade_runtime_get_v1",
        "endpoint_path": endpoint_path,
        "fresh_pretrade_owner": "FULL_CORE_FRESH_PRETRADE_RUNTIME_GET_SEAM_V1",
        "freshness_policy_required": FRESH_PRETRADE_FRESHNESS_POLICY,
        "fresh_pretrade_canonical_policy_pin": FRESHNESS_POLICY,
        "cached_wp_b_may_substitute_fresh_get": False,
        "fresh_pretrade_substitute_forbidden": substitute_forbidden or True,
        "cached_fact_present": cached_wp_b_fact is not None,
        "authority_effect": "NONE",
    }


def balance_equity_observation_adapter_v1(
    balance: BalanceSnapshotV1 | None,
) -> dict[str, Any]:
    if not PRIVATE_BALANCE_EQUITY_OBSERVATION_ALLOWED:
        raise ValueError("PRIVATE_BALANCE_EQUITY_OBSERVATION_FORBIDDEN")
    return {
        "adapter": "private_balance_equity_observation_v1",
        "total_eq": balance.total_eq if balance else None,
        "avail_eq": balance.avail_eq if balance else None,
        "quality": balance.quality.to_dict() if balance else None,
        "private_state_plane_equity_sizing_authority": PRIVATE_STATE_PLANE_EQUITY_SIZING_AUTHORITY,
        "running_account_equity_mint_allowed": RUNNING_ACCOUNT_EQUITY_MINT_ALLOWED,
        "selection_authority": SELECTION_AUTHORITY,
    }


def operator_readmodel_from_private_state_v1(
    facts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_name": "operator_private_state_readmodel.v1",
        "dashboard_authority_effect": "NONE",
        "fact_count": len(facts),
        "strategy_authority": "NONE",
        "execution_authority": "NONE",
    }
