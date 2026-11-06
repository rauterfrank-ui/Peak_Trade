"""Contracts for relocated occupancy classify and C1-gate tokens.

No SecretRef, vault, HMAC, GET, POST, or Keychain access.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    C1_GATE_BAR,
    C1_GATE_NATIVE_ID,
    NON_EXECUTABLE_NEXT_OWNER_GO,
    OCCUPANCY_NEXT_OWNER_GO,
    POST_NEXT_OWNER_GO,
    PREVIOUS_C1_VENUE_EVENT_TIME,
    V5_OWNER_GO,
    _classify_occupancy_v1,
    _evaluate_c1_gate_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_occupancy_classify_and_c1_gate_v1.py"
)
K2_MARKERS = (
    "secretref",
    "SecretRef",
    "file_vault",
    "FILE_VAULT",
    "vault.json",
    "live_credential_ephemeral_v1",
    "hmac",
    "HMAC",
)


def test_extracted_module_has_no_k2_credential_markers() -> None:
    source = SRC.read_text(encoding="utf-8")
    for marker in K2_MARKERS:
        assert marker not in source


def test_frozen_tokens_unchanged() -> None:
    assert PREVIOUS_C1_VENUE_EVENT_TIME == 1789527780.0
    assert C1_GATE_NATIVE_ID == "0G-USDT-SWAP"
    assert C1_GATE_BAR == "1m"
    assert POST_NEXT_OWNER_GO == (
        "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
    )
    assert NON_EXECUTABLE_NEXT_OWNER_GO == (
        "SEPARATE_OWNER_GO_FOR_NEXT_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_FROM_PERSISTED_CURSOR"
    )
    assert OCCUPANCY_NEXT_OWNER_GO == (
        "SEPARATE_OWNER_GO_FOR_CURRENT_OCCUPANCY_DISPOSITION_AFTER_FRESH_REPROOF"
    )
    assert V5_OWNER_GO == (
        "OWNER_GO_CONDITION_GATED_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_AFTER_C1_BOUNDARY_1789527780_V1"
    )


def test_c1_gate_satisfied_and_not_yet() -> None:
    satisfied_ts_ms = 1_789_527_840_000
    payload = {
        "code": "0",
        "data": [
            [
                str(satisfied_ts_ms),
                "0.1880",
                "0.1880",
                "0.1880",
                "0.1880",
                "10",
                "100",
                "USDT",
                "1",
            ]
        ],
    }
    gate = _evaluate_c1_gate_v1(payload=payload)
    assert gate["CONDITION_GATE"] == "SATISFIED"
    assert gate["POST_COUNT"] == "0"
    assert gate["AUTH_HEADER_SENT"] == "false"
    too_old = {
        "code": "0",
        "data": [
            [
                "1789527780000",
                "0.1880",
                "0.1880",
                "0.1880",
                "0.1880",
                "10",
                "100",
                "USDT",
                "1",
            ]
        ],
    }
    not_yet = _evaluate_c1_gate_v1(payload=too_old)
    assert not_yet["CONDITION_GATE"] == "NOT_YET_SATISFIED"


def test_occupancy_absent_and_present() -> None:
    absent = _classify_occupancy_v1(
        positions_payload={"code": "0", "data": []},
        pending_payload={"code": "0", "data": []},
        config_payload={"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]},
        positions_error="",
        pending_error="",
        config_error="",
    )
    assert absent["OCCUPANCY_STATUS"] == "OCCUPANCY_ABSENT"
    assert absent["OCCUPANCY_ABSENT"] == "true"
    present = _classify_occupancy_v1(
        positions_payload={
            "code": "0",
            "data": [{"instId": "0G-USDT-SWAP", "pos": "1"}],
        },
        pending_payload={"code": "0", "data": []},
        config_payload={"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]},
        positions_error="",
        pending_error="",
        config_error="",
    )
    assert present["OCCUPANCY_STATUS"] == "OCCUPANCY_PRESENT"
    assert present["OCCUPANCY_ABSENT"] == "false"
