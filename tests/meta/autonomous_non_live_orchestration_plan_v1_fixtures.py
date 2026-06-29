"""Fixtures for autonomous_non_live_orchestration_plan_v1 tests."""

from __future__ import annotations

from pathlib import Path

from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import (
    AutonomousNonLiveOrchestrationPlanRequest,
    RuntimeObservationToOrchestrationInputRequest,
    build_autonomous_non_live_orchestration_plan_v1,
    build_runtime_observation_to_orchestration_input_v1,
    default_autonomous_non_live_orchestration_plan_request,
    default_runtime_observation_to_orchestration_input_request,
    produce_autonomous_non_live_orchestration_plan_v1,
    produce_runtime_observation_to_orchestration_input_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    LEARNING_INPUT_CONTRACT_NAME,
    OBSERVATION_CONTRACT_NAME,
    build_runtime_observation_bundle_v1,
    build_runtime_to_learning_input_v1,
    default_runtime_observation_bundle_input,
    produce_runtime_observation_bundle_v1,
    produce_runtime_to_learning_input_v1,
)
from tests.meta.runtime_observation_feedback_v1_fixtures import (
    build_valid_learning_request,
    build_valid_observation_input,
    missing_binding,
    produce_learning_input_fixture,
    produce_observation_bundle_fixture,
)


def build_valid_orchestration_input_request(
    **overrides: object,
) -> RuntimeObservationToOrchestrationInputRequest:
    return default_runtime_observation_to_orchestration_input_request(**overrides)


def build_valid_plan_request(**overrides: object) -> AutonomousNonLiveOrchestrationPlanRequest:
    orchestration_input = build_runtime_observation_to_orchestration_input_v1()
    return default_autonomous_non_live_orchestration_plan_request(orchestration_input, **overrides)


def minimal_invalid_digest() -> str:
    return compute_content_sha256({"invalid": True})


def produce_orchestration_input_fixture(
    tmp_path: Path, name: str = "orchestration_input_out"
) -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(parents=True, exist_ok=True)
    out = root / name
    produce_runtime_observation_to_orchestration_input_v1(
        request=default_runtime_observation_to_orchestration_input_request(),
        output_dir=out,
    )
    return out


def produce_plan_fixture(tmp_path: Path, name: str = "plan_out") -> Path:
    orchestration_input = build_runtime_observation_to_orchestration_input_v1()
    root = tmp_path / "evidence_root"
    root.mkdir(parents=True, exist_ok=True)
    out = root / name
    produce_autonomous_non_live_orchestration_plan_v1(
        request=default_autonomous_non_live_orchestration_plan_request(orchestration_input),
        output_dir=out,
    )
    return out


def produce_full_step27_chain_fixtures(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path]:
    observation = produce_observation_bundle_fixture(tmp_path, "chain_observation")
    learning = produce_learning_input_fixture(tmp_path, "chain_learning")
    orchestration = produce_orchestration_input_fixture(tmp_path, "chain_orchestration_input")
    plan = produce_plan_fixture(tmp_path, "chain_plan")
    return observation, learning, orchestration, plan


def build_incomplete_observation_source() -> dict:
    return build_runtime_observation_bundle_v1(
        build_valid_observation_input(
            order_evidence=missing_binding(),
            fill_evidence=missing_binding(),
            position_evidence=missing_binding(),
            pnl_evidence=missing_binding(),
            reconciliation_event=missing_binding(),
        )
    )


def build_invalid_learning_source() -> dict:
    return build_runtime_to_learning_input_v1(
        build_valid_learning_request(
            source_observation_status="INVALID",
            source_observation_body=build_runtime_observation_bundle_v1(
                build_valid_observation_input(instrument="BTC-USDT-SWAP")
            ),
        )
    )


def build_orchestration_request_from_observation_bundle(tmp_path: Path) -> Path:
    out = tmp_path / "evidence_root" / "obs_for_orch"
    out.parent.mkdir(parents=True, exist_ok=True)
    produce_runtime_observation_bundle_v1(
        request=default_runtime_observation_bundle_input(),
        output_dir=out,
    )
    return out


def build_orchestration_request_from_learning_bundle(tmp_path: Path) -> Path:
    return produce_learning_input_fixture(tmp_path, "learning_for_orch")
