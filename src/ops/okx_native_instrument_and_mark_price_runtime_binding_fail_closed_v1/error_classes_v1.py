"""Classified market-data binding errors (deterministic vs transport)."""

from __future__ import annotations

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    DETERMINISTIC_ERROR_CLASSES,
    ERROR_CLASSES,
)


class MarketDataBindingErrorV1(RuntimeError):
    """Fail-closed classified market-data / mapping error."""

    def __init__(self, error_class: str, detail: str = "") -> None:
        if error_class not in ERROR_CLASSES:
            raise ValueError(f"UNKNOWN_ERROR_CLASS:{error_class}")
        self.error_class = error_class
        self.detail = detail
        message = error_class if not detail else f"{error_class}:{detail}"
        super().__init__(message)

    @property
    def reconnectable(self) -> bool:
        return self.error_class not in DETERMINISTIC_ERROR_CLASSES


def classify_transport_message_v1(message: str) -> tuple[str, bool]:
    """Return (error_class, reconnectable) for a transport/exception message."""
    msg = str(message or "")
    for cls in sorted(DETERMINISTIC_ERROR_CLASSES, key=len, reverse=True):
        if msg == cls or msg.startswith(cls + ":") or cls in msg:
            return cls, False
    # Legacy schema strings that must never consume reconnect budget.
    if "REQUIRED_PRICE_FIELD_MISSING" in msg:
        return "REQUIRED_PRICE_FIELD_MISSING", False
    if "REQUIRED_PRICE_FIELD_INVALID" in msg or "INVALID_PRICE_VALUE" in msg:
        return "INVALID_PRICE_VALUE", False
    if "TICKER_DATA_MISSING" in msg or "MARK_PRICE" in msg and "EMPTY" in msg:
        return "PUBLIC_MARK_PRICE_RESPONSE_EMPTY", False
    if "PROVIDER_CODE_" in msg or "PAYLOAD_NOT_OBJECT" in msg:
        return "TRANSPORT_FAILURE", False
    if msg.startswith("HTTP_") or "FETCH_FAILED" in msg or "RATE_LIMIT" in msg:
        return "TRANSPORT_FAILURE", True
    return "TRANSPORT_FAILURE", True
