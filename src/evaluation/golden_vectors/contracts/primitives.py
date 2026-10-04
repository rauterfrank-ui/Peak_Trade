"""Shared nested GVEF contract primitives."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.evaluation.golden_vectors.contracts.enums import CurrentReachabilityVerdict
from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError
from src.evaluation.golden_vectors.contracts.serialization import (
    require_git_sha,
    require_sha256_hex,
    require_semver,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProvenanceRecordV1(_StrictModel):
    source: str
    ref: str | None = None


class PopulationSelectorV1(_StrictModel):
    selector_id: str
    binding_digest: str

    @field_validator("binding_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="population_selector.binding_digest")


class ArtifactIdentityV1(_StrictModel):
    artifact_ref: str
    digest: str

    @field_validator("digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="artifact_identity.digest")


class ConfigIdentityV1(_StrictModel):
    config_path: str
    config_digest: str

    @field_validator("config_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="config_identity.config_digest")


class DataManifestV1(_StrictModel):
    data_manifest_id: str
    data_digest: str

    @field_validator("data_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="data_manifest.data_digest")


class SeedSetV1(_StrictModel):
    seeds: list[int]
    seed_set_digest: str

    @field_validator("seed_set_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="seed_set.seed_set_digest")


class ReplayTraceV1(_StrictModel):
    trace_schema_version: str
    trace_digest: str
    entries: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("trace_schema_version")
    @classmethod
    def _semver(cls, v: str) -> str:
        return require_semver(v, field="replay_trace.trace_schema_version")

    @field_validator("trace_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        return require_sha256_hex(v, field="replay_trace.trace_digest")


class ConstraintRowV1(_StrictModel):
    SIGNAL_EDGE: str
    DOMAIN: str
    PRODUCER: str
    CONSUMER: str
    CONTRACT: str
    ALLOWED_DIRECTION: str
    FORBIDDEN_DIRECTION: str
    AUTHORITY_OWNER: str
    REQUIRED_CURRENT_VERDICT: CurrentReachabilityVerdict
    PRODUCTIVE_REACHABILITY: CurrentReachabilityVerdict
    FAILURE_ACTION: str
    EVIDENCE_PROVENANCE: str


class InstrumentMembershipV1(_StrictModel):
    instrument_id: str


class RankEntryV1(_StrictModel):
    instrument_id: str
    rank: int


class DecisionDeltaV1(_StrictModel):
    delta_id: str
    before: str | None = None
    after: str | None = None


class MembershipDeltaV1(_StrictModel):
    instrument_id: str
    action: str


class OrderDeltaV1(_StrictModel):
    instrument_id: str
    before_rank: int | None = None
    after_rank: int | None = None


class MetricValueValidator:
    @staticmethod
    def validate_metric_value(value: int | str, *, field: str) -> int | str:
        if isinstance(value, bool):
            raise GvefSchemaError(f"{field} must not be bool", field=field)
        if isinstance(value, float):
            raise GvefSchemaError(f"{field} float forbidden", field=field)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return value
        raise GvefSchemaError(f"{field} must be int or str", field=field)


class GitShaField:
    @staticmethod
    def validate(value: str, *, field: str) -> str:
        return require_git_sha(value, field=field)
