"""BWP-7 corpus integrity / drift control tests."""

from __future__ import annotations

import ast
import copy
import json
import os
import subprocess
from pathlib import Path

import pytest

from src.evaluation.golden_vectors.contracts.enums import (
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.validation import (
    parse_corpus_manifest_v1,
    parse_vector_manifest_v1,
)
from src.evaluation.golden_vectors.corpus.digest_v1 import corpus_identity_digest_hex
from src.evaluation.golden_vectors.corpus.errors import GvefCorpusDriftError
from src.evaluation.golden_vectors.corpus.registry_v1 import (
    CANONICAL_CORPUS_ROOT,
    VectorCorpusRegistryV1,
)
from src.evaluation.golden_vectors.corpus.gate_v1 import VectorCorpusIntegrityGateV1
from src.evaluation.golden_vectors.evaluators.productive_trading_path_v1 import (
    ProductiveTradingPathEvaluatorV1,
)
from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
    DeterministicComparatorV1,
    DeterministicDeltaBuilderV1,
    DeterministicEvidenceBuilderV1,
    DeterministicPostGateV1,
    DeterministicPreGateV1,
    DeterministicReplayAdapterV1,
    InMemoryEvidenceRegistryV1,
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
    GenericRunnerV1,
    GvefRunRequestV1,
    GvefRunnerDependenciesV1,
    evidence_complete,
)
from src.evaluation.golden_vectors.runner.states import RunnerState
from tests.evaluation.golden_vectors.corpus_fixtures_v1 import (
    FIXTURE_CORPUS_REF,
    build_corpus_manifest_dict,
    corpus_bound_context,
    parsed_fixture_vectors,
    vector_ptp,
    vector_ru,
)
from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import ptp_context


@pytest.fixture
def registry() -> VectorCorpusRegistryV1:
    return VectorCorpusRegistryV1.default()


def test_fixture_corpus_loads(registry: VectorCorpusRegistryV1) -> None:
    result = registry.validate(FIXTURE_CORPUS_REF)
    assert result.corpus_identity_digest == build_corpus_manifest_dict()["corpus_digest"]
    assert len(result.vector_identity_digests) == 2


def test_corpus_drift_wrong_digest(registry: VectorCorpusRegistryV1) -> None:
    manifest = build_corpus_manifest_dict()
    manifest["corpus_digest"] = "b" * 64
    with pytest.raises(GvefCorpusDriftError):
        registry.validate_in_memory(
            manifest=parse_corpus_manifest_v1(manifest),
            vectors=parsed_fixture_vectors(),
        )


def test_duplicate_vector_id(registry: VectorCorpusRegistryV1) -> None:
    manifest = build_corpus_manifest_dict()
    manifest["vector_ids"] = [
        "vec-gvef-ptp-mechanism-001",
        "vec-gvef-ptp-mechanism-001",
    ]
    with pytest.raises(GvefCorpusDriftError):
        registry.validate_in_memory(
            manifest=parse_corpus_manifest_v1(manifest),
            vectors=parsed_fixture_vectors(),
        )


def test_missing_vector(registry: VectorCorpusRegistryV1) -> None:
    manifest = build_corpus_manifest_dict()
    manifest["vector_ids"] = ["vec-gvef-ptp-mechanism-001", "vec-missing"]
    with pytest.raises(GvefCorpusDriftError):
        registry.validate_in_memory(
            manifest=parse_corpus_manifest_v1(manifest),
            vectors=parsed_fixture_vectors(),
        )


def test_unexpected_vector(registry: VectorCorpusRegistryV1) -> None:
    manifest = build_corpus_manifest_dict()
    vectors = parsed_fixture_vectors()
    vectors["vec-extra"] = parse_vector_manifest_v1(
        {
            **vector_ru(),
            "vector_id": "vec-extra",
        }
    )
    with pytest.raises(GvefCorpusDriftError):
        registry.validate_in_memory(
            manifest=parse_corpus_manifest_v1(manifest),
            vectors=vectors,
        )


def test_unknown_vector_class(registry: VectorCorpusRegistryV1) -> None:
    with pytest.raises(GvefCorpusDriftError):
        registry.assert_vector_class_known("NotARealClass")


def test_vector_content_mutation_is_drift(registry: VectorCorpusRegistryV1) -> None:
    manifest = parse_corpus_manifest_v1(build_corpus_manifest_dict())
    vectors = parsed_fixture_vectors()
    mutated = copy.deepcopy(vectors["vec-gvef-ptp-mechanism-001"])
    mutated_dict = mutated.model_dump(mode="json")
    mutated_dict["invariant_ids"] = ["changed"]
    vectors["vec-gvef-ptp-mechanism-001"] = parse_vector_manifest_v1(mutated_dict)
    with pytest.raises(GvefCorpusDriftError):
        registry.validate_in_memory(manifest=manifest, vectors=vectors)


def test_membership_reorder_changes_digest() -> None:
    manifest = build_corpus_manifest_dict()
    vectors = parsed_fixture_vectors()
    reordered = copy.deepcopy(manifest)
    reordered["vector_ids"] = list(reversed(manifest["vector_ids"]))
    m = parse_corpus_manifest_v1(reordered)
    digests = {k: v for k, v in [(vid, "") for vid in m.vector_ids]}
    from src.evaluation.golden_vectors.corpus.digest_v1 import vector_identity_digest_hex

    digests = {vid: vector_identity_digest_hex(vectors[vid]) for vid in m.vector_ids}
    new_digest = corpus_identity_digest_hex(m, vector_digests_by_id=digests)
    assert new_digest != manifest["corpus_digest"]


def test_deterministic_validation_replay(registry: VectorCorpusRegistryV1) -> None:
    outputs: set[str] = set()
    for _ in range(25):
        result = registry.validate(FIXTURE_CORPUS_REF)
        outputs.add(result.corpus_identity_digest)
    assert len(outputs) == 1


def test_runner_corpus_drift_fails_whole_system_reproof() -> None:
    ctx = corpus_bound_context()
    ctx_dict = ctx.model_dump(mode="json", by_alias=True)
    ctx_dict["corpus_identity"]["corpus_digest"] = "c" * 64
    from src.evaluation.golden_vectors.contracts.validation import (
        parse_domain_evaluation_context_v1,
    )

    bad = parse_domain_evaluation_context_v1(ctx_dict)
    gate = VectorCorpusIntegrityGateV1(registry=VectorCorpusRegistryV1.default())
    deps = GvefRunnerDependenciesV1(
        pre_gate=DeterministicPreGateV1(),
        post_gate=DeterministicPostGateV1(),
        replay_adapter=DeterministicReplayAdapterV1(),
        evaluator=ProductiveTradingPathEvaluatorV1(),
        comparator=DeterministicComparatorV1(),
        delta_builder=DeterministicDeltaBuilderV1(),
        evidence_builder=DeterministicEvidenceBuilderV1(),
        registry=InMemoryEvidenceRegistryV1(),
        corpus_gate=gate,
    )
    record = GenericRunnerV1().execute(GvefRunRequestV1(bad), deps)
    assert record.state is RunnerState.FAILED
    assert record.failure_classification is FailureClassification.CORPUS_DRIFT
    assert record.fan_out_evaluation_class is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    assert not evidence_complete(record)


def test_legacy_runner_without_corpus_gate_still_passes() -> None:
    record = GenericRunnerV1().execute(
        GvefRunRequestV1(ptp_context(synthetic=True)),
        GvefRunnerDependenciesV1(
            pre_gate=DeterministicPreGateV1(),
            post_gate=DeterministicPostGateV1(),
            replay_adapter=DeterministicReplayAdapterV1(),
            evaluator=ProductiveTradingPathEvaluatorV1(),
            comparator=DeterministicComparatorV1(),
            delta_builder=DeterministicDeltaBuilderV1(),
            evidence_builder=DeterministicEvidenceBuilderV1(),
            registry=InMemoryEvidenceRegistryV1(),
        ),
    )
    assert record.state is RunnerState.REGISTERED


def test_no_auto_rebaseline_api() -> None:
    assert not hasattr(VectorCorpusRegistryV1, "rebaseline")
    assert not hasattr(VectorCorpusRegistryV1, "update_digest")
    assert not hasattr(VectorCorpusRegistryV1, "rewrite_manifest")


def test_canonical_corpus_root() -> None:
    assert Path(CANONICAL_CORPUS_ROOT, "fixture_corpus_v1/corpus_manifest.json").is_file()


FORBIDDEN = (
    "full_core_live_path_composition_root_v1",
    "checkout_independent_credential",
    "optimization_proposal_governance_ingress_v1",
    "single_selected_future_policy_v1.persistence",
)


def test_gvef_forbidden_after_corpus() -> None:
    root = Path("src/evaluation/golden_vectors")
    violations: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for frag in FORBIDDEN:
                    if frag in node.module:
                        violations.append(f"{path}:{node.module}")
    assert violations == []


def test_cross_process_corpus_validation() -> None:
    cmd = ["./scripts/pt", "-m", "tests.evaluation.golden_vectors.corpus_replay_worker_v1"]
    env_a = os.environ.copy()
    env_a["PYTHONHASHSEED"] = "1"
    env_b = os.environ.copy()
    env_b["PYTHONHASHSEED"] = "99999"
    out_a = subprocess.check_output(cmd, env=env_a, text=True)
    out_b = subprocess.check_output(cmd, env=env_b, text=True)
    assert json.loads(out_a) == json.loads(out_b)
