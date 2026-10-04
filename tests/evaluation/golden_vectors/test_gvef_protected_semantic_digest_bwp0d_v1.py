"""BWP-0D protected semantic digest layer tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.evaluation.golden_vectors.contracts.enums import (
    DigestVerdict,
    FailureClassification,
    FanOutEvaluationClass,
    ProtectedDomain,
)
from src.evaluation.golden_vectors.contracts.models import (
    ProtectedDigestEntryV1,
    ProtectedSemanticDigestsV1,
)
from src.evaluation.golden_vectors.digest.comparator_v1 import ProtectedSemanticComparatorV1
from src.evaluation.golden_vectors.digest.errors import GvefProtectedDigestDriftError
from src.evaluation.golden_vectors.digest.protected_semantic_digest_layer_v1 import (
    BWP_ID,
    COMPONENT_ID,
    compare_protected_semantic_digests,
    enforce_ranking_universe_selection_separation,
    raise_if_fail_closed,
    reproof_class_for_verdict,
    resolve_reproof_class,
    semantic_payload_digest_hex,
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import GenericRunnerV1
from src.evaluation.golden_vectors.runner.states import RunnerState
from tests.evaluation.golden_vectors.runner_fixtures_v1 import (
    domain_context,
    protected_digests,
)

_SHA = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64


def _digests(*, ru: str = _SHA, sel: str = _SHA_B) -> ProtectedSemanticDigestsV1:
    payload = protected_digests()
    payload["ranking_universe"]["digest_hex"] = ru
    payload["selection"]["digest_hex"] = sel
    return ProtectedSemanticDigestsV1.model_validate(payload)


def test_deterministic_canonical_digest() -> None:
    payload = {"z": 1, "a": 2, "created_at_utc": "ignored"}
    d1 = semantic_payload_digest_hex(payload)
    d2 = semantic_payload_digest_hex({"a": 2, "z": 1})
    assert d1 == d2
    assert len(d1) == 64


def test_key_order_invariance() -> None:
    assert semantic_payload_digest_hex({"b": 2, "a": 1}) == semantic_payload_digest_hex(
        {"a": 1, "b": 2}
    )


def test_semantic_change_detection() -> None:
    assert semantic_payload_digest_hex({"a": 1}) != semantic_payload_digest_hex({"a": 2})


def test_ranking_universe_selection_separation_enforced() -> None:
    with pytest.raises(GvefProtectedDigestDriftError):
        enforce_ranking_universe_selection_separation(_digests(ru=_SHA, sel=_SHA))


def test_digest_equal_verdict() -> None:
    base = _digests()
    report = compare_protected_semantic_digests(baseline=base, candidate=base)
    assert report.fail_closed is False
    assert report.worst_verdict is DigestVerdict.DIGEST_EQUAL


def test_expected_change_verdict() -> None:
    base = _digests()
    cand = _digests(ru=_SHA_C)
    report = compare_protected_semantic_digests(
        baseline=base,
        candidate=cand,
        expected_changed_domains=frozenset({ProtectedDomain.RANKING_UNIVERSE}),
    )
    ru_row = next(r for r in report.comparisons if r.domain is ProtectedDomain.RANKING_UNIVERSE)
    assert ru_row.verdict is DigestVerdict.DIGEST_CHANGED_EXPECTED
    assert ru_row.fail_closed is False


def test_unexpected_change_fail_closed_and_reproof() -> None:
    base = _digests()
    cand = _digests(ru=_SHA_C)
    report = compare_protected_semantic_digests(baseline=base, candidate=cand)
    ru_row = next(r for r in report.comparisons if r.domain is ProtectedDomain.RANKING_UNIVERSE)
    assert ru_row.verdict is DigestVerdict.DIGEST_CHANGED_UNEXPECTED
    assert ru_row.fail_closed is True
    assert ru_row.reproof_class is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    with pytest.raises(GvefProtectedDigestDriftError) as exc:
        raise_if_fail_closed(report)
    assert exc.value.reproof_class is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF


def test_unavailable_digest_fail_closed() -> None:
    base = _digests()
    base = ProtectedSemanticDigestsV1(
        ranking_universe=base.ranking_universe,
        selection=base.selection,
        mv2=ProtectedDigestEntryV1(digest_hex=_SHA, schema_version="1.0.0"),
    )
    cand = _digests()
    report = compare_protected_semantic_digests(baseline=base, candidate=cand)
    mv2_row = next(r for r in report.comparisons if r.domain is ProtectedDomain.MV2)
    assert mv2_row.verdict is DigestVerdict.DIGEST_UNAVAILABLE
    assert mv2_row.fail_closed is True


def test_conflicting_digest_verdict() -> None:
    entry = ProtectedDigestEntryV1(
        digest_hex=_SHA,
        schema_version="1.0.0",
        verdict=DigestVerdict.DIGEST_CONFLICTING,
    )
    dig = ProtectedSemanticDigestsV1(ranking_universe=entry, selection=_digests().selection)
    report = compare_protected_semantic_digests(baseline=dig, candidate=dig)
    ru = next(r for r in report.comparisons if r.domain is ProtectedDomain.RANKING_UNIVERSE)
    assert ru.verdict is DigestVerdict.DIGEST_CONFLICTING
    assert ru.fail_closed is True


def test_no_reproof_downgrade_on_unexpected() -> None:
    base = _digests()
    cand = _digests(ru=_SHA_C)
    report = compare_protected_semantic_digests(baseline=base, candidate=cand)
    assert resolve_reproof_class(report) is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF


def test_reproof_class_mapping_closed() -> None:
    assert (
        reproof_class_for_verdict(DigestVerdict.DIGEST_CHANGED_UNEXPECTED)
        is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    )
    assert (
        reproof_class_for_verdict(DigestVerdict.DIGEST_CHANGED_EXPECTED)
        is FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION
    )


def test_comparator_integration_pass() -> None:
    comp = ProtectedSemanticComparatorV1()
    from src.evaluation.golden_vectors.contracts.validation import parse_domain_evaluation_result_v1

    stub = parse_domain_evaluation_result_v1(
        {
            "domain": "ranking_universe",
            "verdict": "PASS",
            "metrics": [],
            "invariants": [],
            "boundary_results": [],
            "evidence_refs": [],
        }
    )
    d = _digests()
    delta, merged = comp.compare(
        baseline=stub,
        candidate=stub,
        baseline_digests=d,
        candidate_digests=d,
    )
    assert delta.deltas
    assert merged.ranking_universe.verdict is DigestVerdict.DIGEST_EQUAL


def test_runner_fail_closed_on_unexpected_drift() -> None:
    from src.evaluation.golden_vectors.contracts.validation import (
        parse_domain_evaluation_context_v1,
    )
    from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
        DeterministicDomainEvaluatorV1,
        DeterministicDeltaBuilderV1,
        DeterministicEvidenceBuilderV1,
        DeterministicPostGateV1,
        DeterministicPreGateV1,
        DeterministicReplayAdapterV1,
    )
    from src.evaluation.golden_vectors.digest.comparator_v1 import ProtectedSemanticComparatorV1
    from src.evaluation.golden_vectors.registry.evidence_registry_v1 import GvefEvidenceRegistryV1
    from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
        GvefRunRequestV1,
        GvefRunnerDependenciesV1,
    )

    ctx = parse_domain_evaluation_context_v1(domain_context())
    ctx_dict = ctx.model_dump(mode="json", by_alias=True)
    ctx_dict["protected_digest_baseline"] = protected_digests()
    ctx2 = parse_domain_evaluation_context_v1(ctx_dict)

    class DriftEvaluator(DeterministicDomainEvaluatorV1):
        def protected_digests_candidate(self, *, context):  # type: ignore[override]
            return _digests(ru=_SHA_C, sel=_SHA_B)

        def protected_digests_baseline(self, *, context):  # type: ignore[override]
            return _digests()

    record = GenericRunnerV1().execute(
        GvefRunRequestV1(ctx2),
        GvefRunnerDependenciesV1(
            pre_gate=DeterministicPreGateV1(),
            post_gate=DeterministicPostGateV1(),
            replay_adapter=DeterministicReplayAdapterV1(),
            evaluator=DriftEvaluator(),
            comparator=ProtectedSemanticComparatorV1(),
            delta_builder=DeterministicDeltaBuilderV1(),
            evidence_builder=DeterministicEvidenceBuilderV1(),
            registry=GvefEvidenceRegistryV1(),
        ),
        verify_deterministic_replay=False,
    )
    assert record.state is RunnerState.FAILED
    assert record.failure_classification is FailureClassification.PROTECTED_DIGEST_DRIFT
    assert record.fan_out_evaluation_class is FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF


def test_bwp0d_no_productive_side_effects_in_module() -> None:
    root = Path("src/evaluation/golden_vectors/digest")
    forbidden = (
        "requests.post",
        "keychain",
        "subprocess",
        "live_",
        "testnet",
        "promotion_decision",
    )
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        src = ast.dump(tree).lower()
        for token in forbidden:
            assert token not in src, f"{path.name} must not reference {token}"


def test_component_and_bwp_ids() -> None:
    assert BWP_ID == "BWP-0D"
    assert COMPONENT_ID == "gvef.protected_semantic_digest_layer_v1"
