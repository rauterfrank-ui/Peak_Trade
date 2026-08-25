"""§11.13.5.Z2CB P7.4 productive flatten provability forensic persist.

Docs/governance invariants only. Records the reconstructed flatten
path and fail-closed execution adjudication. Does not authorize live,
testnet, canary, flatten execute, Cover, GET, POST, or P7.5. Does not
rewrite Z2CA. Does not promote empty data or NOT_OBSERVED to
position-zero.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CA_HEADING = (
    "### 11.13.5.Z2CA Post-Z2BZ P7.3 flatten precondition and fresh SUI "
    "position-state reobservation"
)
Z2CB_HEADING = (
    "### 11.13.5.Z2CB Post-Z2CA P7.4 productive flatten provability bounded forensic adjudication"
)
Z2CC_HEADING = (
    "### 11.13.5.Z2CC Post-Z2CB P7.5 live-gate reconciliation bounded forensic adjudication"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "SECTION_11_13_5_POST_Z2CA_P7_4_PRODUCTIVE_FLATTEN_PROVABILITY_"
    "BOUNDED_FORENSIC_ADJUDICATION_AND_CONDITIONAL_EXECUTION_ONLY"
)
BASELINE_SHA = "e410f5b413e33f8183fc2b15876755b8c1fe4be4"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cb_section(text: str) -> str:
    start = text.find(Z2CB_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CB heading"
    end = text.find(Z2CC_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CC boundary after Z2CB"
    return text[start:end]


def _z2ca_section(text: str) -> str:
    start = text.find(Z2CA_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CA heading"
    end = text.find(Z2CB_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CB boundary after Z2CA"
    return text[start:end]


def test_z2cb_heading_is_unique_and_follows_z2ca() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CB_HEADING) == 1
    z2ca = text.find(Z2CA_HEADING)
    z2cb = text.find(Z2CB_HEADING)
    z2cc = text.find(Z2CC_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2ca < z2cb < z2cc < ladder


def test_z2ca_historical_slice_was_not_rewritten() -> None:
    section = _z2ca_section(_read(MASTER_RUNBOOK))
    assert "P7_3_STATUS=CLOSED" in section
    assert "P7_4_STARTED=false" in section
    assert "P7_5_STARTED=false" in section
    assert "CURRENT_TARGET_POSITION_STATE=ABSENT_OR_NOT_RETURNED_NOT_EQUIVALENT_TO_ZERO" in section
    assert "EMPTY_EQUALS_ZERO=false" in section
    assert "FLATTEN_PRECONDITION_STATUS=UNRESOLVED_FAIL_CLOSED" in section
    assert "PRODUCTIVE_FLATTEN_REQUIRED_BY_CURRENT_PROOF=false" in section
    assert "\nP7_4_STARTED=true\n" not in section
    assert "Z2CB" not in section


def test_z2cb_docs_bind_forensic_fail_closed_without_mutation() -> None:
    section = _z2cb_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CB_POST_Z2CA_P7_4_PRODUCTIVE_FLATTEN_PROVABILITY_BOUNDED_FORENSIC_ADJUDICATION_AND_CONDITIONAL_EXECUTION_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=Z2CB_P7_4_PRODUCTIVE_FLATTEN_PROVABILITY_FORENSIC_SSOT_PERSIST_DOCS_ONLY",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "ORIGIN_MAIN_SUPERSESSION_STATUS=NONE",
        "PREDECESSOR_SLICE=11.13.5.Z2CA",
        "Z2CA_TEXT_REWRITTEN=false",
        "BTC_EVIDENCE_PROMOTED_TO_SUI=false",
        "P7_3_STATUS=CLOSED",
        "P7_4_STARTED=true",
        "P7_4_STATUS=CLOSED_FAIL_CLOSED_NO_MUTATION",
        "P7_5_STARTED=false",
        "GET_EXECUTED_UNDER_THIS_OWNER_GO=false",
        "PRE_MUTATION_POSITION_GET_COUNT=0",
        "POST_MUTATION_POSITION_GET_COUNT=0",
        "CURRENT_CANONICAL_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "FLATTEN_ENTRYPOINT=run_section_11_13_5_live_canary_minimum_exposure_v1 mode=flatten_execute",
        "FLATTEN_API_HOST=eea.okx.com",
        "FLATTEN_API_ENDPOINT=/api/v5/trade/order",
        "FLATTEN_HTTP_METHOD=POST",
        "FLATTEN_QTY_SOURCE=ABS_OBSERVED_POS_OR_POSSIZE_FIELD_FULL_FLATTEN_ONLY",
        "FLATTEN_QTY_UNIT=VENUE_POS_FIELD_COPIED_TO_SZ_NOT_INDEPENDENTLY_PROVEN_AS_SUI",
        "FLATTEN_EXECUTE_OWNER_GO_CANONICAL=SECTION_11_13_5_FLATTEN_EXECUTE_OWNER_GO",
        "THIS_P7_4_OWNER_GO_EQUALS_FLATTEN_EXECUTE_OWNER_GO_CANONICAL=false",
        "PRODUCTIVE_URLLIB_SEND_IMPLEMENTED=false",
        "EMPTY_EQUALS_ZERO=false",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "PRODUCTIVE_FLATTEN_REQUIRED_BY_CURRENT_PROOF=false",
        "PRODUCTIVE_FLATTEN_NOT_REQUIRED_PROVEN=false",
        "PRODUCTIVE_FLATTEN_REQUIRED_BY_CURRENT_PROOF_FALSE_NE_NOT_REQUIRED_PROVEN=true",
        "EXECUTION_PREREQUISITES=FAIL",
        "EXECUTION_AUTHORIZED=false",
        "PRODUCTIVE_FLATTEN_EXECUTED=false",
        "PRODUCTIVE_MUTATING_CALL_COUNT=0",
        "POST_EXECUTED=false",
        "FLATTEN_PROOF_STATUS=UNRESOLVED_FAIL_CLOSED",
        "ACCEPTED_POST_NE_FLATTEN_PROOF=true",
        "EMPTY_READBACK_NE_ZERO=true",
        "ONE_CONTRACT_EQUALS_ONE_SUI=false",
        "NO_BTC_TO_SUI_SEMANTIC_TRANSFER=true",
        "NO_QTY_INVENTION=true",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "MAX_POSITIONS_EFFECTIVE=1",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "HARD_STOP_AFTER_PR=true",
        "Z2CA_UNCHANGED=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2CB marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nONE_CONTRACT_EQUALS_ONE_SUI=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nPRODUCTIVE_FLATTEN_EXECUTED=true\n",
        "\nP7_5_STARTED=true\n",
        "\nEMPTY_EQUALS_ZERO=true\n",
        "\nBTC_EVIDENCE_PROMOTED_TO_SUI=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nEXECUTION_AUTHORIZED=true\n",
        "\nPRODUCTIVE_FLATTEN_NOT_REQUIRED_PROVEN=true\n",
        "\nZ2CA_TEXT_REWRITTEN=true\n",
        "\nPRODUCTIVE_URLLIB_SEND_IMPLEMENTED=true\n",
        "\nTHIS_P7_4_OWNER_GO_EQUALS_FLATTEN_EXECUTE_OWNER_GO_CANONICAL=true\n",
        "\nMULTI_FUTURE_AUTHORIZED=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2CB marker present: {marker!r}"


def test_z2cb_map_of_truth_remains_navigation_only_without_z2cb_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2CB |" not in mot
    assert "§11.13.5.Z2CA |" not in mot
