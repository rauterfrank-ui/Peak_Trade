"""Bounded Demo session clock, separate from Core/L10 and trading authority."""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re

_DIGEST = re.compile(r"[0-9a-f]{64}")


def utc_v1(value):
    if type(value) is not str:
        raise ValueError("BTC_DEMO_SESSION_UTC_REQUIRED")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("BTC_DEMO_SESSION_UTC_REQUIRED")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class BoundedDemoSessionRegistrationV1:
    session_id: str
    account_identity: str
    instrument_id: str
    started_at_utc: str
    operator_start_digest: str
    duration_seconds: int = 3600
    lane_id: str = "LANE_3"
    native_id: str = "BTC-USD_UM_XPERP-310328"
    execution_environment: str = "TESTNET"

    def validate_v1(self):
        if (
            not all(
                type(s) is str and s and s == s.strip()
                for s in (self.session_id, self.account_identity, self.instrument_id)
            )
            or type(self.operator_start_digest) is not str
            or not _DIGEST.fullmatch(self.operator_start_digest)
            or type(self.duration_seconds) is not int
            or self.duration_seconds != 3600
            or (self.lane_id, self.native_id, self.execution_environment)
            != ("LANE_3", "BTC-USD_UM_XPERP-310328", "TESTNET")
        ):
            raise ValueError("BTC_DEMO_SESSION_REGISTRATION_SCOPE_INVALID")
        utc_v1(self.started_at_utc)

    @property
    def deadline_utc(self):
        self.validate_v1()
        return (utc_v1(self.started_at_utc) + timedelta(seconds=self.duration_seconds)).isoformat()

    def digest_v1(self):
        self.validate_v1()
        return sha256(
            json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def validate_session_control_v1(owner, record):
    if record is None:
        return None
    if type(record) is not dict or record.get("phase") not in {
        "RUNNING",
        "CLOSING",
        "CLOSED",
        "COMPLETED_NO_ENTRY",
    }:
        raise ValueError("BTC_DEMO_SESSION_CONTROL_INVALID")
    keys = {"registration", "registration_digest", "phase"}
    if record["phase"] in {"CLOSING", "CLOSED"}:
        keys.add("close_plan")
    if record["phase"] == "COMPLETED_NO_ENTRY":
        keys.add("no_entry_receipt")
    if record["phase"] == "CLOSED":
        keys.add("close_receipt")
    if set(record) != keys:
        raise ValueError("BTC_DEMO_SESSION_CONTROL_INVALID")
    registration = BoundedDemoSessionRegistrationV1(**record["registration"])
    registration.validate_v1()
    bound = owner._lane_bindings.get("LANE_3", {}).get("bound", {})
    if (
        owner.execution_environment_v1() != "TESTNET"
        or registration.account_identity != owner._account_identity
        or registration.instrument_id != bound.get("instrument_id")
        or registration.native_id != bound.get("venue_native_id")
        or registration.digest_v1() != record["registration_digest"]
    ):
        raise ValueError("BTC_DEMO_SESSION_CONTROL_SCOPE_MISMATCH")
    if record["phase"] in {"CLOSING", "CLOSED"}:
        from src.ops.btc_demo_session_close_v1 import validate_close_plan_v1

        validate_close_plan_v1(owner, registration, record["close_plan"])
    if record["phase"] == "CLOSED":
        from src.ops.btc_demo_session_close_reconciliation_v1 import validate_close_receipt_v1

        validate_close_receipt_v1(owner, record)
    if record["phase"] == "COMPLETED_NO_ENTRY":
        from src.ops.btc_demo_runtime_no_entry_v1 import validate_no_entry_v1

        validate_no_entry_v1(owner, registration, record["no_entry_receipt"])
    return registration


def require_risk_window_v1(owner, *, now_utc):
    registration = validate_session_control_v1(owner, owner._bounded_demo_session_control)
    if registration is None:
        # Existing explicitly called standalone dispatch is not a bounded host.
        # The future bounded-host entrypoint must require a registration.
        return None
    now = utc_v1(now_utc)
    if owner._bounded_demo_session_control["phase"] != "RUNNING" or not utc_v1(
        registration.started_at_utc
    ) <= now < utc_v1(registration.deadline_utc):
        raise ValueError("BTC_DEMO_SESSION_NEW_RISK_WINDOW_CLOSED")
    return registration


def register_session_locked_v1(owner, registration, *, expected_head, now_utc):
    if type(registration) is not BoundedDemoSessionRegistrationV1:
        raise ValueError("BTC_DEMO_ORIGINAL_SESSION_REGISTRATION_REQUIRED")
    registration.validate_v1()
    if (
        owner._store is None
        or owner._storage_failed
        or owner._closed_owner
        or owner._store.head != expected_head
        or owner._bounded_demo_session_control is not None
        or owner._by_key
        or not 0 <= (utc_v1(now_utc) - utc_v1(registration.started_at_utc)).total_seconds() <= 5
    ):
        raise ValueError("BTC_DEMO_FRESH_SESSION_START_REQUIRED")
    record = dict(
        registration=asdict(registration),
        registration_digest=registration.digest_v1(),
        phase="RUNNING",
    )
    validate_session_control_v1(owner, record)
    owner._bounded_demo_session_control = record
    owner._persist_locked()
    return dict(record)
