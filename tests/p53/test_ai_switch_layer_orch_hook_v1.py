from __future__ import annotations

import json
from pathlib import Path

from src.ai.switch_layer.types_v1 import MarketRegimeV1
from src.ai_orchestration.switch_layer_orch_v1 import SwitchLayerContextV1, run_switch_layer_orch_v1


def test_switch_layer_orch_no_outdir_no_write(tmp_path: Path) -> None:
    returns = [0.001] * 120
    ctx = SwitchLayerContextV1(symbol="BTC/USDT", timeframe="1h", out_dir=None)
    decision = run_switch_layer_orch_v1(returns=returns, ctx=ctx)
    assert decision.regime in (MarketRegimeV1.BULL, MarketRegimeV1.BEAR, MarketRegimeV1.NEUTRAL)
    assert not (tmp_path / "switch_layer_decision_v1.json").exists()


def test_switch_layer_orch_writes_evidence_when_outdir_set(tmp_path: Path) -> None:
    returns = [0.002] * 120
    out_dir = tmp_path / "evi"
    ctx = SwitchLayerContextV1(symbol="BTC/USDT", timeframe="1h", out_dir=str(out_dir), meta={"k": "v"})
    decision = run_switch_layer_orch_v1(returns=returns, ctx=ctx)

    p = out_dir / "switch_layer_decision_v1.json"
    assert p.exists()
    payload = json.loads(p.read_text(encoding="utf-8"))
    assert payload["symbol"] == "BTC/USDT"
    assert payload["timeframe"] == "1h"
    assert payload["decision"]["regime"] == decision.regime.value
    assert payload["meta"]["k"] == "v"


def test_switch_layer_orch_deterministic_same_input_same_output(tmp_path: Path) -> None:
    returns = [0.0005] * 200
    ctx = SwitchLayerContextV1(symbol="ETH/USDT", timeframe="4h", out_dir=str(tmp_path / "evi"))
    d1 = run_switch_layer_orch_v1(returns=returns, ctx=ctx)
    d2 = run_switch_layer_orch_v1(returns=returns, ctx=ctx)
    assert d1.regime == d2.regime
    assert d1.confidence == d2.confidence
    assert d1.evidence == d2.evidence
