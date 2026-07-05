"""Unit tests for sparse signal inconclusive failure classification execution v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.research.post_no_pass_sparse_signal_inconclusive_failure_classification_execution_v0 import (
    CONFIRM_GO,
    EVIDENCE_CLASS_ID,
    PRIMARY_CLASSIFICATION,
    PROCESS_CLASSIFICATION,
    _collect_classification,
    _load_json,
    _require_config_gates,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_sparse_signal_inconclusive_failure_classification_v0.json"
)
SOURCE_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
    "/implementation/post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_v0_20260705T213529Z"
)


class TestPostNoPassSparseSignalInconclusiveFailureClassificationExecutionV0:
    def test_require_config_gates_accepts_execution_complete_config(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        payload["status"] = "SCOPE_DEFINED_NOT_EXECUTED"
        _require_config_gates(payload)

    def test_collect_classification_from_parent_evidence(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        config["status"] = "SCOPE_DEFINED_NOT_EXECUTED"
        result = _collect_classification(
            config=config,
            source_ref=SOURCE_EVIDENCE,
            source_manifest_rc=0,
        )
        assert result["evidence_class"] == EVIDENCE_CLASS_ID
        assert result["process_classification"] == PROCESS_CLASSIFICATION
        assert result["consumed_go_token"] == CONFIRM_GO
        assert result["primary_classification"] == PRIMARY_CLASSIFICATION
        assert result["classification_mapped_ratio"] == 1.0
        assert result["admissibility_summary"]["economic_evaluation_executed"] is False
        assert result["admissibility_summary"]["backtests_executed"] is False
        assert result["no_promotion_claim"] is True
        assert len(result["failure_axis_results"]) == 3

    def test_invalid_go_token_rejected(self) -> None:
        from scripts.research.post_no_pass_sparse_signal_inconclusive_failure_classification_execution_v0 import (
            run_classification_execution_v0,
        )

        with pytest.raises(SystemExit):
            run_classification_execution_v0(confirm_go_token="GO_INVALID")

    def test_parent_fleet_verdict_unchanged(self) -> None:
        fleet = _load_json(SOURCE_EVIDENCE / "FLEET_VERDICT.json")
        assert fleet["fleet_status"] == "INCONCLUSIVE"
        assert fleet["fleet_verdict"] == "EXECUTION_FAILED_FAIL_CLOSED"
