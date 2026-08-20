"""§11.13.5.Z2Y filled-position-derived probe is not presently authorizable.

Docs/governance invariants only. Adjudicates that a FILLED_POSITION_DERIVED
IM / notionalUsd / UPL probe cannot presently be presented for a separate
runtime Owner-GO. Does not submit orders, call OKX, fund, open a position,
flatten, unlock Canary, document an executable protocol, or prove Rule C /
Face Value / COVER_USDC.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2Y_HEADING = "### 11.13.5.Z2Y Filled-position-derived probe is not presently authorizable"
Z2X_HEADING = "### 11.13.5.Z2X Unfilled-order state class does not produce independent account IM"
Z2Z_HEADING = "### 11.13.5.Z2Z Evidence-model re-adjudication"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_UNRESOLVED_SAFETY_DEPENDENCIES_BEFORE_ANY_"
    "FILLED_POSITION_DERIVED_RUNTIME_PROPOSAL_FACE_VALUE_CONFLICT_UNRESOLVED_"
    "COVER_USDC_UNINSTANTIATED_FUNDING_PREREQUISITE_UNSATISFIED_LIVE_FLATTEN_"
    "UNPROVEN_FILL_DETERMINISM_UNPROVEN_QTY_ONE_NOT_VENUE_ADMISSIBLE_AT_ZERO_"
    "EQUITY_RULE_C_UNPROVEN_SUPPORT_CONTACT_NOT_AUTHORIZED_CANARY_NOT_AUTHORIZED"
)
OWNER_GO = "OWNER_GO_Z2X_FILLED_POSITION_DERIVED_AUTHORIZABILITY_ADJUDICATION"
BASELINE_SHA = "6a8a5fdcae2fe449834c47d4ca389f88b0877fcc"
CONSUMED_Z2X_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_POSITION_DERIVED_IM_NOTIONALUSD_OR_UPL_"
    "UNFILLED_ORDER_DOES_NOT_PRODUCE_INDEPENDENT_ACCOUNT_RUNTIME_DISCRIMINATOR_"
    "AT_ACCT_LV_2_RULE_C_UNPROVEN_FACE_VALUE_CONFLICT_UNRESOLVED_COVER_USDC_"
    "UNINSTANTIATED_FUNDING_NOT_AUTHORIZED_PARTIAL_FILL_NOT_AUTHORIZED_"
    "SUPPORT_CONTACT_NOT_AUTHORIZED_CANARY_NOT_AUTHORIZED"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2y_section(text: str) -> str:
    start = text.find(Z2Y_HEADING)
    assert start >= 0, "missing §11.13.5.Z2Y heading"
    end = text.find(Z2Z_HEADING, start)
    assert end > start, "missing §11.13.5.Z2Z boundary after Z2Y"
    return text[start:end]


def test_z2y_heading_is_unique_and_follows_z2x() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2Y_HEADING) == 1
    z2x = text.find(Z2X_HEADING)
    z2y = text.find(Z2Y_HEADING)
    z2z = text.find(Z2Z_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2x < z2y < z2z < ladder


def test_z2y_docs_bind_adjudication_b_without_runtime_or_protocol() -> None:
    section = _z2y_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=Z2X_FILLED_POSITION_DERIVED_AUTHORIZABILITY_ADJUDICATION_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "ADJUDICATION=B",
        "ADJUDICATION_CLASS=FILLED_POSITION_DERIVED_PROBE_NOT_PRESENTLY_AUTHORIZABLE",
        "TERMINAL_VERDICT_B_SELECTED=true",
        "TERMINAL_VERDICT_A_SELECTED=false",
        "TERMINAL_VERDICT_C_SELECTED=false",
        "FILLED_POSITION_DERIVED_PROBE_NOT_PRESENTLY_AUTHORIZABLE=true",
        "FILLED_POSITION_DERIVED_PROBE_PRESENTABLE_FOR_SEPARATE_OWNER_GO=false",
        "FILLED_POSITION_DERIVED_RUNTIME_STATE_AUTHORIZED=false",
        "FUTURE_RUNTIME_PROTOCOL_DOCUMENTED=false",
        "PHASE_5_FUTURE_RUNTIME_PROTOCOL=NOT_DOCUMENTED_BECAUSE_A_NOT_SELECTED",
        "MINIMAL_DISCRIMINATING_STATE_CLASS=FILLED_POSITION_DERIVED",
        "PRODUCTIVE_ORDER_SUBMIT_PERFORMED=false",
        "ORDER_COUNT_SUBMITTED=0",
        "ORDER_FILLED=false",
        "PARTIAL_FILL_OCCURRED=false",
        "POSITION_CREATED=false",
        "PARTIAL_FILL_AUTHORIZED=false",
        "POSITION_OPENING_AUTHORIZED=false",
        "FUNDING_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "A_QTY_ONE_VENUE_ADMISSIBLE=false",
        "A_MAX_AVAIL_BUY=0",
        "A_SYNTACTIC_MINSZ=1",
        "A_SYNTACTIC_LOTSZ=1",
        "B_FILLED_POSITION_STRUCTURALLY_IMPOSSIBLE_AT_BOUND_ZERO_EQUITY=true",
        "B_FUNDING_REQUIRED_BEFORE_ANY_POSITION_OPENING_ATTEMPT=true",
        "B_FUNDING_PREREQUISITE_STATUS=REQUIRED_SEPARATE_FUTURE_AUTHORIZATION_BOUNDARY",
        "C_FACE_VALUE_CONFLICT_STATUS=UNRESOLVED",
        "C_CONFLICT_FACTOR=100",
        "C_EXCHANGE_REPORTED_POSITION_NOTIONALUSD=UNPROVEN_NO_POSITION",
        "D_FILL_DETERMINISM_STATUS=UNPROVEN",
        "D_CANARY_ORDER_TYPE_SEMANTICS=LIMIT_ONLY_NO_MARKET",
        "D_LIVE_SUBMIT_ACK_PROVEN=false",
        "E_FLATTEN_GUARANTEE_STATUS=UNPROVEN_HARD_STOP",
        "E_LIVE_REDUCE_ONLY_CLOSE_PRODUCTIVELY_PROVEN=false",
        "E_TRADE_CLOSE_POSITION_IN_CANARY_POST_ALLOWLIST=false",
        "E_DETERMINISTIC_FLATTEN_UNPROVEN_IS_HARD_STOP_FOR_AUTHORIZABILITY=true",
        "F_COVER_USDC_STATUS=UNINSTANTIATED",
        "F_MISSING_COVER_USDC_PREVENTS_SAFE_AUTHORIZATION=true",
        "F_WORST_CASE_LOSS_BOUND_STATUS=UNINSTANTIABLE",
        "G_LIQUIDATION_SAFETY_STATUS=UNPROVEN_WITHOUT_MONETARY_BASE_AND_FACE_VALUE",
        "G_USD_EQUALS_USDC=false",
        "H_FIELDS_ARE_INDEPENDENT_RULE_C_DISCRIMINATORS_IF_POSITION_EXISTS=true",
        "H_NO_NEW_PRODUCTIVE_API_CALL_THIS_PERSIST=true",
        "I_FAILURE_RECOVERY_STATUS=UNPROVEN_HUMAN_IMPROVISATION_REQUIRED",
        "I_PROVEN_FAIL_CLOSED_RECOVERY_WITHOUT_HUMAN_IMPROVISATION=false",
        "J_EXECUTION_GATES_STATUS=ALL_REMAIN_LOCKED_NO_TEMPORARY_AUTHORIZATION",
        "J_LIVE_ENABLED=false",
        "J_LIVE_ARMED=false",
        "J_SUBMIT_UNLOCKED=false",
        "REUSE_BEFORE_NEW_STATUS=INVENTORIED_NO_NEW_EXECUTION_MACHINERY",
        "NO_DUPLICATE_EXECUTION_MACHINERY_CREATED=true",
        "RULE_C_STATUS=UNPROVEN",
        "RULE_C_INDEPENDENT_RUNTIME_IM_SATISFIED=false",
        "FACE_VALUE_CONFLICT_STATUS=UNRESOLVED",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "RUNTIME_EVIDENCE_OBTAINED=false",
        "OKX_API_CALL_PERFORMED=false",
        "GET_EXECUTED_THIS_PERSIST_STEP=false",
        "ORDER_SUBMITTED=false",
        "CANARY_AUTHORIZED=false",
        "RUNTIME_EXECUTION_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "SUPPORT_CONTACT_AUTHORIZED=false",
        "NO_CAPABILITY_ADVANCEMENT=true",
        "NEXT_OWNER_AUTHORIZATION_REQUIRED=true",
        "HARD_STOP_AFTER_THIS_TASK=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "NO_FUNDING",
        "NO_ORDER",
        "NO_CANARY",
        "NO_EXECUTE",
        "NO_MANUFACTURE_COVER_USDC=true",
        "NO_RESOLVE_FACE_VALUE_BY_ASSUMPTION=true",
        "NO_USD_EQUALS_USDC=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2Y marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nRULE_C_STATUS=PROVEN\n",
        "\nFACE_VALUE_CONFLICT_STATUS=RESOLVED\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nPRODUCTIVE_ORDER_SUBMIT_PERFORMED=true\n",
        "\nORDER_SUBMITTED=true\n",
        "\nPOSITION_CREATED=true\n",
        "\nPOSITION_OPENING_AUTHORIZED=true\n",
        "\nPARTIAL_FILL_AUTHORIZED=true\n",
        "\nFUNDING_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nRUNTIME_EXECUTION_AUTHORIZED=true\n",
        "\nOKX_API_CALL_PERFORMED=true\n",
        "\nFILLED_POSITION_DERIVED_RUNTIME_STATE_AUTHORIZED=true\n",
        "\nFUTURE_RUNTIME_PROTOCOL_DOCUMENTED=true\n",
        "\nTERMINAL_VERDICT_A_SELECTED=true\n",
        "\nTERMINAL_VERDICT_C_SELECTED=true\n",
        "\nADJUDICATION=A\n",
        "\nADJUDICATION=C\n",
        "\nADJUDICATION=D\n",
        "\nG_USD_EQUALS_USDC=true\n",
        "\nE_LIVE_REDUCE_ONLY_CLOSE_PRODUCTIVELY_PROVEN=true\n",
        "\nI_PROVEN_FAIL_CLOSED_RECOVERY_WITHOUT_HUMAN_IMPROVISATION=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2Y marker present: {marker!r}"


def test_z2y_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2Y |" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}" in mot
    assert "historical next pointer superseded by §11.13.5.Z2Y" in mot
    assert "historical next pointer superseded by §11.13.5.Z2Z" in mot
    assert "ADJUDICATION=B" in mot
    assert "FUTURE_RUNTIME_PROTOCOL_DOCUMENTED=false" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={CONSUMED_Z2X_POINTER}\n" not in mot
