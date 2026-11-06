# src/trading/master_v2/dynamic_scope_empirical_calibration_research_v1.py
"""
Dynamic Scope empirical calibration research harness v1.

AUTHORITY=NONE — research candidates only; no productive D_t binding.
All regime transitions via execute_naked_mechanical_step_v1 (no logic reimplementation).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple

import pandas as pd

from trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
    MATERIALIZER_OWNER,
    MATERIALIZER_VERSION,
    compute_canonical_volatility_estimate_from_mark_prices_v1,
    materialize_volatility_estimate_on_bars_v1,
)
from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import (
    MECHANICAL_CORE_VERSION,
    NakedMechanicalStateV1,
    NakedMechanicalStepInputV1,
    NakedMechanicalStepResultV1,
    NakedRegimeV1,
    execute_naked_mechanical_step_v1,
    next_naked_mechanical_state_v1,
)

HARNESS_VERSION = "dynamic_scope_empirical_calibration_research/v1"
HARNESS_OWNER = "trading.master_v2.dynamic_scope_empirical_calibration_research_v1"
RUNTIME_AUTHORITY = "NONE"
PRODUCTIVE_D_T_FORMULA_SELECTED = False
PRODUCTIVE_D_T_BINDING_PRESENT = False


class ResearchCandidateFamily(str, Enum):
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    VOL_NORMALIZED = "vol_normalized"


class LineageClass(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    RESEARCH_CANDIDATE = "RESEARCH_CANDIDATE"


@dataclass(frozen=True)
class ResearchMarkObservationV1:
    timestamp_iso: str
    mark_price: float
    sigma_t: Optional[float] = None


@dataclass(frozen=True)
class ResearchDatasetIdentityV1:
    dataset_id: str
    instrument_id: str
    source_path: str
    source_content_sha256: str
    lineage_class: LineageClass
    sampling_spec: str
    volatility_definition: str
    volatility_lineage: str
    bar_count: int
    time_range_start: str
    time_range_end: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "instrument_id": self.instrument_id,
            "source_path": self.source_path,
            "source_content_sha256": self.source_content_sha256,
            "lineage_class": self.lineage_class.value,
            "sampling_spec": self.sampling_spec,
            "volatility_definition": self.volatility_definition,
            "volatility_lineage": self.volatility_lineage,
            "bar_count": self.bar_count,
            "time_range_start": self.time_range_start,
            "time_range_end": self.time_range_end,
        }


@dataclass(frozen=True)
class ResearchCandidateSpecV1:
    family: ResearchCandidateFamily
    parameter_k: float

    def label(self) -> str:
        return f"{self.family.value}:k={self.parameter_k}"


@dataclass(frozen=True)
class SwitchEventRecordV1:
    bar_index: int
    timestamp_iso: str
    cm_t: float
    d_t: float
    cm_over_d: float
    m_t: float
    sigma_t: Optional[float]
    regime_from: str
    regime_to: str


@dataclass
class CandidateRunMetricsV1:
    candidate: ResearchCandidateSpecV1
    total_bars: int
    fail_closed_steps: int
    switch_count: int
    switch_frequency_per_bar: float
    bars_between_switches_mean: Optional[float]
    whipsaw_count: int
    whipsaw_rate: float
    regime_duration_bars_mean: Optional[float]
    favorable_excursion_mean: Optional[float]
    adverse_excursion_mean: Optional[float]
    switch_events: list[SwitchEventRecordV1] = field(default_factory=list)
    segment_switch_counts: dict[str, int] = field(default_factory=dict)
    vol_quantile_switch_counts: dict[str, int] = field(default_factory=dict)
    neighbor_sensitivity: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_family": self.candidate.family.value,
            "parameter_k": self.candidate.parameter_k,
            "total_bars": self.total_bars,
            "fail_closed_steps": self.fail_closed_steps,
            "switch_count": self.switch_count,
            "switch_frequency_per_bar": self.switch_frequency_per_bar,
            "bars_between_switches_mean": self.bars_between_switches_mean,
            "whipsaw_count": self.whipsaw_count,
            "whipsaw_rate": self.whipsaw_rate,
            "regime_duration_bars_mean": self.regime_duration_bars_mean,
            "favorable_excursion_mean": self.favorable_excursion_mean,
            "adverse_excursion_mean": self.adverse_excursion_mean,
            "switch_events": [
                {
                    "bar_index": e.bar_index,
                    "timestamp_iso": e.timestamp_iso,
                    "cm_t": e.cm_t,
                    "d_t": e.d_t,
                    "cm_over_d": e.cm_over_d,
                    "m_t": e.m_t,
                    "sigma_t": e.sigma_t,
                    "regime_from": e.regime_from,
                    "regime_to": e.regime_to,
                }
                for e in self.switch_events
            ],
            "segment_switch_counts": dict(self.segment_switch_counts),
            "vol_quantile_switch_counts": dict(self.vol_quantile_switch_counts),
            "neighbor_sensitivity": dict(self.neighbor_sensitivity),
        }


@dataclass(frozen=True)
class EmpiricalCalibrationEvidenceV1:
    harness_version: str
    mechanical_core_version: str
    dataset: ResearchDatasetIdentityV1
    candidate_sweep: tuple[ResearchCandidateSpecV1, ...]
    runs: tuple[CandidateRunMetricsV1, ...]
    stability_summary: dict[str, Any]
    evidence_digest: str
    labels: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "harness_version": self.harness_version,
            "mechanical_core_version": self.mechanical_core_version,
            "runtime_authority": RUNTIME_AUTHORITY,
            "productive_d_t_formula_selected": PRODUCTIVE_D_T_FORMULA_SELECTED,
            "productive_d_t_binding_present": PRODUCTIVE_D_T_BINDING_PRESENT,
            "dataset": self.dataset.to_dict(),
            "candidate_sweep": [
                {"family": c.family.value, "parameter_k": c.parameter_k}
                for c in self.candidate_sweep
            ],
            "runs": [r.to_dict() for r in self.runs],
            "stability_summary": self.stability_summary,
            "evidence_digest": self.evidence_digest,
            "labels": self.labels,
        }


def stable_sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_research_d_t_v1(
    *,
    family: ResearchCandidateFamily,
    parameter_k: float,
    mark_price_m_t: float,
    sigma_t: Optional[float],
) -> Optional[float]:
    """RESEARCH_CANDIDATE distance only — never productive authority."""
    k = float(parameter_k)
    m = float(mark_price_m_t)
    if not math.isfinite(k) or k <= 0.0 or not math.isfinite(m) or m <= 0.0:
        return None
    if family is ResearchCandidateFamily.ABSOLUTE:
        return k
    if family is ResearchCandidateFamily.RELATIVE:
        return k * m
    if family is ResearchCandidateFamily.VOL_NORMALIZED:
        if sigma_t is None or not math.isfinite(sigma_t) or sigma_t <= 0.0:
            return None
        return k * float(sigma_t) * m
    return None


def load_cap51_offline_fixture_dataset_v1(
    *,
    repo_root: Path,
    instrument_id: str = "SOL-USDT-SWAP",
) -> tuple[ResearchDatasetIdentityV1, list[ResearchMarkObservationV1]]:
    rel = Path(
        "config/ops/fixtures/single_future_canonical_runtime_deterministic_offline_market_data_fixture_v1.json"
    )
    path = repo_root / rel
    payload = json.loads(path.read_text(encoding="utf-8"))
    obs_raw = payload["observations"]
    observations: list[ResearchMarkObservationV1] = []
    for row in obs_raw:
        if row.get("missing"):
            continue
        ts = float(row["event_time_unix"])
        observations.append(
            ResearchMarkObservationV1(
                timestamp_iso=pd.Timestamp(ts, unit="s", tz="UTC").isoformat(),
                mark_price=float(row["mark_price"]),
                sigma_t=None,
            )
        )
    if not observations:
        raise ValueError("cap51_fixture_empty")
    identity = ResearchDatasetIdentityV1(
        dataset_id="cap51_single_future_deterministic_offline_market_data_v1",
        instrument_id=instrument_id,
        source_path=str(rel),
        source_content_sha256=stable_sha256_file(path),
        lineage_class=LineageClass.OBSERVED,
        sampling_spec="fixture_observation_sequence_explicit_event_time_unix",
        volatility_definition="NONE_IN_FIXTURE",
        volatility_lineage=(
            f"{MATERIALIZER_OWNER} available for PT1M series only; "
            "cap51 sequence uses per-observation sigma=None for vol_normalized fail-closed"
        ),
        bar_count=len(observations),
        time_range_start=observations[0].timestamp_iso,
        time_range_end=observations[-1].timestamp_iso,
    )
    return identity, observations


def load_pt1m_bars_dataset_from_materializer_fixture_v1(
    *,
    repo_root: Path,
    instrument_id: str = "RESEARCH-PT1M-MATERIALIZER-FIXTURE",
) -> tuple[ResearchDatasetIdentityV1, list[ResearchMarkObservationV1]]:
    from trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
        exact_known_61_price_fixture_v1,
    )

    rel = Path("src/trading/master_v2/canonical_volatility_estimate_materializer_v1.py")
    bars = exact_known_61_price_fixture_v1()
    mat = materialize_volatility_estimate_on_bars_v1(bars)
    frame = mat.bars
    observations: list[ResearchMarkObservationV1] = []
    for ts, row in frame.iterrows():
        sigma = row["volatility_estimate"]
        sigma_v = None if pd.isna(sigma) else float(sigma)
        observations.append(
            ResearchMarkObservationV1(
                timestamp_iso=pd.Timestamp(ts).isoformat(),
                mark_price=float(row["mark_price"]),
                sigma_t=sigma_v,
            )
        )
    identity = ResearchDatasetIdentityV1(
        dataset_id="pt1m_materializer_exact_known_61_v1",
        instrument_id=instrument_id,
        source_path=str(rel),
        source_content_sha256=stable_sha256_file(repo_root / rel),
        lineage_class=LineageClass.DERIVED,
        sampling_spec="PT1M_contiguous_finalized_mark_price_is_final_true",
        volatility_definition="ROLLING_STD_LOG_RETURN_MARK_PRICE_60B",
        volatility_lineage=f"{MATERIALIZER_VERSION}/{MATERIALIZER_OWNER}",
        bar_count=len(observations),
        time_range_start=observations[0].timestamp_iso,
        time_range_end=observations[-1].timestamp_iso,
    )
    return identity, observations


def attach_sigma_from_materializer_on_series_v1(
    observations: Sequence[ResearchMarkObservationV1],
) -> list[ResearchMarkObservationV1]:
    """DERIVED sigma for irregular series when enough PT1M-like points exist."""
    if len(observations) < 2:
        return list(observations)
    idx = pd.DatetimeIndex([o.timestamp_iso for o in observations])
    marks = pd.Series([o.mark_price for o in observations], index=idx, dtype=float)
    vol = compute_canonical_volatility_estimate_from_mark_prices_v1(marks)
    out: list[ResearchMarkObservationV1] = []
    for ts, obs in zip(idx, observations, strict=True):
        sigma = vol.loc[ts]
        sigma_v = None if pd.isna(sigma) else float(sigma)
        out.append(
            ResearchMarkObservationV1(
                timestamp_iso=obs.timestamp_iso,
                mark_price=obs.mark_price,
                sigma_t=sigma_v,
            )
        )
    return out


def _segment_id(bar_index: int, total: int, segments: int) -> str:
    if total <= 0:
        return "seg-0"
    seg_len = max(1, total // segments)
    return f"seg-{bar_index // seg_len}"


def _vol_quantile_label(sigma: Optional[float], tertiles: tuple[float, float]) -> str:
    if sigma is None or not math.isfinite(sigma):
        return "sigma_invalid"
    lo, hi = tertiles
    if sigma <= lo:
        return "vol_q_low"
    if sigma <= hi:
        return "vol_q_mid"
    return "vol_q_high"


def _compute_tertiles(sigmas: Sequence[Optional[float]]) -> tuple[float, float]:
    valid = sorted(s for s in sigmas if s is not None and math.isfinite(s))
    if len(valid) < 3:
        return (float("inf"), float("inf"))
    n = len(valid)
    lo = valid[n // 3]
    hi = valid[(2 * n) // 3]
    return (lo, hi)


def simulate_candidate_on_series_v1(
    *,
    dataset: ResearchDatasetIdentityV1,
    observations: Sequence[ResearchMarkObservationV1],
    candidate: ResearchCandidateSpecV1,
    initial_regime: NakedRegimeV1 = NakedRegimeV1.BULL,
    whipsaw_window_bars: int = 2,
    temporal_segments: int = 3,
) -> CandidateRunMetricsV1:
    instrument = dataset.instrument_id
    state = NakedMechanicalStateV1(
        instrument_id=instrument,
        regime=initial_regime,
        reference_price_r_t=observations[0].mark_price,
    )
    switch_events: list[SwitchEventRecordV1] = []
    fail_closed = 0
    regime_start = 0
    regime_durations: list[int] = []
    fav_excursions: list[float] = []
    adv_excursions: list[float] = []
    tertiles = _compute_tertiles([o.sigma_t for o in observations])

    for i, obs in enumerate(observations):
        d_t = compute_research_d_t_v1(
            family=candidate.family,
            parameter_k=candidate.parameter_k,
            mark_price_m_t=obs.mark_price,
            sigma_t=obs.sigma_t,
        )
        step = execute_naked_mechanical_step_v1(
            NakedMechanicalStepInputV1(
                instrument_id=instrument,
                mark_price_m_t=obs.mark_price,
                previous_state=state,
                dynamic_scope_d_t=d_t,
            )
        )
        if step.fail_closed:
            fail_closed += 1
            continue
        if step.switch_condition_met and step.state_pre is not step.state_post:
            ratio = step.cm_t / step.d_t if step.d_t else float("nan")
            switch_events.append(
                SwitchEventRecordV1(
                    bar_index=i,
                    timestamp_iso=obs.timestamp_iso,
                    cm_t=step.cm_t,
                    d_t=float(step.d_t or 0.0),
                    cm_over_d=ratio,
                    m_t=step.m_t,
                    sigma_t=obs.sigma_t,
                    regime_from=step.state_pre.value,
                    regime_to=step.state_post.value,
                )
            )
            duration = i - regime_start
            if duration > 0:
                regime_durations.append(duration)
            if regime_start < i:
                fav, adv = _regime_excursions(
                    observations=observations,
                    start_index=regime_start,
                    end_index=i + 1,
                    regime=step.state_pre,
                )
                if fav is not None:
                    fav_excursions.append(fav)
                if adv is not None:
                    adv_excursions.append(adv)
            regime_start = i
        state = next_naked_mechanical_state_v1(previous=state, step=step)

    total = len(observations)
    switch_count = len(switch_events)
    whipsaw = _count_whipsaws(switch_events, window=whipsaw_window_bars)
    seg_counts: dict[str, int] = {f"seg-{s}": 0 for s in range(temporal_segments)}
    vol_counts: dict[str, int] = {}
    for ev in switch_events:
        seg = _segment_id(ev.bar_index, total, temporal_segments)
        seg_counts[seg] = seg_counts.get(seg, 0) + 1
        obs = observations[ev.bar_index]
        vlabel = _vol_quantile_label(obs.sigma_t, tertiles)
        vol_counts[vlabel] = vol_counts.get(vlabel, 0) + 1

    bars_between = _bars_between_switches(switch_events)
    return CandidateRunMetricsV1(
        candidate=candidate,
        total_bars=total,
        fail_closed_steps=fail_closed,
        switch_count=switch_count,
        switch_frequency_per_bar=switch_count / total if total else 0.0,
        bars_between_switches_mean=bars_between,
        whipsaw_count=whipsaw,
        whipsaw_rate=whipsaw / switch_count if switch_count else 0.0,
        regime_duration_bars_mean=(
            sum(regime_durations) / len(regime_durations) if regime_durations else None
        ),
        favorable_excursion_mean=(
            sum(fav_excursions) / len(fav_excursions) if fav_excursions else None
        ),
        adverse_excursion_mean=(
            sum(adv_excursions) / len(adv_excursions) if adv_excursions else None
        ),
        switch_events=switch_events,
        segment_switch_counts=seg_counts,
        vol_quantile_switch_counts=vol_counts,
    )


def _bars_between_switches(events: Sequence[SwitchEventRecordV1]) -> Optional[float]:
    if len(events) < 2:
        return None
    gaps = [events[i].bar_index - events[i - 1].bar_index for i in range(1, len(events))]
    return sum(gaps) / len(gaps)


def _count_whipsaws(events: Sequence[SwitchEventRecordV1], *, window: int) -> int:
    if len(events) < 2:
        return 0
    count = 0
    for i in range(1, len(events)):
        if events[i].bar_index - events[i - 1].bar_index <= window:
            count += 1
    return count


def _regime_excursions(
    *,
    observations: Sequence[ResearchMarkObservationV1],
    start_index: int,
    end_index: int,
    regime: NakedRegimeV1,
) -> tuple[Optional[float], Optional[float]]:
    if end_index <= start_index:
        return None, None
    window = observations[start_index:end_index]
    if not window:
        return None, None
    marks = [o.mark_price for o in window]
    start = window[0].mark_price
    if regime is NakedRegimeV1.BULL:
        fav = max(marks) - start
        adv = start - min(marks)
    else:
        fav = start - min(marks)
        adv = max(marks) - start
    return max(0.0, fav), max(0.0, adv)


def apply_neighbor_sensitivity_v1(
    metrics: CandidateRunMetricsV1,
    *,
    neighbor_switch_counts: Mapping[str, int],
) -> CandidateRunMetricsV1:
    metrics.neighbor_sensitivity = dict(neighbor_switch_counts)
    return metrics


def build_default_candidate_sweep_v1() -> tuple[ResearchCandidateSpecV1, ...]:
    """Documented research sweep — RESEARCH_CANDIDATE parameters only."""
    abs_ks = (0.5, 1.0, 2.0, 5.0)
    rel_ks = (0.005, 0.01, 0.02, 0.05)
    vol_ks = (0.5, 1.0, 1.5, 2.0)
    specs: list[ResearchCandidateSpecV1] = []
    for k in abs_ks:
        specs.append(ResearchCandidateSpecV1(ResearchCandidateFamily.ABSOLUTE, k))
    for k in rel_ks:
        specs.append(ResearchCandidateSpecV1(ResearchCandidateFamily.RELATIVE, k))
    for k in vol_ks:
        specs.append(ResearchCandidateSpecV1(ResearchCandidateFamily.VOL_NORMALIZED, k))
    return tuple(specs)


def compute_stability_summary_v1(runs: Sequence[CandidateRunMetricsV1]) -> dict[str, Any]:
    """DERIVED cross-segment / cross-candidate dispersion metrics (no PnL)."""
    by_family: dict[str, list[CandidateRunMetricsV1]] = {}
    for run in runs:
        by_family.setdefault(run.candidate.family.value, []).append(run)
    summary: dict[str, Any] = {}
    for family, family_runs in by_family.items():
        freqs = [r.switch_frequency_per_bar for r in family_runs]
        seg_vectors = [
            list(r.segment_switch_counts.values()) for r in family_runs if r.segment_switch_counts
        ]
        summary[family] = {
            "run_count": len(family_runs),
            "switch_frequency_min": min(freqs) if freqs else None,
            "switch_frequency_max": max(freqs) if freqs else None,
            "switch_frequency_spread": (max(freqs) - min(freqs)) if freqs else None,
            "segment_count_dispersion_mean": _segment_dispersion_mean(seg_vectors),
            "fail_closed_steps_total": sum(r.fail_closed_steps for r in family_runs),
        }
    return summary


def _segment_dispersion_mean(seg_vectors: Sequence[Sequence[int]]) -> Optional[float]:
    if not seg_vectors:
        return None
    dispersions = []
    for vec in seg_vectors:
        if not vec:
            continue
        mean = sum(vec) / len(vec)
        dispersions.append(sum(abs(v - mean) for v in vec) / len(vec))
    return sum(dispersions) / len(dispersions) if dispersions else None


def run_empirical_calibration_evidence_v1(
    *,
    repo_root: Path,
    dataset_loader: str = "pt1m_materializer_fixture",
    candidate_sweep: Sequence[ResearchCandidateSpecV1] | None = None,
) -> EmpiricalCalibrationEvidenceV1:
    if dataset_loader == "cap51_offline_fixture":
        identity, observations = load_cap51_offline_fixture_dataset_v1(repo_root=repo_root)
    elif dataset_loader == "pt1m_materializer_fixture":
        identity, observations = load_pt1m_bars_dataset_from_materializer_fixture_v1(
            repo_root=repo_root
        )
    else:
        raise ValueError(f"unknown_dataset_loader:{dataset_loader}")

    sweep = tuple(candidate_sweep or build_default_candidate_sweep_v1())
    runs: list[CandidateRunMetricsV1] = []
    switch_by_label: dict[str, int] = {}
    for spec in sweep:
        metrics = simulate_candidate_on_series_v1(
            dataset=identity,
            observations=observations,
            candidate=spec,
        )
        switch_by_label[spec.label()] = metrics.switch_count
        runs.append(metrics)

    for metrics in runs:
        neighbors: dict[str, float] = {}
        k = metrics.candidate.parameter_k
        fam = metrics.candidate.family
        for delta in (-0.001, 0.001):
            if fam is ResearchCandidateFamily.ABSOLUTE:
                nk = k + delta
            elif fam is ResearchCandidateFamily.RELATIVE:
                nk = k + delta
            else:
                nk = k + 0.1 * delta
            label = f"{fam.value}:k={nk}"
            if label in switch_by_label:
                neighbors[label] = float(switch_by_label[label])
        apply_neighbor_sensitivity_v1(metrics, neighbor_switch_counts=neighbors)

    stability = compute_stability_summary_v1(runs)
    payload_without_digest = {
        "dataset": identity.to_dict(),
        "runs": [r.to_dict() for r in runs],
        "stability_summary": stability,
    }
    digest = stable_digest(payload_without_digest)
    labels = {
        "metrics": LineageClass.OBSERVED.value,
        "candidate_parameters": LineageClass.RESEARCH_CANDIDATE.value,
        "stability_summary": LineageClass.DERIVED.value,
        "interpretation": "NONE_PERSISTED",
    }
    return EmpiricalCalibrationEvidenceV1(
        harness_version=HARNESS_VERSION,
        mechanical_core_version=MECHANICAL_CORE_VERSION,
        dataset=identity,
        candidate_sweep=sweep,
        runs=tuple(runs),
        stability_summary=stability,
        evidence_digest=digest,
        labels=labels,
    )


def factual_summary_lines_v1(evidence: EmpiricalCalibrationEvidenceV1) -> tuple[str, ...]:
    """Compact OBSERVED/DERIVED lines — no productive authority."""
    lines = [
        f"DATASET={evidence.dataset.dataset_id}",
        f"INSTRUMENT={evidence.dataset.instrument_id}",
        f"BAR_COUNT={evidence.dataset.bar_count}",
        f"EVIDENCE_DIGEST={evidence.evidence_digest}",
        f"MECHANICAL_CORE={evidence.mechanical_core_version}",
    ]
    for family in ResearchCandidateFamily:
        fr = [r for r in evidence.runs if r.candidate.family is family]
        if not fr:
            continue
        switches = [r.switch_count for r in fr]
        lines.append(
            f"OBSERVED family={family.value} switch_count_min={min(switches)} switch_count_max={max(switches)}"
        )
    return tuple(lines)


__all__ = [
    "HARNESS_VERSION",
    "HARNESS_OWNER",
    "RUNTIME_AUTHORITY",
    "PRODUCTIVE_D_T_FORMULA_SELECTED",
    "PRODUCTIVE_D_T_BINDING_PRESENT",
    "ResearchCandidateFamily",
    "LineageClass",
    "ResearchMarkObservationV1",
    "ResearchDatasetIdentityV1",
    "ResearchCandidateSpecV1",
    "CandidateRunMetricsV1",
    "EmpiricalCalibrationEvidenceV1",
    "compute_research_d_t_v1",
    "load_cap51_offline_fixture_dataset_v1",
    "load_pt1m_bars_dataset_from_materializer_fixture_v1",
    "simulate_candidate_on_series_v1",
    "run_empirical_calibration_evidence_v1",
    "factual_summary_lines_v1",
    "build_default_candidate_sweep_v1",
]
