"""Definition-only contract tests for CS short-horizon return-reversal preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_short_horizon_return_reversal_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    PreregistrationValidationError,
    compute_contract_digest,
    load_and_validate_repo_contract,
    validate_measurement_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
COLLISION = (
    REPO
    / "docs/evidence/new_research_program_identity_definition_discovery_v1/collision_matrix.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only_digest_and_gates() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["evaluation_authorized"] is False
    assert report["development_run_count"] == 0
    assert (
        report["hypothesis_id"]
        == "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1"
    )
    payload = _load(CONTRACT_PATH)
    assert compute_contract_digest(payload) == payload["contract_digest"]
    assert payload["score_and_selection"]["polarity"] == "REVERSAL_NEGATED_TRAILING_LOG_RETURN"
    assert payload["parameter_governance"]["frozen_non_grid_parameters"]["lookback_N"] == 24


def test_fail_closed_on_digest_or_eval_mutation() -> None:
    payload = _load(CONTRACT_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(PreregistrationValidationError, match="EVALUATION_AUTHORIZED"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["contract_digest"] = "0" * 64
    with pytest.raises(PreregistrationValidationError, match="CONTRACT_DIGEST_MISMATCH"):
        validate_measurement_contract(bad2)


def test_collision_matrix_selects_reversal_program() -> None:
    matrix = _load(COLLISION)
    assert matrix["scope_id"] == "NEW_RESEARCH_PROGRAM_IDENTITY_DEFINITION_DISCOVERY_V1"
    assert (
        matrix["selected_program_id"]
        == "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1"
    )
    selected = [c for c in matrix["candidates_compared"] if c.get("selected")]
    assert len(selected) == 1
    assert selected[0]["candidate_id"] == "CS_SHORT_HORIZON_RETURN_REVERSAL"
    assert matrix["evaluation_authorized"] is False
