"""§11.13.5.Z2CV COVER_USDC offline reproof contract. Offline only."""

from __future__ import annotations

from typing import Any

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_cover_usdc_offline_reproof_v1 import (
    ADJUDICATION,
    CENSUS_ENTRIES,
    CENSUS_COMPLETE,
    COVER_USDC_STATUS,
    CURRENT_COVER_USDC_STATUS,
    EPISTEMIC_CLASSES_PRESENT,
    FORBIDDEN_COLLAPSE_CLASSES,
    FORENSIC_SOURCE_COUNT,
    LiveCanaryZ2arCoverUsdcOfflineReproofError,
    OWNER_GO,
    REMAINING_UNRANKED_AFTER_THIS_CLASS,
    REPROOF_PROVEN,
    THIS_GO_AUTHORIZES_FLATTEN,
    THIS_GO_AUTHORIZES_GET,
    THIS_GO_AUTHORIZES_POST,
    Z2AR_CLASS,
    adjudicate_cover_usdc_offline_reproof_v1,
    reject_class_collapse_v1,
    reject_historical_or_navigation_upgrade_v1,
    reject_implied_runtime_v1,
    reject_reproven_without_required_inputs_v1,
)


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_Z2CV_CONTRACT_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def test_adjudication_constants_are_fail_closed() -> None:
    assert Z2AR_CLASS == "COVER_USDC"
    assert ADJUDICATION == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert CURRENT_COVER_USDC_STATUS == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert REPROOF_PROVEN is False
    assert COVER_USDC_STATUS == "UNINSTANTIATED"
    assert CENSUS_COMPLETE is True
    assert FORENSIC_SOURCE_COUNT == len(CENSUS_ENTRIES)
    assert FORENSIC_SOURCE_COUNT >= 20
    assert THIS_GO_AUTHORIZES_GET is False
    assert THIS_GO_AUTHORIZES_POST is False
    assert THIS_GO_AUTHORIZES_FLATTEN is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert "USD_USDC" in FORBIDDEN_COLLAPSE_CLASSES
    assert "FX" in FORBIDDEN_COLLAPSE_CLASSES
    assert "RISK_ENVELOPE_NUMERIC" in FORBIDDEN_COLLAPSE_CLASSES
    assert "COVER_USDC" not in REMAINING_UNRANKED_AFTER_THIS_CLASS
    assert REMAINING_UNRANKED_AFTER_THIS_CLASS == (
        "FX",
        "ROUNDING",
        "FINISHED_RISK_ENVELOPE_NUMERIC",
        "USD_USDC_ACCOUNT_SETTLEMENT",
    )


def test_census_separates_epistemic_classes_and_does_not_upgrade() -> None:
    classes = {str(row["epistemic_class"]) for row in CENSUS_ENTRIES}
    assert classes == set(EPISTEMIC_CLASSES_PRESENT)
    for row in CENSUS_ENTRIES:
        claim = str(row["claim"]).upper()
        if row["epistemic_class"] in {"NAVIGATION_INDEX_ONLY", "HISTORICAL_INTERMEDIATE_STATE"}:
            assert "REPROVEN" not in claim
        if row["epistemic_class"] == "FORENSIC_RAW_ORIGINALS":
            assert "NOT_CURRENT_SUI_COVER_USDC" in str(row["current_applicability"])


def test_default_adjudication_is_not_reproven_missing_evidence() -> None:
    result = adjudicate_cover_usdc_offline_reproof_v1()
    assert result["ADJUDICATION"] == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert result["REPROOF_PROVEN"] is False
    assert result["COVER_USDC_STATUS"] == "UNINSTANTIATED"
    assert result["GET_PERFORMED"] is False
    assert result["EXECUTION_READY"] is False
    assert result["CENSUS_COMPLETE"] is True
    assert result["FORENSIC_SOURCE_COUNT"] == FORENSIC_SOURCE_COUNT
    assert result["CONTRADICTION_COUNT"] == 0


def test_forbid_upgrade_historical_to_proven() -> None:
    with pytest.raises(LiveCanaryZ2arCoverUsdcOfflineReproofError) as exc:
        reject_historical_or_navigation_upgrade_v1(upgrade_historical_to_proven=True)
    assert str(exc.value) == "FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN"


def test_forbid_upgrade_navigation_to_proven() -> None:
    with pytest.raises(LiveCanaryZ2arCoverUsdcOfflineReproofError) as exc:
        reject_historical_or_navigation_upgrade_v1(upgrade_navigation_to_proven=True)
    assert str(exc.value) == "FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN"


def test_forbid_collapse_with_usd_usdc() -> None:
    with pytest.raises(LiveCanaryZ2arCoverUsdcOfflineReproofError) as exc:
        reject_class_collapse_v1(mix_with_usd_usdc=True)
    assert str(exc.value) == "FORBIDDEN_COLLAPSE_COVER_USDC_WITH_USD_USDC"


def test_forbid_collapse_with_fx() -> None:
    with pytest.raises(LiveCanaryZ2arCoverUsdcOfflineReproofError) as exc:
        reject_class_collapse_v1(mix_with_fx=True)
    assert str(exc.value) == "FORBIDDEN_COLLAPSE_COVER_USDC_WITH_FX"


def test_forbid_collapse_with_risk_envelope_numeric() -> None:
    with pytest.raises(LiveCanaryZ2arCoverUsdcOfflineReproofError) as exc:
        reject_class_collapse_v1(mix_with_risk_envelope_numeric=True)
    assert str(exc.value) == "FORBIDDEN_COLLAPSE_COVER_USDC_WITH_RISK_ENVELOPE_NUMERIC"


def test_forbid_implied_venue_observation() -> None:
    with pytest.raises(LiveCanaryZ2arCoverUsdcOfflineReproofError) as exc:
        reject_implied_runtime_v1(implied_venue_observation=True)
    assert str(exc.value) == "FORBIDDEN_IMPLIED_VENUE_OBSERVATION"


def test_forbid_execution_ready_from_reproof() -> None:
    with pytest.raises(LiveCanaryZ2arCoverUsdcOfflineReproofError) as exc:
        reject_implied_runtime_v1(execution_ready_claim=True)
    assert str(exc.value) == "FORBIDDEN_EXECUTION_READY_FROM_REPROOF"


def test_forbid_reproven_claim() -> None:
    with pytest.raises(LiveCanaryZ2arCoverUsdcOfflineReproofError) as exc:
        reject_reproven_without_required_inputs_v1(
            claimed_status="REPROVEN",
            claimed_reproof_proven=True,
        )
    assert str(exc.value) == "FORBIDDEN_REPROVEN_MISSING_REQUIRED_INPUTS"


def test_owner_go_is_not_flatten_execute() -> None:
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token="I_AUTHORIZE_SECTION_11_13_5_FLATTEN_EXECUTE",
        purpose="SECTION_11_13_5_FLATTEN_EXECUTE",
        owner_go=OWNER_GO,
    )
    assert accepted is False
    assert "FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN" in reasons
