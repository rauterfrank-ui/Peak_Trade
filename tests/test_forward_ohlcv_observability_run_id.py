"""NO-LIVE: run_id in OHLCV-Observability-Zeilen (Generate/Evaluate)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

_SAMPLE_META = {
    "symbol": "BTC/EUR",
    "ohlcv_source": "dummy",
    "timeframe": "1h",
    "n_bars_requested": 200,
    "bars_loaded": 0,
    "kraken_pagination_used": None,
    "kraken_bars_shortfall": None,
}


def test_generate_ohlcv_observability_print_includes_run_id(capsys) -> None:
    import generate_forward_signals as gen

    rid = "a" * 64
    gen._print_ohlcv_load_observability(_SAMPLE_META, run_id=rid)
    out = capsys.readouterr().out
    assert "run_id=" in out
    assert rid in out


def test_evaluate_ohlcv_observability_print_includes_run_id(capsys) -> None:
    import evaluate_forward_signals as ev

    rid = "b" * 64
    ev._print_ohlcv_load_observability(_SAMPLE_META, run_id=rid)
    out = capsys.readouterr().out
    assert "run_id=" in out
    assert rid in out


def test_ohlcv_observability_without_run_id_omits_suffix(capsys) -> None:
    import generate_forward_signals as gen

    gen._print_ohlcv_load_observability(_SAMPLE_META)
    out = capsys.readouterr().out
    assert "run_id=" not in out
