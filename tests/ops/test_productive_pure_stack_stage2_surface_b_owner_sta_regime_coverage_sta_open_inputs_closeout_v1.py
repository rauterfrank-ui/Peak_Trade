"""Owner/STA regime-coverage STA open-inputs closeout contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout_v1.constants_v1 import (
    CLOSED_INPUTS,
    CYBERSECURITY_MIRROR_REL,
    DECISION_ID,
    DECISIONS_MANIFEST_REL,
    OWNER_DECISION_REL,
    OWNER_GO,
    OWNER_GO_BASE_SHA,
    PARENT_TRIAD_MANIFEST_REL,
    REQUIRED_INSTRUMENT_BINDING_V1,
    SCHEMA_REL,
    STATUS_CLOSEOUT_RATIFIED,
    VERSIONED_PRODUCER_ID,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_regime_coverage_sta_open_inputs_closeout_v1.validator_v1 import (
    RegimeCoverageStaOpenInputsCloseoutErrorV1,
    assert_provable_eth_usdt_swap_compatibility_v1,
    derive_non_invented_coverage_counts_v1,
    load_canonical_sta_open_inputs_closeout_manifest_v1,
    validate_sta_open_inputs_closeout_manifest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT",
    "CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT",
    f"STATUS={STATUS_CLOSEOUT_RATIFIED}",
    f"DECISION_ID={DECISION_ID}",
    "DECISION_STATUS=RATIFIED",
    f"OWNER_GO={OWNER_GO}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    "non_invented_coverage_counts",
    "provable_eth_usdt_swap_compatibility",
    "PRODUCER_REIMPLEMENTATION=false",
    "CONSUMER_WIRING=false",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "ORDERS_AUTHORIZED=false",
    "TESTNET_AUTHORIZED=false",
    "LIVE_AUTHORIZED=false",
    "RUNTIME_AUTHORIZATION_EFFECT=NONE",
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "PRODUCER_REIMPLEMENTATION=true",
    "CONSUMER_WIRING=true",
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=true",
    "ORDERS_AUTHORIZED=true",
    "TESTNET_AUTHORIZED=true",
    "LIVE_AUTHORIZED=true",
)


def _canonical_observations() -> list[dict[str, object]]:
    return [
        {"event_time_epoch_s": 1_700_000_000, "label": "missing", "reason": "UNSET"},
        {"event_time_epoch_s": 1_700_000_060, "label": "unknown", "reason": "INCOMPLETE"},
        {"event_time_epoch_s": 1_700_000_120, "label": "missing", "reason": "UNSET"},
    ]


def test_closeout_artifacts_exist_v1() -> None:
    assert (REPO_ROOT / OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / DECISIONS_MANIFEST_REL).is_file()
    assert (REPO_ROOT / SCHEMA_REL).is_file()
    assert (REPO_ROOT / CYBERSECURITY_MIRROR_REL).is_file()


def test_closeout_document_markers_v1() -> None:
    text = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_DOC_CLAIMS:
        assert claim not in text, claim


def test_canonical_closeout_manifest_validates_v1() -> None:
    manifest = load_canonical_sta_open_inputs_closeout_manifest_v1(REPO_ROOT)
    result = validate_sta_open_inputs_closeout_manifest_v1(manifest)
    assert result["ok"] is True
    assert result["decision_id"] == DECISION_ID
    assert result["owner_go"] == OWNER_GO
    assert result["closed_inputs"] == list(CLOSED_INPUTS)
    assert result["sta_open_external_inputs_remaining"] == []
    assert result["producer_reimplementation"] is False
    assert result["consumer_wiring"] is False
    assert result["input_authority"] is False
    assert result["runtime_implemented"] is False
    assert result["regime_coverage_producer_available"] is False
    assert result["dashboard_authority_effect"] == "NONE"
    assert result["runtime_authorization_effect"] == "NONE"
    assert tuple(manifest["closed_inputs"]) == CLOSED_INPUTS
    assert tuple(manifest["sta_open_external_inputs_remaining"]) == ()


def test_schema_required_keys_and_closed_inputs_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    required = set(schema["required"])
    for key in (
        "closed_inputs",
        "non_invented_coverage_counts",
        "provable_eth_usdt_swap_compatibility",
        "authority_refs",
        "non_effects",
    ):
        assert key in required
    assert schema["properties"]["closed_inputs"]["prefixItems"][0]["const"] == (
        "non_invented_coverage_counts"
    )
    assert schema["properties"]["closed_inputs"]["prefixItems"][1]["const"] == (
        "provable_eth_usdt_swap_compatibility"
    )


def test_derive_non_invented_coverage_counts_positive_v1() -> None:
    counts = derive_non_invented_coverage_counts_v1(
        observations=_canonical_observations(),
        versioned_producer_id=VERSIONED_PRODUCER_ID,
        producer_digest="abc123digest",
        partition_id="partition-a",
        threshold_authority_ref="OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1",
        lookback_authority_ref="OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1",
        caller_supplied_counts={"missing": 2, "unknown": 1},
    )
    assert counts == {"missing": 2, "unknown": 1}


def test_reject_low_mid_high_while_thresholds_unset_v1() -> None:
    with pytest.raises(
        RegimeCoverageStaOpenInputsCloseoutErrorV1,
        match="LOW_MID_HIGH_FORBIDDEN_WHILE_THRESHOLDS_LOOKBACKS_UNSET",
    ):
        derive_non_invented_coverage_counts_v1(
            observations=[
                {"event_time_epoch_s": 1, "label": "low", "reason": "INVENTED"},
            ],
            versioned_producer_id=VERSIONED_PRODUCER_ID,
            producer_digest="digest",
            partition_id="p1",
            threshold_authority_ref="OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1",
            lookback_authority_ref="OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1",
        )


def test_reject_caller_supplied_invented_counts_v1() -> None:
    with pytest.raises(
        RegimeCoverageStaOpenInputsCloseoutErrorV1,
        match="CALLER_SUPPLIED_OR_INVENTED_COUNTS_REJECTED",
    ):
        derive_non_invented_coverage_counts_v1(
            observations=_canonical_observations(),
            versioned_producer_id=VERSIONED_PRODUCER_ID,
            producer_digest="digest",
            partition_id="p1",
            threshold_authority_ref="OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1",
            lookback_authority_ref="OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1",
            caller_supplied_counts={"missing": 99, "unknown": 0},
        )


def test_reject_unauthorized_producer_for_counts_v1() -> None:
    with pytest.raises(
        RegimeCoverageStaOpenInputsCloseoutErrorV1,
        match="UNAUTHORIZED_PRODUCER_FOR_COVERAGE_COUNTS",
    ):
        derive_non_invented_coverage_counts_v1(
            observations=_canonical_observations(),
            versioned_producer_id="analytics.regimes",
            producer_digest="digest",
            partition_id="p1",
            threshold_authority_ref="OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1",
            lookback_authority_ref="OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1",
        )


def test_provable_eth_usdt_swap_compatibility_positive_v1() -> None:
    triad = json.loads((REPO_ROOT / PARENT_TRIAD_MANIFEST_REL).read_text(encoding="utf-8"))
    result = assert_provable_eth_usdt_swap_compatibility_v1(
        instrument_binding=REQUIRED_INSTRUMENT_BINDING_V1,
        triad_manifest=triad,
        candle_join_ref=(
            "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
            "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#candle_source_authority"
        ),
        mark_join_ref=(
            "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
            "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#mark_source_authority"
        ),
        raw_pt1m_pack_ref=(
            "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md"
        ),
    )
    assert result["ok"] is True
    assert result["string_name_similarity_inference"] is False
    assert result["instrument_binding"]["venue_instrument_id"] == "ETH-USDT-SWAP"


def test_reject_string_similarity_and_binding_mismatch_v1() -> None:
    triad = json.loads((REPO_ROOT / PARENT_TRIAD_MANIFEST_REL).read_text(encoding="utf-8"))
    with pytest.raises(
        RegimeCoverageStaOpenInputsCloseoutErrorV1,
        match="STRING_NAME_SIMILARITY_INFERENCE_FORBIDDEN",
    ):
        assert_provable_eth_usdt_swap_compatibility_v1(
            instrument_binding=REQUIRED_INSTRUMENT_BINDING_V1,
            triad_manifest=triad,
            candle_join_ref=(
                "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
                "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#candle_source_authority"
            ),
            mark_join_ref=(
                "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
                "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#mark_source_authority"
            ),
            raw_pt1m_pack_ref=(
                "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_"
                "INPUT_PACK_OWNER_DECISION_V1.md"
            ),
            allow_string_similarity_inference=True,
        )
    bad_binding = dict(REQUIRED_INSTRUMENT_BINDING_V1)
    bad_binding["venue_instrument_id"] = "ETH-USDT"
    with pytest.raises(
        RegimeCoverageStaOpenInputsCloseoutErrorV1,
        match="INSTRUMENT_BINDING_FIELD_MISMATCH",
    ):
        assert_provable_eth_usdt_swap_compatibility_v1(
            instrument_binding=bad_binding,
            triad_manifest=triad,
            candle_join_ref=(
                "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
                "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#candle_source_authority"
            ),
            mark_join_ref=(
                "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
                "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md#mark_source_authority"
            ),
            raw_pt1m_pack_ref=(
                "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_"
                "INPUT_PACK_OWNER_DECISION_V1.md"
            ),
        )


def test_reject_closeout_non_effect_flips_v1() -> None:
    manifest = copy.deepcopy(load_canonical_sta_open_inputs_closeout_manifest_v1(REPO_ROOT))
    manifest["non_effects"]["input_authority"] = True
    with pytest.raises(RegimeCoverageStaOpenInputsCloseoutErrorV1, match="MUST_REMAIN_FALSE"):
        validate_sta_open_inputs_closeout_manifest_v1(manifest)
    manifest = copy.deepcopy(load_canonical_sta_open_inputs_closeout_manifest_v1(REPO_ROOT))
    manifest["closed_inputs"] = ["non_invented_coverage_counts"]
    with pytest.raises(RegimeCoverageStaOpenInputsCloseoutErrorV1, match="CLOSED_INPUTS_MISMATCH"):
        validate_sta_open_inputs_closeout_manifest_v1(manifest)
