"""Typed models for comparison_metric_input.v1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class ComparisonMetricInputError(ValueError):
    """Fail-closed comparison metric input error."""


@dataclass(frozen=True)
class SourceRef:
    owner_domain: str
    ref_type: str
    ref_id: str
    digest: str

    def to_mapping(self) -> dict[str, str]:
        return {
            "owner_domain": self.owner_domain,
            "ref_type": self.ref_type,
            "ref_id": self.ref_id,
            "digest": self.digest,
        }


@dataclass(frozen=True)
class SourceBindingRecord:
    relative_path: str
    content_sha256: str


@dataclass(frozen=True)
class AdapterArtifacts:
    equity_path: Path
    trades_path: Path
    equity_digest: str
    trades_digest: str
    source_digest: str
    bindings: tuple[SourceBindingRecord, ...]


@dataclass(frozen=True)
class AdapterResult:
    source_domain: str
    source_ref: SourceRef
    source_digest: str
    evaluation_slice_id: str
    comparability_metadata: dict[str, Any]
    metrics: dict[str, float | int]
    source_bindings: tuple[SourceBindingRecord, ...]
    var_suite_companion: dict[str, Any] | None = None


@dataclass(frozen=True)
class ComparisonMetricInputResult:
    output_dir: Path
    manifest_path: Path
    comparison_metric_input_id: str
    manifest: Mapping[str, Any]
