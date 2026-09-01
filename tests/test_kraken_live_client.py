"""KrakenLiveClient is historical-only; current operative construction is rejected."""

from __future__ import annotations

import pytest

from src.exchange.kraken_live import (
    KrakenLiveClient,
    KrakenLiveConfig,
    create_kraken_live_client_from_config,
)
from src.exchange.operative_venue_boundary_v1 import NoncanonicalVenueRejectedError
from src.core.peak_config import PeakConfig
from src.exchange import build_trading_client_from_config


def test_kraken_live_client_operative_construction_rejected() -> None:
    with pytest.raises(NoncanonicalVenueRejectedError):
        KrakenLiveClient(KrakenLiveConfig())


def test_create_kraken_live_client_from_config_rejected() -> None:
    with pytest.raises(NoncanonicalVenueRejectedError):
        create_kraken_live_client_from_config(PeakConfig(raw={}))


def test_trading_factory_rejects_kraken_live() -> None:
    with pytest.raises(ValueError, match="noncanonical_venue_rejected"):
        build_trading_client_from_config(
            PeakConfig(raw={"exchange": {"default_type": "kraken_live"}})
        )
