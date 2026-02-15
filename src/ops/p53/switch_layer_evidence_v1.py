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


def _to_jsonable(obj: Any) -> Any:
    """Convert dataclass/enum to JSON-serializable dict."""
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj) and not isinstance(obj, type):
        d = asdict(obj)
        if hasattr(obj, "regime"):
            d["regime"] = getattr(obj.regime, "value", obj.regime)
        if "allowed_strategies" in d and isinstance(d["allowed_strategies"], tuple):
            d["allowed_strategies"] = list(d["allowed_strategies"])
        return d
    if hasattr(obj, "value"):  # Enum
        return obj.value
    return obj


def write_switch_layer_evidence_pack_v1(
    *,
    out_dir: Path,
    run_id: str,
    meta: Dict[str, Any],
    decision: Any,
    routing: Any,
    regime: Any = None,
) -> None:
    """
    Write evidence pack: meta.json, switch_decision.json, routing.json, manifest.json.
    Optional regime.json when regime is provided (backward-compatible).
    """
    p = Path(out_dir).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)

    def _write(path: Path, data: Any) -> None:
        path.write_text(
            json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    _write(p / "meta.json", {"run_id": run_id, **meta})
    _write(p / "switch_decision.json", _to_jsonable(decision))
    _write(p / "routing.json", _to_jsonable(routing))

    if regime is not None:
        _write(p / "switch_regime.json", _to_jsonable(regime))

    manifest = {
        "version": "p57_evidence_pack_v1",
        "run_id": run_id,
        "files": ["meta.json", "switch_decision.json", "routing.json"],
    }
    if regime is not None:
        manifest["files"].append("switch_regime.json")
    _write(p / "manifest.json", manifest)
