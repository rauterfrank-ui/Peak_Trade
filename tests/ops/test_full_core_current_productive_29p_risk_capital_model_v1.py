"""CURRENT_PRODUCTIVE 29P risk-capital model tests.

OPTION_B: BASE is retired. 29P consumes USDC free margin from
details[ccy=USDC].availEq minus conditional P01. U04 is not subtracted.
eq remains reconciliation-target. Fallback chain stays forbidden. No GET.
No POST. No mint without observation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_AVAIL_EQ_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_BASE_ABSTRACTION,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_EQ_VERDICT,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_CREATED,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SELECTED_OPTION,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_ALGEBRA,
    EQ_RECONCILIATION_TARGET_ONLY,
    GOVERNED_PRODUCER_CREATED,
    SEALED_LEGACY_CENSUS_REOPENED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO,
    OBSERVATION_SURFACE,
    OWNER_GO,
    CurrentProductive29PRiskCapitalModelError,
    CurrentProductiveUsdcFreeMarginObservationV1,
    bind_step_29p_typed_equity_from_risk_capital_v1,
    classify_current_venue_field_adjudication_v1,
    classify_existing_base_abstraction_verdict_v1,
    execute_current_productive_29p_risk_capital_model_v1,
    produce_current_productive_29p_risk_capital_v1,
    reject_direct_avail_eq_29p_claim_v1,
    restart_current_productive_29p_risk_capital_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveEqReconciliationTargetV1,
    CurrentProductiveP01ReductionFactV1,
    CurrentProductiveU04ReservationFactV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
RUNBOOK_PATH = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_V1.md"
PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
EPOCH = "2026-09-15T12:03:00Z"
DIGEST = "a" * 64
CT_HEADING = "11.2.1.CT FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER"
CU_HEADING = "11.2.1.CU FULL_CORE_CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL"


class _Capital:
    evidence_status = "MISSING"
    capital_authority_class = "OBSERVED_NOT_RISK_ADMISSIBLE"
    risk_admissible = False


def _obs(**overrides: str) -> CurrentProductiveUsdcFreeMarginObservationV1:
    payload = {
        "fact_id": "CURRENT_PRODUCTIVE_USDC_FREE_MARGIN_OBSERVATION",
        "surface": OBSERVATION_SURFACE,
        "value": "100.00",
        "settlement_currency": "USDC",
        "selected_ccy": "USDC",
        "bound_account_identity": "acct-1",
        "bound_venue_identity": "okx",
        "bound_td_mode": "cross",
        "decision_epoch": EPOCH,
        "observed_at_as_of": EPOCH,
        "age_seconds": "1",
        "freshness_max_age": "5",
        "provenance_digest": DIGEST,
        "already_net_of_in_use": "true",
        "account_level_avail_eq_used": "false",
        "fallback_chain_used": "false",
    }
    payload.update(overrides)
    return CurrentProductiveUsdcFreeMarginObservationV1(**payload)


def _p01(**overrides: str) -> CurrentProductiveP01ReductionFactV1:
    payload = {
        "fact_id": "CURRENT_PRODUCTIVE_P01_GOVERNED_REDUCTION",
        "applicability_state": "DOES_NOT_APPLY",
        "value": "",
        "settlement_currency": "USDC",
        "bound_account_identity": "acct-1",
        "bound_venue_identity": "okx",
        "bound_td_mode": "cross",
        "decision_epoch": EPOCH,
        "observed_at_as_of": EPOCH,
        "age_seconds": "1",
        "freshness_max_age": "5",
        "provenance_digest": DIGEST,
        "source_class": "GOVERNED_CONDITIONAL",
    }
    payload.update(overrides)
    return CurrentProductiveP01ReductionFactV1(**payload)


def _eligibility() -> CurrentProductiveAccountEligibilityFactV1:
    return CurrentProductiveAccountEligibilityFactV1(
        fact_id="CURRENT_PRODUCTIVE_U01_ACCOUNT_ELIGIBILITY",
        account_mode="OPEN",
        bound_account_identity="acct-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=EPOCH,
        provenance_digest=DIGEST,
    )


def _u04() -> CurrentProductiveU04ReservationFactV1:
    return CurrentProductiveU04ReservationFactV1(
        fact_id="CURRENT_PRODUCTIVE_U04_PENDING_ORDER_RESERVATION",
        value="10",
        settlement_currency="USDC",
        bound_account_identity="acct-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=EPOCH,
        observed_at_as_of=EPOCH,
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest=DIGEST,
        source_class="RESERVATION",
        empty_reservation_proven="false",
    )


def test_standing_pins_and_option_b() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert EQ_RECONCILIATION_TARGET_ONLY is True
    assert SEALED_LEGACY_CENSUS_REOPENED is False
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS == "UNBOUND"
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_ALGEBRA == (
        "BASE_MINUS_U04_MINUS_CONDITIONAL_P01_USDC_V1"
    )
    assert CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_CREATED is True
    assert CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SELECTED_OPTION == "OPTION_B"
    assert CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_BASE_ABSTRACTION == (
        "RETIRED_UNNECESSARY_INTERMEDIATE"
    )
    assert CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA == (
        "DETAILS_USDC_AVAILEQ_MINUS_CONDITIONAL_P01_USDC_V1"
    )
    assert CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE == ("details[ccy=USDC].availEq")
    assert CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_AVAIL_EQ_VERDICT == (
        "CURRENT_PRODUCTIVE_RECLASSIFICATION_JUSTIFIED"
    )
    assert CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_EQ_VERDICT == ("KEEP_RECONCILIATION_TARGET_ONLY")
    assert CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION == (
        "DO_NOT_SUBTRACT_ALREADY_NETTED_IN_VENUE_FREE_MARGIN"
    )


def test_field_adjudication_verdicts() -> None:
    rows = {item["field"]: item for item in classify_current_venue_field_adjudication_v1()}
    assert rows["details[ccy=USDC].availEq"]["verdict"] == (
        "CURRENT_PRODUCTIVE_RECLASSIFICATION_JUSTIFIED"
    )
    assert rows["account.availEq"]["verdict"] == "KEEP_FORBIDDEN"
    assert rows["eq"]["verdict"] == "KEEP_RECONCILIATION_TARGET_ONLY"
    assert rows["totalEq"]["verdict"] == "KEEP_FORBIDDEN"
    assert rows["adjEq"]["verdict"] == "KEEP_FORBIDDEN"
    assert rows["availBal"]["verdict"] == "KEEP_FORBIDDEN"
    assert rows["cashBal"]["verdict"] == "KEEP_FORBIDDEN"
    assert "DO_NOT_SUBTRACT" in rows["ordFrozen"]["verdict"]
    verdict = classify_existing_base_abstraction_verdict_v1()
    assert verdict["verdict"] == "RETIRED_UNNECESSARY_INTERMEDIATE"
    assert verdict["selected_option"] == "OPTION_B"


def test_produce_free_margin_minus_conditional_p01() -> None:
    output = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert output.produced == "true"
    assert output.value == "100.00"
    assert output.u04_applied == "false"
    assert output.p01_applied == "false"
    reduced = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(),
        p01=_p01(applicability_state="APPLIES", value="12.50"),
        eligibility=_eligibility(),
    )
    assert reduced.produced == "true"
    assert reduced.value == "87.50"
    assert reduced.p01_applied == "true"
    assert reduced.u04_applied == "false"


def test_u04_and_forbidden_surfaces_fail_closed() -> None:
    with_u04 = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(),
        p01=_p01(),
        eligibility=_eligibility(),
        u04=_u04(),
    )
    assert with_u04.produced == "false"
    assert "U04_MUST_NOT_BE_SUBTRACTED_AFTER_AVAILEQ" in with_u04.reason_codes
    account = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(surface="availEq", account_level_avail_eq_used="true"),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert account.produced == "false"
    fallback = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(fallback_chain_used="true"),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert fallback.produced == "false"
    unknown = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(),
        p01=_p01(applicability_state="UNKNOWN_FAIL_CLOSED"),
        eligibility=_eligibility(),
    )
    assert unknown.produced == "false"
    missing = produce_current_productive_29p_risk_capital_v1(
        observation=None,
        p01=None,
        eligibility=None,
    )
    assert missing.produced == "false"
    assert missing.value == ""


def test_eq_reconciliation_blocks_without_becoming_source() -> None:
    compared = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(),
        p01=_p01(),
        eligibility=_eligibility(),
        eq_target=CurrentProductiveEqReconciliationTargetV1(
            fact_id="CURRENT_PRODUCTIVE_EQ_RECONCILIATION_TARGET",
            value="120.00",
            settlement_currency="USDC",
            bound_account_identity="acct-1",
            bound_venue_identity="okx",
            bound_td_mode="cross",
            decision_epoch=EPOCH,
            observed_at_as_of=EPOCH,
            provenance_digest=DIGEST,
            compare_requested="true",
        ),
    )
    assert compared.produced == "true"
    assert compared.reconciliation_status == "COMPARED_NO_DIVERGENCE"
    blocked = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(value="150.00"),
        p01=_p01(),
        eligibility=_eligibility(),
        eq_target=CurrentProductiveEqReconciliationTargetV1(
            fact_id="CURRENT_PRODUCTIVE_EQ_RECONCILIATION_TARGET",
            value="120.00",
            settlement_currency="USDC",
            bound_account_identity="acct-1",
            bound_venue_identity="okx",
            bound_td_mode="cross",
            decision_epoch=EPOCH,
            observed_at_as_of=EPOCH,
            provenance_digest=DIGEST,
            compare_requested="true",
        ),
    )
    assert blocked.produced == "false"
    assert "EQ_RECONCILIATION_DIVERGENCE" in blocked.reason_codes


def test_restart_recomputes_and_rejects_kind_set_restore() -> None:
    first = restart_current_productive_29p_risk_capital_v1(
        observation=_obs(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    second = restart_current_productive_29p_risk_capital_v1(
        observation=_obs(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert first.value == second.value
    with pytest.raises(CurrentProductive29PRiskCapitalModelError, match="KIND_SET_RESTORE"):
        restart_current_productive_29p_risk_capital_v1(
            observation=_obs(),
            p01=_p01(),
            eligibility=_eligibility(),
            restore_from_kind_set="KIND_SET",
        )


def test_step_29p_uses_producer_identity_not_venue_field() -> None:
    output = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.MISSING.value,
        live_account_bound_status=LiveAccountBoundStatusV1.MISSING.value,
        expected_instrument_id="SUI-USDC-SWAP",
        observed_instrument_id="SUI-USDC-SWAP",
        fresh_evidence_fetched=False,
        fresh_evidence_validated=False,
    )
    assert claim.typed_account_equity_source_field == (
        "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1"
    )
    assert "availEq" not in claim.typed_account_equity_source_field
    result = evaluate_step_29p_capital_risk_admissibility_v1(capital=_Capital(), claim=claim)
    assert result.risk_admissible is False
    with pytest.raises(CurrentProductive29PRiskCapitalModelError, match="DIRECT_AVAILEQ"):
        reject_direct_avail_eq_29p_claim_v1(claimed="availEq")


def test_execute_defines_model_without_mint_or_get(tmp_path: Path) -> None:
    result = execute_current_productive_29p_risk_capital_model_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
    )
    assert result.selected_option == "OPTION_B"
    assert result.fresh_get_executed == "false"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert result.current_live_critical_blocker == BLOCKER_ID
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0
    with pytest.raises(CurrentProductive29PRiskCapitalModelError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_29p_risk_capital_model_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "bad",
        )


def test_canonical_pack_and_ssot() -> None:
    claims = json.loads((PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["SELECTED_ARCHITECTURE_OPTION"] == "OPTION_B"
    assert claims["AVAIL_EQ_VERDICT"] == "CURRENT_PRODUCTIVE_RECLASSIFICATION_JUSTIFIED"
    assert claims["EQ_VERDICT"] == "KEEP_RECONCILIATION_TARGET_ONLY"
    assert claims["FRESH_GET_EXECUTED"] == "false"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "false"
    assert claims["SEALED_LEGACY_CENSUS_REOPENED"] == "false"
    assert verify_manifest_sha256_v1(store_root=PACK) == 0
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert CT_HEADING in runbook
    assert CU_HEADING in runbook
    assert "DETAILS_USDC_AVAILEQ_MINUS_CONDITIONAL_P01_USDC_V1" in runbook
    assert "FULL_CORE_CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_V1.md" in mot
    assert "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_MODEL_V1" in spec
    assert "11.2.1.CU" in atlas
    assert "current_productive_29p_risk_capital_model_v1.py" in atlas
    assert NEXT_OWNER_GO in runbook
