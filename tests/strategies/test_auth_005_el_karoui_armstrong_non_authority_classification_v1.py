"""AUTH-005: El Karoui / Armstrong Non-Authority classification contracts."""

from __future__ import annotations

import pytest

from src.experiments.armstrong_elkaroui_combi_experiment import (
    ALLOWED_ENVIRONMENTS as COMBI_ALLOWED_ENVIRONMENTS,
    RUN_TYPE_ARMSTRONG_ELKAROUI_COMBI,
)
from src.strategies.armstrong.armstrong_cycle_strategy import ArmstrongCycleStrategy
from src.strategies.el_karoui.el_karoui_vol_model_strategy import ElKarouiVolatilityStrategy
from src.strategies.registry import (
    _STRATEGY_REGISTRY,
    get_strategy_registry_entry,
    get_strategy_spec,
)


_RESEARCH_KEYS = ("armstrong_cycle", "el_karoui_vol_model")


@pytest.mark.parametrize("key", _RESEARCH_KEYS)
def test_auth005_registry_spec_is_research_only_non_live(key: str) -> None:
    spec = get_strategy_spec(key)
    assert spec.is_live_ready is False
    assert spec.tier == "r_and_d"
    assert "live" not in spec.allowed_environments
    assert "paper" not in spec.allowed_environments
    assert set(spec.allowed_environments) <= {"offline_backtest", "research", "backtest"}
    assert "offline_backtest" in spec.allowed_environments
    assert "research" in spec.allowed_environments
    assert "Non-Authority" in spec.description or "R&D" in spec.description


@pytest.mark.parametrize("key", _RESEARCH_KEYS)
def test_auth005_canonical_entry_has_no_live_ready_capability_tag(key: str) -> None:
    entry = get_strategy_registry_entry(key)
    assert "live_ready" not in entry.capability_tags
    assert "r_and_d" in entry.capability_tags
    assert "production" not in entry.capability_tags


def test_auth005_class_level_flags_match_registry() -> None:
    assert ArmstrongCycleStrategy.IS_LIVE_READY is False
    assert ArmstrongCycleStrategy.TIER == "r_and_d"
    assert ElKarouiVolatilityStrategy.IS_LIVE_READY is False
    assert ElKarouiVolatilityStrategy.TIER == "r_and_d"

    arm = get_strategy_spec("armstrong_cycle")
    elk = get_strategy_spec("el_karoui_vol_model")
    assert arm.is_live_ready is ArmstrongCycleStrategy.IS_LIVE_READY
    assert elk.is_live_ready is ElKarouiVolatilityStrategy.IS_LIVE_READY
    assert arm.tier == ArmstrongCycleStrategy.TIER
    assert elk.tier == ElKarouiVolatilityStrategy.TIER


def test_auth005_registry_rejects_live_ready_true_posture_for_research_keys() -> None:
    """Negative: productive live posture must not remain after AUTH-005."""
    for key in _RESEARCH_KEYS:
        spec = get_strategy_spec(key)
        assert spec.is_live_ready is not True
        assert spec.tier != "production"
        assert "live" not in spec.allowed_environments


def test_auth005_no_execution_eligible_metadata_on_research_specs() -> None:
    """Schema has no execution_eligible field; live gate uses is_live_ready=False."""
    for key in _RESEARCH_KEYS:
        spec = get_strategy_spec(key)
        assert (
            not hasattr(spec, "execution_eligible") or getattr(spec, "execution_eligible") is False
        )
        assert spec.is_live_ready is False


def test_auth005_combi_experiment_not_registered_as_strategy_producer() -> None:
    assert RUN_TYPE_ARMSTRONG_ELKAROUI_COMBI not in _STRATEGY_REGISTRY
    assert "armstrong_elkaroui_combi" not in _STRATEGY_REGISTRY
    assert set(COMBI_ALLOWED_ENVIRONMENTS) <= {"offline_backtest", "research"}


def test_auth005_ecm_cycle_is_functional_only_not_oop_live_spec() -> None:
    with pytest.raises(KeyError):
        get_strategy_spec("ecm_cycle")
    entry = get_strategy_registry_entry("ecm_cycle")
    assert "functional" in entry.capability_tags
    assert "live_ready" not in entry.capability_tags


def test_auth005_no_dynamic_scope_or_agreement_override_fields_on_specs() -> None:
    forbidden = (
        "dynamic_scope_mutation",
        "agreement_override",
        "risk_authority",
        "sizing_authority",
        "canonical_chain_bound",
        "direct_long_short_authority",
    )
    for key in _RESEARCH_KEYS:
        spec = get_strategy_spec(key)
        for field in forbidden:
            assert not hasattr(spec, field)


def test_auth005_field_mapping_documented_via_existing_schema() -> None:
    """
    Target classification → existing StrategySpec fields:
    - research_only / LIVE_READY=false → is_live_ready=False + tier='r_and_d'
    - execution_eligible=false → is_live_ready=False and 'live' not in allowed_environments
    - authority=NON_AUTHORITY → description + class docstrings (no parallel schema)
    - canonical_chain_bound=false → not claimed by registry; absence of live envs
    """
    for key in _RESEARCH_KEYS:
        spec = get_strategy_spec(key)
        assert (spec.is_live_ready is False) and (spec.tier == "r_and_d")
