"""§11.13.5.Z2CX remaining unranked Z2AR offline reproof bundle.

Orchestrates three already-separated class adjudications. Does not
collapse classes. Does not reopen FX. Does not adjudicate COVER_USDC.
Does not authorize Live, Testnet, GET, POST, flatten, Class D, or Z2AP.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_finished_risk_envelope_numeric_offline_reproof_v1 import (
    CONTRADICTION_COUNT as FINISHED_RISK_ENVELOPE_NUMERIC_CONTRADICTION_COUNT,
    FORENSIC_SOURCE_COUNT as FINISHED_RISK_ENVELOPE_NUMERIC_FORENSIC_SOURCE_COUNT,
    adjudicate_finished_risk_envelope_numeric_offline_reproof_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_fx_offline_reproof_v1 import (
    CURRENT_FX_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_rounding_offline_reproof_v1 import (
    CONTRADICTION_COUNT as ROUNDING_CONTRADICTION_COUNT,
    FORENSIC_SOURCE_COUNT as ROUNDING_FORENSIC_SOURCE_COUNT,
    adjudicate_rounding_offline_reproof_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_usd_usdc_account_settlement_offline_reproof_v1 import (
    CONTRADICTION_COUNT as USD_USDC_ACCOUNT_SETTLEMENT_CONTRADICTION_COUNT,
    FORENSIC_SOURCE_COUNT as USD_USDC_ACCOUNT_SETTLEMENT_FORENSIC_SOURCE_COUNT,
    adjudicate_usd_usdc_account_settlement_offline_reproof_v1,
)

OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2AR_REMAINING_UNRANKED_OFFLINE_REPROOF_BUNDLE_V1"
THIS_SLICE = "11.13.5.Z2CX"
PREDECESSOR_SLICE = "11.13.5.Z2CW"
FX_STATUS = CURRENT_FX_STATUS
FX_REOPENED = False
COVER_USDC_ADJUDICATED = False
SUI_REPROOF_CLASSES_RANKED = False
REMAINING_UNRANKED_AFTER_THIS_BUNDLE: tuple[str, ...] = ()
FORENSIC_SOURCE_COUNT = (
    ROUNDING_FORENSIC_SOURCE_COUNT
    + FINISHED_RISK_ENVELOPE_NUMERIC_FORENSIC_SOURCE_COUNT
    + USD_USDC_ACCOUNT_SETTLEMENT_FORENSIC_SOURCE_COUNT
)
CONTRADICTION_COUNT = (
    ROUNDING_CONTRADICTION_COUNT
    + FINISHED_RISK_ENVELOPE_NUMERIC_CONTRADICTION_COUNT
    + USD_USDC_ACCOUNT_SETTLEMENT_CONTRADICTION_COUNT
)
NEXT_AUTHORITY_BOUNDARY = "SEPARATE_OWNER_MERGE_GO"


class LiveCanaryZ2arRemainingUnrankedOfflineReproofBundleError(RuntimeError):
    """Fail-closed remaining-unranked bundle violation."""


def _fail(code: str) -> None:
    raise LiveCanaryZ2arRemainingUnrankedOfflineReproofBundleError(code)


def adjudicate_remaining_unranked_offline_reproof_bundle_v1(
    *,
    mix_classes: bool = False,
    reopen_fx: bool = False,
    adjudicate_cover_usdc: bool = False,
    claimed_any_reproven: bool = False,
) -> dict[str, Any]:
    """Run three separate class adjudications. Do not mix verdicts."""
    if mix_classes:
        _fail("FORBIDDEN_CLASS_MIXING")
    if reopen_fx:
        _fail("FORBIDDEN_FX_REOPEN")
    if adjudicate_cover_usdc:
        _fail("FORBIDDEN_COVER_USDC_ADJUDICATION")
    if claimed_any_reproven:
        _fail("FORBIDDEN_REPROVEN_MISSING_REQUIRED_INPUTS")
    if CURRENT_FX_STATUS != "NOT_REPROVEN_MISSING_EVIDENCE":
        _fail("DRIFT_FX_STATUS_REOPENED")

    rounding = adjudicate_rounding_offline_reproof_v1()
    envelope = adjudicate_finished_risk_envelope_numeric_offline_reproof_v1()
    settlement = adjudicate_usd_usdc_account_settlement_offline_reproof_v1()
    if rounding["Z2AR_CLASS"] == envelope["Z2AR_CLASS"]:
        _fail("FORBIDDEN_CLASS_MIXING")
    if rounding["Z2AR_CLASS"] == settlement["Z2AR_CLASS"]:
        _fail("FORBIDDEN_CLASS_MIXING")
    if envelope["Z2AR_CLASS"] == settlement["Z2AR_CLASS"]:
        _fail("FORBIDDEN_CLASS_MIXING")
    if rounding["ADJUDICATION"] == "REPROVEN" or envelope["ADJUDICATION"] == "REPROVEN":
        _fail("FORBIDDEN_REPROVEN_MISSING_REQUIRED_INPUTS")
    if settlement["ADJUDICATION"] == "REPROVEN":
        _fail("FORBIDDEN_REPROVEN_MISSING_REQUIRED_INPUTS")

    return {
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "ROUNDING_STATUS": rounding["ADJUDICATION"],
        "FINISHED_RISK_ENVELOPE_NUMERIC_STATUS": envelope["ADJUDICATION"],
        "USD_USDC_ACCOUNT_SETTLEMENT_STATUS": settlement["ADJUDICATION"],
        "FX_STATUS": FX_STATUS,
        "FX_REOPENED": FX_REOPENED,
        "COVER_USDC_ADJUDICATED": COVER_USDC_ADJUDICATED,
        "ROUNDING": rounding,
        "FINISHED_RISK_ENVELOPE_NUMERIC": envelope,
        "USD_USDC_ACCOUNT_SETTLEMENT": settlement,
        "FORENSIC_SOURCE_COUNT": FORENSIC_SOURCE_COUNT,
        "CONTRADICTION_COUNT": CONTRADICTION_COUNT,
        "SUI_REPROOF_CLASSES_RANKED": SUI_REPROOF_CLASSES_RANKED,
        "REMAINING_UNRANKED_AFTER_THIS_BUNDLE": REMAINING_UNRANKED_AFTER_THIS_BUNDLE,
        "GET_PERFORMED": False,
        "POST_PERFORMED": False,
        "FLATTEN_PERFORMED": False,
        "CLASS_D_CONSUMED": False,
        "Z2AP_CONSUMED": False,
        "EXECUTION_READY": False,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
    }
