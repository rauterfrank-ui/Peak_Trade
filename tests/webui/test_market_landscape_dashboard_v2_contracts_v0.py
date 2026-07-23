"""Contract tests for Market Dashboard Landscape V2 read-only projections."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.webui.market_dashboard_landscape_v2 import (
    AVAILABILITY_VALUES,
    SCHEMA_VERSION,
    Availability,
    CanonicalDecisionSnapshotV1,
    build_source_health_from_snapshots,
    default_not_bound_bundle,
    dumps_projection_canonical,
    owner_registry_by_slot,
    project_canonical_decision_snapshot_v1,
    project_double_play_snapshot_v1,
    serialize_projection,
)
from src.webui.market_dashboard_landscape_v2.unavailable import (
    unavailable_canonical_decision,
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
