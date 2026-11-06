"""§11.13.5.Z2CX remaining unranked offline reproof contracts. Offline only."""

from __future__ import annotations

from typing import Any

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_finished_risk_envelope_numeric_offline_reproof_v1 import (
    ADJUDICATION as ENVELOPE_ADJUDICATION,
    CENSUS_ENTRIES as ENVELOPE_CENSUS,
    EPISTEMIC_CLASSES_PRESENT as ENVELOPE_EPISTEMIC,
    FORENSIC_SOURCE_COUNT as ENVELOPE_SOURCE_COUNT,
    LiveCanaryZ2arFinishedRiskEnvelopeNumericOfflineReproofError,
    Z2AR_CLASS as ENVELOPE_CLASS,
    adjudicate_finished_risk_envelope_numeric_offline_reproof_v1,
    reject_class_collapse_v1 as reject_envelope_collapse_v1,
    reject_identity_or_composition_upgrade_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_remaining_unranked_offline_reproof_bundle_v1 import (
    COVER_USDC_ADJUDICATED,
    FORENSIC_SOURCE_COUNT,
    FX_REOPENED,
    FX_STATUS,
    LiveCanaryZ2arRemainingUnrankedOfflineReproofBundleError,
    OWNER_GO,
    adjudicate_remaining_unranked_offline_reproof_bundle_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_rounding_offline_reproof_v1 import (
    ADJUDICATION as ROUNDING_ADJUDICATION,
    CENSUS_ENTRIES as ROUNDING_CENSUS,
    EPISTEMIC_CLASSES_PRESENT as ROUNDING_EPISTEMIC,
    FORENSIC_SOURCE_COUNT as ROUNDING_SOURCE_COUNT,
    LiveCanaryZ2arRoundingOfflineReproofError,
    Z2AR_CLASS as ROUNDING_CLASS,
    adjudicate_rounding_offline_reproof_v1,
    reject_class_collapse_v1 as reject_rounding_collapse_v1,
    reject_ticksz_as_usdc_precision_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.z2ar_usd_usdc_account_settlement_offline_reproof_v1 import (
    ADJUDICATION as SETTLEMENT_ADJUDICATION,
    CENSUS_ENTRIES as SETTLEMENT_CENSUS,
    EPISTEMIC_CLASSES_PRESENT as SETTLEMENT_EPISTEMIC,
    FORENSIC_SOURCE_COUNT as SETTLEMENT_SOURCE_COUNT,
    LiveCanaryZ2arUsdUsdcAccountSettlementOfflineReproofError,
    Z2AR_CLASS as SETTLEMENT_CLASS,
    adjudicate_usd_usdc_account_settlement_offline_reproof_v1,
    reject_class_collapse_v1 as reject_settlement_collapse_v1,
    reject_idxpx_one_normalization_v1,
    reject_semantic_proposition_upgrade_v1,
    reject_usd_equals_usdc_normalization_v1,
)


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_Z2CX_CONTRACT_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def test_bundle_constants_are_fail_closed() -> None:
    assert OWNER_GO == "PEAK_TRADE_OWNER_GO_Z2AR_REMAINING_UNRANKED_OFFLINE_REPROOF_BUNDLE_V1"
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert FX_STATUS == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert FX_REOPENED is False
    assert COVER_USDC_ADJUDICATED is False
    assert ROUNDING_CLASS == "ROUNDING"
    assert ENVELOPE_CLASS == "FINISHED_RISK_ENVELOPE_NUMERIC"
    assert SETTLEMENT_CLASS == "USD_USDC_ACCOUNT_SETTLEMENT"
    assert ROUNDING_ADJUDICATION == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert ENVELOPE_ADJUDICATION == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert SETTLEMENT_ADJUDICATION == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert ROUNDING_SOURCE_COUNT == len(ROUNDING_CENSUS)
    assert ENVELOPE_SOURCE_COUNT == len(ENVELOPE_CENSUS)
    assert SETTLEMENT_SOURCE_COUNT == len(SETTLEMENT_CENSUS)
    assert ROUNDING_SOURCE_COUNT >= 18
    assert ENVELOPE_SOURCE_COUNT >= 18
    assert SETTLEMENT_SOURCE_COUNT >= 18
    assert FORENSIC_SOURCE_COUNT == (
        ROUNDING_SOURCE_COUNT + ENVELOPE_SOURCE_COUNT + SETTLEMENT_SOURCE_COUNT
    )


def test_each_census_separates_epistemic_classes() -> None:
    for rows, present in (
        (ROUNDING_CENSUS, ROUNDING_EPISTEMIC),
        (ENVELOPE_CENSUS, ENVELOPE_EPISTEMIC),
        (SETTLEMENT_CENSUS, SETTLEMENT_EPISTEMIC),
    ):
        classes = {str(row["epistemic_class"]) for row in rows}
        assert classes == set(present)
        for row in rows:
            claim = str(row["claim"]).upper()
            if row["epistemic_class"] in {
                "NAVIGATION_INDEX_ONLY",
                "HISTORICAL_INTERMEDIATE_STATE",
            }:
                assert "REPROVEN" not in claim


def test_default_bundle_adjudication_is_three_fail_closed_classes() -> None:
    result = adjudicate_remaining_unranked_offline_reproof_bundle_v1()
    assert result["ROUNDING_STATUS"] == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert result["FINISHED_RISK_ENVELOPE_NUMERIC_STATUS"] == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert result["USD_USDC_ACCOUNT_SETTLEMENT_STATUS"] == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert result["FX_STATUS"] == "NOT_REPROVEN_MISSING_EVIDENCE"
    assert result["FX_REOPENED"] is False
    assert result["COVER_USDC_ADJUDICATED"] is False
    assert result["GET_PERFORMED"] is False
    assert result["EXECUTION_READY"] is False
    assert result["CONTRADICTION_COUNT"] == 0
    assert result["ROUNDING"]["Z2AR_CLASS"] == "ROUNDING"
    assert result["FINISHED_RISK_ENVELOPE_NUMERIC"]["Z2AR_CLASS"] == (
        "FINISHED_RISK_ENVELOPE_NUMERIC"
    )
    assert result["USD_USDC_ACCOUNT_SETTLEMENT"]["Z2AR_CLASS"] == "USD_USDC_ACCOUNT_SETTLEMENT"


def test_forbid_class_mixing_and_fx_reopen_and_cover() -> None:
    with pytest.raises(LiveCanaryZ2arRemainingUnrankedOfflineReproofBundleError) as exc:
        adjudicate_remaining_unranked_offline_reproof_bundle_v1(mix_classes=True)
    assert str(exc.value) == "FORBIDDEN_CLASS_MIXING"
    with pytest.raises(LiveCanaryZ2arRemainingUnrankedOfflineReproofBundleError) as exc:
        adjudicate_remaining_unranked_offline_reproof_bundle_v1(reopen_fx=True)
    assert str(exc.value) == "FORBIDDEN_FX_REOPEN"
    with pytest.raises(LiveCanaryZ2arRemainingUnrankedOfflineReproofBundleError) as exc:
        adjudicate_remaining_unranked_offline_reproof_bundle_v1(adjudicate_cover_usdc=True)
    assert str(exc.value) == "FORBIDDEN_COVER_USDC_ADJUDICATION"


def test_rounding_forbids_ticksz_and_collapse() -> None:
    with pytest.raises(LiveCanaryZ2arRoundingOfflineReproofError) as exc:
        reject_ticksz_as_usdc_precision_v1(treat_tick_sz_as_usdc_precision=True)
    assert str(exc.value) == "FORBIDDEN_TICKSZ_AS_USDC_PRECISION"
    with pytest.raises(LiveCanaryZ2arRoundingOfflineReproofError) as exc:
        reject_rounding_collapse_v1(mix_with_fx=True)
    assert str(exc.value) == "FORBIDDEN_COLLAPSE_ROUNDING_WITH_FX"
    with pytest.raises(LiveCanaryZ2arRoundingOfflineReproofError) as exc:
        adjudicate_rounding_offline_reproof_v1(claimed_status="REPROVEN")
    assert str(exc.value) == "FORBIDDEN_REPROVEN_MISSING_REQUIRED_INPUTS"


def test_envelope_forbids_identity_and_composition_upgrade() -> None:
    with pytest.raises(LiveCanaryZ2arFinishedRiskEnvelopeNumericOfflineReproofError) as exc:
        reject_identity_or_composition_upgrade_v1(treat_identity_as_finished=True)
    assert str(exc.value) == "FORBIDDEN_UPGRADE_IDENTITY_TO_FINISHED_RISK_ENVELOPE_NUMERIC"
    with pytest.raises(LiveCanaryZ2arFinishedRiskEnvelopeNumericOfflineReproofError) as exc:
        reject_identity_or_composition_upgrade_v1(treat_composition_as_finished=True)
    assert str(exc.value) == "FORBIDDEN_UPGRADE_COMPOSITION_TO_FINISHED_RISK_ENVELOPE_NUMERIC"
    with pytest.raises(LiveCanaryZ2arFinishedRiskEnvelopeNumericOfflineReproofError) as exc:
        reject_envelope_collapse_v1(mix_with_rounding=True)
    assert str(exc.value) == "FORBIDDEN_COLLAPSE_FINISHED_ENVELOPE_WITH_ROUNDING"


def test_settlement_forbids_idxpx_parity_and_semantic_upgrade() -> None:
    with pytest.raises(LiveCanaryZ2arUsdUsdcAccountSettlementOfflineReproofError) as exc:
        reject_idxpx_one_normalization_v1(treat_idxpx_one_as_settlement_proven=True)
    assert str(exc.value) == "FORBIDDEN_IDXPX_1_NORMALIZED_TO_ACCOUNT_SETTLEMENT_PROVEN"
    with pytest.raises(LiveCanaryZ2arUsdUsdcAccountSettlementOfflineReproofError) as exc:
        reject_usd_equals_usdc_normalization_v1(treat_usd_equals_usdc_as_operator=True)
    assert str(exc.value) == "FORBIDDEN_USD_EQUALS_USDC_NORMALIZED_TO_OPERATOR"
    with pytest.raises(LiveCanaryZ2arUsdUsdcAccountSettlementOfflineReproofError) as exc:
        reject_semantic_proposition_upgrade_v1(
            treat_z2j_semantic_proposition_as_account_settlement=True
        )
    assert str(exc.value) == "FORBIDDEN_UPGRADE_SEMANTIC_PROPOSITION_TO_ACCOUNT_SETTLEMENT"
    with pytest.raises(LiveCanaryZ2arUsdUsdcAccountSettlementOfflineReproofError) as exc:
        reject_settlement_collapse_v1(mix_with_fx=True)
    assert str(exc.value) == "FORBIDDEN_COLLAPSE_ACCOUNT_SETTLEMENT_WITH_FX"


def test_owner_go_is_not_flatten_execute() -> None:
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token="I_AUTHORIZE_SECTION_11_13_5_FLATTEN_EXECUTE",
        purpose="SECTION_11_13_5_FLATTEN_EXECUTE",
        owner_go=OWNER_GO,
    )
    assert accepted is False
    assert "FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN" in reasons
