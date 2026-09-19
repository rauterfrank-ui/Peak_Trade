"""M9 volatility numeric max-age optimizable surface contract tests."""

from __future__ import annotations

import ast
from pathlib import Path

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    BLOCKED_FOR_PARAMETER_DECISION,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    ENFORCEMENT_DURING_RESEARCH,
    NUMERIC_MAX_AGE_DECIDED,
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
    PARAMETER_PROMOTED,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    ALLOWED_POLICY_DOMAIN_REF,
    BOUNDS_REF,
    SURFACE_ID,
    SURFACE_OWNER_REF,
    TARGET_FAMILY,
    build_m9_volatility_numeric_max_age_envelope_payload_v1,
    compute_m9_reproducibility_digest_v1,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    RESOLUTION_NOT_AUTHORIZED,
    REASON_UNREGISTERED_SURFACE,
    SYNTHETIC_OFFLINE_SURFACE_ID,
    OptimizableEnvelopeResolveRequestV1,
    build_authorized_surface_registry_v1,
    build_optimizable_envelope_v1,
    resolve_optimizable_envelope_v1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED as POLICY_NUMERIC_MAX_AGE_DECIDED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
M9_MODULE = (
    REPO_ROOT / "src/experiments/canonical_m9_volatility_numeric_max_age_optimizable_surface_v1.py"
)
ENVELOPE_MODULE = REPO_ROOT / "src/experiments/canonical_optimizable_envelope_v1.py"


def test_m9_surface_in_two_surface_registry() -> None:
    registry = build_authorized_surface_registry_v1()
    assert registry["authorized_surface_count"] == 2
    assert registry["catalog_surface_count"] == 2
    assert SURFACE_ID in registry["authorized_surface_ids"]


def test_domain_is_exact_operator_bound_candidate_set() -> None:
    import json

    domain = json.loads((REPO_ROOT / ALLOWED_POLICY_DOMAIN_REF).read_text(encoding="utf-8"))
    bounds = json.loads((REPO_ROOT / BOUNDS_REF).read_text(encoding="utf-8"))
    assert tuple(domain["candidate_max_age_seconds"]) == OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS
    assert tuple(bounds["candidate_max_age_seconds"]) == OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS


def test_reproducibility_digest_is_deterministic() -> None:
    first = compute_m9_reproducibility_digest_v1()
    second = compute_m9_reproducibility_digest_v1()
    assert first == second
    payload = build_m9_volatility_numeric_max_age_envelope_payload_v1()
    assert payload["reproducibility_digest"] == first


def test_resolver_exact_admission_pass() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=SURFACE_ID)
    )
    assert result["resolution"] == RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION
    assert result["surface_id"] == SURFACE_ID


def test_m4_synthetic_surface_still_not_authorized() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=SYNTHETIC_OFFLINE_SURFACE_ID)
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_UNREGISTERED_SURFACE


def test_envelope_owner_grant_and_identity() -> None:
    envelope = build_optimizable_envelope_v1(
        build_m9_volatility_numeric_max_age_envelope_payload_v1()
    )
    assert envelope["surface_id"] == SURFACE_ID
    assert envelope["surface_owner_ref"] == SURFACE_OWNER_REF
    assert envelope["target_family"] == TARGET_FAMILY
    assert envelope["owner_explicit_authorization"] is True
    assert envelope["owner_authorization_ref"] == SURFACE_OWNER_REF
    assert envelope["productive_authority"] == "NONE"


def test_master_v2_flags_unchanged_and_blocked_for_parameter_decision() -> None:
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert POLICY_NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
    assert ENFORCEMENT_DURING_RESEARCH is False
    assert PARAMETER_PROMOTED is False
    assert BLOCKED_FOR_PARAMETER_DECISION is True


def test_no_envelope_to_master_v2_import_wiring() -> None:
    for module_path in (M9_MODULE, ENVELOPE_MODULE):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert "src.trading.master_v2" not in imported
        assert "trading.master_v2.double_play" not in imported
