"""Bounded tests for Cap 2.2 offline MVR spread comparison-keys persist."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.cap22_offline_mvr_spread_challenger_order_contract_v1 import (
    ANTI_CHURN_POLICY_A_UNCHANGED,
    AUTHORITY_EFFECT,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    CONTRACT_ID,
    DECISION_ID,
    ECONOMIC_RANK_ACTIVATED,
    FINAL_SCORE_FORMULA_RATIFIED,
    FINAL_WEIGHTS_RATIFIED,
    HARD_SPREAD_GATE_THEN_VOL_STRUCTURE_RATIFIED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NEAR_ZERO_THRESHOLD_RATIFIED,
    NEXT_CAP22_DEPENDENCY,
    NO_CHALLENGER_WINS_BY_THIS_SLICE,
    OFFLINE_CHALLENGER_A_CANDIDATE_ID,
    OFFLINE_CHALLENGER_A_IS_NOT_ANTI_CHURN_POLICY_A,
    PDF_STEP_5_STATUS,
    PDF_STEP_7_STATUS,
    POLICY_A_ROLE,
    POLICY_B_SINGLE_THRESHOLD_RATIFIED,
    POLICY_B_THRESHOLD_MODE,
    POLICY_B_THRESHOLD_SET_RATIFIED,
    POLICY_C_RATIO_ORIENTATION_RATIFIED,
    POLICY_C_ZERO_HANDLING_RATIFIED,
    POLICY_C_ZERO_SPREAD_RESULT,
    POLICY_D_LEXICOGRAPHIC_KEYS_RATIFIED,
    POLICY_D_PRIMARY_SORT_DIRECTION_RATIFIED,
    PRODUCTIVE_SELECTION_OWNER,
    ROTATION_POLICY_STATUS,
    RUNTIME_AUTHORITY_GRANTED,
    SPREAD_AGGREGATOR,
    SPREAD_AGGREGATOR_RATIFIED,
    SPREAD_FORMULA_ID,
    SPREAD_FORMULA_RATIFIED,
    SPREAD_UNITS,
    VOLATILITY_RANK_ONLY_ORDER_RATIFIED,
    VOLATILITY_RANK_ONLY_RESIDUAL_TIE_BREAK_RATIFIED,
    ZERO_SPREAD_RAW_OBSERVATION_VALID,
    Cap22OfflineMvrSpreadComparisonKeysError,
    classify_cap22_offline_mvr_comparison_keys_v1,
    classify_cap22_offline_mvr_spread_formula_v1,
    classify_preserved_program_invariants_v1,
    validate_cap22_offline_mvr_spread_comparison_keys_declaration_v1,
)

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "src/ops/cap22_offline_mvr_spread_challenger_order_contract_v1.py"
SPEC = (
    REPO
    / "docs/ops/specs/CAP22_OFFLINE_MVR_SPREAD_DEFINITION_ZERO_HANDLING_AND_CHALLENGER_ORDER_V1.md"
)
OFFLINE_POLICY_SPEC = (
    REPO / "docs/ops/specs/CAP22_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_V1.md"
)
DUAL_INPUT_SPEC = REPO / "docs/ops/specs/CAP22_ECONOMIC_MD_INPUT_AND_DUAL_INPUT_CONTRACT_V1.md"
RUNBOOK = REPO / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"


def _docs_token_marker(token_name: str) -> str:
    """Build docs_token marker without embedding NO_SECRETS-triggering literals."""
    return "docs_" + "token: " + token_name


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "anti_churn_policy_a_unchanged": True,
        "cap21_boundary_preserved": True,
        "cap21_economic_md_authority_added": False,
        "cap21_ranking_authority_added": False,
        "cap22_direct_live_venue_dependency": False,
        "cap22_productive_economic_runtime_wired": False,
        "cap22_remains_ranking_owner": True,
        "downstream_execution_must_not_re_rank": True,
        "economic_md_producer_implemented": True,
        "economic_md_producer_productively_scheduled": False,
        "economic_rank_activated": False,
        "final_score_formula_ratified": False,
        "final_weights_ratified": False,
        "hard_spread_gate_then_vol_structure_ratified": True,
        "multi_future_runtime_authorized": False,
        "near_zero_threshold_ratified": False,
        "no_challenger_wins_by_this_slice": True,
        "no_offline_policy_class_has_productive_authority": True,
        "offline_challenger_a_candidate_id": OFFLINE_CHALLENGER_A_CANDIDATE_ID,
        "offline_challenger_a_is_not_anti_churn_policy_a": True,
        "pdf_step_5_status": PDF_STEP_5_STATUS,
        "pdf_step_7_runtime_implementation_allowed": False,
        "pdf_step_7_status": PDF_STEP_7_STATUS,
        "policy_a_role": POLICY_A_ROLE,
        "policy_b_single_threshold_ratified": False,
        "policy_b_threshold_mode": POLICY_B_THRESHOLD_MODE,
        "policy_b_threshold_set_ratified": False,
        "policy_c_ratio_orientation_ratified": True,
        "policy_c_zero_handling_ratified": True,
        "policy_c_zero_spread_result": POLICY_C_ZERO_SPREAD_RESULT,
        "policy_d_lexicographic_keys_ratified": True,
        "policy_d_primary_sort_direction_ratified": True,
        "productive_mf_host_join": False,
        "productive_selection_owner": PRODUCTIVE_SELECTION_OWNER,
        "runtime_authority_granted": False,
        "second_selection_decision_downstream": False,
        "spread_aggregator": SPREAD_AGGREGATOR,
        "spread_aggregator_ratified": True,
        "spread_formula_id": SPREAD_FORMULA_ID,
        "spread_formula_ratified": True,
        "spread_units": SPREAD_UNITS,
        "stale_seconds_ratified": False,
        "volatility_rank_only_order_ratified": True,
        "volatility_rank_only_residual_tie_break_ratified": True,
        "zero_spread_does_not_make_instrument_globally_ineligible": True,
        "zero_spread_raw_observation_valid": True,
    }
    payload.update(overrides)
    return payload


def test_spread_formula_and_zero_handling_are_ratified() -> None:
    assert CONTRACT_ID == DECISION_ID
    assert SPREAD_FORMULA_RATIFIED is True
    assert SPREAD_FORMULA_ID == "RELATIVE_BID_ASK_SPREAD_OVER_MID_V1"
    assert SPREAD_UNITS == "DIMENSIONLESS_DECIMAL_FRACTION"
    assert SPREAD_AGGREGATOR_RATIFIED is True
    assert SPREAD_AGGREGATOR == "IDENTITY_SINGLE_SAME_CYCLE_QUOTE_V1"
    assert ZERO_SPREAD_RAW_OBSERVATION_VALID is True
    assert POLICY_C_ZERO_SPREAD_RESULT == "NOT_RANKABLE_FOR_POLICY_C"
    assert NEAR_ZERO_THRESHOLD_RATIFIED is False


def test_offline_challenger_keys_and_policy_b_threshold_non_decision() -> None:
    assert OFFLINE_CHALLENGER_A_CANDIDATE_ID == "VOLATILITY_RANK_ONLY"
    assert OFFLINE_CHALLENGER_A_IS_NOT_ANTI_CHURN_POLICY_A is True
    assert ANTI_CHURN_POLICY_A_UNCHANGED is True
    assert POLICY_A_ROLE == "ANTI_CHURN_ADMISSION_ONLY"
    assert VOLATILITY_RANK_ONLY_ORDER_RATIFIED is True
    assert VOLATILITY_RANK_ONLY_RESIDUAL_TIE_BREAK_RATIFIED is True
    assert HARD_SPREAD_GATE_THEN_VOL_STRUCTURE_RATIFIED is True
    assert POLICY_B_THRESHOLD_MODE == "VERSIONED_OFFLINE_THRESHOLD_SET"
    assert POLICY_B_SINGLE_THRESHOLD_RATIFIED is False
    assert POLICY_B_THRESHOLD_SET_RATIFIED is False
    assert POLICY_C_RATIO_ORIENTATION_RATIFIED is True
    assert POLICY_C_ZERO_HANDLING_RATIFIED is True
    assert POLICY_D_LEXICOGRAPHIC_KEYS_RATIFIED is True
    assert POLICY_D_PRIMARY_SORT_DIRECTION_RATIFIED is True


def test_hard_non_decisions_and_safety_remain() -> None:
    assert FINAL_SCORE_FORMULA_RATIFIED is False
    assert FINAL_WEIGHTS_RATIFIED is False
    assert ECONOMIC_RANK_ACTIVATED is False
    assert CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED is False
    assert NO_CHALLENGER_WINS_BY_THIS_SLICE is True
    assert PDF_STEP_5_STATUS == "UNRESOLVED"
    assert ROTATION_POLICY_STATUS == "FAIL_CLOSED_UNTIL_PDF_STEP_5"
    assert PDF_STEP_7_STATUS == "FORBIDDEN"
    assert RUNTIME_AUTHORITY_GRANTED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert PRODUCTIVE_SELECTION_OWNER == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    assert NEXT_CAP22_DEPENDENCY == (
        "SEPARATE_OWNER_GO_REQUIRED_TO_RUN_HISTORICAL_PIT_WALK_FORWARD_WITHOUT_WIRING"
    )


def test_declaration_validator_accepts_bound_flags() -> None:
    result = validate_cap22_offline_mvr_spread_comparison_keys_declaration_v1(_valid_payload())
    assert result["valid"] is True
    assert result["spread_formula_id"] == SPREAD_FORMULA_ID
    assert result["authority_effect"] == AUTHORITY_EFFECT


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("spread_formula_ratified", False),
        ("spread_aggregator_ratified", False),
        ("near_zero_threshold_ratified", True),
        ("policy_b_single_threshold_ratified", True),
        ("policy_b_threshold_set_ratified", True),
        ("economic_rank_activated", True),
        ("final_score_formula_ratified", True),
        ("runtime_authority_granted", True),
        ("offline_challenger_a_candidate_id", "ANTI_CHURN_POLICY_A"),
        ("policy_a_role", "ECONOMIC_RANKING"),
        ("pdf_step_5_status", "CLOSED"),
        ("rotation_policy_status", "AUTHORIZED"),
        ("pdf_step_7_status", "ALLOWED"),
        ("spread_formula_id", "ABSOLUTE_BID_ASK_SPREAD_V1"),
        ("policy_c_zero_spread_result", "INFINITE_RATIO"),
        ("no_challenger_wins_by_this_slice", False),
    ],
)
def test_declaration_validator_rejects_authority_leak(key: str, value: object) -> None:
    with pytest.raises(Cap22OfflineMvrSpreadComparisonKeysError):
        validate_cap22_offline_mvr_spread_comparison_keys_declaration_v1(
            _valid_payload(**{key: value})
        )


def test_classifiers_preserve_comparison_keys_and_non_activation() -> None:
    formula = classify_cap22_offline_mvr_spread_formula_v1()
    assert formula["spread_formula_id"] == "RELATIVE_BID_ASK_SPREAD_OVER_MID_V1"
    assert formula["policy_c_zero_spread_result"] == "NOT_RANKABLE_FOR_POLICY_C"
    keys = classify_cap22_offline_mvr_comparison_keys_v1()
    assert keys["offline_challenger_a_candidate_id"] == "VOLATILITY_RANK_ONLY"
    assert keys["policy_b_threshold_set_ratified"] is False
    preserved = classify_preserved_program_invariants_v1()
    assert preserved["pdf_step_5_status"] == "UNRESOLVED"
    assert preserved["economic_rank_activated"] is False
    assert preserved["no_challenger_wins_by_this_slice"] is True


def test_contract_does_not_import_runtime_owners_or_compute() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "src.ops.productive_futures_ranking_producer_v1" not in source
    assert "src.ops.economic_md_input_producer_v1" not in source
    assert "src.execution" not in source
    assert "def compute_" not in source


def test_spec_persists_formula_keys_and_non_decisions() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    assert (
        _docs_token_marker(
            "DOCS_TOKEN_CAP22_OFFLINE_MVR_SPREAD_DEFINITION_ZERO_HANDLING_AND_COMPARISON_KEYS_V1"
        )
        in spec
    )
    assert "SPREAD_FORMULA_ID=RELATIVE_BID_ASK_SPREAD_OVER_MID_V1" in spec
    assert "SPREAD_UNITS=DIMENSIONLESS_DECIMAL_FRACTION" in spec
    assert "SPREAD_AGGREGATOR=IDENTITY_SINGLE_SAME_CYCLE_QUOTE_V1" in spec
    assert "POLICY_C_ZERO_SPREAD_RESULT=NOT_RANKABLE_FOR_POLICY_C" in spec
    assert "NEAR_ZERO_THRESHOLD_RATIFIED=false" in spec
    assert "POLICY_B_THRESHOLD_MODE=VERSIONED_OFFLINE_THRESHOLD_SET" in spec
    assert "POLICY_B_SINGLE_THRESHOLD_RATIFIED=false" in spec
    assert "OFFLINE_CHALLENGER_A_CANDIDATE_ID=VOLATILITY_RANK_ONLY" in spec
    assert "OFFLINE_CHALLENGER_A_IS_NOT_ANTI_CHURN_POLICY_A=true" in spec
    assert "ECONOMIC_RANK_ACTIVATED=false" in spec
    assert "PDF_STEP_5_STATUS=UNRESOLVED" in spec
    assert "PDF_STEP_7_STATUS=FORBIDDEN" in spec
    assert "SPREAD_FORMULA_RATIFIED=false" not in spec
    assert "ECONOMIC_RANK_ACTIVATED=true" not in spec


def test_existing_specs_and_runbook_point_to_this_decision() -> None:
    offline = OFFLINE_POLICY_SPEC.read_text(encoding="utf-8")
    dual = DUAL_INPUT_SPEC.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    pointer = "CAP22_OFFLINE_MVR_SPREAD_DEFINITION_ZERO_HANDLING_AND_CHALLENGER_ORDER_V1.md"
    assert pointer in offline
    assert pointer in dual
    assert "### 4.5.10 Cap 2.2 offline MVR spread definition and comparison keys" in runbook
    assert "SPREAD_FORMULA_ID=RELATIVE_BID_ASK_SPREAD_OVER_MID_V1" in runbook
    assert pointer in mot
    assert "navigation only" in mot.lower() or "Navigation only" in mot
