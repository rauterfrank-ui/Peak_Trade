"""GVEF V1.5 typed contracts (16 normative schemas)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.evaluation.golden_vectors.contracts.enums import (
    CurrentReachabilityVerdict,
    DigestVerdict,
    DomainEvaluatorId,
    DomainVerdict,
    EvaluationDomain,
    ExternalPromotionStatus,
    FailureClassification,
    FanOutEvaluationClass,
    PassRejectVerdict,
    ProtectedDomain,
    VectorClass,
)
from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError
from src.evaluation.golden_vectors.contracts.primitives import (
    ArtifactIdentityV1,
    ConfigIdentityV1,
    ConstraintRowV1,
    DataManifestV1,
    DecisionDeltaV1,
    InstrumentMembershipV1,
    MembershipDeltaV1,
    MetricValueValidator,
    OrderDeltaV1,
    PopulationSelectorV1,
    ProvenanceRecordV1,
    RankEntryV1,
    ReplayTraceV1,
    SeedSetV1,
    GitShaField,
)
from src.evaluation.golden_vectors.contracts.serialization import (
    canonical_json_bytes,
    require_iso8601_utc_z,
    require_semver,
    require_sha256_hex,
    require_uuid_v4,
    sha256_hex,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MetricResultV1(_StrictModel):
    metric_id: str
    value: int | str
    unit: str | None = None
    baseline_value: int | str | None = None

    @field_validator("value")
    @classmethod
    def _value(cls, v: int | str) -> int | str:
        return MetricValueValidator.validate_metric_value(v, field="metric_id.value")

    @field_validator("baseline_value")
    @classmethod
    def _baseline(cls, v: int | str | None) -> int | str | None:
        if v is None:
            return None
        return MetricValueValidator.validate_metric_value(v, field="metric_id.baseline_value")


class InvariantResultV1(_StrictModel):
    invariant_id: str
    pass_: bool = Field(alias="pass")
    detail: str | None = None

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class BoundaryResultV1(_StrictModel):
    edge_id: str
    pass_: bool = Field(alias="pass")
    producer: str
    consumer: str
    current_verdict: CurrentReachabilityVerdict

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ProtectedDigestEntryV1(_StrictModel):
    digest_hex: str
    schema_version: str
    verdict: DigestVerdict | None = None

    @field_validator("digest_hex")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="digest_hex")

    @field_validator("schema_version")
    @classmethod
    def _semver(cls, v: str) -> str:
        return require_semver(v, field="schema_version")


class ProtectedDigestManifestV1(_StrictModel):
    domain: ProtectedDomain
    digest_hex: str
    schema_version: str
    verdict: DigestVerdict

    @field_validator("digest_hex")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="digest_hex")

    @field_validator("schema_version")
    @classmethod
    def _semver(cls, v: str) -> str:
        return require_semver(v, field="schema_version")


class ProtectedSemanticDigestsV1(_StrictModel):
    """Separate digest domains; ranking_universe and selection MUST NOT be merged."""

    ranking_universe: ProtectedDigestEntryV1
    selection: ProtectedDigestEntryV1
    mv2: ProtectedDigestEntryV1 | None = None
    dp: ProtectedDigestEntryV1 | None = None
    confirmation: ProtectedDigestEntryV1 | None = None
    sidestate: ProtectedDigestEntryV1 | None = None
    entry_exit: ProtectedDigestEntryV1 | None = None
    scope: ProtectedDigestEntryV1 | None = None
    crs: ProtectedDigestEntryV1 | None = None
    sizing: ProtectedDigestEntryV1 | None = None
    admission: ProtectedDigestEntryV1 | None = None
    venue_plan: ProtectedDigestEntryV1 | None = None


class DecisionDeltaManifestV1(_StrictModel):
    deltas: list[DecisionDeltaV1]
    digest: str

    @field_validator("digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="digest")


class RankingUniverseManifestV1(_StrictModel):
    membership: list[InstrumentMembershipV1]
    ranking_snapshot_id: str | None = None
    ordering: list[RankEntryV1] | None = None
    top_k_context: dict[str, Any] | None = None
    provenance: ProvenanceRecordV1


class RankingDeltaManifestV1(_StrictModel):
    membership_deltas: list[MembershipDeltaV1] | None = None
    ordering_deltas: list[OrderDeltaV1] | None = None
    churn_metrics: dict[str, Any] | None = None
    digest: str

    @field_validator("digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="digest")


class CapitalRiskCrsSizingEvidenceBundleV1(_StrictModel):
    crs_state_digest: str | None = None
    sizing_verdict: PassRejectVerdict | None = None
    admission_verdict: PassRejectVerdict | None = None
    capital_context_provenance: ProvenanceRecordV1 | None = None
    risk_context_provenance: ProvenanceRecordV1 | None = None
    exposure_invariants: list[InvariantResultV1] | None = None

    @field_validator("crs_state_digest")
    @classmethod
    def _crs_digest(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return require_sha256_hex(v, field="crs_state_digest")


class RunManifestV1(_StrictModel):
    run_id: str
    experiment_id: str
    baseline_sha: str
    candidate_sha: str
    domain_evaluator_id: DomainEvaluatorId
    corpus_manifest_ref: str
    constraint_matrix_version: str
    constraint_matrix_digest: str
    seed_set_digest: str
    fan_out_evaluation_class: FanOutEvaluationClass
    created_at_utc: str

    @field_validator("run_id")
    @classmethod
    def _run_id(cls, v: str) -> str:
        return require_uuid_v4(v, field="run_id")

    @field_validator("baseline_sha", "candidate_sha")
    @classmethod
    def _git_sha(cls, v: str) -> str:
        return GitShaField.validate(v, field="baseline_sha")

    @field_validator("constraint_matrix_version")
    @classmethod
    def _semver(cls, v: str) -> str:
        return require_semver(v, field="constraint_matrix_version")

    @field_validator("constraint_matrix_digest", "seed_set_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="constraint_matrix_digest")

    @field_validator("created_at_utc")
    @classmethod
    def _ts(cls, v: str) -> str:
        return require_iso8601_utc_z(v, field="created_at_utc")


class VectorManifestV1(_StrictModel):
    vector_id: str
    vector_class: VectorClass
    schema_version: str
    population_selector: PopulationSelectorV1
    invariant_ids: list[str]
    expected_dispositions: list[str] | None = None
    provenance: ProvenanceRecordV1

    @field_validator("schema_version")
    @classmethod
    def _semver(cls, v: str) -> str:
        return require_semver(v, field="schema_version")


class CorpusManifestV1(_StrictModel):
    corpus_version: str
    corpus_digest: str
    vector_ids: list[str]
    metric_schema_version: str
    seed_set: list[int]
    provenance: ProvenanceRecordV1

    @field_validator("corpus_version", "metric_schema_version")
    @classmethod
    def _semver(cls, v: str) -> str:
        return require_semver(v, field="corpus_version")

    @field_validator("corpus_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="corpus_digest")


class ConstraintMatrixV1(_StrictModel):
    matrix_version: str
    matrix_digest: str
    rows: list[ConstraintRowV1]
    baseline_sha: str

    @field_validator("matrix_version")
    @classmethod
    def _semver(cls, v: str) -> str:
        return require_semver(v, field="matrix_version")

    @field_validator("matrix_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="matrix_digest")

    @field_validator("baseline_sha")
    @classmethod
    def _git(cls, v: str) -> str:
        return GitShaField.validate(v, field="baseline_sha")


class DomainEvaluationContextV1(_StrictModel):
    run_manifest: RunManifestV1
    baseline_identity: ArtifactIdentityV1
    candidate_identity: ArtifactIdentityV1
    corpus_identity: CorpusManifestV1
    config_identity: ConfigIdentityV1
    data_identity: DataManifestV1
    seed_identity: SeedSetV1
    constraint_identity: ConstraintMatrixV1
    protected_digest_baseline: ProtectedSemanticDigestsV1
    replay_trace: ReplayTraceV1


class DomainEvaluationResultV1(_StrictModel):
    domain: EvaluationDomain
    verdict: DomainVerdict
    metrics: list[MetricResultV1]
    invariants: list[InvariantResultV1]
    boundary_results: list[BoundaryResultV1]
    decision_deltas: DecisionDeltaManifestV1 | None = None
    semantic_digest_deltas: dict[str, Any] | None = None
    evidence_refs: list[str]
    failure_classification: FailureClassification | None = None


class EvidenceBundleV1(_StrictModel):
    run_id: str
    experiment_id: str
    baseline_sha: str
    candidate_sha: str
    constraint_matrix_version: str
    constraint_matrix_digest: str
    vector_corpus_version: str
    vector_corpus_digest: str
    protected_semantic_digests: ProtectedSemanticDigestsV1
    config_digest: str
    config_provenance: ProvenanceRecordV1
    data_manifest: DataManifestV1
    data_provenance: ProvenanceRecordV1
    seed_set: list[int]
    metric_schema_version: str
    invariant_results: list[InvariantResultV1]
    authority_boundary_results: list[BoundaryResultV1]
    decision_delta_manifest: DecisionDeltaManifestV1
    ranking_universe_manifest: RankingUniverseManifestV1 | None = None
    ranking_delta_manifest: RankingDeltaManifestV1 | None = None
    fan_out_evaluation_class: FanOutEvaluationClass
    capital_risk_crs_sizing_evidence_bundle: CapitalRiskCrsSizingEvidenceBundleV1 | None = None
    evidence_digest: str
    promotion_status: ExternalPromotionStatus
    post_constraint_gate_pass: bool
    failure_classification: FailureClassification | None = None

    @field_validator("run_id")
    @classmethod
    def _run_id(cls, v: str) -> str:
        return require_uuid_v4(v, field="run_id")

    @field_validator(
        "baseline_sha",
        "candidate_sha",
    )
    @classmethod
    def _git(cls, v: str) -> str:
        return GitShaField.validate(v, field="baseline_sha")

    @field_validator(
        "constraint_matrix_digest",
        "vector_corpus_digest",
        "config_digest",
        "evidence_digest",
    )
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="digest")

    @field_validator(
        "constraint_matrix_version",
        "vector_corpus_version",
        "metric_schema_version",
    )
    @classmethod
    def _semver(cls, v: str) -> str:
        return require_semver(v, field="semver")

    @model_validator(mode="after")
    def _ru_selection_separate(self) -> EvidenceBundleV1:
        ru = self.protected_semantic_digests.ranking_universe.digest_hex
        sel = self.protected_semantic_digests.selection.digest_hex
        if ru == sel:
            raise GvefSchemaError(
                "ranking_universe and selection digests must remain distinct",
                field="protected_semantic_digests",
            )
        return self


class PromotionEvidenceEnvelopeV1(_StrictModel):
    evidence_bundle_ref: str
    evidence_digest: str
    governance_handoff_timestamp: str
    post_constraint_gate_pass: bool
    fan_out_evaluation_class: FanOutEvaluationClass

    @field_validator("evidence_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="evidence_digest")

    @field_validator("governance_handoff_timestamp")
    @classmethod
    def _ts(cls, v: str) -> str:
        return require_iso8601_utc_z(v, field="governance_handoff_timestamp")

    @model_validator(mode="after")
    def _handoff_requires_post_gate(self) -> PromotionEvidenceEnvelopeV1:
        if self.post_constraint_gate_pass is not True:
            raise GvefSchemaError(
                "post_constraint_gate_pass must be true for promotion envelope",
                field="post_constraint_gate_pass",
            )
        return self


def contract_to_canonical_mapping(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json", by_alias=True, exclude_none=False)


def contract_canonical_bytes(model: BaseModel) -> bytes:
    payload = contract_to_canonical_mapping(model)
    return canonical_json_bytes(payload)


def contract_digest_hex(model: BaseModel, *, exclude_fields: frozenset[str] | None = None) -> str:
    payload = contract_to_canonical_mapping(model)
    if exclude_fields:
        for key in exclude_fields:
            payload.pop(key, None)
    return sha256_hex(payload)
