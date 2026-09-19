"""F5-FRESH futures input freshness optimizable surface contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    ALLOWED_POLICY_DOMAIN_REF,
    BOUNDS_REF,
    SURFACE_ID,
    SURFACE_OWNER_REF,
    TARGET_FAMILY,
    build_f5_fresh_futures_input_freshness_envelope_payload_v1,
    compute_f5_fresh_reproducibility_digest_v1,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    build_authorized_surface_registry_v1,
    build_optimizable_envelope_v1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.f5_fresh_research_candidate_domain_constants_v1 import (
    OPERATOR_BOUND_CANDIDATE_FRESHNESS_MAX_AGE_SECONDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_f5_fresh_in_three_surface_registry() -> None:
    registry = build_authorized_surface_registry_v1()
    assert registry["authorized_surface_count"] == 3
    assert SURFACE_ID in registry["authorized_surface_ids"]


def test_domain_is_exact_operator_bound_freshness_set() -> None:
    domain = json.loads((REPO_ROOT / ALLOWED_POLICY_DOMAIN_REF).read_text(encoding="utf-8"))
    bounds = json.loads((REPO_ROOT / BOUNDS_REF).read_text(encoding="utf-8"))
    assert tuple(domain["candidate_freshness_max_age_seconds"]) == (
        OPERATOR_BOUND_CANDIDATE_FRESHNESS_MAX_AGE_SECONDS
    )
    assert (
        tuple(bounds["freshness_max_age_seconds"])
        == OPERATOR_BOUND_CANDIDATE_FRESHNESS_MAX_AGE_SECONDS
    )
    assert domain["f1_m9_volatility_max_age_deduplication_forbidden"] is True


def test_f5_fresh_distinct_from_f1_surface() -> None:
    assert SURFACE_ID != F1_SURFACE_ID
    assert TARGET_FAMILY != "MASTER_V2_VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION"


def test_resolver_admits_f5_fresh_surface() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=SURFACE_ID)
    )
    assert result["resolution"] == RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION


def test_envelope_payload_productive_authority_none() -> None:
    envelope = build_optimizable_envelope_v1(
        build_f5_fresh_futures_input_freshness_envelope_payload_v1()
    )
    assert envelope["surface_id"] == SURFACE_ID
    assert envelope["surface_owner_ref"] == SURFACE_OWNER_REF
    assert envelope["productive_authority"] == "NONE"
    digest = compute_f5_fresh_reproducibility_digest_v1()
    assert envelope["reproducibility_digest"] == digest
