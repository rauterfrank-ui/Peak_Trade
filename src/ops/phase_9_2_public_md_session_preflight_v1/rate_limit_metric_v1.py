"""Structured Phase 9.2 rate-limit event counting (no substring false positives).

``rate_limit_event_count`` counts only semantically classified rate-limit
events from:

- exact HTTP status ``429`` on typed status fields;
- canonical transport ``error_code`` / reason tokens
  (``RATE_LIMIT_HTTP_429`` and siblings);
- authoritative transport telemetry field ``http_429_count``.

It must never count bare ``"429"`` substrings inside hashes, digests, IDs,
timestamps or free-text blobs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

# Canonical EEA public-MD transport rate-limit classification codes.
# Source: ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1
CANONICAL_RATE_LIMIT_ERROR_CODES: frozenset[str] = frozenset(
    {
        "RATE_LIMIT_HTTP_429",
        "RATE_LIMIT_SESSION_BUDGET_EXCEEDED",
        "RATE_LIMIT_RETRY_EXHAUSTED",
        "RATE_LIMIT_RETRY_SCHEDULED",
        "RATE_LIMIT_RETRY_AFTER_INVALID",
    }
)

# Colon-/underscore-/slash-delimited token splitter for error chains such as
# FETCH_FAILED:RATE_LIMIT_RETRY_EXHAUSTED:RATE_LIMIT_HTTP_429
_TOKEN_SPLIT_RE = re.compile(r"[^A-Za-z0-9_]+")

# Typed status field names (exact equality to 429 only).
_HTTP_STATUS_FIELDS: frozenset[str] = frozenset(
    {
        "status",
        "http_status",
        "status_code",
        "http_status_code",
        "response_status",
    }
)

# Typed classification field names that may carry canonical error codes.
_CLASSIFICATION_FIELDS: frozenset[str] = frozenset(
    {
        "error_code",
        "reason_code",
        "reason",
        "event",
        "trigger",
        "classification",
        "detail",
    }
)

# JSON / JSONL surfaces under a wallclock evidence root that may carry rate-limit telemetry.
_EVIDENCE_SCAN_NAMES: tuple[str, ...] = (
    "connectivity_events.jsonl",
    "reconnect_events.jsonl",
    "stale_events.jsonl",
    "killstate_events.jsonl",
    "runtime_events.jsonl",
    "shutdown_reason.json",
    "transport_telemetry.json",
    "observation_cycle_counters.json",
    "integrity_manifest.json",
)


def is_exact_http_429_status_v1(value: Any) -> bool:
    """True only for typed HTTP status exactly 429."""
    if value is True or value is False or value is None:
        return False
    if isinstance(value, int):
        return value == 429
    if isinstance(value, str):
        return value.strip() == "429"
    return False


def tokens_from_classification_value_v1(value: Any) -> frozenset[str]:
    """Extract alphanumeric/underscore tokens from a classification string."""
    if not isinstance(value, str):
        return frozenset()
    raw = value.strip()
    if not raw:
        return frozenset()
    return frozenset(tok for tok in _TOKEN_SPLIT_RE.split(raw.upper()) if tok)


def has_canonical_rate_limit_code_v1(value: Any) -> bool:
    """True when a classification value contains a canonical rate-limit code token."""
    return bool(tokens_from_classification_value_v1(value) & CANONICAL_RATE_LIMIT_ERROR_CODES)


def leaf_event_is_rate_limit_v1(event: Mapping[str, Any]) -> bool:
    """Classify one mapping as a rate-limit event using only its own typed fields."""
    if not isinstance(event, Mapping):
        return False

    if event.get("http_429") is True or event.get("rate_limit") is True:
        return True

    for key in _HTTP_STATUS_FIELDS:
        if key in event and is_exact_http_429_status_v1(event.get(key)):
            return True

    for key in _CLASSIFICATION_FIELDS:
        if key in event and has_canonical_rate_limit_code_v1(event.get(key)):
            return True

    return False


def event_is_rate_limit_v1(event: Mapping[str, Any]) -> bool:
    """Public predicate: leaf or nested envelope contains a rate-limit classification."""
    if leaf_event_is_rate_limit_v1(event):
        return True
    for nested_key in ("killstate", "transport", "telemetry", "events"):
        nested = event.get(nested_key)
        if isinstance(nested, Mapping) and event_is_rate_limit_v1(nested):
            return True
        if isinstance(nested, list):
            for item in nested:
                if isinstance(item, Mapping) and event_is_rate_limit_v1(item):
                    return True
    return False


def _authoritative_http_429_count_v1(payload: Mapping[str, Any]) -> int | None:
    """Return transport telemetry http_429_count when present and typed.

    Does not trust packaged ``rate_limit_event_count`` (may be a defective value).
    """
    for key in ("http_429_count", "http_429_event_count"):
        if key in payload:
            value = payload[key]
            if isinstance(value, int) and value >= 0:
                return value
            if isinstance(value, str) and value.strip().isdigit():
                return int(value.strip())
    telemetry = payload.get("transport_telemetry")
    if isinstance(telemetry, Mapping):
        return _authoritative_http_429_count_v1(telemetry)
    return None


def count_rate_limit_events_in_payloads_v1(payloads: Iterable[Any]) -> int:
    """Count rate-limit events across structured payloads (dicts / nested lists)."""
    discrete = 0
    authoritative: list[int] = []

    def _walk(node: Any) -> None:
        nonlocal discrete
        if isinstance(node, Mapping):
            auth = _authoritative_http_429_count_v1(node)
            if auth is not None:
                authoritative.append(auth)
            if leaf_event_is_rate_limit_v1(node):
                discrete += 1
            for value in node.values():
                if isinstance(value, (Mapping, list, tuple)):
                    _walk(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                _walk(item)

    for payload in payloads:
        _walk(payload)

    # Prefer authoritative transport counter when present (single session source).
    if authoritative:
        return max(authoritative)
    return discrete


def _load_json_or_jsonl_v1(path: Path) -> list[Any]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    if path.suffix == ".jsonl":
        out: list[Any] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            out.append(json.loads(line))
        return out
    payload = json.loads(text)
    return [payload]


def count_rate_limit_events_from_evidence_root_v1(evidence_root: Path) -> int:
    """Count structured rate-limit events under a session or wallclock evidence directory."""
    root = Path(evidence_root)
    scan_roots = [root]
    wallclock = root / "wallclock_run"
    if wallclock.is_dir():
        scan_roots.append(wallclock)
    payloads: list[Any] = []
    for scan_root in scan_roots:
        for name in _EVIDENCE_SCAN_NAMES:
            payloads.extend(_load_json_or_jsonl_v1(scan_root / name))
    return count_rate_limit_events_in_payloads_v1(payloads)


def compute_rate_limit_event_count_v1(
    *,
    evidence_root: Path | None = None,
    payloads: Iterable[Any] | None = None,
) -> int:
    """Public Phase 9.2 metric entrypoint for ``rate_limit_event_count``."""
    if evidence_root is not None:
        return count_rate_limit_events_from_evidence_root_v1(Path(evidence_root))
    if payloads is not None:
        return count_rate_limit_events_in_payloads_v1(payloads)
    raise ValueError("RATE_LIMIT_METRIC_INPUT_REQUIRED")
