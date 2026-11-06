"""Focused tests for R1 retained-estimate late-age carrier + hold semantics."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
    ProductiveBridgeMarketSampleV1,
    run_productive_bridge_accumulation_session_v1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1 import (
    NaturalAgeProgressionLifecycleHostV1,
    assert_architecture_guards_v1 as assert_natural_age_architecture_guards_v1,
    assert_natural_age_lifecycle_productive_binding_guards_v1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    LifecycleOutcomeV1,
    NaturalAgeLifecycleErrorV1,
    RecomputeReasonV1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.productive_natural_age_lifecycle_binding_v1 import (
    ProductiveNaturalAgeLifecycleCmcBindingHostV1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.constants_v1 import (
    R1_MATERIALIZED_REPOSITORY_SHA,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.gate_v1 import (
    assert_late_age_session_has_s01_retained_estimate_carrier_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.identity_v1 import (
    derive_r1_campaign_identity_v1,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1 import (
    assert_retained_estimate_late_age_architecture_guards_v1,
    build_retained_estimate_lifecycle_carrier_payload_v1,
    estimate_id_from_source_digest_v1,
    load_retained_estimate_lifecycle_carrier_v1,
    prereg_age_grid_coverage_complete_v1,
    write_retained_estimate_lifecycle_carrier_once_v1,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.models_v1 import (
    RetainedEstimateLateAgeCarrierError,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)

ROOT = Path(__file__).resolve().parents[2]
SHA = R1_MATERIALIZED_REPOSITORY_SHA
VENUE = "okx"
CANON = "ETH-USD_UM_XPERP-310404"
VENUE_INST = "ETH-USD_UM_XPERP-310404"
T0 = 1_700_000_000.0
GRID = (60, 120, 300, 600, 900, 1800, 3600, 7200)


def _price_at(i: int) -> float:
    return 100.0 * math.exp(0.001 * i)


def _sample(i: int) -> MarketSampleIdentityV1:
    return MarketSampleIdentityV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        event_time=EventTimeInstantV1(unix_seconds=T0 + float(i * 60)),
        mark_price=_price_at(i),
    )


def _ingest(host: NaturalAgeProgressionLifecycleHostV1, i: int):
    return host.ingest_finalized_pt1m_mark_sample_v1(
        sample=_sample(i),
        transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
    )


def _warmup_to_first_produce(host: NaturalAgeProgressionLifecycleHostV1):
    for i in range(0, 60):
        obs = _ingest(host, i)
        assert obs.outcome == LifecycleOutcomeV1.WARMUP.value
    produced = _ingest(host, 60)
    assert produced.outcome == LifecycleOutcomeV1.PRODUCED.value
    return produced


def test_architecture_guards_production_authority_none() -> None:
    guards = assert_retained_estimate_late_age_architecture_guards_v1(repo_root=ROOT)
    assert guards["PRODUCTION_AUTHORITY_EFFECT"] == "NONE"
    assert guards["guards_pass"] is True
    assert_natural_age_architecture_guards_v1(repo_root=ROOT)
    assert_natural_age_lifecycle_productive_binding_guards_v1(repo_root=ROOT)


def test_carrier_round_trip_digest_write_once(tmp_path: Path) -> None:
    host = NaturalAgeProgressionLifecycleHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=tmp_path / "mh.jsonl",
    )
    host.enable_age_grid_coverage_tracking_v1(
        research_age_grid_seconds=GRID,
        minimum_distinct_observations_per_age_bucket=1,
    )
    produced = _warmup_to_first_produce(host)
    assert produced.lifecycle_state is not None
    # Cover first bucket and advance naturally.
    for i in range(61, 62):
        _ingest(host, i)
    identity = derive_r1_campaign_identity_v1(repository_sha=SHA)
    payload = build_retained_estimate_lifecycle_carrier_payload_v1(
        campaign_id=identity["campaign_id"],
        early_session_id=identity["session_01_id"],
        late_session_id=identity["session_02_id"],
        repository_sha=SHA,
        preregistration_digest="a" * 64,
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        lifecycle_state=host.lifecycle_state,
        research_age_grid_seconds=GRID,
        minimum_distinct_observations_per_age_bucket=1,
        age_bucket_observation_counts=host.age_bucket_observation_counts,
    )
    path = tmp_path / "retained_estimate_lifecycle_carrier_v1.json"
    written = write_retained_estimate_lifecycle_carrier_once_v1(path=path, payload=payload)
    loaded = load_retained_estimate_lifecycle_carrier_v1(path=path)
    assert loaded.artifact_digest == written.artifact_digest
    assert loaded.estimate_id == estimate_id_from_source_digest_v1(loaded.source_digest)
    assert loaded.as_of_event_time == written.as_of_event_time
    with pytest.raises(RetainedEstimateLateAgeCarrierError, match="duplicate_carrier_write"):
        write_retained_estimate_lifecycle_carrier_once_v1(path=path, payload=payload)


def test_s01_carrier_s02_same_identity_no_session_start(tmp_path: Path) -> None:
    persist = tmp_path / "typed_volatility_persistence.jsonl"
    carrier_path = tmp_path / "retained_estimate_lifecycle_carrier_v1.json"
    identity = derive_r1_campaign_identity_v1(repository_sha=SHA)
    preg_digest = "b" * 64

    host = NaturalAgeProgressionLifecycleHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=persist,
    )
    host.enable_age_grid_coverage_tracking_v1(
        research_age_grid_seconds=GRID,
        minimum_distinct_observations_per_age_bucket=1,
    )
    produced = _warmup_to_first_produce(host)
    assert produced.lifecycle_state is not None
    # Natural contiguous progression covering full prereg age grid on one identity.
    for i in range(61, 60 + 121):
        obs = _ingest(host, i)
        assert obs.outcome in {
            LifecycleOutcomeV1.REUSED.value,
            LifecycleOutcomeV1.RECOMPUTED.value,
        }
        if obs.outcome == LifecycleOutcomeV1.RECOMPUTED.value:
            # Should not recompute before 7201 elapsed under normal floors either,
            # but if it does mid-grid the retained identity for carrier is latest.
            pass
    assert prereg_age_grid_coverage_complete_v1(
        host.age_bucket_observation_counts,
        grid_seconds=GRID,
        minimum_distinct_observations_per_age_bucket=1,
    )
    payload = build_retained_estimate_lifecycle_carrier_payload_v1(
        campaign_id=identity["campaign_id"],
        early_session_id=identity["session_01_id"],
        late_session_id=identity["session_02_id"],
        repository_sha=SHA,
        preregistration_digest=preg_digest,
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        lifecycle_state=host.lifecycle_state,
        research_age_grid_seconds=GRID,
        minimum_distinct_observations_per_age_bucket=1,
        age_bucket_observation_counts=host.age_bucket_observation_counts,
    )
    write_retained_estimate_lifecycle_carrier_once_v1(path=carrier_path, payload=payload)
    carrier = load_retained_estimate_lifecycle_carrier_v1(path=carrier_path)
    s01_estimate_id = carrier.estimate_id
    s01_as_of = carrier.as_of_event_time

    restored = (
        ProductiveNaturalAgeLifecycleCmcBindingHostV1.restore_with_retained_estimate_carrier_v1(
            persistence_path=persist,
            retained_estimate_lifecycle_carrier_path=carrier_path,
            campaign_id=identity["campaign_id"],
            early_session_id=identity["session_01_id"],
            late_session_id=identity["session_02_id"],
            repository_sha=SHA,
            preregistration_digest=preg_digest,
            venue=VENUE,
            canonical_instrument_id=CANON,
            venue_instrument_id=VENUE_INST,
            research_age_grid_seconds=GRID,
        )
    )
    assert restored.lifecycle.lifecycle_state is not None
    assert (
        estimate_id_from_source_digest_v1(restored.lifecycle.lifecycle_state.source_digest)
        == s01_estimate_id
    )
    from datetime import timezone

    assert (
        restored.lifecycle.lifecycle_state.as_of_event_time.astimezone(timezone.utc).isoformat()
        == s01_as_of
    )
    assert restored.restart_without_estimate is False
    # Full grid already covered => hold exited; next sample may recompute via existing authority.
    # Ingest contiguous next sample.
    next_i = 60 + 121
    obs = restored.lifecycle.ingest_finalized_pt1m_mark_sample_v1(
        sample=_sample(next_i),
        transport=ObservationTransportMetadataV1(receive_time=T0 + next_i * 60 + 0.5),
    )
    assert obs.recompute_reason != RecomputeReasonV1.SESSION_START_FIRST_ESTIMATE.value


def test_hold_suppresses_elapsed_recompute_until_full_grid(tmp_path: Path) -> None:
    host = NaturalAgeProgressionLifecycleHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=tmp_path / "mh.jsonl",
    )
    produced = _warmup_to_first_produce(host)
    assert produced.lifecycle_state is not None
    retained = produced.lifecycle_state
    # Seed zero coverage with min=2 so a single natural pass cannot exit hold.
    incomplete = {str(g): 0 for g in GRID}
    host.restore_retained_lifecycle_state_v1(
        retained,
        research_age_grid_seconds=GRID,
        minimum_distinct_observations_per_age_bucket=2,
        age_bucket_observation_counts=incomplete,
        enable_late_age_hold=True,
    )
    assert host.late_age_hold_active is True
    # Contiguous progression past elapsed floor; hold must keep retained identity.
    last_obs = None
    for i in range(61, 60 + 122):
        last_obs = _ingest(host, i)
        assert host.late_age_hold_active is True
        assert last_obs.outcome == LifecycleOutcomeV1.REUSED.value
        assert last_obs.recompute_reason == RecomputeReasonV1.NOT_APPLICABLE.value
        assert last_obs.lifecycle_state is not None
        assert last_obs.lifecycle_state.source_digest == retained.source_digest
    assert last_obs is not None
    assert last_obs.age_seconds is not None and last_obs.age_seconds >= 7201

    # Coverage complete => hold exits on restore; post-hold recompute unchanged.
    host2 = NaturalAgeProgressionLifecycleHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=tmp_path / "mh2.jsonl",
    )
    produced2 = _warmup_to_first_produce(host2)
    retained2 = produced2.lifecycle_state
    assert retained2 is not None
    almost = {str(g): 1 for g in GRID}
    host2.restore_retained_lifecycle_state_v1(
        retained2,
        research_age_grid_seconds=GRID,
        minimum_distinct_observations_per_age_bucket=1,
        age_bucket_observation_counts=almost,
        enable_late_age_hold=True,
    )
    assert host2.late_age_hold_active is False
    for i in range(61, 60 + 122):
        obs2 = _ingest(host2, i)
    assert obs2.outcome == LifecycleOutcomeV1.RECOMPUTED.value
    assert obs2.recompute_reason == RecomputeReasonV1.MINIMUM_EVENT_TIME_ELAPSED_REACHED.value


def test_fail_closed_matrix(tmp_path: Path) -> None:
    with pytest.raises(RetainedEstimateLateAgeCarrierError, match="carrier_missing"):
        load_retained_estimate_lifecycle_carrier_v1(path=tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    with pytest.raises(RetainedEstimateLateAgeCarrierError, match="malformed"):
        load_retained_estimate_lifecycle_carrier_v1(path=bad)

    identity = derive_r1_campaign_identity_v1(repository_sha=SHA)
    binding_path_missing = tmp_path
    # Monkey via gate helper
    from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.active_binding_v1 import (
        build_active_campaign_binding_v1,
    )

    binding = build_active_campaign_binding_v1(repository_sha=SHA)
    with pytest.raises(Exception, match="missing_s01_retained_estimate_carrier"):
        assert_late_age_session_has_s01_retained_estimate_carrier_v1(
            binding,
            session_id=binding.session_02_id,
            repo_root=binding_path_missing,
            evidence_root=binding_path_missing,
        )

    # S02 without carrier via bridge
    with pytest.raises(Exception, match="retained_estimate_lifecycle_carrier_path_required"):
        run_productive_bridge_accumulation_session_v1(
            session_id=identity["session_02_id"],
            campaign_id=identity["campaign_id"],
            repository_sha=SHA,
            samples=[
                ProductiveBridgeMarketSampleV1(
                    mark_price=100.0,
                    event_time_unix_seconds=T0,
                    receive_time_unix_seconds=T0 + 0.5,
                )
            ],
            repo_root=ROOT,
            productive_ledger_path=tmp_path / "p.jsonl",
            join_ledger_path=tmp_path / "j.jsonl",
            quarantine_ledger_path=tmp_path / "q.jsonl",
            retained_estimate_carrier_mode="REQUIRE_RESTORE_S02",
            early_session_id=identity["session_01_id"],
            late_session_id=identity["session_02_id"],
            preregistration_digest="c" * 64,
            require_campaign_authorization=False,
        )


def test_no_carrier_mode_mark_history_only_unchanged(tmp_path: Path) -> None:
    """Non-R1 path without carrier mode keeps mark-history-only restore semantics."""
    persist = tmp_path / "mh.jsonl"
    samples = [
        ProductiveBridgeMarketSampleV1(
            mark_price=_price_at(i),
            event_time_unix_seconds=T0 + float(i * 60),
            receive_time_unix_seconds=T0 + float(i * 60) + 0.5,
        )
        for i in range(0, 65)
    ]
    run_productive_bridge_accumulation_session_v1(
        session_id="s01_non_r1",
        campaign_id="campaign_non_r1",
        repository_sha=SHA,
        samples=samples,
        repo_root=ROOT,
        productive_ledger_path=tmp_path / "prod.jsonl",
        join_ledger_path=tmp_path / "join.jsonl",
        quarantine_ledger_path=tmp_path / "q.jsonl",
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        typed_volatility_persistence_path=persist,
        require_campaign_authorization=False,
    )
    host = ProductiveNaturalAgeLifecycleCmcBindingHostV1.restore_from_persistence_v1(
        persistence_path=persist
    )
    assert host.lifecycle.lifecycle_state is None
    assert host.restart_without_estimate is True
    # First produce after restore is SESSION_START_FIRST_ESTIMATE.
    for i in range(65, 66):
        obs = host.lifecycle.ingest_finalized_pt1m_mark_sample_v1(
            sample=_sample(i),
            transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
        )
    assert obs.outcome == LifecycleOutcomeV1.PRODUCED.value
    assert obs.recompute_reason == RecomputeReasonV1.SESSION_START_FIRST_ESTIMATE.value


def test_hold_exit_predicate_requires_full_prereg_grid() -> None:
    counts = {str(g): 1 for g in GRID}
    assert prereg_age_grid_coverage_complete_v1(
        counts, grid_seconds=GRID, minimum_distinct_observations_per_age_bucket=1
    )
    counts["7200"] = 0
    assert not prereg_age_grid_coverage_complete_v1(
        counts, grid_seconds=GRID, minimum_distinct_observations_per_age_bucket=1
    )


def test_fresh_produce_during_hold_fail_closed(tmp_path: Path) -> None:
    host = NaturalAgeProgressionLifecycleHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=tmp_path / "mh.jsonl",
    )
    produced = _warmup_to_first_produce(host)
    assert produced.lifecycle_state is not None
    host.restore_retained_lifecycle_state_v1(
        produced.lifecycle_state,
        research_age_grid_seconds=GRID,
        minimum_distinct_observations_per_age_bucket=1,
        age_bucket_observation_counts={str(g): 0 for g in GRID},
        enable_late_age_hold=True,
    )
    # Clear lifecycle to simulate missing retained SSOT under hold.
    host._lifecycle = None
    with pytest.raises(
        NaturalAgeLifecycleErrorV1, match="fresh_produce_attempt_during_late_age_hold"
    ):
        _ingest(host, 61)


def test_historical_evidence_untouched() -> None:
    hist = ROOT / (
        "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
        "campaigns/cv_maxage_productive_evidence_campaign_v1_1a638769c1dcb066/"
        "authorization/campaign_authorization.json"
    )
    if not hist.is_file():
        pytest.skip("historical untracked evidence absent")
    payload = json.loads(hist.read_text(encoding="utf-8"))
    # Historical digest must remain the pre-implementation value (not rewritten).
    assert payload["preregistration_digest"] == (
        "fc7f97aa4bf71a44493bd9fe882748f02527f82a6e872c2dff39b6d2b84b8ab6"
    )
    carrier = ROOT / (
        "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
        "campaigns/cv_maxage_productive_evidence_campaign_v1_1a638769c1dcb066/"
        "retained_estimate_lifecycle_carrier_v1.json"
    )
    assert not carrier.exists()
