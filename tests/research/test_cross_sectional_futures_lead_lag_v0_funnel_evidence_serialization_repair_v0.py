"""Contract tests for lead-lag v0 decision funnel evidence serialization repair v0."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.ops import (
    run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 as runner_module,
)
from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingOutcome
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    EconomicClassification,
    ExecutionTerminalStatus,
    FullEconomicEvaluationResultV0,
    REEVALUATION_GO_TOKEN,
    execution_result_to_dict,
)
from src.research.cross_sectional_offline_economic_evaluation_decision_funnel_v0 import (
    RUNBOOK_FUNNEL_FIELDS,
    DecisionFunnelAccumulatorV0,
    build_decision_funnel_bundle_v0,
    materialize_block_reason_counts_v0,
    materialize_compact_decision_funnel_v0,
)
from src.trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from src.trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from src.trading.master_v2.double_play_entry_exit_policy_v0 import EntryEligibility
from src.trading.master_v2.suitability_binding_v1 import SuitabilityBindingStatus
from src.trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus

REPO_ROOT = Path(__file__).resolve().parents[2]


def _intermediate(
    *,
    bull_status: DirectionalAssessmentStatus,
    bear_status: DirectionalAssessmentStatus,
    survival_pass: bool,
    suitability_pass: bool,
    composition_status: CompositionStatus,
    entry_eligible: bool,
    sizing_pass: bool,
    portfolio_bound: bool,
) -> SimpleNamespace:
    return SimpleNamespace(
        bull_assessment=SimpleNamespace(status=bull_status),
        bear_assessment=SimpleNamespace(status=bear_status),
        bull_survival=SimpleNamespace(
            status=SurvivalAssessmentStatus.PASS if survival_pass else SurvivalAssessmentStatus.FAIL
        ),
        bear_survival=SimpleNamespace(status=SurvivalAssessmentStatus.FAIL),
        bull_suitability=SimpleNamespace(
            status=SuitabilityBindingStatus.PASS
            if suitability_pass
            else SuitabilityBindingStatus.FAIL
        ),
        bear_suitability=SimpleNamespace(status=SuitabilityBindingStatus.FAIL),
        composition_result=SimpleNamespace(composition_status=composition_status),
        entry_exit_decision=SimpleNamespace(
            entry_eligibility=(
                EntryEligibility.ELIGIBLE if entry_eligible else EntryEligibility.BLOCKED
            )
        ),
        capital_risk_sizing_decision=SimpleNamespace(
            outcome=CapitalRiskSizingOutcome.PASS
            if sizing_pass
            else CapitalRiskSizingOutcome.BLOCKED
        ),
        canonical_order_intent=object() if portfolio_bound else None,
    )


def test_decision_funnel_accumulator_nontrivial_value_propagation() -> None:
    accumulator = DecisionFunnelAccumulatorV0()
    accumulator.accumulate_from_replay(
        intermediate=_intermediate(
            bull_status=DirectionalAssessmentStatus.CANDIDATE,
            bear_status=DirectionalAssessmentStatus.OBSERVE,
            survival_pass=False,
            suitability_pass=False,
            composition_status=CompositionStatus.OBSERVE,
            entry_eligible=False,
            sizing_pass=False,
            portfolio_bound=False,
        ),
        evidence_reason_codes=("scope_warmup",),
    )
    accumulator.accumulate_from_replay(
        intermediate=_intermediate(
            bull_status=DirectionalAssessmentStatus.CONFIRMED,
            bear_status=DirectionalAssessmentStatus.OBSERVE,
            survival_pass=True,
            suitability_pass=True,
            composition_status=CompositionStatus.LONG_SELECTED,
            entry_eligible=True,
            sizing_pass=True,
            portfolio_bound=True,
        ),
        evidence_reason_codes=("enter_long",),
    )
    accumulator.set_trades_opened_count(2)

    counts = accumulator.counts_dict()
    assert counts["market_epochs_total"] == 2
    assert counts["directional_candidate_count"] == 2
    assert counts["directional_confirmed_count"] == 1
    assert counts["survival_pass_count"] == 1
    assert counts["suitability_pass_count"] == 1
    assert counts["double_play_entry_eligible_count"] == 1
    assert counts["entry_preconditions_pass_count"] == 1
    assert counts["risk_sizing_admissible_count"] == 1
    assert counts["portfolio_admissible_count"] == 1
    assert counts["trades_opened_count"] == 2
    assert counts["directional_candidate_count"] != counts["directional_confirmed_count"]


def test_compact_decision_funnel_serializes_all_runbook_fields_and_block_reasons() -> None:
    accumulator = DecisionFunnelAccumulatorV0()
    accumulator.accumulate_from_replay(
        intermediate=None,
        evidence_reason_codes=("INSUFFICIENT_ELIGIBLE_MEMBERS", "INSUFFICIENT_ELIGIBLE_MEMBERS"),
    )
    compact = materialize_compact_decision_funnel_v0(accumulator)
    assert compact["schema_version"] == "compact_decision_funnel.v0"
    for field_name in RUNBOOK_FUNNEL_FIELDS:
        assert field_name in compact
    assert compact["top_block_reasons"] == [("INSUFFICIENT_ELIGIBLE_MEMBERS", 2)]


def test_build_decision_funnel_bundle_is_deterministic() -> None:
    accumulator = DecisionFunnelAccumulatorV0()
    accumulator.accumulate_from_replay(
        intermediate=_intermediate(
            bull_status=DirectionalAssessmentStatus.CONFIRMED,
            bear_status=DirectionalAssessmentStatus.OBSERVE,
            survival_pass=True,
            suitability_pass=False,
            composition_status=CompositionStatus.SHORT_SELECTED,
            entry_eligible=True,
            sizing_pass=False,
            portfolio_bound=False,
        ),
        evidence_reason_codes=("survival_pass",),
    )
    accumulator.set_trades_opened_count(1)
    first = json.dumps(
        build_decision_funnel_bundle_v0(
            accumulator=accumulator,
            evaluation_status="ECONOMIC_EVALUATION_COMPLETE",
            precheck_passed=True,
            economic_evaluation_executed=True,
            reason_codes=(),
        ),
        sort_keys=True,
    )
    second = json.dumps(
        build_decision_funnel_bundle_v0(
            accumulator=accumulator,
            evaluation_status="ECONOMIC_EVALUATION_COMPLETE",
            precheck_passed=True,
            economic_evaluation_executed=True,
            reason_codes=(),
        ),
        sort_keys=True,
    )
    assert first == second


def test_execution_result_to_dict_includes_funnel_serialization_fields() -> None:
    funnel_bundle = build_decision_funnel_bundle_v0(
        accumulator=DecisionFunnelAccumulatorV0(
            market_epochs_total=3,
            directional_candidate_count=2,
            directional_confirmed_count=1,
            survival_pass_count=1,
            suitability_pass_count=1,
            double_play_entry_eligible_count=1,
            entry_preconditions_pass_count=1,
            risk_sizing_admissible_count=1,
            portfolio_admissible_count=1,
            trades_opened_count=1,
        ),
        evaluation_status="ECONOMIC_EVALUATION_COMPLETE",
        precheck_passed=True,
        economic_evaluation_executed=True,
    )
    result = FullEconomicEvaluationResultV0(
        status=ExecutionTerminalStatus.ECONOMIC_EVALUATION_COMPLETE,
        precheck_passed=True,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest="a" * 64,
        data_digest_is_fixture=False,
        stage_wiring=(),
        backtest=None,
        robustness=None,
        robustness_metrics=None,
        economic_viability_evidence={},
        economic_classification=EconomicClassification.FAIL,
        economic_validity_offline_gate_pass=False,
        promotion_candidate_eligible=False,
        economic_evaluation_executed=True,
        reason_codes=(),
        authority_effect="NONE",
        runtime_effect="NONE",
        compact_decision_funnel=funnel_bundle["compact_decision_funnel"],
        canonical_decision_funnel=funnel_bundle["canonical_decision_funnel"],
        block_reason_counts=funnel_bundle["block_reason_counts"],
    )
    payload = execution_result_to_dict(result)
    for field_name in RUNBOOK_FUNNEL_FIELDS:
        assert field_name in payload["compact_decision_funnel"]
    assert payload["block_reason_counts"] == {}
    assert payload["canonical_decision_funnel"]["schema_version"] == "canonical_decision_funnel.v0"


def test_runner_writes_productive_funnel_evidence_files(tmp_path: Path) -> None:
    funnel_accumulator = DecisionFunnelAccumulatorV0(
        market_epochs_total=5,
        directional_candidate_count=4,
        directional_confirmed_count=3,
        survival_pass_count=2,
        suitability_pass_count=2,
        double_play_entry_eligible_count=2,
        entry_preconditions_pass_count=2,
        risk_sizing_admissible_count=2,
        portfolio_admissible_count=2,
        trades_opened_count=2,
        block_reason_counts=Counter({"INSUFFICIENT_ELIGIBLE_MEMBERS": 1}),
    )
    funnel_bundle = build_decision_funnel_bundle_v0(
        accumulator=funnel_accumulator,
        evaluation_status="ECONOMIC_EVALUATION_COMPLETE",
        precheck_passed=True,
        economic_evaluation_executed=True,
    )
    evaluation = FullEconomicEvaluationResultV0(
        status=ExecutionTerminalStatus.ECONOMIC_EVALUATION_COMPLETE,
        precheck_passed=True,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest="b" * 64,
        data_digest_is_fixture=False,
        stage_wiring=(),
        backtest=None,
        robustness=None,
        robustness_metrics=None,
        economic_viability_evidence={},
        economic_classification=EconomicClassification.FAIL,
        economic_validity_offline_gate_pass=False,
        promotion_candidate_eligible=False,
        economic_evaluation_executed=True,
        reason_codes=(),
        authority_effect="NONE",
        runtime_effect="NONE",
        compact_decision_funnel=funnel_bundle["compact_decision_funnel"],
        canonical_decision_funnel=funnel_bundle["canonical_decision_funnel"],
        block_reason_counts=materialize_block_reason_counts_v0(funnel_accumulator),
    )

    with patch.object(
        runner_module,
        "load_evaluation_path_parity_status_v0",
        return_value=(True, True),
    ):
        with patch.object(
            runner_module,
            "verify_full_evaluation_precheck_v1",
            return_value=(True, (), SimpleNamespace(panel_data_digest="c" * 64)),
        ):
            with patch.object(
                runner_module,
                "run_full_offline_economic_evaluation_v0",
                return_value=evaluation,
            ):
                with patch.object(
                    runner_module,
                    "load_ohlcv_panel_series_for_backtest",
                    return_value=(),
                ):
                    payload = runner_module.run_bounded_full_evaluation_dispatch_v0(
                        confirm=REEVALUATION_GO_TOKEN,
                        durable_evidence_root=tmp_path,
                        primary_worktree=REPO_ROOT,
                        staging_root=REPO_ROOT,
                    )

    bundle_dir = Path(payload["durable_evidence_path"])
    compact = json.loads((bundle_dir / "compact_decision_funnel.json").read_text(encoding="utf-8"))
    assert compact["market_epochs_total"] == 5
    assert compact["trades_opened_count"] == 2
    assert compact["directional_candidate_count"] != compact["survival_pass_count"]
    assert (bundle_dir / "canonical_decision_funnel.json").is_file()
    assert (bundle_dir / "block_reason_counts.json").is_file()
