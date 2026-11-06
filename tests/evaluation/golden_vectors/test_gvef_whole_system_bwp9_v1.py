"""BWP-9 whole-system integration / final build acceptance tests."""

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
from src.evaluation.golden_vectors.contracts.validation import parse_domain_evaluation_context_v1
from src.evaluation.golden_vectors.corpus.gate_v1 import VectorCorpusIntegrityGateV1
from src.evaluation.golden_vectors.corpus.registry_v1 import VectorCorpusRegistryV1
from src.evaluation.golden_vectors.evaluators.market_intelligence_v1 import (
    MarketIntelligenceEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.optimization_universe_v1 import (
    OptimizationUniverseEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.productive_trading_path_v1 import (
    ProductiveTradingPathEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.ranking_universe_v1 import RankingUniverseEvaluatorV1
from src.evaluation.golden_vectors.evaluators.self_learning_v1 import SelfLearningEvaluatorV1
from src.evaluation.golden_vectors.integration.whole_system_v1 import (
    BWP_ID,
    INTEGRATED_REPROOF_CLASS,
    whole_system_runner_v1,
)
from src.evaluation.golden_vectors.promotion.errors import GvefPromotionAuthorityError
from src.evaluation.golden_vectors.promotion.external_governance_boundary_v1 import (
    EXTERNAL_GOVERNANCE_DECISION_OWNER,
    GVEF_AUTHORITY_END_STATE,
    PROMOTION_GVEF_AUTHORITY,
)
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    PromotionAdaptRequestV1,
    PromotionEvidenceAdapterV1,
)
from src.evaluation.golden_vectors.registry.errors import GvefRegistryError
from src.evaluation.golden_vectors.registry.evidence_registry_v1 import (
    COMPONENT_ID as REGISTRY_COMPONENT_ID,
    GvefEvidenceRegistryV1,
)
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
    evidence_complete,
)
from src.evaluation.golden_vectors.runner.states import RunnerState, transition
from tests.evaluation.golden_vectors.corpus_fixtures_v1 import corpus_bound_context
from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import (
    mi_context,
    mi_entries,
    opt_context,
    opt_entries,
    ptp_context,
    ru_context,
    sl_context,
    sl_entries,
)
from tests.evaluation.golden_vectors.promotion_fixtures_v1 import valid_evidence_bundle
from tests.evaluation.golden_vectors.runner_fixtures_v1 import parsed_context
from tests.evaluation.golden_vectors.whole_system_fixtures_v1 import (
    run_whole_system_success,
    whole_system_deps,
    whole_system_success_request,
)

REPO = Path(__file__).resolve().parents[3]
FORBIDDEN_FRAGMENTS = (
    "full_core_live_path_composition_root_v1",
    "checkout_independent_credential",
    "single_selected_future_policy_v1.persistence",
    "full_core_productive_http_post_transport_v1",
)


def test_bwp9_canonical_identity() -> None:
    assert BWP_ID == "BWP-9"
    assert INTEGRATED_REPROOF_CLASS is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    assert REGISTRY_COMPONENT_ID == "gvef.evidence_registry_v1"


def test_evidence_registry_duplicate_fail_closed() -> None:
    bundle = valid_evidence_bundle()
    reg = GvefEvidenceRegistryV1()
    reg.register(bundle)
    with pytest.raises(GvefRegistryError, match="duplicate"):
        reg.register(bundle)


def test_evidence_registry_digest_mismatch_fail_closed() -> None:
    bundle = valid_evidence_bundle()
    bad = bundle.model_copy(update={"evidence_digest": "f" * 64})
    reg = GvefEvidenceRegistryV1()
    with pytest.raises(GvefRegistryError, match="evidence_digest"):
        reg.register(bad)


def test_whole_system_success_vector() -> None:
    record = run_whole_system_success(unique_run=True)
    assert record.state is RunnerState.REGISTERED
    assert evidence_complete(record)
    assert record.promotion_envelope is not None
    assert record.registry_ref is not None
    assert isinstance(record.registry_ref, str)


def test_whole_system_integrated_reproof_on_pre_gate_fail() -> None:
    record = whole_system_runner_v1().execute(
        GvefRunRequestV1(parsed_context()),
        whole_system_deps(pre_gate=DeterministicPreGateV1(should_pass=False)),
    )
    assert record.state is RunnerState.FAILED
    assert record.failure_classification is FailureClassification.CONSTRAINT_FAILURE
    assert record.fan_out_evaluation_class is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    assert not evidence_complete(record)
    assert record.promotion_envelope is None


def test_whole_system_promotion_authority_preserves_failure_class() -> None:
    bundle = valid_evidence_bundle()
    bundle = bundle.model_copy(
        update={"failure_classification": FailureClassification.AUTHORITY_FAILURE.value}
    )
    adapter = PromotionEvidenceAdapterV1()
    with pytest.raises(GvefPromotionAuthorityError):
        adapter.adapt(
            bundle=bundle,
            request=PromotionAdaptRequestV1(
                evidence_bundle_ref="registry/x",
                governance_handoff_timestamp="2026-10-04T09:00:00Z",
            ),
        )


@pytest.mark.parametrize(
    "from_state,to_state",
    [
        (RunnerState.CREATED, RunnerState.REPLAYED),
        (RunnerState.BOUND, RunnerState.EVALUATED),
        (RunnerState.PRE_CONSTRAINT_CHECKED, RunnerState.COMPARED),
        (RunnerState.REPLAYED, RunnerState.DELTA_MANIFEST_BUILT),
        (RunnerState.EVALUATED, RunnerState.POST_CONSTRAINT_CHECKED),
        (RunnerState.COMPARED, RunnerState.EVIDENCE_BUILT),
        (RunnerState.DELTA_MANIFEST_BUILT, RunnerState.REGISTERED),
        (RunnerState.POST_CONSTRAINT_CHECKED, RunnerState.REGISTERED),
    ],
)
def test_illegal_state_skip_rejected(from_state: RunnerState, to_state: RunnerState) -> None:
    with pytest.raises(GvefSchemaError):
        transition(from_state, to_state)


def test_failed_terminal_no_success_transition() -> None:
    with pytest.raises(GvefSchemaError):
        transition(RunnerState.FAILED, RunnerState.REGISTERED)


def _assert_fail_closed(record, *, failure_class: FailureClassification | None = None) -> None:
    assert record.state is RunnerState.FAILED
    assert not evidence_complete(record)
    assert record.promotion_envelope is None
    assert record.fan_out_evaluation_class is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    if failure_class is not None:
        assert record.failure_classification is failure_class


def test_fail_matrix_pre_constraint() -> None:
    _assert_fail_closed(
        whole_system_runner_v1().execute(
            GvefRunRequestV1(parsed_context()),
            whole_system_deps(pre_gate=DeterministicPreGateV1(should_pass=False)),
        ),
        failure_class=FailureClassification.CONSTRAINT_FAILURE,
    )


def test_fail_matrix_nondeterminism() -> None:
    _assert_fail_closed(
        whole_system_runner_v1().execute(
            GvefRunRequestV1(parsed_context()),
            whole_system_deps(
                evaluator=DeterministicDomainEvaluatorV1(nondeterministic_on_replay=True)
            ),
        ),
        failure_class=FailureClassification.NON_DETERMINISM,
    )


def test_fail_matrix_ptp_invariant() -> None:
    ctx = corpus_bound_context()
    ctx_dict = ctx.model_dump(mode="json", by_alias=True)
    ctx_dict["replay_trace"] = ptp_context(stages=("Cap2.4 Binding",)).model_dump(mode="json")[
        "replay_trace"
    ]
    bad = parse_domain_evaluation_context_v1(ctx_dict)
    _assert_fail_closed(
        whole_system_runner_v1().execute(
            GvefRunRequestV1(bad),
            whole_system_deps(evaluator=ProductiveTradingPathEvaluatorV1()),
        ),
        failure_class=FailureClassification.INVARIANT_FAILURE,
    )


def test_fail_matrix_ru_authority() -> None:
    from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import ru_entries

    ctx = ru_context()
    ctx_dict = ctx.model_dump(mode="json", by_alias=True)
    entries = ru_entries(baseline=["A"], candidate=["A"])
    entries[0]["selection_mutation"] = True
    ctx_dict["replay_trace"] = {
        "trace_schema_version": "1.0.0",
        "trace_digest": "a" * 64,
        "entries": entries,
    }
    bad = parse_domain_evaluation_context_v1(ctx_dict)
    record = whole_system_runner_v1().execute(
        GvefRunRequestV1(bad),
        whole_system_deps(evaluator=RankingUniverseEvaluatorV1()),
    )
    _assert_fail_closed(record, failure_class=FailureClassification.AUTHORITY_FAILURE)


def test_fail_matrix_optimization_invariant() -> None:
    ctx = opt_context()
    ctx_dict = ctx.model_dump(mode="json", by_alias=True)
    entries = opt_entries()
    entries[0]["productive_apply"] = True
    ctx_dict["replay_trace"] = {
        "trace_schema_version": "1.0.0",
        "trace_digest": "a" * 64,
        "entries": entries,
    }
    bad = parse_domain_evaluation_context_v1(ctx_dict)
    record = whole_system_runner_v1().execute(
        GvefRunRequestV1(bad),
        whole_system_deps(evaluator=OptimizationUniverseEvaluatorV1()),
    )
    _assert_fail_closed(record, failure_class=FailureClassification.INVARIANT_FAILURE)


def test_fail_matrix_self_learning_authority() -> None:
    ctx = sl_context()
    ctx_dict = ctx.model_dump(mode="json", by_alias=True)
    entries = sl_entries()
    entries[0]["productive_writeback"] = True
    ctx_dict["replay_trace"] = {
        "trace_schema_version": "1.0.0",
        "trace_digest": "a" * 64,
        "entries": entries,
    }
    bad = parse_domain_evaluation_context_v1(ctx_dict)
    record = whole_system_runner_v1().execute(
        GvefRunRequestV1(bad),
        whole_system_deps(evaluator=SelfLearningEvaluatorV1()),
    )
    _assert_fail_closed(record, failure_class=FailureClassification.AUTHORITY_FAILURE)


def test_fail_matrix_market_intelligence_invariant() -> None:
    ctx = mi_context()
    ctx_dict = ctx.model_dump(mode="json", by_alias=True)
    entries = mi_entries()
    entries[0]["materialize_productive_state"] = True
    ctx_dict["replay_trace"] = {
        "trace_schema_version": "1.0.0",
        "trace_digest": "a" * 64,
        "entries": entries,
    }
    bad = parse_domain_evaluation_context_v1(ctx_dict)
    record = whole_system_runner_v1().execute(
        GvefRunRequestV1(bad),
        whole_system_deps(evaluator=MarketIntelligenceEvaluatorV1()),
    )
    _assert_fail_closed(record, failure_class=FailureClassification.INVARIANT_FAILURE)


def test_fail_matrix_corpus_drift() -> None:
    ctx = corpus_bound_context()
    ctx_dict = ctx.model_dump(mode="json", by_alias=True)
    ctx_dict["corpus_identity"]["corpus_digest"] = "d" * 64
    bad = parse_domain_evaluation_context_v1(ctx_dict)
    gate = VectorCorpusIntegrityGateV1(registry=VectorCorpusRegistryV1.default())
    _assert_fail_closed(
        whole_system_runner_v1().execute(
            GvefRunRequestV1(bad),
            whole_system_deps(
                corpus_gate=gate,
                evaluator=ProductiveTradingPathEvaluatorV1(),
            ),
        ),
        failure_class=FailureClassification.CORPUS_DRIFT,
    )


def test_fail_matrix_post_constraint() -> None:
    _assert_fail_closed(
        whole_system_runner_v1().execute(
            GvefRunRequestV1(parsed_context()),
            whole_system_deps(post_gate=DeterministicPostGateV1(should_pass=False)),
        ),
        failure_class=FailureClassification.CONSTRAINT_FAILURE,
    )


def test_fail_matrix_registry_boundary() -> None:
    reg = GvefEvidenceRegistryV1(fail_next_register=True)
    record = whole_system_runner_v1().execute(
        GvefRunRequestV1(parsed_context()),
        whole_system_deps(registry=reg),
    )
    assert record.state is RunnerState.FAILED
    assert not evidence_complete(record)


def test_fail_matrix_duplicate_registration() -> None:
    reg = GvefEvidenceRegistryV1()
    deps = whole_system_deps(
        registry=reg,
        evaluator=ProductiveTradingPathEvaluatorV1(),
        bind_corpus=True,
    )
    req = whole_system_success_request(unique_run=False)
    first = whole_system_runner_v1().execute(req, deps)
    assert first.state is RunnerState.REGISTERED
    second = whole_system_runner_v1().execute(req, deps)
    assert second.state is RunnerState.FAILED


def test_whole_system_determinism_replay_25x() -> None:
    states: set[str] = set()
    digests: set[str] = set()
    envelopes: set[str] = set()
    for _ in range(25):
        record = run_whole_system_success(unique_run=True, verify_replay=True)
        states.add(json.dumps([s.value for s in record.state_history]))
        digests.add(record.protected_output_digest or "")
        if record.promotion_envelope:
            envelopes.add(record.promotion_envelope.evidence_digest)
    assert len(states) == 1
    assert len(digests) == 1
    assert len(envelopes) == 1


def test_cross_process_whole_system_determinism() -> None:
    outputs: set[str] = set()
    for seed in ("0", "1", "42"):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = seed
        env["TZ"] = "UTC"
        proc = subprocess.run(
            [
                str(REPO / "scripts/pt"),
                "-m",
                "tests.evaluation.golden_vectors.whole_system_replay_worker_v1",
            ],
            cwd=str(REPO),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout.strip())
        outputs.add(payload["protected_output_digest"])
    assert len(outputs) == 1


def test_forbidden_productive_dependency_scan() -> None:
    violations: list[str] = []
    root = REPO / "src/evaluation/golden_vectors"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for frag in FORBIDDEN_FRAGMENTS:
                    if frag in node.module:
                        violations.append(f"{path.relative_to(REPO)}:{node.module}")
    assert violations == []


def test_external_governance_boundary_unchanged() -> None:
    assert PROMOTION_GVEF_AUTHORITY is False
    assert GVEF_AUTHORITY_END_STATE == "EVIDENCE_HANDOFF_ONLY"
    assert "optimization_proposal_governance_ingress_v1" in EXTERNAL_GOVERNANCE_DECISION_OWNER


def test_promotion_adapter_authority_probes_fail_closed() -> None:
    bundle = valid_evidence_bundle()
    adapter = PromotionEvidenceAdapterV1()
    probes = (
        {"claims_promotion_authority": True},
        {"claims_governance_self_approval": True},
        {"claims_post_authority": True},
        {"selection_mutation": True},
        {"productive_write": True},
    )
    for probe in probes:
        with pytest.raises(GvefPromotionAuthorityError):
            adapter.adapt(
                bundle=bundle,
                request=PromotionAdaptRequestV1(
                    evidence_bundle_ref="registry/r",
                    governance_handoff_timestamp="2026-10-04T09:00:00Z",
                    authority_probe=probe,
                ),
            )


def test_evidence_complete_predicate() -> None:
    record = run_whole_system_success(unique_run=True)
    assert evidence_complete(record)
    record.state = RunnerState.EVIDENCE_BUILT
    assert not evidence_complete(record)
