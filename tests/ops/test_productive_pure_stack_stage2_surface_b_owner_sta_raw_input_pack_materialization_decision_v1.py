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
    CLOSED_STA_EXTERNAL_INPUTS,
    CYBERSECURITY_MIRROR_REL,
    DECISION_ID,
    DECISION_PACKET_ID,
    DECISIONS_MANIFEST_REL,
    NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS,
    NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_OWNER_VALUE_FIELDS,
    NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_STA_EXTERNAL_INPUT_FIELDS,
    OWNER_DECISION_REL,
    OWNER_GO_BASE_SHA,
    PARENT_RAW_INPUT_PACK_OWNER_DECISION_REL,
    PARENT_REGIME_COVERAGE_DECISION_REL,
    PARENT_STA_OPEN_INPUTS_CLOSEOUT_REL,
    PARENT_SURFACE_B_RATIFICATION_REL,
    PARENT_TRIAD_DECISION_REL,
    PROVABLE_INSTANCE_FIELD_VALUES,
    PROVABLE_INSTANCE_FIELDS,
    RECORDED_OWNER_VALUE,
    REJECT_OWNER_VALUE,
    REMAINING_NULL_INSTANCE_KEYS,
    REQUIRE_EXPLICIT_OWNER_VALUES_FOR,
    SCHEMA_REL,
    STA_OPEN_EXTERNAL_INPUTS,
    STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY,
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
    f"STATUS={STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY}",
    f"DECISION_ID={DECISION_ID}",
    "DECISION_STATUS=RATIFIED",
    f"OWNER_VALUE={RECORDED_OWNER_VALUE}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_ORIGIN_MAIN_SHA}",
    "SCOPE=DOCS_MANIFEST_SCHEMA_VALIDATOR_ONLY",
    f"DECISION_PACKET_ID={DECISION_PACKET_ID}",
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
    "PROVABLE_INSTANCE_FIELDS_CLOSED=true",
    "NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY=true",
    "NON_PROVABLE_INSTANCE_VALUES_STILL_NULL=true",
    "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true",
    "SILENT_DEFAULTS=false",
    "PROPOSED_VALUES=false",
    "INVENTED_VALUES=false",
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
    "PROPOSED_VALUES=true",
    "INVENTED_VALUES=true",
    "SILENT_DEFAULTS=true",
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
    for key, value in PROVABLE_INSTANCE_FIELD_VALUES["instrument_binding"].items():
        assert f"{key}={value}" in text, key
    for item in STA_OPEN_EXTERNAL_INPUTS:
        assert item in text, item
    for item in CLOSED_STA_EXTERNAL_INPUTS:
        assert item in text, item
    for field in NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS:
        assert f"`{field}`" in text, field


def test_canonical_manifest_decision_packet_ready_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    result = validate_raw_input_pack_materialization_manifest_v1(manifest)
    assert result["ok"] is True
    assert result["decision_id"] == DECISION_ID
    assert result["status"] == STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY
    assert result["decision_status"] == "RATIFIED"
    assert result["owner_value"] == RECORDED_OWNER_VALUE
    assert result["allowed_owner_values"] == list(ALLOWED_OWNER_VALUES)
    assert result["authorize_detail_provable_refs_closed"] is True
    assert result["authorize_detail_fields_complete"] is False
    assert result["provable_instance_fields_closed"] is True
    assert result["non_provable_instance_values_decision_packet_ready"] is True
    assert result["non_provable_instance_values_still_null"] is True
    assert result["require_explicit_owner_values_for_non_provable_fields"] is True
    assert result["silent_defaults"] is False
    assert result["proposed_values"] is False
    assert result["invented_values"] is False
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
    for field in PROVABLE_INSTANCE_FIELDS:
        assert manifest["open_null_instance_fields"][field] == PROVABLE_INSTANCE_FIELD_VALUES[field]
    for field in REMAINING_NULL_INSTANCE_KEYS:
        assert manifest["open_null_instance_fields"][field] is None
    assert tuple(manifest["closed_sta_external_inputs"]) == CLOSED_STA_EXTERNAL_INPUTS
    assert tuple(manifest["sta_open_external_inputs"]) == STA_OPEN_EXTERNAL_INPUTS
    assert tuple(manifest["require_explicit_owner_values_for"]) == REQUIRE_EXPLICIT_OWNER_VALUES_FOR
    packet = manifest["non_provable_instance_values_decision_packet"]
    assert packet["packet_id"] == DECISION_PACKET_ID
    assert packet["enumerated_remaining_null_field_count"] == len(
        NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS
    )
    fields = [row["field"] for row in packet["fields"]]
    assert tuple(fields) == NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS
    owner_fields = {row["field"] for row in packet["fields"] if row["input_class"] == "OWNER_VALUE"}
    sta_fields = {
        row["field"] for row in packet["fields"] if row["input_class"] == "STA_EXTERNAL_INPUT"
    }
    assert owner_fields == set(NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_OWNER_VALUE_FIELDS)
    assert sta_fields == set(NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_STA_EXTERNAL_INPUT_FIELDS)
    for row in packet["fields"]:
        assert row["fillable_owner_value"] is None
        assert row["fillable_sta_value"] is None
        assert row["proposed_value"] is None
        assert row["status"] == "OPEN_FILLABLE"
        assert row["constraints"]
        assert row["provenance_requirements"]
        assert row["allowed_format"]


def test_schema_allows_decision_packet_ready_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    assert (
        STATUS_NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_READY
        in schema["properties"]["status"]["enum"]
    )
    assert "RATIFIED" in schema["properties"]["decision_status"]["enum"]
    assert schema["properties"]["raw_input_pack_materialization_authorized"]["const"] is False
    assert schema["properties"]["pack_materialization"]["const"] is False
    packet_schema = schema["properties"]["non_provable_instance_values_decision_packet"]
    assert packet_schema["properties"]["packet_id"]["const"] == DECISION_PACKET_ID
    assert packet_schema["properties"]["proposed_values"]["const"] is False


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


def test_manifest_rejects_non_exact_instrument_binding_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(manifest)
    bad["open_null_instance_fields"]["instrument_binding"] = {
        **PROVABLE_INSTANCE_FIELD_VALUES["instrument_binding"],
        "venue_instrument_id": "BTC-USDT-SWAP",
    }
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1, match="VALUE_MISMATCH"):
        validate_raw_input_pack_materialization_manifest_v1(bad)


def test_manifest_rejects_silent_default_seed_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(manifest)
    bad["open_null_instance_fields"]["seed"] = 0
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1, match="MUST_REMAIN_NULL"):
        validate_raw_input_pack_materialization_manifest_v1(bad)


def test_manifest_rejects_proposed_packet_value_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(manifest)
    bad["non_provable_instance_values_decision_packet"]["fields"][0]["fillable_owner_value"] = (
        "proposed-campaign"
    )
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
