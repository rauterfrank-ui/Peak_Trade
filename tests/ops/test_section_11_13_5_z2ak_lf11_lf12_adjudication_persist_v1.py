"""§11.13.5.Z2AK LF-11 and LF-12 read-only adjudication persist.

Docs/governance invariants only. Persists the already-completed
read-only LF-11 C_UNPROVEN and LF-12 prerequisite-not-closed
adjudications. Does not implement flatten transport, does not bind a
flatten LIMIT price policy, does not raise ORDER_COUNT_LIMIT to 2,
does not authorize a runtime read, productive GET, order, funding,
Canary, or support contact, and does not prove live flatten.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AK_HEADING = "### 11.13.5.Z2AK LF-11 and LF-12 read-only adjudication persist"
Z2AJ_HEADING = "### 11.13.5.Z2AJ USD/USDC public conversion-candidate GET adjudication persist"
Z2AI_HEADING = "### 11.13.5.Z2AI LF-10 read-only adjudication persist"
Z2AH_HEADING = "### 11.13.5.Z2AH API execution denomination PROVEN persist"
Z2AG_HEADING = "### 11.13.5.Z2AG Scoped API ctVal sizing authority split persist"
Z2AF_HEADING = "### 11.13.5.Z2AF LF-09 blocker-DAG re-adjudication persist"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_"
    "STEP_NOT_AUTHORIZED_BY_THIS_PERSIST_LF11_C_UNPROVEN_LF12_"
    "PREREQUISITES_NOT_CLOSED_LIVE_FLATTEN_UNPROVEN_NO_FLATTEN_PRICE_"
    "POLICY_NO_DEDICATED_FLATTEN_TRANSPORT_NO_ORDER_COUNT_LIMIT_RAISE_"
    "TO_2_NO_RUNTIME_READ_NO_PRODUCTIVE_FLATTEN_NO_GET_NO_ORDER_NO_"
    "ALLOWLIST_CANARY_NOT_AUTHORIZED_SUPPORT_CONTACT_NOT_AUTHORIZED"
)
CONSUMED_Z2AJ_POINTER = (
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
OWNER_GO = "GRANTED_FOR_LF11_AND_LF12_SSOT_PERSIST_ONLY"
BASELINE_SHA = "8eed1d8f3939dba287cf0d4c70bec895102d711d"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ak_section(text: str) -> str:
    start = text.find(Z2AK_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AK heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2AK"
    return text[start:end]


def test_z2ak_heading_is_unique_and_follows_z2aj() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AK_HEADING) == 1
    z2af = text.find(Z2AF_HEADING)
    z2ag = text.find(Z2AG_HEADING)
    z2ah = text.find(Z2AH_HEADING)
    z2ai = text.find(Z2AI_HEADING)
    z2aj = text.find(Z2AJ_HEADING)
    z2ak = text.find(Z2AK_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2af < z2ag < z2ah < z2ai < z2aj < z2ak < ladder


def test_z2ak_docs_bind_lf11_c_unproven_and_lf12_prerequisites_not_closed() -> None:
    section = _z2ak_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=LF_11_AND_LF_12_SSOT_PERSIST_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_CANONICALLY_CLOSED_STEP_BEFORE_WRITE=LF_10",
        "LAST_CANONICALLY_CLOSED_STEP=LF_12",
        "LF11_ADJUDICATION=C_UNPROVEN",
        "LF_11_READ_ONLY_ADJUDICATION=COMPLETE",
        "LF12_ADJUDICATION=C_PREREQUISITES_NOT_CLOSED_PRODUCTIVE_FLATTEN_NOT_ADMISSIBLE",
        "LF_12_READ_ONLY_ADJUDICATION=COMPLETE",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN",
        "LIVE_FLATTEN_PROVABILITY_STATUS=UNPROVEN_HARD_STOP",
        "EXISTING_EVIDENCE_SUFFICIENT=false",
        "CLAIMS_NEWLY_PROVEN_THIS_STEP=NONE",
        "NO_NEW_PROVEN_CLAIM=true",
        "PRODUCTIVE_FLATTEN_EXECUTED=false",
        "FLATTEN_RUNTIME_REACHABILITY=ABSENT",
        "FLATTEN_PRICE_BINDING=ABSENT",
        "ORDER_COUNT_LIMIT_IMPACT=ENTRY_ONESHOT_AND_OPEN_POSITION_GATE_BLOCK_NOT_CUMULATIVE_SUBMIT_COUNTER",
        "REDUCE_ONLY_BINDING=OFFLINE_FIELD_TRUE_WIRE_UNBOUND",
        "FULL_FLATTEN_SZ_BINDING=OFFLINE_ABS_OBSERVED_POS_PRODUCTIVE_UNPROVEN",
        "OVERSHOOT_FLIP_RACE_STATUS=UNPROVEN_NOT_OFFLINE_EXCLUDABLE",
        "PARTIAL_FILL_RECOVERY=OFFLINE_HALT_NOT_FLATTEN_WIRED",
        "UNKNOWN_SUBMIT_RECOVERY=ENTRY_PATH_WIRED_FLATTEN_PATH_ABSENT",
        "IDEMPOTENCY_DUPLICATE_PREVENTION=OFFLINE_CLORDID_SPLIT_PROVEN_FLATTEN_CLIENT_LOCK_ABSENT",
        "PRE_POST_POSITION_OBSERVATION_DESIGN=SPECIFIED_NOT_EXECUTED",
        "PENDING_ORDER_CONFIRM_DESIGN=SPECIFIED_NOT_EXECUTED",
        "ORDER_COUNT_LIMIT_RAISE_TO_2_FORBIDDEN=true",
        "MINIMUM_SAFE_CHANGE_IF_ANY=DEDICATED_FLATTEN_SUBMIT_PATH_PLUS_OWNER_RATIFIED_LIMIT_PRICE_POLICY_DO_NOT_RAISE_GLOBAL_ORDER_COUNT_LIMIT_TO_2",
        "ENTRY_AND_FLATTEN_PROOF_COUPLING=SEMANTICALLY_SEPARATE_OPERATIONALLY_COUPLED_IF_NO_POSITION_COMBINED_CAMPAIGN_BLOCKED_ON_CURRENT_PATH",
        "ORDER_ACK_IS_NOT_FILL=true",
        "PARTIAL_FILL_IS_NOT_FLAT=true",
        "CANCEL_SUCCESS_IS_NOT_FLAT=true",
        "REDUCE_ONLY_TRUE_IS_OFFLINE_PLAN_OR_MAPPER_FIELD_NOT_PRODUCTIVE_FLATTEN_WIRE_PROOF=true",
        "CAN_LIVE_FLATTEN_BE_AUTHORIZED_SAFELY_NOW=false",
        "GET_POSITIONS_POS=0",
        "TOTAL_EQ=0",
        "FUNDING_ACTUALLY_REQUIRED=TRUE_FOR_CREATING_ABSENT_POSITION_GIVEN_LAST_BOUND_ZERO_EQUITY_FALSE_FOR_FLATTEN_POST_ITSELF",
        "FRESH_POSITION_VS_FUNDING_GET_AUTHORIZED=false",
        "ARCHIVED_OFF_REPO_EVIDENCE_INSPECTED=true",
        "ARCHIVED_EVIDENCE_AUTHORITY_CLASSIFICATION=INSPECTED_NOT_CANONICAL",
        "NO_FLATTEN_TRANSPORT_IMPLEMENTATION=true",
        "NO_FLATTEN_PRICE_POLICY_IMPLEMENTATION=true",
        "NO_ORDER_COUNT_LIMIT_RAISE_TO_2=true",
        "NO_RUNTIME_CODE_CHANGE=true",
        "NO_TRADING_LOGIC_CHANGE=true",
        "GET_EXECUTED_THIS_PERSIST_STEP=false",
        "AUTHENTICATED_REQUEST_PERFORMED=false",
        "ORDER_SUBMITTED=false",
        "FUNDING_PERFORMED=false",
        "CANARY_EXECUTED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "DOCS_PERSIST_IS_NOT_ADMISSIBLE_PRODUCTIVE_EVIDENCE=true",
        "NO_CAPABILITY_ADVANCEMENT=true",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "NEXT_OWNER_AUTHORIZATION_REQUIRED=SEPARATE_OWNER_GO_REQUIRED_FOR_ANY_NEXT_OPERATIONAL_OR_ADJUDICATION_STEP",
        "HARD_STOP_AFTER_THIS_TASK=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2AK marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nLF_11_AUTHORIZED=true\n",
        "\nLF_12_AUTHORIZED=true\n",
        "\nLF11_IMPLEMENTATION_AUTHORIZED=true\n",
        "\nLF12_IMPLEMENTATION_AUTHORIZED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST_STEP=true\n",
        "\nAUTHENTICATED_REQUEST_PERFORMED=true\n",
        "\nORDER_SUBMITTED=true\n",
        "\nFUNDING_PERFORMED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nEXISTING_EVIDENCE_SUFFICIENT=true\n",
        "\nCAN_LIVE_FLATTEN_BE_AUTHORIZED_SAFELY_NOW=true\n",
        "\nORDER_COUNT_LIMIT_RAISE_TO_2_FORBIDDEN=false\n",
        "\nNO_FLATTEN_TRANSPORT_IMPLEMENTATION=false\n",
        "\nNO_TRADING_LOGIC_CHANGE=false\n",
        "\nCOVER_USDC=INSTANTIATED\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nFRESH_POSITION_VS_FUNDING_GET_AUTHORIZED=true\n",
        "\nPRODUCTIVE_FLATTEN_EXECUTED=true\n",
        "\nLF11_ADJUDICATION=A_PROVEN\n",
        "\nLF12_ADJUDICATION=A_PREREQUISITES_CLOSED\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AK marker present: {marker!r}"


def test_z2ak_does_not_implement_flatten_transport_or_raise_order_count_limit() -> None:
    section = _z2ak_section(_read(MASTER_RUNBOOK))
    assert "NO_FLATTEN_TRANSPORT_IMPLEMENTATION=true" in section
    assert "NO_FLATTEN_PRICE_POLICY_IMPLEMENTATION=true" in section
    assert "ORDER_COUNT_LIMIT_RAISE_TO_2_FORBIDDEN=true" in section
    assert "NO_ORDER_COUNT_LIMIT_RAISE_TO_2=true" in section
    assert (
        "MINIMUM_SAFE_CHANGE_IF_ANY=DEDICATED_FLATTEN_SUBMIT_PATH_PLUS_OWNER_RATIFIED_LIMIT_PRICE_POLICY_DO_NOT_RAISE_GLOBAL_ORDER_COUNT_LIMIT_TO_2"
        in (section)
    )
    assert "ORDER_ACK_IS_NOT_FILL=true" in section
    assert "PARTIAL_FILL_IS_NOT_FLAT=true" in section
    assert "CANCEL_SUCCESS_IS_NOT_FLAT=true" in section
    assert "FLATTEN_RUNTIME_REACHABILITY=ABSENT" in section
    assert "FLATTEN_PRICE_BINDING=ABSENT" in section


def test_z2ak_funding_is_not_required_for_flatten_post_itself() -> None:
    section = _z2ak_section(_read(MASTER_RUNBOOK))
    assert "GET_POSITIONS_POS=0" in section
    assert "TOTAL_EQ=0" in section
    assert (
        "FUNDING_ACTUALLY_REQUIRED=TRUE_FOR_CREATING_ABSENT_POSITION_GIVEN_LAST_BOUND_ZERO_EQUITY_FALSE_FOR_FLATTEN_POST_ITSELF"
        in section
    )
    assert "FRESH_POSITION_VS_FUNDING_GET_AUTHORIZED=false" in section
    assert (
        "ENTRY_AND_FLATTEN_PROOF_COUPLING=SEMANTICALLY_SEPARATE_OPERATIONALLY_COUPLED_IF_NO_POSITION_COMBINED_CAMPAIGN_BLOCKED_ON_CURRENT_PATH"
        in (section)
    )


def test_z2ak_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true" in mot
    assert "THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true" in mot
    assert "§11.13.5.Z2AK |" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={CONSUMED_Z2AJ_POINTER}\n" not in mot
    assert "historical next pointer superseded by §11.13.5.Z2AK" in mot
    assert "LF11_ADJUDICATION=C_UNPROVEN" in mot
    assert "LF12_ADJUDICATION=C_PREREQUISITES_NOT_CLOSED_PRODUCTIVE_FLATTEN_NOT_ADMISSIBLE" in mot
    assert "LIVE_FLATTEN_PROVABILITY=UNPROVEN" in mot
    assert "EXISTING_EVIDENCE_SUFFICIENT=false" in mot
    assert "FLATTEN_RUNTIME_REACHABILITY=ABSENT" in mot
    assert "FLATTEN_PRICE_BINDING=ABSENT" in mot
    assert "ORDER_COUNT_LIMIT_RAISE_TO_2_FORBIDDEN=true" in mot
    assert "CAN_LIVE_FLATTEN_BE_AUTHORIZED_SAFELY_NOW=false" in mot
    assert "ARCHIVED_EVIDENCE_AUTHORITY_CLASSIFICATION=INSPECTED_NOT_CANONICAL" in mot
    assert "LAST_CANONICALLY_CLOSED_STEP=LF_12" in mot
    assert "LF_11_AUTHORIZED=false" in mot
    assert "LF_12_AUTHORIZED=false" in mot
    assert "LIVE_AUTHORIZED=false" in mot
    snapshot_pointer_lines = [
        ln for ln in mot.splitlines() if ln.startswith("NEXT_CANONICAL_STEP_POINTER=")
    ]
    assert snapshot_pointer_lines, "missing snapshot NEXT_CANONICAL_STEP_POINTER"
    assert snapshot_pointer_lines[-1] == f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}"
    current_pointer = snapshot_pointer_lines[-1].split("=", 1)[1]
    assert "Z2AJ_PUBLIC_CONVERSION_CANDIDATE" not in current_pointer
    assert "NO_LF11" not in current_pointer
    assert "NO_FLATTEN_PRICE_POLICY" in current_pointer
    assert "NO_DEDICATED_FLATTEN_TRANSPORT" in current_pointer
    assert "NO_ORDER_COUNT_LIMIT_RAISE_TO_2" in current_pointer
    assert "NO_PRODUCTIVE_FLATTEN" in current_pointer
    assert "NO_RUNTIME_READ" in current_pointer
