"""§11.13.5.Z2J first-party USD-margined X-Perp settlement-semantics adjudication.

Docs/governance invariants only. Distinguishes proven settlement
semantics from unproven numeric COVER_USDC and unproven client-side FX.
Does not authorize Live, Testnet, orders, funding, scaling, or
Multi-Future.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
CANARY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_V1.md"
)

Z2J_HEADING = "### 11.13.5.Z2J First-party USD-margined X-Perp settlement-semantics adjudication"
Z2I_HEADING = (
    "### 11.13.5.Z2I Owner-ratified operative expiry-settlement rate from "
    "verified first-party OKX `delivery`"
)
Z2J_OWNER_GO = "OWNER_GO_CANONICALIZATION_RESEARCH_ADJUDICATION_ONLY"
NEXT_POINTER = (
    "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_"
    "COVER_USDC_TERMS_AFTER_CURRENT_TICKER_BID_ASK_BEFORE_FUNDING"
)
BASELINE_SHA = "120e5aca4f8d57fb4362489709921c7ff542044d"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2j_section(text: str) -> str:
    start = text.find(Z2J_HEADING)
    assert start >= 0, "missing §11.13.5.Z2J heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2J"
    return text[start:end]


def test_z2j_heading_is_unique_and_follows_z2i() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2J_HEADING) == 1
    z2i = text.find(Z2I_HEADING)
    z2j = text.find(Z2J_HEADING)
    ladder = text.find("## 11.14 Live order and economic evidence ladder")
    assert 0 <= z2i < z2j < ladder


def test_z2j_docs_bind_semantic_adjudication_without_instantiating_cover() -> None:
    section = _z2j_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=USD_M_XPERP_SETTLEMENT_SEMANTIC_ADJUDICATION_DOCS_ONLY",
        "PARALLEL_TO_SECTION_11_13_5_Z2I=true",
        "Z2H_CANONICAL_POINTER_REPLACED=false",
        "Z2I_OPERATIVE_EXPIRY_RATE_REMAINS_BINDING=true",
        f"OWNER_GO={Z2J_OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"BASELINE_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "CANARY_INSTRUMENT=BTC-USD_UM_XPERP-310404",
        "ACCOUNT_SETTLE_CCY=USDC",
        "PUBLIC_SETTLE_CCY=USD",
        "SEMANTIC_PROPOSITION_VERDICT=PROVEN",
        "NUMERIC_PROPOSITION_VERDICT=UNPROVEN",
        "CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN",
        "CLIENT_SIDE_FX_REQUIRED=UNPROVEN",
        "USD_USDC_CONVERSION_OPERATOR_MANDATORY=UNPROVEN",
        "MODEL_3_SEMANTICS_CANONICALIZED=true",
        "MODEL_3_NUMERIC_COVER_CANONICALIZED=false",
        "VENUE_INTERNAL_CONVERSION_SEMANTIC_PROVEN=true",
        "VENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=false",
        "CLIENT_SIDE_FX_REQUIRED_PROVEN=false",
        "PHYSICAL_USDC_COVER_AMOUNT_AVAILABLE=false",
        "IDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=false",
        "DISCOUNT_RATE_0_995_IS_USD_M_FUTURES_SETTLEMENT_OPERATOR=false",
        "MODEL_2_ADOPTED=false",
        "NAMED_REMAINING_COVER_USDC_TERM=FINITE_PHYSICAL_USDC_COVER_AMOUNT_ABSENT",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "COVER_USDC_REMAINS_UNINSTANTIATED=true",
        "NO_ONE_TO_ONE_USD_USDC_PARITY_MAY_BE_ASSUMED=true",
        "NO_NUMERIC_FX_CONVERSION_RULE_PRESENTLY_RATIFIED=true",
        "PEAK_TRADE_CLIENT_SIDE_FX_CONVERSION_NOT_PROVEN_MANDATORY=true",
        "FUNDING_AND_CANARY_REMAIN_BLOCKED=true",
        "SUPPORT_TICKET_7831485_STATUS=UNRESOLVED_NO_OEM_ANSWER",
        "SUPPORT_REPLY_MAY_NOT_BE_FABRICATED=true",
        "LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED=false",
        "ORDER_COUNT_SUBMITTED=0",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "NO_FUNDING=true",
        "NO_CANARY=true",
        f"CANONICAL_NEXT_STEP={NEXT_POINTER}",
        "EARLIEST_UNRESOLVED_DEPENDENCY=COVER_USDC_UNINSTANTIATED_REMAINING_UNPROVEN_TERMS_AFTER_CURRENT_TICKER_BID_ASK",
        "NO_INVENTED_FX_RATE=true",
        "NO_USD_EQUALS_USDC_ASSUMPTION=true",
        "LOCAL_DIRTY_TREE_IS_NOT_SSOT=true",
    )
    for marker in required:
        assert marker in section, f"missing Z2J marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCOVER_USDC_STATUS=PROVEN\n",
        "\nCOVER_USDC_STATUS=INSTANTIATED\n",
        "\nNUMERIC_PROPOSITION_VERDICT=PROVEN\n",
        "\nCLIENT_FX_PROPOSITION_VERDICT=PROVEN\n",
        "\nMODEL_3_NUMERIC_COVER_CANONICALIZED=true\n",
        "\nCLIENT_SIDE_FX_REQUIRED=true\n",
        "\nUSD_USDC_CONVERSION_OPERATOR_MANDATORY=true\n",
        "\nVENUE_NUMERIC_CONVERSION_OPERATOR_PROVEN=true\n",
        "\nPHYSICAL_USDC_COVER_AMOUNT_AVAILABLE=true\n",
        "\nIDXPX_USDC_USD_1_IS_COVER_USDC_OPERATOR=true\n",
        "\nDISCOUNT_RATE_0_995_IS_USD_M_FUTURES_SETTLEMENT_OPERATOR=true\n",
        "\nMODEL_2_ADOPTED=true\n",
        "\nLIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED=true\n",
        "\nFUNDING_EXECUTED=true\n",
        "\nNO_USD_EQUALS_USDC_ASSUMPTION=false\n",
        "\nNO_ONE_TO_ONE_USD_USDC_PARITY_MAY_BE_ASSUMED=false\n",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"


def test_map_of_truth_and_spec_record_z2j_without_replacing_z2h_or_cover() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2J" in mot
    assert (
        "OWNER_GO_CANONICALIZATION_RESEARCH_ADJUDICATION_ONLY_STATUS=CONSUMED_SEMANTIC_CLARIFICATION_NOT_EXECUTE"
        in mot
    )
    assert "SEMANTIC_PROPOSITION_VERDICT=PROVEN" in mot
    assert "NUMERIC_PROPOSITION_VERDICT=UNPROVEN" in mot
    assert "CLIENT_FX_PROPOSITION_VERDICT=UNPROVEN" in mot
    assert "MODEL_3_SEMANTICS_CANONICALIZED=true" in mot
    assert "MODEL_3_NUMERIC_COVER_CANONICALIZED=false" in mot
    assert "NAMED_REMAINING_COVER_USDC_TERM=FINITE_PHYSICAL_USDC_COVER_AMOUNT_ABSENT" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert (
        "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_"
        "COVER_USDC_TERMS_AFTER_CURRENT_TICKER_BID_ASK_BEFORE_FUNDING_STATUS="
        "CONSUMED_GET_ONLY_PUBLIC_TIER_MMR_OBSERVED_NOT_COVER_USDC" in mot
    )
    assert "Current SSOT: Master Runbook §11.13.5.Z2K." in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2H." not in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2J." not in spec
    assert "§11.13.5.Z2J" in spec
    assert "`COVER_USDC` remains `UNINSTANTIATED`" in spec
    assert "CLIENT_SIDE_FX_REQUIRED=true" not in mot
    assert "USD_USDC_CONVERSION_OPERATOR_MANDATORY=true" not in mot
