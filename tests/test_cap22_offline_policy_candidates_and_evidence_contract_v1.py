"""Bounded tests for Cap 2.2 offline policy-candidate and evidence persist."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.cap22_offline_policy_candidates_and_evidence_contract_v1 import (
    ADDITIONAL_RAW_INPUT_LIST,
    ADDITIONAL_RAW_INPUT_REQUIRED,
    AUTHORIZED_MVR_INPUTS,
    AUTHORIZED_VOLATILITY_BASE_GRID,
    AUTHORIZED_VOLATILITY_WARMUP,
    CAP21_BOUNDARY_PRESERVED,
    CAP21_ECONOMIC_MD_AUTHORITY_ADDED,
    CAP21_RANKING_AUTHORITY_ADDED,
    CAP22_DIRECT_LIVE_VENUE_DEPENDENCY,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    CAP22_REMAINS_RANKING_OWNER,
    CAP22_TARGET_RANK_MEANING,
    COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED,
    CROSS_SECTIONAL_NORMALIZATION_RATIFIED,
    CURRENT_ALPHABETICAL_BASELINE_VERDICT,
    CURRENT_PERSISTED_CAP22_ECONOMIC_MD_AVAILABLE,
    CURRENT_PRODUCTIVE_ECONOMIC_RANKING,
    CURRENT_PRODUCTIVE_RANKING_POLICY,
    CURRENT_STRUCTURAL_RANKING_IS_ECONOMIC_POLICY,
    DEFERRED_FEATURES,
    DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK,
    ECONOMIC_MD_PRODUCER_IMPLEMENTED,
    ECONOMIC_RANK_ACTIVATED,
    FINAL_SCORE_FORMULA_RATIFIED,
    FINAL_WEIGHTS_RATIFIED,
    FORWARD_LABEL_HORIZON_RATIFIED,
    FRICTION_SENSITIVITY_REQUIRED,
    HARD_SPREAD_GATE_THEN_VOLATILITY_RANK_VERDICT,
    HISTORICAL_REPLAY_HORIZON_RATIFIED,
    LEXICOGRAPHIC_SPREAD_THEN_VOL_VERDICT,
    MISSING_STALE_INPUT_STRESS_REQUIRED,
    MULTIPLICATIVE_OPPORTUNITY_X_TRADABILITY_VERDICT,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MVR_DATA_SUFFICIENT_FOR_POLICY_COMPARISON,
    NEGATIVE_STATUS_QUO_BASELINE,
    NEW_LISTING_WARMUP_TEST_REQUIRED,
    NEXT_CANONICAL_DECISION,
    NEXT_CAP22_DEPENDENCY,
    NO_LOOKAHEAD_REQUIRED,
    NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY,
    PARETO_DIAGNOSTIC_USE_ALLOWED,
    PARETO_VOL_AND_TRADABILITY_VERDICT,
    PDF_STEP_5_STATUS,
    PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED,
    PDF_STEP_7_STATUS,
    PIT_REPLAY_REQUIRED,
    POLICY_A_ROLE,
    PRODUCTIVE_MF_HOST_JOIN,
    PRODUCTIVE_SELECTION_OWNER,
    RANK_STABILITY_TEST_REQUIRED,
    RANKING_CADENCE_RATIFIED,
    RANKING_OBJECTIVE_IS_NOT_DOWNSTREAM_PNL,
    RANKING_OBJECTIVE_METRICS,
    RECOMMENDED_OFFLINE_CHALLENGERS,
    RECOMMENDED_PRIMARY_BASELINE,
    ROTATION_POLICY_STATUS,
    RUNTIME_AUTHORITY_GRANTED,
    SECOND_SELECTION_DECISION_DOWNSTREAM,
    SECONDARY_STRATEGY_METRICS,
    SPREAD_AGGREGATOR_RATIFIED,
    SPREAD_DERIVED_VALUE_ALONE_IS_INSUFFICIENT,
    SPREAD_FORMULA_RATIFIED,
    SPREAD_RAW_QUOTES_MUST_BE_PERSISTED,
    STALE_SECONDS_RATIFIED,
    TOP20_TURNOVER_TEST_REQUIRED,
    VOLATILITY_LOOKBACK_VARIANT_IS_NEW_FEATURE_SEMANTICS,
    VOLATILITY_RANK_ONLY_VERDICT,
    VOLATILITY_TO_SPREAD_RATIO_VERDICT,
    WALK_FORWARD_REQUIRED,
    WEIGHTED_ADDITIVE_COMPOSITE_VERDICT,
    Cap22OfflinePolicyCandidatesAndEvidenceError,
    classify_cap22_offline_evidence_contract_v1,
    classify_cap22_offline_policy_candidates_v1,
    classify_preserved_program_invariants_v1,
    validate_cap22_offline_policy_candidates_and_evidence_declaration_v1,
)

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "src/ops/cap22_offline_policy_candidates_and_evidence_contract_v1.py"
SPEC = REPO / "docs/ops/specs/CAP22_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_V1.md"
DUAL_INPUT_SPEC = REPO / "docs/ops/specs/CAP22_ECONOMIC_MD_INPUT_AND_DUAL_INPUT_CONTRACT_V1.md"
CAP22_SPEC = (
    REPO / "docs/ops/specs/MASTER_V2_CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1.md"
)
RUNBOOK = REPO / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"


def _docs_token_marker(token_name: str) -> str:
    """Build docs_token marker without embedding NO_SECRETS-triggering literals."""
    return "docs_" + "token: " + token_name


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "additional_raw_input_list": ADDITIONAL_RAW_INPUT_LIST,
        "additional_raw_input_required": False,
        "cap21_boundary_preserved": True,
        "cap21_economic_md_authority_added": False,
        "cap21_ranking_authority_added": False,
        "cap22_direct_live_venue_dependency": False,
        "cap22_productive_economic_runtime_wired": False,
        "cap22_remains_ranking_owner": True,
        "current_structural_ranking_is_economic_policy": False,
        "downstream_execution_must_not_re_rank": True,
        "economic_md_producer_implemented": True,
        "economic_md_producer_productively_scheduled": False,
        "economic_rank_activated": False,
        "final_score_formula_ratified": False,
        "final_weights_ratified": False,
        "friction_sensitivity_required": True,
        "identical_candidate_universe_per_policy_comparison": True,
        "missing_stale_input_stress_required": True,
        "mvr_data_sufficient_for_policy_comparison": True,
        "multi_future_runtime_authorized": False,
        "new_listing_warmup_test_required": True,
        "no_lookahead_required": True,
        "no_offline_policy_class_has_productive_authority": True,
        "pareto_vol_and_tradability_verdict": PARETO_VOL_AND_TRADABILITY_VERDICT,
        "pdf_step_5_status": PDF_STEP_5_STATUS,
        "pdf_step_7_runtime_implementation_allowed": False,
        "pdf_step_7_status": PDF_STEP_7_STATUS,
        "pit_replay_required": True,
        "productive_mf_host_join": False,
        "productive_selection_owner": PRODUCTIVE_SELECTION_OWNER,
        "rank_stability_test_required": True,
        "ranking_objective_is_not_downstream_pnl": True,
        "recommended_offline_challengers": RECOMMENDED_OFFLINE_CHALLENGERS,
        "recommended_primary_baseline": RECOMMENDED_PRIMARY_BASELINE,
        "rotation_policy_status": ROTATION_POLICY_STATUS,
        "runtime_authority_granted": False,
        "second_selection_decision_downstream": False,
        "spread_aggregator_ratified": True,
        "spread_formula_ratified": True,
        "spread_raw_quotes_must_be_persisted": True,
        "top20_turnover_test_required": True,
        "volatility_rank_only_verdict": VOLATILITY_RANK_ONLY_VERDICT,
        "walk_forward_required": True,
    }
    payload.update(overrides)
    return payload


def test_policy_candidate_set_matches_adjudication() -> None:
    assert CAP22_TARGET_RANK_MEANING == "TRADABLE_ECONOMIC_OPPORTUNITY_FOR_PEAK_TRADE"
    assert CURRENT_PRODUCTIVE_ECONOMIC_RANKING == "NONE"
    assert CURRENT_PRODUCTIVE_RANKING_POLICY == (
        "productive_futures_universe_structural_ranking_v1"
    )
    assert CURRENT_STRUCTURAL_RANKING_IS_ECONOMIC_POLICY is False
    assert RECOMMENDED_PRIMARY_BASELINE == "VOLATILITY_RANK_ONLY"
    assert VOLATILITY_RANK_ONLY_VERDICT == "BASELINE_ONLY"
    assert NEGATIVE_STATUS_QUO_BASELINE == "CURRENT_STRUCTURAL_THEN_VENUE_ID_ASC"
    assert CURRENT_ALPHABETICAL_BASELINE_VERDICT == "BASELINE_ONLY"
    assert RECOMMENDED_OFFLINE_CHALLENGERS == (
        "HARD_SPREAD_GATE_THEN_VOLATILITY_RANK",
        "VOLATILITY_TO_SPREAD_RATIO",
        "LEXICOGRAPHIC_SPREAD_THEN_VOL",
    )
    assert HARD_SPREAD_GATE_THEN_VOLATILITY_RANK_VERDICT == "RECOMMENDED_OFFLINE_CHALLENGER"
    assert VOLATILITY_TO_SPREAD_RATIO_VERDICT == "RECOMMENDED_OFFLINE_CHALLENGER"
    assert LEXICOGRAPHIC_SPREAD_THEN_VOL_VERDICT == "RECOMMENDED_OFFLINE_CHALLENGER"
    assert MULTIPLICATIVE_OPPORTUNITY_X_TRADABILITY_VERDICT == "DEFER"
    assert WEIGHTED_ADDITIVE_COMPOSITE_VERDICT == "DEFER"
    assert PARETO_VOL_AND_TRADABILITY_VERDICT == "REJECT_AS_TOP20_POLICY"
    assert PARETO_DIAGNOSTIC_USE_ALLOWED is True
    assert NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY is True
    assert "VOLATILITY_RANK_ONLY" not in RECOMMENDED_OFFLINE_CHALLENGERS
    assert "CURRENT_STRUCTURAL_THEN_VENUE_ID_ASC" not in RECOMMENDED_OFFLINE_CHALLENGERS
    assert "MULTIPLICATIVE_OPPORTUNITY_X_TRADABILITY" not in RECOMMENDED_OFFLINE_CHALLENGERS
    assert "WEIGHTED_ADDITIVE_COMPOSITE" not in RECOMMENDED_OFFLINE_CHALLENGERS
    assert "PARETO_VOL_AND_TRADABILITY" not in RECOMMENDED_OFFLINE_CHALLENGERS


def test_mvr_and_evidence_contract_invariants() -> None:
    assert AUTHORIZED_MVR_INPUTS == (
        "FINALIZED_PT1M_MARK_PRICE_HISTORY+SAME_COLLECTION_CYCLE_BIDPX_ASKPX"
    )
    assert MVR_DATA_SUFFICIENT_FOR_POLICY_COMPARISON is True
    assert CURRENT_PERSISTED_CAP22_ECONOMIC_MD_AVAILABLE is False
    assert ADDITIONAL_RAW_INPUT_REQUIRED is False
    assert ADDITIONAL_RAW_INPUT_LIST == "NONE"
    assert SPREAD_RAW_QUOTES_MUST_BE_PERSISTED is True
    assert SPREAD_DERIVED_VALUE_ALONE_IS_INSUFFICIENT is True
    assert AUTHORIZED_VOLATILITY_BASE_GRID == "FINALIZED_PT1M"
    assert AUTHORIZED_VOLATILITY_WARMUP == "61_PT1M_MARKS_60_LOG_RETURNS"
    assert VOLATILITY_LOOKBACK_VARIANT_IS_NEW_FEATURE_SEMANTICS is True
    assert PIT_REPLAY_REQUIRED is True
    assert NO_LOOKAHEAD_REQUIRED is True
    assert WALK_FORWARD_REQUIRED is True
    assert RANK_STABILITY_TEST_REQUIRED is True
    assert TOP20_TURNOVER_TEST_REQUIRED is True
    assert FRICTION_SENSITIVITY_REQUIRED is True
    assert NEW_LISTING_WARMUP_TEST_REQUIRED is True
    assert MISSING_STALE_INPUT_STRESS_REQUIRED is True
    assert RANKING_OBJECTIVE_IS_NOT_DOWNSTREAM_PNL is True
    assert "PNL" in SECONDARY_STRATEGY_METRICS
    assert "PNL" not in RANKING_OBJECTIVE_METRICS
    assert "FRICTION_ADJUSTED_OPPORTUNITY" in RANKING_OBJECTIVE_METRICS
    assert DEFERRED_FEATURES == (
        "CONTRACT_VOLUME",
        "TURNOVER",
        "OPEN_INTEREST",
        "FUNDING",
        "ORDERBOOK_DEPTH",
        "PRICE_IMPACT",
        "MOMENTUM",
        "TREND",
        "ATR",
        "LISTING_AGE",
        "FEE_MODEL",
        "STATIC_SLIPPAGE_MODEL",
    )


def test_hard_non_decisions_and_safety_remain() -> None:
    assert FINAL_SCORE_FORMULA_RATIFIED is False
    assert FINAL_WEIGHTS_RATIFIED is False
    assert CROSS_SECTIONAL_NORMALIZATION_RATIFIED is False
    assert SPREAD_FORMULA_RATIFIED is True
    assert SPREAD_AGGREGATOR_RATIFIED is True
    assert STALE_SECONDS_RATIFIED is False
    assert COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED is False
    assert RANKING_CADENCE_RATIFIED is False
    assert FORWARD_LABEL_HORIZON_RATIFIED is False
    assert HISTORICAL_REPLAY_HORIZON_RATIFIED is False
    assert ECONOMIC_RANK_ACTIVATED is False
    assert ECONOMIC_MD_PRODUCER_IMPLEMENTED is True
    assert CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED is False
    assert CAP21_BOUNDARY_PRESERVED is True
    assert CAP21_RANKING_AUTHORITY_ADDED is False
    assert CAP21_ECONOMIC_MD_AUTHORITY_ADDED is False
    assert CAP22_REMAINS_RANKING_OWNER is True
    assert CAP22_DIRECT_LIVE_VENUE_DEPENDENCY is False
    assert PRODUCTIVE_SELECTION_OWNER == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    assert POLICY_A_ROLE == "ANTI_CHURN_ADMISSION_ONLY"
    assert DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK is True
    assert SECOND_SELECTION_DECISION_DOWNSTREAM is False
    assert PDF_STEP_5_STATUS == "UNRESOLVED"
    assert ROTATION_POLICY_STATUS == "FAIL_CLOSED_UNTIL_PDF_STEP_5"
    assert PDF_STEP_7_STATUS == "FORBIDDEN"
    assert PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED is False
    assert RUNTIME_AUTHORITY_GRANTED is False
    assert PRODUCTIVE_MF_HOST_JOIN is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert NEXT_CANONICAL_DECISION == "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION"
    assert NEXT_CAP22_DEPENDENCY == (
        "SEPARATE_OWNER_GO_REQUIRED_TO_RATIFY_RANKING_CADENCE_FORWARD_LABEL_AND_"
        "HISTORICAL_REPLAY_HORIZONS_THEN_RUN_WALK_FORWARD_WITHOUT_WIRING"
    )


def test_declaration_validator_accepts_bound_flags() -> None:
    result = validate_cap22_offline_policy_candidates_and_evidence_declaration_v1(_valid_payload())
    assert result["valid"] is True
    assert result["recommended_primary_baseline"] == RECOMMENDED_PRIMARY_BASELINE
    assert result["recommended_offline_challengers"] == RECOMMENDED_OFFLINE_CHALLENGERS


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("final_score_formula_ratified", True),
        ("final_weights_ratified", True),
        ("spread_formula_ratified", False),
        ("spread_aggregator_ratified", False),
        ("economic_md_producer_implemented", False),
        ("economic_md_producer_productively_scheduled", True),
        ("economic_rank_activated", True),
        ("runtime_authority_granted", True),
        ("multi_future_runtime_authorized", True),
        ("additional_raw_input_required", True),
        ("no_offline_policy_class_has_productive_authority", False),
        ("volatility_rank_only_verdict", "RECOMMENDED_OFFLINE_CHALLENGER"),
        ("pareto_vol_and_tradability_verdict", "RECOMMENDED_OFFLINE_CHALLENGER"),
        ("recommended_primary_baseline", "WEIGHTED_ADDITIVE_COMPOSITE"),
        ("recommended_offline_challengers", ("VOLATILITY_RANK_ONLY",)),
        ("additional_raw_input_list", "orderbook_depth"),
        ("pdf_step_5_status", "CLOSED"),
        ("rotation_policy_status", "AUTHORIZED"),
        ("pdf_step_7_status", "ALLOWED"),
        ("productive_selection_owner", "CAPABILITY_2_2"),
        ("downstream_execution_must_not_re_rank", False),
    ],
)
def test_declaration_validator_rejects_authority_leak(key: str, value: object) -> None:
    with pytest.raises(Cap22OfflinePolicyCandidatesAndEvidenceError):
        validate_cap22_offline_policy_candidates_and_evidence_declaration_v1(
            _valid_payload(**{key: value})
        )


def test_classifiers_preserve_hard_non_decisions() -> None:
    candidates = classify_cap22_offline_policy_candidates_v1()
    assert candidates["volatility_rank_only_verdict"] == "BASELINE_ONLY"
    assert candidates["recommended_offline_challengers"] == RECOMMENDED_OFFLINE_CHALLENGERS
    assert candidates["pareto_vol_and_tradability_verdict"] == "REJECT_AS_TOP20_POLICY"
    evidence = classify_cap22_offline_evidence_contract_v1()
    assert evidence["additional_raw_input_required"] is False
    assert evidence["ranking_objective_is_not_downstream_pnl"] is True
    preserved = classify_preserved_program_invariants_v1()
    assert preserved["pdf_step_5_status"] == "UNRESOLVED"
    assert preserved["final_score_formula_ratified"] is False
    assert preserved["runtime_authority_granted"] is False
    assert preserved["second_selection_decision_downstream"] is False


def test_contract_does_not_import_runtime_owners() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "src.ops.productive_futures_ranking_producer_v1" not in source
    assert "src.ops.governed_futures_universe_producer_v1" not in source
    assert "src.execution" not in source
    assert "src.ops.single_selected_future" not in source
    assert "def compute_" not in source


def test_spec_persists_challengers_and_hard_non_decisions() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    assert (
        _docs_token_marker("DOCS_TOKEN_CAP22_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_V1")
        in spec
    )
    assert "RECOMMENDED_PRIMARY_BASELINE=VOLATILITY_RANK_ONLY" in spec
    assert "VOLATILITY_RANK_ONLY_VERDICT=BASELINE_ONLY" in spec
    assert "NEGATIVE_STATUS_QUO_BASELINE=CURRENT_STRUCTURAL_THEN_VENUE_ID_ASC" in spec
    assert "HARD_SPREAD_GATE_THEN_VOLATILITY_RANK" in spec
    assert "VOLATILITY_TO_SPREAD_RATIO" in spec
    assert "LEXICOGRAPHIC_SPREAD_THEN_VOL" in spec
    assert "MULTIPLICATIVE_OPPORTUNITY_X_TRADABILITY_VERDICT=DEFER" in spec
    assert "WEIGHTED_ADDITIVE_COMPOSITE_VERDICT=DEFER" in spec
    assert "PARETO_VOL_AND_TRADABILITY_VERDICT=REJECT_AS_TOP20_POLICY" in spec
    assert "PIT_REPLAY_REQUIRED=true" in spec
    assert "NO_LOOKAHEAD_REQUIRED=true" in spec
    assert "WALK_FORWARD_REQUIRED=true" in spec
    assert "RANK_STABILITY_TEST_REQUIRED=true" in spec
    assert "TOP20_TURNOVER_TEST_REQUIRED=true" in spec
    assert "FRICTION_SENSITIVITY_REQUIRED=true" in spec
    assert "NEW_LISTING_WARMUP_TEST_REQUIRED=true" in spec
    assert "MISSING_STALE_INPUT_STRESS_REQUIRED=true" in spec
    assert "ADDITIONAL_RAW_INPUT_REQUIRED=false" in spec
    assert "ADDITIONAL_RAW_INPUT_LIST=NONE" in spec
    assert "FINAL_SCORE_FORMULA_RATIFIED=false" in spec
    assert "FINAL_WEIGHTS_RATIFIED=false" in spec
    assert "ECONOMIC_RANK_ACTIVATED=false" in spec
    assert "ECONOMIC_MD_PRODUCER_IMPLEMENTED=true" in spec
    assert "ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false" in spec
    assert "CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false" in spec
    assert "PDF_STEP_5_STATUS=UNRESOLVED" in spec
    assert "ROTATION_POLICY_STATUS=FAIL_CLOSED_UNTIL_PDF_STEP_5" in spec
    assert "PDF_STEP_7_STATUS=FORBIDDEN" in spec
    assert "RUNTIME_AUTHORITY_GRANTED=false" in spec
    assert "DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK=true" in spec
    assert "SECOND_SELECTION_DECISION_DOWNSTREAM=FORBIDDEN" in spec
    assert "PRODUCTIVE_SELECTION_OWNER=Cap_2.3" in spec
    assert "VOLATILITY_RANK_ONLY_VERDICT=RECOMMENDED_OFFLINE_CHALLENGER" not in spec
    assert "FINAL_SCORE_FORMULA_RATIFIED=true" not in spec
    assert "PDF_STEP_5_STATUS=CLOSED" not in spec


def test_existing_specs_remain_unwired_and_point_to_offline_contract() -> None:
    dual = DUAL_INPUT_SPEC.read_text(encoding="utf-8")
    cap22 = CAP22_SPEC.read_text(encoding="utf-8")
    assert "CAP22_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_V1.md" in dual
    assert "FINAL_SCORE_FORMULA_RATIFIED=false" in dual
    assert "ECONOMIC_MD_PRODUCER_IMPLEMENTED=true" in dual
    assert "ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED=false" in dual
    assert "CAP22_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_V1.md" in cap22
    assert "CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED=false" in cap22
    assert "ECONOMIC_RANK_ACTIVATED=false" in cap22


def test_runbook_and_map_persist_decision_without_unlocking_mf() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "### 4.5.8 Cap 2.2 offline policy candidates and evidence contract" in runbook
    assert "RECOMMENDED_PRIMARY_BASELINE=VOLATILITY_RANK_ONLY" in runbook
    assert "PARETO_VOL_AND_TRADABILITY_VERDICT=REJECT_AS_TOP20_POLICY" in runbook
    assert "FINAL_SCORE_FORMULA_RATIFIED=false" in runbook
    assert "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION=UNRESOLVED" in runbook
    assert "PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED=false" in runbook
    assert "MULTI_FUTURE_RUNTIME_AUTHORIZED=false" in runbook
    assert "CAP22_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_V1.md" in mot
    assert "navigation only" in mot.lower() or "Navigation only" in mot
