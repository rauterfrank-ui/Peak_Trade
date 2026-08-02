"""Capability 7.2 — single-future stateful no-order runtime activation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.single_future_stateful_no_order_runtime_activation_v1.authority_matrix_v1 import (
    inventory_activation_authority_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    build_canonical_config_payload_v1,
    load_activation_config_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    PACKAGE_MARKER,
    PREDECESSOR_CAPABILITY_ID,
    PREDECESSOR_MERGE_SHA,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.cycle_harness_v1 import (
    build_capability_evidence_v1,
    prove_activation_success_v1,
    prove_precondition_blocks_v1,
    prove_startup_restart_v1,
    run_failure_injections_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.network_boundary_v1 import (
    evaluate_public_md_transport_v1,
    prove_network_credential_boundary_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.preconditions_v1 import (
    prove_preconditions_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    prove_execution_port_separation_v1,
    refuse_real_execution_adapter_construction_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1 as HOST_CALL_GRAPH,
)

REPO_SHA = PREDECESSOR_MERGE_SHA


def test_constants_authority_and_call_graph() -> None:
    assert CAPABILITY_ID.endswith("RUNTIME_ACTIVATION_V1")
    assert PACKAGE_MARKER.endswith("=true")
    assert CORE_LOGIC_CHANGE is False
    assert PREDECESSOR_CAPABILITY_ID.endswith("ACTIONABILITY_EVIDENCE_V1")
    inv = inventory_activation_authority_v1()
    assert inv["ONE_CANONICAL_ACTIVATION_AUTHORITY"] is True
    assert inv["NO_PARALLEL_ACTIVATION_PATH"] is True
    assert "repository_config_integrity_check" in HOST_CALL_GRAPH
    assert "simulated_execution_port" in HOST_CALL_GRAPH
    assert "activation_state_validation" in HOST_CALL_GRAPH


def test_preconditions_from_cap71_evidence() -> None:
    pre = prove_preconditions_v1(repository_sha=REPO_SHA)
    assert pre["PRECONDITIONS_ALL_PROVEN"] is True
    assert pre["matrix"]["ENTRY_END_TO_END_EVIDENCE_PROVEN"] is True
    assert pre["matrix"]["EXIT_END_TO_END_EVIDENCE_PROVEN"] is True
    assert pre["matrix"]["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False


def test_activation_success_and_blocks(tmp_path: Path) -> None:
    ok = prove_activation_success_v1(repository_sha=REPO_SHA, work_root=tmp_path / "ok")
    assert ok["FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE"] is True
    assert ok["SIMULATED_EXECUTION_ACTIVE"] is True
    assert ok["PUBLIC_MD_NETWORK_SESSION_OBSERVED"] is False
    blocks = prove_precondition_blocks_v1(repository_sha=REPO_SHA, work_root=tmp_path / "blocks")
    assert blocks["ACTIVATION_BLOCK_ON_MISSING_PRECONDITION"] is True


def test_startup_restart_and_failures(tmp_path: Path) -> None:
    startup = prove_startup_restart_v1(repository_sha=REPO_SHA, work_root=tmp_path / "startup")
    assert startup["ok"] is True
    assert startup["FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE"] is True
    failures = run_failure_injections_v1(repository_sha=REPO_SHA, work_root=tmp_path / "fi")
    assert failures["FAILURE_INJECTION_PROVEN"] is True
    assert failures["rollback"]["ROLLBACK_PROVEN"] is True


def test_execution_port_and_network_boundaries() -> None:
    port = prove_execution_port_separation_v1()
    assert port["SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT"] is True
    assert port["NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST"] is True
    with pytest.raises(Exception):
        refuse_real_execution_adapter_construction_v1()
    net = prove_network_credential_boundary_v1()
    assert net["ok"] is True
    assert net["PRIVATE_ENDPOINT_REACHABLE"] is False
    denied = evaluate_public_md_transport_v1(
        url="https://www.okx.com/api/v5/trade/order", method="GET"
    )
    assert denied.allowed is False
    post = evaluate_public_md_transport_v1(
        url="https://www.okx.com/api/v5/public/instruments", method="POST"
    )
    assert post.allowed is False
    auth = evaluate_public_md_transport_v1(
        url="https://www.okx.com/api/v5/public/instruments",
        method="GET",
        headers={"Authorization": "Bearer x"},
    )
    assert auth.allowed is False


def test_parity_and_full_evidence(tmp_path: Path) -> None:
    parity = prove_trading_logic_parity_v1()
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    cfg_payload = build_canonical_config_payload_v1(repository_sha=REPO_SHA)
    assert cfg_payload["LIVE_ORDERS"] is False
    evidence = build_capability_evidence_v1(
        repository_sha=REPO_SHA, work_root=tmp_path / "evidence"
    )
    payload = evidence.to_dict()
    assert evidence.ok is True
    assert payload["claims"]["FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE"] is True
    assert payload["claims"]["NETWORK_SESSION_STARTED"] is False
    assert payload["claims"]["AUTHORIZATION_CONSUMED"] is False
    assert payload["predecessor_capability_id"] == PREDECESSOR_CAPABILITY_ID


def test_repo_config_loads() -> None:
    cfg = load_activation_config_v1(require_active_claim=True)
    assert cfg.capability_id == CAPABILITY_ID
    assert cfg.full_canonical_stateful_runtime_active is True
    assert cfg.live_orders is False
    assert cfg.public_md_network_session_observed is False
