from __future__ import annotations

from pathlib import Path

import pytest

from src.research.full_canonical_core_completion_plausibility_evaluation_v0 import (
    run_diagnostic_evaluation_v0,
)

CONFIRM = "GO_FULL_CANONICAL_CORE_COMPLETION_AND_PLAUSIBILITY_EVALUATION_DIAGNOSTIC_V0"


def _as_dict(result: object) -> dict[str, object]:
    if hasattr(result, "to_dict"):
        value = result.to_dict()
    elif hasattr(result, "__dict__"):
        value = dict(result.__dict__)
    else:
        pytest.fail(f"Unsupported diagnostic result type: {type(result)!r}")
    assert isinstance(value, dict)
    return value


def test_diagnostic_result_is_explicitly_not_promotion_evidence(tmp_path: Path) -> None:
    result = run_diagnostic_evaluation_v0(
        confirm=CONFIRM,
        repo_root=Path.cwd(),
        durable_evidence_root=tmp_path,
    )
    payload = _as_dict(result)

    assert payload["status"] == "SYSTEM_DIAGNOSTIC_ONLY"
    assert payload["promotion_admissible"] is False
    assert payload["system_economic_evidence_admissible"] is False
    assert payload["economic_validity_claim_allowed"] is False
    assert payload["promotion_boundary_status"] == "DIAGNOSTIC_ONLY_NOT_PROMOTION_EVIDENCE"

    reason_codes = set(payload["promotion_boundary_reason_codes"])
    assert "FULL_CANONICAL_CHAIN_PARITY_REQUIRED_BEFORE_SYSTEM_ECONOMIC_EVIDENCE" in reason_codes
    assert (
        "ECONOMIC_VIABILITY_EVIDENCE_V1_PASS_REQUIRED_BEFORE_PROMOTION_ADMISSIBILITY"
        in reason_codes
    )
    assert "DIAGNOSTIC_RESULT_IS_NOT_PROMOTION_EVIDENCE" in reason_codes
    assert "RAW_RESEARCH_EVIDENCE_IS_NOT_SYSTEM_ECONOMIC_EVIDENCE" in reason_codes


def test_diagnostic_result_grants_no_runtime_or_order_authority(tmp_path: Path) -> None:
    result = run_diagnostic_evaluation_v0(
        confirm=CONFIRM,
        repo_root=Path.cwd(),
        durable_evidence_root=tmp_path,
    )
    payload = _as_dict(result)

    for key in (
        "runtime_admissible",
        "live_authorized",
        "orders_allowed",
        "scheduler_runtime_allowed",
        "shadow_authorized",
        "paper_authorized",
        "testnet_authorized",
        "canary_authorized",
        "credential_access_allowed",
    ):
        assert payload[key] is False
