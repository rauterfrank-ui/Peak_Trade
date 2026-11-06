"""LIVE_ACCOUNTING_RECONSTRUCTED producer, identity, and fail-closed tests."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_adjudication_v1 import (
    adjudicate_live_accounting_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_execute_v1 import (
    bind_accounting_evidence_from_persisted_path_v1,
    execute_live_accounting_reconstructed_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_identity_v1 import (
    ACCOUNTING_TOLERANCE_AUTHORITY,
    ACCOUNTING_UNIT,
    BOUND_CLORDID,
    BOUND_FILL_RAW_RELPATH,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POSITION_RAW_RELPATH,
    BOUND_TRADE_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.accounting_reconstructed_predicate_v1 import (
    ADMISSIBLE_SOURCE_KIND,
    ACCOUNTING_IDENTITY_EQUATION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    HISTORICAL_ACCOUNTING_RECONSTRUCTED_OWNER_GO,
    HISTORICAL_ACCOUNTING_RECONSTRUCTED_SHA,
    LIVE_ACCOUNTING_RECONSTRUCTED_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _live_accounting_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_kind": ADMISSIBLE_SOURCE_KIND,
        "POST_USED": False,
        "GET_PERFORMED": False,
        "PRIVATE_GET_USED": False,
        "CANCEL_USED": False,
        "AMEND_USED": False,
        "FLATTEN_EXECUTE_USED": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "fill_source_path": BOUND_FILL_RAW_RELPATH,
        "position_source_path": BOUND_POSITION_RAW_RELPATH,
        "fill_row": {
            "ordId": BOUND_ORDID,
            "clOrdId": BOUND_CLORDID,
            "instId": BOUND_INSTID,
            "tradeId": BOUND_TRADE_ID,
            "fillSz": "1",
            "fillPx": "0.748",
            "fillPnl": "0",
            "fee": "-0.000374",
            "feeCcy": "USDC",
        },
        "position_row": {
            "instId": BOUND_INSTID,
            "instType": "FUTURES",
            "posSide": "net",
            "posId": "3891385768441942017",
            "pos": "1",
            "ccy": "USDC",
            "fee": "-0.000374",
            "pnl": "0",
            "realizedPnl": "-0.000374",
            "fundingFee": "0",
            "settledPnl": "0",
            "tradeId": BOUND_TRADE_ID,
            "upl": "0.0041",
        },
    }
    if "fill_row" in overrides and isinstance(overrides["fill_row"], dict):
        fill = dict(payload["fill_row"])  # type: ignore[arg-type]
        fill.update(overrides.pop("fill_row"))  # type: ignore[arg-type]
        payload["fill_row"] = fill
    if "position_row" in overrides and isinstance(overrides["position_row"], dict):
        position = dict(payload["position_row"])  # type: ignore[arg-type]
        position.update(overrides.pop("position_row"))  # type: ignore[arg-type]
        payload["position_row"] = position
    payload.update(overrides)
    return payload


def test_identity_bound_persisted_path_reconstructs_realized_pnl() -> None:
    proof = adjudicate_live_accounting_reconstructed_v1(
        accounting_evidence=_live_accounting_evidence()
    )
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is True
    assert proof["LIVE_RESTART_RECONSTRUCTED"] is False
    assert proof["SECTION_11_14_COMPLETE"] is False
    assert proof["CASE_ADJUDICATION"] == "CASE_LIVE_ACCOUNTING_RECONSTRUCTED_RESTART_INELIGIBLE"
    assert proof["ACCOUNTING_RESULT"] == "-0.000374"
    assert proof["ACCOUNTING_RESULT_UNIT"] == ACCOUNTING_UNIT
    assert proof["ACCOUNTING_RESIDUAL"] == "0"
    assert proof["ACCOUNTING_RESIDUAL_UNIT"] == ACCOUNTING_UNIT
    assert proof["ACCOUNTING_TOLERANCE"] == "0"
    assert proof["ACCOUNTING_TOLERANCE_AUTHORITY"] == ACCOUNTING_TOLERANCE_AUTHORITY
    assert proof["GET_PERFORMED"] is False
    assert proof["PRIVATE_GET_USED"] is False
    assert proof["POST_USED"] is False
    assert proof["UPL_IN_REALIZED_IDENTITY"] is False
    assert proof["RAW_UPL_IF_OBSERVED"] == "0.0041"
    assert "reconstructed_realized_pnl" in LIVE_ACCOUNTING_RECONSTRUCTED_CANONICAL_DEFINITION
    assert ACCOUNTING_IDENTITY_EQUATION in proof["ACCOUNTING_IDENTITY_EQUATION"]


def test_independently_recomputed_identity_matches_venue_realized_pnl() -> None:
    fill_pnl = Decimal("0")
    fee = Decimal("-0.000374")
    funding = Decimal("0")
    settled = Decimal("0")
    observed = Decimal("-0.000374")
    reconstructed = fill_pnl + fee + funding + settled
    assert reconstructed == observed
    assert observed - reconstructed == Decimal("0")
    proof = adjudicate_live_accounting_reconstructed_v1(
        accounting_evidence=_live_accounting_evidence()
    )
    assert Decimal(str(proof["ACCOUNTING_RESULT"])) == reconstructed
    assert Decimal(str(proof["ACCOUNTING_RESIDUAL"])) == Decimal("0")


def test_injected_evidence_cannot_promote_live_accounting() -> None:
    proof = adjudicate_live_accounting_reconstructed_v1(
        accounting_evidence=_live_accounting_evidence(source_kind="GOVERNED_OFFLINE_CONTRACT")
    )
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is False
    assert proof["adjudicated_value"] is False


def test_injected_true_field_fails_closed() -> None:
    with pytest.raises(
        Section1114OfflineSurfaceError, match="ACCOUNTING_FIELD_PROMOTED_BY_INJECTED"
    ):
        adjudicate_live_accounting_reconstructed_v1(
            accounting_evidence=_live_accounting_evidence(
                source_kind="GOVERNED_OFFLINE_CONTRACT",
                LIVE_ACCOUNTING_RECONSTRUCTED=True,
            )
        )


def test_missing_funding_fee_is_not_zero() -> None:
    proof = adjudicate_live_accounting_reconstructed_v1(
        accounting_evidence=_live_accounting_evidence(position_row={"fundingFee": ""})
    )
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is False
    assert proof["ACCOUNTING_SEMANTICS_STATUS"] == "REQUIRED_TERM_MISSING_OR_EMPTY"
    assert proof["path_classification"]["MISSING_NOT_REPLACED_BY_ZERO"] is True


def test_absent_funding_fee_field_fails_closed() -> None:
    payload = _live_accounting_evidence()
    position = dict(payload["position_row"])  # type: ignore[arg-type]
    del position["fundingFee"]
    payload["position_row"] = position
    proof = adjudicate_live_accounting_reconstructed_v1(accounting_evidence=payload)
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is False
    assert proof["ACCOUNTING_SEMANTICS_STATUS"] == "REQUIRED_TERM_MISSING_OR_EMPTY"


def test_currency_mismatch_fails_closed() -> None:
    proof = adjudicate_live_accounting_reconstructed_v1(
        accounting_evidence=_live_accounting_evidence(position_row={"ccy": "USD"})
    )
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is False
    assert proof["ACCOUNTING_SEMANTICS_STATUS"] == "CURRENCY_MISMATCH"


def test_trade_id_mismatch_fails_closed() -> None:
    proof = adjudicate_live_accounting_reconstructed_v1(
        accounting_evidence=_live_accounting_evidence(position_row={"tradeId": "999"})
    )
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is False
    assert proof["ACCOUNTING_SEMANTICS_STATUS"] == "TRADE_ID_MISMATCH"


def test_nonzero_residual_fails_closed() -> None:
    proof = adjudicate_live_accounting_reconstructed_v1(
        accounting_evidence=_live_accounting_evidence(position_row={"realizedPnl": "-0.001"})
    )
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is False
    assert proof["ACCOUNTING_SEMANTICS_STATUS"] == "ACCOUNTING_RESIDUAL_NONZERO"
    assert proof["ACCOUNTING_RESIDUAL"] != "0"


def test_fee_path_divergence_fails_closed() -> None:
    proof = adjudicate_live_accounting_reconstructed_v1(
        accounting_evidence=_live_accounting_evidence(position_row={"fee": "-0.001"})
    )
    assert proof["LIVE_ACCOUNTING_RECONSTRUCTED"] is False
    assert proof["ACCOUNTING_SEMANTICS_STATUS"] == "FEE_PATH_DIVERGENCE"


def test_post_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="POST_INVOKED"):
        adjudicate_live_accounting_reconstructed_v1(
            accounting_evidence=_live_accounting_evidence(POST_USED=True)
        )


def test_private_get_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="PRIVATE_GET_INVOKED"):
        adjudicate_live_accounting_reconstructed_v1(
            accounting_evidence=_live_accounting_evidence(GET_PERFORMED=True)
        )


def test_restart_promotion_fails_closed() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="RESTART_PROMOTED"):
        adjudicate_live_accounting_reconstructed_v1(
            accounting_evidence=_live_accounting_evidence(LIVE_RESTART_RECONSTRUCTED=True)
        )


def test_fixture_source_refused() -> None:
    with pytest.raises(Section1114OfflineSurfaceError, match="FORBIDDEN_LIVE_SOURCE"):
        adjudicate_live_accounting_reconstructed_v1(
            accounting_evidence=_live_accounting_evidence(source_kind="FIXTURE")
        )


def test_execute_reads_persisted_raw_without_get() -> None:
    result = execute_live_accounting_reconstructed_v1(
        owner_go=HISTORICAL_ACCOUNTING_RECONSTRUCTED_OWNER_GO,
        origin_main_sha=HISTORICAL_ACCOUNTING_RECONSTRUCTED_SHA,
        repo_root=REPO_ROOT,
        run_id="20260904T185000Z",
    )
    adjudication = result["adjudication"]
    summary = result["summary"]
    assert adjudication["LIVE_ACCOUNTING_RECONSTRUCTED"] is True
    assert summary["GET_PERFORMED"] is False
    assert summary["CREDENTIAL_USE"] is False
    assert summary["POST_USED"] is False
    assert summary["RAW_EVIDENCE_MODIFIED"] is False
    assert result["raw_exchanges"] == []
    bound = bind_accounting_evidence_from_persisted_path_v1(repo_root=REPO_ROOT)
    assert bound["fill_source_path"] == BOUND_FILL_RAW_RELPATH
    assert bound["position_source_path"] == BOUND_POSITION_RAW_RELPATH
    assert (REPO_ROOT / BOUND_FILL_RAW_RELPATH).is_file()
    assert (REPO_ROOT / BOUND_POSITION_RAW_RELPATH).is_file()
