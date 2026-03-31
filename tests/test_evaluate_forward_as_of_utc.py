"""Tests für UTC-Normalisierung von Forward-Signal-as_of (evaluate_forward_signals)."""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_forward_signals import parse_args, parse_as_of_to_utc


@pytest.mark.smoke
def test_parse_as_of_naive_string_is_utc():
    ts = parse_as_of_to_utc("2024-06-01 12:00:00")
    assert ts.tz is not None
    assert str(ts.tz) == "UTC"
    assert ts.hour == 12


def test_parse_as_of_z_suffix():
    ts = parse_as_of_to_utc("2024-06-01T12:00:00Z")
    assert ts.tz is not None
    assert ts == pd.Timestamp("2024-06-01 12:00:00", tz="UTC")


def test_parse_as_of_non_utc_offset_converts():
    ts = parse_as_of_to_utc("2024-06-01 14:00:00+02:00")
    assert ts == pd.Timestamp("2024-06-01 12:00:00", tz="UTC")


def test_parse_as_of_nat_like_raises():
    with pytest.raises(ValueError, match="as_of"):
        parse_as_of_to_utc("")


@pytest.mark.smoke
def test_parse_args_n_bars_default():
    args = parse_args(["dummy.csv"])
    assert args.n_bars == 200


def test_parse_args_n_bars_custom():
    args = parse_args(["signals.csv", "--n-bars", "150"])
    assert args.n_bars == 150
