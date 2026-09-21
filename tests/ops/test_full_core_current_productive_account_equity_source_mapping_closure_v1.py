"""Account-equity source mapping closure v1. Offline. No POST. No wire."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    IMPLEMENTATION_OF_VALUE_BINDING,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    POST_ALLOWED,
    RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION,
    RUNNING_EQUITY_SOURCE_OBJECT,
    RUNNING_EQUITY_SOURCE_SEMANTICS,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    RISK_EQUITY_DIMENSION,
    Step29PCapitalRiskAdmissibilityClaimV1,
    evaluate_step_29p_capital_risk_admissibility_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE,
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED,
    CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_SURFACE,
    PRODUCER_IDENTITY,
    CurrentProductiveUsdcFreeMarginObservationV1,
    bind_step_29p_typed_equity_from_risk_capital_v1,
    produce_current_productive_29p_risk_capital_v1,
    reject_direct_avail_eq_29p_claim_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_account_equity_source_mapping_closure_v1 import (
    CANONICAL_PACK_RELPATH,
    EARLIEST_AFTER_CLOSURE,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveAccountEquitySourceMappingClosureError,
    build_canonical_equity_source_lineage_v1,
    evaluate_canonical_mapping_acceptance_v1,
    execute_current_productive_account_equity_source_mapping_closure_v1,
    reject_historical_fixture_as_equity_authority_v1,
    reject_treasury_observation_alone_as_increase_authority_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.constants_v1 import (
    AVAILABLE_FOR_SIZING_MINT_AUTHORIZED,
    RISK_ADMISSIBLE_MINT_AUTHORIZED,
    STEP_29P_MINT_AUTHORIZED,
)
from tests.ops.test_full_core_step_29p_risk_admissibility_pre_construction_v1 import (
    _capital,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
)


def test_closure_constants_and_dag() -> None:
    assert CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_CLOSED is True
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is True
    assert MAPPING_PROVEN is True
    assert IMPLEMENTATION_OF_VALUE_BINDING is True
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == EARLIEST_AFTER_CLOSURE
    assert RUNNING_EQUITY_SOURCE_OBJECT == PRODUCER_IDENTITY
    assert CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE == PRODUCER_IDENTITY
    assert OBSERVATION_SURFACE == CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
        CONTINUOUS_RUN_AUTHORIZED as ORCH_CONTINUOUS,
    )

    assert ORCH_CONTINUOUS is False


def test_lineage_and_treasury_fixture_guards() -> None:
    lineage = build_canonical_equity_source_lineage_v1()
    assert lineage.source_surface == CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE
    assert lineage.transformation == CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA
    assert lineage.producer_identity == PRODUCER_IDENTITY
    reject_treasury_observation_alone_as_increase_authority_v1(
        treasury_risk_admissible_mint=False,
        step_29p_mint=False,
        available_for_sizing_mint=False,
    )
    with pytest.raises(CurrentProductiveAccountEquitySourceMappingClosureError):
        reject_treasury_observation_alone_as_increase_authority_v1(
            treasury_risk_admissible_mint=True,
            step_29p_mint=False,
            available_for_sizing_mint=False,
        )
    with pytest.raises(Exception):
        reject_historical_fixture_as_equity_authority_v1(source_field="FIXTURE")
    with pytest.raises(Exception):
        reject_direct_avail_eq_29p_claim_v1(claimed="availEq")
    assert RISK_ADMISSIBLE_MINT_AUTHORIZED is False
    assert STEP_29P_MINT_AUTHORIZED is False
    assert AVAILABLE_FOR_SIZING_MINT_AUTHORIZED is False


def test_canonical_acceptance_and_29p_consumer(tmp_path: Path) -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_account_equity_source_mapping_closure_v1 import (
        _sample_eligibility_and_p01_v1,
        _sample_valid_observation_v1,
    )

    obs = _sample_valid_observation_v1()
    eligibility, p01 = _sample_eligibility_and_p01_v1()
    ok, reasons = evaluate_canonical_mapping_acceptance_v1(
        observation=obs, p01=p01, eligibility=eligibility
    )
    assert ok is True
    assert not reasons
    output = produce_current_productive_29p_risk_capital_v1(
        observation=obs, p01=p01, eligibility=eligibility, restart_from_kind_set="false"
    )
    claim = bind_step_29p_typed_equity_from_risk_capital_v1(
        output=output,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        expected_instrument_id="SUI-USD_UM_XPERP-310404",
        observed_instrument_id="SUI-USD_UM_XPERP-310404",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )
    assert claim.typed_account_equity_source_field == PRODUCER_IDENTITY
    assert claim.equity_dimension == RISK_EQUITY_DIMENSION
    capital = _capital()
    result = evaluate_step_29p_capital_risk_admissibility_v1(capital=capital, claim=claim)
    assert result.equity_dimension_bound is True
    assert "CAPITAL_ADMISSION_OPTIMISTIC_FIELD_FALLBACK" not in result.reason_codes


def test_missing_stale_and_mismatch_denied() -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_account_equity_source_mapping_closure_v1 import (
        _sample_eligibility_and_p01_v1,
        _sample_valid_observation_v1,
    )

    obs = _sample_valid_observation_v1()
    eligibility, p01 = _sample_eligibility_and_p01_v1()
    bad_obs = CurrentProductiveUsdcFreeMarginObservationV1(
        **{**obs.__dict__, "surface": "totalEq", "account_level_avail_eq_used": "true"}
    )
    ok, reasons = evaluate_canonical_mapping_acceptance_v1(
        observation=bad_obs, p01=p01, eligibility=eligibility
    )
    assert ok is False
    assert reasons
    missing = Step29PCapitalRiskAdmissibilityClaimV1(
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        expected_instrument_id="SUI-USD_UM_XPERP-310404",
        observed_instrument_id="SUI-USD_UM_XPERP-310404",
        equity_dimension="",
        typed_account_equity_raw="",
        typed_account_equity_source_field="",
        fresh_evidence_fetched=False,
        fresh_evidence_validated=False,
    )
    denied = evaluate_step_29p_capital_risk_admissibility_v1(capital=_capital(), claim=missing)
    assert denied.risk_admissible is False


def test_execute_closure_evidence(tmp_path: Path) -> None:
    result = execute_current_productive_account_equity_source_mapping_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
    )
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "true"
    assert claims["MAPPING_PROVEN"] == "true"
    assert claims["POST_COUNT"] == "0"
    assert claims["EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert claims["MV2_DP_CHANGED"] == "false"
    assert result.manifest_verify_rc == 0


def test_protected_surfaces_unchanged() -> None:
    for rel in PROTECTED_ALGORITHM_FILES:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "OPTIMIZATION_PRODUCTIVE_AUTHORITY" not in text or "NONE" in text
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True


def test_spec_and_atlas_factual() -> None:
    assert SPEC_PATH.is_file()
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE_V1" in spec
    )
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=true" in spec
    assert "ATLAS_AUTHORITY=NONE" in spec
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert "11.2.1.EZ" in atlas
    assert "ACCOUNT_EQUITY_SOURCE_MAPPING_CLOSURE" in atlas or "MAPPING_CLOSURE" in atlas
