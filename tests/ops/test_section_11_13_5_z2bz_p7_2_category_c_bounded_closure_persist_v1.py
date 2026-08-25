"""§11.13.5.Z2BZ P7.2 Category-C bounded closure persist.

Docs/governance invariants only. Records the bounded live-relevant
Category-C contract after the Z2BY SUI identity rebind. Does not
authorize live, testnet, canary, flatten, Cover, GET, POST, P7.3, P7.4,
or P7.5. Does not rewrite Z2BY or the historical BTC Z2BB window.
Does not promote empty windows to universal absence or position-zero.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2BB_HEADING = (
    "### 11.13.5.Z2BB Post-Z2BA Category C productive read-only open "
    "algo-pending runtime GET observation persist"
)
Z2BY_HEADING = (
    "### 11.13.5.Z2BY Post-Z2BX P7.1 canonical SUI identity rebind and fail-closed validation"
)
Z2BZ_HEADING = (
    "### 11.13.5.Z2BZ Post-Z2BY P7.2 Category-C bounded closure "
    "(BOUND; CONTRACT CLOSURE ONLY; NOT UNIVERSAL ABSENCE; NOT POSITION ZERO; "
    "NOT SUI RUNTIME GET; NOT FLATTEN; NOT LIVE; NOT COVER; NOT RISK)"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "SECTION_11_13_5_POST_Z2BY_P7_2_CATEGORY_C_BOUNDED_CLOSURE_ONLY"
BASELINE_SHA = "7062a032fe80491a8749a1641d6f7ec85b50506c"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2bz_section(text: str) -> str:
    start = text.find(Z2BZ_HEADING)
    assert start >= 0, "missing §11.13.5.Z2BZ heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2BZ"
    return text[start:end]


def _z2by_section(text: str) -> str:
    start = text.find(Z2BY_HEADING)
    assert start >= 0, "missing §11.13.5.Z2BY heading"
    end = text.find(Z2BZ_HEADING, start)
    assert end > start, "missing §11.13.5.Z2BZ boundary after Z2BY"
    return text[start:end]


def _z2bb_section(text: str) -> str:
    start = text.find(Z2BB_HEADING)
    assert start >= 0, "missing §11.13.5.Z2BB heading"
    end = text.find("### 11.13.5.Z2BC", start)
    assert end > start, "missing §11.13.5.Z2BC boundary after Z2BB"
    return text[start:end]


def test_z2bz_heading_is_unique_and_follows_z2by() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2BZ_HEADING) == 1
    z2bb = text.find(Z2BB_HEADING)
    z2by = text.find(Z2BY_HEADING)
    z2bz = text.find(Z2BZ_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2bb < z2by < z2bz < ladder


def test_z2by_historical_slice_was_not_rewritten() -> None:
    section = _z2by_section(_read(MASTER_RUNBOOK))
    assert "CURRENT_CANONICAL_INSTRUMENT=SUI-USD_UM_XPERP-310404" in section
    assert "SUI_CANONICAL_REBIND_EXECUTED=true" in section
    assert "CATEGORY_C_UNIVERSAL_ABSENCE_PROVEN=false" in section
    assert (
        "OWNER_GO=SECTION_11_13_5_POST_Z2BX_P7_1_CANONICAL_SUI_REBIND_IMPLEMENTATION_AND_FAIL_CLOSED_VALIDATION_ONLY"
        in section
    )
    assert "\nLIVE_AUTHORIZED=true\n" not in section
    assert "P7_2_STATUS=CLOSED" not in section


def test_z2bb_btc_window_remains_historical_and_not_universal() -> None:
    section = _z2bb_section(_read(MASTER_RUNBOOK))
    assert "TARGET_INSTRUMENT=BTC-USD_UM_XPERP-310404" in section
    assert "CATEGORY_C_RUNTIME_OBSERVATION_STATUS=TARGET_CATEGORY_C_NOT_OBSERVED" in section
    assert "UNIVERSAL_CATEGORY_C_ABSENCE_PROVEN=false" in section
    assert "EMPTY_INFERRED=false" in section
    assert "CAPTURE_STARTED_UTC=2026-08-24T14:50:19.999409Z" in section
    assert "SUI-USD_UM_XPERP-310404" not in section


def test_z2bz_docs_bind_bounded_category_c_without_live_or_flatten() -> None:
    section = _z2bz_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2BZ_POST_Z2BY_P7_2_CATEGORY_C_BOUNDED_CLOSURE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=Z2BZ_CATEGORY_C_BOUNDED_CONTRACT_CLOSURE_SSOT_PERSIST_DOCS_ONLY",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "PREDECESSOR_SLICE=11.13.5.Z2BY",
        "Z2BY_TEXT_REWRITTEN=false",
        "Z2BB_TEXT_REWRITTEN=false",
        "HISTORICAL_BTC_EVIDENCE_REWRITTEN=false",
        "BTC_EVIDENCE_PROMOTED_TO_SUI=false",
        "P7_1_STATUS=CLOSED",
        "P7_2_STATUS=CLOSED",
        "P7_3_STARTED=false",
        "P7_4_STARTED=false",
        "P7_5_STARTED=false",
        "CURRENT_CANONICAL_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "DEFAULT_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "CANARY_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "CATEGORY_C_DEFINITION=TARGET_INSTRUMENT_SCOPED_NAMED_OPEN_ALGO_PENDING_OBSERVATION",
        "CATEGORY_C_SCOPE_CLASS=TARGET_INSTRUMENT_SCOPED",
        "CATEGORY_C_NOT_ACCOUNT_UNIVERSAL=true",
        "CATEGORY_C_INSTRUMENT_PARAMETERIZED=true",
        "EMPTY_EQUALS_ZERO=false",
        "EMPTY_EQUALS_UNIVERSAL_ABSENCE=false",
        "NOT_OBSERVED_EQUALS_POSITION_ZERO=false",
        "BTC_ONLY_WINDOW_EVIDENCE_EQUALS_SUI_ABSENCE_PROOF=false",
        "BTC_WINDOW_PROMOTED_TO_SUI_PROOF=false",
        "Z2BB_TARGET_INSTRUMENT=BTC-USD_UM_XPERP-310404",
        "CATEGORY_C_PRIOR_BTC_ONLY_EVIDENCE_STATUS=HISTORICAL_WINDOW_BOUNDED_NOT_CURRENT_SUI_PROOF",
        "CATEGORY_C_CURRENT_SUI_RUNTIME_OBSERVATION=UNPROVEN",
        "CATEGORY_C_CURRENT_SUI_EVIDENCE_STATUS=UNPROVEN_NO_SUI_ALGO_PENDING_GET_IN_THIS_IDENTITY",
        "CATEGORY_C_REQUIRED_CLAIM=CURRENT_IDENTITY_SCOPED_NAMED_ALGO_PENDING_OBSERVATION_FOR_SUI-USD_UM_XPERP-310404_VIA_GET_ORDERS_ALGO_PENDING_NOT_UNIVERSAL_ABSENCE_NOT_POSITION_ZERO",
        "CATEGORY_C_BOUNDED_CLAIM_STATUS=CLOSED",
        "CATEGORY_C_UNIVERSAL_ABSENCE_PROVEN=false",
        "CATEGORY_C_POSITION_ZERO_PROVEN=false",
        "UNIVERSAL_CATEGORY_C_ABSENCE_PROVEN=false",
        "CATEGORY_C_BOUNDED_CLOSURE_CONSUMED_BY=LATER_FLATTEN_AND_LIVE_GATES_ONLY",
        "CATEGORY_C_BOUNDED_CLOSURE_CONSUMED_BY_COMPOSITION=false",
        "CATEGORY_C_BOUNDED_CLOSURE_CONSUMED_BY_RISK=false",
        "CATEGORY_C_BOUNDED_CLOSURE_CONSUMED_BY_COVER=false",
        "CATEGORY_C_CLOSURE_NE_FLATTEN_COMPLETE=true",
        "CATEGORY_C_CLOSURE_NE_LIVE_AUTHORIZED=true",
        "CATEGORY_C_CLOSURE_NE_RISK_OR_COVER_COMPLETE=true",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "MULTI_FUTURE_AUTHORIZED=false",
        "MAX_POSITIONS_EFFECTIVE=1",
        "POSITION_COUNT_LIMIT=1",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "USD_USDC_OPERATOR_STATUS=UNPROVEN",
        "RISK_ENVELOPE_NUMERIC_STATUS=UNINSTANTIATED",
        "ONE_CONTRACT_EQUALS_ONE_SUI=false",
        "EXCHANGE_POSITION_VALUE_STATUS=UNPROVEN",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "RUNTIME_API_CALLS=0",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "HARD_STOP_AFTER_PR=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2BZ marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nONE_CONTRACT_EQUALS_ONE_SUI=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nMULTI_FUTURE_AUTHORIZED=true\n",
        "\nBTC_EVIDENCE_PROMOTED_TO_SUI=true\n",
        "\nEMPTY_EQUALS_ZERO=true\n",
        "\nCATEGORY_C_UNIVERSAL_ABSENCE_PROVEN=true\n",
        "\nCATEGORY_C_POSITION_ZERO_PROVEN=true\n",
        "\nP7_3_STARTED=true\n",
        "\nP7_4_STARTED=true\n",
        "\nP7_5_STARTED=true\n",
        "\nZ2BY_TEXT_REWRITTEN=true\n",
        "\nZ2BB_TEXT_REWRITTEN=true\n",
        "\nBTC_WINDOW_PROMOTED_TO_SUI_PROOF=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2BZ marker present: {marker!r}"


def test_z2bz_map_of_truth_remains_navigation_only_without_z2bz_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2BZ |" not in mot
    assert "§11.13.5.Z2BY |" not in mot
