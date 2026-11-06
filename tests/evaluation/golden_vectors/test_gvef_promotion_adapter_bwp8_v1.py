"""BWP-8 promotion evidence adapter tests."""

from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path

import pytest

from src.evaluation.golden_vectors.contracts.enums import (
    ExternalPromotionStatus,
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import contract_digest_hex
from src.evaluation.golden_vectors.promotion.errors import GvefPromotionAuthorityError
from src.evaluation.golden_vectors.promotion.external_governance_boundary_v1 import (
    EXTERNAL_GOVERNANCE_DECISION_OWNER,
    GVEF_AUTHORITY_END_STATE,
    PROMOTION_GVEF_AUTHORITY,
)
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    BWP_ID,
    COMPONENT_ID,
    PRIMARY_FAILURE_CLASS,
    REPROOF_CLASS,
    PromotionAdaptRequestV1,
    PromotionEvidenceAdapterV1,
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
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
    GenericRunnerV1,
    GvefRunRequestV1,
    GvefRunnerDependenciesV1,
    evidence_complete,
)
from src.evaluation.golden_vectors.runner.states import RunnerState
from tests.evaluation.golden_vectors.promotion_fixtures_v1 import valid_evidence_bundle
from tests.evaluation.golden_vectors.runner_fixtures_v1 import parsed_context


@pytest.fixture
def adapter() -> PromotionEvidenceAdapterV1:
    return PromotionEvidenceAdapterV1()


def test_canonical_bwp8_identity() -> None:
    assert BWP_ID == "BWP-8"
    assert COMPONENT_ID == "gvef.promotion_evidence_adapter_v1"
    assert PRIMARY_FAILURE_CLASS == "AUTHORITY_FAILURE"
    assert REPROOF_CLASS == "LOCAL_EVALUATION"
    assert PROMOTION_GVEF_AUTHORITY is False
    assert GVEF_AUTHORITY_END_STATE == "EVIDENCE_HANDOFF_ONLY"


def test_valid_adapt(adapter: PromotionEvidenceAdapterV1) -> None:
    bundle = valid_evidence_bundle()
    env = adapter.adapt(
        bundle=bundle,
        request=PromotionAdaptRequestV1(
            evidence_bundle_ref="registry/r1",
            governance_handoff_timestamp="2026-10-04T09:00:00Z",
        ),
    )
    assert env.evidence_digest == bundle.evidence_digest
    assert env.post_constraint_gate_pass is True


def test_post_gate_fail(adapter: PromotionEvidenceAdapterV1) -> None:
    bundle = valid_evidence_bundle(post_gate_pass=False)
    with pytest.raises(GvefPromotionAuthorityError):
        adapter.adapt(
            bundle=bundle,
            request=PromotionAdaptRequestV1(
                evidence_bundle_ref="registry/r1",
                governance_handoff_timestamp="2026-10-04T09:00:00Z",
            ),
        )


@pytest.mark.parametrize(
    "probe_key",
    [
        "claims_promotion_authority",
        "claims_governance_self_approval",
        "claims_post_authority",
        "selection_mutation",
        "productive_write",
        "mutate_source_bundle",
    ],
)
def test_authority_probes(adapter: PromotionEvidenceAdapterV1, probe_key: str) -> None:
    bundle = valid_evidence_bundle()
    with pytest.raises(GvefPromotionAuthorityError):
        adapter.adapt(
            bundle=bundle,
            request=PromotionAdaptRequestV1(
                evidence_bundle_ref="registry/r1",
                governance_handoff_timestamp="2026-10-04T09:00:00Z",
                authority_probe={probe_key: True},
            ),
        )


def test_digest_mismatch(adapter: PromotionEvidenceAdapterV1) -> None:
    bundle = valid_evidence_bundle()
    mutated = bundle.model_dump(mode="json")
    mutated["experiment_id"] = "mutated"
    from src.evaluation.golden_vectors.contracts.validation import parse_evidence_bundle_v1

    bad = parse_evidence_bundle_v1(mutated)
    with pytest.raises(GvefPromotionAuthorityError):
        adapter.adapt(
            bundle=bad,
            request=PromotionAdaptRequestV1(
                evidence_bundle_ref="registry/r1",
                governance_handoff_timestamp="2026-10-04T09:00:00Z",
            ),
        )


def test_external_eligibility_status_rejected(adapter: PromotionEvidenceAdapterV1) -> None:
    from src.evaluation.golden_vectors.contracts.validation import parse_evidence_bundle_v1
    from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
        evidence_bundle_semantic_digest,
    )

    bundle = valid_evidence_bundle()
    payload = bundle.model_dump(mode="json")
    payload["promotion_status"] = ExternalPromotionStatus.LIVE_ELIGIBLE.value
    temp = parse_evidence_bundle_v1({**payload, "evidence_digest": "a" * 64})
    payload["evidence_digest"] = evidence_bundle_semantic_digest(temp)
    eligible = parse_evidence_bundle_v1(payload)
    with pytest.raises(GvefPromotionAuthorityError):
        adapter.adapt(
            bundle=eligible,
            request=PromotionAdaptRequestV1(
                evidence_bundle_ref="registry/r1",
                governance_handoff_timestamp="2026-10-04T09:00:00Z",
            ),
        )


def test_deterministic_adapt(adapter: PromotionEvidenceAdapterV1) -> None:
    bundle = valid_evidence_bundle()
    req = PromotionAdaptRequestV1(
        evidence_bundle_ref="registry/r1",
        governance_handoff_timestamp="2026-10-04T09:00:00Z",
    )
    e1 = adapter.adapt(bundle=bundle, request=req)
    e2 = adapter.adapt(bundle=bundle, request=req)
    assert contract_digest_hex(e1) == contract_digest_hex(e2)


def test_runner_with_promotion_adapter_local_reproof_on_fail() -> None:
    bundle = valid_evidence_bundle()
    bad_adapter = PromotionEvidenceAdapterV1()

    class FailingAdapter(PromotionEvidenceAdapterV1):
        def adapt(self, *, bundle, request):  # type: ignore[override]
            raise GvefPromotionAuthorityError("probe", field="claims_promotion_authority")

    record = GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()),
        GvefRunnerDependenciesV1(
            pre_gate=DeterministicPreGateV1(),
            post_gate=DeterministicPostGateV1(),
            replay_adapter=DeterministicReplayAdapterV1(),
            evaluator=DeterministicDomainEvaluatorV1(),
            comparator=DeterministicComparatorV1(),
            delta_builder=DeterministicDeltaBuilderV1(),
            evidence_builder=DeterministicEvidenceBuilderV1(),
            registry=InMemoryEvidenceRegistryV1(),
            promotion_adapter=FailingAdapter(),
        ),
    )
    assert record.state is RunnerState.FAILED
    assert record.failure_classification is FailureClassification.AUTHORITY_FAILURE
    assert record.fan_out_evaluation_class is FanOutEvaluationClass.LOCAL_EVALUATION
    assert not evidence_complete(record)
    _ = bad_adapter  # silence lint


def test_runner_promotion_envelope_on_success() -> None:
    record = GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()),
        GvefRunnerDependenciesV1(
            pre_gate=DeterministicPreGateV1(),
            post_gate=DeterministicPostGateV1(),
            replay_adapter=DeterministicReplayAdapterV1(),
            evaluator=DeterministicDomainEvaluatorV1(),
            comparator=DeterministicComparatorV1(),
            delta_builder=DeterministicDeltaBuilderV1(),
            evidence_builder=DeterministicEvidenceBuilderV1(),
            registry=InMemoryEvidenceRegistryV1(),
            promotion_adapter=PromotionEvidenceAdapterV1(),
        ),
    )
    assert record.state is RunnerState.REGISTERED
    assert record.promotion_envelope is not None


def test_corpus_drift_unchanged() -> None:
    from src.evaluation.golden_vectors.contracts.validation import parse_corpus_manifest_v1
    from src.evaluation.golden_vectors.corpus.errors import GvefCorpusDriftError
    from src.evaluation.golden_vectors.corpus.registry_v1 import VectorCorpusRegistryV1
    from tests.evaluation.golden_vectors.corpus_fixtures_v1 import FIXTURE_CORPUS_REF

    entry = VectorCorpusRegistryV1.default().load_entry(FIXTURE_CORPUS_REF)
    bad = entry.manifest.model_dump(mode="json")
    bad["corpus_digest"] = "d" * 64
    with pytest.raises(GvefCorpusDriftError):
        VectorCorpusRegistryV1.default().validate_in_memory(
            manifest=parse_corpus_manifest_v1(bad),
            vectors={v.vector_id: v for v in entry.vectors},
        )


def test_cross_process_promotion_adapt() -> None:
    cmd = ["./scripts/pt", "-m", "tests.evaluation.golden_vectors.promotion_replay_worker_v1"]
    env_a = os.environ.copy()
    env_a["PYTHONHASHSEED"] = "1"
    env_b = os.environ.copy()
    env_b["PYTHONHASHSEED"] = "7777"
    assert json.loads(subprocess.check_output(cmd, env=env_a, text=True)) == json.loads(
        subprocess.check_output(cmd, env=env_b, text=True)
    )


FORBIDDEN = (
    "full_core_live_path_composition_root_v1",
    "checkout_independent_credential",
    "optimization_proposal_governance_ingress_v1",
    "single_selected_future_policy_v1.persistence",
)


def test_forbidden_deps() -> None:
    root = Path("src/evaluation/golden_vectors")
    violations: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for frag in FORBIDDEN:
                    if frag in node.module and "external_governance_boundary" not in str(path):
                        violations.append(f"{path}:{node.module}")
    assert violations == []
