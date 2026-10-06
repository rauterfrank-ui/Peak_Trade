#!/usr/bin/env python3
"""Minimum authenticated OKX EEA Demo private GET preflight (GHV credential bind).

Proves Demo SecretRef vault + auth + x-simulated-trading header only.
Does not run GHV observation, Cap23/Cap24 selection, or PRE_EXTERNAL convergence.

RUNTIME_AUTHORIZATION_EFFECT=NONE
POST_ALLOWED=false
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PRIVATE_PREFLIGHT_ENDPOINT = "/api/v5/account/config"


def _main() -> int:
    parser = argparse.ArgumentParser(description="GHV Demo private GET preflight v1 (GET-only)")
    parser.add_argument(
        "--vault-file",
        type=Path,
        default=None,
        help="Operator-local SecretRef vault JSON (default: env or canonical .ops_local path)",
    )
    args = parser.parse_args()

    from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_read_only_get_transport_v1 import (
        GhvDemoReadOnlyGetTransportV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_vault_credential_loader_v1 import (
        load_ghv_testnet_demo_credential_handle_v1,
        prove_demo_credential_presence_gate_v1,
        release_ghv_testnet_demo_opaque_handle_v1,
    )

    gate = prove_demo_credential_presence_gate_v1(vault_file=args.vault_file)
    if gate.get("DEMO_CREDENTIAL_SET_COMPLETE") is not True:
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "blocker": "DEMO_CREDENTIAL_SET_INCOMPLETE",
                    "gate": gate,
                    "PRIVATE_NETWORK_EXECUTED": False,
                },
                sort_keys=True,
            )
        )
        return 2

    handle = load_ghv_testnet_demo_credential_handle_v1(vault_file=args.vault_file)
    try:
        transport = GhvDemoReadOnlyGetTransportV1(handle=handle, max_request_count=1)
        result = transport.get(
            endpoint=PRIVATE_PREFLIGHT_ENDPOINT,
            auth_required=True,
            pretrade_decision_id="ghv-demo-private-get-preflight-v1",
        )
        payload = result.payload if isinstance(result.payload, dict) else {}
        okx_code = str(payload.get("code") or "")
        auth_accepted = result.http_status == 200 and okx_code == "0"
        demo_header_accepted = auth_accepted
        out = {
            "status": "PASS" if auth_accepted else "FAIL_CLOSED",
            "HTTP_STATUS_CATEGORY": "200" if result.http_status == 200 else str(result.http_status),
            "OKX_CODE": okx_code or "UNKNOWN",
            "AUTH_ACCEPTED": auth_accepted,
            "DEMO_HEADER_ACCEPTED": demo_header_accepted,
            "PRIVATE_GET_CONTRACT_VALID": result.get_performed and result.method == "GET",
            "endpoint": PRIVATE_PREFLIGHT_ENDPOINT,
            "transport_class": result.transport_class,
            "error_class": result.error_class or "",
            "PRIVATE_NETWORK_EXECUTED": True,
            "GHV_TESTNET_OBSERVATION_EXECUTED": False,
            "PRE_EXTERNAL_CROSSED": False,
        }
        print(json.dumps(out, sort_keys=True))
        return 0 if auth_accepted else 2
    finally:
        release_ghv_testnet_demo_opaque_handle_v1(handle)


if __name__ == "__main__":
    raise SystemExit(_main())
