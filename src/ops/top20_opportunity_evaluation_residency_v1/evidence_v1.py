"""Observability surfaces for residency scheduling (non-authoritative)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import (
    ResidencyMetricsV1,
    ResidencyStoreSnapshotV1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import load_metrics_v1


def build_residency_observability_report_v1(
    *,
    store: ResidencyStoreSnapshotV1,
    state_root: Path,
) -> dict[str, Any]:
    metrics = load_metrics_v1(state_root)
    pending = sum(1 for r in store.records if r.state == "ADMITTED_PENDING")
    active = sum(1 for r in store.records if r.state == "ACTIVE_RESIDENT")
    return {
        "active_residents": active,
        "capacity_rejected_total": metrics.capacity_rejected_total,
        "evaluation_observed_total": metrics.evaluation_observed_total,
        "expired_active_total": metrics.expired_active_total,
        "expired_pending_total": metrics.expired_pending_total,
        "pending_residents": pending,
        "queue_depth": pending,
        "scheduler_service_rate_hint": _service_rate_hint(metrics),
        "top20_turnover_hint": "observe_via_current_rank_observations",
        "ranking_cadence_hint": "observe_via_cap22_event_times",
    }


def _service_rate_hint(metrics: ResidencyMetricsV1) -> dict[str, Any]:
    samples = metrics.active_to_evaluation_observed_latency_samples
    if not samples:
        return {"samples": 0, "mean_seconds": None}
    mean = sum(samples) / len(samples)
    return {"samples": len(samples), "mean_seconds": mean}
