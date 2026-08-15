"""R3 Regime/Meta gated selection v1 tests (offline, no-order)."""

from __future__ import annotations

import json

import pytest

from src.regime.canonical_regime_meta_gated_selection_v1.constants_v1 import (
    CONTRACT_CONFIG_REL_PATH,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_ROLE,
    RAW_LLM_TRADING_AUTHORITY,
)
from src.regime.canonical_regime_meta_gated_selection_v1.gate_v1 import (
    apply_regime_meta_gate_v1,
)
from src.regime.canonical_regime_meta_gated_selection_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.regime.canonical_regime_meta_gated_selection_v1.models_v1 import (
    GateIntent,
    RegimeMetaGateInputV1,
    RegimeMetaGatedSelectionError,
    SourceClass,
)
from src.regime.canonical_regime_meta_gated_selection_v1.verifier_v1 import (
    evaluate_r3_regime_meta_gated_selection_v1,
    validate_layer_config_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.eligibility_v1 import (
    evaluate_eligibility_v1,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.verifier_v1 import (
    evaluate_r2_registry_suitability_selection_v1,
)


def _input(**overrides: object) -> RegimeMetaGateInputV1:
    payload = load_layer_config_v1()
    base: dict = {
        "candidate_ids": ("ma_crossover", "rsi_reversion", "trend_following"),
        "regime_id": "trending",
        "source_class": SourceClass.REGIME_CONTEXT,
        "intent": GateIntent.APPLY_GATED_CONTEXT,
        "meta_context": {"note": "r3_test"},
        "mapping_version": payload["mapping_version"],
    }
    base.update(overrides)
    return RegimeMetaGateInputV1(**base)


def test_layer_config_exists_and_matches_constants() -> None:
    payload = load_layer_config_v1()
    validate_layer_config_v1(payload)
    path = repo_root() / CONTRACT_CONFIG_REL_PATH
    disk = json.loads(path.read_text(encoding="utf-8"))
    assert digest_mapping(payload) == digest_mapping(disk)


def test_deterministic_same_input_same_output() -> None:
    first = apply_regime_meta_gate_v1(_input())
    second = apply_regime_meta_gate_v1(_input())
    assert first.result_digest == second.result_digest
    assert first.candidates_after == ("ma_crossover", "trend_following")
    assert first.selected_strategy_id is None
    assert first.trading_grant is False
    assert first.adjustment_applied is True


def test_canonical_strategy_ids_only_unknown_fail_closed() -> None:
    with pytest.raises(RegimeMetaGatedSelectionError, match="unknown_or_invalid_strategy_id"):
        apply_regime_meta_gate_v1(_input(candidate_ids=("not_a_strategy",)))


def test_unknown_regime_fail_closed() -> None:
    with pytest.raises(RegimeMetaGatedSelectionError, match="unknown_regime"):
        apply_regime_meta_gate_v1(_input(regime_id="unknown"))
    with pytest.raises(RegimeMetaGatedSelectionError, match="unknown_regime"):
        apply_regime_meta_gate_v1(_input(regime_id="fog"))


def test_malformed_meta_context_fail_closed() -> None:
    with pytest.raises(RegimeMetaGatedSelectionError, match="malformed_meta_context"):
        apply_regime_meta_gate_v1(_input(meta_context={"threshold": "0.9"}))
    with pytest.raises(RegimeMetaGatedSelectionError, match="llm_identity_used_as_market_regime"):
        apply_regime_meta_gate_v1(_input(regime_id="UP", source_class=SourceClass.MARKET_STATE))


def test_duplicate_candidate_fail_closed() -> None:
    with pytest.raises(RegimeMetaGatedSelectionError, match="duplicate"):
        apply_regime_meta_gate_v1(_input(candidate_ids=("ma_crossover", "ma_crossover")))


def test_alias_collision_fail_closed() -> None:
    with pytest.raises(RegimeMetaGatedSelectionError, match="alias_collision"):
        apply_regime_meta_gate_v1(_input(candidate_ids=("el_karoui_vol_v1", "el_karoui_vol_model")))


def test_research_strategy_not_runtime_selectable_after_gate() -> None:
    result = apply_regime_meta_gate_v1(_input())
    for strategy_id in result.candidates_after:
        eligibility = evaluate_eligibility_v1(strategy_id)
        assert eligibility.runtime_authority_eligible is False
    research = evaluate_eligibility_v1("armstrong_cycle")
    assert research.runtime_authority_eligible is False
    assert research.classification == "RESEARCH_INFORMATION"


def test_regime_influences_context_without_trading_authority() -> None:
    trending = apply_regime_meta_gate_v1(_input(regime_id="trending"))
    ranging = apply_regime_meta_gate_v1(_input(regime_id="ranging"))
    assert trending.candidates_after != ranging.candidates_after
    assert trending.authority_effect == "NONE"
    assert ranging.runtime_authority_impact == "NONE"
    assert trending.trading_grant is False
    assert ranging.promotion_authority is False


def test_llm_advisory_passthrough_is_non_authority() -> None:
    result = apply_regime_meta_gate_v1(
        _input(
            regime_id="UP",
            source_class=SourceClass.ADVISORY_LLM_CONTEXT,
            intent=GateIntent.ADVISORY_RECORD_ONLY,
            meta_context={"advisory_text": "no_trading"},
        )
    )
    assert result.adjustment_applied is False
    assert result.candidates_after == result.candidates_before
    assert result.raw_llm_trading_authority == RAW_LLM_TRADING_AUTHORITY
    assert result.trading_grant is False


@pytest.mark.parametrize(
    "intent",
    [
        GateIntent.EMIT_INTENT,
        GateIntent.SUBMIT_ORDER,
        GateIntent.PROMOTE,
        GateIntent.MUTATE_THRESHOLD,
        GateIntent.ACTIVATE_RUNTIME,
    ],
)
def test_forbidden_intents_fail_closed(intent: GateIntent) -> None:
    with pytest.raises(RegimeMetaGatedSelectionError, match="forbidden_gate_intent"):
        apply_regime_meta_gate_v1(_input(intent=intent))


def test_trading_authority_source_class_fail_closed() -> None:
    with pytest.raises(
        RegimeMetaGatedSelectionError, match="source_class_trading_authority_forbidden"
    ):
        apply_regime_meta_gate_v1(_input(source_class=SourceClass.TRADING_AUTHORITY))


def test_max_age_watchdog_only() -> None:
    assert MAX_AGE_ROLE == "WATCHDOG_ONLY"
    assert MAX_AGE_ENFORCEMENT_ENABLED is False
    result = apply_regime_meta_gate_v1(_input())
    assert result.max_age_consulted is False
    payload = load_layer_config_v1()
    assert payload["max_age_enforcement_enabled"] is False
    assert payload["max_age_can_change_selection"] is False


def test_no_silent_threshold_mutation_claim() -> None:
    result = apply_regime_meta_gate_v1(_input())
    assert result.silent_threshold_mutation is False
    payload = dict(load_layer_config_v1())
    payload["silent_threshold_mutation"] = True
    with pytest.raises(RegimeMetaGatedSelectionError, match="silent_threshold_mutation"):
        validate_layer_config_v1(payload)


def test_r2_invariants_still_pass() -> None:
    claims = evaluate_r2_registry_suitability_selection_v1()
    assert claims["verdict"] == "PASS_R2_STRATEGY_REGISTRY_SUITABILITY_SELECTION_V1"
    assert claims["second_strategy_registry_risk"] == "NONE_SRC_STRATEGIES_REGISTRY_ONLY"
    assert claims["max_age_enforcement_enabled"] is False


def test_verifier_pass_single_owners() -> None:
    claims = evaluate_r3_regime_meta_gated_selection_v1()
    assert claims["verdict"] == "PASS_R3_REGIME_META_GATED_SELECTION_V1"
    assert claims["r2_verdict"] == "PASS_R2_STRATEGY_REGISTRY_SUITABILITY_SELECTION_V1"
    assert claims["raw_llm_trading_authority"] == "PERMANENT_NON_AUTHORITY"
    assert claims["promotion_authority"] is False
    assert claims["runtime_authority_impact"] == "NONE"
    assert claims["second_strategy_registry_risk"] == "NONE_SRC_STRATEGIES_REGISTRY_ONLY"
    assert claims["second_selection_path_risk"] == "NONE_SUITABILITY_SELECT_PLUS_R2_NON_AUTHORITY"
    assert (
        claims["second_regime_meta_authority_risk"]
        == "NONE_R3_GATE_ONLY_RESEARCH_SWITCH_NON_AUTHORITY"
    )
    assert len(str(claims["config_digest"])) == 64
    assert len(str(claims["gate_result_digest"])) == 64
