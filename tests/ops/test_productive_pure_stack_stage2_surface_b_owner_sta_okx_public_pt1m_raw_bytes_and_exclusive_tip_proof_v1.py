"""Owner/STA OKX public PT1M raw-bytes and exclusive-tip proof contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1.constants_v1 import (
    ARTIFACTS_REL,
    AUTHORIZED_SOURCE_CLASSES,
    CANDLE_AUTHORITY_SOURCE_REF,
    CANDLE_RAW_REL,
    CYBERSECURITY_MIRROR_REL,
    DECISION_ID,
    DECISIONS_MANIFEST_REL,
    EXCLUSIVE_TIP_FORMULA,
    FORBIDDEN_SOURCE_CLASSES,
    MARK_AUTHORITY_SOURCE_REF,
    MARK_RAW_REL,
    OWNER_DECISION_REL,
    OWNER_GO,
    OWNER_GO_BASE_SHA,
    OWNER_VALUE,
    RAW_SOURCE_CONCAT_REL,
    REQUIRED_INSTRUMENT_BINDING_V1,
    SCHEMA_REL,
    SEALED_CANDLE_RAW_DIGEST,
    SEALED_EXCLUSIVE_TIP_EVENT_TIME_EPOCH_S,
    SEALED_MARK_RAW_DIGEST,
    SEALED_RAW_SOURCE_DIGEST,
    STATUS_NUMERIC_TIP_PROOF_RESOLVED,
    UNRESOLVED_FIELDS,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1.validator_v1 import (
    OkxPublicPt1mRawBytesExclusiveTipProofErrorV1,
    derive_exclusive_tip_from_last_common_bucket_open_v1,
    evaluate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1,
    load_canonical_okx_public_pt1m_raw_bytes_tip_proof_manifest_v1,
    load_sealed_raw_bytes_v1,
    validate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_manifest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF",
    "CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_OKX_PUBLIC_PT1M_RAW_BYTES_AND_EXCLUSIVE_TIP_PROOF",
    f"STATUS={STATUS_NUMERIC_TIP_PROOF_RESOLVED}",
    f"DECISION_ID={DECISION_ID}",
    "DECISION_STATUS=RATIFIED",
    f"OWNER_VALUE={OWNER_VALUE}",
    f"OWNER_GO={OWNER_GO}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    "SCOPE=STA_AUTHORIZED_DOWNLOAD_RAW_BYTES_DIGEST_AND_NUMERIC_PROOF_ONLY",
    f"EXCLUSIVE_TIP_FORMULA={EXCLUSIVE_TIP_FORMULA}",
    "AUTHORIZED_NETWORK_FETCH=true",
    "DOWNLOAD_OR_NETWORK_FETCH=true",
    "PROOF_CONTRACT_READY=true",
    "STA_EXTERNAL_INPUT_FIELDS_READY=true",
    "OWNER_PARTITION_SELECTION_READY=false",
    "NUMERIC_PROOFS_RESOLVED=true",
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
    "WALLCLOCK_AS_DATA_AUTHORITY=false",
    "ORDERS_TESTNET_LIVE=false",
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "PACK_MATERIALIZATION=true",
    "RAW_INPUT_PACK_CREATED=true",
    "CAMPAIGN_START=true",
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "OWNER_PARTITION_SELECTION_READY=true",
    "INVENTED_VALUES=true",
    "SILENT_DEFAULTS=true",
    "PROPOSED_VALUES=true",
    "ORDERS_TESTNET_LIVE=true",
    "WALLCLOCK_AS_DATA_AUTHORITY=true",
)


def test_proof_artifacts_exist_v1() -> None:
    assert (REPO_ROOT / OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / DECISIONS_MANIFEST_REL).is_file()
    assert (REPO_ROOT / SCHEMA_REL).is_file()
    assert (REPO_ROOT / CYBERSECURITY_MIRROR_REL).is_file()
    assert (REPO_ROOT / CANDLE_RAW_REL).is_file()
    assert (REPO_ROOT / MARK_RAW_REL).is_file()
    assert (REPO_ROOT / RAW_SOURCE_CONCAT_REL).is_file()
    assert (REPO_ROOT / ARTIFACTS_REL / "numeric_tip_proof.json").is_file()


def test_proof_document_markers_v1() -> None:
    text = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_DOC_CLAIMS:
        assert claim not in text, claim


def test_canonical_proof_manifest_validates_v1() -> None:
    manifest = load_canonical_okx_public_pt1m_raw_bytes_tip_proof_manifest_v1(REPO_ROOT)
    result = validate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_manifest_v1(
        manifest, repo_root=REPO_ROOT
    )
    assert result["ok"] is True
    assert result["decision_id"] == DECISION_ID
    assert result["owner_go"] == OWNER_GO
    assert result["sta_external_input_fields_ready"] is True
    assert result["owner_partition_selection_ready"] is False
    assert result["numeric_proofs_resolved"] is True
    assert result["exclusive_tip_event_time_epoch_s"] == SEALED_EXCLUSIVE_TIP_EVENT_TIME_EPOCH_S
    assert result["raw_source_digest"] == SEALED_RAW_SOURCE_DIGEST
    assert result["unresolved_fields"] == list(UNRESOLVED_FIELDS)
    assert result["pack_materialization"] is False
    assert result["authorized_network_fetch"] is True


def test_schema_const_surface_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    assert schema["properties"]["owner_go"]["const"] == OWNER_GO
    assert schema["properties"]["exclusive_tip_formula"]["const"] == EXCLUSIVE_TIP_FORMULA
    assert schema["properties"]["authorized_network_fetch"]["const"] is True
    assert schema["properties"]["numeric_proofs_resolved"]["const"] is True
    assert (
        schema["properties"]["numeric_proof_slots"]["properties"][
            "exclusive_tip_event_time_epoch_s"
        ]["const"]
        == SEALED_EXCLUSIVE_TIP_EVENT_TIME_EPOCH_S
    )


def test_derive_exclusive_tip_formula_v1() -> None:
    assert derive_exclusive_tip_from_last_common_bucket_open_v1(1_785_934_620) == 1_785_934_680
    with pytest.raises(OkxPublicPt1mRawBytesExclusiveTipProofErrorV1):
        derive_exclusive_tip_from_last_common_bucket_open_v1(1_785_934_621)


def test_sealed_raw_bytes_evaluate_v1() -> None:
    candle, mark, _concat = load_sealed_raw_bytes_v1(REPO_ROOT)
    result = evaluate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1(
        candle_raw_bytes=candle,
        mark_raw_bytes=mark,
        binding_raw=REQUIRED_INSTRUMENT_BINDING_V1,
        authorized_network_fetch=True,
    )
    assert result["ok"] is True
    assert result["candle_raw_digest"] == SEALED_CANDLE_RAW_DIGEST
    assert result["mark_raw_digest"] == SEALED_MARK_RAW_DIGEST
    assert result["raw_source_digest"] == SEALED_RAW_SOURCE_DIGEST
    assert result["exclusive_tip_event_time_epoch_s"] == SEALED_EXCLUSIVE_TIP_EVENT_TIME_EPOCH_S
    assert result["candle_row_count"] == 299
    assert result["mark_row_count"] == 299
    assert result["authorized_source_classification"] == list(AUTHORIZED_SOURCE_CLASSES)
    assert set(FORBIDDEN_SOURCE_CLASSES).isdisjoint(set(AUTHORIZED_SOURCE_CLASSES))
    assert result["pack_materialization"] is False


def test_evaluate_requires_authorized_fetch_flag_v1() -> None:
    candle, mark, _ = load_sealed_raw_bytes_v1(REPO_ROOT)
    with pytest.raises(OkxPublicPt1mRawBytesExclusiveTipProofErrorV1):
        evaluate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_v1(
            candle_raw_bytes=candle,
            mark_raw_bytes=mark,
            binding_raw=REQUIRED_INSTRUMENT_BINDING_V1,
            authorized_network_fetch=False,
        )


def test_source_refs_match_authorized_classes_v1() -> None:
    assert "history-candles" in CANDLE_AUTHORITY_SOURCE_REF
    assert "history-mark-price-candles" in MARK_AUTHORITY_SOURCE_REF
    assert CANDLE_AUTHORITY_SOURCE_REF != MARK_AUTHORITY_SOURCE_REF


def test_manifest_rejects_pack_materialization_flip_v1() -> None:
    manifest = load_canonical_okx_public_pt1m_raw_bytes_tip_proof_manifest_v1(REPO_ROOT)
    mutated = copy.deepcopy(manifest)
    mutated["non_effects"]["pack_materialization"] = True
    with pytest.raises(OkxPublicPt1mRawBytesExclusiveTipProofErrorV1):
        validate_okx_public_pt1m_raw_bytes_and_exclusive_tip_proof_manifest_v1(
            mutated, repo_root=REPO_ROOT
        )
