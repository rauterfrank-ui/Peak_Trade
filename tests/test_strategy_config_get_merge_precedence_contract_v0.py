"""In-memory contract for ``StrategyConfig.get`` / ``to_dict`` (v0).

No ``ConfigRegistry``, TOML, filesystem, subprocess, env, or network.

Prod definition: ``src.core.config_registry.StrategyConfig``.
"""

from __future__ import annotations

from src.core.config_registry import StrategyConfig


def test_strategy_config_get_params_only_contract_v0() -> None:
    cfg = StrategyConfig(
        name="s",
        active=True,
        params={"alpha": 1},
        defaults={},
        metadata=None,
    )
    assert cfg.get("alpha") == 1
    assert cfg.get("alpha", 99) == 1


def test_strategy_config_get_defaults_fallback_contract_v0() -> None:
    cfg = StrategyConfig(
        name="s",
        active=False,
        params={},
        defaults={"gamma": "x"},
    )
    assert cfg.get("gamma") == "x"
    assert cfg.get("gamma", "fallback") == "x"


def test_strategy_config_get_params_precedence_over_defaults_contract_v0() -> None:
    cfg = StrategyConfig(
        name="s",
        active=True,
        params={"risk": "low"},
        defaults={"risk": "high"},
    )
    assert cfg.get("risk") == "low"


def test_strategy_config_get_missing_returns_call_default_contract_v0() -> None:
    cfg = StrategyConfig(
        name="s",
        active=True,
        params={},
        defaults={},
    )
    assert cfg.get("missing") is None
    assert cfg.get("missing", sentinel := object()) is sentinel


def test_strategy_config_to_dict_merges_defaults_then_params_contract_v0() -> None:
    defaults = {"a": 1, "b": 2}
    params = {"b": 3, "c": 4}
    cfg = StrategyConfig(name="blend", active=True, params=params, defaults=defaults)
    assert cfg.to_dict() == {"a": 1, "b": 3, "c": 4}


def test_strategy_config_to_dict_does_not_mutate_internal_maps_contract_v0() -> None:
    defaults = {"k": {"inner": 0}}
    params = {"k": {"inner": 1}}
    cfg = StrategyConfig(name="m", active=True, params=params, defaults=defaults)
    before_params = dict(cfg.params)
    before_defaults = dict(cfg.defaults)
    _ = cfg.to_dict()
    assert cfg.params == before_params
    assert cfg.defaults == before_defaults


def test_strategy_config_to_dict_output_isolation_nested_mutation_contract_v0() -> None:
    defaults = {"a": {"x": 1}, "shared": [1, 2]}
    params = {"b": {"y": 2}, "shared": [9]}
    cfg = StrategyConfig(name="iso", active=True, params=params, defaults=defaults)
    out = cfg.to_dict()

    out["a"]["x"] = 999
    out["b"]["y"] = 888
    out["shared"].append(7)

    assert cfg.defaults["a"]["x"] == 1
    assert cfg.params["b"]["y"] == 2
    assert cfg.defaults["shared"] == [1, 2]
    assert cfg.params["shared"] == [9]
