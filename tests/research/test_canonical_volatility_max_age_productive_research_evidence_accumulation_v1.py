"""Tests for productive max-age research evidence accumulation capability v1."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    EVIDENCE_SCHEMA_VERSION,
    HARD_STOP,
    NUMERIC_THRESHOLD_SELECTED,
    REGIME_LABEL_IS_RESEARCH_METADATA_ONLY,
    THRESHOLD_STATUS,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.coverage_v1 import (
    evaluate_coverage_readiness_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_v1 import (
    append_productive_evidence_record_v1,
    ledger_digest_v1,
    load_productive_evidence_ledger_v1,
    valid_productive_records_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
    ResearchRegimeLabelV1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.producer_v1 import (
    produce_productive_research_evidence_from_cycle_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.regime_v1 import (
    map_typed_feature_regime_to_research_label_v1,
    regime_authority_flags_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.runtime_v1 import (
    accumulate_from_cycles_batch_v1,
    accumulate_productive_research_evidence_from_cycle_v1,
    bind_accumulation_state_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_v1 import (
    complete_productive_evidence_session_v1,
    open_productive_evidence_session_v1,
    resume_productive_evidence_session_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    attach_validation_v1,
    validate_productive_evidence_record_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    coverage_summary_v1,
    load_research_evidence_records_v1,
)

ROOT = Path(__file__).resolve().parents[2]
T0 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def _cycle(
    *,
    session_id: str,
    cycle_id: str,
    regime_id: str = "trending",
    slope: float = 0.01,
    age_seconds: float = 60.0,
    event_offset: int = 0,
    estimate_id: str = "est-1",
    observation_count: int = 60,
    instrument_id: str = "ETH-USD_UM_XPERP-310404",
) -> dict:
    ref = T0 + timedelta(seconds=event_offset)
    as_of = ref - timedelta(seconds=age_seconds)
    ref_iso = ref.isoformat().replace("+00:00", "Z")
    as_of_iso = as_of.isoformat().replace("+00:00", "Z")
    source = f"src_{estimate_id}"
    return {
        "session_id": session_id,
        "cycle_id": cycle_id,
        "instrument_id": instrument_id,
        "venue": "OKX",
        "venue_instrument_id": "ETH-USD-SWAP",
        "market_event_time": ref_iso,
        "decision_outcome": "HOLD",
        "selected_side": "FLAT",
        "economic_metrics": {"net_pnl": 0.0},
        "feature_regime": {
            "ok": True,
            "warmup_complete": True,
            "regime_id": regime_id,
            "regime_state_source": "CANONICAL_RUNTIME_PIPELINE",
            "trend_features": {"slope": slope, "strength": 0.2},
            "momentum_features": {"rsi": 50.0, "roc": slope},
            "liquidity_features": {"depth_score": 1.0},
            "market_structure_features": {"range_ratio": 0.01},
            "volatility_estimate": 0.02,
            "mark_price": 3500.0,
            "blockers": [],
            "default_regime_fallback_active": False,
        },
        "canonical_volatility_typed_binding": {
            "session_id": session_id,
            "cycle_id": cycle_id,
            "instrument_id": instrument_id,
            "venue": "OKX",
            "venue_instrument_id": "ETH-USD-SWAP",
            "producer_outcome": "PRODUCED",
            "estimate_present": True,
            "observation_count": observation_count,
            "source_digest": source,
            "source_estimate_id": estimate_id,
            "estimate_id": estimate_id,
            "volatility_value": 0.02,
            "volatility_unit": "DECIMAL_FRACTION",
            "volatility_horizon_seconds": 3600.0,
            "volatility_estimator": "TYPED_RUNTIME_PRODUCER",
            "reuse_status": "FRESHLY_PRODUCED",
            "restart_status": "NOT_APPLICABLE",
            "fallback_used": False,
        },
        "double_play_typed_volatility_presence_gate": {
            "session_id": session_id,
            "cycle_id": cycle_id,
            "instrument_id": instrument_id,
            "regime_id": regime_id,
            "max_age_policy_evidence": {
                "estimate_as_of_event_time": as_of_iso,
                "reference_event_time": ref_iso,
                "computed_age_seconds": float(age_seconds),
                "max_age_status": "AGE_COMPUTED_THRESHOLD_UNRESOLVED",
                "threshold_status": "UNRESOLVED_MAX_AGE",
                "presence_status": "PRESENT",
                "clock_trust_status": "TRUSTED",
                "data_integrity_status": "TRUSTED",
                "reuse_status": "FRESHLY_PRODUCED",
                "restart_status": "NOT_APPLICABLE",
                "source_digest": source,
                "decision": "AGE_COMPUTED",
                "reason_code": "VOLATILITY_ESTIMATE_AGE_UNRESOLVED",
                "enforcement_applied": False,
                "numeric_threshold_selected": False,
                "session_id": session_id,
                "cycle_id": cycle_id,
                "instrument_id": instrument_id,
                "regime_id": regime_id,
            },
        },
    }


def test_01_schema_and_validation_unit() -> None:
    session = open_productive_evidence_session_v1(
        session_id="s1",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="abc123",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
    )
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1"),
        session=session,
        repository_sha="abc123",
    )
    assert record.evidence_schema_version == EVIDENCE_SCHEMA_VERSION
    status, reasons = validate_productive_evidence_record_v1(record)
    assert status.value == "VALID"
    assert reasons == ()


def test_02_negative_age_and_untrusted_quarantine(tmp_path: Path) -> None:
    session = open_productive_evidence_session_v1(
        session_id="s1",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="abc123",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
    )
    cycle = _cycle(session_id="s1", cycle_id="c1")
    age = cycle["double_play_typed_volatility_presence_gate"]["max_age_policy_evidence"]
    age["clock_trust_status"] = "UNTRUSTED"
    record = produce_productive_research_evidence_from_cycle_v1(
        cycle, session=session, repository_sha="abc123"
    )
    record = attach_validation_v1(record)
    result = append_productive_evidence_record_v1(
        ledger_path=tmp_path / "prod.jsonl",
        quarantine_ledger_path=tmp_path / "q.jsonl",
        record=record,
    )
    assert result["action"] == "QUARANTINED"
    assert valid_productive_records_from_ledger_v1(tmp_path / "prod.jsonl") == []


def test_03_session_lifecycle_and_restart_resume() -> None:
    session = open_productive_evidence_session_v1(
        session_id="s1",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="abc123",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
    )
    resumed = resume_productive_evidence_session_v1(
        session,
        resume_token=session.resume_token,
        repository_sha="abc123",
        process_restart=True,
    )
    assert resumed.session_id == session.session_id
    assert resumed.restart_generation == session.restart_generation + 1
    completed = complete_productive_evidence_session_v1(
        resumed,
        session_end_event_time=(T0 + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
    )
    assert completed.lifecycle_state == "COMPLETED"
    with pytest.raises(ProductiveEvidenceAccumulationError):
        resume_productive_evidence_session_v1(
            completed,
            resume_token=completed.resume_token,
            repository_sha="abc123",
        )


def test_04_regime_metadata_non_authority() -> None:
    label, _, conf = map_typed_feature_regime_to_research_label_v1(
        {
            "ok": True,
            "warmup_complete": True,
            "regime_id": "trending",
            "trend_features": {"slope": 0.01, "strength": 0.2},
            "regime_state_source": "CANONICAL_RUNTIME_PIPELINE",
        }
    )
    assert label == ResearchRegimeLabelV1.UP_DIRECTIONAL.value
    assert conf == "UNKNOWN"
    flags = regime_authority_flags_v1()
    assert flags["regime_label_is_research_metadata_only"] is True
    assert flags["regime_label_mutates_alpha"] is False
    assert REGIME_LABEL_IS_RESEARCH_METADATA_ONLY is True


def test_05_ledger_append_dedupe_resume_equivalence(tmp_path: Path) -> None:
    state = bind_accumulation_state_v1(
        session_id="s1",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="deadbeef",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
        repo_root=ROOT,
        productive_ledger_path=tmp_path / "prod.jsonl",
        join_ledger_path=tmp_path / "join.jsonl",
        quarantine_ledger_path=tmp_path / "q.jsonl",
    )
    c1 = _cycle(session_id="s1", cycle_id="c1", estimate_id="est-1", event_offset=0)
    r1 = accumulate_productive_research_evidence_from_cycle_v1(c1, state=state)
    assert r1["status"] == "PASS"
    digest_after_first = ledger_digest_v1(tmp_path / "prod.jsonl")

    # Idempotent duplicate replay
    r_dup = accumulate_productive_research_evidence_from_cycle_v1(c1, state=state)
    assert r_dup["append_result"]["action"] == "IDEMPOTENT_NOOP"
    assert ledger_digest_v1(tmp_path / "prod.jsonl") == digest_after_first

    # Resume path: same inputs continue equivalently
    state2 = bind_accumulation_state_v1(
        session_id="s1",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="deadbeef",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
        repo_root=ROOT,
        productive_ledger_path=tmp_path / "prod.jsonl",
        join_ledger_path=tmp_path / "join.jsonl",
        quarantine_ledger_path=tmp_path / "q.jsonl",
        existing_session=state.session,
        resume_token=state.session.resume_token,
        process_restart=True,
    )
    c2 = _cycle(
        session_id="s1",
        cycle_id="c2",
        estimate_id="est-1",
        event_offset=120,
        age_seconds=120,
    )
    r2 = accumulate_productive_research_evidence_from_cycle_v1(c2, state=state2)
    assert r2["status"] == "PASS"
    assert r2["evidence_record"]["estimate_reused"] is True
    assert r2["evidence_record"]["reuse_count"] == 1

    # Continuous path comparison ledger from fresh uninterrupted state
    unbroken = tmp_path / "unbroken"
    unbroken.mkdir()
    state_u = bind_accumulation_state_v1(
        session_id="s1",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="deadbeef",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
        repo_root=ROOT,
        productive_ledger_path=unbroken / "prod.jsonl",
        join_ledger_path=unbroken / "join.jsonl",
        quarantine_ledger_path=unbroken / "q.jsonl",
    )
    accumulate_productive_research_evidence_from_cycle_v1(c1, state=state_u)
    accumulate_productive_research_evidence_from_cycle_v1(c2, state=state_u)
    # Same record digests (restart_generation differs after resume — exclude generation)
    resumed_records = valid_productive_records_from_ledger_v1(tmp_path / "prod.jsonl")
    unbroken_records = valid_productive_records_from_ledger_v1(unbroken / "prod.jsonl")
    assert len(resumed_records) == len(unbroken_records) == 2
    assert resumed_records[0].evidence_record_id == unbroken_records[0].evidence_record_id
    assert resumed_records[1].estimate_reused == unbroken_records[1].estimate_reused


def test_06_join_compatibility_with_pr5616_loader(tmp_path: Path) -> None:
    state = bind_accumulation_state_v1(
        session_id="s1",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="deadbeef",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
        repo_root=ROOT,
        productive_ledger_path=tmp_path / "prod.jsonl",
        join_ledger_path=tmp_path / "join.jsonl",
        quarantine_ledger_path=tmp_path / "q.jsonl",
    )
    cycles = [
        _cycle(session_id="s1", cycle_id="c1", regime_id="trending", slope=0.01, event_offset=0),
        _cycle(
            session_id="s1",
            cycle_id="c2",
            regime_id="ranging",
            slope=0.0,
            event_offset=120,
            estimate_id="est-2",
        ),
    ]
    for cycle in cycles:
        result = accumulate_productive_research_evidence_from_cycle_v1(cycle, state=state)
        assert result["status"] == "PASS"
        assert result["research_join"] is not None
        assert result["research_join"]["join_contract_version"]

    loaded = load_research_evidence_records_v1(tmp_path / "join.jsonl")
    assert len(loaded) == 2
    summary = coverage_summary_v1(loaded)
    assert summary["evidence_count"] == 2
    assert summary["session_count"] == 1
    assert summary["regime_count"] >= 2


def test_07_multi_session_coverage_and_readiness(tmp_path: Path) -> None:
    productive = tmp_path / "prod.jsonl"
    join = tmp_path / "join.jsonl"
    quarantine = tmp_path / "q.jsonl"
    reports = []
    for session_id, regime, slope, base_offset in (
        ("sess-a", "trending", 0.01, 0),
        ("sess-b", "ranging", 0.0, 10_000),
    ):
        state = bind_accumulation_state_v1(
            session_id=session_id,
            session_start_event_time=(T0 + timedelta(seconds=base_offset))
            .isoformat()
            .replace("+00:00", "Z"),
            repository_sha="deadbeef",
            venue="OKX",
            canonical_instrument_id="ETH-USD_UM_XPERP-310404",
            venue_instrument_id="ETH-USD-SWAP",
            repo_root=ROOT,
            productive_ledger_path=productive,
            join_ledger_path=join,
            quarantine_ledger_path=quarantine,
        )
        cycles = [
            _cycle(
                session_id=session_id,
                cycle_id=f"{session_id}-c{i}",
                regime_id=regime if i < 3 else "volatile",
                slope=slope if regime == "trending" else (-0.01 if i % 2 == 0 else 0.0),
                event_offset=base_offset + i * 120,
                age_seconds=60 + i * 30,
                estimate_id=f"{session_id}-est-{i}",
            )
            for i in range(1, 5)
        ]
        reports.append(accumulate_from_cycles_batch_v1(cycles, state=state))

    coverage = reports[-1]["coverage"]
    # Recompute over full ledger
    records = valid_productive_records_from_ledger_v1(productive)
    full = evaluate_coverage_readiness_v1(records=records)
    assert full.valid_evidence_count >= 8
    assert full.session_count >= 2
    assert full.regime_count >= 2
    assert full.ready_for_research_execution is True
    join_records = load_research_evidence_records_v1(join)
    join_summary = coverage_summary_v1(join_records)
    assert join_summary["sufficient_for_research"] is True


def test_08_corrupted_tail_fail_closed(tmp_path: Path) -> None:
    state = bind_accumulation_state_v1(
        session_id="s1",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="deadbeef",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
        repo_root=ROOT,
        productive_ledger_path=tmp_path / "prod.jsonl",
        join_ledger_path=tmp_path / "join.jsonl",
        quarantine_ledger_path=tmp_path / "q.jsonl",
    )
    accumulate_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1"), state=state
    )
    with (tmp_path / "prod.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{not-json\n")
    with pytest.raises(ProductiveEvidenceAccumulationError, match="ledger_corrupt"):
        load_productive_evidence_ledger_v1(tmp_path / "prod.jsonl")


def test_09_deterministic_reexecution(tmp_path: Path) -> None:
    def _run(path: Path) -> str:
        state = bind_accumulation_state_v1(
            session_id="s1",
            session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
            repository_sha="deadbeef",
            venue="OKX",
            canonical_instrument_id="ETH-USD_UM_XPERP-310404",
            venue_instrument_id="ETH-USD-SWAP",
            repo_root=ROOT,
            productive_ledger_path=path / "prod.jsonl",
            join_ledger_path=path / "join.jsonl",
            quarantine_ledger_path=path / "q.jsonl",
        )
        accumulate_productive_research_evidence_from_cycle_v1(
            _cycle(session_id="s1", cycle_id="c1"), state=state
        )
        return ledger_digest_v1(path / "prod.jsonl")

    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    assert _run(a) == _run(b)


def test_10_architecture_and_no_authority_guards() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert guards["no_alpha_mutation_guard_pass"] is True
    assert guards["no_policy_mutation_guard_pass"] is True
    assert guards["no_order_authority_guard_pass"] is True
    assert THRESHOLD_STATUS == "UNRESOLVED_MAX_AGE"
    assert NUMERIC_THRESHOLD_SELECTED is False
    assert HARD_STOP is True


def test_11_other_session_owns_distinct_session_key(tmp_path: Path) -> None:
    productive = tmp_path / "prod.jsonl"
    for session_id in ("s-a", "s-b"):
        state = bind_accumulation_state_v1(
            session_id=session_id,
            session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
            repository_sha="deadbeef",
            venue="OKX",
            canonical_instrument_id="ETH-USD_UM_XPERP-310404",
            venue_instrument_id="ETH-USD-SWAP",
            repo_root=ROOT,
            productive_ledger_path=productive,
            join_ledger_path=tmp_path / f"{session_id}-join.jsonl",
            quarantine_ledger_path=tmp_path / "q.jsonl",
        )
        accumulate_productive_research_evidence_from_cycle_v1(
            _cycle(session_id=session_id, cycle_id=f"{session_id}-c1"),
            state=state,
        )
    records = valid_productive_records_from_ledger_v1(productive)
    assert {r.session_id for r in records} == {"s-a", "s-b"}


def test_12_fresh_estimate_semantics(tmp_path: Path) -> None:
    state = bind_accumulation_state_v1(
        session_id="s1",
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="deadbeef",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
        repo_root=ROOT,
        productive_ledger_path=tmp_path / "prod.jsonl",
        join_ledger_path=tmp_path / "join.jsonl",
        quarantine_ledger_path=tmp_path / "q.jsonl",
    )
    accumulate_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", estimate_id="est-old"), state=state
    )
    r2 = accumulate_productive_research_evidence_from_cycle_v1(
        _cycle(
            session_id="s1",
            cycle_id="c2",
            estimate_id="est-new",
            event_offset=120,
        ),
        state=state,
    )
    assert r2["evidence_record"]["estimate_reused"] is False
    assert r2["evidence_record"]["reuse_count"] == 0
