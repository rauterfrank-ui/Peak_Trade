"""Explicit observation ingress for legacy launchers; never invent a flat book.

The producer of this document is a trusted account-observation port. This is
validation, not transport authentication or permission to read credentials.
"""

import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path
import time

from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)


def require_startup_portfolio_v1(observed_portfolio):
    if not isinstance(observed_portfolio, PortfolioTruthSnapshotV1):
        raise ValueError("OBSERVED_PORTFOLIO_REQUIRED")
    return observed_portfolio


def add_startup_portfolio_arguments_v1(parser, *, replay_clock=False):
    parser.add_argument(
        "--startup-portfolio",
        type=Path,
        required=True,
        help="Complete account-observer document; no implicit flat account",
    )
    parser.add_argument("--expected-account-identity", required=True)
    if replay_clock:
        parser.add_argument(
            "--startup-observation-unix",
            type=float,
            required=True,
            help="Explicit frozen observation clock for offline replay only",
        )


def startup_observation_now_v1(args):
    replay_time = getattr(args, "startup_observation_unix", None)
    return time.time() if replay_time is None else replay_time


def load_startup_portfolio_args_v1(args):
    return read_startup_portfolio_document_v1(
        args.startup_portfolio,
        expected_account_identity=args.expected_account_identity,
        now_unix=startup_observation_now_v1(args),
    )


def read_startup_portfolio_document_v1(path, *, expected_account_identity, now_unix=None):
    """Validate a fresh full-SWAP snapshot exported by the account observer."""
    if (
        not isinstance(expected_account_identity, str)
        or not expected_account_identity
        or expected_account_identity != expected_account_identity.strip()
    ):
        raise ValueError("STARTUP_EXPECTED_ACCOUNT_REQUIRED")

    def unique_fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("STARTUP_OBSERVATION_DUPLICATE_FIELD")
            result[key] = value
        return result

    payload = json.loads(Path(path).read_text(), object_pairs_hook=unique_fields)
    if (
        not isinstance(payload, dict)
        or payload.get("schema") != "peaktrade.startup_portfolio_observation.v1"
    ):
        raise ValueError("STARTUP_OBSERVATION_SCHEMA_INVALID")
    fields = {
        "schema",
        "account_identity",
        "instrument_type",
        "complete_account_scope",
        "pending_orders",
        "source_id",
        "event_time_unix",
        "wall_time_unix",
        "positions",
    }
    if set(payload) != fields:
        raise ValueError("STARTUP_OBSERVATION_FIELDS_INVALID")
    if payload.get("account_identity") != expected_account_identity:
        raise ValueError("STARTUP_OBSERVATION_ACCOUNT_MISMATCH")
    if (
        payload.get("instrument_type") != "SWAP"
        or payload.get("complete_account_scope") is not True
    ):
        raise ValueError("STARTUP_OBSERVATION_COMPLETE_SCOPE_REQUIRED")
    if payload.get("pending_orders") is not False:
        raise ValueError("STARTUP_PENDING_ORDERS_UNRESOLVED")
    source = payload.get("source_id")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("STARTUP_OBSERVATION_SOURCE_REQUIRED")
    event, captured = payload.get("event_time_unix"), payload.get("wall_time_unix")
    now = time.time() if now_unix is None else now_unix
    if any(
        isinstance(t, bool) or not isinstance(t, (float, int)) or not math.isfinite(t)
        for t in (event, captured, now)
    ):
        raise ValueError("STARTUP_OBSERVATION_TIME_INVALID")
    if not 0 <= now - event <= 5 or not event <= captured <= now:
        raise ValueError("STARTUP_OBSERVATION_STALE_OR_FUTURE")
    rows = payload.get("positions")
    if not isinstance(rows, list):
        raise ValueError("STARTUP_OBSERVATION_POSITIONS_REQUIRED")
    positions, seen = [], set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"instrument_id", "signed_quantity", "side"}:
            raise ValueError("STARTUP_OBSERVATION_POSITION_INVALID")
        instrument = row.get("instrument_id")
        if (
            not isinstance(instrument, str)
            or not instrument
            or instrument != instrument.strip()
            or instrument in seen
        ):
            raise ValueError("STARTUP_OBSERVATION_POSITION_ID_INVALID")
        seen.add(instrument)
        try:
            if not isinstance(row.get("signed_quantity"), str):
                raise InvalidOperation
            quantity = Decimal(row["signed_quantity"])
            if not quantity.is_finite():
                raise InvalidOperation
        except (KeyError, InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("STARTUP_OBSERVATION_QUANTITY_INVALID") from exc
        position = PositionTruthV1.from_signed(
            instrument_id=instrument,
            signed_quantity=quantity,
            source_id=source,
            event_time_unix=event,
            wall_time_unix=captured,
        )
        if row.get("side") != position.side:
            raise ValueError("STARTUP_OBSERVATION_POSITION_SIDE_MISMATCH")
        positions.append(position)
    return PortfolioTruthSnapshotV1(
        positions=tuple(positions),
        source_id=source,
        event_time_unix=event,
        wall_time_unix=captured,
    )
