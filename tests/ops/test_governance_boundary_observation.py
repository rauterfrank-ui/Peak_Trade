"""Unit tests for ``build_governance_boundary_observation`` (cockpit aggregate only)."""

from __future__ import annotations

from typing import Any, Dict

from src.ops.governance_boundary_observation import (
    READER_SCHEMA_VERSION,
    build_governance_boundary_observation,
)


def _ai(**over: Any) -> Dict[str, Any]:
    base = {
        "proposer_authority": "advisory_only",
        "critic_authority": "supervisory_only",
        "provider_binding_authority": "not_execution_authority",
        "execution_boundary": "deterministic_gated",
        "closest_to_trade": "not_evidenced_as_llm_final",
    }
    base.update(over)
    return base


def _hs(**over: Any) -> Dict[str, Any]:
    base = {
        "status": "operator_supervised",
        "mode": "intended",
        "summary": "bounded pilot requires operator supervision",
    }
    base.update(over)
    return base


def test_nominal_default_labels() -> None:
    out = build_governance_boundary_observation(
        ai_boundary_state=_ai(),
        human_supervision_state=_hs(),
    )
    assert out["status"] == "nominal"
    assert out["data_source"] == "cockpit_payload_aggregate"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION
    assert "advisory" in out["summary"].lower() or "boundary" in out["summary"].lower()


def test_degraded_bad_ai_value() -> None:
    out = build_governance_boundary_observation(
        ai_boundary_state=_ai(closest_to_trade="llm_final"),
        human_supervision_state=_hs(),
    )
    assert out["status"] == "degraded"


def test_degraded_unsupervised() -> None:
    out = build_governance_boundary_observation(
        ai_boundary_state=_ai(),
        human_supervision_state=_hs(status="unsupervised"),
    )
    assert out["status"] == "degraded"


def test_caution_missing_ai_field() -> None:
    b = _ai()
    del b["proposer_authority"]
    out = build_governance_boundary_observation(
        ai_boundary_state=b,
        human_supervision_state=_hs(),
    )
    assert out["status"] == "caution"


def test_caution_unknown_ai_value() -> None:
    out = build_governance_boundary_observation(
        ai_boundary_state=_ai(execution_boundary="unknown"),
        human_supervision_state=_hs(),
    )
    assert out["status"] == "caution"


def test_caution_missing_supervision_summary() -> None:
    out = build_governance_boundary_observation(
        ai_boundary_state=_ai(),
        human_supervision_state=_hs(summary=""),
    )
    assert out["status"] == "caution"


def test_unknown_missing_ai_dict() -> None:
    out = build_governance_boundary_observation(
        ai_boundary_state=None,  # type: ignore[arg-type]
        human_supervision_state=_hs(),
    )
    assert out["status"] == "unknown"


def test_guard_note_when_deny_not_active() -> None:
    out = build_governance_boundary_observation(
        ai_boundary_state=_ai(),
        human_supervision_state=_hs(),
        guard_state={"deny_by_default": "inactive", "no_trade_baseline": "reference"},
    )
    notes = out.get("consistency_notes") or []
    assert any("deny_by_default" in n for n in notes)


def test_evidence_note_when_partial_summary() -> None:
    out = build_governance_boundary_observation(
        ai_boundary_state=_ai(),
        human_supervision_state=_hs(),
        evidence_state={"summary": "partial"},
    )
    notes = out.get("consistency_notes") or []
    assert any("evidence_audit" in n for n in notes)
