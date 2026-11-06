"""GET-only trade-fee refresh tests. No live network. No POST."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_14_current_origin_main_8605bf_get_only_trade_fee_and_stale_pretrade_predicate_refresh_v1.adjudication_v1 import (
    adjudicate_trade_fee_and_stale_pretrade_refresh_v1,
)
from src.ops.section_11_14_current_origin_main_8605bf_get_only_trade_fee_and_stale_pretrade_predicate_refresh_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EVIDENCE_RELATIVE_ROOT,
    EXACT_OKX_FEE_FORMULA_UNPROVEN,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_PACK_RELATIVE_ROOT,
    OWNER_EXECUTION_AUTHORIZED,
    OWNER_GET_ONLY_GO,
    TRADE_FEE_QUERY,
)
from src.ops.section_11_14_current_origin_main_8605bf_get_only_trade_fee_and_stale_pretrade_predicate_refresh_v1.persist_evidence_v1 import (
    persist_evidence_pack_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_get_refresh_adjudication_keeps_oem_formula_unproven_and_owner_execution_false() -> None:
    result = adjudicate_trade_fee_and_stale_pretrade_refresh_v1(repo_root=REPO_ROOT)
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert EXACT_OKX_FEE_FORMULA_UNPROVEN is True
    assert OWNER_EXECUTION_AUTHORIZED is False
    assert result["EXACT_OKX_FEE_FORMULA_STATUS"] == "UNPROVEN"
    assert result["EXACT_OKX_FEE_FORMULA_UNPROVEN"] is True
    assert result["OWNER_EXECUTION_AUTHORIZED"] is False
    assert result["POST_PERFORMED"] is False
    assert result["WIRE_SEND_EXECUTED"] is False
    assert result["LIVE_SUBMIT_EXECUTED"] is False
    assert result["RESTART_EXECUTED"] is False
    assert result["CRASH_TEST_EXECUTED"] is False
    assert result["GET_PERFORMED"] is True
    assert result["TRADE_FEE_GET_PERFORMED"] is True
    assert result["TRADE_FEE_HTTP_RESULT"] == "HTTP_200"
    assert result["TRADE_FEE_OKX_CODE"] == "0"
    assert result["TRADE_FEE_TARGET_FAMILY_MATCH"] is True
    assert result["TRADE_FEE_QUERY"] == TRADE_FEE_QUERY
    assert result["TRADE_FEE_TAKER_FIELD"] == "takerUSDC"
    assert result["TRADE_FEE_MAKER_FIELD"] == "makerUSDC"
    assert result["TRADE_FEE_TAKER_RAW"] == "-0.0005"
    assert result["TRADE_FEE_MAKER_RAW"] == "-0.0002"
    assert result["TRADE_FEE_DELIVERY_RAW"] == "0.0003"
    assert result["TRADE_FEE_DELIVERY_ROLE"] == "NOT_PART_OF_ENTRY_FILL"
    assert result["CURRENT_ACCOUNT_FEE_RATE_OBSERVED"] is True
    assert result["CURRENT_NUMERIC_FEE_INPUT_PROVEN"] is True
    assert result["BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN"] is True
    assert result["TECHNICAL_PRE_EXECUTION_READINESS"] is True
    assert result["TECHNICAL_EXECUTION_READINESS"] is True
    assert result["EARLIEST_UNRESOLVED_TECHNICAL_PRE_EXECUTION_PREDICATE"] == "NONE"
    assert result["EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE"] == "OWNER_EXECUTION_AUTHORIZED"
    assert result["OWNER_GET_ONLY_GO"] == OWNER_GET_ONLY_GO
    assert result["RECORDED_ORIGIN_MAIN_SHA"] == EXPECTED_ORIGIN_MAIN_SHA
    assert result["LIVE_RESTART_RECONSTRUCTED"] is False
    assert result["HOST_CRASH_DURABILITY"] == "UNPROVEN"


def test_get_refresh_does_not_equate_fee_classes() -> None:
    result = adjudicate_trade_fee_and_stale_pretrade_refresh_v1(repo_root=REPO_ROOT)
    assert result["EXACT_OKX_FEE_FORMULA_STATUS"] != "PROVEN"
    assert result["EXPECTED_FEE_PRETRADE"] != result["TRADE_FEE_TAKER_RAW"]
    assert result["BOUNDED_FEE_ENVELOPE_ROLE"] == (
        "PEAK_TRADE_INTERNAL_CONSERVATIVE_ENVELOPE_NOT_OEM_OKX_FEE_FORMULA"
    )
    formula_row = next(
        row for row in result["PREDICATE_TABLE"] if row["PREDICATE_NAME"] == "EXACT_OKX_FEE_FORMULA"
    )
    assert formula_row["CURRENT_VALUE"] == "UNPROVEN"
    assert formula_row["CHANGE_REASON"] == "UNCHANGED"


def test_get_refresh_persist_manifest_and_non_execution() -> None:
    persisted = persist_evidence_pack_v1(repo_root=REPO_ROOT)
    assert int(persisted["MANIFEST_VERIFY_RC"]) == 0
    overlay = REPO_ROOT / EVIDENCE_RELATIVE_ROOT / CANONICAL_EVIDENCE_RUN_ID
    get_pack = REPO_ROOT / GET_PACK_RELATIVE_ROOT / CANONICAL_EVIDENCE_RUN_ID
    assert int(verify_manifest_v1(overlay).get("MANIFEST_VERIFY_RC", 1)) == 0
    assert int(verify_manifest_v1(get_pack).get("MANIFEST_VERIFY_RC", 1)) == 0
    safety = (overlay / "SAFETY.json").read_text(encoding="utf-8")
    assert '"OWNER_EXECUTION_AUTHORIZED": false' in safety
    assert '"POST_PERFORMED": false' in safety
    assert '"GET_PERFORMED": true' in safety
    summary = (overlay / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"EXACT_OKX_FEE_FORMULA_STATUS": "UNPROVEN"' in summary
    assert '"TECHNICAL_PRE_EXECUTION_READINESS": true' in summary
    assert '"OWNER_EXECUTION_AUTHORIZED": false' in summary
