"""Contract tests for autonomous_non_live_orchestration_plan_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.autonomous_non_live_orchestration_plan_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import (
    AUTONOMOUS_NON_LIVE_ORCHESTRATION_AUTHORITY_INVARIANTS,
    CANONICAL_STAGE_SEQUENCE,
    ORCHESTRATION_INPUT_ARTIFACT_REL,
    PLAN_ARTIFACT_REL,
    AutonomousNonLiveOrchestrationError,
    build_autonomous_non_live_orchestration_plan_v1,
    build_orchestration_input_request_from_learning_input_bundle,
    build_orchestration_input_request_from_observation_bundle,
    build_plan_request_from_orchestration_input_bundle,
    build_runtime_observation_to_orchestration_input_v1,
    default_autonomous_non_live_orchestration_plan_request,
    default_runtime_observation_to_orchestration_input_request,
    evaluate_autonomous_non_live_orchestration_plan_v1,
    evaluate_runtime_observation_to_orchestration_input_v1,
    produce_autonomous_non_live_orchestration_plan_v1,
    produce_runtime_observation_to_orchestration_input_v1,
    reverify_autonomous_non_live_orchestration_plan_v1,
    reverify_runtime_observation_to_orchestration_input_v1,
    serialize_autonomous_non_live_orchestration_plan_v1,
    serialize_runtime_observation_to_orchestration_input_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    LEARNING_INPUT_CONTRACT_NAME,
    OBSERVATION_CONTRACT_NAME,
)
from tests.meta.autonomous_non_live_orchestration_plan_v1_fixtures import (
    build_incomplete_observation_source,
    build_invalid_learning_source,
    build_orchestration_request_from_learning_bundle,
    build_orchestration_request_from_observation_bundle,
    build_valid_orchestration_input_request,
    build_valid_plan_request,
    minimal_invalid_digest,
    produce_full_step27_chain_fixtures,
    produce_orchestration_input_fixture,
    produce_plan_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str) -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


_STAGE_EXEC_FLAGS = (
    "execution_allowed",
    "activation_allowed",
    "scheduler_allowed",
    "orders_allowed",
)


# --- Contract A: runtime_observation_to_orchestration_input_v1 ---


def test_orchestration_input_happy_path() -> None:
    contract = build_runtime_observation_to_orchestration_input_v1()
    assert contract["orchestration_input_status"] == "READY"
    assert contract["offline_projection_only"] is True
    assert contract["orchestration_authorized"] is False
    assert contract["runtime_authorized"] is False
    assert contract["scheduler_authorized"] is False
    assert contract["shadow_authorized"] is False
    assert contract["paper_authorized"] is False
    assert contract["testnet_authorized"] is False
    assert contract["live_authorized"] is False


def test_orchestration_input_deterministic_repeat() -> None:
    request = build_valid_orchestration_input_request()
    assert build_runtime_observation_to_orchestration_input_v1(
        request
    ) == build_runtime_observation_to_orchestration_input_v1(request)


def test_orchestration_input_canonical_json_stability() -> None:
    contract = build_runtime_observation_to_orchestration_input_v1()
    assert serialize_runtime_observation_to_orchestration_input_v1(
        contract
    ) == deterministic_json_dumps(contract)


def test_orchestration_input_producer_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "orch_input_out")
    produce_runtime_observation_to_orchestration_input_v1(
        request=default_runtime_observation_to_orchestration_input_request(),
        output_dir=out,
    )
    verified = reverify_runtime_observation_to_orchestration_input_v1(output_dir=out)
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["orchestration_input_status"] == "READY"


def test_orchestration_input_from_observation_bundle(tmp_path: Path) -> None:
    bundle = build_orchestration_request_from_observation_bundle(tmp_path)
    request = build_orchestration_input_request_from_observation_bundle(bundle)
    contract = build_runtime_observation_to_orchestration_input_v1(request)
    assert contract["source_contract_name"] == OBSERVATION_CONTRACT_NAME
    assert contract["orchestration_input_status"] == "READY"


def test_orchestration_input_from_learning_bundle(tmp_path: Path) -> None:
    bundle = build_orchestration_request_from_learning_bundle(tmp_path)
    request = build_orchestration_input_request_from_learning_input_bundle(bundle)
    contract = build_runtime_observation_to_orchestration_input_v1(request)
    assert contract["source_contract_name"] == LEARNING_INPUT_CONTRACT_NAME
    assert contract["orchestration_input_status"] == "READY"


def test_orchestration_input_rejects_incomplete_observation_source() -> None:
    request = default_runtime_observation_to_orchestration_input_request(
        build_incomplete_observation_source(),
        source_contract_name=OBSERVATION_CONTRACT_NAME,
    )
    contract = build_runtime_observation_to_orchestration_input_v1(request)
    assert contract["orchestration_input_status"] in {"NOT_READY", "INVALID"}


def test_orchestration_input_rejects_invalid_learning_source() -> None:
    request = default_runtime_observation_to_orchestration_input_request(
        build_invalid_learning_source(),
        source_contract_name=LEARNING_INPUT_CONTRACT_NAME,
    )
    contract = build_runtime_observation_to_orchestration_input_v1(request)
    assert contract["orchestration_input_status"] == "INVALID"


def test_orchestration_input_rejects_bitcoin_instrument() -> None:
    request = default_runtime_observation_to_orchestration_input_request(
        build_invalid_learning_source(),
        source_contract_name=LEARNING_INPUT_CONTRACT_NAME,
    )
    contract = build_runtime_observation_to_orchestration_input_v1(request)
    assert contract["orchestration_input_status"] == "INVALID"
    assert "BITCOIN_INSTRUMENT_REJECTED" in contract["blocking_reasons"]


@pytest.mark.parametrize(
    ("override", "expected_code"),
    [
        ({"orchestration_authorization_requested": True}, "ORCHESTRATION_AUTHORIZATION_REQUESTED"),
        ({"runtime_authorization_requested": True}, "RUNTIME_AUTHORIZATION_REQUESTED"),
        ({"scheduler_authorization_requested": True}, "SCHEDULER_AUTHORIZATION_REQUESTED"),
        ({"activation_requested": True}, "ACTIVATION_REQUESTED"),
        ({"champion_selection_requested": True}, "CHAMPION_SELECTION_REQUESTED"),
        ({"role_assignment_requested": True}, "ROLE_ASSIGNMENT_REQUESTED"),
    ],
)
def test_orchestration_input_rejects_forbidden_requests(override: dict, expected_code: str) -> None:
    contract = build_runtime_observation_to_orchestration_input_v1(
        build_valid_orchestration_input_request(**override)
    )
    assert contract["orchestration_input_status"] == "INVALID"
    assert expected_code in contract["blocking_reasons"]


def test_orchestration_input_futures_guard_accepts_eth_swap() -> None:
    contract = build_runtime_observation_to_orchestration_input_v1()
    assert contract["orchestration_input_status"] == "READY"
    assert contract["futures_only"] is True
    assert contract["spot_allowed"] is False
    assert contract["synthetic_spot_allowed"] is False


def test_orchestration_input_no_champion_or_challenger_selection() -> None:
    contract = build_runtime_observation_to_orchestration_input_v1()
    assert contract["champion_selection_performed"] is False
    assert contract["challenger_selection_performed"] is False
    assert contract["role_assignment_executed"] is False


# --- Contract B: autonomous_non_live_orchestration_plan_v1 ---


def test_plan_happy_path() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1()
    assert contract["plan_status"] == "PLAN_READY"
    assert contract["offline_plan_only"] is True
    assert contract["plan_does_not_execute"] is True
    assert contract["plan_does_not_activate"] is True
    assert contract["plan_does_not_schedule"] is True
    assert contract["plan_does_not_issue_authority"] is True
    assert contract["plan_does_not_arm"] is True
    assert contract["progress_registry_mutated"] is False


def test_plan_deterministic_repeat() -> None:
    request = build_valid_plan_request()
    assert build_autonomous_non_live_orchestration_plan_v1(
        request
    ) == build_autonomous_non_live_orchestration_plan_v1(request)


def test_plan_canonical_json_stability() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1()
    assert serialize_autonomous_non_live_orchestration_plan_v1(
        contract
    ) == deterministic_json_dumps(contract)


def test_plan_producer_replay_and_manifest(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "plan_out")
    produce_autonomous_non_live_orchestration_plan_v1(
        request=default_autonomous_non_live_orchestration_plan_request(),
        output_dir=out,
    )
    verified = reverify_autonomous_non_live_orchestration_plan_v1(output_dir=out)
    ok, _msg = verify_manifest_sha256(out)
    assert ok
    assert verified["plan_status"] == "PLAN_READY"


def test_plan_stage_sequence_is_canonical() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1()
    assert tuple(contract["stage_sequence"]) == CANONICAL_STAGE_SEQUENCE
    assert contract["current_stage"] == "REPLAY_ONLY"
    assert contract["next_planned_stage"] == "SHADOW_ONLY"


def test_plan_each_stage_remains_non_executing() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1()
    for stage in contract["stage_contracts"]:
        for flag in _STAGE_EXEC_FLAGS:
            assert stage[flag] is False, f"{stage['stage_name']}.{flag}"


def test_plan_shadow_paper_testnet_require_operator_go() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1()
    by_name = {stage["stage_name"]: stage for stage in contract["stage_contracts"]}
    assert by_name["REPLAY_ONLY"]["separate_operator_go_required"] is False
    assert by_name["SHADOW_ONLY"]["separate_operator_go_required"] is True
    assert by_name["PAPER_ONLY"]["separate_operator_go_required"] is True
    assert by_name["TESTNET_ONLY"]["separate_operator_go_required"] is True


def test_plan_rejects_invalid_stage_sequence() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1(
        build_valid_plan_request(stage_sequence=("SHADOW_ONLY", "REPLAY_ONLY"))
    )
    assert contract["plan_status"] in {"PLAN_BLOCKED", "PLAN_INVALID"}
    assert "INVALID_STAGE_SEQUENCE" in contract["blocking_reasons"]


def test_plan_rejects_unknown_stage() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1(
        build_valid_plan_request(stage_sequence=("REPLAY_ONLY", "LIVE_ONLY"))
    )
    assert contract["plan_status"] in {"PLAN_BLOCKED", "PLAN_INVALID"}


def test_plan_not_ready_for_incomplete_orchestration_input() -> None:
    incomplete_oi = build_runtime_observation_to_orchestration_input_v1(
        default_runtime_observation_to_orchestration_input_request(
            build_incomplete_observation_source(),
            source_contract_name=OBSERVATION_CONTRACT_NAME,
        )
    )
    contract = build_autonomous_non_live_orchestration_plan_v1(
        default_autonomous_non_live_orchestration_plan_request(incomplete_oi)
    )
    assert contract["plan_status"] in {"PLAN_NOT_READY", "PLAN_BLOCKED", "PLAN_INVALID"}


def test_plan_blocked_for_digest_mismatch() -> None:
    oi = build_runtime_observation_to_orchestration_input_v1()
    contract = build_autonomous_non_live_orchestration_plan_v1(
        default_autonomous_non_live_orchestration_plan_request(
            oi,
            source_orchestration_input_digest=minimal_invalid_digest(),
        )
    )
    assert contract["plan_status"] in {"PLAN_BLOCKED", "PLAN_INVALID"}
    assert "ORCHESTRATION_INPUT_DIGEST_MISMATCH" in contract["blocking_reasons"]


def test_plan_champion_challenger_metadata_only() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1()
    assert contract["champion_ref"]["role_name"] == "LIVE_PRIMARY"
    assert contract["champion_ref"]["status"] == "NOT_BOUND"
    assert contract["rollback_standby_ref"]["role_name"] == "ROLLBACK_STANDBY"
    assert contract["challenger_ref"]["role_name"] == "CHALLENGER_SHADOW"
    assert contract["champion_selection_performed"] is False
    assert contract["challenger_selection_performed"] is False
    assert contract["role_assignment_executed"] is False
    assert contract["deployment_performed"] is False
    assert contract["activation_performed"] is False
    assert contract["runtime_started"] is False


def test_plan_futures_only_constraints() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1()
    assert contract["futures_only"] is True
    assert contract["bitcoin_direction_allowed"] is False
    assert contract["spot_allowed"] is False
    assert contract["synthetic_spot_allowed"] is False
    assert contract["environment_constraints"]["live_authorized"] is False


@pytest.mark.parametrize(
    ("override", "expected_code"),
    [
        ({"plan_execution_requested": True}, "PLAN_EXECUTION_REQUESTED"),
        ({"plan_activation_requested": True}, "PLAN_ACTIVATION_REQUESTED"),
        ({"plan_scheduling_requested": True}, "PLAN_SCHEDULING_REQUESTED"),
        ({"champion_selection_requested": True}, "CHAMPION_SELECTION_REQUESTED"),
        ({"progress_registry_mutation_requested": True}, "PROGRESS_REGISTRY_MUTATION_REQUESTED"),
    ],
)
def test_plan_rejects_forbidden_requests(override: dict, expected_code: str) -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1(build_valid_plan_request(**override))
    assert contract["plan_status"] in {"PLAN_BLOCKED", "PLAN_INVALID"}
    assert expected_code in contract["blocking_reasons"]


def test_plan_from_orchestration_input_bundle(tmp_path: Path) -> None:
    orch_bundle = produce_orchestration_input_fixture(tmp_path, "orch_bundle_for_plan")
    request = build_plan_request_from_orchestration_input_bundle(orch_bundle)
    contract = build_autonomous_non_live_orchestration_plan_v1(request)
    assert contract["plan_status"] == "PLAN_READY"


def test_full_step27_chain_fixtures(tmp_path: Path) -> None:
    observation, learning, orchestration, plan = produce_full_step27_chain_fixtures(tmp_path)
    assert (observation / "runtime_observation_bundle_v1.json").is_file()
    assert (learning / "runtime_to_learning_input_v1.json").is_file()
    assert (orchestration / ORCHESTRATION_INPUT_ARTIFACT_REL).is_file()
    assert (plan / PLAN_ARTIFACT_REL).is_file()


def test_authority_invariants_present() -> None:
    assert AUTONOMOUS_NON_LIVE_ORCHESTRATION_AUTHORITY_INVARIANTS["step27_offline_only"] is True
    assert AUTONOMOUS_NON_LIVE_ORCHESTRATION_AUTHORITY_INVARIANTS["runtime_effect"] is False
    assert AUTONOMOUS_NON_LIVE_ORCHESTRATION_AUTHORITY_INVARIANTS["non_authorizing"] is True
    assert (
        AUTONOMOUS_NON_LIVE_ORCHESTRATION_AUTHORITY_INVARIANTS["progress_registry_mutation_allowed"]
        is False
    )
    assert (
        AUTONOMOUS_NON_LIVE_ORCHESTRATION_AUTHORITY_INVARIANTS["step28_implementation_allowed"]
        is False
    )


def test_reuse_step26_owners_import_side_effect_free() -> None:
    import importlib

    mod = importlib.import_module(
        "src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1"
    )
    assert hasattr(mod, "load_verified_observation_bundle")
    assert hasattr(mod, "load_verified_learning_input_bundle")
    assert (
        mod.AUTONOMOUS_NON_LIVE_ORCHESTRATION_AUTHORITY_INVARIANTS[
            "progress_registry_mutation_allowed"
        ]
        is False
    )


def test_plan_stage_readiness_never_authorized() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1()
    for stage_name, status in contract["stage_readiness_status"].items():
        assert status == "NOT_READY", stage_name
        stage = next(s for s in contract["stage_contracts"] if s["stage_name"] == stage_name)
        assert stage["transition_status"] == "NOT_READY"


def test_orchestration_input_rejects_missing_source_bundle(tmp_path: Path) -> None:
    with pytest.raises(AutonomousNonLiveOrchestrationError):
        build_orchestration_input_request_from_observation_bundle(tmp_path / "missing")


def test_plan_ready_does_not_mean_stage_authorized() -> None:
    contract = build_autonomous_non_live_orchestration_plan_v1()
    assert contract["plan_status"] == "PLAN_READY"
    for stage in contract["stage_contracts"]:
        assert stage["execution_allowed"] is False
        assert stage["activation_allowed"] is False
