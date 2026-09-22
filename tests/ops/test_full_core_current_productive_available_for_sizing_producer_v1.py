"""Current-productive AVAILABLE_FOR_SIZING producer tests.

The producer is the 29P source object. Venue eq remains reconciliation-target.
Forbidden venue fields are not algebra inputs. U04 remains reduction after BASE.
P01 is a conditional reduction. Legacy KIND_SET remains sealed. No GET. No POST.
No mint while BASE is unbound.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FRESHNESS_POLICY,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    RISK_EQUITY_DIMENSION,
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_NOT_EQUITY_STOCK,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_29P_BINDING_STATUS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_ALGEBRA,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_CREATED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IS_SOURCE_OBJECT,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED,
    CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
    CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE,
    CURRENT_PRODUCTIVE_SOURCE_SELECTED,
    CURRENT_PRODUCTIVE_U04_CURRENT_APPLICATION,
    EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE,
    GOVERNED_PRODUCER_CREATED,
    KIND_SET_RESOLVED,
    KIND_SET_UPLIFT_THIS_WORKPACKAGE,
    LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
    PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
    PRODUCTIVE_U04_EQUITY_STOCK_ROLE,
    RAW_EQ_SOURCE_AUTHORITY,
    SEALED_LEGACY_CENSUS_REOPENED,
    SOURCE_SELECTED,
    U04_LEGACY_STATUS,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_account_equity_source_architecture_v1 import (
    FORBIDDEN_AUTHORITY_FIELDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXACT_MISSING_PREDICATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    FRESH_GET_NOT_REQUIRED_JUSTIFIED,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    OUTPUT_UNIT,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    PIN_OWNER_GO_STATUS,
    PRODUCER_IDENTITY,
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveAvailableForSizingBaseFactV1,
    CurrentProductiveAvailableForSizingProducerError,
    CurrentProductiveEqReconciliationTargetV1,
    CurrentProductiveP01ReductionFactV1,
    CurrentProductiveU04ReservationFactV1,
    bind_step_29p_typed_equity_from_producer_v1,
    classify_producer_algebra_v1,
    classify_producer_input_facts_v1,
    execute_current_productive_available_for_sizing_producer_v1,
    produce_current_productive_available_for_sizing_v1,
    reject_eq_copied_into_sizing_value_v1,
    reject_kind_set_restart_restore_v1,
    restart_current_productive_available_for_sizing_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_source_selection_v1 import (
    NEXT_OWNER_GO as CS_NEXT_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_available_for_sizing_producer_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CT_HEADING = "11.2.1.CT FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER"
CS_HEADING = "11.2.1.CS FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION"
EPOCH = "pretrade-decision-1"
FORBIDDEN_SOURCE_TOKENS = (
    "urllib",
    "requests",
    "httpx",
    "GET_ENDPOINTS_PRIVATE",
    "max_retries",
    "eq=cashBal",
)


class _Capital:
    evidence_status = "MISSING"
    capital_authority_class = "OBSERVED_NOT_RISK_ADMISSIBLE"
    risk_admissible = False


def _execute(tmp_path: Path) -> object:
    return execute_current_productive_available_for_sizing_producer_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        repo_root=REPO_ROOT,
    )


def _base(**overrides: str) -> CurrentProductiveAvailableForSizingBaseFactV1:
    payload = {
        "fact_id": CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID,
        "value": "100.50",
        "settlement_currency": "USDC",
        "bound_account_identity": "acct-1",
        "bound_venue_identity": "okx",
        "bound_td_mode": "cross",
        "decision_epoch": EPOCH,
        "observed_at_as_of": EPOCH,
        "age_seconds": "1",
        "freshness_max_age": "5",
        "provenance_digest": "a" * 64,
        "source_class": "CURRENT_PRODUCTIVE_TYPED_BASE_OBSERVATION",
        "already_net_of_u04": "false",
    }
    payload.update(overrides)
    return CurrentProductiveAvailableForSizingBaseFactV1(**payload)


def _u04(**overrides: str) -> CurrentProductiveU04ReservationFactV1:
    payload = {
        "fact_id": "CURRENT_PRODUCTIVE_U04_PENDING_ORDER_RESERVATION",
        "value": "10",
        "settlement_currency": "USDC",
        "bound_account_identity": "acct-1",
        "bound_venue_identity": "okx",
        "bound_td_mode": "cross",
        "decision_epoch": EPOCH,
        "observed_at_as_of": EPOCH,
        "age_seconds": "1",
        "freshness_max_age": "5",
        "provenance_digest": "b" * 64,
        "source_class": "CURRENT_PRODUCTIVE_PENDING_ORDER_RESERVATION",
        "empty_reservation_proven": "false",
    }
    payload.update(overrides)
    return CurrentProductiveU04ReservationFactV1(**payload)


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
        "provenance_digest": "c" * 64,
        "source_class": "CURRENT_PRODUCTIVE_P01_DIRECTIVE",
    }
    payload.update(overrides)
    return CurrentProductiveP01ReductionFactV1(**payload)


def _eligibility(**overrides: str) -> CurrentProductiveAccountEligibilityFactV1:
    payload = {
        "fact_id": "CURRENT_PRODUCTIVE_U01_ACCOUNT_ELIGIBILITY",
        "account_mode": "FUTURES_MODE",
        "bound_account_identity": "acct-1",
        "bound_venue_identity": "okx",
        "bound_td_mode": "cross",
        "decision_epoch": EPOCH,
        "provenance_digest": "d" * 64,
    }
    payload.update(overrides)
    return CurrentProductiveAccountEligibilityFactV1(**payload)


def test_standing_pins_remain_fail_closed() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is False
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is True
    assert MAPPING_PROVEN is True
    assert KIND_SET_RESOLVED is False
    assert KIND_SET_UPLIFT_THIS_WORKPACKAGE is False
    assert SOURCE_SELECTED is True
    assert GOVERNED_PRODUCER_CREATED is False
    assert CURRENT_PRODUCTIVE_SOURCE_SELECTED is True
    assert CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED is False
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_CREATED is True
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IS_SOURCE_OBJECT is True
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_MINT_AUTHORIZED is False
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS == "UNBOUND"
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS == (
        "BOUND_TYPED_OFFLINE_PRODUCER_WRAP"
    )
    assert CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE == (
        "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1"
    )
    assert CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED is False
    assert CURRENT_PRODUCTIVE_U04_CURRENT_APPLICATION == "SUBTRACT_AFTER_BASE_ONCE_NOT_SOURCE"
    assert CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_29P_BINDING_STATUS == (
        "CONSUMER_BOUND_TO_PRODUCER_TYPED_SEMANTIC_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )
    assert U04_LEGACY_STATUS == "UNRESOLVED"
    assert PRODUCTIVE_U04_EQUITY_STOCK_ROLE == DISPOSITION_NOT_EQUITY_STOCK
    assert PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )
    assert LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE is False
    assert SEALED_LEGACY_CENSUS_REOPENED is False
    assert PIN_OWNER_GO == CS_NEXT_OWNER_GO


def test_wrong_owner_go_and_origin_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveAvailableForSizingProducerError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_available_for_sizing_producer_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )
    with pytest.raises(
        CurrentProductiveAvailableForSizingProducerError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_current_productive_available_for_sizing_producer_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_algebra_subtracts_u04_and_conditional_p01() -> None:
    output = produce_current_productive_available_for_sizing_v1(
        base=_base(),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert output.produced == "true"
    assert output.value == "90.50"
    assert output.settlement_currency == "USDC"
    assert output.output_unit == OUTPUT_UNIT
    assert output.u04_applied == "true"
    assert output.p01_applied == "false"
    assert output.step_29p_risk_admissible == "false"
    with_p01 = produce_current_productive_available_for_sizing_v1(
        base=_base(),
        u04=_u04(),
        p01=_p01(applicability_state="APPLIES", value="5.25"),
        eligibility=_eligibility(),
    )
    assert with_p01.produced == "true"
    assert with_p01.value == "85.25"
    assert with_p01.p01_applied == "true"


def test_missing_stale_forbidden_and_double_count_fail_closed() -> None:
    missing = produce_current_productive_available_for_sizing_v1(
        base=None,
        u04=None,
        p01=None,
        eligibility=None,
    )
    assert missing.produced == "false"
    assert missing.value == ""
    assert "BASE_FACT_MISSING" in missing.reason_codes
    stale = produce_current_productive_available_for_sizing_v1(
        base=_base(age_seconds="6"),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert stale.produced == "false"
    assert "BASE_STALE" in stale.reason_codes
    forbidden = produce_current_productive_available_for_sizing_v1(
        base=_base(source_class="availEq"),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert forbidden.produced == "false"
    assert "BASE_FORBIDDEN_OR_UNCLASSIFIED_SOURCE_CLASS" in forbidden.reason_codes
    net = produce_current_productive_available_for_sizing_v1(
        base=_base(already_net_of_u04="true"),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert net.produced == "false"
    assert "BASE_MUST_NOT_BE_NET_OF_U04" in net.reason_codes
    p01_u04 = produce_current_productive_available_for_sizing_v1(
        base=_base(),
        u04=_u04(),
        p01=_p01(source_class="U04_PENDING_ORDER_RESERVATION"),
        eligibility=_eligibility(),
    )
    assert p01_u04.produced == "false"
    assert "P01_MUST_NOT_ENCODE_U04" in p01_u04.reason_codes
    unknown_p01 = produce_current_productive_available_for_sizing_v1(
        base=_base(),
        u04=_u04(),
        p01=_p01(applicability_state="UNKNOWN_FAIL_CLOSED"),
        eligibility=_eligibility(),
    )
    assert unknown_p01.produced == "false"
    assert "P01_APPLICABILITY_UNKNOWN_FAIL_CLOSED" in unknown_p01.reason_codes
    retired_open = produce_current_productive_available_for_sizing_v1(
        base=_base(),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(account_mode="OPEN"),
    )
    assert retired_open.produced == "false"
    assert "ACCOUNT_MODE_INELIGIBLE" in retired_open.reason_codes
    contracts = produce_current_productive_available_for_sizing_v1(
        base=_base(settlement_currency="USD"),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert contracts.produced == "false"
    assert "BASE_CURRENCY_NOT_USDC" in contracts.reason_codes
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        blocked = produce_current_productive_available_for_sizing_v1(
            base=_base(source_class=field),
            u04=_u04(),
            p01=_p01(),
            eligibility=_eligibility(),
        )
        assert blocked.produced == "false"


def test_eq_reconciliation_blocks_divergence_without_becoming_source() -> None:
    ok = produce_current_productive_available_for_sizing_v1(
        base=_base(),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(),
        eq_target=CurrentProductiveEqReconciliationTargetV1(
            fact_id="CURRENT_PRODUCTIVE_EQ_RECONCILIATION_TARGET",
            value="100.50",
            settlement_currency="USDC",
            bound_account_identity="acct-1",
            bound_venue_identity="okx",
            bound_td_mode="cross",
            decision_epoch=EPOCH,
            observed_at_as_of=EPOCH,
            provenance_digest="e" * 64,
            compare_requested="true",
        ),
    )
    assert ok.produced == "true"
    assert ok.reconciliation_status == "COMPARED_NO_BLOCKING_DIVERGENCE_EQ_NOT_SOURCE"
    blocked = produce_current_productive_available_for_sizing_v1(
        base=_base(),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(),
        eq_target=CurrentProductiveEqReconciliationTargetV1(
            fact_id="CURRENT_PRODUCTIVE_EQ_RECONCILIATION_TARGET",
            value="80",
            settlement_currency="USDC",
            bound_account_identity="acct-1",
            bound_venue_identity="okx",
            bound_td_mode="cross",
            decision_epoch=EPOCH,
            observed_at_as_of=EPOCH,
            provenance_digest="e" * 64,
            compare_requested="true",
        ),
    )
    assert blocked.produced == "false"
    assert "EQ_RECONCILIATION_DIVERGENCE_BLOCK" in blocked.reason_codes
    assert blocked.reconciliation_status == "DIVERGENCE_BLOCK_EQ_NOT_SOURCE"
    reject_eq_copied_into_sizing_value_v1(claimed="false")
    with pytest.raises(
        CurrentProductiveAvailableForSizingProducerError,
        match="EQ_MUST_NOT_BE_COPIED_INTO_AVAILABLE_FOR_SIZING",
    ):
        reject_eq_copied_into_sizing_value_v1(claimed="COPY_EQ")


def test_restart_recomputes_and_rejects_kind_set_restore() -> None:
    with pytest.raises(
        CurrentProductiveAvailableForSizingProducerError,
        match="KIND_SET_RESTORE_FORBIDDEN_FOR_AVAILABLE_FOR_SIZING_RESTART",
    ):
        reject_kind_set_restart_restore_v1(claimed="KIND_SET")
    recomputed = restart_current_productive_available_for_sizing_v1(
        restore_from_kind_set="false",
        base=_base(),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert recomputed.produced == "true"
    assert recomputed.value == "90.50"


def test_step_29p_binding_uses_producer_identity_not_venue_field() -> None:
    output = produce_current_productive_available_for_sizing_v1(
        base=_base(),
        u04=_u04(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    claim = bind_step_29p_typed_equity_from_producer_v1(
        output=output,
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        expected_instrument_id="SUI-USD_UM_XPERP",
        observed_instrument_id="SUI-USD_UM_XPERP",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )
    assert claim.equity_dimension == RISK_EQUITY_DIMENSION
    assert claim.typed_account_equity_raw == "90.50"
    assert claim.typed_account_equity_source_field == PRODUCER_IDENTITY
    assert claim.typed_account_equity_source_field not in FORBIDDEN_AUTHORITY_FIELDS
    admissibility = evaluate_step_29p_capital_risk_admissibility_v1(
        capital=_Capital(),
        claim=claim,
    )
    assert admissibility.risk_admissible is False
    unbound = produce_current_productive_available_for_sizing_v1(
        base=None,
        u04=None,
        p01=None,
        eligibility=None,
    )
    unbound_claim = bind_step_29p_typed_equity_from_producer_v1(
        output=unbound,
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        expected_instrument_id="SUI-USD_UM_XPERP",
        observed_instrument_id="SUI-USD_UM_XPERP",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )
    assert unbound_claim.typed_account_equity_raw == ""
    assert unbound_claim.typed_account_equity_source_field == ""


def test_execute_defines_producer_without_mint_or_get(tmp_path: Path) -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.source_to_semantic_mapping_and_sizing_producer_bind_under_parallel_decoupled_tracks_v1 import (
        SourceToSemanticMappingBindError,
    )

    with pytest.raises(
        SourceToSemanticMappingBindError,
        match="CONSUME_BASELINE_SUPERSEDED_BY_MAPPING_RATIFICATION_V1",
    ):
        _execute(tmp_path)


def test_source_does_not_get_or_post_or_uplift() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source
    assert "KIND_SET_RESOLVED = True" not in source
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING = True" not in source
    assert "RAW_EQ_SOURCE_AUTHORITY = True" not in source
    assert "SOURCE_SELECTED = True" not in source
    assert "LIVE_ENABLED = True" not in source
    assert classify_producer_algebra_v1()["freshness_policy"] == FRESHNESS_POLICY
    fact_ids = {item["fact_id"] for item in classify_producer_input_facts_v1()}
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_FACT_ID in fact_ids


def test_canonical_pack_sealed() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["AVAILABLE_FOR_SIZING_PRODUCER_CREATED"] == "true"
    assert claims["AVAILABLE_FOR_SIZING_BASE_STATUS"] == "UNBOUND"
    assert claims["SELECTED_SOURCE_OBJECT"] == PRODUCER_IDENTITY
    assert claims["VENUE_SELECTED_SOURCE"] == "NONE"
    assert claims["RECONCILIATION_TARGET_STATUS"] == "EQ_RECONCILIATION_TARGET_ONLY"
    assert claims["U04_APPLICATION"] == "SUBTRACT_AFTER_BASE_ONCE_NOT_SOURCE"
    assert claims["LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE"] == "false"
    assert claims["SEALED_LEGACY_CENSUS_REOPENED"] == "false"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["FRESH_GET_EXECUTED"] == "false"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["FIRST_DEFINITIVE_BLOCK"] == BLOCKER_ID
    assert claims["EXACT_MISSING_PREDICATE"] == EXACT_MISSING_PREDICATE
    assert claims["PIN_OWNER_GO"] == PIN_OWNER_GO
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_ct_persists_producer_without_mint() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ct_section = spec
    assert OWNER_GO in ct_section
    assert PIN_OWNER_GO in ct_section
    assert "AVAILABLE_FOR_SIZING_PRODUCER_CREATED=true" in ct_section
    assert "AVAILABLE_FOR_SIZING_BASE_STATUS=UNBOUND" in ct_section
    assert (
        "SELECTED_SOURCE_OBJECT=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1" in ct_section
    )
    assert "VENUE_SELECTED_SOURCE=NONE" in ct_section
    assert "FRESH_GET_EXECUTED=false" in ct_section
    assert "LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE=false" in ct_section
    assert "SEALED_LEGACY_CENSUS_REOPENED=false" in ct_section
    assert "RECONCILIATION_TARGET_STATUS=EQ_RECONCILIATION_TARGET_ONLY" in ct_section
    assert "U04_APPLICATION=SUBTRACT_AFTER_BASE_ONCE_NOT_SOURCE" in ct_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in ct_section
    assert "AUTHORITY_UPLIFT=false" in ct_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in ct_section
    assert "NO_HOPE_GET=true" in ct_section
    assert "ACTUAL_GET_COUNT=0" in ct_section
    assert BLOCKER_ID in ct_section
    assert (
        "OWNER_GO_RATIFY_SOURCE_TO_SEMANTIC_MAPPING_AND_BIND_AVAILABLE_FOR_SIZING_"
        "PRODUCER_UNDER_PARALLEL_DECOUPLED_TRACKS_V1"
    ) in runbook
    assert ("DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1") in spec
    assert "current_productive_available_for_sizing_producer_v1.py" in atlas
