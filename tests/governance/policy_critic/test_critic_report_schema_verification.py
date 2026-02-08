"""
Governance: Policy Critic Report Schema Verification

Deterministic tests for:
- Policy critic result (report) required fields: max_severity, recommended_action,
  violations, minimum_test_plan, operator_questions, summary
- Violation required fields: rule_id, severity, message, evidence
- Governance report section when persisted: policy_critic, auto_apply_decision
"""

import json

import pytest

from src.governance.policy_critic.auto_apply_gate import (
    AutoApplyDecision,
    ApplyMode,
    persist_decision_to_report,
)
from src.governance.policy_critic.models import (
    Evidence,
    PolicyCriticResult,
    RecommendedAction,
    Severity,
    Violation,
)


# Required top-level keys in policy critic result dict (to_dict / to_canonical_dict)
POLICY_CRITIC_RESULT_REQUIRED_KEYS = [
    "max_severity",
    "recommended_action",
    "violations",
    "minimum_test_plan",
    "operator_questions",
    "summary",
]

# Required keys per violation
VIOLATION_REQUIRED_KEYS = ["rule_id", "severity", "message", "evidence", "suggested_fix"]

# Required keys per evidence item (evidence can be empty list)
EVIDENCE_KEYS = ["file_path", "line_range", "snippet", "pattern"]


class TestPolicyCriticResultSchemaRequiredFields:
    """PolicyCriticResult.to_dict() / to_canonical_dict() must include required fields."""

    def test_minimal_result_has_required_keys(self):
        result = PolicyCriticResult(
            max_severity=Severity.INFO,
            recommended_action=RecommendedAction.ALLOW,
            violations=[],
            minimum_test_plan=[],
            operator_questions=[],
            summary="OK",
        )
        d = result.to_dict()
        for key in POLICY_CRITIC_RESULT_REQUIRED_KEYS:
            assert key in d, f"Missing required key: {key}"
        assert d["max_severity"] == "INFO"
        assert d["recommended_action"] == "ALLOW"
        assert d["violations"] == []
        assert d["summary"] == "OK"

    def test_canonical_dict_also_has_required_keys(self):
        result = PolicyCriticResult(
            max_severity=Severity.WARN,
            recommended_action=RecommendedAction.REVIEW_REQUIRED,
            violations=[],
            summary="Review needed",
        )
        d = result.to_canonical_dict()
        for key in POLICY_CRITIC_RESULT_REQUIRED_KEYS:
            assert key in d, f"Missing required key in canonical: {key}"

    def test_violation_dict_has_required_keys(self):
        v = Violation(
            rule_id="R1",
            severity=Severity.WARN,
            message="Test",
            evidence=[Evidence(file_path="a.py", line_range="1-2")],
            suggested_fix="Fix it",
        )
        result = PolicyCriticResult(
            max_severity=Severity.WARN,
            recommended_action=RecommendedAction.REVIEW_REQUIRED,
            violations=[v],
            summary="",
        )
        d = result.to_dict()
        assert len(d["violations"]) == 1
        vd = d["violations"][0]
        for key in VIOLATION_REQUIRED_KEYS:
            assert key in vd, f"Violation missing key: {key}"
        assert len(vd["evidence"]) == 1
        for key in EVIDENCE_KEYS:
            assert key in vd["evidence"][0], f"Evidence missing key: {key}"


class TestGovernanceReportPersistedSchema:
    """Persisted report (governance section) has required structure."""

    def test_persist_decision_writes_policy_critic_and_auto_apply_sections(self, tmp_path):
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps({"run_id": "test-1"}, indent=2))

        decision = AutoApplyDecision(
            allowed=True,
            mode=ApplyMode.AUTO,
            reason="Test",
            decided_at="2026-01-10T12:00:00Z",
            policy_critic_result={
                "max_severity": "INFO",
                "recommended_action": "ALLOW",
                "violations": [],
                "minimum_test_plan": [],
                "operator_questions": [],
                "summary": "OK",
            },
            inputs_summary={"source": "test"},
        )
        persist_decision_to_report(report_path, decision)

        with open(report_path) as f:
            report = json.load(f)
        assert "governance" in report
        assert "policy_critic" in report["governance"]
        assert "auto_apply_decision" in report["governance"]
        pc = report["governance"]["policy_critic"]
        for key in POLICY_CRITIC_RESULT_REQUIRED_KEYS:
            assert key in pc, f"Persisted policy_critic missing key: {key}"
        assert report["governance"]["auto_apply_decision"]["allowed"] is True
        assert report["governance"]["auto_apply_decision"]["mode"] == "auto"
