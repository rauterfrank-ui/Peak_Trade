"""Authoritative Phase 9.1 classification map for proven repository entries only."""

from __future__ import annotations

from typing import Dict, Tuple

from src.ops.phase_9_1_strategy_registry_closure_v1.constants_v1 import (
    DOUBLE_PLAY_AUTHORITY,
    HOST_COMPOSITION_STUB_ID,
    MASTER_V2_AUTHORITY,
    ORPHAN_MODULE_IDS,
    PRODUCTIVE_HOST_ENTRY,
    REGISTRY_OWNER,
)
from src.ops.phase_9_1_strategy_registry_closure_v1.models_v1 import StrategyAuthorityClassV1

# Target classification for every proven registry strategy_id.
# No silent promotion: catalog production strategies remain EXPERIMENT_ONLY until
# a separate Owner-authorized composition binding exists.
_REGISTRY_TARGET: Dict[str, StrategyAuthorityClassV1] = {
    # Research / named models (Runbook checklist — repository-proven IDs only)
    "armstrong_cycle": StrategyAuthorityClassV1.RESEARCH_INFORMATION,
    "el_karoui_vol_model": StrategyAuthorityClassV1.RESEARCH_INFORMATION,
    "ehlers_cycle_filter": StrategyAuthorityClassV1.RESEARCH_INFORMATION,
    "bouchaud_microstructure": StrategyAuthorityClassV1.RESEARCH_INFORMATION,
    "meta_labeling": StrategyAuthorityClassV1.RESEARCH_INFORMATION,  # Lopez de Prado
    "vol_regime_overlay": StrategyAuthorityClassV1.RESEARCH_INFORMATION,  # Gatheral/Cont
    # Catalog / offline experiment strategies (not Cap 7.2 decision authority)
    "ma_crossover": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "rsi_reversion": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "bollinger_bands": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "macd": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "momentum_1h": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "trend_following": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "mean_reversion": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "breakout": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "vol_regime_filter": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "composite": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "regime_aware_portfolio": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    # Legacy / functional-only / deauthorized loader paths
    "ecm_cycle": StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED,
    "vol_breakout": StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED,
    "mean_reversion_channel": StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED,
    "rsi_strategy": StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED,
    "breakout_donchian": StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED,
    "my_strategy": StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED,
}

_CURRENT_FROM_LEGACY_TIER: Dict[str, StrategyAuthorityClassV1] = {
    "r_and_d": StrategyAuthorityClassV1.RESEARCH_INFORMATION,
    "production": StrategyAuthorityClassV1.EXPERIMENT_ONLY,
    "functional": StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED,
}

_DEAUTH_REASON: Dict[str, str] = {
    "ecm_cycle": "functional_only_loader_path_not_StrategySpec_no_canonical_authority",
    "vol_breakout": "toml_legacy_replaced_by_vol_regime_filter_breakout",
    "mean_reversion_channel": "functional_only_loader_path_not_StrategySpec",
    "rsi_strategy": "functional_only_loader_path_superseded_by_rsi_reversion",
    "breakout_donchian": "toml_legacy_replaced_by_breakout",
    "my_strategy": "toml_legacy_demo_not_for_production",
    "breakout_confirmation_v1": "orphan_module_absent_from_canonical_registry",
    "el_karoui_vol_v1": "deprecated_alias_of_el_karoui_vol_model",
}

# Non-strategy authority / host entries proven in repository code.
_AUTHORITY_AND_HOST_TARGETS: Dict[str, StrategyAuthorityClassV1] = {
    "master_v2": StrategyAuthorityClassV1.CANONICAL_AUTHORITY,
    "double_play": StrategyAuthorityClassV1.CANONICAL_AUTHORITY,
    HOST_COMPOSITION_STUB_ID: StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT,
    "breakout_confirmation_v1": StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED,
    "el_karoui_vol_v1": StrategyAuthorityClassV1.LEGACY_DEAUTHORIZED,
}

_AUTHORITY_IMPL: Dict[str, Tuple[str, str]] = {
    "master_v2": (
        MASTER_V2_AUTHORITY,
        "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    ),
    "double_play": (
        DOUBLE_PLAY_AUTHORITY,
        "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
    ),
    HOST_COMPOSITION_STUB_ID: (
        "SuitabilityStrategyEntryV1",
        "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
        "decision_economics_cycle_bridge_v1.py",
    ),
    "breakout_confirmation_v1": (
        "src.strategies.breakout_confirmation_v1",
        "src/strategies/breakout_confirmation_v1.py",
    ),
    "el_karoui_vol_v1": (
        "alias:el_karoui_vol_model",
        "src/strategies/registry.py",
    ),
}


def registry_target_classification(strategy_id: str) -> StrategyAuthorityClassV1:
    if strategy_id not in _REGISTRY_TARGET:
        raise KeyError(f"unclassified_registry_strategy:{strategy_id}")
    return _REGISTRY_TARGET[strategy_id]


def non_registry_target_classification(entry_id: str) -> StrategyAuthorityClassV1:
    if entry_id not in _AUTHORITY_AND_HOST_TARGETS:
        raise KeyError(f"unclassified_non_registry_entry:{entry_id}")
    return _AUTHORITY_AND_HOST_TARGETS[entry_id]


def current_classification_from_spec_tier(tier: str) -> StrategyAuthorityClassV1:
    return _CURRENT_FROM_LEGACY_TIER.get(tier, StrategyAuthorityClassV1.EXPERIMENT_ONLY)


def deauthorization_reason(entry_id: str) -> str:
    return _DEAUTH_REASON.get(entry_id, "")


def non_registry_implementation(entry_id: str) -> Tuple[str, str]:
    if entry_id not in _AUTHORITY_IMPL:
        raise KeyError(f"missing_implementation_for:{entry_id}")
    return _AUTHORITY_IMPL[entry_id]


def all_required_registry_ids() -> Tuple[str, ...]:
    return tuple(sorted(_REGISTRY_TARGET))


def all_non_registry_ids() -> Tuple[str, ...]:
    return tuple(sorted(_AUTHORITY_AND_HOST_TARGETS))


def productive_callers_for(
    entry_id: str, *, classification: StrategyAuthorityClassV1
) -> Tuple[str, ...]:
    if classification is StrategyAuthorityClassV1.CANONICAL_AUTHORITY:
        return (PRODUCTIVE_HOST_ENTRY, REGISTRY_OWNER)
    if classification is StrategyAuthorityClassV1.AUTHORIZED_COMPOSITION_INPUT:
        return (PRODUCTIVE_HOST_ENTRY,)
    if classification is StrategyAuthorityClassV1.RESEARCH_INFORMATION:
        return (
            "src.backtest.mv2_research_wiring_v1",
            "scripts.run_backtest",
        )
    if classification is StrategyAuthorityClassV1.EXPERIMENT_ONLY:
        return (
            "scripts.run_backtest",
            "src.sweeps.engine",
            "src.strategies.registry.create_strategy_from_config",
        )
    # LEGACY_DEAUTHORIZED — enumerated historical callers; runtime authority denied
    if entry_id == "el_karoui_vol_v1":
        return ("src.strategies.registry.resolve_strategy_id",)
    if entry_id in ORPHAN_MODULE_IDS:
        return ()
    return ("src.strategies.__init__.load_strategy",)
