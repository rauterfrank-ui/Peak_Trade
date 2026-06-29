"""Fixtures for runtime_observation_feedback_v1 tests."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    EvidenceFieldBinding,
    RuntimeObservationBundleInput,
    RuntimePerformanceComparisonInputRequest,
    RuntimeToLearningInputRequest,
    _FIELD_NOT_AVAILABLE,
    build_runtime_observation_bundle_v1,
    build_runtime_performance_comparison_input_v1,
    build_runtime_to_learning_input_v1,
    default_runtime_observation_bundle_input,
    default_runtime_performance_comparison_input_request,
    default_runtime_to_learning_input_request,
    produce_runtime_observation_bundle_v1,
    produce_runtime_performance_comparison_input_v1,
    produce_runtime_to_learning_input_v1,
)


def build_valid_observation_input(**overrides: object) -> RuntimeObservationBundleInput:
    return default_runtime_observation_bundle_input(**overrides)


def build_valid_learning_request(**overrides: object) -> RuntimeToLearningInputRequest:
    observation = build_runtime_observation_bundle_v1()
    return default_runtime_to_learning_input_request(observation, **overrides)


def build_valid_comparison_request(
    **overrides: object,
) -> RuntimePerformanceComparisonInputRequest:
    learning = build_runtime_to_learning_input_v1()
    return default_runtime_performance_comparison_input_request(learning, **overrides)


def minimal_invalid_digest() -> str:
    return compute_content_sha256({"invalid": True})


def missing_binding() -> EvidenceFieldBinding:
    return EvidenceFieldBinding("", "", _FIELD_NOT_AVAILABLE)


def produce_source_evidence_bundle(tmp_path: Path, name: str = "source_evidence") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    bundle = root / name
    bundle.mkdir()
    payload = {"fixture": "source_evidence", "market_type": "FUTURES"}
    (bundle / "source_evidence.json").write_text(
        __import__("json").dumps(payload, sort_keys=True),
        encoding="utf-8",
    )
    write_manifest_sha256(bundle)
    return bundle


def produce_observation_bundle_fixture(tmp_path: Path, name: str = "observation_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(parents=True, exist_ok=True)
    out = root / name
    produce_runtime_observation_bundle_v1(
        request=default_runtime_observation_bundle_input(),
        output_dir=out,
    )
    return out


def produce_learning_input_fixture(tmp_path: Path, name: str = "learning_out") -> Path:
    observation = build_runtime_observation_bundle_v1()
    root = tmp_path / "evidence_root"
    root.mkdir(parents=True, exist_ok=True)
    out = root / name
    produce_runtime_to_learning_input_v1(
        request=default_runtime_to_learning_input_request(observation),
        output_dir=out,
    )
    return out


def produce_comparison_input_fixture(tmp_path: Path, name: str = "comparison_out") -> Path:
    learning = build_runtime_to_learning_input_v1()
    root = tmp_path / "evidence_root"
    root.mkdir(parents=True, exist_ok=True)
    out = root / name
    produce_runtime_performance_comparison_input_v1(
        request=default_runtime_performance_comparison_input_request(learning),
        output_dir=out,
    )
    return out


def produce_full_chain_fixtures(tmp_path: Path) -> tuple[Path, Path, Path]:
    obs = produce_observation_bundle_fixture(tmp_path, "chain_observation")
    learning = produce_learning_input_fixture(tmp_path, "chain_learning")
    comparison = produce_comparison_input_fixture(tmp_path, "chain_comparison")
    return obs, learning, comparison
