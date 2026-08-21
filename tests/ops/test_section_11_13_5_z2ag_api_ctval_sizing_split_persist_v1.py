"""§11.13.5.Z2AG scoped API ctVal sizing authority split persist.

Docs/governance invariants only. Persists the already-completed
read-only Face-Value split: documentary OEM/API conflict remains
CONFLICTED; automated API order sizing uses instrument-specific ctVal.
Does not declare OEM wrong, does not award global API precedence, does
not instantiate COVER_USDC, does not prove settlement PnL or live
flatten, and does not start LF-10, submit orders, call OKX, fund, or
unlock Canary.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AG_HEADING = "### 11.13.5.Z2AG Scoped API ctVal sizing authority split persist"
Z2AF_HEADING = "### 11.13.5.Z2AF LF-09 blocker-DAG re-adjudication persist"
Z2AE_HEADING = "### 11.13.5.Z2AE LF-08 LIVE_FLATTEN_PROVABILITY re-adjudication persist"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_ACTION_NOT_"
    "AUTHORIZED_BY_THIS_PERSIST_Z2AG_SCOPED_API_CTVAL_SIZING_SPLIT_"
    "DOCUMENTARY_FACE_VALUE_CONFLICT_REMAINS_CONFLICTED_OEM_SPEC_NOT_"
    "DEFEATED_NO_GLOBAL_API_WINS_COVER_USDC_UNINSTANTIATED_SETTLEMENT_"
    "PNL_UNPROVEN_LIVE_FLATTEN_UNPROVEN_NO_LF10_NO_FLATTEN_CONTINUATION_"
    "NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_"
    "AUTHORIZED"
)
CONSUMED_Z2AF_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_ACTION_NOT_"
    "AUTHORIZED_BY_THIS_PERSIST_LF09_COMPLETE_DAG_UNCHANGED_LIVE_FLATTEN_"
    "UNPROVEN_FACE_VALUE_CONFLICT_PARALLEL_NUMERIC_ROOT_PRODUCTIVE_RUNTIME_"
    "PROOF_NOT_ADMISSIBLE_NO_LF10_NO_FLATTEN_CONTINUATION_NO_ORDER_NO_"
    "ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_AUTHORIZED"
)
OWNER_GO = "Z2AG_SCOPED_API_CTVAL_SIZING_SPLIT_DOCS_ONLY_PERSIST"
BASELINE_SHA = "364a1e75986490f28aa9041a6b391e11c387cb37"
API_SIZING_STATUS = (
    "PROVEN_SCOPED_OKX_AGENT_TRADE_KIT_SWAP_FUTURES_OPTION_ORDER_"
    "SIZING_USE_INSTRUMENTS_CTVAL_DO_NOT_ASSUME"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ag_section(text: str) -> str:
    start = text.find(Z2AG_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AG heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2AG"
    return text[start:end]


def test_z2ag_heading_is_unique_and_follows_z2af() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AG_HEADING) == 1
    z2ae = text.find(Z2AE_HEADING)
    z2af = text.find(Z2AF_HEADING)
    z2ag = text.find(Z2AG_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2ae < z2af < z2ag < ladder


def test_z2ag_docs_bind_scoped_ctval_split_without_oem_defeat_or_cover() -> None:
    section = _z2ag_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=Z2AG_SCOPED_API_CTVAL_SIZING_AUTHORITY_SPLIT_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP=LF_09",
        "TARGET_INSTID=BTC-USD_UM_XPERP-310404",
        "TARGET_CTVAL=0.0001",
        "TARGET_CTVAL_CCY=BTC",
        "TARGET_CTMULT=1",
        "TARGET_API_CTVAL=0.0001_BTC",
        "OEM_SPEC_CONTRACT_SIZE=0.01_BTC",
        "GUIDE_CONTRACT_SIZE=0.0001_BTC",
        "API_LINEAR_NOTIONAL_FORMULA=sz*ctVal*markPx",
        "DOCUMENTARY_FACE_VALUE_CONFLICT=CONFLICTED",
        "FACE_VALUE_AUTHORITY=CONFLICTED",
        "TARGET_FACE_VALUE_AUTHORITY_STATUS=CONFLICTED",
        "FACE_VALUE_CONFLICT_STATUS=UNRESOLVED",
        "FACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=false",
        "OEM_SPEC_WRONG=false",
        "OEM_SPEC_DECLARED_WRONG=false",
        "OEM_SPEC_DECLARED_STALE=false",
        "OEM_SPEC_DECLARED_TYPO=false",
        "OEM_SPEC_DECLARED_LEGACY=false",
        "GLOBAL_API_WINS=false",
        "SILENT_OEM_DEFEAT=false",
        "NO_SILENT_API_PRECEDENCE_OVER_OEM_SPEC=true",
        "NO_SILENT_OEM_SPEC_PRECEDENCE_OVER_API=true",
        "NO_OKX_PRECEDENCE_RULE_API_OVER_OEM_OR_OEM_OVER_API_LOCATED=true",
        f"API_EXECUTION_PRECEDENCE_RULE_STATUS={API_SIZING_STATUS}",
        f"API_EXECUTION_CTVAL_SIZING_STATUS={API_SIZING_STATUS}",
        "CTVAL_LOOKUP_RULE_FOUND=true",
        "DO_NOT_ASSUME_CONTRACT_SIZE_RULE_FOUND=true",
        "DO_NOT_ASSUME_CONTRACT_SIZES=true",
        "CTVAL_CONTRACT_FACE_VALUE_BINDING_FOUND=true",
        "FUTURES_APPLICABILITY_FOUND=true",
        "OPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_FOR_API_SIZING=0.0001_BTC",
        "OPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_IS_OEM_LEGAL_CONTRACT_SIZE=false",
        "OPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_IS_SETTLEMENT_AMOUNT=false",
        "OPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_IS_ACCOUNT_IM_OR_COVER_OPERATOR=false",
        "HARDCODED_OEM_0_01_IS_NOT_OPERATIVE_API_SIZING_AUTHORITY_FOR_TARGET=true",
        "QTY=1",
        "MARKPX_CURRENT_VALUE=64408.5",
        "API_SIZING_NOTIONAL=6.44085",
        "INTERNAL_NOTIONAL_ENVELOPE_NUMERIC=6.44085",
        "API_SIZING_NOTIONAL_CLASS=API_SIZING_AND_INTERNAL_NOTIONAL_ENVELOPE_NOT_COVER_USDC_NOT_OEM_SETTLEMENT",
        "API_SIZING_NOTIONAL_IS_COVER_USDC=false",
        "API_SIZING_NOTIONAL_IS_OEM_SETTLEMENT_AMOUNT=false",
        "API_SIZING_NOTIONAL_IS_SETTLEMENT_PNL_PROOF=false",
        "API_SIZING_NOTIONAL_IS_USD_EQUALS_USDC_PROOF=false",
        "API_SIZING_NOTIONAL_IS_FINITE_PHYSICAL_USDC_PROOF=false",
        "API_SIZING_NOTIONAL_IS_LIVE_FLATTEN_PROOF=false",
        "INTERNAL_NOTIONAL_ENVELOPE_USED_AS_OEM_PROOF=false",
        "TARGET_POSITION_VALUE_NUMERIC_INSTANTIATION_STATUS=UNPROVEN",
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
        "EARLIEST_NUMERIC_SAFETY_BLOCKER=FACE_VALUE_CONFLICT",
        "PARALLEL_NUMERIC_ROOT=FACE_VALUE_AUTHORITY_CONFLICT",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AG marker: {marker}"
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
        "\nGLOBAL_API_WINS=true\n",
        "\nSILENT_OEM_DEFEAT=true\n",
        "\nFACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=true\n",
        "\nDOCUMENTARY_FACE_VALUE_CONFLICT=RESOLVED\n",
        "\nFACE_VALUE_AUTHORITY=RESOLVED\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nCOVER_USDC=INSTANTIATED\n",
        "\nSETTLEMENT_PNL=PROVEN\n",
        "\nSETTLEMENT_PNL_STATUS=PROVEN\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nNO_USD_EQUALS_USDC=false\n",
        "\nAPI_SIZING_NOTIONAL_IS_COVER_USDC=true\n",
        "\nAPI_SIZING_NOTIONAL_IS_OEM_SETTLEMENT_AMOUNT=true\n",
        "\nOPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_IS_OEM_LEGAL_CONTRACT_SIZE=true\n",
        "\nOPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_IS_SETTLEMENT_AMOUNT=true\n",
        "\nOPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_IS_ACCOUNT_IM_OR_COVER_OPERATOR=true\n",
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
        assert marker not in section, f"forbidden Z2AG marker present: {marker!r}"


def test_z2ag_does_not_classify_644085_as_cover_or_oem_settlement() -> None:
    section = _z2ag_section(_read(MASTER_RUNBOOK))
    assert "API_SIZING_NOTIONAL=6.44085" in section
    assert "INTERNAL_NOTIONAL_ENVELOPE_NUMERIC=6.44085" in section
    assert "MARKPX_CURRENT_VALUE=64408.5" in section
    assert "COVER_USDC=6.44085" not in section
    assert "OEM_SETTLEMENT_AMOUNT=6.44085" not in section
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in section
    assert (
        "API_SIZING_NOTIONAL_CLASS=API_SIZING_AND_INTERNAL_NOTIONAL_ENVELOPE_"
        "NOT_COVER_USDC_NOT_OEM_SETTLEMENT"
    ) in section


def test_z2ag_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true" in mot
    assert "§11.13.5.Z2AG |" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={CONSUMED_Z2AF_POINTER}\n" not in mot
    assert "historical next pointer superseded by §11.13.5.Z2AG" in mot
    assert "DOCUMENTARY_FACE_VALUE_CONFLICT=CONFLICTED" in mot
    assert "OEM_SPEC_WRONG=false" in mot
    assert "GLOBAL_API_WINS=false" in mot
    assert "SILENT_OEM_DEFEAT=false" in mot
    assert "FACE_VALUE_CONFLICT_RESOLVED_GLOBALLY=false" in mot
    assert f"API_EXECUTION_PRECEDENCE_RULE_STATUS={API_SIZING_STATUS}" in mot
    assert "OPERATIVE_RUNTIME_CONTRACT_FACE_VALUE_FOR_API_SIZING=0.0001_BTC" in mot
    assert "API_SIZING_NOTIONAL=6.44085" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert "SETTLEMENT_PNL=UNPROVEN" in mot
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in mot
    assert "LF_10_AUTHORIZED=false" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    assert "TARGET_FACE_VALUE_AUTHORITY_STATUS=CONFLICTED" in mot
    assert "OEM_SPEC_CONTRACT_SIZE=0.01_BTC" in mot
    assert "TARGET_CTVAL=0.0001" in mot
    assert (
        "LF09_COMPLETE_DAG_UNCHANGED"
        not in mot.split("NEXT_CANONICAL_STEP_POINTER=", 1)[1].split("\n", 1)[0]
    )
