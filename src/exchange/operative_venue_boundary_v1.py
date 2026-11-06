"""Current operative venue boundary.

Peak_Trade's current operative venue is OKX EEA. Noncanonical venue
clients, factories, and defaults must fail closed. This module does not
implement exchange I/O and does not relabel other venues as OKX.
"""

from __future__ import annotations

ALLOWED_OPERATIVE_VENUE_SET = frozenset(
    {
        "OKX_EEA",
        "okx",
        "okx_europe_eea",
        "OKX_EEA_DEMO",
    }
)

NONCANONICAL_VENUE_REJECTED = (
    "noncanonical_venue_rejected: current operative venue is OKX_EEA; "
    "this surface is not selectable"
)


class NoncanonicalVenueRejectedError(ValueError):
    """Raised when a noncanonical venue surface is selected or instantiated."""


def reject_noncanonical_operative_surface(*, surface: str) -> None:
    raise NoncanonicalVenueRejectedError(f"{NONCANONICAL_VENUE_REJECTED}; surface={surface}")


def assert_operative_ccxt_venue_id(exchange_id: str) -> str:
    """Map Peak_Trade OKX venue names to the existing ccxt OKX class id only."""
    raw = str(exchange_id or "").strip()
    mapping = {
        "okx": "okx",
        "okx_europe_eea": "okx",
        "OKX_EEA": "okx",
        "OKX_EEA_DEMO": "okx",
    }
    if raw not in mapping:
        raise NoncanonicalVenueRejectedError(f"{NONCANONICAL_VENUE_REJECTED}; exchange_id={raw!r}")
    return mapping[raw]
