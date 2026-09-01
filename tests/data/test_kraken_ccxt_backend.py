"""KrakenCcxtBackend is historical-only; current operative use is rejected."""

from __future__ import annotations

import pytest

from src.data.providers.kraken_ccxt_backend import KrakenCcxtBackend
from src.exchange.operative_venue_boundary_v1 import NoncanonicalVenueRejectedError


def test_kraken_ccxt_backend_exchange_rejected() -> None:
    backend = KrakenCcxtBackend()
    with pytest.raises(NoncanonicalVenueRejectedError):
        backend._exchange()
