"""Contract tests for independent development-panel inventory (regime-gated MR v1).

Inventory evidence pack remains the historical SSOT for the inventory decision.
Live acquisition contract may later become executed/sealed without invalidating
the inventory pack. No sealed-holdout content inspection.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONTRACT = (
    REPO
    / "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json"
)
EVIDENCE = REPO / "docs/evidence/inventory_independent_dev_panel_regime_gated_mr_v1"
GOVERNANCE = (
    REPO / "docs/governance/REGIME_GATED_STANDASIDE_MR_INDEPENDENT_DEV_PANEL_INVENTORY_V1.md"
)
SEALED_HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
FORBIDDEN_PRODUCTIVE_PREFIXES = (
    "src/trading/",
    "src/execution/",
    "src/risk/",
    "src/strategies/",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_inventory_pack_required_acquisition_at_inventory_time() -> None:
    summary = _load(EVIDENCE / "summary.json")
    pointer = _load(EVIDENCE / "acquisition_contract.json")
    contract = _load(CONTRACT)
    assert summary["research_status"] == "ACQUISITION_CONTRACT_REQUIRED"
    assert summary["development_panel_sealed"] is False
    assert summary["acquisition_contract_created"] is True
    assert pointer["acquisition_started"] is False
    assert pointer["holdout_forbidden"] is True
    assert (
        pointer["proposed_development_dataset_id"]
        == "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    )
    assert (
        contract["hypothesis_id"]
        == "REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1"
    )
    assert (
        contract["proposed_development_dataset_id"]
        == "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    )
    classification = contract["classification"]
    assert classification["role"] == "DEVELOPMENT_ONLY"
    assert classification["holdout_forbidden"] is True
    assert classification["promotion_eligible"] is False
    assert classification["economic_gate_opened"] is False
    assert classification["economic_validity_offline_gate_pass"] is False
    assert classification["live_authorized"] is False
    assert classification["orders_allowed"] is False
    acq = contract["acquisition_requirements"]
    assert acq["futures_only"] is True
    assert acq["btc_excluded"] is True
    assert acq["spot_excluded"] is True
    assert acq["frequency"] == "PT1H"
    assert acq["period_end_exclusive_utc"] == "2023-08-16T05:55:00Z"
    assert acq["period_must_end_before_sealed_holdout_start"] is True
    assert contract["inventory_result"]["suitable_existing_candidate_count"] == 0


def test_sealed_holdout_is_opaque_exclusion_only() -> None:
    contract = _load(CONTRACT)
    boundary = (EVIDENCE / "boundary_attestation.md").read_text(encoding="utf-8")
    exclusion = contract["sealed_holdout_opaque_exclusion"]
    assert exclusion["evidence_id"] == SEALED_HOLDOUT_OPAQUE_ID
    assert exclusion["content_inspection_authorized"] is False
    assert exclusion["reuse_for_development_forbidden"] is True
    assert exclusion["derive_partial_panel_forbidden"] is True
    assert "Opaque exclusion" in boundary
    assert "No read of files under" in boundary
    assert "NO_SEALED_HOLDOUT_CONTENT_INSPECTION" in contract["explicit_non_actions"]
    assert "NO_HYPOTHESIS_IMPLEMENTATION" in contract["explicit_non_actions"]
    assert "NO_ECONOMIC_METRICS" in contract["explicit_non_actions"]


def test_candidate_matrix_fail_closed_no_suitable_candidate() -> None:
    matrix = _load(EVIDENCE / "candidate_matrix.json")
    summary = _load(EVIDENCE / "summary.json")
    assert matrix["candidate_count"] == 5
    assert matrix["suitable_candidate_count"] == 0
    assert matrix["sealed_holdout_content_inspected"] is False
    assert matrix["network_acquisition_performed"] is False
    assert all(c["suitable_for_development"] is False for c in matrix["candidates"])
    assert all(c["independent"] is False for c in matrix["candidates"])
    assert summary["research_status"] == "ACQUISITION_CONTRACT_REQUIRED"
    assert summary["development_panel_sealed"] is False
    assert summary["acquisition_contract_created"] is True
    assert summary["sealed_holdout_content_inspected"] is False
    assert summary["hypothesis_implemented"] is False
    assert summary["economic_metrics_computed"] is False
    assert summary["promotion_eligible"] is False
    assert summary["economic_validity_offline_gate_pass"] is False


def test_evidence_and_governance_surfaces_exist() -> None:
    assert GOVERNANCE.is_file()
    gov = GOVERNANCE.read_text(encoding="utf-8")
    assert "PROMOTION_ELIGIBLE=false" in gov
    assert "ACQUISITION_CONTRACT_REQUIRED" in gov
    for name in (
        "README.md",
        "summary.json",
        "candidate_matrix.json",
        "acquisition_contract.json",
        "safety_attestation.md",
        "boundary_attestation.md",
    ):
        assert (EVIDENCE / name).is_file()
    pointer = _load(EVIDENCE / "acquisition_contract.json")
    assert pointer["acquisition_started"] is False
    assert pointer["holdout_forbidden"] is True


def test_inventory_scope_excludes_productive_trading_prefixes() -> None:
    allowed_roots = (
        "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json",
        "docs/evidence/inventory_independent_dev_panel_regime_gated_mr_v1/",
        "docs/governance/REGIME_GATED_STANDASIDE_MR_INDEPENDENT_DEV_PANEL_INVENTORY_V1.md",
        "tests/governance/test_inventory_independent_dev_panel_regime_gated_mr_v1.py",
    )
    for prefix in FORBIDDEN_PRODUCTIVE_PREFIXES:
        assert not any(item.startswith(prefix) for item in allowed_roots)
