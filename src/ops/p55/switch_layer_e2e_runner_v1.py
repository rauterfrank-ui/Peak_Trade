from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class P55RunContextV1:
    """
    P55 runner context.

    Safety:
      - deny-by-default for live/record
      - evidence write ONLY when out_dir is provided
    """

    mode: str = "paper"  # paper|shadow|testnet|live|record
    out_dir: Optional[Path] = None
    run_id: str = "p55"
    allow_live_or_record: bool = False  # hard gate override (default False)


def _json_dump_deterministic(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False)
    path.write_text(payload + "\n", encoding="utf-8")


def _serialize_decision(decision: Any) -> Dict[str, Any]:
    d = asdict(decision)
    if hasattr(decision, "regime"):
        d["regime"] = decision.regime.value
    return d


def _serialize_routing(routing: Any) -> Dict[str, Any]:
    d = asdict(routing)
    if "allowed_strategies" in d and isinstance(d["allowed_strategies"], tuple):
        d["allowed_strategies"] = list(d["allowed_strategies"])
    return d


def _resolve_routing_callable() -> Any:
    """
    P54 routing callable resolver.

    We keep this robust across small refactors by checking a small list of likely
    function names and failing with a helpful error if none are present.
    """
    try:
        import src.ai_orchestration.switch_layer_routing_v1 as routing_mod  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "P55: cannot import P54 routing module: src.ai_orchestration.switch_layer_routing_v1"
        ) from e

    candidates = [
        "route_from_switch_decision_v1",
        "route_by_regime_v1",
        "route_switch_decision_v1",
        "route_strategy_v1",
        "compute_routing_v1",
        "decide_routing_v1",
    ]
    for name in candidates:
        if hasattr(routing_mod, name):
            return getattr(routing_mod, name)

    # fallback: any function name containing "route" and ending with "_v1"
    for name in dir(routing_mod):
        if name.startswith("_"):
            continue
        if "route" in name and name.endswith("_v1") and callable(getattr(routing_mod, name)):
            return getattr(routing_mod, name)

    raise RuntimeError(
        f"P55: no routing callable found in {routing_mod.__name__}. "
        f"Expected one of: {candidates} (or a callable containing 'route' and ending with '_v1')."
    )


def run_switch_layer_e2e_v1(
    prices: Iterable[float],
    ctx: P55RunContextV1,
    *,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    End-to-end (deterministic) pipeline:
      - P53 orchestration hook produces decision + optional evidence
      - P54 routing consumes decision and returns routing output
      - P55 writes a deterministic evidence pack when ctx.out_dir is set

    prices: sequence of returns (or price deltas) for regime computation.
    Returns a dict with keys: decision, routing, meta.
    """
    from src.ai_orchestration.switch_layer_orch_v1 import (
        SwitchLayerContextV1,
        run_switch_layer_orch_v1,
    )

    mode = (ctx.mode or "").strip().lower()
    if mode in {"live", "record"} and not ctx.allow_live_or_record:
        raise PermissionError(
            f"P55 hard gate: mode={mode} denied (deny-by-default). "
            "Use paper/shadow/testnet. If you really need this, set allow_live_or_record=True explicitly."
        )

    prices_list: List[float] = list(prices)
    orch_ctx = SwitchLayerContextV1(
        symbol="p55",
        timeframe="1d",
        out_dir=None,  # P55 writes unified evidence pack; avoid double-write
        meta=meta,
    )
    orch_out = run_switch_layer_orch_v1(returns=prices_list, ctx=orch_ctx)

    routing_fn = _resolve_routing_callable()
    routing_out = routing_fn(decision=orch_out)

    result = {
        "decision": orch_out,
        "routing": routing_out,
        "meta": {
            "p55_run_id": ctx.run_id,
            "mode": mode,
            **(meta or {}),
        },
    }

    if ctx.out_dir is not None:
        out_dir = Path(ctx.out_dir)
        _json_dump_deterministic(result["meta"], out_dir / "meta.json")
        _json_dump_deterministic(_serialize_decision(orch_out), out_dir / "switch_decision.json")
        _json_dump_deterministic(_serialize_routing(routing_out), out_dir / "routing.json")

        manifest = {
            "version": "p55_evidence_pack_v1",
            "run_id": ctx.run_id,
            "mode": mode,
            "files": [
                "meta.json",
                "switch_decision.json",
                "routing.json",
            ],
        }
        _json_dump_deterministic(manifest, out_dir / "manifest.json")

    return result
