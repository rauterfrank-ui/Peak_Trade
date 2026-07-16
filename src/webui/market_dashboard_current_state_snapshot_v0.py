"""Versioned current-state snapshot for GET /market (display-only SSOT).

Provenance (PR #5242 current-state sync):
- docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md
- config/research/full_canonical_system_economic_evidence_generation_v1_offline_execution_result_v0.json
- research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z
- research/pr5242_source_evidence_manifest_verify_log_retention_repair_v1_20260716T154633Z
- research/pr5242_merge_closeout_full_canonical_system_economic_evidence_generation_v1_offline_execution_v1_20260716T155043Z

No trading authority. No runtime effect. Single dashboard owner — no parallel SSOT.
Display-only binding of already-persisted, manifest-verified Full-Canonical evidence closeout.
PR #5242 did not execute a new economic evaluation and did not rematerialize evidence results.
"""

from __future__ import annotations

from typing import Any, Final

SNAPSHOT_VERSION: Final[str] = "market_dashboard_current_state_snapshot_v0"
SNAPSHOT_OWNER: Final[str] = "src/webui/market_dashboard_current_state_snapshot_v0.py"
RUNBOOK_PROGRESS_OWNER: Final[str] = "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
MA_CROSSOVER_CONFIG_OWNER: Final[str] = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_ma_crossover_v1_economic_evaluation_v1.json"
)
VOL_BREAKOUT_CONFIG_OWNER: Final[str] = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_vol_breakout_v1_economic_evaluation_v1.json"
)
CURRENT_STATE_RESULT_JSON: Final[str] = (
    "config/research/full_canonical_system_economic_evidence_generation_v1_offline_execution_result_v0.json"
)

# Audit-/display-only provenance paths (not loaded at request time).
CURRENT_STATE_PRIMARY_EVIDENCE_DIR: Final[str] = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)
CURRENT_STATE_REPAIR_EVIDENCE_DIR: Final[str] = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/pr5242_source_evidence_manifest_verify_log_retention_repair_v1_20260716T154633Z"
)
CURRENT_STATE_CLOSEOUT_EVIDENCE_DIR: Final[str] = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/pr5242_merge_closeout_full_canonical_system_economic_evidence_generation_v1_"
    "offline_execution_v1_20260716T155043Z"
)

FULL_PARITY_CLOSEOUT_EVIDENCE_REF: Final[str] = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5033_surface_p_semantic_parity_status_binding_fix_v0_20260709T135256Z"
)
ECONOMIC_GAP_SCAN_EVIDENCE_REF: Final[str] = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/system_economic_evidence_admissibility_gap_scan_after_full_parity_v0_20260709T141726Z"
)
NOTION_SYNC_EVIDENCE_REF: Final[str] = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "documentation/bounded_notion_current_state_synchronization_after_step29m_ma_crossover_policy_ratification_v0_20260702T002000Z"
)
RATIFICATION_EVIDENCE_REF: Final[str] = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/rank1_vol_breakout_binding_and_evaluation_ratification_read_only_v0_20260710T063915Z"
)

NEXT_PARITY_SLICE: Final[str] = "CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_V0"
DOCUMENTED_ONLY_LATER_PATH: Final[str] = (
    "REQUEST_OPERATOR_RATIFY_STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_OWNER_NARROW_IMPLEMENTATION_FIX_SCOPE_V0"
)
NEXT_BLOCKER: Final[str] = (
    "FULL_CANONICAL_SYSTEM_ECONOMIC_BASELINE_TERMINAL_FAIL_UNCHANGED_RETRY_FORBIDDEN"
)

CURRENT_ORIGIN_MAIN: Final[str] = "0fdacfae2aa3180925a8b625267de5eb5761eccb"
CURRENT_STATE_SOURCE_PR: Final[int] = 5242
CURRENT_STATE_SOURCE_HEAD: Final[str] = CURRENT_ORIGIN_MAIN

LATEST_MERGED_PR_NUMBER: Final[int] = 5242
LATEST_MERGED_PR_TITLE: Final[str] = (
    "research: execute full canonical system economic evidence generation v1"
)
LATEST_MERGED_PR_STATE: Final[str] = "MERGED"
LATEST_MERGED_PR_SQUASH_COMMIT: Final[str] = CURRENT_ORIGIN_MAIN

CURRENT_RESEARCH_STRATEGY_ID: Final[str] = "bollinger_bands"
CURRENT_RESEARCH_STRATEGY_VERSION: Final[str] = "v2"
CURRENT_RESEARCH_BINDING_ID: Final[str] = (
    "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
)
CURRENT_RESEARCH_STATUS: Final[str] = "COMPLETE_FAIL"
ECONOMIC_STATUS: Final[str] = "FAIL"
TRADE_COUNT: Final[int] = 0
NET_RETURN: Final[float] = 0.0

PRIMARY_SOURCE_MANIFEST_VERIFY_RC: Final[int] = 0
SOURCE_REPAIR_MANIFEST_VERIFY_RC: Final[int] = 0
CLOSEOUT_MANIFEST_VERIFY_RC: Final[int] = 0

ECONOMIC_EVALUATION_EXECUTED: Final[bool] = False
EVIDENCE_RESULTS_REMATERIALIZED: Final[bool] = False
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS: Final[bool] = False
UNCHANGED_RETRY_FORBIDDEN: Final[bool] = True
POLICY_RESCUE_ALLOWED: Final[bool] = False

PR5033_MERGE_COMMIT: Final[str] = "720b59bed1c012e873c8e1207b057ebd5fa8f21a"
PR5033_HEAD: Final[str] = "bf6778ef9815b197a8d0e7a649c96dda8cb61546"
PR5033_BASE: Final[str] = "50c714baee959e0bbea8c1f79cf1ebdfdadb46d4"

RATIFICATION_BUNDLE_MANIFEST_VERIFY_RC: Final[int] = 1
RATIFICATION_BUNDLE_MANIFEST_DRIFT_NOTE: Final[str] = (
    "Historical implementation bundle MANIFEST_VERIFY_RC=1 due to REPORT.md hash drift only; "
    "not a current system fault."
)

PARITY_SURFACES_COMPLETED: Final[tuple[dict[str, Any], ...]] = (
    {
        "surface_id": "bull_bear_state_switch",
        "label": "Bull/Bear State Switch",
        "assessment_status": "CLOSED_ASSESSMENT",
        "pr_refs": "5056-5059",
        "surface_class": "closed_assessment",
    },
    {
        "surface_id": "scope_adverse_exit_reversal",
        "label": "Scope Adverse Exit / Reversal",
        "assessment_status": "CLOSED_ASSESSMENT",
        "pr_refs": "5060-5062",
        "surface_class": "closed_assessment",
    },
    {
        "surface_id": "flat_before_opposite_side",
        "label": "Flat Before Opposite Side",
        "assessment_status": "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE",
        "pr_refs": "5063",
        "surface_class": "wired_complete",
    },
    {
        "surface_id": "survival_suitability",
        "label": "Survival / Suitability",
        "assessment_status": "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE",
        "pr_refs": "5064",
        "surface_class": "wired_complete",
    },
    {
        "surface_id": "double_play_composition",
        "label": "Double Play Composition",
        "assessment_status": "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE",
        "pr_refs": "5065",
        "surface_class": "wired_complete",
    },
    {
        "surface_id": "entry_position_exit_policy",
        "label": "Entry / Position Management / Exit Policy",
        "assessment_status": "WIRED_EXISTING_BACKTEST_PARITY_CHAIN_COMPLETE",
        "pr_refs": "5066",
        "surface_class": "wired_complete",
    },
)


def market_dashboard_current_state_snapshot_v0() -> dict[str, Any]:
    """Return the canonical view-only current-state snapshot for the market dashboard."""

    risk_per_trade = 0.005
    stop_pct = 0.025
    max_position_pct = 0.25
    sizing_ceiling = max_position_pct * stop_pct

    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "snapshot_owner": SNAPSHOT_OWNER,
        "provenance": {
            "runbook_progress_owner": RUNBOOK_PROGRESS_OWNER,
            "ma_crossover_config_owner": MA_CROSSOVER_CONFIG_OWNER,
            "vol_breakout_config_owner": VOL_BREAKOUT_CONFIG_OWNER,
            "full_parity_closeout_evidence_ref": FULL_PARITY_CLOSEOUT_EVIDENCE_REF,
            "economic_gap_scan_evidence_ref": ECONOMIC_GAP_SCAN_EVIDENCE_REF,
            "notion_sync_evidence_ref": NOTION_SYNC_EVIDENCE_REF,
            "ratification_evidence_ref": RATIFICATION_EVIDENCE_REF,
            "CURRENT_STATE_SOURCE_PR": CURRENT_STATE_SOURCE_PR,
            "CURRENT_STATE_SOURCE_HEAD": CURRENT_STATE_SOURCE_HEAD,
            "CURRENT_STATE_PRIMARY_EVIDENCE_DIR": CURRENT_STATE_PRIMARY_EVIDENCE_DIR,
            "CURRENT_STATE_REPAIR_EVIDENCE_DIR": CURRENT_STATE_REPAIR_EVIDENCE_DIR,
            "CURRENT_STATE_CLOSEOUT_EVIDENCE_DIR": CURRENT_STATE_CLOSEOUT_EVIDENCE_DIR,
            "CURRENT_STATE_RESULT_JSON": CURRENT_STATE_RESULT_JSON,
            "PRIMARY_SOURCE_MANIFEST_VERIFY_RC": PRIMARY_SOURCE_MANIFEST_VERIFY_RC,
            "SOURCE_REPAIR_MANIFEST_VERIFY_RC": SOURCE_REPAIR_MANIFEST_VERIFY_RC,
            "CLOSEOUT_MANIFEST_VERIFY_RC": CLOSEOUT_MANIFEST_VERIFY_RC,
            "ECONOMIC_EVALUATION_EXECUTED": ECONOMIC_EVALUATION_EXECUTED,
            "EVIDENCE_RESULTS_REMATERIALIZED": EVIDENCE_RESULTS_REMATERIALIZED,
            "MANIFESTS_VERIFIED": True,
        },
        "current_system_state": {
            "CURRENT_ORIGIN_MAIN": CURRENT_ORIGIN_MAIN,
            "LATEST_MERGED_PR_NUMBER": LATEST_MERGED_PR_NUMBER,
            "LATEST_MERGED_PR_TITLE": LATEST_MERGED_PR_TITLE,
            "LATEST_MERGED_PR_STATE": LATEST_MERGED_PR_STATE,
            "LATEST_MERGED_PR_SQUASH_COMMIT": LATEST_MERGED_PR_SQUASH_COMMIT,
            "FULL_CANONICAL_CHAIN_WIRED": True,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": True,
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
            "RUNTIME_REWIRE_ADMISSIBLE": False,
            "NEXT_BLOCKER": NEXT_BLOCKER,
            "STEP29M_EXECUTION_COMPLETE": True,
            "ECONOMIC_VALIDITY_OBJECTIVE_ACHIEVED": False,
            "CURRENT_FLEET_ECONOMIC_VALIDITY_PASS": False,
            "WHOLE_SYSTEM_UNPROFITABLE_NOT_PROVEN": True,
            "AUTHORIZED_PENDING_EVALUATION_COUNT": 0,
            "NEXT_EVALUATION_STRATEGY_ID": "NONE",
            "NEXT_EVALUATION_CONFIG_STATUS": "NONE",
            "CURRENT_RESEARCH_STRATEGY_ID": CURRENT_RESEARCH_STRATEGY_ID,
            "CURRENT_RESEARCH_STRATEGY_VERSION": CURRENT_RESEARCH_STRATEGY_VERSION,
            "CURRENT_RESEARCH_BINDING_ID": CURRENT_RESEARCH_BINDING_ID,
            "CURRENT_RESEARCH_STATUS": CURRENT_RESEARCH_STATUS,
            "ECONOMIC_STATUS": ECONOMIC_STATUS,
            "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
            "TRADE_COUNT": TRADE_COUNT,
            "NET_RETURN": NET_RETURN,
            "UNCHANGED_RETRY_FORBIDDEN": UNCHANGED_RETRY_FORBIDDEN,
            "POLICY_RESCUE_ALLOWED": POLICY_RESCUE_ALLOWED,
            "ECONOMIC_EVALUATION_EXECUTED": ECONOMIC_EVALUATION_EXECUTED,
            "EVIDENCE_RESULTS_REMATERIALIZED": EVIDENCE_RESULTS_REMATERIALIZED,
            "STEP29N_AUTHORIZED": False,
            "STEP29R_AUTHORIZED": False,
            "PROMOTION_ALLOWED": False,
            "RUNTIME_AUTHORIZED": False,
            "LIVE_AUTHORIZED": False,
            "SCHEDULER_RUNTIME_ALLOWED": False,
            "ORDERS_ALLOWED": False,
            "AUTHORITY_EFFECT": "NONE",
            "RUNTIME_EFFECT": "NONE",
            "PROFITABILITY_CLAIM_ALLOWED": False,
            "NOTION_CURRENT": True,
            "NOTION_UPDATED": True,
            "NEXT_PARITY_SLICE": NEXT_PARITY_SLICE,
            "DOCUMENTED_ONLY_LATER_PATH": DOCUMENTED_ONLY_LATER_PATH,
        },
        "technical_completion": {
            "FULL_CANONICAL_CHAIN_WIRED": True,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": True,
            "not_economic_validity": True,
            "not_live_authorization": True,
        },
        "economic_result": {
            "ECONOMIC_STATUS": ECONOMIC_STATUS,
            "TRADE_COUNT": TRADE_COUNT,
            "NET_RETURN": NET_RETURN,
            "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
            "UNCHANGED_RETRY_FORBIDDEN": UNCHANGED_RETRY_FORBIDDEN,
            "POLICY_RESCUE_ALLOWED": POLICY_RESCUE_ALLOWED,
            "ECONOMIC_EVALUATION_EXECUTED": ECONOMIC_EVALUATION_EXECUTED,
            "EVIDENCE_RESULTS_REMATERIALIZED": EVIDENCE_RESULTS_REMATERIALIZED,
        },
        "current_research": {
            "strategy_id": CURRENT_RESEARCH_STRATEGY_ID,
            "strategy_version": CURRENT_RESEARCH_STRATEGY_VERSION,
            "binding_id": CURRENT_RESEARCH_BINDING_ID,
            "status": CURRENT_RESEARCH_STATUS,
            "AUTHORIZED_PENDING_EVALUATION_COUNT": 0,
        },
        "parity_surfaces_completed": list(PARITY_SURFACES_COMPLETED),
        "blocked_main_gates": {
            "FULL_CANONICAL_CHAIN_WIRED": True,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": True,
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
            "RUNTIME_REWIRE_ADMISSIBLE": False,
            "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": False,
        },
        "strategy_fleet": [
            {
                "strategy_id": "macd",
                "strategy_version": "v1",
                "config_version": "v3",
                "status_label": "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL",
                "evaluation_complete": True,
                "economic_validity_pass": False,
                "promotion_eligible": False,
                "runtime_authority": False,
                "fleet_role": "historical_closed",
            },
            {
                "strategy_id": "breakout_donchian",
                "strategy_version": "v1",
                "config_version": "v1",
                "status_label": "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL",
                "evaluation_complete": True,
                "economic_validity_pass": False,
                "promotion_eligible": False,
                "runtime_authority": False,
                "fleet_role": "historical_closed",
            },
            {
                "strategy_id": "ma_crossover",
                "strategy_version": "v1",
                "config_version": "v1",
                "status_label": "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL",
                "evaluation_complete": True,
                "economic_validity_pass": False,
                "promotion_eligible": False,
                "runtime_authority": False,
                "fleet_role": "historical_closed",
            },
            {
                "strategy_id": "vol_breakout",
                "strategy_version": "v1",
                "config_version": "v1",
                "status_label": "TECHNICALLY_VALID_ECONOMIC_POLICY_FAIL",
                "policy_ratified": True,
                "fixed_config_bound": True,
                "economic_evaluation_executed": True,
                "economic_validity_pass": False,
                "promotion_eligible": False,
                "runtime_authority": False,
                "fleet_role": "historical_closed",
            },
            {
                "strategy_id": "bollinger_bands",
                "strategy_version": "v2",
                "config_version": "v1",
                "binding_id": CURRENT_RESEARCH_BINDING_ID,
                "status_label": "COMPLETE_FAIL",
                "evaluation_complete": True,
                "economic_validity_pass": False,
                "promotion_eligible": False,
                "runtime_authority": False,
                "fleet_role": "current_terminal",
                "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
                "evidence_results_rematerialized": EVIDENCE_RESULTS_REMATERIALIZED,
            },
        ],
        "vol_breakout_fixed_config": {
            "strategy_id": "vol_breakout",
            "strategy_version": "v1",
            "instrument_id": "inst-eth-usdt-perp",
            "lookback_breakout": 20,
            "vol_window": 14,
            "vol_percentile": 50.0,
            "side": "both",
            "required_warmup_rows": 40,
            "risk_per_trade": risk_per_trade,
            "stop_pct": stop_pct,
            "max_position_pct": max_position_pct,
            "oversize_policy": "REJECT_OVERSIZE",
            "fixed_config": True,
            "parameter_tuning_allowed": False,
            "dataset_replacement_allowed": False,
            "threshold_tuning_allowed": False,
            "economic_evaluation_executed": True,
            "performance_claim_allowed": False,
            "atr_multiple_bound": False,
            "sizing_invariant": {
                "expression": "risk_per_trade <= max_position_pct * stop_pct",
                "lhs": risk_per_trade,
                "rhs": sizing_ceiling,
                "passes": risk_per_trade <= sizing_ceiling,
            },
        },
        "ma_crossover_fixed_config": {
            "strategy_id": "ma_crossover",
            "strategy_version": "v1",
            "instrument_id": "inst-eth-usdt-perp",
            "fast_window": 20,
            "slow_window": 50,
            "price_col": "close",
            "risk_per_trade": risk_per_trade,
            "stop_pct": stop_pct,
            "max_position_pct": max_position_pct,
            "oversize_policy": "REJECT_OVERSIZE",
            "fixed_config": True,
            "parameter_tuning_allowed": False,
            "dataset_replacement_allowed": False,
            "threshold_tuning_allowed": False,
            "economic_evaluation_executed": True,
            "performance_claim_allowed": False,
            "sizing_invariant": {
                "expression": "risk_per_trade <= max_position_pct * stop_pct",
                "lhs": risk_per_trade,
                "rhs": sizing_ceiling,
                "passes": risk_per_trade <= sizing_ceiling,
            },
        },
        "next_parity_slice": {
            "slice_id": NEXT_PARITY_SLICE,
            "execution_class": "NEXT_EXECUTABLE_PARITY_SLICE",
            "PREFLIGHT_ONLY": True,
            "RUNTIME_AUTHORIZED": False,
            "RUNTIME_REWIRE_ADMISSIBLE": False,
            "ORDERS_ALLOWED": False,
            "LIVE_AUTHORIZED": False,
        },
        "documented_only_later_path": {
            "path_id": DOCUMENTED_ONLY_LATER_PATH,
            "execution_class": "DOCUMENTED_ONLY_NOT_EXECUTABLE",
            "operator_ratification_required": True,
            "RUNTIME_AUTHORIZED": False,
            "PROMOTION_ALLOWED": False,
        },
        "governance_and_safety": {
            "FUTURES_ONLY": True,
            "BITCOIN_DIRECTION_ALLOWED": False,
            "SPOT_ALLOWED": False,
            "SYNTHETIC_SPOT_ALLOWED": False,
            "MAX_POSITIONS": 1,
            "MAX_ACTIVE_DIRECTIONAL_SIDE": 1,
            "PROMOTION_ALLOWED": False,
            "RUNTIME_AUTHORIZED": False,
            "ORDERS_ALLOWED": False,
            "LIVE_AUTHORIZED": False,
            "SCHEDULER_RUNTIME_ALLOWED": False,
            "RUNTIME_REWIRE_ADMISSIBLE": False,
            "AUTHORITY_EFFECT": "NONE",
            "RUNTIME_EFFECT": "NONE",
        },
        "pr_and_evidence_status": {
            "latest_merged_pr": {
                "pr_number": LATEST_MERGED_PR_NUMBER,
                "title": LATEST_MERGED_PR_TITLE,
                "state": LATEST_MERGED_PR_STATE,
                "merge_commit": LATEST_MERGED_PR_SQUASH_COMMIT,
            },
            "PR5033": {
                "pr_number": 5033,
                "state": "MERGED",
                "merge_commit": PR5033_MERGE_COMMIT,
                "head": PR5033_HEAD,
                "base": PR5033_BASE,
            },
            "full_parity_proof": {
                "FULL_CANONICAL_CHAIN_WIRED": True,
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS": True,
                "MANIFEST_VERIFY_RC": 0,
                "evidence_ref": FULL_PARITY_CLOSEOUT_EVIDENCE_REF,
                "historical_note": (
                    "Technical completion remains distinct from economic validity; "
                    "PR #5242 bound Full-Canonical economic FAIL closeout without authority."
                ),
            },
            "economic_evidence_gap": {
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
                "ECONOMIC_STATUS": ECONOMIC_STATUS,
                "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": False,
                "NEXT_BLOCKER": NEXT_BLOCKER,
                "MANIFEST_VERIFY_RC": PRIMARY_SOURCE_MANIFEST_VERIFY_RC,
                "evidence_ref": CURRENT_STATE_PRIMARY_EVIDENCE_DIR,
            },
            "notion_current_state_sync": {
                "NOTION_CURRENT": True,
                "NOTION_UPDATED": True,
                "stale_reason": None,
                "last_verified_evidence_ref": NOTION_SYNC_EVIDENCE_REF,
                "MANIFEST_VERIFY_RC": 0,
            },
            "ratification_evidence": {
                "pr_merge_verified": True,
                "evidence_ref": RATIFICATION_EVIDENCE_REF,
                "MANIFEST_VERIFY_RC": RATIFICATION_BUNDLE_MANIFEST_VERIFY_RC,
                "integrity_note": RATIFICATION_BUNDLE_MANIFEST_DRIFT_NOTE,
                "misrepresentation_forbidden": True,
            },
        },
        "historical_semantics_suppressed": [
            "fleet_fully_exhausted_without_pending_candidate",
            "operator_decision_still_open",
            "ma_crossover_not_ratified",
            "next_step_is_policy_selection",
            "economic_validity_pass_achieved",
            "step29n_or_runtime_authorized",
            "runtime_rewire_admissible",
            "system_economic_evidence_admissible",
            "vol_breakout_authorized_pending_evaluation",
            "authorized_pending_evaluation_count_nonzero",
            "economic_evaluation_executed_by_pr5242",
            "evidence_results_rematerialized_by_pr5242",
            "notion_stale_after_pr5033",
        ],
        "view_only": True,
        "controls_allowed": False,
        "runtime_effect": False,
        "order_effect": False,
    }
