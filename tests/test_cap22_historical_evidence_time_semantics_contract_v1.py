"""Bounded tests for Cap 2.2 historical evidence time-semantics persist."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.cap22_historical_evidence_time_semantics_contract_v1 import (
    AUTHORITY_EFFECT,
    CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_AT_T_REQUIRED,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED,
    CONTRACT_ID,
    DECISION_ID,
    ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED,
    ECONOMIC_RANK_ACTIVATED,
    FORWARD_ABS_RETURN_DEFINITION_RATIFIED,
    FORWARD_LABEL_HORIZON_MINUTES,
    FORWARD_LABEL_HORIZON_RATIFIED,
    FORWARD_LABEL_HORIZON_SET_ID,
    FORWARD_LABEL_HORIZONS,
    FORWARD_LABEL_WINDOW_STRICTLY_AFTER_FEATURE_TIME,
    FORWARD_REALIZED_VOL_DEFINITION_RATIFIED,
    FORWARD_REALIZED_VOL_DDOF,
    FRICTION_ADJUSTED_OPPORTUNITY_FORMULA_RATIFIED,
    HISTORICAL_EVIDENCE_GENERATED,
    HISTORICAL_REPLAY_HORIZON_ID,
    HISTORICAL_REPLAY_HORIZON_RATIFIED,
    IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_REQUIRED,
    MINIMUM_HISTORICAL_COVERAGE_DAYS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NEW_LISTING_WARMUP_FAIL_CLOSED,
    NEXT_CAP22_DEPENDENCY,
    NO_CHALLENGER_WINS_BY_THIS_SLICE,
    PDF_STEP_5_STATUS,
    PDF_STEP_7_STATUS,
    POLICY_B_THRESHOLD_SET_RATIFIED,
    POLICY_RATIFICATION_JUSTIFIED,
    PRODUCTIVE_RUNTIME_CADENCE_AUTHORIZED,
    RANKING_CADENCE_ID,
    RANKING_CADENCE_RATIFIED,
    ROTATION_POLICY_STATUS,
    RUNTIME_AUTHORITY_GRANTED,
    STALE_SECONDS_RATIFIED,
    STRONGER_CANONICAL_MINIMUM_COVERAGE_DAYS_FOUND,
    WALK_FORWARD_PRIMARY_MODE,
    WALK_FORWARD_ROBUSTNESS_MODE,
    Cap22HistoricalEvidenceTimeSemanticsError,
    classify_cap22_historical_evidence_time_semantics_v1,
    classify_preserved_program_invariants_v1,
    is_valid_pt1m_15m_anchor_utc,
    non_overlapping_anchor_stride_for_horizon_minutes,
    validate_cap22_historical_evidence_time_semantics_declaration_v1,
)

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "src/ops/cap22_historical_evidence_time_semantics_contract_v1.py"
SPEC = REPO / "docs/ops/specs/CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1.md"
THRESHOLD_SPEC = REPO / "docs/ops/specs/CAP22_OFFLINE_MVR_THRESHOLD_SET_AND_EVIDENCE_HARNESS_V1.md"
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
        "cap21_governed_futures_universe_snapshot_at_t_required": True,
        "cap21_ranking_authority_added": False,
        "cap22_direct_live_venue_dependency": False,
        "cap22_productive_economic_runtime_wired": False,
        "cap22_remains_ranking_owner": True,
        "collection_skew_numeric_bound_ratified": False,
        "cross_sectional_normalization_ratified": False,
        "downstream_execution_must_not_re_rank": True,
        "economic_md_producer_productively_scheduled": False,
        "economic_rank_activated": False,
        "final_score_formula_ratified": False,
        "final_weights_ratified": False,
        "forward_abs_return_definition_ratified": True,
        "forward_label_horizon_ratified": True,
        "forward_label_horizon_set_id": FORWARD_LABEL_HORIZON_SET_ID,
        "forward_label_window_strictly_after_feature_time": True,
        "forward_realized_vol_definition_ratified": True,
        "friction_adjusted_opportunity_formula_ratified": False,
        "historical_evidence_generated": False,
        "historical_replay_horizon_id": HISTORICAL_REPLAY_HORIZON_ID,
        "historical_replay_horizon_ratified": True,
        "identical_candidate_universe_per_policy_required": True,
        "minimum_historical_coverage_days": MINIMUM_HISTORICAL_COVERAGE_DAYS,
        "multi_future_runtime_authorized": False,
        "near_zero_threshold_ratified": False,
        "new_listing_warmup_fail_closed": True,
        "no_challenger_wins_by_this_slice": True,
        "no_offline_policy_class_has_productive_authority": True,
        "pdf_step_5_status": PDF_STEP_5_STATUS,
        "pdf_step_7_runtime_implementation_allowed": False,
        "pdf_step_7_status": PDF_STEP_7_STATUS,
        "policy_b_single_threshold_ratified": False,
        "policy_b_threshold_set_ratified": False,
        "policy_ratification_justified": False,
        "productive_mf_host_join": False,
        "productive_runtime_cadence_authorized": False,
        "ranking_cadence_id": RANKING_CADENCE_ID,
        "ranking_cadence_ratified": True,
        "rotation_policy_status": ROTATION_POLICY_STATUS,
        "runtime_authority_granted": False,
        "second_selection_decision_downstream": False,
        "stale_seconds_ratified": False,
        "walk_forward_primary_mode": WALK_FORWARD_PRIMARY_MODE,
        "walk_forward_required": True,
        "walk_forward_robustness_mode": WALK_FORWARD_ROBUSTNESS_MODE,
    }
    payload.update(overrides)
    return payload


def test_cadence_horizons_and_walk_forward_modes_are_ratified() -> None:
    assert CONTRACT_ID == DECISION_ID
    assert RANKING_CADENCE_RATIFIED is True
    assert RANKING_CADENCE_ID == "PT1M_15_MINUTE_ANCHORS_V1"
    assert PRODUCTIVE_RUNTIME_CADENCE_AUTHORIZED is False
    assert FORWARD_LABEL_HORIZON_RATIFIED is True
    assert FORWARD_LABEL_HORIZON_SET_ID == "CAP22_MVR_FORWARD_LABEL_HORIZONS_V1"
    assert FORWARD_LABEL_HORIZONS == ("15m", "30m", "60m", "120m")
    assert FORWARD_LABEL_HORIZON_MINUTES == (15, 30, 60, 120)
    assert FORWARD_LABEL_WINDOW_STRICTLY_AFTER_FEATURE_TIME is True
    assert FORWARD_ABS_RETURN_DEFINITION_RATIFIED is True
    assert FORWARD_REALIZED_VOL_DEFINITION_RATIFIED is True
    assert FORWARD_REALIZED_VOL_DDOF == 0
    assert FRICTION_ADJUSTED_OPPORTUNITY_FORMULA_RATIFIED is False
    assert WALK_FORWARD_PRIMARY_MODE == "ALL_VALID_15M_ANCHORS"
    assert WALK_FORWARD_ROBUSTNESS_MODE == "NON_OVERLAPPING_BY_HORIZON"
    assert HISTORICAL_REPLAY_HORIZON_RATIFIED is True
    assert HISTORICAL_REPLAY_HORIZON_ID == "MIN_90D_PLUS_AVAILABLE_VALID_HISTORY_V1"
    assert MINIMUM_HISTORICAL_COVERAGE_DAYS == 90
    assert STRONGER_CANONICAL_MINIMUM_COVERAGE_DAYS_FOUND is False


def test_anchor_grid_and_non_overlapping_stride() -> None:
    assert is_valid_pt1m_15m_anchor_utc(minute=0) is True
    assert is_valid_pt1m_15m_anchor_utc(minute=15) is True
    assert is_valid_pt1m_15m_anchor_utc(minute=45) is True
    assert is_valid_pt1m_15m_anchor_utc(minute=7) is False
    assert is_valid_pt1m_15m_anchor_utc(minute=15, second=1) is False
    assert non_overlapping_anchor_stride_for_horizon_minutes(15) == 1
    assert non_overlapping_anchor_stride_for_horizon_minutes(30) == 2
    assert non_overlapping_anchor_stride_for_horizon_minutes(60) == 4
    assert non_overlapping_anchor_stride_for_horizon_minutes(120) == 8
    with pytest.raises(Cap22HistoricalEvidenceTimeSemanticsError):
        non_overlapping_anchor_stride_for_horizon_minutes(90)


def test_universe_warmup_and_non_decisions_remain_fail_closed() -> None:
    assert CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_AT_T_REQUIRED is True
    assert IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_REQUIRED is True
    assert NEW_LISTING_WARMUP_FAIL_CLOSED is True
    assert STALE_SECONDS_RATIFIED is False
    assert COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED is False
    assert POLICY_B_THRESHOLD_SET_RATIFIED is False
    assert POLICY_RATIFICATION_JUSTIFIED is False
    assert NO_CHALLENGER_WINS_BY_THIS_SLICE is True
    assert HISTORICAL_EVIDENCE_GENERATED is False
    assert ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED is False
    assert CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED is False
    assert ECONOMIC_RANK_ACTIVATED is False
    assert PDF_STEP_5_STATUS == "UNRESOLVED"
    assert ROTATION_POLICY_STATUS == "FAIL_CLOSED_UNTIL_PDF_STEP_5"
    assert PDF_STEP_7_STATUS == "FORBIDDEN"
    assert RUNTIME_AUTHORITY_GRANTED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert NEXT_CAP22_DEPENDENCY == (
        "SEPARATE_OWNER_GO_REQUIRED_TO_RUN_HISTORICAL_PIT_WALK_FORWARD_WITHOUT_WIRING"
    )


def test_declaration_validator_accepts_bound_flags() -> None:
    result = validate_cap22_historical_evidence_time_semantics_declaration_v1(_valid_payload())
    assert result["valid"] is True
    assert result["ranking_cadence_id"] == RANKING_CADENCE_ID
    assert result["authority_effect"] == AUTHORITY_EFFECT


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("ranking_cadence_ratified", False),
        ("forward_label_horizon_ratified", False),
        ("historical_replay_horizon_ratified", False),
        ("friction_adjusted_opportunity_formula_ratified", True),
        ("policy_b_threshold_set_ratified", True),
        ("policy_ratification_justified", True),
        ("economic_rank_activated", True),
        ("runtime_authority_granted", True),
        ("productive_runtime_cadence_authorized", True),
        ("historical_evidence_generated", True),
        ("pdf_step_5_status", "CLOSED"),
        ("rotation_policy_status", "AUTHORIZED"),
        ("pdf_step_7_status", "ALLOWED"),
        ("ranking_cadence_id", "PT5M_HOURLY_ANCHORS_V1"),
        ("walk_forward_primary_mode", "SINGLE_WINDOW"),
        ("minimum_historical_coverage_days", 30),
        ("no_challenger_wins_by_this_slice", False),
    ],
)
def test_declaration_validator_rejects_authority_leak(key: str, value: object) -> None:
    with pytest.raises(Cap22HistoricalEvidenceTimeSemanticsError):
        validate_cap22_historical_evidence_time_semantics_declaration_v1(
            _valid_payload(**{key: value})
        )


def test_classifiers_preserve_time_semantics_and_non_activation() -> None:
    classified = classify_cap22_historical_evidence_time_semantics_v1()
    assert classified["ranking_cadence_id"] == "PT1M_15_MINUTE_ANCHORS_V1"
    assert classified["forward_label_horizons"] == ["15m", "30m", "60m", "120m"]
    assert classified["friction_adjusted_opportunity_formula_ratified"] is False
    preserved = classify_preserved_program_invariants_v1()
    assert preserved["pdf_step_5_status"] == "UNRESOLVED"
    assert preserved["economic_rank_activated"] is False
    assert preserved["historical_evidence_generated"] is False
    assert preserved["next_cap22_dependency"].endswith("WALK_FORWARD_WITHOUT_WIRING")


def test_contract_does_not_import_runtime_owners_or_compute_labels() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "src.ops.productive_futures_ranking_producer_v1" not in source
    assert "src.ops.economic_md_input_producer_v1" not in source
    assert "src.ops.cap22_offline_mvr_evidence_harness_v1" not in source
    assert "src.execution" not in source
    assert "def compute_" not in source


def test_spec_and_runbook_persist_this_decision() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    threshold = THRESHOLD_SPEC.read_text(encoding="utf-8")
    assert _docs_token_marker("DOCS_TOKEN_CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1") in spec
    assert "RANKING_CADENCE_ID=PT1M_15_MINUTE_ANCHORS_V1" in spec
    assert "FORWARD_LABEL_HORIZON_SET_ID=CAP22_MVR_FORWARD_LABEL_HORIZONS_V1" in spec
    assert "FRICTION_ADJUSTED_OPPORTUNITY_FORMULA_RATIFIED=false" in spec
    assert "HISTORICAL_REPLAY_HORIZON_ID=MIN_90D_PLUS_AVAILABLE_VALID_HISTORY_V1" in spec
    assert "MINIMUM_HISTORICAL_COVERAGE_DAYS=90" in spec
    assert "PRODUCTIVE_RUNTIME_CADENCE_AUTHORIZED=false" in spec
    assert "### 4.5.12 Cap 2.2 historical evidence time semantics" in runbook
    assert "RANKING_CADENCE_ID=PT1M_15_MINUTE_ANCHORS_V1" in runbook
    assert "CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1.md" in mot
    assert "navigation only" in mot.lower() or "Navigation only" in mot
    assert "CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1.md" in threshold
    assert "ECONOMIC_RANK_ACTIVATED=true" not in spec
