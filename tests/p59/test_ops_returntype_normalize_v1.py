from __future__ import annotations

import json
from pathlib import Path

from src.ops.p58.switch_layer_online_readiness_v1 import (
    P58RunContextV1,
    run_switch_layer_online_readiness_v1,
)


def test_p58_returns_jsonable_dict(tmp_path: Path) -> None:
    ctx = P58RunContextV1(
        mode="paper",
        run_id="t",
        out_dir=tmp_path,
        allow_bull_strategies=["s1"],
    )
    res = run_switch_layer_online_readiness_v1([0.002] * 220, ctx)
    assert isinstance(res, dict)
    json.dumps(res)

    assert "routing" in res and isinstance(res["routing"], dict)
    assert "regime" in res and res["regime"] in ("bull", "bear", "neutral")
    assert res["routing"]["ai_mode"] in ("disabled", "shadow", "paper")
