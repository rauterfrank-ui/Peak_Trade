"""Bounded Slot-3 process sequencing; economic and execution owners stay original."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time
from uuid import uuid4

from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    exclusive_v1,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)


@dataclass(frozen=True)
class BtcDemoHostStartV1:
    session_id: str
    prepared_config_digest: str
    authorized_at_utc: str
    expires_at_utc: str
    action: str = "START_BOUNDED_SLOT3_TESTNET"
    lane_id: str = "LANE_3"
    native_id: str = "BTC-USD_UM_XPERP-310328"
    duration_seconds: int = 3600
    close_open_position_at_end: bool = True
    execution_environment: str = "TESTNET"

    def digest_v1(self):
        return digest(asdict(self))

    def validate_v1(self, *, config, now_unix, existing_registration=None):
        from src.ops.btc_demo_session_control_v1 import utc_v1

        if (
            self.action != "START_BOUNDED_SLOT3_TESTNET"
            or self.session_id != config["session_id"]
            or self.prepared_config_digest != digest(config)
            or (self.lane_id, self.native_id, self.execution_environment)
            != ("LANE_3", "BTC-USD_UM_XPERP-310328", "TESTNET")
            or type(self.duration_seconds) is not int
            or self.duration_seconds != 3600
            or self.close_open_position_at_end is not True
            or not math.isfinite(now_unix)
        ):
            raise ValueError("BTC_DEMO_BOUNDED_START_SCOPE_MISMATCH")
        issued, expires = (
            utc_v1(self.authorized_at_utc).timestamp(),
            utc_v1(self.expires_at_utc).timestamp(),
        )
        if not 0 < expires - issued <= 300:
            raise ValueError("BTC_DEMO_BOUNDED_START_VALIDITY_INVALID")
        if existing_registration is None:
            if not issued <= now_unix < expires:
                raise ValueError("BTC_DEMO_BOUNDED_START_NOT_CURRENT")
        elif (
            existing_registration.operator_start_digest != self.digest_v1()
            or existing_registration.session_id != self.session_id
        ):
            raise ValueError("BTC_DEMO_BOUNDED_ORIGINAL_START_REQUIRED")


def validate_btc_demo_host_config_v1(config):
    if type(config) is not dict or set(config) != {
        "schema",
        "session_id",
        "testnet_root",
        "repository_sha",
        "account_identity",
        "fixed_pin",
        "entry_budget_policy_path",
        "entry_budget_policy_sha256",
        "signer_service",
        "signer_fields",
        "processing_poll_seconds",
        "close_confirmation_timeout_seconds",
    }:
        raise ValueError("BTC_DEMO_BOUNDED_CONFIG_SHAPE_INVALID")
    if (
        config["schema"] != "btc_demo_bounded_host_preparation.v1"
        or config["signer_service"] != "PeakTrade-Slot3-Demo-BTC"
        or config["signer_fields"]
        != {"api_key": "api-key", "api_secret": "secret", "passphrase": "passphrase"}
    ):
        raise ValueError("BTC_DEMO_BOUNDED_CONFIG_IDENTITY_INVALID")
    for field in ("session_id", "repository_sha", "account_identity"):
        if (
            type(config[field]) is not str
            or not config[field]
            or config[field] != config[field].strip()
        ):
            raise ValueError("BTC_DEMO_BOUNDED_CONFIG_IDENTITY_INVALID")
    root = Path(config["testnet_root"])
    if (
        not root.is_absolute()
        or root.resolve() != root
        or re.fullmatch(r"[0-9a-f]{40}", config["repository_sha"]) is None
        or type(config["processing_poll_seconds"]) not in (float, int)
        or not math.isfinite(config["processing_poll_seconds"])
        or not 0.2 <= config["processing_poll_seconds"] <= 2
        or config["close_confirmation_timeout_seconds"] != 120
    ):
        raise ValueError("BTC_DEMO_BOUNDED_CONFIG_BOUNDS_INVALID")
    return config


def run_btc_demo_bounded_host_v1(*, runtime, operator_start, clock=time.time, sleep=time.sleep):
    """Run only an explicit start; timeout or unknown evidence retains custody.

    The trading window is fixed at 3600 seconds. A separate bounded tail only
    closes/reconciles; it never extends the window for entries or reversals.
    """
    from src.ops.btc_demo_runtime_v1 import BtcDemoRuntimeV1

    if type(runtime) is not BtcDemoRuntimeV1 or type(operator_start) is not BtcDemoHostStartV1:
        raise ValueError("BTC_DEMO_ORIGINAL_BOUNDED_RUNTIME_REQUIRED")
    config = validate_btc_demo_host_config_v1(runtime.config)
    root = Path(config["testnet_root"])
    if not root.exists():
        operator_start.validate_v1(config=config, now_unix=clock())
        root.mkdir(mode=0o700, parents=True)
    with exclusive_v1(root / "bounded-host.lock"):
        registration = runtime.start_or_recover_v1(operator_start=operator_start)
        operator_start.validate_v1(
            config=config, now_unix=clock(), existing_registration=registration
        )
        deadline = datetime.fromisoformat(registration.deadline_utc).timestamp()
        receipt = root / "bounded-host-progress.json"
        previous = None

        def save(status, *, detail=None, result=None):
            nonlocal previous
            row = dict(
                schema="btc_demo_bounded_host_progress.v1",
                session_id=config["session_id"],
                registration_digest=registration.digest_v1(),
                operator_start_digest=operator_start.digest_v1(),
                status=status,
                observed_at_utc=datetime.fromtimestamp(clock(), timezone.utc).isoformat(),
                detail=detail,
                result=result,
            )
            atomic_write_json(path=receipt, payload=row)
            atomic_write_json(path=root / "host-events" / (uuid4().hex + ".json"), payload=row)
            previous = row
            return row

        if receipt.exists():
            retained = json.loads(receipt.read_bytes())
            if (retained.get("registration_digest"), retained.get("operator_start_digest")) != (
                registration.digest_v1(),
                operator_start.digest_v1(),
            ):
                raise ValueError("BTC_DEMO_BOUNDED_HOST_START_CHANGED")
        while clock() < deadline:
            started = clock()
            try:
                result = runtime.step_v1()
                save(result["status"], result=result)
            except (ValueError, RuntimeError, OSError, TimeoutError) as exc:
                # The original state decides what can be retried. No grant,
                # hold, cursor, quantity or budget is reset on this path.
                save(
                    "WAITING_FOR_ORIGINAL_INPUT_OR_RECONCILIATION",
                    detail=type(exc).__name__ + ":" + str(exc),
                )
            now = clock()
            if not math.isfinite(now) or now < started:
                raise ValueError("BTC_DEMO_BOUNDED_HOST_CLOCK_REVERSED")
            if now < deadline:
                sleep(min(config["processing_poll_seconds"], deadline - now))
        save("CLOSING_SESSION")
        while clock() < deadline + config["close_confirmation_timeout_seconds"]:
            started = clock()
            try:
                result = runtime.finish_v1()
                if result["status"] in {"CONFIRMED_CLOSED", "CONFIRMED_NO_ENTRY"}:
                    return save(result["status"], result=result)
                save("AWAITING_CONFIRMED_CLOSE", result=result)
            except (ValueError, RuntimeError, OSError, TimeoutError) as exc:
                save("AWAITING_CONFIRMED_CLOSE", detail=type(exc).__name__ + ":" + str(exc))
            now = clock()
            if not math.isfinite(now) or now < started:
                raise ValueError("BTC_DEMO_BOUNDED_HOST_CLOCK_REVERSED")
            remaining = deadline + config["close_confirmation_timeout_seconds"] - now
            if remaining > 0:
                sleep(min(config["processing_poll_seconds"], remaining))
        return save(
            "CLOSE_UNCONFIRMED_HOLD_RETAINED",
            detail=None if previous is None else previous.get("detail"),
        )
