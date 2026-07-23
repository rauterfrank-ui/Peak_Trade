"""Definition-only contract tests for CSHRVF v1 hypothesis preregistration."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_high_realized_volatility_fade_v1_hypothesis_preregistration_v1 import (
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
    / "scripts/research/run_evaluate_cross_sectional_high_realized_volatility_fade_development_v1.py"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only_preregistered() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["status"] == "DEFINITION_ONLY_PREREGISTERED"
    assert report["hypothesis_id"] == (
        "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_NON_BITCOIN_PERPETUALS_V1"
    )
    assert report["strategy_identity"] == ("CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1")
    assert report["development_run_count"] == 1
    assert report["run_slot_consumed"] is True
    assert report["strategy_implementation_present"] is False
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["materially_distinct_from_vtdc"] is True
    assert len(report["contract_digest"]) == 64


def test_material_difference_vs_vtdc_and_lane_inventory() -> None:
    contract = _load(CONTRACT_PATH)
    md = contract["material_difference_vs_volatility_term_structure_depressed_continuation_v1"]
    assert md["vtdc_retry_forbidden"] is True
    assert md["not_a_parameter_change_of_vtdc_v1"] is True
    assert md["not_a_repair_or_retry_of_vtdc_v1"] is True
    assert "admission_polarity" in md["differences"]
    assert "estimator_axis" in md["differences"]
    admission = contract["admission_mechanism"]
    assert admission["cross_sectional_vol_rank_state"]["low_rank_entry_forbidden_in_v1"] is True
    assert (
        admission["cross_sectional_high_vol_fade_entry"]["direction_rule"]
        == "opposite_to_signed_return_over_short_horizon_window"
    )
    assert (
        admission["cross_sectional_high_vol_fade_entry"][
            "vtdc_depressed_continuation_entry_forbidden"
        ]
        is True
    )
    rationale = contract["successor_selection_rationale"]
    assert "FURTHER_TERM_STRUCTURE_VARIANT" in rationale["alternatives_rejected"]
    assert "CLOSE_LANE_NO_FURTHER_RESEARCH" in rationale["alternatives_rejected"]
    backlog = _load(BACKLOG_PATH)
    assert backlog["preregistered_hypotheses"][0]["strategy_identity"] == (
        "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1"
    )
    terminals = {t["strategy_identity"] for t in backlog["terminal_hypotheses"]}
    assert "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1" in terminals
    assert "VOLATILITY_TERM_STRUCTURE_REVERSION_V1" in terminals
    program = _load(PROGRAM_PATH)
    assert program["strategy_identity"] == ("CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1")
    assert (
        "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1"
        in program["causal_independence"]["forbidden_lineage_refs"]
    )


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["admission_mechanism"]["cross_sectional_high_vol_fade_entry"][
        "entry_only_after_cross_sectional_high_rv_rank_state"
    ] = False
    with pytest.raises(PreregistrationValidationError, match="FADE_ORDER"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["admission_mechanism"]["cross_sectional_high_vol_fade_entry"]["direction_rule"] = (
        "with_signed_return_over_short_horizon_window"
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
        "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
        in json.dumps(_load(OWNER_MAP))
    )


def test_placeholder_cli_fail_closed() -> None:
    import subprocess

    proc = subprocess.run(
        ["python3", str(CLI), "--mode", "evaluate"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "FAIL_CLOSED"
    assert payload["evaluation_executed"] is False
    assert payload["holdout_accessed"] is False
