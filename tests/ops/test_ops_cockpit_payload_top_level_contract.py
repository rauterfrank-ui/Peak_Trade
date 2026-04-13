"""
Regression: minimal top-level key presence for ``build_ops_cockpit_payload``.

Values are intentionally not asserted — only key names, per
``docs/ops/specs/OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md``.
"""

from __future__ import annotations

from pathlib import Path

from src.webui.ops_cockpit import build_ops_cockpit_payload

# Keep in sync with docs/ops/specs/OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md (stable set).
EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS = frozenset(
    {
        "ai_boundary_state",
        "balance_semantics_state",
        "canonical_sources",
        "critical_flags",
        "dependencies_state",
        "evidence_audit_observation",
        "evidence_state",
        "executive_summary",
        "exposure_risk_observation",
        "exposure_state",
        "freshness_status",
        "governance_boundary_observation",
        "guard_state",
        "health_drift_observation",
        "human_supervision_state",
        "incident_safety_observation",
        "incident_state",
        "operator_state",
        "phase83_eligibility_snapshot",
        "policy_go_no_go_observation",
        "policy_state",
        "runtime_unknown_state",
        "run_session_observation",
        "run_state",
        "safety_posture_observation",
        "safety_state",
        "session_end_mismatch_state",
        "source_coverage_status",
        "source_group_summary",
        "source_groups",
        "stale_state",
        "system_state",
        "system_state_observation",
        "transfer_ambiguity_state",
        "truth_state",
        "truth_status",
        "unknown_flags",
        "update_officer_ui",
        "workflow_officer_state",
    }
)


def _minimal_truth_docs(repo: Path) -> None:
    docs_dir = repo / "docs" / "governance" / "ai"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "AI_LAYER_CANONICAL_SPEC_V1.md").write_text("# ok\n", encoding="utf-8")
    (docs_dir / "AI_UNKNOWN_REDUCTION_V1.md").write_text("# ok\n", encoding="utf-8")


def test_build_ops_cockpit_payload_top_level_keys_contract(tmp_path: Path) -> None:
    _minimal_truth_docs(tmp_path)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    missing = EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS - payload.keys()
    assert not missing, f"Missing top-level keys: {sorted(missing)}"
