"""Docs/contract invariants for §11.13.5.Z2A UNKNOWN/NONE delivery term.

Reads canonical docs only. Does not change trading logic, runtime,
activation, orders, credentials, or funding.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2_NEXT_POINTER = (
    "OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_"
    "OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_APPLICABILITY_STATEMENT"
)
Z2A_HEADING = (
    "### 11.13.5.Z2A Fail-closed UNKNOWN/NONE delivery term in operational reserve composition"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2a_section(text: str) -> str:
    start = text.find(Z2A_HEADING)
    assert start >= 0, "missing §11.13.5.Z2A heading"
    end = text.find("### 11.13.5.Z2B", start)
    assert end > start, "missing §11.13.5.Z2B boundary after Z2A"
    return text[start:end]


def test_z2a_unknown_none_delivery_term_contract_persisted() -> None:
    section = _z2a_section(_read(MASTER_RUNBOOK))
    required = (
        "SHARED_OPERATIONAL_RESERVE_DELIVERY_TERM_CONTRACT=true",
        "DELIVERY_TERM_APPLICABILITY_STATUS=UNPROVEN",
        "DELIVERY_RATE_OPERATIVE_VALUE=NONE",
        "OPERATIVE_EXPIRY_FEE_RATE=NONE",
        "DELIVERY_TERM_SOURCE_STATUS=PENDING",
        "DELIVERY_FEE_TERM_NUMERIC_STATUS=UNINSTANTIATED",
        "FULL_OPERATIONAL_RESERVE_COMPOSITION_STATUS=BLOCKED",
        "UNPROVEN_IS_ADMISSIBLE_INTENTIONAL_STATE=true",
        "UNPROVEN_MUST_NOT_BE_REPAIRED_BY_DEFAULTING=true",
        "NONE_MEANS_UNKNOWN_UNINSTANTIATED_WHEN_APPLICABILITY_UNPROVEN=true",
        "NONE_DOES_NOT_MEAN_ZERO=true",
        "CONSUMER_MUST_NOT_DERIVE_NUMERIC_FALLBACK_FROM_NONE=true",
        "SHARED_CONTRACT_STATE_APPLIES_LATER_IF_PROVEN",
        "SHARED_CONTRACT_STATE_DOES_NOT_APPLY_LATER_IF_PROVEN",
        "APPLIES_REQUIRES_EXPLICIT_NORMATIVE_SCOPE_ASSIGNMENT=true",
        "DOES_NOT_APPLY_REQUIRES_EXPLICIT_NORMATIVE_EXCLUSION=true",
        "NOT_APPLICABLE_FORBIDDEN_WHILE_APPLICABILITY_UNPROVEN=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2A contract marker: {marker}"


def test_z2a_silent_zero_and_silent_na_forbidden() -> None:
    section = _z2a_section(_read(MASTER_RUNBOOK))
    assert "SILENT_ZERO_FORBIDDEN=true" in section
    assert "SILENT_NA_FORBIDDEN=true" in section
    assert "NO_SILENT_ZERO" in section
    assert "NO_SILENT_NA" in section
    assert "NO_IMPLICIT_ZERO_FROM_NONE" in section
    assert "NO_IMPLICIT_0003_FROM_NONE" in section
    assert "NO_IMPLICIT_001_PERCENT_FROM_NONE" in section


def test_z2a_dlv_include_always_is_not_applicability_proof() -> None:
    section = _z2a_section(_read(MASTER_RUNBOOK))
    assert "RULE_DELIVERY=DLV-INCLUDE-ALWAYS" in section
    assert "DLV_INCLUDE_ALWAYS_IS_NOT_APPLICABILITY_PROOF=true" in section
    assert (
        "DLV_INCLUDE_ALWAYS_MEANS_TERM_MUST_NOT_BE_SILENTLY_REMOVED_OR_ZEROED_WHILE_EXISTENCE_UNRESOLVED=true"
        in section
    )
    assert "NO_TREATING_DLV_INCLUDE_ALWAYS_AS_APPLICABILITY_PROOF" in section


def test_z2a_does_not_readjudicate_edge_i_or_replace_z2_pointer() -> None:
    section = _z2a_section(_read(MASTER_RUNBOOK))
    assert "EDGE_I_STATUS=UNPROVEN" in section
    assert "APPLICABILITY_VERDICT=C" in section
    assert "FINAL_VERDICT=C" in section
    assert "APPLIES_PROVEN=false" in section
    assert "DOES_NOT_APPLY_PROVEN=false" in section
    assert "APPLICABILITY_UNPROVEN=true" in section
    assert "SUPPORT_EVIDENCE_STATUS=PENDING" in section
    assert "EDGE_I_READJUDICATED=false" in section
    assert "Z2_CANONICAL_POINTER_REPLACED=false" in section
    assert f"CANONICAL_NEXT_STEP={Z2_NEXT_POINTER}" in section
    assert "12_ONLY_IF_APPLICABILITY_PROVEN_APPLIES_THEN_SEPARATE_RATE_OPERAND_BINDING" in section
    assert "LIVE_AUTHORIZED=false" in section
    assert "FUNDING_AMOUNT_PROVEN=false" in section
    assert "TRADING_LOGIC_CHANGED=false" in section
    forbidden_assignments = (
        "\nEDGE_I_STATUS=PROVEN\n",
        "\nFINAL_VERDICT=A\n",
        "\nFINAL_VERDICT=B\n",
        "\nAPPLIES_PROVEN=true\n",
        "\nDOES_NOT_APPLY_PROVEN=true\n",
        "\nFUNDING_AMOUNT_PROVEN=true\n",
        "\nLIVE_AUTHORIZED=true\n",
        "\nOPERATIVE_EXPIRY_FEE_RATE=0\n",
        "\nOPERATIVE_EXPIRY_FEE_RATE=0.0003\n",
        "\nDELIVERY_RATE_OPERATIVE_VALUE=0\n",
        "\nDELIVERY_RATE_OPERATIVE_VALUE=0.0003\n",
    )
    for assignment in forbidden_assignments:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"


def test_map_of_truth_records_z2a_as_parallel_consumed() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2A" in text
    assert (
        "OWNER_GO_FOR_FAIL_CLOSED_UNKNOWN_NONE_DELIVERY_TERM_IN_OPERATIONAL_RESERVE_COMPOSITION_DOCS_ONLY_STATUS=CONSUMED_DOCS_ONLY_Z2_POINTER_UNCHANGED"
        in text
    )
    assert (
        "OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_APPLICABILITY_STATEMENT_STATUS=CONSUMED_BOUND_BY_OWNER_GO_BIND_OKX_TICKET_7823581"
        in text
    )
