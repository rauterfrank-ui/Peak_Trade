"""Contract tests for collector output contract coverage precondition gap fix v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.research.offline_source_evidence_admissibility_review_execution_v0 import (
    _count_missing_source_records,
)
from src.research.offline_source_evidence_contract_collector_materialization_v0 import (
    CONTRACT_IDS,
    collect_all_contracts,
    count_records_with_missing_source_sentinel,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_EVALUATION_BUNDLE = (
    ARCHIVE_ROOT
    / "implementation/post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z"
)
LEGACY_COLLECTOR_BUNDLE = (
    ARCHIVE_ROOT
    / "implementation/offline_source_evidence_contract_collector_materialization_v0_20260706T054758Z"
)


@pytest.fixture
def synthetic_parent_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "parent_evaluation"
    bundle.mkdir()
    for candidate in ("trend_following", "bollinger_bands", "momentum_1h"):
        (bundle / f"CANDIDATE_RESULT_{candidate}.json").write_text(
            json.dumps(
                {
                    "canonical_candidate_identifier": f"{candidate}/post_v4_hypothesis_v0",
                    "evidence_status": "ROBUSTNESS_FAILED",
                    "gross_return": 0.01,
                    "net_return": -0.02,
                    "net_expectancy": -0.03,
                    "evaluation_timestamp": "2026-07-06T04:00:00Z",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (bundle / f"ECONOMIC_VIABILITY_EVIDENCE_{candidate}.json").write_text(
            json.dumps(
                {
                    "instrument_id_or_universe": "ETH-USDT-SWAP",
                    "turnover": {
                        "semantic": "NOT_COMPUTED",
                        "reason_code": "turnover_not_computed",
                    },
                    "fee_drag": {
                        "semantic": "NOT_COMPUTED",
                        "reason_code": "fee_drag_not_computed",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
    return bundle


class TestCollectorOutputContractCoveragePreconditionGapFixV0Contract:
    def test_legacy_archive_collector_output_is_sentinel_only(self) -> None:
        if not LEGACY_COLLECTOR_BUNDLE.is_dir():
            pytest.skip("legacy collector bundle unavailable")
        total = missing = 0
        for contract_id in CONTRACT_IDS:
            missing_count, total_count = _count_missing_source_records(
                LEGACY_COLLECTOR_BUNDLE / f"{contract_id}.jsonl"
            )
            total += total_count
            missing += missing_count
        assert total == 15
        assert missing == 15

    def test_fixed_collector_output_has_no_missing_source_sentinel_records(
        self, synthetic_parent_bundle: Path
    ) -> None:
        result = collect_all_contracts(
            parent_evaluation_ref=synthetic_parent_bundle,
            parent_manifest_digest="digest",
        )
        for contract_id in CONTRACT_IDS:
            records = result["contracts"][contract_id]["records"]
            assert count_records_with_missing_source_sentinel(records) == 0, contract_id

    @pytest.mark.skipif(
        not PARENT_EVALUATION_BUNDLE.is_dir(),
        reason="durable archive parent bundle unavailable",
    )
    def test_archive_parent_fixed_collector_passes_admissibility_sentinel_counter(self) -> None:
        result = collect_all_contracts(
            parent_evaluation_ref=PARENT_EVALUATION_BUNDLE,
            parent_manifest_digest="archive-digest",
        )
        total = missing = 0
        for contract_id in CONTRACT_IDS:
            records = result["contracts"][contract_id]["records"]
            assert count_records_with_missing_source_sentinel(records) == 0, contract_id
            missing += count_records_with_missing_source_sentinel(records)
            total += len(records)
        assert total == 15
        assert missing == 0
