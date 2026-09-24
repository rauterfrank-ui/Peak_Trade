"""Tests for research stratification v2 (decoupled from bridge feature_regime)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    EVIDENCE_SCHEMA_VERSION,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.producer_v1 import (
    produce_productive_research_evidence_from_cycle_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.admission_v2 import (
    evaluate_v2_campaign_admission_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.backflow_check_v2 import (
    assert_no_trading_backflow_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.constants_v2 import (
    EVIDENCE_SCHEMA_VERSION_V2,
    RESEARCH_STRATIFICATION_CONTRACT_VERSION,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.coverage_v2 import (
    evaluate_coverage_readiness_v2_v1,
    is_classified_stratum_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.join_projection_v2 import (
    project_productive_evidence_to_research_join_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.mark_path_v2 import (
    ResearchObservationMarkPathStateV2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.models_v2 import (
    ResearchStratificationBindingV2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.parameter_authority_v2 import (
    ParameterAuthorityEntryV2,
    build_production_parameter_authority_surface_v2,
    parameter_authority_complete_v2,
    parameter_authority_digest_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.preregistration_binding_v2 import (
    build_research_stratification_preregistration_v2,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_v1 import (
    open_productive_evidence_session_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    attach_validation_v1,
    validate_productive_evidence_record_v1,
)

ROOT = Path(__file__).resolve().parents[2]
T0 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def _ratified_test_parameters_v2() -> tuple[ParameterAuthorityEntryV2, ...]:
    """TEST_ONLY — must not be imported by production modules."""
    cv = RESEARCH_STRATIFICATION_CONTRACT_VERSION
    base = {
        "contract_version": cv,
        "authority_status": "RATIFIED",
        "authority_source": "TEST_HARNESS_ONLY",
    }
    return (
        ParameterAuthorityEntryV2(
            name="research_mark_path_lookback_observations",
            value=8,
            unit="OBSERVATIONS",
            semantic_purpose="test",
            **base,
        ),
        ParameterAuthorityEntryV2(
            name="minimum_mark_path_observations",
            value=3,
            unit="OBSERVATIONS",
            semantic_purpose="test",
            **base,
        ),
        ParameterAuthorityEntryV2(
            name="market_state_realized_vol_low_threshold",
            value=0.00001,
            unit="DECIMAL_RETURN_STDEV",
            semantic_purpose="test",
            **base,
        ),
        ParameterAuthorityEntryV2(
            name="market_state_realized_vol_high_threshold",
            value=0.001,
            unit="DECIMAL_RETURN_STDEV",
            semantic_purpose="test",
            **base,
        ),
        ParameterAuthorityEntryV2(
            name="volatility_stratum_low_threshold",
            value=0.01,
            unit="DECIMAL_FRACTION",
            semantic_purpose="test",
            **base,
        ),
        ParameterAuthorityEntryV2(
            name="volatility_stratum_high_threshold",
            value=0.05,
            unit="DECIMAL_FRACTION",
            semantic_purpose="test",
            **base,
        ),
    )


def _cycle(**kwargs) -> dict:
    from tests.research.test_canonical_volatility_max_age_productive_research_evidence_accumulation_v1 import (
        _cycle as base_cycle,
    )

    return base_cycle(
        session_id=kwargs.get("session_id", "s1"), cycle_id=kwargs.get("cycle_id", "c1")
    )


def test_production_parameter_authority_unset_and_admission_false() -> None:
    surface = build_production_parameter_authority_surface_v2()
    assert parameter_authority_complete_v2(surface) is False
    admission = evaluate_v2_campaign_admission_v2(
        research_stratification_contract_version=RESEARCH_STRATIFICATION_CONTRACT_VERSION,
        research_stratification_parameter_digest=parameter_authority_digest_v2(surface),
        parameter_entries=surface,
        preregistration_v2_bound=True,
    )
    assert admission["research_stratification_v2_campaign_admission"] is False


def test_fail_closed_states_do_not_count_as_regimes() -> None:
    for label in ("INSUFFICIENT_DATA", "UNCLASSIFIED", "MISSING", "UNKNOWN"):
        assert is_classified_stratum_v2(label) is False


def test_v1_producer_path_unchanged_without_v2_binding() -> None:
    session = open_productive_evidence_session_v1(
        session_id="s-v1-only",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="abc123",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
    )
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s-v1-only", cycle_id="c1"),
        session=session,
        repository_sha="abc123",
    )
    record = attach_validation_v1(record)
    assert record.evidence_schema_version == EVIDENCE_SCHEMA_VERSION
    assert record.research_stratification_version is None


def test_v2_enrichment_fail_closed_when_production_authority_unset() -> None:
    session = open_productive_evidence_session_v1(
        session_id="s-v2-fc",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="abc123",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
    )
    prereg = build_research_stratification_preregistration_v2()
    binding = ResearchStratificationBindingV2(
        research_stratification_contract_version=RESEARCH_STRATIFICATION_CONTRACT_VERSION,
        research_stratification_parameter_digest=prereg.research_stratification_parameter_digest,
        campaign_id="camp-test",
    )
    mark_state = ResearchObservationMarkPathStateV2(campaign_id="camp-test", session_id="s-v2-fc")
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s-v2-fc", cycle_id="c1"),
        session=session,
        repository_sha="abc123",
        research_stratification_binding_v2=binding,
        research_mark_path_state_v2=mark_state,
    )
    assert record.evidence_schema_version == EVIDENCE_SCHEMA_VERSION_V2
    assert record.stratification_ok is False
    assert record.market_state_stratum_v2 == "UNKNOWN"
    assert record.regime_label  # legacy v1 path preserved


def test_coverage_v2_dimension_separated_with_test_harness_params() -> None:
    from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.compute_v2 import (
        compute_research_stratification_v2,
    )
    from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.research_stratification_v2.models_v2 import (
        CmcVolatilityInputProvenanceV2,
    )

    params = _ratified_test_parameters_v2()
    digest = parameter_authority_digest_v2(params)
    cmc_low = CmcVolatilityInputProvenanceV2(
        volatility_value=0.02,
        volatility_unit="DECIMAL_FRACTION",
        volatility_horizon_seconds=3600.0,
        volatility_estimator="TYPED",
        volatility_observation_count=60,
        volatility_source_digest="digest-low",
    )
    cmc_high = CmcVolatilityInputProvenanceV2(
        volatility_value=0.08,
        volatility_unit="DECIMAL_FRACTION",
        volatility_horizon_seconds=3600.0,
        volatility_estimator="TYPED",
        volatility_observation_count=60,
        volatility_source_digest="digest-high",
    )
    low_marks = [100.0, 100.0, 100.0, 100.0, 100.0]
    high_marks = [100.0, 102.0, 104.0, 106.0, 108.0, 110.0, 112.0, 114.0]
    s_low = compute_research_stratification_v2(
        cmc=cmc_low,
        mark_prices=low_marks,
        parameter_entries=params,
        expected_parameter_digest=digest,
    )
    s_high = compute_research_stratification_v2(
        cmc=cmc_high,
        mark_prices=high_marks,
        parameter_entries=params,
        expected_parameter_digest=digest,
    )
    assert s_low.stratification_ok is True
    assert s_high.stratification_ok is True
    assert s_low.market_state_stratum_v2 != s_high.market_state_stratum_v2

    session = open_productive_evidence_session_v1(
        session_id="s-cov",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="abc123",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
    )
    binding = ResearchStratificationBindingV2(
        research_stratification_contract_version=RESEARCH_STRATIFICATION_CONTRACT_VERSION,
        research_stratification_parameter_digest=digest,
        campaign_id="camp-cov",
        parameter_entries_override=params,
    )
    mark_state = ResearchObservationMarkPathStateV2(campaign_id="camp-cov", session_id="s-cov")
    records = []
    for i, marks in enumerate((low_marks, high_marks)):
        for j, _ in enumerate(marks):
            cycle = _cycle(session_id="s-cov", cycle_id=f"c{i}-{j}")
            cycle["feature_regime"]["mark_price"] = marks[j]
            cycle["canonical_volatility_typed_binding"]["volatility_value"] = (
                0.02 if i == 0 else 0.08
            )
            records.append(
                produce_productive_research_evidence_from_cycle_v1(
                    cycle,
                    session=session,
                    repository_sha="abc123",
                    research_stratification_binding_v2=binding,
                    research_mark_path_state_v2=mark_state,
                )
            )
    records = [attach_validation_v1(r) for r in records]
    cov = evaluate_coverage_readiness_v2_v1(
        records=records,
        expected_parameter_digest=digest,
    )
    assert cov["market_regime_count"] >= 2
    assert cov["volatility_regime_count"] >= 1


def test_mixed_v1_v2_scope_fail_closed() -> None:
    session = open_productive_evidence_session_v1(
        session_id="s-mix",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="abc123",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
    )
    v1 = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s-mix", cycle_id="v1"),
        session=session,
        repository_sha="abc123",
    )
    prereg = build_research_stratification_preregistration_v2()
    binding = ResearchStratificationBindingV2(
        research_stratification_contract_version=RESEARCH_STRATIFICATION_CONTRACT_VERSION,
        research_stratification_parameter_digest=prereg.research_stratification_parameter_digest,
        campaign_id="camp-mix",
    )
    mark_state = ResearchObservationMarkPathStateV2(campaign_id="camp-mix", session_id="s-mix")
    v2 = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s-mix", cycle_id="v2"),
        session=session,
        repository_sha="abc123",
        research_stratification_binding_v2=binding,
        research_mark_path_state_v2=mark_state,
    )
    cov = evaluate_coverage_readiness_v2_v1(records=[v1, v2])
    assert "MIXED_V1_V2_SCOPE_FORBIDDEN" in cov["coverage_gaps"]


def test_cross_session_mark_path_carry_and_cross_campaign_rejected() -> None:
    s1 = ResearchObservationMarkPathStateV2(campaign_id="camp-a", session_id="sess-1")
    s1.append_mark(100.0)
    s2 = ResearchObservationMarkPathStateV2.carry_within_campaign_v2(
        prior=s1, campaign_id="camp-a", next_session_id="sess-2"
    )
    assert s2.mark_prices == s1.mark_prices
    with pytest.raises(ValueError):
        ResearchObservationMarkPathStateV2.carry_within_campaign_v2(
            prior=s1, campaign_id="camp-b", next_session_id="sess-2"
        )


def test_join_v2_uses_stratification_key_not_legacy_regime_id() -> None:
    session = open_productive_evidence_session_v1(
        session_id="s-join",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="abc123",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
    )
    prereg = build_research_stratification_preregistration_v2()
    binding = ResearchStratificationBindingV2(
        research_stratification_contract_version=RESEARCH_STRATIFICATION_CONTRACT_VERSION,
        research_stratification_parameter_digest=prereg.research_stratification_parameter_digest,
        campaign_id="camp-join",
    )
    mark_state = ResearchObservationMarkPathStateV2(campaign_id="camp-join", session_id="s-join")
    record = attach_validation_v1(
        produce_productive_research_evidence_from_cycle_v1(
            _cycle(session_id="s-join", cycle_id="c1"),
            session=session,
            repository_sha="abc123",
            research_stratification_binding_v2=binding,
            research_mark_path_state_v2=mark_state,
        )
    )
    join, ext = project_productive_evidence_to_research_join_v2(record)
    assert ext["join_regime_id_v2"] == record.stratification_key_v2
    assert join.regime_id == record.regime_label


def test_backflow_check_none() -> None:
    result = assert_no_trading_backflow_v2()
    assert result["trading_decision"] == "NONE"


def test_bridge_module_not_modified() -> None:
    bridge = (
        ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/feature_regime_pipeline_v2.py"
    )
    text = bridge.read_text(encoding="utf-8")
    assert "REGIME_UNCLASSIFIED_FAIL_CLOSED" in text
