"""§11.13.5.Z2CA P7.3 flatten-precondition reobservation persist.

Docs/governance invariants only. Records the fresh SUI position-state
GET already executed under the P7.3 Owner-GO and the bounded
absent/not-returned adjudication. Does not authorize live, testnet,
canary, flatten execute, Cover, P7.4, or P7.5. Does not rewrite Z2AX,
Z2BC, Z2BY, or Z2BZ. Does not promote empty data or NOT_OBSERVED to
position-zero.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AX_HEADING = "### 11.13.5.Z2AX Post-Z2AW fresh target-position observation persist"
Z2BC_HEADING = "### 11.13.5.Z2BC Post-Z2BB fresh target-position runtime reobservation persist"
Z2BZ_HEADING = (
    "### 11.13.5.Z2BZ Post-Z2BY P7.2 Category-C bounded closure "
    "(BOUND; CONTRACT CLOSURE ONLY; NOT UNIVERSAL ABSENCE; NOT POSITION ZERO; "
    "NOT SUI RUNTIME GET; NOT FLATTEN; NOT LIVE; NOT COVER; NOT RISK)"
)
Z2CA_HEADING = (
    "### 11.13.5.Z2CA Post-Z2BZ P7.3 flatten precondition and fresh SUI "
    "position-state reobservation"
)
Z2CB_HEADING = (
    "### 11.13.5.Z2CB Post-Z2CA P7.4 productive flatten provability bounded forensic adjudication"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "SECTION_11_13_5_POST_Z2BZ_P7_3_FLATTEN_PRECONDITION_AND_FRESH_POSITION_STATE_REOBSERVATION_ONLY"
BASELINE_SHA = "235374935b4ee183a136fb120d7323d29e62cccd"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ca_section(text: str) -> str:
    start = text.find(Z2CA_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CA heading"
    end = text.find(Z2CB_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CB boundary after Z2CA"
    return text[start:end]


def _z2ax_section(text: str) -> str:
    start = text.find(Z2AX_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AX heading"
    end = text.find("### 11.13.5.Z2AY", start)
    assert end > start, "missing §11.13.5.Z2AY boundary after Z2AX"
    return text[start:end]


def _z2bc_section(text: str) -> str:
    start = text.find(Z2BC_HEADING)
    assert start >= 0, "missing §11.13.5.Z2BC heading"
    end = text.find("### 11.13.5.Z2BD", start)
    assert end > start, "missing §11.13.5.Z2BD boundary after Z2BC"
    return text[start:end]


def _z2bz_section(text: str) -> str:
    start = text.find(Z2BZ_HEADING)
    assert start >= 0, "missing §11.13.5.Z2BZ heading"
    end = text.find(Z2CA_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CA boundary after Z2BZ"
    return text[start:end]


def test_z2ca_heading_is_unique_and_follows_z2bz() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CA_HEADING) == 1
    z2ax = text.find(Z2AX_HEADING)
    z2bc = text.find(Z2BC_HEADING)
    z2bz = text.find(Z2BZ_HEADING)
    z2ca = text.find(Z2CA_HEADING)
    z2cb = text.find(Z2CB_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2ax < z2bc < z2bz < z2ca < z2cb < ladder


def test_z2ax_historical_btc_observation_was_not_rewritten() -> None:
    section = _z2ax_section(_read(MASTER_RUNBOOK))
    assert "TARGET_INSTRUMENT=BTC-USD_UM_XPERP-310404" in section
    assert "POSITION_ENDPOINT=GET /api/v5/account/positions" in section
    assert "POSITION_CAPTURE_TS=2026-08-23T21:37:11.803951Z" in section
    assert "POSITION_CONSUMER_RESULT=TARGET_INSTRUMENT_NOT_OBSERVED" in section
    assert "TARGET_POSITION_NONZERO=false" in section
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=OBSERVED_NONZERO_TARGET_POSITION" in section
    assert "SUI-USD_UM_XPERP-310404" not in section


def test_z2bc_historical_btc_not_observed_was_not_rewritten() -> None:
    section = _z2bc_section(_read(MASTER_RUNBOOK))
    assert "TARGET_INSTRUMENT=BTC-USD_UM_XPERP-310404" in section
    assert "POSITION_ENDPOINT=GET /api/v5/account/positions" in section
    assert "POSITION_CAPTURE_TS=2026-08-24T15:19:06.293270Z" in section
    assert "POSITION_CONSUMER_RESULT=TARGET_INSTRUMENT_NOT_OBSERVED" in section
    assert "EMPTY_DATA_IS_ZERO=false" in section
    assert "ABSENT_TARGET_ROW_IS_ZERO=false" in section
    assert "SUI-USD_UM_XPERP-310404" not in section


def test_z2bz_historical_slice_was_not_rewritten() -> None:
    section = _z2bz_section(_read(MASTER_RUNBOOK))
    assert "CATEGORY_C_BOUNDED_CLAIM_STATUS=CLOSED" in section
    assert "CATEGORY_C_POSITION_ZERO_PROVEN=false" in section
    assert "P7_3_STARTED=false" in section
    assert "P7_4_STARTED=false" in section
    assert "\nP7_3_STARTED=true\n" not in section


def test_z2ca_docs_bind_sui_reobservation_without_zero_or_flatten() -> None:
    section = _z2ca_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CA_POST_Z2BZ_P7_3_FLATTEN_PRECONDITION_AND_FRESH_POSITION_STATE_REOBSERVATION_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=Z2CA_P7_3_FLATTEN_PRECONDITION_REOBSERVATION_SSOT_PERSIST_DOCS_ONLY",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "PREDECESSOR_SLICE=11.13.5.Z2BZ",
        "Z2BZ_TEXT_REWRITTEN=false",
        "Z2BC_TEXT_REWRITTEN=false",
        "Z2AX_TEXT_REWRITTEN=false",
        "BTC_EVIDENCE_PROMOTED_TO_SUI=false",
        "P7_1_STATUS=CLOSED",
        "P7_2_STATUS=CLOSED",
        "P7_3_STARTED=true",
        "P7_3_STATUS=CLOSED",
        "P7_4_STARTED=false",
        "P7_5_STARTED=false",
        "Z2AX_INSTRUMENT_SCOPE=BTC-USD_UM_XPERP-310404",
        "Z2AX_TIME_SCOPE=2026-08-23T21:37:11.803951Z",
        "Z2AX_POSITION_CLAIM=TARGET_INSTRUMENT_NOT_OBSERVED",
        "Z2AX_OBSERVED_NONZERO_TARGET_POSITION_MEANING=UNSATISFIED_FLATTEN_PRECONDITION_RESIDUAL_NOT_AN_OBSERVED_NONZERO_FACT",
        "Z2BC_INSTRUMENT_SCOPE=BTC-USD_UM_XPERP-310404",
        "Z2BC_TIME_SCOPE=2026-08-24T15:19:06.293270Z/2026-08-24T15:19:06.508706Z",
        "Z2BC_POSITION_CLAIM=TARGET_INSTRUMENT_NOT_OBSERVED",
        "Z2BC_EMPTY_DATA_IS_ZERO=false",
        "HISTORICAL_Z2AX_REUSED_AS_CURRENT_PROOF=false",
        "HISTORICAL_Z2BC_REUSED_AS_CURRENT_PROOF=false",
        "POSITION_STATE_REPO_PATH_STATUS=CANONICALLY_PROVEN",
        "POSITION_STATE_ENDPOINT=GET /api/v5/account/positions",
        "POSITION_STATE_QUERY_SCOPE=NONE_PATH_ONLY_NO_INSTID_FILTER",
        "POSITION_STATE_AUTH_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY",
        "GET_EXECUTED_UNDER_THIS_OWNER_GO=true",
        "POSITION_STATE_GET_COUNT=1",
        "TARGET_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "CURRENT_CANONICAL_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "CAPTURE_STARTED_UTC=2026-08-25T03:09:39.455527Z",
        "CAPTURE_ENDED_UTC=2026-08-25T03:09:39.746458Z",
        "HTTP_STATUS=200",
        "OKX_CODE=0",
        "BODY_SHA256=fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a",
        "POSITION_ROW_COUNT=0",
        "POSITION_DATA_ARRAY_EMPTY=true",
        "POSITION_CONSUMER_RESULT=TARGET_INSTRUMENT_NOT_OBSERVED",
        "CURRENT_TARGET_POSITION_STATE=ABSENT_OR_NOT_RETURNED_NOT_EQUIVALENT_TO_ZERO",
        "CURRENT_TARGET_POSITION_QTY=null",
        "EMPTY_EQUALS_ZERO=false",
        "EMPTY_DATA_IS_ZERO=false",
        "ABSENT_TARGET_ROW_IS_ZERO=false",
        "UNIVERSAL_POSITION_ABSENCE_PROVEN=false",
        "NOT_OBSERVED_NE_POSITION_ZERO=true",
        "ABSENT_OR_NOT_RETURNED_NE_PROVEN_ZERO=true",
        "FLATTEN_PRECONDITION_STATUS=UNRESOLVED_FAIL_CLOSED",
        "PRODUCTIVE_FLATTEN_REQUIRED_BY_CURRENT_PROOF=false",
        "PRODUCTIVE_FLATTEN_EXECUTED=false",
        "P7_4_SEPARATION=EXPLICIT_SEPARATE_OWNER_GO_REQUIRED_FOR_ANY_PRODUCTIVE_FLATTEN",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "MULTI_FUTURE_AUTHORIZED=false",
        "MAX_POSITIONS_EFFECTIVE=1",
        "POSITION_COUNT_LIMIT=1",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "USD_USDC_OPERATOR_STATUS=UNPROVEN",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "HARD_STOP_AFTER_PR=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2CA marker: {marker}"
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
        "\nP7_4_STARTED=true\n",
        "\nP7_5_STARTED=true\n",
        "\nEMPTY_EQUALS_ZERO=true\n",
        "\nBTC_EVIDENCE_PROMOTED_TO_SUI=true\n",
        "\nCURRENT_TARGET_POSITION_STATE=PROVEN_ZERO\n",
        "\nCURRENT_TARGET_POSITION_STATE=PROVEN_NONZERO\n",
        "\nUNIVERSAL_POSITION_ABSENCE_PROVEN=true\n",
        "\nPRODUCTIVE_FLATTEN_EXECUTED=true\n",
        "\nZ2AX_TEXT_REWRITTEN=true\n",
        "\nZ2BC_TEXT_REWRITTEN=true\n",
        "\nZ2BZ_TEXT_REWRITTEN=true\n",
        "\nMULTI_FUTURE_AUTHORIZED=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2CA marker present: {marker!r}"


def test_z2ca_map_of_truth_remains_navigation_only_without_z2ca_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2CA |" not in mot
    assert "§11.13.5.Z2BZ |" not in mot
