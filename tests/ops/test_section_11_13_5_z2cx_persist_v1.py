"""§11.13.5.Z2CX remaining unranked offline reproof persist invariants.

Docs/governance plus offline adjudication. No runtime. No venue GET.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_finished_risk_envelope_numeric_offline_reproof_v1 import (
    FORENSIC_SOURCE_COUNT as ENVELOPE_SOURCE_COUNT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_remaining_unranked_offline_reproof_bundle_v1 import (
    FORENSIC_SOURCE_COUNT,
    OWNER_GO as BUNDLE_OWNER_GO,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_rounding_offline_reproof_v1 import (
    FORENSIC_SOURCE_COUNT as ROUNDING_SOURCE_COUNT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_usd_usdc_account_settlement_offline_reproof_v1 import (
    FORENSIC_SOURCE_COUNT as SETTLEMENT_SOURCE_COUNT,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2CW_HEADING = "### 11.13.5.Z2CW FX remaining unranked SUI offline reproof persist"
Z2CX_HEADING = "### 11.13.5.Z2CX remaining unranked SUI offline reproof bundle persist"
Z2CY_HEADING = "### 11.13.5.Z2CY Post-Z2CX P3 dependency reconciliation and next-blocker persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2AR_REMAINING_UNRANKED_OFFLINE_REPROOF_BUNDLE_V1"
BASELINE_SHA = "73d135f0419f01242f5c563e9a4c311546ff80e1"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2cx_section(text: str) -> str:
    start = text.find(Z2CX_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CX heading"
    end = text.find(Z2CY_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CY boundary after Z2CX"
    return text[start:end]


def _z2cw_section(text: str) -> str:
    start = text.find(Z2CW_HEADING)
    assert start >= 0, "missing §11.13.5.Z2CW heading"
    end = text.find(Z2CX_HEADING, start)
    assert end > start, "missing §11.13.5.Z2CX boundary after Z2CW"
    return text[start:end]


def test_z2cx_heading_is_unique_and_follows_z2cw() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2CX_HEADING) == 1
    z2cw = text.find(Z2CW_HEADING)
    z2cx = text.find(Z2CX_HEADING)
    z2cy = text.find(Z2CY_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2cw < z2cx < z2cy < ladder


def test_z2cw_historical_fx_slice_was_not_rewritten() -> None:
    section = _z2cw_section(_read(MASTER_RUNBOOK))
    assert "ADJUDICATION=NOT_REPROVEN_MISSING_EVIDENCE" in section
    assert "EXACT_Z2AR_CLASS=FX" in section
    assert "CURRENT_FX_STATUS=NOT_REPROVEN_MISSING_EVIDENCE" in section
    assert (
        "REMAINING_UNRANKED_AFTER_THIS_CLASS=ROUNDING;FINISHED_RISK_ENVELOPE_NUMERIC;USD_USDC_ACCOUNT_SETTLEMENT"
        in section
    )
    assert "ROUNDING_ADJUDICATED_THIS_PERSIST=false" in section
    assert "GET_EXECUTED_THIS_PERSIST=false" in section
    assert "Z2CX" not in section


def test_z2cx_docs_bind_three_fail_closed_classes_without_get() -> None:
    section = _z2cx_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2CX_Z2AR_REMAINING_UNRANKED_OFFLINE_REPROOF_BUNDLE_DOCS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "PREDECESSOR_SLICE=11.13.5.Z2CW",
        "LAST_CANONICALLY_CLOSED_11_13_5_SLICE=SECTION_11_13_5_Z2CT",
        "THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE=true",
        "THIS_NAMED_CLASS_PERSIST_ID=SECTION_11_13_5_Z2CX",
        "ROUNDING_STATUS=NOT_REPROVEN_MISSING_EVIDENCE",
        "FINISHED_RISK_ENVELOPE_NUMERIC_STATUS=NOT_REPROVEN_MISSING_EVIDENCE",
        "USD_USDC_ACCOUNT_SETTLEMENT_STATUS=NOT_REPROVEN_MISSING_EVIDENCE",
        "ROUNDING_REPROOF_PROVEN=false",
        "FINISHED_RISK_ENVELOPE_NUMERIC_REPROOF_PROVEN=false",
        "USD_USDC_ACCOUNT_SETTLEMENT_REPROOF_PROVEN=false",
        "FX_STATUS=NOT_REPROVEN_MISSING_EVIDENCE",
        "FX_REOPENED=false",
        "COVER_USDC_ADJUDICATED=false",
        "COVER_USDC_ADJUDICATED_THIS_PERSIST=false",
        "FX_ADJUDICATED_THIS_PERSIST=false",
        "ROUNDING_ADJUDICATED_THIS_PERSIST=true",
        "FINISHED_RISK_ENVELOPE_NUMERIC_ADJUDICATED_THIS_PERSIST=true",
        "USD_USDC_ACCOUNT_SETTLEMENT_ADJUDICATED_THIS_PERSIST=true",
        "CENSUS_COMPLETE=true",
        f"ROUNDING_FORENSIC_SOURCE_COUNT={ROUNDING_SOURCE_COUNT}",
        f"FINISHED_RISK_ENVELOPE_NUMERIC_FORENSIC_SOURCE_COUNT={ENVELOPE_SOURCE_COUNT}",
        f"USD_USDC_ACCOUNT_SETTLEMENT_FORENSIC_SOURCE_COUNT={SETTLEMENT_SOURCE_COUNT}",
        f"FORENSIC_SOURCE_COUNT={FORENSIC_SOURCE_COUNT}",
        "CONTRADICTION_COUNT=0",
        "GET_EXECUTED_THIS_PERSIST=false",
        "GET_EXECUTED_UNDER_THIS_OWNER_GO=false",
        "AUTHENTICATED_GET_CALLS=0",
        "VENUE_API_CALLS=0",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
        f"CURRENT_CANONICAL_INSTRUMENT={CURRENT_SUI}",
        "SUI_REPROOF_CLASSES_RANKED=false",
        "NO_RANKING_OF_REMAINDER=true",
        "REMAINING_UNRANKED_AFTER_THIS_BUNDLE=NONE",
        "RULE_ROUNDING=RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION",
        "RULE_ROUNDING_STATUS=UNPROVEN",
        "TICK_SZ_IS_NOT_USDC_PRECISION=true",
        "NO_PROMOTION_IDENTITY_TO_FINISHED_RISK_ENVELOPE_NUMERIC=true",
        "RISK_ENVELOPE_NUMERIC_STATUS=UNINSTANTIATED",
        "USD_USDC_ACCOUNT_SETTLEMENT_PROVEN=false",
        "IDXPX_1_IS_NOT_USD_USDC_OPERATOR=true",
        "Z2J_SEMANTIC_PROPOSITION_IS_NOT_ACCOUNT_SETTLEMENT_PROOF=true",
        "NO_USD_EQUALS_USDC=true",
        "Z2CW_TEXT_REWRITTEN=false",
        "Z2CV_TEXT_REWRITTEN=false",
        "Z2AJ_TEXT_REWRITTEN=false",
        "Z2J_TEXT_REWRITTEN=false",
        "Z2CT_TEXT_REWRITTEN=false",
        "FORBIDDEN_CLASS_MIXING=true",
    )
    for token in required:
        assert token in section, token


def test_z2cx_docs_forbid_activation_and_upgrades() -> None:
    section = _z2cx_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nROUNDING_REPROOF_PROVEN=true\n",
        "\nFINISHED_RISK_ENVELOPE_NUMERIC_REPROOF_PROVEN=true\n",
        "\nUSD_USDC_ACCOUNT_SETTLEMENT_REPROOF_PROVEN=true\n",
        "\nROUNDING_STATUS=REPROVEN\n",
        "\nFINISHED_RISK_ENVELOPE_NUMERIC_STATUS=REPROVEN\n",
        "\nUSD_USDC_ACCOUNT_SETTLEMENT_STATUS=REPROVEN\n",
        "\nFX_REOPENED=true\n",
        "\nCOVER_USDC_ADJUDICATED=true\n",
        "\nCOVER_USDC_ADJUDICATED_THIS_PERSIST=true\n",
        "\nFX_ADJUDICATED_THIS_PERSIST=true\n",
        "\nSUI_REPROOF_CLASSES_RANKED=true\n",
        "\nUSD_EQUALS_USDC_ASSUMED=true\n",
        "\nIDXPX_1_IS_NOT_USD_USDC_OPERATOR=false\n",
        "\nLIVE_FLATTEN_PROVABILITY=PROVEN\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_remains_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2CX" not in text
    assert "11.13.5.Z2CX" not in text


def test_python_adjudication_matches_persist() -> None:
    assert OWNER_GO == BUNDLE_OWNER_GO
    assert FORENSIC_SOURCE_COUNT == (
        ROUNDING_SOURCE_COUNT + ENVELOPE_SOURCE_COUNT + SETTLEMENT_SOURCE_COUNT
    )
    assert FORENSIC_SOURCE_COUNT >= 54


def test_safety_non_regression_standing_flags_and_forbidden_go() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert "CATEGORY_C" not in GATE_NAMES
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
