"""Contract tests for STEP31F promotion metric materialization path execution owner v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.research.panel_sequential_signal_density_research_adapter_v0 import (
    ADAPTER_KIND,
    materialize_panel_member_evaluation_dataset_v0,
    resolve_panel_staging_root,
)
from src.research.step31f_promotion_metric_materialization_path_execution_owner_v0 import (
    PROCESS_CLASSIFICATION,
    REASON_OBSERVED_L1_USED_MISSING,
    REASON_SPARSE_SIGNAL_INPUT_MISSING,
    SCOPE_CLASSIFICATION,
    PromotionMetricMaterializationContractVerdict,
    bind_step31f_promotion_metric_materialization_dataset_manifest_v0,
    materialize_promotion_metric_materialization_record_from_sparse_signal_inputs_v0,
    validate_step31f_promotion_metric_materialization_manifest_contract_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PARENT_MANIFEST = (
    REPO_ROOT.parent
    / "Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/"
    "post_no_pass_metric_materialization_path_offline_economic_evaluation_execution_v0_20260705T235133Z/"
    "RUNTIME_STEP31F_CONFIGS/datasets/okx_linear_perpetual_USDC_USDT_USDT_perp/dataset_manifest.json"
)
SPARSE_FIXTURE = {
    "adapter_kind": ADAPTER_KIND,
    "evaluation_instrument_id": "okx:linear_perpetual:USDC:USDT:USDT:perp",
    "evaluation_native_instrument_id": "USDC-USDT-SWAP",
    "instruments_scanned": 118,
    "instruments_with_nonzero_trades": 93,
    "instruments_with_zero_trades": 25,
    "max_trade_count": 53,
    "member_trade_counts": {"okx:linear_perpetual:USDC:USDT:USDT:perp": 53},
    "panel_member_count": 118,
    "rotation_policy": "deterministic_instrument_id_asc",
    "sparse_signal_research": True,
}


def _load_parent_manifest() -> dict[str, Any]:
    return json.loads(PARENT_MANIFEST.read_text(encoding="utf-8"))


class TestStep31fPromotionMetricMaterializationPathExecutionOwnerV0Contract:
    def test_scope_classification_constants(self) -> None:
        assert (
            PROCESS_CLASSIFICATION
            == "STEP31F_PROMOTION_METRIC_MATERIALIZATION_PATH_EXECUTION_OWNER_NARROW_IMPLEMENTATION_FIX_SCOPE_V0"
        )
        assert (
            SCOPE_CLASSIFICATION
            == "NARROW_IMPLEMENTATION_FIX_NO_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY"
        )

    def test_fail_closed_for_missing_observed_l1_used(self) -> None:
        manifest = _load_parent_manifest()
        verdict, reasons = validate_step31f_promotion_metric_materialization_manifest_contract_v0(
            manifest
        )
        assert verdict is PromotionMetricMaterializationContractVerdict.CONTRACT_FAIL_CLOSED
        assert REASON_OBSERVED_L1_USED_MISSING in reasons

    def test_bind_manifest_satisfies_runner_preconditions(self) -> None:
        manifest = bind_step31f_promotion_metric_materialization_dataset_manifest_v0(
            _load_parent_manifest()
        )
        verdict, reasons = validate_step31f_promotion_metric_materialization_manifest_contract_v0(
            manifest
        )
        assert verdict is PromotionMetricMaterializationContractVerdict.CONTRACT_SATISFIED
        assert reasons == ()
        assert manifest["observed_l1_used"] is False
        assert manifest["l1_observation_status"] == "EXECUTION_MODEL_BOUND_NOT_OBSERVED"

    def test_sparse_signal_inputs_materialize_record_without_pass(self) -> None:
        manifest = bind_step31f_promotion_metric_materialization_dataset_manifest_v0(
            _load_parent_manifest()
        )
        record = materialize_promotion_metric_materialization_record_from_sparse_signal_inputs_v0(
            strategy_id="trend_following",
            strategy_version="v3",
            sparse_signal_density_metrics=SPARSE_FIXTURE,
            dataset_manifest=manifest,
            promotion_metrics_payload=None,
        )
        payload = record.to_dict()
        assert payload["promotion_metrics_materialized"] is False
        assert payload["economic_viability_evidence_pass_created"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["live_authorized"] is False
        assert payload["orders_allowed"] is False
        assert payload["economic_evaluation_executed"] is False
        assert payload["backtest_executed"] is False

    def test_missing_sparse_signal_inputs_fail_closed(self) -> None:
        record = materialize_promotion_metric_materialization_record_from_sparse_signal_inputs_v0(
            strategy_id="trend_following",
            strategy_version="v3",
            sparse_signal_density_metrics={},
            dataset_manifest=_load_parent_manifest(),
        )
        assert record.dataset_manifest_contract_verdict is (
            PromotionMetricMaterializationContractVerdict.CONTRACT_FAIL_CLOSED
        )
        assert REASON_SPARSE_SIGNAL_INPUT_MISSING in record.reason_codes
        assert record.economic_viability_evidence_pass_created is False

    def test_pass_evidence_not_created_from_negative_payload(self) -> None:
        manifest = bind_step31f_promotion_metric_materialization_dataset_manifest_v0(
            _load_parent_manifest()
        )
        record = materialize_promotion_metric_materialization_record_from_sparse_signal_inputs_v0(
            strategy_id="trend_following",
            strategy_version="v3",
            sparse_signal_density_metrics=SPARSE_FIXTURE,
            dataset_manifest=manifest,
            promotion_metrics_payload={"evidence_status": "RESEARCH_NO_PASS"},
        )
        assert record.promotion_metrics_materialized is True
        assert record.economic_viability_evidence_pass_created is False

    @pytest.mark.skipif(
        not resolve_panel_staging_root().is_dir(),
        reason="panel staging root unavailable in this environment",
    )
    def test_panel_adapter_materialized_manifest_satisfies_contract(self, tmp_path: Path) -> None:
        staging_root = resolve_panel_staging_root()
        binding = __import__(
            "src.research.panel_sequential_signal_density_research_adapter_v0",
            fromlist=["load_sorted_panel_binding"],
        ).load_sorted_panel_binding(staging_root)
        instrument_id = binding.instrument_ids[0]
        narrow = materialize_panel_member_evaluation_dataset_v0(
            staging_root=staging_root,
            instrument_id=instrument_id,
            output_root=tmp_path / "member",
        )
        manifest = json.loads(narrow.manifest_path.read_text(encoding="utf-8"))
        verdict, reasons = validate_step31f_promotion_metric_materialization_manifest_contract_v0(
            manifest
        )
        assert verdict is PromotionMetricMaterializationContractVerdict.CONTRACT_SATISFIED, reasons
        assert manifest["observed_l1_used"] is False
