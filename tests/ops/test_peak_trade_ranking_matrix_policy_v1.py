"""B03 Peak Trade Ranking Matrix Policy V1 governance persistence contracts."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.peak_trade_ranking_matrix_policy_v1 import (
    AMPLITUDE_POLICY_ID,
    AMPLITUDE_WEIGHT,
    B03_RATIFIED,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    CAP22_RANKING_POLICY_AUTHORITY,
    CROSS_UNIVERSE_AUTHORITY,
    ECONOMIC_RANK_ACTIVATED,
    INPUT2_MAX_AGE_SECONDS,
    INPUT2_MAX_AGE_SECONDS_RATIFIED,
    POLICY_ID,
    PRODUCTIVE_ECONOMIC_RANK_ACTIVATION,
    PRODUCTIVE_SELECTION_OWNER,
    RANKING_OBJECTIVE,
    SCORE_CONSTRUCTION,
    SOLE_PRODUCTIVE_SELECTION_OWNER,
    VOLATILITY_POLICY_ID,
    VOLATILITY_WEIGHT,
    B04_IMPLEMENTED,
    B05_IMPLEMENTED,
    B06_IMPLEMENTED,
    RUNTIME_WIRING_ADDED_BY_THIS_SLICE,
    build_ranking_matrix_policy_semantic_payload_v1,
    classify_peak_trade_ranking_matrix_policy_v1,
    compute_ranking_matrix_policy_digest_v1,
    validate_peak_trade_ranking_matrix_policy_declaration_v1,
)


def test_b03_policy_ratified_constants() -> None:
    assert POLICY_ID == "PEAK_TRADE_RANKING_MATRIX_POLICY_V1"
    assert B03_RATIFIED is True
    assert RANKING_OBJECTIVE == "BALANCED_MOVEMENT_STRUCTURE"
    assert VOLATILITY_POLICY_ID == "CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1"
    assert AMPLITUDE_POLICY_ID == "CAP22_PT1M_MARK_MID_RELATIVE_RANGE_V1"
    assert SCORE_CONSTRUCTION == ("EQUAL_WEIGHT_CROSS_SECTIONAL_MIDRANK_PERCENTILE_COMPOSITE_V1")
    assert VOLATILITY_WEIGHT == 0.5
    assert AMPLITUDE_WEIGHT == 0.5


def test_freshness_pin_unratified_and_activation_false() -> None:
    assert INPUT2_MAX_AGE_SECONDS_RATIFIED is False
    assert INPUT2_MAX_AGE_SECONDS == "UNRATIFIED"
    assert PRODUCTIVE_ECONOMIC_RANK_ACTIVATION is False
    assert ECONOMIC_RANK_ACTIVATED is False


def test_cap23_sole_selection_owner_and_no_cross_universe() -> None:
    assert SOLE_PRODUCTIVE_SELECTION_OWNER is True
    assert PRODUCTIVE_SELECTION_OWNER == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    assert CROSS_UNIVERSE_AUTHORITY == "NONE"
    assert CAP22_RANKING_POLICY_AUTHORITY is True


def test_policy_digest_deterministic() -> None:
    d1 = compute_ranking_matrix_policy_digest_v1()
    d2 = compute_ranking_matrix_policy_digest_v1()
    assert d1 == d2
    assert len(d1) == 64
    payload = build_ranking_matrix_policy_semantic_payload_v1()
    assert "policy_digest" not in payload
    assert payload["input2_max_age_seconds_ratified"] is False
    assert payload["input2_max_age_seconds"] == "UNRATIFIED"
    assert payload["volatility_weight"] == 0.5
    assert payload["amplitude_weight"] == 0.5


def test_classify_exports_digest() -> None:
    summary = classify_peak_trade_ranking_matrix_policy_v1()
    assert summary["policy_digest"] == compute_ranking_matrix_policy_digest_v1()
    assert summary["runtime_wiring_added_by_this_slice"] is False
    assert summary["productive_economic_rank_activation"] is False


def test_validate_accepts_canonical_declaration() -> None:
    declaration = {
        **classify_peak_trade_ranking_matrix_policy_v1(),
        "b03_ratified": True,
        "policy_ratified": True,
        "runtime_activated": False,
        "economic_rank_activated": False,
        "productive_economic_rank_activation": False,
        "input2_max_age_seconds_ratified": False,
        "cap23_selection_authority_added": False,
        "runtime_wiring_added_by_this_slice": False,
        "b04_implemented": False,
        "b05_implemented": False,
        "b06_implemented": False,
        "cap22_productive_economic_runtime_wired": False,
        "empirically_estimated": False,
        "cross_sectional_normalization_ratified": True,
        "final_score_formula_ratified": True,
        "final_weights_ratified": True,
        "equal_importance_policy_axiom": True,
        "normative_equal_importance_weights": True,
        "incomplete_feature_policy_ratified": True,
        "profile_promotion_v1_ratified": True,
        "ranking_objective_ratified": True,
        "score_construction_ratified": True,
        "volatility_policy_ratified": True,
        "amplitude_policy_ratified": True,
    }
    result = validate_peak_trade_ranking_matrix_policy_declaration_v1(declaration)
    assert result["valid"] is True


def test_validate_rejects_fabricated_max_age() -> None:
    bad = classify_peak_trade_ranking_matrix_policy_v1()
    bad = dict(bad)
    bad["input2_max_age_seconds"] = 300
    with pytest.raises(Exception) as exc:
        validate_peak_trade_ranking_matrix_policy_declaration_v1(bad)
    assert "INPUT2_MAX_AGE" in str(exc.value)


def test_no_runtime_wiring_in_ranking_producer() -> None:
    root = Path(__file__).resolve().parents[2]
    producer = root / "src/ops/productive_futures_ranking_producer_v1/producer_v1.py"
    ranking = root / "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py"
    text = producer.read_text(encoding="utf-8") + ranking.read_text(encoding="utf-8")
    assert "peak_trade_ranking_matrix_policy_v1" not in text
    assert "balanced_movement_score" not in text


def test_no_b04_b05_b06_flags_true() -> None:
    assert B04_IMPLEMENTED is False
    assert B05_IMPLEMENTED is False
    assert B06_IMPLEMENTED is False
    assert RUNTIME_WIRING_ADDED_BY_THIS_SLICE is False
    assert CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED is False


def test_productive_futures_ranking_policy_unchanged() -> None:
    from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
        RANKING_POLICY_ID,
    )

    assert RANKING_POLICY_ID == "productive_futures_universe_structural_ranking_v1"


def test_dual_input_defers_runtime_and_points_at_b03_matrix() -> None:
    from src.ops import cap22_economic_md_dual_input_contract_v1 as dual

    assert dual.PEAK_TRADE_RANKING_MATRIX_POLICY_RATIFIED is True
    assert dual.PEAK_TRADE_RANKING_MATRIX_POLICY_ID == POLICY_ID
    assert dual.FINAL_SCORE_FORMULA_RATIFIED is True
    assert dual.CROSS_SECTIONAL_NORMALIZATION_RATIFIED is True
    assert dual.ECONOMIC_RANK_ACTIVATED is False
    assert dual.CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED is False


def test_offline_mvr_scope_keeps_offline_score_flags_false() -> None:
    from src.ops.cap22_offline_policy_candidates_and_evidence_contract_v1 import (
        FINAL_SCORE_FORMULA_RATIFIED,
        PEAK_TRADE_RANKING_MATRIX_POLICY_RATIFIED,
    )

    assert PEAK_TRADE_RANKING_MATRIX_POLICY_RATIFIED is True
    assert FINAL_SCORE_FORMULA_RATIFIED is False


def test_historical_evidence_json_not_modified() -> None:
    evidence = (
        Path(__file__).resolve().parents[2]
        / "docs/evidence/capability_2_2_productive_futures_ranking_producer_v1/SUMMARY.json"
    )
    if not evidence.is_file():
        pytest.skip("local evidence summary absent")
    text = evidence.read_text(encoding="utf-8")
    assert "PEAK_TRADE_RANKING_MATRIX_POLICY_V1" not in text


def test_ranking_matrix_module_has_no_network_imports() -> None:
    path = Path(__file__).resolve().parents[2] / "src/ops/peak_trade_ranking_matrix_policy_v1.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "requests" not in alias.name
                assert "httpx" not in alias.name
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "requests" not in node.module
            assert "httpx" not in node.module
