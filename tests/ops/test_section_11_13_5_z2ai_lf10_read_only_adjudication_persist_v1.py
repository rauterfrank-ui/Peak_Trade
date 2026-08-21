"""§11.13.5.Z2AI LF-10 read-only adjudication persist.

Docs/governance invariants only. Persists the already-completed
read-only LF-10 adjudication as COMPLETE_READ_ONLY_NO_NEW_PROVEN_CLOSURE.
Does not close a new PROVEN claim, does not prove a 100:1 OEM-to-API
bridge, does not declare OEM 0.01 BTC wrong, does not treat API
0.0001 BTC as a universal OEM/settlement denomination, does not assume
USD=USDC, does not prove settlement PnL, does not instantiate
COVER_USDC, does not prove live flatten, and does not start LF-11,
submit orders, call OKX, fund, or unlock Canary.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AI_HEADING = "### 11.13.5.Z2AI LF-10 read-only adjudication persist"
Z2AJ_HEADING = "### 11.13.5.Z2AJ USD/USDC public conversion-candidate GET adjudication persist"
Z2AH_HEADING = "### 11.13.5.Z2AH API execution denomination PROVEN persist"
Z2AG_HEADING = "### 11.13.5.Z2AG Scoped API ctVal sizing authority split persist"
Z2AF_HEADING = "### 11.13.5.Z2AF LF-09 blocker-DAG re-adjudication persist"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_"
    "STEP_NOT_AUTHORIZED_BY_THIS_PERSIST_LF10_COMPLETE_NO_NEW_PROVEN_"
    "CLOSURE_API_DENOMINATION_PROVEN_OEM_0_01_DOCUMENTARY_QUARANTINED_"
    "100_TO_1_BRIDGE_INFERRED_NOT_PROVEN_NO_OEM_DEFEAT_NO_GLOBAL_API_WINS_"
    "COVER_USDC_UNINSTANTIATED_SETTLEMENT_PNL_UNPROVEN_LIVE_FLATTEN_"
    "UNPROVEN_NO_LF11_NO_FLATTEN_CONTINUATION_NO_COVER_CALC_NO_PRODUCTIVE_"
    "GET_NO_OEM_CLARIFICATION_NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_"
    "SUPPORT_CONTACT_NOT_AUTHORIZED"
)
CONSUMED_Z2AH_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_ACTION_NOT_"
    "AUTHORIZED_BY_THIS_PERSIST_Z2AH_API_EXECUTION_DENOMINATION_PROVEN_"
    "OEM_0_01_DOCUMENTARY_QUARANTINED_100_TO_1_BRIDGE_INFERRED_NOT_PROVEN_"
    "NO_OEM_DEFEAT_NO_GLOBAL_API_WINS_COVER_USDC_UNINSTANTIATED_SETTLEMENT_"
    "PNL_UNPROVEN_LIVE_FLATTEN_UNPROVEN_NO_LF10_NO_FLATTEN_CONTINUATION_"
    "NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_"
    "AUTHORIZED"
)
OWNER_GO = "GRANTED_FOR_LF10_PERSIST_ONLY"
BASELINE_SHA = "32e5b625a5cb16727b9256ef6279195907dc29ae"
API_SIZING_AUTHORITY = "INSTRUMENT_SPECIFIC_CTVAL_DO_NOT_ASSUME_OEM_OR_PRODUCT_CONTRACT_SIZE"
QTY_1_STATUS = "API_SZ1_UNDERLYING_0.0001_BTC_PROVEN_OEM_QTY1_UNPROVEN_UNIFIED_UNPROVEN"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ai_section(text: str) -> str:
    start = text.find(Z2AI_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AI heading"
    end = text.find(Z2AJ_HEADING, start)
    assert end > start, "missing §11.13.5.Z2AJ boundary after Z2AI"
    return text[start:end]


def test_z2ai_heading_is_unique_and_follows_z2ah() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AI_HEADING) == 1
    z2af = text.find(Z2AF_HEADING)
    z2ag = text.find(Z2AG_HEADING)
    z2ah = text.find(Z2AH_HEADING)
    z2ai = text.find(Z2AI_HEADING)
    z2aj = text.find(Z2AJ_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2af < z2ag < z2ah < z2ai < z2aj < ladder


def test_z2ai_docs_bind_lf10_complete_without_new_proven_or_runtime() -> None:
    section = _z2ai_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=LF_10_SSOT_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP_BEFORE_WRITE=LF_09",
        "LAST_CANONICALLY_CLOSED_STEP=LF_10",
        "TARGET_INSTID=BTC-USD_UM_XPERP-310404",
        "LF_10_READ_ONLY_ADJUDICATION=COMPLETE",
        "LF10_ADJUDICATION=COMPLETE_READ_ONLY_NO_NEW_PROVEN_CLOSURE",
        "LF10_PERSIST_STATUS=BOUND",
        "NEW_EVIDENCE_FOUND=false",
        "CLAIMS_PROVEN_THIS_STEP=NONE",
        "NO_NEW_PROVEN_CLAIM=true",
        "BLOCKER_DAG_CHANGED=false",
        "API_EXECUTION_DENOMINATION_STATUS=PROVEN",
        "API_EXECUTION_CTVAL=0.0001_BTC",
        "API_EXECUTION_CTVAL_NUMERIC=0.0001",
        "API_EXECUTION_CTVAL_CCY=BTC",
        "API_EXECUTION_CTMULT=1",
        "API_EXECUTION_LOTSZ=1",
        "API_EXECUTION_MINSZ=1",
        "API_EXECUTION_SZ_UNIT=NUMBER_OF_API_CONTRACTS",
        "API_SZ1_MEANS_ONE_API_CONTRACT_WITH_CTVAL_0_0001_BTC=true",
        f"API_SIZING_AUTHORITY={API_SIZING_AUTHORITY}",
        "HARDCODED_OEM_OR_PRODUCT_CONTRACT_SIZE_IS_NOT_API_SIZING_AUTHORITY=true",
        "UNIVERSAL_XPERP_DENOMINATION_PROVEN=false",
        "UNIVERSAL_XPERP_DENOMINATION_ASSUMED=false",
        "API_0001_IS_NOT_UNIVERSAL_OEM_OR_SETTLEMENT_DENOMINATION=true",
        "API_LINEAR_NOTIONAL_FORMULA=sz*ctVal*markPx",
        "API_SIZING_NOTIONAL=6.44085",
        "API_SIZING_NOTIONAL_CLASS=API_SIZING_AND_INTERNAL_NOTIONAL_ENVELOPE_NOT_COVER_USDC_NOT_OEM_SETTLEMENT",
        "API_SIZING_NOTIONAL_IS_COVER_USDC=false",
        "API_SIZING_NOTIONAL_IS_OEM_SETTLEMENT_AMOUNT=false",
        "API_SIZING_NOTIONAL_IS_OEM_EXPIRY_FEE_MONETARY_BASE=false",
        "POSITION_VALUE_STATUS=UNPROVEN_AS_UNIFIED_EXCHANGE_OR_OEM_VALUE",
        f"QTY_1_EXPOSURE_STATUS={QTY_1_STATUS}",
        "QTY_1_API_EXECUTION_EXPOSURE_BTC=PROVEN_0.0001_BTC",
        "QTY_1_OEM_CONTRACT_EXPOSURE=UNPROVEN",
        "QTY_1_UNIFIED_EXPOSURE=UNPROVEN",
        "EXPIRY_FEE_MONETARY_BASE_STATUS=OEM_OKX_IDENTITY_UNPROVEN",
        "OEM_OKX_MONETARY_BASE_IDENTITY_STATUS=UNPROVEN",
        "NO_NUMERIC_OEM_EXPIRY_FEE_BASE_INVENTED=true",
        "SETTLEMENT_PNL=UNPROVEN",
        "SETTLEMENT_PNL_STATUS=UNPROVEN",
        "FINAL_SETTLEMENT_PNL_FORMULA_STATUS=INFERRED_NOT_PROVEN",
        "FINAL_SETTLEMENT_PNL_CANDIDATE=(settlePx-avgPx)*pos*ctVal",
        "USD_USDC_OPERATOR=UNPROVEN",
        "USD_USDC_OPERATOR_STATUS=UNPROVEN",
        "NO_USD_EQUALS_USDC=true",
        "USD_EQUALS_USDC_ASSUMED=false",
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
        "FACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=false",
        "DOCUMENTARY_FACE_VALUE_CONFLICT=CONFLICTED",
        "OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN",
        "OEM_TO_API_100_TO_1_BRIDGE_PROVEN=false",
        "OEM_TO_API_100_TO_1_BRIDGE_ALLOWED_FOR_API_SIZING=false",
        "OEM_CONTRACT_EQUALS_100_API_CONTRACTS_PROVEN=false",
        "OPERATIVE_CONVERSION_FROM_0_01_OVER_0_0001=false",
        "CONFLICT_FACTOR_IS_OPERATIVE_API_SIZING_CONVERSION=false",
        "FACE_VALUE_CONFLICT_AS_API_NUMERIC_SAFETY_BLOCKER=CLOSED",
        "FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED",
        "FAIL_CLOSED_CTVAL_GUARD_STATUS=REQUIRED",
        "DAG_TOPOLOGY_UNCHANGED=true",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        "EARLIEST_NUMERIC_SAFETY_BLOCKER=COVER_USDC_UNINSTANTIATED",
        "PARALLEL_NUMERIC_ROOT=COVER_USDC_UNINSTANTIATED",
        "COVER_USDC=UNINSTANTIATED",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "LIVE_FLATTEN_PROVABILITY_REMAINS=UNPROVEN_HARD_STOP",
        "PRODUCTIVE_REACHABILITY=NOT_ADMISSIBLE",
        "CANARY_ADMISSIBILITY=NOT_ADMISSIBLE",
        "PRODUCTIVE_RUNTIME_PROOF_ADMISSIBLE=false",
        "NO_BLOCKER_CLOSED_BY_LF10=true",
        "LF_06_OVERALL_ADJUDICATION=NOT_PASS",
        "LF_07_ADJUDICATION=B",
        "LF_08_ADJUDICATION=B",
        "LF_09_READ_ONLY_ADJUDICATION=COMPLETE",
        "LF_11_AUTHORIZED=false",
        "LF_11_STARTED=false",
        "LF11_EXECUTED=false",
        "NO_LF11_ANALYSIS=true",
        "NO_LF11_IMPLEMENTATION=true",
        "NO_OEM_CLARIFICATION=true",
        "NO_PRODUCTIVE_GET=true",
        "NO_COVER_CALC=true",
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
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "NEXT_OWNER_AUTHORIZATION_REQUIRED=SEPARATE_OWNER_GO_REQUIRED_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_STEP",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AI marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nLF_11_AUTHORIZED=true\n",
        "\nLF_11_STARTED=true\n",
        "\nLF11_EXECUTED=true\n",
        "\nCLAIMS_PROVEN_THIS_STEP=API_EXECUTION_DENOMINATION_STATUS\n",
        "\nNO_NEW_PROVEN_CLAIM=false\n",
        "\nNEW_EVIDENCE_FOUND=true\n",
        "\nBLOCKER_DAG_CHANGED=true\n",
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
        "\nUNIVERSAL_XPERP_DENOMINATION_PROVEN=true\n",
        "\nUNIVERSAL_XPERP_DENOMINATION_ASSUMED=true\n",
        "\nAPI_0001_IS_NOT_UNIVERSAL_OEM_OR_SETTLEMENT_DENOMINATION=false\n",
        "\nFACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=CLOSED\n",
        "\nFAIL_CLOSED_CTVAL_GUARD_STATUS=OPTIONAL\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nCOVER_USDC=INSTANTIATED\n",
        "\nSETTLEMENT_PNL=PROVEN\n",
        "\nSETTLEMENT_PNL_STATUS=PROVEN\n",
        "\nFINAL_SETTLEMENT_PNL_FORMULA_STATUS=PROVEN\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nPRODUCTIVE_REACHABILITY=ADMISSIBLE\n",
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
        "\nAPI_SIZING_NOTIONAL_IS_COVER_USDC=true\n",
        "\nAPI_SIZING_NOTIONAL_IS_OEM_SETTLEMENT_AMOUNT=true\n",
        "\nAPI_SIZING_NOTIONAL_IS_OEM_EXPIRY_FEE_MONETARY_BASE=true\n",
        "\nPOSITION_VALUE_STATUS=PROVEN\n",
        "\nQTY_1_OEM_CONTRACT_EXPOSURE=PROVEN\n",
        "\nQTY_1_UNIFIED_EXPOSURE=PROVEN\n",
        "\nEXPIRY_FEE_MONETARY_BASE_STATUS=PROVEN\n",
        "\nOEM_OKX_MONETARY_BASE_IDENTITY_STATUS=PROVEN\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AI marker present: {marker!r}"
    assert "1 OEM contract = 100 API contracts" not in section
    assert "OEM 0.01 BTC is wrong" not in section
    assert "OEM 0.01 is wrong" not in section
    assert "API has global precedence over OEM" not in section


def test_z2ai_retains_oem_0_01_and_does_not_prove_100_to_1_or_settlement() -> None:
    section = _z2ai_section(_read(MASTER_RUNBOOK))
    assert "OEM_DOCUMENTARY_CONTRACT_SIZE=0.01_BTC" in section
    assert "OEM_SPEC_CONTRACT_SIZE=0.01_BTC" in section
    assert "OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN" in section
    assert "OEM_TO_API_100_TO_1_BRIDGE=PROVEN" not in section.replace(
        "OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN", ""
    )
    assert "API_EXECUTION_DENOMINATION_STATUS=PROVEN" in section
    assert "SETTLEMENT_PNL=UNPROVEN" in section
    assert "FINAL_SETTLEMENT_PNL_FORMULA_STATUS=INFERRED_NOT_PROVEN" in section
    assert "FINAL_SETTLEMENT_PNL_FORMULA_STATUS=PROVEN" not in section.replace(
        "FINAL_SETTLEMENT_PNL_FORMULA_STATUS=INFERRED_NOT_PROVEN", ""
    )
    assert "COVER_USDC=UNINSTANTIATED" in section
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in section
    assert "CLAIMS_PROVEN_THIS_STEP=NONE" in section
    assert "API_0001_IS_NOT_UNIVERSAL_OEM_OR_SETTLEMENT_DENOMINATION=true" in section


def test_z2ai_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true" in mot
    assert "§11.13.5.Z2AI |" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={CONSUMED_Z2AH_POINTER}\n" not in mot
    assert "historical next pointer superseded by §11.13.5.Z2AI" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AJ" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AK" in mot
    assert "LF10_ADJUDICATION=COMPLETE_READ_ONLY_NO_NEW_PROVEN_CLOSURE" in mot
    assert "CLAIMS_PROVEN_THIS_STEP=NONE" in mot
    assert "NEW_EVIDENCE_FOUND=false" in mot
    assert "API_EXECUTION_DENOMINATION_STATUS=PROVEN" in mot
    assert "OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN" in mot
    assert "POSITION_VALUE_STATUS=UNPROVEN_AS_UNIFIED_EXCHANGE_OR_OEM_VALUE" in mot
    assert f"QTY_1_EXPOSURE_STATUS={QTY_1_STATUS}" in mot
    assert "EXPIRY_FEE_MONETARY_BASE_STATUS=OEM_OKX_IDENTITY_UNPROVEN" in mot
    assert "SETTLEMENT_PNL_STATUS=UNPROVEN" in mot
    assert "USD_USDC_OPERATOR_STATUS=UNPROVEN" in mot
    assert "FACE_VALUE_CONFLICT_AS_API_NUMERIC_SAFETY_BLOCKER=CLOSED" in mot
    assert "FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED" in mot
    assert "COVER_USDC=UNINSTANTIATED" in mot
    assert "SETTLEMENT_PNL=UNPROVEN" in mot
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in mot
    assert "PRODUCTIVE_REACHABILITY=NOT_ADMISSIBLE" in mot
    assert "LAST_CANONICALLY_CLOSED_STEP=LF_10" in mot
    assert "LF_11_AUTHORIZED=false" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "OEM_DOCUMENTARY_CONTRACT_SIZE=0.01_BTC" in mot
    assert "OEM_SPEC_WRONG=false" in mot
    assert "GLOBAL_API_WINS=false" in mot
    snapshot_pointer_lines = [
        ln for ln in mot.splitlines() if ln.startswith("NEXT_CANONICAL_STEP_POINTER=")
    ]
    assert snapshot_pointer_lines, "missing snapshot NEXT_CANONICAL_STEP_POINTER"
    current_pointer = snapshot_pointer_lines[-1].split("=", 1)[1]
    assert current_pointer != NEXT_POINTER
    assert "LF10_COMPLETE_NO_NEW_PROVEN_CLOSURE" not in current_pointer
    assert "Z2AH_API_EXECUTION_DENOMINATION_PROVEN" not in current_pointer
    assert "Z2AJ_PUBLIC_CONVERSION_CANDIDATE" not in current_pointer
    assert "NO_FLATTEN_PRICE_POLICY" in current_pointer
    assert "NO_DEDICATED_FLATTEN_TRANSPORT" in current_pointer
    assert "NO_ORDER_COUNT_LIMIT_RAISE_TO_2" in current_pointer
    assert "NO_PRODUCTIVE_FLATTEN" in current_pointer
