"""Owner tests for PHASE_9_2_PUBLIC_MD_SESSION_PREFLIGHT_V1."""

from __future__ import annotations

from pathlib import Path

from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    EEA_PUBLIC_MD_HOST,
    SESSION_LADDER,
    SMOKE_DURATION_SECONDS,
    SMOKE_POLL_INTERVAL_SECONDS,
    TASK_ID,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.evidence_v1 import (
    build_preflight_evidence_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.failure_injection_v1 import (
    run_failure_injections_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.network_boundary_v1 import (
    prove_phase92_network_and_execution_boundary_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.parity_v1 import prove_phase92_parity_v1
from src.ops.phase_9_2_public_md_session_preflight_v1.prerequisites_v1 import (
    prove_phase92_prerequisites_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.smoke_session_contract_v1 import (
    build_smoke_session_contract_v1,
    validate_smoke_session_contract_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_SHA = "5c1daf024b2c693c350b664bcae6ae2cb160543d"


def test_session_ladder_and_smoke_budgets() -> None:
    assert SESSION_LADDER[0] == "SMOKE_SESSION"
    assert len(SESSION_LADDER) == 7
    contract = build_smoke_session_contract_v1(repository_sha=REPO_SHA, repo_root=REPO_ROOT)
    assert contract.duration_seconds == SMOKE_DURATION_SECONDS
    assert contract.poll_interval_seconds == SMOKE_POLL_INTERVAL_SECONDS
    assert contract.poll_interval_seconds > 0
    assert contract.minimum_interval_seconds > 0
    assert contract.eea_public_md_host == EEA_PUBLIC_MD_HOST
    assert not contract.network_session_authorized
    assert validate_smoke_session_contract_v1(contract) == []


def test_prerequisites_and_network_boundary() -> None:
    pre = prove_phase92_prerequisites_v1(repository_sha=REPO_SHA, repo_root=REPO_ROOT)
    assert pre["ok"] is True
    assert pre["STRATEGY_REGISTRY_CLOSED"] is True
    assert pre["FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE"] is True
    assert pre["SIMULATED_EXECUTION_ACTIVE"] is True
    net = prove_phase92_network_and_execution_boundary_v1()
    assert net["ok"] is True
    assert net["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert net["AUTH_HEADER_PRESENT"] is False
    assert net["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert net["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert net["LIVE_PATH_REACHABLE"] is False
    assert net["TESTNET_PATH_REACHABLE"] is False


def test_parity_unchanged() -> None:
    assert CORE_LOGIC_CHANGE is False
    parity = prove_phase92_parity_v1()
    assert parity["ok"] is True
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["CORE_LOGIC_CHANGED"] is False


def test_failure_injections() -> None:
    contract = build_smoke_session_contract_v1(repository_sha=REPO_SHA, repo_root=REPO_ROOT)
    result = run_failure_injections_v1(contract=contract)
    assert result["ok"] is True


def test_build_preflight_evidence_ready() -> None:
    evidence = build_preflight_evidence_v1(
        repository_sha=REPO_SHA,
        repo_root=REPO_ROOT,
        materialize=True,
    )
    assert evidence.ok is True
    assert evidence.capability_id == CAPABILITY_ID
    assert evidence.task_id == TASK_ID
    assert evidence.claims["PHASE_9_2_SMOKE_SESSION_PREFLIGHT_READY"] is True
    assert evidence.claims["CONFIRM_TOKEN_PLAINTEXT_EXPOSED"] is False
    assert evidence.gaps == []
    cfg = REPO_ROOT / "config/ops/phase_9_2_public_md_smoke_session_contract_v1.json"
    assert cfg.is_file()
    readiness = (
        REPO_ROOT
        / "docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1"
        / "preflight"
        / "phase_9_2_smoke_session_readiness_report_v1.json"
    )
    assert readiness.is_file()


def test_zero_poll_rejected() -> None:
    contract = build_smoke_session_contract_v1(repository_sha=REPO_SHA, repo_root=REPO_ROOT)
    bad = type(contract)(**{**contract.to_dict(), "poll_interval_seconds": 0.0})
    gaps = validate_smoke_session_contract_v1(bad)
    assert "ZERO_INTERVAL_POLL" in gaps
