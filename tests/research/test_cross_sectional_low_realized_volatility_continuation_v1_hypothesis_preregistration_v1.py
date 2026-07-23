"""Definition-only contract tests for CSLRVC v1 hypothesis preregistration."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_low_realized_volatility_continuation_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    PreregistrationValidationError,
    compute_contract_digest,
    load_and_validate_repo_contract,
    validate_measurement_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
GOVERNANCE = REPO / GOVERNANCE_REL_PATH
EVIDENCE = REPO / EVIDENCE_REL_PATH
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
BACKLOG_PATH = REPO / "config/research/volatility_regime_hypothesis_backlog_v1.json"
PROGRAM_PATH = REPO / "config/research/volatility_regime_research_program_v1.json"
CLI = (
    REPO
    / "scripts/research/run_evaluate_cross_sectional_low_realized_volatility_continuation_development_v1.py"
)
ENTRY_POINT_BINDING_PATH = (
    REPO
    / "config/research/cross_sectional_low_realized_volatility_continuation_v1_development_evaluation_entry_point_binding_v1.json"
)
CSHRVF_ENTRY_POINT_BINDING_PATH = (
    REPO
    / "config/research/cross_sectional_high_realized_volatility_fade_v1_development_evaluation_entry_point_binding_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only_preregistered() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["status"] == "DEFINITION_ONLY_PREREGISTERED"
    assert (
        report["hypothesis_id"]
        == "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
    )
    assert report["strategy_identity"] == "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1"
    assert report["development_run_count"] == 1
    assert report["run_slot_consumed"] is True
    assert report["strategy_implementation_present"] is False
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["materially_distinct_from_cshrvf"] is True
    assert len(report["contract_digest"]) == 64


def test_material_difference_vs_cshrvf_and_lane_inventory() -> None:
    contract = _load(CONTRACT_PATH)
    md = contract["material_difference_vs_cross_sectional_high_realized_volatility_fade_v1"]
    assert md["cshrvf_retry_forbidden"] is True
    assert md["not_a_parameter_change_of_cshrvf_v1"] is True
    admission = contract["admission_mechanism"]
    assert admission["cross_sectional_vol_rank_state"]["high_rank_entry_forbidden_in_v1"] is True
    assert (
        admission["cross_sectional_low_vol_continuation_entry"]["direction_rule"]
        == "with_signed_return_over_short_horizon_window"
    )
    backlog = _load(BACKLOG_PATH)
    assert (
        backlog["preregistered_hypotheses"][0]["strategy_identity"]
        == "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1"
    )
    terminals = {t["strategy_identity"] for t in backlog["terminal_hypotheses"]}
    assert "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1" in terminals
    program = _load(PROGRAM_PATH)
    assert program["strategy_identity"] == "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1"
    assert (
        "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1"
        in program["causal_independence"]["forbidden_lineage_refs"]
    )


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["admission_mechanism"]["cross_sectional_low_vol_continuation_entry"][
        "entry_only_after_cross_sectional_low_rv_rank_state"
    ] = False
    with pytest.raises(PreregistrationValidationError, match="ENTRY_ORDER"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["admission_mechanism"]["cross_sectional_low_vol_continuation_entry"]["direction_rule"] = (
        "opposite_to_signed_return_over_short_horizon_window"
    )
    with pytest.raises(PreregistrationValidationError, match="DIRECTION_RULE"):
        validate_measurement_contract(bad2)
    bad3 = copy.deepcopy(contract)
    bad3["contract_digest"] = "0" * 64
    with pytest.raises(PreregistrationValidationError, match="CONTRACT_DIGEST_MISMATCH"):
        validate_measurement_contract(bad3)


def test_digest_stable_and_artifacts_present() -> None:
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]
    assert GOVERNANCE.is_file()
    assert EVIDENCE.is_dir()
    assert CLI.is_file()
    assert (
        "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
        in json.dumps(_load(OWNER_MAP))
    )


def test_unauthorized_cli_evaluate_fail_closed() -> None:
    import subprocess

    proc = subprocess.run(
        ["python3", str(CLI), "--mode", "evaluate"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": "src:."},
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "FAIL_CLOSED"
    assert payload.get("evaluation_executed") is False
    assert payload.get("holdout_accessed") is False


def test_successor_entry_point_binding_slot_consumed_development_fail() -> None:
    binding = _load(ENTRY_POINT_BINDING_PATH)
    assert binding["hypothesis_id"] == (
        "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
    )
    assert binding["status"] == "RUN_SLOT_CONSUMED_DEVELOPMENT_FAIL"
    assert binding["entry_point_status"] == "RUN_SLOT_CONSUMED_DEVELOPMENT_FAIL"
    assert binding["slice_class"] == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL_FAIL"
    assert binding["verdict"] == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL"
    assert binding["development_run_count"] == 1
    assert binding["runner_start_count"] == 1
    assert binding["runner_present"] is True
    assert binding["development_evaluation_executed"] is True
    assert binding["development_evaluation_authorized"] is True
    assert binding["evaluation_authorized"] is False
    assert binding["holdout_authorized"] is False
    assert binding["holdout_forbidden"] is True
    assert "strategy_params_digest" in binding
    owners = binding["reused_canonical_owners"]
    assert "strategy" in owners
    assert "vol_state" in owners


def test_predecessor_cshrvf_terminal_fail_not_projected_onto_successor() -> None:
    backlog = _load(BACKLOG_PATH)
    terminals = {t["strategy_identity"]: t for t in backlog["terminal_hypotheses"]}
    cshrvf = terminals["CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1"]
    assert cshrvf["status"] == "TERMINAL_FAIL"
    assert cshrvf["terminal_result"] == "FAIL_CLOSED_NO_RETRY"
    assert cshrvf["run_slot_consumed"] is True
    assert cshrvf["development_run_count"] == 1
    assert cshrvf["runner_start_count"] == 1
    assert cshrvf["retry_allowed"] is False
    assert cshrvf["rerun_allowed"] is False
    assert cshrvf["reopen_allowed"] is False

    successor = backlog["preregistered_hypotheses"][0]
    assert successor["strategy_identity"] == (
        "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1"
    )
    assert successor["status"] == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL_FAIL"
    assert successor["development_run_count"] == 1
    assert successor["run_slot_consumed"] is True
    assert successor["implementation_present"] is True
    assert successor["runner_start_count"] == 1

    cshrvf_binding = _load(CSHRVF_ENTRY_POINT_BINDING_PATH)
    assert cshrvf_binding["status"] == "RUN_SLOT_CONSUMED_DEVELOPMENT_FAIL"
    assert cshrvf_binding["development_run_count"] == 1
    assert cshrvf_binding["runner_start_count"] == 1
    assert cshrvf_binding["development_evaluation_executed"] is True

    successor_binding = _load(ENTRY_POINT_BINDING_PATH)
    assert successor_binding["runner_start_count"] == 1
    assert successor_binding["development_run_count"] == 1
    assert successor_binding["development_evaluation_executed"] is True
    assert successor_binding["status"] == "RUN_SLOT_CONSUMED_DEVELOPMENT_FAIL"
    assert successor_binding["hypothesis_id"] != cshrvf_binding["hypothesis_id"]
    assert successor_binding["strategy_identity"] != cshrvf_binding["strategy_identity"]
