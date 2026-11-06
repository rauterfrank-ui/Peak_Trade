"""Typed models for comparison_ssot.v1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

GateStatus = Literal["PASS", "FAIL"]


class ComparisonSsotError(ValueError):
    """Fail-closed comparison SSOT error."""


@dataclass(frozen=True)
class InputRef:
    owner_domain: str
    ref_type: str
    ref_id: str
    digest: str

    def sort_key(self) -> tuple[str, str, str, str]:
        return (self.owner_domain, self.ref_type, self.ref_id, self.digest)

    def to_mapping(self) -> dict[str, str]:
        return {
            "owner_domain": self.owner_domain,
            "ref_type": self.ref_type,
            "ref_id": self.ref_id,
            "digest": self.digest,
        }


@dataclass(frozen=True)
class LoadedMetricInput:
    manifest_path: Path
    manifest: Mapping[str, Any]
    comparison_metric_input_id: str
    source_domain: str
    source_ref: InputRef
    evaluation_slice_id: str
    comparability_metadata: Mapping[str, Any]
    metrics: Mapping[str, float | int]


@dataclass(frozen=True)
class GateOutcome:
    gate_id: str
    version: str
    status: GateStatus
    reason_code: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparisonOfflineResult:
    output_dir: Path
    definition_path: Path
    result_path: Path
    comparison_definition_id: str
    definition_manifest: Mapping[str, Any]
    result_manifest: Mapping[str, Any]
