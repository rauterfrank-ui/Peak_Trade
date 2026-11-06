"""§11.13.5.Z2Z evidence-model re-adjudication.

Docs/governance invariants only. Binds first-party linear notional/UPL
algebra, venue close-position market capability, and OEM last-updated
metadata without closing Z2Y safety dependencies, authorizing runtime,
or changing Adjudication B.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2Z_HEADING = "### 11.13.5.Z2Z Evidence-model re-adjudication"
Z2Y_HEADING = "### 11.13.5.Z2Y Filled-position-derived probe is not presently authorizable"
Z2AB_HEADING = "### 11.13.5.Z2AB Productive runtime proof is not pre-submit admissible"
Z2AC_HEADING = "### 11.13.5.Z2AC LF-06 venue semantics evidence persist"
Z2AA_HEADING = "### 11.13.5.Z2AA Earliest Z2Y safety dependency is not statically provable"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_SEPARATE_FOR_UNRESOLVED_SAFETY_DEPENDENCIES_BEFORE_ANY_"
    "FILLED_POSITION_DERIVED_RUNTIME_PROPOSAL_FACE_VALUE_CONFLICT_UNRESOLVED_"
    "COVER_USDC_UNINSTANTIATED_FUNDING_PREREQUISITE_UNSATISFIED_LIVE_FLATTEN_"
    "UNPROVEN_FILL_DETERMINISM_UNPROVEN_QTY_ONE_NOT_VENUE_ADMISSIBLE_AT_ZERO_"
    "EQUITY_RULE_C_UNPROVEN_SUPPORT_CONTACT_NOT_AUTHORIZED_CANARY_NOT_AUTHORIZED"
)
OWNER_GO = "OWNER_GO_Z2Y_EVIDENCE_MODEL_RE_ADJUDICATION_DOCS_ONLY"
BASELINE_SHA = "44294632218c899d12430043ae16713c9b7b7fc9"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2z_section(text: str) -> str:
    start = text.find(Z2Z_HEADING)
    assert start >= 0, "missing §11.13.5.Z2Z heading"
    end = text.find(Z2AA_HEADING, start)
    assert end > start, "missing §11.13.5.Z2AA boundary after Z2Z"
    return text[start:end]


def test_z2z_heading_is_unique_and_follows_z2y() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2Z_HEADING) == 1
    z2y = text.find(Z2Y_HEADING)
    z2z = text.find(Z2Z_HEADING)
    z2aa = text.find(Z2AA_HEADING)
    z2ab = text.find(Z2AB_HEADING)
    z2ac = text.find(Z2AC_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2y < z2z < z2aa < z2ab < z2ac < ladder


def test_z2z_docs_bind_first_party_evidence_model_without_closing_safety() -> None:
    section = _z2z_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=Z2Y_EVIDENCE_MODEL_RE_ADJUDICATION_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "ADJUDICATION=B",
        "ADJUDICATION_CLASS=FILLED_POSITION_DERIVED_PROBE_NOT_PRESENTLY_AUTHORIZABLE",
        "POSITION_NOTIONAL_ALGEBRA_STATUS=FIRST_PARTY_DOCUMENTED",
        "LINEAR_NOTIONAL_USD_ALGEBRA=sz*ctVal*markPx",
        "LINEAR_UPL_ALGEBRA_STATUS=FIRST_PARTY_DOCUMENTED",
        "LINEAR_UPL_ALGEBRA=(markPx-avgPx)*pos*ctVal",
        "COVER_USDC_EVIDENCE_CLASS=ALGEBRA_PROVEN_BUT_NUMERIC_INSTANTIATION_BLOCKED_BY_CTVAL_AUTHORITY_CONFLICT_AND_ACCOUNT_SETTLEMENT_CURRENCY_OPERATOR",
        "VENUE_CLOSE_POSITION_MARKET_CAPABILITY=FIRST_PARTY_DOCUMENTED",
        "VENUE_CLOSE_POSITION_DOCUMENTED_BEHAVIOR=CLOSE_THE_POSITION_OF_AN_INSTRUMENT_VIA_A_MARKET_ORDER",
        "PEAK_TRADE_CLOSE_POSITION_ALLOWLISTED=false",
        "PEAK_TRADE_CLOSE_POSITION_PRODUCTIVELY_PROVEN=false",
        "LIVE_FLATTEN_PROVABILITY=UNPROVEN_HARD_STOP",
        "VENUE_CAPABILITY_IS_NOT_PEAK_TRADE_LIVE_FLATTEN=true",
        "PREVIOUS_OEM_LAST_UPDATED_ASSERTION=20_AUG_2026_REPRODUCED",
        "CURRENT_FIRST_PARTY_OEM_LAST_UPDATED=20_AUGUST_2026",
        "OEM_SPEC_12_AUG_2026_FIRST_PARTY_REPRODUCED=false",
        "OEM_SPEC_METADATA_CORRECTION_REQUIRED=false",
        "SRC_OEM_SPEC_CONTRACT_SIZE=0.01_BTC",
        "TARGET_API_CTVAL=0.0001_BTC",
        "VENUE_HAS_NON_LIMIT_ONLY_EXECUTION_PRIMITIVES=true",
        "CURRENT_PEAK_TRADE_LIFECYCLE=LIMIT_ONLY_NO_MARKET",
        "FILL_DETERMINISM_STATUS=UNPROVEN",
        "FOK_IS_NOT_FILL_GUARANTEE=true",
        "FACE_VALUE_CONFLICT_STATUS=UNRESOLVED",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "FUNDING_PREREQUISITE_STATUS=UNSATISFIED",
        "WORST_CASE_LOSS_BOUND_STATUS=UNINSTANTIABLE",
        "LIQUIDATION_SAFETY_STATUS=UNPROVEN_WITHOUT_MONETARY_BASE_AND_FACE_VALUE",
        "MONETARY_BASE_NUMERICALLY_RESOLVED=false",
        "NEW_FIRST_PARTY_EVIDENCE_CLOSES_Z2Y_SAFETY_DEPENDENCY=false",
        "NEW_EVIDENCE_CHANGES_RUNTIME_AUTHORIZATION=false",
        "FILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=false",
        "FILLED_POSITION_DERIVED_RUNTIME_STATE_AUTHORIZED=false",
        "FUTURE_RUNTIME_PROTOCOL_DOCUMENTED=false",
        "RULE_C_STATUS=UNPROVEN",
        "NO_ALLOWLIST_EXPANSION=true",
        "NO_POST=true",
        "NO_OKX_API_CALL=true",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUPPORT_CONTACT_AUTHORIZED=false",
        "NO_CAPABILITY_ADVANCEMENT=true",
        "NEXT_OWNER_AUTHORIZATION_REQUIRED=true",
        "HARD_STOP_AFTER_THIS_TASK=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
    )
    for marker in required:
        assert marker in section, f"missing Z2Z marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nRULE_C_STATUS=PROVEN\n",
        "\nFACE_VALUE_CONFLICT_STATUS=RESOLVED\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nMONETARY_BASE_NUMERICALLY_RESOLVED=true\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
        "\nFILL_DETERMINISM_STATUS=PROVEN\n",
        "\nPEAK_TRADE_CLOSE_POSITION_ALLOWLISTED=true\n",
        "\nPEAK_TRADE_CLOSE_POSITION_PRODUCTIVELY_PROVEN=true\n",
        "\nOEM_SPEC_METADATA_CORRECTION_REQUIRED=true\n",
        "\nOEM_SPEC_12_AUG_2026_FIRST_PARTY_REPRODUCED=true\n",
        "\nFILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=true\n",
        "\nFUTURE_RUNTIME_PROTOCOL_DOCUMENTED=true\n",
        "\nADJUDICATION=A\n",
        "\nADJUDICATION=C\n",
        "\nNEW_FIRST_PARTY_EVIDENCE_CLOSES_Z2Y_SAFETY_DEPENDENCY=true\n",
        "\nNEW_EVIDENCE_CHANGES_RUNTIME_AUTHORIZATION=true\n",
        "\nNO_USD_EQUALS_USDC=false\n",
        "\nNO_ALLOWLIST_EXPANSION=false\n",
        "\nOKX_API_CALL_PERFORMED=true\n",
        "\nORDER_SUBMITTED=true\n",
        "\nFUNDING_PERFORMED=true\n",
        "\nCANARY_PERFORMED=true\n",
        "\nSUPPORT_CONTACT_PERFORMED=true\n",
    )
    for marker in forbidden:
        assert marker not in section, f"forbidden Z2Z marker present: {marker!r}"


def test_z2z_map_of_truth_navigation_pointer_matches_runbook() -> None:
    mot = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2Z |" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_POINTER}\n" not in mot
    assert "historical next pointer superseded by §11.13.5.Z2Z" in mot
    assert "historical next pointer superseded by §11.13.5.Z2AA" in mot
    assert "POSITION_NOTIONAL_ALGEBRA_STATUS=FIRST_PARTY_DOCUMENTED" in mot
    assert "VENUE_CLOSE_POSITION_MARKET_CAPABILITY=FIRST_PARTY_DOCUMENTED" in mot
    assert "OEM_SPEC_METADATA_CORRECTION_REQUIRED=false" in mot
    assert "ADJUDICATION=B" in mot
    assert "FILLED_POSITION_DERIVED_RUNTIME_AUTHORIZED=false" in mot
