"""Contract tests for Bollinger-v2 sealed-panel terminal archive + next hypothesis v1.

Evidence/governance only. No full-panel backtest. No runtime/promotion activation.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BINDING = REPO / "config/research/bollinger_bands_v2_full_canonical_system_economic_binding_v1.json"
CLOSEOUT = (
    REPO
    / "config/research/bollinger_bands_v2_sealed_long_panel_terminal_economic_fail_archive_and_next_hypothesis_v1.json"
)
EVIDENCE = REPO / "docs/evidence/archive_failed_bollinger_v2_and_next_hypothesis_v1"
SOURCE_EVIDENCE = REPO / "docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1"
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_BANDS_V2_SEALED_LONG_PANEL_TERMINAL_ECONOMIC_FAIL_ARCHIVE_AND_NEXT_HYPOTHESIS_V1.md"
)
EXPECTED_HASH = "c38f1d25f3c2f84eed9b5bbb2d07e08df197fe2d6805d301a57a25599928af08"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_source_evidence_fail_economic_exists() -> None:
    summary = _load(SOURCE_EVIDENCE / "summary.json")
    assert summary["economic_class"] == "FAIL_ECONOMIC"
    assert summary["PROMOTION_ELIGIBLE"] is False
    assert summary["ECONOMIC_GATE_OPENED"] is False
    assert summary["config_hash"] == EXPECTED_HASH


def test_binding_archived_terminal_and_gate_closed() -> None:
    binding = _load(BINDING)
    assert binding["promotion_eligible"] is False
    assert binding["economic_validity_offline_gate_pass"] is False
    assert binding["economic_validity_status"] == "FAIL_ECONOMIC"
    assert binding["status"] == "TERMINAL_ECONOMIC_FAIL_ARCHIVED"
    assert binding["binding_status"] == "TERMINAL_ECONOMIC_FAIL_ARCHIVED"
    archive = binding["terminal_economic_archive_v1"]
    assert archive["economic_class"] == "FAIL_ECONOMIC"
    assert archive["promotion_eligible"] is False
    assert archive["economic_gate_opened"] is False
    assert archive["economic_validity_offline_gate_changed"] is False
    assert archive["measurement_bug_found"] is False
    assert archive["sealed_holdout_retune_forbidden"] is True
    assert archive["automatic_replacement_activation_forbidden"] is True
    assert archive["append_only"] is True
    assert archive["history_overwrite"] is False
    assert archive["source_evidence_id"] == "offline_economic_reevaluation_sealed_long_panel_v1"
    assert archive["config_file_sha256_at_evaluation"] == EXPECTED_HASH


def test_closeout_defines_exactly_one_research_only_hypothesis() -> None:
    closeout = _load(CLOSEOUT)
    assert closeout["promotion_eligible"] is False
    assert closeout["economic_gate_opened"] is False
    assert closeout["economic_validity_offline_gate_changed"] is False
    assert closeout["new_hypothesis_count"] == 1
    assert (
        closeout["new_hypothesis_id"]
        == "REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1"
    )
    assert closeout["new_hypothesis_research_only"] is True
    assert closeout["new_hypothesis_runtime_activated"] is False
    assert closeout["no_implementation_in_this_slice"] is True
    assert closeout["sealed_holdout_retune_forbidden"] is True
    assert closeout["automatic_replacement_activation_forbidden"] is True


def test_hypothesis_spec_and_holdout_policy() -> None:
    spec = _load(EVIDENCE / "new_hypothesis_spec.json")
    split = _load(EVIDENCE / "dataset_split_policy.json")
    summary = _load(EVIDENCE / "summary.json")
    assert spec["research_only"] is True
    assert spec["runtime_activated"] is False
    assert spec["implementation_authorized"] is False
    assert spec["promotion_eligible"] is False
    assert spec["entry_side_expected"] == "NONE"
    assert spec["direction_semantics"]["long_allowed"] is True
    assert spec["direction_semantics"]["short_allowed"] is True
    assert spec["direction_semantics"]["standaside_required_outside_range_regime"] is True
    assert split["sealed_holdout"]["tuning_forbidden"] is True
    assert split["sealed_holdout"]["hypothesis_selection_forbidden"] is True
    assert split["independent_development_requirements"]["download_now"] is False
    assert summary["sealed_panel_used_for_tuning"] is False
    assert summary["sealed_panel_reserved_as_holdout"] is True
    assert summary["new_hypothesis_count"] == 1
    assert summary["automatic_replacement_activated"] is False


def test_governance_doc_and_evidence_pack_exist() -> None:
    assert GOVERNANCE.is_file()
    assert "PROMOTION_ELIGIBLE=false" in GOVERNANCE.read_text(encoding="utf-8")
    assert (EVIDENCE / "README.md").is_file()
    assert (EVIDENCE / "root_cause_matrix.json").is_file()
    assert (EVIDENCE / "archival_decision.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
