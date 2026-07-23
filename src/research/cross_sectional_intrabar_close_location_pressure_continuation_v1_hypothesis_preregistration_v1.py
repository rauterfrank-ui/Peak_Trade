"""Definition-only preregistration validator for CS intrabar close-location pressure continuation v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_HYPOTHESIS_PREREGISTRATION=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "cross_sectional_intrabar_close_location_pressure_continuation_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = "docs/evidence/preregister_cross_sectional_intrabar_close_location_pressure_continuation_hypothesis_v1/"
REQUIRED_HYPOTHESIS_ID = (
    "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_PROGRAM_ID = (
    "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_RESEARCH_PROGRAM_V1"
)
REQUIRED_WORKSTREAM_ID = (
    "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_WORKSTREAM_V1"
)
REQUIRED_STATUS = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_DIRECTIONAL_FORM = "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION"
REQUIRED_TIME_SEGMENT_DEFINITION_ID = "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"


class PreregistrationValidationError(ValueError):
    """Fail-closed measurement-contract validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise PreregistrationValidationError(code)


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def compute_contract_digest(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k not in ("contract_digest", "provenance")}
    return hashlib.sha256(_canonical_dumps(body).encode("utf-8")).hexdigest()


def validate_measurement_contract(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_DEFINITION_ONLY")
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID")
    _require(payload.get("workstream_id") == REQUIRED_WORKSTREAM_ID, "WORKSTREAM_ID")
    _require(
        payload.get("strategy_identity")
        == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1",
        "STRATEGY_IDENTITY",
    )
    _require(
        payload.get("signal_family") == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE",
        "SIGNAL_FAMILY",
    )
    _require(
        payload.get("target_phenomenon")
        == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION",
        "TARGET_PHENOMENON",
    )
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(
        payload.get("strategy_implementation_present") is False,
        "STRATEGY_IMPLEMENTATION_PRESENT",
    )
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")
    directional = payload.get("directional_form") or {}
    _require(directional.get("selected") == REQUIRED_DIRECTIONAL_FORM, "DIRECTIONAL_FORM")
    _require(
        directional.get("double_play_remains_sole_authority") is True,
        "DOUBLE_PLAY_NOT_SOLE",
    )
    score = payload.get("score_and_selection") or {}
    _require(
        score.get("score_family_policy") == "mean_intrabar_close_location_value_fixed_lookback_v1",
        "SCORE_FAMILY",
    )
    _require(score.get("not_a_cs_momentum_parameter_retune") is True, "CS_MOMENTUM_RETUNE")
    _require(score.get("not_a_csrhr_continuation_or_semantic_reuse") is True, "CSRHR_REUSE")
    _require(score.get("not_a_path_efficiency_retry_or_rename") is True, "PATH_EFFICIENCY_RETRY")
    _require(
        score.get("polarity") == "INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION",
        "POLARITY",
    )
    frozen = (payload.get("parameter_governance") or {}).get("frozen_non_grid_parameters") or {}
    _require(frozen.get("lookback_N") == 36, "LOOKBACK_N")
    _require(frozen.get("rebalance_interval_bars") == 6, "REBALANCE_INTERVAL")
    grid = (payload.get("parameter_governance") or {}).get("development_only_bounded_grid") or {}
    _require(grid.get("authorized") is False, "GRID_AUTHORIZED")
    _require(
        payload.get("time_segment_definition_id") == REQUIRED_TIME_SEGMENT_DEFINITION_ID,
        "TIME_SEGMENT_DEFINITION",
    )
    econ = payload.get("promotion_and_economic_gate_policy") or {}
    _require(econ.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
    shared = payload.get("shared_authority_constraints") or {}
    _require(shared.get("master_v2_mutation_forbidden") is True, "MASTER_V2_MUTATION")
    _require(
        shared.get("double_play_sole_directional_transition_authority") is True,
        "DOUBLE_PLAY_AUTHORITY",
    )
    _require(shared.get("execution_kernel_mutation_forbidden") is True, "EXECUTION_MUTATION")
    _require(shared.get("risk_authority_mutation_forbidden") is True, "RISK_MUTATION")
    rt = payload.get("runtime_policy") or {}
    for key in (
        "live_authorized",
        "orders_allowed",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "scheduler_authorized",
    ):
        _require(rt.get(key) is False, f"RUNTIME_POLICY_{key.upper()}")

    digest = compute_contract_digest(payload)
    _require(payload.get("contract_digest") == digest, "CONTRACT_DIGEST_MISMATCH")
    return {
        "valid": True,
        "definition_only": True,
        "contract_digest": digest,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "evaluation_authorized": False,
        "development_run_count": 0,
    }


def load_and_validate_repo_contract(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONTRACT_REL_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = validate_measurement_contract(payload)
    evidence = repo_root / EVIDENCE_REL_PATH
    _require((evidence / "summary.json").is_file(), "EVIDENCE_SUMMARY_MISSING")
    _require((evidence / "safety_attestation.md").is_file(), "SAFETY_ATTESTATION_MISSING")
    gov = repo_root / GOVERNANCE_REL_PATH
    _require(gov.is_file(), "GOVERNANCE_DOC_MISSING")
    return report
