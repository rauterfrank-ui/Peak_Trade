"""Canonical open MR exit-efficiency hypothesis backlog SSOT validator v1.

Definition-only governance. No evaluation, backtest, holdout access, runtime
activation, or productive trading-logic mutation.

Post V7 definition-only preregistration: exactly one DEFINITION_ONLY_PREREGISTERED
candidate (V7 reentry-cooldown) with genuine economic change vs terminal V6 FAIL;
V1-V6 remain terminal; development_run_count=6 (V7 not executed); no V8 auto-create.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1=true"
BACKLOG_REL_PATH = "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
GOVERNANCE_REL_PATH = "docs/governance/CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1.md"
REQUIRED_STATUS = "OPEN_BACKLOG"
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
REQUIRED_PREREGISTERED_STATUS = "DEFINITION_ONLY_PREREGISTERED"


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
    _assert_true(backlog.get("status") == REQUIRED_STATUS, "STATUS_NOT_OPEN_BACKLOG")
    _assert_true(backlog.get("canonical_ssot") is True, "NOT_CANONICAL_SSOT")
    _assert_true(
        backlog.get("exactly_one_authoritative_truth") is True,
        "NOT_EXACTLY_ONE_AUTHORITATIVE_TRUTH",
    )
    _assert_true(
        backlog.get("productive_trading_logic_included") is False,
        "PRODUCTIVE_TRADING_LOGIC_INCLUDED",
    )
    _assert_true(backlog.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _assert_true(backlog.get("backtest_authorized") is False, "BACKTEST_AUTHORIZED")
    _assert_true(
        backlog.get("evaluation_results_embedded") is False,
        "EVALUATION_RESULTS_EMBEDDED_FLAG",
    )
    _assert_true(
        int(backlog.get("development_run_count", -1)) == 6, "DEVELOPMENT_RUN_COUNT_MUST_BE_6"
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
    _assert_true(rules.get("preregistered_count_exact") == 1, "PREREGISTERED_COUNT_RULE")
    _assert_true(rules.get("open_unpreregistered_count_exact") == 0, "OPEN_COUNT_RULE")

    preregistered = backlog.get("preregistered_hypotheses")
    _assert_true(isinstance(preregistered, list), "PREREGISTERED_MISSING")
    assert isinstance(preregistered, list)
    _assert_true(len(preregistered) == 1, "PREREGISTERED_COUNT", str(len(preregistered)))
    pref = preregistered[0]
    _assert_true(isinstance(pref, Mapping), "PREREGISTERED_ENTRY_TYPE")
    assert isinstance(pref, Mapping)
    _assert_true(pref.get("hypothesis_id") == REQUIRED_V7_HYPOTHESIS_ID, "PREREGISTERED_ID")
    _assert_true(pref.get("status") == REQUIRED_PREREGISTERED_STATUS, "PREREGISTERED_STATUS")
    _assert_true(pref.get("evaluation_authorized") is False, "PREREGISTERED_EVAL_AUTHORIZED")
    _assert_true(pref.get("evaluation_executed") is False, "PREREGISTERED_EVAL_EXECUTED")
    _assert_true(pref.get("evaluation_started") is False, "PREREGISTERED_EVAL_STARTED")
    _assert_true(pref.get("evaluation_completed") is False, "PREREGISTERED_EVAL_COMPLETED")
    _assert_true(int(pref.get("evaluation_run_count", -1)) == 0, "PREREGISTERED_RUN_COUNT")
    _assert_true(int(pref.get("evaluation_run_limit") or 0) == 1, "PREREGISTERED_RUN_LIMIT")
    _assert_true(pref.get("result_class") == "NOT_EVALUATED", "PREREGISTERED_RESULT_CLASS")
    _assert_true(pref.get("mechanism_id") == REQUIRED_V7_MECHANISM_ID, "PREREGISTERED_MECHANISM")
    _assert_true(
        pref.get("identical_exit_mechanism_to_development_v6") is False,
        "PREREGISTERED_EXIT_CHANGED",
    )
    _assert_true(
        pref.get("identical_economic_hypothesis_to_development_v6") is False,
        "PREREGISTERED_ECON_CHANGED",
    )
    _assert_true(
        pref.get("economic_change_vs_development_v6") is True, "PREREGISTERED_ECON_CHANGE_FLAG"
    )
    _assert_true(pref.get("v6_rerun_forbidden") is True, "PREREGISTERED_V6_RERUN_FORBIDDEN")
    _assert_true(pref.get("v6_partial_results_reused") is False, "PREREGISTERED_V6_PARTIAL")
    _assert_true(
        pref.get("predecessor_partial_metrics_used") is False, "PREREGISTERED_PARTIAL_METRICS_USED"
    )
    _assert_true(int(pref.get("cooldown_bars", -1)) == 24, "PREREGISTERED_COOLDOWN_BARS")
    _assert_true(
        pref.get("lifecycle_checkpoint_surface") == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
        "PREREGISTERED_LIFECYCLE_SURFACE",
    )
    _assert_true(
        pref.get("predecessor_hypothesis_id") == REQUIRED_V6_HYPOTHESIS_ID,
        "PREREGISTERED_PREDECESSOR",
    )
    _assert_true(
        pref.get("predecessor_result_class") == "FAIL",
        "PREREGISTERED_PREDECESSOR_RESULT",
    )
    _assert_true(
        pref.get("development_preregistration_digest") == REQUIRED_V7_PREREGISTRATION_DIGEST,
        "PREREGISTERED_DIGEST",
    )

    terminal = backlog.get("terminal_hypotheses")
    _assert_true(isinstance(terminal, list), "TERMINAL_MISSING")
    assert isinstance(terminal, list)
    _assert_true(len(terminal) == 6, "TERMINAL_COUNT", str(len(terminal)))
    by_id = {str(e.get("hypothesis_id")): e for e in terminal if isinstance(e, Mapping)}
    _assert_true(REQUIRED_HYPOTHESIS_ID in by_id, "TERMINAL_V1_MISSING")
    _assert_true(REQUIRED_V2_HYPOTHESIS_ID in by_id, "TERMINAL_V2_MISSING")
    _assert_true(REQUIRED_V3_HYPOTHESIS_ID in by_id, "TERMINAL_V3_MISSING")
    _assert_true(REQUIRED_V4_HYPOTHESIS_ID in by_id, "TERMINAL_V4_MISSING")
    _assert_true(REQUIRED_V5_HYPOTHESIS_ID in by_id, "TERMINAL_V5_MISSING")
    _assert_true(REQUIRED_V6_HYPOTHESIS_ID in by_id, "TERMINAL_V6_MISSING")
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

    non_actions = backlog.get("explicit_non_actions") or []
    _assert_true("NO_V2_RERUN" in non_actions, "NO_V2_RERUN_NON_ACTION_REQUIRED")
    _assert_true("NO_V3_RERUN" in non_actions, "NO_V3_RERUN_NON_ACTION_REQUIRED")
    _assert_true("NO_HOLDOUT_AFTER_FAIL" in non_actions, "NO_HOLDOUT_AFTER_FAIL_REQUIRED")
    _assert_true("NO_RETUNING_AFTER_FAIL" in non_actions, "NO_RETUNING_AFTER_FAIL_REQUIRED")
    _assert_true("NO_V4_RERUN" in non_actions, "NO_V4_RERUN_NON_ACTION_REQUIRED")
    _assert_true("NO_V5_RERUN" in non_actions, "NO_V5_RERUN_REQUIRED")
    _assert_true("NO_V6_RERUN" in non_actions, "NO_V6_RERUN_REQUIRED")
    _assert_true(
        "NO_V6_EVALUATION_IN_THIS_SLICE" not in non_actions,
        "NO_V6_EVALUATION_IN_THIS_SLICE_MUST_BE_ABSENT",
    )
    _assert_true(
        "NO_V7_EVALUATION_IN_THIS_SLICE" in non_actions,
        "NO_V7_EVALUATION_IN_THIS_SLICE_REQUIRED",
    )
    _assert_true("NO_V7_AUTO_CREATE" in non_actions, "NO_V7_AUTO_CREATE_REQUIRED")
    _assert_true("NO_V8_AUTO_CREATE" in non_actions, "NO_V8_AUTO_CREATE_REQUIRED")
    _assert_true("NO_V6_AUTO_CREATE" not in non_actions, "NO_V6_AUTO_CREATE_MUST_BE_ABSENT")
    _assert_true("NO_V5_AUTO_CREATE" not in non_actions, "NO_V5_AUTO_CREATE_MUST_BE_ABSENT")
    _assert_true("NO_V3_ECONOMIC_RESULT_IMPORT" in non_actions, "NO_V3_ECON_IMPORT_REQUIRED")
    _assert_true("NO_V4_AUTO_CREATE" not in non_actions, "NO_V4_AUTO_CREATE_MUST_BE_ABSENT")

    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "preregistered_count": 1,
        "terminal_count": 6,
        "open_unpreregistered_count": 0,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "preregistered_hypothesis_id": REQUIRED_V7_HYPOTHESIS_ID,
        "terminal_hypothesis_ids": [
            REQUIRED_HYPOTHESIS_ID,
            REQUIRED_V2_HYPOTHESIS_ID,
            REQUIRED_V3_HYPOTHESIS_ID,
            REQUIRED_V4_HYPOTHESIS_ID,
            REQUIRED_V5_HYPOTHESIS_ID,
            REQUIRED_V6_HYPOTHESIS_ID,
        ],
        "development_run_count": 6,
        "evaluation_authorized": False,
        "holdout_forbidden": True,
        "short_side_hypothesis_preregistered": False,
        "holdout_candidate_preregistered": False,
        "runtime_locked": True,
        "result_class": "INFRASTRUCTURE_FAILURE",
        "economic_verdict": "NOT_EVALUATED",
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
        "v7_evaluation_run_count": 0,
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
