"""Golden fixture tests for P4C L2 market outlook schema and invariants."""
import json
from pathlib import Path

FIX_DIR = Path(__file__).resolve().parent / "fixtures" / "p4c_l2_market_outlook"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_outlook(fixture_name: str) -> dict:
    p = FIX_DIR / fixture_name / "l2_market_outlook.json"
    return _load(p)


def test_golden_baseline_schema_and_keys():
    """Baseline fixture has required schema keys."""
    data = _load_outlook("baseline")
    assert isinstance(data, dict)
    for k in ["meta", "inputs", "outlook"]:
        assert k in data, f"missing key: {k}"
    meta = data["meta"]
    assert "created_at_utc" in meta
    assert "schema_version" in meta
    outlook = data["outlook"]
    assert "regime" in outlook
    assert "no_trade" in outlook
    assert "no_trade_reasons" in outlook


def test_golden_baseline_invariants():
    """Baseline: NEUTRAL regime, no_trade=false."""
    data = _load_outlook("baseline")
    outlook = data["outlook"]
    assert outlook["regime"] == "NEUTRAL"
    assert outlook["no_trade"] is False
    assert outlook["no_trade_reasons"] == []


def test_golden_high_vol_schema_and_invariants():
    """High-vol fixture: HIGH_VOL regime, no_trade with VOL_EXTREME."""
    data = _load_outlook("high_vol")
    assert "outlook" in data
    outlook = data["outlook"]
    assert "no_trade" in outlook
    assert "no_trade_reasons" in outlook
    assert isinstance(outlook["no_trade_reasons"], list)
    assert outlook["regime"] == "HIGH_VOL"
    assert outlook["no_trade"] is True
    assert "VOL_EXTREME" in outlook["no_trade_reasons"]


def test_golden_illiquid_schema_and_invariants():
    """Illiquid fixture: no_trade with MISSING_FEATURES."""
    data = _load_outlook("illiquid")
    assert "outlook" in data
    outlook = data["outlook"]
    assert "no_trade" in outlook
    assert "no_trade_reasons" in outlook
    assert isinstance(outlook["no_trade_reasons"], list)
    assert outlook["no_trade"] is True
    assert "MISSING_FEATURES" in outlook["no_trade_reasons"]


def test_golden_market_outlook_alias():
    """market_outlook.json is alias of l2_market_outlook.json."""
    for name in ("baseline", "high_vol", "illiquid"):
        p1 = FIX_DIR / name / "l2_market_outlook.json"
        p2 = FIX_DIR / name / "market_outlook.json"
        if p2.exists():
            d1 = _load(p1)
            d2 = _load(p2)
            assert d1 == d2, f"{name}: alias content mismatch"
