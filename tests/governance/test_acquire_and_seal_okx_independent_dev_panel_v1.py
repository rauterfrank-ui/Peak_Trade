"""Contract tests for sealed independent OKX development panel v1.

Evidence/governance only. No network in CI. No sealed-holdout content inspection.
No hypothesis implementation. No economic metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONTRACT = (
    REPO
    / "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json"
)
SEAL_REGISTRY = (
    REPO / "config/research/regime_gated_standaside_mr_independent_dev_panel_seal_registry_v1.json"
)
EVIDENCE = REPO / "docs/evidence/acquire_and_seal_okx_independent_dev_panel_v1"
GOVERNANCE = REPO / "docs/governance/REGIME_GATED_STANDASIDE_MR_INDEPENDENT_DEV_PANEL_SEALED_V1.md"
HOLDOUT_START = "2023-08-16T05:55:00Z"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
PUBLIC_PATHS = {
    "/api/v5/public/instruments",
    "/api/v5/market/history-candles",
}
FORBIDDEN_PRODUCTIVE_PREFIXES = (
    "src/trading/",
    "src/execution/",
    "src/risk/",
    "src/strategies/",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_contract_and_registry_seal_gates_closed() -> None:
    contract = _load(CONTRACT)
    registry = _load(SEAL_REGISTRY)
    assert contract["verdict"] == "SEALED_INDEPENDENT_DEV_PANEL"
    assert contract["status"] == "ACQUISITION_EXECUTED_AND_DEVELOPMENT_PANEL_SEALED"
    assert registry["status"] == "SEALED_INDEPENDENT_DEV_PANEL"
    assert contract["proposed_development_dataset_id"] == DATASET_ID
    assert registry["dataset_id"] == DATASET_ID
    for blob in (contract["classification"], registry["classification"]):
        assert blob["role"] == "DEVELOPMENT_ONLY"
        assert blob["holdout_forbidden"] is True
        assert blob["promotion_eligible"] is False
        assert blob["economic_gate_opened"] is False
        assert blob["economic_validity_offline_gate_pass"] is False
        assert blob["live_authorized"] is False
        assert blob["orders_allowed"] is False
    acq = contract["acquisition_requirements"]
    assert acq["public_okx_read_only"] is True
    assert acq["credentials_forbidden"] is True
    assert set(acq["public_endpoints_used"]) == PUBLIC_PATHS
    assert acq["period_end_exclusive_utc"] == HOLDOUT_START
    assert acq["acquisition_started"] is True
    assert acq["materialized"] is True
    assert contract["execution_result"]["raw_data_tracked_in_git"] is False
    assert "NO_SEALED_HOLDOUT_CONTENT_INSPECTION" in contract["explicit_non_actions"]
    assert "NO_AUTHENTICATED_OKX_ENDPOINTS" in contract["explicit_non_actions"]


def test_panel_period_and_quality_meet_contract() -> None:
    summary = _load(EVIDENCE / "summary.json")
    quality = _load(EVIDENCE / "data_quality.json")
    universe = _load(EVIDENCE / "universe_manifest.json")
    registry = _load(SEAL_REGISTRY)
    assert summary["development_panel_sealed"] is True
    assert summary["decision_class"] == "SEALED_INDEPENDENT_DEV_PANEL"
    assert summary["common_panel_end"] == HOLDOUT_START
    assert summary["common_panel_start"] < HOLDOUT_START
    assert float(summary["common_panel_duration_days"]) >= 365.0
    assert int(summary["instrument_count_valid"]) >= 20
    assert int(summary["instrument_count_acquired"]) == int(summary["instrument_count_valid"])
    assert summary["btc_excluded"] is True
    assert summary["spot_excluded"] is True
    assert summary["futures_only"] is True
    assert summary["gaps_found"] is False
    assert summary["duplicates_found"] is False
    assert summary["ordering_valid"] is True
    assert summary["pit_proven"] is True
    assert quality["gaps_found"] == 0
    assert quality["duplicates_found"] == 0
    assert quality["ordering_errors"] == 0
    assert quality["economic_metrics_computed"] is False
    assert quality["credentials_used"] is False
    assert "BTC-USDT-SWAP" not in universe["long_panel_native_ids"]
    assert all(i.endswith("-USDT-SWAP") for i in universe["long_panel_native_ids"])
    assert not any(i.startswith("BTC-") for i in universe["long_panel_native_ids"])
    assert len(universe["long_panel_native_ids"]) == 46
    assert registry["hashes"]["root_manifest_sha256"] == summary["root_manifest_hash"]
    assert summary["raw_data_tracked_in_git"] is False


def test_sealed_holdout_remains_opaque_exclusion() -> None:
    contract = _load(CONTRACT)
    summary = _load(EVIDENCE / "summary.json")
    boundary = (EVIDENCE / "boundary_attestation.md").read_text(encoding="utf-8")
    exclusion = contract["sealed_holdout_opaque_exclusion"]
    assert exclusion["evidence_id"] == "offline_economic_reevaluation_sealed_long_panel_v1"
    assert exclusion["content_inspection_authorized"] is False
    assert exclusion["reuse_for_development_forbidden"] is True
    assert summary["sealed_holdout_accessed"] is False
    assert summary["sealed_holdout_content_inspected"] is False
    assert "No read/copy/derive of holdout pack contents" in boundary
    this_source = Path(__file__).read_text(encoding="utf-8")
    assert "_".join(("baseline", "metrics.json")) not in this_source
    assert "_".join(("probe", "summary.json")) not in this_source
    assert "_".join(("concentration", "metrics.json")) not in this_source


def test_evidence_governance_and_scope_surfaces() -> None:
    assert GOVERNANCE.is_file()
    gov = GOVERNANCE.read_text(encoding="utf-8")
    assert "PROMOTION_ELIGIBLE=false" in gov
    assert "SEALED_INDEPENDENT_DEV_PANEL" in gov
    for name in (
        "README.md",
        "summary.json",
        "external_artifact_hashes.json",
        "universe_manifest.json",
        "data_quality.json",
        "boundary_attestation.md",
        "safety_attestation.md",
    ):
        assert (EVIDENCE / name).is_file()
    hashes = _load(EVIDENCE / "external_artifact_hashes.json")
    assert hashes["raw_data_tracked_in_git"] is False
    assert len(hashes["root_manifest_sha256"]) == 64
    allowed_roots = (
        "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json",
        "config/research/regime_gated_standaside_mr_independent_dev_panel_seal_registry_v1.json",
        "docs/evidence/acquire_and_seal_okx_independent_dev_panel_v1/",
        "docs/governance/REGIME_GATED_STANDASIDE_MR_INDEPENDENT_DEV_PANEL_SEALED_V1.md",
        "tests/governance/test_acquire_and_seal_okx_independent_dev_panel_v1.py",
        "src/research/longer_chronological_pit_acquisition_v1/",
        "tests/research/test_longer_chronological_pit_sealed_lifecycle_acquisition_v1.py",
    )
    for prefix in FORBIDDEN_PRODUCTIVE_PREFIXES:
        assert not any(item.startswith(prefix) for item in allowed_roots)
