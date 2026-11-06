"""
Governance: Policy Critic Report Determinism

Deterministic tests for:
- Stable ordering of findings (violations) in canonical output
- Same inputs => identical report hash when serialized canonically
"""

import hashlib
import json

import pytest

from src.governance.policy_critic.models import (
    Evidence,
    PolicyCriticResult,
    RecommendedAction,
    Severity,
    Violation,
)


def _canonical_json_hash(obj: dict) -> str:
    """Stable SHA256 of JSON (sort_keys=True, no trailing whitespace)."""
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


class TestPolicyCriticReportStableOrdering:
    """to_canonical_dict() produces stable ordering of violations and evidence."""

    def test_violations_sorted_by_rule_id_then_message(self):
        v1 = Violation(rule_id="R2", severity=Severity.WARN, message="B", evidence=[])
        v2 = Violation(rule_id="R1", severity=Severity.BLOCK, message="A", evidence=[])
        v3 = Violation(rule_id="R1", severity=Severity.INFO, message="C", evidence=[])
        result = PolicyCriticResult(
            max_severity=Severity.BLOCK,
            recommended_action=RecommendedAction.AUTO_APPLY_DENY,
            violations=[v1, v2, v3],
            summary="",
        )
        d = result.to_canonical_dict()
        rule_ids = [v["rule_id"] for v in d["violations"]]
        messages = [v["message"] for v in d["violations"]]
        assert rule_ids == ["R1", "R1", "R2"]
        assert messages == ["A", "C", "B"]

    def test_evidence_sorted_by_file_path_then_line_range(self):
        e1 = Evidence(file_path="z.py", line_range="10-11")
        e2 = Evidence(file_path="a.py", line_range="2-3")
        e3 = Evidence(file_path="a.py", line_range="1-2")
        v = Violation(rule_id="R1", severity=Severity.WARN, message="M", evidence=[e1, e2, e3])
        result = PolicyCriticResult(
            max_severity=Severity.WARN,
            recommended_action=RecommendedAction.REVIEW_REQUIRED,
            violations=[v],
            summary="",
        )
        d = result.to_canonical_dict()
        evidence = d["violations"][0]["evidence"]
        paths = [e["file_path"] for e in evidence]
        assert paths == ["a.py", "a.py", "z.py"]
        assert [e["line_range"] for e in evidence] == ["1-2", "2-3", "10-11"]

    def test_minimum_test_plan_and_operator_questions_sorted(self):
        result = PolicyCriticResult(
            max_severity=Severity.INFO,
            recommended_action=RecommendedAction.ALLOW,
            violations=[],
            minimum_test_plan=["run b", "run a"],
            operator_questions=["q2", "q1"],
            summary="",
        )
        d = result.to_canonical_dict()
        assert d["minimum_test_plan"] == ["run a", "run b"]
        assert d["operator_questions"] == ["q1", "q2"]


class TestPolicyCriticReportSameInputsSameHash:
    """Same logical inputs produce identical canonical report hash."""

    def test_same_violations_different_list_order_same_hash(self):
        v1 = Violation(rule_id="R1", severity=Severity.WARN, message="M1", evidence=[])
        v2 = Violation(rule_id="R2", severity=Severity.INFO, message="M2", evidence=[])
        result_a = PolicyCriticResult(
            max_severity=Severity.WARN,
            recommended_action=RecommendedAction.REVIEW_REQUIRED,
            violations=[v1, v2],
            summary="Same",
        )
        result_b = PolicyCriticResult(
            max_severity=Severity.WARN,
            recommended_action=RecommendedAction.REVIEW_REQUIRED,
            violations=[v2, v1],
            summary="Same",
        )
        hash_a = _canonical_json_hash(result_a.to_canonical_dict())
        hash_b = _canonical_json_hash(result_b.to_canonical_dict())
        assert hash_a == hash_b

    def test_same_evidence_different_order_same_hash(self):
        e1 = Evidence(file_path="a.py", line_range="1")
        e2 = Evidence(file_path="b.py", line_range="2")
        v_a = Violation(rule_id="R1", severity=Severity.WARN, message="M", evidence=[e1, e2])
        v_b = Violation(rule_id="R1", severity=Severity.WARN, message="M", evidence=[e2, e1])
        result_a = PolicyCriticResult(
            max_severity=Severity.WARN,
            recommended_action=RecommendedAction.REVIEW_REQUIRED,
            violations=[v_a],
            summary="",
        )
        result_b = PolicyCriticResult(
            max_severity=Severity.WARN,
            recommended_action=RecommendedAction.REVIEW_REQUIRED,
            violations=[v_b],
            summary="",
        )
        hash_a = _canonical_json_hash(result_a.to_canonical_dict())
        hash_b = _canonical_json_hash(result_b.to_canonical_dict())
        assert hash_a == hash_b

    def test_different_summary_different_hash(self):
        result_a = PolicyCriticResult(
            max_severity=Severity.INFO,
            recommended_action=RecommendedAction.ALLOW,
            violations=[],
            summary="A",
        )
        result_b = PolicyCriticResult(
            max_severity=Severity.INFO,
            recommended_action=RecommendedAction.ALLOW,
            violations=[],
            summary="B",
        )
        hash_a = _canonical_json_hash(result_a.to_canonical_dict())
        hash_b = _canonical_json_hash(result_b.to_canonical_dict())
        assert hash_a != hash_b
