# src/trading/master_v2/dynamic_scope_governed_real_market_evidence_v1.py
"""
Governed REAL historical market evidence for Dynamic Scope research v1.

AUTHORITY=NONE — binds sealed OKX PT1M observation packs and runs the existing
empirical calibration harness (execute_naked_mechanical_step_v1 via research v1).

Does not define productive D_t. Does not mutate mechanical core or research harness.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
    MATERIALIZER_OWNER,
    MATERIALIZER_VERSION,
)
from trading.master_v2.dynamic_scope_empirical_calibration_research_v1 import (
    HARNESS_VERSION,
    LineageClass,
    PRODUCTIVE_D_T_BINDING_PRESENT,
    PRODUCTIVE_D_T_FORMULA_SELECTED,
    RUNTIME_AUTHORITY,
    ResearchCandidateFamily,
    ResearchCandidateSpecV1,
    ResearchDatasetIdentityV1,
    ResearchMarkObservationV1,
    apply_neighbor_sensitivity_v1,
    attach_sigma_from_materializer_on_series_v1,
    build_default_candidate_sweep_v1,
    compute_stability_summary_v1,
    simulate_candidate_on_series_v1,
    stable_digest,
    stable_sha256_file,
)
from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import MECHANICAL_CORE_VERSION

EVIDENCE_OWNER = "trading.master_v2.dynamic_scope_governed_real_market_evidence_v1"
EVIDENCE_VERSION = "dynamic_scope_governed_real_market_evidence/v1"
PRICE_FIELD = "mark_price"

DEFAULT_BINDING_ID = "okx_surface_b_eth_usdt_swap_pt1m_tip1785934680_v1"

GOVERNED_REAL_MARKET_DATASET_BINDINGS_V1: dict[str, dict[str, str]] = {
    DEFAULT_BINDING_ID: {
        "observation_pack_rel": (
            "docs/ops/artifacts/productive_pure_stack_stage2_surface_b_owner_sta_"
            "raw_input_pack_materialization_v1/observation_pack.json"
        ),
        "materialization_proof_rel": (
            "docs/ops/artifacts/productive_pure_stack_stage2_surface_b_owner_sta_"
            "raw_input_pack_materialization_v1/materialization_proof.json"
        ),
        "venue": "okx",
        "source_class": "OBSERVED_OKX_PUBLIC_PT1M_SEALED_OBSERVATION_PACK",
    },
}


class GovernedRealMarketEvidenceError(ValueError):
    """Fail-closed governed REAL market evidence error."""


@dataclass(frozen=True)
class GovernedRealMarketDatasetLineageV1:
    binding_id: str
    dataset_id: str
    dataset_digest: str
    source_path: str
    source_content_sha256: str
    materialization_proof_path: str
    materialization_proof_sha256: str
    venue: str
    instrument_id: str
    venue_instrument_id: str
    time_range_start: str
    time_range_end: str
    observation_count: int
    sampling_spec: str
    price_field: str
    volatility_definition: str
    volatility_lineage: str
    volatility_valid_observations: int
    lineage_labels: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "dataset_id": self.dataset_id,
            "dataset_digest": self.dataset_digest,
            "source_path": self.source_path,
            "source_content_sha256": self.source_content_sha256,
            "materialization_proof_path": self.materialization_proof_path,
            "materialization_proof_sha256": self.materialization_proof_sha256,
            "venue": self.venue,
            "instrument_id": self.instrument_id,
            "venue_instrument_id": self.venue_instrument_id,
            "time_range_start": self.time_range_start,
            "time_range_end": self.time_range_end,
            "observation_count": self.observation_count,
            "sampling_spec": self.sampling_spec,
            "price_field": self.price_field,
            "volatility_definition": self.volatility_definition,
            "volatility_lineage": self.volatility_lineage,
            "volatility_valid_observations": self.volatility_valid_observations,
            "lineage_labels": dict(self.lineage_labels),
        }


@dataclass(frozen=True)
class GovernedRealMarketEvidenceV1:
    evidence_version: str
    harness_version: str
    mechanical_core_version: str
    runtime_authority: str
    productive_d_t_formula_selected: bool
    productive_d_t_binding_present: bool
    lineage: GovernedRealMarketDatasetLineageV1
    parameter_grid: tuple[dict[str, Any], ...]
    calibration_runs: tuple[dict[str, Any], ...]
    stability_summary: dict[str, Any]
    family_summaries: dict[str, Any]
    factual_comparison: dict[str, Any]
    evidence_digest: str
    labels: dict[str, str]
    interpretation: str
    unresolved: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_version": self.evidence_version,
            "harness_version": self.harness_version,
            "mechanical_core_version": self.mechanical_core_version,
            "runtime_authority": self.runtime_authority,
            "productive_d_t_formula_selected": self.productive_d_t_formula_selected,
            "productive_d_t_binding_present": self.productive_d_t_binding_present,
            "lineage": self.lineage.to_dict(),
            "parameter_grid": list(self.parameter_grid),
            "calibration_runs": list(self.calibration_runs),
            "stability_summary": self.stability_summary,
            "family_summaries": self.family_summaries,
            "factual_comparison": self.factual_comparison,
            "evidence_digest": self.evidence_digest,
            "labels": dict(self.labels),
            "interpretation": self.interpretation,
            "unresolved": list(self.unresolved),
        }


def _assert_contiguous_pt1m(bars: Sequence[Mapping[str, Any]]) -> None:
    if len(bars) <= 1:
        return
    times = [int(b["event_time_epoch_s"]) for b in bars]
    for prev, cur in zip(times[:-1], times[1:], strict=True):
        if cur - prev != 60:
            raise GovernedRealMarketEvidenceError(f"non_contiguous_pt1m:gap_{cur - prev}s_at_{cur}")


def _bars_mark_digest(bars: Sequence[Mapping[str, Any]]) -> str:
    canonical = [
        {
            "event_time_epoch_s": int(b["event_time_epoch_s"]),
            "mark_price": float(b["mark_price"]),
            "finalized": bool(b.get("finalized", False)),
        }
        for b in bars
    ]
    return stable_digest({"bars": canonical})


def load_governed_real_market_observation_series_v1(
    *,
    repo_root: Path,
    binding_id: str = DEFAULT_BINDING_ID,
) -> tuple[
    GovernedRealMarketDatasetLineageV1, ResearchDatasetIdentityV1, list[ResearchMarkObservationV1]
]:
    """Load OBSERVED REAL PT1M marks; DERIVED sigma via canonical materializer path."""
    binding = GOVERNED_REAL_MARKET_DATASET_BINDINGS_V1.get(binding_id)
    if binding is None:
        raise GovernedRealMarketEvidenceError(f"unknown_binding:{binding_id}")

    pack_rel = Path(binding["observation_pack_rel"])
    proof_rel = Path(binding["materialization_proof_rel"])
    pack_path = repo_root / pack_rel
    proof_path = repo_root / proof_rel
    if not pack_path.is_file() or not proof_path.is_file():
        raise GovernedRealMarketEvidenceError("governed_real_market_artifact_missing")

    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    bars_raw = payload.get("bars")
    if not isinstance(bars_raw, list) or not bars_raw:
        raise GovernedRealMarketEvidenceError("observation_pack_empty")

    bars = sorted(bars_raw, key=lambda row: int(row["event_time_epoch_s"]))
    _assert_contiguous_pt1m(bars)

    instrument_binding = payload.get("instrument_binding") or {}
    provenance = payload.get("provenance") or {}
    dataset_id = str(provenance.get("dataset_id") or proof.get("dataset_id") or "")
    if not dataset_id:
        raise GovernedRealMarketEvidenceError("dataset_id_missing")

    for i, bar in enumerate(bars):
        if not bar.get("finalized"):
            raise GovernedRealMarketEvidenceError(f"non_finalized_bar_index_{i}")
        mark = bar.get("mark_price")
        if mark is None or not math.isfinite(float(mark)) or float(mark) <= 0.0:
            raise GovernedRealMarketEvidenceError(f"invalid_mark_price_index_{i}")

    observations: list[ResearchMarkObservationV1] = []
    for bar in bars:
        ts = int(bar["event_time_epoch_s"])
        observations.append(
            ResearchMarkObservationV1(
                timestamp_iso=pd.Timestamp(ts, unit="s", tz="UTC").isoformat(),
                mark_price=float(bar["mark_price"]),
            )
        )

    observations = attach_sigma_from_materializer_on_series_v1(observations)
    vol_valid = sum(
        1
        for o in observations
        if o.sigma_t is not None and math.isfinite(o.sigma_t) and o.sigma_t > 0.0
    )
    if vol_valid < 1:
        raise GovernedRealMarketEvidenceError("volatility_valid_observations_zero")

    pack_sha = stable_sha256_file(pack_path)
    proof_sha = stable_sha256_file(proof_path)
    dataset_digest = _bars_mark_digest(bars)

    canonical_instrument = str(
        instrument_binding.get("canonical_instrument_id")
        or provenance.get("instrument_id")
        or "UNKNOWN"
    )
    venue_instrument = str(instrument_binding.get("venue_instrument_id") or "")

    lineage = GovernedRealMarketDatasetLineageV1(
        binding_id=binding_id,
        dataset_id=dataset_id,
        dataset_digest=dataset_digest,
        source_path=str(pack_rel),
        source_content_sha256=pack_sha,
        materialization_proof_path=str(proof_rel),
        materialization_proof_sha256=proof_sha,
        venue=str(binding.get("venue") or provenance.get("venue") or "okx"),
        instrument_id=canonical_instrument,
        venue_instrument_id=venue_instrument,
        time_range_start=observations[0].timestamp_iso,
        time_range_end=observations[-1].timestamp_iso,
        observation_count=len(observations),
        sampling_spec="PT1M_contiguous_finalized_mark_price_venue_native_okx_public",
        price_field=PRICE_FIELD,
        volatility_definition="ROLLING_STD_LOG_RETURN_MARK_PRICE_60B",
        volatility_lineage=f"{MATERIALIZER_VERSION}/{MATERIALIZER_OWNER}",
        volatility_valid_observations=vol_valid,
        lineage_labels={
            "market_observations": LineageClass.OBSERVED.value,
            "volatility_sigma_t": LineageClass.DERIVED.value,
            "calibration_metrics": LineageClass.DERIVED.value,
            "candidate_d_t": LineageClass.RESEARCH_CANDIDATE.value,
        },
    )

    identity = ResearchDatasetIdentityV1(
        dataset_id=dataset_id,
        instrument_id=canonical_instrument,
        source_path=str(pack_rel),
        source_content_sha256=pack_sha,
        lineage_class=LineageClass.OBSERVED,
        sampling_spec=lineage.sampling_spec,
        volatility_definition=lineage.volatility_definition,
        volatility_lineage=lineage.volatility_lineage,
        bar_count=len(observations),
        time_range_start=lineage.time_range_start,
        time_range_end=lineage.time_range_end,
    )
    return lineage, identity, observations


def _run_harness_orchestration_v1(
    *,
    identity: ResearchDatasetIdentityV1,
    observations: Sequence[ResearchMarkObservationV1],
    candidate_sweep: Sequence[ResearchCandidateSpecV1],
) -> tuple[list[Any], dict[str, Any]]:
    """Same orchestration as run_empirical_calibration_evidence_v1 (research owner unchanged)."""
    runs = []
    switch_by_label: dict[str, int] = {}
    for spec in candidate_sweep:
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
    return runs, stability


def _family_summaries(runs: Sequence[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for family in ResearchCandidateFamily:
        fr = [r for r in runs if r.candidate.family is family]
        if not fr:
            continue
        out[family.value] = {
            "parameter_grid": [r.candidate.parameter_k for r in fr],
            "switch_metrics": {
                "switch_count_min": min(r.switch_count for r in fr),
                "switch_count_max": max(r.switch_count for r in fr),
                "switch_frequency_spread": max(r.switch_frequency_per_bar for r in fr)
                - min(r.switch_frequency_per_bar for r in fr),
                "whipsaw_count_total": sum(r.whipsaw_count for r in fr),
                "fail_closed_steps_total": sum(r.fail_closed_steps for r in fr),
            },
            "whipsaw_metrics": {
                "whipsaw_rate_mean": sum(r.whipsaw_rate for r in fr) / len(fr),
            },
            "segment_results": [r.segment_switch_counts for r in fr],
            "volatility_regime_results": [r.vol_quantile_switch_counts for r in fr],
            "sensitivity_results": [r.neighbor_sensitivity for r in fr],
        }
    return out


def _switch_scale_samples(runs: Sequence[Any]) -> dict[str, list[float]]:
    """DERIVED scale ratios at switches (factual samples, not authority)."""
    samples: dict[str, list[float]] = {
        "absolute_d_t": [],
        "d_over_m": [],
        "d_over_sigma_m": [],
    }
    for run in runs:
        fam = run.candidate.family.value
        for event in run.switch_events:
            if event.m_t > 0:
                samples["d_over_m"].append(event.d_t / event.m_t)
            if event.sigma_t and event.sigma_t > 0 and event.m_t > 0:
                samples["d_over_sigma_m"].append(event.d_t / (event.sigma_t * event.m_t))
            if fam == "absolute":
                samples["absolute_d_t"].append(event.d_t)
    return samples


def _dispersion(values: Sequence[float]) -> Optional[float]:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    return sum(abs(v - mean) for v in values) / len(values)


def build_factual_comparison_v1(runs: Sequence[Any]) -> dict[str, Any]:
    """INTERPRETATION-free numeric comparison across families at switch events."""
    by_family: dict[str, Any] = {}
    for family in ResearchCandidateFamily:
        fr = [r for r in runs if r.candidate.family is family]
        if not fr:
            continue
        scales = _switch_scale_samples(fr)
        by_family[family.value] = {
            "switch_event_count": sum(len(r.switch_events) for r in fr),
            "mean_abs_d_t_at_switch": (
                sum(scales["absolute_d_t"]) / len(scales["absolute_d_t"])
                if scales["absolute_d_t"]
                else None
            ),
            "d_over_m_mean_abs_deviation": _dispersion(scales["d_over_m"]),
            "d_over_sigma_m_mean_abs_deviation": _dispersion(scales["d_over_sigma_m"]),
        }
    return {
        "families": by_family,
        "label": LineageClass.DERIVED.value,
        "note": "Lower dispersion is not declared winner; research-only comparison.",
    }


def run_governed_real_market_evidence_v1(
    *,
    repo_root: Path,
    binding_id: str = DEFAULT_BINDING_ID,
    candidate_sweep: Sequence[ResearchCandidateSpecV1] | None = None,
) -> GovernedRealMarketEvidenceV1:
    lineage, identity, observations = load_governed_real_market_observation_series_v1(
        repo_root=repo_root,
        binding_id=binding_id,
    )
    sweep = tuple(candidate_sweep or build_default_candidate_sweep_v1())
    runs, stability = _run_harness_orchestration_v1(
        identity=identity,
        observations=observations,
        candidate_sweep=sweep,
    )
    family_summaries = _family_summaries(runs)
    factual_comparison = build_factual_comparison_v1(runs)

    parameter_grid = tuple({"family": s.family.value, "parameter_k": s.parameter_k} for s in sweep)
    calibration_runs = tuple(r.to_dict() for r in runs)

    payload_without_digest = {
        "lineage": lineage.to_dict(),
        "parameter_grid": list(parameter_grid),
        "calibration_runs": list(calibration_runs),
        "stability_summary": stability,
        "family_summaries": family_summaries,
        "factual_comparison": factual_comparison,
    }
    digest = stable_digest(payload_without_digest)

    interpretation = (
        "INTERPRETATION: On the bound OKX ETH-USDT-SWAP PT1M REAL series, "
        "candidate families exhibit different switch/whipsaw profiles across the "
        "documented k-grid. No family is promoted to productive D_t authority."
    )
    unresolved = (
        "Single-instrument ~5h window; not multi-year; no walk-forward split executed.",
        "Additional REAL futures require separate governed bindings.",
        "Relative-family scale stability requires cross-check on longer panels.",
    )

    labels = {
        "market_data": LineageClass.OBSERVED.value,
        "metrics": LineageClass.DERIVED.value,
        "candidate_parameters": LineageClass.RESEARCH_CANDIDATE.value,
        "factual_comparison": LineageClass.DERIVED.value,
        "interpretation_block": "INTERPRETATION_NON_AUTHORITY",
    }

    return GovernedRealMarketEvidenceV1(
        evidence_version=EVIDENCE_VERSION,
        harness_version=HARNESS_VERSION,
        mechanical_core_version=MECHANICAL_CORE_VERSION,
        runtime_authority=RUNTIME_AUTHORITY,
        productive_d_t_formula_selected=PRODUCTIVE_D_T_FORMULA_SELECTED,
        productive_d_t_binding_present=PRODUCTIVE_D_T_BINDING_PRESENT,
        lineage=lineage,
        parameter_grid=parameter_grid,
        calibration_runs=calibration_runs,
        stability_summary=stability,
        family_summaries=family_summaries,
        factual_comparison=factual_comparison,
        evidence_digest=digest,
        labels=labels,
        interpretation=interpretation,
        unresolved=unresolved,
    )


def default_evidence_output_dir_v1(repo_root: Path) -> Path:
    return repo_root / "docs/evidence/dynamic_scope_governed_real_market_evidence_v1"


def write_governed_real_market_evidence_artifacts_v1(
    evidence: GovernedRealMarketEvidenceV1,
    *,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    full_path = output_dir / "governed_real_market_calibration_evidence_v1.json"
    summary_path = output_dir / "SUMMARY.json"
    full_path.write_text(
        json.dumps(evidence.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "DATASET_ID": evidence.lineage.dataset_id,
        "DATASET_DIGEST": evidence.lineage.dataset_digest,
        "SOURCE": evidence.lineage.source_path,
        "VENUE": evidence.lineage.venue,
        "INSTRUMENT": evidence.lineage.instrument_id,
        "START": evidence.lineage.time_range_start,
        "END": evidence.lineage.time_range_end,
        "OBSERVATION_COUNT": evidence.lineage.observation_count,
        "SAMPLING_SPEC": evidence.lineage.sampling_spec,
        "PRICE_FIELD": evidence.lineage.price_field,
        "VOLATILITY_DEFINITION": evidence.lineage.volatility_definition,
        "VOLATILITY_VALID_OBSERVATIONS": evidence.lineage.volatility_valid_observations,
        "EVIDENCE_DIGEST": evidence.evidence_digest,
        "RUNTIME_AUTHORITY": evidence.runtime_authority,
        "labels": evidence.labels,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"full": full_path, "summary": summary_path}


__all__ = [
    "EVIDENCE_OWNER",
    "EVIDENCE_VERSION",
    "DEFAULT_BINDING_ID",
    "GOVERNED_REAL_MARKET_DATASET_BINDINGS_V1",
    "GovernedRealMarketEvidenceError",
    "GovernedRealMarketDatasetLineageV1",
    "GovernedRealMarketEvidenceV1",
    "load_governed_real_market_observation_series_v1",
    "run_governed_real_market_evidence_v1",
    "write_governed_real_market_evidence_artifacts_v1",
    "default_evidence_output_dir_v1",
    "build_factual_comparison_v1",
]
