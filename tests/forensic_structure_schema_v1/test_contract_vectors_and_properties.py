"""Bound-input contract vectors TV-001..TV-012 and residual properties."""

from __future__ import annotations

import pytest

from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    bound_inputs_available,
    run_bound_transformer as _run_bound,
)
from scripts.ops.forensic_structure_schema_v1.constants import (
    DR_RESIDUAL_IDS,
    DUAL_CLASS_OCCURRENCE_ID,
    EXPECTED_SIDECAR_SHA256,
    EXPECTED_SOURCE_SHA256,
    FIXTURE_IDS,
    HISTORICAL_LOCATOR_TOKEN_CLASS,
    SW_RESIDUAL_IDS,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes
from scripts.ops.forensic_structure_schema_v1.transformer import transform_read_only


def run_bound_transformer():
    if not bound_inputs_available():
        pytest.skip("bound forensic source/sidecar not present in this environment")
    return _run_bound()


def test_tv_001_ordered_before() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-001"].status == "PASS"


def test_tv_002_pointer_conflict() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-002"].status == "PASS"


def test_tv_003_multilabel() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-003"].status == "PASS"


def test_tv_004_duplicate_fence() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-004"].status == "PASS"


def test_tv_005_t5_range() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-005"].status == "PASS"


def test_tv_006_hash_unknown() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-006"].status == "PASS"


def test_tv_007_h1_span() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-007"].status == "PASS"


def test_tv_008_current_token() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-008"].status == "PASS"


def test_tv_009_dependency_alias() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-009"].status == "PASS"


def test_tv_010_embedded_prior_report() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-010"].status == "PASS"


def test_tv_011_wrapper_mention() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-011"].status == "PASS"


def test_tv_012_tick5_inner() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["TV-012"].status == "PASS"


def test_sw_r_013_duplicate_multilabel_labels() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["SW-R-013"].status == "PASS"
    residual = next(r for r in result.state.residuals if r.residual_id == "SW-R-013")
    assert residual.status == "OPEN"
    assert residual.auto_closed is False


def test_sw_r_014_null_forensic_record_sha() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["SW-R-014"].status == "PASS"
    residual = next(r for r in result.state.residuals if r.residual_id == "SW-R-014")
    assert residual.status == "OPEN"


def test_sw_r_015_t3_heading_vs_region() -> None:
    result = run_bound_transformer()
    assert result.state.contract_tests["SW-R-015"].status == "PASS"
    residual = next(r for r in result.state.residuals if r.residual_id == "SW-R-015")
    assert residual.status == "OPEN"


def test_layer1_byte_coverage() -> None:
    result = run_bound_transformer()
    spans = result.state.layer1_ordered
    assert len(spans) == 121930
    assert spans[0].byte_start == 0
    assert spans[-1].byte_end == 8639369
    for i in range(len(spans) - 1):
        assert spans[i].byte_end == spans[i + 1].byte_start


def test_exact_duplicate_preservation() -> None:
    result = run_bound_transformer()
    assert result.state.losslessness_audit is not None
    assert result.state.losslessness_audit.counts["H1_CONTINUATION_COUNT"] == 70
    assert result.state.losslessness_audit.counts["FENCE_DUPLICATE_GROUPS"] == 11


def test_deterministic_serialization_two_runs() -> None:
    run_bound_transformer()
    second = transform_read_only(source_path=BOUND_SOURCE, sidecar_path=BOUND_SIDECAR)
    third = transform_read_only(source_path=BOUND_SOURCE, sidecar_path=BOUND_SIDECAR)
    assert second.payload_bytes == third.payload_bytes
    assert dumps_canonical_bytes(second.payload) == second.payload_bytes


def test_round_trip_traceability() -> None:
    result = run_bound_transformer()
    overlay_id = FIXTURE_IDS["TV_006_SHA64"]
    env = result.state.envelope_by_overlay_id[overlay_id][0]
    assert env.source_sha256 == EXPECTED_SOURCE_SHA256
    assert env.sidecar_overlay_id.value == overlay_id
    assert env.layer1_occurrence_id.presence == "present"
    raw = result.state.source_bytes[env.source_byte_start : env.source_byte_end]
    assert raw.decode("utf-8") == env.token_verbatim.value


def test_unknown_preservation() -> None:
    result = run_bound_transformer()
    env = result.state.envelope_by_overlay_id[FIXTURE_IDS["TV_006_SHA64"]][0]
    assert env.hash_kind.to_canonical() == {"presence": "present", "value": "UNKNOWN"}
    assert env.epistemic_class == "UNCLASSIFIED"
    assert env.authority_status == "NONE"
    unclassified_layer2_missing = 121930 - 4068
    assert unclassified_layer2_missing == 117862


def test_stable_source_order() -> None:
    result = run_bound_transformer()
    fences = [e for e in result.state.envelopes if e.overlay_class == "fence_block"]
    orders = [e.source_order for e in fences]
    assert orders == sorted(orders)
    rel_orders = [r.source_order for r in result.state.relations]
    assert rel_orders == list(range(len(result.state.relations)))


def test_zero_source_and_sidecar_mutation() -> None:
    result = run_bound_transformer()
    assert result.state.source_sha256_before == EXPECTED_SOURCE_SHA256
    assert result.state.source_sha256_after == EXPECTED_SOURCE_SHA256
    assert result.state.sidecar_sha256_before == EXPECTED_SIDECAR_SHA256
    assert result.state.sidecar_sha256_after == EXPECTED_SIDECAR_SHA256
    assert result.state.losslessness_audit is not None
    assert result.state.losslessness_audit.source_mutated is False
    assert result.state.losslessness_audit.sidecar_mutated is False


def test_token_layer1_disjointness() -> None:
    result = run_bound_transformer()
    assert result.state.token_occurrence_ids.isdisjoint(result.state.layer1_by_id)


def test_dual_class_h1_preservation() -> None:
    result = run_bound_transformer()
    dual = result.state.layer2_envelopes_by_occurrence[DUAL_CLASS_OCCURRENCE_ID]
    assert len(dual) == 2
    classes = {e.content_class for e in dual}
    assert classes == {"navigation_index", "conflicting_point"}
    assert dual[0].transformation_local_id != dual[1].transformation_local_id


def test_no_synthetic_inner_fence() -> None:
    result = run_bound_transformer()
    assert len(result.state.overlays_by_class["fence_block"]) == 1368


def test_historical_locator_preservation() -> None:
    result = run_bound_transformer()
    locators = [
        r
        for r in result.state.overlays_by_class["token_occurrence"]
        if r.payload.get("token_class") == HISTORICAL_LOCATOR_TOKEN_CLASS
    ]
    assert len(locators) == 50
    desktopish = [
        r
        for r in locators
        if "Desktop" in str(r.payload.get("token_verbatim"))
        or "Downloads" in str(r.payload.get("token_verbatim"))
    ]
    assert desktopish
    for rec in locators:
        assert rec.payload.get("normalized") is False
        assert rec.payload.get("locator_role") == "HISTORICAL_STRING"


def test_authority_none_everywhere() -> None:
    result = run_bound_transformer()
    assert all(e.authority_status == "NONE" for e in result.state.envelopes)
    assert all(r.authority_status == "NONE" for r in result.state.relations)
    assert result.state.witness is not None
    assert result.state.witness.target_authority == "NONE"
    assert result.state.witness.sidecar_authority == "NONE"


def test_currentness_not_promoted() -> None:
    result = run_bound_transformer()
    allowed = {"CURRENTNESS_UNKNOWN", "historical"}
    assert all(e.currentness_status in allowed for e in result.state.envelopes)
    assert all(r.currentness_status == "CURRENTNESS_UNKNOWN" for r in result.state.relations)


def test_residuals_remain_open() -> None:
    result = run_bound_transformer()
    ids = [r.residual_id for r in result.state.residuals]
    assert ids == list(SW_RESIDUAL_IDS) + list(DR_RESIDUAL_IDS)
    assert all(r.status == "OPEN" and r.auto_closed is False for r in result.state.residuals)


def test_output_eligible_test_artifact_only() -> None:
    result = run_bound_transformer()
    assert result.output_eligible is True
    assert result.output_role == "TEST_ARTIFACT_ONLY"
    assert result.payload["output_not_canonical"] is True
    assert result.payload["output_not_source_replacement"] is True
    assert result.payload["residuals_auto_closed"] is False
