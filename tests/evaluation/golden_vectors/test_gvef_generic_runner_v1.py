"""BWP-2 GVEF generic runner tests."""

from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path

import pytest

from src.evaluation.golden_vectors.contracts.enums import (
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError
from src.evaluation.golden_vectors.runner.digest_projection import (
    run_manifest_protected_digest_hex,
)
from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
    DeterministicComparatorV1,
    DeterministicDeltaBuilderV1,
    DeterministicDomainEvaluatorV1,
    DeterministicEvidenceBuilderV1,
    DeterministicPostGateV1,
    DeterministicPreGateV1,
    DeterministicReplayAdapterV1,
    InMemoryEvidenceRegistryV1,
    baseline_result_digest,
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
    GenericRunnerV1,
    GvefRunRequestV1,
    GvefRunnerDependenciesV1,
    evidence_complete,
)
from src.evaluation.golden_vectors.runner.states import RunnerState, transition
from tests.evaluation.golden_vectors.runner_fixtures_v1 import parsed_context, parsed_run


def _deps(**kwargs) -> GvefRunnerDependenciesV1:
    return GvefRunnerDependenciesV1(
        pre_gate=kwargs.get("pre_gate", DeterministicPreGateV1()),
        post_gate=kwargs.get("post_gate", DeterministicPostGateV1()),
        replay_adapter=DeterministicReplayAdapterV1(),
        evaluator=kwargs.get("evaluator", DeterministicDomainEvaluatorV1()),
        comparator=DeterministicComparatorV1(),
        delta_builder=DeterministicDeltaBuilderV1(),
        evidence_builder=DeterministicEvidenceBuilderV1(),
        registry=kwargs.get("registry", InMemoryEvidenceRegistryV1()),
    )


def test_success_state_sequence_includes_delta_manifest_built() -> None:
    record = GenericRunnerV1().execute(GvefRunRequestV1(parsed_context()), _deps())
    assert RunnerState.DELTA_MANIFEST_BUILT in record.state_history
    assert record.state is RunnerState.REGISTERED
    assert evidence_complete(record)


def test_failed_terminal_no_exit() -> None:
    record = GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()),
        _deps(pre_gate=DeterministicPreGateV1(should_pass=False)),
    )
    assert record.state is RunnerState.FAILED
    with pytest.raises(GvefSchemaError):
        transition(RunnerState.FAILED, RunnerState.BOUND)


def test_pre_gate_blocks_evaluator() -> None:
    ev = DeterministicDomainEvaluatorV1()
    GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()),
        _deps(pre_gate=DeterministicPreGateV1(should_pass=False), evaluator=ev),
    )
    assert ev.baseline_calls == 0


def test_post_gate_blocks_evidence_complete() -> None:
    record = GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()),
        _deps(post_gate=DeterministicPostGateV1(should_pass=False)),
    )
    assert record.state is RunnerState.FAILED
    assert not evidence_complete(record)


def test_registry_failure_prevents_registered() -> None:
    reg = InMemoryEvidenceRegistryV1(fail_next_register=True)
    record = GenericRunnerV1().execute(GvefRunRequestV1(parsed_context()), _deps(registry=reg))
    assert record.state is RunnerState.FAILED


def test_baseline_immutable_during_run() -> None:
    record = GenericRunnerV1().execute(GvefRunRequestV1(parsed_context()), _deps())
    assert record.baseline_result is not None
    assert record.baseline_result_digest == baseline_result_digest(record.baseline_result)


def test_deterministic_replay_stress() -> None:
    runner = GenericRunnerV1()
    ctx = parsed_context()
    digests: set[str] = set()
    sequences: set[tuple[str, ...]] = set()
    for _ in range(25):
        record = runner.execute(GvefRunRequestV1(ctx), _deps())
        digests.add(record.protected_output_digest or "")
        sequences.add(tuple(s.value for s in record.state_history))
    assert len(digests) == 1
    assert len(sequences) == 1


def test_created_at_utc_volatile_excluded_from_protected_digest() -> None:
    r1 = parsed_run(created_at_utc="2026-10-04T09:00:00Z")
    r2 = parsed_run(created_at_utc="2026-10-04T10:00:00Z")
    assert run_manifest_protected_digest_hex(r1) == run_manifest_protected_digest_hex(r2)


def test_protected_semantic_field_change_changes_manifest_digest() -> None:
    r1 = parsed_run()
    r2 = parsed_run()
    r2_dict = r2.model_dump(mode="json", by_alias=True)
    r2_dict["experiment_id"] = "different-experiment"
    from src.evaluation.golden_vectors.contracts.validation import parse_run_manifest_v1

    r2b = parse_run_manifest_v1(r2_dict)
    assert run_manifest_protected_digest_hex(r1) != run_manifest_protected_digest_hex(r2b)


def test_non_determinism_fails_closed() -> None:
    record = GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()),
        _deps(evaluator=DeterministicDomainEvaluatorV1(nondeterministic_on_replay=True)),
    )
    assert record.state is RunnerState.FAILED
    assert record.failure_classification is FailureClassification.NON_DETERMINISM
    assert record.fan_out_evaluation_class is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF


def test_cross_process_determinism() -> None:
    cmd = [
        "./scripts/pt",
        "-m",
        "tests.evaluation.golden_vectors.runner_replay_worker_v1",
    ]
    env_a = os.environ.copy()
    env_a["PYTHONHASHSEED"] = "1"
    env_a["TZ"] = "UTC"
    env_b = os.environ.copy()
    env_b["PYTHONHASHSEED"] = "99999"
    env_b["TZ"] = "Europe/Berlin"
    out_a = subprocess.check_output(cmd, env=env_a, text=True)
    out_b = subprocess.check_output(cmd, env=env_b, text=True)
    pa = json.loads(out_a)
    pb = json.loads(out_b)
    assert pa["protected_output_digest"] == pb["protected_output_digest"]
    assert pa["state_sequence"] == pb["state_sequence"]


FORBIDDEN = (
    "full_core_live_path_composition_root_v1",
    "checkout_independent_credential",
    "optimization_proposal_governance_ingress_v1",
    "single_selected_future_policy_v1.persistence",
)


def test_runner_forbidden_imports() -> None:
    root = Path("src/evaluation/golden_vectors")
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for frag in FORBIDDEN:
                        assert frag not in alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                for frag in FORBIDDEN:
                    assert frag not in node.module


def test_bwp1_schema_tests_still_importable() -> None:
    assert Path("tests/evaluation/golden_vectors/test_gvef_contracts_schema_v1.py").is_file()
