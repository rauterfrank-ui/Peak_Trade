"""Focused verifier for §11.13.5.E1 fresh OKX temp-security clearance evidence."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.verify_section_11_13_5_okx_temp_security_clearance_evidence_collection_v1 import (
    verify_section_11_13_5_okx_temp_security_clearance_evidence_collection_v1,
)

REPO = Path(__file__).resolve().parents[2]
FRESH_ROOT = (
    REPO
    / "evidence/ops/section_11_13_5_okx_temp_security_clearance_evidence_collection_v1"
    / "20260815T190010Z"
)


def test_fresh_okx_temp_security_clearance_collection_verifier_pass() -> None:
    result = verify_section_11_13_5_okx_temp_security_clearance_evidence_collection_v1(FRESH_ROOT)
    assert result["ok"] is True
    assert result["MANIFEST_VERIFY_RC"] == 0
    assert result["OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE"] == "PRESENT_PROVEN"
    assert result["LIVE_CANARY_CYBERSECURITY_GATE"] == "NOT_REEVALUATED"
    assert result["LIVE_AUTHORIZED"] is False
    assert result["CURRENT_ORIGIN_MAIN_SHA"] == ("c271364d1cc85d65cabc6f1938fe5b9ed8b3fc64")
