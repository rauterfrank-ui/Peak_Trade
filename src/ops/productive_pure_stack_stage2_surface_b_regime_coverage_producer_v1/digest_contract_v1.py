"""Producer digest contract for Surface-B regime-coverage producer v1."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.models_v1 import (
    RegimeCoverageBarInputV1,
    RegimeCoverageLabelObservationV1,
)


def digest_mapping(payload: Mapping[str, Any] | dict[str, Any]) -> str:
    """Local deterministic digest (canonical JSON + SHA-256)."""
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def compute_regime_coverage_producer_digest_v1(
    *,
    instrument_id: str,
    as_of_event_time_epoch_s: int,
    bars: Sequence[RegimeCoverageBarInputV1],
    observations: Sequence[RegimeCoverageLabelObservationV1],
) -> str:
    payload: Mapping[str, object] = {
        "versioned_producer_id": C.VERSIONED_PRODUCER_ID,
        "canonical_producer_name": C.CANONICAL_PRODUCER_NAME,
        "canonical_producer_version": C.CANONICAL_PRODUCER_VERSION,
        "taxonomy_binding": C.TAXONOMY_BINDING,
        "threshold_authority_ref": C.THRESHOLD_AUTHORITY_REF,
        "lookback_window_authority_ref": C.LOOKBACK_WINDOW_AUTHORITY_REF,
        "time_basis": C.TIME_BASIS,
        "instrument_id": instrument_id,
        "as_of_event_time_epoch_s": int(as_of_event_time_epoch_s),
        "bars": [b.to_dict() for b in bars],
        "observations": [o.to_dict() for o in observations],
        "productive_emission": C.PRODUCTIVE_EMISSION,
        "coverage_counts": None,
        "regime_coverage_instance": None,
    }
    return digest_mapping(payload)
