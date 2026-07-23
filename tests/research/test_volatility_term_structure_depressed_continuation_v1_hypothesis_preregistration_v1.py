"""Definition-only contract tests for VTDC v1 hypothesis preregistration."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.volatility_term_structure_depressed_continuation_v1_hypothesis_preregistration_v1 import (
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
    / "scripts/research/run_evaluate_volatility_term_structure_depressed_continuation_development_v1.py"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only_preregistered() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["status"] == "DEFINITION_ONLY_PREREGISTERED"
    assert report["hypothesis_id"] == (
        "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
    )
    assert report["strategy_identity"] == ("VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1")
    assert report["development_run_count"] == 0
    assert report["run_slot_consumed"] is False
    assert report["strategy_implementation_present"] is False
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["materially_distinct_from_vtsr"] is True
    assert len(report["contract_digest"]) == 64


def test_material_difference_vs_vtsr_and_lane_inventory() -> None:
    contract = _load(CONTRACT_PATH)
    md = contract["material_difference_vs_volatility_term_structure_reversion_v1"]
    assert md["vtsr_retry_forbidden"] is True
    assert md["not_a_parameter_change_of_vtsr_v1"] is True
    assert md["not_a_repair_or_retry_of_vtsr_v1"] is True
    assert "admission_polarity" in md["differences"]
    assert "direction_rule" in md["differences"]
    admission = contract["admission_mechanism"]
    assert admission["term_structure_state"]["elevated_entry_forbidden_in_v1"] is True
    assert (
        admission["depressed_continuation_entry"]["direction_rule"]
        == "with_signed_return_over_short_horizon_window"
    )
    assert (
        admission["depressed_continuation_entry"]["vtsr_elevated_reversion_fade_entry_forbidden"]
        is True
    )
    backlog = _load(BACKLOG_PATH)
    assert backlog["preregistered_hypotheses"][0]["strategy_identity"] == (
        "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1"
    )
    terminals = {t["strategy_identity"] for t in backlog["terminal_hypotheses"]}
    assert "VOLATILITY_TERM_STRUCTURE_REVERSION_V1" in terminals
    assert "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1" in terminals
    program = _load(PROGRAM_PATH)
    assert program["strategy_identity"] == ("VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1")
    assert (
        "VOLATILITY_TERM_STRUCTURE_REVERSION_V1"
        in program["causal_independence"]["forbidden_lineage_refs"]
    )


def test_fail_closed_on_semantics_mutation() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["admission_mechanism"]["depressed_continuation_entry"][
        "entry_only_after_depressed_term_structure_state"
    ] = False
    with pytest.raises(PreregistrationValidationError, match="CONTINUATION_ORDER"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(contract)
    bad2["admission_mechanism"]["depressed_continuation_entry"]["direction_rule"] = (
        "opposite_to_signed_return_over_short_horizon_window"
    )
    with pytest.raises(PreregistrationValidationError, match="DIRECTION_RULE"):
        validate_measurement_contract(bad2)
    bad3 = copy.deepcopy(contract)
    bad3["development_run_count"] = 1
    with pytest.raises(PreregistrationValidationError, match="DEVELOPMENT_RUN_COUNT"):
        validate_measurement_contract(bad3)
    bad4 = copy.deepcopy(contract)
    bad4["holdout_authorized"] = True
    with pytest.raises(PreregistrationValidationError, match="HOLDOUT_AUTHORIZED"):
        validate_measurement_contract(bad4)
    bad5 = copy.deepcopy(contract)
    bad5["contract_digest"] = "0" * 64
    with pytest.raises(PreregistrationValidationError, match="CONTRACT_DIGEST_MISMATCH"):
        validate_measurement_contract(bad5)


def test_digest_stable_and_evidence_surfaces() -> None:
    contract = _load(CONTRACT_PATH)
    assert compute_contract_digest(contract) == contract["contract_digest"]
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1_"
        "PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1"
    ) in text
    assert "HOLDOUT" in text.upper()
    assert EVIDENCE.is_dir()
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert CLI.is_file()
    owners = _load(OWNER_MAP)["allowed_optimization_surfaces"]
    key = (
        "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1_"
        "HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
    )
    assert key in owners
    assert CONTRACT_REL_PATH in owners[key]["path_prefixes"]
