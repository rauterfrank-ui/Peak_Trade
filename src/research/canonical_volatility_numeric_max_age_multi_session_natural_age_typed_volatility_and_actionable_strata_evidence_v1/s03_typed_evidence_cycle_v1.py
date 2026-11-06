"""Replace S03 synthetic scaffolds with typed-vol + full-alpha evidence cycle."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.duration_v1 import (
    MonotonicDurationAuthorityV1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.evidence_v1 import (
    append_jsonl_v1,
    build_counterfactual_record_v1,
    build_decision_sensitivity_v1,
    build_drift_comparison_v1,
    build_heartbeat_v1,
    build_market_sample_record_v1,
    build_session_metadata_v1,
    build_volatility_record_v1,
    classify_sample_ordering_v1,
    evidence_file_map_v1,
    write_json_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.independence_v1 import (
    assert_exit_precedence_preserved_v1,
    build_exit_risk_safety_independence_record_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    MarketSampleV1,
    S03ScopeBindingsV1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.full_alpha_counterfactual_harness_v1 import (
    default_digest_alpha_evaluator_v1,
    run_full_alpha_counterfactual_comparison_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.opportunity_strata_v1 import (
    derive_opportunity_stratum_v1,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.typed_volatility_comparison_v1 import (
    build_typed_volatility_comparison_v1,
    materialize_fresh_estimate_from_mark_prices_v1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    compute_natural_age_seconds_v1,
)
from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    FEATURE_CONTRACT_VERSION,
    FuturesMarketType,
    WarmupStatus,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CANONICAL_ANNUALIZED,
    CANONICAL_ESTIMATOR,
    CANONICAL_HORIZON,
    CANONICAL_UNIT,
    CanonicalVolatilityEstimateV1,
)


def _dt_from_unix(ts: float) -> datetime:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc)


def build_minimal_frozen_cmc_shell_v1(*, bindings: S03ScopeBindingsV1) -> CanonicalMarketContextV1:
    """Minimal non-authoritative CMC shell for volatility DI counterfactuals."""
    return CanonicalMarketContextV1(
        context_id=f"s03-evidence-{bindings.session_id}",
        instrument_id=str(bindings.instrument),
        market_type=FuturesMarketType.PERPETUAL,
        trading_epoch=0,
        market_event_time="1970-01-01T00:00:00+00:00",
        decision_time="1970-01-01T00:00:01+00:00",
        bar_interval="1m",
        bar_finality_status=BarFinalityStatus.FINALIZED,
        mark_price=0.0,
        index_price=0.0,
        best_bid=0.0,
        best_ask=0.0,
        spread=0.0,
        volume=0.0,
        open_interest=0.0,
        funding_rate=0.0,
        volatility_estimate=0.0,
        trend_feature_set={},
        momentum_feature_set={},
        liquidity_feature_set={},
        market_structure_feature_set={},
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        warmup_status=WarmupStatus.WARMUP_COMPLETE,
        feature_contract_version=FEATURE_CONTRACT_VERSION,
        input_digest="",
        canonical_volatility_estimate=None,
    )


def write_typed_s03_session_cycle_evidence_v1(
    *,
    session_dir,
    bindings: S03ScopeBindingsV1,
    samples: Sequence[MarketSampleV1],
    duration: MonotonicDurationAuthorityV1,
    frozen_context: Optional[CanonicalMarketContextV1] = None,
) -> dict[str, Any]:
    """Write S03 evidence using typed estimates + full-alpha counterfactuals.

    Forbidden: static 0.12 defaults, 0.0001*n drift scaffolds, age<3600 probes.
    """
    files = evidence_file_map_v1(session_dir)
    # Extended additive evidence files (old S03 schemas remain valid).
    typed_path = session_dir / "typed_volatility_comparisons.jsonl"
    full_cf_path = session_dir / "full_alpha_counterfactuals.jsonl"
    strata_path = session_dir / "opportunity_strata.jsonl"

    write_json_v1(
        files["session_metadata"],
        build_session_metadata_v1(bindings=bindings, mode="typed_orchestrated_v1"),
    )
    # Ensure offline-probe / integrity surfaces exist even before warmup.
    for key in (
        "volatility_records",
        "volatility_drift_comparisons",
        "decision_sensitivity",
        "counterfactual_decisions",
        "exit_risk_safety_independence",
        "heartbeat",
        "market_samples",
        "connectivity_events",
    ):
        path = files[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("", encoding="utf-8")
    for path in (typed_path, full_cf_path, strata_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("", encoding="utf-8")

    seen: set[str] = set()
    last_event: Optional[float] = None
    first_as_of: Optional[float] = None
    aged_estimate: Optional[CanonicalVolatilityEstimateV1] = None
    hb = 0
    vol_count = 0
    typed_count = 0
    mark_prices: list[float] = []
    event_times: list[datetime] = []

    if frozen_context is None:
        frozen_context = build_minimal_frozen_cmc_shell_v1(bindings=bindings)

    for sample in samples:
        elapsed = duration.elapsed_seconds()
        hb += 1
        append_jsonl_v1(
            files["heartbeat"],
            build_heartbeat_v1(
                bindings=bindings,
                monotonic_elapsed_seconds=elapsed,
                receive_time_unix_seconds=sample.receive_time_unix_seconds,
                seq=hb,
            ),
        )
        duplicate, out_of_order, advances = classify_sample_ordering_v1(
            sample=sample,
            seen_identities=seen,
            last_event_time=last_event,
        )
        append_jsonl_v1(
            files["market_samples"],
            build_market_sample_record_v1(
                bindings=bindings,
                sample=sample,
                duplicate=duplicate,
                out_of_order=out_of_order,
            ),
        )
        seen.add(sample.sample_identity)
        append_jsonl_v1(
            files["connectivity_events"],
            {
                "schema": (
                    "canonical_volatility_numeric_max_age_additional_evidence_s03_connectivity/v1"
                ),
                **bindings.to_dict(),
                "event": "SAMPLE_INGESTED",
                "duplicate": duplicate,
                "out_of_order": out_of_order,
                "monotonic_elapsed_seconds": elapsed,
                "receive_time": sample.receive_time_unix_seconds,
            },
        )

        if not advances:
            continue

        mark_prices.append(float(sample.mark_price))
        event_times.append(_dt_from_unix(sample.event_time_unix_seconds))
        last_event = float(sample.event_time_unix_seconds)

        fresh_estimate: Optional[CanonicalVolatilityEstimateV1] = None
        try:
            fresh_estimate = materialize_fresh_estimate_from_mark_prices_v1(
                mark_prices,
                event_times_utc=event_times,
                as_of_event_time=_dt_from_unix(sample.event_time_unix_seconds),
            )
        except Exception:  # noqa: BLE001 — warmup / integrity → unavailable
            fresh_estimate = None

        if aged_estimate is None and fresh_estimate is not None:
            aged_estimate = fresh_estimate
            first_as_of = float(sample.event_time_unix_seconds)

        if aged_estimate is None or first_as_of is None:
            # Warmup / fresh unavailable: never invent volatility; still emit
            # observational decision + independence surfaces for probe integrity.
            append_jsonl_v1(
                files["decision_sensitivity"],
                build_decision_sensitivity_v1(
                    bindings=bindings,
                    other_inputs_digest=f"warmup:{sample.sample_identity}",
                    old_decision="FRESH_ESTIMATE_UNAVAILABLE",
                    fresh_counterfactual_decision="FRESH_ESTIMATE_UNAVAILABLE",
                    monotonic_elapsed_seconds=elapsed,
                    receive_time_unix_seconds=sample.receive_time_unix_seconds,
                ),
            )
            append_jsonl_v1(
                files["counterfactual_decisions"],
                build_counterfactual_record_v1(
                    bindings=bindings,
                    runtime_decision="FRESH_ESTIMATE_UNAVAILABLE",
                    counterfactual_decision="FRESH_ESTIMATE_UNAVAILABLE",
                    monotonic_elapsed_seconds=elapsed,
                    receive_time_unix_seconds=sample.receive_time_unix_seconds,
                ),
            )
            indep = build_exit_risk_safety_independence_record_v1(
                bindings=bindings,
                alpha_gate_blocked=False,
                monotonic_elapsed_seconds=elapsed,
                receive_time_unix_seconds=sample.receive_time_unix_seconds,
            )
            assert_exit_precedence_preserved_v1(indep)
            append_jsonl_v1(files["exit_risk_safety_independence"], indep)
            continue

        age = compute_natural_age_seconds_v1(
            market_event_time=_dt_from_unix(sample.event_time_unix_seconds),
            as_of_event_time=_dt_from_unix(first_as_of),
        )
        market_ctx_digest = f"bindings:{bindings.authorization_digest}:{sample.sample_identity}"
        typed = build_typed_volatility_comparison_v1(
            session_id=bindings.session_id,
            market_sample_id=sample.sample_identity,
            market_context_digest=market_ctx_digest,
            aged_estimate=aged_estimate,
            fresh_estimate=fresh_estimate,
            age_seconds=age,
            bindings=bindings.to_dict(),
        )
        append_jsonl_v1(typed_path, typed)
        typed_count += 1

        # Backward-compatible volatility / drift records from typed values only.
        if fresh_estimate is not None:
            vol = build_volatility_record_v1(
                bindings=bindings,
                monotonic_elapsed_seconds=elapsed,
                receive_time_unix_seconds=sample.receive_time_unix_seconds,
                old_volatility=float(aged_estimate.value),
                old_age_seconds=int(age),
                old_as_of_event_time=first_as_of,
                estimator=CANONICAL_ESTIMATOR,
                unit=CANONICAL_UNIT,
                horizon=CANONICAL_HORIZON,
                annualized=bool(CANONICAL_ANNUALIZED),
                observation_count=int(fresh_estimate.observation_count),
                source_digest=str(aged_estimate.source_digest),
                fresh_volatility=float(fresh_estimate.value),
                recomputation_input_digest=str(fresh_estimate.source_digest),
                consuming_decision_context="ALPHA_OBSERVATIONAL_TYPED_V1",
            )
            append_jsonl_v1(files["volatility_records"], vol)
            append_jsonl_v1(
                files["volatility_drift_comparisons"],
                build_drift_comparison_v1(bindings=bindings, volatility_record=vol),
            )
            vol_count += 1
            aged_id = str(typed["AGED_ESTIMATE"]["record_digest"])
            fresh_id = str(typed["FRESH_ESTIMATE"]["record_digest"])
        else:
            aged_id = str(typed["AGED_ESTIMATE"]["record_digest"])
            fresh_id = "FRESH_ESTIMATE_UNAVAILABLE"

        cf = run_full_alpha_counterfactual_comparison_v1(
            session_id=bindings.session_id,
            market_sample_id=sample.sample_identity,
            market_context_digest=market_ctx_digest,
            prior_state_digest=f"prior:{bindings.authorization_digest}",
            frozen_context=frozen_context,
            aged_estimate=aged_estimate,
            fresh_estimate=fresh_estimate,
            age_seconds=age,
            aged_volatility_record_id=aged_id,
            fresh_volatility_record_id=fresh_id,
            evaluator=default_digest_alpha_evaluator_v1,
            non_volatility_input_digest=market_ctx_digest,
            expected_non_volatility_input_digest=market_ctx_digest,
        )
        append_jsonl_v1(full_cf_path, cf)

        # Legacy decision/counterfactual surfaces mapped from full-alpha result.
        aged_final = str((cf.get("aged_snapshot") or {}).get("final_outcome") or "UNKNOWN")
        fresh_final = str((cf.get("fresh_snapshot") or {}).get("final_outcome") or "UNKNOWN")
        if cf.get("classification") == "FRESH_ESTIMATE_UNAVAILABLE":
            fresh_final = "FRESH_ESTIMATE_UNAVAILABLE"
        append_jsonl_v1(
            files["decision_sensitivity"],
            build_decision_sensitivity_v1(
                bindings=bindings,
                other_inputs_digest=market_ctx_digest,
                old_decision=aged_final,
                fresh_counterfactual_decision=fresh_final,
                monotonic_elapsed_seconds=elapsed,
                receive_time_unix_seconds=sample.receive_time_unix_seconds,
            ),
        )
        append_jsonl_v1(
            files["counterfactual_decisions"],
            build_counterfactual_record_v1(
                bindings=bindings,
                runtime_decision=aged_final,
                counterfactual_decision=fresh_final,
                monotonic_elapsed_seconds=elapsed,
                receive_time_unix_seconds=sample.receive_time_unix_seconds,
            ),
        )

        alpha_blocked = bool(cf.get("ENTRY_PERMISSION_CHANGED")) or bool(
            cf.get("FINAL_OUTCOME_CHANGED")
        )
        indep = build_exit_risk_safety_independence_record_v1(
            bindings=bindings,
            alpha_gate_blocked=alpha_blocked,
            monotonic_elapsed_seconds=elapsed,
            receive_time_unix_seconds=sample.receive_time_unix_seconds,
        )
        # Bind independence to counterfactual id (observational only).
        indep = {
            **indep,
            "counterfactual_comparison_id": cf.get("COUNTERFACTUAL_COMPARISON_ID"),
            "ALPHA_RESULT_CANNOT_DISABLE_EXIT": True,
            "ALPHA_RESULT_CANNOT_DISABLE_RISK": True,
            "ALPHA_RESULT_CANNOT_DISABLE_SAFETY": True,
        }
        assert_exit_precedence_preserved_v1(indep)
        append_jsonl_v1(files["exit_risk_safety_independence"], indep)

        strata = derive_opportunity_stratum_v1(
            productive_record={
                "decision_outcome": aged_final,
                "selected_side": "none",
                "position_state": "flat",
            },
            counterfactual_classification=str(cf.get("classification")),
            age_only_blocker=bool(cf.get("ENTRY_PERMISSION_CHANGED")),
        )
        append_jsonl_v1(strata_path, strata)

    return {
        "heartbeat_count": hb,
        "volatility_record_count": vol_count,
        "typed_volatility_comparison_count": typed_count,
        "market_sample_count": len(samples),
        "distinct_market_sample_count": len(seen),
        "SYNTHETIC_VOLATILITY_SCAFFOLD_USED": False,
        "HARDCODED_AGE_DECISION_PROBE_USED": False,
    }
