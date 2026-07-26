from __future__ import annotations

import json
from pathlib import Path

from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_entry_point_v1 import (
    load_and_validate_repo_entry_point,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    FROZEN_MEASUREMENT_CONTRACT_DIGEST,
    HYPOTHESIS_ID,
    STRATEGY_IDENTITY,
)

REPO = Path(__file__).resolve().parents[2]


def test_entry_point_binding_slot_consumed_after_development_fail() -> None:
    report = load_and_validate_repo_entry_point(REPO)
    assert report["valid"] is True
    assert report["development_run_slot_consumed"] is True
    assert report["hypothesis_id"] == HYPOTHESIS_ID


def test_evidence_summary_terminal_fail() -> None:
    summary = json.loads(
        (
            REPO
            / "docs/evidence/evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1/summary.json"
        ).read_text(encoding="utf-8")
    )
    assert summary["status"] == "DEVELOPMENT_FAIL"
    assert summary["economic_validity"] == "FAIL"
    assert summary["evaluation_executed"] is True
    assert summary["holdout_accessed"] is False
    assert summary["sealed_accessed"] is False
    assert summary["run_slot_consumed"] is True
    assert summary["development_run_count"] == 1
    assert summary["dataset_id"] == DATASET_ID
    assert int(summary["trade_count"]) > 0
    assert summary["economic_gate_pass"] is False


def test_measurement_contract_digest_frozen() -> None:
    contract = json.loads(
        (
            REPO
            / "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_v1_preregistered_economic_hypothesis_measurement_contract_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert contract["contract_digest"] == FROZEN_MEASUREMENT_CONTRACT_DIGEST
    assert contract["strategy_identity"] == STRATEGY_IDENTITY
    # Frozen measurement SSOT keeps pre-run counters; slot truth lives in entry-point/evidence.
    assert contract["development_run_count"] == 0
    assert contract["run_slot_consumed"] is False
