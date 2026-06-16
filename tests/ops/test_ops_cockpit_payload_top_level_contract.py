"""
Regression: minimal top-level key presence for ``build_ops_cockpit_payload``.

Values are intentionally not asserted — only key names, per
``docs/ops/specs/OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md``.

SLICE-OC-2: static reflection-token guard for
``docs/ops/specs/OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md`` (read-only; non-authorizing).
"""

from __future__ import annotations

import re
from pathlib import Path

from src.webui.ops_cockpit import build_ops_cockpit_payload

REPO_ROOT = Path(__file__).resolve().parents[2]
OPS_COCKPIT_OPERATOR_SUMMARY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md"
)
REMOTE_RUNTIME_DOCS_GUARD = (
    REPO_ROOT / "tests" / "ops" / "test_remote_runtime_contract_docs_guard_v0.py"
)
THIS_MODULE = Path(__file__).name

CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
OPDS1_HEADING = "## Post-Release Operator Package Decision Contract v0"
OPDS1_BLOCK_ANCHOR = "POST_RELEASE_OPERATOR_PACKAGE_DECISION_CONTRACT_V0=true"
OPDS1_EXPECTED: dict[str, str] = {
    "POST_RELEASE_OPERATOR_DECISION_SYSTEM_PACKAGE_V1_STARTED": "true",
    "OPDS1_PACKAGE_DECISION_CONTRACT_COMPLETE": "true",
    "POST_RELEASE_OPERATOR_PACKAGE_DECISION_CONTRACT_V0": "true",
    "PACKAGE_FIRST_WHEN_SAFE_PACKAGE_EXISTS": "true",
    "PACKAGE_SIZE_HARD_CAP_MAX": "3",
    "POINTER_ONLY_PR_REJECTED": "true",
    "HANDOFF_LEDGER_ONLY_PR_REJECTED": "true",
    "MICRO_CHURN_SLICE_REJECTED": "true",
    "STOP_IDLE_REQUIRES_EXPLICIT_NO_PACKAGE_REASON": "true",
    "POST_SLICE_REVIEW_REQUIRED": "true",
    "COMPLETED_RC_DOES_NOT_IMPLY_NEXT_RUNTIME": "true",
    "COSMETIC_GAP_DOES_NOT_AUTO_BECOME_PR": "true",
    "ENFORCEMENT_ACTIVATED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "READY_FOR_OPERATOR_ARMING": "false",
    "NO_RUNTIME": "true",
    "PROTECTED_AREAS_NO_TOUCH": "true",
    "REUSE_DRIFT_GUARD": "REUSE_OK",
    "NO_PARALLEL_DOCS": "true",
}
OC_REFLECTION_HEADING = "## Ops Cockpit — post-trilogy operator status reflection v0"
OC_REFLECTION_BLOCK_ANCHOR = "OPS_COCKPIT_OR_OPERATOR_STATUS_INDEX_RC_V0=true"
OC_REFLECTION_EXPECTED: dict[str, str] = {
    "OPS_COCKPIT_OR_OPERATOR_STATUS_INDEX_RC_V0": "true",
    "SLICE_OC1_DOCS_ONLY_REFLECTION": "true",
    "OPS_COCKPIT_DISPLAY_REFLECTION_ONLY": "true",
    "OPS_COCKPIT_AUTHORITY_CHANGED": "false",
    "OPERATOR_EXPERIENCE_RELEASE_RC_V0_CORE_DONE": "true",
    "CYBERSECURITY_VISIBILITY_RELEASE_RC_V0_CORE_DONE": "true",
    "EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0_CORE_DONE": "true",
    "ER_DETAILS_PREFLIGHT_OWNER_ONLY": "true",
    "NOTION_AS_MIRROR_ONLY": "true",
    "NOTION_WRITES": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "RUNTIME_AUTHORITY_CHANGED": "false",
    "TRADING_AUTHORITY_CHANGED": "false",
    "MASTER_V2_LOGIC_CHANGED": "false",
}
FENCED_BLOCK_RX = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

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


def _operator_summary_text() -> str:
    assert OPS_COCKPIT_OPERATOR_SUMMARY_SPEC.is_file()
    return OPS_COCKPIT_OPERATOR_SUMMARY_SPEC.read_text(encoding="utf-8")


def _fenced_blocks(text: str) -> list[str]:
    return [block.strip() for block in FENCED_BLOCK_RX.findall(text)]


def _block_containing(text: str, anchor: str) -> str:
    for block in _fenced_blocks(text):
        if anchor in block:
            return block
    raise AssertionError(f"missing fenced machine-line block containing {anchor!r}")


def _machine_line_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key and value:
            values[key.strip()] = value.strip()
    return values


def _oc_reflection_section(text: str) -> str:
    start = text.find(OC_REFLECTION_HEADING)
    assert start != -1, "missing post-trilogy operator status reflection section"
    end = text.find("## Related", start)
    if end == -1:
        end = len(text)
    return text[start:end]


def test_ops_cockpit_operator_summary_surface_oc1_reflection_tokens_v0() -> None:
    text = _operator_summary_text()
    section = _oc_reflection_section(text)
    block = _block_containing(text, OC_REFLECTION_BLOCK_ANCHOR)
    values = _machine_line_values(block)

    assert "read-only" in section.lower()
    assert "reflection" in section.lower()
    assert (
        "ops_cockpit_display_reflection_only" in section.lower()
        or "display or reflect" in section.lower()
    )
    assert "durable Evidence Archive" in section or "durable evidence archive" in section.lower()
    assert "mirror/status" in section.lower() or "mirror" in section.lower()
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "SLICE-OC-2" in section
    assert "new payload keys" in section.lower()
    assert "PII" in section or "raw logs" in section.lower()

    missing = set(OC_REFLECTION_EXPECTED) - values.keys()
    assert not missing, f"missing OC reflection keys: {sorted(missing)}"
    for key, expected in OC_REFLECTION_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_ops_cockpit_payload_contract_reciprocal_remote_runtime_docs_guard_v0() -> None:
    guard_text = REMOTE_RUNTIME_DOCS_GUARD.read_text(encoding="utf-8")
    assert THIS_MODULE in guard_text
    assert "test_ops_cockpit_payload_top_level_contract.py" in guard_text
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert "test_remote_runtime_contract_docs_guard_v0.py" in owner_text


def _ci_audit_text() -> str:
    assert CI_AUDIT.is_file()
    return CI_AUDIT.read_text(encoding="utf-8")


def _opds1_section(text: str) -> str:
    start = text.find(OPDS1_HEADING)
    assert start != -1, "missing Post-Release Operator Package Decision Contract section"
    end = text.find("## Master V2", start)
    assert end != -1, "missing section boundary after OPDS1"
    return text[start:end]


def test_ci_audit_opds1_post_release_package_decision_contract_v0() -> None:
    text = _ci_audit_text()
    section = _opds1_section(text)
    block = _block_containing(text, OPDS1_BLOCK_ANCHOR)
    values = _machine_line_values(block)

    assert "package-first" in section.lower()
    assert "1–3 PR" in section or "1-3 PR" in section
    assert "micro-churn" in section.lower() or "micro-slice" in section.lower()
    assert "pointer-only" in section.lower() or "pointer only" in section.lower()
    assert "handoff" in section.lower()
    assert "STOP_IDLE" in section
    assert "post-slice review" in section.lower()
    assert "no runtime" in section.lower() or "no** runtime" in section.lower()
    assert "no enforcement" in section.lower() or "no** enforcement" in section.lower()
    assert "READY_FOR_OPERATOR_ARMING=false" in section
    assert "test_ops_cockpit_payload_top_level_contract.py" in section
    assert "test_recommend_manual_only_workflows.py" in section
    assert "SLICE-OPDS-1" in section

    missing = set(OPDS1_EXPECTED) - values.keys()
    assert not missing, f"missing OPDS1 keys: {sorted(missing)}"
    for key, expected in OPDS1_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_opds1_ci_audit_reciprocal_test_owner_reference_v0() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert "test_ci_audit_opds1_post_release_package_decision_contract_v0" in owner_text
    audit = _ci_audit_text()
    assert "tests/ops/test_ops_cockpit_payload_top_level_contract.py" in audit
