"""Owner/STA raw input-pack materialization decision surface contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1.constants_v1 import (
    ALLOWED_OWNER_VALUES,
    AUTHORIZE_DETAIL_FILLED_FIELD_VALUES,
    AUTHORIZE_DETAIL_PROVABLE_FIELD_VALUES,
    AUTHORIZE_DETAIL_PROVABLE_FIELDS,
    AUTHORIZE_DETAIL_REMAINING_NULL_FIELDS,
    AUTHORIZE_OWNER_VALUE,
    BASELINE_ORIGIN_MAIN_SHA,
    CAPABILITY_SCOPE,
    CLOSED_STA_EXTERNAL_INPUTS,
    CYBERSECURITY_MIRROR_REL,
    DECISION_ID,
    DECISION_PACKET_ENUMERATED_REMAINING_NULL_FIELD_COUNT,
    DECISION_PACKET_ID,
    DECISION_PACKET_REMAINING_NULL_FIELDS,
    DECISION_PACKET_STATUS,
    DECISIONS_MANIFEST_REL,
    FILLED_DATASET_ID,
    FILLED_SCENARIO_ID,
    NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS,
    NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELD_SPECS,
    NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_OWNER_VALUE_FIELDS,
    NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_STA_EXTERNAL_INPUT_FIELDS,
    OPEN_INSTANCE_EXPLICIT_NULL_RATIFIED_FIELDS,
    OPEN_INSTANCE_FILLED_FIELD_VALUES,
    OPEN_INSTANCE_REMAINING_NULL_FIELDS,
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
    REQUIRE_EXPLICIT_OWNER_VALUES_FOR,
    SCHEMA_REL,
    STA_OPEN_EXTERNAL_INPUTS,
    FILLED_OBSERVATION_PACK_DIGEST,
    STATUS_RAW_INPUT_PACK_MATERIALIZED,
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
    f"STATUS={STATUS_RAW_INPUT_PACK_MATERIALIZED}",
    f"DECISION_ID={DECISION_ID}",
    "DECISION_STATUS=RATIFIED",
    f"OWNER_VALUE={RECORDED_OWNER_VALUE}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_ORIGIN_MAIN_SHA}",
    "SCOPE=RAW_INPUT_PACK_MATERIALIZATION_ONLY",
    f"DECISION_PACKET_ID={DECISION_PACKET_ID}",
    "PRODUCER_REIMPLEMENTATION=false",
    "CONSUMER_WIRING=false",
    "PT1M_ADAPTER=false",
    "PACK_MATERIALIZATION=true",
    "CAMPAIGN_START=false",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "CAMPAIGN_START_AUTHORIZED=false",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true",
    "RAW_INPUT_PACK_CREATED=true",
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
    "NON_PROVABLE_INSTANCE_VALUES_STILL_NULL=false",
    "NON_PROVABLE_INSTANCE_VALUES_PARTIALLY_FILLED=true",
    "REQUIRE_EXPLICIT_OWNER_VALUES_FOR_NON_PROVABLE_FIELDS=true",
    "SILENT_DEFAULTS=false",
    "PROPOSED_VALUES=false",
    "INVENTED_VALUES=false",
    f"dataset_id={FILLED_DATASET_ID}",
    f"scenario_id={FILLED_SCENARIO_ID}",
    f"observation_pack_digest={FILLED_OBSERVATION_PACK_DIGEST}",
    "AUTHORIZE_SURFACE_B_RAW_INPUT_PACK_MATERIALIZATION",
    "EXPLICITLY_REJECT_RAW_INPUT_PACK_MATERIALIZATION",
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "CAMPAIGN_START_AUTHORIZED=true",
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
    for key, value in PROVABLE_INSTANCE_FIELD_VALUES["instrument_binding"].items():
        assert f"{key}={value}" in text, key
    for item in STA_OPEN_EXTERNAL_INPUTS:
        assert item in text, item
    for field in NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELDS:
        assert f"`{field}`" in text or f"{field}=" in text, field


def test_canonical_manifest_raw_input_pack_materialized_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    result = validate_raw_input_pack_materialization_manifest_v1(manifest)
    assert result["ok"] is True
    assert result["decision_id"] == DECISION_ID
    assert result["status"] == STATUS_RAW_INPUT_PACK_MATERIALIZED
    assert result["decision_status"] == "RATIFIED"
    assert result["owner_value"] == RECORDED_OWNER_VALUE
    assert result["allowed_owner_values"] == list(ALLOWED_OWNER_VALUES)
    assert result["authorize_detail_provable_refs_closed"] is True
    assert result["authorize_detail_fields_complete"] is False
    assert result["provable_instance_fields_closed"] is True
    assert result["non_provable_instance_values_decision_packet_ready"] is True
    assert result["non_provable_instance_values_still_null"] is False
    assert result["non_provable_instance_values_partially_filled"] is True
    assert result["require_explicit_owner_values_for_non_provable_fields"] is True
    assert result["silent_defaults"] is False
    assert result["proposed_values"] is False
    assert result["invented_values"] is False
    assert result["input_authority"] is False
    assert result["runtime_implemented"] is False
    assert result["raw_input_pack_created"] is True
    assert result["raw_input_pack_materialization_authorized"] is True
    assert result["pack_materialization"] is True
    assert result["campaign_started"] is False
    assert result["productive_numeric_values_set"] == 0
    assert result["dashboard_authority_effect"] == "NONE"
    for field in AUTHORIZE_DETAIL_PROVABLE_FIELDS:
        assert (
            manifest["authorize_detail_fields"][field]
            == AUTHORIZE_DETAIL_PROVABLE_FIELD_VALUES[field]
        )
    for field, expected in AUTHORIZE_DETAIL_FILLED_FIELD_VALUES.items():
        assert manifest["authorize_detail_fields"][field] == expected
    for field in AUTHORIZE_DETAIL_REMAINING_NULL_FIELDS:
        assert manifest["authorize_detail_fields"][field] is None
    for field in PROVABLE_INSTANCE_FIELDS:
        assert manifest["open_null_instance_fields"][field] == PROVABLE_INSTANCE_FIELD_VALUES[field]
    for field, expected in OPEN_INSTANCE_FILLED_FIELD_VALUES.items():
        assert manifest["open_null_instance_fields"][field] == expected
    for field in OPEN_INSTANCE_EXPLICIT_NULL_RATIFIED_FIELDS:
        assert manifest["open_null_instance_fields"][field] is None
    for field in OPEN_INSTANCE_REMAINING_NULL_FIELDS:
        assert manifest["open_null_instance_fields"][field] is None
    assert tuple(manifest["closed_sta_external_inputs"]) == CLOSED_STA_EXTERNAL_INPUTS
    assert tuple(manifest["sta_open_external_inputs"]) == STA_OPEN_EXTERNAL_INPUTS
    assert tuple(manifest["require_explicit_owner_values_for"]) == REQUIRE_EXPLICIT_OWNER_VALUES_FOR
    packet = manifest["non_provable_instance_values_decision_packet"]
    assert packet["packet_id"] == DECISION_PACKET_ID
    assert packet["status"] == DECISION_PACKET_STATUS
    assert (
        packet["enumerated_remaining_null_field_count"]
        == DECISION_PACKET_ENUMERATED_REMAINING_NULL_FIELD_COUNT
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
        expected = NON_PROVABLE_INSTANCE_VALUES_DECISION_PACKET_FIELD_SPECS[row["field"]]
        assert row["status"] == expected["status"]
        assert row["fillable_owner_value"] == expected["fillable_owner_value"]
        assert row["fillable_sta_value"] == expected["fillable_sta_value"]
        assert row["proposed_value"] is None
        assert row["constraints"]
        assert row["provenance_requirements"]
        assert row["allowed_format"]
    remaining = {
        row["field"]
        for row in packet["fields"]
        if row["status"] in {"OPEN_FILLABLE", "EXPLICITLY_LEFT_NULL_BY_OWNER"}
        or row["field"] in DECISION_PACKET_REMAINING_NULL_FIELDS
    }
    assert set(DECISION_PACKET_REMAINING_NULL_FIELDS).issubset(remaining)


def test_schema_allows_raw_input_pack_materialized_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    assert STATUS_RAW_INPUT_PACK_MATERIALIZED in schema["properties"]["status"]["enum"]
    assert "RATIFIED" in schema["properties"]["decision_status"]["enum"]
    assert schema["properties"]["raw_input_pack_materialization_authorized"]["type"] == "boolean"
    assert schema["properties"]["pack_materialization"]["type"] == "boolean"
    packet_schema = schema["properties"]["non_provable_instance_values_decision_packet"]
    assert packet_schema["properties"]["packet_id"]["const"] == DECISION_PACKET_ID
    assert packet_schema["properties"]["proposed_values"]["const"] is False


def test_owner_choice_authorize_keeps_effects_false_v1() -> None:
    from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_decision_v1.constants_v1 import (
        AUTHORIZE_DETAIL_FIELDS,
    )

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
        validate_raw_input_pack_materialization_owner_choice_v1("AUTHORIZE_SOMETHING_ELSE")


def test_manifest_rejects_campaign_start_flip_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    mutated = copy.deepcopy(manifest)
    mutated["campaign_start_authorized"] = True
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_raw_input_pack_materialization_manifest_v1(mutated)


def test_manifest_rejects_pack_materialization_false_after_execution_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    mutated = copy.deepcopy(manifest)
    mutated["pack_materialization"] = False
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1, match="MUST_BE_TRUE"):
        validate_raw_input_pack_materialization_manifest_v1(mutated)


def test_manifest_rejects_dataset_id_drift_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_decisions_manifest_v1(REPO_ROOT)
    mutated = copy.deepcopy(manifest)
    mutated["authorize_detail_fields"]["dataset_id"] = "fixture_demo_dataset"
    with pytest.raises(RawInputPackMaterializationDecisionErrorV1):
        validate_raw_input_pack_materialization_manifest_v1(mutated)
