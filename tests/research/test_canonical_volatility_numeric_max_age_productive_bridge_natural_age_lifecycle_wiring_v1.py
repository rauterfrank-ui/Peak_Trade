"""Productive bridge natural-age lifecycle wiring capability tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1 as assert_productive_accumulation_guards_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.counterfactual_grid_v1 import (
    evaluate_counterfactual_age_grid_batch_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_v1 import (
    open_productive_evidence_session_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_v1 import (
    valid_productive_records_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
    run_productive_bridge_accumulation_session_v1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1 import (
    NaturalAgeProgressionLifecycleHostV1,
    assert_architecture_guards_v1,
    assert_natural_age_lifecycle_productive_binding_guards_v1,
    assign_age_bucket_v1,
    compute_natural_age_seconds_v1,
    evaluate_counterfactual_candidate_impact_v1,
    project_actionable_alpha_strata_v1,
    project_safety_risk_exit_observability_v1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    DOUBLE_PLAY_LOGIC_CHANGED,
    MASTER_V2_LOGIC_CHANGED,
    RESEARCH_RECOMPUTE_MINIMUM_EVENT_TIME_ELAPSED_SECONDS,
    RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    LifecycleOutcomeV1,
    NaturalAgeLifecycleErrorV1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.productive_natural_age_lifecycle_binding_v1 import (
    CAPABILITY_ID,
    LEGACY_PER_SAMPLE_REMATERIALIZATION_UNREACHABLE,
    NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND,
    SECOND_AGE_AUTHORITY_PRESENT,
    SECOND_DECISION_AUTHORITY_PRESENT,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.recompute_policy_v1 import (
    evaluate_recompute_decision_v1,
    build_natural_age_research_recompute_policy_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)

ROOT = Path(__file__).resolve().parents[2]
REPO_SHA = "51a3625b3666bc905b89ba9a8ad1bcfe84494430"
VENUE = "okx"
CANON = "ETH-USD_UM_XPERP-310404"
VENUE_INST = "ETH-USD_UM_XPERP-310404"
T0 = 1_700_000_000.0
REQUIRED_AGE_BUCKETS = (0, 60, 120, 300, 600, 900, 1800, 3600, 7200)
SESSION_02_LEDGER = ROOT / (
    "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
    "campaigns/cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe/"
    "sessions/session_02_manifest.json"
)


def _price_at(i: int) -> float:
    import math

    return 100.0 * math.exp(0.001 * i)


def _sample(i: int) -> MarketSampleIdentityV1:
    return MarketSampleIdentityV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        event_time=EventTimeInstantV1(unix_seconds=T0 + float(i * 60)),
        mark_price=_price_at(i),
    )


def _host(tmp_path: Path | None = None) -> NaturalAgeProgressionLifecycleHostV1:
    path = None if tmp_path is None else tmp_path / "mark_history.json"
    return NaturalAgeProgressionLifecycleHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=path,
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


def _fingerprint_session_02() -> str | None:
    if not SESSION_02_LEDGER.exists():
        return None
    digest = hashlib.sha256()
    digest.update(SESSION_02_LEDGER.read_bytes())
    parent = SESSION_02_LEDGER.parent
    for path in sorted(parent.rglob("*")):
        if path.is_file() and path.suffix != ".lock":
            digest.update(path.relative_to(parent).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


SESSION_02_FINGERPRINT_BEFORE = _fingerprint_session_02()


def test_unit_first_produce_age_zero_distinct_zero() -> None:
    host = _host()
    produced = _warmup_to_first_produce(host)
    assert produced.age_seconds == 0.0
    assert produced.distinct_observations_since_recompute == 0
    assert produced.as_of_event_time is not None


def test_unit_plus_60_distinct_reuse() -> None:
    host = _host()
    produced = _warmup_to_first_produce(host)
    reused = _ingest(host, 61)
    assert reused.outcome == LifecycleOutcomeV1.REUSED.value
    assert reused.age_seconds == 60.0
    assert reused.distinct_observations_since_recompute == 1
    assert reused.as_of_event_time == produced.as_of_event_time


def test_unit_duplicate_full_noop() -> None:
    host = _host()
    _warmup_to_first_produce(host)
    first = _ingest(host, 61)
    dup = _ingest(host, 61)
    assert dup.outcome == LifecycleOutcomeV1.DUPLICATE_NOOP.value
    assert dup.reuse_count == first.reuse_count
    assert dup.distinct_observations_since_recompute == first.distinct_observations_since_recompute
    assert dup.age_seconds is None


def test_unit_out_of_order_no_advance() -> None:
    host = _host()
    produced = _warmup_to_first_produce(host)
    _ingest(host, 65)
    before = host.lifecycle_state
    assert before is not None
    ooo = _ingest(host, 63)
    assert ooo.outcome == LifecycleOutcomeV1.OUT_OF_ORDER_NOT_EVALUABLE.value
    after = host.lifecycle_state
    assert after is not None
    assert after.as_of_event_time == before.as_of_event_time
    assert (
        after.distinct_observations_since_recompute == before.distinct_observations_since_recompute
    )
    assert after.as_of_event_time.isoformat() == produced.as_of_event_time


def test_unit_warmup_no_artificial_age() -> None:
    host = _host()
    warm = _ingest(host, 0)
    assert warm.outcome == LifecycleOutcomeV1.WARMUP.value
    assert warm.age_seconds is None
    assert warm.age_evaluable is False
    assert host.lifecycle_state is None


def test_unit_reuse_sequence_to_age_7200_and_no_early_recompute() -> None:
    host = _host()
    produced = _warmup_to_first_produce(host)
    policy = build_natural_age_research_recompute_policy_v1()
    assert policy.minimum_new_distinct_observations == (
        RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS
    )
    assert policy.minimum_event_time_elapsed_seconds == (
        RESEARCH_RECOMPUTE_MINIMUM_EVENT_TIME_ELAPSED_SECONDS
    )
    ages: list[float] = [0.0]
    for offset in range(1, 121):
        obs = _ingest(host, 60 + offset)
        assert obs.outcome == LifecycleOutcomeV1.REUSED.value, offset
        assert obs.as_of_event_time == produced.as_of_event_time
        assert obs.age_seconds == float(offset * 60)
        ages.append(float(obs.age_seconds))
        # Decision before reuse increment: at age 7200 prior.distinct was 119.
        if offset == 120:
            assert obs.distinct_observations_since_recompute == 120
            assert obs.age_seconds == 7200.0
    assert 7200.0 in ages
    # No recompute before age 7200.
    assert all(a < 7200.0 or a == 7200.0 for a in ages)
    assert host.lifecycle_state is not None
    last = host.last_observation
    assert last is not None and last.market_event_time is not None
    # At exactly 7200 elapsed with distinct=120: elapsed < 7201 and distinct < 121 => REUSE.
    decision = evaluate_recompute_decision_v1(
        policy=policy,
        prior_state=host.lifecycle_state,
        current_market_event_time=last.market_event_time,
        newly_materialized_source_digest="ignored-slide",
    )
    assert decision[0] is False


def test_unit_recompute_after_contract_resets_state() -> None:
    host = _host()
    produced = _warmup_to_first_produce(host)
    for offset in range(1, 121):
        _ingest(host, 60 + offset)
    recomputed = _ingest(host, 60 + 121)
    assert recomputed.outcome == LifecycleOutcomeV1.RECOMPUTED.value
    assert recomputed.age_seconds == 0.0
    assert recomputed.distinct_observations_since_recompute == 0
    assert recomputed.as_of_event_time != produced.as_of_event_time
    assert recomputed.source_digest != produced.source_digest


def test_unit_negative_age_fail_closed() -> None:
    with pytest.raises(NaturalAgeLifecycleErrorV1, match="negative_age"):
        compute_natural_age_seconds_v1(
            market_event_time="2026-08-01T00:00:00+00:00",
            as_of_event_time="2026-08-01T00:01:00+00:00",
        )


def test_unit_missing_lifecycle_state_fail_closed_in_evidence_producer() -> None:
    from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
        ProductiveEvidenceAccumulationError,
    )
    from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.producer_v1 import (
        produce_productive_research_evidence_from_cycle_v1,
    )

    session = open_productive_evidence_session_v1(
        session_id="missing-lifecycle",
        session_start_event_time="2023-11-14T22:13:20+00:00",
        repository_sha=REPO_SHA,
        venue="okx_europe",
        canonical_instrument_id=CANON,
        venue_instrument_id=CANON,
    )
    cycle = {
        "session_id": "missing-lifecycle",
        "cycle_id": "c1",
        "instrument_id": CANON,
        "venue": "okx_europe",
        "venue_instrument_id": CANON,
        "decision_outcome": "hold",
        "selected_side": "none",
        "canonical_volatility_typed_binding": {
            "estimate_present": True,
            "natural_age_lifecycle_host_bound": True,
            "natural_age_seconds": None,
            "estimate_as_of_event_time": "2023-11-14T23:13:20+00:00",
            "source_digest": "abc123",
            "volatility_value": 0.01,
            "volatility_unit": "DECIMAL_FRACTION",
            "volatility_horizon_seconds": 3600,
            "volatility_estimator": "TYPED",
            "observation_count": 60,
            "estimate_id": "est_abc123",
        },
        "double_play_typed_volatility_presence_gate": {
            "max_age_policy_evidence": {
                "reference_event_time": "2023-11-14T23:13:20+00:00",
                "estimate_as_of_event_time": "2023-11-14T23:13:20+00:00",
                "computed_age_seconds": 0.0,
                "clock_trust_status": "TRUSTED",
                "data_integrity_status": "TRUSTED",
                "presence_status": "PRESENT",
                "source_digest": "abc123",
            }
        },
        "feature_regime": {"volatility_estimate": 0.01},
        "productive_bridge_cycle_authority": {
            "authority_id": (
                "MASTER_V2_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_"
                "HARDENED_BRIDGE_CYCLE_OUTPUT"
            ),
            "source_is_authoritative_bridge_cycle": True,
            "synthetic": False,
            "fixture": False,
            "test_data": False,
            "campaign_id": "c",
            "market_sample_id": "msi_x",
            "repository_sha": REPO_SHA,
        },
    }
    with pytest.raises(
        ProductiveEvidenceAccumulationError,
        match="natural_age_lifecycle_state_missing",
    ):
        produce_productive_research_evidence_from_cycle_v1(
            cycle, session=session, repository_sha=REPO_SHA
        )


def test_productive_bridge_integration_age_buckets_recompute_and_consumers(
    tmp_path: Path,
) -> None:
    import math

    from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
        ProductiveBridgeMarketSampleV1,
    )

    prod = tmp_path / "prod.jsonl"
    join = tmp_path / "join.jsonl"
    q = tmp_path / "q.jsonl"
    persist = tmp_path / "persist.json"
    # warmup(60) + produce + 120 reuse to 7200 + 1 recompute = 182 samples.
    # Explicit max_cycles override (preregistration default remains 128).
    start_unix = 1_700_000_000.0
    samples = [
        ProductiveBridgeMarketSampleV1(
            mark_price=float(100.0 * math.exp(0.001 * i)),
            event_time_unix_seconds=float(start_unix + i * 60.0),
            receive_time_unix_seconds=float(start_unix + i * 60.0 + 0.5),
        )
        for i in range(182)
    ]
    report = run_productive_bridge_accumulation_session_v1(
        session_id="natage-bridge-s1",
        campaign_id="campaign_natage_bridge_v1",
        repository_sha=REPO_SHA,
        samples=samples,
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=persist,
        require_campaign_authorization=False,
        max_cycles=182,
    )
    assert report["status"] == "PASS"
    records = valid_productive_records_from_ledger_v1(prod)
    ages = [float(r.age_seconds) for r in records]
    assert ages[0] == 0.0
    for bucket in REQUIRED_AGE_BUCKETS:
        assert bucket in ages, f"missing age bucket {bucket}"
    # Exactly one initial produce identity until recompute.
    first_as_of = records[0].as_of_event_time
    reused_block = [r for r in records if r.as_of_event_time == first_as_of]
    assert reused_block[0].age_seconds == 0.0
    assert max(float(r.age_seconds) for r in reused_block) == 7200.0
    recomputed = [r for r in records if r.as_of_event_time != first_as_of]
    assert recomputed, "expected recompute after contract boundary"
    assert float(recomputed[0].age_seconds) == 0.0

    # Evidence projections consume canonical ages unchanged (consumers, not authority).
    for rec in records:
        payload = rec.to_dict()
        assert float(payload["age_seconds"]) == float(rec.age_seconds)
        strata = project_actionable_alpha_strata_v1(productive_record=payload)
        assert strata.age_bucket == assign_age_bucket_v1(float(rec.age_seconds))
        assert strata.second_decision_authority is False
        obs = project_safety_risk_exit_observability_v1(
            strata=strata, counterfactual_stale=float(rec.age_seconds) > 60.0
        )
        assert obs.alpha_only_counterfactual_block is True
        assert obs.exit_counterfactual_block is False
        assert obs.risk_counterfactual_block is False
        assert obs.safety_counterfactual_block is False

    grid = evaluate_counterfactual_age_grid_batch_v1(records)
    assert grid["record_count"] == len(records)
    assert len(grid["research_age_candidate_grid_seconds"]) >= 8
    impact = evaluate_counterfactual_candidate_impact_v1([r.to_dict() for r in records])
    assert impact["candidate_discrimination_observed"] is True
    buckets = {assign_age_bucket_v1(a) for a in ages}
    assert "AGE_LE_7200_S" in buckets
    assert len({float(a) for a in ages}) >= len(REQUIRED_AGE_BUCKETS)


def test_architecture_guards_and_non_goals() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert guards["NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND"] is True
    assert guards["LEGACY_PER_SAMPLE_REMATERIALIZATION_UNREACHABLE"] is True
    assert guards["SECOND_AGE_AUTHORITY_PRESENT"] is False
    assert guards["SECOND_DECISION_AUTHORITY_PRESENT"] is False
    assert guards["MASTER_V2_LOGIC_CHANGED"] is False
    assert guards["DOUBLE_PLAY_LOGIC_CHANGED"] is False
    binding = assert_natural_age_lifecycle_productive_binding_guards_v1(repo_root=ROOT)
    assert binding["guards_pass"] is True
    assert NATURAL_AGE_LIFECYCLE_HOST_PRODUCTIVE_BOUND is True
    assert LEGACY_PER_SAMPLE_REMATERIALIZATION_UNREACHABLE is True
    assert SECOND_AGE_AUTHORITY_PRESENT is False
    assert SECOND_DECISION_AUTHORITY_PRESENT is False
    assert MASTER_V2_LOGIC_CHANGED is False
    assert DOUBLE_PLAY_LOGIC_CHANGED is False
    assert CAPABILITY_ID.endswith("NATURAL_AGE_LIFECYCLE_WIRING_V1")
    prod_guards = assert_productive_accumulation_guards_v1(repo_root=ROOT)
    assert prod_guards["guards_pass"] is True


def test_session_02_evidence_unchanged() -> None:
    after = _fingerprint_session_02()
    if SESSION_02_FINGERPRINT_BEFORE is None:
        pytest.skip("session_02 evidence root not present locally")
    assert after == SESSION_02_FINGERPRINT_BEFORE
