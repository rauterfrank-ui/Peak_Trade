"""Tests für ISO-UTC-as_of in generate_forward_signals."""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from generate_forward_signals import format_as_of_iso_utc


@pytest.mark.smoke
def test_format_as_of_iso_utc_from_utc_timestamp():
    ts = pd.Timestamp("2025-01-01 12:00:00", tz="UTC")
    assert format_as_of_iso_utc(ts) == "2025-01-01T12:00:00Z"


def test_format_as_of_iso_utc_converts_offset():
    ts = pd.Timestamp("2025-01-01 14:00:00+02:00")
    assert format_as_of_iso_utc(ts) == "2025-01-01T12:00:00Z"


def test_format_as_of_iso_utc_naive_localized_to_utc():
    ts = pd.Timestamp("2025-01-01 12:00:00")
    assert format_as_of_iso_utc(ts) == "2025-01-01T12:00:00Z"


def test_format_as_of_iso_utc_nat_raises():
    with pytest.raises(ValueError, match="as_of"):
        format_as_of_iso_utc(pd.NaT)
