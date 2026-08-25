"""§11.13.5.Z2CC P7.5 live-gate reconciliation forensic persist.

Docs/governance invariants only. Records the bounded SUI live-readiness
matrix without runtime, GET, POST, flatten, Cover, live, testnet, or
canary authorization. Does not rewrite Z2CB. Does not promote empty
data or NOT_OBSERVED to position-zero. Does not infer live readiness
from Composition, Risk identity, Rebind, Category C, P7.3, or P7.4
individually.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CB_HEADING = (
    "### 11.13.5.Z2CB Post-Z2CA P7.4 productive flatten provability bounded forensic adjudication"
)
Z2CC_HEADING = (
    "### 11.13.5.Z2CC Post-Z2CB P7.5 live-gate reconciliation bounded forensic adjudication"
)
Z2CD_HEADING = "### 11.13.5.Z2CD Post-Z2CC P8 final forensic audit persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "SECTION_11_13_5_POST_Z2CB_P7_5_LIVE_GATE_RECONCILIATION_READ_ONLY_FORENSIC_ADJUDICATION_ONLY"
)
BASELINE_SHA = "2befeb0627d58a04c2a78639af0a1213a2b0cd19"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cc_section(text: str) -> str:
    start = text.find(Z2CC_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CC heading"
    end = text.find(Z2CD_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CD boundary after Z2CC"
    return text[start:end]


def _z2cb_section(text: str) -> str:
    start = text.find(Z2CB_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CB heading"
    end = text.find(Z2CC_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CC boundary after Z2CB"
    return text[start:end]


def test_z2cc_heading_is_unique_and_follows_z2cb() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CC_HEADING) == 1
    z2cb = text.find(Z2CB_HEADING)
    z2cc = text.find(Z2CC_HEADING)
    z2cd = text.find(Z2CD_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cb < z2cc < z2cd < ladder


def test_z2cb_historical_slice_was_not_rewritten() -> None:
    section = _z2cb_section(_read(MASTER_RUNBOOK))
    assert "P7_4_STATUS=CLOSED_FAIL_CLOSED_NO_MUTATION" in section
    assert "P7_5_STARTED=false" in section
    assert "FLATTEN_PROOF_STATUS=UNRESOLVED_FAIL_CLOSED" in section
    assert "EMPTY_EQUALS_ZERO=false" in section
    assert "EXECUTION_AUTHORIZED=false" in section
    assert "\nP7_5_STARTED=true\n" not in section
    assert "Z2CC" not in section


def test_z2cc_docs_bind_forensic_fail_closed_without_runtime() -> None:
    section = _z2cc_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CC_POST_Z2CB_P7_5_LIVE_GATE_RECONCILIATION_READ_ONLY_FORENSIC_ADJUDICATION_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "PERSIST_CLASS=Z2CC_P7_5_LIVE_GATE_RECONCILIATION_FORENSIC_SSOT_PERSIST_DOCS_ONLY",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "ORIGIN_MAIN_SUPERSESSION_STATUS=NONE",
        "PREDECESSOR_SLICE=11.13.5.Z2CB",
        "Z2CB_TEXT_REWRITTEN=false",
        "Z2CA_TEXT_REWRITTEN=false",
        "BTC_EVIDENCE_PROMOTED_TO_SUI=false",
        "P7_3_STATUS=CLOSED",
        "P7_4_STATUS=CLOSED_FAIL_CLOSED_NO_MUTATION",
        "P7_5_STARTED=true",
        "P7_5_STATUS=CLOSED_FAIL_CLOSED_WITHOUT_RUNTIME",
        "P8_STARTED=false",
        "GET_EXECUTED_UNDER_THIS_OWNER_GO=false",
        "CURRENT_CANONICAL_INSTRUMENT=SUI-USD_UM_XPERP-310404",
        "P7_3_FLATTEN_PRECONDITION_STATUS=UNRESOLVED_FAIL_CLOSED",
        "P7_3_TARGET_POSITION_ZERO_PROVEN=false",
        "P7_3_TARGET_POSITION_NONZERO_PROVEN=false",
        "P7_4_FLATTEN_PROOF_STATUS=UNRESOLVED_FAIL_CLOSED",
        "P7_4_PRODUCTIVE_URLLIB_SEND_IMPLEMENTED=false",
        "NO_P7_3_REINTERPRETATION=true",
        "NO_P7_4_REINTERPRETATION=true",
        "NO_EMPTY_AS_ZERO_FROM_P7_3_OR_P7_4=true",
        "INTERNAL_RISK_PROGRAM_STATUS=BOUND_COMPOSITION_NUMERIC",
        "RISK_ENVELOPE_STATUS=IDENTITY_BOUND_NUMERIC_UNINSTANTIATED",
        "USD_USDC_OPERATOR_STATUS=UNPROVEN",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "COVER_NEGATIVE_CONTRACT=true",
        "COVER_USDC_REQUIRED_FOR_LIVE=true_FOR_COVER_CONSUMING_LIVE_OR_CANARY_FUNDING_OR_EXPOSURE_INSTANTIATION",
        "COVER_USDC_REQUIRED_TO_CLOSE_P7_5=false",
        "COVER_USDC_BLOCKS_SPECIFIC_LIVE_READINESS_EDGE=true",
        "COVER_USDC_IS_UNIQUE_EARLIEST_DEPENDENCY=false",
        "ACCOUNT_MODE_STATUS=SATISFIED_HISTORICAL_ACCOUNT_WIDE_GET_acctLv=2_NOT_REOBSERVED_POST_SUI",
        "POSITION_MODE_STATUS=SATISFIED_HISTORICAL_ACCOUNT_WIDE_GET_posMode=net_NOT_REOBSERVED_POST_SUI",
        "LEVERAGE_STATUS=UNPROVEN_BTC_SET_ACCOUNT_LEVERAGE_3_NOT_TRANSFERRED_TO_SUI",
        "IMPLEMENTATION_RUNBOOK_DRIFT_CLASS=NONE_ON_STANDING_LIVE_FLAGS",
        "LIVE_GATE_TOTAL_COUNT=40",
        "LIVE_GATE_SATISFIED_COUNT=14",
        "LIVE_GATE_PROVEN_COUNT=3",
        "LIVE_GATE_UNPROVEN_COUNT=14",
        "LIVE_GATE_BLOCKED_COUNT=3",
        "LIVE_GATE_FAIL_COUNT=3",
        "LIVE_GATE_SEPARATE_OWNER_GO_COUNT=3",
        "LIVE_GATE_UNRESOLVED_COUNT=23",
        "LIVE_GATE_MATRIX_STATUS=COMPLETE_FAIL_CLOSED_NOT_READY",
        "LIVE_READINESS_STATUS=FAIL_CLOSED_NOT_READY",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "NEXT_STEP_ADJUDICATION=A_P7_5_CAN_BE_CLOSED_AS_FAIL_CLOSED_WITHOUT_RUNTIME",
        "EARLIEST_UNRESOLVED_DEPENDENCY=NONE_BY_P3_POLICY_PARALLEL_UNRESOLVED_SET",
        "P3_INDEPENDENT_PARALLEL_TRACKS_POLICY=true",
        "EMPTY_EQUALS_ZERO=false",
        "P7_5_RECONCILIATION_IS_NOT_LIVE_AUTHORIZATION=true",
        "P7_5_RECONCILIATION_DOES_NOT_IMPLY_USD_EQUALS_USDC=true",
        "P7_5_RECONCILIATION_DOES_NOT_IMPLY_EMPTY_POSITION_RESPONSE_EQUALS_ZERO=true",
        "P7_5_RECONCILIATION_DOES_NOT_PROMOTE_IMPLEMENTATION_EXISTENCE_TO_EXECUTION_PROOF=true",
        "P7_5_RECONCILIATION_DOES_NOT_OVERRIDE_P7_4_FAIL_CLOSED_STATUS=true",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "HARD_STOP_AFTER_PR=true",
        "Z2CB_UNCHANGED=true",
        "RUNTIME_API_CALLS=0",
        "AUTHENTICATED_CALLS=0",
        "PUBLIC_GET_CALLS=0",
        "POST_CALLS=0",
        "POSITION_MUTATIONS=0",
        "ACCOUNT_MUTATIONS=0",
    )
    for marker in required:
        assert marker in section, f"missing Z2CC marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nP8_STARTED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nPRODUCTIVE_FLATTEN_EXECUTED=true\n",
        "\nEMPTY_EQUALS_ZERO=true\n",
        "\nBTC_EVIDENCE_PROMOTED_TO_SUI=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nZ2CB_TEXT_REWRITTEN=true\n",
        "\nONE_CONTRACT_EQUALS_ONE_SUI=true\n",
        "\nMULTI_FUTURE_AUTHORIZED=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2CC marker present: {marker!r}"


def test_z2cc_map_of_truth_remains_navigation_only_without_z2cc_ssot_row() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "§11.13.5.Z2CC |" not in mot
    assert "§11.13.5.Z2CB |" not in mot
