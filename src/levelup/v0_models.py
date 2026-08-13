"""
Typed v0 contracts for Level-Up work units (Evidence-first roadmap alignment).

These types do not perform live trading, broker I/O, or unlock gates — they describe
slice metadata and pointers to under-repo evidence directories (typically ``out/ops/``).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import re
from typing import Any, Literal, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.experiments.cross_lane_identity_join_v1 import CrossLaneIdentityJoinV1
from src.levelup.i52_levelup_named_lane_identity_join_v1 import (
    join_i52_named_lane_identity_v1,
)

_SCHEMA = "levelup/manifest/v0"
_EVIDENCE_PREFIX = "out/ops/"
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/]*$")


class EvidenceBundleRefV0(BaseModel):
    """Reference to an evidence bundle directory under the repo (offline pointer)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    relative_dir: str = Field(
        ...,
        description="Path relative to repository root; must stay under out/ops/.",
    )

    @field_validator("relative_dir")
    @classmethod
    def _must_be_ops_evidence(cls, v: str) -> str:
        s = v.strip().replace("\\", "/")
        if not s.startswith(_EVIDENCE_PREFIX):
            raise ValueError(f"evidence path must start with {_EVIDENCE_PREFIX!r}, got {v!r}")
        if ".." in s or s.startswith("/"):
            raise ValueError("path traversal not allowed")
        rest = s[len(_EVIDENCE_PREFIX) :]
        if not rest or not _SAFE_SEGMENT.match(rest):
            raise ValueError("invalid evidence path segments")
        return s


class SliceContractV0(BaseModel):
    """One Level-Up work unit: contract summary + optional evidence pointer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    slice_id: str = Field(..., min_length=1, max_length=256)
    title: str = Field(..., min_length=1, max_length=512)
    contract_summary: str = Field(
        ...,
        description="What is guaranteed / what blocks (operator-facing, short).",
        max_length=8000,
    )
    evidence: Optional[EvidenceBundleRefV0] = None


class LevelUpManifestV0(BaseModel):
    """Root document for a Level-Up v0 manifest (serializable JSON artifact)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["levelup/manifest/v0"] = _SCHEMA
    title: str = Field(default="Peak Trade Level-Up (Evidence-first)", min_length=1, max_length=512)
    slices: tuple[SliceContractV0, ...] = ()

    @field_validator("title")
    @classmethod
    def _root_title_stripped_nonempty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("manifest title must be non-empty after stripping whitespace")
        return s

    @model_validator(mode="after")
    def _slice_ids_unique(self) -> LevelUpManifestV0:
        seen: set[str] = set()
        for sl in self.slices:
            if sl.slice_id in seen:
                raise ValueError(f"duplicate slice_id in manifest: {sl.slice_id!r}")
            seen.add(sl.slice_id)
        return self


@dataclass(frozen=True)
class LevelUpManifestNamedLaneIdentityJoinResultV0:
    contract: LevelUpManifestV0
    join: CrossLaneIdentityJoinV1


@dataclass(frozen=True)
class SliceContractNamedLaneIdentityJoinResultV0:
    contract: SliceContractV0
    join: CrossLaneIdentityJoinV1


@dataclass(frozen=True)
class EvidenceBundleNamedLaneIdentityJoinResultV0:
    contract: EvidenceBundleRefV0
    join: CrossLaneIdentityJoinV1


def parse_levelup_manifest_with_identity_join_v1(
    raw: Mapping[str, Any],
    **sidecars: Any,
) -> LevelUpManifestNamedLaneIdentityJoinResultV0:
    """Parse a live I52 manifest and fail-closed join Package-N IDENTITY sidecar."""
    if not isinstance(raw, Mapping):
        raise ValueError("malformed plane data rejected: I52 manifest is not an object")
    snapshot = copy.deepcopy(dict(raw))
    contract = LevelUpManifestV0.model_validate(raw)
    join = join_i52_named_lane_identity_v1(
        contract.model_dump(mode="python"),
        surface="manifest",
        **sidecars,
    )
    if dict(raw) != snapshot:
        raise ValueError("I52 manifest input was mutated")
    return LevelUpManifestNamedLaneIdentityJoinResultV0(contract=contract, join=join)


def parse_slice_contract_with_identity_join_v1(
    raw: Mapping[str, Any],
    **sidecars: Any,
) -> SliceContractNamedLaneIdentityJoinResultV0:
    """Parse a live I52 slice and fail-closed join Package-N IDENTITY sidecar."""
    if not isinstance(raw, Mapping):
        raise ValueError("malformed plane data rejected: I52 slice is not an object")
    snapshot = copy.deepcopy(dict(raw))
    contract = SliceContractV0.model_validate(raw)
    join = join_i52_named_lane_identity_v1(
        contract.model_dump(mode="python"),
        surface="slice",
        **sidecars,
    )
    if dict(raw) != snapshot:
        raise ValueError("I52 slice input was mutated")
    return SliceContractNamedLaneIdentityJoinResultV0(contract=contract, join=join)


def parse_evidence_bundle_with_identity_join_v1(
    raw: Mapping[str, Any],
    **sidecars: Any,
) -> EvidenceBundleNamedLaneIdentityJoinResultV0:
    """Parse a live I52 evidence bundle and fail-closed join Package-N IDENTITY sidecar."""
    if not isinstance(raw, Mapping):
        raise ValueError("malformed plane data rejected: I52 evidence_bundle is not an object")
    snapshot = copy.deepcopy(dict(raw))
    contract = EvidenceBundleRefV0.model_validate(raw)
    join = join_i52_named_lane_identity_v1(
        contract.model_dump(mode="python"),
        surface="evidence_bundle",
        **sidecars,
    )
    if dict(raw) != snapshot:
        raise ValueError("I52 evidence_bundle input was mutated")
    return EvidenceBundleNamedLaneIdentityJoinResultV0(contract=contract, join=join)


def levelup_manifest_v0_json_schema() -> dict[str, Any]:
    """JSON Schema dict for ``LevelUpManifestV0`` (CLI ``export-json-schema`` / committed artifact)."""
    return LevelUpManifestV0.model_json_schema()
