"""Evaluability and robustness analyses without threshold selection."""

from __future__ import annotations

import random
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.counterfactual_grid_v1 import (
    evaluate_counterfactual_age_grid_batch_v1,
    evaluate_counterfactual_age_grid_for_record_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.coverage_v1 import (
    evaluate_coverage_readiness_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveResearchEvidenceRecordV1,
    sha256_hex,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.preregistration_v1 import (
    RESEARCH_AGE_CANDIDATE_GRID_SECONDS,
    build_productive_evidence_accumulation_preregistration_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1 import (
    parse_event_time,
)

EVALUABILITY_SCHEMA_VERSION = (
    "canonical_volatility_numeric_max_age_productive_research_evaluability/v1"
)
SESSION_BLOCKED_BOOTSTRAP_REPETITIONS = 64
SESSION_BLOCKED_BOOTSTRAP_SEED = 0xA6E00101
PARAMETER_DECISION_STATUS_BLOCKED = "BLOCKED_FOR_PARAMETER_DECISION"


def _as_payload(record: ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(record, ProductiveResearchEvidenceRecordV1):
        return record.to_dict()
    return dict(record)


def _distinct_observation_key(payload: Mapping[str, Any]) -> tuple[str, ...]:
    return (
        str(payload.get("source_estimate_id") or ""),
        str(payload.get("as_of_event_time") or ""),
        str(payload.get("volatility_source_digest") or ""),
        str(payload.get("market_sample_id") or ""),
    )


def _age_seconds(payload: Mapping[str, Any]) -> Optional[float]:
    raw = payload.get("estimate_age_seconds", payload.get("age_seconds"))
    if raw is None:
        return None
    return float(raw)


def compute_session_metrics_v1(
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
) -> dict[str, Any]:
    payloads = [_as_payload(r) for r in records]
    observation_count = len(payloads)
    distinct = {_distinct_observation_key(p) for p in payloads}
    duplicate_count = sum(
        1
        for p in payloads
        if p.get("estimate_reused") or p.get("reuse_status") == "DUPLICATE_SAMPLE_REUSE"
    )
    out_of_order_count = sum(
        1 for p in payloads if str(p.get("reuse_status") or "") == "OUT_OF_ORDER_REJECTED_REUSE"
    )
    sessions = sorted({str(p.get("session_id") or "") for p in payloads if p.get("session_id")})
    regimes = sorted({str(p.get("regime_label") or p.get("regime") or "") for p in payloads})
    vol_regimes = sorted(
        {str(p.get("volatility_regime") or "") for p in payloads if p.get("volatility_regime")}
    )

    # Transition counts across event-time order within each session.
    stale_transitions = 0
    unknown_transitions = 0
    trusted_to_untrusted = 0
    refresh_intervals: list[float] = []
    data_gaps: list[float] = []
    by_session: dict[str, list[dict[str, Any]]] = {}
    for p in payloads:
        by_session.setdefault(str(p.get("session_id") or ""), []).append(p)
    for session_rows in by_session.values():
        ordered = sorted(
            session_rows,
            key=lambda row: str(
                row.get("market_event_time") or row.get("observation_event_time") or ""
            ),
        )
        prev = None
        for row in ordered:
            if prev is not None:
                prev_present = bool(prev.get("estimate_present"))
                cur_present = bool(row.get("estimate_present"))
                if prev_present and not cur_present:
                    unknown_transitions += 1
                prev_trusted = (
                    str(prev.get("clock_trust_state")) == "TRUSTED"
                    and str(prev.get("data_trust_state")) == "TRUSTED"
                )
                cur_trusted = (
                    str(row.get("clock_trust_state")) == "TRUSTED"
                    and str(row.get("data_trust_state")) == "TRUSTED"
                )
                if prev_trusted and not cur_trusted:
                    trusted_to_untrusted += 1
                prev_age = _age_seconds(prev)
                cur_age = _age_seconds(row)
                # Diagnostic stale transition: age increased across observations.
                if prev_age is not None and cur_age is not None and cur_age > prev_age:
                    stale_transitions += 1
                try:
                    t0 = parse_event_time(
                        prev.get("market_event_time"), field_name="market_event_time"
                    )
                    t1 = parse_event_time(
                        row.get("market_event_time"), field_name="market_event_time"
                    )
                    gap = (t1 - t0).total_seconds()
                    data_gaps.append(float(gap))
                    if prev.get("source_estimate_id") != row.get("source_estimate_id"):
                        refresh_intervals.append(float(gap))
                except Exception:
                    pass
            prev = row

    return {
        "observation_count": observation_count,
        "distinct_observation_count": len(distinct),
        "duplicate_rate": (duplicate_count / observation_count) if observation_count else 0.0,
        "out_of_order_rate": (out_of_order_count / observation_count) if observation_count else 0.0,
        "stale_transition_count": stale_transitions,
        "unknown_transition_count": unknown_transitions,
        "trusted_to_untrusted_transition_count": trusted_to_untrusted,
        "estimate_refresh_interval_mean": (
            sum(refresh_intervals) / len(refresh_intervals) if refresh_intervals else None
        ),
        "data_gap_seconds_mean": (sum(data_gaps) / len(data_gaps) if data_gaps else None),
        "session_ids": sessions,
        "regime_coverage": regimes,
        "volatility_regime_coverage": vol_regimes,
        "exit_path_preservation_rate": (
            sum(1 for p in payloads if p.get("exit_path_preservation", True)) / observation_count
            if observation_count
            else 1.0
        ),
    }


def coverage_by_age_bucket_v1(
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
) -> dict[str, Any]:
    matrix: dict[str, dict[str, Any]] = {}
    for candidate in RESEARCH_AGE_CANDIDATE_GRID_SECONDS:
        key = f"AGE_LE_{candidate}_S"
        fresh = 0
        stale = 0
        eligible_entry = 0
        for record in records:
            cells = evaluate_counterfactual_age_grid_for_record_v1(record)
            cell = next(c for c in cells if c.candidate_max_age_seconds == candidate)
            if cell.would_be_fresh:
                fresh += 1
            if cell.would_be_stale:
                stale += 1
            if cell.entry_eligibility_counterfactual == "ENTRY_WOULD_BE_ALLOWED_IF_THRESHOLD":
                eligible_entry += 1
        matrix[key] = {
            "candidate_max_age_seconds": candidate,
            "fresh_count": fresh,
            "stale_count": stale,
            "entry_allowed_count": eligible_entry,
            "coverage_fraction_fresh": (fresh / len(records)) if records else 0.0,
        }
    return {
        "age_bucket_coverage_matrix": matrix,
        "ranking_with_productive_winner": False,
        "selected_threshold": None,
    }


def coverage_by_session_and_regime_v1(
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
) -> dict[str, Any]:
    by_session: dict[str, int] = {}
    by_regime: dict[str, int] = {}
    by_vol_regime: dict[str, int] = {}
    for record in records:
        p = _as_payload(record)
        sid = str(p.get("session_id") or "UNKNOWN")
        regime = str(p.get("regime_label") or p.get("regime") or "UNCLASSIFIED")
        vol = str(p.get("volatility_regime") or "UNCLASSIFIED")
        by_session[sid] = by_session.get(sid, 0) + 1
        by_regime[regime] = by_regime.get(regime, 0) + 1
        by_vol_regime[vol] = by_vol_regime.get(vol, 0) + 1
    return {
        "coverage_by_session": dict(sorted(by_session.items())),
        "coverage_by_market_regime": dict(sorted(by_regime.items())),
        "coverage_by_volatility_regime": dict(sorted(by_vol_regime.items())),
    }


def _fresh_fraction_for_candidate(
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
    candidate: int,
) -> float:
    if not records:
        return 0.0
    fresh = 0
    for record in records:
        cells = evaluate_counterfactual_age_grid_for_record_v1(record)
        cell = next(c for c in cells if c.candidate_max_age_seconds == candidate)
        if cell.would_be_fresh:
            fresh += 1
    return fresh / len(records)


def session_blocked_bootstrap_v1(
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
    *,
    repetitions: int = SESSION_BLOCKED_BOOTSTRAP_REPETITIONS,
    seed: int = SESSION_BLOCKED_BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Session-blocked bootstrap CIs — dependency-aware, no threshold selection."""
    by_session: dict[str, list[Any]] = {}
    for record in records:
        p = _as_payload(record)
        by_session.setdefault(str(p.get("session_id") or "UNKNOWN"), []).append(record)
    session_ids = sorted(by_session)
    if not session_ids:
        return {
            "executed": False,
            "reason": "no_sessions",
            "confidence_intervals": {},
            "selected_threshold": None,
        }

    rng = random.Random(seed)
    intervals: dict[str, dict[str, float]] = {}
    for candidate in RESEARCH_AGE_CANDIDATE_GRID_SECONDS:
        samples: list[float] = []
        for _ in range(max(1, repetitions)):
            drawn_sessions = [rng.choice(session_ids) for _ in session_ids]
            drawn_records: list[Any] = []
            for sid in drawn_sessions:
                drawn_records.extend(by_session[sid])
            samples.append(_fresh_fraction_for_candidate(drawn_records, candidate))
        samples_sorted = sorted(samples)
        lo_idx = max(0, int(0.025 * (len(samples_sorted) - 1)))
        hi_idx = min(len(samples_sorted) - 1, int(0.975 * (len(samples_sorted) - 1)))
        mean = sum(samples_sorted) / len(samples_sorted)
        intervals[f"CANDIDATE_{candidate}_S"] = {
            "mean_fresh_fraction": mean,
            "ci95_low": samples_sorted[lo_idx],
            "ci95_high": samples_sorted[hi_idx],
        }
    return {
        "executed": True,
        "method": "SESSION_BLOCKED_BOOTSTRAP",
        "repetitions": repetitions,
        "seed": seed,
        "confidence_intervals": intervals,
        "selected_threshold": None,
        "ranking_with_productive_winner": False,
    }


def stability_plateaus_v1(
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
    *,
    plateau_epsilon: float = 0.05,
) -> dict[str, Any]:
    """Identify contiguous fresh-fraction plateaus — never pick a single best value."""
    points = [
        {
            "candidate_max_age_seconds": c,
            "fresh_fraction": _fresh_fraction_for_candidate(records, c),
        }
        for c in RESEARCH_AGE_CANDIDATE_GRID_SECONDS
    ]
    plateaus: list[dict[str, Any]] = []
    if points:
        start = 0
        for idx in range(1, len(points)):
            if (
                abs(points[idx]["fresh_fraction"] - points[start]["fresh_fraction"])
                > plateau_epsilon
            ):
                plateaus.append(
                    {
                        "from_seconds": points[start]["candidate_max_age_seconds"],
                        "to_seconds": points[idx - 1]["candidate_max_age_seconds"],
                        "fresh_fraction": points[start]["fresh_fraction"],
                    }
                )
                start = idx
        plateaus.append(
            {
                "from_seconds": points[start]["candidate_max_age_seconds"],
                "to_seconds": points[-1]["candidate_max_age_seconds"],
                "fresh_fraction": points[start]["fresh_fraction"],
            }
        )
    return {
        "points": points,
        "plateaus": plateaus,
        "single_best_value_selected": False,
        "selected_threshold": None,
    }


def sensitivity_and_stress_v1(
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
) -> dict[str, Any]:
    payloads = [_as_payload(r) for r in records]
    without_duplicates = [
        p
        for p in payloads
        if not (p.get("estimate_reused") or p.get("reuse_status") == "DUPLICATE_SAMPLE_REUSE")
    ]
    without_ooo = [
        p for p in payloads if str(p.get("reuse_status") or "") != "OUT_OF_ORDER_REJECTED_REUSE"
    ]
    present_only = [p for p in payloads if p.get("estimate_present")]
    # Polling-frequency proxy: compare odd/even event-time order within sessions.
    odd_rows: list[dict[str, Any]] = []
    even_rows: list[dict[str, Any]] = []
    by_session: dict[str, list[dict[str, Any]]] = {}
    for p in payloads:
        by_session.setdefault(str(p.get("session_id") or ""), []).append(p)
    for rows in by_session.values():
        ordered = sorted(rows, key=lambda r: str(r.get("market_event_time") or ""))
        for idx, row in enumerate(ordered):
            (even_rows if idx % 2 == 0 else odd_rows).append(row)

    def _mean_age(rows: Sequence[Mapping[str, Any]]) -> Optional[float]:
        ages = [_age_seconds(r) for r in rows]
        ages_f = [a for a in ages if a is not None]
        return (sum(ages_f) / len(ages_f)) if ages_f else None

    gap_heavy = []
    for rows in by_session.values():
        ordered = sorted(rows, key=lambda r: str(r.get("market_event_time") or ""))
        for idx, row in enumerate(ordered):
            if idx == 0:
                continue
            try:
                t0 = parse_event_time(
                    ordered[idx - 1].get("market_event_time"), field_name="market_event_time"
                )
                t1 = parse_event_time(row.get("market_event_time"), field_name="market_event_time")
                if (t1 - t0).total_seconds() >= 300.0:
                    gap_heavy.append(row)
            except Exception:
                continue

    exit_regression = (
        all(bool(p.get("exit_path_preservation", True)) for p in payloads) if payloads else True
    )
    return {
        "polling_frequency_sensitivity": {
            "even_subsample_mean_age": _mean_age(even_rows),
            "odd_subsample_mean_age": _mean_age(odd_rows),
            "even_count": len(even_rows),
            "odd_count": len(odd_rows),
        },
        "duplicate_sample_sensitivity": {
            "with_duplicates_count": len(payloads),
            "without_duplicates_count": len(without_duplicates),
            "fresh_fraction_with": _fresh_fraction_for_candidate(payloads, 600),
            "fresh_fraction_without": _fresh_fraction_for_candidate(without_duplicates, 600),
        },
        "out_of_order_sensitivity": {
            "with_ooo_count": len(payloads),
            "without_ooo_count": len(without_ooo),
            "fresh_fraction_with": _fresh_fraction_for_candidate(payloads, 600),
            "fresh_fraction_without": _fresh_fraction_for_candidate(without_ooo, 600),
        },
        "missing_sample_sensitivity": {
            "all_count": len(payloads),
            "present_only_count": len(present_only),
            "missing_count": len(payloads) - len(present_only),
        },
        "data_gap_and_recovery_stress": {
            "gap_heavy_observation_count": len(gap_heavy),
            "gap_heavy_mean_age": _mean_age(gap_heavy),
        },
        "exit_path_preservation_regression": {
            "pass": exit_regression,
            "exit_path_preservation_required": True,
        },
        "selected_threshold": None,
        "ranking_with_productive_winner": False,
    }


def evaluate_productive_evidence_evaluability_v1(
    records: Sequence[ProductiveResearchEvidenceRecordV1 | Mapping[str, Any]],
    *,
    sessions: Sequence[Any] = (),
    invalid_count: int = 0,
    quarantined_count: int = 0,
    duplicate_count: int = 0,
) -> dict[str, Any]:
    """Full evaluability report. Never selects or recommends a productive threshold."""
    prereg = build_productive_evidence_accumulation_preregistration_v1()
    typed_records = [r for r in records if isinstance(r, ProductiveResearchEvidenceRecordV1)]
    coverage = evaluate_coverage_readiness_v1(
        records=typed_records,
        sessions=sessions,
        invalid_count=invalid_count,
        quarantined_count=quarantined_count,
        duplicate_count=duplicate_count,
    )
    metrics = compute_session_metrics_v1(records)
    age_bucket = coverage_by_age_bucket_v1(records)
    strata = coverage_by_session_and_regime_v1(records)
    bootstrap = session_blocked_bootstrap_v1(records)
    plateaus = stability_plateaus_v1(records)
    stress = sensitivity_and_stress_v1(records)
    counterfactual = evaluate_counterfactual_age_grid_batch_v1(records)

    evidence_sufficient = bool(coverage.ready_for_research_execution)
    # Parameter decision remains blocked in this capability even when coverage is
    # research-execution-ready — decision requires a separate authorized step.
    blocked_for_parameter_decision = True
    parameter_decision_status = PARAMETER_DECISION_STATUS_BLOCKED
    open_gaps = list(coverage.coverage_gaps)
    if not records:
        open_gaps.append("NO_PRODUCTIVE_EVIDENCE_RECORDS")
    if metrics["distinct_observation_count"] < int(
        prereg.minimum_evidence_requirements["minimum_distinct_observations_per_age_bucket"]
    ):
        open_gaps.append("MINIMUM_DISTINCT_OBSERVATIONS_PER_AGE_BUCKET")
    if len(metrics["volatility_regime_coverage"]) < int(
        prereg.minimum_evidence_requirements["minimum_volatility_regimes"]
    ):
        open_gaps.append("MINIMUM_VOLATILITY_REGIME_COVERAGE")
    open_gaps.append(PARAMETER_DECISION_STATUS_BLOCKED)

    report = {
        "evaluability_schema_version": EVALUABILITY_SCHEMA_VERSION,
        "productive_preregistration_digest": prereg.productive_preregistration_digest,
        "design_preregistration_digest": prereg.design_preregistration_digest,
        "coverage_readiness": coverage.to_dict(),
        "session_metrics": metrics,
        "age_bucket_coverage": age_bucket,
        "session_regime_coverage": strata,
        "session_blocked_bootstrap": bootstrap,
        "stability_plateaus": plateaus,
        "sensitivity_and_stress": stress,
        "counterfactual_evaluation": {
            "per_candidate": counterfactual["per_candidate"],
            "record_count": counterfactual["record_count"],
            "counterfactual_only": True,
            "threshold_selected": False,
            "enforcement_applied": False,
        },
        "evidence_sufficient_for_parameter_decision": False,
        "blocked_for_parameter_decision": blocked_for_parameter_decision,
        "parameter_decision_status": parameter_decision_status,
        "ready_for_research_execution": bool(coverage.ready_for_research_execution),
        "open_evidence_gaps": sorted(set(open_gaps)),
        "selected_threshold": None,
        "ranking_with_productive_winner": False,
        "alpha_semantics_changed": False,
        "state_semantics_changed": False,
        "enforcement_applied": False,
        "max_age_threshold_selected": False,
        "max_age_enforcement_enabled": False,
        "evidence_sufficient_for_coverage": evidence_sufficient,
    }
    report["evaluability_digest"] = sha256_hex(
        {k: v for k, v in report.items() if k != "evaluability_digest"}
    )
    return report


def parameter_decision_prerequisites_v1() -> dict[str, Any]:
    """Exact prerequisites for a later, separately authorized parameter-decision step."""
    prereg = build_productive_evidence_accumulation_preregistration_v1()
    return {
        "required_separate_operator_go": True,
        "required_review_mode": (
            "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_DECISION_V1"
        ),
        "blocked_until": [
            "PRODUCTIVE_EVIDENCE_PRESENT_ACROSS_MINIMUM_SESSIONS",
            "MINIMUM_MARKET_AND_VOLATILITY_REGIME_COVERAGE",
            "MINIMUM_DISTINCT_OBSERVATIONS_PER_AGE_BUCKET",
            "JOIN_LEDGER_LOADABLE_BY_RESEARCH_EXECUTION",
            "ROBUSTNESS_AND_STABILITY_PLATEAU_EVIDENCE_RECORDED",
            "EXPLICIT_OPERATOR_GO_FOR_PARAMETER_DECISION",
        ],
        "forbidden_in_decision_step_without_go": [
            "THRESHOLD_SELECTION",
            "ENFORCEMENT_ENABLEMENT",
            "ALPHA_OR_STATE_MUTATION",
            "POLICY_OR_CONFIG_DEFAULT_MUTATION",
        ],
        "productive_preregistration_digest": prereg.productive_preregistration_digest,
        "design_preregistration_digest": prereg.design_preregistration_digest,
        "research_age_candidate_grid_seconds": list(prereg.research_age_candidate_grid_seconds),
        "current_status": PARAMETER_DECISION_STATUS_BLOCKED,
    }
