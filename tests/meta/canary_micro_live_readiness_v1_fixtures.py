"""Fixtures for canary_micro_live_readiness_v1 tests."""

from __future__ import annotations

from pathlib import Path

from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import (
    build_autonomous_non_live_orchestration_plan_v1,
    default_autonomous_non_live_orchestration_plan_request,
    produce_autonomous_non_live_orchestration_plan_v1,
)
from src.meta.learning_loop.canary_micro_live_readiness_v1 import (
    CanaryMicroLiveReadinessRequest,
    CanaryReadinessInputRequest,
    build_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
    build_canary_micro_live_readiness_evidence_v1,
    default_canary_micro_live_readiness_request,
    default_canary_readiness_input_request,
    produce_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
    produce_canary_micro_live_readiness_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.meta.autonomous_non_live_orchestration_plan_v1_fixtures import (
    build_invalid_learning_source,
    produce_plan_fixture,
)


def build_valid_canary_input_request(**overrides: object) -> CanaryReadinessInputRequest:
    return default_canary_readiness_input_request(**overrides)


def build_valid_readiness_request(**overrides: object) -> CanaryMicroLiveReadinessRequest:
    canary_input = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    return default_canary_micro_live_readiness_request(canary_input, **overrides)


def minimal_invalid_digest() -> str:
    return compute_content_sha256({"invalid": True})


def produce_canary_input_fixture(tmp_path: Path, name: str = "canary_input_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(parents=True, exist_ok=True)
    out = root / name
    produce_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        request=default_canary_readiness_input_request(),
        output_dir=out,
    )
    return out


def produce_readiness_fixture(tmp_path: Path, name: str = "readiness_out") -> Path:
    canary_input = build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    root = tmp_path / "evidence_root"
    root.mkdir(parents=True, exist_ok=True)
    out = root / name
    produce_canary_micro_live_readiness_evidence_v1(
        request=default_canary_micro_live_readiness_request(canary_input),
        output_dir=out,
    )
    return out


def produce_full_step28_chain_fixtures(
    tmp_path: Path,
) -> tuple[Path, Path, Path]:
    plan = produce_plan_fixture(tmp_path, "chain_plan")
    canary_input = produce_canary_input_fixture(tmp_path, "chain_canary_input")
    readiness = produce_readiness_fixture(tmp_path, "chain_readiness")
    return plan, canary_input, readiness


def build_bitcoin_plan_source() -> dict:
    invalid_learning = build_invalid_learning_source()
    from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import (
        build_runtime_observation_to_orchestration_input_v1,
        default_runtime_observation_to_orchestration_input_request,
    )
    from src.meta.learning_loop.runtime_observation_feedback_v1 import (
        LEARNING_INPUT_CONTRACT_NAME,
    )

    orchestration_input = build_runtime_observation_to_orchestration_input_v1(
        default_runtime_observation_to_orchestration_input_request(
            invalid_learning,
            source_contract_name=LEARNING_INPUT_CONTRACT_NAME,
        )
    )
    return build_autonomous_non_live_orchestration_plan_v1(
        default_autonomous_non_live_orchestration_plan_request(orchestration_input)
    )


def build_not_ready_plan_source() -> dict:
    from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import (
        build_runtime_observation_to_orchestration_input_v1,
        default_runtime_observation_to_orchestration_input_request,
    )
    from src.meta.learning_loop.runtime_observation_feedback_v1 import (
        OBSERVATION_CONTRACT_NAME,
    )
    from tests.meta.autonomous_non_live_orchestration_plan_v1_fixtures import (
        build_incomplete_observation_source,
    )

    orchestration_input = build_runtime_observation_to_orchestration_input_v1(
        default_runtime_observation_to_orchestration_input_request(
            build_incomplete_observation_source(),
            source_contract_name=OBSERVATION_CONTRACT_NAME,
        )
    )
    return build_autonomous_non_live_orchestration_plan_v1(
        default_autonomous_non_live_orchestration_plan_request(orchestration_input)
    )
