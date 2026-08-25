"""§11.13.5.Z2CD P8 final forensic audit persist.

Docs/governance invariants only. Records the already-completed P8
audit without runtime, GET, POST, flatten, Cover, live, testnet, or
canary authorization. Does not rewrite Z2CC. Does not rewrite P8 PASS
into FERTIG_B, LIVE_READY, or LIVE_AUTHORIZED. Does not close audited
open residuals.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CC_HEADING = (
    "### 11.13.5.Z2CC Post-Z2CB P7.5 live-gate reconciliation bounded forensic adjudication"
)
Z2CD_HEADING = "### 11.13.5.Z2CD Post-Z2CC P8 final forensic audit persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "SECTION_11_13_5_POST_Z2CC_P8_FINAL_FORENSIC_AUDIT_PERSIST_ONLY"
BASELINE_SHA = "50baf122b9f42e3e0353108baad1fe014ba8b4bc"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cd_section(text: str) -> str:
    start = text.find(Z2CD_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CD heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2CD"
    return text[start:end]


def _z2cc_section(text: str) -> str:
    start = text.find(Z2CC_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CC heading"
    end = text.find(Z2CD_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CD boundary after Z2CC"
    return text[start:end]


def test_z2cd_heading_is_unique_and_follows_z2cc() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CD_HEADING) == 1
    z2cc = text.find(Z2CC_HEADING)
    z2cd = text.find(Z2CD_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cc < z2cd < ladder


def test_z2cc_historical_slice_was_not_rewritten() -> None:
    section = _z2cc_section(_read(MASTER_RUNBOOK))
    assert "P7_5_STATUS=CLOSED_FAIL_CLOSED_WITHOUT_RUNTIME" in section
    assert "P8_STARTED=false" in section
    assert "LIVE_READINESS_STATUS=FAIL_CLOSED_NOT_READY" in section
    assert "LIVE_GATE_MATRIX_STATUS=COMPLETE_FAIL_CLOSED_NOT_READY" in section
    assert "EMPTY_EQUALS_ZERO=false" in section
    assert "\nP8_STARTED=true\n" not in section
    assert "Z2CD" not in section


def test_z2cd_docs_bind_p8_pass_without_live_ready() -> None:
    section = _z2cd_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CD_POST_Z2CC_P8_FINAL_FORENSIC_AUDIT_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=Z2CD_P8_FINAL_FORENSIC_AUDIT_SSOT_PERSIST_DOCS_ONLY",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "ORIGIN_MAIN_SUPERSESSION_STATUS=NONE",
        "PREDECESSOR_SLICE=11.13.5.Z2CC",
        f"PREDECESSOR_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "Z2CC_TEXT_REWRITTEN=false",
        "BTC_EVIDENCE_PROMOTED_TO_SUI=false",
        "P8_READ_ONLY_AUDIT_SCOPE=POST_Z2CC_P8_FINAL_FORENSIC_AUDIT_ONLY",
        "P8_NEW_RUNTIME_API_CALLS_TOTAL=0",
        "P8_NEW_AUTHENTICATED_GETS_TOTAL=0",
        "P8_NEW_PUBLIC_GETS_TOTAL=0",
        "P8_NEW_POST_CALLS_TOTAL=0",
        "P8_POSITION_MUTATIONS=0",
        "P8_ACCOUNT_MUTATIONS=0",
        "P8_ORDER_MUTATIONS=0",
        "P8_CONFIG_MUTATIONS=0",
        "P0_STATUS=CLOSED",
        "P1_STATUS=CLOSED",
        "P2_STATUS=CLOSED",
        "P3_STATUS=CLOSED",
        "P4_STATUS=CLOSED",
        "P5_STATUS=CLOSED",
        "P6_STATUS=NOT_EXECUTED",
        "P6_CLASS=OPTIONAL",
        "P7_1_STATUS=CLOSED",
        "P7_2_STATUS=CLOSED_BOUNDED",
        "P7_3_STATUS=SLICE_CLOSED_RESIDUAL_FAIL_CLOSED",
        "P7_4_STATUS=CLOSED_FAIL_CLOSED_NO_MUTATION",
        "P7_5_STATUS=CLOSED_FAIL_CLOSED_WITHOUT_RUNTIME",
        "P8_STARTED=true",
        "INTERNAL_NOTIONAL_PV_POLICY_TERM=0.8044",
        "MM_LIQ_BUFFER_NUMERIC=0.016088",
        "SLIPPAGE_RESERVE_NUMERIC=0.0008",
        "FEE_RESERVE_NUMERIC=0.00080440",
        "DELIVERY_COVER_INTERNAL_NUMERIC=0.00024132",
        "COMPOSITION_NUMERIC=0.01793372",
        "COMPOSITION_NUMERIC_REPRODUCED=0.01793372",
        "COMPOSITION_NUMERIC_PERSISTED=0.01793372",
        "COMPOSITION_NUMERIC_MATCH=true",
        "INTERNAL_RISK_PROGRAM_STATUS=BOUND_COMPOSITION_NUMERIC=0.01793372",
        "RISK_ENVELOPE_STATUS=IDENTITY_BOUND_NUMERIC_UNINSTANTIATED",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "USD_USDC_OPERATOR_STATUS=UNPROVEN",
        "NO_USD_EQUALS_USDC=true",
        "ONE_CONTRACT_EQUALS_ONE_SUI=false",
        "BID_ASK_EXECUTION_PRICE_EQUIVALENCE=false",
        "EXCHANGE_POSITION_VALUE_STATUS=UNPROVEN",
        "EMPTY_EQUALS_ZERO=false",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "BOUNDED_CATEGORY_C_NE_UNIVERSAL_ABSENCE=true",
        "COMPOSITION_NE_COVER=true",
        "RISK_ENVELOPE_IDENTITY_NE_EXCHANGE_TRUTH=true",
        "BTC_HISTORICAL_OR_CURRENT_SEMANTICS_MUST_NOT_RESURRECT_INTO_SUI=true",
        "HISTORICAL_P3_SUI_AUTHENTICATED_TRADE_FEE_GET=true",
        "HISTORICAL_P7_3_AUTHENTICATED_POSITIONS_GET=true",
        "HISTORICAL_BTC_CATEGORY_C_Z2BB=true",
        "HISTORICAL_PUBLIC_SUI_GETS_MARKPX_INSTRUMENTS_TICKER=true",
        "HISTORICAL_CANARY_POST_HTTP_401_WITHOUT_FILL_OR_ACK=true",
        "HISTORICAL_BTC_SET_ACCOUNT_LEVERAGE_3=true",
        "P7_3_FLATTEN_PRECONDITION_STATUS=UNRESOLVED_FAIL_CLOSED",
        "PRODUCTIVE_URLLIB_FLATTEN_SEND_IMPLEMENTED=false",
        "FLATTEN_EXECUTE_OWNER_GO_STATUS=ABSENT",
        "FLATTEN_SUCCESS_PREDICATE=AMBIGUOUS",
        "LIVE_FLATTEN_PROVABILITY_STATUS=UNPROVEN",
        "NO_RESIDUAL_CLOSED_BY_THIS_PERSIST=true",
        "LIVE_GATE_MATRIX_STATUS=COMPLETE_FAIL_CLOSED_NOT_READY",
        "LIVE_READINESS_STATUS=FAIL_CLOSED_NOT_READY",
        "LIVE_AUTHORIZED=false",
        "LIVE_ENABLED_STATUS=false",
        "LIVE_ARMED_STATUS=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "P8_FINAL_FORENSIC_AUDIT_STATUS=PASS",
        "P8_PASS_IS_NOT_FERTIG_B=true",
        "P8_PASS_IS_NOT_LIVE_READY=true",
        "P8_PASS_IS_NOT_LIVE_AUTHORIZATION=true",
        "FERTIG_B=false",
        "LIVE_READY=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "HARD_STOP_AFTER_PR=true",
        "Z2CC_UNCHANGED=true",
        "RUNTIME_API_CALLS=0",
        "AUTHENTICATED_CALLS=0",
        "PUBLIC_GET_CALLS=0",
        "POST_CALLS=0",
        "POSITION_MUTATIONS=0",
        "ACCOUNT_MUTATIONS=0",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "CURRENT_CANONICAL_INSTRUMENT=SUI-USD_UM_XPERP-310404",
    )
    for marker in required:
        assert marker in section, f"missing Z2CD marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nPRODUCTIVE_FLATTEN_EXECUTED=true\n",
        "\nEMPTY_EQUALS_ZERO=true\n",
        "\nBTC_EVIDENCE_PROMOTED_TO_SUI=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nZ2CC_TEXT_REWRITTEN=true\n",
        "\nONE_CONTRACT_EQUALS_ONE_SUI=true\n",
        "\nFERTIG_B=true\n",
        "\nLIVE_READY=true\n",
        "\nP8_PASS_IS_NOT_FERTIG_B=false\n",
        "\nP8_PASS_IS_NOT_LIVE_READY=false\n",
        "\nCOMPOSITION_NUMERIC_MATCH=false\n",
        "\nNO_RESIDUAL_CLOSED_BY_THIS_PERSIST=false\n",
        "\nMULTI_FUTURE_AUTHORIZED=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2CD marker present: {marker!r}"


def test_z2cd_map_of_truth_remains_navigation_only_without_z2cd_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2CD |" not in mot
    assert "§11.13.5.Z2CC |" not in mot
    assert "§11.13.5.Z2CB |" not in mot
