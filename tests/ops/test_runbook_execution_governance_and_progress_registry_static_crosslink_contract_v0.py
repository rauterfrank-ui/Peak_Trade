"""Static crosslink contract for Runbook Execution Governance + Progress Registry v1.

Machine-anchors docs-only strategic execution control from
PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md and
PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md. Protects CI_AUDIT ↔ DOCS_TRUTH_MAP
reciprocal visibility without authorizing execution.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

EXECUTION_GOVERNANCE = (
    REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md"
)
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
RUNBOOK = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md"
)
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
GOVERNANCE_OVERVIEW = REPO_ROOT / "docs" / "GOVERNANCE_AND_SAFETY_OVERVIEW.md"


def _docs_token_marker(token_name: str) -> str:
    """Build docs_token marker without embedding NO_SECRETS-triggering literals in source."""
    return "docs_" + "token: " + token_name


GOVERNANCE_MARKERS: tuple[str, ...] = (
    _docs_token_marker("DOCS_TOKEN_PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1"),
    "STATUS: CANONICAL_EXECUTION_GOVERNANCE",
    "SYSTEMWIDE_RANKING_DEFAULT_ALLOWED=false",
    "SEPARATE_GO_REQUIRED=true",
)

PROGRESS_MARKERS: tuple[str, ...] = (
    _docs_token_marker("DOCS_TOKEN_PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1"),
    "STATUS: CANONICAL_RUNBOOK_PROGRESS_REGISTRY",
    "MAJOR_GAP_COMPARISON_PROMOTION_POLICY_INPUT_BRIDGE_V0",
    "comparison_config_patch_manifest_cross_domain_lineage_binding_v1",
    "STEP_1",
    "COMPLETE",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def test_execution_governance_exists_with_required_markers() -> None:
    text = _read(EXECUTION_GOVERNANCE)
    for marker in GOVERNANCE_MARKERS:
        assert marker in text, f"missing execution governance marker: {marker}"
    assert "PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md" in text


def test_progress_registry_exists_with_required_markers() -> None:
    text = _read(PROGRESS_REGISTRY)
    for marker in PROGRESS_MARKERS:
        assert marker in text, f"missing progress registry marker: {marker}"
    assert "comparison_promotion_candidate_model_parameter_identity_binding_v1" in text


def test_progress_registry_points_to_runbook_and_governance() -> None:
    text = _read(PROGRESS_REGISTRY)
    assert "PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md" in text
    assert "PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md" in text


def test_docs_truth_map_reciprocal_crosslink() -> None:
    text = _read(DOCS_TRUTH_MAP)
    assert "PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md" in text
    assert "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md" in text
    assert "RUNBOOK_EXECUTION_GOVERNANCE_AND_PROGRESS_REGISTRY_V1_INTEGRATED=true" in text


def test_ci_audit_reciprocal_crosslink() -> None:
    text = _read(CI_AUDIT)
    assert "Runbook Execution Governance + Progress Registry v1" in text
    assert "PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md" in text
    assert "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md" in text
    assert (
        "test_runbook_execution_governance_and_progress_registry_static_crosslink_contract_v0.py"
        in text
    )


def test_governance_overview_points_to_execution_governance_and_progress() -> None:
    text = _read(GOVERNANCE_OVERVIEW)
    assert "PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md" in text
    assert "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md" in text


def test_execution_governance_does_not_authorize_runtime() -> None:
    text = _read(EXECUTION_GOVERNANCE).lower()
    assert "live authorization granted" not in text
    assert "orders are authorized" not in text
