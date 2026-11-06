"""Closed-program SSOT validator for CS open-gap pressure fade program v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1=true"
PROGRAM_REL_PATH = "config/research/cross_sectional_open_gap_pressure_fade_research_program_v1.json"
GOVERNANCE_REL_PATH = (
    "docs/governance/CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1.md"
)
REQUIRED_PROGRAM_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1"
REQUIRED_WORKSTREAM_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_WORKSTREAM_V1"
REQUIRED_STATUS = "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_SIGNAL_FAMILY = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE"
REQUIRED_TARGET = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE"
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1"
REQUIRED_TREATMENT = "OWN_INSTRUMENT_CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_ADMISSION"
REQUIRED_NEXT_STEP = (
    "NEW_DISTINCT_RESEARCH_PROGRAM_OR_FULL_CANONICAL_SYSTEM_BINDING_OR_OTHER_EVIDENCE_CLASS"
    "_REQUIRES_OPERATOR_RATIFICATION"
)
CLOSED_VOL = "config/research/volatility_regime_research_program_v1.json"
CLOSED_CS_MOM = "config/research/material_different_cross_sectional_momentum_program_v1.json"
CLOSED_CSRHR = (
    "config/research/cross_sectional_short_horizon_return_reversal_research_program_v1.json"
)
CLOSED_CSRHR_BACKLOG = (
    "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)
REQUIRED_CLOSED_PROGRAM = "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_CSRHR_STATUS = "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_CSRHR_BACKLOG_STATUS = "LANE_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_EVIDENCE = "docs/evidence/evaluate_cross_sectional_open_gap_pressure_fade_development_v1/"


class ProgramValidationError(ValueError):
    """Fail-closed program SSOT validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise ProgramValidationError(code)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_program_contract(
    payload: Mapping[str, Any], *, repo_root: Path | None = None
) -> dict[str, Any]:
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID_MISMATCH")
    _require(payload.get("workstream_id") == REQUIRED_WORKSTREAM_ID, "WORKSTREAM_ID_MISMATCH")
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_PROGRAM_CLOSED")
    _require(payload.get("program_family") == REQUIRED_SIGNAL_FAMILY, "FAMILY")
    _require(
        payload.get("slice_class") == "DOCUMENTARY_AND_REGISTRY_TRUTH_RECONCILIATION",
        "SLICE_NOT_TRUTH_RECONCILIATION",
    )
    _require(payload.get("authority_effect") == "NONE", "AUTHORITY_EFFECT_NOT_NONE")
    _require(payload.get("runtime_effect") == "NONE", "RUNTIME_EFFECT_NOT_NONE")
    _require(payload.get("signal_family") == REQUIRED_SIGNAL_FAMILY, "SIGNAL_FAMILY")
    _require(payload.get("target_phenomenon") == REQUIRED_TARGET, "TARGET_PHENOMENON")
    _require(payload.get("treatment_type") == REQUIRED_TREATMENT, "TREATMENT_TYPE")
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED_TRUE",
    )
    _require(
        payload.get("development_evaluation_executed") is True,
        "DEVELOPMENT_EVALUATION_EXECUTED_FALSE",
    )
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT_NOT_ONE")
    _require(payload.get("development_run_limit") == 1, "DEVELOPMENT_RUN_LIMIT_NOT_1")
    _require(payload.get("development_result") == "DEVELOPMENT_FAIL", "DEVELOPMENT_RESULT")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT_NOT_ONE")
    _require(payload.get("run_slot_consumed") is True, "RUN_SLOT_CONSUMED")
    _require(payload.get("run_budget_consumed") is True, "RUN_BUDGET_CONSUMED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(payload.get("implementation_authorized") is False, "IMPLEMENTATION_AUTHORIZED")
    _require(
        payload.get("strategy_implementation_present") is True,
        "STRATEGY_IMPLEMENTATION_ABSENT",
    )
    _require(payload.get("implementation_pr") == 5495, "IMPLEMENTATION_PR")
    _require(payload.get("development_pr") == 5496, "DEVELOPMENT_PR")
    _require(payload.get("runtime_authorized") is False, "RUNTIME_AUTHORIZED")
    _require(payload.get("explicit_closeout_decision") is True, "CLOSEOUT_DECISION_REQUIRED")
    _require(payload.get("next_canonical_step") == REQUIRED_NEXT_STEP, "NEXT_STEP_STALE")
    _require(payload.get("next_eligible") == "NONE", "NEXT_ELIGIBLE_NOT_NONE")
    _require(
        payload.get("lane_backlog_status") == "LANE_CLOSED_NO_FURTHER_RESEARCH",
        "LANE_BACKLOG_NOT_CLOSED",
    )
    independence = payload.get("causal_independence") or {}
    _require(
        independence.get("independent_from_closed_volatility_regime_program") is True,
        "NOT_INDEPENDENT_OF_VOL_REGIME",
    )
    _require(
        independence.get("independent_from_closed_cross_sectional_momentum_lane") is True,
        "NOT_INDEPENDENT_OF_CS_MOMENTUM",
    )
    _require(
        independence.get("independent_from_closed_csrhr_program") is True,
        "NOT_INDEPENDENT_OF_CLOSED_CSRHR",
    )
    _require(
        independence.get("independent_from_terminal_path_efficiency_continuation") is True,
        "NOT_INDEPENDENT_OF_PATH_EFFICIENCY",
    )
    _require(
        independence.get("independent_from_terminal_clv_pressure_continuation") is True,
        "NOT_INDEPENDENT_OF_CLV_PRESSURE",
    )
    _require(
        independence.get("not_a_csrhr_continuation_or_semantic_reuse") is True,
        "CSRHR_REUSE_NOT_FORBIDDEN",
    )
    _require(
        independence.get("not_a_path_efficiency_retry_or_rename") is True,
        "PATH_EFFICIENCY_RETRY_NOT_FORBIDDEN",
    )
    _require(
        independence.get("not_a_clv_pressure_retry_or_rename") is True,
        "CLV_PRESSURE_RETRY_NOT_FORBIDDEN",
    )
    _require(
        independence.get("not_a_retry_of_terminal_cross_sectional_relative_strength_momentum_v1")
        is True,
        "CS_MOMENTUM_RETRY_NOT_FORBIDDEN",
    )
    _require(
        independence.get("not_a_volatility_regime_reopen") is True,
        "VOL_REGIME_REOPEN_NOT_FORBIDDEN",
    )
    _require(independence.get("volume_dependency") is False, "VOLUME_DEPENDENCY")
    retry = payload.get("retry_policy") or {}
    _require(retry.get("after_development_fail") == "FAIL_CLOSED_NO_RETRY", "RETRY_POLICY")
    _require(payload.get("retry_allowed") is False, "RETRY_ALLOWED")
    rt = payload.get("runtime_policy") or {}
    for key in (
        "live_authorized",
        "orders_allowed",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "scheduler_authorized",
        "runtime_activated",
    ):
        _require(rt.get(key) is False, f"RUNTIME_POLICY_{key.upper()}")
    econ = payload.get("promotion_and_economic_gate_policy") or {}
    _require(econ.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
    _require(econ.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(econ.get("economic_validity_offline_gate_pass") is False, "ECONOMIC_VALIDITY_PASS")
    universe = payload.get("universe_scope") or {}
    _require(universe.get("bitcoin_excluded") is True, "BTC_NOT_EXCLUDED")
    _require(universe.get("spot_excluded") is True, "SPOT_NOT_EXCLUDED")
    _require(universe.get("venue") == "OKX", "VENUE_NOT_OKX")
    _require(universe.get("frequency") == "PT1H", "TIMEFRAME_NOT_PT1H")
    _require(
        payload.get("sealed_holdout_binding_status") == "UNBOUND_UNTOUCHED_ACCESS_FORBIDDEN",
        "HOLDOUT_STATUS",
    )

    if repo_root is not None:
        vol = load_json(repo_root / CLOSED_VOL)
        mom = load_json(repo_root / CLOSED_CS_MOM)
        csrhr = load_json(repo_root / CLOSED_CSRHR)
        csrhr_bl = load_json(repo_root / CLOSED_CSRHR_BACKLOG)
        _require(vol.get("status") == REQUIRED_CLOSED_PROGRAM, "VOL_REGIME_NOT_CLOSED")
        _require(mom.get("status") == REQUIRED_CLOSED_PROGRAM, "CS_MOMENTUM_NOT_CLOSED")
        _require(csrhr.get("status") == REQUIRED_CSRHR_STATUS, "CSRHR_NOT_CLOSED")
        _require(
            csrhr_bl.get("status") == REQUIRED_CSRHR_BACKLOG_STATUS,
            "CSRHR_BACKLOG_NOT_CLOSED",
        )
        gov = repo_root / GOVERNANCE_REL_PATH
        _require(gov.is_file(), "GOVERNANCE_DOC_MISSING")
        evidence = repo_root / REQUIRED_EVIDENCE
        _require(evidence.is_dir(), "EVALUATION_EVIDENCE_MISSING")
        summary = load_json(evidence / "summary.json")
        _require(summary.get("development_result") == "DEVELOPMENT_FAIL", "SUMMARY_NOT_FAIL")
        _require(summary.get("holdout_accessed") is False, "HOLDOUT_ACCESSED")
        _require(summary.get("promotion_eligible") is False, "SUMMARY_PROMOTION")

    return {
        "valid": True,
        "definition_only": False,
        "program_closed": True,
        "program_id": REQUIRED_PROGRAM_ID,
        "workstream_id": REQUIRED_WORKSTREAM_ID,
        "status": REQUIRED_STATUS,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "evaluation_authorized": False,
        "development_run_count": 1,
        "development_result": "DEVELOPMENT_FAIL",
        "strategy_implementation_present": True,
        "holdout_forbidden": True,
        "next_canonical_step": REQUIRED_NEXT_STEP,
    }


def load_and_validate_repo_program(repo_root: Path) -> dict[str, Any]:
    payload = load_json(repo_root / PROGRAM_REL_PATH)
    return validate_program_contract(payload, repo_root=repo_root)
