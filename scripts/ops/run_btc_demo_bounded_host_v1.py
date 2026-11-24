"""Prepare the Slot-3 host offline, or run an explicitly supplied fresh start.

The default path does not open credentials, network ports, a session or orders.
"""

import argparse
from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time

from src.ops.btc_demo_bounded_host_v1 import (
    BtcDemoHostStartV1,
    run_btc_demo_bounded_host_v1,
    validate_btc_demo_host_config_v1,
)
from src.ops.btc_demo_runtime_v1 import BtcDemoRuntimeV1, fixed_demo_pin_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    resolve_and_assert_live_post_execution_baseline_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    bind_already_held_k1_venue_auth_session_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
    require_btc_testnet_slot_scope_v1,
)
from scripts.ops.check_n1_double_play_runtime_seal_v1 import verify_content

REPO = Path(__file__).resolve().parents[2]


def prepare_btc_demo_host_v1(config, *, require_integrated_source=False):
    validate_btc_demo_host_config_v1(config)
    bound = fixed_demo_pin_v1(config["fixed_pin"])
    path = Path(config["entry_budget_policy_path"])
    if (
        not path.is_absolute()
        or sha256(path.read_bytes()).hexdigest() != config["entry_budget_policy_sha256"]
    ):
        raise ValueError("BTC_DEMO_PREPARED_POLICY_SOURCE_CHANGED")
    policy = replace(
        load_slot_entry_budget_v1(path),
        allowed_slot_ids=("LANE_3",),
        aggregate_reserved_notional_limit=Decimal(25),
    )
    require_btc_testnet_slot_scope_v1(policy, {"LANE_3": bound})
    if policy.require_xperp_liquidation_projection:
        raise ValueError(
            "BTC_DEMO_ADDITIONAL_LIQUIDATION_POLICY_REQUIRES_ITS_ORIGINAL_CUSTODY_BINDING"
        )
    blockers = verify_content(REPO)
    try:
        current = resolve_and_assert_live_post_execution_baseline_v1(
            declared_baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA
        )
        if current != config["repository_sha"]:
            blockers.append("BTC_DEMO_PREPARED_REPOSITORY_REVISION_CHANGED")
    except (ValueError, RuntimeError) as exc:
        blockers.append(type(exc).__name__ + ":" + str(exc))
    if require_integrated_source and blockers:
        raise ValueError("BTC_DEMO_SOURCE_INTEGRATION_REQUIRED:" + ";".join(blockers))
    return dict(
        status="PREPARED_NO_START" if not blockers else "PREPARED_SOURCE_INTEGRATION_PENDING",
        lane_id="LANE_3",
        native_id=bound.venue_native_id,
        session_id=config["session_id"],
        config_digest=digest(config),
        repository_sha=config["repository_sha"],
        duration_seconds=3600,
        close_confirmation_tail_seconds=120,
        initial_budget_usdc="25",
        policy_revision=policy.revision,
        source_blockers=blockers,
        credentials_accessed=False,
        account_read_performed=False,
        session_started=False,
        orders_sent=0,
        entry_waits_for_original_core=True,
    )


@contextmanager
def macos_demo_signer_v1(config):
    """Only the run branch reads the existing exact Demo Keychain fields."""
    values = {}
    for name, field in config["signer_fields"].items():
        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-s",
                config["signer_service"],
                "-a",
                field,
                "-w",
            ],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0 or not result.stdout.strip():
            values.clear()
            raise ValueError("BTC_DEMO_EXISTING_SIGNER_FIELD_UNAVAILABLE:" + field)
        values[name] = result.stdout.decode().strip()
    handle = bind_already_held_k1_venue_auth_session_v1(**values, execution_environment="TESTNET")
    values.clear()
    try:
        yield handle
    finally:
        release_k1_venue_auth_session_v1(handle)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--operator-start", type=Path)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_bytes())
    if not args.run:
        if args.operator_start is not None:
            parser.error("--operator-start requires the explicit --run action")
        print(json.dumps(prepare_btc_demo_host_v1(config), sort_keys=True))
        return 0
    if args.operator_start is None:
        parser.error("--run requires an explicit --operator-start record")
    prepare_btc_demo_host_v1(config, require_integrated_source=True)
    start = BtcDemoHostStartV1(**json.loads(args.operator_start.read_bytes()))
    # Recovery validates this same original start against the registered writer.
    if not (
        Path(config["testnet_root"]) / "testnet-state/budget-owner/owner/reservations.sqlite3"
    ).is_file():
        start.validate_v1(config=config, now_unix=time.time())
    with macos_demo_signer_v1(config) as handle:
        runtime = BtcDemoRuntimeV1(config=config, signing_handle=handle)
        try:
            result = run_btc_demo_bounded_host_v1(runtime=runtime, operator_start=start)
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] in {"CONFIRMED_CLOSED", "CONFIRMED_NO_ENTRY"} else 2
        finally:
            runtime.close()


if __name__ == "__main__":
    sys.exit(main())
