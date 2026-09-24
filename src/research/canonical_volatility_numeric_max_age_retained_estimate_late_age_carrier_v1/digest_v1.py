"""Content digest for retained-estimate lifecycle carriers."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    sha256_hex,
)


def carrier_content_digest_v1(
    payload: Mapping[str, Any],
    *,
    exclude: Sequence[str] = ("artifact_digest",),
) -> str:
    filtered = {k: v for k, v in payload.items() if k not in set(exclude)}
    return sha256_hex(filtered)
