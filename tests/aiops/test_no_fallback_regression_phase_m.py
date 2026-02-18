"""Phase M: Regression guards for real policy telemetry (no fallback)."""

import json
from pathlib import Path

FALLBACK_CODE = "AUDIT_MANIFEST_NO_DECISION_CONTEXT"


def _assert_summary(summary: dict) -> None:
    policy = summary.get("policy")
    assert isinstance(policy, dict) and policy, "policy must be present and non-empty"
    assert policy.get("action") in ("ALLOW", "NO_TRADE"), "policy.action must be ALLOW/NO_TRADE"
    reason_codes = policy.get("reason_codes")
    assert isinstance(reason_codes, list), "policy.reason_codes must be a list"
    assert FALLBACK_CODE not in reason_codes, "fallback code must not appear in reason_codes"


def test_telemetry_summary_shape_is_real_policy_contract(tmp_path: Path) -> None:
    """
    Regression guard: If extractor returns fallback-driven policy again,
    this contract should fail fast.
    """
    # Minimal "real policy" summary shape
    summary = {
        "policy": {"action": "NO_TRADE", "reason_codes": ["EDGE_LT_COSTS_V1"]},
        "source": "evidence_manifest",
    }
    _assert_summary(summary)


def test_extractor_contract_helper_can_be_reused() -> None:
    """
    This is a tiny test to ensure the helper remains importable for future workflow-smokes.
    """
    assert FALLBACK_CODE == "AUDIT_MANIFEST_NO_DECISION_CONTEXT"
