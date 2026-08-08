#!/usr/bin/env python3
"""Real §11.12.8 productive Testnet EXECUTE operator entrypoint.

Consumes EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW through the unlocked real path.
Pre-merge acceptance: wire send forbidden.
Post-merge Owner EXECUTE: wire send permitted when --allow-wire-send and vault file
are provided (SecretRef + hidden confirm remain runtime preconditions).
Does NOT start §11.13. Does NOT enable Live.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (  # noqa: E402
    SCOPED_OWNER_GO_AUTHORIZATION,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.acceptance_gate_v1 import (  # noqa: E402
    run_pre_merge_unlock_acceptance_gate_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (  # noqa: E402
    AUTHORIZATION_REQUIRED_AFTER_MERGE,
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    CAPABILITY_ID,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.unlock_orchestrator_v1 import (  # noqa: E402
    execute_unlocked_productive_path_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.vault_resolver_v1 import (  # noqa: E402
    FileSecretRefVaultBackendV1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unlocked real productive Testnet execute-path operator entrypoint"
    )
    parser.add_argument(
        "--pre-merge-acceptance",
        action="store_true",
        help="Run pre-merge acceptance gate (wire send forbidden).",
    )
    parser.add_argument(
        "--confirm-token-digest",
        default="",
        help="SHA-256 hex digest of hidden confirm token (digest-only; never plaintext).",
    )
    parser.add_argument(
        "--allow-wire-send",
        action="store_true",
        help=(
            "Permit real Testnet HTTP wire send under EXECUTE_PRODUCTIVE_TESTNET_CAMPAIGN_NOW "
            "(post-merge Owner runtime GO; Live remains hard-blocked)."
        ),
    )
    parser.add_argument(
        "--vault-file",
        default="",
        help="JSON SecretRef vault file for real ephemeral credential resolve (not argv secrets).",
    )
    parser.add_argument(
        "--work-dir",
        default="",
        help="Optional work directory for durable state/evidence.",
    )
    args = parser.parse_args(argv)

    if args.pre_merge_acceptance:
        if args.allow_wire_send:
            print(
                json.dumps(
                    {
                        "STATUS": "FAIL",
                        "REASON": "PRE_MERGE_WIRE_SEND_FORBIDDEN",
                        "CAPABILITY_ID": CAPABILITY_ID,
                    },
                    sort_keys=True,
                )
            )
            return 2
        with tempfile.TemporaryDirectory(prefix="pt_11_12_8_unlock_ep_") as tmp:
            gate = run_pre_merge_unlock_acceptance_gate_v1(
                work_dir=Path(tmp) / f"g-{uuid4().hex[:8]}"
            )
        print(
            json.dumps(
                {
                    "STATUS": "PASS" if gate.get("ok") else "FAIL",
                    "CAPABILITY_ID": CAPABILITY_ID,
                    "ENTRYPOINT": "REAL_OPERATOR_EXECUTE",
                    "MODE": "PRE_MERGE_ACCEPTANCE",
                    "NETWORK_SEND_BOUNDARY_REACHED": gate.get("NETWORK_SEND_BOUNDARY_REACHED"),
                    "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
                    "NETWORK_EFFECT": gate.get("NETWORK_EFFECT"),
                    "ORDER_EFFECT": gate.get("ORDER_EFFECT"),
                    "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
                    "CANONICAL_NEXT_STEP_AFTER_MERGE": CANONICAL_NEXT_STEP_AFTER_MERGE,
                    "AUTHORIZATION_REQUIRED": AUTHORIZATION_REQUIRED_AFTER_MERGE,
                    "SCOPED_OWNER_GO_SCOPE": SCOPED_OWNER_GO_SCOPE,
                    "SCOPED_OWNER_GO_AUTHORIZATION": SCOPED_OWNER_GO_AUTHORIZATION,
                    "SCOPED_OWNER_GO_TOKEN": SCOPED_OWNER_GO_TOKEN,
                },
                sort_keys=True,
            )
        )
        return 0 if gate.get("ok") else 2

    digest = str(args.confirm_token_digest or "").strip().lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        print(
            json.dumps(
                {
                    "STATUS": "FAIL",
                    "REASON": "CONFIRM_TOKEN_DIGEST_REQUIRED",
                    "CAPABILITY_ID": CAPABILITY_ID,
                },
                sort_keys=True,
            )
        )
        return 2

    vault_backend = None
    if args.allow_wire_send:
        vault_path = Path(str(args.vault_file or "").strip())
        if not vault_path.is_file():
            print(
                json.dumps(
                    {
                        "STATUS": "FAIL",
                        "REASON": "VAULT_FILE_REQUIRED_FOR_WIRE_SEND",
                        "CAPABILITY_ID": CAPABILITY_ID,
                        "HINT": "SecretRef vault file is a runtime precondition, not a future GO.",
                    },
                    sort_keys=True,
                )
            )
            return 2
        vault_backend = FileSecretRefVaultBackendV1(vault_file=vault_path)

    work = (
        Path(args.work_dir) if args.work_dir else Path(tempfile.mkdtemp(prefix="pt_unlock_exec_"))
    )
    result = execute_unlocked_productive_path_v1(
        work_dir=work,
        confirm_token_digest=digest,
        expected_confirm_token_digest=digest,
        allow_wire_send=bool(args.allow_wire_send),
        vault_backend=vault_backend,
        argv=list(argv or []),
    )
    print(
        json.dumps(
            {
                "STATUS": "PASS" if result.ok else "FAIL",
                "CAPABILITY_ID": CAPABILITY_ID,
                "ENTRYPOINT": "REAL_OPERATOR_EXECUTE",
                "MODE": "PRODUCTIVE_REAL_NETWORK",
                "ALLOW_WIRE_SEND": bool(args.allow_wire_send),
                "NETWORK_SEND_BOUNDARY_REACHED": result.network_send_boundary_reached,
                "CLIENT_BOUND": result.client_bound,
                "EVIDENCE_PATH": result.run.evidence_path,
                "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
                "NETWORK_EFFECT": result.run.network_effect,
                "ORDER_EFFECT": result.run.order_effect,
                "SECTION_11_13_STARTED": False,
                "CANONICAL_NEXT_STEP_AFTER_MERGE": CANONICAL_NEXT_STEP_AFTER_MERGE,
                "AUTHORIZATION_REQUIRED": AUTHORIZATION_REQUIRED_AFTER_MERGE,
            },
            sort_keys=True,
        )
    )
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
