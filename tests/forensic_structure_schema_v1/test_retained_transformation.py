"""Retained derived transformation persist tests. Authority remains NONE."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    bound_inputs_available,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.constants import (
    DR_RESIDUAL_IDS,
    EXPECTED_LOSSLESSNESS,
    EXPECTED_SOURCE_SHA256,
    OUTPUT_AUTHORITY,
    RETAINED_OUTPUT_ROLE,
    SW_RESIDUAL_IDS,
)
from scripts.ops.forensic_structure_schema_v1.retained_output import persist_retained_derived
from scripts.ops.run_forensic_structure_schema_v1_transformer import main as runner_main


def test_runner_exposes_retained_persist_flag() -> None:
    assert callable(runner_main)
    text = Path("scripts/ops/run_forensic_structure_schema_v1_transformer.py").read_text(
        encoding="utf-8"
    )
    assert "--persist-retained-derived" in text
    assert "--two-run-determinism" in text
    assert "persist_retained_derived" in text


def test_retained_role_is_not_canonical() -> None:
    assert RETAINED_OUTPUT_ROLE == "DERIVED_FORENSIC_STRUCTURE"
    assert OUTPUT_AUTHORITY == "NONE"


@pytest.mark.skipif(not bound_inputs_available(), reason="bound forensic inputs absent")
def test_retained_dataset_oracles_and_non_inference(tmp_path: Path) -> None:
    cached = run_bound_transformer()
    persist = persist_retained_derived(
        source_path=BOUND_SOURCE,
        sidecar_path=BOUND_SIDECAR,
        reports_dir=tmp_path / "reports",
        dataset_dir=tmp_path / "dataset",
        run_pipeline=False,
        result=cached,
    )
    assert persist.result.output_eligible is True
    assert persist.dataset["output_role"] == RETAINED_OUTPUT_ROLE
    assert persist.dataset["output_authority"] == "NONE"
    assert persist.dataset["output_is_canonical"] is False
    assert persist.dataset["semantic_canonicalization_performed"] is False
    assert persist.losslessness_audit["status"] == "PASS"
    assert persist.invariant_report["status"] == "PASS"
    assert persist.traceability_report["status"] == "PASS"
    assert persist.non_inference_audit["status"] == "PASS"
    assert persist.residual_register["residuals_auto_closed"] is False
    assert persist.residual_register["resolved_by_transformation"] is False
    assert persist.residual_register["open_sw_residuals"] == list(SW_RESIDUAL_IDS)
    assert persist.residual_register["open_dr_residuals"] == list(DR_RESIDUAL_IDS)
    assert persist.manifest["source_locator"] == str(BOUND_SOURCE)
    assert "Desktop" not in persist.manifest["source_locator"]
    assert "Downloads" not in persist.manifest["source_locator"]
    counts = persist.result.state.losslessness_audit.counts
    assert counts["LAYER1_COUNT"] == EXPECTED_LOSSLESSNESS["LAYER1_COUNT"]
    assert counts["LAYER1_GAPS"] == 0
    assert counts["LAYER1_OVERLAPS"] == 0
    assert counts["T5_MULTILABEL_COLLAPSED_TRUE_COUNT"] == 0
    assert all(
        flag is False for flag in persist.non_inference_audit["promotions_detected"].values()
    )
    for env in persist.dataset["semantic_envelopes"]:
        assert env["transformation_local_id"]
        assert env["source_sha256"] == EXPECTED_SOURCE_SHA256
    for rel in persist.dataset["relation_envelopes"]:
        assert rel["relation_id"]
        assert rel["from_binding"]["kind"]
        assert rel["to_binding"]["kind"]
    assert persist.losslessness_audit["preservation_oracles"] == {
        "SOURCE_OCCURRENCE_PRESERVATION": "PASS",
        "OVERLAY_CARDINALITY_PRESERVATION": "PASS",
        "DUPLICATE_PRESERVATION": "PASS",
        "NULL_PRESERVATION": "PASS",
        "ABSENT_PRESERVATION": "PASS",
        "UNKNOWN_PRESERVATION": "PASS",
        "UNCLASSIFIED_PRESERVATION": "PASS",
        "SOURCE_ORDER_PRESERVATION": "PASS",
        "NAVIGATION_VIEW_RETENTION": "PASS",
        "NAVIGATION_VIEW_NON_AUTHORITY": "PASS",
        "LAYER1_UNCHANGED_BY_VIEW_RETENTION": "PASS",
    }
    assert persist.dataset["dataset_only_reconstruction_claim"] is False
    assert persist.manifest["dataset_only_reconstruction_claim"] is False
    assert persist.losslessness_audit["reconstruction_sha_match"] is True
    reconstructed_sha = persist.losslessness_audit["reconstructed_source_sha256"]
    assert reconstructed_sha == EXPECTED_SOURCE_SHA256
    views = persist.dataset["navigation_views"]
    assert len(views) == 12
    assert all(v["sw_r_009_status"] == "OPEN" for v in views)
    sw9 = next(r for r in persist.result.state.residuals if r.residual_id == "SW-R-009")
    assert sw9.status == "OPEN"
    assert persist.record_counts["navigation_views"] == 12
    assert persist.record_counts["residuals"] == 21
