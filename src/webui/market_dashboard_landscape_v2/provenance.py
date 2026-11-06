"""Immutable provenance + freshness envelope for Landscape V2 projections."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .availability import Availability


def _require_non_empty(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_utc(name: str, value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware UTC")
    # Normalize to UTC for stable serialization.
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class SnapshotProvenanceV1:
    """Mandatory provenance for every Landscape V2 projection.

    All fields are explicit. Callers must not invent digests, timestamps, or
    availability. Use Availability.NOT_BOUND / MISSING_SOURCE when unbound.
    """

    schema_id: str
    schema_version: str
    producer_module: str
    generated_at: datetime
    effective_at: datetime | None
    source_kind: str
    source_reference: str | None
    evidence_digest: str | None
    git_sha: str | None
    availability: Availability

    def __post_init__(self) -> None:
        _require_non_empty("schema_id", self.schema_id)
        _require_non_empty("schema_version", self.schema_version)
        _require_non_empty("producer_module", self.producer_module)
        _require_non_empty("source_kind", self.source_kind)
        object.__setattr__(self, "generated_at", _require_utc("generated_at", self.generated_at))
        if self.effective_at is not None:
            object.__setattr__(
                self, "effective_at", _require_utc("effective_at", self.effective_at)
            )
        if not isinstance(self.availability, Availability):
            raise TypeError("availability must be Availability")
        if self.source_reference is not None and not isinstance(self.source_reference, str):
            raise TypeError("source_reference must be str|None")
        if self.evidence_digest is not None and not isinstance(self.evidence_digest, str):
            raise TypeError("evidence_digest must be str|None")
        if self.git_sha is not None and not isinstance(self.git_sha, str):
            raise TypeError("git_sha must be str|None")

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "producer_module": self.producer_module,
            "generated_at": self.generated_at.isoformat().replace("+00:00", "Z"),
            "effective_at": (
                None
                if self.effective_at is None
                else self.effective_at.isoformat().replace("+00:00", "Z")
            ),
            "source_kind": self.source_kind,
            "source_reference": self.source_reference,
            "evidence_digest": self.evidence_digest,
            "git_sha": self.git_sha,
            "availability": self.availability.value,
        }


@dataclass(frozen=True)
class FreshnessV1:
    """Freshness metadata; stale thresholds are caller-supplied, never invented."""

    observed_at: datetime
    max_age_seconds: int | None
    is_stale: bool
    stale_reason: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "observed_at", _require_utc("observed_at", self.observed_at))
        if self.max_age_seconds is not None:
            if not isinstance(self.max_age_seconds, int) or self.max_age_seconds < 0:
                raise ValueError("max_age_seconds must be int>=0 or None")
        if not isinstance(self.is_stale, bool):
            raise TypeError("is_stale must be bool")
        if self.is_stale and (self.stale_reason is None or not str(self.stale_reason).strip()):
            raise ValueError("stale_reason required when is_stale=True")
        if not self.is_stale and self.stale_reason is not None:
            raise ValueError("stale_reason must be None when is_stale=False")

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "observed_at": self.observed_at.isoformat().replace("+00:00", "Z"),
            "max_age_seconds": self.max_age_seconds,
            "is_stale": self.is_stale,
            "stale_reason": self.stale_reason,
        }
