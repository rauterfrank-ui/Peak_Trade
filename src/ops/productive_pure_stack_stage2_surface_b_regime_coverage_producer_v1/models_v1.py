"""Models for dedicated Surface-B regime-coverage producer v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple


class RegimeCoverageProducerErrorV1(ValueError):
    """Fail-closed regime-coverage producer error."""


@dataclass(frozen=True)
class RegimeCoverageBarInputV1:
    """PIT-safe finalized PT1M bar input accepted by the producer.

    Candle OHLCV and mark remain separate fields. No candle/mark substitution.
    """

    instrument_id: str
    event_time_epoch_s: int
    open: float
    high: float
    low: float
    close: float
    mark_price: float
    volume: float
    finalized: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "event_time_epoch_s": int(self.event_time_epoch_s),
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "mark_price": float(self.mark_price),
            "volume": float(self.volume),
            "finalized": bool(self.finalized),
        }


@dataclass(frozen=True)
class RegimeCoverageLabelObservationV1:
    event_time_epoch_s: int
    label: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_time_epoch_s": int(self.event_time_epoch_s),
            "label": self.label,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RegimeCoverageProducerResultV1:
    """Versioned deterministic producer result without invented coverage counts."""

    versioned_producer_id: str
    instrument_id: str
    as_of_event_time_epoch_s: int
    observations: Tuple[RegimeCoverageLabelObservationV1, ...]
    producer_digest: str
    taxonomy_sink_labels: Tuple[str, ...]
    threshold_authority_ref: str
    lookback_window_authority_ref: str
    productive_emission: bool
    coverage_counts: Optional[Mapping[str, int]]
    regime_coverage_instance: Optional[Mapping[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "versioned_producer_id": self.versioned_producer_id,
            "instrument_id": self.instrument_id,
            "as_of_event_time_epoch_s": int(self.as_of_event_time_epoch_s),
            "observations": [o.to_dict() for o in self.observations],
            "producer_digest": self.producer_digest,
            "taxonomy_sink_labels": list(self.taxonomy_sink_labels),
            "threshold_authority_ref": self.threshold_authority_ref,
            "lookback_window_authority_ref": self.lookback_window_authority_ref,
            "productive_emission": bool(self.productive_emission),
            "coverage_counts": None if self.coverage_counts is None else dict(self.coverage_counts),
            "regime_coverage_instance": None
            if self.regime_coverage_instance is None
            else dict(self.regime_coverage_instance),
        }


def require_sequence(raw: Any, *, label: str) -> Sequence[Any]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise RegimeCoverageProducerErrorV1(f"SEQUENCE_REQUIRED:{label}")
    return raw
