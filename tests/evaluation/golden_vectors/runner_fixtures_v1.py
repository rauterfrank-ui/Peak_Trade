"""Shared deterministic fixtures for GVEF runner tests."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.validation import (
    parse_domain_evaluation_context_v1,
    parse_run_manifest_v1,
)

_SHA = "a" * 64
_SHA_B = "b" * 64
_GIT = "e1c884fcb6e105864073d049617bbed57811ecf9"
_TS = "2026-10-04T09:00:00Z"
_TS2 = "2026-10-04T10:00:00Z"


def provenance() -> dict:
    return {"source": "fixture", "ref": "tests/evaluation/golden_vectors"}


def protected_digests() -> dict:
    return {
        "ranking_universe": {"digest_hex": _SHA, "schema_version": "1.0.0"},
        "selection": {"digest_hex": _SHA_B, "schema_version": "1.0.0"},
    }


def run_manifest(*, created_at_utc: str = _TS) -> dict:
    return {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "experiment_id": "exp-gvef-bwp2",
        "baseline_sha": _GIT,
        "candidate_sha": _GIT,
        "domain_evaluator_id": "productive_trading_path_evaluator_v1",
        "corpus_manifest_ref": "corpus/fixture/v1",
        "constraint_matrix_version": "1.5.0",
        "constraint_matrix_digest": _SHA,
        "seed_set_digest": _SHA,
        "fan_out_evaluation_class": "LOCAL_EVALUATION",
        "created_at_utc": created_at_utc,
    }


def domain_context(*, created_at_utc: str = _TS) -> dict:
    return {
        "run_manifest": run_manifest(created_at_utc=created_at_utc),
        "baseline_identity": {"artifact_ref": "baseline", "digest": _SHA},
        "candidate_identity": {"artifact_ref": "candidate", "digest": _SHA_B},
        "corpus_identity": {
            "corpus_version": "1.0.0",
            "corpus_digest": _SHA,
            "vector_ids": ["vec-001"],
            "metric_schema_version": "1.0.0",
            "seed_set": [42],
            "provenance": provenance(),
        },
        "config_identity": {"config_path": "config/fixture.json", "config_digest": _SHA},
        "data_identity": {"data_manifest_id": "data-1", "data_digest": _SHA},
        "seed_identity": {"seeds": [42], "seed_set_digest": _SHA},
        "constraint_identity": {
            "matrix_version": "1.5.0",
            "matrix_digest": _SHA,
            "baseline_sha": _GIT,
            "rows": [
                {
                    "SIGNAL_EDGE": "RANKING_UNIVERSE->SELECTION",
                    "DOMAIN": "RANKING_UNIVERSE",
                    "PRODUCER": "Cap2.2",
                    "CONSUMER": "Cap2.3",
                    "CONTRACT": "handoff",
                    "ALLOWED_DIRECTION": "handoff_to_cap23_only",
                    "FORBIDDEN_DIRECTION": "gvef_to_selection_command",
                    "AUTHORITY_OWNER": "Cap2.3",
                    "REQUIRED_CURRENT_VERDICT": "PROVEN_CURRENT",
                    "PRODUCTIVE_REACHABILITY": "PROVEN_CURRENT",
                    "FAILURE_ACTION": "AUTHORITY_FAILURE",
                    "EVIDENCE_PROVENANCE": "tests",
                }
            ],
        },
        "protected_digest_baseline": protected_digests(),
        "replay_trace": {
            "trace_schema_version": "1.0.0",
            "trace_digest": _SHA,
            "entries": [],
        },
    }


def parsed_context(*, created_at_utc: str = _TS):
    return parse_domain_evaluation_context_v1(domain_context(created_at_utc=created_at_utc))


def parsed_run(*, created_at_utc: str = _TS):
    return parse_run_manifest_v1(run_manifest(created_at_utc=created_at_utc))
