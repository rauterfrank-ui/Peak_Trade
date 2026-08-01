"""Contract tests: max-age research design + evidence accumulation v1."""

from __future__ import annotations

import json
import math
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)
from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    CAPABILITY_ID,
    COUNTERFACTUAL_ENFORCEMENT_ENABLED,
    ENFORCEMENT_APPLIED,
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
    PARAMETER_RESEARCH_EXECUTED,
    PREREGISTERED_LEAKAGE_CONTROLS,
    PREREGISTERED_REJECTION_CRITERIA,
    PREREGISTERED_RESEARCH_DIMENSIONS,
    PREREGISTERED_RESEARCH_METRICS,
    PREREGISTERED_ROBUSTNESS_REQUIREMENTS,
    PREREGISTERED_SELECTION_CRITERIA,
    PREREGISTERED_STRESS_CONTROLS,
    THRESHOLD_SELECTED,
    CounterfactualAgeLabelV1,
    MaxAgeResearchDesignContractError,
    MaxAgeSelectionCriterionV1,
    accumulate_max_age_research_evidence_record_from_cycle_v1,
    append_max_age_research_evidence_ledger_record_v1,
    assert_architecture_guards_v1,
    assert_capability_non_goals_v1,
    build_max_age_research_evidence_join_from_cycle_v1,
    build_max_age_research_evidence_join_v1,
    build_ratified_max_age_research_design_contract_v1,
    evaluate_counterfactual_max_age_threshold_diagnostic_v1,
    load_max_age_research_evidence_ledger_v1,
    summarize_max_age_research_evidence_accumulation_v1,
    validate_max_age_research_design_contract_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    VolatilityPresenceStatusV1,
    VolatilityRestartStatusV1,
    VolatilityReuseStatusV1,
    derive_reuse_and_restart_status_for_age_policy_v1,
    evaluate_canonical_volatility_estimate_age_policy_v1,
)
from trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
    CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1,
)
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
)

T0 = 1_700_000_000.0
AS_OF = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)
VENUE = "okx_europe"
CANON = "ETH-USD_UM_XPERP-310404"
VENUE_INST = "ETH-USD_UM_XPERP-310404"


def _context(*, market_event_time: str | None = None) -> CanonicalMarketContextV1:
    ref = market_event_time or "2026-06-30T12:05:00+00:00"
    return with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id="ctx-eth-max-age-research",
            instrument_id=CANON,
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=1,
            market_event_time=ref,
            decision_time="2026-06-30T12:05:01+00:00",
            bar_interval="1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=3500.0,
            index_price=3499.5,
            best_bid=3499.8,
            best_ask=3500.2,
            spread=0.4,
            volume=1_250_000.0,
            open_interest=85_000_000.0,
            funding_rate=0.00012,
            volatility_estimate=0.38,
            trend_feature_set={"slope": 0.02},
            momentum_feature_set={"rsi": 55.0},
            liquidity_feature_set={"depth_score": 0.88},
            market_structure_feature_set={"range_ratio": 0.42},
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=WarmupStatus.WARMUP_COMPLETE,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
            canonical_volatility_estimate=None,
        )
    )


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


def _age_evidence(**kwargs):
    return evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=None,
        reference_market_event_time=AS_OF,
        presence_status=VolatilityPresenceStatusV1.MISSING,
        reuse_status=VolatilityReuseStatusV1.WARMUP_WITHOUT_ESTIMATE,
        **kwargs,
    )


def _cycle(
    *,
    session_id: str = "sess-a",
    cycle_id: str = "sess-a-c0",
    instrument_id: str = CANON,
    regime_id: str = "trending",
    age=None,
    binding_extra: dict | None = None,
    gate_extra: dict | None = None,
) -> dict:
    age_payload = (age or _age_evidence()).to_dict()
    binding = {
        "producer_outcome": "WARMUP",
        "reuse_status": VolatilityReuseStatusV1.WARMUP_WITHOUT_ESTIMATE.value,
        "restart_status": VolatilityRestartStatusV1.NOT_APPLICABLE.value,
        "restart_without_estimate": False,
        "estimate_present": False,
        "observation_count": None,
        "source_digest": None,
    }
    if binding_extra:
        binding.update(binding_extra)
    gate = {
        "alpha_scope_entry_authority_allowed": False,
        "max_age_policy_evidence": age_payload,
    }
    if gate_extra:
        gate.update(gate_extra)
    return {
        "session_id": session_id,
        "cycle_id": cycle_id,
        "cycle_index": 0,
        "instrument_id": instrument_id,
        "trading_epoch": 1,
        "decision_outcome": "HOLD",
        "selected_side": "none",
        "economic_metrics": {"net_pnl": "0"},
        "feature_regime": {"regime_id": regime_id},
        "canonical_volatility_typed_binding": binding,
        "double_play_typed_volatility_presence_gate": gate,
    }


def test_01_research_design_contract_complete_unresolved_digested() -> None:
    design = build_ratified_max_age_research_design_contract_v1()
    assert design.threshold_status == "UNRESOLVED_MAX_AGE"
    assert design.numeric_max_age_seconds is None
    assert design.enforcement_enabled is False
    assert design.enforcement_applied is False
    assert design.alpha_enforcement_allowed is False
    assert design.parameter_research_executed is False
    assert design.research_question
    assert design.candidate_threshold_source
    assert design.dataset_scope
    assert design.session_scope
    assert design.instrument_scope
    assert design.cost_assumptions
    assert design.purged_split_policy
    assert design.embargo_policy
    assert design.walk_forward_design
    assert design.final_holdout_policy
    assert design.minimum_evidence_requirements
    assert set(design.candidate_dimensions) == set(PREREGISTERED_RESEARCH_DIMENSIONS)
    assert set(design.metrics) == set(PREREGISTERED_RESEARCH_METRICS)
    assert set(design.leakage_controls) == set(PREREGISTERED_LEAKAGE_CONTROLS)
    assert set(design.stress_controls) == set(PREREGISTERED_STRESS_CONTROLS)
    assert set(design.robustness_controls) == set(PREREGISTERED_ROBUSTNESS_REQUIREMENTS)
    assert set(design.rejection_criteria) == set(PREREGISTERED_REJECTION_CRITERIA)
    assert set(design.selection_criteria) == set(PREREGISTERED_SELECTION_CRITERIA)
    assert MaxAgeSelectionCriterionV1.NO_BEST_SHARPE_POINT_SELECTION.value in (
        design.selection_criteria
    )
    again = build_ratified_max_age_research_design_contract_v1()
    assert again.preregistration_digest == design.preregistration_digest
    assert len(design.preregistration_digest) == 64
    validate_max_age_research_design_contract_v1(design)


def test_01b_research_design_rejects_empty_required_fields() -> None:
    design = build_ratified_max_age_research_design_contract_v1()
    broken = replace(design, research_question="   ", preregistration_digest="0" * 64)
    assert {f.name for f in fields(design)}
    try:
        validate_max_age_research_design_contract_v1(broken)
        raise AssertionError("expected fail-closed")
    except MaxAgeResearchDesignContractError:
        pass


def test_02_reuse_restart_mapper_productive_labels() -> None:
    assert derive_reuse_and_restart_status_for_age_policy_v1(
        producer_outcome="PRODUCED",
        cycle_without_sample=False,
        estimate_bound=True,
        restart_without_estimate=False,
    ) == (
        VolatilityReuseStatusV1.FRESHLY_PRODUCED,
        VolatilityRestartStatusV1.NOT_APPLICABLE,
    )
    assert derive_reuse_and_restart_status_for_age_policy_v1(
        producer_outcome="DUPLICATE_NOOP",
        cycle_without_sample=False,
        estimate_bound=True,
        restart_without_estimate=False,
    ) == (
        VolatilityReuseStatusV1.DUPLICATE_SAMPLE_REUSE,
        VolatilityRestartStatusV1.NOT_APPLICABLE,
    )
    assert derive_reuse_and_restart_status_for_age_policy_v1(
        producer_outcome="WARMUP",
        cycle_without_sample=True,
        estimate_bound=True,
        restart_without_estimate=False,
    ) == (
        VolatilityReuseStatusV1.NO_SAMPLE_REUSE,
        VolatilityRestartStatusV1.NOT_APPLICABLE,
    )
    assert derive_reuse_and_restart_status_for_age_policy_v1(
        producer_outcome="OUT_OF_ORDER_REJECTED",
        cycle_without_sample=False,
        estimate_bound=False,
        restart_without_estimate=False,
    ) == (
        VolatilityReuseStatusV1.OUT_OF_ORDER_REJECTED_REUSE,
        VolatilityRestartStatusV1.NOT_APPLICABLE,
    )
    assert derive_reuse_and_restart_status_for_age_policy_v1(
        producer_outcome="PRODUCED",
        cycle_without_sample=False,
        estimate_bound=True,
        restart_without_estimate=False,
        first_production_after_restart=True,
    ) == (
        VolatilityReuseStatusV1.FRESHLY_PRODUCED,
        VolatilityRestartStatusV1.FIRST_PRODUCTION_AFTER_RESTART,
    )
    assert derive_reuse_and_restart_status_for_age_policy_v1(
        producer_outcome="WARMUP",
        cycle_without_sample=True,
        estimate_bound=False,
        restart_without_estimate=True,
    ) == (
        VolatilityReuseStatusV1.WARMUP_WITHOUT_ESTIMATE,
        VolatilityRestartStatusV1.RESTART_WITHOUT_ESTIMATE,
    )
    assert not hasattr(VolatilityRestartStatusV1, "RESTORED_EXISTING_ESTIMATE")


def test_03_binding_host_emits_reuse_restart_into_presence_gate(tmp_path: Path) -> None:
    host = CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=tmp_path / "h.json",
    )
    ctx = _context()
    produced = None
    for i in range(0, 61):
        produced = host.apply_to_market_context_v1(
            ctx,
            sample=_sample(i),
            transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
            ingest_sample=True,
        )
    assert produced is not None
    assert produced.telemetry.reuse_status == VolatilityReuseStatusV1.FRESHLY_PRODUCED.value
    assert produced.telemetry.restart_status == VolatilityRestartStatusV1.NOT_APPLICABLE.value

    dup = host.apply_to_market_context_v1(
        ctx,
        sample=_sample(60),
        transport=ObservationTransportMetadataV1(receive_time=T0 + 60 * 60 + 0.5),
        ingest_sample=True,
    )
    assert dup.telemetry.reuse_status == VolatilityReuseStatusV1.DUPLICATE_SAMPLE_REUSE.value
    assert dup.bound_estimate is not None
    as_of = dup.bound_estimate.as_of_event_time

    no_sample = host.apply_to_market_context_v1(dup.context, ingest_sample=False)
    assert no_sample.telemetry.reuse_status == VolatilityReuseStatusV1.NO_SAMPLE_REUSE.value
    assert no_sample.bound_estimate is not None
    assert no_sample.bound_estimate.as_of_event_time == as_of

    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        no_sample.context,
        eligibility=no_sample.typed_binding_eligibility,
        reuse_status=VolatilityReuseStatusV1(no_sample.telemetry.reuse_status),
        restart_status=VolatilityRestartStatusV1(no_sample.telemetry.restart_status),
    )
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.reuse_status == (
        VolatilityReuseStatusV1.NO_SAMPLE_REUSE.value
    )
    assert gate.max_age_policy_evidence.enforcement_applied is False
    assert gate.alpha_scope_entry_authority_allowed is True


def test_04_restart_restore_labels_fail_closed_no_estimate_rematerialization(
    tmp_path: Path,
) -> None:
    path = tmp_path / "hist.json"
    host = CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=path,
    )
    ctx = _context()
    for i in range(0, 61):
        host.apply_to_market_context_v1(
            ctx,
            sample=_sample(i),
            transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
            ingest_sample=True,
        )
    restored = (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.restore_from_persistence_v1(
            persistence_path=path,
        )
    )
    cycle = restored.apply_to_market_context_v1(ctx, ingest_sample=False)
    assert cycle.telemetry.restart_status == (
        VolatilityRestartStatusV1.RESTART_WITHOUT_ESTIMATE.value
    )
    assert cycle.telemetry.reuse_status != VolatilityReuseStatusV1.FRESHLY_PRODUCED.value
    assert cycle.bound_estimate is None
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        cycle.context,
        eligibility=cycle.typed_binding_eligibility,
        reuse_status=VolatilityReuseStatusV1(cycle.telemetry.reuse_status),
        restart_status=VolatilityRestartStatusV1(cycle.telemetry.restart_status),
    )
    assert gate.alpha_scope_entry_authority_allowed is False
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.max_age_status == "UNDEFINED"


def test_04b_invalid_restore_fail_closed(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not-json", encoding="utf-8")
    try:
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.restore_from_persistence_v1(
            persistence_path=bad,
        )
        raise AssertionError("expected fail-closed restore")
    except Exception:
        pass


def test_05_research_evidence_join_and_digest() -> None:
    age = _age_evidence()
    join = build_max_age_research_evidence_join_v1(
        session_id="s1",
        cycle_id="c1",
        instrument_id=CANON,
        regime_id="trending",
        max_age_policy_evidence=age,
        producer_outcome="WARMUP",
        reuse_status=VolatilityReuseStatusV1.WARMUP_WITHOUT_ESTIMATE.value,
        restart_status=VolatilityRestartStatusV1.NOT_APPLICABLE.value,
        estimate_present=False,
        decision_outcome="HOLD",
    )
    assert join.threshold_status == "UNRESOLVED_MAX_AGE"
    assert join.enforcement_applied is False
    assert join.join_digest
    assert len(join.join_digest) == 64
    again = build_max_age_research_evidence_join_v1(
        session_id="s1",
        cycle_id="c1",
        instrument_id=CANON,
        regime_id="trending",
        max_age_policy_evidence=age,
        producer_outcome="WARMUP",
        reuse_status=VolatilityReuseStatusV1.WARMUP_WITHOUT_ESTIMATE.value,
        restart_status=VolatilityRestartStatusV1.NOT_APPLICABLE.value,
        estimate_present=False,
        decision_outcome="HOLD",
    )
    assert again.join_digest == join.join_digest


def test_06_join_rejects_enforcement_resolved_and_empty_identities() -> None:
    age = _age_evidence()
    payload = age.to_dict()
    payload["enforcement_applied"] = True
    try:
        build_max_age_research_evidence_join_v1(
            session_id="s",
            cycle_id="c",
            instrument_id=CANON,
            regime_id="trending",
            max_age_policy_evidence=payload,
        )
        raise AssertionError("expected fail-closed")
    except MaxAgeResearchDesignContractError:
        pass
    payload = age.to_dict()
    payload["threshold_status"] = "RESOLVED"
    try:
        build_max_age_research_evidence_join_v1(
            session_id="s",
            cycle_id="c",
            instrument_id=CANON,
            regime_id="trending",
            max_age_policy_evidence=payload,
        )
        raise AssertionError("expected fail-closed")
    except MaxAgeResearchDesignContractError:
        pass
    for kwargs in (
        {"session_id": "", "cycle_id": "c", "instrument_id": CANON, "regime_id": "r"},
        {"session_id": "s", "cycle_id": "  ", "instrument_id": CANON, "regime_id": "r"},
        {"session_id": "s", "cycle_id": "c", "instrument_id": "", "regime_id": "r"},
        {"session_id": "s", "cycle_id": "c", "instrument_id": CANON, "regime_id": None},
    ):
        try:
            build_max_age_research_evidence_join_v1(
                max_age_policy_evidence=age,
                **kwargs,
            )
            raise AssertionError(f"expected fail-closed for {kwargs}")
        except MaxAgeResearchDesignContractError:
            pass


def test_06b_join_rejects_cross_identity_mismatches() -> None:
    age = _age_evidence()
    try:
        build_max_age_research_evidence_join_from_cycle_v1(
            _cycle(
                session_id="sess-a",
                binding_extra={"session_id": "sess-b"},
                age=age,
            )
        )
        raise AssertionError("expected cross-session fail-closed")
    except MaxAgeResearchDesignContractError as exc:
        assert "cross_session" in str(exc)
    try:
        build_max_age_research_evidence_join_from_cycle_v1(
            _cycle(
                instrument_id=CANON,
                gate_extra={"instrument_id": "BTC-USD_UM_XPERP-1"},
                age=age,
            )
        )
        raise AssertionError("expected cross-instrument fail-closed")
    except MaxAgeResearchDesignContractError as exc:
        assert "cross_instrument" in str(exc)
    try:
        build_max_age_research_evidence_join_from_cycle_v1(
            _cycle(
                cycle_id="c-1",
                binding_extra={"cycle_id": "c-2"},
                age=age,
            )
        )
        raise AssertionError("expected cross-cycle fail-closed")
    except MaxAgeResearchDesignContractError as exc:
        assert "cross_cycle" in str(exc)


def test_07_counterfactual_diagnostic_no_enforcement() -> None:
    fresh = evaluate_counterfactual_max_age_threshold_diagnostic_v1(
        computed_age_seconds=30.0,
        candidate_max_age_seconds_argument=60.0,
    )
    stale = evaluate_counterfactual_max_age_threshold_diagnostic_v1(
        computed_age_seconds=90.0,
        candidate_max_age_seconds_argument=60.0,
    )
    missing = evaluate_counterfactual_max_age_threshold_diagnostic_v1(
        computed_age_seconds=None,
        candidate_max_age_seconds_argument=60.0,
    )
    assert fresh.counterfactual_label == (
        CounterfactualAgeLabelV1.WOULD_BE_FRESH_IF_THRESHOLD.value
    )
    assert stale.counterfactual_label == (
        CounterfactualAgeLabelV1.WOULD_BE_STALE_IF_THRESHOLD.value
    )
    assert missing.counterfactual_label == CounterfactualAgeLabelV1.AGE_UNAVAILABLE.value
    assert fresh.enforcement_applied is False
    assert fresh.alpha_decision_mutated is False
    assert stale.threshold_status_productive == "UNRESOLVED_MAX_AGE"
    assert COUNTERFACTUAL_ENFORCEMENT_ENABLED is False


def test_08_multi_session_multi_regime_accumulation_and_duplicates(tmp_path: Path) -> None:
    ledger = tmp_path / "research_evidence_ledger.jsonl"
    records: list[dict] = []
    for session_id, regime_id in (("sess-a", "trending"), ("sess-b", "volatile")):
        join = accumulate_max_age_research_evidence_record_from_cycle_v1(
            _cycle(
                session_id=session_id,
                cycle_id=f"{session_id}-c0",
                regime_id=regime_id,
            ),
            ledger_path=ledger,
            in_memory_ledger=records,
        )
        assert join.session_id == session_id
        assert join.regime_id == regime_id

    loaded = load_max_age_research_evidence_ledger_v1(ledger)
    assert len(loaded) == 2
    summary = summarize_max_age_research_evidence_accumulation_v1(loaded)
    assert summary["multi_session_coverage"] is True
    assert summary["multi_regime_coverage"] is True
    assert summary["numeric_max_age_decided"] is False
    assert summary["enforcement_enabled"] is False
    assert summary["parameter_research_executed"] is False
    assert len(records) == 2

    first = build_max_age_research_evidence_join_from_cycle_v1(
        _cycle(session_id="sess-a", cycle_id="sess-a-c0", regime_id="trending")
    )
    again = append_max_age_research_evidence_ledger_record_v1(
        ledger_path=ledger,
        record=first,
    )
    assert again.join_digest == first.join_digest
    assert len(load_max_age_research_evidence_ledger_v1(ledger)) == 2

    conflict = first.to_dict()
    conflict["decision_outcome"] = "ENTER"
    rebuilt = build_max_age_research_evidence_join_v1(
        session_id=conflict["session_id"],
        cycle_id=conflict["cycle_id"],
        instrument_id=conflict["instrument_id"],
        regime_id=conflict["regime_id"],
        max_age_policy_evidence={
            "estimate_as_of_event_time": conflict["estimate_as_of_event_time"],
            "reference_event_time": conflict["reference_event_time"],
            "computed_age_seconds": conflict["computed_age_seconds"],
            "max_age_status": conflict["max_age_status"],
            "threshold_status": conflict["threshold_status"],
            "presence_status": conflict["presence_status"],
            "clock_trust_status": conflict["clock_trust_status"],
            "data_integrity_status": conflict["data_integrity_status"],
            "reuse_status": conflict["reuse_status"],
            "restart_status": conflict["restart_status"],
            "source_digest": conflict["source_digest"],
            "decision": conflict["age_decision"],
            "reason_code": conflict["age_reason_code"],
            "enforcement_applied": False,
        },
        producer_outcome=conflict["producer_outcome"],
        reuse_status=conflict["reuse_status"],
        restart_status=conflict["restart_status"],
        estimate_present=conflict["estimate_present"],
        decision_outcome="ENTER",
    )
    assert rebuilt.join_digest != first.join_digest
    try:
        append_max_age_research_evidence_ledger_record_v1(
            ledger_path=ledger,
            record=rebuilt,
        )
        raise AssertionError("expected digest conflict")
    except MaxAgeResearchDesignContractError as exc:
        assert "digest_conflict" in str(exc)


def test_08b_ledger_load_fail_closed_corruption_and_authority(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.jsonl"
    corrupt.write_text("{bad\n", encoding="utf-8")
    try:
        load_max_age_research_evidence_ledger_v1(corrupt)
        raise AssertionError("expected corrupt json fail-closed")
    except MaxAgeResearchDesignContractError as exc:
        assert "ledger_corrupt_json" in str(exc)

    join = build_max_age_research_evidence_join_from_cycle_v1(_cycle())
    resolved = tmp_path / "resolved.jsonl"
    payload = join.to_dict()
    payload["threshold_status"] = "RESOLVED"
    resolved.write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        load_max_age_research_evidence_ledger_v1(resolved)
        raise AssertionError("expected resolved threshold reject")
    except MaxAgeResearchDesignContractError:
        pass

    enforced = tmp_path / "enforced.jsonl"
    payload = join.to_dict()
    payload["enforcement_applied"] = True
    enforced.write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        load_max_age_research_evidence_ledger_v1(enforced)
        raise AssertionError("expected enforcement reject")
    except MaxAgeResearchDesignContractError:
        pass

    digest_mismatch = tmp_path / "digest.jsonl"
    payload = join.to_dict()
    payload["join_digest"] = "0" * 64
    digest_mismatch.write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        load_max_age_research_evidence_ledger_v1(digest_mismatch)
        raise AssertionError("expected digest mismatch reject")
    except MaxAgeResearchDesignContractError as exc:
        assert "join_digest_mismatch" in str(exc)


def test_08c_restart_resumption_deterministic(tmp_path: Path) -> None:
    ledger = tmp_path / "resume.jsonl"
    join = append_max_age_research_evidence_ledger_record_v1(
        ledger_path=ledger,
        record=build_max_age_research_evidence_join_from_cycle_v1(_cycle()),
    )
    loaded_a = load_max_age_research_evidence_ledger_v1(ledger)
    loaded_b = load_max_age_research_evidence_ledger_v1(ledger)
    assert loaded_a == loaded_b
    assert loaded_a[0]["join_digest"] == join.join_digest


def test_09_join_from_cycle_requires_age_evidence() -> None:
    try:
        build_max_age_research_evidence_join_from_cycle_v1({"session_id": "x"})
        raise AssertionError("expected fail-closed")
    except MaxAgeResearchDesignContractError:
        pass


def test_10_architecture_guards_non_goals_and_governance() -> None:
    guards = assert_architecture_guards_v1()
    assert guards["guards_pass"] is True
    assert guards["capability_id"] == CAPABILITY_ID
    non_goals = assert_capability_non_goals_v1()
    assert non_goals["numeric_max_age_decided"] is False
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
    assert ENFORCEMENT_APPLIED is False
    assert PARAMETER_RESEARCH_EXECUTED is False
    assert THRESHOLD_SELECTED is False
    assert non_goals["hard_stop"] is True

    auth = Path("config/governance/technical_canonical_wiring_authorization_v1.json")
    text = auth.read_text(encoding="utf-8")
    assert "MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_RESEARCH_DESIGN_EVIDENCE_ACCUMULATION_V1" in text
    assert "machine-readable preregistration" in text
    assert "forbids numeric threshold selection" in text
    assert "enforcement" in text.lower()


def test_11_age_grows_under_labeled_no_sample_reuse(tmp_path: Path) -> None:
    host = CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=tmp_path / "age.json",
    )
    ctx = _context()
    produced = None
    for i in range(0, 61):
        produced = host.apply_to_market_context_v1(
            ctx,
            sample=_sample(i),
            transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
            ingest_sample=True,
        )
    assert produced is not None and produced.bound_estimate is not None
    as_of = produced.bound_estimate.as_of_event_time
    reused = host.apply_to_market_context_v1(produced.context, ingest_sample=False)
    assert reused.bound_estimate is not None
    assert reused.bound_estimate.as_of_event_time == as_of
    later = with_computed_input_digest(
        _context(market_event_time=(as_of + timedelta(seconds=300)).isoformat())
    )
    from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
        bind_typed_canonical_volatility_estimate_into_market_context_v1,
    )

    bound = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        later, reused.bound_estimate
    )
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        bound,
        reuse_status=VolatilityReuseStatusV1.NO_SAMPLE_REUSE,
        restart_status=VolatilityRestartStatusV1.NOT_APPLICABLE,
    )
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.computed_age_seconds == 300.0
    assert gate.max_age_policy_evidence.reuse_status == (
        VolatilityReuseStatusV1.NO_SAMPLE_REUSE.value
    )
    assert gate.max_age_policy_evidence.enforcement_applied is False
    assert gate.alpha_scope_entry_authority_allowed is True
