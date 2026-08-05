"""Owner/STA raw input-pack materialization decision surface contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1.constants_v1 import (
    ALLOWED_OWNER_VALUES,
    AUTHORIZE_DETAIL_FIELDS,
    AUTHORIZE_DETAIL_INSTANCE_NULL_FIELDS,
    AUTHORIZE_DETAIL_PROVABLE_FIELD_VALUES,
    AUTHORIZE_DETAIL_PROVABLE_FIELDS,
    AUTHORIZE_OWNER_VALUE,
    BASELINE_ORIGIN_MAIN_SHA,
    CAPABILITY_SCOPE,
    CYBERSECURITY_MIRROR_REL,
    DECISION_ID,
    DECISIONS_MANIFEST_REL,
    OWNER_DECISION_REL,
    OWNER_GO_BASE_SHA,
    PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL,
    PARENT_REGIME_COVERAGE_DECISION_REL,
    PARENT_STA_OPEN_INPUTS_CLOSEOUT_REL,
    PARENT_SURFACE_B_RATIFICATION_REL,
    PARENT_TRIAD_DECISION_REL,
    RECORDED_OWNER_VALUE,
    REJECT_OWNER_VALUE,
    SCHEMA_REL,
    STA_OPEN_EXTERNAL_INPUTS,
    STATUS_AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1.validator_v1 import (
    RawInputPackMaterializationDecisionErrorV1,
    load_canonical_raw_input_pack_materialization_decisions_manifest_v1,
    validate_raw_input_pack_materialization_manifest_v1,
    validate_raw_input_pack_materialization_owner_choice_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_DECISION",
    f"CAPABILITY_SCOPE={CAPABILITY_SCOPE}",
    f"STATUS={STATUS_AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED}",
    f"DECISION_ID={DECISION_ID}",
    "DECISION_STATUS=RATIFIED",
    f"OWNER_VALUE={RECORDED_OWNER_VALUE}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_ORIGIN_MAIN_SHA}",
    "SCOPE=DOCS_MANIFEST_SCHEMA_VALIDATOR_ONLY",
    "PRODUCER_REIMPLEMENTATION=false",
    "CONSUMER_WIRING=false",
    "PT1M_ADAPTER=false",
    "PACK_MATERIALIZATION=false",
    "CAMPAIGN_START=false",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "CAMPAIGN_START_AUTHORIZED=false",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false",
    "RAW_INPUT_PACK_CREATED=false",
    "CAMPAIGN_STARTED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "PRODUCTIVE_THRESHOLDS_LOOKBACKS=false",
    "REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=false",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
    "AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED=true",
    "AUTHORIZE_DETAIL_FIELDS_COMPLETE=false",
    "AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION",
    "EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION",
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "CAMPAIGN_START_AUTHORIZED=true",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true",
    "PACK_MATERIALIZATION=true",
    "NOTION_SSOT=true",
    "DASHBOARD_AUTHORITY_EFFECT=AUTHORITY",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=true",
    "AUTHORIZE_DETAIL_FIELDS_COMPLETE=true",
)


def test_materialization_artifacts_exist_v1() -> None:
    assert (REPO_ROOT / OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / DECISIONS_MANIFEST_REL).is_file()
    assert (REPO_ROOT / SCHEMA_REL).is_file()
    assert (REPO_ROOT / CYBERSECURITY_MIRROR_REL).is_file()
    assert (REPO_ROOT / PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / PARENT_TRIAD_DECISION_REL).is_file()
    assert (REPO_ROOT / PARENT_REGIME_COVERAGE_DECISION_REL).is_file()
    assert (REPO_ROOT / PARENT_STA_OPEN_INPUTS_CLOSEOUT_REL).is_file()
    assert (REPO_ROOT / PARENT_SURFACE_B_RATIFICATION_REL).is_file()


def test_materialization_document_markers_v1() -> None:
    text = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_DOC_CLAIMS:
        assert claim not in text, claim
    for field, value in AUTHORIZE_DETAIL_PROVABLE_FIELD_VALUES.items():
        assert f"{field}={value}" in text, field
    for field in AUTHORIZE_DETAIL_INSTANCE_NULL_FIELDS:
        assert f"{field}=null" in text, field
    for item in STA_OPEN_EXTERNAL_INPUTS:
        assert item in text, item


def test_canonical_manifest_provable_refs_closed_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    result = validate_raw_input_pack_materialization_manifest_v1(manifest)
    assert result["ok"] is True
    assert result["decision_id"] == DECISION_ID
    assert result["status"] == STATUS_AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED
    assert result["decision_status"] == "RATIFIED"
    assert result["owner_value"] == RECORDED_OWNER_VALUE
    assert result["allowed_owner_values"] == list(ALLOWED_OWNER_VALUES)
    assert result["authorize_detail_provable_refs_closed"] is True
    assert result["authorize_detail_fields_complete"] is False
    assert result["input_authority"] is False
    assert result["runtime_implemented"] is False
    assert result["raw_input_pack_created"] is False
    assert result["raw_input_pack_materialization_authorized"] is False
    assert result["pack_materialization"] is False
    assert result["campaign_started"] is False
    assert result["productive_numeric_values_set"] == 0
    assert result["dashboard_authority_effect"] == "NONE"
    for field in AUTHORIZE_DETAIL_PROVABLE_FIELDS:
        assert (
            manifest["authorize_detail_fields"][field]
            == AUTHORIZE_DETAIL_PROVABLE_FIELD_VALUES[field]
        )
    for field in AUTHORIZE_DETAIL_INSTANCE_NULL_FIELDS:
        assert manifest["authorize_detail_fields"][field] is None


def test_schema_allows_provable_refs_closed_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    assert STATUS_AUTHORIZE_DETAIL_PROVABLE_REFS_CLOSED in schema["properties"]["status"]["enum"]
    assert "RATIFIED" in schema["properties"]["decision_status"]["enum"]
    assert schema["properties"]["raw_input_pack_materialization_authorized"]["const"] is False
    assert schema["properties"]["pack_materialization"]["const"] is False


def test_owner_choice_authorize_keeps_effects_false_v1() -> None:
    result = validate_raw_input_pack_materialization_owner_choice_v1(
        AUTHORIZE_OWNER_VALUE,
        authorize_detail_fields={field: None for field in AUTHORIZE_DETAIL_FIELDS},
        claim={
            "input_authority": False,
            "runtime_implemented": False,
            "raw_input_pack_created": False,
            "raw_input_pack_materialization_authorized": False,
            "pack_materialization": False,
            "campaign_started": False,
            "campaign_start_authorized": False,
            "dashboard_authority_effect": "NONE",
            "productive_numeric_values_set": 0,
        },
    )
    assert result["ok"] is True
    assert result["owner_value"] == AUTHORIZE_OWNER_VALUE
    assert result["pack_materialization"] is False
    assert result["raw_input_pack_materialization_authorized"] is False


def test_owner_choice_reject_v1() -> None:
    result = validate_raw_input_pack_materialization_owner_choice_v1(REJECT_OWNER_VALUE)
    assert result["ok"] is True
    assert result["owner_value"] == REJECT_OWNER_VALUE


def test_owner_choice_rejects_foreign_value_v1() -> None:
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1, match="OWNER_VALUE_NOT_ALLOWED"):
        validate_raw_input_pack_materialization_owner_choice_v1("AUTHORIZE_ANYTHING")


def test_manifest_rejects_materialization_flip_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(manifest)
    bad["pack_materialization"] = True
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_raw_input_pack_materialization_manifest_v1(bad)


def test_manifest_rejects_authorization_flip_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(manifest)
    bad["raw_input_pack_materialization_authorized"] = True
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_raw_input_pack_materialization_manifest_v1(bad)


def test_manifest_rejects_invented_instance_detail_field_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(manifest)
    bad["authorize_detail_fields"]["campaign_id"] = "invented-campaign"
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1, match="MUST_REMAIN_NULL"):
        validate_raw_input_pack_materialization_manifest_v1(bad)


def test_manifest_rejects_non_exact_provable_ref_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(manifest)
    bad["authorize_detail_fields"]["candle_authority_source_ref"] = "venue://invented/source"
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1, match="VALUE_MISMATCH"):
        validate_raw_input_pack_materialization_manifest_v1(bad)


def test_manifest_rejects_fixture_source_token_in_forbidden_list_gap_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(manifest)
    bad["forbidden_sources"] = [t for t in bad["forbidden_sources"] if t != "fixture"]
    with pytest.raises(
        RawInputPackMaterializationDecisionErrorV1, match="FORBIDDEN_SOURCE_TOKEN_MISSING"
    ):
        validate_raw_input_pack_materialization_manifest_v1(bad)
