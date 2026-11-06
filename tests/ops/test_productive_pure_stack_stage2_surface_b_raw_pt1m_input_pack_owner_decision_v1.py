"""Owner Decision + fail-closed validator for Surface-B raw PT1M input pack."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_owner_decision_v1.constants_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    CAPABILITY_SCOPE,
    DECISIONS_MANIFEST_REL,
    OWNER_DECISION_REL,
    SCHEMA_REL,
)
from src.ops.productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_owner_decision_v1.validator_v1 import (
    RawInputPackOwnerDecisionErrorV1,
    load_canonical_decisions_manifest_v1,
    validate_candle_mark_instrument_inputs_v1,
    validate_owner_decision_manifest_v1,
    validate_raw_input_pack_campaign_binding_claim_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_BUCKET = 1_700_000_040  # PT1M-aligned bucket open

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_AUTHORITY_DECISION",
    "CAPABILITY_SCOPE=SURFACE_B_RAW_PT1M_CANDLE_MARK_INPUT_PACK_AND_CAMPAIGN_INSTANCE_BINDING",
    "STATUS=OWNER_DECISION_STRUCTURE_RATIFIED_INSTANCE_FIELDS_OPEN",
    f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_ORIGIN_MAIN_SHA}",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "CAMPAIGN_START_AUTHORIZED=false",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "PURGE_VALUE=null",
    "EMBARGO_VALUE=null",
    "FOLD_SIZES_VALUE=null",
    "CANDLE_MARK_TRADE_EQUIVALENCE=FORBIDDEN",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
    "AS_OF_EQUALS_PACK_EXCLUSIVE_TIP=true",
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "CAMPAIGN_START_AUTHORIZED=true",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true",
    "PRODUCTIVE_NUMERIC_VALUES_SET=1",
    "NOTION_SSOT=true",
    "DASHBOARD_AUTHORITY_EFFECT=AUTHORITATIVE",
)


def _binding() -> dict[str, str]:
    return {
        "venue": "okx",
        "canonical_instrument_id": "BTC-USDT-SWAP",
        "venue_instrument_id": "BTC-USDT-SWAP",
        "contract_type": "swap",
        "market_type": "futures",
        "quote_currency": "USDT",
        "settlement_currency": "USDT",
        "binding_mode": "SINGLE_SELECTED_FUTURE_VENUE_NATIVE",
    }


def _candle(*, open_tip: bool = False, finalized: bool = True, close: float = 101.0) -> dict:
    return {
        "event_time_epoch_s": _BUCKET,
        "open": 100.0,
        "high": 102.0,
        "low": 99.0,
        "close": close,
        "volume": 1.0,
        "venue_finalized": finalized,
        "open_tip": open_tip,
    }


def _mark(*, price: float = 100.5) -> dict:
    return {"event_time_epoch_s": _BUCKET, "mark_price": price}


def test_owner_decision_artifacts_exist_v1() -> None:
    assert (REPO_ROOT / OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / DECISIONS_MANIFEST_REL).is_file()
    assert (REPO_ROOT / SCHEMA_REL).is_file()


def test_owner_decision_document_markers_v1() -> None:
    text = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_DOC_CLAIMS:
        assert claim not in text, claim


def test_canonical_manifest_structure_valid_v1() -> None:
    manifest = load_canonical_decisions_manifest_v1(REPO_ROOT)
    result = validate_owner_decision_manifest_v1(manifest)
    assert result["ok"] is True
    assert result["input_authority"] is False
    assert result["runtime_implemented"] is False
    assert result["campaign_start_authorized"] is False
    assert result["raw_input_pack_materialization_authorized"] is False
    assert result["productive_numeric_values_set"] == 0
    assert result["purge"] is None
    assert result["embargo"] is None
    assert result["fold_sizes"] is None
    assert result["notion_ssot"] is False
    assert manifest["capability_scope"] == CAPABILITY_SCOPE
    assert manifest["campaign_instance"]["campaign_id"] is None
    assert manifest["campaign_instance"]["seed"] is None
    assert manifest["campaign_instance"]["candle_authority"]["candles"] is None
    assert manifest["campaign_instance"]["mark_price_authority"]["marks"] is None


def test_schema_required_keys_present_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    required = set(schema["required"])
    for key in (
        "campaign_start_authorized",
        "raw_input_pack_materialization_authorized",
        "input_authority",
        "runtime_implemented",
        "purge",
        "embargo",
        "fold_sizes",
        "campaign_instance",
    ):
        assert key in required


def test_structure_only_binding_claim_ok_v1() -> None:
    manifest = load_canonical_decisions_manifest_v1(REPO_ROOT)
    result = validate_raw_input_pack_campaign_binding_claim_v1(
        {
            "input_authority": False,
            "runtime_implemented": False,
            "productive_numeric_values_set": 0,
            "campaign_start_authorized": False,
            "raw_input_pack_materialization_authorized": False,
        },
        owner_manifest=manifest,
    )
    assert result["ok"] is True
    assert result["campaign_start_authorized"] is False


def test_reject_campaign_start_unauthorized_v1() -> None:
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="CAMPAIGN_START_UNAUTHORIZED"):
        validate_raw_input_pack_campaign_binding_claim_v1(
            {"campaign_start_authorized": True, "input_authority": False}
        )
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="CAMPAIGN_START_UNAUTHORIZED"):
        validate_raw_input_pack_campaign_binding_claim_v1(
            {"start_evidence_collection": True, "input_authority": False}
        )


def test_reject_pack_materialization_unauthorized_v1() -> None:
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="PACK_MATERIALIZATION_UNAUTHORIZED"):
        validate_raw_input_pack_campaign_binding_claim_v1(
            {"raw_input_pack_materialization_authorized": True, "input_authority": False}
        )


def test_reject_missing_candles_v1() -> None:
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="CANDLES_REQUIRED"):
        validate_raw_input_pack_campaign_binding_claim_v1(
            {
                "instrument_binding": _binding(),
                "dataset_id": "ds_open_v1",
                "candles": None,
                "marks": [_mark()],
            }
        )


def test_reject_missing_marks_v1() -> None:
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="MARKS_REQUIRED"):
        validate_candle_mark_instrument_inputs_v1(
            binding_raw=_binding(),
            dataset_id="ds_open_v1",
            candles_raw=[_candle()],
            marks_raw=None,
        )


def test_reject_candle_mark_equivalence_alias_v1() -> None:
    with pytest.raises(
        RawInputPackOwnerDecisionErrorV1, match="CANDLE_MARK_TRADE_EQUIVALENCE_FORBIDDEN"
    ):
        validate_candle_mark_instrument_inputs_v1(
            binding_raw=_binding(),
            dataset_id="ds_open_v1",
            candles_raw=[_candle()],
            marks_raw=[_mark()],
            allow_candle_mark_equivalence=True,
        )


def test_reject_open_tip_candle_v1() -> None:
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="OPEN_TIP_BARS_FORBIDDEN"):
        validate_candle_mark_instrument_inputs_v1(
            binding_raw=_binding(),
            dataset_id="ds_open_v1",
            candles_raw=[_candle(open_tip=True)],
            marks_raw=[_mark()],
        )


def test_reject_unfinalized_candle_v1() -> None:
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="VENUE_CANDLE_NOT_FINALIZED"):
        validate_candle_mark_instrument_inputs_v1(
            binding_raw=_binding(),
            dataset_id="ds_open_v1",
            candles_raw=[_candle(finalized=False)],
            marks_raw=[_mark()],
        )


def test_reject_fixture_and_dashboard_sources_v1() -> None:
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="FORBIDDEN_SOURCE"):
        validate_raw_input_pack_campaign_binding_claim_v1({"source_id": "fixture_pack_v1"})
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="FORBIDDEN_SOURCE"):
        validate_raw_input_pack_campaign_binding_claim_v1(
            {"authority_source": "dashboard_readmodel"}
        )
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="FORBIDDEN_SOURCE"):
        validate_raw_input_pack_campaign_binding_claim_v1({"candle_source": "demo_ohlcv"})


def test_reject_non_venue_native_binding_mode_v1() -> None:
    binding = _binding()
    binding["binding_mode"] = "SYNTHETIC_POOL"
    with pytest.raises(
        RawInputPackOwnerDecisionErrorV1, match="INSTRUMENT_BINDING_NOT_VENUE_NATIVE"
    ):
        validate_candle_mark_instrument_inputs_v1(
            binding_raw=binding,
            dataset_id="ds_open_v1",
            candles_raw=[_candle()],
            marks_raw=[_mark()],
        )


def test_reject_inconsistent_dataset_identity_v1() -> None:
    with pytest.raises(
        RawInputPackOwnerDecisionErrorV1, match="DATASET_CAMPAIGN_IDENTITY_INCONSISTENT"
    ):
        validate_raw_input_pack_campaign_binding_claim_v1(
            {
                "campaign_id": "camp_a",
                "dataset_id": "ds_a",
                "dataset_id_binding": "ds_b",
            }
        )


def test_reject_non_deterministic_seed_v1() -> None:
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="SEED_MUST_BE_INT"):
        validate_raw_input_pack_campaign_binding_claim_v1({"seed": "random"})
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="SEED_REQUIRED"):
        validate_raw_input_pack_campaign_binding_claim_v1({"require_seed": True, "seed": None})


def test_reject_purge_embargo_fold_sizes_set_v1() -> None:
    for payload in (
        {"purge": 60},
        {"embargo": 60},
        {"fold_sizes": {"fold_1": 10}},
        {"purge_seconds": 1},
    ):
        with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="MUST_REMAIN_NULL"):
            validate_raw_input_pack_campaign_binding_claim_v1(payload)


def test_reject_input_authority_or_runtime_flip_v1() -> None:
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="INPUT_AUTHORITY_FLIP"):
        validate_raw_input_pack_campaign_binding_claim_v1({"input_authority": True})
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="RUNTIME_IMPLEMENTED_FLIP"):
        validate_raw_input_pack_campaign_binding_claim_v1({"runtime_implemented": True})


def test_reject_manifest_with_invented_instance_values_v1() -> None:
    manifest = copy.deepcopy(load_canonical_decisions_manifest_v1(REPO_ROOT))
    manifest["campaign_instance"]["campaign_id"] = "invented_campaign"
    with pytest.raises(RawInputPackOwnerDecisionErrorV1, match="MUST_REMAIN_NULL"):
        validate_owner_decision_manifest_v1(manifest)


def test_hygiene_accepts_separate_mark_join_v1() -> None:
    result = validate_candle_mark_instrument_inputs_v1(
        binding_raw=_binding(),
        dataset_id="ds_hygiene_only_v1",
        candles_raw=[_candle(close=101.0)],
        marks_raw=[_mark(price=100.5)],
        event_time_epoch_s=_BUCKET + 60,
    )
    assert result["ok"] is True
    assert result["bar_count"] == 1
    assert result["campaign_start_authorized"] is False
    assert result["raw_input_pack_materialization_authorized"] is False


def test_no_order_tokens_in_new_package_v1() -> None:
    pkg = (
        REPO_ROOT
        / "src/ops/productive_pure_stack_stage2_surface_b_raw_pt1m_input_pack_owner_decision_v1"
    )
    forbidden = (
        "enable_live_trading",
        "submit_order",
        "exchange_credentials",
        "testnet_authorized",
    )
    for path in pkg.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path}:{token}"
