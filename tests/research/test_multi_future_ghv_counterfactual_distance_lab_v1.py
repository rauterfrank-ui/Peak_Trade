from __future__ import annotations

from decimal import Decimal

import pytest

from research.multi_future_ghv_counterfactual_distance_lab_v1.behavioral_models_v1 import (
    LEGACY_FIXED_ADVERSE,
    MODEL_MANIFEST,
    resolve_behavioral_layer_c_distances_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.contract_profiles_v1 import (
    synthetic_contract_profile_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.counterfactual_replay_v1 import (
    run_counterfactual_integrated_replay_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.distance_geometry_v1 import (
    evaluate_distance_geometry_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.replay_fixtures_v1 import (
    build_integrated_replay_input_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.safety_v1 import assert_lab_safety_v1
from research.multi_future_ghv_counterfactual_distance_lab_v1.synthetic_market_v1 import (
    build_future_profile_catalog_v1,
    generate_price_path_v1,
    generalization_future_profile_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.trading_logic_digest_v1 import (
    compare_trading_logic_preservation_v1,
    run_trading_logic_reference_replay_v1,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    resolve_layer_c_event_distances_from_mark_and_volatility_v1,
)


def test_safety_assert_post_disabled() -> None:
    snap = assert_lab_safety_v1(real_post_count=0)
    assert snap.post_allowed is False
    assert snap.real_post_count == 0


def test_synthetic_profile_determinism() -> None:
    p = generalization_future_profile_v1("MICRO_TREND")
    a = generate_price_path_v1(
        p0=0.2, sigma=0.02, profile=p, regime_id="R02", seed=7, mode="MODE_B", steps=20
    )
    b = generate_price_path_v1(
        p0=0.2, sigma=0.02, profile=p, regime_id="R02", seed=7, mode="MODE_B", steps=20
    )
    assert a == b


def test_positive_price_invariant() -> None:
    p = generalization_future_profile_v1("MICRO_JUMP")
    path = generate_price_path_v1(
        p0=0.2, sigma=0.5, profile=p, regime_id="R10", seed=1, mode="MODE_B", steps=100
    )
    assert all(x > 0 for x in path)


def test_layer_c_resolver_equality_with_current_owner() -> None:
    mark, vol = 3500.0, 0.38
    owner = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=mark, volatility_estimate=vol
    )
    lab = resolve_behavioral_layer_c_distances_v1(
        model_id="MODEL_B_CURRENT_LAYER_C", mark_price=mark, volatility_estimate=vol
    )
    assert owner == lab


def test_legacy_fixed_80_negative_control() -> None:
    lab = resolve_behavioral_layer_c_distances_v1(
        model_id="MODEL_A_LEGACY_FIXED_80", mark_price=100000.0, volatility_estimate=0.01
    )
    assert lab.ok
    assert lab.adverse_exit_distance == LEGACY_FIXED_ADVERSE


def test_same_normalized_path_mode_a_scaling() -> None:
    rels = []
    for p0 in (0.1, 10.0, 1000.0):
        g = evaluate_distance_geometry_v1(
            model_id="MODEL_B_CURRENT_LAYER_C",
            mark_price=p0,
            volatility_estimate=0.04,
            contract=synthetic_contract_profile_v1(future_profile_id="fp", p0=p0),
        )
        rels.append(g["DISTANCE_RELATIVE_TO_SIGMA_P"])
    assert rels[0] == pytest.approx(rels[1])
    assert rels[1] == pytest.approx(rels[2])


def test_trading_logic_control_lane_equivalence() -> None:
    inp = build_integrated_replay_input_v1(
        instrument_id="inst-control",
        mark_price=3500.0,
        volatility_estimate=0.38,
        price_path=(3500.0, 3570.0),
    )
    _, d1 = run_trading_logic_reference_replay_v1(inp)
    _, d2 = run_trading_logic_reference_replay_v1(inp)
    pres = compare_trading_logic_preservation_v1(d1, d2)
    assert pres["TRADING_LOGIC_PRESERVATION_PASS"] is True


def test_counterfactual_lane_model_b_matches_reference() -> None:
    inp = build_integrated_replay_input_v1(
        instrument_id="inst-b",
        mark_price=3500.0,
        volatility_estimate=0.38,
        price_path=(3500.0, 3570.0),
    )
    ref, d_ref = run_trading_logic_reference_replay_v1(inp)
    cf = run_counterfactual_integrated_replay_v1(inp, model_id="MODEL_B_CURRENT_LAYER_C")
    from research.multi_future_ghv_counterfactual_distance_lab_v1.trading_logic_digest_v1 import (
        replay_semantic_digest_v1,
    )

    assert replay_semantic_digest_v1(ref) == replay_semantic_digest_v1(cf)


def test_no_symbol_specific_model_parameters() -> None:
    for spec in MODEL_MANIFEST.values():
        assert spec.symbol_specific is False


def test_diagnostic_invariant_not_in_behavioral_manifest() -> None:
    assert "DIAGNOSTIC_CMC_VS_BAND_MISMATCH" not in MODEL_MANIFEST


def test_regime_catalog_non_empty() -> None:
    assert len(build_future_profile_catalog_v1()) >= 100


def test_contract_metadata_validity() -> None:
    c = synthetic_contract_profile_v1(future_profile_id="x", p0=1.0)
    assert c.tick_size > 0
    assert c.min_notional >= Decimal("5")
