"""Owner/STA raw PT1M observation-input and exclusive-tip proof contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_pt1m_observation_input_and_exclusive_tip_proof_v1.constants_v1 import (
    AUTHORIZED_SOURCE_CLASSES,
    CANDLE_AUTHORITY_SOURCE_REF,
    CYBERSECURITY_MIRROR_REL,
    DECISION_ID,
    DECISIONS_MANIFEST_REL,
    EXCLUSIVE_TIP_FORMULA,
    FORBIDDEN_SOURCE_CLASSES,
    MARK_AUTHORITY_SOURCE_REF,
    NUMERIC_PROOF_NULL_FIELDS,
    OWNER_DECISION_REL,
    OWNER_GO,
    OWNER_GO_BASE_SHA,
    OWNER_VALUE,
    REQUIRED_INSTRUMENT_BINDING_V1,
    SCHEMA_REL,
    STATUS_PROOF_CONTRACT_READY_NUMERIC_UNRESOLVED,
    UNRESOLVED_FIELDS,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_pt1m_observation_input_and_exclusive_tip_proof_v1.validator_v1 import (
    ObservationInputExclusiveTipProofErrorV1,
    derive_exclusive_tip_event_time_epoch_s_v1,
    evaluate_observation_input_and_exclusive_tip_proof_v1,
    load_canonical_observation_input_and_exclusive_tip_proof_manifest_v1,
    validate_observation_input_and_exclusive_tip_proof_manifest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF",
    "CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_RAW_PT1M_OBSERVATION_INPUT_AND_EXCLUSIVE_TIP_PROOF",
    f"STATUS={STATUS_PROOF_CONTRACT_READY_NUMERIC_UNRESOLVED}",
    f"DECISION_ID={DECISION_ID}",
    "DECISION_STATUS=RATIFIED",
    f"OWNER_VALUE={OWNER_VALUE}",
    f"OWNER_GO={OWNER_GO}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    "SCOPE=STA_INPUT_PROOF_DOCS_MANIFEST_SCHEMA_VALIDATOR_EVIDENCE_ONLY",
    f"EXCLUSIVE_TIP_FORMULA={EXCLUSIVE_TIP_FORMULA}",
    "DOWNLOAD_OR_NETWORK_FETCH=false",
    "PROOF_CONTRACT_READY=true",
    "STA_EXTERNAL_INPUT_FIELDS_READY=false",
    "OWNER_PARTITION_SELECTION_READY=false",
    "NUMERIC_PROOFS_RESOLVED=false",
    "PACK_MATERIALIZATION=false",
    "RAW_INPUT_PACK_CREATED=false",
    "CAMPAIGN_START=false",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "INVENTED_VALUES=false",
    "SILENT_DEFAULTS=false",
    "PROPOSED_VALUES=false",
    "ORDERS_TESTNET_LIVE=false",
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "DOWNLOAD_OR_NETWORK_FETCH=true",
    "PACK_MATERIALIZATION=true",
    "RAW_INPUT_PACK_CREATED=true",
    "CAMPAIGN_START=true",
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "STA_EXTERNAL_INPUT_FIELDS_READY=true",
    "OWNER_PARTITION_SELECTION_READY=true",
    "NUMERIC_PROOFS_RESOLVED=true",
    "INVENTED_VALUES=true",
    "SILENT_DEFAULTS=true",
    "PROPOSED_VALUES=true",
    "ORDERS_TESTNET_LIVE=true",
)


def _rows(times: list[int]) -> list[dict[str, object]]:
    return [
        {
            "event_time_epoch_s": t,
            "confirm": 1,
            "finalized": True,
            "instrument_binding": dict(REQUIRED_INSTRUMENT_BINDING_V1),
        }
        for t in times
    ]


def test_proof_artifacts_exist_v1() -> None:
    assert (REPO_ROOT / OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / DECISIONS_MANIFEST_REL).is_file()
    assert (REPO_ROOT / SCHEMA_REL).is_file()
    assert (REPO_ROOT / CYBERSECURITY_MIRROR_REL).is_file()


def test_proof_document_markers_v1() -> None:
    text = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_DOC_CLAIMS:
        assert claim not in text, claim


def test_canonical_proof_manifest_validates_v1() -> None:
    manifest = load_canonical_observation_input_and_exclusive_tip_proof_manifest_v1(REPO_ROOT)
    result = validate_observation_input_and_exclusive_tip_proof_manifest_v1(manifest)
    assert result["ok"] is True
    assert result["decision_id"] == DECISION_ID
    assert result["owner_go"] == OWNER_GO
    assert result["proof_contract_ready"] is True
    assert result["sta_external_input_fields_ready"] is False
    assert result["owner_partition_selection_ready"] is False
    assert result["numeric_proofs_resolved"] is False
    assert result["pack_materialization"] is False
    assert result["download_or_network_fetch"] is False
    assert result["unresolved_fields"] == list(UNRESOLVED_FIELDS)
    for field in NUMERIC_PROOF_NULL_FIELDS:
        assert manifest["numeric_proof_slots"][field] is None
    assert manifest["authorized_source_classification"]["authorized_source_classes"] == list(
        AUTHORIZED_SOURCE_CLASSES
    )
    assert manifest["authorized_source_classification"]["forbidden_source_classes"] == list(
        FORBIDDEN_SOURCE_CLASSES
    )


def test_schema_required_keys_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    required = set(schema["required"])
    for key in (
        "authorized_source_classification",
        "numeric_proof_slots",
        "rule_proofs",
        "digest_provenance",
        "unresolved_fields",
        "instrument_binding",
        "exclusive_tip_formula",
    ):
        assert key in required
    assert schema["properties"]["exclusive_tip_formula"]["const"] == EXCLUSIVE_TIP_FORMULA
    assert schema["properties"]["download_or_network_fetch"]["const"] is False


def test_derive_exclusive_tip_formula_v1() -> None:
    assert derive_exclusive_tip_event_time_epoch_s_v1(1_704_067_200) == 1_704_067_260


def test_reject_unaligned_tip_base_v1() -> None:
    with pytest.raises(ObservationInputExclusiveTipProofErrorV1, match="PT1M_ALIGNMENT_FAILED"):
        derive_exclusive_tip_event_time_epoch_s_v1(1_704_067_201)


def test_evaluate_requires_download_authorization_v1() -> None:
    times = [1_704_067_200, 1_704_067_260, 1_704_067_320]
    with pytest.raises(
        ObservationInputExclusiveTipProofErrorV1,
        match="DOWNLOAD_OR_NETWORK_FETCH_NOT_AUTHORIZED",
    ):
        evaluate_observation_input_and_exclusive_tip_proof_v1(
            binding_raw=REQUIRED_INSTRUMENT_BINDING_V1,
            candle_rows=_rows(times),
            mark_rows=_rows(times),
            candle_source_ref=CANDLE_AUTHORITY_SOURCE_REF,
            mark_source_ref=MARK_AUTHORITY_SOURCE_REF,
            download_or_network_fetch_authorized=False,
        )


def test_evaluate_positive_when_authorized_v1() -> None:
    times = [1_704_067_200, 1_704_067_260, 1_704_067_320]
    result = evaluate_observation_input_and_exclusive_tip_proof_v1(
        binding_raw=REQUIRED_INSTRUMENT_BINDING_V1,
        candle_rows=_rows(times),
        mark_rows=_rows(times),
        candle_source_ref=CANDLE_AUTHORITY_SOURCE_REF,
        mark_source_ref=MARK_AUTHORITY_SOURCE_REF,
        download_or_network_fetch_authorized=True,
        observation_pack_bytes=b"obs-pack",
        raw_source_bytes=b"raw-source",
    )
    assert result["ok"] is True
    assert result["candle_row_count"] == 3
    assert result["mark_row_count"] == 3
    assert result["first_finalized_bucket_open_event_time_epoch_s"] == 1_704_067_200
    assert result["last_finalized_bucket_open_event_time_epoch_s"] == 1_704_067_320
    assert result["exclusive_tip_event_time_epoch_s"] == 1_704_067_380
    assert result["pt1m_alignment_proof"] is True
    assert result["candle_mark_join_proof"] is True
    assert result["contiguity_proof"] is True
    assert result["duplicate_free_proof"] is True
    assert result["observation_pack_digest"] is not None
    assert result["raw_source_digest"] is not None
    assert result["pack_materialization"] is False
    assert result["raw_input_pack_created"] is False


def test_reject_candle_mark_join_mismatch_v1() -> None:
    candles = _rows([1_704_067_200, 1_704_067_260])
    marks = _rows([1_704_067_260, 1_704_067_320])
    with pytest.raises(
        ObservationInputExclusiveTipProofErrorV1, match="CANDLE_MARK_BUCKET_JOIN_FAILED"
    ):
        evaluate_observation_input_and_exclusive_tip_proof_v1(
            binding_raw=REQUIRED_INSTRUMENT_BINDING_V1,
            candle_rows=candles,
            mark_rows=marks,
            candle_source_ref=CANDLE_AUTHORITY_SOURCE_REF,
            mark_source_ref=MARK_AUTHORITY_SOURCE_REF,
            download_or_network_fetch_authorized=True,
        )


def test_reject_contiguity_gap_v1() -> None:
    with pytest.raises(ObservationInputExclusiveTipProofErrorV1, match="CONTIGUITY_GAP"):
        evaluate_observation_input_and_exclusive_tip_proof_v1(
            binding_raw=REQUIRED_INSTRUMENT_BINDING_V1,
            candle_rows=_rows([1_704_067_200, 1_704_067_320]),
            mark_rows=_rows([1_704_067_200, 1_704_067_320]),
            candle_source_ref=CANDLE_AUTHORITY_SOURCE_REF,
            mark_source_ref=MARK_AUTHORITY_SOURCE_REF,
            download_or_network_fetch_authorized=True,
        )


def test_reject_non_null_numeric_slot_on_canonical_manifest_v1() -> None:
    manifest = load_canonical_observation_input_and_exclusive_tip_proof_manifest_v1(REPO_ROOT)
    mutated = copy.deepcopy(manifest)
    mutated["numeric_proof_slots"]["exclusive_tip_event_time_epoch_s"] = 1_704_067_380
    with pytest.raises(ObservationInputExclusiveTipProofErrorV1, match="MUST_REMAIN_NULL"):
        validate_observation_input_and_exclusive_tip_proof_manifest_v1(mutated)
