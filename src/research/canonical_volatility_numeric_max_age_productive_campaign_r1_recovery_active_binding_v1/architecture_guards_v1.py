"""Architecture guards for R1 recovery / active-binding package."""

from __future__ import annotations

from pathlib import Path

from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.constants_v1 import (
    ADDITIONAL_EVIDENCE_RECLASSIFICATION,
    CROSS_SHA_REUSE_ALLOWED,
    SYNTHETIC_S01_ALLOWED,
)

_PACKAGE_DIR = Path(__file__).resolve().parent


def assert_r1_recovery_architecture_guards_v1() -> dict[str, bool]:
    texts: list[str] = []
    for path in sorted(_PACKAGE_DIR.glob("*.py")):
        if path.name == "architecture_guards_v1.py":
            continue
        texts.append(path.read_text(encoding="utf-8"))
    text = "\n".join(texts)
    if "CAMPAIGN_R1_RECOVERY_ACTIVE_BINDING_V1" not in text:
        raise AssertionError("package_marker_missing")
    if CROSS_SHA_REUSE_ALLOWED or SYNTHETIC_S01_ALLOWED or ADDITIONAL_EVIDENCE_RECLASSIFICATION:
        raise AssertionError("forbidden_authority_flags_enabled")
    if "LIVE_AUTHORIZED = True" in text or "ORDERS_ALLOWED = True" in text:
        raise AssertionError("execution_authority_flag_forbidden")
    return {
        "package_marker_present": True,
        "cross_sha_reuse_allowed": False,
        "synthetic_s01_allowed": False,
        "additional_evidence_reclassification": False,
    }
