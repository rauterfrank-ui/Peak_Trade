"""Versioned current-state snapshot for GET /market (display-only SSOT).

Provenance:
- docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md
- research/merge_closeout_pr5033_surface_p_semantic_parity_status_binding_fix_v0_20260709T135256Z
- research/system_economic_evidence_admissibility_gap_scan_after_full_parity_v0_20260709T141726Z

No trading authority. No runtime effect. Single dashboard owner — no parallel SSOT.
"""

from __future__ import annotations

from typing import Any, Final

SNAPSHOT_VERSION: Final[str] = "market_dashboard_current_state_snapshot_v0"
SNAPSHOT_OWNER: Final[str] = "src/webui/market_dashboard_current_state_snapshot_v0.py"
RUNBOOK_PROGRESS_OWNER: Final[str] = "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
MA_CROSSOVER_CONFIG_OWNER: Final[str] = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_ma_crossover_v1_economic_evaluation_v1.json"
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
    "implementation/bounded_step29m_ma_crossover_fixed_config_policy_ratification_v0_20260702T001219Z"
)

NEXT_CANONICAL_STEP: Final[str] = (
    "OFFLINE_ONLY_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_AND_REUSE_FIRST_BINDING"
)
NEXT_BLOCKER: Final[str] = "SYSTEM_ECONOMIC_EVIDENCE_NOT_PROVEN"

CURRENT_ORIGIN_MAIN: Final[str] = "720b59bed1c012e873c8e1207b057ebd5fa8f21a"

PR5033_MERGE_COMMIT: Final[str] = CURRENT_ORIGIN_MAIN
PR5033_HEAD: Final[str] = "bf6778ef9815b197a8d0e7a649c96dda8cb61546"
PR5033_BASE: Final[str] = "50c714baee959e0bbea8c1f79cf1ebdfdadb46d4"

RATIFICATION_BUNDLE_MANIFEST_VERIFY_RC: Final[int] = 1
RATIFICATION_BUNDLE_MANIFEST_DRIFT_NOTE: Final[str] = (
    "Historical implementation bundle MANIFEST_VERIFY_RC=1 due to REPORT.md hash drift only; "
    "not a current system fault."
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
            "full_parity_closeout_evidence_ref": FULL_PARITY_CLOSEOUT_EVIDENCE_REF,
            "economic_gap_scan_evidence_ref": ECONOMIC_GAP_SCAN_EVIDENCE_REF,
            "notion_sync_evidence_ref": NOTION_SYNC_EVIDENCE_REF,
            "ratification_evidence_ref": RATIFICATION_EVIDENCE_REF,
        },
        "current_system_state": {
            "CURRENT_ORIGIN_MAIN": CURRENT_ORIGIN_MAIN,
            "FULL_CANONICAL_CHAIN_WIRED": True,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": True,
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
            "RUNTIME_REWIRE_ADMISSIBLE": False,
            "NEXT_BLOCKER": NEXT_BLOCKER,
            "STEP29M_EXECUTION_COMPLETE": True,
            "ECONOMIC_VALIDITY_OBJECTIVE_ACHIEVED": False,
            "CURRENT_FLEET_ECONOMIC_VALIDITY_PASS": False,
            "WHOLE_SYSTEM_UNPROFITABLE_NOT_PROVEN": True,
            "AUTHORIZED_PENDING_EVALUATION_COUNT": 1,
            "NEXT_EVALUATION_STRATEGY_ID": "ma_crossover",
            "NEXT_EVALUATION_CONFIG_STATUS": "AUTHORIZED_PENDING_EVALUATION",
            "STEP29N_AUTHORIZED": False,
            "STEP29R_AUTHORIZED": False,
            "PROMOTION_ALLOWED": False,
            "RUNTIME_AUTHORIZED": False,
            "LIVE_AUTHORIZED": False,
            "PROFITABILITY_CLAIM_ALLOWED": False,
            "NEXT_CANONICAL_STEP": NEXT_CANONICAL_STEP,
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
            },
            {
                "strategy_id": "ma_crossover",
                "strategy_version": "v1",
                "config_version": "v1",
                "status_label": "AUTHORIZED_PENDING_EVALUATION",
                "policy_ratified": True,
                "fixed_config_bound": True,
                "economic_evaluation_executed": False,
                "economic_validity_pass": False,
                "promotion_eligible": False,
                "runtime_authority": False,
            },
        ],
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
            "economic_evaluation_executed": False,
            "performance_claim_allowed": False,
            "sizing_invariant": {
                "expression": "risk_per_trade <= max_position_pct * stop_pct",
                "lhs": risk_per_trade,
                "rhs": sizing_ceiling,
                "passes": risk_per_trade <= sizing_ceiling,
            },
        },
        "next_canonical_step": {
            "step_id": NEXT_CANONICAL_STEP,
            "PREFLIGHT_ONLY": True,
            "ECONOMIC_EVALUATION_AUTHORIZED": False,
            "PRODUCTIVE_RUNNER_INVOCATIONS_ALLOWED": 0,
            "BACKTEST_ALLOWED": False,
            "PERFORMANCE_COMPUTATION_ALLOWED": False,
            "STEP29N_AUTHORIZED": False,
            "STEP29R_AUTHORIZED": False,
            "RUNTIME_AUTHORIZED": False,
            "RUNTIME_REWIRE_ADMISSIBLE": False,
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
            "RUNTIME_REWIRE_ADMISSIBLE": False,
        },
        "pr_and_evidence_status": {
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
            },
            "economic_evidence_gap": {
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
                "NEXT_BLOCKER": NEXT_BLOCKER,
                "MANIFEST_VERIFY_RC": 0,
                "evidence_ref": ECONOMIC_GAP_SCAN_EVIDENCE_REF,
            },
            "notion_current_state_sync": {
                "NOTION_CURRENT": False,
                "stale_reason": "Last verified Notion mirror is STEP29M/PR4740 (20260702); post-PR5033 full-parity mirror pending operator write GO.",
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
            "notion_current_after_pr5033",
        ],
        "view_only": True,
        "controls_allowed": False,
        "runtime_effect": False,
        "order_effect": False,
    }
