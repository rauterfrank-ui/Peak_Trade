"""Definition-only contract tests for CS intrabar close-location pressure continuation preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_intrabar_close_location_pressure_continuation_v1_hypothesis_preregistration_v1 import (
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
    / "docs/evidence/cross_sectional_intrabar_close_location_pressure_continuation_definition_discovery_v1/collision_matrix.json"
)
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
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
        == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
    )
    payload = _load(CONTRACT_PATH)
    assert compute_contract_digest(payload) == payload["contract_digest"]
    assert (
        payload["score_and_selection"]["polarity"]
        == "INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION"
    )
    assert payload["parameter_governance"]["frozen_non_grid_parameters"]["lookback_N"] == 36
    assert (
        payload["parameter_governance"]["frozen_non_grid_parameters"]["rebalance_interval_bars"]
        == 6
    )


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


def test_collision_matrix_selects_clv_program() -> None:
    matrix = _load(COLLISION)
    assert (
        matrix["scope_id"]
        == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_DEFINITION_ONLY_PREREGISTRATION_V1"
    )
    assert (
        matrix["selected_program_id"]
        == "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_RESEARCH_PROGRAM_V1"
    )
    selected = [c for c in matrix["candidates_compared"] if c.get("selected")]
    assert len(selected) == 1
    assert selected[0]["candidate_id"] == "CS_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION"
    assert matrix["evaluation_authorized"] is False


def test_owner_map_registers_preregistration_surface() -> None:
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    key = "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
    assert key in surfaces
    paths = surfaces[key]["path_prefixes"]
    assert CONTRACT_REL_PATH in paths
