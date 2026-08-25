"""§11.13.5.Z2BY P7.1 canonical SUI identity rebind persist.

Docs/governance invariants only. Records the fail-closed current-identity
rebind from BTC-USD_UM_XPERP-310404 to SUI-USD_UM_XPERP-310404. Does not
authorize live, testnet, canary, flatten, Category C, COVER_USDC, USD=USDC,
GET, POST, or Map-of-Truth mutation. Does not rewrite Z2BX.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2BX_HEADING = "### 11.13.5.Z2BX Post-Z2BW P5 risk-envelope identity and Cover negative contract"
Z2BY_HEADING = (
    "### 11.13.5.Z2BY Post-Z2BX P7.1 canonical SUI identity rebind and fail-closed validation"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "SECTION_11_13_5_POST_Z2BX_P7_1_CANONICAL_SUI_REBIND_IMPLEMENTATION_AND_FAIL_CLOSED_VALIDATION_ONLY"
BASELINE_SHA = "a0f084f4795ae0b6ccbe60df125f3166bb446d15"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2by_section(text: str) -> str:
    start = text.find(Z2BY_HEADING)
    assert start >= 0, "missing §11.13.5.Z2BY heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2BY"
    return text[start:end]


def _z2bx_section(text: str) -> str:
    start = text.find(Z2BX_HEADING)
    assert start >= 0, "missing §11.13.5.Z2BX heading"
    end = text.find(Z2BY_HEADING, start)
    assert end > start, "missing §11.13.5.Z2BY boundary after Z2BX"
    return text[start:end]


def test_z2by_heading_is_unique_and_follows_z2bx() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2BY_HEADING) == 1
    z2bx = text.find(Z2BX_HEADING)
    z2by = text.find(Z2BY_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2bx < z2by < ladder


def test_z2bx_historical_slice_was_not_rewritten() -> None:
    section = _z2bx_section(_read(MASTER_RUNBOOK))
    assert "CURRENT_CANONICAL_INSTRUMENT=BTC-USD_UM_XPERP-310404" in section
    assert "SUI_CANONICAL_REBIND_READY=false" in section
    assert "SUI_CANONICAL_REBIND_EXECUTED=false" in section
    assert "RISK_ENVELOPE_IDENTITY_NUMERIC=0.01793372" in section
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in section
    assert "\nLIVE_AUTHORIZED=true\n" not in section
    assert "SUI_SELECTED_AS_CURRENT_CANONICAL_INSTRUMENT=true" not in section


def test_z2by_docs_bind_identity_rebind_without_live_or_cover() -> None:
    section = _z2by_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2BY_POST_Z2BX_P7_1_CANONICAL_SUI_IDENTITY_REBIND_AND_FAIL_CLOSED_VALIDATION_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=Z2BY_CANONICAL_SUI_IDENTITY_REBIND_SSOT_PERSIST_PLUS_FAIL_CLOSED_IMPLEMENTATION",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "PREDECESSOR_SLICE=11.13.5.Z2BX",
        "Z2BX_TEXT_REWRITTEN=false",
        "Z2BX_COMPOSITION_RECOMPUTED=false",
        "HISTORICAL_BTC_EVIDENCE_REWRITTEN=false",
        "CANONICAL_REBIND=true",
        "SUI_CANONICAL_REBIND_READY=true",
        "SUI_CANONICAL_REBIND_EXECUTED=true",
        "SUI_SELECTED_AS_CURRENT_CANONICAL_INSTRUMENT=true",
        "CURRENT_CANONICAL_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "DEFAULT_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "CANARY_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "OWNER_SELECTED_SUCCESSOR_TARGET=SUI-USD_UM_XPERP-310404",
        "PRE_REBIND_CANONICAL_INSTRUMENT=BTC-USD_UM_XPERP-310404",
        "SILENT_BTC_FALLBACK_PRESENT=false",
        "ARBITRARY_INSTRUMENT_STRINGS_ACCEPTED=false",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "SUI_CTVAL=1",
        "SUI_CTVAL_CCY=SUI",
        "SUI_TICKSZ=0.0001",
        "SUI_MINSZ=1",
        "SUI_LOTSZ=1",
        "ONE_CONTRACT_EQUALS_ONE_SUI=false",
        "EXCHANGE_POSITION_VALUE_STATUS=UNPROVEN",
        "RISK_ENVELOPE_IDENTITY_NUMERIC=0.01793372",
        "RISK_ENVELOPE_IDENTITY_STATUS=BOUND",
        "RISK_ENVELOPE_NUMERIC_STATUS=UNINSTANTIATED",
        "SUI_RISK_ENVELOPE_NUMERIC_PROVEN=false",
        "COMPOSITION_NUMERIC=0.01793372",
        "NO_COMPOSITION_RECOMPUTED=true",
        "NO_RISK_ENVELOPE_IDENTITY_RECOMPUTED=true",
        "COVER_NEGATIVE_CONTRACT=true",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "USD_USDC_OPERATOR_STATUS=UNPROVEN",
        "USD_EQUALS_USDC_ASSUMED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "MULTI_FUTURE_AUTHORIZED=false",
        "MAX_POSITIONS_EFFECTIVE=1",
        "POSITION_COUNT_LIMIT=1",
        "SUBMIT_UNLOCKED=false",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "GLOBAL_UNIQUE_CANONICAL_NEXT_STEP=NONE_BY_P3_POLICY",
        "CANONICAL_IDENTITY_REBIND_NE_LIVE_AUTHORIZATION=true",
        "CANONICAL_IDENTITY_REBIND_NE_TESTNET_AUTHORIZATION=true",
        "CANONICAL_IDENTITY_REBIND_NE_CANARY_AUTHORIZATION=true",
        "CANONICAL_IDENTITY_REBIND_NE_CATEGORY_C_UNIVERSAL_ABSENCE=true",
        "CANONICAL_IDENTITY_REBIND_NE_PRODUCTIVE_FLATTEN_PROOF=true",
        "CANONICAL_IDENTITY_REBIND_NE_COVER_USDC=true",
        "CANONICAL_IDENTITY_REBIND_NE_USD_EQUALS_USDC_PROOF=true",
        "BTC_HISTORICAL_ROWS_EVIDENCE_NE_CURRENT_SUI_STATE=true",
        "SUI_CTVAL_METADATA_NE_EXCHANGE_POSITION_VALUE=true",
        "CTVAL_1_CTVALCCY_SUI_NE_ONE_CONTRACT_EQUALS_ONE_SUI=true",
        "FUTURES_XPERP_LINEAR_FIELD_EQUALITY_NE_BROADER_PRODUCT_COMPATIBILITY=true",
        "COMPOSITION_RISK_COMPLETION_NE_LIVE_READINESS=true",
        "NO_NEW_GET=true",
        "NO_POST=true",
        "THIS_PERSIST_RUNTIME_CALLS=false",
        "THIS_PERSIST_PUBLIC_GETS=false",
        "THIS_PERSIST_AUTHENTICATED_CALLS=false",
        "THIS_PERSIST_POST_CALLS=false",
        "HARD_STOP_AFTER_THIS_TASK=true",
        "HARD_STOP_AFTER_PR=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
    )
    for marker in required:
        assert marker in section, f"missing Z2BY marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nCAN_SUBMIT_ORDER_TODAY=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nONE_CONTRACT_EQUALS_ONE_SUI=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nMULTI_FUTURE_AUTHORIZED=true\n",
        "\nHISTORICAL_BTC_EVIDENCE_REWRITTEN=true\n",
        "\nZ2BX_TEXT_REWRITTEN=true\n",
        "\nNO_COMPOSITION_RECOMPUTED=false\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2BY marker present: {marker!r}"


def test_z2by_map_of_truth_remains_navigation_only_without_z2by_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2BY |" not in mot
