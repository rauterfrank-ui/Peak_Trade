"""Focused verifier for §11.13.5.F Live-Canary cybersecurity-gate reevaluation."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.verify_section_11_13_5_live_canary_cybersecurity_gate_reevaluation_v1 import (
    verify_section_11_13_5_live_canary_cybersecurity_gate_reevaluation_v1,
)

REPO = Path(__file__).resolve().parents[2]
FRESH_ROOT = (
    REPO
    / "evidence/ops/section_11_13_5_live_canary_cybersecurity_gate_reevaluation_v1"
    / "20260815T193911Z"
)


def test_live_canary_cybersecurity_gate_reevaluation_verifier_pass() -> None:
    result = verify_section_11_13_5_live_canary_cybersecurity_gate_reevaluation_v1(FRESH_ROOT)
    assert result["ok"] is True
    assert result["MANIFEST_VERIFY_RC"] == 0
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "PASS"
    assert result["LIVE_AUTHORIZED"] is False
    assert result["LIVE_CANARY_EXECUTED"] is False
    assert result["CYBERSECURITY_GATE_REQUIREMENTS_PROVEN"] == 21
    assert result["CYBERSECURITY_GATE_REQUIREMENTS_TOTAL"] == 21
    assert result["CURRENT_ORIGIN_MAIN_SHA"] == ("2c72dfd81d226fd04d7f4d4183041b54d1526f55")
