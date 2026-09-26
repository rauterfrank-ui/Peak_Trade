"""B10 robustness/stress proof tests for CURRENT Peak_Trade economic ranking."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.ops.peak_trade_economic_ranking_runtime_v1.economic_rank_v1 import (
    classify_and_rank_economic_candidates_v1,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import RankingFeatureValueState
from src.ops.peak_trade_ranking_matrix_policy_v1 import (
    AMPLITUDE_POLICY_ID,
    VOLATILITY_POLICY_ID,
)
from src.ops.peak_trade_robustness_and_stress_v1.constants_v1 import (
    CAP23_RERANK_COUNT,
    CAP23_RESCORE_COUNT,
    CAP23_SOLE_SELECTION_OWNER,
    INFRASTRUCTURE_CENSUS_V1,
)
from src.ops.peak_trade_robustness_and_stress_v1.robustness_v1 import (
    _evaluate_scenario_v1,
    _manual_feature_snapshot_v1,
    _scenario_specs_v1,
    _universe_v1,
    build_b10_robustness_report_v1,
    validate_b10_robustness_report_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
    compute_b03_ratified_raw_features_pure_v1,
)
import src.ops.peak_trade_robustness_and_stress_v1.robustness_v1 as b10_module


@pytest.fixture(scope="module")
def b10_report() -> dict[str, object]:
    report = build_b10_robustness_report_v1()
    validate_b10_robustness_report_v1(report)
    return report


def _scenario(report: dict[str, object], scenario_id: str) -> dict[str, object]:
    scenarios = report["scenarios"]
    assert isinstance(scenarios, list)
    for row in scenarios:
        if row["scenario_id"] == scenario_id:
            return row
    raise AssertionError(f"missing scenario {scenario_id}")


def test_b10_census_reuses_authoritative_b05_b06_surfaces(b10_report: dict[str, object]) -> None:
    census = {(row["surface"], row["classification"]) for row in INFRASTRUCTURE_CENSUS_V1}
    assert ("ranking feature production", "AUTHORITATIVE_REUSED") in census
    assert ("economic ranking", "AUTHORITATIVE_REUSED") in census
    assert "compute_b03_ratified_raw_features_pure_v1" in str(
        b10_report["authoritative_feature_implementation_reused"]
    )
    assert "classify_and_rank_economic_candidates_v1" in str(
        b10_report["authoritative_ranking_implementation_reused"]
    )


def test_walk_forward_preserves_no_lookahead_and_records_transitions(
    b10_report: dict[str, object],
) -> None:
    walk = b10_report["walk_forward"]
    assert walk["proven"] is True
    assert walk["window_count"] == 4
    assert len(walk["top_rank_sequence"]) == 4
    for row in b10_report["scenarios"]:
        if row["domain"] == "WALK_FORWARD":
            assert row["no_lookahead_preserved"] is True
            assert row["rank_witness"]
            assert row["result_digest"]


def test_identical_scenario_is_reproducible(b10_report: dict[str, object]) -> None:
    determinism = b10_report["determinism"]
    assert determinism["proven"] is True
    assert determinism["all_compared_outputs_equal"] is True
    assert all(determinism["equality"].values())


def test_exact_tie_uses_ratified_identity_tie_break(b10_report: dict[str, object]) -> None:
    tied = _scenario(b10_report, "sensitivity_exact_tie")
    assert [row["venue_native_id"] for row in tied["rank_witness"]] == [
        "ADA-USDT-SWAP",
        "ETH-USDT-SWAP",
        "SOL-USDT-SWAP",
    ]
    assert tied["tie_count"] == 3


def test_near_tie_perturbation_is_deterministic_and_explainable(
    b10_report: dict[str, object],
) -> None:
    near = _scenario(b10_report, "sensitivity_near_tie_small_perturbation")
    assert near["finding_classification"] == "EXPECTED_BEHAVIOR"
    assert near["rank_witness"]
    for ranked in near["rank_witness"]:
        assert ranked["normalized_features"]
        assert ranked["score_contributions"]


def test_single_feature_dominance_analysis_shows_both_features_can_affect_order(
    b10_report: dict[str, object],
) -> None:
    dominance = b10_report["single_feature_dominance"]
    assert dominance["structurally_suppressed"] is False
    assert dominance["dominant_feature"] == "NONE"
    assert dominance["owner_policy_decision_required"] is False
    assert dominance["volatility_only_order"] == dominance["amplitude_only_order"]
    ranges = dominance["contribution_ranges"]
    assert ranges[VOLATILITY_POLICY_ID]["max"] > ranges[VOLATILITY_POLICY_ID]["min"]
    assert ranges[AMPLITUDE_POLICY_ID]["max"] > ranges[AMPLITUDE_POLICY_ID]["min"]


def test_missing_and_insufficient_required_inputs_fail_closed(
    b10_report: dict[str, object],
) -> None:
    assert b10_report["missing_data_stress"]["proven"] is True
    for scenario_id in ("missing_mark", "insufficient_lookback", "non_contiguous_finalized_bars"):
        row = _scenario(b10_report, scenario_id)
        assert row["exclusion_counts"]
        assert row["productive_ok"] is True or row["productive_failure_codes"]
        assert row["finding_classification"] == "EXPECTED_BEHAVIOR"
    assert b10_report["missing_data_stress"]["no_guessed_value"] is True
    assert b10_report["missing_data_stress"]["no_silent_default"] is True
    assert b10_report["missing_data_stress"]["no_synthetic_rank"] is True
    assert (
        b10_report["missing_data_stress"]["no_venue_order_fallback_as_economic_substitute"] is True
    )


def test_stale_and_invalid_inputs_follow_current_semantics(b10_report: dict[str, object]) -> None:
    stale = _scenario(b10_report, "stale_unratified_observed_age_classified")
    assert stale["finding_classification"] == "UNRATIFIED_POLICY_GAP"
    assert b10_report["stale_invalid_stress"]["stale_max_age_policy"].startswith(
        "UNRATIFIED_POLICY_GAP"
    )
    invalid_ts = _scenario(b10_report, "invalid_timestamp_ordering")
    non_finite = _scenario(b10_report, "non_finite_mark_rejected_by_feature_production")
    assert invalid_ts["exclusion_counts"]
    assert non_finite["exclusion_counts"]


def test_non_finite_ready_feature_cannot_enter_economic_ranking_silently() -> None:
    universe = _universe_v1()
    snapshot = _manual_feature_snapshot_v1(
        {
            "ETH-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.1, AMPLITUDE_POLICY_ID: 0.1},
            "SOL-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.2, AMPLITUDE_POLICY_ID: 0.2},
            "ADA-USDT-SWAP": {VOLATILITY_POLICY_ID: 0.3, AMPLITUDE_POLICY_ID: 0.3},
        }
    )
    eth = snapshot.instruments[0]
    bad_raw = replace(eth.raw_features[0], raw_value=float("inf"))
    bad_eth = replace(eth, raw_features=(bad_raw, eth.raw_features[1]))
    bad_snapshot = replace(
        snapshot,
        instruments=(bad_eth, *snapshot.instruments[1:]),
    )
    result = classify_and_rank_economic_candidates_v1(
        universe_snapshot=universe.to_dict(),
        feature_production_snapshot=bad_snapshot,
    )
    assert result.exclusion_counts
    ranked_ids = [row.canonical_instrument_id for row in result.ranked]
    assert ranked_ids
    assert bad_eth.canonical_instrument_id not in ranked_ids


def test_extreme_valid_values_remain_deterministic(b10_report: dict[str, object]) -> None:
    assert b10_report["outlier_stress"]["proven"] is True
    one = _scenario(b10_report, "extreme_valid_one_candidate_shock")
    market = _scenario(b10_report, "extreme_valid_market_wide_shock")
    assert one["result_digest"]
    assert market["result_digest"]
    assert b10_report["outlier_stress"]["invalid_non_finite_output_count"] == 0


def test_config_version_mismatch_is_detected_in_b10_witness(
    b10_report: dict[str, object],
) -> None:
    mismatch = _scenario(b10_report, "config_mismatch_detection_witness")
    assert mismatch["config_identity"]["ranking_policy_version"] == "B10_CONFIG_MISMATCH_INJECTION"
    clean = _scenario(b10_report, "walk_forward_window_01")
    assert mismatch["config_identity"] != clean["config_identity"]


def test_profile_only_fields_and_cap23_authority_remain_inert(
    b10_report: dict[str, object],
) -> None:
    authority = b10_report["authority_preservation"]
    assert CAP23_RESCORE_COUNT == 0
    assert CAP23_RERANK_COUNT == 0
    assert CAP23_SOLE_SELECTION_OWNER is True
    assert authority["cap23_rescore_count"] == 0
    assert authority["cap23_rerank_count"] == 0
    assert authority["cap23_sole_selection_owner"] is True
    assert authority["profile_only_selection_effect"] is False
    assert authority["max_positions_effective"] == 1
    assert authority["multi_future_runtime_authorized"] is False
    assert authority["live_external_effect_authorized"] is False


def test_harness_uses_authoritative_feature_and_ranking_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"feature": 0, "ranking": 0}
    original_feature = b10_module.produce_ranking_feature_production_snapshot_v1
    original_ranking = b10_module.classify_and_rank_economic_candidates_v1

    def feature_spy(*args: object, **kwargs: object) -> object:
        calls["feature"] += 1
        return original_feature(*args, **kwargs)

    def ranking_spy(*args: object, **kwargs: object) -> object:
        calls["ranking"] += 1
        return original_ranking(*args, **kwargs)

    monkeypatch.setattr(b10_module, "produce_ranking_feature_production_snapshot_v1", feature_spy)
    monkeypatch.setattr(b10_module, "classify_and_rank_economic_candidates_v1", ranking_spy)
    spec = _scenario_specs_v1()[0]
    row = _evaluate_scenario_v1(spec)
    assert row["feature_witness"]
    marks = tuple(str(100 + idx) for idx in range(61))
    pure_features = compute_b03_ratified_raw_features_pure_v1(marks)
    assert all(feature.state == RankingFeatureValueState.READY for feature in pure_features)
    assert calls == {"feature": 1, "ranking": 1}
