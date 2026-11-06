"""BWP-9 whole-system integration fixtures (TEST_ONLY_SYNTHETIC)."""

from __future__ import annotations

from src.evaluation.golden_vectors.corpus.gate_v1 import (
    PassThroughCorpusIntegrityGateV1,
    VectorCorpusIntegrityGateV1,
)
from src.evaluation.golden_vectors.corpus.registry_v1 import VectorCorpusRegistryV1
from src.evaluation.golden_vectors.evaluators.productive_trading_path_v1 import (
    ProductiveTradingPathEvaluatorV1,
)
from src.evaluation.golden_vectors.integration.whole_system_v1 import whole_system_runner_v1
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    PromotionEvidenceAdapterV1,
)
from src.evaluation.golden_vectors.registry.evidence_registry_v1 import GvefEvidenceRegistryV1
from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
    DeterministicComparatorV1,
    DeterministicDeltaBuilderV1,
    DeterministicDomainEvaluatorV1,
    DeterministicEvidenceBuilderV1,
    DeterministicPostGateV1,
    DeterministicPreGateV1,
    DeterministicReplayAdapterV1,
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
    GvefRunRequestV1,
    GvefRunnerDependenciesV1,
)
from tests.evaluation.golden_vectors.corpus_fixtures_v1 import corpus_bound_context


def whole_system_deps(
    *,
    registry: GvefEvidenceRegistryV1 | None = None,
    pre_gate: DeterministicPreGateV1 | None = None,
    post_gate: DeterministicPostGateV1 | None = None,
    evaluator=None,
    corpus_gate=None,
    promotion_adapter: PromotionEvidenceAdapterV1 | None = None,
    bind_corpus: bool = False,
) -> GvefRunnerDependenciesV1:
    if corpus_gate is not None:
        gate = corpus_gate
    elif bind_corpus:
        gate = VectorCorpusIntegrityGateV1(registry=VectorCorpusRegistryV1.default())
    else:
        gate = PassThroughCorpusIntegrityGateV1()
    return GvefRunnerDependenciesV1(
        pre_gate=pre_gate or DeterministicPreGateV1(),
        post_gate=post_gate or DeterministicPostGateV1(),
        replay_adapter=DeterministicReplayAdapterV1(),
        evaluator=evaluator or DeterministicDomainEvaluatorV1(),
        comparator=DeterministicComparatorV1(),
        delta_builder=DeterministicDeltaBuilderV1(),
        evidence_builder=DeterministicEvidenceBuilderV1(),
        registry=registry or GvefEvidenceRegistryV1(),
        corpus_gate=gate,
        promotion_adapter=promotion_adapter or PromotionEvidenceAdapterV1(),
    )


def whole_system_success_request(*, unique_run: bool = False) -> GvefRunRequestV1:
    from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import (
        ptp_stage_entries,
        replay_trace,
    )

    ctx = corpus_bound_context(domain_evaluator_id="productive_trading_path_evaluator_v1")
    ctx_dict = ctx.model_dump(mode="json", by_alias=True)
    run_id = ctx_dict["run_manifest"]["run_id"]
    if unique_run:
        # Deterministic UUID v4 (BWP-1 run_id contract) for replay/determinism tests.
        run_id = "a1b2c3d4-e5f6-4789-a012-3456789abcde"
        ctx_dict["run_manifest"]["run_id"] = run_id
    ctx_dict["replay_trace"] = replay_trace(ptp_stage_entries(run_id=run_id, synthetic=True))
    from src.evaluation.golden_vectors.contracts.validation import (
        parse_domain_evaluation_context_v1,
    )

    return GvefRunRequestV1(parse_domain_evaluation_context_v1(ctx_dict))


def run_whole_system_success(*, unique_run: bool = False, verify_replay: bool = True):
    return whole_system_runner_v1().execute(
        whole_system_success_request(unique_run=unique_run),
        whole_system_deps(
            evaluator=ProductiveTradingPathEvaluatorV1(),
            bind_corpus=True,
        ),
        verify_deterministic_replay=verify_replay,
    )
