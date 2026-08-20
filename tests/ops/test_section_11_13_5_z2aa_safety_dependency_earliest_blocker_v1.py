"""§11.13.5.Z2AA earliest Z2Y safety dependency is not statically provable.

Docs/governance invariants only. Adjudicates that live flatten is not
statically provable under LIMIT_ONLY_NO_MARKET, that the fill state
machine remains unproven/not activated, and that the next necessary
proof requires a productive runtime state (C). Does not close Z2Y
authorizability B, Rule C, Face Value, or COVER_USDC. Does not submit
orders, call OKX, fund, open a position, flatten, or unlock Canary.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2AA_HEADING = "### 11.13.5.Z2AA Earliest Z2Y safety dependency is not statically provable"
Z2AB_HEADING = "### 11.13.5.Z2AB Productive runtime proof is not pre-submit admissible"
Z2Z_HEADING = "### 11.13.5.Z2Z Evidence-model re-adjudication"
Z2Y_HEADING = "### 11.13.5.Z2Y Filled-position-derived probe is not presently authorizable"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_PRODUCTIVE_FILLED_POSITION_OR_LIVE_FLATTEN_"
    "PROOF_NOT_STATICALLY_PROVABLE_UNDER_LIMIT_ONLY_NO_MARKET_VENUE_CLOSE_IS_"
    "MARKET_FACE_VALUE_CONFLICT_UNRESOLVED_COVER_USDC_UNINSTANTIATED_FILL_"
    "DETERMINISM_UNPROVEN_RULE_C_UNPROVEN_SUPPORT_CONTACT_NOT_AUTHORIZED_"
    "CANARY_NOT_AUTHORIZED_ALLOWLIST_EXPANSION_NOT_AUTHORIZED"
)
CONSUMED_Z2Z_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_UNRESOLVED_SAFETY_DEPENDENCIES_BEFORE_ANY_"
    "FILLED_POSITION_DERIVED_RUNTIME_PROPOSAL_FACE_VALUE_CONFLICT_UNRESOLVED_"
    "COVER_USDC_UNINSTANTIATED_FUNDING_PREREQUISITE_UNSATISFIED_LIVE_FLATTEN_"
    "UNPROVEN_FILL_DETERMINISM_UNPROVEN_QTY_ONE_NOT_VENUE_ADMISSIBLE_AT_ZERO_"
    "EQUITY_RULE_C_UNPROVEN_SUPPORT_CONTACT_NOT_AUTHORIZED_CANARY_NOT_AUTHORIZED"
)
OWNER_GO = "SECTION_11_13_5_POST_Z2Z_NEXT_Z2Y_SAFETY_DEPENDENCY_WORK"
BASELINE_SHA = "d4cda097841565cbb6e94674cc93af051a754765"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2aa_section(text: str) -> str:
    start = text.find(Z2AA_HEADING)
    assert start >= 0, "missing §11.13.5.Z2AA heading"
    end = text.find(Z2AB_HEADING, start)
    assert end > start, "missing §11.13.5.Z2AB boundary after Z2AA"
    return text[start:end]


def test_z2aa_heading_is_unique_and_follows_z2z() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2AA_HEADING) == 1
    z2y = text.find(Z2Y_HEADING)
    z2z = text.find(Z2Z_HEADING)
    z2aa = text.find(Z2AA_HEADING)
    z2ab = text.find(Z2AB_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2y < z2z < z2aa < z2ab < ladder


def test_z2aa_docs_bind_adjudication_c_without_runtime_or_proven_flatten() -> None:
    section = _z2aa_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=POST_Z2Z_NEXT_Z2Y_SAFETY_DEPENDENCY_WORK_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "Z2Z_EVIDENCE_MODEL_REMAINS_BINDING=true",
        "Z2Y_AUTHORIZABILITY_ADJUDICATION_REMAINS=B",
        "SAFETY_DEPENDENCY_STEP_ADJUDICATION=C",
        "SAFETY_DEPENDENCY_STEP_ADJUDICATION_CLASS=NEXT_PROOF_REQUIRES_PRODUCTIVE_RUNTIME_STATE",
        "TERMINAL_VERDICT_A=EARLIEST_SAFETY_DEPENDENCY_PROVEN=false",
        "TERMINAL_VERDICT_B=READ_ONLY_NON_MUTATING_EVIDENCE_ACTION_IS_NEXT=false",
        "TERMINAL_VERDICT_D=INSUFFICIENT_EVIDENCE_TO_CHOOSE_A_B_C=false",
        "TERMINAL_VERDICT_C=NEXT_PROOF_REQUIRES_PRODUCTIVE_RUNTIME_STATE=true",
        "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY",
        "EARLIEST_EXECUTION_SAFETY_BLOCKER=LIVE_FLATTEN_PROVABILITY",
        "EARLIEST_NUMERIC_SAFETY_BLOCKER=FACE_VALUE_CONFLICT",
        "LIVE_FLATTEN_STATICALLY_PROVABLE_UNDER_CURRENT_CONTRACT=false",
        "VENUE_DOCUMENTED_CLOSE_IS_MARKET_ORDER=true",
        "PEAK_TRADE_LIFECYCLE_FORBIDS_MARKET=true",
        "VENUE_DOCUMENTED_CLOSE_INCOMPATIBLE_WITH_LIMIT_ONLY_NO_MARKET=true",
        "LIMIT_REDUCE_ONLY_CLOSE_INHERITS_FILL_DETERMINISM_UNPROVEN=true",
        "PEAK_TRADE_CLOSE_POSITION_ALLOWLISTED=false",
        "PEAK_TRADE_CLOSE_POSITION_PRODUCTIVELY_PROVEN=false",
        "REDUCEONLY_IN_CANARY_PAYLOAD=false",
        "LIFECYCLE_CONTRACT_ACTIVATED=false",
        "AUTONOMOUS_FAIL_CLOSED_FLATTEN_PROVEN=false",
        "VENUE_CLOSE_BINDS_TO_ENTIRE_POSITION=true",
        "VENUE_CLOSE_REQUEST_HAS_NO_SZ_PARAMETER=true",
        "RUNTIME_EVIDENCE_REQUIRED_FOR_PEAK_TRADE_LIVE_FLATTEN=true",
        "FILL_STATE_MACHINE_STATUS=DOCUMENTED_NOT_ACTIVATED_UNPROVEN",
        "SM_PRE_SUBMIT=GATED;OBS=NO_ORDER;INV=LIVE_ARMED_FALSE;REC=NONE;FC=REMAIN_GATED",
        "SM_PARTIALLY_FILLED=UNPROVEN_UNAUTHORIZED",
        "SM_FULLY_FILLED=UNPROVEN",
        "SM_CANCELED_WITH_PARTIAL_FILL=UNPROVEN_UNAUTHORIZED",
        "SM_FLAT_CONFIRMED=UNPROVEN",
        "SM_UNKNOWN_RECONCILIATION_REQUIRED=UNPROVEN",
        "LIMIT_MAY_PARTIALLY_FILL=true",
        "MARKET_CLOSE_FORBIDDEN_BY_LIFECYCLE=true",
        "WORST_CASE_LOSS_BOUND_STATUS=UNINSTANTIABLE",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN_HARD_STOP",
        "FILL_DETERMINISM=UNPROVEN",
        "RULE_C_STATUS=UNPROVEN",
        "FACE_VALUE_CONFLICT=UNRESOLVED",
        "COVER_USDC=UNINSTANTIATED",
        "USD_EQUALS_USDC_ASSUMED=false",
        "NEW_EVIDENCE_CLOSES_Z2Y_SAFETY_DEPENDENCY=false",
        "NEW_EVIDENCE_CHANGES_RUNTIME_AUTHORIZATION=false",
        "NEXT_ACTION_REQUIRES_RUNTIME_STATE=true",
        "NEXT_ACTION_REQUIRES_ORDER_SUBMIT=true",
        "NEXT_ACTION_REQUIRES_POSITION=true",
        "NEXT_ACTION_REQUIRES_FUNDING=true",
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
        "NEXT_OWNER_AUTHORIZATION_REQUIRED=true",
        "HARD_STOP_AFTER_THIS_TASK=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
    )
    for marker in required:
        assert marker in section, f"missing Z2AA marker: {marker}"
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
        "\nPEAK_TRADE_CLOSE_POSITION_ALLOWLISTED=true\n",
        "\nPEAK_TRADE_CLOSE_POSITION_PRODUCTIVELY_PROVEN=true\n",
        "\nLIVE_FLATTEN_STATICALLY_PROVABLE_UNDER_CURRENT_CONTRACT=true\n",
        "\nLIFECYCLE_CONTRACT_ACTIVATED=true\n",
        "\nFILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=true\n",
        "\nFUTURE_RUNTIME_PROTOCOL_DOCUMENTED=true\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nSAFETY_DEPENDENCY_STEP_ADJUDICATION=A\n",
        "\nSAFETY_DEPENDENCY_STEP_ADJUDICATION=B\n",
        "\nSAFETY_DEPENDENCY_STEP_ADJUDICATION=D\n",
        "\nZ2Y_AUTHORIZABILITY_ADJUDICATION_REMAINS=A\n",
        "\nZ2Y_AUTHORIZABILITY_ADJUDICATION_REMAINS=C\n",
        "\nTERMINAL_VERDICT_A=EARLIEST_SAFETY_DEPENDENCY_PROVEN=true\n",
        "\nTERMINAL_VERDICT_B=READ_ONLY_NON_MUTATING_EVIDENCE_ACTION_IS_NEXT=true\n",
        "\nNEW_EVIDENCE_CLOSES_Z2Y_SAFETY_DEPENDENCY=true\n",
        "\nNEW_EVIDENCE_CHANGES_RUNTIME_AUTHORIZATION=true\n",
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
        assert marker not in section, f"forbidden Z2AA marker present: {marker!r}"


def test_z2aa_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2AA |" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={CONSUMED_Z2Z_POINTER}\n" not in mot
    assert "historical next pointer superseded by §11.13.5.Z2AA" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AB" in mot
    assert "SAFETY_DEPENDENCY_STEP_ADJUDICATION=C" in mot
    assert "Z2Y_AUTHORIZABILITY_ADJUDICATION_REMAINS=B" in mot
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_FLATTEN_PROVABILITY" in mot
    assert "LIVE_FLATTEN_STATICALLY_PROVABLE_UNDER_CURRENT_CONTRACT=false" in mot
    assert "FILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=false" in mot
