"""Contract tests for Market Dashboard Landscape V2 read-only projections."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.backtest.economic_viability_evidence_v1 import EconomicViabilityStatus
from src.webui.market_dashboard_landscape_v2 import (
    AVAILABILITY_VALUES,
    SCHEMA_VERSION,
    Availability,
    CanonicalDecisionSnapshotV1,
    EconomicSummarySnapshotV1,
    build_source_health_from_snapshots,
    default_not_bound_bundle,
    dumps_projection_canonical,
    owner_registry_by_slot,
    project_canonical_decision_snapshot_v1,
    project_double_play_snapshot_v1,
    serialize_projection,
)
from src.webui.market_dashboard_landscape_v2.provenance import (
    FreshnessV1,
    SnapshotProvenanceV1,
)
from src.webui.market_dashboard_landscape_v2.unavailable import (
    unavailable_canonical_decision,
    unavailable_economic_summary,
)

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 23, 14, 0, 0, tzinfo=timezone.utc)


def test_availability_vocabulary_exact() -> None:
    assert AVAILABILITY_VALUES == frozenset(
        {"AVAILABLE", "NOT_BOUND", "MISSING_SOURCE", "STALE", "INVALID"}
    )


def test_default_not_bound_bundle_covers_all_slots_without_silent_clock() -> None:
    with pytest.raises(ValueError, match="generated_at required"):
        default_not_bound_bundle()
    bundle = default_not_bound_bundle(generated_at=STAMP)
    assert "source_health" not in bundle
    for slot, snap in bundle.items():
        assert snap.availability is Availability.NOT_BOUND
        assert snap.schema_version == SCHEMA_VERSION
        assert snap.provenance.availability is Availability.NOT_BOUND
        assert snap.freshness.is_stale is False
        payload = serialize_projection(snap)
        assert payload["availability"] == "NOT_BOUND"
        assert payload["provenance"]["schema_id"]
        assert payload["freshness"]["observed_at"].endswith("Z")


def test_immutability_frozen_snapshots() -> None:
    snap = unavailable_canonical_decision(
        availability=Availability.NOT_BOUND,
        generated_at=STAMP,
        reason="TEST_NOT_BOUND",
    )
    with pytest.raises(FrozenInstanceError):
        snap.decision = "BUY"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        snap.provenance.availability = Availability.AVAILABLE  # type: ignore[misc]


def test_provenance_completeness_on_available_decision() -> None:
    snap = project_canonical_decision_snapshot_v1(
        instrument_id="PF_XBTUSD",
        decision="HOLD",
        direction="FLAT",
        reason_codes=("REASON_A",),
        blockers=(),
        decision_id="dec-1",
        evidence_schema_version="canonical_trading_decision_evidence_v1",
        evidence_digest="a" * 64,
        generated_at=STAMP,
        effective_at=STAMP,
        source_reference="evidence://dec-1",
        git_sha="deadbeef",
    )
    assert snap.availability is Availability.AVAILABLE
    prov = snap.provenance.to_json_dict()
    for key in (
        "schema_id",
        "schema_version",
        "producer_module",
        "generated_at",
        "source_kind",
        "availability",
    ):
        assert prov[key]
    assert prov["evidence_digest"] == "a" * 64
    assert prov["git_sha"] == "deadbeef"


def test_available_decision_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="required"):
        project_canonical_decision_snapshot_v1(
            instrument_id="",
            decision="HOLD",
            direction="FLAT",
            reason_codes=(),
            blockers=(),
            decision_id=None,
            evidence_schema_version="canonical_trading_decision_evidence_v1",
            evidence_digest=None,
            generated_at=STAMP,
            effective_at=None,
            source_reference=None,
        )


def test_stale_and_invalid_semantics() -> None:
    stale = unavailable_canonical_decision(
        availability=Availability.STALE,
        generated_at=STAMP,
        reason="EVIDENCE_STALE",
    )
    assert stale.availability is Availability.STALE
    assert stale.freshness.is_stale is True
    assert stale.freshness.stale_reason == "EVIDENCE_STALE"
    assert stale.decision is None

    invalid = unavailable_canonical_decision(
        availability=Availability.INVALID,
        generated_at=STAMP,
        reason="SCHEMA_MISMATCH",
    )
    assert invalid.availability is Availability.INVALID
    assert invalid.decision is None


def test_missing_source_and_not_bound_no_invented_decision() -> None:
    missing = unavailable_canonical_decision(
        availability=Availability.MISSING_SOURCE,
        generated_at=STAMP,
        reason="PRODUCER_OUTPUT_ABSENT",
    )
    assert missing.decision is None
    assert missing.direction is None
    assert "PRODUCER_OUTPUT_ABSENT" in missing.blockers


def test_source_health_aggregation_fail_closed_and_complete() -> None:
    bundle = default_not_bound_bundle(generated_at=STAMP)
    health = build_source_health_from_snapshots(bundle, generated_at=STAMP)
    assert health.availability is Availability.NOT_BOUND
    assert set(health.slot_availability) == set(bundle)
    assert set(health.incomplete_slots) == set(bundle)
    payload = health.to_json_dict()
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["slot_availability"]["canonical_decision"] == "NOT_BOUND"

    with pytest.raises(ValueError, match="required snapshot slot absent"):
        build_source_health_from_snapshots({}, generated_at=STAMP)


def test_source_health_prefers_invalid_over_available() -> None:
    from src.webui.market_dashboard_landscape_v2.unavailable import (
        unavailable_safety_authority,
    )

    bundle = default_not_bound_bundle(generated_at=STAMP)
    bundle["canonical_decision"] = project_canonical_decision_snapshot_v1(
        instrument_id="PF_XBTUSD",
        decision="HOLD",
        direction="FLAT",
        reason_codes=("OK",),
        blockers=(),
        decision_id="d1",
        evidence_schema_version="canonical_trading_decision_evidence_v1",
        evidence_digest=None,
        generated_at=STAMP,
        effective_at=STAMP,
        source_reference="ref",
    )
    bundle["safety_authority"] = unavailable_safety_authority(
        availability=Availability.INVALID,
        generated_at=STAMP,
        reason="BAD",
    )
    health = build_source_health_from_snapshots(bundle, generated_at=STAMP)
    assert health.availability is Availability.INVALID
    assert health.slot_availability["canonical_decision"] is Availability.AVAILABLE


def test_serialization_stability() -> None:
    snap = project_double_play_snapshot_v1(
        overall_status="display_ready",
        panel_summaries=({"name": "composition", "status": "display_ready"},),
        blockers=(),
        generated_at=STAMP,
        source_reference="dp-display",
    )
    first = dumps_projection_canonical(snap)
    second = dumps_projection_canonical(snap)
    assert first == second
    parsed = json.loads(first)
    assert parsed["availability"] == "AVAILABLE"
    assert parsed["live_authorization"] is False
    assert parsed["display_only"] is True


def test_owner_registry_reuses_canonical_modules_no_second_truth() -> None:
    registry = owner_registry_by_slot()
    decision = registry["canonical_decision"]
    assert decision.owner_module.endswith("canonical_trading_decision_evidence_v1")
    assert decision.reuse_status == "REUSED"
    dp = registry["double_play"]
    assert "double_play_dashboard_display" in dp.owner_module
    # Landscape package must not claim decision authority.
    assert "market_dashboard_landscape_v2" not in decision.owner_module


def test_schema_version_stable() -> None:
    snap = unavailable_canonical_decision(
        availability=Availability.NOT_BOUND,
        generated_at=STAMP,
        reason="X",
    )
    assert isinstance(snap, CanonicalDecisionSnapshotV1)
    assert snap.schema_version == "v1"


def test_package_lives_under_webui_not_deleted_names() -> None:
    pkg = REPO / "src" / "webui" / "market_dashboard_landscape_v2"
    assert pkg.is_dir()
    deleted = REPO / "src" / "webui" / "market_dashboard_readmodels_v1"
    assert not deleted.exists()


def _economic_available_snapshot(
    *,
    status: EconomicViabilityStatus,
    economic_validity_proven: bool,
    policy_threshold_status: str,
) -> EconomicSummarySnapshotV1:
    """Construct AVAILABLE economic summary by direct field copy (no producer load)."""
    schema_id = "market_dashboard_landscape_projection.economic_summary.v1"
    provenance = SnapshotProvenanceV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        producer_module="backtest.economic_viability_evidence_v1",
        generated_at=STAMP,
        effective_at=STAMP,
        source_kind="economic_viability_evidence_v1",
        source_reference="evidence://economic-test",
        evidence_digest="b" * 64,
        git_sha="deadbeef",
        availability=Availability.AVAILABLE,
    )
    freshness = FreshnessV1(
        observed_at=STAMP,
        max_age_seconds=None,
        is_stale=False,
        stale_reason=None,
    )
    metric = {"semantic": "COMPUTED", "value": 1.25}
    return EconomicSummarySnapshotV1(
        schema_id=schema_id,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=Availability.AVAILABLE,
        economic_viability_status=status.value,
        economic_validity_proven=economic_validity_proven,
        profitability_claim_allowed=False,
        policy_threshold_status=policy_threshold_status,
        policy_version="economic_validity_policy_v1",
        authority_effect="NONE",
        runtime_effect=False,
        order_effect=False,
        reason_codes=("REASON_A", "REASON_B"),
        profit_factor=dict(metric),
        net_return={"semantic": "COMPUTED", "value": 0.01},
        max_drawdown={"semantic": "COMPUTED", "value": -0.05},
        sharpe={"semantic": "COMPUTED", "value": 0.5},
        trade_count={"semantic": "COMPUTED", "value": 12.0},
        funding_drag={"semantic": "COMPUTED", "value": -0.001},
        evidence_ref="evidence://economic-test",
        contract_version="v1",
        owner="backtest.economic_viability_evidence_v1",
        strategy_id="strategy_x",
        strategy_version="1",
        config_digest="c" * 64,
        implementation_digest="d" * 64,
        data_digest="e" * 64,
        manifest_digest="f" * 64,
        wiring_chain_digest="g" * 64,
        policy_digest="h" * 64,
    )


def test_economic_viability_status_preserves_exact_source_enum() -> None:
    for status in EconomicViabilityStatus:
        snap = _economic_available_snapshot(
            status=status,
            economic_validity_proven=False,
            policy_threshold_status="BELOW_THRESHOLD",
        )
        assert snap.economic_viability_status == status.value
        payload = serialize_projection(snap)
        assert payload["economic_viability_status"] == status.value
        assert "economic_gate_status" not in payload


def test_economic_validity_proven_copied_not_recomputed() -> None:
    # Intentionally inconsistent with PROMISING status — proves no policy recompute.
    snap = _economic_available_snapshot(
        status=EconomicViabilityStatus.RESEARCH_ONLY,
        economic_validity_proven=True,
        policy_threshold_status="BELOW_THRESHOLD",
    )
    assert snap.economic_validity_proven is True
    assert snap.economic_viability_status == "RESEARCH_ONLY"
    assert snap.policy_threshold_status == "BELOW_THRESHOLD"


def test_policy_threshold_status_remains_distinct_from_viability_status() -> None:
    snap = _economic_available_snapshot(
        status=EconomicViabilityStatus.ECONOMICALLY_VIABLE_OFFLINE,
        economic_validity_proven=True,
        policy_threshold_status="PASS",
    )
    assert snap.economic_viability_status == "ECONOMICALLY_VIABLE_OFFLINE"
    assert snap.policy_threshold_status == "PASS"
    assert snap.economic_viability_status != snap.policy_threshold_status


def test_economic_gate_status_forbidden_for_evi_status() -> None:
    snap = _economic_available_snapshot(
        status=EconomicViabilityStatus.PROMISING,
        economic_validity_proven=False,
        policy_threshold_status="BELOW_THRESHOLD",
    )
    assert not hasattr(snap, "economic_gate_status")
    fields = set(EconomicSummarySnapshotV1.__dataclass_fields__)
    assert "economic_viability_status" in fields
    assert "economic_gate_status" not in fields


def test_economic_summary_promotion_lifecycle_risk_fields_absent() -> None:
    snap = _economic_available_snapshot(
        status=EconomicViabilityStatus.PROMISING,
        economic_validity_proven=False,
        policy_threshold_status="BELOW_THRESHOLD",
    )
    fields = set(snap.__dataclass_fields__)
    forbidden = {
        "economic_gate_status",
        "promotion_economic_gate_status",
        "promotion_eligibility",
        "promotion_status",
        "DEVELOPMENT_ONLY",
        "HOLDOUT",
        "SEALED_LONG_PANEL",
        "TERMINAL",
        "PREREGISTRATION_ONLY",
        "NOT_EVALUATED",
        "lifecycle_label",
        "research_lifecycle",
        "risk_status",
        "sizing_status",
        "capital_status",
        "quantity",
        "position_size",
        "risk_budget",
    }
    assert fields.isdisjoint(forbidden)
    payload = serialize_projection(snap)
    assert set(payload).isdisjoint(forbidden)


def test_zero_injected_economic_source_remains_not_bound() -> None:
    snap = unavailable_economic_summary(
        availability=Availability.NOT_BOUND,
        generated_at=STAMP,
        reason="LANDSCAPE_V2_SLOT_NOT_BOUND",
    )
    assert snap.availability is Availability.NOT_BOUND
    assert snap.economic_viability_status is None
    assert snap.economic_validity_proven is None
    assert snap.policy_threshold_status is None
    assert snap.profit_factor is None
    assert snap.evidence_ref is None
    bundle = default_not_bound_bundle(generated_at=STAMP)
    assert bundle["economic_summary"].availability is Availability.NOT_BOUND


def test_economic_summary_immutable_and_serializable() -> None:
    snap = _economic_available_snapshot(
        status=EconomicViabilityStatus.ECONOMICALLY_VIABLE_OFFLINE,
        economic_validity_proven=True,
        policy_threshold_status="PASS",
    )
    with pytest.raises(FrozenInstanceError):
        snap.economic_viability_status = "RESEARCH_ONLY"  # type: ignore[misc]
    first = dumps_projection_canonical(snap)
    second = dumps_projection_canonical(snap)
    assert first == second
    parsed = json.loads(first)
    assert parsed["economic_viability_status"] == "ECONOMICALLY_VIABLE_OFFLINE"
    assert parsed["reason_codes"] == ["REASON_A", "REASON_B"]
    assert parsed["profit_factor"] == {"semantic": "COMPUTED", "value": 1.25}


def test_economic_owner_registry_ratified_bound() -> None:
    entry = owner_registry_by_slot()["economic_summary"]
    assert entry.owner_module == "backtest.economic_viability_evidence_v1"
    assert entry.owner_symbol == "EconomicViabilityEvidenceV1"
    assert entry.reuse_status == "REUSED"
    assert "economic_viability_status" in entry.notes
    assert "explicit injection only" in entry.notes
    assert "MISSING_SOURCE" in entry.notes


def test_diagnostics_summary_owner_registry_option_a_not_bound() -> None:
    """Phase 4.6C OPTION_A: diagnostics_summary NOT_BOUND; owner UNRESOLVED."""
    entry = owner_registry_by_slot()["diagnostics_summary"]
    assert entry.owner_module == "UNRESOLVED"
    assert entry.owner_symbol == "UNRESOLVED"
    assert entry.reuse_status == "NOT_BOUND"
    assert entry.authority_class == "diagnostics"
    assert "Phase 4.6C" in entry.notes
    assert "OPTION_A_KEEP_NOT_BOUND" in entry.notes
    assert "WorkflowDashboardReadModelV1" in entry.notes
    assert "NON_SOURCE" in entry.notes
    assert "consumer-contract redesign" in entry.notes
    assert "OPTION_B" in entry.notes
    assert "OPTION_D" in entry.notes
    assert "OPTION_C" in entry.notes
    # Default runtime availability remains NOT_BOUND (no silent rebinding).
    bundle = default_not_bound_bundle(generated_at=STAMP)
    snap = bundle["diagnostics_summary"]
    assert snap.availability is Availability.NOT_BOUND
    assert serialize_projection(snap)["availability"] == "NOT_BOUND"
