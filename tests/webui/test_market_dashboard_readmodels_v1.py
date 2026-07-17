"""Focused contract tests for market_dashboard_readmodels_v1 (PR-B)."""

from __future__ import annotations

import math
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.webui.market_dashboard_readmodels_v1 import (
    AuthorityClassificationV1,
    CanonicalDecisionStatusV1,
    DashboardAvailabilityStateV1,
    DashboardFreshnessStateV1,
    DashboardSourceKindV1,
    DecisionDirectionV1,
    EconomicGateStatusV1,
    EligibilityStatusV1,
    MarketDashboardReadModelContractError,
    MarketRankingItemV1,
    OperatingModeV1,
    PACKAGE_ID,
    SideAssessmentV1,
    SourceFreshnessEntryV1,
    TriStateV1,
    dumps_json,
    loads_page_snapshot_json,
    new_canonical_decision_summary_v1,
    new_dashboard_freshness_snapshot_v1,
    new_dashboard_snapshot_provenance_v1,
    new_diagnostics_summary_snapshot_v1,
    new_double_play_decision_snapshot_v1,
    new_economic_summary_snapshot_v1,
    new_execution_state_snapshot_v1,
    new_market_dashboard_page_snapshot_v1,
    new_market_instrument_snapshot_v1,
    new_market_ranking_snapshot_v1,
    new_safety_authority_snapshot_v1,
    new_unavailable_snapshot_v1,
    page_snapshot_to_json_dict,
    to_json_dict,
)
from src.webui.market_dashboard_readmodels_v1.contracts import OhlcvBarV1

DIGEST_A = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
DIGEST_B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
TS = datetime(2026, 7, 17, 8, 0, tzinfo=timezone.utc)
TS2 = datetime(2026, 7, 17, 8, 5, tzinfo=timezone.utc)
PACKAGE_DIR = (
    Path(__file__).resolve().parents[2] / "src" / "webui" / "market_dashboard_readmodels_v1"
)


def _prov(**overrides):
    base = dict(
        producer_module="tests.fixture.producer",
        generated_at=TS2,
        effective_at=TS,
        source_kind=DashboardSourceKindV1.EVIDENCE_BUNDLE,
        freshness_state=DashboardFreshnessStateV1.FRESH,
        producer_version="test-1",
        source_reference="evidence/test/bundle",
        evidence_digest=DIGEST_A,
    )
    base.update(overrides)
    return new_dashboard_snapshot_provenance_v1(**base)


def _unavailable(**overrides):
    base = dict(
        availability_state=DashboardAvailabilityStateV1.NOT_BOUND,
        reason_code="PRODUCER_NOT_BOUND",
        detail="Producer binding is deferred to PR-C.",
        expected_source="canonical.producer.module",
        generated_at=TS2,
    )
    base.update(overrides)
    return new_unavailable_snapshot_v1(**base)


def _market(**overrides):
    base = dict(
        instrument_id="ETHUSDT",
        venue="binance_futures",
        effective_at=TS,
        freshness_state=DashboardFreshnessStateV1.FRESH,
        provenance=_prov(),
        mark_price=2500.5,
        last_price=2501.0,
        change_abs=10.0,
        change_pct=0.4,
        volume=1000.0,
        ohlcv=OhlcvBarV1(open=2490.0, high=2510.0, low=2480.0, close=2501.0, volume=900.0),
    )
    base.update(overrides)
    return new_market_instrument_snapshot_v1(**base)


def _ranking(**overrides):
    items = (
        MarketRankingItemV1(
            instrument_id="SOLUSDT",
            rank=2,
            score=0.7,
            eligibility_status=EligibilityStatusV1.ELIGIBLE,
            reason_codes=("B", "A"),
        ),
        MarketRankingItemV1(
            instrument_id="ETHUSDT",
            rank=1,
            score=0.9,
            eligibility_status=EligibilityStatusV1.ELIGIBLE,
            reason_codes=("Z",),
        ),
    )
    base = dict(
        ranked_items=items,
        selected_instrument_id="ETHUSDT",
        effective_at=TS,
        provenance=_prov(),
    )
    base.update(overrides)
    return new_market_ranking_snapshot_v1(**base)


def _decision(**overrides):
    base = dict(
        decision_status=CanonicalDecisionStatusV1.UNKNOWN,
        direction=DecisionDirectionV1.NOT_PROVIDED,
        confidence=None,
        evidence_status="NOT_BOUND",
        reason_codes=("R2", "R1"),
        blockers=("BLK_B", "BLK_A"),
        evidence_digest=DIGEST_B,
        evidence_reference=None,
        effective_at=TS,
        provenance=_prov(),
    )
    base.update(overrides)
    return new_canonical_decision_summary_v1(**base)


def _double_play(**overrides):
    base = dict(
        bull_assessment=SideAssessmentV1(status="UNKNOWN", score=None, reason_codes=("B1",)),
        bear_assessment=SideAssessmentV1(status="UNKNOWN", score=None, reason_codes=("A1",)),
        composition_result="NOT_BOUND",
        arbitration_status="NOT_BOUND",
        blockers=("DP_B", "DP_A"),
        evidence_digest=DIGEST_A,
        evidence_reference=None,
        effective_at=TS,
        provenance=_prov(),
    )
    base.update(overrides)
    return new_double_play_decision_snapshot_v1(**base)


def _safety(**overrides):
    base = dict(
        authority_classification=AuthorityClassificationV1.UNKNOWN,
        kill_switch_state=TriStateV1.UNKNOWN,
        risk_gate_state=TriStateV1.NOT_PROVIDED,
        execution_permission_state=TriStateV1.UNKNOWN,
        fail_closed_reason_codes=("FC_B", "FC_A"),
        effective_at=TS,
        provenance=_prov(),
    )
    base.update(overrides)
    return new_safety_authority_snapshot_v1(**base)


def _execution(**overrides):
    base = dict(
        operating_mode=OperatingModeV1.UNKNOWN,
        intent_state="NOT_PROVIDED",
        fill_state="NOT_PROVIDED",
        reconciliation_state="NOT_PROVIDED",
        unknown_outcome_state="UNKNOWN",
        effective_at=TS,
        provenance=_prov(),
    )
    base.update(overrides)
    return new_execution_state_snapshot_v1(**base)


def _economic(**overrides):
    base = dict(
        economic_gate_status=EconomicGateStatusV1.UNKNOWN,
        sample_size=None,
        evidence_digest=DIGEST_A,
        evidence_reference=None,
        effective_at=TS,
        provenance=_prov(),
        gross_return=None,
        net_return=None,
        profit_factor=None,
        drawdown=None,
        cost_drag=None,
        expectancy=None,
        authoritative_gate=True,
    )
    base.update(overrides)
    return new_economic_summary_snapshot_v1(**base)


def _diagnostics(**overrides):
    base = dict(
        diagnostic_statuses=("WARN_B", "WARN_A"),
        bundle_digest=DIGEST_B,
        bundle_reference=None,
        effective_at=TS,
        provenance=_prov(),
    )
    base.update(overrides)
    return new_diagnostics_summary_snapshot_v1(**base)


def _freshness(**overrides):
    entries = (
        SourceFreshnessEntryV1(
            source_key="ranking",
            freshness_state=DashboardFreshnessStateV1.MISSING,
            source_age_seconds=None,
            missing=True,
            stale=False,
        ),
        SourceFreshnessEntryV1(
            source_key="market",
            freshness_state=DashboardFreshnessStateV1.FRESH,
            source_age_seconds=12.5,
            missing=False,
            stale=False,
        ),
    )
    base = dict(
        page_generated_at=TS2,
        source_entries=entries,
        provenance=_prov(source_kind=DashboardSourceKindV1.COMPOSITION_RUNTIME),
    )
    base.update(overrides)
    return new_dashboard_freshness_snapshot_v1(**base)


def _page(**overrides):
    base = dict(
        generated_at=TS2,
        market=_market(),
        ranking=_unavailable(expected_source="ranking.producer"),
        decision=_decision(),
        double_play=_unavailable(
            availability_state=DashboardAvailabilityStateV1.MISSING_SOURCE,
            reason_code="DP_EVIDENCE_MISSING",
            expected_source="composition_matrix_v1",
        ),
        safety_authority=_safety(),
        execution=_execution(),
        economic=_economic(),
        diagnostics=_diagnostics(),
        freshness=_freshness(),
    )
    base.update(overrides)
    return new_market_dashboard_page_snapshot_v1(**base)


def test_package_id() -> None:
    assert PACKAGE_ID == "market_dashboard_readmodels.v1"
    assert PACKAGE_DIR.is_dir()
    doc = (
        Path(__file__).resolve().parents[2] / "docs" / "webui" / "MARKET_DASHBOARD_READMODELS_V1.md"
    )
    assert doc.is_file()


@pytest.mark.parametrize(
    "factory",
    [
        _prov,
        _unavailable,
        _market,
        _ranking,
        _decision,
        _double_play,
        _safety,
        _execution,
        _economic,
        _diagnostics,
        _freshness,
        _page,
    ],
)
def test_immutability(factory) -> None:
    obj = factory()
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        obj.schema_id = "mutated"  # type: ignore[misc]


def test_valid_construction_all_available_snapshots() -> None:
    assert _market().instrument_id == "ETHUSDT"
    assert _ranking().ranked_items[0].instrument_id == "ETHUSDT"
    assert _decision().decision_status is CanonicalDecisionStatusV1.UNKNOWN
    assert _double_play().composition_result == "NOT_BOUND"
    assert _safety().authority_classification is AuthorityClassificationV1.UNKNOWN
    assert _execution().operating_mode is OperatingModeV1.UNKNOWN
    assert _economic().profit_factor is None
    assert _diagnostics().non_authoritative is True
    assert _freshness().source_entries[0].source_key == "market"


def test_valid_explicit_unavailable_construction() -> None:
    snap = _unavailable(availability_state=DashboardAvailabilityStateV1.MALFORMED_SOURCE)
    assert snap.availability_state is DashboardAvailabilityStateV1.MALFORMED_SOURCE
    with pytest.raises(MarketDashboardReadModelContractError, match="AVAILABLE"):
        _unavailable(availability_state=DashboardAvailabilityStateV1.AVAILABLE)


def test_reject_naive_timestamps() -> None:
    naive = datetime(2026, 7, 17, 8, 0)
    with pytest.raises(MarketDashboardReadModelContractError, match="timezone-aware"):
        _prov(generated_at=naive, effective_at=naive)


def test_reject_invalid_schema_version_and_empty_producer() -> None:
    from src.webui.market_dashboard_readmodels_v1.provenance import (
        DashboardSnapshotProvenanceV1,
    )

    with pytest.raises(MarketDashboardReadModelContractError):
        _prov(producer_module="")
    with pytest.raises(MarketDashboardReadModelContractError, match=">= 1"):
        DashboardSnapshotProvenanceV1(
            schema_id="peak_trade.market_dashboard.snapshot_provenance.v1",
            schema_version=0,
            producer_module="tests.fixture.producer",
            generated_at=TS2,
            effective_at=TS,
            source_kind=DashboardSourceKindV1.UNKNOWN,
            freshness_state=DashboardFreshnessStateV1.UNKNOWN,
            producer_version="1",
            source_reference="ref",
        )


def test_reject_malformed_digest() -> None:
    with pytest.raises(MarketDashboardReadModelContractError, match="sha256"):
        _prov(evidence_digest="not-a-digest")


def test_reject_nan_and_infinity() -> None:
    with pytest.raises(MarketDashboardReadModelContractError, match="finite"):
        _market(mark_price=math.nan)
    with pytest.raises(MarketDashboardReadModelContractError, match="finite"):
        _market(last_price=math.inf)
    with pytest.raises(MarketDashboardReadModelContractError, match="finite"):
        _economic(profit_factor=math.nan)


def test_reject_negative_age_and_counts() -> None:
    with pytest.raises(MarketDashboardReadModelContractError, match=">="):
        SourceFreshnessEntryV1(
            source_key="market",
            freshness_state=DashboardFreshnessStateV1.STALE,
            source_age_seconds=-1.0,
            missing=False,
            stale=True,
        )
    with pytest.raises(MarketDashboardReadModelContractError, match=">="):
        _economic(sample_size=-1, evidence_reference="path")


def test_deterministic_serialization_and_reason_blocker_ordering() -> None:
    decision = _decision()
    assert decision.reason_codes == ("R1", "R2")
    assert decision.blockers == ("BLK_A", "BLK_B")
    ranking = _ranking()
    assert [item.instrument_id for item in ranking.ranked_items] == ["ETHUSDT", "SOLUSDT"]
    assert ranking.ranked_items[0].reason_codes == ("Z",)
    assert ranking.ranked_items[1].reason_codes == ("A", "B")
    payload = to_json_dict(decision)
    assert list(payload.keys())[0] == "schema_id"
    assert dumps_json(decision) == dumps_json(decision)


def test_available_vs_unavailable_union_and_aggregate_mixed() -> None:
    page = _page()
    assert isinstance(page.market, type(_market()))
    assert page.ranking.availability_state is DashboardAvailabilityStateV1.NOT_BOUND
    assert page.double_play.availability_state is DashboardAvailabilityStateV1.MISSING_SOURCE
    assert page.decision.decision_status is CanonicalDecisionStatusV1.UNKNOWN


def test_economic_missing_metrics_remain_unavailable_not_zero() -> None:
    economic = _economic()
    payload = to_json_dict(economic)
    for key in (
        "gross_return",
        "net_return",
        "profit_factor",
        "drawdown",
        "cost_drag",
        "expectancy",
        "sample_size",
    ):
        assert payload[key] is None
        assert payload[key] != 0.0


def test_unknown_authority_not_converted_to_blocked_or_safe() -> None:
    safety = _safety()
    assert safety.authority_classification is AuthorityClassificationV1.UNKNOWN
    assert safety.kill_switch_state is TriStateV1.UNKNOWN
    assert safety.execution_permission_state is TriStateV1.UNKNOWN
    assert safety.authority_classification not in {
        AuthorityClassificationV1.AUTHORIZED,
        AuthorityClassificationV1.NOT_AUTHORIZED,
    }


def test_unknown_decision_state_not_inferred() -> None:
    decision = _decision()
    assert decision.decision_status is CanonicalDecisionStatusV1.UNKNOWN
    assert decision.direction is DecisionDirectionV1.NOT_PROVIDED
    assert decision.confidence is None


def test_diagnostics_explicitly_non_authoritative() -> None:
    diag = _diagnostics()
    assert diag.non_authoritative is True
    assert diag.diagnostic_only is True
    with pytest.raises(MarketDashboardReadModelContractError, match="non_authoritative"):
        _diagnostics(non_authoritative=False)


def test_duplicate_ranked_instrument_and_rank_handling() -> None:
    with pytest.raises(MarketDashboardReadModelContractError, match="unique instrument"):
        _ranking(
            ranked_items=(
                MarketRankingItemV1(
                    instrument_id="ETHUSDT",
                    rank=1,
                    score=1.0,
                    eligibility_status=EligibilityStatusV1.ELIGIBLE,
                ),
                MarketRankingItemV1(
                    instrument_id="ETHUSDT",
                    rank=2,
                    score=0.5,
                    eligibility_status=EligibilityStatusV1.ELIGIBLE,
                ),
            )
        )
    with pytest.raises(MarketDashboardReadModelContractError, match="duplicate ranks"):
        _ranking(
            ranked_items=(
                MarketRankingItemV1(
                    instrument_id="ETHUSDT",
                    rank=1,
                    score=1.0,
                    eligibility_status=EligibilityStatusV1.ELIGIBLE,
                ),
                MarketRankingItemV1(
                    instrument_id="SOLUSDT",
                    rank=1,
                    score=0.5,
                    eligibility_status=EligibilityStatusV1.ELIGIBLE,
                ),
            )
        )
    allowed = _ranking(
        allow_duplicate_ranks=True,
        ranked_items=(
            MarketRankingItemV1(
                instrument_id="ETHUSDT",
                rank=1,
                score=1.0,
                eligibility_status=EligibilityStatusV1.ELIGIBLE,
            ),
            MarketRankingItemV1(
                instrument_id="SOLUSDT",
                rank=1,
                score=0.5,
                eligibility_status=EligibilityStatusV1.ELIGIBLE,
            ),
        ),
    )
    assert len(allowed.ranked_items) == 2


def test_no_production_fixture_helper_fabricating_complete_dashboard_truth() -> None:
    """Package must not ship a production helper that fabricates full dashboard truth."""

    py_files = list(PACKAGE_DIR.glob("*.py"))
    forbidden_tokens = (
        "fabricate_complete_dashboard",
        "build_static_dashboard_display_dict",
        "dummy_market_dashboard_truth",
        "complete_dashboard_fixture_factory",
    )
    for path in py_files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{path.name} contains forbidden fixture helper {token}"


def test_serialization_round_trip_page_aggregate() -> None:
    page = _page()
    encoded = dumps_json(page)
    restored = loads_page_snapshot_json(encoded)
    assert page_snapshot_to_json_dict(restored) == page_snapshot_to_json_dict(page)
    assert restored.market.instrument_id == "ETHUSDT"
    assert restored.ranking.availability_state is DashboardAvailabilityStateV1.NOT_BOUND
    assert restored.economic.profit_factor is None


def test_market_requires_price_or_ohlcv_else_unavailable() -> None:
    with pytest.raises(MarketDashboardReadModelContractError, match="UnavailableSnapshotV1"):
        _market(mark_price=None, last_price=None, ohlcv=None)
