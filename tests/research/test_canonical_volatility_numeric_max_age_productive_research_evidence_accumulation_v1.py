"""Focused tests for numeric max-age productive research evidence accumulation v1."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.architecture_guards_v1 import (
    assert_architecture_guards_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    BLOCKED_FOR_PARAMETER_DECISION,
    COUNTERFACTUAL_ONLY,
    EVIDENCE_SUFFICIENT_FOR_PARAMETER_DECISION,
    NUMERIC_THRESHOLD_SELECTED,
    REVIEW_MODE_ID,
    THRESHOLD_STATUS,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.counterfactual_grid_v1 import (
    evaluate_counterfactual_age_grid_batch_v1,
    evaluate_counterfactual_age_grid_for_record_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.evaluability_v1 import (
    evaluate_productive_evidence_evaluability_v1,
    parameter_decision_prerequisites_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_v1 import (
    append_productive_evidence_record_v1,
    ledger_digest_v1,
    load_productive_evidence_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.preregistration_v1 import (
    RESEARCH_AGE_CANDIDATE_GRID_SECONDS,
    assert_preregistration_before_evidence_v1,
    build_productive_evidence_accumulation_preregistration_v1,
    preregistration_matrix_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.producer_v1 import (
    produce_productive_research_evidence_from_cycle_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.session_v1 import (
    open_productive_evidence_session_v1,
    resume_productive_evidence_session_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    compute_age_seconds_v1,
)
from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
    MAX_AGE_ENFORCEMENT_ENABLED,
    VOLATILITY_UNKNOWN_ENTRY_FAIL_CLOSED,
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
    estimate_present: bool = True,
    fallback_used: bool = False,
    volatility_value: float = 0.015,
    receive_time_offset: int | None = None,
    reuse_status: str = "FRESHLY_PRODUCED",
) -> dict:
    ref = T0 + timedelta(seconds=event_offset)
    as_of = ref - timedelta(seconds=age_seconds)
    ref_iso = ref.isoformat().replace("+00:00", "Z")
    as_of_iso = as_of.isoformat().replace("+00:00", "Z")
    receive = None
    if receive_time_offset is not None:
        receive = (ref + timedelta(seconds=receive_time_offset)).isoformat().replace("+00:00", "Z")
    source = f"src_{estimate_id}"
    return {
        "session_id": session_id,
        "cycle_id": cycle_id,
        "instrument_id": "ETH-USD_UM_XPERP-310404",
        "venue": "OKX",
        "venue_instrument_id": "ETH-USD-SWAP",
        "market_event_time": ref_iso,
        "receive_time": receive,
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
            "volatility_estimate": volatility_value,
            "mark_price": 3500.0,
            "blockers": [],
            "default_regime_fallback_active": fallback_used,
            "volatility_regime": "HIGH_VOLATILITY" if regime_id == "volatile" else "UNCLASSIFIED",
        },
        "canonical_volatility_typed_binding": {
            "session_id": session_id,
            "cycle_id": cycle_id,
            "instrument_id": "ETH-USD_UM_XPERP-310404",
            "venue": "OKX",
            "venue_instrument_id": "ETH-USD-SWAP",
            "producer_outcome": "PRODUCED" if estimate_present else "ABSENT",
            "estimate_present": estimate_present,
            "observation_count": observation_count,
            "source_digest": source,
            "source_estimate_id": estimate_id,
            "estimate_id": estimate_id,
            "volatility_value": volatility_value,
            "volatility_unit": "DECIMAL_FRACTION",
            "volatility_horizon_seconds": 3600.0,
            "volatility_estimator": "TYPED_RUNTIME_PRODUCER",
            "reuse_status": reuse_status,
            "restart_status": "NOT_APPLICABLE",
            "fallback_used": fallback_used,
        },
        "double_play_typed_volatility_presence_gate": {
            "session_id": session_id,
            "cycle_id": cycle_id,
            "instrument_id": "ETH-USD_UM_XPERP-310404",
            "regime_id": regime_id,
            "max_age_policy_evidence": {
                "estimate_as_of_event_time": as_of_iso if estimate_present else None,
                "reference_event_time": ref_iso,
                "computed_age_seconds": float(age_seconds) if estimate_present else None,
                "max_age_status": "AGE_COMPUTED_THRESHOLD_UNRESOLVED",
                "threshold_status": "UNRESOLVED_MAX_AGE",
                "presence_status": "PRESENT" if estimate_present else "ABSENT",
                "clock_trust_status": "TRUSTED",
                "data_integrity_status": "TRUSTED",
                "reuse_status": reuse_status,
                "restart_status": "NOT_APPLICABLE",
                "source_digest": source,
                "decision": "AGE_COMPUTED",
                "reason_code": "VOLATILITY_ESTIMATE_AGE_UNRESOLVED",
                "enforcement_applied": False,
                "numeric_threshold_selected": False,
                "session_id": session_id,
                "cycle_id": cycle_id,
                "instrument_id": "ETH-USD_UM_XPERP-310404",
                "regime_id": regime_id,
            },
        },
    }


def _session(session_id: str = "s1"):
    return open_productive_evidence_session_v1(
        session_id=session_id,
        session_start_event_time=T0.isoformat().replace("+00:00", "Z"),
        repository_sha="abc123",
        venue="OKX",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD-SWAP",
    )


def test_01_event_time_age_correctly_computed() -> None:
    age = compute_age_seconds_v1(
        market_event_time="2026-01-01T00:10:00Z",
        as_of_event_time="2026-01-01T00:05:00Z",
    )
    assert age == 300.0
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", age_seconds=300.0),
        session=_session(),
        repository_sha="abc123",
    )
    assert record.estimate_age_seconds == 300.0
    assert record.age_seconds == 300.0
    assert record.age_reference_clock == "MARKET_EVENT_TIME"


def test_02_receive_time_does_not_replace_event_time() -> None:
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(
            session_id="s1",
            cycle_id="c1",
            age_seconds=120.0,
            receive_time_offset=9999,
        ),
        session=_session(),
        repository_sha="abc123",
    )
    assert record.receive_time is not None
    assert record.estimate_age_seconds == 120.0
    assert "9999" not in str(record.estimate_age_seconds)


def test_03_duplicate_samples_do_not_increase_distinct_observation_count() -> None:
    session = _session()
    # Same estimate identity / as_of; later observation only advances market event time.
    first = produce_productive_research_evidence_from_cycle_v1(
        _cycle(
            session_id="s1",
            cycle_id="c1",
            estimate_id="est-dup",
            event_offset=0,
            age_seconds=60.0,
        ),
        session=session,
        repository_sha="abc123",
    )
    second = produce_productive_research_evidence_from_cycle_v1(
        _cycle(
            session_id="s1",
            cycle_id="c2",
            estimate_id="est-dup",
            event_offset=120,
            age_seconds=180.0,
        ),
        session=session,
        repository_sha="abc123",
        prior_source_estimate_id=first.source_estimate_id,
        prior_reuse_count=0,
        prior_cycle_id=first.cycle_id,
    )
    assert first.as_of_event_time == second.as_of_event_time
    assert second.estimate_reused is True
    assert second.reuse_status == "DUPLICATE_SAMPLE_REUSE"
    from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.evaluability_v1 import (
        compute_session_metrics_v1,
    )

    metrics = compute_session_metrics_v1([first, second])
    assert metrics["observation_count"] == 2
    assert metrics["distinct_observation_count"] == 1


def test_04_runtime_cycles_are_not_market_samples() -> None:
    from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
        RUNTIME_CYCLE_IS_NOT_MARKET_SAMPLE,
    )

    assert RUNTIME_CYCLE_IS_NOT_MARKET_SAMPLE is True
    prereg = build_productive_evidence_accumulation_preregistration_v1()
    assert "runtime cycle index is never a market sample" in prereg.distinct_observation_semantics


def test_05_out_of_order_policy_deterministic() -> None:
    session = _session()
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(
            session_id="s1",
            cycle_id="c1",
            reuse_status="OUT_OF_ORDER_REJECTED_REUSE",
            event_offset=10,
        ),
        session=session,
        repository_sha="abc123",
    )
    assert record.reuse_status == "OUT_OF_ORDER_REJECTED_REUSE"
    again = produce_productive_research_evidence_from_cycle_v1(
        _cycle(
            session_id="s1",
            cycle_id="c1",
            reuse_status="OUT_OF_ORDER_REJECTED_REUSE",
            event_offset=10,
        ),
        session=session,
        repository_sha="abc123",
    )
    assert again.record_digest == record.record_digest


def test_06_missing_required_fields_fail_closed() -> None:
    session = _session()
    bad = _cycle(session_id="s1", cycle_id="c1")
    bad["double_play_typed_volatility_presence_gate"]["max_age_policy_evidence"] = {}
    with pytest.raises(ProductiveEvidenceAccumulationError):
        produce_productive_research_evidence_from_cycle_v1(
            bad, session=session, repository_sha="abc123"
        )


def test_07_ledger_append_only(tmp_path: Path) -> None:
    session = _session()
    ledger = tmp_path / "productive.jsonl"
    quarantine = tmp_path / "quarantine.jsonl"
    r1 = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", event_offset=0),
        session=session,
        repository_sha="abc123",
    )
    r2 = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c2", estimate_id="est-2", event_offset=60),
        session=session,
        repository_sha="abc123",
    )
    append_productive_evidence_record_v1(
        ledger_path=ledger, quarantine_ledger_path=quarantine, record=r1
    )
    append_productive_evidence_record_v1(
        ledger_path=ledger, quarantine_ledger_path=quarantine, record=r2
    )
    loaded = load_productive_evidence_ledger_v1(ledger)
    assert len(loaded) == 2
    assert loaded[0].ledger_record_sequence == 1
    assert loaded[1].ledger_record_sequence == 2
    assert loaded[1].prev_ledger_chain_digest == loaded[0].ledger_chain_digest


def test_08_ledger_digest_reproducible(tmp_path: Path) -> None:
    session = _session()
    ledger = tmp_path / "productive.jsonl"
    quarantine = tmp_path / "quarantine.jsonl"
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1"),
        session=session,
        repository_sha="abc123",
    )
    append_productive_evidence_record_v1(
        ledger_path=ledger, quarantine_ledger_path=quarantine, record=record
    )
    d1 = ledger_digest_v1(ledger)
    d2 = ledger_digest_v1(ledger)
    assert d1 == d2


def test_09_restart_and_session_separation() -> None:
    session = _session("s-restart")
    resumed = resume_productive_evidence_session_v1(
        session,
        resume_token=session.resume_token,
        repository_sha="abc123",
        process_restart=True,
    )
    assert resumed.session_id == session.session_id
    assert resumed.restart_generation == session.restart_generation + 1
    other = _session("s-other")
    assert other.session_id != resumed.session_id


def test_10_counterfactual_does_not_mutate_decision() -> None:
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", age_seconds=900.0),
        session=_session(),
        repository_sha="abc123",
    )
    before = record.decision_outcome
    cells = evaluate_counterfactual_age_grid_for_record_v1(record)
    assert cells
    assert all(c.alpha_decision_mutated is False for c in cells)
    assert record.decision_outcome == before


def test_11_counterfactual_does_not_enable_enforcement() -> None:
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", age_seconds=7200.0),
        session=_session(),
        repository_sha="abc123",
    )
    batch = evaluate_counterfactual_age_grid_batch_v1([record])
    assert batch["enforcement_applied"] is False
    assert batch["threshold_selected"] is False
    assert batch["counterfactual_only"] is True
    assert all(
        c.enforcement_applied is False
        for c in evaluate_counterfactual_age_grid_for_record_v1(record)
    )


def test_12_unknown_volatility_remains_entry_fail_closed() -> None:
    assert VOLATILITY_UNKNOWN_ENTRY_FAIL_CLOSED is True
    assert MAX_AGE_ENFORCEMENT_ENABLED is False
    cells = evaluate_counterfactual_age_grid_for_record_v1(
        {
            "estimate_age_seconds": None,
            "age_seconds": None,
            "estimate_present": False,
            "counterfactual_eligible": False,
            "exit_path_preservation": True,
            "evidence_record_id": "evr_unknown",
            "session_id": "s1",
        }
    )
    assert all(c.entry_eligibility_counterfactual.startswith("ENTRY_BLOCKED") for c in cells)


def test_13_exit_paths_remain_available_for_unknown_or_stale() -> None:
    record = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", age_seconds=10000.0),
        session=_session(),
        repository_sha="abc123",
    )
    assert record.exit_path_preservation is True
    cells = evaluate_counterfactual_age_grid_for_record_v1(record)
    assert all(c.exit_path_preservation is True for c in cells)


def test_14_legacy_fallbacks_are_not_research_truth() -> None:
    session = _session()
    with pytest.raises(ProductiveEvidenceAccumulationError, match="legacy_fallback"):
        produce_productive_research_evidence_from_cycle_v1(
            _cycle(
                session_id="s1",
                cycle_id="c1",
                fallback_used=True,
                volatility_value=0.02,
            ),
            session=session,
            repository_sha="abc123",
        )


def test_15_offline_runtime_evidence_semantics_equivalent() -> None:
    session = _session()
    offline = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", age_seconds=180.0, event_offset=0),
        session=session,
        repository_sha="abc123",
    )
    runtime_like = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", age_seconds=180.0, event_offset=0),
        session=session,
        repository_sha="abc123",
    )
    assert offline.estimate_age_seconds == runtime_like.estimate_age_seconds
    assert offline.age_reference_clock == runtime_like.age_reference_clock
    assert offline.record_digest == runtime_like.record_digest


def test_16_same_inputs_produce_same_evidence() -> None:
    session = _session()
    a = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", age_seconds=240.0),
        session=session,
        repository_sha="abc123",
    )
    b = produce_productive_research_evidence_from_cycle_v1(
        _cycle(session_id="s1", cycle_id="c1", age_seconds=240.0),
        session=session,
        repository_sha="abc123",
    )
    assert a.record_digest == b.record_digest
    assert a.evidence_record_id == b.evidence_record_id


def test_17_no_threshold_promotion() -> None:
    prereg = assert_preregistration_before_evidence_v1()
    assert prereg.threshold_selected is False
    assert NUMERIC_THRESHOLD_SELECTED is False
    assert THRESHOLD_STATUS == "UNRESOLVED_MAX_AGE"
    report = evaluate_productive_evidence_evaluability_v1([])
    assert report["max_age_threshold_selected"] is False
    assert report["selected_threshold"] is None
    assert report["blocked_for_parameter_decision"] is True
    assert BLOCKED_FOR_PARAMETER_DECISION is True
    assert EVIDENCE_SUFFICIENT_FOR_PARAMETER_DECISION is False


def test_18_no_alpha_or_state_semantics_change() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["no_alpha_mutation_guard_pass"] is True
    assert guards["blocked_for_parameter_decision"] is True
    assert guards["counterfactual_only"] is True
    assert COUNTERFACTUAL_ONLY is True
    assert REVIEW_MODE_ID.endswith("PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_V1")
    matrix = preregistration_matrix_v1()
    assert matrix["research_age_candidate_grid_seconds"] == list(
        RESEARCH_AGE_CANDIDATE_GRID_SECONDS
    )
    prereq = parameter_decision_prerequisites_v1()
    assert prereq["current_status"] == "BLOCKED_FOR_PARAMETER_DECISION"
    assert prereq["required_separate_operator_go"] is True
