"""§11.13.5.Z2CW FX offline reproof contract. Offline only."""

from __future__ import annotations

from typing import Any

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_fx_offline_reproof_v1 import (
    ADJUDICATION,
    CENSUS_ENTRIES,
    CENSUS_COMPLETE,
    CURRENT_FX_STATUS,
    EPISTEMIC_CLASSES_PRESENT,
    FORBIDDEN_COLLAPSE_CLASSES,
    FORENSIC_SOURCE_COUNT,
    FX_STATUS,
    LiveCanaryZ2arFxOfflineReproofError,
    OWNER_GO,
    REMAINING_UNRANKED_AFTER_THIS_CLASS,
    REPROOF_PROVEN,
    THIS_GO_AUTHORIZES_FLATTEN,
    THIS_GO_AUTHORIZES_GET,
    THIS_GO_AUTHORIZES_POST,
    Z2AR_CLASS,
    adjudicate_fx_offline_reproof_v1,
    reject_class_collapse_v1,
    reject_historical_or_navigation_upgrade_v1,
    reject_idxpx_one_normalization_v1,
    reject_implied_runtime_v1,
    reject_reproven_without_required_inputs_v1,
    reject_usd_equals_usdc_normalization_v1,
)


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_Z2CW_CONTRACT_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def test_adjudication_constants_are_fail_closed() -> None:
    assert Z2AR_CLASS == "FX"
    assert ADJUDICATION == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert CURRENT_FX_STATUS == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert REPROOF_PROVEN is False
    assert FX_STATUS == "UNPROVEN"
    assert CENSUS_COMPLETE is True
    assert FORENSIC_SOURCE_COUNT == len(CENSUS_ENTRIES)
    assert FORENSIC_SOURCE_COUNT >= 20
    assert THIS_GO_AUTHORIZES_GET is False
    assert THIS_GO_AUTHORIZES_POST is False
    assert THIS_GO_AUTHORIZES_FLATTEN is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert "COVER_USDC" in FORBIDDEN_COLLAPSE_CLASSES
    assert "ROUNDING" in FORBIDDEN_COLLAPSE_CLASSES
    assert "USD_USDC_ACCOUNT_SETTLEMENT" in FORBIDDEN_COLLAPSE_CLASSES
    assert "FX" not in REMAINING_UNRANKED_AFTER_THIS_CLASS
    assert REMAINING_UNRANKED_AFTER_THIS_CLASS == (
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
            assert "NOT_CURRENT_SUI_FX_OPERATOR" in str(row["current_applicability"])


def test_default_adjudication_is_not_reproven_missing_evidence() -> None:
    result = adjudicate_fx_offline_reproof_v1()
    assert result["ADJUDICATION"] == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert result["REPROOF_PROVEN"] is False
    assert result["FX_STATUS"] == "UNPROVEN"
    assert result["GET_PERFORMED"] is False
    assert result["EXECUTION_READY"] is False
    assert result["CENSUS_COMPLETE"] is True
    assert result["FORENSIC_SOURCE_COUNT"] == FORENSIC_SOURCE_COUNT
    assert result["CONTRADICTION_COUNT"] == 0
    assert result["IDXPX_1_IS_NOT_FX_OPERATOR"] is True
    assert result["USD_EQUALS_USDC_ASSUMED"] is False


def test_forbid_upgrade_historical_to_proven() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_historical_or_navigation_upgrade_v1(upgrade_historical_to_proven=True)
    assert str(exc.value) == "FORBIDDEN_UPGRADE_HISTORICAL_TO_PROVEN"


def test_forbid_upgrade_navigation_to_proven() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_historical_or_navigation_upgrade_v1(upgrade_navigation_to_proven=True)
    assert str(exc.value) == "FORBIDDEN_UPGRADE_NAVIGATION_TO_PROVEN"


def test_forbid_idxpx_one_normalized_to_fx_proven() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_idxpx_one_normalization_v1(treat_idxpx_one_as_fx_proven=True)
    assert str(exc.value) == "FORBIDDEN_IDXPX_1_NORMALIZED_TO_FX_PROVEN"


def test_forbid_usd_equals_usdc_normalized_to_operator() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_usd_equals_usdc_normalization_v1(treat_usd_equals_usdc_as_operator=True)
    assert str(exc.value) == "FORBIDDEN_USD_EQUALS_USDC_NORMALIZED_TO_OPERATOR"


def test_forbid_collapse_with_rounding() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_class_collapse_v1(mix_with_rounding=True)
    assert str(exc.value) == "FORBIDDEN_COLLAPSE_FX_WITH_ROUNDING"


def test_forbid_collapse_with_account_settlement() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_class_collapse_v1(mix_with_account_settlement=True)
    assert str(exc.value) == "FORBIDDEN_COLLAPSE_FX_WITH_ACCOUNT_SETTLEMENT"


def test_forbid_collapse_with_cover_usdc() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_class_collapse_v1(mix_with_cover_usdc=True)
    assert str(exc.value) == "FORBIDDEN_COLLAPSE_FX_WITH_COVER_USDC"


def test_forbid_implied_venue_observation() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_implied_runtime_v1(implied_venue_observation=True)
    assert str(exc.value) == "FORBIDDEN_IMPLIED_VENUE_OBSERVATION"


def test_forbid_execution_ready_from_reproof() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_implied_runtime_v1(execution_ready_claim=True)
    assert str(exc.value) == "FORBIDDEN_EXECUTION_READY_FROM_REPROOF"


def test_forbid_class_d_and_z2ap_consume() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_implied_runtime_v1(class_d_consumed_claim=True)
    assert str(exc.value) == "FORBIDDEN_CLASS_D_CONSUME"
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_implied_runtime_v1(z2ap_consumed_claim=True)
    assert str(exc.value) == "FORBIDDEN_Z2AP_CONSUME"


def test_forbid_reproven_claim() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        reject_reproven_without_required_inputs_v1(
            claimed_status="REPROVEN",
            claimed_reproof_proven=True,
        )
    assert str(exc.value) == "FORBIDDEN_REPROVEN_MISSING_REQUIRED_INPUTS"


def test_adjudicate_rejects_idxpx_and_parity_upgrades() -> None:
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        adjudicate_fx_offline_reproof_v1(treat_idxpx_one_as_fx_proven=True)
    assert str(exc.value) == "FORBIDDEN_IDXPX_1_NORMALIZED_TO_FX_PROVEN"
    with pytest.raises(LiveCanaryZ2arFxOfflineReproofError) as exc:
        adjudicate_fx_offline_reproof_v1(treat_usd_equals_usdc_as_operator=True)
    assert str(exc.value) == "FORBIDDEN_USD_EQUALS_USDC_NORMALIZED_TO_OPERATOR"


def test_owner_go_is_not_flatten_execute() -> None:
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token="I_AUTHORIZE_SECTION_11_13_5_FLATTEN_EXECUTE",
        purpose="SECTION_11_13_5_FLATTEN_EXECUTE",
        owner_go=OWNER_GO,
    )
    assert accepted is False
    assert "FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN" in reasons
