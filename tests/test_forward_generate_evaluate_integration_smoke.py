"""
Integrationssmoke: Forward-Signal-CSV (ISO-UTC as_of) → Evaluation mit gemeinsamem OHLCV-Fenster.

Hintergrund: ``evaluate_signals_for_symbol`` braucht eine Bar *nach* ``as_of`` (Entry).
Signale von ``generate_forward_signals`` nutzen typischerweise die letzte Bar als ``as_of`` —
dann ist kein Entry möglich. Der End-to-End-Test schreibt daher ein bewusstes ``as_of``
in die Mitte der Serie, während Preisdaten und Loader mit dem Generate-Lauf übereinstimmen.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from evaluate_forward_signals import (  # noqa: E402
    evaluate_signals_for_symbol,
    load_signal_df,
)
from generate_forward_signals import format_as_of_iso_utc  # noqa: E402
from _shared_ohlcv_loader import load_dummy_ohlcv  # noqa: E402


@pytest.mark.smoke
@pytest.mark.integration
def test_csv_roundtrip_as_of_iso_utc_aligns_with_price_index(tmp_path, monkeypatch):
    """Smoke: ISO-Z-as_of aus CSV + UTC-Preisindex → mindestens ein auswertbarer Trade."""
    df_price = load_dummy_ohlcv("BTC/EUR", n_bars=200)
    as_of_ts = df_price.index[80]
    as_of_str = format_as_of_iso_utc(as_of_ts)

    csv_path = tmp_path / "signals.csv"
    pd.DataFrame(
        [
            {
                "symbol": "BTC/EUR",
                "as_of": as_of_str,
                "direction": 1.0,
            }
        ]
    ).to_csv(csv_path, index=False)

    monkeypatch.setattr(
        "evaluate_forward_signals.load_price_data",
        lambda symbol, n_bars=200: df_price,
    )

    df_sig = load_signal_df(csv_path)
    out = evaluate_signals_for_symbol(
        df_sig.groupby("symbol").get_group("BTC/EUR"),
        "BTC/EUR",
        horizon_bars=1,
    )
    assert not out.empty
    assert (out["return"].astype(float).notna()).all()


@pytest.mark.integration
def test_generate_then_evaluate_with_captured_ohlcv(tmp_path, monkeypatch):
    """Generate → CSV → Evaluate mit identischem OHLCV-Fenster (as_of mittig gesetzt)."""
    import generate_forward_signals as gen
    import evaluate_forward_signals as ev

    cfg_path = ROOT / "config" / "config.test.toml"
    if not cfg_path.is_file():
        pytest.skip(f"fehlt: {cfg_path}")

    captured: dict[str, pd.DataFrame] = {}

    def capture_load(symbol: str, n_bars: int = 200) -> pd.DataFrame:
        df = load_dummy_ohlcv(symbol, n_bars=n_bars)
        captured[symbol] = df
        return df

    exp_dir = tmp_path / "experiments"
    exp_csv = exp_dir / "experiments.csv"
    monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", exp_dir)
    monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", exp_csv)

    monkeypatch.setattr(gen, "load_data_for_symbol", capture_load)

    out_dir = tmp_path / "forward"
    out_dir.mkdir(parents=True)

    gen.main(
        [
            "--strategy",
            "ma_crossover",
            "--symbols",
            "BTC/EUR",
            "--config-path",
            str(cfg_path),
            "--output-dir",
            str(out_dir),
            "--run-name",
            "integration_smoke",
            "--n-bars",
            "200",
        ]
    )

    sig_files = list(out_dir.glob("*_signals.csv"))
    assert len(sig_files) == 1
    sig_path = sig_files[0]

    df_csv = pd.read_csv(sig_path)
    assert "as_of" in df_csv.columns
    df_p = captured["BTC/EUR"]
    df_csv.loc[0, "as_of"] = format_as_of_iso_utc(df_p.index[-40])
    df_csv.to_csv(sig_path, index=False)

    monkeypatch.setattr(ev, "load_price_data", lambda sym, n_bars=200: captured[sym].copy())

    eval_dir = tmp_path / "eval"
    eval_dir.mkdir()

    ev.main(
        [
            str(sig_path),
            "--horizon-bars",
            "1",
            "--config-path",
            str(cfg_path),
            "--output-dir",
            str(eval_dir),
        ]
    )

    eval_files = list(eval_dir.glob("*_eval_*.csv"))
    assert len(eval_files) >= 1
    df_eval = pd.read_csv(eval_files[0])
    assert not df_eval.empty
    assert "return" in df_eval.columns
