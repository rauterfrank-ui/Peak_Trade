"""§11.13.5.Z2AH API execution denomination PROVEN persist.

Docs/governance invariants only. Persists the already-completed
Z2AH adjudication: instrument-specific API denomination for
BTC-USD_UM_XPERP-310404 is PROVEN. Does not prove a 100:1 OEM-to-API
bridge, does not declare OEM 0.01 BTC wrong, does not award global API
precedence, does not instantiate COVER_USDC, does not prove settlement
PnL or live flatten, and does not start LF-10, submit orders, call OKX,
fund, or unlock Canary.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AI_HEADING = "### 11.13.5.Z2AI LF-10 read-only adjudication persist"
Z2AH_HEADING = "### 11.13.5.Z2AH API execution denomination PROVEN persist"
Z2AG_HEADING = "### 11.13.5.Z2AG Scoped API ctVal sizing authority split persist"
Z2AF_HEADING = "### 11.13.5.Z2AF LF-09 blocker-DAG re-adjudication persist"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_ACTION_NOT_"
    "AUTHORIZED_BY_THIS_PERSIST_Z2AH_API_EXECUTION_DENOMINATION_PROVEN_"
    "OEM_0_01_DOCUMENTARY_QUARANTINED_100_TO_1_BRIDGE_INFERRED_NOT_PROVEN_"
    "NO_OEM_DEFEAT_NO_GLOBAL_API_WINS_COVER_USDC_UNINSTANTIATED_SETTLEMENT_"
    "PNL_UNPROVEN_LIVE_FLATTEN_UNPROVEN_NO_LF10_NO_FLATTEN_CONTINUATION_"
    "NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_"
    "AUTHORIZED"
)
CONSUMED_Z2AG_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_ACTION_NOT_"
    "AUTHORIZED_BY_THIS_PERSIST_Z2AG_SCOPED_API_CTVAL_SIZING_SPLIT_"
    "DOCUMENTARY_FACE_VALUE_CONFLICT_REMAINS_CONFLICTED_OEM_SPEC_NOT_"
    "DEFEATED_NO_GLOBAL_API_WINS_COVER_USDC_UNINSTANTIATED_SETTLEMENT_"
    "PNL_UNPROVEN_LIVE_FLATTEN_UNPROVEN_NO_LF10_NO_FLATTEN_CONTINUATION_"
    "NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_"
    "AUTHORIZED"
)
OWNER_GO = "Z2AH_API_EXECUTION_DENOMINATION_PROVEN_PERSIST"
BASELINE_SHA = "458affc2764907c3d24b5bd2c6de05287c96c221"
API_SIZING_AUTHORITY = "INSTRUMENT_SPECIFIC_CTVAL_DO_NOT_ASSUME_OEM_OR_PRODUCT_CONTRACT_SIZE"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ah_section(text: str) -> str:
    start = text.find(Z2AH_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AH heading"
    end = text.find(Z2AI_HEADING, start)
    assert end > start, "missing §11.13.5.Z2AI boundary after Z2AH"
    return text[start:end]


def test_z2ah_heading_is_unique_and_follows_z2ag() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AH_HEADING) == 1
    z2af = text.find(Z2AF_HEADING)
    z2ag = text.find(Z2AG_HEADING)
    z2ah = text.find(Z2AH_HEADING)
    z2ai = text.find(Z2AI_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2af < z2ag < z2ah < z2ai < ladder


def test_z2ah_docs_bind_api_denomination_proven_without_100_to_1_or_oem_defeat() -> None:
    section = _z2ah_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=Z2AH_API_EXECUTION_DENOMINATION_PROVEN_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP=LF_09",
        "TARGET_INSTID=BTC-USD_UM_XPERP-310404",
        "API_EXECUTION_DENOMINATION_STATUS=PROVEN",
        "API_EXECUTION_CTVAL=0.0001_BTC",
        "API_EXECUTION_CTVAL_NUMERIC=0.0001",
        "API_EXECUTION_CTVAL_CCY=BTC",
        "API_EXECUTION_CTMULT=1",
        "API_EXECUTION_LOTSZ=1",
        "API_EXECUTION_MINSZ=1",
        "API_EXECUTION_SZ_UNIT=NUMBER_OF_API_CONTRACTS",
        f"API_SIZING_AUTHORITY={API_SIZING_AUTHORITY}",
        "HARDCODED_OEM_OR_PRODUCT_CONTRACT_SIZE_IS_NOT_API_SIZING_AUTHORITY=true",
        "UNIVERSAL_XPERP_DENOMINATION_PROVEN=false",
        "UNIVERSAL_XPERP_DENOMINATION_ASSUMED=false",
        "PROVEN_BASIS_EXACT_TARGET_INSTRUMENTS_GET=true",
        "PROVEN_BASIS_OKX_API_CTVAL_SZ_NOTIONAL_PNL_SEMANTICS=true",
        "PROVEN_BASIS_XPERPS_GUIDE_AND_MARGIN_0_0001_BTC=true",
        "PROVEN_BASIS_OKX_AGENT_TRADE_KIT_CTVAL_LOOKUP_DO_NOT_ASSUME_CONTRACT_SIZES=true",
        "PROVEN_BASIS_IS_OEM_TO_API_100_TO_1_BRIDGE=false",
        "PROVEN_BASIS_IS_OPERATIVE_CONVERSION_FROM_0_01_OVER_0_0001=false",
        "OEM_DOCUMENTARY_CONTRACT_SIZE=0.01_BTC",
        "OEM_DOCUMENTARY_FACE_VALUE_STATUS=RETAINED_NOT_ADJUDICATED_WRONG",
        "OEM_SPEC_CONTRACT_SIZE=0.01_BTC",
        "OEM_SPEC_WRONG=false",
        "OEM_SPEC_DECLARED_WRONG=false",
        "OEM_SPEC_DECLARED_STALE=false",
        "OEM_SPEC_DECLARED_TYPO=false",
        "OEM_SPEC_DECLARED_LEGACY=false",
        "OEM_DOCUMENTARY_CONTRACT_SIZE_DELETED=false",
        "GLOBAL_API_WINS=false",
        "GLOBAL_API_WINS_OVER_OEM=false",
        "SILENT_OEM_DEFEAT=false",
        "NO_SILENT_API_PRECEDENCE_OVER_OEM_SPEC=true",
        "FACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=false",
        "DOCUMENTARY_FACE_VALUE_CONFLICT=CONFLICTED",
        "OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN",
        "OEM_TO_API_100_TO_1_BRIDGE_PROVEN=false",
        "OEM_TO_API_100_TO_1_BRIDGE_REQUIRED_FOR_API_SIZING=false",
        "OEM_TO_API_100_TO_1_BRIDGE_ALLOWED_FOR_API_SIZING=false",
        "OEM_CONTRACT_EQUALS_100_API_CONTRACTS_PROVEN=false",
        "OPERATIVE_CONVERSION_FROM_0_01_OVER_0_0001=false",
        "CONFLICT_FACTOR_IS_OPERATIVE_API_SIZING_CONVERSION=false",
        "FACE_VALUE_CONFLICT_AS_API_NUMERIC_SAFETY_BLOCKER=CLOSED",
        "FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED",
        "FAIL_CLOSED_CTVAL_GUARD_STATUS=REQUIRED",
        "MISSING_CTVAL_FAIL_CLOSED=true",
        "INVALID_CTVAL_FAIL_CLOSED=true",
        "NON_POSITIVE_CTVAL_FAIL_CLOSED=true",
        "NON_INSTRUMENT_SPECIFIC_CTVAL_FAIL_CLOSED=true",
        "UNBOUND_CTVAL_FAIL_CLOSED=true",
        "HARDCODED_OEM_CONTRACT_SIZE_FAIL_CLOSED=true",
        "COVER_USDC=UNINSTANTIATED",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "SETTLEMENT_PNL=UNPROVEN",
        "SETTLEMENT_PNL_STATUS=UNPROVEN",
        "USD_TO_USDC_OPERATOR=UNPROVEN",
        "USD_USDC_OPERATOR=UNPROVEN",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "LIVE_FLATTEN_PROVABILITY_REMAINS=UNPROVEN_HARD_STOP",
        "NO_USD_EQUALS_USDC=true",
        "USD_EQUALS_USDC_ASSUMED=false",
        "LF_10_AUTHORIZED=false",
        "LF_10_STARTED=false",
        "LF10_EXECUTED=false",
        "NO_LF10_ANALYSIS=true",
        "NO_LF10_IMPLEMENTATION=true",
        "NO_RUNTIME_CODE_CHANGE=true",
        "NO_TRADING_LOGIC_CHANGE=true",
        "NO_OKX_API_CALL=true",
        "NO_POST=true",
        "NO_ORDER=true",
        "NO_FUNDING=true",
        "NO_SUPPORT_CONTACT=true",
        "NO_ALLOWLIST_EXPANSION=true",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUPPORT_CONTACT_AUTHORIZED=false",
        "DOCS_PERSIST_IS_NOT_ADMISSIBLE_PRODUCTIVE_EVIDENCE=true",
        "NO_CAPABILITY_ADVANCEMENT=true",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        "EARLIEST_NUMERIC_SAFETY_BLOCKER=COVER_USDC_UNINSTANTIATED",
        "PARALLEL_NUMERIC_ROOT=COVER_USDC_UNINSTANTIATED",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AH marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nLF_10_AUTHORIZED=true\n",
        "\nLF_10_STARTED=true\n",
        "\nLF10_EXECUTED=true\n",
        "\nOEM_SPEC_WRONG=true\n",
        "\nOEM_SPEC_DECLARED_WRONG=true\n",
        "\nOEM_SPEC_DECLARED_STALE=true\n",
        "\nOEM_SPEC_DECLARED_TYPO=true\n",
        "\nOEM_SPEC_DECLARED_LEGACY=true\n",
        "\nOEM_DOCUMENTARY_CONTRACT_SIZE_DELETED=true\n",
        "\nGLOBAL_API_WINS=true\n",
        "\nGLOBAL_API_WINS_OVER_OEM=true\n",
        "\nSILENT_OEM_DEFEAT=true\n",
        "\nFACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=true\n",
        "\nDOCUMENTARY_FACE_VALUE_CONFLICT=RESOLVED\n",
        "\nOEM_TO_API_100_TO_1_BRIDGE=PROVEN\n",
        "\nOEM_TO_API_100_TO_1_BRIDGE_PROVEN=true\n",
        "\nOEM_TO_API_100_TO_1_BRIDGE_REQUIRED_FOR_API_SIZING=true\n",
        "\nOEM_TO_API_100_TO_1_BRIDGE_ALLOWED_FOR_API_SIZING=true\n",
        "\nOEM_CONTRACT_EQUALS_100_API_CONTRACTS_PROVEN=true\n",
        "\nOPERATIVE_CONVERSION_FROM_0_01_OVER_0_0001=true\n",
        "\nCONFLICT_FACTOR_IS_OPERATIVE_API_SIZING_CONVERSION=true\n",
        "\nPROVEN_BASIS_IS_OEM_TO_API_100_TO_1_BRIDGE=true\n",
        "\nUNIVERSAL_XPERP_DENOMINATION_PROVEN=true\n",
        "\nUNIVERSAL_XPERP_DENOMINATION_ASSUMED=true\n",
        "\nFACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=CLOSED\n",
        "\nFAIL_CLOSED_CTVAL_GUARD_STATUS=OPTIONAL\n",
        "\nMISSING_CTVAL_FAIL_CLOSED=false\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nCOVER_USDC=INSTANTIATED\n",
        "\nSETTLEMENT_PNL=PROVEN\n",
        "\nSETTLEMENT_PNL_STATUS=PROVEN\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nNO_USD_EQUALS_USDC=false\n",
        "\nDOCS_PERSIST_IS_NOT_ADMISSIBLE_PRODUCTIVE_EVIDENCE=false\n",
        "\nORDER_SUBMITTED=true\n",
        "\nFUNDING_PERFORMED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUPPORT_CONTACT_AUTHORIZED=true\n",
        "\nALLOWLIST_EXPANSION_AUTHORIZED=true\n",
        "\nOKX_API_CALL_PERFORMED=true\n",
        "\nNO_RUNTIME_CODE_CHANGE=false\n",
        "\nNO_TRADING_LOGIC_CHANGE=false\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AH marker present: {marker!r}"
    assert "1 OEM contract = 100 API contracts" not in section
    assert "OEM 0.01 BTC is wrong" not in section
    assert "OEM 0.01 is wrong" not in section
    assert "API has global precedence over OEM" not in section


def test_z2ah_retains_oem_0_01_and_does_not_prove_100_to_1_bridge() -> None:
    section = _z2ah_section(_read(MASTER_RUNBOOK))
    assert "OEM_DOCUMENTARY_CONTRACT_SIZE=0.01_BTC" in section
    assert "OEM_SPEC_CONTRACT_SIZE=0.01_BTC" in section
    assert "OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN" in section
    assert "OEM_TO_API_100_TO_1_BRIDGE=PROVEN" not in section.replace(
        "OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN", ""
    )
    assert "API_EXECUTION_DENOMINATION_STATUS=PROVEN" in section
    assert "PROVEN_BASIS_IS_OEM_TO_API_100_TO_1_BRIDGE=false" in section


def test_z2ah_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true" in mot
    assert "§11.13.5.Z2AH |" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={CONSUMED_Z2AG_POINTER}\n" not in mot
    assert "historical next pointer superseded by §11.13.5.Z2AH" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AI" in mot
    assert "API_EXECUTION_DENOMINATION_STATUS=PROVEN" in mot
    assert "API_EXECUTION_CTVAL=0.0001_BTC" in mot
    assert "API_EXECUTION_CTMULT=1" in mot
    assert "API_EXECUTION_LOTSZ=1" in mot
    assert "API_EXECUTION_MINSZ=1" in mot
    assert f"API_SIZING_AUTHORITY={API_SIZING_AUTHORITY}" in mot
    assert "OEM_DOCUMENTARY_CONTRACT_SIZE=0.01_BTC" in mot
    assert "OEM_DOCUMENTARY_FACE_VALUE_STATUS=RETAINED_NOT_ADJUDICATED_WRONG" in mot
    assert "OEM_SPEC_WRONG=false" in mot
    assert "GLOBAL_API_WINS=false" in mot
    assert "OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN" in mot
    assert "OEM_TO_API_100_TO_1_BRIDGE_ALLOWED_FOR_API_SIZING=false" in mot
    assert "OEM_CONTRACT_EQUALS_100_API_CONTRACTS_PROVEN=false" in mot
    assert "FACE_VALUE_CONFLICT_AS_API_NUMERIC_SAFETY_BLOCKER=CLOSED" in mot
    assert "FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED" in mot
    assert "FAIL_CLOSED_CTVAL_GUARD_STATUS=REQUIRED" in mot
    assert "DOCUMENTARY_FACE_VALUE_CONFLICT=CONFLICTED" in mot
    assert "OEM_SPEC_CONTRACT_SIZE=0.01_BTC" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert "SETTLEMENT_PNL=UNPROVEN" in mot
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in mot
    assert "LF_10_AUTHORIZED=false" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert (
        "Z2AG_SCOPED_API_CTVAL_SIZING_SPLIT"
        not in mot.split("NEXT_CANONICAL_STEP_POINTER=", 1)[1].split("\n", 1)[0]
    )
    assert (
        "Z2AH_API_EXECUTION_DENOMINATION_PROVEN"
        not in mot.split("NEXT_CANONICAL_STEP_POINTER=", 1)[1].split("\n", 1)[0]
    )
