"""Exit-Codes und Run-Manifeste für Forward-Generate/Evaluate (NO-LIVE)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def cfg_test_path() -> Path:
    p = ROOT / "config" / "config.test.toml"
    if not p.is_file():
        pytest.skip(f"fehlt: {p}")
    return p


def test_generate_forward_exits_1_and_writes_manifest_when_no_signals(
    tmp_path, monkeypatch, cfg_test_path: Path
) -> None:
    import generate_forward_signals as gen

    empty_meta = {
        "symbol": "BTC/EUR",
        "ohlcv_source": "dummy",
        "timeframe": "1h",
        "n_bars_requested": 200,
        "bars_loaded": 0,
        "kraken_pagination_used": None,
        "kraken_bars_shortfall": None,
    }

    def empty_load(*_a, **_k):
        return pd.DataFrame(), empty_meta

    monkeypatch.setattr(gen, "load_data_for_symbol", empty_load)

    out_dir = tmp_path / "forward"
    out_dir.mkdir()
    code = gen.main(
        [
            "--strategy",
            "ma_crossover",
            "--symbols",
            "BTC/EUR",
            "--config-path",
            str(cfg_test_path),
            "--output-dir",
            str(out_dir),
            "--run-name",
            "contract_empty",
            "--n-bars",
            "200",
        ]
    )
    assert code == 1
    manifests = list(out_dir.glob("*_run_manifest.json"))
    assert len(manifests) == 1
    payload = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert payload["exit_code"] == 1
    assert payload["script_name"] == "generate_forward_signals.py"
    assert payload["strategy"] == "ma_crossover"
    assert "symbols" in payload and "BTC/EUR" in payload["symbols"]
    assert "run_id" in payload and len(payload["run_id"]) == 64
    assert payload.get("generated_at_utc") and isinstance(payload["generated_at_utc"], str)
    assert payload["generated_at_utc"].endswith("Z")
    assert payload["config_path"] == str(cfg_test_path)
    assert "python_version" in payload


def test_evaluate_forward_exits_1_on_empty_signals_csv(tmp_path, cfg_test_path: Path) -> None:
    import evaluate_forward_signals as ev

    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("symbol,as_of,direction\n", encoding="utf-8")
    out_dir = tmp_path / "eval"
    out_dir.mkdir()

    code = ev.main(
        [
            str(csv_path),
            "--config-path",
            str(cfg_test_path),
            "--output-dir",
            str(out_dir),
        ]
    )
    assert code == 1
    man = out_dir / "empty_eval_run_manifest.json"
    assert man.is_file()
    payload = json.loads(man.read_text(encoding="utf-8"))
    assert payload["exit_code"] == 1
    assert payload["script_name"] == "evaluate_forward_signals.py"
    assert payload["signals_csv"] == str(csv_path)
    assert "run_id" in payload and len(payload["run_id"]) == 64
    assert payload.get("generated_at_utc") and isinstance(payload["generated_at_utc"], str)
    assert payload["generated_at_utc"].endswith("Z")
    assert payload["config_path"] == str(cfg_test_path)
