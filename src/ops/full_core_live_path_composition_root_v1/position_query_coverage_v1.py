"""Bind a scoped positions read to a previously observed filled order.

Acquisition evidence only. No invented zero-position row or selection authority.
UTC fields describe the local request interval, not an exchange snapshot clock.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qs, urlsplit

SCHEMA = "position_query_coverage.v1"
POSITIONS_PATH = "/api/v5/account/positions"


def payload_digest_v1(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_position_query_coverage_v1(
    *,
    identity: Any,
    endpoint: str,
    method: str,
    response: Any,
    started_at_utc: str,
    completed_at_utc: str,
    preceding_orders: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Called after a fresh read; preceding_orders were observed before the read."""
    parsed = urlsplit(endpoint)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if (
        method != "GET"
        or parsed.scheme
        or parsed.netloc
        or parsed.fragment
        or parsed.path != POSITIONS_PATH
        or set(query) != {"instId"}
        or query["instId"] != [identity.native_id]
        or not isinstance(response, Mapping)
        or response.get("code") != "0"
        or not isinstance(response.get("data"), list)
        or not started_at_utc
        or not completed_at_utc
    ):
        return None
    # Matching the exact closing order before issuing the positions query gives
    # a causal boundary independent of comparisons between host and venue clocks.
    anchors = [
        row
        for row in preceding_orders
        if row.get("instId") == identity.native_id
        and row.get("clOrdId") == identity.clordid
        and row.get("state") == "filled"
    ]
    if not anchors:
        return None
    return {
        "schema": SCHEMA,
        "identity_digest": identity.identity_digest(),
        "account": identity.account_identity,
        "environment": identity.execution_environment,
        "endpoint": endpoint,
        "method": method,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at_utc,
        "response_digest": payload_digest_v1(response),
        "preceding_filled_order_digests": sorted({payload_digest_v1(row) for row in anchors}),
    }
