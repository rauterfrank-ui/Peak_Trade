"""SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1 — canonical redaction owner.

Capability: SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1
Contract ID: secret_hygiene_redaction_v1

Design decision: Option B — ratify one narrowly scoped canonical redaction owner
because no repository-wide redaction SSOT existed. Fragmented local helpers
(evidence_pack_generator._redact_content, model_client.redact_outbound_envelope,
bounded shadow command sanitizer, private-readonly allowlists) remain legacy
consumers and must not grow parallel policy; new serialization/logging/diagnostics
/evidence boundaries must call this module.

Non-authorizing. Does not rotate secrets, mutate Runtime/trading authority,
or rewrite Git history. Dashboard/read-model callers remain pure consumers.
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

CONTRACT_ID = "secret_hygiene_redaction_v1"
CONTRACT_VERSION = "v1"
CAPABILITY_ID = "SECRET_HYGIENE_AND_REDACTION_UNIFICATION_V1"
REDACTION_MARKER = "[REDACTED]"
UNSUPPORTED_PAYLOAD_MARKER = "[REDACTED:UNSUPPORTED_PAYLOAD]"
MAX_RECURSION_DEPTH = 32
MAX_STRING_CHARS = 1_000_000

# Exact / suffix-oriented sensitive key names (case-insensitive match on
# normalized key: lower, non-alnum -> underscore).
SENSITIVE_KEY_NAMES: frozenset[str] = frozenset(
    {
        "api_key",
        "apikey",
        "api_secret",
        "apisecret",
        "access_key",
        "access_token",
        "refresh_token",
        "id_token",
        "client_secret",
        "client_secret_key",
        "password",
        "passwd",
        "passphrase",
        "secret",
        "secrets",
        "token",
        "auth_token",
        "authorization",
        "proxy_authorization",
        "cookie",
        "set_cookie",
        "session",
        "session_id",
        "csrf_token",
        "confirm_token",
        "webhook_secret",
        "private_key",
        "privatekey",
        "ssh_key",
        "signing_key",
        "aws_secret_access_key",
        "aws_access_key_id",
        "database_url",
        "db_url",
        "db_password",
        "redis_url",
        "mongo_uri",
        "connection_string",
        "credentials",
        "credential",
        "exchange_api_key",
        "exchange_secret",
        "okx_api_key",
        "okx_secret_key",
        "okx_passphrase",
        "kraken_api_key",
        "kraken_api_secret",
        "binance_api_key",
        "binance_api_secret",
    }
)

SENSITIVE_HEADER_NAMES: frozenset[str] = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "x-amz-security-token",
    }
)

_BEARER_RX = re.compile(r"(?i)\b(Bearer)\s+([A-Za-z0-9_\-\.\/=+]+)")
_BASIC_AUTH_HEADER_RX = re.compile(r"(?i)\b(Basic)\s+([A-Za-z0-9_\-\.\/=+]+)")
_SK_RX = re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")
_AKIA_RX = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_JWT_RX = re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b")
_PEM_BLOCK_RX = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    re.DOTALL,
)
_ASSIGNMENT_RX = re.compile(
    r"(?i)\b(api[_-]?key|api[_-]?secret|client[_-]?secret|access[_-]?token|"
    r"refresh[_-]?token|password|passwd|passphrase|secret|token|authorization|"
    r"cookie|set[_-]?cookie|session)"
    r"\s*[=:]\s*([^\s\"']+)"
)
_URL_USERINFO_RX = re.compile(
    r"(?i)\b((?:https?|postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://)"
    r"([^/\s:@]+):([^/\s@]+)@"
)
# Bracketless placeholder keeps urlsplit host/path intact ([REDACTED] looks like IPv6).
_URL_USERINFO_PLACEHOLDER = "REDACTED:REDACTED@"


def _normalize_key(key: Any) -> str:
    text = str(key).strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def is_sensitive_key(key: Any) -> bool:
    """Return True when a mapping key is treated as secret-bearing."""
    normalized = _normalize_key(key)
    if not normalized:
        return False
    if normalized in SENSITIVE_KEY_NAMES:
        return True
    # Suffix / compound forms: foo_api_key, my_password, auth_token_value
    for marker in (
        "api_key",
        "api_secret",
        "access_token",
        "refresh_token",
        "client_secret",
        "private_key",
        "password",
        "passphrase",
        "webhook_secret",
        "secret_key",
        "auth_token",
    ):
        if normalized == marker or normalized.endswith("_" + marker):
            return True
    if normalized.endswith("_secret") or normalized.endswith("_token"):
        return True
    return False


def redact_string(value: str) -> str:
    """Redact embedded credential-like fragments in a string. Idempotent."""
    if value is None:  # type: ignore[unreachable]
        return value
    if not isinstance(value, str):
        raise TypeError("redact_string expects str")
    if value == "" or value == REDACTION_MARKER or value == UNSUPPORTED_PAYLOAD_MARKER:
        return value
    if len(value) > MAX_STRING_CHARS:
        # Fail closed: oversized opaque blobs are not passed through raw.
        return REDACTION_MARKER

    out = value
    if REDACTION_MARKER in out and not _still_contains_secret_like(out):
        # Already fully redacted for detectable classes.
        pass

    out = _PEM_BLOCK_RX.sub(REDACTION_MARKER, out)
    out = _BEARER_RX.sub(rf"\1 {REDACTION_MARKER}", out)
    out = _BASIC_AUTH_HEADER_RX.sub(rf"\1 {REDACTION_MARKER}", out)
    out = _JWT_RX.sub(REDACTION_MARKER, out)
    out = _SK_RX.sub(REDACTION_MARKER, out)
    out = _AKIA_RX.sub(REDACTION_MARKER, out)
    out = _ASSIGNMENT_RX.sub(rf"\1={REDACTION_MARKER}", out)
    out = _URL_USERINFO_RX.sub(rf"\1{_URL_USERINFO_PLACEHOLDER}", out)
    out = _redact_url_query_secrets(out)
    return out


def _still_contains_secret_like(text: str) -> bool:
    probes = (_PEM_BLOCK_RX, _BEARER_RX, _BASIC_AUTH_HEADER_RX, _JWT_RX, _SK_RX, _AKIA_RX)
    return any(rx.search(text) for rx in probes)


def _redact_url_query_secrets(text: str) -> str:
    """Redact credential-bearing query parameters while keeping host/path."""

    def _rewrite_match(match: re.Match[str]) -> str:
        raw = match.group(0)
        try:
            parts = urlsplit(raw)
        except ValueError:
            return REDACTION_MARKER
        if not parts.scheme or not parts.netloc:
            return raw
        if not parts.query:
            return raw
        pairs: list[str] = []
        for item in parts.query.split("&"):
            if not item:
                continue
            if "=" not in item:
                pairs.append(item)
                continue
            key, _val = item.split("=", 1)
            if is_sensitive_key(key):
                pairs.append(f"{key}={REDACTION_MARKER}")
            else:
                pairs.append(item)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "&".join(pairs), parts.fragment))

    return re.sub(r"https?://[^\s\"'<>]+", _rewrite_match, text)


def redact_headers(headers: Mapping[Any, Any] | None) -> dict[str, Any]:
    """Redact HTTP header maps. Preserves non-sensitive header names/values."""
    if headers is None:
        return {}
    if not isinstance(headers, Mapping):
        return {"_redaction_status": UNSUPPORTED_PAYLOAD_MARKER}
    out: dict[str, Any] = {}
    for key, value in headers.items():
        key_text = str(key)
        if key_text.lower() in SENSITIVE_HEADER_NAMES or is_sensitive_key(key_text):
            out[key_text] = REDACTION_MARKER
        elif isinstance(value, str):
            out[key_text] = redact_string(value)
        else:
            out[key_text] = redact_structured(value, _depth=1)
    return out


def redact_structured(payload: Any, *, _depth: int = 0) -> Any:
    """Recursively redact mappings/sequences/dataclasses/strings.

    Fail-closed:
    - depth overflow -> REDACTION_MARKER
    - unsupported object types -> UNSUPPORTED_PAYLOAD_MARKER (never raw repr)
    - never fabricates replacement business data
    """
    if _depth > MAX_RECURSION_DEPTH:
        return REDACTION_MARKER

    if payload is None or isinstance(payload, bool):
        return payload
    if isinstance(payload, (int, float)):
        return payload
    if isinstance(payload, str):
        return redact_string(payload)
    if isinstance(payload, bytes):
        # Opaque bytes are not decoded into possibly-secret text.
        return REDACTION_MARKER
    if is_dataclass(payload) and not isinstance(payload, type):
        try:
            return redact_structured(asdict(payload), _depth=_depth + 1)
        except Exception:
            return UNSUPPORTED_PAYLOAD_MARKER
    if isinstance(payload, Mapping):
        out: dict[Any, Any] = {}
        for key, value in payload.items():
            if is_sensitive_key(key):
                # Preserve empty/null as-is (no secret material).
                if value is None or value == "":
                    out[key] = value
                else:
                    out[key] = REDACTION_MARKER
            else:
                out[key] = redact_structured(value, _depth=_depth + 1)
        return out
    if isinstance(payload, tuple):
        return tuple(redact_structured(item, _depth=_depth + 1) for item in payload)
    if isinstance(payload, list):
        return [redact_structured(item, _depth=_depth + 1) for item in payload]
    if isinstance(payload, set):
        # Deterministic ordering for testability.
        return {redact_structured(item, _depth=_depth + 1) for item in sorted(payload, key=repr)}
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        return [redact_structured(item, _depth=_depth + 1) for item in payload]

    # Fail closed: do not pass through unknown objects via repr/str.
    return UNSUPPORTED_PAYLOAD_MARKER


def redact_exception(exc: BaseException) -> str:
    """Render an exception for logs/diagnostics without raw secret passthrough."""
    cls = type(exc).__name__
    msg = redact_string(str(exc))
    return f"{cls}: {msg}"


def redact_for_logging(message: Any, *args: Any) -> str:
    """Boundary helper for log messages (and %-style args already interpolated)."""
    if args:
        try:
            rendered = str(message) % args
        except Exception:
            rendered = f"{message!s} | args={REDACTION_MARKER}"
    else:
        rendered = message if isinstance(message, str) else str(message)
    return redact_string(rendered)


def redact_for_diagnostics(payload: Any) -> Any:
    """Boundary helper for diagnostics / audit payloads."""
    return redact_structured(payload)


def redact_for_evidence_export(payload: Any) -> Any:
    """Boundary helper for evidence / report export serialization."""
    return redact_structured(payload)


def redact_for_webui_payload(payload: Any) -> Any:
    """Boundary helper for dashboard/API/read-model serialization.

    Dashboard remains a pure read-only consumer and not a security authority;
    this helper is the approved serialization-edge redaction.
    """
    return redact_structured(payload)


def assert_no_raw_secret(output: Any, synthetic_secret: str) -> None:
    """Test helper: fail if a complete synthetic secret appears in output."""
    if not synthetic_secret:
        raise ValueError("synthetic_secret must be non-empty")
    blob = output if isinstance(output, str) else repr(output)
    if synthetic_secret in blob:
        raise AssertionError("synthetic secret leaked into redacted output")


class SecretRedactionLoggingFilter(logging.Filter):
    """Logging filter that redacts secret-like content at the logging boundary."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            record.msg = REDACTION_MARKER
            record.args = ()
            return True
        redacted = redact_string(msg)
        record.msg = redacted
        record.args = ()
        # Also scrub common extra fields if present.
        for attr in ("api_key", "token", "password", "authorization", "secret"):
            if hasattr(record, attr):
                setattr(record, attr, REDACTION_MARKER)
        return True


def install_logging_redaction_filter(
    logger: logging.Logger | None = None,
) -> SecretRedactionLoggingFilter:
    """Attach the canonical redaction filter to a logger (root if None)."""
    target = logger if logger is not None else logging.getLogger()
    existing = [f for f in target.filters if isinstance(f, SecretRedactionLoggingFilter)]
    if existing:
        return existing[0]
    filt = SecretRedactionLoggingFilter()
    target.addFilter(filt)
    return filt


def owner_identity() -> dict[str, str]:
    """Machine-readable owner identity for uniqueness contracts."""
    return {
        "capability_id": CAPABILITY_ID,
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "redaction_marker": REDACTION_MARKER,
        "module": "scripts.security.secret_hygiene_redaction_v1",
    }


__all__ = [
    "CAPABILITY_ID",
    "CONTRACT_ID",
    "CONTRACT_VERSION",
    "MAX_RECURSION_DEPTH",
    "REDACTION_MARKER",
    "SENSITIVE_HEADER_NAMES",
    "SENSITIVE_KEY_NAMES",
    "UNSUPPORTED_PAYLOAD_MARKER",
    "SecretRedactionLoggingFilter",
    "assert_no_raw_secret",
    "install_logging_redaction_filter",
    "is_sensitive_key",
    "owner_identity",
    "redact_exception",
    "redact_for_diagnostics",
    "redact_for_evidence_export",
    "redact_for_logging",
    "redact_for_webui_payload",
    "redact_headers",
    "redact_string",
    "redact_structured",
]
