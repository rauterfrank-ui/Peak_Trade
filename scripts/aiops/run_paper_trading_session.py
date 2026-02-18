#!/usr/bin/env python3
"""P7 — Paper Trading Session Runner (deterministic, no exchange)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.aiops.p4c.evidence import build_manifest, write_json
from src.execution import OrderIntent
from src.execution.policy import PolicyEnforcerV0
from src.observability.nowcast.decision_context_v1 import build_decision_context_v1
from src.observability.policy.policy_v1 import decide_policy_v1
from src.sim.paper.models import Order
from src.sim.paper.simulator import FeeModel, PaperAccount, PaperTradingSimulator
from src.sim.paper.slippage import SlippageModel


def _env_flag(name: str) -> bool:
    v = os.getenv(name, "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _capture_decision_context_from_spec(
    spec: Dict[str, Any], mids: Dict[str, float]
) -> Dict[str, Any] | None:
    """Phase H: Compute decision_context from spec (no pipeline execution, Policy Critic safe)."""
    if not _env_flag("PT_EVIDENCE_INCLUDE_DECISION"):
        return None
    orders = spec.get("orders") or []
    if not orders:
        return None
    o = orders[0]
    symbol_raw = str(o["symbol"])
    symbol = f"{symbol_raw}/EUR" if "/" not in symbol_raw else symbol_raw
    mid = mids.get(symbol_raw) or mids.get(symbol)
    if mid is None:
        return None
    try:
        intent = OrderIntent(
            symbol=symbol,
            side=str(o["side"]).lower(),
            quantity=float(o["qty"]),
            current_price=float(mid),
        )
        env_str = "paper"
        context: Dict[str, Any] = {}
        context["decision"] = build_decision_context_v1(
            intent=intent,
            env=env_str,
            is_testnet=False,
            current_price=float(mid),
            source="paper_session_cli",
        )
        _policy_raw = decide_policy_v1(env=env_str, decision=context["decision"])
        _policy = _policy_raw.to_dict()
        context["decision"]["policy"] = _policy
        pe = PolicyEnforcerV0.from_env().evaluate(env=env_str, policy=_policy)
        context["decision"]["policy_enforce"] = {
            "allowed": bool(pe.allowed),
            "reason_code": pe.reason_code,
            "reason_detail": pe.reason_detail,
            "action": pe.action,
        }
        return context["decision"] if isinstance(context.get("decision"), dict) else None
    except Exception:
        return None


def _maybe_attach_decision_envelope(path: Path) -> None:
    """Phase G: optionally attach decision envelope (opt-in via PT_EVIDENCE_INCLUDE_DECISION=1)."""
    if not _env_flag("PT_EVIDENCE_INCLUDE_DECISION"):
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "decision" in data:
            return
        dc = data.get("decision_context") if isinstance(data.get("decision_context"), dict) else {}
        policy = dc.get("policy") if isinstance(dc.get("policy"), dict) else {}
        pe = dc.get("policy_enforce") if isinstance(dc.get("policy_enforce"), dict) else {}
        data["decision"] = {
            "source": "paper_session_cli",
            "policy": policy,
            "policy_enforce": pe,
            "costs": dc.get("costs") if isinstance(dc.get("costs"), dict) else {},
            "forecast": dc.get("forecast") if isinstance(dc.get("forecast"), dict) else {},
            "micro": dc.get("micro") if isinstance(dc.get("micro"), dict) else {},
            "regime": dc.get("regime"),
        }
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except Exception:
        pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        o = json.load(f)
    if not isinstance(o, dict):
        raise TypeError(f"expected dict json: {p}")
    return o


def ensure_outdir(repo: Path, run_id: str) -> Path:
    rid = run_id.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    out = repo / "out" / "ops" / "p7" / f"paper_{rid}"
    out.mkdir(parents=True, exist_ok=True)
    return out.resolve()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", type=str, required=True, help="Paper run spec JSON")
    ap.add_argument("--run-id", type=str, default="", help="Deterministic run id (optional)")
    ap.add_argument("--outdir", type=str, default="", help="Override output dir (optional)")
    ap.add_argument("--evidence", type=int, default=1, help="Write evidence manifest (1 default)")
    args = ap.parse_args()

    repo = _repo_root
    spec_path = (
        Path(args.spec).expanduser().resolve()
        if Path(args.spec).is_absolute()
        else (repo / args.spec).resolve()
    )
    spec = load_json(spec_path)

    outdir = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else ensure_outdir(repo, args.run_id)
    )
    outdir.mkdir(parents=True, exist_ok=True)

    acct = PaperAccount(cash=float(spec["initial_cash"]))
    sim = PaperTradingSimulator(
        fee_model=FeeModel(rate=float(spec.get("fee_rate", 0.0))),
        slippage=SlippageModel(bps=float(spec.get("slippage_bps", 0.0))),
    )

    mids: Dict[str, float] = {k: float(v) for k, v in (spec.get("mid_prices") or {}).items()}
    fills: List[Dict[str, Any]] = []

    for o in spec.get("orders") or []:
        order = Order(symbol=str(o["symbol"]), side=str(o["side"]), qty=float(o["qty"]))
        mid = mids[order.symbol]
        f = sim.execute(acct, order, mid_price=mid)
        fills.append(
            {"symbol": f.symbol, "side": f.side, "qty": f.qty, "price": f.price, "fee": f.fee}
        )

    cash, pos = sim.reconcile(acct)

    out_fills = outdir / "fills.json"
    out_acct = outdir / "account.json"
    write_json(out_fills, {"schema_version": "p7.fills.v0", "fills": fills})
    write_json(out_acct, {"schema_version": "p7.account.v0", "cash": cash, "positions": pos})

    printed: List[Path] = [out_fills, out_acct]
    if int(args.evidence) == 1:
        meta = {
            "kind": "p7_paper_manifest",
            "schema_version": "p7.paper_run.v0",
            "created_at_utc": utc_now_iso(),
        }
        manifest = build_manifest(printed, meta, base_dir=outdir)
        dc = _capture_decision_context_from_spec(spec, mids)
        if isinstance(dc, dict) and dc:
            manifest["decision_context"] = dc
        out_manifest = outdir / "evidence_manifest.json"
        write_json(out_manifest, manifest)
        _maybe_attach_decision_envelope(out_manifest)
        printed.append(out_manifest)

    for p in printed:
        print(str(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
