"""Contract tests for FULL_CANONICAL_SYSTEM offline economic evidence execution result."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_REL = "config/research/full_canonical_system_economic_evidence_generation_v1_offline_execution_result_v0.json"
BINDING_REL = "config/research/bollinger_bands_v2_full_canonical_system_economic_binding_v1.json"
EXPECTED_BINDING_DIGEST = "b0b51de225a7e282263c1b00091ccb457612f74df0e817d8dd03efc7af837320"
EXPECTED_DATASET_DIGEST = "0083e0502a05667f5b0ca31d374b3bef066f65aacfdb05ee020490cc1f15c638"
GO_TOKEN = "GO_FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_OFFLINE_EXECUTION"
CANONICAL_ENTRY = "scripts/ops/run_economic_viability_evidence_evaluation_v1.py"


def _load_result() -> dict:
    return json.loads((REPO_ROOT / RESULT_REL).read_text(encoding="utf-8"))


def _load_binding() -> dict:
    return json.loads((REPO_ROOT / BINDING_REL).read_text(encoding="utf-8"))


class TestFullCanonicalSystemEconomicEvidenceGenerationV1OfflineExecutionResult:
    def test_result_digest_identity_matches_ratified_binding(self) -> None:
        result = _load_result()
        binding = _load_binding()
        assert result["binding_digest"] == EXPECTED_BINDING_DIGEST
        assert binding["binding_digest"] == EXPECTED_BINDING_DIGEST
        assert result["dataset_digest"] == EXPECTED_DATASET_DIGEST
        assert binding["dataset_digest"] == EXPECTED_DATASET_DIGEST
        assert result["universe_digest"] == EXPECTED_DATASET_DIGEST
        assert (
            result["binding_id"] == "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
        )

    def test_canonical_entry_point_and_offline_boundaries(self) -> None:
        result = _load_result()
        binding = _load_binding()
        assert result["canonical_entry_point"] == CANONICAL_ENTRY
        assert binding["canonical_offline_orchestrator"] == CANONICAL_ENTRY
        assert (REPO_ROOT / CANONICAL_ENTRY).is_file()
        assert result["offline_only"] is True
        assert result["runtime_effect"] == "NONE"
        assert result["authority_effect"] == "NONE"
        assert result["legacy_bypass_detected"] is False
        assert result["realistic_costs_bound"] is True

    def test_economic_fail_zero_trade_and_robustness_gate(self) -> None:
        result = _load_result()
        assert result["economic_evaluation_executed"] is True
        assert result["economic_status"] == "FAIL"
        assert result["economic_validity_offline_gate_pass"] is False
        assert result["trade_count"] == 0
        assert result["net_return"] == 0.0
        assert result["net_expectancy"] == 0.0
        assert result["profit_factor"] == 0.0
        assert result["sharpe"] == 0.0
        assert result["max_drawdown"] == 0.0
        assert "ZERO_TRADE_DEGENERATION" in result["primary_reason_codes"]
        assert result["robustness_executed"] is False
        assert result["robustness_not_executed_reason"] == "NOT_EXECUTED_BASELINE_NEGATIVE"
        assert result["unchanged_retry_allowed"] is False
        assert result["promotion_eligible"] is False

    def test_go_token_and_evidence_ref_surface(self) -> None:
        result = _load_result()
        assert result["go_token"] == GO_TOKEN
        assert result["go_token_consumed"] is True
        assert result["manifest_verify_rc"] == 0
        assert (
            "full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_"
            in (result["durable_evidence_dir"])
        )
        assert result["status"] == "COMPLETE_FAIL"
        assert result["verdict"] == "FULL_CANONICAL_SYSTEM_ECONOMIC_BASELINE_FAIL"

    def test_robustness_contracts_still_require_separate_go_in_binding(self) -> None:
        binding = _load_binding()
        for key in ("walk_forward_contract", "monte_carlo_contract", "stress_contract"):
            contract = binding[key]
            assert contract["requires_separate_operator_go_after_positive_baseline"] is True
