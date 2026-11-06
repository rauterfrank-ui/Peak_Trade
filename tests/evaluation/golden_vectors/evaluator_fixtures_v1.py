"""Fixtures for GVEF domain evaluator tests (BWP-3 through BWP-6)."""

from __future__ import annotations

from copy import deepcopy

from src.evaluation.golden_vectors.contracts.primitives import ReplayTraceV1
from src.evaluation.golden_vectors.contracts.validation import parse_domain_evaluation_context_v1
from src.evaluation.golden_vectors.evaluators.ptp_owners_v1 import (
    PTP_STAGE_ORDER,
    PTP_STAGE_OWNERS,
)
from tests.evaluation.golden_vectors.runner_fixtures_v1 import domain_context

_SHA = "a" * 64


def ptp_stage_entries(
    *,
    run_id: str = "550e8400-e29b-41d4-a716-446655440000",
    synthetic: bool = False,
    stages: tuple[str, ...] | None = None,
) -> list[dict]:
    order = stages or PTP_STAGE_ORDER
    entries: list[dict] = []
    for stage in order:
        entry: dict = {
            "kind": "ptp_stage",
            "run_id": run_id,
            "stage": stage,
            "owner": PTP_STAGE_OWNERS.get(stage, "unknown"),
        }
        if synthetic:
            entry["TEST_ONLY_SYNTHETIC"] = True
        entries.append(entry)
    return entries


def ru_entries(
    *,
    baseline: list[str],
    candidate: list[str],
    baseline_ordering: list[dict] | None = None,
    candidate_ordering: list[dict] | None = None,
    top_k_context: dict | None = None,
) -> list[dict]:
    base_entry: dict = {"kind": "ranking_universe", "label": "baseline", "membership": baseline}
    cand_entry: dict = {
        "kind": "ranking_universe",
        "label": "candidate",
        "membership": candidate,
    }
    if baseline_ordering is not None:
        base_entry["ordering"] = baseline_ordering
    if candidate_ordering is not None:
        cand_entry["ordering"] = candidate_ordering
    if top_k_context is not None:
        base_entry["top_k_context"] = top_k_context
        cand_entry["top_k_context"] = top_k_context
    return [base_entry, cand_entry]


def replay_trace(entries: list[dict]) -> dict:
    from src.evaluation.golden_vectors.contracts.serialization import sha256_hex

    return {
        "trace_schema_version": "1.0.0",
        "trace_digest": sha256_hex({"entries": entries}),
        "entries": entries,
    }


def ptp_context(*, synthetic: bool = True, stages: tuple[str, ...] | None = None):
    ctx = deepcopy(domain_context())
    entries = ptp_stage_entries(synthetic=synthetic, stages=stages)
    ctx["replay_trace"] = replay_trace(entries)
    return parse_domain_evaluation_context_v1(ctx)


def ru_context(*, baseline: list[str] | None = None, candidate: list[str] | None = None):
    ctx = deepcopy(domain_context())
    ctx["run_manifest"]["domain_evaluator_id"] = "ranking_universe_evaluator_v1"
    b = baseline or ["BTC-PERP", "ETH-PERP"]
    c = candidate or ["BTC-PERP", "SOL-PERP"]
    ctx["replay_trace"] = replay_trace(ru_entries(baseline=b, candidate=c))
    return parse_domain_evaluation_context_v1(ctx)


def parsed_replay(entries: list[dict]) -> ReplayTraceV1:
    return ReplayTraceV1.model_validate(replay_trace(entries))


def opt_entries(
    *,
    baseline: dict | None = None,
    candidate: dict | None = None,
) -> list[dict]:
    b = baseline or {"TEST_ONLY_SYNTHETIC": True, "alpha": "1", "beta": "2"}
    c = candidate or {"TEST_ONLY_SYNTHETIC": True, "alpha": "1", "beta": "3"}
    return [
        {"kind": "optimization_universe", "label": "baseline", "parameters": b},
        {"kind": "optimization_universe", "label": "candidate", "parameters": c},
    ]


def sl_entries(
    *,
    baseline: dict | None = None,
    candidate: dict | None = None,
) -> list[dict]:
    b = baseline or {"TEST_ONLY_SYNTHETIC": True, "model_id": "m1", "epoch": 1}
    c = candidate or {"TEST_ONLY_SYNTHETIC": True, "model_id": "m1", "epoch": 2}
    return [
        {"kind": "self_learning", "label": "baseline", "learning_artifact": b},
        {"kind": "self_learning", "label": "candidate", "learning_artifact": c},
    ]


def mi_entries(
    *,
    baseline: dict | None = None,
    candidate: dict | None = None,
) -> list[dict]:
    b = baseline or {
        "TEST_ONLY_SYNTHETIC": True,
        "freshness_token": "t0",
        "causality_proof_present": True,
    }
    c = candidate or {
        "TEST_ONLY_SYNTHETIC": True,
        "freshness_token": "t1",
        "causality_proof_present": True,
    }
    return [
        {"kind": "market_intelligence", "label": "baseline", "mi_context_bundle": b},
        {"kind": "market_intelligence", "label": "candidate", "mi_context_bundle": c},
    ]


def _ctx_for(domain_evaluator_id: str, entries: list[dict]):
    ctx = deepcopy(domain_context())
    ctx["run_manifest"]["domain_evaluator_id"] = domain_evaluator_id
    ctx["run_manifest"]["fan_out_evaluation_class"] = "LOCAL_EVALUATION"
    ctx["replay_trace"] = replay_trace(entries)
    return parse_domain_evaluation_context_v1(ctx)


def opt_context(**kwargs):
    return _ctx_for("optimization_universe_evaluator_v1", opt_entries(**kwargs))


def sl_context(**kwargs):
    return _ctx_for("self_learning_evaluator_v1", sl_entries(**kwargs))


def mi_context(**kwargs):
    return _ctx_for("market_intelligence_evaluator_v1", mi_entries(**kwargs))
