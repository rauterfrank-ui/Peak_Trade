"""Confirm an entirely unentered bounded session without inventing a trade."""

from copy import deepcopy
from datetime import datetime, timezone
import json

from src.ops.btc_demo_session_control_v1 import utc_v1
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    immutable_json_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
    FUTURES_FINANCIAL_BASE_GETS,
    futures_financial_pending_gets_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    collect_host_account_observation_v1,
)


def validate_no_entry_v1(owner, registration, receipt, *, check_disk=True):
    if (
        owner._by_key
        or owner._execution_links
        or type(receipt) is not dict
        or set(receipt)
        != {
            "registration_digest",
            "inventory_gets",
            "started_at_utc",
            "completed_at_utc",
            "proof_digest",
        }
    ):
        raise ValueError("BTC_DEMO_NO_ENTRY_ORIGINAL_EMPTY_JOURNAL_REQUIRED")
    body = {k: v for k, v in receipt.items() if k != "proof_digest"}
    if receipt["registration_digest"] != registration.digest_v1() or receipt[
        "proof_digest"
    ] != digest(body):
        raise ValueError("BTC_DEMO_NO_ENTRY_PROOF_DIGEST_MISMATCH")
    reads = receipt["inventory_gets"]
    pending = futures_financial_pending_gets_v1()
    if set(reads) != {*FUTURES_FINANCIAL_BASE_GETS, *pending}:
        raise ValueError("BTC_DEMO_NO_ENTRY_FULL_INVENTORY_REQUIRED")
    started, completed = map(utc_v1, (receipt["started_at_utc"], receipt["completed_at_utc"]))
    if (
        not utc_v1(registration.deadline_utc) <= started <= completed
        or (completed - started).total_seconds() > 5
    ):
        raise ValueError("BTC_DEMO_NO_ENTRY_INVENTORY_CLOCK_INVALID")
    for endpoint, row in reads.items():
        if (
            row["get_performed"] is not True
            or row["endpoint"] != endpoint
            or row["method"] != "GET"
            or row["http_status"] != 200
            or row["auth_header_sent"] is not True
            or row["historical_reuse"] is not False
            or row["venue_live_contact"] is not True
            or row["error_class"]
            or row["payload"]["code"] != "0"
            or not started <= utc_v1(row["acquired_at_utc"]) <= completed
        ):
            raise ValueError("BTC_DEMO_NO_ENTRY_ORIGINAL_GET_UNPROVEN")
        if endpoint in pending or endpoint == "/api/v5/account/positions":
            if row["payload"]["data"] != []:
                raise ValueError("BTC_DEMO_NO_ENTRY_ACCOUNT_NOT_FLAT")
    config = reads["/api/v5/account/config"]["payload"]["data"]
    if len(config) != 1 or (
        config[0].get("uid"),
        config[0].get("posMode"),
        config[0].get("settleCcy"),
    ) != (registration.account_identity, "net_mode", "USDC"):
        raise ValueError("BTC_DEMO_NO_ENTRY_ACCOUNT_CHANGED")
    if check_disk:
        disk = json.loads(
            (owner._store.root.parents[2] / "no-entry-confirmation.json").read_bytes()
        )
        if disk != receipt:
            raise ValueError("BTC_DEMO_NO_ENTRY_ORIGINAL_SOURCE_CHANGED")
    return deepcopy(receipt)


def confirm_no_entry_v1(*, runtime):
    owner = runtime.owner
    with owner._lock:
        control = owner._bounded_demo_session_control
        if control["phase"] == "COMPLETED_NO_ENTRY":
            receipt = validate_no_entry_v1(owner, runtime.registration, control["no_entry_receipt"])
        else:
            if owner._by_key or owner._execution_links or control["phase"] != "RUNNING":
                raise ValueError("BTC_DEMO_NO_ENTRY_ORIGINAL_EMPTY_JOURNAL_REQUIRED")
            observation = collect_host_account_observation_v1(
                private_rest_fetch=runtime.inventory,
                instrument_ids_by_native_id={
                    runtime.bound.venue_native_id: runtime.bound.instrument_id
                },
                session_id=runtime.config["session_id"],
                clock=runtime.clock,
                expected_account=runtime.config["account_identity"],
            )
            original = runtime.inventory.inspect_futures_financial_gets_v1(
                observation, read_count=runtime.inventory.transport.read_count
            )
            receipt = dict(
                registration_digest=runtime.registration.digest_v1(),
                inventory_gets=original.gets,
                started_at_utc=datetime.fromtimestamp(
                    observation.observed.event_time_unix, timezone.utc
                ).isoformat(),
                completed_at_utc=datetime.fromtimestamp(
                    observation.observed.wall_time_unix, timezone.utc
                ).isoformat(),
            )
            receipt["proof_digest"] = digest(receipt)
            validate_no_entry_v1(owner, runtime.registration, receipt, check_disk=False)
            immutable_json_v1(runtime.root / "no-entry-confirmation.json", receipt)
            owner._bounded_demo_session_control = dict(
                deepcopy(control), phase="COMPLETED_NO_ENTRY", no_entry_receipt=receipt
            )
            owner._admitted = False
            owner._recovery_required = True
            owner._persist_locked()
        disk = json.loads((runtime.root / "no-entry-confirmation.json").read_bytes())
        if disk != receipt:
            raise ValueError("BTC_DEMO_NO_ENTRY_ORIGINAL_SOURCE_CHANGED")
        return dict(
            status="CONFIRMED_NO_ENTRY",
            session_id=runtime.registration.session_id,
            original_inventory_proof=receipt["proof_digest"],
            orders_sent=0,
            confirmed_trades=0,
            no_pnl_or_account_return_invented=True,
        )
