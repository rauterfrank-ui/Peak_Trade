"""§11.13.5.Z2AB productive runtime proof is not pre-submit admissible.

Docs/governance invariants only. Adjudicates that a filled-position /
flatten proof cannot be instantiated with a pre-submit hard loss bound
without violating current policy (C). Does not close Z2Y
authorizability B, Z2AA safety-dependency C, Rule C, Face Value, or
COVER_USDC. Does not submit orders, call OKX, fund, open a position,
flatten, or unlock Canary.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AB_HEADING = "### 11.13.5.Z2AB Productive runtime proof is not pre-submit admissible"
Z2AC_HEADING = "### 11.13.5.Z2AC LF-06 venue semantics evidence persist"
Z2AA_HEADING = "### 11.13.5.Z2AA Earliest Z2Y safety dependency is not statically provable"
Z2Z_HEADING = "### 11.13.5.Z2Z Evidence-model re-adjudication"
Z2Y_HEADING = "### 11.13.5.Z2Y Filled-position-derived probe is not presently authorizable"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_BECAUSE_PRODUCTIVE_RUNTIME_PROOF_NOT_ADMISSIBLE_"
    "PRE_SUBMIT_LOSS_BOUND_UNINSTANTIABLE_LIMIT_REDUCEONLY_FLATTEN_NOT_"
    "DETERMINISTIC_REDUCEONLY_ABSENT_FROM_CANARY_PAYLOAD_CLOSE_POSITION_NOT_"
    "ALLOWLISTED_FACE_VALUE_UNRESOLVED_COVER_USDC_UNINSTANTIATED_FUNDING_"
    "PREREQUISITE_UNSATISFIED_FILL_DETERMINISM_UNPROVEN_RULE_C_UNPROVEN_NO_"
    "ORDER_NO_POSITION_NO_FUNDING_NO_ALLOWLIST_EXPANSION_CANARY_NOT_"
    "AUTHORIZED_SUPPORT_CONTACT_NOT_AUTHORIZED"
)
CONSUMED_Z2AA_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_PRODUCTIVE_FILLED_POSITION_OR_LIVE_FLATTEN_"
    "PROOF_NOT_STATICALLY_PROVABLE_UNDER_LIMIT_ONLY_NO_MARKET_VENUE_CLOSE_IS_"
    "MARKET_FACE_VALUE_CONFLICT_UNRESOLVED_COVER_USDC_UNINSTANTIATED_FILL_"
    "DETERMINISM_UNPROVEN_RULE_C_UNPROVEN_SUPPORT_CONTACT_NOT_AUTHORIZED_"
    "CANARY_NOT_AUTHORIZED_ALLOWLIST_EXPANSION_NOT_AUTHORIZED"
)
OWNER_GO = "SECTION_11_13_5_POST_Z2AA_PRODUCTIVE_RUNTIME_PROOF_ADMISSIBILITY"
BASELINE_SHA = "1beb3ee4001352d7f902fe9dc80b4d20b7e4c9a4"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ab_section(text: str) -> str:
    start = text.find(Z2AB_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AB heading"
    end = text.find(Z2AC_HEADING, start)
    assert end > start, "missing §11.13.5.Z2AC boundary after Z2AB"
    return text[start:end]


def test_z2ab_heading_is_unique_and_follows_z2aa() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AB_HEADING) == 1
    z2y = text.find(Z2Y_HEADING)
    z2z = text.find(Z2Z_HEADING)
    z2aa = text.find(Z2AA_HEADING)
    z2ab = text.find(Z2AB_HEADING)
    z2ac = text.find(Z2AC_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2y < z2z < z2aa < z2ab < z2ac < ladder


def test_z2ab_docs_bind_adjudication_c_without_runtime_or_admissible_proof() -> None:
    section = _z2ab_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=POST_Z2AA_PRODUCTIVE_RUNTIME_PROOF_ADMISSIBILITY_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "Z2AA_SAFETY_DEPENDENCY_REMAINS_BINDING=true",
        "Z2Y_AUTHORIZABILITY_ADJUDICATION_REMAINS=B",
        "SAFETY_DEPENDENCY_STEP_ADJUDICATION_REMAINS=C",
        "PRODUCTIVE_RUNTIME_PROOF_ADMISSIBILITY_ADJUDICATION=C",
        "PRODUCTIVE_RUNTIME_PROOF_ADMISSIBLE=false",
        "CAN_A_SINGLE_MINIMUM_PRODUCTIVE_POSITION_BE_CREATED_AND_FLATTENED_WITH_A_PRE_SUBMIT_HARD_LOSS_BOUND_AND_WITHOUT_VIOLATING_CURRENT_POLICY=false",
        "GATE_1_EXACT_INSTRUMENT_BINDING=PASS",
        "GATE_1_INSTID=BTC-USD_UM_XPERP-310404",
        "GATE_1_INSTTYPE=FUTURES",
        "GATE_1_RULETYPE=xperp",
        "GATE_1_CTTYPE=linear",
        "GATE_1_CTVAL=0.0001",
        "GATE_1_CTVALCCY=BTC",
        "GATE_1_CTMULT=1",
        "GATE_1_MINSZ=1",
        "GATE_1_LOTSZ=1",
        "GATE_1_TICKSZ=0.1",
        "GATE_1_SETTLECCY=USD",
        "GATE_1_FAMILY_OR_OEM_FACE_VALUE_USED_AS_BINDING=false",
        "GATE_2_MINIMUM_SIZE=PASS",
        "GATE_2_QTY=1",
        "GATE_2_MAX_POSITIONS_EFFECTIVE=1",
        "GATE_3_ENTRY_ORDER_POLICY=PASS",
        "GATE_3_ENTRY_ORDER_TYPE=LIMIT",
        "GATE_3_MARKET=false",
        "GATE_3_IOC=false",
        "GATE_3_FOK=false",
        "GATE_3_NEW_SUBMIT_SURFACE=false",
        "GATE_4_FLATTEN_CAPABILITY=FAIL",
        "GATE_4_TRADE_ORDER_ENDPOINT_ALLOWLISTED=true",
        "GATE_4_CLOSE_POSITION_ENDPOINT_ALLOWLISTED=false",
        "GATE_4_REDUCEONLY_IN_CANARY_PAYLOAD=false",
        "GATE_4_OBSERVED_POSITION_SIZE_FLATTEN_IMPLEMENTED=false",
        "GATE_4_OVERSHOOT_FLIP_PROTECTION_PROVEN=false",
        "GATE_5_PRICE_BOUND_FOR_ENTRY=FAIL",
        "GATE_5_EXACT_ENTRY_PRICE_BOUND=NONE_UNBOUNDED",
        "GATE_6_PRICE_BOUND_FOR_FLATTEN=FAIL",
        "GATE_6_FINITE_PRICE_TIME_BOUND_PROVEN=false",
        "GATE_7_FILL_STATE_MACHINE=UNPROVEN",
        "GATE_8_WORST_CASE_LOSS_BOUND=FAIL",
        "GATE_8_OEM_FACE_VALUE_0_01_USED=false",
        "GATE_8_USD_EQUALS_USDC_USED=false",
        "GATE_9_FUNDING_INDEPENDENCE=PASS",
        "GATE_10_RUNTIME_OBSERVABILITY=PASS",
        "GATE_10_POSITION_CREATED_TO_TEST_GETS=false",
        "TERMINAL_VERDICT_A=ALL_MANDATORY_GATES_INCLUDING_FINITE_PRE_SUBMIT_LOSS_BOUND_PROVEN=false",
        "TERMINAL_VERDICT_B=READ_ONLY_NON_MUTATING_EVIDENCE_ACTION_CAN_CLOSE_A_MANDATORY_GATE=false",
        "TERMINAL_VERDICT_D=INSUFFICIENT_EVIDENCE_TO_CHOOSE_A_B_C=false",
        "TERMINAL_VERDICT_C=AT_LEAST_ONE_MANDATORY_GATE_CANNOT_CLOSE_WITHOUT_ORDER_POSITION_FUNDING_OR_ALLOWLIST_EXPANSION=true",
        "ADJUDICATION=C",
        "EXACT_MINIMUM_PROBE_QTY=1",
        "EXACT_ENTRY_ORDER_TYPE=LIMIT",
        "EXACT_ENTRY_PRICE_BOUND=NONE_UNBOUNDED",
        "EXACT_FLATTEN_MECHANISM=NONE_ADMISSIBLE_UNDER_CURRENT_POLICY",
        "EXACT_FLATTEN_PRICE_BOUND=NONE_UNBOUNDED",
        "EXACT_MAX_LOSS_BOUND=UNINSTANTIABLE",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN_HARD_STOP",
        "FILL_DETERMINISM=UNPROVEN",
        "WORST_CASE_LOSS_BOUND=UNINSTANTIABLE",
        "RULE_C_STATUS=UNPROVEN",
        "FACE_VALUE_CONFLICT=UNRESOLVED",
        "COVER_USDC=UNINSTANTIATED",
        "FUNDING_PREREQUISITE=UNSATISFIED",
        "USD_EQUALS_USDC_ASSUMED=false",
        "NEW_EVIDENCE_CLOSES_Z2Y_SAFETY_DEPENDENCY=false",
        "NEW_EVIDENCE_CHANGES_RUNTIME_AUTHORIZATION=false",
        "NEXT_ACTION_REQUIRES_ORDER_SUBMIT=false",
        "NEXT_ACTION_REQUIRES_POSITION=false",
        "NEXT_ACTION_REQUIRES_FUNDING=false",
        "NEXT_ACTION_REQUIRES_ALLOWLIST_CHANGE=false",
        "ORDER_SUBMIT_AUTHORIZED=false",
        "FILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=false",
        "FUTURE_RUNTIME_PROTOCOL_DOCUMENTED=false",
        "NO_POST=true",
        "NO_OKX_API_CALL=true",
        "NO_ALLOWLIST_EXPANSION=true",
        "NO_MARKET_ORDER_ACTIVATION=true",
        "NO_USD_EQUALS_USDC=true",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUPPORT_CONTACT_AUTHORIZED=false",
        "ALLOWLIST_EXPANSION_AUTHORIZED=false",
        "NO_CAPABILITY_ADVANCEMENT=true",
        "NEXT_OWNER_AUTHORIZATION_REQUIRED=SEPARATE_OWNER_GO_TO_ADDRESS_UNRESOLVED_ADMISSIBILITY_BLOCKERS_WITHOUT_IMPLIED_ORDER_AUTHORITY",
        "HARD_STOP_AFTER_THIS_TASK=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
    )
    for marker in required:
        assert marker in section, f"missing Z2AB marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nRULE_C_STATUS=PROVEN\n",
        "\nFACE_VALUE_CONFLICT=RESOLVED\n",
        "\nFACE_VALUE_CONFLICT_STATUS=RESOLVED\n",
        "\nCOVER_USDC=INSTANTIATED\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nFILL_DETERMINISM=PROVEN\n",
        "\nWORST_CASE_LOSS_BOUND_STATUS=INSTANTIATED\n",
        "\nPRODUCTIVE_RUNTIME_PROOF_ADMISSIBLE=true\n",
        "\nORDER_SUBMIT_AUTHORIZED=true\n",
        "\nGATE_4_FLATTEN_CAPABILITY=PASS\n",
        "\nGATE_5_PRICE_BOUND_FOR_ENTRY=PASS\n",
        "\nGATE_6_PRICE_BOUND_FOR_FLATTEN=PASS\n",
        "\nGATE_8_WORST_CASE_LOSS_BOUND=PASS\n",
        "\nGATE_8_OEM_FACE_VALUE_0_01_USED=true\n",
        "\nGATE_8_USD_EQUALS_USDC_USED=true\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nFILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=true\n",
        "\nFUTURE_RUNTIME_PROTOCOL_DOCUMENTED=true\n",
        "\nADJUDICATION=A\n",
        "\nADJUDICATION=B\n",
        "\nADJUDICATION=D\n",
        "\nTERMINAL_VERDICT_A=ALL_MANDATORY_GATES_INCLUDING_FINITE_PRE_SUBMIT_LOSS_BOUND_PROVEN=true\n",
        "\nTERMINAL_VERDICT_B=READ_ONLY_NON_MUTATING_EVIDENCE_ACTION_CAN_CLOSE_A_MANDATORY_GATE=true\n",
        "\nNEW_EVIDENCE_CLOSES_Z2Y_SAFETY_DEPENDENCY=true\n",
        "\nNEW_EVIDENCE_CHANGES_RUNTIME_AUTHORIZATION=true\n",
        "\nNEXT_ACTION_REQUIRES_ORDER_SUBMIT=true\n",
        "\nNEXT_ACTION_REQUIRES_POSITION=true\n",
        "\nNEXT_ACTION_REQUIRES_FUNDING=true\n",
        "\nNEXT_ACTION_REQUIRES_ALLOWLIST_CHANGE=true\n",
        "\nNO_USD_EQUALS_USDC=false\n",
        "\nNO_ALLOWLIST_EXPANSION=false\n",
        "\nOKX_API_CALL_PERFORMED=true\n",
        "\nORDER_SUBMITTED=true\n",
        "\nFUNDING_PERFORMED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUPPORT_CONTACT_AUTHORIZED=true\n",
        "\nALLOWLIST_EXPANSION_AUTHORIZED=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2AB marker present: {marker!r}"


def test_z2ab_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2AB |" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={CONSUMED_Z2AA_POINTER}\n" not in mot
    assert "historical next pointer superseded by §11.13.5.Z2AB" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AC" in mot
    assert "PRODUCTIVE_RUNTIME_PROOF_ADMISSIBLE=false" in mot
    assert "GATE_4_FLATTEN_CAPABILITY=FAIL" in mot
    assert "GATE_8_WORST_CASE_LOSS_BOUND=FAIL" in mot
    assert "ADJUDICATION=C" in mot
    assert "FILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=false" in mot
    assert "ORDER_SUBMIT_AUTHORIZED=false" in mot
