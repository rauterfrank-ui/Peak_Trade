"""GVEF comparator using protected semantic digest layer (BWP-0D)."""

from __future__ import annotations

from dataclasses import dataclass

from src.evaluation.golden_vectors.contracts.enums import ProtectedDomain
from src.evaluation.golden_vectors.contracts.models import (
    DecisionDeltaManifestV1,
    DecisionDeltaV1,
    DomainEvaluationResultV1,
    ProtectedSemanticDigestsV1,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
from src.evaluation.golden_vectors.digest.errors import GvefProtectedDigestDriftError
from src.evaluation.golden_vectors.digest.protected_semantic_digest_layer_v1 import (
    apply_verdicts,
    compare_protected_semantic_digests,
    raise_if_fail_closed,
    resolve_reproof_class,
)

BWP_ID = "BWP-0D"


@dataclass(frozen=True)
class ProtectedSemanticComparatorV1:
    """Baseline vs candidate protected digest comparison (AUTHORITY=NONE)."""

    expected_changed_domains: frozenset[ProtectedDomain] = frozenset()

    def compare(
        self,
        *,
        baseline: DomainEvaluationResultV1,
        candidate: DomainEvaluationResultV1,
        baseline_digests: ProtectedSemanticDigestsV1,
        candidate_digests: ProtectedSemanticDigestsV1,
    ) -> tuple[DecisionDeltaManifestV1, ProtectedSemanticDigestsV1]:
        _ = (baseline, candidate)
        report = compare_protected_semantic_digests(
            baseline=baseline_digests,
            candidate=candidate_digests,
            expected_changed_domains=self.expected_changed_domains,
        )
        raise_if_fail_closed(report)
        merged = apply_verdicts(candidate_digests, report)
        delta_body = {
            "protected_digest_comparisons": [
                {
                    "domain": row.domain.value,
                    "verdict": row.verdict.value,
                    "reproof_class": row.reproof_class.value,
                }
                for row in report.comparisons
            ],
            "worst_reproof_class": resolve_reproof_class(report).value,
        }
        delta = DecisionDeltaManifestV1(
            deltas=[
                DecisionDeltaV1(
                    delta_id="protected_semantic_digest_layer_v1",
                    before=baseline_digests.ranking_universe.digest_hex,
                    after=candidate_digests.ranking_universe.digest_hex,
                )
            ],
            digest=sha256_hex(delta_body),
        )
        return delta, merged

    def compare_or_fail_with_reproof(
        self,
        *,
        baseline_digests: ProtectedSemanticDigestsV1,
        candidate_digests: ProtectedSemanticDigestsV1,
    ) -> tuple[ProtectedSemanticDigestsV1, GvefProtectedDigestDriftError | None]:
        report = compare_protected_semantic_digests(
            baseline=baseline_digests,
            candidate=candidate_digests,
            expected_changed_domains=self.expected_changed_domains,
        )
        try:
            raise_if_fail_closed(report)
        except GvefProtectedDigestDriftError as exc:
            return candidate_digests, exc
        return apply_verdicts(candidate_digests, report), None
