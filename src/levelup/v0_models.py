"""
Typed v0 contracts for Level-Up work units (Evidence-first roadmap alignment).

These types do not perform live trading, broker I/O, or unlock gates — they describe
slice metadata and pointers to under-repo evidence directories (typically ``out/ops/``).
"""

from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    title: str = Field(default="Peak Trade Level-Up (Evidence-first)", max_length=512)
    slices: tuple[SliceContractV0, ...] = ()
