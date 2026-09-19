"""Contract tests for optimizable envelope v1 resolver."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from src.experiments.canonical_optimizable_envelope_v1 import (
    ENVELOPE_CONTRACT_VERSION,
    REASON_AMBIGUOUS_AUTHORITY,
    REASON_CORE_MUTATION_REQUEST,
    REASON_MISSING_CONSTRAINT,
    REASON_NOT_OPTIMIZABLE,
    REASON_OWNER_MAP_NOT_AUTHORITY,
    REASON_OWNER_MISMATCH,
    REASON_PARTIAL,
    REASON_STALE_VERSION,
    REASON_SURFACE_NOT_IN_AUTHORIZED_REGISTRY,
    REASON_SURFACE_NOT_OWNER_AUTHORIZED,
    REASON_UNREGISTERED_SURFACE,
    REASON_UNKNOWN_FAIL_CLOSED,
    REASON_UNKNOWN_SURFACE,
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    RESOLUTION_FORBIDDEN,
    RESOLUTION_NOT_AUTHORIZED,
    RESOLUTION_NOT_OPTIMIZABLE,
    RESOLUTION_UNKNOWN_FAIL_CLOSED,
    SECTION5_OWNER_MAP_EVIDENCE_REF,
    STATUS_AUTHORIZED_RESEARCH_OPTIMIZATION,
    STATUS_NOT_OPTIMIZABLE,
    STATUS_UNKNOWN_FAIL_CLOSED,
    ZERO_AUTHORIZED_PRODUCTIVE_TARGETS,
    OptimizableEnvelopeResolveRequestV1,
    build_authorized_surface_registry_v1,
    build_optimizable_envelope_v1,
    derive_optimizable_envelope_identity_v1,
    resolve_optimizable_envelope_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_optimizable_envelope_v1.py"
_TEST_SURFACE = "research.surface.contract-test"
_TEST_OWNER = "owner.research.contract-test.v1"
_REPRO_DIGEST = compute_content_sha256({"fixture": "optimizable_envelope_v1"})


def _complete_envelope(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "envelope_id": "envelope.contract-test.v1",
        "envelope_version": ENVELOPE_CONTRACT_VERSION,
        "surface_id": _TEST_SURFACE,
        "surface_owner_ref": _TEST_OWNER,
        "target_family": "RESEARCH_TARGET_FAMILY_PENDING",
        "allowed_value_or_policy_domain": "policy.domain.owner.pending.v1",
        "bounds_ref": "bounds.owner.pending.v1",
        "change_rate_ref": "change_rate.owner.pending.v1",
        "risk_constraints_ref": "risk.owner.pending.v1",
        "evidence_requirements_ref": "evidence.owner.pending.v1",
        "provenance": {"contract": "test_fixture"},
        "reproducibility_digest": _REPRO_DIGEST,
        "status": STATUS_AUTHORIZED_RESEARCH_OPTIMIZATION,
        "owner_explicit_authorization": True,
        "owner_authorization_ref": _TEST_OWNER,
    }
    base.update(overrides)
    return base


def test_envelope_identity_is_deterministic() -> None:
    envelope = build_optimizable_envelope_v1(_complete_envelope())
    first = derive_optimizable_envelope_identity_v1(envelope)
    second = derive_optimizable_envelope_identity_v1(envelope)
    assert first == second
    assert envelope["envelope_identity"] == first


def test_authorized_surface_registry_includes_m9_and_f2_surfaces() -> None:
    registry = build_authorized_surface_registry_v1()
    assert registry["authorized_surface_count"] == 2
    assert registry["zero_authorized_productive_targets"] is True
    assert ZERO_AUTHORIZED_PRODUCTIVE_TARGETS is True


def test_unknown_surface_fail_closed() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id="UNKNOWN")
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_UNKNOWN_SURFACE


def test_unregistered_surface_without_envelope() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id="surface.not.in.catalog")
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_UNREGISTERED_SURFACE


def test_partial_record_not_authorized() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(bounds_ref="PARTIAL"),
        )
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_PARTIAL


def test_missing_constraint_not_authorized() -> None:
    payload = _complete_envelope()
    del payload["risk_constraints_ref"]
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=_TEST_SURFACE, envelope=payload)
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_MISSING_CONSTRAINT


def test_stale_version_not_authorized() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(envelope_version="optimizable_envelope_contract_v0"),
        )
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_STALE_VERSION


def test_owner_mismatch_not_authorized() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(),
            claimed_surface_owner_ref="owner.other.v1",
        )
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_OWNER_MISMATCH


def test_ambiguous_authority_not_authorized() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(owner_authorization_ref="owner.other.v1"),
        )
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_AMBIGUOUS_AUTHORITY


def test_core_mutation_forbidden() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(),
            requested_core_mutation=True,
        )
    )
    assert result["resolution"] == RESOLUTION_FORBIDDEN
    assert result["reason"] == REASON_CORE_MUTATION_REQUEST


def test_explicit_not_optimizable() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(status=STATUS_NOT_OPTIMIZABLE),
        )
    )
    assert result["resolution"] == RESOLUTION_NOT_OPTIMIZABLE
    assert result["reason"] == REASON_NOT_OPTIMIZABLE


def test_unknown_fail_closed_status() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(status=STATUS_UNKNOWN_FAIL_CLOSED),
        )
    )
    assert result["resolution"] == RESOLUTION_UNKNOWN_FAIL_CLOSED
    assert result["reason"] == REASON_UNKNOWN_FAIL_CLOSED


def test_owner_map_provenance_never_authorizes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.experiments.canonical_optimizable_envelope_v1._AUTHORIZED_SURFACE_IDS",
        frozenset({_TEST_SURFACE}),
    )
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(),
            owner_map_provenance_ref=SECTION5_OWNER_MAP_EVIDENCE_REF,
        )
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_OWNER_MAP_NOT_AUTHORITY


def test_complete_envelope_still_not_authorized_without_registry_entry() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(),
        )
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_SURFACE_NOT_IN_AUTHORIZED_REGISTRY


def test_missing_owner_explicit_authorization_not_authorized() -> None:
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(owner_explicit_authorization=False),
        )
    )
    assert result["resolution"] == RESOLUTION_NOT_AUTHORIZED
    assert result["reason"] == REASON_SURFACE_NOT_OWNER_AUTHORIZED


def test_authorized_research_optimization_only_when_registry_and_owner_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.experiments.canonical_optimizable_envelope_v1._AUTHORIZED_SURFACE_IDS",
        frozenset({_TEST_SURFACE}),
    )
    result = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(
            surface_id=_TEST_SURFACE,
            envelope=_complete_envelope(),
        )
    )
    assert result["resolution"] == RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION
    assert result["reason"] == STATUS_AUTHORIZED_RESEARCH_OPTIMIZATION
    assert result["zero_authorized_productive_targets"] is True


def test_no_runtime_promotion_execution_or_forbidden_paths() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_imports = {
        "src.core.peak_config",
        "src.governance.promotion_loop",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "src.live",
        "src.live.live_gates",
        "src.risk",
        "src.trading",
        "src.trading.master_v2",
        "src.experiments.canonical_advanced_search_v1",
        "src.experiments.canonical_automated_offline_research_loop_v1",
        "src.meta.learning_loop.bridge",
    }
    assert forbidden_imports.isdisjoint(imported)
