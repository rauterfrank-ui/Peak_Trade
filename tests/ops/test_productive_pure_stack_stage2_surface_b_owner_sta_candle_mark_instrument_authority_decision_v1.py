"""Owner/STA candle-mark-instrument authority decision surface contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority_decision_v1.constants_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    CAPABILITY_SCOPE,
    DECISIONS_MANIFEST_REL,
    OWNER_DECISION_REL,
    PROPOSED_CANDLE_SOURCE_REF,
    PROPOSED_MARK_SOURCE_REF,
    SCHEMA_REL,
    STATUS_SURFACE_OPEN,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_candle_mark_instrument_authority_decision_v1.validator_v1 import (
    OwnerStaAuthorityDecisionErrorV1,
    load_canonical_owner_sta_decisions_manifest_v1,
    validate_owner_sta_authority_manifest_v1,
    validate_owner_sta_ratification_claim_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_STA_AUTHORITY_DECISION",
    f"CAPABILITY_SCOPE={CAPABILITY_SCOPE}",
    f"STATUS={STATUS_SURFACE_OPEN}",
    f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_ORIGIN_MAIN_SHA}",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "CANDLE_AUTHORITY_RATIFIED=false",
    "MARK_AUTHORITY_RATIFIED=false",
    "INSTRUMENT_BINDING_RATIFIED=false",
    "CAMPAIGN_START_AUTHORIZED=false",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false",
    "RAW_INPUT_PACK_CREATED=false",
    "CAMPAIGN_STARTED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
    "STA_PRODUCER_IS_RAW_SOURCE_AUTHORITY=false",
    "O4_PT1H_AS_PT1M_FORBIDDEN=true",
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "CANDLE_AUTHORITY_RATIFIED=true",
    "MARK_AUTHORITY_RATIFIED=true",
    "INSTRUMENT_BINDING_RATIFIED=true",
    "CAMPAIGN_START_AUTHORIZED=true",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true",
    "NOTION_SSOT=true",
)


def _eth_binding() -> dict[str, str]:
    return {
        "venue": "okx",
        "canonical_instrument_id": "inst-eth-usdt-perp",
        "venue_instrument_id": "ETH-USDT-SWAP",
        "contract_type": "perpetual",
        "market_type": "futures",
        "quote_currency": "USDT",
        "settlement_currency": "USDT",
    }


def test_owner_sta_artifacts_exist_v1() -> None:
    assert (REPO_ROOT / OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / DECISIONS_MANIFEST_REL).is_file()
    assert (REPO_ROOT / SCHEMA_REL).is_file()


def test_owner_sta_document_markers_v1() -> None:
    text = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_DOC_CLAIMS:
        assert claim not in text, claim


def test_canonical_manifest_structure_open_valid_v1() -> None:
    manifest = load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT)
    result = validate_owner_sta_authority_manifest_v1(manifest)
    assert result["ok"] is True
    assert result["input_authority"] is False
    assert result["runtime_implemented"] is False
    assert result["candle_authority_ratified"] is False
    assert result["mark_authority_ratified"] is False
    assert result["instrument_binding_ratified"] is False
    assert result["raw_input_pack_created"] is False
    assert result["campaign_started"] is False
    assert result["productive_numeric_values_set"] == 0
    assert result["regime_coverage_status"] == "SEMANTICALLY_UNRESOLVED"
    assert manifest["candle_source_authority"]["proposed_source_ref"] == PROPOSED_CANDLE_SOURCE_REF
    assert manifest["mark_source_authority"]["proposed_source_ref"] == PROPOSED_MARK_SOURCE_REF
    assert (
        manifest["candle_source_authority"]["proposed_source_ref"]
        != manifest["mark_source_authority"]["proposed_source_ref"]
    )


def test_schema_required_keys_present_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    required = set(schema["required"])
    for key in (
        "candle_authority_ratified",
        "mark_authority_ratified",
        "instrument_binding_ratified",
        "owner_decision_table",
        "regime_coverage_status",
        "open_null_instance_fields",
    ):
        assert key in required


def test_structure_claim_without_ratification_ok_v1() -> None:
    result = validate_owner_sta_ratification_claim_v1(
        {
            "input_authority": False,
            "runtime_implemented": False,
            "candle_authority_ratified": False,
            "mark_authority_ratified": False,
            "instrument_binding_ratified": False,
        },
        owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
    )
    assert result["ok"] is True
    assert result["candle_authority_ratified"] is False


def test_reject_ratification_without_separate_authorities_v1() -> None:
    with pytest.raises(
        OwnerStaAuthorityDecisionErrorV1,
        match="RATIFICATION_REQUIRES_SEPARATE_CANDLE_MARK_AND_COMPLETE_BINDING",
    ):
        validate_owner_sta_ratification_claim_v1(
            {
                "candle_authority_ratified": True,
                "mark_authority_ratified": False,
                "instrument_binding_ratified": True,
                "candle_source_ref": PROPOSED_CANDLE_SOURCE_REF,
                "mark_source_ref": PROPOSED_MARK_SOURCE_REF,
                "instrument_binding": _eth_binding(),
            },
            owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
        )


def test_reject_ratification_missing_mark_source_ref_v1() -> None:
    with pytest.raises(
        OwnerStaAuthorityDecisionErrorV1, match="MARK_SOURCE_REF_REQUIRED_FOR_RATIFICATION"
    ):
        validate_owner_sta_ratification_claim_v1(
            {
                "candle_authority_ratified": True,
                "mark_authority_ratified": True,
                "instrument_binding_ratified": True,
                "candle_source_ref": PROPOSED_CANDLE_SOURCE_REF,
                "mark_source_ref": None,
                "instrument_binding": _eth_binding(),
            },
            owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
        )


def test_reject_identical_candle_mark_source_refs_v1() -> None:
    with pytest.raises(
        OwnerStaAuthorityDecisionErrorV1, match="CANDLE_AND_MARK_SOURCE_REF_MUST_DIFFER"
    ):
        validate_owner_sta_ratification_claim_v1(
            {
                "candle_authority_ratified": True,
                "mark_authority_ratified": True,
                "instrument_binding_ratified": True,
                "candle_source_ref": PROPOSED_CANDLE_SOURCE_REF,
                "mark_source_ref": PROPOSED_CANDLE_SOURCE_REF,
                "instrument_binding": _eth_binding(),
            },
            owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
        )


def test_reject_incomplete_instrument_binding_v1() -> None:
    binding = _eth_binding()
    del binding["settlement_currency"]
    with pytest.raises(
        OwnerStaAuthorityDecisionErrorV1, match="INSTRUMENT_BINDING_INCOMPLETE:settlement_currency"
    ):
        validate_owner_sta_ratification_claim_v1(
            {
                "candle_authority_ratified": True,
                "mark_authority_ratified": True,
                "instrument_binding_ratified": True,
                "candle_source_ref": PROPOSED_CANDLE_SOURCE_REF,
                "mark_source_ref": PROPOSED_MARK_SOURCE_REF,
                "instrument_binding": binding,
            },
            owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
        )


def test_reject_btc_test_binding_v1() -> None:
    binding = _eth_binding()
    binding["canonical_instrument_id"] = "BTC-USDT-SWAP"
    binding["venue_instrument_id"] = "BTC-USDT-SWAP"
    with pytest.raises(OwnerStaAuthorityDecisionErrorV1, match="BTC_TEST_BINDING_FORBIDDEN"):
        validate_owner_sta_ratification_claim_v1(
            {
                "candle_authority_ratified": True,
                "mark_authority_ratified": True,
                "instrument_binding_ratified": True,
                "candle_source_ref": PROPOSED_CANDLE_SOURCE_REF,
                "mark_source_ref": PROPOSED_MARK_SOURCE_REF,
                "instrument_binding": binding,
            },
            owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
        )


def test_reject_previous_candle_close_fallback_v1() -> None:
    with pytest.raises(
        OwnerStaAuthorityDecisionErrorV1, match="PREVIOUS_CANDLE_CLOSE_FALLBACK_FORBIDDEN"
    ):
        validate_owner_sta_ratification_claim_v1(
            {
                "candle_authority_ratified": True,
                "mark_authority_ratified": True,
                "instrument_binding_ratified": True,
                "candle_source_ref": PROPOSED_CANDLE_SOURCE_REF,
                "mark_source_ref": PROPOSED_MARK_SOURCE_REF,
                "instrument_binding": _eth_binding(),
                "previous_candle_close_fallback": True,
            },
            owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
        )


def test_reject_ratification_while_surface_open_even_if_complete_v1() -> None:
    with pytest.raises(
        OwnerStaAuthorityDecisionErrorV1,
        match="OWNER_STA_RATIFICATION_BLOCKED_WHILE_SURFACE_OPEN",
    ):
        validate_owner_sta_ratification_claim_v1(
            {
                "candle_authority_ratified": True,
                "mark_authority_ratified": True,
                "instrument_binding_ratified": True,
                "candle_source_ref": PROPOSED_CANDLE_SOURCE_REF,
                "mark_source_ref": PROPOSED_MARK_SOURCE_REF,
                "instrument_binding": _eth_binding(),
            },
            owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
        )


def test_reject_campaign_start_and_pack_materialization_v1() -> None:
    with pytest.raises(OwnerStaAuthorityDecisionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_owner_sta_ratification_claim_v1(
            {"campaign_start_authorized": True},
            owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
        )
    with pytest.raises(OwnerStaAuthorityDecisionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_owner_sta_ratification_claim_v1(
            {"raw_input_pack_materialization_authorized": True},
            owner_manifest=load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT),
        )


def test_reject_owner_value_mutation_in_structure_open_manifest_v1() -> None:
    manifest = copy.deepcopy(load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT))
    manifest["owner_decision_table"][0]["owner_value"] = PROPOSED_CANDLE_SOURCE_REF
    with pytest.raises(OwnerStaAuthorityDecisionErrorV1, match="MUST_REMAIN_NULL"):
        validate_owner_sta_authority_manifest_v1(manifest)


def test_competing_candidates_documented_and_btc_excluded_v1() -> None:
    manifest = load_canonical_owner_sta_decisions_manifest_v1(REPO_ROOT)
    candidates = manifest["instrument_binding"]["competing_candidates"]
    ids = {c["candidate_id"] for c in candidates}
    assert "CAND_ETH_USDT_SWAP_RESEARCH_STAGING" in ids
    assert "EXCL_BTC_USDT_SWAP_TEST_FIXTURE" in ids
    btc = next(c for c in candidates if c["candidate_id"] == "EXCL_BTC_USDT_SWAP_TEST_FIXTURE")
    assert btc["eligibility"] == "EXCLUDED"
    assert btc["selected"] is False
    assert all(c.get("selected") is False for c in candidates)
