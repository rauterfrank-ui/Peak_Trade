"""§11.13.5.Z2AJ USD/USDC public conversion-candidate GET persist.

Docs/governance invariants only. Persists the already-completed
read-only public EEA GET + USD/USDC conversion-candidate adjudication
as C_UNPROVEN. Does not treat idxPx=1 as a USD/USDC operator, does not
reinterpret a missing USDC-USD spot instrument as
NO_CLIENT_CONVERSION_REQUIRED, does not instantiate COVER_USDC, does
not prove settlement PnL or live flatten, and does not start LF-11,
submit orders, call OKX, fund, or unlock Canary.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AJ_HEADING = "### 11.13.5.Z2AJ USD/USDC public conversion-candidate GET adjudication persist"
Z2AK_HEADING = "### 11.13.5.Z2AK LF-11 and LF-12 read-only adjudication persist"
Z2AI_HEADING = "### 11.13.5.Z2AI LF-10 read-only adjudication persist"
Z2AH_HEADING = "### 11.13.5.Z2AH API execution denomination PROVEN persist"
Z2AG_HEADING = "### 11.13.5.Z2AG Scoped API ctVal sizing authority split persist"
Z2AF_HEADING = "### 11.13.5.Z2AF LF-09 blocker-DAG re-adjudication persist"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_"
    "STEP_NOT_AUTHORIZED_BY_THIS_PERSIST_Z2AJ_PUBLIC_CONVERSION_CANDIDATE_"
    "SURFACES_ADJUDICATED_USDC_USD_INDEX_1_NON_OPERATOR_NEGATIVE_CONTRACT_"
    "USD_USDC_OPERATOR_UNPROVEN_NO_CLIENT_CONVERSION_REQUIRED_UNPROVEN_"
    "COVER_USDC_UNINSTANTIATED_SETTLEMENT_PNL_UNPROVEN_LIVE_FLATTEN_"
    "UNPROVEN_NO_LF11_NO_FLATTEN_CONTINUATION_NO_COVER_CALC_NO_REPEAT_"
    "PUBLIC_USDC_USD_INDEX_OR_SPOT_GET_WITHOUT_NEW_DISCRIMINATING_"
    "HYPOTHESIS_NO_OEM_CLARIFICATION_NO_ORDER_NO_ALLOWLIST_CANARY_NOT_"
    "AUTHORIZED_SUPPORT_CONTACT_NOT_AUTHORIZED"
)
CONSUMED_Z2AI_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_"
    "STEP_NOT_AUTHORIZED_BY_THIS_PERSIST_LF10_COMPLETE_NO_NEW_PROVEN_"
    "CLOSURE_API_DENOMINATION_PROVEN_OEM_0_01_DOCUMENTARY_QUARANTINED_"
    "100_TO_1_BRIDGE_INFERRED_NOT_PROVEN_NO_OEM_DEFEAT_NO_GLOBAL_API_WINS_"
    "COVER_USDC_UNINSTANTIATED_SETTLEMENT_PNL_UNPROVEN_LIVE_FLATTEN_"
    "UNPROVEN_NO_LF11_NO_FLATTEN_CONTINUATION_NO_COVER_CALC_NO_PRODUCTIVE_"
    "GET_NO_OEM_CLARIFICATION_NO_ORDER_NO_ALLOWLIST_CANARY_NOT_AUTHORIZED_"
    "SUPPORT_CONTACT_NOT_AUTHORIZED"
)
OWNER_GO = "GRANTED_FOR_POST_Z2AI_USD_USDC_PUBLIC_GET_ADJUDICATION_PERSIST_ONLY"
PRIOR_GET_OWNER_GO = "GRANTED_AND_CONSUMED_FOR_THIS_READ_ONLY_PRODUCTIVE_GET"
BASELINE_SHA = "6685a9224e6bbe1daf6ea09e1478ea25936fd05e"
CONVERSION_NUMERIC_STATUS = "UNINSTANTIATED_REQUIRES_LATER_PRODUCTIVE_USD_USDC_EVIDENCE"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2aj_section(text: str) -> str:
    start = text.find(Z2AJ_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AJ heading"
    end = text.find(Z2AK_HEADING, start)
    assert end > start, "missing §11.13.5.Z2AK boundary after Z2AJ"
    return text[start:end]


def test_z2aj_heading_is_unique_and_follows_z2ai() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AJ_HEADING) == 1
    z2af = text.find(Z2AF_HEADING)
    z2ag = text.find(Z2AG_HEADING)
    z2ah = text.find(Z2AH_HEADING)
    z2ai = text.find(Z2AI_HEADING)
    z2aj = text.find(Z2AJ_HEADING)
    z2ak = text.find(Z2AK_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2af < z2ag < z2ah < z2ai < z2aj < z2ak < ladder


def test_z2aj_docs_bind_c_unproven_without_operator_or_cover() -> None:
    section = _z2aj_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=Z2AJ_USD_USDC_PUBLIC_GET_ADJUDICATION_SSOT_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"PRIOR_GET_OWNER_GO={PRIOR_GET_OWNER_GO}",
        "PRIOR_GET_OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP_BEFORE_WRITE=LF_10",
        "LAST_CANONICALLY_CLOSED_STEP=LF_10",
        "GET_EXECUTED_THIS_PERSIST_STEP=false",
        "GET_AUTHORIZED_THIS_PERSIST_STEP=false",
        "PRIOR_GET_EXECUTED=true",
        "PRIOR_GET_COUNT=4",
        "PRIOR_GET_HOST=eea.okx.com",
        "PRIOR_GET_AUTHENTICATED=false",
        "GET_1_OKX_CODE=0",
        "GET_1_IDXPX=1",
        "GET_1_INSTID=USDC-USD",
        "GET_1_TS=1787277298160",
        "GET_2_OKX_CODE=51001",
        "GET_2_INSTRUMENT_EXISTS=false",
        "GET_3_OKX_CODE=51001",
        "GET_3_INSTRUMENT_EXISTS=false",
        "GET_4_OKX_CODE=51001",
        "GET_4_INSTRUMENT_EXISTS=false",
        "USDC_USD_SPOT_INSTRUMENT_EXISTS_ON_PROBED_EEA_SURFACE=false",
        "USDC_USD_TICKER_INSTRUMENT_EXISTS_ON_PROBED_EEA_SURFACE=false",
        "IDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=false",
        "IDXPX_1_IS_OBSERVATION_ONLY=true",
        "IDXPX_1_IS_NOT_EXPLICIT_SETTLEMENT_OR_COVER_OPERATOR=true",
        "IDXPX_1_IS_NOT_USD_TO_USDC_FORMULA=true",
        "IDXPX_1_IS_NOT_RATIFIED_COVER_USDC_CONVERSION_RATE=true",
        "IDXPX_1_IS_NOT_PROOF_OF_NO_CLIENT_CONVERSION_REQUIRED=true",
        "IDXPX_1_IS_NOT_USD_USDC_OPERATOR=true",
        "USD_EQUALS_USDC_ASSUMED=false",
        "NO_USD_EQUALS_USDC=true",
        "MISSING_USDC_USD_SPOT_IS_NOT_NO_CLIENT_CONVERSION_REQUIRED=true",
        "MISSING_USDC_USD_TICKER_IS_NOT_NO_CLIENT_CONVERSION_REQUIRED=true",
        "PUBLIC_CONVERSION_CANDIDATE_SURFACES_ADJUDICATED=true",
        "USDC_USD_INDEX_1_NON_OPERATOR_NEGATIVE_CONTRACT=true",
        "REPEAT_PUBLIC_USDC_USD_INDEX_OR_SPOT_GET_WITHOUT_NEW_DISCRIMINATING_HYPOTHESIS=FORBIDDEN",
        "REPEAT_OF_ADJUDICATED_PUBLIC_PATHS_AUTHORIZED=false",
        "NUMERIC_USD_USDC_OPERATOR_FOUND=false",
        "USD_USDC_OPERATOR=UNPROVEN",
        "USD_USDC_OPERATOR_STATUS=UNPROVEN",
        "NO_CLIENT_CONVERSION_REQUIRED_PROVEN=false",
        "CLIENT_FX_REQUIRED=UNPROVEN",
        "COVER_USDC=UNINSTANTIATED",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "SETTLEMENT_PNL=UNPROVEN",
        "SETTLEMENT_PNL_STATUS=UNPROVEN",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "LIVE_FLATTEN_PROVABILITY_STATUS=UNPROVEN_HARD_STOP",
        f"CONVERSION_NUMERIC_STATUS={CONVERSION_NUMERIC_STATUS}",
        "Z2J_REMAINS_CONTROLLING_FOR_CONVERSION_NUMERIC_STATUS=true",
        "FORBIDDEN_UPGRADE_FROM_ACCOUNT_SETTLECCY_USDC=true",
        "FORBIDDEN_UPGRADE_FROM_PUBLIC_SETTLECCY_USD=true",
        "FORBIDDEN_UPGRADE_FROM_TAKERUSDC_MAKERUSDC_FIELD_NAMES=true",
        "FORBIDDEN_UPGRADE_FROM_IDXPX_1=true",
        "FORBIDDEN_UPGRADE_FROM_DISCOUNT_RATE_0_995=true",
        "FORBIDDEN_UPGRADE_FROM_NOTIONALUSD=true",
        "FORBIDDEN_UPGRADE_FROM_INTERNAL_PEAK_TRADE_ENVELOPES=true",
        "FORBIDDEN_UPGRADE_FROM_CTVAL_0_0001_BTC=true",
        "IDXPX_1_MAY_NOT_PROMOTE_USD_USDC_OPERATOR_TO_PROVEN=true",
        "MISSING_USDC_USD_SPOT_MAY_NOT_PROVE_NO_CLIENT_CONVERSION_REQUIRED=true",
        "COVER_USDC_MAY_NOT_INSTANTIATE_WITHOUT_NEW_FIRST_PARTY_PROOF=true",
        "ADJUDICATION_RESULT=C_UNPROVEN",
        "CLAIMS_PROVEN_THIS_STEP=NONE",
        "CLAIMS_NEWLY_PROVEN_THIS_STEP=NONE",
        "NO_NEW_PROVEN_CLAIM=true",
        "TARGET_INSTID=BTC-USD_UM_XPERP-310404",
        "API_EXECUTION_DENOMINATION_STATUS=PROVEN",
        "API_EXECUTION_CTVAL=0.0001_BTC",
        "OEM_DOCUMENTARY_CONTRACT_SIZE=0.01_BTC",
        "OEM_SPEC_WRONG=false",
        "GLOBAL_API_WINS=false",
        "OEM_TO_API_100_TO_1_BRIDGE=INFERRED_NOT_PROVEN",
        "FACE_VALUE_CONFLICT_AS_API_NUMERIC_SAFETY_BLOCKER=CLOSED",
        "FACE_VALUE_CONFLICT_AS_DOCUMENTARY_CONFLICT=OPEN_QUARANTINED",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        "EARLIEST_NUMERIC_SAFETY_BLOCKER=COVER_USDC_UNINSTANTIATED",
        "LF_11_AUTHORIZED=false",
        "LF_11_STARTED=false",
        "NO_RUNTIME_CODE_CHANGE=true",
        "NO_TRADING_LOGIC_CHANGE=true",
        "NO_NEW_GET=true",
        "NO_AUTHENTICATED_REQUEST=true",
        "NO_ORDER=true",
        "NO_FUNDING=true",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "DOCS_PERSIST_IS_NOT_ADMISSIBLE_PRODUCTIVE_EVIDENCE=true",
        "NO_CAPABILITY_ADVANCEMENT=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "NEXT_OWNER_AUTHORIZATION_REQUIRED=SEPARATE_OWNER_GO_REQUIRED_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_STEP",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AJ marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nLF_11_AUTHORIZED=true\n",
        "\nLF_11_STARTED=true\n",
        "\nLF11_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST_STEP=true\n",
        "\nGET_AUTHORIZED_THIS_PERSIST_STEP=true\n",
        "\nOKX_API_CALL_PERFORMED=true\n",
        "\nAUTHENTICATED_REQUEST_PERFORMED=true\n",
        "\nUSD_USDC_OPERATOR=PROVEN\n",
        "\nUSD_USDC_OPERATOR_STATUS=PROVEN\n",
        "\nNO_CLIENT_CONVERSION_REQUIRED_PROVEN=true\n",
        "\nCLIENT_FX_REQUIRED=true\n",
        "\nIDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=true\n",
        "\nIDXPX_1_IS_OBSERVATION_ONLY=false\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nNO_USD_EQUALS_USDC=false\n",
        "\nCOVER_USDC=INSTANTIATED\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nSETTLEMENT_PNL=PROVEN\n",
        "\nSETTLEMENT_PNL_STATUS=PROVEN\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nNUMERIC_USD_USDC_OPERATOR_FOUND=true\n",
        "\nREPEAT_OF_ADJUDICATED_PUBLIC_PATHS_AUTHORIZED=true\n",
        "\nCLAIMS_NEWLY_PROVEN_THIS_STEP=USD_USDC_OPERATOR\n",
        "\nNO_NEW_PROVEN_CLAIM=false\n",
        "\nADJUDICATION_RESULT=A_PROVEN\n",
        "\nADJUDICATION_RESULT=B_NOT_REQUIRED\n",
        "\nOEM_SPEC_WRONG=true\n",
        "\nGLOBAL_API_WINS=true\n",
        "\nOEM_TO_API_100_TO_1_BRIDGE=PROVEN\n",
        "\nORDER_SUBMITTED=true\n",
        "\nFUNDING_PERFORMED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUPPORT_CONTACT_AUTHORIZED=true\n",
        "\nALLOWLIST_MUTATED=true\n",
        "\nNO_RUNTIME_CODE_CHANGE=false\n",
        "\nNO_TRADING_LOGIC_CHANGE=false\n",
        "\nIDXPX_1_MAY_NOT_PROMOTE_USD_USDC_OPERATOR_TO_PROVEN=false\n",
        "\nMISSING_USDC_USD_SPOT_MAY_NOT_PROVE_NO_CLIENT_CONVERSION_REQUIRED=false\n",
        "\nCOVER_USDC_MAY_NOT_INSTANTIATE_WITHOUT_NEW_FIRST_PARTY_PROOF=false\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AJ marker present: {marker!r}"


def test_z2aj_idxpx_1_cannot_promote_usd_usdc_operator() -> None:
    section = _z2aj_section(_read(MASTER_RUNBOOK))
    assert "GET_1_IDXPX=1" in section
    assert "IDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=false" in section
    assert "IDXPX_1_MAY_NOT_PROMOTE_USD_USDC_OPERATOR_TO_PROVEN=true" in section
    assert "USD_USDC_OPERATOR=UNPROVEN" in section
    assert "USD_USDC_OPERATOR=PROVEN" not in section.replace(
        "USD_USDC_OPERATOR=UNPROVEN", ""
    ).replace("USD_USDC_OPERATOR_STATUS=UNPROVEN", "")
    assert "IDXPX_1_IS_NOT_USD_USDC_OPERATOR=true" in section


def test_z2aj_missing_spot_cannot_prove_no_client_conversion_required() -> None:
    section = _z2aj_section(_read(MASTER_RUNBOOK))
    assert "GET_3_OKX_CODE=51001" in section
    assert "USDC_USD_SPOT_INSTRUMENT_EXISTS_ON_PROBED_EEA_SURFACE=false" in section
    assert "MISSING_USDC_USD_SPOT_IS_NOT_NO_CLIENT_CONVERSION_REQUIRED=true" in section
    assert "MISSING_USDC_USD_SPOT_MAY_NOT_PROVE_NO_CLIENT_CONVERSION_REQUIRED=true" in (section)
    assert "NO_CLIENT_CONVERSION_REQUIRED_PROVEN=false" in section
    assert "NO_CLIENT_CONVERSION_REQUIRED_PROVEN=true" not in section


def test_z2aj_cover_usdc_remains_uninstantiated_without_new_first_party_proof() -> None:
    section = _z2aj_section(_read(MASTER_RUNBOOK))
    assert "COVER_USDC=UNINSTANTIATED" in section
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in section
    assert "COVER_USDC_MAY_NOT_INSTANTIATE_WITHOUT_NEW_FIRST_PARTY_PROOF=true" in section
    assert "NO_COVER_USDC_INSTANTIATION=true" in section
    assert "COVER_USDC=INSTANTIATED" not in section.replace(
        "COVER_USDC=UNINSTANTIATED", ""
    ).replace("COVER_USDC_STATUS=UNINSTANTIATED", "")
    assert f"CONVERSION_NUMERIC_STATUS={CONVERSION_NUMERIC_STATUS}" in section


def test_z2aj_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true" in mot
    assert "§11.13.5.Z2AJ |" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={CONSUMED_Z2AI_POINTER}\n" not in mot
    assert "historical next pointer superseded by §11.13.5.Z2AJ" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AK" in mot
    assert "ADJUDICATION_RESULT=C_UNPROVEN" in mot
    assert "CLAIMS_NEWLY_PROVEN_THIS_STEP=NONE" in mot
    assert "PUBLIC_CONVERSION_CANDIDATE_SURFACES_ADJUDICATED=true" in mot
    assert "USDC_USD_INDEX_1_NON_OPERATOR_NEGATIVE_CONTRACT=true" in mot
    assert "IDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=false" in mot
    assert "USD_EQUALS_USDC_ASSUMED=false" in mot
    assert "NUMERIC_USD_USDC_OPERATOR_FOUND=false" in mot
    assert "USD_USDC_OPERATOR_STATUS=UNPROVEN" in mot
    assert "NO_CLIENT_CONVERSION_REQUIRED_PROVEN=false" in mot
    assert "CLIENT_FX_REQUIRED=UNPROVEN" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert "SETTLEMENT_PNL_STATUS=UNPROVEN" in mot
    assert "LIVE_FLATTEN_PROVABILITY_STATUS=UNPROVEN_HARD_STOP" in mot
    assert f"CONVERSION_NUMERIC_STATUS={CONVERSION_NUMERIC_STATUS}" in mot
    assert "LAST_CANONICALLY_CLOSED_STEP=LF_10" in mot
    assert "LF_11_AUTHORIZED=false" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    snapshot_pointer_lines = [
        ln for ln in mot.splitlines() if ln.startswith("NEXT_CANONICAL_STEP_POINTER=")
    ]
    assert snapshot_pointer_lines, "missing snapshot NEXT_CANONICAL_STEP_POINTER"
    assert snapshot_pointer_lines[-1] != f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}"
    current_pointer = snapshot_pointer_lines[-1].split("=", 1)[1]
    assert "LF10_COMPLETE_NO_NEW_PROVEN_CLOSURE" not in current_pointer
    assert "Z2AH_API_EXECUTION_DENOMINATION_PROVEN" not in current_pointer
    assert "Z2AJ_PUBLIC_CONVERSION_CANDIDATE" not in current_pointer
    assert "Z2AL_STATIC_FLATTEN_PREREQUISITES" not in current_pointer
    assert "Z2AO_EXTRA_DEVIATION_BOUND_NOT_REQUIRED" in current_pointer
    assert "NO_ORDER_COUNT_LIMIT_RAISE_TO_2" in current_pointer
    assert "NO_PRODUCTIVE_FLATTEN" in current_pointer
