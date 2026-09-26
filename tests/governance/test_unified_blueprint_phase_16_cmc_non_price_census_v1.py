"""Governance proof for Unified Blueprint Phase 16 CMC census."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.unified_blueprint_phase_16_cmc_non_price_census_v1 import (
    INTEGRATION_CONFIG,
    WORKPACKAGE_ID,
    build_phase_16_census_summary_v1,
    prove_unified_blueprint_phase_16_cmc_non_price_census_v1,
    validate_phase_16_authority_invariants,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))


def test_phase_16_census_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_phase_16_cmc_non_price_census_v1(repo_root=REPO_ROOT)


def test_phase_16_census_authority_invariants() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_phase_16_authority_invariants(doc)
    assert doc["cmc_census_closure_status"] == "CLOSED"


def test_phase_16_summary_records_blocker_and_next_boundary() -> None:
    summary = build_phase_16_census_summary_v1(repo_root=REPO_ROOT)
    assert summary["phase_16_cmc_census_status"] == "PROVEN_COMPLETE"
    assert summary["earliest_blocker_before_phase_17"] == (
        "NORMATIVE_NON_PRICE_CMC_CONTRACT_OWNER_DECISION"
    )
