"""GVEF BWP-0D protected semantic digest compute/compare (AUTHORITY=NONE)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.evaluation.golden_vectors.contracts.enums import (
    DigestVerdict,
    FailureClassification,
    FanOutEvaluationClass,
    ProtectedDomain,
)
from src.evaluation.golden_vectors.contracts.models import (
    ProtectedDigestEntryV1,
    ProtectedSemanticDigestsV1,
    contract_to_canonical_mapping,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
from src.evaluation.golden_vectors.digest.errors import GvefProtectedDigestDriftError

BWP_ID = "BWP-0D"
COMPONENT_ID = "gvef.protected_semantic_digest_layer_v1"
PRIMARY_FAILURE_CLASS = FailureClassification.PROTECTED_DIGEST_DRIFT
UNEXPECTED_REPROOF_CLASS = FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF

# contract_schema_manifest.json / V1.5 digest model
EXCLUDED_VOLATILE_FIELDS = frozenset(
    {"created_at_utc", "runner_host", "process_id", "timestamp_utc"}
)

_FAIL_CLOSED_VERDICTS = frozenset(
    {
        DigestVerdict.DIGEST_CHANGED_UNEXPECTED,
        DigestVerdict.DIGEST_UNAVAILABLE,
        DigestVerdict.DIGEST_CONFLICTING,
    }
)


def project_semantic_payload(
    payload: Mapping[str, Any],
    *,
    exclude: frozenset[str] = EXCLUDED_VOLATILE_FIELDS,
) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k not in exclude}


def semantic_payload_digest_hex(
    payload: Mapping[str, Any],
    *,
    exclude: frozenset[str] = EXCLUDED_VOLATILE_FIELDS,
) -> str:
    """SHA-256 over canonical JSON with sorted keys (volatile fields stripped)."""
    return sha256_hex(project_semantic_payload(payload, exclude=exclude))


def protected_semantic_digests_aggregate_hex(digests: ProtectedSemanticDigestsV1) -> str:
    return sha256_hex(contract_to_canonical_mapping(digests))


def enforce_ranking_universe_selection_separation(digests: ProtectedSemanticDigestsV1) -> None:
    if digests.ranking_universe.digest_hex == digests.selection.digest_hex:
        raise GvefProtectedDigestDriftError(
            "ranking_universe and selection digests must remain separate (Cap2.3 invariant)",
            verdict=DigestVerdict.DIGEST_CONFLICTING,
            reproof_class=UNEXPECTED_REPROOF_CLASS,
            domain=ProtectedDomain.RANKING_UNIVERSE.value,
        )


def reproof_class_for_verdict(verdict: DigestVerdict) -> FanOutEvaluationClass:
    if verdict is DigestVerdict.DIGEST_CHANGED_UNEXPECTED:
        return FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    if verdict is DigestVerdict.DIGEST_CONFLICTING:
        return FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    if verdict is DigestVerdict.DIGEST_UNAVAILABLE:
        return FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    if verdict is DigestVerdict.DIGEST_CHANGED_EXPECTED:
        return FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION
    return FanOutEvaluationClass.LOCAL_EVALUATION


def compare_digest_hex(
    *,
    baseline_hex: str,
    candidate_hex: str,
    expected_change: bool,
) -> DigestVerdict:
    if baseline_hex == candidate_hex:
        return DigestVerdict.DIGEST_EQUAL
    if expected_change:
        return DigestVerdict.DIGEST_CHANGED_EXPECTED
    return DigestVerdict.DIGEST_CHANGED_UNEXPECTED


def compare_digest_entry(
    *,
    domain: ProtectedDomain,
    baseline: ProtectedDigestEntryV1 | None,
    candidate: ProtectedDigestEntryV1 | None,
    expected_change: bool,
) -> DigestVerdict:
    if baseline is None or candidate is None:
        return DigestVerdict.DIGEST_UNAVAILABLE
    if baseline.verdict is DigestVerdict.DIGEST_CONFLICTING:
        return DigestVerdict.DIGEST_CONFLICTING
    if candidate.verdict is DigestVerdict.DIGEST_CONFLICTING:
        return DigestVerdict.DIGEST_CONFLICTING
    verdict = compare_digest_hex(
        baseline_hex=baseline.digest_hex,
        candidate_hex=candidate.digest_hex,
        expected_change=expected_change,
    )
    _ = domain
    return verdict


@dataclass(frozen=True)
class DomainDigestComparisonV1:
    domain: ProtectedDomain
    verdict: DigestVerdict
    fail_closed: bool
    reproof_class: FanOutEvaluationClass


@dataclass(frozen=True)
class ProtectedDigestComparisonReportV1:
    comparisons: tuple[DomainDigestComparisonV1, ...]
    worst_verdict: DigestVerdict
    worst_reproof_class: FanOutEvaluationClass
    fail_closed: bool


def _optional_entry(
    digests: ProtectedSemanticDigestsV1, domain: ProtectedDomain
) -> ProtectedDigestEntryV1 | None:
    return getattr(digests, domain.value, None)


def compare_protected_semantic_digests(
    *,
    baseline: ProtectedSemanticDigestsV1,
    candidate: ProtectedSemanticDigestsV1,
    expected_changed_domains: frozenset[ProtectedDomain] | None = None,
) -> ProtectedDigestComparisonReportV1:
    enforce_ranking_universe_selection_separation(baseline)
    enforce_ranking_universe_selection_separation(candidate)
    expected = expected_changed_domains or frozenset()
    domains = (
        ProtectedDomain.RANKING_UNIVERSE,
        ProtectedDomain.SELECTION,
        ProtectedDomain.MV2,
        ProtectedDomain.DP,
        ProtectedDomain.CONFIRMATION,
        ProtectedDomain.SIDESTATE,
        ProtectedDomain.ENTRY_EXIT,
        ProtectedDomain.SCOPE,
        ProtectedDomain.CRS,
        ProtectedDomain.SIZING,
        ProtectedDomain.ADMISSION,
        ProtectedDomain.VENUE_PLAN,
    )
    comparisons: list[DomainDigestComparisonV1] = []
    worst = DigestVerdict.DIGEST_EQUAL
    worst_reproof = FanOutEvaluationClass.LOCAL_EVALUATION
    any_fail = False

    for domain in domains:
        b_entry = _optional_entry(baseline, domain)
        c_entry = _optional_entry(candidate, domain)
        if domain not in (ProtectedDomain.RANKING_UNIVERSE, ProtectedDomain.SELECTION):
            if b_entry is None and c_entry is None:
                continue
        verdict = compare_digest_entry(
            domain=domain,
            baseline=b_entry,
            candidate=c_entry,
            expected_change=domain in expected,
        )
        fc = verdict in _FAIL_CLOSED_VERDICTS
        reproof = reproof_class_for_verdict(verdict)
        comparisons.append(
            DomainDigestComparisonV1(
                domain=domain,
                verdict=verdict,
                fail_closed=fc,
                reproof_class=reproof,
            )
        )
        if fc:
            any_fail = True
        if verdict is not DigestVerdict.DIGEST_EQUAL and worst is DigestVerdict.DIGEST_EQUAL:
            worst = verdict
            worst_reproof = reproof
        elif verdict in _FAIL_CLOSED_VERDICTS and worst not in _FAIL_CLOSED_VERDICTS:
            worst = verdict
            worst_reproof = reproof
        elif (
            verdict is DigestVerdict.DIGEST_CHANGED_UNEXPECTED
            and worst is not DigestVerdict.DIGEST_CONFLICTING
        ):
            worst = verdict
            worst_reproof = reproof

    return ProtectedDigestComparisonReportV1(
        comparisons=tuple(comparisons),
        worst_verdict=worst,
        worst_reproof_class=worst_reproof,
        fail_closed=any_fail,
    )


def raise_if_fail_closed(report: ProtectedDigestComparisonReportV1) -> None:
    for row in report.comparisons:
        if not row.fail_closed:
            continue
        raise GvefProtectedDigestDriftError(
            f"protected digest fail-closed: {row.domain.value} -> {row.verdict.value}",
            verdict=row.verdict,
            reproof_class=row.reproof_class,
            domain=row.domain.value,
        )


def apply_verdicts(
    candidate: ProtectedSemanticDigestsV1,
    report: ProtectedDigestComparisonReportV1,
) -> ProtectedSemanticDigestsV1:
    updates: dict[str, Any] = contract_to_canonical_mapping(candidate)
    for row in report.comparisons:
        key = row.domain.value
        if key not in updates or updates[key] is None:
            continue
        entry = dict(updates[key])
        entry["verdict"] = row.verdict.value
        updates[key] = entry
    return ProtectedSemanticDigestsV1.model_validate(updates)


def resolve_reproof_class(report: ProtectedDigestComparisonReportV1) -> FanOutEvaluationClass:
    """Never downgrade ambiguous/unexpected protected drift below WHOLE_SYSTEM."""
    classes = {row.reproof_class for row in report.comparisons if row.fail_closed}
    if FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF in classes:
        return FanOutEvaluationClass.WHOLE_SYSTEM_REPROOF
    if FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION in classes:
        return FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION
    return report.worst_reproof_class
