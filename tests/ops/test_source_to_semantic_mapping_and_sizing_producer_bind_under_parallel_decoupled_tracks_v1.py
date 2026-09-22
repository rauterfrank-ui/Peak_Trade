"""Source→semantic mapping ratification under parallel-decoupled tracks."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    MAPPING_PROVEN,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    RISK_EQUITY_DIMENSION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    GOVERNED_PRODUCER_CREATED,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    RECONCILIATION_CONTRACT_CREATED,
    SOURCE_SELECTED,
    SOURCE_SELECTED_OBJECT,
    SOURCE_TO_SEMANTIC_MAPPING_RATIFIED_UNDER_PARALLEL_DECOUPLED_TRACKS_V1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_SURFACE,
    CurrentProductive29PRiskCapitalModelError,
    CurrentProductiveUsdcFreeMarginObservationV1,
    produce_current_productive_29p_risk_capital_v1,
    reject_direct_avail_eq_29p_claim_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_producer_v1 import (
    CurrentProductiveAccountEligibilityFactV1,
    CurrentProductiveP01ReductionFactV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_CREATED,
    build_running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.source_to_semantic_mapping_and_sizing_producer_bind_under_parallel_decoupled_tracks_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    NETWORK_ACCESS_PERFORMED,
    NUMERIC_CURRENT_VENUE_VALUE_BOUND,
    OWNER_GO,
    SOURCE_OBJECT,
    TRANSFORM,
    execute_source_to_semantic_mapping_and_sizing_producer_bind_v1,
    prove_static_producer_to_step29p_trace_v1,
    reject_reconstruction_as_sizing_source_v1,
    run_offline_step29p_e2e_proof_v1,
    SourceToSemanticMappingBindError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC = (
    REPO_ROOT
    / "docs/ops/specs"
    / "FULL_CORE_SOURCE_TO_SEMANTIC_MAPPING_AND_SIZING_PRODUCER_BIND_UNDER_PARALLEL_DECOUPLED_TRACKS_V1.md"
)
MOT = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"

EPOCH = "2026-09-22T06:25:00Z"
DIGEST = "c" * 64
FRESH_GET_BLOCKER = (
    "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
)


def _obs() -> CurrentProductiveUsdcFreeMarginObservationV1:
    return CurrentProductiveUsdcFreeMarginObservationV1(
        fact_id="CURRENT_PRODUCTIVE_USDC_FREE_MARGIN_OBSERVATION",
        surface=OBSERVATION_SURFACE,
        value="250.00",
        settlement_currency="USDC",
        selected_ccy="USDC",
        bound_account_identity="acct-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=EPOCH,
        observed_at_as_of=EPOCH,
        age_seconds="1",
        freshness_max_age="5",
        provenance_digest=DIGEST,
        already_net_of_in_use="true",
        account_level_avail_eq_used="false",
        fallback_chain_used="false",
    )


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
        account_mode="FUTURES_MODE",
        bound_account_identity="acct-1",
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=EPOCH,
        provenance_digest=DIGEST,
    )


def test_ratified_mapping_pins_and_dag() -> None:
    assert SOURCE_TO_SEMANTIC_MAPPING_RATIFIED_UNDER_PARALLEL_DECOUPLED_TRACKS_V1 is True
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is True
    assert MAPPING_PROVEN is True
    assert MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING is True
    assert SOURCE_SELECTED is True
    assert SOURCE_SELECTED_OBJECT == SOURCE_OBJECT
    assert TRANSFORM == CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == "UNRESOLVED"
    assert GOVERNED_PRODUCER_CREATED is False
    assert RECONCILIATION_CONTRACT_CREATED is False
    assert PARALLEL_DECOUPLED_TRACKS_AUTHORITY_INTERFACE_RECONCILIATION_CONTRACT_CREATED is True
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == FRESH_GET_BLOCKER
    assert NUMERIC_CURRENT_VENUE_VALUE_BOUND is False
    assert NETWORK_ACCESS_PERFORMED is False


def test_parallel_track_separation_still_builds() -> None:
    contract = build_running_account_equity_parallel_decoupled_tracks_authority_interface_reconciliation_contract_v1(
        contract_id="POST_MAPPING_RATIFICATION_FIXTURE",
    )
    assert contract.canonically_valid_account_equity_source_mapping is True
    assert contract.account_equity_authority_owner == "UNRESOLVED"
    assert contract.option_d_reconstruction_reconciliation_contract_created is False


def test_offline_e2e_and_negative_guards() -> None:
    trace = prove_static_producer_to_step29p_trace_v1()
    assert trace["target_semantic"] == RISK_EQUITY_DIMENSION
    assert trace["source_object"] == SOURCE_OBJECT
    e2e = run_offline_step29p_e2e_proof_v1(
        observation=_obs(),
        p01=_p01(),
        eligibility=_eligibility(),
    )
    assert e2e.typed_equity_raw == "250.00"
    assert e2e.typed_source_field == SOURCE_OBJECT
    with pytest.raises(CurrentProductive29PRiskCapitalModelError, match="DIRECT_AVAILEQ"):
        reject_direct_avail_eq_29p_claim_v1(claimed="details.availEq")
    with pytest.raises(SourceToSemanticMappingBindError, match="RECONSTRUCTION"):
        reject_reconstruction_as_sizing_source_v1(claimed="RECONSTRUCTION")
    blocked = produce_current_productive_29p_risk_capital_v1(
        observation=_obs(),
        p01=_p01(applicability_state="APPLIES", value="1.00"),
        eligibility=_eligibility(),
    )
    assert blocked.produced == "false"
    assert "P01_APPLIES_WITHOUT_CANONICAL_DIRECTIVE_SOURCE" in blocked.reason_codes


def test_execute_persists_offline_proof(tmp_path: Path) -> None:
    result = execute_source_to_semantic_mapping_and_sizing_producer_bind_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
    )
    assert result["OFFLINE_STEP29P_E2E_PROVEN"] == "true"
    assert (tmp_path / "pack" / "claims.json").is_file()
    with pytest.raises(SourceToSemanticMappingBindError, match="OWNER_GO_MISMATCH"):
        execute_source_to_semantic_mapping_and_sizing_producer_bind_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "bad",
        )


def test_runbook_spec_and_mot_navigation() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC.read_text(encoding="utf-8")
    mot = MOT.read_text(encoding="utf-8")
    assert OWNER_GO in runbook
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=true" in runbook
    assert "ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED" in runbook
    assert FRESH_GET_BLOCKER in runbook
    assert (
        "DOCS_TOKEN_FULL_CORE_SOURCE_TO_SEMANTIC_MAPPING_AND_SIZING_PRODUCER_BIND_"
        "UNDER_PARALLEL_DECOUPLED_TRACKS_V1"
    ) in spec
    assert (
        "FULL_CORE_SOURCE_TO_SEMANTIC_MAPPING_AND_SIZING_PRODUCER_BIND_"
        "UNDER_PARALLEL_DECOUPLED_TRACKS_V1.md"
    ) in mot
