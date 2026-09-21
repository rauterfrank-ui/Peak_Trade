"""Digest helpers for R1 recovery artifacts."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
    digest_excluding_keys,
)


def artifact_digest_v1(
    payload: Mapping[str, Any], *, exclude: Sequence[str] = ("artifact_digest",)
) -> str:
    return digest_excluding_keys(payload, exclude=exclude)
