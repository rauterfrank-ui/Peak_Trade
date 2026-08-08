"""B01–B24 closure matrix for ACTUAL start package."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    BLOCKER_IDS,
    CAPABILITY_ID,
)

_MATRIX: dict[str, dict[str, str]] = {
    "B01": {
        "location": "owner_go_consumer_v1.consume_actual_start_owner_go_v1",
        "test": "test_owner_go_accept_and_rejects",
        "status": "CLOSED",
    },
    "B02": {
        "location": "owner_go_consumer_v1 (productive_campaign_authorized=true)",
        "test": "test_owner_go_accept_and_rejects",
        "status": "CLOSED",
    },
    "B03": {
        "location": "productive_consumer_v1.execute_productive_section_11_12_8_campaign_run_v1",
        "test": "test_pre_merge_acceptance_gate",
        "status": "CLOSED",
    },
    "B04": {
        "location": "testnet_authorization_v1.authorize_testnet_runtime_v1",
        "test": "test_testnet_authorization_runtime",
        "status": "CLOSED",
    },
    "B05": {
        "location": "productive_consumer_v1 (new consumer; legacy refuse preserved)",
        "test": "test_legacy_hard_refuse_preserved",
        "status": "CLOSED",
    },
    "B06": {
        "location": "productive_consumer_v1 (terminal refuse preserved)",
        "test": "test_legacy_hard_refuse_preserved",
        "status": "CLOSED",
    },
    "B07": {
        "location": "secretref_credential_v1.resolve_and_load_secretref_ephemeral_v1",
        "test": "test_secretref_and_plaintext_leak_negatives",
        "status": "CLOSED",
    },
    "B08": {
        "location": "secretref_credential_v1",
        "test": "test_secretref_and_plaintext_leak_negatives",
        "status": "CLOSED",
    },
    "B09": {
        "location": "network_session_v1.reach_network_session_entry_boundary_v1",
        "test": "test_network_session_go_ephemeral_only",
        "status": "CLOSED",
    },
    "B10": {
        "location": "network_session_v1 + Phase92 bind_ephemeral_network_session_go_v1",
        "test": "test_network_session_go_ephemeral_only",
        "status": "CLOSED",
    },
    "B11": {
        "location": "productive_execution_port_v1.ProductiveTestnetExecutionPortV1",
        "test": "test_productive_port_and_transport",
        "status": "CLOSED",
    },
    "B12": {
        "location": "testnet_transport_v1 (stubbed+real surfaces; Cap11.4 anti-corruption)",
        "test": "test_productive_port_and_transport",
        "status": "CLOSED",
    },
    "B13": {
        "location": "durable_state_v1.validate_actual_start_durable_state_v1",
        "test": "test_activation_state_machine_and_restart",
        "status": "CLOSED",
    },
    "B14": {
        "location": "campaign_executor_v1 + durable COMPLETED/ABORTED",
        "test": "test_campaign_lifecycle_complete_and_abort",
        "status": "CLOSED",
    },
    "B15": {
        "location": "evidence_v1.write_productive_execution_evidence_v1",
        "test": "test_execution_evidence_and_seal",
        "status": "CLOSED",
    },
    "B16": {
        "location": "hidden_confirm_v1.latch_and_consume_confirm_digest_v1",
        "test": "test_hidden_confirm_one_time_replay",
        "status": "CLOSED",
    },
    "B17": {
        "location": "constants (wrappers not extended); test asserts residual flags",
        "test": "test_deprecated_wrappers_not_extended",
        "status": "CLOSED",
    },
    "B18": {
        "location": "closeout_v1 (PROVEN only via real evidence; stub does not flip)",
        "test": "test_closeout_does_not_flip_proven_on_stub",
        "status": "CLOSED",
    },
    "B19": {
        "location": "closeout_v1 + evidence binding",
        "test": "test_closeout_does_not_flip_proven_on_stub",
        "status": "CLOSED",
    },
    "B20": {
        "location": "account_endpoint_binding_v1.bind_and_verify_testnet_account_v1",
        "test": "test_account_and_endpoint_binding",
        "status": "CLOSED",
    },
    "B21": {
        "location": "campaign_executor_v1.run_campaign_lifecycle_v1",
        "test": "test_campaign_lifecycle_complete_and_abort",
        "status": "CLOSED",
    },
    "B22": {
        "location": "scripts/...operator_entrypoint_v1.py",
        "test": "test_operator_entrypoint_stubbed",
        "status": "CLOSED",
    },
    "B23": {
        "location": "account_endpoint_binding_v1 + constants TESTNET allowlist",
        "test": "test_account_and_endpoint_binding",
        "status": "CLOSED",
    },
    "B24": {
        "location": "constants NEXT_CONSUMER + this CAPABILITY_ID as real package",
        "test": "test_capability_identity",
        "status": "CLOSED",
    },
}


def build_b01_b24_closure_matrix_v1() -> dict[str, Any]:
    assert set(_MATRIX) == set(BLOCKER_IDS)
    open_ids = [bid for bid, row in _MATRIX.items() if row["status"] != "CLOSED"]
    return {
        "ok": len(open_ids) == 0,
        "CAPABILITY_ID": CAPABILITY_ID,
        "ALL_B01_B24_CLOSED": len(open_ids) == 0,
        "RESIDUAL_BLOCKER_COUNT": len(open_ids),
        "matrix": _MATRIX,
        "open_ids": open_ids,
    }
