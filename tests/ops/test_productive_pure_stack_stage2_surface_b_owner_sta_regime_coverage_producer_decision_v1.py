"""Owner/STA regime-coverage producer decision surface contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decision_v1.constants_v1 import (
    ALLOWED_OWNER_VALUES,
    AUTHORIZE_DETAIL_FIELDS,
    AUTHORIZE_OWNER_VALUE,
    BASELINE_ORIGIN_MAIN_SHA,
    CAPABILITY_SCOPE,
    CYBERSECURITY_MIRROR_REL,
    DECISION_ID,
    DECISIONS_MANIFEST_REL,
    FORBIDDEN_EXISTING_PRODUCER_TOKENS,
    OWNER_DECISION_REL,
    PARENT_TRIAD_MANIFEST_REL,
    REJECT_OWNER_VALUE,
    SCHEMA_REL,
    STATUS_SURFACE_OPEN,
    TAXONOMY_SINK_LABELS,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_producer_decision_v1.validator_v1 import (
    RegimeCoverageProducerDecisionErrorV1,
    load_canonical_regime_coverage_producer_decisions_manifest_v1,
    validate_regime_coverage_owner_choice_v1,
    validate_regime_coverage_producer_manifest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION",
    f"CAPABILITY_SCOPE={CAPABILITY_SCOPE}",
    f"STATUS={STATUS_SURFACE_OPEN}",
    f"DECISION_ID={DECISION_ID}",
    "DECISION_STATUS=OPEN",
    "OWNER_VALUE=null",
    f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_ORIGIN_MAIN_SHA}",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "CAMPAIGN_START_AUTHORIZED=false",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false",
    "RAW_INPUT_PACK_CREATED=false",
    "CAMPAIGN_STARTED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED",
    "EXISTING_PRODUCERS_ELEVATED=false",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
    "AUTHORIZE_DEDICATED_SURFACE_B_REGIME_COVERAGE_PRODUCER",
    "EXPLICITLY_REJECT_REGIME_COVERAGE_PRODUCER",
    "canonical_producer_name=null",
    "PIT_no_lookahead_rules_ref=null",
    "low | mid | high | unknown | missing",
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "CAMPAIGN_START_AUTHORIZED=true",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true",
    "NOTION_SSOT=true",
    "EXISTING_PRODUCERS_ELEVATED=true",
    "DASHBOARD_AUTHORITY_EFFECT=AUTHORITY",
)


def test_regime_coverage_artifacts_exist_v1() -> None:
    assert (REPO_ROOT / OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / DECISIONS_MANIFEST_REL).is_file()
    assert (REPO_ROOT / SCHEMA_REL).is_file()
    assert (REPO_ROOT / CYBERSECURITY_MIRROR_REL).is_file()


def test_regime_coverage_document_markers_v1() -> None:
    text = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_DOC_CLAIMS:
        assert claim not in text, claim


def test_canonical_manifest_open_and_null_v1() -> None:
    manifest = load_canonical_regime_coverage_producer_decisions_manifest_v1(REPO_ROOT)
    result = validate_regime_coverage_producer_manifest_v1(manifest)
    assert result["ok"] is True
    assert result["decision_id"] == DECISION_ID
    assert result["status"] == STATUS_SURFACE_OPEN
    assert result["decision_status"] == "OPEN"
    assert result["owner_value"] is None
    assert result["allowed_owner_values"] == list(ALLOWED_OWNER_VALUES)
    assert result["authorize_detail_fields_null"] is True
    assert result["existing_producers_elevated"] is False
    assert result["input_authority"] is False
    assert result["runtime_implemented"] is False
    assert result["raw_input_pack_created"] is False
    assert result["raw_input_pack_materialization_authorized"] is False
    assert result["campaign_started"] is False
    assert result["campaign_start_authorized"] is False
    assert result["productive_numeric_values_set"] == 0
    assert result["regime_coverage_status"] == "SEMANTICALLY_UNRESOLVED"
    assert result["dashboard_authority_effect"] == "NONE"
    assert manifest["owner_value"] is None
    assert manifest["decision_status"] == "OPEN"
    assert tuple(manifest["allowed_owner_values"]) == ALLOWED_OWNER_VALUES
    assert tuple(manifest["taxonomy_sink_labels"]) == TAXONOMY_SINK_LABELS
    for field in AUTHORIZE_DETAIL_FIELDS:
        assert manifest["authorize_detail_fields"][field] is None, field
    for key, value in manifest["open_null_instance_fields"].items():
        assert value is None, key
    assert manifest["open_null_instance_fields"]["regime_coverage_counts"] is None
    assert manifest["decisions"]["REGIME_COVERAGE_PRODUCER"]["coverage_counts"] is None


def test_schema_required_keys_present_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    required = set(schema["required"])
    for key in (
        "decision_id",
        "decision_status",
        "owner_value",
        "allowed_owner_values",
        "authorize_detail_fields",
        "regime_coverage_status",
        "existing_producers_elevated",
        "dashboard_authority_effect",
    ):
        assert key in required


def test_markdown_json_semantic_consistency_v1() -> None:
    md = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    manifest = load_canonical_regime_coverage_producer_decisions_manifest_v1(REPO_ROOT)
    assert f"DECISION_ID={manifest['decision_id']}" in md
    assert f"DECISION_STATUS={manifest['decision_status']}" in md
    assert "OWNER_VALUE=null" in md
    assert manifest["owner_value"] is None
    for value in ALLOWED_OWNER_VALUES:
        assert value in md
        assert value in manifest["allowed_owner_values"]
    for field in AUTHORIZE_DETAIL_FIELDS:
        assert f"{field}=null" in md
        assert manifest["authorize_detail_fields"][field] is None
    assert "REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED" in md
    assert manifest["regime_coverage_status"] == "SEMANTICALLY_UNRESOLVED"
    assert "DASHBOARD_AUTHORITY_EFFECT=NONE" in md
    assert manifest["dashboard_authority_effect"] == "NONE"


def test_only_two_owner_values_accepted_v1() -> None:
    for value in ALLOWED_OWNER_VALUES:
        result = validate_regime_coverage_owner_choice_v1(value)
        assert result["ok"] is True
        assert result["owner_value"] == value
        assert result["input_authority"] is False
        assert result["runtime_implemented"] is False
        assert result["campaign_started"] is False
    with pytest.raises(RegimeCoverageProducerDecisionErrorV1, match="OWNER_VALUE_NOT_ALLOWED"):
        validate_regime_coverage_owner_choice_v1("SEMANTICALLY_UNRESOLVED")
    with pytest.raises(RegimeCoverageProducerDecisionErrorV1, match="OWNER_VALUE_NOT_ALLOWED"):
        validate_regime_coverage_owner_choice_v1("analytics.regimes")


def test_reject_existing_producer_elevation_v1() -> None:
    for token in (
        "analytics.regimes",
        "regime.detectors",
        "feature_regime_pipeline_v2",
        "ai.switch_layer",
        "bull/bear evidence readmodel",
        "dashboard_readmodel",
        "test_fixture",
    ):
        assert any(
            forbidden.lower() in token.lower() for forbidden in FORBIDDEN_EXISTING_PRODUCER_TOKENS
        )
        with pytest.raises(
            RegimeCoverageProducerDecisionErrorV1,
            match="EXISTING_PRODUCER_ELEVATION_FORBIDDEN|FORBIDDEN_SOURCE",
        ):
            validate_regime_coverage_owner_choice_v1(
                AUTHORIZE_OWNER_VALUE,
                claim={"canonical_producer": token},
            )


def test_reject_coverage_counts_and_numeric_invention_v1() -> None:
    with pytest.raises(
        RegimeCoverageProducerDecisionErrorV1, match="COVERAGE_COUNTS_MUST_REMAIN_NULL"
    ):
        validate_regime_coverage_owner_choice_v1(
            AUTHORIZE_OWNER_VALUE,
            claim={"coverage_counts": {"low": 1}},
        )
    with pytest.raises(
        RegimeCoverageProducerDecisionErrorV1,
        match="PRODUCTIVE_NUMERIC_VALUES_MUST_REMAIN_ZERO",
    ):
        validate_regime_coverage_owner_choice_v1(
            REJECT_OWNER_VALUE,
            claim={"productive_numeric_values_set": 3},
        )
    manifest = copy.deepcopy(
        load_canonical_regime_coverage_producer_decisions_manifest_v1(REPO_ROOT)
    )
    manifest["decisions"]["REGIME_COVERAGE_PRODUCER"]["coverage_counts"] = {"low": 12}
    with pytest.raises(
        RegimeCoverageProducerDecisionErrorV1,
        match="INVENTED_NUMERIC_OR_COUNT_FORBIDDEN",
    ):
        validate_regime_coverage_producer_manifest_v1(manifest)


def test_reject_dashboard_authority_and_runtime_authorization_v1() -> None:
    with pytest.raises(
        RegimeCoverageProducerDecisionErrorV1, match="DASHBOARD_AUTHORITY_MUST_BE_NONE"
    ):
        validate_regime_coverage_owner_choice_v1(
            AUTHORIZE_OWNER_VALUE,
            claim={"dashboard_authority_effect": "AUTHORITY"},
        )
    with pytest.raises(RegimeCoverageProducerDecisionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_regime_coverage_owner_choice_v1(
            AUTHORIZE_OWNER_VALUE,
            claim={"input_authority": True},
        )
    with pytest.raises(RegimeCoverageProducerDecisionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_regime_coverage_owner_choice_v1(
            AUTHORIZE_OWNER_VALUE,
            claim={"campaign_start_authorized": True},
        )
    with pytest.raises(RegimeCoverageProducerDecisionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_regime_coverage_owner_choice_v1(
            AUTHORIZE_OWNER_VALUE,
            claim={"raw_input_pack_materialization_authorized": True},
        )


def test_authorize_detail_fields_must_remain_null_on_open_surface_v1() -> None:
    manifest = copy.deepcopy(
        load_canonical_regime_coverage_producer_decisions_manifest_v1(REPO_ROOT)
    )
    manifest["authorize_detail_fields"]["canonical_producer_name"] = "analytics.regimes"
    with pytest.raises(RegimeCoverageProducerDecisionErrorV1, match="MUST_REMAIN_NULL"):
        validate_regime_coverage_producer_manifest_v1(manifest)
    with pytest.raises(RegimeCoverageProducerDecisionErrorV1, match="MUST_REMAIN_NULL"):
        validate_regime_coverage_owner_choice_v1(
            AUTHORIZE_OWNER_VALUE,
            authorize_detail_fields={"canonical_producer_name": "feature_regime_pipeline_v2"},
        )


def test_parent_triad_still_keeps_regime_open_v1() -> None:
    triad = json.loads((REPO_ROOT / PARENT_TRIAD_MANIFEST_REL).read_text(encoding="utf-8"))
    row = next(r for r in triad["owner_decision_table"] if r["decision_id"] == DECISION_ID)
    assert row["status"] == "OPEN"
    assert row["owner_value"] is None
    assert triad["regime_coverage_status"] == "SEMANTICALLY_UNRESOLVED"
    assert triad["regime_coverage_producer_available"] is False
    assert set(ALLOWED_OWNER_VALUES).issubset(set(row["allowed_options"]))
