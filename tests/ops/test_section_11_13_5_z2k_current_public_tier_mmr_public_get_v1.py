"""§11.13.5.Z2K current public-tier MMR GET evidence.

Code contract plus docs/governance invariants. Does not authorize Live,
Testnet, orders, funding, scaling, or Multi-Future. Does not instantiate
COVER_USDC or a numeric MM_LIQ_BUFFER.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    REUSED_BINDING_REST_HOST,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_public_tier_mmr_productive_evidence_v1 import (
    AUTHORIZED_SCOPE,
    CANARY_INST_FAMILY,
    COVER_USDC_STATUS,
    CoverUsdcCurrentPublicTierMmrEvidenceError,
    MM_LIQ_BUFFER_NUMERIC_STATUS,
    MMR_TERM_STATUS,
    NEXT_CANONICAL_POINTER,
    OWNER_GO,
    POSITION_TIERS_QUERY_PATH,
    PUBLIC_MMR_CLASSIFICATION,
    adjudicate_current_public_tier_mmr_public_get_v1,
    classify_current_public_tier_mmr_evidence_surface_v1,
    collect_current_public_tier_mmr_public_get_v1,
    encode_fixture_position_tiers_payload_v1,
    extract_qty_one_mmr_from_public_position_tiers_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.governance_state_matrix_v1 import (
    NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
CANARY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_V1.md"
)
Z2K_HEADING = "### 11.13.5.Z2K Current public-tier MMR public GET evidence"
OBSERVED_MMR = "0.01"
OBSERVED_IMR = "0.02"

CURRENT_MMR = "0.012"
CURRENT_IMR = "0.02"
CURRENT_TIER = "1"
CURRENT_MIN_SZ = "0"
CURRENT_MAX_SZ = "25000"
RECEIVE_TS = "1787088001.25"

_ADJ_KWARGS = {
    "mmr_public_tier_qty_one_current_value": CURRENT_MMR,
    "imr_public_tier_qty_one_observed": CURRENT_IMR,
    "tier_current_value": CURRENT_TIER,
    "min_sz_current_value": CURRENT_MIN_SZ,
    "max_sz_current_value": CURRENT_MAX_SZ,
    "receive_ts_unix": RECEIVE_TS,
    "instrument_id": DEFAULT_INSTRUMENT_ID,
    "inst_family": CANARY_INST_FAMILY,
    "host": REUSED_BINDING_REST_HOST,
    "endpoint": POSITION_TIERS_QUERY_PATH,
    "http_status": 200,
    "okx_code": "0",
    "get_request_count": 1,
    "post_count": 0,
    "owner_go": OWNER_GO,
}


def _adjudicate(**overrides: object):
    kwargs = dict(_ADJ_KWARGS)
    kwargs.update(overrides)
    return adjudicate_current_public_tier_mmr_public_get_v1(**kwargs)


def test_classification_is_public_readonly_position_tiers_not_ticker() -> None:
    surface = classify_current_public_tier_mmr_evidence_surface_v1()
    assert surface["METHOD"] == "GET"
    assert surface["AUTHENTICATION_REQUIREMENT"] == "NONE_PUBLIC"
    assert surface["READ_ONLY"] is True
    assert surface["ENDPOINT"] == POSITION_TIERS_QUERY_PATH
    assert "position-tiers" in surface["ENDPOINT"]
    assert "ticker" not in surface["ENDPOINT"]
    assert "mark-price" not in surface["ENDPOINT"]
    assert "MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE_OBSERVATIONAL" in surface["TERM_CAN_INSTANTIATE"]
    assert "COVER_USDC" in surface["TERM_CANNOT_PROVE"]
    assert "MM_LIQ_BUFFER_NUMERIC" in surface["TERM_CANNOT_PROVE"]
    assert "ACCOUNT_EFFECTIVE_MMR" in surface["TERM_CANNOT_PROVE"]


def test_extract_selects_unique_qty_one_tier() -> None:
    body = encode_fixture_position_tiers_payload_v1(
        inst_family=CANARY_INST_FAMILY,
        qty_one_mmr=CURRENT_MMR,
        extra_rows=[
            {
                "instId": "",
                "instFamily": CANARY_INST_FAMILY,
                "tier": "2",
                "minSz": "25001",
                "maxSz": "50000",
                "imr": "0.025",
                "mmr": "0.015",
            }
        ],
    )
    payload = json.loads(body.decode("utf-8"))
    mmr, imr, tier, min_sz, max_sz, family = (
        extract_qty_one_mmr_from_public_position_tiers_payload_v1(
            payload,
            expected_inst_family=CANARY_INST_FAMILY,
        )
    )
    assert mmr == CURRENT_MMR
    assert imr == CURRENT_IMR
    assert tier == CURRENT_TIER
    assert min_sz == CURRENT_MIN_SZ
    assert max_sz == CURRENT_MAX_SZ
    assert family == CANARY_INST_FAMILY


def test_extract_rejects_missing_mmr() -> None:
    payload = {
        "code": "0",
        "data": [
            {
                "instFamily": CANARY_INST_FAMILY,
                "tier": "1",
                "minSz": "0",
                "maxSz": "25000",
                "imr": CURRENT_IMR,
            }
        ],
    }
    with pytest.raises(CoverUsdcCurrentPublicTierMmrEvidenceError, match="mmr"):
        extract_qty_one_mmr_from_public_position_tiers_payload_v1(
            payload,
            expected_inst_family=CANARY_INST_FAMILY,
        )


def test_extract_rejects_non_unique_qty_one_tier() -> None:
    payload = {
        "code": "0",
        "data": [
            {
                "instFamily": CANARY_INST_FAMILY,
                "tier": "1",
                "minSz": "0",
                "maxSz": "1",
                "imr": "0.02",
                "mmr": "0.01",
            },
            {
                "instFamily": CANARY_INST_FAMILY,
                "tier": "1b",
                "minSz": "1",
                "maxSz": "2",
                "imr": "0.02",
                "mmr": "0.011",
            },
        ],
    }
    with pytest.raises(CoverUsdcCurrentPublicTierMmrEvidenceError, match="QTY_ONE_TIER_NOT_UNIQUE"):
        extract_qty_one_mmr_from_public_position_tiers_payload_v1(
            payload,
            expected_inst_family=CANARY_INST_FAMILY,
        )


def test_adjudication_is_observational_and_leaves_cover_usdc_uninstantiated() -> None:
    bound = _adjudicate()
    assert bound.mmr_term_status == MMR_TERM_STATUS
    assert bound.mmr_public_tier_qty_one_current_value == CURRENT_MMR
    assert bound.mm_liq_buffer_numeric_status == MM_LIQ_BUFFER_NUMERIC_STATUS
    assert bound.public_mmr_classification == PUBLIC_MMR_CLASSIFICATION
    assert bound.public_mmr_is_not_liquidation_price_evidence is True
    assert bound.cover_usdc_status == COVER_USDC_STATUS
    assert bound.numeric_funding_amount_produced is False
    assert bound.markpx_term_status == "OBSERVED_NOT_NORMATIVELY_BOUND"
    assert bound.bid_ask_term_status == "OBSERVED_NOT_NORMATIVELY_BOUND"
    assert bound.slippage_reserve_numeric_status == "UNINSTANTIATED"
    assert bound.monetary_base_status == "UNPROVEN"
    assert bound.fx_status == "UNPROVEN"
    assert bound.rounding_status == "UNPROVEN"
    assert bound.get_request_count == 1
    assert bound.post_count == 0
    assert bound.live_authorized is False
    assert bound.next_canonical_pointer == NEXT_CANONICAL_POINTER
    assert bound.provider_ts_ms == "NONE_NOT_IN_POSITION_TIERS_PAYLOAD"


@pytest.mark.parametrize(
    "kwargs,needle",
    [
        ({"substitute_historical_mmr": True}, "HISTORICAL_MMR_IS_NOT_CURRENT"),
        (
            {"instantiate_mm_liq_buffer_numeric": True},
            "MM_LIQ_BUFFER_NUMERIC_REMAINS_UNINSTANTIATED",
        ),
        ({"treat_as_account_effective_mmr": True}, "PUBLIC_MMR_IS_NOT_ACCOUNT_EFFECTIVE"),
        (
            {"treat_as_liquidation_price": True},
            "PUBLIC_MMR_IS_NOT_LIQUIDATION_PRICE_EVIDENCE",
        ),
        ({"instantiate_cover_usdc": True}, "COVER_USDC_REMAINS_UNINSTANTIATED"),
        ({"invent_monetary_base": True}, "MONETARY_BASE_REMAINS_UNPROVEN"),
        ({"apply_usd_usdc_conversion": True}, "USD_USDC_CONVERSION_UNPROVEN"),
        ({"assume_usd_equals_usdc": True}, "USD_USDC_CONVERSION_UNPROVEN"),
        ({"apply_rounding": True}, "USDC_ROUNDING_PRECISION_UNPROVEN"),
        ({"produce_numeric_funding_amount": True}, "NUMERIC_FUNDING_AMOUNT_REMAINS_UNPROVEN"),
        ({"collect_ticker": True}, "TICKER_NOT_IN_THIS_GET_SCOPE"),
        ({"collect_mark_price": True}, "MARK_PRICE_NOT_IN_THIS_GET_SCOPE"),
        ({"live_authorized": True}, "LIVE_NOT_AUTHORIZED"),
        ({"testnet_authorized": True}, "TESTNET_NOT_AUTHORIZED"),
        ({"post_count": 1}, "POST_NOT_AUTHORIZED"),
        ({"get_request_count": 2}, "GET_REQUEST_COUNT_NOT_ONE"),
    ],
)
def test_adjudication_fail_closed_guards(kwargs: dict, needle: str) -> None:
    with pytest.raises(CoverUsdcCurrentPublicTierMmrEvidenceError, match=needle):
        _adjudicate(**kwargs)


def test_collect_uses_one_public_get_and_no_post() -> None:
    body = encode_fixture_position_tiers_payload_v1(
        inst_family=CANARY_INST_FAMILY,
        qty_one_mmr=CURRENT_MMR,
    )
    transport = RecordingFakeCanaryTransportV1(body=body, venue_live_contact=True)
    bound, snapshot, response = collect_current_public_tier_mmr_public_get_v1(
        transport=transport,
        receive_ts_unix=RECEIVE_TS,
    )
    assert len(transport.calls) == 1
    request = transport.calls[0]
    assert request.method == "GET"
    assert request.host == "eea.okx.com"
    assert request.endpoint == POSITION_TIERS_QUERY_PATH
    assert request.body_text == ""
    assert bound.mmr_public_tier_qty_one_current_value == CURRENT_MMR
    assert bound.get_request_count == 1
    assert bound.post_count == 0
    assert snapshot["POST_COUNT"] == 0
    assert snapshot["NO_TICKER_GET_THIS_STEP"] is True
    assert snapshot["NO_MARK_PRICE_GET_THIS_STEP"] is True
    assert snapshot["NO_PRIVATE_GET_THIS_STEP"] is True
    assert response.status_code == 200


def test_z2k_go_does_not_authorize_live_order_or_funding() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    assert NEXT_CANONICAL_POINTER in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    evaluation = evaluate_canary_submit_gates_v1(
        owner_go=OWNER_GO,
        owner_go_consumed=False,
        authorization_scope=AUTHORIZATION_SCOPE,
        bound_origin_main_sha="abc",
        expected_origin_main_sha="abc",
        live_canary_authorized=True,
        live_enabled=True,
        live_armed=True,
        confirm_token=LIVE_CONFIRM_TOKEN,
        blocks_new_entry=False,
        unresolved_economic_divergence=False,
        live_reconciliation_proven=True,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        environment="LIVE",
        fixture_or_demo_or_testnet=False,
        max_notional="6.30437",
        min_executable_notional="6.30437",
        order_count=0,
        position_count=0,
        exposure_above_minimum_bound=False,
        live_canary_cybersecurity_gate="PASS",
        rest_host="eea.okx.com",
        secretref_uri="secretref://vault/peak-trade/live-canary-minimum-exposure/okx",
    )
    assert evaluation.submit_allowed is False
    assert "REEVALUATION_OR_PREPARATION_GO_CANNOT_AUTHORIZE_SUBMIT" in evaluation.reasons


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2k_section(text: str) -> str:
    start = text.find(Z2K_HEADING)
    assert start >= 0, "missing §11.13.5.Z2K heading"
    end = text.find("### 11.13.5.Z2L", start)
    assert end > start, "missing §11.13.5.Z2L boundary after Z2K"
    return text[start:end]


def test_z2k_docs_bind_observational_mmr_without_cover_usdc() -> None:
    section = _z2k_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=CURRENT_PUBLIC_TIER_MMR_PUBLIC_GET_EVIDENCE_ONLY",
        "MMR_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND",
        f"MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE={OBSERVED_MMR}",
        "PUBLIC_MMR_CLASSIFICATION=PUBLIC_TIER_FACT_NOT_ACCOUNT_EFFECTIVE_MMR",
        "PUBLIC_MMR_IS_NOT_LIQUIDATION_PRICE_EVIDENCE=true",
        "MM_LIQ_BUFFER_NUMERIC_STATUS=UNINSTANTIATED",
        "SLIPPAGE_RESERVE_NUMERIC_STATUS=UNINSTANTIATED",
        "BID_ASK_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND",
        "BID_PX_CURRENT_VALUE=64529.9",
        "ASK_PX_CURRENT_VALUE=64530",
        "MARKPX_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND",
        "MARKPX_CURRENT_VALUE=64495.3",
        "MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS=UNPROVEN",
        "HISTORICAL_MMR_IS_NOT_CURRENT=true",
        "HISTORICAL_L_OR_S_PACK_SUBSTITUTED=false",
        "NO_PROVIDER_TS_INVENTED=true",
        f"IMR_PUBLIC_TIER_QTY_ONE_OBSERVED={OBSERVED_IMR}",
        "TIER_CURRENT_VALUE=1",
        "MONETARY_BASE_STATUS=UNPROVEN",
        "FX_STATUS=UNPROVEN",
        "ROUNDING_STATUS=UNPROVEN",
        "EXACT_OKX_FEE_FORMULA_STATUS=UNPROVEN",
        "POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN",
        "NORMAL_EXPIRY_RATE_0_0001_STATUS=PROVEN_APPLICABILITY_NON_OPERATIVE",
        "CONSERVATIVE_RATE_0_0003_STATUS=INTERNAL_CONSERVATIVE_POLICY_NOT_EXCHANGE_TRUTH",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "NUMERIC_FUNDING_AMOUNT_PRODUCED=false",
        "NUMERIC_FUNDING_AMOUNT=NONE",
        "QTY_LIMIT=1",
        "SCALING_AUTHORIZED=false",
        "MULTI_FUTURE_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "FUNDING_EXECUTED=false",
        "EXCHANGE_TRUTH_CHANGED=false",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CANONICAL_NEXT_STEP={NEXT_CANONICAL_POINTER}",
        "NO_USD_EQUALS_USDC",
        "NO_COVER_USDC_INSTANTIATION",
        "NO_MM_LIQ_BUFFER_NUMERIC",
        "NO_NUMERIC_FUNDING_AMOUNT",
        "NO_FUNDING",
        "NO_EXECUTE",
        "/api/v5/public/position-tiers",
    )
    for marker in required:
        assert marker in section, f"missing Z2K marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nSCALING_AUTHORIZED=true\n",
        "\nFUNDING_AMOUNT_PROVEN=true\n",
        "\nCOVER_USDC_STATUS=PROVEN\n",
        "\nEXCHANGE_TRUTH_CHANGED=true\n",
        "\nFX_STATUS=PROVEN\n",
        "\nROUNDING_STATUS=PROVEN\n",
        "\nMONETARY_BASE_STATUS=PROVEN\n",
        "\nNUMERIC_FUNDING_AMOUNT_PRODUCED=true\n",
        "\nUSD_EQUALS_USDC=true\n",
        "MM_LIQ_BUFFER_NUMERIC_STATUS=PROVEN",
        "MMR_TERM_STATUS=UNINSTANTIATED",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"


def test_map_of_truth_and_spec_follow_z2k_current_pointer() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2K" in mot
    assert f"{OWNER_GO}_STATUS=CONSUMED_GET_ONLY_PUBLIC_TIER_MMR_OBSERVED_NOT_COVER_USDC" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_CANONICAL_POINTER}" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert "MMR_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND" in mot
    assert "MM_LIQ_BUFFER_NUMERIC_STATUS=UNINSTANTIATED" in mot
    assert "Current SSOT: Master Runbook §11.13.5.Z2K." in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2H." not in spec
    assert OWNER_GO in spec
    assert NEXT_CANONICAL_POINTER in spec
    assert "CURRENT_PUBLIC_TIER_MMR_PUBLIC_GET_EVIDENCE_ONLY" in spec


def test_sealed_z2k_evidence_pack_verifies_without_cover_usdc() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
        verify_manifest_v1,
    )

    root = (
        REPO_ROOT
        / "evidence"
        / "ops"
        / "section_11_13_5_z2k_current_public_tier_mmr_public_get_v1"
        / "20260819T085545Z"
    )
    verify = verify_manifest_v1(root)
    assert verify["MANIFEST_VERIFY_RC"] == 0
    summary = _read(root / "SUMMARY.json")
    assert f'"MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE": "{OBSERVED_MMR}"' in summary
    assert '"COVER_USDC_STATUS": "UNINSTANTIATED"' in summary
    assert '"POST_COUNT": 0' in summary
    assert '"LIVE_AUTHORIZED": false' in summary
    zero = _read(root / "zero_write_assertions.json")
    assert '"ORDER_EXECUTED": false' in zero
    redaction = _read(root / "redaction_check.json")
    assert '"SECRET_VALUE_PERSISTED": false' in redaction
