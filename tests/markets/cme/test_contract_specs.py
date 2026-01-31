from __future__ import annotations

from datetime import date

import pytest

from src.markets.cme.calendar import cme_equity_index_roll_date, third_friday
from src.markets.cme.contracts import get_contract_spec
from src.markets.cme.symbols import (
    MONTH_CODE_BY_MONTH,
    format_cme_contract_symbol,
    parse_cme_contract_symbol,
)


def test_nq_mnq_tick_values() -> None:
    nq = get_contract_spec("NQ")
    mnq = get_contract_spec("MNQ")

    assert nq.multiplier == 20.0
    assert nq.min_tick == 0.25
    assert nq.tick_value == 5.0

    assert mnq.multiplier == 2.0
    assert mnq.min_tick == 0.25
    assert mnq.tick_value == 0.5


def test_month_code_mapping_complete() -> None:
    assert set(MONTH_CODE_BY_MONTH.keys()) == set(range(1, 13))
    assert len(set(MONTH_CODE_BY_MONTH.values())) == 12
    assert MONTH_CODE_BY_MONTH[3] == "H"  # March
    assert MONTH_CODE_BY_MONTH[12] == "Z"  # December


def test_contract_symbol_format_and_parse_roundtrip() -> None:
    sym = format_cme_contract_symbol("nq", 3, 2026)
    assert sym == "NQH2026"
    parsed = parse_cme_contract_symbol(sym)
    assert parsed.root == "NQ"
    assert parsed.month == 3
    assert parsed.year == 2026
    assert parsed.to_symbol() == "NQH2026"


def test_third_friday_known_month() -> None:
    # March 2026 third Friday is 2026-03-20
    assert third_friday(2026, 3) == date(2026, 3, 20)


@pytest.mark.roll
def test_roll_date_is_monday_prior_to_third_friday() -> None:
    # Roll date = third Friday - 4 days => Monday
    roll = cme_equity_index_roll_date(2026, 3)
    assert roll == date(2026, 3, 16)
    assert roll.weekday() == 0  # Monday


@pytest.mark.roll
def test_roll_date_input_validation() -> None:
    with pytest.raises(ValueError):
        third_friday(2026, 13)
