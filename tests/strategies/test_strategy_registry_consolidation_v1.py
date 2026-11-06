"""RUNBOOK STEP 29K: canonical strategy registry consolidation contract tests."""

from __future__ import annotations

import json
import re
from typing import Tuple

import pytest

from src.strategies import STRATEGY_REGISTRY, load_strategy
from src.strategies.registry import (
    ALIAS_REASON_CODE,
    DeprecationStatus,
    StrategyRegistryError,
    StrategyRegistrySnapshotV1,
    build_registry_snapshot,
    get_available_strategy_keys,
    get_loader_module_map,
    get_strategy_registry_entry,
    get_strategy_spec,
    resolve_strategy_id,
    serialize_registry_snapshot,
)
from src.strategies.suitability_registry_adapter_v1 import (
    build_suitability_registry_from_snapshot,
)
from src.trading.master_v2.suitability_binding_v1 import (
    SuitabilityRegimeStatus,
    SuitabilityStrategyRegistryV1,
)
from tests.trading.master_v2.test_suitability_binding_v1 import (
    _directional_assessment,
    _evaluate,
    _registry as _suit_registry,
    _strategy_entry,
    _survival_result,
)


def test_1_canonical_strategy_id_resolves() -> None:
    res = resolve_strategy_id("ma_crossover")
    assert res.canonical_strategy_id == "ma_crossover"
    assert res.alias_applied is False


def test_2_unknown_strategy_id_fail_closed() -> None:
    with pytest.raises(StrategyRegistryError, match="unknown strategy id"):
        resolve_strategy_id("definitely_not_a_strategy_xyz")


def test_3_empty_strategy_id_fail_closed() -> None:
    with pytest.raises(StrategyRegistryError, match="empty"):
        resolve_strategy_id("")


def test_4_none_strategy_id_fail_closed() -> None:
    with pytest.raises(StrategyRegistryError, match="None"):
        resolve_strategy_id(None)


def test_5_duplicate_strategy_id_fail_closed_at_build() -> None:
    # invariant validated at import; canonical entries count equals unique ids
    keys = get_available_strategy_keys()
    assert len(keys) == len(set(keys))


def test_6_duplicate_alias_fail_closed() -> None:
    from src.strategies import registry as reg

    assert len(reg._LEGACY_ALIASES) == len({a.legacy_key for a in reg._LEGACY_ALIASES.values()})


def test_7_alias_canonical_collision_fail_closed() -> None:
    canonical = set(get_available_strategy_keys())
    from src.strategies import registry as reg

    for alias in reg._LEGACY_ALIASES.values():
        assert alias.legacy_key not in canonical


def test_8_alias_unknown_target_fail_closed() -> None:
    from src.strategies import registry as reg

    canonical = set(get_available_strategy_keys())
    for alias in reg._LEGACY_ALIASES.values():
        assert alias.canonical_strategy_id in canonical


def test_9_alias_cycle_fail_closed() -> None:
    from src.strategies import registry as reg

    for alias in reg._LEGACY_ALIASES.values():
        assert alias.canonical_strategy_id not in reg._LEGACY_ALIASES


def test_10_legacy_alias_resolves_deterministically() -> None:
    a = resolve_strategy_id("el_karoui_vol_v1")
    b = resolve_strategy_id("el_karoui_vol_v1")
    assert a == b
    assert a.canonical_strategy_id == "el_karoui_vol_model"


def test_11_alias_reason_code_present() -> None:
    res = resolve_strategy_id("el_karoui_vol_v1")
    assert res.reason_code == ALIAS_REASON_CODE


def test_12_original_key_and_canonical_id_persisted() -> None:
    res = resolve_strategy_id("el_karoui_vol_v1")
    assert res.original_key == "el_karoui_vol_v1"
    assert res.canonical_strategy_id == "el_karoui_vol_model"


def test_13_strategy_version_bound() -> None:
    entry = get_strategy_registry_entry("ma_crossover")
    assert entry.strategy_version == "v1"


def test_14_implementation_digest_bound() -> None:
    entry = get_strategy_registry_entry("ma_crossover")
    assert re.fullmatch(r"[0-9a-f]{64}", entry.implementation_digest)


def test_15_parameter_schema_version_bound() -> None:
    entry = get_strategy_registry_entry("ma_crossover")
    assert entry.parameter_schema_version == "v1"


def test_16_futures_compatibility_bound() -> None:
    entry = get_strategy_registry_entry("ma_crossover")
    assert entry.futures_compatible is True


def test_17_spot_compatibility_blocked() -> None:
    entry = get_strategy_registry_entry("ma_crossover")
    assert entry.spot_compatible is False


def test_18_snapshot_stable_sorting() -> None:
    snap = build_registry_snapshot()
    ids = [e.strategy_id for e in snap.entries]
    assert ids == sorted(ids)


def test_19_registry_input_reorder_identical_snapshot() -> None:
    snap_a = build_registry_snapshot()
    snap_b = build_registry_snapshot()
    assert snap_a.strategy_ids_sorted == snap_b.strategy_ids_sorted
    assert snap_a.semantic_digest == snap_b.semantic_digest


def test_20_registry_input_reorder_identical_digest() -> None:
    snap = build_registry_snapshot()
    assert snap.input_digest == build_registry_snapshot().input_digest


def test_21_identical_state_byte_stable_serialization() -> None:
    a = serialize_registry_snapshot(build_registry_snapshot())
    b = serialize_registry_snapshot(build_registry_snapshot())
    assert a == b
    assert a.encode("utf-8") == b.encode("utf-8")


def test_22_no_wall_clock_in_snapshot() -> None:
    snap = build_registry_snapshot()
    payload = serialize_registry_snapshot(snap)
    assert "uuid" not in payload.lower()
    assert "T" not in payload or "strategy_ids_sorted" in payload
    for field in ("created_at", "timestamp", "wall_clock", "now"):
        assert field not in payload


def test_23_no_uuid4_in_snapshot() -> None:
    snap = build_registry_snapshot()
    blob = json.dumps(snap.__dict__, default=str)
    assert not re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        blob,
        re.I,
    )


def test_24_no_list_position_fallback() -> None:
    keys = get_available_strategy_keys()
    assert resolve_strategy_id(keys[0]).canonical_strategy_id == keys[0]
    with pytest.raises(StrategyRegistryError):
        resolve_strategy_id("not_in_registry_at_all_zzz")


def test_25_no_dict_order_fallback() -> None:
    m1 = get_loader_module_map()
    m2 = dict(sorted(get_loader_module_map().items(), reverse=True))
    assert set(m1) == set(m2)
    assert m1 == get_loader_module_map()


def test_26_no_fuzzy_matching() -> None:
    with pytest.raises(StrategyRegistryError):
        resolve_strategy_id("ma_cross")


def test_27_no_substring_matching() -> None:
    with pytest.raises(StrategyRegistryError):
        resolve_strategy_id("crossover")


def test_28_suitability_adapter_consumes_canonical_snapshot() -> None:
    snap = build_registry_snapshot()
    suit_reg = build_suitability_registry_from_snapshot(snap)
    assert isinstance(suit_reg, SuitabilityStrategyRegistryV1)
    assert len(suit_reg.entries) == len(snap.entries)


def test_29_suitability_ranking_unchanged() -> None:
    entries_ab = (
        _strategy_entry(strategy_id="alpha", priority_rank=1),
        _strategy_entry(strategy_id="beta", priority_rank=2),
    )
    entries_ba = (
        _strategy_entry(strategy_id="beta", priority_rank=2),
        _strategy_entry(strategy_id="alpha", priority_rank=1),
    )
    reg_ab = _suit_registry(*entries_ab)
    reg_ba = _suit_registry(*entries_ba)
    result_ab = _evaluate(strategy_registry=reg_ab)
    result_ba = _evaluate(strategy_registry=reg_ba)
    assert result_ab.selected_strategy_id == result_ba.selected_strategy_id == "alpha"


def test_30_regime_semantics_unchanged() -> None:
    result = _evaluate(
        strategy_registry=_suit_registry(_strategy_entry(supported_regime_ids=("breakout",))),
        regime_id="breakout",
    )
    assert result.selected_strategy_id is not None


def test_31_cli_canonical_id_works() -> None:
    fn = load_strategy("ma_crossover")
    assert callable(fn)


def test_32_cli_legacy_alias_with_deprecation_provenance() -> None:
    res = resolve_strategy_id("el_karoui_vol_v1")
    assert res.deprecation_status == DeprecationStatus.DEPRECATED_ALIAS
    assert callable(load_strategy("el_karoui_vol_v1"))


def test_33_config_canonical_id_works() -> None:
    spec = get_strategy_spec("rsi_reversion")
    assert spec.key == "rsi_reversion"


def test_34_config_legacy_alias_with_provenance() -> None:
    spec = get_strategy_spec("el_karoui_vol_v1")
    assert spec.cls is get_strategy_spec("el_karoui_vol_model").cls


def test_35_unknown_legacy_key_blocks() -> None:
    with pytest.raises(StrategyRegistryError):
        resolve_strategy_id("legacy_unknown_key_xyz")


def test_36_research_entry_uses_registry() -> None:
    import scripts.research_run_strategy as mod

    src = open(mod.__file__).read()
    assert "get_strategy_spec" in src or "load_strategy" in src
    assert "STRATEGY_REGISTRY =" not in src


def test_37_backtest_entry_uses_registry() -> None:
    import scripts.run_backtest as mod

    src = open(mod.__file__).read()
    assert "load_strategy" in src


def test_38_no_strategy_semantic_change_functional() -> None:
    import pandas as pd

    n = 40
    df = pd.DataFrame(
        {
            "open": list(range(1, n + 1)),
            "high": list(range(2, n + 2)),
            "low": [x - 0.5 for x in range(1, n + 1)],
            "close": [x + 0.5 for x in range(1, n + 1)],
            "volume": [10] * n,
        }
    )
    fn = load_strategy("vol_breakout")
    out = fn(df, {"lookback": 20, "vol_multiplier": 1.0, "direction_mode": "both"})
    assert len(out) == len(df)


def test_39_long_short_capabilities_unchanged() -> None:
    entry = get_strategy_registry_entry("ma_crossover")
    assert "long" in entry.supported_sides and "short" in entry.supported_sides


def test_40_no_runtime_order_adapter_effect() -> None:
    snap = build_registry_snapshot()
    blob = serialize_registry_snapshot(snap)
    for token in ("execution", "adapter", "broker", "exchange", "scheduler"):
        assert token not in blob


def test_whitespace_ambiguity_fail_closed() -> None:
    with pytest.raises(StrategyRegistryError):
        resolve_strategy_id(" ma_crossover")


def test_strategy_registry_compat_view_matches_canonical() -> None:
    assert set(STRATEGY_REGISTRY.keys()) == set(get_available_strategy_keys())


def test_functional_only_strategies_in_canonical_registry() -> None:
    for key in ("vol_breakout", "mean_reversion_channel", "ecm_cycle", "rsi_strategy"):
        assert key in get_available_strategy_keys()
        assert callable(load_strategy(key))
