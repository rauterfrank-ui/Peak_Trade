"""Canonical open MR exit-efficiency hypothesis backlog SSOT validator v1.

Definition-only governance. No evaluation, backtest, holdout access, runtime
activation, or productive trading-logic mutation.

Post V8 terminal PASS closeout: zero DEFINITION_ONLY_PREREGISTERED candidates;
V1-V8 terminal (V8 PASS after one authorized DEVELOPMENT evaluation);
development_run_count=8; no V8 rerun/reopen; no V9 auto-create; economic/promotion closed.

Lane status vocabulary and post-terminal legality are owned solely by
CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CONTRACT_ID as LIFECYCLE_CONTRACT_ID,
    CONTRACT_REL_PATH as LIFECYCLE_CONTRACT_REL_PATH,
    ResearchLaneLifecycleContractError,
    resolve_post_terminal_transition,
    validate_lane_snapshot,
)

PACKAGE_MARKER = "CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1=true"
BACKLOG_REL_PATH = "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
GOVERNANCE_REL_PATH = "docs/governance/CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1.md"
REQUIRED_STATUS = "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS"
REQUIRED_OPERATOR_DECISION = "DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS"
REQUIRED_LIFECYCLE_AUTHORITY = "SHARED_POST_TERMINAL_LIFECYCLE_CONTRACT_V1_SOLE_AUTHORITY"
ENTRY_ELIGIBILITY_BACKLOG_REL_PATH = (
    "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
)
REQUIRED_ENTRY_ELIGIBILITY_LANE_STATUS = "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS"
REQUIRED_ENTRY_ELIGIBILITY_STATUS_AUTHORITY = (
    "SIBLING_ENTRY_ELIGIBILITY_BACKLOG_UNDER_SHARED_LIFECYCLE_CONTRACT_V1"
)
POST_TERMINAL_EMPTY_INVENTORY_STATE = "POST_TERMINAL_OPERATOR_DECISION_REQUIRED"
REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
REQUIRED_TREATMENT_TYPE = "POST_ENTRY_EXIT_EFFICIENCY_MECHANISM"
REQUIRED_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1"
)
REQUIRED_V2_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2"
)
REQUIRED_V3_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3"
)
REQUIRED_V4_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4"
)
REQUIRED_V5_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V5"
)
REQUIRED_V6_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6"
)
REQUIRED_V6_MECHANISM_ID = (
    "canonical_bollinger_side_aware_middle_band_exit_with_frozen_max_holding_horizon_v1"
)
REQUIRED_V7_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7"
)
REQUIRED_V7_MECHANISM_ID = "canonical_bollinger_side_aware_midband_exit_with_frozen_max_holding_and_same_side_reentry_cooldown_v1"
REQUIRED_V7_PREREGISTRATION_DIGEST = (
    "4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680"
)
REQUIRED_V8_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8"
)
REQUIRED_V8_MECHANISM_ID = REQUIRED_V7_MECHANISM_ID
REQUIRED_V8_PREREGISTRATION_DIGEST = (
    "610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c"
)
REQUIRED_V8_PREDECESSOR_RESULT_DIGEST = (
    "86fd0b862fa74b9fc3f28ddc63eede0258caded9cfbc35b1d9d9c5fbdf851fd6"
)
REQUIRED_BINDING_FIX_SURFACE = "MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX"
REQUIRED_OBSERVABILITY_SURFACE = "EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1"
REQUIRED_FALSY_ZERO_HYGIENE_SURFACE = "PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE"
REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5"
)
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
REQUIRED_RESEARCH_QUESTION = (
    "Given COSTS_DESTROY_MARGINAL_EDGE on the sealed DEVELOPMENT_ONLY Bollinger/MR "
    "baseline (marginal gross PF~1.01, all-SHORT book), does a cost-structure or "
    "holding/exit-efficiency change class exist that preserves gross edge without "
    "retuning terminal entry-eligibility parameters or reopening exhausted filter families?"
)
FORBIDDEN_EMBEDDED_RESULT_KEYS = frozenset(
    {
        "baseline_metrics",
        "treatment_metrics",
        "measured_net_return",
        "measured_profit_factor",
        "economic_metrics",
        "probe_summary",
    }
)
REQUIRED_TERMINAL_STATUS = "TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
REQUIRED_TERMINAL_FAIL_STATUS = "TERMINAL_FAIL"
REQUIRED_TERMINAL_INFRA_STATUS = "TERMINAL_INFRASTRUCTURE_FAILURE"
REQUIRED_TERMINAL_PASS_STATUS = "TERMINAL_PASS"
REQUIRED_V7_NEXT_STEP = (
    "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS_NO_EXECUTABLE_GO_WITHOUT_CONCRETE_TARGET"
)
REQUIRED_V8_NEXT_STEP = (
    "AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS_NO_EXECUTABLE_GO_WITHOUT_CONCRETE_TARGET"
)
REQUIRED_AWAITING_NEXT_STEP = REQUIRED_V8_NEXT_STEP
REQUIRED_PREREGISTERED_STATUS = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_V7_DIAGNOSTIC_CLASS = "PRE_PANEL_FROZEN_EXIT_PARAMETERS_MISMATCH_NO_PANEL_BACKTEST"
REQUIRED_V8_DECISION_REASON = "ALL_PASS_REQUIRES_MET"
REQUIRED_V8_LIFECYCLE_TERMINAL = "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/PASS"


class BacklogValidationError(ValueError):
    """Fail-closed exit-efficiency backlog SSOT validation error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_true(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        suffix = f": {detail}" if detail else ""
        raise BacklogValidationError(f"{code}{suffix}")


def _contains_banned_result_keys(obj: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            key_path = f"{path}.{key}"
            if key in FORBIDDEN_EMBEDDED_RESULT_KEYS:
                found.append(key_path)
            found.extend(_contains_banned_result_keys(value, key_path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(_contains_banned_result_keys(item, f"{path}[{idx}]"))
    return found


def _assert_terminal_inconclusive_entry(
    entry: Mapping[str, Any],
    *,
    hypothesis_id: str,
    code_prefix: str,
) -> None:
    _assert_true(isinstance(entry, Mapping), f"{code_prefix}_ENTRY_TYPE")
    _assert_true(entry.get("hypothesis_id") == hypothesis_id, f"{code_prefix}_ID")
    _assert_true(entry.get("status") == REQUIRED_TERMINAL_STATUS, f"{code_prefix}_STATUS")
    _assert_true(entry.get("treatment_type") == REQUIRED_TREATMENT_TYPE, f"{code_prefix}_TREATMENT")
    _assert_true(entry.get("development_only") is True, f"{code_prefix}_DEV_ONLY")
    _assert_true(entry.get("holdout_allowed") is False, f"{code_prefix}_HOLDOUT_ALLOWED")
    _assert_true(entry.get("evaluation_authorized") is False, f"{code_prefix}_EVAL_AUTHORIZED")
    _assert_true(entry.get("evaluation_executed") is True, f"{code_prefix}_EVAL_EXECUTED")
    _assert_true(entry.get("evaluation_started") is True, f"{code_prefix}_EVAL_STARTED")
    _assert_true(entry.get("evaluation_completed") is False, f"{code_prefix}_EVAL_COMPLETED")
    _assert_true(int(entry.get("evaluation_run_count", -1)) == 1, f"{code_prefix}_RUN_COUNT")
    _assert_true(int(entry.get("evaluation_run_limit") or 0) == 1, f"{code_prefix}_RUN_LIMIT")
    _assert_true(
        entry.get("result_class") == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE",
        f"{code_prefix}_RESULT_CLASS",
    )
    _assert_true(entry.get("economic_verdict") == "NOT_EVALUATED", f"{code_prefix}_ECONOMIC")
    _assert_true(entry.get("pass") is False, f"{code_prefix}_PASS_MUST_BE_FALSE")
    _assert_true(entry.get("fail") is False, f"{code_prefix}_FAIL_MUST_BE_FALSE")
    _assert_true(entry.get("rerun_allowed") is False, f"{code_prefix}_RERUN_FORBIDDEN")


def _assert_terminal_fail_entry(
    entry: Mapping[str, Any],
    *,
    hypothesis_id: str,
    code_prefix: str,
) -> None:
    _assert_true(isinstance(entry, Mapping), f"{code_prefix}_ENTRY_TYPE")
    _assert_true(entry.get("hypothesis_id") == hypothesis_id, f"{code_prefix}_ID")
    _assert_true(entry.get("status") == REQUIRED_TERMINAL_FAIL_STATUS, f"{code_prefix}_STATUS")
    _assert_true(entry.get("treatment_type") == REQUIRED_TREATMENT_TYPE, f"{code_prefix}_TREATMENT")
    _assert_true(entry.get("development_only") is True, f"{code_prefix}_DEV_ONLY")
    _assert_true(entry.get("holdout_allowed") is False, f"{code_prefix}_HOLDOUT_ALLOWED")
    _assert_true(entry.get("evaluation_authorized") is False, f"{code_prefix}_EVAL_AUTHORIZED")
    _assert_true(entry.get("evaluation_executed") is True, f"{code_prefix}_EVAL_EXECUTED")
    _assert_true(entry.get("evaluation_started") is True, f"{code_prefix}_EVAL_STARTED")
    _assert_true(entry.get("evaluation_completed") is True, f"{code_prefix}_EVAL_COMPLETED")
    _assert_true(int(entry.get("evaluation_run_count", -1)) == 1, f"{code_prefix}_RUN_COUNT")
    _assert_true(int(entry.get("evaluation_run_limit") or 0) == 1, f"{code_prefix}_RUN_LIMIT")
    _assert_true(entry.get("result_class") == "FAIL", f"{code_prefix}_RESULT_CLASS")
    _assert_true(entry.get("economic_verdict") == "FAIL", f"{code_prefix}_ECONOMIC")
    _assert_true(entry.get("pass") is False, f"{code_prefix}_PASS_MUST_BE_FALSE")
    _assert_true(entry.get("fail") is True, f"{code_prefix}_FAIL_MUST_BE_TRUE")
    _assert_true(entry.get("rerun_allowed") is False, f"{code_prefix}_RERUN_FORBIDDEN")
    _assert_true(entry.get("acceptance_criteria_met") is False, f"{code_prefix}_ACCEPTANCE")


def _assert_terminal_pass_entry(
    entry: Mapping[str, Any],
    *,
    hypothesis_id: str,
    code_prefix: str,
) -> None:
    _assert_true(isinstance(entry, Mapping), f"{code_prefix}_ENTRY_TYPE")
    _assert_true(entry.get("hypothesis_id") == hypothesis_id, f"{code_prefix}_ID")
    _assert_true(entry.get("status") == REQUIRED_TERMINAL_PASS_STATUS, f"{code_prefix}_STATUS")
    _assert_true(entry.get("treatment_type") == REQUIRED_TREATMENT_TYPE, f"{code_prefix}_TREATMENT")
    _assert_true(entry.get("development_only") is True, f"{code_prefix}_DEV_ONLY")
    _assert_true(entry.get("holdout_allowed") is False, f"{code_prefix}_HOLDOUT_ALLOWED")
    _assert_true(entry.get("evaluation_authorized") is False, f"{code_prefix}_EVAL_AUTHORIZED")
    _assert_true(entry.get("evaluation_executed") is True, f"{code_prefix}_EVAL_EXECUTED")
    _assert_true(entry.get("evaluation_started") is True, f"{code_prefix}_EVAL_STARTED")
    _assert_true(entry.get("evaluation_completed") is True, f"{code_prefix}_EVAL_COMPLETED")
    _assert_true(int(entry.get("evaluation_run_count", -1)) == 1, f"{code_prefix}_RUN_COUNT")
    _assert_true(int(entry.get("evaluation_run_limit") or 0) == 1, f"{code_prefix}_RUN_LIMIT")
    _assert_true(entry.get("result_class") == "PASS", f"{code_prefix}_RESULT_CLASS")
    _assert_true(entry.get("economic_verdict") == "PASS", f"{code_prefix}_ECONOMIC")
    _assert_true(entry.get("pass") is True, f"{code_prefix}_PASS_MUST_BE_TRUE")
    _assert_true(entry.get("fail") is False, f"{code_prefix}_FAIL_MUST_BE_FALSE")
    _assert_true(entry.get("acceptance_criteria_met") is True, f"{code_prefix}_ACCEPTANCE")
    _assert_true(entry.get("rerun_allowed") is False, f"{code_prefix}_RERUN_FORBIDDEN")
    _assert_true(entry.get("run_slot_consumed") is True, f"{code_prefix}_SLOT")
    _assert_true(entry.get("panel_backtest_executed") is True, f"{code_prefix}_PANEL")
    _assert_true(entry.get("v8_reopen_allowed") is False, f"{code_prefix}_REOPEN")
    _assert_true(entry.get("v8_rerun_forbidden") is True, f"{code_prefix}_V8_RERUN")


def _assert_terminal_infrastructure_entry(
    entry: Mapping[str, Any],
    *,
    hypothesis_id: str,
    code_prefix: str,
) -> None:
    _assert_true(isinstance(entry, Mapping), f"{code_prefix}_ENTRY_TYPE")
    _assert_true(entry.get("hypothesis_id") == hypothesis_id, f"{code_prefix}_ID")
    _assert_true(entry.get("status") == REQUIRED_TERMINAL_INFRA_STATUS, f"{code_prefix}_STATUS")
    _assert_true(entry.get("treatment_type") == REQUIRED_TREATMENT_TYPE, f"{code_prefix}_TREATMENT")
    _assert_true(entry.get("development_only") is True, f"{code_prefix}_DEV_ONLY")
    _assert_true(entry.get("holdout_allowed") is False, f"{code_prefix}_HOLDOUT_ALLOWED")
    _assert_true(entry.get("evaluation_authorized") is False, f"{code_prefix}_EVAL_AUTHORIZED")
    _assert_true(entry.get("evaluation_executed") is True, f"{code_prefix}_EVAL_EXECUTED")
    _assert_true(entry.get("evaluation_started") is True, f"{code_prefix}_EVAL_STARTED")
    _assert_true(entry.get("evaluation_completed") is False, f"{code_prefix}_EVAL_COMPLETED")
    _assert_true(int(entry.get("evaluation_run_count", -1)) == 1, f"{code_prefix}_RUN_COUNT")
    _assert_true(int(entry.get("evaluation_run_limit") or 0) == 1, f"{code_prefix}_RUN_LIMIT")
    _assert_true(
        entry.get("result_class") == "INFRASTRUCTURE_FAILURE", f"{code_prefix}_RESULT_CLASS"
    )
    _assert_true(entry.get("economic_verdict") == "NOT_EVALUATED", f"{code_prefix}_ECONOMIC")
    _assert_true(entry.get("pass") is False, f"{code_prefix}_PASS_MUST_BE_FALSE")
    _assert_true(entry.get("fail") is False, f"{code_prefix}_FAIL_MUST_BE_FALSE")
    _assert_true(entry.get("rerun_allowed") is False, f"{code_prefix}_RERUN_FORBIDDEN")
    _assert_true(entry.get("acceptance_criteria_met") is False, f"{code_prefix}_ACCEPTANCE")


def validate_backlog_contract(backlog: Mapping[str, Any]) -> dict[str, Any]:
    _assert_true(
        backlog.get("status") == REQUIRED_STATUS,
        "STATUS_NOT_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS",
    )
    _assert_true(
        backlog.get("lifecycle_contract_id") == LIFECYCLE_CONTRACT_ID,
        "LIFECYCLE_CONTRACT_ID_MISMATCH",
    )
    _assert_true(
        backlog.get("lifecycle_contract_ref") == LIFECYCLE_CONTRACT_REL_PATH,
        "LIFECYCLE_CONTRACT_REF_MISMATCH",
    )
    _assert_true(
        backlog.get("lifecycle_authority") == REQUIRED_LIFECYCLE_AUTHORITY,
        "LIFECYCLE_AUTHORITY_MISMATCH",
    )
    _assert_true(backlog.get("explicit_closeout_decision") is False, "UNEXPECTED_CLOSEOUT_DECISION")
    _assert_true(backlog.get("explicit_waiting_decision") is True, "WAITING_DECISION_REQUIRED")
    _assert_true(backlog.get("lane_auto_closed") is False, "LANE_AUTO_CLOSED_FORBIDDEN")
    _assert_true(
        backlog.get("entry_eligibility_lane_status") == REQUIRED_ENTRY_ELIGIBILITY_LANE_STATUS,
        "ENTRY_ELIGIBILITY_LANE_STATUS_NOT_CANONICAL",
    )
    _assert_true(
        backlog.get("entry_eligibility_lane_status_authority")
        == REQUIRED_ENTRY_ELIGIBILITY_STATUS_AUTHORITY,
        "ENTRY_ELIGIBILITY_STATUS_AUTHORITY_MISMATCH",
    )
    _assert_true(backlog.get("canonical_ssot") is True, "NOT_CANONICAL_SSOT")
    _assert_true(
        backlog.get("exactly_one_authoritative_truth") is True,
        "NOT_EXACTLY_ONE_AUTHORITATIVE_TRUTH",
    )
    _assert_true(
        backlog.get("productive_trading_logic_included") is False,
        "PRODUCTIVE_TRADING_LOGIC_INCLUDED",
    )
    # Top-level evaluation_authorized may become true after separate ratification
    # (authorized for separate run; not yet executed). Validated against V7 lifecycle below.
    _assert_true(backlog.get("backtest_authorized") is False, "BACKTEST_AUTHORIZED")
    _assert_true(
        backlog.get("evaluation_results_embedded") is False,
        "EVALUATION_RESULTS_EMBEDDED_FLAG",
    )
    _assert_true(
        int(backlog.get("development_run_count", -1)) == 8, "DEVELOPMENT_RUN_COUNT_MUST_BE_8"
    )
    _assert_true(backlog.get("dataset_id") == REQUIRED_DATASET_ID, "DATASET_ID_MISMATCH")
    _assert_true(backlog.get("dataset_class") == "DEVELOPMENT_ONLY", "DATASET_CLASS")
    _assert_true(backlog.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _assert_true(backlog.get("sealed_holdout_id") == HOLDOUT_OPAQUE_ID, "HOLDOUT_ID_MISMATCH")
    _assert_true(
        backlog.get("required_treatment_type") == REQUIRED_TREATMENT_TYPE,
        "TREATMENT_TYPE_MISMATCH",
    )
    _assert_true(
        backlog.get("research_question") == REQUIRED_RESEARCH_QUESTION,
        "RESEARCH_QUESTION_MISMATCH",
    )
    _assert_true(
        backlog.get("research_question_scope_selected") == "EXIT_EFFICIENCY_ONLY",
        "SCOPE_MUST_BE_EXIT_EFFICIENCY_ONLY",
    )
    _assert_true(
        backlog.get("short_side_hypothesis_preregistered") is False,
        "SHORT_SIDE_HYPOTHESIS_PREREGISTERED",
    )
    _assert_true(
        backlog.get("holdout_candidate_preregistered") is False,
        "HOLDOUT_CANDIDATE_PREREGISTERED",
    )
    _assert_true(
        backlog.get("cost_structure_hypothesis_preregistered") is False,
        "COST_STRUCTURE_HYPOTHESIS_PREREGISTERED",
    )

    banned = _contains_banned_result_keys(backlog)
    _assert_true(not banned, "EMBEDDED_RESULT_METRICS", ", ".join(banned[:8]))

    runtime = backlog.get("runtime_policy")
    _assert_true(isinstance(runtime, Mapping), "RUNTIME_POLICY_MISSING")
    assert isinstance(runtime, Mapping)
    for key in (
        "runtime_activated",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
        "capital_activated",
    ):
        _assert_true(runtime.get(key) is False, f"RUNTIME_UNLOCKED:{key}")

    promo = backlog.get("promotion_and_economic_gate_policy")
    _assert_true(isinstance(promo, Mapping), "PROMOTION_POLICY_MISSING")
    assert isinstance(promo, Mapping)
    _assert_true(promo.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _assert_true(promo.get("promotion_gate_open") is False, "PROMOTION_GATE_OPEN")
    _assert_true(
        promo.get("economic_validity_offline_gate_pass") is False,
        "ECONOMIC_GATE_OPEN",
    )
    _assert_true(promo.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN_FLAG")

    open_cands = backlog.get("open_unpreregistered_candidates")
    _assert_true(isinstance(open_cands, list), "OPEN_CANDIDATES_MISSING")
    assert isinstance(open_cands, list)
    _assert_true(len(open_cands) == 0, "OPEN_UNPREREGISTERED_MUST_BE_EMPTY")

    competing = backlog.get("competing_open_hypotheses")
    _assert_true(isinstance(competing, list), "COMPETING_OPEN_MISSING")
    assert isinstance(competing, list)
    _assert_true(len(competing) == 0, "COMPETING_OPEN_MUST_BE_EMPTY")

    rules = backlog.get("governance_rules")
    _assert_true(isinstance(rules, Mapping), "GOVERNANCE_RULES_MISSING")
    assert isinstance(rules, Mapping)
    _assert_true(
        rules.get("max_concurrent_definition_only_preregistrations") == 1, "MAX_CONCURRENT"
    )
    _assert_true(rules.get("development_runs_per_hypothesis") == 1, "DEV_RUNS_PER_HYP")
    _assert_true(rules.get("holdout_use_forbidden") is True, "HOLDOUT_USE_ALLOWED")
    _assert_true(
        rules.get("short_side_parallel_hypothesis_forbidden") is True,
        "SHORT_SIDE_PARALLEL_ALLOWED",
    )
    _assert_true(
        rules.get("entry_eligibility_reopen_forbidden") is True,
        "ENTRY_ELIGIBILITY_REOPEN_ALLOWED",
    )
    _assert_true(rules.get("economic_gate_closed") is True, "ECONOMIC_GATE_NOT_CLOSED")
    _assert_true(rules.get("promotion_closed") is True, "PROMOTION_NOT_CLOSED")
    _assert_true(rules.get("preregistered_count_exact") == 0, "PREREGISTERED_COUNT_RULE")
    _assert_true(rules.get("open_unpreregistered_count_exact") == 0, "OPEN_COUNT_RULE")

    preregistered = backlog.get("preregistered_hypotheses")
    _assert_true(isinstance(preregistered, list), "PREREGISTERED_MISSING")
    assert isinstance(preregistered, list)
    _assert_true(len(preregistered) == 0, "PREREGISTERED_COUNT", str(len(preregistered)))
    _assert_true(backlog.get("evaluation_authorized") is False, "TOP_EVAL_AUTHORIZED")
    _assert_true(
        backlog.get("next_canonical_step") == REQUIRED_V8_NEXT_STEP,
        "NEXT_STEP_AFTER_V8_TERMINAL",
    )

    terminal = backlog.get("terminal_hypotheses")
    _assert_true(isinstance(terminal, list), "TERMINAL_MISSING")
    assert isinstance(terminal, list)
    _assert_true(len(terminal) == 8, "TERMINAL_COUNT", str(len(terminal)))
    by_id = {str(e.get("hypothesis_id")): e for e in terminal if isinstance(e, Mapping)}
    _assert_true(REQUIRED_HYPOTHESIS_ID in by_id, "TERMINAL_V1_MISSING")
    _assert_true(REQUIRED_V2_HYPOTHESIS_ID in by_id, "TERMINAL_V2_MISSING")
    _assert_true(REQUIRED_V3_HYPOTHESIS_ID in by_id, "TERMINAL_V3_MISSING")
    _assert_true(REQUIRED_V4_HYPOTHESIS_ID in by_id, "TERMINAL_V4_MISSING")
    _assert_true(REQUIRED_V5_HYPOTHESIS_ID in by_id, "TERMINAL_V5_MISSING")
    _assert_true(REQUIRED_V6_HYPOTHESIS_ID in by_id, "TERMINAL_V6_MISSING")
    _assert_true(REQUIRED_V7_HYPOTHESIS_ID in by_id, "TERMINAL_V7_MISSING")
    _assert_true(REQUIRED_V8_HYPOTHESIS_ID in by_id, "TERMINAL_V8_MISSING")
    _assert_terminal_inconclusive_entry(
        by_id[REQUIRED_HYPOTHESIS_ID],
        hypothesis_id=REQUIRED_HYPOTHESIS_ID,
        code_prefix="TERMINAL_V1",
    )
    _assert_terminal_inconclusive_entry(
        by_id[REQUIRED_V2_HYPOTHESIS_ID],
        hypothesis_id=REQUIRED_V2_HYPOTHESIS_ID,
        code_prefix="TERMINAL_V2",
    )
    _assert_terminal_fail_entry(
        by_id[REQUIRED_V3_HYPOTHESIS_ID],
        hypothesis_id=REQUIRED_V3_HYPOTHESIS_ID,
        code_prefix="TERMINAL_V3",
    )
    _assert_terminal_infrastructure_entry(
        by_id[REQUIRED_V4_HYPOTHESIS_ID],
        hypothesis_id=REQUIRED_V4_HYPOTHESIS_ID,
        code_prefix="TERMINAL_V4",
    )
    _assert_terminal_infrastructure_entry(
        by_id[REQUIRED_V5_HYPOTHESIS_ID],
        hypothesis_id=REQUIRED_V5_HYPOTHESIS_ID,
        code_prefix="TERMINAL_V5",
    )
    v5 = by_id[REQUIRED_V5_HYPOTHESIS_ID]
    _assert_true(v5.get("new_evaluation_not_rerun") is True, "TERMINAL_V5_NOT_RERUN")
    _assert_true(v5.get("v4_partial_results_reused") is False, "TERMINAL_V5_PARTIAL_REUSE")
    _assert_true(v5.get("v4_economic_result_imported") is False, "TERMINAL_V5_ECON_IMPORT")
    _assert_true(v5.get("v4_rerun_forbidden") is True, "TERMINAL_V5_V4_RERUN")
    _assert_true(
        v5.get("lifecycle_checkpoint_surface") == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
        "TERMINAL_V5_LIFECYCLE",
    )
    _assert_true(
        v5.get("observability_surface") == REQUIRED_OBSERVABILITY_SURFACE,
        "TERMINAL_V5_OBSERVABILITY",
    )
    _assert_true(
        v5.get("predecessor_hypothesis_id") == REQUIRED_V4_HYPOTHESIS_ID,
        "TERMINAL_V5_PREDECESSOR",
    )
    _assert_true(
        v5.get("process_death_root_cause")
        == "PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL",
        "TERMINAL_V5_ROOT_CAUSE",
    )
    _assert_true(v5.get("baseline_members_completed") == "3/46", "TERMINAL_V5_BASELINE")
    _assert_true(v5.get("treatment_members_completed") == "0/46", "TERMINAL_V5_TREATMENT")
    v2 = by_id[REQUIRED_V2_HYPOTHESIS_ID]
    _assert_true(v2.get("new_evaluation_not_rerun") is True, "TERMINAL_V2_NOT_RERUN")
    _assert_true(v2.get("v1_partial_results_reused") is False, "TERMINAL_V2_PARTIAL_REUSE")
    _assert_true(
        v2.get("observability_surface") == REQUIRED_OBSERVABILITY_SURFACE,
        "TERMINAL_V2_OBSERVABILITY",
    )
    _assert_true(
        v2.get("predecessor_hypothesis_id") == REQUIRED_HYPOTHESIS_ID,
        "TERMINAL_V2_PREDECESSOR",
    )
    v3 = by_id[REQUIRED_V3_HYPOTHESIS_ID]
    _assert_true(v3.get("new_evaluation_not_rerun") is True, "TERMINAL_V3_NOT_RERUN")
    _assert_true(v3.get("v2_partial_results_reused") is False, "TERMINAL_V3_PARTIAL_REUSE")
    _assert_true(v3.get("v2_economic_result_imported") is False, "TERMINAL_V3_ECON_IMPORT")
    _assert_true(
        v3.get("observability_surface") == REQUIRED_OBSERVABILITY_SURFACE,
        "TERMINAL_V3_OBSERVABILITY",
    )
    _assert_true(
        v3.get("falsy_zero_hygiene_surface") == REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
        "TERMINAL_V3_FALSY_ZERO",
    )
    _assert_true(
        v3.get("predecessor_hypothesis_id") == REQUIRED_V2_HYPOTHESIS_ID,
        "TERMINAL_V3_PREDECESSOR",
    )
    _assert_true(
        v3.get("decision_reason") == "identical_arms_no_exit_divergence",
        "TERMINAL_V3_REASON",
    )
    v4 = by_id[REQUIRED_V4_HYPOTHESIS_ID]
    _assert_true(v4.get("new_evaluation_not_rerun") is True, "TERMINAL_V4_NOT_RERUN")
    _assert_true(v4.get("v3_partial_results_reused") is False, "TERMINAL_V4_PARTIAL_REUSE")
    _assert_true(v4.get("v3_economic_result_imported") is False, "TERMINAL_V4_ECON_IMPORT")
    _assert_true(
        v4.get("observability_surface") == REQUIRED_OBSERVABILITY_SURFACE,
        "TERMINAL_V4_OBSERVABILITY",
    )
    _assert_true(
        v4.get("falsy_zero_hygiene_surface") == REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
        "TERMINAL_V4_FALSY_ZERO",
    )
    _assert_true(
        v4.get("binding_fix_surface") == REQUIRED_BINDING_FIX_SURFACE,
        "TERMINAL_V4_BINDING_FIX",
    )
    _assert_true(
        v4.get("predecessor_hypothesis_id") == REQUIRED_V3_HYPOTHESIS_ID,
        "TERMINAL_V4_PREDECESSOR",
    )
    _assert_terminal_fail_entry(
        by_id[REQUIRED_V6_HYPOTHESIS_ID],
        hypothesis_id=REQUIRED_V6_HYPOTHESIS_ID,
        code_prefix="TERMINAL_V6",
    )
    v6 = by_id[REQUIRED_V6_HYPOTHESIS_ID]
    _assert_true(v6.get("new_evaluation_not_rerun") is True, "TERMINAL_V6_NOT_RERUN")
    _assert_true(v6.get("mechanism_id") == REQUIRED_V6_MECHANISM_ID, "TERMINAL_V6_MECHANISM")
    _assert_true(
        v6.get("identical_exit_mechanism_to_development_v5") is False,
        "TERMINAL_V6_EXIT_CHANGED",
    )
    _assert_true(v6.get("economic_change_vs_development_v5") is True, "TERMINAL_V6_ECON_CHANGE")
    _assert_true(v6.get("v5_partial_results_reused") is False, "TERMINAL_V6_V5_PARTIAL")
    _assert_true(
        v6.get("lifecycle_checkpoint_surface") == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
        "TERMINAL_V6_LIFECYCLE",
    )
    _assert_true(
        v6.get("predecessor_hypothesis_id") == REQUIRED_V5_HYPOTHESIS_ID,
        "TERMINAL_V6_PREDECESSOR",
    )
    _assert_true(
        v6.get("decision_reason") == "NET_PROFIT_FACTOR_NOT_IMPROVED",
        "TERMINAL_V6_REASON",
    )
    _assert_true(v6.get("baseline_members_completed") == "46/46", "TERMINAL_V6_BASELINE")
    _assert_true(v6.get("treatment_members_completed") == "46/46", "TERMINAL_V6_TREATMENT")
    _assert_terminal_inconclusive_entry(
        by_id[REQUIRED_V7_HYPOTHESIS_ID],
        hypothesis_id=REQUIRED_V7_HYPOTHESIS_ID,
        code_prefix="TERMINAL_V7",
    )
    v7 = by_id[REQUIRED_V7_HYPOTHESIS_ID]
    _assert_true(v7.get("new_evaluation_not_rerun") is True, "TERMINAL_V7_NOT_RERUN")
    _assert_true(v7.get("mechanism_id") == REQUIRED_V7_MECHANISM_ID, "TERMINAL_V7_MECHANISM")
    _assert_true(v7.get("v6_partial_results_reused") is False, "TERMINAL_V7_V6_PARTIAL")
    _assert_true(
        v7.get("lifecycle_checkpoint_surface") == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
        "TERMINAL_V7_LIFECYCLE",
    )
    _assert_true(
        v7.get("predecessor_hypothesis_id") == REQUIRED_V6_HYPOTHESIS_ID,
        "TERMINAL_V7_PREDECESSOR",
    )
    _assert_true(
        v7.get("process_death_root_cause") == REQUIRED_V7_DIAGNOSTIC_CLASS,
        "TERMINAL_V7_ROOT_CAUSE",
    )
    _assert_true(
        v7.get("development_preregistration_digest") == REQUIRED_V7_PREREGISTRATION_DIGEST,
        "TERMINAL_V7_DIGEST",
    )
    _assert_true(v7.get("baseline_members_completed") == "0/46", "TERMINAL_V7_BASELINE")
    _assert_true(v7.get("treatment_members_completed") == "0/46", "TERMINAL_V7_TREATMENT")
    _assert_true(v7.get("panel_backtest_executed") is False, "TERMINAL_V7_PANEL")
    _assert_true(
        v7.get("failure_class") == "FROZEN_EXIT_PARAMETERS_MISMATCH", "TERMINAL_V7_FAILURE_CLASS"
    )
    _assert_true(v7.get("failure_timing") == "BEFORE_PANEL_ACCESS", "TERMINAL_V7_FAILURE_TIMING")
    _assert_true(v7.get("v7_reopen_allowed") is False, "TERMINAL_V7_REOPEN")
    _assert_true(v7.get("strategy_fail") is False, "TERMINAL_V7_NOT_STRATEGY_FAIL")
    _assert_true(v7.get("economic_fail") is False, "TERMINAL_V7_NOT_ECONOMIC_FAIL")
    _assert_true(v7.get("measurement_pass") is False, "TERMINAL_V7_NOT_MEASUREMENT_PASS")
    _assert_true(v7.get("development_metrics_produced") is False, "TERMINAL_V7_NO_DEV_METRICS")
    _assert_true(v7.get("economic_metrics_produced") is False, "TERMINAL_V7_NO_ECON_METRICS")
    _assert_terminal_pass_entry(
        by_id[REQUIRED_V8_HYPOTHESIS_ID],
        hypothesis_id=REQUIRED_V8_HYPOTHESIS_ID,
        code_prefix="TERMINAL_V8",
    )
    v8 = by_id[REQUIRED_V8_HYPOTHESIS_ID]
    _assert_true(v8.get("new_evaluation_not_rerun") is True, "TERMINAL_V8_NOT_RERUN")
    _assert_true(v8.get("mechanism_id") == REQUIRED_V8_MECHANISM_ID, "TERMINAL_V8_MECHANISM")
    _assert_true(v8.get("frozen_parameters_complete") is True, "TERMINAL_V8_FROZEN")
    _assert_true(v8.get("not_a_v7_reopen") is True, "TERMINAL_V8_NOT_V7_REOPEN")
    _assert_true(v8.get("not_a_v7_retry") is True, "TERMINAL_V8_NOT_V7_RETRY")
    _assert_true(
        v8.get("development_preregistration_digest") == REQUIRED_V8_PREREGISTRATION_DIGEST,
        "TERMINAL_V8_DIGEST",
    )
    _assert_true(
        v8.get("predecessor_hypothesis_id") == REQUIRED_V7_HYPOTHESIS_ID,
        "TERMINAL_V8_PREDECESSOR",
    )
    _assert_true(
        v8.get("predecessor_result_class") == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE",
        "TERMINAL_V8_PREDECESSOR_RESULT",
    )
    _assert_true(
        v8.get("decision_reason") == REQUIRED_V8_DECISION_REASON,
        "TERMINAL_V8_REASON",
    )
    _assert_true(
        v8.get("lifecycle_terminal_state") == REQUIRED_V8_LIFECYCLE_TERMINAL,
        "TERMINAL_V8_LIFECYCLE",
    )
    _assert_true(v8.get("baseline_members_completed") == "46/46", "TERMINAL_V8_BASELINE")
    _assert_true(v8.get("treatment_members_completed") == "46/46", "TERMINAL_V8_TREATMENT")
    _assert_true(
        v8.get("lifecycle_checkpoint_surface") == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
        "TERMINAL_V8_CHECKPOINT",
    )

    non_actions = backlog.get("explicit_non_actions") or []
    _assert_true("NO_V2_RERUN" in non_actions, "NO_V2_RERUN_NON_ACTION_REQUIRED")
    _assert_true("NO_V3_RERUN" in non_actions, "NO_V3_RERUN_NON_ACTION_REQUIRED")
    _assert_true("NO_HOLDOUT_AFTER_FAIL" in non_actions, "NO_HOLDOUT_AFTER_FAIL_REQUIRED")
    _assert_true("NO_RETUNING_AFTER_FAIL" in non_actions, "NO_RETUNING_AFTER_FAIL_REQUIRED")
    _assert_true("NO_V4_RERUN" in non_actions, "NO_V4_RERUN_NON_ACTION_REQUIRED")
    _assert_true("NO_V5_RERUN" in non_actions, "NO_V5_RERUN_REQUIRED")
    _assert_true("NO_V6_RERUN" in non_actions, "NO_V6_RERUN_REQUIRED")
    _assert_true("NO_V7_RERUN" in non_actions, "NO_V7_RERUN_REQUIRED")
    _assert_true("NO_V7_REOPEN" in non_actions, "NO_V7_REOPEN_REQUIRED")
    _assert_true("NO_V8_RERUN" in non_actions, "NO_V8_RERUN_REQUIRED")
    _assert_true("NO_V8_REOPEN" in non_actions, "NO_V8_REOPEN_REQUIRED")
    _assert_true("NO_HOLDOUT_AFTER_PASS" in non_actions, "NO_HOLDOUT_AFTER_PASS_REQUIRED")
    _assert_true(
        "NO_RUNTIME_PROMOTION_FROM_DEVELOPMENT_PASS" in non_actions,
        "NO_RUNTIME_PROMOTION_FROM_DEVELOPMENT_PASS_REQUIRED",
    )
    _assert_true(
        "NO_V7_EVALUATION_IN_THIS_SLICE" not in non_actions,
        "NO_V7_EVALUATION_IN_THIS_SLICE_MUST_BE_ABSENT",
    )
    _assert_true(
        "NO_V8_EVALUATION_IN_THIS_SLICE" not in non_actions,
        "NO_V8_EVALUATION_IN_THIS_SLICE_MUST_BE_ABSENT",
    )
    _assert_true("NO_V7_AUTO_CREATE" in non_actions, "NO_V7_AUTO_CREATE_REQUIRED")
    _assert_true("NO_V8_AUTO_CREATE" in non_actions, "NO_V8_AUTO_CREATE_REQUIRED")
    _assert_true("NO_V9_AUTO_CREATE" in non_actions, "NO_V9_AUTO_CREATE_REQUIRED")
    _assert_true("NO_V6_AUTO_CREATE" not in non_actions, "NO_V6_AUTO_CREATE_MUST_BE_ABSENT")
    _assert_true("NO_V5_AUTO_CREATE" not in non_actions, "NO_V5_AUTO_CREATE_MUST_BE_ABSENT")
    _assert_true("NO_V3_ECONOMIC_RESULT_IMPORT" in non_actions, "NO_V3_ECON_IMPORT_REQUIRED")
    _assert_true("NO_V4_AUTO_CREATE" not in non_actions, "NO_V4_AUTO_CREATE_MUST_BE_ABSENT")

    # Shared post-terminal lifecycle is the sole status authority.
    open_cands = list(backlog.get("open_unpreregistered_candidates") or [])
    prereg = list(backlog.get("preregistered_hypotheses") or [])
    lifecycle_snapshot = {
        "status": backlog.get("status"),
        "open_unpreregistered_candidates": open_cands,
        "preregistered_hypotheses": prereg,
        "explicit_closeout_decision": bool(backlog.get("explicit_closeout_decision")),
        "explicit_waiting_decision": bool(backlog.get("explicit_waiting_decision")),
        "go_executable": False,
        "auto_created_successor": False,
        "implicit_successor": False,
        "lane_auto_closed": bool(backlog.get("lane_auto_closed")),
    }
    try:
        lifecycle_report = validate_lane_snapshot(lifecycle_snapshot)
    except ResearchLaneLifecycleContractError as exc:
        raise BacklogValidationError(f"LIFECYCLE_CONTRACT_REJECTED:{exc}") from exc
    _assert_true(lifecycle_report.get("valid") is True, "LIFECYCLE_SNAPSHOT_INVALID")
    _assert_true(lifecycle_report.get("status") == REQUIRED_STATUS, "LIFECYCLE_STATUS_DRIFT")
    _assert_true(
        lifecycle_report.get("inventory_non_empty") is False,
        "LIFECYCLE_INVENTORY_MUST_BE_EMPTY",
    )
    resolved = resolve_post_terminal_transition(
        result_class="PASS",
        inventory_non_empty_flag=False,
    )
    # Empty-inventory post-terminal resolution still yields the pre-decision holding
    # state; the live lane has already executed DECLARE_AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS.
    _assert_true(
        resolved.get("next_state") == POST_TERMINAL_EMPTY_INVENTORY_STATE,
        "POST_TERMINAL_RESOLUTION_DRIFT",
        str(resolved.get("next_state")),
    )
    _assert_true(
        resolved.get("operator_decision_required") is True,
        "POST_TERMINAL_OPERATOR_DECISION_NOT_REQUIRED",
    )
    _assert_true(
        REQUIRED_OPERATOR_DECISION in (resolved.get("allowed_operator_decisions") or []),
        "DECLARE_AWAITING_NOT_IN_ALLOWED_DECISIONS",
    )

    # Read-only sibling mirror: Entry Eligibility status under shared contract (no mutation).
    entry_path = _repo_root() / ENTRY_ELIGIBILITY_BACKLOG_REL_PATH
    _assert_true(entry_path.is_file(), "ENTRY_ELIGIBILITY_BACKLOG_MISSING", str(entry_path))
    entry_backlog = _load_json(entry_path)
    _assert_true(
        entry_backlog.get("status") == REQUIRED_ENTRY_ELIGIBILITY_LANE_STATUS,
        "ENTRY_ELIGIBILITY_SIBLING_STATUS_DRIFT",
        str(entry_backlog.get("status")),
    )
    _assert_true(
        entry_backlog.get("explicit_waiting_decision") is True,
        "ENTRY_ELIGIBILITY_SIBLING_WAITING_DECISION_REQUIRED",
    )
    _assert_true(
        backlog.get("entry_eligibility_lane_status") == entry_backlog.get("status"),
        "ENTRY_ELIGIBILITY_STATUS_MIRROR_MISMATCH",
    )

    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "explicit_waiting_decision": True,
        "explicit_closeout_decision": False,
        "lane_auto_closed": False,
        "operator_decision": REQUIRED_OPERATOR_DECISION,
        "lifecycle_contract_id": LIFECYCLE_CONTRACT_ID,
        "lifecycle_authority": REQUIRED_LIFECYCLE_AUTHORITY,
        "preregistered_count": 0,
        "terminal_count": 8,
        "open_unpreregistered_count": 0,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "preregistered_hypothesis_id": None,
        "terminal_hypothesis_ids": [
            REQUIRED_HYPOTHESIS_ID,
            REQUIRED_V2_HYPOTHESIS_ID,
            REQUIRED_V3_HYPOTHESIS_ID,
            REQUIRED_V4_HYPOTHESIS_ID,
            REQUIRED_V5_HYPOTHESIS_ID,
            REQUIRED_V6_HYPOTHESIS_ID,
            REQUIRED_V7_HYPOTHESIS_ID,
            REQUIRED_V8_HYPOTHESIS_ID,
        ],
        "development_run_count": 8,
        "evaluation_authorized": False,
        "holdout_forbidden": True,
        "short_side_hypothesis_preregistered": False,
        "holdout_candidate_preregistered": False,
        "runtime_locked": True,
        "result_class": "PASS",
        "economic_verdict": "PASS",
        "rerun_allowed": False,
        "v2_evaluation_run_count": 1,
        "v2_is_rerun_of_v1": False,
        "v3_evaluation_run_count": 1,
        "v3_result_class": "FAIL",
        "v3_is_rerun_of_v2": False,
        "v4_evaluation_run_count": 1,
        "v4_result_class": "INFRASTRUCTURE_FAILURE",
        "v4_is_rerun_of_v3": False,
        "v5_evaluation_run_count": 1,
        "v5_result_class": "INFRASTRUCTURE_FAILURE",
        "v5_is_rerun_of_v4": False,
        "v6_evaluation_run_count": 1,
        "v6_result_class": "FAIL",
        "v6_is_rerun_of_v5": False,
        "v7_evaluation_run_count": 1,
        "v7_result_class": "INCONCLUSIVE_INFRASTRUCTURE_FAILURE",
        "v8_evaluation_run_count": 1,
        "v8_result_class": "PASS",
        "observability_surface": REQUIRED_OBSERVABILITY_SURFACE,
        "falsy_zero_hygiene_surface": REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
        "binding_fix_surface": REQUIRED_BINDING_FIX_SURFACE,
    }


def load_and_validate_repo_backlog(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / BACKLOG_REL_PATH
    _assert_true(path.is_file(), "BACKLOG_SSOT_MISSING", str(path))
    governance = root / GOVERNANCE_REL_PATH
    _assert_true(governance.is_file(), "GOVERNANCE_DOC_MISSING", str(governance))
    backlog = _load_json(path)
    report = validate_backlog_contract(backlog)
    report["backlog_path"] = BACKLOG_REL_PATH
    report["governance_path"] = GOVERNANCE_REL_PATH
    return report


def assert_exactly_one_exit_efficiency_backlog_ssot(repo_root: Path | None = None) -> None:
    root = repo_root or _repo_root()
    matches = sorted((root / "config" / "research").glob("*open*mr*exit_efficiency*backlog*.json"))
    unique = sorted({p.resolve() for p in matches})
    _assert_true(len(unique) == 1, "EXIT_EFFICIENCY_BACKLOG_SSOT_COUNT", str(unique))
    _assert_true(
        unique[0] == (root / BACKLOG_REL_PATH).resolve(),
        "EXIT_EFFICIENCY_BACKLOG_SSOT_PATH_UNEXPECTED",
        str(unique[0]),
    )
