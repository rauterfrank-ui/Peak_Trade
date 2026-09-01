"""Historical kraken_futures_demo payload builder is not a current operative surface."""

from __future__ import annotations

import pytest

from src.exchange.operative_venue_boundary_v1 import NoncanonicalVenueRejectedError
from src.ops.order_capability_payload_builder_contract_v1 import (
    PACKAGE_MARKER,
    build_order_capability_payload,
)


def test_package_marker_present() -> None:
    assert PACKAGE_MARKER.endswith("=true")


def test_build_order_capability_payload_current_operative_use_rejected() -> None:
    with pytest.raises(NoncanonicalVenueRejectedError):
        build_order_capability_payload(object())  # type: ignore[arg-type]
