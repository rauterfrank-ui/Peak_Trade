from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.ai.switch_layer.types_v1 import SwitchDecisionV1


def write_switch_layer_evidence_v1(
    *,
    out_dir: str,
    symbol: str,
    timeframe: str,
    decision: SwitchDecisionV1,
    meta: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Persist switch-layer decision as an ops artifact.
    Pure side-effect: file write only. No model calls. No network.
    """
    p = Path(out_dir).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)

    d = asdict(decision)
    d["regime"] = decision.regime.value  # JSON-serializable

    payload: Dict[str, Any] = {
        "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "symbol": symbol,
        "timeframe": timeframe,
        "decision": d,
        "meta": meta or {},
    }

    out_path = p / "switch_layer_decision_v1.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path
