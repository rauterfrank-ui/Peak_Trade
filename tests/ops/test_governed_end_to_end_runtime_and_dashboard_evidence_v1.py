"""Deterministic contract tests for CAPABILITY_O7 offline governed evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.governed_end_to_end_runtime_and_dashboard_evidence_v1.constants_v1 import (
    CAPABILITY_ID,
    DEFERRED_CLASSIFICATIONS,
    LADDER_DEFERRED_ITEMS,
    LADDER_PROVEN_ITEMS,
    PRODUCTION_SURFACES_REUSED,
    REQUIRED_TRUTH_CLASSIFICATIONS,
    SAFETY_INVARIANTS,
)
from src.ops.governed_end_to_end_runtime_and_dashboard_evidence_v1.harness_v1 import (
    run_o7_offline_governed_evidence_harness_v1,
)


@pytest.fixture()
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_capability_constants_and_safety() -> None:
    assert CAPABILITY_ID.endswith("_V1")
    assert SAFETY_INVARIANTS["CORE_LOGIC_CHANGE_ALLOWED"] is False
    assert SAFETY_INVARIANTS["NETWORK_SESSION_ALLOWED"] is False
    assert SAFETY_INVARIANTS["ORDERS_ALLOWED"] is False
    assert SAFETY_INVARIANTS["DASHBOARD_TRADING_AUTHORITY"] is False
    assert SAFETY_INVARIANTS["PARALLEL_LAUNCHER_FORBIDDEN"] is True
    assert REQUIRED_TRUTH_CLASSIFICATIONS["O7_BOUNDED_OFFLINE_EVIDENCE_COMPLETE"] is True
    assert REQUIRED_TRUTH_CLASSIFICATIONS["O7_NETWORK_BOUND_EVIDENCE_COMPLETE"] is False
    assert REQUIRED_TRUTH_CLASSIFICATIONS["O7_FULL_CAPABILITY_CLOSED"] is False
    assert DEFERRED_CLASSIFICATIONS["SEPARATE_NETWORK_SESSION_OWNER_GO_REQUIRED"] is True
    assert len(LADDER_PROVEN_ITEMS) == 10
    assert len(LADDER_DEFERRED_ITEMS) == 3
    assert "canonical_local_launcher_and_process_supervision_v1" in PRODUCTION_SURFACES_REUSED
    assert "runtime_health_recovery_and_failure_injection_closure_v1" in PRODUCTION_SURFACES_REUSED


def test_offline_harness_proves_bounded_ladder(tmp_path: Path, repo_root: Path) -> None:
    result = run_o7_offline_governed_evidence_harness_v1(
        repository_root=repo_root,
        work_root=tmp_path / "o7_work",
        repository_sha="a" * 40,
    )
    assert result["ok"] is True
    assert result["PARALLEL_AUTHORITIES_CREATED"] is False
    proven = set(result["O7_LADDER_ITEMS_PROVEN"])
    assert proven == set(LADDER_PROVEN_ITEMS)
    assert result["O7_LADDER_ITEMS_DEFERRED"] == list(LADDER_DEFERRED_ITEMS)
    metrics = result["OPERATIONAL_METRICS"]
    assert metrics["startup_success_count"] >= 1
    assert metrics["graceful_shutdown_success"] is True
    assert metrics["recovery_success"] is True
    assert metrics["orders_submitted"] == 0
    assert metrics["credentials_used"] == 0
    assert metrics["network_session_started"] is False
    assert metrics["authorization_consumed"] is False
    assert metrics["confirm_token_minted"] is False
    assert result["PROOFS"]["multi_session"]["duplicate_blocked"] is True
    assert (
        result["PROOFS"]["dashboard_restart_without_scaffold_restart"]["scaffold_pid_unchanged"]
        is True
    )
    assert (
        result["PROOFS"]["scaffold_restart_with_read_model_recovery"]["read_model_digest_match"]
        is True
    )
    assert result["PROOFS"]["boundary_preservation"]["dashboard_trading_authority"] is False


def test_deferred_network_classifications_are_explicit() -> None:
    assert DEFERRED_CLASSIFICATIONS["LONG_RUNNING_PUBLIC_MD_SESSION"] == "DEFERRED"
    assert DEFERRED_CLASSIFICATIONS["LIVE_OHLCV_MATRIX_CONTINUITY"] == "DEFERRED"
    assert DEFERRED_CLASSIFICATIONS["END_TO_END_NETWORK_LATENCY"] == "DEFERRED"
    assert "LONG_RUNNING_PUBLIC_MD_SESSION" in LADDER_DEFERRED_ITEMS
