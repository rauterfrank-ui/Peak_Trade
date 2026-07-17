"""Static contract: system audit plan closeout SSOT v1.

Docs/config/tests-only. Guards residual-gap categories and closeout markers.
Does not mutate GitHub settings, AWS, OKX, runtime, or trading-core.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_JSON = REPO_ROOT / "config" / "governance" / "system_audit_plan_closeout_ssot_v1.json"
PLAN_DOC = REPO_ROOT / "docs" / "audits" / "Peak_Trade_Prioritaetenplan_Systemaudit_2026-07-17.md"

EXPECTED_BASE_SHA = "17febbfd677e8133ce529ddc8db6ad0fab1d0d58"

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "PEAK_TRADE_PRIORITAETENPLAN_SYSTEMAUDIT_2026_07_17=true",
    "SYSTEM_AUDIT_PLAN_CLOSEOUT=true",
    f"BASE_SHA={EXPECTED_BASE_SHA}",
    "SECOND_ACTIVE_TRUTH=false",
    "THIS_DOCUMENT_IS_THE_CANONICAL_PLAN_SSOT=true",
    "TRADING_CORE_CHANGED=false",
    "EXECUTION_SEMANTICS_CHANGED=false",
    "GITHUB_SETTINGS_MUTATED=false",
    "EXTERNAL_SYSTEM_MUTATIONS=false",
    "RUNTIME_BRIDGE_ACTIVATED=false",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "CONFIRMED_DEFECT_COUNT=0",
    "PARTIAL_READ_ONLY_AUDIT",
    "PARTIAL_PASS_PRIVATE_NOT_VERIFIABLE",
    "DONE_READ_ONLY",
    "INVENTORY DONE",
    "# Verbleibende Restlücken nach Audit-Closeout",
    "### A. CONFIRMED_DEFECT",
    "### B. ACCESS_OR_CREDENTIAL_BLOCKED",
    "### C. INTENTIONAL_GOVERNANCE_DEBT",
    "### D. OPTIONAL_HYGIENE",
    "### E. INTENTIONAL_BLOCKED_STATE",
    "NONE_PENDING_OPERATOR_DECISION",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "TRADING_CORE_CHANGED=true",
    "EXECUTION_SEMANTICS_CHANGED=true",
    "GITHUB_SETTINGS_MUTATED=true",
    "EXTERNAL_SYSTEM_MUTATIONS=true",
    "RUNTIME_BRIDGE_ACTIVATED=true",
    "LIVE_AUTHORIZED=true",
    "ORDERS_ENABLED=true",
    "SECOND_ACTIVE_TRUTH=true",
    "CONFIRMED_DEFECT_COUNT=1",
)

REQUIRED_STATUS_PHRASES: tuple[str, ...] = (
    "INVENTORY DONE",
    "PR `#5296` squash-merged",
    "Konsolidierung NOT_STARTED",
    "Decommission NOT_STARTED",
    "kein Authority Leak",
    "keine Runtime-Aktivierung",
    "PARTIAL_READ_ONLY_AUDIT",
    "PARTIAL_PASS_PRIVATE_NOT_VERIFIABLE",
    "DONE_READ_ONLY",
    "Actual ruleset drift count",
    "Actual workflow drift count",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing: {path}"
    return path.read_text(encoding="utf-8")


def _load() -> dict:
    return json.loads(_read(SSOT_JSON))


def test_plan_doc_markers_and_forbidden_claims() -> None:
    text = _read(PLAN_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing marker: {marker}"
    lowered = text.lower()
    for claim in FORBIDDEN_CLAIMS:
        assert claim.lower() not in lowered, f"forbidden claim: {claim}"
    for phrase in REQUIRED_STATUS_PHRASES:
        assert phrase in text, f"missing status phrase: {phrase}"


def test_ssot_priority_and_gap_counts() -> None:
    payload = _load()
    status = payload["priority_status"]
    assert status["p1_github_ssot"] == "DONE"
    assert status["p1_tombstone_documentation"] == "DONE"
    assert status["p1_surface_p_contract_drift"] == "DONE"
    assert status["p2_promotion_owner_inventory"] == "DONE"
    assert status["p2_risk_sizing_inventory"] == "DONE"
    assert status["p2_risk_sizing_consolidation"] == "NOT_STARTED"
    assert status["p2_legacy_order_intent_inventory"] == "INVENTORY_DONE"
    assert status["p2_legacy_order_intent_consolidation"] == "NOT_STARTED"
    assert status["p2_legacy_order_intent_decommission"] == "NOT_STARTED"
    assert status["p2_legacy_order_intent_authority_leak_detected"] is False
    assert status["p3_aws"] == "PARTIAL_READ_ONLY_AUDIT"
    assert status["p3_okx"] == "PARTIAL_PASS_PRIVATE_NOT_VERIFIABLE"
    assert status["p3_monitoring"] == "DONE"
    assert status["p4_repository_hygiene"] == "DONE_READ_ONLY"

    gaps = payload["residual_gap_counts"]
    assert gaps["confirmed_defect_count"] == 0
    assert gaps["access_blocked_gap_count"] == 2
    assert gaps["intentional_governance_debt_count"] == 3
    assert gaps["optional_hygiene_count"] == 2
    assert gaps["intentional_blocked_state_count"] == 6
    assert payload["residual_gaps"]["confirmed_defect"] == []
    assert payload["definition_of_done_reconciled"] is True
    assert payload["next_canonical_priority"] == "NONE_PENDING_OPERATOR_DECISION"


def test_hygiene_and_aws_okx_notes_fail_closed() -> None:
    payload = _load()
    hygiene = payload["repository_hygiene"]
    assert hygiene["classic_branch_protection_effective"] is True
    assert hygiene["required_checks_ssot_match"] is True
    assert hygiene["required_checks_count"] == 11
    assert hygiene["local_workflow_count"] == 73
    assert hygiene["remote_workflow_api_count"] == 80
    assert hygiene["historical_remote_only_count"] == 7
    assert hygiene["actual_ruleset_drift_count"] == 0
    assert hygiene["actual_workflow_drift_count"] == 0
    assert hygiene["github_mutation_required"] is False

    aws = payload["aws_notes"]
    assert aws["canonical_account_id"] == "511913187493"
    assert aws["dual_live_sts_claimed_in_durable_audit"] is False
    assert aws["secret_values_read"] is False
    assert aws["aws_mutations_performed"] is False
    assert aws["not_acute_trading_core_defect"] is True

    okx = payload["okx_notes"]
    assert okx["public_rest_reachable"] is True
    assert okx["public_websocket_reachable"] is True
    assert okx["private_auth_verified"] is False
    assert okx["not_confirmed_drift"] is True


def test_governance_readme_points_to_plan() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "Peak_Trade_Prioritaetenplan_Systemaudit_2026-07-17.md" in readme


def test_no_second_active_plan_filename() -> None:
    audits = REPO_ROOT / "docs" / "audits"
    matches = sorted(audits.glob("*Prioritaetenplan*Systemaudit*"))
    assert [p.name for p in matches] == ["Peak_Trade_Prioritaetenplan_Systemaudit_2026-07-17.md"]
