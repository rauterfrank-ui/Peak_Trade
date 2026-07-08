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


def test_diagnostic_result_explicitly_blocks_full_system_economic_evidence_until_full_chain_parity(
    tmp_path: Path,
) -> None:
    result = run_diagnostic_evaluation_v0(
        confirm=CONFIRM,
        repo_root=Path.cwd(),
        durable_evidence_root=tmp_path,
    )
    payload = _as_dict(result)

    assert payload["status"] == "SYSTEM_DIAGNOSTIC_ONLY"
    assert payload["full_canonical_chain_wired"] is False
    assert payload["backtest_runtime_decision_parity_pass"] is False
    assert payload["system_economic_evidence_admissible"] is False
    assert payload["economic_validity_claim_allowed"] is False
    assert payload["full_canonical_chain_wired_status"] == "DIAGNOSTIC_ONLY_NOT_FULLY_WIRED"

    reason_codes = set(payload["full_canonical_chain_wired_reason_codes"])
    assert "FULL_CANONICAL_CHAIN_WIRED_STATUS_NOT_YET_PROVEN" in reason_codes
    assert "BACKTEST_RUNTIME_DECISION_PARITY_NOT_YET_PROVEN" in reason_codes
    assert "SYSTEM_ECONOMIC_EVIDENCE_REQUIRES_FULL_CANONICAL_CHAIN_PARITY" in reason_codes
    assert "DIAGNOSTIC_RESULT_DOES_NOT_WIRE_CANONICAL_CHAIN" in reason_codes


def test_full_chain_status_contract_grants_no_promotion_runtime_or_order_authority(
    tmp_path: Path,
) -> None:
    result = run_diagnostic_evaluation_v0(
        confirm=CONFIRM,
        repo_root=Path.cwd(),
        durable_evidence_root=tmp_path,
    )
    payload = _as_dict(result)

    assert payload["promotion_admissible"] is False
    assert payload["runtime_admissible"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False
    assert payload["scheduler_runtime_allowed"] is False
    assert payload["shadow_authorized"] is False
    assert payload["paper_authorized"] is False
    assert payload["testnet_authorized"] is False
    assert payload["canary_authorized"] is False
    assert payload["credential_access_allowed"] is False
