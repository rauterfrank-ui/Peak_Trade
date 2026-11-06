"""R2 Strategy Registry / Suitability / Selection v1 tests (offline, no-order)."""

from __future__ import annotations

import json

import pytest

from src.ops.phase_9_1_strategy_registry_closure_v1.constants_v1 import HOST_COMPOSITION_STUB_ID
from src.strategies.canonical_strategy_registry_suitability_selection_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_ROLE,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.eligibility_v1 import (
    evaluate_eligibility_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.identity_v1 import (
    resolve_canonical_identity_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
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
    validate_layer_config_v1,
)
from src.strategies.registry import build_registry_snapshot
from src.strategies.suitability_registry_adapter_v1 import (
    build_suitability_registry_from_snapshot,
)
from src.trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingStatus,
    SuitabilityRankingPolicyV1,
    SuitabilityStrategyRegistryV1,
    rank_eligible_strategies,
    select_strategy_deterministic,
)
from tests.trading.master_v2.test_suitability_binding_v1 import _strategy_entry


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_registry_uniqueness_and_identity_stability() -> None:
    snapshot = build_registry_snapshot()
    assert len(snapshot.strategy_ids_sorted) == len(set(snapshot.strategy_ids_sorted))
    first = resolve_canonical_identity_v1("ma_crossover")
    second = resolve_canonical_identity_v1("ma_crossover")
    assert first.canonical_strategy_id == "ma_crossover"
    assert first.identity_digest == second.identity_digest
    alias = resolve_canonical_identity_v1("el_karoui_vol_v1")
    canonical = resolve_canonical_identity_v1("el_karoui_vol_model")
    assert alias.canonical_strategy_id == "el_karoui_vol_model"
    assert alias.alias_applied is True
    assert alias.strategy_version == canonical.strategy_version


@pytest.mark.parametrize(
    "raw_key",
    ["", "definitely_not_a_strategy_xyz"],
)
def test_unknown_or_invalid_identity_fail_closed(raw_key: str) -> None:
    with pytest.raises(StrategyRegistrySuitabilitySelectionError):
        resolve_canonical_identity_v1(raw_key)


def test_duplicate_requested_ids_fail_closed() -> None:
    with pytest.raises(StrategyRegistrySuitabilitySelectionError, match="duplicate"):
        select_registered_strategies_v1(
            requested_ids=("ma_crossover", "ma_crossover"),
            intent=SelectionIntent.CATALOG_ENUMERATE,
        )


def test_suitability_snapshot_deterministic_and_unique() -> None:
    snapshot = build_registry_snapshot()
    first = build_suitability_registry_from_snapshot(snapshot)
    second = build_suitability_registry_from_snapshot(snapshot)
    ids = tuple(entry.strategy_id for entry in first.entries)
    assert ids == tuple(entry.strategy_id for entry in second.entries)
    assert len(ids) == len(set(ids))
    for strategy_id in snapshot.strategy_ids_sorted:
        record = evaluate_eligibility_v1(strategy_id)
        assert record.max_age_consulted is False
        assert record.runtime_authority_eligible is False


def test_suitability_ranking_reuses_canonical_owner() -> None:
    registry = SuitabilityStrategyRegistryV1(
        entries=(
            _strategy_entry(strategy_id="beta", priority_rank=2),
            _strategy_entry(strategy_id="alpha", priority_rank=2),
            _strategy_entry(strategy_id="gamma", priority_rank=1),
        )
    )
    policy = SuitabilityRankingPolicyV1(
        validity_epochs=1,
        no_match_status=SuitabilityBindingStatus.FAIL,
        policy_version=SUITABILITY_RANKING_POLICY_VERSION,
        tie_break_field="strategy_id",
    )
    ranked_a = rank_eligible_strategies(registry.entries, policy=policy)
    ranked_b = rank_eligible_strategies(registry.entries, policy=policy)
    assert tuple(e.strategy_id for e in ranked_a) == tuple(e.strategy_id for e in ranked_b)
    selected, _trace = select_strategy_deterministic(ranked_a, policy=policy)
    assert selected == "gamma"


def test_catalog_selection_deterministic_and_non_authoritative() -> None:
    first = select_registered_strategies_v1(intent=SelectionIntent.CATALOG_ENUMERATE)
    second = select_registered_strategies_v1(intent=SelectionIntent.CATALOG_ENUMERATE)
    assert first.selection_digest == second.selection_digest
    assert first.selected_strategy_id is None
    assert first.trading_grant is False
    assert first.authority_effect == "NONE"
    assert first.max_age_consulted is False
    assert first.eligible_ids == ()


def test_catalog_strategy_not_composition_or_runtime_selectable() -> None:
    with pytest.raises(StrategyRegistrySuitabilitySelectionError, match="composition_input_denied"):
        select_registered_strategies_v1(
            requested_ids=("ma_crossover",),
            intent=SelectionIntent.COMPOSITION_CANDIDATE,
        )
    with pytest.raises(StrategyRegistrySuitabilitySelectionError, match="runtime_authority_denied"):
        select_registered_strategies_v1(
            requested_ids=("ma_crossover",),
            intent=SelectionIntent.RUNTIME_AUTHORITY,
        )


def test_host_composition_stub_selectable_without_trading_grant() -> None:
    result = select_registered_strategies_v1(
        requested_ids=(HOST_COMPOSITION_STUB_ID,),
        intent=SelectionIntent.COMPOSITION_CANDIDATE,
    )
    assert result.selected_strategy_id == HOST_COMPOSITION_STUB_ID
    assert result.trading_grant is False
    assert result.runtime_effect is False
    eligibility = evaluate_eligibility_v1(HOST_COMPOSITION_STUB_ID)
    assert eligibility.composition_eligible is True
    assert eligibility.runtime_authority_eligible is False


@pytest.mark.parametrize(
    "intent",
    [SelectionIntent.TRADING_ACTIVATE, SelectionIntent.PROMOTE],
)
def test_forbidden_intents_fail_closed(intent: SelectionIntent) -> None:
    with pytest.raises(
        StrategyRegistrySuitabilitySelectionError, match="forbidden_selection_intent"
    ):
        select_registered_strategies_v1(intent=intent)


def test_max_age_is_watchdog_only_and_not_in_selection() -> None:
    assert MAX_AGE_ROLE == "WATCHDOG_ONLY"
    assert MAX_AGE_ENFORCEMENT_ENABLED is False
    payload = load_layer_config_v1()
    assert payload["max_age_role"] == "WATCHDOG_ONLY"
    assert payload["max_age_enforcement_enabled"] is False
    assert payload["max_age_can_change_selection"] is False
    result = select_registered_strategies_v1(intent=SelectionIntent.CATALOG_ENUMERATE)
    assert result.max_age_consulted is False


def test_config_drift_fail_closed() -> None:
    payload = dict(load_layer_config_v1())
    payload["activated"] = True
    with pytest.raises(StrategyRegistrySuitabilitySelectionError, match="activated"):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["max_age_enforcement_enabled"] = True
    with pytest.raises(
        StrategyRegistrySuitabilitySelectionError, match="max_age_enforcement_enabled"
    ):
        validate_layer_config_v1(payload)
    payload = dict(load_layer_config_v1())
    payload["registry_is_live_permission"] = True
    with pytest.raises(
        StrategyRegistrySuitabilitySelectionError, match="registry_is_live_permission"
    ):
        validate_layer_config_v1(payload)


def test_verifier_pass_and_no_second_owners() -> None:
    claims = evaluate_r2_registry_suitability_selection_v1()
    assert claims["verdict"] == "PASS_R2_STRATEGY_REGISTRY_SUITABILITY_SELECTION_V1"
    assert claims["activated"] is False
    assert claims["productive_caller_exists"] is False
    assert claims["second_strategy_registry_risk"] == "NONE_SRC_STRATEGIES_REGISTRY_ONLY"
    assert claims["second_selection_path_risk"] == "NONE_SUITABILITY_SELECT_PLUS_R2_NON_AUTHORITY"
    assert claims["second_identity_model_risk"] == "NONE_CANONICAL_RESOLVE_STRATEGY_ID"
    assert claims["max_age_role"] == "WATCHDOG_ONLY"
    assert claims["max_age_enforcement_enabled"] is False
    assert claims["eg_reg_callers_enumerated"] is True
    assert claims["g14_non_authoritative_until_promotion"] is True
    assert len(str(claims["config_digest"])) == 64
    assert len(str(claims["registry_semantic_digest"])) == 64
    assert len(str(claims["catalog_selection_digest"])) == 64
