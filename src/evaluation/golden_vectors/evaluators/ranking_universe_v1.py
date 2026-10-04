"""BWP-3-RU Ranking Universe domain evaluator (observation only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.evaluation.golden_vectors.contracts.enums import (
    EvaluationDomain,
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import (
    DomainEvaluationContextV1,
    DomainEvaluationResultV1,
    InvariantResultV1,
    MetricResultV1,
    ProtectedDigestEntryV1,
    ProtectedSemanticDigestsV1,
    RankingDeltaManifestV1,
    RankingUniverseManifestV1,
    ReplayTraceV1,
    contract_digest_hex,
    contract_to_canonical_mapping,
)
from src.evaluation.golden_vectors.contracts.primitives import (
    InstrumentMembershipV1,
    MembershipDeltaV1,
    ProvenanceRecordV1,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
from src.evaluation.golden_vectors.evaluators._fanout_v1 import bwp3_failure_fan_out
from src.evaluation.golden_vectors.evaluators._result_v1 import fail_result, pass_result
from src.evaluation.golden_vectors.evaluators.ru_owners_v1 import CAP2_3_SELECTION_OWNER

RANKING_UNIVERSE_EVALUATOR_ID = "ranking_universe_evaluator_v1"
EVALUATOR_SCHEMA_VERSION = "1.5.0"
BWP_ID = "BWP-3-RU"
PRIMARY_FAILURE_CLASS = FailureClassification.AUTHORITY_FAILURE
REPROOF_CLASS = FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION


@dataclass
class RankingUniverseEvaluatorV1:
    """Ranking Universe metrics only. Must not mutate Selection."""

    evaluator_id: str = RANKING_UNIVERSE_EVALUATOR_ID
    schema_version: str = EVALUATOR_SCHEMA_VERSION
    _baseline_membership: list[str] | None = field(default=None, init=False)
    _baseline_ru_digest: str | None = field(default=None, init=False)
    _candidate_ru_digest: str | None = field(default=None, init=False)

    def evaluate_baseline(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        auth_err = self._authority_violation(replay)
        if auth_err:
            return fail_result(
                domain=EvaluationDomain.RANKING_UNIVERSE,
                failure=FailureClassification.AUTHORITY_FAILURE,
                detail=auth_err,
            )
        membership, err = self._membership(replay, label="baseline")
        if err:
            return fail_result(
                domain=EvaluationDomain.RANKING_UNIVERSE,
                failure=FailureClassification.AUTHORITY_FAILURE,
                detail=err,
            )
        self._baseline_membership = list(membership)
        manifest = self._manifest(membership, snapshot_id="ru-baseline")
        self._baseline_ru_digest = sha256_hex(contract_to_canonical_mapping(manifest))
        return self._pass(manifest, None, membership, label="baseline")

    def evaluate_candidate(
        self, *, context: DomainEvaluationContextV1, replay: ReplayTraceV1
    ) -> DomainEvaluationResultV1:
        auth_err = self._authority_violation(replay)
        if auth_err:
            return fail_result(
                domain=EvaluationDomain.RANKING_UNIVERSE,
                failure=FailureClassification.AUTHORITY_FAILURE,
                detail=auth_err,
            )
        membership, err = self._membership(replay, label="candidate")
        if err:
            return fail_result(
                domain=EvaluationDomain.RANKING_UNIVERSE,
                failure=FailureClassification.AUTHORITY_FAILURE,
                detail=err,
            )
        if self._baseline_membership is None:
            return fail_result(
                domain=EvaluationDomain.RANKING_UNIVERSE,
                failure=FailureClassification.AUTHORITY_FAILURE,
                detail="baseline not evaluated",
            )
        manifest = self._manifest(membership, snapshot_id="ru-candidate")
        delta = self._delta(self._baseline_membership, membership)
        self._candidate_ru_digest = sha256_hex(contract_to_canonical_mapping(manifest))
        return self._pass(manifest, delta, membership, label="candidate")

    def protected_digests_baseline(
        self, *, context: DomainEvaluationContextV1
    ) -> ProtectedSemanticDigestsV1:
        digest = (
            self._baseline_ru_digest
            or context.protected_digest_baseline.ranking_universe.digest_hex
        )
        return self._digests(context, ru_digest=digest)

    def protected_digests_candidate(
        self, *, context: DomainEvaluationContextV1
    ) -> ProtectedSemanticDigestsV1:
        digest = (
            self._candidate_ru_digest
            or self._baseline_ru_digest
            or context.protected_digest_baseline.ranking_universe.digest_hex
        )
        return self._digests(context, ru_digest=digest)

    def failure_fan_out(self, failure: FailureClassification) -> FanOutEvaluationClass:
        return bwp3_failure_fan_out(failure)

    def _authority_violation(self, replay: ReplayTraceV1) -> str | None:
        for entry in replay.entries:
            if entry.get("selection_mutation") is True:
                return "selection mutation attempted"
            if entry.get("claims_cap23_ownership") is True:
                return "Cap2.3 ownership claim forbidden"
            if entry.get("selected_future_write"):
                return "selected-future write forbidden"
            if entry.get("binding_mutation") is True:
                return "binding mutation forbidden"
            if entry.get("collapse_ru_selection_digest") is True:
                return "RU/Selection digest collapse forbidden"
        return None

    def _membership(self, replay: ReplayTraceV1, *, label: str) -> tuple[list[str], str | None]:
        for entry in replay.entries:
            if entry.get("kind") != "ranking_universe":
                continue
            if entry.get("label") not in (None, label):
                continue
            raw = entry.get("membership")
            if not isinstance(raw, list) or not all(isinstance(x, str) for x in raw):
                return [], "malformed ranking universe membership"
            return list(raw), None
        return [], "missing ranking universe evidence"

    def _manifest(self, membership: list[str], *, snapshot_id: str) -> RankingUniverseManifestV1:
        return RankingUniverseManifestV1(
            membership=[InstrumentMembershipV1(instrument_id=m) for m in membership],
            ranking_snapshot_id=snapshot_id,
            provenance=ProvenanceRecordV1(source="gvef.evaluator", ref=snapshot_id),
        )

    def _delta(self, baseline: list[str], candidate: list[str]) -> RankingDeltaManifestV1:
        base_set = set(baseline)
        cand_set = set(candidate)
        membership_deltas: list[MembershipDeltaV1] = []
        for inst in sorted(cand_set - base_set):
            membership_deltas.append(MembershipDeltaV1(instrument_id=inst, action="added"))
        for inst in sorted(base_set - cand_set):
            membership_deltas.append(MembershipDeltaV1(instrument_id=inst, action="removed"))
        delta_body: dict[str, Any] = {}
        if membership_deltas:
            delta_body["membership_deltas"] = [
                contract_to_canonical_mapping(d) for d in membership_deltas
            ]
        return RankingDeltaManifestV1(
            membership_deltas=membership_deltas or None,
            digest=sha256_hex(delta_body),
        )

    def _pass(
        self,
        manifest: RankingUniverseManifestV1,
        delta: RankingDeltaManifestV1 | None,
        membership: list[str],
        *,
        label: str,
    ) -> DomainEvaluationResultV1:
        ru_digest = sha256_hex(contract_to_canonical_mapping(manifest))
        semantic: dict[str, Any] = {
            "ranking_universe_manifest": contract_to_canonical_mapping(manifest),
            "ranking_universe_digest": ru_digest,
        }
        if delta is not None:
            semantic["ranking_delta_manifest"] = contract_to_canonical_mapping(delta)
        return pass_result(
            domain=EvaluationDomain.RANKING_UNIVERSE,
            metrics=[
                MetricResultV1(metric_id="ru.membership_count", value=len(membership)),
                MetricResultV1(metric_id="ru.digest", value=ru_digest),
            ],
            invariants=[
                InvariantResultV1(
                    invariant_id="ru.not_selection",
                    pass_=True,
                    detail="RANKING_UNIVERSE_IS_NOT_SELECTION",
                )
            ],
            boundary_results=[],
            evidence_refs=[f"evidence/ru/{label}"],
            semantic_digest_deltas=semantic,
        )

    def _digests(
        self, context: DomainEvaluationContextV1, *, ru_digest: str
    ) -> ProtectedSemanticDigestsV1:
        base = context.protected_digest_baseline
        sel = base.selection
        if ru_digest == sel.digest_hex:
            raise ValueError("RU/Selection digest collapse")
        return ProtectedSemanticDigestsV1(
            ranking_universe=ProtectedDigestEntryV1(digest_hex=ru_digest, schema_version="1.0.0"),
            selection=sel,
        )


def ru_protected_output_digest(result: DomainEvaluationResultV1) -> str:
    return contract_digest_hex(result)
