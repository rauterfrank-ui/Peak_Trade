from __future__ import annotations

from pathlib import Path

import pytest

from research.multi_future_ghv_counterfactual_distance_lab_v3.proof_gates_v3 import (
    prove_s08_stateful_reference_v3,
    prove_state_isolation_v3,
    prove_stateful_adapter_contract_v3,
    prove_symmetric_fork_v3,
    run_pre_run_gates_v3,
)


def test_stateful_adapter_contract_v3() -> None:
    proof = prove_stateful_adapter_contract_v3()
    assert proof["STATEFUL_ADAPTER_USES_CURRENT_STATE_CONTRACT"] is True


def test_state_isolation_v3() -> None:
    iso = prove_state_isolation_v3()
    assert iso["INTER_FLIGHT_STATE_LEAK_COUNT"] == 0
    assert iso["INTER_MODEL_STATE_LEAK_COUNT"] == 0


def test_symmetric_fork_v3() -> None:
    fork = prove_symmetric_fork_v3()
    assert fork["SYMMETRIC_FORK_PROVEN"] is True
    assert fork["MODEL_B_V3_VS_CURRENT_REFERENCE_PASS"] is True


def test_s08_stateful_reference_v3() -> None:
    s08 = prove_s08_stateful_reference_v3()
    assert s08["S08_STATEFUL_REFERENCE_PASS"] is True
    assert s08["S08_V3_DECISION"] == "enter_long"


def test_pre_run_gates_v3(tmp_path: Path) -> None:
    gates = run_pre_run_gates_v3(tmp_path)
    assert gates["gates_ok"] is True
