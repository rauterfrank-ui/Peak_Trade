#!/usr/bin/env python3
"""Bounded K1 read-only account-scope check. Default validates config only.

No raw account rows, credentials, amounts or UID are emitted. No service,
portfolio adoption, capital mint, order or transfer. No automatic retry.
"""

import argparse
import json
import os
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_SERVICE_ID,
    KEYCHAIN_ACCOUNT_ID,
    SOURCE_REF_URI,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    K1_ACCOUNT_READ_PROFILE,
    load_k1_account_source_config_v1,
    open_k1_account_observation_source_v1,
)

_SAFE_ERRORS = {
    "OBSERVATION_ACCOUNT_MISMATCH",
    "OBSERVATION_GET_EVIDENCE_INVALID",
    "OBSERVATION_RESPONSE_INVALID",
    "OBSERVATION_RESPONSE_SCOPE_UNPROVEN",
    "K1_CREDENTIAL_ACQUISITION_FAIL_CLOSED",
    "GET_REDIRECT_FORBIDDEN",
    "MAX_REQUEST_COUNT_EXCEEDED",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-account-identity")
    parser.add_argument(
        "--config", type=Path, help="Explicit identifier-only K1 source configuration"
    )
    parser.add_argument(
        "--observe-once",
        action="store_true",
        help="Explicit real K1 lookup and seven scope or three Treasury GETs; no retry",
    )
    parser.add_argument(
        "--treasury-inputs",
        action="store_true",
        help="Choose three account/trading/funding reads instead of seven scope reads",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--accounting-bills",
        action="store_true",
        help="Inspect unfiltered account bills (one config plus at most six archive GETs)",
    )
    args = parser.parse_args(argv)
    if args.accounting_bills and args.treasury_inputs:
        parser.error("choose one observation profile")
    if args.config is not None:
        configured = load_k1_account_source_config_v1(args.config)
        if (
            args.expected_account_identity is not None
            and args.expected_account_identity != configured["expected_account_identity"]
        ):
            parser.error("expected account conflicts with explicit configuration")
        args.expected_account_identity = configured["expected_account_identity"]
    if (
        not args.expected_account_identity
        or args.expected_account_identity != args.expected_account_identity.strip()
    ):
        parser.error("expected account identity must be explicit and nonempty")
    if args.output is not None and (
        not args.output.is_absolute()
        or not args.output.parent.is_dir()
        or args.output.exists()
        or args.output.is_symlink()
    ):
        parser.error("output must be a new absolute file in an existing private directory")
    report = {
        "profile": K1_ACCOUNT_READ_PROFILE,
        "keychain_service": KEYCHAIN_SERVICE_ID,
        "keychain_account": KEYCHAIN_ACCOUNT_ID,
        "source_ref": SOURCE_REF_URI,
        "expected_account_configured": True,
        "mode": "CONFIG_ONLY",
        "keychain_access_attempted": False,
        "private_get_attempt_count": 0,
        "order_or_transfer_count": 0,
        "service_activated": False,
        "capital_admitted": False,
    }
    rc = 0
    if args.observe_once:
        report.update(mode="REAL_READ_ONLY_ONCE", keychain_access_attempted=True)
        try:
            with open_k1_account_observation_source_v1(
                expected_account_identity=args.expected_account_identity,
                session_id="k1-account-readiness-once",
                max_request_count=10,
            ) as source:
                try:
                    report["observation"] = (
                        source.inspect_accounting_bills_v1()
                        if args.accounting_bills
                        else (
                            source.inspect_treasury_inputs_v1()
                            if args.treasury_inputs
                            else source.inspect_account_scope_v1()
                        )
                    )
                    if args.accounting_bills:
                        # Successful observation is not a full accounting readiness PASS.
                        rc = 2 if report["observation"]["blockers"] else 0
                    else:
                        ready = "inputs_ready" if args.treasury_inputs else "supported_scope_clear"
                        rc = 0 if report["observation"][ready] else 2
                finally:
                    report["private_get_attempt_count"] = source.transport.read_count
                    report["last_read"] = source.transport.last_read
        except Exception as exc:
            detail = str(exc)
            report["error_code"] = detail if detail in _SAFE_ERRORS else "K1_SOURCE_READ_FAILED"
            report["error_type"] = type(exc).__name__
            rc = 2
    report["result"] = "PASS" if rc == 0 else "BLOCKED"
    encoded = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(encoded)
    print(encoded, end="")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
