"""Docs/contract invariants for §11.13.5.Z2B ticket 7823581 evidence.

Reads canonical docs only. Does not change trading logic, runtime,
activation, orders, credentials, or funding. Distinguishes a proven
non-operative 0.01% rate from an unproven operative computation.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
CANARY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_V1.md"
)

Z2B_HEADING = (
    "### 11.13.5.Z2B OKX ticket 7823581 normal-expiry fee applicability and non-operative rate"
)
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_"
    "OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_MONETARY_BASE"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2b_section(text: str) -> str:
    start = text.find(Z2B_HEADING)
    assert start >= 0, "missing §11.13.5.Z2B heading"
    end = text.find("### 11.13.5.Z2C", start)
    assert end > start, "missing §11.13.5.Z2C boundary after Z2B"
    return text[start:end]


def test_z2b_binds_ticket_7823581_applicability_and_non_operative_rate() -> None:
    section = _z2b_section(_read(MASTER_RUNBOOK))
    required = (
        "TICKET_ID=7823581",
        "OWNER_GO=OWNER_GO_BIND_OKX_TICKET_7823581",
        "OWNER_GO_STATUS=CONSUMED",
        "PRODUCT_SET_MEMBERSHIP=PROVEN",
        "TARGET_INSTRUMENT_APPLICABILITY_BTC_USD_UM_XPERP=PROVEN",
        "NORMAL_EXPIRY_FEE_RATE_PROVEN=true",
        "NORMAL_EXPIRY_FEE_RATE_DECIMAL=0.0001",
        "NORMAL_EXPIRY_FEE_RATE_PERCENT=0.01",
        "RATE_PROVEN_NON_OPERATIVE=true",
        "TIER_INDEPENDENT_FOR_EXPIRY_SETTLEMENT=PROVEN",
        "FORCED_LIQUIDATION_DISTINCT_FROM_NORMAL_EXPIRY=PROVEN",
        "E4_0_01_SENTENCE_TO_EXACT_PRODUCT_SET_X=PROVEN",
        "E5_TARGET_IN_X=PROVEN",
        "APPLIES_PROVEN=true",
        "APPLICABILITY_VERDICT=A",
        "FINAL_VERDICT=A",
        "DELIVERY_TERM_APPLICABILITY_STATUS=APPLIES",
        "SUPPORT_EVIDENCE_STATUS=BOUND",
        "TARGET_INSTRUMENT=BTC-USD_UM_XPERP",
    )
    for marker in required:
        assert marker in section, f"missing Z2B evidence marker: {marker}"


def test_z2b_keeps_monetary_base_and_api_delivery_and_operative_computation_unproven() -> None:
    section = _z2b_section(_read(MASTER_RUNBOOK))
    required = (
        "MONETARY_BASE_STATUS=UNPROVEN",
        "API_DELIVERY_0_0003_STATUS=UNPROVEN",
        "OPERATIVE_FEE_COMPUTATION_PROVEN=false",
        "DELIVERY_RATE_OPERATIVE_VALUE=NONE",
        "OPERATIVE_EXPIRY_FEE_RATE=NONE",
        "PUBLIC_001_PERCENT_OPERATIVE=false",
        "W_PACK_DELIVERY_0_0003_NOT_OPERATIVE=true",
        "DELIVERY_FEE_TERM_NUMERIC_STATUS=UNINSTANTIATED",
        "FULL_OPERATIONAL_RESERVE_COMPOSITION_STATUS=BLOCKED",
        "TRADE_FEE_DELIVERY_FIELD_EVENT_B_APPLICABILITY=UNPROVEN",
        "NO_MONETARY_BASE_INVENTION",
        "NO_NOTIONAL_ASSUMPTION",
        "NO_IDENTIFYING_API_DELIVERY_0003_WITH_001_PERCENT",
        "NO_PUBLIC_001_PERCENT_PROMOTION_TO_OPERATIVE",
        "LIVE_AUTHORIZED=false",
        "TRADING_LOGIC_CHANGED=false",
        "RUNTIME_CHANGED=false",
        "CONFIG_CHANGED=false",
        "NEW_SUPPORT_MESSAGE_SENT=false",
        "TICKET_RATED=false",
    )
    for marker in required:
        assert marker in section, f"missing Z2B fail-closed marker: {marker}"
    forbidden_assignments = (
        "\nOPERATIVE_EXPIRY_FEE_RATE=0.0001\n",
        "\nOPERATIVE_EXPIRY_FEE_RATE=0.0003\n",
        "\nOPERATIVE_EXPIRY_FEE_RATE=0\n",
        "\nDELIVERY_RATE_OPERATIVE_VALUE=0.0001\n",
        "\nDELIVERY_RATE_OPERATIVE_VALUE=0.0003\n",
        "\nMONETARY_BASE_STATUS=PROVEN\n",
        "\nAPI_DELIVERY_0_0003_STATUS=PROVEN\n",
        "\nOPERATIVE_FEE_COMPUTATION_PROVEN=true\n",
        "\nLIVE_AUTHORIZED=true\n",
        "\nFUNDING_AMOUNT_PROVEN=true\n",
    )
    for assignment in forbidden_assignments:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"


def test_z2b_consumes_applicability_pointer_and_points_to_monetary_base() -> None:
    section = _z2b_section(_read(MASTER_RUNBOOK))
    assert (
        "11F_OKX_TICKET_7823581_NORMAL_EXPIRY_FEE_APPLICABILITY_AND_RATE_BOUND_NON_OPERATIVE"
        in section
    )
    assert f"CANONICAL_NEXT_STEP={NEXT_POINTER}" in section
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=NORMAL_EXPIRY_FEE_MONETARY_BASE_UNPROVEN" in section
    assert "LIVE_AUTHORIZED=false" in section


def test_map_of_truth_and_spec_record_z2b_as_consumed_historical() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2B" in mot
    assert "OWNER_GO_BIND_OKX_TICKET_7823581_STATUS=CONSUMED_DOCS_ONLY_RATE_NON_OPERATIVE" in mot
    assert (
        "OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_MONETARY_BASE_STATUS=SUPERSEDED_NOT_CRITICAL_PATH_FOR_MINIMUM_EXPOSURE_CANARY"
        in mot
    )
    assert "OPERATIVE_EXPIRY_FEE_RATE=NONE" in mot
    assert "OWNER_GO_BIND_OKX_TICKET_7823581" in spec
    assert NEXT_POINTER in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2B." not in spec
